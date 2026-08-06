"""V10 DE/rand/1/bin ensemble optimizer plus own full-vector MC-DE evaluator
(``formal-nonbinary-ldpc-v10-de-peg-fftqspa``, additive layer; frozen
semantics per design sections 2-4).

Contents:

- **Own full-vector MC-DE evaluator** (fitness backend, q = 4..1024): every
  message is a full length-q probability vector; the check-node update is a
  batched XOR-order unnormalized WHT convolution (own implementation, ``/q``
  inverse) with all-unity coefficients and zero syndrome — the DE check-node
  semantics identical to the accepted V9 ``check_update_mcde``; variable and
  belief updates sample the exact edge-view degree per sample with a fresh
  QSC channel term; probability floor ``1e-300``; fail-closed normalization;
  PCG64 deterministic; convergence when the mean base-q check-message entropy
  stays below ``entropy_tol`` for ``streak`` consecutive iterations.  RNG draw
  order (frozen): degrees first, then one ``rng.integers(0, N, N)`` draw per
  product/convolution slot — exactly like the accepted V8/V9 MC-DE.
- ``threshold_binary_search``: deterministic binary probe of the DE threshold
  proxy (fixed p_lo/p_hi/p_tol, fixed seed per probe).
- **DE/rand/1/bin**: candidates encoded as 16 reals (8 degree slots + 8
  logits); degree slots are quantized with
  ``round(max(2, min(40, x + 2.0)))``; logits are used directly (softmax
  normalized over the 8 retained degrees).  Deterministic bias-free population
  initialization derived from the search seed; mutation
  ``v = x_r1 + F*(x_r2 - x_r3)`` with ``r1 != r2 != r3 != i``; binomial
  crossover; selection replaces only on a strictly better objective (equal
  retains the incumbent).  NaN/Inf trial vectors get a 1e12 penalty and join
  the death pool; structurally invalid candidates (duplicate degrees,
  weight < 0.01, sum != 1) get a 1e6 + violation-amount penalty.  Per-
  generation checkpoint (population + state JSON), transcript, resume from the
  exact saved state, no-overwrite on a completed run, hard ``max_evaluations``
  cap, single-threaded.
- **6-tier hierarchical lexicographic objective**: (1) entropy convergence at
  the gate p (eligible), (2) fewer converged iterations, (3) lower final mean
  base-q entropy, (4) lower symbol error probability, (5) higher threshold
  proxy (computed post-screen for eligible candidates only), (6) canonical
  ``(d0..d7, lambda0..lambda7)`` ascending lexicographic tie-break.

Imports: standard library, numpy, numba, ``nonbinary_v10_common`` and the
accepted field tables only.  Never imports any V8/V9 module (V8 is a
test-only oracle).

Numba integration (amendment ``evidence/v10_budget_amendment.json``,
AMEND-2026-08-05-01): the per-sample MC-DE hot loops are accelerated with
``numba.njit`` nopython kernels — the XOR-order WHT butterfly
(``_wht_row_jit`` / ``_wht_rows_jit``), the check-node convolution
(``_check_conv_jit``), the variable/belief product updates
(``_product_update_jit``) and the row normalization (floored inside the same
kernels).  The kernels are bit-identical to the numpy reference semantics
(engineering probe diff = 0.0; tests assert ``allclose(rtol=1e-12)`` plus a
known-answer delta -> all-ones butterfly regression).  ``cache=True`` is
intentionally NOT used, so no ``.npyc`` files are produced; nopython mode
only.  The DE optimizer body and the RNG (numpy PCG64) are untouched: every
random draw still happens in numpy in the frozen order (degrees first, then
one ``rng.integers(0, N, N)`` draw per product/convolution slot), so the RNG
trajectory is byte-for-byte unchanged and the kernels only consume the
pre-drawn indices.
"""
from __future__ import annotations

import json
import math
import os
import time
from dataclasses import asdict, dataclass
from numbers import Integral
from typing import Any, Mapping

import numpy as np
from numba import njit

from . import nonbinary_v10_common as common

__all__ = [
    "fwht_batched",
    "parse_degree_hist",
    "variable_update_mcde",
    "check_update_mcde",
    "belief_update_mcde",
    "entropy_base_q",
    "run_mcde",
    "threshold_binary_search",
    "ObjectiveRecord",
    "decode_vector",
    "quantize_degree_slots",
    "init_population",
    "evaluate_candidate",
    "evaluate_vector",
    "objective_compare",
    "record_to_dict",
    "record_from_dict",
    "run_de_search",
    "PENALTY_STRUCTURAL_BASE",
    "PENALTY_NAN_INF",
    "DEGREE_MAX",
]

#: Positivity floor for probability-domain products (V7 exact-DE convention).
_FLOOR = 1e-300
#: Upper bound on any degree in an edge-perspective histogram.
DEGREE_MAX = 64
#: Structural-invalidity penalty base (1e6 + violation amount).
PENALTY_STRUCTURAL_BASE = 1e6
#: NaN/Inf trial penalty (death pool).
PENALTY_NAN_INF = 1e12
#: Sentinel iteration count for non-converged candidates (finite, JSON-safe).
_SENTINEL_ITER = 10 ** 9
#: Sentinel entropy/error for non-converged candidates (finite, JSON-safe).
_SENTINEL_VALUE = 1e18
#: Frozen K=8 sparse representation constants.
_K = 8
_DEG_LO, _DEG_HI = 2, 40
_WEIGHT_TOL = 1e-12


# --------------------------------------------------------------------------- #
# own Walsh-Hadamard transform (XOR order, unnormalized)
# --------------------------------------------------------------------------- #


