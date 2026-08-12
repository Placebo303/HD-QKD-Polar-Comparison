"""V11 paper-faithful SMP density evolution for nonbinary spatially coupled
LDPC ensembles (``formal-nonbinary-ldpc-v11-sc-de-gate``, Stage E, R1
reference reproduction; additive layer, frozen semantics).

Contents
--------

- **Uncoupled SMP-DE** for regular ``(dv, dc)`` ensembles over the q-ary
  symmetric channel, following Lázaro et al. (Globecom 2019, arXiv:1906.02537,
  ref [15] of the AEIT paper): check-node update in closed form (eq. (11)
  summed over ``psi_{j,0}``), extrinsic channel error probability
  ``xi = 1 - s0`` (eq. (12)), and the exact variable-node update (eq. (17))
  evaluated by direct enumeration of the ``dv - 1`` incoming message symbols
  (feasible for the frozen ``dv = 3``; larger ``dv`` is rejected fail-closed).
- **Coupled SMP-DE** for terminated SC-LDPC protographs following Ben Yacoub
  et al. (AEIT 2019, DOI 10.23919/AEIT.2019.8893373): the SC base matrix (3)
  with submatrices ``B_i = (1 ... 1)`` (``m0 x n0``, ``n0 = dc/dv`` VN types
  per spatial position, ``w = dv - 1``; for rate-1/2 ``(3,6)`` this is the
  C^ms=2_[3,6] construction of Wei et al., B0 = B1 = B2 = [1 1]), windowed
  decoding on ``B[1:5W, 1:W]`` with the frozen window ``W = 30``, check
  update (5), variable-node update (6) and a-posteriori update (7).
  Convergence of the window decoder is declared when the probability of a
  correct decision for the VNs in the *first block column* reaches ``1``
  (within ``conv_tol``).
- **Threshold search**: deterministic binary search over the QSC error
  probability ``p`` with search tolerance ``p_tol <= 0.001`` (design.md R1).
- **Reference reproduction**: :func:`reproduce_ben_yacoub_2019` runs the four
  frozen ``(q, mode)`` cases and compares against the published AEIT Tables I
  and II anchors; every case gets a full trace (p value, iteration count,
  convergence decision, threshold, deviation, pass/fail).

Scientific boundaries (frozen)
------------------------------

SMP passes only *symbol estimates* between nodes: every exchanged message is
a single element of GF(q). It is **not** FFT-QSPA and **not** a
full-probability-vector decoder, and the DE here tracks only the scalar
``p0`` (probability that a message is the correct symbol 0) under the
all-zeros-codeword symmetry. This module is a paper-faithful reference
implementation for the V11 R1 gate; **it must not be reused as the GF(1024)
scientific decoder** for the V11 Gate (the full-vector coupled MC-DE of
Stage E is a separate module). The DE is fully deterministic (no RNG): all
probabilities are computed by exact finite enumeration.

Imports: standard library and numpy only. Never imports any V8/V9/V10
module.
"""
from __future__ import annotations

import json
import math
from numbers import Integral
from typing import Any, Mapping

import numpy as np

__all__ = [
    "W_FROZEN",
    "REPRODUCTION_DV",
    "REPRODUCTION_DC",
    "PUBLISHED_THRESHOLDS",
    "REPRODUCTION_TOL",
    "SEARCH_P_TOL",
    "qsc_reliability",
    "check_update_uncoupled",
    "variable_update_uncoupled",
    "run_smp_de_uncoupled",
    "SCWindow",
    "check_update_coupled",
    "variable_update_coupled",
    "app_update_coupled",
    "run_smp_de_coupled",
    "threshold_binary_search",
    "reproduce_ben_yacoub_2019",
]

