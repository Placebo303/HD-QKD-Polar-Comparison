"""Bounded deterministic q-ary density evolution for ``nbldpc_formal_v7_r2_qsc_de``
(``formal-nonbinary-ldpc-v7-successor-ladder``, R2, V7-20).

Scientific identity (frozen, spec.md R2): the R2 selection is made by a
*faithful q-ary density evolution* whose equations are the exact FFT-QSPA
message-passing equations restricted to the symmetric (two-level) message
model, and that recursion is INDEPENDENTLY validated against published
small-field vectors:

- **q=2**: the two-level model is exact (there is only one wrong symbol), so
  the recursion is exactly the standard binary belief-propagation DE.  Its
  threshold reproduces the published binary-symmetric-channel threshold of the
  regular ``(3,6)`` ensemble (p* ~= 0.084, Richardson--Urbanke 2001) and the
  published binary-erasure-channel thresholds of ``(3,6)`` / ``(3,4)`` /
  ``(4,8)`` / ``(4,6)`` (epsilon* ~= 0.4294 / 0.6473 / 0.3834 / 0.5061, the
  published regular-ensemble BEC table, e.g. arxiv cs/0410019 Table 1) via
  the erasure-domain special case of the same recursion.
- **q=4**: the two-level check-update convolution is verified EXACTLY against
  exhaustive enumeration over GF(4) for every small check degree, and the
  full two-level DE threshold is compared against an exact full-vector
  (unapproximated) Monte-Carlo DE at q=4 (same channel, same degree
  distributions, same decoder equations); agreement is required within a
  frozen tolerance.
- The production q=1024 selection uses the same two-level recursion (the
  frozen deterministic approximation), whose complexity is independent of q
  (the recursion tracks only the ratio of the mass on the true symbol to the
  mass on any wrong symbol).

Model (frozen):

- QSC(p) with symbol error probability ``p`` on GF(q) (error XOR, each nonzero
  error value equally likely).  Channel message ratios: ``R_hi = (1-p)(q-1)/p``
  with probability ``1-p`` (no error) and ``R_lo = p(q-1)/(q-1-p)`` with
  probability ``p`` (error), the projected two-level ratios of the exact QSC
  posterior.
- **Variable update**: ``R_v = R_ch * prod(R_i)`` over the ``d_v - 1`` other
  incident check messages (exact for two-level messages).
- **Check update**: exact GF(q) sum-distribution of ``d_c - 1`` independent
  two-level inputs; the convolution ``(P0, P1) * (alpha, beta)`` is closed:
  ``P0' = P0*a + (q-1)*P1*b``, ``P1' = P0*b + P1*a + (q-2)*P1*b``, with
  ``a = R/(R+q-1)``, ``b = 1/(R+q-1)``; ``R_out = P0/P1``.
- Belief: ``R_bel = R_ch * prod_{i=1}^{d_v} R_i``; the decision is the
  transmitted symbol iff ``R_bel > 1``.
- The recursion is a **deterministic Monte-Carlo density evolution**: every
  iteration draws exactly ``n_samples`` variable-edge and check-edge messages
  iid from the previous iteration's empirical density using a fixed-seed
  PCG64 generator, so the whole computation is reproducible byte-for-byte.

Bound (frozen): the population search evaluates AT MOST 32 candidate
variable-degree distributions (degrees 2..8, mean check degree <= 12) in a
canonical deterministic order and selects the distribution with the highest
DE threshold proxy (ties broken by canonical order).  The selected
distribution is the one frozen into ``nonbinary_v7_r2_codebook``.

The module is pure and deterministic (numpy only).  It never touches the
filesystem and never reads any frame or channel data beyond the frozen
stratum ``p``.
"""
from __future__ import annotations

import math
from numbers import Integral
from typing import Any, Mapping, Sequence

import numpy as np