def fwht_batched(values: Any) -> np.ndarray:
    """Unnormalized XOR-order WHT along the last axis, vectorized over the
    leading axes (own implementation of the accepted butterfly).

    ``q = values.shape[-1]`` must be a power of two >= 2; the result is
    ``WHT(f)`` with ``WHT(WHT(f)) = q * f``.  The butterfly itself runs in
    the njit kernel :func:`_wht_rows_jit` (bit-identical to the numpy
    semantics, AMEND-2026-08-05-01); validation stays here fail-closed.
    """
    out = np.asarray(values, dtype=np.float64)
    if out.ndim < 1:
        raise ValueError("fwht_batched requires at least one axis")
    q = out.shape[-1]
    if q < 2 or q & (q - 1):
        raise ValueError("last axis size must be a power of two >= 2")
    if not np.all(np.isfinite(out)):
        raise ValueError("fwht_batched inputs must be finite")
    block = np.ascontiguousarray(out.reshape(-1, q))
    return _wht_rows_jit(block).reshape(out.shape)


# --------------------------------------------------------------------------- #
# numba njit hot kernels (AMEND-2026-08-05-01)
# --------------------------------------------------------------------------- #
# numba (already a root requirements.txt dependency) accelerates the
# per-sample MC-DE hot loops below.  cache=True is intentionally NOT used so
# no .npyc files are produced; nopython mode only.  The kernels are
# bit-identical to the numpy reference semantics (engineering probe diff =
# 0.0; tests assert allclose(rtol=1e-12) plus a known-answer butterfly
# regression).  The RNG stays entirely in numpy PCG64 with the frozen draw
# order — the kernels only consume pre-drawn index arrays.


@njit(cache=False)
def _wht_row_jit(row: np.ndarray) -> None:
    """In-place unnormalized XOR-order WHT of a single row."""
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
def _check_conv_jit(v2c: np.ndarray, idx: np.ndarray,
                    draws: np.ndarray) -> np.ndarray:
    """njit check-node convolution (V10 semantics).

    Per draw slot ``d``: gather the pre-drawn rows ``v2c[idx[d]]``, WHT each,
    multiply into the accumulated spectrum (delta-at-0 spectrum starts at all
    ones) only for samples whose degree exceeds the slot; then inverse WHT,
    ``/ q``, ``1e-300`` floor and row normalization — all inside the kernel.
    """
    n = v2c.shape[0]
    q = v2c.shape[1]
    acc = np.ones((n, q))  # spectrum of delta at 0 = all ones
    tmp = np.empty(q)
    for d in range(idx.shape[0]):
        for i in range(n):
            tmp[:] = v2c[idx[d, i]]
            _wht_row_jit(tmp)
            if draws[i] > d:
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


@njit(cache=False)
def _product_update_jit(c2v: np.ndarray, channel: np.ndarray, idx: np.ndarray,
                        draws: np.ndarray) -> np.ndarray:
    """njit variable/belief product update.

    Starts from the channel row; per draw slot ``d`` multiply in the
    pre-drawn incoming row ``c2v[idx[d]]`` for samples whose degree exceeds
    the slot; then ``1e-300`` floor and row normalization — all inside the
    kernel.
    """
    n = c2v.shape[0]
    q = c2v.shape[1]
    product = channel.copy()
    for d in range(idx.shape[0]):
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


# --------------------------------------------------------------------------- #
# degree-distribution helpers
# --------------------------------------------------------------------------- #


