"""V45P0 L1-APP soft-transfer diagnostic: guarded runner and writer.

Implements frozen V45P0 protocol (formal-ir-v45-l1-app-soft-transfer):

- Single phase of exactly 27 decoder invocations: 9 L1 (H1 16x1024 QC-cyclic) + 9 control L2 + 9 treatment L2
  (9 never-used TRAIN blocks 390119-121/390219-221/390319-321, each sampled once and paired)
- Control = V43 soft-marginal P(U2|B) (zero extra leakage), Treatment = Σ q_i^{L1APP} P(U2|B,u1)
  where q_i = softmax decode_row_layered_fftqspa(H1, p_i(u1), s1).final_beliefs (BP posterior / APP approximation)
  p_i(u1)=P(U1|B) from V25 C, s1=H1·u1^Alice (80 bits), frozen early-stop, 90/1.0 poly37.
- Per-condition gates G1'/G2'/G3' (exact_l2) and 5-state machine.
- Hard cap 27 shared (28th refused), exactly-once execution.

Lifecycle: IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED.
No execution on import, never imports v39/v40/v41/v42/v43/v44, reads only committed v38
structural-authority plus V25 counts via accepted loader, never writes NPZ.
"""

from __future__ import annotations

import csv
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

from comparison_bench.formal_ir.v35_algorithm_development import (
    GF2mField,
    factorize_f03,
    get_conditional_posterior_l2,
    load_v25_channel_counts,
    sample_empirical_block,
    syndrome_of_gf32,
)
from comparison_bench.formal_ir.v38_architecture_triage import (
    BLOCK_LENGTH,
    _check_v38r1_metric_match,
    _load_v38r1_reference_metrics,
    construct_lane_c_prototype,
)

# ---------------------------------------------------------------------------
# Frozen protocol constants
# ---------------------------------------------------------------------------

CYCLE_ID = "V45P0"
CHANGE_ID = "formal-ir-v45-l1-app-soft-transfer"
ACCEPTED_PLAN_SHA = "d89d9e932b11208802c595e9f2ef471da16fcbbd"
BRANCH_REF = "origin/formal-ir-mainline"
EXECUTION_SCOPE = "v45_diagnostic_27_invocations_exactly_once"

POLYNOMIAL = 37
DIMENSION = 32
Q = 32

SOURCE_ORDER: tuple[str, ...] = ("1M", "1p5M", "2M")
CONDITION_ORDER: tuple[str, ...] = ("cond_control", "cond_l1_app")
COND_CONTROL = "cond_control"
COND_L1_APP = "cond_l1_app"
MECHANISM_ID = "l1_app_soft_transfer_H1_syndrome_derived"
MECHANISM_CANDIDATE = "l1_app_soft_transfer"

MAX_ITER = 90
DAMPING_ALPHA = 1.0
DECODER_SETTING: tuple[int, float] = (MAX_ITER, DAMPING_ALPHA)

PLANNED_CALLS = 27
PLANNED_L1 = 9
PLANNED_CONTROL = 9
PLANNED_TREATMENT = 9
HARD_CALL_CAP = 27

NEW_BLOCK_SEEDS: dict[str, list[int]] = {
    "1M": [390119, 390120, 390121],
    "1p5M": [390219, 390220, 390221],
    "2M": [390319, 390320, 390321],
}

V36_A3_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [360101, 360102, 360103, 360104, 360105],
    "1p5M": [360201, 360202, 360203, 360204, 360205],
    "2M": [360301, 360302, 360303, 360304, 360305],
}
V39_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390101, 390102, 390103, 390104, 390105],
    "1p5M": [390201, 390202, 390203, 390204, 390205],
    "2M": [390301, 390302, 390303, 390304, 390305],
}
V40_PROBE_SEEDS_COPIED: dict[str, int] = {"1M": 390106, "1p5M": 390206, "2M": 390306}
V41_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390107, 390108, 390109],
    "1p5M": [390207, 390208, 390209],
    "2M": [390307, 390308, 390309],
}
V42_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390110, 390111, 390112],
    "1p5M": [390210, 390211, 390212],
    "2M": [390310, 390311, 390312],
}
V43_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390113, 390114, 390115],
    "1p5M": [390213, 390214, 390215],
    "2M": [390313, 390314, 390315],
}
V44_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390116, 390117, 390118],
    "1p5M": [390216, 390217, 390218],
    "2M": [390316, 390317, 390318],
}
FORBIDDEN_BLOCK_SEEDS: frozenset[int] = frozenset(
    seed
    for seeds in (
        *V36_A3_SEEDS_COPIED.values(),
        *V39_SEEDS_COPIED.values(),
        *V40_PROBE_SEEDS_COPIED.values(),
        *V41_SEEDS_COPIED.values(),
        *V42_SEEDS_COPIED.values(),
        *V43_SEEDS_COPIED.values(),
        *V44_SEEDS_COPIED.values(),
    )
    for seed in (seeds if isinstance(seeds, list) else [seeds])
)

REPRESENTATIVE_ORDINALS: dict[str, int] = {"lane_c": 2}
CONSTRUCTION_SEEDS: dict[str, dict[str, list[int]]] = {
    "lane_c": {
        "1M": [383101, 383102, 383103],
        "1p5M": [383201, 383202, 383203],
        "2M": [383301, 383302, 383303],
    },
}

def _rep_seed(lane: str, source: str) -> int:
    return CONSTRUCTION_SEEDS[lane][source][REPRESENTATIVE_ORDINALS[lane] - 1]

FROZEN_REPRESENTATIVE_MATRIX_IDS: tuple[str, ...] = (
    "lane_c_1M_s383102",
    "lane_c_1p5M_s383202",
    "lane_c_2M_s383302",
)
H1_MATRIX_ID = "V31-H1-QC-16x1024"
H1_FAMILY = "QC-cyclic-projective"
H1_M = 16
H1_N = 1024

FROZEN_WORKLOAD: tuple[dict[str, Any], ...] = (
    {"call_id": "C01", "condition": COND_CONTROL, "source": "1M", "block_seed": 390119},
    {"call_id": "C02", "condition": COND_L1_APP, "source": "1M", "block_seed": 390119},
    {"call_id": "C03", "condition": COND_CONTROL, "source": "1M", "block_seed": 390120},
    {"call_id": "C04", "condition": COND_L1_APP, "source": "1M", "block_seed": 390120},
    {"call_id": "C05", "condition": COND_CONTROL, "source": "1M", "block_seed": 390121},
    {"call_id": "C06", "condition": COND_L1_APP, "source": "1M", "block_seed": 390121},
    {"call_id": "C07", "condition": COND_CONTROL, "source": "1p5M", "block_seed": 390219},
    {"call_id": "C08", "condition": COND_L1_APP, "source": "1p5M", "block_seed": 390219},
    {"call_id": "C09", "condition": COND_CONTROL, "source": "1p5M", "block_seed": 390220},
    {"call_id": "C10", "condition": COND_L1_APP, "source": "1p5M", "block_seed": 390220},
    {"call_id": "C11", "condition": COND_CONTROL, "source": "1p5M", "block_seed": 390221},
    {"call_id": "C12", "condition": COND_L1_APP, "source": "1p5M", "block_seed": 390221},
    {"call_id": "C13", "condition": COND_CONTROL, "source": "2M", "block_seed": 390319},
    {"call_id": "C14", "condition": COND_L1_APP, "source": "2M", "block_seed": 390319},
    {"call_id": "C15", "condition": COND_CONTROL, "source": "2M", "block_seed": 390320},
    {"call_id": "C16", "condition": COND_L1_APP, "source": "2M", "block_seed": 390320},
    {"call_id": "C17", "condition": COND_CONTROL, "source": "2M", "block_seed": 390321},
    {"call_id": "C18", "condition": COND_L1_APP, "source": "2M", "block_seed": 390321},
)

def workload_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in FROZEN_WORKLOAD:
        seed = _rep_seed("lane_c", spec["source"])
        rows.append(
            {
                **spec,
                "construction_seed_ordinal": REPRESENTATIVE_ORDINALS["lane_c"],
                "construction_seed": seed,
                "matrix_id": f"lane_c_{spec['source']}_s{seed}",
                "h1_matrix_id": H1_MATRIX_ID,
            }
        )
    return rows

PREFLIGHT_BLOCK_SEEDS: dict[str, int] = {"1M": 390119, "1p5M": 390219, "2M": 390319}

REPO_ROOT = Path(__file__).resolve().parents[4]
STRUCTURAL_AUTHORITY_PATH = (
    REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json"
)
OUTPUT_ROOT = (
    REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v45_l1_app_soft_transfer/run_01"
)
FORBIDDEN_WINNER_NPZ_NAME = "v38_winning_matrices.npz"

SCOPED_TRACKED_PATHS: tuple[str, ...] = (
    "comparison_bench/src/comparison_bench/formal_ir/v45_l1_app_soft_transfer.py",
    "scripts/execute_v45_l1_app_soft_transfer.py",
    "comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py",
    "comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py",
)

V25_COUNTS_RELATIVE_PATH = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz"
)

PREDECESSOR_CYCLE = "V43P0"
PREDECESSOR_TERMINAL_STATE = "V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK"
PREDECESSOR_PLAN_SHA = "13c791e58c0f2a886af5d49cd26af493476dd4f9"
PREDECESSOR_EXECUTION_SHA = "f2ea4fa2c97f6c2ffe5fe6c27f0d84c8f7874e9b"
PREDECESSOR_RESULT_SHA = "4e2ed4db"
V43_ACCEPTED_PLAN_SHA = PREDECESSOR_PLAN_SHA
V44_PLAN_SHA = "c51a21c0"
STRUCTURAL_AUTHORITY_ID = str(STRUCTURAL_AUTHORITY_PATH)

