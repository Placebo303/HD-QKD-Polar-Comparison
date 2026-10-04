"""Bounded fresh-frame soft-prior restart probe for fixed GF(32) deep H."""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import nonbinary_v10_common as common

BATCH_UUID = "31dca97b-808c-4205-ac01-7c5ab7b9e9b5"
CONTRACT = "NBLDPC-GF32-SOFT-PRIOR-RESCUE-20261001/PREREG_AND_AUTH.md"
SEED_NAMESPACE = "gf32-softprior-v1"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_softprior_31dca97b"
SOURCE_BATCH_UUID = "a9352bc1-ae56-443b-ae93-9dcfa85d4229"
SOURCE_CONTRACT = "NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md"
SOURCE_NAMESPACE = "gf32-degree-admitted-v1"
SOURCE_KIND = "admitted_source"
SOURCE_UUID = "a9a18abe-3547-4d16-aa50-1f7150182f31"
SOURCE_PATH = "workspace/gf32_construct_a9a18abe/constructions.json"
GRAPH_IDS = tuple(range(2026093901, 2026093907))
PROFILE_ORDER = ("control", "candidate")
N, M, Q = 128, 52, 32
P0 = 0.550
SHAPE_COUNTS = ((1, 2295), (3, 1126), (7, 557), (15, 304), (31, 146))
SHAPE_TOTAL = 4428
HOLDOUT_STREAMS = (0, 1)
HOLDOUT_FRAMES_PER_STREAM = 16
HOLDOUT_PAIRS = len(GRAPH_IDS) * len(HOLDOUT_STREAMS) * HOLDOUT_FRAMES_PER_STREAM
MAX_ITER, DAMPING_ALPHA = 90, 1.0
GUESSES = (0, 1, 3, 7, 15, 31)
MAX_PHYSICAL_CALLS = HOLDOUT_PAIRS * (1 + len(GUESSES))
WALL_CAP_S, CALL_CAP_S = 1800.0, 120.0
RSS_CAP_BYTES = 4 * 1024 ** 3
ARTIFACT_CAP_BYTES = 20 * 1024 * 1024
SYNDROME_BITS = 260
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_softprior_rescue --execute "
    "--out-root workspace/gf32_softprior_31dca97b"
)

SOURCE_ARRAY_KEYS = (
    "batch_uuid", "contract", "seed_namespace", "graph_input_kind",
    "profile_order", "graph_seed", "deep_profile_index", "deep_graph_index",
    "H_deep", "constructor_profile_index", "constructor_graph_index",
    "constructor_source_uuid", "constructor_source_path",
    "constructor_source_matrix_index", "constructor_source_attempt_j",
    "constructor_source_seed", "constructor_source_graph_id",
)

