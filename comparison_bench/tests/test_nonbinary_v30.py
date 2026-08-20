"""Small, in-memory tests for the V30R finite-graph construction packet.

These tests intentionally do not invoke DE, a decoder, parquet loading, or a
V30R production output root.  The M0 test only rebuilds the accepted V28R
matrix in memory and reads its already-persisted canonical directory metadata.
"""
from __future__ import annotations

from pathlib import Path
import uuid
import json
from copy import deepcopy

import pytest

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v30 as v30
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v28 as v28


def test_frozen_gf32_metadata():
    cfg = v30.frozen_v30r_config(n=16)
    assert cfg["field"]["constructor"] == "GF2mField.create(32)"
    assert cfg["field"]["primitive_polynomial"] == 0b100101
    assert cfg["field"]["field_id"] == v30.FIELD_ID
    assert tuple(v30.FIELD.nonzero_cycle) == tuple(dict.fromkeys(v30.FIELD.nonzero_cycle))


def test_m0_reproduces_v28r_baseline_without_scientific_inputs():
    report = v30.run_m0_baseline()
    assert report["ok"]
    assert all(report["canonical_config_checks"].values())
    assert all(report["canonical_source_checks"].values())
    assert report["scientific_inputs_read"] == []
    assert report["de_rerun"] is False and report["decoder_rerun"] is False
    assert report["expected_l1_counts"] == {
        "support_group_count": 15,
        "max_support_group_multiplicity": 69,
        "duplicate_projective_classes": 303,
        "affected_columns": 922,
        "proportional_pairs": 1107,
    }


def test_projective_key_and_duplicate_audit():
    matrix = ((1, 0, 1), (1, 2, 2), (0, 1, 0))
    audit = v30.projective_column_audit(matrix)
    assert audit["columns"][0]["projective_key"] == [0, 1, 1]
    # Columns 1 and 2 share support (0,1), but their ratios differ.
    assert audit["duplicate_projective_classes"] == 0
    duplicate = ((1, 1), (1, 1), (0, 0))
    assert v30.projective_column_audit(duplicate)["duplicate_projective_classes"] == 1


def test_balanced_and_peg_supports_are_deterministic_and_lexicographic():
    for family in (v30.FAMILY_BALANCED, v30.FAMILY_PEG):
        first = v30.build_supports(family, 5, 25)
        second = v30.build_supports(family, 5, 25)
        assert first == second
        assert all(a < b for a, b in first)
        assert len(first) == 25


def test_tanner6_canonical_and_frc_degenerate_product():
    # Current column (0,1), prior columns (0,2) and (1,2), all coefficients 1.
    result = v30.newly_closed_tanner6(
        v30.FIELD,
        [(0, 2), (1, 2)],
        [(1, 1), (1, 1)],
        2,
        (0, 1),
        (1, 1),
    )
    expected = (2, 0, 0, 2, 1, 1)
    assert result["new_cycle_count"] == 1
    assert result["degenerate_6_new"] == 1
    assert result["canonical_degenerate_cycles"] == [expected]
    assert v30.canonical_tanner6_tuple(2, 1, 1, 2, 0, 0) == expected
    assert v30.tanner6_alternating_product(v30.FIELD, (1, 1), (1, 1), (1, 1)) == 1


def test_tanner6_non_degenerate_candidate_score_changes_with_ratio():
    # Product is 1/ratio in this simple cycle, so ratio 1 is degenerate and
    # ratio 2 is not.
    assert v30.score_tanner6_candidate(
        v30.FIELD, [(0, 2), (1, 2)], [(1, 1), (1, 1)], 2, (0, 1), 1
    ) == 1
    assert v30.score_tanner6_candidate(
        v30.FIELD, [(0, 2), (1, 2)], [(1, 1), (1, 1)], 2, (0, 1), 2
    ) == 0


def test_projective_ratio_direction_and_duplicate_is_rejected_before_tanner6(monkeypatch):
    duplicate_ratio = v30.FIELD.mul(4, v30.FIELD.inverse(2))
    assert duplicate_ratio == 2
    assert v30.projective_key(v30.FIELD, (0, 1), (2, 4)) == (0, 1, duplicate_ratio)
    seen: list[int] = []

    def score(_field, _supports, _coefficients, _column, _support, ratio):
        assert int(ratio) != duplicate_ratio
        seen.append(int(ratio))
        return 0

    monkeypatch.setattr(v30, "score_tanner6_candidate", score)
    selected = v30.select_projective_ratio(
        v30.FIELD, [(0, 1)], [(2, 4)], 1, (0, 1), None,
    )
    assert duplicate_ratio not in seen
    assert selected["ratio"] != duplicate_ratio
    assert selected["ratio_index"] == 0  # first nonzero-cycle element is 1


def test_build_layer_projective_safe_rank_and_replay():
    matrix, audit = v30.build_layer(5, 40, family=v30.FAMILY_BALANCED)
    assert np.asarray(matrix).shape == (5, 40)
    assert audit["construction_ok"]
    assert audit["projective_hard_gate"]
    assert audit["projective"]["duplicate_projective_classes"] == 0
    assert audit["rank"] == 5
    assert len(audit["label_replay"]) == 40
    assert all(row["selected_score"][1] == row["selected_ratio_index"] for row in audit["label_replay"])
    assert audit["tanner6_newly_closed_total"] >= audit["tanner6_degenerate_total"]
    assert audit["tanner6_degenerate_max_per_column"] >= 0


