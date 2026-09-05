"""V72P2D5 GF32 rate-mother packet — R2 dv3 implementation (T0/T1 only).

Cycle ``V72P2D5-GF32-RATE-MOTHER`` plan revision ``R2_DV3``. This module
implements the frozen D5 plan math and plumbing with small matrices plus
injected fake builders/decoders only. It performs no full-size
construction, calls no real decoder, reads no data files, and writes no
output files: every phase function returns an in-memory result dict and
refuses before any work unless explicitly authorized.

Frozen plan reference (read-only, see ``openspec/changes/
formal-ir-v72p2d5-gf32-rate-mother-plan/``):
``A = 32*U1 + U2``, ``counts.shape == (Alice, Bob)``, normalization sums
along ``axis0`` (Alice), ``lambda* = 137.3823795883264``, audit floor
``1e-300`` / decoder floor ``1e-15`` (both renormalized afterwards),
probability-domain transfer, ``log2`` only for CE checks.

Mother path is the single ``G2_MINIMAL_NESTED_DV3_GF32`` column-degree-3
nested construction (2 base edges + 1 expansion edge per variable, GF32
coefficients ``1..31``). Disclosure ``H[:k]`` uses construction order
directly.
"""

from __future__ import annotations

import math
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------
# Frozen constants (D5 plan, must not change without an OpenSpec revision)
# --------------------------------------------------------------------------
Q = 32
GF_POLY = 37
N = 1024
M_MAX = 1000
COLUMN_DEGREE = 3
L1_K_MIN = 782
L2_K_MIN = 686
LAMBDA_STAR = 137.3823795883264
AUDIT_FLOOR = 1e-300
DECODER_FLOOR = 1e-15
CE_L1_MEAN = 3.814742
CE_L2_ORACLE_MEAN = 3.347605
CE_JOINT_MEAN = 7.162347
L1_GRAPH_SEED = 2026090501
L2_GRAPH_SEED = 2026090502
L1_PREFIXES = (782, 821, 860, 938)
L2_PREFIXES = (686, 720, 755, 823)
G0_SEEDS = tuple(range(2026090510, 2026090518))
G1_SEEDS = tuple(range(2026090600, 2026090700))
G2_SEEDS = tuple(range(2026091000, 2026091200))
G1_F = (1.0, 1.2)
G2_F = (1.0, 1.1, 1.2)
P0_F = (1.0, 1.2)
G1_BLOCKS = 100
G2_BLOCKS = 200
G1_ORACLE_SUBSET = 20
G2_ORACLE_SUBSET = 40
G1_WIDTH = 64
G2_WIDTH = 256
P0_WIDTH = 64
TINY_WIDTH = 8
MAX_ITER = 90
DAMPING_ALPHA = 1.0
PHASES = ("structure", "g0", "p0-cost", "g1", "g2")
_PHASE_AUTH_KEYS = {
    "structure": "structure_execution_authorized",
    "g0": "g0_execution_authorized",
    "p0-cost": "p0_cost_execution_authorized",
    "g1": "g1_execution_authorized",
    "g2": "g2_execution_authorized",
}
GRADE_QUALIFIED = "G2_SYNTHETIC_QUALIFIED"
GRADE_INCONCLUSIVE = "G2_INCONCLUSIVE"
GRADE_FAILED = "G2_CURRENT_CONFIGURATION_FAILED"
GRADE_BLOCKED = "IMPLEMENTATION_OR_NUMERICAL_BLOCKED"


class NotAuthorizedError(PermissionError):
    """Raised when a phase is entered without its frozen authorization."""


def is_phase_authorized(cycle_state, phase):
    """Return True only when ``cycle_state`` authorizes ``phase``.

    Single authorization choke point: unknown phases deny by default.
    ``cycle_state`` is a plain mapping of the frozen ``cycle_state.yaml``
    keys to booleans.
    """
    key = _PHASE_AUTH_KEYS.get(phase)
    if key is None:
        return False
    return bool(cycle_state.get(key, False))


# --------------------------------------------------------------------------
# GF(32) arithmetic, pinned to poly 37 (0b100101)
# --------------------------------------------------------------------------
def _gf32_mul_raw(a, b):
    r = 0
    aa, bb = int(a), int(b)
    while bb:
        if bb & 1:
            r ^= aa
        bb >>= 1
        aa <<= 1
        if aa & 0x20:
            aa ^= 0x25
    return r & 0x1F


_GF_ALOG = np.zeros(63, dtype=np.int64)
_GF_LOG = np.zeros(32, dtype=np.int64)
_v = 1
for _i in range(63):
    _GF_ALOG[_i] = _v
    _v = _gf32_mul_raw(_v, 2)
for _i in range(31):
    _GF_LOG[int(_GF_ALOG[_i])] = _i
del _v, _i


def _gf32_mul_vec_vec(a, b):
    a = np.asarray(a, dtype=np.int64)
    b = np.asarray(b, dtype=np.int64)
    out = np.zeros(np.broadcast_shapes(a.shape, b.shape), dtype=np.int64)
    aa, bb = np.broadcast_arrays(a, b)
    nz = (aa != 0) & (bb != 0)
    out[nz] = _GF_ALOG[(_GF_LOG[aa[nz]] + _GF_LOG[bb[nz]]) % 31]
    return out


def _gf32_mul_scalar_vec(row, s):
    s = int(s)
    row = np.asarray(row, dtype=np.int64)
    if s == 0:
        return np.zeros_like(row)
    if s == 1:
        return row.copy()
    out = np.zeros_like(row)
    nz = row != 0
    out[nz] = _GF_ALOG[(_GF_LOG[row[nz]] + _GF_LOG[s]) % 31]
    return out


def _gf32_inv(s):
    s = int(s)
    if s == 0:
        raise ValueError("GF(32) inverse of zero is undefined")
    return int(_GF_ALOG[(31 - _GF_LOG[s]) % 31])


def _gf32_rank(mat):
    """Row rank over GF(32) by forward elimination (vectorized)."""
    a = np.asarray(mat, dtype=np.int64).copy()
    if a.ndim != 2:
        raise ValueError("rank input must be 2-D")
    m, n = a.shape
    r = 0
    for c in range(n):
        col = a[r:, c]
        hit = np.flatnonzero(col)
        if hit.shape[0] == 0:
            continue
        piv = r + int(hit[0])
        if piv != r:
            a[[r, piv]] = a[[piv, r]]
        inv = _gf32_inv(a[r, c])
        if inv != 1:
            a[r] = _gf32_mul_scalar_vec(a[r], inv)
        sub = a[r + 1:]
        if sub.shape[0]:
            f = sub[:, c]
            live = f != 0
            prow_live = a[r] != 0
            if np.any(live) and np.any(prow_live):
                lp = np.zeros(n, dtype=np.int64)
                lp[prow_live] = _GF_LOG[a[r, prow_live]]
                add = _GF_ALOG[(lp[None, :] + _GF_LOG[f][:, None]) % 31]
                add[~live[:, None] | ~prow_live[None, :]] = 0
                sub ^= add
        r += 1
        if r == m:
            break
    return int(r)


def _gf32_syndrome(h, x):
    """Syndrome vector of symbol word ``x`` under matrix ``h`` over GF(32)."""
    h = np.asarray(h, dtype=np.int64)
    x = np.asarray(x, dtype=np.int64)
    m, n = h.shape
    if x.shape != (n,):
        raise ValueError("word length must match matrix width")
    out = np.zeros(m, dtype=np.int64)
    for i in range(m):
        row = h[i]
        nz = row != 0
        if np.any(nz):
            prod = _gf32_mul_vec_vec(row[nz], x[nz])
            s = 0
            for v in prod:
                s ^= int(v)
            out[i] = s
    return out


