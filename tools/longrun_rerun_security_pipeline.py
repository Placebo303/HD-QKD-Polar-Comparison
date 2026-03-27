#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _longrun_common import (
    DEFAULT_BETA_BASELINE,
    DEFAULT_EPS_COR,
    DEFAULT_EPS_SEC,
    DEFAULT_FRANSON_VISIBILITY,
    DEFAULT_WORKERS,
    FULLGRID_BWS,
    FULLGRID_DIMS,
    LOSS_INPUT_CONFIGS,
    REPRESENTATIVE_BWS,
    REPRESENTATIVE_DIMS,
    bws_arg,
    candidate_dir_for_loss,
    dims_arg,
    python_tool,
    subprocess_run,
    write_text,
)


def _run_extract(loss_db: int, out_root: Path, *, dims: list[int], bws: list[int], workers: int, overwrite: bool) -> None:
    cfg = LOSS_INPUT_CONFIGS[int(loss_db)]
    subprocess_run(
        [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "experiments" / "run_e2e_pipeline.py"),
        "--grid-table",
        str(cfg["grid_table"]),
        "--ttbin",
        str(cfg["ttbin"]),
        "--ttbin-ch-a-override",
        str(cfg["ch_a"]),
        "--ttbin-ch-b-override",
        str(cfg["ch_b"]),
        "--dims",
        dims_arg(dims),
        "--bws",
        bws_arg(bws),
        "--materialize-processing-rule-version",
        "pairing_v2",
        "--extract-workers",
        str(int(workers)),
        "--jobs",
        str(int(workers)),
        "--skip-polar",
        "--out-root",
        str(out_root),
        *(["--overwrite"] if False else []),
        ],
    )


def _run_polar(out_root: Path, *, dims: list[int], bws: list[int], workers: int) -> None:
    only_points = ";".join(f"{int(d)},{int(bw)}" for d in dims for bw in bws)
    subprocess_run(
        [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "experiments" / "run_real_polar_max_pie.py"),
        "--grid-table",
        str(out_root / "_tmp_grid_table.csv"),
        "--in-csv",
        str(out_root / "_tmp_src_table.csv"),
        "--out-csv",
        str(out_root / "polar_e2e_results.csv"),
        "--only-points",
        only_points,
        "--jobs",
        str(int(workers)),
        "--N",
        "4096",
        "--frames",
        "100",
        "--visibility",
        str(DEFAULT_FRANSON_VISIBILITY),
        "--prefer-sidecar-map-ser",
        ],
    )


def _run_stage1(candidate_dir: Path, out_dir: Path, *, workers: int) -> None:
    python_tool(
        "longrun_build_replay_index.py",
        "--input-dirs",
        str(candidate_dir),
        "--output-dir",
        str(out_dir),
        "--jobs",
        str(int(workers)),
        "--overwrite",
    )
    python_tool(
        "longrun_run_actual_ir_replay.py",
        "--input-dirs",
        str(candidate_dir),
        "--replay-index-dir",
        str(out_dir),
        "--output-dir",
        str(out_dir),
        "--workers",
        str(int(workers)),
        "--overwrite",
    )
    python_tool(
        "longrun_build_actual_ir_logs_index.py",
        "--input-dirs",
        str(out_dir),
        "--candidate-dirs",
        str(candidate_dir),
        "--replay-index-dir",
        str(out_dir),
        "--output-dir",
        str(out_dir),
        "--overwrite",
    )


