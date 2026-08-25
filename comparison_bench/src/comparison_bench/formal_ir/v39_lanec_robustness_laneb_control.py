"""V39P0 Lane C robustness with Lane B control: guarded runner and writer.

Implements the frozen V39P0 protocol (change
``formal-ir-v39-lanec-robustness-laneb-control``, accepted plan SHA
8efb626ba0eaa6b031abd934ed583739ba70065b):

- Lane C (main) and Lane B (control) over ALL nine pre-registered
  construction seeds each, deterministically reconstructed from the accepted
  V38R1 constructors and strictly compared against the committed V38P0
  27-record structural JSON.
- 15 NEW development blocks per the frozen registry, sampled from the same
  source-specific V25 TRAIN empirical counts with oracle-L1 conditioning and
  complete-Bob posterior binding.
- Same-block frozen V31 baseline recomputed exactly once per block.
- Exactly 105 real decoder calls (45 + 45 + 15), max_iter=30,
  damping_alpha=1.0, GF(32) polynomial 37; success = exact_l2 only.
- Frozen gates C1 / B1 / CB / BASE(per ordinal) and an exhaustive terminal
  machine with integrity-first precedence.

Lifecycle: IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED.
This module performs no execution on import and never reads the ignored
winner archive ``v38_winning_matrices.npz`` nor writes any NPZ.
"""

from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import numpy as np

from comparison_bench.formal_ir.v35_algorithm_development import (
    GF2mField,
    factorize_f03,
    get_conditional_posterior_l2,
    load_v31_qc_baseline_matrices,
    load_v25_channel_counts,
    sample_empirical_block,
)
from comparison_bench.formal_ir.v38_architecture_triage import (
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

CYCLE_ID = "V39P0"
CHANGE_ID = "formal-ir-v39-lanec-robustness-laneb-control"
ACCEPTED_PLAN_SHA = "8efb626ba0eaa6b031abd934ed583739ba70065b"
BRANCH_REF = "origin/formal-ir-mainline"

POLYNOMIAL = 37
DIMENSION = 32
BLOCK_LENGTH = 1024
MAX_ITER = 30
DAMPING_ALPHA = 1.0

SOURCE_ORDER: tuple[str, ...] = ("1M", "1p5M", "2M")
LANE_ORDER: tuple[str, ...] = ("lane_c", "lane_b")
BASELINE_LANE = "v31_baseline"

# Pre-registered construction seeds (frozen; ordinal = list position).
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

# NEW development block seeds (frozen; non-overlapping with V36/V38 seeds).
BLOCK_SEEDS: dict[str, list[int]] = {
    "1M": [390101, 390102, 390103, 390104, 390105],
    "1p5M": [390201, 390202, 390203, 390204, 390205],
    "2M": [390301, 390302, 390303, 390304, 390305],
}
PROBE_BLOCK_SEEDS: dict[str, int] = {"1M": 390101, "1p5M": 390201, "2M": 390301}
# Seeds already used by V36 A3 and reused by V38/V38R1; overlap is failure I3.
FORBIDDEN_BLOCK_SEEDS: frozenset[int] = frozenset(
    seed for seeds in V36_A3_BLOCK_SEEDS.values() for seed in seeds
)

EXPECTED_CALLS = {"lane_c": 45, "lane_b": 45, BASELINE_LANE: 15}
TOTAL_CALLS = 105

REPO_ROOT = Path(__file__).resolve().parents[4]
STRUCTURAL_AUTHORITY_PATH = (
    REPO_ROOT
    / "comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json"
)
OUTPUT_ROOT = (
    REPO_ROOT
    / "comparison_bench/outputs_comparison/formal_ir_methods/v39_lanec_robustness_laneb_control/run_01"
)
FORBIDDEN_WINNER_NPZ_NAME = "v38_winning_matrices.npz"

# Scoped tracked-dirty check: only these directly reused/scientific files must
# match HEAD before an authorized run. The rest of the worktree is not judged.
SCOPED_TRACKED_PATHS: tuple[str, ...] = (
    "comparison_bench/src/comparison_bench/formal_ir/v39_lanec_robustness_laneb_control.py",
    "scripts/execute_v39_development.py",
    "comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py",
    "comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py",
)

V25_COUNTS_RELATIVE_PATH = (
    "comparison_bench/outputs_comparison/nonbinary_diagnostics/"
    "nbldpc_v25_20260818/run_04/channel_counts.npz"
)
V31_PACKET_ID = "m1_16_n1024_n1024|QC-cyclic-projective"

# Gate thresholds (frozen).
C1_OVERALL_MIN = 36          # of 45
C1_SOURCE_MIN = 12           # of 15
C1_ORDINAL_MIN = 12          # of 15
C1_CELL_MIN = 4              # of 5, for every (source, construction_seed)
CB_EXACT_MARGIN = 5          # exact_count_C >= exact_count_B + CB_EXACT_MARGIN
CB_DISCORDANCE_MARGIN = 3    # d_CB - d_BC >= CB_DISCORDANCE_MARGIN
CB_PER_SOURCE_TRAIL_TOLERANCE = 1

TERMINAL_EVIDENCE_INVALID = "V39_EVIDENCE_INVALID"
TERMINAL_C_ROBUST_AND_ADVANTAGE = "V39_C_ROBUST_AND_ADVANTAGE"
TERMINAL_C_ROBUST_NO_COMPLETE_ADVANTAGE = "V39_C_ROBUST_NO_COMPLETE_ADVANTAGE"
TERMINAL_BOTH_ROUTES_ROBUST = "V39_BOTH_ROUTES_ROBUST"
TERMINAL_B_ONLY_ROBUST = "V39_B_ONLY_ROBUST"
TERMINAL_NO_ROBUST_ROUTE_SIGNAL = "V39_NO_ROBUST_ROUTE_SIGNAL"
ALL_TERMINALS = frozenset(
    {
        TERMINAL_EVIDENCE_INVALID,
        TERMINAL_C_ROBUST_AND_ADVANTAGE,
        TERMINAL_C_ROBUST_NO_COMPLETE_ADVANTAGE,
        TERMINAL_BOTH_ROUTES_ROBUST,
        TERMINAL_B_ONLY_ROBUST,
        TERMINAL_NO_ROBUST_ROUTE_SIGNAL,
    }
)

LANE_RECORD_FIELDS: tuple[str, ...] = (
    "lane",
    "source",
    "construction_seed",
    "construction_seed_ordinal",
    "block_seed",
    "matrix_id",
    "errors_initial",
    "errors_final",
    "exact_l2",
    "syndrome_ok",
    "wrong_codeword",
    "iterations",
    "status",
    "runtime_s",
)

Z_95 = 1.959963984540054


class IntegrityFailure(Exception):
    """Raised when a frozen integrity check fails (check id + message)."""

    def __init__(self, check_id: str, message: str) -> None:
        super().__init__(f"[{check_id}] {message}")
        self.check_id = check_id
        self.message = message


# ---------------------------------------------------------------------------
# Descriptive statistics helpers (naive / clustering-uncorrected)
# ---------------------------------------------------------------------------


def wilson_interval_95(successes: int, total: int) -> Optional[list[float]]:
    """Naive Wilson score interval at 95% (descriptive summary only)."""
    if total <= 0:
        return None
    p = successes / total
    z = Z_95
    denom = 1.0 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return [max(0.0, center - half), min(1.0, center + half)]


def mcnemar_exact_two_sided(d_cb: int, d_bc: int) -> float:
    """Two-sided exact McNemar p-value on discordant counts (descriptive)."""
    n = d_cb + d_bc
    if n == 0:
        return 1.0
    k = min(d_cb, d_bc)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2.0 * tail)


