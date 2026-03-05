#!/usr/bin/env python3
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np


def _iter_sparse_entries(joint_counts_sparse: list[Any]) -> tuple[int, int, float]:
    for item in joint_counts_sparse:
        if isinstance(item, dict):
            i_raw = item.get("i")
            j_raw = item.get("j")
            c_raw = item.get("count")
        elif isinstance(item, (list, tuple)) and len(item) >= 3:
            i_raw, j_raw, c_raw = item[0], item[1], item[2]
        else:
            continue
        try:
            i = int(i_raw)
            j = int(j_raw)
            c = float(c_raw)
        except Exception:
            continue
        if i < 0 or j < 0:
            continue
        if (not math.isfinite(c)) or c <= 0.0:
            continue
        yield i, j, c


def coarse_grain_joint_dense(joint_dense: np.ndarray, factor: int = 2) -> np.ndarray:
    j = np.asarray(joint_dense, dtype=np.float64)
    if j.ndim != 2 or j.shape[0] != j.shape[1]:
        raise ValueError("joint_dense must be square [d,d]")
    d = int(j.shape[0])
    f = int(factor)
    if f <= 0:
        raise ValueError("factor must be >0")
    if d % f != 0:
        raise ValueError(f"dimension {d} not divisible by factor {f}")
    d2 = d // f
    # reshape -> sum over intra-bin axes
    out = j.reshape(d2, f, d2, f).sum(axis=(1, 3))
    return np.asarray(out, dtype=np.float64)


def coarse_grain_sparse_joint(
    joint_counts_sparse: list[Any],
    d: int,
    factor: int = 2,
) -> tuple[int, list[dict[str, float]]]:
    d0 = int(d)
    f = int(factor)
    if d0 <= 0:
        raise ValueError("d must be >0")
    if f <= 0:
        raise ValueError("factor must be >0")
    if d0 % f != 0:
        raise ValueError(f"dimension {d0} not divisible by factor {f}")
    d2 = d0 // f
    agg: dict[tuple[int, int], float] = defaultdict(float)
    for i, j, c in _iter_sparse_entries(joint_counts_sparse):
        if i >= d0 or j >= d0:
            continue
        ii = int(i) // f
        jj = int(j) // f
        agg[(ii, jj)] += float(c)
    out = [
        {"i": int(i), "j": int(j), "count": float(c)}
        for (i, j), c in agg.items()
        if c > 0.0
    ]
    out.sort(key=lambda x: (int(x["i"]), int(x["j"])))
    return d2, out


def dense_from_sparse(joint_counts_sparse: list[Any], d: int) -> np.ndarray:
    d0 = int(d)
    if d0 <= 0:
        raise ValueError("d must be >0")
    out = np.zeros((d0, d0), dtype=np.float64)
    for i, j, c in _iter_sparse_entries(joint_counts_sparse):
        if i >= d0 or j >= d0:
            continue
        out[int(i), int(j)] += float(c)
    return out


def coarse_grain_symbols_floor_div(symbols: np.ndarray, factor: int) -> np.ndarray:
    f = int(factor)
    if f <= 0:
        raise ValueError("factor must be >0")
    arr = np.asarray(symbols, dtype=np.int64)
    return (arr // f).astype(np.int64, copy=False)


def compute_info_from_joint(joint_dense: np.ndarray) -> dict[str, float]:
    j = np.asarray(joint_dense, dtype=np.float64)
    if j.ndim != 2 or j.shape[0] != j.shape[1]:
        raise ValueError("joint_dense must be square [d,d]")
    d = int(j.shape[0])
    tot = float(np.sum(j))
    if tot <= 0.0:
        raise ValueError("joint total count must be positive")
    p_ab = j / tot
    p_a = np.sum(p_ab, axis=1)
    p_b = np.sum(p_ab, axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        log_pa = np.where(p_a > 0.0, np.log2(p_a), 0.0)
    h_a = -float(np.sum(p_a * log_pa))
    h_cond = 0.0
    for b in range(d):
        pb = float(p_b[b])
        if pb <= 0.0:
            continue
        pab = p_ab[:, b]
        with np.errstate(divide="ignore", invalid="ignore"):
            pa_given_b = np.where(pab > 0.0, pab / pb, 0.0)
            log_cond = np.where(pa_given_b > 0.0, np.log2(pa_given_b), 0.0)
        h_cond += -float(np.sum(pab * log_cond))
    i_ab = float(h_a - h_cond)
    # modular delta entropy
    p_k = np.zeros((d,), dtype=np.float64)
    nz = np.argwhere(j > 0)
    for a, b in nz:
        p_k[(int(a) - int(b)) % d] += float(j[a, b])
    p_k /= float(np.sum(p_k))
    with np.errstate(divide="ignore", invalid="ignore"):
        log_pk = np.where(p_k > 0.0, np.log2(p_k), 0.0)
    h_k = -float(np.sum(p_k * log_pk))
    m_eff = float(2.0**h_k)
    return {
        "dimension": float(d),
        "sum_counts": float(tot),
        "H_A_bpc": float(h_a),
        "H_A_given_B_bpc": float(h_cond),
        "I_AB_bpc": float(i_ab),
        "H_K_bpc": float(h_k),
        "M_eff": float(m_eff),
    }
