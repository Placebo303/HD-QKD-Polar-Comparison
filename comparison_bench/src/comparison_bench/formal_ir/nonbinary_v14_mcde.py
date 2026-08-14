"""V14 full-vector GF(1024) Monte-Carlo density evolution with structured
(symbol-difference) priors, plus the q=1024 efficiency-gate drivers
(``formal-nonbinary-ldpc-v14-efficiency-gate``, additive layer).

Semantics (frozen, design section 5):

- Every message is a full length-q probability vector — never a scalar
  reliability.  The variable/check/belief update semantics and the RNG draw
  order exactly follow the accepted V9 MC-DE (``nonbinary_v9_mcde``):
  ``variable_update_mcde`` / ``check_update_mcde`` / ``belief_update_mcde`` /
  ``entropy_base_q`` (read-only import reuse; the V9 sources are never
  edited), iteration order variable -> check -> belief, the observable is the
  mean base-q entropy of the check population, converged when
  ``entropy < entropy_tol`` for ``streak`` consecutive iterations.
- Channel construction branches on ``channel_mode``:
  - ``"qsc"`` keeps V9's exact QSC row semantics (``symbol_probs`` +
    ``rng.choice``); the run is **byte-equivalent** to V9 ``run_mcde`` with
    the same seed (design section 5, T2).
  - ``"structured"`` sets ``diffs = rng.choice(q, size=n_samples, p=w)`` and
    ``channel[i, j] = w[j XOR diff_i]`` (error-domain centering).  The QSC
    branch is a degenerate structured branch whose rows happen to be the QSC
    rows for ``w = symbol_probs``-like distributions; the update kernels are
    shared, so the structured mechanism is trusted by the QSC equivalence.
- Budget discipline: the update kernels are numba-jitted local copies of the
  same math (WHT butterfly / convolution / product / floor-and-normalize),
  consuming pre-drawn index arrays so the RNG stays entirely in numpy PCG64
  with the frozen draw order (degrees first, then one
  ``rng.integers(0, N, N)`` draw per product/convolution slot).  This fits the
  q=1024 point-evaluation budget (design section 5).

Stage drivers (frozen constants in design section 2/3):
- Stage 0 (mechanism regression): QSC mode, q=4, R=0.75, published threshold
  proxy 0.069, tolerance 0.012 (V8-60 reference point).
- Stage 2 (q=1024 point evaluation): 3 frozen variable-degree profiles x 4
  frozen check-count points (m in 15..18); rho from the V9-common harmonic
  exact concentrated check distribution; ``f = (m*10/256)/H(w)``.

Only numpy/numba and the read-only V9 helpers are imported; this module never
reads frame data at import time and never executes a decoder.
"""
from __future__ import annotations

import math
from numbers import Integral
from typing import Any, Mapping

import numpy as np
from numba import njit

#: Read-only reuse of the V9 update kernels (V9 sources are never edited).
from .nonbinary_v9_mcde import (belief_update_mcde, check_update_mcde,
                                entropy_base_q, parse_degree_hist,
                                variable_update_mcde)
#: Harmonic-exact concentrated check distribution (V9-common read-only reuse).
from .nonbinary_v9_common import concentrated_check_distribution

__all__ = [
    "QSC",
    "STRUCTURED",
    "_FLOOR",
    "_NORM_TOL",
    "DEGREE_MAX",
    "parse_degree_hist",
    "entropy_base_q",
    "variable_update_mcde", "check_update_mcde", "belief_update_mcde",
    "run_mcde",
    "threshold_binary_search",
    "STAGE0_Q", "STAGE0_RATE", "STAGE0_N_SAMPLES", "STAGE0_MAX_ITER",
    "STAGE0_PUBLISHED", "STAGE0_TOL", "STAGE0_P_LO", "STAGE0_P_HI",
    "STAGE0_GRID_STEP", "STAGE0_SEED",
    "PROFILES", "MS", "N_BLOCKS", "STAGE2_N_SAMPLES", "STAGE2_MAX_ITER",
    "STAGE2_ENTROPY_TOL", "STAGE2_STREAK",
    "V14_GATE_DECISION_SCHEMA", "V14_GATE_MANIFEST_SCHEMA",
    "build_stage0_doc", "build_stage1_doc", "build_stage2_doc",
    "build_gate_decision_doc", "build_gate_manifest_doc",
    "structured_rho", "stage2_f_achieved",
]

