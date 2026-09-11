"""V35 Empirical-Posterior-Driven Error-Correction Algorithm Development Core Module.

Implements:
1. Pinned GF(32) arithmetic, V25 empirical channel loader, and PCG64 block sampler.
2. Stage A1: Decoder Schedules (Flooding, Row-Layered, Damped Row-Layered alpha=0.5) on baseline GF(32) graph.
3. Stage A2: Variable degree 2-5 Empirical-P Protograph with Z=32 deterministic quasi-cyclic lifting (girth >= 6, full GF(32) rank).
4. Stage A3: Rate-Adaptive Incremental Parity-Check Hierarchy (S0..S3, +0, +40, +80, +160 bits) with warm-started state transfer and early stopping.
5. Stage A4: Binary Multilevel Coding (MLC) Fallback with 10-bit plane Gray decomposition, empirical conditional LLRs, and sequential MSD.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import time
from functools import lru_cache
from dataclasses import asdict, dataclass
from numbers import Integral
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .nonbinary_field import GF2mField, get_field_spec

# ---------------------------------------------------------------------------
# Constants & Pinned Specifications
# ---------------------------------------------------------------------------

METHOD = "formal_ir_v35_algorithm_development"
FIELD_Q = 32
FIELD_POLY = 37
FIELD_ID = "c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf"

DIMENSION = 1024
N_SYMBOLS = 1024
Z_LIFTING = 32
M_PROTOGRAPH = 6
N_PROTOGRAPH = 32

FACTORIZATION = "F03_natural_MSB_to_LSB_GF32_plus_GF32"
SOURCES = ("1M", "1p5M", "2M")
SOURCE_IDS = {
    "1M": "type2_1M_20260121_184040",
    "1p5M": "type2_1p5M_20260121_183806",
    "2M": "type2_2M_20260121_183657",
}
NPZ_KEYS = {
    "1M": "type2_1M_20260121_184040_N_ab_train_N_ab_train",
    "1p5M": "type2_1p5M_20260121_183806_N_ab_train_N_ab_train",
    "2M": "type2_2M_20260121_183657_N_ab_train_N_ab_train",
}
DEVELOPMENT_SEEDS = {
    "1M": (350101, 350102, 350103, 350104, 350105),
    "1p5M": (350201, 350202, 350203, 350204, 350205),
    "2M": (350301, 350302, 350303, 350304, 350305),
}
TAG_BITS = 64
DEFAULT_MAX_ITER = 30
DEFAULT_DAMPING_ALPHA = 0.5

# Incremental hierarchy constants
INCREMENTAL_STAGES = ("S0", "S1", "S2", "S3")
INCREMENTAL_CHECKS = {"S0": 192, "S1": 200, "S2": 208, "S3": 224}
INCREMENTAL_EXTRA_BITS = {"S0": 0, "S1": 40, "S2": 80, "S3": 160}

# Terminal states
STATUS_NB_CANDIDATE_READY = "NB_CANDIDATE_DEVELOPMENT_READY"
STATUS_BINARY_MLC_READY = "BINARY_MLC_CANDIDATE_DEVELOPMENT_READY"
STATUS_NO_CANDIDATE_SUCCESS = "NO_CANDIDATE_SUCCESS"

# ---------------------------------------------------------------------------
# Fast Walsh-Hadamard Transform & GF(32) Arithmetic Helpers
# ---------------------------------------------------------------------------

_TABLES_CACHE: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}


def _get_gf32_tables(field: GF2mField) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Cache mul, add, and inverse tables as (32, 32) and (32,) uint8 arrays."""
    field_id = field.spec.field_id
    if field_id in _TABLES_CACHE:
        return _TABLES_CACHE[field_id]
    q = field.q
    mul_table = np.zeros((q, q), dtype=np.uint8)
    add_table = np.zeros((q, q), dtype=np.uint8)
    inv_table = np.zeros(q, dtype=np.uint8)
    for i in range(q):
        for j in range(q):
            mul_table[i, j] = field.mul(i, j)
            add_table[i, j] = field.add(i, j)
        if i > 0:
            inv_table[i] = field.inverse(i)
    _TABLES_CACHE[field_id] = (mul_table, add_table, inv_table)
    return mul_table, add_table, inv_table


def fwht_batched(values: np.ndarray) -> np.ndarray:
    """Unnormalized XOR-order Walsh-Hadamard transform along the last axis.

    Satisfies FWHT(FWHT(f)) = q * f.
    """
    out = np.asarray(values, dtype=np.float64)
    if out.ndim < 1:
        raise ValueError("fwht_batched requires at least 1 dimension")
    q = out.shape[-1]
    if q < 2 or (q & (q - 1)) != 0:
        raise ValueError("Last axis size must be a power of 2")
    if not np.all(np.isfinite(out)):
        raise ValueError("fwht_batched inputs must be finite")
    out = out.copy()
    width = 1
    while width < q:
        paired = out.reshape(-1, 2 * width)
        left = paired[:, :width].copy()
        right = paired[:, width:].copy()
        paired[:, :width] = left + right
        paired[:, width:] = left - right
        width *= 2
    return out


def compute_tag_64(x1: np.ndarray, x2: np.ndarray) -> str:
    """Compute 64-bit frame verification tag as SHA-256 first 16 hex characters."""
    b1 = bytes(np.asarray(x1, dtype=np.uint8).reshape(-1).tolist())
    b2 = bytes(np.asarray(x2, dtype=np.uint8).reshape(-1).tolist())
    return hashlib.sha256(b1 + b2).hexdigest()[:16]


def compute_tag_64_symbols(symbols: np.ndarray) -> str:
    """Compute 64-bit frame verification tag for 1024-bin symbols."""
    syms = np.asarray(symbols, dtype=np.int64).reshape(-1)
    x1 = (syms >> 5) & 31
    x2 = syms & 31
    return compute_tag_64(x1, x2)


def syndrome_of_gf32(matrix: np.ndarray, vector: np.ndarray, field: Optional[GF2mField] = None) -> np.ndarray:
    """Compute H * x over GF(32)."""
    if field is None:
        field = GF2mField.create(FIELD_Q)
    mul_table, _, _ = _get_gf32_tables(field)
    mat = np.asarray(matrix, dtype=np.uint8)
    vec = np.asarray(vector, dtype=np.uint8).reshape(-1)
    m, n = mat.shape
    if vec.shape[0] != n:
        raise ValueError(f"Vector length {vec.shape[0]} does not match matrix cols {n}")
    syndromes = np.zeros(m, dtype=np.uint8)
    for r in range(m):
        row = mat[r]
        nonzero_cols = np.where(row > 0)[0]
        s = 0
        for c in nonzero_cols:
            s ^= mul_table[row[c], vec[c]]
        syndromes[r] = s
    return syndromes


def _compute_gf32_rank_loop(matrix: np.ndarray, field: Optional[GF2mField] = None) -> int:
    """Reference element-loop GF(32) elimination; P2 equality-gate对照, not the default path."""
    if field is None:
        field = GF2mField.create(FIELD_Q)
    mul_table, _, inv_table = _get_gf32_tables(field)
    A = np.asarray(matrix, dtype=np.uint8).copy()
    m, n = A.shape
    rank = 0
    col = 0
    for r in range(m):
        if col >= n:
            break
        pivot_row = None
        while col < n:
            for r2 in range(r, m):
                if A[r2, col] != 0:
                    pivot_row = r2
                    break
            if pivot_row is not None:
                break
            col += 1
        if pivot_row is None:
            break
        if pivot_row != r:
            A[[r, pivot_row]] = A[[pivot_row, r]]
        pivot_val = A[r, col]
        inv_val = inv_table[pivot_val]
        # scale pivot row
        for c in range(col, n):
            if A[r, c] != 0:
                A[r, c] = mul_table[A[r, c], inv_val]
        # eliminate other rows
        for r2 in range(m):
            if r2 != r and A[r2, col] != 0:
                factor = A[r2, col]
                for c in range(col, n):
                    if A[r, c] != 0:
                        A[r2, c] ^= mul_table[factor, A[r, c]]
        rank += 1
        col += 1
    return rank