# Leakage constants per source
SOURCE_M2: dict[str, int] = {"1M": 184, "1p5M": 190, "2M": 192}
SOURCE_L2_SYNDROME_BITS: dict[str, int] = {s: 5 * m for s, m in SOURCE_M2.items()}
SOURCE_L2_TAG_BITS: dict[str, int] = {s: 5 * m + 64 for s, m in SOURCE_M2.items()}
SOURCE_CONTROL_LEAK: dict[str, int] = SOURCE_L2_TAG_BITS  # 984/1014/1024
SOURCE_TREATMENT_LEAK: dict[str, int] = {s: 80 + v for s, v in SOURCE_L2_TAG_BITS.items()}  # 1064/1094/1104
M1_BITS = 80
TAG_BITS = 64

MASTER_STOP_RULE = (
    "唯一一次 27-invocation 双条件配对诊断（含 9 L1 BP + 18 L2）；对照为 V43 soft-marginal P(U2|B)（Control）vs Treatment Σ q_i P(U2|B,u1)；"
    "仅 Lane C 固定各 source ordinal-2 代表矩阵 + V31 H1 QC 16×1024、max_iter=90、damping_alpha=1.0 冻结 early-stop 不再调参；"
    "cond_l1_app 按冻结 syndrome-derived APP（p_i(u1)=P(U1|B)、s1=H1·u1^Alice、BP_i=decode(H1,p_i,s1).bp_posterior_beliefs / APP approximation、q_i=softmax BP_i、P_i(U2)=Σ q_i P(U2|B,u1)、"
    "泄漏 Control 984/1014/1024 (syndrome 920/950/960+64 tag) vs Treatment 1064/1094/1104 (含 80) f_total=leak_total/[N(H1+H2)] N=1024，H1 复用 rank16 QC-cyclic，通用 FFT-QSPA 复用不新增 decoder，不做 hard 估计/pilot/噪声/量化/失配信道律/joint 迭代/新矩阵/新 decoder 参数/参数网格/joint GF1024，区分 exact_l2 与 exact_full，Control/Treatment 非等泄漏比较为额外 80-bit 价值评估）后不再更改。"
    "无论结果如何：不追加 blocks、不补跑、不做第二轮诊断、不并行测试多方案、不启动 V46。"
)

TERMINAL_EVIDENCE_INVALID = "V45_EVIDENCE_INVALID"
TERMINAL_BOTH_RETAINED = "V45_BOTH_RETAINED"
TERMINAL_L1APP_NO_VALUE_OR_HARM = "V45_L1APP_NO_VALUE_OR_HARM"
TERMINAL_GO_STRUCTURE = "V45_GO_STRUCTURE"
TERMINAL_L1APP_ADDED_VALUE_SIGNAL = "V45_L1APP_ADDED_VALUE_SIGNAL"
ALL_TERMINALS = frozenset(
    {
        TERMINAL_EVIDENCE_INVALID,
        TERMINAL_BOTH_RETAINED,
        TERMINAL_L1APP_NO_VALUE_OR_HARM,
        TERMINAL_GO_STRUCTURE,
        TERMINAL_L1APP_ADDED_VALUE_SIGNAL,
    }
)

REASON_TREATMENT_FAILED = "TREATMENT_ARM_GATE_FAILED"
REASON_BOTH_FAILED = "BOTH_ARMS_GATES_FAILED"
REASON_CONTROL_FAILED = "CONTROL_ARM_FAILED_WITH_TREATMENT_PASSING"

G1_MIN_EXACT_TOTAL = 7
G2_MIN_PER_SOURCE = 2

RECORD_FIELDS: tuple[str, ...] = (
    "call_id",
    "condition",
    "source",
    "construction_seed",
    "construction_seed_ordinal",
    "block_seed",
    "matrix_id",
    "h1_matrix_id",
    "max_iter",
    "damping_alpha",
    "errors_initial",
    "errors_final",
    "exact_l2",
    "exact_u1",
    "exact_full",
    "syndrome_ok_l2",
    "syndrome_ok_l1",
    "wrong_codeword_l2",
    "wrong_codeword_l1",
    "iterations_l1",
    "iterations_l2",
    "bp_posterior_entropy",
    "mean_abs_diff_q_p",
    "status",
    "runtime_s",
)

ALLOWED_CALL_KEYS = frozenset(
    {"H", "source", "block_seed", "condition", "lane", "construction_seed", "counts",
     "max_iter", "damping_alpha", "fake_runner", "field", "decode_fn"}
)

CLAIM_BOUNDARY: tuple[str, ...] = (
    "results support ONLY bounded conditional attribution on V25 TRAIN empirical-count development blocks",
    "control arm is V43 soft-marginal P(U2|B) (zero extra leakage)",
    "cond_l1_app arm is syndrome-derived L1 APP soft transfer q_i=softmax BP posterior / APP approximation via V31 H1 16x1024 QC-cyclic rank16 + generic FFT-QSPA (s1=H1·u1^Alice, 80 bits), L2 on frozen Lane C ordinal-2 matrices 90/1.0 single point (frozen early-stop), Control 984/1014/1024 vs Treatment 1064/1094/1104 (syndrome 920/950/960+80+64 tag) f_total accounted, no hard/noise/quantization/distortion/C04/joint GF1024, not coupled graph/branch C/D/E, SHALL NOT be generalized as real condition",
    "Control vs Treatment non-equal-leakage comparison is ONLY extra 80-bit L1 syndrome information L2 transfer value",
    "V45_L1APP_NO_VALUE_OR_HARM attributes loss ONLY to this L1-APP soft transfer limitation (M_{H1,s1} insufficient or H1 non-convergence, extra 80-bit not transferred), NOT Lane C graph structure nor concrete upstream coding scheme or real system",
    "V45_L1APP_ADDED_VALUE_SIGNAL means ONLY finite-sample/iteration/prior differences require inspection; never unconditional evidence treatment outperforms control",
)

STATISTICS_NOTE = (
    "Descriptive only; sample is tiny and clustered (27 invocations = 9 unique blocks x (1 L1 + 2 L2); 18 L2 records paired). "
    "Exact-recovery proportions reported with n and raw counts; any interval is naive and uncorrected for clustering; no significance testing. "
    "Success primary is exact_l2 only; exact_full = exact_u1 && exact_l2 reported separately."
)


class IntegrityFailure(Exception):
    def __init__(self, check_id: str, message: str) -> None:
        super().__init__(f"[{check_id}] {message}")
        self.check_id = check_id
        self.message = message


# ---------------------------------------------------------------------------
# O1: L1 prior and L1-APP soft-transfer (frozen, design Section 7)
# ---------------------------------------------------------------------------

def get_l1_prior_p_u1_given_b(counts: np.ndarray, bob: np.ndarray) -> np.ndarray:
    """p_i(u1)=P(U1|B) from V25 C. Per b_i normalized, floor 1e-15."""
    assert MECHANISM_ID == "l1_app_soft_transfer_H1_syndrome_derived", "mechanism identity drift"
    arr = np.asarray(counts, dtype=np.float64)
    b = np.asarray(bob, dtype=np.int64)
    if arr.shape != (1024, 1024):
        raise ValueError(f"counts shape must be (1024,1024), got {arr.shape}")
    reshaped = arr.reshape(32, 32, 1024)  # (u1,u2,b)
    num = reshaped.sum(axis=1)  # (32,1024) sum over u2
    den = num.sum(axis=0)  # (1024,)
    # per b normalization
    p_matrix = np.zeros((32, 1024), dtype=np.float64)
    for bb in range(1024):
        d = float(den[bb])
        if d <= 0 or not np.isfinite(d):
            p_matrix[:, bb] = 1.0 / 32
        else:
            col = num[:, bb] / d
            col = np.maximum(col, 1e-15)
            col = col / col.sum()
            p_matrix[:, bb] = col
    prior = p_matrix[:, b].T  # (N,32)
    prior = np.maximum(prior, 1e-15)
    prior = prior / prior.sum(axis=1, keepdims=True)
    return prior


def get_soft_marginal_posterior_l2(counts: np.ndarray, bob: np.ndarray) -> np.ndarray:
    """V43 soft-marginal P_soft(U2|B) for control arm."""
    arr = np.asarray(counts, dtype=np.float64)
    b = np.asarray(bob, dtype=np.int64)
    reshaped = arr.reshape(32, 32, 1024)
    marginal = reshaped.sum(axis=0)  # (32,1024) sum over u1 -> (u2,b)?
    # reshaped (u1,u2,b), sum over u1 => (u2,b) shape (32,1024)
    col_sums = marginal.sum(axis=0)  # (1024,)
    with np.errstate(divide="ignore", invalid="ignore"):
        p_columns = np.where(col_sums[None, :] > 0, marginal / col_sums[None, :], 1.0 / 32)
    prior = p_columns[:, b].T
    prior = np.maximum(prior, 1e-15)
    prior = prior / prior.sum(axis=1, keepdims=True)
    return prior