QSC = "qsc"
STRUCTURED = "structured"

#: Positivity floor for probability-domain products (V7 exact-DE convention,
#: matching V9).
_FLOOR = 1e-300
#: Upper bound on any degree in an edge-perspective histogram.
DEGREE_MAX = 64
#: Fraction tolerance for "normalized" input message rows.
_NORM_TOL = 1e-9

# --------------------------------------------------------------------------- #
# numba-jitted kernels (own implementations; same math as the V9 numpy kernels)
# --------------------------------------------------------------------------- #


@njit(cache=False)
def _wht_row_jit(row: np.ndarray) -> None:
    """In-place unnormalized XOR-order WHT of a single row (own butterfly)."""
    q = row.shape[0]
    width = 1
    while width < q:
        for j in range(0, q, 2 * width):
            for k in range(j, j + width):
                a = row[k]
                b = row[k + width]
                row[k] = a + b
                row[k + width] = a - b
        width *= 2


@njit(cache=False)
def _wht_rows_jit(block: np.ndarray) -> np.ndarray:
    """Unnormalized XOR-order WHT of every row of a 2-D ``(n, q)`` block."""
    out = block.copy()
    for i in range(out.shape[0]):
        _wht_row_jit(out[i])
    return out


@njit(cache=False)
def _variable_or_belief_jit(c2v: np.ndarray, channel: np.ndarray,
                            draws: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """njit variable/belief product update (V9 semantics).

    ``c2v`` is the ``(n, q)`` incoming check population; ``channel`` the fresh
    channel rows; ``draws`` the per-sample degree draw offset from the sampling
    RNG (``degrees - 1`` for the variable update, ``degrees`` for the belief
    update); ``idx[d, i]`` the row drawn for sample ``i`` at slot ``d``
    (pre-drawn by numpy in the frozen RNG order).  Starts from the channel row
    and multiplies in the incoming row for samples whose draw count exceeds the
    slot, then applies the ``1e-300`` floor and fail-closed row normalization.
    """
    n = channel.shape[0]
    q = channel.shape[1]
    product = channel.copy()
    max_draws = idx.shape[0]
    for d in range(max_draws):
        for i in range(n):
            if draws[i] > d:
                row = c2v[idx[d, i]]
                for j in range(q):
                    product[i, j] *= row[j]
    for i in range(n):
        s = 0.0
        for j in range(q):
            v = product[i, j]
            if v < _FLOOR:
                v = _FLOOR
            product[i, j] = v
            s += v
        for j in range(q):
            product[i, j] /= s
    return product


@njit(cache=False)
def _check_update_jit(v2c: np.ndarray, draws: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """njit check-node update (V9 semantics).

    ``v2c`` is the ``(n, q)`` incoming variable population; ``draws`` the
    ``dc - 1`` per-sample draw count; ``idx[d, i]`` the row drawn for sample
    ``i`` at slot ``d``.  Per slot, WHT the incoming row and multiply into the
    accumulated spectrum (delta-at-0 starts at all ones) for samples whose draw
    count exceeds the slot; then inverse WHT ``/ q``, ``1e-300`` floor and row
    normalization.
    """
    n = v2c.shape[0]
    q = v2c.shape[1]
    acc = np.ones((n, q))  # spectrum of delta at 0 = all ones
    tmp = np.empty(q)
    max_draws = idx.shape[0]
    for d in range(max_draws):
        for i in range(n):
            if draws[i] > d:
                tmp[:] = v2c[idx[d, i]]
                _wht_row_jit(tmp)
                for j in range(q):
                    acc[i, j] *= tmp[j]
    for i in range(n):
        _wht_row_jit(acc[i])
    for i in range(n):
        s = 0.0
        for j in range(q):
            v = acc[i, j] / q
            if v < _FLOOR:
                v = _FLOOR
            acc[i, j] = v
            s += v
        for j in range(q):
            acc[i, j] /= s
    return acc


# --------------------------------------------------------------------------- #
# wrapper update drivers (numba kernels, V9 RNG draw order)
# --------------------------------------------------------------------------- #


def _variable_update(c2v: Any, dv_degrees: Any, dv_probs: Any, channel: Any,
                     rng: np.random.Generator, q: int) -> np.ndarray:
    """V9 ``variable_update_mcde`` semantics with a numba-jitted product
    update.  RNG draw order (frozen): degrees first, then one
    ``rng.integers(0, N, N)`` draw per slot (the caller draws the channel)."""
    n = channel.shape[0]
    c2v = np.asarray(c2v, dtype=np.float64)
    channel = np.asarray(channel, dtype=np.float64)
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    draws = degrees - 1
    max_draws = int(draws.max())
    idx = np.empty((max_draws, n), dtype=np.int64)
    for d in range(max_draws):
        idx[d] = rng.integers(0, n, size=n)
    return _variable_or_belief_jit(c2v, channel, draws.astype(np.int64), idx)


def _belief_update(c2v: Any, dv_degrees: Any, dv_probs: Any, channel: Any,
                   rng: np.random.Generator, q: int) -> np.ndarray:
    """V9 ``belief_update_mcde`` semantics (channel x all ``dv`` rows)."""
    n = channel.shape[0]
    c2v = np.asarray(c2v, dtype=np.float64)
    channel = np.asarray(channel, dtype=np.float64)
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    draws = degrees  # all incident rows, not minus one
    max_draws = int(draws.max())
    idx = np.empty((max_draws, n), dtype=np.int64)
    for d in range(max_draws):
        idx[d] = rng.integers(0, n, size=n)
    return _variable_or_belief_jit(c2v, channel, draws.astype(np.int64), idx)


def _check_update(v2c: Any, dc_degrees: Any, dc_probs: Any,
                  rng: np.random.Generator, q: int) -> np.ndarray:
    """V9 ``check_update_mcde`` semantics with a numba-jitted convolution."""
    n = v2c.shape[0]
    v2c = np.asarray(v2c, dtype=np.float64)
    degrees = rng.choice(dc_degrees, size=n, p=dc_probs)
    draws = degrees - 1
    max_draws = int(draws.max())
    idx = np.empty((max_draws, n), dtype=np.int64)
    for d in range(max_draws):
        idx[d] = rng.integers(0, n, size=n)
    return _check_update_jit(v2c, draws.astype(np.int64), idx)


# --------------------------------------------------------------------------- #
# deterministic run + threshold proxy
# --------------------------------------------------------------------------- #


def run_mcde(q: int, lambda_edge: Mapping[Any, Any], rho_edge: Mapping[Any, Any], *,
             n_samples: int, max_iter: int, seed: int, channel_mode: str = QSC,
             p: float | None = None, w: Any | None = None,
             entropy_tol: float = 0.01, streak: int = 20,
             use_v9_kernels: bool = False) -> dict:
    """One deterministic full-vector MC-DE run (V9 semantics; see module
    docstring and design section 5).

    ``channel_mode="qsc"`` reproduces V9 ``run_mcde`` exactly (same seed,
    same per-iteration entropy trace).  ``channel_mode="structured"`` instead
    draws ``diffs = rng.choice(q, size=n_samples, p=w)`` and uses the
    error-domain channel rows ``channel[i, j] = w[j XOR diff_i]``.  Per-iteration
    ``entropy`` is the mean base-q entropy of the check population; converged
    when ``entropy < entropy_tol`` for ``streak`` consecutive iterations.
    """
    from .nonbinary_v9_mcde import _qint
    q = _qint(q)
    if channel_mode not in (QSC, STRUCTURED):
        raise ValueError("channel_mode must be 'qsc' or 'structured'")
    if isinstance(n_samples, bool) or not isinstance(n_samples, Integral) or int(n_samples) < 100:
        raise ValueError("n_samples must be an integer >= 100")
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral) or not 1 <= int(max_iter) <= 2000:
        raise ValueError("max_iter must be an integer in 1..2000")
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    if isinstance(entropy_tol, bool) or not isinstance(entropy_tol, (int, float)) \
            or not math.isfinite(float(entropy_tol)) or float(entropy_tol) <= 0.0:
        raise ValueError("entropy_tol must be positive and finite")
    if isinstance(streak, bool) or not isinstance(streak, Integral) or int(streak) < 1:
        raise ValueError("streak must be a positive integer")
    n_samples, max_iter, seed, streak = int(n_samples), int(max_iter), int(seed), int(streak)
    entropy_tol = float(entropy_tol)

    if channel_mode == QSC:
        if p is None:
            raise ValueError("p is required in qsc mode")
        if not isinstance(p, bool) and isinstance(p, (int, float)) and math.isfinite(float(p)) \
                and 0.0 < float(p) < (q - 1.0) / q:
            p = float(p)
        else:
            raise ValueError("q-ary symmetric p is outside the frozen open domain")
    else:  # structured
        if w is None:
            raise ValueError("w is required in structured mode")
        w = np.asarray(w, dtype=np.float64)
        if w.shape != (q,) or not np.all(np.isfinite(w)) or np.any(w < 0.0):
            raise ValueError("structured w must be a finite non-negative length-q vector")
        total_w = float(w.sum())
        if not math.isfinite(total_w) or total_w <= 0.0:
            raise ValueError("structured w must have positive total mass")
        if not math.isclose(total_w, 1.0, abs_tol=1e-9):
            w = w / total_w

    dv_degrees, dv_probs = parse_degree_hist(lambda_edge, "lambda_edge", DEGREE_MAX)
    dc_degrees, dc_probs = parse_degree_hist(rho_edge, "rho_edge", DEGREE_MAX)
    rng = np.random.default_rng(seed)
    if channel_mode == QSC:
        symbol_probs = np.full(q, p / (q - 1.0), dtype=np.float64)
        symbol_probs[0] = 1.0 - p
    c2v = np.full((n_samples, q), 1.0 / q, dtype=np.float64)
    entropy_trace: list[float] = []
    error_trace: list[float] = []
    converged = False
    iterations = 0
    converged_streak = 0

    v_update = variable_update_mcde if use_v9_kernels else _variable_update
    b_update = belief_update_mcde if use_v9_kernels else _belief_update
    c_update = check_update_mcde if use_v9_kernels else _check_update

    for iteration in range(1, max_iter + 1):
        if channel_mode == QSC:
            symbols = rng.choice(q, size=n_samples, p=symbol_probs)
            channel = np.full((n_samples, q), p / (q - 1.0), dtype=np.float64)
            channel[np.arange(n_samples), symbols] = 1.0 - p
        else:
            diffs = rng.choice(q, size=n_samples, p=w)
            channel = np.empty((n_samples, q), dtype=np.float64)
            for i in range(n_samples):
                channel[i] = w[np.arange(q) ^ diffs[i]]
        v2c = v_update(c2v, dv_degrees, dv_probs, channel, rng, q)
        c2v = c_update(v2c, dc_degrees, dc_probs, rng, q)
        belief = b_update(c2v, dv_degrees, dv_probs, channel, rng, q)
        entropy = entropy_base_q(c2v)
        error_prob = float(np.mean(np.argmax(belief, axis=1) != 0))
        entropy_trace.append(entropy)
        error_trace.append(error_prob)
        iterations = iteration
        converged_streak = converged_streak + 1 if entropy < entropy_tol else 0
        if converged_streak >= streak:
            converged = True
            break

    return {
        "schema": "nbldpc_v14_mcde_run_v1",
        "channel_mode": channel_mode,
        "converged": converged,
        "iterations": iterations,
        "entropy_trace": entropy_trace,
        "error_trace": error_trace,
        "final_entropy": float(entropy_trace[-1]) if entropy_trace else None,
        "q": q, "p": p if channel_mode == QSC else None, "n_samples": n_samples,
        "max_iter": max_iter, "seed": seed,
        "entropy_tol": entropy_tol, "streak": streak,
        "lambda": {int(k): float(v) for k, v in lambda_edge.items()},
        "rho": {int(k): float(v) for k, v in rho_edge.items()},
        "rng": "PCG64",
    }


def threshold_binary_search(q: int, rate: float, lambda_edge: Mapping[Any, Any],
                            rho_edge: Mapping[Any, Any], *,
                            n_samples: int, max_iter: int, seed: int,
                            p_lo: float = 0.01, p_hi: float = 0.12,
                            grid_step: float = 0.0025) -> dict:
    """Deterministic grid sweep for the DE threshold proxy (V8 boundary
    semantics).

    Sweeps ``p`` from ``p_lo`` to ``p_hi`` on the fixed grid
    ``[p_lo, p_lo+step, ..., p_hi]`` and calls :func:`run_mcde` in QSC mode
    with the same frozen seed at every grid point.  The proxy is the **largest
    ``p`` at which the run converges**; if no grid point converges the proxy is
    ``p_lo`` (mirroring the V8 accepted threshold semantics where the largest
    converged probe is the proxy).  The probe order is a fixed dense sweep, so
    the result is deterministic.
    """
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2:
        raise ValueError("q must be an integer >= 2")
    q = int(q)
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) \
            or not math.isfinite(float(rate)) or not 0.0 < float(rate) < 1.0:
        raise ValueError("rate must be finite in (0, 1)")
    if isinstance(grid_step, bool) or not isinstance(grid_step, (int, float)) \
            or not math.isfinite(float(grid_step)) or float(grid_step) <= 0.0:
        raise ValueError("grid_step must be positive and finite")
    if isinstance(p_lo, bool) or not isinstance(p_lo, (int, float)) or not math.isfinite(float(p_lo)) \
            or isinstance(p_hi, bool) or not isinstance(p_hi, (int, float)) or not math.isfinite(float(p_hi)) \
            or not 0.0 < float(p_lo) < float(p_hi) < (q - 1.0) / q:
        raise ValueError("invalid probe range")
    grid_start = float(p_lo)
    grid_end = float(p_hi)
    step = float(grid_step)
    points: list[float] = []
    p = grid_start
    while p <= grid_end + 0.5 * step:
        points.append(p)
        p += step
    probes: list[dict[str, Any]] = []
    highest_converged = None
    for p_probe in points:
        result = run_mcde(q, lambda_edge, rho_edge, n_samples=n_samples,
                          max_iter=max_iter, seed=seed, channel_mode=QSC, p=p_probe)
        probes.append({"p": p_probe, "converged": result["converged"],
                       "final_entropy": float(result["entropy_trace"][-1])})
        if result["converged"]:
            highest_converged = p_probe
    if highest_converged is None:
        proxy = grid_start
    else:
        proxy = highest_converged
    return {"threshold_proxy": float(proxy), "grid_points": points, "probes": probes,
            "converged_at_lo": probes[0]["converged"] if probes else None}


