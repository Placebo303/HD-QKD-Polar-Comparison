"""V9 scalable full-vector GF(1024) QSC Monte-Carlo density evolution kernel
(``formal-nonbinary-ldpc-v9-gf1024-long-ir``, additive layer).

Frozen semantics (V9-10 / spec V9-1, V9-2):

- Every message is a full length-q probability vector (q a power of two,
  2 <= q <= 1024; production q = 1024).  A scalar reliability surrogate is
  forbidden.
- Probability-domain messages with fail-closed normalization: inputs reject
  NaN/Inf/negative/zero mass; computed products are floored at ``_FLOOR =
  1e-300`` before normalizing (the same floor as the accepted V7 exact
  full-vector DE) and normalization fails closed on non-finite or
  non-positive total mass.
- ``fwht_batched`` is an own unnormalized XOR-order Walsh-Hadamard transform
  along the last axis, vectorized over the leading axes (the accepted
  butterfly pattern, implemented here in full; it MUST NOT and does not
  import any earlier-stage WHT routine).
- ``check_update_fft`` is the coefficient-correct check convolution: scale
  each message by its edge coefficient (``scaled[c (x) s] = msg[s]`` using the
  accepted field tables), batched WHT, pointwise spectra product excluding
  the target edge, inverse WHT (``/q``), then the syndrome shift
  ``outgoing[s] = conv[syndrome XOR c_t (x) s]``, normalized.  It must agree
  with the independent V8 direct oracle ``oracle_check_update_dense`` within
  the frozen tolerance 1e-9 at q=4/8/32 and bounded q=1024 (V8 is a test-only
  import; this module never imports V8).
- ``variable_update_mcde`` / ``belief_update_mcde`` / ``check_update_mcde``
  sample the exact edge-view degree per sample, draw iid rows from the other
  population, and update with a fresh QSC channel term (variable/belief).
  The check update is a batched pairwise WHT convolution (all-unity
  coefficients, zero syndrome — the DE check-node message).  RNG draw order
  (frozen): degrees first, then one ``rng.integers(0, N, N)`` draw per
  product/convolution slot, exactly like the accepted V8 MC-DE.
- ``run_mcde`` is a deterministic seeded PCG64 run with the frozen iteration
  order variable -> check -> belief; the observable is the mean base-q message
  entropy of the check population, and the run converges when
  ``entropy < entropy_tol`` for ``streak`` consecutive iterations.
- ``threshold_binary_search`` is the deterministic binary probe of the DE
  threshold proxy.

This module imports only ``numpy``, the standard library, and the accepted
field tables (``nonbinary_field.GF2mField``).  It never reads frame data and
never executes a decoder.
"""
from __future__ import annotations

import math
from numbers import Integral
from typing import Any, Mapping

import numpy as np

from .nonbinary_field import GF2mField

__all__ = [
    "fwht_batched",
    "check_update_fft",
    "parse_degree_hist",
    "qsc_channel_message",
    "variable_update_mcde",
    "check_update_mcde",
    "belief_update_mcde",
    "entropy_base_q",
    "run_mcde",
    "threshold_binary_search",
]

#: Positivity floor for probability-domain products (V7 exact-DE convention).
_FLOOR = 1e-300
#: Upper bound on any degree in an edge-perspective histogram.
DEGREE_MAX = 64
#: Tolerance for "normalized" input message rows.
_NORM_TOL = 1e-9


# --------------------------------------------------------------------------- #
# Walsh-Hadamard transform
# --------------------------------------------------------------------------- #


def fwht_batched(values: Any) -> np.ndarray:
    """Unnormalized XOR-order WHT along the last axis, vectorized over the
    leading axes (own implementation of the accepted butterfly).

    ``q = values.shape[-1]`` must be a power of two >= 2; the result is
    ``WHT(f)`` with ``WHT(WHT(f)) = q * f``.
    """
    out = np.asarray(values, dtype=np.float64)
    if out.ndim < 1:
        raise ValueError("fwht_batched requires at least one axis")
    q = out.shape[-1]
    if q < 2 or q & (q - 1):
        raise ValueError("last axis size must be a power of two >= 2")
    if not np.all(np.isfinite(out)):
        raise ValueError("fwht_batched inputs must be finite")
    out = out.copy()
    width = 1
    while width < q:
        paired = out.reshape(-1, 2 * width)
        left = paired[:, :width].copy()
        right = paired[:, width:].copy()
        paired[:, :width] = left + right
        paired[:, width:] = left - right
        width *= 2
    return out


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


