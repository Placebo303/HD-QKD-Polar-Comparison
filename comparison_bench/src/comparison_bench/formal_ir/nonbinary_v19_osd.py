"""V19 bounded q-ary OSD helper (diagnostic).

This module provides a small GF(q) Gaussian-elimination based OSD-0/1
post-processor.  It is additive and intended for diagnostic finite-length
q=1024 experiments only.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from .nonbinary_field import GF2mField

__all__ = [
    "gf_rref", "solve_with_free", "osd_decode", "osd_decode_candidates",
    "osd_decode_candidates_order2", "osd_decode_candidates_fast",
    "osd_decode_candidates_order2_fast", "osd_decode_candidates_order3_fast",
    "osd_decode_candidates_order4_fast", "osd_decode_candidates_fast_generic",
    "osd_decode_candidates_mrb",
]


def _reliability(beliefs: np.ndarray, hard: Sequence[int]) -> dict[int, float]:
    """Return per-variable reliability as max-posterior minus second-max.

    Lower values mean less reliable, which is a better OSD ordering than the
    raw max posterior when all variables have similar scales.
    """
    out = {}
    for i in range(len(hard)):
        row = beliefs[i]
        top = np.sort(row)[::-1]
        out[i] = float(top[0] - top[1]) if len(top) > 1 else float(top[0])
    return out


def gf_rref(field: GF2mField, matrix: Any, syndrome: Sequence[int]):
    """Return (rref, pivot_cols) for the augmented system [H | s] over GF(q).

    ``rref`` is a list of rows with length n+1 (last column is the syndrome).
    ``pivot_cols`` is the list of pivot column indices in row order.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    a = [[int(x) for x in row] + [int(s)] for row, s in zip(matrix, syndrome)]
    m = len(a)
    if m == 0:
        return [], []
    n = len(a[0]) - 1
    pivot_cols = []
    row = 0
    for col in range(n):
        pivot = None
        for i in range(row, m):
            if a[i][col] != 0:
                pivot = i
                break
        if pivot is None:
            continue
        a[row], a[pivot] = a[pivot], a[row]
        inv = field.inverse(a[row][col])
        a[row] = [field.mul(v, inv) for v in a[row]]
        for i in range(m):
            if i != row and a[i][col] != 0:
                factor = a[i][col]
                a[i] = [field.add(x, field.mul(factor, y))
                        for x, y in zip(a[i], a[row])]
        pivot_cols.append(col)
        row += 1
        if row == m:
            break
    # Check inconsistency: zero row with nonzero syndrome.
    for i in range(row, m):
        if any(a[i][j] != 0 for j in range(n)) is False and a[i][n] != 0:
            raise ValueError("inconsistent linear system")
    return a, pivot_cols


def solve_with_free(field: GF2mField, rref: Sequence[Sequence[int]],
                    pivot_cols: Sequence[int], free_assign: dict[int, int],
                    n: int) -> list[int] | None:
    """Solve the RREF system given assignments to all free (non-pivot) columns.

    ``free_assign`` must contain every non-pivot column index.  Returns the
    solution vector or None if inconsistent.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    x = [0] * n
    for col, val in free_assign.items():
        x[int(col)] = int(val)
    pivot_set = set(int(p) for p in pivot_cols)
    for row, pivot_col in enumerate(pivot_cols):
        # x[pivot] = rhs - sum_{j != pivot} a[row,j] * x[j]
        acc = int(rref[row][-1])
        for j in range(n):
            if j == pivot_col:
                continue
            coeff = int(rref[row][j])
            if coeff != 0:
                acc = field.add(acc, field.mul(coeff, x[j]))
        x[pivot_col] = acc
    # Verify all rows.
    for row in rref:
        total = 0
        for j in range(n):
            coeff = int(row[j])
            if coeff != 0:
                total = field.add(total, field.mul(coeff, x[j]))
        if total != int(row[-1]):
            return None
    return x


def osd_decode(*, field: GF2mField, matrix: Any, syndrome: Sequence[int],
               beliefs: Any = None, e_hat: Sequence[int] | None = None,
               order: int = 0, top_info: int = 8) -> list[int] | None:
    """Bounded OSD decode.

    Uses the BP hard decision (or the most-likely symbols from beliefs) as the
    initial free-variable assignment, then tries OSD-0 and optionally OSD-1 on
    the ``top_info`` least reliable free variables.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    matrix = np.asarray(matrix, dtype=np.int64)
    m, n = matrix.shape
    rref, pivots = gf_rref(field, matrix.tolist(), list(syndrome))
    free_cols = [j for j in range(n) if j not in set(int(p) for p in pivots)]
    # Initial hard decision.
    if e_hat is not None:
        hard = [int(x) for x in e_hat]
    elif beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        hard = [int(np.argmax(beliefs[i])) for i in range(n)]
    else:
        hard = [0] * n
    # Reliability ordering for free cols.
    if beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        rel = _reliability(beliefs, hard)
        free_ordered = sorted(free_cols, key=lambda i: rel.get(i, 0.0))
    else:
        free_ordered = list(free_cols)
    # OSD-0
    assign = {i: hard[i] for i in free_cols}
    sol = solve_with_free(field, rref, pivots, assign, n)
    if sol is not None:
        return sol
    if order < 1:
        return None
    # OSD-1 on least reliable free variables
    for i in free_ordered[:top_info]:
        for cand in range(field.q):
            if cand == hard[i]:
                continue
            assign2 = dict(assign)
            assign2[i] = cand
            sol = solve_with_free(field, rref, pivots, assign2, n)
            if sol is not None:
                return sol
    return None