DEGREE_MIN = 2
DEGREE_MAX = 8
MAX_CANDIDATES = 32
MEAN_CHECK_DEGREE_MAX = 12.0
# Check degrees can reach ceil(mean check degree) + 1 = 13 (mean <= 12).
CHECK_DEGREE_MAX = MEAN_CHECK_DEGREE_MAX + 1
_Q = 1024
_N = 1024
# Frozen one-time search budgets for the q=1024 selection (bounded).
_SEARCH_N_SAMPLES = 5000
_SEARCH_MAX_ITER = 800
_SEARCH_P_TOL = 0.001
_SEARCH_SEED = 2026080402
# Validation budgets (small fields, tests).
_VAL_N_SAMPLES = 50000
_VAL_MAX_ITER = 2000
# Frozen convergence criterion: an error probability below this at the final
# iteration means the channel is below the DE threshold (empirically 0 once
# the empirical density converges).
_CONV_TOL = 1e-4
# Ratio clamps: values beyond these are decisively known/erased.
_R_MIN, _R_MAX = 1e-12, 1e12
# Positivity floor for the exact full-vector DE (probability-domain products
# underflow to zero; the floor keeps the exact recursion numerically stable
# and is far below any decision-relevant mass).
_FLOOR = 1e-300

# Published small-field validation vectors (frozen, see module docstring).
# BEC values are the published regular-ensemble thresholds: (3,6)=0.4294,
# (3,4)=0.6473, (4,8)=0.3834, (4,6)=0.5061 (e.g. arxiv cs/0410019 Table 1).
# NOTE (V7-20 engineering): the value 0.5061 belongs to the (4,6) ensemble;
# the (3,4) threshold is 0.6474, not 0.5061.
PUBLISHED_BSC_THRESHOLDS = {(3, 6): 0.084}
PUBLISHED_BEC_THRESHOLDS = {(3, 6): 0.429438, (3, 4): 0.647426, (4, 8): 0.383441,
                            (4, 6): 0.506132}
_BSC_TOL = 0.004
_BEC_TOL = 0.002
_Q4_EXACT_DE_TOL = 0.03


def _clamp(ratio: np.ndarray) -> np.ndarray:
    return np.clip(ratio, _R_MIN, _R_MAX)


def check_ratio(ratios: Sequence[float], q: int) -> float:
    """Exact GF(q) check-update ratio of two-level inputs (the DE recursion).

    ``R_out = P0/P1`` where ``(P0, P1)`` is the GF(q) sum distribution of the
    ``d_c - 1`` independent two-level input messages folded by the closed
    convolution.  Returns a clamped ratio; fails closed on invalid input.
    """
    q = _qint(q)
    if isinstance(ratios, (str, bytes)) or not hasattr(ratios, "__iter__"):
        raise ValueError("check_ratio requires an iterable of ratios")
    values = [float(r) for r in ratios]
    if not values or any(not math.isfinite(r) or r <= 0.0 for r in values):
        raise ValueError("check_ratio requires positive finite ratios")
    p0, p1 = 1.0, 0.0
    for ratio in values:
        alpha = ratio / (ratio + q - 1.0)
        beta = 1.0 / (ratio + q - 1.0)
        p0, p1 = p0 * alpha + (q - 1.0) * p1 * beta, \
                 p0 * beta + p1 * alpha + (q - 2.0) * p1 * beta
    if not math.isfinite(p0) or not math.isfinite(p1):
        raise ValueError("check_ratio convolution diverged")
    if p1 <= 0.0:
        return _R_MAX
    return float(np.clip(p0 / p1, _R_MIN, _R_MAX))


def check_ratio_bruteforce(ratios: Sequence[float], q: int) -> float:
    """Independent exhaustive GF(q) enumeration of the same check update.

    For every input symbol combination over GF(q), accumulate the product of
    the input masses that satisfy the XOR check with all-unity coefficients
    and zero syndrome; ``R_out = mass(0) / mass(any nonzero)`` (nonzero
    masses are equal by symmetry).  Only feasible for tiny q (tests).
    """
    q = _qint(q)
    values = [float(r) for r in ratios]
    if not values or any(not math.isfinite(r) or r <= 0.0 for r in values):
        raise ValueError("check_ratio_bruteforce requires positive finite ratios")
    if q > 8 or len(values) > 4:
        raise ValueError("brute-force check update is bounded to q<=8, degree<=5")
    masses = [np.full(q, 1.0 / (r + q - 1.0), dtype=np.float64) for r in values]
    for index, ratio in enumerate(values):
        masses[index][0] = ratio / (ratio + q - 1.0)
    total = np.zeros(q, dtype=np.float64)
    for combo in np.ndindex(*((q,) * len(values))):
        # mass for the target symbol y is the sum over combos whose XOR is y.
        xorsum = 0
        for x in combo:
            xorsum ^= int(x)
        contribution = 1.0
        for index, symbol in enumerate(combo):
            contribution *= masses[index][symbol]
        total[xorsum] += contribution
    zero_mass = float(total[0])
    nonzero_mass = float(total[1:].mean())
    if nonzero_mass <= 0.0:
        return _R_MAX
    return float(np.clip(zero_mass / nonzero_mass, _R_MIN, _R_MAX))


