"""V17 Stage 0 — small-q bit-plane decomposition DE mechanism reproduction gate
(``formal-nonbinary-ldpc-v17-multibit-structured-de-gate``, additive layer).

The V17 gate is a feasibility ruling on edge-label / bit-plane structured
nonbinary LDPC ensembles over the frozen V13 multibit channel model.  Before
any model build or q=1024 point evaluation, Stage 0 must reproduce the
*Cohen-style bit-plane decomposition mechanism* on a small field and cross-check
it against two frozen anchors (design section 2):

- **Anchor A (internal consistency)**: q=4 (2-bit decomposition, the degenerate
  p_1 = p_2 = p case).  The bit-plane decomposition DE — each of the 2 Gray bit
  planes of a QSC(p) run as an *independent* binary-symmetric-channel DE with
  the plane's marginal crossover ``q_plane(p)`` (joint convergence = every
  plane converges) — must reproduce the symbol-level QSC(p) DE threshold to
  within ``|delta| <= 0.005`` under the SAME n_samples / max_iter / seed /
  convergence protocol (point-by-point grid comparison).
- **Anchor B (literature cross-check)**: q=4, R=0.75 symbol-level QSC DE
  threshold vs the published value 0.069 with ``|delta| <= 0.012``, directly
  reusing the V14/V8-60 anchor machinery (same q=4 R=0.75 ensemble,
  n_samples=1e5, max_iter=150, entropy <= 0.01 for 20 consecutive iterations).

PASS requires BOTH anchors (no boolean fallback).  Any anchor failure freezes
the gate before Stage 1/2.

Mechanism equivalences exploited (read-only reuse, V9/V14 sources are never
edited):

- A GF(2^m) XOR-check convolution factorizes across bit planes
  (``WHT_{2^m} = WHT_2 (x) ... (x) WHT_2``), so the Cohen bit-plane
  decomposition is the *exact* per-bit-plane limit of the q-ary check update;
  the only approximation being validated is modelling the QSC prior as an
  independent per-plane BSC marginals.
- The binary per-plane DE is :func:`nonbinary_v14_mcde.run_mcde` at ``q=2`` in
  QSC mode (q=2 QSC == binary symmetric channel, full 2-vector messages == the
  exact binary BP DE messages), so the bit-plane and symbol-level recursions
  share the SAME kernel and the SAME frozen PCG64 RNG draw order.

Only numpy/numba and the read-only V9/V14 helpers are imported; this module
never reads frame data and never executes a decoder.
"""
from __future__ import annotations

import math
from numbers import Integral
from typing import Any, Mapping

import numpy as np

# Read-only reuse of the V14 q=4 QSC anchor machinery and the frozen DE kernel.
from .nonbinary_v14_mcde import (DEGREE_MAX, QSC, STAGE0_LAMBDA_DEGREES,
                                 STAGE0_MAX_ITER, STAGE0_N_SAMPLES,
                                 STAGE0_PUBLISHED, STAGE0_Q, STAGE0_RATE,
                                 STAGE0_SEED, STAGE0_TOL,
                                 threshold_binary_search, run_mcde,
                                 structured_rho as _concentrated_rho)

__all__ = [
    "QSC",
    "DEGREE_MAX",
    "STAGE0_Q", "STAGE0_RATE", "STAGE0_N_SAMPLES", "STAGE0_MAX_ITER",
    "STAGE0_PUBLISHED", "STAGE0_TOL", "STAGE0_SEED",
    "ANCHOR_A_Q", "ANCHOR_A_BITS", "ANCHOR_A_RATE", "ANCHOR_A_N_SAMPLES",
    "ANCHOR_A_MAX_ITER", "ANCHOR_A_ENTROPY_TOL", "ANCHOR_A_STREAK",
    "ANCHOR_A_SEED", "ANCHOR_A_TOL", "ANCHOR_A_P_LO", "ANCHOR_A_P_HI",
    "ANCHOR_A_GRID_STEP",
    "gray_bit", "qsc_bitplane_marginals", "bitplane_decomposed_threshold",
    "run_anchor_a", "run_anchor_b", "build_stage0_doc",
    "run_stage0",
]

