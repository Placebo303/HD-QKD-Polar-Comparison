#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _security_round_common import REPO_ROOT, ensure_output_dir, write_summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Build merged Round 2 security summary.")
    ap.add_argument("--actual-ir-dir", required=True)
    ap.add_argument("--beta-baseline-dir", required=True)
    ap.add_argument("--performance-proxy-input-dirs", nargs="*", default=[])
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        ensure_output_dir(output_dir, overwrite=bool(args.overwrite))

    actual = pd.read_csv(Path(args.actual_ir_dir) / "actual_ir_finite_key_point_table.csv")
    beta = pd.read_csv(Path(args.beta_baseline_dir) / "beta_baseline_finite_key_point_table.csv")
    perf = pd.read_csv(output_dir / "finite_key_audit_point_table.csv")
    for col in ("lambda_ver_bits_actual", "epsilon_EC_empirical", "epsilon_EC_bound", "decoder_fail_rate_oracle", "eps_cor_total", "eps_cor_budget_rule"):
        if col not in perf.columns:
            perf[col] = pd.NA

    merged = actual.merge(
        beta[["loss_db", "dimension", "bin_width_ps", "beta_baseline", "PIE_secure_beta_baseline", "SKR_secure_beta_baseline_bps"]],
        on=["loss_db", "dimension", "bin_width_ps"],
        how="left",
    ).merge(
        perf[["loss_db", "dimension", "bin_width_ps", "PIE_practical", "SKR_measured_bps", "DeltaFK_calibrated", "franson_visibility_global", "leak_EC_source_tag", "lambda_ver_bits_actual", "epsilon_EC_empirical", "epsilon_EC_bound", "decoder_fail_rate_oracle", "eps_cor_total", "eps_cor_budget_rule"]],
        on=["loss_db", "dimension", "bin_width_ps"],
        how="left",
        suffixes=("", "_perf"),
    )
    merged["PIE_main"] = pd.to_numeric(merged["PIE_secure_actual_ir"], errors="coerce")
    merged["SKR_main_bps"] = pd.to_numeric(merged["SKR_secure_actual_ir_bps"], errors="coerce")
    merged["main_result_source"] = "actual_ir_finite_key"
    merged["performance_proxy_role"] = "diagnostic_only"
    front_cols = [
        "loss_db",
        "dimension",
        "bin_width_ps",
        "PIE_main",
        "SKR_main_bps",
        "main_result_source",
        "PIE_secure_actual_ir",
        "SKR_secure_actual_ir_bps",
    ]
    rest_cols = [c for c in merged.columns if c not in front_cols]
    merged = merged[[*front_cols, *rest_cols]]
    merged.to_csv(output_dir / "round2_security_master_table.csv", index=False)

    beta_minus_actual = pd.to_numeric(merged["PIE_secure_beta_baseline"], errors="coerce") - pd.to_numeric(merged["PIE_secure_actual_ir"], errors="coerce")
    perf_minus_actual = pd.to_numeric(merged["PIE_practical"], errors="coerce") - pd.to_numeric(merged["PIE_secure_actual_ir"], errors="coerce")
    best_rows = []
    for loss_db, grp in merged.groupby("loss_db"):
        perf_best = grp.loc[pd.to_numeric(grp["SKR_measured_bps"], errors="coerce").idxmax()]
        actual_best = grp.loc[pd.to_numeric(grp["SKR_secure_actual_ir_bps"], errors="coerce").idxmax()]
        best_rows.append(f"- loss={int(loss_db)} performance_best=(d={int(perf_best['dimension'])},bw={int(perf_best['bin_width_ps'])}) actual_ir_best=(d={int(actual_best['dimension'])},bw={int(actual_best['bin_width_ps'])})")

    lines = [
        f"point_count: {len(merged)}",
        f"1. actual_leak_rows: {int(merged['leak_EC_source_tag'].astype(str).str.startswith('actual_ir_replay').sum())}",
        "2. DeltaFK_explicit_inputs: n_pairs_actual, layer_fraction, accepted_frame_fraction, block_success_rate_used, eps_sec, eps_cor",
        "3. post-selection sensitivity region: higher-bw / lower-clean-fraction points move most because post_selection_correction follows accepted_frame_fraction",
        f"4. mean_PIE_drop_actual_vs_performance: {perf_minus_actual.mean()}",
        f"5. beta_baseline_more_optimistic_rows: {int((beta_minus_actual > 0).sum())}; more_conservative_rows: {int((beta_minus_actual < 0).sum())}",
        f"5b. formal_epsilon_bound_rows: {int(merged['eps_cor_budget_rule'].astype(str).eq('verification_only_shadow').sum()) if 'eps_cor_budget_rule' in merged.columns else 0}",
        "6. best_point_shift_by_loss:",
        *best_rows,
        f"7. positive_actual_secure_rows: {int((pd.to_numeric(merged['SKR_secure_actual_ir_bps'], errors='coerce') > 0).sum())}",
        f"8. surrogate_sensitive_rows: {int(merged['leak_EC_source_tag'].astype(str).str.startswith('surrogate').sum())}",
        "PRIMARY_REPORTING_MODE = actual_ir_finite_key",
        "DEFAULT_MAIN_COLUMNS = PIE_main, SKR_main_bps",
        "MAIN_COLUMNS_SOURCE = PIE_secure_actual_ir, SKR_secure_actual_ir_bps",
        "PERFORMANCE_PROXY_ROLE = diagnostic_only",
        "BETA_BASELINE_ROLE = comparison_only",
        "NIU_2016_STATUS = not_supported_by_current_observables",
    ]
    write_summary(output_dir / "round2_summary.txt", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
