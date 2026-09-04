"""V72P2D3 GF32 contrast thin adapter — synthetic-only, no real data.

Frozen mapping low=bits0..4 high=bits5..9 bit0 LSB symbol=low+32*high
same direction as v35 factorize_f03 (u1=high MSB, u2=low LSB), no Gray,
no permutation. Prior Stage1 P(high|B)=P(U1|B) and Stage2
P(low|high,B)=P(U2|U1,B) from current CAL only; production L2 prior is
q@P via V54 get_l1_app_prior_l2 where q=softmax(L1 final_beliefs). CE in
log2, prior log for the G layers in natural log. Arm A is D1 read-only
reuse (binary only). G uses the same VAL block and CAL702..1725 domain.
No tag in the diagnostic.

HISTORICAL_KERNEL (R1): v35 decode_row_layered_fftqspa, codeword domain.
Input (H, prior P(X), syndrome H*x); output (x_hat, syndrome_ok,
iterations 0..max, final_beliefs); syndrome-equality stop; warm_beliefs
is log-belief initial value only; V54 production path is always cold
start (belief_warm=None). Unique production chain (R2) is the V54 chain:
L1 (_dec_l1/H1) + L2 three stages (H_base/H_joint/H_total, prior_l2=q@P,
max90 damping1.0). Thin adapter (R3) only does mapping/matrix/prior
direction/syndrome/true-kernel call/field unification/stage
orchestration/diagnostics; production directly calls the true iterative
function. No argmax impersonation, no fixed hard, no hard-coded iters,
no imitated decoder in production, no simplified decoder, no binary-called-GF32, no
history-kernel modification.

Call graph (production, decode_fn=None):
  symbols_to_layers/factorize_f03 binding (u1=high/MSB, u2=low/LSB)
  -> get_gf32_field (v35 GF2mField.create(32) poly37, unified)
  -> nested_geometry/H matrices (H1=16; H_base184/H_joint192/H_total200)
  -> build_stage1_P/build_stage2_P (synthetic) or V54
     get_l1_prior_p_u1_given_b (P(U1|B)) / get_l1_app_prior_l2 (q@P)
  -> gf32_syndrome targets via v35 syndrome_of_gf32
     (s1=H1*u1 Alice; s_base=H_base*u2, s_joint, s_total Alice)
  -> history_decode (v35 decode_row_layered_fftqspa, belief_warm=None cold)
  -> run_g_layer/run_l1_stage/run_l2_incremental_chain diagnostics
     (L1 q=softmax(final_beliefs) always feeds L2; base-ok skips
     joint/total; joint-ok skips total; each stage cold)
  -> write_contrast_outputs (4-file schema).
Short-circuit (R5, V54 order): base verify skips joint/total; joint
verify skips total; L1 q always feeds L2 (no L1 gate).

Real-entry production call chain (frozen order, fake-E2E only in this
change): gate(authorize/preflight/output) -> registry -> CAL/VAL validate
-> fit -> assemble block -> A reuse -> words -> matrices -> syndromes
(Alice side) -> true kernel (L1 cold + L2 chain cold, production
decode_fn=None) -> reassemble -> posthoc -> four files. Budgets
prep<=300s, G<=300s, invocation<=600s, peak RSS<2GiB. No parquet import,
no real decoder run, no production-root creation here; callers inject
registry/frames/matrices and an explicit test-only decode_fn.
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
from typing import Any

import numpy as np

Q = 1024
Q_SUB = 32
N = 1024
NBIT = 10240
M_BASE = 184
H1_ROWS = 16
M_TOTAL = 200
NESTED_ROWS = (184, 192, 200)
MAX_ITER = 90
DAMPING_ALPHA = 1.0
POLY = 37
SESSION_ID = "20260123_1M_600k_0dB"
VAL_FRAMES = (1726, 1727, 1728, 1729)
CAL_START = 702
CAL_END = 1725
LEAK_BASE = 1064
LEAK_S1 = 1104
LEAK_S2 = 1144
TAG_BITS = 0
TAG_OK = "NOT_APPLICABLE"
A_M = 9036
A_NBIT = 10240
A_NNZ = 49620
A_LADDER_FIRST = 160
A_LADDER_LAST = 9036
A_LADDER_COUNT = 72
A_PER_CKPT = 10
A_PER_ARM = 720
HISTORY_KERNEL_ID = "V35-decode_row_layered_fftqspa-via-V54-chain"
HISTORY_DECODER_FN = "v35_algorithm_development.decode_row_layered_fftqspa"
HISTORY_L1_FN = "v54_two_stage_incremental_l2_rescue._dec_l1(H1)"
HISTORY_L2_CHAIN = "V54-base(H_base)-stage1(H_joint)-stage2(H_total)-prior_l2=q@P"
RESIDUAL_NOT_RECORDED = "NOT_RECORDED"
PROB_FLOOR = 1e-300
LN2 = math.log(2.0)
CYCLE_ID = "V72P2D3-GF32"
BASE_SHA = "e094f7e548380db4bfcbc1fe73472e670c32379a"

# Real-entry budgets and fixed block geometry (EXECUTION_PACKET section 6:
# prep300 / G300 / invocation600 seconds, RSS 2GiB). Single VAL block only;
# a nine-block loop SHALL NOT be added here.
PREP_LIMIT_S = 300.0
G_LIMIT_S = 300.0
INV_LIMIT_S = 600.0
RSS_LIMIT_BYTES = 2 * 1024**3
FRAME_PAIRS = 256
REAL_CAL_IDS = tuple(range(CAL_START, CAL_END + 1))
REAL_BLOCK_IDS = tuple(VAL_FRAMES)
# ponytail: fake-E2E smoothing is a frozen scalar, not a tuned grid; the
# production selection grid lives outside this change.
FAKE_E2E_LAM = 1.0
REAL_BRANCHES = (
    "G_EXACT",
    "G_COLLISION",
    "G_IMPROVED_NO_SYNDROME",
    "G_NO_MOTION",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_history_module(file_name: str, module_name: str) -> Any:
    import sys

    path = (
        _repo_root()
        / "comparison_bench"
        / "src"
        / "comparison_bench"
        / "formal_ir"
        / file_name
    )
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load history module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def get_gf32_field() -> Any:
    """Return the bound history GF(32) field, poly37 only (v35 unified)."""
    try:
        from comparison_bench.formal_ir.v35_algorithm_development import (
            GF2mField as _F1,
        )
    except ImportError:
        try:
            from comparison_bench.src.comparison_bench.formal_ir.v35_algorithm_development import (
                GF2mField as _F1,
            )
        except ImportError:
            mod = _load_history_module(
                "v35_algorithm_development.py", "v72p2d3_history_v35"
            )
            _F1 = mod.GF2mField
    field = _F1.create(32)
    if int(field.primitive_polynomial) != POLY:
        raise ValueError("history field polynomial mismatch")
    if int(field.q) != Q_SUB:
        raise ValueError("history field order mismatch")
    return field


def _load_v35() -> Any:
    """Load the frozen v35 history module without modifying it."""
    try:
        from comparison_bench.formal_ir import (
            v35_algorithm_development as _m,
        )

        return _m
    except ImportError:
        try:
            from comparison_bench.src.comparison_bench.formal_ir import (
                v35_algorithm_development as _m,
            )

            return _m
        except ImportError:
            return _load_history_module(
                "v35_algorithm_development.py", "v72p2d3_history_v35"
            )


def _load_v54() -> Any:
    """Load the frozen V54 chain module without modifying it."""
    try:
        from comparison_bench.formal_ir import (
            v54_two_stage_incremental_l2_rescue as _m,
        )

        return _m
    except ImportError:
        try:
            from comparison_bench.src.comparison_bench.formal_ir import (
                v54_two_stage_incremental_l2_rescue as _m,
            )

            return _m
        except ImportError:
            return _load_history_module(
                "v54_two_stage_incremental_l2_rescue.py", "v72p2d3_history_v54"
            )


def history_decoder_fn() -> Any:
    """Return the unique history decoder (v35 decode_row_layered_fftqspa)."""
    return _load_v35().decode_row_layered_fftqspa


def gf32_syndrome(h_matrix: np.ndarray, x: np.ndarray, field: Any = None) -> np.ndarray:
    """G-layer GF32 syndrome H*x via the history kernel (never binary)."""
    v35 = _load_v35()
    fld = field if field is not None else get_gf32_field()
    return np.asarray(
        v35.syndrome_of_gf32(
            np.asarray(h_matrix, dtype=np.uint8),
            np.asarray(x, dtype=np.uint8).reshape(-1),
            fld,
        ),
        dtype=np.uint8,
    )


def factorize_f03_binding(
    alice: np.ndarray, bob: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Delegate mapping direction to v35 factorize_f03 (u1=high, u2=low)."""
    return _load_v35().factorize_f03(
        np.asarray(alice), np.asarray(bob)
    )


