"""Post-BP GF(32) MRB free-coordinate reachability diagnostic."""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from comparison_bench.cli.probes_closed import nbldpc_gf32_mrb_rescue_probe as source_runner
from comparison_bench.cli.probes_closed import nbldpc_gf32_search_depth_probe as search_runner
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.formal_ir.nonbinary_v19_osd import gf_rref, solve_with_free
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

CONTRACT = "NBLDPC-GF32-MRB-REACHABILITY-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "c4fab9ba-ead1-4c64-8d0b-82177ace721c"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_mrb_reachability_c4fab9ba"
SEED_PREFIX = "gf32-mrb-reachability-v1"
N = search_runner.N
M = search_runner.M
EDGE_COUNT = search_runner.EDGE_COUNT
GRAPH_SEEDS = tuple(search_runner.GRAPH_SEEDS)
HOLDOUT_STREAMS = tuple(source_runner.HOLDOUT_STREAMS)
HOLDOUT_FRAMES_PER_STREAM = source_runner.HOLDOUT_FRAMES_PER_STREAM
HOLDOUT_CALLS = len(GRAPH_SEEDS) * len(HOLDOUT_STREAMS) * HOLDOUT_FRAMES_PER_STREAM
MAX_CALLS = 192
MAX_ITER = 90
DAMPING_ALPHA = 1.0
WARM_BELIEFS = None
FIELD = None
DISCLOSURE_BITS_PER_CALL = 260
WALL_CAP_S = 900.0
CALL_CAP_S = 120.0
RSS_CAP_BYTES = 4 * 1024 ** 3
ARTIFACT_LIMIT_BYTES = 20 * 1024 ** 2
ARTIFACTS = (
    "manifest.json", "frame_records.csv", "summary.json",
    "EXPLORATION_LOG.md", "diagnostics.npz",
)
FRAME_FIELDS = (
    "call_index", "seed", "graph_seed", "stream", "frame",
    "raw_status", "raw_iterations", "raw_syndrome_ok_reported",
    "raw_symbols_equal", "raw_exact", "raw_syndrome_ok", "raw_stratum",
    "rank", "free_count",
    "D_free", "truth_syndrome_ok", "truth_reconstruction_ok",
    "base_syndrome_ok", "base_equals_truth", "bp_wall_s",
    "diagnostic_wall_s", "arm_wall_s", "rss_before_bytes",
    "rss_after_bp_bytes", "rss_after_diagnostic_bytes",
    "diagnostic_array_index", "status", "failure_reason",
)
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.probes_closed.nbldpc_gf32_mrb_reachability_probe "
    "--execute --out-root workspace/gf32_mrb_reachability_c4fab9ba"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _seed_plan() -> list[tuple[int, int, int, int]]:
    return source_runner._validate_seed_plan(SEED_PREFIX)


def _shape_record() -> dict[str, Any]:
    return search_runner.shape_pmf_grid()[0]


def verify_t0() -> dict[str, bool]:
    """Check only fixed math, PMF, dimensions and the seed namespace."""
    field = GF2mField.create(32)
    shape = _shape_record()
    pmf = np.asarray(shape["pmf"], dtype=np.float64)
    seeds = _seed_plan()
    checks = {name: bool(value) for name, value in {
        "gf32_poly37": field.q == 32 and field.primitive_polynomial == 37,
        "fixed_graph_profile": (N, M, EDGE_COUNT) == (128, 52, 256),
        "fixed_graph_seeds": GRAPH_SEEDS == tuple(range(2026093901, 2026093907)),
        "fixed_iid_pmf": (
            float(pmf[0]) == 0.55
            and np.flatnonzero(pmf).tolist() == [0, 1, 3, 7, 15, 31]
            and np.isclose(float(pmf.sum()), 1.0, rtol=0.0, atol=1e-12)
        ),
        "fixed_decoder_settings": (MAX_ITER, DAMPING_ALPHA, WARM_BELIEFS, FIELD)
        == (90, 1.0, None, None),
        "fixed_holdout_plan": (
            len(seeds) == MAX_CALLS == HOLDOUT_CALLS
            and len({row[3] for row in seeds}) == MAX_CALLS
            and [row[:3] for row in seeds] == [
                (graph, stream, frame)
                for graph in GRAPH_SEEDS
                for stream in HOLDOUT_STREAMS
                for frame in range(HOLDOUT_FRAMES_PER_STREAM)
            ]
        ),
    }.items()}
    if not all(checks.values()):
        raise AssertionError("reachability T0 failed: %s" % checks)
    return checks


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


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    """No-write preflight; never constructs a graph or binds the decoder."""
    root = validate_out_root(out_root, repo_root)
    checks = verify_t0()
    return {
        "status": "DRY_RUN", "track": "EXPLORE", "contract": CONTRACT,
        "batch_uuid": BATCH_UUID, "out_root": str(root),
        "writes": 0, "artifact_reads": 0, "graph_construction_calls": 0,
        "decoder_calls": 0, "osd_calls": 0, "holdout_call_count": MAX_CALLS,
        "t0": checks,
    }