def variable_ratio(channel_ratio: float, check_ratios: Sequence[float]) -> float:
    """Variable-node update: the ratio product over the channel and the other
    incident check messages (exact for two-level messages)."""
    value = float(channel_ratio)
    for ratio in check_ratios:
        value *= float(ratio)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("variable_ratio diverged")
    return float(np.clip(value, _R_MIN, _R_MAX))


def channel_ratio_distribution(q: int, p: float) -> tuple[np.ndarray, np.ndarray]:
    """Projected QSC channel message ratios: ``(values, probabilities)``."""
    q = _qint(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1.0) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    p = float(p)
    r_hi = (1.0 - p) * (q - 1.0) / p
    r_lo = p * (q - 1.0) / ((q - 1.0) - p)
    return (np.array([r_hi, r_lo], dtype=np.float64),
            np.array([1.0 - p, p], dtype=np.float64))


def _qint(q: Any) -> int:
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1):
        raise ValueError("DE requires a power-of-two GF(q) with q >= 2")
    return int(q)


def _degree_histogram(hist: Mapping[Any, Any], name: str,
                      degree_max: int = DEGREE_MAX) -> tuple[np.ndarray, np.ndarray]:
    if not isinstance(hist, Mapping):
        raise ValueError(f"{name} must be a mapping")
    degrees, weights = [], []
    for key, value in hist.items():
        degree = int(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) \
                or not math.isfinite(float(value)) or float(value) <= 0.0:
            raise ValueError(f"{name} requires positive weights")
        if degree < DEGREE_MIN or degree > degree_max:
            raise ValueError(f"{name} degree outside {DEGREE_MIN}..{degree_max}")
        degrees.append(degree)
        weights.append(float(value))
    if not degrees:
        raise ValueError(f"{name} is empty")
    order = np.argsort(degrees)
    return (np.asarray(degrees, dtype=np.intp)[order],
            np.asarray(weights, dtype=np.float64)[order] / sum(weights))


def implied_check_histogram(n: int, m: int, mean_check_degree: float) -> dict[str, float]:
    """Deterministic two-point check-degree histogram implied by ``E = n*dv_mean``
    edges over ``m`` checks (``dc_lo``/``dc_hi`` counts)."""
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) <= 0:
        raise ValueError("n must be a positive integer")
    if isinstance(m, bool) or not isinstance(m, Integral) or int(m) <= 0:
        raise ValueError("m must be a positive integer")
    if not math.isfinite(float(mean_check_degree)):
        raise ValueError("mean_check_degree must be finite")
    n, m = int(n), int(m)
    edges = n * float(mean_check_degree)
    if edges > m * MEAN_CHECK_DEGREE_MAX:
        raise ValueError("mean check degree exceeds the frozen bound 12")
    dc_lo = int(math.floor(edges / m))
    if dc_lo < 2:
        dc_lo = 2
    dc_hi = dc_lo + 1
    extra = int(round(edges)) - m * dc_lo
    if extra < 0:
        extra = 0
    if extra > m:
        extra = m
    return {str(dc_lo): float(m - extra), str(dc_hi): float(extra)}


