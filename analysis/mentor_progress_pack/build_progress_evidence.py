from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from analysis.mentor_progress_pack.utils_progress_pack import (
    DEFAULT_DATA_ROOT,
    PackContext,
    build_bw_scan_keypoints,
    build_claim_boundary_table,
    build_completeness_table,
    build_contamination_summary,
    build_file_presence_manifest,
    build_fullgrid_20db_matrix,
    build_loss_coverage_table,
    build_report_markdown,
    choose_representative_points,
    compare_summary_from_existing,
    discover_threshold_runs,
    read_csv_if_exists,
    write_csv,
    write_markdown,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    ap.add_argument("--output-root", default="")
    args = ap.parse_args()

    data_root = Path(args.data_root).resolve()
    output_root = Path(args.output_root).resolve() if args.output_root else None
    ctx = PackContext.create(Path(__file__).name, data_root=data_root, output_root=output_root)

    tables_written = 0
    coverage_df = build_loss_coverage_table(data_root)
    presence_df = build_file_presence_manifest(data_root)
    matrix_df = build_fullgrid_20db_matrix(data_root)
    completeness_df = build_completeness_table(data_root)
    claim_df = build_claim_boundary_table()
    contamination_df = build_contamination_summary(matrix_df)
    bw_df = build_bw_scan_keypoints(matrix_df)
    threshold_df = discover_threshold_runs(REPO_ROOT)
    compare_df = read_csv_if_exists(ctx.tables_dir / "v1_v2_compare_table.csv")
    if compare_df.empty:
        ctx.log("WARN", f"missing optional source: {ctx.tables_dir / 'v1_v2_compare_table.csv'}")
    compare_summary_df = compare_summary_from_existing(REPO_ROOT)
    representative_df = choose_representative_points(matrix_df)
    reports_written = 0

    for name, df in (
        ("loss_directory_coverage.csv", coverage_df),
        ("file_presence_manifest.csv", presence_df),
        ("fullgrid_20db_matrix.csv", matrix_df),
        ("canonical_field_completeness.csv", completeness_df),
        ("canonical_claim_boundary_table.csv", claim_df),
        ("contamination_summary_by_d.csv", contamination_df),
        ("bw_scan_keypoints.csv", bw_df),
        ("threshold_sensitivity_summary.csv", threshold_df),
        ("representative_points_for_next_step.csv", representative_df),
    ):
        write_csv(df, ctx.tables_dir / name, ctx)
        tables_written += 1

    report_md, ppt_md = build_report_markdown(
        ctx=ctx,
        coverage_df=coverage_df,
        matrix_df=matrix_df,
        contamination_df=contamination_df,
        compare_df=compare_df,
        compare_summary_df=compare_summary_df,
        representative_df=representative_df,
        threshold_df=threshold_df,
        bw_df=bw_df,
    )
    write_markdown(report_md, ctx.reports_dir / "mentor_progress_evidence_report.md", ctx)
    reports_written += 1
    write_markdown(ppt_md, ctx.reports_dir / "mentor_progress_ppt_ready.md", ctx)
    reports_written += 1

    ctx.log("INFO", f"representative points selected: {len(representative_df)}")
    ctx.summary(
        tables_written=tables_written,
        figures_written=0,
        reports_written=reports_written,
        representative_points=len(representative_df),
        used_existing_results_only=True,
        performed_new_small_scope_runs=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
