#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT_DEFAULT = Path(r"D:\Data\Raw Data\ASENoise_Type0")
SOURCE_TIMESTAMP_DEFAULT = "20260427_090053"
SUBSET_RUN_TEMPLATE = "hdqkd_asenoise_type0_ch3_2_subset_{timestamp}"
SYNTHETIC_LOSS_DB = 6
FIXED_DROPS = {"low": 2.1, "mid": 2.3, "high": 2.5}
SMOKE_DIMS = [4096]
SMOKE_BWS = [120, 200]
FULL_DIMS = [512, 1024, 2048, 4096]
FULL_BWS = [30, 60, 120, 200]


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _run(cmd: list[str], *, cwd: Path = REPO_ROOT, log_path: Path | None = None) -> int:
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n[{_now()}] RUN {' '.join(cmd)}\n")
            fh.flush()
            proc = subprocess.Popen(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            assert proc.stdout is not None
            for line in proc.stdout:
                fh.write(line)
                fh.flush()
                try:
                    print(line, end="")
                except UnicodeEncodeError:
                    enc = sys.stdout.encoding or "utf-8"
                    print(line.encode(enc, errors="replace").decode(enc, errors="replace"), end="")
            return int(proc.wait())
    proc = subprocess.run(cmd, cwd=str(cwd))
    return int(proc.returncode)


def _source_run_root(dataset_dir: Path, source_timestamp: str) -> Path:
    return dataset_dir / SUBSET_RUN_TEMPLATE.format(timestamp=source_timestamp)


def _source_shadow_master(data_root: Path, source_timestamp: str) -> Path:
    return data_root / f"asenoise_type0_actual_ir_finite_key_master_{source_timestamp}.csv"


def _datasets(data_root: Path, selected: str) -> list[Path]:
    wanted = {x.strip() for x in str(selected).split(",") if x.strip()}
    return [p for p in sorted(data_root.iterdir(), key=lambda x: x.name) if p.is_dir() and (not wanted or p.name in wanted)]


def _safe_float(v: Any, default: float = float("nan")) -> float:
    try:
        out = float(v)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def estimate(args: argparse.Namespace) -> int:
    data_root = Path(args.data_root)
    source = Path(args.input_csv) if str(args.input_csv).strip() else _source_shadow_master(data_root, str(args.source_timestamp))
    if not source.exists():
        raise SystemExit(f"missing input shadow master: {source}")
    ts = str(args.timestamp or _timestamp())
    out_csv = data_root / f"asenoise_type0_routeA_estimated_master_{ts}.csv"
    out_summary = data_root / f"asenoise_type0_routeA_estimated_summary_{ts}.txt"
    df = pd.read_csv(source)
    if "accepted_rate_proxy" in df.columns:
        rate = pd.to_numeric(df["accepted_rate_proxy"], errors="coerce")
    else:
        rate = pd.to_numeric(df.get("SKR_secure_actual_ir_bps"), errors="coerce") / pd.to_numeric(df.get("PIE_secure_actual_ir"), errors="coerce")
    shadow = pd.to_numeric(df["PIE_secure_actual_ir"], errors="coerce")
    df["routeA_est_model_tag"] = "fixed_empirical_band_from_prior_routeA_actual_replay"
    df["routeA_est_source_shadow_csv"] = str(source)
    for key, drop in FIXED_DROPS.items():
        pie_col = f"PIE_routeA_est_{key}"
        skr_col = f"SKR_routeA_est_{key}_bps"
        drop_col = f"routeA_est_{key}_drop_bit_per_pair"
        df[drop_col] = float(drop)
        df[pie_col] = np.maximum(0.0, shadow - float(drop))
        df[skr_col] = pd.to_numeric(df[pie_col], errors="coerce") * rate
    df.to_csv(out_csv, index=False)

    lines = [
        f"created_at: {_now()}",
        f"input_shadow_master: {source}",
        f"output_csv: {out_csv}",
        f"row_count: {len(df)}",
        "reporting_role: empirical Route A correction estimate only; not actual replay.",
        "fixed_drop_band_bit_per_pair: low=2.1, mid=2.3, high=2.5",
    ]
    mid_skr = pd.to_numeric(df["SKR_routeA_est_mid_bps"], errors="coerce")
    if mid_skr.notna().any():
        best = df.loc[mid_skr.idxmax()]
        lines.append(f"global_best_mid: dataset={best.get('dataset_label')},d={int(best['dimension'])},bw={int(best['bin_width_ps'])},PIE={_safe_float(best['PIE_routeA_est_mid']):.6g},SKR={_safe_float(best['SKR_routeA_est_mid_bps']):.6g}")
    for label, grp in df.groupby("dataset_label"):
        vals = pd.to_numeric(grp["SKR_routeA_est_mid_bps"], errors="coerce")
        if vals.notna().any():
            best = grp.loc[vals.idxmax()]
            lines.append(f"dataset_best_mid: dataset={label},d={int(best['dimension'])},bw={int(best['bin_width_ps'])},PIE={_safe_float(best['PIE_routeA_est_mid']):.6g},SKR={_safe_float(best['SKR_routeA_est_mid_bps']):.6g}")
    _write_text(out_summary, "\n".join(lines))
    print(f"[ASENOISE_ROUTEA] estimate_csv={out_csv}")
    print(f"[ASENOISE_ROUTEA] estimate_summary={out_summary}")
    return 0


def _copy_candidate_csvs(candidate_dir: Path, staging_dir: Path, dims: set[int], bws: set[int]) -> None:
    staging_dir.mkdir(parents=True, exist_ok=True)
    for name in ("polar_e2e_results.csv", "polar_diag_summary.csv", "polar_layer_metrics.csv"):
        src = candidate_dir / name
        df = pd.read_csv(src)
        if "dimension" in df.columns:
            df = df[pd.to_numeric(df["dimension"], errors="coerce").isin(sorted(dims))].copy()
        if "bin_width_ps" in df.columns:
            df = df[pd.to_numeric(df["bin_width_ps"], errors="coerce").isin(sorted(bws))].copy()
        df.to_csv(staging_dir / name, index=False)


def _build_replay_index(candidate_dir: Path, output_dir: Path, dataset_label: str, dims: set[int], bws: set[int]) -> dict[str, Any]:
    main = pd.read_csv(candidate_dir / "polar_e2e_results.csv")
    layer = pd.read_csv(candidate_dir / "polar_layer_metrics.csv")
    main = main[pd.to_numeric(main["dimension"], errors="coerce").isin(sorted(dims)) & pd.to_numeric(main["bin_width_ps"], errors="coerce").isin(sorted(bws))].copy()
    layer = layer[pd.to_numeric(layer["dimension"], errors="coerce").isin(sorted(dims)) & pd.to_numeric(layer["bin_width_ps"], errors="coerce").isin(sorted(bws))].copy()

    point_rows: list[dict[str, Any]] = []
    layer_rows: list[dict[str, Any]] = []
    for _, row in main.iterrows():
        d = int(row["dimension"])
        bw = int(row["bin_width_ps"])
        pid = f"asenoise_{dataset_label}_d{d}_bw{bw}"
        sidecar = candidate_dir.parent / "e2e_center_aligned" / "sidecars" / f"d{d}_bw{bw}" / "blk0"
        a_path = sidecar / "a_eff.npy"
        b_path = sidecar / "b_eff.npy"
        a_count = int(np.load(a_path, mmap_mode="r").shape[0]) if a_path.exists() else None
        b_count = int(np.load(b_path, mmap_mode="r").shape[0]) if b_path.exists() else None
        point_layers = layer[(pd.to_numeric(layer["dimension"], errors="coerce") == d) & (pd.to_numeric(layer["bin_width_ps"], errors="coerce") == bw)].copy()
        ready = "yes"
        reason = "fixed_blocks_drop_tail"
        if a_count is None or b_count is None:
            ready = "no"
            reason = "missing_sidecar_arrays"
        elif point_layers.empty:
            ready = "no"
            reason = "missing_layer_rows"
        point_rows.append(
            {
                "dataset_label": dataset_label,
                "loss_db": SYNTHETIC_LOSS_DB,
                "dimension": d,
                "bin_width_ps": bw,
                "point_id": pid,
                "a_eff_source_path": str(a_path) if a_path.exists() else "MISSING",
                "b_eff_source_path": str(b_path) if b_path.exists() else "MISSING",
                "a_eff_count": a_count if a_count is not None else "MISSING",
                "b_eff_count": b_count if b_count is not None else "MISSING",
                "layer_metrics_source_path": str(candidate_dir / "polar_layer_metrics.csv"),
                "sidecar_source_path": str(sidecar / "sidecar_meta.json"),
                "replay_ready_tag": ready,
                "replay_block_rule_tag": reason,
            }
        )
        for _, lrow in point_layers.iterrows():
            layer_idx = int(float(lrow.get("layer_idx", lrow.get("layer_id", 0))))
            decoder_mode = str(lrow.get("decoder_mode_best") or "").strip()
            k_best = _safe_float(lrow.get("k_best"))
            block_symbols = _safe_float(lrow.get("layer_block_symbols"))
            rescue_success = int(_safe_float(lrow.get("rescue_success"), 0.0))
            layer_ready = "yes" if ready == "yes" and rescue_success == 1 and decoder_mode and k_best > 0 and block_symbols > 0 else "no"
            layer_rows.append(
                {
                    "dataset_label": dataset_label,
                    "loss_db": SYNTHETIC_LOSS_DB,
                    "dimension": d,
                    "bin_width_ps": bw,
                    "point_id": pid,
                    "layer_id": layer_idx,
                    "decoder_mode_best": decoder_mode or "MISSING",
                    "k_best": int(k_best) if k_best > 0 else "MISSING",
                    "rate_best": lrow.get("rate_best", "MISSING"),
                    "crc_bits": lrow.get("crc_bits", "MISSING"),
                    "frozen_count_best": lrow.get("frozen_count_best", "MISSING"),
                    "layer_block_symbols": int(block_symbols) if block_symbols > 0 else "MISSING",
                    "layer_replay_ready_tag": layer_ready,
                }
            )
    output_dir.mkdir(parents=True, exist_ok=True)
    point_df = pd.DataFrame(point_rows)
    layer_df = pd.DataFrame(layer_rows)
    point_df.to_csv(output_dir / "replay_index_point_table.csv", index=False)
    layer_df.to_csv(output_dir / "replay_index_layer_table.csv", index=False)
    ready_points = int(point_df["replay_ready_tag"].astype(str).eq("yes").sum()) if not point_df.empty else 0
    ready_layers = int(layer_df["layer_replay_ready_tag"].astype(str).eq("yes").sum()) if not layer_df.empty else 0
    _write_text(
        output_dir / "round1a_summary.txt",
        "\n".join(
            [
                f"dataset_label: {dataset_label}",
                f"candidate_dir: {candidate_dir}",
                f"point_count: {len(point_df)}",
                f"layer_count: {len(layer_df)}",
                f"replay_ready_points: {ready_points}",
                f"replay_ready_layers: {ready_layers}",
                f"synthetic_loss_db_for_routeA_tools: {SYNTHETIC_LOSS_DB}",
            ]
        ),
    )
    return {"point_count": int(len(point_df)), "layer_count": int(len(layer_df)), "ready_points": ready_points, "ready_layers": ready_layers}


def _run_stage_c(*, candidate_stage_dir: Path, stage1_dir: Path, stage2_dir: Path, log_path: Path) -> int:
    cmds = [
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "longrun_build_finite_key_audit_table.py"),
            "--input-dirs",
            str(candidate_stage_dir),
            str(stage1_dir),
            "--franson-visibility",
            "0.95",
            "--eps-sec",
            "1e-10",
            "--eps-cor",
            "1e-10",
            "--output-dir",
            str(stage2_dir),
            "--overwrite",
        ],
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "round2_build_actual_ir_finite_key_shadow.py"),
            "--output-dir",
            str(stage2_dir),
            "--overwrite",
        ],
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "round2_build_beta_baseline_shadow.py"),
            "--output-dir",
            str(stage2_dir),
            "--overwrite",
        ],
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "longrun_build_security_master_table.py"),
            "--actual-ir-dir",
            str(stage2_dir),
            "--beta-baseline-dir",
            str(stage2_dir),
            "--performance-proxy-input-dirs",
            str(candidate_stage_dir),
            "--output-dir",
            str(stage2_dir),
            "--overwrite",
        ],
    ]
    for cmd in cmds:
        rc = _run(cmd, log_path=log_path)
        if rc != 0:
            return rc
    return 0