def _resource_check(started: float, *, now: Callable[[], float],
                    rss_fn: Callable[[], int | None],
                    rss_samples: list[int],
                    arm_wall_s: float | None = None
                    ) -> tuple[str, int | None]:
    try:
        rss_value = rss_fn()
    except Exception as exc:
        return ("resource_check_exception:%s:%s" %
                (type(exc).__name__, str(exc)), None)
    if rss_value is not None:
        rss_samples.append(int(rss_value))
    reasons = []
    if arm_wall_s is not None and float(arm_wall_s) >= CALL_CAP_S:
        reasons.append("decoder_diagnostic_call_wall_cap")
    if max(float(now()) - float(started), 0.0) >= WALL_CAP_S:
        reasons.append("total_wall_cap")
    if rss_value is not None and int(rss_value) >= RSS_CAP_BYTES:
        reasons.append("rss_cap")
    return ",".join(reasons), None if rss_value is None else int(rss_value)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def _append_log(root: Path, message: str) -> None:
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as stream:
        stream.write("- %s\n" % message)


def _start_outputs(root: Path, manifest: dict[str, Any]) -> None:
    root.mkdir(parents=False, exist_ok=False)
    _write_json(root / "manifest.json", manifest)
    with (root / "frame_records.csv").open(
            "w", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=FRAME_FIELDS).writeheader()
    _write_json(root / "summary.json", {"status": "RUNNING"})
    with (root / "EXPLORATION_LOG.md").open("w", encoding="utf-8") as stream:
        stream.write("# GF32 MRB reachability EXPLORE log\n\n")
        stream.write("Batch UUID: `%s`; contract: `%s`.\n\n" %
                     (BATCH_UUID, CONTRACT))
        stream.write("Independent batch-end review: pending.\n")


def _initial_manifest(command: str) -> dict[str, Any]:
    shape = _shape_record()
    return {
        "track": "EXPLORE", "contract": CONTRACT, "batch_uuid": BATCH_UUID,
        "status": "RUNNING", "command": command, "artifacts": list(ARTIFACTS),
        "seed_namespace": SEED_PREFIX,
        "profile": {"n": N, "m": M, "E": EDGE_COUNT,
                    "field": "GF(32)", "primitive_polynomial": 37},
        "graph_seeds": list(GRAPH_SEEDS),
        "source": {
            "role": "synthetic iid marginal-shape proxy",
            "p0": float(shape["p0"]), "pmf": [float(x) for x in shape["pmf"]],
            "support": list(shape["support"]), "counts": {
                "1": 2295, "3": 1126, "7": 557, "15": 304, "31": 146,
            },
            "no_empirical_input_reads": True,
        },
        "decoder": {
            "implementation": "v35.decode_row_layered_fftqspa",
            "schedule": "row_layered", "max_iter": MAX_ITER,
            "damping_alpha": DAMPING_ALPHA, "warm_beliefs": None,
            "field_argument": None, "raw_bp_calls": MAX_CALLS,
            "osd_or_mrb_candidate_calls": 0,
        },
        "diagnostic": {
            "reliability": "max-minus-second on original final_beliefs",
            "permutation": "stable ascending; tied columns keep original order",
            "free_coordinates": "permuted nonpivot columns",
            "truth_read_boundary": "after raw BP return only",
        },
        "resource_caps": {
            "process_wall_s": WALL_CAP_S, "bp_plus_diagnostic_arm_s": CALL_CAP_S,
            "sampled_rss_bytes": RSS_CAP_BYTES,
        },
        "claim_ceiling": (
            "finite synthetic GF32 MRB-basis algebraic reachability diagnostic; "
            "not FER, f_eff, SKR, throughput, route, qualification or promotion"),
        "independent_review": "pending",
    }


def _summary_groups(rows: list[dict[str, Any]], graph_seeds: Sequence[int]
                    ) -> dict[str, Any]:
    strata = ("raw_exact", "raw_syndrome_valid_wrong", "raw_syndrome_fail")
    groups: dict[str, list[dict[str, Any]]] = {"total": rows}
    groups.update({"graph_seed=%d" % int(seed): [
        row for row in rows if int(row["graph_seed"]) == int(seed)
    ] for seed in graph_seeds})
    result: dict[str, Any] = {}
    for group_name, group_rows in groups.items():
        result[group_name] = {}
        for stratum in strata:
            selected = [row for row in group_rows if row["raw_stratum"] == stratum]
            distances = [int(row["D_free"]) for row in selected]
            histogram = {str(distance): 0 for distance in range(N - M + 1)}
            for distance in distances:
                histogram[str(distance)] += 1
            result[group_name][stratum] = {
                "denominator": len(selected),
                "D0": sum(distance == 0 for distance in distances),
                "D1": sum(distance == 1 for distance in distances),
                "D_ge_2": sum(distance >= 2 for distance in distances),
                "distance_histogram": histogram,
            }
        result[group_name]["primary_denominator_raw_syndrome_fail"] = len([
            row for row in group_rows if row["raw_stratum"] == "raw_syndrome_fail"
        ])
    return result