CALL_FIELDS = (
    "call_index", "pair_index", "graph_id", "graph_seed", "stream",
    "frame", "seed", "role", "branch_index", "guess_symbol",
    "selected_variable", "returned_selected_symbol", "status",
    "decoder_status", "iterations", "decoder_runtime_s", "wall_s",
    "rss_bytes", "syndrome_valid", "syndrome_ok_reported", "exact",
    "syndrome_valid_wrong", "syndrome_failed", "raw_vector_index",
    "score_original_prior", "belief_provenance",
    "candidate_selected_call_index",
    "selector_violated_check_ids", "selector_active_variable_columns",
    "selector_max_entropy_bits", "selector_entropy_bits_json",
    "failure_reason",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def pmf() -> np.ndarray:
    result = np.zeros(Q, dtype=np.float64)
    result[0] = P0
    for symbol, count in SHAPE_COUNTS:
        result[symbol] = (1.0 - P0) * count / SHAPE_TOTAL
    return result


def effective_prior(prior: Any) -> np.ndarray:
    values = np.asarray(prior, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != Q:
        raise ValueError("prior must have shape (n,32)")
    if not np.all(np.isfinite(values)) or np.any(values < 0.0):
        raise ValueError("prior must be finite and non-negative")
    values = np.maximum(values, 1e-15)
    totals = values.sum(axis=1, keepdims=True)
    if not np.all(np.isfinite(totals)) or np.any(totals <= 0.0):
        raise ValueError("prior rows must have finite positive mass")
    return values / totals


def build_seed_plan(seed_namespace: str = SEED_NAMESPACE) -> list[tuple[int, int, int, int]]:
    return [
        (graph_id, stream, frame, int(common.v10_seed(
            f"{seed_namespace}:holdout:{graph_id}:{stream}:{frame}")))
        for graph_id in GRAPH_IDS
        for stream in HOLDOUT_STREAMS
        for frame in range(HOLDOUT_FRAMES_PER_STREAM)
    ]


def _prior_seed_plans() -> list[tuple[str, Any, int]]:
    """The thirteen source-free exclusion generators frozen by S1."""
    from comparison_bench.cli import nbldpc_gf32_degree_probe as D
    from comparison_bench.cli import nbldpc_gf32_roworder_probe as R
    from comparison_bench.cli import nbldpc_gf32_mrb_rescue_probe as mr
    from comparison_bench.cli import nbldpc_gf32_mrb_top6_probe as mt
    from comparison_bench.cli import nbldpc_gf32_mrb_reachability_probe as mg

    return [
        ("R.prior_runner._seed_plan", R.prior_runner._seed_plan(), 264),
        ("R.search_runner.fine_runner.predecessor.seed_plan",
         R.search_runner.fine_runner.predecessor.seed_plan(), 288),
        ("R.search_runner.fine_runner.seed_plan",
         R.search_runner.fine_runner.seed_plan(), 360),
        ("R.search_runner.replica_runner.seed_plan",
         R.search_runner.replica_runner.seed_plan(), 192),
        ("R.search_runner.seed_plan", R.search_runner.seed_plan(), 192),
        ("R.iter_cap_runner.resource_runner.seed_plan",
         R.iter_cap_runner.resource_runner.seed_plan(), 192),
        ("R.iter_cap_runner.seed_plan", R.iter_cap_runner.seed_plan(), 192),
        ("R.seed_plan/gf32-roworder-v1", R.seed_plan(), 192),
        ("D.seed_plan/gf32-degree-v1", D.seed_plan(), 192),
        ("D.seed_plan/gf32-degree-admitted-v1",
         D.seed_plan(seed_prefix="gf32-degree-admitted-v1"), 192),
        ("MRB rescue/gf32-mrb-rescue-v1", mr.seed_plan(), 192),
        ("MRB top6/gf32-mrb-top6-v1", mt.seed_plan(), 192),
        ("MRB reachability/gf32-mrb-reachability-v1", mg._seed_plan(), 192),
    ]


def _seeds_from_plan(value: Any) -> list[int]:
    """Extract the final seed from the frozen nested (graph,stream,frame,seed) rows."""
    if isinstance(value, Mapping):
        if "seed" in value:
            return [int(value["seed"])]
        result: list[int] = []
        for item in value.values():
            result.extend(_seeds_from_plan(item))
        return result
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, (list, tuple)):
        if len(value) == 4 and all(
                isinstance(x, (int, np.integer)) and not isinstance(x, (bool, np.bool_))
                for x in value):
            return [int(value[3])]
        result = []
        for item in value:
            result.extend(_seeds_from_plan(item))
        return result
    raise ValueError("frozen seed generator returned an unsupported row structure")


def validate_seed_plan(
        plan: Sequence[Sequence[int]] | None = None, *,
        seed_namespace: str = SEED_NAMESPACE,
        additional_excluded_plans: Sequence[tuple[str, Sequence[Sequence[int]]]] = (),
        ) -> tuple[list[tuple[int, int, int, int]], list[dict[str, Any]]]:
    rows = build_seed_plan(seed_namespace) if plan is None else [
        tuple(int(value) for value in row) for row in plan]
    expected = build_seed_plan(seed_namespace)
    keys = [(row[0], row[1], row[2]) for row in rows]
    seeds = [row[3] for row in rows]
    if rows != expected or len(set(keys)) != HOLDOUT_PAIRS \
            or len(set(seeds)) != HOLDOUT_PAIRS:
        raise ValueError("new frozen seed plan is changed, incomplete, or duplicated")
    records = []
    exclusion_union: set[int] = set()
    exclusion_plans = _prior_seed_plans()
    exclusion_plans.extend(
        (name, frozen_plan, HOLDOUT_PAIRS)
        for name, frozen_plan in additional_excluded_plans)
    for name, frozen_plan, expected_rows in exclusion_plans:
        old = _seeds_from_plan(frozen_plan)
        if len(old) != expected_rows or len(set(old)) != expected_rows:
            raise ValueError(f"frozen prior seed plan changed: {name}")
        overlap = set(seeds).intersection(old)
        if overlap:
            raise ValueError(f"new seed plan overlaps {name}")
        exclusion_union.update(old)
        records.append({"generator": name, "rows": len(old), "unique_seeds": len(set(old))})
    expected_union_size = 2832 + HOLDOUT_PAIRS * len(additional_excluded_plans)
    if len(exclusion_union) != expected_union_size or set(seeds).intersection(exclusion_union):
        raise ValueError("frozen prior seed union changed or new seeds overlap it")
    return rows, records


def select_uncertain_variable(
        H: Any, x_hat: Any, final_beliefs: Any, syndrome: Any, *,
        belief_provenance: str) -> tuple[int, dict[str, Any]]:
    matrix = np.asarray(H)
    vector = np.asarray(x_hat, dtype=np.int64).ravel()
    target = np.asarray(syndrome, dtype=np.int64).ravel()
    beliefs = np.asarray(final_beliefs, dtype=np.float64)
    if belief_provenance != "CHECK_UPDATED":
        raise ValueError("baseline failure beliefs must have CHECK_UPDATED provenance")
    if (matrix.ndim != 2 or vector.shape != (matrix.shape[1],)
            or target.shape != (matrix.shape[0],)):
        raise ValueError("selector H/vector/syndrome shapes are invalid")
    if (not np.issubdtype(matrix.dtype, np.integer) or np.any(matrix < 0)
            or np.any(matrix > 31) or np.any(vector < 0) or np.any(vector >= Q)):
        raise ValueError("selector H/vector contains invalid GF(32) symbols")
    if beliefs.shape != (matrix.shape[1], Q) or not np.all(np.isfinite(beliefs)):
        raise ValueError("final_beliefs must be finite shape (n,32)")
    observed = np.asarray(layout.gf32_syndrome(matrix, vector), dtype=np.int64).ravel()
    violated = np.flatnonzero(observed != target)
    active = np.flatnonzero(np.any(matrix[violated] != 0, axis=0)) if len(violated) else np.asarray([], dtype=np.int64)
    if len(active) == 0:
        raise ValueError("baseline failure has no variables adjacent to violated checks")
    shifted = beliefs - np.max(beliefs, axis=1, keepdims=True)
    probabilities = np.exp(shifted)
    probabilities /= probabilities.sum(axis=1, keepdims=True)
    entropy = -np.sum(probabilities * np.log2(np.maximum(probabilities, 1e-300)), axis=1)
    maximum = float(np.max(entropy[active]))
    tied = [int(column) for column in active if maximum - float(entropy[column]) <= 1e-12]
    selected = min(tied)
    metadata = {
        "entropy_bits": entropy.tolist(),
        "active_variable_columns": [int(x) for x in active],
        "violated_check_ids": [int(x) for x in violated],
        "selected_column": selected,
        "max_entropy_bits": maximum,
    }
    return selected, metadata


def select_soft_prior_branch(
        valid_vectors: Sequence[Mapping[str, Any]], original_prior: Any
        ) -> tuple[int | None, list[dict[str, Any]]]:
    prior_eff = effective_prior(original_prior)
    score_rows: list[dict[str, Any]] = []
    candidates = []
    for row in valid_vectors:
        call_index = int(row["call_index"])
        branch_index = int(row["branch_index"])
        is_valid = bool(row["syndrome_valid"])
        score: float | None = None
        if is_valid:
            vector = np.asarray(row["x_hat"], dtype=np.int64).ravel()
            if vector.shape != (prior_eff.shape[0],) or np.any(vector < 0) or np.any(vector >= Q):
                raise ValueError("valid branch vector is not a GF(32) vector")
            score = float(np.log(prior_eff[np.arange(len(vector)), vector]).sum())
            candidates.append((branch_index, call_index, score))
        score_rows.append({
            "call_index": call_index, "branch_index": branch_index,
            "score": score, "syndrome_valid": is_valid,
        })
    if not candidates:
        return None, score_rows
    maximum = max(item[2] for item in candidates)
    selected = min((item for item in candidates if maximum - item[2] <= 1e-12),
                   key=lambda item: item[0])
    return int(selected[1]), score_rows


def _scalar_text(value: Any, key: str) -> str:
    array = np.asarray(value)
    if array.size != 1:
        raise ValueError(f"source {key} must be scalar")
    item = array.reshape(-1)[0]
    if isinstance(item, bytes):
        item = item.decode("utf-8")
    return str(item)


def _check_connected_support(H: np.ndarray) -> bool:
    support = H != 0
    if np.any(support.sum(axis=0) != 2):
        return False
    adjacency = [set() for _ in range(M)]
    for column in range(N):
        rows = np.flatnonzero(support[:, column])
        a, b = int(rows[0]), int(rows[1])
        adjacency[a].add(b)
        adjacency[b].add(a)
    seen, pending = {0}, [0]
    while pending:
        row = pending.pop()
        for neighbor in adjacency[row] - seen:
            seen.add(neighbor)
            pending.append(neighbor)
    return len(seen) == M


def select_sources(source: Mapping[str, Any]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    missing = [key for key in SOURCE_ARRAY_KEYS if key not in source]
    if missing:
        raise ValueError(f"source NPZ lacks required keys: {missing}")
    identity = {
        "batch_uuid": _scalar_text(source["batch_uuid"], "batch_uuid"),
        "contract": _scalar_text(source["contract"], "contract"),
        "seed_namespace": _scalar_text(source["seed_namespace"], "seed_namespace"),
        "graph_input_kind": _scalar_text(source["graph_input_kind"], "graph_input_kind"),
    }
    expected_identity = {
        "batch_uuid": SOURCE_BATCH_UUID, "contract": SOURCE_CONTRACT,
        "seed_namespace": SOURCE_NAMESPACE, "graph_input_kind": SOURCE_KIND,
    }
    if identity != expected_identity:
        raise ValueError(f"source identity mismatch: {identity}")
    profile_order = [str(x) for x in np.asarray(source["profile_order"]).tolist()]
    if tuple(profile_order) != PROFILE_ORDER:
        raise ValueError("source profile_order differs from the frozen order")
    graph_seeds = np.asarray(source["graph_seed"], dtype=np.int64).ravel()
    if len(set(int(x) for x in graph_seeds)) != len(graph_seeds) \
            or set(int(x) for x in graph_seeds) != set(GRAPH_IDS):
        raise ValueError("source graph_seed differs from the six frozen graph IDs")
    graph_index = {int(seed): index for index, seed in enumerate(graph_seeds)}

    deep_profiles = np.asarray(source["deep_profile_index"], dtype=np.int64).ravel()
    deep_graphs = np.asarray(source["deep_graph_index"], dtype=np.int64).ravel()
    deep_matrices = np.asarray(source["H_deep"])
    expected_pairs = {(p, graph_index[g]) for p in range(2) for g in GRAPH_IDS}
    deep_pairs = list(zip(deep_profiles.tolist(), deep_graphs.tolist()))
    if (deep_matrices.ndim != 3 or deep_matrices.shape[1:] != (M, N)
            or len(deep_matrices) != len(deep_pairs)
            or set(deep_pairs) != expected_pairs or len(set(deep_pairs)) != len(deep_pairs)):
        raise ValueError("source deep-H/profile/graph maps are incomplete or duplicated")
    deep_rows = {pair: i for i, pair in enumerate(deep_pairs)}

    constructor_profiles = np.asarray(source["constructor_profile_index"], dtype=np.int64).ravel()
    constructor_graphs = np.asarray(source["constructor_graph_index"], dtype=np.int64).ravel()
    constructor_pairs = list(zip(constructor_profiles.tolist(), constructor_graphs.tolist()))
    if (len(constructor_pairs) != len(expected_pairs)
            or set(constructor_pairs) != expected_pairs
            or len(set(constructor_pairs)) != len(constructor_pairs)):
        raise ValueError("source constructor lineage maps are incomplete or duplicated")
    constructor_rows = {pair: i for i, pair in enumerate(constructor_pairs)}
    lineage_keys = (
        "constructor_source_uuid", "constructor_source_path",
        "constructor_source_matrix_index", "constructor_source_attempt_j",
        "constructor_source_seed", "constructor_source_graph_id",
    )
    lineage_arrays = {key: np.asarray(source[key]).ravel() for key in lineage_keys}
    if any(len(values) != len(constructor_pairs) for values in lineage_arrays.values()):
        raise ValueError("source constructor lineage arrays are misaligned")
    expected_matrix_index = dict(zip(GRAPH_IDS, (0, 2, 4, 6, 9, 11)))

    selected = []
    for graph_id in GRAPH_IDS:
        pair = (profile_order.index("control"), graph_index[graph_id])
        deep_row = deep_rows[pair]
        constructor_row = constructor_rows[pair]
        matrix = np.asarray(deep_matrices[deep_row])
        if (not np.issubdtype(matrix.dtype, np.integer)
                or matrix.shape != (M, N) or np.any(matrix < 0) or np.any(matrix > 31)):
            raise ValueError(f"source H_deep invalid for graph {graph_id}")
        check_degrees = np.count_nonzero(matrix != 0, axis=1)
        variable_degrees = np.count_nonzero(matrix != 0, axis=0)
        if (not np.all(variable_degrees == 2)
                or int(np.count_nonzero(check_degrees == 4)) != 4
                or int(np.count_nonzero(check_degrees == 5)) != 48
                or int(check_degrees.sum()) != 256
                or not _check_connected_support(matrix)):
            raise ValueError(f"source H_deep degree/support admission failed for graph {graph_id}")
        source_j = 1 if graph_id == 2026093905 else 0
        source_seed = 2560859716 if graph_id == 2026093905 else graph_id
        lineage = {
            "source_uuid": str(lineage_arrays["constructor_source_uuid"][constructor_row]),
            "source_path": str(lineage_arrays["constructor_source_path"][constructor_row]),
            "source_matrix_index": int(lineage_arrays["constructor_source_matrix_index"][constructor_row]),
            "source_attempt_j": int(lineage_arrays["constructor_source_attempt_j"][constructor_row]),
            "source_construction_seed": int(lineage_arrays["constructor_source_seed"][constructor_row]),
            "source_graph_id": int(lineage_arrays["constructor_source_graph_id"][constructor_row]),
        }
        if (lineage["source_uuid"] != SOURCE_UUID or lineage["source_path"] != SOURCE_PATH
                or lineage["source_matrix_index"] != expected_matrix_index[graph_id]
                or lineage["source_attempt_j"] != source_j
                or lineage["source_construction_seed"] != source_seed
                or lineage["source_graph_id"] != graph_id):
            raise ValueError(f"source constructor lineage mismatch for graph {graph_id}")
        selected.append({
            "graph_id": graph_id, "graph_seed": graph_id, "H": matrix.copy(),
            "deep_row_index": deep_row, "constructor_row_index": constructor_row,
            "profile_index": pair[0], "graph_index": pair[1],
            "source_lineage": lineage,
        })
    return identity, selected


def _default_source_reader(repo_root: str | Path | None = None
                           ) -> Callable[[], Mapping[str, Any]]:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    path = root / "workspace" / "gf32_degree_admitted_a9352bc1" / "diagnostics.npz"

    def read() -> Mapping[str, Any]:
        with np.load(path, allow_pickle=False) as archive:
            return {key: archive[key] for key in SOURCE_ARRAY_KEYS}
    return read


def _rss_bytes() -> int | None:
    try:
        import resource
    except ImportError:
        return None
    # Linux/WSL ru_maxrss is a process high-water mark reported in KiB.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None, *,
                      official_root: str | Path = OUT_ROOT_RELATIVE) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() else (root / requested).resolve()
    expected_path = Path(official_root)
    expected = (root / expected_path).resolve() if not expected_path.is_absolute() else expected_path.resolve()
    if resolved != expected:
        raise ValueError(f"out-root must equal frozen fresh root {expected}")
    if resolved.exists():
        raise FileExistsError(f"refusing existing output root {resolved}")
    return resolved


def verify_t0(*, batch_uuid: str = BATCH_UUID, contract: str = CONTRACT,
              seed_namespace: str = SEED_NAMESPACE,
              additional_excluded_plans: Sequence[tuple[str, Sequence[Sequence[int]]]] = ()
              ) -> dict[str, Any]:
    rows, exclusions = validate_seed_plan(
        seed_namespace=seed_namespace,
        additional_excluded_plans=additional_excluded_plans)
    distribution = pmf()
    if len(rows) != HOLDOUT_PAIRS or not np.isclose(distribution.sum(), 1.0, atol=1e-15):
        raise AssertionError("frozen pair plan or PMF is invalid")
    return {
        "status": "PASS", "batch_uuid": batch_uuid, "contract": contract,
        "seed_namespace": seed_namespace, "holdout_pairs": HOLDOUT_PAIRS,
        "prior_exclusion_plan_count": len(exclusions),
        "prior_exclusion_rows": sum(int(row["rows"]) for row in exclusions),
        "source_reads": 0, "sampler_calls": 0, "decoder_calls": 0,
        "writes": 0,
    }


def dry_run(out_root: str | Path = OUT_ROOT_RELATIVE,
            repo_root: str | Path | None = None, *,
            batch_uuid: str = BATCH_UUID, contract: str = CONTRACT,
            seed_namespace: str = SEED_NAMESPACE,
            official_root: str | Path = OUT_ROOT_RELATIVE,
            additional_excluded_plans: Sequence[tuple[str, Sequence[Sequence[int]]]] = ()
            ) -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root, official_root=official_root)
    t0 = verify_t0(
        batch_uuid=batch_uuid, contract=contract, seed_namespace=seed_namespace,
        additional_excluded_plans=additional_excluded_plans)
    return {
        "status": "DRY_RUN", "batch_uuid": batch_uuid, "contract": contract,
        "out_root": str(root), "source_reads": 0, "sampler_calls": 0,
        "decoder_calls": 0, "writes": 0, "t0": t0,
    }


