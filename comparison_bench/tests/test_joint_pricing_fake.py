"""Fake-only tests for joint-code budget-fit pricing arithmetic (packet P-3).

Hand-computable constants only; zero scientific/real-data contact -- this
file reads no CQ JSON, no S0_RESULT.json, no .ttbin, nothing. Temporary
directories live under fresh additive workspace/jp__pytest_<uuid8> roots.
"""

from __future__ import annotations

import json
import math
import uuid
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.cli import joint_pricing as jp


def _fresh_root() -> Path:
    root = Path(f"workspace/jp__pytest_{uuid.uuid4().hex[:8]}")
    root.mkdir(parents=False, exist_ok=False)
    return root


def test_joint_bits_nominal_ceil():
    # ceil(1024 * 1.3 * 0.5) = ceil(665.6) = 666.
    assert jp.joint_bits(0.5, 1.3) == 666


def test_joint_bits_backoff_inside_ceil():
    # ceil(1024 * 1.3 * 1.2 * 0.5) = ceil(798.72) = 799.
    assert jp.joint_bits(0.5, 1.3 * 1.20) == 799


def test_joint_bits_boundary():
    # ceil(1024 * 1.3 * 1.0) = ceil(1331.2) = 1332.
    assert jp.joint_bits(1.0, 1.3) == 1332


def test_total_identity_on_real_function_hand_inputs():
    # C-1 on the module's real total function: TOTAL == ceil(f*N*H),
    # LEAK == TOTAL - 64, and TOTAL <= 1104 iff LEAK <= 1040.
    # Hand case f=1.3, H=0.5 -> ceil(665.6)=666, LEAK 602, margins 438.
    total = jp.joint_bits(0.5, 1.3)
    assert total == 666
    assert total - 64 == 602
    assert jp.within_single(jp.totals_single(total))
    assert (1104 - jp.totals_single(total)) == (1040 - (total - 64)) == 438


def test_real_function_does_not_double_count():
    # The budget-compared quantity must equal the bare ceil: no second tag.
    total = jp.joint_bits(0.5, 1.3)
    assert jp.totals_single(total) == 666  # not 666 + 64 = 730
    assert jp.excess_single(total) == 666 - 1104 == -438
    assert jp.totals_recorded(total) == (666 - 64) + 1024 == 1626
    assert jp.excess_recorded(total) == jp.excess_single(total)


def test_budget_gate_both_sides_both_comparisons():
    # Comparator-only gate test: necessary but explicitly NOT sufficient --
    # it exercises within_budget/totals without anchoring the total
    # construction itself (STAGE0 §16.3 procedural rule); the C-1/C-2 trap
    # cases above carry the construction check.
    # CORRECTED 2026-09-28, superseding the old fixtures below: the joint
    # ceil IS the tag-inclusive total, so asserting totals_single(1040) ==
    # 1104 and excess == m - 1040 encoded the double count (a total compared
    # against the leak budget 1040). The corrected gate compares the total
    # against 1104 and the excess is m - 1104 on both comparisons.
    # Hand TOTAL = 1104 fits on both comparisons; 1105 is over on both.
    assert jp.totals_single(1104) == 1104
    assert jp.within_single(jp.totals_single(1104))
    assert jp.totals_recorded(1104) == 2064
    assert jp.within_recorded(jp.totals_recorded(1104))
    assert jp.totals_single(1105) == 1105
    assert not jp.within_single(jp.totals_single(1105))
    assert jp.totals_recorded(1105) == 2065
    assert not jp.within_recorded(jp.totals_recorded(1105))


def test_excess_identity_hand_m():
    # CORRECTED 2026-09-28: the old identity (excess == m - 1040) compared a
    # tag-inclusive total against the leak budget and is superseded. The
    # consistent excess is TOTAL - 1104, identical on both comparisons (so the
    # verdict stays tag-accounting-invariant). Comparator-only identity tests
    # are necessary but explicitly not sufficient: the C-1/C-2 tests above
    # anchor the total construction itself.
    for m in (666, 799, 1040, 1041, 1100, 1319, 1332):
        assert jp.excess_single(m) == jp.excess_recorded(m) == m - 1104


def test_scope_selection_uses_own_h():
    assert jp.select_scope_h(0.8, 0.7, "A") == 0.8
    assert jp.select_scope_h(0.8, 0.7, "B") == 0.7
    with pytest.raises(jp.Refusal):
        jp.select_scope_h(0.8, 0.7, "C")
    assert jp.joint_bits(jp.select_scope_h(0.8, 0.7, "A"), 1.3) == math.ceil(1024 * 1.3 * 0.8) == 1065
    assert jp.joint_bits(jp.select_scope_h(0.8, 0.7, "B"), 1.3) == math.ceil(1024 * 1.3 * 0.7) == 932