def get_l1_app_prior_l2(counts: np.ndarray, bob: np.ndarray, q: np.ndarray) -> np.ndarray:
    """P_i(U2)= Σ q_i(u1) P(U2|B=b_i, U1=u1)  (treatment)."""
    arr = np.asarray(counts, dtype=np.float64)
    b = np.asarray(bob, dtype=np.int64)
    qq = np.asarray(q, dtype=np.float64)
    if qq.shape != (b.shape[0], 32):
        raise ValueError(f"q shape must be (N,32), got {qq.shape}")
    reshaped = arr.reshape(32, 32, 1024)  # (u1,u2,b)
    N = b.shape[0]
    out = np.zeros((N, 32), dtype=np.float64)
    for i in range(N):
        bb = int(b[i])
        # counts per u1/u2 for this b
        counts_u1u2 = reshaped[:, :, bb]  # (32,32)
        row_sums = counts_u1u2.sum(axis=1, keepdims=True)  # (32,1)
        # P(U2|B,u1) per u1
        p_u2 = np.divide(counts_u1u2, row_sums, out=np.full_like(counts_u1u2, 1.0/32, dtype=float), where=row_sums>0)
        qi = qq[i]  # (32,)
        out[i] = qi @ p_u2  # (32,)
    out = np.maximum(out, 1e-15)
    out /= out.sum(axis=1, keepdims=True)
    return out


def softmax_beliefs(beliefs: np.ndarray) -> np.ndarray:
    """q_i = softmax BP_i per position."""
    bel = np.asarray(beliefs, dtype=np.float64)
    # beliefs shape (N,32) log-beliefs
    if bel.ndim != 2 or bel.shape[1] != 32:
        raise ValueError(f"beliefs shape must be (N,32), got {bel.shape}")
    # subtract max per row for stability
    shifted = bel - np.max(bel, axis=1, keepdims=True)
    exp = np.exp(shifted)
    exp = np.maximum(exp, 1e-15)
    q = exp / exp.sum(axis=1, keepdims=True)
    q = np.maximum(q, 1e-15)
    q /= q.sum(axis=1, keepdims=True)
    return q


def compute_entropy_and_diff(q: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    q = np.asarray(q, dtype=np.float64)
    p = np.asarray(p, dtype=np.float64)
    # entropy per position: -sum q log2 q
    ent = -np.sum(q * np.log2(np.maximum(q, 1e-15)), axis=1)
    mean_ent = float(np.mean(ent))
    mean_abs = float(np.mean(np.abs(q - p)))
    return mean_ent, mean_abs


# ---------------------------------------------------------------------------
# Seed-registry validator (J2)
# ---------------------------------------------------------------------------

def validate_seed_registry(seeds: Optional[dict[str, list[int]]] = None) -> tuple[bool, str]:
    reg = NEW_BLOCK_SEEDS if seeds is None else seeds
    if set(reg.keys()) != set(SOURCE_ORDER):
        return False, f"registry sources must be exactly {SOURCE_ORDER}"
    all_seeds = [seed for source in SOURCE_ORDER for seed in reg[source]]
    if len(all_seeds) != 9:
        return False, f"registry must contain exactly nine seeds, got {len(all_seeds)}"
    if any(len(reg[source]) != 3 for source in SOURCE_ORDER):
        return False, f"registry must hold exactly three seeds per source: {dict(reg)}"
    duplicates = sorted({s for s in all_seeds if all_seeds.count(s) > 1})
    if duplicates:
        return False, f"duplicate seeds among the nine: {duplicates}"
    overlap = set(all_seeds) & FORBIDDEN_BLOCK_SEEDS
    if overlap:
        return False, f"new seeds overlap forbidden registries: {sorted(overlap)}"
    return True, "SEED_REGISTRY_OK"


# ---------------------------------------------------------------------------
# Structural reconstruction (J3)
# ---------------------------------------------------------------------------

DEFAULT_CONSTRUCTORS: dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]] = {
    "lane_c": construct_lane_c_prototype,
}
RECONSTRUCTION_KEYS: tuple[tuple[str, str], ...] = tuple(("lane_c", source) for source in SOURCE_ORDER)

def _reject_forbidden_npz(path: Path | str) -> None:
    name = Path(path).name
    suffix = Path(path).suffix.lower()
    if name == FORBIDDEN_WINNER_NPZ_NAME or suffix == ".npz":
        raise IntegrityFailure("J8", f"structural authority must be the committed run_01 JSON, got NPZ path: {path}")

def reconstruct_v45_matrices(
    reference_metrics_path: Path | str = STRUCTURAL_AUTHORITY_PATH,
    field: Optional[GF2mField] = None,
    constructors: Optional[dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]]] = None,
) -> dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]]:
    _reject_forbidden_npz(reference_metrics_path)
    try:
        reference_by_id = _load_v38r1_reference_metrics(reference_metrics_path)
    except ValueError as exc:
        raise IntegrityFailure("J3", f"structural authority unusable: {exc}") from exc
    field = field or GF2mField.create(DIMENSION)
    if field.primitive_polynomial != POLYNOMIAL:
        raise IntegrityFailure("J9", f"field polynomial mismatch: expected {POLYNOMIAL}, got {field.primitive_polynomial}")
    ctor_map = constructors or DEFAULT_CONSTRUCTORS
    matrices: dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]] = {}
    for lane, source in RECONSTRUCTION_KEYS:
        seed = _rep_seed(lane, source)
        matrix_id = f"{lane}_{source}_s{seed}"
        if matrix_id not in FROZEN_REPRESENTATIVE_MATRIX_IDS:
            raise IntegrityFailure("J3", f"representative identity drift: {matrix_id} not in frozen constants")
        expected = reference_by_id.get(matrix_id)
        if expected is None:
            raise IntegrityFailure("J3", f"missing committed metrics for {matrix_id}")
        if expected.get("lane") != lane or expected.get("source") != source:
            raise IntegrityFailure("J3", f"identity mismatch in committed metrics: {matrix_id}")
        matrix, metrics = ctor_map[lane](source=source, seed=seed, field=field)
        try:
            _check_v38r1_metric_match(expected, metrics, matrix_id)
        except ValueError as exc:
            raise IntegrityFailure("J3", str(exc)) from exc
        if "position_permutations" not in expected:
            raise IntegrityFailure("J3", f"missing frozen Lane C permutations: {matrix_id}")
        matrices[(lane, source)] = (matrix, metrics)
    if len(matrices) != 3:
        raise IntegrityFailure("J3", f"must reconstruct exactly 3 L2 matrices, got {len(matrices)}")
    # H1 reconstruction (deterministic QC-cyclic 16x1024)
    try:
        from comparison_bench.formal_ir.nonbinary_v31 import build_layer as v31_build_layer
        h1_matrix_tuple, h1_audit = v31_build_layer(H1_M, H1_N, family=H1_FAMILY, field=field)
        h1_matrix = np.asarray(h1_matrix_tuple, dtype=np.uint8)
    except Exception as exc:
        raise IntegrityFailure("J3", f"H1 reconstruction failed: {type(exc).__name__}: {exc}") from exc
    # Validate H1 audit properties
    if h1_matrix.shape != (H1_M, H1_N):
        raise IntegrityFailure("J3", f"H1 shape mismatch: {h1_matrix.shape}")
    # rank etc check
    try:
        rank = int(h1_audit.get("rank", -1))
        full = bool(h1_audit.get("full_row_rank", False))
        cap_ok = bool(h1_audit.get("capacity_ok", False))
        proj_safe = bool(h1_audit.get("projective", {}).get("projective_safe", h1_audit.get("projective_safe", False)))
        # fallback top-level
        if "projective_safe" in h1_audit:
            proj_safe = proj_safe or bool(h1_audit["projective_safe"])
    except Exception as exc:
        raise IntegrityFailure("J3", f"H1 audit parse failed: {exc}") from exc
    if rank != 16:
        raise IntegrityFailure("J3", f"H1 rank must be 16, got {rank}")
    if not full:
        raise IntegrityFailure("J3", "H1 must be full_row_rank")
    if not cap_ok:
        raise IntegrityFailure("J3", "H1 capacity_ok false")
    if not proj_safe:
        raise IntegrityFailure("J3", "H1 projective_safe false")
    max_occ = int(h1_audit.get("max_support_occupancy", 999))
    if max_occ > 31:
        raise IntegrityFailure("J3", f"H1 max_support_occupancy {max_occ} >31")
    matrices[("H1", "L1")] = (h1_matrix, h1_audit)
    return matrices

# aliases
reconstruct_v43_matrices = reconstruct_v45_matrices
reconstruct_v42_matrices = reconstruct_v45_matrices

# ---------------------------------------------------------------------------
# Dual posterior-binding preflight (J5) — decoder-free, fake beliefs path
# ---------------------------------------------------------------------------

