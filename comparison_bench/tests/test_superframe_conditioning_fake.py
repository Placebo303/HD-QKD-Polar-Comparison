"""Fake-only tests for superframe conditioning arithmetic (packet P-3).

Hand-computable constants only; zero scientific/real-data contact -- this
file reads no M0 CSV, no CQ JSON, nothing. Temporary directories live
under fresh additive workspace/sf__pytest_<uuid8> roots.
"""

from __future__ import annotations

import json
import math
import uuid
from pathlib import Path

import pytest

from comparison_bench.src.comparison_bench.cli import superframe_conditioning as sf


def _fresh_root() -> Path:
    root = Path(f"workspace/sf__pytest_{uuid.uuid4().hex[:8]}")
    root.mkdir(parents=False, exist_ok=False)
    return root


def _row(m, sframe, err, ok=True, undet=False):
    return {"m": str(m), "superframe": str(sframe),
            "exact_match": "True" if ok else "False",
            "undetected": "True" if undet else "False",
            "raw_symbol_errors": str(err), "u2_symbol_errors": str(err)}


def test_dedup_agreement_three_superframes():
    rows = []
    for sframe, err in enumerate([10, 20, 30]):
        rows.append(_row(200, sframe, err))
        rows.append(_row(204, sframe, err))
    x, m_lo, m_hi, p_lo = sf.dedup_sequence(rows)
    assert x == [10, 20, 30]
    assert (m_lo, m_hi) == (200, 204)
    assert p_lo == 1.0


def test_dedup_refuses_cross_arm_disagreement():
    rows = [_row(200, 0, 10), _row(204, 0, 11),
            _row(200, 1, 20), _row(204, 1, 20)]
    with pytest.raises(sf.Refusal):
        sf.dedup_sequence(rows)


def test_dedup_refuses_raw_u2_mismatch():
    rows = [_row(200, 0, 10), _row(204, 0, 10)]
    rows[0] = dict(rows[0], u2_symbol_errors="9")
    with pytest.raises(sf.Refusal):
        sf.dedup_sequence(rows)


def test_dedup_refuses_wrong_dm():
    rows = [_row(200, 0, 10), _row(206, 0, 10)]
    with pytest.raises(sf.Refusal):
        sf.dedup_sequence(rows)


def test_drift_z_hand_sequence():
    # halves [1,2,3] mean 2 var 1; [10,11,12] mean 11 var 1;
    # SE = sqrt(1/3+1/3), z = 9/SE.
    x = [1, 2, 3, 10, 11, 12]
    d = sf.drift_stats(x)
    assert d["z"] == pytest.approx(9.0 / math.sqrt(2.0 / 3.0), abs=1e-9)
    assert d["flag_drift"] is True


def test_drift_silent_on_flat_halves():
    x = [10, 11, 9, 10, 11, 9]
    d = sf.drift_stats(x)
    assert abs(d["z"]) < 3.0
    assert d["flag_drift"] is False


def test_autocorr_fires_on_trend():
    # n = 20 monotonic: r_1 ~ 1 > 3/sqrt(20) ~ 0.6708.
    x = list(range(1, 21))
    c = sf.autocorr_family(x)
    assert c["r_1"] == pytest.approx(1.0, abs=1e-9)
    assert c["flag_corr"] is True


def test_autocorr_silent_on_short_alternation():
    # Block-alternating hand sequence, n = 12: r_1 = 0.1, silent against
    # the 3/sqrt(12) ~ 0.866 band; n >= 12 keeps every k = 1..5 lag window
    # at length >= 7 with nonzero variance (length-1 windows STOP per §9).
    x = [0, 0, 10, 10] * 3
    c = sf.autocorr_family(x)
    assert c["r_1"] == pytest.approx(0.1, abs=1e-9)
    assert c["flag_corr"] is False