def two_level_de(q: int, dv_hist: Mapping[Any, Any], dc_hist: Mapping[Any, Any],
                 p: float, *, n_samples: int, max_iter: int,
                 seed: int) -> tuple[list[float], np.ndarray]:
    """Deterministic Monte-Carlo two-level q-ary DE.

    Returns ``(error_probs, final_check_ratios)``; ``error_probs[i]`` is the
    empirical belief-error fraction after iteration ``i+1``.  ``dc_hist`` is
    the check-DEGREE distribution (each check update draws ``d_c - 1``
    variable messages).  Byte-for-byte reproducible for a fixed seed.
    """
    q = _qint(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1.0) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    if isinstance(n_samples, bool) or not isinstance(n_samples, Integral) or int(n_samples) < 100:
        raise ValueError("n_samples must be an integer >= 100")
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral) or not 1 <= int(max_iter) <= 10000:
        raise ValueError("max_iter must be an integer in 1..10000")
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    n_samples, max_iter, q = int(n_samples), int(max_iter), int(q)
    rng = np.random.default_rng(int(seed))
    dv_degrees, dv_probs = _degree_histogram(dv_hist, "dv_hist")
    dc_degrees, dc_probs = _degree_histogram(dc_hist, "dc_hist", degree_max=CHECK_DEGREE_MAX)
    channel_values, channel_probs = channel_ratio_distribution(q, p)
    dv_max = int(dv_degrees.max())
    dc_max = int(dc_degrees.max())

    # Initial check-to-variable messages: uniform (ratio 1) -> the first
    # variable update reduces to the channel message.
    check_samples = np.ones(n_samples, dtype=np.float64)
    error_probs: list[float] = []
    converged_streak = 0
    try:
        for _ in range(max_iter):
            # ---- variable update: R_v = R_ch * prod(d_v - 1 check ratios)
            degrees = rng.choice(dv_degrees, size=n_samples, p=dv_probs)
            channel = channel_values[rng.choice(2, size=n_samples, p=channel_probs)]
            variable = channel.copy()
            for draw in range(dv_max - 1):
                incoming = check_samples[rng.integers(0, n_samples, size=n_samples)]
                variable = np.where(degrees >= draw + 2, variable * incoming, variable)

            # ---- check update: R_c = P0/P1 over d_c - 1 variable messages
            c_degrees = rng.choice(dc_degrees, size=n_samples, p=dc_probs)
            p0 = np.ones(n_samples, dtype=np.float64)
            p1 = np.zeros(n_samples, dtype=np.float64)
            for draw in range(dc_max - 1):
                incoming = variable[rng.integers(0, n_samples, size=n_samples)]
                alpha = incoming / (incoming + q - 1.0)
                beta = 1.0 / (incoming + q - 1.0)
                p0_new = p0 * alpha + (q - 1.0) * p1 * beta
                p1_new = p0 * beta + p1 * alpha + (q - 2.0) * p1 * beta
                mask = c_degrees >= draw + 2
                p0 = np.where(mask, p0_new, p0)
                p1 = np.where(mask, p1_new, p1)
            ratio = np.full(n_samples, _R_MAX, dtype=np.float64)
            positive = p1 > 0.0
            ratio[positive] = p0[positive] / p1[positive]
            check_samples = _clamp(ratio)

            # ---- belief: R_bel = R_ch * prod(d_v check ratios)
            belief = check_samples[rng.integers(0, n_samples, size=n_samples)]
            for _ in range(dv_max - 1):
                belief *= check_samples[rng.integers(0, n_samples, size=n_samples)]
            belief = _clamp(belief)
            error = float(np.mean(belief < 1.0))
            error_probs.append(error)
            # Early exit once the empirical density has converged (the error
            # is exactly zero for 20 consecutive iterations): below-threshold
            # probes are the majority and finish in a few tens of iterations.
            converged_streak = converged_streak + 1 if error < _CONV_TOL else 0
            if converged_streak >= 20:
                break
    except (ArithmeticError, FloatingPointError, ValueError):
        raise ValueError("DE recursion failed numerically")
    return error_probs, check_samples


def de_converged(error_probs: Sequence[float], tol: float = _CONV_TOL) -> bool:
    if not error_probs:
        return False
    return float(error_probs[-1]) < tol


