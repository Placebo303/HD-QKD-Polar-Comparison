"""Fixed-source GF(32) constructor/deep-label endpoint EXPLORE diagnostic."""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from comparison_bench.cli.probes_closed import nbldpc_gf32_label_probe as prior_runner
from comparison_bench.formal_ir import nbldpc_l1_degree2_layout as layout
from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

CONTRACT = "NBLDPC-GF32-ENDPOINT-ABLATION-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "67ca7191-3adc-4202-9d78-8bcd1a90a05a"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_endpoint_67ca7191"
SEED_PREFIX = "gf32-endpoint-ablation-v1"

SOURCE_UUID = "a9352bc1-ae56-443b-ae93-9dcfa85d4229"
SOURCE_CONTRACT = "NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md"
SOURCE_SEED_PREFIX = "gf32-degree-admitted-v1"
SOURCE_NPZ_RELATIVE = (Path("workspace") / "gf32_degree_admitted_a9352bc1"
                       / "diagnostics.npz")
SOURCE_CONSTRUCTION_UUID = "a9a18abe-3547-4d16-aa50-1f7150182f31"
SOURCE_CONSTRUCTION_PATH = (
    "workspace/gf32_construct_a9a18abe/constructions.json")

N, M, EDGE_COUNT, Q = 128, 52, 384, 32
GRAPH_SEEDS = tuple(range(2026093901, 2026093907))
PROFILE_ORDER = ("control", "candidate")
ENDPOINT_PROFILE = "candidate"
ARMS = ("constructor", "deep")
HOLDOUT_PAIRS = 192
MAX_CALLS = 384
MAX_ITER = 90
DAMPING_ALPHA = 1.0
WARM_BELIEFS = None
FIELD = None
P0 = 0.550
SHAPE_COUNTS = {1: 2295, 3: 1126, 7: 557, 15: 304, 31: 146}
SYNDROME_BITS = 5 * M
WALL_CAP_S = 1200.0
CALL_CAP_S = 120.0
RSS_CAP_BYTES = 4 * 1024 ** 3
ARTIFACT_LIMIT_BYTES = 20 * 1024 * 1024
EDGE_UPDATE_PROXY_CAP = MAX_CALLS * MAX_ITER * EDGE_COUNT

FRAME_FIELDS = (
    "call_index", "pair_index", "graph_id", "stream", "frame", "seed",
    "arm", "decoder_status", "status", "iterations", "raw_vector_saved",
    "raw_symbols_equal", "syndrome_accept", "syndrome_consistent_wrong",
    "exact", "wall_s", "rss_b", "syndrome_bits", "failure_reason",
    "source_uuid", "source_path", "constructor_source_uuid",
    "constructor_source_path", "constructor_source_matrix_index",
    "constructor_source_attempt_j", "constructor_source_seed",
    "constructor_source_graph_id", "source_graph_index",
    "source_constructor_row_index", "source_deep_row_index",
    "deep_profile_index", "deep_graph_index",
)

COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.probes_closed.nbldpc_gf32_endpoint_ablation_probe --execute "
    "--out-root workspace/gf32_endpoint_67ca7191"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _scalar_text(source: Mapping[str, Any], key: str) -> str:
    values = np.asarray(source[key]).reshape(-1)
    if values.size != 1:
        raise ValueError("source identity field %s must have one value" % key)
    return str(values[0])


def _int_array(source: Mapping[str, Any], key: str) -> np.ndarray:
    values = np.asarray(source[key])
    if (not np.issubdtype(values.dtype, np.integer)
            or np.any(values < 0)):
        raise ValueError("source map %s must contain nonnegative integers" % key)
    return values.astype(np.int64, copy=False)


def _fixed_matrix(value: Any, name: str) -> np.ndarray:
    matrix = np.asarray(value)
    if (matrix.shape != (M, N)
            or not np.issubdtype(matrix.dtype, np.integer)
            or np.any(matrix < 0) or np.any(matrix >= Q)):
        raise ValueError("%s must be an integer GF(32) matrix of shape (52,128)" % name)
    matrix = matrix.astype(np.int64, copy=True)
    if int(np.count_nonzero(matrix)) != EDGE_COUNT:
        raise ValueError("%s must have exactly 384 nonzero coefficients" % name)
    if (not np.all(np.count_nonzero(matrix, axis=0) == 3)
            or not np.array_equal(np.sort(np.count_nonzero(matrix, axis=1)),
                                  np.asarray([7] * 32 + [8] * 20))):
        raise ValueError("%s does not have the frozen dv3x128 / dc7x32+8x20 profile" % name)
    return matrix


