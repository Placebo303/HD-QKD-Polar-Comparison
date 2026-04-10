#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _minrerun_common import (
    KEY_COLS,
    ensure_output_dir,
    existing_fresh_losses,
    fresh_stage1_dir,
    load_stage1_tables,
    normalize_verification_source_tag,
    write_summary,
)


def main() -> int:
    ap = argparse.ArgumentParser(description='Augment existing actual IR replay logs with verification usage/source tags.')
    ap.add_argument('--input-dirs', nargs='*', default=[])
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    ensure_output_dir(out_dir, overwrite=bool(args.overwrite))

    stage1_dir = fresh_stage1_dir(20)
    block_df, point_df = load_stage1_tables(stage1_dir)
    block_df['verification_bits_used_actual'] = pd.to_numeric(block_df.get('verification_bits_revealed'), errors='coerce')
    block_df['verification_source_tag'] = [normalize_verification_source_tag(t, b) for t, b in zip(block_df.get('verification_source_tag'), block_df['verification_bits_used_actual'])]
    ok_mask = block_df['replay_status'].astype(str).str.startswith('ok')
    block_success = pd.to_numeric(block_df.get('block_success_flag'), errors='coerce')
    decode_fail = pd.to_numeric(block_df.get('decode_fail_flag'), errors='coerce')
    block_df['verification_pass_flag'] = pd.Series(pd.NA, index=block_df.index, dtype='Int64')
    block_df['verification_fail_flag'] = pd.Series(pd.NA, index=block_df.index, dtype='Int64')
    block_df.loc[ok_mask, 'verification_pass_flag'] = block_success[ok_mask].fillna(0).astype(int)
    block_df.loc[ok_mask, 'verification_fail_flag'] = decode_fail[ok_mask].fillna(0).astype(int)
    block_df['verification_outcome_source_tag'] = 'missing'
    block_df.loc[ok_mask, 'verification_outcome_source_tag'] = 'replay_oracle_from_block_success'
    block_df = block_df.sort_values(KEY_COLS + ['layer_id', 'block_index']).reset_index(drop=True)
    block_df.to_csv(out_dir / 'actual_ir_block_table_augmented.csv', index=False)

    agg = block_df.groupby(KEY_COLS + ['point_id'], as_index=False).agg(
        verification_bits_used_actual=('verification_bits_used_actual', 'sum'),
        verification_pass_count=('verification_pass_flag', 'sum'),
        verification_fail_count=('verification_fail_flag', 'sum'),
    )
    source = block_df.groupby(KEY_COLS + ['point_id'])['verification_source_tag'].agg(lambda s: ';'.join(sorted(set(str(x) for x in s if str(x).strip())))).reset_index()
    outcome_source = block_df.groupby(KEY_COLS + ['point_id'])['verification_outcome_source_tag'].agg(lambda s: ';'.join(sorted(set(str(x) for x in s if str(x).strip())))).reset_index()
    aug_point = point_df.merge(agg, on=KEY_COLS + ['point_id'], how='left').merge(source, on=KEY_COLS + ['point_id'], how='left').merge(outcome_source, on=KEY_COLS + ['point_id'], how='left')
    aug_point['verification_source_tag'] = aug_point['verification_source_tag'].fillna('missing')
    aug_point['verification_outcome_source_tag'] = aug_point['verification_outcome_source_tag'].fillna('missing')
    audited = pd.to_numeric(aug_point.get('audited_block_count'), errors='coerce')
    fails = pd.to_numeric(aug_point.get('verification_fail_count'), errors='coerce')
    aug_point['epsilon_EC'] = pd.NA
    valid = audited.gt(0)
    aug_point.loc[valid, 'epsilon_EC'] = (fails[valid].fillna(0.0) / audited[valid]).astype(float)
    aug_point['epsilon_EC_source_tag'] = 'missing'
    aug_point.loc[valid, 'epsilon_EC_source_tag'] = 'empirical_block_fail_rate_from_replay'
    aug_point.to_csv(out_dir / 'actual_ir_point_table_augmented.csv', index=False)

    lines = [
        f'point_count: {len(aug_point)}',
        f'block_count: {len(block_df)}',
        f'configured_budget_blocks: {int(block_df["verification_source_tag"].eq("configured_budget").sum())}',
        f'actual_replay_verification_blocks: {int(block_df["verification_source_tag"].eq("actual_replay").sum())}',
        f'points_with_empirical_epsilon_EC: {int(aug_point["epsilon_EC_source_tag"].eq("empirical_block_fail_rate_from_replay").sum())}',
        'note: current fresh rerun verification usage comes from configured CRC budget on SCL rows, not transcript logs.',
        'note: verification pass/fail and epsilon_EC are replay-audit quantities inferred from block success, not strict composable transcript bounds.',
    ]
    write_summary(out_dir / 'stageB_patch_summary.txt', lines)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
