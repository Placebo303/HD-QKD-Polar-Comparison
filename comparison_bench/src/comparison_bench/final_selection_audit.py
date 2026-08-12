"""Read-only Phase-4 audit for the locked final IR method-selection run."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


REQUIRED_ROUTE_A_FIELDS = (
    "verification_protocol_id", "verification_family", "verification_scope",
    "verification_seed_policy", "verification_public_message_rule",
    "verification_tag_bits", "point_id", "loss_db", "dimension", "bin_width_ps",
    "layer_id", "block_index", "syndrome_bits_revealed",
    "verification_bits_used_actual", "lambda_ver_bits_actual",
    "verification_invoked_block_count", "undetected_error_count_empirical",
    "epsilon_EC_bound", "epsilon_EC_empirical", "decoder_fail_rate_oracle",
    "eps_cor_total", "eps_cor_from_epsilon_EC",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exact_two_sided_binomial(discordant_a: int, discordant_b: int) -> float:
    """Exact two-sided McNemar/binomial p-value (null p=0.5)."""
    n = discordant_a + discordant_b
    if n == 0:
        return 1.0
    k = min(discordant_a, discordant_b)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def decide_paired_outcome(
    *, eligible: bool, cascade_only_success: int, layered_ldpc_only_success: int,
    p_value: float, alpha: float,
) -> tuple[str, str]:
    """Apply the locked decision rule without adapting sample size or direction."""
    if not eligible:
        return "insufficient_evidence", "audit_preconditions_failed"
    if cascade_only_success == layered_ldpc_only_success:
        return "no_decision", "no_discordant_pairs"
    if p_value >= alpha:
        return "no_decision", "pre_registered_test_not_significant"
    if cascade_only_success > layered_ldpc_only_success:
        return "cascade_lite", "pre_registered_paired_test_significant"
    return "layered_ldpc_lite", "pre_registered_paired_test_significant"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative_or_absolute(value: str, root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def audit(v1_dir: Path, v2_dir: Path) -> dict:
    """Audit only persisted artifacts; return serializable evidence and decision."""
    v1_dir, v2_dir = Path(v1_dir), Path(v2_dir)
    lock_path = v1_dir / "data_lock_manifest.json"
    invalid_path = v1_dir / "invalid_run_notice.json"
    manifest_path = v2_dir / "run_manifest.json"
    grid_path = v2_dir / "predeclared_tuning_grid.json"
    frozen_path = v2_dir / "frozen_candidate_configs.json"
    outcomes_path = v2_dir / "confirmation_frame_outcomes.csv"
    summary_path = v2_dir / "aggregate_summary.csv"
    for path in (lock_path, invalid_path, manifest_path, grid_path, frozen_path, outcomes_path, summary_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    lock, run, grid, frozen = map(_read_json, (lock_path, manifest_path, grid_path, frozen_path))
    ledger: dict[str, dict] = {}
    references = {
        "v1_data_lock_manifest": lock_path, "v1_invalid_run_notice": invalid_path,
        "v1_locked_frame_split": Path(lock["locked_split"]["path"]),
        "v1_source": Path(lock["source"]["path"]), "v2_run_manifest": manifest_path,
        "v2_predeclared_tuning_grid": grid_path, "v2_frozen_candidate_configs": frozen_path,
        "v2_confirmation_frame_outcomes": outcomes_path, "v2_aggregate_summary": summary_path,
    }
    for name, path in references.items():
        recorded = None
        if name == "v1_locked_frame_split": recorded = lock["locked_split"]["sha256"]
        elif name == "v1_source": recorded = lock["source"]["sha256"]
        elif name == "v1_data_lock_manifest": recorded = run.get("data_lock_sha256")
        ledger[name] = {"path": str(path), "sha256": sha256_file(path), "recorded_sha256": recorded,
                        "recorded_hash_matches": None if recorded is None else sha256_file(path) == recorded}

    split_rows = list(csv.DictReader((v1_dir / "locked_frame_split.csv").open(encoding="utf-8", newline="")))
    locked = {r["locked_frame_key"] for r in split_rows if r["split"] == "confirmation"}
    required_confirmation = int(lock["counts"]["required_confirmation_frames_per_stratum"])
    outcomes = list(csv.DictReader(outcomes_path.open(encoding="utf-8", newline="")))
    candidates = ("cascade_lite", "layered_ldpc_lite")
    by_method = {m: [r for r in outcomes if r["method"] == m and r["split"] == "confirmation"] for m in candidates}
    keys = {m: [r["locked_frame_key"] for r in rows] for m, rows in by_method.items()}
    shared = all(len(keys[m]) == required_confirmation and len(set(keys[m])) == required_confirmation and set(keys[m]) == locked for m in candidates)
    status_counts = {m: {} for m in candidates}
    outcomes_by_key = {}
    for method, rows in by_method.items():
        for row in rows:
            status_counts[method][row["frame_status"]] = status_counts[method].get(row["frame_status"], 0) + 1
            outcomes_by_key.setdefault(row["locked_frame_key"], {})[method] = row["verified_success"].strip().lower() == "true"
    missing_pairs = sorted(k for k in locked if set(outcomes_by_key.get(k, {})) != set(candidates))
    a_only = sum(v["cascade_lite"] and not v["layered_ldpc_lite"] for v in outcomes_by_key.values() if len(v) == 2)
    b_only = sum(v["layered_ldpc_lite"] and not v["cascade_lite"] for v in outcomes_by_key.values() if len(v) == 2)
    p_value = exact_two_sided_binomial(a_only, b_only)
    alpha = float(lock["decision_rule"]["alpha"])
    aggregate = {r["method"]: r for r in csv.DictReader(summary_path.open(encoding="utf-8", newline="")) if r["split"] == "confirmation"}
    aggregate_has_candidates = set(candidates).issubset(aggregate)
    aggregate_matches = aggregate_has_candidates and all(
        int(aggregate[m]["attempted_frames"]) == len(by_method[m]) and
        int(aggregate[m]["verified_successes"]) == sum(r["verified_success"].lower() == "true" for r in by_method[m]) and
        int(aggregate[m]["failed_frames"]) == sum(r["verified_success"].lower() != "true" for r in by_method[m])
        for m in candidates
    )
    persisted_grid = grid.get("grid", {})
    frozen_candidates = frozen.get("candidates", {})
    frozen_matches_grid = all(m in frozen_candidates and m in persisted_grid and frozen_candidates[m]["config"] in persisted_grid[m] for m in candidates)
    failed_checks = []
    if len(locked) != required_confirmation:
        failed_checks.append("locked_confirmation_count_matches_declared_requirement")
    if not shared: failed_checks.append("same_60_unique_locked_confirmation_keys")
    if missing_pairs: failed_checks.append("complete_paired_outcomes")
    if not aggregate_matches: failed_checks.append("aggregate_matches_frame_rows")
    if not frozen_matches_grid: failed_checks.append("frozen_configurations_match_persisted_corrected_grid")
    if frozen.get("frozen_before_confirmation") is not True: failed_checks.append("frozen_before_confirmation")
    if run.get("status") != "completed_within_bound": failed_checks.append("bounded_run_completed")
    if run.get("source_sha256_verified") is not True: failed_checks.append("source_sha256_verified")
    if run.get("preprocessing_mapping_verification") != lock.get("preprocessing_mapping_verification_contract"):
        failed_checks.append("shared_preprocessing_mapping_verification_contract")
    if any(x["recorded_hash_matches"] is False for x in ledger.values()): failed_checks.append("recorded_hash_matches")
    audit_passed = not failed_checks
    decision, decision_reason = decide_paired_outcome(
        eligible=audit_passed, cascade_only_success=a_only,
        layered_ldpc_only_success=b_only, p_value=p_value, alpha=alpha,
    )
    return {
        "audit_passed": audit_passed,
        "decision": decision, "decision_reason": decision_reason,
        "alpha": alpha, "exact_two_sided_p_value": p_value,
        "paired_outcomes": {"cascade_only_success": a_only, "layered_ldpc_only_success": b_only, "discordant_pairs": a_only + b_only, "missing_pairs": missing_pairs},
        "frame_identity": {"locked_confirmation_unique_keys": len(locked), "candidate_key_counts": {m: len(keys[m]) for m in candidates}, "same_60_unique_locked_keys": shared},
        "status_counts": status_counts, "aggregate_matches_frame_rows": aggregate_matches,
        "frozen_configurations_match_persisted_corrected_grid": frozen_matches_grid,
        "failed_checks": failed_checks,
        "leakage": {m: {"same_method_total_leak_bits": aggregate.get(m, {}).get("same_method_total_leak_bits"), "ranked_across_methods": False,
                         "note": aggregate.get(m, {}).get("leakage_comparison_note")} for m in candidates},
        "hash_ledger": ledger, "domain": lock["domain"],
        "non_claims": ["No claim outside real d=1024, 64-symbol frames, dataset raw-SER [0.20, 0.30).",
                       "No Polar or qLDPC winner comparison; they were not frame-identical executable candidates.",
                       "No cross-method leakage ranking and no Route A numerical/proof claim."],
    }


def route_a_gate() -> dict:
    """Document-schema gate: Phase-3 outcomes do not carry Route-A proof fields."""
    return {"gate": "fail", "mode": "non_numerical_documented_field_compatibility", "route_a_required_fields": list(REQUIRED_ROUTE_A_FIELDS),
            "present_in_phase3_confirmation_schema": [], "missing_fields": list(REQUIRED_ROUTE_A_FIELDS),
            "reason": "Phase-3 comparison outcomes provide crc32 verification and method-local leak_bits_frame, not the documented Route A universal-hash correctness interface.",
            "non_claim": "No Route A run, numerical result, or formal-proof completion is inferred."}