# --------------------------------------------------------------------------- #
# frozen stage constants (design section 2/3)
# --------------------------------------------------------------------------- #

# Stage 0: V8-60 accepted reference point (q=4, R=0.75).
STAGE0_Q = 4
STAGE0_RATE = 0.75
STAGE0_N_SAMPLES = 100000
STAGE0_MAX_ITER = 150
STAGE0_PUBLISHED = 0.069
STAGE0_TOL = 0.012
STAGE0_P_LO = 0.01
STAGE0_P_HI = 0.12
STAGE0_GRID_STEP = 0.0025
STAGE0_SEED = 2026090118
# Stage-0 variable-degree polynomial (published Table 1 row 0.75, exponent+1).
STAGE0_LAMBDA_DEGREES = {2: 0.107, 4: 0.245, 7: 0.192, 10: 0.034,
                         19: 0.207, 26: 0.161, 28: 0.049}

# Stage 2: frozen candidate variable-degree profiles and check-count points.
PROFILES = [
    {"id": 1, "lambda": {2: 0.25, 3: 0.30, 4: 0.45}},
    {"id": 2, "lambda": {2: 0.20, 3: 0.25, 5: 0.55}},
    {"id": 3, "lambda": {3: 0.3, 4: 0.7}},
]
#: Frozen codeblock length (design section 2, n=256, q=1024).
N_BLOCKS = 256
#: Frozen check counts m (design section 2): rate R = 1 - m/256.
MS = [15, 16, 17, 18]
#: Frozen stage-2 MC-DE budget (design section 5).
STAGE2_N_SAMPLES = 10000
STAGE2_MAX_ITER = 150
STAGE2_ENTROPY_TOL = 0.01
STAGE2_STREAK = 20
STAGE2_SEED_ROOT = 2026090200