def test_build_layer_peg_has_same_replay_contract():
    matrix, audit = v30.build_layer(4, 24, family=v30.FAMILY_PEG)
    assert np.asarray(matrix).shape == (4, 24)
    assert audit["family"] == v30.FAMILY_PEG
    assert audit["construction_ok"]
    assert audit["tanner8_rule"] == "topology_only"
    assert audit["standard_variable_side_ace"] == "omitted_for_dv_2"


def test_peg_exact_tuple_has_explicit_unreachable_semantics():
    assert v30.peg_support_score(4, [], (0, 3)) == (0, 0, 1, 2, 0, 3)
    # Prior edges 0-1 and 1-2 give d_check(0,2)=2 and local Tanner score 6.
    assert v30.peg_support_score(4, [(0, 1), (1, 2)], (0, 2)) == (1, -6, 2, 12, 0, 2)


def test_matrix_packet_has_independent_l2_and_four_cycle_components():
    packet = v30.build_matrix_packet(
        4, {"1M": 4, "1p5M": 5, "2M": 6}, n=20,
        family=v30.FAMILY_BALANCED, allocation_id="test_m1_4",
    )
    assert packet["construction_ok"]
    assert set(packet["matrices"]["L2"]) == set(v30.SOURCE_ORDER)
    assert set(packet["four_cycle_components"]) == {"L1", "L2:1M", "L2:1p5M", "L2:2M"}
    assert packet["four_cycle_count"] == sum(packet["four_cycle_components"].values())
    # Each layer starts with an independent empty graph/ratio state.
    l1_again, _ = v30.build_layer(4, 20, family=v30.FAMILY_BALANCED)
    assert packet["matrices"]["L1"] == l1_again
    assert packet["matrices"]["L2"]["1M"] == l1_again


def test_topology_metrics_are_aggregate_only():
    metrics = v30.cycle_topology([(0, 1), (1, 2), (0, 2), (0, 1)])
    assert metrics["four_cycle_count"] == 1
    assert metrics["six_cycle_count"] == 2
    # K4 has all three undirected Hamiltonian 4-check cycles.
    assert v30.cycle_topology([(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)])["eight_cycle_count"] == 3


def test_v28r_canonical_binding_is_read_only_and_exact():
    root = Path(v30._repo_root()) / v30.V28R_CANONICAL
    assert (root / "v28_config.json").exists()
    assert (root / "v28_evidence.json").exists()
    assert (root / "RUN_MANIFEST.json").exists()
    assert (root / "readonly_verify.json").exists()


def _fake_blocks(n: int = 16) -> list[dict]:
    blocks = []
    for source in v30.SOURCE_ORDER:
        for block_index in range(v30.BLOCKS_PER_SOURCE):
            blocks.append({
                "source": source, "source_id": v30.SOURCE_IDS[source],
                "delay_used_ps": v30.SOURCE_DELAY_PS[source],
                "block_index": block_index, "frame_ids": [],
                "public": {"bob_symbols": [0] * n, "s1": [0] * 3, "s2": [0] * 3},
            })
    return blocks


def _tiny_packet() -> dict:
    audit = {
        "shape": [1, 2], "rank": 1, "full_row_rank": True,
        "projective_hard_gate": True, "tanner6_newly_closed_total": 0,
        "tanner6_degenerate_total": 0, "tanner6_degenerate_max_per_column": 0,
        "tanner8_rule": "topology_only",
        "projective": {
            "columns": [
                {"column": 0, "valid": True, "projective_key": [0, 1, 1]},
                {"column": 1, "valid": True, "projective_key": [0, 1, 2]},
            ],
            "duplicate_projective_classes": 0, "affected_columns": 0,
        },
        "label_replay": [],
    }
    matrix = [[1, 1]]
    return {
        "packet_id": "tiny-packet", "matrix_id": "tiny-matrix",
        "allocation_id": "m1_9", "family": v30.FAMILY_BALANCED, "m1": 9,
        "m2_by_source": {"1M": 191, "1p5M": 197, "2M": 199},
        "construction_ok": True, "projective_hard_gate": True,
        "full_row_rank": True, "field": {
            "constructor": "GF2mField.create(32)", "primitive_polynomial": v30.PRIMITIVE_POLYNOMIAL,
            "field_id": v30.FIELD_ID,
        },
        "four_cycle_components": {"L1": 0, "L2:1M": 0, "L2:1p5M": 0, "L2:2M": 0},
        "four_cycle_count": 0,
        "matrices": {"L1": matrix, "L2": {label: matrix for label in v30.SOURCE_ORDER}},
        "audits": {"L1": audit, "L2": {label: audit for label in v30.SOURCE_ORDER}},
    }


