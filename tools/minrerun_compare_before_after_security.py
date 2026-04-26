#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _minrerun_common import KEY_COLS, ensure_output_dir, fresh_stage2_dir, write_summary


def main() -> int:
    ap = argparse.ArgumentParser(description='Compare old vs refined 20 dB security tables.')
    ap.add_argument('--old-dir', required=False, default='')
    ap.add_argument('--new-dir', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    old_dir = Path(args.old_dir) if str(args.old_dir).strip() else fresh_stage2_dir(20)
    old_df = pd.read_csv(old_dir / 'security_calibrated_master_table.csv')
    new_df = pd.read_csv(Path(args.new_dir) / 'security_calibrated_master_table_20dB_refined.csv')
    merged = old_df.merge(new_df, on=KEY_COLS, how='outer', suffixes=('_old', '_new'))
    for col in ['accepted_frame_fraction', 'frame_success_rate', 'post_selection_correction', 'n_eff_pairs', 'DeltaFK_calibrated', 'PIE_secure_actual_ir', 'SKR_secure_actual_ir_bps']:
        merged[f'delta_{col}'] = pd.to_numeric(merged.get(f'{col}_new'), errors='coerce') - pd.to_numeric(merged.get(f'{col}_old'), errors='coerce')
    merged.to_csv(out_dir / 'security_before_after_diff_20dB.csv', index=False)
    lines = [
        f'point_count: {len(merged)}',
        f'changed_rows_PIE: {int((pd.to_numeric(merged["delta_PIE_secure_actual_ir"], errors="coerce").fillna(0).abs() > 0).sum())}',
        f'changed_rows_SKR: {int((pd.to_numeric(merged["delta_SKR_secure_actual_ir_bps"], errors="coerce").fillna(0).abs() > 0).sum())}',
    ]
    write_summary(out_dir / 'compare_before_after_summary.txt', lines)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
