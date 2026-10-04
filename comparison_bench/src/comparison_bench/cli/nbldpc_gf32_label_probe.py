"""One frozen EXPLORE probe for fixed-support GF(32) label alignment.

Default invocation is a read-only dry run. The authorized synthetic batch is
available only with ``--execute`` and writes a fresh, fixed workspace root.
Tests inject tiny fake graphs/decoders through pure helpers; this module never
loads private/model inputs.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5
from comparison_bench.formal_ir import nbldpc_gf32_label_alignment as mechanism

BATCH_UUID = "a74e912c-4bac-4d7d-9fe9-2358bd8a85d1"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_label_a74e912c"
WALL_CAP_S = 1800.0
CALL_CAP_S = 120.0
RSS_CAP_BYTES = 4 * 1024 ** 3
N = 128
M = 118
EDGE_COUNT = 301
SYNDROME_BITS = 5 * M
MAX_CALLS = 456
MAX_PILOT_CALLS = 72
HOLDOUT_PAIRS = 192
FRAME_FIELDS = (
    "phase", "pmf_index", "p0", "graph_seed", "stream", "frame",
    "seed", "arm", "exact", "syndrome_accept",
    "syndrome_consistent_wrong", "status", "iterations", "wall_s",
    "rss_b", "syndrome_bits",
)
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_label_probe "
    "--execute --out-root workspace/gf32_label_a74e912c"
)

__all__ = [
    "BATCH_UUID", "OUT_ROOT_RELATIVE", "WALL_CAP_S", "CALL_CAP_S",
    "RSS_CAP_BYTES", "FRAME_FIELDS", "pilot_seed", "holdout_seed",
    "arm_order", "sample_error", "paired_arm_data", "validate_out_root", "check_before_call",
    "decode_observation", "build_parser", "dry_run", "execute_batch",
    "main",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def pilot_seed(pmf_index: int, graph_seed: int, frame: int) -> int:
    """Frozen control-pilot seed namespace."""
    return int(common.v10_seed(
        "gf32-label-v1:pilot:%d:%d:%d"
        % (int(pmf_index), int(graph_seed), int(frame))))


def holdout_seed(graph_seed: int, stream: int, frame: int) -> int:
    """Frozen paired-holdout seed namespace."""
    return int(common.v10_seed(
        "gf32-label-v1:holdout:%d:%d:%d"
        % (int(graph_seed), int(stream), int(frame))))


def arm_order(frame: int) -> tuple[str, str]:
    """Alternate control-first and candidate-first by paired frame index."""
    return ("control", "candidate") if int(frame) % 2 == 0 \
        else ("candidate", "control")


def sample_error(seed: int, pmf: Any, width: int = N) -> np.ndarray:
    """Draw one reproducible additive GF(32) error vector."""
    p = mechanism.validate_pmf(pmf)
    return np.random.default_rng(int(seed)).choice(
        mechanism.Q, size=int(width), p=p).astype(np.int64)


def paired_arm_data(control_h: Any, candidate_h: Any, truth: Any,
                    prior: Any) -> dict[str, dict[str, Any]]:
    """Share the same truth/prior and compute each arm's own syndrome."""
    truth_array = np.asarray(truth, dtype=np.int64).ravel()
    prior_array = np.asarray(prior, dtype=np.float64)
    arms = {"control": np.asarray(control_h, dtype=np.int64),
            "candidate": np.asarray(candidate_h, dtype=np.int64)}
    return {
        arm: {
            "dense": dense,
            "truth": truth_array,
            "prior": prior_array,
            "syndrome": np.asarray(layout.gf32_syndrome(dense, truth_array),
                                    dtype=np.int64),
        }
        for arm, dense in arms.items()
    }


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None) -> Path:
    """Accept only the frozen fresh workspace root; never overwrite."""
    root = Path(repo_root).resolve() if repo_root is not None \
        else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() \
        else (root / requested).resolve()
    expected = (root / OUT_ROOT_RELATIVE).resolve()
    if resolved != expected:
        raise ValueError("out-root must be the frozen path %s" % expected)
    return layout.refuse_out_root(resolved)


