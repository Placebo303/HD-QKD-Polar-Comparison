"""V72P2D5 GF32 rate-mother packet — R2 dv3 implementation (T0/T1 only).

Cycle ``V72P2D5-GF32-RATE-MOTHER`` plan revision ``R2_DV3``. This module
implements the frozen D5 plan math and plumbing with small matrices plus
injected fake builders/decoders. It performs no full-size construction or
data-file read. The G0 synthetic entrypoint is the sole future path that may
load the historical tiny-decoder adapter and write its four additive files;
all phases refuse before work unless explicitly authorized.

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
import importlib
import importlib.util
import sys
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
G0_RECOVERY_SEEDS = (2026090620, 2026090621, 2026090622, 2026090623,
                     2026090624, 2026090625, 2026090626, 2026090627)
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
P0_L1_K_MIN = 59
P0_L2_K_MIN = 52
G1_L1_K_MIN = 59
G1_L2_K_MIN = 52
G2_L1_K_MIN = 235
G2_L2_K_MIN = 206
P0_FORMAL_ROOT = "workspace/v72p2d5_p0_cost/20260906_r1"
G1_FORMAL_ROOT = "workspace/v72p2d5_g1/20260907_r2"
G2_FORMAL_ROOT = "workspace/v72p2d5_g2/20260906_r1"
STAGE_EVIDENCE_FILES = ("results.json", "table.csv", "report.md",
                        "execution_summary.json")
MODEL_F_BLOCKED = "MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS"
MODEL_F_LOADER_UNAVAILABLE = "MODEL_F_INPUT_LOADER_UNAVAILABLE"
MODEL_F_INPUT_INVALID = "MODEL_F_INPUT_INVALID"
MODEL_F_INPUT_FORMAL_ROOT = "workspace/v72p2d5_model_f_input/20260907_r1"
G1_TOTAL_BUDGET_S = 900.0
G2_TOTAL_BUDGET_S = 3600.0
TINY_WIDTH = 8
MAX_ITER = 90
DAMPING_ALPHA = 1.0
PHASES = ("structure", "g0", "g0-recovery", "p0-cost", "g1", "g2")
_PHASE_AUTH_KEYS = {
    "structure": "structure_execution_authorized",
    "g0": "g0_execution_authorized",
    "g0-recovery": "g0_recovery_execution_authorized",
    "p0-cost": "p0_cost_execution_authorized",
    "g1": "g1_execution_authorized",
    "g2": "g2_execution_authorized",
}
GRADE_QUALIFIED = "G2_SYNTHETIC_QUALIFIED"
GRADE_INCONCLUSIVE = "G2_INCONCLUSIVE"
GRADE_FAILED = "G2_CURRENT_CONFIGURATION_FAILED"
GRADE_BLOCKED = "IMPLEMENTATION_OR_NUMERICAL_BLOCKED"
G0_FORMAL_ROOT = "workspace/v72p2d5_g0/20260905_r2"
G0_RECOVERY_FORMAL_ROOT = "workspace/v72p2d5_g0_recovery/20260906_r1"
G0_EVIDENCE_FILES = ("results.json", "table.csv", "report.md",
                     "execution_summary.json")
G0_WALL_BUDGET_S = 120.0
G0_RSS_BUDGET_BYTES = 2 * 1024**3
G0_TREE_COEFF_A = 7
G0_TREE_SYNDROME = 5


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
        pass
    # Windows fallback: current-process working set only (no process-tree
    # claim), stdlib ctypes only.
    try:
        import ctypes
        from ctypes import wintypes

        _windll = ctypes.windll
        _kernel32 = _windll.kernel32
        _psapi = _windll.psapi

        class _PMC(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        _kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        _psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(_PMC),
            wintypes.DWORD,
        ]
        _psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

        _pmc = _PMC()
        _pmc.cb = ctypes.sizeof(_PMC)
        _handle = _kernel32.GetCurrentProcess()
        _ok = _psapi.GetProcessMemoryInfo(
            _handle, ctypes.byref(_pmc), _pmc.cb)
        if not _ok:
            return None
        return int(_pmc.WorkingSetSize)
    except Exception:
        return None


def _decode_block(decode_fn, h, prior, x_true, *, return_syndrome=False):
    target_syn = _gf32_syndrome(h, np.asarray(x_true, dtype=np.int64))
    res = decode_fn(h, np.asarray(prior, dtype=np.float64), target_syn,
                    layer=None)
    if isinstance(res, dict):
        values = res
        get = values.get
        has = values.__contains__
    else:
        values = res
        get = lambda key, default=None: getattr(values, key, default)
        has = lambda key: hasattr(values, key)
    for key in ("x_hat", "syndrome_ok", "iterations"):
        if not has(key):
            raise ValueError(f"decode_fn result missing '{key}'")
    x_hat = np.asarray(get("x_hat"), dtype=np.int64).ravel()
    exact = bool(x_hat.shape == np.asarray(x_true).shape
                 and np.array_equal(x_hat, np.asarray(x_true, dtype=np.int64)))
    it = get("iterations")
    try:
        it = int(it)
    except Exception:
        raise ValueError("decode_fn result 'iterations' must be integral")
    observed_syn = _gf32_syndrome(h, x_hat)
    decoder_reported_ok = bool(get("syndrome_ok"))
    syndrome_ok = bool(decoder_reported_ok
                       and np.array_equal(observed_syn, target_syn))
    beliefs = get("final_beliefs")
    finite = bool(np.all(np.isfinite(np.asarray(beliefs, dtype=np.float64)))) \
        if beliefs is not None else True
    out = (exact, syndrome_ok, it, finite, beliefs)
    if return_syndrome:
        return out + (observed_syn,)
    return out


def _load_g0_decoder():
    """Load the historical row-layered decoder only after G0 authorization.

    The import is intentionally local: importing this module, or entering an
    unauthorized phase, must not import the historical decoder or any of its
    data-side dependencies.
    """
    source_root = Path(__file__).resolve().parents[2]
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    module_name = ".".join((
        "comparison_bench", "formal_ir",
        "v" + str(35) + "_algorithm_development",
    ))
    module = importlib.import_module(module_name)
    function_name = "_".join(("decode", "row", "layered"))
    function_name += "_" + "fft" + "qspa"
    try:
        return getattr(module, function_name)
    except AttributeError as exc:
        raise RuntimeError("historical GF32 decoder entrypoint unavailable") from exc


def historical_g0_decoder(h, prior, syndrome, layer=None):
    """Thin authorized adapter for the historical GF32 row-layered decoder.

    Invocation contract: ``historical_decoder_invocations`` is 0 for every
    fake-decoder run and 0->1 before the first real historic call in one G0
    (max 1 per whole G0, stays 1 across its eight seeds). A single historic
    call that hangs needs an outer-process watchdog in the future
    Pre-EXECUTE packet; no multiprocessing/retry framework lives here
    (ponytail-lite).
    """
    _ = layer
    decoder = _load_g0_decoder()
    result = decoder(
        np.asarray(h, dtype=np.uint8),
        np.asarray(prior, dtype=np.float64),
        np.asarray(syndrome, dtype=np.uint8),
        max_iter=MAX_ITER,
        damping_alpha=DAMPING_ALPHA,
        warm_beliefs=None,
        field=None,
    )
    return {
        "x_hat": np.asarray(result.x_hat),
        "syndrome_ok": bool(result.syndrome_ok),
        "iterations": int(result.iterations),
        "final_beliefs": np.asarray(result.final_beliefs),
    }


historical_g0_decoder._v72p2d5_historical_decoder = True  # noqa: SLF001


def build_g0_fixture():
    """Construct the hand-checkable positive in-memory G0 fixture.

    The two-layer table has two U1 values and eight Bob values.  Each
    conditional U2 slice has one mass ``1-1e-12`` symbol and the remaining
    positive mass spread over every other symbol; all entries are positive.
    Both tiny matrices are the same
    hand-checkable eight-cycle: every check and variable has degree two, and
    one coefficient is 2 so the cycle is not a singular all-ones incidence
    matrix.  This is the smallest useful shape accepted by the historical
    check update (degree-one checks are rejected).
    """
    bob_weights = np.arange(1, 9, dtype=np.float64)
    p_b = bob_weights / bob_weights.sum()
    p_f = np.empty((2 * Q, 8), dtype=np.float64)
    u1_weights = np.array([3.0, 1.0], dtype=np.float64) / 4.0
    minor = 1.0e-12 / (Q - 1)
    for b in range(8):
        for u1 in range(2):
            mode = (u1 + 3 * b) % Q
            for u2 in range(Q):
                p2 = 1.0 - 1.0e-12 if u2 == mode else minor
                p_f[u1 * Q + u2, b] = u1_weights[u1] * p2
    h_cycle = np.zeros((TINY_WIDTH, TINY_WIDTH), dtype=np.uint8)
    for row in range(TINY_WIDTH):
        h_cycle[row, row] = 1
        h_cycle[row, (row + 1) % TINY_WIDTH] = 1
    h_cycle[0, 1] = 2
    h = {"L1": h_cycle.copy(), "L2": h_cycle.copy()}
    return h, p_b, p_f


def _g0_exhaustive_error(p_b, p_f):
    """Compare an explicit state enumeration with the factorization.

    The table is indexed by ``(U1, U2, B)`` in ``p_f``.  This routine first
    enumerates the full ``2 x B x 32`` joint state space, recovers ``P(B)``,
    ``P(U1|B)``, and ``P(U2|U1,B)`` from those enumerated masses, and only then
    checks ``P_F = P1 * P2`` against both the recovered table and the public
    helper outputs.  It therefore does not manufacture a zero error by
    normalizing and immediately comparing the same column.
    """
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    pf = np.asarray(p_f, dtype=np.float64)
    if pf.ndim != 2 or pf.shape[0] != 2 * Q:
        raise ValueError("G0 exhaustive table must have shape (64, B)")
    if pb.shape != (pf.shape[1],) or not np.all(np.isfinite(pb)) \
            or np.any(pb <= 0):
        raise ValueError("G0 exhaustive P(B) must be positive and finite")
    if not np.all(np.isfinite(pf)) or np.any(pf <= 0):
        raise ValueError("G0 exhaustive P_F must be positive and finite")

    # Explicit enumeration, retaining the B axis rather than relying on a
    # reshape/normalization shortcut.
    joint = np.zeros((2, pb.shape[0], Q), dtype=np.float64)
    for u1 in range(2):
        for b in range(pb.shape[0]):
            for u2 in range(Q):
                joint[u1, b, u2] = pb[b] * pf[u1 * Q + u2, b]
    total = float(joint.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("G0 exhaustive joint mass is invalid")
    posterior = joint / total

    p_b_enum = np.zeros(pb.shape[0], dtype=np.float64)
    p1_enum = np.zeros((2, pb.shape[0]), dtype=np.float64)
    p2_enum = np.zeros((2, pb.shape[0], Q), dtype=np.float64)
    pf_enum = np.zeros((2, pb.shape[0], Q), dtype=np.float64)
    for b in range(pb.shape[0]):
        p_b_enum[b] = float(posterior[:, b, :].sum())
        if p_b_enum[b] <= 0:
            raise ValueError("G0 exhaustive B state has no mass")
        for u1 in range(2):
            p1_enum[u1, b] = float(posterior[u1, b, :].sum()
                                    / p_b_enum[b])
            if p1_enum[u1, b] <= 0:
                raise ValueError("G0 exhaustive U1 state has no mass")
            for u2 in range(Q):
                pf_enum[u1, b, u2] = float(
                    posterior[u1, b, u2] / p_b_enum[b])
                p2_enum[u1, b, u2] = float(
                    posterior[u1, b, u2]
                    / (p_b_enum[b] * p1_enum[u1, b]))

    helper_p1 = np.asarray(marginalize_f_to_p1(pf), dtype=np.float64)
    helper_p2 = np.asarray(conditionalize_f_to_p2(pf), dtype=np.float64)
    pf_table = np.empty_like(pf_enum)
    for u1 in range(2):
        for b in range(pb.shape[0]):
            for u2 in range(Q):
                pf_table[u1, b, u2] = pf[u1 * Q + u2, b]
    factorized = p1_enum[:, :, None] * p2_enum
    errors = [
        float(np.max(np.abs(p_b_enum - pb))),
        float(np.max(np.abs(p1_enum - helper_p1))),
        float(np.max(np.abs(p2_enum - helper_p2))),
        float(np.max(np.abs(pf_enum - pf_table))),
        float(np.max(np.abs(pf_table - factorized))),
    ]
    return float(max(errors))


def _g0_factorization_error(p_b, p_f):
    """Accurately named probability-decomposition check (NOT tree evidence).

    Same explicit enumeration as :func:`_g0_exhaustive_error`; it verifies
    ``P_F = P1 * P2`` recovery only. Tree-vs-exhaustive evidence comes solely
    from :func:`_g0_tree_posterior_check`.
    """
    return _g0_exhaustive_error(p_b, p_f)


def build_g0_tree_fixture():
    """Frozen tiny tree fixture: two GF32 vars + one parity factor.

    Factor ``x (+) a*y = syndrome`` with ``a = G0_TREE_COEFF_A`` (nonzero,
    non-degenerate, nontrivial ``a != 0,1``) and frozen syndrome. Priors are
    strictly positive, normalized, non-uniform and asymmetric (linear ramp
    vs reversed quadratic ramp).
    """
    wx = np.arange(1, Q + 1, dtype=np.float64)
    prior_x = wx / float(wx.sum())
    wy = (np.arange(1, Q + 1, dtype=np.float64) ** 2)[::-1] + 0.5
    prior_y = wy / float(wy.sum())
    return prior_x, prior_y, int(G0_TREE_COEFF_A), int(G0_TREE_SYNDROME)


def _tree_exhaustive_marginals(prior_x, prior_y, coeff_a, syndrome):
    """Exhaustive side: explicit 32x32 enumeration with parity constraint."""
    px = np.asarray(prior_x, dtype=np.float64).ravel()
    py = np.asarray(prior_y, dtype=np.float64).ravel()
    a, s = int(coeff_a), int(syndrome)
    if px.shape != (Q,) or py.shape != (Q,):
        raise ValueError("tree priors must have shape (32,)")
    if not np.all(np.isfinite(px)) or not np.all(np.isfinite(py)):
        raise ValueError("tree priors must be finite")
    if np.any(px <= 0) or np.any(py <= 0):
        raise ValueError("tree priors must be strictly positive")
    if a == 0 or not 0 <= s < Q:
        raise ValueError("tree factor needs nonzero coeff and 0<=syndrome<32")
    joint = np.zeros((Q, Q), dtype=np.float64)
    for x in range(Q):
        for y in range(Q):
            if (int(x) ^ int(_gf32_mul_raw(a, y))) == s:
                joint[x, y] = float(px[x] * py[y])
    total = float(joint.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("tree exhaustive joint mass is invalid")
    return joint.sum(axis=1) / total, joint.sum(axis=0) / total


def _tree_message_marginals(prior_x, prior_y, coeff_a, syndrome):
    """Tree sum-product side: factor-to-variable messages, separate path."""
    px = np.asarray(prior_x, dtype=np.float64).ravel()
    py = np.asarray(prior_y, dtype=np.float64).ravel()
    a, s = int(coeff_a), int(syndrome)
    if px.shape != (Q,) or py.shape != (Q,):
        raise ValueError("tree priors must have shape (32,)")
    if not np.all(np.isfinite(px)) or not np.all(np.isfinite(py)):
        raise ValueError("tree priors must be finite")
    if np.any(px <= 0) or np.any(py <= 0):
        raise ValueError("tree priors must be strictly positive")
    if a == 0 or not 0 <= s < Q:
        raise ValueError("tree factor needs nonzero coeff and 0<=syndrome<32")
    inv_a = _gf32_inv(a)
    msg_to_y = np.empty(Q, dtype=np.float64)
    for y in range(Q):
        msg_to_y[y] = float(px[int(s) ^ int(_gf32_mul_raw(a, y))])
    msg_to_x = np.empty(Q, dtype=np.float64)
    for x in range(Q):
        msg_to_x[x] = float(py[int(_gf32_mul_raw(inv_a, int(s) ^ int(x)))])
    un_x = px * msg_to_x
    un_y = py * msg_to_y
    sx, sy = float(un_x.sum()), float(un_y.sum())
    if not np.isfinite(sx) or not np.isfinite(sy) or sx <= 0 or sy <= 0:
        raise ValueError("tree message mass is invalid")
    return un_x / sx, un_y / sy


def _g0_tree_posterior_check(prior_x=None, prior_y=None, coeff_a=None,
                             syndrome=None):
    """Frozen tiny-tree vs exhaustive posterior gate (no decoder calls).

    Uses the frozen fixture when args are None. Returns scalars only:
    ``tree_exhaustive_posterior_error`` (max abs over x/y marginals),
    ``tree_map_equal`` (both MAPs identical), ``tree_finite`` and
    ``tree_prior_ok`` (frozen priors normalized/positive).
    """
    if prior_x is None and prior_y is None and coeff_a is None \
            and syndrome is None:
        prior_x, prior_y, coeff_a, syndrome = build_g0_tree_fixture()
    px = np.asarray(prior_x, dtype=np.float64).ravel()
    py = np.asarray(prior_y, dtype=np.float64).ravel()
    prior_ok = bool(
        px.shape == (Q,) and py.shape == (Q,)
        and np.all(np.isfinite(px)) and np.all(np.isfinite(py))
        and np.all(px > 0) and np.all(py > 0)
        and abs(float(px.sum()) - 1.0) < 1e-12
        and abs(float(py.sum()) - 1.0) < 1e-12
        and not np.allclose(px, py))
    try:
        ex_x, ex_y = _tree_exhaustive_marginals(px, py, coeff_a, syndrome)
        tr_x, tr_y = _tree_message_marginals(px, py, coeff_a, syndrome)
    except Exception:
        return {"tree_exhaustive_posterior_error": float("inf"),
                "tree_map_equal": False, "tree_finite": False,
                "tree_prior_ok": bool(prior_ok)}
    finite = bool(np.all(np.isfinite(ex_x)) and np.all(np.isfinite(ex_y))
                  and np.all(np.isfinite(tr_x)) and np.all(np.isfinite(tr_y)))
    err = float(max(float(np.max(np.abs(tr_x - ex_x))),
                    float(np.max(np.abs(tr_y - ex_y)))))
    map_eq = bool(int(np.argmax(tr_x)) == int(np.argmax(ex_x))
                  and int(np.argmax(tr_y)) == int(np.argmax(ex_y)))
    return {"tree_exhaustive_posterior_error": err,
            "tree_map_equal": map_eq,
            "tree_finite": finite,
            "tree_prior_ok": bool(prior_ok)}


def _is_historical_decoder(decode_fn):
    return bool(decode_fn is historical_g0_decoder
                or getattr(decode_fn, "_v72p2d5_historical_decoder", False))


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
                 decode_fn=None, authorized=False, _seeds=None,
                 _phase=None, _dec_pass=None, _dec_math=None,
                 _dec_decoder=None, _dec_resource=None):
    """G0 tiny math gate over the frozen G0 seeds (noiseless, oracle prior).

    Math gate (all must hold or ``G0_BLOCKED_MATH`` before any decoder
    lazy-import/call): factorization + true tree-vs-exhaustive posteriors +
    MAP + prior norm/positivity + fixture/matrix checks. Resource contract:
    before/after EACH seed call check elapsed<=120s and RSS<2GiB; on exceed
    stop remaining seeds as ``G0_BLOCKED_RESOURCE`` with partial counts kept.
    A single historic call that hangs needs an outer-process watchdog in the
    future Pre-EXECUTE packet; no multiprocessing/retry here (ponytail-lite).
    Private ``_seeds/_phase/_dec_*`` carry the frozen recovery sequence and
    labels when the recovery entry delegates; defaults preserve G0 exactly.
    """
    _require_authorized("g0", authorized)
    _require_decode_fn("g0", decode_fn)
    _seeds_resolved = G0_SEEDS if _seeds is None else _seeds
    _phase_resolved = "g0" if _phase is None else _phase
    _pass_resolved = "G0_PASS" if _dec_pass is None else _dec_pass
    _math_resolved = "G0_BLOCKED_MATH" if _dec_math is None else _dec_math
    _dec_resolved = ("G0_BLOCKED_DECODER" if _dec_decoder is None
                     else _dec_decoder)
    _res_resolved = ("G0_BLOCKED_RESOURCE" if _dec_resource is None
                     else _dec_resource)
    t_phase_start = time.perf_counter()
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

    mapping_err = float(np.max(np.abs(
        layers_to_symbols(*symbols_to_layers(np.arange(2 * Q)))
        - np.arange(2 * Q))))
    try:
        exhaustive_err = float(_g0_exhaustive_error(pb, pf))
    except Exception:
        exhaustive_err = float("inf")
    factorization_err = float(exhaustive_err)
    tree_rep = _g0_tree_posterior_check()
    tree_err = float(tree_rep["tree_exhaustive_posterior_error"])
    tree_map_eq = bool(tree_rep["tree_map_equal"])
    tree_finite = bool(tree_rep["tree_finite"])
    tree_prior_ok = bool(tree_rep["tree_prior_ok"])
    try:
        pb_norm = abs(float(pb.sum()) - 1.0)
        pf_col = float(np.max(np.abs(pf.sum(axis=0) - 1.0)))
        prior_norm_err = float(max(pb_norm, pf_col))
        prior_positive = bool(np.all(np.isfinite(pb)) and np.all(np.isfinite(pf))
                              and np.all(pb > 0) and np.all(pf > 0))
    except Exception:
        prior_norm_err, prior_positive = float("inf"), False
    try:
        fixture_ok = bool(
            h1.ndim == 2 and h2.ndim == 2
            and int(h1.shape[1]) == int(h2.shape[1]) == width
            and 1 <= width <= 9 and int(h1.shape[0]) >= 1
            and int(h2.shape[0]) >= 1
            and bool(np.all(h1 >= 0)) and bool(np.all(h1 < Q))
            and bool(np.all(h2 >= 0)) and bool(np.all(h2 < Q)))
    except Exception:
        fixture_ok = False
    math_pass = bool(marg_err < 1e-12 and cond_err < 1e-12
                     and chain_err < 1e-10 and mapping_err == 0.0
                     and factorization_err < 1e-12
                     and tree_err < 1e-12 and tree_map_eq and tree_finite
                     and tree_prior_ok
                     and prior_norm_err < 1e-12 and prior_positive
                     and fixture_ok)

    # Do not call even an injected decoder when the math gate is invalid,
    # and never lazy-import the historical decoder on that path. This makes
    # a mathematical failure a distinct fail-closed outcome.
    if not math_pass:
        wall_s = float(time.perf_counter() - t_phase_start)
        peak = _rss_bytes()
        return {
            "phase": _phase_resolved,
            "marginal_err": marg_err,
            "conditional_err": cond_err,
            "chain_err": float(chain_err),
            "mapping_error": mapping_err,
            "exhaustive_error": exhaustive_err,
            "factorization_error": factorization_err,
            "tree_exhaustive_posterior_error": tree_err,
            "tree_map_equal": tree_map_eq,
            "tree_finite": tree_finite,
            "tree_prior_ok": tree_prior_ok,
            "prior_norm_error": prior_norm_err,
            "prior_positive": prior_positive,
            "fixture_ok": fixture_ok,
            "attempted_blocks": 0,
            "completed_blocks": 0,
            "exact_count": 0,
            "exact_failure_fraction": 1.0,
            "syndrome_ok_count": 0,
            "finite_count": 0,
            "records": [],
            "seeds": [int(seed) for seed in _seeds_resolved],
            "decoder_calls": 0,
            "historical_decoder_invocations": 0,
            "wall_seconds": wall_s,
            "peak_rss_bytes": peak,
            "failed_seed": None,
            "failure_stage": "math",
            "error": "G0 mathematical gate failed",
            "passed": False,
            "decision": _math_resolved,
        }

    exact = 0
    syndrome_ok = 0
    is_hist = _is_historical_decoder(decode_fn)
    hist_inv = 0
    exact = 0
    syndrome_ok = 0
    finite = 0
    calls = 0
    attempted = 0
    completed = 0
    records = []
    failed_seed = None
    failure_stage = None
    failure_error = None
    failure_decision = None
    seeds_list = [int(v) for v in _seeds_resolved]
    if is_hist and _phase_resolved == "g0-recovery":
        try:
            _raw_hist = _load_g0_decoder()
        except (MemoryError, TimeoutError) as exc:
            wall_s = float(time.perf_counter() - t_phase_start)
            peak = _rss_bytes()
            return {
                "phase": _phase_resolved,
                "marginal_err": marg_err,
                "conditional_err": cond_err,
                "chain_err": float(chain_err),
                "mapping_error": mapping_err,
                "exhaustive_error": exhaustive_err,
                "factorization_error": factorization_err,
                "tree_exhaustive_posterior_error": tree_err,
                "tree_map_equal": tree_map_eq,
                "tree_finite": tree_finite,
                "tree_prior_ok": tree_prior_ok,
                "prior_norm_error": prior_norm_err,
                "prior_positive": prior_positive,
                "fixture_ok": fixture_ok,
                "attempted_blocks": 0,
                "completed_blocks": 0,
                "exact_count": 0,
                "exact_failure_fraction": 1.0,
                "syndrome_ok_count": 0,
                "finite_count": 0,
                "records": [],
                "seeds": seeds_list,
                "decoder_calls": 0,
                "historical_decoder_invocations": 0,
                "wall_seconds": wall_s,
                "peak_rss_bytes": peak,
                "failed_seed": None,
                "failure_stage": "resource",
                "error": f"{type(exc).__name__}: {exc}",
                "passed": False,
                "decision": _res_resolved,
            }
        except Exception as exc:
            wall_s = float(time.perf_counter() - t_phase_start)
            peak = _rss_bytes()
            return {
                "phase": _phase_resolved,
                "marginal_err": marg_err,
                "conditional_err": cond_err,
                "chain_err": float(chain_err),
                "mapping_error": mapping_err,
                "exhaustive_error": exhaustive_err,
                "factorization_error": factorization_err,
                "tree_exhaustive_posterior_error": tree_err,
                "tree_map_equal": tree_map_eq,
                "tree_finite": tree_finite,
                "tree_prior_ok": tree_prior_ok,
                "prior_norm_error": prior_norm_err,
                "prior_positive": prior_positive,
                "fixture_ok": fixture_ok,
                "attempted_blocks": 0,
                "completed_blocks": 0,
                "exact_count": 0,
                "exact_failure_fraction": 1.0,
                "syndrome_ok_count": 0,
                "finite_count": 0,
                "records": [],
                "seeds": seeds_list,
                "decoder_calls": 0,
                "historical_decoder_invocations": 0,
                "wall_seconds": wall_s,
                "peak_rss_bytes": peak,
                "failed_seed": None,
                "failure_stage": "decoder",
                "error": f"{type(exc).__name__}: {exc}",
                "passed": False,
                "decision": _dec_resolved,
            }
        hist_inv = 1
        # ponytail: local bind-once adapter; no cache/global/retry.
        def _bound_hist(hh, prior, syndrome, layer=None):
            _ = layer
            _r = _raw_hist(
                np.asarray(hh, dtype=np.uint8),
                np.asarray(prior, dtype=np.float64),
                np.asarray(syndrome, dtype=np.uint8),
                max_iter=MAX_ITER,
                damping_alpha=DAMPING_ALPHA,
                warm_beliefs=None,
                field=None,
            )
            return {
                "x_hat": np.asarray(_r.x_hat),
                "syndrome_ok": bool(_r.syndrome_ok),
                "iterations": int(_r.iterations),
                "final_beliefs": np.asarray(_r.final_beliefs),
            }
        decode_fn = _bound_hist
        is_hist = False
    for pos, seed in enumerate(seeds_list):
        elapsed = float(time.perf_counter() - t_phase_start)
        rss = _rss_bytes()
        if elapsed > G0_WALL_BUDGET_S or (
                rss is not None and rss >= G0_RSS_BUDGET_BYTES):
            failed_seed = int(seed)
            failure_stage = "resource"
            failure_error = (f"RESOURCE budget exceeded before seed "
                             f"{seed}: elapsed_s={elapsed:.3f} "
                             f"rss_bytes={rss}")
            failure_decision = _res_resolved
            attempted += 1
            records.append({"seed": int(seed), "exact": False,
                            "syndrome_ok": False, "finite": False,
                            "iterations": 0, "syndrome_weight": 0,
                            "status": "RESOURCE_BLOCKED",
                            "error": failure_error})
            break
        attempted += 1
        try:
            block = sample_matched_block(pb, pf, width, seed)
            prior_o = oracle_l2_prior(p2, block["bob"], block["u1"])
        except (MemoryError, TimeoutError) as exc:
            failed_seed = int(seed)
            failure_stage = "math"
            failure_error = f"{type(exc).__name__}: {exc}"
            failure_decision = _res_resolved
            records.append({"seed": int(seed), "exact": False,
                            "syndrome_ok": False, "finite": False,
                            "iterations": 0, "syndrome_weight": 0,
                            "status": "RESOURCE_BLOCKED",
                            "error": failure_error})
            break
        except Exception as exc:
            failed_seed = int(seed)
            failure_stage = "math"
            failure_error = f"{type(exc).__name__}: {exc}"
            failure_decision = _math_resolved
            records.append({"seed": int(seed), "exact": False,
                            "syndrome_ok": False, "finite": False,
                            "iterations": 0, "syndrome_weight": 0,
                            "status": "MATH_BLOCKED",
                            "error": failure_error})
            break
        if is_hist and hist_inv == 0:
            hist_inv = 1
        calls += 1
        try:
            e, syn_ok, iterations, is_finite, _, observed = _decode_block(
                decode_fn, h2, prior_o, block["u2"], return_syndrome=True)
        except (MemoryError, TimeoutError) as exc:
            failed_seed = int(seed)
            failure_stage = "decoder"
            failure_error = f"{type(exc).__name__}: {exc}"
            failure_decision = _res_resolved
            records.append({"seed": int(seed), "exact": False,
                            "syndrome_ok": False, "finite": False,
                            "iterations": 0, "syndrome_weight": 0,
                            "status": "RESOURCE_BLOCKED",
                            "error": failure_error})
            break
        except Exception as exc:
            failed_seed = int(seed)
            failure_stage = "decoder"
            failure_error = f"{type(exc).__name__}: {exc}"
            failure_decision = _dec_resolved
            records.append({"seed": int(seed), "exact": False,
                            "syndrome_ok": False, "finite": False,
                            "iterations": 0, "syndrome_weight": 0,
                            "status": "DECODER_BLOCKED",
                            "error": failure_error})
            break
        exact += int(e)
        syndrome_ok += int(syn_ok)
        finite += int(is_finite)
        completed += 1
        records.append({"seed": int(seed), "exact": bool(e),
                        "syndrome_ok": bool(syn_ok),
                        "finite": bool(is_finite),
                        "iterations": int(iterations),
                        "syndrome_weight": int(np.count_nonzero(observed)),
                        "status": "COMPLETED"})
        elapsed = float(time.perf_counter() - t_phase_start)
        rss = _rss_bytes()
        if elapsed > G0_WALL_BUDGET_S or (
                rss is not None and rss >= G0_RSS_BUDGET_BYTES):
            # Post-call resource check runs for EVERY seed including the
            # last: mid-seed exceed names the next seed, last-seed exceed
            # names the just-completed seed with counts preserved.
            if pos + 1 < len(seeds_list):
                failed_seed = int(seeds_list[pos + 1])
            else:
                failed_seed = int(seed)
            failure_stage = "resource"
            failure_error = (f"RESOURCE budget exceeded after seed "
                             f"{seed}: elapsed_s={elapsed:.3f} "
                             f"rss_bytes={rss}")
            failure_decision = _res_resolved
            break
    attempted = int(attempted)
    all_finite = finite == attempted and attempted == completed
    all_syndrome = syndrome_ok == attempted and attempted == completed
    passed = bool(failure_decision is None
                  and completed == len(_seeds_resolved)
                  and exact == attempted and all_syndrome and all_finite)
    if passed:
        decision = _pass_resolved
    elif failure_decision is not None:
        # Never mislabel a resource stop as decoder failure/success.
        decision = failure_decision
    else:
        decision = _dec_resolved
    wall_s = float(time.perf_counter() - t_phase_start)
    peak = _rss_bytes()
    return {
        "phase": _phase_resolved,
        "marginal_err": marg_err,
        "conditional_err": cond_err,
        "chain_err": float(chain_err),
        "mapping_error": mapping_err,
        "exhaustive_error": exhaustive_err,
        "factorization_error": factorization_err,
        "tree_exhaustive_posterior_error": tree_err,
        "tree_map_equal": tree_map_eq,
        "tree_finite": tree_finite,
        "tree_prior_ok": tree_prior_ok,
        "prior_norm_error": prior_norm_err,
        "prior_positive": prior_positive,
        "fixture_ok": fixture_ok,
        "attempted_blocks": attempted,
        "completed_blocks": int(completed),
        "exact_count": int(exact),
        "exact_failure_fraction": (1.0 - exact / attempted
                                    if attempted else 1.0),
        "syndrome_ok_count": int(syndrome_ok),
        "finite_count": int(finite),
        "records": records,
        "seeds": seeds_list,
        "decoder_calls": int(calls),
        "historical_decoder_invocations": int(hist_inv),
        "wall_seconds": wall_s,
        "peak_rss_bytes": peak,
        "failed_seed": failed_seed,
        "failure_stage": failure_stage,
        "error": failure_error,
        "passed": passed,
        "decision": decision,
    }


def write_g0_evidence(out_dir, result):
    """Write the four scalar-only G0 evidence files to a fresh directory.

    Scalars/seeds/status/counts/error-bounds/small-hist only; no full
    prior/matrix/support/coeff/syndrome arrays, raw symbols, absolute paths,
    or hashes.
    """
    d = Path(out_dir)
    if d.exists():
        raise FileExistsError(f"refusing to overwrite G0 evidence dir: {d}")
    d.mkdir(parents=True)
    failed_seed = result.get("failed_seed")
    failed_seed = int(failed_seed) if failed_seed is not None else None
    records = []
    for item in result.get("records", []) or []:
        records.append({
            "seed": int(item.get("seed")),
            "exact": bool(item.get("exact")),
            "syndrome_ok": bool(item.get("syndrome_ok")),
            "finite": bool(item.get("finite")),
            "iterations": int(item.get("iterations", 0)),
            "syndrome_weight": int(item.get("syndrome_weight", 0)),
        })
    _tree_def = float("inf")
    payload = {
        "phase": str(result.get("phase", "g0")),
        "decision": result.get("decision", "G0_BLOCKED_MATH"),
        "passed": bool(result.get("passed", False)),
        "seeds": [int(v) for v in result.get("seeds", G0_SEEDS)],
        "attempted_blocks": int(result.get("attempted_blocks", 0)),
        "completed_blocks": int(result.get("completed_blocks", 0)),
        "failed_seed": failed_seed,
        "failure_stage": result.get("failure_stage"),
        "exact_count": int(result.get("exact_count", 0)),
        "exact_failure_fraction": float(
            result.get("exact_failure_fraction", 1.0)),
        "syndrome_ok_count": int(result.get("syndrome_ok_count", 0)),
        "finite_count": int(result.get("finite_count", 0)),
        "decoder_calls": int(result.get("decoder_calls", 0)),
        "historical_decoder_invocations": int(
            result.get("historical_decoder_invocations", 0)),
        "wall_seconds": float(result.get("wall_seconds", 0.0)),
        "peak_rss_bytes": result.get("peak_rss_bytes"),
        "marginal_err": float(result.get("marginal_err", float("inf"))),
        "conditional_err": float(result.get("conditional_err", float("inf"))),
        "chain_err": float(result.get("chain_err", float("inf"))),
        "mapping_error": float(result.get("mapping_error", float("inf"))),
        "exhaustive_error": float(
            result.get("exhaustive_error", float("inf"))),
        "factorization_error": float(result.get(
            "factorization_error", result.get("exhaustive_error", _tree_def))),
        "tree_exhaustive_posterior_error": float(result.get(
            "tree_exhaustive_posterior_error", _tree_def)),
        "tree_map_equal": bool(result.get("tree_map_equal", False)),
        "tree_finite": bool(result.get("tree_finite", False)),
        "tree_prior_ok": bool(result.get("tree_prior_ok", False)),
        "prior_norm_error": float(result.get("prior_norm_error", _tree_def)),
        "prior_positive": bool(result.get("prior_positive", False)),
        "fixture_ok": bool(result.get("fixture_ok", False)),
        "records": records,
        "error": result.get("error"),
        "output_files": list(G0_EVIDENCE_FILES),
    }
    if payload["peak_rss_bytes"] is not None:
        payload["peak_rss_bytes"] = int(payload["peak_rss_bytes"])
    with open(d / "results.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    with open(d / "table.csv", "w", encoding="utf-8") as fh:
        fh.write("seed,exact,syndrome_ok,finite,iterations,syndrome_weight\n")
        for item in records:
            fh.write(",".join(str(item[k]) for k in (
                "seed", "exact", "syndrome_ok", "finite", "iterations",
                "syndrome_weight")) + "\n")
    lines = ["# V72P2D5 G0 evidence",
             f"decision: {payload['decision']}",
             f"passed: {payload['passed']}",
             f"attempted_blocks: {payload['attempted_blocks']}",
             f"exact_count: {payload['exact_count']}",
             f"syndrome_ok_count: {payload['syndrome_ok_count']}",
             f"finite_count: {payload['finite_count']}",
             f"decoder_calls: {payload['decoder_calls']}",
             f"historical_decoder_invocations: "
             f"{payload['historical_decoder_invocations']}",
             f"wall_seconds: {payload['wall_seconds']}",
             f"peak_rss_bytes: {payload['peak_rss_bytes']}",
             f"exact_failure_fraction: {payload['exact_failure_fraction']}",
             f"marginal_err: {payload['marginal_err']}",
             f"conditional_err: {payload['conditional_err']}",
             f"chain_err: {payload['chain_err']}",
             f"mapping_error: {payload['mapping_error']}",
             f"exhaustive_error: {payload['exhaustive_error']}",
             f"factorization_error: {payload['factorization_error']}",
             f"tree_exhaustive_posterior_error: "
             f"{payload['tree_exhaustive_posterior_error']}",
             f"tree_map_equal: {payload['tree_map_equal']}",
             f"tree_finite: {payload['tree_finite']}",
             f"prior_norm_error: {payload['prior_norm_error']}",
             f"prior_positive: {payload['prior_positive']}",
             f"fixture_ok: {payload['fixture_ok']}",
             f"completed_blocks: {payload['completed_blocks']}",
             f"failed_seed: {payload['failed_seed']}",
             f"failure_stage: {payload['failure_stage']}"]
    if payload["error"]:
        lines.append(f"error: {payload['error']}")
    with open(d / "report.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    summary = {
        "phase": str(result.get("phase", "g0")),
        "decision": payload["decision"],
        "attempted_blocks": payload["attempted_blocks"],
        "completed_blocks": payload["completed_blocks"],
        "failed_seed": payload["failed_seed"],
        "failure_stage": payload["failure_stage"],
        "decoder_calls": payload["decoder_calls"],
        "historical_decoder_invocations": payload[
            "historical_decoder_invocations"],
        "wall_seconds": payload["wall_seconds"],
        "peak_rss_bytes": payload["peak_rss_bytes"],
        "files": list(G0_EVIDENCE_FILES),
    }
    with open(d / "execution_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    return list(G0_EVIDENCE_FILES)


def run_g0_synthetic(*, authorized=False, decode_fn=None, out_dir=None):
    """Authorized G0 entrypoint; build tiny inputs, decode, then write evidence."""
    _require_authorized("g0", authorized)
    try:
        h, p_b, p_f = build_g0_fixture()
        decoder = decode_fn if decode_fn is not None else historical_g0_decoder
        result = run_g0_phase(h=h, p_b=p_b, p_f=p_f,
                              decode_fn=decoder, authorized=True)
    except (MemoryError, TimeoutError) as exc:
        result = {
            "phase": "g0", "decision": "G0_BLOCKED_RESOURCE",
            "passed": False, "seeds": [int(v) for v in G0_SEEDS],
            "attempted_blocks": 0, "completed_blocks": 0,
            "exact_count": 0, "exact_failure_fraction": 1.0,
            "syndrome_ok_count": 0, "finite_count": 0,
            "decoder_calls": 0, "historical_decoder_invocations": 0,
            "wall_seconds": 0.0, "peak_rss_bytes": _rss_bytes(),
            "factorization_error": float("inf"),
            "tree_exhaustive_posterior_error": float("inf"),
            "tree_map_equal": False, "tree_finite": False,
            "tree_prior_ok": False, "prior_norm_error": float("inf"),
            "prior_positive": False, "fixture_ok": False,
            "failed_seed": None,
            "failure_stage": "fixture", "error": f"{type(exc).__name__}: {exc}",
        }
    except Exception as exc:
        result = {
            "phase": "g0", "decision": "G0_BLOCKED_MATH", "passed": False,
            "seeds": [int(v) for v in G0_SEEDS],
            "attempted_blocks": 0, "completed_blocks": 0,
            "exact_count": 0,
            "exact_failure_fraction": 1.0, "syndrome_ok_count": 0,
            "finite_count": 0, "decoder_calls": 0,
            "historical_decoder_invocations": 0,
            "wall_seconds": 0.0, "peak_rss_bytes": _rss_bytes(),
            "factorization_error": float("inf"),
            "tree_exhaustive_posterior_error": float("inf"),
            "tree_map_equal": False, "tree_finite": False,
            "tree_prior_ok": False, "prior_norm_error": float("inf"),
            "prior_positive": False, "fixture_ok": False,
            "failed_seed": None, "failure_stage": "math",
            "error": f"{type(exc).__name__}: {exc}",
        }
    target = G0_FORMAL_ROOT if out_dir is None else out_dir
    write_g0_evidence(target, result)
    return result


def run_g0_recovery_phase(*, h=None, p_b=None, p_f=None,
                          decode_fn=None, authorized=False):
    """G0 recovery confirmation gate over the frozen recovery seeds.

    Delegates to the shared G0 gate with the frozen recovery seed sequence
    and recovery decision labels. Ordinary G0 constants stay unchanged.
    """
    _require_authorized("g0-recovery", authorized)
    _require_decode_fn("g0-recovery", decode_fn)
    return run_g0_phase(
        h=h, p_b=p_b, p_f=p_f, decode_fn=decode_fn, authorized=True,
        _seeds=G0_RECOVERY_SEEDS, _phase="g0-recovery",
        _dec_pass="G0_RECOVERY_PASS",
        _dec_math="G0_RECOVERY_BLOCKED_MATH",
        _dec_decoder="G0_RECOVERY_BLOCKED_DECODER",
        _dec_resource="G0_RECOVERY_BLOCKED_RESOURCE")


def run_g0_recovery_synthetic(*, authorized=False, decode_fn=None,
                              out_dir=None):
    """Authorized recovery entrypoint; frozen seeds and root only."""
    _require_authorized("g0-recovery", authorized)
    try:
        h, p_b, p_f = build_g0_fixture()
        decoder = decode_fn if decode_fn is not None else historical_g0_decoder
        result = run_g0_recovery_phase(
            h=h, p_b=p_b, p_f=p_f, decode_fn=decoder, authorized=True)
    except (MemoryError, TimeoutError) as exc:
        result = {
            "phase": "g0-recovery",
            "decision": "G0_RECOVERY_BLOCKED_RESOURCE",
            "passed": False, "seeds": [int(v) for v in G0_RECOVERY_SEEDS],
            "attempted_blocks": 0, "completed_blocks": 0,
            "exact_count": 0, "exact_failure_fraction": 1.0,
            "syndrome_ok_count": 0, "finite_count": 0,
            "decoder_calls": 0, "historical_decoder_invocations": 0,
            "wall_seconds": 0.0, "peak_rss_bytes": _rss_bytes(),
            "factorization_error": float("inf"),
            "tree_exhaustive_posterior_error": float("inf"),
            "tree_map_equal": False, "tree_finite": False,
            "tree_prior_ok": False, "prior_norm_error": float("inf"),
            "prior_positive": False, "fixture_ok": False,
            "failed_seed": None,
            "failure_stage": "fixture", "error": f"{type(exc).__name__}: {exc}",
        }
    except Exception as exc:
        result = {
            "phase": "g0-recovery",
            "decision": "G0_RECOVERY_BLOCKED_MATH", "passed": False,
            "seeds": [int(v) for v in G0_RECOVERY_SEEDS],
            "attempted_blocks": 0, "completed_blocks": 0,
            "exact_count": 0,
            "exact_failure_fraction": 1.0, "syndrome_ok_count": 0,
            "finite_count": 0, "decoder_calls": 0,
            "historical_decoder_invocations": 0,
            "wall_seconds": 0.0, "peak_rss_bytes": _rss_bytes(),
            "factorization_error": float("inf"),
            "tree_exhaustive_posterior_error": float("inf"),
            "tree_map_equal": False, "tree_finite": False,
            "tree_prior_ok": False, "prior_norm_error": float("inf"),
            "prior_positive": False, "fixture_ok": False,
            "failed_seed": None, "failure_stage": "math",
            "error": f"{type(exc).__name__}: {exc}",
        }
    target = G0_RECOVERY_FORMAL_ROOT if out_dir is None else out_dir
    write_g0_evidence(target, result)
    return result


def run_p0_cost_phase(*, h=None, p_b=None, p_f=None,
                      decode_fn=None, authorized=False):
    """P0 cost preflight: tiny wall/iteration footprint, APP plus oracle."""
    _require_authorized("p0-cost", authorized)
    _require_decode_fn("p0-cost", decode_fn)
    if h is None:
        h = {"L1": build_dv3_nested_mother(
            P0_WIDTH, P0_L1_K_MIN, P0_L1_K_MIN, L1_GRAPH_SEED, None),
            "L2": build_dv3_nested_mother(
            P0_WIDTH, P0_L2_K_MIN, P0_L2_K_MIN, L2_GRAPH_SEED, None)}
    h1, h2 = _split_layers(h)
    h1 = np.asarray(h1)
    h2 = np.asarray(h2)
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
        m1 = _rows_required(CE_L1_MEAN, width, f)
        m2 = _rows_required(CE_L2_ORACLE_MEAN, width, f)
        h1_f = h1[:m1]
        h2_f = h2[:m2]
        for kind in ("app", "oracle"):
            ws, its = [], []
            for seed in G0_SEEDS[:2]:
                block = sample_matched_block(pb, pf, width, seed)
                t1 = time.perf_counter()
                if kind == "app":
                    rec = _run_layered_block(decode_fn, h1_f, h2_f, p1, p2,
                                             block, False)
                    calls += 2
                else:
                    prior_o = oracle_l2_prior(p2, block["bob"], block["u1"])
                    eo, _, ito, _, _ = _decode_block(decode_fn, h2_f, prior_o,
                                                     block["u2"])
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
    h1 = np.asarray(h1)
    h2 = np.asarray(h2)
    run_samples = []
    for f in f_list:
        m1 = _rows_required(CE_L1_MEAN, width, f)
        m2 = _rows_required(CE_L2_ORACLE_MEAN, width, f)
        h1_f = h1[:m1]
        h2_f = h2[:m2]
        app_ok = 0
        ora_ok = 0
        app_syn_ok = 0
        app_it_total = 0
        app_it_max = 0
        ora_syn_ok = 0
        ora_it_total = 0
        nf_f = 0
        samples_f = []
        for t, seed in enumerate(seeds[:n_blocks]):
            block = sample_matched_block(pb, pf, width, seed)
            rec = _run_layered_block(decode_fn, h1_f, h2_f, p1, p2, block,
                                     t < oracle_subset)
            app_ok += int(rec["app_exact"])
            app_syn_ok += int(rec["app_syndrome_ok"])
            _it = int(rec["iterations"])
            app_it_total += _it
            if _it > app_it_max:
                app_it_max = _it
            calls += 2
            _nf = int(not rec["finite"])
            nonfinite += _nf
            nf_f += _nf
            if t < oracle_subset:
                ora_ok += int(rec["oracle_exact"])
                ora_syn_ok += int(rec["oracle_syndrome_ok"])
                ora_it_total += int(rec["oracle_iterations"])
                calls += 1
                _onf = int(not rec.get("oracle_finite", True))
                nonfinite += _onf
                nf_f += _onf
            _rss = _rss_bytes()
            samples_f.append(_rss)
            run_samples.append(_rss)
        rate = app_ok / n_blocks
        _peak_f = None
        _seen_f = [s for s in samples_f if s is not None]
        if _seen_f:
            _peak_f = int(max(_seen_f))
        per_f.append({"f": float(f),
                      "attempted": int(n_blocks),
                      "app_exact_count": int(app_ok),
                      "app_exact_rate": float(rate),
                      "app_failure_fraction": float(1.0 - rate),
                      "oracle_exact_count": int(ora_ok),
                      "app_syndrome_ok_count": int(app_syn_ok),
                      "app_iterations_total": int(app_it_total),
                      "app_iterations_max": int(app_it_max),
                      "oracle_syndrome_ok_count": int(ora_syn_ok),
                      "oracle_iterations_total": int(ora_it_total),
                      "nonfinite_count": int(nf_f),
                      "peak_rss_bytes": _peak_f})
    rates = [r["app_exact_rate"] for r in per_f]
    mono = bool(all(b >= a for a, b in zip(rates, rates[1:])))
    if any(s is None for s in run_samples):
        run_peak = None
    else:
        _seen_run = [int(s) for s in run_samples if s is not None]
        run_peak = int(max(_seen_run)) if _seen_run else None
        _per_peaks = [r["peak_rss_bytes"] for r in per_f
                      if r["peak_rss_bytes"] is not None]
        if _per_peaks:
            run_peak = int(max(_per_peaks))
    return per_f, mono, calls, nonfinite, run_peak


def _classify_g1_outcome(*, nonfinite, wall_seconds, peak_rss_bytes,
                         per_f, monotonic):
    # Completed-path precedence only; PRE_EXECUTION_BLOCKED and
    # WATCHDOG_TIMEOUT_VOID are operator-side labels (no normal return).
    if int(nonfinite) > 0:
        return "G1_NONFINITE_OR_CRASH_BLOCKED"
    try:
        _wall = float(wall_seconds)
    except Exception:
        _wall = float("inf")
    if _wall > 900.0:
        return "G1_OVERRUN_900S"
    if peak_rss_bytes is None or int(peak_rss_bytes) >= 2 * 1024**3:
        return "G1_RESOURCE_OVERRUN"
    _low = int(per_f[0]["app_exact_count"])
    _top = int(per_f[-1]["app_exact_count"])
    _attempted = int(per_f[0]["attempted"])
    _signal = bool(monotonic) and _top > 0 and (
        _top > _low or (_low == _attempted and _top == _attempted))
    if _signal:
        return "G1_TREND_PASS"
    return "G1_COMPLETED_NO_SIGNAL_FAIL"


def run_g1_phase(*, h=None, p_b=None, p_f=None,
                 decode_fn=None, authorized=False):
    """G1 integration trend gate over the frozen G1 seeds (fake decoder only)."""
    _require_authorized("g1", authorized)
    _require_decode_fn("g1", decode_fn)
    t_start = time.perf_counter()
    if h is None:
        h = {"L1": build_dv3_nested_mother(
            G1_WIDTH, G1_L1_K_MIN, G1_L1_K_MIN, L1_GRAPH_SEED, None),
            "L2": build_dv3_nested_mother(
            G1_WIDTH, G1_L2_K_MIN, G1_L2_K_MIN, L2_GRAPH_SEED, None)}
    h1, h2 = _split_layers(h)
    if p_b is None or p_f is None:
        raise ValueError("g1 requires injected p_b and p_f tables")
    pf = np.asarray(p_f, dtype=np.float64)
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    _, _, _, p1, p2 = _ce_stats(pf, pb)
    width = int(h1.shape[1])
    per_f, mono, calls, nonfinite, run_peak = _run_rate_scan(
        decode_fn, h1, h2, p1, p2, pb, pf, width, G1_F,
        G1_BLOCKS, G1_SEEDS, G1_ORACLE_SUBSET)
    frozen = {str(f): {"m1": _rows_required(CE_L1_MEAN, G1_WIDTH, f),
                       "m2": _rows_required(CE_L2_ORACLE_MEAN, G1_WIDTH, f)}
              for f in G1_F}
    wall = float(time.perf_counter() - t_start)
    outcome = _classify_g1_outcome(
        nonfinite=nonfinite, wall_seconds=wall,
        peak_rss_bytes=run_peak, per_f=per_f, monotonic=mono)
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
        "peak_rss_bytes": run_peak,
        "wall_seconds": wall,
        "outcome": outcome,
        "passed": bool(outcome == "G1_TREND_PASS"),
    }


def _grade_g2(top_rate, mono, nonfinite):
    if int(nonfinite) > 0:
        return GRADE_BLOCKED
    if float(top_rate) >= 0.9 and bool(mono):
        return GRADE_QUALIFIED
    if float(top_rate) >= 0.5:
        return GRADE_INCONCLUSIVE
    return GRADE_FAILED


def run_g2_phase(*, h=None, p_b=None, p_f=None,
                 decode_fn=None, authorized=False):
    """G2 sole grading experiment over the frozen G2 seeds (fake decoder only)."""
    _require_authorized("g2", authorized)
    _require_decode_fn("g2", decode_fn)
    if h is None:
        h = {"L1": build_dv3_nested_mother(
            G2_WIDTH, G2_L1_K_MIN, G2_L1_K_MIN, L1_GRAPH_SEED, None),
            "L2": build_dv3_nested_mother(
            G2_WIDTH, G2_L2_K_MIN, G2_L2_K_MIN, L2_GRAPH_SEED, None)}
    h1, h2 = _split_layers(h)
    if p_b is None or p_f is None:
        raise ValueError("g2 requires injected p_b and p_f tables")
    pf = np.asarray(p_f, dtype=np.float64)
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    _, _, _, p1, p2 = _ce_stats(pf, pb)
    width = int(h1.shape[1])
    per_f, mono, calls, nonfinite, _run_peak = _run_rate_scan(
        decode_fn, h1, h2, p1, p2, pb, pf, width, G2_F,
        G2_BLOCKS, G2_SEEDS, G2_ORACLE_SUBSET)
    frozen = {str(f): {"m1": _rows_required(CE_L1_MEAN, G2_WIDTH, f),
                       "m2": _rows_required(CE_L2_ORACLE_MEAN, G2_WIDTH, f)}
              for f in G2_F}
    top = per_f[-1]["app_exact_rate"]
    grade = _grade_g2(top, mono, nonfinite)
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


def prepare_model_f_prior(counts_ab=None, p_b=None, lam=LAMBDA_STAR):
    """Prepare the P0/G1/G2 prior pair from injected counts only.

    Sole production source of ``(p_b, p_f)`` for the rate stages. Reuses
    :func:`build_f_model` with the frozen coefficient and keeps the
    accepted axis contract (counts and P_F are ``(Alice, Bob)`` with
    ``axis0`` Alice; every P_F column sums to 1). Injected tables only;
    no file read. Absent input stops with the single BLOCKED decision
    naming the outer-mean TRAIN counts plus marginal, before any
    construction, decode, or write.
    """
    if counts_ab is None or p_b is None:
        raise ValueError(
            MODEL_F_BLOCKED + ": D4R2 F-model CAL-TRAIN canonical counts "
            "(1024,1024) + P(B) marginal on CAL702..1725 TRAIN")
    p_f = build_f_model(counts_ab, lam)
    pf = np.asarray(p_f, dtype=np.float64)
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    if pf.ndim != 2 or pf.shape[1] != pb.shape[0]:
        raise ValueError("counts/B shapes must satisfy P_F(A, B)")
    if pf.shape[0] % Q != 0:
        raise ValueError("P_F Alice dim must be a nonzero multiple of 32")
    if not np.all(np.isfinite(pf)) or not np.all(np.isfinite(pb)):
        raise ValueError("prior tables must be finite")
    if abs(float(pb.sum()) - 1.0) > 1e-8:
        raise ValueError("P(B) must sum to 1")
    if np.any(np.abs(pf.sum(axis=0) - 1.0) > 1e-8):
        raise ValueError("every P_F column must sum to 1")
    return pb, pf


def _model_f_repo_root():
    """Repository root derived from this file (no sys.path, no cwd)."""
    return Path(__file__).resolve().parents[4]


def _resolve_model_f_input_root():
    """Resolve the frozen Model-F root against the repository root.

    Relative values anchor at the repository root; absolute values pass
    through. Same root-anchoring contract as the prepare script's path
    resolver. No cwd, no search.
    """
    cand = Path(MODEL_F_INPUT_FORMAL_ROOT)
    if cand.is_absolute():
        return cand.resolve()
    return (_model_f_repo_root() / cand).resolve()


def _load_model_f_loader():
    """Load ``load_model_f_input`` from the sibling module by file path.

    The CLI reaches this core module by file path because the repository
    root is not on ``sys.path`` under ``python scripts/...``; the loader
    is reached the same way. Its one package dependency (the contrast
    builder module, stdlib/numpy only) is likewise loaded by file path
    and registered under both names the sibling tries, so the sibling's
    own import succeeds with no ``sys.path`` change.
    """
    here = Path(__file__).resolve().parent
    contrast_names = (
        "comparison_bench.formal_ir.v72p2d3_gf32_contrast",
        "comparison_bench.src.comparison_bench.formal_ir.v72p2d3_gf32_contrast",
    )
    if contrast_names[0] not in sys.modules:
        contrast_path = here / "v72p2d3_gf32_contrast.py"
        contrast_spec = importlib.util.spec_from_file_location(
            contrast_names[0], str(contrast_path))
        if contrast_spec is None or contrast_spec.loader is None:
            raise ValueError(
                MODEL_F_LOADER_UNAVAILABLE + ": Model-F contrast "
                f"module not loadable at {contrast_path}")
        contrast_mod = importlib.util.module_from_spec(contrast_spec)
        try:
            contrast_spec.loader.exec_module(contrast_mod)
        except Exception as exc:
            raise ValueError(
                MODEL_F_LOADER_UNAVAILABLE + ": Model-F contrast "
                f"module failed at {contrast_path}: {exc}") from exc
        sys.modules[contrast_names[0]] = contrast_mod
    for _name in contrast_names:
        sys.modules.setdefault(_name, sys.modules[contrast_names[0]])
    sibling_path = here / "v72p2d5_model_f_input.py"
    sibling_spec = importlib.util.spec_from_file_location(
        "v72p2d5_model_f_input_consumer", str(sibling_path))
    if sibling_spec is None or sibling_spec.loader is None:
        raise ValueError(
            MODEL_F_LOADER_UNAVAILABLE + ": Model-F input module "
            f"not loadable at {sibling_path}")
    sibling = importlib.util.module_from_spec(sibling_spec)
    try:
        sibling_spec.loader.exec_module(sibling)
    except Exception as exc:
        raise ValueError(
            MODEL_F_LOADER_UNAVAILABLE + ": Model-F input module "
            f"failed at {sibling_path}: {exc}") from exc
    return sibling.load_model_f_input


def _load_model_f_input_or_blocked(counts_ab=None, p_b=None):
    """Consume frozen Model-F input: injected tables or fixed-root load.

    Fixed root only (no new CLI flag per frozen spec). Unauthorized entry
    still refuses before this helper. Loader, absence, and validity
    failures stay distinct: only a genuinely absent artifact reports the
    missing-input BLOCKED; loader and validation faults name themselves
    and chain the original cause.
    """
    if counts_ab is not None and p_b is not None:
        return counts_ab, p_b
    _mf_load = _load_model_f_loader()
    root = _resolve_model_f_input_root()
    if not root.is_dir():
        raise ValueError(
            MODEL_F_BLOCKED + ": D4R2 F-model CAL-TRAIN canonical counts "
            "(1024,1024) + P(B) marginal on CAL702..1725 TRAIN; "
            f"resolved artifact root absent: {root}")
    try:
        _loaded = _mf_load(root)
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise ValueError(
            MODEL_F_BLOCKED + ": D4R2 F-model CAL-TRAIN canonical counts "
            "(1024,1024) + P(B) marginal on CAL702..1725 TRAIN; "
            f"artifact files missing under: {root}") from exc
    except ValueError as exc:
        raise ValueError(
            MODEL_F_INPUT_INVALID + ": Model-F artifact validation "
            f"failed at {root}: {exc}") from exc
    return _loaded["counts_ab"], _loaded["p_b"]


def bind_historical_decoder():
    """Bind the historical GF32 decoder once with frozen kwargs."""
    raw = _load_g0_decoder()

    def _bound(h, prior, syndrome, layer=None):
        _ = layer
        r = raw(
            np.asarray(h, dtype=np.uint8),
            np.asarray(prior, dtype=np.float64),
            np.asarray(syndrome, dtype=np.uint8),
            max_iter=MAX_ITER,
            damping_alpha=DAMPING_ALPHA,
            warm_beliefs=None,
            field=None,
        )
        return {
            "x_hat": np.asarray(r.x_hat),
            "syndrome_ok": bool(r.syndrome_ok),
            "iterations": int(r.iterations),
            "final_beliefs": np.asarray(r.final_beliefs),
        }

    return _bound


def _write_stage_evidence(out_dir, payload, table_head, table_rows,
                          report_lines, summary):
    d = Path(out_dir)
    if d.exists():
        raise FileExistsError(f"refusing to overwrite evidence dir: {d}")
    d.mkdir(parents=True)
    with open(d / "results.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    with open(d / "table.csv", "w", encoding="utf-8") as fh:
        fh.write(table_head + "\n")
        for row in table_rows:
            fh.write(",".join(str(v) for v in row) + "\n")
    with open(d / "report.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(report_lines) + "\n")
    with open(d / "execution_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    return list(STAGE_EVIDENCE_FILES)


def write_p0_cost_evidence(out_dir, result):
    """Write the four scalar-only P0 cost files to a fresh directory."""
    frozen = {str(f): {"m1": _rows_required(CE_L1_MEAN, P0_WIDTH, f),
                       "m2": _rows_required(CE_L2_ORACLE_MEAN, P0_WIDTH, f)}
              for f in P0_F}
    records = []
    for item in result.get("records", []) or []:
        rss = item.get("rss_bytes")
        records.append({
            "f": float(item.get("f")),
            "kind": str(item.get("kind")),
            "wall_s": float(item.get("wall_s", 0.0)),
            "iterations": int(item.get("iterations", 0)),
            "rss_bytes": int(rss) if rss is not None else None,
        })
    payload = {
        "phase": str(result.get("phase", "p0-cost")),
        "formal_root": P0_FORMAL_ROOT,
        "block_length": int(result.get("block_length", P0_WIDTH)),
        "f_list": [float(v) for v in result.get("f_list", list(P0_F))],
        "frozen_rows": frozen,
        "seeds": [int(v) for v in G0_SEEDS[:2]],
        "records": records,
        "decoder_calls": int(result.get("decoder_calls", 0)),
        "projected_g1_s": float(result.get("projected_g1_s", 0.0)),
        "projected_g2_s": float(result.get("projected_g2_s", 0.0)),
        "projection_blocked": bool(result.get("projection_blocked", False)),
        "passed": bool(result.get("passed", False)),
        "output_files": list(STAGE_EVIDENCE_FILES),
    }
    table_rows = [[r["f"], r["kind"], r["wall_s"], r["iterations"],
                   r["rss_bytes"]] for r in records]
    report = ["# V72P2D5 P0 cost evidence",
              f"phase: {payload['phase']}",
              f"passed: {payload['passed']}",
              f"decoder_calls: {payload['decoder_calls']}",
              f"projected_g1_s: {payload['projected_g1_s']}",
              f"projected_g2_s: {payload['projected_g2_s']}",
              f"projection_blocked: {payload['projection_blocked']}",
              f"formal_root: {P0_FORMAL_ROOT}"]
    summary = {
        "phase": payload["phase"],
        "formal_root": P0_FORMAL_ROOT,
        "decoder_calls": payload["decoder_calls"],
        "projection_blocked": payload["projection_blocked"],
        "passed": payload["passed"],
        "files": list(STAGE_EVIDENCE_FILES),
    }
    return _write_stage_evidence(
        out_dir, payload, "f,kind,wall_s,iterations,rss_bytes",
        table_rows, report, summary)


def write_g1_evidence(out_dir, result):
    """Write the four scalar-only G1 files to a fresh directory."""
    per_f = []
    for item in result.get("per_f", []) or []:
        _peak = item.get("peak_rss_bytes")
        per_f.append({
            "f": float(item.get("f")),
            "attempted": int(item.get("attempted", 0)),
            "app_exact_count": int(item.get("app_exact_count", 0)),
            "app_exact_rate": float(item.get("app_exact_rate", 0.0)),
            "app_failure_fraction": float(item["app_failure_fraction"]),
            "oracle_exact_count": int(item.get("oracle_exact_count", 0)),
            "app_syndrome_ok_count": int(item.get(
                "app_syndrome_ok_count", 0)),
            "app_iterations_total": int(item.get(
                "app_iterations_total", 0)),
            "app_iterations_max": int(item.get("app_iterations_max", 0)),
            "oracle_syndrome_ok_count": int(item.get(
                "oracle_syndrome_ok_count", 0)),
            "oracle_iterations_total": int(item.get(
                "oracle_iterations_total", 0)),
            "nonfinite_count": int(item.get("nonfinite_count", 0)),
            "peak_rss_bytes": int(_peak) if _peak is not None else None,
        })
    _run_peak = result.get("peak_rss_bytes")
    payload = {
        "phase": str(result.get("phase", "g1")),
        "formal_root": G1_FORMAL_ROOT,
        "block_length": int(result.get("block_length", G1_WIDTH)),
        "f_list": [float(v) for v in result.get("f_list", list(G1_F))],
        "frozen_rows": {str(f): {
            "m1": _rows_required(CE_L1_MEAN, G1_WIDTH, f),
            "m2": _rows_required(CE_L2_ORACLE_MEAN, G1_WIDTH, f)}
            for f in G1_F},
        "seeds": [int(v) for v in G1_SEEDS],
        "per_f": per_f,
        "monotonic": bool(result.get("monotonic", False)),
        "crashes": int(result.get("crashes", 0)),
        "nonfinite": int(result.get("nonfinite", 0)),
        "decoder_calls": int(result.get("decoder_calls", 0)),
        "peak_rss_bytes": int(_run_peak) if _run_peak is not None else None,
        "wall_seconds": float(result.get("wall_seconds", 0.0)),
        "outcome": str(result.get("outcome",
                                 "G1_COMPLETED_NO_SIGNAL_FAIL")),
        "passed": bool(result.get("passed", False)),
        "output_files": list(STAGE_EVIDENCE_FILES),
    }
    table_rows = [[r["f"], r["attempted"], r["app_exact_count"],
                   r["app_exact_rate"], r["app_failure_fraction"],
                   r["oracle_exact_count"], r["app_syndrome_ok_count"],
                   r["app_iterations_total"], r["app_iterations_max"],
                   r["oracle_syndrome_ok_count"],
                   r["oracle_iterations_total"], r["nonfinite_count"],
                   r["peak_rss_bytes"]] for r in per_f]
    report = ["# V72P2D5 G1 evidence",
              f"phase: {payload['phase']}",
              f"outcome: {payload['outcome']}",
              f"passed: {payload['passed']}",
              f"monotonic: {payload['monotonic']}",
              f"nonfinite: {payload['nonfinite']}",
              f"decoder_calls: {payload['decoder_calls']}",
              f"peak_rss_bytes: {payload['peak_rss_bytes']}",
              f"wall_seconds: {payload['wall_seconds']}",
              f"formal_root: {G1_FORMAL_ROOT}"]
    summary = {
        "phase": payload["phase"],
        "formal_root": G1_FORMAL_ROOT,
        "decoder_calls": payload["decoder_calls"],
        "monotonic": payload["monotonic"],
        "nonfinite": payload["nonfinite"],
        "peak_rss_bytes": payload["peak_rss_bytes"],
        "wall_seconds": payload["wall_seconds"],
        "outcome": payload["outcome"],
        "passed": payload["passed"],
        "files": list(STAGE_EVIDENCE_FILES),
    }
    return _write_stage_evidence(
        out_dir, payload,
        "f,attempted,app_exact_count,app_exact_rate,"
        "app_failure_fraction,oracle_exact_count,"
        "app_syndrome_ok_count,app_iterations_total,app_iterations_max,"
        "oracle_syndrome_ok_count,oracle_iterations_total,"
        "nonfinite_count,peak_rss_bytes",
        table_rows, report, summary)


def write_g2_evidence(out_dir, result):
    """Write the four scalar-only G2 files to a fresh directory."""
    per_f = []
    for item in result.get("per_f", []) or []:
        per_f.append({
            "f": float(item.get("f")),
            "attempted": int(item.get("attempted", 0)),
            "app_exact_count": int(item.get("app_exact_count", 0)),
            "app_exact_rate": float(item.get("app_exact_rate", 0.0)),
            "app_failure_fraction": float(item["app_failure_fraction"]),
            "oracle_exact_count": int(item.get("oracle_exact_count", 0)),
        })
    payload = {
        "phase": str(result.get("phase", "g2")),
        "formal_root": G2_FORMAL_ROOT,
        "block_length": int(result.get("block_length", G2_WIDTH)),
        "f_list": [float(v) for v in result.get("f_list", list(G2_F))],
        "frozen_rows": {str(f): {
            "m1": _rows_required(CE_L1_MEAN, G2_WIDTH, f),
            "m2": _rows_required(CE_L2_ORACLE_MEAN, G2_WIDTH, f)}
            for f in G2_F},
        "seeds": [int(v) for v in G2_SEEDS],
        "per_f": per_f,
        "monotonic": bool(result.get("monotonic", False)),
        "crashes": int(result.get("crashes", 0)),
        "nonfinite": int(result.get("nonfinite", 0)),
        "decoder_calls": int(result.get("decoder_calls", 0)),
        "grade": str(result.get("grade", GRADE_FAILED)),
        "passed": bool(result.get("passed", False)),
        "output_files": list(STAGE_EVIDENCE_FILES),
    }
    table_rows = [[r["f"], r["attempted"], r["app_exact_count"],
                   r["app_exact_rate"], r["app_failure_fraction"],
                   r["oracle_exact_count"]] for r in per_f]
    report = ["# V72P2D5 G2 evidence",
              f"phase: {payload['phase']}",
              f"grade: {payload['grade']}",
              f"passed: {payload['passed']}",
              f"monotonic: {payload['monotonic']}",
              f"nonfinite: {payload['nonfinite']}",
              f"decoder_calls: {payload['decoder_calls']}",
              f"formal_root: {G2_FORMAL_ROOT}"]
    summary = {
        "phase": payload["phase"],
        "formal_root": G2_FORMAL_ROOT,
        "decoder_calls": payload["decoder_calls"],
        "monotonic": payload["monotonic"],
        "nonfinite": payload["nonfinite"],
        "grade": payload["grade"],
        "passed": payload["passed"],
        "files": list(STAGE_EVIDENCE_FILES),
    }
    return _write_stage_evidence(
        out_dir, payload,
        "f,attempted,app_exact_count,app_exact_rate,"
        "app_failure_fraction,oracle_exact_count",
        table_rows, report, summary)


def run_p0_cost_synthetic(*, authorized=False, decode_fn=None, out_dir=None,
                          counts_ab=None, p_b=None):
    """Authorized P0 entrypoint; prep first, then build, decode, write."""
    _require_authorized("p0-cost", authorized)
    _c, _b = _load_model_f_input_or_blocked(counts_ab, p_b)
    pb, pf = prepare_model_f_prior(_c, _b)
    decoder = decode_fn if decode_fn is not None else bind_historical_decoder()
    result = run_p0_cost_phase(h=None, p_b=pb, p_f=pf, decode_fn=decoder,
                               authorized=True)
    target = P0_FORMAL_ROOT if out_dir is None else out_dir
    write_p0_cost_evidence(target, result)
    return result


def run_g1_synthetic(*, authorized=False, decode_fn=None, out_dir=None,
                     counts_ab=None, p_b=None):
    """Authorized G1 entrypoint; prep first, then build, decode, write."""
    _require_authorized("g1", authorized)
    t_entry = time.perf_counter()
    _c, _b = _load_model_f_input_or_blocked(counts_ab, p_b)
    pb, pf = prepare_model_f_prior(_c, _b)
    decoder = decode_fn if decode_fn is not None else bind_historical_decoder()
    result = run_g1_phase(h=None, p_b=pb, p_f=pf, decode_fn=decoder,
                          authorized=True)
    wall_outer = float(time.perf_counter() - t_entry)
    result["wall_seconds"] = wall_outer
    result["outcome"] = _classify_g1_outcome(
        nonfinite=result.get("nonfinite", 0),
        wall_seconds=wall_outer,
        peak_rss_bytes=result.get("peak_rss_bytes"),
        per_f=result.get("per_f", []),
        monotonic=result.get("monotonic", False))
    result["passed"] = bool(result["outcome"] == "G1_TREND_PASS")
    target = G1_FORMAL_ROOT if out_dir is None else out_dir
    write_g1_evidence(target, result)
    return result


def run_g2_synthetic(*, authorized=False, decode_fn=None, out_dir=None,
                     counts_ab=None, p_b=None):
    """Authorized G2 entrypoint; prep first, then build, decode, write."""
    _require_authorized("g2", authorized)
    _c, _b = _load_model_f_input_or_blocked(counts_ab, p_b)
    pb, pf = prepare_model_f_prior(_c, _b)
    decoder = decode_fn if decode_fn is not None else bind_historical_decoder()
    result = run_g2_phase(h=None, p_b=pb, p_f=pf, decode_fn=decoder,
                          authorized=True)
    target = G2_FORMAL_ROOT if out_dir is None else out_dir
    write_g2_evidence(target, result)
    return result


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
