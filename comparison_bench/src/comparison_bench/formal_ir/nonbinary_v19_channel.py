"""V19 channel helpers for the Nonbinary LDPC primary route (N0-N6).

This module is an additive diagnostic layer under ``comparison_bench/``.  It
reuses the frozen V17/V18 structured-channel model read-only and adds small
helpers for honest leakage accounting and QSC control channels.  It never
executes a decoder and never modifies frozen baselines.
"""
from __future__ import annotations

import math
from numbers import Integral
from typing import Any

import numpy as np

from .nonbinary_v18_b2_structured_de import (
    _V17_PER_PLANE_ERROR as V17_PER_PLANE_ERROR,
    build_folded_w,
    build_real_w_q1024,
)

__all__ = [
    "V17_PER_PLANE_ERROR",
    "H_FULL_Q1024",
    "build_real_w_q1024",
    "build_folded_w",
    "build_qsc_w",
    "binary_entropy_bits",
    "symbol_entropy_bits",
    "folded_entropy_bits",
    "f_plain_qary",
    "f_full_two_stage",
    "lsb_public_capacity_f",
    "build_high_plane_w",
    "build_channel_doc",
]

#: Frozen full-channel entropy model (V17 product-of-marginals, bits/symbol).
H_FULL_Q1024 = 0.549955


def build_qsc_w(q: int, p: float) -> np.ndarray:
    """Return a q-ary symmetric channel difference distribution.

    ``w[0] = 1-p`` and every nonzero difference has probability ``p/(q-1)``.
    """
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1):
        raise ValueError("q must be a power of two >= 2")
    q = int(q)
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 < float(p) < (q - 1.0) / q:
        raise ValueError("p must be finite in (0, (q-1)/q)")
    p = float(p)
    w = np.full(q, p / (q - 1.0), dtype=np.float64)
    w[0] = 1.0 - p
    return w


def binary_entropy_bits(p: float) -> float:
    """Binary entropy h2(p) in bits."""
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) \
            or not 0.0 <= float(p) <= 1.0:
        raise ValueError("p must be finite in [0, 1]")
    p = float(p)
    if p == 0.0 or p == 1.0:
        return 0.0
    return float(-p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p))