def _tiny_m1_records(allocations):
    screen_items = list(v30._screen_items(allocations))
    screen_calls = [{**item, "converged": True, "final_entropy_bits": 0.0,
                     "iterations": 1, "terminal": "converged", "entropy_trace_bits": [],
                     "runtime_s": 0.0, "call_index": index}
                    for index, item in enumerate(screen_items)]
    selected = ["m1_9", "m1_12"]
    ranks = {allocation["allocation_id"]: list(v30._allocation_rank(
        screen_calls, allocation)) for allocation in allocations}
    screen = {
        "schema": "nbldpc_v30r_de_allocation_screen_v1", "calls": screen_calls,
        "n_calls": 72, "expected_calls": 72,
        "allocation_call_counts": {allocation["allocation_id"]: 12 for allocation in allocations},
        "allocation_eligibility": {allocation["allocation_id"]: True for allocation in allocations},
        "eligible_allocations": [allocation["allocation_id"] for allocation in allocations],
        "rank_tuples": ranks, "selected_allocations": selected,
        "resource_meter_seconds": 0.0, "resource_limit_seconds": v30.RESOURCE_LIMIT_SECONDS,
        "terminal": None, "registered_plan_calls": 72,
    }
    confirmation_items = []
    by_id = {allocation["allocation_id"]: allocation for allocation in allocations}
    for allocation_id in selected:
        confirmation_items.extend(v30._confirmation_items(by_id[allocation_id]))
    confirmation_calls = [{**item, "converged": True, "final_entropy_bits": 0.0,
                           "iterations": 1, "terminal": "converged", "entropy_trace_bits": [],
                           "runtime_s": 0.0, "call_index": index}
                          for index, item in enumerate(confirmation_items)]
    confirmation = {
        "schema": "nbldpc_v30r_de_allocation_confirmation_v1", "calls": confirmation_calls,
        "n_calls": 60, "expected_max_calls": 60, "selected_allocations": selected,
        "allocation_call_counts": {allocation_id: 30 for allocation_id in selected},
        "allocation_confirmed": {allocation_id: True for allocation_id in selected},
        "confirmed_allocations": selected, "resource_meter_seconds": 0.0,
        "resource_limit_seconds": v30.RESOURCE_LIMIT_SECONDS, "terminal": "de_allocation_pass",
    }
    return screen, confirmation


def _tiny_block_records(packet):
    truth1, truth2 = [0, 1], [0, 1]
    syndrome1 = v28.compute_syndrome(v30.FIELD, packet["matrices"]["L1"], truth1)
    syndrome2 = v28.compute_syndrome(v30.FIELD, packet["matrices"]["L2"]["1M"], truth2)
    records = []
    for stage, indices in (("screen", range(20)), ("confirmation", range(20, 70))):
        for source in v30.SOURCE_ORDER:
            for block_index in indices:
                start = v30.SOURCE_FRAME_RANGES[source][0] + block_index * v30.BLOCK_FRAMES
                records.append({
                    "schema": "nbldpc_v30r_block_result_v1", "packet_id": packet["packet_id"],
                    "source": source, "source_id": v30.SOURCE_IDS[source],
                    "delay_used_ps": v30.SOURCE_DELAY_PS[source], "block_index": block_index,
                    "frame_ids": list(range(start, start + v30.BLOCK_FRAMES)), "stage": stage,
                    "l1_status": "success", "l2_status": "success",
                    "l1_ok": True, "l2_ok": True, "l2_not_run_due_l1": False,
                    "l1_syndrome": syndrome1, "l2_syndrome": syndrome2,
                    "l1_syndrome_target": syndrome1, "l2_syndrome_target": syndrome2,
                    "truth_x1": truth1, "truth_x2": truth2,
                    "decoded_x1": truth1, "decoded_x2": truth2,
                    "offline_exact": True, "tag_verified": True, "false_accept": False,
                    "runtime_s": 0.0, "l1_iterations": 1, "l2_iterations": 1,
                })
    return records


def _patch_tiny_verifier(monkeypatch):
    baseline = {"ok": True, "expected_l1_counts": {
        "support_group_count": 15, "max_support_group_multiplicity": 69,
        "duplicate_projective_classes": 303, "affected_columns": 922, "proportional_pairs": 1107,
    }, "reproduced": {}}
    monkeypatch.setattr(v30, "load_bound_h_values", lambda: v30.SOURCE_H)
    monkeypatch.setattr(v30, "run_m0_baseline", lambda: baseline)

    def tiny_build(m1, m2_by_source, *, family, n, allocation_id):
        packet = deepcopy(_tiny_packet())
        packet["allocation_id"] = allocation_id
        packet["family"] = family
        packet["m1"] = int(m1)
        packet["m2_by_source"] = dict(m2_by_source)
        return packet

    monkeypatch.setattr(v30, "build_matrix_packet", tiny_build)


@pytest.fixture
def _tiny_gate_evidence(monkeypatch):
    """Create one tiny, fully additive evidence root without n=1024 builds."""
    packet = _tiny_packet()
    allocations = v30.build_allocation_plan(h_values=v30.SOURCE_H)
    screen, confirmation = _tiny_m1_records(allocations)
    records = _tiny_block_records(packet)
    selection = v30._m3_recompute_selection([packet], records)
    m3 = {
        "schema": "nbldpc_v30r_finite_gate_v1", "status": v30.TERMINAL_PASS,
        "screen_outcomes": selection["screen_outcomes"], "screen_eligible": selection["screen_eligible"],
        "top_ranked_packet_ids": selection["top_ranked_packet_ids"],
        "selected_packet_id": selection["selected_packet_id"], "confirmation": selection["confirmation"],
        "records": records, "record_count": len(records), "resource_meter_seconds": 0.0,
        "resource_limit_seconds": v30.RESOURCE_LIMIT_SECONDS,
        "source_summary": {}, "screen_source_summary": {}, "confirmation_source_summary": {},
        "no_fallback_confirmation": True, "screen_block_window": [0, 19],
        "confirmation_block_window": [20, 69],
    }
    baseline = {"ok": True, "expected_l1_counts": {
        "support_group_count": 15, "max_support_group_multiplicity": 69,
        "duplicate_projective_classes": 303, "affected_columns": 922, "proportional_pairs": 1107,
    }, "reproduced": {}}
    root = Path("workspace/v30r_tests") / f"tiny_tamper_{uuid.uuid4().hex}"
    with monkeypatch.context() as patch:
        patch.setattr(v30, "load_bound_h_values", lambda: v30.SOURCE_H)
        patch.setattr(v30, "run_m0_baseline", lambda: baseline)
        patch.setattr(v30, "run_m1_screen", lambda *args, **kwargs: screen)
        patch.setattr(v30, "run_m1_confirmation", lambda *args, **kwargs: confirmation)
        patch.setattr(v30, "build_confirmed_packets", lambda *args: {
            "schema": "nbldpc_v30r_matrix_construction_v1", "packets": [packet],
            "rejected": [], "packet_cap": 4, "packet_cap_ok": True,
        })
        patch.setattr(v30, "load_validation_blocks", lambda: [])
        patch.setattr(v30, "run_m3_gate", lambda *args, **kwargs: m3)
        patch.setattr(v30, "verify_v30r", lambda *args: {"ok": True, "no_de_rerun": True, "no_decoder_rerun": True})
        v30.run_v30r_gate(
            root,
            de_runner=lambda item: {"converged": True, "final_entropy_bits": 0.0, "runtime_s": 0.0},
            decoder_runner=lambda *args: None,
        )
    return root


