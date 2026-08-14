#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from ._security_calibrated_common import chi_from_visibility, load_candidate_frame
    from ._security_round_common import REPO_ROOT, ensure_output_dir, write_summary
except ImportError:
    from _security_calibrated_common import chi_from_visibility, load_candidate_frame
    from _security_round_common import REPO_ROOT, ensure_output_dir, write_summary


RECONCILIATION_CLAIM_BOUNDARY = "public_ec_only_not_secure"


def compute_reconciled_net(
    *,
    total_kept_info_bits: object,
    total_leak_ec_bits: object,
    n_pairs_actual: object,
    coincidence_rate_hz: object,
    leak_source_tag: object,
    coincidence_rate_verified: bool = False,
) -> dict[str, object]:
    """Compute public-EC net PIE/SKR without mixing per-pair and total units.

    The replay totals are deliberately required.  A per-pair leak proxy or a
    surrogate row can remain in the audit table, but cannot produce a main
    reconciled result.
    """

    source = str(leak_source_tag or "")
    if not source.startswith("actual_ir_replay"):
        status = "blocked_missing_actual_ir_replay_leak"
        evidence_source = "reconciliation_inputs_not_actual_ir_replay"
    else:
        kept = pd.to_numeric(pd.Series([total_kept_info_bits]), errors="coerce").iloc[0]
        leak = pd.to_numeric(pd.Series([total_leak_ec_bits]), errors="coerce").iloc[0]
        pairs = pd.to_numeric(pd.Series([n_pairs_actual]), errors="coerce").iloc[0]
        rate = pd.to_numeric(pd.Series([coincidence_rate_hz]), errors="coerce").iloc[0]
        finite_kept = pd.notna(kept) and np.isfinite(float(kept))
        finite_leak = pd.notna(leak) and np.isfinite(float(leak))
        finite_pairs = pd.notna(pairs) and np.isfinite(float(pairs)) and float(pairs) > 0.0
        finite_rate = pd.notna(rate) and np.isfinite(float(rate)) and float(rate) >= 0.0
        rate_verified = finite_rate and coincidence_rate_verified
        if not finite_kept or not finite_leak:
            status = "blocked_missing_actual_replay_totals"
            evidence_source = "actual_ir_replay_totals_missing_or_nonfinite"
        elif not finite_pairs:
            status = "blocked_invalid_n_pairs_actual"
            evidence_source = "actual_ir_replay_n_pairs_missing_or_nonpositive"
        elif not rate_verified:
            status = "blocked_missing_verified_coincidence_rate"
            evidence_source = "coincidence_rate_missing_nonfinite_or_unverified"
        else:
            pie = max(0.0, (float(kept) - float(leak)) / float(pairs))
            skr = pie * float(rate)
            return {
                "PIE_reconciled_net": pie,
                "SKR_reconciled_net_bps": skr,
                "reconciliation_evidence_status": "verified_actual_ir_replay_reconciled_net",
                "reconciliation_evidence_source": "actual_ir_replay_total_kept_minus_total_leak_ec",
                "claim_boundary": RECONCILIATION_CLAIM_BOUNDARY,
            }

    return {
        "PIE_reconciled_net": np.nan,
        "SKR_reconciled_net_bps": np.nan,
        "reconciliation_evidence_status": status,
        "reconciliation_evidence_source": evidence_source,
        "claim_boundary": RECONCILIATION_CLAIM_BOUNDARY,
    }


def _effective_pair_count(
    *,
    n_pairs: float,
    layer_fraction: float,
    accepted_frame_fraction: float,
    block_success_rate: float,
    layer_fraction_source_tag: str,
) -> tuple[float, str]:
    base = float(n_pairs) * float(layer_fraction) * float(accepted_frame_fraction)
    if layer_fraction_source_tag == "actual_from_replay_kept_bits":
        return base, "block_success_already_in_actual_kept_bits"
    return base * float(block_success_rate), "block_success_applied_to_surrogate_layer_fraction"


def _separate_inputs(input_dirs: list[Path]) -> tuple[list[Path], Path | None]:
    candidate_dirs: list[Path] = []
    actual_ir_dir: Path | None = None
    for p in input_dirs:
        if (p / "polar_e2e_results.csv").exists():
            candidate_dirs.append(p)
        elif (p / "actual_ir_point_table.csv").exists():
            actual_ir_dir = p
    return candidate_dirs, actual_ir_dir


