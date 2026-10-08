"""C-2 fit tests (EXPLORE): C2_PACKET.md §2 T0/T1.

T0: unconditional degeneracy checks — δ=0 symmetry P+1=P-1, bw→∞ p→floor,
large-σ limit, A(a) numeric-derivative self-consistency, p even in δ.
T1: synthetic small-case fit recovery (forward-model inversion) + landed
H recomputation check on the Z-2 T2-1M/bw200 literals (no raw data read).
"""

from __future__ import annotations

import math

import pytest

from comparison_bench.src.comparison_bench.formal_ir.msd_c2_fit import (
    A_func,
    H_from_top_errors,
    Phi,
    apply_floor,
    cond_dist,
    fold_err,
    p_cond,
    p_uncond,
    phi_std,
    solve_ab,
    support_pred,
    tail_ge2_obs,
    tail_ge2_pred,
    ternary_uncond,
)


def test_phi_Phi_basic() -> None:
    assert Phi(0.0) == pytest.approx(0.5)
    assert Phi(8.0) == pytest.approx(1.0, abs=1e-12)
    assert Phi(-8.0) == pytest.approx(0.0, abs=1e-12)
    assert phi_std(0.0) == pytest.approx(1.0 / math.sqrt(2 * math.pi))
    # Phi'(x) == phi(x) by finite difference
    h = 1e-6
    assert (Phi(1.0 + h) - Phi(1.0 - h)) / (2 * h) == pytest.approx(
        phi_std(1.0), rel=1e-6)


def test_delta_zero_symmetry() -> None:
    for bw, sig in ((200, 60.0), (400, 60.0), (6400, 60.0), (100, 30.0)):
        pm, _, pp = ternary_uncond(bw, sig, 0.0)
        assert pm == pytest.approx(pp, rel=1e-12)


def test_p_even_in_delta() -> None:
    for d in (10.0, 50.0, 120.0):
        assert p_uncond(200.0, 60.0, d) == pytest.approx(
            p_uncond(200.0, 60.0, -d), rel=1e-12)


def test_A_numeric_derivative_self_consistent() -> None:
    # dA/da = Phi(a/σ) - Phi((a-bw)/σ)
    for a, bw, sig in ((30.0, 200.0, 60.0), (-40.0, 400.0, 55.0),
                       (6400.0, 6400.0, 60.0)):
        h = 1e-5
        num = (A_func(a + h, bw, sig) - A_func(a - h, bw, sig)) / (2 * h)
        ana = Phi(a / sig) - Phi((a - bw) / sig)
        assert num == pytest.approx(ana, rel=1e-6)


def test_fold_err_and_tail_ge2() -> None:
    assert fold_err(1, 4096) == 1
    assert fold_err(4095, 4096) == -1
    assert fold_err(4094, 4096) == -2
    # Z-2 T2-1M bw50 literals: |e|>=2 mass = e2 + e3 + e-2 + rest.
    top = [[1, 0.764616], [0, 0.13851], [2, 0.090746],
           [4095, 0.003397], [3, 0.001687], [4094, 0.000468]]
    t = tail_ge2_obs(top, 4096)
    assert t == pytest.approx(0.090746 + 0.001687 + 0.000468 + 0.000576,
                              abs=1e-6)
    # Gaussian tail prediction is a proper fraction.
    tp = tail_ge2_pred(50.0, 60.0, 50.0)
    assert 0.0 < tp < 1.0


def test_bw_infty_p_goes_to_floor() -> None:
    assert p_uncond(1e9, 60.0, 50.0) == pytest.approx(0.0, abs=1e-6)
    pm, p0, pp = ternary_uncond(1e9, 60.0, 50.0)
    eps = 0.007
    _, p0f, _ = apply_floor(pm, p0, pp, eps)
    assert (1.0 - p0f) == pytest.approx(eps, abs=1e-6)


def test_large_sigma_limit_p_goes_to_one() -> None:
    # P0 ~ bw/(σ√2π) ≈ 8e-6 at σ=1e7: p→1 up to that scale.
    assert p_uncond(200.0, 1e7, 50.0) == pytest.approx(1.0, abs=2e-5)
    pm, _, pp = ternary_uncond(200.0, 1e7, 0.0)
    assert pm == pytest.approx(pp, rel=1e-9)


def test_conditional_sums_to_one() -> None:
    for bw, sig, d in ((50, 60.0, 50.0), (100, 60.0, -50.0)):
        tot = 0.0
        _, cover = cond_dist(bw, sig, d, 0)
        for k in range(-8, 9):
            jk, _ = cond_dist(bw, sig, d, k)
            tot += jk / cover
        assert tot == pytest.approx(1.0, abs=1e-6)
        assert 0.0 < p_cond(bw, sig, d) < 1.0


def test_support_rule_nominal() -> None:
    n = 525831
    assert support_pred(200.0, 60.0, 50.0, n, 1024) == 3
    assert support_pred(6400.0, 60.0, 50.0, n, 32) == 3
    assert support_pred(100.0, 60.0, 50.0, n, 2048) in (3, 5, 7)
    assert support_pred(50.0, 60.0, 50.0, n, 4096) in (7, 9, 11, 13)


def test_H_recompute_matches_landed_nonwide() -> None:
    # Z-2 T2-1M bw200 literals (full 3-support listed, rest = 0).
    top = [[0, 0.76203], [1, 0.23658], [1023, 0.00139]]
    h, rest = H_from_top_errors(top)
    assert rest == pytest.approx(0.0, abs=1e-9)
    assert h == pytest.approx(0.804, abs=1e-3)


def test_synthetic_recovery_estimator_A() -> None:
    sig_true, mag_true = 55.0, 50.0
    p200 = p_uncond(200.0, sig_true, mag_true)
    p400 = p_uncond(400.0, sig_true, mag_true)
    sig_hat, mag_hat = solve_ab(p200, p400)
    assert sig_hat == pytest.approx(sig_true, rel=0.01)
    assert mag_hat == pytest.approx(mag_true, abs=1.0)