def history_decode(
    h_matrix: np.ndarray,
    prior: np.ndarray,
    syndrome_target: np.ndarray,
    max_iter: int = MAX_ITER,
    damping_alpha: float = DAMPING_ALPHA,
    belief_warm: np.ndarray | None = None,
    field: Any = None,
) -> Any:
    """Thin passthrough to the true iterative history kernel (cold default).

    belief_warm, when given, is only the initial log-belief value (R1/R4);
    it is never message carry. Production stages always pass None (cold
    start, matching V54 which never passes warm_beliefs).
    """
    if isinstance(max_iter, bool) or not isinstance(max_iter, int):
        raise ValueError("max_iter must be an integer")
    if int(max_iter) < 1 or int(max_iter) > MAX_ITER:
        raise ValueError(f"max_iter must lie in 1..{MAX_ITER}")
    if float(damping_alpha) != float(DAMPING_ALPHA):
        raise ValueError("damping_alpha is frozen at 1.0")
    fld = field if field is not None else get_gf32_field()
    dec = history_decoder_fn()
    warm = None
    if belief_warm is not None:
        warm = np.asarray(belief_warm, dtype=np.float64)
        if warm.ndim != 2 or warm.shape[1] != Q_SUB:
            raise ValueError("belief_warm must have shape (n,32)")
        if not np.all(np.isfinite(warm)):
            raise ValueError("belief_warm must be finite")
        if warm.shape[0] != np.asarray(h_matrix).shape[1]:
            raise ValueError("belief_warm width must equal variable count")
    return dec(
        np.asarray(h_matrix, dtype=np.uint8),
        np.asarray(prior, dtype=np.float64),
        np.asarray(syndrome_target, dtype=np.uint8).reshape(-1),
        max_iter=int(max_iter),
        damping_alpha=float(damping_alpha),
        warm_beliefs=warm,
        field=fld,
    )


def get_l1_prior_production(counts: np.ndarray, bob: np.ndarray) -> np.ndarray:
    """Production L1 prior P(U1|B) via exact V54 reuse (counts 1024x1024)."""
    return _load_v54().get_l1_prior_p_u1_given_b(
        np.asarray(counts, dtype=np.float64), np.asarray(bob, dtype=np.int64)
    )


def build_l2_prior_from_l1(
    counts: np.ndarray, bob: np.ndarray, q: np.ndarray
) -> np.ndarray:
    """Production L2 prior prior_l2=q@P via exact V54 reuse."""
    return _load_v54().get_l1_app_prior_l2(
        np.asarray(counts, dtype=np.float64),
        np.asarray(bob, dtype=np.int64),
        np.asarray(q, dtype=np.float64),
    )


def softmax_beliefs_history(beliefs: np.ndarray) -> np.ndarray:
    """q=softmax(final_beliefs) via exact V54 reuse."""
    return _load_v54().softmax_beliefs(np.asarray(beliefs, dtype=np.float64))


def history_kernel_id() -> str:
    return HISTORY_KERNEL_ID


def split_symbol(sym: int) -> tuple[int, int]:
    s = int(sym)
    if not 0 <= s < Q:
        raise ValueError("symbol outside 0..1023")
    low = s & 31
    high = (s >> 5) & 31
    return low, high


def combine_symbol(low: int, high: int) -> int:
    lo, hi = int(low), int(high)
    if not 0 <= lo < Q_SUB or not 0 <= hi < Q_SUB:
        raise ValueError("low/high outside 0..31")
    return lo + 32 * hi