def threshold_probe(q: int, dv_hist: Mapping[Any, Any], dc_hist: Mapping[Any, Any],
                    p: float, *, n_samples: int, max_iter: int, seed: int) -> dict[str, Any]:
    """One bounded DE threshold probe: returns converged flag and the final
    error probability (deterministic)."""
    errors, _ = two_level_de(q, dv_hist, dc_hist, p, n_samples=n_samples,
                             max_iter=max_iter, seed=seed)
    return {"p": float(p), "converged": de_converged(errors),
            "final_error_probability": float(errors[-1])}


def threshold_binary_search(q: int, dv_hist: Mapping[Any, Any], dc_hist: Mapping[Any, Any],
                            *, n_samples: int, max_iter: int, seed: int,
                            p_tol: float = _SEARCH_P_TOL, p_lo: float = 0.001,
                            p_hi: float = 0.49) -> dict[str, Any]:
    """Deterministic binary search for the DE threshold proxy p*.

    ``p*`` is the largest p (to ``p_tol``) for which the DE error probability
    converges to zero.  The probe order is deterministic (a fixed binary
    search sequence from fixed endpoints), so the result is reproducible.
    """
    q = _qint(q)
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    seed = int(seed)
    if not 0.0 < float(p_lo) < float(p_hi) < (q - 1.0) / q:
        raise ValueError("invalid probe range")
    lo, hi = float(p_lo), float(p_hi)
    probes = []
    while hi - lo > p_tol:
        mid = (lo + hi) / 2.0
        result = threshold_probe(q, dv_hist, dc_hist, mid, n_samples=n_samples,
                                 max_iter=max_iter, seed=seed)
        probes.append(result)
        if result["converged"]:
            lo = mid
        else:
            hi = mid
    return {"threshold_proxy": (lo + hi) / 2.0, "p_lo": lo, "p_hi": hi,
            "converged_at_lo": probes[-1]["converged"] if probes else None,
            "probe_count": len(probes), "probes": probes}


def candidate_distributions(n: int, m: int, *, max_candidates: int = MAX_CANDIDATES,
                            degree_min: int = DEGREE_MIN,
                            degree_max: int = DEGREE_MAX) -> list[dict[str, int]]:
    """Deterministic canonical population of at most ``max_candidates``
    variable-degree distributions over degrees 2..8 with mean check degree
    <= 12: regular distributions first, then two-point mixtures ordered by
    (d1, d2, fraction), deduplicated, capped at ``max_candidates``.

    Every returned distribution assigns whole column counts to n=1024 columns
    (fractions are quarters of n)."""
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) <= 0:
        raise ValueError("n must be a positive integer")
    if isinstance(m, bool) or not isinstance(m, Integral) or int(m) <= 0:
        raise ValueError("m must be a positive integer")
    if isinstance(max_candidates, bool) or not isinstance(max_candidates, Integral) \
            or not 1 <= int(max_candidates) <= 64:
        raise ValueError("max_candidates must be an integer in 1..64")
    n, m, max_candidates = int(n), int(m), int(max_candidates)
    limit = MEAN_CHECK_DEGREE_MAX * m / n
    seen: set[tuple[int, ...]] = set()
    candidates: list[dict[str, int]] = []

    def add(dist: dict[str, int]) -> None:
        if len(candidates) >= max_candidates:
            return
        key = tuple(sorted((int(d), int(c)) for d, c in dist.items()))
        if key in seen:
            return
        seen.add(key)
        candidates.append(dist)

    for degree in range(degree_min, degree_max + 1):
        if degree <= limit:
            add({str(degree): n})
    for d1 in range(degree_min, degree_max):
        for d2 in range(d1 + 1, degree_max + 1):
            for fraction in (0.25, 0.5, 0.75):
                mean = fraction * d1 + (1.0 - fraction) * d2
                if mean > limit:
                    continue
                count1 = int(round(fraction * n))
                add({str(d1): count1, str(d2): n - count1})
                if len(candidates) >= max_candidates:
                    return candidates
    return candidates


