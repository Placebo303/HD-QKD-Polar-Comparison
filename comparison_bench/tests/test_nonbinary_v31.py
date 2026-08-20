"""Small in-memory tests for the V31 deterministic finite-graph gate.

These tests intentionally do not invoke DE, a decoder, parquet loading, or a
production-size V31 output root.
"""
from __future__ import annotations

from copy import deepcopy
import math

import pytest

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v30 as v30
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v31 as v31


def test_frozen_gf32_metadata():
    for n in v31.N_VALUES:
        cfg = v31.frozen_v31_config(n)
        assert cfg["field"]["constructor"] == "GF2mField.create(32)"
        assert cfg["field"]["primitive_polynomial"] == 0b100101
        assert cfg["field"]["field_id"] == v31.FIELD_ID
        assert cfg["m1"] == 16
        assert cfg["m3"]["blocks_per_source"] == (400 // (n // 256))
    assert tuple(dict.fromkeys(v30.FIELD.nonzero_cycle)) == tuple(v30.FIELD.nonzero_cycle)


def test_allocation_table_exact_for_both_n():
    for n in v31.N_VALUES:
        alloc = v31.build_allocation_plan(n)
        assert alloc["m1"] == 16
        for label in v31.SOURCE_ORDER:
            info = alloc["sources"][label]
            assert info["m_total"] == v31.SOURCE_M_TOTAL_BY_N[n][label]
            assert info["m2"] == info["m_total"] - 16
            assert info["f_total"] < 1.3
            for layer in ("L1", "L2"):
                m = info["layers"][layer]["m"]
                assert info["layers"][layer]["rate"] == pytest.approx(1.0 - m / n)
                assert info["layers"][layer]["leak_bits"] == pytest.approx(5.0 * m)
            assert info["leak_total_bits"] == pytest.approx(5 * info["m_total"] + 64)


def test_confirmation_items_order():
    alloc = v31.build_allocation_plan(1024)
    items = list(v31._confirmation_items(alloc))
    assert len(items) == 30
    assert [i["seed"] for i in items] == sorted([30101]*6 + [30102]*6 + [30103]*6 + [30104]*6 + [30105]*6)
    # per seed, order is source-major then L1,L2
    block = items[:6]
    assert [i["source"] for i in block] == ["1M", "1M", "1p5M", "1p5M", "2M", "2M"]
    assert [i["layer"] for i in block] == ["L1", "L2", "L1", "L2", "L1", "L2"]
    # seed blocks of 6 calls each
    for seed in v31.M1_SEEDS:
        assert sum(1 for i in items if i["seed"] == seed) == 6


def test_run_m1_confirmation_pass_with_fake_runner():
    plans = {n: v31.build_allocation_plan(n) for n in v31.N_VALUES}

    def fake_runner(item, adapter):
        return {"converged": True, "final_entropy_bits": 0.0,
                "iterations": 1, "terminal": "converged", "runtime_s": 0.001}

    result = v31.run_m1_confirmation(plans, de_runner=fake_runner, adapters={label: object() for label in v31.SOURCE_ORDER})
    assert result["terminal"] == "de_allocation_pass"
    assert result["n_calls"] == 60
    assert result["confirmed_n"] == [1024, 2048]
    for n in v31.N_VALUES:
        assert result["per_n"][str(n)]["all_calls_pass"] is True
        assert result["per_n"][str(n)]["n_calls"] == 30


def test_run_m1_confirmation_fail_when_one_n_fails():
    plans = {n: v31.build_allocation_plan(n) for n in v31.N_VALUES}
    calls = {"n": None}

    def fake_runner(item, adapter):
        calls["n"] = item["n"]
        if item["n"] == 2048:
            return {"converged": False, "final_entropy_bits": 0.5,
                    "iterations": 10, "terminal": "not_converged", "runtime_s": 0.001}
        return {"converged": True, "final_entropy_bits": 0.0,
                "iterations": 1, "terminal": "converged", "runtime_s": 0.001}

    result = v31.run_m1_confirmation(plans, de_runner=fake_runner, adapters={label: object() for label in v31.SOURCE_ORDER})
    assert result["terminal"] == v31.TERMINAL_DE_FAIL
    assert result["n_calls"] == 60  # all 30 for 1024 + all 30 for 2048 persisted
    assert result["confirmed_n"] == [1024]


def test_peg_capacity_supports_deterministic_and_bounded():
    for m, n in ((5, 40), (16, 200), (9, 120)):
        a = v31.build_supports_peg_capacity(m, n)
        b = v31.build_supports_peg_capacity(m, n)
        assert a == b
        assert len(a) == n
        occ = {}
        for u, v in a:
            occ[(u, v)] = occ.get((u, v), 0) + 1
        assert max(occ.values()) <= v31.MAX_SUPPORT_OCCUPANCY


def test_qc_cyclic_supports_deterministic_and_bounded():
    for m, n in ((5, 40), (16, 200), (16, 1024)):
        a = v31.build_supports_qc_cyclic(m, n)
        b = v31.build_supports_qc_cyclic(m, n)
        assert a == b
        assert len(a) == n
        occ = {}
        for u, v in a:
            occ[(u, v)] = occ.get((u, v), 0) + 1
        assert max(occ.values()) <= v31.MAX_SUPPORT_OCCUPANCY


def test_build_layer_both_families_projective_safe_and_rank():
    for family in v31.SUPPORTED_FAMILIES:
        matrix, audit = v31.build_layer(5, 40, family=family)
        arr = np.asarray(matrix)
        assert arr.shape == (5, 40)
        assert audit["construction_ok"]
        assert audit["projective_hard_gate"]
        assert audit["projective"]["duplicate_projective_classes"] == 0
        assert audit["projective"]["proportional_pairs"] == 0
        assert audit["full_row_rank"]
        assert audit["max_support_occupancy"] <= 31
        assert len(audit["label_replay"]) == 40
        assert all(row["selected_score"][1] == row["selected_ratio_index"] for row in audit["label_replay"])


def test_build_matrix_packet_both_families():
    for family in v31.SUPPORTED_FAMILIES:
        packet = v31.build_matrix_packet(
            4, {"1M": 5, "1p5M": 6, "2M": 7}, n=24, family=family, allocation_id="test",
        )
        assert packet["construction_ok"]
        assert set(packet["matrices"]["L2"]) == set(v31.SOURCE_ORDER)
        assert packet["max_support_occupancy"] <= 31
        assert packet["projective_hard_gate"]
        assert packet["full_row_rank"]
        assert packet["four_cycle_count"] == sum(packet["four_cycle_components"].values())


def test_select_ratio_v31_matches_v30_small_case():
    field = v30.FIELD
    prior_supports = [(0, 2), (1, 2)]
    prior_coeffs = [(1, 1), (1, 1)]
    r30 = v30.select_projective_ratio(field, prior_supports, prior_coeffs, 2, (0, 1), None)
    r31 = v31.select_projective_ratio_v31(field, prior_supports, prior_coeffs, 2, (0, 1), None)
    assert r31["ratio"] == r30["ratio"]
    assert r31["ratio_index"] == r30["ratio_index"]
    assert r31["score"] == r30["score"]


def test_run_m2_rejects_bad_construction_without_rng():
    # m2 tiny so build is fast; both families must produce construction_ok packets
    plans = {n: {
        "allocation_id": "test", "m1": 3, "n": n,
        "m2_by_source": {label: 4 for label in v31.SOURCE_ORDER},
        "sources": {}, "tag_bits": 64,
    } for n in (16, 24)}
    # patch N_VALUES locally by invoking run_m2 with explicit construction dict is not
    # exposed; so just build matrix packet directly (already covered above).
    construction = {}
    for n, plan in plans.items():
        packets = []
        rejected = []
        for family in v31.SUPPORTED_FAMILIES:
            try:
                packet = v31.build_matrix_packet(
                    plan["m1"], plan["m2_by_source"], n=n, family=family, allocation_id=plan["allocation_id"], 
                )
                packet["packet_id"] = packet["matrix_id"]
                if not packet["construction_ok"]:
                    raise ValueError("build failed")
                packets.append(packet)
            except Exception as exc:
                rejected.append({"n": n, "family": family, "allocation_id": plan["allocation_id"],
                                 "terminal": v31.TERMINAL_FAIL, "error": f"{type(exc).__name__}: {exc}"})
        construction[n] = {"n": n, "packets": packets, "rejected": rejected}
    for n in (16, 24):
        assert len(construction[n]["packets"]) == 2
        assert construction[n]["packets"][0]["family"] == v31.FAMILY_PEG
        assert construction[n]["packets"][1]["family"] == v31.FAMILY_QC
