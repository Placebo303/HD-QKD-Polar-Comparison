"""C-1 k-bin tests (OP1): C1-KBIN-01.

Packet §3.1/§4: small exact assertions on support/modulus/fold/syndrome-free
entropy arithmetic, plus the k=1 -> G-1 ternary consistency check against the
landed T2-1M probabilities (literals copied from G1_TERNARY.md; no raw data
is read anywhere in this file).
"""

from __future__ import annotations

import math

import pytest

from comparison_bench.src.comparison_bench.formal_ir.msd_c1_kbin import (
    fold_error,
    modulus,
    params_from_stats,
    support_of,
)


def test_support_and_modulus_exact() -> None:
    assert support_of(1) == [-1, 0, 1]
    assert support_of(2) == [-2, -1, 0, 1, 2]
    assert support_of(3) == [-3, -2, -1, 0, 1, 2, 3]
    assert modulus(1) == 3
    assert modulus(2) == 5
    assert modulus(3) == 7


def test_support_and_modulus_reject_bad_k() -> None:
    for bad in (0, -1, True, 1.5, "1", None):
        with pytest.raises(ValueError):
            support_of(bad)
        with pytest.raises(ValueError):
            modulus(bad)


def test_fold_error_wide_domain() -> None:
    D = 1009
    assert fold_error(0, D, 1) == 0
    assert fold_error(1, D, 1) == 1
    assert fold_error(-1, D, 1) == -1
    assert fold_error(2, D, 1) is None
    assert fold_error(-2, D, 1) is None
    assert fold_error(D - 1, D, 1) == -1
    assert fold_error(D + 1, D, 1) == 1
    assert fold_error(2, D, 2) == 2
    assert fold_error(-2, D, 2) == -2
    assert fold_error(3, D, 2) is None
    assert fold_error(-3, D, 2) is None
    assert fold_error(3, D, 3) == 3
    assert fold_error(-3, D, 3) == -3
    assert fold_error(4, D, 3) is None


def test_fold_error_compact_domain() -> None:
    # D == q == 3, k == 1: every residue lands in support.
    assert fold_error(0, 3, 1) == 0
    assert fold_error(1, 3, 1) == 1
    assert fold_error(2, 3, 1) == -1
    assert fold_error(-1, 3, 1) == -1
    assert fold_error(-2, 3, 1) == 1


def test_fold_error_rejects_bad_domain() -> None:
    with pytest.raises(ValueError):
        fold_error(0, 0, 1)
    with pytest.raises(ValueError):
        fold_error(0, -5, 1)


def test_pure_arithmetic_ternary_entropy() -> None:
    # Landed T2-1M row of G1_TERNARY.md, used as pure arithmetic对照.
    p0, p_plus, p_minus_abs = 0.76243, 0.23619, 0.001379
    assert abs((p0 + p_plus + p_minus_abs) - 1.0) < 1e-6
    h = -(p0 * math.log2(p0) + p_plus * math.log2(p_plus)
          + p_minus_abs * math.log2(p_minus_abs))
    assert h == pytest.approx(0.8032, abs=1e-3)


def test_params_k1_matches_g1_ternary() -> None:
    # p = P(e != 0), p_minus = absolute P(e = -1) (PM_ABS口径): the k=1
    # construction must reproduce the G-1 ternary entropy magnitude.
    q, h_q, ideal_bps = params_from_stats(
        support=[-1, 0, 1], p=0.23757, p_minus=0.001379, k=1)
    assert q == 3
    assert h_q == pytest.approx(0.8032, abs=1e-3)
    assert ideal_bps == h_q


def test_params_k2_k3_smoke() -> None:
    q2, h2, ideal2 = params_from_stats(
        support=[-2, -1, 0, 1, 2], p=0.25, p_minus=0.002, k=2)
    assert q2 == 5
    assert 0.0 < h2 < math.log2(5)
    assert ideal2 == h2
    q3, h3, ideal3 = params_from_stats(
        support=[-3, -2, -1, 0, 1, 2, 3], p=0.25, p_minus=0.002, k=3)
    assert q3 == 7
    assert 0.0 < h3 < math.log2(7)
    assert ideal3 == h3


def test_params_rest_listed_separately() -> None:
    # Out-of-support tail mass is its own entropy outcome, not merged.
    _, h_norest, _ = params_from_stats(
        support=[-1, 0, 1], p=0.23757, p_minus=0.001379, k=1)
    q, h_rest, ideal = params_from_stats(
        support=[-1, 0, 1], p=0.23757, p_minus=0.001379, k=1, rest=0.01)
    assert q == 3
    assert ideal == h_rest
    assert h_rest != pytest.approx(h_norest)
    assert 0.0 < h_rest < math.log2(4)


def test_params_rejects_inconsistent_inputs() -> None:
    with pytest.raises(ValueError):  # p_minus above p
        params_from_stats(support=[-1, 0, 1], p=0.1, p_minus=0.2, k=1)
    with pytest.raises(ValueError):  # p + rest above 1
        params_from_stats(
            support=[-1, 0, 1], p=0.9, p_minus=0.01, k=1, rest=0.2)
    with pytest.raises(ValueError):  # support mismatch
        params_from_stats(support=[-1, 0, 1], p=0.1, p_minus=0.01, k=2)
    with pytest.raises(ValueError):  # negative p
        params_from_stats(support=[-1, 0, 1], p=-0.1, p_minus=0.0, k=1)