def _select_impl(p: float, q: int, n: int, m: int, *, n_samples: int, max_iter: int,
                 seed: int, max_candidates: int, p_tol: float) -> dict[str, Any]:
    """Bounded deterministic population search (shared by the frozen selection
    and the tests).  Evaluates at most ``max_candidates`` candidate variable-
    degree distributions by the DE threshold proxy and returns the winner."""
    q = _qint(q)
    if float(p) not in (0.20, 0.30):
        raise ValueError("stratum p mismatch")
    candidates = candidate_distributions(n, m, max_candidates=max_candidates)
    if not candidates or len(candidates) > max_candidates:
        raise ValueError("candidate population is out of the frozen bounds")
    evaluated: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for order, dist in enumerate(candidates):
        dv_mean = sum(int(d) * count for d, count in dist.items()) / float(n)
        dc_hist = implied_check_histogram(n, m, dv_mean)
        result = threshold_binary_search(q, dist, dc_hist, n_samples=n_samples,
                                         max_iter=max_iter, seed=seed + order, p_tol=p_tol)
        entry = {"order": order, "variable_distribution": dist,
                 "mean_variable_degree": dv_mean,
                 "implied_check_histogram": dc_hist,
                 "threshold_proxy": result["threshold_proxy"],
                 "probe_count": result["probe_count"]}
        evaluated.append(entry)
        if best is None or entry["threshold_proxy"] > best["threshold_proxy"]:
            best = entry
    assert best is not None
    return {"stratum_p": float(p), "q": q, "n": n, "m": m,
            "candidates_evaluated": len(evaluated), "candidate_cap": max_candidates,
            "selected": best, "candidates": evaluated}


def select_distribution(p: float, *, q: int = _Q, n: int = _N, m: int | None = None,
                        n_samples: int = _SEARCH_N_SAMPLES, max_iter: int = _SEARCH_MAX_ITER,
                        seed: int = _SEARCH_SEED, max_candidates: int = MAX_CANDIDATES,
                        p_tol: float = _SEARCH_P_TOL) -> dict[str, Any]:
    """Run the frozen bounded population search for one stratum and return the
    full deterministic record (the codebook freezes the selected entry)."""
    if m is None:
        m = int(math.ceil(1.15 * qary_entropy_bits(q, float(p)) / 10.0 * n))
    return _select_impl(float(p), q, n, int(m), n_samples=n_samples, max_iter=max_iter,
                        seed=seed, max_candidates=max_candidates, p_tol=p_tol)


def qary_entropy_bits(q: int, p: float) -> float:
    """Exact ``H_q(p) = h2(p) + p*log2(q-1)`` in bits per symbol."""
    q = _qint(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1.0) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    p = float(p)
    h2 = -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)
    return h2 + p * math.log2(q - 1)


def frozen_check_count(q: int, p: float, n: int = _N) -> int:
    """``ceil(1.15 * H_q(p) / 10 * n)`` — the frozen whole-check-count freeze.

    Exact values (V7-20 implementation note): p=.20 -> 321, p=.30 -> 458.
    """
    return int(math.ceil(1.15 * qary_entropy_bits(q, float(p)) / 10.0 * int(n)))


# ------------------------------------------------------------------ small-field
# validation vectors (independent of the q=1024 production path)


def binary_bec_threshold(dv: int, dc: int, *, tol: float = 1e-9,
                         max_iter: int = 20000) -> float:
    """Analytic erasure-domain DE threshold (the erasure special case of the
    same message-passing recursion): ``eps* = sup{eps : eps->0 under
    eps' = eps*(1-(1-eps)^(dc-1))^(dv-1)}``.

    Returns the published binary-erasure-channel threshold of the regular
    ``(dv, dc)`` ensemble to ``tol`` (deterministic bisection).
    """
    if isinstance(dv, bool) or not isinstance(dv, Integral) or isinstance(dc, bool) \
            or not isinstance(dc, Integral) or int(dv) < 2 or int(dc) < 2:
        raise ValueError("regular (dv, dc) with dv, dc >= 2 required")
    dv, dc = int(dv), int(dc)

    def converges(eps: float) -> bool:
        # The DE starts from the channel erasure probability itself; below the
        # threshold the erasure recursion decreases to 0, above it converges to
        # a positive fixed point (never below 1e-9).
        value = eps
        for _ in range(int(max_iter)):
            value = eps * (1.0 - (1.0 - value) ** (dc - 1)) ** (dv - 1)
        return value < 1e-9

    lo, hi = 0.0, 1.0 - 1e-9
    while hi - lo > tol:
        mid = (lo + hi) / 2.0
        if converges(mid):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def binary_bsc_threshold(dv: int, dc: int, *, n_samples: int = _VAL_N_SAMPLES,
                         max_iter: int = _VAL_MAX_ITER, seed: int = 2026080403,
                         p_tol: float = 0.001) -> float:
    """q=2 DE threshold of the regular ``(dv, dc)`` binary ensemble (the same
    two-level recursion at q=2, where it is exact = standard binary BP DE)."""
    dv_hist = {str(dv): 1.0}
    dc_hist = {str(dc): 1.0}
    result = threshold_binary_search(2, dv_hist, dc_hist, n_samples=n_samples,
                                     max_iter=max_iter, seed=seed, p_tol=p_tol)
    return result["threshold_proxy"]


