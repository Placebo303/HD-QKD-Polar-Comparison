"""V41P0 fresh-block confirmation: guarded runner and writer.

Implements the frozen V41P0 confirmation protocol (change
``formal-ir-v41-fresh-block-confirm``):

- Single phase of exactly 18 real decoder calls (C01-C18): nine never-used
  TRAIN development blocks (3 per source: 390107-390109 / 390207-390209 /
  390307-390309), each decoded once per lane with that source's representative
  ordinal-2 matrix, at the single fixed setting max_iter=90, damping_alpha=1.0.
- Per-lane independent retention gates G1/G2/G3 (route retention only, not a
  B/C superiority test) and a total, disjoint terminal machine
  (design Section 8 rules 0-5; integrity-first; global wrong-codeword scope).
- Hard cap 18 with structural refusal of call 19; execution exactly once;
  additive evidence outputs; no NPZ ever written.

Lifecycle: IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED.
This module performs no execution on import, never imports the v39 or v40
modules (design D6/D8: pattern copy only), reads only the committed v38
structural-authority JSON plus read-only V25 TRAIN counts via the accepted
loader, and never writes any NPZ.
"""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np

from comparison_bench.formal_ir.v35_algorithm_development import (
    GF2mField,
    factorize_f03,
    get_conditional_posterior_l2,
    load_v25_channel_counts,
    sample_empirical_block,
)
from comparison_bench.formal_ir.v38_architecture_triage import (
    BLOCK_LENGTH,
    _check_v38r1_metric_match,
    _load_v38r1_reference_metrics,
    construct_lane_b_prototype,
    construct_lane_c_prototype,
    evaluate_single_block,
)

# ---------------------------------------------------------------------------
# Frozen protocol constants (tasks A2)
# ---------------------------------------------------------------------------

CYCLE_ID = "V41P0"
CHANGE_ID = "formal-ir-v41-fresh-block-confirm"
BRANCH_REF = "origin/formal-ir-mainline"
EXECUTION_SCOPE = "v41_confirmation_18_calls_exactly_once"

POLYNOMIAL = 37
DIMENSION = 32

SOURCE_ORDER: tuple[str, ...] = ("1M", "1p5M", "2M")
LANE_ORDER: tuple[str, ...] = ("lane_c", "lane_b")

# Decoder contract (design Section 6): single fixed setting for all 18 calls.
MAX_ITER = 90
DAMPING_ALPHA = 1.0
DECODER_SETTING: tuple[int, float] = (MAX_ITER, DAMPING_ALPHA)

# Budget: exactly 18 confirmation calls; call 19 structurally refused (J10).
PLANNED_CALLS = 18
HARD_CALL_CAP = 18

# Nine new block seeds, three per source (frozen; design Section 3).
NEW_BLOCK_SEEDS: dict[str, list[int]] = {
    "1M": [390107, 390108, 390109],
    "1p5M": [390207, 390208, 390209],
    "2M": [390307, 390308, 390309],
}

# Forbidden seed registries copied as data (R4; v39/v40 modules NOT imported):
# V36_A3 seeds reused by V38/V38R1, the V39 registry, and the V40 probe seeds.
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
FORBIDDEN_BLOCK_SEEDS: frozenset[int] = frozenset(
    seed
    for seeds in (
        *V36_A3_SEEDS_COPIED.values(),
        *V39_SEEDS_COPIED.values(),
        *V40_PROBE_SEEDS_COPIED.values(),
    )
    for seed in (seeds if isinstance(seeds, list) else [seeds])
)

# Representative ordinal-2 construction seeds per lane/source (design Section 5;
# verified against the committed V40 module constant facts without importing it).
REPRESENTATIVE_ORDINALS: dict[str, int] = {"lane_c": 2, "lane_b": 2}
CONSTRUCTION_SEEDS: dict[str, dict[str, list[int]]] = {
    "lane_c": {
        "1M": [383101, 383102, 383103],
        "1p5M": [383201, 383202, 383203],
        "2M": [383301, 383302, 383303],
    },
    "lane_b": {
        "1M": [382101, 382102, 382103],
        "1p5M": [382201, 382202, 382203],
        "2M": [382301, 382302, 382303],
    },
}


def _rep_seed(lane: str, source: str) -> int:
    """Construction seed of the lane's representative ordinal for a source."""
    return CONSTRUCTION_SEEDS[lane][source][REPRESENTATIVE_ORDINALS[lane] - 1]


# Six unique ordinal-2 representative matrix ids (frozen identities).
FROZEN_REPRESENTATIVE_MATRIX_IDS: tuple[str, ...] = (
    "lane_c_1M_s383102",
    "lane_b_1M_s382102",
    "lane_c_1p5M_s383202",
    "lane_b_1p5M_s382202",
    "lane_c_2M_s383302",
    "lane_b_2M_s382302",
)