def record_block_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate stats for a group of records (naive descriptive level)."""
    n = len(records)
    exact = sum(1 for r in records if r["exact_l2"])
    finals = [int(r["errors_final"]) for r in records]
    iters = [int(r["iterations"]) for r in records]
    runtimes = [float(r["runtime_s"]) for r in records]
    return {
        "records_count": n,
        "exact_count": exact,
        "exact_fraction": (exact / n) if n else None,
        "wilson_95_naive": wilson_interval_95(exact, n),
        "median_errors_final": float(np.median(finals)) if finals else None,
        "mean_errors_final": (sum(finals) / n) if n else None,
        "median_iterations": float(np.median(iters)) if iters else None,
        "mean_iterations": (sum(iters) / n) if n else None,
        "runtime_total_s": sum(runtimes) if runtimes else 0.0,
        "wrong_codeword_count": sum(1 for r in records if r["wrong_codeword"]),
    }


# ---------------------------------------------------------------------------
# Registry and record validators
# ---------------------------------------------------------------------------


def validate_block_registry(seeds: Optional[dict[str, list[int]]] = None) -> tuple[bool, str]:
    """Exact frozen block-seed registry check including V36/V38 overlap (I3)."""
    reg = BLOCK_SEEDS if seeds is None else seeds
    if set(reg.keys()) != set(SOURCE_ORDER):
        return False, f"registry sources must be {SOURCE_ORDER}"
    for source, expected in BLOCK_SEEDS.items():
        actual = list(reg[source])
        if len(actual) != 5 or len(set(actual)) != 5:
            return False, f"source {source} must have 5 unique block seeds"
        overlap = set(actual) & FORBIDDEN_BLOCK_SEEDS
        if overlap:
            return False, f"source {source} overlaps V36/V38-used seeds: {sorted(overlap)}"
        if sorted(actual) != sorted(expected):
            return False, f"source {source} seeds {actual} != frozen {expected}"
    return True, "BLOCK_REGISTRY_OK"


def validate_record_schema(record: dict[str, Any]) -> tuple[bool, str]:
    """Record schema completeness incl. derived wrong_codeword (I7)."""
    for key in LANE_RECORD_FIELDS:
        if key not in record:
            return False, f"missing field {key}"
    for key in ("exact_l2", "syndrome_ok", "wrong_codeword"):
        if not isinstance(record[key], bool):
            return False, f"field {key} must be bool"
    for key in ("errors_initial", "errors_final", "iterations"):
        if not isinstance(record[key], int) or isinstance(record[key], bool):
            return False, f"field {key} must be int"
    if not isinstance(record["block_seed"], int):
        return False, "block_seed must be int"
    expected_wrong = record["syndrome_ok"] and not record["exact_l2"]
    if record["wrong_codeword"] != expected_wrong:
        return False, "wrong_codeword must equal syndrome_ok and not exact_l2"
    if record["lane"] == BASELINE_LANE:
        if record["construction_seed"] is not None or record["construction_seed_ordinal"] is not None:
            return False, "baseline records must have null construction fields"
        if not str(record["matrix_id"]).startswith("v31_baseline_"):
            return False, "baseline matrix_id must start with v31_baseline_"
    else:
        if not isinstance(record["construction_seed"], int):
            return False, "lane construction_seed must be int"
        if record["construction_seed_ordinal"] not in (1, 2, 3):
            return False, "construction_seed_ordinal must be 1..3"
    return True, "SCHEMA_OK"


def validate_post_evaluation(
    lane_records: list[dict[str, Any]],
    baseline_records: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    """Post-evaluation integrity checks I5/I6/I7/I8; returns failures."""
    failures: list[tuple[str, str]] = []
    for lane in LANE_ORDER:
        recs = [r for r in lane_records if r["lane"] == lane]
        if len(recs) != EXPECTED_CALLS[lane]:
            failures.append(("I6", f"{lane} has {len(recs)} records, expected {EXPECTED_CALLS[lane]}"))
    if len(lane_records) != 90:
        failures.append(("I6", f"lane records total {len(lane_records)}, expected 90"))
    if len(baseline_records) != EXPECTED_CALLS[BASELINE_LANE]:
        failures.append(("I6", f"baseline has {len(baseline_records)} records, expected 15"))
    if len(lane_records) + len(baseline_records) != TOTAL_CALLS:
        failures.append(("I6", f"total calls {len(lane_records) + len(baseline_records)}, expected {TOTAL_CALLS}"))

    for rec in lane_records:
        ok, msg = validate_record_schema(rec)
        if not ok:
            failures.append(("I7", f"lane record {rec.get('matrix_id')}/{rec.get('block_seed')}: {msg}"))
    for rec in baseline_records:
        ok, msg = validate_record_schema(rec)
        if not ok:
            failures.append(("I7", f"baseline record {rec.get('source')}/{rec.get('block_seed')}: {msg}"))

    # Cell counts: every (lane, source, construction_seed) has exactly 5 blocks.
    for lane in LANE_ORDER:
        for source in SOURCE_ORDER:
            for seed in CONSTRUCTION_SEEDS[lane][source]:
                cell = [
                    r
                    for r in lane_records
                    if r["lane"] == lane
                    and r["source"] == source
                    and r["construction_seed"] == seed
                ]
                if len(cell) != 5 or {r["block_seed"] for r in cell} != set(BLOCK_SEEDS[source]):
                    failures.append(("I6", f"cell {lane}/{source}/s{seed} incomplete"))

    # Baseline dedup (I5): exactly one record per (source, block_seed).
    base_keys: dict[tuple[str, int], dict[str, Any]] = {}
    for rec in baseline_records:
        key = (rec["source"], rec["block_seed"])
        if key in base_keys:
            failures.append(("I5", f"duplicate baseline record {key}"))
        base_keys[key] = rec
    if len(base_keys) != 15:
        failures.append(("I5", f"baseline covers {len(base_keys)} unique blocks, expected 15"))

    # Pairing completeness and errors_initial equality (I8).
    by_lane: dict[str, dict[tuple[str, int, int], dict[str, Any]]] = {lane: {} for lane in LANE_ORDER}
    for rec in lane_records:
        by_lane[rec["lane"]][(rec["source"], rec["construction_seed_ordinal"], rec["block_seed"])] = rec
    c_keys = set(by_lane["lane_c"].keys())
    b_keys = set(by_lane["lane_b"].keys())
    if c_keys != b_keys or len(c_keys) != 45:
        failures.append(("I8", f"C/B pairing keys differ or incomplete (C={len(c_keys)}, B={len(b_keys)})"))
    baseline_by_block: dict[tuple[str, int], dict[str, Any]] = base_keys
    for key in sorted(c_keys & b_keys):
        source, _, block_seed = key
        bkey = (source, block_seed)
        if bkey not in baseline_by_block:
            failures.append(("I8", f"missing same-block baseline join for {bkey}"))
            continue
        initials = {
            by_lane["lane_c"][key]["errors_initial"],
            by_lane["lane_b"][key]["errors_initial"],
            baseline_by_block[bkey]["errors_initial"],
        }
        if len(initials) != 1:
            failures.append(("I8", f"errors_initial mismatch for {key}: {sorted(initials)}"))
    return failures


# ---------------------------------------------------------------------------
# Deterministic structural reconstruction (decoder-free)
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
            "I10",
            f"structural authority must be the committed run_01 JSON, got NPZ path: {path}",
        )


def reconstruct_v39_matrices(
    reference_metrics_path: Path | str = STRUCTURAL_AUTHORITY_PATH,
    field: Optional[GF2mField] = None,
    constructors: Optional[dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]]] = None,
    only: Optional[frozenset[tuple[str, str, int]]] = None,
) -> dict[tuple[str, str, int], tuple[np.ndarray, dict[str, Any]],]:
    """Rebuild all 18 Lane B/C matrices and strict-compare vs committed metrics.

    ``only`` restricts reconstruction to a subset of ``(lane, source, seed)``
    keys (used by focused tests); production runs reconstruct all 18.
    """
    _reject_forbidden_npz(reference_metrics_path)
    reference_by_id = _load_v38r1_reference_metrics(reference_metrics_path)
    field = field or GF2mField.create(DIMENSION)
    if field.primitive_polynomial != POLYNOMIAL:
        raise IntegrityFailure(
            "I11", f"field polynomial mismatch: expected {POLYNOMIAL}, got {field.primitive_polynomial}"
        )
    ctor_map = constructors or DEFAULT_CONSTRUCTORS
    matrices: dict[tuple[str, str, int], tuple[np.ndarray, dict[str, Any]]] = {}
    for lane in LANE_ORDER:
        for source in SOURCE_ORDER:
            for seed in CONSTRUCTION_SEEDS[lane][source]:
                if only is not None and (lane, source, seed) not in only:
                    continue
                matrix_id = f"{lane}_{source}_s{seed}"
                expected = reference_by_id.get(matrix_id)
                if expected is None:
                    raise IntegrityFailure("I2", f"missing committed metrics for {matrix_id}")
                if expected.get("lane") != lane or expected.get("source") != source:
                    raise IntegrityFailure("I2", f"identity mismatch in committed metrics: {matrix_id}")
                matrix, metrics = ctor_map[lane](source=source, seed=seed, field=field)
                try:
                    _check_v38r1_metric_match(expected, metrics, matrix_id)
                except ValueError as exc:
                    raise IntegrityFailure("I1", str(exc)) from exc
                matrices[(lane, source, seed)] = (matrix, metrics)
    if not matrices:
        raise IntegrityFailure("I1", "no matrices reconstructed")
    return matrices


def structural_reconstruction_rows(
    matrices: dict[tuple[str, str, int], tuple[np.ndarray, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Normalized rows for v39_structural_reconstruction outputs."""
    rows: list[dict[str, Any]] = []
    for lane in LANE_ORDER:
        for source in SOURCE_ORDER:
            for seed in CONSTRUCTION_SEEDS[lane][source]:
                key = (lane, source, seed)
                _, metrics = matrices[key]
                perms = metrics.get("position_permutations")
                rows.append(
                    {
                        "lane": lane,
                        "source": source,
                        "construction_seed": seed,
                        "construction_seed_ordinal": CONSTRUCTION_SEEDS[lane][source].index(seed) + 1,
                        "matrix_id": f"{lane}_{source}_s{seed}",
                        "shape": metrics.get("shape"),
                        "rank_GF32": metrics.get("rank_GF32"),
                        "support_edge_count": metrics.get("support_edge_count"),
                        "row_degree_max": metrics.get("row_degree_max"),
                        "support_cycles_4": metrics.get("support_cycles_4"),
                        "degenerate_cycles_4": metrics.get("degenerate_cycles_4"),
                        "degenerate_cycles_6": metrics.get("degenerate_cycles_6"),
                        "degenerate_cycles_8": metrics.get("degenerate_cycles_8"),
                        "structurally_valid": metrics.get("structurally_valid"),
                        "position_permutations_json": json.dumps(perms) if perms is not None else "",
                        "strict_match_committed_metrics": True,
                    }
                )
    return rows