# ------------------------------------------------------------ exact q=4 DE


def _batched_fwht(values: np.ndarray) -> np.ndarray:
    """Unnormalised XOR-order Walsh-Hadamard transform along the last axis
    (exactly the accepted ``nonbinary_qspa._fwht`` butterfly, vectorized over
    the leading axes)."""
    out = np.asarray(values, dtype=np.float64).copy()
    width = 1
    while width < out.shape[-1]:
        paired = out.reshape(-1, 2 * width)
        left = paired[:, :width].copy()
        right = paired[:, width:2 * width].copy()
        paired[:, :width] = left + right
        paired[:, width:2 * width] = left - right
        width *= 2
    return out


def exact_check_update(messages: Sequence[np.ndarray], q: int) -> np.ndarray | None:
    """Exact unapproximated check-to-variable update over GF(q) (all-unity
    coefficients, zero syndrome): the FFT-QSPA convolution of the incoming
    full-vector messages, normalized.  Used by the q=4 exact DE validation."""
    q = _qint(q)
    if len(messages) < 1:
        raise ValueError("exact_check_update needs at least one message")
    product = np.ones(q, dtype=np.float64)
    for message in messages:
        vector = np.asarray(message, dtype=np.float64).reshape(-1)
        if vector.shape != (q,) or not np.all(np.isfinite(vector)) or vector.sum() <= 0.0:
            raise ValueError("exact_check_update requires normalized finite messages")
        product *= _batched_fwht(vector)
    convolved = _batched_fwht(product) / q
    total = float(convolved.sum())
    if not math.isfinite(total) or total <= 0.0:
        return None
    return np.maximum(convolved, 0.0) / total