def check_before_call(started: float, *, now: Callable[[], float],
                      rss_fn: Callable[[], int | None],
                      calls: int = 0) -> str:
    """Return the frozen pre-call stop reason, if a budget is already spent."""
    if int(calls) >= MAX_CALLS:
        return "decoder_call_count_cap_before_next_call"
    elapsed = max(float(now()) - float(started), 0.0)
    if elapsed >= WALL_CAP_S:
        return "total_wall_cap_before_next_call"
    rss = rss_fn()
    if rss is not None and int(rss) >= RSS_CAP_BYTES:
        return "rss_cap_before_next_call"
    return ""


def decode_observation(decode_fn, dense: Any, prior: Any, truth: Any,
                       syndrome: Any, *, now: Callable[[], float],
                       rss_fn: Callable[[], int | None]) -> tuple[dict[str, Any], str]:
    """Call an injected decoder once and classify its returned hard decision.

    Syndrome acceptance is recomputed from the returned word. A mismatch with
    the decoder's own flag is an integrity stop; a syndrome-consistent wrong
    word is retained as an ordinary exact=False failure.
    """
    h = np.asarray(dense, dtype=np.int64)
    target = np.asarray(truth, dtype=np.int64).ravel()
    prior_array = np.asarray(prior, dtype=np.float64)
    syn = np.asarray(syndrome, dtype=np.int64).ravel()
    before = float(now())
    try:
        decoded = decode_fn(h, prior_array, syn)
    except Exception as exc:  # retain an attempted call and stop on bad output
        elapsed = max(float(now()) - before, 0.0)
        return ({
            "exact": False, "syndrome_accept": False,
            "syndrome_consistent_wrong": False,
            "status": "decoder_exception:%s" % type(exc).__name__,
            "iterations": 0, "wall_s": elapsed, "rss_b": rss_fn(),
        }, "decoder_exception")
    elapsed = max(float(now()) - before, 0.0)
    rss = rss_fn()
    try:
        estimate = np.asarray(decoded.x_hat, dtype=np.int64).ravel()
        reported_syndrome = bool(decoded.syndrome_ok)
        iterations = int(decoded.iterations)
        status = str(decoded.status)
        valid = (estimate.shape == target.shape
                 and np.all((estimate >= 0) & (estimate < mechanism.Q)))
    except (AttributeError, TypeError, ValueError, OverflowError):
        valid = False
        estimate = np.zeros_like(target)
        reported_syndrome = False
        iterations = 0
        status = "integrity_error"
    if not valid:
        return ({
            "exact": False, "syndrome_accept": False,
            "syndrome_consistent_wrong": False,
            "status": "integrity_error", "iterations": iterations,
            "wall_s": elapsed, "rss_b": rss,
        }, "decoder_output_integrity")
    recomputed = bool(layout.syndrome_ok(h, estimate, syn))
    if recomputed != reported_syndrome:
        return ({
            "exact": bool(np.array_equal(estimate, target)),
            "syndrome_accept": recomputed,
            "syndrome_consistent_wrong": bool(
                recomputed and not np.array_equal(estimate, target)),
            "status": "integrity_error", "iterations": iterations,
            "wall_s": elapsed, "rss_b": rss,
        }, "decoder_syndrome_flag_mismatch")
    exact = bool(np.array_equal(estimate, target))
    syndrome_wrong = bool(recomputed and not exact)
    record = {
        "exact": exact,
        "syndrome_accept": recomputed,
        "syndrome_consistent_wrong": syndrome_wrong,
        "status": status,
        "iterations": iterations,
        "wall_s": elapsed,
        "rss_b": rss,
    }
    if elapsed > CALL_CAP_S:
        record["status"] = "resource_abort"
        return record, "decoder_call_wall_cap_after_return"
    if rss is not None and int(rss) >= RSS_CAP_BYTES:
        record["status"] = "resource_abort"
        return record, "rss_cap_after_call"
    return record, ""


