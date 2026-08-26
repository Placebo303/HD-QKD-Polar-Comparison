"""V40P0 decoder-cap diagnostic: guarded runner and writer.

Implements the frozen V40P0 diagnostic protocol (change
``formal-ir-v40-decoder-cap-diagnostic``, accepted plan SHA
36a3751e190ff06e0e88024b51b6f8713c13a4dc):

- Phase A (exactly 12 calls): the 12 instances underlying V39 run_01's six
  ``NEITHER_EXACT`` pairs, re-decoded at max_iter=90, damping_alpha=1.0.
- Phase B (conditionally exactly 12 calls): same instances at 90/0.7; only
  when W_A == 0 AND R_A <= 1 (out of 12) AND IMP_A >= 0.25.
- Probe (conditionally exactly 6 calls): three new TRAIN blocks
  (390106/390206/390306) x two representative ordinal-2 matrices per lane,
  at the single setting selected by Phase A/B.
- Hard budget 30 real decoder calls, exactly once, additive outputs,
  integrity-first terminal machine (design Section 13 rules 0-6).

Lifecycle: IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED.
This module performs no execution on import, never imports the v39 module
(design D6: pattern copy only; V39 run_01 JSONs are read as data), never
reads ``v38_winning_matrices.npz`` and never writes any NPZ.
"""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

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
    SOURCE_CHECKS,
    V36_A3_BLOCK_SEEDS,
    _check_v38r1_metric_match,
    _load_v38r1_reference_metrics,
    construct_lane_b_prototype,
    construct_lane_c_prototype,
    evaluate_single_block,
)

# ---------------------------------------------------------------------------
# Frozen protocol constants
# ---------------------------------------------------------------------------

CYCLE_ID = "V40P0"
CHANGE_ID = "formal-ir-v40-decoder-cap-diagnostic"
ACCEPTED_PLAN_SHA = "36a3751e190ff06e0e88024b51b6f8713c13a4dc"
BRANCH_REF = "origin/formal-ir-mainline"

POLYNOMIAL = 37
DIMENSION = 32

SOURCE_ORDER: tuple[str, ...] = ("1M", "1p5M", "2M")
LANE_ORDER: tuple[str, ...] = ("lane_c", "lane_b")

PHASE_A = "phase_a"
PHASE_B = "phase_b"
PROBE = "probe"
EXECUTED_PHASE_ORDER: tuple[str, ...] = (PHASE_A, PHASE_B, PROBE)

# Decoder contract per phase (design Section 10): (max_iter, damping_alpha).
PHASE_SETTINGS: dict[str, tuple[int, float]] = {
    PHASE_A: (90, 1.0),
    PHASE_B: (90, 0.7),
}
PROBE_SETTINGS_BY_TRIGGER = {"CAP_MATERIAL": (90, 1.0), "DAMPING_VALUE": (90, 0.7)}
BUDGET_CAPS: dict[str, int] = {PHASE_A: 12, PHASE_B: 12, PROBE: 6}
HARD_CALL_CAP = 30

# Frozen instance table A01-A12 (design Section 3). Extracted rows must equal
# this table field-by-field in this exact order (J1).
# NOTE: errors_initial=252 for A11/A12 (block 390101) comes from the V39
# run_01 paired-comparison authority (design Section 2, read-only) --
# identical to A01-A06 on the same block_seed, as required by the design's
# deterministic sampling semantics and the J7 cross-lane equality rule.
FROZEN_INSTANCES: tuple[dict[str, Any], ...] = (
    {"idx": "A01", "pair_no": 1, "lane": "lane_c", "source": "1M", "construction_seed_ordinal": 1, "construction_seed": 383101, "block_seed": 390101, "matrix_id": "lane_c_1M_s383101", "v39_reference_errors_initial": 252, "v39_reference_errors_final": 139, "v39_reference_exact_l2": False},
    {"idx": "A02", "pair_no": 1, "lane": "lane_b", "source": "1M", "construction_seed_ordinal": 1, "construction_seed": 382101, "block_seed": 390101, "matrix_id": "lane_b_1M_s382101", "v39_reference_errors_initial": 252, "v39_reference_errors_final": 127, "v39_reference_exact_l2": False},
    {"idx": "A03", "pair_no": 2, "lane": "lane_c", "source": "1M", "construction_seed_ordinal": 1, "construction_seed": 383101, "block_seed": 390103, "matrix_id": "lane_c_1M_s383101", "v39_reference_errors_initial": 274, "v39_reference_errors_final": 196, "v39_reference_exact_l2": False},
    {"idx": "A04", "pair_no": 2, "lane": "lane_b", "source": "1M", "construction_seed_ordinal": 1, "construction_seed": 382101, "block_seed": 390103, "matrix_id": "lane_b_1M_s382101", "v39_reference_errors_initial": 274, "v39_reference_errors_final": 79, "v39_reference_exact_l2": False},
    {"idx": "A05", "pair_no": 3, "lane": "lane_c", "source": "1M", "construction_seed_ordinal": 2, "construction_seed": 383102, "block_seed": 390101, "matrix_id": "lane_c_1M_s383102", "v39_reference_errors_initial": 252, "v39_reference_errors_final": 171, "v39_reference_exact_l2": False},
    {"idx": "A06", "pair_no": 3, "lane": "lane_b", "source": "1M", "construction_seed_ordinal": 2, "construction_seed": 382102, "block_seed": 390101, "matrix_id": "lane_b_1M_s382102", "v39_reference_errors_initial": 252, "v39_reference_errors_final": 198, "v39_reference_exact_l2": False},
    {"idx": "A07", "pair_no": 4, "lane": "lane_c", "source": "1M", "construction_seed_ordinal": 2, "construction_seed": 383102, "block_seed": 390102, "matrix_id": "lane_c_1M_s383102", "v39_reference_errors_initial": 258, "v39_reference_errors_final": 75, "v39_reference_exact_l2": False},
    {"idx": "A08", "pair_no": 4, "lane": "lane_b", "source": "1M", "construction_seed_ordinal": 2, "construction_seed": 382102, "block_seed": 390102, "matrix_id": "lane_b_1M_s382102", "v39_reference_errors_initial": 258, "v39_reference_errors_final": 77, "v39_reference_exact_l2": False},
    {"idx": "A09", "pair_no": 5, "lane": "lane_c", "source": "1M", "construction_seed_ordinal": 2, "construction_seed": 383102, "block_seed": 390103, "matrix_id": "lane_c_1M_s383102", "v39_reference_errors_initial": 274, "v39_reference_errors_final": 195, "v39_reference_exact_l2": False},
    {"idx": "A10", "pair_no": 5, "lane": "lane_b", "source": "1M", "construction_seed_ordinal": 2, "construction_seed": 382102, "block_seed": 390103, "matrix_id": "lane_b_1M_s382102", "v39_reference_errors_initial": 274, "v39_reference_errors_final": 97, "v39_reference_exact_l2": False},
    {"idx": "A11", "pair_no": 6, "lane": "lane_c", "source": "1M", "construction_seed_ordinal": 3, "construction_seed": 383103, "block_seed": 390101, "matrix_id": "lane_c_1M_s383103", "v39_reference_errors_initial": 252, "v39_reference_errors_final": 184, "v39_reference_exact_l2": False},
    {"idx": "A12", "pair_no": 6, "lane": "lane_b", "source": "1M", "construction_seed_ordinal": 3, "construction_seed": 382103, "block_seed": 390101, "matrix_id": "lane_b_1M_s382103", "v39_reference_errors_initial": 252, "v39_reference_errors_final": 220, "v39_reference_exact_l2": False},
)

# Representative construction-seed ordinals frozen from the V39 run_01
# summary argmax (lane_c ordinals 1/2/3 = 11/12/10 -> 2; lane_b 10/11/10 -> 2).
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

