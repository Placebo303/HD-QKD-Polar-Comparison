"""V8 full-vector q-ary QSC Monte-Carlo density evolution (additive reference
layer).

Every message is a length-q probability vector — never a scalar ratio.  The
check-node update is a direct pairwise XOR convolution (no Fourier / Walsh-
Hadamard transforms anywhere), and the only imports are ``numpy`` and the
standard library: this module must not import any V1-V7 module, and it does
not need the field tables at all (XOR convolution only needs the group
structure of GF(2^m), so ``q`` must be a power of two >= 2).

Frozen semantics (V8 spec):

- degree distributions are EDGE-perspective; the node-perspective conversion
  is a separately named, tested helper;
- the actual degree is sampled for every variable/check update (``_degree_mode
  = "sampled"``); ``"fixed_max"`` reproduces the old R2 behavior and exists
  only for golden regression detection;
- a fresh channel message enters every variable update (``_channel_mode =
  "fresh"``); ``"omitted"`` replaces it with the uniform vector and exists
  only for golden regression detection;
- the convergence observable is the mean message entropy in base q;
- all entry points fail closed (``ValueError``) on non-finite, negative, or
  zero-total mass, invalid histograms, and out-of-domain parameters;
- seeded populations make every run byte-for-byte reproducible.
"""
from __future__ import annotations

import math
from numbers import Integral
from typing import Any, Mapping

import numpy as np

__all__ = [
    "parse_degree_hist",
    "edge_to_node_hist",
    "node_to_edge_hist",
    "edge_mean_inverse",
    "concentrated_check_distribution",
    "reconstructed_rate",
    "qsc_channel_message",
    "xor_conv_pairwise",
    "check_update_mcde",
    "variable_update_mcde",
    "belief_update_mcde",
    "entropy_base_q",
    "run_mcde",
    "threshold_binary_search",
    "REPRODUCTION_Q",
    "REPRODUCTION_RATE",
    "REPRODUCTION_LAMBDA_PUBLISHED",
    "REPRODUCTION_LAMBDA_DEGREES",
    "REPRODUCTION_DET_PUBLISHED",
    "REPRODUCTION_TOL",
    "REPRODUCTION_N_SAMPLES",
    "REPRODUCTION_MAX_ITER",
    "REPRODUCTION_SEED",
    "REPRODUCTION_P_LO",
    "REPRODUCTION_P_HI",
    "REPRODUCTION_P_TOL",
    "REPRODUCTION_ENTROPY_TOL",
    "REPRODUCTION_STREAK",
    "REPRODUCTION_CITATION",
]

#: Upper bound on any degree in an edge-perspective histogram.
DEGREE_MAX = 64
#: Fraction tolerance for "normalized" histograms in the perspective helpers.
_SUM_TOL = 1e-9


# --------------------------------------------------------------------------- #
# degree-distribution helpers
# --------------------------------------------------------------------------- #