def osd_decode_candidates(*, field: GF2mField, matrix: Any, syndrome: Sequence[int],
                          beliefs: Any = None, e_hat: Sequence[int] | None = None,
                          order: int = 1, top_info: int = 4,
                          max_candidates: int = 2000) -> list[list[int]]:
    """Return multiple OSD candidate solutions (diagnostic).

    Similar to :func:`osd_decode`, but collects up to ``max_candidates`` valid
    syndrome-consistent solutions from OSD-0 and OSD-1 flips.  This lets a
    caller test whether any candidate equals Alice's word.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    matrix = np.asarray(matrix, dtype=np.int64)
    m, n = matrix.shape
    rref, pivots = gf_rref(field, matrix.tolist(), list(syndrome))
    free_cols = [j for j in range(n) if j not in set(int(p) for p in pivots)]
    if e_hat is not None:
        hard = [int(x) for x in e_hat]
    elif beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        hard = [int(np.argmax(beliefs[i])) for i in range(n)]
    else:
        hard = [0] * n
    if beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        rel = _reliability(beliefs, hard)
        free_ordered = sorted(free_cols, key=lambda i: rel.get(i, 0.0))
    else:
        free_ordered = list(free_cols)
    candidates: list[list[int]] = []
    assign = {i: hard[i] for i in free_cols}
    sol = solve_with_free(field, rref, pivots, assign, n)
    if sol is not None:
        candidates.append(sol)
    if order < 1:
        return candidates
    for i in free_ordered[:top_info]:
        for cand in range(field.q):
            if cand == hard[i]:
                continue
            assign2 = dict(assign)
            assign2[i] = cand
            sol = solve_with_free(field, rref, pivots, assign2, n)
            if sol is not None:
                candidates.append(sol)
                if len(candidates) >= max_candidates:
                    return candidates
    return candidates


def osd_decode_candidates_order2(*, field: GF2mField, matrix: Any, syndrome: Sequence[int],
                                 beliefs: Any = None, e_hat: Sequence[int] | None = None,
                                 top_info: int = 4, top_symbols: int = 12,
                                 max_candidates: int = 4000) -> list[list[int]]:
    """Bounded OSD-2 candidate enumeration.

    Enumerates pairs of free-variable flips using only the ``top_symbols``
    most likely alternative symbols per variable.  This is a diagnostic
    approximation of order-2 OSD that is feasible for q=1024.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    matrix = np.asarray(matrix, dtype=np.int64)
    m, n = matrix.shape
    rref, pivots = gf_rref(field, matrix.tolist(), list(syndrome))
    free_cols = [j for j in range(n) if j not in set(int(p) for p in pivots)]
    if e_hat is not None:
        hard = [int(x) for x in e_hat]
    elif beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        hard = [int(np.argmax(beliefs[i])) for i in range(n)]
    else:
        hard = [0] * n
    if beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        rel = _reliability(beliefs, hard)
        free_ordered = sorted(free_cols, key=lambda i: rel.get(i, 0.0))[:int(top_info)]
    else:
        free_ordered = list(free_cols)[:int(top_info)]
    candidates: list[list[int]] = []
    assign0 = {i: hard[i] for i in free_cols}
    sol0 = solve_with_free(field, rref, pivots, assign0, n)
    if sol0 is not None:
        candidates.append(sol0)
    # Precompute candidate symbol lists.
    cands = {}
    for i in free_ordered:
        if beliefs is not None and beliefs.shape == (n, field.q):
            top = set(np.argsort(beliefs[i])[::-1][:int(top_symbols)].tolist())
            top.add(hard[i])
            cands[i] = sorted(top)
        else:
            cands[i] = list(range(field.q))
    for idx_a in range(len(free_ordered)):
        i = free_ordered[idx_a]
        for idx_b in range(idx_a + 1, len(free_ordered)):
            j = free_ordered[idx_b]
            for a in cands[i]:
                for b in cands[j]:
                    if a == hard[i] and b == hard[j]:
                        continue
                    assign = dict(assign0)
                    assign[i] = a
                    assign[j] = b
                    sol = solve_with_free(field, rref, pivots, assign, n)
                    if sol is not None:
                        candidates.append(sol)
                        if len(candidates) >= max_candidates:
                            return candidates
    return candidates


