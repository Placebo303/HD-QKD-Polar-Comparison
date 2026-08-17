"""V20 bounded-weight maximum-likelihood list decoder (diagnostic).

For very short high-rate q-ary LDPC codes (n<=64, m small) this module
implements a bounded-support ML decoder: it enumerates all error supports of
size up to ``max_weight``, solves the GF(q) linear system for each support, and
returns the syndrome-consistent error vector with the largest channel prior
score.  It is independent of BP/OSD information-set ordering.

The heavy k=4 enumeration is implemented with numba for speed.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_v19_osd import osd_decode_candidates_bounded_weight

__all__ = ["bounded_weight_ml_decode", "bounded_weight_ml_decode_candidates"]


def _log_score(e: Sequence[int], logw: np.ndarray) -> float:
    return float(np.sum(logw[np.asarray(e, dtype=np.int64)]))


def _python_ml_up_to_3(*, field: GF2mField, matrix: Any, syndrome: Sequence[int],
                       logw: np.ndarray, max_weight: int) -> list[int] | None:
    """Exact ML search over supports of size 1..max_weight (max_weight<=3)."""
    if int(max_weight) > 3:
        raise ValueError("python ML path only supports max_weight<=3")
    cands = osd_decode_candidates_bounded_weight(
        field=field, matrix=matrix, syndrome=syndrome,
        max_weight=int(max_weight), max_candidates=2000000)
    if not cands:
        return None
    best = None
    best_score = -1e100
    for e in cands:
        sc = _log_score(e, logw)
        if sc > best_score:
            best_score = sc
            best = list(e)
    return best


# ---------------------------------------------------------------------------
# Numba k=4 ML enumeration
# ---------------------------------------------------------------------------
try:
    from numba import njit

    @njit(cache=True)
    def _gf_mul(a: int, b: int, exp: np.ndarray, log: np.ndarray, q: int) -> int:
        if a == 0 or b == 0:
            return 0
        return exp[(log[a] + log[b]) % (q - 1)]

    @njit(cache=True)
    def _solve4(A: np.ndarray, s: np.ndarray, exp: np.ndarray,
                log: np.ndarray, q: int):
        M = np.empty((4, 5), dtype=np.int64)
        for i in range(4):
            for j in range(4):
                M[i, j] = A[i, j]
            M[i, 4] = s[i]
        row = 0
        for col in range(4):
            piv = -1
            for i in range(row, 4):
                if M[i, col] != 0:
                    piv = i
                    break
            if piv == -1:
                return np.zeros(4, dtype=np.int64), False
            if piv != row:
                for j in range(5):
                    tmp = M[row, j]
                    M[row, j] = M[piv, j]
                    M[piv, j] = tmp
            v = M[row, col]
            inv = exp[(-log[v]) % (q - 1)] if v != 0 else 0
            for j in range(col, 5):
                M[row, j] = _gf_mul(M[row, j], inv, exp, log, q)
            for i in range(4):
                if i != row and M[i, col] != 0:
                    factor = M[i, col]
                    for j in range(col, 5):
                        M[i, j] ^= _gf_mul(factor, M[row, j], exp, log, q)
            row += 1
        x = np.zeros(4, dtype=np.int64)
        for i in range(4):
            x[i] = M[i, 4]
        return x, True

    @njit(cache=True)
    def _bounded4_ml(H: np.ndarray, s: np.ndarray, logw: np.ndarray,
                     exp: np.ndarray, log: np.ndarray, q: int):
        n = H.shape[1]
        best_score = -1e100
        best = np.zeros(8, dtype=np.int64)
        found = False
        base_log0 = logw[0] * (n - 4)
        for i in range(n):
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    for l in range(k + 1, n):
                        A = np.empty((4, 4), dtype=np.int64)
                        A[0, 0] = H[0, i]; A[0, 1] = H[0, j]; A[0, 2] = H[0, k]; A[0, 3] = H[0, l]
                        A[1, 0] = H[1, i]; A[1, 1] = H[1, j]; A[1, 2] = H[1, k]; A[1, 3] = H[1, l]
                        A[2, 0] = H[2, i]; A[2, 1] = H[2, j]; A[2, 2] = H[2, k]; A[2, 3] = H[2, l]
                        A[3, 0] = H[3, i]; A[3, 1] = H[3, j]; A[3, 2] = H[3, k]; A[3, 3] = H[3, l]
                        x, ok = _solve4(A, s, exp, log, q)
                        if not ok:
                            continue
                        ok2 = True
                        for r in range(4):
                            acc = 0
                            acc ^= _gf_mul(H[r, i], x[0], exp, log, q)
                            acc ^= _gf_mul(H[r, j], x[1], exp, log, q)
                            acc ^= _gf_mul(H[r, k], x[2], exp, log, q)
                            acc ^= _gf_mul(H[r, l], x[3], exp, log, q)
                            if acc != s[r]:
                                ok2 = False
                                break
                        if not ok2:
                            continue
                        score = base_log0 + logw[x[0]] + logw[x[1]] + logw[x[2]] + logw[x[3]]
                        if score > best_score:
                            best_score = score
                            best[0] = i; best[1] = j; best[2] = k; best[3] = l
                            best[4] = x[0]; best[5] = x[1]; best[6] = x[2]; best[7] = x[3]
                            found = True
        return best, found, best_score


    @njit(cache=True)
    def _solve5(A: np.ndarray, s: np.ndarray, exp: np.ndarray,
                log: np.ndarray, q: int):
        M = np.empty((5, 6), dtype=np.int64)
        for i in range(5):
            for j in range(5):
                M[i, j] = A[i, j]
            M[i, 5] = s[i]
        row = 0
        for col in range(5):
            piv = -1
            for i in range(row, 5):
                if M[i, col] != 0:
                    piv = i
                    break
            if piv == -1:
                return np.zeros(5, dtype=np.int64), False
            if piv != row:
                for j in range(6):
                    tmp = M[row, j]
                    M[row, j] = M[piv, j]
                    M[piv, j] = tmp
            v = M[row, col]
            inv = exp[(-log[v]) % (q - 1)] if v != 0 else 0
            for j in range(col, 6):
                M[row, j] = _gf_mul(M[row, j], inv, exp, log, q)
            for i in range(5):
                if i != row and M[i, col] != 0:
                    factor = M[i, col]
                    for j in range(col, 6):
                        M[i, j] ^= _gf_mul(factor, M[row, j], exp, log, q)
            row += 1
        x = np.zeros(5, dtype=np.int64)
        for i in range(5):
            x[i] = M[i, 5]
        return x, True

    @njit(cache=True)
    def _bounded5_ml(H: np.ndarray, s: np.ndarray, logw: np.ndarray,
                     exp: np.ndarray, log: np.ndarray, q: int):
        n = H.shape[1]
        best_score = -1e100
        best = np.zeros(10, dtype=np.int64)
        found = False
        base_log0 = logw[0] * (n - 5)
        for i0 in range(n):
            for i1 in range(i0 + 1, n):
                for i2 in range(i1 + 1, n):
                    for i3 in range(i2 + 1, n):
                        for i4 in range(i3 + 1, n):
                            A = np.empty((5, 5), dtype=np.int64)
                            A[0,0]=H[0,i0]; A[0,1]=H[0,i1]; A[0,2]=H[0,i2]; A[0,3]=H[0,i3]; A[0,4]=H[0,i4]
                            A[1,0]=H[1,i0]; A[1,1]=H[1,i1]; A[1,2]=H[1,i2]; A[1,3]=H[1,i3]; A[1,4]=H[1,i4]
                            A[2,0]=H[2,i0]; A[2,1]=H[2,i1]; A[2,2]=H[2,i2]; A[2,3]=H[2,i3]; A[2,4]=H[2,i4]
                            A[3,0]=H[3,i0]; A[3,1]=H[3,i1]; A[3,2]=H[3,i2]; A[3,3]=H[3,i3]; A[3,4]=H[3,i4]
                            A[4,0]=H[4,i0]; A[4,1]=H[4,i1]; A[4,2]=H[4,i2]; A[4,3]=H[4,i3]; A[4,4]=H[4,i4]
                            x, ok = _solve5(A, s, exp, log, q)
                            if not ok:
                                continue
                            ok2 = True
                            for r in range(5):
                                acc = 0
                                acc ^= _gf_mul(H[r,i0], x[0], exp, log, q)
                                acc ^= _gf_mul(H[r,i1], x[1], exp, log, q)
                                acc ^= _gf_mul(H[r,i2], x[2], exp, log, q)
                                acc ^= _gf_mul(H[r,i3], x[3], exp, log, q)
                                acc ^= _gf_mul(H[r,i4], x[4], exp, log, q)
                                if acc != s[r]:
                                    ok2 = False
                                    break
                            if not ok2:
                                continue
                            score = base_log0 + logw[x[0]] + logw[x[1]] + logw[x[2]] + logw[x[3]] + logw[x[4]]
                            if score > best_score:
                                best_score = score
                                best[0]=i0; best[1]=i1; best[2]=i2; best[3]=i3; best[4]=i4
                                best[5]=x[0]; best[6]=x[1]; best[7]=x[2]; best[8]=x[3]; best[9]=x[4]
                                found = True
        return best, found, best_score


    @njit(cache=True)
    def _bounded5_topk(H: np.ndarray, s: np.ndarray, logw: np.ndarray,
                       exp: np.ndarray, log: np.ndarray, q: int, K: int):
        n = H.shape[1]
        top_scores = np.full(K, -1e100)
        top_data = np.zeros((K, 10), dtype=np.int64)
        base_log0 = logw[0] * (n - 5)
        for i0 in range(n):
            for i1 in range(i0 + 1, n):
                for i2 in range(i1 + 1, n):
                    for i3 in range(i2 + 1, n):
                        for i4 in range(i3 + 1, n):
                            A = np.empty((5, 5), dtype=np.int64)
                            A[0,0]=H[0,i0]; A[0,1]=H[0,i1]; A[0,2]=H[0,i2]; A[0,3]=H[0,i3]; A[0,4]=H[0,i4]
                            A[1,0]=H[1,i0]; A[1,1]=H[1,i1]; A[1,2]=H[1,i2]; A[1,3]=H[1,i3]; A[1,4]=H[1,i4]
                            A[2,0]=H[2,i0]; A[2,1]=H[2,i1]; A[2,2]=H[2,i2]; A[2,3]=H[2,i3]; A[2,4]=H[2,i4]
                            A[3,0]=H[3,i0]; A[3,1]=H[3,i1]; A[3,2]=H[3,i2]; A[3,3]=H[3,i3]; A[3,4]=H[3,i4]
                            A[4,0]=H[4,i0]; A[4,1]=H[4,i1]; A[4,2]=H[4,i2]; A[4,3]=H[4,i3]; A[4,4]=H[4,i4]
                            x, ok = _solve5(A, s, exp, log, q)
                            if not ok:
                                continue
                            ok2 = True
                            for r in range(5):
                                acc = 0
                                acc ^= _gf_mul(H[r,i0], x[0], exp, log, q)
                                acc ^= _gf_mul(H[r,i1], x[1], exp, log, q)
                                acc ^= _gf_mul(H[r,i2], x[2], exp, log, q)
                                acc ^= _gf_mul(H[r,i3], x[3], exp, log, q)
                                acc ^= _gf_mul(H[r,i4], x[4], exp, log, q)
                                if acc != s[r]:
                                    ok2 = False
                                    break
                            if not ok2:
                                continue
                            score = base_log0 + logw[x[0]] + logw[x[1]] + logw[x[2]] + logw[x[3]] + logw[x[4]]
                            # Insert into top K if applicable.
                            if score > top_scores[K - 1]:
                                pos = K - 1
                                while pos > 0 and score > top_scores[pos - 1]:
                                    top_scores[pos] = top_scores[pos - 1]
                                    for t in range(10):
                                        top_data[pos, t] = top_data[pos - 1, t]
                                    pos -= 1
                                top_scores[pos] = score
                                top_data[pos, 0]=i0; top_data[pos,1]=i1; top_data[pos,2]=i2; top_data[pos,3]=i3; top_data[pos,4]=i4
                                top_data[pos,5]=x[0]; top_data[pos,6]=x[1]; top_data[pos,7]=x[2]; top_data[pos,8]=x[3]; top_data[pos,9]=x[4]
        return top_scores, top_data

    _HAS_NUMBA = True
except Exception:  # pragma: no cover - optional dependency guard
    _HAS_NUMBA = False


def bounded_weight_ml_decode(*, field: GF2mField, matrix: Any,
                             syndrome: Sequence[int], w: Any,
                             max_weight: int = 4) -> list[int] | None:
    """Return the most likely bounded-weight error vector, or None.

    ``w`` is the length-q channel prior (or per-symbol prior is not supported
    here).  Only small ``max_weight`` (<=4 for n<=64; max_weight=5 for n<=80)
    is intended.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    if int(max_weight) < 1 or int(max_weight) > 5:
        raise ValueError("max_weight must be in 1..5")
    matrix = np.asarray(matrix, dtype=np.int64)
    n = matrix.shape[1]
    m = matrix.shape[0]
    if int(max_weight) <= 4 and n > 64:
        raise ValueError("bounded_weight_ml_decode max_weight<=4 is intended for n<=64")
    if int(max_weight) == 5 and (n > 80 or m < 5):
        raise ValueError("bounded_weight_ml_decode max_weight=5 is intended for n<=80 and m>=5")
    w = np.asarray(w, dtype=np.float64)
    if w.shape != (field.q,):
        raise ValueError("w must be a length-q vector")
    if not np.all(np.isfinite(w)) or np.any(w < 0.0):
        raise ValueError("w must be finite and non-negative")
    if not np.isclose(float(w.sum()), 1.0, atol=1e-9):
        w = w / float(w.sum())
    logw = np.log(np.maximum(w, 1e-300))
    syndrome = [int(x) for x in syndrome]

    best: list[int] | None = None
    best_score = -1e100
    if int(max_weight) <= 3:
        cand = _python_ml_up_to_3(
            field=field, matrix=matrix, syndrome=syndrome,
            logw=logw, max_weight=int(max_weight))
        if cand is not None:
            sc = _log_score(cand, logw)
            if sc > best_score:
                best_score = sc
                best = cand
        return best

    # Combine python k<=3 with the numba k=4 or k=5 search.
    cand3 = _python_ml_up_to_3(
        field=field, matrix=matrix, syndrome=syndrome,
        logw=logw, max_weight=3)
    if cand3 is not None:
        sc = _log_score(cand3, logw)
        if sc > best_score:
            best_score = sc
            best = cand3
    if not _HAS_NUMBA:  # pragma: no cover - optional dependency guard
        return best
    exp = np.asarray(field.nonzero_cycle, dtype=np.int64)
    log = np.full(field.q, -1, dtype=np.int64)
    for idx, v in enumerate(exp):
        log[v] = idx
    if int(max_weight) == 4:
        best4, found4, score4 = _bounded4_ml(
            matrix, np.asarray(syndrome, dtype=np.int64), logw, exp, log, field.q)
        if found4 and score4 > best_score:
            e = [0] * n
            e[int(best4[0])] = int(best4[4])
            e[int(best4[1])] = int(best4[5])
            e[int(best4[2])] = int(best4[6])
            e[int(best4[3])] = int(best4[7])
            best = e
            best_score = float(score4)
    else:  # max_weight == 5
        best5, found5, score5 = _bounded5_ml(
            matrix, np.asarray(syndrome, dtype=np.int64), logw, exp, log, field.q)
        if found5 and score5 > best_score:
            e = [0] * n
            e[int(best5[0])] = int(best5[5])
            e[int(best5[1])] = int(best5[6])
            e[int(best5[2])] = int(best5[7])
            e[int(best5[3])] = int(best5[8])
            e[int(best5[4])] = int(best5[9])
            best = e
            best_score = float(score5)
    return best


