#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _minrerun_common import (
    FRESH_LOSS_ORDER,
    build_frame_audit_from_candidate,
    candidate_point_frame,
    ensure_output_dir,
    fresh_candidate_dir,
    fresh_stage1_dir,
    fresh_stage2_dir,
    FRESH_ROOT,
    load_stage1_tables,
    load_stage2_audit,
    load_stage2_master,
    normalize_verification_source_tag,
    recompute_finite_key,
    write_summary,
)


def main() -> int:
    ap = argparse.ArgumentParser(description='Expand refined frame-audit-based security rebuild to other losses.')
    ap.add_argument('--input-dirs', nargs='*', default=[])
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()
    out_dir = Path(args.output_dir)
    ensure_output_dir(out_dir, overwrite=bool(args.overwrite))

    master_frames: list[pd.DataFrame] = []
    for loss_db in [16, 10, 6]:
        loss_dir = out_dir / f'loss_{loss_db}dB'
        loss_dir.mkdir(parents=True, exist_ok=True)
        candidate_dir = fresh_candidate_dir(loss_db)
        stage1_dir = fresh_stage1_dir(loss_db)
        stage2_dir = fresh_stage2_dir(loss_db)
        block_df, point_df = load_stage1_tables(stage1_dir)
        block_df['verification_bits_used_actual'] = pd.to_numeric(block_df.get('verification_bits_revealed'), errors='coerce')
        block_df['verification_source_tag'] = [normalize_verification_source_tag(t, b) for t, b in zip(block_df.get('verification_source_tag'), block_df['verification_bits_used_actual'])]
        aug_point = point_df.merge(block_df.groupby(['loss_db','dimension','bin_width_ps','point_id'], as_index=False).agg(verification_bits_used_actual=('verification_bits_used_actual','sum')), on=['loss_db','dimension','bin_width_ps','point_id'], how='left')
        source = block_df.groupby(['loss_db','dimension','bin_width_ps','point_id'])['verification_source_tag'].agg(lambda s: ';'.join(sorted(set(str(x) for x in s if str(x).strip())))).reset_index()
        aug_point = aug_point.merge(source, on=['loss_db','dimension','bin_width_ps','point_id'], how='left')
        frame_point = build_frame_audit_from_candidate(candidate_dir, candidate_point_frame(candidate_dir)[['loss_db','dimension','bin_width_ps','point_id']])
        frame_point = frame_point.merge(aug_point[['loss_db','dimension','bin_width_ps','point_id','verification_bits_used_actual','verification_source_tag']], on=['loss_db','dimension','bin_width_ps','point_id'], how='left')
        frame_point.to_csv(loss_dir / 'frame_audit_point_table.csv', index=False)
        new_master = recompute_finite_key(load_stage2_master(stage2_dir), load_stage2_audit(stage2_dir), frame_point)
        new_master['actual_coverage_tag'] = 'actual'
        new_master.to_csv(loss_dir / 'security_calibrated_master_table_refined.csv', index=False)
        master_frames.append(new_master)

    refined_20 = FRESH_ROOT.parent / '_tmp_minrerun_stageC_security_20dB' / 'security_calibrated_master_table_20dB_refined.csv'
    if refined_20.exists():
        master_frames.append(pd.read_csv(refined_20))
    merged = pd.concat(master_frames, ignore_index=True).sort_values(['loss_db','dimension','bin_width_ps']).reset_index(drop=True)
    merged.to_csv(out_dir / 'cross_loss_security_master_table_refined.csv', index=False)
    write_summary(out_dir / 'stageD_expand_summary.txt', [
        f'losses_expanded: 16,10,6',
        f'point_count: {len(merged)}',
        'note: expansion reused fresh rerun candidate/stage1/stage2 outputs only; no front-half rerun executed.',
    ])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