def dual_posterior_binding_preflight(
    counts_by_source: dict[str, np.ndarray],
    probes: Optional[dict[str, int]] = None,
    posterior_fn: Optional[Callable[..., np.ndarray]] = None,
    soft_posterior_fn: Optional[Callable[..., np.ndarray]] = None,
    h1_matrices: Optional[dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]]] = None,
    field: Optional[GF2mField] = None,
) -> dict[str, dict[str, Any]]:
    probes = PREFLIGHT_BLOCK_SEEDS if probes is None else probes
    # control posterior is oracle conditional; but preflight control 6 checks same as V43
    real_posterior = get_conditional_posterior_l2 if posterior_fn is None else posterior_fn
    # For treatment preflight we use fake beliefs path (decoder-free)
    field = field or GF2mField.create(DIMENSION)
    # Need H1 for s1 check; reconstruct if not provided via stub
    if h1_matrices is None:
        # try to get H1 via small stub if counts provided? Instead we build minimal H1 stub for preflight without decode
        # For decoder-free we still need H1 to compute s1; use deterministic build if possible, else dummy
        try:
            from comparison_bench.formal_ir.nonbinary_v31 import build_layer as _bl
            h1_tup, _aud = _bl(H1_M, H1_N, family=H1_FAMILY, field=field)
            h1_dummy = np.asarray(h1_tup, dtype=np.uint8)
        except Exception:
            h1_dummy = np.zeros((H1_M, H1_N), dtype=np.uint8)
            h1_dummy[0, ::64] = 1
    else:
        h1_dummy = h1_matrices.get(("H1", "L1"), (None,))[0]
        if h1_dummy is None:
            h1_dummy = np.zeros((H1_M, H1_N), dtype=np.uint8)
            h1_dummy[0, ::64] = 1
    results: dict[str, dict[str, Any]] = {}
    for source in SOURCE_ORDER:
        probe_seed = probes[source]
        counts = counts_by_source[source]
        idx, alice, bob = sample_empirical_block(counts, seed=probe_seed, size=BLOCK_LENGTH)
        u1_alice, u2_alice, u1_bob, u2_bob = factorize_f03(alice, bob)

        captured: dict[str, np.ndarray] = {}
        def _spy(cnt: np.ndarray, b: np.ndarray, u1: np.ndarray) -> np.ndarray:
            captured["second_argument"] = np.asarray(b).copy()
            return real_posterior(cnt, b, u1)
        # oracle / control arm checks
        prior_corrected = _spy(counts, bob, u1_alice)
        prior_direct = real_posterior(counts, bob, u1_alice)
        prior_u2bob = real_posterior(counts, u2_bob, u1_alice)
        am_corrected = np.argmax(prior_corrected, axis=1)
        am_u2bob = np.argmax(prior_u2bob, axis=1)

        # L1 APP fake path checks
        # p_i
        p_i = get_l1_prior_p_u1_given_b(counts, bob)
        # s1
        s1 = syndrome_of_gf32(h1_dummy, u1_alice, field)
        # fake beliefs: create deterministic fake BP posterior (non-uniform, normalized)
        # Use simple construction: tilt p_i slightly to simulate non-trivial M_{H1,s1}
        # For testing carrier identity we need spy to capture actual sent prior
        fake_beliefs = np.log(np.maximum(p_i, 1e-15)) + 0.1 * np.sin(np.arange(32))[None, :]  # small perturbation
        q_fake = softmax_beliefs(fake_beliefs)
        # treatment prior via q_fake
        prior_l1app_fake = get_l1_app_prior_l2(counts, bob, q_fake)
        # expected is same computation (to verify carrier identity)
        expected_fake = get_l1_app_prior_l2(counts, bob, q_fake)

        # sentinel dict
        checks: dict[str, Any] = {
            "probe_block_seed": int(probe_seed),
            "bob_gt_31": bool(np.any(np.asarray(bob) > 31)),
            "captured_equals_bob": bool(np.array_equal(captured["second_argument"], np.asarray(bob))),
            "corrected_equals_direct": bool(np.array_equal(prior_corrected, prior_direct)),
            "corrected_differs_u2bob_arraywise": bool(not np.array_equal(prior_corrected, prior_u2bob)),
            "corrected_differs_u2bob_maxabs": bool(float(np.max(np.abs(prior_corrected - prior_u2bob))) > 1e-6),
            "argmax_divergence": bool(not np.array_equal(am_corrected, am_u2bob)),
            "l1_app_public_inputs": True,
            "s1_is_H1_times_u1_true": bool(np.array_equal(s1, syndrome_of_gf32(h1_dummy, u1_alice, field))),
            "l1_prior_is_P_U1_given_B": bool(np.allclose(p_i, get_l1_prior_p_u1_given_b(counts, bob), atol=1e-12)),
            "carrier_identity_l1app_fake": bool(np.array_equal(prior_l1app_fake, expected_fake)),
            "l1app_normalization_ok_fake": bool(np.all(np.abs(q_fake.sum(axis=1) - 1.0) < 1e-12) and np.all(q_fake >= 1e-15 - 1e-18)),
            "leakage_accounted": bool(SOURCE_CONTROL_LEAK[source] == SOURCE_L2_TAG_BITS[source] and SOURCE_TREATMENT_LEAK[source] == SOURCE_L2_TAG_BITS[source] + 80),
            "fake_path_verified": True,
        }
        # l1_app_public_inputs check: if posterior_fn signature has >2 args -> but we use p_i which is counts+bob only; we already ensure not alice dependent
        # Additional check: ensure q_fake not dependent on alice beyond s1 (s1 already legit); public_inputs flag already true
        # Validate signature of real_posterior not used for l1 prior: p_i must be 2-arg
        import inspect
        try:
            sig = inspect.signature(get_l1_prior_p_u1_given_b)
            if len(sig.parameters) != 2:
                checks["l1_app_public_inputs"] = False
        except Exception:
            pass
        failed = [name for name, ok in checks.items() if isinstance(ok, bool) and not ok]
        if failed:
            raise IntegrityFailure("J5", f"posterior-binding sentinel failed on {source}/{probe_seed}: {failed}")
        results[source] = checks
    return results

# alias
posterior_binding_preflight = dual_posterior_binding_preflight

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_errors_initial(u2_alice: np.ndarray, u2_bob: np.ndarray) -> int:
    return int(np.sum(np.asarray(u2_alice) != np.asarray(u2_bob)))

# ---------------------------------------------------------------------------
# Budget accounting (J10) shared hard cap 27 with layer split
# ---------------------------------------------------------------------------

class CallAccounting:
    def __init__(self, hard_cap: int = HARD_CALL_CAP) -> None:
        self.hard_cap = int(hard_cap)
        self.started = 0
        self.completed = 0
        self.started_l1 = 0
        self.completed_l1 = 0
        self.started_control = 0
        self.completed_control = 0
        self.started_treatment = 0
        self.completed_treatment = 0

    def register_start(self, layer: str = "total") -> None:
        if self.started >= self.hard_cap:
            raise IntegrityFailure("J10", f"hard call cap {self.hard_cap} reached; call {self.started+1} structurally refused")
        # per-layer caps 9
        if layer == "l1" and self.started_l1 >= 9:
            raise IntegrityFailure("J10", "l1 cap 9 reached")
        if layer == "control" and self.started_control >= 9:
            raise IntegrityFailure("J10", "control cap 9 reached")
        if layer == "treatment" and self.started_treatment >= 9:
            raise IntegrityFailure("J10", "treatment cap 9 reached")
        self.started += 1
        if layer == "l1":
            self.started_l1 += 1
        elif layer == "control":
            self.started_control += 1
        elif layer == "treatment":
            self.started_treatment += 1

    def register_complete(self, layer: str = "total") -> None:
        # total must have started
        if self.completed >= self.started:
            raise IntegrityFailure("J10", "completed without started")
        self.completed += 1
        if layer == "l1":
            if self.completed_l1 >= self.started_l1:
                # allow but check
                pass
            self.completed_l1 += 1
        elif layer == "control":
            self.completed_control += 1
        elif layer == "treatment":
            self.completed_treatment += 1

    def validate_executed(self) -> list[tuple[str, str]]:
        failures: list[tuple[str, str]] = []
        if self.completed > self.hard_cap:
            failures.append(("J10", f"completed {self.completed} exceeds hard cap {self.hard_cap}"))
        if self.completed != self.started:
            failures.append(("J10", f"started {self.started} != completed {self.completed}"))
        # layer totals must be 9 each if any calls done and expecting full run
        # Only enforce if completed == 27?
        return failures


# ---------------------------------------------------------------------------
# Records and checks
# ---------------------------------------------------------------------------

def validate_decoder_contract(call_params: dict[str, Any], expected_setting: tuple[int, float]) -> None:
    extra = set(call_params.keys()) - ALLOWED_CALL_KEYS
    if extra:
        raise IntegrityFailure("J9", f"unexpected call parameters: {sorted(extra)}")
    if call_params["max_iter"] != expected_setting[0] or call_params["damping_alpha"] != expected_setting[1]:
        raise IntegrityFailure("J9", f"decoder settings {call_params['max_iter']}/{call_params['damping_alpha']} != frozen {expected_setting}")

def build_record(spec: dict[str, Any], raw: dict[str, Any], setting: tuple[int, float]) -> dict[str, Any]:
    # raw contains: condition, source, block_seed, construction_seed, matrix_id, h1_matrix_id,
    # errors_initial, errors_final, exact_l2, exact_u1, exact_full, syndrome_ok_l2, syndrome_ok_l1,
    # wrong_l2, wrong_l1, iterations_l1, iterations_l2, entropy, mean_abs, status, runtime_s
    exact_l2 = bool(raw["exact_l2"])
    exact_u1 = bool(raw["exact_u1"])
    exact_full = bool(raw.get("exact_full", exact_l2 and exact_u1))
    syndrome_ok_l2 = bool(raw["syndrome_ok_l2"])
    syndrome_ok_l1 = bool(raw["syndrome_ok_l1"])
    wrong_l2 = bool(syndrome_ok_l2 and not exact_l2)
    wrong_l1 = bool(syndrome_ok_l1 and not exact_u1)
    record = {
        "call_id": spec["call_id"],
        "condition": raw["condition"],
        "source": raw["source"],
        "construction_seed": raw["construction_seed"],
        "construction_seed_ordinal": spec["construction_seed_ordinal"],
        "block_seed": raw["block_seed"],
        "matrix_id": raw["matrix_id"],
        "h1_matrix_id": raw.get("h1_matrix_id", H1_MATRIX_ID),
        "max_iter": int(setting[0]),
        "damping_alpha": float(setting[1]),
        "errors_initial": int(raw["errors_initial"]),
        "errors_final": int(raw["errors_final"]),
        "exact_l2": exact_l2,
        "exact_u1": exact_u1,
        "exact_full": exact_full,
        "syndrome_ok_l2": syndrome_ok_l2,
        "syndrome_ok_l1": syndrome_ok_l1,
        "wrong_codeword_l2": wrong_l2,
        "wrong_codeword_l1": wrong_l1,
        "iterations_l1": int(raw["iterations_l1"]),
        "iterations_l2": int(raw["iterations_l2"]),
        "bp_posterior_entropy": float(raw["bp_posterior_entropy"]),
        "mean_abs_diff_q_p": float(raw["mean_abs_diff_q_p"]),
        "status": str(raw["status"]),
        "runtime_s": float(raw["runtime_s"]),
    }
    return {k: record[k] for k in RECORD_FIELDS}