# Frozen workload C01-C18 (design Section 4; sources 1M/1p5M/2M, blocks
# ascending by seed within a source, lane_c before lane_b within a block).
FROZEN_WORKLOAD: tuple[dict[str, Any], ...] = (
    {"call_id": "C01", "lane": "lane_c", "source": "1M", "block_seed": 390107},
    {"call_id": "C02", "lane": "lane_b", "source": "1M", "block_seed": 390107},
    {"call_id": "C03", "lane": "lane_c", "source": "1M", "block_seed": 390108},
    {"call_id": "C04", "lane": "lane_b", "source": "1M", "block_seed": 390108},
    {"call_id": "C05", "lane": "lane_c", "source": "1M", "block_seed": 390109},
    {"call_id": "C06", "lane": "lane_b", "source": "1M", "block_seed": 390109},
    {"call_id": "C07", "lane": "lane_c", "source": "1p5M", "block_seed": 390207},
    {"call_id": "C08", "lane": "lane_b", "source": "1p5M", "block_seed": 390207},
    {"call_id": "C09", "lane": "lane_c", "source": "1p5M", "block_seed": 390208},
    {"call_id": "C10", "lane": "lane_b", "source": "1p5M", "block_seed": 390208},
    {"call_id": "C11", "lane": "lane_c", "source": "1p5M", "block_seed": 390209},
    {"call_id": "C12", "lane": "lane_b", "source": "1p5M", "block_seed": 390209},
    {"call_id": "C13", "lane": "lane_c", "source": "2M", "block_seed": 390307},
    {"call_id": "C14", "lane": "lane_b", "source": "2M", "block_seed": 390307},
    {"call_id": "C15", "lane": "lane_c", "source": "2M", "block_seed": 390308},
    {"call_id": "C16", "lane": "lane_b", "source": "2M", "block_seed": 390308},
    {"call_id": "C17", "lane": "lane_c", "source": "2M", "block_seed": 390309},
    {"call_id": "C18", "lane": "lane_b", "source": "2M", "block_seed": 390309},
)


def workload_rows() -> list[dict[str, Any]]:
    """The frozen 18-call workload with representative matrix identity per call."""
    rows: list[dict[str, Any]] = []
    for spec in FROZEN_WORKLOAD:
        seed = _rep_seed(spec["lane"], spec["source"])
        rows.append(
            {
                **spec,
                "construction_seed_ordinal": REPRESENTATIVE_ORDINALS[spec["lane"]],
                "construction_seed": seed,
                "matrix_id": f"{spec['lane']}_{spec['source']}_s{seed}",
            }
        )
    return rows


# Posterior-binding sentinels run on the FIRST new block of each source (D6).
PREFLIGHT_BLOCK_SEEDS: dict[str, int] = {"1M": 390107, "1p5M": 390207, "2M": 390307}

REPO_ROOT = Path(__file__).resolve().parents[4]
STRUCTURAL_AUTHORITY_PATH = (
    REPO_ROOT
    / "comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json"
)
OUTPUT_ROOT = (
    REPO_ROOT
    / "comparison_bench/outputs_comparison/formal_ir_methods/v41_fresh_block_confirm/run_01"
)
FORBIDDEN_WINNER_NPZ_NAME = "v38_winning_matrices.npz"

# Scoped tracked-dirty check: four-file scope (design D8), checked before any
# root creation (J1 refusal class). v39/v40 modules are deliberately absent.
SCOPED_TRACKED_PATHS: tuple[str, ...] = (
    "comparison_bench/src/comparison_bench/formal_ir/v41_fresh_block_confirm.py",
    "scripts/execute_v41_fresh_block_confirm.py",
    "comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py",
    "comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py",
)

V25_COUNTS_RELATIVE_PATH = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "nbldpc_v25_20260818/run_04/channel_counts.npz"
)

# Predecessor bindings (R1); recorded in the summary provenance only.
PREDECESSOR_CYCLE = "V40P0"
PREDECESSOR_PLAN_SHA = "36a3751e190ff06e0e88024b51b6f8713c13a4dc"
PREDECESSOR_EXECUTION_SHA = "80d605489f1f65eefd091625134514e8a09902de"
PREDECESSOR_TERMINAL_STATE = "V40_PROBE_CONFIRM_ALLOWED"

MASTER_STOP_RULE = (
    "唯一一次 18-call 全新确认；不再调 decoder 参数；不复用 V40 probe 作为确认样本。"
    "无论结果如何：不追加 blocks、不补跑、不做第二轮确认。"
)

# ---------------------------------------------------------------------------
# Terminals, gates, records (design Sections 7/8/11)
# ---------------------------------------------------------------------------

TERMINAL_EVIDENCE_INVALID = "V41_EVIDENCE_INVALID"
TERMINAL_BOTH_LANES_RETAINED = "V41_BOTH_LANES_RETAINED"
TERMINAL_C_ONLY_RETAINED = "V41_C_ONLY_RETAINED"
TERMINAL_B_ONLY_RETAINED = "V41_B_ONLY_RETAINED"
TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION = "V41_STOP_BC_PARAMETER_OPTIMIZATION"
ALL_TERMINALS = frozenset(
    {
        TERMINAL_EVIDENCE_INVALID,
        TERMINAL_BOTH_LANES_RETAINED,
        TERMINAL_C_ONLY_RETAINED,
        TERMINAL_B_ONLY_RETAINED,
        TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION,
    }
)