def _record_row(*, phase: str, pmf: Mapping[str, Any], graph_seed: int,
                stream: int | str, frame: int, seed: int, arm: str,
                observed: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "phase": phase,
        "pmf_index": int(pmf["index"]),
        "p0": float(pmf["p0"]),
        "graph_seed": int(graph_seed),
        "stream": stream,
        "frame": int(frame),
        "seed": int(seed),
        "arm": arm,
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


def _write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(value, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _start_outputs(root: Path, manifest: dict[str, Any]) -> None:
    root.mkdir(parents=False, exist_ok=False)
    _write_json(root / "manifest.json", manifest)
    with (root / "frame_records.csv").open(
            "w", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=FRAME_FIELDS).writeheader()
    with (root / "EXPLORATION_LOG.md").open("w", encoding="utf-8") as fh:
        fh.write("# GF32 label alignment EXPLORE log\n\n")
        fh.write("Batch UUID: `%s`. Independent batch-end review: pending.\n"
                 % BATCH_UUID)


def _append_row(root: Path, row: Mapping[str, Any]) -> None:
    with (root / "frame_records.csv").open(
            "a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=FRAME_FIELDS).writerow(
            {field: row.get(field) for field in FRAME_FIELDS})
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as fh:
        fh.write(
            "- call %d: %s/%s graph=%s stream=%s frame=%s seed=%s "
            "exact=%s syndrome_accept=%s syndrome_consistent_wrong=%s "
            "status=%s wall_s=%.6f rss_b=%s\n"
            % (int(row.get("call_index", 0)), row["phase"], row["arm"],
               row["graph_seed"], row["stream"], row["frame"], row["seed"],
               row["exact"], row["syndrome_accept"],
               row["syndrome_consistent_wrong"], row["status"],
               row["wall_s"], row["rss_b"]))


def _append_log(root: Path, message: str) -> None:
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as fh:
        fh.write("- %s\n" % message)


def _candidate_metadata(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "labels": [int(x) for x in result["labels"]],
        "J0_bits": float(result["J0"]),
        "Jc_bits": float(result["Jc"]),
        "baseline_rank": int(result["baseline_rank"]),
        "candidate_rank": int(result["candidate_rank"]),
        "support_equal": bool(result["support_equal"]),
        "gauge_equal": bool(result["gauge_equal"]),
        "nontrivial": bool(result["nontrivial"]),
        "candidate_admitted": bool(result["candidate_admitted"]),
    }


def _summarize_holdout(rows: list[dict[str, Any]],
                       completed_pairs: list[dict[str, Any]],
                       stop_reason: str) -> dict[str, Any]:
    control = [r for r in rows if r["phase"] == "holdout" and r["arm"] == "control"]
    candidate = [r for r in rows
                 if r["phase"] == "holdout" and r["arm"] == "candidate"]
    c_exact = sum(bool(r["exact"]) and bool(r["syndrome_accept"])
                  for r in control)
    k_exact = sum(bool(r["exact"]) and bool(r["syndrome_accept"])
                  for r in candidate)
    by_graph: dict[str, dict[str, int]] = {}
    for seed in mechanism.GRAPH_SEEDS:
        c_n = sum(bool(r["exact"]) and bool(r["syndrome_accept"])
                  for r in control if int(r["graph_seed"]) == seed)
        k_n = sum(bool(r["exact"]) and bool(r["syndrome_accept"])
                  for r in candidate if int(r["graph_seed"]) == seed)
        by_graph[str(seed)] = {
            "control_exact": int(c_n), "candidate_exact": int(k_n),
            "delta_g": int(k_n - c_n),
        }
    complete = len(completed_pairs) == HOLDOUT_PAIRS
    count_wrong = sum(bool(r["syndrome_consistent_wrong"]) for r in rows)
    wrong_by_arm = {
        arm: sum(bool(r["syndrome_consistent_wrong"]) for r in rows
                 if r["arm"] == arm)
        for arm in ("control", "candidate")
    }
    pilot_exact_by_pmf = {
        str(index): sum(bool(r["exact"]) and bool(r["syndrome_accept"])
                        for r in rows if r["phase"] == "pilot"
                        and int(r["pmf_index"]) == index)
        for index in range(len(mechanism.PMF_P0S))
    }
    count_integrity = sum(
        str(r["status"]) == "integrity_error"
        or str(r["status"]).startswith("decoder_exception") for r in rows)
    count_resource = sum(str(r["status"]) == "resource_abort" for r in rows)
    if not complete:
        classification = "INCOMPLETE"
    elif not 39 <= c_exact <= 153:
        classification = "CONTROL_RANGE_UNINFORMATIVE"
    elif (k_exact - c_exact >= 12
          and sum(v["delta_g"] > 0 for v in by_graph.values()) >= 4
          and count_integrity == 0 and count_resource == 0):
        classification = "MECHANISM_SIGNAL"
    else:
        classification = "NO_SUFFICIENT_SIGNAL"
    pair_states = {"control_only": 0, "candidate_only": 0,
                   "both": 0, "neither": 0}
    for pair in completed_pairs:
        c = bool(pair["control_exact"])
        k = bool(pair["candidate_exact"])
        pair_states[{(True, False): "control_only", (False, True): "candidate_only",
                     (True, True): "both", (False, False): "neither"}[(c, k)]] += 1
    return {
        "classification": classification,
        "stop_reason": stop_reason,
        "holdout_complete": complete,
        "holdout_pairs_completed": len(completed_pairs),
        "pilot_control_exact_by_pmf": pilot_exact_by_pmf,
        "control_exact": int(c_exact),
        "candidate_exact": int(k_exact),
        "delta": int(k_exact - c_exact),
        "delta_by_graph": by_graph,
        "paired_states": pair_states,
        "syndrome_consistent_wrong_rows": int(count_wrong),
        "syndrome_consistent_wrong_by_arm": wrong_by_arm,
        "integrity_violations": int(count_integrity),
        "resource_violations": int(count_resource),
        "authorization_violations": 0,
        "FER": None,
        "f_eff": None,
        "tag_bits": 0,
        "verification_status": "NOT_IMPLEMENTED",
        "undetected_status": "NOT_MEASURED",
        "claim_ceiling": (
            "synthetic L1 mechanism screening only; no FER, full-pair, "
            "real-data, f_eff, SKR, qualification, or route-closure claim"),
    }


def _seed_plan() -> tuple[list[tuple[int, int, int, int]],
                          list[tuple[int, int, int]]]:
    pilots = [(pmf_index, graph_seed, frame,
               pilot_seed(pmf_index, graph_seed, frame))
              for pmf_index in range(len(mechanism.PMF_P0S))
              for graph_seed in mechanism.GRAPH_SEEDS
              for frame in range(4)]
    holdouts = [(graph_seed, stream, frame,
                 holdout_seed(graph_seed, stream, frame))
                for graph_seed in mechanism.GRAPH_SEEDS
                for stream in (0, 1) for frame in range(16)]
    return pilots, holdouts


def _initial_manifest(command: str) -> dict[str, Any]:
    return {
        "track": "EXPLORE",
        "batch_uuid": BATCH_UUID,
        "contract": "NBLDPC-GF32-LABEL-MECHANISM-20260930/PREREG_AND_AUTH.md",
        "width": N, "checks": M, "edge_count": EDGE_COUNT,
        "field": "GF(32)/polynomial-37",
        "graph_seeds": [int(s) for s in mechanism.GRAPH_SEEDS],
        "pmf_grid": [
            {k: v for k, v in entry.items() if k != "pmf"}
            for entry in mechanism.pmf_grid()],
        "decoder_profile": (
            "v35 row-layered FFT-QSPA; max_iter=90; damping_alpha=1.0; "
            "warm_beliefs=None; field=None via accepted production adapter"),
        "pairing": "same sampled error and repeated PMF prior; own syndrome per arm",
        "arm_order": "control first on even frame index, candidate first on odd",
        "frame_streams": {
            "pilot": "v10_seed('gf32-label-v1:pilot:{pmf_index}:{graph_seed}:{frame}')",
            "holdout": "v10_seed('gf32-label-v1:holdout:{graph_seed}:{stream}:{frame}')",
        },
        "error_sampling": (
            "numpy.default_rng(seed).choice(32, size=128, p=pmf)"),
        "budgets": {"total_wall_s": WALL_CAP_S,
                    "per_decoder_call_s": CALL_CAP_S,
                    "rss_bytes": RSS_CAP_BYTES,
                    "max_decoder_calls": MAX_CALLS,
                    "max_pilot_calls": MAX_PILOT_CALLS},
        "accounting": {
            "syndrome_bits": SYNDROME_BITS,
            "tag_bits": 0,
            "verification_status": "NOT_IMPLEMENTED",
            "undetected_status": "NOT_MEASURED",
            "success": "exact AND syndrome_accept",
            "syndrome_consistent_wrong": "recorded exact=False failure; not a stop trigger",
            "truth_and_prior_arrays_saved": False,
        },
        "exact_command": command or COMMAND,
        "status": "RUNNING",
        "attempted_decoder_calls": 0,
        "attempted_call_counts": {"pilot": 0, "holdout": 0, "total": 0},
        "stop_reason": "",
        "graph_diagnostics": [],
        "candidate_diagnostics": [],
        "git_head_provenance_only": None,
    }


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    """Validate fixed paths/seeds/math and return a zero-write plan."""
    root = validate_out_root(out_root, repo_root=repo_root)
    t0 = mechanism.verify_t0()
    pilots, holdouts = _seed_plan()
    pilot_seeds = {row[3] for row in pilots}
    holdout_seeds = {row[3] for row in holdouts}
    if pilot_seeds & holdout_seeds:
        raise AssertionError("pilot and holdout seed namespaces overlap")
    return {
        "status": "DRY_RUN", "out_root": str(root),
        "writes": 0, "decoder_calls": 0,
        "t0": t0,
        "pilot_call_ceiling": MAX_PILOT_CALLS,
        "holdout_pair_count": HOLDOUT_PAIRS,
        "holdout_call_count": 2 * HOLDOUT_PAIRS,
        "maximum_call_count": MAX_CALLS,
        "pilot_holdout_seed_disjoint": True,
        "candidate_decoder_binding": "not loaded during dry-run",
    }


def execute_batch(*, out_root: str | Path, decode_fn,
                  command: str = COMMAND,
                  repo_root: str | Path | None = None,
                  now: Callable[[], float] = time.perf_counter,
                  rss_fn: Callable[[], int | None] | None = None,
                  graph_builder: Callable[[int, int], Mapping[str, Any]] | None = None
                  ) -> dict[str, Any]:
    """Execute the frozen synthetic pilot/holdout sequence with injection.

    The CLI uses the accepted production decoder adapter. Tests must pass an
    explicit fake decoder; no fake or production binding is the default here.
    """
    if decode_fn is None or not callable(decode_fn):
        raise ValueError("an explicit decoder callable is required")
    root = validate_out_root(out_root, repo_root=repo_root)
    if rss_fn is None:
        rss_fn = d5._rss_bytes
    if graph_builder is None:
        graph_builder = layout.build_control_l1
    started = float(now())
    manifest = _initial_manifest(command)
    _start_outputs(root, manifest)
    rows: list[dict[str, Any]] = []
    completed_pairs: list[dict[str, Any]] = []
    graphs: dict[int, np.ndarray] = {}
    candidate_graphs: dict[int, np.ndarray] = {}
    stop_reason = ""
    calls = 0
    selected_pmf: dict[str, Any] | None = None
    selected_pmf_index: int | None = None
    terminal = "INCOMPLETE"

    def finish() -> dict[str, Any]:
        summary = _summarize_holdout(rows, completed_pairs, stop_reason)
        summary["terminal_status"] = terminal
        summary["selected_pmf_index"] = selected_pmf_index
        summary["attempted_decoder_calls"] = calls
        summary["attempted_frame_rows"] = len(rows)
        phase_calls = {
            "pilot": sum(r["phase"] == "pilot" for r in rows),
            "holdout": sum(r["phase"] == "holdout" for r in rows),
            "total": calls,
        }
        summary["attempted_call_counts"] = phase_calls
        summary["batch_wall_s"] = max(float(now()) - started, 0.0)
        _write_json(root / "summary.json", summary)
        manifest.update({
            "status": terminal,
            "selected_pmf_index": selected_pmf_index,
            "attempted_decoder_calls": calls,
            "attempted_call_counts": phase_calls,
            "attempted_frame_rows": len(rows),
            "stop_reason": stop_reason,
            "batch_wall_s": summary["batch_wall_s"],
            "graph_diagnostics": graph_diagnostics,
            "candidate_diagnostics": candidate_diagnostics,
        })
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "terminal=%s; stop_reason=%s; calls=%d; rows=%d"
                    % (terminal, stop_reason or "none", calls, len(rows)))
        return summary

    def store_row(row: dict[str, Any]) -> None:
        row["call_index"] = calls
        rows.append(row)
        _append_row(root, row)

    def do_decode(*, phase: str, pmf: Mapping[str, Any],
                  graph_seed: int, stream: int | str, frame: int,
                  seed: int, arm: str, dense: np.ndarray, prior: np.ndarray,
                  truth: np.ndarray, syndrome: np.ndarray
                  ) -> tuple[dict[str, Any] | None, str]:
        nonlocal calls
        pre = check_before_call(started, now=now, rss_fn=rss_fn,
                                calls=calls)
        if pre:
            return None, pre
        calls += 1
        observed, issue = decode_observation(
            decode_fn, dense, prior, truth, syndrome, now=now, rss_fn=rss_fn)
        if not issue:
            elapsed = max(float(now()) - started, 0.0)
            rss = observed["rss_b"]
            if elapsed > WALL_CAP_S:
                issue = "total_wall_cap_after_call"
                observed["status"] = "resource_abort"
            elif rss is not None and int(rss) >= RSS_CAP_BYTES:
                issue = "rss_cap_after_call"
                observed["status"] = "resource_abort"
        row = _record_row(
            phase=phase, pmf=pmf, graph_seed=graph_seed, stream=stream,
            frame=frame, seed=seed, arm=arm, observed=observed)
        store_row(row)
        return row, issue

    graph_diagnostics: list[dict[str, Any]] = []
    candidate_diagnostics: list[dict[str, Any]] = []
    try:
        _append_log(root, "T0 started; no decoder call has occurred")
        try:
            t0 = mechanism.verify_t0()
        except Exception as exc:
            stop_reason = "MATH_OR_MAPPING_FAILURE:%s:%s" % (
                type(exc).__name__, str(exc))
            terminal = "MATH_OR_MAPPING_FAILURE"
            _append_log(root, stop_reason)
            return finish()
        manifest["t0"] = t0
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "T0 PASS: %s" % ", ".join(k for k, v in t0.items() if v))

        preflight_failed = False
        for seed in mechanism.GRAPH_SEEDS:
            graph = graph_builder(N, int(seed))
            dense = graph.get("dense")
            rank = int(graph.get("structure", {}).get("gf32_rank", -1))
            shape_ok = dense is not None and np.asarray(dense).shape == (M, N)
            edge_count = int(graph.get("E", -1))
            admitted = bool(graph.get("admitted", False))
            row = {
                "graph_seed": int(seed), "status": str(graph.get("status")),
                "admitted": admitted, "shape": list(np.asarray(dense).shape)
                if dense is not None else None,
                "edge_count": edge_count, "gf32_rank": rank,
                "full_row_rank": rank == M,
            }
            graph_diagnostics.append(row)
            if shape_ok and admitted and edge_count == EDGE_COUNT and rank == M:
                graphs[int(seed)] = np.asarray(dense, dtype=np.int64)
            else:
                preflight_failed = True
            _append_log(root, "baseline preflight graph=%d status=%s admitted=%s "
                        "rank=%d edges=%d" % (seed, row["status"], admitted,
                                               rank, edge_count))
        if preflight_failed or len(graphs) != len(mechanism.GRAPH_SEEDS):
            stop_reason = "BASELINE_GRAPH_PREFLIGHT_FAILED"
            terminal = stop_reason
            return finish()

        pilot_plan, holdout_plan = _seed_plan()
        all_pilot_seeds = {entry[3] for entry in pilot_plan}
        all_holdout_seeds = {entry[3] for entry in holdout_plan}
        if (len(all_pilot_seeds) != len(pilot_plan)
                or len(all_holdout_seeds) != len(holdout_plan)
                or all_pilot_seeds & all_holdout_seeds):
            stop_reason = "PILOT_HOLDOUT_SEED_COLLISION"
            terminal = stop_reason
            return finish()

        for pmf_entry in mechanism.pmf_grid():
            pmf_index = int(pmf_entry["index"])
            p = pmf_entry["pmf"]
            prior = np.tile(p, (N, 1))
            successes = 0
            _append_log(root, "pilot PMF %d started; control only" % pmf_index)
            for graph_seed in mechanism.GRAPH_SEEDS:
                for frame in range(4):
                    seed = pilot_seed(pmf_index, graph_seed, frame)
                    truth = sample_error(seed, p)
                    h = graphs[int(graph_seed)]
                    syndrome = np.asarray(layout.gf32_syndrome(h, truth),
                                          dtype=np.int64)
                    observed, issue = do_decode(
                        phase="pilot", pmf=pmf_entry,
                        graph_seed=graph_seed, stream="pilot", frame=frame,
                        seed=seed, arm="control", dense=h, prior=prior,
                        truth=truth, syndrome=syndrome)
                    if observed is not None and observed["exact"] \
                            and observed["syndrome_accept"]:
                        successes += 1
                    if issue:
                        stop_reason = issue
                        terminal = "RESOURCE_STOP" if "cap" in issue else "INTEGRITY_STOP"
                        return finish()
            _append_log(root, "pilot PMF %d control exact=%d/24"
                        % (pmf_index, successes))
            if 5 <= successes <= 19:
                selected_pmf = pmf_entry
                selected_pmf_index = pmf_index
                break
        if selected_pmf is None:
            stop_reason = "CONTROL_RANGE_UNINFORMATIVE"
            terminal = stop_reason
            return finish()

        # Candidate construction is frozen to the selected pilot PMF and is
        # completed for all six graphs before any holdout error is generated.
        selected_p = selected_pmf["pmf"]
        candidate_failed = False
        for graph_seed in mechanism.GRAPH_SEEDS:
            result = mechanism.align_labels(graphs[int(graph_seed)], selected_p)
            metadata = {"graph_seed": int(graph_seed), **_candidate_metadata(result)}
            candidate_diagnostics.append(metadata)
            if result["candidate_admitted"]:
                candidate_graphs[int(graph_seed)] = np.asarray(
                    result["candidate"], dtype=np.int64)
            else:
                candidate_failed = True
            _append_log(root, "candidate preflight graph=%d J0=%.12f Jc=%.12f "
                        "nontrivial=%s admitted=%s" % (
                            graph_seed, result["J0"], result["Jc"],
                            result["nontrivial"], result["candidate_admitted"]))
        if candidate_failed or len(candidate_graphs) != len(mechanism.GRAPH_SEEDS):
            stop_reason = "NO_NONTRIVIAL_LABEL_CANDIDATE"
            terminal = stop_reason
            return finish()

        p = selected_p
        prior = np.tile(p, (N, 1))
        for graph_seed, stream, frame, seed in holdout_plan:
            truth = sample_error(seed, p)
            paired = paired_arm_data(
                graphs[graph_seed], candidate_graphs[graph_seed], truth, prior)
            arm_rows: dict[str, dict[str, Any]] = {}
            for arm in arm_order(frame):
                arm_input = paired[arm]
                observed, issue = do_decode(
                    phase="holdout", pmf=selected_pmf,
                    graph_seed=graph_seed, stream=stream, frame=frame,
                    seed=seed, arm=arm, dense=arm_input["dense"],
                    prior=arm_input["prior"], truth=arm_input["truth"],
                    syndrome=arm_input["syndrome"])
                if observed is not None:
                    arm_rows[arm] = observed
                if issue:
                    stop_reason = issue
                    terminal = "RESOURCE_STOP" if "cap" in issue else "INTEGRITY_STOP"
                    return finish()
            if set(arm_rows) == {"control", "candidate"}:
                completed_pairs.append({
                    "graph_seed": graph_seed, "stream": stream,
                    "frame": frame,
                    "control_exact": bool(arm_rows["control"]["exact"]
                                           and arm_rows["control"]["syndrome_accept"]),
                    "candidate_exact": bool(arm_rows["candidate"]["exact"]
                                              and arm_rows["candidate"]["syndrome_accept"]),
                })
        summary = _summarize_holdout(rows, completed_pairs, stop_reason)
        terminal = summary["classification"]
        stop_reason = "" if terminal in (
            "MECHANISM_SIGNAL", "NO_SUFFICIENT_SIGNAL",
            "CONTROL_RANGE_UNINFORMATIVE") else stop_reason
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
        description="Frozen synthetic GF(32) label alignment EXPLORE probe")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true",
                      help="run the one frozen synthetic batch")
    mode.add_argument("--dry-run", action="store_true",
                      help="check field math, seeds and output path only")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE),
                        help="must equal the frozen fresh workspace root")
    return parser


def _bind_production_decoder():
    """Resolve the accepted Stage-2 v35 binding only for --execute."""
    from comparison_bench.formal_ir.nbldpc_l1d2_production_decode import (
        production_decode_fn,
    )
    return production_decode_fn


def main(argv: list[str] | None = None) -> dict[str, Any]:
    parser = build_parser()
    args = parser.parse_args(argv)
    resolved_root = validate_out_root(args.out_root)
    if not args.execute:
        result = dry_run(resolved_root)
    else:
        result = execute_batch(out_root=resolved_root,
                               decode_fn=_bind_production_decoder(),
                               command=COMMAND)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
