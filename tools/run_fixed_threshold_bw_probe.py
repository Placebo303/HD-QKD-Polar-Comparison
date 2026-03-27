#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

from _diagnostics_common import (
    LOSS_CONFIGS,
    REPO_ROOT,
    candidate_main_csv,
    ensure_output_dir,
    load_csv,
    monotonic_increasing,
    normalize_numeric,
    parse_int_csv,
    write_summary,
)

NUMERIC_COLS = [
    "dimension",
    "bin_width_ps",
    "threshold_ps",
    "effective_pairing_window_ps",
    "map_ser",
    "coincidence_rate_hz",
    "layers_success_best",
    "PIE_practical",
    "SKR_measured_bps",
]


def _trend_tag(current_up: bool, probe_up: bool) -> str:
    if current_up and probe_up:
        return "current_up_probe_up"
    if current_up and (not probe_up):
        return "current_up_probe_not_up"
    if (not current_up) and probe_up:
        return "current_not_up_probe_up"
    return "current_not_up_probe_not_up"


def _verdict(current_up: bool, probe_up: bool) -> str:
    if current_up and (not probe_up):
        return "reversed"
    if current_up == probe_up:
        return "unchanged"
    return "weakened"


def _argmax_row(df: pd.DataFrame, col: str) -> pd.Series:
    valid = df[pd.notna(df[col])]
    if len(valid) == 0:
        return df.iloc[0]
    return valid.loc[valid[col].idxmax()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Run fixed-threshold BW probe on pairing_v2 candidate points.")
    ap.add_argument("--losses", default="6,10,16,20")
    ap.add_argument("--dimensions", default="256,512,1024,2048")
    ap.add_argument("--bin-widths", default="20,30,40,50,60,80,100,120,150,180,200")
    ap.add_argument("--fixed-threshold-ps", type=float, default=20.0)
    ap.add_argument("--output-root", default=str(REPO_ROOT / "results" / "_tmp_bw_d_rootcause" / "fixed_threshold_bw_probe"))
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--extract-workers", type=int, default=6)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    losses = parse_int_csv(args.losses, name="losses")
    dimensions = parse_int_csv(args.dimensions, name="dimensions")
    bin_widths = parse_int_csv(args.bin_widths, name="bin-widths")
    fixed_threshold_ps = int(round(float(args.fixed_threshold_ps)))
    if fixed_threshold_ps <= 0:
        raise SystemExit("--fixed-threshold-ps must be > 0")

    output_root = Path(args.output_root)
    ensure_output_dir(output_root, overwrite=bool(args.overwrite))

    dims_s = ",".join(str(x) for x in dimensions)
    bws_s = ",".join(str(x) for x in bin_widths)
    aggregate_lines = [
        f"output_root: {output_root}",
        f"losses: {','.join(str(x) for x in losses)}",
        f"dimensions: {dims_s}",
        f"bin_widths: {bws_s}",
        f"fixed_threshold_ps: {fixed_threshold_ps}",
        "",
    ]

    for loss_db in losses:
        cfg = LOSS_CONFIGS[int(loss_db)]
        probe_root = output_root / f"{loss_db}dB_probe"
        ensure_output_dir(probe_root, overwrite=True)

        cmd = [
            sys.executable,
            str(REPO_ROOT / "experiments" / "run_e2e_pipeline.py"),
            "--grid-table",
            str(cfg["grid_table"]),
            "--ttbin",
            str(cfg["ttbin"]),
            "--ttbin-ch-a-override",
            "1",
            "--ttbin-ch-b-override",
            "5",
            "--dims",
            dims_s,
            "--bws",
            bws_s,
            "--materialize-processing-rule-version",
            "pairing_v2",
            "--coinc-window-override-ps",
            str(fixed_threshold_ps),
            "--jobs",
            str(max(1, int(args.jobs))),
            "--extract-workers",
            str(max(1, int(args.extract_workers))),
            "--out-root",
            str(probe_root),
        ]
        print("[BW_PROBE] running:", " ".join(cmd))
        rc = subprocess.run(cmd, cwd=str(REPO_ROOT))
        if rc.returncode != 0:
            raise SystemExit(rc.returncode)

        probe_main = probe_root / "polar_e2e_results.csv"
        shutil.copy2(probe_main, probe_root / "polar_e2e_results_probe.csv")

        current_df = normalize_numeric(load_csv(candidate_main_csv(cfg["candidate_dir"])), NUMERIC_COLS)
        probe_df = normalize_numeric(load_csv(probe_main), NUMERIC_COLS)
        current_df = current_df[current_df["dimension"].isin(dimensions) & current_df["bin_width_ps"].isin(bin_widths)].copy()
        probe_df = probe_df[probe_df["dimension"].isin(dimensions) & probe_df["bin_width_ps"].isin(bin_widths)].copy()

        merged = current_df.merge(probe_df, on=["dimension", "bin_width_ps"], how="outer", suffixes=("_current", "_probe"))
        merged["loss_db"] = int(loss_db)
        merged["fixed_threshold_ps"] = int(fixed_threshold_ps)
        merged["current_threshold_ps"] = merged.get("threshold_ps_current")
        merged["probe_threshold_ps"] = merged.get("threshold_ps_probe")
        merged["current_effective_pairing_window_ps"] = merged.get("effective_pairing_window_ps_current")
        merged["probe_effective_pairing_window_ps"] = merged.get("effective_pairing_window_ps_probe")
        merged["current_pairing_window_source_tag"] = merged.get("pairing_window_source_tag_current")
        merged["probe_pairing_window_source_tag"] = merged.get("pairing_window_source_tag_probe")
        merged["current_map_ser"] = merged.get("map_ser_current")
        merged["probe_map_ser"] = merged.get("map_ser_probe")
        merged["delta_map_ser"] = merged["probe_map_ser"] - merged["current_map_ser"]
        merged["current_coincidence_rate_hz"] = merged.get("coincidence_rate_hz_current")
        merged["probe_coincidence_rate_hz"] = merged.get("coincidence_rate_hz_probe")
        merged["delta_coincidence_rate_hz"] = merged["probe_coincidence_rate_hz"] - merged["current_coincidence_rate_hz"]
        merged["current_layers_success_best"] = merged.get("layers_success_best_current")
        merged["probe_layers_success_best"] = merged.get("layers_success_best_probe")
        merged["delta_layers_success_best"] = merged["probe_layers_success_best"] - merged["current_layers_success_best"]
        merged["current_PIE_practical"] = merged.get("PIE_practical_current")
        merged["probe_PIE_practical"] = merged.get("PIE_practical_probe")
        merged["delta_PIE_practical"] = merged["probe_PIE_practical"] - merged["current_PIE_practical"]
        merged["current_SKR_measured_bps"] = merged.get("SKR_measured_bps_current")
        merged["probe_SKR_measured_bps"] = merged.get("SKR_measured_bps_probe")
        merged["delta_SKR_measured_bps"] = merged["probe_SKR_measured_bps"] - merged["current_SKR_measured_bps"]
        merged["pie_trend_tag"] = ""
        merged["skr_trend_tag"] = ""

        summary_lines = [
            f"loss_db: {loss_db}",
            f"current_main: {candidate_main_csv(cfg['candidate_dir'])}",
            f"probe_main: {probe_main}",
            f"point_count: {len(merged)}",
            f"fixed_threshold_ps: {fixed_threshold_ps}",
            "",
        ]
        for dim in sorted(merged["dimension"].dropna().astype(int).unique()):
            sl = merged[merged["dimension"] == dim].sort_values("bin_width_ps")
            current_pie = [float(v) for v in sl["current_PIE_practical"].tolist() if pd.notna(v)]
            probe_pie = [float(v) for v in sl["probe_PIE_practical"].tolist() if pd.notna(v)]
            current_skr = [float(v) for v in sl["current_SKR_measured_bps"].tolist() if pd.notna(v)]
            probe_skr = [float(v) for v in sl["probe_SKR_measured_bps"].tolist() if pd.notna(v)]
            current_pie_up = monotonic_increasing(current_pie)
            probe_pie_up = monotonic_increasing(probe_pie)
            current_skr_up = monotonic_increasing(current_skr)
            probe_skr_up = monotonic_increasing(probe_skr)
            merged.loc[merged["dimension"] == dim, "pie_trend_tag"] = _trend_tag(current_pie_up, probe_pie_up)
            merged.loc[merged["dimension"] == dim, "skr_trend_tag"] = _trend_tag(current_skr_up, probe_skr_up)
            best_probe_pie_row = _argmax_row(sl, "probe_PIE_practical")
            best_probe_skr_row = _argmax_row(sl, "probe_SKR_measured_bps")
            summary_lines.extend(
                [
                    f"dimension {dim}",
                    f"  current_pie_monotonic_increasing: {'yes' if current_pie_up else 'no'}",
                    f"  probe_pie_monotonic_increasing: {'yes' if probe_pie_up else 'no'}",
                    f"  best_probe_pie_bw: {int(best_probe_pie_row['bin_width_ps'])}",
                    f"  best_probe_skr_bw: {int(best_probe_skr_row['bin_width_ps'])}",
                    f"  pie_trend_verdict: {_verdict(current_pie_up, probe_pie_up)}",
                    f"  skr_trend_verdict: {_verdict(current_skr_up, probe_skr_up)}",
                ]
            )
        pie_slice_tags = merged.groupby("dimension")["pie_trend_tag"].first().tolist()
        if any(str(v) == "current_up_probe_not_up" for v in pie_slice_tags):
            loss_conclusion = "threshold decoupling materially weakens or reverses the larger-bw trend in at least part of this loss."
        else:
            loss_conclusion = "threshold decoupling does not clearly remove the larger-bw trend in this loss."
        summary_lines.extend(["", f"loss_conclusion: {loss_conclusion}"])

        keep_cols = [
            "loss_db",
            "dimension",
            "bin_width_ps",
            "fixed_threshold_ps",
            "current_threshold_ps",
            "probe_threshold_ps",
            "current_effective_pairing_window_ps",
            "probe_effective_pairing_window_ps",
            "current_pairing_window_source_tag",
            "probe_pairing_window_source_tag",
            "current_map_ser",
            "probe_map_ser",
            "delta_map_ser",
            "current_coincidence_rate_hz",
            "probe_coincidence_rate_hz",
            "delta_coincidence_rate_hz",
            "current_layers_success_best",
            "probe_layers_success_best",
            "delta_layers_success_best",
            "current_PIE_practical",
            "probe_PIE_practical",
            "delta_PIE_practical",
            "current_SKR_measured_bps",
            "probe_SKR_measured_bps",
            "delta_SKR_measured_bps",
            "pie_trend_tag",
            "skr_trend_tag",
        ]
        merged.sort_values(["dimension", "bin_width_ps"])[keep_cols].to_csv(probe_root / "bw_probe_compare_vs_current.csv", index=False)
        write_summary(probe_root / "bw_probe_summary.txt", summary_lines)
        aggregate_lines.extend(summary_lines)
        aggregate_lines.extend(["", "=" * 60, ""])

    write_summary(output_root / "bw_probe_summary.txt", aggregate_lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