def extract_source_data(source: Mapping[str, Any]) -> dict[str, Any]:
    """Join only candidate-profile matrices and original pairs by explicit maps."""
    if not isinstance(source, Mapping):
        raise ValueError("diagnostic_reader must return a mapping of NPZ arrays")
    required = (
        "batch_uuid", "contract", "seed_namespace", "profile_order",
        "graph_seed", "graph_input_kind",
        "constructor_profile_index", "constructor_graph_index",
        "H_constructor", "constructor_source_uuid", "constructor_source_path",
        "constructor_source_matrix_index", "constructor_source_attempt_j",
        "constructor_source_seed", "constructor_source_graph_id",
        "deep_profile_index", "deep_graph_index", "H_deep",
        "pair_index", "pair_graph_index", "pair_graph_seed", "pair_stream",
        "pair_frame", "pair_seed", "pair_truth",
    )
    missing = [key for key in required if key not in source]
    if missing:
        raise ValueError("source diagnostics missing required maps: %s" % ",".join(missing))
    if (_scalar_text(source, "batch_uuid") != SOURCE_UUID
            or _scalar_text(source, "contract") != SOURCE_CONTRACT
            or _scalar_text(source, "seed_namespace") != SOURCE_SEED_PREFIX
            or _scalar_text(source, "graph_input_kind") != "admitted_source"):
        raise ValueError("source diagnostics identity/admission does not match the frozen source")

    profiles = tuple(str(x) for x in np.asarray(source["profile_order"]).reshape(-1))
    graph_ids = _int_array(source, "graph_seed").reshape(-1)
    if profiles != PROFILE_ORDER or tuple(graph_ids.tolist()) != GRAPH_SEEDS:
        raise ValueError("source profile or graph order does not match the frozen map")
    profile_index = profiles.index(ENDPOINT_PROFILE)
    graph_index = {int(seed): index for index, seed in enumerate(graph_ids)}

    c_profile = _int_array(source, "constructor_profile_index").reshape(-1)
    c_graph = _int_array(source, "constructor_graph_index").reshape(-1)
    h_constructor = np.asarray(source["H_constructor"])
    d_profile = _int_array(source, "deep_profile_index").reshape(-1)
    d_graph = _int_array(source, "deep_graph_index").reshape(-1)
    h_deep = np.asarray(source["H_deep"])
    if (h_constructor.shape != (len(c_profile), M, N)
            or c_profile.shape != c_graph.shape
            or h_deep.shape != (len(d_profile), M, N)
            or d_profile.shape != d_graph.shape
            or np.any(c_profile >= len(profiles))
            or np.any(c_graph >= len(graph_ids))
            or np.any(d_profile >= len(profiles))
            or np.any(d_graph >= len(graph_ids))):
        raise ValueError("source matrix arrays and explicit profile/graph maps disagree")

    provenance_keys = (
        "constructor_source_uuid", "constructor_source_path",
        "constructor_source_matrix_index", "constructor_source_attempt_j",
        "constructor_source_seed", "constructor_source_graph_id",
    )
    provenance = {key: np.asarray(source[key]).reshape(-1) for key in provenance_keys}
    if any(values.size != len(c_profile) for values in provenance.values()):
        raise ValueError("constructor lineage maps do not match H_constructor rows")

    c_lookup: dict[tuple[int, int], int] = {}
    d_lookup: dict[tuple[int, int], int] = {}
    for position, key in enumerate(zip(c_profile.tolist(), c_graph.tolist())):
        if key in c_lookup:
            raise ValueError("source repeats an H_constructor profile/graph map")
        c_lookup[key] = position
    for position, key in enumerate(zip(d_profile.tolist(), d_graph.tolist())):
        if key in d_lookup:
            raise ValueError("source repeats an H_deep profile/graph map")
        d_lookup[key] = position

    graphs: dict[int, dict[str, Any]] = {}
    for graph_id in GRAPH_SEEDS:
        index = graph_index[graph_id]
        c_row = c_lookup.get((profile_index, index))
        d_row = d_lookup.get((profile_index, index))
        if c_row is None or d_row is None:
            raise ValueError("source lacks a candidate DV3 endpoint for graph %d" % graph_id)
        constructor = _fixed_matrix(h_constructor[c_row], "H_constructor[%d]" % graph_id)
        deep = _fixed_matrix(h_deep[d_row], "H_deep[%d]" % graph_id)
        if not np.array_equal(constructor != 0, deep != 0):
            raise ValueError("constructor/deep support mismatch for graph %d" % graph_id)
        lineage = {
            "constructor_source_uuid": str(provenance["constructor_source_uuid"][c_row]),
            "constructor_source_path": str(provenance["constructor_source_path"][c_row]),
            "constructor_source_matrix_index": int(provenance["constructor_source_matrix_index"][c_row]),
            "constructor_source_attempt_j": int(provenance["constructor_source_attempt_j"][c_row]),
            "constructor_source_seed": int(provenance["constructor_source_seed"][c_row]),
            "constructor_source_graph_id": int(provenance["constructor_source_graph_id"][c_row]),
        }
        expected_construction_seed = (
            2560859716 if graph_id == 2026093905 else graph_id)
        if (lineage["constructor_source_uuid"] != SOURCE_CONSTRUCTION_UUID
                or lineage["constructor_source_path"] != SOURCE_CONSTRUCTION_PATH
                or lineage["constructor_source_graph_id"] != graph_id
                or lineage["constructor_source_seed"] != expected_construction_seed):
            raise ValueError("constructor source lineage mismatch for graph %d" % graph_id)
        if graph_id == 2026093905 and (
                lineage["constructor_source_matrix_index"] != 10
                or lineage["constructor_source_attempt_j"] != 1
                or lineage["constructor_source_seed"] != expected_construction_seed):
            raise ValueError("graph 2026093905 constructor lineage must remain index10/j1/seed2560859716")
        lineage.update({
            "source_graph_index": index,
            "source_constructor_row_index": c_row,
            "source_deep_row_index": d_row,
            "deep_profile_index": profile_index,
            "deep_graph_index": index,
        })
        graphs[graph_id] = {
            "constructor": constructor, "deep": deep, **lineage,
        }

    pair_index = _int_array(source, "pair_index").reshape(-1)
    pair_graph_index = _int_array(source, "pair_graph_index").reshape(-1)
    pair_graph_seed = _int_array(source, "pair_graph_seed").reshape(-1)
    pair_stream = _int_array(source, "pair_stream").reshape(-1)
    pair_frame = _int_array(source, "pair_frame").reshape(-1)
    pair_seed = _int_array(source, "pair_seed").reshape(-1)
    pair_truth = np.asarray(source["pair_truth"])
    pair_maps = (pair_graph_index, pair_graph_seed, pair_stream, pair_frame, pair_seed)
    if (pair_index.shape != (HOLDOUT_PAIRS,)
            or any(values.shape != (HOLDOUT_PAIRS,) for values in pair_maps)
            or pair_truth.shape != (HOLDOUT_PAIRS, N)
            or set(pair_index.tolist()) != set(range(HOLDOUT_PAIRS))):
        raise ValueError("source pair arrays/maps are not the frozen 192-row shape")
    if (not np.issubdtype(pair_truth.dtype, np.integer)
            or np.any(pair_truth < 0) or np.any(pair_truth >= Q)
            or len(set(pair_seed.tolist())) != HOLDOUT_PAIRS):
        raise ValueError("source truth symbols or pair seeds are invalid")
    pairs = []
    pair_cells: set[tuple[int, int, int]] = set()
    for row in np.argsort(pair_index):
        graph_id = int(pair_graph_seed[row])
        graph_idx = graph_index.get(graph_id)
        stream, frame = int(pair_stream[row]), int(pair_frame[row])
        if (graph_idx is None or int(pair_graph_index[row]) != graph_idx
                or stream not in (0, 1) or not 0 <= frame < 16):
            raise ValueError("source pair graph/stream/frame map is invalid")
        cell = (graph_id, stream, frame)
        if cell in pair_cells:
            raise ValueError("source repeats a graph/stream/frame pair")
        pair_cells.add(cell)
        pairs.append({
            "pair_index": int(pair_index[row]), "graph_id": graph_id,
            "stream": stream, "frame": frame,
            "seed": int(pair_seed[row]),
            "truth": pair_truth[row].astype(np.uint8, copy=True),
        })
    if any(sum(p["graph_id"] == graph for p in pairs) != 32 for graph in GRAPH_SEEDS):
        raise ValueError("source must contain 32 original pairs per graph")
    expected_cells = {(graph, stream, frame) for graph in GRAPH_SEEDS
                      for stream in (0, 1) for frame in range(16)}
    if pair_cells != expected_cells:
        raise ValueError("source pair maps do not cover the frozen stream/frame grid")
    return {
        "source_uuid": SOURCE_UUID, "source_contract": SOURCE_CONTRACT,
        "source_path": SOURCE_NPZ_RELATIVE.as_posix(),
        "graphs": graphs, "pairs": pairs,
    }


