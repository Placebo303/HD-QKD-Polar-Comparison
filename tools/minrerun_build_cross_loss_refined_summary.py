#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _minrerun_common import ensure_output_dir, write_summary


def main() -> int:
    ap = argparse.ArgumentParser(description='Build refined cross-loss summary and compare against old cross-loss pack.')
    ap.add_argument('--old-dir', required=False, default='')
    ap.add_argument('--new-dir', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    new_df = pd.read_csv(Path(args.new_dir) / 'cross_loss_security_master_table_refined.csv')
    old_path = Path(args.old_dir) / 'cross_loss_security_master_table.csv' if str(args.old_dir).strip() else None
    if old_path is not None and old_path.exists():
        old_df = pd.read_csv(old_path)
        merged = old_df.merge(new_df, on=['loss_db','dimension','bin_width_ps'], how='outer', suffixes=('_old','_new'))
        merged.to_csv(out_dir / 'cross_loss_before_after_diff.csv', index=False)
    new_df.to_csv(out_dir / 'cross_loss_security_master_table_refined.csv', index=False)
    lines = ['actual_coverage_by_loss:']
    for loss_db, grp in new_df.groupby('loss_db'):
        best = grp.loc[pd.to_numeric(grp['SKR_secure_actual_ir_bps'], errors='coerce').idxmax()]
        lines.append(f"- loss={int(loss_db)} actual={len(grp)}/{len(grp)} best_point=(d={int(best['dimension'])},bw={int(best['bin_width_ps'])})")
    lines.extend([
        f"cross_loss_positive_actual_rows: {int((pd.to_numeric(new_df['SKR_secure_actual_ir_bps'], errors='coerce') > 0).sum())}",
        'main_text_scope: refined actual-IR finite-key cross-loss trends may move from preliminary to main text because frame accounting now comes from actual sidecar occupancy summaries.',
        'NIU_2016_STATUS = not_supported_by_current_observables',
    ])
    write_summary(out_dir / 'stageD_summary.txt', lines)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
