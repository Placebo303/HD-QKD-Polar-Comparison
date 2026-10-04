"""R2 source-aware edge-label EXPLORE probe for accepted GF(32) graphs.

The candidate performs one source-overlap coordinate pass from the accepted
deep H0D matrix. The paired batch is synthetic and keeps the graph support,
source marginal, prior, decoder and schedule fixed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from comparison_bench.cli.probes_closed import nbldpc_gf32_cycle_census as census
from comparison_bench.cli.probes_closed import nbldpc_gf32_cycle_source_overlap as source_overlap
from comparison_bench.cli.probes_closed import nbldpc_gf32_edge_label_probe as edge_runner
from comparison_bench.cli.probes_closed import nbldpc_gf32_label_probe as prior_runner
from comparison_bench.cli.probes_closed import nbldpc_gf32_search_depth_probe as search_runner
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as d10
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

CONTRACT = "NBLDPC-GF32-SOURCE-AWARE-LABEL-R2-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "358c49ba-4cab-4df2-b424-e17dad5bfe55"
PARENT_BATCH_UUID = "f6fbf8cf-8773-4099-af68-54136326b60d"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_source_label_r2_358c49ba"
CENSUS_ROOT_RELATIVE = census.OUT_ROOT_RELATIVE
OVERLAP_ROOT_RELATIVE = source_overlap.OUT_ROOT_RELATIVE
SEED_PREFIX = "gf32-source-label-v1"

N = edge_runner.N
M = edge_runner.M
EDGE_COUNT = edge_runner.EDGE_COUNT
GRAPH_SEEDS = tuple(edge_runner.GRAPH_SEEDS)
SHAPE_COUNTS = tuple(source_overlap.SHAPE_COUNTS)
SHAPE_TOTAL = int(source_overlap.SHAPE_TOTAL)
P0 = float(source_overlap.P0)
HOLDOUT_STREAMS = edge_runner.HOLDOUT_STREAMS
HOLDOUT_FRAMES_PER_STREAM = edge_runner.HOLDOUT_FRAMES_PER_STREAM
HOLDOUT_PAIRS = edge_runner.HOLDOUT_PAIRS
MAX_CALLS = 2 * HOLDOUT_PAIRS
WALL_CAP_S = edge_runner.WALL_CAP_S
CALL_CAP_S = edge_runner.CALL_CAP_S
RSS_CAP_BYTES = edge_runner.RSS_CAP_BYTES
SYNDROME_BITS = edge_runner.SYNDROME_BITS
CONTROL_MIN = edge_runner.CONTROL_MIN
CONTROL_MAX = edge_runner.CONTROL_MAX
SIGNAL_DELTA = edge_runner.SIGNAL_DELTA
SIGNAL_POSITIVE_GRAPHS = edge_runner.SIGNAL_POSITIVE_GRAPHS
MIN_REDUCED_GRAPHS = 4
TIE_TOL = 1e-14
REFERENCE_TOL = 1e-12
MAX_LABEL_TRIALS = EDGE_COUNT * 31 * len(GRAPH_SEEDS)
MAX_AFFECTED_CYCLE_EVALUATIONS = 2_000_000
FRAME_FIELDS = tuple(edge_runner.FRAME_FIELDS)
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.probes_closed.nbldpc_gf32_source_label_probe "
    "--execute --out-root workspace/gf32_source_label_r2_358c49ba"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def source_pmf() -> np.ndarray:
    """Return the accepted exact sparse iid PMF, without a decoder floor."""
    return source_overlap.source_pmf()


def pmf_entry() -> dict[str, Any]:
    return edge_runner.shape_pmf_grid()[0]


def holdout_seed(graph_seed: int, stream: int, frame: int) -> int:
    return int(common.v10_seed(
        "%s:holdout:%d:%d:%d"
        % (SEED_PREFIX, int(graph_seed), int(stream), int(frame))))


def seed_plan() -> tuple[list[tuple[int, int, int, int]],
                          list[tuple[int, int, int, int]]]:
    holdouts = [
        (seed, stream, frame, holdout_seed(seed, stream, frame))
        for seed in GRAPH_SEEDS for stream in HOLDOUT_STREAMS
        for frame in range(HOLDOUT_FRAMES_PER_STREAM)
    ]
    return [], holdouts


def arm_order(frame: int) -> tuple[str, str]:
    return edge_runner.arm_order(frame)


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


def _validate_seed_plan() -> tuple[list[tuple[int, int, int, int]],
                                   list[tuple[int, int, int, int]]]:
    pilots, holdouts = seed_plan()
    seeds = {row[3] for row in holdouts}
    old_plans = (
        [row for plan in prior_runner._seed_plan() for row in plan],
        [row for plan in edge_runner.fine_runner.predecessor.seed_plan()
         for row in plan],
        [row for plan in edge_runner.fine_runner.seed_plan() for row in plan],
        [row for plan in edge_runner.replica_runner.seed_plan() for row in plan],
        [row for plan in search_runner.seed_plan() for row in plan],
        [row for plan in edge_runner.seed_plan() for row in plan],
    )
    if (pilots or len(holdouts) != HOLDOUT_PAIRS
            or len(seeds) != HOLDOUT_PAIRS
            or any(seeds & {int(row[3]) for row in plan} for plan in old_plans)):
        raise AssertionError("source-label seed plan is incomplete or overlaps")
    return pilots, holdouts


def _plain(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(_plain(value), stream, indent=2, sort_keys=True)
        stream.write("\n")


def _load_cycle_inventory(repo_root: str | Path,
                          controls: Mapping[int, np.ndarray]
                          ) -> dict[int, list[dict[str, Any]]]:
    """Load accepted derived inventories and bind each saved control edge."""
    root = Path(repo_root).resolve()
    census_root = root / CENSUS_ROOT_RELATIVE
    overlap_root = root / OVERLAP_ROOT_RELATIVE
    accepted_census = source_overlap.load_predecessor(census_root)
    overlap_manifest = json.loads(
        (overlap_root / "manifest.json").read_text(encoding="utf-8"))
    overlap_summary = json.loads(
        (overlap_root / "summary.json").read_text(encoding="utf-8"))
    if (overlap_manifest.get("batch_uuid") != source_overlap.BATCH_UUID
            or overlap_manifest.get("status") != "OVERLAP_COMPLETE"
            or overlap_manifest.get("input_batch_uuid") != census.BATCH_UUID
            or overlap_summary.get("batch_uuid") != source_overlap.BATCH_UUID
            or overlap_summary.get("terminal_status") != "OVERLAP_COMPLETE"
            or overlap_summary.get("batch_complete") is not True
            or overlap_summary.get("reference_batch_uuid") != census.BATCH_UUID
            or overlap_summary.get("input_rows_processed")
                != accepted_census["expected_rows"]):
        raise ValueError("source-overlap predecessor is not the accepted complete batch")

    expected_rows: dict[tuple[int, tuple[int, ...]], dict[str, str]] = {}
    census_path = census_root / "cycles.csv"
    with census_path.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            key = (int(row["graph_seed"]),
                   tuple(int(x) for x in json.loads(row["cycle_key_json"])))
            if key in expected_rows:
                raise ValueError("census contains a duplicate canonical cycle")
            expected_rows[key] = row
    if len(expected_rows) != accepted_census["expected_rows"]:
        raise ValueError("census CSV row count differs from its accepted summary")

    by_seed: dict[int, list[dict[str, Any]]] = {seed: [] for seed in GRAPH_SEEDS}
    seen_rows: set[tuple[int, tuple[int, ...]]] = set()
    supports: dict[int, set[tuple[int, ...]]] = {seed: set() for seed in GRAPH_SEEDS}
    counts: dict[tuple[int, int], int] = {}
    overlap_path = overlap_root / "source_overlap.csv"
    with overlap_path.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            seed = int(row["graph_seed"])
            key_tuple = tuple(int(x) for x in json.loads(row["cycle_key_json"]))
            key = (seed, key_tuple)
            if key in seen_rows or key not in expected_rows:
                raise ValueError("overlap rows do not exactly match census cycles")
            seen_rows.add(key)
            if row.get("row_status") != "OK" or row.get("failure_reason"):
                raise ValueError("accepted overlap row contains a failed cycle")
            verified = source_overlap.verify_cycle_row(row)
            census_row = expected_rows[key]
            for name in ("ell", "check_rows_json", "variable_columns_json",
                         "control_numerator_coefficients_json",
                         "control_denominator_coefficients_json"):
                if row[name] != census_row[name]:
                    raise ValueError("overlap row differs from canonical census field %s" % name)
            rows = [int(x) for x in verified["rows"]]
            variables = [int(x) for x in verified["variables"]]
            if seed not in controls:
                raise ValueError("cycle inventory contains an unexpected graph")
            matrix = np.asarray(controls[seed], dtype=np.int64)
            ell = len(rows)
            actual_num = [int(matrix[rows[i], variables[i]]) for i in range(ell)]
            actual_den = [int(matrix[rows[(i + 1) % ell], variables[i]])
                          for i in range(ell)]
            saved_num = [int(x) for x in json.loads(
                row["control_numerator_coefficients_json"])]
            saved_den = [int(x) for x in json.loads(
                row["control_denominator_coefficients_json"])]
            if actual_num != saved_num or actual_den != saved_den:
                raise ValueError("saved control coefficients do not match reconstructed H0D")
            actual_facts = census.cycle_matrix_facts(matrix, rows, variables)
            if (actual_facts["numerator_coefficients"] != saved_num
                    or actual_facts["denominator_coefficients"] != saved_den
                    or actual_facts["product"] != int(row["control_product"])
                    or actual_facts["unit"] != (row["control_unit"] == "True")):
                raise ValueError("reconstructed H0D cycle facts disagree with saved control")
            support = tuple(sorted(variables))
            if support in supports[seed]:
                raise ValueError("cycle inventory has duplicate variable support")
            supports[seed].add(support)
            counts[(seed, ell)] = counts.get((seed, ell), 0) + 1
            by_seed[seed].append({
                "graph_seed": seed, "ell": ell,
                "cycle_key": list(key_tuple), "rows": rows,
                "variables": variables,
            })
    if seen_rows != set(expected_rows):
        raise ValueError("source-overlap and census inventories are incomplete or different")
    for seed in GRAPH_SEEDS:
        expected_by_ell = accepted_census["expected_by_graph_ell"][seed]
        if len(by_seed[seed]) != sum(expected_by_ell.values()):
            raise ValueError("source cycle inventory has a wrong per-graph count")
        for ell, expected_count in expected_by_ell.items():
            if counts.get((seed, ell), 0) != expected_count:
                raise ValueError("source cycle inventory has a wrong per-length count")
    return by_seed


def _cycle_state(matrix: np.ndarray, cycle: Mapping[str, Any],
                 b_values: np.ndarray) -> dict[str, Any]:
    """Compute one cycle's local word and exact source overlap without rank."""
    rows = tuple(int(x) for x in cycle["rows"])
    variables = tuple(int(x) for x in cycle["variables"])
    ell = len(rows)
    numerator = [int(matrix[rows[i], variables[i]]) for i in range(ell)]
    denominator = [int(matrix[rows[(i + 1) % ell], variables[i]])
                   for i in range(ell)]
    if any(value < 1 or value >= 32 for value in numerator + denominator):
        raise ValueError("cycle incidence is zero or outside GF(32)")
    product = 1
    for top, bottom in zip(numerator, denominator):
        product = int(layout.gf32_mul(
            product, census._gf32_div(top, bottom)))
    unit = product == 1
    witness: list[int] | None = None
    orbit = None
    overlap = None
    if unit:
        values = [1]
        for index in range(1, ell):
            previous = int(matrix[rows[index], variables[index - 1]])
            current = int(matrix[rows[index], variables[index]])
            values.append(int(layout.gf32_mul(
                int(layout.gf32_mul(previous, values[-1])),
                census._gf32_inverse(current))))
        witness = values
        orbit = source_overlap.normalize_orbit(variables, witness)
        overlap = source_overlap.overlap_for_orbit(orbit, b_values)
    return {
        "numerator_coefficients": numerator,
        "denominator_coefficients": denominator,
        "product": int(product), "unit": bool(unit),
        "witness_values": witness,
        "orbit": [list(pair) for pair in orbit] if orbit is not None else None,
        "W": float(overlap["W"]) if overlap is not None else None,
        "positive_overlap_terms": (
            int(overlap["positive_overlap_terms"])
            if overlap is not None else None),
        "source_status": (
            str(overlap["source_status"]) if overlap is not None
            else "NONUNIT_NO_LOCAL_CODEWORD"),
    }