def _merge_with_shadow(dataset_label: str, stage2_dir: Path, shadow_master: pd.DataFrame) -> pd.DataFrame:
    master = pd.read_csv(stage2_dir / "security_calibrated_master_table.csv")
    master["dataset_label"] = dataset_label
    master["noise"] = dataset_label
    if "PIE_main" not in master.columns:
        master["PIE_main"] = pd.to_numeric(master["PIE_secure_actual_ir"], errors="coerce")
    if "SKR_main_bps" not in master.columns:
        master["SKR_main_bps"] = pd.to_numeric(master["SKR_secure_actual_ir_bps"], errors="coerce")
    master["main_result_source"] = "actual_ir_finite_key"
    master["performance_proxy_role"] = "diagnostic_only"
    shadow = shadow_master[shadow_master["dataset_label"].astype(str) == str(dataset_label)].copy()
    keep = ["dataset_label", "dimension", "bin_width_ps", "PIE_secure_actual_ir", "SKR_secure_actual_ir_bps"]
    shadow = shadow[keep].rename(
        columns={
            "PIE_secure_actual_ir": "PIE_shadow_secure_actual_ir",
            "SKR_secure_actual_ir_bps": "SKR_shadow_secure_actual_ir_bps",
        }
    )
    merged = master.merge(shadow, on=["dataset_label", "dimension", "bin_width_ps"], how="left")
    merged["delta_PIE_shadow_minus_actual"] = pd.to_numeric(merged["PIE_shadow_secure_actual_ir"], errors="coerce") - pd.to_numeric(merged["PIE_secure_actual_ir"], errors="coerce")
    merged["delta_SKR_shadow_minus_actual_bps"] = pd.to_numeric(merged["SKR_shadow_secure_actual_ir_bps"], errors="coerce") - pd.to_numeric(merged["SKR_secure_actual_ir_bps"], errors="coerce")
    front_cols = [
        "noise",
        "dataset_label",
        "dimension",
        "bin_width_ps",
        "PIE_main",
        "SKR_main_bps",
        "main_result_source",
        "PIE_secure_actual_ir",
        "SKR_secure_actual_ir_bps",
    ]
    rest_cols = [c for c in merged.columns if c not in front_cols and c != "loss_db"]
    merged = merged[[*front_cols, *rest_cols]]
    return merged