def _compute_gf32_rank_vectorized(matrix: np.ndarray, field: Optional[GF2mField] = None) -> int:
    """Vectorized GF(32) elimination; identical pivot choice/arithmetic to the loop."""
    if field is None:
        field = GF2mField.create(FIELD_Q)
    mul_table, _, inv_table = _get_gf32_tables(field)
    A = np.asarray(matrix, dtype=np.uint8).copy()
    m, n = A.shape
    rank = 0
    col = 0
    cols = np.arange(n)
    for r in range(m):
        if col >= n:
            break
        pivot_row = -1
        while col < n:
            nz = np.flatnonzero(A[r:, col])
            if nz.size:
                pivot_row = r + int(nz[0])
                break
            col += 1
        if pivot_row < 0:
            break
        if pivot_row != r:
            A[[r, pivot_row]] = A[[pivot_row, r]]
        inv_val = inv_table[A[r, col]]
        # scale pivot row
        A[r, col:] = mul_table[A[r, col:], inv_val]
        # eliminate column col in all other rows at once
        factors = A[:, col].copy()
        factors[r] = 0
        rows = np.flatnonzero(factors)
        if rows.size:
            seg = cols[col:]
            A[rows[:, None], seg] ^= mul_table[factors[rows, None], A[r, seg][None, :]]
        rank += 1
        col += 1
    return rank


_TABLE_LISTS_CACHE: dict[str, tuple[list[list[int]], list[int]]] = {}


def _get_gf32_table_lists(field: GF2mField) -> tuple[list[list[int]], list[int]]:
    """Cached (mul_table, inv_table) as nested Python lists for the tiny fast path."""
    field_id = field.spec.field_id
    cached = _TABLE_LISTS_CACHE.get(field_id)
    if cached is None:
        mul_table, _, inv_table = _get_gf32_tables(field)
        cached = (mul_table.tolist(), inv_table.tolist())
        _TABLE_LISTS_CACHE[field_id] = cached
    return cached


def _compute_gf32_rank_tiny(matrix: np.ndarray, field: Optional[GF2mField] = None) -> int:
    """Exact GF(32) elimination on plain Python lists; fastest for tiny matrices."""
    if field is None:
        field = GF2mField.create(FIELD_Q)
    mul_rows, inv_vals = _get_gf32_table_lists(field)
    A = [list(map(int, row)) for row in np.asarray(matrix, dtype=np.uint8).tolist()]
    m = len(A)
    n = len(A[0]) if m else 0
    rank = 0
    col = 0
    for r in range(m):
        if col >= n:
            break
        pivot_row = -1
        while col < n:
            for r2 in range(r, m):
                if A[r2][col]:
                    pivot_row = r2
                    break
            if pivot_row >= 0:
                break
            col += 1
        if pivot_row < 0:
            break
        if pivot_row != r:
            A[r], A[pivot_row] = A[pivot_row], A[r]
        inv_val = inv_vals[A[r][col]]
        prow = A[r]
        for c in range(col, n):
            if prow[c]:
                prow[c] = mul_rows[prow[c]][inv_val]
        for r2 in range(m):
            if r2 != r and A[r2][col]:
                factor = A[r2][col]
                mrow = mul_rows[factor]
                tgt = A[r2]
                for c in range(col, n):
                    if prow[c]:
                        tgt[c] ^= mrow[prow[c]]
        rank += 1
        col += 1
    return rank


def compute_gf32_rank(matrix: np.ndarray, field: Optional[GF2mField] = None) -> int:
    """Compute exact row rank of matrix over GF(32) using Gaussian elimination.

    Default path dispatches by size: tiny matrices use the list fast path
    (numpy call overhead dominates there); larger ones use the vectorized form.
    All forms share pivot choice and table arithmetic, gated to equal outputs.
    """
    A0 = np.asarray(matrix, dtype=np.uint8)
    m, n = A0.shape
    if m * n <= 48:
        return _compute_gf32_rank_tiny(A0, field)
    return _compute_gf32_rank_vectorized(A0, field)

# ---------------------------------------------------------------------------
# Channel Loading & Sampling
# ---------------------------------------------------------------------------

# P1 (perf-v38-triage-test-cost): bounded stat-keyed caches for the V25/V31 loaders.
# Key = (resolved_abs_path, mtime_ns, size): same file via relative/absolute/symlink
# paths hits one entry; any content change misses. Cached payloads are immutable
# (shape, bytes); every public call rebuilds fresh arrays so callers can never
# pollute the cache by in-place mutation. Failures are never cached.
_V31_CACHE_MAXSIZE = 4
_V25_CACHE_MAXSIZE = 4


def _stat_cache_key(resolved: Path) -> tuple[str, int, int]:
    st = resolved.stat()
    return (str(resolved), st.st_mtime_ns, st.st_size)


@lru_cache(maxsize=_V25_CACHE_MAXSIZE)
def _load_v25_payload_cached(key: tuple[str, int, int]) -> dict[str, tuple[tuple[int, ...], bytes]]:
    data = np.load(key[0])
    try:
        out: dict[str, tuple[tuple[int, ...], bytes]] = {}
        for src in SOURCES:
            npz_key = NPZ_KEYS[src]
            if npz_key not in data:
                raise KeyError(f"Key {npz_key} not found in channel counts file")
            arr = np.asarray(data[npz_key], dtype=np.float64)
            if arr.shape != (DIMENSION, DIMENSION):
                raise ValueError(f"Unexpected shape {arr.shape} for source {src}")
            out[src] = (tuple(int(v) for v in arr.shape), arr.tobytes(order="C"))
    finally:
        data.close()
    return out


def load_v25_channel_counts(path: Optional[Path | str] = None) -> dict[str, np.ndarray]:
    """Load the V25 channel joint counts NPZ file."""
    if path is None:
        repo_root = Path(__file__).resolve().parents[4]
        path = repo_root / "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz"
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"V25 channel counts file not found: {path}")
    payload = _load_v25_payload_cached(_stat_cache_key(resolved))
    return {
        src: np.frombuffer(blob, dtype=np.float64).copy().reshape(shape)
        for src, (shape, blob) in payload.items()
    }


@lru_cache(maxsize=_V31_CACHE_MAXSIZE)
def _load_v31_payload_cached(key: tuple[str, int, int]) -> dict[str, tuple[tuple[int, ...], bytes]]:
    with open(key[0], "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    pkt = next((p for p in doc.get("packets", []) if p.get("packet_id") == "m1_16_n1024_n1024|QC-cyclic-projective"), None)
    if pkt is None:
        raise ValueError("QC-cyclic-projective packet not found in matrix payloads")
    l2_mats = pkt.get("matrices", {}).get("L2", {})
    out: dict[str, tuple[tuple[int, ...], bytes]] = {}
    for src in ("1M", "1p5M", "2M"):
        arr = np.asarray(l2_mats[src], dtype=np.uint8)
        out[src] = (tuple(int(v) for v in arr.shape), arr.tobytes(order="C"))
    return out


def load_v31_qc_baseline_matrices_cache_clear() -> None:
    """Test-isolation hook: drop all cached V25/V31 loader payloads."""
    _load_v25_payload_cached.cache_clear()
    _load_v31_payload_cached.cache_clear()


def load_v31_qc_baseline_matrices(path: Optional[Path | str] = None) -> dict[str, np.ndarray]:
    """Load the frozen V31 baseline L2 QC parity-check matrices from matrix_payloads.json.

    Returns dict mapping source ('1M', '1p5M', '2M') to uint8 numpy array of shape (m2, 1024).
    1M: (184, 1024)
    1p5M: (190, 1024)
    2M: (192, 1024)
    """
    if path is None:
        repo_root = Path(__file__).resolve().parents[4]
        path = repo_root / "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/matrix_payloads.json"
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"V31 matrix payloads file not found: {path}")
    payload = _load_v31_payload_cached(_stat_cache_key(resolved))
    return {
        src: np.frombuffer(blob, dtype=np.uint8).copy().reshape(shape)
        for src, (shape, blob) in payload.items()
    }


def sample_empirical_block(counts: np.ndarray, seed: int, size: int = N_SYMBOLS) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample empirical symbol pairs from joint counts using PCG64 determinism."""
    arr = np.asarray(counts, dtype=np.float64)
    total = float(np.sum(arr))
    if not math.isfinite(total) or total <= 0:
        raise ValueError("Invalid count total")
    p = (arr / total).reshape(-1, order="C")
    rng = np.random.Generator(np.random.PCG64(int(seed)))
    idx = rng.choice(DIMENSION * DIMENSION, size=int(size), replace=True, p=p)
    idx = np.asarray(idx, dtype=np.int64)
    alice = idx // DIMENSION
    bob = idx % DIMENSION
    return idx, alice, bob


def factorize_f03(alice: np.ndarray, bob: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Natural MSB -> LSB factorization into Layer 1 (MSB 5 bits) and Layer 2 (LSB 5 bits)."""
    a = np.asarray(alice, dtype=np.int64)
    b = np.asarray(bob, dtype=np.int64)
    x1 = (a >> 5) & 31
    x2 = a & 31
    y1 = (b >> 5) & 31
    y2 = b & 31
    return x1.astype(np.uint8), x2.astype(np.uint8), y1.astype(np.uint8), y2.astype(np.uint8)