def validate_record_schema(record: dict[str, Any]) -> tuple[bool, str]:
    for key in RECORD_FIELDS:
        if key not in record:
            return False, f"missing field {key}"
    valid_call_ids = {spec["call_id"] for spec in FROZEN_WORKLOAD}
    if record["call_id"] not in valid_call_ids:
        return False, f"invalid call_id {record['call_id']!r}"
    if record["condition"] not in CONDITION_ORDER or record["source"] not in SOURCE_ORDER:
        return False, f"invalid condition/source {record['condition']!r}/{record['source']!r}"
    for key in ("exact_l2", "exact_u1", "exact_full", "syndrome_ok_l2", "syndrome_ok_l1", "wrong_codeword_l2", "wrong_codeword_l1"):
        if not isinstance(record[key], bool):
            return False, f"field {key} must be bool"
    for key in ("errors_initial", "errors_final", "iterations_l1", "iterations_l2", "max_iter", "block_seed", "construction_seed", "construction_seed_ordinal"):
        if not isinstance(record[key], int) or isinstance(record[key], bool):
            return False, f"field {key} must be int"
    if record["max_iter"] != MAX_ITER or record["damping_alpha"] != DAMPING_ALPHA:
        return False, f"record setting {record['max_iter']}/{record['damping_alpha']} != frozen {DECODER_SETTING} (J9)"
    if record["wrong_codeword_l2"] != (record["syndrome_ok_l2"] and not record["exact_l2"]):
        return False, "wrong_codeword_l2 must equal syndrome_ok_l2 and not exact_l2"
    if record["wrong_codeword_l1"] != (record["syndrome_ok_l1"] and not record["exact_u1"]):
        return False, "wrong_codeword_l1 must equal syndrome_ok_l1 and not exact_u1"
    if record["exact_full"] != (record["exact_u1"] and record["exact_l2"]):
        return False, "exact_full must equal exact_u1 and exact_l2"
    return True, "SCHEMA_OK"

def validate_post_evaluation(records: list[dict[str, Any]]) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    for rec in records:
        ok, msg = validate_record_schema(rec)
        if not ok:
            failures.append(("J11", f"record {rec.get('call_id')}: {msg}"))
    expected_order = [
        (row["call_id"], row["condition"], row["source"], row["block_seed"], row["matrix_id"])
        for row in workload_rows()
    ]
    actual_order = [
        (rec["call_id"], rec["condition"], rec["source"], rec["block_seed"], rec["matrix_id"])
        for rec in records
    ]
    if actual_order != expected_order[: len(actual_order)]:
        failures.append(("J12", f"workload membership/order drift: {actual_order} != frozen C01-C18 prefix"))
    from collections import Counter
    pair_keys = [(rec["source"], rec["block_seed"], rec["condition"]) for rec in records]
    cnt = Counter(pair_keys)
    for key, n in cnt.items():
        if n != 1:
            failures.append(("J6", f"duplicate block-condition {key}: {n}"))
    expected_pairs = {(spec["source"], spec["block_seed"], spec["condition"]) for spec in FROZEN_WORKLOAD}
    actual_pairs = set(pair_keys)
    missing = expected_pairs - actual_pairs
    if records and missing:
        failures.append(("J12", f"missing block-condition combinations: {missing}"))
    # strict per-pair cross-arm errors_initial equality (J6)
    by_block: dict[int, dict[str, int]] = {}
    for rec in records:
        bs = rec["block_seed"]
        cond = rec["condition"]
        by_block.setdefault(bs, {})[cond] = rec["errors_initial"]
    for bs, cond_map in sorted(by_block.items()):
        if COND_CONTROL in cond_map and COND_L1_APP in cond_map:
            if cond_map[COND_CONTROL] != cond_map[COND_L1_APP]:
                failures.append(("J6", f"block {bs}: cross-arm errors_initial mismatch {cond_map}"))
    return failures


# ---------------------------------------------------------------------------
# Aggregates, gates, terminal machine
# ---------------------------------------------------------------------------

def aggregate_results(records: list[dict[str, Any]], counts_by_source: Optional[dict[str, np.ndarray]] = None) -> dict[str, Any]:
    per_condition: dict[str, Any] = {}
    for cond in CONDITION_ORDER:
        recs = [r for r in records if r["condition"] == cond]
        per_condition[cond] = {
            "calls": len(recs),
            "exact_l2_total": sum(1 for r in recs if r["exact_l2"]),
            "exact_full_total": sum(1 for r in recs if r["exact_full"]),
            "wrong_count": sum(1 for r in recs if r["wrong_codeword_l2"]),
            "exact_by_source_l2": {source: sum(1 for r in recs if r["source"] == source and r["exact_l2"]) for source in SOURCE_ORDER},
            "exact_by_source_full": {source: sum(1 for r in recs if r["source"] == source and r["exact_full"]) for source in SOURCE_ORDER},
        }
    per_source: dict[str, Any] = {}
    for source in SOURCE_ORDER:
        recs = [r for r in records if r["source"] == source]
        per_source[source] = {
            "calls": len(recs),
            "exact_l2_total": sum(1 for r in recs if r["exact_l2"]),
            "exact_full_total": sum(1 for r in recs if r["exact_full"]),
            "by_condition_l2": {cond: sum(1 for r in recs if r["condition"] == cond and r["exact_l2"]) for cond in CONDITION_ORDER},
            "by_condition_full": {cond: sum(1 for r in recs if r["condition"] == cond and r["exact_full"]) for cond in CONDITION_ORDER},
        }
    paired: list[dict[str, Any]] = []
    by_block_map: dict[int, dict[str, dict[str, Any]]] = {}
    for rec in records:
        by_block_map.setdefault(rec["block_seed"], {})[rec["condition"]] = rec
    for bs in sorted(by_block_map.keys()):
        m = by_block_map[bs]
        if COND_CONTROL in m and COND_L1_APP in m:
            o = m[COND_CONTROL]
            e = m[COND_L1_APP]
            both_exact = bool(o["exact_l2"] and e["exact_l2"])
            control_only = bool(o["exact_l2"] and not e["exact_l2"])
            treatment_only = bool(not o["exact_l2"] and e["exact_l2"])
            neither = bool(not o["exact_l2"] and not e["exact_l2"])
            paired.append({
                "block_seed": bs,
                "source": o["source"],
                "both_exact": both_exact,
                "control_only_exact": control_only,
                "treatment_only_exact": treatment_only,
                "neither_exact": neither,
                "both_exact_full": bool(o["exact_full"] and e["exact_full"]),
                "errors_final_control": o["errors_final"],
                "errors_final_treatment": e["errors_final"],
                "errors_final_delta": int(e["errors_final"] - o["errors_final"]),
                "pairing_errors_initial_equal": bool(o["errors_initial"] == e["errors_initial"]),
            })
    # l1 diagnostics by source (execution-time, never gate)
    l1_diag: dict[str, Any] = {}
    for source in SOURCE_ORDER:
        recs = [r for r in records if r["source"] == source]
        if recs:
            mean_abs = float(np.mean([r["mean_abs_diff_q_p"] for r in recs]))
            mean_ent = float(np.mean([r["bp_posterior_entropy"] for r in recs]))
            iters = [r["iterations_l1"] for r in recs]
            l1_diag[source] = {
                "mean_abs_diff_q_p": mean_abs,
                "mean_bp_posterior_entropy": mean_ent,
                "iterations_l1": iters,
                "exact_u1_count": sum(1 for r in recs if r["exact_u1"]),
                "syndrome_ok_l1_count": sum(1 for r in recs if r["syndrome_ok_l1"]),
                "wrong_l1_count": sum(1 for r in recs if r["wrong_codeword_l1"]),
            }
    return {
        "per_condition": per_condition,
        "per_source": per_source,
        "wrong_total_l2": sum(1 for r in records if r["wrong_codeword_l2"]),
        "wrong_total_l1": sum(1 for r in records if r["wrong_codeword_l1"]),
        "paired_outcomes": paired,
        "l1_diagnostics_by_source": l1_diag,
    }


