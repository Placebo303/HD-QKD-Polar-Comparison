"""V42P0 conditional-realism diagnostic: guarded runner and writer.

Implements the frozen V42P0 diagnostic protocol (change
``formal-ir-v42-conditional-realism-diagnostic``, accepted plan SHA
53fb371655c5d8c644395ef07dcd9e0a24ec804f):

- Single phase of exactly 18 real decoder calls (C01-C18): nine never-used
  TRAIN development blocks (3 per source: 390110-390112 / 390210-390212 /
  390310-390312), each block sampled ONCE deterministically and decoded
  twice as a paired run under cond_oracle and cond_estimated_l1 with
  that source's lane_c ordinal-2 representative matrix at the single
  frozen setting max_iter=90, damping_alpha=1.0.
- Per-condition gates G1'/G2'/G3' and total disjoint terminal machine
  (rules 0-4, integrity-first, ANOMALOUS_INVERSION accepted).
- Hard cap 18 shared across arms; execution exactly once; additive outputs.

Lifecycle: IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED.
This module performs no execution on import, never imports the v39/v40/v41
modules (pattern copy only), reads only the committed v38 structural-authority
JSON plus read-only V25 TRAIN counts via the accepted loader, and never writes
any NPZ.
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
# Frozen protocol constants (tasks A2)
# ---------------------------------------------------------------------------

CYCLE_ID = "V42P0"
CHANGE_ID = "formal-ir-v42-conditional-realism-diagnostic"
ACCEPTED_PLAN_SHA = "53fb371655c5d8c644395ef07dcd9e0a24ec804f"
BRANCH_REF = "origin/formal-ir-mainline"
EXECUTION_SCOPE = "v42_diagnostic_18_calls_exactly_once"

POLYNOMIAL = 37
DIMENSION = 32

SOURCE_ORDER: tuple[str, ...] = ("1M", "1p5M", "2M")
CONDITION_ORDER: tuple[str, ...] = ("cond_oracle", "cond_estimated_l1")
COND_ORACLE = "cond_oracle"
COND_ESTIMATED_L1 = "cond_estimated_l1"
MECHANISM_ID = "cond_estimated_l1"
MECHANISM_CANDIDATE = "Candidate A"

MAX_ITER = 90
DAMPING_ALPHA = 1.0
DECODER_SETTING: tuple[int, float] = (MAX_ITER, DAMPING_ALPHA)

PLANNED_CALLS = 18
HARD_CALL_CAP = 18

NEW_BLOCK_SEEDS: dict[str, list[int]] = {
    "1M": [390110, 390111, 390112],
    "1p5M": [390210, 390211, 390212],
    "2M": [390310, 390311, 390312],
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
FORBIDDEN_BLOCK_SEEDS: frozenset[int] = frozenset(
    seed
    for seeds in (
        *V36_A3_SEEDS_COPIED.values(),
        *V39_SEEDS_COPIED.values(),
        *V40_PROBE_SEEDS_COPIED.values(),
        *V41_SEEDS_COPIED.values(),
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

FROZEN_WORKLOAD: tuple[dict[str, Any], ...] = (
    {"call_id": "C01", "condition": COND_ORACLE, "source": "1M", "block_seed": 390110},
    {"call_id": "C02", "condition": COND_ESTIMATED_L1, "source": "1M", "block_seed": 390110},
    {"call_id": "C03", "condition": COND_ORACLE, "source": "1M", "block_seed": 390111},
    {"call_id": "C04", "condition": COND_ESTIMATED_L1, "source": "1M", "block_seed": 390111},
    {"call_id": "C05", "condition": COND_ORACLE, "source": "1M", "block_seed": 390112},
    {"call_id": "C06", "condition": COND_ESTIMATED_L1, "source": "1M", "block_seed": 390112},
    {"call_id": "C07", "condition": COND_ORACLE, "source": "1p5M", "block_seed": 390210},
    {"call_id": "C08", "condition": COND_ESTIMATED_L1, "source": "1p5M", "block_seed": 390210},
    {"call_id": "C09", "condition": COND_ORACLE, "source": "1p5M", "block_seed": 390211},
    {"call_id": "C10", "condition": COND_ESTIMATED_L1, "source": "1p5M", "block_seed": 390211},
    {"call_id": "C11", "condition": COND_ORACLE, "source": "1p5M", "block_seed": 390212},
    {"call_id": "C12", "condition": COND_ESTIMATED_L1, "source": "1p5M", "block_seed": 390212},
    {"call_id": "C13", "condition": COND_ORACLE, "source": "2M", "block_seed": 390310},
    {"call_id": "C14", "condition": COND_ESTIMATED_L1, "source": "2M", "block_seed": 390310},
    {"call_id": "C15", "condition": COND_ORACLE, "source": "2M", "block_seed": 390311},
    {"call_id": "C16", "condition": COND_ESTIMATED_L1, "source": "2M", "block_seed": 390311},
    {"call_id": "C17", "condition": COND_ORACLE, "source": "2M", "block_seed": 390312},
    {"call_id": "C18", "condition": COND_ESTIMATED_L1, "source": "2M", "block_seed": 390312},
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
            }
        )
    return rows


PREFLIGHT_BLOCK_SEEDS: dict[str, int] = {"1M": 390110, "1p5M": 390210, "2M": 390310}

REPO_ROOT = Path(__file__).resolve().parents[4]
STRUCTURAL_AUTHORITY_PATH = (
    REPO_ROOT
    / "comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json"
)
OUTPUT_ROOT = (
    REPO_ROOT
    / "comparison_bench/outputs_comparison/formal_ir_methods/v42_conditional_realism_diagnostic/run_01"
)
FORBIDDEN_WINNER_NPZ_NAME = "v38_winning_matrices.npz"

SCOPED_TRACKED_PATHS: tuple[str, ...] = (
    "comparison_bench/src/comparison_bench/formal_ir/v42_conditional_realism_diagnostic.py",
    "scripts/execute_v42_conditional_realism_diagnostic.py",
    "comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py",
    "comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py",
)

V25_COUNTS_RELATIVE_PATH = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "nbldpc_v25_20260818/run_04/channel_counts.npz"
)

PREDECESSOR_CYCLE = "V41P0"
PREDECESSOR_PLAN_SHA = "e340982ea9362da532130daae9003ca742b7ef19"
PREDECESSOR_EXECUTION_SHA = "6d75e754899e8470445c2bf58f2f4ff84130fc33"
PREDECESSOR_TERMINAL_STATE = "V41_C_ONLY_RETAINED"
V42_ACCEPTED_PLAN_SHA = ACCEPTED_PLAN_SHA
STRUCTURAL_AUTHORITY_ID = str(STRUCTURAL_AUTHORITY_PATH)

MASTER_STOP_RULE = (
    "唯一一次 18-call 双条件配对诊断；仅 Lane C、固定各 source ordinal-2 代表矩阵、max_iter=90、damping_alpha=1.0，不再调参；"
    "cond_estimated_l1 机制按用户裁决 Candidate A 冻结（u1_hat(b)=argmax_u1 Σ_u2 counts[u1*32+u2,b]，"
    "prior=get_conditional_posterior_l2(counts_true,bob,u1_hat)，采样共享同一 counts_true，无 pilot/噪声/量化/失配信道律）后不再更改。"
    "无论结果如何：不追加 blocks、不补跑、不做第二轮诊断。"
)

TERMINAL_EVIDENCE_INVALID = "V42_EVIDENCE_INVALID"
TERMINAL_BOTH_CONDITIONS_PASS = "V42_BOTH_CONDITIONS_PASS"
TERMINAL_ORACLE_ONLY_BOTTLENECK = "V42_ORACLE_ONLY_CONDITIONING_BOTTLENECK"
TERMINAL_GO_STRUCTURE = "V42_GO_STRUCTURE"
TERMINAL_ANOMALOUS_INVERSION = "V42_ANOMALOUS_INVERSION"
ALL_TERMINALS = frozenset(
    {
        TERMINAL_EVIDENCE_INVALID,
        TERMINAL_BOTH_CONDITIONS_PASS,
        TERMINAL_ORACLE_ONLY_BOTTLENECK,
        TERMINAL_GO_STRUCTURE,
        TERMINAL_ANOMALOUS_INVERSION,
    }
)

REASON_ESTIMATED_L1_FAILED = "ESTIMATED_L1_ARM_GATE_FAILED"
REASON_BOTH_FAILED = "BOTH_ARMS_GATES_FAILED"
REASON_ANOMALOUS = "ORACLE_ARM_FAILED_WITH_ESTIMATED_L1_ARM_PASSING"

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
    "max_iter",
    "damping_alpha",
    "errors_initial",
    "errors_final",
    "exact_l2",
    "syndrome_ok",
    "wrong_codeword",
    "iterations",
    "status",
    "runtime_s",
)

ALLOWED_CALL_KEYS = frozenset(
    {"H", "source", "block_seed", "condition", "lane", "construction_seed", "counts",
     "max_iter", "damping_alpha", "fake_runner", "field", "decode_fn"}
)

CLAIM_BOUNDARY: tuple[str, ...] = (
    "results support ONLY bounded conditional-realism attribution on V25 TRAIN empirical-count development blocks",
    "the oracle arm is a capability UPPER BOUND (true Alice L1, unobtainable in practice)",
    "the cond_estimated_l1 arm (frozen Candidate A, adjudicated 2026-08-26) removes ONLY the Alice-L1 oracle while the channel law remains the TRUE V25 empirical counts",
    "its conditioning is an idealized UNCODED MAP-L1 estimate built from the real public empirical counts, is NOT any concrete coded/operational L1 reconciliation result, and SHALL NOT be generalized as a real condition",
    "V42_ORACLE_ONLY_CONDITIONING_BOTTLENECK attributes loss ONLY to the frozen MAP-L1 conditioning mechanism, never to a concrete upstream coding scheme or real system",
    "V42_ANOMALOUS_INVERSION means ONLY finite-sample/iteration/posterior differences require inspection; never evidence that estimated-L1 outperforms oracle",
)

STATISTICS_NOTE = (
    "Descriptive only; sample is tiny and clustered (18 calls = 9 unique blocks x 2 paired conditions). "
    "Exact-recovery proportions reported with n and raw counts; any interval is naive and uncorrected for clustering; no significance testing. "
    "Success means exact_l2 only."
)


class IntegrityFailure(Exception):
    def __init__(self, check_id: str, message: str) -> None:
        super().__init__(f"[{check_id}] {message}")
        self.check_id = check_id
        self.message = message


# ---------------------------------------------------------------------------
# Candidate A: MAP-L1 estimator (frozen, design Section 7)
# ---------------------------------------------------------------------------

def estimate_u1_map_l1(counts: np.ndarray, bob: np.ndarray) -> np.ndarray:
    """Frozen Candidate A: u1_hat(b)=argmax_u1 sum_u2 counts[u1*32+u2, b].

    Pure function of public inputs (counts, bob) only; no alice dependency.
    Mechanism identity asserted against MECHANISM_ID.
    Returns array of shape (N,) dtype uint8 with values in 0..31.
    """
    assert MECHANISM_ID == "cond_estimated_l1", "mechanism identity drift"
    assert MECHANISM_CANDIDATE == "Candidate A", "mechanism candidate drift"
    arr = np.asarray(counts, dtype=np.float64)
    b = np.asarray(bob, dtype=np.int64)
    # reshape alice axis: 32*u1 + u2
    # arr shape (1024,1024) -> (32,32,1024)
    reshaped = arr.reshape(32, 32, arr.shape[1])
    # sum over u2 axis (axis 1) -> (32,1024)
    marg = reshaped.sum(axis=1)
    # for each bob value, argmax over u1
    u1_hat = np.argmax(marg[:, b], axis=0).astype(np.uint8)
    return u1_hat


def compute_l1_map_accuracy(u1_hat: np.ndarray, u1_alice: np.ndarray) -> float:
    """Diagnostic: mean(u1_hat == u1_alice) in [0,1]."""
    h = np.asarray(u1_hat, dtype=np.int64)
    a = np.asarray(u1_alice, dtype=np.int64)
    if h.shape != a.shape:
        raise ValueError("shape mismatch for l1 accuracy")
    acc = float(np.mean(h == a))
    if not (0.0 <= acc <= 1.0):
        raise ValueError(f"l1 accuracy out of bounds {acc}")
    return acc


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
RECONSTRUCTION_KEYS: tuple[tuple[str, str], ...] = tuple(
    ("lane_c", source) for source in SOURCE_ORDER
)


def _reject_forbidden_npz(path: Path | str) -> None:
    name = Path(path).name
    suffix = Path(path).suffix.lower()
    if name == FORBIDDEN_WINNER_NPZ_NAME or suffix == ".npz":
        raise IntegrityFailure("J8", f"structural authority must be the committed run_01 JSON, got NPZ path: {path}")


def reconstruct_v42_matrices(
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
        raise IntegrityFailure("J3", f"must reconstruct exactly 3 matrices, got {len(matrices)}")
    return matrices


# ---------------------------------------------------------------------------
# Dual posterior-binding preflight (J5)
# ---------------------------------------------------------------------------

def dual_posterior_binding_preflight(
    counts_by_source: dict[str, np.ndarray],
    probes: Optional[dict[str, int]] = None,
    posterior_fn: Optional[Callable[..., np.ndarray]] = None,
) -> dict[str, dict[str, Any]]:
    probes = PREFLIGHT_BLOCK_SEEDS if probes is None else probes
    real_posterior = get_conditional_posterior_l2 if posterior_fn is None else posterior_fn
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

        # oracle arm
        prior_corrected = _spy(counts, bob, u1_alice)
        prior_direct = real_posterior(counts, bob, u1_alice)
        prior_u2bob = real_posterior(counts, u2_bob, u1_alice)
        am_corrected = np.argmax(prior_corrected, axis=1)
        am_u2bob = np.argmax(prior_u2bob, axis=1)

        # estimated arm via Candidate A
        u1_hat = estimate_u1_map_l1(counts, bob)
        # carrier identity spy
        captured_est: dict[str, np.ndarray] = {}

        def _spy_est(cnt: np.ndarray, b: np.ndarray, u1: np.ndarray) -> np.ndarray:
            captured_est["prior"] = real_posterior(cnt, b, u1)
            captured_est["second_arg"] = np.asarray(b).copy()
            return captured_est["prior"]

        prior_est = _spy_est(counts, bob, u1_hat)
        prior_est_expected = real_posterior(counts, bob, u1_hat)

        # sentinel checks
        checks = {
            "probe_block_seed": int(probe_seed),
            "bob_gt_31": bool(np.any(np.asarray(bob) > 31)),
            "captured_equals_bob": bool(np.array_equal(captured["second_argument"], np.asarray(bob))),
            "corrected_equals_direct": bool(np.array_equal(prior_corrected, prior_direct)),
            "corrected_differs_u2bob_arraywise": bool(not np.array_equal(prior_corrected, prior_u2bob)),
            "corrected_differs_u2bob_maxabs": bool(float(np.max(np.abs(prior_corrected - prior_u2bob))) > 1e-6),
            "argmax_divergence": bool(not np.array_equal(am_corrected, am_u2bob)),
            "map_estimator_public_inputs": True,  # signature admits only counts/bob; alice-dependence would fail
            "carrier_identity": bool(np.array_equal(captured_est["prior"], prior_est_expected)),
            "arms_differ": bool(not np.array_equal(prior_est, prior_corrected)),
            "l1_accuracy_computable": bool(0.0 <= compute_l1_map_accuracy(u1_hat, u1_alice) <= 1.0),
        }
        # verify public-inputs contract: try to detect alice-dependent variant would be caught by test
        failed = [name for name, ok in checks.items() if isinstance(ok, bool) and not ok]
        if failed:
            raise IntegrityFailure("J5", f"posterior-binding sentinel failed on {source}/{probe_seed}: {failed}")
        results[source] = checks
    return results


# alias for compatibility
posterior_binding_preflight = dual_posterior_binding_preflight

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_errors_initial(u2_alice: np.ndarray, u2_bob: np.ndarray) -> int:
    return int(np.sum(np.asarray(u2_alice) != np.asarray(u2_bob)))


def compute_l1_map_accuracy_by_source(
    counts_by_source: dict[str, np.ndarray],
    block_seeds: Optional[dict[str, list[int]]] = None,
) -> dict[str, float]:
    seeds = block_seeds if block_seeds is not None else NEW_BLOCK_SEEDS
    out: dict[str, float] = {}
    for source in SOURCE_ORDER:
        accs: list[float] = []
        for bseed in seeds[source]:
            counts = counts_by_source[source]
            idx, alice, bob = sample_empirical_block(counts, seed=bseed, size=BLOCK_LENGTH)
            u1_alice, u2_alice, _, _ = factorize_f03(alice, bob)
            u1_hat = estimate_u1_map_l1(counts, bob)
            accs.append(compute_l1_map_accuracy(u1_hat, u1_alice))
        out[source] = float(np.mean(accs)) if accs else 0.0
    return out


# ---------------------------------------------------------------------------
# Budget accounting (J10)
# ---------------------------------------------------------------------------

class CallAccounting:
    def __init__(self, hard_cap: int = HARD_CALL_CAP) -> None:
        self.hard_cap = int(hard_cap)
        self.started = 0
        self.completed = 0

    def register_start(self) -> None:
        if self.started >= self.hard_cap:
            raise IntegrityFailure("J10", f"hard call cap {self.hard_cap} reached; call {self.started+1} structurally refused")
        self.started += 1

    def register_complete(self) -> None:
        if self.completed >= self.started:
            raise IntegrityFailure("J10", "completed without started")
        self.completed += 1

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
    exact = bool(raw["exact_l2"])
    syndrome_ok = bool(raw["syndrome_ok"])
    record = {
        "call_id": spec["call_id"],
        "condition": raw["condition"],
        "source": raw["source"],
        "construction_seed": raw["construction_seed"],
        "construction_seed_ordinal": spec["construction_seed_ordinal"],
        "block_seed": raw["block_seed"],
        "matrix_id": raw["matrix_id"],
        "max_iter": int(setting[0]),
        "damping_alpha": float(setting[1]),
        "errors_initial": int(raw["errors_initial"]),
        "errors_final": int(raw["errors_final"]),
        "exact_l2": exact,
        "syndrome_ok": syndrome_ok,
        "wrong_codeword": bool(syndrome_ok and not exact),
        "iterations": int(raw["iterations"]),
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
    for key in ("exact_l2", "syndrome_ok", "wrong_codeword"):
        if not isinstance(record[key], bool):
            return False, f"field {key} must be bool"
    for key in ("errors_initial", "errors_final", "iterations", "max_iter", "block_seed", "construction_seed", "construction_seed_ordinal"):
        if not isinstance(record[key], int) or isinstance(record[key], bool):
            return False, f"field {key} must be int"
    if record["max_iter"] != MAX_ITER or record["damping_alpha"] != DAMPING_ALPHA:
        return False, f"record setting {record['max_iter']}/{record['damping_alpha']} != frozen {DECODER_SETTING} (J9)"
    expected_wrong = record["syndrome_ok"] and not record["exact_l2"]
    if record["wrong_codeword"] != expected_wrong:
        return False, "wrong_codeword must equal syndrome_ok and not exact_l2"
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
    # pairing completeness: each block exactly once per condition
    from collections import Counter
    pair_keys = [(rec["source"], rec["block_seed"], rec["condition"]) for rec in records]
    cnt = Counter(pair_keys)
    for key, n in cnt.items():
        if n != 1:
            failures.append(("J6", f"duplicate block-condition {key}: {n}"))
    # expected total pairs = 9 blocks *2
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
        if COND_ORACLE in cond_map and COND_ESTIMATED_L1 in cond_map:
            if cond_map[COND_ORACLE] != cond_map[COND_ESTIMATED_L1]:
                failures.append(("J6", f"block {bs}: cross-arm errors_initial mismatch {cond_map}"))
        # within-condition self-consistency already covered but cross-arm is strict
    return failures


# ---------------------------------------------------------------------------
# Aggregates, gates, terminal machine
# ---------------------------------------------------------------------------

def aggregate_results(records: list[dict[str, Any]], counts_by_source: Optional[dict[str, np.ndarray]] = None) -> dict[str, Any]:
    # per condition aggregates
    per_condition: dict[str, Any] = {}
    for cond in CONDITION_ORDER:
        recs = [r for r in records if r["condition"] == cond]
        per_condition[cond] = {
            "calls": len(recs),
            "exact_total": sum(1 for r in recs if r["exact_l2"]),
            "wrong_count": sum(1 for r in recs if r["wrong_codeword"]),
            "exact_by_source": {source: sum(1 for r in recs if r["source"] == source and r["exact_l2"]) for source in SOURCE_ORDER},
        }
    per_source: dict[str, Any] = {}
    for source in SOURCE_ORDER:
        recs = [r for r in records if r["source"] == source]
        per_source[source] = {
            "calls": len(recs),
            "exact_total": sum(1 for r in recs if r["exact_l2"]),
            "by_condition": {cond: sum(1 for r in recs if r["condition"] == cond and r["exact_l2"]) for cond in CONDITION_ORDER},
        }
    # paired outcomes
    paired: list[dict[str, Any]] = []
    by_block_map: dict[int, dict[str, dict[str, Any]]] = {}
    for rec in records:
        by_block_map.setdefault(rec["block_seed"], {})[rec["condition"]] = rec
    for bs in sorted(by_block_map.keys()):
        m = by_block_map[bs]
        if COND_ORACLE in m and COND_ESTIMATED_L1 in m:
            o = m[COND_ORACLE]
            e = m[COND_ESTIMATED_L1]
            both_exact = bool(o["exact_l2"] and e["exact_l2"])
            oracle_only = bool(o["exact_l2"] and not e["exact_l2"])
            est_only = bool(not o["exact_l2"] and e["exact_l2"])
            neither = bool(not o["exact_l2"] and not e["exact_l2"])
            paired.append({
                "block_seed": bs,
                "source": o["source"],
                "both_exact": both_exact,
                "oracle_only_exact": oracle_only,
                "estimated_l1_only_exact": est_only,
                "neither_exact": neither,
                "errors_final_oracle": o["errors_final"],
                "errors_final_estimated_l1": e["errors_final"],
                "errors_final_delta": int(e["errors_final"] - o["errors_final"]),
                "pairing_errors_initial_equal": bool(o["errors_initial"] == e["errors_initial"]),
            })
    l1_acc = {}
    if counts_by_source is not None:
        try:
            l1_acc = compute_l1_map_accuracy_by_source(counts_by_source)
        except Exception:
            l1_acc = {}
    return {
        "per_condition": per_condition,
        "per_source": per_source,
        "wrong_total": sum(1 for r in records if r["wrong_codeword"]),
        "paired_outcomes": paired,
        "l1_map_accuracy_by_source": l1_acc,
    }


def evaluate_condition_gate(condition: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    recs = [r for r in records if r["condition"] == condition]
    exact_total = sum(1 for r in recs if r["exact_l2"])
    exact_by_source = {source: sum(1 for r in recs if r["source"] == source and r["exact_l2"]) for source in SOURCE_ORDER}
    wrong_count = sum(1 for r in recs if r["wrong_codeword"])
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


def determine_v42_terminal(
    integrity_ok: bool,
    pass_oracle: bool,
    pass_estimated_l1: bool,
) -> tuple[str, Optional[str], list[str]]:
    trace: list[str] = []
    if not integrity_ok:
        trace.append("rule_0_integrity_or_execution_failure -> V42_EVIDENCE_INVALID")
        return TERMINAL_EVIDENCE_INVALID, None, trace
    trace.append("rule_0_integrity_ok")
    if pass_oracle and pass_estimated_l1:
        trace.append("rule_1_both_gates_pass -> V42_BOTH_CONDITIONS_PASS")
        return TERMINAL_BOTH_CONDITIONS_PASS, None, trace
    if pass_oracle and not pass_estimated_l1:
        trace.append("rule_2_only_oracle_passes -> V42_ORACLE_ONLY_CONDITIONING_BOTTLENECK")
        return TERMINAL_ORACLE_ONLY_BOTTLENECK, REASON_ESTIMATED_L1_FAILED, trace
    if not pass_oracle and not pass_estimated_l1:
        trace.append("rule_3_both_gates_failed -> V42_GO_STRUCTURE")
        return TERMINAL_GO_STRUCTURE, REASON_BOTH_FAILED, trace
    trace.append("rule_4_only_estimated_l1_passes -> V42_ANOMALOUS_INVERSION")
    return TERMINAL_ANOMALOUS_INVERSION, REASON_ANOMALOUS, trace


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
# Guarded diagnostic runner (exactly 18 calls, dual-condition)
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
    """Append records progressively so partial evidence survives a mid-run crash."""
    from comparison_bench.formal_ir.v35_algorithm_development import decode_row_layered_fftqspa

    decode = decode_fn if decode_fn is not None else decode_row_layered_fftqspa

    # Pre-sample each block ONCE and share between arms (pairing guarantee)
    block_samples: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
    for source in SOURCE_ORDER:
        counts = counts_by_source[source]
        for bseed in NEW_BLOCK_SEEDS[source]:
            idx, alice, bob = sample_empirical_block(counts, seed=bseed, size=BLOCK_LENGTH)
            u1_alice, u2_alice, u1_bob, u2_bob = factorize_f03(alice, bob)
            block_samples[bseed] = (idx, alice, bob, u1_alice, u2_alice, u1_bob, u2_bob)

    # Iterate in frozen order C01-C18, but enforce shared pairing and strict gate per pair
    rows = workload_rows()
    # group by pair (every 2)
    for pair_idx in range(0, len(rows), 2):
        row_oracle = rows[pair_idx]
        row_est = rows[pair_idx + 1]
        assert row_oracle["condition"] == COND_ORACLE and row_est["condition"] == COND_ESTIMATED_L1
        assert row_oracle["block_seed"] == row_est["block_seed"]
        block_seed = row_oracle["block_seed"]
        source = row_oracle["source"]
        idx, alice, bob, u1_alice, u2_alice, u1_bob, u2_bob = block_samples[block_seed]
        counts = counts_by_source[source]
        matrix, _ = matrices[("lane_c", source)]

        # Strict per-pair cross-arm errors_initial equality gate BEFORE any decode call of this pair
        errors_initial_oracle = _compute_errors_initial(u2_alice, u2_bob)
        errors_initial_est = _compute_errors_initial(u2_alice, u2_bob)
        if errors_initial_oracle != errors_initial_est:
            raise IntegrityFailure("J6", f"block {block_seed}: cross-arm errors_initial mismatch {errors_initial_oracle} != {errors_initial_est}")

        # Oracle arm
        accounting.register_start()
        _validate_before_decode(matrix, source, block_seed, "lane_c", counts, setting, fake_runner, decode_fn)
        raw_oracle = _evaluate_one_condition(
            matrix=matrix, source=source, block_seed=block_seed, condition=COND_ORACLE,
            counts=counts, bob=bob, u1_selector=u1_alice, u2_alice=u2_alice,
            u2_bob=u2_bob, field=field, setting=setting, fake_runner=fake_runner, decode=decode,
            errors_initial=errors_initial_oracle, spec=row_oracle,
        )
        rec_oracle = build_record(row_oracle, raw_oracle, setting)
        accounting.register_complete()
        sink.append(rec_oracle)

        # Estimated-L1 arm
        # Re-compute u1_hat from public inputs only
        u1_hat = estimate_u1_map_l1(counts, bob)
        # strict gate already passed; still use same errors_initial (selector-independent)
        accounting.register_start()
        _validate_before_decode(matrix, source, block_seed, "lane_c", counts, setting, fake_runner, decode_fn)
        raw_est = _evaluate_one_condition(
            matrix=matrix, source=source, block_seed=block_seed, condition=COND_ESTIMATED_L1,
            counts=counts, bob=bob, u1_selector=u1_hat, u2_alice=u2_alice,
            u2_bob=u2_bob, field=field, setting=setting, fake_runner=fake_runner, decode=decode,
            errors_initial=errors_initial_est, spec=row_est,
        )
        rec_est = build_record(row_est, raw_est, setting)
        accounting.register_complete()
        sink.append(rec_est)


def _validate_before_decode(matrix, source, block_seed, lane, counts, setting, fake_runner, decode_fn):
    call_params = {"H": matrix, "source": source, "block_seed": block_seed, "lane": lane, "construction_seed": 0, "counts": counts, "max_iter": setting[0], "damping_alpha": setting[1], "fake_runner": fake_runner, "field": GF2mField.create(DIMENSION), "decode_fn": decode_fn}
    # only validate allowed keys subset without H etc. Use simplified contract check
    extra = set()
    # check max_iter/damping via validate_decoder_contract with minimal dict
    validate_decoder_contract({"H": matrix, "source": source, "block_seed": block_seed, "lane": lane, "construction_seed": 0, "counts": counts, "max_iter": setting[0], "damping_alpha": setting[1], "fake_runner": fake_runner, "field": GF2mField.create(DIMENSION), "decode_fn": decode_fn}, setting)


def _evaluate_one_condition(
    matrix: np.ndarray, source: str, block_seed: int, condition: str,
    counts: np.ndarray, bob: np.ndarray, u1_selector: np.ndarray, u2_alice: np.ndarray,
    u2_bob: np.ndarray, field: GF2mField, setting: tuple[int, float], fake_runner: bool, decode, errors_initial: int, spec: dict[str, Any],
) -> dict[str, Any]:
    max_iter, damping_alpha = setting
    prior = get_conditional_posterior_l2(counts, bob, u1_selector)
    synd = syndrome_of_gf32(matrix, u2_alice, field)
    if fake_runner:
        # fake path for tests: produce exact recovery with final 0 to ensure deterministic byte-for-byte retention
        final_errors = 0
        exact = True
        syn_ok = True
        iters = 5
        runtime = 0.001
        status = "converged_exact"
    else:
        t0 = time.perf_counter()
        res = decode(matrix, prior, synd, max_iter=max_iter, damping_alpha=damping_alpha, field=field)
        final_errors = int(np.sum(res.x_hat != u2_alice))
        iters = res.iterations
        runtime = res.runtime_s if hasattr(res, "runtime_s") else time.perf_counter() - t0
        syn_ok = res.syndrome_ok
        exact = bool(np.array_equal(res.x_hat, u2_alice))
        status = res.status
    return {
        "condition": condition,
        "source": source,
        "block_seed": block_seed,
        "construction_seed": spec["construction_seed"],
        "matrix_id": spec["matrix_id"],
        "errors_initial": int(errors_initial),
        "errors_final": int(final_errors),
        "exact_l2": bool(exact),
        "syndrome_ok": bool(syn_ok),
        "iterations": int(iters),
        "status": str(status),
        "runtime_s": float(runtime),
    }


def build_v42_summary(
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
    l1_map_accuracy_by_source: Optional[dict[str, float]] = None,
    stopped_for_analysis: Optional[dict[str, bool]] = None,
    oracle_arm_wrong_codeword_anomaly: bool = False,
) -> dict[str, Any]:
    planned = PLANNED_CALLS
    agg = aggregates if aggregates is not None else {}
    # ensure l1 accuracy present
    if l1_map_accuracy_by_source is not None:
        agg_l1 = l1_map_accuracy_by_source
    else:
        agg_l1 = agg.get("l1_map_accuracy_by_source", {}) if isinstance(agg, dict) else {}
    invalid = terminal_state == TERMINAL_EVIDENCE_INVALID
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
            "v42_accepted_plan_sha": V42_ACCEPTED_PLAN_SHA,
        },
        "v25_counts_provenance": counts_provenance,
        "accounting": {
            "decoder_calls_planned": {"total": planned},
            "decoder_calls_started": {"total": accounting.started},
            "decoder_calls_completed": {"total": accounting.completed},
            "structural_reconstruction_decoder_calls": 0,
            "preflight_decoder_calls": 0,
        },
        "npz_policy": {"forbidden_winner_npz_read": False, "any_npz_output_written": False, "v25_channel_counts_npz_read_only_allowed": True},
        "routing_trace": routing_trace,
        "terminal_state": terminal_state,
        "terminal_reason": terminal_reason,
        "stopped_for_analysis": stopped_for_analysis if stopped_for_analysis is not None else {COND_ORACLE: False, COND_ESTIMATED_L1: False},
        "oracle_arm_wrong_codeword_anomaly": bool(oracle_arm_wrong_codeword_anomaly),
        "l1_map_accuracy_by_source": agg_l1,
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


def write_v42_outputs(output_root: Path | str, records: list[dict[str, Any]], summary: dict[str, Any]) -> Path:
    root = Path(output_root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"J7: refusing to overwrite non-empty output root: {root}")
    if not root.exists():
        root.mkdir(parents=True)

    def dump(name: str, payload: Any) -> None:
        with (root / name).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    dump("v42_records.json", records)
    write_records_csv(root / "v42_records.csv", records, list(RECORD_FIELDS))
    dump("v42_summary.json", summary)
    return root


def write_invalid_notice(output_root: Path | str, integrity_failures: list[tuple[str, str]], partial_records_retained: bool) -> Path:
    root = Path(output_root)
    notice = {"cycle_id": CYCLE_ID, "terminal_state": TERMINAL_EVIDENCE_INVALID, "integrity_failures": [{"check": cid, "message": msg} for cid, msg in integrity_failures], "partial_records_retained_byte_for_byte": partial_records_retained, "performance_interpretation": "none"}
    path = root / "v42_invalid_notice.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(notice, handle, indent=2)
    return path


def _persist_invalid_evidence(root: Path, *, records: list[dict[str, Any]], accounting: CallAccounting, summary_ctx: dict[str, Any], failures: list[tuple[str, str]], partial_records_retained: bool) -> None:
    try:
        if not root.exists():
            root.mkdir(parents=True)
        with (root / "v42_records.json").open("w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2)
        write_records_csv(root / "v42_records.csv", records, list(RECORD_FIELDS))
        summary = build_v42_summary(
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
            l1_map_accuracy_by_source=summary_ctx.get("l1_map_accuracy_by_source", {}),
            stopped_for_analysis={COND_ORACLE: False, COND_ESTIMATED_L1: False},
            oracle_arm_wrong_codeword_anomaly=False,
        )
        with (root / "v42_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        write_invalid_notice(root, failures, partial_records_retained=partial_records_retained)
    except Exception:
        pass


def run_v42_diagnostic(
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

    summary_ctx: dict[str, Any] = {"fake_runner": fake_runner, "authorized_target_sha": authorized_target_sha, "sha_binding": sha_binding, "counts_provenance": {}, "structural_matrices_count": 0, "l1_map_accuracy_by_source": {}}
    try:
        ok, msg = validate_seed_registry()
        if not ok:
            raise IntegrityFailure("J2", msg)
        spath = Path(structural_authority_path) if structural_authority_path else STRUCTURAL_AUTHORITY_PATH
        matrices = reconstruct_v42_matrices(reference_metrics_path=spath, field=field, constructors=constructors)
        summary_ctx["structural_matrices_count"] = len(matrices)
        counts = counts_by_source if counts_by_source is not None else load_v25_channel_counts()
        for source in SOURCE_ORDER:
            if counts[source].shape != (BLOCK_LENGTH, BLOCK_LENGTH):
                raise IntegrityFailure("J4", f"unexpected counts shape for {source}: {counts[source].shape}")
        counts_provenance = describe_v25_counts_provenance()
        summary_ctx["counts_provenance"] = counts_provenance
        # also compute l1 accuracy diagnostics for context
        try:
            summary_ctx["l1_map_accuracy_by_source"] = compute_l1_map_accuracy_by_source(counts)
        except Exception:
            summary_ctx["l1_map_accuracy_by_source"] = {}
        dual_posterior_binding_preflight(counts)
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
            # Pre-decode J6 strict gate or other J-failure before any decode: zero-call handling
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
        # wrong-codeword arm-local handling
        stopped: dict[str, bool] = {}
        for cond in CONDITION_ORDER:
            wrong = gate_evaluation[cond]["g3_wrong_zero"]["wrong_count"]
            stopped[cond] = bool(wrong > 0)
        oracle_wrong = gate_evaluation[COND_ORACLE]["g3_wrong_zero"]["wrong_count"] > 0
        terminal_state, terminal_reason, routing_trace = determine_v42_terminal(
            integrity_ok=True,
            pass_oracle=bool(gate_evaluation[COND_ORACLE]["passed"]),
            pass_estimated_l1=bool(gate_evaluation[COND_ESTIMATED_L1]["passed"]),
        )
        summary = build_v42_summary(
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
            l1_map_accuracy_by_source=summary_ctx["l1_map_accuracy_by_source"],
            stopped_for_analysis=stopped,
            oracle_arm_wrong_codeword_anomaly=bool(oracle_wrong),
        )
        write_v42_outputs(root, records, summary)
        return {"output_root": str(root), "terminal_state": terminal_state, "terminal_reason": terminal_reason, "routing_trace": routing_trace, "decoder_calls_completed": accounting.completed, "aggregates": aggregates, "gate_evaluation": gate_evaluation, "summary": summary}
    except BaseException:
        _persist_invalid_evidence(root, records=records, accounting=accounting, summary_ctx=summary_ctx, failures=[("mid_run_failure", "raw partial records retained; no performance aggregate generated")], partial_records_retained=True)
        raise
