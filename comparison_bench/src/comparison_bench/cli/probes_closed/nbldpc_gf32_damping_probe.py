"""Fixed-alpha damping comparison on the accepted GF(32) deep H0D graph.

This EXPLORE runner reuses the accepted search-depth graph and synthetic
marginal-shape helpers. The only arm difference is the explicit v35
``damping_alpha`` argument; imports and dry runs never bind or invoke v35.
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
from comparison_bench.cli.probes_closed import nbldpc_gf32_search_depth_probe as search_runner
from comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

CONTRACT = "NBLDPC-GF32-DAMPING-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "a3444f81-f091-4ffd-9c16-393c6062f6e3"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_damping_a3444f81"
SEED_PREFIX = "gf32-damping-v1"
CONTROL_ALPHA = 1.0
CANDIDATE_ALPHA = 0.5
MAX_ITER = 90
WARM_BELIEFS = None
FIELD = None
DECODER_SCHEDULE = "row_layered"

N = search_runner.N
M = search_runner.M
EDGE_COUNT = search_runner.EDGE_COUNT
GRAPH_SEEDS = search_runner.GRAPH_SEEDS
VAR_COUNTS = search_runner.VAR_COUNTS
CHECK_COUNTS = search_runner.CHECK_COUNTS
SHAPE_COUNTS = search_runner.SHAPE_COUNTS
SHAPE_TOTAL = search_runner.SHAPE_TOTAL
P0 = search_runner.P0
HOLDOUT_STREAMS = search_runner.HOLDOUT_STREAMS
HOLDOUT_FRAMES_PER_STREAM = search_runner.HOLDOUT_FRAMES_PER_STREAM
HOLDOUT_PAIRS = search_runner.HOLDOUT_PAIRS
MAX_CALLS = 2 * HOLDOUT_PAIRS
WALL_CAP_S = search_runner.WALL_CAP_S
CALL_CAP_S = search_runner.CALL_CAP_S
RSS_CAP_BYTES = search_runner.RSS_CAP_BYTES
SYNDROME_BITS = search_runner.SYNDROME_BITS
SIGNAL_DELTA = search_runner.SIGNAL_DELTA
SIGNAL_POSITIVE_GRAPHS = search_runner.SIGNAL_POSITIVE_GRAPHS
CONTROL_MIN = search_runner.CONTROL_MIN
CONTROL_MAX = search_runner.CONTROL_MAX
ARM_ALPHA = {"control": CONTROL_ALPHA, "candidate": CANDIDATE_ALPHA}
FRAME_FIELDS = tuple(search_runner.FRAME_FIELDS) + (
    "decoder_branch", "damping_alpha", "max_iter",
)
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.probes_closed.nbldpc_gf32_damping_probe "
    "--execute --out-root workspace/gf32_damping_a3444f81"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def shape_pmf_grid() -> list[dict[str, Any]]:
    """Expose only the single frozen p0=.55 synthetic marginal PMF."""
    return search_runner.shape_pmf_grid()


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
    return [], holdouts


def arm_order(frame: int) -> tuple[str, str]:
    return search_runner.arm_order(frame)


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
    """Run only the accepted pure field/PMF checks; no graph or decode."""
    checks = search_runner.verify_t0()
    row = shape_pmf_grid()[0]
    pmf = search_runner.predecessor.alignment.validate_pmf(row["pmf"])
    if not np.isclose(float(pmf.sum()), 1.0, rtol=0.0, atol=1e-12):
        raise AssertionError("damping PMF is not normalized")
    if np.flatnonzero(pmf).tolist() != [0, 1, 3, 7, 15, 31]:
        raise AssertionError("damping PMF support changed")
    if CANDIDATE_ALPHA != 0.5 or CONTROL_ALPHA != 1.0 or MAX_ITER != 90:
        raise AssertionError("frozen damping parameters changed")
    checks["fixed_damping_parameters_and_pmf"] = True
    return checks


def _validate_seed_plan() -> tuple[list[tuple[int, int, int, int]],
                                   list[tuple[int, int, int, int]]]:
    pilots, holdouts = seed_plan()
    seeds = [row[3] for row in holdouts]
    if pilots or len(holdouts) != HOLDOUT_PAIRS or len(set(seeds)) != len(seeds):
        raise AssertionError("damping seed plan is incomplete or duplicated")

    # The accepted predecessor helper checks the prior batches up to search
    # depth. Compare directly with each published plan as well for this prefix.
    old_plans = (
        prior_runner._seed_plan(),
        search_runner.fine_runner.predecessor.seed_plan(),
        search_runner.fine_runner.seed_plan(),
        search_runner.replica_runner.seed_plan(),
        search_runner.seed_plan(),
    )
    for plan in old_plans:
        old = {int(row[3]) for rows in plan for row in rows}
        if set(seeds) & old:
            raise AssertionError("damping seed plan overlaps a prior batch")
    return pilots, holdouts


def _serialized_pmf() -> dict[str, Any]:
    return {key: value for key, value in shape_pmf_grid()[0].items()
            if key != "pmf"}


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
            "graph_seeds": list(GRAPH_SEEDS),
            "cross_batch_baseline": False,
            "matrix_source": (
                "accepted SEARCH-DEPTH deep H0D reconstruction for each "
                "same-seed D10 graph; one common matrix per paired arms"),
        },
        "source_shape_proxy": {
            "source": "accepted historical 2M aggregate summary only",
            "counts": {str(e): count for e, count in SHAPE_COUNTS},
            "total": SHAPE_TOTAL,
            "role": "synthetic iid marginal shape proxy",
            "not_conditional_channel_reconstruction": True,
            "no_empirical_input_reads": True,
        },
        "pmf": _serialized_pmf(), "fixed_p0": P0,
        "pilot": "NOT_RUN_FIXED_PMF", "seed_namespace": SEED_PREFIX,
        "seed_plan_counts": {"pilot": 0, "holdout_pairs": len(holdouts)},
        "seed_plan_disjoint_from_prior_batches": True,
        "decoder": {
            "implementation": "v35.decode_row_layered_fftqspa",
            "schedule": DECODER_SCHEDULE,
            "max_iter": MAX_ITER,
            "warm_beliefs": WARM_BELIEFS,
            "field": FIELD,
            "control_damping_alpha": CONTROL_ALPHA,
            "candidate_damping_alpha": CANDIDATE_ALPHA,
            "only_arm_difference": "damping_alpha",
            "probability_mixing": (
                "p_damped=(1-alpha)*softmax(old)+alpha*softmax(new); "
                "then existing 1e-15 floor, normalization and log"),
            "result_return": "raw v35 DecoderResult unchanged",
        },
        "arm_mapping": {
            "control": "same accepted deep H0D; damping_alpha=1.0",
            "candidate": "same accepted deep H0D; damping_alpha=0.5",
        },
        "arm_dispatch": (
            "select decoder callable explicitly by arm label; never inspect "
            "matrix identity/content or mutable call state"),
        "pairing": (
            "same immutable deep H0D, sampled iid error, repeated prior and "
            "resulting syndrome within each pair"),
        "arm_order": "control first on even frame, candidate first on odd",
        "frame_stream": (
            "v10_seed('gf32-damping-v1:holdout:{graph_seed}:{stream}:{frame}')"),
        "error_sampling": "numpy.default_rng(seed).choice(32,size=128,p=pmf)",
        "budgets": {
            "total_wall_s": WALL_CAP_S,
            "per_decoder_call_s": CALL_CAP_S,
            "rss_bytes": RSS_CAP_BYTES,
            "max_pilot_calls": 0,
            "max_holdout_calls": MAX_CALLS,
            "max_decoder_calls": MAX_CALLS,
        },
        "resource_measurement": {
            "batch_wall_s": "measured with time.perf_counter",
            "max_call_wall_s": "measured around each synchronous decoder call",
            "max_rss_bytes": (
                "sampled process high-water RSS via the accepted d5 helper; "
                "Windows fallback is current process working set"),
        },
        "accounting": {
            "syndrome_bits_per_attempt": SYNDROME_BITS,
            "tag_bits": 0,
            "verification_status": "NOT_IMPLEMENTED",
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


def _write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def _start_outputs(root: Path, manifest: dict[str, Any]) -> None:
    root.mkdir(parents=False, exist_ok=False)
    _write_json(root / "manifest.json", manifest)
    with (root / "frame_records.csv").open(
            "w", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=FRAME_FIELDS).writeheader()
    _write_json(root / "summary.json", {"status": "RUNNING"})
    with (root / "EXPLORATION_LOG.md").open("w", encoding="utf-8") as stream:
        stream.write("# GF32 fixed-damping EXPLORE log\n\n")
        stream.write("Batch UUID: `%s`. Independent batch-end review: pending.\n"
                     % BATCH_UUID)


def _append_log(root: Path, message: str) -> None:
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as stream:
        stream.write("- %s\n" % message)


def _append_row(root: Path, row: Mapping[str, Any]) -> None:
    with (root / "frame_records.csv").open(
            "a", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=FRAME_FIELDS).writerow(
            {field: row.get(field) for field in FRAME_FIELDS})
    _append_log(
        root,
        "call %d %s/%s graph=%s stream=%s frame=%s seed=%s alpha=%s "
        "iterations=%s exact=%s syndrome_accept=%s wrong=%s status=%s "
        "wall_s=%.6f rss_b=%s"
        % (int(row["call_index"]), row["phase"], row["arm"],
           row["graph_seed"], row["stream"], row["frame"], row["seed"],
           row["damping_alpha"], row["iterations"], row["exact"],
           row["syndrome_accept"], row["syndrome_consistent_wrong"],
           row["status"], row["wall_s"], row["rss_b"]))


def _summarize(rows: list[dict[str, Any]],
               completed_pairs: list[dict[str, Any]],
               stop_reason: str) -> dict[str, Any]:
    holdout_rows = [row for row in rows if row["phase"] == "holdout"]
    control_rows = [row for row in holdout_rows if row["arm"] == "control"]
    candidate_rows = [row for row in holdout_rows if row["arm"] == "candidate"]
    success = lambda row: bool(row["exact"] and row["syndrome_accept"])
    complete = len(completed_pairs) == HOLDOUT_PAIRS
    control_successes = sum(success(row) for row in control_rows)
    candidate_successes = sum(success(row) for row in candidate_rows)
    per_graph: dict[str, Any] = {}
    for graph_seed in GRAPH_SEEDS:
        graph_rows = [row for row in holdout_rows
                      if int(row["graph_seed"]) == int(graph_seed)]
        graph_pairs = [pair for pair in completed_pairs
                       if int(pair["graph_seed"]) == int(graph_seed)]
        c_rows = [row for row in graph_rows if row["arm"] == "control"]
        k_rows = [row for row in graph_rows if row["arm"] == "candidate"]
        item = {
            "completed_pairs": len(graph_pairs),
            "control_attempts": len(c_rows),
            "candidate_attempts": len(k_rows),
        }
        if complete:
            c = sum(success(row) for row in c_rows)
            k = sum(success(row) for row in k_rows)
            item.update({"control_exact": int(c), "candidate_exact": int(k),
                         "delta_g": int(k - c)})
        else:
            item.update({"control_exact": None, "candidate_exact": None,
                         "delta_g": None})
        per_graph[str(graph_seed)] = item

    integrity = sum(
        str(row["status"]).startswith(("integrity_error", "decoder_exception"))
        for row in rows)
    resources = sum("resource_abort" in str(row["status"]) for row in rows)
    wrong_by_arm = {
        arm: sum(bool(row["syndrome_consistent_wrong"])
                 for row in rows if row["arm"] == arm)
        for arm in ("control", "candidate")
    }
    if not complete:
        classification = "INCOMPLETE"
        control_value = candidate_value = delta = states = None
    else:
        control_value = int(control_successes)
        candidate_value = int(candidate_successes)
        delta = int(candidate_successes - control_successes)
        states = {"control_only": 0, "candidate_only": 0,
                  "both": 0, "neither": 0}
        for pair in completed_pairs:
            c = bool(pair["control_success"])
            k = bool(pair["candidate_success"])
            key = {(True, False): "control_only", (False, True): "candidate_only",
                   (True, True): "both", (False, False): "neither"}[(c, k)]
            states[key] += 1
        positive = sum(item["delta_g"] > 0 for item in per_graph.values())
        if not CONTROL_MIN <= control_successes <= CONTROL_MAX:
            classification = "CONTROL_RANGE_UNINFORMATIVE"
        elif (delta >= SIGNAL_DELTA and positive >= SIGNAL_POSITIVE_GRAPHS
              and integrity == 0 and resources == 0):
            classification = "MECHANISM_SIGNAL"
        else:
            classification = "NO_SUFFICIENT_SIGNAL"

    decoder_calls = {"control": len(control_rows), "candidate": len(candidate_rows)}
    decoder_iterations = {
        arm: int(sum(int(row["iterations"]) for row in rows
                     if row["arm"] == arm))
        for arm in ("control", "candidate")
    }
    decoder_wall_s = {
        arm: float(sum(float(row["wall_s"]) for row in rows
                       if row["arm"] == arm))
        for arm in ("control", "candidate")
    }
    return {
        "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "classification": classification, "stop_reason": stop_reason,
        "holdout_complete": complete,
        "holdout_pairs_completed": len(completed_pairs),
        "pilot_control_exact_by_pmf": {},
        "fixed_p0": P0, "fixed_pmf_index": 0, "selected_pmf_index": None,
        "seed_namespace": SEED_PREFIX,
        "control_exact": control_value,
        "candidate_exact": candidate_value, "delta": delta,
        "delta_by_graph": per_graph, "paired_states": states,
        "decoder_calls_by_arm": decoder_calls,
        "decoder_iterations_by_arm": decoder_iterations,
        "decoder_wall_s_by_arm": decoder_wall_s,
        "syndrome_consistent_wrong_rows": sum(wrong_by_arm.values()),
        "syndrome_consistent_wrong_by_arm": wrong_by_arm,
        "integrity_violations": int(integrity),
        "resource_violations": int(resources),
        "authorization_violations": 0,
        "syndrome_bits_per_attempt": SYNDROME_BITS,
        "actual_syndrome_disclosure_bits": len(rows) * SYNDROME_BITS,
        "tag_bits": 0, "verification_status": "NOT_IMPLEMENTED",
        "undetected_status": "NOT_MEASURED",
        "FER": None, "f_eff": None, "SKR": None,
        "claim_ceiling": (
            "fixed damping comparison on six accepted deep H0D graphs under "
            "a synthetic iid marginal-shape proxy; no cross-batch pooling, "
            "conditional channel, FER, f_eff, SKR, throughput, qualification, "
            "publication, or route claim"),
    }


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root)
    t0 = verify_t0()
    pilots, holdouts = _validate_seed_plan()
    return {
        "status": "DRY_RUN", "out_root": str(root),
        "writes": 0, "empirical_input_reads": 0,
        "graph_construction_calls": 0, "candidate_construction_calls": 0,
        "decoder_calls": 0, "t0": t0,
        "fixed_p0": P0, "control_damping_alpha": CONTROL_ALPHA,
        "candidate_damping_alpha": CANDIDATE_ALPHA,
        "max_iter": MAX_ITER, "pilot_seed_count": len(pilots),
        "pilot_call_ceiling": 0, "holdout_pair_count": len(holdouts),
        "holdout_call_count": MAX_CALLS, "maximum_call_count": MAX_CALLS,
        "holdout_seeds_disjoint_from_prior_batches": True,
        "profile": {"n": N, "m": M, "E": EDGE_COUNT},
    }


def _resource_stop(started: float, now: Callable[[], float],
                   rss_fn: Callable[[], int | None], calls: int) -> str:
    if int(calls) >= MAX_CALLS:
        return "decoder_call_count_cap_before_next_call"
    elapsed = max(float(now()) - float(started), 0.0)
    rss = rss_fn()
    if elapsed >= WALL_CAP_S:
        return "total_wall_cap_before_next_call"
    if rss is not None and int(rss) >= RSS_CAP_BYTES:
        return "rss_cap_before_next_call"
    return ""


def _decoder_adapter(v35_decode: Callable[..., Any],
                     damping_alpha: float) -> Callable[..., Any]:
    """Bind fixed v35 kwargs and return its raw result unchanged."""
    alpha = float(damping_alpha)

    def decode(h, prior, syndrome):
        return v35_decode(
            h, prior, syndrome, max_iter=MAX_ITER,
            damping_alpha=alpha, warm_beliefs=WARM_BELIEFS, field=FIELD)

    return decode


def _bind_production_decoders() -> dict[str, Callable[..., Any]]:
    """Lazily bind two explicit v35 callbacks; only alpha differs."""
    from comparison_bench.formal_ir import v35_algorithm_development as v35

    decode = v35.decode_row_layered_fftqspa
    return {
        "control": _decoder_adapter(decode, CONTROL_ALPHA),
        "candidate": _decoder_adapter(decode, CANDIDATE_ALPHA),
    }


def execute_batch(*, out_root: str | Path, decode_fns: Mapping[str, Callable],
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
    if not isinstance(decode_fns, Mapping) or set(decode_fns) != {
            "control", "candidate"} or any(
                not callable(decode_fns[key]) for key in ("control", "candidate")):
        raise ValueError("explicit control and candidate decoder callbacks are required")
    if graph_builder is None or not callable(graph_builder):
        raise ValueError("an explicit graph builder is required")
    build_candidates = candidate_builder or search_runner._candidate_pair_for_graph
    root = validate_out_root(out_root, repo_root=repo_root)
    if rss_fn is None:
        rss_fn = d5._rss_bytes

    started = float(now())
    rss_samples: list[int] = []

    def sample_rss() -> int | None:
        value = rss_fn()
        if value is not None:
            rss_samples.append(int(value))
        return value

    sample_rss()
    manifest = _initial_manifest(command)
    _start_outputs(root, manifest)
    rows: list[dict[str, Any]] = []
    completed_pairs: list[dict[str, Any]] = []
    graph_diagnostics: list[dict[str, Any]] = []
    candidate_diagnostics: list[dict[str, Any]] = []
    graphs: dict[int, np.ndarray] = {}
    deep_matrices: dict[int, np.ndarray] = {}
    calls = 0
    stop_reason = ""
    terminal = "INCOMPLETE"

    def measured_cost() -> dict[str, Any]:
        return {
            "batch_wall_s": max(float(now()) - started, 0.0),
            "max_call_wall_s": (max(float(row["wall_s"]) for row in rows)
                                if rows else None),
            "max_rss_bytes": max(rss_samples) if rss_samples else None,
            "rss_samples": len(rss_samples),
        }

    def finish() -> dict[str, Any]:
        sample_rss()
        cost = measured_cost()
        summary = _summarize(rows, completed_pairs, stop_reason)
        summary.update({
            "terminal_status": terminal,
            "attempted_decoder_calls": calls,
            "attempted_frame_rows": len(rows),
            "attempted_call_counts": {
                "pilot": 0,
                "holdout": len(rows),
                "total": calls,
            },
            "resource_measurement": {
                "batch_wall_s": cost["batch_wall_s"],
                "max_call_wall_s": cost["max_call_wall_s"],
                "max_rss_bytes": cost["max_rss_bytes"],
                "rss_sample_count": cost["rss_samples"],
                "rss_scope": (
                    "process high-water RSS from d5._rss_bytes; Windows "
                    "fallback reports current process working set"),
            },
        })
        _write_json(root / "summary.json", summary)
        manifest.update({
            "status": terminal,
            "attempted_decoder_calls": calls,
            "attempted_call_counts": summary["attempted_call_counts"],
            "attempted_frame_rows": len(rows),
            "stop_reason": stop_reason,
            "resource_measurement": summary["resource_measurement"],
            "graph_diagnostics": graph_diagnostics,
            "candidate_diagnostics": candidate_diagnostics,
        })
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "terminal=%s stop_reason=%s calls=%d rows=%d"
                    % (terminal, stop_reason or "none", calls, len(rows)))
        return summary

    def record_row(graph_seed: int, stream: int, frame: int, seed: int,
                   arm: str, observed: Mapping[str, Any]) -> dict[str, Any]:
        base = search_runner.fine_runner.predecessor._record_row(
            call_index=calls, phase="holdout", pmf=shape_pmf_grid()[0],
            graph_seed=graph_seed, stream=stream, frame=frame, seed=seed,
            arm=arm, observed=observed)
        base.update({
            "decoder_branch": arm,
            "damping_alpha": ARM_ALPHA[arm],
            "max_iter": MAX_ITER,
        })
        rows.append(base)
        _append_row(root, base)
        return base

    def dispatch(graph_seed: int, stream: int, frame: int, seed: int,
                 arm: str, dense: np.ndarray, prior: np.ndarray,
                 truth: np.ndarray, syndrome: np.ndarray
                 ) -> tuple[dict[str, Any] | None, str]:
        nonlocal calls
        resource = _resource_stop(started, now, sample_rss, calls)
        if resource:
            return None, resource
        calls += 1
        observed, issue = prior_runner.decode_observation(
            decode_fns[arm], dense, prior, truth, syndrome,
            now=now, rss_fn=sample_rss)
        wall = float(observed["wall_s"])
        latest_rss = sample_rss()
        resource_reasons: list[str] = []
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
        if not 0 <= iterations <= MAX_ITER:
            observed.update({
                "exact": False, "syndrome_accept": False,
                "syndrome_consistent_wrong": False,
                "status": "integrity_error:iteration_count_out_of_range",
                "iterations": iterations,
            })
            issue = ";".join(part for part in
                              (str(issue) if issue else "",
                               "decoder_iteration_count_out_of_range") if part)
        if resource_reasons:
            resource_text = ",".join(resource_reasons)
            status = str(observed["status"])
            observed["status"] = status + "|resource_abort:" + resource_text
            issue = ";".join(part for part in
                              (str(issue) if issue else "", resource_text) if part)
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
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "T0 PASS; fixed PMF, alpha and seed plan verified")

        graph_failure = False
        for graph_seed in GRAPH_SEEDS:
            resource = _resource_stop(started, now, sample_rss, calls)
            if resource:
                stop_reason, terminal = resource, "RESOURCE_STOP"
                graph_diagnostics.append({
                    "graph_seed": int(graph_seed), "status": "not_started",
                    "admitted": False, "failure_reason": resource,
                })
                graph_failure = True
                break
            graph = graph_builder(int(graph_seed))
            admitted, diagnostic = search_runner.graph_preflight(graph, graph_seed)
            graph_diagnostics.append(diagnostic)
            if admitted:
                graphs[int(graph_seed)] = np.asarray(graph["dense"], dtype=np.int64)
            else:
                graph_failure = True
            _append_log(root, "graph preflight seed=%d admitted=%s reason=%s"
                        % (graph_seed, admitted,
                           diagnostic.get("failure_reason", "")))
            resource = _resource_stop(started, now, sample_rss, calls)
            if resource:
                stop_reason, terminal = resource, "RESOURCE_STOP"
                graph_failure = True
                break
        if graph_failure or len(graphs) != len(GRAPH_SEEDS):
            if not stop_reason:
                stop_reason = "GRAPH_PREFLIGHT_FAILED"
                terminal = stop_reason
            return finish()

        pmf = np.asarray(shape_pmf_grid()[0]["pmf"], dtype=np.float64)
        for graph_seed in GRAPH_SEEDS:
            resource = _resource_stop(started, now, sample_rss, calls)
            if resource:
                stop_reason, terminal = resource, "RESOURCE_STOP"
                return finish()
            onepass, deep, diagnostic = build_candidates(
                graphs[int(graph_seed)], pmf, int(graph_seed))
            candidate_diagnostics.append(diagnostic)
            _append_log(root, "accepted deep candidate seed=%d admitted=%s stop=%s"
                        % (graph_seed,
                           diagnostic.get("deep_candidate_admitted", deep is not None),
                           diagnostic.get("construction_stop", False)))
            admitted = bool(diagnostic.get("candidate_admitted", onepass is not None))
            deep_admitted = bool(diagnostic.get("deep_candidate_admitted", deep is not None))
            if (diagnostic.get("construction_stop") or not admitted
                    or not deep_admitted or onepass is None or deep is None):
                stop_reason = str(diagnostic.get(
                    "failure_reason", "DEEP_CANDIDATE_ADMISSION_STOP"))
                terminal = "DEEP_CANDIDATE_ADMISSION_STOP"
                return finish()
            deep_matrices[int(graph_seed)] = np.asarray(deep, dtype=np.int64)
            resource = _resource_stop(started, now, sample_rss, calls)
            if resource:
                stop_reason, terminal = resource, "RESOURCE_STOP"
                return finish()
        if len(deep_matrices) != len(GRAPH_SEEDS):
            stop_reason, terminal = "DEEP_CANDIDATE_ADMISSION_STOP", \
                "DEEP_CANDIDATE_ADMISSION_STOP"
            return finish()

        _, holdouts = _validate_seed_plan()
        pmf_entry = shape_pmf_grid()[0]
        prior = np.tile(pmf, (N, 1))
        for graph_seed, stream, frame, seed in holdouts:
            truth = prior_runner.sample_error(seed, pmf, width=N)
            common_h = deep_matrices[int(graph_seed)]
            paired = prior_runner.paired_arm_data(
                common_h, common_h, truth, prior)
            arm_results: dict[str, dict[str, Any]] = {}
            for arm in arm_order(frame):
                arm_input = paired[arm]
                row, issue = dispatch(
                    int(graph_seed), int(stream), int(frame), int(seed), arm,
                    arm_input["dense"], arm_input["prior"],
                    arm_input["truth"], arm_input["syndrome"])
                if row is not None:
                    arm_results[arm] = row
                if issue:
                    stop_reason = issue
                    terminal = ("RESOURCE_STOP" if any(
                        marker in issue for marker in
                        ("cap", "wall", "rss", "resource_abort"))
                                else "INTEGRITY_STOP")
                    return finish()
            if set(arm_results) == {"control", "candidate"}:
                completed_pairs.append({
                    "graph_seed": int(graph_seed), "stream": int(stream),
                    "frame": int(frame),
                    "control_success": bool(arm_results["control"]["exact"]
                                            and arm_results["control"]["syndrome_accept"]),
                    "candidate_success": bool(arm_results["candidate"]["exact"]
                                               and arm_results["candidate"]["syndrome_accept"]),
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
        description="Fixed-alpha GF(32) damping EXPLORE probe")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true",
                      help="run the frozen synthetic batch")
    mode.add_argument("--dry-run", action="store_true",
                      help="check pure math and the output path")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE),
                        help="must equal the frozen fresh workspace root")
    return parser


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    if not args.execute:
        result = dry_run(args.out_root)
    else:
        result = execute_batch(
            out_root=args.out_root, decode_fns=_bind_production_decoders(),
            graph_builder=search_runner.build_profile_graph,
            command=COMMAND)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