def test_fidelity_comparator_exact_match_passes():
    assert jp.fidelity_ab_ok(0.8256785297622027, 0.8256785297622027)


def test_fidelity_comparator_planted_mismatch_flagged():
    assert not jp.fidelity_ab_ok(0.8256785297622027, 0.8256785297622027 + 1e-12)


def test_chain_comparator_both_sides():
    ok, _ = jp.chain_ok(0.024911563989704053, 0.8007669657724986, 0.8256785297622027)
    assert ok
    ok_out, _ = jp.chain_ok(0.02, 0.78, 0.8 + 2e-9)
    assert not ok_out


def test_feasibility_arms():
    ok, _ = jp.joint_feasible(666)
    assert ok
    ok, _ = jp.joint_feasible(10240)
    assert ok
    ok, reason = jp.joint_feasible(0)
    assert not ok and reason == "M <= 0"
    ok, reason = jp.joint_feasible(10241)
    assert not ok and reason == "M > 10240"


def test_path_gate_refuses_ttbin():
    with pytest.raises(jp.Refusal):
        jp.validate_input_path("workspace/cq_15d6f160/frames.ttbin")


def test_path_gate_refuses_npz():
    with pytest.raises(jp.Refusal):
        jp.validate_input_path("docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz")


def test_path_gate_refuses_parquet():
    case = "comparison_bench/outputs_comparison/ir_frame_results.parquet"
    with pytest.raises(jp.Refusal):
        jp.validate_input_path(case)


def test_path_gate_refuses_nonfrozen_json():
    with pytest.raises(jp.Refusal):
        jp.validate_input_path("workspace/cq_15d6f160/CQ-20c.json")


def test_path_gate_accepts_frozen_six():
    for path, label in jp.FROZEN_INPUTS.items():
        assert jp.validate_input_path(path) == label


def test_root_gate_accepts_fresh_jp_root():
    assert jp.validate_root_string("workspace/jp_ab12cd34") == "workspace/jp_ab12cd34"


def test_root_gate_refuses_protected_and_odd_roots():
    with pytest.raises(jp.Refusal):
        jp.validate_root_string("results/jp_ab12cd34")
    with pytest.raises(jp.Refusal):
        jp.validate_root_string("comparison_bench/outputs_comparison/jp_ab12cd34")
    with pytest.raises(jp.Refusal):
        jp.validate_root_string("workspace/jp__pytest_ab12cd34")


def test_prepare_root_refuses_evidence_collision():
    root = _fresh_root()
    (root / "JP_RESULT.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
    with pytest.raises(jp.Refusal):
        jp.prepare_root(root, root / "JOINT_PRICING_LOG.md")


def test_decide_rule_three_states_plus_thin_margin():
    # Intents preserved; quantities corrected 2026-09-28 to tag-inclusive
    # totals (the old hand values were pre-tag M's fed through M + 64).
    # PASS with thin nominal margin (1104 - 1064 = 40 < 64).
    w, c, thin = jp.decide_primary(1064, 1064)
    assert (w, c, thin) == ("PASS", "section 5.1", True)
    # PASS with comfortable nominal margin (1104 - 964 = 140).
    w, c, thin = jp.decide_primary(964, 964)
    assert (w, c, thin) == ("PASS", "section 5.1", False)
    # KILL: nominal total over budget.
    w, c, thin = jp.decide_primary(1105, 2000)
    assert (w, c) == ("KILL", "section 5.2")
    # KILL: nominal allocation infeasible.
    w, c, thin = jp.decide_primary(0, 0)
    assert w == "KILL"
    # MARGINAL: nominal fits, backoff column breaches.
    w, c, thin = jp.decide_primary(1064, 1105)
    assert (w, c) == ("MARGINAL", "section 5.3")


def test_c2_trap_real_total_bare_ceil_passes_plus64_rejected():
    # STAGE0 §16.3 item-2 / C-2 trap on the module's REAL total function.
    # Hand case f=1.3, H=0.5: bare ceil = ceil(665.6) = 666 passes the C-2
    # identity Q - B == ceil(f*N*H) - B; the trapped quantity ceil + TAG =
    # 730 FAILS it. Production anchors on the real excess path (correct form
    # TOTAL - 1104): nominal 1100 fits by 4, backoff 1319 exceeds by 215.
    bare = jp.joint_bits(0.5, 1.3)
    assert bare == 666
    assert (jp.totals_single(bare) - jp.BUDGET_SINGLE) == (666 - 1104) == -438
    trapped = bare + jp.TAG_SINGLE
    assert trapped == 730
    assert (trapped - jp.BUDGET_SINGLE) != (bare - jp.BUDGET_SINGLE)
    assert jp.excess_single(trapped) == -374
    assert jp.excess_single(bare) == -438
    assert jp.excess_single(1100) == -4
    assert jp.excess_single(1319) == 215