REASON_WRONG_CODEWORD_GLOBAL = "WRONG_CODEWORD_GLOBAL"
REASON_BOTH_LANES_GATES_FAILED = "BOTH_LANES_GATES_FAILED"

G1_MIN_EXACT_TOTAL = 7  # out of 9 per lane
G2_MIN_PER_SOURCE = 2  # out of 3 per source within a lane

RECORD_FIELDS: tuple[str, ...] = (
    "call_id",
    "lane",
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

# Exact call-kwarg contract for evaluate_single_block (no warm start etc.; J9).
ALLOWED_CALL_KEYS = frozenset(
    {"H", "source", "block_seed", "lane", "construction_seed", "counts",
     "max_iter", "damping_alpha", "fake_runner", "field"}
)

CLAIM_BOUNDARY: tuple[str, ...] = (
    "results support ONLY bounded route-retention judgments on V25 TRAIN "
    "empirical-count development blocks with oracle-L1 inputs - these are NOT "
    "real-frame FER evidence",
    "do not infer threshold, SKR, formal-execution, qualification, or promotion results",
    "success metric is exact_l2 only; syndrome_ok/wrong_codeword reported separately "
    "and wrong codewords are NEVER counted as exact recoveries",
    "retention gates judge ROUTE RETENTION only; they are NOT a Lane C or Lane B "
    "superiority result and support no B-vs-C comparative ranking regardless of outcome",
    "forbidden regardless of outcome: FER, asymptotic threshold, SKR, security, formal "
    "qualification, promotion, real-frame behavior, Lane C superiority, Lane B superiority, "
    "or any statement that historical gates would now pass",
    "retention terminals do not auto-start any successor work; successor directions "
    "(more-realistic/non-oracle comparison after dual retention; protograph/MET after STOP) "
    "are directional descriptions recorded in this summary only",
)

STATISTICS_NOTE = (
    "Descriptive only; sample is tiny and clustered (18 calls = 9 unique blocks x 2 lanes). "
    "Exact-recovery proportions are reported with n and raw counts; any interval printed is "
    "naive and uncorrected for block/lane clustering; no significance testing is performed. "
    "Success means exact_l2 only."
)


class IntegrityFailure(Exception):
    """Raised when a frozen integrity check fails (check id + message)."""

    def __init__(self, check_id: str, message: str) -> None:
        super().__init__(f"[{check_id}] {message}")
        self.check_id = check_id
        self.message = message


# ---------------------------------------------------------------------------
# Seed-registry validator (J2)
# ---------------------------------------------------------------------------


def validate_seed_registry(seeds: Optional[dict[str, list[int]]] = None) -> tuple[bool, str]:
    """No duplicates among the nine; zero overlap with the forbidden union;
    exactly three seeds per source (J2)."""
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
        return False, (
            f"new seeds overlap V36_A3/V39/V40-probe registries: {sorted(overlap)}"
        )
    return True, "SEED_REGISTRY_OK"


# ---------------------------------------------------------------------------
# Structural reconstruction (J3; decoder-free, strict match vs authority)
# ---------------------------------------------------------------------------

DEFAULT_CONSTRUCTORS: dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]] = {
    "lane_b": construct_lane_b_prototype,
    "lane_c": construct_lane_c_prototype,
}

# The six unique (lane, source) reconstruction keys at representative ordinal 2.
RECONSTRUCTION_KEYS: tuple[tuple[str, str], ...] = tuple(
    (lane, source) for lane in LANE_ORDER for source in SOURCE_ORDER
)


def _reject_forbidden_npz(path: Path | str) -> None:
    name = Path(path).name
    suffix = Path(path).suffix.lower()
    if name == FORBIDDEN_WINNER_NPZ_NAME or suffix == ".npz":
        raise IntegrityFailure(
            "J8",
            f"structural authority must be the committed run_01 JSON, got NPZ path: {path}",
        )


