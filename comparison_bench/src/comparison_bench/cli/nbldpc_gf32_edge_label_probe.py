"""Fixed-graph GF(32) edge-label EXPLORE batch.

This runner compares the accepted deep H0D control with one deterministic
row-major edge-label sweep under the same synthetic iid marginal-shape proxy.
It does not read empirical inputs or reconstruct a conditional channel.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from comparison_bench.cli import nbldpc_gf32_label_probe as prior_runner
from comparison_bench.cli import nbldpc_gf32_label_replica_probe as replica_runner
from comparison_bench.cli import nbldpc_gf32_shape_fine_probe as fine_runner
from comparison_bench.cli import nbldpc_gf32_search_depth_probe as search_depth
from comparison_bench.formal_ir import nbldpc_gf32_label_alignment as alignment
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as d10

predecessor = fine_runner.predecessor
CONTRACT = "NBLDPC-GF32-EDGE-LABEL-20261001/PREREG_AND_AUTH.md"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_edge_label_1efed423"
SEED_PREFIX = "gf32-edge-label-v1"
BATCH_UUID = "1efed423-10c8-4c51-a119-844f2b922ab5"
CONTROL_MAX_SWEEPS = search_depth.MAX_SWEEPS
EDGE_SWEEPS = 1

N = fine_runner.N
M = fine_runner.M
EDGE_COUNT = fine_runner.EDGE_COUNT
VAR_COUNTS = fine_runner.VAR_COUNTS
CHECK_COUNTS = fine_runner.CHECK_COUNTS
GRAPH_SEEDS = tuple(range(2026093901, 2026093907))
SHAPE_COUNTS = fine_runner.SHAPE_COUNTS
SHAPE_TOTAL = fine_runner.SHAPE_TOTAL
P0 = 0.550
P0_GRID = (P0,)
HOLDOUT_STREAMS = fine_runner.HOLDOUT_STREAMS
HOLDOUT_FRAMES_PER_STREAM = fine_runner.HOLDOUT_FRAMES_PER_STREAM
HOLDOUT_PAIRS = fine_runner.HOLDOUT_PAIRS
MAX_PILOT_CALLS = 0
MAX_HOLDOUT_CALLS = 2 * HOLDOUT_PAIRS
MAX_CALLS = MAX_HOLDOUT_CALLS
WALL_CAP_S = fine_runner.WALL_CAP_S
CALL_CAP_S = fine_runner.CALL_CAP_S
RSS_CAP_BYTES = fine_runner.RSS_CAP_BYTES
SYNDROME_BITS = 5 * M
SIGNAL_DELTA = fine_runner.SIGNAL_DELTA
SIGNAL_POSITIVE_GRAPHS = fine_runner.SIGNAL_POSITIVE_GRAPHS
CONTROL_MIN = fine_runner.CONTROL_MIN
CONTROL_MAX = fine_runner.CONTROL_MAX
FRAME_FIELDS = fine_runner.FRAME_FIELDS
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_edge_label_probe "
    "--execute --out-root workspace/gf32_edge_label_1efed423"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def shape_pmf_grid() -> list[dict[str, Any]]:
    """Return the sole frozen PMF, preserving the accepted five-bin shape."""
    q = np.zeros(32, dtype=np.float64)
    for symbol, count in SHAPE_COUNTS:
        q[symbol] = count / SHAPE_TOTAL
    if sum(count for _, count in SHAPE_COUNTS) != SHAPE_TOTAL:
        raise AssertionError("frozen source-shape counts do not sum to 4428")
    pmf = np.zeros(32, dtype=np.float64)
    pmf[0] = P0
    pmf += (1.0 - P0) * q
    pmf[0] = P0
    pmf = fine_runner.predecessor.alignment.validate_pmf(pmf)
    return [{
        "index": 0, "p0": P0,
        "formula": "p[0]=0.550; p[e]=0.450*count[e]/4428; "
                   "counts={1:2295,3:1126,7:557,15:304,31:146}",
        "entropy_bits": fine_runner.predecessor.alignment.entropy_bits(pmf),
        "nonzero_shape_entropy_bits":
            fine_runner.predecessor.alignment.entropy_bits(q),
        "support": [0, 1, 3, 7, 15, 31], "pmf": pmf,
    }]


def holdout_seed(graph_seed: int, stream: int, frame: int) -> int:
    return int(common.v10_seed(
        "%s:holdout:%d:%d:%d"
        % (SEED_PREFIX, int(graph_seed), int(stream), int(frame))))


def seed_plan() -> tuple[list[tuple[int, int, int, int]],
                          list[tuple[int, int, int, int]]]:
    holdouts = [
        (graph_seed, stream, frame,
         holdout_seed(graph_seed, stream, frame))
        for graph_seed in GRAPH_SEEDS
        for stream in HOLDOUT_STREAMS
        for frame in range(HOLDOUT_FRAMES_PER_STREAM)
    ]
    # Keep the established helper shape: the first list is explicitly empty.
    return [], holdouts


def arm_order(frame: int) -> tuple[str, str]:
    return fine_runner.arm_order(frame)


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() \
        else (root / requested).resolve()
    expected = (root / OUT_ROOT_RELATIVE).resolve()
    if resolved != expected:
        raise ValueError("out-root must equal the frozen fresh root %s" % expected)
    if resolved.exists():
        raise FileExistsError("refusing existing output root %s" % resolved)
    return resolved


def verify_t0() -> dict[str, bool]:
    """Pure field and fixed-PMF checks; no graph, decoder, input or writes."""
    checks = fine_runner.predecessor.verify_t0()
    for row in shape_pmf_grid():
        pmf = fine_runner.predecessor.alignment.validate_pmf(row["pmf"])
        if np.flatnonzero(pmf).tolist() != [0, 1, 3, 7, 15, 31]:
            raise AssertionError("edge-label PMF changed frozen sparse support")
        if not np.isclose(float(pmf.sum()), 1.0, rtol=0.0, atol=1e-12):
            raise AssertionError("edge-label PMF is not normalized")
        if not np.isclose(fine_runner.predecessor.alignment.entropy_bits(pmf),
                          float(row["entropy_bits"]), rtol=0.0, atol=1e-12):
            raise AssertionError("edge-label PMF entropy changed")
    checks["edge_label_fixed_shape_pmf"] = True
    base = np.ones((2, 2), dtype=np.int64)
    identity = gauge_diagnostics(base, base)
    row_scaled = np.asarray([[layout.gf32_mul(2, int(x)) for x in row]
                             for row in base], dtype=np.int64)
    column_scaled = alignment.scale_columns(base, [3, 5])
    row_column_scaled = np.asarray(
        [[layout.gf32_mul(2, int(x)) for x in row]
         for row in column_scaled], dtype=np.int64)
    if not identity["row_column_gauge_equivalent"]:
        raise AssertionError("identity gauge diagnostic failed")
    for transformed in (row_scaled, column_scaled, row_column_scaled):
        result = gauge_diagnostics(base, transformed)
        if not result["row_column_gauge_equivalent"]:
            raise AssertionError("row/column gauge transform was misclassified")
    changed_cycle = base.copy()
    changed_cycle[1, 1] = 2
    cycle_result = gauge_diagnostics(base, changed_cycle)
    if (cycle_result["row_column_gauge_equivalent"]
            or not cycle_result["cycle_class_changed"]
            or cycle_result["witness"] is None
            or int(cycle_result["witness"]["residual"]) == 1):
        raise AssertionError("closing-edge cycle witness was not detected")
    checks["row_column_gauge_and_cycle_witness"] = True
    return checks


# These accepted helpers accept a graph seed and do not bind the old seed list.
build_profile_graph = fine_runner.build_profile_graph
graph_preflight = fine_runner.graph_preflight

def _gf32_div(numerator: int, denominator: int) -> int:
    """Divide nonzero GF(32) values using the accepted field helpers."""
    inverse = int(alignment.column_inverse([int(denominator)])[0])
    return int(layout.gf32_mul(int(numerator), inverse))


def _row_entropy(coefficients: np.ndarray, pmf: np.ndarray) -> float:
    row = np.asarray(coefficients, dtype=np.int64)
    distribution = alignment.check_sum_pmf(
        pmf, row[row != 0].tolist())
    return float(alignment.entropy_bits(distribution))


def edge_sweep(matrix: np.ndarray, pmf: np.ndarray) -> dict[str, Any]:
    """Perform one deterministic row-major absolute-label sweep over edges."""
    h = np.asarray(matrix, dtype=np.int64).copy()
    p = alignment.validate_pmf(pmf)
    if h.ndim != 2 or h.shape[0] == 0 or h.shape[1] == 0:
        raise ValueError("edge-label matrix must be nonempty and two-dimensional")
    if np.any(h < 0) or np.any(h >= alignment.Q):
        raise ValueError("edge-label matrix entries must lie in GF(32)")

    initial_j, _ = alignment.marginal_score(h, p)
    row_entropies = [
        _row_entropy(h[row], p) for row in range(h.shape[0])
    ]
    accumulated_j = float(initial_j)
    updates: list[dict[str, Any]] = []
    for row in range(h.shape[0]):
        for column in range(h.shape[1]):
            old = int(h[row, column])
            if old == 0:
                continue
            trial_scores: list[tuple[int, float]] = []
            score_by_beta: dict[int, float] = {}
            trial_row = h[row].copy()
            for beta in range(1, alignment.Q):
                trial_row[column] = beta
                score = _row_entropy(trial_row, p)
                trial_scores.append((beta, score))
                score_by_beta[beta] = score
            selected = int(alignment.choose_label(
                trial_scores, old, alignment.TIE_TOL))
            new_entropy = float(score_by_beta[selected])
            accumulated_j += new_entropy - row_entropies[row]
            changed = selected != old
            if changed:
                h[row, column] = selected
            row_entropies[row] = new_entropy
            updates.append({
                "row": int(row), "column": int(column), "old": old,
                "chosen": selected, "changed": bool(changed),
            })

    final_j, _ = alignment.marginal_score(h, p)
    reference_drift = float(final_j - accumulated_j)
    j_decrease = float(final_j - initial_j)
    stop_reasons: list[str] = []
    if abs(reference_drift) > 1e-10:
        stop_reasons.append("FULL_J_INCREMENT_DRIFT")
    if j_decrease < -1e-10:
        stop_reasons.append("MATERIAL_J_DECREASE")
    return {
        "matrix": h,
        "initial_J_bits": float(initial_j),
        "J_bits": float(final_j),
        "accumulated_J_bits": float(accumulated_j),
        "reference_drift_bits": reference_drift,
        "J_change_bits": j_decrease,
        "updates": updates,
        "changed_edge_count": sum(bool(row["changed"]) for row in updates),
        "sweep_count": EDGE_SWEEPS,
        "construction_stop": bool(stop_reasons),
        "failure_reason": ",".join(stop_reasons),
    }


def gauge_diagnostics(control: np.ndarray,
                      candidate: np.ndarray) -> dict[str, Any]:
    """Test full row/column GF(32) gauge equivalence on fixed support."""
    a = np.asarray(control, dtype=np.int64)
    b = np.asarray(candidate, dtype=np.int64)
    if (a.ndim != 2 or b.ndim != 2 or a.shape != b.shape
            or a.shape[0] == 0 or a.shape[1] == 0):
        raise ValueError("gauge matrices must be nonempty and have equal shape")
    if (np.any(a < 0) or np.any(a >= alignment.Q)
            or np.any(b < 0) or np.any(b >= alignment.Q)):
        raise ValueError("gauge matrix entries must lie in GF(32)")
    support_a = a != 0
    support_b = b != 0
    base: dict[str, Any] = {
        "support_equal": bool(np.array_equal(support_a, support_b)),
        "tree_edges": [],
        "row_potentials": [None] * int(a.shape[0]),
        "column_potentials": [None] * int(a.shape[1]),
        "non_tree_residuals": [],
        "nonunit_residual_count": None,
        "witness": None,
        "row_column_gauge_equivalent": None,
        "cycle_class_changed": None,
        "construction_stop": False,
        "failure_reason": "",
    }
    if not base["support_equal"]:
        base["construction_stop"] = True
        base["failure_reason"] = "GAUGE_SUPPORT_MISMATCH"
        return base

    edge_rows = np.flatnonzero(support_a.any(axis=1)).tolist()
    edge_columns = np.flatnonzero(support_a.any(axis=0)).tolist()
    if not edge_rows or not edge_columns:
        base["construction_stop"] = True
        base["failure_reason"] = "GAUGE_ZERO_SUPPORT"
        return base
    ratios: dict[tuple[int, int], int] = {}
    rows_by_column = [np.flatnonzero(support_a[:, col]).tolist()
                      for col in range(a.shape[1])]
    columns_by_row = [np.flatnonzero(support_a[row]).tolist()
                      for row in range(a.shape[0])]
    for row in range(a.shape[0]):
        for column in columns_by_row[row]:
            if int(a[row, column]) == 0 or int(b[row, column]) == 0:
                base["construction_stop"] = True
                base["failure_reason"] = "GAUGE_ZERO_EDGE"
                return base
            ratios[(row, column)] = _gf32_div(
                int(b[row, column]), int(a[row, column]))

    row_potentials: list[int | None] = [None] * int(a.shape[0])
    column_potentials: list[int | None] = [None] * int(a.shape[1])
    tree_edges: set[tuple[int, int]] = set()
    # The frozen support is connected. Retain a forest-style traversal so a
    # disconnected synthetic fixture returns an explicit STOP diagnostic.
    row_potentials[0] = 1
    queue: list[tuple[str, int]] = [("row", 0)]
    cursor = 0
    while cursor < len(queue):
        kind, node = queue[cursor]
        cursor += 1
        if kind == "row":
            row = node
            for column in columns_by_row[row]:
                if column_potentials[column] is None:
                    column_potentials[column] = _gf32_div(
                        ratios[(row, column)], int(row_potentials[row]))
                    tree_edges.add((row, column))
                    queue.append(("column", column))
        else:
            column = node
            for row in rows_by_column[column]:
                if row_potentials[row] is None:
                    row_potentials[row] = _gf32_div(
                        ratios[(row, column)], int(column_potentials[column]))
                    tree_edges.add((row, column))
                    queue.append(("row", row))

    reached = (all(value is not None and int(value) != 0
                   for value in row_potentials)
               and all(value is not None and int(value) != 0
                       for value in column_potentials))
    if not reached:
        base.update({
            "tree_edges": [list(edge) for edge in sorted(tree_edges)],
            "row_potentials": row_potentials,
            "column_potentials": column_potentials,
            "construction_stop": True,
            "failure_reason": "GAUGE_UNREACHED_SUPPORT_VERTEX",
        })
        return base

    non_tree_residuals: list[dict[str, Any]] = []
    for row in range(a.shape[0]):
        for column in columns_by_row[row]:
            if (row, column) in tree_edges:
                continue
            predicted = int(layout.gf32_mul(
                int(row_potentials[row]), int(column_potentials[column])))
            actual = int(ratios[(row, column)])
            residual = _gf32_div(actual, predicted)
            non_tree_residuals.append({
                "row": int(row), "column": int(column),
                "ratio": actual, "predicted": predicted,
                "residual": residual,
            })
    witnesses = [row for row in non_tree_residuals
                 if int(row["residual"]) != 1]
    base.update({
        "tree_edges": [list(edge) for edge in sorted(tree_edges)],
        "row_potentials": [int(value) for value in row_potentials],
        "column_potentials": [int(value) for value in column_potentials],
        "non_tree_residuals": non_tree_residuals,
        "nonunit_residual_count": len(witnesses),
        "witness": dict(witnesses[0]) if witnesses else None,
        "row_column_gauge_equivalent": not bool(witnesses),
        "cycle_class_changed": bool(witnesses),
    })
    return base


build_profile_graph = search_depth.build_profile_graph
graph_preflight = search_depth.graph_preflight


def candidate_builder(
        dense: np.ndarray, pmf: np.ndarray, graph_seed: int
        ) -> tuple[np.ndarray | None, np.ndarray | None, dict[str, Any]]:
    """Build accepted deep H0D control and its one-pass edge-label candidate."""
    h0 = np.asarray(dense, dtype=np.int64)
    p = alignment.validate_pmf(pmf)
    onepass, control, control_diagnostics = search_depth.build_candidate_pair(
        h0, p, int(graph_seed))
    diagnostics: dict[str, Any] = {
        "graph_seed": int(graph_seed),
        "control_admitted": False,
        "candidate_admitted": False,
        "construction_stop": False,
        "control_search": control_diagnostics,
        "edge_sweep": None,
        "gauge": None,
    }
    if (onepass is None or control is None
            or control_diagnostics.get("construction_stop")
            or not control_diagnostics.get("deep_candidate_admitted", False)):
        diagnostics["construction_stop"] = True
        diagnostics["failure_reason"] = (
            control_diagnostics.get("failure_reason")
            or "CONTROL_DEEP_RECONSTRUCTION_STOP")
        return control, None, diagnostics

    diagnostics["control_admitted"] = True
    edge_result = edge_sweep(control, p)
    edge_matrix = np.asarray(edge_result["matrix"], dtype=np.int64)
    gauge = gauge_diagnostics(control, edge_matrix)
    base_rank = int(d10.gf32_row_rank(control))
    candidate_rank = int(d10.gf32_row_rank(edge_matrix))
    support_equal = bool(np.array_equal(control != 0, edge_matrix != 0))
    degrees_equal = bool(
        np.array_equal(np.count_nonzero(control, axis=0),
                       np.count_nonzero(edge_matrix, axis=0))
        and np.array_equal(np.count_nonzero(control, axis=1),
                           np.count_nonzero(edge_matrix, axis=1)))
    diagnostics.update({
        "edge_sweep": {key: value for key, value in edge_result.items()
                       if key != "matrix"},
        "gauge": gauge,
        "control_J_bits": float(alignment.marginal_score(control, p)[0]),
        "candidate_J_initial_bits": float(edge_result["initial_J_bits"]),
        "candidate_J_bits": float(edge_result["J_bits"]),
        "candidate_J_gain_bits": float(edge_result["J_change_bits"]),
        "control_rank": base_rank,
        "candidate_rank": candidate_rank,
        "support_equal": support_equal,
        "degrees_equal": degrees_equal,
        "candidate_nontrivial": bool(np.any(edge_matrix != control)),
        "row_column_gauge_equivalent": gauge.get(
            "row_column_gauge_equivalent"),
        "cycle_class_changed": gauge.get("cycle_class_changed"),
        "nonunit_residual_count": gauge.get("nonunit_residual_count"),
        "gauge_witness": gauge.get("witness"),
    })
    valid_structure = bool(support_equal and degrees_equal
                           and base_rank == M and candidate_rank == M)
    diagnostics["candidate_admitted"] = valid_structure
    if edge_result["construction_stop"] or gauge["construction_stop"]:
        diagnostics["construction_stop"] = True
        diagnostics["failure_reason"] = (
            edge_result.get("failure_reason")
            or gauge.get("failure_reason")
            or "EDGE_CANDIDATE_CONSTRUCTION_STOP")
    elif not valid_structure:
        diagnostics["construction_stop"] = True
        diagnostics["failure_reason"] = "EDGE_CANDIDATE_STRUCTURE_STOP"
    return control, edge_matrix, diagnostics


def _candidate_pair_for_graph(
        dense: np.ndarray, pmf: np.ndarray, graph_seed: int
        ) -> tuple[np.ndarray | None, np.ndarray | None, dict[str, Any]]:
    return candidate_builder(dense, pmf, graph_seed)


def _validate_seed_plan() -> tuple[list[tuple[int, int, int, int]],
                                   list[tuple[int, int, int, int]]]:
    pilots, holdouts = seed_plan()
    seeds = [row[3] for row in holdouts]
    old_seed_sets = []
    # Prior accepted label batch, four-point fd01 batch and fine-grid batch.
    old_seed_sets.append({row[3] for plan in prior_runner._seed_plan()
                          for row in plan})
    old_seed_sets.append({row[3] for plan in
                          fine_runner.predecessor.seed_plan() for row in plan})
    old_seed_sets.append({row[3] for plan in fine_runner.seed_plan()
                          for row in plan})
    old_seed_sets.append({row[3] for plan in replica_runner.seed_plan()
                          for row in plan})
    old_seed_sets.append({row[3] for plan in search_depth.seed_plan()
                          for row in plan})
    if (pilots or len(holdouts) != HOLDOUT_PAIRS
            or len(set(seeds)) != len(seeds)
            or any(set(seeds) & old for old in old_seed_sets)):
        raise AssertionError("edge-label seed plan overlaps a prior batch")
    return pilots, holdouts


def _serialized_grid() -> list[dict[str, Any]]:
    return [{key: value for key, value in row.items() if key != "pmf"}
            for row in shape_pmf_grid()]


def _initial_manifest(command: str) -> dict[str, Any]:
    _, holdouts = _validate_seed_plan()
    return {
        "track": "EXPLORE", "batch_uuid": BATCH_UUID,
        "contract": CONTRACT, "status": "RUNNING",
        "graph_profile": {
            "n": N, "m": M, "E": EDGE_COUNT,
            "variable_degrees": VAR_COUNTS,
            "check_degrees": CHECK_COUNTS,
            "field": "GF(32)/polynomial-37",
            "constructor": "v72p2d10_mixed_degree_l1.build_degree_sequence_peg",
            "coefficient_rule": (
                "coefficients_for_edges(edges, width=128, graph_seed); "
                "original D10 d10:coeff:128:{graph_seed} stream"),
            "graph_seeds": list(GRAPH_SEEDS),
            "cross_batch_baseline": False,
        },
        "source_shape_proxy": {
            "source": "accepted historical 2M aggregate summary only",
            "counts": {str(e): c for e, c in SHAPE_COUNTS},
            "total": SHAPE_TOTAL,
            "role": "synthetic iid marginal shape proxy",
            "not_conditional_channel_reconstruction": True,
            "no_empirical_input_reads": True,
        },
        "pmf": _serialized_grid()[0],
        "pmf_index": 0, "fixed_p0": P0, "pilot": "NOT_RUN_FIXED_PMF",
        "seed_namespace": SEED_PREFIX,
        "seed_plan_counts": {"pilot": 0, "holdout_pairs": len(holdouts)},
        "seed_plan_disjoint_from_prior_batches": True,
        "decoder_profile": (
            "v35 row-layered FFT-QSPA; max_iter=90; damping_alpha=1.0; "
            "warm_beliefs=None; field=None via accepted adapter; prior zeros "
            "are floored to 1e-15 and row-renormalized internally"),
        "pairing": "same sampled error and same repeated PMF prior; own syndrome per arm",
        "arm_mapping": {
            "control": "accepted deep H0D rebuilt by search-depth helper",
            "candidate": "one row-major absolute edge-label sweep from control",
        },
        "arm_order": "control first on even frame, edge candidate first on odd",
        "label_search": {
            "objective": "sum of check-marginal entropies J(H,p)",
            "control": (
                "accepted search-depth deep H0D; max 8 total column sweeps "
                "including accepted first pass; stop on no-change"),
            "candidate": "one row-major sweep over every nonzero edge from control",
            "max_control_total_sweeps": CONTROL_MAX_SWEEPS,
            "candidate_sweep_count": EDGE_SWEEPS,
            "edge_order": "row-major nonzero matrix entries",
            "beta_order": "absolute GF32 edge coefficients 1..31",
            "tie_tolerance": alignment.TIE_TOL,
            "tie_rule": "retain current label if tied, otherwise smallest tied label",
            "rank_filter_during_optimization": False,
            "post_sweep_stops": [
                "full J versus accumulated row increments drift >1e-10 bits",
                "J decrease >1e-10 bits",
                "support/degrees/rank52 failure",
                "invalid/disconnected full row-column gauge support",
            ],
            "gauge_test": (
                "GF32 edge ratios on common support; deterministic BFS "
                "spanning-tree potentials from row0 and all chord residuals"),
            "gauge_or_j_gain_is_admission_filter": False,
        },
        "frame_stream": (
            "v10_seed('gf32-edge-label-v1:holdout:{graph_seed}:"
            "{stream}:{frame}')"),
        "error_sampling": "numpy.default_rng(seed).choice(32,size=128,p=pmf)",
        "budgets": {
            "total_wall_s": WALL_CAP_S, "per_decoder_call_s": CALL_CAP_S,
            "rss_bytes": RSS_CAP_BYTES, "max_pilot_calls": MAX_PILOT_CALLS,
            "max_holdout_calls": MAX_HOLDOUT_CALLS,
            "max_decoder_calls": MAX_CALLS,
            "max_control_total_sweeps_per_graph": CONTROL_MAX_SWEEPS,
            "edge_label_sweeps_per_graph": EDGE_SWEEPS,
        },
        "accounting": {
            "syndrome_bits_per_attempt": SYNDROME_BITS,
            "tag_bits": 0, "verification_status": "NOT_IMPLEMENTED",
            "undetected_status": "NOT_MEASURED",
            "success": "exact AND syndrome_accept",
            "wrong": "syndrome_accept AND NOT exact; separately recorded failure",
            "truth_prior_and_conditional_arrays_saved": False,
        },
        "exact_command": command or COMMAND,
        "attempted_decoder_calls": 0,
        "attempted_call_counts": {"pilot": 0, "holdout": 0, "total": 0},
        "stop_reason": "", "graph_diagnostics": [],
        "candidate_diagnostics": [],
        "dirty_tree_reference_uuid": BATCH_UUID,
    }


def _start_outputs(root: Path, manifest: dict[str, Any]) -> None:
    root.mkdir(parents=False, exist_ok=False)
    fine_runner.predecessor._write_json(root / "manifest.json", manifest)
    with (root / "frame_records.csv").open(
            "w", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=FRAME_FIELDS).writeheader()
    with (root / "summary.json").open("w", encoding="utf-8") as stream:
        json.dump({"status": "RUNNING"}, stream)
        stream.write("\n")
    with (root / "EXPLORATION_LOG.md").open("w", encoding="utf-8") as stream:
        stream.write("# GF32 edge-label EXPLORE log\n\n")
        stream.write("Batch UUID: `%s`. Independent batch-end review: pending.\n"
                     % BATCH_UUID)


def _append_log(root: Path, message: str) -> None:
    fine_runner.predecessor._append_log(root, message)


def _append_row(root: Path, row: Mapping[str, Any]) -> None:
    fine_runner._append_row(root, row)


def _summarize(rows: list[dict[str, Any]],
               completed_pairs: list[dict[str, Any]],
               stop_reason: str,
               candidate_diagnostics: list[dict[str, Any]] | None = None
               ) -> dict[str, Any]:
    """Aggregate only the six frozen graph seeds; mask partial denominators."""
    holdout_rows = [row for row in rows if row["phase"] == "holdout"]
    completed = len(completed_pairs) == HOLDOUT_PAIRS
    success = lambda row: bool(row["exact"] and row["syndrome_accept"])
    control_rows = [row for row in holdout_rows if row["arm"] == "control"]
    candidate_rows = [row for row in holdout_rows if row["arm"] == "candidate"]
    control_successes = sum(success(row) for row in control_rows)
    candidate_successes = sum(success(row) for row in candidate_rows)
    diagnostics_by_seed = {
        str(diagnostic.get("graph_seed")): diagnostic
        for diagnostic in (candidate_diagnostics or [])
    }
    per_graph: dict[str, Any] = {}
    for graph_seed in GRAPH_SEEDS:
        graph_rows = [row for row in holdout_rows
                      if int(row["graph_seed"]) == graph_seed]
        graph_pairs = [pair for pair in completed_pairs
                       if int(pair["graph_seed"]) == graph_seed]
        c_rows = [row for row in graph_rows if row["arm"] == "control"]
        k_rows = [row for row in graph_rows if row["arm"] == "candidate"]
        if completed:
            c_success = sum(success(row) for row in c_rows)
            k_success = sum(success(row) for row in k_rows)
            per_graph[str(graph_seed)] = {
                "completed_pairs": len(graph_pairs),
                "control_attempts": len(c_rows), "candidate_attempts": len(k_rows),
                "control_exact": int(c_success),
                "candidate_exact": int(k_success),
                "delta_g": int(k_success - c_success),
            }
        else:
            per_graph[str(graph_seed)] = {
                "completed_pairs": len(graph_pairs),
                "control_attempts": len(c_rows), "candidate_attempts": len(k_rows),
                "control_exact": None, "candidate_exact": None,
                "delta_g": None,
            }
        diagnostic = diagnostics_by_seed.get(str(graph_seed), {})
        gauge = diagnostic.get("gauge") or {}
        per_graph[str(graph_seed)].update({
            "cycle_class_changed": gauge.get("cycle_class_changed"),
            "row_column_gauge_equivalent":
                gauge.get("row_column_gauge_equivalent"),
            "nonunit_residual_count": gauge.get("nonunit_residual_count"),
            "gauge_witness": gauge.get("witness"),
            "positive_delta_without_cycle_change": (
                bool(per_graph[str(graph_seed)]["delta_g"] > 0
                     and gauge.get("cycle_class_changed") is False)
                if completed and per_graph[str(graph_seed)]["delta_g"] is not None
                and gauge.get("cycle_class_changed") is not None else None),
        })

    integrity = sum(
        str(row["status"]).startswith("integrity_error")
        or str(row["status"]).startswith("decoder_exception")
        for row in rows)
    resources = sum(
        str(row["status"]).startswith("resource_abort")
        or "|resource_abort:" in str(row["status"])
        for row in rows)
    authorization = 0
    cycle_changed_graph_count = (
        sum(bool(diagnostic.get("cycle_class_changed"))
            for diagnostic in (candidate_diagnostics or []))
        if len(candidate_diagnostics or []) == len(GRAPH_SEEDS) else None)
    if not completed:
        classification = "INCOMPLETE"
        states = None
        control_value = candidate_value = delta = None
    else:
        control_value = int(control_successes)
        candidate_value = int(candidate_successes)
        delta = int(candidate_successes - control_successes)
        states = {"control_only": 0, "candidate_only": 0,
                  "both": 0, "neither": 0}
        for pair in completed_pairs:
            c, k = bool(pair["control_exact"]), bool(pair["candidate_exact"])
            key = {(True, False): "control_only", (False, True): "candidate_only",
                   (True, True): "both", (False, False): "neither"}[(c, k)]
            states[key] += 1
        if not CONTROL_MIN <= control_successes <= CONTROL_MAX:
            classification = "CONTROL_RANGE_UNINFORMATIVE"
        elif (delta >= SIGNAL_DELTA
              and sum(value["delta_g"] > 0 for value in per_graph.values())
              >= SIGNAL_POSITIVE_GRAPHS
              and cycle_changed_graph_count is not None
              and cycle_changed_graph_count >= SIGNAL_POSITIVE_GRAPHS
              and integrity == 0 and resources == 0
              and authorization == 0):
            classification = "MECHANISM_SIGNAL"
        else:
            classification = "NO_SUFFICIENT_SIGNAL"

    gauge_by_graph = {
        str(diagnostic.get("graph_seed")): diagnostic.get("gauge")
        for diagnostic in (candidate_diagnostics or [])
    }
    edge_diagnostics_by_graph = {
        str(diagnostic.get("graph_seed")): {
            "control_J_bits": diagnostic.get("control_J_bits"),
            "candidate_initial_J_bits": diagnostic.get("candidate_J_initial_bits"),
            "candidate_final_J_bits": diagnostic.get("candidate_J_bits"),
            "candidate_J_gain_bits": diagnostic.get("candidate_J_gain_bits"),
            "edge_sweep_count": (diagnostic.get("edge_sweep") or {}).get(
                "sweep_count"),
            "changed_edge_count": (diagnostic.get("edge_sweep") or {}).get(
                "changed_edge_count"),
            "construction_stop": diagnostic.get("construction_stop"),
        }
        for diagnostic in (candidate_diagnostics or [])
    }

    return {
        "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "classification": classification, "stop_reason": stop_reason,
        "holdout_complete": completed,
        "holdout_pairs_completed": len(completed_pairs),
        "pilot_control_exact_by_pmf": {},
        "fixed_p0": P0, "fixed_pmf_index": 0, "selected_pmf_index": None,
        "p0_grid": list(P0_GRID), "seed_namespace": SEED_PREFIX,
        "control_exact": control_value,
        "candidate_exact": candidate_value, "delta": delta,
        "delta_by_graph": per_graph, "paired_states": states,
        "cycle_changed_graphs": cycle_changed_graph_count,
        "cycle_class_screen_minimum": SIGNAL_POSITIVE_GRAPHS,
        "gauge_by_graph": gauge_by_graph,
        "edge_diagnostics_by_graph": edge_diagnostics_by_graph,
        "search_diagnostics": candidate_diagnostics or [],
        "syndrome_consistent_wrong_rows": sum(
            bool(row["syndrome_consistent_wrong"]) for row in rows),
        "syndrome_consistent_wrong_by_arm": {
            arm: sum(bool(row["syndrome_consistent_wrong"])
                     for row in rows if row["arm"] == arm)
            for arm in ("control", "candidate")},
        "integrity_violations": int(integrity),
        "resource_violations": int(resources),
        "authorization_violations": int(authorization),
        "syndrome_bits_per_attempt": SYNDROME_BITS,
        "tag_bits": 0, "verification_status": "NOT_IMPLEMENTED",
        "undetected_status": "NOT_MEASURED",
        "FER": None, "f_eff": None, "SKR": None,
        "claim_ceiling": (
            "synthetic iid marginal-shape proxy on the six fixed graphs with "
            "a new holdout namespace; no pooled cross-batch result, conditional "
            "channel, FER, f_eff, SKR, throughput, qualification, or route claim"),
    }


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root)
    t0 = verify_t0()
    pilots, holdouts = _validate_seed_plan()
    return {
        "status": "DRY_RUN", "out_root": str(root),
        "writes": 0, "empirical_input_reads": 0,
        "graph_construction_calls": 0, "decoder_calls": 0,
        "t0": t0, "fixed_p0": P0,
        "max_control_total_sweeps_per_graph": CONTROL_MAX_SWEEPS,
        "edge_label_sweeps_per_graph": EDGE_SWEEPS,
        "pilot_call_ceiling": MAX_PILOT_CALLS,
        "holdout_pair_count": len(holdouts),
        "holdout_call_count": MAX_HOLDOUT_CALLS,
        "maximum_call_count": MAX_CALLS,
        "pilot_seed_count": len(pilots), "holdout_seed_count": len(holdouts),
        "holdout_seeds_disjoint_from_prior_batches": True,
        "profile": {"n": N, "m": M, "E": EDGE_COUNT},
    }


def _resource_stop(started: float, now: Callable[[], float],
                   rss_fn: Callable[[], int | None]) -> str:
    if max(float(now()) - float(started), 0.0) >= WALL_CAP_S:
        return "total_wall_cap_before_next_call"
    rss = rss_fn()
    if rss is not None and int(rss) >= RSS_CAP_BYTES:
        return "rss_cap_before_next_call"
    return ""


def execute_batch(*, out_root: str | Path, decode_fn,
                  graph_builder: Callable[[int], Mapping[str, Any]],
                  command: str = COMMAND,
                  repo_root: str | Path | None = None,
                  now: Callable[[], float] = time.perf_counter,
                  rss_fn: Callable[[], int | None] | None = None,
                  candidate_builder: Callable[[np.ndarray, np.ndarray, int],
                                              tuple[np.ndarray | None,
                                                    np.ndarray | None,
                                                    dict[str, Any]]] | None = None
                  ) -> dict[str, Any]:
    if decode_fn is None or not callable(decode_fn):
        raise ValueError("an explicit decoder callable is required")
    if graph_builder is None or not callable(graph_builder):
        raise ValueError("an explicit graph builder is required")
    build_candidates = candidate_builder or _candidate_pair_for_graph
    root = validate_out_root(out_root, repo_root=repo_root)
    if rss_fn is None:
        rss_fn = fine_runner.predecessor.d5._rss_bytes
    started = float(now())
    manifest = _initial_manifest(command)
    _start_outputs(root, manifest)
    rows: list[dict[str, Any]] = []
    completed_pairs: list[dict[str, Any]] = []
    graph_diagnostics: list[dict[str, Any]] = []
    candidate_diagnostics: list[dict[str, Any]] = []
    graphs: dict[int, np.ndarray] = {}
    control_candidates: dict[int, np.ndarray] = {}
    edge_candidates: dict[int, np.ndarray] = {}
    calls = 0
    stop_reason = ""
    terminal = "INCOMPLETE"

    def finish() -> dict[str, Any]:
        summary = _summarize(rows, completed_pairs, stop_reason,
                             candidate_diagnostics)
        summary.update({
            "terminal_status": terminal,
            "attempted_decoder_calls": calls,
            "attempted_frame_rows": len(rows),
            "attempted_call_counts": {
                "pilot": 0,
                "holdout": sum(row["phase"] == "holdout" for row in rows),
                "total": calls,
            },
            "batch_wall_s": max(float(now()) - started, 0.0),
            "actual_syndrome_disclosure_bits": calls * SYNDROME_BITS,
        })
        fine_runner.predecessor._write_json(root / "summary.json", summary)
        manifest.update({
            "status": terminal,
            "attempted_decoder_calls": calls,
            "attempted_call_counts": summary["attempted_call_counts"],
            "attempted_frame_rows": len(rows), "stop_reason": stop_reason,
            "batch_wall_s": summary["batch_wall_s"],
            "graph_diagnostics": graph_diagnostics,
            "candidate_diagnostics": candidate_diagnostics,
        })
        fine_runner.predecessor._write_json(root / "manifest.json", manifest)
        _append_log(root, "terminal=%s stop_reason=%s calls=%d rows=%d"
                    % (terminal, stop_reason or "none", calls, len(rows)))
        return summary

    def record_row(graph_seed: int, stream: int, frame: int, seed: int,
                   arm: str, observed: Mapping[str, Any]) -> dict[str, Any]:
        pmf = shape_pmf_grid()[0]
        row = fine_runner.predecessor._record_row(
            call_index=calls, phase="holdout", pmf=pmf,
            graph_seed=graph_seed, stream=stream, frame=frame, seed=seed,
            arm=arm, observed=observed)
        rows.append(row)
        _append_row(root, row)
        return row

    def dispatch(graph_seed: int, stream: int, frame: int, seed: int,
                 arm: str, dense: np.ndarray, prior: np.ndarray,
                 truth: np.ndarray, syndrome: np.ndarray
                 ) -> tuple[dict[str, Any] | None, str]:
        nonlocal calls
        if calls >= MAX_CALLS:
            return None, "decoder_call_count_cap_before_next_call"
        resource = _resource_stop(started, now, rss_fn)
        if resource:
            return None, resource
        calls += 1
        observed, issue = prior_runner.decode_observation(
            decode_fn, dense, prior, truth, syndrome, now=now, rss_fn=rss_fn)
        # The inherited helper misses post-return resource checks on exception;
        # apply every frozen cap here for every return path.
        resource_reasons = []
        if float(observed["wall_s"]) > CALL_CAP_S:
            resource_reasons.append("decoder_call_wall_cap_after_return")
        if max(float(now()) - float(started), 0.0) > WALL_CAP_S:
            resource_reasons.append("total_wall_cap_after_call")
        if observed["rss_b"] is not None \
                and int(observed["rss_b"]) >= RSS_CAP_BYTES:
            resource_reasons.append("rss_cap_after_call")
        if resource_reasons:
            reason_text = ",".join(resource_reasons)
            issue = ";".join(part for part in
                              (str(issue) if issue else "", reason_text)
                              if part)
            status = str(observed["status"])
            if status.startswith("resource_abort"):
                observed["status"] = status + ":" + reason_text
            else:
                observed["status"] = status + "|resource_abort:" + reason_text
        row = record_row(graph_seed, stream, frame, seed, arm, observed)
        return row, issue

    try:
        _append_log(root, "T0 started; no graph or decoder call has occurred")
        try:
            t0 = verify_t0()
        except Exception as exc:
            stop_reason = "MATH_OR_MAPPING_FAILURE:%s:%s" % (
                type(exc).__name__, str(exc))
            terminal = "MATH_OR_MAPPING_FAILURE"
            return finish()
        manifest["t0"] = t0
        fine_runner.predecessor._write_json(root / "manifest.json", manifest)
        _append_log(root, "T0 PASS; fixed PMF and seed plan verified")

        graph_failure = False
        for graph_seed in GRAPH_SEEDS:
            resource = _resource_stop(started, now, rss_fn)
            if resource:
                stop_reason = resource
                terminal = "RESOURCE_STOP"
                graph_diagnostics.append({
                    "graph_seed": int(graph_seed), "status": "not_started",
                    "admitted": False, "failure_reason": resource,
                })
                graph_failure = True
                break
            graph = graph_builder(int(graph_seed))
            admitted, diagnostic = graph_preflight(graph, graph_seed)
            graph_diagnostics.append(diagnostic)
            if admitted:
                graphs[int(graph_seed)] = np.asarray(graph["dense"],
                                                    dtype=np.int64)
            else:
                graph_failure = True
            _append_log(root, "graph preflight seed=%d admitted=%s reason=%s"
                        % (graph_seed, admitted,
                           diagnostic.get("failure_reason", "")))
            resource = _resource_stop(started, now, rss_fn)
            if resource:
                stop_reason = resource
                terminal = "RESOURCE_STOP"
                graph_failure = True
                break
        if graph_failure or len(graphs) != len(GRAPH_SEEDS):
            if not stop_reason:
                stop_reason = "GRAPH_PREFLIGHT_FAILED"
                terminal = stop_reason
            return finish()

        pmf_entry = shape_pmf_grid()[0]
        pmf = pmf_entry["pmf"]
        prior = np.tile(pmf, (N, 1))
        for graph_seed in GRAPH_SEEDS:
            resource = _resource_stop(started, now, rss_fn)
            if resource:
                stop_reason = resource
                terminal = "RESOURCE_STOP"
                return finish()
            control, edge_candidate, diagnostic = build_candidates(
                graphs[graph_seed], pmf, graph_seed)
            candidate_diagnostics.append(diagnostic)
            edge_trace = diagnostic.get("edge_sweep") or {}
            gauge = diagnostic.get("gauge") or {}
            _append_log(
                root,
                "edge-label seed=%d control=%s candidate=%s updates=%s "
                "J_gain=%s cycle_changed=%s nonunit_residuals=%s"
                % (graph_seed,
                   diagnostic.get("control_admitted", control is not None),
                   diagnostic.get("candidate_admitted", edge_candidate is not None),
                   edge_trace.get("changed_edge_count"),
                   diagnostic.get("candidate_J_gain_bits"),
                   gauge.get("cycle_class_changed"),
                   gauge.get("nonunit_residual_count")))
            if not diagnostic.get("control_admitted", control is not None):
                stop_reason = diagnostic.get(
                    "failure_reason", "CONTROL_RECONSTRUCTION_STOP")
                terminal = "CONTROL_RECONSTRUCTION_STOP"
                return finish()
            if diagnostic.get("construction_stop"):
                stop_reason = diagnostic.get(
                    "failure_reason", "EDGE_CANDIDATE_CONSTRUCTION_STOP")
                terminal = "EDGE_CANDIDATE_CONSTRUCTION_STOP"
                return finish()
            if (control is None or edge_candidate is None
                    or not diagnostic.get("candidate_admitted", True)):
                stop_reason = diagnostic.get(
                    "failure_reason", "EDGE_CANDIDATE_ADMISSION_STOP")
                terminal = "EDGE_CANDIDATE_ADMISSION_STOP"
                return finish()
            control_candidates[graph_seed] = np.asarray(control, dtype=np.int64)
            edge_candidates[graph_seed] = np.asarray(edge_candidate, dtype=np.int64)
            resource = _resource_stop(started, now, rss_fn)
            if resource:
                stop_reason = resource
                terminal = "RESOURCE_STOP"
                return finish()
        if (len(control_candidates) != len(GRAPH_SEEDS)
                or len(edge_candidates) != len(GRAPH_SEEDS)):
            stop_reason = "CANDIDATE_CONSTRUCTION_INCOMPLETE"
            terminal = stop_reason
            return finish()

        _, holdout_plan = _validate_seed_plan()
        for graph_seed, stream, frame, seed in holdout_plan:
            truth = prior_runner.sample_error(seed, pmf, width=N)
            pair = prior_runner.paired_arm_data(
                control_candidates[graph_seed], edge_candidates[graph_seed],
                truth, prior)
            arm_results: dict[str, dict[str, Any]] = {}
            for arm in arm_order(frame):
                arm_input = pair[arm]
                row, issue = dispatch(
                    graph_seed, stream, frame, seed, arm,
                    arm_input["dense"], arm_input["prior"],
                    arm_input["truth"], arm_input["syndrome"])
                if row is not None:
                    arm_results[arm] = row
                if issue:
                    stop_reason = issue
                    terminal = ("RESOURCE_STOP" if "cap" in issue
                                or "wall" in issue or "rss" in issue
                                else "INTEGRITY_STOP")
                    return finish()
            if set(arm_results) == {"control", "candidate"}:
                arm_success = {
                    arm: bool(row["exact"] and row["syndrome_accept"])
                    for arm, row in arm_results.items()}
                completed_pairs.append({
                    "graph_seed": int(graph_seed), "stream": int(stream),
                    "frame": int(frame),
                    "control_exact": arm_success["control"],
                    "candidate_exact": arm_success["candidate"],
                })

        summary = _summarize(rows, completed_pairs, "",
                             candidate_diagnostics)
        terminal = str(summary["classification"])
        return finish()
    except Exception as exc:
        stop_reason = "implementation_exception:%s:%s" % (
            type(exc).__name__, str(exc))
        terminal = "IMPLEMENTATION_STOP"
        _append_log(root, stop_reason)
        finish()
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fixed-graph GF(32) edge-label EXPLORE probe")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true",
                      help="run the frozen synthetic batch")
    mode.add_argument("--dry-run", action="store_true",
                      help="check pure math and the output path")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE),
                        help="must equal the frozen fresh workspace root")
    return parser


def _bind_production_decoder():
    from comparison_bench.formal_ir.nbldpc_l1d2_production_decode import (
        production_decode_fn,
    )
    return production_decode_fn


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    root = validate_out_root(args.out_root)
    if not args.execute:
        result = dry_run(root)
    else:
        result = execute_batch(
            out_root=root, decode_fn=_bind_production_decoder(),
            graph_builder=build_profile_graph, command=COMMAND)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