def symbol_entropy_bits(w: Any) -> float:
    """Shannon entropy of a probability vector in bits."""
    vector = np.asarray(w, dtype=np.float64)
    if vector.ndim != 1 or not np.all(np.isfinite(vector)) or np.any(vector < 0.0):
        raise ValueError("w must be a finite non-negative vector")
    total = float(vector.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("w must have positive total mass")
    if not math.isclose(total, 1.0, abs_tol=1e-9):
        vector = vector / total
    positive = vector > 0.0
    if not positive.any():
        return 0.0
    return float(-np.sum(vector[positive] * np.log2(vector[positive])))


def folded_entropy_bits(q_small: int = 16) -> float:
    """Entropy (bits/symbol) of the folded real structured channel."""
    return float(symbol_entropy_bits(build_folded_w(q_small)))


def f_plain_qary(*, rate: float, q: int, h_bits: float) -> float:
    """Plain q-ary syndrome-only f: ``(1-rate)*log2(q)/H``.

    This is the leakage of a full q-ary syndrome with no separate public bits.
    """
    if isinstance(q, bool) or not isinstance(q, Integral) or int(q) < 2 or int(q) & (int(q) - 1):
        raise ValueError("q must be a power of two >= 2")
    q = int(q)
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(float(rate)) \
            or not 0.0 < float(rate) < 1.0:
        raise ValueError("rate must be finite in (0, 1)")
    if isinstance(h_bits, bool) or not isinstance(h_bits, (int, float)) \
            or not math.isfinite(float(h_bits)) or float(h_bits) <= 0.0:
        raise ValueError("h_bits must be positive and finite")
    return (1.0 - float(rate)) * math.log2(q) / float(h_bits)


def f_full_two_stage(*, syndrome_bits_per_symbol: float,
                     public_bits_per_symbol: float,
                     h_full_bits: float = H_FULL_Q1024) -> float:
    """Honest two-stage f against the full q=1024 channel entropy.

    ``syndrome_bits_per_symbol`` is the NB-LDPC syndrome cost per original
    symbol; ``public_bits_per_symbol`` is any disclosed LSB/control overhead.
    """
    if isinstance(syndrome_bits_per_symbol, bool) or not isinstance(syndrome_bits_per_symbol, (int, float)) \
            or not math.isfinite(float(syndrome_bits_per_symbol)) or float(syndrome_bits_per_symbol) < 0.0:
        raise ValueError("syndrome_bits_per_symbol must be finite and non-negative")
    if isinstance(public_bits_per_symbol, bool) or not isinstance(public_bits_per_symbol, (int, float)) \
            or not math.isfinite(float(public_bits_per_symbol)) or float(public_bits_per_symbol) < 0.0:
        raise ValueError("public_bits_per_symbol must be finite and non-negative")
    if isinstance(h_full_bits, bool) or not isinstance(h_full_bits, (int, float)) \
            or not math.isfinite(float(h_full_bits)) or float(h_full_bits) <= 0.0:
        raise ValueError("h_full_bits must be positive and finite")
    return (float(syndrome_bits_per_symbol) + float(public_bits_per_symbol)) / float(h_full_bits)


def build_high_plane_w(*, public_lsb_planes: int,
                        per_plane_error: Any = V17_PER_PLANE_ERROR) -> np.ndarray:
    """Build the effective symbol-difference distribution for the high-bit
    planes that remain after publicly disclosing the ``public_lsb_planes``
    least-significant Gray planes.

    This is the channel model for a Pacher-style LSB-public two-step route.
    The result is a length ``2^(10-public_lsb_planes)`` distribution over the
    high-bit XOR differences, averaged over all high-bit Alice symbols.
    """
    if isinstance(public_lsb_planes, bool) or not isinstance(public_lsb_planes, int) \
            or not 0 <= int(public_lsb_planes) <= 10:
        raise ValueError("public_lsb_planes must be an integer in 0..10")
    l = int(public_lsb_planes)
    rates = np.asarray(per_plane_error, dtype=np.float64)
    if rates.shape != (10,) or not np.all(np.isfinite(rates)) or np.any(rates < 0.0) \
            or np.any(rates > 1.0):
        raise ValueError("per_plane_error must be a 10-vector in [0,1]")
    n_high = 10 - l
    q_high = 1 << n_high
    if n_high == 0:
        return np.array([1.0], dtype=np.float64)
    # Gray code for high-bit indices 0..n_high-1 (MSB-first plane order).
    gray = np.array([(i ^ (i >> 1)) for i in range(q_high)], dtype=np.int64)
    bit = np.array([[(g >> k) & 1 for k in range(n_high)] for g in gray], dtype=np.int64)
    p = rates[:n_high]
    w = np.zeros(q_high, dtype=np.float64)
    for s in range(q_high):
        gs = bit[s]
        for d in range(q_high):
            gd = bit[s ^ d]
            diff = gs ^ gd
            prob = 1.0
            for k in range(n_high):
                prob *= (float(p[k]) if diff[k] else 1.0 - float(p[k]))
            w[d] += prob
    w /= w.sum()
    return w


def lsb_public_capacity_f(*, public_lsb_planes: int,
                           per_plane_error: Any = V17_PER_PLANE_ERROR,
                           h_full_bits: float = H_FULL_Q1024) -> dict:
    """Capacity-ideal LSB-public two-step leakage estimate.

    If the ``public_lsb_planes`` least-significant Gray planes are publicly
    disclosed (one bit per symbol each), the remaining high-bit planes still
    need reconciliation.  This function returns the public-bit cost, the
    residual high-plane entropy (ideal syndrome cost in bits/symbol), and the
    resulting ideal f.  This is a diagnostic bound, not a code construction.
    """
    if isinstance(public_lsb_planes, bool) or not isinstance(public_lsb_planes, int) \
            or not 0 <= int(public_lsb_planes) <= 10:
        raise ValueError("public_lsb_planes must be an integer in 0..10")
    l = int(public_lsb_planes)
    rates = np.asarray(per_plane_error, dtype=np.float64)
    if rates.shape != (10,) or not np.all(np.isfinite(rates)) or np.any(rates < 0.0) \
            or np.any(rates > 1.0):
        raise ValueError("per_plane_error must be a 10-vector in [0,1]")
    # MSB-first list: indices 0..9; the l least-significant planes are indices 10-l..9.
    high_h2 = float(sum(binary_entropy_bits(float(p)) for p in rates[:10 - l]))
    ideal_syndrome = high_h2
    public_bits = float(l)
    f_ideal = (public_bits + ideal_syndrome) / float(h_full_bits)
    return {
        "public_lsb_planes": l,
        "public_bits_per_symbol": public_bits,
        "residual_high_plane_entropy_bits_per_symbol": high_h2,
        "ideal_syndrome_bits_per_symbol": ideal_syndrome,
        "ideal_f_full": float(f_ideal),
        "note": "capacity-ideal diagnostic bound; real finite codes will be worse",
    }


def build_channel_doc(*, q_small: int = 16, qsc_p: float = 0.038,
                      run_id: str = "v19_channel") -> dict:
    """Build a small diagnostic channel document for N1 evidence.

    The document contains the V17 per-plane errors, the full q=1024 averaged
    raw-XOR distribution entropy, the folded small-q distribution, the QSC
    equal-entropy control, and the plain-f formula for the known q=16 rate
    0.60 boundary.
    """
    w_full = build_real_w_q1024()
    w_fold = build_folded_w(q_small)
    h_fold = float(symbol_entropy_bits(w_fold))
    w_qsc = build_qsc_w(q_small, qsc_p)
    h_qsc = float(symbol_entropy_bits(w_qsc))
    return {
        "schema": "nbldpc_v19_channel_v1",
        "run_id": run_id,
        "q_small": q_small,
        "qsc_p": qsc_p,
        "h_full_q1024": H_FULL_Q1024,
        "h_full_empirical": float(symbol_entropy_bits(w_full)),
        "h_folded": h_fold,
        "h_qsc_equal_entropy": h_qsc,
        "v17_per_plane_error": [float(x) for x in V17_PER_PLANE_ERROR],
        "per_plane_h2_bits": [float(binary_entropy_bits(float(x))) for x in V17_PER_PLANE_ERROR],
        "sum_per_plane_h2_bits": float(sum(binary_entropy_bits(float(x)) for x in V17_PER_PLANE_ERROR)),
        "folded_w": [float(x) for x in w_fold],
        "qsc_w": [float(x) for x in w_qsc],
        "f_plain_rate_0_60_q16": float(f_plain_qary(rate=0.60, q=q_small, h_bits=h_fold)),
        "notes": [
            "diagnostic_only; V17/V18 channel model reused read-only",
            "plain q=16 folded DE boundary from V18-B2: rate 0.60, f~4.18",
            "f<=1.3 on q=16 requires plain rate >= 0.8756 per route-b-c-d plan",
        ],
    }