def reconstruct_v41_matrices(
    reference_metrics_path: Path | str = STRUCTURAL_AUTHORITY_PATH,
    field: Optional[GF2mField] = None,
    constructors: Optional[dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]]] = None,
) -> dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]]:
    """Rebuild exactly the six ordinal-2 representative matrices via the accepted
    V38 constructors and strictly compare against the committed structural
    authority (including Lane C ``position_permutations``).

    Representative identities must equal the frozen constants. Decoder-free,
    write-free; the ignored NPZ archive is never an input (J8) and no NPZ is
    ever written.
    """
    _reject_forbidden_npz(reference_metrics_path)
    try:
        reference_by_id = _load_v38r1_reference_metrics(reference_metrics_path)
    except ValueError as exc:
        raise IntegrityFailure("J3", f"structural authority unusable: {exc}") from exc
    field = field or GF2mField.create(DIMENSION)
    if field.primitive_polynomial != POLYNOMIAL:
        raise IntegrityFailure(
            "J9", f"field polynomial mismatch: expected {POLYNOMIAL}, got {field.primitive_polynomial}"
        )
    ctor_map = constructors or DEFAULT_CONSTRUCTORS
    matrices: dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]] = {}
    for lane, source in RECONSTRUCTION_KEYS:
        seed = _rep_seed(lane, source)
        matrix_id = f"{lane}_{source}_s{seed}"
        if matrix_id not in FROZEN_REPRESENTATIVE_MATRIX_IDS:
            raise IntegrityFailure(
                "J3", f"representative identity drift: {matrix_id} not in frozen constants"
            )
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
        if lane == "lane_c" and "position_permutations" not in expected:
            raise IntegrityFailure("J3", f"missing frozen Lane C permutations: {matrix_id}")
        matrices[(lane, source)] = (matrix, metrics)
    if len(matrices) != 6:
        raise IntegrityFailure("J3", f"must reconstruct exactly 6 matrices, got {len(matrices)}")
    return matrices


# ---------------------------------------------------------------------------
# Posterior-binding preflight (J5; decoder-free, write-free)
# ---------------------------------------------------------------------------


def posterior_binding_preflight(
    counts_by_source: dict[str, np.ndarray],
    probes: Optional[dict[str, int]] = None,
    posterior_fn: Optional[Callable[..., np.ndarray]] = None,
) -> dict[str, dict[str, Any]]:
    """Verify complete-Bob binding on the first new block of each source.

    Fixed sentinels per probe block (design Section 10): bob_gt_31,
    captured_equals_bob, corrected_equals_direct, corrected_differs_u2bob_arraywise,
    corrected_differs_u2bob_maxabs (>1e-6), argmax_divergence. Zero production
    decoder calls; writes nothing.
    """
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

        prior_corrected = _spy(counts, bob, u1_alice)
        prior_direct = real_posterior(counts, bob, u1_alice)
        prior_u2bob = real_posterior(counts, u2_bob, u1_alice)

        am_corrected = np.argmax(prior_corrected, axis=1)
        am_u2bob = np.argmax(prior_u2bob, axis=1)
        checks = {
            "probe_block_seed": int(probe_seed),
            "bob_gt_31": bool(np.any(np.asarray(bob) > 31)),
            "captured_equals_bob": bool(np.array_equal(captured["second_argument"], np.asarray(bob))),
            "corrected_equals_direct": bool(np.array_equal(prior_corrected, prior_direct)),
            "corrected_differs_u2bob_arraywise": bool(not np.array_equal(prior_corrected, prior_u2bob)),
            "corrected_differs_u2bob_maxabs": bool(
                float(np.max(np.abs(prior_corrected - prior_u2bob))) > 1e-6
            ),
            "argmax_divergence": bool(not np.array_equal(am_corrected, am_u2bob)),
        }
        failed = [name for name, ok in checks.items() if isinstance(ok, bool) and not ok]
        if failed:
            raise IntegrityFailure(
                "J5",
                f"posterior-binding sentinel failed on preflight block {source}/{probe_seed}: "
                f"{failed}; sentinel probes are replaceable only at plan-review stage",
            )
        results[source] = checks
    return results


# ---------------------------------------------------------------------------
# Budget accounting (J10)
# ---------------------------------------------------------------------------


class CallAccounting:
    """Hard-capped started/completed actuals for the single 18-call phase."""

    def __init__(self, hard_cap: int = HARD_CALL_CAP) -> None:
        self.hard_cap = int(hard_cap)
        self.started = 0
        self.completed = 0

    def register_start(self) -> None:
        if self.started >= self.hard_cap:
            raise IntegrityFailure(
                "J10",
                f"hard call cap {self.hard_cap} reached; call {self.started + 1} structurally refused",
            )
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
# Records and post-evaluation checks (J9/J6/J11/J12)
# ---------------------------------------------------------------------------


def validate_decoder_contract(call_params: dict[str, Any], expected_setting: tuple[int, float]) -> None:
    """Exact call-path contract: fixed keys, frozen setting, no warm start (J9)."""
    extra = set(call_params.keys()) - ALLOWED_CALL_KEYS
    if extra:
        raise IntegrityFailure(
            "J9", f"unexpected call parameters (warm-start/third-setting class): {sorted(extra)}"
        )
    if call_params["max_iter"] != expected_setting[0] or call_params["damping_alpha"] != expected_setting[1]:
        raise IntegrityFailure(
            "J9",
            f"decoder settings {call_params['max_iter']}/{call_params['damping_alpha']} != frozen {expected_setting}",
        )