def symbols_to_layers(symbols: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """low=u2=bits0..4, high=u1=bits5..9; direction bound to v35 factorize_f03."""
    arr = np.asarray(symbols, dtype=np.int64).reshape(-1)
    if np.any(arr < 0) or np.any(arr >= Q):
        raise ValueError("symbols outside 0..1023")
    low = (arr & 31).astype(np.int64)
    high = ((arr >> 5) & 31).astype(np.int64)
    return low, high


def layers_to_symbols(low: np.ndarray, high: np.ndarray) -> np.ndarray:
    """symbol=low+32*high; must roundtrip factorize_f03 direction."""
    lo = np.asarray(low, dtype=np.int64).reshape(-1)
    hi = np.asarray(high, dtype=np.int64).reshape(-1)
    if lo.shape != hi.shape:
        raise ValueError("low/high length mismatch")
    if np.any(lo < 0) or np.any(lo >= Q_SUB) or np.any(hi < 0) or np.any(hi >= Q_SUB):
        raise ValueError("low/high outside 0..31")
    return (lo + 32 * hi).astype(np.int64)


def nested_geometry() -> dict[str, Any]:
    return {
        "m_base": M_BASE,
        "h1_rows": H1_ROWS,
        "m_total": M_TOTAL,
        "nested": tuple(NESTED_ROWS),
        "shapes": [(M_BASE, N), (M_BASE + 8, N), (M_TOTAL, N)],
        "leak": (LEAK_BASE, LEAK_S1, LEAK_S2),
        "q": Q_SUB,
        "poly": POLY,
    }


def build_tiny_nested() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Tiny shape/nested demo only (binary-valued 0/1 subset of GF32 values, never claimed as GF32 production matrices): 4/6/8 rows over 8 columns, prefix nested."""
    n = 8
    h_total = np.eye(8, n, dtype=np.uint8)
    h_base = h_total[:4].copy()
    h_joint = h_total[:6].copy()
    return h_base, h_joint, h_total


def _gf2_rank(mat: np.ndarray) -> int:
    a = np.asarray(mat, dtype=np.uint8).copy() & 1
    m, n = a.shape
    rank = 0
    row = 0
    for col in range(n):
        piv = -1
        for r in range(row, m):
            if a[r, col]:
                piv = r
                break
        if piv < 0:
            continue
        a[[row, piv]] = a[[piv, row]]
        for r in range(m):
            if r != row and a[r, col]:
                a[r] ^= a[row]
        row += 1
        rank += 1
        if row >= m:
            break
    return rank


def _smooth_counts(counts: np.ndarray, lam: float) -> np.ndarray:
    c = np.asarray(counts, dtype=np.float64)
    if c.ndim != 2 or c.shape[1] <= 0:
        raise ValueError("counts must be 2-D with positive width")
    if not np.all(c >= 0) or not np.all(np.isfinite(c)):
        raise ValueError("counts must be finite nonnegative")
    lam_f = float(lam)
    if not np.isfinite(lam_f) or lam_f <= 0:
        raise ValueError("lam must be finite positive")
    total = float(c.sum())
    if total <= 0:
        raise ValueError("counts are all zero")
    n_b = c.sum(axis=1).astype(np.float64)
    p_global = c.sum(axis=0).astype(np.float64) / total
    out = np.empty_like(c, dtype=np.float64)
    for i in range(c.shape[0]):
        if n_b[i] == 0:
            out[i] = p_global
        else:
            out[i] = (c[i] + lam_f * p_global) / (n_b[i] + lam_f)
    out = np.maximum(out, 0.0)
    out /= out.sum(axis=1, keepdims=True)
    return out


def build_stage1_P(
    bob_cal: np.ndarray,
    high_cal: np.ndarray,
    lam: float,
    n_b_states: int = Q,
    q_sub: int = Q_SUB,
) -> np.ndarray:
    """Synthetic-only P(high|B)=P(U1|B); production SHALL use get_l1_prior_production."""
    b = np.asarray(bob_cal, dtype=np.int64).reshape(-1)
    h = np.asarray(high_cal, dtype=np.int64).reshape(-1)
    if b.shape != h.shape or b.size == 0:
        raise ValueError("CAL arrays must be non-empty equal length")
    nb, qs = int(n_b_states), int(q_sub)
    if nb <= 0 or qs <= 0:
        raise ValueError("state sizes must be positive")
    if np.any(b < 0) or np.any(b >= nb) or np.any(h < 0) or np.any(h >= qs):
        raise ValueError("CAL values outside declared ranges")
    counts = np.zeros((nb, qs), dtype=np.float64)
    np.add.at(counts, (b, h), 1.0)
    return _smooth_counts(counts, lam)


def build_stage2_P(
    high_cal: np.ndarray,
    bob_cal: np.ndarray,
    low_cal: np.ndarray,
    lam: float,
    n_b_states: int = Q,
    q_sub: int = Q_SUB,
) -> np.ndarray:
    """Synthetic-only P(low|high,B)=P(U2|U1,B); production L2 prior is q@P."""
    hi = np.asarray(high_cal, dtype=np.int64).reshape(-1)
    b = np.asarray(bob_cal, dtype=np.int64).reshape(-1)
    lo = np.asarray(low_cal, dtype=np.int64).reshape(-1)
    if not (hi.shape == b.shape == lo.shape) or b.size == 0:
        raise ValueError("CAL arrays must be non-empty equal length")
    nb, qs = int(n_b_states), int(q_sub)
    if nb <= 0 or qs <= 0:
        raise ValueError("state sizes must be positive")
    if np.any(hi < 0) or np.any(hi >= qs) or np.any(b < 0) or np.any(b >= nb):
        raise ValueError("conditioning values outside declared ranges")
    if np.any(lo < 0) or np.any(lo >= qs):
        raise ValueError("low values outside 0..q_sub-1")
    counts = np.zeros((qs, nb, qs), dtype=np.float64)
    for t in range(b.size):
        counts[int(hi[t]), int(b[t]), int(lo[t])] += 1.0
    total = float(counts.sum())
    if total <= 0:
        raise ValueError("counts are all zero")
    p_global = counts.sum(axis=(0, 1)).astype(np.float64) / total
    lam_f = float(lam)
    if not np.isfinite(lam_f) or lam_f <= 0:
        raise ValueError("lam must be finite positive")
    out = np.empty_like(counts)
    for a in range(qs):
        for bidx in range(nb):
            n_row = float(counts[a, bidx].sum())
            if n_row == 0:
                out[a, bidx] = p_global
            else:
                out[a, bidx] = (counts[a, bidx] + lam_f * p_global) / (n_row + lam_f)
            s = float(out[a, bidx].sum())
            if s <= 0 or not np.isfinite(s):
                raise ValueError("smoothing produced invalid row")
            out[a, bidx] /= s
    return out


def prior_logp_from_P(prob: np.ndarray) -> np.ndarray:
    p = np.asarray(prob, dtype=np.float64)
    if np.any(~np.isfinite(p)):
        raise ValueError("probability table must be finite")
    return np.log(np.maximum(p, PROB_FLOOR))


def ce_stage1_log2(
    p_stage1: np.ndarray, bob_eval: np.ndarray, high_eval: np.ndarray
) -> float:
    p = np.asarray(p_stage1, dtype=np.float64)
    b = np.asarray(bob_eval, dtype=np.int64).reshape(-1)
    h = np.asarray(high_eval, dtype=np.int64).reshape(-1)
    if b.shape != h.shape or b.size == 0:
        raise ValueError("eval arrays must be non-empty equal length")
    vals = np.maximum(p[b, h], PROB_FLOOR)
    return float(-np.mean(np.log2(vals)))


def ce_stage2_log2(
    p_stage2: np.ndarray,
    high_eval: np.ndarray,
    bob_eval: np.ndarray,
    low_eval: np.ndarray,
) -> float:
    p = np.asarray(p_stage2, dtype=np.float64)
    hi = np.asarray(high_eval, dtype=np.int64).reshape(-1)
    b = np.asarray(bob_eval, dtype=np.int64).reshape(-1)
    lo = np.asarray(low_eval, dtype=np.int64).reshape(-1)
    if not (hi.shape == b.shape == lo.shape) or b.size == 0:
        raise ValueError("eval arrays must be non-empty equal length")
    vals = np.maximum(p[hi, b, lo], PROB_FLOOR)
    return float(-np.mean(np.log2(vals)))


def ce_joint_log2(
    p_stage1: np.ndarray,
    p_stage2: np.ndarray,
    bob_eval: np.ndarray,
    high_eval: np.ndarray,
    low_eval: np.ndarray,
) -> float:
    p1 = np.asarray(p_stage1, dtype=np.float64)
    p2 = np.asarray(p_stage2, dtype=np.float64)
    b = np.asarray(bob_eval, dtype=np.int64).reshape(-1)
    hi = np.asarray(high_eval, dtype=np.int64).reshape(-1)
    lo = np.asarray(low_eval, dtype=np.int64).reshape(-1)
    if not (b.shape == hi.shape == lo.shape) or b.size == 0:
        raise ValueError("eval arrays must be non-empty equal length")
    joint = np.maximum(p1[b, hi], PROB_FLOOR) * np.maximum(p2[hi, b, lo], PROB_FLOOR)
    joint = np.maximum(joint, PROB_FLOOR)
    return float(-np.mean(np.log2(joint)))


def run_g_layer(
    prior_logp: np.ndarray,
    syndrome_target: np.ndarray,
    h_matrix: np.ndarray,
    max_iter: int = MAX_ITER,
    damping_alpha: float = DAMPING_ALPHA,
    belief_warm: np.ndarray | None = None,
    bob_layer: np.ndarray | None = None,
    field: Any = None,
    decode_fn: Any = None,
) -> dict[str, Any]:
    """One GF32 stage via the true history kernel (cold default).

    Production path (decode_fn=None) directly calls v35
    decode_row_layered_fftqspa; no argmax impersonation, no fixed hard,
    no hard-coded iters, no simplified decoder. belief_warm is only an
    initial log-belief value (R4); production always passes None (cold,
    matching V54). decode_fn is test-only injection (explicit fake) and
    SHALL NOT be used by production.
    """
    import time as _time

    if isinstance(max_iter, bool) or not isinstance(max_iter, int):
        raise ValueError("max_iter must be an integer")
    if int(max_iter) < 1 or int(max_iter) > MAX_ITER:
        raise ValueError(f"max_iter must lie in 1..{MAX_ITER}")
    if float(damping_alpha) != float(DAMPING_ALPHA):
        raise ValueError("damping_alpha is frozen at 1.0")
    prior = np.asarray(prior_logp, dtype=np.float64)
    if prior.ndim != 2 or prior.shape[1] != Q_SUB or prior.shape[0] == 0:
        raise ValueError("prior_logp must have shape (n,32)")
    if not np.all(np.isfinite(prior)):
        raise ValueError("prior_logp must be finite")
    # History kernel takes probability-domain prior P(X); convert log->P.
    # ponytail: exp/log roundtrip here is the explicit CE/log2 bridge.
    prior_p = np.exp(prior)
    prior_p = np.maximum(prior_p, 1e-15)
    prior_p /= prior_p.sum(axis=1, keepdims=True)
    target = np.asarray(syndrome_target, dtype=np.uint8).reshape(-1)
    h_mat = np.asarray(h_matrix, dtype=np.uint8)
    if h_mat.ndim != 2 or h_mat.shape[1] != prior.shape[0]:
        raise ValueError("H width must equal variable count")
    if target.shape[0] != h_mat.shape[0]:
        raise ValueError("syndrome length must equal row count")
    fld = field if field is not None else get_gf32_field()
    warm = None
    if belief_warm is not None:
        warm = np.asarray(belief_warm, dtype=np.float64)
        if warm.shape != prior.shape:
            raise ValueError("belief_warm must match prior shape (n,32)")
        if not np.all(np.isfinite(warm)):
            raise ValueError("belief_warm must be finite")
    t0 = _time.perf_counter()
    if decode_fn is not None:
        # Test-only explicit fake path; production never passes decode_fn.
        res = decode_fn(h_mat, prior_p, target)
        x_hat = np.asarray(res["x_hat"], dtype=np.int64).reshape(-1) & 31
        iterations_used = int(res.get("iterations_used", res.get("iterations", 0)))
        syndrome_ok_kernel = bool(res.get("syndrome_ok", False))
        runtime_s = float(res.get("runtime_s", _time.perf_counter() - t0))
        stop = str(res.get("stop", res.get("status", "fake")))
        final_beliefs = res.get("final_beliefs", None)
        finite = bool(np.all(np.isfinite(final_beliefs))) if final_beliefs is not None else True
        if final_beliefs is None:
            final_beliefs = np.log(prior_p)
    else:
        dec = history_decoder_fn()
        out = dec(
            h_mat,
            prior_p,
            target,
            max_iter=int(max_iter),
            damping_alpha=float(damping_alpha),
            warm_beliefs=warm,
            field=fld,
        )
        x_hat = np.asarray(out.x_hat, dtype=np.int64).reshape(-1) & 31
        syndrome_ok_kernel = bool(out.syndrome_ok)
        iterations_used = int(out.iterations)
        runtime_s = float(out.runtime_s)
        stop = str(out.status)
        final_beliefs = np.asarray(out.final_beliefs, dtype=np.float64)
        finite = bool(np.all(np.isfinite(final_beliefs)))
    if not 0 <= iterations_used <= int(max_iter):
        raise ValueError("history kernel returned out-of-range iterations")
    syndrome_observed = np.asarray(
        gf32_syndrome(h_mat, x_hat.astype(np.uint8), fld), dtype=np.uint8
    )
    syndrome_ok = bool(
        finite and syndrome_ok_kernel and np.array_equal(syndrome_observed, target & 31)
    )
    if bob_layer is not None:
        bob_arr = np.asarray(bob_layer).reshape(-1)
        if bob_arr.shape != x_hat.shape:
            raise ValueError("bob_layer length must equal variable count")
        vs_bob = int(np.count_nonzero(x_hat != bob_arr))
        candidate_changed = bool(vs_bob > 0)
    else:
        vs_bob = None
        candidate_changed = None
    return {
        # R3 diagnostics (production truth, no fabrication).
        "x_hat": x_hat.astype(np.int64),
        "syndrome_observed": syndrome_observed.astype(np.uint8),
        "syndrome_ok": syndrome_ok,
        "iterations_used": int(iterations_used),
        "residual": RESIDUAL_NOT_RECORDED,
        "finite": finite,
        "runtime_s": float(runtime_s),
        "stop": stop,
        "candidate_changed": candidate_changed,
        "vs_bob": vs_bob,
        "cold_start": bool(belief_warm is None),
        # L1->L2 recombination input: q=softmax(final_beliefs) via V54.
        "final_beliefs": np.asarray(final_beliefs, dtype=np.float64),
        # Back-compat aliases for the frozen D6 contract: views of
        # x_hat/iterations_used/syndrome_ok, not separate measurements.
        "hard": x_hat.astype(np.int64),
        "iters": int(iterations_used),
        "syndrome_satisfied": bool(syndrome_ok),
        "max_iter": int(max_iter),
        "damping_alpha": float(damping_alpha),
    }


def run_l1_stage(
    h1: np.ndarray,
    prior_u1: np.ndarray,
    syndrome_u1: np.ndarray,
    bob_u1: np.ndarray | None = None,
    field: Any = None,
    decode_fn: Any = None,
) -> dict[str, Any]:
    """V54 L1 stage: H1 + P(U1|B), cold start, true kernel only."""
    logp = np.log(np.maximum(np.asarray(prior_u1, dtype=np.float64), 1e-15))
    return run_g_layer(
        logp,
        np.asarray(syndrome_u1, dtype=np.uint8),
        np.asarray(h1, dtype=np.uint8),
        max_iter=MAX_ITER,
        damping_alpha=DAMPING_ALPHA,
        belief_warm=None,
        bob_layer=bob_u1,
        field=field,
        decode_fn=decode_fn,
    )


def run_l2_incremental_chain(
    h_base: np.ndarray,
    h_joint: np.ndarray,
    h_total: np.ndarray,
    prior_l2: np.ndarray,
    syndrome_base: np.ndarray,
    syndrome_joint: np.ndarray,
    syndrome_total: np.ndarray,
    bob_u2: np.ndarray | None = None,
    field: Any = None,
    decode_fn: Any = None,
) -> dict[str, Any]:
    """V54 L2 chain: base->joint->total, same prior_l2=q@P, cold each stage.

    Frozen history order with short-circuit: base verify skips joint and
    total; joint verify skips total. Each stage is an independent cold
    start (belief_warm=None); belief carry is forbidden.
    """
    logp = np.log(np.maximum(np.asarray(prior_l2, dtype=np.float64), 1e-15))
    base = run_g_layer(
        logp, syndrome_base, h_base, belief_warm=None,
        bob_layer=bob_u2, field=field, decode_fn=decode_fn,
    )
    stages: dict[str, Any] = {"base": base}
    skipped: dict[str, bool] = {"joint": False, "total": False}
    if bool(base["syndrome_ok"]):
        skipped["joint"] = True
        skipped["total"] = True
        stages["joint"] = None
        stages["total"] = None
        return {"stages": stages, "skipped": skipped, "final": base}
    joint = run_g_layer(
        logp, syndrome_joint, h_joint, belief_warm=None,
        bob_layer=bob_u2, field=field, decode_fn=decode_fn,
    )
    stages["joint"] = joint
    if bool(joint["syndrome_ok"]):
        skipped["total"] = True
        stages["total"] = None
        return {"stages": stages, "skipped": skipped, "final": joint}
    total = run_g_layer(
        logp, syndrome_total, h_total, belief_warm=None,
        bob_layer=bob_u2, field=field, decode_fn=decode_fn,
    )
    stages["total"] = total
    return {"stages": stages, "skipped": skipped, "final": total}


def binary_syndrome(h_matrix: np.ndarray, bits: np.ndarray) -> np.ndarray:
    """Arm A binary-baseline syndrome only; G layers SHALL use gf32_syndrome."""
    h_mat = np.asarray(h_matrix, dtype=np.uint8) & 1
    x = np.asarray(bits, dtype=np.uint8).reshape(-1) & 1
    if h_mat.ndim != 2 or x.shape[0] != h_mat.shape[1]:
        raise ValueError("H/bits shapes are inconsistent")
    return ((h_mat.astype(np.int64) @ x.astype(np.int64)) & 1).astype(np.uint8)


def gf32_prefix_violation(
    h_matrix: np.ndarray, x_hat: np.ndarray, target: np.ndarray, rows: int, field: Any = None
) -> int:
    """G-layer GF32 prefix violation weight via the history syndrome."""
    r = int(rows)
    h_mat = np.asarray(h_matrix, dtype=np.uint8)
    xh = np.asarray(x_hat, dtype=np.uint8).reshape(-1)
    tgt = np.asarray(target, dtype=np.uint8).reshape(-1)
    if r < 0 or r > h_mat.shape[0] or r > tgt.shape[0]:
        raise ValueError("prefix rows outside available range")
    if xh.shape[0] != h_mat.shape[1]:
        raise ValueError("x_hat length must equal matrix width")
    if r == 0:
        return 0
    obs = gf32_syndrome(h_mat[:r], xh, field)
    return int(np.count_nonzero((obs ^ tgt[:r]) & 31))


def prefix_violation(
    h_matrix: np.ndarray, hard_bits: np.ndarray, target: np.ndarray, rows: int
) -> int:
    """Arm A binary prefix violation only; G layers SHALL use gf32_prefix_violation."""
    r = int(rows)
    h_mat = np.asarray(h_matrix, dtype=np.uint8)
    hard = np.asarray(hard_bits, dtype=np.uint8).reshape(-1)
    tgt = np.asarray(target, dtype=np.uint8).reshape(-1)
    if r < 0 or r > h_mat.shape[0] or r > tgt.shape[0]:
        raise ValueError("prefix rows outside available range")
    if hard.shape[0] != h_mat.shape[1]:
        raise ValueError("hard-bit length must equal matrix width")
    if r == 0:
        return 0
    obs = binary_syndrome(h_mat[:r], hard)
    return int(np.count_nonzero((obs ^ tgt[:r]) & 1))


def tag_probe_readonly(x1: np.ndarray, x2: np.ndarray) -> str:
    """Read-only history tag helper probe; never counted as leakage, never enters syndrome/decoder gating (strict: missing helper raises, no fallback)."""
    try:
        from comparison_bench.formal_ir.v35_algorithm_development import (
            compute_tag_64 as _tag,
        )
    except ImportError:
        from comparison_bench.src.comparison_bench.formal_ir.v35_algorithm_development import (
            compute_tag_64 as _tag,
        )
    return str(_tag(np.asarray(x1), np.asarray(x2)))


def direct_flips(candidate: np.ndarray, bob: np.ndarray) -> int:
    c = np.asarray(candidate).reshape(-1)
    b = np.asarray(bob).reshape(-1)
    if c.shape != b.shape:
        raise ValueError("candidate/bob shapes differ")
    return int(np.count_nonzero(c != b))


def leak_for_m(m_total: int) -> int:
    # Canonical V54 total form 5*m_total+64 where m_total already includes H1
    # (1M: 184+16=200 -> 1064; 192+16=208 -> 1104; 200+16=216 -> 1144).
    # L2-only rows 184/192/200 use leak_for_base instead; do not pass L2-only
    # rows here (leak_for_m(192)=1024 would be wrong).
    return int(5 * int(m_total) + 64)


def leak_for_base(m_base: int) -> int:
    # V54 base: 5*m2 + 5*16 + 64 = 5*m_base + 80 + 64
    # (184 -> 1064; 192 -> 1104; 200 -> 1144 for the 1M nested ladder).
    return int(5 * int(m_base) + 80 + 64)


def leak_for_source_v54(source: str) -> tuple[int, int, int]:
    """Exact V54 leakage triple (base/stage1/stage2) without reimplementing."""
    v54 = _load_v54()
    return (
        int(v54.leak_for(source)),
        int(v54.leak_stage1_for(source)),
        int(v54.leak_stage2_for(source)),
    )


def a_baseline_record() -> dict[str, Any]:
    return {
        "arm": "A",
        "reuse": True,
        "attempted": False,
        "mother": [A_M, A_NBIT],
        "nnz": A_NNZ,
        "ladder_count": A_LADDER_COUNT,
        "ladder_first": A_LADDER_FIRST,
        "ladder_last": A_LADDER_LAST,
        "per_ckpt": A_PER_CKPT,
        "per_arm": A_PER_ARM,
        "dtype": "float64",
        "clip": 20.0,
        "tol": 1e-6,
        "status": "LADDER_EXHAUSTED",
        "iters": 334,
        "bits": 3100,
        "symbols": 620,
        "accounting": [A_M, 64, 71],
        "tag_bits": TAG_BITS,
        "tag_ok": TAG_OK,
    }


def _production_root() -> Path:
    return (
        _repo_root()
        / "comparison_bench"
        / "outputs_comparison"
        / "v72p2d3_gf32_contrast_20260904"
    ).resolve()


def write_contrast_outputs(
    out_dir: str | Path, arm_g: dict[str, Any], arm_a: dict[str, Any] | None = None
) -> Path:
    import csv
    import json

    out = Path(out_dir).resolve()
    prod = _production_root()
    if out == prod or prod in out.parents:
        raise ValueError("synthetic outputs must stay outside the production root")
    if not isinstance(arm_g, dict):
        raise ValueError("arm_g must be a mapping of scalars")
    arm_a = dict(arm_a) if isinstance(arm_a, dict) else a_baseline_record()
    out.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema": "v72p2d3_gf32_contrast_manifest_v1",
        "cycle": CYCLE_ID,
        "base_sha": BASE_SHA,
        "accepted_plan_sha": None,
        "implementation_sha": None,
        "session": SESSION_ID,
        "block": list(VAL_FRAMES),
        "cal": [CAL_START, CAL_END],
        "non_fresh": True,
        "mapping": "low=bits0..4/high=bits5..9/bit0=LSB/symbol=low+32*high=v35-factorize_f03",
        "field": {"q": Q_SUB, "poly": POLY, "unified": "v35-GF2mField"},
        "matrix": {"m_base": M_BASE, "h1": H1_ROWS, "m_total": M_TOTAL},
        "nested": list(NESTED_ROWS),
        "prior": "P(high|B)=P(U1|B)/P(low|high,B)=P(U2|U1,B) CAL-only; production prior_l2=q@P via V54",
        "decoder": "v35-decode_row_layered_fftqspa max90 damping1.0 cold each stage",
        "stage_order": "L1(H1)->base(H_base)->joint(H_joint)->total(H_total) V54 short-circuit",
        "leakage": {"base": LEAK_BASE, "s1": LEAK_S1, "s2": LEAK_S2},
        "tag_bits": TAG_BITS,
        "tag_ok": TAG_OK,
        "history_kernel": HISTORY_KERNEL_ID,
        "synthetic_only": True,
        "claim_boundary": "descriptive GF32 contrast only; no FER/SKR/promotion",
    }
    results = {
        "schema": "v72p2d3_gf32_contrast_results_v1",
        "cycle": CYCLE_ID,
        "non_fresh": True,
        "tag_bits": TAG_BITS,
        "tag_ok": TAG_OK,
        "arms": {"A": dict(arm_a), "G": dict(arm_g)},
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    fields = ["arm", "status", "rows", "iters", "syndrome_satisfied", "bit_flips", "symbol_flips"]
    with (out / "table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for arm_id, arm in (("A", arm_a), ("G", arm_g)):
            writer.writerow(
                {
                    "arm": arm_id,
                    "status": arm.get("status"),
                    "rows": arm.get("rows"),
                    "iters": arm.get("iters"),
                    "syndrome_satisfied": arm.get("syndrome_satisfied"),
                    "bit_flips": arm.get("bit_flips"),
                    "symbol_flips": arm.get("symbol_flips"),
                }
            )
    lines = [
        "# V72P2D3 GF32 contrast (synthetic-only)",
        "",
        "Descriptive only; no FER/SKR/information-limit/promotion claim.",
        "",
        f"- cycle: `{CYCLE_ID}`",
        f"- history_kernel: `{HISTORY_KERNEL_ID}`",
        f"- mapping: `symbol=low+32*high`",
        f"- tag: `{TAG_BITS}/{TAG_OK}`",
    ]
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    names = {item.name for item in out.iterdir()}
    if names != {"manifest.json", "results.json", "table.csv", "report.md"}:
        raise RuntimeError("contrast output root must contain exactly four files")
    return out


def require_real_gate(
    *,
    execute_real: bool,
    authorized: bool,
    preflight: dict[str, Any] | None,
    out_dir: str | Path,
    workspace_root: str | Path | None = None,
    allow_production_root: bool = False,
) -> dict[str, Any]:
    """Step 1: authorization / preflight / output check (no data touched).

    R3: the exact pre-registered production root passes only with
    allow_production_root=True (execute-real production entry); any other
    production path stays rejected and an existing root still refuses.
    """
    if not execute_real:
        raise PermissionError("real chain requires execute_real")
    if not authorized:
        raise PermissionError("real execution is not authorized")
    if not isinstance(preflight, dict) or preflight.get("status") != "PASS":
        raise PermissionError("synthetic preflight PASS artifact is required")
    if preflight.get("cycle") != CYCLE_ID and preflight.get("cycle_id") != CYCLE_ID:
        raise PermissionError("preflight belongs to another cycle")
    out = Path(out_dir).resolve()
    prod = _production_root()
    prod_exact_allowed = bool(allow_production_root) and out == prod
    if (out == prod or prod in out.parents) and not prod_exact_allowed:
        raise ValueError("fake-E2E output must stay outside the production root")
    if workspace_root is not None and not prod_exact_allowed:
        try:
            out.relative_to(Path(workspace_root).resolve())
        except ValueError as exc:
            raise ValueError("fake-E2E output must stay under workspace/") from exc
    if out.exists():
        raise FileExistsError(f"output directory already exists: {out}")
    return {"gate": "PASS"}


def validate_registry(registry: dict[str, Any]) -> dict[str, Any]:
    """Step 2: registry check — one 1M session, CAL702..1725, block VAL1726..1729."""
    if not isinstance(registry, dict):
        raise ValueError("registry must be a mapping")
    sessions = registry.get("sessions", [])
    found = [
        s
        for s in sessions
        if isinstance(s, dict)
        and s.get("session_id") == SESSION_ID
        and s.get("source_label") == "1M"
    ]
    if len(found) != 1:
        raise ValueError("registry must contain exactly one target 1M session")
    session = found[0]
    cal_ids = [int(v) for v in session.get("stage2_CAL_frame_ids", [])]
    if cal_ids != list(REAL_CAL_IDS):
        raise ValueError("CAL assignment is not the frozen 702..1725 sequence")
    val_ids = [int(v) for v in session.get("stage2_VAL_frame_ids", [])]
    if val_ids[:4] != list(REAL_BLOCK_IDS):
        raise ValueError("VAL assignment does not start with frozen 1726..1729")
    # Single fixed block only; never loop VAL groups here (no nine-block runner).
    return {
        "session": dict(session),
        "cal_ids": cal_ids,
        "block_ids": list(REAL_BLOCK_IDS),
    }


def validate_frame_bundle(
    frames: dict[Any, Any], frame_ids: list[int]
) -> dict[int, dict[str, np.ndarray]]:
    """Step 3: CAL/VAL loading validation — 256 integral symbols 0..1023/frame."""
    if not isinstance(frames, dict):
        raise ValueError("frames must be a mapping")
    bundle: dict[int, dict[str, np.ndarray]] = {}
    for fid in frame_ids:
        rec = frames.get(int(fid), frames.get(str(fid)))
        if not isinstance(rec, dict):
            raise ValueError(f"frame {fid} is missing")
        alice = np.asarray(rec["alice_symbols"]).reshape(-1)
        bob = np.asarray(rec["bob_symbols"]).reshape(-1)
        if alice.shape != (FRAME_PAIRS,) or bob.shape != (FRAME_PAIRS,):
            raise ValueError(f"frame {fid} must hold {FRAME_PAIRS} pairs")
        for arr in (alice, bob):
            if np.any(arr < 0) or np.any(arr >= Q):
                raise ValueError(f"frame {fid} symbol outside 0..1023")
            if not np.all(arr == np.floor(arr.astype(np.float64))):
                raise ValueError(f"frame {fid} has non-integral symbols")
        bundle[int(fid)] = {
            "alice_symbols": alice.astype(np.int64),
            "bob_symbols": bob.astype(np.int64),
        }
    return bundle


def fit_cal_prior_from_frames(
    cal_bundle: dict[int, dict[str, np.ndarray]], lam: float = FAKE_E2E_LAM
) -> dict[str, Any]:
    """Step 4: CAL-only fit — P1(high|B), P2(low|high,B), V54 counts (no VAL)."""
    if len(cal_bundle) == 0:
        raise ValueError("CAL bundle must be non-empty")
    a_cal = np.concatenate([cal_bundle[f]["alice_symbols"] for f in sorted(cal_bundle)])
    b_cal = np.concatenate([cal_bundle[f]["bob_symbols"] for f in sorted(cal_bundle)])
    a_low, a_high = symbols_to_layers(a_cal)
    _, _ = symbols_to_layers(b_cal)
    p1 = build_stage1_P(b_cal, a_high, float(lam), n_b_states=Q, q_sub=Q_SUB)
    p2 = build_stage2_P(a_high, b_cal, a_low, float(lam), n_b_states=Q, q_sub=Q_SUB)
    counts = np.zeros((Q, Q), dtype=np.float64)
    np.add.at(counts, (b_cal.astype(np.int64), a_cal.astype(np.int64)), 1.0)
    if float(counts.sum()) <= 0:
        raise ValueError("CAL counts are all zero")
    return {
        "P1": p1,
        "P2": p2,
        "counts": counts,
        "lam": float(lam),
        "n_cal": int(a_cal.size),
    }


def assemble_block_frames(
    bundle: dict[int, dict[str, np.ndarray]], block_ids: list[int]
) -> tuple[np.ndarray, np.ndarray]:
    """Step 5:拼块 — four consecutive VAL frames into one 1024-symbol block."""
    if list(block_ids) != list(REAL_BLOCK_IDS):
        raise ValueError("block must be the frozen VAL1726..1729")
    alice = np.concatenate([bundle[int(f)]["alice_symbols"] for f in block_ids])
    bob = np.concatenate([bundle[int(f)]["bob_symbols"] for f in block_ids])
    if alice.shape != (N,) or bob.shape != (N,):
        raise ValueError("a four-frame block must contain 1024 symbols")
    return alice.astype(np.int64), bob.astype(np.int64)


def validate_nested_matrices(
    h1: np.ndarray,
    h_base: np.ndarray,
    h_joint: np.ndarray,
    h_total: np.ndarray,
) -> dict[str, Any]:
    """Step 8: matrix check — shapes, nested prefix, row weight cap (GF32 values)."""
    mats = {
        "h1": (np.asarray(h1, dtype=np.uint8), (H1_ROWS, N)),
        "h_base": (np.asarray(h_base, dtype=np.uint8), (M_BASE, N)),
        "h_joint": (np.asarray(h_joint, dtype=np.uint8), (M_BASE + 8, N)),
        "h_total": (np.asarray(h_total, dtype=np.uint8), (M_TOTAL, N)),
    }
    for name, (mat, shape) in mats.items():
        if mat.shape != shape:
            raise ValueError(f"{name} shape must be {shape}, got {mat.shape}")
        if mat.max() >= Q_SUB:
            raise ValueError(f"{name} holds values outside GF32")
        if int((mat != 0).sum(axis=1).max()) > 16:
            raise ValueError(f"{name} row weight exceeds 16")
    h1m, hbm = mats["h1"][0], mats["h_base"][0]
    hjm, htm = mats["h_joint"][0], mats["h_total"][0]
    if not (np.array_equal(hjm[:M_BASE], hbm) and np.array_equal(htm[:M_BASE], hbm)):
        raise ValueError("nested prefix 184 does not match H_base")
    if not np.array_equal(htm[: M_BASE + 8], hjm):
        raise ValueError("nested prefix 192 does not match H_joint")
    return {"rows": (H1_ROWS, M_BASE, M_BASE + 8, M_TOTAL), "nested": list(NESTED_ROWS)}


def _sample_rss(rss_reader: Any = None) -> int | None:
    if rss_reader is not None:
        try:
            return int(rss_reader())
        except Exception:
            return None
    try:
        import psutil as _psutil
        import os as _os

        return int(_psutil.Process(_os.getpid()).memory_info().rss)
    except Exception:
        return None


def run_real_contrast(
    *,
    out_dir: str | Path,
    registry: dict[str, Any],
    frames: dict[Any, Any],
    matrices: dict[str, np.ndarray],
    preflight: dict[str, Any] | None = None,
    authorized: bool = False,
    execute_real: bool = True,
    decode_fn: Any = None,
    lam: float = FAKE_E2E_LAM,
    clock: Any = None,
    rss_reader: Any = None,
    workspace_root: str | Path | None = None,
    allow_production_root: bool = False,
) -> dict[str, Any]:
    """Run the frozen 11-step real-entry chain on injected fakes (no parquet).

    Order: gate -> registry -> CAL/VAL validate -> fit -> assemble block ->
    A reuse -> words -> matrices -> syndromes -> true kernel -> reassemble ->
    posthoc -> four files. Production calls pass decode_fn=None (true v35
    kernel, cold each stage); tests pass an explicit fake decode_fn.
    """
    import time as _time

    now = clock if clock is not None else _time.monotonic
    inv_start = float(now())
    rss_peak: list[int] = []

    def _sample() -> None:
        value = _sample_rss(rss_reader)
        if value is not None:
            rss_peak.append(int(value))

    _sample()
    prep_start = float(now())
    gate = require_real_gate(
        execute_real=execute_real,
        authorized=authorized,
        preflight=preflight,
        out_dir=out_dir,
        workspace_root=workspace_root,
        allow_production_root=allow_production_root,
    )
    reg = validate_registry(registry)
    cal_ids, block_ids = reg["cal_ids"], reg["block_ids"]
    cal_provided = sorted({int(f) for f in frames} & set(cal_ids))
    if len(cal_provided) == 0:
        raise ValueError("frames hold no CAL frame in 702..1725")
    cal_bundle = validate_frame_bundle(frames, cal_provided)
    block_bundle = validate_frame_bundle(frames, block_ids)
    fit = fit_cal_prior_from_frames(cal_bundle, lam)
    alice, bob = assemble_block_frames(block_bundle, block_ids)
    # Step 6: A只读复用 — never rerun.
    arm_a = a_baseline_record()
    if arm_a.get("attempted") is not False:
        raise ValueError("Arm A must stay read-only reuse")
    # Step 7: words — symbols_to_layers, direction bound to v35 factorize_f03.
    alice_low, alice_high = symbols_to_layers(alice)
    bob_low, bob_high = symbols_to_layers(bob)
    u1, u2, _, _ = factorize_f03_binding(alice, bob)
    if not (
        np.array_equal(u1.astype(np.int64), alice_high)
        and np.array_equal(u2.astype(np.int64), alice_low)
    ):
        raise ValueError("word direction disagrees with v35 factorize_f03")
    geo = validate_nested_matrices(
        matrices["h1"], matrices["h_base"], matrices["h_joint"], matrices["h_total"]
    )
    field = get_gf32_field()
    h1 = np.asarray(matrices["h1"], dtype=np.uint8)
    h_base = np.asarray(matrices["h_base"], dtype=np.uint8)
    h_joint = np.asarray(matrices["h_joint"], dtype=np.uint8)
    h_total = np.asarray(matrices["h_total"], dtype=np.uint8)
    # Step 9: syndromes, Alice side only, via the history GF32 oracle.
    s1 = gf32_syndrome(h1, alice_high.astype(np.uint8), field)
    s_base = gf32_syndrome(h_base, alice_low.astype(np.uint8), field)
    s_joint = gf32_syndrome(h_joint, alice_low.astype(np.uint8), field)
    s_total = gf32_syndrome(h_total, alice_low.astype(np.uint8), field)
    # Production prior order: P(U1|B) then q@P (exact V54 reuse).
    counts = np.asarray(fit["counts"], dtype=np.float64)
    prior_u1 = get_l1_prior_production(counts, bob)
    prep_wall = float(now()) - prep_start
    _sample()
    if prep_wall > PREP_LIMIT_S:
        raise TimeoutError(f"prep wall {prep_wall:.3f}s exceeds {PREP_LIMIT_S}s")
    # Step 10:真核 — L1 cold, then L2 chain cold (production decode_fn=None).
    g_start = float(now())
    l1 = run_l1_stage(
        h1, prior_u1, s1, bob_u1=bob_high, field=field, decode_fn=decode_fn
    )
    # Frozen recombination: q=softmax(L1 final_beliefs), then prior_l2=q@P.
    q = softmax_beliefs_history(np.asarray(l1["final_beliefs"], dtype=np.float64))
    prior_l2 = build_l2_prior_from_l1(counts, bob, q)
    chain = run_l2_incremental_chain(
        h_base,
        h_joint,
        h_total,
        prior_l2,
        s_base,
        s_joint,
        s_total,
        bob_u2=bob_low,
        field=field,
        decode_fn=decode_fn,
    )
    g_wall = float(now()) - g_start
    _sample()
    if g_wall > G_LIMIT_S:
        raise TimeoutError(f"G wall {g_wall:.3f}s exceeds {G_LIMIT_S}s")
    final = chain["final"]
    # Step 11a:重组 — layers_to_symbols (+ q already recombined above).
    final_u1 = np.asarray(l1["x_hat"], dtype=np.int64).reshape(-1)
    final_u2 = np.asarray(final["x_hat"], dtype=np.int64).reshape(-1)
    final_symbols = layers_to_symbols(final_u2, final_u1)
    if not np.array_equal(
        layers_to_symbols(*symbols_to_layers(final_symbols)), final_symbols
    ):
        raise ValueError("reassembly roundtrip failed")
    # Step 11b: posthoc oracle (final candidate only, after arm end).
    vs_bob = direct_flips(final_symbols, bob)
    vs_alice = direct_flips(final_symbols, alice)
    oracle_exact = bool(np.array_equal(final_symbols, alice))
    final_ok = bool(final["syndrome_ok"])
    # Measurement-only prior-argmax baseline for the IMPROVED branch; it is
    # never fed back into any decoder.
    prior_argmax = layers_to_symbols(
        np.argmax(np.asarray(prior_l2, dtype=np.float64), axis=1).astype(np.int64),
        np.argmax(np.asarray(prior_u1, dtype=np.float64), axis=1).astype(np.int64),
    )
    prior_vs_bob = direct_flips(prior_argmax, bob)
    changed = bool(vs_bob != prior_vs_bob or not np.array_equal(final_symbols, prior_argmax))
    if final_ok and oracle_exact:
        branch = "G_EXACT"
    elif final_ok:
        branch = "G_COLLISION"
    elif changed or vs_bob < prior_vs_bob:
        branch = "G_IMPROVED_NO_SYNDROME"
    else:
        branch = "G_NO_MOTION"
    joint_executed = not bool(chain["skipped"]["joint"])
    total_executed = not bool(chain["skipped"]["total"])
    reached_base = 184 if not joint_executed else (192 if not total_executed else 200)
    leak_bits = leak_for_base(int(reached_base))
    control_bits = int(joint_executed) + int(total_executed)
    arm_g = {
        "status": "SYNDROME_SATISFIED" if final_ok else "LADDER_EXHAUSTED",
        "branch": branch,
        "rows": int(geo["rows"][3]),
        "iters": int(l1["iterations_used"]) + int(final["iterations_used"]),
        "iters_l1": int(l1["iterations_used"]),
        "iters_l2": int(final["iterations_used"]),
        "syndrome_satisfied": bool(final_ok),
        "final_oracle_exact": bool(oracle_exact),
        "bit_flips": int(vs_bob),
        "symbol_flips": int(vs_bob),
        "vs_bob": int(vs_bob),
        "vs_alice": int(vs_alice),
        "prior_vs_bob": int(prior_vs_bob),
        "leak_bits": int(leak_bits),
        "control_bits": int(control_bits),
        "reached_base": int(reached_base),
        "wall_prep_s": float(prep_wall),
        "wall_g_s": float(g_wall),
        "cold_start": bool(l1.get("cold_start", True)),
        "tag_bits": TAG_BITS,
        "tag_ok": TAG_OK,
        "synthetic_only": True,
    }
    written = write_contrast_outputs(out_dir, arm_g, arm_a)
    _sample()
    inv_wall = float(now()) - inv_start
    peak = max(rss_peak) if rss_peak else None
    if inv_wall > INV_LIMIT_S:
        raise TimeoutError(f"invocation wall {inv_wall:.3f}s exceeds {INV_LIMIT_S}s")
    if peak is not None and peak >= RSS_LIMIT_BYTES:
        raise MemoryError("peak RSS exceeds 2GiB")
    return {
        "cycle": CYCLE_ID,
        "gate": gate["gate"],
        "status": arm_g["status"],
        "branch": branch,
        "block_ids": list(block_ids),
        "n_cal_frames": len(cal_provided),
        "n_cal_symbols": int(fit["n_cal"]),
        "arm_a_attempted": False,
        "final_syndrome_satisfied": bool(final_ok),
        "final_oracle_exact": bool(oracle_exact),
        "vs_bob": int(vs_bob),
        "vs_alice": int(vs_alice),
        "leak_bits": int(leak_bits),
        "control_bits": int(control_bits),
        "tag_bits": TAG_BITS,
        "tag_ok": TAG_OK,
        "prep_wall_s": float(prep_wall),
        "g_wall_s": float(g_wall),
        "inv_wall_s": float(inv_wall),
        "peak_rss_bytes": peak,
        "output": str(written),
        "fake_decoder": decode_fn is not None,
    }


# ---------------------------------------------------------------------------
# R2-R6 real-input adaptation, prepare-only (no decoder, no syndrome publish,
# no formal dir, no decoder-auth consumption, no tag/hash).
#
# Frozen chain (prepare-only stops here, decoder_calls == 0):
#   registry JSON -> parquet path -> filtered read (4 cols only) ->
#   CAL/VAL validate -> prior fit -> block assemble -> D1 A scalar ->
#   words -> matrix/syndrome shape validate -> workspace READY.
#
# Registry rules (R2, no checksum/hash/tag):
#   schema/session/parquet-exists/256/CAL702..1725/VAL1726..1729 disjoint/
#   forbid 1730+/used_2m false/columns exist. Extra checksum/hash/tag keys
#   are ignored, never read or computed.
# Parquet rules (R3): 4 cols only, record read/retained rows, validate
#   CAL1024x256 VAL4x256 pair0..255 no-dup/no-NaN symbols0..1023 sorted;
#   data rows never persist to disk (scalars only in summary).
# Summary rules (R4-R6): prepare_summary.json scalars only, formal false,
#   decoder 0, published 0; bans Alice/Bob arrays, prior/syndrome values,
#   matrices values, candidate/messages. A reuses D1 scalars, missing is
#   null+reason, missing inputs is PREP_FAILED. G prep records accepted
#   adapter true-kernel per-stage fields, first-layer failure follows history
#   short-circuit, oracle at end, no protocol field. Budgets prep300/G300/
#   inv600/RSS2GiB phased, overlimit BLOCKED with counts retained.
# ---------------------------------------------------------------------------

REGISTRY_SCHEMA = "v72p2d3_real_registry_v1"
PREPARE_SCHEMA = "v72p2d3_prepare_summary_v1"
REQUIRED_PARQUET_COLUMNS = ("frame_id", "pair_idx", "alice_symbol", "bob_symbol")
PREPARE_LAM = FAKE_E2E_LAM
PREPARE_CAL = [CAL_START, CAL_END]
PREPARE_VAL = [VAL_FRAMES[0], VAL_FRAMES[-1]]
# ponytail: scalar-only summary; shapes/weights are frozen scalars, not data.
PREPARE_BANNED_KEYS = (
    "alice_symbols",
    "bob_symbols",
    "prior_logp",
    "syndrome_target",
    "syndrome_observed",
    "syndrome_bytes",
    "candidate",
    "messages",
    "check_to_variable",
    "alice_bits",
)


def _resolve_prepare_parquet(raw: Any, registry_dir: Path) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("registry parquet_path must be a non-empty string")
    cand = Path(raw.strip())
    if not cand.is_absolute():
        cand = (registry_dir / cand).resolve()
        if not cand.exists():
            alt = (_repo_root() / raw.strip()).resolve()
            if alt.exists():
                cand = alt
    return cand.resolve()


def validate_prepare_registry(
    registry: dict[str, Any], registry_path: str | Path | None = None
) -> dict[str, Any]:
    """R2 registry validation (no checksum/hash/tag read or computed)."""
    if not isinstance(registry, dict):
        raise ValueError("registry must be a mapping")
    if registry.get("schema") != REGISTRY_SCHEMA:
        raise ValueError(f"registry schema must be {REGISTRY_SCHEMA}")
    if registry.get("session_id") != SESSION_ID:
        raise ValueError("registry session_id must be the frozen 1M session")
    if registry.get("source_label") != "1M":
        raise ValueError("registry source_label must be 1M")
    if bool(registry.get("used_2m", False)) is not False:
        raise ValueError("registry used_2m must be false")
    if bool(registry.get("used_2M", False)) is not False:
        raise ValueError("registry used_2M must be false")
    cal_ids = [int(v) for v in registry.get("cal_frame_ids", [])]
    val_ids = [int(v) for v in registry.get("val_frame_ids", [])]
    if cal_ids != list(REAL_CAL_IDS):
        raise ValueError("CAL must be the frozen 702..1725 sequence (1024 frames)")
    if val_ids != list(REAL_BLOCK_IDS):
        raise ValueError("VAL must be the frozen 1726..1729 sequence (4 frames)")
    if set(cal_ids) & set(val_ids):
        raise ValueError("CAL/VAL must be disjoint")
    if any(v >= 1730 for v in cal_ids + val_ids):
        raise ValueError("frame 1730+ is forbidden")
    cols = list(registry.get("columns", []))
    if set(cols) != set(REQUIRED_PARQUET_COLUMNS):
        raise ValueError(f"registry columns must be exactly {list(REQUIRED_PARQUET_COLUMNS)}")
    base_dir = Path(registry_path).resolve().parent if registry_path is not None else _repo_root()
    parquet_path = _resolve_prepare_parquet(registry.get("parquet_path"), base_dir)
    if not parquet_path.is_file():
        raise ValueError(f"registry parquet_path does not exist: {parquet_path}")
    # No checksum/hash/tag: intentionally never read or compute them here.
    return {
        "session_id": SESSION_ID,
        "parquet_path": parquet_path,
        "cal_ids": cal_ids,
        "val_ids": list(val_ids),
        "columns": list(REQUIRED_PARQUET_COLUMNS),
    }


def load_and_validate_prepare_frames(
    parquet_path: str | Path,
    cal_ids: list[int] | None = None,
    val_ids: list[int] | None = None,
) -> dict[str, Any]:
    """R3 filtered parquet read (4 cols only); validates CAL/VAL geometry.

    Returns in-memory bundles for the prepare chain plus scalar counts.
    Data rows are never written to disk by this module; the summary keeps
    scalars only.
    """
    import pandas as pd

    cal = list(REAL_CAL_IDS) if cal_ids is None else [int(v) for v in cal_ids]
    val = list(REAL_BLOCK_IDS) if val_ids is None else [int(v) for v in val_ids]
    if cal != list(REAL_CAL_IDS) or val != list(REAL_BLOCK_IDS):
        raise ValueError("CAL/VAL ids must be the frozen sequences")
    cols = list(REQUIRED_PARQUET_COLUMNS)
    try:
        df = pd.read_parquet(Path(parquet_path), columns=cols)
    except Exception as exc:
        raise ValueError(f"parquet unreadable: {type(exc).__name__}: {exc}") from exc
    n_read = int(len(df))
    if set(df.columns) != set(cols):
        raise ValueError(f"parquet columns must be exactly {cols}")
    if int(df.isna().sum().sum()) != 0:
        raise ValueError("parquet contains NaN")
    for col in cols:
        vals = df[col].to_numpy()
        if not np.all(vals == np.floor(vals.astype(np.float64))):
            raise ValueError(f"parquet column {col} must be integral")
    keep = df[df["frame_id"].isin(cal + val)]
    n_retained = int(len(keep))
    # CAL 1024x256, VAL 4x256.
    if n_retained != 1024 * 256 + 4 * 256:
        raise ValueError(f"retained rows must be 263168, got {n_retained}")
    for fid in cal + val:
        sub = keep[keep["frame_id"] == fid].sort_values("pair_idx")
        if len(sub) != 256:
            raise ValueError(f"frame {fid} must hold 256 rows")
        pairs = sub["pair_idx"].to_numpy(dtype=np.int64)
        if not np.array_equal(pairs, np.arange(256, dtype=np.int64)):
            raise ValueError(f"frame {fid} pair_idx must be sorted 0..255 with no dup")
        for col in ("alice_symbol", "bob_symbol"):
            syms = sub[col].to_numpy(dtype=np.int64)
            if np.any(syms < 0) or np.any(syms >= Q):
                raise ValueError(f"frame {fid} {col} outside 0..1023")
    # In-memory bundles reuse the frozen fake-E2E builders (shared builder).
    frames: dict[int, dict[str, np.ndarray]] = {}
    for fid in cal + val:
        sub = keep[keep["frame_id"] == fid].sort_values("pair_idx")
        frames[int(fid)] = {
            "alice_symbols": sub["alice_symbol"].to_numpy(dtype=np.int64),
            "bob_symbols": sub["bob_symbol"].to_numpy(dtype=np.int64),
        }
    cal_bundle = {f: frames[f] for f in cal}
    val_bundle = {f: frames[f] for f in val}
    return {
        "n_read_rows": n_read,
        "n_retained_rows": n_retained,
        "n_cal_frames": len(cal),
        "n_val_frames": len(val),
        "n_cal_symbols": len(cal) * 256,
        "n_val_symbols": len(val) * 256,
        "cal_bundle": cal_bundle,
        "val_bundle": val_bundle,
    }


def _prepare_g_stages() -> dict[str, Any]:
    """G prep per-stage scalars with accepted adapter true-kernel fields.

    Decoder never runs here (iters 0, stop NOT_ATTEMPTED_PREPARE_ONLY).
    Short-circuit follows history: L1 failure still enters L2 with q;
    L2 base-ok would skip joint/total, joint-ok would skip total. Oracle
    is recorded at the end only (null until a real run). No protocol field.
    """
    stages: dict[str, Any] = {}
    for name, active in (("l1", H1_ROWS), ("base", M_BASE), ("joint", M_BASE + 8), ("total", M_TOTAL)):
        stages[name] = {
            "active": int(active),
            "iters": 0,
            "viol": None,
            "ok": None,
            "changed": None,
            "vs_bob": None,
            "finite": True,
            "runtime_s": 0.0,
            "rss_bytes": None,
            "stop": "NOT_ATTEMPTED_PREPARE_ONLY",
        }
    return {
        "accepted": True,
        "kernel": HISTORY_KERNEL_ID,
        "stages": stages,
        "short_circuit": "l1-fail-still-enters-l2; base-ok-skips-joint-total; joint-ok-skips-total",
        "final_oracle_exact": None,
        "oracle_runs_after_arm_end": True,
    }


def build_prepare_summary(
    *,
    registry_path: str | Path,
    validated: dict[str, Any],
    counts: dict[str, Any],
    fit: dict[str, Any],
    ce: dict[str, float],
    prep_wall_s: float,
    g_wall_s: float,
    inv_wall_s: float,
    peak_rss: int | None,
    status: str,
) -> dict[str, Any]:
    """Assemble the scalar-only prepare summary (no data rows/values)."""
    arm_a = a_baseline_record()
    arm_a = dict(arm_a)
    arm_a["decoder_calls"] = 0
    arm_a["new_metrics"] = None
    arm_a["not_recorded_reason"] = "D1 baseline did not record this metric; A was not rerun"
    summary: dict[str, Any] = {
        "schema": PREPARE_SCHEMA,
        "status": status,
        "registry": str(registry_path),
        "session": SESSION_ID,
        "cal": [CAL_START, CAL_END],
        "val": [VAL_FRAMES[0], VAL_FRAMES[-1]],
        "rows": {
            "n_cal_frames": int(counts["n_cal_frames"]),
            "n_val_frames": int(counts["n_val_frames"]),
            "n_cal_symbols": int(counts["n_cal_symbols"]),
            "n_val_symbols": int(counts["n_val_symbols"]),
            "n_read_rows": int(counts["n_read_rows"]),
            "n_retained_rows": int(counts["n_retained_rows"]),
        },
        "lambda": float(fit["lam"]),
        "ce": {"stage1": float(ce["stage1"]), "stage2": float(ce["stage2"]), "joint": float(ce["joint"])},
        "prior_shapes": {"P1": [Q, Q_SUB], "P2": [Q_SUB, Q, Q_SUB], "counts": [Q, Q]},
        "matrix": {
            "h1": [H1_ROWS, N],
            "h_base": [M_BASE, N],
            "h_joint": [M_BASE + 8, N],
            "h_total": [M_TOTAL, N],
        },
        "nested": list(NESTED_ROWS),
        "syndrome": {
            "s1_len": H1_ROWS,
            "s_base_len": M_BASE,
            "s_joint_len": M_BASE + 8,
            "s_total_len": M_TOTAL,
            "max_row_weight": 16,
        },
        "arm_a": arm_a,
        "arm_g_prep": _prepare_g_stages(),
        "wall": {"prep_s": float(prep_wall_s), "g_s": float(g_wall_s), "inv_s": float(inv_wall_s)},
        "rss": {"peak_bytes": None if peak_rss is None else int(peak_rss)},
        "decoder_calls": 0,
        "published_bits": 0,
        "formal": False,
    }
    return summary


def _check_prepare_summary_allowed(summary: dict[str, Any]) -> None:
    import json as _json

    payload = _json.dumps(summary, ensure_ascii=False)
    lowered = payload.lower()
    for banned in PREPARE_BANNED_KEYS:
        if banned.lower() in lowered:
            raise ValueError(f"prepare summary must not store {banned}")
    if '"protocol"' in lowered:
        raise ValueError("prepare summary must not define protocol")


def prepare_real_input(
    *,
    registry_path: str | Path,
    out_dir: str | Path,
    lam: float = PREPARE_LAM,
    clock: Any = None,
    rss_reader: Any = None,
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    """R2-R6 prepare-only chain (decoder never called, nothing published).

    Writes exactly one file ``prepare_summary.json`` under a fresh workspace
    directory and returns the scalar report. Missing inputs give PREP_FAILED;
    budget overruns give BLOCKED with counts retained.
    """
    import json as _json
    import time as _time

    now = clock if clock is not None else _time.monotonic
    inv_start = float(now())
    rss_peak: list[int] = []

    def _sample() -> None:
        value = _sample_rss(rss_reader)
        if value is not None:
            rss_peak.append(int(value))

    _sample()
    prep_start = float(now())
    out = Path(out_dir).resolve()
    prod = _production_root()
    if out == prod or prod in out.parents:
        raise ValueError("prepare output must stay outside the production root")
    if workspace_root is not None:
        try:
            out.relative_to(Path(workspace_root).resolve())
        except ValueError as exc:
            raise ValueError("prepare output must stay under workspace/") from exc
    if out.exists():
        raise FileExistsError(f"output directory already exists: {out}")
    if out.name == "run_01" or "run_01" in out.parts:
        raise ValueError("prepare output must not be run_01")
    try:
        reg_raw = _json.loads(Path(registry_path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"PREP_FAILED: registry file is missing: {registry_path}") from exc
    try:
        validated = validate_prepare_registry(reg_raw, registry_path)
    except ValueError as exc:
        # Missing/invalid registry contract is PREP_FAILED, not READY/BLOCKED.
        msg = str(exc)
        if "PREP_FAILED" in msg:
            raise
        raise ValueError(f"PREP_FAILED: {exc}") from exc
    loaded = load_and_validate_prepare_frames(
        validated["parquet_path"], validated["cal_ids"], validated["val_ids"]
    )
    fit = fit_cal_prior_from_frames(loaded["cal_bundle"], float(lam))
    a_cal = np.concatenate([loaded["cal_bundle"][f]["alice_symbols"] for f in sorted(loaded["cal_bundle"])])
    b_cal = np.concatenate([loaded["cal_bundle"][f]["bob_symbols"] for f in sorted(loaded["cal_bundle"])])
    a_low, a_high = symbols_to_layers(a_cal)
    ce_s1 = ce_stage1_log2(fit["P1"], b_cal, a_high)
    ce_s2 = ce_stage2_log2(fit["P2"], a_high, b_cal, a_low)
    ce_j = ce_joint_log2(fit["P1"], fit["P2"], b_cal, a_high, a_low)
    ce = {"stage1": float(ce_s1), "stage2": float(ce_s2), "joint": float(ce_j)}
    # Block assemble (VAL1726..1729 -> 1024 symbols, sorted by frame/pair).
    alice, bob = assemble_block_frames(loaded["val_bundle"], validated["val_ids"])
    # D1 A scalar reuse is recorded in the summary; decoder_calls stays 0.
    _arm_a = a_baseline_record()
    if _arm_a.get("attempted") is not False:
        raise ValueError("Arm A must stay read-only reuse")
    # Words direction check (mapping only, no decoder).
    alice_low, alice_high = symbols_to_layers(alice)
    bob_low, bob_high = symbols_to_layers(bob)
    u1, u2, _, _ = factorize_f03_binding(alice, bob)
    if not (
        np.array_equal(u1.astype(np.int64), alice_high)
        and np.array_equal(u2.astype(np.int64), alice_low)
    ):
        raise ValueError("word direction disagrees with v35 factorize_f03")
    # Matrix/syndrome shape validation (frozen geometry scalars only; no
    # syndrome values are computed or published here).
    geo = nested_geometry()
    if tuple(geo["nested"]) != tuple(NESTED_ROWS):
        raise ValueError("nested geometry drift")
    if geo["shapes"] != [(M_BASE, N), (M_BASE + 8, N), (M_TOTAL, N)]:
        raise ValueError("matrix shape drift")
    if (H1_ROWS, M_BASE, M_TOTAL) != (16, 184, 200):
        raise ValueError("matrix shape drift")
    _ = (bob_low, bob_high)
    prep_wall = float(now()) - prep_start
    _sample()
    peak = max(rss_peak) if rss_peak else None
    g_wall = 0.0
    if prep_wall > PREP_LIMIT_S or g_wall > G_LIMIT_S:
        status = "BLOCKED"
    else:
        status = "READY"
    inv_wall = float(now()) - inv_start
    if inv_wall > INV_LIMIT_S:
        status = "BLOCKED"
    if peak is not None and peak >= RSS_LIMIT_BYTES:
        status = "BLOCKED"
    summary = build_prepare_summary(
        registry_path=Path(registry_path).resolve(),
        validated=validated,
        counts=loaded,
        fit=fit,
        ce=ce,
        prep_wall_s=prep_wall,
        g_wall_s=g_wall,
        inv_wall_s=inv_wall,
        peak_rss=peak,
        status=status,
    )
    _check_prepare_summary_allowed(summary)
    out.mkdir(parents=True, exist_ok=False)
    (out / "prepare_summary.json").write_text(
        _json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    names = {item.name for item in out.iterdir()}
    if names != {"prepare_summary.json"}:
        raise RuntimeError("prepare output must contain exactly prepare_summary.json")
    _sample()
    return {
        "status": status,
        "registry": str(Path(registry_path).resolve()),
        "session": SESSION_ID,
        "n_cal_frames": int(loaded["n_cal_frames"]),
        "n_val_frames": int(loaded["n_val_frames"]),
        "n_read_rows": int(loaded["n_read_rows"]),
        "n_retained_rows": int(loaded["n_retained_rows"]),
        "decoder_calls": 0,
        "published_bits": 0,
        "formal": False,
        "prep_wall_s": float(prep_wall),
        "g_wall_s": float(g_wall),
        "inv_wall_s": float(inv_wall),
        "peak_rss_bytes": peak,
        "output": str((out / "prepare_summary.json").resolve()),
    }