#: Frozen decoding window (number of spatial block columns), AEIT 2019 Sec. V.
W_FROZEN = 30
#: Frozen regular ensemble for the R1 reference ladder (rate-1/2, (3,6)).
REPRODUCTION_DV = 3
REPRODUCTION_DC = 6
#: Published AEIT 2019 anchors, Tables I and II, ``(q, mode) -> threshold``.
PUBLISHED_THRESHOLDS = {
    (4, "uncoupled"): 0.0890,
    (16, "uncoupled"): 0.1075,
    (4, "coupled"): 0.0942,
    (16, "coupled"): 0.1288,
}
#: Absolute reproduction tolerance for R1 (design.md R1).
REPRODUCTION_TOL = 0.002
#: Threshold-search tolerance (design.md R1: at most .001).
SEARCH_P_TOL = 0.001
#: Probability floor (V10 convention) for log-reliabilities.
_PROB_FLOOR = 1e-300
#: Default DE iteration budget.
_MAX_ITER = 3000
#: Default convergence tolerance for the APP/first-column criterion.
_CONV_TOL = 1e-8


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #


def _qint(q: Any) -> int:
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 \
            or int(q) & (int(q) - 1) or int(q) > 1024:
        raise ValueError("SMP-DE requires a power-of-two GF(q) with 2 <= q <= 1024")
    return int(q)


def qsc_reliability(x: float, q: int) -> float:
    """``D(x) = log((1-x)/(x/(q-1)))`` — the q-SC L-vector weight for an
    extrinsic channel with crossover probability ``x`` (Globecom eq. (2)
    definition of ``D(epsilon)``), floored to keep logs finite."""
    q = _qint(q)
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(float(x)):
        raise ValueError("crossover probability must be finite")
    x = float(x)
    if not 0.0 <= x <= 1.0:
        raise ValueError("crossover probability must be in [0, 1]")
    x = min(max(x, _PROB_FLOOR), 1.0 - _PROB_FLOOR)
    return math.log(1.0 - x) - math.log(x / (q - 1.0))


def _validate_eps(q: int, eps: Any) -> float:
    if isinstance(eps, bool) or not isinstance(eps, (int, float)) \
            or not math.isfinite(float(eps)) or not 0.0 <= float(eps) <= 1.0:
        raise ValueError("QSC error probability must be in [0, 1]")
    return float(eps)


def _validate_dv_dc(q: int, dv: Any, dc: Any) -> tuple[int, int]:
    if isinstance(dv, bool) or not isinstance(dv, Integral) or int(dv) < 2:
        raise ValueError("dv must be an integer >= 2")
    if isinstance(dc, bool) or not isinstance(dc, Integral) or int(dc) < 2:
        raise ValueError("dc must be an integer >= 2")
    dv, dc = int(dv), int(dc)
    if dc % dv != 0:
        raise ValueError("dc must be a multiple of dv for the frozen protograph construction")
    if dv == 3 and dc // dv != 2:
        raise ValueError("exact VN update enumeration is frozen for (3,6) only")
    if dv != 3:
        raise ValueError("exact VN update enumeration is frozen for dv = 3 only")
    return dv, dc


# --------------------------------------------------------------------------- #
# uncoupled SMP-DE (Globecom 2019 [15], eqs. (11)-(17))
# --------------------------------------------------------------------------- #


def check_update_uncoupled(p0: float, dc: int, q: int) -> float:
    """Check-node update, Globecom eq. (11) summed in closed form:
    ``s0 = (1/q)[1 + (q-1) * ((q*p0 - 1)/(q-1))^{dc-1}]`` (probability that a
    check-to-variable message equals the correct symbol 0)."""
    q = _qint(q)
    if isinstance(dc, bool) or not isinstance(dc, Integral) or int(dc) < 2:
        raise ValueError("dc must be an integer >= 2")
    dc = int(dc)
    if isinstance(p0, bool) or not isinstance(p0, (int, float)) or not math.isfinite(float(p0)):
        raise ValueError("p0 must be finite")
    p0 = float(p0)
    if not 0.0 <= p0 <= 1.0:
        raise ValueError("p0 must be in [0, 1]")
    base = (q * p0 - 1.0) / (q - 1.0)
    return (1.0 / q) * (1.0 + (q - 1.0) * base ** (dc - 1))