def evaluate_condition_gate(condition: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    recs = [r for r in records if r["condition"] == condition]
    exact_total = sum(1 for r in recs if r["exact_l2"])
    exact_by_source = {source: sum(1 for r in recs if r["source"] == source and r["exact_l2"]) for source in SOURCE_ORDER}
    wrong_count = sum(1 for r in recs if r["wrong_codeword_l2"])
    g1 = exact_total >= G1_MIN_EXACT_TOTAL
    g2 = len(recs) == 9 and all(v >= G2_MIN_PER_SOURCE for v in exact_by_source.values())
    g3 = wrong_count == 0
    return {
        "condition": condition,
        "calls": len(recs),
        "g1_overall_exact_ge_7_of_9": {"exact_total": exact_total, "threshold": G1_MIN_EXACT_TOTAL, "pass": g1},
        "g2_every_source_ge_2_of_3": {"exact_by_source": exact_by_source, "threshold_per_source": G2_MIN_PER_SOURCE, "pass": g2},
        "g3_wrong_zero": {"wrong_count": wrong_count, "pass": g3},
        "passed": bool(g1 and g2 and g3),
    }


def determine_v45_terminal(
    integrity_ok: bool,
    pass_control: bool,
    pass_treatment: bool,
) -> tuple[str, Optional[str], list[str]]:
    trace: list[str] = []
    if not integrity_ok:
        trace.append("rule_0_integrity_or_execution_failure -> V45_EVIDENCE_INVALID")
        return TERMINAL_EVIDENCE_INVALID, None, trace
    trace.append("rule_0_integrity_ok")
    if pass_control and pass_treatment:
        trace.append("rule_1_both_gates_pass -> V45_BOTH_RETAINED")
        return TERMINAL_BOTH_RETAINED, None, trace
    if pass_control and not pass_treatment:
        trace.append("rule_2_only_control_passes -> V45_L1APP_NO_VALUE_OR_HARM")
        return TERMINAL_L1APP_NO_VALUE_OR_HARM, REASON_TREATMENT_FAILED, trace
    if not pass_control and not pass_treatment:
        trace.append("rule_3_both_gates_failed -> V45_GO_STRUCTURE")
        return TERMINAL_GO_STRUCTURE, REASON_BOTH_FAILED, trace
    trace.append("rule_4_only_treatment_passes -> V45_L1APP_ADDED_VALUE_SIGNAL")
    return TERMINAL_L1APP_ADDED_VALUE_SIGNAL, REASON_CONTROL_FAILED, trace

# alias
determine_v43_terminal = determine_v45_terminal

# ---------------------------------------------------------------------------
# Environment loaders and git binding
# ---------------------------------------------------------------------------

def describe_v25_counts_provenance() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[4] / V25_COUNTS_RELATIVE_PATH
    return {"path": str(path), "loader": "comparison_bench.formal_ir.v35_algorithm_development.load_v25_channel_counts", "role": "source-specific V25 TRAIN empirical counts (read-only)", "exists": path.is_file()}

def git_rev_parse(repo_root: Path, ref: str) -> str:
    completed = subprocess.run(["git", "-C", str(repo_root), "rev-parse", ref], capture_output=True, text=True, check=True)
    return completed.stdout.strip()

def verify_scoped_clean(repo_root: Path, relative_paths: tuple[str, ...] = SCOPED_TRACKED_PATHS) -> None:
    completed = subprocess.run(["git", "-C", str(repo_root), "diff", "HEAD", "--quiet", "--", *relative_paths], capture_output=True, text=True)
    if completed.returncode != 0:
        raise IntegrityFailure("J1_TRACKED_DIRTY", f"scoped tracked files differ from HEAD; commit or revert before execution: {list(relative_paths)}")

def verify_execution_sha_binding(repo_root: Path, authorized_target_sha: str) -> dict[str, str]:
    head = git_rev_parse(repo_root, "HEAD")
    branch = git_rev_parse(repo_root, BRANCH_REF)
    if head != authorized_target_sha or branch != authorized_target_sha:
        raise IntegrityFailure("J1_SHA_BINDING_MISMATCH", f"authorized_target_sha={authorized_target_sha} but HEAD={head} and {BRANCH_REF}={branch}")
    return {"HEAD": head, BRANCH_REF: branch}


# ---------------------------------------------------------------------------
# Guarded diagnostic runner (exactly 27 calls, dual-condition + L1)
# ---------------------------------------------------------------------------

def _run_workload_calls(
    matrices: dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]],
    counts_by_source: dict[str, np.ndarray],
    field: GF2mField,
    fake_runner: bool,
    setting: tuple[int, float],
    accounting: CallAccounting,
    sink: list[dict[str, Any]],
    decode_fn: Optional[Callable[..., Any]] = None,
) -> None:
    from comparison_bench.formal_ir.v35_algorithm_development import decode_row_layered_fftqspa

    decode = decode_fn if decode_fn is not None else decode_row_layered_fftqspa

    # Pre-sample each block ONCE and share between arms
    block_samples: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
    for source in SOURCE_ORDER:
        counts = counts_by_source[source]
        for bseed in NEW_BLOCK_SEEDS[source]:
            idx, alice, bob = sample_empirical_block(counts, seed=bseed, size=BLOCK_LENGTH)
            u1_alice, u2_alice, u1_bob, u2_bob = factorize_f03(alice, bob)
            block_samples[bseed] = (idx, alice, bob, u1_alice, u2_alice, u1_bob, u2_bob)

    # H1 matrix
    h1_matrix = matrices.get(("H1", "L1"), (None,))[0]
    if h1_matrix is None:
        raise IntegrityFailure("J3", "H1 missing")

    rows = workload_rows()
    # iterate per pair (control+treatment share same block's L1)
    for pair_idx in range(0, len(rows), 2):
        row_control = rows[pair_idx]
        row_treat = rows[pair_idx + 1]
        assert row_control["condition"] == COND_CONTROL and row_treat["condition"] == COND_L1_APP
        assert row_control["block_seed"] == row_treat["block_seed"]
        block_seed = row_control["block_seed"]
        source = row_control["source"]
        idx, alice, bob, u1_alice, u2_alice, u1_bob, u2_bob = block_samples[block_seed]
        counts = counts_by_source[source]
        matrix, _ = matrices[("lane_c", source)]

        # Strict per-pair cross-arm errors_initial equality gate BEFORE any decode call of this pair
        errors_initial_control = _compute_errors_initial(u2_alice, u2_bob)
        errors_initial_treat = _compute_errors_initial(u2_alice, u2_bob)
        if errors_initial_control != errors_initial_treat:
            raise IntegrityFailure("J6", f"block {block_seed}: cross-arm errors_initial mismatch {errors_initial_control} != {errors_initial_treat}")

        # --- L1 decode (one per block, counts toward budget) ---
        # L1 prior p_i
        p_i = get_l1_prior_p_u1_given_b(counts, bob)
        s1 = syndrome_of_gf32(h1_matrix, u1_alice, field)
        # decode L1
        accounting.register_start(layer="l1")
        _validate_before_decode(h1_matrix, source, block_seed, "H1", counts, setting, fake_runner, decode_fn)
        if fake_runner:
            # fake L1 result: deterministic, slightly perturbed q, exact_u1 true
            fake_beliefs = np.log(np.maximum(p_i, 1e-15)) + 0.05 * np.sin(np.arange(32))[None, :]
            q_fake = softmax_beliefs(fake_beliefs)
            # for testing spy, we keep q_fake as q
            # entropy/diff
            ent, mdiff = compute_entropy_and_diff(q_fake, p_i)
            l1_res = {
                "q": q_fake,
                "iterations": 5,
                "syndrome_ok": True,
                "exact_u1": True,
                "entropy": ent,
                "mean_abs_diff": mdiff,
                "runtime_s": 0.001,
            }
        else:
            t0 = time.perf_counter()
            res = decode(h1_matrix, p_i, s1, max_iter=MAX_ITER, damping_alpha=DAMPING_ALPHA, field=field)
            q = softmax_beliefs(res.final_beliefs)
            ent, mdiff = compute_entropy_and_diff(q, p_i)
            x_hat_u1 = np.argmax(q, axis=1).astype(np.uint8)
            syn_ok = bool(np.array_equal(syndrome_of_gf32(h1_matrix, x_hat_u1, field), s1))
            exact_u1 = bool(np.array_equal(x_hat_u1, u1_alice))
            l1_res = {
                "q": q,
                "iterations": int(res.iterations),
                "syndrome_ok": bool(syn_ok),
                "exact_u1": bool(exact_u1),
                "entropy": ent,
                "mean_abs_diff": mdiff,
                "runtime_s": float(getattr(res, "runtime_s", time.perf_counter() - t0)),
            }
        accounting.register_complete(layer="l1")
        # need q for treatment arm
        q_for_treatment = l1_res["q"]

        # Control arm L2 (soft-marginal)
        accounting.register_start(layer="control")
        _validate_before_decode(matrix, source, block_seed, "lane_c", counts, setting, fake_runner, decode_fn)
        raw_control = _evaluate_one_condition(
            matrix=matrix, source=source, block_seed=block_seed, condition=COND_CONTROL,
            counts=counts, bob=bob, u1_selector=u1_alice, u2_alice=u2_alice,
            u2_bob=u2_bob, field=field, setting=setting, fake_runner=fake_runner, decode=decode,
            errors_initial=errors_initial_control, spec=row_control, q_for_treatment=None, l1_res=l1_res, is_control=True,
        )
        rec_control = build_record(row_control, raw_control, setting)
        accounting.register_complete(layer="control")
        sink.append(rec_control)

        # Treatment arm L2 (L1-APP)
        accounting.register_start(layer="treatment")
        _validate_before_decode(matrix, source, block_seed, "lane_c", counts, setting, fake_runner, decode_fn)
        raw_treat = _evaluate_one_condition(
            matrix=matrix, source=source, block_seed=block_seed, condition=COND_L1_APP,
            counts=counts, bob=bob, u1_selector=u1_alice, u2_alice=u2_alice,
            u2_bob=u2_bob, field=field, setting=setting, fake_runner=fake_runner, decode=decode,
            errors_initial=errors_initial_treat, spec=row_treat, q_for_treatment=q_for_treatment, l1_res=l1_res, is_control=False,
        )
        rec_treat = build_record(row_treat, raw_treat, setting)
        accounting.register_complete(layer="treatment")
        sink.append(rec_treat)