def build_record(spec: dict[str, Any], raw: dict[str, Any], setting: tuple[int, float]) -> dict[str, Any]:
    """Normalize one evaluator result into the record schema of design Section 11."""
    exact = bool(raw["exact_l2"])
    syndrome_ok = bool(raw["syndrome_ok"])
    record = {
        "call_id": spec["call_id"],
        "lane": raw["lane"],
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
    return {key: record[key] for key in RECORD_FIELDS}


def validate_record_schema(record: dict[str, Any]) -> tuple[bool, str]:
    """Record schema completeness incl. derived wrong_codeword and frozen setting (J11/J9)."""
    for key in RECORD_FIELDS:
        if key not in record:
            return False, f"missing field {key}"
    valid_call_ids = {spec["call_id"] for spec in FROZEN_WORKLOAD}
    if record["call_id"] not in valid_call_ids:
        return False, f"invalid call_id {record['call_id']!r}"
    if record["lane"] not in LANE_ORDER or record["source"] not in SOURCE_ORDER:
        return False, f"invalid lane/source {record['lane']!r}/{record['source']!r}"
    for key in ("exact_l2", "syndrome_ok", "wrong_codeword"):
        if not isinstance(record[key], bool):
            return False, f"field {key} must be bool"
    for key in ("errors_initial", "errors_final", "iterations", "max_iter", "block_seed",
                "construction_seed", "construction_seed_ordinal"):
        if not isinstance(record[key], int) or isinstance(record[key], bool):
            return False, f"field {key} must be int"
    if record["max_iter"] != MAX_ITER or record["damping_alpha"] != DAMPING_ALPHA:
        return False, (
            f"record setting {record['max_iter']}/{record['damping_alpha']} != frozen "
            f"{DECODER_SETTING} (J9)"
        )
    expected_wrong = record["syndrome_ok"] and not record["exact_l2"]
    if record["wrong_codeword"] != expected_wrong:
        return False, "wrong_codeword must equal syndrome_ok and not exact_l2"
    return True, "SCHEMA_OK"


def validate_post_evaluation(records: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Schema (J11), workload membership/order (J12), cross-lane errors_initial
    equality per block (J6), and frozen decoder setting on every record."""
    failures: list[tuple[str, str]] = []

    for rec in records:
        ok, msg = validate_record_schema(rec)
        if not ok:
            failures.append(("J11", f"record {rec.get('call_id')}: {msg}"))

    expected_order = [
        (row["call_id"], row["lane"], row["source"], row["block_seed"], row["matrix_id"])
        for row in workload_rows()
    ]
    actual_order = [
        (rec["call_id"], rec["lane"], rec["source"], rec["block_seed"], rec["matrix_id"])
        for rec in records
    ]
    if actual_order != expected_order[: len(actual_order)]:
        failures.append(
            ("J12", f"workload membership/order drift: {actual_order} != frozen C01-C18 prefix")
        )

    by_block: dict[int, set[int]] = {}
    for rec in records:
        by_block.setdefault(rec["block_seed"], set()).add(rec["errors_initial"])
    for block_seed, initials in sorted(by_block.items()):
        if len(initials) != 1:
            failures.append(
                ("J6", f"block {block_seed}: cross-lane errors_initial mismatch {sorted(initials)}")
            )
    return failures


# ---------------------------------------------------------------------------
# Aggregates, gates, terminal machine (design Sections 7/8)
# ---------------------------------------------------------------------------


def aggregate_results(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-lane and per-source aggregates over complete records."""
    per_lane: dict[str, dict[str, Any]] = {}
    for lane in LANE_ORDER:
        recs = [r for r in records if r["lane"] == lane]
        per_lane[lane] = {
            "calls": len(recs),
            "exact_total": sum(1 for r in recs if r["exact_l2"]),
            "wrong_count": sum(1 for r in recs if r["wrong_codeword"]),
            "exact_by_source": {
                source: sum(1 for r in recs if r["source"] == source and r["exact_l2"])
                for source in SOURCE_ORDER
            },
        }
    per_source: dict[str, dict[str, Any]] = {}
    for source in SOURCE_ORDER:
        recs = [r for r in records if r["source"] == source]
        per_source[source] = {
            "calls": len(recs),
            "exact_total": sum(1 for r in recs if r["exact_l2"]),
            "by_lane": {
                lane: sum(1 for r in recs if r["lane"] == lane and r["exact_l2"])
                for lane in LANE_ORDER
            },
        }
    return {
        "per_lane": per_lane,
        "per_source": per_source,
        "wrong_total": sum(1 for r in records if r["wrong_codeword"]),
    }


def evaluate_lane_gate(lane: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-lane retention gate G1/G2/G3 (route retention only; design Section 7)."""
    recs = [r for r in records if r["lane"] == lane]
    exact_total = sum(1 for r in recs if r["exact_l2"])
    exact_by_source = {
        source: sum(1 for r in recs if r["source"] == source and r["exact_l2"])
        for source in SOURCE_ORDER
    }
    wrong_count = sum(1 for r in recs if r["wrong_codeword"])
    g1_pass = exact_total >= G1_MIN_EXACT_TOTAL
    g2_pass = len(recs) == 9 and all(v >= G2_MIN_PER_SOURCE for v in exact_by_source.values())
    g3_pass = wrong_count == 0
    return {
        "lane": lane,
        "calls": len(recs),
        "g1_overall_exact_ge_7_of_9": {"exact_total": exact_total, "threshold": G1_MIN_EXACT_TOTAL, "pass": g1_pass},
        "g2_every_source_ge_2_of_3": {"exact_by_source": exact_by_source, "threshold_per_source": G2_MIN_PER_SOURCE, "pass": g2_pass},
        "g3_wrong_zero": {"wrong_count": wrong_count, "pass": g3_pass},
        "passed": bool(g1_pass and g2_pass and g3_pass),
    }


def determine_v41_terminal(
    integrity_ok: bool,
    wrong_total: int,
    pass_lane_c: bool,
    pass_lane_b: bool,
) -> tuple[str, Optional[str], list[str]]:
    """Total, disjoint terminal machine (design Section 8 rules 0-5; first-match-wins)."""
    trace: list[str] = []
    if not integrity_ok:
        trace.append("rule_0_integrity_or_execution_failure -> V41_EVIDENCE_INVALID")
        return TERMINAL_EVIDENCE_INVALID, None, trace
    trace.append("rule_0_integrity_ok")
    if wrong_total > 0:
        trace.append(f"rule_1_wrong_total={wrong_total} -> V41_STOP_BC_PARAMETER_OPTIMIZATION")
        return TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION, REASON_WRONG_CODEWORD_GLOBAL, trace
    trace.append("rule_1_no_wrong_codeword_no_fire")
    if pass_lane_c and pass_lane_b:
        trace.append("rule_2_both_gates_pass -> V41_BOTH_LANES_RETAINED")
        return TERMINAL_BOTH_LANES_RETAINED, None, trace
    if pass_lane_c:
        trace.append("rule_3_only_lane_c_passes -> V41_C_ONLY_RETAINED")
        return TERMINAL_C_ONLY_RETAINED, None, trace
    if pass_lane_b:
        trace.append("rule_4_only_lane_b_passes -> V41_B_ONLY_RETAINED")
        return TERMINAL_B_ONLY_RETAINED, None, trace
    trace.append("rule_5_both_gates_failed -> V41_STOP_BC_PARAMETER_OPTIMIZATION")
    return TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION, REASON_BOTH_LANES_GATES_FAILED, trace


# ---------------------------------------------------------------------------
# Environment loaders and git binding (accepted pattern, v41 four-file scope)
# ---------------------------------------------------------------------------


def describe_v25_counts_provenance() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[4] / V25_COUNTS_RELATIVE_PATH
    return {
        "path": str(path),
        "loader": "comparison_bench.formal_ir.v35_algorithm_development.load_v25_channel_counts",
        "role": "source-specific V25 TRAIN empirical counts (read-only)",
        "exists": path.is_file(),
    }


def git_rev_parse(repo_root: Path, ref: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", ref],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def verify_scoped_clean(
    repo_root: Path,
    relative_paths: tuple[str, ...] = SCOPED_TRACKED_PATHS,
) -> None:
    """Refuse execution when any scoped tracked file differs from HEAD (J1)."""
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "HEAD", "--quiet", "--", *relative_paths],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise IntegrityFailure(
            "J1_TRACKED_DIRTY",
            f"scoped tracked files differ from HEAD; commit or revert before "
            f"execution: {list(relative_paths)}",
        )


def verify_execution_sha_binding(repo_root: Path, authorized_target_sha: str) -> dict[str, str]:
    """Exact-equality binding of HEAD AND origin branch to the authorized SHA (J1)."""
    head = git_rev_parse(repo_root, "HEAD")
    branch = git_rev_parse(repo_root, BRANCH_REF)
    if head != authorized_target_sha or branch != authorized_target_sha:
        raise IntegrityFailure(
            "J1_SHA_BINDING_MISMATCH",
            f"authorized_target_sha={authorized_target_sha} but HEAD={head} and {BRANCH_REF}={branch}",
        )
    return {"HEAD": head, BRANCH_REF: branch}


# ---------------------------------------------------------------------------
# Guarded confirmation runner (exactly 18 calls)
# ---------------------------------------------------------------------------


def _run_workload_calls(
    matrices: dict[tuple[str, str], tuple[np.ndarray, dict[str, Any]]],
    counts_by_source: dict[str, np.ndarray],
    field: GF2mField,
    fake_runner: bool,
    setting: tuple[int, float],
    accounting: CallAccounting,
    sink: list[dict[str, Any]],
) -> None:
    """Append records progressively so partial evidence survives a mid-run crash."""
    for row in workload_rows():
        matrix, _ = matrices[(row["lane"], row["source"])]
        accounting.register_start()  # raises J10 structurally at call 19
        call_params = {
            "H": matrix,
            "source": row["source"],
            "block_seed": row["block_seed"],
            "lane": row["lane"],
            "construction_seed": row["construction_seed"],
            "counts": counts_by_source[row["source"]],
            "max_iter": setting[0],
            "damping_alpha": setting[1],
            "fake_runner": fake_runner,
            "field": field,
        }
        validate_decoder_contract(call_params, setting)
        raw = evaluate_single_block(**call_params)
        record = build_record(row, raw, setting)
        accounting.register_complete()
        sink.append(record)


def build_v41_summary(
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
) -> dict[str, Any]:
    """Summary with terminal determination displayed BEFORE gate details (D4)."""
    invalid = terminal_state == TERMINAL_EVIDENCE_INVALID
    planned = PLANNED_CALLS
    return {
        "cycle_id": CYCLE_ID,
        "change_id": CHANGE_ID,
        "lifecycle_state": lifecycle_state,
        "execution_scope": EXECUTION_SCOPE,
        "fake_runner": fake_runner,
        "provenance": {
            "authorized_target_sha": authorized_target_sha,
            "sha_binding": sha_binding,
            "structural_authority": str(STRUCTURAL_AUTHORITY_PATH),
            "structural_records_strict_match": structural_matrices_count,
            "predecessor_cycle": PREDECESSOR_CYCLE,
            "predecessor_terminal_state": PREDECESSOR_TERMINAL_STATE,
            "predecessor_plan_sha": PREDECESSOR_PLAN_SHA,
            "predecessor_execution_sha": PREDECESSOR_EXECUTION_SHA,
        },
        "v25_counts_provenance": counts_provenance,
        "accounting": {
            "decoder_calls_planned": {"total": planned},
            "decoder_calls_started": {"total": accounting.started},
            "decoder_calls_completed": {"total": accounting.completed},
            "structural_reconstruction_decoder_calls": 0,
            "preflight_decoder_calls": 0,
        },
        "npz_policy": {
            "forbidden_winner_npz_read": False,
            "any_npz_output_written": False,
            "v25_channel_counts_npz_read_only_allowed": True,
        },
        "routing_trace": routing_trace,
        "terminal_state": terminal_state,
        "terminal_reason": terminal_reason,
        "gate_evaluation": gate_evaluation if gate_evaluation is not None else {},
        "aggregates": aggregates if aggregates is not None else {},
        "master_stop_rule": MASTER_STOP_RULE,
        "statistics_note": STATISTICS_NOTE,
        "claim_boundary": list(CLAIM_BOUNDARY),
        "integrity_failures": (
            [{"check": cid, "message": msg} for cid, msg in integrity_failures]
            if integrity_failures
            else []
        ),
        "performance_interpretation_presented": not invalid,
    }


# ---------------------------------------------------------------------------
# Evidence writers (additive root, CSV/JSON parity, no NPZ)
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


def write_v41_outputs(
    output_root: Path | str,
    records: list[dict[str, Any]],
    summary: dict[str, Any],
) -> Path:
    """Write the minimal fixed file set (design D10); fail closed on non-empty root.

    The guarded runner pre-creates the (empty) root just before the decoder
    stage, so writing into an existing-but-empty root owned by this run is
    expected; any pre-existing NON-empty root is refused. No NPZ is ever written.
    """
    root = Path(output_root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"J7: refusing to overwrite non-empty output root: {root}")
    if not root.exists():
        root.mkdir(parents=True)

    def dump(name: str, payload: Any) -> None:
        with (root / name).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    dump("v41_confirm_records.json", records)
    write_records_csv(root / "v41_confirm_records.csv", records, list(RECORD_FIELDS))
    dump("v41_summary.json", summary)
    return root


def write_invalid_notice(
    output_root: Path | str,
    integrity_failures: list[tuple[str, str]],
    partial_records_retained: bool,
) -> Path:
    root = Path(output_root)
    notice = {
        "cycle_id": CYCLE_ID,
        "terminal_state": TERMINAL_EVIDENCE_INVALID,
        "integrity_failures": [
            {"check": cid, "message": msg} for cid, msg in integrity_failures
        ],
        "partial_records_retained_byte_for_byte": partial_records_retained,
        "performance_interpretation": "none",
    }
    path = root / "v41_invalid_notice.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(notice, handle, indent=2)
    return path


def _persist_invalid_evidence(
    root: Path,
    *,
    records: list[dict[str, Any]],
    accounting: CallAccounting,
    summary_ctx: dict[str, Any],
    failures: list[tuple[str, str]],
    partial_records_retained: bool,
) -> None:
    """Retain collected records byte-for-byte plus notice/summary; no aggregation.

    Never masks the original failure with writer problems. Preflight failures
    pass empty records (trio: notice + empty records + summary, D9).
    """
    try:
        if not root.exists():
            root.mkdir(parents=True)
        with (root / "v41_confirm_records.json").open("w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2)
        write_records_csv(root / "v41_confirm_records.csv", records, list(RECORD_FIELDS))
        summary = build_v41_summary(
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
        )
        with (root / "v41_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        write_invalid_notice(root, failures, partial_records_retained=partial_records_retained)
    except Exception:  # ponytail: accepted V40 pattern - never mask the original failure
        pass


def run_v41_confirmation(
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
) -> dict[str, Any]:
    """Guarded single-run orchestration; default-deny, fail-closed.

    Order (design Section 10): refusal-class guards FIRST (default deny, flags,
    SHA binding, scoped dirty) with NOTHING created on failure; then scientific
    preflights (J2 registry, J3 reconstruction, J4 counts, J5 sentinels);
    preflight failure creates the additive root with the invalid trio and stops
    with ZERO calls; success creates the root before the first decoder call.
    """
    if not execution_authorized:
        raise PermissionError(
            "EXECUTE_NOT_AUTHORIZED: pass --execution-authorized bound to an "
            f"explicit user EXECUTE_AUTH for scope {EXECUTION_SCOPE}"
        )

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
            raise IntegrityFailure(
                "J1_SHA_BINDING_MISSING",
                "authorized_target_sha is required for the authorized run",
            )
        sha_binding = verify_execution_sha_binding(REPO_ROOT, authorized_target_sha)
    if check_scoped_dirty:
        # Execution-refusal class failure: raised before any evidence root exists.
        verify_scoped_clean(REPO_ROOT)

    # ---- scientific preflights (decoder-free, write-free) ------------------
    summary_ctx: dict[str, Any] = {
        "fake_runner": fake_runner,
        "authorized_target_sha": authorized_target_sha,
        "sha_binding": sha_binding,
        "counts_provenance": {},
        "structural_matrices_count": 0,
    }
    try:
        registry_ok, registry_msg = validate_seed_registry()
        if not registry_ok:
            raise IntegrityFailure("J2", registry_msg)

        spath = Path(structural_authority_path) if structural_authority_path else STRUCTURAL_AUTHORITY_PATH
        matrices = reconstruct_v41_matrices(
            reference_metrics_path=spath,
            field=field,
            constructors=constructors,
        )
        summary_ctx["structural_matrices_count"] = len(matrices)

        counts = counts_by_source if counts_by_source is not None else load_v25_channel_counts()
        for source in SOURCE_ORDER:
            if counts[source].shape != (BLOCK_LENGTH, BLOCK_LENGTH):
                raise IntegrityFailure(
                    "J4", f"unexpected counts shape for {source}: {counts[source].shape}"
                )
        counts_provenance = describe_v25_counts_provenance()
        summary_ctx["counts_provenance"] = counts_provenance

        posterior_binding_preflight(counts)  # raises IntegrityFailure("J5") on any sentinel failure
    except IntegrityFailure as exc:
        _persist_invalid_evidence(
            root,
            records=[],
            accounting=CallAccounting(),
            summary_ctx=summary_ctx,
            failures=[(exc.check_id, exc.message)],
            partial_records_retained=False,
        )
        return {
            "output_root": str(root),
            "terminal_state": TERMINAL_EVIDENCE_INVALID,
            "terminal_reason": None,
            "integrity_failures": [(exc.check_id, exc.message)],
        }

    # ---- decoder stage: occupy the additive root NOW -----------------------
    # From this point any crash - including KeyboardInterrupt or process kill -
    # leaves the root (plus retained raw partials) in place so a relaunch fails
    # closed on J7 instead of silently re-running.
    root.mkdir(parents=True)
    accounting = CallAccounting()
    records: list[dict[str, Any]] = []
    try:
        _run_workload_calls(
            matrices, counts, field, fake_runner, DECODER_SETTING, accounting, records,
        )

        failures = validate_post_evaluation(records) + accounting.validate_executed()
        if failures:
            _persist_invalid_evidence(
                root, records=records, accounting=accounting,
                summary_ctx=summary_ctx, failures=failures,
                partial_records_retained=True,
            )
            return {
                "output_root": str(root),
                "terminal_state": TERMINAL_EVIDENCE_INVALID,
                "terminal_reason": None,
                "integrity_failures": failures,
            }

        aggregates = aggregate_results(records)
        gate_evaluation = {lane: evaluate_lane_gate(lane, records) for lane in LANE_ORDER}
        terminal_state, terminal_reason, routing_trace = determine_v41_terminal(
            integrity_ok=True,
            wrong_total=int(aggregates["wrong_total"]),
            pass_lane_c=bool(gate_evaluation["lane_c"]["passed"]),
            pass_lane_b=bool(gate_evaluation["lane_b"]["passed"]),
        )

        summary = build_v41_summary(
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
        )
        write_v41_outputs(root, records, summary)
        return {
            "output_root": str(root),
            "terminal_state": terminal_state,
            "terminal_reason": terminal_reason,
            "routing_trace": routing_trace,
            "decoder_calls_completed": accounting.completed,
            "aggregates": aggregates,
            "gate_evaluation": gate_evaluation,
            "summary": summary,
        }
    except BaseException:
        _persist_invalid_evidence(
            root, records=records, accounting=accounting, summary_ctx=summary_ctx,
            failures=[("mid_run_failure", "raw partial records retained; no performance aggregate generated")],
            partial_records_retained=True,
        )
        raise