def bounded_weight_ml_decode_candidates(*, field: GF2mField, matrix: Any,
                                        syndrome: Sequence[int], w: Any,
                                        max_weight: int = 5,
                                        top_k: int = 4) -> list[list[int]]:
    """Return up to ``top_k`` most likely bounded-weight error vectors.

    This is the list-decoding variant of :func:`bounded_weight_ml_decode`.
    It is intended for V20 diagnostic evaluation where a short public hash could
    later select among the returned candidates.  Currently supports
    ``max_weight=5`` / n<=80,m>=5.
    """
    if int(max_weight) != 5:
        raise ValueError("bounded_weight_ml_decode_candidates currently supports max_weight=5 only")
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    matrix = np.asarray(matrix, dtype=np.int64)
    n = matrix.shape[1]
    m = matrix.shape[0]
    if n > 80 or m < 5:
        raise ValueError("max_weight=5 list decoding is intended for n<=80 and m>=5")
    w = np.asarray(w, dtype=np.float64)
    if w.shape != (field.q,):
        raise ValueError("w must be a length-q vector")
    if not np.all(np.isfinite(w)) or np.any(w < 0.0):
        raise ValueError("w must be finite and non-negative")
    if not np.isclose(float(w.sum()), 1.0, atol=1e-9):
        w = w / float(w.sum())
    logw = np.log(np.maximum(w, 1e-300))
    syndrome = [int(x) for x in syndrome]
    K = int(top_k)
    if K < 1:
        raise ValueError("top_k must be >=1")

    # k<=3 candidates from the existing bounded-weight enumerator.
    cands3 = osd_decode_candidates_bounded_weight(
        field=field, matrix=matrix, syndrome=syndrome,
        max_weight=3, max_candidates=2000000)
    scored: list[tuple[float, list[int]]] = []
    for e in cands3:
        sc = _log_score(e, logw)
        scored.append((sc, list(e)))
    # k=5 top candidates from numba.
    if _HAS_NUMBA:
        exp = np.asarray(field.nonzero_cycle, dtype=np.int64)
        log = np.full(field.q, -1, dtype=np.int64)
        for idx, v in enumerate(exp):
            log[v] = idx
        top_scores, top_data = _bounded5_topk(
            matrix, np.asarray(syndrome, dtype=np.int64), logw, exp, log,
            field.q, K)
        for r in range(K):
            if top_scores[r] <= -1e99:
                continue
            e = [0] * n
            e[int(top_data[r,0])] = int(top_data[r,5])
            e[int(top_data[r,1])] = int(top_data[r,6])
            e[int(top_data[r,2])] = int(top_data[r,7])
            e[int(top_data[r,3])] = int(top_data[r,8])
            e[int(top_data[r,4])] = int(top_data[r,9])
            scored.append((float(top_scores[r]), e))
    # Deduplicate by tuple and keep top K.
    seen = set()
    uniq: list[tuple[float, list[int]]] = []
    for sc, e in scored:
        t = tuple(e)
        if t in seen:
            continue
        seen.add(t)
        uniq.append((sc, e))
    uniq.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in uniq[:K]]