def parse_degree_hist(hist: Mapping[Any, Any], name: str,
                      degree_max: int) -> tuple[np.ndarray, np.ndarray]:
    """Validate an edge-perspective degree histogram -> ``(degrees, probs)``.

    Accepts a mapping ``degree -> positive finite weight`` (any positive sum;
    the weights are normalized here), rejects empty maps, non-positive /
    non-finite weights and degrees outside ``[1, degree_max]``.
    """
    if isinstance(degree_max, bool) or not isinstance(degree_max, Integral) or int(degree_max) < 2:
        raise ValueError("degree_max must be an integer >= 2")
    degree_max = int(degree_max)
    if not isinstance(hist, Mapping):
        raise ValueError(f"{name} must be a mapping")
    degrees: list[int] = []
    weights: list[float] = []
    for key, value in hist.items():
        if isinstance(key, bool) or not isinstance(key, Integral):
            raise ValueError(f"{name} degrees must be integers")
        degree = int(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(float(value)) or float(value) <= 0.0:
            raise ValueError(f"{name} requires positive finite weights")
        if not 1 <= degree <= degree_max:
            raise ValueError(f"{name} degree outside 1..{degree_max}")
        degrees.append(degree)
        weights.append(float(value))
    if not degrees:
        raise ValueError(f"{name} is empty")
    order = np.argsort(degrees)
    degree_array = np.asarray(degrees, dtype=np.int64)[order]
    weight_array = np.asarray(weights, dtype=np.float64)[order]
    total = float(weight_array.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError(f"{name} weights have invalid total")
    return degree_array, weight_array / total


def _as_mapping(degrees: Any, probs: Any) -> dict[int, float]:
    return {int(degree): float(prob) for degree, prob in zip(degrees, probs)}


# --------------------------------------------------------------------------- #
# population validation and normalization (fail-closed)
# --------------------------------------------------------------------------- #


def _validate_pop(pop: Any, n: int, q: int, name: str) -> np.ndarray:
    array = np.asarray(pop, dtype=np.float64)
    if array.shape != (n, q):
        raise ValueError(f"{name} must have shape ({n}, {q})")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    if np.any(array < 0.0):
        raise ValueError(f"{name} must be non-negative")
    totals = array.sum(axis=1)
    if not np.all(np.isfinite(totals)) or np.any(totals <= 0.0):
        raise ValueError(f"{name} must have positive row mass")
    return array


def _validate_normalized(pop: np.ndarray, name: str) -> np.ndarray:
    """Fail-closed validation of a kernel-normalized population.

    The njit kernels already apply the ``1e-300`` floor and the row
    normalization inside the compiled code; this re-checks the invariants so
    a NaN/Inf propagating through a kernel is still caught and raised
    (fail-closed) instead of silently flowing into the optimizer.
    """
    if not np.all(np.isfinite(pop)):
        raise ValueError(f"{name}: non-finite mass")
    if np.any(pop < -1e-12):
        raise ValueError(f"{name}: negative mass")
    totals = pop.sum(axis=1)
    if not np.all(np.isfinite(totals)) or np.any(totals <= 0.0):
        raise ValueError(f"{name}: zero or non-finite total mass")
    return pop


def _qint(q: Any) -> int:
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1) \
            or int(q) > 1024:
        raise ValueError("V10 requires a power-of-two GF(q) with 2 <= q <= 1024")
    return int(q)


# --------------------------------------------------------------------------- #
# MC-DE update steps (every message is a length-q vector)
# --------------------------------------------------------------------------- #


def check_update_mcde(v2c: Any, dc_degrees: Any, dc_probs: Any, rng: np.random.Generator,
                      q: int) -> np.ndarray:
    """Check-node update for an (N, q) incoming population.

    Per sample: sample the exact check degree, draw ``dc - 1`` iid incoming
    rows, XOR-convolve them via the batched WHT (all-unity coefficients, zero
    syndrome), floor and normalize.  RNG draw order (frozen): degrees first,
    then one ``rng.integers(0, N, N)`` draw per convolution slot.  The
    convolution itself runs in the njit kernel :func:`_check_conv_jit`
    (AMEND-2026-08-05-01); the numpy PCG64 draws are byte-for-byte unchanged.
    """
    n = v2c.shape[0]
    q = _qint(q)
    v2c = _validate_pop(v2c, n, q, "v2c")
    dc_degrees, dc_probs = parse_degree_hist(_as_mapping(dc_degrees, dc_probs),
                                             "dc_degrees", DEGREE_MAX)
    degrees = rng.choice(dc_degrees, size=n, p=dc_probs)
    draws = degrees - 1
    max_draws = int(draws.max())
    idx = np.empty((max_draws, n), dtype=np.int64)
    for draw in range(max_draws):
        idx[draw] = rng.integers(0, n, size=n)
    conv = _check_conv_jit(v2c, idx, draws)
    return _validate_normalized(conv, "check update")


def variable_update_mcde(c2v: Any, dv_degrees: Any, dv_probs: Any, channel: Any,
                         rng: np.random.Generator, q: int) -> np.ndarray:
    """Variable-node update for an (N, q) check-message population.

    Per sample: sample the exact variable degree, multiply in a FRESH channel
    row and ``dv - 1`` iid incoming check rows pointwise, floor and normalize.
    RNG draw order (frozen): degrees first, then one ``rng.integers(0, N, N)``
    draw per product slot (channel rows are drawn by the caller).  The product
    update runs in the njit kernel :func:`_product_update_jit`
    (AMEND-2026-08-05-01); the numpy PCG64 draws are byte-for-byte unchanged.
    """
    n = c2v.shape[0]
    q = _qint(q)
    c2v = _validate_pop(c2v, n, q, "c2v")
    channel = _validate_pop(channel, n, q, "channel")
    dv_degrees, dv_probs = parse_degree_hist(_as_mapping(dv_degrees, dv_probs),
                                             "dv_degrees", DEGREE_MAX)
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    draws = degrees - 1
    max_draws = int(draws.max())
    idx = np.empty((max_draws, n), dtype=np.int64)
    for draw in range(max_draws):
        idx[draw] = rng.integers(0, n, size=n)
    product = _product_update_jit(c2v, channel, idx, draws)
    return _validate_normalized(product, "variable update")


def belief_update_mcde(c2v: Any, dv_degrees: Any, dv_probs: Any, channel: Any,
                       rng: np.random.Generator, q: int) -> np.ndarray:
    """Belief population: channel x all ``dv`` incident check rows, floored and
    normalized.  RNG draw order (frozen): degrees first, then one
    ``rng.integers(0, N, N)`` draw per product slot.  The product update runs
    in the njit kernel :func:`_product_update_jit` (AMEND-2026-08-05-01); the
    numpy PCG64 draws are byte-for-byte unchanged."""
    n = c2v.shape[0]
    q = _qint(q)
    c2v = _validate_pop(c2v, n, q, "c2v")
    channel = _validate_pop(channel, n, q, "channel")
    dv_degrees, dv_probs = parse_degree_hist(_as_mapping(dv_degrees, dv_probs),
                                             "dv_degrees", DEGREE_MAX)
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    draws = degrees
    max_draws = int(draws.max())
    idx = np.empty((max_draws, n), dtype=np.int64)
    for draw in range(max_draws):
        idx[draw] = rng.integers(0, n, size=n)
    product = _product_update_jit(c2v, channel, idx, draws)
    return _validate_normalized(product, "belief update")


def entropy_base_q(pop: Any) -> float:
    """Mean row entropy in base q: ``mean over rows of -sum p*log_q(p)``
    (0 for a degenerate deterministic mass).  Zero-mass rows are rejected
    fail-closed."""
    array = np.asarray(pop, dtype=np.float64)
    if array.ndim != 2:
        raise ValueError("pop must be a 2-D (N, q) array")
    q = array.shape[-1]
    q = _qint(q)
    if not np.all(np.isfinite(array)):
        raise ValueError("pop must be finite")
    if np.any(array < 0.0):
        raise ValueError("pop must be non-negative")
    totals = array.sum(axis=1)
    if not np.all(np.isfinite(totals)) or np.any(totals <= 0.0):
        raise ValueError("pop rows must have positive total mass")
    logq = math.log(q)
    terms = np.zeros_like(array)
    nonzero = array > 0.0
    terms[nonzero] = -array[nonzero] * np.log(array[nonzero]) / logq
    return float(np.mean(terms.sum(axis=1)))


# --------------------------------------------------------------------------- #
# deterministic MC-DE runs
# --------------------------------------------------------------------------- #


def run_mcde(q: int, lambda_edge: Mapping[Any, Any], rho_edge: Mapping[Any, Any], p: float, *,
             n_samples: int, max_iter: int, seed: int, entropy_tol: float = 0.01,
             streak: int = 20) -> dict:
    """One deterministic full-vector MC-DE run (see module docstring).

    Iteration order (frozen): variable update -> check update -> belief; the
    recorded ``entropy`` is the mean base-q entropy of the check-message
    population and ``error_prob`` the fraction of belief argmax symbols != 0.
    Converged when ``entropy < entropy_tol`` for ``streak`` consecutive
    iterations.  All parameters are validated fail-closed.
    """
    q = _qint(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1.0) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    p = float(p)
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
    dv_degrees, dv_probs = parse_degree_hist(lambda_edge, "lambda_edge", DEGREE_MAX)
    dc_degrees, dc_probs = parse_degree_hist(rho_edge, "rho_edge", DEGREE_MAX)
    rng = np.random.default_rng(seed)
    symbol_probs = np.full(q, p / (q - 1.0), dtype=np.float64)
    symbol_probs[0] = 1.0 - p
    c2v = np.full((n_samples, q), 1.0 / q, dtype=np.float64)
    entropy_trace: list[float] = []
    error_trace: list[float] = []
    converged = False
    iterations = 0
    converged_streak = 0
    for iteration in range(1, max_iter + 1):
        symbols = rng.choice(q, size=n_samples, p=symbol_probs)
        channel = np.full((n_samples, q), p / (q - 1.0), dtype=np.float64)
        channel[np.arange(n_samples), symbols] = 1.0 - p
        v2c = variable_update_mcde(c2v, dv_degrees, dv_probs, channel, rng, q)
        c2v = check_update_mcde(v2c, dc_degrees, dc_probs, rng, q)
        belief = belief_update_mcde(c2v, dv_degrees, dv_probs, channel, rng, q)
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
        "converged": converged,
        "iterations": iterations,
        "entropy_trace": entropy_trace,
        "error_trace": error_trace,
        "q": q, "p": p, "n_samples": n_samples, "max_iter": max_iter, "seed": seed,
        "entropy_tol": entropy_tol, "streak": streak,
        "lambda": {int(k): float(v) for k, v in lambda_edge.items()},
        "rho": {int(k): float(v) for k, v in rho_edge.items()},
    }