def replay(args: argparse.Namespace) -> int:
    data_root = Path(args.data_root)
    ts = str(args.timestamp or _timestamp())
    mode = str(args.mode)
    dims = set(SMOKE_DIMS if mode == "smoke" else FULL_DIMS)
    bws = set(SMOKE_BWS if mode == "smoke" else FULL_BWS)
    selected = _datasets(data_root, str(args.datasets))
    shadow_master_path = _source_shadow_master(data_root, str(args.source_timestamp))
    shadow_master = pd.read_csv(shadow_master_path)
    aggregate_frames: list[pd.DataFrame] = []
    results: list[dict[str, Any]] = []
    for dataset_dir in selected:
        dataset_label = dataset_dir.name
        source_root = _source_run_root(dataset_dir, str(args.source_timestamp))
        candidate_dir = source_root / "polar"
        out_root = dataset_dir / f"routeA_actual_replay_{mode}_{ts}"
        log_path = out_root / "run.log"
        item: dict[str, Any] = {
            "dataset_label": dataset_label,
            "started_at": _now(),
            "source_root": str(source_root),
            "out_root": str(out_root),
            "mode": mode,
            "dims": sorted(dims),
            "bws": sorted(bws),
            "errors": [],
        }
        if out_root.exists() and bool(args.overwrite):
            shutil.rmtree(out_root)
        out_root.mkdir(parents=True, exist_ok=True)
        if not (candidate_dir / "polar_e2e_results.csv").exists():
            item["errors"].append(f"missing_candidate:{candidate_dir}")
            results.append(item)
            continue
        replay_index_dir = out_root / "replay_index"
        stage1_dir = out_root / "stage1_actual_ir"
        stage2_dir = out_root / "stage2_security"
        candidate_stage_dir = out_root / "asenoise_6dB_candidate"
        _copy_candidate_csvs(candidate_dir, candidate_stage_dir, dims, bws)
        item["replay_index"] = _build_replay_index(candidate_dir, replay_index_dir, dataset_label, dims, bws)
        rc = _run(
            [
                sys.executable,
                str(REPO_ROOT / "tools" / "routeA_run_formal_replay_shards.py"),
                "--candidate-dir",
                str(candidate_stage_dir),
                "--replay-index-dir",
                str(replay_index_dir),
                "--output-dir",
                str(stage1_dir),
                "--shards",
                str(int(args.shards)),
                "--workers",
                str(int(args.workers)),
                "--verification-tag-bits",
                "32",
                "--overwrite",
            ],
            log_path=log_path,
        )
        item["stage1_exit_code"] = rc
        if rc != 0:
            item["errors"].append(f"stage1_failed:{rc}")
            item["finished_at"] = _now()
            _write_json(out_root / "run_manifest.json", item)
            results.append(item)
            continue
        rc = _run_stage_c(candidate_stage_dir=candidate_stage_dir, stage1_dir=stage1_dir, stage2_dir=stage2_dir, log_path=log_path)
        item["stage2_exit_code"] = rc
        if rc != 0:
            item["errors"].append(f"stage2_failed:{rc}")
            item["finished_at"] = _now()
            _write_json(out_root / "run_manifest.json", item)
            results.append(item)
            continue
        merged = _merge_with_shadow(dataset_label, stage2_dir, shadow_master)
        merged.to_csv(out_root / "routeA_actual_vs_shadow_point_table.csv", index=False)
        aggregate_frames.append(merged)
        formal_rows = int(merged.get("epsilon_EC_bound_formula_tag", pd.Series(dtype=str)).astype(str).eq("union_bound_over_blocks_universal_hash").sum())
        actual_rows = int(merged.get("leak_EC_source_tag", pd.Series(dtype=str)).astype(str).str.startswith("actual_ir_replay").sum())
        item["validation"] = {
            "actual_rows": actual_rows,
            "formal_rows": formal_rows,
            "point_rows": int(len(merged)),
            "expected_rows": int(len(dims) * len(bws)),
            "ok": bool(len(merged) == len(dims) * len(bws) and actual_rows == len(merged) and formal_rows == len(merged)),
        }
        item["finished_at"] = _now()
        _write_json(out_root / "run_manifest.json", item)
        results.append(item)

    aggregate_path = data_root / f"asenoise_type0_routeA_actual_replay_{mode}_master_{ts}.csv"
    summary_path = data_root / f"asenoise_type0_routeA_actual_replay_{mode}_summary_{ts}.txt"
    manifest_path = data_root / f"asenoise_type0_routeA_actual_replay_{mode}_manifest_{ts}.json"
    if aggregate_frames:
        agg = pd.concat(aggregate_frames, ignore_index=True)
        agg.to_csv(aggregate_path, index=False)
        delta = pd.to_numeric(agg["delta_PIE_shadow_minus_actual"], errors="coerce")
        lines = [
            f"created_at: {_now()}",
            f"mode: {mode}",
            f"row_count: {len(agg)}",
            f"aggregate_csv: {aggregate_path}",
            f"mean_delta_PIE_shadow_minus_actual: {float(delta.mean()) if delta.notna().any() else 'nan'}",
            f"median_delta_PIE_shadow_minus_actual: {float(delta.median()) if delta.notna().any() else 'nan'}",
            f"max_delta_PIE_shadow_minus_actual: {float(delta.max()) if delta.notna().any() else 'nan'}",
        ]
        for label, grp in agg.groupby("dataset_label"):
            vals = pd.to_numeric(grp["SKR_secure_actual_ir_bps"], errors="coerce")
            if vals.notna().any():
                best = grp.loc[vals.idxmax()]
                lines.append(f"dataset_actual_best: dataset={label},d={int(best['dimension'])},bw={int(best['bin_width_ps'])},PIE={_safe_float(best['PIE_secure_actual_ir']):.6g},SKR={_safe_float(best['SKR_secure_actual_ir_bps']):.6g}")
        _write_text(summary_path, "\n".join(lines))
    _write_json(
        manifest_path,
        {
            "created_at": _now(),
            "mode": mode,
            "source_timestamp": str(args.source_timestamp),
            "shadow_master": str(shadow_master_path),
            "aggregate_csv": str(aggregate_path) if aggregate_frames else "",
            "summary": str(summary_path) if aggregate_frames else "",
            "results": results,
        },
    )
    print(f"[ASENOISE_ROUTEA] manifest={manifest_path}")
    if aggregate_frames:
        print(f"[ASENOISE_ROUTEA] aggregate_csv={aggregate_path}")
        print(f"[ASENOISE_ROUTEA] summary={summary_path}")
    return 0 if all(not r.get("errors") and (r.get("validation") or {}).get("ok") for r in results) else 2


