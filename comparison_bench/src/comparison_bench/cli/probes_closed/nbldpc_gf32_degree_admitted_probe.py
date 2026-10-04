"""Matched GF32 degree-profile probe using the accepted constructor canary."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from comparison_bench.cli.probes_closed import nbldpc_gf32_degree_probe as degree_probe

CONTRACT = "NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md"
BATCH_UUID = "a9352bc1-ae56-443b-ae93-9dcfa85d4229"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_degree_admitted_a9352bc1"
SEED_PREFIX = "gf32-degree-admitted-v1"
SOURCE_UUID = "a9a18abe-3547-4d16-aa50-1f7150182f31"
SOURCE_CONTRACT = "NBLDPC-GF32-CONSTRUCTION-CANARY-20261001/PREREG_AND_AUTH.md"
SOURCE_NAMESPACE = "gf32-construct-v1"
SOURCE_JSON_RELATIVE = (
    Path("workspace") / "gf32_construct_a9a18abe" / "constructions.json")
GRAPH_SEEDS = tuple(degree_probe.GRAPH_SEEDS)
PROFILE_ORDER = tuple(degree_probe.PROFILE_ORDER)
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.probes_closed.nbldpc_gf32_degree_admitted_probe "
    "--execute --out-root workspace/gf32_degree_admitted_a9352bc1"
)


def selected_graphs(doc: Mapping[str, Any]
                    ) -> dict[tuple[int, str], dict[str, Any]]:
    """Join only the source canary's selected matrices by explicit matrix_index."""
    if (not isinstance(doc, Mapping)
            or doc.get("batch_uuid") != SOURCE_UUID
            or doc.get("contract") != SOURCE_CONTRACT
            or doc.get("seed_namespace") != SOURCE_NAMESPACE
            or doc.get("terminal_status") != "COMPLETE"
            or doc.get("classification") != "CONSTRUCTION_FEASIBLE"
            or doc.get("complete_all_groups") is not True
            or doc.get("stop_reason") not in (None, "")):
        raise ValueError("source construction canary identity/status is not admitted")
    matrices = doc.get("matrices")
    attempts = doc.get("attempts")
    groups = doc.get("groups")
    if (not isinstance(matrices, list) or not isinstance(attempts, list)
            or not isinstance(groups, list) or len(groups) != len(GRAPH_SEEDS)
            or int(doc.get("matrix_count", -1)) != len(matrices)):
        raise ValueError("source construction canary graph records are incomplete")

    matrices_by_index: dict[int, Mapping[str, Any]] = {}
    for record in matrices:
        if not isinstance(record, Mapping) or record.get("matrix_index") is None:
            raise ValueError("source matrix record has no matrix_index")
        index = int(record["matrix_index"])
        if index in matrices_by_index:
            raise ValueError("source construction canary repeats a matrix_index")
        matrices_by_index[index] = record

    attempts_by_matrix_index: dict[int, Mapping[str, Any]] = {}
    for record in attempts:
        if not isinstance(record, Mapping):
            raise ValueError("source attempt record is malformed")
        index = record.get("matrix_index")
        if index is None:
            continue
        index = int(index)
        if index in attempts_by_matrix_index:
            raise ValueError("source attempts repeat a matrix_index")
        attempts_by_matrix_index[index] = record

    groups_by_id: dict[int, Mapping[str, Any]] = {}
    for group in groups:
        if not isinstance(group, Mapping) or group.get("graph_id") is None:
            raise ValueError("source selected group is malformed")
        graph_id = int(group["graph_id"])
        if graph_id in groups_by_id:
            raise ValueError("source canary repeats a graph_id")
        groups_by_id[graph_id] = group
    if set(groups_by_id) != set(GRAPH_SEEDS):
        raise ValueError("source canary graph IDs do not match the frozen plan")

    selected: dict[tuple[int, str], dict[str, Any]] = {}
    used_matrix_indices: set[int] = set()
    for graph_id in GRAPH_SEEDS:
        group = groups_by_id[graph_id]
        matrix_indices = group.get("selected_matrix_indices")
        attempt_j = group.get("selected_attempt_j")
        common_seed = group.get("selected_seed")
        if (group.get("status") != "SELECTED"
                or not isinstance(matrix_indices, Mapping)
                or set(matrix_indices) != set(PROFILE_ORDER)
                or attempt_j is None or common_seed is None):
            raise ValueError(f"source graph {graph_id} has no selected common pair")
        expected_j = 1 if graph_id == 2026093905 else 0
        expected_seed = 2560859716 if graph_id == 2026093905 else graph_id
        if int(attempt_j) != expected_j or int(common_seed) != expected_seed:
            raise ValueError(f"source graph {graph_id} selected seed/attempt mismatch")
        if (graph_id == 2026093905
                and {key: int(value) for key, value in matrix_indices.items()}
                != {"control": 9, "candidate": 10}):
            raise ValueError("source graph 2026093905 selected matrix indices mismatch")
        for profile_id in PROFILE_ORDER:
            matrix_index = int(matrix_indices[profile_id])
            if matrix_index in used_matrix_indices:
                raise ValueError("source selected pairs reuse a matrix_index")
            used_matrix_indices.add(matrix_index)
            matrix = matrices_by_index.get(matrix_index)
            attempt = attempts_by_matrix_index.get(matrix_index)
            if matrix is None or attempt is None:
                raise ValueError("selected matrix_index is not joined in both source tables")
            construction_seed = int(common_seed)
            if (int(matrix.get("graph_id", -1)) != graph_id
                    or matrix.get("profile_id") != profile_id
                    or int(matrix.get("attempt_j", -1)) != int(attempt_j)
                    or int(matrix.get("construction_seed", -1)) != construction_seed
                    or int(attempt.get("graph_id", -1)) != graph_id
                    or attempt.get("profile_id") != profile_id
                    or int(attempt.get("attempt_j", -1)) != int(attempt_j)
                    or int(attempt.get("construction_seed", -1)) != construction_seed
                    or int(attempt.get("matrix_index", -1)) != matrix_index
                    or attempt.get("status") != "admitted"
                    or attempt.get("admitted") is not True):
                raise ValueError("selected source matrix/attempt provenance mismatch")
            constructor_record = attempt.get("constructor_record")
            preflight = attempt.get("preflight")
            if (not isinstance(constructor_record, Mapping)
                    or constructor_record.get("status") != "ok"
                    or constructor_record.get("admitted") is not True
                    or not isinstance(preflight, Mapping)
                    or preflight.get("graph_seed") != construction_seed
                    or preflight.get("profile_id") != profile_id
                    or not isinstance(preflight.get("checks"), Mapping)
                    or not all(preflight["checks"].values())):
                raise ValueError("selected source constructor record/preflight is not admitted")
            if (constructor_record.get("profile_id") != profile_id
                    or int(constructor_record.get("graph_seed", -1)) != construction_seed
                    or len(constructor_record.get("edges", ()))
                    != int(degree_probe.PROFILES[profile_id]["edge_count"])
                    or len(constructor_record.get("coefficients", ()))
                    != int(degree_probe.PROFILES[profile_id]["edge_count"])):
                raise ValueError("selected source constructor record does not match profile")
            selected[(graph_id, profile_id)] = {
                "profile_id": profile_id, "graph_seed": graph_id,
                "n": int(constructor_record["n"]),
                "m": int(constructor_record["m"]),
                "E": int(constructor_record["E"]),
                "edges": constructor_record["edges"],
                "coefficients": constructor_record["coefficients"],
                "H": np.asarray(matrix.get("H")),
                "structure": matrix.get("structure"),
                "status": "ok", "admitted": True, "failure_reason": "",
                "source_uuid": SOURCE_UUID,
                "source_path": SOURCE_JSON_RELATIVE.as_posix(),
                "source_matrix_index": matrix_index,
                "source_attempt_j": int(attempt_j),
                "source_construction_seed": construction_seed,
                "source_graph_id": graph_id,
                "source_preflight": preflight,
                "constructor_record": constructor_record,
            }
    if len(selected) != 2 * len(GRAPH_SEEDS):
        raise ValueError("source canary does not provide six selected profile pairs")
    return selected


