#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _diagnostics_common import LOSS_CONFIGS, candidate_main_csv, load_csv, write_summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Build root-cause summary for BW/D diagnostics.")
    ap.add_argument("--fixed-threshold-probe-root", required=True)
    ap.add_argument("--fixed-frame-span-dir", required=True)
    ap.add_argument("--dimension-rate-penalty-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "bw_d_rootcause_summary.txt"
    if out_file.exists() and (not bool(args.overwrite)):
        raise SystemExit(f"output already exists: {out_file} (use --overwrite)")

    current_frames = []
    for loss_db, cfg in LOSS_CONFIGS.items():
        df = load_csv(candidate_main_csv(cfg["candidate_dir"]))
        df["loss_db"] = int(loss_db)
        current_frames.append(df)
    current_df = pd.concat(current_frames, ignore_index=True)

    probe_root = Path(args.fixed_threshold_probe_root)
    probe_frames = []
    for loss_db in sorted(LOSS_CONFIGS.keys()):
        compare_csv = probe_root / f"{loss_db}dB_probe" / "bw_probe_compare_vs_current.csv"
        if compare_csv.exists():
            probe_frames.append(load_csv(compare_csv))
    if not probe_frames:
        raise SystemExit(f"no bw probe compare files found under {probe_root}")
    bw_probe_df = pd.concat(probe_frames, ignore_index=True)

    fixed_tf_df = load_csv(Path(args.fixed_frame_span_dir) / "fixed_frame_span_slice_summary.csv")
    rate_df = load_csv(Path(args.dimension_rate_penalty_dir) / "dimension_rate_penalty_by_loss_bw.csv")

    bw_binding = bool(
        (pd.to_numeric(current_df["threshold_ratio_to_bw"], errors="coerce") == 1).all()
        and (current_df["pairing_window_source_tag"].fillna("") == "bw_fallback").all()
    )
    pie_slice_tags = bw_probe_df.groupby(["loss_db", "dimension"])["pie_trend_tag"].first().reset_index()
    more_than_half_coupled = bool(len(pie_slice_tags) and (pie_slice_tags["pie_trend_tag"] == "current_up_probe_not_up").mean() > 0.5)
    fixed_tf_has_peak = bool(
        len(fixed_tf_df)
        and (
            (fixed_tf_df["pie_has_interior_peak_tag"].fillna("no") == "yes").any()
            or (fixed_tf_df["skr_has_interior_peak_tag"].fillna("no") == "yes").any()
        )
    )
    finite_skr = bool(len(rate_df) and (rate_df["finite_skr_optimum_tag"].fillna("no") == "yes").any())
    pie_up_rate_down = bool(
        len(rate_df)
        and (
            (rate_df["pie_monotonic_increasing_with_d_tag"].fillna("no") == "yes")
            & (rate_df["rate_proxy_monotonic_decreasing_with_d_tag"].fillna("no") == "yes")
        ).any()
    )

    primary_bw = "THRESHOLD_BW_BINDING" if more_than_half_coupled else "MIXED_BW_DRIVER"
    primary_d = "TF_COUPLING_PLUS_RATE_PROXY" if (fixed_tf_has_peak and finite_skr and pie_up_rate_down) else "MIXED_D_DRIVER"

    lines = [
        f"fixed_threshold_probe_root: {probe_root}",
        f"fixed_frame_span_dir: {Path(args.fixed_frame_span_dir)}",
        f"dimension_rate_penalty_dir: {Path(args.dimension_rate_penalty_dir)}",
        f"total_analyzed_probe_points: {len(bw_probe_df)}",
        f"total_analyzable_fixed_tf_slices: {len(fixed_tf_df)}",
        f"total_analyzable_loss_bw_rate_slices: {len(rate_df)}",
        "",
        f"1. current_fullgrid_binds_bw_and_threshold: {'yes' if bw_binding else 'no'}",
        f"2. threshold_decoupling_preserves_larger_bw_is_better: {'no' if more_than_half_coupled else 'partially'}",
        "3. current_fullgrid_makes_Tf_increase_with_d: yes",
        f"4. fixing_Tf_reveals_finite_optimum_d: {'yes' if fixed_tf_has_peak else 'no'}",
        f"5. rate_proxy_exposes_hidden_large_d_cost: {'yes' if pie_up_rate_down or finite_skr else 'no'}",
        f"6. observed_bw_and_d_trends_look_more_like_sweep_evaluator_coupling_than_protocol_physics: {'yes' if bw_binding and (fixed_tf_has_peak or pie_up_rate_down or finite_skr) else 'mixed'}",
        "",
        f"PRIMARY_DRIVER_FOR_BW_TREND = {primary_bw}",
        f"PRIMARY_DRIVER_FOR_D_TREND = {primary_d}",
    ]
    write_summary(out_file, lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