def test_autocorr_all_five_lags_present():
    x = list(range(1, 21))
    c = sf.autocorr_family(x)
    for k in range(1, 6):
        assert math.isfinite(c[f"r_{k}"])


def test_dispersion_fires_on_overdispersed():
    # [0,0,0,0,100]: mean 20, var 2000, D = 100 > 3.121 band.
    x = [0, 0, 0, 0, 100]
    v = sf.dispersion_family(x)
    assert v["D"] == pytest.approx(100.0, abs=1e-9)
    assert v["flag_overdisp"] is True


def test_dispersion_silent_on_poisson_like():
    # [10,9,11,10,9,11]: mean 10, var 0.8, D = 0.08 < 1.
    x = [10, 9, 11, 10, 9, 11]
    v = sf.dispersion_family(x)
    assert v["D"] == pytest.approx(0.08, abs=1e-9)
    assert v["flag_overdisp"] is False


def test_t3a_twenty_times_p_lo_with_undetected_excluded():
    # lo-arm: 2 successes, 1 plain failure, 1 undetected (excluded).
    rows = [_row(200, 0, 10, ok=True), _row(204, 0, 10, ok=True),
            _row(200, 1, 20, ok=True), _row(204, 1, 20, ok=True),
            _row(200, 2, 30, ok=False), _row(204, 2, 30, ok=False),
            _row(200, 3, 40, ok=True, undet=True), _row(204, 3, 40, ok=False)]
    _, _, _, p_lo = sf.dedup_sequence(rows)
    assert p_lo == pytest.approx(0.5)
    assert sf.t3a_saving(p_lo) == pytest.approx(10.0)


def test_t3b_ten_times_spread():
    assert sf.t3b_spread([10, 20, 30]) == pytest.approx(100.0)


def test_decide_gate_both_sides():
    assert sf.decide_word(True, 215.0) == ("PASS", "section 5.1")
    assert sf.decide_word(True, 214.999)[0] == "KILL"
    assert "5.3" in sf.decide_word(True, 100.0)[1]
    assert "5.2" in sf.decide_word(False, 100000.0)[1]


def test_path_gate_refuses_forbidden_suffixes():
    for bad in ("workspace/x/frames.ttbin",
                "workspace/x/gamma_f03.npz",
                "comparison_bench/outputs_comparison/ir_frame_results.parquet",
                "workspace/m0_359922a7_1M/rows.json"):
        with pytest.raises(sf.Refusal):
            sf.validate_input_path(bad)


def test_path_gate_refuses_nonfrozen_file():
    with pytest.raises(sf.Refusal):
        sf.validate_input_path("workspace/cq_15d6f160/CQ-20c.json")


def test_path_gate_accepts_frozen_eight():
    for path, label in sf.FROZEN_INPUTS.items():
        assert sf.validate_input_path(path) == label


def test_root_gate():
    assert sf.validate_root_string("workspace/sf_ab12cd34") == "workspace/sf_ab12cd34"
    for bad in ("results/sf_ab12cd34",
                "comparison_bench/outputs_comparison/sf_ab12cd34",
                "workspace/sf__pytest_ab12cd34"):
        with pytest.raises(sf.Refusal):
            sf.validate_root_string(bad)


def test_prepare_root_refuses_evidence_collision():
    root = _fresh_root()
    (root / "SF_RESULT.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
    with pytest.raises(sf.Refusal):
        sf.prepare_root(root, root / "SF_LOG.md")


def test_frozen_reference_constants():
    assert (sf.R_NOMINAL_M, sf.R_NOMINAL_BUDGET, sf.R_NOMINAL_FIT) == (1100, 1104, 4)
    assert (sf.R_BACKOFF_M, sf.R_BACKOFF_EXCESS) == (1319, 215)
    assert (sf.R_M_SLOPE, sf.R_M_TAG, sf.R_DM, sf.R_T3A_CAP) == (5, 64, 4, 20)
    assert (sf.R_PLANES, sf.R_SPREAD_C) == (10, 10)
