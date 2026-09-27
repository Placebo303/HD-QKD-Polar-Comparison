"""Fake-only tests for the layered-binary LDPC baseline (M2 T9; no real data).

Zero production calls: every run injects explicit fake ``construct_fn``/``decode_fn``
AND monkeypatches the production PEG + binary-SPA path to raise. Tiny synthetic
inputs only (3 frames x 4 symbols, d=1024, explicit ``allow_non64=True``). Zero disk
writes by construction (no writer, no root, no file import anywhere in this file).
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.methods import layered_binary as lb
from comparison_bench.src.comparison_bench.types import FrameBatch, IRRunConfig


def _batch() -> FrameBatch:
    alice = np.array([[0, 1, 2, 3], [5, 6, 7, 8], [10, 11, 12, 13]], dtype=np.int64)
    bob = alice.copy()
    bob[2, 3] = (bob[2, 3] + 2) % 1024  # one raw symbol error -> finite raw BER
    return FrameBatch("fake-lb", alice, bob, 1024, 4, {"mapping": "gray"})


def _cfg() -> IRRunConfig:
    return IRRunConfig("layered_binary", "per_plane_blind", 1024, 4, 300)


def _allocation() -> lb.PlaneAllocation:
    rows = {0: 20, 1: 20, 2: 20, 3: 20, 4: 20, 5: 20, 6: 21, 7: 21, 8: 21, 9: 21}
    assert sum(rows.values()) == 204
    return lb.PlaneAllocation(source_key="2M", h_basis=0.832563, m_basis=204, plane_rows=rows)


def _stages() -> lb.BlindStageTable:
    return lb.BlindStageTable(m_init=190, delta_steps=[4, 5, 5])


def _params() -> lb.LayeredParams:
    return lb.LayeredParams(source_key="2M", allow_non64=True)


def _fake_construct(n_plane, m_rows, seed, frame_idx, plane_idx):
    assert n_plane == 4  # tiny fake plane length (production n=64 family bypassed explicitly)
    return {"triples": [(0, 0, 1)], "status": "ok", "four_cycles": 0,
            "min_girth": 8, "rank": 1, "n": n_plane, "m": m_rows}


def _fake_decode(a_planes, b_planes, constructions, stages, frame_idx, max_iter, streak):
    assert (max_iter, streak) == (300, 3)  # frozen SPA pins reach the (fake) decoder
    assert len(a_planes) == 10 and len(constructions) == 10
    script = {
        0: {"exact_match": True, "accepted": True, "syndrome_consistent": True,
            "toeplitz_verified": True, "leak_ec_bits": 60, "blind_stage_bits": [4, 5, 0],
            "rescue_bits": 0.0, "control_bits": 1, "messages_actual": 3.14,
            "prior_entropy_bits": 8.0, "construction": "fake"},
        # syndrome ok but Toeplitz fails -> accepted-wrong (undetected), never success.
        1: {"exact_match": False, "accepted": True, "syndrome_consistent": True,
            "toeplitz_verified": False, "leak_ec_bits": 70, "blind_stage_bits": [4, 5, 5],
            "rescue_bits": 6.0, "control_bits": 1, "messages_actual": 3.14,
            "prior_entropy_bits": 9.0, "construction": "fake"},
        2: {"exact_match": False, "accepted": False, "syndrome_consistent": False,
            "toeplitz_verified": False, "leak_ec_bits": 50, "blind_stage_bits": [4, 0, 0],
            "rescue_bits": 0.0, "control_bits": 1, "messages_actual": 1.0,
            "prior_entropy_bits": 7.0, "construction": "fake"},
    }
    return dict(script[int(frame_idx)])


def test_plane_split_reuses_gray_helper():
    from comparison_bench.src.comparison_bench.methods.layered_ldpc_lite import split_symbol_bitplanes
    planes = split_symbol_bitplanes(np.array([0, 1]), 1024, mapping="gray")
    assert len(planes) == 10
    assert planes[9].tolist() == [0, 1]  # Gray(0)=0, Gray(1)=1 differ only in LSB plane


def test_allocation_sum_gate_and_no_refit():
    rows = {p: 20 for p in range(10)}  # Σ=200 != 204
    with pytest.raises(ValueError, match="m_basis"):
        lb.PlaneAllocation(source_key="2M", h_basis=0.832563, m_basis=204,
                           plane_rows=rows).validated(10)
    good_rows = dict(_allocation().plane_rows)
    with pytest.raises(ValueError, match="no refit"):
        lb.PlaneAllocation(source_key="2M", h_basis=0.90, m_basis=204,
                           plane_rows=good_rows).validated(10)
    with pytest.raises(ValueError, match="exactly"):
        lb.PlaneAllocation(source_key="2M", h_basis=0.832563, m_basis=204,
                           plane_rows={p: 20 for p in range(9)}).validated(10)
    over = {0: 65, 1: 15, 2: 15, 3: 15, 4: 15, 5: 15, 6: 16, 7: 16, 8: 16, 9: 16}
    assert sum(over.values()) == 204  # sum gate passes; single-plane gate must refuse
    with pytest.raises(ValueError, match="plane 0"):
        lb.PlaneAllocation(source_key="2M", h_basis=0.832563, m_basis=204,
                           plane_rows=over).validated(10)


def test_blind_stage_and_spa_freeze():
    with pytest.raises(ValueError, match="positive ints"):
        lb.BlindStageTable(m_init=190, delta_steps=[]).validated()
    with pytest.raises(ValueError, match="positive ints"):
        lb.BlindStageTable(m_init=190, delta_steps=[4, -1]).validated()
    with pytest.raises(ValueError, match="frozen"):
        lb.LayeredParams(source_key="2M", max_iter=100, allow_non64=True).validated()
    with pytest.raises(ValueError, match="frozen"):
        lb.LayeredParams(source_key="2M", streak=5, allow_non64=True).validated()
    with pytest.raises(ValueError, match="n=64"):
        lb.run_layered_binary(_batch(), _cfg(), allocation=_allocation(), stages=_stages(),
                              params=lb.LayeredParams(source_key="2M"),
                              construct_fn=_fake_construct, decode_fn=_fake_decode)


def test_fake_run_accounting(monkeypatch):
    # Production PEG + SPA must never be entered: prove fake-only by arming to raise.
    monkeypatch.setattr(lb, "_construct_plane_production", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("production PEG entered during fake test")))
    monkeypatch.setattr(lb, "_spa_decode_production", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("production SPA entered during fake test")))
    res = lb.run_layered_binary(_batch(), _cfg(), allocation=_allocation(), stages=_stages(),
                                params=_params(), construct_fn=_fake_construct,
                                decode_fn=_fake_decode)
    md = res.metadata
    # Four counts + undetected isolation incl. the syndrome-ok/Toeplitz-fail gate.
    assert (res.n_frames_attempted, res.n_frames_success) == (3, 1)
    assert md["accepted_wrong"] == 1 and md["undetected"] == 1
    assert md["frame_results"][1]["accepted_wrong"] is True
    assert md["frame_results"][1]["syndrome_consistent"] is True
    assert md["frame_results"][1]["toeplitz_verified"] is False
    assert md["fer"] == pytest.approx(2 / 3)
    # Blind stages join leak_EC decomposition; rescue stays single column.
    assert md["lambda_parts"]["blind_stages"] == pytest.approx([12.0, 10.0, 5.0])
    assert md["lambda_parts"]["leak_EC"] == pytest.approx(69.0 + 84.0 + 54.0)
    assert md["lambda_parts"] == {"leak_EC": pytest.approx(207.0), "tag": 192.0,
                                  "rescue": 6.0, "control": 3.0,
                                  "blind_stages": pytest.approx([12.0, 10.0, 5.0])}
    assert md["lambda_total"] == pytest.approx(207.0 + 192.0 + 6.0 + 3.0)
    # f triple, this-arm m basis (m=204, own-source H), prior-free numerator.
    h, m = 0.832563, 204
    assert md["f_super"] == pytest.approx((5 * m + 64) / (1024 * h))
    assert md["f_notag"] == pytest.approx((5 * m) / (1024 * h))
    assert md["f_eff"] == pytest.approx(md["f_super"] + 4.785675 * (2 / 3))
    assert abs(md["f_super"] * 1024 * h - (5 * m + 64)) < 1e-9
    # 1.50x prior report-only, excluded from λ_total and f numerators.
    assert md["prior_1p50_reportonly"] == pytest.approx(1.50 * (8.0 + 9.0 + 7.0))
    # Messages: LDPC 3.14 aperture + actual, Cascade 446 non-comparable.
    assert md["messages_ldpc_ref"] == 3.14
    assert md["messages_per_frame_actual"] == pytest.approx((3.14 + 3.14 + 1.0) / 3)
    assert md["messages_cascade_ref_noncomparable"] == 446
    # Allocation rows echo Σm_j=m; SPA pins frozen; N_req/d/q/n_IR columns.
    assert sum(md["allocation_rows"].values()) == 204
    assert md["spa_pins"] == {"max_iter": 300, "streak": 3}
    assert md["blind_schedule"] == {"m_init": 190, "delta_steps": [4, 5, 5]}
    assert md["n_req_reportonly"] == float(math.ceil(3 * 4.785675 / (1.3 - md["f_super"])))
    assert md["key_eligible_contrast"] == (200, 276, 364)
    assert md["d_dim"] == 1024 and md["n_ir_bits"] == 40
    assert res.beta_eff_empirical == pytest.approx(0.0)
    assert res.method == "layered_binary" and md["method_status"] == "ok"
