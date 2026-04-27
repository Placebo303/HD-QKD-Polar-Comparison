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

import pandas as pd

from _longrun_common import (
    DEFAULT_BETA_BASELINE,
    DEFAULT_EPS_COR,
    DEFAULT_EPS_SEC,
    DEFAULT_FRANSON_VISIBILITY,
    DEFAULT_WORKERS,
    REPRESENTATIVE_BWS,
    REPRESENTATIVE_DIMS,
    bws_arg,
    dims_arg,
    infer_loss_from_candidate_dir,
    python_tool,
    safe_copy,
    write_text,
)


def _run_loss(candidate_dir: Path, output_dir: Path, *, workers: int) -> tuple[str, Path]:
    stage1_dir = output_dir / "stage1_actual_ir"
    stage2_dir = output_dir / "stage2_security"
    try:
        python_tool(
            "longrun_build_replay_index.py",
            "--input-dirs",
            str(candidate_dir),
            "--output-dir",
            str(stage1_dir),
            "--jobs",
            str(int(workers)),
            "--overwrite",
        )
        mode = "fullgrid"
    except Exception:
        python_tool(
            "longrun_build_replay_index.py",
            "--input-dirs",
            str(candidate_dir),
            "--output-dir",
            str(stage1_dir),
            "--jobs",
            str(int(workers)),
            "--dimensions",
            dims_arg(REPRESENTATIVE_DIMS),
            "--bin-widths",
            bws_arg(REPRESENTATIVE_BWS),
            "--overwrite",
        )
        mode = "representative_subset"

    python_tool(
        "longrun_run_actual_ir_replay.py",
        "--input-dirs",
        str(candidate_dir),
        "--replay-index-dir",
        str(stage1_dir),
        "--output-dir",
        str(stage1_dir),
        "--workers",
        str(int(workers)),
        "--overwrite",
    )
    python_tool(
        "longrun_build_actual_ir_logs_index.py",
        "--input-dirs",
        str(stage1_dir),
        "--candidate-dirs",
        str(candidate_dir),
        "--replay-index-dir",
        str(stage1_dir),
        "--output-dir",
        str(stage1_dir),
        "--overwrite",
    )
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
        "--output-dir",
        str(stage2_dir),
        "--overwrite",
    )
    python_tool(
        "longrun_build_beta_baseline_shadow.py",
        "--beta-baseline",
        str(DEFAULT_BETA_BASELINE),
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
    return mode, stage2_dir


def main() -> int:
    ap = argparse.ArgumentParser(description="Expand longrun actual-IR pipeline to additional losses.")
    ap.add_argument("--input-dirs", nargs="*", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    losses = sorted([Path(p) for p in args.input_dirs], key=lambda p: {16: 0, 10: 1, 6: 2}.get(infer_loss_from_candidate_dir(p), 99))

    all_frames: list[pd.DataFrame] = []
    summary_lines = ["loss_runs:"]
    for candidate_dir in losses:
        loss_db = infer_loss_from_candidate_dir(candidate_dir)
        loss_dir = output_dir / f"loss_{int(loss_db)}dB"
        mode, stage2_dir = _run_loss(candidate_dir, loss_dir, workers=int(args.workers))
        df = pd.read_csv(stage2_dir / "security_calibrated_master_table.csv")
        df["actual_coverage_tag"] = df["leak_EC_source_tag"].astype(str).apply(lambda s: "actual" if s.startswith("actual_ir_replay") else ("surrogate" if s.startswith("surrogate") else "missing"))
        df.to_csv(stage2_dir / "security_calibrated_master_table.csv", index=False)
        all_frames.append(df)
        actual_rows = int(df["actual_coverage_tag"].eq("actual").sum())
        summary_lines.append(f"- loss={int(loss_db)} mode={mode} point_count={len(df)} actual_rows={actual_rows}")

    if all_frames:
        merged = pd.concat(all_frames, ignore_index=True)
    else:
        merged = pd.DataFrame(columns=["loss_db", "dimension", "bin_width_ps"])
    keep = [
        "loss_db", "dimension", "bin_width_ps", "leak_EC_source_tag", "PIE_secure_actual_ir",
        "SKR_secure_actual_ir_bps", "PIE_secure_beta_baseline", "SKR_secure_beta_baseline_bps",
        "PIE_practical", "SKR_measured_bps", "beta_eff", "actual_coverage_tag",
    ]
    merged[[c for c in keep if c in merged.columns]].to_csv(output_dir / "cross_loss_security_master_table.csv", index=False)
    write_text(output_dir / "stage3_expand_summary.txt", "\n".join(summary_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

