"""Create and verify the immutable Phase-2 frame split for final IR selection."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_commit(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def select_group_disjoint_split(
    eligible: pd.DataFrame, *, seed: int, tuning_frames: int, confirmation_frames: int,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Select deterministic group-disjoint frame IDs from an eligible frame table.

    This is deliberately file-free so the split policy can be unit tested without
    depending on pytest temporary-directory cleanup on Windows.
    """
    needed = tuning_frames + confirmation_frames
    if len(eligible) < needed:
        raise ValueError(f"eligible frames={len(eligible)}; need {needed} for the declared split")
    eligible = eligible.sort_values(["dataset_id", "frame_id"]).reset_index(drop=True)
    rng = np.random.default_rng(seed)
    groups = rng.permutation(eligible["dataset_id"].drop_duplicates().to_numpy()).tolist()
    tuning_groups, confirmation_groups = [], []
    tuning_pool = confirmation_pool = pd.DataFrame()
    for group in groups:
        pool = eligible.loc[eligible["dataset_id"] == group]
        if len(tuning_pool) < tuning_frames:
            tuning_groups.append(group)
            tuning_pool = pd.concat([tuning_pool, pool], ignore_index=True)
        else:
            confirmation_groups.append(group)
            confirmation_pool = pd.concat([confirmation_pool, pool], ignore_index=True)
        if len(tuning_pool) >= tuning_frames and len(confirmation_pool) >= confirmation_frames:
            break
    if len(tuning_pool) < tuning_frames or len(confirmation_pool) < confirmation_frames:
        raise ValueError("eligible source groups cannot support group-disjoint tuning and confirmation splits")
    chosen = pd.concat([
        tuning_pool.iloc[rng.permutation(len(tuning_pool))[:tuning_frames]].assign(split="tuning"),
        confirmation_pool.iloc[rng.permutation(len(confirmation_pool))[:confirmation_frames]].assign(split="confirmation"),
    ], ignore_index=True)
    chosen["locked_frame_key"] = chosen["dataset_id"].astype(str) + ":" + chosen["frame_id"].astype(str)
    if chosen["locked_frame_key"].duplicated().any():
        raise AssertionError("locked frame keys are not unique")
    return chosen, tuning_groups, confirmation_groups


