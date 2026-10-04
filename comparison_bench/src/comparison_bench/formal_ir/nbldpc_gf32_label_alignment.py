"""Fixed-support GF(32) label alignment for the frozen L1 probe.

The candidate is ``H0 D`` for a nonzero diagonal column scaling ``D``.  Its
support, rank, and column-equivalence class are checked against ``H0``; this
module does not build graphs or call a decoder.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout

Q = 32
POLY = 37
WIDTH = 128
GRAPH_SEEDS = tuple(layout.GRAPH_SEEDS[WIDTH])
PMF_P0S = (0.20, 0.25, 0.30)
TIE_TOL = 1e-12
MIN_SCORE_GAIN = 1e-10

_MUL = np.asarray(
    [[layout.gf32_mul(a, b) for b in range(Q)] for a in range(Q)],
    dtype=np.int64,
)

__all__ = [
    "Q", "POLY", "WIDTH", "GRAPH_SEEDS", "PMF_P0S", "TIE_TOL",
    "MIN_SCORE_GAIN", "pmf_grid", "validate_pmf", "entropy_bits",
    "xor_convolve", "scale_pmf", "check_sum_pmf", "marginal_score",
    "choose_label", "scale_columns", "column_inverse", "align_labels",
    "verify_t0",
]


def validate_pmf(pmf: Any) -> np.ndarray:
    """Return one normalized, finite 32-symbol PMF as float64."""
    p = np.asarray(pmf, dtype=np.float64)
    if p.shape != (Q,) or not np.all(np.isfinite(p)) or np.any(p < 0):
        raise ValueError("GF(32) PMF must be a finite nonnegative length-32 vector")
    if not np.isclose(float(p.sum()), 1.0, rtol=0.0, atol=1e-12):
        raise ValueError("GF(32) PMF must sum to one")
    return p.copy()


def pmf_grid() -> list[dict[str, Any]]:
    """Frozen synthetic additive-error PMFs, in preregistered order."""
    rows = []
    for index, p0 in enumerate(PMF_P0S):
        p = np.full(Q, (0.90 - p0) / 30.0, dtype=np.float64)
        p[0] = p0
        p[1] = 0.10
        p = validate_pmf(p)
        rows.append({
            "index": index,
            "p0": p0,
            "p1": 0.10,
            "p2_to_31_each": (0.90 - p0) / 30.0,
            "formula": ("p[0]=%.2f; p[1]=0.10; "
                        "p[2..31]=(0.90-%.2f)/30" % (p0, p0)),
            "entropy_bits": entropy_bits(p),
            "pmf": p,
        })
    return rows


def entropy_bits(pmf: Any) -> float:
    """Shannon entropy in bits for a 32-symbol distribution."""
    p = validate_pmf(pmf)
    nonzero = p > 0
    return float(-np.sum(p[nonzero] * np.log2(p[nonzero])))


def xor_convolve(left: Any, right: Any) -> np.ndarray:
    """Convolve two GF(32) symbol distributions under XOR addition."""
    a = validate_pmf(left)
    b = validate_pmf(right)
    out = np.zeros(Q, dtype=np.float64)
    for x, mass in enumerate(a):
        if mass:
            out[np.arange(Q) ^ x] += mass * b
    return out


def scale_pmf(pmf: Any, coefficient: int) -> np.ndarray:
    """Distribution of ``coefficient * E`` over the pinned GF(32) field."""
    p = validate_pmf(pmf)
    c = int(coefficient)
    if c < 1 or c >= Q:
        raise ValueError("edge coefficient must be nonzero in GF(32)")
    out = np.zeros(Q, dtype=np.float64)
    out[_MUL[c]] = p
    return out


def check_sum_pmf(pmf: Any, coefficients: Sequence[int]) -> np.ndarray:
    """Distribution of the XOR sum of independent labelled errors."""
    p = validate_pmf(pmf)
    out = np.zeros(Q, dtype=np.float64)
    out[0] = 1.0
    for coefficient in coefficients:
        out = xor_convolve(out, scale_pmf(p, int(coefficient)))
    return out


def _matrix(dense: Any) -> np.ndarray:
    h = np.asarray(dense, dtype=np.int64)
    if h.ndim != 2 or h.size == 0:
        raise ValueError("GF(32) parity-check matrix must be nonempty and 2-D")
    if np.any(h < 0) or np.any(h >= Q):
        raise ValueError("GF(32) matrix entries must be in 0..31")
    return h


def marginal_score(dense: Any, pmf: Any) -> tuple[float, list[np.ndarray]]:
    """Sum check-marginal entropies ``J(H,p)`` and return each marginal."""
    h = _matrix(dense)
    p = validate_pmf(pmf)
    distributions = []
    for row in h:
        coefficients = row[row != 0].tolist()
        distributions.append(check_sum_pmf(p, coefficients))
    return float(sum(entropy_bits(dist) for dist in distributions)), distributions


def choose_label(scores: Sequence[tuple[int, float]], current: int,
                 tolerance: float = TIE_TOL) -> int:
    """Choose a maximum score; preserve current on a tolerance tie."""
    if not scores:
        raise ValueError("at least one candidate label is required")
    best = max(float(score) for _, score in scores)
    tied = [int(label) for label, score in scores
            if best - float(score) <= float(tolerance)]
    if int(current) in tied:
        return int(current)
    return min(tied)


def scale_columns(dense: Any, labels: Sequence[int]) -> np.ndarray:
    """Return ``H D`` by multiplying each column by its nonzero label."""
    h = _matrix(dense)
    d = np.asarray(labels, dtype=np.int64)
    if d.shape != (h.shape[1],) or np.any(d < 1) or np.any(d >= Q):
        raise ValueError("one nonzero GF(32) label is required per column")
    return np.where(h != 0, _MUL[h, d[None, :]], 0).astype(np.int64)


def column_inverse(labels: Sequence[int]) -> np.ndarray:
    """Return multiplicative inverses of a vector of nonzero field labels."""
    d = np.asarray(labels, dtype=np.int64)
    if d.ndim != 1 or np.any(d < 1) or np.any(d >= Q):
        raise ValueError("labels must be a vector of nonzero GF(32) elements")
    inverse = np.empty_like(d)
    for index, value in enumerate(d):
        matches = np.flatnonzero(_MUL[int(value)] == 1)
        if matches.size != 1:
            raise ArithmeticError("GF(32) inverse table is not unique")
        inverse[index] = int(matches[0])
    return inverse


def align_labels(dense: Any, pmf: Any) -> dict[str, Any]:
    """Apply one frozen coordinate pass over columns 0..n-1.

    Only checks adjacent to the current column are rescored for each trial
    label. A tolerance tie retains the current label; otherwise the smallest
    tied label wins. There are no restarts or decoder-dependent choices.
    """
    h = _matrix(dense)
    p = validate_pmf(pmf)
    m, n = h.shape
    labels = np.ones(n, dtype=np.int64)
    rows_by_column = [np.flatnonzero(h[:, v]).tolist() for v in range(n)]
    columns_by_row = [np.flatnonzero(h[r]).tolist() for r in range(m)]
    transformed = np.zeros((Q, Q), dtype=np.float64)
    for coefficient in range(1, Q):
        transformed[coefficient, _MUL[coefficient]] = p

    def row_distribution(row: int, override_col: int = -1,
                         override_label: int = 1) -> np.ndarray:
        dist = np.zeros(Q, dtype=np.float64)
        dist[0] = 1.0
        for col in columns_by_row[row]:
            label = override_label if col == override_col else int(labels[col])
            coefficient = int(_MUL[int(h[row, col]), label])
            dist = xor_convolve(dist, transformed[coefficient])
        return dist

    row_pmfs = [row_distribution(r) for r in range(m)]
    row_entropies = np.asarray([entropy_bits(q) for q in row_pmfs],
                               dtype=np.float64)
    initial_score = float(row_entropies.sum())

    for column in range(n):
        adjacent = rows_by_column[column]
        if not adjacent:
            continue
        trial_scores = []
        for beta in range(1, Q):
            score = 0.0
            for row in adjacent:
                score += entropy_bits(row_distribution(row, column, beta))
            trial_scores.append((beta, score))
        selected = choose_label(trial_scores, int(labels[column]))
        if selected != int(labels[column]):
            labels[column] = selected
            for row in adjacent:
                row_pmfs[row] = row_distribution(row)
                row_entropies[row] = entropy_bits(row_pmfs[row])

    candidate = scale_columns(h, labels)
    final_score, final_pmfs = marginal_score(candidate, p)
    base_rank = int(layout.gf32_row_rank(h))
    candidate_rank = int(layout.gf32_row_rank(candidate))
    support_equal = bool(np.array_equal(h != 0, candidate != 0))
    gauge_back = scale_columns(candidate, column_inverse(labels))
    gauge_equal = bool(np.array_equal(gauge_back, h))
    return {
        "labels": labels,
        "candidate": candidate,
        "J0": initial_score,
        "Jc": final_score,
        "baseline_rank": base_rank,
        "candidate_rank": candidate_rank,
        "support_equal": support_equal,
        "gauge_equal": gauge_equal,
        "nontrivial": bool(np.any(labels != 1)),
        "candidate_admitted": bool(
            np.any(labels != 1) and final_score > initial_score + MIN_SCORE_GAIN
            and support_equal and base_rank == candidate_rank and gauge_equal),
        "check_entropies": [entropy_bits(q) for q in final_pmfs],
    }


def verify_t0() -> dict[str, bool]:
    """Run deterministic arithmetic checks only; no graph construction or decode."""
    if (layout.gf32_mul(2, 2) != 4 or layout.gf32_mul(2, 16) != 5
            or any(layout.gf32_mul(a, 1) != a for a in range(Q))
            or any(layout.gf32_mul(a, 0) != 0 for a in range(Q))):
        raise AssertionError("GF(32)/polynomial-37 multiplication check failed")
    for a in range(1, Q):
        if not np.any(_MUL[a] == 1):
            raise AssertionError("a nonzero GF(32) element has no inverse")
    for entry in pmf_grid():
        validate_pmf(entry["pmf"])

    sparse = np.zeros(Q, dtype=np.float64)
    sparse[0], sparse[1] = 0.8, 0.2
    same = check_sum_pmf(sparse, (1, 1))
    if not np.isclose(same[0], 0.68) or not np.isclose(same[1], 0.32):
        raise AssertionError("two-edge equal-label example does not match")
    different = check_sum_pmf(sparse, (1, 2))
    expected = np.zeros(Q, dtype=np.float64)
    expected[0], expected[1], expected[2], expected[3] = 0.64, 0.16, 0.16, 0.04
    if not np.allclose(different, expected, rtol=0.0, atol=1e-15):
        raise AssertionError("two-edge unequal-label example does not match")

    qsc = np.full(Q, 0.1 / 31.0, dtype=np.float64)
    qsc[0] = 0.9
    qsc_a = check_sum_pmf(qsc, (1, 2, 3, 31))
    qsc_b = check_sum_pmf(qsc, (4, 8, 9, 17))
    if not np.allclose(qsc_a, qsc_b, rtol=0.0, atol=1e-15):
        raise AssertionError("QSC single-check law changed under relabelling")

    h0 = np.asarray([[1, 2, 0], [3, 0, 5]], dtype=np.int64)
    d = np.asarray([2, 3, 7], dtype=np.int64)
    hc = scale_columns(h0, d)
    restored = scale_columns(hc, column_inverse(d))
    if not np.array_equal(restored, h0):
        raise AssertionError("column scaling gauge did not restore H0")
    if not np.array_equal(h0 != 0, hc != 0):
        raise AssertionError("column scaling changed support")
    if layout.gf32_row_rank(h0) != layout.gf32_row_rank(hc):
        raise AssertionError("column scaling changed GF(32) rank")

    return {
        "field_multiplication": True,
        "field_inverses": True,
        "pmf_normalization": True,
        "two_edge_exact": True,
        "qsc_single_check_invariance": True,
        "column_gauge_rank_support": True,
    }