def variable_update_uncoupled(s0: float, eps: float, dv: int, q: int) -> float:
    """Variable-node update, Globecom eq. (17) evaluated exactly.

    The ``dv - 1`` incoming check messages are enumerated symbol by symbol
    (feasible for the frozen ``dv = 3``, i.e. 2 messages -> ``q^2`` pairs).
    ``E_b = D(xi)*f_b + D(eps)*[b == y]`` with ``xi = 1 - s0``; the result is
    ``sum_y Pr{Y=y} * sum over message pairs of P(pair) * I(0 in argmax E) /
    |argmax E|``.  The sum over ``y`` is folded into two cases (y = 0 with
    weight ``1 - eps``, y != 0 with total weight ``eps``) by channel
    symmetry.
    """
    q = _qint(q)
    dv, _ = _validate_dv_dc(q, dv, 2 * int(dv))
    eps = _validate_eps(q, eps)
    if isinstance(s0, bool) or not isinstance(s0, (int, float)) or not math.isfinite(float(s0)):
        raise ValueError("s0 must be finite")
    s0 = float(s0)
    if not 0.0 <= s0 <= 1.0:
        raise ValueError("s0 must be in [0, 1]")
    xi = 1.0 - s0
    d_xi = qsc_reliability(xi, q)
    d_eps = qsc_reliability(eps, q)
    symbols = np.arange(q)
    m1, m2 = np.meshgrid(symbols, symbols, indexing="ij")
    m1, m2 = m1.ravel(), m2.ravel()
    weight = (np.where(m1 == 0, 1.0 - xi, xi / (q - 1.0))
              * np.where(m2 == 0, 1.0 - xi, xi / (q - 1.0)))
    counts = (m1[:, None] == symbols[None, :]).astype(float) \
        + (m2[:, None] == symbols[None, :]).astype(float)
    terms = []
    for y in (0, 1):
        energy = d_xi * counts + d_eps * (symbols[None, :] == y).astype(float)
        maximum = energy.max(axis=1)
        is_max = energy == maximum[:, None]
        num_max = is_max.sum(axis=1)
        contribution = is_max[:, 0].astype(float) / num_max
        terms.append(float(np.sum(weight * contribution)))
    return (1.0 - eps) * terms[0] + eps * terms[1]


def run_smp_de_uncoupled(q: int, dv: int, dc: int, eps: float, *,
                         max_iter: int = _MAX_ITER, conv_tol: float = _CONV_TOL,
                         streak: int = 5) -> dict[str, Any]:
    """One deterministic uncoupled SMP-DE run (see module docstring).

    The tracked scalar is ``p0`` (probability that a variable-to-check
    message equals the correct symbol 0); the run converges when ``p0``
    exceeds ``1 - conv_tol`` for ``streak`` consecutive iterations (the
    threshold definition of [15] is ``p0 -> 1``)."""
    q = _qint(q)
    dv, dc = _validate_dv_dc(q, dv, dc)
    eps = _validate_eps(q, eps)
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral) or int(max_iter) < 1:
        raise ValueError("max_iter must be a positive integer")
    if isinstance(conv_tol, bool) or not isinstance(conv_tol, (int, float)) \
            or not math.isfinite(float(conv_tol)) or not 0.0 < float(conv_tol) < 1.0:
        raise ValueError("conv_tol must be in (0, 1)")
    if isinstance(streak, bool) or not isinstance(streak, Integral) or int(streak) < 1:
        raise ValueError("streak must be a positive integer")
    max_iter, streak = int(max_iter), int(streak)
    conv_tol = float(conv_tol)
    p0 = 1.0 - eps
    p0_trace: list[float] = []
    s0_trace: list[float] = []
    converged = False
    iterations = 0
    run_streak = 0
    for iteration in range(1, max_iter + 1):
        s0 = check_update_uncoupled(p0, dc, q)
        p0 = variable_update_uncoupled(s0, eps, dv, q)
        p0_trace.append(p0)
        s0_trace.append(s0)
        iterations = iteration
        run_streak = run_streak + 1 if p0 > 1.0 - conv_tol else 0
        if run_streak >= streak:
            converged = True
            break
    return {
        "converged": converged,
        "iterations": iterations,
        "p0_trace": p0_trace,
        "s0_trace": s0_trace,
        "q": q, "dv": dv, "dc": dc, "eps": eps,
        "max_iter": max_iter, "conv_tol": conv_tol, "streak": streak,
    }


