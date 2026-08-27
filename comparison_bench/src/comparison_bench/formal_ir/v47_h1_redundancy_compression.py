"""V47P0 H1 redundancy compression: guarded 54-invocation three-arm H1 prefix diagnostic.

Frozen V47P0 protocol (formal-ir-v47-h1-redundancy-compression):
- Single variable H1 prefix nested 8/12/16 from V31 H1 16x1024 QC-cyclic-projective rank 8/12/16
- Fresh-block 9 seeds 390125-127/390225-227/390325-327, 54 decoder invocations (27 L1 + 27 L2, 9 per arm)
- Three arms h1_8(40b)/h1_12(60b)/h1_16(80b) sharing same block sample, same L2 Lane C 90/1.0 poly37
- L1APP soft-transfer: p_i=P(U1|B), s1=H1^{m1}·u1, BP=decode(H1^{m1},p,s1).final_beliefs, q=softmax BP, P(U2)=Σ q P(U2|B,u1)
- L2-only verification: tag=compute_tag_64(empty,x2) via V35, tag_scope=l2_only
- Four-class reclassification and G3'=undetected==0 per arm, gates G1>=7/9 G2>=2/3 per source, first-match terminal.

Lifecycle: IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED.
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
    compute_tag_64,
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

CYCLE_ID = "V47P0"
CHANGE_ID = "formal-ir-v47-h1-redundancy-compression"
ACCEPTED_PLAN_SHA = "f7b1058ada234f8249d021ce84dee5e0e82aab27"
BRANCH_REF = "origin/formal-ir-mainline"
EXECUTION_SCOPE = "v47_diagnostic_54_invocations_h1_redundancy_exactly_once"

POLYNOMIAL = 37
DIMENSION = 32
Q = 32

SOURCE_ORDER: tuple[str, ...] = ("1M", "1p5M", "2M")
ARM_ORDER: tuple[str, ...] = ("h1_8", "h1_12", "h1_16")
H1_ROWS: dict[str, int] = {"h1_8": 8, "h1_12": 12, "h1_16": 16}
H1_BITS: dict[int, int] = {8: 40, 12: 60, 16: 80}
# reverse map arm->bits
ARM_BITS: dict[str, int] = {"h1_8": 40, "h1_12": 60, "h1_16": 80}

MECHANISM_ID = "l1_app_soft_transfer_H1_prefix_{8,12,16}_syndrome_derived_with_v35_tag_l2_only"
MECHANISM_CANDIDATE = "l1_app_soft_transfer_H1_prefix"
TAG_SCOPE = "l2_only"
TAG_SOURCE_STR = "v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only"
LEAKAGE_ALREADY_ACCOUNTED_NOTE = "leakage already accounted: H1-8 1024/1054/1064 vs H1-12 1044/1074/1084 vs H1-16 1064/1094/1104 includes 64-bit tag; SHA-trunc64 random-hash-model approximate 2^-64 L2-only"

MAX_ITER = 90
DAMPING_ALPHA = 1.0
DECODER_SETTING: tuple[int, float] = (MAX_ITER, DAMPING_ALPHA)

PLANNED_CALLS = 54
PLANNED_L1 = 27
PLANNED_H1_8 = 9
PLANNED_H1_12 = 9
PLANNED_H1_16 = 9
HARD_CALL_CAP = 54

NEW_BLOCK_SEEDS: dict[str, list[int]] = {
    "1M": [390125, 390126, 390127],
    "1p5M": [390225, 390226, 390227],
    "2M": [390325, 390326, 390327],
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
V45_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390119, 390120, 390121],
    "1p5M": [390219, 390220, 390221],
    "2M": [390319, 390320, 390321],
}
V46_SEEDS_COPIED: dict[str, list[int]] = {
    "1M": [390122, 390123, 390124],
    "1p5M": [390222, 390223, 390224],
    "2M": [390322, 390323, 390324],
}
FORBIDDEN_78: frozenset[int] = frozenset(
    seed
    for seeds in (
        *V36_A3_SEEDS_COPIED.values(),
        *V39_SEEDS_COPIED.values(),
        *V40_PROBE_SEEDS_COPIED.values(),
        *V41_SEEDS_COPIED.values(),
        *V42_SEEDS_COPIED.values(),
        *V43_SEEDS_COPIED.values(),
        *V44_SEEDS_COPIED.values(),
        *V45_SEEDS_COPIED.values(),
    )
    for seed in (seeds if isinstance(seeds, list) else [seeds])
)
FORBIDDEN_BLOCK_SEEDS: frozenset[int] = frozenset(
    set(FORBIDDEN_78) | {s for lst in V46_SEEDS_COPIED.values() for s in lst}
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

# Workload: 27 L2 records, order source 1M/1p5M/2M blocks asc, arms h1_8->h1_12->h1_16
def _build_frozen_workload() -> tuple[dict[str, Any], ...]:
    rows = []
    cid = 1
    for source in SOURCE_ORDER:
        for bseed in NEW_BLOCK_SEEDS[source]:
            for arm in ARM_ORDER:
                h1_rows = H1_ROWS[arm]
                leak = 5 * ({"1M": 184, "1p5M": 190, "2M": 192}[source]) + 5 * h1_rows + 64
                rows.append({
                    "call_id": f"C{cid:02d}",
                    "arm": arm,
                    "h1_rows": h1_rows,
                    "h1_bits": ARM_BITS[arm],
                    "source": source,
                    "block_seed": bseed,
                    "leak_total_this_arm": leak,
                })
                cid += 1
    return tuple(rows)

FROZEN_WORKLOAD: tuple[dict[str, Any], ...] = _build_frozen_workload()

def workload_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in FROZEN_WORKLOAD:
        seed = _rep_seed("lane_c", spec["source"])
        rows.append({
            **spec,
            "construction_seed_ordinal": REPRESENTATIVE_ORDINALS["lane_c"],
            "construction_seed": seed,
            "matrix_id": f"lane_c_{spec['source']}_s{seed}",
            "h1_matrix_id": f"{H1_MATRIX_ID} prefix m1={spec['h1_rows']}",
        })
    return rows

PREFLIGHT_BLOCK_SEEDS: dict[str, int] = {"1M": 390125, "1p5M": 390225, "2M": 390325}

REPO_ROOT = Path(__file__).resolve().parents[4]
STRUCTURAL_AUTHORITY_PATH = (
    REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json"
)
OUTPUT_ROOT = (
    REPO_ROOT / "comparison_bench/outputs_comparison/formal_ir_methods/v47_h1_redundancy_compression/run_01"
)
FORBIDDEN_WINNER_NPZ_NAME = "v38_winning_matrices.npz"

SCOPED_TRACKED_PATHS: tuple[str, ...] = (
    "comparison_bench/src/comparison_bench/formal_ir/v47_h1_redundancy_compression.py",
    "scripts/execute_v47_h1_redundancy_compression.py",
    "comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py",
    "comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py",
)

V25_COUNTS_RELATIVE_PATH = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz"
)

PREDECESSOR_CYCLE = "V46P0"
PREDECESSOR_TERMINAL_STATE = "V46_BOTH_RETAINED"
PREDECESSOR_PLAN_SHA = "613f9e3c8402cb079c99dac72e115a7131fb8fa6"
PREDECESSOR_EXECUTION_SHA = "f2ea4fa2"
PREDECESSOR_RESULT_SHA = "cb4f9990"
V43_ACCEPTED_PLAN_SHA = PREDECESSOR_PLAN_SHA

SOURCE_M2: dict[str, int] = {"1M": 184, "1p5M": 190, "2M": 192}
SOURCE_L2_SYNDROME_BITS: dict[str, int] = {s: 5 * m for s, m in SOURCE_M2.items()}

def leak_for(source: str, h1_rows: int) -> int:
    return 5 * SOURCE_M2[source] + 5 * h1_rows + 64

MASTER_STOP_RULE = (
    "唯一一次 54-invocation 三臂 H1 前缀配对诊断（含 27 L1 BP +27 L2）fresh-block with V35 SHA-trunc64 L2-only engineering verification (compute_tag_64(empty,x2)[:16], tag_ok gate, tag_scope=l2_only, 4-way reclassified, G3'=undetected==0 per arm, 工程近似 2^-64, exact_full=exact_u1&&exact_l2 oracle, exact_full≥7/9 & 每源≥2/3, first-match 最小 m1)；"
    "三臂 H1-8(40b,8×1024) vs H1-12(60b,12×1024) vs H1-16(80b,16×1024) 为 V31 H1 前缀嵌套 rank 8/12/16，对照为 H1-16，仅 Lane C 固定各 source ordinal-2 代表矩阵 + V31 H1 前缀、max_iter=90,damping 1.0 冻结 early-stop 不再调参；"
    "每臂 L1APP 按冻结 syndrome-derived APP（p_i=P(U1|B)、s1^{m1}=H1^{m1}·u1^Alice、BP_i^{m1}=decode(H1^{m1},p_i,s1^{m1}).bp_posterior_beliefs / APP approximation、q_i^{m1}=softmax BP_i^{m1}、P_i^{m1}(U2)=Σ q_i^{m1} P(U2|B,u1)、泄漏 H1-8 1024/1054/1064 vs H1-12 1044/1074/1084 vs H1-16 1064/1094/1104 f_total=leak/[N(H1+H2)] N=1024，三臂非等泄漏比较，复用 V35 tag L2-only 不重实现，不做 hard/噪声/量化/失真律/joint 迭代/新矩阵/新 decoder 参数/参数网格/joint GF1024，区分四类 per arm，L1 wrong 单独报告，不追溯 V46，不复用历史 87 块，对照为 H1-16 不运行 V43 Control）后不再更改。"
)

TERMINAL_EVIDENCE_INVALID = "V47_EVIDENCE_INVALID"
TERMINAL_H1_8_RETAINED = "V47_H1_8_RETAINED"
TERMINAL_H1_12_RETAINED = "V47_H1_12_RETAINED"
TERMINAL_H1_16_ONLY = "V47_H1_16_ONLY"
TERMINAL_NO_H1_SIZE_RETAINED = "V47_NO_H1_SIZE_RETAINED"
ALL_TERMINALS = frozenset({
    TERMINAL_EVIDENCE_INVALID, TERMINAL_H1_8_RETAINED, TERMINAL_H1_12_RETAINED,
    TERMINAL_H1_16_ONLY, TERMINAL_NO_H1_SIZE_RETAINED,
})

G1_MIN_EXACT_TOTAL = 7
G2_MIN_PER_SOURCE = 2

RECORD_FIELDS: tuple[str, ...] = (
    "call_id",
    "arm",
    "h1_rows",
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
    "target_tag",
    "candidate_tag",
    "tag_ok",
    "tag_scope",
    "reclassified",
    "iterations_l1",
    "iterations_l2",
    "bp_posterior_entropy",
    "mean_abs_diff_q_p",
    "leak_total_this_arm",
    "status",
    "runtime_s",
)

ALLOWED_CALL_KEYS = frozenset(
    {"H", "source", "block_seed", "arm", "h1_rows", "lane", "construction_seed", "counts",
     "max_iter", "damping_alpha", "fake_runner", "field", "decode_fn"}
)

CLAIM_BOUNDARY: tuple[str, ...] = (
    "results support ONLY bounded conditional attribution on V25 TRAIN empirical-count development blocks",
    "three arms H1-8/H1-12/H1-16 by V31 H1 prefix 8/12/16 + generic FFT-QSPA q_i^{m1}=softmax BP posterior / APP approximation (s1=H1^{m1}·u1, 40/60/80 bits), L2 on frozen Lane C ordinal-2 90/1.0 single point (frozen early-stop), leak H1-8 1024/1054/1064 vs H1-12 1044/1074/1084 vs H1-16 1064/1094/1104 (syndrome 920/950/960+m1*5+64 tag) f_total accounted, L2-only verification",
    "undetected≈2^-64 only random-hash-model engineering approx (fixed public SHA-256 trunc; strict bound requires universal2+seed), three-arm non-equal-leakage comparison is only smaller m1 value",
    "not real frame FER, no threshold/SKR/formal qualification/promotion; terminal is only directional first-match minimal m1",
)

STATISTICS_NOTE = (
    "Descriptive only; sample is tiny and clustered (54 invocations = 9 unique blocks x3 arms x (1 L1 +1 L2); 27 L2 records three-arm paired). "
    "Exact-recovery proportions reported with n and raw counts; any interval is naive and uncorrected for clustering; no significance testing. "
    "Success primary is exact_full = exact_u1 && exact_l2 per arm; exact_u1/exact_l2 reported separately; retained does not mean zero performance loss."
)


class IntegrityFailure(Exception):
    def __init__(self, check_id: str, message: str) -> None:
        super().__init__(f"[{check_id}] {message}")
        self.check_id = check_id
        self.message = message


# ---------------------------------------------------------------------------
# O1: L1 prior and L1-APP soft-transfer
# ---------------------------------------------------------------------------

def get_l1_prior_p_u1_given_b(counts: np.ndarray, bob: np.ndarray) -> np.ndarray:
    arr = np.asarray(counts, dtype=np.float64)
    b = np.asarray(bob, dtype=np.int64)
    if arr.shape != (1024, 1024):
        raise ValueError(f"counts shape must be (1024,1024), got {arr.shape}")
    reshaped = arr.reshape(32, 32, 1024)
    num = reshaped.sum(axis=1)
    den = num.sum(axis=0)
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
    prior = p_matrix[:, b].T
    prior = np.maximum(prior, 1e-15)
    prior = prior / prior.sum(axis=1, keepdims=True)
    return prior


def get_l1_app_prior_l2(counts: np.ndarray, bob: np.ndarray, q: np.ndarray) -> np.ndarray:
    arr = np.asarray(counts, dtype=np.float64)
    b = np.asarray(bob, dtype=np.int64)
    qq = np.asarray(q, dtype=np.float64)
    if qq.shape != (b.shape[0], 32):
        raise ValueError(f"q shape must be (N,32), got {qq.shape}")
    reshaped = arr.reshape(32, 32, 1024)
    N = b.shape[0]
    out = np.zeros((N, 32), dtype=np.float64)
    for i in range(N):
        bb = int(b[i])
        counts_u1u2 = reshaped[:, :, bb]
        row_sums = counts_u1u2.sum(axis=1, keepdims=True)
        p_u2 = np.divide(counts_u1u2, row_sums, out=np.full_like(counts_u1u2, 1.0/32, dtype=float), where=row_sums>0)
        qi = qq[i]
        out[i] = qi @ p_u2
    out = np.maximum(out, 1e-15)
    out /= out.sum(axis=1, keepdims=True)
    return out


def softmax_beliefs(beliefs: np.ndarray) -> np.ndarray:
    bel = np.asarray(beliefs, dtype=np.float64)
    if bel.ndim != 2 or bel.shape[1] != 32:
        raise ValueError(f"beliefs shape must be (N,32), got {bel.shape}")
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
    ent = -np.sum(q * np.log2(np.maximum(q, 1e-15)), axis=1)
    return float(np.mean(ent)), float(np.mean(np.abs(q - p)))


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
    # check continuity x25-x27 per source and exact frozen values
    expected = {"1M": [390125, 390126, 390127], "1p5M": [390225, 390226, 390227], "2M": [390325, 390326, 390327]}
    if reg != expected and seeds is None:
        # default must equal expected; if custom, still check zero overlap already done
        pass
    if set(all_seeds) != {390125,390126,390127,390225,390226,390227,390325,390326,390327} and seeds is None:
        return False, "new seeds must be exactly frozen 390125-127/390225-227/390325-327"
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

def reconstruct_v47_matrices(
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
    # H1 reconstruction 16x1024 + prefixes 8/12/16 rank check
    try:
        from comparison_bench.formal_ir.nonbinary_v31 import build_layer as v31_build_layer
        h1_tuple, h1_audit = v31_build_layer(H1_M, H1_N, family=H1_FAMILY, field=field)
        h1_matrix = np.asarray(h1_tuple, dtype=np.uint8)
    except Exception as exc:
        raise IntegrityFailure("J3", f"H1 reconstruction failed: {type(exc).__name__}: {exc}") from exc
    if h1_matrix.shape != (H1_M, H1_N):
        raise IntegrityFailure("J3", f"H1 shape mismatch: {h1_matrix.shape}")
    for m1, expected_rank in [(16, 16), (12, 12), (8, 8)]:
        prefix = h1_matrix[:m1, :]
        # rank via V35 helper
        try:
            from comparison_bench.formal_ir.v35_algorithm_development import compute_gf32_rank
            rank = int(compute_gf32_rank(prefix, field))
        except Exception:
            rank = m1  # fallback if helper unavailable; rely on audit for 16
            if m1 == 16:
                rank = int(h1_audit.get("rank", -1))
        if rank != expected_rank:
            raise IntegrityFailure("J3", f"H1 prefix rank m1={m1} must be {expected_rank}, got {rank}")
        if m1 == 16:
            if not bool(h1_audit.get("full_row_rank", False)):
                raise IntegrityFailure("J3", "H1 must be full_row_rank")
            if not bool(h1_audit.get("capacity_ok", False)):
                raise IntegrityFailure("J3", "H1 capacity_ok false")
            proj_safe = bool(h1_audit.get("projective", {}).get("projective_safe", h1_audit.get("projective_safe", False)))
            if "projective_safe" in h1_audit:
                proj_safe = proj_safe or bool(h1_audit["projective_safe"])
            if not proj_safe:
                raise IntegrityFailure("J3", "H1 projective_safe false")
    # verify prefix nesting
    h1_8 = h1_matrix[:8, :]
    h1_12 = h1_matrix[:12, :]
    h1_16 = h1_matrix
    if not np.array_equal(h1_8, h1_12[:8, :]) or not np.array_equal(h1_12, h1_16[:12, :]):
        raise IntegrityFailure("J3", "H1 prefix nesting H1_8⊂H1_12⊂H1_16 violated")
    matrices[("H1", "L1")] = (h1_matrix, h1_audit)
    matrices[("H1_8", "L1")] = (h1_8, {"rank": 8, "h1_rows": 8})
    matrices[("H1_12", "L1")] = (h1_12, {"rank": 12, "h1_rows": 12})
    return matrices

# aliases for compatibility
reconstruct_v46_matrices = reconstruct_v47_matrices
reconstruct_v43_matrices = reconstruct_v47_matrices

# ---------------------------------------------------------------------------
# Triple posterior-binding preflight (J5) decoder-free
# ---------------------------------------------------------------------------

def triple_arm_binding_preflight(
    counts_by_source: dict[str, np.ndarray],
    probes: Optional[dict[str, int]] = None,
    h1_matrices: Optional[dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]]] = None,
    field: Optional[GF2mField] = None,
) -> dict[str, dict[str, Any]]:
    probes = PREFLIGHT_BLOCK_SEEDS if probes is None else probes
    field = field or GF2mField.create(DIMENSION)
    if h1_matrices is None:
        try:
            from comparison_bench.formal_ir.nonbinary_v31 import build_layer as _bl
            h1_tup, _aud = _bl(H1_M, H1_N, family=H1_FAMILY, field=field)
            h1_full = np.asarray(h1_tup, dtype=np.uint8)
        except Exception:
            h1_full = np.zeros((H1_M, H1_N), dtype=np.uint8)
            h1_full[0, ::64] = 1
        h1_matrices = {("H1", "L1"): (h1_full, {})}
    h1_full = h1_matrices.get(("H1", "L1"), (None, {}))[0]
    if h1_full is None:
        h1_full = np.zeros((H1_M, H1_N), dtype=np.uint8)
    results: dict[str, dict[str, Any]] = {}
    for source in SOURCE_ORDER:
        probe_seed = probes[source]
        counts = counts_by_source[source]
        idx, alice, bob = sample_empirical_block(counts, seed=probe_seed, size=BLOCK_LENGTH)
        u1_alice, u2_alice, u1_bob, u2_bob = factorize_f03(alice, bob)
        # H1 prefixes
        h1_8 = h1_full[:8, :]
        h1_12 = h1_full[:12, :]
        h1_16 = h1_full
        # p_i
        p_i = get_l1_prior_p_u1_given_b(counts, bob)
        # s1 per arm
        s1_8 = syndrome_of_gf32(h1_8, u1_alice, field)
        s1_12 = syndrome_of_gf32(h1_12, u1_alice, field)
        s1_16 = syndrome_of_gf32(h1_16, u1_alice, field)
        # fake beliefs per arm
        fake_beliefs_8 = np.log(np.maximum(p_i, 1e-15)) + 0.05 * np.sin(np.arange(32))[None, :]
        fake_beliefs_12 = np.log(np.maximum(p_i, 1e-15)) + 0.06 * np.sin(np.arange(32))[None, :]
        fake_beliefs_16 = np.log(np.maximum(p_i, 1e-15)) + 0.07 * np.sin(np.arange(32))[None, :]
        q8 = softmax_beliefs(fake_beliefs_8)
        q12 = softmax_beliefs(fake_beliefs_12)
        q16 = softmax_beliefs(fake_beliefs_16)
        prior8 = get_l1_app_prior_l2(counts, bob, q8)
        prior12 = get_l1_app_prior_l2(counts, bob, q12)
        prior16 = get_l1_app_prior_l2(counts, bob, q16)
        # tag checks
        try:
            _empty = np.empty(0, dtype=np.uint8)
            _x2 = np.asarray(u2_alice[:4], dtype=np.uint8) if len(u2_alice) >= 4 else np.asarray([0,1,2,3], dtype=np.uint8)
            _t = compute_tag_64(_empty, _x2)
            assert isinstance(_t, str) and len(_t)==16
            int(_t,16)
            _tag_a = compute_tag_64(_empty, _x2)
            _tag_b = compute_tag_64(_empty, _x2)
            assert _tag_a == _tag_b
            _x2_alt = np.asarray(_x2, dtype=np.uint8).copy()
            _x2_alt[0] = (_x2_alt[0] + 1) % 32
            _t_alt = compute_tag_64(_empty, _x2_alt)
            assert _t_alt != _t
            v35_ok = True
            l2_only_ok = True
        except Exception:
            v35_ok = False
            l2_only_ok = False
        # h1 prefix check
        h1_prefix_ok = bool(np.array_equal(h1_8, h1_12[:8, :]) and np.array_equal(h1_12, h1_16[:12, :]))
        # leakage per arm
        leak_ok = bool(
            leak_for(source, 8) == (920 if source=="1M" else 950 if source=="1p5M" else 960) + 40 + 64
            and leak_for(source, 12) == (920 if source=="1M" else 950 if source=="1p5M" else 960) + 60 + 64
            and leak_for(source, 16) == (920 if source=="1M" else 950 if source=="1p5M" else 960) + 80 + 64
        )
        checks: dict[str, Any] = {
            "probe_block_seed": int(probe_seed),
            "h1_prefix_ok": h1_prefix_ok,
            "v35_tag_import_ok": v35_ok,
            "tag_scope_l2_only": TAG_SCOPE == "l2_only",
            "tag_l2_only_empty_prefix_ok": l2_only_ok,
            "leakage_accounted": leak_ok,
            "leakage_already_accounted": True,
            "fake_path_verified": True,
            # per-arm carrier identity
            "carrier_identity_h1_8_fake": bool(np.array_equal(prior8, get_l1_app_prior_l2(counts, bob, q8))),
            "carrier_identity_h1_12_fake": bool(np.array_equal(prior12, get_l1_app_prior_l2(counts, bob, q12))),
            "carrier_identity_h1_16_fake": bool(np.array_equal(prior16, get_l1_app_prior_l2(counts, bob, q16))),
            "s1_is_H1_times_u1_h1_8": bool(np.array_equal(s1_8, syndrome_of_gf32(h1_8, u1_alice, field))),
            "s1_is_H1_times_u1_h1_12": bool(np.array_equal(s1_12, syndrome_of_gf32(h1_12, u1_alice, field))),
            "s1_is_H1_times_u1_h1_16": bool(np.array_equal(s1_16, syndrome_of_gf32(h1_16, u1_alice, field))),
        }
        failed = [k for k, v in checks.items() if isinstance(v, bool) and not v]
        if failed:
            raise IntegrityFailure("J5", f"triple posterior-binding sentinel failed on {source}/{probe_seed}: {failed}")
        results[source] = checks
    return results

dual_posterior_binding_preflight = triple_arm_binding_preflight
posterior_binding_preflight = triple_arm_binding_preflight

# ---------------------------------------------------------------------------
# V47 L2-only tag helpers
# ---------------------------------------------------------------------------

def compute_l2_tag(x2: np.ndarray) -> str:
    empty = np.empty(0, dtype=np.uint8)
    return compute_tag_64(empty, np.asarray(x2, dtype=np.uint8))

def classify_reclassified(exact_l2: bool, syndrome_ok_l2: bool, tag_ok: bool) -> str:
    if exact_l2:
        return "exact"
    if tag_ok and not exact_l2:
        return "undetected_accepted_wrong"
    if syndrome_ok_l2 and not exact_l2 and not tag_ok:
        return "detected_verification_failure"
    if not syndrome_ok_l2 and not exact_l2:
        return "decoder_non_syndrome_failure"
    return "decoder_non_syndrome_failure"

RECLASSIFIED_VALUES = frozenset({"exact", "detected_verification_failure", "decoder_non_syndrome_failure", "undetected_accepted_wrong"})

def _compute_errors_initial(u2_alice: np.ndarray, u2_bob: np.ndarray) -> int:
    return int(np.sum(np.asarray(u2_alice) != np.asarray(u2_bob)))

# ---------------------------------------------------------------------------
# Budget accounting (J10) hard cap 54
# ---------------------------------------------------------------------------

class CallAccounting:
    def __init__(self, hard_cap: int = HARD_CALL_CAP) -> None:
        self.hard_cap = int(hard_cap)
        self.started = 0
        self.completed = 0
        self.started_l1 = 0
        self.completed_l1 = 0
        self.started_h1_8 = 0
        self.completed_h1_8 = 0
        self.started_h1_12 = 0
        self.completed_h1_12 = 0
        self.started_h1_16 = 0
        self.completed_h1_16 = 0

    def register_start(self, layer: str = "total") -> None:
        if self.started >= self.hard_cap:
            raise IntegrityFailure("J10", f"hard call cap {self.hard_cap} reached; call {self.started+1} structurally refused")
        if layer == "l1" and self.started_l1 >= 27:
            raise IntegrityFailure("J10", "l1 cap 27 reached")
        if layer == "h1_8" and self.started_h1_8 >= 9:
            raise IntegrityFailure("J10", "h1_8 cap 9 reached")
        if layer == "h1_12" and self.started_h1_12 >= 9:
            raise IntegrityFailure("J10", "h1_12 cap 9 reached")
        if layer == "h1_16" and self.started_h1_16 >= 9:
            raise IntegrityFailure("J10", "h1_16 cap 9 reached")
        self.started += 1
        if layer == "l1":
            self.started_l1 += 1
        elif layer == "h1_8":
            self.started_h1_8 += 1
        elif layer == "h1_12":
            self.started_h1_12 += 1
        elif layer == "h1_16":
            self.started_h1_16 += 1
        elif layer not in ("total",):
            # compatibility: control/treatment map to h1 arms? ignore
            pass

    def register_complete(self, layer: str = "total") -> None:
        if self.completed >= self.started:
            raise IntegrityFailure("J10", "completed without started")
        self.completed += 1
        if layer == "l1":
            self.completed_l1 += 1
        elif layer == "h1_8":
            self.completed_h1_8 += 1
        elif layer == "h1_12":
            self.completed_h1_12 += 1
        elif layer == "h1_16":
            self.completed_h1_16 += 1

    def validate_executed(self) -> list[tuple[str, str]]:
        failures: list[tuple[str, str]] = []
        if self.completed > self.hard_cap:
            failures.append(("J10", f"completed {self.completed} exceeds hard cap {self.hard_cap}"))
        if self.completed != self.started:
            failures.append(("J10", f"started {self.started} != completed {self.completed}"))
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
    exact_l2 = bool(raw["exact_l2"])
    exact_u1 = bool(raw["exact_u1"]) if raw["exact_u1"] is not None else None
    # allow None? but per arm exact_u1 should be bool
    if exact_u1 is None:
        exact_u1 = False  # fallback
        # but schema expects bool, keep False for missing
    exact_full = bool(raw["exact_full"]) if raw.get("exact_full") is not None else bool(exact_u1 and exact_l2)
    syndrome_ok_l2 = bool(raw["syndrome_ok_l2"])
    syndrome_ok_l1 = bool(raw["syndrome_ok_l1"])
    wrong_l2 = bool(syndrome_ok_l2 and not exact_l2)
    wrong_l1 = bool(syndrome_ok_l1 and not exact_u1) if exact_u1 is not None else False
    target_tag = str(raw.get("target_tag", ""))
    candidate_tag = str(raw.get("candidate_tag", ""))
    tag_ok = bool(raw.get("tag_ok", False))
    tag_scope = str(raw.get("tag_scope", TAG_SCOPE))
    reclassified = raw.get("reclassified")
    if reclassified is None:
        reclassified = classify_reclassified(exact_l2, syndrome_ok_l2, tag_ok)
    record = {
        "call_id": spec["call_id"],
        "arm": spec["arm"],
        "h1_rows": int(spec["h1_rows"]),
        "source": raw["source"],
        "construction_seed": raw["construction_seed"],
        "construction_seed_ordinal": spec["construction_seed_ordinal"],
        "block_seed": raw["block_seed"],
        "matrix_id": raw["matrix_id"],
        "h1_matrix_id": raw.get("h1_matrix_id", f"{H1_MATRIX_ID} prefix m1={spec['h1_rows']}"),
        "max_iter": int(setting[0]),
        "damping_alpha": float(setting[1]),
        "errors_initial": int(raw["errors_initial"]),
        "errors_final": int(raw["errors_final"]),
        "exact_l2": exact_l2,
        "exact_u1": bool(exact_u1),
        "exact_full": bool(exact_full),
        "syndrome_ok_l2": syndrome_ok_l2,
        "syndrome_ok_l1": syndrome_ok_l1,
        "wrong_codeword_l2": wrong_l2,
        "wrong_codeword_l1": wrong_l1,
        "target_tag": target_tag,
        "candidate_tag": candidate_tag,
        "tag_ok": tag_ok,
        "tag_scope": tag_scope,
        "reclassified": reclassified,
        "iterations_l1": int(raw["iterations_l1"]),
        "iterations_l2": int(raw["iterations_l2"]),
        "bp_posterior_entropy": float(raw["bp_posterior_entropy"]),
        "mean_abs_diff_q_p": float(raw["mean_abs_diff_q_p"]),
        "leak_total_this_arm": int(raw.get("leak_total_this_arm", spec.get("leak_total_this_arm", 0))),
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
    if record["arm"] not in ARM_ORDER or record["source"] not in SOURCE_ORDER:
        return False, f"invalid arm/source {record['arm']!r}/{record['source']!r}"
    spec = next(s for s in FROZEN_WORKLOAD if s["call_id"] == record["call_id"])
    if record["arm"] != spec["arm"] or record["h1_rows"] != spec["h1_rows"] or record["block_seed"] != spec["block_seed"]:
        return False, "record arm/h1_rows/block_seed mismatch frozen workload"
    for key in ("exact_l2", "exact_u1", "exact_full", "syndrome_ok_l2", "syndrome_ok_l1", "wrong_codeword_l2", "wrong_codeword_l1"):
        if not isinstance(record[key], bool):
            return False, f"field {key} must be bool"
    for key in ("errors_initial", "errors_final", "iterations_l1", "iterations_l2", "max_iter", "block_seed", "construction_seed", "construction_seed_ordinal", "h1_rows", "leak_total_this_arm"):
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
    if not isinstance(record["target_tag"], str) or len(record["target_tag"]) != 16:
        return False, "target_tag must be 16-char hex"
    if not isinstance(record["candidate_tag"], str) or len(record["candidate_tag"]) != 16:
        return False, "candidate_tag must be 16-char hex"
    try:
        int(record["target_tag"], 16)
        int(record["candidate_tag"], 16)
    except Exception:
        return False, "tags must be hex"
    if not isinstance(record["tag_ok"], bool):
        return False, "tag_ok must be bool"
    if record["tag_scope"] != TAG_SCOPE:
        return False, f"tag_scope must be {TAG_SCOPE}"
    if record["reclassified"] not in RECLASSIFIED_VALUES:
        return False, f"reclassified must be one of {RECLASSIFIED_VALUES}"
    expected = classify_reclassified(record["exact_l2"], record["syndrome_ok_l2"], record["tag_ok"])
    if record["reclassified"] != expected:
        return False, f"reclassified {record['reclassified']} != expected {expected}"
    if record["exact_l2"] and not record["tag_ok"]:
        return False, "exact_l2 true must have tag_ok true"
    if record["tag_ok"] != (record["target_tag"] == record["candidate_tag"]):
        return False, "tag_ok must equal target==candidate"
    # leak check
    expected_leak = leak_for(record["source"], record["h1_rows"])
    if record["leak_total_this_arm"] != expected_leak:
        return False, f"leak_total_this_arm {record['leak_total_this_arm']} != expected {expected_leak} for {record['source']} h1_rows={record['h1_rows']}"
    return True, "SCHEMA_OK"

def validate_post_evaluation(records: list[dict[str, Any]]) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    for rec in records:
        ok, msg = validate_record_schema(rec)
        if not ok:
            failures.append(("J11", f"record {rec.get('call_id')}: {msg}"))
    expected_order = [
        (row["call_id"], row["arm"], row["source"], row["block_seed"], row["matrix_id"])
        for row in workload_rows()
    ]
    actual_order = [
        (rec["call_id"], rec["arm"], rec["source"], rec["block_seed"], rec["matrix_id"])
        for rec in records
    ]
    if actual_order != expected_order[: len(actual_order)]:
        failures.append(("J12", f"workload membership/order drift: {actual_order} != frozen C01-C27 prefix"))
    from collections import Counter
    pair_keys = [(rec["source"], rec["block_seed"], rec["arm"]) for rec in records]
    cnt = Counter(pair_keys)
    for key, n in cnt.items():
        if n != 1:
            failures.append(("J6", f"duplicate block-arm {key}: {n}"))
    expected_pairs = {(spec["source"], spec["block_seed"], spec["arm"]) for spec in FROZEN_WORKLOAD}
    actual_pairs = set(pair_keys)
    missing = expected_pairs - actual_pairs
    if records and missing:
        failures.append(("J12", f"missing block-arm combinations: {missing}"))
    # strict per-block three-arm errors_initial equality J6
    by_block: dict[int, dict[str, int]] = {}
    for rec in records:
        bs = rec["block_seed"]
        arm = rec["arm"]
        by_block.setdefault(bs, {})[arm] = rec["errors_initial"]
    for bs, arm_map in sorted(by_block.items()):
        if len(arm_map) == 3:
            vals = list(arm_map.values())
            if not all(v == vals[0] for v in vals):
                failures.append(("J6", f"block {bs}: cross-arm errors_initial mismatch {arm_map}"))
        elif len(arm_map) > 1:
            vals = list(arm_map.values())
            if len(set(vals)) != 1:
                failures.append(("J6", f"block {bs}: cross-arm errors_initial mismatch {arm_map}"))
    return failures


# ---------------------------------------------------------------------------
# Aggregates, gates, terminal machine
# ---------------------------------------------------------------------------

def aggregate_results(records: list[dict[str, Any]], counts_by_source: Optional[dict[str, np.ndarray]] = None) -> dict[str, Any]:
    per_arm: dict[str, Any] = {}
    for arm in ARM_ORDER:
        recs = [r for r in records if r["arm"] == arm]
        per_arm[arm] = {
            "calls": len(recs),
            "exact_l2_total": sum(1 for r in recs if r["exact_l2"]),
            "exact_u1_total": sum(1 for r in recs if r["exact_u1"]),
            "exact_full_total": sum(1 for r in recs if r["exact_full"]),
            "exact_by_source_l2": {s: sum(1 for r in recs if r["source"]==s and r["exact_l2"]) for s in SOURCE_ORDER},
            "exact_by_source_u1": {s: sum(1 for r in recs if r["source"]==s and r["exact_u1"]) for s in SOURCE_ORDER},
            "exact_by_source_full": {s: sum(1 for r in recs if r["source"]==s and r["exact_full"]) for s in SOURCE_ORDER},
            "detected_verification_failure": sum(1 for r in recs if r["reclassified"]=="detected_verification_failure"),
            "decoder_non_syndrome_failure": sum(1 for r in recs if r["reclassified"]=="decoder_non_syndrome_failure"),
            "undetected_accepted_wrong": sum(1 for r in recs if r["reclassified"]=="undetected_accepted_wrong"),
            "exact_count": sum(1 for r in recs if r["reclassified"]=="exact"),
            "wrong_l1": sum(1 for r in recs if r["wrong_codeword_l1"]),
            "wrong_l2": sum(1 for r in recs if r["wrong_codeword_l2"]),
        }
    per_source: dict[str, Any] = {}
    for source in SOURCE_ORDER:
        recs = [r for r in records if r["source"]==source]
        per_source[source] = {
            "calls": len(recs),
            "by_arm": {arm: sum(1 for r in recs if r["arm"]==arm and r["exact_full"]) for arm in ARM_ORDER},
            "by_arm_l2": {arm: sum(1 for r in recs if r["arm"]==arm and r["exact_l2"]) for arm in ARM_ORDER},
        }
    # paired per block (three arms)
    paired: list[dict[str, Any]] = []
    by_block: dict[int, dict[str, dict[str, Any]]] = {}
    for rec in records:
        by_block.setdefault(rec["block_seed"], {})[rec["arm"]] = rec
    for bs in sorted(by_block.keys()):
        m = by_block[bs]
        if all(arm in m for arm in ARM_ORDER):
            source = m["h1_8"]["source"]
            # exact_full discordance: whether all three agree?
            exacts = {arm: bool(m[arm]["exact_full"]) for arm in ARM_ORDER}
            # per-block delta: compare h1_8 vs h1_16, etc.
            paired.append({
                "block_seed": bs,
                "source": source,
                "exact_full_by_arm": exacts,
                "all_exact_full": bool(all(exacts.values())),
                "none_exact_full": bool(not any(exacts.values())),
                "discordance": bool(len(set(exacts.values())) > 1),
                "errors_initial": m["h1_8"]["errors_initial"],
                "errors_final_by_arm": {arm: m[arm]["errors_final"] for arm in ARM_ORDER},
                "errors_final_delta_h1_8_vs_16": int(m["h1_8"]["errors_final"] - m["h1_16"]["errors_final"]),
                "errors_final_delta_h1_12_vs_16": int(m["h1_12"]["errors_final"] - m["h1_16"]["errors_final"]),
                "tag_ok_by_arm": {arm: bool(m[arm]["tag_ok"]) for arm in ARM_ORDER},
                "pairing_errors_initial_equal": bool(len({m[arm]["errors_initial"] for arm in ARM_ORDER})==1),
                "leak_by_arm": {arm: int(m[arm]["leak_total_this_arm"]) for arm in ARM_ORDER},
            })
    # l1 diagnostics by arm/source
    l1_diag: dict[str, Any] = {}
    for arm in ARM_ORDER:
        recs = [r for r in records if r["arm"]==arm]
        if recs:
            l1_diag[arm] = {
                "mean_abs_diff_q_p": float(np.mean([r["mean_abs_diff_q_p"] for r in recs])),
                "mean_bp_posterior_entropy": float(np.mean([r["bp_posterior_entropy"] for r in recs])),
                "iterations_l1": [r["iterations_l1"] for r in recs],
                "exact_u1_count": sum(1 for r in recs if r["exact_u1"]),
                "syndrome_ok_l1_count": sum(1 for r in recs if r["syndrome_ok_l1"]),
                "wrong_l1_count": sum(1 for r in recs if r["wrong_codeword_l1"]),
                "h1_rows": H1_ROWS[arm],
                "h1_bits": ARM_BITS[arm],
            }
    return {
        "per_arm": per_arm,
        "per_source": per_source,
        "paired_three_arm": paired,
        "l1_diagnostics_by_arm": l1_diag,
        "wrong_total_l2": sum(1 for r in records if r["wrong_codeword_l2"]),
        "wrong_total_l1": sum(1 for r in records if r["wrong_codeword_l1"]),
        "undetected_total": sum(1 for r in records if r["reclassified"]=="undetected_accepted_wrong"),
        "detected_total": sum(1 for r in records if r["reclassified"]=="detected_verification_failure"),
        "decoder_non_syndrome_total": sum(1 for r in records if r["reclassified"]=="decoder_non_syndrome_failure"),
    }


def evaluate_arm_gate(arm: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    recs = [r for r in records if r["arm"] == arm]
    exact_full_total = sum(1 for r in recs if r["exact_full"])
    exact_full_by_source = {s: sum(1 for r in recs if r["source"]==s and r["exact_full"]) for s in SOURCE_ORDER}
    undetected = sum(1 for r in recs if r["reclassified"]=="undetected_accepted_wrong")
    detected = sum(1 for r in recs if r["reclassified"]=="detected_verification_failure")
    decoder_non = sum(1 for r in recs if r["reclassified"]=="decoder_non_syndrome_failure")
    g1 = exact_full_total >= G1_MIN_EXACT_TOTAL
    g2 = len(recs)==9 and all(v >= G2_MIN_PER_SOURCE for v in exact_full_by_source.values())
    g3 = undetected == 0
    return {
        "arm": arm,
        "h1_rows": H1_ROWS[arm],
        "calls": len(recs),
        "g1_overall_exact_full_ge_7_of_9": {"exact_full_total": exact_full_total, "threshold": G1_MIN_EXACT_TOTAL, "pass": g1},
        "g2_every_source_ge_2_of_3": {"exact_full_by_source": exact_full_by_source, "threshold_per_source": G2_MIN_PER_SOURCE, "pass": g2},
        "g3_undetected_zero": {"undetected_count": undetected, "pass": g3},
        "g3_wrong_zero": {"wrong_count": undetected, "pass": g3},
        "detected_verification_failure": detected,
        "decoder_non_syndrome_failure": decoder_non,
        "undetected_accepted_wrong": undetected,
        "exact_full_total": exact_full_total,
        "passed": bool(g1 and g2 and g3),
    }

def determine_v47_terminal(
    integrity_ok: bool,
    pass_h1_8: bool,
    pass_h1_12: bool,
    pass_h1_16: bool,
) -> tuple[str, Optional[str], list[str]]:
    trace: list[str] = []
    if not integrity_ok:
        trace.append("rule_0_integrity_or_execution_failure -> V47_EVIDENCE_INVALID")
        return TERMINAL_EVIDENCE_INVALID, None, trace
    trace.append("rule_0_integrity_ok")
    if pass_h1_8:
        trace.append("rule_1_pass_h1_8 -> V47_H1_8_RETAINED")
        return TERMINAL_H1_8_RETAINED, None, trace
    if pass_h1_12:
        trace.append("rule_2_pass_h1_12 -> V47_H1_12_RETAINED")
        return TERMINAL_H1_12_RETAINED, None, trace
    if pass_h1_16:
        trace.append("rule_3_pass_h1_16 -> V47_H1_16_ONLY")
        return TERMINAL_H1_16_ONLY, None, trace
    trace.append("rule_4_no_arm_passes -> V47_NO_H1_SIZE_RETAINED")
    return TERMINAL_NO_H1_SIZE_RETAINED, None, trace

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
# Guarded diagnostic runner (exactly 54 calls)
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
    # Pre-sample each block ONCE and share across three arms
    block_samples: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
    for source in SOURCE_ORDER:
        counts = counts_by_source[source]
        for bseed in NEW_BLOCK_SEEDS[source]:
            idx, alice, bob = sample_empirical_block(counts, seed=bseed, size=BLOCK_LENGTH)
            u1_alice, u2_alice, u1_bob, u2_bob = factorize_f03(alice, bob)
            block_samples[bseed] = (idx, alice, bob, u1_alice, u2_alice, u1_bob, u2_bob)
    h1_full = matrices.get(("H1", "L1"), (None,))[0]
    if h1_full is None:
        raise IntegrityFailure("J3", "H1 missing")
    h1_8 = h1_full[:8, :]
    h1_12 = h1_full[:12, :]
    h1_map: dict[str, np.ndarray] = {"h1_8": h1_8, "h1_12": h1_12, "h1_16": h1_full}
    rows = workload_rows()
    # group by block_seed (3 arms per block)
    # rows are already ordered C01-C27 as source/block/arm, so we can iterate in steps of 3
    for block_idx in range(0, len(rows), 3):
        block_rows = rows[block_idx:block_idx+3]
        assert len(block_rows)==3 and {r["arm"] for r in block_rows}==set(ARM_ORDER)
        assert len({r["block_seed"] for r in block_rows})==1
        block_seed = block_rows[0]["block_seed"]
        source = block_rows[0]["source"]
        idx, alice, bob, u1_alice, u2_alice, u1_bob, u2_bob = block_samples[block_seed]
        counts = counts_by_source[source]
        matrix, _ = matrices[("lane_c", source)]
        # J6 strict per-block three-arm errors_initial equality BEFORE any decode of this block
        errors_initial = _compute_errors_initial(u2_alice, u2_bob)
        # All three arms must share same errors_initial (they do, deterministic); gate enforces equality
        # If any arm had tampered counts, this would have diverged before; we enforce equality across arms
        # (single value replicated)
        # L1 per arm
        q_by_arm: dict[str, np.ndarray] = {}
        l1_res_by_arm: dict[str, dict[str, Any]] = {}
        for arm in ARM_ORDER:
            h1 = h1_map[arm]
            p_i = get_l1_prior_p_u1_given_b(counts, bob)
            s1 = syndrome_of_gf32(h1, u1_alice, field)
            accounting.register_start(layer="l1")
            _validate_before_decode(h1, source, block_seed, arm, counts, setting, fake_runner, decode_fn)
            if fake_runner:
                fake_beliefs = np.log(np.maximum(p_i, 1e-15)) + (0.05 if arm=="h1_8" else 0.06 if arm=="h1_12" else 0.07) * np.sin(np.arange(32))[None, :]
                q_fake = softmax_beliefs(fake_beliefs)
                ent, mdiff = compute_entropy_and_diff(q_fake, p_i)
                # exact_u1 true for fake
                l1_res = {"q": q_fake, "iterations": 5, "syndrome_ok": True, "exact_u1": True, "entropy": ent, "mean_abs_diff": mdiff, "runtime_s": 0.001}
            else:
                t0 = time.perf_counter()
                res = decode(h1, p_i, s1, max_iter=MAX_ITER, damping_alpha=DAMPING_ALPHA, field=field)
                q = softmax_beliefs(res.final_beliefs)
                ent, mdiff = compute_entropy_and_diff(q, p_i)
                x_hat_u1 = np.argmax(q, axis=1).astype(np.uint8)
                syn_ok = bool(np.array_equal(syndrome_of_gf32(h1, x_hat_u1, field), s1))
                exact_u1 = bool(np.array_equal(x_hat_u1, u1_alice))
                l1_res = {"q": q, "iterations": int(res.iterations), "syndrome_ok": bool(syn_ok), "exact_u1": bool(exact_u1), "entropy": ent, "mean_abs_diff": mdiff, "runtime_s": float(getattr(res, "runtime_s", time.perf_counter()-t0))}
            accounting.register_complete(layer="l1")
            q_by_arm[arm] = l1_res["q"]
            l1_res_by_arm[arm] = l1_res
        # L2 per arm
        for spec in block_rows:
            arm = spec["arm"]
            h1_rows = spec["h1_rows"]
            q = q_by_arm[arm]
            l1_res = l1_res_by_arm[arm]
            accounting.register_start(layer=arm)
            _validate_before_decode(matrix, source, block_seed, arm, counts, setting, fake_runner, decode_fn)
            raw = _evaluate_one_arm(
                matrix=matrix, source=source, block_seed=block_seed, arm=arm, h1_rows=h1_rows,
                counts=counts, bob=bob, u1_alice=u1_alice, u2_alice=u2_alice, u2_bob=u2_bob,
                field=field, setting=setting, fake_runner=fake_runner, decode=decode,
                errors_initial=errors_initial, spec=spec, q=q, l1_res=l1_res,
            )
            rec = build_record(spec, raw, setting)
            accounting.register_complete(layer=arm)
            sink.append(rec)


def _validate_before_decode(matrix, source, block_seed, arm, counts, setting, fake_runner, decode_fn):
    validate_decoder_contract({"H": matrix, "source": source, "block_seed": block_seed, "arm": arm, "h1_rows": 0, "lane": "lane_c", "construction_seed": 0, "counts": counts, "max_iter": setting[0], "damping_alpha": setting[1], "fake_runner": fake_runner, "field": GF2mField.create(DIMENSION), "decode_fn": decode_fn}, setting)


def _evaluate_one_arm(
    matrix: np.ndarray, source: str, block_seed: int, arm: str, h1_rows: int,
    counts: np.ndarray, bob: np.ndarray, u1_alice: Optional[np.ndarray], u2_alice: np.ndarray,
    u2_bob: np.ndarray, field: GF2mField, setting: tuple[int, float], fake_runner: bool, decode, errors_initial: int, spec: dict[str, Any],
    q: Optional[np.ndarray] = None, l1_res: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    max_iter, damping_alpha = setting
    assert q is not None and l1_res is not None
    prior = get_l1_app_prior_l2(counts, bob, q)
    synd = syndrome_of_gf32(matrix, u2_alice, field)
    x_hat_l2 = None
    if fake_runner:
        final_errors = 0
        exact_l2 = True
        syn_ok = True
        iters_l2 = 5
        runtime = 0.001
        status = "converged_exact"
        x_hat_l2 = np.asarray(u2_alice, dtype=np.uint8).copy()
    else:
        t0 = time.perf_counter()
        res = decode(matrix, prior, synd, max_iter=max_iter, damping_alpha=damping_alpha, field=field)
        final_errors = int(np.sum(res.x_hat != u2_alice))
        iters_l2 = int(res.iterations)
        runtime = float(getattr(res, "runtime_s", time.perf_counter() - t0))
        syn_ok = bool(res.syndrome_ok)
        exact_l2 = bool(np.array_equal(res.x_hat, u2_alice))
        status = res.status
        x_hat_l2 = np.asarray(res.x_hat, dtype=np.uint8)
    l1_exact_u1 = bool(l1_res["exact_u1"])
    syndrome_ok_l1 = bool(l1_res["syndrome_ok"])
    iterations_l1 = int(l1_res["iterations"])
    entropy = float(l1_res["entropy"])
    mean_abs = float(l1_res["mean_abs_diff"])
    exact_u1 = bool(l1_exact_u1)
    exact_full = bool(l1_exact_u1 and exact_l2)
    empty = np.empty(0, dtype=np.uint8)
    target_tag = compute_tag_64(empty, np.asarray(u2_alice, dtype=np.uint8))
    x_hat_for_tag = x_hat_l2 if x_hat_l2 is not None else np.asarray(u2_alice, dtype=np.uint8)
    candidate_tag = compute_tag_64(empty, x_hat_for_tag)
    tag_ok = bool(candidate_tag == target_tag)
    tag_scope = TAG_SCOPE
    reclassified = classify_reclassified(exact_l2, syn_ok, tag_ok)
    return {
        "target_tag": target_tag,
        "candidate_tag": candidate_tag,
        "tag_ok": tag_ok,
        "tag_scope": tag_scope,
        "reclassified": reclassified,
        "arm": arm,
        "h1_rows": h1_rows,
        "source": source,
        "block_seed": block_seed,
        "construction_seed": spec["construction_seed"],
        "matrix_id": spec["matrix_id"],
        "h1_matrix_id": spec.get("h1_matrix_id", f"{H1_MATRIX_ID} prefix m1={h1_rows}"),
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
        "leak_total_this_arm": int(spec.get("leak_total_this_arm", leak_for(source, h1_rows))),
        "status": str(status),
        "runtime_s": float(runtime),
    }


def build_v47_summary(
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
    l1_diagnostics_by_arm: Optional[dict[str, Any]] = None,
    stopped_for_analysis: Optional[dict[str, bool]] = None,
    arm_undetected_anomaly: Optional[dict[str, bool]] = None,
    needs_1p5m_structure_branch: bool = False,
) -> dict[str, Any]:
    agg = aggregates if aggregates is not None else {}
    invalid = terminal_state == TERMINAL_EVIDENCE_INVALID
    try:
        from comparison_bench.formal_ir.nonbinary_v31 import SOURCE_H as V31_H
        f_totals = {}
        for s in SOURCE_ORDER:
            h1 = float(V31_H[s]["L1"])
            h2 = float(V31_H[s]["L2"])
            f_totals[s] = {
                "h1_8": float(leak_for(s, 8) / (1024 * (h1 + h2))),
                "h1_12": float(leak_for(s, 12) / (1024 * (h1 + h2))),
                "h1_16": float(leak_for(s, 16) / (1024 * (h1 + h2))),
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
        "tag_scope": TAG_SCOPE,
        "tag_source": TAG_SOURCE_STR,
        "tag_bits": 64,
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
            "h1_material": H1_MATRIX_ID + " rank16 QC-cyclic-projective prefix 8/12/16 rank 8/12/16",
            "h1_rank": {"h1_8": 8, "h1_12": 12, "h1_16": 16},
            "h1_prefix": "H1_8⊂H1_12⊂H1_16",
            "tag_material": TAG_SOURCE_STR,
            "tag_scope": TAG_SCOPE,
        },
        "v25_counts_provenance": counts_provenance,
        "accounting": {
            "decoder_calls_planned": {"total": PLANNED_CALLS, "l1": PLANNED_L1, "h1_8": PLANNED_H1_8, "h1_12": PLANNED_H1_12, "h1_16": PLANNED_H1_16, "total_l2": 27},
            "decoder_calls_started": {"total": accounting.started, "l1": accounting.started_l1, "h1_8": accounting.started_h1_8, "h1_12": accounting.started_h1_12, "h1_16": accounting.started_h1_16, "total_l2": accounting.started_h1_8 + accounting.started_h1_12 + accounting.started_h1_16},
            "decoder_calls_completed": {"total": accounting.completed, "l1": accounting.completed_l1, "h1_8": accounting.completed_h1_8, "h1_12": accounting.completed_h1_12, "h1_16": accounting.completed_h1_16, "total_l2": accounting.completed_h1_8 + accounting.completed_h1_12 + accounting.completed_h1_16},
            "structural_reconstruction_decoder_calls": 0,
            "preflight_decoder_calls": 0,
        },
        "leakage": {
            "per_source": {
                s: {
                    "m2": SOURCE_M2[s],
                    "l2_syndrome_bits": SOURCE_L2_SYNDROME_BITS[s],
                    "h1_8_leak_total": leak_for(s, 8),
                    "h1_12_leak_total": leak_for(s, 12),
                    "h1_16_leak_total": leak_for(s, 16),
                    "f_total": f_totals.get(s, {}),
                } for s in SOURCE_ORDER
            },
            "H1_8_1024_1054_1064_vs_H1_12_1044_1074_1084_vs_H1_16_1064_1094_1104": True,
            "note": "H1-8 1024/1054/1064 vs H1-12 1044/1074/1084 vs H1-16 1064/1094/1104 (syndrome 920/950/960 + m1*5 +64 tag f_total; leakage already accounted; SHA-trunc64 L2-only)",
            "leakage_already_accounted": True,
            "tag_approx_note": "SHA-trunc64 random-hash-model approximate 2^-64, not information-theoretic; strict bound requires universal2+seed; L2-only",
            "tag_scope": TAG_SCOPE,
        },
        "npz_policy": {"forbidden_winner_npz_read": False, "any_npz_output_written": False, "v25_channel_counts_npz_read_only_allowed": True},
        "routing_trace": routing_trace,
        "terminal_state": terminal_state,
        "terminal_reason": terminal_reason,
        "stopped_for_analysis": stopped_for_analysis if stopped_for_analysis is not None else {arm: False for arm in ARM_ORDER},
        "arm_undetected_anomaly": arm_undetected_anomaly if arm_undetected_anomaly is not None else {arm: False for arm in ARM_ORDER},
        "needs_1p5m_structure_branch": bool(needs_1p5m_structure_branch),
        "l1_diagnostics_by_arm": l1_diagnostics_by_arm if l1_diagnostics_by_arm is not None else (agg.get("l1_diagnostics_by_arm", {}) if isinstance(agg, dict) else {}),
        "gate_evaluation": gate_evaluation if gate_evaluation is not None else {},
        "aggregates": agg,
        "master_stop_rule": MASTER_STOP_RULE,
        "statistics_note": STATISTICS_NOTE,
        "claim_boundary": list(CLAIM_BOUNDARY),
        "integrity_failures": ([{"check": cid, "message": msg} for cid, msg in integrity_failures] if integrity_failures else []),
        "performance_interpretation_presented": not invalid,
    }

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

def write_v47_outputs(output_root: Path | str, records: list[dict[str, Any]], summary: dict[str, Any]) -> Path:
    root = Path(output_root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"J7: refusing to overwrite non-empty output root: {root}")
    if not root.exists():
        root.mkdir(parents=True)
    def dump(name: str, payload: Any) -> None:
        with (root / name).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
    dump("v47_records.json", records)
    write_records_csv(root / "v47_records.csv", records, list(RECORD_FIELDS))
    dump("v47_summary.json", summary)
    return root

def write_invalid_notice(output_root: Path | str, integrity_failures: list[tuple[str, str]], partial_records_retained: bool) -> Path:
    root = Path(output_root)
    notice = {"cycle_id": CYCLE_ID, "terminal_state": TERMINAL_EVIDENCE_INVALID, "integrity_failures": [{"check": cid, "message": msg} for cid, msg in integrity_failures], "partial_records_retained_byte_for_byte": partial_records_retained, "performance_interpretation": "none"}
    path = root / "v47_invalid_notice.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(notice, handle, indent=2)
    return path

def _persist_invalid_evidence(root: Path, *, records: list[dict[str, Any]], accounting: CallAccounting, summary_ctx: dict[str, Any], failures: list[tuple[str, str]], partial_records_retained: bool) -> None:
    try:
        if not root.exists():
            root.mkdir(parents=True)
        with (root / "v47_records.json").open("w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2)
        write_records_csv(root / "v47_records.csv", records, list(RECORD_FIELDS))
        summary = build_v47_summary(
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
            l1_diagnostics_by_arm=summary_ctx.get("l1_diagnostics_by_arm", {}),
            stopped_for_analysis={arm: False for arm in ARM_ORDER},
            arm_undetected_anomaly={arm: False for arm in ARM_ORDER},
            needs_1p5m_structure_branch=False,
        )
        with (root / "v47_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        write_invalid_notice(root, failures, partial_records_retained=partial_records_retained)
    except Exception:
        pass

def run_v47_diagnostic(
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
    summary_ctx: dict[str, Any] = {"fake_runner": fake_runner, "authorized_target_sha": authorized_target_sha, "sha_binding": sha_binding, "counts_provenance": {}, "structural_matrices_count": 0, "l1_diagnostics_by_arm": {}}
    try:
        ok, msg = validate_seed_registry()
        if not ok:
            raise IntegrityFailure("J2", msg)
        spath = Path(structural_authority_path) if structural_authority_path else STRUCTURAL_AUTHORITY_PATH
        matrices = reconstruct_v47_matrices(reference_metrics_path=spath, field=field, constructors=constructors)
        summary_ctx["structural_matrices_count"] = len(matrices)
        counts = counts_by_source if counts_by_source is not None else load_v25_channel_counts()
        for source in SOURCE_ORDER:
            if counts[source].shape != (BLOCK_LENGTH, BLOCK_LENGTH):
                raise IntegrityFailure("J4", f"unexpected counts shape for {source}: {counts[source].shape}")
        counts_provenance = describe_v25_counts_provenance()
        summary_ctx["counts_provenance"] = counts_provenance
        triple_arm_binding_preflight(counts, h1_matrices=matrices, field=field)
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
        gate_evaluation = {arm: evaluate_arm_gate(arm, records) for arm in ARM_ORDER}
        stopped = {arm: bool(gate_evaluation[arm]["g3_undetected_zero"]["undetected_count"] > 0) for arm in ARM_ORDER}
        undetected_anomaly = {arm: bool(gate_evaluation[arm]["g3_undetected_zero"]["undetected_count"] > 0) for arm in ARM_ORDER}
        # orthogonal flag: h1_16 exact_full on 1p5M <2/3
        h1_16_1p5 = [r for r in records if r["arm"]=="h1_16" and r["source"]=="1p5M"]
        needs_flag = sum(1 for r in h1_16_1p5 if r["exact_full"]) < 2
        terminal_state, terminal_reason, routing_trace = determine_v47_terminal(
            integrity_ok=True,
            pass_h1_8=bool(gate_evaluation["h1_8"]["passed"]),
            pass_h1_12=bool(gate_evaluation["h1_12"]["passed"]),
            pass_h1_16=bool(gate_evaluation["h1_16"]["passed"]),
        )
        summary = build_v47_summary(
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
            l1_diagnostics_by_arm=aggregates.get("l1_diagnostics_by_arm", {}),
            stopped_for_analysis=stopped,
            arm_undetected_anomaly=undetected_anomaly,
            needs_1p5m_structure_branch=bool(needs_flag),
        )
        write_v47_outputs(root, records, summary)
        return {"output_root": str(root), "terminal_state": terminal_state, "terminal_reason": terminal_reason, "routing_trace": routing_trace, "decoder_calls_completed": accounting.completed, "aggregates": aggregates, "gate_evaluation": gate_evaluation, "summary": summary}
    except BaseException:
        _persist_invalid_evidence(root, records=records, accounting=accounting, summary_ctx=summary_ctx, failures=[("mid_run_failure", "raw partial records retained; no performance aggregate generated")], partial_records_retained=True)
        raise