def _source_graph_builder(source_reader: Callable[[], Mapping[str, Any]]
                          ) -> Callable[[Mapping[str, Any], int], Mapping[str, Any]]:
    """Load and join the frozen source JSON once, on the first in-budget graph callback."""
    if not callable(source_reader):
        raise ValueError("an explicit source_reader callback is required")
    lookup: dict[tuple[int, str], dict[str, Any]] | None = None
    read_error: Exception | None = None
    read_attempted = False

    def graph_builder(profile: Mapping[str, Any], graph_id: int
                      ) -> Mapping[str, Any]:
        nonlocal lookup, read_error, read_attempted
        if not read_attempted:
            read_attempted = True
            try:
                lookup = selected_graphs(source_reader())
            except Exception as exc:
                read_error = exc
        if read_error is not None:
            raise read_error
        assert lookup is not None
        profile_id = str(profile["profile_id"])
        try:
            return lookup[(int(graph_id), profile_id)]
        except KeyError as exc:
            raise ValueError(
                f"source has no selected matrix for graph {graph_id}/{profile_id}") from exc

    return graph_builder


def _default_source_reader(repo_root: str | Path | None = None
                           ) -> Callable[[], Mapping[str, Any]]:
    root = Path(repo_root).resolve() if repo_root is not None else degree_probe._repo_root()
    path = root / SOURCE_JSON_RELATIVE

    def read() -> Mapping[str, Any]:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)

    return read