# --------------------------------------------------------------------------- #
# coupled SMP-DE (AEIT 2019, eqs. (3)-(7); windowed decoding, W = 30)
# --------------------------------------------------------------------------- #


class SCWindow:
    """Frozen terminated SC-LDPC window protograph ``B[1:5W, 1:W]``.

    Per spatial position there are ``m0 = 1`` check-node type and
    ``n0 = dc/dv`` variable-node types; the SC submatrices are
    ``B_i = (1 ... 1)`` (a row of ``n0`` ones), ``i = 0..w`` with
    ``w = dv - 1`` (for rate-1/2 ``(3,6)``: the Wei et al. C^ms=2_[3,6]
    construction B0 = B1 = B2 = [1 1]).  The window takes the first ``5W``
    block rows and the first ``W`` block columns of the terminated SC base
    matrix (AEIT Sec. V).  Check row ``r`` connects to VN column ``c`` iff
    ``0 <= r - c <= w`` (both VN subtypes), matching eq. (3).

    The per-column variable-node and first-column a-posteriori enumeration
    grids are precomputed once so a threshold bisection reuses them.
    """

    def __init__(self, q: int, dv: int, dc: int, W: int = W_FROZEN):
        q = _qint(q)
        dv, dc = _validate_dv_dc(q, dv, dc)
        if isinstance(W, bool) or not isinstance(W, Integral) or int(W) < 1:
            raise ValueError("W must be a positive integer")
        W = int(W)
        self.q = q
        self.dv = dv
        self.dc = dc
        self.W = W
        self.n0 = dc // dv
        self.w = dv - 1
        self.rows = 5 * W
        self.edges: list[tuple[int, int]] = []
        self.by_check: dict[int, list[int]] = {}
        self.by_vn: dict[int, list[int]] = {}
        for r in range(1, self.rows + 1):
            for c in range(1, W + 1):
                if 0 <= r - c <= self.w:
                    self.edges.append((r, c))
                    self.by_check.setdefault(r, []).append(c)
                    self.by_vn.setdefault(c, []).append(r)
        self.edges.sort()
        symbols = np.arange(q)
        self._vn_grids: dict[tuple[int, int], tuple[np.ndarray, list[int]]] = {}
        for c, checks in self.by_vn.items():
            for r in checks:
                others = [e for e in checks if e != r]
                grid = np.array(np.meshgrid(*([symbols] * len(others)),
                                            indexing="ij")).reshape(len(others), -1).T
                self._vn_grids[(r, c)] = (grid, others)
        self._app_grids: dict[int, tuple[np.ndarray, list[int]]] = {}
        for c, checks in self.by_vn.items():
            if c != 1:
                continue
            grid = np.array(np.meshgrid(*([symbols] * len(checks)),
                                        indexing="ij")).reshape(len(checks), -1).T
            self._app_grids[c] = (grid, checks)
        self._first_column = [c for c in self.by_vn if c == 1]

    # -- check-node update, AEIT eq. (5) -------------------------------- #

    def check_update(self, p0_map: Mapping[tuple[int, int], float]) -> dict[tuple[int, int], float]:
        """``s0(r, c) = (1/q)[1 + (q-1) * A(r,c) * prod_{c' != c} A(r,c')^2]``
        with ``A(r,c') = (q*p0(r,c') - 1)/(q-1)``; the square accounts for
        the two VN subtypes at column ``c'`` and the bare factor for the
        target column's second subtype (b_{i,e} = 1, exponent 1 - delta)."""
        q = self.q
        out: dict[tuple[int, int], float] = {}
        for r, cols in self.by_check.items():
            A = {c: (q * p0_map[(r, c)] - 1.0) / (q - 1.0) for c in cols}
            for c in cols:
                prod = 1.0
                for c2 in cols:
                    if c2 == c:
                        continue
                    prod *= A[c2] * A[c2]
                out[(r, c)] = (1.0 / q) * (1.0 + (q - 1.0) * A[c] * prod)
        return out

    # -- variable-node update, AEIT eq. (6) ------------------------------ #

    def variable_update(self, s0_map: Mapping[tuple[int, int], float], eps: float,
                        ) -> dict[tuple[int, int], float]:
        """Exact ``p0(r, c)`` by enumerating the symbols of the ``dv - 1``
        incoming messages (all incident checks except the target ``r``);
        ``E_u = D(eps)[u = y] + sum_e D(xi(e,c)) [m_e = u]``."""
        q = self.q
        symbols = np.arange(q)
        d_eps = qsc_reliability(eps, q)
        out: dict[tuple[int, int], float] = {}
        for c, checks in self.by_vn.items():
            xi = {e: 1.0 - s0_map[(e, c)] for e in checks}
            d_xi = {e: qsc_reliability(x, q) for e, x in xi.items()}
            for r in checks:
                grid, others = self._vn_grids[(r, c)]
                weight = np.ones(grid.shape[0])
                energy = np.zeros((grid.shape[0], q))
                for idx, e in enumerate(others):
                    sym = grid[:, idx]
                    weight *= np.where(sym == 0, s0_map[(e, c)], xi[e] / (q - 1.0))
                    energy += d_xi[e] * (symbols[None, :] == sym[:, None]).astype(float)
                terms = []
                for y in (0, 1):
                    total = energy + d_eps * (symbols[None, :] == y).astype(float)
                    maximum = total.max(axis=1)
                    is_max = total == maximum[:, None]
                    num_max = is_max.sum(axis=1)
                    contribution = is_max[:, 0].astype(float) / num_max
                    terms.append(float(np.sum(weight * contribution)))
                out[(r, c)] = (1.0 - eps) * terms[0] + eps * terms[1]
        return out

    # -- a-posteriori update, AEIT eq. (7), first block column ----------- #

    def app_first_column(self, s0_map: Mapping[tuple[int, int], float], eps: float,
                         ) -> dict[int, float]:
        """Probability of a correct decision for every VN type in the first
        block column (window-decoder convergence criterion)."""
        q = self.q
        symbols = np.arange(q)
        d_eps = qsc_reliability(eps, q)
        out: dict[int, float] = {}
        for c in self._first_column:
            grid, checks = self._app_grids[c]
            weight = np.ones(grid.shape[0])
            energy = np.zeros((grid.shape[0], q))
            for idx, e in enumerate(checks):
                sym = grid[:, idx]
                s_e = s0_map[(e, c)]
                weight *= np.where(sym == 0, s_e, (1.0 - s_e) / (q - 1.0))
                energy += qsc_reliability(1.0 - s_e, q) * \
                    (symbols[None, :] == sym[:, None]).astype(float)
            terms = []
            for y in (0, 1):
                total = energy + d_eps * (symbols[None, :] == y).astype(float)
                maximum = total.max(axis=1)
                is_max = total == maximum[:, None]
                num_max = is_max.sum(axis=1)
                contribution = is_max[:, 0].astype(float) / num_max
                terms.append(float(np.sum(weight * contribution)))
            out[c] = (1.0 - eps) * terms[0] + eps * terms[1]
        return out


