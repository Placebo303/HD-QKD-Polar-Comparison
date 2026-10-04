"""Fake-only tests for the proxy-recalibration sampler (packet P-3).

Hand-computable constants only; zero scientific/real-data contact -- this
file reads no CQ JSON, no baseline rows, no graph, no archive, nothing.
Temporary directories live under fresh additive
workspace/proxy_recal__pytest_<uuid8> roots.

Toy 2-bit Gray case, hand derivation (uniform source over {0,1,2,3},
slip masses m_0 = 0.75, m_+1 = 0.0, m_-1 = 0.25, clamp edges):
2-bit Gray labels are Gray(0)=00, Gray(1)=01, Gray(2)=11, Gray(3)=10.
Only -1 slips occur (probability 0.25 each): a=0 clamps to b=0 (no error);
a=1 -> b=0 flips plane 0 (01 vs 00); a=2 -> b=1 flips plane 1 (11 vs 01);
a=3 -> b=2 flips plane 0 (10 vs 11). Hence emergent p_0 = (0.25 + 0.25)/4
= 0.125 and p_1 = 0.25/4 = 0.0625, both exact binary fractions, and
ser = 3*0.25/4 = 0.1875.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.cli import proxy_recal_sampler as pr


def _fresh_root() -> Path:
    root = Path(f"workspace/proxy_recal__pytest_{uuid.uuid4().hex[:8]}")
    root.mkdir(parents=False, exist_ok=False)
    return root


def _toy_gray(a: int) -> int:
    return int(a) ^ (int(a) >> 1)


def test_pytest_root_is_fresh_additive():
    root = _fresh_root()
    assert root.is_dir()
    assert str(root).startswith("workspace/proxy_recal__pytest_")


def test_toy_gray_plane_rates_hand_exact():
    rates, ser = pr.analytic_plane_rates(4, 2, _toy_gray, 0.75, 0.0, 0.25)
    assert rates[0] == 0.125
    assert rates[1] == 0.0625
    assert ser == 0.1875


def test_toy_matches_frozen_gray_mapping():
    # The script's frozen survey mapping reproduces the toy by hand.
    from comparison_bench.src.comparison_bench.formal_ir import (
        nonbinary_v25_gate as v25,
    )
    rates, ser = pr.analytic_plane_rates(
        4, 2, lambda a: int(v25.gray_label(a)), 0.75, 0.0, 0.25)
    assert rates == [0.125, 0.0625] and ser == 0.1875


def test_validation_gate_passes_toy():
    gate = pr.validation_gate([0.125, 0.0625], [0.125, 0.0625],
                              1_000_000, 0.1875, 0.1875)
    assert gate["verdict"] == "PASS"
    assert all(m["ok"] for m in gate["margins"])


def test_validation_gate_refuses_shifted_vector():
    # A planted 10% shift on plane 0 (0.0125 absolute) exceeds the
    # max(5% p, 5 SE) tolerance at N = 10^6 (tol = 0.00625).
    with pytest.raises(pr.Refusal):
        pr.validation_gate([0.1375, 0.0625], [0.125, 0.0625],
                           1_000_000, 0.1875, 0.1875)


def test_validation_gate_refuses_ser_shift():
    with pytest.raises(pr.Refusal):
        pr.validation_gate([0.125, 0.0625], [0.125, 0.0625],
                           1_000_000, 0.1925, 0.1875)


def test_overlap_predicate_pass_case():
    word, clause = pr.decide_word(15, 10, 0.030, 0.080, 0.025875, 0.066776)
    assert (word, clause) == ("PASS", "section 5.1")


def test_overlap_predicate_marginal_case():
    word, clause = pr.decide_word(60, 10, 0.200, 0.300, 0.025875, 0.066776)
    assert (word, clause) == ("MARGINAL", "section 5.2")


def test_overlap_predicate_kill_case():
    word, clause = pr.decide_word(10, 10, 0.020, 0.070, 0.025875, 0.066776)
    assert (word, clause) == ("KILL", "section 5.3")
    word2, _ = pr.decide_word(3, 10, 0.001, 0.010, 0.025875, 0.066776)
    assert word2 == "KILL"


def test_wilson_endpoints_hand_checked():
    lo0, hi0 = pr.wilson(0, 240)
    assert lo0 == 0.0
    assert 0.0 < hi0 < 0.05
    lo1, hi1 = pr.wilson(240, 240)
    assert hi1 == 1.0
    assert 0.95 < lo1 < 1.0
    lo, hi = pr.wilson(10, 240)
    assert 0.0 < lo < 10 / 240 < hi < 1.0


def test_paired_table_hand_worked():
    old = {1: False, 2: False, 3: True, 4: True}
    new = {1: False, 2: True, 3: False, 4: True}
    t = pr.paired_table(old, new)
    assert t["matched_frame_count"] == 4
    assert t["transitions"] == {"old_success_new_success": 1,
                                "old_success_new_failure": 1,
                                "old_failure_new_success": 1,
                                "old_failure_new_failure": 1}


def test_path_gate_refuses_npz():
    with pytest.raises(pr.Refusal):
        pr.validate_input_path("docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz")


def test_path_gate_refuses_ttbin():
    with pytest.raises(pr.Refusal):
        pr.validate_input_path("workspace/cq_15d6f160/frames.ttbin")


def test_path_gate_refuses_parquet():
    with pytest.raises(pr.Refusal):
        pr.validate_input_path("comparison_bench/outputs_comparison/pairs.parquet")


def test_path_gate_refuses_outside_nine():
    with pytest.raises(pr.Refusal):
        pr.validate_input_path("workspace/m3a_nested_200p8_20260926/arm2.json")


def test_path_gate_accepts_frozen_nine_strings():
    for path, role in pr.FROZEN_INPUTS.items():
        assert pr.validate_input_path(path) == role


def test_root_gate_accepts_fresh_rejects_protected():
    assert pr.validate_root_string("workspace/proxy_recal_1234abcd") == \
        "workspace/proxy_recal_1234abcd"
    with pytest.raises(pr.Refusal):
        pr.validate_root_string("results/ir_benchmark_results.csv")
    with pytest.raises(pr.Refusal):
        pr.validate_root_string("workspace/m3b_nested_paired_20260926/P1S1-R1_73d2f40a")


def _fake_loader_dict(with_pins: bool) -> dict:
    # Loader-shaped dict: frozen (n, m) + synthetic triples only; the pin
    # fields mirror the I-7 artifact values (four_cycles 0, rank 208,
    # min_girth 6) without reading any input file.
    triples = [(i % 208, (i * 13) % 1024, 1) for i in range(2128)]
    d = {"n": 1024, "m": 208, "triples": triples, "status": "ok"}
    if with_pins:
        d.update({"four_cycles": 0, "rank": 208, "min_girth": 6})
    return d


def test_f6_gate_refuses_pinless_loader_dict():
    # Regression pin for the attempt-1 failure mode: a loader dict shaped
    # like the pre-repair one (n/m/triples/status only) must be refused by
    # the frozen F6 gate before any decode.
    from comparison_bench.src.comparison_bench.cli import p1_stage1_runner as p1

    def loader(instance: int, trials: int) -> dict:
        return _fake_loader_dict(False)

    with pytest.raises(p1.Refusal):
        p1.construct_and_pin("P1S1-R1", loader, lambda dense: 200)


def test_f6_gate_accepts_pinned_loader_dict_and_records_girth():
    # The repaired loader shape (pins passed through by direct index, no
    # defaults) clears the frozen F6 gate; girth is recorded, not gated.
    from comparison_bench.src.comparison_bench.cli import p1_stage1_runner as p1

    def loader(instance: int, trials: int) -> dict:
        return _fake_loader_dict(True)

    pinned = p1.construct_and_pin("P1S1-R1", loader, lambda dense: 200)
    assert pinned["a208_pins"] == {"four_cycles": 0, "rank": 208,
                                   "girth": 6, "twice_identical": True}
    assert pinned["base_rank"] == 200
    assert pinned["base"]["m"] == 200 and pinned["full"]["m"] == 208