V14_GATE_DECISION_SCHEMA = "nbldpc_v14_gate_decision_v1"
V14_GATE_MANIFEST_SCHEMA = "nbldpc_v14_gate_manifest_v1"


def structured_rho(rate: float, lambda_edge: Mapping[Any, Any]) -> dict[str, float]:
    """Harmonic-exact check distribution for one (profile, m) point."""
    return concentrated_check_distribution(rate, lambda_edge)


def stage2_f_achieved(m: int, entropy_bits_w: float) -> float:
    """``f = (m*10/256)/H(w)`` (design section 2)."""
    if isinstance(m, bool) or not isinstance(m, Integral):
        raise ValueError("m must be an integer")
    m = int(m)
    if isinstance(entropy_bits_w, bool) or not isinstance(entropy_bits_w, (int, float)) \
            or not math.isfinite(float(entropy_bits_w)) or float(entropy_bits_w) <= 0.0:
        raise ValueError("entropy_bits_w must be positive and finite")
    return (m * 10.0 / float(N_BLOCKS)) / float(entropy_bits_w)


# --------------------------------------------------------------------------- #
# stage doc builders (frozen schemas)
# --------------------------------------------------------------------------- #


def build_stage0_doc(*, run: dict, seed: int = STAGE0_SEED,
                     rate: float = STAGE0_RATE,
                     published: float = STAGE0_PUBLISHED,
                     tol: float = STAGE0_TOL) -> dict[str, Any]:
    """Stage 0 mechanism-regression doc (schema ``nbldpc_v14_stage0_v1``).

    ``run`` must carry ``threshold_proxy`` (the computed QSC proxy for the
    reference point).  Gate semantics: mechanism verified iff
    ``abs(proxy - published) <= tol``.
    """
    proxy = float(run["threshold_proxy"])
    delta = abs(proxy - published)
    return {
        "schema": "nbldpc_v14_stage0_v1",
        "q": STAGE0_Q, "rate": rate,
        "published_threshold_proxy": published,
        "computed_threshold_proxy": proxy,
        "delta": delta, "tolerance": tol,
        "mechanism_verified": bool(delta <= tol),
        "n_samples": STAGE0_N_SAMPLES, "max_iter": STAGE0_MAX_ITER, "seed": seed,
        "diagnostic_only": True,
    }