def run_smp_de_coupled(q: int, dv: int, dc: int, eps: float, *,
                       W: int = W_FROZEN, max_iter: int = _MAX_ITER,
                       conv_tol: float = _CONV_TOL, streak: int = 5) -> dict[str, Any]:
    """One deterministic coupled windowed SMP-DE run (AEIT 2019 Sec. IV-V).

    Converges when the minimum correct-decision probability over the first
    block column exceeds ``1 - conv_tol`` for ``streak`` consecutive
    iterations (the window-decoder convergence criterion of the paper)."""
    q = _qint(q)
    dv, dc = _validate_dv_dc(q, dv, dc)
    eps = _validate_eps(q, eps)
    if isinstance(W, bool) or not isinstance(W, Integral) or int(W) < 1:
        raise ValueError("W must be a positive integer")
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral) or int(max_iter) < 1:
        raise ValueError("max_iter must be a positive integer")
    if isinstance(conv_tol, bool) or not isinstance(conv_tol, (int, float)) \
            or not math.isfinite(float(conv_tol)) or not 0.0 < float(conv_tol) < 1.0:
        raise ValueError("conv_tol must be in (0, 1)")
    if isinstance(streak, bool) or not isinstance(streak, Integral) or int(streak) < 1:
        raise ValueError("streak must be a positive integer")
    W, max_iter, streak = int(W), int(max_iter), int(streak)
    conv_tol = float(conv_tol)
    window = SCWindow(q, dv, dc, W=W)
    p0_map = {edge: 1.0 - eps for edge in window.edges}
    app_trace: list[float] = []
    converged = False
    iterations = 0
    run_streak = 0
    for iteration in range(1, max_iter + 1):
        s0_map = window.check_update(p0_map)
        p0_map = window.variable_update(s0_map, eps)
        app = window.app_first_column(s0_map, eps)
        value = min(app.values())
        app_trace.append(value)
        iterations = iteration
        run_streak = run_streak + 1 if value > 1.0 - conv_tol else 0
        if run_streak >= streak:
            converged = True
            break
    return {
        "converged": converged,
        "iterations": iterations,
        "app_trace": app_trace,
        "q": q, "dv": dv, "dc": dc, "eps": eps, "W": W,
        "max_iter": max_iter, "conv_tol": conv_tol, "streak": streak,
    }


