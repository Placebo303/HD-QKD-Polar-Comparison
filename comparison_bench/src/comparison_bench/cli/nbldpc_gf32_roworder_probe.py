"""Fixed within-degree GF(32) check-row ordering EXPLORE probe."""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from comparison_bench.cli import nbldpc_gf32_label_probe as prior_runner
from comparison_bench.cli import nbldpc_gf32_search_depth_probe as search_runner
from comparison_bench.cli import nbldpc_gf32_itercap_probe as iter_cap_runner
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

CONTRACT = "NBLDPC-GF32-ROW-ORDER-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "44c394bc-e3dd-4e6b-9d4a-8a5b0dd5cdfc"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_roworder_44c394bc"
SEED_PREFIX = "gf32-roworder-v1"

N = search_runner.N
M = search_runner.M
EDGE_COUNT = search_runner.EDGE_COUNT
GRAPH_SEEDS = tuple(search_runner.GRAPH_SEEDS)
SHAPE_COUNTS = tuple(search_runner.SHAPE_COUNTS)
SHAPE_TOTAL = int(search_runner.SHAPE_TOTAL)
P0 = 0.550
HOLDOUT_STREAMS = (0, 1)
HOLDOUT_FRAMES_PER_STREAM = 16
HOLDOUT_PAIRS = len(GRAPH_SEEDS) * len(HOLDOUT_STREAMS) * HOLDOUT_FRAMES_PER_STREAM
MAX_CALLS = 2 * HOLDOUT_PAIRS
WALL_CAP_S = 1800.0
CALL_CAP_S = 120.0
RSS_CAP_BYTES = 4 * 1024 ** 3
ARTIFACT_LIMIT_BYTES = 20 * 1024 * 1024
MAX_ITER = 90
CONTROL_ALPHA = 1.0
SYNDROME_BITS = 5 * M
CONTROL_MIN = 39
CONTROL_MAX = 153
SIGNAL_DELTA = 12
SIGNAL_POSITIVE_GRAPHS = 4

FRAME_FIELDS = (
    "call_index", "pair_index", "graph_seed", "stream", "frame", "seed",
    "arm", "row_order", "decoder_status", "status", "iterations",
    "raw_vector_saved", "raw_symbols_equal", "syndrome_accept",
    "base_syndrome_accept", "syndrome_consistent_wrong", "exact",
    "wall_s", "rss_b", "syndrome_bits", "failure_reason",
)
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_roworder_probe --execute "
    "--out-root workspace/gf32_roworder_44c394bc"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def seed_for(graph_seed: int, stream: int, frame: int) -> int:
    return int(common.v10_seed(
        f"{SEED_PREFIX}:holdout:{int(graph_seed)}:{int(stream)}:{int(frame)}"))


def seed_plan() -> list[tuple[int, int, int, int]]:
    return [
        (seed, stream, frame, seed_for(seed, stream, frame))
        for seed in GRAPH_SEEDS
        for stream in HOLDOUT_STREAMS
        for frame in range(HOLDOUT_FRAMES_PER_STREAM)
    ]


def arm_order(frame: int) -> tuple[str, str]:
    return ("control", "candidate") if int(frame) % 2 == 0 \
        else ("candidate", "control")


def _validate_seed_plan() -> list[tuple[int, int, int, int]]:
    plan = seed_plan()
    seeds = [row[3] for row in plan]
    old_plans = (
        prior_runner._seed_plan(),
        search_runner.fine_runner.predecessor.seed_plan(),
        search_runner.fine_runner.seed_plan(),
        search_runner.replica_runner.seed_plan(),
        search_runner.seed_plan(),
        iter_cap_runner.resource_runner.seed_plan(),
    )
    previous = {
        int(row[3]) for old_plan in old_plans
        for plan_part in old_plan for row in plan_part
    }
    previous.update(int(row[3]) for row in iter_cap_runner.seed_plan())
    if (len(plan) != HOLDOUT_PAIRS or len(set(seeds)) != HOLDOUT_PAIRS
            or len({row[:3] for row in plan}) != HOLDOUT_PAIRS
            or set(seeds) & previous):
        raise AssertionError("row-order seeds must be unique and prior-disjoint")
    if SEED_PREFIX != "gf32-roworder-v1":
        raise AssertionError("row-order seed namespace changed")
    return plan


def row_permutation(dense: Any) -> np.ndarray:
    """Return source row indices, preserving degree-block order and reversing each block."""
    h = np.asarray(dense)
    if h.ndim != 2 or h.shape[0] == 0:
        raise ValueError("row permutation requires a nonempty matrix")
    degrees = np.count_nonzero(h, axis=1)
    degree_order: list[int] = []
    rows_by_degree: dict[int, list[int]] = {}
    for index, degree_value in enumerate(degrees):
        degree = int(degree_value)
        if degree not in rows_by_degree:
            degree_order.append(degree)
            rows_by_degree[degree] = []
        rows_by_degree[degree].append(index)
    return np.asarray([
        index for degree in degree_order
        for index in reversed(rows_by_degree[degree])
    ], dtype=np.int64)