# --------------------------------------------------------------------------
# F1. Prior math layer (pure functions, probability domain)
# --------------------------------------------------------------------------
def build_f_model(counts_ab, lam=LAMBDA_STAR):
    """Smooth ``counts`` (Alice rows, Bob columns) and normalize to P_F(A|B).

    Single-coefficient smoothing ``lam`` is added cell-wise along the count
    columns, then each column is normalized along ``axis0`` (Alice) so every
    Bob column sums to 1. An all-zero column with ``lam <= 0`` falls back to
    uniform ``1/A`` to preserve normalization.
    """
    counts = np.asarray(counts_ab, dtype=np.float64)
    if counts.ndim != 2 or counts.shape[0] < 1 or counts.shape[1] < 1:
        raise ValueError("counts_ab must be a non-empty 2-D (Alice, Bob) table")
    if not np.all(np.isfinite(counts)):
        raise ValueError("counts_ab must be finite")
    if np.any(counts < 0):
        raise ValueError("counts_ab must be nonnegative")
    lam = float(lam)
    if not np.isfinite(lam) or lam < 0:
        raise ValueError("lam must be a finite nonnegative coefficient")
    n_a = counts.shape[0]
    sm = counts + lam
    col = sm.sum(axis=0)
    p = np.empty_like(sm)
    good = col > 0
    p[:, good] = sm[:, good] / col[good]
    p[:, ~good] = 1.0 / n_a
    return p