def _json_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True,
                               default=_json_value) + "\n", encoding="utf-8")


def _append_log(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(text.rstrip() + "\n")


def _empty_summary(batch_uuid: str = BATCH_UUID, contract: str = CONTRACT,
                   seed_namespace: str = SEED_NAMESPACE) -> dict[str, Any]:
    return {
        "track": "EXPLORE", "batch_uuid": batch_uuid, "contract": contract,
        "seed_namespace": seed_namespace, "status": "RUNNING",
        "classification": None, "stop_reasons": [],
        "planned_pairs": HOLDOUT_PAIRS, "completed_pairs": 0,
        "sampled_pairs": 0, "attempted_physical_calls": 0,
        "baseline_calls": 0, "branch_calls": 0,
        "logical_control_calls": 0, "logical_candidate_calls": 0,
        "physical_decoder_iterations": 0, "logical_control_iterations": 0,
        "logical_candidate_iterations": 0, "nominal_edge_iteration_proxy": 0,
        "nominal_edge_iteration_proxy_cap": 256 * MAX_ITER * MAX_PHYSICAL_CALLS,
        "disclosure_bits": 0, "syndrome_bits_per_method_frame": SYNDROME_BITS,
        "internal_branch_disclosure_bits": 0, "tag_bits": 0,
        "verification": "NOT_IMPLEMENTED", "undetected": "NOT_MEASURED",
        "control_exact": None, "candidate_exact": None, "delta_exact": None,
        "syndrome_valid_wrong_control": None,
        "syndrome_valid_wrong_candidate": None,
        "syndrome_failed_control": None, "syndrome_failed_candidate": None,
        "paired": None, "per_graph": None,
        "resource_violations": 0, "integrity_violations": 0,
        "data_violations": 0, "authorization_violations": 0,
        "peak_rss_bytes": None, "resource_checkpoint_wall_s": None,
        "total_wall_s": None,
    }


def _null_comparison_totals(summary: dict[str, Any]) -> None:
    for key in (
        "control_exact", "candidate_exact", "delta_exact",
        "syndrome_valid_wrong_control", "syndrome_valid_wrong_candidate",
        "syndrome_failed_control", "syndrome_failed_candidate", "paired",
        "per_graph",
    ):
        summary[key] = None
    summary["classification"] = (
        "STOP" if summary["status"] == "STOP" else "INCOMPLETE")


def _classification(summary: dict[str, Any], pairs: Sequence[Mapping[str, Any]]) -> str:
    control = int(sum(bool(row["control_exact"]) for row in pairs))
    candidate = int(sum(bool(row["candidate_exact"]) for row in pairs))
    delta = candidate - control
    graph_delta = {}
    for graph_id in GRAPH_IDS:
        graph_rows = [row for row in pairs if int(row["graph_id"]) == graph_id]
        graph_delta[str(graph_id)] = int(
            sum(bool(row["candidate_exact"]) for row in graph_rows)
            - sum(bool(row["control_exact"]) for row in graph_rows))
    if not 39 <= control <= 153:
        return "CONTROL_RANGE_UNINFORMATIVE"
    if delta >= 12 and sum(value > 0 for value in graph_delta.values()) >= 4:
        if int(summary["syndrome_valid_wrong_candidate"]) \
                <= int(summary["syndrome_valid_wrong_control"]):
            return "MECHANISM_SIGNAL"
        return "EXACT_GAIN_WITH_SELECTION_RISK"
    return "NO_SUFFICIENT_SIGNAL"


def _compute_full_totals(summary: dict[str, Any], pairs: Sequence[Mapping[str, Any]]) -> None:
    control_exact = sum(bool(row["control_exact"]) for row in pairs)
    candidate_exact = sum(bool(row["candidate_exact"]) for row in pairs)
    wrong_control = sum(bool(row["control_valid_wrong"]) for row in pairs)
    wrong_candidate = sum(bool(row["candidate_valid_wrong"]) for row in pairs)
    failed_control = sum(bool(row["control_syndrome_failed"]) for row in pairs)
    failed_candidate = sum(bool(row["candidate_syndrome_failed"]) for row in pairs)
    per_graph = {}
    for graph_id in GRAPH_IDS:
        rows = [row for row in pairs if int(row["graph_id"]) == graph_id]
        c = sum(bool(row["control_exact"]) for row in rows)
        r = sum(bool(row["candidate_exact"]) for row in rows)
        per_graph[str(graph_id)] = {
            "control_exact": int(c), "candidate_exact": int(r),
            "delta_exact": int(r - c),
            "control_valid_wrong": int(sum(bool(x["control_valid_wrong"]) for x in rows)),
            "candidate_valid_wrong": int(sum(bool(x["candidate_valid_wrong"]) for x in rows)),
            "control_syndrome_failed": int(sum(bool(x["control_syndrome_failed"]) for x in rows)),
            "candidate_syndrome_failed": int(sum(bool(x["candidate_syndrome_failed"]) for x in rows)),
        }
    both = sum(bool(row["control_exact"] and row["candidate_exact"]) for row in pairs)
    control_only = sum(bool(row["control_exact"] and not row["candidate_exact"]) for row in pairs)
    candidate_only = sum(bool(row["candidate_exact"] and not row["control_exact"]) for row in pairs)
    neither = len(pairs) - both - control_only - candidate_only
    summary.update({
        "control_exact": int(control_exact), "candidate_exact": int(candidate_exact),
        "delta_exact": int(candidate_exact - control_exact),
        "syndrome_valid_wrong_control": int(wrong_control),
        "syndrome_valid_wrong_candidate": int(wrong_candidate),
        "syndrome_failed_control": int(failed_control),
        "syndrome_failed_candidate": int(failed_candidate),
        "paired": {
            "both_exact": int(both), "candidate_only": int(candidate_only),
            "control_only": int(control_only), "neither": int(neither),
        },
        "per_graph": per_graph,
    })


def _diagnostic_arrays(
        selected_sources: Sequence[Mapping[str, Any]],
        source_identity: Mapping[str, str] | None,
        original_prior: np.ndarray,
        pairs: Sequence[Mapping[str, Any]],
        calls: Sequence[Mapping[str, Any]],
        raw_vectors: Sequence[np.ndarray],
        belief_rows: Sequence[Mapping[str, Any]],
        selector_rows: Sequence[Mapping[str, Any]],
        branch_scores: Sequence[Mapping[str, Any]],
        ) -> dict[str, np.ndarray]:
    n_source = len(selected_sources)
    source_lineage = [row.get("source_lineage", {}) for row in selected_sources]
    arrays = {
        "source_batch_uuid": np.asarray(
            ["" if source_identity is None else source_identity["batch_uuid"]], dtype="<U36"),
        "source_contract": np.asarray(
            ["" if source_identity is None else source_identity["contract"]], dtype="<U96"),
        "source_seed_namespace": np.asarray(
            ["" if source_identity is None else source_identity["seed_namespace"]], dtype="<U40"),
        "source_graph_input_kind": np.asarray(
            ["" if source_identity is None else source_identity["graph_input_kind"]], dtype="<U32"),
        "source_graph_id": np.asarray([r["graph_id"] for r in selected_sources], dtype=np.int64),
        "source_graph_seed": np.asarray([r["graph_seed"] for r in selected_sources], dtype=np.int64),
        "source_deep_row_index": np.asarray([r["deep_row_index"] for r in selected_sources], dtype=np.int64),
        "source_constructor_row_index": np.asarray([r["constructor_row_index"] for r in selected_sources], dtype=np.int64),
        "source_profile_index": np.asarray([r["profile_index"] for r in selected_sources], dtype=np.int64),
        "source_graph_index": np.asarray([r["graph_index"] for r in selected_sources], dtype=np.int64),
        "H_deep": (np.stack([r["H"] for r in selected_sources]).astype(np.uint8, copy=False)
                   if n_source else np.empty((0, M, N), dtype=np.uint8)),
        "source_constructor_uuid": np.asarray(
            [r.get("source_uuid", "") for r in source_lineage], dtype="<U36"),
        "source_constructor_path": np.asarray(
            [r.get("source_path", "") for r in source_lineage], dtype="<U160"),
        "source_constructor_matrix_index": np.asarray(
            [r.get("source_matrix_index", -1) for r in source_lineage], dtype=np.int64),
        "source_constructor_attempt_j": np.asarray(
            [r.get("source_attempt_j", -1) for r in source_lineage], dtype=np.int64),
        "source_constructor_seed": np.asarray(
            [r.get("source_construction_seed", -1) for r in source_lineage], dtype=np.int64),
        "source_constructor_graph_id": np.asarray(
            [r.get("source_graph_id", -1) for r in source_lineage], dtype=np.int64),
        "original_prior": np.asarray(original_prior, dtype=np.float64),
        "pair_index": np.asarray([r["pair_index"] for r in pairs], dtype=np.int64),
        "pair_graph_id": np.asarray([r["graph_id"] for r in pairs], dtype=np.int64),
        "pair_graph_seed": np.asarray([r["graph_seed"] for r in pairs], dtype=np.int64),
        "pair_stream": np.asarray([r["stream"] for r in pairs], dtype=np.int64),
        "pair_frame": np.asarray([r["frame"] for r in pairs], dtype=np.int64),
        "pair_seed": np.asarray([r["seed"] for r in pairs], dtype=np.int64),
        "pair_truth": (np.stack([r["truth"] for r in pairs]).astype(np.uint8, copy=False)
                       if pairs else np.empty((0, N), dtype=np.uint8)),
        "pair_syndrome": (np.stack([r["syndrome"] for r in pairs]).astype(np.uint8, copy=False)
                          if pairs else np.empty((0, M), dtype=np.uint8)),
        "pair_completed": np.asarray([r.get("completed", False) for r in pairs], dtype=np.bool_),
        "pair_baseline_call_index": np.asarray([r.get("baseline_call_index", -1) for r in pairs], dtype=np.int64),
        "pair_candidate_selected_call_index": np.asarray([r.get("candidate_selected_call_index", -1) for r in pairs], dtype=np.int64),
        "pair_selected_variable": np.asarray([r.get("selected_variable", -1) for r in pairs], dtype=np.int64),
        "call_index": np.asarray([r["call_index"] for r in calls], dtype=np.int64),
        "call_pair_index": np.asarray([r["pair_index"] for r in calls], dtype=np.int64),
        "call_graph_id": np.asarray([r["graph_id"] for r in calls], dtype=np.int64),
        "call_graph_seed": np.asarray([r["graph_seed"] for r in calls], dtype=np.int64),
        "call_stream": np.asarray([r["stream"] for r in calls], dtype=np.int64),
        "call_frame": np.asarray([r["frame"] for r in calls], dtype=np.int64),
        "call_seed": np.asarray([r["seed"] for r in calls], dtype=np.int64),
        "call_role": np.asarray([r["role"] for r in calls], dtype="<U12"),
        "call_branch_index": np.asarray([r.get("branch_index", -1) for r in calls], dtype=np.int64),
        "call_guess_symbol": np.asarray([r.get("guess_symbol", -1) for r in calls], dtype=np.int64),
        "call_selected_variable": np.asarray([r.get("selected_variable", -1) for r in calls], dtype=np.int64),
        "call_returned_selected_symbol": np.asarray([r.get("returned_selected_symbol", -1) for r in calls], dtype=np.int64),
        "call_status": np.asarray([r["status"] for r in calls], dtype="<U32"),
        "call_decoder_status": np.asarray([r.get("decoder_status") or "" for r in calls], dtype="<U64"),
        "call_iterations": np.asarray([-1 if r.get("iterations") is None else r["iterations"] for r in calls], dtype=np.int64),
        "call_decoder_runtime_s": np.asarray([r.get("decoder_runtime_s", np.nan) for r in calls], dtype=np.float64),
        "call_wall_s": np.asarray([r.get("wall_s", np.nan) for r in calls], dtype=np.float64),
        "call_rss_bytes": np.asarray([-1 if r.get("rss_bytes") is None else r["rss_bytes"] for r in calls], dtype=np.int64),
        "call_syndrome_valid": np.asarray([r.get("syndrome_valid", False) for r in calls], dtype=np.bool_),
        "call_syndrome_ok_reported": np.asarray([r.get("syndrome_ok_reported", None) is True for r in calls], dtype=np.bool_),
        "call_syndrome_ok_reported_available": np.asarray([r.get("syndrome_ok_reported") is not None for r in calls], dtype=np.bool_),
        "call_exact": np.asarray([r.get("exact", False) for r in calls], dtype=np.bool_),
        "call_syndrome_valid_wrong": np.asarray([r.get("syndrome_valid_wrong", False) for r in calls], dtype=np.bool_),
        "call_syndrome_failed": np.asarray([r.get("syndrome_failed", False) for r in calls], dtype=np.bool_),
        "call_raw_vector_index": np.asarray([-1 if r.get("raw_vector_index") is None else r["raw_vector_index"] for r in calls], dtype=np.int64),
        "call_score_original_prior": np.asarray([r.get("score_original_prior", np.nan) for r in calls], dtype=np.float64),
        "call_belief_provenance": np.asarray([r.get("belief_provenance") or "" for r in calls], dtype="<U32"),
        "call_candidate_selected_call_index": np.asarray([-1 if r.get("candidate_selected_call_index") is None else r["candidate_selected_call_index"] for r in calls], dtype=np.int64),
        "call_failure_reason": np.asarray([r.get("failure_reason") or "" for r in calls], dtype="<U256"),
        "raw_vector_call_index": np.asarray(
            [r["call_index"] for r in calls if r.get("raw_vector_index") is not None],
            dtype=np.int64),
        "raw_x_hat": (np.stack(raw_vectors).astype(np.uint8, copy=False)
                      if raw_vectors else np.empty((0, N), dtype=np.uint8)),
        "belief_call_index": np.asarray([r["call_index"] for r in belief_rows], dtype=np.int64),
        "baseline_failure_belief_provenance": np.asarray([r["provenance"] for r in belief_rows], dtype="<U32"),
        "baseline_failure_beliefs": (np.stack([r["beliefs"] for r in belief_rows]).astype(np.float64, copy=False)
                                     if belief_rows else np.empty((0, N, Q), dtype=np.float64)),
        "selector_call_index": np.asarray([r["call_index"] for r in selector_rows], dtype=np.int64),
        "selector_entropy_bits": (np.stack([r["metadata"]["entropy_bits"] for r in selector_rows]).astype(np.float64, copy=False)
                                  if selector_rows else np.empty((0, N), dtype=np.float64)),
        "selector_active_mask": (np.stack([r["active_mask"] for r in selector_rows]).astype(np.bool_, copy=False)
                                 if selector_rows else np.empty((0, N), dtype=np.bool_)),
        "selector_violated_check_mask": (np.stack([r["violated_mask"] for r in selector_rows]).astype(np.bool_, copy=False)
                                         if selector_rows else np.empty((0, M), dtype=np.bool_)),
        "selector_selected_column": np.asarray([r["metadata"]["selected_column"] for r in selector_rows], dtype=np.int64),
        "branch_score_call_index": np.asarray([r["call_index"] for r in branch_scores], dtype=np.int64),
        "branch_score_branch_index": np.asarray([r["branch_index"] for r in branch_scores], dtype=np.int64),
        "branch_score_guess_symbol": np.asarray([r["guess_symbol"] for r in branch_scores], dtype=np.int64),
        "branch_score_original_prior": np.asarray([np.nan if r["score"] is None else r["score"] for r in branch_scores], dtype=np.float64),
        "branch_score_available": np.asarray([r["score"] is not None for r in branch_scores], dtype=np.bool_),
        "branch_score_syndrome_valid": np.asarray([r["syndrome_valid"] for r in branch_scores], dtype=np.bool_),
    }
    return arrays


def _write_diagnostics(path: Path, arrays: Mapping[str, np.ndarray]) -> int:
    payload = sum(int(value.nbytes) for value in arrays.values())
    if payload > ARTIFACT_CAP_BYTES:
        raise ValueError("diagnostics.npz payload exceeds the frozen 20 MiB cap")
    np.savez_compressed(path, **arrays)
    size = int(path.stat().st_size)
    if size > ARTIFACT_CAP_BYTES:
        raise ValueError("diagnostics.npz exceeds the frozen 20 MiB cap")
    return size


def execute_batch(
        *, source_reader: Callable[[], Mapping[str, Any]],
        sampler: Callable[..., Any],
        decode_fns: Mapping[str, Callable[..., Any]],
        out_root: str | Path,
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str = COMMAND,
        batch_uuid: str = BATCH_UUID,
        contract: str = CONTRACT,
        seed_namespace: str = SEED_NAMESPACE,
        official_root: str | Path = OUT_ROOT_RELATIVE,
        additional_excluded_plans: Sequence[tuple[str, Sequence[Sequence[int]]]] = (),
        ) -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root, official_root=official_root)
    if not callable(source_reader) or not callable(sampler):
        raise ValueError("explicit source_reader and sampler callbacks are required")
    if (not isinstance(decode_fns, Mapping)
            or set(decode_fns) != {"baseline", "soft_prior"}
            or any(not callable(decode_fns[name]) for name in decode_fns)):
        raise ValueError("decode_fns must provide baseline and soft_prior callbacks")
    rss_fn = _rss_bytes if rss_fn is None else rss_fn
    started = float(now())
    root.mkdir(parents=True, exist_ok=False)
    log_path = root / "EXPLORATION_LOG.md"
    _append_log(log_path, (
        f"EXPLORE batch {batch_uuid} started; source and seed plans are frozen; "
        "production bindings were supplied only to --execute."))

    summary = _empty_summary(batch_uuid, contract, seed_namespace)
    plan: list[tuple[int, int, int, int]] = []
    exclusion_records: list[dict[str, Any]] = []
    source_identity: dict[str, str] | None = None
    selected_sources: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    raw_vectors: list[np.ndarray] = []
    belief_rows: list[dict[str, Any]] = []
    selector_rows: list[dict[str, Any]] = []
    branch_scores: list[dict[str, Any]] = []
    stop_reasons: list[str] = []
    peak_rss: int | None = None
    original_pmf = pmf()
    original_prior = np.tile(original_pmf, (N, 1))
    prior_eff = effective_prior(original_prior)
    resource_events: list[str] = []
    run_status = "RUNNING"

    def sample_resources(phase: str, current: float | None = None,
                         call_wall: float | None = None) -> list[str]:
        nonlocal peak_rss
        elapsed = max((float(now()) if current is None else current) - started, 0.0)
        rss_value = rss_fn()
        if rss_value is not None:
            rss_value = int(rss_value)
            peak_rss = rss_value if peak_rss is None else max(peak_rss, rss_value)
        reasons = []
        if elapsed > WALL_CAP_S:
            reasons.append("total_wall_cap")
        if rss_value is not None and rss_value > RSS_CAP_BYTES:
            reasons.append("peak_rss_cap")
        if call_wall is not None and call_wall > CALL_CAP_S:
            reasons.append("decoder_call_wall_cap_after_return")
        if reasons:
            resource_events.extend(f"{phase}:{reason}" for reason in reasons)
        return reasons

    def stop(status: str, reason: str, kind: str) -> None:
        nonlocal run_status
        run_status = status
        if reason not in stop_reasons:
            stop_reasons.append(reason)
        key = {
            "resource": "resource_violations",
            "integrity": "integrity_violations",
            "data": "data_violations",
            "authorization": "authorization_violations",
        }[kind]
        summary[key] = int(summary[key]) + 1

    def pair_context(pair: Mapping[str, Any]) -> dict[str, Any]:
        return {key: pair[key] for key in (
            "pair_index", "graph_id", "graph_seed", "stream", "frame", "seed")}

    def make_call(pair: dict[str, Any], role: str, prior: np.ndarray,
                  *, branch_index: int | None = None,
                  guess_symbol: int | None = None,
                  selected_variable: int | None = None,
                  selector_metadata: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
        nonlocal run_status, peak_rss
        before_reasons = sample_resources("before_decoder_call")
        if before_reasons:
            stop("INCOMPLETE", ";".join(before_reasons), "resource")
            return None
        call_index = len(calls)
        call_started = float(now())
        row: dict[str, Any] = {
            **pair_context(pair), "call_index": call_index, "role": role,
            "branch_index": -1 if branch_index is None else int(branch_index),
            "guess_symbol": -1 if guess_symbol is None else int(guess_symbol),
            "selected_variable": -1 if selected_variable is None else int(selected_variable),
            "returned_selected_symbol": -1, "status": "RUNNING",
            "decoder_status": None, "iterations": None,
            "decoder_runtime_s": None, "wall_s": None, "rss_bytes": None,
            "syndrome_valid": None, "syndrome_ok_reported": None,
            "exact": None, "syndrome_valid_wrong": None,
            "syndrome_failed": None, "raw_vector_index": None,
            "score_original_prior": None, "belief_provenance": None,
            "candidate_selected_call_index": None,
            "selector_violated_check_ids": [],
            "selector_active_variable_columns": [],
            "selector_max_entropy_bits": None,
            "selector_entropy_bits_json": "", "failure_reason": "",
            "x_hat": None,
        }
        if selector_metadata is not None:
            row.update({
                "selector_violated_check_ids": selector_metadata["violated_check_ids"],
                "selector_active_variable_columns": selector_metadata["active_variable_columns"],
                "selector_max_entropy_bits": selector_metadata["max_entropy_bits"],
                "selector_entropy_bits_json": json.dumps(selector_metadata["entropy_bits"]),
            })
        calls.append(row)
        try:
            raw = decode_fns["baseline" if role == "baseline" else "soft_prior"](
                pair["H"], prior, pair["syndrome"], max_iter=MAX_ITER,
                damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)
            x_hat = np.asarray(raw.x_hat)
            if (x_hat.shape != (N,) or not np.issubdtype(x_hat.dtype, np.integer)
                    or np.any(x_hat < 0) or np.any(x_hat >= Q)):
                raise ValueError("decoder x_hat must be an integer GF(32) vector of length 128")
            x_hat = x_hat.astype(np.uint8, copy=True)
            iterations = int(raw.iterations)
            runtime_s = float(raw.runtime_s)
            if not 0 <= iterations <= MAX_ITER or not math.isfinite(runtime_s) or runtime_s < 0.0:
                raise ValueError("decoder iterations/runtime are outside the frozen range")
            decoder_status = str(raw.status)
            provenance = getattr(raw, "belief_provenance", None)
            reported = getattr(raw, "syndrome_ok", None)
            syndrome_valid = bool(np.array_equal(
                np.asarray(layout.gf32_syndrome(pair["H"], x_hat), dtype=np.int64).ravel(),
                pair["syndrome"]))
            vector_index = len(raw_vectors)
            raw_vectors.append(x_hat)
            row.update({
                "status": "COMPLETE", "decoder_status": decoder_status,
                "iterations": iterations, "decoder_runtime_s": runtime_s,
                "syndrome_valid": syndrome_valid,
                "syndrome_ok_reported": None if reported is None else bool(reported),
                "raw_vector_index": vector_index, "belief_provenance": provenance,
                "x_hat": x_hat, "_raw_result": raw,
            })
            if selected_variable is not None:
                row["returned_selected_symbol"] = int(x_hat[selected_variable])
            pair_started_wall = max(float(now()) - call_started, 0.0)
            rss_value = rss_fn()
            if rss_value is not None:
                rss_value = int(rss_value)
                peak_rss = rss_value if peak_rss is None else max(peak_rss, rss_value)
            row["wall_s"] = pair_started_wall
            row["rss_bytes"] = rss_value
            over = []
            if pair_started_wall > CALL_CAP_S:
                over.append("decoder_call_wall_cap_after_return")
            if pair_started_wall + max(call_started - started, 0.0) > WALL_CAP_S:
                over.append("total_wall_cap")
            if rss_value is not None and rss_value > RSS_CAP_BYTES:
                over.append("peak_rss_cap")
            mismatch = reported is not None and bool(reported) != syndrome_valid
            if mismatch:
                row["failure_reason"] = "decoder_syndrome_flag_mismatch"
                row["syndrome_ok_reported"] = bool(reported)
                row["status"] = "STOP"
                stop("STOP", "decoder_syndrome_flag_mismatch", "integrity")
            if over:
                resource_events.extend(f"after_decoder_call:{reason}" for reason in over)
                if not mismatch:
                    row["status"] = "RESOURCE_STOP_AFTER_RETURN"
                    row["failure_reason"] = ";".join(over)
                stop("INCOMPLETE", ";".join(over), "resource")
            return row
        except Exception as exc:
            row["status"] = "CALL_EXCEPTION"
            row["failure_reason"] = f"{type(exc).__name__}:{exc}"
            row["wall_s"] = max(float(now()) - call_started, 0.0)
            rss_value = rss_fn()
            row["rss_bytes"] = None if rss_value is None else int(rss_value)
            if row["rss_bytes"] is not None:
                peak_rss = row["rss_bytes"] if peak_rss is None else max(peak_rss, row["rss_bytes"])
            stop("STOP", "decoder_call_failed", "integrity")
            over = []
            if row["wall_s"] > CALL_CAP_S:
                over.append("decoder_call_wall_cap_after_return")
            if call_started + row["wall_s"] - started > WALL_CAP_S:
                over.append("total_wall_cap")
            if row["rss_bytes"] is not None and row["rss_bytes"] > RSS_CAP_BYTES:
                over.append("peak_rss_cap")
            if over:
                resource_events.extend(f"after_decoder_call:{reason}" for reason in over)
                stop("INCOMPLETE", ";".join(over), "resource")
            return row

    def finalize_pair(pair: dict[str, Any], baseline: dict[str, Any],
                      candidate_call_index: int, selected_variable: int | None) -> None:
        candidate = calls[candidate_call_index]
        baseline_exact = bool(baseline["syndrome_valid"] and np.array_equal(
            baseline["x_hat"], pair["truth"]))
        candidate_exact = bool(candidate["syndrome_valid"] and np.array_equal(
            candidate["x_hat"], pair["truth"]))
        baseline_wrong = bool(baseline["syndrome_valid"] and not baseline_exact)
        candidate_wrong = bool(candidate["syndrome_valid"] and not candidate_exact)
        baseline_failed = not bool(baseline["syndrome_valid"])
        candidate_failed = not bool(candidate["syndrome_valid"])
        if baseline_exact and not candidate_exact:
            stop("STOP", "baseline_valid_passthrough_lost_exact_frame", "integrity")
        pair.update({
            "completed": True, "baseline_call_index": baseline["call_index"],
            "candidate_selected_call_index": candidate_call_index,
            "selected_variable": -1 if selected_variable is None else selected_variable,
            "control_exact": baseline_exact, "candidate_exact": candidate_exact,
            "control_valid_wrong": baseline_wrong,
            "candidate_valid_wrong": candidate_wrong,
            "control_syndrome_failed": baseline_failed,
            "candidate_syndrome_failed": candidate_failed,
        })
        for row in calls:
            if row["pair_index"] == pair["pair_index"]:
                row["candidate_selected_call_index"] = candidate_call_index
        baseline.update({
            "exact": baseline_exact, "syndrome_valid_wrong": baseline_wrong,
            "syndrome_failed": baseline_failed,
        })
        candidate.update({
            "exact": candidate_exact, "syndrome_valid_wrong": candidate_wrong,
            "syndrome_failed": candidate_failed,
        })

    try:
        plan, exclusion_records = validate_seed_plan(
            seed_namespace=seed_namespace,
            additional_excluded_plans=additional_excluded_plans)
        summary["prior_exclusion_plan_count"] = len(exclusion_records)
        summary["prior_exclusion_rows"] = sum(row["rows"] for row in exclusion_records)
    except Exception as exc:
        stop("STOP", f"seed_plan:{type(exc).__name__}:{exc}", "authorization")

    if run_status == "RUNNING":
        try:
            source_identity, selected_sources = select_sources(source_reader())
        except Exception as exc:
            stop("STOP", f"source:{type(exc).__name__}:{exc}", "data")

    source_by_graph = {int(row["graph_id"]): row for row in selected_sources}
    plan_by_key = {(g, s, f): seed for g, s, f, seed in plan}
    for graph_id in GRAPH_IDS:
        for stream in HOLDOUT_STREAMS:
            for frame in range(HOLDOUT_FRAMES_PER_STREAM):
                if run_status != "RUNNING":
                    break
                pre = sample_resources("before_sample")
                if pre:
                    stop("INCOMPLETE", ";".join(pre), "resource")
                    break
                graph = source_by_graph[graph_id]
                pair_index = len(pairs)
                seed = int(plan_by_key[(graph_id, stream, frame)])
                try:
                    truth = np.asarray(sampler(seed, original_pmf.copy(), width=N))
                    if (truth.shape != (N,) or not np.issubdtype(truth.dtype, np.integer)
                            or np.any(truth < 0) or np.any(truth >= Q)):
                        raise ValueError("sampler must return an integer GF(32) vector of length 128")
                    truth = truth.astype(np.uint8, copy=True)
                    syndrome = np.asarray(layout.gf32_syndrome(graph["H"], truth), dtype=np.uint8).ravel()
                    if syndrome.shape != (M,):
                        raise ValueError("sampled truth produced an invalid syndrome shape")
                except Exception as exc:
                    stop("STOP", f"sampler:{type(exc).__name__}:{exc}", "data")
                    break
                pair = {
                    "pair_index": pair_index, "graph_id": graph_id,
                    "graph_seed": graph_id, "stream": stream, "frame": frame,
                    "seed": seed, "truth": truth, "syndrome": syndrome,
                    "H": graph["H"], "completed": False,
                    "baseline_call_index": -1,
                    "candidate_selected_call_index": -1,
                    "selected_variable": -1,
                }
                pairs.append(pair)
                baseline = make_call(pair, "baseline", original_prior.copy())
                if baseline is None or run_status != "RUNNING" or baseline["status"] != "COMPLETE":
                    break
                if baseline["syndrome_valid"]:
                    finalize_pair(pair, baseline, baseline["call_index"], None)
                    summary["completed_pairs"] += 1
                    continue

                raw_result = baseline.get("_raw_result")
                if raw_result is None:
                    stop("STOP", "baseline_failure_beliefs_unavailable", "integrity")
                    break
                provenance = getattr(raw_result, "belief_provenance", None)
                raw_beliefs = getattr(raw_result, "final_beliefs", None)
                try:
                    actual_beliefs = np.asarray(raw_beliefs, dtype=np.float64)
                    if actual_beliefs.shape == (N, Q):
                        belief_rows.append({
                            "call_index": baseline["call_index"],
                            "provenance": "" if provenance is None else str(provenance),
                            "beliefs": actual_beliefs.copy(),
                        })
                except (TypeError, ValueError):
                    pass
                try:
                    selected_variable, selector_metadata = select_uncertain_variable(
                        pair["H"], baseline["x_hat"], raw_beliefs, pair["syndrome"],
                        belief_provenance=provenance)
                except Exception as exc:
                    stop("STOP", f"baseline_beliefs:{type(exc).__name__}:{exc}", "integrity")
                    break
                violated_mask = np.zeros(M, dtype=np.bool_)
                violated_mask[selector_metadata["violated_check_ids"]] = True
                active_mask = np.zeros(N, dtype=np.bool_)
                active_mask[selector_metadata["active_variable_columns"]] = True
                selector_row = {
                    "call_index": baseline["call_index"], "metadata": selector_metadata,
                    "active_mask": active_mask, "violated_mask": violated_mask,
                }
                selector_rows.append(selector_row)
                baseline["selected_variable"] = selected_variable
                baseline["selector_violated_check_ids"] = selector_metadata["violated_check_ids"]
                baseline["selector_active_variable_columns"] = selector_metadata["active_variable_columns"]
                baseline["selector_max_entropy_bits"] = selector_metadata["max_entropy_bits"]
                baseline["selector_entropy_bits_json"] = json.dumps(selector_metadata["entropy_bits"])
                pair["selected_variable"] = selected_variable

                branches = []
                branch_complete = True
                for branch_index, guess in enumerate(GUESSES):
                    if run_status != "RUNNING":
                        branch_complete = False
                        break
                    branch_prior = original_prior.copy()
                    branch_prior[selected_variable] = 0.0
                    branch_prior[selected_variable, guess] = 1.0
                    branch = make_call(
                        pair, "soft_prior", branch_prior,
                        branch_index=branch_index, guess_symbol=guess,
                        selected_variable=selected_variable,
                        selector_metadata=selector_metadata)
                    if branch is None or run_status != "RUNNING" or branch["status"] != "COMPLETE":
                        branch_complete = False
                        break
                    branches.append(branch)
                if not branch_complete or len(branches) != len(GUESSES):
                    break
                selected_call, score_rows = select_soft_prior_branch(branches, original_prior)
                branch_scores.extend({
                    **row, "guess_symbol": int(branches[row["branch_index"]]["guess_symbol"])
                } for row in score_rows)
                for branch, score_row in zip(branches, score_rows):
                    branch["score_original_prior"] = score_row["score"]
                if selected_call is None:
                    selected_call = baseline["call_index"]
                finalize_pair(pair, baseline, selected_call, selected_variable)
                summary["completed_pairs"] += 1

    # Count all attempted physical calls; logical arm costs remain separate.
    summary["sampled_pairs"] = len(pairs)
    summary["attempted_physical_calls"] = len(calls)
    summary["baseline_calls"] = sum(row["role"] == "baseline" for row in calls)
    summary["branch_calls"] = sum(row["role"] == "soft_prior" for row in calls)
    summary["logical_control_calls"] = summary["baseline_calls"]
    summary["logical_candidate_calls"] = summary["baseline_calls"] + summary["branch_calls"]
    summary["physical_decoder_iterations"] = int(sum(
        int(row["iterations"] or 0) for row in calls))
    summary["logical_control_iterations"] = int(sum(
        int(row["iterations"] or 0) for row in calls if row["role"] == "baseline"))
    summary["logical_candidate_iterations"] = summary["physical_decoder_iterations"]
    summary["nominal_edge_iteration_proxy"] = 256 * summary["physical_decoder_iterations"]
    summary["disclosure_bits"] = len(pairs) * 2 * SYNDROME_BITS
    summary["resource_violations"] = len(resource_events)
    summary["stop_reasons"] = stop_reasons
    summary["peak_rss_bytes"] = peak_rss

    if run_status == "RUNNING" and summary["completed_pairs"] == HOLDOUT_PAIRS:
        if summary["integrity_violations"] or summary["data_violations"] \
                or summary["resource_violations"] or summary["authorization_violations"]:
            run_status = "INCOMPLETE"
        else:
            run_status = "COMPLETE"
    elif run_status == "RUNNING":
        run_status = "INCOMPLETE"
    summary["status"] = run_status
    full_comparison = run_status == "COMPLETE" and summary["completed_pairs"] == HOLDOUT_PAIRS
    if full_comparison:
        _compute_full_totals(summary, [row for row in pairs if row.get("completed")])
        summary["classification"] = _classification(summary, pairs)
    else:
        _null_comparison_totals(summary)

    manifest = {
        "track": "EXPLORE", "batch_uuid": batch_uuid,
        "contract": contract, "seed_namespace": seed_namespace,
        "status": summary["status"], "classification": summary["classification"],
        "exact_command": command, "source_expected": {
            "batch_uuid": SOURCE_BATCH_UUID, "contract": SOURCE_CONTRACT,
            "seed_namespace": SOURCE_NAMESPACE, "graph_input_kind": SOURCE_KIND,
        },
        "source_identity": source_identity,
        "source_maps": [{k: v for k, v in row.items() if k not in ("H",)}
                         for row in selected_sources],
        "seed_plan": [
            {"graph_id": g, "stream": s, "frame": f, "seed": seed}
            for g, s, f, seed in plan
        ],
        "seed_exclusion_generators": exclusion_records,
        "pmf": original_pmf.tolist(),
        "decoder": {
            "implementation": "v35.decode_row_layered_fftqspa",
            "max_iter": MAX_ITER, "damping_alpha": DAMPING_ALPHA,
            "warm_beliefs": None, "field": None,
        },
        "algorithm": {
            "baseline_validity": "independent H*x_hat == given syndrome",
            "belief_provenance_required": "CHECK_UPDATED",
            "selector": "max stable-softmax entropy among variables adjacent to violated checks; 1e-12 tie -> lowest column",
            "guesses": list(GUESSES),
            "branch_prior": "copy original probability prior; replace only selected row by one-hot; decoder floors at 1e-15",
            "candidate_score": "sum log(P_eff[i,x_hat_i]) using original effective prior; 1e-12 tie -> lowest branch index",
        },
        "accounting": {
            "physical_calls": summary["attempted_physical_calls"],
            "logical_control_calls": summary["logical_control_calls"],
            "logical_candidate_calls": summary["logical_candidate_calls"],
            "syndrome_bits_per_method_frame": SYNDROME_BITS,
            "internal_branch_disclosure_bits": 0,
            "tag_bits": 0, "verification": "NOT_IMPLEMENTED",
            "undetected": "NOT_MEASURED",
        },
        "budgets": {
            "wall_s": WALL_CAP_S, "per_call_s_after_return": CALL_CAP_S,
            "rss_bytes": RSS_CAP_BYTES, "diagnostics_bytes": ARTIFACT_CAP_BYTES,
            "physical_calls": MAX_PHYSICAL_CALLS,
            "osd_calls": 0, "graph_build_calls": 0, "label_search_calls": 0,
        },
        "resource_events": resource_events,
        "stop_reasons": stop_reasons,
        "summary": summary,
    }
    arrays = _diagnostic_arrays(
        selected_sources, source_identity, original_prior, pairs, calls,
        raw_vectors, belief_rows, selector_rows, branch_scores)
    diagnostics_path = root / "diagnostics.npz"
    diagnostics_size = _write_diagnostics(diagnostics_path, arrays)
    manifest["diagnostics_npz_bytes"] = diagnostics_size
    csv_path = root / "frame_records.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CALL_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in calls:
            writer.writerow({
                key: (json.dumps(row[key]) if isinstance(row.get(key), (list, dict)) else row.get(key))
                for key in CALL_FIELDS
            })
    summary_path = root / "summary.json"
    manifest_path = root / "manifest.json"
    _write_json(summary_path, summary)
    _write_json(manifest_path, manifest)

    # This is the frozen final checkpoint: it follows all first-pass artifacts.
    checkpoint_wall = max(float(now()) - started, 0.0)
    checkpoint_reasons = sample_resources("after_first_pass_artifacts", current=started + checkpoint_wall)
    summary["resource_checkpoint_wall_s"] = checkpoint_wall
    summary["total_wall_s"] = checkpoint_wall
    summary["peak_rss_bytes"] = peak_rss
    if checkpoint_reasons:
        summary["resource_violations"] = len(resource_events)
        summary["status"] = "INCOMPLETE"
        summary["stop_reasons"] = list(dict.fromkeys(
            [*summary["stop_reasons"], "resource_overcap_after_first_pass_artifacts"]))
        _null_comparison_totals(summary)
        manifest["status"] = summary["status"]
        manifest["classification"] = summary["classification"]
        manifest["resource_events"] = resource_events
        manifest["stop_reasons"] = summary["stop_reasons"]
        manifest["summary"] = summary
        _write_json(summary_path, summary)
        _write_json(manifest_path, manifest)
    else:
        manifest["summary"] = summary
        manifest["resource_events"] = resource_events
        _write_json(summary_path, summary)
        _write_json(manifest_path, manifest)

    _append_log(log_path, (
        f"FINAL_STATUS={summary['status']}; classification={summary['classification']}; "
        f"completed_pairs={summary['completed_pairs']}; "
        f"physical_calls={summary['attempted_physical_calls']}; "
        f"branch_calls={summary['branch_calls']}; resource_checkpoint_wall_s={checkpoint_wall:.9f}; "
        f"peak_rss_bytes={summary['peak_rss_bytes']}; stop_reasons={summary['stop_reasons']}"))
    result = dict(summary)
    public_calls = [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in calls
    ]
    result.update({
        "summary": summary, "calls": public_calls, "pairs": pairs,
        "source_maps": [{k: v for k, v in row.items() if k != "H"}
                        for row in selected_sources],
        "artifacts": {
            "manifest": str(manifest_path), "summary": str(summary_path),
            "frame_records": str(csv_path), "diagnostics": str(diagnostics_path),
            "exploration_log": str(log_path),
        },
    })
    return result


def _bind_production() -> dict[str, Any]:
    """Create source/sampler/decoder callbacks only from explicit --execute."""
    from comparison_bench.cli import nbldpc_gf32_label_probe as sampler_module
    from comparison_bench.formal_ir import v35_algorithm_development as v35

    def decode(h, prior, syndrome, *, max_iter, damping_alpha,
               warm_beliefs, field):
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=max_iter,
            damping_alpha=damping_alpha, warm_beliefs=warm_beliefs, field=field)

    return {
        "source_reader": _default_source_reader(),
        "sampler": sampler_module.sample_error,
        "decode_fns": {"baseline": decode, "soft_prior": decode},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GF(32) single-symbol soft-prior rescue EXPLORE")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--t0", action="store_true", help="source-free seed/contract checks")
    mode.add_argument("--dry-run", action="store_true", help="validate frozen root; no reads/writes")
    mode.add_argument("--execute", action="store_true", help="run one frozen synthetic batch")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.t0:
        result = verify_t0()
    elif args.dry_run:
        result = dry_run(args.out_root)
    else:
        result = execute_batch(
            **_bind_production(), out_root=args.out_root, command=COMMAND)
    print(json.dumps(result, indent=2, sort_keys=True, default=_json_value))
    return 0 if result.get("status") in ("PASS", "DRY_RUN", "COMPLETE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