class _StopBatch(Exception):
    pass


def _prior_matrix() -> np.ndarray:
    pmf = np.zeros(Q, dtype=np.float64)
    pmf[0] = P0
    for symbol, count in SHAPE_COUNTS.items():
        pmf[symbol] = (1.0 - P0) * count / sum(SHAPE_COUNTS.values())
    pmf = np.maximum(pmf, 1e-15)
    pmf /= float(pmf.sum())
    return np.tile(pmf, (N, 1))


def verify_t0() -> dict[str, bool]:
    """Pure fixed-input and tiny GF(32) checks; no source or decoder binding."""
    prior = _prior_matrix()
    if (sum(SHAPE_COUNTS.values()) != 4428
            or prior.shape != (N, Q)
            or not np.isclose(float(prior[0].sum()), 1.0, rtol=0.0, atol=1e-15)
            or not np.isclose(float(prior[0, 0]), P0, rtol=0.0, atol=1e-12)
            or any(prior[0, symbol] <= 0 for symbol in range(Q))):
        raise AssertionError("frozen GF(32) synthetic prior changed")
    if (N, M, EDGE_COUNT, MAX_ITER, DAMPING_ALPHA, WALL_CAP_S,
            CALL_CAP_S, RSS_CAP_BYTES, EDGE_UPDATE_PROXY_CAP) != (
            128, 52, 384, 90, 1.0, 1200.0, 120.0,
            4 * 1024 ** 3, 13271040):
        raise AssertionError("frozen endpoint dimensions or budgets changed")
    h0 = np.asarray([[1, 0]], dtype=np.int64)
    h1 = np.asarray([[2, 0]], dtype=np.int64)
    truth = np.asarray([7, 0], dtype=np.int64)
    arms = prior_runner.paired_arm_data(h0, h1, truth, np.ones((2, Q)) / Q)
    if (arms["control"]["syndrome"].shape != (1,)
            or arms["candidate"]["syndrome"].shape != (1,)
            or np.array_equal(arms["control"]["syndrome"],
                              arms["candidate"]["syndrome"])):
        raise AssertionError("GF(32) endpoint-specific syndrome check failed")
    return {
        "frozen_source_and_pair_counts": HOLDOUT_PAIRS == 192 and MAX_CALLS == 384,
        "fixed_prior_and_decoder_settings": True,
        "own_GF32_syndromes": True,
        "fixed_budget_and_artifact_caps": True,
        "no_source_read_or_production_binding": True,
    }


def arm_order(frame: int) -> tuple[str, str]:
    """Alternate the frozen physical endpoints by the original frame index."""
    return ARMS if int(frame) % 2 == 0 else tuple(reversed(ARMS))


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() \
        else (root / requested).resolve()
    expected = (root / OUT_ROOT_RELATIVE).resolve()
    if resolved != expected:
        raise ValueError("out-root must equal the frozen path %s" % expected)
    return layout.refuse_out_root(resolved)


def dry_run(out_root: str | Path = OUT_ROOT_RELATIVE,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    checks = verify_t0()
    root = validate_out_root(out_root, repo_root=repo_root)
    return {
        "track": "EXPLORE", "status": "DRY_RUN",
        "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "out_root": str(root), "exists": root.exists(), "t0": checks,
        "diagnostic_reads": 0, "attempted_decoder_calls": 0,
        "source_extractions": 0, "production_bindings": 0, "writes": 0,
    }


def _bind_production_decoders(
        v35_decode: Callable[..., Any] | None = None
        ) -> dict[str, Callable[[np.ndarray, np.ndarray, np.ndarray], Any]]:
    if v35_decode is None:
        from comparison_bench.formal_ir import v35_algorithm_development as v35
        v35_decode = v35.decode_row_layered_fftqspa

    def decode(h: np.ndarray, prior: np.ndarray,
               syndrome: np.ndarray) -> Any:
        return v35_decode(
            h, prior, syndrome, max_iter=MAX_ITER,
            damping_alpha=DAMPING_ALPHA, warm_beliefs=WARM_BELIEFS,
            field=FIELD)

    return {"constructor": decode, "deep": decode}


def _default_diagnostic_reader(
        repo_root: str | Path | None = None) -> Callable[[], Mapping[str, Any]]:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    path = root / SOURCE_NPZ_RELATIVE

    def read() -> Mapping[str, Any]:
        with np.load(path, allow_pickle=False) as archive:
            return {key: archive[key] for key in archive.files}

    return read


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True,
                               allow_nan=False) + "\n", encoding="utf-8")