def test_m1_exact_72_calls_and_confirmation_cap():
    allocations = v30.build_allocation_plan()
    screen = v30.run_m1_screen(
        allocations,
        de_runner=lambda item: {"converged": True, "final_entropy_bits": 0.0, "runtime_s": 0.0},
    )
    assert screen["n_calls"] == 72
    assert all(value == 12 for value in screen["allocation_call_counts"].values())
    assert screen["selected_allocations"] == ["m1_9", "m1_12"]
    confirmation = v30.run_m1_confirmation(
        screen, allocations,
        de_runner=lambda item: {"converged": True, "final_entropy_bits": 0.0, "runtime_s": 0.0},
    )
    assert confirmation["n_calls"] == 60
    assert all(value == 30 for value in confirmation["allocation_call_counts"].values())
    assert confirmation["confirmed_allocations"] == ["m1_9", "m1_12"]


def test_m1_failed_allocation_still_completes_and_other_selection_continues():
    allocations = v30.build_allocation_plan()

    def runner(item):
        if item["m1"] == 9:
            return {"converged": False, "final_entropy_bits": 0.5, "runtime_s": 0.0}
        return {"converged": True, "final_entropy_bits": 0.0, "runtime_s": 0.0}

    screen = v30.run_m1_screen(allocations, de_runner=runner)
    assert screen["n_calls"] == 72
    assert screen["allocation_call_counts"]["m1_9"] == 12
    assert "m1_9" not in screen["eligible_allocations"]
    assert len(screen["selected_allocations"]) == 2


def test_m1_resource_persists_current_call_before_blocking():
    allocations = v30.build_allocation_plan()
    screen = v30.run_m1_screen(
        allocations,
        de_runner=lambda item: {"converged": True, "final_entropy_bits": 0.0, "runtime_s": 1.0},
        resource_limit_seconds=0.5,
    )
    assert screen["terminal"] == v30.TERMINAL_RESOURCE
    assert screen["n_calls"] == 1


def test_m3_bob_only_sequential_success_and_evidence_counts():
    packet = v30.build_matrix_packet(
        3, {"1M": 3, "1p5M": 3, "2M": 3}, n=16,
        family=v30.FAMILY_BALANCED, allocation_id="a",
    )
    packet["packet_id"] = "packet-a"
    calls = []

    def decoder(block, public, adapter, packet_arg, config):
        assert "alice_symbols" not in block
        assert "alice_symbols" not in public
        calls.append((block["source"], block["block_index"]))
        return {"l1_ok": True, "l2_ok": True, "l2_conditioning": "returned_L1_x1_hat",
                "offline_exact": True, "tag_verified": True, "false_accept": False,
                "runtime_s": 0.0}

    result = v30.run_m3_gate([packet], _fake_blocks(), decoder_runner=decoder)
    assert result["status"] == v30.TERMINAL_PASS
    assert result["record_count"] == 210  # 60 screen + 150 confirmation
    assert result["selected_packet_id"] == "packet-a"
    assert len(calls) == 210


def _run_tiny_m3_pass():
    packet = v30.build_matrix_packet(
        3, {"1M": 3, "1p5M": 3, "2M": 3}, n=16,
        family=v30.FAMILY_BALANCED, allocation_id="m3-registration",
    )
    packet["packet_id"] = "packet-registration"
    return packet, v30.run_m3_gate(
        [packet], _fake_blocks(),
        decoder_runner=lambda block, public, adapter, packet_arg, config: {
            "l1_ok": True, "l2_ok": True, "l2_conditioning": "returned_L1_x1_hat",
            "offline_exact": True, "tag_verified": True, "false_accept": False,
            "runtime_s": 0.0,
        },
    )


def test_m3_confirmation_missing_middle_is_not_a_prefix():
    packet, result = _run_tiny_m3_pass()
    records = list(result["records"])
    del records[60 + 25]  # 1M confirmation block 25; block 26 is not legal next.
    selection = v30._m3_recompute_selection([packet], records)
    problems = v30._m3_record_registration_problems(
        [packet], records, selection, terminal=v30.TERMINAL_PASS,
    )
    assert "m3_confirmation_global_order" in problems
    assert "m3_pass_confirmation_registered_set" in problems


