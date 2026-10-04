"""Matched GF32 degree-profile EXPLORE probe (fixed two-profile batch)."""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from comparison_bench.cli import nbldpc_gf32_label_probe as prior_runner
from comparison_bench.cli import nbldpc_gf32_roworder_probe as base_runner
from comparison_bench.cli import nbldpc_gf32_search_depth_probe as search_runner
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import nonbinary_v10_common as common
from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as d10
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

CONTRACT = "NBLDPC-GF32-DEGREE-PROFILE-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "8c881d42-8d11-4867-8175-bc6f5c97f1f3"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_degree_8c881d42"
SEED_PREFIX = "gf32-degree-v1"
N, M = 128, 52
GRAPH_SEEDS = tuple(range(2026093901, 2026093907))
SHAPE_COUNTS = tuple(search_runner.SHAPE_COUNTS)
SHAPE_TOTAL = int(search_runner.SHAPE_TOTAL)
P0 = 0.550
HOLDOUT_STREAMS = (0, 1)
HOLDOUT_FRAMES_PER_STREAM = 16
HOLDOUT_PAIRS = len(GRAPH_SEEDS) * len(HOLDOUT_STREAMS) * HOLDOUT_FRAMES_PER_STREAM
MAX_CALLS = 2 * HOLDOUT_PAIRS
MAX_ITER = 90
DAMPING_ALPHA = 1.0
SYNDROME_BITS = 5 * M
WALL_CAP_S = 1800.0
CALL_CAP_S = 120.0
RSS_CAP_BYTES = 4 * 1024 ** 3
ARTIFACT_LIMIT_BYTES = 20 * 1024 * 1024
EDGE_UPDATE_PROXY_CAP = HOLDOUT_PAIRS * MAX_ITER * (256 + 384)

PROFILE_ORDER = ("control", "candidate")
PROFILES: dict[str, dict[str, Any]] = {
    "control": {
        "profile_id": "control", "n": N, "m": M, "edge_count": 256,
        "variable_counts": {2: 128}, "check_counts": {4: 4, 5: 48},
    },
    "candidate": {
        "profile_id": "candidate", "n": N, "m": M, "edge_count": 384,
        "variable_counts": {3: 128}, "check_counts": {7: 32, 8: 20},
    },
}

FRAME_FIELDS = (
    "call_index", "pair_index", "graph_seed", "stream", "frame", "seed",
    "arm", "profile_id", "decoder_status", "status", "iterations",
    "raw_vector_saved", "raw_symbols_equal", "syndrome_accept",
    "base_syndrome_accept", "syndrome_consistent_wrong", "exact",
    "wall_s", "rss_b", "syndrome_bits", "failure_reason",
    "batch_uuid", "contract", "seed_namespace",
)
SOURCE_FRAME_FIELDS = (
    "source_uuid", "source_path", "source_matrix_index", "source_attempt_j",
    "source_construction_seed", "source_graph_id", "graph_input_kind",
)

# NPZ indices are explicit; no zero-filled placeholder matrices or vectors.
NPZ_INDEX_SCHEMA = {
    "identity": "batch_uuid, contract, seed_namespace",
    "profile_order": ("control", "candidate"),
    "matrices": "constructor_profile_index + constructor_graph_index -> H_constructor",
    "deep_matrices": "deep_profile_index + deep_graph_index -> H_deep",
    "pairs": "pair_index, pair_graph_index, pair_seed, pair_stream, pair_frame, pair_truth, pair_syndrome[pair,profile,:]",
    "calls": "call_index, call_pair_index, call_profile_index, call_graph_index, call_vector_index",
    "vectors": "vector_call_index, vector_pair_index, vector_profile_index, vector_graph_index, vector_stream, vector_frame, vector_seed, raw_x_hat",
}

COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_degree_probe --execute "
    "--out-root workspace/gf32_degree_8c881d42"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def seed_for(graph_seed: int, stream: int, frame: int,
             seed_prefix: str | None = None) -> int:
    namespace = SEED_PREFIX if seed_prefix is None else str(seed_prefix)
    return int(common.v10_seed(
        f"{namespace}:holdout:{int(graph_seed)}:{int(stream)}:{int(frame)}"))


def seed_plan(seed_prefix: str | None = None) -> list[tuple[int, int, int, int]]:
    return [
        (graph_seed, stream, frame, seed_for(
            graph_seed, stream, frame, seed_prefix=seed_prefix))
        for graph_seed in GRAPH_SEEDS
        for stream in HOLDOUT_STREAMS
        for frame in range(HOLDOUT_FRAMES_PER_STREAM)
    ]


def arm_order(frame: int) -> tuple[str, str]:
    return ("control", "candidate") if int(frame) % 2 == 0 \
        else ("candidate", "control")


def _validate_seed_plan(
        seed_prefix: str | None = None,
        seed_rows: Sequence[Sequence[int]] | None = None,
        ) -> list[tuple[int, int, int, int]]:
    namespace = SEED_PREFIX if seed_prefix is None else str(seed_prefix)
    expected_plan = seed_plan(namespace)
    plan = (expected_plan if seed_rows is None else
            [tuple(int(value) for value in row) for row in seed_rows])
    keys = [(row[0], row[1], row[2]) for row in plan]
    seeds = [row[3] for row in plan]
    previous = {int(row[3]) for row in base_runner._validate_seed_plan()}
    if namespace != "gf32-degree-v1":
        previous.update(int(row[3]) for row in seed_plan("gf32-degree-v1"))
    if (seed_rows is not None and plan != expected_plan
            or seed_prefix is None and SEED_PREFIX != "gf32-degree-v1"
            or len(plan) != HOLDOUT_PAIRS
            or len(set(keys)) != HOLDOUT_PAIRS
            or len(set(seeds)) != HOLDOUT_PAIRS
            or set(seeds) & previous):
        raise AssertionError("degree-profile seeds must match the namespace plan, be unique, and prior-disjoint")
    return plan