def threshold_binary_search(q: int, lambda_edge: Mapping[Any, Any], rho_edge: Mapping[Any, Any], *,
                            n_samples: int, max_iter: int, seed: int,
                            p_lo: float, p_hi: float, p_tol: float) -> dict:
    """Deterministic binary search for the DE threshold proxy p*.

    ``p*`` is the largest p (to ``p_tol``) for which the run converges.  Each
    probe calls :func:`run_mcde` with the same frozen seed; the probe order is
    a fixed binary search from the frozen endpoints, so the result is
    byte-for-byte reproducible.
    """
    q = _qint(q)
    if isinstance(p_lo, bool) or not isinstance(p_lo, (int, float)) or not math.isfinite(float(p_lo)) \
            or isinstance(p_hi, bool) or not isinstance(p_hi, (int, float)) or not math.isfinite(float(p_hi)) \
            or not 0.0 < float(p_lo) < float(p_hi) < (q - 1.0) / q:
        raise ValueError("invalid probe range")
    if isinstance(p_tol, bool) or not isinstance(p_tol, (int, float)) \
            or not math.isfinite(float(p_tol)) or float(p_tol) <= 0.0:
        raise ValueError("p_tol must be positive and finite")
    lo, hi = float(p_lo), float(p_hi)
    probes: list[dict[str, Any]] = []
    while hi - lo > float(p_tol):
        mid = (lo + hi) / 2.0
        result = run_mcde(q, lambda_edge, rho_edge, mid, n_samples=n_samples,
                          max_iter=max_iter, seed=seed)
        probes.append({"p": mid, "converged": result["converged"],
                       "final_entropy": float(result["entropy_trace"][-1]),
                       "final_error": float(result["error_trace"][-1])})
        if result["converged"]:
            lo = mid
        else:
            hi = mid
    return {"threshold_proxy": (lo + hi) / 2.0, "probes": probes,
            "converged_at_lo": probes[-1]["converged"] if probes else None}


# --------------------------------------------------------------------------- #
# K=8 sparse representation
# --------------------------------------------------------------------------- #


def quantize_degree_slots(slots: Any) -> np.ndarray:
    """Map the 8 floating degree slots to integer degrees in [2, 40]:
    ``round(max(2, min(40, x + 2.0)))`` (frozen quantization)."""
    values = np.asarray(slots, dtype=np.float64)
    if values.shape != (_K,):
        raise ValueError(f"degree slots must be a length-{_K} vector")
    if not np.all(np.isfinite(values)):
        raise ValueError("degree slots must be finite")
    quantized = np.round(np.clip(values + 2.0, _DEG_LO, _DEG_HI))
    return quantized.astype(np.int64)


def decode_vector(x: Any) -> dict[int, float]:
    """Decode a 16-real DE vector into a ``{degree: weight}`` lambda edge
    histogram: quantize the 8 degree slots, softmax-normalize the 8 logits.
    The returned dict is *not* validated (callers must validate or pay the
    structural penalty); degrees may repeat after quantization."""
    vector = np.asarray(x, dtype=np.float64)
    if vector.shape != (2 * _K,):
        raise ValueError(f"candidate vector must have length {2 * _K}")
    if not np.all(np.isfinite(vector)):
        raise ValueError("candidate vector must be finite")
    degrees = quantize_degree_slots(vector[:_K])
    logits = vector[_K:]
    shifted = logits - logits.max()
    exp_logits = np.exp(shifted)
    weights = exp_logits / exp_logits.sum()
    return {int(degree): float(weight) for degree, weight in zip(degrees, weights)}


