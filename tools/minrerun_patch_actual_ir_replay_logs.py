#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
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
    block_df['verification_bits_used_actual'] = pd.to_numeric(block_df.get('verification_bits_used_actual', block_df.get('verification_bits_revealed')), errors='coerce')
    block_df['verification_bits_used_actual_legacy_crc'] = pd.to_numeric(block_df.get('verification_bits_revealed_legacy_crc'), errors='coerce')
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
        verification_bits_used_actual_legacy_crc=('verification_bits_used_actual_legacy_crc', 'sum'),
        verification_pass_count=('verification_pass_flag', 'sum'),
        verification_fail_count=('verification_fail_flag', 'sum'),
    )
    source = block_df.groupby(KEY_COLS + ['point_id'])['verification_source_tag'].agg(lambda s: ';'.join(sorted(set(str(x) for x in s if str(x).strip())))).reset_index()
    outcome_source = block_df.groupby(KEY_COLS + ['point_id'])['verification_outcome_source_tag'].agg(lambda s: ';'.join(sorted(set(str(x) for x in s if str(x).strip())))).reset_index()
    aug_point = point_df.merge(agg, on=KEY_COLS + ['point_id'], how='left').merge(source, on=KEY_COLS + ['point_id'], how='left').merge(outcome_source, on=KEY_COLS + ['point_id'], how='left')
    aug_point['verification_source_tag'] = aug_point['verification_source_tag'].fillna('missing')
    aug_point['verification_outcome_source_tag'] = aug_point['verification_outcome_source_tag'].fillna('missing')
    aug_point['lambda_ver_bits_actual'] = pd.to_numeric(aug_point.get('verification_bits_used_actual'), errors='coerce')
    aug_point['lambda_ver_source_tag'] = 'universal_hash_transcript'
    aug_point['lambda_ver_bits_legacy_crc'] = pd.to_numeric(aug_point.get('verification_bits_used_actual_legacy_crc'), errors='coerce')
    for col in ('undetected_error_count_empirical', 'verification_invoked_block_count', 'verification_tag_bits'):
        if col not in aug_point.columns:
            aug_point[col] = pd.NA
    audited = pd.to_numeric(aug_point.get('audited_block_count'), errors='coerce')
    fails = pd.to_numeric(aug_point.get('verification_fail_count'), errors='coerce')
    undetected = pd.to_numeric(aug_point.get('undetected_error_count_empirical'), errors='coerce')
    invoked = pd.to_numeric(aug_point.get('verification_invoked_block_count'), errors='coerce')
    aug_point['epsilon_EC_empirical'] = pd.NA
    valid = audited.gt(0)
    undetected_valid = invoked.gt(0)
    aug_point.loc[undetected_valid, 'epsilon_EC_empirical'] = (undetected[undetected_valid].fillna(0.0) / invoked[undetected_valid]).astype(float)
    aug_point['epsilon_EC_empirical_source_tag'] = 'missing'
    aug_point.loc[undetected_valid, 'epsilon_EC_empirical_source_tag'] = 'empirical_undetected_error_rate_from_replay'
    tag_bits = pd.to_numeric(aug_point.get('verification_tag_bits'), errors='coerce')
    aug_point['epsilon_EC_bound'] = pd.NA
    bound_valid = invoked.gt(0) & tag_bits.gt(0)
    aug_point.loc[bound_valid, 'epsilon_EC_bound'] = (invoked[bound_valid] * np.power(2.0, -tag_bits[bound_valid])).clip(upper=1.0).astype(float)
    aug_point['epsilon_EC_bound_formula_tag'] = 'missing'
    aug_point.loc[bound_valid, 'epsilon_EC_bound_formula_tag'] = 'union_bound_over_blocks_universal_hash'
    aug_point['decoder_fail_rate_oracle'] = pd.NA
    aug_point.loc[valid, 'decoder_fail_rate_oracle'] = (fails[valid].fillna(0.0) / audited[valid]).astype(float)
    aug_point['decoder_fail_rate_oracle_source_tag'] = 'missing'
    aug_point.loc[valid, 'decoder_fail_rate_oracle_source_tag'] = 'empirical_decode_fail_rate_from_replay'
    aug_point.to_csv(out_dir / 'actual_ir_point_table_augmented.csv', index=False)

    lines = [
        f'point_count: {len(aug_point)}',
        f'block_count: {len(block_df)}',
        f'configured_budget_blocks: {int(block_df["verification_source_tag"].eq("configured_budget").sum())}',
        f'actual_replay_verification_blocks: {int(block_df["verification_source_tag"].eq("actual_replay").sum())}',
        f'points_with_empirical_epsilon_EC: {int(aug_point["epsilon_EC_empirical_source_tag"].eq("empirical_undetected_error_rate_from_replay").sum())}',
        'note: verification_bits_used_actual now tracks universal-hash transcript leakage when present; legacy CRC budgeting is retained for compare.',
        'note: decoder_fail_rate_oracle is kept separate from epsilon_EC_empirical and epsilon_EC_bound.',
    ]
    write_summary(out_dir / 'stageB_patch_summary.txt', lines)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
