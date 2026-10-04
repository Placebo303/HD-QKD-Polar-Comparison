"""Frozen source-shape GF(32) label-alignment EXPLORE probe.

The error law is a synthetic marginal shape proxy built from an already
accepted aggregate. This module reads no empirical inputs and does not
reconstruct the historical conditional channel.
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
from comparison_bench.formal_ir import nbldpc_gf32_label_alignment as alignment
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as d10
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

BATCH_UUID = "fd01e03e-3832-4f01-bdb1-eecd744e4b40"
CONTRACT = "NBLDPC-GF32-SHAPE-LABEL-20260930/PREREG_AND_AUTH.md"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_shape_fd01e03e"

N = 128
M = 52
EDGE_COUNT = 256
VAR_COUNTS = {2: 128}
CHECK_COUNTS = {4: 4, 5: 48}
GRAPH_SEEDS = tuple(range(2026093801, 2026093807))
SHAPE_COUNTS = ((1, 2295), (3, 1126), (7, 557), (15, 304), (31, 146))
SHAPE_TOTAL = 4428
P0_GRID = (0.85, 0.65, 0.45, 0.25)
PILOT_FRAMES_PER_GRAPH = 4
PILOT_SUCCESS_MIN = 5
PILOT_SUCCESS_MAX = 19
HOLDOUT_STREAMS = (0, 1)
HOLDOUT_FRAMES_PER_STREAM = 16
HOLDOUT_PAIRS = 192
MAX_PILOT_CALLS = 96
MAX_HOLDOUT_CALLS = 384
MAX_CALLS = 480
WALL_CAP_S = 1800.0
CALL_CAP_S = 120.0
RSS_CAP_BYTES = 4 * 1024 ** 3
SYNDROME_BITS = 5 * M
SIGNAL_DELTA = 12
SIGNAL_POSITIVE_GRAPHS = 4
CONTROL_MIN = 39
CONTROL_MAX = 153

FRAME_FIELDS = (
    "call_index", "phase", "pmf_index", "p0", "graph_seed", "stream",
    "frame", "seed", "arm", "exact", "syndrome_accept",
    "syndrome_consistent_wrong", "status", "iterations", "wall_s",
    "rss_b", "syndrome_bits",
)
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_shape_probe "
    "--execute --out-root workspace/gf32_shape_fd01e03e"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def shape_pmf_grid() -> list[dict[str, Any]]:
    """Build the frozen four-point PMF grid from the 2M marginal shape."""
    q = np.zeros(32, dtype=np.float64)
    for symbol, count in SHAPE_COUNTS:
        q[symbol] = count / SHAPE_TOTAL
    if int(sum(count for _, count in SHAPE_COUNTS)) != SHAPE_TOTAL:
        raise AssertionError("frozen source-shape counts do not sum to 4428")
    rows = []
    for index, p0 in enumerate(P0_GRID):
        pmf = np.zeros(32, dtype=np.float64)
        pmf[0] = p0
        pmf += (1.0 - p0) * q
        pmf[0] = p0
        pmf = alignment.validate_pmf(pmf)
        rows.append({
            "index": index,
            "p0": p0,
            "formula": "p[0]=%.2f; p[e]=(1-p0)*count[e]/4428; "
                       "counts={1:2295,3:1126,7:557,15:304,31:146}"
                       % p0,
            "entropy_bits": alignment.entropy_bits(pmf),
            "nonzero_shape_entropy_bits": alignment.entropy_bits(q),
            "support": [0, 1, 3, 7, 15, 31],
            "pmf": pmf,
        })
    return rows


def pilot_seed(pmf_index: int, graph_seed: int, frame: int) -> int:
    return int(common.v10_seed(
        "gf32-shape-v1:pilot:%d:%d:%d"
        % (int(pmf_index), int(graph_seed), int(frame))))


def holdout_seed(graph_seed: int, stream: int, frame: int) -> int:
    return int(common.v10_seed(
        "gf32-shape-v1:holdout:%d:%d:%d"
        % (int(graph_seed), int(stream), int(frame))))


def seed_plan() -> tuple[list[tuple[int, int, int, int]],
                          list[tuple[int, int, int, int]]]:
    pilots = [
        (index, graph_seed, frame, pilot_seed(index, graph_seed, frame))
        for index in range(len(P0_GRID))
        for graph_seed in GRAPH_SEEDS
        for frame in range(PILOT_FRAMES_PER_GRAPH)
    ]
    holdouts = [
        (graph_seed, stream, frame,
         holdout_seed(graph_seed, stream, frame))
        for graph_seed in GRAPH_SEEDS
        for stream in HOLDOUT_STREAMS
        for frame in range(HOLDOUT_FRAMES_PER_STREAM)
    ]
    return pilots, holdouts


def arm_order(frame: int) -> tuple[str, str]:
    return (("control", "candidate") if int(frame) % 2 == 0
            else ("candidate", "control"))


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() \
        else (root / requested).resolve()
    expected = (root / OUT_ROOT_RELATIVE).resolve()
    if resolved != expected:
        raise ValueError("out-root must equal the frozen fresh root %s"
                         % expected)
    if resolved.exists():
        raise FileExistsError("refusing existing output root %s" % resolved)
    return resolved


def verify_t0() -> dict[str, bool]:
    """Pure field/PMF checks; no graph, decoder, empirical input or writes."""
    checks = alignment.verify_t0()
    grid = shape_pmf_grid()
    for entry in grid:
        pmf = alignment.validate_pmf(entry["pmf"])
        support = np.flatnonzero(pmf).tolist()
        if support != [0, 1, 3, 7, 15, 31]:
            raise AssertionError("source-shape PMF support changed")
        if not np.isclose(float(pmf.sum()), 1.0, rtol=0.0, atol=1e-12):
            raise AssertionError("source-shape PMF is not normalized")
        if not np.isclose(alignment.entropy_bits(pmf),
                          float(entry["entropy_bits"]),
                          rtol=0.0, atol=1e-12):
            raise AssertionError("source-shape PMF entropy changed")
    checks["sparse_shape_grid"] = True
    return checks


def build_profile_graph(graph_seed: int) -> dict[str, Any]:
    """Build one graph with the frozen custom D10 GF32 profile."""
    built = d10.build_degree_sequence_peg(
        N, M, VAR_COUNTS, CHECK_COUNTS, int(graph_seed))
    if built.get("status") != "ok":
        return {
            "status": str(built.get("status", "construction_failed")),
            "graph_seed": int(graph_seed), "n": N, "m": M,
            "E": int(built.get("E", EDGE_COUNT)),
            "edges": [], "coefficients": [], "dense": None,
            "structure": None, "admitted": False,
            "failure_reason": str(built.get("failure_reason", "")),
        }
    edges = built["edges"]
    coefficients = d10.coefficients_for_edges(edges, N, int(graph_seed))
    dense = d10.dense_from_edges(N, M, edges, coefficients)
    structure = d10.structural_record(dense, VAR_COUNTS, CHECK_COUNTS)
    return {
        "status": "ok", "graph_seed": int(graph_seed), "n": N, "m": M,
        "E": int(built["E"]), "edges": edges,
        "coefficients": coefficients, "dense": dense,
        "structure": structure, "admitted": bool(structure["admitted"]),
        "failure_reason": "" if structure["admitted"]
        else "D10 structural_record admission failed",
    }


def _histogram(values: np.ndarray) -> dict[int, int]:
    degrees, counts = np.unique(np.asarray(values, dtype=np.int64),
                                return_counts=True)
    return {int(d): int(c) for d, c in zip(degrees, counts) if int(c) > 0}


def graph_preflight(graph: Mapping[str, Any], graph_seed: int
                    ) -> tuple[bool, dict[str, Any]]:
    """Check dimensions/profile locally and D10 connectivity/rank evidence."""
    dense_value = graph.get("dense")
    if dense_value is None:
        return False, {
            "graph_seed": int(graph_seed), "status": str(graph.get("status")),
            "admitted": False, "failure_reason": str(
                graph.get("failure_reason", "missing dense matrix")),
        }
    dense = np.asarray(dense_value, dtype=np.int64)
    structure = graph.get("structure") or {}
    admission = structure.get("admission") or {}
    col_hist = _histogram(np.count_nonzero(dense, axis=0)) \
        if dense.ndim == 2 else {}
    row_hist = _histogram(np.count_nonzero(dense, axis=1)) \
        if dense.ndim == 2 else {}
    gf32_rank = int(structure.get("gf32_rank", -1))
    structural_rank = int(structure.get("structural_rank", -1))
    components = int(structure.get("connected_components", -1))
    duplicate_edges = int(structure.get("duplicate_edges", -1))
    expected = (
        dense.shape == (M, N)
        and np.all((dense >= 0) & (dense < 32))
        and int(np.count_nonzero(dense)) == EDGE_COUNT
        and col_hist == VAR_COUNTS
        and row_hist == CHECK_COUNTS
        and str(graph.get("status")) == "ok"
        and bool(graph.get("admitted"))
        and bool(structure.get("admitted"))
        and bool(admission)
        and all(bool(value) for value in admission.values())
        and gf32_rank == M and structural_rank == M
        and components == 1 and duplicate_edges == 0
    )
    return bool(expected), {
        "graph_seed": int(graph_seed), "status": str(graph.get("status")),
        "admitted": bool(expected), "n": int(dense.shape[1]),
        "m": int(dense.shape[0]), "E": int(np.count_nonzero(dense)),
        "variable_degree_histogram": col_hist,
        "check_degree_histogram": row_hist,
        "connected_components": components,
        "structural_rank": structural_rank, "gf32_rank": gf32_rank,
        "duplicate_edges": duplicate_edges,
        "admission": {str(k): bool(v) for k, v in admission.items()},
        "failure_reason": "" if expected else str(
            graph.get("failure_reason", "custom graph preflight failed")),
    }


def _candidate_for_graph(dense: np.ndarray, pmf: np.ndarray,
                         graph_seed: int) -> tuple[np.ndarray | None,
                                                   dict[str, Any]]:
    result = alignment.align_labels(dense, pmf)
    candidate = np.asarray(result["candidate"], dtype=np.int64)
    labels = np.asarray(result["labels"], dtype=np.int64)
    gauge_equal = bool(result["gauge_equal"] and np.array_equal(
        alignment.scale_columns(candidate, alignment.column_inverse(labels)),
        dense))
    support_equal = bool(result["support_equal"] and np.array_equal(
        dense != 0, candidate != 0))
    same_degrees = bool(np.array_equal(
        np.count_nonzero(dense, axis=0), np.count_nonzero(candidate, axis=0))
        and np.array_equal(np.count_nonzero(dense, axis=1),
                           np.count_nonzero(candidate, axis=1)))
    candidate_rank = int(d10.gf32_row_rank(candidate))
    baseline_rank = int(d10.gf32_row_rank(dense))
    nontrivial = bool(np.any(labels != 1))
    score_gain = float(result["Jc"] - result["J0"])
    admitted = bool(
        result["candidate_admitted"] and nontrivial
        and score_gain > alignment.MIN_SCORE_GAIN
        and support_equal and same_degrees
        and baseline_rank == M and candidate_rank == M and gauge_equal)
    diagnostic = {
        "graph_seed": int(graph_seed),
        "labels": [int(x) for x in labels],
        "J0_bits": float(result["J0"]), "Jc_bits": float(result["Jc"]),
        "score_gain_bits": score_gain,
        "baseline_rank": baseline_rank, "candidate_rank": candidate_rank,
        "support_equal": support_equal, "degrees_equal": same_degrees,
        "gauge_equal": gauge_equal, "nontrivial": nontrivial,
        "candidate_admitted": admitted,
    }
    return (candidate if admitted else None), diagnostic


def _resource_stop(started: float, now: Callable[[], float],
                   rss_fn: Callable[[], int | None]) -> str:
    if max(float(now()) - float(started), 0.0) >= WALL_CAP_S:
        return "total_wall_cap_before_next_call"
    rss = rss_fn()
    if rss is not None and int(rss) >= RSS_CAP_BYTES:
        return "rss_cap_before_next_call"
    return ""


def _serialized_grid() -> list[dict[str, Any]]:
    return [{k: v for k, v in row.items() if k != "pmf"}
            for row in shape_pmf_grid()]


def _initial_manifest(command: str) -> dict[str, Any]:
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
        "pmf_grid": _serialized_grid(),
        "decoder_profile": (
            "v35 row-layered FFT-QSPA; max_iter=90; damping_alpha=1.0; "
            "warm_beliefs=None; field=None via accepted adapter; prior zeros "
            "are floored to 1e-15 and row-renormalized internally"),
        "pairing": "same sampled error and same repeated PMF prior; own syndrome per arm",
        "arm_order": "control first on even frame index, candidate first on odd",
        "frame_streams": {
            "pilot": "v10_seed('gf32-shape-v1:pilot:{pmf_index}:{graph_seed}:{frame}')",
            "holdout": "v10_seed('gf32-shape-v1:holdout:{graph_seed}:{stream}:{frame}')",
        },
        "error_sampling": "numpy.default_rng(seed).choice(32,size=128,p=pmf)",
        "budgets": {
            "total_wall_s": WALL_CAP_S, "per_decoder_call_s": CALL_CAP_S,
            "rss_bytes": RSS_CAP_BYTES, "max_pilot_calls": MAX_PILOT_CALLS,
            "max_holdout_calls": MAX_HOLDOUT_CALLS,
            "max_decoder_calls": MAX_CALLS,
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
    _write_json(root / "manifest.json", manifest)
    with (root / "frame_records.csv").open(
            "w", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=FRAME_FIELDS).writeheader()
    with (root / "summary.json").open("w", encoding="utf-8") as stream:
        json.dump({"status": "RUNNING"}, stream)
        stream.write("\n")
    with (root / "EXPLORATION_LOG.md").open("w", encoding="utf-8") as stream:
        stream.write("# GF32 source-shape EXPLORE log\n\n")
        stream.write("Batch UUID: `%s`. Independent batch-end review: pending.\n"
                     % BATCH_UUID)


def _write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def _append_log(root: Path, message: str) -> None:
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as stream:
        stream.write("- %s\n" % message)


def _append_row(root: Path, row: Mapping[str, Any]) -> None:
    with (root / "frame_records.csv").open(
            "a", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=FRAME_FIELDS).writerow(row)
    _append_log(
        root, "call %d %s/%s graph=%s stream=%s frame=%s seed=%s exact=%s "
        "syndrome_accept=%s syndrome_consistent_wrong=%s status=%s "
        "wall_s=%.6f rss_b=%s" % (
            int(row["call_index"]), row["phase"], row["arm"],
            row["graph_seed"], row["stream"], row["frame"], row["seed"],
            row["exact"], row["syndrome_accept"],
            row["syndrome_consistent_wrong"], row["status"],
            row["wall_s"], row["rss_b"]))


def _record_row(*, call_index: int, phase: str,
                pmf: Mapping[str, Any], graph_seed: int,
                stream: int | str, frame: int, seed: int, arm: str,
                observed: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "call_index": int(call_index), "phase": phase,
        "pmf_index": int(pmf["index"]), "p0": float(pmf["p0"]),
        "graph_seed": int(graph_seed), "stream": stream,
        "frame": int(frame), "seed": int(seed), "arm": arm,
        "exact": bool(observed["exact"]),
        "syndrome_accept": bool(observed["syndrome_accept"]),
        "syndrome_consistent_wrong": bool(
            observed["syndrome_consistent_wrong"]),
        "status": str(observed["status"]),
        "iterations": int(observed["iterations"]),
        "wall_s": float(observed["wall_s"]),
        "rss_b": observed["rss_b"],
        "syndrome_bits": SYNDROME_BITS,
    }


def _summarize(rows: list[dict[str, Any]],
               completed_pairs: list[dict[str, Any]],
               pilot_results: list[dict[str, Any]],
               stop_reason: str) -> dict[str, Any]:
    holdout_control = [r for r in rows
                       if r["phase"] == "holdout" and r["arm"] == "control"]
    holdout_candidate = [r for r in rows
                         if r["phase"] == "holdout"
                         and r["arm"] == "candidate"]
    exact_success = lambda row: bool(row["exact"] and row["syndrome_accept"])
    c_exact = sum(exact_success(row) for row in holdout_control)
    k_exact = sum(exact_success(row) for row in holdout_candidate)
    per_graph = {}
    for graph_seed in GRAPH_SEEDS:
        paired = [pair for pair in completed_pairs
                  if int(pair["graph_seed"]) == graph_seed]
        control_rows = [row for row in holdout_control
                        if int(row["graph_seed"]) == graph_seed]
        candidate_rows = [row for row in holdout_candidate
                          if int(row["graph_seed"]) == graph_seed]
        if not paired:
            per_graph[str(graph_seed)] = {
                "completed_pairs": 0,
                "control_attempts": len(control_rows),
                "candidate_attempts": len(candidate_rows),
                "control_exact": None, "candidate_exact": None,
                "delta_g": None,
            }
        else:
            c = sum(exact_success(row) for row in control_rows)
            k = sum(exact_success(row) for row in candidate_rows)
            per_graph[str(graph_seed)] = {
                "completed_pairs": len(paired),
                "control_attempts": len(control_rows),
                "candidate_attempts": len(candidate_rows),
                "control_exact": int(c), "candidate_exact": int(k),
                "delta_g": int(k - c),
            }
    complete = len(completed_pairs) == HOLDOUT_PAIRS
    integrity = sum(
        str(r["status"]) == "integrity_error"
        or str(r["status"]).startswith("decoder_exception") for r in rows)
    resources = sum(str(r["status"]) == "resource_abort" for r in rows)
    if not complete:
        classification = "INCOMPLETE"
    elif not CONTROL_MIN <= c_exact <= CONTROL_MAX:
        classification = "CONTROL_RANGE_UNINFORMATIVE"
    elif (k_exact - c_exact >= SIGNAL_DELTA
          and sum((v["delta_g"] or 0) > 0 for v in per_graph.values())
          >= SIGNAL_POSITIVE_GRAPHS and integrity == 0 and resources == 0):
        classification = "MECHANISM_SIGNAL"
    else:
        classification = "NO_SUFFICIENT_SIGNAL"
    pair_states = {"control_only": 0, "candidate_only": 0,
                   "both": 0, "neither": 0}
    for pair in completed_pairs:
        c, k = bool(pair["control_exact"]), bool(pair["candidate_exact"])
        label = {(True, False): "control_only", (False, True): "candidate_only",
                 (True, True): "both", (False, False): "neither"}[(c, k)]
        pair_states[label] += 1
    pilot_exact = {str(row["pmf_index"]): row["control_exact"]
                   for row in pilot_results}
    return {
        "classification": classification, "stop_reason": stop_reason,
        "holdout_complete": complete,
        "holdout_pairs_completed": len(completed_pairs),
        "pilot_control_exact_by_pmf": pilot_exact,
        "control_exact": int(c_exact) if complete else None,
        "candidate_exact": int(k_exact) if complete else None,
        "delta": int(k_exact - c_exact) if complete else None,
        "delta_by_graph": per_graph, "paired_states": pair_states,
        "syndrome_consistent_wrong_rows": sum(
            bool(r["syndrome_consistent_wrong"]) for r in rows),
        "syndrome_consistent_wrong_by_arm": {
            arm: sum(bool(r["syndrome_consistent_wrong"])
                     for r in rows if r["arm"] == arm)
            for arm in ("control", "candidate")},
        "integrity_violations": integrity,
        "resource_violations": resources,
        "authorization_violations": 0,
        "syndrome_bits_per_attempt": SYNDROME_BITS,
        "tag_bits": 0, "verification_status": "NOT_IMPLEMENTED",
        "undetected_status": "NOT_MEASURED",
        "FER": None, "f_eff": None, "SKR": None,
        "claim_ceiling": (
            "synthetic iid marginal shape proxy; no conditional channel, FER, "
            "f_eff, SKR, throughput, qualification, or route claim"),
    }


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root)
    t0 = verify_t0()
    pilot_rows, holdout_rows = seed_plan()
    p_seeds = [row[3] for row in pilot_rows]
    h_seeds = [row[3] for row in holdout_rows]
    if (len(set(p_seeds)) != len(p_seeds)
            or len(set(h_seeds)) != len(h_seeds)
            or set(p_seeds) & set(h_seeds)):
        raise AssertionError("pilot/holdout seed plan is not unique and disjoint")
    if len(pilot_rows) != MAX_PILOT_CALLS \
            or len(holdout_rows) != HOLDOUT_PAIRS:
        raise AssertionError("frozen call plan count changed")
    return {
        "status": "DRY_RUN", "out_root": str(root),
        "writes": 0, "empirical_input_reads": 0,
        "graph_construction_calls": 0, "decoder_calls": 0,
        "t0": t0, "pilot_call_ceiling": MAX_PILOT_CALLS,
        "holdout_pair_count": HOLDOUT_PAIRS,
        "holdout_call_count": MAX_HOLDOUT_CALLS,
        "maximum_call_count": MAX_CALLS,
        "pilot_holdout_seed_disjoint": True,
        "profile": {"n": N, "m": M, "E": EDGE_COUNT},
    }


def execute_batch(*, out_root: str | Path, decode_fn,
                  graph_builder: Callable[[int], Mapping[str, Any]],
                  command: str = COMMAND,
                  repo_root: str | Path | None = None,
                  now: Callable[[], float] = time.perf_counter,
                  rss_fn: Callable[[], int | None] | None = None
                  ) -> dict[str, Any]:
    """Run the frozen sequence with explicitly injected graph/decoder calls."""
    if decode_fn is None or not callable(decode_fn):
        raise ValueError("an explicit decoder callable is required")
    if graph_builder is None or not callable(graph_builder):
        raise ValueError("an explicit graph builder is required")
    root = validate_out_root(out_root, repo_root=repo_root)
    if rss_fn is None:
        rss_fn = d5._rss_bytes
    started = float(now())
    manifest = _initial_manifest(command)
    _start_outputs(root, manifest)
    rows: list[dict[str, Any]] = []
    completed_pairs: list[dict[str, Any]] = []
    pilot_results: list[dict[str, Any]] = []
    graph_diagnostics: list[dict[str, Any]] = []
    candidate_diagnostics: list[dict[str, Any]] = []
    graphs: dict[int, np.ndarray] = {}
    candidates: dict[int, np.ndarray] = {}
    calls = 0
    selected_pmf_index: int | None = None
    stop_reason = ""
    terminal = "INCOMPLETE"

    def finish() -> dict[str, Any]:
        summary = _summarize(rows, completed_pairs, pilot_results, stop_reason)
        summary.update({
            "terminal_status": terminal,
            "selected_pmf_index": selected_pmf_index,
            "attempted_decoder_calls": calls,
            "attempted_frame_rows": len(rows),
            "attempted_call_counts": {
                "pilot": sum(r["phase"] == "pilot" for r in rows),
                "holdout": sum(r["phase"] == "holdout" for r in rows),
                "total": calls,
            },
            "batch_wall_s": max(float(now()) - started, 0.0),
        })
        _write_json(root / "summary.json", summary)
        manifest.update({
            "status": terminal, "selected_pmf_index": selected_pmf_index,
            "attempted_decoder_calls": calls,
            "attempted_call_counts": summary["attempted_call_counts"],
            "attempted_frame_rows": len(rows), "stop_reason": stop_reason,
            "batch_wall_s": summary["batch_wall_s"],
            "graph_diagnostics": graph_diagnostics,
            "candidate_diagnostics": candidate_diagnostics,
        })
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "terminal=%s stop_reason=%s calls=%d rows=%d"
                    % (terminal, stop_reason or "none", calls, len(rows)))
        return summary

    def record_row(phase: str, pmf: Mapping[str, Any], graph_seed: int,
                   stream: int | str, frame: int, seed: int, arm: str,
                   observed: Mapping[str, Any]) -> dict[str, Any]:
        row = _record_row(call_index=calls, phase=phase, pmf=pmf,
                          graph_seed=graph_seed, stream=stream, frame=frame,
                          seed=seed, arm=arm, observed=observed)
        rows.append(row)
        _append_row(root, row)
        return row

    def dispatch(phase: str, pmf: Mapping[str, Any], graph_seed: int,
                 stream: int | str, frame: int, seed: int, arm: str,
                 dense: np.ndarray, prior: np.ndarray, truth: np.ndarray,
                 syndrome: np.ndarray) -> tuple[dict[str, Any] | None, str]:
        nonlocal calls
        if calls >= MAX_CALLS:
            return None, "decoder_call_count_cap_before_next_call"
        resource = _resource_stop(started, now, rss_fn)
        if resource:
            return None, resource
        calls += 1
        observed, issue = prior_runner.decode_observation(
            decode_fn, dense, prior, truth, syndrome, now=now, rss_fn=rss_fn)
        if not issue:
            elapsed = max(float(now()) - started, 0.0)
            if elapsed > WALL_CAP_S:
                issue = "total_wall_cap_after_call"
                observed["status"] = "resource_abort"
            elif observed["rss_b"] is not None \
                    and int(observed["rss_b"]) >= RSS_CAP_BYTES:
                issue = "rss_cap_after_call"
                observed["status"] = "resource_abort"
        row = record_row(phase, pmf, graph_seed, stream, frame, seed,
                         arm, observed)
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
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "T0 PASS")

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

        pilot_seeds, holdout_rows = seed_plan()
        p_values = [row[3] for row in pilot_seeds]
        h_values = [row[3] for row in holdout_rows]
        if (len(set(p_values)) != len(p_values)
                or len(set(h_values)) != len(h_values)
                or set(p_values) & set(h_values)):
            stop_reason = "PILOT_HOLDOUT_SEED_COLLISION"
            terminal = stop_reason
            return finish()

        selected: dict[str, Any] | None = None
        for pmf_entry in shape_pmf_grid():
            p = pmf_entry["pmf"]
            prior = np.tile(p, (N, 1))
            exact_successes = 0
            _append_log(root, "pilot PMF %d started; control only"
                        % int(pmf_entry["index"]))
            for graph_seed in GRAPH_SEEDS:
                for frame in range(PILOT_FRAMES_PER_GRAPH):
                    seed = pilot_seed(int(pmf_entry["index"]), graph_seed, frame)
                    truth = prior_runner.sample_error(seed, p, width=N)
                    dense = graphs[graph_seed]
                    syndrome = np.asarray(layout.gf32_syndrome(dense, truth),
                                          dtype=np.int64)
                    row, issue = dispatch(
                        "pilot", pmf_entry, graph_seed, "pilot", frame, seed,
                        "control", dense, prior, truth, syndrome)
                    if row is not None and row["exact"] \
                            and row["syndrome_accept"]:
                        exact_successes += 1
                    if issue:
                        stop_reason = issue
                        terminal = ("RESOURCE_STOP" if "cap" in issue
                                    else "INTEGRITY_STOP")
                        return finish()
            pilot_results.append({
                "pmf_index": int(pmf_entry["index"]),
                "p0": float(pmf_entry["p0"]),
                "control_exact": int(exact_successes),
                "calls": len(GRAPH_SEEDS) * PILOT_FRAMES_PER_GRAPH,
            })
            _append_log(root, "pilot PMF %d control exact=%d/24"
                        % (int(pmf_entry["index"]), exact_successes))
            if PILOT_SUCCESS_MIN <= exact_successes <= PILOT_SUCCESS_MAX:
                selected = pmf_entry
                selected_pmf_index = int(pmf_entry["index"])
                break
        if selected is None:
            stop_reason = "CONTROL_RANGE_UNINFORMATIVE"
            terminal = stop_reason
            return finish()

        selected_p = selected["pmf"]
        for graph_seed in GRAPH_SEEDS:
            resource = _resource_stop(started, now, rss_fn)
            if resource:
                stop_reason = resource
                terminal = "RESOURCE_STOP"
                return finish()
            candidate, diagnostic = _candidate_for_graph(
                graphs[graph_seed], selected_p, graph_seed)
            candidate_diagnostics.append(diagnostic)
            _append_log(root, "candidate seed=%d admitted=%s J0=%.12f Jc=%.12f"
                        % (graph_seed, diagnostic["candidate_admitted"],
                           diagnostic["J0_bits"], diagnostic["Jc_bits"]))
            if candidate is not None:
                candidates[graph_seed] = candidate
        if len(candidates) != len(GRAPH_SEEDS):
            stop_reason = "NO_NONTRIVIAL_LABEL_CANDIDATE"
            terminal = stop_reason
            return finish()

        p = selected_p
        prior = np.tile(p, (N, 1))
        for graph_seed, stream, frame, seed in holdout_rows:
            truth = prior_runner.sample_error(seed, p, width=N)
            pair = prior_runner.paired_arm_data(
                graphs[graph_seed], candidates[graph_seed], truth, prior)
            arm_results: dict[str, dict[str, Any]] = {}
            for arm in arm_order(frame):
                arm_input = pair[arm]
                row, issue = dispatch(
                    "holdout", selected, graph_seed, stream, frame, seed,
                    arm, arm_input["dense"], arm_input["prior"],
                    arm_input["truth"], arm_input["syndrome"])
                if row is not None:
                    arm_results[arm] = row
                if issue:
                    stop_reason = issue
                    terminal = ("RESOURCE_STOP" if "cap" in issue
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

        summary = _summarize(rows, completed_pairs, pilot_results, "")
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
        description="Frozen synthetic GF(32) source-shape label EXPLORE probe")
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