def test_m3_pass_missing_last_confirmation_block_is_rejected():
    packet, result = _run_tiny_m3_pass()
    records = list(result["records"])
    records.pop()  # 2M confirmation block 69: legal prefix, but not PASS.
    selection = v30._m3_recompute_selection([packet], records)
    problems = v30._m3_record_registration_problems(
        [packet], records, selection, terminal=v30.TERMINAL_PASS,
    )
    assert "m3_pass_confirmation_registered_set" in problems
    assert "m3_confirmation_early_stop_terminal" in problems


def test_m3_confirmation_legal_early_prefix_has_recomputed_proof():
    packet = v30.build_matrix_packet(
        3, {"1M": 3, "1p5M": 3, "2M": 3}, n=16,
        family=v30.FAMILY_BALANCED, allocation_id="m3-early-prefix",
    )
    packet["packet_id"] = "packet-early-prefix"

    def decoder(block, public, adapter, packet_arg, config):
        confirmation = int(block["block_index"]) >= 20
        return {
            "l1_ok": True, "l2_ok": True, "l2_conditioning": "returned_L1_x1_hat",
            "offline_exact": not confirmation, "tag_verified": not confirmation,
            "false_accept": confirmation, "runtime_s": 0.0,
        }

    result = v30.run_m3_gate([packet], _fake_blocks(), decoder_runner=decoder)
    assert result["status"] == v30.TERMINAL_FINITE_FAIL
    assert len(result["records"]) == 61
    assert result["early_stop_proof"]["reason"] == "impossible_threshold"
    selection = v30._m3_recompute_selection([packet], result["records"])
    problems = v30._m3_record_registration_problems(
        [packet], result["records"], selection,
        terminal=result["status"], resource_limit_seconds=1.0,
    )
    assert not any(problem.startswith("m3_confirmation_") for problem in problems)


def test_m3_l1_failure_forces_l2_not_run_and_matrix_local_removal():
    packet = v30.build_matrix_packet(
        3, {"1M": 3, "1p5M": 3, "2M": 3}, n=16,
        family=v30.FAMILY_BALANCED, allocation_id="a",
    )
    packet["packet_id"] = "packet-fail"
    result = v30.run_m3_gate(
        [packet], _fake_blocks(),
        decoder_runner=lambda block, public, adapter, packet_arg, config: {
            "l1_ok": False, "l1_status": "failed", "l2_status": "not_run",
            "offline_exact": False, "tag_verified": False, "false_accept": False,
            "runtime_s": 0.0,
        },
    )
    assert result["status"] == v30.TERMINAL_FINITE_FAIL
    assert result["screen_outcomes"][0]["status"] == "matrix_local_fail"
    assert result["records"][0]["l2_status"] == "not_run"
    assert result["records"][0]["l2_not_run_due_l1"] is True
    assert result["confirmation"] is None


def test_m3_false_accept_is_scientific_failure_before_resource():
    packet = v30.build_matrix_packet(
        3, {"1M": 3, "1p5M": 3, "2M": 3}, n=16,
        family=v30.FAMILY_BALANCED, allocation_id="a",
    )
    packet["packet_id"] = "packet-fa"
    result = v30.run_m3_gate(
        [packet], _fake_blocks(), resource_limit_seconds=1.0,
        decoder_runner=lambda block, public, adapter, packet_arg, config: {
            "l1_ok": True, "l2_ok": True, "offline_exact": False,
            "tag_verified": True, "false_accept": True, "runtime_s": 0.0,
        },
    )
    assert result["status"] == v30.TERMINAL_FINITE_FAIL
    assert result["records"][0]["false_accept"] is True


def test_readonly_gate_evidence_and_verifier_do_not_call_science():
    # A failed DE screen is enough to exercise the complete additive E01-E09
    # writer/verifier path without constructing production matrices or reading
    # validation parquet.
    root = Path("workspace/v30r_tests") / f"evidence_{uuid.uuid4().hex}"
    calls = {"de": 0, "decoder": 0}

    def de_runner(item):
        calls["de"] += 1
        return {"converged": False, "final_entropy_bits": 1.0, "runtime_s": 0.0}

    def decoder_runner(*args):
        calls["decoder"] += 1
        raise AssertionError("decoder must not run after DE allocation failure")

    run = v30.run_v30r_gate(root, de_runner=de_runner, decoder_runner=decoder_runner)
    assert run["status"] == v30.TERMINAL_DE_FAIL
    assert calls["de"] == 72
    assert calls["decoder"] == 0
    for filename in (
        "RUN_MANIFEST.json", "projective_column_audit.json", "de_allocation_screen.json",
        "de_allocation_confirmation.json", "matrix_audits.json", "frame_selection.json",
        "block_manifest.json", "per_block_results.jsonl", "source_summary.json",
        "gate.json", "readonly_verify.json",
    ):
        assert (root / filename).exists()
    assert run["readonly_verify"]["ok"] is True
    assert run["readonly_verify"]["no_de_rerun"] is True
    assert run["readonly_verify"]["no_decoder_rerun"] is True


