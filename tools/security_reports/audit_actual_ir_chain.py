#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _security_calibrated_common import (
    default_input_dirs,
    ensure_output_dir,
    find_direct_leak_fields,
    format_float,
    load_candidate_frame,
    write_summary,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit actual Polar IR observables and leakage-chain availability.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    input_dirs = [Path(p) for p in args.input_dirs] if args.input_dirs else default_input_dirs()

    frames = [load_candidate_frame(p) for p in input_dirs]
    df = pd.concat(frames, ignore_index=True)
    direct_fields = find_direct_leak_fields(df)

    point_df = df[[
        "loss_db",
        "dimension",
        "bin_width_ps",
        "raw_ser",
        "map_ser",
        "n_pairs_actual",
        "layers_success_best",
        "best_hard_PIE",
        "IAB_est",
        "beta_eff_from_best_hard_pie",
        "leak_ec_bits_or_proxy",
        "frame_diag_available",
        "clean_pair_fraction",
    ]].copy()
    point_df = point_df.rename(
        columns={
            "beta_eff_from_best_hard_pie": "beta_eff_surrogate",
            "leak_ec_bits_or_proxy": "leak_EC_candidate_bits",
        }
    )
    for field in [
        "syndrome_bits_revealed",
        "verification_bits_revealed",
        "total_leak_ec_bits",
        "block_success_flag",
        "block_success_rate",
        "frame_success_rate",
        "decode_fail_count",
        "kept_block_count",
        "dropped_block_count",
    ]:
        point_df[field] = "MISSING"
    point_df["leak_EC_source_tag"] = "surrogate_from_best_hard_pie_gap"
    point_df["actual_ir_chain_status"] = "surrogate_only"
    point_df.to_csv(output_dir / "actual_ir_chain_point_table.csv", index=False)

    direct_present = [k for k, v in direct_fields.items() if v]
    lines = [
        "# Actual IR Chain Audit",
        "",
        "## Inputs",
        *[f"- {p}" for p in input_dirs],
        f"- point_count: {len(point_df)}",
        "",
        "## 1. Which real Polar IR leakage fields are directly available",
    ]
    if direct_present:
        lines.extend([f"- {name}" for name in direct_present])
    else:
        lines.append("- DIRECT LEAK FIELDS: MISSING")
    lines.extend([
        "- Closest directly available chain terms in current results: best_hard_PIE, layers_success_best, raw_ser, map_ser, n_pairs_actual, coincidence_rate_hz.",
        "",
        "## 2. Which fields are still missing",
        "- syndrome_bits_revealed: MISSING",
        "- verification_bits_revealed: MISSING",
        "- total_leak_ec_bits: MISSING",
        "- block_success_flag: MISSING",
        "- block_success_rate: MISSING",
        "- frame_success_rate: MISSING",
        "- decode_fail_count: MISSING",
        "- kept_block_count: MISSING",
        "- dropped_block_count: MISSING",
        "",
        "## 3. Does the current main table already contain implicit leak_EC / success information",
        "- Yes. best_hard_PIE already captures the actually achieved post-reconciliation information term.",
        "- layers_success_best already captures which Polar layers were successfully rescued.",
        "",
        "## 4. Closest substitute when total_leak_ec_bits is unavailable",
        "- leak_EC_candidate_bits = max(IAB_est - best_hard_PIE, 0).",
        "- This is derived from the actual Polar reconciliation outcome, not from a fixed literature beta.",
        "",
        "## 5. Which field should be used as leak_EC_actual in the primary shadow result",
        "- Use leak_EC_candidate_bits with leak_EC_source_tag = surrogate_from_best_hard_pie_gap.",
        "- This is still a surrogate, but it remains anchored to real Polar IR performance instead of a fixed beta assumption.",
        "",
        "## 6. Extra observations",
        f"- beta_eff_surrogate range: {format_float(point_df['beta_eff_surrogate'].min())} .. {format_float(point_df['beta_eff_surrogate'].max())}",
        f"- leak_EC_candidate_bits range: {format_float(point_df['leak_EC_candidate_bits'].min())} .. {format_float(point_df['leak_EC_candidate_bits'].max())}",
        f"- rows with n_pairs_actual available: {int(point_df['n_pairs_actual'].notna().sum())}/{len(point_df)}",
    ])
    write_summary(output_dir / "actual_ir_chain_audit.md", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
