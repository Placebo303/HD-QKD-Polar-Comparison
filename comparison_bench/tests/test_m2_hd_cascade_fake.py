"""Fake-only tests for the HD-Cascade honest baseline (M2 T8; no real data).

Zero production calls: every run injects an explicit fake ``decode_fn`` AND
monkeypatches the production per-plane cascade path to raise. Tiny synthetic
inputs only (3 frames x 4 symbols, d=1024). Zero disk writes by construction
(no writer, no root, no file import anywhere in this file).
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.methods import hd_cascade as hc
from comparison_bench.src.comparison_bench.types import FrameBatch, IRRunConfig


def _batch() -> FrameBatch:
    alice = np.array([[0, 1, 2, 3], [5, 6, 7, 8], [10, 11, 12, 13]], dtype=np.int64)
    bob = alice.copy()
    bob[0, 0] = (bob[0, 0] + 1) % 1024  # one raw symbol error -> finite raw BER
    return FrameBatch("fake-hdc", alice, bob, 1024, 4, {"mapping": "gray"})


def _cfg() -> IRRunConfig:
    return IRRunConfig("hd_cascade", "mueller3_parallel", 1024, 4, 10)


def _table() -> hc.HdCascadeBlockTable:
    return hc.HdCascadeBlockTable({p: [8, 4] for p in range(10)}, max_cross_plane_sweeps=1)


def _params() -> hc.HdCascadeParams:
    return hc.HdCascadeParams(source_key="1M", h_basis=0.801038, m_basis=197)


def _fake_decode(a_planes, b_planes, schedules, frame_idx, seed):
    script = {
        0: {"exact_match": True, "accepted": True, "toeplitz_verified": True,
            "leak_ec_bits": 40, "rescue_bits": 0.0, "control_bits": 2,
            "messages_actual": 446, "prior_entropy_bits": 10.0},
        1: {"exact_match": False, "accepted": True, "toeplitz_verified": False,  # undetected
            "leak_ec_bits": 50, "rescue_bits": 8.0, "control_bits": 2,
            "messages_actual": 446, "prior_entropy_bits": 12.0},
        2: {"exact_match": False, "accepted": False, "toeplitz_verified": False,  # fail
            "leak_ec_bits": 30, "rescue_bits": 0.0, "control_bits": 2,
            "messages_actual": 200, "prior_entropy_bits": 9.0},
    }
    assert len(schedules) == 10  # 改①: one schedule per Gray plane
    return dict(script[int(frame_idx)])


def test_gray_plane_grouping_10bit():
    planes = hc.symbols_to_gray_planes(np.array([0, 1]), 1024)
    assert len(planes) == 10
    # Gray(0)=0, Gray(1)=1: only the LSB plane differs.
    assert planes[9].tolist() == [0, 1]
    for p in range(9):
        assert planes[p].tolist() == [0, 0]


def test_block_table_missing_plane_refuses():
    with pytest.raises(ValueError, match="missing planes"):
        hc.HdCascadeBlockTable({p: [8] for p in range(9)}).planes(10)
    with pytest.raises(ValueError, match="missing plane"):
        hc.HdCascadeBlockTable({p: [8] for p in range(9)}).schedule_for(9)


def test_cross_source_h_refused_and_tag_frozen():
    bad = hc.HdCascadeParams(source_key="1M", h_basis=0.832563, m_basis=197)
    with pytest.raises(ValueError, match="own-source"):
        hc.run_hd_cascade(_batch(), _cfg(), params=bad, block_table=_table(), decode_fn=_fake_decode)
    bad_tag = hc.HdCascadeParams(source_key="1M", h_basis=0.801038, m_basis=197, tag_bits=32)
    with pytest.raises(ValueError, match="tag_bits frozen"):
        hc.run_hd_cascade(_batch(), _cfg(), params=bad_tag, block_table=_table(), decode_fn=_fake_decode)


def test_fake_run_accounting(monkeypatch):
    # Production path must never be entered: prove fake-only by arming it to raise.
    monkeypatch.setattr(hc, "_run_planes_production", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("production cascade entered during fake test")))
    res = hc.run_hd_cascade(_batch(), _cfg(), params=_params(), block_table=_table(),
                            decode_fn=_fake_decode)
    md = res.metadata
    # Four counts + undetected isolation (A-CMPE-1).
    assert (res.n_frames_attempted, res.n_frames_success) == (3, 1)
    assert md["accepted_wrong"] == 1 and md["undetected"] == 1
    assert md["fer"] == pytest.approx(2 / 3)
    assert res.n_frames_failed_decode == 1 and res.n_frames_failed_verify == 1
    # f triple, this-arm m basis (A-CMPE-2): packet literals, prior-free numerator.
    h, m = 0.801038, 197
    assert md["f_super"] == pytest.approx((5 * m + 64) / (1024 * h))
    assert md["f_notag"] == pytest.approx((5 * m) / (1024 * h))
    assert md["f_eff"] == pytest.approx(md["f_super"] + 4.785675 * (2 / 3))
    assert abs(md["f_super"] * 1024 * h - (5 * m + 64)) < 1e-9  # no prior term
    assert md["f_super"] > md["f_notag"]
    # λ_total decomposition (A-CMPE-3): leak + 64tag + rescue single col + control.
    assert md["lambda_parts"] == {"leak_EC": 120.0, "tag": 192.0, "rescue": 8.0, "control": 6.0}
    assert md["lambda_total"] == pytest.approx(120.0 + 192.0 + 8.0 + 6.0)
    assert md["frame_results"][1]["lambda_total"] == pytest.approx(50.0 + 64.0 + 8.0 + 2.0)
    # 1.50x prior report-only, never into λ_total/f numerators (A-CMPE-3).
    assert md["prior_1p50_reportonly"] == pytest.approx(1.50 * (10.0 + 12.0 + 9.0))
    assert md["lambda_total"] == pytest.approx(
        md["lambda_parts"]["leak_EC"] + md["lambda_parts"]["tag"]
        + md["lambda_parts"]["rescue"] + md["lambda_parts"]["control"])
    # Messages: Cascade 446 aperture + actual, LDPC 3.14 non-comparable (A-CMPE-4).
    assert md["messages_cascade_ref"] == 446
    assert md["messages_per_frame_actual"] == pytest.approx((446 + 446 + 200) / 3)
    assert md["messages_ldpc_ref_noncomparable"] == 3.14
    # N_req report-only, d/q/n_IR separated (A-CMPE-5).
    assert md["n_req_reportonly"] == float(math.ceil(3 * 4.785675 / (1.3 - md["f_super"])))
    assert md["key_eligible_contrast"] == (200, 276, 364)
    assert (md["d_dim"], md["q_alphabet"], md["n_ir_bits"]) == (1024, 1024, 40)
    # beta derived from leakage/error inputs (clamped over-disclosure -> 0.0).
    assert res.beta_eff_empirical == pytest.approx(0.0)
    assert res.method == "hd_cascade" and md["method_status"] == "ok"


def test_success_requires_accepted_gate(monkeypatch):
    # Unified gate (layered style): exact + verified but NOT accepted is not success.
    monkeypatch.setattr(hc, "_run_planes_production", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("production cascade entered during fake test")))
    alice = np.array([[0, 1]], dtype=np.int64)
    batch = FrameBatch("fake-hdc-gate", alice, alice.copy(), 1024, 2, {"mapping": "gray"})
    cfg = IRRunConfig("hd_cascade", "mueller3_parallel", 1024, 2, 10)

    def _gate(a_planes, b_planes, schedules, frame_idx, seed):
        return {"exact_match": True, "accepted": False, "toeplitz_verified": True,
                "leak_ec_bits": 40, "rescue_bits": 0.0, "control_bits": 2,
                "messages_actual": 446, "prior_entropy_bits": 10.0}

    res = hc.run_hd_cascade(batch, cfg, params=_params(), block_table=_table(), decode_fn=_gate)
    assert res.n_frames_success == 0
    assert res.n_frames_failed_decode == 1
    assert res.metadata["accepted_wrong"] == 0
