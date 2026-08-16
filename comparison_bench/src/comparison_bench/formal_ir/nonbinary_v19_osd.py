"""V19 bounded q-ary OSD helper (diagnostic).

This module provides a small GF(q) Gaussian-elimination based OSD-0/1
post-processor.  It is additive and intended for diagnostic finite-length
q=1024 experiments only.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from .nonbinary_field import GF2mField

__all__ = ["gf_rref", "solve_with_free", "osd_decode", "osd_decode_candidates", "osd_decode_candidates_order2"]


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