def _diagnostic_arrays(graph_matrices: Mapping[int, np.ndarray],
                       rows: list[dict[str, Any]],
                       arrays_by_index: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    graph_seeds = [seed for seed in GRAPH_SEEDS if seed in graph_matrices]
    matrices = [np.asarray(graph_matrices[seed], dtype=np.uint8)
                for seed in graph_seeds]
    result: dict[str, np.ndarray] = {
        "graph_seed": np.asarray(graph_seeds, dtype=np.int64),
        "H": (np.stack(matrices).astype(np.uint8, copy=False) if matrices else
              np.empty((0, M, N), dtype=np.uint8)),
    }
    accepted = [row for row in rows if row.get("diagnostic_array_index") is not None]
    graph_index = {seed: index for index, seed in enumerate(graph_seeds)}
    result.update({
        "truth": (np.stack([item["truth"] for item in arrays_by_index]).astype(
            np.uint8, copy=False) if arrays_by_index else np.empty((0, N), dtype=np.uint8)),
        "raw_hard": (np.stack([item["raw_hard"] for item in arrays_by_index]).astype(
            np.uint8, copy=False) if arrays_by_index else np.empty((0, N), dtype=np.uint8)),
        "syndrome": (np.stack([item["syndrome"] for item in arrays_by_index]).astype(
            np.uint8, copy=False) if arrays_by_index else np.empty((0, M), dtype=np.uint8)),
        "final_beliefs": (np.stack([item["final_beliefs"] for item in arrays_by_index]).astype(
            np.float64, copy=False) if arrays_by_index else
            np.empty((0, N, 32), dtype=np.float64)),
        "frame_call_index": np.asarray([int(row["call_index"]) for row in accepted],
                                        dtype=np.int64),
        "frame_graph_index": np.asarray([
            graph_index[int(row["graph_seed"])] for row in accepted], dtype=np.int64),
        "frame_graph_seed": np.asarray([int(row["graph_seed"]) for row in accepted],
                                        dtype=np.int64),
        "frame_stream": np.asarray([int(row["stream"]) for row in accepted],
                                    dtype=np.int64),
        "frame_index": np.asarray([int(row["frame"]) for row in accepted],
                                   dtype=np.int64),
        "frame_seed": np.asarray([int(row["seed"]) for row in accepted],
                                  dtype=np.int64),
    })
    return result


def _write_diagnostics_npz(root: Path, arrays: Mapping[str, np.ndarray]) -> int:
    path = root / "diagnostics.npz"
    np.savez(path, **arrays)
    size = path.stat().st_size
    if size > ARTIFACT_LIMIT_BYTES:
        raise ValueError("diagnostics.npz exceeds the frozen 20 MiB limit")
    return size

def _mrb_reachability_diagnostic(
        *, field: GF2mField, matrix: Any, syndrome: Sequence[int],
        final_beliefs: Any, raw_hard: Sequence[int], truth: Sequence[int]
        ) -> dict[str, Any]:
    """Measure truth distance on the actual MRB free coordinates after BP.

    The caller must invoke this only after the raw decoder has returned.  The
    truth vector is used here only for the algebraic diagnostic and its
    reconstruction checks; it does not influence the reliability permutation
    or the raw-free base.
    """
    H = np.asarray(matrix, dtype=np.int64)
    s = np.asarray(syndrome, dtype=np.int64)
    beliefs = np.asarray(final_beliefs, dtype=np.float64)
    hard = np.asarray(raw_hard, dtype=np.int64)
    target = np.asarray(truth, dtype=np.int64)
    if H.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    m, n = H.shape
    if s.shape != (m,) or hard.shape != (n,) or target.shape != (n,):
        raise ValueError("syndrome and symbol vectors must match matrix shape")
    if beliefs.shape != (n, field.q) or not np.all(np.isfinite(beliefs)):
        raise ValueError("final_beliefs must be finite with shape (n, field.q)")
    if (np.any(H < 0) or np.any(H >= field.q)
            or np.any(s < 0) or np.any(s >= field.q)
            or np.any(hard < 0) or np.any(hard >= field.q)
            or np.any(target < 0) or np.any(target >= field.q)):
        raise ValueError("matrix and symbols must lie in the configured field")

    # Match _reliability/osd_decode_candidates_mrb: max-minus-second over the
    # original final beliefs, with Python's stable ascending sort.
    reliability = []
    for row in beliefs:
        ordered = np.sort(row)[::-1]
        reliability.append(float(ordered[0] - ordered[1]))
    permutation = sorted(range(n), key=lambda column: reliability[column])
    permuted_matrix = H[:, permutation]
    rref, pivots = gf_rref(field, permuted_matrix.tolist(), s.tolist())
    rank = len(pivots)
    if rank != m:
        raise ValueError("MRB matrix rank does not equal row count")
    pivot_set = set(int(column) for column in pivots)
    free_cols = [column for column in range(n) if column not in pivot_set]

    raw_free = {column: int(hard[permutation[column]]) for column in free_cols}
    raw_base_perm = solve_with_free(field, rref, pivots, raw_free, n)
    truth_free = {column: int(target[permutation[column]])
                  for column in free_cols}
    truth_reconstructed_perm = solve_with_free(
        field, rref, pivots, truth_free, n)
    if raw_base_perm is None or truth_reconstructed_perm is None:
        raise ValueError("free-coordinate assignment did not reconstruct")

    def to_original(permuted: Sequence[int]) -> list[int]:
        original = [0] * n
        for column, symbol in enumerate(permuted):
            original[permutation[column]] = int(symbol)
        return original

    raw_base = to_original(raw_base_perm)
    truth_reconstructed = to_original(truth_reconstructed_perm)

    def syndrome_of(vector: Sequence[int]) -> list[int]:
        output = []
        for row in H:
            total = 0
            for coefficient, symbol in zip(row, vector):
                if int(coefficient) != 0 and int(symbol) != 0:
                    total = field.add(
                        total, field.mul(int(coefficient), int(symbol)))
            output.append(total)
        return output

    truth_syndrome_ok = syndrome_of(target.tolist()) == s.tolist()
    truth_reconstruction_ok = truth_reconstructed == target.tolist()
    base_syndrome_ok = syndrome_of(raw_base) == s.tolist()
    if not truth_syndrome_ok:
        raise ValueError("truth does not satisfy the supplied syndrome")
    if not truth_reconstruction_ok:
        raise ValueError("truth free values did not reconstruct truth uniquely")
    if not base_syndrome_ok:
        raise ValueError("raw-free base does not satisfy the supplied syndrome")

    distance = sum(
        int(hard[permutation[column]]) != int(target[permutation[column]])
        for column in free_cols)
    base_equals_truth = raw_base == target.tolist()
    if (distance == 0) != base_equals_truth:
        raise ValueError("D_free/base equality premise failed")

    return {
        "permutation": permutation,
        "pivot_cols": [int(column) for column in pivots],
        "pivot_original_cols": [permutation[int(column)] for column in pivots],
        "free_cols": free_cols,
        "rank": rank,
        "free_count": len(free_cols),
        "D_free": int(distance),
        "raw_free_base": raw_base,
        "truth_reconstructed": truth_reconstructed,
        "truth_syndrome_ok": truth_syndrome_ok,
        "truth_reconstruction_ok": truth_reconstruction_ok,
        "base_syndrome_ok": base_syndrome_ok,
        "base_equals_truth": base_equals_truth,
    }


def _is_resource_reason(reason: str) -> bool:
    return any(marker in reason for marker in (
        "resource_check_exception", "decoder_diagnostic_call_wall_cap",
        "total_wall_cap", "rss_cap"))


def _row_template(call_index: int, graph_seed: int, stream: int,
                  frame: int, seed: int) -> dict[str, Any]:
    row = {name: None for name in FRAME_FIELDS}
    row.update({
        "call_index": int(call_index), "seed": int(seed),
        "graph_seed": int(graph_seed), "stream": int(stream),
        "frame": int(frame), "status": "NOT_STARTED",
    })
    return row


def _append_row(root: Path, row: Mapping[str, Any]) -> None:
    with (root / "frame_records.csv").open(
            "a", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=FRAME_FIELDS).writerow(
            {name: row.get(name) for name in FRAME_FIELDS})
    _append_log(
        root,
        "call=%s graph=%s stream=%s frame=%s raw_stratum=%s D_free=%s "
        "status=%s failure=%s"
        % (row["call_index"], row["graph_seed"], row["stream"],
           row["frame"], row.get("raw_stratum"), row.get("D_free"),
           row["status"], row.get("failure_reason")))


def _summary(*, status: str, stop_reason: str, calls: int,
             rows: list[dict[str, Any]], diagnostic_count: int,
             graph_seeds: Sequence[int], resource: Mapping[str, Any],
             npz_bytes: int | None) -> dict[str, Any]:
    complete = (status == "REACHABILITY_DIAGNOSTIC_COMPLETE"
                and calls == MAX_CALLS and len(rows) == MAX_CALLS
                and diagnostic_count == MAX_CALLS)
    aggregates = _summary_groups(rows, graph_seeds) if complete else None
    primary_denominator = (aggregates["total"][
        "raw_syndrome_fail"]["denominator"] if complete else None)
    return {
        "track": "EXPLORE", "contract": CONTRACT,
        "batch_uuid": BATCH_UUID, "seed_namespace": SEED_PREFIX,
        "status": status, "stop_reason": stop_reason or None,
        "attempted_decoder_calls": int(calls),
        "attempted_call_counts": {"holdout": int(calls), "total": int(calls)},
        "frame_rows": len(rows), "completed_diagnostic_rows": int(diagnostic_count),
        "failed_rows_without_diagnostics": sum(
            row.get("diagnostic_array_index") is None for row in rows),
        "disclosure_bits_per_attempted_bp_call": DISCLOSURE_BITS_PER_CALL,
        "disclosure_bits_actual": int(calls * DISCLOSURE_BITS_PER_CALL),
        "disclosure_bits_complete_contract": (
            int(MAX_CALLS * DISCLOSURE_BITS_PER_CALL) if complete else None),
        "tag_bits": 0, "verification": "NOT_IMPLEMENTED",
        "undetected": "NOT_MEASURED",
        "primary_denominator_raw_syndrome_fail": primary_denominator,
        "counts_and_distance_histograms_by_stratum_graph_and_total": aggregates,
        "distance_histogram_bins_when_complete": list(range(N - M + 1)),
        "resource_measurement": dict(resource),
        "diagnostics_npz_bytes": npz_bytes,
        "diagnostics_npz_limit_bytes": ARTIFACT_LIMIT_BYTES,
        "claim_ceiling": (
            "finite synthetic GF32 MRB-basis algebraic reachability diagnostic; "
            "not FER, f_eff, SKR, throughput, route, qualification or promotion"),
    }


def execute_batch(*, out_root: str | Path,
                  decode_fn: Callable[..., Any],
                  graph_builder: Callable[[int], Mapping[str, Any]],
                  candidate_builder: Callable[[np.ndarray, np.ndarray, int],
                                              tuple[np.ndarray | None, np.ndarray | None,
                                                    dict[str, Any]]],
                  preflight_fn: Callable[[Mapping[str, Any], int],
                                         tuple[bool, Mapping[str, Any]]] | None = None,
                  repo_root: str | Path | None = None,
                  now: Callable[[], float] = time.perf_counter,
                  rss_fn: Callable[[], int | None] | None = None,
                  command: str = COMMAND) -> dict[str, Any]:
    """Run one raw-BP arm; all executable dependencies are explicit callbacks."""
    if not callable(decode_fn) or not callable(graph_builder) \
            or not callable(candidate_builder):
        raise ValueError("explicit decoder, graph, and candidate callbacks are required")
    if preflight_fn is None:
        preflight_fn = search_runner.graph_preflight
    if rss_fn is None:
        rss_fn = d5._rss_bytes
    root = validate_out_root(out_root, repo_root)
    started = float(now())
    rss_samples: list[int] = []
    rows: list[dict[str, Any]] = []
    arrays_by_index: list[dict[str, Any]] = []
    graph_matrices: dict[int, np.ndarray] = {}
    graph_records: list[dict[str, Any]] = []
    calls = 0
    max_arm_wall = 0.0
    stop_reason = ""
    terminal = "INCOMPLETE"
    resource_stop_reasons: list[str] = []
    manifest = _initial_manifest(command)
    _start_outputs(root, manifest)

    def check_resource(arm_wall_s: float | None = None) -> tuple[str, int | None]:
        return _resource_check(started, now=now, rss_fn=rss_fn,
                               rss_samples=rss_samples,
                               arm_wall_s=arm_wall_s)

    def stop(reason: str, state: str | None = None) -> None:
        nonlocal stop_reason, terminal
        if not stop_reason:
            stop_reason = str(reason)
        terminal = state or ("RESOURCE_STOP" if _is_resource_reason(reason)
                             else "INCOMPLETE")

    def note_resource_stop(reason: str) -> bool:
        added = False
        for item in str(reason).split(","):
            item = item.strip()
            if item and item not in resource_stop_reasons:
                resource_stop_reasons.append(item)
                added = True
        if not stop_reason:
            stop(reason)
        return added

    def measured_resource(npz_bytes: int | None = None) -> dict[str, Any]:
        return {
            "batch_wall_s_before_terminal_summary_manifest_log": max(
                float(now()) - started, 0.0),
            "max_bp_plus_diagnostic_arm_wall_s": max_arm_wall or None,
            "max_sampled_rss_bytes": max(rss_samples) if rss_samples else None,
            "rss_sample_count": len(rss_samples),
            "rss_scope": (
                "values returned by d5._rss_bytes at explicit checkpoints; "
                "not a continuous or absolute process peak"),
            "wall_scope": (
                "includes graph construction, source generation, BP, diagnostics, "
                "CSV and diagnostics.npz; excludes the compact terminal summary, "
                "manifest and log write boundary"),
            "diagnostics_npz_bytes": npz_bytes,
            "resource_stop_reasons": list(resource_stop_reasons),
            "resource_violation_count": len(resource_stop_reasons),
            "terminal_write_boundary": "one final summary/manifest/log update; no recursive refresh",
        }

    def finish() -> dict[str, Any]:
        nonlocal stop_reason, terminal
        before_reason, _ = check_resource()
        if before_reason:
            note_resource_stop(before_reason)
        complete_candidate = (
            not stop_reason and calls == MAX_CALLS and len(rows) == MAX_CALLS
            and len(arrays_by_index) == MAX_CALLS)
        if complete_candidate:
            terminal = "REACHABILITY_DIAGNOSTIC_COMPLETE"
        arrays = _diagnostic_arrays(graph_matrices, rows, arrays_by_index)
        npz_bytes: int | None = None
        try:
            npz_bytes = _write_diagnostics_npz(root, arrays)
        except Exception as exc:
            stop("diagnostics_npz_write:%s:%s" % (type(exc).__name__, str(exc)),
                 "ARTIFACT_STOP")
        post_npz_reason, _ = check_resource()
        if post_npz_reason:
            note_resource_stop(post_npz_reason)
        resource = measured_resource(npz_bytes)
        summary = _summary(
            status=terminal, stop_reason=stop_reason, calls=calls,
            rows=rows, diagnostic_count=len(arrays_by_index),
            graph_seeds=GRAPH_SEEDS, resource=resource, npz_bytes=npz_bytes)
        manifest.update({
            "status": terminal, "stop_reason": stop_reason or None,
            "attempted_decoder_calls": calls,
            "completed_diagnostic_rows": len(arrays_by_index),
            "frame_rows": len(rows), "graph_records": graph_records,
            "resource_measurement": resource,
            "independent_review": "pending",
        })
        _write_json(root / "summary.json", summary)
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "terminal=%s stop_reason=%s resource_stops=%s "
                    "calls=%d rows=%d diagnostics=%d"
                    % (terminal, stop_reason or "none",
                       ",".join(resource_stop_reasons) or "none", calls,
                       len(rows), len(arrays_by_index)))
        after_reason, _ = check_resource()
        if after_reason and note_resource_stop(after_reason):
            resource = measured_resource(npz_bytes)
            summary = _summary(
                status=terminal, stop_reason=stop_reason, calls=calls,
                rows=rows, diagnostic_count=len(arrays_by_index),
                graph_seeds=GRAPH_SEEDS, resource=resource, npz_bytes=npz_bytes)
            manifest.update({"status": terminal, "stop_reason": stop_reason,
                             "resource_measurement": resource})
            _write_json(root / "summary.json", summary)
            _write_json(root / "manifest.json", manifest)
            _append_log(root, "post-terminal-write resource stop=%s" % stop_reason)
        return summary

    try:
        _append_log(root, "T0 started; graph/BP/OSD calls=0")
        checks = verify_t0()
        manifest["t0"] = checks
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "T0 PASS; fixed GF32, PMF, graph and seed plan")
        reason, _ = check_resource()
        if reason:
            stop(reason)
        else:
            shape = _shape_record()
            pmf = np.asarray(shape["pmf"], dtype=np.float64)
            for graph_seed in GRAPH_SEEDS:
                reason, _ = check_resource()
                if reason:
                    stop(reason)
                    break
                try:
                    graph = graph_builder(int(graph_seed))
                    reason, _ = check_resource()
                    if reason:
                        graph_records.append({
                            "graph_seed": int(graph_seed),
                            "status": "RESOURCE_STOP",
                            "failure_reason": reason,
                        })
                        stop(reason)
                        break
                    admitted, graph_diag = preflight_fn(graph, int(graph_seed))
                    dense = np.asarray(graph["dense"], dtype=np.int64)
                    if not admitted or dense.shape != (M, N):
                        raise ValueError("accepted profile graph preflight failed")
                    reason, _ = check_resource()
                    if reason:
                        graph_records.append({
                            "graph_seed": int(graph_seed),
                            "status": "RESOURCE_STOP",
                            "failure_reason": reason,
                        })
                        stop(reason)
                        break
                    onepass, deep, candidate_diag = candidate_builder(
                        dense, pmf, int(graph_seed))
                    deep_ok = bool(candidate_diag.get(
                        "deep_candidate_admitted", deep is not None))
                    onepass_ok = bool(candidate_diag.get(
                        "candidate_admitted", onepass is not None))
                    if (candidate_diag.get("construction_stop") or not deep_ok
                            or not onepass_ok or deep is None):
                        raise ValueError(str(candidate_diag.get(
                            "failure_reason", "deep H0D candidate not admitted")))
                    deep_array = np.asarray(deep, dtype=np.int64)
                    if deep_array.shape != (M, N):
                        raise ValueError("deep H0D matrix has wrong shape")
                    if np.any(deep_array < 0) or np.any(deep_array >= 32):
                        raise ValueError("deep H0D matrix contains a non-GF32 symbol")
                    graph_matrices[int(graph_seed)] = deep_array.copy()
                    graph_records.append({
                        "graph_seed": int(graph_seed), "status": "ADMITTED",
                        "profile_graph_preflight": bool(admitted),
                        "deep_candidate_admitted": deep_ok,
                    })
                    _append_log(root, "graph seed=%d preflight=PASS deep_H0D=PASS"
                                % graph_seed)
                except Exception as exc:
                    graph_records.append({
                        "graph_seed": int(graph_seed), "status": "STOP",
                        "failure_reason": "%s:%s" % (type(exc).__name__, str(exc)),
                    })
                    stop("graph_construction_or_admission:%s:%s" %
                         (type(exc).__name__, str(exc)), "GRAPH_PREFLIGHT_STOP")
                    break
                reason, _ = check_resource()
                if reason:
                    stop(reason)
                    break

        if not stop_reason and len(graph_matrices) == len(GRAPH_SEEDS):
            shape = _shape_record()
            pmf = np.asarray(shape["pmf"], dtype=np.float64)
            prior = np.tile(pmf, (N, 1))
            field = GF2mField.create(32)
            for call_index, (graph_seed, stream, frame, seed) in enumerate(
                    _seed_plan(), start=1):
                reason, rss_before = check_resource()
                if reason:
                    stop(reason)
                    break
                truth = source_runner.prior_runner.prior_runner.sample_error(
                    int(seed), pmf, width=N)
                dense = graph_matrices[int(graph_seed)]
                syndrome = np.asarray(layout.gf32_syndrome(dense, truth),
                                      dtype=np.int64)
                reason, rss_before = check_resource()
                if reason:
                    stop(reason)
                    break
                arm_started = float(now())
                calls += 1
                row = _row_template(call_index, graph_seed, stream, frame, seed)
                row["rss_before_bytes"] = rss_before
                try:
                    raw = decode_fn(dense, prior, syndrome)
                except Exception as exc:
                    arm_wall = max(float(now()) - arm_started, 0.0)
                    max_arm_wall = max(max_arm_wall, arm_wall)
                    resource_reason, rss_after = check_resource(arm_wall)
                    row.update({
                        "status": "BP_EXCEPTION_STOP",
                        "failure_reason": "%s:%s" % (type(exc).__name__, str(exc)),
                        "arm_wall_s": arm_wall,
                        "bp_wall_s": arm_wall,
                        "rss_after_bp_bytes": rss_after,
                    })
                    rows.append(row)
                    _append_row(root, row)
                    stop(resource_reason or row["failure_reason"],
                         "RESOURCE_STOP" if resource_reason else "BP_EXCEPTION_STOP")
                    break

                bp_returned = float(now())
                bp_wall = max(bp_returned - arm_started, 0.0)
                row["bp_wall_s"] = bp_wall
                try:
                    raw_status = str(raw.status)
                    raw_iterations = int(raw.iterations)
                    raw_reported_syn = bool(raw.syndrome_ok)
                    row.update({
                        "raw_status": raw_status,
                        "raw_iterations": raw_iterations,
                        "raw_syndrome_ok_reported": raw_reported_syn,
                    })
                    raw_hard = np.asarray(raw.x_hat, dtype=np.int64).ravel()
                    beliefs = np.asarray(raw.final_beliefs, dtype=np.float64)
                    if raw_hard.shape != (N,) or np.any(raw_hard < 0) \
                            or np.any(raw_hard >= 32):
                        raise ValueError("raw x_hat must be a GF32 vector of length 128")
                    if not 0 <= raw_iterations <= MAX_ITER:
                        raise ValueError("raw iteration count is outside [0, 90]")
                    raw_syn = bool(layout.syndrome_ok(dense, raw_hard, syndrome))
                    raw_symbols_equal = bool(np.array_equal(raw_hard, truth))
                    raw_exact = bool(raw_symbols_equal and raw_syn)
                    row.update({
                        "raw_symbols_equal": raw_symbols_equal,
                        "raw_exact": raw_exact,
                        "raw_syndrome_ok": raw_syn,
                    })
                    if raw_symbols_equal and not raw_syn:
                        raise ValueError("exact raw output failed its syndrome")
                    if raw_syn != raw_reported_syn:
                        raise ValueError("raw decoder syndrome flag disagrees with H*x=s")
                    if raw_exact:
                        raw_stratum = "raw_exact"
                    elif raw_syn:
                        raw_stratum = "raw_syndrome_valid_wrong"
                    else:
                        raw_stratum = "raw_syndrome_fail"
                    row.update({
                        "raw_stratum": raw_stratum,
                    })
                except Exception as exc:
                    arm_wall = max(float(now()) - arm_started, 0.0)
                    max_arm_wall = max(max_arm_wall, arm_wall)
                    resource_reason, rss_after = check_resource(arm_wall)
                    row.update({
                        "status": "RAW_RESULT_STOP",
                        "failure_reason": "%s:%s" % (type(exc).__name__, str(exc)),
                        "arm_wall_s": arm_wall,
                        "rss_after_bp_bytes": rss_after,
                    })
                    rows.append(row)
                    _append_row(root, row)
                    stop(resource_reason or row["failure_reason"],
                         "RESOURCE_STOP" if resource_reason else "INTEGRITY_STOP")
                    break

                resource_reason, rss_after_bp = check_resource(bp_wall)
                row["rss_after_bp_bytes"] = rss_after_bp
                if resource_reason:
                    arm_wall = max(float(now()) - arm_started, 0.0)
                    max_arm_wall = max(max_arm_wall, arm_wall)
                    row.update({
                        "status": "RESOURCE_STOP",
                        "failure_reason": resource_reason,
                        "arm_wall_s": arm_wall,
                    })
                    rows.append(row)
                    _append_row(root, row)
                    stop(resource_reason)
                    break

                diagnostic_started = float(now())
                try:
                    diagnostic = _mrb_reachability_diagnostic(
                        field=field, matrix=dense, syndrome=syndrome,
                        final_beliefs=beliefs, raw_hard=raw_hard, truth=truth)
                except Exception as exc:
                    diagnostic_wall = max(float(now()) - diagnostic_started, 0.0)
                    arm_wall = max(float(now()) - arm_started, 0.0)
                    max_arm_wall = max(max_arm_wall, arm_wall)
                    resource_reason, rss_after_diag = check_resource(arm_wall)
                    row.update({
                        "diagnostic_wall_s": diagnostic_wall,
                        "arm_wall_s": arm_wall,
                        "rss_after_diagnostic_bytes": rss_after_diag,
                        "status": "DIAGNOSTIC_STOP",
                        "failure_reason": "%s:%s" % (type(exc).__name__, str(exc)),
                    })
                    rows.append(row)
                    _append_row(root, row)
                    stop(resource_reason or row["failure_reason"],
                         "RESOURCE_STOP" if resource_reason else "DIAGNOSTIC_STOP")
                    break

                diagnostic_wall = max(float(now()) - diagnostic_started, 0.0)
                arm_wall = max(float(now()) - arm_started, 0.0)
                max_arm_wall = max(max_arm_wall, arm_wall)
                resource_reason, rss_after_diag = check_resource(arm_wall)
                array_index = len(arrays_by_index)
                row.update({
                    "rank": diagnostic["rank"],
                    "free_count": diagnostic["free_count"],
                    "D_free": diagnostic["D_free"],
                    "truth_syndrome_ok": diagnostic["truth_syndrome_ok"],
                    "truth_reconstruction_ok": diagnostic["truth_reconstruction_ok"],
                    "base_syndrome_ok": diagnostic["base_syndrome_ok"],
                    "base_equals_truth": diagnostic["base_equals_truth"],
                    "diagnostic_wall_s": diagnostic_wall,
                    "arm_wall_s": arm_wall,
                    "rss_after_diagnostic_bytes": rss_after_diag,
                    "diagnostic_array_index": array_index,
                    "status": "RESOURCE_STOP" if resource_reason else "COMPLETE",
                    "failure_reason": resource_reason or None,
                })
                arrays_by_index.append({
                    "truth": np.asarray(truth, dtype=np.uint8).copy(),
                    "raw_hard": np.asarray(raw_hard, dtype=np.uint8).copy(),
                    "syndrome": np.asarray(syndrome, dtype=np.uint8).copy(),
                    "final_beliefs": np.asarray(beliefs, dtype=np.float64).copy(),
                })
                rows.append(row)
                _append_row(root, row)
                if resource_reason:
                    stop(resource_reason)
                    break
    except Exception as exc:
        stop("implementation_exception:%s:%s" % (type(exc).__name__, str(exc)),
             "IMPLEMENTATION_STOP")
        _append_log(root, stop_reason)

    return finish()


def _bind_production_decoder() -> Callable[..., Any]:
    """Bind the frozen raw BP decoder only after explicit --execute."""
    from comparison_bench.formal_ir import v35_algorithm_development as v35

    def decode(h, prior, syndrome):
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=MAX_ITER,
            damping_alpha=DAMPING_ALPHA, warm_beliefs=WARM_BELIEFS,
            field=FIELD)

    return decode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GF32 MRB free-coordinate reachability EXPLORE")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true",
                      help="run the frozen synthetic single-arm batch")
    mode.add_argument("--dry-run", action="store_true",
                      help="check fixed math, seeds, and fresh output root only")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE),
                        help="must equal the frozen fresh workspace root")
    return parser


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    if not args.execute:
        result = dry_run(args.out_root)
    else:
        result = execute_batch(
            out_root=args.out_root, decode_fn=_bind_production_decoder(),
            graph_builder=search_runner.build_profile_graph,
            candidate_builder=search_runner._candidate_pair_for_graph,
            command=COMMAND)
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