def _cycle_cost(state: Mapping[str, Any]) -> float:
    return float(state["W"]) if state["unit"] else 0.0


def _full_reference(matrix: np.ndarray, cycles: list[dict[str, Any]],
                    b_values: np.ndarray, *, verify_rank: bool = False
                    ) -> tuple[float, list[dict[str, Any]]]:
    states = [_cycle_state(matrix, cycle, b_values) for cycle in cycles]
    if verify_rank:
        for cycle, state in zip(cycles, states):
            facts = census.cycle_matrix_facts(
                matrix, cycle["rows"], cycle["variables"])
            if (facts["numerator_coefficients"] != state["numerator_coefficients"]
                    or facts["denominator_coefficients"]
                        != state["denominator_coefficients"]
                    or facts["product"] != state["product"]
                    or facts["unit"] != state["unit"]
                    or facts["witness_values"] != state["witness_values"]):
                raise ArithmeticError("full GF32 reference facts disagree")
            state["cycle_submatrix_rank"] = int(facts["cycle_submatrix_rank"])
    total = math.fsum(_cycle_cost(state) for state in states)
    return float(total), states


def _choose_beta(scores: Mapping[int, float], current: int,
                 tolerance: float = TIE_TOL) -> int:
    if current not in scores or not scores:
        raise ValueError("coordinate scores must include the current label")
    minimum = min(float(value) for value in scores.values())
    if float(scores[current]) - minimum <= tolerance:
        return int(current)
    return min(beta for beta, value in scores.items()
               if float(value) - minimum <= tolerance)