def lock_frames(
    source: Path,
    output_dir: Path,
    *,
    seed: int = 20260725,
    dimension: int = 1024,
    frame_len_symbols: int = 64,
    ser_low: float = 0.20,
    ser_high: float = 0.30,
    tuning_frames: int = 60,
    confirmation_frames: int = 60,
    repo_root: Path | None = None,
) -> dict:
    """Lock a deterministic, disjoint split from a pre-existing real frame table.

    Eligibility is based solely on source-table metadata and raw frame errors;
    no candidate-method result is read by this function.
    """
    source, output_dir = Path(source).resolve(), Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing data-lock directory: {output_dir}")
    df = pd.read_parquet(source)
    required = {"dataset_id", "frame_id", "pair_idx", "alice_symbol", "bob_symbol", "dimension", "frame_len_symbols"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"source table lacks required columns: {sorted(missing)}")
    base = df.loc[(df["dimension"] == dimension) & (df["frame_len_symbols"] == frame_len_symbols)].copy()
    if base.empty:
        raise ValueError("no frames match declared dimension and frame length")
    frame = base.groupby(["dataset_id", "frame_id"], as_index=False).agg(
        dimension=("dimension", "first"),
        frame_len_symbols=("frame_len_symbols", "first"),
        symbols=("pair_idx", "size"),
        raw_ser=("alice_symbol", lambda a: 0.0),
    )
    errors = base.assign(_error=base["alice_symbol"].ne(base["bob_symbol"]).astype(int)).groupby(
        ["dataset_id", "frame_id"], as_index=False
    )["_error"].mean().rename(columns={"_error": "frame_raw_ser"})
    frame = frame.drop(columns="raw_ser").merge(errors, on=["dataset_id", "frame_id"], validate="one_to_one")
    dataset_ser = frame.groupby("dataset_id", as_index=False)["frame_raw_ser"].mean().rename(columns={"frame_raw_ser": "dataset_raw_ser"})
    frame = frame.merge(dataset_ser, on="dataset_id", validate="many_to_one")
    eligible = frame.loc[(frame["symbols"] == frame_len_symbols) & (frame["dataset_raw_ser"] >= ser_low) & (frame["dataset_raw_ser"] < ser_high)].copy()
    chosen, tuning_groups, confirmation_groups = select_group_disjoint_split(
        eligible, seed=seed, tuning_frames=tuning_frames, confirmation_frames=confirmation_frames,
    )
    output_dir.mkdir(parents=True)
    split_path = output_dir / "locked_frame_split.csv"
    chosen.sort_values(["split", "dataset_id", "frame_id"]).to_csv(split_path, index=False)
    root = Path(repo_root or Path.cwd())
    config_sources = [root / "comparison_bench/configs/cascade_param_sweep.yaml", root / "comparison_bench/configs/layered_ldpc_param_sweep.yaml"]
    config_records = [{"path": str(path), "sha256": sha256_file(path)} for path in config_sources]
    policy = {
        "candidates": ["cascade_lite", "layered_ldpc_lite"], "tune_only_on": "tuning",
        "one_global_config_per_candidate": True, "per_point_oracle_selection": False,
        "selection_order": ["verified success fraction", "failure count", "compatible leakage only within method", "runtime"],
        "config_sources": config_records,
    }
    policy_path = output_dir / "initial_global_candidate_config_policy.json"
    policy_path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "final_ir_method_selection_data_lock_v1",
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": {"path": str(source), "sha256": sha256_file(source)},
        "locked_split": {"path": str(split_path), "sha256": sha256_file(split_path)},
        "domain": {"data_mode": "real_data", "dimension": dimension, "frame_len_symbols": frame_len_symbols,
                   "dataset_raw_ser_stratum": {"lower_inclusive": ser_low, "upper_exclusive": ser_high}},
        "counts": {"eligible_frames": int(len(eligible)), "tuning_frames": tuning_frames,
                   "confirmation_frames": confirmation_frames, "required_confirmation_frames_per_stratum": 60},
        "split": {"seed": seed, "selection": "numpy PCG64 assigns whole dataset/source groups before sampling sorted composite frame IDs",
                  "disjoint": True, "group_disjoint": True, "tuning_dataset_ids": tuning_groups,
                  "confirmation_dataset_ids": confirmation_groups},
        "preprocessing_mapping_verification_contract": {
            "input_columns": sorted(required), "preprocessing": "source frame table as stored; no symbol remapping during lock",
            "mapping": "gray for both executable candidates", "verification": "independent per-frame verification; failures retained in attempted denominator",
            "success_classifier": "comparison_bench.metrics.success.classify_real_ir_success_row"},
        "candidate_config_policy": policy,
        "decision_rule": {"primary": "paired independently verified frame success", "test": "exact two-sided binomial test on McNemar discordant pairs", "alpha": 0.05,
                          "no_decision": "zero discordant pairs, p >= 0.05, missing paired outcome, any required stratum under 60 attempted frames, or bounded run incomplete"},
        "confidence_and_stopping": {"zero_failure_95pct_upper_bound": "1 - 0.05**(1/n); n=60 gives 0.0487", "no_adaptive_extension": True,
                                    "confirmation_frame_cap_per_stratum": confirmation_frames, "time_limit": "declared before Phase 3; unset at data lock"},
        "reserved_output_paths": ["frozen_candidate_configs.json", "confirmation_frame_outcomes.csv", "aggregate_summary.csv", "route_a_compatibility_gate.json", "decision_report.md"],
        "policy_artifact": {"path": str(policy_path), "sha256": sha256_file(policy_path)},
        "environment": {"python": sys.version, "platform": platform.platform(), "pandas": pd.__version__, "numpy": np.__version__, "git_commit": _git_commit(root)},
    }
    (output_dir / "data_lock_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def verify_lock(manifest_path: Path) -> bool:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    for item in (manifest["source"], manifest["locked_split"]):
        if sha256_file(Path(item["path"])) != item["sha256"]:
            return False
    split = pd.read_csv(manifest["locked_split"]["path"])
    return not split["locked_frame_key"].duplicated().any() and set(split["split"]) == {"tuning", "confirmation"}