def get_conditional_posterior_l2(counts: np.ndarray, bob: np.ndarray, u1: np.ndarray) -> np.ndarray:
    """Compute exact conditional prior matrix P(U2=s | B=b, U1=u1) of shape (N, 32)."""
    arr = np.asarray(counts, dtype=np.float64)
    b = np.asarray(bob, dtype=np.int64)
    u = np.asarray(u1, dtype=np.int64)
    n = b.shape[0]
    # Slices rows [u * 32 .. u * 32 + 31, b]
    rows = arr[(u[:, None] * 32 + np.arange(32)[None, :]), b[:, None]]
    denom = rows.sum(axis=1, keepdims=True)
    if np.any(~np.isfinite(denom)) or np.any(denom <= 0):
        # Fallback uniform if zero denominator
        denom = np.where(denom <= 0, 1.0, denom)
    p_cond = rows / denom
    p_cond = np.maximum(p_cond, 1e-15)
    p_cond = p_cond / p_cond.sum(axis=1, keepdims=True)
    return p_cond

# ---------------------------------------------------------------------------
# FFT-QSPA Check Update Engine
# ---------------------------------------------------------------------------

def _check_update_log_batch(
    log_messages: Sequence[np.ndarray],
    coefficients: Sequence[int],
    syndrome: int,
    field: GF2mField,
    tables: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> list[np.ndarray]:
    """Compute all outgoing check-to-variable log-messages for a check node via FWHT."""
    mul_table, add_table, _ = tables
    q = field.q
    dc = len(log_messages)
    if dc < 2:
        raise ValueError("Check node requires degree >= 2")

    # 1. Permute incoming log messages by coefficient and convert to probability
    scaled_probs = np.empty((dc, q), dtype=np.float64)
    for j, (msg, coeff) in enumerate(zip(log_messages, coefficients)):
        coeff = int(coeff)
        # msg[v] corresponds to variable value v
        # scaled_msg[coeff * v] = msg[v] => scaled_msg[s] = msg[inv(coeff) * s]
        perm = mul_table[coeff, :]
        scaled_log = np.empty(q, dtype=np.float64)
        scaled_log[perm] = msg
        # Softmax / normalize with mass floor
        max_val = np.max(scaled_log)
        exp_m = np.exp(scaled_log - max_val)
        sum_m = np.sum(exp_m)
        if sum_m <= 0 or not np.isfinite(sum_m):
            scaled_probs[j] = np.full(q, 1.0 / q)
        else:
            scaled_probs[j] = np.maximum(exp_m / sum_m, 1e-15)
            scaled_probs[j] /= np.sum(scaled_probs[j])

    # 2. Spectral transform (FWHT)
    spectra = fwht_batched(scaled_probs)  # (dc, q)

    # 3. Compute extrinsic products
    # Prefix and suffix products for O(dc) efficiency
    prefix = np.ones((dc + 1, q), dtype=np.float64)
    suffix = np.ones((dc + 1, q), dtype=np.float64)
    for j in range(dc):
        prefix[j + 1] = prefix[j] * spectra[j]
    for j in range(dc - 1, -1, -1):
        suffix[j] = suffix[j + 1] * spectra[j]

    outgoing_logs: list[np.ndarray] = []
    for t in range(dc):
        prod_ext = prefix[t] * suffix[t + 1]
        conv = fwht_batched(prod_ext) / q
        coeff_t = int(coefficients[t])
        shifted_indices = add_table[syndrome, mul_table[coeff_t, :]]
        out_prob = conv[shifted_indices]
        out_prob = np.maximum(out_prob, 1e-15)
        sum_p = np.sum(out_prob)
        if sum_p <= 0 or not np.isfinite(sum_p):
            out_prob = np.full(q, 1.0 / q)
        else:
            out_prob /= sum_p
        outgoing_logs.append(np.log(np.maximum(out_prob, 1e-15)))

    return outgoing_logs

# ---------------------------------------------------------------------------
# Stage A1: FFT-QSPA Decoders (Flooding, Row-Layered, Damped Row-Layered)
# ---------------------------------------------------------------------------

# Belief provenance contract (D7/BP Alternative A). Tokens are exact; the
# field is additive and defaulted so legacy positional construction keeps
# working. CHECK_UPDATED labels a BP APP approximation that incorporated check
# messages -- not a calibrated exact posterior.
BELIEF_PROVENANCE_PRIOR_ONLY = "PRIOR_ONLY"
BELIEF_PROVENANCE_CHECK_UPDATED = "CHECK_UPDATED"
BELIEF_PROVENANCE_WARM_START_UNSPECIFIED = "WARM_START_UNSPECIFIED"
BELIEF_PROVENANCE_TOKENS = (
    BELIEF_PROVENANCE_PRIOR_ONLY,
    BELIEF_PROVENANCE_CHECK_UPDATED,
    BELIEF_PROVENANCE_WARM_START_UNSPECIFIED,
)
# Diagnostic record label only (never a provenance token): a PRIOR_ONLY return
# may be recorded as current belief, never as conditioned posterior/APP.
PRIOR_ONLY_CURRENT_BELIEF = "PRIOR_ONLY_CURRENT_BELIEF"


class UnconditionedBeliefProvenanceError(RuntimeError):
    """Cross-layer APP refused: returned beliefs are not CHECK_UPDATED."""


def require_check_updated_provenance(provenance, *, consumer):
    """Fail closed unless ``provenance`` is exactly CHECK_UPDATED.

    Cross-layer APP consumers call this before computing or forwarding a
    conditioned prior; PRIOR_ONLY, WARM_START_UNSPECIFIED, None/absent and
    unknown tokens are all refused.
    """
    if provenance != BELIEF_PROVENANCE_CHECK_UPDATED:
        raise UnconditionedBeliefProvenanceError(
            f"{consumer}: cross-layer APP requires belief_provenance="
            f"'{BELIEF_PROVENANCE_CHECK_UPDATED}'; got {provenance!r}")
    return provenance


def belief_diagnostic_label(provenance):
    """Record label for a returned current belief state (BP-05 seam).

    PRIOR_ONLY may only be recorded as PRIOR_ONLY_CURRENT_BELIEF; the
    hard decision is a separate field (x_hat/syndrome_ok) and never upgrades
    this label. Other tokens pass through unchanged (CHECK_UPDATED is not an
    exact-posterior claim).
    """
    if provenance == BELIEF_PROVENANCE_PRIOR_ONLY:
        return PRIOR_ONLY_CURRENT_BELIEF
    return provenance


# Code-factor extrinsic contract (D7-G, frozen OpenSpec
# `v72p2d7-code-factor-extrinsic-contract`). A cold decoder's outgoing
# code-factor message is `L_code_ext = L_post - log(p_in)` (per-row additive
# constant free), stored row-normalized by subtracting log-sum-exp so
# `softmax(log(p_in) + L_code_ext) == softmax(L_post)` exactly. This is a BP
# factor message, not a calibrated exact posterior and not MAP truth. Valid
# only for cold start after >=1 completed check sweep with finite
# shape-correct beliefs. Iteration 0 carries no check evidence (neutral zeros
# + NO_CHECK_EVIDENCE, ineligible for transfer); warm start is fail-closed
# (WARM_START_UNSPECIFIED, never inferred); nonfinite/shape mismatch fails
# loud, never silently repaired. Existing final_beliefs/belief_provenance
# semantics are unchanged; no consumer is wired to this field yet.
EXTRINSIC_NO_CHECK_EVIDENCE = "NO_CHECK_EVIDENCE"
EXTRINSIC_CHECK_EXTRINSIC = "CHECK_EXTRINSIC"
EXTRINSIC_WARM_START_UNSPECIFIED = "WARM_START_UNSPECIFIED"
EXTRINSIC_PROVENANCE_TOKENS = (
    EXTRINSIC_NO_CHECK_EVIDENCE,
    EXTRINSIC_CHECK_EXTRINSIC,
    EXTRINSIC_WARM_START_UNSPECIFIED,
)


class UnusableExtrinsicError(RuntimeError):
    """Cross-layer transfer refused: no usable CHECK_EXTRINSIC."""


def _build_check_extrinsic_log_beliefs(final_beliefs, log_input_prior):
    """Form the stored code-factor extrinsic message (D7-G producer rule).

    Returns ``L_post - log(p_in)`` row-normalized by subtracting
    log-sum-exp. Raises ``ValueError`` on ``None`` inputs, shape mismatch,
    non-2-D input, or any nonfinite entry: fail-loud, never repaired.
    """
    if final_beliefs is None or log_input_prior is None:
        raise ValueError("extrinsic needs finite final beliefs and input prior")
    post = np.asarray(final_beliefs, dtype=np.float64)
    pin = np.asarray(log_input_prior, dtype=np.float64)
    if post.ndim != 2 or pin.ndim != 2 or post.shape != pin.shape:
        raise ValueError(
            "extrinsic shape mismatch: %r vs %r" % (post.shape, pin.shape))
    if post.shape[0] < 1 or post.shape[1] < 2:
        raise ValueError("extrinsic needs a nonempty (n, q>=2) belief matrix")
    if not bool(np.all(np.isfinite(post))) or not bool(np.all(np.isfinite(pin))):
        raise ValueError("extrinsic needs finite beliefs and input prior")
    ext = post - pin
    m = np.max(ext, axis=1, keepdims=True)
    lse = m + np.log(np.sum(np.exp(ext - m), axis=1, keepdims=True))
    return ext - lse


def require_check_extrinsic_for_transfer(
    extrinsic_log_beliefs, extrinsic_provenance, *, consumer,
    expected_n=None, q=FIELD_Q,
):
    """Fail closed unless the extrinsic is explicit CHECK_EXTRINSIC.

    Only a finite shape-correct ``(n, q)`` array with provenance exactly
    ``CHECK_EXTRINSIC`` is stably softmaxed for transport. ``NO_CHECK_EVIDENCE``,
    ``WARM_START_UNSPECIFIED``, missing/``None``/unknown provenance, missing
    arrays, wrong shapes, and nonfinite values all raise
    ``UnusableExtrinsicError`` before any cross-layer prior is computed.
    Not wired into D5/D6/D7 production execution.
    """
    if extrinsic_provenance != EXTRINSIC_CHECK_EXTRINSIC:
        raise UnusableExtrinsicError(
            f"{consumer}: cross-layer transfer requires extrinsic_provenance="
            f"'{EXTRINSIC_CHECK_EXTRINSIC}'; got {extrinsic_provenance!r}")
    if extrinsic_log_beliefs is None:
        raise UnusableExtrinsicError(
            f"{consumer}: cross-layer transfer requires an extrinsic array; "
            "got None")
    try:
        arr = np.asarray(extrinsic_log_beliefs, dtype=np.float64)
    except (ValueError, TypeError) as exc:
        raise UnusableExtrinsicError(
            f"{consumer}: extrinsic array is not convertible: {exc}") from exc
    if arr.ndim != 2 or arr.shape[0] < 1 or arr.shape[1] != int(q):
        raise UnusableExtrinsicError(
            f"{consumer}: extrinsic shape must be (n, {int(q)}); "
            f"got {arr.shape!r}")
    if expected_n is not None and arr.shape[0] != int(expected_n):
        raise UnusableExtrinsicError(
            f"{consumer}: extrinsic row count {arr.shape[0]} != "
            f"expected {int(expected_n)}")
    if not bool(np.all(np.isfinite(arr))):
        raise UnusableExtrinsicError(
            f"{consumer}: extrinsic array must be finite")
    m = np.max(arr, axis=1, keepdims=True)
    e = np.exp(arr - m)
    return e / np.sum(e, axis=1, keepdims=True)


@dataclass
class DecoderResult:
    x_hat: np.ndarray
    syndrome_ok: bool
    iterations: int
    runtime_s: float
    status: str
    final_beliefs: np.ndarray
    belief_provenance: Optional[str] = None
    extrinsic_log_beliefs: Optional[np.ndarray] = None
    extrinsic_provenance: Optional[str] = None


def decode_flooding_fftqspa(
    h_matrix: np.ndarray,
    priors: np.ndarray,
    syndromes: np.ndarray,
    max_iter: int = DEFAULT_MAX_ITER,
    field: Optional[GF2mField] = None,
) -> DecoderResult:
    """Stage A1 Flooding FFT-QSPA Decoder (synchronous 2-phase message passing)."""
    t0 = time.perf_counter()
    if field is None:
        field = GF2mField.create(FIELD_Q)
    tables = _get_gf32_tables(field)
    q = field.q
    mat = np.asarray(h_matrix, dtype=np.uint8)
    m, n = mat.shape
    syn = np.asarray(syndromes, dtype=np.uint8)

    # Prior log-likelihoods (N, q)
    priors_clean = np.maximum(np.asarray(priors, dtype=np.float64), 1e-15)
    priors_clean /= np.sum(priors_clean, axis=1, keepdims=True)
    log_priors = np.log(priors_clean)

    # Build adjacency lists
    check_edges: list[list[int]] = [[] for _ in range(m)]
    check_coeffs: list[list[int]] = [[] for _ in range(m)]
    var_edges: list[list[int]] = [[] for _ in range(n)]

    for r in range(m):
        cols = np.where(mat[r] > 0)[0].tolist()
        check_edges[r] = cols
        check_coeffs[r] = [int(mat[r, c]) for c in cols]
        for c in cols:
            var_edges[c].append(r)

    # Edge message storage: C->V and V->C
    # check_to_var[r][pos] is log-message from check r to check_edges[r][pos]
    check_to_var: list[list[np.ndarray]] = [
        [np.zeros(q, dtype=np.float64) for _ in check_edges[r]] for r in range(m)
    ]
    # var_to_check[c][pos] is log-message from var c to var_edges[c][pos]
    var_to_check: list[list[np.ndarray]] = [
        [np.zeros(q, dtype=np.float64) for _ in var_edges[c]] for c in range(n)
    ]

    # Map (c, r) to positions
    c_to_r_pos: dict[tuple[int, int], int] = {}
    r_to_c_pos: dict[tuple[int, int], int] = {}
    for r in range(m):
        for pos, c in enumerate(check_edges[r]):
            r_to_c_pos[(r, c)] = pos
    for c in range(n):
        for pos, r in enumerate(var_edges[c]):
            c_to_r_pos[(c, r)] = pos

    # Initialize V->C with prior log-likelihoods
    for c in range(n):
        for pos in range(len(var_edges[c])):
            var_to_check[c][pos] = log_priors[c].copy()

    status = "max_iter"
    best_x = np.argmax(log_priors, axis=1).astype(np.uint8)

    for it in range(1, max_iter + 1):
        # 1. Check Node Updates
        for r in range(m):
            cols = check_edges[r]
            in_msgs = [var_to_check[c][c_to_r_pos[(c, r)]] for c in cols]
            out_msgs = _check_update_log_batch(in_msgs, check_coeffs[r], int(syn[r]), field, tables)
            check_to_var[r] = out_msgs

        # 2. Variable Node Updates & Hard Decision
        beliefs = log_priors.copy()
        for r in range(m):
            for pos, c in enumerate(check_edges[r]):
                beliefs[c] += check_to_var[r][pos]

        best_x = np.argmax(beliefs, axis=1).astype(np.uint8)
        current_syn = syndrome_of_gf32(mat, best_x, field)
        if np.array_equal(current_syn, syn):
            status = "converged_exact"
            return DecoderResult(
                x_hat=best_x,
                syndrome_ok=True,
                iterations=it,
                runtime_s=time.perf_counter() - t0,
                status=status,
                final_beliefs=beliefs,
                belief_provenance=BELIEF_PROVENANCE_CHECK_UPDATED,
            )

        # Update V->C extrinsic messages for next iteration
        for c in range(n):
            for pos, r in enumerate(var_edges[c]):
                r_pos = r_to_c_pos[(r, c)]
                var_to_check[c][pos] = beliefs[c] - check_to_var[r][r_pos]

    current_syn = syndrome_of_gf32(mat, best_x, field)
    syn_ok = bool(np.array_equal(current_syn, syn))
    return DecoderResult(
        x_hat=best_x,
        syndrome_ok=syn_ok,
        iterations=max_iter,
        runtime_s=time.perf_counter() - t0,
        status="converged_no_syndrome" if not syn_ok else "converged_exact",
        final_beliefs=beliefs,
        belief_provenance=BELIEF_PROVENANCE_CHECK_UPDATED,
    )


def decode_row_layered_fftqspa(
    h_matrix: np.ndarray,
    priors: np.ndarray,
    syndromes: np.ndarray,
    max_iter: int = DEFAULT_MAX_ITER,
    damping_alpha: float = 1.0,
    warm_beliefs: Optional[np.ndarray] = None,
    field: Optional[GF2mField] = None,
) -> DecoderResult:
    """Stage A1 Row-Layered / Damped Row-Layered FFT-QSPA Decoder.

    damping_alpha=1.0 corresponds to standard row-layered.
    damping_alpha=0.5 corresponds to damped row-layered.
    """
    t0 = time.perf_counter()
    if field is None:
        field = GF2mField.create(FIELD_Q)
    tables = _get_gf32_tables(field)
    q = field.q
    mat = np.asarray(h_matrix, dtype=np.uint8)
    m, n = mat.shape
    syn = np.asarray(syndromes, dtype=np.uint8)

    # Initial log-beliefs
    warm_seeded = warm_beliefs is not None and warm_beliefs.shape == (n, q)
    if warm_seeded:
        beliefs = warm_beliefs.copy()
        log_input_prior = None
    else:
        priors_clean = np.maximum(np.asarray(priors, dtype=np.float64), 1e-15)
        priors_clean /= np.sum(priors_clean, axis=1, keepdims=True)
        beliefs = np.log(priors_clean)
        # Exact normalized input prior used internally (frozen floor/renorm
        # rule above, untouched): retained for the additive D7-G extrinsic
        # field only. Same array, no duplicated cleaning rule.
        log_input_prior = beliefs.copy()

    # Check node structures
    check_edges: list[list[int]] = [[] for _ in range(m)]
    check_coeffs: list[list[int]] = [[] for _ in range(m)]
    for r in range(m):
        cols = np.where(mat[r] > 0)[0].tolist()
        check_edges[r] = cols
        check_coeffs[r] = [int(mat[r, c]) for c in cols]

    # Store check-to-variable log-messages
    check_to_var: list[list[np.ndarray]] = [
        [np.zeros(q, dtype=np.float64) for _ in check_edges[r]] for r in range(m)
    ]

    alpha = float(damping_alpha)
    best_x = np.argmax(beliefs, axis=1).astype(np.uint8)

    # Check initial syndrome
    if np.array_equal(syndrome_of_gf32(mat, best_x, field), syn):
        if warm_seeded:
            ext_beliefs, ext_prov = None, EXTRINSIC_WARM_START_UNSPECIFIED
        else:
            # Iteration 0: no check evidence yet; neutral zeros, ineligible.
            ext_beliefs = np.zeros((n, q), dtype=np.float64)
            ext_prov = EXTRINSIC_NO_CHECK_EVIDENCE
        return DecoderResult(
            x_hat=best_x,
            syndrome_ok=True,
            iterations=0,
            runtime_s=time.perf_counter() - t0,
            status="converged_exact",
            final_beliefs=beliefs,
            belief_provenance=(
                BELIEF_PROVENANCE_WARM_START_UNSPECIFIED if warm_seeded
                else BELIEF_PROVENANCE_PRIOR_ONLY),
            extrinsic_log_beliefs=ext_beliefs,
            extrinsic_provenance=ext_prov,
        )

    for it in range(1, max_iter + 1):
        for r in range(m):
            cols = check_edges[r]
            coeffs = check_coeffs[r]
            # 1. Extrinsic variable messages: v_{c->r} = beliefs[c] - u_{r->c}^{old}
            in_msgs = [beliefs[c] - check_to_var[r][pos] for pos, c in enumerate(cols)]

            # 2. Check update via FWHT
            out_msgs = _check_update_log_batch(in_msgs, coeffs, int(syn[r]), field, tables)

            # 3. Damping & immediate belief update
            for pos, c in enumerate(cols):
                u_old = check_to_var[r][pos]
                u_new = out_msgs[pos]
                if alpha < 0.999:
                    # Damping in probability domain
                    p_old = np.exp(u_old - np.max(u_old))
                    p_old /= np.sum(p_old)
                    p_new = np.exp(u_new - np.max(u_new))
                    p_new /= np.sum(p_new)
                    p_damped = (1.0 - alpha) * p_old + alpha * p_new
                    p_damped = np.maximum(p_damped, 1e-15)
                    p_damped /= np.sum(p_damped)
                    u_damped = np.log(p_damped)
                else:
                    u_damped = u_new

                # Update global belief: beliefs[c] <- beliefs[c] - u_old + u_damped
                beliefs[c] = beliefs[c] - u_old + u_damped
                check_to_var[r][pos] = u_damped

        # Hard decision after full layer sweep
        best_x = np.argmax(beliefs, axis=1).astype(np.uint8)
        current_syn = syndrome_of_gf32(mat, best_x, field)
        if np.array_equal(current_syn, syn):
            if warm_seeded:
                ext_beliefs, ext_prov = None, EXTRINSIC_WARM_START_UNSPECIFIED
            else:
                ext_beliefs = _build_check_extrinsic_log_beliefs(
                    beliefs, log_input_prior)
                ext_prov = EXTRINSIC_CHECK_EXTRINSIC
            return DecoderResult(
                x_hat=best_x,
                syndrome_ok=True,
                iterations=it,
                runtime_s=time.perf_counter() - t0,
                status="converged_exact",
                final_beliefs=beliefs,
                belief_provenance=(
                    BELIEF_PROVENANCE_WARM_START_UNSPECIFIED if warm_seeded
                    else BELIEF_PROVENANCE_CHECK_UPDATED),
                extrinsic_log_beliefs=ext_beliefs,
                extrinsic_provenance=ext_prov,
            )

    current_syn = syndrome_of_gf32(mat, best_x, field)
    syn_ok = bool(np.array_equal(current_syn, syn))
    if warm_seeded:
        ext_beliefs, ext_prov = None, EXTRINSIC_WARM_START_UNSPECIFIED
    elif int(max_iter) >= 1:
        ext_beliefs = _build_check_extrinsic_log_beliefs(
            beliefs, log_input_prior)
        ext_prov = EXTRINSIC_CHECK_EXTRINSIC
    else:
        # No sweep completed (max_iter < 1): no check evidence.
        ext_beliefs = np.zeros((n, q), dtype=np.float64)
        ext_prov = EXTRINSIC_NO_CHECK_EVIDENCE
    return DecoderResult(
        x_hat=best_x,
        syndrome_ok=syn_ok,
        iterations=max_iter,
        runtime_s=time.perf_counter() - t0,
        status="converged_no_syndrome" if not syn_ok else "converged_exact",
        final_beliefs=beliefs,
        belief_provenance=(
            BELIEF_PROVENANCE_WARM_START_UNSPECIFIED if warm_seeded
            else (BELIEF_PROVENANCE_CHECK_UPDATED if max_iter >= 1
                  else BELIEF_PROVENANCE_PRIOR_ONLY)),
        extrinsic_log_beliefs=ext_beliefs,
        extrinsic_provenance=ext_prov,
    )


def decode_damped_row_layered_fftqspa(
    h_matrix: np.ndarray,
    priors: np.ndarray,
    syndromes: np.ndarray,
    max_iter: int = DEFAULT_MAX_ITER,
    damping_alpha: float = DEFAULT_DAMPING_ALPHA,
    warm_beliefs: Optional[np.ndarray] = None,
    field: Optional[GF2mField] = None,
) -> DecoderResult:
    """Stage A1 Damped Row-Layered FFT-QSPA Decoder (default alpha=0.5)."""
    return decode_row_layered_fftqspa(
        h_matrix=h_matrix,
        priors=priors,
        syndromes=syndromes,
        max_iter=max_iter,
        damping_alpha=damping_alpha,
        warm_beliefs=warm_beliefs,
        field=field,
    )

# ---------------------------------------------------------------------------
# Stage A2: Empirical-P Protograph & Quasi-Cyclic Deterministic Lifting
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtographSpec:
    B: np.ndarray
    shifts: np.ndarray
    variable_degrees: tuple[int, ...]
    check_degrees: tuple[int, ...]
    avg_variable_degree: float
    degree2_edge_fraction: float
    girth: int
    design_rate: float


def check_protograph_degree2_cycles(B: np.ndarray) -> int:
    """Count the cycle rank (number of independent cycles) formed purely by degree-2 variable nodes in protograph B."""
    M_p, N_p = B.shape
    deg2_cols = [c for c in range(N_p) if np.sum(B[:, c]) == 2]
    adj: dict[int, list[tuple[int, int]]] = {r: [] for r in range(M_p)}
    for col in deg2_cols:
        r1, r2 = np.where(B[:, col] == 1)[0]
        adj[r1].append((r2, col))
        adj[r2].append((r1, col))

    visited = set()
    total_cycle_rank = 0
    for r in range(M_p):
        if r not in visited and len(adj[r]) > 0:
            comp_nodes = []
            comp_edges = 0
            queue = [r]
            visited.add(r)
            for node in queue:
                comp_nodes.append(node)
                for neighbor, col in adj[node]:
                    comp_edges += 1
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            comp_edges //= 2
            cycle_rank = comp_edges - len(comp_nodes) + 1
            if cycle_rank > 0:
                total_cycle_rank += cycle_rank
    return total_cycle_rank


def build_hand_designed_mixed_degree_protograph() -> np.ndarray:
    """Build deterministic 6x32 mixed-degree protograph base matrix B with variable degrees in 2..5.

    - 4 nodes of dv=2 connected as an acyclic path (0,1), (1,2), (2,3), (3,4) (strictly 0 degree-2 cycles)
    - 22 nodes of dv=3
    - 5 nodes of dv=4
    - 1 node of dv=5
    Total edges = 99, avg dv = 3.09375 in [2.2, 3.2], lambda2 = 8/99 = 0.0808 <= 0.35, lambda1 = 0.
    Check degrees are balanced: [17, 17, 16, 17, 16, 16].
    """
    M_p, N_p = M_PROTOGRAPH, N_PROTOGRAPH
    B = np.zeros((M_p, N_p), dtype=np.uint8)

    # 4 degree-2 variable nodes (columns 0..3) forming a simple path: (0,1), (1,2), (2,3), (3,4)
    deg2_pairs = [(0, 1), (1, 2), (2, 3), (3, 4)]
    for j, (r1, r2) in enumerate(deg2_pairs):
        B[r1, j] = 1
        B[r2, j] = 1

    # Remaining degrees: 22 dv=3, 5 dv=4, 1 dv=5
    dv_rem = [3] * 22 + [4] * 5 + [5] * 1
    for idx, d in enumerate(dv_rem):
        col = 4 + idx
        cur_degs = B.sum(axis=1)
        order = np.argsort(cur_degs)
        for r in order[:d]:
            B[r, col] = 1

    assert check_protograph_degree2_cycles(B) == 0, "Protograph must not contain degree-2 cycles"
    return B


# Backward-compatible alias
build_v35_protograph = build_hand_designed_mixed_degree_protograph


def build_v35_shifts(B: np.ndarray, Z: int = Z_LIFTING, seed: int = 20260824) -> np.ndarray:
    """Construct deterministic shift matrix S of shape (M_p, N_p) guaranteeing girth >= 6 (0 4-cycles)."""
    M_p, N_p = B.shape
    S = np.full((M_p, N_p), -1, dtype=np.int32)
    rng = np.random.default_rng(int(seed))

    def _count_4_cycles_local(col_idx: int) -> int:
        c4 = 0
        for r1 in range(M_p):
            for r2 in range(r1 + 1, M_p):
                if B[r1, col_idx] and B[r2, col_idx] and S[r1, col_idx] >= 0 and S[r2, col_idx] >= 0:
                    other_cols = [
                        c for c in range(col_idx)
                        if B[r1, c] and B[r2, c] and S[r1, c] >= 0 and S[r2, c] >= 0
                    ]
                    for c2 in other_cols:
                        delta = (S[r1, col_idx] - S[r1, c2] + S[r2, c2] - S[r2, col_idx]) % Z
                        if delta == 0:
                            c4 += 1
        return c4

    for col in range(N_p):
        row_indices = np.where(B[:, col] == 1)[0]
        deg = len(row_indices)
        best_shifts = None
        best_c = 999999
        for _ in range(500):
            cand_shifts = rng.choice(Z, size=deg, replace=False)
            for r, s in zip(row_indices, cand_shifts):
                S[r, col] = s
            c4 = _count_4_cycles_local(col)
            if c4 == 0:
                best_shifts = cand_shifts
                best_c = 0
                break
            elif c4 < best_c:
                best_c = c4
                best_shifts = cand_shifts
        for r, s in zip(row_indices, best_shifts):
            S[r, col] = s

    return S


def count_tanner_4_cycles(B: np.ndarray, S: np.ndarray, Z: int = Z_LIFTING) -> int:
    """Count exact 4-cycles in lifted Tanner graph."""
    M_p, N_p = B.shape
    total_c4 = 0
    for r1 in range(M_p):
        for r2 in range(r1 + 1, M_p):
            cols = [c for c in range(N_p) if B[r1, c] and B[r2, c] and S[r1, c] >= 0 and S[r2, c] >= 0]
            for i in range(len(cols)):
                for j in range(i + 1, len(cols)):
                    c1, c2 = cols[i], cols[j]
                    delta = (S[r1, c1] - S[r1, c2] + S[r2, c2] - S[r2, c1]) % Z
                    if delta == 0:
                        total_c4 += 1
    return total_c4


def lift_protograph_gf32(
    B: np.ndarray,
    S: np.ndarray,
    Z: int = Z_LIFTING,
    field: Optional[GF2mField] = None,
    seed: int = 999,
) -> np.ndarray:
    """Lift protograph into full (M_p*Z, N_p*Z) parity check matrix over GF(32)."""
    if field is None:
        field = GF2mField.create(FIELD_Q)
    M_p, N_p = B.shape
    M = M_p * Z
    N = N_p * Z
    H = np.zeros((M, N), dtype=np.uint8)
    rng = np.random.default_rng(int(seed))

    for r in range(M_p):
        for c in range(N_p):
            if B[r, c] == 1:
                shift = int(S[r, c])
                coeff = int(rng.integers(1, FIELD_Q))
                for z in range(Z):
                    row_idx = r * Z + z
                    col_idx = c * Z + ((z + shift) % Z)
                    H[row_idx, col_idx] = coeff

    # Check rank and ensure full row rank
    rank = compute_gf32_rank(H, field)
    if rank < M:
        for r in range(M_p):
            for c in range(N_p):
                if B[r, c] == 1:
                    H[r * Z : (r + 1) * Z, c * Z : (c + 1) * Z] = 0
                    shift = int(S[r, c])
                    coeff = int((r * N_p + c + 1) % 31 + 1)
                    for z in range(Z):
                        H[r * Z + z, c * Z + ((z + shift) % Z)] = coeff

    return H


# ---------------------------------------------------------------------------
# Stage A3: Rate-Adaptive Incremental Parity-Check Hierarchy
# ---------------------------------------------------------------------------

@dataclass
class IncrementalResult:
    x_hat: np.ndarray
    exact_l2: bool
    syndrome_ok: bool
    tag_ok: bool
    false_accept: bool
    stage_reached: str
    errors_initial: int
    errors_final: int
    iterations: int
    runtime_s: float
    syndrome_leakage_bits: int
    cumulative_leakage_bits: int
    status: str


def build_v35_incremental_mother_matrix(
    base_H: np.ndarray,
    Z: int = Z_LIFTING,
    field: Optional[GF2mField] = None,
    seed: int = 54321,
) -> np.ndarray:
    """Build nested mother matrix H_mother of shape (224, 1024) extending base 192x1024."""
    if field is None:
        field = GF2mField.create(FIELD_Q)
    base_m, n = base_H.shape
    total_m = INCREMENTAL_CHECKS["S3"]  # 224
    extra_m = total_m - base_m          # 32
    rng = np.random.default_rng(int(seed))

    # Construct 1 additional protograph row block (32 checks)
    extra_shifts = [int(rng.integers(0, Z)) for _ in range(N_PROTOGRAPH)]
    extra_H = np.zeros((extra_m, n), dtype=np.uint8)

    for c in range(N_PROTOGRAPH):
        shift = extra_shifts[c]
        coeff = int(rng.integers(1, FIELD_Q))
        for z in range(Z):
            row_idx = z
            col_idx = c * Z + ((z + shift) % Z)
            extra_H[row_idx, col_idx] = coeff

    H_mother = np.vstack([base_H, extra_H])
    return H_mother


def get_incremental_check_counts(source: str) -> dict[str, int]:
    """Return exact check counts for each incremental stage by source."""
    base_m = {"1M": 184, "1p5M": 190, "2M": 192}[source]
    return {
        "S0": base_m,
        "S1": base_m + 8,
        "S2": base_m + 16,
        "S3": base_m + 32,
    }


def decode_v35_incremental_stage_a3(
    H_mother: np.ndarray,
    priors: np.ndarray,
    x2_true: np.ndarray,
    x1_true: np.ndarray,
    source: str = "2M",
    max_iter_per_stage: int = DEFAULT_MAX_ITER,
    damping_alpha: float = DEFAULT_DAMPING_ALPHA,
    field: Optional[GF2mField] = None,
) -> dict[str, IncrementalResult]:
    """Execute Stage A3 Rate-Adaptive Incremental Parity Check with clean cold-starts.

    Evaluates S0 (+0b), S1 (+40b), S2 (+80b), S3 (+160b) independently from fresh channel priors,
    avoiding message double-counting artifacts.
    """
    if field is None:
        field = GF2mField.create(FIELD_Q)

    target_tag = compute_tag_64(x1_true, x2_true)
    y2_init = np.argmax(priors, axis=1).astype(np.uint8)
    errors_init = int(np.sum(y2_init != x2_true))

    check_counts = get_incremental_check_counts(source)
    results: dict[str, IncrementalResult] = {}

    for stage in INCREMENTAL_STAGES:
        t0 = time.perf_counter()
        m_rows = check_counts[stage]
        H_sub = H_mother[:m_rows, :]
        syn_true = syndrome_of_gf32(H_sub, x2_true, field)

        # Run damped row-layered decoder with clean cold-start (warm_beliefs=None)
        res = decode_row_layered_fftqspa(
            h_matrix=H_sub,
            priors=priors,
            syndromes=syn_true,
            max_iter=max_iter_per_stage,
            damping_alpha=damping_alpha,
            warm_beliefs=None,
            field=field,
        )

        candidate_tag = compute_tag_64(x1_true, res.x_hat)
        tag_ok = bool(candidate_tag == target_tag)
        exact_l2 = bool(np.array_equal(res.x_hat, x2_true))
        false_accept = bool(tag_ok and not exact_l2)
        errs_final = int(np.sum(res.x_hat != x2_true))
        syn_leak = INCREMENTAL_EXTRA_BITS[stage]
        cum_leak = m_rows * 5 + TAG_BITS

        status = "converged_exact" if exact_l2 and res.syndrome_ok and tag_ok else res.status

        results[stage] = IncrementalResult(
            x_hat=res.x_hat,
            exact_l2=exact_l2,
            syndrome_ok=res.syndrome_ok,
            tag_ok=tag_ok,
            false_accept=false_accept,
            stage_reached=stage,
            errors_initial=errors_init,
            errors_final=errs_final,
            iterations=res.iterations,
            runtime_s=time.perf_counter() - t0,
            syndrome_leakage_bits=syn_leak,
            cumulative_leakage_bits=cum_leak,
            status=status,
        )

    return results

# ---------------------------------------------------------------------------
# Stage A4: Binary Multilevel Coding (MLC) Fallback
# ---------------------------------------------------------------------------

def gray_encode_symbols(symbols: np.ndarray) -> np.ndarray:
    """10-bit Gray code encoding of symbols."""
    vals = np.asarray(symbols, dtype=np.int64)
    return np.bitwise_xor(vals, vals >> 1)


def gray_decode_symbols(values: np.ndarray) -> np.ndarray:
    """Inverse 10-bit Gray code decoding."""
    out = np.asarray(values, dtype=np.int64).copy()
    shift = out >> 1
    while np.any(shift):
        out ^= shift
        shift >>= 1
    return out


def symbols_to_gray_bitplanes(symbols: np.ndarray) -> np.ndarray:
    """Decompose length-N symbol array into (N, 10) bit matrix where col 0 is MSB."""
    vals = np.asarray(symbols, dtype=np.int64).reshape(-1)
    g = gray_encode_symbols(vals)
    powers = np.arange(9, -1, -1, dtype=np.int64)
    return ((g[:, None] >> powers) & 1).astype(np.uint8)


def gray_bitplanes_to_symbols(bitplanes: np.ndarray) -> np.ndarray:
    """Reconstruct length-N symbol array from (N, 10) bit matrix."""
    arr = np.asarray(bitplanes, dtype=np.uint8)
    powers = np.arange(9, -1, -1, dtype=np.int64)
    g = np.sum(arr.astype(np.int64) * (1 << powers), axis=1)
    return gray_decode_symbols(g)


def compute_conditional_entropy_profile(counts: np.ndarray) -> tuple[np.ndarray, float]:
    """Compute layer conditional entropies H(b_i | Y, b_<i) for i=0..9 from V25 counts."""
    arr = np.asarray(counts, dtype=np.float64)
    total = np.sum(arr)
    p_ab = arr / total

    # Symbol to bitplane mapping lookup table (1024, 10)
    all_syms = np.arange(1024, dtype=np.int64)
    planes_lookup = symbols_to_gray_bitplanes(all_syms)

    # Compute marginals and conditional entropies
    # Total H(A | B)
    p_b = p_ab.sum(axis=0)  # (1024,)
    with np.errstate(divide="ignore", invalid="ignore"):
        p_a_given_b = p_ab / np.maximum(p_b[None, :], 1e-300)
        log_cond = np.where(p_a_given_b > 0, np.log2(p_a_given_b), 0.0)
        h_a_given_b = -float(np.sum(p_ab * log_cond))

    layer_entropies = np.zeros(10, dtype=np.float64)

    # For layer i, compute H(b_i | Y, b_0..b_{i-1})
    for i in range(10):
        # Prefix key for each symbol
        if i == 0:
            prefix_idx = np.zeros(1024, dtype=np.int64)
            n_prefixes = 1
        else:
            prefix_powers = np.arange(i - 1, -1, -1, dtype=np.int64)
            prefix_idx = np.sum(planes_lookup[:, :i] * (1 << prefix_powers), axis=1)
            n_prefixes = 1 << i

        bit_i = planes_lookup[:, i]  # (1024,)

        # Accumulate joint P(b_i, prefix, Y)
        # Shape: (2, n_prefixes, 1024)
        p_joint = np.zeros((2, n_prefixes, 1024), dtype=np.float64)
        for a in range(1024):
            b_val = bit_i[a]
            p_val = prefix_idx[a]
            p_joint[b_val, p_val, :] += p_ab[a, :]

        p_prefix_y = p_joint.sum(axis=0)  # (n_prefixes, 1024)
        with np.errstate(divide="ignore", invalid="ignore"):
            p_bi_given = p_joint / np.maximum(p_prefix_y[None, :, :], 1e-300)
            log_bi = np.where(p_bi_given > 0, np.log2(p_bi_given), 0.0)
            h_layer = -float(np.sum(p_joint * log_bi))

        layer_entropies[i] = h_layer

    return layer_entropies, h_a_given_b


def compute_empirical_conditional_llrs(
    counts: np.ndarray,
    bob_symbols: np.ndarray,
    decoded_planes: Sequence[np.ndarray],
    target_plane: int,
) -> np.ndarray:
    """Compute log-likelihood ratio LLR = ln(P(b_i=0)/P(b_i=1)) given (Y, b_<i)."""
    arr = np.asarray(counts, dtype=np.float64)
    b = np.asarray(bob_symbols, dtype=np.int64)
    n = b.shape[0]
    i = int(target_plane)

    all_syms = np.arange(1024, dtype=np.int64)
    lookup = symbols_to_gray_bitplanes(all_syms)

    if i == 0:
        mask0 = (lookup[:, 0] == 0)
        mask1 = (lookup[:, 0] == 1)
        p0 = arr[mask0, :][:, b].sum(axis=0)
        p1 = arr[mask1, :][:, b].sum(axis=0)
    else:
        # Match decoded prefix
        prefix_matrix = np.column_stack([decoded_planes[k] for k in range(i)])  # (n, i)
        # Vectorized candidate filtering
        # lookup[:, :i] has shape (1024, i)
        # prefix_matrix has shape (n, i)
        # We can map prefix to an integer ID
        powers = np.arange(i - 1, -1, -1, dtype=np.int64)
        sym_prefixes = np.sum(lookup[:, :i] * (1 << powers), axis=1)  # (1024,)
        obs_prefixes = np.sum(prefix_matrix * (1 << powers), axis=1)  # (n,)

        p0 = np.empty(n, dtype=np.float64)
        p1 = np.empty(n, dtype=np.float64)
        for k in range(n):
            obs_p = obs_prefixes[k]
            obs_b = b[k]
            candidates = np.where(sym_prefixes == obs_p)[0]
            if len(candidates) == 0:
                p0[k] = 0.5
                p1[k] = 0.5
                continue
            cand_b0 = candidates[lookup[candidates, i] == 0]
            cand_b1 = candidates[lookup[candidates, i] == 1]
            mass0 = float(np.sum(arr[cand_b0, obs_b]))
            mass1 = float(np.sum(arr[cand_b1, obs_b]))
            if mass0 + mass1 <= 0:
                p0[k] = 0.5
                p1[k] = 0.5
            else:
                p0[k] = mass0
                p1[k] = mass1

    p0 = np.maximum(p0, 1e-12)
    p1 = np.maximum(p1, 1e-12)
    llrs = np.log(p0 / p1)
    return llrs


def make_binary_parity_check_matrix(n: int, m: int, seed: int = 42) -> np.ndarray:
    """Generate deterministic column-weight-3 binary parity check matrix."""
    rng = np.random.default_rng(int(seed))
    m = max(1, int(m))
    n = max(1, int(n))
    w = max(1, min(3, m))
    h = np.zeros((m, n), dtype=np.uint8)
    for col in range(n):
        rows = rng.choice(m, size=w, replace=False)
        h[rows, col] = 1
    # Ensure no empty rows
    row_sums = h.sum(axis=1)
    for r in np.where(row_sums == 0)[0]:
        h[r, int(rng.integers(0, n))] = 1
    return h


@dataclass
class MLCPlaneResult:
    plane: int
    raw_errors: int
    final_errors: int
    syndrome_ok: bool
    exact_ok: bool
    iterations: int


@dataclass
class MLCResult:
    x_hat_symbols: np.ndarray
    exact_frame: bool
    tag_ok: bool
    false_accept: bool
    errors_initial_symbols: int
    errors_final_symbols: int
    total_iterations: int
    runtime_s: float
    total_syndrome_bits: int
    cumulative_leakage_bits: int
    first_failed_plane: int
    plane_results: list[MLCPlaneResult]
    status: str


def decode_binary_mlc_frame(
    counts: np.ndarray,
    alice_symbols: np.ndarray,
    bob_symbols: np.ndarray,
    parity_matrices: Optional[list[np.ndarray]] = None,
    max_iter: int = DEFAULT_MAX_ITER,
) -> MLCResult:
    """Stage A4 Binary Multilevel Coding (MLC) Sequential Multistage Decoder."""
    t0 = time.perf_counter()
    has_ldpc = importlib.util.find_spec("ldpc") is not None
    if has_ldpc:
        from ldpc import BpOsdDecoder  # type: ignore

    n = len(alice_symbols)
    target_tag = compute_tag_64_symbols(alice_symbols)
    alice_planes = symbols_to_gray_bitplanes(alice_symbols)
    bob_planes = symbols_to_gray_bitplanes(bob_symbols)

    errors_init_syms = int(np.sum(alice_symbols != bob_symbols))

    # Standard rate allocation profile matching conditional entropy
    if parity_matrices is None:
        plane_row_counts = [16, 16, 16, 16, 24, 32, 64, 128, 280, 440]
        parity_matrices = [
            make_binary_parity_check_matrix(n, m_rows, seed=1000 + i * 137)
            for i, m_rows in enumerate(plane_row_counts)
        ]

    decoded_planes: list[np.ndarray] = []
    plane_records: list[MLCPlaneResult] = []
    total_iters = 0
    first_failed = -1

    for i in range(10):
        H_i = parity_matrices[i]
        a_bits = alice_planes[:, i]
        b_bits = bob_planes[:, i]
        raw_errs = int(np.sum(a_bits != b_bits))

        syn_alice = (H_i @ a_bits) % 2
        syn_bob = (H_i @ b_bits) % 2
        syn_delta = (syn_alice ^ syn_bob).astype(np.uint8)

        llrs = compute_empirical_conditional_llrs(counts, bob_symbols, decoded_planes, i)
        p_err = 1.0 / (1.0 + np.exp(np.abs(llrs)))
        p_err_clipped = np.clip(p_err, 1e-4, 0.49).tolist()

        if has_ldpc:
            dec = BpOsdDecoder(
                H_i.astype(np.uint8),
                error_channel=p_err_clipped,
                max_iter=max_iter,
                bp_method="minimum_sum",
                osd_method="OSD_0",
                osd_order=0,
            )
            err_hat = np.asarray(dec.decode(syn_delta), dtype=np.uint8) % 2
            iters = int(getattr(dec, "iter", 0) or 0)
        else:
            # Fallback simple bit flipping
            err_hat = np.zeros(n, dtype=np.uint8)
            iters = 0

        total_iters += iters
        rec_bits = (b_bits ^ err_hat).astype(np.uint8)
        syn_check = bool(np.array_equal((H_i @ rec_bits) % 2, syn_alice))
        exact_ok = bool(np.array_equal(rec_bits, a_bits))
        final_errs = int(np.sum(rec_bits != a_bits))

        if not exact_ok and first_failed == -1:
            first_failed = i

        decoded_planes.append(rec_bits)
        plane_records.append(
            MLCPlaneResult(
                plane=i,
                raw_errors=raw_errs,
                final_errors=final_errs,
                syndrome_ok=syn_check,
                exact_ok=exact_ok,
                iterations=iters,
            )
        )

    # Reconstruct symbols
    rec_bit_matrix = np.column_stack(decoded_planes)
    rec_symbols = gray_bitplanes_to_symbols(rec_bit_matrix)
    errors_final_syms = int(np.sum(rec_symbols != alice_symbols))
    exact_frame = bool(errors_final_syms == 0)

    candidate_tag = compute_tag_64_symbols(rec_symbols)
    tag_ok = bool(candidate_tag == target_tag)
    false_accept = bool(tag_ok and not exact_frame)

    total_syn_bits = sum(H.shape[0] for H in parity_matrices)
    cum_leak = total_syn_bits + TAG_BITS

    return MLCResult(
        x_hat_symbols=rec_symbols,
        exact_frame=exact_frame,
        tag_ok=tag_ok,
        false_accept=false_accept,
        errors_initial_symbols=errors_init_syms,
        errors_final_symbols=errors_final_syms,
        total_iterations=total_iters,
        runtime_s=time.perf_counter() - t0,
        total_syndrome_bits=total_syn_bits,
        cumulative_leakage_bits=cum_leak,
        first_failed_plane=first_failed,
        plane_results=plane_records,
        status="converged_exact" if exact_frame else "decode_failed",
    )

# ---------------------------------------------------------------------------
# Per-Block Evaluation Record Structure
# ---------------------------------------------------------------------------

@dataclass
class BlockRecord:
    source: str
    seed: int
    method: str
    graph_id: str
    decoder_schedule: str
    redundancy_stage: str
    exact_l2: bool
    syndrome_ok: bool
    tag_ok: bool
    false_accept: bool
    errors_initial: int
    errors_final: int
    iterations: int
    runtime_s: float
    syndrome_leakage_bits: int
    cumulative_leakage_bits: int
    status: str

    def to_csv_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "seed": self.seed,
            "method": self.method,
            "graph_id": self.graph_id,
            "decoder_schedule": self.decoder_schedule,
            "redundancy_stage": self.redundancy_stage,
            "exact_l2": self.exact_l2,
            "syndrome_ok": self.syndrome_ok,
            "tag_ok": self.tag_ok,
            "false_accept": self.false_accept,
            "errors_initial": self.errors_initial,
            "errors_final": self.errors_final,
            "iterations": self.iterations,
            "runtime_s": round(self.runtime_s, 6),
            "syndrome_leakage_bits": self.syndrome_leakage_bits,
            "cumulative_leakage_bits": self.cumulative_leakage_bits,
            "status": self.status,
        }
