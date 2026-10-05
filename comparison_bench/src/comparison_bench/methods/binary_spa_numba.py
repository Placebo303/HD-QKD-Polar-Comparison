"""Numba port of the binary syndrome min-sum kernel (M3, R7 enabling work).

Bit-identical target: :func:`decode_error_min_sum_llr` in
``formal_ir.msd_m1_synthetic`` (which mirrors ``methods.binary_spa_numpy``
message rules with a per-variable LLR prior). Same check-neighbor order,
same exact-zero sign convention, same syndrome-sign rule, same degree-1 pin
magnitude, same row-order accumulation and extrinsic rebuild. No
algorithmic change: no pruning, no first-valid, no schedule change.
"""

from __future__ import annotations

import numpy as np
from numba import njit

PIN_MAG = 1e6


@njit(cache=True)
def _min_sum_llr_numba(
    row_ptr: np.ndarray,
    col_idx: np.ndarray,
    syndrome: np.ndarray,
    llr0: np.ndarray,
    max_iter: int,
    out_err: np.ndarray,
    out_tot: np.ndarray,
) -> tuple[bool, int]:
    m = syndrome.shape[0]
    n = llr0.shape[0]
    v2c = np.zeros((m, n), dtype=np.float64)
    for c in range(m):
        for k in range(row_ptr[c], row_ptr[c + 1]):
            v2c[c, col_idx[k]] = llr0[col_idx[k]]
    c2v = np.zeros((m, n), dtype=np.float64)
    tot = np.empty(n, dtype=np.float64)
    for v in range(n):
        tot[v] = llr0[v]
    err = np.empty(n, dtype=np.uint8)
    for v in range(n):
        err[v] = 1 if tot[v] < 0.0 else 0
    # initial syndrome check
    ok = True
    for c in range(m):
        acc = 0
        for k in range(row_ptr[c], row_ptr[c + 1]):
            acc ^= int(err[col_idx[k]])
        if acc != int(syndrome[c]):
            ok = False
            break
    if ok:
        for v in range(n):
            out_err[v] = err[v]
            out_tot[v] = tot[v]
        return True, 0
    for it in range(1, max_iter + 1):
        for c in range(m):
            start = row_ptr[c]
            stop = row_ptr[c + 1]
            deg = stop - start
            if deg == 0:
                continue
            flip = -1.0 if syndrome[c] == 1 else 1.0
            for i in range(deg):
                v = col_idx[start + i]
                if deg == 1:
                    c2v[c, v] = flip * PIN_MAG
                    continue
                s = flip
                best = np.inf
                for k in range(deg):
                    if k == i:
                        continue
                    u = col_idx[start + k]
                    msg = v2c[c, u]
                    s *= -1.0 if msg < 0.0 else 1.0
                    a = msg if msg >= 0.0 else -msg
                    if a < best:
                        best = a
                c2v[c, v] = s * best
        for v in range(n):
            acc = llr0[v]
            for c in range(m):
                acc += c2v[c, v]
            tot[v] = acc
            err[v] = 1 if acc < 0.0 else 0
        for c in range(m):
            for k in range(row_ptr[c], row_ptr[c + 1]):
                v = col_idx[k]
                v2c[c, v] = tot[v] - c2v[c, v]
        ok = True
        for c in range(m):
            acc = 0
            for k in range(row_ptr[c], row_ptr[c + 1]):
                acc ^= int(err[col_idx[k]])
            if acc != int(syndrome[c]):
                ok = False
                break
        if ok:
            for v in range(n):
                out_err[v] = err[v]
                out_tot[v] = tot[v]
            return True, it
    for v in range(n):
        out_err[v] = err[v]
        out_tot[v] = tot[v]
    return False, max_iter


def decode_error_min_sum_llr_numba(
    h_dense: np.ndarray,
    syndrome: np.ndarray,
    llr0: np.ndarray,
    max_iter: int = 100,
) -> tuple[np.ndarray, bool, int, np.ndarray]:
    """Numba port entry point; returns (err, ok, iters, tot).

    ``tot`` is returned so tests can assert bit-identical soft state, not
    just identical hard decisions.
    """
    h = np.asarray(h_dense, dtype=np.uint8)
    d = np.asarray(syndrome, dtype=np.uint8).reshape(-1)
    v0 = np.asarray(llr0, dtype=np.float64).reshape(-1)
    m, n = int(h.shape[0]), int(h.shape[1])
    if d.shape != (m,) or v0.shape != (n,):
        raise ValueError("shape mismatch (fail closed)")
    if isinstance(max_iter, bool):
        raise ValueError("max_iter must be an int (fail closed)")
    max_iter = int(max_iter)
    if max_iter < 1:
        raise ValueError("max_iter must be >= 1 (fail closed)")
    indptr = np.zeros(m + 1, dtype=np.int64)
    cols: list = []
    for c in range(m):
        nb = np.flatnonzero(h[c])
        indptr[c + 1] = indptr[c] + nb.size
        cols.extend(int(v) for v in nb)
    col_idx = np.asarray(cols, dtype=np.int64)
    out_err = np.empty(n, dtype=np.uint8)
    out_tot = np.empty(n, dtype=np.float64)
    ok, iters = _min_sum_llr_numba(indptr, col_idx, d, v0, max_iter, out_err, out_tot)
    return out_err, bool(ok), int(iters), out_tot