def test_verifier_rejects_m1_registry_call_tampering_and_no_science(monkeypatch):
    root = Path("workspace/v30r_tests") / f"m1_tamper_{uuid.uuid4().hex}"
    run = v30.run_v30r_gate(
        root,
        de_runner=lambda item: {"converged": False, "final_entropy_bits": 1.0, "runtime_s": 0.0},
        decoder_runner=lambda *args: (_ for _ in ()).throw(AssertionError("decoder rerun")),
    )
    assert run["status"] == v30.TERMINAL_DE_FAIL
    monkeypatch.setattr(v30, "_invoke_de_runner", lambda *args: (_ for _ in ()).throw(AssertionError("DE rerun")))
    monkeypatch.setattr(v30, "_invoke_decoder", lambda *args: (_ for _ in ()).throw(AssertionError("decoder rerun")))
    path = root / "de_allocation_screen.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutations = (("seed", 39999), ("rate", 0.123), ("n_samples", 401), ("max_iter", 101))
    for field, value in mutations:
        original = payload["calls"][0][field]
        payload["calls"][0][field] = value
        path.write_text(json.dumps(payload), encoding="utf-8")
        report = v30.verify_v30r(root)
        assert report["ok"] is False
        assert report["no_de_rerun"] is True and report["no_decoder_rerun"] is True
        payload["calls"][0][field] = original
    payload["selected_allocations"] = ["m1_9"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    report = v30.verify_v30r(root)
    assert report["ok"] is False


def test_verifier_rejects_matrix_payload_rank_projective_and_t6_tampering(_tiny_gate_evidence, monkeypatch):
    root = _tiny_gate_evidence
    _patch_tiny_verifier(monkeypatch)
    monkeypatch.setattr(v30, "_invoke_de_runner", lambda *args: (_ for _ in ()).throw(AssertionError("DE rerun")))
    monkeypatch.setattr(v30, "_invoke_decoder", lambda *args: (_ for _ in ()).throw(AssertionError("decoder rerun")))

    payload_path = root / "matrix_payloads.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    original_value = payload["packets"][0]["matrices"]["L1"][0][0]
    payload["packets"][0]["matrices"]["L1"][0][0] = (int(original_value) + 1) % v30.Q
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    assert v30.verify_v30r(root)["ok"] is False
    payload["packets"][0]["matrices"]["L1"][0][0] = original_value
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    audit_path = root / "matrix_audits.json"
    audits = json.loads(audit_path.read_text(encoding="utf-8"))
    audit = audits["packets"][0]["audits"]["L1"]
    for field in ("rank", "tanner6_degenerate_total"):
        original = audit[field]
        audit[field] = int(original) + 1
        audit_path.write_text(json.dumps(audits), encoding="utf-8")
        assert v30.verify_v30r(root)["ok"] is False
        audit[field] = original

    original_duplicate = audit["projective"]["duplicate_projective_classes"]
    audit["projective"]["duplicate_projective_classes"] = int(original_duplicate) + 1
    audit_path.write_text(json.dumps(audits), encoding="utf-8")
    assert v30.verify_v30r(root)["ok"] is False
    audit["projective"]["duplicate_projective_classes"] = original_duplicate
    audit_path.write_text(json.dumps(audits), encoding="utf-8")


def test_verifier_accepts_nested_l2_source_audits(_tiny_gate_evidence, monkeypatch):
    root = _tiny_gate_evidence
    _patch_tiny_verifier(monkeypatch)
    report = v30.verify_v30r(root)
    # This fixture intentionally has one packet for two confirmed
    # allocations, so packet completeness remains an unrelated expected
    # finding.  The nested L2 audit must nevertheless be traversed as three
    # source audits rather than as one mapping-shaped audit.
    assert "confirmed_packet_completeness" in report["problems"]
    assert not any(":L2" in problem and problem.split(":", 1)[0] in {
        "tanner8_rule", "invalid_column", "projective_key", "duplicate_recompute",
        "affected_recompute", "tanner6_new_total", "tanner6_degenerate_total",
        "tanner6_degenerate_max", "ratio_replay",
    } for problem in report["problems"])


def test_verifier_rejects_m3_record_selection_and_no_fallback_tampering(_tiny_gate_evidence, monkeypatch):
    root = _tiny_gate_evidence
    _patch_tiny_verifier(monkeypatch)
    monkeypatch.setattr(v30, "_invoke_de_runner", lambda *args: (_ for _ in ()).throw(AssertionError("DE rerun")))
    monkeypatch.setattr(v30, "_invoke_decoder", lambda *args: (_ for _ in ()).throw(AssertionError("decoder rerun")))

    records_path = root / "per_block_results.jsonl"
    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    tamper_fields = (("source_id", "wrong-source"), ("frame_ids", [999, 1000, 1001, 1002]),
                     ("block_index", 99), ("tag_verified", False),
                     ("offline_exact", False), ("false_accept", True))
    for field, value in tamper_fields:
        original = records[0][field]
        records[0][field] = value
        records_path.write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")
        report = v30.verify_v30r(root)
        assert report["ok"] is False
        records[0][field] = original
    records_path.write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")

    gate_path = root / "gate.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    for field, value in (("m3_top_ranked_packet_ids", []), ("m3_selected_packet_id", None),
                         ("no_fallback_confirmation", False)):
        original = gate[field]
        gate[field] = value
        gate_path.write_text(json.dumps(gate), encoding="utf-8")
        assert v30.verify_v30r(root)["ok"] is False
        gate[field] = original
    gate_path.write_text(json.dumps(gate), encoding="utf-8")