def osd_decode_candidates_fast(*, field: GF2mField, matrix: Any, syndrome: Sequence[int],
                               beliefs: Any = None, e_hat: Sequence[int] | None = None,
                               top_info: int | None = None,
                               max_candidates: int = 200000) -> list[list[int]]:
    """Fast full/partial OSD-1 candidate enumeration.

    Uses the precomputed RREF linear map so each single-flip candidate costs
    O(m) rather than O(m*n).  ``top_info=None`` enumerates all free variables.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    matrix = np.asarray(matrix, dtype=np.int64)
    m, n = matrix.shape
    rref, pivots = gf_rref(field, matrix.tolist(), list(syndrome))
    pivot_set = set(int(p) for p in pivots)
    free_cols = [j for j in range(n) if j not in pivot_set]
    if top_info is not None:
        if beliefs is not None:
            beliefs = np.asarray(beliefs, dtype=np.float64)
            hard_all = [int(np.argmax(beliefs[i])) for i in range(n)] if e_hat is None else [int(x) for x in e_hat]
            rel = _reliability(beliefs, hard_all)
            free_cols = sorted(free_cols, key=lambda i: rel.get(i, 0.0))[:int(top_info)]
        else:
            free_cols = free_cols[:int(top_info)]
    if e_hat is not None:
        hard = [int(x) for x in e_hat]
    elif beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        hard = [int(np.argmax(beliefs[i])) for i in range(n)]
    else:
        hard = [0] * n
    assign = {i: hard[i] for i in free_cols}
    base = solve_with_free(field, rref, pivots, assign, n)
    if base is None:
        return []
    candidates = [base]
    # coeff[p_idx][free_idx]
    pivot_to_row = {int(p): idx for idx, p in enumerate(pivots)}
    coeff = {}
    for p in pivots:
        row_idx = pivot_to_row[int(p)]
        coeff[int(p)] = {j: int(rref[row_idx][j]) for j in free_cols}
    for i in free_cols:
        old = int(hard[i])
        for cand in range(field.q):
            if cand == old:
                continue
            d = field.add(old, cand)  # old XOR cand in GF(2^m)
            new_sol = list(base)
            new_sol[i] = cand
            for p in pivots:
                factor = coeff[int(p)].get(i, 0)
                if factor != 0:
                    new_sol[p] = field.add(new_sol[p], field.mul(factor, d))
            candidates.append(new_sol)
            if len(candidates) >= max_candidates:
                return candidates
    return candidates


def osd_decode_candidates_order2_fast(*, field: GF2mField, matrix: Any, syndrome: Sequence[int],
                                      beliefs: Any = None, e_hat: Sequence[int] | None = None,
                                      top_info: int = 20, top_symbols: int = 16,
                                      max_candidates: int = 200000) -> list[list[int]]:
    """Fast bounded OSD-2 candidate enumeration using the RREF linear map.

    Each two-flip candidate costs O(m) instead of O(m*n).  This allows much
    broader OSD-2 searches than the previous implementation.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    matrix = np.asarray(matrix, dtype=np.int64)
    m, n = matrix.shape
    rref, pivots = gf_rref(field, matrix.tolist(), list(syndrome))
    pivot_set = set(int(p) for p in pivots)
    free_cols = [j for j in range(n) if j not in pivot_set]
    if e_hat is not None:
        hard = [int(x) for x in e_hat]
    elif beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        hard = [int(np.argmax(beliefs[i])) for i in range(n)]
    else:
        hard = [0] * n
    if beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        rel = _reliability(beliefs, hard)
        free_ordered = sorted(free_cols, key=lambda i: rel.get(i, 0.0))[:int(top_info)]
    else:
        free_ordered = list(free_cols)[:int(top_info)]
    assign = {i: hard[i] for i in free_cols}
    base = solve_with_free(field, rref, pivots, assign, n)
    if base is None:
        return []
    candidates = [base]
    pivot_to_row = {int(p): idx for idx, p in enumerate(pivots)}
    coeff = {}
    for p in pivots:
        row_idx = pivot_to_row[int(p)]
        coeff[int(p)] = {j: int(rref[row_idx][j]) for j in free_cols}
    cands = {}
    for i in free_ordered:
        if beliefs is not None and beliefs.shape == (n, field.q):
            top = set(np.argsort(beliefs[i])[::-1][:int(top_symbols)].tolist())
            top.add(int(hard[i]))
            cands[i] = sorted(top)
        else:
            cands[i] = list(range(field.q))
    for idx_a in range(len(free_ordered)):
        i = free_ordered[idx_a]
        old_i = int(hard[i])
        for idx_b in range(idx_a + 1, len(free_ordered)):
            j = free_ordered[idx_b]
            old_j = int(hard[j])
            for a in cands[i]:
                d_i = field.add(old_i, a)
                for b in cands[j]:
                    if a == old_i and b == old_j:
                        continue
                    d_j = field.add(old_j, b)
                    new_sol = list(base)
                    new_sol[i] = a
                    new_sol[j] = b
                    for p in pivots:
                        val = new_sol[p]
                        f_i = coeff[int(p)].get(i, 0)
                        if f_i != 0:
                            val = field.add(val, field.mul(f_i, d_i))
                        f_j = coeff[int(p)].get(j, 0)
                        if f_j != 0:
                            val = field.add(val, field.mul(f_j, d_j))
                        new_sol[p] = val
                    candidates.append(new_sol)
                    if len(candidates) >= max_candidates:
                        return candidates
    return candidates


