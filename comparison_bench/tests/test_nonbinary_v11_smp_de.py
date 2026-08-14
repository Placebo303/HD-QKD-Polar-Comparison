"""V11 SMP-DE reference tests (additive; V11-10.1/10.2 scope, T0/T1).

T0: module import, function signatures, frozen constants.
T1: DE sanity — the noiseless limit (p=0 -> zero error), the saturation
limit (p=(q-1)/q -> uniform, no convergence), threshold-search
monotonicity/convergence, and trace completeness.  Reproduction of the four
published AEIT 2019 anchors is covered by the frozen evidence bundle and the
CLI ``--reproduce`` gate; here we assert the module-level reproduction
constants and the fail-closed validators instead of re-running the (slow)
full coupled bisection.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v11_smp_de as v11


# --------------------------------------------------------------------------- #
# T0: import, signatures, frozen constants
# --------------------------------------------------------------------------- #


def test_module_import_and_all_exports():
    expected = {
        "W_FROZEN", "REPRODUCTION_DV", "REPRODUCTION_DC",
        "PUBLISHED_THRESHOLDS", "REPRODUCTION_TOL", "SEARCH_P_TOL",
        "qsc_reliability", "check_update_uncoupled",
        "variable_update_uncoupled", "run_smp_de_uncoupled", "SCWindow",
        "check_update_coupled", "variable_update_coupled",
        "app_update_coupled", "run_smp_de_coupled",
        "threshold_binary_search", "reproduce_ben_yacoub_2019",
    }
    assert expected <= set(v11.__all__)


def test_frozen_constants():
    assert v11.W_FROZEN == 30
    assert v11.REPRODUCTION_DV == 3
    assert v11.REPRODUCTION_DC == 6
    assert v11.REPRODUCTION_TOL == 0.002
    assert v11.SEARCH_P_TOL <= 0.001  # design.md R1: search tolerance at most .001
    assert v11.PUBLISHED_THRESHOLDS == {
        (4, "uncoupled"): 0.0890,
        (16, "uncoupled"): 0.1075,
        (4, "coupled"): 0.0942,
        (16, "coupled"): 0.1288,
    }


def test_function_signatures():
    import inspect
    assert list(inspect.signature(v11.check_update_uncoupled).parameters) == ["p0", "dc", "q"]
    assert list(inspect.signature(v11.variable_update_uncoupled).parameters) == [
        "s0", "eps", "dv", "q"]
    assert list(inspect.signature(v11.run_smp_de_uncoupled).parameters)[:4] == [
        "q", "dv", "dc", "eps"]
    assert list(inspect.signature(v11.run_smp_de_coupled).parameters)[:5] == [
        "q", "dv", "dc", "eps", "W"]
    assert list(inspect.signature(v11.threshold_binary_search).parameters)[:5] == [
        "q", "dv", "dc", "mode", "W"]


def test_fail_closed_domain_validation():
    with pytest.raises(ValueError):
        v11.run_smp_de_uncoupled(4, 3, 6, -0.1)
    with pytest.raises(ValueError):
        v11.run_smp_de_uncoupled(4, 3, 6, 1.5)
    with pytest.raises(ValueError):
        v11.run_smp_de_uncoupled(4, 4, 8, 0.1)  # dv != 3 is rejected (frozen)
    with pytest.raises(ValueError):
        v11.run_smp_de_uncoupled(4, 3, 9, 0.1)  # dc/dv != 2 rejected
    with pytest.raises(ValueError):
        v11.threshold_binary_search(4, 3, 6, "bogus")
    with pytest.raises(ValueError):
        v11.qsc_reliability(1.5, 4)


# --------------------------------------------------------------------------- #
# T1: uncoupled DE sanity
# --------------------------------------------------------------------------- #


def test_uncoupled_noiseless_limit():
    # p = 0: channel is noiseless, first VN message is always correct;
    # check update yields s0 -> 1 and the run converges immediately.
    result = v11.run_smp_de_uncoupled(4, 3, 6, 0.0, max_iter=50)
    assert result["converged"] is True
    assert result["p0_trace"][-1] == pytest.approx(1.0)
    assert result["s0_trace"][-1] == pytest.approx(1.0)


def test_uncoupled_saturation_limit():
    # p = (q-1)/q: channel is pure noise; messages saturate to uniform, so
    # p0 -> 1/q and the DE never converges.
    result = v11.run_smp_de_uncoupled(4, 3, 6, 3.0 / 4.0, max_iter=200)
    assert result["converged"] is False
    assert result["p0_trace"][-1] == pytest.approx(1.0 / 4.0, abs=1e-9)


def test_uncoupled_monotonic_p0_and_threshold():
    # Below the threshold p0 rises towards 1; the run converges; the search
    # returns a threshold consistent with the published anchor.
    result = v11.run_smp_de_uncoupled(4, 3, 6, 0.05, max_iter=500)
    assert result["converged"] is True
    trace = result["p0_trace"]
    # trace[0] is the value AFTER the first full iteration (initialized at
    # 1 - eps, then check+variable update), so it already exceeds the
    # channel reliability and keeps rising towards 1.
    assert trace[0] > 1.0 - 0.05
    assert trace[-1] > trace[0]
    search = v11.threshold_binary_search(4, 3, 6, "uncoupled", p_tol=0.001,
                                         max_iter=500)
    threshold = search["threshold_proxy"]
    assert 0.085 <= threshold <= 0.092  # published 0.0890 within .002 + search tol
    assert abs(threshold - v11.PUBLISHED_THRESHOLDS[(4, "uncoupled")]) <= \
        v11.REPRODUCTION_TOL + search["p_tol"]


def test_uncoupled_trace_completeness():
    result = v11.run_smp_de_uncoupled(4, 3, 6, 0.05, max_iter=300)
    assert len(result["p0_trace"]) == len(result["s0_trace"]) == result["iterations"]
    assert all(0.0 <= value <= 1.0 for value in result["p0_trace"])
    assert result["q"] == 4 and result["dv"] == 3 and result["dc"] == 6
    assert result["eps"] == 0.05


def test_uncoupled_determinism():
    first = v11.run_smp_de_uncoupled(4, 3, 6, 0.05, max_iter=100)
    second = v11.run_smp_de_uncoupled(4, 3, 6, 0.05, max_iter=100)
    assert first["p0_trace"] == second["p0_trace"]
    assert first["iterations"] == second["iterations"]


# --------------------------------------------------------------------------- #
# T1: coupled (windowed) DE sanity
# --------------------------------------------------------------------------- #


def test_coupled_window_structure():
    window = v11.SCWindow(4, 3, 6, W=8)  # small window for speed
    assert window.n0 == 2
    assert window.w == 2
    assert window.rows == 5 * 8
    # first block column VN type must exist and be tracked
    assert 1 in window.by_vn
    # every check row's columns satisfy 0 <= r - c <= w
    for r, cols in window.by_check.items():
        for c in cols:
            assert 0 <= r - c <= window.w
            assert 1 <= c <= 8


def test_coupled_noiseless_limit():
    result = v11.run_smp_de_coupled(4, 3, 6, 0.0, W=8, max_iter=100)
    assert result["converged"] is True
    assert result["app_trace"][-1] == pytest.approx(1.0)


def test_coupled_saturation_limit():
    result = v11.run_smp_de_coupled(4, 3, 6, 3.0 / 4.0, W=8, max_iter=100)
    assert result["converged"] is False
    assert result["app_trace"][-1] == pytest.approx(1.0 / 4.0, abs=1e-9)


def test_coupled_trace_completeness():
    result = v11.run_smp_de_coupled(4, 3, 6, 0.05, W=8, max_iter=200)
    assert len(result["app_trace"]) == result["iterations"]
    assert all(0.0 <= value <= 1.0 for value in result["app_trace"])
    assert result["W"] == 8


def test_coupled_determinism():
    first = v11.run_smp_de_coupled(4, 3, 6, 0.05, W=8, max_iter=100)
    second = v11.run_smp_de_coupled(4, 3, 6, 0.05, W=8, max_iter=100)
    assert first["app_trace"] == second["app_trace"]


# --------------------------------------------------------------------------- #
# T1: threshold-search structure and reproduction constants
# --------------------------------------------------------------------------- #


def test_threshold_search_bisection_structure():
    search = v11.threshold_binary_search(4, 3, 6, "uncoupled", p_tol=0.001,
                                         max_iter=300)
    assert search["p_tol"] == 0.001
    assert len(search["probes"]) >= 5
    assert all("p" in probe and "converged" in probe and "iterations" in probe
               for probe in search["probes"])
    # The returned bracket [p_lo, p_hi] straddles the threshold and its width
    # is within the search tolerance: a deterministic rerun at the lower bound
    # converges and at the upper bound does not (same iteration budget).
    assert search["p_hi"] - search["p_lo"] <= search["p_tol"]
    assert search["p_lo"] < search["threshold_proxy"] < search["p_hi"]
    lower = v11.run_smp_de_uncoupled(4, 3, 6, search["p_lo"], max_iter=300)
    upper = v11.run_smp_de_uncoupled(4, 3, 6, search["p_hi"], max_iter=300)
    assert lower["converged"] is True
    assert upper["converged"] is False


def test_reproduce_function_shape_without_traces():
    result = v11.reproduce_ben_yacoub_2019(include_traces=False)
    assert result["schema"] == "v11_smp_de_reproduction_v1"
    assert result["status"] in ("reproduce_pass", "failed_reference")
    assert len(result["cases"]) == 4
    for case in result["cases"]:
        assert set(case) >= {"q", "mode", "published", "reproduced",
                             "deviation", "pass", "search"}
