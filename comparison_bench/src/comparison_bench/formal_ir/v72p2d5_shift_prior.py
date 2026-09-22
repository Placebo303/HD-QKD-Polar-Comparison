"""Shift/delta structured prior (S1, additive-only).

Frozen scope: q[delta] = sum_b counts[(b+delta) % A, b] / N with fallback
P(a|b) = (q[(a-b) % A] + eps * p_global[a]) / (1 + eps). Pure function of the
injected counts table; no file read, no decoder, no graph. Downstream reuses
the frozen marginalize/conditionalize helpers by import (never copied here).

State firewall: the legacy frozen concentration constant from the
nonparametric backoff has different semantics and is never imported,
referenced, or reused on this path (not even as a default).
"""
from __future__ import annotations

import numpy as np

DEFAULT_EPS = 1e-4


def build_shift_prior_concentration(counts_ab, eps=DEFAULT_EPS):
    """Build P(A|B) from the pooled shift histogram with eps fallback.

    Same call shape as the nonparametric concentration builder
    ``(counts_ab, scalar=...)``; every column sums to 1 within 1e-12.
    An all-zero Bob column falls back naturally (same q row); an all-zero
    table raises. Deterministic in its inputs.
    """
    counts = np.asarray(counts_ab, dtype=np.float64)
    if counts.ndim != 2 or counts.shape[0] < 1 or counts.shape[1] < 1:
        raise ValueError("counts_ab must be a non-empty 2-D (Alice, Bob) table")
    if not np.all(np.isfinite(counts)):
        raise ValueError("counts_ab must be finite")
    if np.any(counts < 0):
        raise ValueError("counts_ab must be nonnegative")
    eps = float(eps)
    if not np.isfinite(eps) or eps < 0:
        raise ValueError("eps must be a finite nonnegative concentration")
    total = float(counts.sum())
    if total <= 0:
        raise ValueError("counts are all zero")
    n_a, n_b = counts.shape
    p_global = counts.sum(axis=1) / total
    # ponytail: O(A*B) loop, vectorize only if widths grow past 1024.
    q = np.zeros(n_a, dtype=np.float64)
    for b in range(n_b):
        q += np.roll(counts[:, b], int((-b) % n_a))
    q /= total
    avec = np.arange(n_a)[:, None]
    bvec = np.arange(n_b)[None, :]
    p = (q[(avec - bvec) % n_a] + eps * p_global[:, None]) / (1.0 + eps)
    col = p.sum(axis=0)
    if not np.all(np.abs(col - 1.0) <= 1e-12):
        raise ValueError("shift P columns must sum to 1 within 1e-12")
    return p