def coordinate_pass(matrix: np.ndarray, cycles: list[dict[str, Any]],
                    b_values: np.ndarray, *,
                    checkpoint: Callable[[str, int, int], str | None] | None = None,
                    counters: dict[str, int] | None = None,
                    graph_seed: int = -1) -> dict[str, Any]:
    """One row-major absolute-beta pass, minimizing local source-overlap F."""
    h = np.asarray(matrix, dtype=np.int64).copy()
    if h.ndim != 2 or h.shape == (0, 0) or np.any(h < 0) or np.any(h >= 32):
        raise ValueError("source-label matrix must be a nonempty GF(32) matrix")
    if counters is None:
        counters = {"label_trials": 0, "affected_cycle_evaluations": 0,
                    "reference_cycle_evaluations": 0}
    for key in ("label_trials", "affected_cycle_evaluations",
                "reference_cycle_evaluations"):
        counters.setdefault(key, 0)
    initial_f, states = _full_reference(h, cycles, b_values, verify_rank=True)
    counters["reference_cycle_evaluations"] += len(cycles)
    control_states = [dict(state) for state in states]
    current_f = float(initial_f)
    updates: list[dict[str, Any]] = []
    incidence: dict[tuple[int, int], list[int]] = {}
    for index, cycle in enumerate(cycles):
        rows = cycle["rows"]
        variables = cycle["variables"]
        for i in range(len(rows)):
            incidence.setdefault((int(rows[i]), int(variables[i])), []).append(index)
            incidence.setdefault((int(rows[(i + 1) % len(rows)]),
                                  int(variables[i])), []).append(index)
    for row, column in sorted(
            (int(r), int(c)) for r, c in np.argwhere(h != 0)):
        if checkpoint is not None:
            reason = checkpoint("before_coordinate", row, column)
            if reason:
                return _coordinate_result(
                    h, cycles, current_f, initial_f, states, control_states,
                    updates, counters, reason, graph_seed=graph_seed)
        old = int(h[row, column])
        affected = sorted(set(incidence.get((row, column), ())))
        affected_set = set(affected)
        unaffected_f = math.fsum(
            _cycle_cost(state) for i, state in enumerate(states)
            if i not in affected_set)
        scores: dict[int, float] = {}
        state_by_beta: dict[int, dict[int, dict[str, Any]]] = {}
        for beta in range(1, 32):
            if counters["label_trials"] >= MAX_LABEL_TRIALS:
                return _coordinate_result(
                    h, cycles, current_f, initial_f, states, control_states,
                    updates, counters, "LABEL_TRIAL_CAP", graph_seed=graph_seed)
            if counters["affected_cycle_evaluations"] + len(affected) \
                    > MAX_AFFECTED_CYCLE_EVALUATIONS:
                return _coordinate_result(
                    h, cycles, current_f, initial_f, states, control_states,
                    updates, counters, "AFFECTED_CYCLE_EVALUATION_CAP",
                    graph_seed=graph_seed)
            counters["label_trials"] += 1
            counters["affected_cycle_evaluations"] += len(affected)
            h[row, column] = beta
            trial_states = {
                i: _cycle_state(h, cycles[i], b_values) for i in affected
            }
            scores[beta] = float(math.fsum(
                [unaffected_f]
                + [_cycle_cost(trial_states[i]) for i in affected]))
            state_by_beta[beta] = trial_states
        h[row, column] = old
        selected = _choose_beta(scores, old)
        chosen_f = float(scores[selected])
        changed = selected != old and current_f - chosen_f > TIE_TOL
        update = {
            "graph_seed": int(graph_seed), "row": row, "column": column,
            "old_beta": old, "chosen_beta": int(selected),
            "committed": bool(changed), "affected_cycle_count": len(affected),
            "F_before": float(current_f), "F_minimum_trial": min(scores.values()),
            "F_chosen_trial": chosen_f,
            "trial_F_by_beta": [
                {"beta": beta, "F": float(scores[beta])}
                for beta in range(1, 32)
            ],
            "reference_F_after": None, "reference_drift": None,
        }
        if changed:
            h[row, column] = selected
            for index, state in state_by_beta[selected].items():
                states[index] = state
            reference_f, reference_states = _full_reference(
                h, cycles, b_values, verify_rank=False)
            counters["reference_cycle_evaluations"] += len(cycles)
            drift = float(reference_f - chosen_f)
            material_increase = float(reference_f - current_f)
            update["reference_F_after"] = float(reference_f)
            update["reference_drift"] = drift
            update["material_increase"] = material_increase
            updates.append(update)
            states = reference_states
            if abs(drift) > REFERENCE_TOL:
                return _coordinate_result(
                    h, cycles, reference_f, initial_f, states, control_states,
                    updates, counters, "FULL_REFERENCE_DRIFT",
                    graph_seed=graph_seed)
            if material_increase > REFERENCE_TOL:
                return _coordinate_result(
                    h, cycles, reference_f, initial_f, states, control_states,
                    updates, counters, "MATERIAL_OBJECTIVE_INCREASE",
                    graph_seed=graph_seed)
            current_f = float(reference_f)
        else:
            updates.append(update)
        if checkpoint is not None:
            reason = checkpoint("after_coordinate", row, column)
            if reason:
                return _coordinate_result(
                    h, cycles, current_f, initial_f, states, control_states,
                    updates, counters, reason, graph_seed=graph_seed)
    final_f, final_states = _full_reference(h, cycles, b_values, verify_rank=True)
    counters["reference_cycle_evaluations"] += len(cycles)
    final_drift = float(final_f - current_f)
    if abs(final_drift) > REFERENCE_TOL:
        stop_reason = "FINAL_REFERENCE_DRIFT"
    else:
        stop_reason = ""
    return _coordinate_result(
        h, cycles, final_f, initial_f, final_states, control_states,
        updates, counters, stop_reason, final_reference_drift=final_drift,
        graph_seed=graph_seed)


