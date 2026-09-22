"""D7-G independent GF(32) code-factor extrinsic oracle.

Slow-by-design ground truth for certifying the code-factor extrinsic-message
contract (``L_code_ext = L_post - log(p_in)``). Independence rule: this module
must not import or copy the production derived tables, FFT/Walsh helper,
check-update helper, extrinsic builder/helper, syndrome helper, or
row-layered update code from the production V35 decoder module (or any other
production module). Field arithmetic is built from the declared GF(2^5)
primitive polynomial by shift-and-reduce; check messages enumerate
assignments explicitly; the loopy recurrence is independently coded in the
probability domain; two-layer channel transfers use explicit einsum
marginalization.

Only ``Q`` / ``PRIMITIVE_POLY`` numeric constants mirror production, after
independently checking their declared values (``FIELD_Q == 32``,
``FIELD_POLY == 37 == 0b100101``); the certification tests assert this.
numpy (+itertools) only.
"""

from __future__ import annotations

import itertools

import numpy as np

Q = 32
PRIMITIVE_POLY = 0b100101  # 37: x^5 + x^2 + 1, GF(2^5) primitive polynomial
PROB_FLOOR = 1e-15


def gf_add(a: int, b: int) -> int:
    """Add in GF(2^5): XOR of polynomial coefficients."""
    a, b = int(a), int(b)
    if not (0 <= a < Q and 0 <= b < Q):
        raise ValueError("field values must lie in 0..31")
    return a ^ b


def gf_mul(a: int, b: int) -> int:
    """Multiply in GF(2^5) by shift-and-reduce with the primitive polynomial."""
    a, b = int(a) & 0xFF, int(b) & 0xFF
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


def _build_tables() -> tuple[np.ndarray, np.ndarray]:
    mul = np.zeros((Q, Q), dtype=np.uint8)
    add = np.zeros((Q, Q), dtype=np.uint8)
    for i in range(Q):
        for j in range(Q):
            mul[i, j] = gf_mul(i, j)
            add[i, j] = gf_add(i, j)
    return mul, add


MUL, ADD = _build_tables()


def clean_probs(p: np.ndarray) -> np.ndarray:
    """Floor at 1e-15 and renormalize one probability vector (frozen rule)."""
    v = np.maximum(np.asarray(p, dtype=np.float64), PROB_FLOOR)
    s = float(np.sum(v))
    if not np.isfinite(s) or s <= 0:
        raise ValueError("non-finite prior mass")
    return v / s


def clean_prior_rows(priors: np.ndarray) -> np.ndarray:
    """Apply the frozen floor/renorm cleaning rule row-wise."""
    mat = np.asarray(priors, dtype=np.float64)
    if mat.ndim != 2 or mat.shape[1] != Q:
        raise ValueError("priors must have shape (n, 32)")
    return np.array([clean_probs(mat[i]) for i in range(mat.shape[0])])


def softmax_rows(log_msgs: np.ndarray) -> np.ndarray:
    """Stable row-wise softmax (transport normalization)."""
    z = np.asarray(log_msgs, dtype=np.float64)
    m = np.max(z, axis=1, keepdims=True)
    e = np.exp(z - m)
    return e / np.sum(e, axis=1, keepdims=True)


def normalize_log_rows(log_msgs: np.ndarray) -> np.ndarray:
    """Row-normalize log vectors by subtracting log-sum-exp (stored form)."""
    z = np.asarray(log_msgs, dtype=np.float64)
    m = np.max(z, axis=1, keepdims=True)
    lse = m + np.log(np.sum(np.exp(z - m), axis=1, keepdims=True))
    return z - lse


def code_extrinsic_from_beliefs(
    final_log_beliefs: np.ndarray, log_input_prior: np.ndarray
) -> np.ndarray:
    """Oracle-side extrinsic: ``L_post - log(p_in)``, log-sum-exp normalized."""
    post = np.asarray(final_log_beliefs, dtype=np.float64)
    pin = np.asarray(log_input_prior, dtype=np.float64)
    if post.shape != pin.shape or post.ndim != 2:
        raise ValueError("belief/prior shape mismatch")
    if not np.all(np.isfinite(post)) or not np.all(np.isfinite(pin)):
        raise ValueError("nonfinite beliefs/prior")
    return normalize_log_rows(post - pin)