def parse_degree_hist(hist: Mapping[Any, Any], name: str,
                      degree_max: int) -> tuple[np.ndarray, np.ndarray]:
    """Validate a degree histogram and return ``(degrees int64, probs float64)``.

    Accepts a mapping ``degree -> positive finite weight`` (any positive sum;
    the weights are normalized here — this is documented for published rounded
    vectors whose entries do not sum to exactly 1).  Rejects empty maps,
    non-positive / non-finite weights, and degrees outside ``[1, degree_max]``.
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


def _hist_dict(degrees: np.ndarray, probs: np.ndarray) -> dict[int, float]:
    return {int(degree): float(prob) for degree, prob in zip(degrees, probs)}


def _require_sum_one(hist: Mapping[Any, Any], name: str) -> None:
    total = sum(float(value) for value in hist.values())
    if not math.isfinite(total) or abs(total - 1.0) > _SUM_TOL:
        raise ValueError(f"{name} weights must sum to 1 within {_SUM_TOL}")


def edge_to_node_hist(edge_hist: Mapping[Any, Any]) -> dict[int, float]:
    """Edge-perspective ``lambda_d`` -> node-perspective ``L_d = (lambda_d/d) /
    (sum_j lambda_j/j)``.  Rejects inputs whose weights do not sum to 1, and
    rejects non-positive or non-finite weights."""
    _validate_hist_entries(edge_hist, "edge_hist")
    _require_sum_one(edge_hist, "edge_hist")
    total = sum(float(value) / int(degree) for degree, value in edge_hist.items())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("edge_hist has invalid normalization total")
    return {int(degree): (float(value) / int(degree)) / total
            for degree, value in edge_hist.items()}


def node_to_edge_hist(node_hist: Mapping[Any, Any]) -> dict[int, float]:
    """Node-perspective ``L_d`` -> edge-perspective ``lambda_d = (d*L_d) /
    (sum_j j*L_j)``.  Rejects inputs whose weights do not sum to 1, and
    rejects non-positive or non-finite weights."""
    _validate_hist_entries(node_hist, "node_hist")
    _require_sum_one(node_hist, "node_hist")
    total = sum(int(degree) * float(value) for degree, value in node_hist.items())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("node_hist has invalid normalization total")
    return {int(degree): (int(degree) * float(value)) / total
            for degree, value in node_hist.items()}


def _validate_hist_entries(hist: Mapping[Any, Any], name: str) -> None:
    for degree, value in hist.items():
        if isinstance(degree, bool) or not isinstance(degree, Integral) or int(degree) < 1:
            raise ValueError(f"{name} degrees must be positive integers")
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(float(value)) or float(value) <= 0.0:
            raise ValueError(f"{name} requires positive finite weights")


def edge_mean_inverse(edge_hist: Mapping[Any, Any]) -> float:
    """``integral_0^1 lambda(x) dx = sum_d lambda_d / d`` (edge-perspective).

    Computed with the weights as given (a raw published vector is used
    directly); for a normalized histogram this equals the usual integral.
    """
    total = 0.0
    for degree, value in edge_hist.items():
        if isinstance(degree, bool) or not isinstance(degree, Integral) or int(degree) < 1:
            raise ValueError("edge_hist degrees must be positive integers")
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(float(value)) or float(value) <= 0.0:
            raise ValueError("edge_hist requires positive finite weights")
        total += float(value) / int(degree)
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("edge_hist has invalid integral")
    return float(total)


def concentrated_check_distribution(rate: float, lambda_edge: Mapping[Any, Any]) -> dict[str, float]:
    """Two-point concentrated check-degree distribution that solves the
    edge-perspective rate condition exactly.

    For edge-perspective degree distributions the ensemble rate is
    ``R = 1 - (sum_j rho_j/j) / (sum_i lambda_i/i)``, so the concentrated check
    distribution must satisfy ``sum_j rho_j/j = (1-R) * sum_i lambda_i/i``
    exactly.  With ``target = (1 - rate) * integral_lambda`` and
    ``dc = 1/target``, the unique two-point distribution
    ``{dc_lo: w_lo, dc_hi: w_hi}`` on the adjacent degrees ``dc_lo =
    floor(dc)``, ``dc_hi = dc_lo + 1`` that solves the equation has
    ``w_lo = (target - 1/dc_hi) / (1/dc_lo - 1/dc_hi)``, ``w_hi = 1 - w_lo``;
    an integer ``dc`` degenerates to the regular single check degree.  The old
    mean-matched weights (``w_lo = dc_hi - dc_mean``) only approximated this
    condition (relative error ~1e-4) and are replaced by the harmonic-exact
    weights (V8-60 audit finding).  ``dc_mean`` is now the node-perspective
    mean check degree ``1/target``, not the two-point weighted mean.  Raises
    when ``rate`` is non-finite, ``(1 - rate) <= 0``, the implied degree is
    ``< 2`` (a degree-1 check is meaningless), or the weights are negative.
    """
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(float(rate)):
        raise ValueError("rate must be finite")
    rate = float(rate)
    if (1.0 - rate) <= 0.0:
        raise ValueError("(1 - rate) must be positive")
    integral = edge_mean_inverse(lambda_edge)
    target = (1.0 - rate) * integral
    if not math.isfinite(target) or target <= 0.0:
        raise ValueError("target (1-rate)*integral_lambda must be positive and finite")
    dc = 1.0 / target
    if not math.isfinite(dc) or dc < 2.0:
        raise ValueError("implied mean check degree must be >= 2")
    d_lo = int(math.floor(dc))
    if d_lo < 2:
        raise ValueError("implied mean check degree must be >= 2")
    d_hi = d_lo + 1
    if abs(dc - d_lo) < 1e-12:
        # Integer mean: the concentrated distribution degenerates to a regular
        # check degree; the harmonic weights collapse to {d: 1.0}.
        w_lo, w_hi = 1.0, 0.0
    else:
        w_lo = (target - 1.0 / d_hi) / (1.0 / d_lo - 1.0 / d_hi)
        w_hi = 1.0 - w_lo
        if w_lo < 0.0 or w_hi < 0.0:
            raise ValueError("concentrated distribution weights must be non-negative")
    return {"dc_lo": float(d_lo), "dc_hi": float(d_hi), "w_lo": w_lo, "w_hi": w_hi,
            "dc_mean": dc, "integral_lambda": integral, "integral_rho": target,
            "rate_reconstructed": 1.0 - target / integral}


def reconstructed_rate(lambda_edge: Mapping[Any, Any], rho_edge: Mapping[Any, Any]) -> float:
    """Edge-perspective ensemble rate reconstructed from the degree
    distributions: ``R = 1 - (sum_j rho_j/j) / (sum_i lambda_i/i)``.

    Per-entry validation follows :func:`edge_mean_inverse` (positive integer
    degrees, positive finite weights); raises on invalid input or a
    non-positive/non-finite integral.
    """
    integral_lambda = edge_mean_inverse(lambda_edge)
    integral_rho = edge_mean_inverse(rho_edge)
    return 1.0 - integral_rho / integral_lambda


# --------------------------------------------------------------------------- #
# channel and convolution helpers
# --------------------------------------------------------------------------- #


def _qint(q: Any) -> int:
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1):
        raise ValueError("MC-DE requires a power-of-two GF(q) with q >= 2")
    return int(q)


def qsc_channel_message(q: int, p: float) -> np.ndarray:
    """QSC channel message for received symbol 0: ``[1-p, p/(q-1), ...]``.

    Validates the frozen open domain ``0 < p < (q-1)/q``.
    """
    q = _qint(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1.0) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    p = float(p)
    vector = np.full(q, p / (q - 1.0), dtype=np.float64)
    vector[0] = 1.0 - p
    return vector


def xor_conv_pairwise(a: Any, b: Any) -> np.ndarray:
    """Direct XOR convolution of two probability vectors (O(q^2)).

    Batch-aware: the last axis is the GF(q) symbol axis and any leading axes
    are broadcast; 1-D inputs return a 1-D result.
    """
    left = np.asarray(a, dtype=np.float64)
    right = np.asarray(b, dtype=np.float64)
    if left.ndim < 1 or right.ndim < 1:
        raise ValueError("inputs must be vectors or batches")
    q = left.shape[-1]
    if right.shape[-1] != q:
        raise ValueError("last axis sizes must match")
    if q < 2 or q & (q - 1):
        raise ValueError("last axis size must be a power of two >= 2")
    if not np.all(np.isfinite(left)) or not np.all(np.isfinite(right)):
        raise ValueError("inputs must be finite")
    scalar = left.ndim == 1 and right.ndim == 1
    aa = left.reshape((1,) + left.shape) if left.ndim == 1 else left
    bb = right.reshape((1,) + right.shape) if right.ndim == 1 else right
    lead = np.broadcast_shapes(aa.shape[:-1], bb.shape[:-1])
    aa = np.broadcast_to(aa, lead + (q,))
    bb = np.broadcast_to(bb, lead + (q,))
    out = np.zeros(lead + (q,), dtype=np.float64)
    for i in range(q):
        for j in range(q):
            out[..., i ^ j] += aa[..., i] * bb[..., j]
    return out[0] if scalar else out


def _normalize_rows(pop: np.ndarray, name: str) -> np.ndarray:
    """Fail-closed row normalization of an (N, q) population."""
    if not np.all(np.isfinite(pop)):
        raise ValueError(f"{name}: non-finite mass")
    if np.any(pop < 0.0):
        raise ValueError(f"{name}: negative mass")
    sums = pop.sum(axis=1, keepdims=True)
    if not np.all(np.isfinite(sums)) or np.any(sums <= 0.0):
        raise ValueError(f"{name}: zero or non-finite total mass")
    return pop / sums


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


def _validate_channel(channel: Any, n: int, q: int) -> np.ndarray:
    return _validate_pop(channel, n, q, "channel")


# --------------------------------------------------------------------------- #
# MC-DE update steps (every message is a length-q vector)
# --------------------------------------------------------------------------- #


def check_update_mcde(v2c: np.ndarray, dc_degrees: Any, dc_probs: Any, rng: np.random.Generator,
                      q: int, *, _degree_mode: str = "sampled") -> np.ndarray:
    """Check-node update for an (N, q) incoming population.

    Per sample: sample the check degree (or use ``dc_max`` for every sample in
    ``_degree_mode="fixed_max"``, the old R2 behavior), draw ``dc - 1`` iid
    incoming rows, XOR-convolve them pairwise, normalize.  Fail closed.

    RNG draw order (frozen): degrees first, then one ``rng.integers(0, N, N)``
    draw per convolution slot.
    """
    n = v2c.shape[0]
    q = _qint(q)
    v2c = _validate_pop(v2c, n, q, "v2c")
    dc_degrees, dc_probs = parse_degree_hist(_as_mapping(dc_degrees, dc_probs), "dc_degrees", DEGREE_MAX)
    if _degree_mode == "sampled":
        degrees = rng.choice(dc_degrees, size=n, p=dc_probs)
    elif _degree_mode == "fixed_max":
        degrees = np.full(n, int(dc_degrees.max()), dtype=np.intp)
    else:
        raise ValueError("unknown check degree mode")
    draws = degrees - 1
    acc = np.zeros((n, q), dtype=np.float64)
    acc[:, 0] = 1.0
    max_draws = int(draws.max())
    for draw in range(max_draws):
        mask = draws > draw
        incoming = v2c[rng.integers(0, n, size=n)]
        acc = np.where(mask[:, None], xor_conv_pairwise(acc, incoming), acc)
    return _normalize_rows(acc, "check update")


def variable_update_mcde(c2v: np.ndarray, dv_degrees: Any, dv_probs: Any, channel: np.ndarray,
                         rng: np.random.Generator, q: int, *, _channel_mode: str = "fresh",
                         _degree_mode: str = "sampled") -> np.ndarray:
    """Variable-node update for an (N, q) check-message population.

    Per sample: sample the variable degree (or ``dv_max`` in
    ``_degree_mode="fixed_max"``), multiply in a FRESH channel message
    (``_channel_mode="fresh"``; ``"omitted"`` uses the uniform vector so the
    channel term drops out), then pointwise-multiply ``dv - 1`` iid incoming
    check rows, normalize.  Fail closed.

    RNG draw order (frozen): degrees first, then channel symbols (drawn by the
    caller via :func:`run_mcde`), then one ``rng.integers(0, N, N)`` draw per
    product slot.
    """
    n = c2v.shape[0]
    q = _qint(q)
    c2v = _validate_pop(c2v, n, q, "c2v")
    channel = _validate_channel(channel, n, q)
    dv_degrees, dv_probs = parse_degree_hist(_as_mapping(dv_degrees, dv_probs), "dv_degrees", DEGREE_MAX)
    if _channel_mode == "fresh":
        product = channel.copy()
    elif _channel_mode == "omitted":
        product = np.full((n, q), 1.0 / q, dtype=np.float64)
    else:
        raise ValueError("unknown channel mode")
    if _degree_mode == "sampled":
        degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    elif _degree_mode == "fixed_max":
        degrees = np.full(n, int(dv_degrees.max()), dtype=np.intp)
    else:
        raise ValueError("unknown variable degree mode")
    draws = degrees - 1
    max_draws = int(draws.max())
    for draw in range(max_draws):
        mask = draws > draw
        incoming = c2v[rng.integers(0, n, size=n)]
        product = np.where(mask[:, None], product * incoming, product)
    return _normalize_rows(product, "variable update")


def belief_update_mcde(c2v: np.ndarray, dv_degrees: Any, dv_probs: Any, channel: np.ndarray,
                       rng: np.random.Generator, q: int) -> np.ndarray:
    """Belief population: channel x all ``dv`` incident check rows, normalized.

    RNG draw order (frozen): degrees first, then one ``rng.integers(0, N, N)``
    draw per product slot.
    """
    n = c2v.shape[0]
    q = _qint(q)
    c2v = _validate_pop(c2v, n, q, "c2v")
    channel = _validate_channel(channel, n, q)
    dv_degrees, dv_probs = parse_degree_hist(_as_mapping(dv_degrees, dv_probs), "dv_degrees", DEGREE_MAX)
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    product = channel.copy()
    draws = degrees
    max_draws = int(draws.max())
    for draw in range(max_draws):
        mask = draws > draw
        incoming = c2v[rng.integers(0, n, size=n)]
        product = np.where(mask[:, None], product * incoming, product)
    return _normalize_rows(product, "belief update")


def _as_mapping(degrees: Any, probs: Any) -> dict[int, float]:
    """Rebuild a mapping from parallel degree/prob arrays (internal use)."""
    return {int(degree): float(prob) for degree, prob in zip(degrees, probs)}


def entropy_base_q(pop: np.ndarray) -> float:
    """Mean row entropy in base q: ``mean over rows of -sum p*log_q(p)``
    (0 for a degenerate deterministic mass, base-q logarithm).  Zero-mass rows
    are not valid distributions and are rejected fail-closed."""
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
             streak: int = 20, _channel_mode: str = "fresh",
             _degree_mode: str = "sampled") -> dict:
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
        v2c = variable_update_mcde(c2v, dv_degrees, dv_probs, channel, rng, q,
                                   _channel_mode=_channel_mode, _degree_mode=_degree_mode)
        c2v = check_update_mcde(v2c, dc_degrees, dc_probs, rng, q, _degree_mode=_degree_mode)
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
        "channel_mode": _channel_mode, "degree_mode": _degree_mode,
        "lambda": {int(k): float(v) for k, v in lambda_edge.items()},
        "rho": {int(k): float(v) for k, v in rho_edge.items()},
    }


def threshold_binary_search(q: int, lambda_edge: Mapping[Any, Any], rho_edge: Mapping[Any, Any], *,
                            n_samples: int, max_iter: int, seed: int,
                            p_lo: float = 0.01, p_hi: float = 0.49,
                            p_tol: float = 0.0025) -> dict:
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
    if not math.isfinite(float(p_tol)) or float(p_tol) <= 0.0:
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
# frozen published-reproduction constants (frozen BEFORE the single run; see
# evidence/v8_literature_provenance.json and evidence/v8_muller2024_table1_extract.txt)
# --------------------------------------------------------------------------- #

REPRODUCTION_Q = 4
REPRODUCTION_RATE = 0.75
# Verbatim published polynomial coefficients (Table 1 row "0.75"): the keys are
# the polynomial EXPONENTS as printed in the paper, lambda(x) = sum lambda_d
# x^(d-1) per the paper's eq. 13, so the corresponding variable DEGREES are
# key + 1 (see REPRODUCTION_LAMBDA_DEGREES below and
# evidence/v8_muller2024_table1_extract.txt).
REPRODUCTION_LAMBDA_PUBLISHED = {
    1: 0.107, 3: 0.245, 6: 0.192, 9: 0.034, 18: 0.207, 25: 0.161, 27: 0.049,
}
#: The same distribution keyed by the effective variable DEGREES (exponent+1),
#: i.e. what the MC-DE actually samples.  Derived once from the published
#: constants; normalized inside parse_degree_hist.
REPRODUCTION_LAMBDA_DEGREES = {
    int(degree) + 1: float(weight) for degree, weight in REPRODUCTION_LAMBDA_PUBLISHED.items()
}
REPRODUCTION_DET_PUBLISHED = 0.069
# Frozen reproduction tolerance (V8-60 corrected, auditable arithmetic):
#   0.0005 (3-decimal published rounding of DET 0.069)
# + 0.00125 (binary-search half-step p_tol/2)
# + 0.005   (our MC-DE finite-sample threshold-estimate error at 100000 nodes)
# + 0.005   (paper MC-DE estimate error at its 100000 nodes)
# = 0.01175 <= 0.012  (frozen tolerance; replaces the invalid 0.005+0.003+0.0025=0.015 claim)
REPRODUCTION_TOL = 0.012
REPRODUCTION_N_SAMPLES = 100000
REPRODUCTION_MAX_ITER = 150
REPRODUCTION_SEED = 2026080418
REPRODUCTION_P_LO = 0.01
REPRODUCTION_P_HI = 0.12
REPRODUCTION_P_TOL = 0.0025
REPRODUCTION_ENTROPY_TOL = 0.01
REPRODUCTION_STREAK = 20

REPRODUCTION_CITATION = {
    "title": "Efficient Information Reconciliation for High-Dimensional Quantum Key Distribution",
    "authors": ["Ronny Müller", "Domenico Ribezzo", "Mujtaba Zahidy",
                "Leif Katsuo Oxenløwe", "Davide Bacco", "Søren Forchhammer"],
    "year": 2024,
    "venue": "Quantum Information Processing 23, 195 (2024)",
    "url": "https://arxiv.org/abs/2307.02225",
    "arxiv": "arXiv:2307.02225v2",
    "table": "Table 1",
    "section": "Section 3.1",
    "row": "0.75",
}