def verify_t0() -> dict[str, bool]:
    """Check frozen source/caps and the fixed row/syndrome identity without graph work."""
    checks = search_runner.verify_t0()
    pmf = np.asarray(search_runner.shape_pmf_grid()[0]["pmf"], dtype=np.float64)
    expected = np.zeros(32, dtype=np.float64)
    expected[0] = P0
    for symbol, count in SHAPE_COUNTS:
        expected[int(symbol)] = (1.0 - P0) * int(count) / SHAPE_TOTAL
    expected[0] = P0
    if (not np.allclose(pmf, expected, rtol=0.0, atol=1e-15)
            or MAX_ITER != 90 or CONTROL_ALPHA != 1.0
            or (N, M, EDGE_COUNT) != (128, 52, 256)
            or tuple(HOLDOUT_STREAMS) != (0, 1)
            or HOLDOUT_FRAMES_PER_STREAM != 16
            or MAX_CALLS != 384):
        raise AssertionError("frozen row-order inputs changed")
    tiny = np.asarray([[1, 1, 0], [0, 0, 1], [1, 0, 1], [0, 1, 0]],
                      dtype=np.int64)
    pi = row_permutation(tiny)
    truth = np.asarray([2, 7, 15], dtype=np.int64)
    base_syndrome = np.asarray(layout.gf32_syndrome(tiny, truth),
                               dtype=np.int64)
    if (pi.tolist() != [2, 0, 3, 1]
            or sorted(pi.tolist()) != list(range(tiny.shape[0]))
            or not np.array_equal(layout.gf32_syndrome(tiny[pi], truth),
                                  base_syndrome[pi])):
        raise AssertionError("row permutation is not bijective/syndrome preserving")
    plan = _validate_seed_plan()
    if any(arm_order(frame) not in (
            ("control", "candidate"), ("candidate", "control"))
           for _, _, frame, _ in plan):
        raise AssertionError("invalid paired arm order")
    checks.update({
        "exact_frozen_pmf": True,
        "fixed_graph_decoder_profile": True,
        "fixed_within_degree_permutation_and_syndrome": True,
        "new_seed_namespace_unique_and_prior_disjoint": True,
        "192_pairs_384_calls": True,
    })
    return checks


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() \
        else (root / requested).resolve()
    expected = (root / OUT_ROOT_RELATIVE).resolve()
    if resolved != expected:
        raise ValueError(f"out-root must equal the frozen fresh root {expected}")
    if resolved.exists():
        raise FileExistsError(f"refusing existing output root {resolved}")
    return resolved


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root)
    t0 = verify_t0()
    return {
        "track": "EXPLORE", "status": "DRY_RUN", "batch_uuid": BATCH_UUID,
        "contract": CONTRACT, "out_root": str(root), "exists": root.exists(),
        "t0": t0, "attempted_decoder_calls": 0, "writes": 0,
        "artifact_reads": 0, "graph_calls": 0, "preflight_calls": 0,
        "candidate_calls": 0, "sampler_calls": 0, "decoder_calls": 0,
        "osd_calls": 0, "holdout_pairs": HOLDOUT_PAIRS,
        "maximum_decoder_calls": MAX_CALLS,
    }