# --------------------------------------------------------------------------- #
# Anchor A frozen constants (design section 2)
# --------------------------------------------------------------------------- #
ANCHOR_A_Q = 4
ANCHOR_A_BITS = 2
ANCHOR_A_RATE = STAGE0_RATE            # same q=4 R=0.75 ensemble as Anchor B
ANCHOR_A_N_SAMPLES = STAGE0_N_SAMPLES  # 1e5 (frozen same protocol)
ANCHOR_A_MAX_ITER = STAGE0_MAX_ITER    # 150
ANCHOR_A_ENTROPY_TOL = 0.01
ANCHOR_A_STREAK = 20
ANCHOR_A_SEED = STAGE0_SEED            # same seed protocol as Anchor B
ANCHOR_A_TOL = 0.005                   # frozen |delta| bound (internal consistency)
ANCHOR_A_P_LO = 0.005                  # symbol-error grid low endpoint
ANCHOR_A_P_HI = 0.25                   # symbol-error grid high endpoint
ANCHOR_A_GRID_STEP = 0.0025            # frozen dense-sweep step (V14 semantics)


def _struct_rho(rate: float, lam: Mapping[Any, Any]) -> dict[int, float]:
    """Edge-perspective check-degree map from the harmonic-exact concentrated
    distribution (``{dc_lo: w_lo, dc_hi: w_hi}``, zero-weight entries dropped)."""
    conc = _concentrated_rho(rate, lam)
    return {int(k): float(v) for k, v in
            ((conc["dc_lo"], conc["w_lo"]), (conc["dc_hi"], conc["w_hi"]))
            if float(v) > 0.0}


# --------------------------------------------------------------------------- #
# bit-plane helpers (gray marginal decomposition)
# --------------------------------------------------------------------------- #

def gray_bit(symbol: int, bit: int) -> int:
    """The ``bit``-th binary-reflected Gray bit of ``symbol`` (LSB=0).

    ``gray(s) = s XOR (s >> 1)``; returns ``(gray(s) >> bit) & 1``.
    """
    if isinstance(symbol, bool) or not isinstance(symbol, Integral) or int(symbol) < 0:
        raise ValueError("symbol must be a non-negative integer")
    if isinstance(bit, bool) or not isinstance(bit, Integral) or int(bit) < 0:
        raise ValueError("bit must be a non-negative integer")
    return (int(symbol) ^ (int(symbol) >> 1) >> int(bit)) & 1