def _initial_manifest(command: str) -> dict[str, Any]:
    return {
        "track": "EXPLORE", "batch_uuid": BATCH_UUID,
        "contract": CONTRACT, "status": "RUNNING",
        "classification": "INCOMPLETE", "command": command,
        "source": {
            "batch_uuid": SOURCE_UUID, "contract": SOURCE_CONTRACT,
            "path": SOURCE_NPZ_RELATIVE.as_posix(),
            "selected_profile": ENDPOINT_PROFILE,
            "selected_graph_ids": list(GRAPH_SEEDS),
            "read_once_during_execute_only": True,
        },
        "paired_inputs": {
            "pair_count": HOLDOUT_PAIRS,
            "original_seed_map_reused": True,
            "same_truth_and_prior": True,
            "own_endpoint_syndromes": True,
            "arm_order": "even constructor-first; odd deep-first",
            "truth_passed_to_decoder": False,
        },
        "graph_profile": {
            "n": N, "m": M, "E": EDGE_COUNT,
            "variable_degrees": {"3": N},
            "check_degrees": {"7": 32, "8": 20},
            "field": "GF(32)/polynomial-37",
            "source_rank_connectivity": "reused from accepted upstream A5",
        },
        "prior": {
            "role": "synthetic iid marginal-shape proxy",
            "p0": P0,
            "counts": {str(k): int(v) for k, v in SHAPE_COUNTS.items()},
            "normalization": "floor 1e-15; normalize; v35 logs normalized prior",
        },
        "decoder": {
            "implementation": "v35.decode_row_layered_fftqspa",
            "max_iter": MAX_ITER, "damping_alpha": DAMPING_ALPHA,
            "warm_beliefs": WARM_BELIEFS, "field": FIELD,
            "only_arm_difference": "H coefficient endpoint",
            "capture": "same raw x_hat returned and classified",
        },
        "budget": {
            "wall_cap_s": WALL_CAP_S, "per_call_cap_s": CALL_CAP_S,
            "sampled_rss_cap_bytes": RSS_CAP_BYTES,
            "max_decoder_calls": MAX_CALLS,
            "syndrome_bits_per_attempted_arm": SYNDROME_BITS,
            "nominal_edge_update_proxy_cap": EDGE_UPDATE_PROXY_CAP,
            "tag_bits": 0, "verification": "NOT_IMPLEMENTED",
            "undetected": "NOT_MEASURED",
            "diagnostics_payload_cap_bytes": ARTIFACT_LIMIT_BYTES,
        },
        "claim_ceiling": (
            "finite synthetic fixed-endpoint association on reused samples; "
            "no FER, f_eff, SKR, throughput, causality, route, qualification, "
            "publication, or cross-batch ranking claim"),
    }


