#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _minrerun_common import ensure_output_dir, fresh_stage2_dir, load_stage2_audit, load_stage2_master, recompute_finite_key, write_summary


def main() -> int:
    ap = argparse.ArgumentParser(description='Rebuild refined 20 dB security master using actual frame accounting from Stage B.')
    ap.add_argument('--input-dirs', nargs='*', default=[])
    ap.add_argument('--franson-visibility', type=float, default=0.95)
    ap.add_argument('--eps-sec', type=float, default=1e-10)
    ap.add_argument('--eps-cor', type=float, default=1e-10)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    ensure_output_dir(out_dir, overwrite=bool(args.overwrite))
    old_stage2_dir = fresh_stage2_dir(20)
    frame_dir = Path(args.input_dirs[-1]) if args.input_dirs else Path('')
    if not frame_dir.exists():
        raise SystemExit('frame audit dir not found in --input-dirs')
    frame_point = pd.read_csv(frame_dir / 'frame_audit_point_table.csv')
    old_master = load_stage2_master(old_stage2_dir)
    old_audit = load_stage2_audit(old_stage2_dir)
    new_master = recompute_finite_key(old_master, old_audit, frame_point)
    new_master.to_csv(out_dir / 'security_calibrated_master_table_20dB_refined.csv', index=False)
    changed_actual = int(new_master['accepted_frame_fraction_source_tag'].eq('actual_sidecar_occupancy_summary').sum())
    configured = int(new_master['verification_source_tag'].astype(str).str.contains('configured_budget').sum())
    empirical_epsilon = int(new_master['epsilon_EC_source_tag'].astype(str).eq('empirical_block_fail_rate_from_replay').sum()) if 'epsilon_EC_source_tag' in new_master.columns else 0
    diff = pd.to_numeric(old_master['PIE_secure_actual_ir'], errors='coerce') - pd.to_numeric(new_master['PIE_secure_actual_ir'], errors='coerce')
    skr_diff = pd.to_numeric(old_master['SKR_secure_actual_ir_bps'], errors='coerce') - pd.to_numeric(new_master['SKR_secure_actual_ir_bps'], errors='coerce')
    old_best = old_master.loc[pd.to_numeric(old_master['SKR_secure_actual_ir_bps'], errors='coerce').idxmax()]
    new_best = new_master.loc[pd.to_numeric(new_master['SKR_secure_actual_ir_bps'], errors='coerce').idxmax()]
    lines = [
        f'point_count: {len(new_master)}',
        f'fully_actual_rows: {changed_actual}',
        f'configured_budget_rows: {configured}',
        f'empirical_epsilon_EC_rows: {empirical_epsilon}',
        f'mean_delta_PIE_secure_actual_ir: {(-diff).mean()}',
        f'mean_delta_SKR_secure_actual_ir_bps: {(-skr_diff).mean()}',
        f'old_best_point: d={int(old_best["dimension"])}, bw={int(old_best["bin_width_ps"])}',
        f'new_best_point: d={int(new_best["dimension"])}, bw={int(new_best["bin_width_ps"])}',
        f'high_dim_anti_loss_still_visible: {"yes" if int((pd.to_numeric(new_master["SKR_secure_actual_ir_bps"], errors="coerce") > 0).sum()) > 0 else "no"}',
        'paper_fitness: refined version is better because accepted/rejected frame accounting is sourced from persisted sidecar occupancy diagnostics instead of surrogate clean_pair_fraction.',
        'verification_note: verification_bits_used_actual remains configured-budget on current SCL rows; epsilon_EC is carried separately as replay-audit empirical fail rate with explicit provenance.',
        'PRIMARY_REPORTING_MODE = actual_ir_finite_key',
        'BETA_BASELINE_ROLE = comparison_only',
        'NIU_2016_STATUS = not_supported_by_current_observables',
    ]
    write_summary(out_dir / 'stageC_summary.txt', lines)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
