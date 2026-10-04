"""Fake-only tests for Stage 0 per-plane feasibility arithmetic (packet P-3).

Hand-computable constants only; zero scientific/real-data contact -- this
file reads no CQ JSON, no .ttbin, nothing. Temporary directories live under
fresh additive workspace/s0__pytest_<uuid8> roots.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.cli.probes_closed import perplane_stage0 as s0


def _fresh_root() -> Path:
    root = Path(f"workspace/s0__pytest_{uuid.uuid4().hex[:8]}")
    root.mkdir(parents=False, exist_ok=False)
    return root


def test_h2_half_is_exactly_one():
    assert s0.h2_binary(0.5) == 1.0


def test_h2_tenth_matches_hand_constant():
    assert abs(s0.h2_binary(0.1) - 0.4689955936) < 1e-9


def test_h2_endpoints_by_continuity():
    assert s0.h2_binary(0.0) == 0.0
    assert s0.h2_binary(1.0) == 0.0


def test_ceil_boundary_hand_worked():
    # 1024 * 2.0 * 0.25 = 512.0 exactly -> ceil is 512 (no round-up).
    assert s0.parity_bits(0.25, 2.0) == 512
    # Any epsilon above the integer boundary rounds up to 513.
    assert s0.parity_bits(0.25 + 1e-9, 2.0) == 513


def test_infeasible_arm_zero_redundancy():
    # p = 0 -> h2 = 0 -> m = 0 -> infeasible (m_k <= 0 arm).
    m = s0.parity_bits(s0.h2_binary(0.0), 1.3)
    assert m == 0
    ok, reason = s0.plane_feasible(m)
    assert not ok and reason == "m_k <= 0"


def test_infeasible_arm_over_block():
    # p = 0.5, f = 1.3 -> ceil(1024*1.3*1.0) = ceil(1331.2) = 1332 > 1024.
    m = s0.parity_bits(s0.h2_binary(0.5), 1.3)
    assert m == 1332
    ok, reason = s0.plane_feasible(m)
    assert not ok and reason == "m_k > 1024"


def test_budget_gate_both_sides_of_1104():
    # Comparator-only gate test: necessary but explicitly NOT sufficient --
    # within_budget alone cannot catch a mis-constructed total; the C-3
    # frame-shape cases anchor the construction itself (STAGE0 §16.3).
    assert s0.within_budget(1104)
    assert not s0.within_budget(1105)


def test_coherence_comparator_both_sides_of_tolerance():
    ok_inside, gap_inside = s0.coherence_ok(1.0, 1.0 + 0.5e-9)
    assert ok_inside and gap_inside >= -1e-9
    ok_out, gap_out = s0.coherence_ok(1.0, 1.0 + 2e-9)
    assert (not ok_out) and gap_out < -1e-9


def test_path_gate_refuses_ttbin():
    with pytest.raises(s0.Refusal):
        s0.validate_input_path("workspace/cq_15d6f160/frames.ttbin")


def test_path_gate_refuses_npz():
    with pytest.raises(s0.Refusal):
        s0.validate_input_path("docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz")


def test_path_gate_refuses_parquet():
    case = "comparison_bench/outputs_comparison/ir_frame_results.parquet"
    with pytest.raises(s0.Refusal):
        s0.validate_input_path(case)


def test_path_gate_refuses_nonfrozen_json():
    with pytest.raises(s0.Refusal):
        s0.validate_input_path("workspace/cq_15d6f160/CQ-20c.json")


def test_path_gate_accepts_frozen_five():
    for path, label in s0.FROZEN_INPUTS.items():
        assert s0.validate_input_path(path) == label


def test_root_gate_accepts_fresh_s0_root():
    assert s0.validate_root_string("workspace/s0_ab12cd34") == "workspace/s0_ab12cd34"


def test_root_gate_refuses_protected_and_odd_roots():
    with pytest.raises(s0.Refusal):
        s0.validate_root_string("results/s0_ab12cd34")
    with pytest.raises(s0.Refusal):
        s0.validate_root_string("comparison_bench/outputs_comparison/s0_ab12cd34")
    with pytest.raises(s0.Refusal):
        s0.validate_root_string("workspace/s0__pytest_ab12cd34")


def test_prepare_root_refuses_evidence_collision():
    root = _fresh_root()
    (root / "S0_RESULT.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
    with pytest.raises(s0.Refusal):
        s0.prepare_root(root, root / "STAGE0_LOG.md")


def test_decide_rule_three_states():
    feas = [100] * 10
    over = [100] * 9 + [2000]
    # PASS: backoff column feasible and within budget.
    w, c = s0.decide_primary({"f1.3": feas, "f1.3+20%": feas},
                             {"f1.3": 1064, "f1.3+20%": 1064})
    assert (w, c) == ("PASS", "section 5.1")
    # KILL: nominal total over budget.
    w, c = s0.decide_primary({"f1.3": feas, "f1.3+20%": feas},
                             {"f1.3": 1105, "f1.3+20%": 2000})
    assert (w, c) == ("KILL", "section 5.2")
    # KILL: nominal plane infeasible.
    w, c = s0.decide_primary({"f1.3": over, "f1.3+20%": over},
                             {"f1.3": 900, "f1.3+20%": 900})
    assert (w, c) == ("KILL", "section 5.2")
    # MARGINAL: nominal fits, backoff column breaches.
    w, c = s0.decide_primary({"f1.3": feas, "f1.3+20%": feas},
                             {"f1.3": 1000, "f1.3+20%": 1105})
    assert (w, c) == ("MARGINAL", "section 5.3")


def test_frame_shape_adds_shared_tag_exactly_once():
    # C-3 on the real parity_bits: ten pure-parity blocks plus ONE shared tag.
    # Comparator-only tests (e.g. within_budget(1104)) are necessary but
    # explicitly not sufficient: this case anchors the frame-total
    # construction itself -- FRAME_TOTAL - sum(parities) == 64 exactly, so
    # both a tag-omitted total (difference 0) and a tag-doubled total
    # (difference 128) trip it.
    parities = [s0.parity_bits(0.05 * (k + 1), 1.3) for k in range(10)]
    frame_total = sum(parities) + s0.TAG_BITS
    assert frame_total - sum(parities) == 64
    assert (frame_total - sum(parities) == 0) is False
    assert (frame_total - sum(parities) == 128) is False


def test_c3_trap_real_parity_total_path_tag_exactly_once():
    # STAGE0 §16.3 item-2 / C-3 trap on the module's REAL parity/total path:
    # ten pure-parity blocks via parity_bits plus ONE shared TAG_BITS. The
    # honest frame total satisfies FRAME_TOTAL - sum(parities) == 64 exactly
    # (different hand vector than the case above, so the identity is shown
    # general, not fitted to one vector); the tag-omitted misform
    # (difference 0) and the tag-doubled misform (difference 128) both trip.
    parities = [s0.parity_bits(0.10 + 0.03 * k, 1.3) for k in range(10)]
    honest = sum(parities) + s0.TAG_BITS
    assert honest - sum(parities) == s0.TAG_BITS == 64
    omitted = sum(parities)
    assert omitted - sum(parities) == 0
    assert (omitted - sum(parities)) != 64
    doubled = sum(parities) + 2 * s0.TAG_BITS
    assert doubled - sum(parities) == 128
    assert (doubled - sum(parities)) != 64
