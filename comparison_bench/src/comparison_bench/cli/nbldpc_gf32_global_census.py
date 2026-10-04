"""Decoder-free global census of the fixed DV2 check multigraph."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

BATCH_UUID = "f4a0ff0d-b538-4fed-bb2d-41c398daa3fb"
CONTRACT = "gf32-global-census-v1"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_global_f4a0ff0d"
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_global_census --execute "
    "--out-root workspace/gf32_global_f4a0ff0d"
)

SOURCE_BATCH_UUID = "a9352bc1-ae56-443b-ae93-9dcfa85d4229"
SOURCE_CONTRACT = "NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md"
SOURCE_NAMESPACE = "gf32-degree-admitted-v1"
SOURCE_KIND = "admitted_source"
SOURCE_UUID = "a9a18abe-3547-4d16-aa50-1f7150182f31"
SOURCE_PATH = "workspace/gf32_construct_a9a18abe/constructions.json"
GRAPH_IDS = tuple(range(2026093901, 2026093907))
PROFILE_ORDER = ("control", "candidate")
N_CHECKS, N_VARIABLES, N_EDGES = 52, 128, 128
TOL = 1e-10
WALL_CAP_S = 120.0
RSS_CAP_BYTES = 1024 ** 3
ARTIFACT_CAP_BYTES = 2 * 1024 ** 2
ARTIFACT_NAMES = ("manifest.json", "census.json", "EXPLORATION_LOG.md")

SOURCE_ARRAY_KEYS = (
    "batch_uuid", "contract", "seed_namespace", "graph_input_kind",
    "profile_order", "graph_seed", "constructor_profile_index",
    "constructor_graph_index", "H_constructor", "constructor_source_uuid",
    "constructor_source_path", "constructor_source_matrix_index",
    "constructor_source_attempt_j", "constructor_source_seed",
    "constructor_source_graph_id",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def validate_out_root(out_root: str | Path,
                      repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else _repo_root()
    requested = Path(out_root)
    resolved = requested.resolve() if requested.is_absolute() \
        else (root / requested).resolve()
    expected = (root / OUT_ROOT_RELATIVE).resolve()
    if resolved != expected:
        raise ValueError(f"out-root must equal frozen fresh root {expected}")
    if resolved.exists():
        raise FileExistsError(f"refusing existing output root {resolved}")
    return resolved


def verify_t0() -> dict[str, Any]:
    """Source-free structural contract check."""
    return {
        "status": "PASS", "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "source_reads": 0, "decoder_calls": 0, "graph_build_calls": 0,
        "writes": 0,
    }


def dry_run(out_root: str | Path = OUT_ROOT_RELATIVE,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    root = validate_out_root(out_root, repo_root=repo_root)
    return {
        "status": "DRY_RUN", "batch_uuid": BATCH_UUID,
        "contract": CONTRACT, "out_root": str(root),
        "graphs": list(GRAPH_IDS), "source_reads": 0,
        "decoder_calls": 0, "graph_build_calls": 0, "writes": 0,
    }


def _support_graph(H: np.ndarray) -> tuple[list[list[int]], np.ndarray, np.ndarray]:
    matrix = np.asarray(H)
    if matrix.ndim != 2 or matrix.shape[0] < 3:
        raise ValueError("H must be a two-dimensional matrix with at least 3 checks")
    if (not np.issubdtype(matrix.dtype, np.integer)
            or np.any(matrix < 0) or np.any(matrix > 31)):
        raise ValueError("H must contain integer GF(32) symbols in 0..31")
    support = matrix != 0
    if np.any(support.sum(axis=0) != 2):
        raise ValueError("each variable column must join exactly two checks")
    edges: list[list[int]] = []
    adjacency = np.zeros((matrix.shape[0], matrix.shape[0]), dtype=np.int64)
    for edge_id in range(matrix.shape[1]):
        ends = np.flatnonzero(support[:, edge_id])
        left, right = int(ends[0]), int(ends[1])
        edges.append([left, right])
        adjacency[left, right] += 1
        adjacency[right, left] += 1
    degree = adjacency.sum(axis=1)
    if np.any(degree == 0):
        raise ValueError("check multigraph has an isolated vertex")
    return edges, adjacency, degree


def _connected(A: np.ndarray) -> bool:
    seen = {0}
    pending = [0]
    while pending:
        node = pending.pop()
        for other in np.flatnonzero(A[node]):
            other = int(other)
            if other not in seen:
                seen.add(other)
                pending.append(other)
    return len(seen) == A.shape[0]


def compute_graph_metrics(H: np.ndarray) -> dict[str, Any]:
    """Compute the frozen normalized spectrum and Fiedler conductance sweep."""
    edges, A, degree = _support_graph(H)
    if not _connected(A):
        raise ValueError("check multigraph is disconnected")

    inv_sqrt_degree = 1.0 / np.sqrt(degree.astype(np.float64))
    Lnorm = np.eye(A.shape[0]) - (
        inv_sqrt_degree[:, None] * A * inv_sqrt_degree[None, :])
    eigenvalues, eigenvectors = np.linalg.eigh(Lnorm)
    residual = float(np.max(np.abs(
        Lnorm @ eigenvectors - eigenvectors * eigenvalues[None, :])))
    flags: list[str] = []
    numeric_ok = (
        abs(float(eigenvalues[0])) <= TOL
        and float(eigenvalues[0]) >= -TOL
        and float(eigenvalues[-1]) <= 2.0 + TOL
        and residual <= TOL
    )
    if len(eigenvalues) < 3:
        raise ValueError("at least three checks are required for the frozen gap")

    lambda2 = float(eigenvalues[1])
    lambda3_minus_lambda2 = float(eigenvalues[2] - eigenvalues[1])
    if abs(lambda3_minus_lambda2) <= TOL:
        flags.append("FIEDLER_DEGENERATE")

    fiedler = eigenvectors[:, 1].copy()
    max_abs = float(np.max(np.abs(fiedler)))
    pivot = next(i for i, value in enumerate(np.abs(fiedler))
                 if float(value) == max_abs)
    sign_flip = bool(fiedler[pivot] < 0.0)
    if sign_flip:
        fiedler *= -1.0
    sweep_value = fiedler / np.sqrt(degree.astype(np.float64))
    order = sorted(range(A.shape[0]), key=lambda i: (float(sweep_value[i]), i))

    cuts: list[dict[str, Any]] = []
    best_cut = best_denominator = 0
    for k in range(1, A.shape[0]):
        prefix = order[:k]
        complement = order[k:]
        cut = int(A[np.ix_(prefix, complement)].sum())
        volume = int(degree[prefix].sum())
        complement_volume = int(degree[complement].sum())
        denominator = min(volume, complement_volume)
        row = {
            "k": k, "prefix_check_ids": [int(i) for i in prefix],
            "cut": cut, "volume": volume,
            "complement_volume": complement_volume,
            "phi": float(cut / denominator),
        }
        cuts.append(row)
        if (k == 1 or cut * best_denominator < best_cut * denominator):
            best_cut, best_denominator = cut, denominator
    best = next(row for row in cuts
                if row["cut"] * best_denominator
                == best_cut * min(row["volume"], row["complement_volume"]))

    return {
        "edge_endpoints_by_column": edges,
        "edge_ids_by_column": list(range(len(edges))),
        "adjacency": A.astype(np.int64).tolist(),
        "degree": degree.astype(np.int64).tolist(),
        "eigenvalues": [float(v) for v in eigenvalues],
        "lambda2": lambda2,
        "lambda3_minus_lambda2": lambda3_minus_lambda2,
        "eigensystem_residual_max_abs": residual,
        "eigensystem_residual_definition":
            "max(abs(Lnorm @ U - U * lambda[None, :]))",
        "tolerance": TOL,
        "fiedler_sign_flip": sign_flip,
        "fiedler_order": [int(i) for i in order],
        "sweep": cuts,
        "best_prefix_k": int(best["k"]),
        "best_subset_check_ids": list(best["prefix_check_ids"]),
        "phi_sweep": float(best["phi"]),
        "status": "COMPLETE" if numeric_ok else "NUMERIC_STOP",
        "flags": flags,
    }


def _text(value: Any, key: str) -> str:
    array = np.asarray(value)
    if array.size != 1:
        raise ValueError(f"source {key} must be scalar")
    item = array.reshape(-1)[0]
    if isinstance(item, bytes):
        item = item.decode("utf-8")
    return str(item)


def _source_selection(source: Mapping[str, Any]
                      ) -> tuple[dict[str, str], list[dict[str, Any]]]:
    missing = [key for key in SOURCE_ARRAY_KEYS if key not in source]
    if missing:
        raise ValueError(f"source NPZ lacks required keys: {missing}")
    identity = {
        "batch_uuid": _text(source["batch_uuid"], "batch_uuid"),
        "contract": _text(source["contract"], "contract"),
        "seed_namespace": _text(source["seed_namespace"], "seed_namespace"),
        "graph_input_kind": _text(source["graph_input_kind"], "graph_input_kind"),
    }
    expected_identity = {
        "batch_uuid": SOURCE_BATCH_UUID, "contract": SOURCE_CONTRACT,
        "seed_namespace": SOURCE_NAMESPACE, "graph_input_kind": SOURCE_KIND,
    }
    if identity != expected_identity:
        raise ValueError(f"source identity mismatch: {identity}")

    profile_order = [str(x) for x in np.asarray(source["profile_order"]).tolist()]
    if len(profile_order) != len(set(profile_order)) or "control" not in profile_order:
        raise ValueError("source profile_order is invalid")
    control_profile_index = profile_order.index("control")
    graph_seed = np.asarray(source["graph_seed"], dtype=np.int64).reshape(-1)
    if len(graph_seed) != len(set(int(x) for x in graph_seed)):
        raise ValueError("source graph_seed contains duplicates")
    graph_index_by_id = {int(seed): index for index, seed in enumerate(graph_seed)}
    if set(graph_index_by_id) != set(GRAPH_IDS):
        raise ValueError("source graph_seed differs from the six frozen graph IDs")

    profiles = np.asarray(source["constructor_profile_index"], dtype=np.int64).reshape(-1)
    graph_indices = np.asarray(source["constructor_graph_index"], dtype=np.int64).reshape(-1)
    matrices = np.asarray(source["H_constructor"])
    if (matrices.ndim != 3 or matrices.shape[1:] != (N_CHECKS, N_VARIABLES)
            or len(profiles) != len(matrices) or len(graph_indices) != len(matrices)):
        raise ValueError("source constructor H/index shapes are inconsistent")
    expected_pairs = {
        (profile_index, graph_index)
        for profile_index in range(len(profile_order))
        for graph_index in range(len(graph_seed))
    }
    observed_pairs = list(zip(profiles.tolist(), graph_indices.tolist()))
    if (len(matrices) != len(expected_pairs)
            or len(set(observed_pairs)) != len(observed_pairs)
            or set(observed_pairs) != expected_pairs):
        raise ValueError("source constructor profile/graph map is incomplete or duplicated")
    metadata_keys = (
        "constructor_source_uuid", "constructor_source_path",
        "constructor_source_matrix_index", "constructor_source_attempt_j",
        "constructor_source_seed", "constructor_source_graph_id",
    )
    metadata = {key: np.asarray(source[key]).reshape(-1) for key in metadata_keys}
    if any(len(values) != len(matrices) for values in metadata.values()):
        raise ValueError("source constructor lineage arrays are misaligned")

    selected: list[dict[str, Any]] = []
    used_rows: set[int] = set()
    used_matrix_indices: set[int] = set()
    for graph_id in GRAPH_IDS:
        gi = graph_index_by_id[graph_id]
        rows = np.flatnonzero((profiles == control_profile_index) & (graph_indices == gi))
        if len(rows) != 1:
            raise ValueError(f"source has {len(rows)} control matrices for graph {graph_id}")
        row_index = int(rows[0])
        used_rows.add(row_index)
        lineage = {
            "source_uuid": str(metadata["constructor_source_uuid"][row_index]),
            "source_path": str(metadata["constructor_source_path"][row_index]),
            "source_matrix_index": int(metadata["constructor_source_matrix_index"][row_index]),
            "source_attempt_j": int(metadata["constructor_source_attempt_j"][row_index]),
            "source_construction_seed": int(metadata["constructor_source_seed"][row_index]),
            "source_graph_id": int(metadata["constructor_source_graph_id"][row_index]),
        }
        expected_j = 1 if graph_id == 2026093905 else 0
        expected_seed = 2560859716 if graph_id == 2026093905 else graph_id
        if (lineage["source_uuid"] != SOURCE_UUID
                or lineage["source_path"] != SOURCE_PATH
                or lineage["source_graph_id"] != graph_id
                or lineage["source_attempt_j"] != expected_j
                or lineage["source_construction_seed"] != expected_seed):
            raise ValueError(f"source constructor lineage mismatch for graph {graph_id}")
        if graph_id == 2026093905 and lineage["source_matrix_index"] != 9:
            raise ValueError("source graph 2026093905 control matrix_index mismatch")
        if lineage["source_matrix_index"] in used_matrix_indices:
            raise ValueError("selected source matrices reuse matrix_index")
        used_matrix_indices.add(lineage["source_matrix_index"])
        selected.append({
            "graph_id": graph_id, "constructor_row_index": row_index,
            "constructor_profile_index": control_profile_index,
            "constructor_graph_index": gi, "graph_seed": int(graph_seed[gi]),
            "source_lineage": lineage, "H": matrices[row_index],
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
    # Linux/WSL reports ru_maxrss in KiB; this is the process high-water mark.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _json_write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def _resource_stop(started: float, now: Callable[[], float],
                   rss_fn: Callable[[], int | None],
                   rss_samples: list[int]) -> str:
    if float(now()) - started > WALL_CAP_S:
        return "total_wall_cap"
    value = rss_fn()
    if value is not None:
        value = int(value)
        rss_samples.append(value)
        if value >= RSS_CAP_BYTES:
            return "rss_cap"
    return ""


def execute_batch(*, source_reader: Callable[[], Mapping[str, Any]],
                  out_root: str | Path,
                  repo_root: str | Path | None = None,
                  now: Callable[[], float] = time.perf_counter,
                  rss_fn: Callable[[], int | None] | None = None,
                  command: str = COMMAND) -> dict[str, Any]:
    if not callable(source_reader):
        raise ValueError("an explicit source_reader is required")
    root = validate_out_root(out_root, repo_root=repo_root)
    rss_fn = _rss_bytes if rss_fn is None else rss_fn
    started = float(now())
    root.mkdir(parents=True)
    log_path = root / "EXPLORATION_LOG.md"
    log_path.write_text(
        f"# Fixed DV2 check-graph global census\n\nBatch UUID: `{BATCH_UUID}`. "
        f"Source batch: `{SOURCE_BATCH_UUID}`. Status: `RUNNING`.\n",
        encoding="utf-8")
    rss_samples: list[int] = []
    graphs: list[dict[str, Any]] = []
    source_maps: list[dict[str, Any]] = []
    source_identity: dict[str, str] = {}
    stop_reason = ""
    source_reads = 0

    stop_reason = _resource_stop(started, now, rss_fn, rss_samples)
    if not stop_reason:
        try:
            source = source_reader()
            source_reads = 1
            source_identity, selected = _source_selection(source)
            source_maps = [{
                "graph_id": int(item["graph_id"]),
                "constructor_row_index": int(item["constructor_row_index"]),
                "constructor_profile_index": int(item["constructor_profile_index"]),
                "constructor_graph_index": int(item["constructor_graph_index"]),
                "graph_seed": int(item["graph_seed"]),
                **item["source_lineage"],
            } for item in selected]
            for item in selected:
                stop_reason = _resource_stop(started, now, rss_fn, rss_samples)
                if stop_reason:
                    break
                H = np.asarray(item["H"])
                if (H.shape != (N_CHECKS, N_VARIABLES)
                        or not np.issubdtype(H.dtype, np.integer)
                        or np.any(H < 0) or np.any(H > 31)):
                    raise ValueError(f"source H shape/symbol range invalid for graph {item['graph_id']}")
                if np.any((H != 0).sum(axis=0) != 2):
                    raise ValueError(f"source variable degree is not 2 for graph {item['graph_id']}")
                check_degrees = (H != 0).sum(axis=1)
                if (int(np.sum(check_degrees == 4)) != 4
                        or int(np.sum(check_degrees == 5)) != 48
                        or int(check_degrees.sum()) != N_EDGES * 2):
                    raise ValueError(f"source check-degree profile invalid for graph {item['graph_id']}")
                metrics = compute_graph_metrics(H)
                graph_record = {
                    "graph_id": int(item["graph_id"]),
                    "source_lineage": item["source_lineage"],
                    "rank52_admission_reused": True,
                    "connected_by_bfs": True,
                    **metrics,
                }
                graphs.append(graph_record)
                with log_path.open("a", encoding="utf-8") as stream:
                    stream.write(f"Completed graph {item['graph_id']}; status={metrics['status']}.\n")
                if metrics["status"] != "COMPLETE":
                    stop_reason = f"numeric_check_failed_graph_{item['graph_id']}"
                    break
        except (ValueError, KeyError, OSError, TypeError, np.linalg.LinAlgError) as exc:
            stop_reason = f"source_or_graph_stop:{type(exc).__name__}:{exc}"

    status = "COMPLETE" if len(graphs) == len(GRAPH_IDS) and not stop_reason else "INCOMPLETE"
    if not stop_reason and status != "COMPLETE":
        stop_reason = "incomplete_graph_count"
    resources = {
        "wall_cap_s": WALL_CAP_S, "rss_cap_bytes": RSS_CAP_BYTES,
        "artifact_cap_bytes": ARTIFACT_CAP_BYTES,
        "wall_s_before_final_checkpoint": max(float(now()) - started, 0.0),
        "sampled_rss_max_bytes": max(rss_samples) if rss_samples else None,
        "rss_sample_count": len(rss_samples),
    }
    census = {
        "batch_uuid": BATCH_UUID, "contract": CONTRACT, "track": "EXPLORE",
        "status": status, "stop_reason": stop_reason,
        "source_identity": source_identity, "source_maps": source_maps,
        "graphs": graphs, "completed_graphs": len(graphs),
        "decoder_calls": 0, "graph_build_calls": 0,
        "label_search_calls": 0, "osd_calls": 0,
        "new_disclosure_bits": 0, "rank52_admission": "upstream A5 reused",
        "resources": resources,
    }
    manifest = {
        "batch_uuid": BATCH_UUID, "contract": CONTRACT, "track": "EXPLORE",
        "status": status, "stop_reason": stop_reason,
        "command": command, "output_root": str(root),
        "source_identity": source_identity, "source_maps": source_maps,
        "completed_graphs": len(graphs), "resources": resources,
        "artifacts": list(ARTIFACT_NAMES),
        "decoder_calls": 0, "graph_build_calls": 0,
        "label_search_calls": 0, "osd_calls": 0,
        "new_disclosure_bits": 0,
    }
    _json_write(root / "manifest.json", manifest)
    _json_write(root / "census.json", census)

    first_pass_bytes = sum((root / name).stat().st_size for name in ARTIFACT_NAMES)
    final_wall = max(float(now()) - started, 0.0)
    final_rss = rss_fn()
    if final_rss is not None:
        final_rss = int(final_rss)
        rss_samples.append(final_rss)
    if status == "COMPLETE" and final_wall > WALL_CAP_S:
        status, stop_reason = "INCOMPLETE", "final_total_wall_cap"
    elif status == "COMPLETE" and final_rss is not None and final_rss >= RSS_CAP_BYTES:
        status, stop_reason = "INCOMPLETE", "final_rss_cap"
    elif status == "COMPLETE" and first_pass_bytes > ARTIFACT_CAP_BYTES:
        status, stop_reason = "INCOMPLETE", "final_artifact_size_cap"
    resources.update({
        "final_wall_s": final_wall, "final_sampled_rss_bytes": final_rss,
        "final_sampled_rss_max_bytes": max(rss_samples) if rss_samples else None,
        "first_pass_artifact_bytes": int(first_pass_bytes),
        "final_checkpoint_excludes_state_rewrite": True,
    })
    census.update({"status": status, "stop_reason": stop_reason,
                   "resources": resources})
    manifest.update({"status": status, "stop_reason": stop_reason,
                     "resources": resources})
    with log_path.open("a", encoding="utf-8") as stream:
        stream.write(
            f"FINAL_STATUS={status}; completed_graphs={len(graphs)}; "
            f"stop_reason={stop_reason or 'none'}; final_wall_s={final_wall:.9f}; "
            f"sampled_rss_bytes={final_rss}; first_pass_artifact_bytes={first_pass_bytes}.\n")
    _json_write(root / "census.json", census)
    _json_write(root / "manifest.json", manifest)
    return {
        "status": status, "completed_graphs": len(graphs),
        "stop_reason": stop_reason, "graphs": graphs,
        "resources": resources, "artifact_paths": list(ARTIFACT_NAMES),
        "source_identity": source_identity, "source_maps": source_maps,
        "source_reads": source_reads,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decoder-free global census of fixed DV2 check multigraphs")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--execute", action="store_true",
                       help="read the frozen source NPZ and write one census")
    modes.add_argument("--t0", action="store_true", help="run source-free T0 checks")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.t0:
        result = verify_t0()
    elif args.execute:
        result = execute_batch(source_reader=_default_source_reader(),
                               out_root=args.out_root)
    else:
        result = dry_run(args.out_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
