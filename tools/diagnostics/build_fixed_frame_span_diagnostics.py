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
from pathlib import Path

import numpy as np
import pandas as pd

from _diagnostics_common import (
    REPO_ROOT,
    candidate_main_csv,
    ensure_output_dir,
    has_interior_peak,
    infer_loss_db_from_dir,
    load_csv,
    monotonic_increasing,
    normalize_numeric,
    write_summary,
)

NUMERIC_COLS = [
    "dimension",
    "bin_width_ps",
    "map_ser",
    "coincidence_rate_hz",
    "layers_success_best",
    "best_hard_PIE",
    "chi_E",
    "PIE_practical",
    "SKR_measured_bps",
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Build fixed-frame-span diagnostics from pairing_v2 candidate results.")
    ap.add_argument("--input-dirs", nargs="+", required=True)
    ap.add_argument("--output-dir", default=str(REPO_ROOT / "results" / "_tmp_bw_d_rootcause" / "fixed_frame_span"))
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))

    point_frames: list[pd.DataFrame] = []
    input_paths: list[str] = []
    for item in args.input_dirs:
        inp = Path(item)
        main_csv = candidate_main_csv(inp)
        input_paths.append(str(main_csv))
        df = normalize_numeric(load_csv(main_csv), NUMERIC_COLS)
        df["loss_db"] = infer_loss_db_from_dir(inp)
        df["frame_span_ps"] = df["dimension"] * df["bin_width_ps"]
        df["log2_dimension"] = np.log2(df["dimension"])
        df["is_positive_pie"] = df["PIE_practical"] > 0
        df["is_positive_skr"] = df["SKR_measured_bps"] > 0
        point_frames.append(
            df[
                [
                    "loss_db",
                    "dimension",
                    "bin_width_ps",
                    "frame_span_ps",
                    "log2_dimension",
                    "map_ser",
                    "coincidence_rate_hz",
                    "layers_success_best",
                    "best_hard_PIE",
                    "chi_E",
                    "PIE_practical",
                    "SKR_measured_bps",
                    "is_positive_pie",
                    "is_positive_skr",
                ]
            ]
        )

    point_df = pd.concat(point_frames, ignore_index=True).sort_values(["loss_db", "frame_span_ps", "dimension"])
    point_df.to_csv(output_dir / "fixed_frame_span_point_table.csv", index=False)

    slice_rows: list[dict[str, object]] = []
    skipped_slices = 0
    for (loss_db, frame_span_ps), grp in point_df.groupby(["loss_db", "frame_span_ps"], sort=True):
        grp = grp.sort_values("dimension")
        unique_dims = sorted(set(int(x) for x in grp["dimension"].dropna().tolist()))
        if len(unique_dims) < 3:
            skipped_slices += 1
            continue
        pie_vals = [float(x) for x in grp["PIE_practical"].tolist()]
        skr_vals = [float(x) for x in grp["SKR_measured_bps"].tolist()]
        pie_idx = int(np.nanargmax(np.asarray(pie_vals, dtype=float)))
        skr_idx = int(np.nanargmax(np.asarray(skr_vals, dtype=float)))
        slice_rows.append(
            {
                "loss_db": int(loss_db),
                "frame_span_ps": int(frame_span_ps),
                "n_points_in_slice": int(len(grp)),
                "n_dimensions_in_slice": int(len(unique_dims)),
                "min_dimension": int(min(unique_dims)),
                "max_dimension": int(max(unique_dims)),
                "best_pie_dimension": int(grp.iloc[pie_idx]["dimension"]),
                "best_pie_value": float(grp.iloc[pie_idx]["PIE_practical"]),
                "best_skr_dimension": int(grp.iloc[skr_idx]["dimension"]),
                "best_skr_value": float(grp.iloc[skr_idx]["SKR_measured_bps"]),
                "pie_monotonic_increasing_tag": "yes" if monotonic_increasing(pie_vals) else "no",
                "skr_monotonic_increasing_tag": "yes" if monotonic_increasing(skr_vals) else "no",
                "pie_has_interior_peak_tag": "yes" if has_interior_peak(unique_dims, pie_vals) else "no",
                "skr_has_interior_peak_tag": "yes" if has_interior_peak(unique_dims, skr_vals) else "no",
            }
        )
    slice_df = pd.DataFrame(slice_rows)
    if len(slice_df):
        slice_df = slice_df.sort_values(["loss_db", "frame_span_ps"])
    slice_df.to_csv(output_dir / "fixed_frame_span_slice_summary.csv", index=False)

    lines = [
        "input_files:",
        *[f"  - {p}" for p in input_paths],
        f"point_count: {len(point_df)}",
        f"analyzable_slices: {len(slice_df)}",
        "skip_rule: slices with < 3 distinct dimensions are skipped",
        f"skipped_slices: {skipped_slices}",
        f"pie_monotonic_increasing_count: {int((slice_df['pie_monotonic_increasing_tag'] == 'yes').sum()) if len(slice_df) else 0}",
        f"skr_monotonic_increasing_count: {int((slice_df['skr_monotonic_increasing_tag'] == 'yes').sum()) if len(slice_df) else 0}",
        f"pie_interior_peak_count: {int((slice_df['pie_has_interior_peak_tag'] == 'yes').sum()) if len(slice_df) else 0}",
        f"skr_interior_peak_count: {int((slice_df['skr_has_interior_peak_tag'] == 'yes').sum()) if len(slice_df) else 0}",
        "",
    ]
    for loss_db in sorted(slice_df["loss_db"].unique()) if len(slice_df) else []:
        sub = slice_df[slice_df["loss_db"] == loss_db]
        pie_peaks = ",".join(str(int(x)) for x in sub.loc[sub["pie_has_interior_peak_tag"] == "yes", "frame_span_ps"].tolist()) or "none"
        skr_peaks = ",".join(str(int(x)) for x in sub.loc[sub["skr_has_interior_peak_tag"] == "yes", "frame_span_ps"].tolist()) or "none"
        lines.extend(
            [
                f"loss {int(loss_db)} dB",
                f"  pie_interior_peak_frame_spans: {pie_peaks}",
                f"  skr_interior_peak_frame_spans: {skr_peaks}",
            ]
        )
    lines.extend(
        [
            "",
            f"conclusion_fixed_tf_pie_broadly_monotonic_in_d: {'yes' if len(slice_df) and (slice_df['pie_monotonic_increasing_tag'] == 'yes').mean() > 0.5 else 'no'}",
            f"conclusion_fixed_tf_skr_broadly_monotonic_in_d: {'yes' if len(slice_df) and (slice_df['skr_monotonic_increasing_tag'] == 'yes').mean() > 0.5 else 'no'}",
            f"conclusion_fixed_tf_finite_optimum_d_present: {'yes' if len(slice_df) and (((slice_df['pie_has_interior_peak_tag'] == 'yes') | (slice_df['skr_has_interior_peak_tag'] == 'yes')).any()) else 'no'}",
        ]
    )
    if len(slice_df):
        pie_peak_by_loss = slice_df.groupby("loss_db")["pie_has_interior_peak_tag"].apply(lambda s: int((s == "yes").sum()))
        skr_peak_by_loss = slice_df.groupby("loss_db")["skr_has_interior_peak_tag"].apply(lambda s: int((s == "yes").sum()))
        lines.append(f"loss_most_pie_interior_peaks: {int(pie_peak_by_loss.idxmax()) if len(pie_peak_by_loss) else 'none'}")
        lines.append(f"loss_most_skr_interior_peaks: {int(skr_peak_by_loss.idxmax()) if len(skr_peak_by_loss) else 'none'}")
        hot_spans = slice_df.loc[(slice_df["pie_has_interior_peak_tag"] == "yes") | (slice_df["skr_has_interior_peak_tag"] == "yes"), "frame_span_ps"]
        lines.append(f"frame_spans_with_any_interior_peak: {','.join(str(int(x)) for x in sorted(hot_spans.unique())) if len(hot_spans) else 'none'}")
    write_summary(output_dir / "fixed_frame_span_summary.txt", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