def compare(args: argparse.Namespace) -> int:
    data_root = Path(args.data_root)
    replay_csv = Path(args.replay_csv) if str(args.replay_csv).strip() else data_root / f"asenoise_type0_routeA_actual_replay_full_master_{args.replay_timestamp}.csv"
    estimate_csv = Path(args.estimate_csv) if str(args.estimate_csv).strip() else data_root / f"asenoise_type0_routeA_estimated_master_{args.estimate_timestamp}.csv"
    if not replay_csv.exists():
        raise SystemExit(f"missing replay csv: {replay_csv}")
    if not estimate_csv.exists():
        raise SystemExit(f"missing estimate csv: {estimate_csv}")
    ts = str(args.timestamp or _timestamp())
    out_csv = data_root / f"asenoise_type0_routeA_actual_vs_estimate_compare_{ts}.csv"
    out_summary = data_root / f"asenoise_type0_routeA_actual_vs_estimate_compare_{ts}.txt"
    actual = pd.read_csv(replay_csv)
    est = pd.read_csv(estimate_csv)
    keep = [
        "dataset_label",
        "dimension",
        "bin_width_ps",
        "PIE_routeA_est_low",
        "PIE_routeA_est_mid",
        "PIE_routeA_est_high",
        "SKR_routeA_est_low_bps",
        "SKR_routeA_est_mid_bps",
        "SKR_routeA_est_high_bps",
    ]
    merged = actual.merge(est[[c for c in keep if c in est.columns]], on=["dataset_label", "dimension", "bin_width_ps"], how="left")
    for key in ("low", "mid", "high"):
        merged[f"delta_PIE_est_{key}_minus_actual"] = pd.to_numeric(merged[f"PIE_routeA_est_{key}"], errors="coerce") - pd.to_numeric(merged["PIE_secure_actual_ir"], errors="coerce")
        merged[f"delta_SKR_est_{key}_minus_actual_bps"] = pd.to_numeric(merged[f"SKR_routeA_est_{key}_bps"], errors="coerce") - pd.to_numeric(merged["SKR_secure_actual_ir_bps"], errors="coerce")
    merged.to_csv(out_csv, index=False)

    lines = [
        f"created_at: {_now()}",
        f"actual_replay_csv: {replay_csv}",
        f"estimate_csv: {estimate_csv}",
        f"output_csv: {out_csv}",
        f"row_count: {len(merged)}",
    ]
    for key in ("low", "mid", "high"):
        d = pd.to_numeric(merged[f"delta_PIE_est_{key}_minus_actual"], errors="coerce")
        lines.append(f"delta_PIE_est_{key}_minus_actual_mean_median_max_abs: {float(d.mean())}, {float(d.median())}, {float(d.abs().max())}")
    same_best = 0
    total = 0
    for label, grp in merged.groupby("dataset_label"):
        total += 1
        actual_skr = pd.to_numeric(grp["SKR_secure_actual_ir_bps"], errors="coerce")
        est_skr = pd.to_numeric(grp["SKR_routeA_est_mid_bps"], errors="coerce")
        actual_best = grp.loc[actual_skr.idxmax()]
        est_best = grp.loc[est_skr.idxmax()]
        same = int(int(actual_best["dimension"]) == int(est_best["dimension"]) and int(actual_best["bin_width_ps"]) == int(est_best["bin_width_ps"]))
        same_best += same
        lines.append(
            "dataset_best_shift: "
            f"dataset={label},estimate_mid=(d={int(est_best['dimension'])},bw={int(est_best['bin_width_ps'])}),"
            f"actual=(d={int(actual_best['dimension'])},bw={int(actual_best['bin_width_ps'])}),same={same},"
            f"actual_PIE={_safe_float(actual_best['PIE_secure_actual_ir']):.6g},actual_SKR={_safe_float(actual_best['SKR_secure_actual_ir_bps']):.6g}"
        )
    lines.append(f"dataset_best_stability_fraction: {same_best}/{total}")
    actual_global = merged.loc[pd.to_numeric(merged["SKR_secure_actual_ir_bps"], errors="coerce").idxmax()]
    est_global = merged.loc[pd.to_numeric(merged["SKR_routeA_est_mid_bps"], errors="coerce").idxmax()]
    lines.append(f"global_best_estimate_mid: dataset={est_global['dataset_label']},d={int(est_global['dimension'])},bw={int(est_global['bin_width_ps'])}")
    lines.append(f"global_best_actual: dataset={actual_global['dataset_label']},d={int(actual_global['dimension'])},bw={int(actual_global['bin_width_ps'])}")
    _write_text(out_summary, "\n".join(lines))
    print(f"[ASENOISE_ROUTEA] compare_csv={out_csv}")
    print(f"[ASENOISE_ROUTEA] compare_summary={out_summary}")
    return 0