def init_population(pop_size: int, search_seed: int) -> np.ndarray:
    """Deterministic bias-free population initialization from the search seed.

    Degree slots are set so the quantization maps back to the sampled distinct
    degrees (slot = degree - 2.0); logits are zero-mean standard normal.  All
    randomness derives from ``v10_seed(f"de:init:{search_seed}")``."""
    if isinstance(pop_size, bool) or not isinstance(pop_size, Integral) or int(pop_size) < 1:
        raise ValueError("pop_size must be a positive integer")
    if isinstance(search_seed, bool) or not isinstance(search_seed, Integral):
        raise ValueError("search_seed must be an integer")
    pop_size = int(pop_size)
    rng = np.random.default_rng(common.v10_seed(f"de:init:{int(search_seed)}"))
    population = np.zeros((pop_size, 2 * _K), dtype=np.float64)
    degree_pool = np.arange(_DEG_LO, _DEG_HI + 1, dtype=np.int64)
    for index in range(pop_size):
        degrees = np.sort(rng.choice(degree_pool, size=_K, replace=False))
        logits = rng.standard_normal(_K)
        population[index, :_K] = degrees.astype(np.float64) - 2.0
        population[index, _K:] = logits
    return population


def _structural_violation_amount(lambda_edge: Mapping[Any, Any]) -> float:
    """Quantitative structural violation amount for the 1e6 penalty (0.0 when
    the lambda is structurally valid)."""
    if not isinstance(lambda_edge, Mapping) or len(lambda_edge) != _K:
        return float(abs(len(lambda_edge) - _K))
    degrees: list[int] = []
    weights: list[float] = []
    amount = 0.0
    for key, value in lambda_edge.items():
        if isinstance(key, bool) or not isinstance(key, Integral):
            return float(1.0)
        degree = int(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(float(value)):
            return float(1e6)
        weight = float(value)
        if not _DEG_LO <= degree <= _DEG_HI:
            amount += 1.0
        if weight < 0.0:
            amount += -weight
        degrees.append(degree)
        weights.append(weight)
    if len(set(degrees)) != _K:
        amount += float(len(degrees) - len(set(degrees)))
    for degree, weight in zip(degrees, weights):
        if weight < 0.01:
            amount += 0.01 - weight
    total = sum(weights)
    amount += abs(total - 1.0)
    return float(amount)


def _canonical_tuple(lambda_edge: Mapping[Any, Any]) -> tuple:
    """Canonical ``(d0..d7, lambda0..lambda7)`` with degrees sorted ascending."""
    degrees = sorted(int(d) for d in lambda_edge)
    return tuple(degrees) + tuple(float(lambda_edge[d]) for d in degrees)


# --------------------------------------------------------------------------- #
# 6-tier lexicographic objective
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ObjectiveRecord:
    """One candidate objective.

    Tiers: 1 ``entropy_converged`` (gate at p; must be True to be eligible),
    2 ``converged_iter`` (min), 3 ``final_entropy`` (min), 4 ``error_prob``
    (min), 5 ``threshold_proxy`` (max; None until computed post-screen),
    6 ``canonical_tuple`` (ascending lexicographic).  ``penalty > 0`` marks a
    structurally invalid (1e6 + violation) or NaN/Inf (1e12) candidate, which
    is strictly worse than any valid candidate.  Non-converged valid
    candidates carry finite sentinel maxima for tiers 2-4.
    """
    entropy_converged: bool
    converged_iter: int
    final_entropy: float
    error_prob: float
    threshold_proxy: float | None
    canonical_tuple: tuple
    penalty: float = 0.0


def record_to_dict(record: ObjectiveRecord) -> dict[str, Any]:
    data = asdict(record)
    data["canonical_tuple"] = list(record.canonical_tuple)
    return data


def record_from_dict(data: Mapping[str, Any]) -> ObjectiveRecord:
    return ObjectiveRecord(
        entropy_converged=bool(data["entropy_converged"]),
        converged_iter=int(data["converged_iter"]),
        final_entropy=float(data["final_entropy"]),
        error_prob=float(data["error_prob"]),
        threshold_proxy=(None if data["threshold_proxy"] is None
                         else float(data["threshold_proxy"])),
        canonical_tuple=tuple(float(v) for v in data["canonical_tuple"]),
        penalty=float(data["penalty"]),
    )


def objective_compare(left: ObjectiveRecord, right: ObjectiveRecord) -> int:
    """Return -1 when ``left`` is strictly better, +1 when ``right`` is
    strictly better, 0 when equal.  Deterministic total order: penalty first
    (valid beats penalized; lower penalty among penalized), then tiers 1-6."""
    if left.penalty != right.penalty:
        return -1 if left.penalty < right.penalty else 1
    if left.penalty > 0.0:
        return 0
    if left.entropy_converged != right.entropy_converged:
        return -1 if left.entropy_converged else 1
    if left.converged_iter != right.converged_iter:
        return -1 if left.converged_iter < right.converged_iter else 1
    if left.final_entropy != right.final_entropy:
        return -1 if left.final_entropy < right.final_entropy else 1
    if left.error_prob != right.error_prob:
        return -1 if left.error_prob < right.error_prob else 1
    if left.threshold_proxy is not None and right.threshold_proxy is not None \
            and left.threshold_proxy != right.threshold_proxy:
        return -1 if left.threshold_proxy > right.threshold_proxy else 1
    if left.canonical_tuple != right.canonical_tuple:
        return -1 if left.canonical_tuple < right.canonical_tuple else 1
    return 0


def _rho_from_concentrated(conc: Mapping[str, Any]) -> dict[int, float]:
    return {int(degree): float(weight) for degree, weight in (
        (conc["dc_lo"], conc["w_lo"]), (conc["dc_hi"], conc["w_hi"])) if float(weight) > 0.0}


def evaluate_candidate(lambda_edge: Mapping[Any, Any], q: int, rate: float, p_gate: float, *,
                       seed: int, n_samples: int, max_iter: int,
                       entropy_tol: float = 0.01, streak: int = 20,
                       threshold_p_lo: float = 0.01, threshold_p_hi: float = 0.49,
                       threshold_p_tol: float = 0.0025,
                       compute_threshold: bool = False) -> ObjectiveRecord:
    """Deterministic MC-DE evaluation of one lambda candidate at the gate p.

    Fail-closed: an invalid lambda (structural violation) returns a penalty
    record of ``1e6 + violation amount`` without running MC-DE.  A valid
    candidate runs :func:`run_mcde` at ``p_gate`` with the frozen ``seed``;
    only entropy-converged (eligible) candidates compute the threshold proxy
    (binary search) when ``compute_threshold`` is set.
    """
    q = _qint(q)
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(float(rate)):
        raise ValueError("rate must be finite")
    rate = float(rate)
    if isinstance(p_gate, bool) or not isinstance(p_gate, (int, float)) \
            or not math.isfinite(float(p_gate)) or not 0.0 < float(p_gate) < (q - 1.0) / q:
        raise ValueError("p_gate must be inside the frozen open domain")
    p_gate = float(p_gate)
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    violation = _structural_violation_amount(lambda_edge)
    canonical = _canonical_tuple(lambda_edge)
    if violation > 0.0:
        return ObjectiveRecord(
            entropy_converged=False, converged_iter=_SENTINEL_ITER,
            final_entropy=_SENTINEL_VALUE, error_prob=_SENTINEL_VALUE,
            threshold_proxy=None, canonical_tuple=canonical,
            penalty=PENALTY_STRUCTURAL_BASE + violation)
    try:
        conc = common.concentrated_check_distribution(rate, lambda_edge)
        rho_edge = _rho_from_concentrated(conc)
        result = run_mcde(q, lambda_edge, rho_edge, p_gate, n_samples=n_samples,
                          max_iter=max_iter, seed=int(seed), entropy_tol=entropy_tol,
                          streak=streak)
    except ValueError:
        # Fail-closed: a degenerate candidate that breaks the rho algebra or
        # the MC-DE validation is penalized, never allowed to crash the search.
        return ObjectiveRecord(
            entropy_converged=False, converged_iter=_SENTINEL_ITER,
            final_entropy=_SENTINEL_VALUE, error_prob=_SENTINEL_VALUE,
            threshold_proxy=None, canonical_tuple=canonical,
            penalty=PENALTY_STRUCTURAL_BASE + 1.0)
    if not result["converged"]:
        return ObjectiveRecord(
            entropy_converged=False, converged_iter=_SENTINEL_ITER,
            final_entropy=_SENTINEL_VALUE, error_prob=_SENTINEL_VALUE,
            threshold_proxy=None, canonical_tuple=canonical, penalty=0.0)
    threshold_proxy = None
    if compute_threshold:
        try:
            threshold_proxy = threshold_binary_search(
                q, lambda_edge, rho_edge, n_samples=n_samples, max_iter=max_iter,
                seed=int(seed), p_lo=threshold_p_lo, p_hi=threshold_p_hi,
                p_tol=threshold_p_tol)["threshold_proxy"]
        except ValueError:
            threshold_proxy = None
    return ObjectiveRecord(
        entropy_converged=True, converged_iter=int(result["iterations"]),
        final_entropy=float(result["entropy_trace"][-1]),
        error_prob=float(result["error_trace"][-1]),
        threshold_proxy=threshold_proxy, canonical_tuple=canonical, penalty=0.0)


def evaluate_vector(x: Any, q: int, rate: float, p_gate: float, *,
                    seed: int, n_samples: int, max_iter: int,
                    entropy_tol: float = 0.01, streak: int = 20,
                    threshold_p_lo: float = 0.01, threshold_p_hi: float = 0.49,
                    threshold_p_tol: float = 0.0025,
                    compute_threshold: bool = False) -> ObjectiveRecord:
    """Evaluate one raw 16-real DE vector (decode -> validate -> MC-DE).

    NaN/Inf in the raw vector -> penalty 1e12 (death pool).  Structural
    violations -> penalty 1e6 + violation amount.  Otherwise identical to
    :func:`evaluate_candidate`.
    """
    vector = np.asarray(x, dtype=np.float64)
    if vector.shape != (2 * _K,):
        raise ValueError(f"candidate vector must have length {2 * _K}")
    if not np.all(np.isfinite(vector)):
        return ObjectiveRecord(
            entropy_converged=False, converged_iter=_SENTINEL_ITER,
            final_entropy=_SENTINEL_VALUE, error_prob=_SENTINEL_VALUE,
            threshold_proxy=None, canonical_tuple=(), penalty=PENALTY_NAN_INF)
    lambda_edge = decode_vector(vector)
    return evaluate_candidate(lambda_edge, q, rate, p_gate, seed=seed,
                              n_samples=n_samples, max_iter=max_iter,
                              entropy_tol=entropy_tol, streak=streak,
                              threshold_p_lo=threshold_p_lo,
                              threshold_p_hi=threshold_p_hi,
                              threshold_p_tol=threshold_p_tol,
                              compute_threshold=compute_threshold)


# --------------------------------------------------------------------------- #
# DE/rand/1/bin search with checkpoint/resume
# --------------------------------------------------------------------------- #


def _mutation_rng(search_seed: int, generation: int, index: int) -> np.random.Generator:
    return np.random.default_rng(
        common.v10_seed(f"de:mut:{int(search_seed)}:g{int(generation)}:i{int(index)}"))


def _draw_distinct(rng: np.random.Generator, pop_size: int, exclude: int) -> tuple[int, int, int]:
    pool = [index for index in range(pop_size) if index != exclude]
    chosen = rng.choice(pool, size=3, replace=False)
    return int(chosen[0]), int(chosen[1]), int(chosen[2])


def _binomial_crossover(rng: np.random.Generator, mutant: np.ndarray, incumbent: np.ndarray,
                        cr: float) -> np.ndarray:
    mask = rng.random(incumbent.shape[0]) < float(cr)
    if not mask.any():
        mask[rng.integers(0, incumbent.shape[0])] = True
    return np.where(mask, mutant, incumbent)


def run_de_search(*, q: int, p_gate: float, rate: float, search_seed: int,
                  pop_size: int, max_gen: int, f: float, cr: float,
                  n_samples: int, max_iter: int, entropy_tol: float = 0.01,
                  streak: int = 20, max_evaluations: int | None = None,
                  out_dir: str | None = None, resume: bool = False,
                  threshold_p_lo: float = 0.01, threshold_p_hi: float = 0.49,
                  threshold_p_tol: float = 0.0025,
                  compute_threshold: bool = True) -> dict[str, Any]:
    """One deterministic single-threaded DE/rand/1/bin search.

    Screen evaluations (each = one MC-DE run at the gate p) count toward
    ``max_evaluations`` (hard cap; initial population counts pop_size).
    Checkpoints are written after every generation when ``out_dir`` is given;
    ``resume=True`` continues from the most recent checkpoint (exact state).
    A completed run in ``out_dir`` refuses to be overwritten.  After the last
    generation, eligible candidates of the final population enter the binary
    search for the threshold proxy (post-screen protocol step 2).
    """
    q = _qint(q)
    if isinstance(p_gate, bool) or not isinstance(p_gate, (int, float)) \
            or not math.isfinite(float(p_gate)) or not 0.0 < float(p_gate) < (q - 1.0) / q:
        raise ValueError("p_gate must be inside the frozen open domain")
    p_gate = float(p_gate)
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(float(rate)):
        raise ValueError("rate must be finite")
    rate = float(rate)
    if isinstance(search_seed, bool) or not isinstance(search_seed, Integral):
        raise ValueError("search_seed must be an integer")
    if isinstance(pop_size, bool) or not isinstance(pop_size, Integral) or int(pop_size) < 1:
        raise ValueError("pop_size must be a positive integer")
    if int(pop_size) < 4:
        raise ValueError("pop_size must be >= 4 for DE/rand/1/bin (three distinct others)")
    if isinstance(max_gen, bool) or not isinstance(max_gen, Integral) or int(max_gen) < 0:
        raise ValueError("max_gen must be a non-negative integer")
    if isinstance(f, bool) or not isinstance(f, (int, float)) or not math.isfinite(float(f)) \
            or float(f) <= 0.0:
        raise ValueError("F must be positive and finite")
    if isinstance(cr, bool) or not isinstance(cr, (int, float)) or not math.isfinite(float(cr)) \
            or not 0.0 <= float(cr) <= 1.0:
        raise ValueError("CR must be in [0, 1]")
    if max_evaluations is not None and (isinstance(max_evaluations, bool)
                                        or not isinstance(max_evaluations, Integral)
                                        or int(max_evaluations) < 1):
        raise ValueError("max_evaluations must be a positive integer or None")
    pop_size, max_gen, search_seed = int(pop_size), int(max_gen), int(search_seed)
    f, cr = float(f), float(cr)
    max_evaluations = None if max_evaluations is None else int(max_evaluations)

    params = {
        "q": q, "p_gate": p_gate, "rate": rate, "search_seed": search_seed,
        "pop_size": pop_size, "max_gen": max_gen, "F": f, "CR": cr,
        "n_samples": n_samples, "max_iter": max_iter, "entropy_tol": entropy_tol,
        "streak": streak, "max_evaluations": max_evaluations,
        "threshold_p_lo": threshold_p_lo, "threshold_p_hi": threshold_p_hi,
        "threshold_p_tol": threshold_p_tol, "compute_threshold": compute_threshold,
        "de_variant": "DE/rand/1/bin", "K": _K,
        "degree_range": [_DEG_LO, _DEG_HI], "min_weight": 0.01,
        "objective": "hierarchical_6tier_lexicographic",
        "workers": 1,
    }

    complete_marker = None if out_dir is None else os.path.join(out_dir, "run_complete.json")
    if out_dir is not None and os.path.exists(complete_marker):
        raise ValueError(f"refusing to overwrite a completed run: {complete_marker}")
    if out_dir is not None:
        os.makedirs(out_dir, exist_ok=True)

    population, objectives, generation, evaluations, best_index, death_pool, transcript = \
        _initial_state(search_seed, pop_size, params, resume=resume, out_dir=out_dir)

    started_at = time.time()
    gen_times: list[float] = []
    stop_reason = "max_gen_reached"
    while generation < max_gen and (max_evaluations is None or evaluations < max_evaluations):
        gen_start = time.time()
        generation += 1
        trials: list[dict[str, Any]] = []
        for index in range(pop_size):
            if max_evaluations is not None and evaluations >= max_evaluations:
                break
            rng = _mutation_rng(search_seed, generation, index)
            r1, r2, r3 = _draw_distinct(rng, pop_size, index)
            mutant = population[r1] + f * (population[r2] - population[r3])
            trial = _binomial_crossover(rng, mutant, population[index], cr)
            trial_objective = evaluate_vector(trial, q, rate, p_gate,
                                              seed=search_seed, n_samples=n_samples,
                                              max_iter=max_iter, entropy_tol=entropy_tol,
                                              streak=streak,
                                              threshold_p_lo=threshold_p_lo,
                                              threshold_p_hi=threshold_p_hi,
                                              threshold_p_tol=threshold_p_tol,
                                              compute_threshold=False)
            evaluations += 1
            if trial_objective.penalty >= PENALTY_NAN_INF:
                death_pool.append([float(value) for value in trial])
            replaced = False
            if objective_compare(trial_objective, objectives[index]) < 0:
                population[index] = trial
                objectives[index] = trial_objective
                replaced = True
            trials.append({
                "i": index, "r1": r1, "r2": r2, "r3": r3, "replaced": replaced,
                "trial_objective": record_to_dict(trial_objective),
            })
        best_index = _best_of(population, objectives)
        gen_times.append(time.time() - gen_start)
        transcript.append({
            "generation": generation,
            "evaluations_so_far": evaluations,
            "best_index": best_index,
            "best_objective": record_to_dict(objectives[best_index]),
            "best_lambda": decode_vector(population[best_index]),
            "trials": trials,
            "death_pool_count": len(death_pool),
        })
        if out_dir is not None:
            _write_checkpoint(out_dir, params, generation, evaluations, population,
                              objectives, best_index, death_pool, transcript)
        if max_evaluations is not None and evaluations >= max_evaluations:
            stop_reason = "max_evaluations_reached"
            break
    elapsed = time.time() - started_at

    best_index = _best_of(population, objectives)
    eligible: list[dict[str, Any]] = []
    for index in range(pop_size):
        record = objectives[index]
        if record.penalty > 0.0 or not record.entropy_converged:
            continue
        entry = record_to_dict(record)
        entry["population_index"] = index
        entry["lambda"] = decode_vector(population[index])
        eligible.append(entry)
    if compute_threshold and eligible:
        for entry in eligible:
            lambda_edge = entry["lambda"]
            record = evaluate_candidate(lambda_edge, q, rate, p_gate,
                                        seed=search_seed, n_samples=n_samples,
                                        max_iter=max_iter, entropy_tol=entropy_tol,
                                        streak=streak,
                                        threshold_p_lo=threshold_p_lo,
                                        threshold_p_hi=threshold_p_hi,
                                        threshold_p_tol=threshold_p_tol,
                                        compute_threshold=True)
            entry["threshold_proxy"] = record.threshold_proxy
        eligible.sort(key=lambda entry: (-float("inf") if entry["threshold_proxy"] is None
                                         else -entry["threshold_proxy"],
                                         tuple(entry["canonical_tuple"])))
    if out_dir is not None:
        final = {
            "schema": "v10_de_search_run_complete_v1",
            "params": params,
            "stop_reason": stop_reason,
            "generations_completed": generation,
            "evaluations": evaluations,
            "wall_clock_seconds": elapsed,
            "best_index": best_index,
            "best_objective": record_to_dict(objectives[best_index]),
            "best_lambda": decode_vector(population[best_index]),
            "eligible_candidates": eligible,
            "death_pool_size": len(death_pool),
        }
        with open(complete_marker, "w", encoding="utf-8") as handle:
            json.dump(final, handle, indent=2, sort_keys=True)
    return {
        "schema": "v10_de_search_results_v1",
        "params": params,
        "stop_reason": stop_reason,
        "generations_completed": generation,
        "evaluations": evaluations,
        "wall_clock_seconds": elapsed,
        "mean_seconds_per_generation": (float(np.mean(gen_times)) if gen_times else None),
        "best_index": best_index,
        "best_objective": record_to_dict(objectives[best_index]),
        "best_lambda": decode_vector(population[best_index]),
        "eligible_candidates": eligible,
        "death_pool_size": len(death_pool),
        "checkpoint_files": _list_checkpoints(out_dir),
    }


def _initial_state(search_seed: int, pop_size: int, params: Mapping[str, Any], *,
                   resume: bool, out_dir: str | None):
    if resume:
        checkpoints = _list_checkpoints(out_dir)
        if not checkpoints:
            raise ValueError("resume requested but no checkpoint found")
        checkpoint_path = checkpoints[-1]
        with open(checkpoint_path, encoding="utf-8") as handle:
            state = json.load(handle)
        saved_params = state["params"]
        for key in ("q", "p_gate", "rate", "search_seed", "pop_size", "max_gen",
                    "F", "CR", "n_samples", "max_iter", "entropy_tol", "streak"):
            if saved_params[key] != params[key]:
                raise ValueError(f"resume parameter mismatch for {key}")
        population = np.asarray(state["population"], dtype=np.float64)
        objectives = [record_from_dict(record) for record in state["objectives"]]
        generation = int(state["generation"])
        evaluations = int(state["evaluations"])
        best_index = int(state["best_index"])
        death_pool: list[list[float]] = [list(entry) for entry in state["death_pool"]]
        transcript = list(state["transcript"])
        return population, objectives, generation, evaluations, best_index, death_pool, transcript
    population = init_population(pop_size, search_seed)
    objectives: list[ObjectiveRecord] = []
    evaluations = 0
    for index in range(pop_size):
        objectives.append(evaluate_vector(population[index], params["q"], params["rate"],
                                          params["p_gate"], seed=search_seed,
                                          n_samples=params["n_samples"],
                                          max_iter=params["max_iter"],
                                          entropy_tol=params["entropy_tol"],
                                          streak=params["streak"],
                                          threshold_p_lo=params["threshold_p_lo"],
                                          threshold_p_hi=params["threshold_p_hi"],
                                          threshold_p_tol=params["threshold_p_tol"],
                                          compute_threshold=False))
        evaluations += 1
    best_index = _best_of(population, objectives)
    return population, objectives, 0, evaluations, best_index, [], []


def _best_of(population: np.ndarray, objectives: list[ObjectiveRecord]) -> int:
    best = 0
    for index in range(1, len(objectives)):
        if objective_compare(objectives[index], objectives[best]) < 0:
            best = index
    return best


def _write_checkpoint(out_dir: str, params: Mapping[str, Any], generation: int,
                      evaluations: int, population: np.ndarray,
                      objectives: list[ObjectiveRecord], best_index: int,
                      death_pool: list[list[float]], transcript: list[dict[str, Any]]) -> None:
    state = {
        "schema": "v10_de_checkpoint_v1",
        "params": dict(params),
        "generation": generation,
        "evaluations": evaluations,
        "population": [[float(value) for value in row] for row in population],
        "objectives": [record_to_dict(record) for record in objectives],
        "best_index": best_index,
        "death_pool": death_pool,
        "transcript": transcript,
    }
    path = os.path.join(out_dir, f"checkpoint_gen_{generation:04d}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)


def _list_checkpoints(out_dir: str | None) -> list[str]:
    if out_dir is None or not os.path.isdir(out_dir):
        return []
    names = sorted(name for name in os.listdir(out_dir)
                   if name.startswith("checkpoint_gen_") and name.endswith(".json"))
    return [os.path.join(out_dir, name) for name in names]
