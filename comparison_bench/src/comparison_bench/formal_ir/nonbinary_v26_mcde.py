"""V26 NB-LDPC Monte-Carlo density evolution accepting arbitrary posterior
populations over GF(2)/GF(32)/GF(512), with random nonzero edge-coefficient
permutation, true-symbol centering and bits/symbol entropy.

Extends ``nonbinary_v14_mcde`` (which only accepted shift-invariant ``w[delta]``
in ``structured`` mode) by injecting a full ``(n_samples, q)`` row-normalized
posterior population as the channel.  The variable/belief product update is
reused verbatim from V14 (no coefficient permutation needed there); the
check-node update is a new jitted kernel that permutes each incoming
variable-to-check message by its edge's nonzero GF coefficient (y = h*x) before
the WHT XOR convolution, matching the ``sum_e h_e x_e = 0`` parity-check law.

Semantics follow V14/V9: full length-q probability vectors, variable -> check ->
belief per iteration, deterministic numba update math, the observable is the
mean **bits/symbol** entropy of the check population, converged when it is below
``entropy_tol_bits`` for ``streak`` consecutive iterations.  All random draws
stay in numpy PCG64 with the frozen draw order.
"""
from __future__ import annotations

import math
from numbers import Integral
from typing import Any, Callable, Mapping

import numpy as np
from numba import njit

from .nonbinary_v9_mcde import entropy_base_q, parse_degree_hist
from .nonbinary_v9_common import concentrated_check_distribution
from .nonbinary_field import GF2mField
from .nonbinary_v14_mcde import (_FLOOR, _NORM_TOL,
                                 _variable_or_belief_jit, _wht_row_jit)

__all__ = [
    "build_gf_perm_table", "centered_channel_from_population",
    "variable_update_mcde", "belief_update_mcde", "check_update_mcde_posterior",
    "run_mcde_posterior", "mean_bits_entropy", "target_rate_layer",
    "make_rho", "CONCENTRATED",
]

#: RGBA of a posterior population row is checked against this tolerance before use.
POSTE_RTOL = 1e-6
#: Upper bound on any edge-perspective degree (check degrees can be large for
#: very-high-rate layers such as F03 L1 ~0.99, dc ~300).
DEGREE_MAX = 2048


@njit(cache=False)
def _check_update_coeff_jit(v2c: np.ndarray, draws: np.ndarray,
                            idx: np.ndarray, coeff: np.ndarray,
                            perm: np.ndarray) -> np.ndarray:
    """njit check-node update with nonzero GF edge coefficients.

    ``v2c`` (n,q) incoming variable population; ``draws`` dc-1 per sample;
    ``idx[d,i]`` row drawn at slot d; ``coeff[d,i]`` nonzero GF coefficient of
    the edge used at slot d; ``perm`` (q, q) integer index map with
    ``perm[h, y] = inverse(h)*y`` in GF(q) so that
    ``to_y(m,h)[y] = m[perm[h,y]]``.  Each incoming row is permuted to the
    y-domain (y = h*x) before its WHT is accumulated; inverse WHT then is over
    the y-domain of the remainder edge (a random edge has the same marginal law,
    so the outgoing coefficient is absorbed as identity — symmetric).
    """
    n = v2c.shape[0]
    q = v2c.shape[1]
    acc = np.ones((n, q))
    tmp = np.empty(q)
    max_draws = idx.shape[0]
    for d in range(max_draws):
        for i in range(n):
            if draws[i] > d:
                h = coeff[d, i]
                src = idx[d, i]
                for y in range(q):
                    tmp[y] = v2c[src, perm[h, y]]
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


