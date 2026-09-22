"""D7-A independent GF(32) decoder reference oracle.

Slow-by-design ground truth for certifying the historical row-layered
FFT-QSPA decoder. Independence rule: this module must not import or copy the
production derived tables, FFT/Walsh helper, check-update helper,
syndrome-offset helper, or row-layered update code. Field arithmetic is built
from the declared GF(2^5) primitive polynomial by bitwise reduction; the
check update is explicit assignment enumeration; tiny posteriors enumerate
all assignments satisfying ``H x = s``.

Only ``Q`` / ``PRIMITIVE_POLY`` numeric constants are shared with production,
after independently checking their declared values
(``nonbinary_field._POLYNOMIALS[5] == 0b100101``, ``FIELD_Q == 32``).
"""

from __future__ import annotations

import itertools

import numpy as np

Q = 32
PRIMITIVE_POLY = 0b100101  # 37: x^5 + x^2 + 1, GF(2^5) primitive polynomial
PROB_FLOOR = 1e-15


def gf32_mul_independent(a: int, b: int) -> int:
    """Multiply in GF(2^5) by shift-and-reduce with the primitive polynomial."""
    a = int(a) & 0xFF
    b = int(b) & 0xFF
    if a >= Q or b >= Q:
        raise ValueError("field values must lie in 0..31")
    result = 0
    multiplicand = a
    multiplier = b
    while multiplier:
        if multiplier & 1:
            result ^= multiplicand
        multiplier >>= 1
        multiplicand <<= 1
        if multiplicand & 0x20:  # x^5 term overflow -> reduce
            multiplicand ^= PRIMITIVE_POLY
    return result & 0x1F


def gf32_add_independent(a: int, b: int) -> int:
    """Add in GF(2^5): XOR of polynomial coefficients."""
    a, b = int(a), int(b)
    if not (0 <= a < Q and 0 <= b < Q):
        raise ValueError("field values must lie in 0..31")
    return a ^ b


def gf32_inv_independent(a: int) -> int:
    """Inverse in GF(2^5) by brute-force search (independent of any table)."""
    a = int(a)
    if not 0 < a < Q:
        raise ValueError("only nonzero elements have inverses")
    for cand in range(1, Q):
        if gf32_mul_independent(a, cand) == 1:
            return cand
    raise AssertionError("no inverse found; polynomial may not be primitive")


def _build_reference_tables() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mul = np.zeros((Q, Q), dtype=np.uint8)
    add = np.zeros((Q, Q), dtype=np.uint8)
    inv = np.zeros(Q, dtype=np.uint8)
    for i in range(Q):
        for j in range(Q):
            mul[i, j] = gf32_mul_independent(i, j)
            add[i, j] = gf32_add_independent(i, j)
        if i > 0:
            inv[i] = gf32_inv_independent(i)
    return mul, add, inv


MUL_REF, ADD_REF, INV_REF = _build_reference_tables()