def osd_decode_candidates_order3_fast(*, field: GF2mField, matrix: Any, syndrome: Sequence[int],
                                      beliefs: Any = None, e_hat: Sequence[int] | None = None,
                                      top_info: int = 10, top_symbols: int = 4,
                                      max_candidates: int = 200000) -> list[list[int]]:
    """Fast bounded OSD-3 candidate enumeration.

    Uses the RREF linear map; each three-flip candidate costs O(m).
    This is a diagnostic higher-order OSD search.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    matrix = np.asarray(matrix, dtype=np.int64)
    m, n = matrix.shape
    rref, pivots = gf_rref(field, matrix.tolist(), list(syndrome))
    pivot_set = set(int(p) for p in pivots)
    free_cols = [j for j in range(n) if j not in pivot_set]
    if e_hat is not None:
        hard = [int(x) for x in e_hat]
    elif beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        hard = [int(np.argmax(beliefs[i])) for i in range(n)]
    else:
        hard = [0] * n
    if beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        rel = _reliability(beliefs, hard)
        free_ordered = sorted(free_cols, key=lambda i: rel.get(i, 0.0))[:int(top_info)]
    else:
        free_ordered = list(free_cols)[:int(top_info)]
    assign = {i: hard[i] for i in free_cols}
    base = solve_with_free(field, rref, pivots, assign, n)
    if base is None:
        return []
    candidates = [base]
    pivot_to_row = {int(p): idx for idx, p in enumerate(pivots)}
    coeff = {}
    for p in pivots:
        row_idx = pivot_to_row[int(p)]
        coeff[int(p)] = {j: int(rref[row_idx][j]) for j in free_cols}
    cands = {}
    for i in free_ordered:
        if beliefs is not None and beliefs.shape == (n, field.q):
            top = set(np.argsort(beliefs[i])[::-1][:int(top_symbols)].tolist())
            top.add(int(hard[i]))
            cands[i] = sorted(top)
        else:
            cands[i] = list(range(field.q))
    for idx_a in range(len(free_ordered)):
        i = free_ordered[idx_a]
        old_i = int(hard[i])
        for idx_b in range(idx_a + 1, len(free_ordered)):
            j = free_ordered[idx_b]
            old_j = int(hard[j])
            for idx_c in range(idx_b + 1, len(free_ordered)):
                k = free_ordered[idx_c]
                old_k = int(hard[k])
                for a in cands[i]:
                    d_i = field.add(old_i, a)
                    for b in cands[j]:
                        d_j = field.add(old_j, b)
                        for c in cands[k]:
                            if a == old_i and b == old_j and c == old_k:
                                continue
                            d_k = field.add(old_k, c)
                            new_sol = list(base)
                            new_sol[i] = a; new_sol[j] = b; new_sol[k] = c
                            for p in pivots:
                                val = new_sol[p]
                                f_i = coeff[int(p)].get(i, 0)
                                if f_i != 0:
                                    val = field.add(val, field.mul(f_i, d_i))
                                f_j = coeff[int(p)].get(j, 0)
                                if f_j != 0:
                                    val = field.add(val, field.mul(f_j, d_j))
                                f_k = coeff[int(p)].get(k, 0)
                                if f_k != 0:
                                    val = field.add(val, field.mul(f_k, d_k))
                                new_sol[p] = val
                            candidates.append(new_sol)
                            if len(candidates) >= max_candidates:
                                return candidates
    return candidates


def osd_decode_candidates_order4_fast(*, field: GF2mField, matrix: Any, syndrome: Sequence[int],
                                      beliefs: Any = None, e_hat: Sequence[int] | None = None,
                                      top_info: int = 8, top_symbols: int = 2,
                                      max_candidates: int = 200000) -> list[list[int]]:
    """Fast bounded OSD-4 candidate enumeration (diagnostic)."""
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    matrix = np.asarray(matrix, dtype=np.int64)
    m, n = matrix.shape
    rref, pivots = gf_rref(field, matrix.tolist(), list(syndrome))
    pivot_set = set(int(p) for p in pivots)
    free_cols = [j for j in range(n) if j not in pivot_set]
    if e_hat is not None:
        hard = [int(x) for x in e_hat]
    elif beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        hard = [int(np.argmax(beliefs[i])) for i in range(n)]
    else:
        hard = [0] * n
    if beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        rel = _reliability(beliefs, hard)
        free_ordered = sorted(free_cols, key=lambda i: rel.get(i, 0.0))[:int(top_info)]
    else:
        free_ordered = list(free_cols)[:int(top_info)]
    assign = {i: hard[i] for i in free_cols}
    base = solve_with_free(field, rref, pivots, assign, n)
    if base is None:
        return []
    candidates = [base]
    pivot_to_row = {int(p): idx for idx, p in enumerate(pivots)}
    coeff = {}
    for p in pivots:
        row_idx = pivot_to_row[int(p)]
        coeff[int(p)] = {j: int(rref[row_idx][j]) for j in free_cols}
    cands = {}
    for i in free_ordered:
        if beliefs is not None and beliefs.shape == (n, field.q):
            top = set(np.argsort(beliefs[i])[::-1][:int(top_symbols)].tolist())
            top.add(int(hard[i]))
            cands[i] = sorted(top)
        else:
            cands[i] = list(range(field.q))
    for ia in range(len(free_ordered)):
        i = free_ordered[ia]; old_i = int(hard[i])
        for ib in range(ia+1, len(free_ordered)):
            j = free_ordered[ib]; old_j = int(hard[j])
            for ic in range(ib+1, len(free_ordered)):
                k = free_ordered[ic]; old_k = int(hard[k])
                for id_ in range(ic+1, len(free_ordered)):
                    l = free_ordered[id_]; old_l = int(hard[l])
                    for a in cands[i]:
                        d_i = field.add(old_i, a)
                        for b in cands[j]:
                            d_j = field.add(old_j, b)
                            for c in cands[k]:
                                d_k = field.add(old_k, c)
                                for e in cands[l]:
                                    if a==old_i and b==old_j and c==old_k and e==old_l:
                                        continue
                                    d_l = field.add(old_l, e)
                                    new_sol = list(base)
                                    new_sol[i]=a; new_sol[j]=b; new_sol[k]=c; new_sol[l]=e
                                    for p in pivots:
                                        val = new_sol[p]
                                        for idx, dlt in [(i,d_i),(j,d_j),(k,d_k),(l,d_l)]:
                                            f = coeff[int(p)].get(idx,0)
                                            if f != 0:
                                                val = field.add(val, field.mul(f, dlt))
                                        new_sol[p]=val
                                    candidates.append(new_sol)
                                    if len(candidates) >= max_candidates:
                                        return candidates
    return candidates


def osd_decode_candidates_fast_generic(*, field: GF2mField, matrix: Any, syndrome: Sequence[int],
                                       beliefs: Any = None, e_hat: Sequence[int] | None = None,
                                       order: int = 5, top_info: int = 8, top_symbols: int = 2,
                                       max_candidates: int = 200000) -> list[list[int]]:
    """Generic fast bounded OSD-k candidate enumeration (diagnostic).

    Supports arbitrary small ``order`` using combinations and recursion.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    if int(order) < 1:
        raise ValueError("order must be >=1")
    matrix = np.asarray(matrix, dtype=np.int64)
    m, n = matrix.shape
    rref, pivots = gf_rref(field, matrix.tolist(), list(syndrome))
    pivot_set = set(int(p) for p in pivots)
    free_cols = [j for j in range(n) if j not in pivot_set]
    if e_hat is not None:
        hard = [int(x) for x in e_hat]
    elif beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        hard = [int(np.argmax(beliefs[i])) for i in range(n)]
    else:
        hard = [0] * n
    if beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        rel = _reliability(beliefs, hard)
        free_ordered = sorted(free_cols, key=lambda i: rel.get(i, 0.0))[:int(top_info)]
    else:
        free_ordered = list(free_cols)[:int(top_info)]
    assign = {i: hard[i] for i in free_cols}
    base = solve_with_free(field, rref, pivots, assign, n)
    if base is None:
        return []
    candidates = [base]
    pivot_to_row = {int(p): idx for idx, p in enumerate(pivots)}
    coeff = {}
    for p in pivots:
        row_idx = pivot_to_row[int(p)]
        coeff[int(p)] = {j: int(rref[row_idx][j]) for j in free_cols}
    cands = {}
    for i in free_ordered:
        if beliefs is not None and beliefs.shape == (n, field.q):
            top = set(np.argsort(beliefs[i])[::-1][:int(top_symbols)].tolist())
            top.add(int(hard[i]))
            cands[i] = sorted(top)
        else:
            cands[i] = list(range(field.q))
    import itertools
    for combo in itertools.combinations(free_ordered, int(order)):
        # Recursively enumerate symbol choices for combo.
        def rec(pos, new_sol, deltas):
            nonlocal candidates
            if len(candidates) >= max_candidates:
                return
            if pos == len(combo):
                candidates.append(list(new_sol))
                return
            var = combo[pos]
            old = int(hard[var])
            for sym in cands[var]:
                new_sol2 = list(new_sol)
                d = field.add(old, sym)
                new_sol2[var] = sym
                for p in pivots:
                    f = coeff[int(p)].get(var, 0)
                    if f != 0:
                        new_sol2[p] = field.add(new_sol2[p], field.mul(f, d))
                deltas2 = deltas + [(var, d)]
                rec(pos + 1, new_sol2, deltas2)
        rec(0, base, [])
        if len(candidates) >= max_candidates:
            return candidates
    return candidates