# --------------------------------------------------------------------------- #
# threshold search and reference reproduction
# --------------------------------------------------------------------------- #


def threshold_binary_search(q: int, dv: int, dc: int, mode: str, *,
                            W: int = W_FROZEN, p_lo: float = 0.01,
                            p_hi: float | None = None, p_tol: float = SEARCH_P_TOL,
                            max_iter: int = _MAX_ITER, conv_tol: float = _CONV_TOL,
                            streak: int = 5) -> dict[str, Any]:
    """Deterministic binary search for the largest ``p`` at which the SMP-DE
    converges (the iterative decoding threshold proxy).

    ``mode`` is ``"uncoupled"`` or ``"coupled"``.  The returned
    ``threshold_proxy`` is the converged lower bound of the last bisection
    bracket (deterministic, reproducible)."""
    q = _qint(q)
    dv, dc = _validate_dv_dc(q, dv, dc)
    if mode not in ("uncoupled", "coupled"):
        raise ValueError("mode must be 'uncoupled' or 'coupled'")
    if isinstance(p_lo, bool) or not isinstance(p_lo, (int, float)) \
            or not math.isfinite(float(p_lo)) or not 0.0 < float(p_lo) < 1.0:
        raise ValueError("p_lo must be in (0, 1)")
    if p_hi is None:
        p_hi = 0.5 * (q - 1.0) / q
    if isinstance(p_hi, bool) or not isinstance(p_hi, (int, float)) \
            or not math.isfinite(float(p_hi)) or not 0.0 < float(p_hi) < 1.0:
        raise ValueError("p_hi must be in (0, 1)")
    if isinstance(p_tol, bool) or not isinstance(p_tol, (int, float)) \
            or not math.isfinite(float(p_tol)) or float(p_tol) <= 0.0:
        raise ValueError("p_tol must be positive and finite")
    if not float(p_lo) < float(p_hi):
        raise ValueError("p_lo must be < p_hi")
    lo, hi = float(p_lo), float(p_hi)
    probes: list[dict[str, Any]] = []
    converged_at_lo: bool | None = None
    while hi - lo > float(p_tol):
        mid = (lo + hi) / 2.0
        if mode == "uncoupled":
            result = run_smp_de_uncoupled(q, dv, dc, mid, max_iter=max_iter,
                                          conv_tol=conv_tol, streak=streak)
        else:
            result = run_smp_de_coupled(q, dv, dc, mid, W=W, max_iter=max_iter,
                                        conv_tol=conv_tol, streak=streak)
        probes.append({"p": mid, "converged": result["converged"],
                       "iterations": result["iterations"]})
        if result["converged"]:
            lo = mid
            converged_at_lo = True
        else:
            hi = mid
            converged_at_lo = False
    return {"threshold_proxy": (lo + hi) / 2.0, "p_lo": lo, "p_hi": hi,
            "p_tol": float(p_tol), "probes": probes,
            "converged_at_lo": converged_at_lo}