def profile_preflight(
        profile: Mapping[str, Any], graph: Mapping[str, Any], graph_seed: int
        ) -> tuple[bool, dict[str, Any]]:
    """Check the actual D10 structure against the selected degree profile."""
    h = np.asarray(graph.get("H"))
    structure = graph.get("structure")
    var_hist = {int(d): int(c) for d, c in profile["variable_counts"].items()}
    check_hist = {int(d): int(c) for d, c in profile["check_counts"].items()}
    actual_var = ({int(d): int(c) for d, c in
                   zip(*np.unique(np.count_nonzero(h != 0, axis=0), return_counts=True))
                   if int(d) > 0} if h.ndim == 2 else {})
    actual_check = ({int(d): int(c) for d, c in
                     zip(*np.unique(np.count_nonzero(h != 0, axis=1), return_counts=True))
                     if int(d) > 0} if h.ndim == 2 else {})
    coeffs = graph.get("coefficients", ())
    admission = structure.get("admission", {}) if isinstance(structure, Mapping) else {}
    checks = {
        "profile_id": graph.get("profile_id") == profile["profile_id"],
        "graph_seed": int(graph.get("graph_seed", -1)) == int(graph_seed),
        "dimensions": h.shape == (int(profile["m"]), int(profile["n"])),
        "gf32_symbols": h.ndim == 2 and np.issubdtype(h.dtype, np.integer)
        and not np.any(h < 0) and not np.any(h >= 32),
        "n": int(profile["n"]) == N,
        "m": int(profile["m"]) == M,
        "edge_count": h.ndim == 2
        and int(np.count_nonzero(h)) == int(profile["edge_count"])
        and int(graph.get("E", -1)) == int(profile["edge_count"])
        and isinstance(structure, Mapping)
        and int(structure.get("E", -1)) == int(profile["edge_count"]),
        "variable_histogram": actual_var == var_hist,
        "check_histogram": actual_check == check_hist,
        "connected_components": isinstance(structure, Mapping)
        and int(structure.get("connected_components", -1)) == 1,
        "gf32_rank": isinstance(structure, Mapping)
        and int(structure.get("gf32_rank", -1)) == M,
        "nonzero_coefficients": len(coeffs) == int(profile["edge_count"])
        and all(1 <= int(value) < 32 for value in coeffs),
        "constructor_admitted": graph.get("status") == "ok"
        and graph.get("admitted") is True
        and isinstance(structure, Mapping)
        and structure.get("admitted") is True
        and set(admission) == {
            "A1_exact_degrees_socket_balance", "A2_simple_graph_min_degree",
            "A3_single_component", "A4_structural_rank_m", "A5_gf32_rank_m",
        }
        and all(admission.values()),
    }
    return all(checks.values()), {"profile_id": profile["profile_id"],
                                  "graph_seed": int(graph_seed),
                                  "checks": checks}


def verify_t0(seed_prefix: str | None = None,
              seed_rows: Sequence[Sequence[int]] | None = None
              ) -> dict[str, bool]:
    """Pure constants, PMF, seed and edge-proxy checks; constructs no graph."""
    expected = np.zeros(32, dtype=np.float64)
    expected[0] = P0
    for symbol, count in SHAPE_COUNTS:
        expected[int(symbol)] = (1.0 - P0) * int(count) / SHAPE_TOTAL
    actual = np.asarray(search_runner.shape_pmf_grid()[0]["pmf"], dtype=np.float64)
    checks = base_runner.verify_t0()
    if (not np.allclose(actual, expected, rtol=0.0, atol=1e-15)
            or (N, M, SYNDROME_BITS) != (128, 52, 260)
            or PROFILE_ORDER != ("control", "candidate")
            or sum(2 * c for c in PROFILES["control"]["variable_counts"].values()) != 256
            or sum(3 * c for c in PROFILES["candidate"]["variable_counts"].values()) != 384
            or 192 * 90 * (256 + 384) != EDGE_UPDATE_PROXY_CAP
            or EDGE_UPDATE_PROXY_CAP != 11_059_200):
        raise AssertionError("frozen degree-profile inputs or edge proxy changed")
    _validate_seed_plan(seed_prefix=seed_prefix, seed_rows=seed_rows)
    checks.update({"degree_profiles_fixed": True,
                   "degree_pmf_exact": True,
                   "degree_seed_plan_disjoint": True,
                   "edge_update_proxy_cap": True})
    return checks


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None,
                      out_root_relative: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() \
        else (root / requested).resolve()
    relative_root = (OUT_ROOT_RELATIVE if out_root_relative is None
                     else Path(out_root_relative))
    expected = (root / relative_root).resolve()
    if resolved != expected:
        raise ValueError(f"out-root must equal frozen fresh root {expected}")
    if resolved.exists():
        raise FileExistsError(f"refusing existing output root {resolved}")
    return resolved


def dry_run(out_root: str | Path,
            repo_root: str | Path | None = None,
            *, batch_uuid: str | None = None, contract_id: str | None = None,
            seed_prefix: str | None = None,
            seed_rows: Sequence[Sequence[int]] | None = None,
            out_root_relative: str | Path | None = None,
            graph_input_kind: str = "constructed") -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root,
                             out_root_relative=out_root_relative)
    plan = _validate_seed_plan(seed_prefix=seed_prefix, seed_rows=seed_rows)
    t0 = verify_t0(seed_prefix=seed_prefix, seed_rows=plan)
    result = {
        "status": "DRY_RUN", "out_root": str(root), "t0": t0,
        "writes": 0, "artifact_reads": 0, "graph_build_calls": 0,
        "label_calls": 0, "decoder_calls": 0,
        "holdout_pairs": len(plan), "maximum_decoder_calls": MAX_CALLS,
        "edge_update_proxy_cap": EDGE_UPDATE_PROXY_CAP,
        "profile_order": list(PROFILE_ORDER),
    }
    if any(value is not None for value in
           (batch_uuid, contract_id, seed_prefix, out_root_relative)):
        result.update({
            "batch_uuid": BATCH_UUID if batch_uuid is None else str(batch_uuid),
            "contract": CONTRACT if contract_id is None else str(contract_id),
            "seed_namespace": SEED_PREFIX if seed_prefix is None else str(seed_prefix),
            "graph_input_kind": graph_input_kind,
        })
    return result