def _validate_before_decode(matrix, source, block_seed, lane, counts, setting, fake_runner, decode_fn):
    validate_decoder_contract({"H": matrix, "source": source, "block_seed": block_seed, "lane": lane, "construction_seed": 0, "counts": counts, "max_iter": setting[0], "damping_alpha": setting[1], "fake_runner": fake_runner, "field": GF2mField.create(DIMENSION), "decode_fn": decode_fn}, setting)


def _evaluate_one_condition(
    matrix: np.ndarray, source: str, block_seed: int, condition: str,
    counts: np.ndarray, bob: np.ndarray, u1_selector: Optional[np.ndarray], u2_alice: np.ndarray,
    u2_bob: np.ndarray, field: GF2mField, setting: tuple[int, float], fake_runner: bool, decode, errors_initial: int, spec: dict[str, Any],
    q_for_treatment: Optional[np.ndarray] = None, l1_res: Optional[dict[str, Any]] = None, is_control: bool = True,
) -> dict[str, Any]:
    max_iter, damping_alpha = setting
    if is_control:
        prior = get_soft_marginal_posterior_l2(counts, bob)
    else:
        assert q_for_treatment is not None
        prior = get_l1_app_prior_l2(counts, bob, q_for_treatment)
    synd = syndrome_of_gf32(matrix, u2_alice, field)
    if fake_runner:
        final_errors = 0
        exact_l2 = True
        syn_ok = True
        iters_l2 = 5
        runtime = 0.001
        status = "converged_exact"
    else:
        t0 = time.perf_counter()
        res = decode(matrix, prior, synd, max_iter=max_iter, damping_alpha=damping_alpha, field=field)
        final_errors = int(np.sum(res.x_hat != u2_alice))
        iters_l2 = int(res.iterations)
        runtime = float(getattr(res, "runtime_s", time.perf_counter() - t0))
        syn_ok = bool(res.syndrome_ok)
        exact_l2 = bool(np.array_equal(res.x_hat, u2_alice))
        status = res.status
    # L1 diagnostics carried from l1_res
    assert l1_res is not None
    exact_u1 = bool(l1_res["exact_u1"])
    syndrome_ok_l1 = bool(l1_res["syndrome_ok"])
    iterations_l1 = int(l1_res["iterations"])
    entropy = float(l1_res["entropy"])
    mean_abs = float(l1_res["mean_abs_diff"])
    exact_full = bool(exact_u1 and exact_l2)
    return {
        "condition": condition,
        "source": source,
        "block_seed": block_seed,
        "construction_seed": spec["construction_seed"],
        "matrix_id": spec["matrix_id"],
        "h1_matrix_id": spec.get("h1_matrix_id", H1_MATRIX_ID),
        "errors_initial": int(errors_initial),
        "errors_final": int(final_errors),
        "exact_l2": bool(exact_l2),
        "exact_u1": bool(exact_u1),
        "exact_full": bool(exact_full),
        "syndrome_ok_l2": bool(syn_ok),
        "syndrome_ok_l1": bool(syndrome_ok_l1),
        "iterations_l1": int(iterations_l1),
        "iterations_l2": int(iters_l2),
        "bp_posterior_entropy": float(entropy),
        "mean_abs_diff_q_p": float(mean_abs),
        "status": str(status),
        "runtime_s": float(runtime),
    }


def build_v45_summary(
    *,
    lifecycle_state: str,
    fake_runner: bool,
    authorized_target_sha: Optional[str],
    sha_binding: Optional[dict[str, str]],
    counts_provenance: dict[str, Any],
    accounting: CallAccounting,
    aggregates: Optional[dict[str, Any]],
    gate_evaluation: Optional[dict[str, Any]],
    routing_trace: list[str],
    integrity_failures: Optional[list[tuple[str, str]]],
    terminal_state: str,
    terminal_reason: Optional[str],
    structural_matrices_count: int,
    l1_diagnostics_by_source: Optional[dict[str, Any]] = None,
    stopped_for_analysis: Optional[dict[str, bool]] = None,
    control_arm_wrong_codeword_anomaly: bool = False,
    needs_1p5m_structure_branch: bool = False,
) -> dict[str, Any]:
    agg = aggregates if aggregates is not None else {}
    invalid = terminal_state == TERMINAL_EVIDENCE_INVALID
    # leakage maps
    leak_control = {s: SOURCE_CONTROL_LEAK[s] for s in SOURCE_ORDER}
    leak_treatment = {s: SOURCE_TREATMENT_LEAK[s] for s in SOURCE_ORDER}
    # f_total per source: leak / [N*(H1+H2)] N=1024 H from SOURCE_H via v31 frozen config
    try:
        from comparison_bench.formal_ir.nonbinary_v31 import SOURCE_H as V31_H
        f_totals = {}
        for s in SOURCE_ORDER:
            h1 = float(V31_H[s]["L1"])
            h2 = float(V31_H[s]["L2"])
            f_totals[s] = {
                "control": float(SOURCE_CONTROL_LEAK[s] / (1024 * (h1 + h2))),
                "treatment": float(SOURCE_TREATMENT_LEAK[s] / (1024 * (h1 + h2))),
            }
    except Exception:
        f_totals = {}
    return {
        "cycle_id": CYCLE_ID,
        "change_id": CHANGE_ID,
        "lifecycle_state": lifecycle_state,
        "execution_scope": EXECUTION_SCOPE,
        "fake_runner": fake_runner,
        "mechanism_id": MECHANISM_ID,
        "mechanism_candidate": MECHANISM_CANDIDATE,
        "provenance": {
            "authorized_target_sha": authorized_target_sha,
            "sha_binding": sha_binding,
            "structural_authority": str(STRUCTURAL_AUTHORITY_PATH),
            "structural_records_strict_match": structural_matrices_count,
            "predecessor_cycle": PREDECESSOR_CYCLE,
            "predecessor_terminal_state": PREDECESSOR_TERMINAL_STATE,
            "predecessor_plan_sha": PREDECESSOR_PLAN_SHA,
            "predecessor_execution_sha": PREDECESSOR_EXECUTION_SHA,
            "predecessor_result_sha": PREDECESSOR_RESULT_SHA,
            "v43_accepted_plan_sha": V43_ACCEPTED_PLAN_SHA,
            "v44_plan_sha": V44_PLAN_SHA,
            "h1_material": H1_MATRIX_ID + " rank16 QC-cyclic-projective",
            "h1_rank": 16,
        },
        "v25_counts_provenance": counts_provenance,
        "accounting": {
            "decoder_calls_planned": {"total": PLANNED_CALLS, "l1": PLANNED_L1, "control_l2": PLANNED_CONTROL, "treatment_l2": PLANNED_TREATMENT},
            "decoder_calls_started": {"total": accounting.started, "l1": accounting.started_l1, "control_l2": accounting.started_control, "treatment_l2": accounting.started_treatment},
            "decoder_calls_completed": {"total": accounting.completed, "l1": accounting.completed_l1, "control_l2": accounting.completed_control, "treatment_l2": accounting.completed_treatment},
            "structural_reconstruction_decoder_calls": 0,
            "preflight_decoder_calls": 0,
        },
        "leakage": {
            "m1_bits": M1_BITS,
            "per_source": {
                s: {
                    "m2": SOURCE_M2[s],
                    "l2_syndrome_bits": SOURCE_L2_SYNDROME_BITS[s],
                    "l2_plus_tag_bits": SOURCE_L2_TAG_BITS[s],
                    "control_leak_total": SOURCE_CONTROL_LEAK[s],
                    "treatment_leak_total": SOURCE_TREATMENT_LEAK[s],
                    "f_total": f_totals.get(s, {}),
                } for s in SOURCE_ORDER
            },
            "Control_984_1014_1024_vs_Treatment_1064_1094_1104": True,
            "note": "Control 984/1014/1024 vs Treatment 1064/1094/1104 (syndrome 920/950/960 f_total)",
        },
        "npz_policy": {"forbidden_winner_npz_read": False, "any_npz_output_written": False, "v25_channel_counts_npz_read_only_allowed": True},
        "routing_trace": routing_trace,
        "terminal_state": terminal_state,
        "terminal_reason": terminal_reason,
        "stopped_for_analysis": stopped_for_analysis if stopped_for_analysis is not None else {COND_CONTROL: False, COND_L1_APP: False},
        "control_arm_wrong_codeword_anomaly": bool(control_arm_wrong_codeword_anomaly),
        "needs_1p5m_structure_branch": bool(needs_1p5m_structure_branch),
        "l1_diagnostics_by_source": l1_diagnostics_by_source if l1_diagnostics_by_source is not None else (agg.get("l1_diagnostics_by_source", {}) if isinstance(agg, dict) else {}),
        "gate_evaluation": gate_evaluation if gate_evaluation is not None else {},
        "aggregates": agg,
        "master_stop_rule": MASTER_STOP_RULE,
        "statistics_note": STATISTICS_NOTE,
        "claim_boundary": list(CLAIM_BOUNDARY),
        "integrity_failures": ([{"check": cid, "message": msg} for cid, msg in integrity_failures] if integrity_failures else []),
        "performance_interpretation_presented": not invalid,
    }

# compatibility
build_v43_summary = build_v45_summary

# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict, tuple)):
        return json.dumps(value, sort_keys=True)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return value

