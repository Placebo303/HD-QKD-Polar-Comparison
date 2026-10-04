"""Decoder-free short-cycle census for the frozen GF(32) edge-label batch.

The census reconstructs the accepted predecessor matrices, compares their
construction diagnostics with the predecessor artifacts, and enumerates
simple Tanner cycles of variable length 2..6. It does not sample frames or
call a decoder.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import resource
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from comparison_bench.cli.probes_closed import nbldpc_gf32_edge_label_probe as edge_runner
from comparison_bench.cli.probes_closed import runner_support
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout

CONTRACT = "NBLDPC-GF32-SHORT-CYCLE-CENSUS-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "475c2ad3-bd5a-4000-8498-ea989bad1bba"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_cycle_census_475c2ad3"
REFERENCE_ROOT_RELATIVE = edge_runner.OUT_ROOT_RELATIVE
REFERENCE_BATCH_UUID = edge_runner.BATCH_UUID
GRAPH_SEEDS = edge_runner.GRAPH_SEEDS
N = edge_runner.N
M = edge_runner.M
EDGE_COUNT = edge_runner.EDGE_COUNT
POLY = 37
MIN_ELL = 2
MAX_ELL = 6
MAX_DFS_STATES = 2_000_000
MAX_CYCLES_PER_GRAPH = 100_000
WALL_CAP_S = 1800.0
RSS_CAP_BYTES = 4 * 1024**3
RESOURCE_CHECK_STATES = 1024
ROW_ID_OFFSET = 52

COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.probes_closed.nbldpc_gf32_cycle_census --execute "
    "--out-root workspace/gf32_cycle_census_475c2ad3"
)

CYCLE_COLUMNS = (
    "graph_seed", "ell", "cycle_key_json", "check_rows_json",
    "variable_columns_json", "control_numerator_coefficients_json",
    "control_denominator_coefficients_json", "control_product",
    "control_unit", "control_witness_values_json",
    "candidate_numerator_coefficients_json",
    "candidate_denominator_coefficients_json", "candidate_product",
    "candidate_unit", "candidate_witness_values_json", "state_transition",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    return runner_support.validate_out_root(
        out_root, root, OUT_ROOT_RELATIVE, error_qualifier="the "
    )


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    """Check the frozen destination without reading inputs or doing inventory."""
    resolved = validate_out_root(out_root, repo_root=repo_root)
    return {
        "status": "DRY_RUN",
        "batch_uuid": BATCH_UUID,
        "output_root": str(resolved),
        "graphs": list(GRAPH_SEEDS),
        "ell_range": [MIN_ELL, MAX_ELL],
        "dfs_state_cap_per_graph": MAX_DFS_STATES,
        "cycle_cap_per_graph": MAX_CYCLES_PER_GRAPH,
        "decoder_calls": 0,
        "graph_construction_calls": 0,
        "candidate_reconstruction_calls": 0,
        "cycle_enumerations": 0,
        "reference_artifact_reads": 0,
        "writes": 0,
    }


def _gf32_inverse(value: int) -> int:
    value = int(value)
    if value < 1 or value >= 32:
        raise ValueError("GF(32) denominator must be nonzero")
    return int(edge_runner.alignment.column_inverse([value])[0])


def _gf32_div(numerator: int, denominator: int) -> int:
    return int(layout.gf32_mul(int(numerator), _gf32_inverse(denominator)))


def canonical_cycle_key(rows: list[int] | tuple[int, ...],
                        variables: list[int] | tuple[int, ...]
                        ) -> tuple[int, ...]:
    """Canonical alternating row/variable key, rooted at the smallest row."""
    row_ids = tuple(int(value) for value in rows)
    variable_ids = tuple(int(value) for value in variables)
    if len(row_ids) != len(variable_ids) or len(row_ids) < MIN_ELL:
        raise ValueError("a Tanner cycle needs equal row/variable lengths >= 2")
    if len(set(row_ids)) != len(row_ids) or len(set(variable_ids)) != len(variable_ids):
        raise ValueError("cycle rows and variables must be distinct")
    root = min(range(len(row_ids)), key=row_ids.__getitem__)
    forward_rows = row_ids[root:] + row_ids[:root]
    forward_variables = variable_ids[root:] + variable_ids[:root]
    reverse_rows = (row_ids[root],) + tuple(
        row_ids[(root - step) % len(row_ids)]
        for step in range(1, len(row_ids)))
    reverse_variables = tuple(
        variable_ids[(root - step) % len(row_ids)]
        for step in range(1, len(row_ids) + 1))
    forward: list[int] = []
    reverse: list[int] = []
    for row, variable in zip(forward_rows, forward_variables):
        forward.extend((row, ROW_ID_OFFSET + variable))
    for row, variable in zip(reverse_rows, reverse_variables):
        reverse.extend((row, ROW_ID_OFFSET + variable))
    return min(tuple(forward), tuple(reverse))


def _cycle_from_key(key: tuple[int, ...]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    rows = tuple(int(value) for value in key[0::2])
    variables = tuple(int(value) - ROW_ID_OFFSET for value in key[1::2])
    return rows, variables


def enumerate_cycles(
        matrix: Any, *, max_states: int = MAX_DFS_STATES,
        max_cycles: int = MAX_CYCLES_PER_GRAPH,
        checkpoint: Callable[[int, int], str | None] | None = None
        ) -> dict[str, Any]:
    """Enumerate canonical simple cycles on a degree-two-variable support.

    `checkpoint` is called at every 1024th recursive state. It may return a
    resource-stop reason; discovered cycles and state counts are retained.
    """
    h = np.asarray(matrix, dtype=np.int64)
    if h.ndim != 2 or h.size == 0 or np.any(h < 0) or np.any(h >= 32):
        raise ValueError("cycle matrix must be nonempty GF(32) matrix")
    if not np.all(np.count_nonzero(h, axis=0) == 2):
        raise ValueError("every variable column must have degree two")
    if max_states < 0 or max_cycles < 0:
        raise ValueError("enumeration caps must be nonnegative")

    neighbors: list[list[int]] = [[] for _ in range(h.shape[0])]
    endpoints: dict[int, tuple[int, int]] = {}
    for variable in range(h.shape[1]):
        rows = tuple(int(row) for row in np.flatnonzero(h[:, variable]))
        if len(rows) != 2 or rows[0] == rows[1]:
            raise ValueError("each variable must join two distinct checks")
        endpoints[variable] = (rows[0], rows[1])
        neighbors[rows[0]].append(variable)
        neighbors[rows[1]].append(variable)
    for row_neighbors in neighbors:
        row_neighbors.sort()

    found: dict[tuple[int, ...], tuple[tuple[int, ...], tuple[int, ...]]] = {}
    path_rows: list[int] = []
    path_variables: list[int] = []
    states = 0
    stop_reason = ""

    def visit(start: int, current: int) -> None:
        nonlocal states, stop_reason
        if stop_reason:
            return
        if states >= max_states:
            stop_reason = "ENUMERATION_CAP_STOP:dfs_states"
            return
        states += 1
        if checkpoint is not None and states % RESOURCE_CHECK_STATES == 0:
            reason = checkpoint(states, len(found))
            if reason:
                stop_reason = "RESOURCE_STOP:" + str(reason)
                return

        for variable in neighbors[current]:
            if stop_reason:
                return
            if variable in path_variables:
                continue
            first, second = endpoints[variable]
            next_row = second if first == current else first
            if next_row == start:
                ell = len(path_variables) + 1
                if ell < MIN_ELL or ell > MAX_ELL:
                    continue
                rows = tuple(path_rows)
                variables = tuple(path_variables + [variable])
                key = canonical_cycle_key(rows, variables)
                if key not in found:
                    if len(found) >= max_cycles:
                        stop_reason = "ENUMERATION_CAP_STOP:unique_cycles"
                        return
                    found[key] = _cycle_from_key(key)
                continue
            if next_row <= start or next_row in path_rows:
                continue
            if len(path_variables) + 1 >= MAX_ELL:
                continue
            path_rows.append(next_row)
            path_variables.append(variable)
            visit(start, next_row)
            path_variables.pop()
            path_rows.pop()

    for start in range(h.shape[0]):
        if stop_reason:
            break
        path_rows[:] = [start]
        path_variables.clear()
        visit(start, start)

    cycles = [
        {"key": list(key), "rows": list(found[key][0]),
         "variables": list(found[key][1])}
        for key in sorted(found)
    ]
    return {"cycles": cycles, "dfs_states": states,
            "stop_reason": stop_reason}


def cycle_matrix_facts(matrix: Any, rows: list[int] | tuple[int, ...],
                       variables: list[int] | tuple[int, ...]
                       ) -> dict[str, Any]:
    """Return the GF(32) cycle product and, when unit, a normalized witness."""
    h = np.asarray(matrix, dtype=np.int64)
    row_ids = tuple(int(row) for row in rows)
    variable_ids = tuple(int(variable) for variable in variables)
    if len(row_ids) != len(variable_ids) or len(row_ids) < MIN_ELL:
        raise ValueError("cycle rows and variables must have equal length >= 2")
    ell = len(row_ids)
    numerator = [int(h[row_ids[i], variable_ids[i]]) for i in range(ell)]
    denominator = [int(h[row_ids[(i + 1) % ell], variable_ids[i]])
                   for i in range(ell)]
    if any(value == 0 for value in numerator + denominator):
        raise ValueError("cycle incidences must be nonzero")

    product = 1
    for top, bottom in zip(numerator, denominator):
        product = int(layout.gf32_mul(product, _gf32_div(top, bottom)))
    unit = product == 1
    witness: list[int] | None = None
    if unit:
        values = [1]
        for index in range(1, ell):
            previous_coefficient = int(
                h[row_ids[index], variable_ids[index - 1]])
            current_coefficient = int(
                h[row_ids[index], variable_ids[index]])
            values.append(int(layout.gf32_mul(
                layout.gf32_mul(previous_coefficient, values[-1]),
                _gf32_inverse(current_coefficient))))
        for index in range(ell):
            previous_index = (index - 1) % ell
            left = int(layout.gf32_mul(
                h[row_ids[index], variable_ids[previous_index]],
                values[previous_index]))
            right = int(layout.gf32_mul(
                h[row_ids[index], variable_ids[index]], values[index]))
            if left ^ right:
                raise ArithmeticError("unit-product cycle witness failed a check")
        witness = values

    cycle_matrix = np.zeros((ell, ell), dtype=np.int64)
    for index in range(ell):
        cycle_matrix[index, index] = numerator[index]
        cycle_matrix[index, (index - 1) % ell] = denominator[index]
    rank = int(layout.gf32_row_rank(cycle_matrix))
    expected_rank = ell - 1 if unit else ell
    if rank != expected_rank:
        raise ArithmeticError("cycle submatrix rank does not match its product")
    return {
        "numerator_coefficients": numerator,
        "denominator_coefficients": denominator,
        "product": product,
        "unit": unit,
        "witness_values": witness,
        "cycle_submatrix_rank": rank,
    }


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


def _compare_values(actual: Any, expected: Any, path: str,
                    tolerance: float = 1e-10) -> None:
    actual = _plain(actual)
    expected = _plain(expected)
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise ValueError("reference diagnostic keys differ at %s" % path)
        for key in expected:
            _compare_values(actual[key], expected[key], "%s.%s" % (path, key),
                            tolerance)
        return
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise ValueError("reference diagnostic length differs at %s" % path)
        for index, (left, right) in enumerate(zip(actual, expected)):
            _compare_values(left, right, "%s[%d]" % (path, index), tolerance)
        return
    if isinstance(expected, (float, int)) and not isinstance(expected, bool):
        if not isinstance(actual, (float, int)) or isinstance(actual, bool):
            raise ValueError("reference numeric type differs at %s" % path)
        if not math.isclose(float(actual), float(expected), rel_tol=0.0,
                            abs_tol=tolerance):
            raise ValueError("reference numeric value differs at %s" % path)
        return
    if actual != expected:
        raise ValueError("reference value differs at %s" % path)


def _read_reference(reference_root: Path) -> dict[str, Any]:
    manifest = json.loads((reference_root / "manifest.json").read_text(
        encoding="utf-8"))
    summary = json.loads((reference_root / "summary.json").read_text(
        encoding="utf-8"))
    if manifest.get("batch_uuid") != REFERENCE_BATCH_UUID \
            or summary.get("batch_uuid") != REFERENCE_BATCH_UUID:
        raise ValueError("reference edge batch UUID does not match frozen input")
    if (summary.get("holdout_complete") is not True
            or summary.get("holdout_pairs_completed") != 192
            or manifest.get("attempted_decoder_calls") != 384):
        raise ValueError("reference edge batch is not the complete frozen holdout")
    mapping = manifest.get("arm_mapping", {})
    if (mapping.get("control") !=
            "accepted deep H0D rebuilt by search-depth helper"
            or mapping.get("candidate") !=
            "one row-major absolute edge-label sweep from control"):
        raise ValueError("reference arm mapping does not match frozen predecessor")
    manifest_graphs = manifest.get("graph_diagnostics")
    manifest_candidates = manifest.get("candidate_diagnostics")
    summary_candidates = summary.get("search_diagnostics")
    if not all(isinstance(rows, list) for rows in
               (manifest_graphs, manifest_candidates, summary_candidates)):
        raise ValueError("reference edge artifacts lack full graph diagnostics")
    if not (len(manifest_graphs) == len(manifest_candidates)
            == len(summary_candidates) == len(GRAPH_SEEDS)):
        raise ValueError("reference edge artifacts do not contain six graphs")
    graph_by_seed: dict[int, Any] = {}
    candidate_by_seed: dict[int, Any] = {}
    for graph_diag, candidate_diag, summary_diag in zip(
            manifest_graphs, manifest_candidates, summary_candidates):
        seed = int(graph_diag["graph_seed"])
        if seed != int(candidate_diag["graph_seed"]) \
                or seed != int(summary_diag["graph_seed"]):
            raise ValueError("reference edge graph seeds are misaligned")
        _compare_values(candidate_diag, summary_diag,
                        "reference.search_diagnostics[%d]" % seed)
        graph_by_seed[seed] = graph_diag
        candidate_by_seed[seed] = candidate_diag
    if tuple(graph_by_seed) != GRAPH_SEEDS or tuple(candidate_by_seed) != GRAPH_SEEDS:
        raise ValueError("reference graph order/seeds differ from frozen six")
    return {"manifest": manifest, "summary": summary,
            "graph_by_seed": graph_by_seed,
            "candidate_by_seed": candidate_by_seed}


def _summary_edge_projection(diagnostic: Mapping[str, Any]) -> dict[str, Any]:
    edge = diagnostic["edge_sweep"]
    return {
        "control_J_bits": diagnostic["control_J_bits"],
        "candidate_initial_J_bits": diagnostic["candidate_J_initial_bits"],
        "candidate_final_J_bits": diagnostic["candidate_J_bits"],
        "candidate_J_gain_bits": diagnostic["candidate_J_gain_bits"],
        "changed_edge_count": edge["changed_edge_count"],
        "edge_sweep_count": edge["sweep_count"],
        "construction_stop": diagnostic["construction_stop"],
    }


def _check_reference_graph(reference: Mapping[str, Any], seed: int,
                           graph_diag: Any, candidate_diag: Any) -> None:
    expected_graph = reference["graph_by_seed"][seed]
    _compare_values(graph_diag, expected_graph,
                    "graph_diagnostics[%d]" % seed)
    expected_candidate = reference["candidate_by_seed"][seed]
    _compare_values(candidate_diag, expected_candidate,
                    "candidate_diagnostics[%d]" % seed)
    summary = reference["summary"]
    summary_seed = str(seed)
    expected_edge = summary.get("edge_diagnostics_by_graph", {}).get(summary_seed)
    expected_gauge = summary.get("gauge_by_graph", {}).get(summary_seed)
    if expected_edge is None or expected_gauge is None:
        raise ValueError("reference summary lacks edge/gauge projection for %d" % seed)
    _compare_values(_summary_edge_projection(candidate_diag), expected_edge,
                    "edge_diagnostics_by_graph[%d]" % seed)
    _compare_values(candidate_diag["gauge"], expected_gauge,
                    "gauge_by_graph[%d]" % seed)


def _rss_bytes() -> int:
    return runner_support.rss_bytes_required(resource)


def _resource_stop(started: float, now: Callable[[], float],
                   rss_fn: Callable[[], int]) -> str:
    return runner_support.resource_stop(
        started, now, rss_fn, wall_cap_s=WALL_CAP_S,
        rss_cap_bytes=RSS_CAP_BYTES, clamp_elapsed=True,
    )


def _json_write(path: Path, value: Any) -> None:
    runner_support.json_write(path, value, convert=_plain)


def _append_log(path: Path, line: str) -> None:
    runner_support.append_log(path, line)


def _base_summary() -> dict[str, Any]:
    return {
        "contract": CONTRACT,
        "batch_uuid": BATCH_UUID,
        "track": "EXPLORE",
        "reference_batch_uuid": REFERENCE_BATCH_UUID,
        "graph_seeds": list(GRAPH_SEEDS),
        "ell_range": [MIN_ELL, MAX_ELL],
        "batch_complete": False,
        "completed_graphs": [],
        "attempted_graphs": [],
        "per_graph": {},
        "totals_by_ell": None,
        "control_matrix_outcome": None,
        "edge_candidate_matrix_outcome": None,
        "stop_reason": "",
        "terminal_status": "RUNNING",
        "decoder_calls": 0,
        "sampled_frames": 0,
        "truth_prior_or_conditional_arrays_saved": False,
        "claim_ceiling": (
            "availability of unit-product simple Tanner cycles on the six "
            "fixed synthetic GF(32) matrices for ell=2..6 only; no global "
            "distance, composite-support, decoder-benefit, FER, f_eff, SKR, "
            "throughput, qualification, or route claim"
        ),
    }


def _new_graph_summary(seed: int) -> dict[str, Any]:
    return {
        "graph_seed": int(seed),
        "status": "IN_PROGRESS",
        "dfs_states": 0,
        "cycle_count": 0,
        "by_ell": {
            str(ell): {
                "cycle_count": 0,
                "control_unit_count": 0,
                "edge_candidate_unit_count": 0,
                "unit_to_nonunit": 0,
                "nonunit_to_unit": 0,
            }
            for ell in range(MIN_ELL, MAX_ELL + 1)
        },
        "control_matrix_outcome": None,
        "edge_candidate_matrix_outcome": None,
    }


def _matrix_outcome(unit_count: int) -> str:
    return "UNIT_PRESENT_IN_RANGE" if unit_count else "NO_UNIT_CYCLE_IN_RANGE"


def _csv_record(graph_seed: int, cycle: Mapping[str, Any],
                control: Mapping[str, Any], candidate: Mapping[str, Any]
                ) -> dict[str, Any]:
    control_unit = bool(control["unit"])
    candidate_unit = bool(candidate["unit"])
    transition = (
        "unit_to_nonunit" if control_unit and not candidate_unit else
        "nonunit_to_unit" if candidate_unit and not control_unit else
        "both_unit" if control_unit and candidate_unit else "neither_unit"
    )
    encode = lambda value: json.dumps(value, separators=(",", ":"))
    return {
        "graph_seed": int(graph_seed),
        "ell": len(cycle["rows"]),
        "cycle_key_json": encode(cycle["key"]),
        "check_rows_json": encode(cycle["rows"]),
        "variable_columns_json": encode(cycle["variables"]),
        "control_numerator_coefficients_json": encode(
            control["numerator_coefficients"]),
        "control_denominator_coefficients_json": encode(
            control["denominator_coefficients"]),
        "control_product": int(control["product"]),
        "control_unit": control_unit,
        "control_witness_values_json": encode(control["witness_values"]),
        "candidate_numerator_coefficients_json": encode(
            candidate["numerator_coefficients"]),
        "candidate_denominator_coefficients_json": encode(
            candidate["denominator_coefficients"]),
        "candidate_product": int(candidate["product"]),
        "candidate_unit": candidate_unit,
        "candidate_witness_values_json": encode(candidate["witness_values"]),
        "state_transition": transition,
    }


def execute_batch(
        *, out_root: str | Path, repo_root: str | Path | None = None,
        reference_root: str | Path | None = None,
        graph_builder: Callable[[int], Any],
        candidate_builder: Callable[[Any, np.ndarray, int], tuple[Any, Any, Any]],
        graph_preflight_fn: Callable[[Any, int], tuple[bool, Any]],
        command: str = COMMAND,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int] = _rss_bytes,
        ) -> dict[str, Any]:
    """Run a decoder-free census; graph/candidate callbacks are explicit."""
    root = validate_out_root(out_root, repo_root=repo_root)
    repository = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    reference = (Path(reference_root).resolve() if reference_root is not None
                 else repository / REFERENCE_ROOT_RELATIVE)
    started = float(now())
    root.mkdir(parents=True)
    manifest: dict[str, Any] = {
        "contract": CONTRACT,
        "batch_uuid": BATCH_UUID,
        "track": "EXPLORE",
        "status": "RUNNING",
        "exact_command": command,
        "reference_root": str(reference),
        "reference_batch_uuid": REFERENCE_BATCH_UUID,
        "graph_seeds": list(GRAPH_SEEDS),
        "graph_profile": {"n": N, "m": M, "E": EDGE_COUNT, "q": 32,
                           "polynomial": POLY},
        "enumeration": {
            "ell_min": MIN_ELL, "ell_max": MAX_ELL,
            "max_dfs_states_per_graph": MAX_DFS_STATES,
            "max_unique_cycles_per_graph": MAX_CYCLES_PER_GRAPH,
            "resource_check_every_dfs_states": RESOURCE_CHECK_STATES,
        },
        "budgets": {"total_wall_s": WALL_CAP_S,
                    "rss_bytes": RSS_CAP_BYTES, "decoder_calls": 0},
        "decoder_calls": 0,
        "sampled_frames": 0,
        "truth_prior_or_conditional_arrays_saved": False,
        "graph_diagnostics": [],
        "candidate_diagnostics": [],
        "attempted_graphs": [],
        "stop_reason": "",
    }
    summary = _base_summary()
    log_path = root / "EXPLORATION_LOG.md"
    manifest_path = root / "manifest.json"
    summary_path = root / "summary.json"
    cycles_path = root / "cycles.csv"
    _append_log(log_path, "EXPLORE batch %s started; decoder_calls=0" % BATCH_UUID)
    _json_write(manifest_path, manifest)
    _json_write(summary_path, summary)

    terminal = "IMPLEMENTATION_STOP"
    stop_reason = ""
    reference_data: dict[str, Any] | None = None
    csv_handle = cycles_path.open("w", newline="", encoding="utf-8")
    writer = csv.DictWriter(csv_handle, fieldnames=CYCLE_COLUMNS)
    writer.writeheader()

    def persist(status: str, reason: str) -> dict[str, Any]:
        nonlocal terminal, stop_reason
        terminal = status
        stop_reason = reason
        summary["terminal_status"] = terminal
        summary["stop_reason"] = stop_reason
        manifest["status"] = terminal
        manifest["stop_reason"] = stop_reason
        manifest["batch_complete"] = bool(summary["batch_complete"])
        _json_write(manifest_path, manifest)
        _json_write(summary_path, summary)
        _append_log(log_path, "terminal=%s stop_reason=%s completed_graphs=%d"
                    % (terminal, stop_reason or "none",
                       len(summary["completed_graphs"])))
        return summary

    try:
        reference_data = _read_reference(reference)
        manifest["reference_artifacts"] = ["manifest.json", "summary.json"]
        _json_write(manifest_path, manifest)
        _append_log(log_path, "read predecessor manifest/summary only")
        pmf = edge_runner.shape_pmf_grid()[0]["pmf"]
        for graph_seed in GRAPH_SEEDS:
            reason = _resource_stop(started, now, rss_fn)
            if reason:
                return persist("RESOURCE_STOP", reason)

            summary["attempted_graphs"].append(int(graph_seed))
            manifest["attempted_graphs"].append(int(graph_seed))
            _json_write(manifest_path, manifest)
            _json_write(summary_path, summary)
            graph = graph_builder(int(graph_seed))
            admitted, graph_diag = graph_preflight_fn(graph, int(graph_seed))
            manifest["graph_diagnostics"].append(_plain(graph_diag))
            _json_write(manifest_path, manifest)
            if not admitted:
                return persist("GRAPH_PREFLIGHT_FAILED", str(
                    _plain(graph_diag).get("failure_reason", "graph not admitted")))
            try:
                _compare_values(
                    graph_diag,
                    reference_data["graph_by_seed"][int(graph_seed)],
                    "graph_diagnostics[%d]" % int(graph_seed))
            except (KeyError, TypeError, ValueError) as exc:
                return persist("REFERENCE_MISMATCH_STOP", str(exc))

            dense = np.asarray(graph["dense"], dtype=np.int64)
            control, candidate, diagnostic = candidate_builder(
                dense, pmf, int(graph_seed))
            diagnostic = _plain(diagnostic)
            manifest["candidate_diagnostics"].append(diagnostic)
            _json_write(manifest_path, manifest)
            if not diagnostic.get("control_admitted", False) \
                    or not diagnostic.get("candidate_admitted", False) \
                    or diagnostic.get("construction_stop", True):
                return persist("CANDIDATE_ADMISSION_STOP",
                               str(diagnostic.get("failure_reason", "not admitted")))
            control = np.asarray(control, dtype=np.int64)
            candidate = np.asarray(candidate, dtype=np.int64)
            if not np.array_equal(control != 0, candidate != 0):
                return persist("CANDIDATE_SUPPORT_STOP",
                               "reconstructed arms do not share support")
            try:
                _check_reference_graph(reference_data, int(graph_seed),
                                      graph_diag, diagnostic)
            except (KeyError, TypeError, ValueError) as exc:
                return persist("REFERENCE_MISMATCH_STOP", str(exc))

            reason = _resource_stop(started, now, rss_fn)
            if reason:
                return persist("RESOURCE_STOP", reason)

            graph_summary = _new_graph_summary(int(graph_seed))
            summary["per_graph"][str(graph_seed)] = graph_summary

            def checkpoint(_states: int, _cycles: int) -> str | None:
                return _resource_stop(started, now, rss_fn)

            inventory = enumerate_cycles(
                control, max_states=MAX_DFS_STATES,
                max_cycles=MAX_CYCLES_PER_GRAPH, checkpoint=checkpoint)
            graph_summary["dfs_states"] = int(inventory["dfs_states"])
            for cycle in inventory["cycles"]:
                control_facts = cycle_matrix_facts(
                    control, cycle["rows"], cycle["variables"])
                candidate_facts = cycle_matrix_facts(
                    candidate, cycle["rows"], cycle["variables"])
                writer.writerow(_csv_record(
                    int(graph_seed), cycle, control_facts, candidate_facts))
                ell_summary = graph_summary["by_ell"][str(len(cycle["rows"]))]
                ell_summary["cycle_count"] += 1
                ell_summary["control_unit_count"] += int(control_facts["unit"])
                ell_summary["edge_candidate_unit_count"] += int(
                    candidate_facts["unit"])
                ell_summary["unit_to_nonunit"] += int(
                    control_facts["unit"] and not candidate_facts["unit"])
                ell_summary["nonunit_to_unit"] += int(
                    candidate_facts["unit"] and not control_facts["unit"])
                graph_summary["cycle_count"] += 1
            csv_handle.flush()

            if inventory["stop_reason"]:
                graph_summary["status"] = "PARTIAL_STOP"
                summary["per_graph"][str(graph_seed)] = graph_summary
                reason = str(inventory["stop_reason"])
                if reason.startswith("RESOURCE_STOP:"):
                    return persist("RESOURCE_STOP", reason.split(":", 1)[1])
                return persist("ENUMERATION_CAP_STOP", reason)

            graph_summary["status"] = "COMPLETE"
            control_units = 0
            candidate_units = 0
            for ell_summary in graph_summary["by_ell"].values():
                control_units += int(ell_summary["control_unit_count"])
                candidate_units += int(ell_summary["edge_candidate_unit_count"])
            graph_summary["control_matrix_outcome"] = _matrix_outcome(control_units)
            graph_summary["edge_candidate_matrix_outcome"] = _matrix_outcome(
                candidate_units)
            summary["completed_graphs"].append(int(graph_seed))
            _append_log(log_path,
                        "graph=%d complete states=%d cycles=%d control_units=%d "
                        "edge_candidate_units=%d"
                        % (graph_seed, graph_summary["dfs_states"],
                           graph_summary["cycle_count"], control_units,
                           candidate_units))
            _json_write(summary_path, summary)

            reason = _resource_stop(started, now, rss_fn)
            if reason:
                return persist("RESOURCE_STOP", reason)

        totals: dict[str, Any] = {}
        control_total = 0
        candidate_total = 0
        for ell in range(MIN_ELL, MAX_ELL + 1):
            counts = {
                "cycle_count": 0,
                "control_unit_count": 0,
                "edge_candidate_unit_count": 0,
                "unit_to_nonunit": 0,
                "nonunit_to_unit": 0,
            }
            for graph_summary in summary["per_graph"].values():
                for key in counts:
                    counts[key] += int(graph_summary["by_ell"][str(ell)][key])
            control_total += counts["control_unit_count"]
            candidate_total += counts["edge_candidate_unit_count"]
            totals[str(ell)] = counts
        summary["totals_by_ell"] = totals
        summary["control_matrix_outcome"] = _matrix_outcome(control_total)
        summary["edge_candidate_matrix_outcome"] = _matrix_outcome(
            candidate_total)
        summary["batch_complete"] = True
        return persist("INVENTORY_COMPLETE", "")
    except Exception as exc:
        _append_log(log_path, "implementation_exception=%s:%s"
                    % (type(exc).__name__, str(exc)))
        return persist("IMPLEMENTATION_STOP",
                       "implementation_exception:%s:%s"
                       % (type(exc).__name__, str(exc)))
    finally:
        csv_handle.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decoder-free GF(32) short-cycle inventory")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true",
                      help="run the frozen decoder-free inventory")
    mode.add_argument("--dry-run", action="store_true",
                      help="validate only the fresh output root")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE),
                        help="must equal the frozen fresh workspace root")
    return parser


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    root = validate_out_root(args.out_root)
    if not args.execute:
        result = dry_run(root)
    else:
        result = execute_batch(
            out_root=root,
            reference_root=_repo_root() / REFERENCE_ROOT_RELATIVE,
            graph_builder=edge_runner.build_profile_graph,
            candidate_builder=edge_runner.candidate_builder,
            graph_preflight_fn=edge_runner.graph_preflight,
            repo_root=_repo_root(), command=COMMAND,
        )
    print(json.dumps(_plain(result), indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