def syndrome_reference(h_matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    """Compute H * x over GF(32) with the independent tables (plain loops)."""
    mat = np.asarray(h_matrix, dtype=np.int64)
    vec = np.asarray(vector, dtype=np.int64).reshape(-1)
    m, n = mat.shape
    if vec.shape[0] != n:
        raise ValueError("vector length does not match matrix cols")
    out = np.zeros(m, dtype=np.uint8)
    for r in range(m):
        acc = 0
        for c in range(n):
            coeff = int(mat[r, c])
            if coeff:
                acc ^= int(MUL_REF[coeff, int(vec[c])])
        out[r] = acc
    return out


def _clean_probs(p: np.ndarray) -> np.ndarray:
    p = np.maximum(np.asarray(p, dtype=np.float64), PROB_FLOOR)
    s = p.sum()
    if not np.isfinite(s) or s <= 0:
        raise ValueError("non-finite prior mass")
    return p / s


def direct_check_to_var(
    in_probs: list[np.ndarray],
    coefficients: list[int],
    syndrome: int,
) -> list[np.ndarray]:
    """Direct sum-product check update by explicit enumeration (deg 2/3 only).

    Outgoing message to edge ``t`` at value ``v`` is proportional to the sum
    of the product of incoming messages over all assignments of the other
    edges with ``sum_j c_j x_j + c_t v == syndrome``.
    """
    deg = len(in_probs)
    if deg not in (2, 3):
        raise ValueError("direct enumeration supports degree 2 and 3 only")
    coeffs = [int(c) for c in coefficients]
    if any(not 0 < c < Q for c in coeffs):
        raise ValueError("check coefficients must be nonzero field elements")
    syn = int(syndrome)
    if not 0 <= syn < Q:
        raise ValueError("syndrome must lie in 0..31")
    cleaned = [_clean_probs(p) for p in in_probs]
    outgoing: list[np.ndarray] = []
    for t in range(deg):
        others = [j for j in range(deg) if j != t]
        msg = np.zeros(Q, dtype=np.float64)
        for v in range(Q):
            target = int(ADD_REF[syn, int(MUL_REF[coeffs[t], v])])
            total = 0.0
            for assign in itertools.product(range(Q), repeat=deg - 1):
                acc = 0
                prod = 1.0
                for j, xj in zip(others, assign):
                    acc ^= int(MUL_REF[coeffs[j], xj])
                    prod *= cleaned[j][xj]
                if acc == target:
                    total += prod
            msg[v] = total
        outgoing.append(_clean_probs(np.maximum(msg, PROB_FLOOR)))
    return outgoing


def exact_posterior(
    h_matrix: np.ndarray,
    priors: np.ndarray,
    syndromes: np.ndarray,
) -> np.ndarray:
    """Exact per-variable posterior by enumerating all assignments with Hx=s.

    Only for tiny graphs (total assignments capped at 32^3).
    """
    mat = np.asarray(h_matrix, dtype=np.int64)
    m, n = mat.shape
    syn = np.asarray(syndromes, dtype=np.int64).reshape(-1)
    if syn.shape[0] != m:
        raise ValueError("syndrome length does not match matrix rows")
    if Q**n > Q**3:
        raise ValueError("exact enumeration capped at 3 variables")
    prior = np.asarray(priors, dtype=np.float64)
    if prior.shape != (n, Q):
        raise ValueError("priors must have shape (n, 32)")
    cleaned = np.array([_clean_probs(prior[i]) for i in range(n)])
    post = np.zeros((n, Q), dtype=np.float64)
    for assign in itertools.product(range(Q), repeat=n):
        ok = True
        for r in range(m):
            acc = 0
            for c in range(n):
                coeff = int(mat[r, c])
                if coeff:
                    acc ^= int(MUL_REF[coeff, assign[c]])
            if acc != int(syn[r]):
                ok = False
                break
        if not ok:
            continue
        w = 1.0
        for i, xi in enumerate(assign):
            w *= cleaned[i][xi]
        for i, xi in enumerate(assign):
            post[i, xi] += w
    totals = post.sum(axis=1)
    if np.any(totals <= 0):
        raise ValueError("no assignment satisfies Hx=s under these fixtures")
    return post / totals[:, None]


def row_layered_reference(
    h_matrix: np.ndarray,
    priors: np.ndarray,
    syndromes: np.ndarray,
    max_iter: int,
) -> tuple[list[np.ndarray], int, np.ndarray]:
    """Independent row-layered sum-product recurrence (damping 1.0, cold start).

    Same schedule as the historical decoder: cold-start log beliefs from
    floored priors; rows processed in index order; per row, extrinsic
    ``v = beliefs - u_old``, direct-SP check update, immediate
    ``beliefs += u_new - u_old``; hard decision + syndrome check after each
    full sweep. Returns (per-sweep log-beliefs, iterations, x_hat), mirroring
    the production stopping convention (0 = initial MAP already satisfied).
    """
    mat = np.asarray(h_matrix, dtype=np.int64)
    m, n = mat.shape
    syn = np.asarray(syndromes, dtype=np.int64).reshape(-1)
    prior = np.asarray(priors, dtype=np.float64)
    if prior.shape != (n, Q):
        raise ValueError("priors must have shape (n, 32)")
    edges: list[list[int]] = []
    coeffs: list[list[int]] = []
    for r in range(m):
        cols = [c for c in range(n) if int(mat[r, c]) != 0]
        if len(cols) < 2:
            raise ValueError("reference requires check degree >= 2")
        edges.append(cols)
        coeffs.append([int(mat[r, c]) for c in cols])
    beliefs = np.log(np.array([_clean_probs(prior[i]) for i in range(n)]))
    u_old: list[list[np.ndarray]] = [
        [np.zeros(Q, dtype=np.float64) for _ in edges[r]] for r in range(m)
    ]
    x_hat = np.argmax(beliefs, axis=1).astype(np.int64)
    if np.array_equal(syndrome_reference(mat, x_hat), syn.astype(np.uint8)):
        return [], 0, x_hat
    sweeps: list[np.ndarray] = []
    for _ in range(1, int(max_iter) + 1):
        for r in range(m):
            cols = edges[r]
            in_probs = []
            for pos, c in enumerate(cols):
                v_log = beliefs[c] - u_old[r][pos]
                v_max = np.max(v_log)
                e = np.exp(v_log - v_max)
                in_probs.append(e / e.sum())
            out_probs = direct_check_to_var(in_probs, coeffs[r], int(syn[r]))
            for pos, c in enumerate(cols):
                u_new = np.log(out_probs[pos])
                beliefs[c] = beliefs[c] - u_old[r][pos] + u_new
                u_old[r][pos] = u_new
        sweeps.append(beliefs.copy())
        x_hat = np.argmax(beliefs, axis=1).astype(np.int64)
        if np.array_equal(syndrome_reference(mat, x_hat), syn.astype(np.uint8)):
            return sweeps, len(sweeps), x_hat
    return sweeps, int(max_iter), x_hat