def _initial_manifest(command: str) -> dict[str, Any]:
    pmf = np.asarray(search_runner.shape_pmf_grid()[0]["pmf"], dtype=float)
    return {
        "track": "EXPLORE", "batch_uuid": BATCH_UUID,
        "contract": CONTRACT, "status": "RUNNING",
        "graph_profile": {
            "n": N, "m": M, "E": EDGE_COUNT,
            "field": "GF(32)/polynomial-37",
            "graph_seeds": list(GRAPH_SEEDS),
            "constructor": "accepted SEARCH-DEPTH H0D construction",
        },
        "source_shape_proxy": {
            "p0": P0,
            "counts": {str(e): c for e, c in SHAPE_COUNTS},
            "total": SHAPE_TOTAL,
            "role": "synthetic iid marginal shape with Bob=0 and matched prior",
            "empirical_input_reads": False,
        },
        "pmf": [float(value) for value in pmf],
        "seed_namespace": SEED_PREFIX,
        "seed_plan": [
            {"graph_seed": g, "stream": s, "frame": f, "seed": seed}
            for g, s, f, seed in _validate_seed_plan()
        ],
        "seed_plan_disjoint_from_prior_batches": True,
        "arm_mapping": {"control": "natural row order of admitted deep H0D",
                        "candidate": "one fixed within-degree block reversal"},
        "row_permutation_rule": (
            "first-occurrence degree-class order; reverse source row indices "
            "within each class; candidate H=Hdeep[pi], syndrome=syndrome_deep[pi]"),
        "npz_matrix_mapping": {
            "H_base": "constructor H0 provenance only; neither arm decodes this matrix",
            "H_candidate": "admitted deep H0D in natural row order; control uses this, candidate uses H_candidate[pi]",
        },
        "decoder_profile": {
            "decoder": "layered FFT-QSPA", "max_iter": MAX_ITER,
            "damping_alpha": CONTROL_ALPHA,
            "warm_start": None, "field": None,
        },
        "arm_order": "control first on even frame, candidate first on odd",
        "budgets": {
            "total_wall_s": WALL_CAP_S, "per_call_wall_s": CALL_CAP_S,
            "sampled_rss_bytes": RSS_CAP_BYTES,
            "maximum_bp_calls": MAX_CALLS, "maximum_osd_calls": 0,
            "diagnostics_bytes": ARTIFACT_LIMIT_BYTES,
        },
        "accounting": {
            "syndrome_bits_per_attempted_arm": SYNDROME_BITS,
            "tag_bits": 0, "verification": "NOT_IMPLEMENTED",
            "undetected": "NOT_MEASURED",
            "success": "raw vector equals truth and independently passes base and arm syndrome",
            "wrong": "syndrome-valid but not exact; separately counted failure",
        },
        "exact_command": command or COMMAND,
        "attempted_decoder_calls": 0,
        "attempted_frame_rows": 0,
        "stop_reason": "", "graph_diagnostics": [],
        "candidate_diagnostics": [], "permutations": [],
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
        stream.write("# GF32 within-degree row-order EXPLORE log\n\n")
        stream.write(f"Batch UUID: `{BATCH_UUID}`.\n\n")


def _append_log(root: Path, message: str) -> None:
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as stream:
        stream.write(f"- {message}\n")


def _append_row(root: Path, row: Mapping[str, Any]) -> None:
    with (root / "frame_records.csv").open(
            "a", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=FRAME_FIELDS).writerow(
            {key: row.get(key) for key in FRAME_FIELDS})
    _append_log(root, (
        "call={call_index} pair={pair_index} {arm}/{row_order} graph={graph_seed} "
        "stream={stream} frame={frame} seed={seed} exact={exact} "
        "syndrome={syndrome_accept} base_syndrome={base_syndrome_accept} "
        "iterations={iterations} status={status} wall_s={wall_s:.6f}"
    ).format(**row))


def _summarize(
        rows: Sequence[Mapping[str, Any]], *,
        expected_pairs: int = HOLDOUT_PAIRS,
        terminal_status: str = "COMPLETE",
        stop_reason: str | None = None,
        resource_stop_markers: Sequence[str] = (),
        integrity_violations: int = 0,
        authorization_violations: int = 0,
        ) -> dict[str, Any]:
    grouped: dict[int, dict[str, Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(int(row["pair_index"]), {})[str(row["arm"])] = row
    complete = bool(
        len(grouped) == int(expected_pairs)
        and len(rows) == 2 * int(expected_pairs)
        and len({(int(row["pair_index"]), str(row["arm"]))
                 for row in rows}) == len(rows)
        and all(set(pair) == {"control", "candidate"}
                for pair in grouped.values())
        and all(row.get("exact") is not None
                and row.get("syndrome_accept") is not None
                and row.get("base_syndrome_accept") is not None
                for pair in grouped.values() for row in pair.values())
    )
    arm_rows = {
        arm: [row for row in rows if row.get("arm") == arm]
        for arm in ("control", "candidate")
    }
    result: dict[str, Any] = {
        "track": "EXPLORE", "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "complete": complete, "terminal_status": terminal_status,
        "classification": "INCOMPLETE" if not complete else "NO_SUFFICIENT_SIGNAL",
        "stop_reason": stop_reason,
        "stop_reasons": [stop_reason] if stop_reason else [],
        "attempted_decoder_calls": len(rows), "attempted_frame_rows": len(rows),
        "attempted_pairs": len(grouped),
        "completed_pairs": sum(set(pair) == {"control", "candidate"}
                                for pair in grouped.values()),
        "seed_namespace": SEED_PREFIX, "fixed_p0": P0,
        "max_iter": MAX_ITER, "damping_alpha": CONTROL_ALPHA,
        "syndrome_bits_per_attempted_arm": SYNDROME_BITS,
        "disclosed_syndrome_bits": len(rows) * SYNDROME_BITS,
        "tag_bits": 0, "verification": "NOT_IMPLEMENTED",
        "undetected": "NOT_MEASURED",
        "integrity_violations": int(integrity_violations),
        "resource_violations": len(resource_stop_markers),
        "resource_stop_markers": list(resource_stop_markers),
        "authorization_violations": int(authorization_violations),
        "per_arm_attempts": {arm: len(values) for arm, values in arm_rows.items()},
        "control_exact": None, "candidate_exact": None, "delta": None,
        "positive_graphs": None, "per_graph": None, "paired": None,
        "transitions": None, "per_arm_outcomes": None,
    }
    if not complete:
        return result

    def arm_counts(selected: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        walls = [float(row["wall_s"]) for row in selected
                 if row.get("wall_s") is not None]
        rss = [int(row["rss_b"]) for row in selected
               if row.get("rss_b") is not None]
        valid = [row for row in selected
                 if row.get("syndrome_accept") is True
                 and row.get("base_syndrome_accept") is True]
        return {
            "attempted": len(selected),
            "exact_and_syndrome": sum(row.get("exact") is True for row in selected),
            "syndrome_valid_wrong": sum(
                row.get("syndrome_consistent_wrong") is True for row in selected),
            "raw_syndrome_fail": len(selected) - len(valid),
            "iterations_sum": sum(int(row.get("iterations") or 0)
                                   for row in selected),
            "wall_s_sum": float(sum(walls)),
            "max_call_wall_s": max(walls, default=None),
            "max_sampled_rss_bytes": max(rss, default=None),
        }

    per_arm = {arm: arm_counts(values) for arm, values in arm_rows.items()}
    per_graph: dict[str, dict[str, int]] = {}
    for graph_seed in GRAPH_SEEDS:
        selected = [pair for pair in grouped.values()
                    if int(pair["control"]["graph_seed"]) == int(graph_seed)]
        control = sum(pair["control"].get("exact") is True for pair in selected)
        candidate = sum(pair["candidate"].get("exact") is True for pair in selected)
        per_graph[str(graph_seed)] = {
            "pairs": len(selected), "control_exact": int(control),
            "candidate_exact": int(candidate),
            "delta_g": int(candidate - control),
        }
    delta = int(per_arm["candidate"]["exact_and_syndrome"]
                - per_arm["control"]["exact_and_syndrome"])
    positive = sum(item["delta_g"] > 0 for item in per_graph.values())
    paired = {key: 0 for key in
              ("both", "control_only", "candidate_only", "neither")}
    transitions = {
        "control_raw_fail_to_candidate_exact": 0,
        "control_raw_fail_to_candidate_valid_wrong": 0,
        "control_raw_fail_to_candidate_still_fail": 0,
    }
    for pair in grouped.values():
        control = pair["control"]
        candidate = pair["candidate"]
        c_ok = control.get("exact") is True
        k_ok = candidate.get("exact") is True
        paired[{(True, True): "both", (True, False): "control_only",
                (False, True): "candidate_only", (False, False): "neither"}
               [(c_ok, k_ok)]] += 1
        if not (control.get("syndrome_accept") is True
                and control.get("base_syndrome_accept") is True):
            if candidate.get("exact") is True:
                transitions["control_raw_fail_to_candidate_exact"] += 1
            elif candidate.get("syndrome_consistent_wrong") is True:
                transitions["control_raw_fail_to_candidate_valid_wrong"] += 1
            elif not (candidate.get("syndrome_accept") is True
                      and candidate.get("base_syndrome_accept") is True):
                transitions["control_raw_fail_to_candidate_still_fail"] += 1
    control_exact = int(per_arm["control"]["exact_and_syndrome"])
    if not CONTROL_MIN <= control_exact <= CONTROL_MAX:
        classification = "CONTROL_RANGE_UNINFORMATIVE"
    elif (delta >= SIGNAL_DELTA and positive >= SIGNAL_POSITIVE_GRAPHS
          and integrity_violations == 0 and not resource_stop_markers
          and authorization_violations == 0):
        classification = "MECHANISM_SIGNAL"
    else:
        classification = "NO_SUFFICIENT_SIGNAL"
    result.update({
        "classification": classification,
        "control_exact": control_exact,
        "candidate_exact": int(per_arm["candidate"]["exact_and_syndrome"]),
        "delta": delta, "positive_graphs": int(positive),
        "per_graph": per_graph, "paired": paired,
        "transitions": transitions, "per_arm_outcomes": per_arm,
    })
    return result


def _validated_raw_vector(raw_result: Any) -> np.ndarray | None:
    try:
        raw = np.asarray(raw_result.x_hat)
        if raw.shape != (N,) or not np.issubdtype(raw.dtype, np.integer):
            return None
        if np.any(raw < 0) or np.any(raw >= 32):
            return None
        return raw.astype(np.uint8, copy=True)
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None


def _diagnostics_arrays(
        graph_matrices: Mapping[int, np.ndarray],
        candidate_matrices: Mapping[int, np.ndarray],
        permutations: Mapping[int, np.ndarray],
        pair_inputs: Sequence[Mapping[str, Any]],
        rows: Sequence[Mapping[str, Any]],
        vectors: Sequence[Mapping[str, Any]],
        ) -> dict[str, np.ndarray]:
    seeds = [seed for seed in GRAPH_SEEDS
             if seed in graph_matrices and seed in candidate_matrices
             and seed in permutations]
    graph_index = {seed: index for index, seed in enumerate(seeds)}
    pairs = list(pair_inputs)
    vector_by_call = {int(vector["call_index"]): index
                      for index, vector in enumerate(vectors)}
    return {
        "graph_seed": np.asarray(seeds, dtype=np.int64),
        "H_base": np.stack([graph_matrices[s] for s in seeds]).astype(
            np.uint8, copy=False) if seeds else np.empty((0, M, N), np.uint8),
        "H_candidate": np.stack([candidate_matrices[s] for s in seeds]).astype(
            np.uint8, copy=False) if seeds else np.empty((0, M, N), np.uint8),
        "row_permutation": np.stack([permutations[s] for s in seeds]).astype(
            np.int64, copy=False) if seeds else np.empty((0, M), np.int64),
        "pair_index": np.asarray([p["pair_index"] for p in pairs], np.int64),
        "pair_graph_index": np.asarray([
            graph_index[int(p["graph_seed"])] for p in pairs], np.int64),
        "pair_graph_seed": np.asarray([p["graph_seed"] for p in pairs], np.int64),
        "pair_stream": np.asarray([p["stream"] for p in pairs], np.int64),
        "pair_frame": np.asarray([p["frame"] for p in pairs], np.int64),
        "pair_seed": np.asarray([p["seed"] for p in pairs], np.int64),
        "pair_truth": np.stack([p["truth"] for p in pairs]).astype(
            np.uint8, copy=False) if pairs else np.empty((0, N), np.uint8),
        "pair_syndrome_base": np.stack([p["syndrome_base"] for p in pairs]).astype(
            np.uint8, copy=False) if pairs else np.empty((0, M), np.uint8),
        "pair_syndrome_candidate": np.stack([
            p["syndrome_candidate"] for p in pairs]).astype(
                np.uint8, copy=False) if pairs else np.empty((0, M), np.uint8),
        "call_index": np.asarray([row["call_index"] for row in rows], np.int64),
        "call_pair_index": np.asarray([row["pair_index"] for row in rows], np.int64),
        "call_arm": np.asarray([row["arm"] for row in rows], dtype="<U9"),
        "call_vector_index": np.asarray([
            vector_by_call.get(int(row["call_index"]), -1) for row in rows], np.int64),
        "vector_call_index": np.asarray([v["call_index"] for v in vectors], np.int64),
        "vector_pair_index": np.asarray([v["pair_index"] for v in vectors], np.int64),
        "vector_arm": np.asarray([v["arm"] for v in vectors], dtype="<U9"),
        "vector_graph_seed": np.asarray([v["graph_seed"] for v in vectors], np.int64),
        "vector_stream": np.asarray([v["stream"] for v in vectors], np.int64),
        "vector_frame": np.asarray([v["frame"] for v in vectors], np.int64),
        "vector_seed": np.asarray([v["seed"] for v in vectors], np.int64),
        "raw_x_hat": np.stack([v["raw_x_hat"] for v in vectors]).astype(
            np.uint8, copy=False) if vectors else np.empty((0, N), np.uint8),
    }


def _write_diagnostics(root: Path, arrays: Mapping[str, np.ndarray]) -> int:
    payload = sum(int(value.nbytes) for value in arrays.values())
    if payload > ARTIFACT_LIMIT_BYTES:
        raise ValueError("diagnostics.npz payload exceeds the frozen 20 MiB cap")
    path = root / "diagnostics.npz"
    np.savez_compressed(path, **arrays)
    size = int(path.stat().st_size)
    if size > ARTIFACT_LIMIT_BYTES:
        raise ValueError("diagnostics.npz exceeds the frozen 20 MiB cap")
    return size


def execute_batch(
        *, out_root: str | Path,
        decode_fns: Mapping[str, Callable[[np.ndarray, np.ndarray, np.ndarray], Any]],
        graph_builder: Callable[[int], Mapping[str, Any]],
        candidate_builder: Callable[
            [np.ndarray, np.ndarray, int],
            tuple[np.ndarray | None, np.ndarray | None, Mapping[str, Any]]],
        preflight_fn: Callable[
            [Mapping[str, Any], int], tuple[bool, Mapping[str, Any]]],
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str = COMMAND,
        ) -> dict[str, Any]:
    if (not isinstance(decode_fns, Mapping)
            or set(decode_fns) != {"control", "candidate"}
            or any(not callable(decode_fns[key])
                   for key in ("control", "candidate"))):
        raise ValueError("explicit control and candidate decoder callbacks are required")
    if not all(callable(fn) for fn in (graph_builder, candidate_builder, preflight_fn)):
        raise ValueError("explicit graph, candidate and preflight callbacks are required")
    root = validate_out_root(out_root, repo_root=repo_root)
    if rss_fn is None:
        rss_fn = d5._rss_bytes

    started = float(now())
    rss_samples: list[int] = []
    resource_markers: list[str] = []
    rss_errors: list[str] = []
    calls = 0
    integrity_violations = 0
    stop_reason = ""
    terminal = "INCOMPLETE"
    graph_diagnostics: list[dict[str, Any]] = []
    candidate_diagnostics: list[dict[str, Any]] = []
    graph_matrices: dict[int, np.ndarray] = {}
    candidate_matrices: dict[int, np.ndarray] = {}
    permutations: dict[int, np.ndarray] = {}
    pair_inputs: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    vectors: list[dict[str, Any]] = []
    output_started = False

    def sampled_rss() -> int | None:
        try:
            value = rss_fn()
        except Exception as exc:
            marker = f"rss_monitor_exception:{type(exc).__name__}:{exc}"
            if marker not in rss_errors:
                rss_errors.append(marker)
            return None
        if value is not None:
            rss_samples.append(int(value))
        return value

    def resource_issue(*, before_call: bool = True) -> str:
        if before_call and calls >= MAX_CALLS:
            return "decoder_call_count_cap_before_next_call"
        if max(float(now()) - started, 0.0) >= WALL_CAP_S:
            return "total_wall_cap_before_next_call"
        value = sampled_rss()
        if rss_errors:
            return rss_errors[0]
        if value is not None and int(value) >= RSS_CAP_BYTES:
            return "rss_cap_before_next_call"
        return ""

    def finish() -> dict[str, Any]:
        nonlocal output_started, terminal, stop_reason
        pre_write_resource = resource_issue(before_call=False)
        if pre_write_resource and pre_write_resource not in resource_markers:
            resource_markers.append(pre_write_resource)
            if not stop_reason:
                stop_reason = pre_write_resource
                terminal = "RESOURCE_STOP"
        arrays = _diagnostics_arrays(
            graph_matrices, candidate_matrices, permutations,
            pair_inputs, rows, vectors)
        npz_size = _write_diagnostics(root, arrays)
        post_write_resource = resource_issue(before_call=False)
        if post_write_resource and post_write_resource not in resource_markers:
            resource_markers.append(post_write_resource)
            if not stop_reason:
                stop_reason = post_write_resource
                terminal = "RESOURCE_STOP"
        summary = _summarize(
            rows, terminal_status=terminal,
            stop_reason=stop_reason or None,
            resource_stop_markers=resource_markers,
            integrity_violations=integrity_violations)
        summary.update({
            "terminal_status": terminal,
            "attempted_decoder_calls": calls,
            "attempted_frame_rows": len(rows),
            "sampled_pairs_with_inputs": len(pair_inputs),
            "batch_wall_s": max(float(now()) - started, 0.0),
            "sampled_max_rss_bytes": max(rss_samples, default=None),
            "rss_sample_count": len(rss_samples),
            "rss_monitor_errors": list(rss_errors),
            "npz_bytes": npz_size,
            "actual_syndrome_disclosure_bits": calls * SYNDROME_BITS,
            "actual_osd_calls": 0,
        })
        _write_json(root / "summary.json", summary)
        manifest.update({
            "status": terminal, "stop_reason": stop_reason,
            "attempted_decoder_calls": calls,
            "attempted_frame_rows": len(rows),
            "attempted_pairs": len(pair_inputs),
            "batch_wall_s": summary["batch_wall_s"],
            "sampled_max_rss_bytes": summary["sampled_max_rss_bytes"],
            "rss_sample_count": len(rss_samples),
            "rss_monitor_errors": list(rss_errors),
            "graph_diagnostics": graph_diagnostics,
            "candidate_diagnostics": candidate_diagnostics,
            "permutations": [
                {"graph_seed": seed, "pi": permutations[seed].tolist()}
                for seed in GRAPH_SEEDS if seed in permutations
            ],
            "diagnostics_npz_bytes": npz_size,
        })
        _write_json(root / "manifest.json", manifest)
        _append_log(root, (
            f"terminal={terminal} classification={summary['classification']} "
            f"calls={calls} pairs={summary['completed_pairs']} "
            f"stop_reason={stop_reason or 'none'}"))
        output_started = True
        return summary

    pmf_entry = search_runner.shape_pmf_grid()[0]
    pmf = np.asarray(pmf_entry["pmf"], dtype=np.float64)
    manifest = _initial_manifest(command)
    _start_outputs(root, manifest)
    output_started = True
    _append_log(root, "T0 started; no graph, sample, or decoder call has occurred")
    try:
        t0 = verify_t0()
        manifest["t0"] = t0
        _write_json(root / "manifest.json", manifest)
        _append_log(root, "T0 PASS")

        stop = ""
        for graph_seed in GRAPH_SEEDS:
            stop = resource_issue()
            if stop:
                terminal = "RESOURCE_STOP"
                resource_markers.append(stop)
                break
            graph = graph_builder(int(graph_seed))
            admitted, diagnostic = preflight_fn(graph, int(graph_seed))
            graph_diagnostics.append(dict(diagnostic))
            dense_value = graph.get("dense")
            if (not admitted or dense_value is None
                    or np.asarray(dense_value).shape != (M, N)):
                stop = str(diagnostic.get("failure_reason")
                           or f"graph_preflight_failed:{graph_seed}")
                terminal = "GRAPH_PREFLIGHT_STOP"
                break
            graph_matrices[int(graph_seed)] = np.asarray(
                dense_value, dtype=np.int64).copy()
            stop = resource_issue()
            if stop:
                terminal = "RESOURCE_STOP"
                resource_markers.append(stop)
                break
        if not stop and len(graph_matrices) != len(GRAPH_SEEDS):
            stop = "GRAPH_PREFLIGHT_INCOMPLETE"
            terminal = "GRAPH_PREFLIGHT_STOP"

        if not stop:
            prior = np.tile(pmf, (N, 1))
            for graph_seed in GRAPH_SEEDS:
                stop = resource_issue()
                if stop:
                    terminal = "RESOURCE_STOP"
                    resource_markers.append(stop)
                    break
                onepass, deep, diagnostic = candidate_builder(
                    graph_matrices[graph_seed], pmf.copy(), int(graph_seed))
                diagnostic = dict(diagnostic)
                candidate_diagnostics.append(diagnostic)
                admitted_onepass = bool(diagnostic.get(
                    "candidate_admitted", onepass is not None))
                admitted_deep = bool(diagnostic.get(
                    "deep_candidate_admitted", deep is not None))
                if (diagnostic.get("construction_stop") or not admitted_onepass
                        or not admitted_deep or onepass is None or deep is None):
                    stop = str(diagnostic.get("failure_reason")
                               or f"candidate_admission_failed:{graph_seed}")
                    terminal = "CANDIDATE_ADMISSION_STOP"
                    break
                h0 = graph_matrices[graph_seed]
                h_deep = np.asarray(deep, dtype=np.int64)
                h_onepass = np.asarray(onepass, dtype=np.int64)
                if (h_onepass.shape != (M, N) or h_deep.shape != (M, N)
                        or not np.array_equal(h0 != 0, h_onepass != 0)
                        or not np.array_equal(h0 != 0, h_deep != 0)):
                    stop = f"candidate_shape_or_support_integrity:{graph_seed}"
                    terminal = "INTEGRITY_STOP"
                    integrity_violations += 1
                    break
                pi = row_permutation(h_deep)
                h_candidate = h_deep[pi].copy()
                if (sorted(pi.tolist()) != list(range(M))
                        or not np.array_equal(
                            np.count_nonzero(h_candidate, axis=1),
                            np.count_nonzero(h_deep, axis=1)[pi])):
                    stop = f"row_permutation_integrity:{graph_seed}"
                    terminal = "INTEGRITY_STOP"
                    integrity_violations += 1
                    break
                candidate_matrices[graph_seed] = h_deep.copy()
                permutations[graph_seed] = pi
                stop = resource_issue()
                if stop:
                    terminal = "RESOURCE_STOP"
                    resource_markers.append(stop)
                    break
        if not stop and len(candidate_matrices) != len(GRAPH_SEEDS):
            stop = "CANDIDATE_CONSTRUCTION_INCOMPLETE"
            terminal = "CANDIDATE_ADMISSION_STOP"

        if not stop:
            for pair_index, (graph_seed, stream, frame, seed) in enumerate(
                    _validate_seed_plan()):
                pair_stop = resource_issue()
                if pair_stop:
                    stop = pair_stop
                    terminal = "RESOURCE_STOP"
                    resource_markers.append(pair_stop)
                    break
                truth = prior_runner.sample_error(seed, pmf, width=N)
                h_deep = candidate_matrices[graph_seed]
                pi = permutations[graph_seed]
                h_candidate = h_deep[pi]
                arm_inputs = prior_runner.paired_arm_data(
                    h_deep, h_candidate, truth, prior)
                syndrome_base = np.asarray(
                    arm_inputs["control"]["syndrome"], dtype=np.int64)
                syndrome_candidate = syndrome_base[pi].copy()
                if not np.array_equal(syndrome_candidate,
                                      arm_inputs["candidate"]["syndrome"]):
                    stop = f"permuted_syndrome_integrity:{graph_seed}:{stream}:{frame}"
                    terminal = "INTEGRITY_STOP"
                    integrity_violations += 1
                    break
                pair_inputs.append({
                    "pair_index": int(pair_index), "graph_seed": int(graph_seed),
                    "stream": int(stream), "frame": int(frame), "seed": int(seed),
                    "truth": np.asarray(truth, dtype=np.uint8).copy(),
                    "syndrome_base": syndrome_base.astype(np.uint8, copy=True),
                    "syndrome_candidate": syndrome_candidate.astype(
                        np.uint8, copy=True),
                })
                arm_rows: dict[str, dict[str, Any]] = {}
                for arm in arm_order(frame):
                    pair_stop = resource_issue()
                    if pair_stop:
                        stop = pair_stop
                        terminal = "RESOURCE_STOP"
                        resource_markers.append(pair_stop)
                        break
                    row_order = ("natural" if arm == "control"
                                 else "degree_block_reversed")
                    dense = h_deep if arm == "control" else h_candidate
                    syndrome = (syndrome_base if arm == "control"
                                else syndrome_candidate)
                    call_index = calls
                    calls += 1
                    row, raw_vector, issue = _observe_call(
                        decode_fns[arm], dense, prior, syndrome, truth,
                        h_deep, syndrome_base, now=now, rss_fn=sampled_rss,
                        arm=arm)
                    row.update({
                        "call_index": call_index, "pair_index": pair_index,
                        "graph_seed": graph_seed, "stream": stream,
                        "frame": frame, "seed": seed, "arm": arm,
                        "row_order": row_order,
                        "syndrome_bits": SYNDROME_BITS,
                    })
                    rows.append(row)
                    if raw_vector is not None:
                        vectors.append({
                            "call_index": call_index, "pair_index": pair_index,
                            "graph_seed": graph_seed, "stream": stream,
                            "frame": frame, "seed": seed, "arm": arm,
                            "raw_x_hat": raw_vector,
                        })
                    _append_row(root, row)
                    arm_rows[arm] = row
                    post_resource = resource_issue(before_call=False)
                    if post_resource:
                        if post_resource not in resource_markers:
                            resource_markers.append(post_resource)
                        issue = ";".join(x for x in (issue, post_resource) if x)
                    if issue:
                        stop = issue
                        issue_parts = issue.split(";")
                        resource_parts = [part for part in issue_parts
                                          if any(token in part for token in
                                                 ("cap", "wall", "rss", "resource"))]
                        integrity_parts = [part for part in issue_parts
                                           if part not in resource_parts]
                        for marker in resource_parts:
                            if marker not in resource_markers:
                                resource_markers.append(marker)
                        if integrity_parts:
                            integrity_violations += 1
                        if resource_parts:
                            terminal = "RESOURCE_STOP"
                        else:
                            terminal = "INTEGRITY_STOP"
                        break
                if stop:
                    break
                if set(arm_rows) != {"control", "candidate"}:
                    stop = "paired_call_incomplete"
                    terminal = "INTEGRITY_STOP"
                    integrity_violations += 1
                    break
            if not stop:
                terminal = "COMPLETE"
                stop_reason = ""
            else:
                stop_reason = stop
        else:
            stop_reason = stop

        return finish()
    except Exception as exc:
        if not stop_reason:
            stop_reason = f"implementation_exception:{type(exc).__name__}:{exc}"
        terminal = "IMPLEMENTATION_STOP"
        if output_started:
            _append_log(root, stop_reason)
            finish()
        raise


def _observe_call(decode_fn, dense: np.ndarray, prior: np.ndarray,
                  syndrome: np.ndarray, truth: np.ndarray,
                  base_h: np.ndarray, base_syndrome: np.ndarray, *,
                  now: Callable[[], float], rss_fn: Callable[[], int | None],
                  arm: str) -> tuple[dict[str, Any], np.ndarray | None, str]:
    input_h = np.asarray(dense, dtype=np.int64).copy()
    input_prior = np.asarray(prior, dtype=np.float64).copy()
    input_syndrome = np.asarray(syndrome, dtype=np.int64).copy()
    before = (input_h.copy(), input_prior.copy(), input_syndrome.copy())
    captured: dict[str, Any] = {}

    def capture(h, p, syn):
        result = decode_fn(h, p, syn)
        captured["result"] = result
        return result

    observed, issue = prior_runner.decode_observation(
        capture, input_h, input_prior, truth, input_syndrome,
        now=now, rss_fn=rss_fn)
    raw_result = captured.get("result")
    raw = _validated_raw_vector(raw_result)
    if raw is None and not issue:
        issue = "raw_vector_not_validated_for_evidence"
    mutated = not (np.array_equal(input_h, before[0])
                   and np.array_equal(input_prior, before[1])
                   and np.array_equal(input_syndrome, before[2]))
    if mutated:
        issue = ";".join(x for x in (issue, "decoder_input_mutation") if x)
    try:
        iterations = int(observed["iterations"])
        elapsed = float(observed["wall_s"])
        rss = observed["rss_b"]
    except (KeyError, TypeError, ValueError, OverflowError):
        iterations, elapsed, rss = 0, 0.0, None
        issue = ";".join(x for x in (issue, "observation_record_integrity") if x)
    exact_raw = (None if raw is None else bool(np.array_equal(raw, truth)))
    arm_syndrome_ok = (None if raw is None else bool(
        layout.syndrome_ok(input_h, raw, input_syndrome)))
    base_syndrome_ok = (None if raw is None else bool(
        layout.syndrome_ok(base_h, raw, base_syndrome)))
    if raw is not None:
        if bool(observed["syndrome_accept"]) != bool(arm_syndrome_ok):
            issue = ";".join(x for x in (issue, "observer_syndrome_mismatch") if x)
        if arm_syndrome_ok != base_syndrome_ok:
            issue = ";".join(x for x in (issue, "base_arm_syndrome_mismatch") if x)
        raw_iterations = getattr(raw_result, "iterations", None)
        if (isinstance(raw_iterations, bool)
                or not isinstance(raw_iterations, (int, np.integer))
                or iterations < 0 or iterations > MAX_ITER):
            issue = ";".join(x for x in (issue, "iteration_count_integrity") if x)
        elif not arm_syndrome_ok and iterations != MAX_ITER:
            issue = ";".join(x for x in (issue, "raw_failure_not_at_cap") if x)
    raw_wrong = (None if raw is None else bool(
        arm_syndrome_ok and base_syndrome_ok and not exact_raw))
    exact = (None if raw is None else bool(
        exact_raw and arm_syndrome_ok and base_syndrome_ok))
    decoder_status = getattr(raw_result, "status", None) if raw_result is not None else None
    row = {
        "decoder_status": None if decoder_status is None else str(decoder_status),
        "status": str(observed.get("status", "observation_error")),
        "iterations": iterations,
        "raw_vector_saved": raw is not None,
        "raw_symbols_equal": exact_raw,
        "syndrome_accept": arm_syndrome_ok,
        "base_syndrome_accept": base_syndrome_ok,
        "syndrome_consistent_wrong": raw_wrong,
        "exact": exact, "wall_s": elapsed, "rss_b": rss,
        "failure_reason": issue,
    }
    return row, raw, issue


def _bind_production() -> dict[str, Any]:
    """Lazily bind accepted graph/deep-H helpers and fixed decoder settings."""
    from comparison_bench.formal_ir import v35_algorithm_development as v35

    def decode(h, prior, syndrome):
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=MAX_ITER,
            damping_alpha=CONTROL_ALPHA, warm_beliefs=None, field=None)

    return {
        "decode_fns": {"control": decode, "candidate": decode},
        "graph_builder": search_runner.build_profile_graph,
        "candidate_builder": search_runner._candidate_pair_for_graph,
        "preflight_fn": search_runner.graph_preflight,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fixed within-degree GF(32) row-order EXPLORE probe")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true",
                      help="run the frozen synthetic batch")
    mode.add_argument("--dry-run", action="store_true",
                      help="check pure math and the fresh output root")
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
            out_root=root, command=COMMAND, **_bind_production())
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
