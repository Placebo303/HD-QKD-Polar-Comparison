#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .round2_build_finite_key_audit_table import compute_reconciled_net
except ImportError:
    from round2_build_finite_key_audit_table import compute_reconciled_net
try:
    from ._security_round_common import REPO_ROOT, ensure_output_dir, write_summary
except ImportError:
    from _security_round_common import REPO_ROOT, ensure_output_dir, write_summary


def _default_output_dir() -> Path:
    return REPO_ROOT / "results" / "_tmp_round2_finite_key"


def main() -> int:
    ap = argparse.ArgumentParser(description="Build actual-IR finite-key calibrated shadow from audit table.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--franson-visibility", type=float, default=0.95)
    ap.add_argument("--eps-sec", type=float, default=1e-10)
    ap.add_argument("--eps-cor", type=float, default=1e-10)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    audit = pd.read_csv(output_dir / "finite_key_audit_point_table.csv")
    # These total replay fields are the only inputs allowed for the public-EC
    # reconciled net result.  Keep old tables readable, but make them blocked.
    for col in ("total_kept_info_bits", "total_leak_ec_bits", "coincidence_rate_hz", "coincidence_rate_source_tag"):
        if col not in audit.columns:
            audit[col] = "" if col == "coincidence_rate_source_tag" else np.nan
    audit["PIE_secure_actual_ir"] = np.maximum(
        0.0,
        pd.to_numeric(audit["IAB_est"], errors="coerce")
        - pd.to_numeric(audit["leak_EC_actual_bits"], errors="coerce")
        - pd.to_numeric(audit["chi_E_calibrated"], errors="coerce")
        - pd.to_numeric(audit["DeltaFK_calibrated"], errors="coerce")
        - pd.to_numeric(audit["post_selection_correction"], errors="coerce").fillna(0.0),
    )
    audit["SKR_secure_actual_ir_bps"] = pd.to_numeric(audit["PIE_secure_actual_ir"], errors="coerce") * pd.to_numeric(audit["accepted_rate_proxy"], errors="coerce")
    reconciled = audit.apply(
        lambda row: compute_reconciled_net(
            total_kept_info_bits=row.get("total_kept_info_bits"),
            total_leak_ec_bits=row.get("total_leak_ec_bits"),
            n_pairs_actual=row.get("n_pairs_actual"),
            coincidence_rate_hz=row.get("coincidence_rate_hz"),
            leak_source_tag=row.get("leak_EC_source_tag"),
            coincidence_rate_verified=str(row.get("coincidence_rate_source_tag", "")) in {
                "explicit_acquisition_duration",
                "grid_table_preserved_measured_rate",
                "source_candidate_preserved_measured_rate",
                "authoritative_candidate_grid_table_preserved_measured_rate",
            },
        ),
        axis=1,
        result_type="expand",
    )
    for col in ("PIE_reconciled_net", "SKR_reconciled_net_bps", "reconciliation_evidence_status", "reconciliation_evidence_source", "claim_boundary"):
        audit[col] = reconciled[col]
    audit["legacy_secure_result_status"] = "scientifically_blocked_dimensional_inconsistency"
    audit["legacy_secure_result_role"] = "diagnostic_only"
    audit["beta_eff"] = np.where(
        pd.to_numeric(audit["IAB_est"], errors="coerce") > 0.0,
        np.maximum(
            0.0,
            pd.to_numeric(audit["IAB_est"], errors="coerce") - pd.to_numeric(audit["leak_EC_actual_bits"], errors="coerce"),
        ) / pd.to_numeric(audit["IAB_est"], errors="coerce"),
        np.nan,
    )
    actual_mask = audit["leak_EC_source_tag"].astype(str).str.startswith("actual_ir_replay")
    audit["actual_ir_model_tag"] = np.where(
        actual_mask,
        "legacy_calibrated_shadow_blocked",
        "legacy_surrogate_shadow_blocked",
    )
    audit["composable_security_claim_flag"] = 0
    audit["security_evidence_status"] = "scientifically_blocked_dimensional_inconsistency"
    audit["missing_security_observables"] = "protocol_specific_phase_error_and_parameter_estimation_inputs"
    optional_cols = [
        "leak_EC_actual_bits_legacy_crc", "eps_cor_total", "eps_cor_from_epsilon_EC",
        "eps_cor_budget_rule", "epsilon_EC_in_budget_flag", "verification_bits_used_actual",
        "verification_bits_used_actual_legacy_crc", "lambda_ver_bits_actual", "lambda_ver_source_tag",
        "lambda_ver_bits_legacy_crc", "verification_protocol_id", "verification_invoked_block_count",
        "verification_pass_count", "verification_fail_count", "undetected_error_count_empirical",
        "epsilon_EC_empirical", "epsilon_EC_empirical_source_tag", "epsilon_EC_bound",
        "epsilon_EC_bound_formula_tag", "decoder_fail_rate_oracle", "decoder_fail_rate_oracle_source_tag",
        "n_eff_pairs_rule", "n_pairs_actual",
    ]
    for col in optional_cols:
        if col not in audit.columns:
            audit[col] = np.nan
    keep = [
        "loss_db", "dimension", "bin_width_ps", "franson_visibility_global", "IAB_est", "leak_EC_actual_bits",
        "leak_EC_actual_bits_legacy_crc", "leak_EC_source_tag", "eps_sec", "eps_cor", "eps_cor_total", "eps_cor_from_epsilon_EC",
        "eps_cor_budget_rule", "epsilon_EC_in_budget_flag", "n_eff_pairs", "clean_pair_fraction", "layer_fraction",
        "accepted_frame_fraction", "rejected_frame_fraction", "exactly_one_click_fraction", "post_selection_correction",
        "DeltaFK_calibrated", "accepted_rate_proxy", "PIE_secure_actual_ir", "SKR_secure_actual_ir_bps", "beta_eff",
        "verification_bits_used_actual", "verification_bits_used_actual_legacy_crc", "lambda_ver_bits_actual", "lambda_ver_source_tag",
        "lambda_ver_bits_legacy_crc", "verification_protocol_id", "verification_invoked_block_count", "verification_pass_count",
        "verification_fail_count", "undetected_error_count_empirical", "epsilon_EC_empirical", "epsilon_EC_empirical_source_tag",
        "epsilon_EC_bound", "epsilon_EC_bound_formula_tag", "decoder_fail_rate_oracle", "decoder_fail_rate_oracle_source_tag",
        "processing_rule_version", "pairing_path_tag", "pairing_window_source_tag", "threshold_ps", "effective_pairing_window_ps",
        "threshold_ratio_to_bw", "n_pairs_actual", "best_hard_PIE", "PIE_practical", "SKR_measured_bps", "actual_ir_model_tag",
        "total_kept_info_bits", "total_leak_ec_bits", "coincidence_rate_hz", "coincidence_rate_source_tag", "PIE_reconciled_net", "SKR_reconciled_net_bps",
        "reconciliation_evidence_status", "reconciliation_evidence_source", "claim_boundary", "legacy_secure_result_status", "legacy_secure_result_role",
        "composable_security_claim_flag", "security_evidence_status", "missing_security_observables", "n_eff_pairs_rule",
    ]
    audit[keep].to_csv(output_dir / "actual_ir_finite_key_point_table.csv", index=False)
    perf_drop = pd.to_numeric(audit["PIE_practical"], errors="coerce") - pd.to_numeric(audit["PIE_secure_actual_ir"], errors="coerce")
    large_mask = (pd.to_numeric(audit["bin_width_ps"], errors="coerce") >= 120) | (pd.to_numeric(audit["dimension"], errors="coerce") >= 1024)
    lines = [
        f"point_count: {len(audit)}",
        f"actual_leak_rows: {int(audit['leak_EC_source_tag'].astype(str).str.startswith('actual_ir_replay').sum())}",
        f"surrogate_leak_rows: {int(audit['leak_EC_source_tag'].astype(str).str.startswith('surrogate').sum())}",
        "DeltaFK_primary_inputs: n_pairs_actual, layer_fraction, accepted_frame_fraction, conditional block_success_rate_used, eps_cor_total",
        "security_claim_boundary: legacy calibrated shadow is scientifically blocked; reconciled result is public-EC-only and not secure",
        f"mean_PIE_drop_vs_performance_proxy: {perf_drop.mean()}",
        f"large_bw_or_large_d_mean_PIE_drop: {pd.to_numeric(perf_drop[large_mask], errors='coerce').mean()}",
        f"beta_eff_range_p10_p90: {audit['beta_eff'].quantile(0.10)} .. {audit['beta_eff'].quantile(0.90)}",
        f"formal_epsilon_bound_rows: {int(audit['epsilon_EC_bound_formula_tag'].astype(str).eq('union_bound_over_blocks_universal_hash').sum()) if 'epsilon_EC_bound_formula_tag' in audit.columns else 0}",
    ]
    write_summary(output_dir / "actual_ir_finite_key_summary.txt", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