def build_gf_perm_table(q: int) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(perm, nonzero_coeffs)`` for GF(q).

    ``perm[h, y] = inverse(h)*y`` (a 0..q-1 integer index map) for every nonzero
    ``h``; ``nonzero_coeffs`` = the field's primitive cycle (all nonzero).
    Row ``h=0`` is left as zeros (never used; coefficients are nonzero).
    """
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or (q & (q - 1)):
        raise ValueError("GF(q) q must be a power of 2 >= 2")
    q = int(q)
    field = GF2mField.create(q)
    perm = np.zeros((q, q), dtype=np.int64)
    nonzero = np.asarray(field.nonzero_cycle, dtype=np.int64)
    y = np.arange(q, dtype=np.int64)
    for h in nonzero:
        inv = field.inverse(int(h))
        # perm[h, y] = inverse(h)*y
        row = np.empty(q, dtype=np.int64)
        for yy in range(q):
            row[yy] = field.mul(int(inv), yy)
        perm[int(h)] = row
    return perm, nonzero


def mean_bits_entropy(pop: np.ndarray, q: int) -> float:
    """Mean entropy of a ``(n, q)`` population in bits/symbol (= base-q * log2 q)."""
    base_q = entropy_base_q(pop)
    return float(base_q * math.log2(q))


def _channel_rows_from_centered(centered_rows: np.ndarray) -> np.ndarray:
    centered_rows = np.asarray(centered_rows, dtype=np.float64)
    if centered_rows.ndim != 2:
        raise ValueError("centered_rows must be 2-D (n, q)")
    q = centered_rows.shape[1]
    if not np.all(np.isfinite(centered_rows)):
        raise ValueError("posterior population must be finite")
    if np.any(centered_rows < 0.0):
        raise ValueError("posterior population must be non-negative")
    totals = centered_rows.sum(axis=1)
    if not np.all(np.isfinite(totals)) or np.any(totals <= 0.0):
        raise ValueError("posterior population rows must have positive total mass")
    # row-normalize (float drift guard) and verify near-normalized
    out = centered_rows / totals[:, None]
    if not np.all(np.abs(out.sum(axis=1) - 1.0) < POSTE_RTOL):
        raise ValueError("posterior population not normalized")
    return out


def variable_update_mcde(c2v: np.ndarray, dv_degrees: np.ndarray,
                         dv_probs: np.ndarray, channel: np.ndarray,
                         rng: np.random.Generator, q: int) -> np.ndarray:
    """V14 variable product update (channel x incoming c2v), unchanged."""
    n = channel.shape[0]
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    draws = degrees - 1
    max_draws = int(draws.max())
    idx = np.empty((max_draws, n), dtype=np.int64)
    for d in range(max_draws):
        idx[d] = rng.integers(0, n, size=n)
    return _variable_or_belief_jit(c2v, channel, draws.astype(np.int64), idx)


def belief_update_mcde(c2v: np.ndarray, dv_degrees: np.ndarray,
                       dv_probs: np.ndarray, channel: np.ndarray,
                       rng: np.random.Generator, q: int) -> np.ndarray:
    """V14 belief update (channel x all incident c2v rows), unchanged."""
    n = channel.shape[0]
    degrees = rng.choice(dv_degrees, size=n, p=dv_probs)
    draws = degrees
    max_draws = int(draws.max())
    idx = np.empty((max_draws, n), dtype=np.int64)
    for d in range(max_draws):
        idx[d] = rng.integers(0, n, size=n)
    return _variable_or_belief_jit(c2v, channel, draws.astype(np.int64), idx)


def check_update_mcde_posterior(v2c: np.ndarray, dc_degrees: np.ndarray,
                                dc_probs: np.ndarray, perm: np.ndarray,
                                nonzero_coeffs: np.ndarray,
                                rng: np.random.Generator, q: int) -> np.ndarray:
    """V26 check update with random nonzero edge coefficients.

    ``perm`` and ``nonzero_coeffs`` from :func:`build_gf_perm_table`.
    Coefficients are drawn per (slot, sample) from ``nonzero_coeffs`` in the
    frozen RNG order after the degree/index draws.
    """
    n = v2c.shape[0]
    degrees = rng.choice(dc_degrees, size=n, p=dc_probs)
    draws = degrees - 1
    max_draws = int(draws.max())
    idx = np.empty((max_draws, n), dtype=np.int64)
    for d in range(max_draws):
        idx[d] = rng.integers(0, n, size=n)
    coeff = np.empty((max_draws, n), dtype=np.int64)
    for d in range(max_draws):
        coeff[d] = rng.choice(nonzero_coeffs, size=n)
    return _check_update_coeff_jit(v2c, draws.astype(np.int64), idx, coeff, perm)


def concentrated_check_distribution_wrapper(rate: float,
                                             lambda_edge: Mapping[Any, Any]) -> dict[str, float]:
    return concentrated_check_distribution(rate, lambda_edge)


def concentrated_rho_to_hist(conc: Mapping[Any, Any]) -> dict[int, float]:
    """Convert a concentrated-check dict (dc_lo/dc_hi/w_lo/w_hi, float)
    into the standard integer-degree edge-perspective ``{degree: weight}`` map
    accepted by ``parse_degree_hist``."""
    out: dict[int, float] = {}
    d_lo = int(conc["dc_lo"]); d_hi = int(conc["dc_hi"])
    w_lo = float(conc["w_lo"]); w_hi = float(conc["w_hi"])
    if w_lo > 0.0:
        out[d_lo] = w_lo
    if w_hi > 0.0:
        out[d_hi] = w_hi
    if not out:
        raise ValueError("concentrated distribution has no positive weight")
    return out


def _degree_arrays(hist: Mapping[Any, Any], name: str, q: int) -> tuple[np.ndarray, np.ndarray]:
    return parse_degree_hist(hist, name, DEGREE_MAX)


def target_rate_layer(f: float, H_bits: float, width: int) -> float:
    """Layer target code rate at efficiency ``f``.

    ``R_target = 1 - f * (H_bits / width)``, where ``width = log2(q)`` is the
    layer's field width in bits.  Clamps to ``(0, 1)`` open domain.
    """
    if not math.isfinite(f) or f <= 0.0:
        raise ValueError("f must be positive and finite")
    if not math.isfinite(H_bits) or H_bits < 0.0:
        raise ValueError("H_bits must be non-negative and finite")
    if isinstance(width, bool) or not isinstance(width, Integral) or int(width) < 1:
        raise ValueError("width must be a positive integer")
    rate = 1.0 - f * (float(H_bits) / float(width))
    if rate <= 0.0 or rate >= 1.0:
        rate = min(max(rate, 1e-6), 1.0 - 1e-6)
    return float(rate)


def make_rho(rate: float, lambda_edge: Mapping[Any, Any]) -> dict[int, float]:
    """Harmonic-exact concentrated check distribution for the given rate,
    as a valid integer-degree edge-perspective ``{degree: weight}`` map."""
    conc = concentrated_check_distribution(rate, lambda_edge)
    return concentrated_rho_to_hist(conc)


def run_mcde_posterior(q: int, lambda_edge: Mapping[Any, Any],
                       rho_edge: Mapping[Any, Any], *,
                       channel_sampler: Callable[[int, np.random.Generator], np.ndarray],
                       n_samples: int, max_iter: int, seed: int,
                       entropy_tol_bits: float = 0.01, streak: int = 20,
                       record_entropy: bool = True,
                       record_channel_entropy: bool = False) -> dict:
    """Run one V26 posterior-population MC-DE.

    ``channel_sampler(n, rng)`` must return a ``(n, q)`` **already true-symbol
    centered** row-normalized posterior population (each row a probability
    vector over the layer's GF symbols with the true symbol at index 0).
    ``rho_edge`` is the check distribution for the target rate.  Convergence is
    on mean bits/symbol entropy of the check population.

    ``record_channel_entropy`` (default False, read-only M1 evidence only) also
    records the mean bits/symbol entropy of *the channel population the DE
    actually consumed* at each iteration.  It never changes the update math or
    the frozen screen/confirmation call semantics — it only appends an
    observational trace to the returned dict.
    """
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or (q & (q - 1)):
        raise ValueError("q must be a power of 2 >= 2")
    q = int(q)
    if isinstance(n_samples, bool) or not isinstance(n_samples, Integral) or int(n_samples) < 100:
        raise ValueError("n_samples must be >= 100")
    if isinstance(max_iter, bool) or not isinstance(max_iter, Integral) or not 1 <= int(max_iter) <= 5000:
        raise ValueError("max_iter must be in 1..5000")
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    if not math.isfinite(float(entropy_tol_bits)) or float(entropy_tol_bits) <= 0.0:
        raise ValueError("entropy_tol_bits must be positive and finite")
    if isinstance(streak, bool) or not isinstance(streak, Integral) or int(streak) < 1:
        raise ValueError("streak must be a positive integer")
    n_samples, max_iter, seed = int(n_samples), int(max_iter), int(seed)
    entropy_tol_bits = float(entropy_tol_bits)
    streak = int(streak)

    dv_degrees, dv_probs = _degree_arrays(lambda_edge, "lambda_edge", q)
    dc_degrees, dc_probs = _degree_arrays(rho_edge, "rho_edge", q)
    perm, nonzero_coeffs = build_gf_perm_table(q)
    rng = np.random.default_rng(seed)

    c2v = np.full((n_samples, q), 1.0 / q, dtype=np.float64)
    entropy_trace: list[float] = []
    channel_entropy_trace: list[float] = []
    converged_streak = 0
    converged = False
    iterations = 0
    for iteration in range(1, max_iter + 1):
        centered = channel_sampler(n_samples, rng)
        channel = _channel_rows_from_centered(centered)
        if record_channel_entropy:
            channel_entropy_trace.append(float(mean_bits_entropy(channel, q)))
        v2c = variable_update_mcde(c2v, dv_degrees, dv_probs, channel, rng, q)
        c2v = check_update_mcde_posterior(v2c, dc_degrees, dc_probs, perm,
                                          nonzero_coeffs, rng, q)
        entropy = mean_bits_entropy(c2v, q) if record_entropy else None
        if record_entropy:
            entropy_trace.append(float(entropy))
            if entropy < entropy_tol_bits:
                converged_streak += 1
            else:
                converged_streak = 0
            if converged_streak >= streak:
                converged = True
                iterations = iteration
                break
        iterations = iteration
    result = {
        "schema": "nbldpc_v26_mcde_run_v1",
        "converged": converged,
        "iterations": iterations,
        "entropy_trace_bits": entropy_trace,
        "final_entropy_bits": float(entropy_trace[-1]) if entropy_trace else None,
        "q": q, "n_samples": n_samples, "max_iter": max_iter, "seed": seed,
        "entropy_tol_bits": entropy_tol_bits, "streak": streak,
        "lambda": {int(k): float(v) for k, v in lambda_edge.items()},
        "rho": {int(k): float(v) for k, v in rho_edge.items()},
        "rng": "PCG64",
    }
    if record_channel_entropy:
        result["channel_entropy_trace_bits"] = channel_entropy_trace
    return result