# New probe block seeds (frozen; one never-used TRAIN development block per source).
PROBE_BLOCK_SEEDS: dict[str, int] = {"1M": 390106, "1p5M": 390206, "2M": 390306}
# V39 block registry (data copied from the committed V39 protocol; the v39
# module is deliberately NOT imported, design D6).
V39_BLOCK_SEEDS: dict[str, list[int]] = {
    "1M": [390101, 390102, 390103, 390104, 390105],
    "1p5M": [390201, 390202, 390203, 390204, 390205],
    "2M": [390301, 390302, 390303, 390304, 390305],
}
FORBIDDEN_BLOCK_SEEDS: frozenset[int] = frozenset(
    seed for seeds in (*V36_A3_BLOCK_SEEDS.values(), *V39_BLOCK_SEEDS.values()) for seed in seeds
)

# Frozen probe workload PR1-PR6 (design Section 8; D8 order).
PROBE_WORKLOAD: tuple[dict[str, Any], ...] = (
    {"call": "PR1", "lane": "lane_c", "source": "1M", "block_seed": 390106},
    {"call": "PR2", "lane": "lane_b", "source": "1M", "block_seed": 390106},
    {"call": "PR3", "lane": "lane_c", "source": "1p5M", "block_seed": 390206},
    {"call": "PR4", "lane": "lane_b", "source": "1p5M", "block_seed": 390206},
    {"call": "PR5", "lane": "lane_c", "source": "2M", "block_seed": 390306},
    {"call": "PR6", "lane": "lane_b", "source": "2M", "block_seed": 390306},
)


def _rep_seed(lane: str, source: str) -> int:
    """Construction seed of the lane's representative ordinal for a source."""
    return CONSTRUCTION_SEEDS[lane][source][REPRESENTATIVE_ORDINALS[lane] - 1]


# 10 unique matrix ids behind the 12 usage rows (Phases A/B + probe).
RECONSTRUCTION_KEYS: tuple[tuple[str, str, int], ...] = tuple(
    dict.fromkeys(
        [(inst["lane"], inst["source"], inst["construction_seed"]) for inst in FROZEN_INSTANCES]
        + [(_rep_kind["lane"], _rep_kind["source"], _rep_seed(_rep_kind["lane"], _rep_kind["source"])) for _rep_kind in PROBE_WORKLOAD]
    )
)

REPO_ROOT = Path(__file__).resolve().parents[4]
PAIRED_AUTHORITY_PATH = (
    REPO_ROOT
    / "comparison_bench/outputs_comparison/formal_ir_methods/v39_lanec_robustness_laneb_control/run_01/v39_paired_comparison.json"
)
SUMMARY_AUTHORITY_PATH = (
    REPO_ROOT
    / "comparison_bench/outputs_comparison/formal_ir_methods/v39_lanec_robustness_laneb_control/run_01/v39_summary.json"
)
STRUCTURAL_AUTHORITY_PATH = (
    REPO_ROOT
    / "comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json"
)
OUTPUT_ROOT = (
    REPO_ROOT
    / "comparison_bench/outputs_comparison/formal_ir_methods/v40_decoder_cap_diagnostic/run_01"
)
FORBIDDEN_WINNER_NPZ_NAME = "v38_winning_matrices.npz"

# Scoped tracked-dirty check: four-file pattern as accepted in V39 (design D6),
# with the v40 module + CLI replacing v39. Checked before root creation (J11).
SCOPED_TRACKED_PATHS: tuple[str, ...] = (
    "comparison_bench/src/comparison_bench/formal_ir/v40_decoder_cap_diagnostic.py",
    "scripts/execute_v40_decoder_cap_diagnostic.py",
    "comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py",
    "comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py",
)

V25_COUNTS_RELATIVE_PATH = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "nbldpc_v25_20260818/run_04/channel_counts.npz"
)

# Predecessor bindings (R1) and input identities recorded in the summary.
PREDECESSOR_PLAN_SHA = "8efb626ba0eaa6b031abd934ed583739ba70065b"
PREDECESSOR_EXECUTION_SHA = "90d2d834c136833000ad612adfd8e09bf815d5d2"
PREDECESSOR_RESULT_SHA = "940bfc996a0bd87d60e958150c4f770ee35f16b8"

MASTER_STOP_RULE = (
    "不同时继续优化 B、C、decoder 和新算法；先用 12 calls 判断 decoder cap；"
    "没有强信号就把额度投入 protograph/MET。"
)

# ---------------------------------------------------------------------------
# Signals and terminals (design Section 13)
# ---------------------------------------------------------------------------

SIGNAL_CAP_MATERIAL = "CAP_MATERIAL"
SIGNAL_WEAK_RESIDUAL = "WEAK_RESIDUAL"
SIGNAL_RESIDUAL_ONLY_NO_EXACT_RESCUE = "RESIDUAL_ONLY_NO_EXACT_RESCUE"
SIGNAL_DAMPING_VALUE = "DAMPING_VALUE"
SIGNAL_DAMPING_NO_VALUE = "DAMPING_NO_VALUE"

TERMINAL_EVIDENCE_INVALID = "V40_EVIDENCE_INVALID"
TERMINAL_GO_STRUCTURE = "V40_GO_STRUCTURE"
TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION = "V40_STOP_BC_PARAMETER_OPTIMIZATION"
TERMINAL_PROBE_INCONCLUSIVE = "V40_PROBE_INCONCLUSIVE"
TERMINAL_PROBE_CONFIRM_ALLOWED = "V40_PROBE_CONFIRM_ALLOWED"
ALL_TERMINALS = frozenset(
    {
        TERMINAL_EVIDENCE_INVALID,
        TERMINAL_GO_STRUCTURE,
        TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION,
        TERMINAL_PROBE_INCONCLUSIVE,
        TERMINAL_PROBE_CONFIRM_ALLOWED,
    }
)

REASON_WRONG_CODEWORD_PHASE_A = "WRONG_CODEWORD_PHASE_A"
REASON_WRONG_CODEWORD_PHASE_B = "WRONG_CODEWORD_PHASE_B"
REASON_WEAK_EXACT_RESCUE = "WEAK_EXACT_RESCUE"
REASON_NO_MATERIAL_CAP_EFFECT = "NO_MATERIAL_CAP_EFFECT"
REASON_DAMPING_NO_VALUE = "DAMPING_NO_VALUE"

RECORD_FIELDS: tuple[str, ...] = (
    "phase",
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
    "v39_reference_errors_final",
    "v39_reference_exact_l2",
    "rescued_vs_v39",
)

# Exact call-kwarg contract for evaluate_single_block (no warm start etc.; J10).
ALLOWED_CALL_KEYS = frozenset(
    {"H", "source", "block_seed", "lane", "construction_seed", "counts",
     "max_iter", "damping_alpha", "fake_runner", "field"}
)

CLAIM_BOUNDARY: tuple[str, ...] = (
    "bounded diagnostic statements about the iteration cap's contribution on "
    "empirical-count development samples with oracle-L1 conditioning only",
    "success metric is exact_l2 only; syndrome_ok/wrong_codeword reported separately "
    "and wrong codewords are NEVER counted as exact recoveries",
    "diagnostic rescues are NOT Lane B/C route successes and do not alter the V39 "
    "terminal state or any historical B/C conclusion",
    "V40_PROBE_CONFIRM_ALLOWED authorizes nothing by itself; it only marks that ONE "
    "future fresh-block confirmation may be proposed in a NEW OpenSpec change",
    "forbidden regardless of outcome: FER, asymptotic threshold, SKR, security, formal "
    "qualification, promotion, real-frame behavior, Lane C superiority, Lane B superiority, "
    "or any statement that V39 gates would now pass",
)

STATISTICS_NOTE = (
    "Descriptive only; sample is tiny and clustered (12 Phase-A/B calls on 3 unique "
    "blocks x 2 lanes; 6 probe calls on 3 new blocks x 2 lanes). Rescue proportions "
    "are reported with n and raw counts; Wilson intervals, where printed, are naive "
    "and uncorrected for block/lane clustering; no significance testing is performed."
)


class IntegrityFailure(Exception):
    """Raised when a frozen integrity check fails (check id + message)."""

    def __init__(self, check_id: str, message: str) -> None:
        super().__init__(f"[{check_id}] {message}")
        self.check_id = check_id
        self.message = message