def _run_stage2(candidate_dir: Path, stage1_dir: Path, stage2_dir: Path) -> None:
    python_tool(
        "longrun_build_finite_key_audit_table.py",
        "--input-dirs",
        str(candidate_dir),
        str(stage1_dir),
        "--franson-visibility",
        str(DEFAULT_FRANSON_VISIBILITY),
        "--eps-sec",
        str(DEFAULT_EPS_SEC),
        "--eps-cor",
        str(DEFAULT_EPS_COR),
        "--output-dir",
        str(stage2_dir),
        "--overwrite",
    )
    python_tool(
        "longrun_build_actual_ir_finite_key_shadow.py",
        "--franson-visibility",
        str(DEFAULT_FRANSON_VISIBILITY),
        "--eps-sec",
        str(DEFAULT_EPS_SEC),
        "--eps-cor",
        str(DEFAULT_EPS_COR),
        "--output-dir",
        str(stage2_dir),
        "--overwrite",
    )
    python_tool(
        "longrun_build_beta_baseline_shadow.py",
        "--franson-visibility",
        str(DEFAULT_FRANSON_VISIBILITY),
        "--beta-baseline",
        str(DEFAULT_BETA_BASELINE),
        "--eps-sec",
        str(DEFAULT_EPS_SEC),
        "--eps-cor",
        str(DEFAULT_EPS_COR),
        "--output-dir",
        str(stage2_dir),
        "--overwrite",
    )
    python_tool(
        "longrun_build_security_master_table.py",
        "--actual-ir-dir",
        str(stage2_dir),
        "--beta-baseline-dir",
        str(stage2_dir),
        "--performance-proxy-input-dirs",
        str(candidate_dir),
        "--output-dir",
        str(stage2_dir),
        "--overwrite",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Fresh rerun pipeline with explicit cache boundaries and smoke validation.")
    ap.add_argument("--output-root", required=True)
    ap.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    ap.add_argument("--run-smoke", action="store_true")
    ap.add_argument("--run-full", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    summary_lines = [f"output_root: {output_root}", f"workers: {int(args.workers)}"]

    if bool(args.run_smoke):
        smoke_root = output_root / "smoke_20dB"
        rerun_dir = smoke_root / "candidate_rerun"
        _run_extract(20, rerun_dir, dims=REPRESENTATIVE_DIMS, bws=REPRESENTATIVE_BWS, workers=int(args.workers), overwrite=bool(args.overwrite))
        _run_polar(rerun_dir, dims=REPRESENTATIVE_DIMS, bws=REPRESENTATIVE_BWS, workers=int(args.workers))
        python_tool(
            "longrun_validate_smoke_subset.py",
            "--fresh-dir",
            str(rerun_dir),
            "--baseline-dir",
            str(candidate_dir_for_loss(20)),
            "--output-dir",
            str(smoke_root / "validation"),
            "--overwrite",
        )
        summary_lines.append(f"smoke_rerun_dir: {rerun_dir}")
        summary_lines.append(f"smoke_validation_dir: {smoke_root / 'validation'}")

    if bool(args.run_full):
        stage0_root = output_root / "fresh_candidates"
        stage1_root = output_root / "stage1_actual_ir"
        stage2_root = output_root / "stage2_security"
        stage3_root = output_root / "stage3_cross_loss"
        stage4_root = output_root / "stage4_conference_pack"
        loss_order = [20, 16, 10, 6]
        stage2_dirs: list[Path] = []
        for loss_db in loss_order:
            rerun_dir = stage0_root / f"loss_{int(loss_db)}dB"
            dims = FULLGRID_DIMS
            bws = FULLGRID_BWS
            _run_extract(loss_db, rerun_dir, dims=dims, bws=bws, workers=int(args.workers), overwrite=bool(args.overwrite))
            _run_polar(rerun_dir, dims=dims, bws=bws, workers=int(args.workers))
            loss_stage1 = stage1_root / f"loss_{int(loss_db)}dB"
            _run_stage1(rerun_dir, loss_stage1, workers=int(args.workers))
            loss_stage2 = stage2_root / f"loss_{int(loss_db)}dB"
            _run_stage2(rerun_dir, loss_stage1, loss_stage2)
            stage2_dirs.append(loss_stage2)
        python_tool(
            "longrun_build_cross_loss_security_summary.py",
            "--input-dirs",
            *[str(p) for p in stage2_dirs],
            "--output-dir",
            str(stage3_root),
            "--overwrite",
        )
        python_tool(
            "longrun_build_conference_result_pack.py",
            "--input-dirs",
            *[str(p) for p in stage2_dirs],
            str(stage3_root),
            "--output-dir",
            str(stage4_root),
            "--overwrite",
        )
        summary_lines.extend(
            [
                f"full_candidate_root: {stage0_root}",
                f"stage1_root: {stage1_root}",
                f"stage2_root: {stage2_root}",
                f"stage3_root: {stage3_root}",
                f"stage4_root: {stage4_root}",
            ]
        )

    write_text(output_root / "pipeline_summary.txt", "\n".join(summary_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