def syndrome_of(h_matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
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
                acc ^= int(MUL[coeff, int(vec[c])])
        out[r] = acc
    return out


def tree_message_to_var(
    in_probs: list[np.ndarray],
    coefficients: list[int],
    syndrome: int,
    target: int,
) -> np.ndarray:
    """Exact outgoing code-factor message to one variable (distribution).

    For a single check ``sum_j c_j x_j == syndrome``, the message to variable
    ``target`` at value ``v`` is proportional to the prior-weighted sum over
    all assignments of the other variables satisfying the constraint with
    ``x_target = v``. Normalized to a distribution (compare distributions,
    not MAP only).
    """
    deg = len(in_probs)
    if deg not in (2, 3):
        raise ValueError("enumeration supports degree 2 and 3 only")
    coeffs = [int(c) for c in coefficients]
    if any(not 0 < c < Q for c in coeffs):
        raise ValueError("check coefficients must be nonzero field elements")
    syn = int(syndrome)
    if not 0 <= syn < Q:
        raise ValueError("syndrome must lie in 0..31")
    if not 0 <= int(target) < deg:
        raise ValueError("target out of range")
    cleaned = [clean_probs(p) for p in in_probs]
    others = [j for j in range(deg) if j != int(target)]
    msg = np.zeros(Q, dtype=np.float64)
    for v in range(Q):
        # Constraint residual the other variables must satisfy.
        target_sum = int(ADD[syn, int(MUL[coeffs[int(target)], v])])
        total = 0.0
        for assign in itertools.product(range(Q), repeat=deg - 1):
            acc = 0
            prod = 1.0
            for j, xj in zip(others, assign):
                acc ^= int(MUL[coeffs[j], xj])
                prod *= cleaned[j][xj]
            if acc == target_sum:
                total += prod
        msg[v] = total
    return clean_probs(np.maximum(msg, PROB_FLOOR))


def row_layered_message_sums(
    h_matrix: np.ndarray,
    priors: np.ndarray,
    syndromes: np.ndarray,
    n_sweeps: int,
) -> list[np.ndarray]:
    """Independent cold row-layered recurrence (damping 1.0, no early stop).

    Same schedule as the certified decoder: cold-start log beliefs from
    floored priors; rows in index order; per row, extrinsic
    ``v = beliefs - u_old``, direct-SP check update via explicit enumeration,
    immediate ``beliefs += u_new - u_old``. Returns the accumulated
    check-to-variable log-message sums per variable after each completed
    sweep (``beliefs - log(p_in)``), unnormalized; compare after
    log-sum-exp normalization. No early stopping: entry ``k`` is exactly
    sweep ``k + 1``.
    """
    mat = np.asarray(h_matrix, dtype=np.int64)
    m, n = mat.shape
    syn = np.asarray(syndromes, dtype=np.int64).reshape(-1)
    if syn.shape[0] != m:
        raise ValueError("syndrome length does not match matrix rows")
    prior = np.asarray(priors, dtype=np.float64)
    if prior.shape != (n, Q):
        raise ValueError("priors must have shape (n, 32)")
    edges: list[list[int]] = []
    coeffs: list[list[int]] = []
    for r in range(m):
        cols = [c for c in range(n) if int(mat[r, c]) != 0]
        if len(cols) not in (2, 3):
            raise ValueError("reference requires check degree 2 or 3")
        edges.append(cols)
        coeffs.append([int(mat[r, c]) for c in cols])
    cleaned = clean_prior_rows(prior)
    log_prior = np.log(cleaned)
    beliefs = log_prior.copy()
    u_old: list[list[np.ndarray]] = [
        [np.zeros(Q, dtype=np.float64) for _ in edges[r]] for r in range(m)
    ]
    sums: list[np.ndarray] = []
    for _ in range(int(n_sweeps)):
        for r in range(m):
            cols = edges[r]
            in_probs = []
            for pos, c in enumerate(cols):
                v_log = beliefs[c] - u_old[r][pos]
                v_max = float(np.max(v_log))
                e = np.exp(v_log - v_max)
                in_probs.append(e / float(np.sum(e)))
            for pos, c in enumerate(cols):
                out = tree_message_to_var(in_probs, coeffs[r], int(syn[r]), pos)
                u_new = np.log(out)
                beliefs[c] = beliefs[c] - u_old[r][pos] + u_new
                u_old[r][pos] = u_new
        sums.append(beliefs - log_prior)
    return sums


def _einsum_channel(ch, w0, w1, w2, target):
    if target == "b1":
        return np.einsum("ijkl,i,j,l->k", ch, w0, w1, w2)
    if target == "b2":
        return np.einsum("ijkl,i,j,k->l", ch, w0, w1, w2)
    if target == "a1":
        return np.einsum("ijkl,j,k,l->i", ch, w0, w1, w2)
    if target == "a2":
        return np.einsum("ijkl,i,k,l->j", ch, w0, w1, w2)
    raise ValueError("target must be one of a1/a2/b1/b2")


def transfer_to_b1(channel, msg_a1, msg_a2, msg_b2):
    """CH message to b1 from incoming (a1, a2, b2) messages."""
    return _einsum_channel(
        np.asarray(channel, dtype=np.float64),
        np.asarray(msg_a1, dtype=np.float64).reshape(-1),
        np.asarray(msg_a2, dtype=np.float64).reshape(-1),
        np.asarray(msg_b2, dtype=np.float64).reshape(-1),
        "b1",
    )


def transfer_to_b2(channel, msg_a1, msg_a2, msg_b1):
    """CH message to b2 from incoming (a1, a2, b1) messages."""
    return _einsum_channel(
        np.asarray(channel, dtype=np.float64),
        np.asarray(msg_a1, dtype=np.float64).reshape(-1),
        np.asarray(msg_a2, dtype=np.float64).reshape(-1),
        np.asarray(msg_b1, dtype=np.float64).reshape(-1),
        "b2",
    )


def transfer_to_a1(channel, msg_b1, msg_b2, msg_a2):
    """CH message to a1 from incoming (b1, b2, a2) messages."""
    return _einsum_channel(
        np.asarray(channel, dtype=np.float64),
        np.asarray(msg_b1, dtype=np.float64).reshape(-1),
        np.asarray(msg_b2, dtype=np.float64).reshape(-1),
        np.asarray(msg_a2, dtype=np.float64).reshape(-1),
        "a1",
    )


def transfer_to_a2(channel, msg_b1, msg_b2, msg_a1):
    """CH message to a2 from incoming (b1, b2, a1) messages."""
    return _einsum_channel(
        np.asarray(channel, dtype=np.float64),
        np.asarray(msg_b1, dtype=np.float64).reshape(-1),
        np.asarray(msg_b2, dtype=np.float64).reshape(-1),
        np.asarray(msg_a1, dtype=np.float64).reshape(-1),
        "a2",
    )


def normalize_dist(v: np.ndarray) -> np.ndarray:
    """Normalize a nonnegative vector to a distribution (fail on bad mass)."""
    w = np.asarray(v, dtype=np.float64).reshape(-1)
    s = float(np.sum(w))
    if not np.isfinite(s) or s <= 0:
        raise ValueError("non-finite transfer mass")
    return w / s
