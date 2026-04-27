#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SECURITY_REPORTS = REPO_ROOT / "tools" / "security_reports"
for _p in (REPO_ROOT, SECURITY_REPORTS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from _diagnostics_common import (
    LOSS_CONFIGS,
    REPO_ROOT,
    candidate_diag_csv,
    candidate_main_csv,
    ensure_output_dir,
    load_csv,
    monotonic_increasing,
    normalize_numeric,
    parse_int_csv,
    tol_for_values,
    write_summary,
)

MAIN_NUMERIC_COLS = [
    "dimension",
    "bin_width_ps",
    "threshold_ps",
    "effective_pairing_window_ps",
    "raw_ser",
    "map_ser",
    "coincidence_rate_hz",
    "layers_success_best",
    "best_hard_PIE",
    "PIE_practical",
    "SKR_measured_bps",
    "n_pairs_actual",
    "near_neighbor_frac",
    "frame_diag_available",
]

DIAG_NUMERIC_COLS = [
    "dimension",
    "bin_width_ps",
    "raw_ser",
    "near_neighbor_frac",
    "n_pairs_actual",
    "frame_diag_available",
]

COMPARE_COLS = [
    "loss_db",
    "dimension",
    "bin_width_ps",
    "current_threshold_ps",
    "probe_threshold_ps",
    "current_effective_pairing_window_ps",
    "probe_effective_pairing_window_ps",
    "current_pairing_window_source_tag",
    "probe_pairing_window_source_tag",
    "current_raw_ser",
    "probe_raw_ser",
    "delta_raw_ser",
    "current_map_ser",
    "probe_map_ser",
    "delta_map_ser",
    "current_coincidence_rate_hz",
    "probe_coincidence_rate_hz",
    "delta_coincidence_rate_hz",
    "current_layers_success_best",
    "probe_layers_success_best",
    "delta_layers_success_best",
    "current_best_hard_PIE",
    "probe_best_hard_PIE",
    "delta_best_hard_PIE",
    "current_PIE_practical",
    "probe_PIE_practical",
    "delta_PIE_practical",
    "current_SKR_measured_bps",
    "probe_SKR_measured_bps",
    "delta_SKR_measured_bps",
    "current_frame_diag_available",
    "probe_frame_diag_available",
    "stage_change_tag",
    "pie_trend_tag",
]


def _parse_threshold_list(args: argparse.Namespace) -> list[int]:
    if args.threshold_list:
        vals = parse_int_csv(args.threshold_list, name="threshold-list")
    else:
        vals = [int(round(float(args.fixed_threshold_ps)))]
    vals = [int(v) for v in vals]
    if not vals or any(v <= 0 for v in vals):
        raise SystemExit("threshold values must be > 0")
    return vals


def _load_enriched_results(root: Path) -> pd.DataFrame:
    main = normalize_numeric(load_csv(candidate_main_csv(root)), MAIN_NUMERIC_COLS)
    diag_path = candidate_diag_csv(root)
    if diag_path.exists():
        diag = normalize_numeric(load_csv(diag_path), DIAG_NUMERIC_COLS)
        keep = [c for c in ["dimension", "bin_width_ps", "raw_ser", "near_neighbor_frac", "n_pairs_actual", "frame_diag_available"] if c in diag.columns]
        if keep:
            main = main.merge(diag[keep].drop_duplicates(["dimension", "bin_width_ps"]), on=["dimension", "bin_width_ps"], how="left", suffixes=("", "_diag"))
            for col in ("raw_ser", "near_neighbor_frac", "n_pairs_actual", "frame_diag_available"):
                diag_col = f"{col}_diag"
                if diag_col in main.columns:
                    if col not in main.columns:
                        main[col] = main[diag_col]
                    else:
                        main[col] = main[col].where(pd.notna(main[col]), main[diag_col])
                    main = main.drop(columns=[diag_col])
    return main


def _trend_tag(current_up: bool, probe_up: bool) -> str:
    if current_up and probe_up:
        return "current_up_probe_up"
    if current_up and (not probe_up):
        return "current_up_probe_not_up"
    if (not current_up) and probe_up:
        return "current_not_up_probe_up"
    return "current_not_up_probe_not_up"


def _stage_change(row: pd.Series) -> str:
    stage_order = [
        ("raw_ser", row.get("delta_raw_ser")),
        ("map_ser", row.get("delta_map_ser")),
        ("layers_success_best", row.get("delta_layers_success_best")),
        ("best_hard_PIE", row.get("delta_best_hard_PIE")),
        ("PIE_practical", row.get("delta_PIE_practical")),
        ("SKR_measured_bps", row.get("delta_SKR_measured_bps")),
    ]
    for name, value in stage_order:
        if pd.isna(value):
            continue
        if abs(float(value)) > tol_for_values(float(value)):
            return name
    return "unchanged"


def _best_bw(df: pd.DataFrame, col: str) -> str:
    valid = df[pd.notna(df[col])]
    if len(valid) == 0:
        return ""
    row = valid.loc[valid[col].idxmax()]
    return str(int(row["bin_width_ps"]))


def _slice_rows(df: pd.DataFrame, dim: int) -> pd.DataFrame:
    return df[df["dimension"] == dim].sort_values("bin_width_ps")


def _subset(df: pd.DataFrame, dimensions: list[int], bin_widths: list[int]) -> pd.DataFrame:
    return df[df["dimension"].isin(dimensions) & df["bin_width_ps"].isin(bin_widths)].copy()


def _run_single_threshold(
    *,
    loss_db: int,
    dimensions: list[int],
    bin_widths: list[int],
    threshold_ps: int,
    threshold_root: Path,
    jobs: int,
    extract_workers: int,
) -> None:
    cfg = LOSS_CONFIGS[int(loss_db)]
    loss_root = threshold_root / f"loss_{loss_db}dB"
    ensure_output_dir(loss_root, overwrite=True)

    dims_s = ",".join(str(x) for x in dimensions)
    bws_s = ",".join(str(x) for x in bin_widths)
    cmd = [
        sys.executable,
        str(REPO_ROOT / "experiments" / "run_e2e_pipeline.py"),
        "--grid-table", str(cfg["grid_table"]),
        "--ttbin", str(cfg["ttbin"]),
        "--ttbin-ch-a-override", "1",
        "--ttbin-ch-b-override", "5",
        "--dims", dims_s,
        "--bws", bws_s,
        "--materialize-processing-rule-version", "pairing_v2",
        "--coinc-window-override-ps", str(threshold_ps),
        "--jobs", str(max(1, int(jobs))),
        "--extract-workers", str(max(1, int(extract_workers))),
        "--out-root", str(loss_root),
    ]
    print("[FIXED_THRESHOLD] running:", " ".join(cmd))
    rc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if rc.returncode != 0:
        raise SystemExit(rc.returncode)

    probe_main = loss_root / "polar_e2e_results.csv"
    shutil.copy2(probe_main, loss_root / "polar_e2e_results_probe.csv")

    current_df = _subset(_load_enriched_results(Path(cfg["candidate_dir"])), dimensions, bin_widths)
    probe_df = _subset(_load_enriched_results(loss_root), dimensions, bin_widths)

    merged = current_df.merge(probe_df, on=["dimension", "bin_width_ps"], how="outer", suffixes=("_current", "_probe"))
    merged["loss_db"] = int(loss_db)
    merged["current_threshold_ps"] = merged.get("threshold_ps_current")
    merged["probe_threshold_ps"] = merged.get("threshold_ps_probe")
    merged["current_effective_pairing_window_ps"] = merged.get("effective_pairing_window_ps_current")
    merged["probe_effective_pairing_window_ps"] = merged.get("effective_pairing_window_ps_probe")
    merged["current_pairing_window_source_tag"] = merged.get("pairing_window_source_tag_current")
    merged["probe_pairing_window_source_tag"] = merged.get("pairing_window_source_tag_probe")
    merged["current_raw_ser"] = merged.get("raw_ser_current")
    merged["probe_raw_ser"] = merged.get("raw_ser_probe")
    merged["delta_raw_ser"] = merged["probe_raw_ser"] - merged["current_raw_ser"]
    merged["current_map_ser"] = merged.get("map_ser_current")
    merged["probe_map_ser"] = merged.get("map_ser_probe")
    merged["delta_map_ser"] = merged["probe_map_ser"] - merged["current_map_ser"]
    merged["current_coincidence_rate_hz"] = merged.get("coincidence_rate_hz_current")
    merged["probe_coincidence_rate_hz"] = merged.get("coincidence_rate_hz_probe")
    merged["delta_coincidence_rate_hz"] = merged["probe_coincidence_rate_hz"] - merged["current_coincidence_rate_hz"]
    merged["current_layers_success_best"] = merged.get("layers_success_best_current")
    merged["probe_layers_success_best"] = merged.get("layers_success_best_probe")
    merged["delta_layers_success_best"] = merged["probe_layers_success_best"] - merged["current_layers_success_best"]
    merged["current_best_hard_PIE"] = merged.get("best_hard_PIE_current")
    merged["probe_best_hard_PIE"] = merged.get("best_hard_PIE_probe")
    merged["delta_best_hard_PIE"] = merged["probe_best_hard_PIE"] - merged["current_best_hard_PIE"]
    merged["current_PIE_practical"] = merged.get("PIE_practical_current")
    merged["probe_PIE_practical"] = merged.get("PIE_practical_probe")
    merged["delta_PIE_practical"] = merged["probe_PIE_practical"] - merged["current_PIE_practical"]
    merged["current_SKR_measured_bps"] = merged.get("SKR_measured_bps_current")
    merged["probe_SKR_measured_bps"] = merged.get("SKR_measured_bps_probe")
    merged["delta_SKR_measured_bps"] = merged["probe_SKR_measured_bps"] - merged["current_SKR_measured_bps"]
    merged["current_frame_diag_available"] = merged.get("frame_diag_available_current")
    merged["probe_frame_diag_available"] = merged.get("frame_diag_available_probe")
    merged["pie_trend_tag"] = ""
    merged["stage_change_tag"] = merged.apply(_stage_change, axis=1)

    weakened: list[str] = []
    unchanged: list[str] = []
    reversed_dims: list[str] = []
    still_large_bw: list[str] = []
    stage_counts: dict[str, int] = {}
    summary_lines = [
        f"loss_db: {loss_db}",
        f"current_main: {candidate_main_csv(Path(cfg['candidate_dir']))}",
        f"probe_main: {probe_main}",
        f"probe_diag: {candidate_diag_csv(loss_root)}",
        f"point_count: {len(merged)}",
        f"dimensions: {','.join(str(x) for x in dimensions)}",
        f"bin_widths: {','.join(str(x) for x in bin_widths)}",
        f"threshold_ps: {threshold_ps}",
        "",
    ]
    for dim in sorted(int(x) for x in merged["dimension"].dropna().unique()):
        sl = _slice_rows(merged, dim)
        current_pie = [float(v) for v in sl["current_PIE_practical"].tolist() if pd.notna(v)]
        probe_pie = [float(v) for v in sl["probe_PIE_practical"].tolist() if pd.notna(v)]
        current_up = monotonic_increasing(current_pie)
        probe_up = monotonic_increasing(probe_pie)
        tag = _trend_tag(current_up, probe_up)
        merged.loc[merged["dimension"] == dim, "pie_trend_tag"] = tag
        if current_up and not probe_up:
            weakened.append(f"d={dim}")
            reversed_dims.append(f"d={dim}")
        elif current_up == probe_up:
            unchanged.append(f"d={dim}")
        if probe_up:
            still_large_bw.append(f"d={dim}")

        stage_mode = sl["stage_change_tag"].value_counts(dropna=True)
        top_stage = str(stage_mode.index[0]) if len(stage_mode) else "unchanged"
        stage_counts[top_stage] = stage_counts.get(top_stage, 0) + 1
        summary_lines.extend(
            [
                f"dimension {dim}",
                f"  current_pie_monotonic_increasing: {'yes' if current_up else 'no'}",
                f"  probe_pie_monotonic_increasing: {'yes' if probe_up else 'no'}",
                f"  best_probe_pie_bw: {_best_bw(sl, 'probe_PIE_practical')}",
                f"  best_probe_skr_bw: {_best_bw(sl, 'probe_SKR_measured_bps')}",
                f"  dominant_stage_change: {top_stage}",
            ]
        )

    summary_lines.extend(
        [
            "",
            f"coupled_pie_near_monotonic_dims: {','.join(still_large_bw) if still_large_bw else '(none)'}",
            f"decoupling_weakened_large_bw_dims: {','.join(weakened) if weakened else '(none)'}",
            f"decoupling_reversed_large_bw_dims: {','.join(reversed_dims) if reversed_dims else '(none)'}",
            f"probe_still_monotonic_dims: {','.join(still_large_bw) if still_large_bw else '(none)'}",
            f"stage_change_counts: {stage_counts}",
        ]
    )

    merged = merged.sort_values(["dimension", "bin_width_ps"])
    merged[COMPARE_COLS].to_csv(loss_root / "fixed_threshold_compare_vs_current.csv", index=False)
    write_summary(loss_root / "fixed_threshold_probe_summary.txt", summary_lines)


def _build_threshold_sweep_summary(output_root: Path, thresholds: list[int], losses: list[int]) -> None:
    rows: list[pd.DataFrame] = []
    for threshold_ps in thresholds:
        threshold_root = output_root / f"fixed_threshold_{threshold_ps}ps"
        for loss_db in losses:
            probe_main = threshold_root / f"loss_{loss_db}dB" / "polar_e2e_results_probe.csv"
            if not probe_main.exists():
                continue
            df = _load_enriched_results(threshold_root / f"loss_{loss_db}dB")
            df = df[[c for c in ["dimension", "bin_width_ps", "PIE_practical", "SKR_measured_bps", "map_ser", "layers_success_best"] if c in df.columns]].copy()
            df["loss_db"] = int(loss_db)
            df["threshold_ps"] = int(threshold_ps)
            rows.append(df)
    if rows:
        out = pd.concat(rows, ignore_index=True)
        out = out[["loss_db", "dimension", "bin_width_ps", "threshold_ps", "PIE_practical", "SKR_measured_bps", "map_ser", "layers_success_best"]]
        out.to_csv(output_root / "threshold_sweep_summary.csv", index=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run fixed-threshold probe on pairing_v2 candidate points.")
    ap.add_argument("--losses", default="6,10,16,20")
    ap.add_argument("--dimensions", default="256,512,1024,2048")
    ap.add_argument("--bin-widths", default="20,30,40,50,60,80,100,120,150,180,200")
    ap.add_argument("--fixed-threshold-ps", type=float, default=30.0)
    ap.add_argument("--threshold-list", default="")
    ap.add_argument("--output-root", default=str(REPO_ROOT / "results" / "_tmp_fixed_threshold_probe"))
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--extract-workers", type=int, default=6)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    losses = parse_int_csv(args.losses, name="losses")
    dimensions = parse_int_csv(args.dimensions, name="dimensions")
    bin_widths = parse_int_csv(args.bin_widths, name="bin-widths")
    thresholds = _parse_threshold_list(args)

    output_root = Path(args.output_root)
    ensure_output_dir(output_root, overwrite=bool(args.overwrite))

    for threshold_ps in thresholds:
        threshold_root = output_root / f"fixed_threshold_{threshold_ps}ps"
        ensure_output_dir(threshold_root, overwrite=True)
        for loss_db in losses:
            _run_single_threshold(
                loss_db=int(loss_db),
                dimensions=dimensions,
                bin_widths=bin_widths,
                threshold_ps=int(threshold_ps),
                threshold_root=threshold_root,
                jobs=int(args.jobs),
                extract_workers=int(args.extract_workers),
            )
    if len(thresholds) > 1:
        _build_threshold_sweep_summary(output_root, thresholds, losses)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