def _inventory_summary(states: list[dict[str, Any]]) -> dict[str, Any]:
    unit = [state for state in states if state["unit"]]
    positive = sum(state["source_status"] == "POSITIVE_OVERLAP" for state in unit)
    zero = sum(state["source_status"] == "ZERO_SOURCE_OVERLAP" for state in unit)
    return {
        "cycle_rows": len(states), "unit_cycle_rows": len(unit),
        "nonunit_cycle_rows": len(states) - len(unit),
        "unique_unit_orbits": len(unit),
        "positive_overlap_orbits": int(positive),
        "zero_source_overlap_orbits": int(zero),
        "sum_W_unique_orbits": float(math.fsum(
            float(state["W"]) for state in unit)),
    }


def _coordinate_result(matrix, cycles, final_f, initial_f, states,
                       control_states, updates, counters, stop_reason,
                       final_reference_drift=None, graph_seed=-1):
    diagnostics = {
        "graph_seed": (int(cycles[0]["graph_seed"]) if cycles
                       else int(graph_seed)),
        "initial_F": float(initial_f), "final_F": float(final_f),
        "F_reduction": float(initial_f - final_f),
        "coordinate_count": len(updates),
        "changed_edges": sum(bool(row["committed"]) for row in updates),
        "coordinate_updates": updates,
        "control_cycle_inventory": _inventory_summary(control_states),
        "candidate_cycle_inventory": _inventory_summary(states),
        "candidate_cycle_states": [
            {"cycle_key": cycle["cycle_key"], "ell": cycle["ell"],
             "rows": cycle["rows"], "variables": cycle["variables"],
             "control": control, "candidate": candidate}
            for cycle, control, candidate in zip(cycles, control_states, states)
        ],
        "counters": dict(counters),
        "final_reference_drift": final_reference_drift,
        "construction_stop": bool(stop_reason),
        "failure_reason": str(stop_reason),
    }
    return {"matrix": np.asarray(matrix, dtype=np.int64), **diagnostics}


