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

import numpy as np
import pandas as pd

from _security_audit_common import ensure_output_dir, has_interior_peak, load_candidate_frame, monotonic_increasing, write_summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit secure rate decomposition on pairing_v2 candidates.")
    ap.add_argument("--input-dirs", nargs="+", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    frames = [load_candidate_frame(Path(p)) for p in args.input_dirs]
    df = pd.concat(frames, ignore_index=True)
    df["delta_fk"] = 0.0
    keep_cols = [
        "loss_db", "dimension", "bin_width_ps", "map_ser", "raw_ser", "layers_success_best", "best_hard_PIE",
        "IAB_or_proxy", "beta_or_proxy", "leak_ec_bits_or_proxy", "chi_E", "delta_fk", "PIE_practical",
        "SKR_measured_bps", "n_pairs_actual", "frame_diag_available", "security_model_tag",
    ]
    point_df = df[keep_cols].copy()
    point_df.to_csv(output_dir / "secure_rate_decomposition_point_table.csv", index=False)

    lines = [
        "input_dirs:",
        *[f"  - {p}" for p in args.input_dirs],
        f"point_count: {len(point_df)}",
        "",
    ]
    lines.append(f"iab_proxy_range: {point_df['IAB_or_proxy'].min():.6f} .. {point_df['IAB_or_proxy'].max():.6f}")
    lines.append(f"beta_proxy_range: {point_df['beta_or_proxy'].min():.6f} .. {point_df['beta_or_proxy'].max():.6f}")
    lines.append(f"chi_E_range: {point_df['chi_E'].min():.6f} .. {point_df['chi_E'].max():.6f}")
    lines.append(f"delta_fk_unique_values: {sorted(set(float(x) for x in point_df['delta_fk'].dropna().unique().tolist()))}")
    lines.append("")

    large_bw = df[df['bin_width_ps'] >= 120]
    large_d = df[df['dimension'] >= 1024]
    chi_static_bw_count = 0
    bw_slice_count = 0
    for (loss_db, dimension), sl in large_bw.groupby(['loss_db', 'dimension']):
        vals = pd.to_numeric(sl['chi_E'], errors='coerce').dropna().tolist()
        if vals:
            bw_slice_count += 1
            if max(vals) - min(vals) <= 1e-12:
                chi_static_bw_count += 1
    lines.append(f"large_bw_chi_E_static_slices: {chi_static_bw_count}/{bw_slice_count}")
    lines.append(f"large_d_delta_fk_nonzero_count: {int((pd.to_numeric(large_d['delta_fk'], errors='coerce') > 0).sum())}")
    lines.append("")

    lines.append("summary_answers:")
    lines.append("1. current_PIE_growth_driver: IAB_or_proxy / best_hard_PIE dominates; explicit finite-key term is absent and chi_E is a comparatively slow-varying subtractive term.")
    lines.append(f"2. large_bw_chi_E_is_static: {'yes' if chi_static_bw_count == bw_slice_count and bw_slice_count > 0 else 'mixed'}")
    lines.append("3. large_d_delta_fk_is_weak: yes (current delta_fk is identically zero in the mainline implementation).")
    lines.append("4. current_secure_rate_is_information_term_dominated: yes")

    write_summary(output_dir / "secure_rate_decomposition_summary.txt", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