def qsc_bitplane_marginals(q: int, p: float) -> np.ndarray:
    """MSB-first per-bit-plane crossover of a QSC(p) under Gray labelling.

    Symbol 0 is transmitted (mass ``1 - p``, all zero bits); each of the
    ``q - 1`` nonzero symbols carries mass ``p / (q - 1)``.  The marginal
    crossover of bit plane ``b`` is ``p / (q-1) * #{s != 0 : gray_bit(s, b) = 1}``.
    Returns a length-``log2(q)`` array in MSB-first order (matches the V13
    ``mismatch_rate`` MSB-first convention).  Degenerate q=4 case: both planes
    equal ``2p/3`` (balanced Gray).
    """
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1):
        raise ValueError("q must be a power of two >= 2")
    q = int(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 <= float(p) < (q - 1.0) / q:
        raise ValueError("p must be finite in [0, (q-1)/q)")
    p = float(p)
    m = q.bit_length() - 1
    if p == 0.0:
        return np.zeros(m, dtype=np.float64)
    off = p / (q - 1.0)
    marginals = np.zeros(m, dtype=np.float64)
    for symbol in range(1, q):
        gray = int(symbol) ^ (int(symbol) >> 1)
        for bit in range(m):
            if (gray >> bit) & 1:
                marginals[m - 1 - bit] += off  # MSB-first
    return marginals


def bitplane_decomposed_threshold(q: int, lambda_edge: Mapping[Any, Any],
                                  rho_edge: Mapping[Any, Any], *,
                                  n_samples: int, max_iter: int, seed: int,
                                  p_lo: float = ANCHOR_A_P_LO,
                                  p_hi: float = ANCHOR_A_P_HI,
                                  grid_step: float = ANCHOR_A_GRID_STEP,
                                  entropy_tol: float = ANCHOR_A_ENTROPY_TOL,
                                  streak: int = ANCHOR_A_STREAK) -> dict:
    """Bit-plane decomposition DE threshold of a QSC(p) over GF(q), reported in
    the SYMBOL-error coordinate ``p``.

    At each grid point ``p`` the q-ary QSC is Gray-sliced into ``log2(q)``
    independent binary symmetric channels with per-plane crossover
    ``qsc_bitplane_marginals(q, p)``; each plane runs the SAME frozen kernel
    :func:`run_mcde` at ``q=2`` (exact binary BP DE) with the SAME seed, and the
    point converges iff EVERY plane converges (joint convergence).  The proxy is
    the largest converging ``p`` (mirrors V14 grid-sweep semantics: highest
    converged probe, else ``p_lo``).
    """
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1):
        raise ValueError("q must be a power of two >= 2")
    q = int(q)
    m = q.bit_length() - 1
    if isinstance(grid_step, bool) or not isinstance(grid_step, (int, float)) \
            or not math.isfinite(float(grid_step)) or float(grid_step) <= 0.0:
        raise ValueError("grid_step must be positive and finite")
    if not (0.0 < float(p_lo) < float(p_hi) < (q - 1.0) / q):
        raise ValueError("invalid Anchor A probe range")
    points: list[float] = []
    p = float(p_lo)
    while p <= float(p_hi) + 0.5 * float(grid_step):
        points.append(p)
        p += float(grid_step)
    probes: list[dict[str, Any]] = []
    highest = None
    for p_probe in points:
        marginals = qsc_bitplane_marginals(q, p_probe)
        plane_results: list[dict[str, Any]] = []
        for plane in range(m):
            run = run_mcde(2, lambda_edge, rho_edge, channel_mode=QSC,
                           p=float(marginals[plane]), n_samples=int(n_samples),
                           max_iter=int(max_iter), seed=int(seed),
                           entropy_tol=float(entropy_tol), streak=int(streak))
            plane_results.append({"plane": plane, "crossover": float(marginals[plane]),
                                  "converged": bool(run["converged"]),
                                  "final_entropy": run["final_entropy"]})
        joint = bool(plane_results) and all(r["converged"] for r in plane_results)
        probes.append({"p": p_probe, "joint_converged": joint,
                       "planes": plane_results})
        if joint:
            highest = p_probe
    proxy = float(p_lo) if highest is None else float(highest)
    return {"threshold_proxy": proxy, "grid_points": points, "probes": probes,
            "n_planes": m, "converged_at_lo": bool(probes[0]["joint_converged"]) if probes else None}


def run_anchor_a(*, lambda_edge: Mapping[Any, Any] | None = None,
                 n_samples: int = ANCHOR_A_N_SAMPLES,
                 max_iter: int = ANCHOR_A_MAX_ITER, seed: int = ANCHOR_A_SEED,
                 tol: float = ANCHOR_A_TOL) -> dict:
    """Anchor A: bit-plane decomposition DE vs symbol-level QSC DE threshold
    agreement at q=4 (degenerate p_1 = p_2 case), |delta| <= ``tol``.

    Both recursions use the SAME q=4 R=0.75 ensemble, n_samples, max_iter, seed
    and convergence protocol (entropy <= 0.01 for 20 consecutive iterations).
    The symbol-level threshold is computed with the V14 frozen grid-sweep
    :func:`threshold_binary_search`; the bit-plane threshold with
    :func:`bitplane_decomposed_threshold` (2 Gray planes, joint convergence).
    """
    lam = dict(STAGE0_LAMBDA_DEGREES if lambda_edge is None else lambda_edge)
    rho = _struct_rho(ANCHOR_A_RATE, lam)
    bp = bitplane_decomposed_threshold(
        ANCHOR_A_Q, lam, rho, n_samples=n_samples, max_iter=max_iter, seed=seed,
        p_lo=ANCHOR_A_P_LO, p_hi=ANCHOR_A_P_HI, grid_step=ANCHOR_A_GRID_STEP,
        entropy_tol=ANCHOR_A_ENTROPY_TOL, streak=ANCHOR_A_STREAK)
    sym = threshold_binary_search(
        ANCHOR_A_Q, ANCHOR_A_RATE, lam, rho, n_samples=n_samples,
        max_iter=max_iter, seed=seed, p_lo=ANCHOR_A_P_LO, p_hi=ANCHOR_A_P_HI,
        grid_step=ANCHOR_A_GRID_STEP)
    p_bp = float(bp["threshold_proxy"])
    p_sym = float(sym["threshold_proxy"])
    delta = abs(p_bp - p_sym)
    return {
        "anchor": "A",
        "q": ANCHOR_A_Q, "bits": ANCHOR_A_BITS, "rate": ANCHOR_A_RATE,
        "n_samples": int(n_samples), "max_iter": int(max_iter), "seed": int(seed),
        "entropy_tol": ANCHOR_A_ENTROPY_TOL, "streak": ANCHOR_A_STREAK,
        "tolerance": float(tol),
        "bitplane_threshold_proxy": p_bp,
        "symbol_level_threshold_proxy": p_sym,
        "delta": float(delta),
        "mechanism_verified": bool(delta <= tol),
        "bitplane_run": bp,
        "symbol_run": sym,
        "diagnostic_only": True,
    }