def _initial_manifest(command: str) -> dict[str, Any]:
    _, holdouts = _validate_seed_plan()
    pmf = source_pmf()
    return {
        "track": "EXPLORE", "batch_uuid": BATCH_UUID,
        "parent_batch_uuid": PARENT_BATCH_UUID,
        "contract": CONTRACT, "status": "RUNNING",
        "graph_profile": {
            "n": N, "m": M, "E": EDGE_COUNT,
            "field": "GF(32)/polynomial-37",
            "graph_seeds": list(GRAPH_SEEDS),
            "source_graph": "accepted SEARCH-DEPTH deep H0D per same-seed D10 graph",
            "candidate_start": "control deep H0D; no pivot freeze",
        },
        "source_shape_proxy": {
            "source": "accepted historical 2M aggregate summary only",
            "counts": {str(symbol): count for symbol, count in SHAPE_COUNTS},
            "total": SHAPE_TOTAL, "role": "synthetic iid marginal shape proxy",
            "not_conditional_channel_reconstruction": True,
            "no_empirical_input_reads": True,
        },
        "source_pmf": pmf.tolist(), "p0": P0,
        "decoder": {
            "implementation": "v35 row-layered FFT-QSPA",
            "max_iter": 90, "damping_alpha": 1.0,
            "warm_beliefs": None, "field": None,
            "prior_floor": "existing decoder 1e-15 floor and normalization",
            "only_arm_difference": "edge labels in fixed H support",
        },
        "objective": {
            "name": "sum W over fixed unique local unit-cycle orbits",
            "cycle_inventory": "accepted simple cycles ell=2..6",
            "tie_tolerance": TIE_TOL,
            "tie_rule": "current beta if within tolerance; otherwise smallest beta within tolerance",
            "commit_rule": "only current F minus chosen F > 1e-14",
            "reference_tolerance": REFERENCE_TOL,
            "nonunit_cycle_cost": 0,
            "unit_zero_overlap_is_distinct_from_nonunit": True,
            "claim_ceiling": "dimensionless local source overlap; not FER or an error bound",
        },
        "pairing": "same sampled error/prior; arm-specific syndrome from each H",
        "arm_order": "control first on even frame; candidate first on odd",
        "seed_namespace": SEED_PREFIX,
        "seed_plan_counts": {"pilot": 0, "holdout_pairs": len(holdouts)},
        "seed_plan_disjoint_from_prior_batches": True,
        "accounting": {
            "syndrome_bits_per_attempt": SYNDROME_BITS, "tag_bits": 0,
            "verification_status": "NOT_IMPLEMENTED",
            "undetected_status": "NOT_MEASURED",
            "success": "exact AND independently recomputed syndrome acceptance",
            "wrong": "syndrome_accept AND NOT exact; separately recorded failure",
            "truth_prior_and_conditional_arrays_saved": False,
        },
        "budgets": {
            "total_wall_s": WALL_CAP_S,
            "per_decoder_call_s": CALL_CAP_S,
            "rss_bytes": RSS_CAP_BYTES,
            "max_decoder_calls": MAX_CALLS,
            "max_label_trials": MAX_LABEL_TRIALS,
            "max_affected_cycle_evaluations": MAX_AFFECTED_CYCLE_EVALUATIONS,
        },
        "input_roots": {
            "census": str(CENSUS_ROOT_RELATIVE),
            "source_overlap": str(OVERLAP_ROOT_RELATIVE),
            "census_uuid": census.BATCH_UUID,
            "source_overlap_uuid": source_overlap.BATCH_UUID,
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
    _write_json(root / "manifest.json", manifest)
    with (root / "frame_records.csv").open(
            "w", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=FRAME_FIELDS).writeheader()
    _write_json(root / "summary.json", {"status": "RUNNING"})
    with (root / "EXPLORATION_LOG.md").open("w", encoding="utf-8") as stream:
        stream.write("# GF32 source-aware edge-label R2 EXPLORE log\n\n")
        stream.write("Batch UUID: `%s`. Parent failed batch UUID: `%s`. "
                     "Independent batch-end review: pending.\n"
                     % (BATCH_UUID, PARENT_BATCH_UUID))


def _append_log(root: Path, message: str) -> None:
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as stream:
        stream.write("- %s\n" % message)


def _append_row(root: Path, row: Mapping[str, Any]) -> None:
    with (root / "frame_records.csv").open(
            "a", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=FRAME_FIELDS).writerow(
            {field: row.get(field) for field in FRAME_FIELDS})
    _append_log(root,
                "call %d %s/%s graph=%s stream=%s frame=%s seed=%s "
                "iterations=%s exact=%s syndrome_accept=%s wrong=%s status=%s "
                "wall_s=%.6f"
                % (int(row["call_index"]), row["phase"], row["arm"],
                   row["graph_seed"], row["stream"], row["frame"], row["seed"],
                   row["iterations"], row["exact"], row["syndrome_accept"],
                   row["syndrome_consistent_wrong"], row["status"], row["wall_s"]))


def _summarize(rows: list[dict[str, Any]], completed_pairs: list[dict[str, Any]],
               candidate_diagnostics: list[dict[str, Any]],
               stop_reason: str) -> dict[str, Any]:
    holdout = [row for row in rows if row["phase"] == "holdout"]
    control = [row for row in holdout if row["arm"] == "control"]
    candidate = [row for row in holdout if row["arm"] == "candidate"]
    complete = len(completed_pairs) == HOLDOUT_PAIRS
    good = lambda row: bool(row["exact"] and row["syndrome_accept"])
    ctrl_n = sum(good(row) for row in control)
    cand_n = sum(good(row) for row in candidate)
    integrity = sum(str(row["status"]).startswith(
        ("integrity_error", "decoder_exception")) for row in rows)
    resource = sum("resource_abort" in str(row["status"]) for row in rows)
    wrong_by_arm = {
        arm: sum(bool(row["syndrome_consistent_wrong"])
                 for row in rows if row["arm"] == arm)
        for arm in ("control", "candidate")
    }
    graph_summary: dict[str, Any] = {}
    for seed in GRAPH_SEEDS:
        grow = [row for row in holdout if int(row["graph_seed"]) == seed]
        gpairs = [pair for pair in completed_pairs
                  if int(pair["graph_seed"]) == seed]
        crows = [row for row in grow if row["arm"] == "control"]
        krows = [row for row in grow if row["arm"] == "candidate"]
        item = {"completed_pairs": len(gpairs), "control_attempts": len(crows),
                "candidate_attempts": len(krows)}
        if complete:
            c = sum(good(row) for row in crows)
            k = sum(good(row) for row in krows)
            item.update({"control_exact": int(c), "candidate_exact": int(k),
                         "delta_g": int(k - c)})
        else:
            item.update({"control_exact": None, "candidate_exact": None,
                         "delta_g": None})
        graph_summary[str(seed)] = item
    positive = (sum(item["delta_g"] > 0 for item in graph_summary.values())
                if complete else None)
    reductions = {str(item["graph_seed"]): float(item["F_reduction"])
                  for item in candidate_diagnostics}
    reduced_graphs = sum(value > TIE_TOL for value in reductions.values())
    states = None
    if complete:
        states = {"control_only": 0, "candidate_only": 0,
                  "both": 0, "neither": 0}
        for pair in completed_pairs:
            key = {(True, False): "control_only", (False, True): "candidate_only",
                   (True, True): "both", (False, False): "neither"}[
                       (bool(pair["control_success"]),
                        bool(pair["candidate_success"]))]
            states[key] += 1
        delta = int(cand_n - ctrl_n)
        if not CONTROL_MIN <= ctrl_n <= CONTROL_MAX:
            classification = "CONTROL_RANGE_UNINFORMATIVE"
        elif (delta >= SIGNAL_DELTA and positive >= SIGNAL_POSITIVE_GRAPHS
              and reduced_graphs >= MIN_REDUCED_GRAPHS
              and integrity == 0 and resource == 0):
            classification = "MECHANISM_SIGNAL"
        else:
            classification = "NO_SUFFICIENT_SIGNAL"
    else:
        delta = None
        classification = "INCOMPLETE"
    return {
        "batch_uuid": BATCH_UUID, "parent_batch_uuid": PARENT_BATCH_UUID,
        "contract": CONTRACT,
        "classification": classification, "stop_reason": stop_reason,
        "holdout_complete": complete,
        "holdout_pairs_completed": len(completed_pairs),
        "control_exact": int(ctrl_n) if complete else None,
        "candidate_exact": int(cand_n) if complete else None,
        "delta": delta, "positive_graphs": positive,
        "delta_by_graph": graph_summary, "paired_states": states,
        "source_objective_reductions_by_graph": reductions,
        "source_objective_reduced_graphs": int(reduced_graphs),
        "decoder_calls_by_arm": {"control": len(control),
                                  "candidate": len(candidate)},
        "decoder_iterations_by_arm": {
            arm: int(sum(int(row["iterations"]) for row in rows if row["arm"] == arm))
            for arm in ("control", "candidate")},
        "decoder_wall_s_by_arm": {
            arm: float(sum(float(row["wall_s"]) for row in rows if row["arm"] == arm))
            for arm in ("control", "candidate")},
        "syndrome_consistent_wrong_rows": int(sum(wrong_by_arm.values())),
        "syndrome_consistent_wrong_by_arm": wrong_by_arm,
        "integrity_violations": int(integrity),
        "resource_violations": int(resource),
        "authorization_violations": 0,
        "syndrome_bits_per_attempt": SYNDROME_BITS,
        "actual_syndrome_disclosure_bits": len(rows) * SYNDROME_BITS,
        "tag_bits": 0, "verification_status": "NOT_IMPLEMENTED",
        "undetected_status": "NOT_MEASURED", "FER": None,
        "f_eff": None, "SKR": None,
        "claim_ceiling": (
            "one source-overlap label pass on six fixed GF(32) synthetic graphs "
            "under an iid marginal-shape proxy; not FER, an error bound, "
            "conditional-channel reconstruction, route, or security claim"),
    }


def _resource_stop(started: float, now: Callable[[], float],
                   rss_fn: Callable[[], int | None], calls: int) -> str:
    if calls >= MAX_CALLS:
        return "decoder_call_count_cap_before_next_call"
    elapsed = max(float(now()) - float(started), 0.0)
    rss = rss_fn()
    if elapsed >= WALL_CAP_S:
        return "total_wall_cap_before_next_step"
    if rss is not None and int(rss) >= RSS_CAP_BYTES:
        return "rss_cap_before_next_step"
    return ""


def verify_t0() -> dict[str, bool]:
    """Check only finite-field/source identities and a tiny cycle fixture."""
    pmf = source_pmf()
    b_values = source_overlap.bhattacharyya_values(pmf)
    if np.flatnonzero(pmf).tolist() != [0, 1, 3, 7, 15, 31]:
        raise AssertionError("frozen source support changed")
    if not np.isclose(math.fsum(float(x) for x in pmf), 1.0,
                      rtol=0.0, atol=2e-15):
        raise AssertionError("source PMF normalization failed")
    direct = source_overlap.direct_two_symbol_overlap(pmf, (3, 7))
    factored = float(b_values[3] * b_values[7])
    if not math.isclose(direct, factored, rel_tol=0.0, abs_tol=2e-14):
        raise AssertionError("direct and factored source overlaps disagree")
    matrix = np.asarray([[1, 1], [1, 1]], dtype=np.int64)
    cycle = {"graph_seed": 1, "ell": 2, "cycle_key": [0, 2, 1, 3],
             "rows": [0, 1], "variables": [0, 1]}
    state = _cycle_state(matrix, cycle, b_values)
    scaled = source_overlap.normalize_orbit([0, 1], [7, 7])
    scaled_w = source_overlap.overlap_for_orbit(scaled, b_values)["W"]
    if not state["unit"] or not math.isclose(state["W"], scaled_w,
                                            rel_tol=0.0, abs_tol=1e-14):
        raise AssertionError("unit-cycle scalar-orbit source overlap failed")
    no_cycles = coordinate_pass(matrix, [], b_values)
    if (no_cycles["construction_stop"] or no_cycles["changed_edges"] != 0
            or no_cycles["counters"]["label_trials"] != 4 * 31):
        raise AssertionError("empty-inventory coordinate pass did not retain labels")
    return {
        "fixed_source_pmf": True, "direct_overlap_factorization": True,
        "scalar_orbit_invariance": True, "empty_inventory_no_change": True,
    }


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root)
    checks = verify_t0()
    _, holdouts = _validate_seed_plan()
    return {
        "status": "DRY_RUN", "batch_uuid": BATCH_UUID,
        "parent_batch_uuid": PARENT_BATCH_UUID,
        "out_root": str(root), "writes": 0,
        "empirical_input_reads": 0, "census_artifact_reads": 0,
        "cycle_rows_read": 0, "graph_construction_calls": 0,
        "decoder_calls": 0, "t0": checks,
        "p0": P0, "holdout_pairs": len(holdouts),
        "holdout_calls": MAX_CALLS, "pilot_calls": 0,
        "max_label_trials": MAX_LABEL_TRIALS,
        "max_affected_cycle_evaluations": MAX_AFFECTED_CYCLE_EVALUATIONS,
        "profile": {"n": N, "m": M, "E": EDGE_COUNT,
                    "graph_seeds": list(GRAPH_SEEDS)},
    }


def execute_batch(*, out_root: str | Path, decode_fns: Mapping[str, Callable],
                  graph_builder: Callable[[int], Mapping[str, Any]],
                  command: str = COMMAND,
                  repo_root: str | Path | None = None,
                  now: Callable[[], float] = time.perf_counter,
                  rss_fn: Callable[[], int | None] | None = None,
                  graph_preflight_fn: Callable | None = None,
                  control_builder: Callable | None = None,
                  cycle_loader: Callable | None = None,
                  candidate_builder: Callable | None = None) -> dict[str, Any]:
    if (not isinstance(decode_fns, Mapping)
            or set(decode_fns) != {"control", "candidate"}
            or any(not callable(decode_fns[arm])
                   for arm in ("control", "candidate"))):
        raise ValueError("explicit control and candidate decoder callbacks are required")
    if graph_builder is None or not callable(graph_builder):
        raise ValueError("an explicit graph builder is required")
    root = validate_out_root(out_root, repo_root=repo_root)
    root_base = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    rss_fn = rss_fn or d5._rss_bytes
    graph_preflight_fn = graph_preflight_fn or edge_runner.graph_preflight
    control_builder = control_builder or search_runner.build_candidate_pair
    cycle_loader = cycle_loader or _load_cycle_inventory
    started = float(now())
    rss_values: list[int] = []
    calls = 0
    rows: list[dict[str, Any]] = []
    completed_pairs: list[dict[str, Any]] = []
    graph_diagnostics: list[dict[str, Any]] = []
    candidate_diagnostics: list[dict[str, Any]] = []
    search_counters = {"label_trials": 0, "affected_cycle_evaluations": 0,
                       "reference_cycle_evaluations": 0}
    controls: dict[int, np.ndarray] = {}
    candidates: dict[int, np.ndarray] = {}
    per_seed_cycles: dict[int, list[dict[str, Any]]] = {}
    stop_reason = ""
    terminal = "INCOMPLETE"
    manifest = _initial_manifest(command)

    def sample_rss() -> int | None:
        value = rss_fn()
        if value is not None:
            rss_values.append(int(value))
        return value

    def check_resource(stage: str) -> str:
        elapsed = max(float(now()) - started, 0.0)
        rss = sample_rss()
        if elapsed >= WALL_CAP_S:
            return "total_wall_cap:%s" % stage
        if rss is not None and int(rss) >= RSS_CAP_BYTES:
            return "rss_cap:%s" % stage
        return ""

    def finish() -> dict[str, Any]:
        sample_rss()
        summary = _summarize(rows, completed_pairs, candidate_diagnostics,
                             stop_reason)
        summary.update({
            "terminal_status": terminal,
            "attempted_decoder_calls": calls,
            "attempted_frame_rows": len(rows),
            "attempted_call_counts": {"pilot": 0, "holdout": len(rows),
                                      "total": calls},
            "batch_wall_s": max(float(now()) - started, 0.0),
            "max_call_wall_s": (max(float(row["wall_s"]) for row in rows)
                                if rows else None),
            "max_rss_bytes": max(rss_values) if rss_values else None,
            "rss_sample_count": len(rss_values),
            "rss_scope": ("process high-water RSS via d5 helper; Windows "
                          "fallback is current process working set"),
            "search_counters": dict(search_counters),
            "graph_diagnostics": graph_diagnostics,
            "candidate_diagnostics": candidate_diagnostics,
        })
        _write_json(root / "summary.json", summary)
        manifest.update({
            "status": terminal, "stop_reason": stop_reason,
            "attempted_decoder_calls": calls,
            "attempted_call_counts": summary["attempted_call_counts"],
            "attempted_frame_rows": len(rows),
            "batch_wall_s": summary["batch_wall_s"],
            "max_call_wall_s": summary["max_call_wall_s"],
            "max_rss_bytes": summary["max_rss_bytes"],
            "rss_sample_count": summary["rss_sample_count"],
            "search_counters": search_counters,
            "graph_diagnostics": graph_diagnostics,
            "candidate_diagnostics": [
                {key: value for key, value in item.items()
                 if key not in ("coordinate_updates", "candidate_cycle_states")}
                for item in candidate_diagnostics],
        })
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "terminal=%s stop_reason=%s calls=%d rows=%d"
                    % (terminal, stop_reason or "none", calls, len(rows)))
        return summary

    def stop(reason: str, status: str) -> dict[str, Any]:
        nonlocal stop_reason, terminal
        stop_reason, terminal = str(reason), str(status)
        return finish()

    sample_rss()
    _start_outputs(root, manifest)
    try:
        manifest["t0"] = verify_t0()
        _write_json(root / "manifest.json", manifest)
        for seed in GRAPH_SEEDS:
            reason = check_resource("before_graph:%d" % seed)
            if reason:
                return stop(reason, "RESOURCE_STOP")
            graph = graph_builder(int(seed))
            admitted, diagnostic = graph_preflight_fn(graph, int(seed))
            graph_diagnostics.append(diagnostic)
            reason = check_resource("after_graph:%d" % seed)
            if reason:
                return stop(reason, "RESOURCE_STOP")
            if not admitted:
                return stop("GRAPH_PREFLIGHT_FAILED:%d" % seed,
                            "GRAPH_PREFLIGHT_STOP")
            dense = np.asarray(graph["dense"], dtype=np.int64)
            reason = check_resource("before_deep_control:%d" % seed)
            if reason:
                return stop(reason, "RESOURCE_STOP")
            onepass, deep, diag = control_builder(
                dense, source_pmf(), int(seed))
            reason = check_resource("after_deep_control:%d" % seed)
            if reason:
                return stop(reason, "RESOURCE_STOP")
            if (deep is None or diag.get("construction_stop")
                    or not diag.get("deep_candidate_admitted", True)):
                return stop("DEEP_H0D_RECONSTRUCTION_STOP:%d:%s"
                            % (seed, diag.get("failure_reason", "")),
                            "CONSTRUCTION_STOP")
            deep = np.asarray(deep, dtype=np.int64)
            if deep.shape != (M, N) or not np.array_equal(deep != 0, dense != 0):
                return stop("DEEP_H0D_SUPPORT_MISMATCH:%d" % seed,
                            "CONSTRUCTION_STOP")
            controls[int(seed)] = deep
            graph_diagnostics[-1]["deep_control"] = {
                "accepted": True,
                "deep_rank": int(d10.gf32_row_rank(deep)),
                "search": diag,
                "onepass_present": onepass is not None,
            }
            if int(graph_diagnostics[-1]["deep_control"]["deep_rank"]) != M:
                return stop("DEEP_H0D_RANK_FAILED:%d" % seed,
                            "CONSTRUCTION_STOP")
        reason = check_resource("before_reference_inventory")
        if reason:
            return stop(reason, "RESOURCE_STOP")
        try:
            per_seed_cycles = cycle_loader(root_base, controls)
        except Exception as exc:
            return stop("PREDECESSOR_INVALID:%s:%s"
                        % (type(exc).__name__, str(exc)), "PREDECESSOR_STOP")
        reason = check_resource("after_reference_inventory")
        if reason:
            return stop(reason, "RESOURCE_STOP")
        b_values = source_overlap.bhattacharyya_values(source_pmf())
        for seed in GRAPH_SEEDS:
            if seed not in per_seed_cycles:
                return stop("CYCLE_INVENTORY_MISSING_GRAPH:%d" % seed,
                            "PREDECESSOR_STOP")
            reason = check_resource("before_source_search:%d" % seed)
            if reason:
                return stop(reason, "RESOURCE_STOP")

            def checkpoint(stage: str, row: int, column: int,
                           _seed=int(seed)) -> str | None:
                reason = check_resource(
                    "%s:%d:%d:%d" % (stage, _seed, row, column))
                return reason or None

            if candidate_builder is None:
                search_result = coordinate_pass(
                    controls[int(seed)], per_seed_cycles[int(seed)], b_values,
                    checkpoint=checkpoint, counters=search_counters,
                    graph_seed=int(seed))
            else:
                search_result = candidate_builder(
                    controls[int(seed)], per_seed_cycles[int(seed)], b_values,
                    checkpoint=checkpoint, counters=search_counters,
                    graph_seed=int(seed))
            candidate_diagnostics.append({key: value for key, value in
                                           search_result.items()
                                           if key != "matrix"})
            if search_result.get("construction_stop"):
                why = str(search_result.get("failure_reason", "search stop"))
                status = "RESOURCE_STOP" if "cap" in why or "wall" in why \
                    or "rss" in why else "CONSTRUCTION_STOP"
                return stop("SOURCE_LABEL_SEARCH_STOP:%d:%s" % (seed, why), status)
            candidate_matrix = np.asarray(search_result["matrix"], dtype=np.int64)
            control = controls[int(seed)]
            support_equal = np.array_equal(candidate_matrix != 0, control != 0)
            degrees_equal = bool(
                np.array_equal(np.count_nonzero(candidate_matrix, axis=0),
                               np.count_nonzero(control, axis=0))
                and np.array_equal(np.count_nonzero(candidate_matrix, axis=1),
                                   np.count_nonzero(control, axis=1)))
            rank = int(d10.gf32_row_rank(candidate_matrix))
            if not support_equal or not degrees_equal or rank != M:
                return stop("FINAL_SUPPORT_DEGREE_OR_RANK_GATE_FAILED:%d" % seed,
                            "CONSTRUCTION_STOP")
            gauge = edge_runner.gauge_diagnostics(control, candidate_matrix)
            candidate_diagnostics[-1]["candidate_rank"] = rank
            candidate_diagnostics[-1]["support_equal"] = support_equal
            candidate_diagnostics[-1]["degrees_equal"] = degrees_equal
            candidate_diagnostics[-1]["gauge_diagnostic_only"] = gauge
            candidates[int(seed)] = candidate_matrix
            reason = check_resource("after_source_search:%d" % seed)
            if reason:
                return stop(reason, "RESOURCE_STOP")

        prior = np.tile(source_pmf(), (N, 1))
        _, holdouts = _validate_seed_plan()
        for seed, stream, frame, sample_seed in holdouts:
            truth = prior_runner.sample_error(sample_seed, source_pmf(), width=N)
            paired = prior_runner.paired_arm_data(
                controls[int(seed)], candidates[int(seed)], truth, prior)
            pair_rows: dict[str, dict[str, Any]] = {}
            for arm in arm_order(frame):
                reason = _resource_stop(started, now, sample_rss, calls)
                if reason:
                    return stop(reason, "RESOURCE_STOP")
                calls += 1
                observed, issue = prior_runner.decode_observation(
                    decode_fns[arm], paired[arm]["dense"], paired[arm]["prior"],
                    paired[arm]["truth"], paired[arm]["syndrome"],
                    now=now, rss_fn=sample_rss)
                wall = float(observed["wall_s"])
                latest_rss = sample_rss()
                resource_reasons = []
                if wall >= CALL_CAP_S:
                    resource_reasons.append("decoder_call_wall_cap_after_return")
                if max(float(now()) - started, 0.0) >= WALL_CAP_S:
                    resource_reasons.append("total_wall_cap_after_call")
                if latest_rss is not None and int(latest_rss) >= RSS_CAP_BYTES:
                    resource_reasons.append("rss_cap_after_call")
                try:
                    iterations = int(observed["iterations"])
                except (TypeError, ValueError, OverflowError):
                    iterations = -1
                if not 0 <= iterations <= 90:
                    observed.update({
                        "exact": False, "syndrome_accept": False,
                        "syndrome_consistent_wrong": False,
                        "status": "integrity_error:iteration_count_out_of_range",
                        "iterations": iterations,
                    })
                    issue = ";".join(x for x in
                                      (str(issue) if issue else "",
                                       "decoder_iteration_count_out_of_range") if x)
                if resource_reasons:
                    observed["status"] = str(observed["status"]) \
                        + "|resource_abort:" + ",".join(resource_reasons)
                    issue = ";".join(x for x in
                                      (str(issue) if issue else "",
                                       ",".join(resource_reasons)) if x)
                row = edge_runner.fine_runner.predecessor._record_row(
                    call_index=calls, phase="holdout", pmf=pmf_entry(),
                    graph_seed=int(seed), stream=int(stream), frame=int(frame),
                    seed=int(sample_seed), arm=arm, observed=observed)
                rows.append(row)
                _append_row(root, row)
                pair_rows[arm] = row
                if issue:
                    return stop(issue, "RESOURCE_STOP" if resource_reasons
                                else "INTEGRITY_STOP")
            if set(pair_rows) == {"control", "candidate"}:
                completed_pairs.append({
                    "graph_seed": int(seed), "stream": int(stream),
                    "frame": int(frame),
                    "control_success": bool(pair_rows["control"]["exact"]
                                            and pair_rows["control"]["syndrome_accept"]),
                    "candidate_success": bool(pair_rows["candidate"]["exact"]
                                               and pair_rows["candidate"]["syndrome_accept"]),
                })
        summary = _summarize(rows, completed_pairs, candidate_diagnostics, "")
        terminal = str(summary["classification"])
        stop_reason = ""
        return finish()
    except Exception as exc:
        stop_reason = "implementation_exception:%s:%s" % (
            type(exc).__name__, str(exc))
        terminal = "IMPLEMENTATION_STOP"
        _append_log(root, stop_reason)
        return finish()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GF32 source-overlap edge-label EXPLORE probe")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true",
                      help="run the frozen synthetic batch")
    mode.add_argument("--dry-run", action="store_true",
                      help="check tiny pure math and the output path")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE),
                        help="must equal the frozen fresh workspace root")
    return parser


def _bind_production_decoders() -> dict[str, Callable]:
    decoder = prior_runner._bind_production_decoder()
    return {"control": decoder, "candidate": decoder}


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    if args.execute:
        result = execute_batch(
            out_root=args.out_root, decode_fns=_bind_production_decoders(),
            graph_builder=edge_runner.build_profile_graph,
            command=COMMAND)
    else:
        result = dry_run(args.out_root)
    print(json.dumps(_plain(result), indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