def test_verifier_rejects_each_terminal_status_tamper(_tiny_gate_evidence, monkeypatch):
    """Every persisted terminal must agree with independent evidence."""
    _patch_tiny_verifier(monkeypatch)
    monkeypatch.setattr(v30, "_invoke_de_runner", lambda *args: (_ for _ in ()).throw(AssertionError("DE rerun")))
    monkeypatch.setattr(v30, "_invoke_decoder", lambda *args: (_ for _ in ()).throw(AssertionError("decoder rerun")))
    roots: list[tuple[Path, str]] = [(_tiny_gate_evidence, v30.TERMINAL_PASS)]

    de_root = Path("workspace/v30r_tests") / f"terminal_de_{uuid.uuid4().hex}"
    v30.run_v30r_gate(
        de_root,
        de_runner=lambda item: {"converged": False, "final_entropy_bits": 1.0, "runtime_s": 0.0},
        decoder_runner=lambda *args: None,
    )
    roots.append((de_root, v30.TERMINAL_DE_FAIL))

    resource_root = Path("workspace/v30r_tests") / f"terminal_resource_{uuid.uuid4().hex}"
    v30.run_v30r_gate(
        resource_root,
        de_runner=lambda item: {"converged": True, "final_entropy_bits": 0.0, "runtime_s": 1.0},
        decoder_runner=lambda *args: None, resource_limit_seconds=0.5,
    )
    roots.append((resource_root, v30.TERMINAL_RESOURCE))

    implementation_root = Path("workspace/v30r_tests") / f"terminal_impl_{uuid.uuid4().hex}"
    v30.run_v30r_gate(
        implementation_root,
        de_runner=lambda item: (_ for _ in ()).throw(RuntimeError("fake implementation stop")),
        decoder_runner=lambda *args: None,
    )
    roots.append((implementation_root, v30.TERMINAL_IMPL))

    finite_root = Path("workspace/v30r_tests") / f"terminal_finite_{uuid.uuid4().hex}"
    with monkeypatch.context() as patch:
        patch.setattr(v30, "build_confirmed_packets", lambda *args: {
            "schema": "nbldpc_v30r_matrix_construction_v1", "packets": [],
            "rejected": [], "packet_cap": 4, "packet_cap_ok": True,
        })
        v30.run_v30r_gate(
            finite_root,
            de_runner=lambda item: {"converged": True, "final_entropy_bits": 0.0, "runtime_s": 0.0},
            decoder_runner=lambda *args: None,
        )
    roots.append((finite_root, v30.TERMINAL_FINITE_FAIL))

    all_statuses = [v30.TERMINAL_DE_FAIL, v30.TERMINAL_RESOURCE,
                    v30.TERMINAL_IMPL, v30.TERMINAL_FINITE_FAIL, v30.TERMINAL_PASS]
    for root, actual in roots:
        path = root / "gate.json"
        gate = json.loads(path.read_text(encoding="utf-8"))
        target = next(status for status in all_statuses if status != actual)
        original = gate["status"]
        gate["status"] = target
        path.write_text(json.dumps(gate), encoding="utf-8")
        assert v30.verify_v30r(root)["ok"] is False
        gate["status"] = original
        path.write_text(json.dumps(gate), encoding="utf-8")


def test_global_screen_terminal_stops_confirmation_and_preserves_meter():
    allocations = v30.build_allocation_plan()
    screen = v30.run_m1_screen(
        allocations,
        de_runner=lambda item: (_ for _ in ()).throw(RuntimeError("global implementation stop")),
    )
    assert screen["terminal"] == v30.TERMINAL_IMPL
    assert screen["n_calls"] == 1
    confirmation = v30.run_m1_confirmation(
        screen, allocations,
        de_runner=lambda item: (_ for _ in ()).throw(AssertionError("must not run")),
        initial_resource_meter_seconds=screen["resource_meter_seconds"],
    )
    assert confirmation["terminal"] == v30.TERMINAL_IMPL
    assert confirmation["n_calls"] == 0
    assert confirmation["resource_meter_seconds"] >= screen["resource_meter_seconds"]


def test_confirmation_uses_screen_meter_without_reset():
    allocations = v30.build_allocation_plan()
    screen = {"terminal": None, "selected_allocations": ["m1_9"]}
    confirmation = v30.run_m1_confirmation(
        screen, allocations,
        de_runner=lambda item: {"converged": True, "final_entropy_bits": 0.0, "runtime_s": 0.5},
        initial_resource_meter_seconds=0.75, resource_limit_seconds=1.0,
    )
    assert confirmation["terminal"] == v30.TERMINAL_RESOURCE
    assert confirmation["n_calls"] == 1
    assert confirmation["resource_meter_seconds"] == pytest.approx(1.25)


