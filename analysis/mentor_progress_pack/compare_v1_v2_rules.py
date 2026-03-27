from __future__ import annotations

import argparse
from pathlib import Path
import sys
import shutil

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from analysis.mentor_progress_pack.utils_progress_pack import (
    DEFAULT_DATA_ROOT,
    PackContext,
    compare_summary_from_existing,
    copy_compare_sidecars,
    existing_compare_sources,
    run_subprocess,
    summarize_compare_runs,
    write_csv,
)


SELECTED_POINTS = {
    (4, 30),
    (16, 50),
    (256, 120),
    (1024, 30),
    (2048, 30),
    (4096, 40),
}


def run_version(ctx: PackContext, compare_root: Path, staging_root: Path, version: str) -> Path:
    version_grid = copy_compare_sidecars(compare_root, version, staging_root, selected_points=SELECTED_POINTS)
    if version_grid.empty:
        ctx.log("WARN", f"missing optional source: {compare_root / version}")
        return Path()

    work_dir = staging_root / version
    grid_csv = staging_root / f"{version}_grid.csv"
    src_csv = staging_root / f"{version}_src.csv"
    out_csv = work_dir / "polar_e2e_results_refresh.csv"
    version_grid.to_csv(grid_csv, index=False)
    version_grid[["dimension", "bin_width_ps", "status", "sidecar_map_ser"]].rename(columns={"sidecar_map_ser": "map_ser"}).to_csv(src_csv, index=False)

    only_points = ";".join(f"{int(r.dimension)},{int(r.bin_width_ps)}" for r in version_grid.itertuples())
    command = [
        "python",
        "experiments/run_real_polar_max_pie.py",
        "--grid-table",
        str(grid_csv.resolve()),
        "--in-csv",
        str(src_csv.resolve()),
        "--out-csv",
        str(out_csv.resolve()),
        "--only-points",
        only_points,
        "--prefer-sidecar-map-ser",
        "--frames",
        "4",
        "--jobs",
        "1",
        "--disable-scl",
    ]
    code, _ = run_subprocess(command, REPO_ROOT, ctx)
    if code != 0:
        raise RuntimeError(f"run_real_polar_max_pie failed for {version}")
    return work_dir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    ap.add_argument("--output-root", default="")
    args = ap.parse_args()

    data_root = Path(args.data_root).resolve()
    output_root = Path(args.output_root).resolve() if args.output_root else None
    ctx = PackContext.create(Path(__file__).name, data_root=data_root, output_root=output_root)

    compare_root, summary_path = existing_compare_sources(REPO_ROOT)
    if not compare_root.exists():
        ctx.log("WARN", f"missing optional source: {compare_root}")
        ctx.summary(
            tables_written=0,
            figures_written=0,
            reports_written=0,
            representative_points=0,
            used_existing_results_only=True,
            performed_new_small_scope_runs=False,
        )
        return 0

    staging_root = ctx.logs_dir / f"v1_v2_stage_{ctx.log_path.stem}"
    staging_root.mkdir(parents=True, exist_ok=True)

    legacy_dir = run_version(ctx, compare_root, staging_root, "legacy_v1")
    pairing_dir = run_version(ctx, compare_root, staging_root, "pairing_v2")
    compare_df = summarize_compare_runs(legacy_dir, pairing_dir, "small_scope_existing_sidecar_replay")
    compare_summary_df = compare_summary_from_existing(REPO_ROOT)

    if not compare_summary_df.empty:
        compare_df = compare_df.merge(
            compare_summary_df[["dimension", "bin_width_ps", "migration_class_tag", "migration_recommendation_tag"]].rename(
                columns={"dimension": "d", "bin_width_ps": "bw"}
            ),
            on=["d", "bw"],
            how="left",
        )
    write_csv(compare_df, ctx.tables_dir / "v1_v2_compare_table.csv", ctx)
    shutil.rmtree(staging_root, ignore_errors=True)

    representative_points = int(compare_df[["d", "bw"]].drop_duplicates().shape[0]) if not compare_df.empty else 0
    ctx.log("INFO", f"representative points selected: {representative_points}")
    ctx.summary(
        tables_written=1,
        figures_written=0,
        reports_written=0,
        representative_points=representative_points,
        used_existing_results_only=False,
        performed_new_small_scope_runs=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
