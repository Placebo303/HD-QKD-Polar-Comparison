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
    block_df['verification_pass_flag'] = 'MISSING'
    block_df['verification_fail_flag'] = 'MISSING'
    block_df = block_df.sort_values(KEY_COLS + ['layer_id', 'block_index']).reset_index(drop=True)
    block_df.to_csv(out_dir / 'actual_ir_block_table_augmented.csv', index=False)

    agg = block_df.groupby(KEY_COLS + ['point_id'], as_index=False).agg(
        verification_bits_used_actual=('verification_bits_used_actual', 'sum')
    )
    source = block_df.groupby(KEY_COLS + ['point_id'])['verification_source_tag'].agg(lambda s: ';'.join(sorted(set(str(x) for x in s if str(x).strip())))).reset_index()
    aug_point = point_df.merge(agg, on=KEY_COLS + ['point_id'], how='left').merge(source, on=KEY_COLS + ['point_id'], how='left')
    aug_point['verification_source_tag'] = aug_point['verification_source_tag'].fillna('missing')
    aug_point.to_csv(out_dir / 'actual_ir_point_table_augmented.csv', index=False)

    lines = [
        f'point_count: {len(aug_point)}',
        f'block_count: {len(block_df)}',
        f'configured_budget_blocks: {int(block_df["verification_source_tag"].eq("configured_budget").sum())}',
        f'actual_replay_verification_blocks: {int(block_df["verification_source_tag"].eq("actual_replay").sum())}',
        'note: current fresh rerun verification usage comes from configured CRC budget on SCL rows, not transcript logs.',
    ]
    write_summary(out_dir / 'stageB_patch_summary.txt', lines)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