def run_anchor_b(*, lambda_edge: Mapping[Any, Any] | None = None,
                 n_samples: int = STAGE0_N_SAMPLES,
                 max_iter: int = STAGE0_MAX_ITER, seed: int = STAGE0_SEED,
                 published: float = STAGE0_PUBLISHED,
                 tol: float = STAGE0_TOL) -> dict:
    """Anchor B: literature cross-check — q=4 R=0.75 QSC symbol-level DE
    threshold vs the published 0.069, |delta| <= 0.012 (V14/V8-60 machinery).
    """
    lam = dict(STAGE0_LAMBDA_DEGREES if lambda_edge is None else lambda_edge)
    rho = _struct_rho(STAGE0_RATE, lam)
    sweep = threshold_binary_search(
        STAGE0_Q, STAGE0_RATE, lam, rho, n_samples=n_samples, max_iter=max_iter,
        seed=seed, p_lo=0.01, p_hi=0.12, grid_step=0.0025)
    proxy = float(sweep["threshold_proxy"])
    delta = abs(proxy - float(published))
    return {
        "anchor": "B",
        "q": STAGE0_Q, "rate": STAGE0_RATE,
        "n_samples": int(n_samples), "max_iter": int(max_iter), "seed": int(seed),
        "published_threshold": float(published),
        "computed_threshold_proxy": proxy,
        "delta": float(delta),
        "tolerance": float(tol),
        "mechanism_verified": bool(delta <= tol),
        "symbol_run": sweep,
        "diagnostic_only": True,
    }


def build_stage0_doc(*, anchor_a: dict, anchor_b: dict) -> dict[str, Any]:
    """Stage 0 mechanism-reproduction doc (schema ``nbldpc_v17_stage0_v1``).

    PASS iff BOTH anchors verify (no boolean fallback); any failure freezes the
    gate before Stage 1/2.
    """
    a_ok = bool(anchor_a["mechanism_verified"])
    b_ok = bool(anchor_b["mechanism_verified"])
    return {
        "schema": "nbldpc_v17_stage0_v1",
        "gate_state": "pass" if (a_ok and b_ok) else "fail",
        "anchor_a": anchor_a,
        "anchor_b": anchor_b,
        "both_anchors_verified": bool(a_ok and b_ok),
        "diagnostic_only": True,
    }


def run_stage0(*, anchor_a_kwargs: Mapping[str, Any] | None = None,
               anchor_b_kwargs: Mapping[str, Any] | None = None) -> dict:
    """Run both Stage 0 anchors and build the frozen stage-0 doc."""
    a = run_anchor_a(**(anchor_a_kwargs or {}))
    b = run_anchor_b(**(anchor_b_kwargs or {}))
    return build_stage0_doc(anchor_a=a, anchor_b=b)