def finalize_main(args: argparse.Namespace) -> int:
    path = Path(args.input_csv)
    if not path.exists():
        raise SystemExit(f"missing input csv: {path}")
    out_path = Path(args.output_csv) if str(args.output_csv).strip() else path
    backup = ""
    if out_path == path and bool(args.backup):
        backup_path = path.with_name(path.name + f".bak_finalize_main_{_timestamp()}")
        shutil.copy2(path, backup_path)
        backup = str(backup_path)
    df = pd.read_csv(path)
    if "dataset_label" in df.columns:
        df["noise"] = df["dataset_label"].astype(str)
    elif "noise" not in df.columns:
        raise SystemExit("cannot finalize ASENoise main csv without dataset_label or noise column")
    df["PIE_main"] = pd.to_numeric(df["PIE_secure_actual_ir"], errors="coerce")
    df["SKR_main_bps"] = pd.to_numeric(df["SKR_secure_actual_ir_bps"], errors="coerce")
    df["main_result_source"] = "actual_ir_finite_key"
    df["performance_proxy_role"] = "diagnostic_only"
    front_cols = [
        "noise",
        "dataset_label" if "dataset_label" in df.columns else "",
        "dimension",
        "bin_width_ps",
        "PIE_main",
        "SKR_main_bps",
        "main_result_source",
        "PIE_secure_actual_ir",
        "SKR_secure_actual_ir_bps",
    ]
    front_cols = [c for c in front_cols if c and c in df.columns]
    rest_cols = [c for c in df.columns if c not in front_cols and c != "loss_db"]
    df = df[[*front_cols, *rest_cols]]
    df.to_csv(out_path, index=False)
    summary_path = out_path.with_suffix(out_path.suffix + ".main_summary.txt")
    missing_main = int(pd.to_numeric(df["PIE_main"], errors="coerce").isna().sum() + pd.to_numeric(df["SKR_main_bps"], errors="coerce").isna().sum())
    lines = [
        f"created_at: {_now()}",
        f"input_csv: {path}",
        f"output_csv: {out_path}",
        f"backup_csv: {backup or 'none'}",
        f"row_count: {len(df)}",
        f"missing_main_numeric_values: {missing_main}",
        "default_main_columns: PIE_main, SKR_main_bps",
        "default_main_source: PIE_secure_actual_ir, SKR_secure_actual_ir_bps",
        "performance_proxy_role: diagnostic_only",
    ]
    _write_text(summary_path, "\n".join(lines))
    print(f"[ASENOISE_ROUTEA] finalized_main_csv={out_path}")
    print(f"[ASENOISE_ROUTEA] main_summary={summary_path}")
    if backup:
        print(f"[ASENOISE_ROUTEA] backup_csv={backup}")
    return 0 if missing_main == 0 else 2