# ---------------------------------------------------------------------------
# Instance extraction + reference guards (J1/J2)
# ---------------------------------------------------------------------------


def extract_instances(paired_path: Path | str = PAIRED_AUTHORITY_PATH) -> list[dict[str, Any]]:
    """Extract NEITHER_EXACT pairs in file order (lane_c then lane_b) and freeze-check.

    Raises IntegrityFailure("J1") on any membership/order/value drift from
    FROZEN_INSTANCES and ("J2") if any V39 reference residual is <= 0.
    """
    with Path(paired_path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise IntegrityFailure("J1", f"paired authority is not a list: {paired_path}")
    neither = [row for row in data if row.get("discordance_label") == "NEITHER_EXACT"]
    if len(neither) != 6:
        raise IntegrityFailure("J1", f"expected exactly 6 NEITHER_EXACT pairs, got {len(neither)}")
    extracted: list[dict[str, Any]] = []
    for pair_no, row in enumerate(neither, start=1):
        for lane_key, lane_name in (("c", "lane_c"), ("b", "lane_b")):
            ordinal = int(row["construction_seed_ordinal"])
            source = row["source"]
            construction_seed = CONSTRUCTION_SEEDS[lane_name][source][ordinal - 1]
            if row[f"{lane_key}_matrix_id"] != f"{lane_name}_{source}_s{construction_seed}":
                raise IntegrityFailure(
                    "J1",
                    f"pair {pair_no}: matrix_id {row[f'{lane_key}_matrix_id']!r} does not match "
                    f"registry seed {construction_seed} for {lane_name}/{source} ordinal {ordinal}",
                )
            extracted.append(
                {
                    "pair_no": pair_no,
                    "lane": lane_name,
                    "source": source,
                    "construction_seed_ordinal": ordinal,
                    "block_seed": row["block_seed"],
                    "construction_seed": construction_seed,
                    "matrix_id": row[f"{lane_key}_matrix_id"],
                    "v39_reference_errors_initial": row["errors_initial"],
                    "v39_reference_errors_final": row[f"{lane_key}_errors_final"],
                    "v39_reference_exact_l2": row[f"{lane_key}_exact_l2"],
                }
            )
    if len(extracted) != len(FROZEN_INSTANCES):
        raise IntegrityFailure("J1", f"extracted {len(extracted)} instances, expected 12")
    for got, want in zip(extracted, FROZEN_INSTANCES):
        for key, want_value in want.items():
            if key == "idx":
                continue  # positional label attached below once order/values verified
            got_value = got.get(key)
            if got_value != want_value:
                raise IntegrityFailure(
                    "J1",
                    f"instance drift at {want['idx']} field {key}: expected {want_value!r}, got {got_value!r}",
                )
    for pos, item in enumerate(extracted):
        item["idx"] = FROZEN_INSTANCES[pos]["idx"]
    finals = [inst["v39_reference_errors_final"] for inst in extracted]
    if min(finals) <= 0:
        raise IntegrityFailure("J2", f"V39 reference residual <= 0 present: min={min(finals)}")
    return extracted


# ---------------------------------------------------------------------------
# Representative-ordinal recomputation (J3)
# ---------------------------------------------------------------------------


def recompute_representative_ordinals(summary_path: Path | str = SUMMARY_AUTHORITY_PATH) -> dict[str, int]:
    """Argmax over by_construction_seed_ordinal exact_count (ties -> lowest ordinal)."""
    with Path(summary_path).open("r", encoding="utf-8") as handle:
        doc = json.load(handle)
    aggregates = doc.get("aggregates") or {}
    result: dict[str, int] = {}
    for lane in LANE_ORDER:
        by_ordinal = (aggregates.get(lane) or {}).get("by_construction_seed_ordinal") or {}
        counts = sorted((int(o), int(stats["exact_count"])) for o, stats in by_ordinal.items())
        if not counts:
            raise IntegrityFailure("J3", f"missing by_construction_seed_ordinal aggregates for {lane}")
        best = max(counts, key=lambda item: (item[1], -item[0]))
        result[lane] = best[0]
    return result


def verify_representative_ordinals(summary_path: Path | str = SUMMARY_AUTHORITY_PATH) -> dict[str, int]:
    recomputed = recompute_representative_ordinals(summary_path)
    if recomputed != REPRESENTATIVE_ORDINALS:
        raise IntegrityFailure(
            "J3",
            f"representative ordinals {recomputed} != frozen constants {REPRESENTATIVE_ORDINALS}",
        )
    return recomputed


# ---------------------------------------------------------------------------
# Probe-seed registry validation (J4)
# ---------------------------------------------------------------------------


def validate_probe_seeds(seeds: Optional[dict[str, int]] = None) -> tuple[bool, str]:
    """Exact one-per-source shape, no duplicates, mechanical disjointness vs forbidden union."""
    reg = PROBE_BLOCK_SEEDS if seeds is None else seeds
    if set(reg.keys()) != set(SOURCE_ORDER):
        return False, f"registry sources must be exactly {SOURCE_ORDER}"
    values = list(reg.values())
    if len(values) != len(SOURCE_ORDER) or len(set(values)) != len(values):
        return False, f"probe seeds must be one unique seed per source, got {values}"
    overlap = set(values) & FORBIDDEN_BLOCK_SEEDS
    if overlap:
        return False, f"probe seeds overlap V36_A3/V39-used seeds: {sorted(overlap)}"
    return True, "PROBE_SEED_REGISTRY_OK"


# ---------------------------------------------------------------------------
# Structural reconstruction (decoder-free; strict match vs committed metrics)
# ---------------------------------------------------------------------------

DEFAULT_CONSTRUCTORS: dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]] = {
    "lane_b": construct_lane_b_prototype,
    "lane_c": construct_lane_c_prototype,
}


def _reject_forbidden_npz(path: Path | str) -> None:
    name = Path(path).name
    suffix = Path(path).suffix.lower()
    if name == FORBIDDEN_WINNER_NPZ_NAME or suffix == ".npz":
        raise IntegrityFailure(
            "J9",
            f"structural authority must be the committed run_01 JSON, got NPZ path: {path}",
        )


def matrix_usage_rows() -> list[dict[str, Any]]:
    """The frozen 12 matrix usage rows deduplicating to 10 unique ids.

    Six 1M matrices serve Phases A/B (2 lanes x 3 ordinals; each decodes six
    instances) and six representative matrices serve the probe.
    """
    rows: list[dict[str, Any]] = []
    for lane in LANE_ORDER:
        for ordinal in (1, 2, 3):
            seed = CONSTRUCTION_SEEDS[lane]["1M"][ordinal - 1]
            rows.append(
                {
                    "usage_row": len(rows) + 1,
                    "usage": "phase_ab",
                    "lane": lane,
                    "source": "1M",
                    "construction_seed_ordinal": ordinal,
                    "construction_seed": seed,
                    "matrix_id": f"{lane}_1M_s{seed}",
                }
            )
    for spec in PROBE_WORKLOAD:
        rows.append(
            {
                "usage_row": len(rows) + 1,
                "usage": "probe",
                "lane": spec["lane"],
                "source": spec["source"],
                "construction_seed_ordinal": REPRESENTATIVE_ORDINALS[spec["lane"]],
                "construction_seed": _rep_seed(spec["lane"], spec["source"]),
                "matrix_id": f"{spec['lane']}_{spec['source']}_s{_rep_seed(spec['lane'], spec['source'])}",
            }
        )
    return rows


