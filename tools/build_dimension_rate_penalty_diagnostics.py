#!/usr/bin/env python3
from __future__ import annotations

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
    monotonic_decreasing,
    monotonic_increasing,
    normalize_numeric,
    write_summary,
)

NUMERIC_COLS = [
    "dimension",
    "bin_width_ps",
    "coincidence_rate_hz",
    "layers_success_best",
    "PIE_practical",
    "SKR_measured_bps",
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Build dimension/rate-penalty diagnostics from pairing_v2 candidate results.")
    ap.add_argument("--input-dirs", nargs="+", required=True)
    ap.add_argument("--output-dir", default=str(REPO_ROOT / "results" / "_tmp_bw_d_rootcause" / "dimension_rate_penalty"))
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
        df["frame_rate_ceiling_hz"] = 1e12 / df["frame_span_ps"]
        df["log2_dimension"] = np.log2(df["dimension"])
        df["pie_per_layer"] = df["PIE_practical"] / df["layers_success_best"].clip(lower=1)
        df["skr_over_pie_rate_proxy_hz"] = np.where(df["PIE_practical"] > 0, df["SKR_measured_bps"] / df["PIE_practical"], np.nan)
        df["coincidence_per_frame_ceiling"] = df["coincidence_rate_hz"] / df["frame_rate_ceiling_hz"]
        point_frames.append(
            df[
                [
                    "loss_db",
                    "dimension",
                    "bin_width_ps",
                    "frame_span_ps",
                    "frame_rate_ceiling_hz",
                    "log2_dimension",
                    "layers_success_best",
                    "PIE_practical",
                    "SKR_measured_bps",
                    "pie_per_layer",
                    "skr_over_pie_rate_proxy_hz",
                    "coincidence_rate_hz",
                    "coincidence_per_frame_ceiling",
                ]
            ]
        )

    point_df = pd.concat(point_frames, ignore_index=True).sort_values(["loss_db", "bin_width_ps", "dimension"])
    point_df.to_csv(output_dir / "dimension_rate_penalty_point_table.csv", index=False)

    by_rows: list[dict[str, object]] = []
    skipped = 0
    for (loss_db, bw), grp in point_df.groupby(["loss_db", "bin_width_ps"], sort=True):
        grp = grp.sort_values("dimension")
        dims = [int(x) for x in grp["dimension"].dropna().tolist()]
        if len(set(dims)) < 3:
            skipped += 1
            continue
        pie_vals = [float(x) for x in grp["PIE_practical"].tolist()]
        skr_vals = [float(x) for x in grp["SKR_measured_bps"].tolist()]
        rate_vals = [float(x) for x in grp["skr_over_pie_rate_proxy_hz"].tolist() if pd.notna(x)]
        pie_idx = int(np.nanargmax(np.asarray(pie_vals, dtype=float)))
        skr_idx = int(np.nanargmax(np.asarray(skr_vals, dtype=float)))
        by_rows.append(
            {
                "loss_db": int(loss_db),
                "bin_width_ps": int(bw),
                "best_pie_dimension": int(grp.iloc[pie_idx]["dimension"]),
                "best_pie_value": float(grp.iloc[pie_idx]["PIE_practical"]),
                "best_skr_dimension": int(grp.iloc[skr_idx]["dimension"]),
                "best_skr_value": float(grp.iloc[skr_idx]["SKR_measured_bps"]),
                "min_frame_rate_ceiling_hz": float(grp["frame_rate_ceiling_hz"].min()),
                "max_frame_rate_ceiling_hz": float(grp["frame_rate_ceiling_hz"].max()),
                "min_skr_over_pie_rate_proxy_hz": float(np.nanmin(grp["skr_over_pie_rate_proxy_hz"].to_numpy(dtype=float))),
                "max_skr_over_pie_rate_proxy_hz": float(np.nanmax(grp["skr_over_pie_rate_proxy_hz"].to_numpy(dtype=float))),
                "pie_monotonic_increasing_with_d_tag": "yes" if monotonic_increasing(pie_vals) else "no",
                "skr_monotonic_increasing_with_d_tag": "yes" if monotonic_increasing(skr_vals) else "no",
                "rate_proxy_monotonic_decreasing_with_d_tag": "yes" if monotonic_decreasing(rate_vals) else "no",
                "finite_skr_optimum_tag": "yes" if has_interior_peak(dims, skr_vals) else "no",
            }
        )
    by_df = pd.DataFrame(by_rows)
    if len(by_df):
        by_df = by_df.sort_values(["loss_db", "bin_width_ps"])
    by_df.to_csv(output_dir / "dimension_rate_penalty_by_loss_bw.csv", index=False)

    lines = [
        "input_files:",
        *[f"  - {p}" for p in input_paths],
        f"point_count: {len(point_df)}",
        f"analyzed_loss_bw_slices: {len(by_df)}",
        "skip_rule: slices with < 3 dimensions are skipped",
        f"skipped_slices: {skipped}",
        f"pie_monotonic_increasing_count: {int((by_df['pie_monotonic_increasing_with_d_tag'] == 'yes').sum()) if len(by_df) else 0}",
        f"skr_monotonic_increasing_count: {int((by_df['skr_monotonic_increasing_with_d_tag'] == 'yes').sum()) if len(by_df) else 0}",
        f"rate_proxy_monotonic_decreasing_count: {int((by_df['rate_proxy_monotonic_decreasing_with_d_tag'] == 'yes').sum()) if len(by_df) else 0}",
        f"pie_up_and_rate_proxy_down_count: {int(((by_df['pie_monotonic_increasing_with_d_tag'] == 'yes') & (by_df['rate_proxy_monotonic_decreasing_with_d_tag'] == 'yes')).sum()) if len(by_df) else 0}",
        f"finite_skr_optimum_count: {int((by_df['finite_skr_optimum_tag'] == 'yes').sum()) if len(by_df) else 0}",
        "",
        "pie_up_and_rate_proxy_down_slices:",
    ]
    pie_up_rate_down = by_df[(by_df["pie_monotonic_increasing_with_d_tag"] == "yes") & (by_df["rate_proxy_monotonic_decreasing_with_d_tag"] == "yes")] if len(by_df) else pd.DataFrame()
    finite_skr_df = by_df[by_df["finite_skr_optimum_tag"] == "yes"] if len(by_df) else pd.DataFrame()
    if len(pie_up_rate_down):
        for _, row in pie_up_rate_down.iterrows():
            lines.append(f"  - loss={int(row['loss_db'])}, bw={int(row['bin_width_ps'])}")
    else:
        lines.append("  - none")
    lines.append("finite_skr_optimum_slices:")
    if len(finite_skr_df):
        for _, row in finite_skr_df.iterrows():
            lines.append(f"  - loss={int(row['loss_db'])}, bw={int(row['bin_width_ps'])}")
    else:
        lines.append("  - none")
    lines.extend(
        [
            "",
            "conclusion_frame_rate_ceiling_decreases_with_d_at_fixed_bw: yes",
            f"conclusion_rate_proxy_decreases_or_saturates_with_d: {'yes' if len(by_df) and ((by_df['rate_proxy_monotonic_decreasing_with_d_tag'] == 'yes').any()) else 'no'}",
            f"conclusion_pie_can_rise_while_rate_proxy_falls: {'yes' if len(pie_up_rate_down) else 'no'}",
            f"conclusion_finite_skr_optimum_exists: {'yes' if len(finite_skr_df) else 'no'}",
            f"conclusion_large_d_always_better_is_primarily_per_photon_view: {'yes' if len(pie_up_rate_down) or len(finite_skr_df) else 'no'}",
        ]
    )
    write_summary(output_dir / "dimension_rate_penalty_summary.txt", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