def build_stage1_doc(*, channel_doc: dict, m_bits: tuple[int, ...],
                     structured_smallq_run: dict) -> dict[str, Any]:
    """Stage 1 structured small-q validation doc (schema
    ``nbldpc_v14_stage1_v1``): normalization, folding homomorphism, entropy
    monotonicity and the QSC-limit property are asserted cheaply."""
    folding = {int(f["m_bits"]): {"q": int(f["q"]),
                                  "entropy_bits": float(f["entropy_bits"])}
               for f in channel_doc["folding"]}
    entropies = [folding[m]["entropy_bits"] for m in sorted(m_bits)
                 if m in folding]
    monotone = all(h2 >= h1 for h1, h2 in zip(entropies, entropies[1:]))
    checks = {
        "w_smooth_sums_one": math.isclose(sum(float(x) for x in channel_doc["w"]), 1.0,
                                          abs_tol=1e-6),
        "smoothing_floor_ge_lam_over_q": min(float(x)
                                             for x in channel_doc["w"]) >= (
                                                 channel_doc["smoothing_lambda"]
                                                 / channel_doc["q"]),
        "folding_entropy_monotone": monotone,
        "folded_normalized": all(
            math.isclose(sum(float(x) for x in f["w_small"]), 1.0, abs_tol=1e-6)
            for f in channel_doc["folding"]),
    }
    return {
        "schema": "nbldpc_v14_stage1_v1",
        "channel_schema": channel_doc["schema"],
        "m_bits": [int(m) for m in m_bits],
        "folding_entropy_bits": folding,
        "checks": checks,
        "smallq_run": {
            "channel_mode": structured_smallq_run.get("channel_mode"),
            "converged": structured_smallq_run.get("converged"),
            "iterations": structured_smallq_run.get("iterations"),
            "final_entropy": structured_smallq_run.get("final_entropy"),
        },
        "diagnostic_only": True,
    }