def _default_inputs() -> list[Path]:
    return [
        REPO_ROOT / "results" / "e2e_20dB_fullgrid_pairing_v2_candidate_t15",
        REPO_ROOT / "results" / "_tmp_round1b_actual_ir",
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="Build explicit finite-key audit table from candidate and actual-IR replay outputs.")
    ap.add_argument("--input-dirs", nargs="*", default=[])
    ap.add_argument("--franson-visibility", type=float, default=0.95)
    ap.add_argument("--eps-sec", type=float, default=1e-10)
    ap.add_argument("--eps-cor", type=float, default=1e-10)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir, overwrite=bool(args.overwrite))
    input_dirs = [Path(p) for p in args.input_dirs] if args.input_dirs else _default_inputs()
    candidate_dirs, actual_ir_dir = _separate_inputs(input_dirs)
    if not candidate_dirs:
        raise SystemExit("no candidate dir found in --input-dirs")

    perf = pd.concat([load_candidate_frame(p) for p in candidate_dirs], ignore_index=True)
    perf["loss_db"] = pd.to_numeric(perf["loss_db"], errors="coerce").astype(int)
    perf["dimension"] = pd.to_numeric(perf["dimension"], errors="coerce").astype(int)
    perf["bin_width_ps"] = pd.to_numeric(perf["bin_width_ps"], errors="coerce").astype(int)

    actual_df = pd.DataFrame(columns=["loss_db", "dimension", "bin_width_ps"])
    if actual_ir_dir is not None and (actual_ir_dir / "actual_ir_point_table.csv").exists():
        actual_df = pd.read_csv(actual_ir_dir / "actual_ir_point_table.csv")
        actual_df["loss_db"] = pd.to_numeric(actual_df["loss_db"], errors="coerce").astype(int)
        actual_df["dimension"] = pd.to_numeric(actual_df["dimension"], errors="coerce").astype(int)
        actual_df["bin_width_ps"] = pd.to_numeric(actual_df["bin_width_ps"], errors="coerce").astype(int)

    df = perf.merge(
        actual_df,
        on=["loss_db", "dimension", "bin_width_ps"],
        how="left",
        suffixes=("", "_actual"),
    )
    rows = []
    for _, row in df.iterrows():
        d = int(row["dimension"])
        bits = max(1.0, math.log2(max(2, d)))
        n_pairs = pd.to_numeric(pd.Series([row.get("n_pairs_actual")]), errors="coerce").iloc[0]
        actual_total_leak = pd.to_numeric(pd.Series([row.get("total_leak_ec_bits")]), errors="coerce").iloc[0]
        actual_total_leak_legacy_crc = pd.to_numeric(pd.Series([row.get("total_leak_ec_bits_legacy_crc")]), errors="coerce").iloc[0]
        if pd.notna(actual_total_leak) and pd.notna(n_pairs) and float(n_pairs) > 0.0:
            leak_bits = float(actual_total_leak) / float(n_pairs)
            raw_leak_tag = row.get("leak_ec_source_tag")
            leak_tag = str(raw_leak_tag) if pd.notna(raw_leak_tag) else "actual_ir_replay"
        else:
            leak_bits = float(row.get("leak_ec_bits_or_proxy")) if pd.notna(row.get("leak_ec_bits_or_proxy")) else np.nan
            leak_tag = "surrogate_from_best_hard_pie_gap"
        leak_bits_legacy_crc = float(actual_total_leak_legacy_crc) / float(n_pairs) if pd.notna(actual_total_leak_legacy_crc) and pd.notna(n_pairs) and float(n_pairs) > 0.0 else np.nan

        kept_bits = pd.to_numeric(pd.Series([row.get("total_kept_info_bits")]), errors="coerce").iloc[0]
        if pd.notna(kept_bits) and pd.notna(n_pairs) and float(n_pairs) > 0.0:
            layer_fraction = min(1.0, max(0.0, float(kept_bits) / (float(n_pairs) * bits)))
            layer_fraction_tag = "actual_from_replay_kept_bits"
        else:
            layers_success = pd.to_numeric(pd.Series([row.get("layers_success_best")]), errors="coerce").iloc[0]
            layer_fraction = min(1.0, max(0.0, float(layers_success) / bits)) if pd.notna(layers_success) else np.nan
            layer_fraction_tag = "surrogate_from_layers_success_best"

        accepted_frame_fraction_val = row.get("frame_success_rate")
        accepted_frame_fraction = pd.to_numeric(pd.Series([accepted_frame_fraction_val]), errors="coerce").iloc[0]
        if pd.notna(accepted_frame_fraction):
            accepted_frame_tag = "actual_frame_success_rate"
        else:
            accepted_frame_fraction = pd.to_numeric(pd.Series([row.get("clean_pair_fraction")]), errors="coerce").iloc[0]
            accepted_frame_tag = "surrogate_clean_pair_fraction" if pd.notna(accepted_frame_fraction) else "MISSING"
        rejected_frame_fraction = (1.0 - float(accepted_frame_fraction)) if pd.notna(accepted_frame_fraction) else np.nan

        verification_accept_value = row.get("verification_accept_rate", row.get("block_success_rate"))
        block_success_rate = pd.to_numeric(pd.Series([verification_accept_value]), errors="coerce").iloc[0]
        if pd.isna(block_success_rate):
            block_success_rate = 1.0
            block_success_rate_tag = "surrogate_unity_no_replay_block_rate"
        else:
            block_success_rate_tag = "actual_verification_accept_rate"

        accepted_rate_proxy = np.nan
        coincidence_rate_value = row.get("coincidence_rate_hz")
        if pd.isna(pd.to_numeric(pd.Series([coincidence_rate_value]), errors="coerce").iloc[0]):
            coincidence_rate_value = row.get("coincidence_rate_hz_actual")
        coincidence_rate = pd.to_numeric(pd.Series([coincidence_rate_value]), errors="coerce").iloc[0]
        coincidence_rate_source_tag = str(row.get("coincidence_rate_source_tag", ""))
        coincidence_rate_verified = coincidence_rate_source_tag in {
            "explicit_acquisition_duration",
            "grid_table_preserved_measured_rate",
            "source_candidate_preserved_measured_rate",
            "authoritative_candidate_grid_table_preserved_measured_rate",
        }
        if pd.notna(coincidence_rate) and pd.notna(accepted_frame_fraction) and pd.notna(block_success_rate):
            accepted_rate_proxy = float(coincidence_rate) * float(accepted_frame_fraction) * float(block_success_rate)

        reconciliation = compute_reconciled_net(
            total_kept_info_bits=row.get("total_kept_info_bits"),
            total_leak_ec_bits=row.get("total_leak_ec_bits"),
            n_pairs_actual=n_pairs,
            coincidence_rate_hz=coincidence_rate,
            leak_source_tag=leak_tag,
            coincidence_rate_verified=coincidence_rate_verified,
        )

        n_eff_pairs = np.nan
        n_eff_pairs_rule = "MISSING"
        if pd.notna(n_pairs) and pd.notna(layer_fraction) and pd.notna(accepted_frame_fraction) and pd.notna(block_success_rate):
            n_eff_pairs, n_eff_pairs_rule = _effective_pair_count(
                n_pairs=float(n_pairs),
                layer_fraction=float(layer_fraction),
                accepted_frame_fraction=float(accepted_frame_fraction),
                block_success_rate=float(block_success_rate),
                layer_fraction_source_tag=layer_fraction_tag,
            )

        epsilon_ec_bound = pd.to_numeric(pd.Series([row.get("epsilon_EC_bound")]), errors="coerce").iloc[0]
        eps_cor_total = float(epsilon_ec_bound) if pd.notna(epsilon_ec_bound) else float(args.eps_cor)
        delta_fk = np.nan
        if pd.notna(n_eff_pairs) and float(n_eff_pairs) > 0.0:
            delta_fk = 4.0 * math.sqrt(math.log2(2.0 / float(args.eps_sec)) / float(n_eff_pairs))
            delta_fk += 2.0 * math.log2(2.0 / float(eps_cor_total)) / float(n_eff_pairs)

        # KNOWN-ISSUE (docs/decision-log.md 2026-08-14): this column stores the
        # dimensionless accepted-frame fraction (0..1) and the consumers subtract
        # it as if it were bits/symbol. Acceptance is already accounted for
        # multiplicatively via accepted_rate_proxy and via n_eff_pairs in DeltaFK,
        # so the subtraction is a redundant, dimensionally wrong third application.
        # The column is kept for provenance only; the consuming secure columns are
        # blocked as scientifically_blocked_dimensional_inconsistency.
        post_sel = float(accepted_frame_fraction) if pd.notna(accepted_frame_fraction) else np.nan
        chi_e = chi_from_visibility(dimension=d, franson_visibility=float(args.franson_visibility))

        rows.append(
            {
                "loss_db": int(row["loss_db"]),
                "dimension": d,
                "bin_width_ps": int(row["bin_width_ps"]),
                "franson_visibility_global": float(args.franson_visibility),
                "IAB_est": row.get("IAB_est"),
                "leak_EC_actual_bits": leak_bits,
                "leak_EC_actual_bits_legacy_crc": leak_bits_legacy_crc,
                "leak_EC_source_tag": leak_tag,
                "total_kept_info_bits": row.get("total_kept_info_bits"),
                "total_leak_ec_bits": row.get("total_leak_ec_bits"),
                "eps_sec": float(args.eps_sec),
                "eps_cor": float(args.eps_cor),
                "eps_cor_total": eps_cor_total,
                "eps_cor_from_epsilon_EC": float(epsilon_ec_bound) if pd.notna(epsilon_ec_bound) else np.nan,
                "eps_cor_budget_rule": "verification_only_shadow" if pd.notna(epsilon_ec_bound) else "legacy_eps_cor",
                "epsilon_EC_in_budget_flag": 1 if pd.notna(epsilon_ec_bound) else 0,
                "n_eff_pairs": n_eff_pairs,
                "n_eff_pairs_rule": n_eff_pairs_rule,
                "clean_pair_fraction": row.get("clean_pair_fraction"),
                "layer_fraction": layer_fraction,
                "layer_fraction_source_tag": layer_fraction_tag,
                "accepted_frame_fraction": accepted_frame_fraction,
                "accepted_frame_fraction_source_tag": accepted_frame_tag,
                "rejected_frame_fraction": rejected_frame_fraction,
                "exactly_one_click_fraction": "MISSING",
                "post_selection_correction": post_sel,
                "block_success_rate_used": block_success_rate,
                "block_success_rate_source_tag": block_success_rate_tag,
                "accepted_rate_proxy": accepted_rate_proxy,
                "DeltaFK_calibrated": delta_fk,
                "chi_E_calibrated": chi_e,
                "verification_bits_used_actual": row.get("verification_bits_used_actual"),
                "verification_bits_used_actual_legacy_crc": row.get("verification_bits_used_actual_legacy_crc"),
                "lambda_ver_bits_actual": row.get("lambda_ver_bits_actual"),
                "lambda_ver_source_tag": row.get("lambda_ver_source_tag"),
                "lambda_ver_bits_legacy_crc": row.get("lambda_ver_bits_legacy_crc"),
                "verification_protocol_id": row.get("verification_protocol_id"),
                "verification_invoked_block_count": row.get("verification_invoked_block_count"),
                "verification_pass_count": row.get("verification_pass_count"),
                "verification_fail_count": row.get("verification_fail_count"),
                "undetected_error_count_empirical": row.get("undetected_error_count_empirical"),
                "epsilon_EC_empirical": row.get("epsilon_EC_empirical"),
                "epsilon_EC_empirical_source_tag": row.get("epsilon_EC_empirical_source_tag"),
                "epsilon_EC_bound": row.get("epsilon_EC_bound"),
                "epsilon_EC_bound_formula_tag": row.get("epsilon_EC_bound_formula_tag"),
                "decoder_fail_rate_oracle": row.get("decoder_fail_rate_oracle"),
                "decoder_fail_rate_oracle_source_tag": row.get("decoder_fail_rate_oracle_source_tag"),
                "n_pairs_actual": row.get("n_pairs_actual"),
                "coincidence_rate_hz": coincidence_rate,
                "coincidence_rate_source_tag": coincidence_rate_source_tag,
                **reconciliation,
                "best_hard_PIE": row.get("best_hard_PIE"),
                "PIE_practical": row.get("PIE_practical"),
                "SKR_measured_bps": row.get("SKR_measured_bps"),
                "processing_rule_version": row.get("processing_rule_version"),
                "pairing_path_tag": row.get("pairing_path_tag"),
                "pairing_window_source_tag": row.get("pairing_window_source_tag"),
                "threshold_ps": row.get("threshold_ps"),
                "effective_pairing_window_ps": row.get("effective_pairing_window_ps"),
                "threshold_ratio_to_bw": row.get("threshold_ratio_to_bw"),
            }
        )

    audit = pd.DataFrame(rows).sort_values(["loss_db", "dimension", "bin_width_ps"]).reset_index(drop=True)
    audit.to_csv(output_dir / "finite_key_audit_point_table.csv", index=False)
    summary_lines = [
        "input_dirs:",
        *[f"  - {p}" for p in input_dirs],
        f"point_count: {len(audit)}",
        f"actual_leak_rows: {int(audit['leak_EC_source_tag'].astype(str).str.startswith('actual_ir_replay').sum())}",
        "DeltaFK_explicit_inputs: n_pairs_actual, layer_fraction, accepted_frame_fraction, conditional block_success_rate_used, eps_sec, eps_cor_total",
        f"post_selection_sensitive_rows: {int(pd.to_numeric(audit['post_selection_correction'], errors='coerce').notna().sum())}",
    ]
    write_summary(output_dir / "round2_finite_key_audit_summary.txt", summary_lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
