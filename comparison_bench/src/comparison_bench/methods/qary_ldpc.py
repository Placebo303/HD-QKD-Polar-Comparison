from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


PRIMITIVE_POLY = {
    1: 0b11,
    2: 0b111,
    3: 0b1011,
    4: 0b10011,
    5: 0b100101,
    6: 0b1000011,
    7: 0b10000011,
    8: 0b100011101,
}


@dataclass
class GF2m:
    q: int
    m: int
    exp: np.ndarray
    log: np.ndarray

    @classmethod
    def create(cls, q: int) -> "GF2m":
        q = int(q)
        if q < 2 or q & (q - 1):
            raise ValueError("fallback GF supports only q=2^m")
        m = int(np.log2(q))
        if m < 1 or m > 8:
            raise ValueError("fallback GF supports 2 <= q <= 256")
        prim = PRIMITIVE_POLY[m]
        exp = np.zeros(2 * (q - 1), dtype=np.int64)
        log = np.full(q, -1, dtype=np.int64)
        x = 1
        for i in range(q - 1):
            exp[i] = x
            log[x] = i
            x <<= 1
            if x & q:
                x ^= prim
            x &= q - 1
        exp[q - 1:] = exp[:q - 1]
        return cls(q=q, m=m, exp=exp, log=log)

    def add(self, a: Any, b: Any) -> Any:
        return np.bitwise_xor(a, b)

    def sub(self, a: Any, b: Any) -> Any:
        return np.bitwise_xor(a, b)

    def mul(self, a: Any, b: Any) -> Any:
        aa = np.asarray(a, dtype=np.int64)
        bb = np.asarray(b, dtype=np.int64)
        out = np.zeros(np.broadcast_shapes(aa.shape, bb.shape), dtype=np.int64)
        aaa = np.broadcast_to(aa, out.shape)
        bbb = np.broadcast_to(bb, out.shape)
        mask = (aaa != 0) & (bbb != 0)
        out[mask] = self.exp[(self.log[aaa[mask]] + self.log[bbb[mask]]) % (self.q - 1)]
        return int(out) if out.shape == () else out


def make_gf(q: int):
    try:
        import galois  # type: ignore

        return galois.GF(int(q))
    except Exception:
        return GF2m.create(int(q))


def gf_add(gf: Any, a: Any, b: Any) -> Any:
    if isinstance(gf, GF2m):
        return gf.add(a, b)
    return np.asarray(gf(a) + gf(b), dtype=np.int64)


def gf_sub(gf: Any, a: Any, b: Any) -> Any:
    if isinstance(gf, GF2m):
        return gf.sub(a, b)
    return np.asarray(gf(a) - gf(b), dtype=np.int64)


def gf_mul(gf: Any, a: Any, b: Any) -> Any:
    if isinstance(gf, GF2m):
        return gf.mul(a, b)
    return np.asarray(gf(a) * gf(b), dtype=np.int64)


def make_qary_ldpc_h(
    n_symbols: int,
    m_checks: int,
    q: int,
    row_weight: int,
    col_weight: int | None = None,
    seed: int = 0,
) -> np.ndarray:
    gf = make_gf(q)
    rng = np.random.default_rng(int(seed))
    n = max(1, int(n_symbols))
    m = max(1, int(m_checks))
    rw = max(1, min(int(row_weight), n))
    h = np.zeros((m, n), dtype=np.int64)
    for r in range(m):
        cols = rng.choice(n, size=rw, replace=False)
        h[r, cols] = rng.integers(1, int(q), size=rw, dtype=np.int64)
    if col_weight:
        cw = max(1, int(col_weight))
        for c in range(n):
            if np.count_nonzero(h[:, c]) < cw:
                rows = rng.choice(m, size=min(cw, m), replace=False)
                empty = h[rows, c] == 0
                h[rows[empty], c] = rng.integers(1, int(q), size=int(np.count_nonzero(empty)), dtype=np.int64)
    # Ensure each column is connected at least once.
    for c in np.where(np.count_nonzero(h, axis=0) == 0)[0]:
        h[int(rng.integers(0, m)), c] = int(rng.integers(1, int(q)))
    return h


def qary_syndrome(h: np.ndarray, x: np.ndarray, gf: Any) -> np.ndarray:
    h = np.asarray(h, dtype=np.int64)
    x = np.asarray(x, dtype=np.int64).reshape(-1)
    out = np.zeros(h.shape[0], dtype=np.int64)
    for r in range(h.shape[0]):
        acc = 0
        nz = np.nonzero(h[r])[0]
        for c in nz:
            acc = gf_add(gf, acc, gf_mul(gf, int(h[r, c]), int(x[c])))
        out[r] = int(acc)
    return out


def qary_symbol_error_syndrome(h: np.ndarray, alice: np.ndarray, bob: np.ndarray, gf: Any) -> np.ndarray:
    return gf_sub(gf, qary_syndrome(h, alice, gf), qary_syndrome(h, bob, gf)).astype(np.int64)


def _syndrome_weight(s: np.ndarray) -> int:
    return int(np.count_nonzero(np.asarray(s, dtype=np.int64)))


def _apply_symbol_error_to_syndrome(residual: np.ndarray, h_col: np.ndarray, err: int, gf: Any) -> np.ndarray:
    contribution = gf_mul(gf, h_col, int(err))
    return gf_sub(gf, residual, contribution).astype(np.int64)


def qary_hard_syndrome_bf(
    h: np.ndarray,
    syndrome_delta: np.ndarray,
    q: int,
    gf: Any,
    max_iter: int = 20,
) -> tuple[np.ndarray, bool, dict[str, Any]]:
    h = np.asarray(h, dtype=np.int64)
    residual = np.asarray(syndrome_delta, dtype=np.int64).reshape(-1).copy()
    n = h.shape[1]
    error = np.zeros(n, dtype=np.int64)
    initial = _syndrome_weight(residual)
    updates = 0
    for it in range(max(1, int(max_iter))):
        current = _syndrome_weight(residual)
        if current == 0:
            return error, True, {
                "iterations_used": it,
                "unsatisfied_checks_initial": initial,
                "unsatisfied_checks_final": 0,
                "syndrome_weight_initial": initial,
                "syndrome_weight_final": 0,
                "candidate_updates": updates,
            }
        best: tuple[int, int, np.ndarray, int] | None = None
        for c in range(n):
            if not np.any(h[:, c]):
                continue
            for err in range(1, int(q)):
                trial = _apply_symbol_error_to_syndrome(residual, h[:, c], err, gf)
                weight = _syndrome_weight(trial)
                if weight < current and (best is None or weight < best[3]):
                    best = (c, err, trial, weight)
                    if weight == 0:
                        break
            if best is not None and best[3] == 0:
                break
        if best is None:
            break
        c, err, residual, _weight = best
        error[c] = gf_add(gf, int(error[c]), err)
        updates += 1
    final = _syndrome_weight(residual)
    return error, final == 0, {
        "iterations_used": int(max_iter),
        "unsatisfied_checks_initial": initial,
        "unsatisfied_checks_final": final,
        "syndrome_weight_initial": initial,
        "syndrome_weight_final": final,
        "candidate_updates": updates,
    }


def h_density(h: np.ndarray) -> float:
    arr = np.asarray(h)
    return float(np.count_nonzero(arr) / arr.size) if arr.size else float("nan")