def reconstruct_v40_matrices(
    reference_metrics_path: Path | str = STRUCTURAL_AUTHORITY_PATH,
    field: Optional[GF2mField] = None,
    constructors: Optional[dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]]] = None,
    only: Optional[frozenset[tuple[str, str, int]]] = None,
) -> dict[tuple[str, str, int], tuple[np.ndarray, dict[str, Any]]]:
    """Rebuild the required matrices via the accepted V38 constructors and strictly compare.

    The committed 27-record structural JSON is the metric authority (including
    Lane C ``position_permutations``). The ignored NPZ archive is never an
    input (J9); no NPZ is ever written. Decoder-free.
    """
    _reject_forbidden_npz(reference_metrics_path)
    reference_by_id = _load_v38r1_reference_metrics(reference_metrics_path)
    field = field or GF2mField.create(DIMENSION)
    if field.primitive_polynomial != POLYNOMIAL:
        raise IntegrityFailure(
            "J10", f"field polynomial mismatch: expected {POLYNOMIAL}, got {field.primitive_polynomial}"
        )
    ctor_map = constructors or DEFAULT_CONSTRUCTORS
    keys = list(RECONSTRUCTION_KEYS) if only is None else sorted(only)
    matrices: dict[tuple[str, str, int], tuple[np.ndarray, dict[str, Any]]] = {}
    for lane, source, seed in keys:
        matrix_id = f"{lane}_{source}_s{seed}"
        expected = reference_by_id.get(matrix_id)
        if expected is None:
            raise IntegrityFailure("RECONSTRUCTION_MISMATCH", f"missing committed metrics for {matrix_id}")
        if expected.get("lane") != lane or expected.get("source") != source:
            raise IntegrityFailure("RECONSTRUCTION_MISMATCH", f"identity mismatch in committed metrics: {matrix_id}")
        matrix, metrics = ctor_map[lane](source=source, seed=seed, field=field)
        try:
            _check_v38r1_metric_match(expected, metrics, matrix_id)
        except ValueError as exc:
            raise IntegrityFailure("RECONSTRUCTION_MISMATCH", str(exc)) from exc
        matrices[(lane, source, seed)] = (matrix, metrics)
    if not matrices:
        raise IntegrityFailure("RECONSTRUCTION_MISMATCH", "no matrices reconstructed")
    return matrices


# ---------------------------------------------------------------------------
# Posterior-binding preflight (P-BIND sentinels; decoder-free, write-free)
# ---------------------------------------------------------------------------


def posterior_binding_preflight(
    counts_by_source: dict[str, np.ndarray],
    probes: Optional[dict[str, int]] = None,
) -> dict[str, dict[str, Any]]:
    """Verify complete-Bob binding on the three new probe blocks.

    Fixed sentinels per probe source (design Section 16): bob_gt_31,
    captured_equals_bob, corrected_equals_direct,
    corrected_differs_u2bob_arraywise, corrected_differs_u2bob_maxabs (>1e-6),
    argmax_divergence. Zero production decoder calls; writes nothing.
    """
    probes = PROBE_BLOCK_SEEDS if probes is None else probes
    results: dict[str, dict[str, Any]] = {}
    real_posterior = get_conditional_posterior_l2
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
                "POSTERIOR_BINDING",
                f"posterior-binding sentinel failed on probe {source}/{probe_seed}: {failed}; "
                "probe replacement requires a plan-review change, never post-execution",
            )
        results[source] = checks
    return results


# ---------------------------------------------------------------------------
# Residual-improvement metric (design Section 6, R9)
# ---------------------------------------------------------------------------


def residual_improvement(
    phase_records: list[dict[str, Any]],
    instances: list[dict[str, Any]],
    label: str = "IMP",
) -> dict[str, Any]:
    """IMP_P over the matched still-non-exact subset S_P with matched denominators.

    Returns imp plus both medians (matched-subset phase median, matched-subset
    V39 median) and the pooled all-12 V39 median as descriptive context.
    Empty S_P -> imp := 1.0; zero denominator median raises J2.
    """
    if len(phase_records) != len(instances):
        raise IntegrityFailure("J7", f"{label}: {len(phase_records)} records vs {len(instances)} instances")
    pooled_refs = [int(inst["v39_reference_errors_final"]) for inst in instances]
    subset_phase: list[int] = []
    subset_v39: list[int] = []
    for rec, inst in zip(phase_records, instances):
        if rec["exact_l2"]:
            continue
        ref = int(inst["v39_reference_errors_final"])
        subset_phase.append(int(rec["errors_final"]))
        subset_v39.append(ref)
    pooled_median = float(np.median(pooled_refs))
    if not subset_phase:
        return {
            "label": label,
            "imp": 1.0,
            "matched_subset_size": 0,
            "median_errors_final_subset": None,
            "median_v39_residual_subset": None,
            "pooled_v39_median_all12": pooled_median,
        }
    denom = float(np.median(subset_v39))
    if denom <= 0:
        raise IntegrityFailure("J2", f"{label}: zero matched-denominator median (subset={subset_v39})")
    numer = float(np.median(subset_phase))
    return {
        "label": label,
        "imp": float(1.0 - numer / denom),
        "matched_subset_size": len(subset_phase),
        "median_errors_final_subset": numer,
        "median_v39_residual_subset": denom,
        "pooled_v39_median_all12": pooled_median,
    }


# ---------------------------------------------------------------------------
# Signals, gating, probe judgment, terminal machine (design Section 13)
# ---------------------------------------------------------------------------


def phase_a_signal(w_a: int, r_a: int, imp_a: float) -> Optional[str]:
    """Routing signal emitted by Phase A (None under rule 1 / rule 4 outcomes)."""
    if w_a > 0:
        return None
    if r_a >= 4:
        return SIGNAL_CAP_MATERIAL
    if r_a >= 2:
        return SIGNAL_WEAK_RESIDUAL
    if imp_a >= 0.25:
        return SIGNAL_RESIDUAL_ONLY_NO_EXACT_RESCUE
    return None


def phase_b_trigger(w_a: int, r_a: int, imp_a: float) -> bool:
    """Frozen literal R10 trigger: W_A == 0 AND R_A <= 1 AND IMP_A >= 0.25."""
    return w_a == 0 and r_a <= 1 and imp_a >= 0.25


def require_phase_b_trigger(w_a: int, r_a: int, imp_a: float) -> None:
    if not phase_b_trigger(w_a, r_a, imp_a):
        raise IntegrityFailure(
            "J12",
            f"Phase-B gating violation: trigger requires W_A==0, R_A<=1 (of 12), IMP_A>=0.25; "
            f"got W_A={w_a}, R_A={r_a}, IMP_A={imp_a!r}",
        )


def resolve_probe_setting(cap_material: bool, damping_value: bool) -> Optional[tuple[int, float]]:
    """Exactly one trigger may fire; returns the unique fixed probe setting."""
    if cap_material and damping_value:
        raise IntegrityFailure("J12", "ambiguous probe setting: CAP_MATERIAL and DAMPING_VALUE both fired")
    if cap_material:
        return PROBE_SETTINGS_BY_TRIGGER[SIGNAL_CAP_MATERIAL]
    if damping_value:
        return PROBE_SETTINGS_BY_TRIGGER[SIGNAL_DAMPING_VALUE]
    return None


def judge_probe(
    exact_total: int,
    exact_lane_c: int,
    exact_lane_b: int,
    wrong_total: int,
) -> tuple[str, Optional[str]]:
    """Rule 6: exhaustive and mutually exclusive probe judgments."""
    if wrong_total > 0:
        return TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION, None
    if exact_total <= 2:
        return TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION, None
    if exact_total == 3:
        return TERMINAL_PROBE_INCONCLUSIVE, None
    if exact_lane_c < 2 or exact_lane_b < 2:
        return TERMINAL_PROBE_INCONCLUSIVE, None
    return TERMINAL_PROBE_CONFIRM_ALLOWED, None