def osd_decode_candidates_mrb(*, field: GF2mField, matrix: Any, syndrome: Sequence[int],
                              beliefs: Any = None, e_hat: Sequence[int] | None = None,
                              order: int = 1, top_info: int | None = None,
                              top_symbols: int | None = None,
                              max_candidates: int = 200000) -> list[list[int]]:
    """Reliability-sorted (most-reliable-basis) OSD candidate enumeration.

    Unlike the existing OSD helpers, this function first permutes the parity
    columns by increasing reliability.  Gaussian elimination then tends to
    select the least-reliable columns as pivots, leaving the most-reliable
    columns as the free/information set.  This is the standard OSD ordering
    and is expected to improve the chance of recovering Alice's codeword.

    Returned candidates are in the original column order.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be GF2mField")
    if int(order) < 0:
        raise ValueError("order must be >=0")
    matrix = np.asarray(matrix, dtype=np.int64)
    m, n = matrix.shape
    if e_hat is not None:
        hard = [int(x) for x in e_hat]
    elif beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        hard = [int(np.argmax(beliefs[i])) for i in range(n)]
    else:
        hard = [0] * n
    # Reliability in original coordinates.
    if beliefs is not None:
        beliefs = np.asarray(beliefs, dtype=np.float64)
        rel = _reliability(beliefs, hard)
        rel_list = [rel.get(i, 0.0) for i in range(n)]
        # Least reliable first => they become pivot columns when possible.
        perm = sorted(range(n), key=lambda i: rel_list[i])
    else:
        rel_list = [0.0] * n
        perm = list(range(n))
    M_perm = matrix[:, perm]
    hard_perm = [hard[p] for p in perm]
    rref, pivots = gf_rref(field, M_perm.tolist(), list(syndrome))
    pivot_set = set(int(p) for p in pivots)
    free_cols = [j for j in range(n) if j not in pivot_set]
    if top_info is not None:
        free_ordered = sorted(free_cols, key=lambda j: rel_list[perm[j]])[:int(top_info)]
    else:
        free_ordered = list(free_cols)
    assign = {i: hard_perm[i] for i in free_cols}
    base = solve_with_free(field, rref, pivots, assign, n)
    if base is None:
        return []

    def to_orig(x_perm: Sequence[int]) -> list[int]:
        x = [0] * n
        for j, val in enumerate(x_perm):
            x[perm[j]] = int(val)
        return x

    candidates = [base]
    candidates_orig = [to_orig(base)]
    if int(order) == 0:
        return candidates_orig
    pivot_to_row = {int(p): idx for idx, p in enumerate(pivots)}
    coeff = {}
    for p in pivots:
        row_idx = pivot_to_row[int(p)]
        coeff[int(p)] = {j: int(rref[row_idx][j]) for j in free_cols}
    cands = {}
    for i in free_ordered:
        if top_symbols is None:
            cands[i] = list(range(field.q))
        elif beliefs is not None and beliefs.shape == (n, field.q):
            orig_i = perm[i]
            top = set(np.argsort(beliefs[orig_i])[::-1][:int(top_symbols)].tolist())
            top.add(int(hard_perm[i]))
            cands[i] = sorted(top)
        else:
            cands[i] = list(range(field.q))
    import itertools
    for combo in itertools.combinations(free_ordered, int(order)):
        def rec(pos: int, cur: list[int], changed: bool) -> None:
            nonlocal candidates, candidates_orig
            if len(candidates) >= max_candidates:
                return
            if pos == len(combo):
                if changed:
                    candidates.append(list(cur))
                    candidates_orig.append(to_orig(cur))
                return
            var = combo[pos]
            old = int(hard_perm[var])
            for sym in cands[var]:
                cur2 = list(cur)
                d = field.add(old, sym)
                if d != 0:
                    for p in pivots:
                        f = coeff[int(p)].get(var, 0)
                        if f != 0:
                            cur2[p] = field.add(cur2[p], field.mul(f, d))
                cur2[var] = sym
                rec(pos + 1, cur2, changed or (sym != old))
        rec(0, base, False)
        if len(candidates) >= max_candidates:
            return candidates_orig
    return candidates_orig