def _candidate_preflight(onepass: Any, deep: Any,
                         diagnostics: Mapping[str, Any]
                         ) -> tuple[bool, dict[str, bool]]:
    one = np.asarray(onepass) if onepass is not None else np.empty((0, 0))
    final = np.asarray(deep) if deep is not None else np.empty((0, 0))
    checks = {
        "construction_stop_false": diagnostics.get("construction_stop") is False,
        "candidate_admitted": diagnostics.get("candidate_admitted") is True,
        "deep_candidate_admitted": diagnostics.get("deep_candidate_admitted") is True,
        "onepass_present_and_shaped": one.shape == (M, N),
        "deep_present_and_shaped": final.shape == (M, N),
        "deep_baseline_rank": diagnostics.get("deep_baseline_rank") == M,
        "deep_candidate_rank": diagnostics.get("deep_candidate_rank") == M,
        "deep_support_equal": diagnostics.get("deep_support_equal") is True,
        "deep_degrees_equal": diagnostics.get("deep_degrees_equal") is True,
        "deep_gauge_equal": diagnostics.get("deep_gauge_equal") is True,
    }
    return all(checks.values()), checks


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot write {type(value).__name__} to JSON")


def _write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, default=_json_default)
        stream.write("\n")


def _start_outputs(root: Path, manifest: dict[str, Any],
                   *, frame_fields: Sequence[str] | None = None,
                   batch_uuid: str | None = None,
                   contract_id: str | None = None,
                   seed_prefix: str | None = None) -> None:
    fields = FRAME_FIELDS if frame_fields is None else frame_fields
    run_uuid = BATCH_UUID if batch_uuid is None else str(batch_uuid)
    run_contract = CONTRACT if contract_id is None else str(contract_id)
    run_prefix = SEED_PREFIX if seed_prefix is None else str(seed_prefix)
    root.mkdir(parents=True)
    _write_json(root / "manifest.json", manifest)
    with (root / "frame_records.csv").open(
            "w", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=fields).writeheader()
    _write_json(root / "summary.json", {
        "terminal_status": "RUNNING",
        "batch_uuid": run_uuid, "contract": run_contract,
        "seed_namespace": run_prefix,
    })
    with (root / "EXPLORATION_LOG.md").open("w", encoding="utf-8") as stream:
        stream.write("# GF32 matched degree-profile EXPLORE log\n\n")
        stream.write(
            f"Batch UUID: `{run_uuid}`. Contract: `{run_contract}`. "
            f"Seed namespace: `{run_prefix}`. Independent review: pending.\n")


def _append_row(root: Path, row: Mapping[str, Any],
                fieldnames: Sequence[str] = FRAME_FIELDS) -> None:
    with (root / "frame_records.csv").open(
            "a", encoding="utf-8", newline="") as stream:
        csv.DictWriter(stream, fieldnames=fieldnames).writerow(row)


def _append_log(root: Path, text: str) -> None:
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as stream:
        stream.write(text.rstrip() + "\n")


def _diagnostics_arrays(
        constructor_matrices: Mapping[tuple[str, int], np.ndarray],
        deep_matrices: Mapping[tuple[str, int], np.ndarray],
        pairs: Sequence[Mapping[str, Any]],
        rows: Sequence[Mapping[str, Any]],
        vectors: Sequence[Mapping[str, Any]],
        *, batch_uuid: str | None = None, contract_id: str | None = None,
        seed_prefix: str | None = None,
        graph_input_kind: str = "constructed",
        source_provenance: Mapping[tuple[str, int], Mapping[str, Any]] | None = None,
        ) -> dict[str, np.ndarray]:
    run_uuid = BATCH_UUID if batch_uuid is None else str(batch_uuid)
    run_contract = CONTRACT if contract_id is None else str(contract_id)
    run_prefix = SEED_PREFIX if seed_prefix is None else str(seed_prefix)
    graph_index = {seed: index for index, seed in enumerate(GRAPH_SEEDS)}
    profile_index = {name: index for index, name in enumerate(PROFILE_ORDER)}
    constructor_keys = [(name, seed) for name in PROFILE_ORDER
                        for seed in GRAPH_SEEDS
                        if (name, seed) in constructor_matrices]
    deep_keys = [(name, seed) for name in PROFILE_ORDER
                 for seed in GRAPH_SEEDS if (name, seed) in deep_matrices]
    vector_by_call = {int(vector["call_index"]): index
                      for index, vector in enumerate(vectors)}
    arrays = {
        "batch_uuid": np.asarray([run_uuid], dtype="<U36"),
        "contract": np.asarray(
            [run_contract], dtype=f"<U{max(len(run_contract), 96)}"),
        "seed_namespace": np.asarray(
            [run_prefix], dtype=f"<U{max(len(run_prefix), 40)}"),
        "profile_order": np.asarray(PROFILE_ORDER, dtype="<U9"),
        "graph_seed": np.asarray(GRAPH_SEEDS, dtype=np.int64),
        "constructor_profile_index": np.asarray(
            [profile_index[name] for name, _ in constructor_keys], dtype=np.int64),
        "constructor_graph_index": np.asarray(
            [graph_index[seed] for _, seed in constructor_keys], dtype=np.int64),
        "H_constructor": np.stack([
            constructor_matrices[key] for key in constructor_keys]).astype(
                np.int64, copy=False) if constructor_keys
            else np.empty((0, M, N), dtype=np.int64),
        "deep_profile_index": np.asarray(
            [profile_index[name] for name, _ in deep_keys], dtype=np.int64),
        "deep_graph_index": np.asarray(
            [graph_index[seed] for _, seed in deep_keys], dtype=np.int64),
        "H_deep": np.stack([deep_matrices[key] for key in deep_keys]).astype(
            np.int64, copy=False) if deep_keys
            else np.empty((0, M, N), dtype=np.int64),
        "pair_index": np.asarray([p["pair_index"] for p in pairs], dtype=np.int64),
        "pair_graph_index": np.asarray(
            [graph_index[int(p["graph_seed"])] for p in pairs], dtype=np.int64),
        "pair_graph_seed": np.asarray(
            [p["graph_seed"] for p in pairs], dtype=np.int64),
        "pair_stream": np.asarray([p["stream"] for p in pairs], dtype=np.int64),
        "pair_frame": np.asarray([p["frame"] for p in pairs], dtype=np.int64),
        "pair_seed": np.asarray([p["seed"] for p in pairs], dtype=np.int64),
        "pair_truth": np.stack([p["truth"] for p in pairs]).astype(
            np.uint8, copy=False) if pairs else np.empty((0, N), dtype=np.uint8),
        "pair_syndrome": np.stack([p["syndrome"] for p in pairs]).astype(
            np.uint8, copy=False) if pairs
            else np.empty((0, len(PROFILE_ORDER), M), dtype=np.uint8),
        "call_index": np.asarray([r["call_index"] for r in rows], dtype=np.int64),
        "call_pair_index": np.asarray([r["pair_index"] for r in rows], dtype=np.int64),
        "call_profile_index": np.asarray(
            [profile_index[str(r["profile_id"])] for r in rows], dtype=np.int64),
        "call_graph_index": np.asarray(
            [graph_index[int(r["graph_seed"])] for r in rows], dtype=np.int64),
        "call_vector_index": np.asarray([
            vector_by_call.get(int(r["call_index"]), -1) for r in rows], dtype=np.int64),
        "vector_call_index": np.asarray(
            [v["call_index"] for v in vectors], dtype=np.int64),
        "vector_pair_index": np.asarray(
            [v["pair_index"] for v in vectors], dtype=np.int64),
        "vector_profile_index": np.asarray(
            [profile_index[str(v["profile_id"])] for v in vectors], dtype=np.int64),
        "vector_graph_index": np.asarray(
            [graph_index[int(v["graph_seed"])] for v in vectors], dtype=np.int64),
        "vector_stream": np.asarray([v["stream"] for v in vectors], dtype=np.int64),
        "vector_frame": np.asarray([v["frame"] for v in vectors], dtype=np.int64),
        "vector_seed": np.asarray([v["seed"] for v in vectors], dtype=np.int64),
        "raw_x_hat": np.stack([v["raw_x_hat"] for v in vectors]).astype(
            np.uint8, copy=False) if vectors else np.empty((0, N), dtype=np.uint8),
    }
    if graph_input_kind == "admitted_source":
        provenance = source_provenance or {}
        source_rows = [provenance[(name, seed)] for name, seed in constructor_keys]
        arrays.update({
            "graph_input_kind": np.asarray([graph_input_kind], dtype="<U32"),
            "constructor_source_uuid": np.asarray(
                [row["source_uuid"] for row in source_rows], dtype="<U36"),
            "constructor_source_path": np.asarray(
                [row["source_path"] for row in source_rows], dtype="<U160"),
            "constructor_source_matrix_index": np.asarray(
                [row["source_matrix_index"] for row in source_rows], dtype=np.int64),
            "constructor_source_attempt_j": np.asarray(
                [row["source_attempt_j"] for row in source_rows], dtype=np.int64),
            "constructor_source_seed": np.asarray(
                [row["source_construction_seed"] for row in source_rows], dtype=np.int64),
            "constructor_source_graph_id": np.asarray(
                [row["source_graph_id"] for row in source_rows], dtype=np.int64),
        })
    return arrays