# ---------------------------------------------------------------------------
# Posterior-binding preflight (P-BIND-1/2/3, decoder-free)
# ---------------------------------------------------------------------------


def posterior_binding_preflight(
    counts_by_source: dict[str, np.ndarray],
    probes: Optional[dict[str, int]] = None,
) -> dict[str, dict[str, Any]]:
    """Verify complete-Bob binding on the frozen probe blocks (I4 on failure).

    Fixed sentinels per probe source:
      bob_gt_31, captured_equals_bob, corrected_equals_direct,
      corrected_differs_u2bob_arraywise, corrected_differs_u2bob_maxabs,
      argmax_divergence.
    No production decoder call occurs here and nothing is written.
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
                "I4",
                f"posterior-binding sentinel failed on probe {source}/{probe_seed}: {failed}; "
                "probe replacement requires a plan-review change, never post-execution",
            )
        results[source] = checks
    return results


# ---------------------------------------------------------------------------
# Aggregations (levels 1-8), gates, paired comparison, terminal machine
# ---------------------------------------------------------------------------


def aggregate_lane_records(
    lane_records: list[dict[str, Any]],
    baseline_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregation levels 1-8 over the frozen grouping hierarchy."""
    out: dict[str, Any] = {}
    for lane in LANE_ORDER:
        recs = [r for r in lane_records if r["lane"] == lane]
        lane_stats: dict[str, Any] = {"overall": record_block_stats(recs)}
        lane_stats["by_source"] = {
            s: record_block_stats([r for r in recs if r["source"] == s]) for s in SOURCE_ORDER
        }
        lane_stats["by_construction_seed_ordinal"] = {
            str(o): record_block_stats([r for r in recs if r["construction_seed_ordinal"] == o])
            for o in (1, 2, 3)
        }
        cells = {}
        for source in SOURCE_ORDER:
            for seed in CONSTRUCTION_SEEDS[lane][source]:
                key = f"{source}_s{seed}"
                cells[key] = record_block_stats(
                    [r for r in recs if r["source"] == source and r["construction_seed"] == seed]
                )
        lane_stats["by_source_construction_seed"] = cells
        clusters = {}
        for source in SOURCE_ORDER:
            for block_seed in BLOCK_SEEDS[source]:
                group = [
                    r
                    for r in recs
                    if r["source"] == source and r["block_seed"] == block_seed
                ]
                residuals = [int(r["errors_final"]) for r in group]
                clusters[f"{source}_{block_seed}"] = {
                    "matrices_count": len(group),
                    "seed_exact_count": sum(1 for r in group if r["exact_l2"]),
                    "seed_exact_fraction": (
                        sum(1 for r in group if r["exact_l2"]) / len(group) if group else None
                    ),
                    "residual_mean_across_3_matrices": (
                        sum(residuals) / len(residuals) if residuals else None
                    ),
                    "residual_median_across_3_matrices": (
                        float(np.median(residuals)) if residuals else None
                    ),
                }
        lane_stats["block_clusters"] = clusters
        out[lane] = lane_stats
    out[BASELINE_LANE] = {
        "overall": record_block_stats(baseline_records),
        "by_source": {
            s: record_block_stats([r for r in baseline_records if r["source"] == s])
            for s in SOURCE_ORDER
        },
    }
    return out