# --------------------------------------------------------------------------- #
# channel and validation helpers
# --------------------------------------------------------------------------- #


def _qint(q: Any) -> int:
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1) \
            or int(q) > 1024:
        raise ValueError("V9 requires a power-of-two GF(q) with 2 <= q <= 1024")
    return int(q)


def _validate_field(field: Any) -> GF2mField:
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    _qint(field.q)
    return field


def _validate_qvec(message: Any, q: int, name: str) -> np.ndarray:
    """Fail-closed probability-vector validation: shape (q,), finite,
    non-negative, positive total mass, normalized to 1 within 1e-9."""
    vector = np.asarray(message, dtype=np.float64)
    if vector.shape != (q,):
        raise ValueError(f"{name} must be a length-{q} vector")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must be finite")
    if np.any(vector < 0.0):
        raise ValueError(f"{name} must be non-negative")
    total = float(vector.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError(f"{name} must have positive total mass")
    if abs(total - 1.0) > _NORM_TOL:
        raise ValueError(f"{name} must be normalized (sums to 1)")
    return vector


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


def _normalize_rows_fc(pop: np.ndarray, name: str) -> np.ndarray:
    """Fail-closed row normalization with the 1e-300 floor (products may carry
    sub-floor or tiny roundoff negatives; meaningful negatives are rejected)."""
    if not np.all(np.isfinite(pop)):
        raise ValueError(f"{name}: non-finite mass")
    if np.any(pop < -1e-12):
        raise ValueError(f"{name}: negative mass")
    floored = np.maximum(pop, _FLOOR)
    sums = floored.sum(axis=1, keepdims=True)
    if not np.all(np.isfinite(sums)) or np.any(sums <= 0.0):
        raise ValueError(f"{name}: zero or non-finite total mass")
    return floored / sums


def _normalize_qvec_fc(values: np.ndarray, name: str) -> np.ndarray:
    """Fail-closed normalization of a single length-q vector (floor 1e-300)."""
    if values.ndim != 1:
        raise ValueError(f"{name} must be a 1-D vector")
    if not np.all(np.isfinite(values)):
        raise ValueError(f"{name}: non-finite mass")
    if np.any(values < -1e-12):
        raise ValueError(f"{name}: negative mass")
    floored = np.maximum(values, _FLOOR)
    total = float(floored.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError(f"{name}: zero or non-finite total mass")
    return floored / total


def qsc_channel_message(q: int, p: float) -> np.ndarray:
    """QSC channel message for received symbol 0: ``[1-p, p/(q-1), ...]``."""
    q = _qint(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1.0) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    p = float(p)
    vector = np.full(q, p / (q - 1.0), dtype=np.float64)
    vector[0] = 1.0 - p
    return vector


# --------------------------------------------------------------------------- #
# coefficient-correct check convolution (WHT route)
# --------------------------------------------------------------------------- #


def _scale_message_by_coefficient(field: GF2mField, message: np.ndarray,
                                  coefficient: int) -> np.ndarray:
    """``scaled[c (x) s] = msg[s]`` — coefficient scaling by field mul."""
    scaled = np.zeros(field.q, dtype=np.float64)
    for symbol in range(field.q):
        scaled[field.mul(coefficient, symbol)] = message[symbol]
    return scaled


def _validate_coefficient(field: GF2mField, coefficient: Any) -> int:
    field.mul(coefficient, 0)  # raises on non-Integral / out-of-domain
    value = int(coefficient)
    if value == 0:
        raise ValueError("check coefficients must be nonzero")
    return value


def check_update_fft(messages: Any, coefficients: Any, target: int, syndrome: int,
                     field: GF2mField) -> np.ndarray:
    """Coefficient-correct check-to-variable update via the WHT (GF(2^m)-exact).

    ``outgoing[v]`` is proportional to the mass of configurations where
    ``sum_{j != t} c_j (x) x_j = syndrome XOR (c_t (x) v)`` over the
    coefficient-scaled incoming probability vectors: scale by the coefficient
    permutation, batched WHT, pointwise spectra product excluding the target,
    inverse WHT ``/q``, syndrome shift ``outgoing[s] = conv[syndrome XOR
    c_t (x) s]``, then fail-closed normalization (floor 1e-300).  This is the
    FFT-QSPA route; it must agree with the independent V8 dense oracle within
    the frozen tolerance 1e-9 (tests).
    """
    field = _validate_field(field)
    q = field.q
    dc = len(messages)
    if dc < 2:
        raise ValueError("check update requires at least two messages")
    if isinstance(target, bool) or not isinstance(target, Integral) or not 0 <= int(target) < dc:
        raise ValueError("target outside the message range")
    target = int(target)
    syndrome = field.mul(1, syndrome)  # validates the syndrome symbol
    if len(coefficients) != dc:
        raise ValueError("coefficients must match the message count")
    scaled: list[np.ndarray] = []
    for index, (message, coefficient) in enumerate(zip(messages, coefficients)):
        vector = _validate_qvec(message, q, f"message[{index}]")
        coefficient = _validate_coefficient(field, coefficient)
        scaled.append(_scale_message_by_coefficient(field, vector, coefficient))
    others = [index for index in range(dc) if index != target]
    spectra = fwht_batched(np.stack(scaled))  # (dc, q)
    product = np.prod(spectra[others], axis=0)
    conv = fwht_batched(product) / q
    coefficient = int(coefficients[target])
    outgoing = np.empty(q, dtype=np.float64)
    for v in range(q):
        outgoing[v] = conv[field.add(syndrome, field.mul(coefficient, v))]
    return _normalize_qvec_fc(outgoing, "check update")


# --------------------------------------------------------------------------- #
# MC-DE update steps
# --------------------------------------------------------------------------- #


def check_update_mcde(v2c: Any, dc_degrees: Any, dc_probs: Any, rng: np.random.Generator,
                      q: int) -> np.ndarray:
    """Check-node update for an (N, q) incoming population.

    Per sample: sample the exact check degree, draw ``dc - 1`` iid incoming
    rows, XOR-convolve them via the batched WHT (all-unity coefficients, zero
    syndrome), floor and normalize.  RNG draw order (frozen): degrees first,
    then one ``rng.integers(0, N, N)`` draw per convolution slot.
    """
    n = v2c.shape[0]
    q = _qint(q)
    v2c = _validate_pop(v2c, n, q, "v2c")
    dc_degrees, dc_probs = parse_degree_hist(_as_mapping(dc_degrees, dc_probs),
                                             "dc_degrees", DEGREE_MAX)
    degrees = rng.choice(dc_degrees, size=n, p=dc_probs)
    draws = degrees - 1
    max_draws = int(draws.max())
    acc = np.ones((n, q), dtype=np.float64)  # spectrum of delta at 0 = all ones
    for draw in range(max_draws):
        mask = draws > draw
        incoming = v2c[rng.integers(0, n, size=n)]
        acc = np.where(mask[:, None], acc * fwht_batched(incoming), acc)
    conv = fwht_batched(acc) / q
    return _normalize_rows_fc(conv, "check update")


def variable_update_mcde(c2v: Any, dv_degrees: Any, dv_probs: Any, channel: Any,
                         rng: np.random.Generator, q: int) -> np.ndarray:
    """Variable-node update for an (N, q) check-message population.

    Per sample: sample the exact variable degree, multiply in a FRESH channel
    row and ``dv - 1`` iid incoming check rows pointwise, floor and normalize.
    RNG draw order (frozen): degrees first, then one ``rng.integers(0, N, N)``
    draw per product slot (channel rows are drawn by the caller).
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
    product = channel.copy()
    for draw in range(max_draws):
        mask = draws > draw
        incoming = c2v[rng.integers(0, n, size=n)]
        product = np.where(mask[:, None], product * incoming, product)
    return _normalize_rows_fc(product, "variable update")


def belief_update_mcde(c2v: Any, dv_degrees: Any, dv_probs: Any, channel: Any,
                       rng: np.random.Generator, q: int) -> np.ndarray:
    """Belief population: channel x all ``dv`` incident check rows, floored and
    normalized.  RNG draw order (frozen): degrees first, then one
    ``rng.integers(0, N, N)`` draw per product slot."""
    n = c2v.shape[0]
    q = _qint(q)
    c2v = _validate_pop(c2v, n, q, "c2v")
    channel = _validate_pop(channel, n, q, "channel")
    dv_degrees, dv_probs = parse_degree_hist(_as_mapping(dv_degrees, dv_probs),
                                             "dv_degrees", DEGREE_MAX)
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    product = channel.copy()
    draws = degrees
    max_draws = int(draws.max())
    for draw in range(max_draws):
        mask = draws > draw
        incoming = c2v[rng.integers(0, n, size=n)]
        product = np.where(mask[:, None], product * incoming, product)
    return _normalize_rows_fc(product, "belief update")


def _as_mapping(degrees: Any, probs: Any) -> dict[int, float]:
    return {int(degree): float(prob) for degree, prob in zip(degrees, probs)}


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
# deterministic runs
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