def _write_diagnostics(root: Path, arrays: Mapping[str, np.ndarray]
                       ) -> tuple[int, int]:
    payload = sum(int(array.nbytes) for array in arrays.values())
    if payload > ARTIFACT_LIMIT_BYTES:
        raise ValueError("diagnostics.npz payload exceeds the frozen 20 MiB cap")
    path = root / "diagnostics.npz"
    np.savez_compressed(path, **arrays)
    size = int(path.stat().st_size)
    if size > ARTIFACT_LIMIT_BYTES:
        raise ValueError("diagnostics.npz exceeds the frozen 20 MiB cap")
    return size, payload


def execute_batch(
        *, out_root: str | Path,
        decode_fns: Mapping[str, Callable[[np.ndarray, np.ndarray, np.ndarray], Any]],
        graph_builder: Callable[[Mapping[str, Any], int], Mapping[str, Any]],
        candidate_builder: Callable[
            [np.ndarray, np.ndarray, int],
            tuple[np.ndarray | None, np.ndarray | None, Mapping[str, Any]]],
        profile_preflight_fn: Callable[
            [Mapping[str, Any], Mapping[str, Any], int],
            tuple[bool, Mapping[str, Any]]],
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str = COMMAND,
        batch_uuid: str | None = None,
        contract_id: str | None = None,
        seed_prefix: str | None = None,
        seed_rows: Sequence[Sequence[int]] | None = None,
        out_root_relative: str | Path | None = None,
        graph_input_kind: str = "constructed",
        ) -> dict[str, Any]:
    """Run one fixed matched-profile batch through explicit fake seams."""
    if (not isinstance(decode_fns, Mapping)
            or set(decode_fns) != set(PROFILE_ORDER)
            or any(not callable(decode_fns[name]) for name in PROFILE_ORDER)):
        raise ValueError("explicit control and candidate decoders are required")
    if not all(callable(fn) for fn in
               (graph_builder, candidate_builder, profile_preflight_fn)):
        raise ValueError("explicit graph, candidate and profile-preflight callbacks are required")
    run_uuid = BATCH_UUID if batch_uuid is None else str(batch_uuid)
    run_contract = CONTRACT if contract_id is None else str(contract_id)
    run_prefix = SEED_PREFIX if seed_prefix is None else str(seed_prefix)
    run_root_relative = (OUT_ROOT_RELATIVE if out_root_relative is None
                         else Path(out_root_relative))
    if graph_input_kind not in {"constructed", "admitted_source"}:
        raise ValueError("graph_input_kind must be constructed or admitted_source")
    root = validate_out_root(out_root, repo_root=repo_root,
                             out_root_relative=run_root_relative)
    planned_seed_rows = _validate_seed_plan(
        seed_prefix=seed_prefix, seed_rows=seed_rows)
    verify_t0(seed_prefix=seed_prefix, seed_rows=planned_seed_rows)
    if rss_fn is None:
        rss_fn = d5._rss_bytes

    started = float(now())
    resource_markers: list[str] = []
    rss_samples: list[int] = []
    integrity_violations = 0
    stop_reason = ""
    terminal = "INCOMPLETE"
    calls = 0
    rows: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    vectors: list[dict[str, Any]] = []
    constructor_matrices: dict[tuple[str, int], np.ndarray] = {}
    source_provenance: dict[tuple[str, int], dict[str, Any]] = {}
    deep_matrices: dict[tuple[str, int], np.ndarray] = {}
    graph_diagnostics: list[dict[str, Any]] = []
    candidate_diagnostics: list[dict[str, Any]] = []
    profile_costs = {name: {"graph_build_wall_s": 0.0,
                            "label_search_wall_s": 0.0,
                            "graphs_built": 0, "graphs_admitted": 0,
                            "deep_candidates_admitted": 0}
                     for name in PROFILE_ORDER}
    if graph_input_kind == "admitted_source":
        for costs in profile_costs.values():
            costs.update({"graph_load_wall_s": 0.0, "graphs_loaded": 0})
    pmf = np.asarray(search_runner.shape_pmf_grid()[0]["pmf"], dtype=np.float64)
    frame_fields = (FRAME_FIELDS + SOURCE_FRAME_FIELDS
                    if graph_input_kind == "admitted_source" else FRAME_FIELDS)
    manifest = {
        "track": "EXPLORE", "batch_uuid": run_uuid, "contract": run_contract,
        "status": "RUNNING", "profile_order": list(PROFILE_ORDER),
        "profiles": [dict(PROFILES[name]) for name in PROFILE_ORDER],
        "graph_seeds": list(GRAPH_SEEDS), "seed_namespace": run_prefix,
        "seed_plan_counts": {"holdout_pairs": HOLDOUT_PAIRS},
        "source_shape_proxy": {"p0": P0,
            "counts": {str(e): c for e, c in SHAPE_COUNTS},
            "total": SHAPE_TOTAL, "role": "synthetic iid marginal proxy"},
        "decoder_profile": "v35 layered FFT-QSPA; max_iter=90; alpha=1; warm_start=None; field=None",
        "pairing": "shared truth/prior, own syndrome from each admitted deep H",
        "arm_order": "control first on even frame; candidate first on odd frame",
        "budgets": {"max_decoder_calls": MAX_CALLS,
                    "total_wall_s": WALL_CAP_S,
                    "per_call_s_after_return": CALL_CAP_S,
                    "sampled_rss_bytes": RSS_CAP_BYTES,
                    "diagnostics_bytes": ARTIFACT_LIMIT_BYTES},
        "edge_update_proxy_cap": EDGE_UPDATE_PROXY_CAP,
        "accounting": {"syndrome_bits_per_attempted_call": SYNDROME_BITS,
                       "tag_bits": 0, "verification": "NOT_IMPLEMENTED",
                       "undetected": "NOT_MEASURED",
                       "success": "raw vector equals truth and passes its arm syndrome"},
        "exact_command": command,
        "attempted_decoder_calls": 0,
        "graph_diagnostics": [], "candidate_diagnostics": [],
        "profile_costs": profile_costs,
    }
    if graph_input_kind != "constructed":
        manifest["graph_input_kind"] = graph_input_kind

    def write_outputs() -> dict[str, Any]:
        nonlocal terminal, stop_reason
        arrays = _diagnostics_arrays(
            constructor_matrices, deep_matrices, pairs, rows, vectors,
            batch_uuid=run_uuid, contract_id=run_contract,
            seed_prefix=run_prefix, graph_input_kind=graph_input_kind,
            source_provenance=source_provenance)
        try:
            npz_bytes, npz_payload = _write_diagnostics(root, arrays)
        except ValueError as exc:
            add_resource_stop(f"diagnostics_cap:{exc}")
            npz_bytes, npz_payload = None, sum(
                int(array.nbytes) for array in arrays.values())
        _sample_rss()
        if not stop_reason and float(now()) - started >= WALL_CAP_S:
            add_resource_stop("total_wall_cap_after_artifacts")
        summary = base_runner._summarize(
            rows, expected_pairs=HOLDOUT_PAIRS,
            terminal_status=terminal,
            stop_reason=stop_reason or None,
            resource_stop_markers=resource_markers,
            integrity_violations=integrity_violations,
            authorization_violations=0)
        attempted_proxy = {
            name: int(PROFILES[name]["edge_count"] * sum(
                int(row.get("iterations") or 0) for row in rows
                if row.get("profile_id") == name))
            for name in PROFILE_ORDER
        }
        summary.update({
            "batch_uuid": run_uuid, "contract": run_contract,
            "seed_namespace": run_prefix,
            "terminal_status": terminal, "stop_reason": stop_reason or None,
            "profile_order": list(PROFILE_ORDER),
            "profiles": [dict(PROFILES[name]) for name in PROFILE_ORDER],
            "profile_costs": profile_costs,
            "attempted_decoder_calls": calls,
            "attempted_frame_rows": len(rows),
            "batch_wall_s": max(float(now()) - started, 0.0),
            "sampled_rss_max_bytes": max(rss_samples, default=None),
            "sampled_rss_count": len(rss_samples),
            "npz_bytes": npz_bytes, "npz_payload_bytes": npz_payload,
            "attempted_edge_update_proxy": attempted_proxy,
            "edge_update_proxy": ({
                name: int(PROFILES[name]["edge_count"]
                          * summary["per_arm_outcomes"][name]["iterations_sum"])
                for name in PROFILE_ORDER
            } if summary.get("complete") else None),
            "edge_update_proxy_is_measured_operations": False,
            "disclosed_syndrome_bits": calls * SYNDROME_BITS,
            "tag_bits": 0, "verification": "NOT_IMPLEMENTED",
            "undetected": "NOT_MEASURED",
        })
        if graph_input_kind != "constructed":
            summary["graph_input_kind"] = graph_input_kind
            summary["source_provenance"] = [
                {"profile_id": profile_id, "graph_seed": graph_seed,
                 **source_provenance[(profile_id, graph_seed)]}
                for profile_id in PROFILE_ORDER for graph_seed in GRAPH_SEEDS
                if (profile_id, graph_seed) in source_provenance]
        manifest.update({
            "status": terminal, "attempted_decoder_calls": calls,
            "attempted_pairs": len(pairs), "stop_reason": stop_reason,
            "batch_wall_s": summary["batch_wall_s"],
            "resource_stop_markers": list(resource_markers),
            "integrity_violations": integrity_violations,
            "sampled_rss_max_bytes": summary["sampled_rss_max_bytes"],
            "sampled_rss_count": len(rss_samples),
            "npz_bytes": npz_bytes, "npz_payload_bytes": npz_payload,
            "graph_diagnostics": graph_diagnostics,
            "candidate_diagnostics": candidate_diagnostics,
            "profile_costs": profile_costs,
        })
        if graph_input_kind != "constructed":
            manifest["graph_input_kind"] = graph_input_kind
            manifest["source_provenance"] = summary["source_provenance"]
        _write_json(root / "summary.json", summary)
        _write_json(root / "manifest.json", manifest)
        _append_log(root, (
            f"terminal={terminal} classification={summary['classification']} "
            f"calls={calls} pairs={len(pairs)} stop_reason={stop_reason or 'none'}"))
        return summary

    def add_resource_stop(reason: str) -> None:
        nonlocal stop_reason, terminal
        if reason not in resource_markers:
            resource_markers.append(reason)
        if not stop_reason:
            stop_reason = reason
        terminal = "STOP"

    def add_integrity_stop(reason: str) -> None:
        nonlocal stop_reason, terminal, integrity_violations
        if not stop_reason:
            stop_reason = reason
        terminal = "STOP"
        integrity_violations += 1

    def _sample_rss() -> int | None:
        try:
            value = rss_fn()
        except Exception as exc:
            reason = f"rss_monitor_exception:{type(exc).__name__}:{exc}"
            if reason not in resource_markers:
                resource_markers.append(reason)
            return None
        if value is not None:
            rss_samples.append(int(value))
        return None if value is None else int(value)

    def resource_check(stage: str) -> str:
        if max(float(now()) - started, 0.0) >= WALL_CAP_S:
            reason = f"total_wall_cap_{stage}"
            add_resource_stop(reason)
            return reason
        before = len(resource_markers)
        rss = _sample_rss()
        if len(resource_markers) != before:
            reason = resource_markers[-1]
            add_resource_stop(reason)
            return reason
        if rss is not None and rss >= RSS_CAP_BYTES:
            reason = f"rss_cap_{stage}:{rss}"
            add_resource_stop(reason)
            return reason
        return ""

    def build_start() -> None:
        _start_outputs(root, manifest, frame_fields=frame_fields,
                       batch_uuid=run_uuid, contract_id=run_contract,
                       seed_prefix=run_prefix)
        reason = resource_check("after_initial_write")
        if reason:
            raise StopBatch(reason)

    class StopBatch(Exception):
        pass

    try:
        build_start()
        graph_failed = False
        # Build both profile matrices for each fixed seed before deciding whether
        # construction admission permits label search or any BP call.
        for graph_seed in GRAPH_SEEDS:
            this_seed_failed = False
            for profile_id in PROFILE_ORDER:
                reason = resource_check("before_graph_build")
                if reason:
                    raise StopBatch(reason)
                profile = PROFILES[profile_id]
                before = float(now())
                try:
                    graph = graph_builder(profile, graph_seed)
                except Exception as exc:
                    elapsed = max(float(now()) - before, 0.0)
                    if graph_input_kind == "admitted_source":
                        profile_costs[profile_id]["graph_load_wall_s"] += elapsed
                    else:
                        profile_costs[profile_id]["graph_build_wall_s"] += elapsed
                    graph_diagnostics.append({
                        "profile_id": profile_id, "graph_seed": graph_seed,
                        "status": "construction_exception",
                        "failure_reason": f"{type(exc).__name__}:{exc}",
                        "wall_s": elapsed,
                    })
                    this_seed_failed = True
                    continue
                elapsed = max(float(now()) - before, 0.0)
                if graph_input_kind == "admitted_source":
                    profile_costs[profile_id]["graph_load_wall_s"] += elapsed
                    profile_costs[profile_id]["graphs_loaded"] += int(
                        graph.get("H") is not None)
                else:
                    profile_costs[profile_id]["graph_build_wall_s"] += elapsed
                    profile_costs[profile_id]["graphs_built"] += int(
                        graph.get("H") is not None)
                h = graph.get("H")
                try:
                    admitted, preflight = profile_preflight_fn(
                        profile, graph, graph_seed)
                except Exception as exc:
                    admitted = False
                    preflight = {"error": f"{type(exc).__name__}:{exc}"}
                source_values: dict[str, Any] = {}
                source_valid = True
                if graph_input_kind == "admitted_source":
                    source_values = {
                        "source_uuid": graph.get("source_uuid"),
                        "source_path": graph.get("source_path"),
                        "source_matrix_index": graph.get("source_matrix_index"),
                        "source_attempt_j": graph.get("source_attempt_j"),
                        "source_construction_seed": graph.get("source_construction_seed"),
                        "source_graph_id": graph.get("source_graph_id"),
                    }
                    source_valid = (
                        isinstance(source_values["source_uuid"], str)
                        and bool(source_values["source_uuid"])
                        and isinstance(source_values["source_path"], str)
                        and bool(source_values["source_path"])
                        and all(isinstance(source_values[name], (int, np.integer))
                                and not isinstance(source_values[name], (bool, np.bool_))
                                for name in ("source_matrix_index", "source_attempt_j",
                                             "source_construction_seed", "source_graph_id"))
                        and int(source_values["source_matrix_index"]) >= 0
                        and int(source_values["source_attempt_j"]) >= 0
                        and int(source_values["source_graph_id"]) == graph_seed)
                    if not source_valid:
                        admitted = False
                        preflight = dict(preflight) if isinstance(preflight, Mapping) else {}
                        preflight["source_provenance_valid"] = False
                    else:
                        source_provenance[(profile_id, graph_seed)] = source_values
                if h is not None and (source_valid or graph_input_kind == "constructed"):
                    matrix = np.asarray(h, dtype=np.uint8)
                    if matrix.shape == (M, N):
                        constructor_matrices[(profile_id, graph_seed)] = matrix.copy()
                graph_entry = {
                    "profile_id": profile_id, "graph_seed": graph_seed,
                    "status": graph.get("status"),
                    "admitted": bool(admitted),
                    "failure_reason": graph.get("failure_reason", ""),
                    "structure": graph.get("structure"),
                    "preflight": preflight, "wall_s": elapsed,
                }
                if graph_input_kind == "admitted_source":
                    graph_entry.update(source_values)
                    graph_entry.update({
                        "edges": graph.get("edges"),
                        "coefficients": graph.get("coefficients"),
                        "source_preflight": graph.get("source_preflight"),
                    })
                    if not source_valid:
                        graph_entry["failure_reason"] = "source provenance missing or invalid"
                graph_diagnostics.append(graph_entry)
                if admitted:
                    profile_costs[profile_id]["graphs_admitted"] += 1
                else:
                    this_seed_failed = True
                reason = resource_check("after_graph_build")
                if reason:
                    raise StopBatch(reason)
            if this_seed_failed:
                graph_failed = True
                if not stop_reason:
                    add_integrity_stop(
                        f"profile_construction_or_admission_stop:{graph_seed}")
                break
        if graph_failed or stop_reason:
            raise StopBatch(stop_reason or "profile_construction_or_admission_stop")

        pmf = np.asarray(search_runner.shape_pmf_grid()[0]["pmf"], dtype=np.float64)
        for graph_seed in GRAPH_SEEDS:
            for profile_id in PROFILE_ORDER:
                reason = resource_check("before_label_search")
                if reason:
                    raise StopBatch(reason)
                profile = PROFILES[profile_id]
                base_h = constructor_matrices[(profile_id, graph_seed)]
                before = float(now())
                try:
                    onepass, deep, diagnostics = candidate_builder(
                        base_h, pmf, graph_seed)
                except Exception as exc:
                    elapsed = max(float(now()) - before, 0.0)
                    profile_costs[profile_id]["label_search_wall_s"] += elapsed
                    candidate_diagnostics.append({
                        "profile_id": profile_id, "graph_seed": graph_seed,
                        "status": "label_exception",
                        "failure_reason": f"{type(exc).__name__}:{exc}",
                        "wall_s": elapsed,
                    })
                    add_integrity_stop(
                        f"label_search_exception:{profile_id}:{graph_seed}:{type(exc).__name__}")
                    raise StopBatch(stop_reason)
                elapsed = max(float(now()) - before, 0.0)
                profile_costs[profile_id]["label_search_wall_s"] += elapsed
                admitted, checks = _candidate_preflight(
                    onepass, deep, diagnostics)
                candidate_diagnostics.append({
                    "profile_id": profile_id, "graph_seed": graph_seed,
                    "admitted": admitted, "checks": checks,
                    "diagnostics": diagnostics, "wall_s": elapsed,
                })
                if deep is not None:
                    deep_matrix = np.asarray(deep, dtype=np.uint8)
                    if deep_matrix.shape == (M, N):
                        deep_matrices[(profile_id, graph_seed)] = deep_matrix.copy()
                if admitted:
                    profile_costs[profile_id]["deep_candidates_admitted"] += 1
                else:
                    add_integrity_stop(
                        f"deep_candidate_admission_stop:{profile_id}:{graph_seed}")
                    raise StopBatch(stop_reason)
                reason = resource_check("after_label_search")
                if reason:
                    raise StopBatch(reason)

        seed_to_index = {int(row[3]): index for index, row in enumerate(planned_seed_rows)}
        for pair_index, (graph_seed, stream, frame, seed) in enumerate(planned_seed_rows):
            reason = resource_check("before_pair_sample")
            if reason:
                raise StopBatch(reason)
            truth = prior_runner.sample_error(seed, pmf, width=N)
            shared_prior = np.tile(pmf, (N, 1))
            arm_data = prior_runner.paired_arm_data(
                deep_matrices[("control", graph_seed)],
                deep_matrices[("candidate", graph_seed)],
                truth, shared_prior)
            pair = {
                "pair_index": pair_index, "graph_seed": graph_seed,
                "graph_index": GRAPH_SEEDS.index(graph_seed),
                "stream": stream, "frame": frame, "seed": seed,
                "truth": np.asarray(truth, dtype=np.uint8).copy(),
                "syndrome": np.stack([
                    np.asarray(arm_data[name]["syndrome"], dtype=np.uint8)
                    for name in PROFILE_ORDER]),
            }
            pairs.append(pair)
            for arm in arm_order(frame):
                reason = resource_check("before_decoder_call")
                if reason:
                    raise StopBatch(reason)
                call_index = calls
                calls += 1
                dense = np.asarray(arm_data[arm]["dense"], dtype=np.int64).copy()
                prior = np.asarray(arm_data[arm]["prior"], dtype=np.float64).copy()
                syndrome = np.asarray(arm_data[arm]["syndrome"], dtype=np.int64).copy()
                before_inputs = (dense.copy(), prior.copy(), syndrome.copy())
                captured: dict[str, Any] = {}

                def capture(h: np.ndarray, p: np.ndarray, s: np.ndarray) -> Any:
                    result = decode_fns[arm](h, p, s)
                    captured["raw_result"] = result
                    return result

                rss_marker_start = len(resource_markers)
                observed, issue = prior_runner.decode_observation(
                    capture, dense, prior, truth, syndrome,
                    now=now, rss_fn=_sample_rss)
                call_resource_markers = resource_markers[rss_marker_start:]
                if call_resource_markers:
                    issue = ";".join(
                        x for x in (issue, call_resource_markers[0]) if x)
                raw_result = captured.get("raw_result")
                raw = base_runner._validated_raw_vector(raw_result)
                mutated = not (
                    np.array_equal(dense, before_inputs[0])
                    and np.array_equal(prior, before_inputs[1])
                    and np.array_equal(syndrome, before_inputs[2]))
                if raw is None and raw_result is not None:
                    issue = ";".join(x for x in (issue, "raw_vector_not_validated") if x)
                if mutated:
                    issue = ";".join(x for x in (issue, "decoder_input_mutation") if x)
                iterations = observed.get("iterations", 0)
                raw_iterations = getattr(raw_result, "iterations", None)
                valid_iterations = (
                    isinstance(raw_iterations, (int, np.integer))
                    and not isinstance(raw_iterations, (bool, np.bool_))
                    and 0 <= int(raw_iterations) <= MAX_ITER
                    and int(iterations) == int(raw_iterations))
                if raw is not None and not valid_iterations:
                    issue = ";".join(x for x in (issue, "iteration_count_integrity") if x)
                syndrome_ok: bool | None = None
                exact_raw: bool | None = None
                wrong: bool | None = None
                exact: bool | None = None
                if raw is not None:
                    exact_raw = bool(np.array_equal(raw, truth))
                    syndrome_ok = bool(layout.syndrome_ok(dense, raw, syndrome))
                    wrong = bool(syndrome_ok and not exact_raw)
                    exact = bool(exact_raw and syndrome_ok)
                    if syndrome_ok != bool(observed.get("syndrome_accept")):
                        issue = ";".join(x for x in (issue, "decoder_syndrome_flag_mismatch") if x)
                    if not syndrome_ok and valid_iterations and int(iterations) != MAX_ITER:
                        issue = ";".join(x for x in (issue, "raw_failure_not_at_cap") if x)
                row_status = str(observed.get("status", "observation_error"))
                if raw is None and raw_result is not None:
                    row_status = "integrity_error"
                if "decoder_input_mutation" in issue or "integrity" in issue or "mismatch" in issue:
                    row_status = "integrity_error"
                if row_status == "resource_abort" or any(
                        marker.startswith("rss_monitor_exception")
                        for marker in resource_markers):
                    row_status = "resource_abort"
                if row_status == "resource_abort" and not issue:
                    issue = next((marker for marker in call_resource_markers
                                  if marker.startswith("rss_monitor_exception")),
                                 "decoder_resource_abort")
                row = {
                    "call_index": call_index, "pair_index": pair_index,
                    "graph_seed": graph_seed, "stream": stream,
                    "frame": frame, "seed": seed, "arm": arm,
                    "profile_id": arm,
                    "decoder_status": (None if raw_result is None else
                                       str(getattr(raw_result, "status", ""))),
                    "status": row_status,
                    "iterations": int(iterations) if str(iterations).lstrip("-").isdigit() else 0,
                    "raw_vector_saved": raw is not None,
                    "raw_symbols_equal": exact_raw,
                    "syndrome_accept": syndrome_ok,
                    "base_syndrome_accept": syndrome_ok,
                    "syndrome_consistent_wrong": wrong,
                    "exact": exact, "wall_s": observed.get("wall_s"),
                    "rss_b": observed.get("rss_b"),
                    "syndrome_bits": SYNDROME_BITS,
                    "failure_reason": issue,
                    "batch_uuid": run_uuid, "contract": run_contract,
                    "seed_namespace": run_prefix,
                }
                if graph_input_kind == "admitted_source":
                    row.update(source_provenance[(arm, graph_seed)])
                    row["graph_input_kind"] = graph_input_kind
                rows.append(row)
                _append_row(root, row, fieldnames=frame_fields)
                if raw is not None:
                    vectors.append({
                        "call_index": call_index, "pair_index": pair_index,
                        "profile_id": arm, "graph_seed": graph_seed,
                        "stream": stream, "frame": frame, "seed": seed,
                        "raw_x_hat": raw,
                    })
                if issue or row_status == "resource_abort":
                    if row_status == "resource_abort":
                        add_resource_stop(issue or "decoder_resource_abort")
                    else:
                        add_integrity_stop(issue)
                    raise StopBatch(stop_reason)
                reason = resource_check("after_decoder_call")
                if reason:
                    raise StopBatch(reason)
        terminal = "COMPLETE"
    except StopBatch:
        pass
    except Exception as exc:
        if not stop_reason:
            add_integrity_stop(f"operator_exception:{type(exc).__name__}:{exc}")
        _append_log(root, f"primary_error={type(exc).__name__}:{exc}")
    return write_outputs()