def build_paired_rows(
    lane_records: list[dict[str, Any]],
    baseline_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """The 45 C/B pairs joined to the single same-block baseline record."""
    index: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    for rec in lane_records:
        index[(rec["lane"], rec["source"], rec["construction_seed_ordinal"], rec["block_seed"])] = rec
    baseline_by_block = {(r["source"], r["block_seed"]): r for r in baseline_records}
    rows: list[dict[str, Any]] = []
    for source in SOURCE_ORDER:
        for ordinal in (1, 2, 3):
            for block_seed in BLOCK_SEEDS[source]:
                c = index[("lane_c", source, ordinal, block_seed)]
                b = index[("lane_b", source, ordinal, block_seed)]
                base = baseline_by_block[(source, block_seed)]
                if c["exact_l2"] and not b["exact_l2"]:
                    label = "C_ONLY_EXACT"
                elif b["exact_l2"] and not c["exact_l2"]:
                    label = "B_ONLY_EXACT"
                elif c["exact_l2"] and b["exact_l2"]:
                    label = "BOTH_EXACT"
                else:
                    label = "NEITHER_EXACT"
                rows.append(
                    {
                        "source": source,
                        "construction_seed_ordinal": ordinal,
                        "block_seed": block_seed,
                        "errors_initial": c["errors_initial"],
                        "c_matrix_id": c["matrix_id"],
                        "c_exact_l2": c["exact_l2"],
                        "c_errors_final": c["errors_final"],
                        "b_matrix_id": b["matrix_id"],
                        "b_exact_l2": b["exact_l2"],
                        "b_errors_final": b["errors_final"],
                        "v31_baseline_errors_final": base["errors_final"],
                        "discordance_label": label,
                    }
                )
    return rows


def paired_discordance_summary(paired_rows: list[dict[str, Any]]) -> dict[str, Any]:
    d_cb = sum(1 for r in paired_rows if r["discordance_label"] == "C_ONLY_EXACT")
    d_bc = sum(1 for r in paired_rows if r["discordance_label"] == "B_ONLY_EXACT")
    concordant_exact = sum(1 for r in paired_rows if r["discordance_label"] == "BOTH_EXACT")
    concordant_fail = sum(1 for r in paired_rows if r["discordance_label"] == "NEITHER_EXACT")
    return {
        "pairs_count": len(paired_rows),
        "d_CB": d_cb,
        "d_BC": d_bc,
        "discordance_margin_d_CB_minus_d_BC": d_cb - d_bc,
        "concordant_both_exact": concordant_exact,
        "concordant_neither_exact": concordant_fail,
        "mcnemar_exact_p_two_sided_descriptive_uncorrected": mcnemar_exact_two_sided(d_cb, d_bc),
    }


def evaluate_gate_robustness(lane: str, lane_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Frozen gate C1 / B1 (identical thresholds; includes >=4/5 cells)."""
    recs = [r for r in lane_records if r["lane"] == lane]
    overall = record_block_stats(recs)
    sources = {
        s: record_block_stats([r for r in recs if r["source"] == s]) for s in SOURCE_ORDER
    }
    ordinals = {
        o: record_block_stats([r for r in recs if r["construction_seed_ordinal"] == o])
        for o in (1, 2, 3)
    }
    cells = {}
    for source in SOURCE_ORDER:
        for seed in CONSTRUCTION_SEEDS[lane][source]:
            key = f"{source}_s{seed}"
            cells[key] = record_block_stats(
                [r for r in recs if r["source"] == source and r["construction_seed"] == seed]
            )
    details = {
        "overall_min_36_of_45": {
            "passed": overall["exact_count"] >= C1_OVERALL_MIN,
            "exact_count": overall["exact_count"],
            "threshold": C1_OVERALL_MIN,
        },
        "each_source_min_12_of_15": {
            s: {
                "passed": sources[s]["exact_count"] >= C1_SOURCE_MIN,
                "exact_count": sources[s]["exact_count"],
                "threshold": C1_SOURCE_MIN,
            }
            for s in SOURCE_ORDER
        },
        "each_ordinal_min_12_of_15": {
            str(o): {
                "passed": ordinals[o]["exact_count"] >= C1_ORDINAL_MIN,
                "exact_count": ordinals[o]["exact_count"],
                "threshold": C1_ORDINAL_MIN,
            }
            for o in (1, 2, 3)
        },
        "each_cell_min_4_of_5": {
            key: {
                "passed": stat["exact_count"] >= C1_CELL_MIN,
                "exact_count": stat["exact_count"],
                "threshold": C1_CELL_MIN,
            }
            for key, stat in cells.items()
        },
        "overall_median_errors_final_zero": {
            "passed": overall["median_errors_final"] == 0.0,
            "value": overall["median_errors_final"],
        },
        "each_source_median_errors_final_zero": {
            s: {"passed": sources[s]["median_errors_final"] == 0.0, "value": sources[s]["median_errors_final"]}
            for s in SOURCE_ORDER
        },
        "wrong_codeword_count_reported_separately": overall["wrong_codeword_count"],
    }
    passed = (
        details["overall_min_36_of_45"]["passed"]
        and all(v["passed"] for v in details["each_source_min_12_of_15"].values())
        and all(v["passed"] for v in details["each_ordinal_min_12_of_15"].values())
        and all(v["passed"] for v in details["each_cell_min_4_of_5"].values())
        and details["overall_median_errors_final_zero"]["passed"]
        and all(v["passed"] for v in details["each_source_median_errors_final_zero"].values())
    )
    return {"gate": "C1" if lane == "lane_c" else "B1", "lane": lane, "passed": passed, "details": details}


def evaluate_gate_cb(
    lane_records: list[dict[str, Any]],
    paired_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Frozen gate CB: CB-a/B/C/D, each computed and reported separately."""
    c_recs = [r for r in lane_records if r["lane"] == "lane_c"]
    b_recs = [r for r in lane_records if r["lane"] == "lane_b"]
    exact_c = sum(1 for r in c_recs if r["exact_l2"])
    exact_b = sum(1 for r in b_recs if r["exact_l2"])
    disc = paired_discordance_summary(paired_rows)

    cb_a = exact_c >= exact_b + CB_EXACT_MARGIN
    cb_b = disc["discordance_margin_d_CB_minus_d_BC"] >= CB_DISCORDANCE_MARGIN

    per_source_c = {s: sum(1 for r in c_recs if r["source"] == s and r["exact_l2"]) for s in SOURCE_ORDER}
    per_source_b = {s: sum(1 for r in b_recs if r["source"] == s and r["exact_l2"]) for s in SOURCE_ORDER}
    cb_c = all(
        per_source_c[s] >= per_source_b[s] - CB_PER_SOURCE_TRAIL_TOLERANCE for s in SOURCE_ORDER
    )

    mean_c = sum(int(r["errors_final"]) for r in c_recs) / len(c_recs)
    mean_b = sum(int(r["errors_final"]) for r in b_recs) / len(b_recs)
    cb_d = mean_c <= mean_b

    passed = cb_a and cb_b and cb_c and cb_d
    return {
        "gate": "CB",
        "passed": passed,
        "details": {
            "cb_a_exact_margin": {
                "passed": cb_a,
                "exact_count_C": exact_c,
                "exact_count_B": exact_b,
                "threshold": f"exact_count_C >= exact_count_B + {CB_EXACT_MARGIN}",
            },
            "cb_b_discordance_margin": {
                "passed": cb_b,
                "d_CB": disc["d_CB"],
                "d_BC": disc["d_BC"],
                "margin": disc["discordance_margin_d_CB_minus_d_BC"],
                "threshold": f"d_CB - d_BC >= {CB_DISCORDANCE_MARGIN}",
                "note": "under complete pairing exact_count_C - exact_count_B = d_CB - d_BC; "
                "CB-a implies CB-b and CB-b does NOT imply CB-a",
            },
            "cb_c_no_source_trails_by_more_than_one": {
                "passed": cb_c,
                "per_source_exact_C": per_source_c,
                "per_source_exact_B": per_source_b,
                "tolerance": CB_PER_SOURCE_TRAIL_TOLERANCE,
            },
            "cb_d_mean_residual_compare": {
                "passed": cb_d,
                "mean_errors_final_C": mean_c,
                "mean_errors_final_B": mean_b,
                "metric": "mean (not median)",
            },
        },
    }


def evaluate_gate_base(
    lane: str,
    lane_records: list[dict[str, Any]],
    baseline_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Frozen gate BASE evaluated per construction-seed ordinal (15-vs-15)."""
    base_overall = record_block_stats(baseline_records)
    base_sources = {
        s: record_block_stats([r for r in baseline_records if r["source"] == s]) for s in SOURCE_ORDER
    }
    ordinals: dict[str, Any] = {}
    for o in (1, 2, 3):
        lane_o = [r for r in lane_records if r["lane"] == lane and r["construction_seed_ordinal"] == o]
        stats_o = record_block_stats(lane_o)
        per_source = {}
        for s in SOURCE_ORDER:
            lane_so = [r for r in lane_o if r["source"] == s]
            med_so = float(np.median([int(r["errors_final"]) for r in lane_so])) if lane_so else None
            per_source[s] = {
                "passed": (med_so is not None and med_so <= float(base_sources[s]["median_errors_final"])),
                "median_errors_final_lane_source_ordinal": med_so,
                "median_errors_final_v31_source": base_sources[s]["median_errors_final"],
            }
        exact_ok = stats_o["exact_count"] > base_overall["exact_count"]
        median_ok = stats_o["median_errors_final"] < base_overall["median_errors_final"]
        ordinals[str(o)] = {
            "passed": bool(exact_ok and median_ok and all(v["passed"] for v in per_source.values())),
            "exact_count_lane_ordinal": stats_o["exact_count"],
            "exact_count_v31_baseline": base_overall["exact_count"],
            "exact_condition_passed": exact_ok,
            "median_errors_final_lane_ordinal": stats_o["median_errors_final"],
            "median_errors_final_v31_overall": base_overall["median_errors_final"],
            "median_condition_passed": median_ok,
            "per_source_median_conditions": per_source,
        }
    overall_passed = all(v["passed"] for v in ordinals.values())
    return {
        "gate": "BASE",
        "lane": lane,
        "report_only": lane == "lane_b",
        "ordinals": ordinals,
        "passed": overall_passed,
        "note": "V31 remains exactly 15 calls/records; joins reuse the single same-block "
        "baseline record and never create new independent baseline observations",
    }


def determine_v39_terminal_state(
    integrity_ok: bool,
    c1_pass: bool,
    cb_pass: bool,
    base_c_pass: bool,
    b1_pass: bool,
) -> tuple[str, Optional[str]]:
    """Exhaustive integrity-first terminal machine; first matching rule wins."""
    if not integrity_ok:
        return TERMINAL_EVIDENCE_INVALID, None
    if c1_pass and cb_pass and base_c_pass:
        return TERMINAL_C_ROBUST_AND_ADVANTAGE, None
    if c1_pass and not b1_pass:
        if not cb_pass and base_c_pass:
            reason = "CB_FAIL"
        elif cb_pass and not base_c_pass:
            reason = "BASE_C_FAIL"
        else:
            reason = "CB_AND_BASE_C_FAIL"
        return TERMINAL_C_ROBUST_NO_COMPLETE_ADVANTAGE, reason
    if c1_pass and b1_pass:
        return TERMINAL_BOTH_ROUTES_ROBUST, None
    if b1_pass:
        return TERMINAL_B_ONLY_ROBUST, None
    return TERMINAL_NO_ROBUST_ROUTE_SIGNAL, None


# ---------------------------------------------------------------------------
# Environment loaders (counts provenance, V31 identity, git binding)
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


def read_v31_packet_identity() -> dict[str, Any]:
    from comparison_bench.formal_ir import v35_algorithm_development as v35

    path = (
        Path(v35.__file__).resolve().parents[4]
        / "comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/matrix_payloads.json"
    )
    with path.open("r", encoding="utf-8") as handle:
        doc = json.load(handle)
    pkt = next((p for p in doc.get("packets", []) if p.get("packet_id") == V31_PACKET_ID), None)
    if pkt is None:
        raise IntegrityFailure("P3", f"V31 packet {V31_PACKET_ID} not found in {path}")
    l2 = pkt.get("matrices", {}).get("L2", {})
    return {
        "packet_id": V31_PACKET_ID,
        "source_path": str(path),
        "source_shapes": {src: list(np.array(l2[src]).shape) for src in SOURCE_ORDER},
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
    """Refuse execution when any scoped tracked file differs from HEAD.

    Only the listed scientific/implementation files are judged (index +
    worktree vs HEAD). Untracked files and unrelated modifications elsewhere
    in the worktree are deliberately ignored.
    """
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "HEAD", "--quiet", "--", *relative_paths],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise IntegrityFailure(
            "TRACKED_DIRTY",
            f"scoped tracked files differ from HEAD; commit or revert before "
            f"execution: {list(relative_paths)}",
        )


def verify_execution_sha_binding(repo_root: Path, authorized_target_sha: str) -> dict[str, str]:
    """Exact-equality binding of HEAD AND origin branch to the authorized SHA."""
    head = git_rev_parse(repo_root, "HEAD")
    branch = git_rev_parse(repo_root, BRANCH_REF)
    if head != authorized_target_sha or branch != authorized_target_sha:
        raise IntegrityFailure(
            "SHA_BINDING_MISMATCH",
            f"authorized_target_sha={authorized_target_sha} but HEAD={head} and {BRANCH_REF}={branch}",
        )
    return {"HEAD": head, BRANCH_REF: branch}


# ---------------------------------------------------------------------------
# Guarded development runner
# ---------------------------------------------------------------------------


def _normalize_lane_record(record: dict[str, Any]) -> dict[str, Any]:
    ordered = {key: record[key] for key in LANE_RECORD_FIELDS}
    return ordered


def _evaluate_all_calls(
    matrices: dict[tuple[str, str, int], tuple[np.ndarray, dict[str, Any]]],
    counts_by_source: dict[str, np.ndarray],
    v31_matrices: dict[str, np.ndarray],
    field: GF2mField,
    fake_runner: bool,
    lane_sink: list[dict[str, Any]],
    baseline_sink: list[dict[str, Any]],
) -> None:
    """Append records progressively so partial evidence survives a mid-run crash."""
    for lane in LANE_ORDER:
        for source in SOURCE_ORDER:
            for ordinal, seed in enumerate(CONSTRUCTION_SEEDS[lane][source], start=1):
                matrix, _ = matrices[(lane, source, seed)]
                for block_seed in BLOCK_SEEDS[source]:
                    raw = evaluate_single_block(
                        H=matrix,
                        source=source,
                        block_seed=block_seed,
                        lane=lane,
                        construction_seed=seed,
                        counts=counts_by_source[source],
                        max_iter=MAX_ITER,
                        damping_alpha=DAMPING_ALPHA,
                        fake_runner=fake_runner,
                        field=field,
                    )
                    raw["construction_seed_ordinal"] = ordinal
                    raw["wrong_codeword"] = bool(raw["syndrome_ok"] and not raw["exact_l2"])
                    lane_sink.append(_normalize_lane_record(raw))
    for source in SOURCE_ORDER:
        for block_seed in BLOCK_SEEDS[source]:
            raw = evaluate_single_block(
                H=v31_matrices[source],
                source=source,
                block_seed=block_seed,
                lane=BASELINE_LANE,
                construction_seed=0,
                counts=counts_by_source[source],
                max_iter=MAX_ITER,
                damping_alpha=DAMPING_ALPHA,
                fake_runner=fake_runner,
                field=field,
            )
            raw["lane"] = BASELINE_LANE
            raw["construction_seed"] = None
            raw["construction_seed_ordinal"] = None
            raw["matrix_id"] = f"v31_baseline_{source}"
            raw["wrong_codeword"] = bool(raw["syndrome_ok"] and not raw["exact_l2"])
            baseline_sink.append(_normalize_lane_record(raw))


def build_v39_summary(
    lifecycle_state: str,
    fake_runner: bool,
    authorized_target_sha: Optional[str],
    sha_binding: Optional[dict[str, str]],
    counts_provenance: dict[str, Any],
    v31_identity: dict[str, Any],
    structural_rows: list[dict[str, Any]],
    aggregates: Optional[dict[str, Any]],
    gates: Optional[dict[str, Any]],
    discordance: Optional[dict[str, Any]],
    integrity_failures: Optional[list[tuple[str, str]]],
    terminal_state: str,
    terminal_reason: Optional[str],
    completed_lane_records: Optional[list[dict[str, Any]]] = None,
    completed_baseline_records: Optional[list[dict[str, Any]]] = None,
    decoder_calls_started: Optional[int] = None,
) -> dict[str, Any]:
    invalid = terminal_state == TERMINAL_EVIDENCE_INVALID
    lane_done = list(completed_lane_records or [])
    baseline_done = list(completed_baseline_records or [])
    return {
        "cycle_id": CYCLE_ID,
        "change_id": CHANGE_ID,
        "accepted_plan_sha": ACCEPTED_PLAN_SHA,
        "lifecycle_state": lifecycle_state,
        "execution_status": lifecycle_state,
        "fake_runner": fake_runner,
        "provenance": {
            "authorized_target_sha": authorized_target_sha,
            "sha_binding": sha_binding,
            "structural_authority": str(STRUCTURAL_AUTHORITY_PATH),
            "structural_records_strict_match": len(structural_rows),
        },
        "v25_counts_provenance": counts_provenance,
        "v31_packet_identity": v31_identity,
        "accounting": {
            "decoder_calls_planned": {
                "total": TOTAL_CALLS,
                "lane_c": EXPECTED_CALLS["lane_c"],
                "lane_b": EXPECTED_CALLS["lane_b"],
                "v31_baseline": EXPECTED_CALLS[BASELINE_LANE],
            },
            "decoder_calls_completed": {
                "total": len(lane_done) + len(baseline_done),
                "lane_c": sum(1 for r in lane_done if r.get("lane") == "lane_c"),
                "lane_b": sum(1 for r in lane_done if r.get("lane") == "lane_b"),
                "v31_baseline": len(baseline_done),
            },
            "decoder_calls_started": decoder_calls_started,
            "structural_reconstruction_decoder_calls": 0,
            "preflight_decoder_calls": 0,
        },
        "npz_policy": {
            "forbidden_winner_npz_read": False,
            "any_npz_output_written": False,
            "v25_channel_counts_npz_read_only_allowed": True,
        },
        "statistics_note": (
            "45 lane records per lane are 15 unique sampled blocks x 3 construction "
            "matrices, NOT 45 independent block draws. Record-level Wilson intervals "
            "are naive descriptive summaries and the 45-pair McNemar test is "
            "descriptive and uncorrected for construction/block clustering; neither "
            "indicates independent-sample significance nor replaces the frozen gates."
        ),
        "aggregates": aggregates,
        "paired_discordance": discordance,
        "gates": gates,
        "integrity_failures": (
            [{"check": cid, "message": msg} for cid, msg in integrity_failures]
            if integrity_failures
            else []
        ),
        "terminal_state": terminal_state,
        "terminal_reason": terminal_reason,
        "performance_interpretation_presented": not invalid,
        "claim_boundary": [
            "bounded reproducibility evidence on empirical-count development samples "
            "with oracle-L1 conditioning",
            "success metric is exact_l2 only; syndrome_ok/wrong_codeword reported separately",
            "no FER, asymptotic threshold, SKR, security, qualification, promotion, or "
            "real-frame claim",
            "V39_B_ONLY_ROBUST asserts B1 robustness only and does not assert Lane B "
            "superiority over V31; BASE-B verdicts accompany interpretation",
        ],
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


def write_v39_outputs(
    output_root: Path | str,
    structural_rows: list[dict[str, Any]],
    lane_records: list[dict[str, Any]],
    baseline_records: list[dict[str, Any]],
    paired_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> Path:
    """Write the fixed additive evidence set; fail closed on a non-empty root.

    The guarded runner pre-creates the (empty) root just before the decoder
    phase, so writing into an existing-but-empty root owned by this run is
    expected; any pre-existing NON-empty root is refused.
    """
    root = Path(output_root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"I9: refusing to overwrite non-empty output root: {root}")
    if not root.exists():
        root.mkdir(parents=True)

    def dump(name: str, payload: Any) -> None:
        with (root / name).open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    structural_columns = list(structural_rows[0].keys()) if structural_rows else []
    lane_columns = list(LANE_RECORD_FIELDS)
    paired_columns = list(paired_rows[0].keys()) if paired_rows else []

    dump("v39_structural_reconstruction.json", structural_rows)
    write_records_csv(root / "v39_structural_reconstruction.csv", structural_rows, structural_columns)
    dump("v39_block_records.json", lane_records)
    write_records_csv(root / "v39_block_records.csv", lane_records, lane_columns)
    dump("v39_baseline_records.json", baseline_records)
    write_records_csv(root / "v39_baseline_records.csv", baseline_records, lane_columns)
    dump("v39_paired_comparison.json", paired_rows)
    write_records_csv(root / "v39_paired_comparison.csv", paired_rows, paired_columns)
    dump("v39_summary.json", summary)
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
    path = root / "v39_invalid_notice.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(notice, handle, indent=2)
    return path


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def run_v39_development(
    development_execution_authorized: bool = False,
    authorized_target_sha: Optional[str] = None,
    fake_runner: bool = False,
    output_root: Optional[Path | str] = None,
    structural_authority_path: Optional[Path | str] = None,
    counts_by_source: Optional[dict[str, np.ndarray]] = None,
    v31_matrices: Optional[dict[str, np.ndarray]] = None,
    field: Optional[GF2mField] = None,
    check_git: bool = True,
    check_scoped_dirty: bool = True,
    constructors: Optional[dict[str, Callable[..., tuple[np.ndarray, dict[str, Any]]]]] = None,
    reconstruct_only: Optional[frozenset[tuple[str, str, int]]] = None,
) -> dict[str, Any]:
    """Guarded single-run orchestration; default-deny, fail-closed."""
    if not development_execution_authorized:
        raise PermissionError(
            "EXECUTE_NOT_AUTHORIZED: pass --development-execution-authorized bound to an "
            "explicit user EXECUTE_AUTH for scope v39_decoder_only_105_calls_exactly_once"
        )

    root_arg = output_root if output_root is not None else OUTPUT_ROOT
    root = Path(root_arg)
    if root.exists():
        raise FileExistsError(f"I9: refusing to overwrite existing output root: {root}")

    spath = Path(structural_authority_path) if structural_authority_path else STRUCTURAL_AUTHORITY_PATH
    field = field or GF2mField.create(DIMENSION)
    if field.primitive_polynomial != POLYNOMIAL:
        raise IntegrityFailure("I11", f"polynomial mismatch: {field.primitive_polynomial}")

    sha_binding: Optional[dict[str, str]] = None
    if check_git:
        if not authorized_target_sha:
            raise IntegrityFailure(
                "SHA_BINDING_MISSING",
                "authorized_target_sha is required for the authorized run",
            )
        sha_binding = verify_execution_sha_binding(REPO_ROOT, authorized_target_sha)

    if check_scoped_dirty:
        # Execution-refusal class failure: raised before any evidence root
        # exists, so nothing is created.
        verify_scoped_clean(REPO_ROOT)

    registry_ok, registry_msg = validate_block_registry()
    if not registry_ok:
        raise IntegrityFailure("I3", registry_msg)

    matrices = reconstruct_v39_matrices(
        reference_metrics_path=spath,
        field=field,
        constructors=constructors,
        only=reconstruct_only,
    )
    expected_matrices = 18 if reconstruct_only is None else len(reconstruct_only)
    if len(matrices) != expected_matrices:
        raise IntegrityFailure("I1", f"reconstructed {len(matrices)} matrices, expected {expected_matrices}")
    structural_rows = structural_reconstruction_rows(matrices)

    counts = counts_by_source if counts_by_source is not None else load_v25_channel_counts()
    for source in SOURCE_ORDER:
        if counts[source].shape != (1024, 1024):
            raise IntegrityFailure("I4", f"unexpected counts shape for {source}: {counts[source].shape}")
    counts_provenance = describe_v25_counts_provenance()

    posterior_binding_preflight(counts)  # raises IntegrityFailure(I4) on any sentinel failure

    v31 = v31_matrices if v31_matrices is not None else load_v31_qc_baseline_matrices()
    v31_identity = read_v31_packet_identity()
    for source in SOURCE_ORDER:
        expected_shape = (184 if source == "1M" else 190 if source == "1p5M" else 192, BLOCK_LENGTH)
        if v31[source].shape != expected_shape:
            raise IntegrityFailure("P3", f"V31 matrix shape mismatch for {source}: {v31[source].shape}")

    # All preflight (reconstruction, posterior sentinels, V31 identity) is
    # complete. The run is about to enter the real decoder phase: occupy the
    # additive root NOW. From this point any crash — including KeyboardInterrupt
    # or process kill — leaves the root (plus retained raw partials) in place
    # so a relaunch fails closed on I9 instead of silently re-running.
    root.mkdir(parents=True)
    lane_records: list[dict[str, Any]] = []
    baseline_records: list[dict[str, Any]] = []
    try:
        _evaluate_all_calls(
            matrices, counts, v31, field, fake_runner, lane_records, baseline_records
        )
    except BaseException:
        _persist_invalid_evidence(
            root,
            structural_rows=structural_rows,
            lane_records=lane_records,
            baseline_records=baseline_records,
            summary_ctx={
                "fake_runner": fake_runner,
                "authorized_target_sha": authorized_target_sha,
                "sha_binding": sha_binding,
                "counts_provenance": counts_provenance,
                "v31_identity": v31_identity,
            },
            failures=[("mid_run_failure", "raw partial records retained; no performance aggregate generated")],
        )
        raise

    failures = validate_post_evaluation(lane_records, baseline_records)
    if failures:
        _persist_invalid_evidence(
            root,
            structural_rows=structural_rows,
            lane_records=lane_records,
            baseline_records=baseline_records,
            summary_ctx={
                "fake_runner": fake_runner,
                "authorized_target_sha": authorized_target_sha,
                "sha_binding": sha_binding,
                "counts_provenance": counts_provenance,
                "v31_identity": v31_identity,
            },
            failures=failures,
        )
        return {
            "output_root": str(root),
            "terminal_state": TERMINAL_EVIDENCE_INVALID,
            "terminal_reason": None,
            "integrity_failures": failures,
        }

    aggregates = aggregate_lane_records(lane_records, baseline_records)
    paired_rows = build_paired_rows(lane_records, baseline_records)
    discordance = paired_discordance_summary(paired_rows)
    gate_c1 = evaluate_gate_robustness("lane_c", lane_records)
    gate_b1 = evaluate_gate_robustness("lane_b", lane_records)
    gate_cb = evaluate_gate_cb(lane_records, paired_rows)
    base_c = evaluate_gate_base("lane_c", lane_records, baseline_records)
    base_b = evaluate_gate_base("lane_b", lane_records, baseline_records)
    gates = {"C1": gate_c1, "B1": gate_b1, "CB": gate_cb, "BASE_C": base_c, "BASE_B": base_b}
    terminal_state, terminal_reason = determine_v39_terminal_state(
        integrity_ok=True,
        c1_pass=gate_c1["passed"],
        cb_pass=gate_cb["passed"],
        base_c_pass=base_c["passed"],
        b1_pass=gate_b1["passed"],
    )

    summary = build_v39_summary(
        lifecycle_state="DEVELOPMENT_RESULT_CANDIDATE",
        fake_runner=fake_runner,
        authorized_target_sha=authorized_target_sha,
        sha_binding=sha_binding,
        counts_provenance=counts_provenance,
        v31_identity=v31_identity,
        structural_rows=structural_rows,
        aggregates=aggregates,
        gates=gates,
        discordance=discordance,
        integrity_failures=None,
        terminal_state=terminal_state,
        terminal_reason=terminal_reason,
        completed_lane_records=lane_records,
        completed_baseline_records=baseline_records,
        decoder_calls_started=TOTAL_CALLS,
    )
    write_v39_outputs(root, structural_rows, lane_records, baseline_records, paired_rows, summary)
    return {
        "output_root": str(root),
        "terminal_state": terminal_state,
        "terminal_reason": terminal_reason,
        "decoder_calls_total": TOTAL_CALLS,
        "gates": {name: g["passed"] for name, g in gates.items()},
        "summary": summary,
    }


def _persist_invalid_evidence(
    root: Path,
    *,
    structural_rows: list[dict[str, Any]],
    lane_records: list[dict[str, Any]],
    baseline_records: list[dict[str, Any]],
    summary_ctx: dict[str, Any],
    failures: list[tuple[str, str]],
) -> None:
    """Retain raw collected evidence byte-for-byte plus invalid notice/summary.

    No performance aggregate, gate, or paired-comparison artifact is produced.
    Never masks the original failure with writer problems.
    """
    try:
        if not root.exists():
            root.mkdir(parents=True)
        if structural_rows:
            with (root / "v39_structural_reconstruction.json").open("w", encoding="utf-8") as handle:
                json.dump(structural_rows, handle, indent=2)
            write_records_csv(
                root / "v39_structural_reconstruction.csv",
                structural_rows,
                list(structural_rows[0].keys()),
            )
        if lane_records:
            with (root / "v39_block_records.json").open("w", encoding="utf-8") as handle:
                json.dump(lane_records, handle, indent=2)
            write_records_csv(
                root / "v39_block_records.csv", lane_records, list(LANE_RECORD_FIELDS)
            )
        if baseline_records:
            with (root / "v39_baseline_records.json").open("w", encoding="utf-8") as handle:
                json.dump(baseline_records, handle, indent=2)
            write_records_csv(
                root / "v39_baseline_records.csv", baseline_records, list(LANE_RECORD_FIELDS)
            )
        summary = build_v39_summary(
            lifecycle_state="DEVELOPMENT_RESULT_CANDIDATE",
            fake_runner=summary_ctx.get("fake_runner", False),
            authorized_target_sha=summary_ctx.get("authorized_target_sha"),
            sha_binding=summary_ctx.get("sha_binding"),
            counts_provenance=summary_ctx.get("counts_provenance", {}),
            v31_identity=summary_ctx.get("v31_identity", {}),
            structural_rows=structural_rows,
            aggregates=None,
            gates=None,
            discordance=None,
            integrity_failures=failures,
            terminal_state=TERMINAL_EVIDENCE_INVALID,
            terminal_reason=None,
            completed_lane_records=lane_records,
            completed_baseline_records=baseline_records,
        )
        with (root / "v39_summary.json").open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        write_invalid_notice(root, failures, partial_records_retained=True)
    except Exception:  # never mask the original failure with writer problems
        pass
