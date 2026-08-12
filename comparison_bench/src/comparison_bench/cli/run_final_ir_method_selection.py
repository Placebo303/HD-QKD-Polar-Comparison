"""Bounded Phase-3 tuning and confirmation for final IR method selection.

This deliberately does not reuse the broad sweep runners: it reconstructs only
the immutable Phase-2 split, writes its fixed grid before execution, and never
looks at confirmation outcomes while choosing candidate configurations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from ..data_lock import sha256_file, verify_lock
from ..methods.cascade_lite import run_cascade_lite
from ..methods.layered_ldpc_lite import run_layered_ldpc_lite
from ..types import FrameBatch, IRRunConfig, IRRunResult


DEFAULT_LIMIT_S = 600.0
RESERVED = (
    "predeclared_tuning_grid.json", "tuning_frame_outcomes.csv", "tuning_config_summary.csv",
    "frozen_candidate_configs.json", "confirmation_frame_outcomes.csv", "aggregate_summary.csv",
    "pre_run_plan.json", "run_manifest.json",
)


def _grid() -> dict[str, list[dict[str, Any]]]:
    # Conservative subset of the existing v3 schedules/configurations.
    return {
        "cascade_lite": [
            {"block_size_schedule": [16, 32, 64, 128], "num_passes": 4, "permutation_mode": "seeded_random", "seed": 0, "mapping": "gray", "verify_mode": "crc32"},
            {"block_size_schedule": [12, 6, 24, 13], "num_passes": 4, "permutation_mode": "seeded_random", "seed": 0, "mapping": "gray", "verify_mode": "crc32"},
            {"block_size_schedule": [8, 4, 16, 13], "num_passes": 4, "permutation_mode": "seeded_random", "seed": 0, "mapping": "gray", "verify_mode": "crc32"},
            {"block_size_schedule": [16, 32, 64, 128], "num_passes": 3, "permutation_mode": "seeded_random", "seed": 0, "mapping": "gray", "verify_mode": "crc32"},
        ],
        "layered_ldpc_lite": [
            {"parity_fraction": 0.80, "max_iter": 20, "osd_order": 0, "bp_method": "minimum_sum", "mapping": "gray", "llr_mode": "bsc_estimated", "bitplane_rate_mode": "uniform", "column_weight": 3, "ldpc_seed": 20260428},
            {"parity_fraction": 0.80, "max_iter": 50, "osd_order": 0, "bp_method": "minimum_sum", "mapping": "gray", "llr_mode": "bsc_estimated", "bitplane_rate_mode": "uniform", "column_weight": 3, "ldpc_seed": 20260428},
            {"parity_fraction": 0.90, "max_iter": 50, "osd_order": 0, "bp_method": "minimum_sum", "mapping": "gray", "llr_mode": "bsc_estimated", "bitplane_rate_mode": "uniform", "column_weight": 3, "ldpc_seed": 20260428},
            {"parity_fraction": 1.00, "max_iter": 50, "osd_order": 0, "bp_method": "minimum_sum", "mapping": "gray", "llr_mode": "bsc_estimated", "bitplane_rate_mode": "uniform", "column_weight": 3, "ldpc_seed": 20260428},
        ],
    }


def _config_id(method: str, config: dict[str, Any]) -> str:
    text = json.dumps({"method": method, "config": config}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _load_locked_batch(manifest: dict[str, Any], split_name: str) -> tuple[FrameBatch, pd.DataFrame]:
    split = pd.read_csv(manifest["locked_split"]["path"])
    locked = split.loc[split["split"] == split_name].sort_values(["dataset_id", "frame_id"]).reset_index(drop=True)
    expected = int(manifest["counts"][f"{split_name}_frames"])
    if len(locked) != expected:
        raise ValueError(f"expected {expected} {split_name} frames, found {len(locked)}")
    source = pd.read_parquet(manifest["source"]["path"])
    wanted = locked[["dataset_id", "frame_id"]].copy()
    wanted["_locked_order"] = np.arange(len(wanted))
    rows = source.merge(wanted, on=["dataset_id", "frame_id"], how="inner", validate="many_to_one")
    rows = rows.sort_values(["_locked_order", "pair_idx"])
    counts = rows.groupby("_locked_order").size()
    if len(counts) != expected or not (counts == int(manifest["domain"]["frame_len_symbols"])).all():
        raise ValueError("source cannot reconstruct every locked frame exactly")
    alice = rows["alice_symbol"].to_numpy(dtype=np.int64).reshape(expected, -1)
    bob = rows["bob_symbol"].to_numpy(dtype=np.int64).reshape(expected, -1)
    batch = FrameBatch(
        dataset_id=f"final_ir_locked_{split_name}", alice_symbols=alice, bob_symbols=bob,
        dimension=int(manifest["domain"]["dimension"]), frame_len_symbols=int(manifest["domain"]["frame_len_symbols"]),
        metadata={"data_mode": "real_data", "source_path": manifest["source"]["path"], "mapping": "gray", "locked_split": split_name},
    )
    return batch, locked


def _run(method: str, batch: FrameBatch, config: dict[str, Any]) -> IRRunResult:
    local = FrameBatch(batch.dataset_id, batch.alice_symbols, batch.bob_symbols, batch.dimension, batch.frame_len_symbols, {**batch.metadata, **config})
    cfg = IRRunConfig(method=method, method_variant="gray", dimension=local.dimension, frame_len_symbols=local.frame_len_symbols,
                      max_iter=int(config.get("max_iter", 0)), verify_mode=str(config.get("verify_mode", "crc32")))
    runner: Callable[[FrameBatch, IRRunConfig], IRRunResult] = run_cascade_lite if method == "cascade_lite" else run_layered_ldpc_lite
    return runner(local, cfg)


def _outcomes(result: IRRunResult, locked: pd.DataFrame, method: str, split: str, config_id: str, config: dict[str, Any], elapsed_s: float | None = None) -> list[dict[str, Any]]:
    explicit = list((result.metadata or {}).get("frame_results", []))
    by_idx = {int(r.get("frame_idx", i)): r for i, r in enumerate(explicit) if isinstance(r, dict)}
    out = []
    for idx, key in locked.reset_index(drop=True).iterrows():
        row = by_idx.get(idx, {})
        decode = bool(row.get("decode_success", False))
        verify = bool(row.get("verify_success", False))
        out.append({"split": split, "locked_frame_key": key["locked_frame_key"], "dataset_id": key["dataset_id"], "frame_id": int(key["frame_id"]),
                    "method": method, "config_id": config_id, "decode_success": decode, "verify_success": verify,
                    "verified_success": bool(decode and verify), "frame_status": "verified_success" if decode and verify else ("decode_failed" if not decode else "verify_failed"),
                    "raw_frame_ser": row.get("raw_frame_ser"), "raw_frame_ber": row.get("raw_frame_ber"), "post_frame_ser": row.get("post_frame_ser"),
                    "leak_bits_frame": row.get("leak_bits_frame"), "runtime_ms": row.get("runtime_ms"), "method_status": (result.metadata or {}).get("method_status", "unknown"),
                    "config_json": json.dumps(config, sort_keys=True), "run_elapsed_s": elapsed_s})
    return out


def _summary(rows: list[dict[str, Any]], method: str, config_id: str, config: dict[str, Any], result: IRRunResult, split: str) -> dict[str, Any]:
    df = pd.DataFrame(rows)
    return {"split": split, "method": method, "config_id": config_id, "config_json": json.dumps(config, sort_keys=True),
            "attempted_frames": len(df), "verified_successes": int(df["verified_success"].sum()),
            "failed_frames": int((~df["verified_success"]).sum()), "same_method_total_leak_bits": float(result.leak_EC_actual_bits),
            "runtime_s": float(result.runtime_s), "method_status": (result.metadata or {}).get("method_status", "unknown"),
            "leakage_comparison_note": "method-specific disclosure accounting; not cross-method ranked"}


def main() -> int:
    ap = argparse.ArgumentParser(description="Run bounded final-IR tuning then confirmation on the immutable Phase-2 lock.")
    ap.add_argument("--output-dir", required=True, help="new additive Phase-3 directory; required to prevent accidental reuse")
    ap.add_argument("--lock-manifest", help="immutable Phase-2 lock manifest; defaults to OUTPUT-DIR/data_lock_manifest.json")
    ap.add_argument("--time-limit-s", type=float, default=DEFAULT_LIMIT_S)
    args = ap.parse_args()
    out = Path(args.output_dir)
    manifest_path = Path(args.lock_manifest) if args.lock_manifest else out / "data_lock_manifest.json"
    if not manifest_path.exists() or not verify_lock(manifest_path):
        raise SystemExit("data lock verification failed; no Phase-3 file was written")
    existing = [name for name in RESERVED if (out / name).exists()]
    if existing:
        raise SystemExit(f"refusing to overwrite Phase-3 reserved files: {existing}")
    out.mkdir(parents=True, exist_ok=True)
    lock = json.loads(manifest_path.read_text(encoding="utf-8"))
    grid = _grid()
    limit = float(args.time_limit_s)
    run_manifest = {"schema_version": "final_ir_method_selection_phase3_v1", "started_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "data_lock_manifest": str(manifest_path), "data_lock_sha256": sha256_file(manifest_path), "source_sha256_verified": True,
        "limits": {"wall_time_limit_s": limit, "tuning_frames_per_config": lock["counts"]["tuning_frames"], "confirmation_frames_per_candidate": lock["counts"]["confirmation_frames"], "tuning_tasks": sum(map(len, grid.values())), "confirmation_tasks": 2, "no_adaptive_extension": True},
        "candidate_scope": ["cascade_lite", "layered_ldpc_lite"], "excluded": {"qldpc_reference": "reference_only; not run", "polar_existing": "historical context; not run"},
        "selection": "within candidate: verified successes descending, same-method total leak ascending, runtime ascending; no per-frame or per-point oracle", "preprocessing_mapping_verification": lock["preprocessing_mapping_verification_contract"],
        "grid": grid, "environment": {"python": platform.python_version(), "platform": platform.platform(), "pandas": pd.__version__, "numpy": np.__version__}}
    (out / "pre_run_plan.json").write_text(json.dumps(run_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "predeclared_tuning_grid.json").write_text(json.dumps({"grid": grid, "selection": run_manifest["selection"]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    started = time.monotonic()
    tuning_batch, tuning_locked = _load_locked_batch(lock, "tuning")
    tuning_rows: list[dict[str, Any]] = []
    tuning_summary: list[dict[str, Any]] = []
    frozen: dict[str, Any] = {}
    for method, configs in grid.items():
        candidates = []
        for config in configs:
            if time.monotonic() - started > limit:
                raise TimeoutError("Phase-3 wall-time limit reached during tuning")
            cid = _config_id(method, config)
            result = _run(method, tuning_batch, config)
            rows = _outcomes(result, tuning_locked, method, "tuning", cid, config, time.monotonic() - started)
            tuning_rows.extend(rows)
            summary = _summary(rows, method, cid, config, result, "tuning")
            tuning_summary.append(summary)
            candidates.append(summary)
        candidates.sort(key=lambda r: (-r["verified_successes"], r["same_method_total_leak_bits"], r["runtime_s"], r["config_id"]))
        winner = candidates[0]
        frozen[method] = {"config_id": winner["config_id"], "config": json.loads(winner["config_json"]), "tuning_selection_summary": winner}
    pd.DataFrame(tuning_rows).to_csv(out / "tuning_frame_outcomes.csv", index=False)
    pd.DataFrame(tuning_summary).to_csv(out / "tuning_config_summary.csv", index=False)
    (out / "frozen_candidate_configs.json").write_text(json.dumps({"frozen_before_confirmation": True, "candidates": frozen}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    confirmation_batch, confirmation_locked = _load_locked_batch(lock, "confirmation")
    confirmation_rows: list[dict[str, Any]] = []
    aggregate: list[dict[str, Any]] = []
    for method, item in frozen.items():
        if time.monotonic() - started > limit:
            raise TimeoutError("Phase-3 wall-time limit reached before confirmation completion")
        result = _run(method, confirmation_batch, item["config"])
        rows = _outcomes(result, confirmation_locked, method, "confirmation", item["config_id"], item["config"], time.monotonic() - started)
        confirmation_rows.extend(rows)
        aggregate.append(_summary(rows, method, item["config_id"], item["config"], result, "confirmation"))
    pd.DataFrame(confirmation_rows).to_csv(out / "confirmation_frame_outcomes.csv", index=False)
    pd.DataFrame(aggregate).to_csv(out / "aggregate_summary.csv", index=False)
    run_manifest.update({"completed_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "runtime_s": time.monotonic() - started,
        "outputs": {name: str(out / name) for name in RESERVED if (out / name).exists()}, "status": "completed_within_bound"})
    (out / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": run_manifest["status"], "runtime_s": run_manifest["runtime_s"], "frozen": frozen, "confirmation": aggregate}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