def _bind_production() -> dict[str, Any]:
    """Bind only the packet-fixed D10 constructor, accepted label search and decoder."""
    from comparison_bench.formal_ir import v35_algorithm_development as v35

    def graph_builder(profile: Mapping[str, Any], graph_seed: int) -> dict[str, Any]:
        construction = d10.build_degree_sequence_peg(
            int(profile["n"]), int(profile["m"]), profile["variable_counts"],
            profile["check_counts"], int(graph_seed))
        record: dict[str, Any] = {
            "profile_id": profile["profile_id"], "graph_seed": int(graph_seed),
            "n": int(profile["n"]), "m": int(profile["m"]),
            "E": 0, "edges": [], "coefficients": [], "H": None,
            "structure": None, "status": "construction_failed",
            "admitted": False,
            "failure_reason": construction.get("failure_reason", ""),
        }
        if construction.get("status") != "ok":
            return record
        edges = construction["edges"]
        coeffs = d10.coefficients_for_edges(edges, width=N,
                                            graph_seed=int(graph_seed))
        h = d10.dense_from_edges(N, M, edges, coeffs)
        structure = d10.structural_record(
            h, profile["variable_counts"], profile["check_counts"])
        record.update({
            "E": int(len(edges)), "edges": edges,
            "coefficients": coeffs, "H": h, "structure": structure,
            "status": "ok", "admitted": bool(structure["admitted"]),
            "failure_reason": "" if structure["admitted"] else "D10 structure admission failed",
        })
        return record

    def decode(h: np.ndarray, prior: np.ndarray,
               syndrome: np.ndarray) -> Any:
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=MAX_ITER,
            damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)

    return {
        "decode_fns": {"control": decode, "candidate": decode},
        "graph_builder": graph_builder,
        "candidate_builder": search_runner._candidate_pair_for_graph,
        "profile_preflight_fn": profile_preflight,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GF32 matched degree-profile EXPLORE probe")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--execute", action="store_true", help="run the frozen synthetic batch")
    modes.add_argument("--dry-run", action="store_true", help="perform pure T0 and fresh-root checks")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE))
    return parser


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    if not args.execute:
        result = dry_run(args.out_root)
        print(json.dumps(result, sort_keys=True))
        return result
    bindings = _bind_production()
    result = execute_batch(out_root=args.out_root, command=COMMAND, **bindings)
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