def main() -> int:
    ap = argparse.ArgumentParser(description="ASENoise Route A estimate and actual replay runner.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    est = sub.add_parser("estimate")
    est.add_argument("--data-root", default=str(DATA_ROOT_DEFAULT))
    est.add_argument("--source-timestamp", default=SOURCE_TIMESTAMP_DEFAULT)
    est.add_argument("--input-csv", default="")
    est.add_argument("--timestamp", default="")
    est.set_defaults(func=estimate)

    rep = sub.add_parser("replay")
    rep.add_argument("--data-root", default=str(DATA_ROOT_DEFAULT))
    rep.add_argument("--source-timestamp", default=SOURCE_TIMESTAMP_DEFAULT)
    rep.add_argument("--timestamp", default="")
    rep.add_argument("--mode", choices=["smoke", "full"], default="smoke")
    rep.add_argument("--datasets", default="")
    rep.add_argument("--shards", type=int, default=12)
    rep.add_argument("--workers", type=int, default=12)
    rep.add_argument("--overwrite", action="store_true")
    rep.set_defaults(func=replay)

    cmp_ap = sub.add_parser("compare")
    cmp_ap.add_argument("--data-root", default=str(DATA_ROOT_DEFAULT))
    cmp_ap.add_argument("--replay-timestamp", default="")
    cmp_ap.add_argument("--estimate-timestamp", default="")
    cmp_ap.add_argument("--replay-csv", default="")
    cmp_ap.add_argument("--estimate-csv", default="")
    cmp_ap.add_argument("--timestamp", default="")
    cmp_ap.set_defaults(func=compare)

    fin = sub.add_parser("finalize-main")
    fin.add_argument("--input-csv", required=True)
    fin.add_argument("--output-csv", default="")
    fin.add_argument("--backup", action="store_true")
    fin.set_defaults(func=finalize_main)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