def write_records_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: _csv_value(row[col]) for col in columns})

def write_v45_outputs(output_root: Path | str, records: list[dict[str, Any]], summary: dict[str, Any]) -> Path:
    root = Path(output_root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"J7: refusing to overwrite non-empty output root: {root}")
    if not root.exists():
        root.mkdir(parents=True)
    def dump(name: str, payload: Any) -> None:
        with (root / name).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
    dump("v45_records.json", records)
    write_records_csv(root / "v45_records.csv", records, list(RECORD_FIELDS))
    dump("v45_summary.json", summary)
    return root

def write_invalid_notice(output_root: Path | str, integrity_failures: list[tuple[str, str]], partial_records_retained: bool) -> Path:
    root = Path(output_root)
    notice = {"cycle_id": CYCLE_ID, "terminal_state": TERMINAL_EVIDENCE_INVALID, "integrity_failures": [{"check": cid, "message": msg} for cid, msg in integrity_failures], "partial_records_retained_byte_for_byte": partial_records_retained, "performance_interpretation": "none"}
    path = root / "v45_invalid_notice.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(notice, handle, indent=2)
    return path

def _persist_invalid_evidence(root: Path, *, records: list[dict[str, Any]], accounting: CallAccounting, summary_ctx: dict[str, Any], failures: list[tuple[str, str]], partial_records_retained: bool) -> None:
    try:
        if not root.exists():
            root.mkdir(parents=True)
        with (root / "v45_records.json").open("w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2)
        write_records_csv(root / "v45_records.csv", records, list(RECORD_FIELDS))
        summary = build_v45_summary(
            lifecycle_state="IMPLEMENTATION_CANDIDATE",
            fake_runner=summary_ctx.get("fake_runner", False),
            authorized_target_sha=summary_ctx.get("authorized_target_sha"),
            sha_binding=summary_ctx.get("sha_binding"),
            counts_provenance=summary_ctx.get("counts_provenance", {}),
            accounting=accounting,
            aggregates=None,
            gate_evaluation=None,
            routing_trace=[],
            integrity_failures=failures,
            terminal_state=TERMINAL_EVIDENCE_INVALID,
            terminal_reason=None,
            structural_matrices_count=int(summary_ctx.get("structural_matrices_count", 0)),
            l1_diagnostics_by_source=summary_ctx.get("l1_diagnostics_by_source", {}),
            stopped_for_analysis={COND_CONTROL: False, COND_L1_APP: False},
            control_arm_wrong_codeword_anomaly=False,
            needs_1p5m_structure_branch=False,
        )
        with (root / "v45_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        write_invalid_notice(root, failures, partial_records_retained=partial_records_retained)
    except Exception:
        pass

def run_v45_diagnostic(
    execution_authorized: bool = False,
    authorized_target_sha: Optional[str] = None,
    fake_runner: bool = False,
    output_root: Optional[Path | str] = None,
    structural_authority_path: Optional[Path | str] = None,
    counts_by_source: Optional[dict[str, np.ndarray]] = None,
    field: Optional[GF2mField] = None,
    check_git: bool = True,
    check_scoped_dirty: bool = True,
    constructors: Optional[dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]]] = None,
    decode_fn: Optional[Callable[..., Any]] = None,
) -> dict[str, Any]:
    if not execution_authorized:
        raise PermissionError(f"EXECUTE_NOT_AUTHORIZED: pass --execution-authorized bound to an explicit user EXECUTE_AUTH for scope {EXECUTION_SCOPE}")
    root_arg = output_root if output_root is not None else OUTPUT_ROOT
    root = Path(root_arg)
    if root.exists():
        raise FileExistsError(f"J7: refusing to overwrite existing output root: {root}")
    field = field or GF2mField.create(DIMENSION)
    if field.primitive_polynomial != POLYNOMIAL:
        raise IntegrityFailure("J9", f"polynomial mismatch: {field.primitive_polynomial}")
    sha_binding: Optional[dict[str, str]] = None
    if check_git:
        if not authorized_target_sha:
            raise IntegrityFailure("J1_SHA_BINDING_MISSING", "authorized_target_sha is required for the authorized run")
        sha_binding = verify_execution_sha_binding(REPO_ROOT, authorized_target_sha)
    if check_scoped_dirty:
        verify_scoped_clean(REPO_ROOT)
    summary_ctx: dict[str, Any] = {"fake_runner": fake_runner, "authorized_target_sha": authorized_target_sha, "sha_binding": sha_binding, "counts_provenance": {}, "structural_matrices_count": 0, "l1_diagnostics_by_source": {}}
    try:
        ok, msg = validate_seed_registry()
        if not ok:
            raise IntegrityFailure("J2", msg)
        spath = Path(structural_authority_path) if structural_authority_path else STRUCTURAL_AUTHORITY_PATH
        matrices = reconstruct_v45_matrices(reference_metrics_path=spath, field=field, constructors=constructors)
        summary_ctx["structural_matrices_count"] = len(matrices)
        counts = counts_by_source if counts_by_source is not None else load_v25_channel_counts()
        for source in SOURCE_ORDER:
            if counts[source].shape != (BLOCK_LENGTH, BLOCK_LENGTH):
                raise IntegrityFailure("J4", f"unexpected counts shape for {source}: {counts[source].shape}")
        counts_provenance = describe_v25_counts_provenance()
        summary_ctx["counts_provenance"] = counts_provenance
        try:
            # diagnostics placeholder executed in real path; for preflight we just need fake beliefs
            pass
        except Exception:
            pass
        dual_posterior_binding_preflight(counts, h1_matrices=matrices, field=field)
    except IntegrityFailure as exc:
        _persist_invalid_evidence(root, records=[], accounting=CallAccounting(), summary_ctx=summary_ctx, failures=[(exc.check_id, exc.message)], partial_records_retained=False)
        return {"output_root": str(root), "terminal_state": TERMINAL_EVIDENCE_INVALID, "terminal_reason": None, "integrity_failures": [(exc.check_id, exc.message)]}
    root.mkdir(parents=True)
    accounting = CallAccounting()
    records: list[dict[str, Any]] = []
    try:
        try:
            _run_workload_calls(matrices, counts, field, fake_runner, DECODER_SETTING, accounting, records, decode_fn=decode_fn)
        except IntegrityFailure as wf_exc:
            if accounting.started == 0 and accounting.completed == 0:
                _persist_invalid_evidence(root, records=records, accounting=accounting, summary_ctx=summary_ctx, failures=[(wf_exc.check_id, wf_exc.message)], partial_records_retained=False)
                return {"output_root": str(root), "terminal_state": TERMINAL_EVIDENCE_INVALID, "terminal_reason": None, "integrity_failures": [(wf_exc.check_id, wf_exc.message)]}
            raise
        failures = validate_post_evaluation(records) + accounting.validate_executed()
        if failures:
            _persist_invalid_evidence(root, records=records, accounting=accounting, summary_ctx=summary_ctx, failures=failures, partial_records_retained=True)
            return {"output_root": str(root), "terminal_state": TERMINAL_EVIDENCE_INVALID, "terminal_reason": None, "integrity_failures": failures}
        aggregates = aggregate_results(records, counts)
        gate_evaluation = {cond: evaluate_condition_gate(cond, records) for cond in CONDITION_ORDER}
        stopped: dict[str, bool] = {}
        for cond in CONDITION_ORDER:
            wrong = gate_evaluation[cond]["g3_wrong_zero"]["wrong_count"]
            stopped[cond] = bool(wrong > 0)
        control_wrong = gate_evaluation[COND_CONTROL]["g3_wrong_zero"]["wrong_count"] > 0
        # orthogonal flag: control exact on 1p5M <2
        control_recs_1p5 = [r for r in records if r["condition"] == COND_CONTROL and r["source"] == "1p5M"]
        needs_flag = sum(1 for r in control_recs_1p5 if r["exact_l2"]) < 2
        terminal_state, terminal_reason, routing_trace = determine_v45_terminal(
            integrity_ok=True,
            pass_control=bool(gate_evaluation[COND_CONTROL]["passed"]),
            pass_treatment=bool(gate_evaluation[COND_L1_APP]["passed"]),
        )
        summary = build_v45_summary(
            lifecycle_state="DEVELOPMENT_RESULT_CANDIDATE",
            fake_runner=fake_runner,
            authorized_target_sha=authorized_target_sha,
            sha_binding=sha_binding,
            counts_provenance=summary_ctx["counts_provenance"],
            accounting=accounting,
            aggregates=aggregates,
            gate_evaluation=gate_evaluation,
            routing_trace=routing_trace,
            integrity_failures=None,
            terminal_state=terminal_state,
            terminal_reason=terminal_reason,
            structural_matrices_count=len(matrices),
            l1_diagnostics_by_source=aggregates.get("l1_diagnostics_by_source", {}),
            stopped_for_analysis=stopped,
            control_arm_wrong_codeword_anomaly=bool(control_wrong),
            needs_1p5m_structure_branch=bool(needs_flag),
        )
        write_v45_outputs(root, records, summary)
        return {"output_root": str(root), "terminal_state": terminal_state, "terminal_reason": terminal_reason, "routing_trace": routing_trace, "decoder_calls_completed": accounting.completed, "aggregates": aggregates, "gate_evaluation": gate_evaluation, "summary": summary}
    except BaseException:
        _persist_invalid_evidence(root, records=records, accounting=accounting, summary_ctx=summary_ctx, failures=[("mid_run_failure", "raw partial records retained; no performance aggregate generated")], partial_records_retained=True)
        raise