def reproduce_ben_yacoub_2019(*, dv: int = REPRODUCTION_DV, dc: int = REPRODUCTION_DC,
                              W: int = W_FROZEN, p_tol: float = SEARCH_P_TOL,
                              max_iter: int = _MAX_ITER, conv_tol: float = _CONV_TOL,
                              streak: int = 5,
                              include_traces: bool = True) -> dict[str, Any]:
    """Run the four frozen ``(q, mode)`` reference cases and grade them
    against the published AEIT 2019 anchors (Tables I and II).

    Every case carries its full trace (per-iteration ``p0`` or first-column
    APP), the threshold search probes, the reproduced threshold, the
    deviation from the published anchor and a pass/fail flag against
    ``REPRODUCTION_TOL = 0.002``.  The overall status is ``reproduce_pass``
    only if all four cases pass."""
    cases: list[dict[str, Any]] = []
    overall_pass = True
    for (q, mode), published in sorted(PUBLISHED_THRESHOLDS.items()):
        search = threshold_binary_search(q, dv, dc, mode, W=W, p_tol=p_tol,
                                         max_iter=max_iter, conv_tol=conv_tol,
                                         streak=streak)
        reproduced = float(search["threshold_proxy"])
        deviation = abs(reproduced - published)
        passed = deviation <= REPRODUCTION_TOL
        overall_pass = overall_pass and passed
        case: dict[str, Any] = {
            "q": q, "mode": mode, "dv": dv, "dc": dc, "W": W,
            "published": published, "reproduced": reproduced,
            "deviation": deviation, "pass": passed,
            "search": search,
        }
        if include_traces:
            # Trace at the last verified-converged search bound (p_lo): a run
            # exactly at the threshold midpoint is dominated by critical
            # slowing down and may exhaust the iteration budget, which would
            # make the trace itself misleading.
            eps = float(search["p_lo"])
            if mode == "uncoupled":
                case["trace"] = run_smp_de_uncoupled(q, dv, dc, eps, max_iter=max_iter,
                                                     conv_tol=conv_tol, streak=streak)
            else:
                case["trace"] = run_smp_de_coupled(q, dv, dc, eps, W=W,
                                                   max_iter=max_iter, conv_tol=conv_tol,
                                                   streak=streak)
        cases.append(case)
    return {
        "schema": "v11_smp_de_reproduction_v1",
        "status": "reproduce_pass" if overall_pass else "failed_reference",
        "reproduction_tol": REPRODUCTION_TOL,
        "search_p_tol": SEARCH_P_TOL,
        "dv": dv, "dc": dc, "W": W,
        "cases": cases,
    }


# --------------------------------------------------------------------------- #
# module self-check
# --------------------------------------------------------------------------- #


def _self_check() -> None:
    """Run the four frozen reproductions and require ``reproduce_pass``."""
    result = reproduce_ben_yacoub_2019(include_traces=False)
    print(json.dumps({key: value for key, value in result.items() if key != "cases"},
                     indent=2, sort_keys=True))
    for case in result["cases"]:
        print(f"q={case['q']} {case['mode']:9s} reproduced={case['reproduced']:.4f} "
              f"published={case['published']:.4f} dev={case['deviation']:.6f} "
              f"pass={case['pass']}")
    if result["status"] != "reproduce_pass":
        raise SystemExit(f"self-check failed: {result['status']}")


if __name__ == "__main__":
    _self_check()
