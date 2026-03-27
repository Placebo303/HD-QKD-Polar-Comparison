#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _longrun_common import REPO_ROOT, csv_read, python_tool, write_text
from _security_round_common import load_candidate_bundle


def main() -> int:
    ap = argparse.ArgumentParser(description="Longrun wrapper to aggregate actual-IR replay outputs and write Stage 1 summary.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--candidate-dirs", nargs="*", default=[str(REPO_ROOT / "results" / "e2e_20dB_fullgrid_pairing_v2_candidate_t15")])
    ap.add_argument("--replay-index-dir", default="")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "_shards").mkdir(parents=True, exist_ok=True)
    replay_inputs = [str(output_dir)] if not args.input_dirs else [str(Path(p)) for p in args.input_dirs]
    replay_index_dir = Path(args.replay_index_dir) if str(args.replay_index_dir).strip() else output_dir

    python_tool(
        "round1b_build_actual_ir_logs_index.py",
        "--input-dirs",
        *replay_inputs,
        "--candidate-dirs",
        *[str(Path(p)) for p in args.candidate_dirs],
        "--output-dir",
        str(output_dir),
        "--overwrite",
    )

    point_idx = csv_read(replay_index_dir / "replay_index_point_table.csv")
    point_actual = csv_read(output_dir / "actual_ir_point_table.csv")
    ready_count = int(point_idx["replay_ready_tag"].astype(str).str.lower().eq("yes").sum()) if "replay_ready_tag" in point_idx.columns else 0
    fullgrid_point_count = len(point_idx)
    if args.candidate_dirs:
        fullgrid_counts = []
        for cand in args.candidate_dirs:
            try:
                main, _, _ = load_candidate_bundle(Path(cand))
                fullgrid_counts.append(len(main))
            except Exception:
                pass
        if fullgrid_counts:
            fullgrid_point_count = max(fullgrid_counts)
    actual_count = int(point_actual["leak_ec_source_tag"].astype(str).str.startswith("actual_ir_replay").sum()) if "leak_ec_source_tag" in point_actual.columns else 0
    blocked = point_actual[point_actual["replay_status"].astype(str).eq("blocked")].copy() if "replay_status" in point_actual.columns else pd.DataFrame()
    missing_fields = []
    if "frame_success_rate" in point_actual.columns:
        vals = point_actual["frame_success_rate"].astype(str).str.upper()
        if vals.eq("MISSING").any():
            missing_fields.append("frame_success_rate")
    blocked_reason_counts = blocked["blocked_reason"].astype(str).value_counts().to_dict() if not blocked.empty and "blocked_reason" in blocked.columns else {}
    coverage_ratio = (float(actual_count) / float(fullgrid_point_count)) if fullgrid_point_count > 0 else 0.0
    lines = [
        "stage1_inputs:",
        f"  - replay_index_dir: {replay_index_dir}",
        *[f"  - replay_output_dir: {p}" for p in replay_inputs],
        *[f"  - candidate_dir: {Path(p)}" for p in args.candidate_dirs],
        f"replay_ready_points: {ready_count}",
        f"candidate_fullgrid_point_count: {fullgrid_point_count}",
        f"points_with_actual_total_leak: {actual_count}",
        f"actual_coverage_ratio: {coverage_ratio:.6f}",
        f"fields_still_missing: {', '.join(missing_fields) if missing_fields else 'none'}",
        f"blocked_point_count: {len(blocked)}",
        f"blocked_reason_counts: {blocked_reason_counts if blocked_reason_counts else 'none'}",
        f"actual_coverage_sufficient_for_master: {'yes' if coverage_ratio >= 0.80 else 'partial'}",
        "notes:",
        "- actual replay rows retain configured CRC verification budgeting on SCL points; this is tagged in leak_ec_source_tag and upstream summaries.",
        "- frame_success_rate remains MISSING unless a rigorous frame-level denominator becomes available.",
    ]
    write_text(output_dir / "stage1_summary.txt", "\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