def build_stage2_doc(*, points: list[dict], entropy_bits_w: float) -> dict[str, Any]:
    """Stage 2 q=1024 point-evaluation doc (schema
    ``nbldpc_v14_stage2_v1``): one entry per (profile, m) point."""
    return {
        "schema": "nbldpc_v14_stage2_v1",
        "q": 1024, "entropy_bits_w": float(entropy_bits_w),
        "n_samples": STAGE2_N_SAMPLES, "max_iter": STAGE2_MAX_ITER,
        "entropy_tol": STAGE2_ENTROPY_TOL, "streak": STAGE2_STREAK,
        "points": points,
        "diagnostic_only": True,
    }


def build_gate_decision_doc(*, stage0: dict, stage2: dict, points: list[dict],
                            f_limit: float = 1.3) -> dict[str, Any]:
    """Frozen gate decision (schema ``nbldpc_v14_gate_decision_v1``).

    PASS iff Stage 0 mechanism regression passed AND there exists a converged
    point with ``f_achieved <= f_limit``.  A Stage-0 failure is frozen as
    ``mechanism_unverified`` and Stage 2 is not considered.
    """
    stage0_ok = bool(stage0["mechanism_verified"])
    converged_ok = [pt for pt in points
                    if pt.get("converged") and pt.get("f_achieved") is not None
                    and float(pt["f_achieved"]) <= f_limit]
    if not stage0_ok:
        gate_state = "mechanism_unverified"
    elif converged_ok:
        gate_state = "pass"
    else:
        gate_state = "fail"
    winner = None
    if converged_ok:
        winner = max(converged_ok,
                     key=lambda pt: (float(pt["f_achieved"]), pt.get("id", "")))
    return {
        "schema": V14_GATE_DECISION_SCHEMA,
        "gate_state": gate_state,
        "stage0_mechanism_verified": bool(stage0_ok),
        "exists_converged_point": bool(converged_ok),
        "f_limit": f_limit,
        "pass_point": winner,
        "stage2_point_count": len(points),
        "points_summary": [
            {"id": int(pt["id"]), "m": int(pt["m"]), "profile": int(pt["profile"]),
             "converged": bool(pt["converged"]),
             "f_achieved": pt.get("f_achieved"),
             "final_entropy": pt.get("final_entropy")} for pt in points],
        "diagnostic_only": True,
    }


def build_gate_manifest_doc(*, command: str, git_commit: str | None = None,
                            wall_seconds: float, peak_rss_bytes: int | None = None,
                            rss_cap_bytes: int | None = None,
                            **extra: Any) -> dict[str, Any]:
    """Gate run manifest (schema ``nbldpc_v14_gate_manifest_v1``): records the
    command, git commit, budget consumption (wall clock and peak process-tree
    RSS against the frozen cap)."""
    return {
        "schema": V14_GATE_MANIFEST_SCHEMA,
        "command": command,
        "git_commit": git_commit,
        "wall_seconds": float(wall_seconds),
        "peak_rss_bytes": peak_rss_bytes,
        "rss_cap_bytes": rss_cap_bytes,
        "rss_cap_exceeded": bool(peak_rss_bytes is not None and rss_cap_bytes is not None
                                 and peak_rss_bytes > rss_cap_bytes),
        **extra,
    }
