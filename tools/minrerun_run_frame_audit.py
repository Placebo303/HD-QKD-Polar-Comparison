#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _minrerun_common import (
    KEY_COLS,
    build_frame_audit_from_candidate,
    candidate_point_frame,
    ensure_output_dir,
    fresh_candidate_dir,
    point_id,
)


def main() -> int:
    ap = argparse.ArgumentParser(description='Derive frame-accounting tables from existing sidecar occupancy summaries.')
    ap.add_argument('--input-dirs', nargs='*', default=[])
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    aug_block = pd.read_csv(out_dir / 'actual_ir_block_table_augmented.csv')
    aug_point = pd.read_csv(out_dir / 'actual_ir_point_table_augmented.csv')
    formal_cols = [
        'total_leak_ec_bits',
        'total_leak_ec_bits_legacy_crc',
        'verification_bits_used_actual_legacy_crc',
        'lambda_ver_bits_actual',
        'lambda_ver_source_tag',
        'lambda_ver_bits_legacy_crc',
        'verification_pass_count',
        'verification_fail_count',
        'verification_outcome_source_tag',
        'epsilon_EC_empirical',
        'epsilon_EC_empirical_source_tag',
        'epsilon_EC_bound',
        'epsilon_EC_bound_formula_tag',
        'decoder_fail_rate_oracle',
        'decoder_fail_rate_oracle_source_tag',
    ]
    for col in formal_cols:
        if col not in aug_point.columns:
            aug_point[col] = pd.NA
    candidate_dir = fresh_candidate_dir(20)
    point_frame = candidate_point_frame(candidate_dir)
    frame_point = build_frame_audit_from_candidate(candidate_dir, point_frame[[*KEY_COLS, 'point_id']])
    frame_point = frame_point.merge(
        aug_point[KEY_COLS + [
            'point_id',
            'total_leak_ec_bits',
            'total_leak_ec_bits_legacy_crc',
            'verification_bits_used_actual',
            'verification_bits_used_actual_legacy_crc',
            'lambda_ver_bits_actual',
            'lambda_ver_source_tag',
            'lambda_ver_bits_legacy_crc',
            'verification_source_tag',
            'verification_pass_count',
            'verification_fail_count',
            'verification_outcome_source_tag',
            'epsilon_EC_empirical',
            'epsilon_EC_empirical_source_tag',
            'epsilon_EC_bound',
            'epsilon_EC_bound_formula_tag',
            'decoder_fail_rate_oracle',
            'decoder_fail_rate_oracle_source_tag',
        ]],
        on=KEY_COLS + ['point_id'],
        how='left',
    )
    frame_point.to_csv(out_dir / 'frame_audit_point_table.csv', index=False)

    frame_block = aug_block.merge(frame_point[KEY_COLS + ['point_id', 'candidate_frame_count', 'accepted_frame_count', 'rejected_frame_count', 'accepted_frame_fraction', 'rejected_frame_fraction', 'frame_success_count', 'frame_success_rate', 'accepted_frame_fraction_source_tag', 'frame_success_rate_source_tag']], on=KEY_COLS + ['point_id'], how='left')
    frame_block.to_csv(out_dir / 'frame_audit_block_table.csv', index=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