def _start_outputs(root: Path, manifest: Mapping[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=False)
    _write_json(root / "manifest.json", manifest)
    with (root / "frame_records.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        csv.DictWriter(handle, fieldnames=FRAME_FIELDS).writeheader()
    (root / "EXPLORATION_LOG.md").write_text(
        "# GF(32) endpoint ablation EXPLORE log\n\n"
        "Batch UUID: %s\n\nContract: %s\n\n"
        "One frozen constructor/deep attempt; no rerun or repair.\n"
        % (BATCH_UUID, CONTRACT), encoding="utf-8")


def _append_row(root: Path, row: Mapping[str, Any]) -> None:
    with (root / "frame_records.csv").open(
            "a", newline="", encoding="utf-8") as handle:
        csv.DictWriter(handle, fieldnames=FRAME_FIELDS).writerow(
            {key: row.get(key) for key in FRAME_FIELDS})


def _diagnostics_arrays(
        source_data: Mapping[str, Any] | None,
        pair_syndromes: Mapping[int, Mapping[str, np.ndarray]],
        rows: list[Mapping[str, Any]], vectors: list[Mapping[str, Any]]) -> dict[str, np.ndarray]:
    graph_ids = np.asarray(GRAPH_SEEDS if source_data else (), dtype=np.int64)
    graph_index = {int(value): i for i, value in enumerate(graph_ids)}
    graph_map = (source_data["graphs"] if source_data else {})
    pairs = source_data["pairs"] if source_data else []
    prepared = [pair for pair in pairs
                if int(pair["pair_index"]) in pair_syndromes]
    pair_syndrome = np.stack([
        np.stack([pair_syndromes[int(pair["pair_index"])][arm]
                  for arm in ARMS]) for pair in prepared
    ]).astype(np.uint8, copy=False) if prepared else np.empty((0, 2, M), dtype=np.uint8)
    vector_by_call = {int(vector["call_index"]): i
                      for i, vector in enumerate(vectors)}
    if graph_map:
        constructor_h = np.stack([graph_map[int(g)]["constructor"]
                                  for g in graph_ids]).astype(np.uint8, copy=False)
        deep_h = np.stack([graph_map[int(g)]["deep"]
                           for g in graph_ids]).astype(np.uint8, copy=False)
        lineage = [graph_map[int(g)] for g in graph_ids]
    else:
        constructor_h = deep_h = np.empty((0, M, N), dtype=np.uint8)
        lineage = []
    arrays = {
        "batch_uuid": np.asarray([BATCH_UUID], dtype="<U36"),
        "contract": np.asarray([CONTRACT], dtype="<U96"),
        "seed_namespace": np.asarray([SEED_PREFIX], dtype="<U40"),
        "source_batch_uuid": np.asarray([SOURCE_UUID], dtype="<U36"),
        "source_contract": np.asarray([SOURCE_CONTRACT], dtype="<U80"),
        "source_path": np.asarray([SOURCE_NPZ_RELATIVE.as_posix()], dtype="<U96"),
        "source_graph_seed": np.asarray(GRAPH_SEEDS, dtype=np.int64),
        "profile_order": np.asarray(PROFILE_ORDER, dtype="<U9"),
        "endpoint_profile_index": np.asarray([1], dtype=np.int64),
        "graph_id": graph_ids,
        "constructor_profile_index": np.full(len(graph_ids), 1, dtype=np.int64),
        "constructor_graph_index": np.asarray(
            [g["source_graph_index"] for g in lineage], dtype=np.int64),
        "constructor_source_graph_index": np.asarray(
            [g["source_graph_index"] for g in lineage], dtype=np.int64),
        "source_constructor_row_index": np.asarray(
            [g["source_constructor_row_index"] for g in lineage], dtype=np.int64),
        "source_deep_row_index": np.asarray(
            [g["source_deep_row_index"] for g in lineage], dtype=np.int64),
        "deep_profile_index": np.asarray(
            [g["deep_profile_index"] for g in lineage], dtype=np.int64),
        "deep_graph_index": np.asarray(
            [g["deep_graph_index"] for g in lineage], dtype=np.int64),
        "constructor_source_uuid": np.asarray(
            [g["constructor_source_uuid"] for g in lineage], dtype="<U36"),
        "constructor_source_path": np.asarray(
            [g["constructor_source_path"] for g in lineage], dtype="<U160"),
        "constructor_source_matrix_index": np.asarray(
            [g["constructor_source_matrix_index"] for g in lineage], dtype=np.int64),
        "constructor_source_attempt_j": np.asarray(
            [g["constructor_source_attempt_j"] for g in lineage], dtype=np.int64),
        "constructor_source_seed": np.asarray(
            [g["constructor_source_seed"] for g in lineage], dtype=np.int64),
        "constructor_source_graph_id": np.asarray(
            [g["constructor_source_graph_id"] for g in lineage], dtype=np.int64),
        "H_constructor": constructor_h,
        "H_deep": deep_h,
        "pair_index": np.asarray([p["pair_index"] for p in pairs], dtype=np.int64),
        "pair_graph_index": np.asarray(
            [graph_index[int(p["graph_id"])] for p in pairs], dtype=np.int64),
        "pair_graph_id": np.asarray([p["graph_id"] for p in pairs], dtype=np.int64),
        "pair_stream": np.asarray([p["stream"] for p in pairs], dtype=np.int64),
        "pair_frame": np.asarray([p["frame"] for p in pairs], dtype=np.int64),
        "pair_seed": np.asarray([p["seed"] for p in pairs], dtype=np.int64),
        "pair_truth": np.stack([p["truth"] for p in pairs]).astype(
            np.uint8, copy=False) if pairs else np.empty((0, N), dtype=np.uint8),
        "pair_syndrome_pair_index": np.asarray(
            [p["pair_index"] for p in prepared], dtype=np.int64),
        "pair_syndrome_arm_order": np.asarray(ARMS, dtype="<U12"),
        "pair_syndrome": pair_syndrome,
        "call_index": np.asarray([r["call_index"] for r in rows], dtype=np.int64),
        "call_pair_index": np.asarray([r["pair_index"] for r in rows], dtype=np.int64),
        "call_arm": np.asarray([r["arm"] for r in rows], dtype="<U12"),
        "call_graph_index": np.asarray(
            [graph_index.get(int(r["graph_id"]), -1) for r in rows], dtype=np.int64),
        "call_seed": np.asarray([r["seed"] for r in rows], dtype=np.int64),
        "call_stream": np.asarray([r["stream"] for r in rows], dtype=np.int64),
        "call_frame": np.asarray([r["frame"] for r in rows], dtype=np.int64),
        "call_vector_index": np.asarray([
            vector_by_call.get(int(r["call_index"]), -1) for r in rows], dtype=np.int64),
        "vector_call_index": np.asarray(
            [v["call_index"] for v in vectors], dtype=np.int64),
        "vector_pair_index": np.asarray(
            [v["pair_index"] for v in vectors], dtype=np.int64),
        "vector_arm": np.asarray([v["arm"] for v in vectors], dtype="<U12"),
        "vector_graph_index": np.asarray(
            [graph_index[int(v["graph_id"])] for v in vectors], dtype=np.int64),
        "vector_seed": np.asarray([v["seed"] for v in vectors], dtype=np.int64),
        "vector_stream": np.asarray([v["stream"] for v in vectors], dtype=np.int64),
        "vector_frame": np.asarray([v["frame"] for v in vectors], dtype=np.int64),
        "raw_x_hat": np.stack([v["raw_x_hat"] for v in vectors]).astype(
            np.uint8, copy=False) if vectors else np.empty((0, N), dtype=np.uint8),
    }
    payload = sum(int(value.nbytes) for value in arrays.values())
    if payload > ARTIFACT_LIMIT_BYTES:
        raise ValueError("diagnostics.npz payload exceeds the frozen 20 MiB cap")
    return arrays


def _write_diagnostics(root: Path, arrays: Mapping[str, np.ndarray]) -> int:
    path = root / "diagnostics.npz"
    np.savez_compressed(path, **arrays)
    size = int(path.stat().st_size)
    if size > ARTIFACT_LIMIT_BYTES:
        raise ValueError("diagnostics.npz exceeds the frozen 20 MiB cap")
    return size


def _summarize(rows: list[Mapping[str, Any]], *, complete: bool,
               stop_reason: str | None, source_data: Mapping[str, Any] | None,
               pair_syndromes: Mapping[int, Mapping[str, np.ndarray]],
               vectors: list[Mapping[str, Any]], resource: Mapping[str, Any],
               batch_wall_s: float) -> dict[str, Any]:
    pairs_seen = {int(row["pair_index"]) for row in rows}
    grouped: dict[int, dict[str, Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(int(row["pair_index"]), {})[str(row["arm"])] = row
    complete_pairs = sum(set(value) == set(ARMS) for value in grouped.values())
    complete = bool(complete and len(rows) == MAX_CALLS
                    and complete_pairs == HOLDOUT_PAIRS and stop_reason is None)
    result: dict[str, Any] = {
        "track": "EXPLORE", "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "complete": complete,
        "terminal_status": "COMPLETE" if complete else "INCOMPLETE",
        "classification": "INCOMPLETE", "stop_reason": stop_reason,
        "attempted_decoder_calls": len(rows), "attempted_pairs": len(pairs_seen),
        "completed_pairs": int(complete_pairs), "raw_vectors_saved": len(vectors),
        "source_pairs": len(source_data["pairs"]) if source_data else 0,
        "pairs_with_own_syndromes": len(pair_syndromes),
        "syndrome_bits_per_attempted_arm": SYNDROME_BITS,
        "disclosed_syndrome_bits": len(rows) * SYNDROME_BITS,
        "tag_bits": 0, "verification": "NOT_IMPLEMENTED",
        "undetected": "NOT_MEASURED", "resource_measurement": dict(resource),
        "batch_wall_s": float(batch_wall_s),
        "integrity_violations": sum(
            str(row.get("failure_reason", "")).startswith("decoder_")
            or row.get("status") == "integrity_error" for row in rows),
        "resource_violations": int(stop_reason is not None
                                    and ("wall_cap" in stop_reason or "rss_cap" in stop_reason)),
        "authorization_violations": 0,
        "source_uuid": SOURCE_UUID, "source_path": SOURCE_NPZ_RELATIVE.as_posix(),
        "constructor_exact": None, "deep_exact": None, "delta": None,
        "per_arm_outcomes": None, "per_graph": None, "paired": None,
        "transitions": None, "nominal_edge_update_proxy": None,
        "nominal_edge_update_proxy_by_arm": None,
        "max_call_wall_s": None, "decoder_wall_s_by_arm": None,
        "iterations_sum_by_arm": None,
        "claim_ceiling": (
            "finite synthetic fixed-endpoint association on reused samples; "
            "no FER, f_eff, SKR, throughput, causality, route, qualification, "
            "publication, or cross-batch ranking claim"),
    }
    if not complete:
        result["partial_attempts_by_arm"] = {
            arm: sum(row.get("arm") == arm for row in rows) for arm in ARMS}
        return result

    counts = {}
    for arm in ARMS:
        selected = [row for row in rows if row["arm"] == arm]
        counts[arm] = {
            "attempted": len(selected),
            "exact": sum(row["exact"] is True for row in selected),
            "syndrome_valid_wrong": sum(
                row["syndrome_consistent_wrong"] is True for row in selected),
            "raw_syndrome_fail": sum(row["syndrome_accept"] is False for row in selected),
            "iterations_sum": sum(int(row["iterations"]) for row in selected),
            "wall_s_sum": float(sum(float(row["wall_s"]) for row in selected)),
            "max_call_wall_s": max(float(row["wall_s"]) for row in selected),
        }
    per_graph = {}
    for graph_id in GRAPH_SEEDS:
        selected = [pair for pair in grouped.values()
                    if int(pair["constructor"]["graph_id"]) == graph_id]
        c = sum(pair["constructor"]["exact"] is True for pair in selected)
        d = sum(pair["deep"]["exact"] is True for pair in selected)
        per_graph[str(graph_id)] = {
            "pairs": len(selected), "constructor_exact": int(c),
            "deep_exact": int(d), "delta_deep_minus_constructor": int(d - c),
        }
    paired = {"both": 0, "constructor_only": 0, "deep_only": 0, "neither": 0}
    categories = ("exact", "syndrome_valid_wrong", "raw_syndrome_fail")
    transitions = {"%s_to_%s" % (c, d): 0
                   for c in categories for d in categories}
    for pair in grouped.values():
        c_row, d_row = pair["constructor"], pair["deep"]
        c_ok, d_ok = c_row["exact"] is True, d_row["exact"] is True
        paired[{(True, True): "both", (True, False): "constructor_only",
                (False, True): "deep_only", (False, False): "neither"}[(c_ok, d_ok)]] += 1
        c_cat = ("exact" if c_ok else "syndrome_valid_wrong"
                 if c_row["syndrome_consistent_wrong"] else "raw_syndrome_fail")
        d_cat = ("exact" if d_ok else "syndrome_valid_wrong"
                 if d_row["syndrome_consistent_wrong"] else "raw_syndrome_fail")
        transitions["%s_to_%s" % (c_cat, d_cat)] += 1
    c_exact, d_exact = counts["constructor"]["exact"], counts["deep"]["exact"]
    c_iter = counts["constructor"]["iterations_sum"]
    d_iter = counts["deep"]["iterations_sum"]
    result.update({
        "classification": "COMPLETE_DESCRIPTIVE_ONLY",
        "constructor_exact": int(c_exact), "deep_exact": int(d_exact),
        "delta": int(d_exact - c_exact),
        "per_arm_outcomes": counts, "per_graph": per_graph,
        "paired": paired, "transitions": transitions,
        "iterations_sum_by_arm": {
            "constructor": int(c_iter), "deep": int(d_iter)},
        "decoder_wall_s_by_arm": {
            arm: counts[arm]["wall_s_sum"] for arm in ARMS},
        "max_call_wall_s": max(row["wall_s"] for row in rows),
        "nominal_edge_update_proxy_by_arm": {
            "constructor": int(EDGE_COUNT * c_iter),
            "deep": int(EDGE_COUNT * d_iter)},
        "nominal_edge_update_proxy": int(EDGE_COUNT * (c_iter + d_iter)),
    })
    return result


def execute_batch(
        *, out_root: str | Path,
        diagnostic_reader: Callable[[], Mapping[str, Any]],
        decode_fns: Mapping[str, Callable[[np.ndarray, np.ndarray, np.ndarray], Any]],
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str = COMMAND) -> dict[str, Any]:
    if not callable(diagnostic_reader):
        raise ValueError("an explicit diagnostic_reader callback is required")
    if (not isinstance(decode_fns, Mapping) or set(decode_fns) != set(ARMS)
            or any(not callable(decode_fns[arm]) for arm in ARMS)):
        raise ValueError("decode_fns must explicitly provide constructor and deep decoders")
    root = validate_out_root(out_root, repo_root=repo_root)
    rss_reader = d5._rss_bytes if rss_fn is None else rss_fn
    started = float(now())
    rss_samples = 0
    max_rss: int | None = None
    rows: list[dict[str, Any]] = []
    vectors: list[dict[str, Any]] = []
    pair_syndromes: dict[int, dict[str, np.ndarray]] = {}
    source_data: dict[str, Any] | None = None
    stop_reason: str | None = None
    source_read_wall_s: float | None = None

    def sampled_rss() -> int | None:
        nonlocal rss_samples, max_rss
        value = rss_reader()
        if value is None:
            return None
        value = int(value)
        rss_samples += 1
        max_rss = value if max_rss is None else max(max_rss, value)
        return value

    def budget_stop() -> str | None:
        if max(float(now()) - started, 0.0) >= WALL_CAP_S:
            return "total_wall_cap"
        value = sampled_rss()
        if value is not None and value >= RSS_CAP_BYTES:
            return "rss_cap"
        return None

    manifest = _initial_manifest(command)
    _start_outputs(root, manifest)
    try:
        stop_reason = budget_stop()
        if stop_reason:
            raise _StopBatch(stop_reason)
        read_started = float(now())
        source_arrays = diagnostic_reader()
        source_read_wall_s = max(float(now()) - read_started, 0.0)
        source_data = extract_source_data(source_arrays)
        stop_reason = budget_stop()
        if stop_reason:
            raise _StopBatch(stop_reason)
        prior = _prior_matrix()

        for pair in source_data["pairs"]:
            stop_reason = budget_stop()
            if stop_reason:
                raise _StopBatch(stop_reason)
            graph = source_data["graphs"][pair["graph_id"]]
            paired_from_shared_helper = prior_runner.paired_arm_data(
                graph["constructor"], graph["deep"], pair["truth"], prior)
            paired = {
                "constructor": paired_from_shared_helper["control"],
                "deep": paired_from_shared_helper["candidate"],
            }
            pair_syndromes[pair["pair_index"]] = {
                arm: np.asarray(paired[arm]["syndrome"], dtype=np.uint8).copy()
                for arm in ARMS}
            for arm in arm_order(pair["frame"]):
                stop_reason = budget_stop()
                if stop_reason:
                    raise _StopBatch(stop_reason)
                raw_vector: np.ndarray | None = None

                def captured_decode(h, arm_prior, syndrome):
                    nonlocal raw_vector
                    decoded = decode_fns[arm](h, arm_prior, syndrome)
                    try:
                        value = np.asarray(decoded.x_hat)
                        if (value.shape == (N,)
                                and np.issubdtype(value.dtype, np.integer)
                                and np.all((value >= 0) & (value < Q))):
                            raw_vector = value.copy()
                    except (AttributeError, TypeError, ValueError):
                        raw_vector = None
                    return decoded

                observed, issue = prior_runner.decode_observation(
                    captured_decode, paired[arm]["dense"], paired[arm]["prior"],
                    pair["truth"], paired[arm]["syndrome"], now=now,
                    rss_fn=sampled_rss)
                call_index = len(rows)
                graph_record = source_data["graphs"][pair["graph_id"]]
                row = {
                    "call_index": call_index,
                    "pair_index": pair["pair_index"], "graph_id": pair["graph_id"],
                    "stream": pair["stream"], "frame": pair["frame"],
                    "seed": pair["seed"], "arm": arm,
                    "decoder_status": observed["status"],
                    "status": ("integrity_error" if issue.startswith("decoder_")
                               else observed["status"]),
                    "iterations": int(observed["iterations"]),
                    "raw_vector_saved": raw_vector is not None,
                    "raw_symbols_equal": bool(observed["exact"]),
                    "syndrome_accept": bool(observed["syndrome_accept"]),
                    "syndrome_consistent_wrong": bool(
                        observed["syndrome_consistent_wrong"]),
                    "exact": bool(observed["exact"] and observed["syndrome_accept"]),
                    "wall_s": float(observed["wall_s"]), "rss_b": observed["rss_b"],
                    "syndrome_bits": SYNDROME_BITS,
                    "failure_reason": issue,
                    "source_uuid": SOURCE_UUID,
                    "source_path": SOURCE_NPZ_RELATIVE.as_posix(),
                    "constructor_source_uuid": graph_record["constructor_source_uuid"],
                    "constructor_source_path": graph_record["constructor_source_path"],
                    "constructor_source_matrix_index": graph_record[
                        "constructor_source_matrix_index"],
                    "constructor_source_attempt_j": graph_record[
                        "constructor_source_attempt_j"],
                    "constructor_source_seed": graph_record["constructor_source_seed"],
                    "constructor_source_graph_id": graph_record[
                        "constructor_source_graph_id"],
                    "source_graph_index": graph_record["source_graph_index"],
                    "source_constructor_row_index": graph_record[
                        "source_constructor_row_index"],
                    "source_deep_row_index": graph_record["source_deep_row_index"],
                    "deep_profile_index": graph_record["deep_profile_index"],
                    "deep_graph_index": graph_record["deep_graph_index"],
                }
                rows.append(row)
                if raw_vector is not None:
                    vectors.append({
                        "call_index": call_index,
                        "pair_index": pair["pair_index"], "graph_id": pair["graph_id"],
                        "arm": arm, "seed": pair["seed"],
                        "stream": pair["stream"], "frame": pair["frame"],
                        "raw_x_hat": raw_vector,
                    })
                _append_row(root, row)
                if issue:
                    stop_reason = issue
                else:
                    stop_reason = budget_stop()
                if stop_reason:
                    raise _StopBatch(stop_reason)
    except _StopBatch as exc:
        if stop_reason is None:
            stop_reason = str(exc)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        if stop_reason is None:
            stop_reason = "source_or_operator_error:%s:%s" % (type(exc).__name__, exc)

    complete = stop_reason is None and len(rows) == MAX_CALLS
    resource = {
        "rss_samples": rss_samples, "sampled_max_rss_bytes": max_rss,
        "rss_peak_is_continuous": False,
        "source_read_wall_s": source_read_wall_s,
        "batch_wall_cap_s": WALL_CAP_S, "per_call_wall_cap_s": CALL_CAP_S,
        "rss_cap_bytes": RSS_CAP_BYTES,
    }
    arrays = _diagnostics_arrays(source_data, pair_syndromes, rows, vectors)
    artifact_bytes = _write_diagnostics(root, arrays)
    resource["diagnostics_npz_bytes"] = artifact_bytes
    summary = _summarize(
        rows, complete=complete, stop_reason=stop_reason,
        source_data=source_data, pair_syndromes=pair_syndromes,
        vectors=vectors, resource=resource,
        batch_wall_s=max(float(now()) - started, 0.0))
    _write_json(root / "summary.json", summary)
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as handle:
        handle.write(
            "\n## Single frozen attempt\n\n"
            "- terminal_status: %s\n- stop_reason: %s\n"
            "- source_reads: %d\n- decoder_calls: %d\n"
            "- attempted_pairs: %d\n- saved_vectors: %d\n"
            % (summary["terminal_status"], stop_reason or "none",
               int(source_read_wall_s is not None), len(rows),
               len({int(row["pair_index"]) for row in rows}), len(vectors)))
    manifest.update({
        "status": summary["terminal_status"],
        "classification": summary["classification"],
        "stop_reason": stop_reason,
        "source_read_wall_s": source_read_wall_s,
        "source_rows": len(source_data["pairs"]) if source_data else 0,
        "attempted_decoder_calls": len(rows),
        "artifact_files": ["manifest.json", "summary.json", "frame_records.csv",
                           "diagnostics.npz", "EXPLORATION_LOG.md"],
    })
    _write_json(root / "manifest.json", manifest)

    # This completion checkpoint includes all first-pass data, summary, log,
    # and manifest writes. The small terminal status record below is after the
    # checkpoint and is not recursively timed against itself.
    final_wall_s = max(float(now()) - started, 0.0)
    final_rss_b = sampled_rss()
    final_checkpoint_stops = []
    if final_wall_s >= WALL_CAP_S:
        final_checkpoint_stops.append("total_wall_cap_after_first_pass_artifacts")
    if final_rss_b is not None and final_rss_b >= RSS_CAP_BYTES:
        final_checkpoint_stops.append("rss_cap_after_first_pass_artifacts")
    final_checkpoint = {
        "stage": "after_first_pass_artifacts",
        "wall_s": final_wall_s,
        "sampled_rss_bytes": final_rss_b,
        "stop_reasons": final_checkpoint_stops,
        "status_record_write_after_checkpoint_excluded_from_recursive_timing": True,
    }
    resource.update({
        "rss_samples": rss_samples,
        "sampled_max_rss_bytes": max_rss,
        "final_checkpoint": final_checkpoint,
    })
    initial_stop_reason = stop_reason
    if stop_reason is None and final_checkpoint_stops:
        stop_reason = final_checkpoint_stops[0]
    summary = _summarize(
        rows, complete=complete and not final_checkpoint_stops,
        stop_reason=stop_reason, source_data=source_data,
        pair_syndromes=pair_syndromes, vectors=vectors,
        resource=resource, batch_wall_s=final_wall_s)
    if final_checkpoint_stops:
        summary["resource_violations"] = max(
            int(summary["resource_violations"]), 1)
    summary["final_checkpoint"] = final_checkpoint
    summary["first_stop_reason"] = initial_stop_reason
    summary["final_checkpoint_stop_reasons"] = final_checkpoint_stops
    with (root / "EXPLORATION_LOG.md").open("a", encoding="utf-8") as handle:
        handle.write(
            "\n## Terminal artifact-write budget checkpoint\n\n"
            "- stage: after first-pass diagnostics, summary, attempt-log, and manifest writes\n"
            "- final_terminal_status: %s\n- final_classification: %s\n"
            "- this checkpoint status supersedes the initial attempt status above\n"
            "- batch_wall_s: %.9f\n- sampled_rss_bytes: %s\n"
            "- final_checkpoint_stop_reasons: %s\n"
            "- terminal summary/manifest/log state write follows this checkpoint and is not recursively timed\n"
            % (summary["terminal_status"], summary["classification"],
               final_wall_s, "null" if final_rss_b is None else str(final_rss_b),
               ",".join(final_checkpoint_stops) or "none"))
    manifest.update({
        "status": summary["terminal_status"],
        "classification": summary["classification"],
        "stop_reason": stop_reason,
        "first_stop_reason": initial_stop_reason,
        "final_checkpoint_stop_reasons": final_checkpoint_stops,
        "batch_wall_s": final_wall_s,
        "final_checkpoint": final_checkpoint,
        "terminal_status_write_self_timing": "excluded_after_completion_checkpoint",
    })
    _write_json(root / "summary.json", summary)
    _write_json(root / "manifest.json", manifest)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GF(32) constructor/deep-label endpoint EXPLORE diagnostic")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--execute", action="store_true",
                       help="run the one frozen source-replay attempt")
    modes.add_argument("--dry-run", action="store_true",
                       help="perform source-free T0 and fresh-root checks")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE))
    return parser


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    if not args.execute:
        result = dry_run(args.out_root)
    else:
        result = execute_batch(
            out_root=args.out_root,
            diagnostic_reader=_default_diagnostic_reader(),
            decode_fns=_bind_production_decoders(), command=COMMAND)
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