def determine_v40_terminal(
    *,
    integrity_ok: bool,
    w_a: int,
    r_a: int,
    imp_a: float,
    phase_b_ran: bool = False,
    w_b: int = 0,
    r_b_new: int = 0,
    probe_ran: bool = False,
    probe_aggregates: Optional[dict[str, int]] = None,
) -> tuple[str, Optional[str], list[str]]:
    """Total/disjoint first-match-wins machine over design Section 13 rules 0-6.

    Returns (terminal_state, terminal_reason, routing_trace). Unreachable
    combinations raise J12 rather than silently mapping anywhere: Phase B may
    have run only when the unique R10 trigger holds (W_A == 0, R_A <= 1 of 12,
    IMP_A >= 0.25), and the probe may have run only on the CAP_MATERIAL route
    or a legal DAMPING_VALUE route; illegal Phase B/probe combinations are
    never absorbed by a normal terminal.
    """
    trace: list[str] = []
    if not integrity_ok:
        trace.append("rule_0:integrity_first")
        return TERMINAL_EVIDENCE_INVALID, None, trace

    # J12 phase-consistency guards: illegal combinations precede any routing.
    if phase_b_ran and not phase_b_trigger(w_a, r_a, imp_a):
        raise IntegrityFailure(
            "J12",
            f"Phase B ran but the unique trigger is unsatisfied "
            f"(requires W_A==0, R_A<=1 (out of 12), IMP_A>=0.25); "
            f"got W_A={w_a}, R_A={r_a}, IMP_A={imp_a!r}",
        )
    cap_material_route = w_a == 0 and r_a >= 4
    damping_value_route = (
        phase_b_trigger(w_a, r_a, imp_a) and phase_b_ran and w_b == 0 and r_b_new >= 3
    )
    if probe_ran and not (cap_material_route or damping_value_route):
        raise IntegrityFailure(
            "J12",
            "probe ran but neither the CAP_MATERIAL route nor a legal "
            "DAMPING_VALUE route (W_B==0, R_B_new>=3 after a triggered Phase B) is active",
        )
    if w_a > 0:
        trace.append(f"rule_1:W_A>0->{TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION}")
        return TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION, REASON_WRONG_CODEWORD_PHASE_A, trace
    if r_a >= 4:
        trace.append(f"rule_2:{SIGNAL_CAP_MATERIAL}")
        probe_due = True
    elif r_a >= 2:
        trace.append(f"rule_3:{SIGNAL_WEAK_RESIDUAL}->{TERMINAL_GO_STRUCTURE}")
        return TERMINAL_GO_STRUCTURE, REASON_WEAK_EXACT_RESCUE, trace
    elif imp_a < 0.25:
        trace.append(f"rule_4:no_material_cap_effect->{TERMINAL_GO_STRUCTURE}")
        return TERMINAL_GO_STRUCTURE, REASON_NO_MATERIAL_CAP_EFFECT, trace
    else:
        trace.append(f"rule_5:{SIGNAL_RESIDUAL_ONLY_NO_EXACT_RESCUE}")
        if not phase_b_ran:
            raise IntegrityFailure("J12", "rule 5 selected but Phase B did not run")
        if w_b > 0:
            trace.append(f"rule_5a:W_B>0->{TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION}")
            return TERMINAL_STOP_BC_PARAMETER_OPTIMIZATION, REASON_WRONG_CODEWORD_PHASE_B, trace
        if r_b_new >= 3:
            trace.append(f"rule_5b:{SIGNAL_DAMPING_VALUE}")
            probe_due = True
        else:
            trace.append(f"rule_5c:{SIGNAL_DAMPING_NO_VALUE}->{TERMINAL_GO_STRUCTURE}")
            return TERMINAL_GO_STRUCTURE, REASON_DAMPING_NO_VALUE, trace
    if not probe_ran or probe_aggregates is None:
        raise IntegrityFailure("J12", "probe eligible but did not run")
    terminal, reason = judge_probe(
        exact_total=int(probe_aggregates["exact_total"]),
        exact_lane_c=int(probe_aggregates["exact_lane_c"]),
        exact_lane_b=int(probe_aggregates["exact_lane_b"]),
        wrong_total=int(probe_aggregates.get("wrong_lane_c", 0)) + int(probe_aggregates.get("wrong_lane_b", 0)),
    )
    trace.append(f"rule_6:probe->{terminal}")
    return terminal, reason, trace


# ---------------------------------------------------------------------------
# Budget accounting (J5)
# ---------------------------------------------------------------------------


class CallAccounting:
    """Hard-capped started/completed actuals per phase."""

    def __init__(self, caps: Optional[dict[str, int]] = None, hard_cap: int = HARD_CALL_CAP) -> None:
        self.caps = dict(BUDGET_CAPS if caps is None else caps)
        self.hard_cap = int(hard_cap)
        self.started: dict[str, int] = {phase: 0 for phase in self.caps}
        self.completed: dict[str, int] = {phase: 0 for phase in self.caps}

    @property
    def started_total(self) -> int:
        return sum(self.started.values())

    @property
    def completed_total(self) -> int:
        return sum(self.completed.values())

    def register_start(self, phase: str) -> None:
        if phase not in self.caps:
            raise IntegrityFailure("J5", f"unknown phase {phase!r}")
        if self.started_total >= self.hard_cap:
            raise IntegrityFailure("J5", f"hard call cap {self.hard_cap} would be exceeded")
        self.started[phase] += 1

    def register_complete(self, phase: str, record: dict[str, Any]) -> None:
        if self.started[phase] <= self.completed[phase]:
            raise IntegrityFailure("J5", f"completed without started in phase {phase}")
        self.completed[phase] += 1

    def validate_executed(self, executed_phases: Iterable[str]) -> list[tuple[str, str]]:
        failures: list[tuple[str, str]] = []
        executed = set(executed_phases)
        for phase, cap in self.caps.items():
            if phase in executed:
                if self.completed[phase] != cap or self.started[phase] != cap:
                    failures.append(("J5", f"{phase}: planned {cap}, started {self.started[phase]}, completed {self.completed[phase]}"))
            else:
                if self.started[phase] != 0 or self.completed[phase] != 0:
                    failures.append(("J5", f"skipped {phase} consumed calls (started {self.started[phase]}, completed {self.completed[phase]})"))
        if self.completed_total > self.hard_cap:
            failures.append(("J5", f"total completed {self.completed_total} exceeds hard cap {self.hard_cap}"))
        return failures


# ---------------------------------------------------------------------------
# Record building, schema, and post-evaluation checks (J6/J7/J10)
# ---------------------------------------------------------------------------


def validate_decoder_contract(call_params: dict[str, Any], expected_setting: tuple[int, float]) -> None:
    """Exact call-path contract: fixed keys, frozen settings, no warm start (J10)."""
    extra = set(call_params.keys()) - ALLOWED_CALL_KEYS
    if extra:
        raise IntegrityFailure("J10", f"unexpected call parameters (warm-start/third-setting class): {sorted(extra)}")
    if call_params["max_iter"] != expected_setting[0] or call_params["damping_alpha"] != expected_setting[1]:
        raise IntegrityFailure(
            "J10",
            f"decoder settings {call_params['max_iter']}/{call_params['damping_alpha']} != frozen {expected_setting}",
        )


