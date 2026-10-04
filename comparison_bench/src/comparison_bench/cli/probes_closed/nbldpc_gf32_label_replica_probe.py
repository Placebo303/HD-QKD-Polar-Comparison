"""Fixed-PMF, new-graph GF(32) label-replica EXPLORE batch.

The input law is a synthetic iid marginal-shape proxy from an accepted
aggregate. This runner does not read empirical inputs or reconstruct a
conditional channel.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from comparison_bench.cli.probes_closed import nbldpc_gf32_label_probe as prior_runner
from comparison_bench.cli.probes_closed import nbldpc_gf32_shape_fine_probe as fine_runner
from comparison_bench.formal_ir import nonbinary_v10_common as common

predecessor = fine_runner.predecessor
BATCH_UUID = "7d6e57f0-b78c-45ea-b18d-dc2c2adec353"
CONTRACT = "NBLDPC-GF32-INDEPENDENT-REPLICA-DRAFT/PREREG_AND_AUTH.md"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_label_replica_7d6e57f0"
SEED_PREFIX = "gf32-label-replica-v1"

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
    "comparison_bench.cli.probes_closed.nbldpc_gf32_label_replica_probe "
    "--execute --out-root workspace/gf32_label_replica_7d6e57f0"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


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
            raise AssertionError("replica PMF changed frozen sparse support")
        if not np.isclose(float(pmf.sum()), 1.0, rtol=0.0, atol=1e-12):
            raise AssertionError("replica PMF is not normalized")
        if not np.isclose(fine_runner.predecessor.alignment.entropy_bits(pmf),
                          float(row["entropy_bits"]), rtol=0.0, atol=1e-12):
            raise AssertionError("replica PMF entropy changed")
    checks["replica_fixed_shape_pmf"] = True
    return checks


# These accepted helpers accept a graph seed and do not bind the old seed list.
build_profile_graph = fine_runner.build_profile_graph
graph_preflight = fine_runner.graph_preflight
_candidate_for_graph = fine_runner._candidate_for_graph


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
    if (pilots or len(holdouts) != HOLDOUT_PAIRS
            or len(set(seeds)) != len(seeds)
            or any(set(seeds) & old for old in old_seed_sets)):
        raise AssertionError("replica seed plan is invalid or overlaps prior batches")
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
        "arm_order": "control first on even frame index, candidate first on odd",
        "frame_stream": (
            "v10_seed('gf32-label-replica-v1:holdout:{graph_seed}:" 
            "{stream}:{frame}')"),
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
    fine_runner.predecessor._write_json(root / "manifest.json", manifest)
    with (root / "frame_records.csv").open(
            "w", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=FRAME_FIELDS).writeheader()
    with (root / "summary.json").open("w", encoding="utf-8") as stream:
        json.dump({"status": "RUNNING"}, stream)
        stream.write("\n")
    with (root / "EXPLORATION_LOG.md").open("w", encoding="utf-8") as stream:
        stream.write("# GF32 independent label-replica EXPLORE log\n\n")
        stream.write("Batch UUID: `%s`. Independent batch-end review: pending.\n"
                     % BATCH_UUID)


def _append_log(root: Path, message: str) -> None:
    fine_runner.predecessor._append_log(root, message)


def _append_row(root: Path, row: Mapping[str, Any]) -> None:
    fine_runner._append_row(root, row)


def _summarize(rows: list[dict[str, Any]],
               completed_pairs: list[dict[str, Any]],
               stop_reason: str) -> dict[str, Any]:
    """Aggregate only the six new graph seeds; mask incomplete denominators."""
    holdout_rows = [row for row in rows if row["phase"] == "holdout"]
    completed = len(completed_pairs) == HOLDOUT_PAIRS
    success = lambda row: bool(row["exact"] and row["syndrome_accept"])
    control_rows = [row for row in holdout_rows if row["arm"] == "control"]
    candidate_rows = [row for row in holdout_rows if row["arm"] == "candidate"]
    control_successes = sum(success(row) for row in control_rows)
    candidate_successes = sum(success(row) for row in candidate_rows)
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

    integrity = sum(
        str(row["status"]).startswith("integrity_error")
        or str(row["status"]).startswith("decoder_exception")
        for row in rows)
    resources = sum(
        str(row["status"]).startswith("resource_abort")
        or "|resource_abort:" in str(row["status"])
        for row in rows)
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
              >= SIGNAL_POSITIVE_GRAPHS and integrity == 0 and resources == 0):
            classification = "MECHANISM_SIGNAL"
        else:
            classification = "NO_SUFFICIENT_SIGNAL"

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
        "syndrome_consistent_wrong_rows": sum(
            bool(row["syndrome_consistent_wrong"]) for row in rows),
        "syndrome_consistent_wrong_by_arm": {
            arm: sum(bool(row["syndrome_consistent_wrong"])
                     for row in rows if row["arm"] == arm)
            for arm in ("control", "candidate")},
        "integrity_violations": int(integrity),
        "resource_violations": int(resources),
        "authorization_violations": 0,
        "syndrome_bits_per_attempt": SYNDROME_BITS,
        "tag_bits": 0, "verification_status": "NOT_IMPLEMENTED",
        "undetected_status": "NOT_MEASURED",
        "FER": None, "f_eff": None, "SKR": None,
        "claim_ceiling": (
            "synthetic iid marginal shape proxy on six new graphs; no pooled "
            "cross-batch result, conditional channel, FER, f_eff, SKR, "
            "throughput, qualification, or route claim"),
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
                                                    dict[str, Any]]] | None = None
                  ) -> dict[str, Any]:
    if decode_fn is None or not callable(decode_fn):
        raise ValueError("an explicit decoder callable is required")
    if graph_builder is None or not callable(graph_builder):
        raise ValueError("an explicit graph builder is required")
    build_candidate = candidate_builder or _candidate_for_graph
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
    candidates: dict[int, np.ndarray] = {}
    calls = 0
    stop_reason = ""
    terminal = "INCOMPLETE"

    def finish() -> dict[str, Any]:
        summary = _summarize(rows, completed_pairs, stop_reason)
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
            candidate, diagnostic = build_candidate(
                graphs[graph_seed], pmf, graph_seed)
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

        _, holdout_plan = _validate_seed_plan()
        for graph_seed, stream, frame, seed in holdout_plan:
            truth = prior_runner.sample_error(seed, pmf, width=N)
            pair = prior_runner.paired_arm_data(
                graphs[graph_seed], candidates[graph_seed], truth, prior)
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

        summary = _summarize(rows, completed_pairs, "")
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
        description="Fixed-PMF synthetic GF(32) label-replica EXPLORE probe")
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