def test_gate_m1_meter_uses_cumulative_confirmation_or_screen_terminal(monkeypatch):
    """The persisted gate meter must not add screen twice."""
    monkeypatch.setattr(v30, "build_confirmed_packets", lambda *args: {"packets": [], "rejected": []})
    monkeypatch.setattr(v30, "verify_v30r", lambda root: {
        "ok": True, "no_de_rerun": True, "no_decoder_rerun": True,
    })
    screen = {
        "terminal": None, "resource_meter_seconds": 1.25, "n_calls": 72,
    }
    confirmation = {
        "terminal": v30.TERMINAL_DE_FAIL, "resource_meter_seconds": 3.75, "n_calls": 2,
    }
    monkeypatch.setattr(v30, "run_m1_screen", lambda *args, **kwargs: screen)
    monkeypatch.setattr(v30, "run_m1_confirmation", lambda *args, **kwargs: confirmation)
    root = Path("workspace/v30r_tests") / f"meter_cumulative_{uuid.uuid4().hex}"
    result = v30.run_v30r_gate(root)
    assert result["gate"]["m1_de_resource_meter_seconds"] == pytest.approx(3.75)

    screen_terminal = {
        "terminal": v30.TERMINAL_IMPL, "resource_meter_seconds": 0.75, "n_calls": 1,
    }
    confirmation_not_run = {
        "terminal": v30.TERMINAL_IMPL, "resource_meter_seconds": 0.75, "n_calls": 0,
    }
    monkeypatch.setattr(v30, "run_m1_screen", lambda *args, **kwargs: screen_terminal)
    monkeypatch.setattr(v30, "run_m1_confirmation", lambda *args, **kwargs: confirmation_not_run)
    root_terminal = Path("workspace/v30r_tests") / f"meter_screen_terminal_{uuid.uuid4().hex}"
    result_terminal = v30.run_v30r_gate(root_terminal)
    assert result_terminal["gate"]["m1_de_resource_meter_seconds"] == pytest.approx(0.75)


def test_default_production_path_loads_v26_adapters_once(monkeypatch):
    loaded = {"count": 0}
    monkeypatch.setattr(v30, "load_v26_adapters_once", lambda: loaded.update(count=loaded["count"] + 1) or {label: object() for label in v30.SOURCE_ORDER})
    monkeypatch.setattr(v30, "_invoke_de_runner", lambda runner, item, adapter: {"converged": False, "final_entropy_bits": 1.0, "runtime_s": 0.0})
    root = Path("workspace/v30r_tests") / f"adapter_once_{uuid.uuid4().hex}"
    result = v30.run_v30r_gate(root, de_runner=None, decoder_runner=lambda *args: None)
    assert result["status"] == v30.TERMINAL_DE_FAIL
    assert loaded["count"] == 1


def test_strict_validation_loader_rejects_wrong_source_split(monkeypatch):
    from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v29 as v29
    bad = [{"source": "1M", "source_id": "wrong", "delay_used_ps": 0,
            "block_index": 0, "frame_ids": [1200, 1201, 1202, 1203],
            "pair_idx_ranges": [[0, 255]] * 4,
            "alice_symbols": [0] * 1024, "bob_symbols": [0] * 1024}]
    monkeypatch.setattr(v29, "load_blocks", lambda *args, **kwargs: bad)
    with pytest.raises(ValueError, match="exactly 300 blocks"):
        v30.load_validation_blocks()


def test_finite_record_recomputes_raw_xhat_truth_syndrome_and_tag():
    packet = v30.build_matrix_packet(3, {"1M": 3, "1p5M": 3, "2M": 3}, n=16,
                                     family=v30.FAMILY_BALANCED, allocation_id="raw")
    packet["packet_id"] = "raw-packet"
    blocks = []
    for source in v30.SOURCE_ORDER:
        for index in range(100):
            blocks.append({"source": source, "source_id": v30.SOURCE_IDS[source],
                           "delay_used_ps": v30.SOURCE_DELAY_PS[source], "block_index": index,
                           "frame_ids": [], "alice_symbols": [0] * 16, "bob_symbols": [0] * 16})
    result = v30.run_m3_gate(
        [packet], blocks,
        decoder_runner=lambda block, public, adapter, packet_arg, config: {
            "L1": {"status": "success", "iterations": 4},
            "L2": {"status": "success", "iterations": 5},
            "x1_hat": [0] * 16, "x2_hat": [0] * 16, "decoder_calls": 2,
            # Deliberately contradictory predicates: they must be ignored when
            # truth is available and raw estimates are present.
            "offline_exact": False, "tag_verified": False, "false_accept": True,
            "runtime_s": 0.0,
        },
    )
    assert result["status"] == v30.TERMINAL_PASS
    row = result["records"][0]
    assert row["offline_exact"] is True and row["tag_verified"] is True and row["false_accept"] is False
    assert row["l1_syndrome_ok"] is True and row["l2_syndrome_ok"] is True
    assert row["l1_symbol_errors"] == 0 and row["l2_symbol_errors"] == 0
    assert row["l1_iterations"] == 4 and row["l2_iterations"] == 5


def test_readonly_verifier_detects_m0_tamper_without_science_rerun(monkeypatch):
    root = Path("workspace/v30r_tests") / f"tamper_{uuid.uuid4().hex}"
    run = v30.run_v30r_gate(
        root,
        de_runner=lambda item: {"converged": False, "final_entropy_bits": 1.0, "runtime_s": 0.0},
        decoder_runner=lambda *args: (_ for _ in ()).throw(AssertionError("decoder rerun")),
    )
    bundle = json.loads((root / "projective_column_audit.json").read_text(encoding="utf-8"))
    bundle["baseline"]["expected_l1_counts"]["proportional_pairs"] += 1
    (root / "projective_column_audit.json").write_text(json.dumps(bundle), encoding="utf-8")
    monkeypatch.setattr(v30, "_invoke_de_runner", lambda *args: (_ for _ in ()).throw(AssertionError("DE rerun")))
    report = v30.verify_v30r(root)
    assert report["ok"] is False
    assert report["no_de_rerun"] is True and report["no_decoder_rerun"] is True


def test_cli_rejects_existing_output_root():
    from comparison_bench.src.comparison_bench.cli.run_nonbinary_v30_gate import main
    root = Path("workspace/v30r_tests") / f"cli_existing_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    with pytest.raises(SystemExit):
        main([str(root)])
