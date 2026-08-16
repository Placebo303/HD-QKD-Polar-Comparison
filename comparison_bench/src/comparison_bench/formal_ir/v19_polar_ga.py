"""V19 Gaussian-approximation (GA) frozen-set construction for Polar MLC.

This is an experimental, non-frozen helper for selecting Polar info positions
on per-plane BSC channels. It does not modify the original Polar source.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm


def phi(x):
    """J-function approximation for BPSK/AWGN LLR mean (Erfanian et al.)."""
    x = np.asarray(x, dtype=np.float64)
    out = np.empty_like(x)
    small = x < 10.0
    out[small] = np.exp(-0.4527 * np.power(x[small], 0.86) + 0.0218)
    big = ~small
    out[big] = np.sqrt(np.pi / x[big]) * np.exp(-x[big] / 4.0) * (1.0 - 10.0 / (7.0 * x[big]))
    return out


def phi_inv(y, lo: float = 1e-9, hi: float = 60.0, iters: int = 60):
    """Inverse of phi via vectorized bisection."""
    y = np.asarray(y, dtype=np.float64)
    lo_arr = np.full_like(y, lo)
    hi_arr = np.full_like(y, hi)
    for _ in range(iters):
        mid = (lo_arr + hi_arr) / 2.0
        val = phi(mid)
        # phi is monotonically decreasing: if phi(mid) > y, mid is too small.
        lo_arr = np.where(val > y, mid, lo_arr)
        hi_arr = np.where(val > y, hi_arr, mid)
    return (lo_arr + hi_arr) / 2.0


def ga_llr_means(p: float, n: int) -> np.ndarray:
    """Return length-n LLR mean vector for BSC(p) using GA recursion."""
    if not (0.0 < p < 1.0):
        raise ValueError("p must be in (0,1)")
    if n <= 0 or (n & (n - 1)) != 0:
        raise ValueError("n must be a power of two")
    m0 = 2.0 * norm.isf(float(p)) ** 2
    m = np.asarray([m0], dtype=np.float64)
    levels = int(round(math.log2(n)))
    for _ in range(levels):
        left = phi_inv(1.0 - (1.0 - phi(m)) ** 2)
        right = 2.0 * m
        m = np.concatenate([left, right])
    return m


def ga_info_mask(p: float, n: int, k: int) -> np.ndarray:
    """Return uint8 mask with 1 at the k most reliable info positions."""
    means = ga_llr_means(p, n)
    order = np.argsort(means)[::-1]  # largest mean = most reliable
    info = order[:k]
    mask = np.zeros(n, dtype=np.uint8)
    mask[info] = 1
    return mask