def execute_batch(
        *, out_root: str | Path,
        source_reader: Callable[[], Mapping[str, Any]],
        decode_fns: Mapping[str, Callable[[np.ndarray, np.ndarray, np.ndarray], Any]],
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
        ) -> dict[str, Any]:
    graph_builder = _source_graph_builder(source_reader)
    return degree_probe.execute_batch(
        out_root=out_root, decode_fns=decode_fns,
        graph_builder=graph_builder, candidate_builder=candidate_builder,
        profile_preflight_fn=profile_preflight_fn, repo_root=repo_root,
        now=now, rss_fn=rss_fn, command=command,
        batch_uuid=BATCH_UUID, contract_id=CONTRACT,
        seed_prefix=SEED_PREFIX, seed_rows=None,
        out_root_relative=OUT_ROOT_RELATIVE,
        graph_input_kind="admitted_source")


def verify_t0() -> dict[str, bool]:
    return degree_probe.verify_t0(seed_prefix=SEED_PREFIX)


def dry_run(out_root: str | Path = OUT_ROOT_RELATIVE,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    result = degree_probe.dry_run(
        out_root, repo_root=repo_root, batch_uuid=BATCH_UUID,
        contract_id=CONTRACT, seed_prefix=SEED_PREFIX,
        out_root_relative=OUT_ROOT_RELATIVE)
    result["graph_input_kind"] = "admitted_source"
    result["source_reads"] = 0
    return result


def _bind_production() -> dict[str, Any]:
    bindings = degree_probe._bind_production()
    return {
        "decode_fns": bindings["decode_fns"],
        "candidate_builder": bindings["candidate_builder"],
        "profile_preflight_fn": degree_probe.profile_preflight,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GF32 admitted-matrix matched degree-profile EXPLORE probe")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--execute", action="store_true",
                       help="run the frozen admitted-matrix batch")
    modes.add_argument("--dry-run", action="store_true",
                       help="perform pure T0 and fresh-root checks")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE))
    return parser


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = build_parser().parse_args(argv)
    if not args.execute:
        result = dry_run(args.out_root)
    else:
        bindings = _bind_production()
        result = execute_batch(
            out_root=args.out_root,
            source_reader=_default_source_reader(),
            command=COMMAND, **bindings)
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