def marginalize_f_to_p1(p_f):
    """Derive ``P1(U1|B)`` by summing the reshaped P_F over the U2 axis."""
    pf = np.asarray(p_f, dtype=np.float64)
    if pf.ndim != 2 or pf.shape[0] % Q != 0:
        raise ValueError("p_f Alice dim must be a nonzero multiple of 32")
    n_b = pf.shape[1]
    r = pf.reshape(pf.shape[0] // Q, Q, n_b).sum(axis=1)
    s = r.sum(axis=0)
    out = np.empty_like(r)
    good = s > 0
    out[:, good] = r[:, good] / s[good]
    out[:, ~good] = 1.0 / Q
    return out


def conditionalize_f_to_p2(p_f):
    """Derive ``P2`` with shape ``(U1, Bob, U2)``, normalized over U2.

    Slices with zero mass fall back to uniform ``1/32``; no sample is
    dropped.
    """
    pf = np.asarray(p_f, dtype=np.float64)
    if pf.ndim != 2 or pf.shape[0] % Q != 0:
        raise ValueError("p_f Alice dim must be a nonzero multiple of 32")
    n_b = pf.shape[1]
    n_u2 = Q
    r = pf.reshape(pf.shape[0] // Q, n_u2, n_b)
    mass = r.sum(axis=1, keepdims=True)
    p2 = np.empty_like(r)
    good = (mass[:, 0, :] > 0)
    for u in range(r.shape[0]):
        g = good[u]
        p2[u][:, g] = r[u][:, g] / mass[u, 0, g]
        p2[u][:, ~g] = 1.0 / n_u2
    return np.moveaxis(p2, 1, 2).copy()


def _floor_renorm(prior, floor):
    p = np.maximum(np.asarray(prior, dtype=np.float64), float(floor))
    s = p.sum(axis=-1, keepdims=True)
    if np.any(s <= 0) or not np.all(np.isfinite(s)):
        raise ValueError("prior floor produced a non-positive row sum")
    return p / s


def app_fed_l2_prior(p2, bob_symbols, q_l1):
    """Production L2 prior ``q @ P`` from L1 APP beliefs (probability domain).

    ``p2`` has shape ``(U1, Bob, U2)``, ``bob_symbols`` has shape ``(N,)``,
    ``q_l1`` has shape ``(N, U1)``. The decoder floor is applied and rows
    are renormalized afterwards.
    """
    p2a = np.asarray(p2, dtype=np.float64)
    bob = np.asarray(bob_symbols, dtype=np.int64).ravel()
    q = np.asarray(q_l1, dtype=np.float64)
    if p2a.ndim != 3:
        raise ValueError("p2 must have shape (U1, Bob, U2)")
    n_u, n_b, n_v = p2a.shape
    n = bob.shape[0]
    if q.shape != (n, n_u):
        raise ValueError("q_l1 must have shape (N, U1) matching p2 and bob")
    if not np.all(np.isfinite(q)) or np.any(q < 0):
        raise ValueError("q_l1 must be finite and nonnegative")
    if np.any(bob < 0) or np.any(bob >= n_b):
        raise ValueError("bob_symbols out of range for p2 Bob dim")
    seg = p2a[:, bob, :]
    prior = np.einsum("nq,qnv->nv", q, seg)
    return _floor_renorm(prior, DECODER_FLOOR)


def oracle_l2_prior(p2, bob_symbols, u1_true):
    """Diagnostic-only oracle L2 prior using the true U1 symbols.

    Diagnostic-only: production decoding must use :func:`app_fed_l2_prior`.
    This helper exists solely to quantify the oracle upper-bound gap.
    """
    p2a = np.asarray(p2, dtype=np.float64)
    bob = np.asarray(bob_symbols, dtype=np.int64).ravel()
    u1 = np.asarray(u1_true, dtype=np.int64).ravel()
    if p2a.ndim != 3:
        raise ValueError("p2 must have shape (U1, Bob, U2)")
    n_u, n_b, _ = p2a.shape
    if bob.shape != u1.shape:
        raise ValueError("bob_symbols and u1_true must share shape")
    if np.any(bob < 0) or np.any(bob >= n_b):
        raise ValueError("bob_symbols out of range for p2 Bob dim")
    if np.any(u1 < 0) or np.any(u1 >= n_u):
        raise ValueError("u1_true out of range for p2 U1 dim")
    prior = p2a[u1, bob, :]
    return _floor_renorm(prior, DECODER_FLOOR)


def symbols_to_layers(symbols):
    """Split full symbols ``A`` into ``(U1, U2)`` with ``A = 32*U1 + U2``."""
    s = np.asarray(symbols, dtype=np.int64)
    if np.any(s < 0):
        raise ValueError("symbols must be nonnegative")
    return s // Q, s % Q


def layers_to_symbols(u1, u2):
    """Join ``(U1, U2)`` layers into full symbols ``A = 32*U1 + U2``."""
    a = np.asarray(u1, dtype=np.int64)
    b = np.asarray(u2, dtype=np.int64)
    if a.shape != b.shape:
        raise ValueError("u1 and u2 must share shape")
    if np.any(a < 0) or np.any(a >= Q) or np.any(b < 0) or np.any(b >= Q):
        raise ValueError("u1/u2 values must lie in 0..31")
    return a * Q + b


# --------------------------------------------------------------------------
# F2. dv3 nested support + GF32 coefficients (single minimal construction)
# --------------------------------------------------------------------------
def build_dv3_nested_support(n, m_max, k_min, seed):
    """Build dv3 nested support with 2 base edges + 1 expansion per variable.

    Returns int array ``support`` of shape ``(n, 3)`` with
    ``support[v] = [base1, base2, expansion]``. Base rows lie in
    ``[0, k_min)`` on distinct checks with globally unique unordered base
    pairs; the expansion differs from both base rows; unordered support
    triples are globally unique; every base row and every suffix row
    ``[k_min, m_max)`` ends with degree at least 2. One deterministic
    attempt only; any failure raises with a ``DV3_SUPPORT_*_BLOCKED`` tag.
    """
    n = int(n)
    m_max = int(m_max)
    k_min = int(k_min)
    seed = int(seed)
    if n < 1 or m_max < 1 or k_min < 1 or k_min > m_max:
        raise ValueError("DV3_SUPPORT_CAPACITY_BLOCKED: bad dims")
    if k_min * (k_min - 1) // 2 < n:
        raise ValueError(
            "DV3_SUPPORT_CAPACITY_BLOCKED: base-pair capacity "
            f"C({k_min},2) < n={n}"
        )
    sfx_total = m_max - k_min
    if n < 2 * sfx_total:
        raise ValueError(
            "DV3_SUPPORT_CAPACITY_BLOCKED: suffix stubs "
            f"n={n} < 2*(m_max-k_min)={2 * sfx_total}"
        )
    if 3 * n < 2 * m_max:
        raise ValueError(
            "DV3_SUPPORT_CAPACITY_BLOCKED: edge budget "
            f"3*n={3 * n} < 2*m_max={2 * m_max}"
        )
    if 2 * n < n + k_min - 1:
        raise ValueError(
            "DV3_SUPPORT_CAPACITY_BLOCKED: earliest-prefix connectivity "
            f"2*n={2 * n} < n+k_min-1={n + k_min - 1}"
        )
    rng = np.random.default_rng(seed)
    var_seq = rng.permutation(n)
    base_perm = rng.permutation(k_min)
    if sfx_total > 0:
        sfx_perm = rng.permutation(sfx_total)
    else:
        sfx_perm = np.zeros(0, dtype=np.int64)
    base_pos = np.empty(k_min, dtype=np.int64)
    for pos, row in enumerate(base_perm):
        base_pos[int(row)] = int(pos)
    if sfx_total > 0:
        sfx_pos = np.empty(sfx_total, dtype=np.int64)
        for pos, idx in enumerate(sfx_perm):
            sfx_pos[int(idx)] = int(pos)
    else:
        sfx_pos = np.zeros(0, dtype=np.int64)
    prio_full = np.empty(m_max, dtype=np.int64)
    prio_full[:k_min] = base_pos
    if sfx_total > 0:
        prio_full[k_min:] = sfx_pos
    support = np.full((n, 3), -1, dtype=np.int64)
    deg = np.zeros(m_max, dtype=np.int64)
    used_pairs: set = set()
    used_triples: set = set()
    idx_all_base = np.arange(k_min, dtype=np.int64)
    idx_all = np.arange(m_max, dtype=np.int64)
    for v_np in var_seq:
        v = int(v_np)
        order = np.lexsort((idx_all_base, base_pos, deg[:k_min]))
        done = False
        for b1_np in order:
            b1 = int(b1_np)
            for b2_np in order:
                b2 = int(b2_np)
                if b2 == b1:
                    continue
                a, b = (b1, b2) if b1 < b2 else (b2, b1)
                if (a, b) in used_pairs:
                    continue
                support[v, 0] = b1
                support[v, 1] = b2
                deg[b1] += 1
                deg[b2] += 1
                used_pairs.add((a, b))
                done = True
                break
            if done:
                break
        if not done:
            raise ValueError(
                "DV3_SUPPORT_CONSTRUCTION_BLOCKED: no legal base pair"
            )
    sfx_visit = [int(k_min + int(x)) for x in sfx_perm]
    pending = [int(x) for x in var_seq]
    for srow in sfx_visit:
        for _ in range(2):
            pick_at = -1
            for ti, v in enumerate(pending):
                b1 = int(support[v, 0])
                b2 = int(support[v, 1])
                t = (b1, b2, int(srow))
                t = (min(t), sorted(t)[1], max(t))
                if t not in used_triples:
                    pick_at = ti
                    break
            if pick_at < 0:
                raise ValueError(
                    "DV3_SUPPORT_CONSTRUCTION_BLOCKED: suffix cover failed"
                )
            v = pending.pop(pick_at)
            support[v, 2] = int(srow)
            deg[int(srow)] += 1
            b1 = int(support[v, 0])
            b2 = int(support[v, 1])
            t = tuple(sorted((b1, b2, int(srow))))
            used_triples.add(t)
    for v in list(pending):
        b1 = int(support[v, 0])
        b2 = int(support[v, 1])
        order = np.lexsort((idx_all, prio_full, deg))
        placed = False
        for r_np in order:
            r = int(r_np)
            if r == b1 or r == b2:
                continue
            t = tuple(sorted((b1, b2, r)))
            if t in used_triples:
                continue
            support[v, 2] = r
            deg[r] += 1
            used_triples.add(t)
            pending.remove(v)
            placed = True
            break
        if not placed:
            raise ValueError(
                "DV3_SUPPORT_CONSTRUCTION_BLOCKED: expansion placement failed"
            )
    for _ in range(2 * m_max + 4):
        weak = np.flatnonzero(deg < 2)
        if weak.shape[0] == 0:
            break
        r = int(weak[0])
        moved = False
        for v_np in var_seq:
            v = int(v_np)
            b1 = int(support[v, 0])
            b2 = int(support[v, 1])
            e = int(support[v, 2])
            if deg[e] <= 2:
                continue
            if r == b1 or r == b2 or r == e:
                continue
            t_old = tuple(sorted((b1, b2, e)))
            t_new = tuple(sorted((b1, b2, r)))
            if t_new in used_triples:
                continue
            support[v, 2] = r
            deg[e] -= 1
            deg[r] += 1
            used_triples.discard(t_old)
            used_triples.add(t_new)
            moved = True
            break
        if not moved:
            raise ValueError(
                "DV3_SUPPORT_CONSTRUCTION_BLOCKED: low-degree swap failed"
            )
    else:
        raise ValueError(
            "DV3_SUPPORT_CONSTRUCTION_BLOCKED: low-degree swap failed"
        )
    if support.shape != (n, 3):
        raise ValueError("DV3_SUPPORT_CONSTRUCTION_BLOCKED: bad shape")
    if bool(np.any(support < 0)) or bool(np.any(support >= m_max)):
        raise ValueError("DV3_SUPPORT_CONSTRUCTION_BLOCKED: out of range")
    for v in range(n):
        row = support[v]
        if len({int(row[0]), int(row[1]), int(row[2])}) != 3:
            raise ValueError(
                "DV3_SUPPORT_CONSTRUCTION_BLOCKED: per-variable distinct"
            )
        if int(row[0]) >= k_min or int(row[1]) >= k_min:
            raise ValueError(
                "DV3_SUPPORT_CONSTRUCTION_BLOCKED: base range"
            )
        if int(row[2]) == int(row[0]) or int(row[2]) == int(row[1]):
            raise ValueError(
                "DV3_SUPPORT_CONSTRUCTION_BLOCKED: expansion distinct"
            )
    pairs = set()
    triples = set()
    for v in range(n):
        b1 = int(support[v, 0])
        b2 = int(support[v, 1])
        a, b = (b1, b2) if b1 < b2 else (b2, b1)
        if (a, b) in pairs:
            raise ValueError(
                "DV3_SUPPORT_CONSTRUCTION_BLOCKED: base-pair duplicate"
            )
        pairs.add((a, b))
        t = tuple(sorted((b1, b2, int(support[v, 2]))))
        if t in triples:
            raise ValueError(
                "DV3_SUPPORT_CONSTRUCTION_BLOCKED: triple duplicate"
            )
        triples.add(t)
    if int(deg.sum()) != 3 * n:
        raise ValueError("DV3_SUPPORT_CONSTRUCTION_BLOCKED: edge count")
    if int(np.count_nonzero(deg)) != m_max:
        raise ValueError("DV3_SUPPORT_CONSTRUCTION_BLOCKED: zero row")
    if bool(np.any(deg < 2)):
        raise ValueError("DV3_SUPPORT_CONSTRUCTION_BLOCKED: low degree")
    return support


def assign_gf32_coefficients(support, seed, field=None, m_max=None):
    """Put GF32 values ``1..31`` on support entries, else ``0``.

    Dense ``(m_max, n)`` ``uint8`` output for compat. One deterministic
    generator supplies each nonzero exactly once. Same seed gives
    elementwise identical output.
    """
    _ = field
    s = np.asarray(support, dtype=np.int64)
    if s.ndim != 2 or s.shape[1] != 3:
        raise ValueError("support must have shape (n, 3)")
    cnt = int(s.shape[0])
    if m_max is None:
        m_max = int(s.max()) + 1 if cnt else 0
    m_max = int(m_max)
    if cnt < 1 or m_max < 1:
        raise ValueError("need nonempty support and positive m_max")
    if bool(np.any(s < 0)) or bool(np.any(s >= m_max)):
        raise ValueError("support entries must lie in 0..m_max-1")
    gen = np.random.default_rng(int(seed))
    vals = gen.integers(1, 32, size=(cnt, 3))
    out = np.zeros((m_max, cnt), dtype=np.uint8)
    for v in range(cnt):
        for j in range(3):
            row = int(s[v, j])
            if out[row, v] != 0:
                raise ValueError("support has a duplicated position")
            out[row, v] = np.uint8(int(vals[v, j]))
    if bool(np.any(out < 0)) or bool(np.any(out >= Q)):
        raise ValueError("values must lie in 0..31")
    return out


def build_dv3_nested_mother(n, m_max, k_min, seed, field=None):
    """Thin wrapper: support first, then coefficients, nothing else."""
    s = build_dv3_nested_support(int(n), int(m_max), int(k_min), int(seed))
    return assign_gf32_coefficients(s, int(seed), field, int(m_max))


# --------------------------------------------------------------------------
# F3. Structure audit (pure functions)
# --------------------------------------------------------------------------
class _DSU:
    def __init__(self, size):
        self.p = list(range(size))

    def find(self, x):
        p = self.p
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def _prefix_graph(h, k):
    p = np.asarray(h, dtype=np.int64)[:k]
    m, n = p.shape
    supp_rows = [np.flatnonzero(p[i]).tolist() for i in range(m)]
    supp_cols = [np.flatnonzero(p[:, j]).tolist() for j in range(n)]
    return p, supp_rows, supp_cols


def audit_prefix(h, k, field=None):
    """Audit the row prefix ``H[:k]`` and report the frozen items.

    ``field`` is accepted for call-site compatibility; the arithmetic is
    pinned to GF(32)/poly-37 per the frozen constants. Connectivity uses an
    inline union-find; 4-cycles are counted as variable-shared check pairs
    ``sum_C(shared, 2)``; projective duplicates are column pairs with an
    identical zero pattern whose support entries are proportional over
    GF(32) (all-zero column pairs count as duplicates).
    """
    _ = field
    h = np.asarray(h)
    if h.ndim != 2 or int(k) < 1 or int(k) > h.shape[0]:
        raise ValueError("k must satisfy 1 <= k <= rows(H)")
    k = int(k)
    p, supp_rows, supp_cols = _prefix_graph(h, k)
    m, n = p.shape
    total_edges = int(np.count_nonzero(p))
    vals_ok = bool(np.all(p >= 0) and np.all(p < Q))
    rank = _gf32_rank(p) if vals_ok else 0
    zero_rows = int(sum(1 for s in supp_rows if not s))
    zero_cols = int(sum(1 for s in supp_cols if not s))
    degs = np.array([len(s) for s in supp_cols], dtype=np.int64)
    deg_min = int(degs.min())
    deg_med = float(np.median(degs))
    deg_max = int(degs.max())
    deg1 = int(np.sum(degs == 1))
    deg2 = int(np.sum(degs == 2))
    deg3 = int(np.sum(degs == 3))
    isolated = int(np.sum(degs == 0))
    dsu = _DSU(m + n)
    for i, s in enumerate(supp_rows):
        for v in s:
            dsu.union(i, m + v)
    comp_of = [dsu.find(x) for x in range(m + n)]
    comp_count = len(set(comp_of))
    var_comp = Counter(dsu.find(m + v) for v in range(n))
    largest_frac = max(var_comp.values()) / n
    hist = {int(d): int(c) for d, c in sorted(Counter(len(s) for s in supp_rows).items())}
    shared: dict = {}
    for rows in supp_cols:
        t = len(rows)
        for a in range(t):
            for b in range(a + 1, t):
                key = (rows[a], rows[b])
                shared[key] = shared.get(key, 0) + 1
    pair_counts: dict = {}
    for rows in supp_cols:
        t = len(rows)
        for a in range(t):
            for b in range(a + 1, t):
                key = (rows[a], rows[b]) if rows[a] < rows[b] else (rows[b], rows[a])
                pair_counts[key] = pair_counts.get(key, 0) + 1
    four = int(sum(c * (c - 1) // 2 for c in pair_counts.values()))
    incid = [0] * n
    for j, rows in enumerate(supp_cols):
        t = len(rows)
        tot = 0
        for a in range(t):
            for b in range(a + 1, t):
                key = (rows[a], rows[b]) if rows[a] < rows[b] else (rows[b], rows[a])
                tot += pair_counts.get(key, 1) - 1
        incid[j] = int(tot)
    incid_max = int(max(incid)) if incid else 0
    mask = (p != 0)
    groups: dict = {}
    for j in range(n):
        key = mask[:, j].tobytes()
        groups.setdefault(key, []).append(j)
    dup = 0
    for members in groups.values():
        if len(members) < 2:
            continue
        if not np.any(mask[:, members[0]]):
            t = len(members)
            dup += t * (t - 1) // 2
            continue
        for a in range(len(members)):
            for b in range(a + 1, len(members)):
                c1 = p[:, members[a]]
                c2 = p[:, members[b]]
                nz = np.flatnonzero(c1)
                s0 = _gf32_mul_vec_vec(
                    np.array([int(c1[nz[0]])]), np.array([_gf32_inv(int(c2[nz[0]]))])
                )[0]
                ok = True
                for i in nz:
                    if int(_gf32_mul_vec_vec(
                            np.array([int(c2[i])]), np.array([int(s0)]))[0]) != int(c1[i]):
                        ok = False
                        break
                if ok:
                    dup += 1
    triple_counter: dict = {}
    for s in supp_cols:
        if len(s) == 3:
            key = tuple(sorted(int(v) for v in s))
            triple_counter[key] = triple_counter.get(key, 0) + 1
    triple_dup = int(sum(c * (c - 1) // 2 for c in triple_counter.values()))
    base_counter: dict = {}
    for s in supp_cols:
        if len(s) >= 2:
            key = tuple(sorted(int(v) for v in s)[:2])
            base_counter[key] = base_counter.get(key, 0) + 1
    base_dup = int(sum(c * (c - 1) // 2 for c in base_counter.values()))
    passed = bool(
        rank == k and zero_rows == 0 and zero_cols == 0 and isolated == 0
        and comp_count == 1 and largest_frac == 1.0 and dup == 0 and vals_ok
        and deg_min >= 2 and base_dup == 0 and triple_dup == 0
    )
    if not passed:
        status = "STRUCTURE_BLOCKED"
    elif four == 0:
        status = "STRUCTURE_PASS"
    else:
        status = "STRUCTURE_PASS_WITH_CYCLE_RISK"
    return {
        "prefix_rows": k,
        "total_edges": total_edges,
        "column_degree_full": deg_max,
        "rank": int(rank),
        "zero_rows": zero_rows,
        "zero_columns": zero_cols,
        "variable_degree_min": deg_min,
        "variable_degree_median": deg_med,
        "variable_degree_max": deg_max,
        "degree1_variables": deg1,
        "degree2_variables": deg2,
        "degree3_variables": deg3,
        "connected_components": int(comp_count),
        "largest_component_fraction": float(largest_frac),
        "isolated_variables": isolated,
        "row_degree_histogram": hist,
        "four_cycles": four,
        "four_cycle_variable_incidence_max": incid_max,
        "duplicate_projective_columns": int(dup),
        "base_pair_duplicates": int(base_dup),
        "support_triple_duplicates": int(triple_dup),
        "coefficients_nonzero": vals_ok,
        "passed": passed,
        "status": status,
    }


def audit_frozen_prefixes(h, prefixes, field=None):
    """Audit every frozen disclosure prefix of ``H`` in the given order."""
    h = np.asarray(h)
    prefs = tuple(int(v) for v in prefixes)
    if any(v < 1 or v > h.shape[0] for v in prefs):
        raise ValueError("every prefix must satisfy 1 <= k <= rows(H)")
    audits = [audit_prefix(h, v, field) for v in prefs]
    passed = bool(all(a["passed"] for a in audits))
    if not passed:
        status = "STRUCTURE_BLOCKED"
    elif any(a["four_cycles"] > 0 for a in audits):
        status = "STRUCTURE_PASS_WITH_CYCLE_RISK"
    else:
        status = "STRUCTURE_PASS"
    return {
        "prefix_rows": list(prefs),
        "audits": audits,
        "passed": passed,
        "status": status,
    }


# --------------------------------------------------------------------------
# F5. Matched generator (in-memory only)
# --------------------------------------------------------------------------
def sample_matched_block(p_b, p_f, n, seed):
    """Sample one matched block: ``B ~ P(B)``, ``A ~ P_F(.|B)``.

    Probability tables are injected by the caller (never read from files
    here) and must be normalized and finite. Uses a fixed NumPy generator
    so ``seed`` reproduces the block exactly. Returns a dict of int arrays
    ``bob``, ``alice``, ``u1``, ``u2`` with ``A = 32*U1 + U2``.
    """
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    pf = np.asarray(p_f, dtype=np.float64)
    n = int(n)
    if n < 1:
        raise ValueError("n must be positive")
    if pb.ndim != 1 or pf.ndim != 2 or pf.shape[1] != pb.shape[0]:
        raise ValueError("shapes must satisfy p_f(A, B) with len(p_b) == B")
    if pf.shape[0] % Q != 0:
        raise ValueError("p_f Alice dim must be a nonzero multiple of 32")
    if (not np.all(np.isfinite(pb)) or not np.all(np.isfinite(pf))
            or np.any(pb < 0) or np.any(pf < 0)):
        raise ValueError("probability inputs must be finite and nonnegative")
    if abs(float(pb.sum()) - 1.0) > 1e-8:
        raise ValueError("p_b must sum to 1")
    col = pf.sum(axis=0)
    if np.any(np.abs(col - 1.0) > 1e-8):
        raise ValueError("every p_f column must sum to 1")
    rng = np.random.default_rng(int(seed))
    b_dim, a_dim = pb.shape[0], pf.shape[0]
    bob = rng.choice(b_dim, size=n, p=pb / pb.sum())
    alice = np.empty(n, dtype=np.int64)
    for i in range(n):
        c = pf[:, int(bob[i])]
        alice[i] = int(rng.choice(a_dim, p=c / c.sum()))
    u1, u2 = symbols_to_layers(alice)
    return {
        "bob": np.asarray(bob, dtype=np.int64),
        "alice": alice,
        "u1": np.asarray(u1, dtype=np.int64),
        "u2": np.asarray(u2, dtype=np.int64),
    }


# --------------------------------------------------------------------------
# Shared phase plumbing (private)
# --------------------------------------------------------------------------
def _require_authorized(phase, authorized):
    if not authorized:
        raise NotAuthorizedError(
            f"phase '{phase}' is not authorized; refusing before any work"
        )


def _require_decode_fn(phase, decode_fn):
    if decode_fn is None:
        raise ValueError(
            f"phase '{phase}' requires an injected decode_fn; "
            "no default decoder is used"
        )
    if not callable(decode_fn):
        raise ValueError(f"phase '{phase}' decode_fn must be callable")


def _split_layers(h):
    if isinstance(h, dict):
        h1 = np.asarray(h["L1"], dtype=np.int64)
        h2 = np.asarray(h["L2"], dtype=np.int64)
    elif h is None:
        raise ValueError("a mother matrix H (or L1/L2 mapping) is required")
    else:
        h1 = h2 = np.asarray(h, dtype=np.int64)
    if h1.ndim != 2 or h2.ndim != 2 or h1.shape[1] != h2.shape[1]:
        raise ValueError("L1/L2 matrices must be 2-D with equal width")
    if np.any(h1 < 0) or np.any(h1 >= Q) or np.any(h2 < 0) or np.any(h2 >= Q):
        raise ValueError("H values must lie in 0..31")
    return h1, h2


def _softmax_rows(z):
    z = np.asarray(z, dtype=np.float64)
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def _rows_required(ce, width, f):
    return int(math.ceil(width * float(ce) * float(f) / 5.0))


def _ce_stats(p_f, p_b):
    pf = np.asarray(p_f, dtype=np.float64)
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    joint = float(-np.sum(pb * np.sum(
        np.maximum(pf, AUDIT_FLOOR) * np.log2(np.maximum(pf, AUDIT_FLOOR)), axis=0)))
    p1 = marginalize_f_to_p1(pf)
    l1 = float(-np.sum(pb * np.sum(
        np.maximum(p1, AUDIT_FLOOR) * np.log2(np.maximum(p1, AUDIT_FLOOR)), axis=0)))
    p2 = conditionalize_f_to_p2(pf)
    seg = np.moveaxis(p2, 1, 0)
    l2 = float(-np.sum(
        pb[:, None, None] * np.moveaxis(p1, 1, 0)[:, :, None]
        * np.maximum(seg, AUDIT_FLOOR) * np.log2(np.maximum(seg, AUDIT_FLOOR))))
    return joint, l1, l2, p1, p2


def _rss_bytes():
    try:
        import resource

        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    except Exception:
        return None


def _decode_block(decode_fn, h, prior, x_true):
    syn = _gf32_syndrome(h, np.asarray(x_true, dtype=np.int64))
    res = decode_fn(h, np.asarray(prior, dtype=np.float64), syn, layer=None)
    if not isinstance(res, dict):
        raise ValueError("decode_fn must return a dict result")
    for key in ("x_hat", "syndrome_ok", "iterations"):
        if key not in res:
            raise ValueError(f"decode_fn result missing '{key}'")
    x_hat = np.asarray(res["x_hat"], dtype=np.int64).ravel()
    exact = bool(x_hat.shape == np.asarray(x_true).shape
                 and np.array_equal(x_hat, np.asarray(x_true, dtype=np.int64)))
    it = res["iterations"]
    try:
        it = int(it)
    except Exception:
        raise ValueError("decode_fn result 'iterations' must be integral")
    beliefs = res.get("final_beliefs")
    finite = bool(np.all(np.isfinite(np.asarray(beliefs, dtype=np.float64)))) \
        if beliefs is not None else True
    return exact, bool(res["syndrome_ok"]), it, finite, res.get("final_beliefs")


def _run_layered_block(decode_fn, h1, h2, p1, p2, block, oracle):
    n = block["bob"].shape[0]
    prior_l1 = _floor_renorm(p1[:, block["bob"]].T, DECODER_FLOOR)
    e1, s1, it1, f1, bel1 = _decode_block(decode_fn, h1, prior_l1, block["u1"])
    if bel1 is None:
        q = np.full_like(prior_l1, 1.0 / prior_l1.shape[1])
    else:
        bel = np.asarray(bel1, dtype=np.float64)
        q = _softmax_rows(bel) if bel.shape != prior_l1.shape else _softmax_rows(bel)
        if q.shape != prior_l1.shape:
            q = np.full_like(prior_l1, 1.0 / prior_l1.shape[1])
    prior_l2 = app_fed_l2_prior(p2, block["bob"], q)
    e2, s2, it2, f2, _ = _decode_block(decode_fn, h2, prior_l2, block["u2"])
    out = {
        "app_exact": bool(e1 and e2), "app_l1_exact": bool(e1),
        "app_syndrome_ok": bool(s1 and s2), "iterations": int(it1 + it2),
        "finite": bool(f1 and f2),
    }
    if oracle:
        prior_o = oracle_l2_prior(p2, block["bob"], block["u1"])
        eo, so, ito, fo, _ = _decode_block(decode_fn, h2, prior_o, block["u2"])
        out.update({"oracle_exact": bool(eo), "oracle_syndrome_ok": bool(so),
                    "oracle_iterations": int(ito), "oracle_finite": bool(fo)})
    return out


# --------------------------------------------------------------------------
# F6. Phase functions (implement but DO NOT execute with a real decoder)
# --------------------------------------------------------------------------
def run_structure_phase(*, h=None, layer="L1", authorized=False):
    """M0 structure gate: audit every frozen prefix of one mother matrix."""
    _require_authorized("structure", authorized)
    if layer == "L1":
        prefixes, seed, k_min = L1_PREFIXES, L1_GRAPH_SEED, L1_K_MIN
    elif layer == "L2":
        prefixes, seed, k_min = L2_PREFIXES, L2_GRAPH_SEED, L2_K_MIN
    else:
        raise ValueError("layer must be 'L1' or 'L2'")
    if h is None:
        h = build_dv3_nested_mother(N, M_MAX, k_min, seed, None)
    h = np.asarray(h)
    if h.ndim != 2 or h.shape[1] != N or h.shape[0] < max(prefixes):
        raise ValueError("structure mother must cover the frozen prefixes")
    rep = audit_frozen_prefixes(h, prefixes)
    return {
        "phase": "structure",
        "layer": layer,
        "m_max": int(h.shape[0]),
        "n": int(h.shape[1]),
        "k_min": int(k_min),
        "graph_seed": int(seed),
        "prefix_rows": rep["prefix_rows"],
        "per_prefix": rep["audits"],
        "passed": bool(rep["passed"]),
        "status": rep["status"],
        "decoder_calls": 0,
    }


def run_g0_phase(*, h=None, p_b=None, p_f=None,
                 decode_fn=None, authorized=False):
    """G0 tiny math gate over the frozen G0 seeds (noiseless, oracle prior)."""
    _require_authorized("g0", authorized)
    _require_decode_fn("g0", decode_fn)
    h1, h2 = _split_layers(h)
    if p_b is None or p_f is None:
        raise ValueError("g0 requires injected p_b and p_f tables")
    pf = np.asarray(p_f, dtype=np.float64)
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    joint, l1, l2, p1, p2 = _ce_stats(pf, pb)
    chain_err = abs(joint - l1 - l2)
    marg_err = float(max(
        float(np.max(np.abs(pf.sum(axis=0) - 1.0))),
        float(np.max(np.abs(p1.sum(axis=0) - 1.0))),
    ))
    cond_err = float(np.max(np.abs(
        np.moveaxis(p2, 2, 1).sum(axis=1) - 1.0)))
    width = int(h1.shape[1])
    if width > 9:
        raise ValueError("g0 tiny blocks require matrix width <= 9")
    exact = 0
    calls = 0
    for seed in G0_SEEDS:
        block = sample_matched_block(pb, pf, width, seed)
        prior_o = oracle_l2_prior(p2, block["bob"], block["u1"])
        e, _, _, _, _ = _decode_block(decode_fn, h2, prior_o, block["u2"])
        exact += int(e)
        calls += 1
    attempted = len(G0_SEEDS)
    return {
        "phase": "g0",
        "marginal_err": marg_err,
        "conditional_err": cond_err,
        "chain_err": float(chain_err),
        "attempted_blocks": attempted,
        "exact_count": int(exact),
        "exact_failure_fraction": 1.0 - exact / attempted,
        "decoder_calls": int(calls),
        "passed": bool(marg_err < 1e-12 and cond_err < 1e-12
                        and chain_err < 1e-10 and exact == attempted),
    }


def run_p0_cost_phase(*, h=None, p_b=None, p_f=None,
                      decode_fn=None, authorized=False):
    """P0 cost preflight: tiny wall/iteration footprint, APP plus oracle."""
    _require_authorized("p0-cost", authorized)
    _require_decode_fn("p0-cost", decode_fn)
    h1, h2 = _split_layers(h)
    if p_b is None or p_f is None:
        raise ValueError("p0-cost requires injected p_b and p_f tables")
    pf = np.asarray(p_f, dtype=np.float64)
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    _, _, _, p1, p2 = _ce_stats(pf, pb)
    width = int(h1.shape[1])
    records = []
    calls = 0
    t0 = time.perf_counter()
    for f in P0_F:
        for kind in ("app", "oracle"):
            ws, its = [], []
            for seed in G0_SEEDS[:2]:
                block = sample_matched_block(pb, pf, width, seed)
                t1 = time.perf_counter()
                if kind == "app":
                    rec = _run_layered_block(decode_fn, h1, h2, p1, p2, block, False)
                    calls += 2
                else:
                    prior_o = oracle_l2_prior(p2, block["bob"], block["u1"])
                    eo, _, ito, _, _ = _decode_block(decode_fn, h2, prior_o, block["u2"])
                    rec = {"oracle_exact": eo, "oracle_iterations": ito}
                    calls += 1
                ws.append(time.perf_counter() - t1)
                its.append(rec.get("iterations", rec.get("oracle_iterations", 0)))
            records.append({"f": float(f), "kind": kind,
                            "wall_s": float(sum(ws)),
                            "iterations": int(sum(its)),
                            "rss_bytes": _rss_bytes()})
    total_wall = time.perf_counter() - t0
    per_call = total_wall / calls if calls else 0.0
    proj_g1 = per_call * (G1_BLOCKS * len(G1_F)
                          + G1_ORACLE_SUBSET * len(G1_F))
    proj_g2 = per_call * (G2_BLOCKS * len(G2_F)
                          + G2_ORACLE_SUBSET * len(G2_F))
    return {
        "phase": "p0-cost",
        "block_length": width,
        "f_list": [float(f) for f in P0_F],
        "records": records,
        "decoder_calls": int(calls),
        "projected_g1_s": float(proj_g1),
        "projected_g2_s": float(proj_g2),
        "projection_blocked": bool(proj_g2 > 3600.0),
        "passed": True,
    }


def _run_rate_scan(decode_fn, h1, h2, p1, p2, pb, pf, width, f_list,
                   n_blocks, seeds, oracle_subset):
    per_f = []
    calls = 0
    nonfinite = 0
    for f in f_list:
        app_ok = 0
        ora_ok = 0
        for t, seed in enumerate(seeds[:n_blocks]):
            block = sample_matched_block(pb, pf, width, seed)
            rec = _run_layered_block(decode_fn, h1, h2, p1, p2, block,
                                     t < oracle_subset)
            app_ok += int(rec["app_exact"])
            calls += 2
            nonfinite += int(not rec["finite"])
            if t < oracle_subset:
                ora_ok += int(rec["oracle_exact"])
                calls += 1
                nonfinite += int(not rec.get("oracle_finite", True))
        rate = app_ok / n_blocks
        per_f.append({"f": float(f),
                      "attempted": int(n_blocks),
                      "app_exact_count": int(app_ok),
                      "app_exact_rate": float(rate),
                      "app_failure_fraction": float(1.0 - rate),
                      "oracle_exact_count": int(ora_ok)})
    rates = [r["app_exact_rate"] for r in per_f]
    mono = bool(all(b >= a for a, b in zip(rates, rates[1:])))
    return per_f, mono, calls, nonfinite


def run_g1_phase(*, h=None, p_b=None, p_f=None,
                 decode_fn=None, authorized=False):
    """G1 integration trend gate over the frozen G1 seeds (fake decoder only)."""
    _require_authorized("g1", authorized)
    _require_decode_fn("g1", decode_fn)
    h1, h2 = _split_layers(h)
    if p_b is None or p_f is None:
        raise ValueError("g1 requires injected p_b and p_f tables")
    pf = np.asarray(p_f, dtype=np.float64)
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    _, _, _, p1, p2 = _ce_stats(pf, pb)
    width = int(h1.shape[1])
    per_f, mono, calls, nonfinite = _run_rate_scan(
        decode_fn, h1, h2, p1, p2, pb, pf, width, G1_F,
        G1_BLOCKS, G1_SEEDS, G1_ORACLE_SUBSET)
    frozen = {str(f): {"m1": _rows_required(CE_L1_MEAN, G1_WIDTH, f),
                       "m2": _rows_required(CE_L2_ORACLE_MEAN, G1_WIDTH, f)}
              for f in G1_F}
    return {
        "phase": "g1",
        "block_length": width,
        "f_list": [float(f) for f in G1_F],
        "frozen_rows": frozen,
        "per_f": per_f,
        "monotonic": mono,
        "crashes": 0,
        "nonfinite": int(nonfinite),
        "decoder_calls": int(calls),
        "passed": bool(mono and nonfinite == 0),
    }


def run_g2_phase(*, h=None, p_b=None, p_f=None,
                 decode_fn=None, authorized=False):
    """G2 sole grading experiment over the frozen G2 seeds (fake decoder only)."""
    _require_authorized("g2", authorized)
    _require_decode_fn("g2", decode_fn)
    h1, h2 = _split_layers(h)
    if p_b is None or p_f is None:
        raise ValueError("g2 requires injected p_b and p_f tables")
    pf = np.asarray(p_f, dtype=np.float64)
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    _, _, _, p1, p2 = _ce_stats(pf, pb)
    width = int(h1.shape[1])
    per_f, mono, calls, nonfinite = _run_rate_scan(
        decode_fn, h1, h2, p1, p2, pb, pf, width, G2_F,
        G2_BLOCKS, G2_SEEDS, G2_ORACLE_SUBSET)
    frozen = {str(f): {"m1": _rows_required(CE_L1_MEAN, G2_WIDTH, f),
                       "m2": _rows_required(CE_L2_ORACLE_MEAN, G2_WIDTH, f)}
              for f in G2_F}
    top = per_f[-1]["app_exact_rate"]
    if nonfinite > 0:
        grade = GRADE_BLOCKED
    elif top >= 0.9 and mono:
        grade = GRADE_QUALIFIED
    elif top >= 0.5:
        grade = GRADE_INCONCLUSIVE
    else:
        grade = GRADE_FAILED
    return {
        "phase": "g2",
        "block_length": width,
        "f_list": [float(f) for f in G2_F],
        "frozen_rows": frozen,
        "per_f": per_f,
        "monotonic": mono,
        "crashes": 0,
        "nonfinite": int(nonfinite),
        "decoder_calls": int(calls),
        "grade": grade,
        "passed": bool(grade == GRADE_QUALIFIED),
    }


# --------------------------------------------------------------------------
# F7. Structure orchestration: preflight + L1->L2 sequence + evidence writer
# (STRUCTURE_EXECUTION_PACKET frozen contract; small/fake only this round)
# --------------------------------------------------------------------------
STRUCTURE_FORMAL_ROOT = "workspace/v72p2d5_structure/20260905_r2"
STRUCTURE_EVIDENCE_FILES = ("results.json", "table.csv", "report.md",
                            "execution_summary.json")
STRUCTURE_SINGLE_BUDGET_S = 900.0
STRUCTURE_TOTAL_BUDGET_S = 1800.0
STRUCTURE_RSS_BUDGET_BYTES = 2 * 1024**3
PREFLIGHT_FIXTURE = (12, 10, 7, (7, 8, 9, 10))
PREFLIGHT_PROXY = (64, 64, 48, (48, 54, 59, 64))
PREFLIGHT_MAX_N = 256


def extrapolate_structure_cost(*, t_build_l1_s, t_build_l2_s,
                               t_rank_proxy_s, rss_probe_bytes,
                               proxy_n=PREFLIGHT_PROXY[0],
                               proxy_m=PREFLIGHT_PROXY[1]):
    """Recomputable 2-layer cost projection (frozen formula).

    edge_scale = N / proxy_n scales dv3 build work (3n edges, linear scan);
    rank_scale = (M_MAX / proxy_m)^2 * (N / proxy_n) scales GF32 prefix-rank
    elimination work (~k^2 n per prefix). Per-layer full build = measured
    proxy build * edge_scale; per-prefix full rank = measured proxy rank *
    rank_scale. single = max(per-layer build) + 4 prefixes * rank;
    total = both builds + 8 prefixes * rank; rss scales linearly in edges.
    Blocked when single > 900 s, total > 1800 s, or rss >= 2 GiB.
    """
    edge = N / float(proxy_n)
    rank_scale = (M_MAX / float(proxy_m)) ** 2 * edge
    b1 = float(t_build_l1_s) * edge
    b2 = float(t_build_l2_s) * edge
    rk = float(t_rank_proxy_s) * rank_scale
    single = max(b1, b2) + 4.0 * rk
    total = b1 + b2 + 8.0 * rk
    rss = None if rss_probe_bytes is None else int(rss_probe_bytes * edge)
    blocked = bool(single > STRUCTURE_SINGLE_BUDGET_S
                   or total > STRUCTURE_TOTAL_BUDGET_S
                   or (rss is not None and rss >= STRUCTURE_RSS_BUDGET_BYTES))
    return {
        "edge_scale": float(edge),
        "rank_scale": float(rank_scale),
        "build_full_s": {"L1": float(b1), "L2": float(b2)},
        "rank_full_per_prefix_s": float(rk),
        "single_layer_s": float(single),
        "total_s": float(total),
        "rss_projected_bytes": rss,
        "budgets": {"single_s": float(STRUCTURE_SINGLE_BUDGET_S),
                    "total_s": float(STRUCTURE_TOTAL_BUDGET_S),
                    "rss_bytes": int(STRUCTURE_RSS_BUDGET_BYTES)},
        "projection_blocked": blocked,
    }


def run_structure_preflight(*, authorized=False, build_fn=None,
                            audit_fn=None):
    """Cost preflight with small fixture + n<=256 proxy builds only.

    Never builds the full 1000x1024 mother. Records per-layer proxy build
    walls, per-prefix proxy audit (rank-dominated) walls, fixture walls,
    and peak RSS, then projects via :func:`extrapolate_structure_cost`.
    Returns an in-memory dict; a preflight never counts as an attempt.
    """
    _require_authorized("structure", authorized)
    build = build_fn or build_dv3_nested_mother
    audit = audit_fn or audit_prefix
    fn, fm, fk, fprefs = PREFLIGHT_FIXTURE
    pn, pm, pk, pprefs = PREFLIGHT_PROXY
    for n in (fn, pn):
        if int(n) > PREFLIGHT_MAX_N:
            raise ValueError("preflight probes are capped at n<=256")
    build_wall = {}
    fixture_wall = {}
    rank_wall = {}
    for layer, seed in (("L1", L1_GRAPH_SEED), ("L2", L2_GRAPH_SEED)):
        t0 = time.perf_counter()
        build(fn, fm, fk, seed)
        fixture_wall[layer] = time.perf_counter() - t0
        t0 = time.perf_counter()
        h = build(pn, pm, pk, seed)
        build_wall[layer] = time.perf_counter() - t0
        walls = []
        for k in pprefs:
            t1 = time.perf_counter()
            audit(h, int(k))
            walls.append(time.perf_counter() - t1)
        rank_wall[layer] = [float(w) for w in walls]
    pooled = [w for walls in rank_wall.values() for w in walls]
    mean_rank = sum(pooled) / len(pooled) if pooled else 0.0
    rss = _rss_bytes()
    proj = extrapolate_structure_cost(
        t_build_l1_s=build_wall["L1"], t_build_l2_s=build_wall["L2"],
        t_rank_proxy_s=mean_rank, rss_probe_bytes=rss)
    blocked = bool(proj["projection_blocked"])
    return {
        "phase": "structure_preflight",
        "fixture": {"n": int(fn), "m_max": int(fm), "k_min": int(fk),
                    "prefixes": [int(v) for v in fprefs]},
        "proxy": {"n": int(pn), "m_max": int(pm), "k_min": int(pk),
                  "prefixes": [int(v) for v in pprefs]},
        "fixture_wall_s": {k: float(v) for k, v in fixture_wall.items()},
        "build_wall_s": {k: float(v) for k, v in build_wall.items()},
        "rank_wall_s": {k: list(v) for k, v in rank_wall.items()},
        "rss_bytes": rss,
        "projected": proj,
        "proceed": not blocked,
        "projection_blocked": blocked,
        "decoder_calls": 0,
    }


def _structure_terminal(base, *, decision, attempts, completed, events,
                        preflight, layers, l2_attempted, build_calls,
                        error, out_dir, write):
    res = dict(base)
    res.update({"decision": decision, "attempts": int(attempts),
                "completed": int(completed), "events": list(events),
                "preflight": preflight, "layers": dict(layers),
                "l2_attempted": bool(l2_attempted),
                "build_calls": dict(build_calls), "error": error})
    if out_dir is not None:
        write(out_dir, res)
    return res


def run_structure_sequence(*, authorized=False, build_fn=None,
                           audit_fn=None, preflight_fn=None,
                           writer_fn=None, out_dir=None):
    """Single structure orchestrator: preflight, then L1, then L2.

    Authorization is checked before any preflight/builder/writer/dir work.
    Preflight never counts as an attempt; attempts moves 0->1 immediately
    before the first full L1 builder call. Each layer is built at most
    once: an L1 hard fail stops the sequence with L2 never built. Failures
    stop the sequence with seeds, order, family, and coefficients left
    unchanged. Exceptions yield STRUCTURE_BLOCKED with completed=0;
    audit-complete hard fails yield completed=1. With out_dir given, the
    4-file evidence set is written for every terminal outcome. Returns the
    in-memory result; never touches cycle_state.yaml.
    """
    if not authorized:
        raise NotAuthorizedError(
            "phase 'structure' is not authorized; refusing before any work")
    build = build_fn or build_dv3_nested_mother
    audit = audit_fn or audit_frozen_prefixes
    preflight = preflight_fn or run_structure_preflight
    write = writer_fn or write_structure_evidence
    base = {"phase": "structure", "decoder_calls": 0, "cal_rows_read": 0,
            "val_rows_read": 0, "formal_root": STRUCTURE_FORMAL_ROOT}
    events = ["auth_ok"]
    calls = {"L1": 0, "L2": 0}
    try:
        pf = preflight(authorized=True)
    except Exception as exc:
        return _structure_terminal(
            base, decision="STRUCTURE_RESOURCE_PROJECTION_BLOCKED",
            attempts=0, completed=0, events=events + ["preflight_error"],
            preflight=None, layers={}, l2_attempted=False,
            build_calls=calls, error=f"preflight: {exc}",
            out_dir=out_dir, write=write)
    events.append("preflight_done")
    if not pf.get("proceed", False):
        return _structure_terminal(
            base, decision="STRUCTURE_RESOURCE_PROJECTION_BLOCKED",
            attempts=0, completed=0, events=events, preflight=pf,
            layers={}, l2_attempted=False, build_calls=calls, error=None,
            out_dir=out_dir, write=write)
    attempts = 1
    events.append("attempt=1")
    layers = {}
    try:
        h1 = build(N, M_MAX, L1_K_MIN, L1_GRAPH_SEED)
    except Exception as exc:
        return _structure_terminal(
            base, decision="STRUCTURE_BLOCKED", attempts=attempts,
            completed=0, events=events, preflight=pf, layers=layers,
            l2_attempted=False, build_calls=calls,
            error=f"L1 build: {exc}", out_dir=out_dir, write=write)
    calls["L1"] = 1
    events.append("L1_build")
    try:
        a1 = audit(h1, L1_PREFIXES)
    except Exception as exc:
        return _structure_terminal(
            base, decision="STRUCTURE_BLOCKED", attempts=attempts,
            completed=0, events=events, preflight=pf, layers=layers,
            l2_attempted=False, build_calls=calls,
            error=f"L1 audit: {exc}", out_dir=out_dir, write=write)
    events.append("L1_audit")
    layers["L1"] = {"graph_seed": int(L1_GRAPH_SEED), "m_max": int(M_MAX),
                    "n": int(N), "k_min": int(L1_K_MIN),
                    "prefix_rows": [int(v) for v in a1["prefix_rows"]],
                    "audits": a1["audits"], "passed": bool(a1["passed"]),
                    "status": a1["status"]}
    if not a1.get("passed", False):
        events.append("L1_blocked")
        return _structure_terminal(
            base, decision="STRUCTURE_BLOCKED", attempts=attempts,
            completed=1, events=events, preflight=pf, layers=layers,
            l2_attempted=False, build_calls=calls, error=None,
            out_dir=out_dir, write=write)
    events.append("L1_pass")
    try:
        h2 = build(N, M_MAX, L2_K_MIN, L2_GRAPH_SEED)
    except Exception as exc:
        return _structure_terminal(
            base, decision="STRUCTURE_BLOCKED", attempts=attempts,
            completed=0, events=events, preflight=pf, layers=layers,
            l2_attempted=False, build_calls=calls,
            error=f"L2 build: {exc}", out_dir=out_dir, write=write)
    calls["L2"] = 1
    events.append("L2_build")
    try:
        a2 = audit(h2, L2_PREFIXES)
    except Exception as exc:
        return _structure_terminal(
            base, decision="STRUCTURE_BLOCKED", attempts=attempts,
            completed=0, events=events, preflight=pf, layers=layers,
            l2_attempted=True, build_calls=calls,
            error=f"L2 audit: {exc}", out_dir=out_dir, write=write)
    events.append("L2_audit")
    layers["L2"] = {"graph_seed": int(L2_GRAPH_SEED), "m_max": int(M_MAX),
                    "n": int(N), "k_min": int(L2_K_MIN),
                    "prefix_rows": [int(v) for v in a2["prefix_rows"]],
                    "audits": a2["audits"], "passed": bool(a2["passed"]),
                    "status": a2["status"]}
    if not a2.get("passed", False):
        events.append("L2_blocked")
        return _structure_terminal(
            base, decision="STRUCTURE_BLOCKED", attempts=attempts,
            completed=1, events=events, preflight=pf, layers=layers,
            l2_attempted=True, build_calls=calls, error=None,
            out_dir=out_dir, write=write)
    events.append("L2_pass")
    four_total = sum(int(a["four_cycles"])
                     for info in (a1, a2) for a in info["audits"])
    decision = ("STRUCTURE_PASS" if four_total == 0
                else "STRUCTURE_PASS_WITH_CYCLE_RISK")
    events.append("done")
    return _structure_terminal(
        base, decision=decision, attempts=attempts, completed=1,
        events=events, preflight=pf, layers=layers, l2_attempted=True,
        build_calls=calls, error=None, out_dir=out_dir, write=write)


def write_structure_evidence(out_dir, result):
    """Write exactly the 4 frozen evidence files under out_dir.

    out_dir must not exist (no overwrite, no merge). Only scalars and the
    small per-prefix row-degree histograms are stored; full mothers,
    supports, coefficients, priors, syndromes, decoder messages, digests,
    and absolute paths are never written. Every terminal outcome
    (PASS, CYCLE_RISK, BLOCKED, projection-blocked, exception) yields the
    same 4-file set.
    """
    d = Path(out_dir)
    if d.exists():
        raise FileExistsError(
            f"refusing to overwrite existing evidence dir: {d}")
    d.mkdir(parents=True)
    layers = result.get("layers", {}) or {}
    table_rows = []
    for layer in ("L1", "L2"):
        info = layers.get(layer, {}) or {}
        for a in info.get("audits", []) or []:
            table_rows.append([
                layer, a.get("prefix_rows"), a.get("rank"),
                a.get("zero_rows"), a.get("zero_columns"),
                a.get("isolated_variables"),
                a.get("connected_components"),
                a.get("largest_component_fraction"),
                a.get("duplicate_projective_columns"),
                a.get("coefficients_nonzero"),
                a.get("variable_degree_min"),
                a.get("base_pair_duplicates"),
                a.get("support_triple_duplicates"),
                a.get("four_cycles"), a.get("status")])
    payload = {
        "phase": result.get("phase", "structure"),
        "formal_root": STRUCTURE_FORMAL_ROOT,
        "decision": result.get("decision"),
        "attempts": result.get("attempts"),
        "completed": result.get("completed"),
        "decoder_calls": 0,
        "cal_rows_read": 0,
        "val_rows_read": 0,
        "l2_attempted": result.get("l2_attempted"),
        "build_calls": result.get("build_calls"),
        "error": result.get("error"),
        "events": result.get("events"),
        "preflight": result.get("preflight"),
        "layers": layers,
    }
    with open(d / "results.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    head = ("layer,prefix_rows,rank,zero_rows,zero_columns,"
            "isolated_variables,connected_components,"
            "largest_component_fraction,duplicate_projective_columns,"
            "coefficients_nonzero,variable_degree_min,"
            "base_pair_duplicates,support_triple_duplicates,four_cycles,"
            "status")
    with open(d / "table.csv", "w", encoding="utf-8") as fh:
        fh.write(head + "\n")
        for row in table_rows:
            fh.write(",".join(str(v) for v in row) + "\n")
    rep = ["# V72P2D5 structure evidence",
           f"decision: {result.get('decision')}",
           f"attempts: {result.get('attempts')} (max 1)",
           f"completed: {result.get('completed')}",
           f"decoder_calls: 0",
           f"cal_rows_read: 0",
           f"val_rows_read: 0",
           f"l2_attempted: {result.get('l2_attempted')}",
           f"formal_root: {STRUCTURE_FORMAL_ROOT}"]
    err = result.get("error")
    if err:
        rep.append(f"error: {err}")
    for layer in ("L1", "L2"):
        info = layers.get(layer, {}) or {}
        if not info:
            rep.append(f"{layer}: not attempted")
            continue
        rep.append(f"{layer}: seed {info.get('graph_seed')} "
                   f"status {info.get('status')}")
        for a in info.get("audits", []) or []:
            rep.append(f"  k={a.get('prefix_rows')} rank={a.get('rank')} "
                       f"four_cycles={a.get('four_cycles')} "
                       f"{a.get('status')}")
    with open(d / "report.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(rep) + "\n")
    summary = {
        "phase": result.get("phase", "structure"),
        "formal_root": STRUCTURE_FORMAL_ROOT,
        "decision": result.get("decision"),
        "attempts": result.get("attempts"),
        "completed": result.get("completed"),
        "decoder_calls": 0,
        "cal_rows_read": 0,
        "val_rows_read": 0,
        "l2_attempted": result.get("l2_attempted"),
        "build_calls": result.get("build_calls"),
        "error": result.get("error"),
        "files": list(STRUCTURE_EVIDENCE_FILES),
    }
    with open(d / "execution_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    return list(STRUCTURE_EVIDENCE_FILES)