def build_record(
    phase: str,
    spec: dict[str, Any],
    raw: dict[str, Any],
    setting: tuple[int, float],
    v39_reference: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """Normalize one evaluator result into the diagnostic record schema."""
    exact = bool(raw["exact_l2"])
    syndrome_ok = bool(raw["syndrome_ok"])
    rescued: Optional[bool] = None
    ref_final: Optional[int] = None
    ref_exact: Optional[bool] = None
    if v39_reference is not None:
        ref_final = int(v39_reference["v39_reference_errors_final"])
        ref_exact = bool(v39_reference["v39_reference_exact_l2"])
        rescued = bool((not ref_exact) and exact)
    record = {
        "phase": phase,
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
        "v39_reference_errors_final": ref_final,
        "v39_reference_exact_l2": ref_exact,
        "rescued_vs_v39": rescued,
    }
    return {key: record[key] for key in RECORD_FIELDS}


def validate_record_schema(record: dict[str, Any]) -> tuple[bool, str]:
    """Record schema completeness incl. derived wrong_codeword (J6)."""
    for key in RECORD_FIELDS:
        if key not in record:
            return False, f"missing field {key}"
    if record["phase"] not in (PHASE_A, PHASE_B, PROBE):
        return False, f"invalid phase {record['phase']!r}"
    for key in ("exact_l2", "syndrome_ok", "wrong_codeword"):
        if not isinstance(record[key], bool):
            return False, f"field {key} must be bool"
    for key in ("errors_initial", "errors_final", "iterations", "max_iter", "block_seed", "construction_seed", "construction_seed_ordinal"):
        if not isinstance(record[key], int) or isinstance(record[key], bool):
            return False, f"field {key} must be int"
    expected_wrong = record["syndrome_ok"] and not record["exact_l2"]
    if record["wrong_codeword"] != expected_wrong:
        return False, "wrong_codeword must equal syndrome_ok and not exact_l2"
    if record["rescued_vs_v39"] is not None and not isinstance(record["rescued_vs_v39"], bool):
        return False, "rescued_vs_v39 must be bool or null"
    if record["phase"] == PROBE:
        if record["v39_reference_errors_final"] is not None or record["v39_reference_exact_l2"] is not None or record["rescued_vs_v39"] is not None:
            return False, "probe records must carry null V39 references and null rescued_vs_v39"
    else:
        if not isinstance(record["v39_reference_errors_final"], int):
            return False, "phase A/B records require integer v39_reference_errors_final"
        if not isinstance(record["v39_reference_exact_l2"], bool):
            return False, "phase A/B records require bool v39_reference_exact_l2"
        if not isinstance(record["rescued_vs_v39"], bool):
            return False, "phase A/B records require bool rescued_vs_v39"
    return True, "SCHEMA_OK"


def validate_post_evaluation(
    all_records: list[dict[str, Any]],
    instances: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Schema (J6) and errors_initial equality (J7) over collected records."""
    failures: list[tuple[str, str]] = []
    for rec in all_records:
        ok, msg = validate_record_schema(rec)
        if not ok:
            failures.append(("J6", f"record {rec.get('phase')}/{rec.get('matrix_id')}/{rec.get('block_seed')}: {msg}"))

    by_phase: dict[str, list[dict[str, Any]]] = {phase: [] for phase in EXECUTED_PHASE_ORDER}
    for rec in all_records:
        by_phase[rec["phase"]].append(rec)

    # Cross-lane same-block equality within each phase (J7).
    for phase, recs in by_phase.items():
        by_block: dict[int, set[int]] = {}
        for rec in recs:
            by_block.setdefault(rec["block_seed"], set()).add(rec["errors_initial"])
        for block_seed, initials in by_block.items():
            if len(initials) != 1:
                failures.append(("J7", f"{phase} block {block_seed}: cross-lane errors_initial mismatch {sorted(initials)}"))

    # Phase A/B equality vs the V39 references (J7).
    for phase in (PHASE_A, PHASE_B):
        recs = by_phase[phase]
        if len(recs) != len(instances):
            continue  # accounting (J5) owns count mismatches
        for rec, inst in zip(recs, instances):
            if (rec["lane"], rec["block_seed"]) != (inst["lane"], inst["block_seed"]):
                failures.append(("J7", f"{phase}: record order drift at {inst['idx']}"))
                continue
            if rec["errors_initial"] != inst["v39_reference_errors_initial"]:
                failures.append(
                    ("J7", f"{phase} {inst['idx']}: errors_initial {rec['errors_initial']} != V39 reference {inst['v39_reference_errors_initial']}")
                )
    return failures


def phase_counts(records: list[dict[str, Any]]) -> tuple[int, int]:
    """Return (wrong_codeword_count, rescued_count) for a phase-A/B record list."""
    wrong = sum(1 for r in records if r["wrong_codeword"])
    rescued = sum(1 for r in records if r["rescued_vs_v39"])
    return wrong, rescued


# ---------------------------------------------------------------------------
# Environment loaders and git binding (accepted V39 pattern, v40 scope)
# ---------------------------------------------------------------------------


def describe_v25_counts_provenance() -> dict[str, Any]:
    from comparison_bench.formal_ir import v35_algorithm_development as v35

    path = Path(v35.__file__).resolve().parents[4] / V25_COUNTS_RELATIVE_PATH
    return {
        "path": str(path),
        "loader": "comparison_bench.formal_ir.v35_algorithm_development.load_v25_channel_counts",
        "role": "source-specific V25 TRAIN empirical counts (read-only)",
        "exists": path.is_file(),
    }


def describe_v39_input_identity() -> dict[str, Any]:
    return {
        "paired_authority": str(PAIRED_AUTHORITY_PATH),
        "summary_authority": str(SUMMARY_AUTHORITY_PATH),
        "predecessor_cycle": "V39P0",
        "predecessor_plan_sha": PREDECESSOR_PLAN_SHA,
        "predecessor_execution_sha": PREDECESSOR_EXECUTION_SHA,
        "predecessor_result_sha": PREDECESSOR_RESULT_SHA,
        "predecessor_terminal_state": "V39_NO_ROBUST_ROUTE_SIGNAL",
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
    """Refuse execution when any scoped tracked file differs from HEAD (J11)."""
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "HEAD", "--quiet", "--", *relative_paths],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise IntegrityFailure(
            "J11_TRACKED_DIRTY",
            f"scoped tracked files differ from HEAD; commit or revert before "
            f"execution: {list(relative_paths)}",
        )


def verify_execution_sha_binding(repo_root: Path, authorized_target_sha: str) -> dict[str, str]:
    """Exact-equality binding of HEAD AND origin branch to the authorized SHA (J11)."""
    head = git_rev_parse(repo_root, "HEAD")
    branch = git_rev_parse(repo_root, BRANCH_REF)
    if head != authorized_target_sha or branch != authorized_target_sha:
        raise IntegrityFailure(
            "J11_SHA_BINDING_MISMATCH",
            f"authorized_target_sha={authorized_target_sha} but HEAD={head} and {BRANCH_REF}={branch}",
        )
    return {"HEAD": head, BRANCH_REF: branch}


# ---------------------------------------------------------------------------
# Guarded diagnostic runner
# ---------------------------------------------------------------------------


def _run_instance_calls(
    phase: str,
    specs: list[dict[str, Any]],
    matrices: dict[tuple[str, str, int], tuple[np.ndarray, dict[str, Any]]],
    counts_by_source: dict[str, np.ndarray],
    field: GF2mField,
    fake_runner: bool,
    setting: tuple[int, float],
    accounting: CallAccounting,
    sink: list[dict[str, Any]],
) -> None:
    """Append records progressively so partial evidence survives a mid-run crash."""
    for spec in specs:
        key = (spec["lane"], spec["source"], spec["construction_seed"])
        matrix, _ = matrices[key]
        accounting.register_start(phase)
        call_params = {
            "H": matrix,
            "source": spec["source"],
            "block_seed": spec["block_seed"],
            "lane": spec["lane"],
            "construction_seed": spec["construction_seed"],
            "counts": counts_by_source[spec["source"]],
            "max_iter": setting[0],
            "damping_alpha": setting[1],
            "fake_runner": fake_runner,
            "field": field,
        }
        validate_decoder_contract(call_params, PHASE_SETTINGS[phase])
        raw = evaluate_single_block(**call_params)
        record = build_record(phase, spec, raw, setting, spec)
        accounting.register_complete(phase, record)
        sink.append(record)


def _run_probe_calls(
    setting: tuple[int, float],
    matrices: dict[tuple[str, str, int], tuple[np.ndarray, dict[str, Any]]],
    counts_by_source: dict[str, np.ndarray],
    field: GF2mField,
    fake_runner: bool,
    accounting: CallAccounting,
    sink: list[dict[str, Any]],
) -> None:
    for spec in PROBE_WORKLOAD:
        seed = _rep_seed(spec["lane"], spec["source"])
        key = (spec["lane"], spec["source"], seed)
        matrix, _ = matrices[key]
        probe_spec = {
            "lane": spec["lane"],
            "source": spec["source"],
            "block_seed": spec["block_seed"],
            "construction_seed": seed,
            "construction_seed_ordinal": REPRESENTATIVE_ORDINALS[spec["lane"]],
        }
        accounting.register_start(PROBE)
        call_params = {
            "H": matrix,
            "source": spec["source"],
            "block_seed": spec["block_seed"],
            "lane": spec["lane"],
            "construction_seed": seed,
            "counts": counts_by_source[spec["source"]],
            "max_iter": setting[0],
            "damping_alpha": setting[1],
            "fake_runner": fake_runner,
            "field": field,
        }
        validate_decoder_contract(call_params, setting)
        raw = evaluate_single_block(**call_params)
        record = build_record(PROBE, probe_spec, raw, setting, None)
        accounting.register_complete(PROBE, record)
        sink.append(record)


def probe_aggregates_from_records(probe_records: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "exact_total": sum(1 for r in probe_records if r["exact_l2"]),
        "exact_lane_c": sum(1 for r in probe_records if r["lane"] == "lane_c" and r["exact_l2"]),
        "exact_lane_b": sum(1 for r in probe_records if r["lane"] == "lane_b" and r["exact_l2"]),
        "wrong_lane_c": sum(1 for r in probe_records if r["lane"] == "lane_c" and r["wrong_codeword"]),
        "wrong_lane_b": sum(1 for r in probe_records if r["lane"] == "lane_b" and r["wrong_codeword"]),
    }


def build_v40_summary(
    lifecycle_state: str,
    fake_runner: bool,
    authorized_target_sha: Optional[str],
    sha_binding: Optional[dict[str, str]],
    counts_provenance: dict[str, Any],
    accounting: CallAccounting,
    executed_phases: list[str],
    signals: dict[str, Any],
    improvements: dict[str, Any],
    rescue_wrong_counts: dict[str, Any],
    probe_results: Optional[dict[str, int]],
    routing_trace: list[str],
    integrity_failures: Optional[list[tuple[str, str]]],
    terminal_state: str,
    terminal_reason: Optional[str],
    structural_rows_count: int,
) -> dict[str, Any]:
    invalid = terminal_state == TERMINAL_EVIDENCE_INVALID
    return {
        "cycle_id": CYCLE_ID,
        "change_id": CHANGE_ID,
        "accepted_plan_sha": ACCEPTED_PLAN_SHA,
        "lifecycle_state": lifecycle_state,
        "execution_scope": "v40_decoder_only_max30_calls_exactly_once",
        "fake_runner": fake_runner,
        "provenance": {
            "authorized_target_sha": authorized_target_sha,
            "sha_binding": sha_binding,
            "structural_authority": str(STRUCTURAL_AUTHORITY_PATH),
            "structural_records_strict_match": structural_rows_count,
            "v39_input_identity": describe_v39_input_identity(),
        },
        "v25_counts_provenance": counts_provenance,
        "accounting": {
            "decoder_calls_planned": {"total": HARD_CALL_CAP, **BUDGET_CAPS},
            "decoder_calls_started": {"total": accounting.started_total, **accounting.started},
            "decoder_calls_completed": {"total": accounting.completed_total, **accounting.completed},
            "executed_phases": list(executed_phases),
            "structural_reconstruction_decoder_calls": 0,
            "preflight_decoder_calls": 0,
        },
        "npz_policy": {
            "forbidden_winner_npz_read": False,
            "any_npz_output_written": False,
            "v25_channel_counts_npz_read_only_allowed": True,
        },
        "signals": signals,
        "improvements": improvements,
        "rescue_and_wrong_counts": rescue_wrong_counts,
        "probe_results": probe_results,
        "routing_trace": routing_trace,
        "master_stop_rule": MASTER_STOP_RULE,
        "statistics_note": STATISTICS_NOTE,
        "claim_boundary": list(CLAIM_BOUNDARY),
        "integrity_failures": (
            [{"check": cid, "message": msg} for cid, msg in integrity_failures]
            if integrity_failures
            else []
        ),
        "terminal_state": terminal_state,
        "terminal_reason": terminal_reason,
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


def write_v40_outputs(
    output_root: Path | str,
    records: list[dict[str, Any]],
    summary: dict[str, Any],
) -> Path:
    """Write the fixed minimal evidence set (design D9); fail closed on non-empty root.

    The guarded runner pre-creates the (empty) root just before the decoder
    stage, so writing into an existing-but-empty root owned by this run is
    expected; any pre-existing NON-empty root is refused.
    """
    root = Path(output_root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"J8: refusing to overwrite non-empty output root: {root}")
    if not root.exists():
        root.mkdir(parents=True)

    def dump(name: str, payload: Any) -> None:
        with (root / name).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    dump("v40_diagnostic_records.json", records)
    write_records_csv(root / "v40_diagnostic_records.csv", records, list(RECORD_FIELDS))
    dump("v40_summary.json", summary)
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
    path = root / "v40_invalid_notice.json"
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
    partial_records_retained: bool = True,
) -> None:
    """Retain raw collected records byte-for-byte plus notice/summary; no aggregates.

    Never masks the original failure with writer problems.
    """
    try:
        if not root.exists():
            root.mkdir(parents=True)
        if records:
            with (root / "v40_diagnostic_records.json").open("w", encoding="utf-8") as handle:
                json.dump(records, handle, indent=2)
            write_records_csv(root / "v40_diagnostic_records.csv", records, list(RECORD_FIELDS))
        summary = build_v40_summary(
            lifecycle_state="DEVELOPMENT_RESULT_CANDIDATE",
            fake_runner=summary_ctx.get("fake_runner", False),
            authorized_target_sha=summary_ctx.get("authorized_target_sha"),
            sha_binding=summary_ctx.get("sha_binding"),
            counts_provenance=summary_ctx.get("counts_provenance", {}),
            accounting=accounting,
            executed_phases=summary_ctx.get("executed_phases", []),
            signals={},
            improvements={},
            rescue_wrong_counts={},
            probe_results=None,
            routing_trace=[],
            integrity_failures=failures,
            terminal_state=TERMINAL_EVIDENCE_INVALID,
            terminal_reason=None,
            structural_rows_count=int(summary_ctx.get("structural_rows_count", 0)),
        )
        with (root / "v40_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        write_invalid_notice(root, failures, partial_records_retained=partial_records_retained)
    except Exception:  # never mask the original failure with writer problems
        pass


def run_v40_diagnostic(
    execution_authorized: bool = False,
    authorized_target_sha: Optional[str] = None,
    fake_runner: bool = False,
    output_root: Optional[Path | str] = None,
    structural_authority_path: Optional[Path | str] = None,
    paired_authority_path: Optional[Path | str] = None,
    summary_authority_path: Optional[Path | str] = None,
    counts_by_source: Optional[dict[str, np.ndarray]] = None,
    field: Optional[GF2mField] = None,
    check_git: bool = True,
    check_scoped_dirty: bool = True,
    constructors: Optional[dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]]] = None,
    reconstruct_only: Optional[frozenset[tuple[str, str, int]]] = None,
) -> dict[str, Any]:
    """Guarded single-run orchestration; default-deny, fail-closed."""
    if not execution_authorized:
        raise PermissionError(
            "EXECUTE_NOT_AUTHORIZED: pass --execution-authorized bound to an "
            "explicit user EXECUTE_AUTH for scope v40_decoder_only_max30_calls_exactly_once"
        )

    root_arg = output_root if output_root is not None else OUTPUT_ROOT
    root = Path(root_arg)
    if root.exists():
        raise FileExistsError(f"J8: refusing to overwrite existing output root: {root}")

    field = field or GF2mField.create(DIMENSION)
    if field.primitive_polynomial != POLYNOMIAL:
        raise IntegrityFailure("J10", f"polynomial mismatch: {field.primitive_polynomial}")

    sha_binding: Optional[dict[str, str]] = None
    if check_git:
        if not authorized_target_sha:
            raise IntegrityFailure(
                "J11_SHA_BINDING_MISSING",
                "authorized_target_sha is required for the authorized run",
            )
        sha_binding = verify_execution_sha_binding(REPO_ROOT, authorized_target_sha)
    if check_scoped_dirty:
        # Execution-refusal class failure: raised before any evidence root exists.
        verify_scoped_clean(REPO_ROOT)

    # ---- preflight (decoder-free, nothing written yet) --------------------
    # Execution-refusal failures above raise without creating any root.
    # SCIENTIFIC preflight failures (J1-J4, matrix reconstruction, J9 counts,
    # posterior binding) are captured here and persisted as invalid evidence
    # in a formal additive root: planned fixed per protocol, started=0,
    # completed=0, zero evaluator calls, no performance aggregates. Stop; no
    # rerun.
    summary_ctx: dict[str, Any] = {
        "fake_runner": fake_runner,
        "authorized_target_sha": authorized_target_sha,
        "sha_binding": sha_binding,
        "counts_provenance": {},
        "structural_rows_count": 0,
        "executed_phases": [],
    }
    try:
        paired_path = Path(paired_authority_path) if paired_authority_path else PAIRED_AUTHORITY_PATH
        summary_path = Path(summary_authority_path) if summary_authority_path else SUMMARY_AUTHORITY_PATH
        instances = extract_instances(paired_path)  # J1/J2
        verify_representative_ordinals(summary_path)  # J3
        registry_ok, registry_msg = validate_probe_seeds()
        if not registry_ok:
            raise IntegrityFailure("J4", registry_msg)

        spath = Path(structural_authority_path) if structural_authority_path else STRUCTURAL_AUTHORITY_PATH
        matrices = reconstruct_v40_matrices(
            reference_metrics_path=spath,
            field=field,
            constructors=constructors,
            only=reconstruct_only,
        )
        summary_ctx["structural_rows_count"] = len(matrices)

        counts = counts_by_source if counts_by_source is not None else load_v25_channel_counts()
        for source in SOURCE_ORDER:
            if counts[source].shape != (1024, 1024):
                raise IntegrityFailure("J9", f"unexpected counts shape for {source}: {counts[source].shape}")
        counts_provenance = describe_v25_counts_provenance()
        summary_ctx["counts_provenance"] = counts_provenance

        posterior_binding_preflight(counts)  # raises IntegrityFailure on any sentinel failure
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

    # ---- decoder stage: occupy the additive root NOW ----------------------
    # From this point any crash — including KeyboardInterrupt or process kill —
    # leaves the root (plus retained raw partials) in place so a relaunch
    # fails closed on J8 instead of silently re-running.
    root.mkdir(parents=True)
    accounting = CallAccounting()
    records: list[dict[str, Any]] = []
    try:
        # Phase A always: exactly 12 calls in frozen order A01..A12.
        phase_a_specs = [dict(inst) for inst in instances]
        _run_instance_calls(
            PHASE_A, phase_a_specs, matrices, counts, field, fake_runner,
            PHASE_SETTINGS[PHASE_A], accounting, records,
        )
        summary_ctx["executed_phases"] = [PHASE_A]
        phase_a_records = list(records)
        w_a, r_a = phase_counts(phase_a_records)
        imp_a_report = residual_improvement(phase_a_records, instances, label="IMP_A")
        imp_a = imp_a_report["imp"]
        signal_a = phase_a_signal(w_a, r_a, imp_a)

        # Phase B: unique trigger is RESIDUAL_ONLY_NO_EXACT_RESCUE (R10).
        phase_b_ran = False
        w_b = 0
        r_b_new = 0
        imp_b_report: Optional[dict[str, Any]] = None
        damping_value = False
        if signal_a == SIGNAL_RESIDUAL_ONLY_NO_EXACT_RESCUE:
            require_phase_b_trigger(w_a, r_a, imp_a)  # J12 backstop
            phase_b_start = len(records)
            _run_instance_calls(
                PHASE_B, phase_a_specs, matrices, counts, field, fake_runner,
                PHASE_SETTINGS[PHASE_B], accounting, records,
            )
            summary_ctx["executed_phases"] = [PHASE_A, PHASE_B]
            phase_b_ran = True
            phase_b_records = records[phase_b_start:]
            w_b, _ = phase_counts(phase_b_records)
            r_b_new = sum(
                1 for rec_a, rec_b in zip(phase_a_records, phase_b_records)
                if rec_b["exact_l2"] and not rec_a["exact_l2"]
            )
            imp_b_report = residual_improvement(phase_b_records, instances, label="IMP_B")
            damping_value = w_b == 0 and r_b_new >= 3

        # Probe: exactly one trigger can fire (uniqueness asserted, J12).
        cap_material = signal_a == SIGNAL_CAP_MATERIAL
        probe_setting = resolve_probe_setting(cap_material, damping_value)
        probe_ran = False
        probe_results: Optional[dict[str, int]] = None
        if probe_setting is not None:
            probe_start = len(records)
            _run_probe_calls(
                probe_setting, matrices, counts, field, fake_runner, accounting, records,
            )
            summary_ctx["executed_phases"] = list(summary_ctx["executed_phases"]) + [PROBE]
            probe_ran = True
            probe_results = probe_aggregates_from_records(records[probe_start:])

        # ---- post-evaluation integrity ------------------------------------
        executed = list(summary_ctx["executed_phases"])
        failures = validate_post_evaluation(records, instances) + accounting.validate_executed(executed)
        if failures:
            _persist_invalid_evidence(root, records=records, accounting=accounting,
                                      summary_ctx=summary_ctx, failures=failures)
            return {
                "output_root": str(root),
                "terminal_state": TERMINAL_EVIDENCE_INVALID,
                "terminal_reason": None,
                "integrity_failures": failures,
            }

        try:
            terminal_state, terminal_reason, routing_trace = determine_v40_terminal(
                integrity_ok=True,
                w_a=w_a,
                r_a=r_a,
                imp_a=imp_a,
                phase_b_ran=phase_b_ran,
                w_b=w_b,
                r_b_new=r_b_new,
                probe_ran=probe_ran,
                probe_aggregates=probe_results,
            )
        except IntegrityFailure as exc:
            # Runner-layer consistency guard: a machine-detected J12 (illegal
            # Phase B/probe combination) terminates as invalid evidence with
            # the check id retained -- never absorbed by a normal terminal.
            _persist_invalid_evidence(root, records=records, accounting=accounting,
                                      summary_ctx=summary_ctx, failures=[(exc.check_id, exc.message)])
            return {
                "output_root": str(root),
                "terminal_state": TERMINAL_EVIDENCE_INVALID,
                "terminal_reason": None,
                "integrity_failures": [(exc.check_id, exc.message)],
            }

        improvements = {"IMP_A": imp_a_report}
        if imp_b_report is not None:
            improvements["IMP_B"] = imp_b_report
        rescue_wrong_counts = {
            "phase_a": {"wrong_codewords": w_a, "rescued_vs_v39": r_a},
            "phase_b": {"wrong_codewords": w_b, "new_exacts_vs_phase_a": r_b_new},
        }
        signals = {
            "A_signal": signal_a,
            "B_signal": (SIGNAL_DAMPING_VALUE if damping_value else SIGNAL_DAMPING_NO_VALUE) if phase_b_ran else None,
        }
        summary = build_v40_summary(
            lifecycle_state="DEVELOPMENT_RESULT_CANDIDATE",
            fake_runner=fake_runner,
            authorized_target_sha=authorized_target_sha,
            sha_binding=sha_binding,
            counts_provenance=counts_provenance,
            accounting=accounting,
            executed_phases=executed,
            signals=signals,
            improvements=improvements,
            rescue_wrong_counts=rescue_wrong_counts,
            probe_results=probe_results,
            routing_trace=routing_trace,
            integrity_failures=None,
            terminal_state=terminal_state,
            terminal_reason=terminal_reason,
            structural_rows_count=len(matrices),
        )
        write_v40_outputs(root, records, summary)
        return {
            "output_root": str(root),
            "terminal_state": terminal_state,
            "terminal_reason": terminal_reason,
            "routing_trace": routing_trace,
            "decoder_calls_completed": accounting.completed_total,
            "signals": signals,
            "probe_results": probe_results,
            "summary": summary,
        }
    except BaseException:
        _persist_invalid_evidence(root, records=records, accounting=accounting,
                                  summary_ctx=summary_ctx,
                                  failures=[("mid_run_failure", "raw partial records retained; no performance aggregate generated")])
        raise