def exact_de(q: int, dv_hist: Mapping[Any, Any], dc_hist: Mapping[Any, Any],
             p: float, *, n_samples: int, max_iter: int, seed: int) -> list[float]:
    """Deterministic Monte-Carlo DE tracking the FULL q-vector messages (no
    two-level projection): variable updates are exact pointwise products, check
    updates are the exact FFT-QSPA convolution (``exact_check_update``).  Only
    feasible for tiny q (validation)."""
    q = _qint(q)
    if q > 8:
        raise ValueError("exact full-vector DE is bounded to q <= 8")
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1.0) / q:
        raise ValueError("q-ary symmetric p is outside the frozen open domain")
    n_samples, max_iter = int(n_samples), int(max_iter)
    rng = np.random.default_rng(int(seed))
    dv_degrees, dv_probs = _degree_histogram(dv_hist, "dv_hist")
    dc_degrees, dc_probs = _degree_histogram(dc_hist, "dc_hist", degree_max=CHECK_DEGREE_MAX)
    p = float(p)
    q_scalar = q
    # Received symbols follow the QSC error model: symbol 0 with prob 1-p,
    # each nonzero error with prob p/(q-1) (the transmitted symbol is 0 WLOG).
    symbol_probs = np.full(q_scalar, p / (q_scalar - 1.0), dtype=np.float64)
    symbol_probs[0] = 1.0 - p

    def channel_message(symbol: int) -> np.ndarray:
        vector = np.full(q_scalar, p / (q_scalar - 1.0), dtype=np.float64)
        vector[symbol] = 1.0 - p
        return vector

    # uniform initial check messages -> first variable update is the channel.
    check_messages = np.full((n_samples, q_scalar), 1.0 / q_scalar, dtype=np.float64)
    error_probs: list[float] = []
    converged_streak = 0
    regular_dc = None
    if len(dc_degrees) == 1:
        regular_dc = int(dc_degrees[0])
    try:
        for _ in range(max_iter):
            # ---- variable update (exact pointwise product + normalize)
            symbols = rng.choice(q_scalar, size=n_samples, p=symbol_probs)
            variable = np.empty((n_samples, q_scalar), dtype=np.float64)
            for index in range(n_samples):
                variable[index] = channel_message(int(symbols[index]))
            degrees = rng.choice(dv_degrees, size=n_samples, p=dv_probs)
            for _ in range(int(dv_degrees.max()) - 1):
                sources = rng.integers(0, n_samples, size=n_samples)
                variable *= check_messages[sources]
            variable = np.maximum(variable, _FLOOR)
            norms = variable.sum(axis=1, keepdims=True)
            if not np.all(np.isfinite(variable)) or np.any(norms <= 0.0):
                raise ValueError("exact DE variable update diverged")
            variable /= norms

            # ---- check update (exact convolution over GF(q))
            if regular_dc is not None:
                # Vectorized over the N samples: dc-1 iid draws per sample.
                sources = rng.integers(0, n_samples, size=(n_samples, regular_dc - 1))
                inputs = variable[sources]  # (N, dc-1, q)
                spectra = _batched_fwht(inputs)
                product = np.prod(spectra, axis=1)
                convolved = _batched_fwht(product) / q_scalar
                totals = convolved.sum(axis=1, keepdims=True)
                if np.any(totals <= 0.0) or not np.all(np.isfinite(convolved)):
                    raise ValueError("exact DE check update diverged")
                check_messages = np.maximum(convolved, 0.0) / totals
            else:
                c_degrees = rng.choice(dc_degrees, size=n_samples, p=dc_probs)
                checks = np.empty((n_samples, q_scalar), dtype=np.float64)
                for index in range(n_samples):
                    inputs = [variable[int(source)] for source in rng.integers(0, n_samples, size=int(c_degrees[index]) - 1)]
                    checks[index] = exact_check_update(inputs, q_scalar)
                check_messages = checks

            # ---- belief (exact): channel * all d_v check messages
            belief = np.empty((n_samples, q_scalar), dtype=np.float64)
            for index in range(n_samples):
                belief[index] = channel_message(int(symbols[index]))
            for _ in range(int(dv_degrees.max())):
                sources = rng.integers(0, n_samples, size=n_samples)
                belief *= check_messages[sources]
            belief = np.maximum(belief, _FLOOR)
            norms = belief.sum(axis=1, keepdims=True)
            if not np.all(np.isfinite(belief)) or np.any(norms <= 0.0):
                raise ValueError("exact DE belief update diverged")
            belief /= norms
            error = float(np.mean(np.argmax(belief, axis=1) != 0))
            error_probs.append(error)
            converged_streak = converged_streak + 1 if error < _CONV_TOL else 0
            if converged_streak >= 20:
                break
    except (ArithmeticError, FloatingPointError, ValueError):
        raise ValueError("exact DE recursion failed numerically")
    return error_probs


def exact_de_threshold(q: int, dv_hist: Mapping[Any, Any], dc_hist: Mapping[Any, Any],
                       *, n_samples: int, max_iter: int, seed: int,
                       p_tol: float = 0.002, p_lo: float = 0.01, p_hi: float = 0.49) -> float:
    """DE threshold of the exact full-vector recursion (binary search)."""
    q = _qint(q)
    lo, hi = float(p_lo), float(p_hi)
    while hi - lo > p_tol:
        mid = (lo + hi) / 2.0
        errors = exact_de(q, dv_hist, dc_hist, mid, n_samples=n_samples,
                          max_iter=max_iter, seed=seed)
        if de_converged(errors):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0
