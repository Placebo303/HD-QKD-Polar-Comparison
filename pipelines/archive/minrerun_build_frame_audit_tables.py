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

from _minrerun_common import ensure_output_dir, write_summary


def main() -> int:
    ap = argparse.ArgumentParser(description='Finalize minimal-rerun frame-audit tables and summary.')
    ap.add_argument('--input-dirs', nargs='*', default=[])
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    point_df = pd.read_csv(out_dir / 'frame_audit_point_table.csv')
    block_df = pd.read_csv(out_dir / 'frame_audit_block_table.csv')
    point_df = point_df.sort_values(['loss_db', 'dimension', 'bin_width_ps']).reset_index(drop=True)
    block_df = block_df.sort_values(['loss_db', 'dimension', 'bin_width_ps', 'layer_id', 'block_index']).reset_index(drop=True)
    point_df.to_csv(out_dir / 'frame_audit_point_table.csv', index=False)
    block_df.to_csv(out_dir / 'frame_audit_block_table.csv', index=False)
    lines = [
        'rules:',
        '- candidate_frame_count := n_frames_total from sidecar occupancy_filter_summary.csv',
        '- accepted_frame_count := n_frames_clean_single_single from sidecar occupancy_filter_summary.csv',
        '- rejected_frame_count := candidate_frame_count - accepted_frame_count',
        '- frame_success_count := accepted_frame_count',
        '- frame_success_rate := accepted_frame_count / candidate_frame_count',
        f'point_count: {len(point_df)}',
        f'configured_budget_points: {int(point_df["verification_source_tag"].astype(str).str.contains("configured_budget").sum())}',
        f'actual_sidecar_frame_points: {int(point_df["accepted_frame_fraction_source_tag"].eq("actual_sidecar_occupancy_summary").sum())}',
        f'empirical_epsilon_EC_points: {int(point_df["epsilon_EC_empirical_source_tag"].astype(str).eq("empirical_undetected_error_rate_from_replay").sum()) if "epsilon_EC_empirical_source_tag" in point_df.columns else 0}',
        f'bounded_epsilon_EC_points: {int(point_df["epsilon_EC_bound_formula_tag"].astype(str).eq("union_bound_over_blocks_universal_hash").sum()) if "epsilon_EC_bound_formula_tag" in point_df.columns else 0}',
        'note: frame_success_rate is accepted as actual_sidecar_occupancy_summary in this refined pass because denominator and accepted count both come from persisted sidecar occupancy diagnostics.',
        'note: epsilon_EC_empirical is the undetected-error empirical rate; epsilon_EC_bound is the universal-hash union bound used for correctness budgeting.',
    ]
    write_summary(out_dir / 'stageB_summary.txt', lines)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

