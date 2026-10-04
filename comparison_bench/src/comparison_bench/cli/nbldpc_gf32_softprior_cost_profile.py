"""Posthoc counterfactual profile of stored GF(32) soft-prior branches."""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

BATCH_UUID = "90dcb594-6672-4395-a161-348e7ce74e6c"
CONTRACT = "NBLDPC-GF32-SOFT-PRIOR-COST-PROFILE-20261002/PREREG_AND_AUTH.md"
OUT_ROOT_RELATIVE = Path("workspace") / "gf32_softprior_cost_90dcb594"
K_VALUES = (1, 2, 3, 6)
GUESSES = (0, 1, 3, 7, 15, 31)
TIE_TOL = 1e-12
WALL_CAP_S = 120.0
RSS_CAP_BYTES = 1024 ** 3
ARTIFACT_CAP_BYTES = 5 * 1024 * 1024
COMMAND = (
    "wsl -d Ubuntu --cd /mnt/d/Code/HD-QKD_Polar_Comparison env "
    "PYTHONPATH=comparison_bench/src .venv/bin/python -m "
    "comparison_bench.cli.nbldpc_gf32_softprior_cost_profile --execute "
    "--out-root workspace/gf32_softprior_cost_90dcb594"
)

PARENT_SPECS = (
    (
        "31dca97b-808c-4205-ac01-7c5ab7b9e9b5",
        "NBLDPC-GF32-SOFT-PRIOR-RESCUE-20261001/PREREG_AND_AUTH.md",
        "gf32-softprior-v1",
        Path("workspace") / "gf32_softprior_31dca97b",
        "CONTROL_RANGE_UNINFORMATIVE",
    ),
    (
        "cbe151fe-25f7-4990-8895-858091467e2b",
        "NBLDPC-GF32-SOFT-PRIOR-REPLICA-20261001/PREREG_AND_AUTH.md",
        "gf32-softprior-replica-v1",
        Path("workspace") / "gf32_softprior_replica_cbe151fe",
        "MECHANISM_SIGNAL",
    ),
)
SOURCE_EXPECTED = {
    "batch_uuid": "a9352bc1-ae56-443b-ae93-9dcfa85d4229",
    "contract": "NBLDPC-GF32-DEGREE-ADMITTED-20261001/PREREG_AND_AUTH.md",
    "seed_namespace": "gf32-degree-admitted-v1",
    "graph_input_kind": "admitted_source",
}
GRAPH_IDS = tuple(range(2026093901, 2026093907))
N, M, Q = 128, 52, 32

PARENT_DIAGNOSTIC_KEYS = (
    "source_batch_uuid", "source_contract", "source_seed_namespace",
    "source_graph_input_kind", "source_graph_id", "source_graph_seed",
    "source_profile_index", "source_graph_index", "source_constructor_uuid",
    "source_constructor_path", "source_constructor_matrix_index",
    "source_constructor_attempt_j", "source_constructor_seed",
    "source_constructor_graph_id", "H_deep", "original_prior",
    "pair_index", "pair_graph_id", "pair_stream", "pair_frame", "pair_seed",
    "pair_truth", "pair_syndrome", "pair_completed", "pair_baseline_call_index",
    "pair_candidate_selected_call_index", "pair_selected_variable",
    "call_index", "call_pair_index", "call_graph_id", "call_stream", "call_frame",
    "call_seed", "call_role", "call_branch_index", "call_guess_symbol",
    "call_selected_variable", "call_status", "call_iterations",
    "call_decoder_runtime_s", "call_wall_s", "call_syndrome_valid",
    "call_raw_vector_index", "call_score_original_prior",
    "call_candidate_selected_call_index", "raw_vector_call_index", "raw_x_hat",
    "belief_call_index", "baseline_failure_belief_provenance",
    "baseline_failure_beliefs", "selector_call_index", "selector_selected_column",
)
EXPECTED_FAILURES = {
    "31dca97b-808c-4205-ac01-7c5ab7b9e9b5": 37,
    "cbe151fe-25f7-4990-8895-858091467e2b": 50,
}


def rank_allowed_guesses(
        log_beliefs: Any, selected_variable: int,
        ) -> tuple[list[int], dict[int, float]]:
    beliefs = np.asarray(log_beliefs, dtype=np.float64)
    variable = int(selected_variable)
    if (beliefs.ndim != 2 or beliefs.shape[1] != Q
            or variable < 0 or variable >= beliefs.shape[0]):
        raise ValueError("log_beliefs must be (n,32) and selected variable must be in range")
    row = beliefs[variable]
    if not np.all(np.isfinite(row)):
        raise ValueError("selected variable log-beliefs must be finite")
    shifted = row - np.max(row)
    probabilities = np.exp(shifted)
    total = float(probabilities.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("selected variable softmax has invalid mass")
    probabilities /= total
    allowed_probabilities = {guess: float(probabilities[guess]) for guess in GUESSES}
    remaining = list(GUESSES)
    ranking = []
    while remaining:
        maximum = max(allowed_probabilities[guess] for guess in remaining)
        tied = [guess for guess in remaining
                if maximum - allowed_probabilities[guess] <= TIE_TOL]
        selected = min(tied)
        ranking.append(selected)
        remaining.remove(selected)
    return ranking, allowed_probabilities


def choose_parent_candidate(
        baseline_call_index: int,
        allowed_topk_symbols: Sequence[int],
        branch_call_rows: Sequence[Mapping[str, Any]],
        ) -> dict[str, Any]:
    allowed = {int(symbol) for symbol in allowed_topk_symbols}
    if not allowed.issubset(GUESSES):
        raise ValueError("top-k symbols must be a subset of the six frozen guesses")
    candidates = []
    for row in branch_call_rows:
        if int(row["guess_symbol"]) not in allowed or not bool(row["syndrome_valid"]):
            continue
        score = float(row["score_original_prior"])
        if not math.isfinite(score):
            raise ValueError("syndrome-valid branch lacks finite original-prior score")
        candidates.append((int(row["branch_index"]), int(row["call_index"]),
                           int(row["guess_symbol"]), int(row["raw_vector_index"]), score))
    if not candidates:
        return {
            "candidate_call_index": int(baseline_call_index),
            "selected_branch_index": None, "selected_guess_symbol": None,
            "selected_raw_vector_index": None, "fallback": True,
        }
    maximum = max(row[4] for row in candidates)
    winner = min((row for row in candidates if maximum - row[4] <= TIE_TOL),
                 key=lambda row: row[0])
    return {
        "candidate_call_index": winner[1],
        "selected_branch_index": winner[0], "selected_guess_symbol": winner[2],
        "selected_raw_vector_index": winner[3], "fallback": False,
    }


def _root_path(out_root: str | Path, repo_root: str | Path | None) -> Path:
    base = Path.cwd() if repo_root is None else Path(repo_root)
    path = Path(out_root)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def _require_frozen_root(out_root: str | Path) -> None:
    if Path(out_root) != OUT_ROOT_RELATIVE:
        raise ValueError(f"out_root must be the frozen relative path {OUT_ROOT_RELATIVE}")


def verify_t0(*, out_root: str | Path = OUT_ROOT_RELATIVE,
              repo_root: str | Path | None = None) -> dict[str, Any]:
    _require_frozen_root(out_root)
    root = _root_path(out_root, repo_root)
    if root.exists():
        raise FileExistsError(root)
    return {
        "status": "PASS", "batch_uuid": BATCH_UUID, "contract_id": CONTRACT,
        "seed_namespaces": [spec[2] for spec in PARENT_SPECS],
        "k_values": list(K_VALUES), "source_reads": 0,
        "decoder_calls": 0, "sampler_calls": 0, "writes": 0,
    }


def dry_run(*, out_root: str | Path = OUT_ROOT_RELATIVE,
            repo_root: str | Path | None = None) -> dict[str, Any]:
    result = verify_t0(out_root=out_root, repo_root=repo_root)
    result["status"] = "DRY_RUN"
    return result


def _rss_bytes() -> int | None:
    import resource
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _read_parent(root: Path) -> dict[str, Any]:
    with (root / "manifest.json").open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    with (root / "summary.json").open(encoding="utf-8") as stream:
        summary = json.load(stream)
    with np.load(root / "diagnostics.npz", allow_pickle=False) as archive:
        diagnostics = {key: archive[key] for key in PARENT_DIAGNOSTIC_KEYS}
    return {"manifest": manifest, "summary": summary, "diagnostics": diagnostics}


def _scalar_text(array: Any) -> str:
    values = np.asarray(array).reshape(-1)
    if values.size != 1:
        raise ValueError("source identity array must contain one value")
    return str(values[0])


def _source_map_fingerprint(diagnostics: Mapping[str, Any]) -> tuple[Any, ...]:
    keys = (
        "source_graph_id", "source_graph_seed", "source_profile_index",
        "source_graph_index", "source_constructor_uuid", "source_constructor_path",
        "source_constructor_matrix_index", "source_constructor_attempt_j",
        "source_constructor_seed", "source_constructor_graph_id", "H_deep",
        "original_prior",
    )
    return tuple(np.asarray(diagnostics[key]).copy() for key in keys)


def _validate_parent(
        loaded: Mapping[str, Any], spec: tuple[Any, ...],
        source_reference: tuple[Any, ...] | None,
        ) -> tuple[dict[str, Any], tuple[Any, ...]]:
    manifest = loaded["manifest"]
    summary = loaded["summary"]
    diagnostics = loaded["diagnostics"]
    parent_uuid, parent_contract, namespace, root_rel, classification = spec
    for label, record in (("manifest", manifest), ("summary", summary)):
        if record.get("batch_uuid") != parent_uuid:
            raise ValueError(f"{label}_batch_uuid_mismatch")
        if record.get("contract") != parent_contract:
            raise ValueError(f"{label}_contract_mismatch")
        if record.get("seed_namespace") != namespace:
            raise ValueError(f"{label}_seed_namespace_mismatch")
        if record.get("status") != "COMPLETE":
            raise ValueError(f"{label}_not_complete")
        if record.get("classification") != classification:
            raise ValueError(f"{label}_classification_mismatch")
    if int(summary.get("completed_pairs", -1)) != 192:
        raise ValueError("parent_pair_count_mismatch")
    if set(diagnostics) != set(PARENT_DIAGNOSTIC_KEYS):
        raise ValueError("parent_diagnostic_keys_mismatch")
    for name, expected in SOURCE_EXPECTED.items():
        actual = _scalar_text(diagnostics[f"source_{name}"])
        if actual != expected:
            raise ValueError(f"source_{name}_mismatch")
    source_identity = manifest.get("source_identity")
    if not isinstance(source_identity, Mapping):
        raise ValueError("manifest_source_identity_missing")
    for key, expected in SOURCE_EXPECTED.items():
        if source_identity.get(key) != expected:
            raise ValueError(f"manifest_source_{key}_mismatch")

    ids = np.asarray(diagnostics["source_graph_id"], dtype=np.int64)
    seeds = np.asarray(diagnostics["source_graph_seed"], dtype=np.int64)
    profiles = np.asarray(diagnostics["source_profile_index"], dtype=np.int64)
    graph_indices = np.asarray(diagnostics["source_graph_index"], dtype=np.int64)
    h_deep = np.asarray(diagnostics["H_deep"])
    prior = np.asarray(diagnostics["original_prior"], dtype=np.float64)
    if (ids.shape != (6,) or tuple(sorted(ids.tolist())) != GRAPH_IDS
            or seeds.shape != (6,) or profiles.shape != (6,)
            or graph_indices.shape != (6,) or h_deep.shape != (6, M, N)
            or prior.shape != (N, Q)):
        raise ValueError("source_graph_or_matrix_shape_mismatch")
    if not np.all(np.isfinite(prior)) or np.any(prior < 0.0):
        raise ValueError("original_prior_invalid")
    if not np.allclose(prior.sum(axis=1), 1.0, rtol=0.0, atol=1e-12):
        raise ValueError("original_prior_not_normalized")
    maps = manifest.get("source_maps")
    if not isinstance(maps, list) or len(maps) != 6:
        raise ValueError("manifest_source_maps_mismatch")
    ordered_maps = sorted(maps, key=lambda row: int(row["graph_id"]))
    lineage_fields = (
        ("source_constructor_uuid", "source_uuid"),
        ("source_constructor_path", "source_path"),
        ("source_constructor_matrix_index", "source_matrix_index"),
        ("source_constructor_attempt_j", "source_attempt_j"),
        ("source_constructor_seed", "source_construction_seed"),
        ("source_constructor_graph_id", "source_graph_id"),
    )
    for index, row in enumerate(ordered_maps):
        if (int(row["graph_id"]) != int(ids[index])
                or int(row["graph_seed"]) != int(seeds[index])
                or int(row["profile_index"]) != int(profiles[index])
                or int(row["graph_index"]) != int(graph_indices[index])):
            raise ValueError("manifest_source_map_values_mismatch")
        lineage = row.get("source_lineage", {})
        for array_key, map_key in lineage_fields:
            value = lineage.get(map_key)
            if str(value) != str(np.asarray(diagnostics[array_key])[index]):
                raise ValueError("manifest_source_lineage_mismatch")

    if source_reference is not None:
        for left, right in zip(source_reference, _source_map_fingerprint(diagnostics)):
            if not np.array_equal(left, right):
                raise ValueError("parent_source_maps_differ")

    pair_count = len(np.asarray(diagnostics["pair_index"]))
    if pair_count != 192:
        raise ValueError("parent_pair_arrays_mismatch")
    pair_graph = np.asarray(diagnostics["pair_graph_id"], dtype=np.int64)
    if any(int(np.count_nonzero(pair_graph == graph_id)) != 32 for graph_id in GRAPH_IDS):
        raise ValueError("parent_graph_pair_counts_mismatch")
    if not np.all(np.asarray(diagnostics["pair_completed"], dtype=np.bool_)):
        raise ValueError("parent_has_incomplete_pairs")

    call_indices = np.asarray(diagnostics["call_index"], dtype=np.int64)
    call_pairs = np.asarray(diagnostics["call_pair_index"], dtype=np.int64)
    call_candidate_indices = np.asarray(
        diagnostics["call_candidate_selected_call_index"], dtype=np.int64)
    call_roles = np.asarray(diagnostics["call_role"]).astype(str)
    call_statuses = np.asarray(diagnostics["call_status"]).astype(str)
    call_branches = np.asarray(diagnostics["call_branch_index"], dtype=np.int64)
    call_guesses = np.asarray(diagnostics["call_guess_symbol"], dtype=np.int64)
    call_valid = np.asarray(diagnostics["call_syndrome_valid"], dtype=np.bool_)
    call_vector_index = np.asarray(diagnostics["call_raw_vector_index"], dtype=np.int64)
    call_scores = np.asarray(diagnostics["call_score_original_prior"], dtype=np.float64)
    call_iterations = np.asarray(diagnostics["call_iterations"], dtype=np.int64)
    call_runtime = np.asarray(diagnostics["call_decoder_runtime_s"], dtype=np.float64)
    call_wall = np.asarray(diagnostics["call_wall_s"], dtype=np.float64)
    raw_call_indices = np.asarray(diagnostics["raw_vector_call_index"], dtype=np.int64)
    raw_vectors = np.asarray(diagnostics["raw_x_hat"], dtype=np.int64)
    if (call_indices.ndim != 1 or len(set(call_indices.tolist())) != len(call_indices)
            or call_pairs.shape != call_indices.shape or call_roles.shape != call_indices.shape
            or call_statuses.shape != call_indices.shape
            or call_candidate_indices.shape != call_indices.shape
            or call_branches.shape != call_indices.shape or call_guesses.shape != call_indices.shape
            or call_valid.shape != call_indices.shape or call_vector_index.shape != call_indices.shape
            or call_scores.shape != call_indices.shape or call_iterations.shape != call_indices.shape
            or call_runtime.shape != call_indices.shape or call_wall.shape != call_indices.shape
            or raw_call_indices.shape != (len(raw_vectors),)
            or raw_vectors.shape != (len(raw_call_indices), N)
            or np.any(call_pairs < 0) or np.any(call_pairs >= 192)):
        raise ValueError("parent_call_arrays_mismatch")
    if (not np.all(call_statuses == "COMPLETE")
            or np.any(call_vector_index < 0)
            or np.any(call_iterations < 0)
            or not np.all(np.isfinite(call_runtime))
            or not np.all(np.isfinite(call_wall))
            or np.any(call_runtime < 0.0) or np.any(call_wall < 0.0)):
        raise ValueError("parent_contains_incomplete_call_record")
    call_position = {int(index): offset for offset, index in enumerate(call_indices)}
    raw_position = {int(index): offset for offset, index in enumerate(raw_call_indices)}
    if len(raw_position) != len(raw_call_indices):
        raise ValueError("duplicate_raw_vector_call_index")
    call_rows: dict[int, dict[str, Any]] = {}
    for offset, call_index in enumerate(call_indices):
        vector_index = int(call_vector_index[offset])
        if vector_index >= 0:
            if vector_index >= len(raw_vectors) or int(raw_call_indices[vector_index]) != int(call_index):
                raise ValueError("call_raw_vector_map_mismatch")
        call_rows[int(call_index)] = {
            "call_index": int(call_index), "pair_index": int(call_pairs[offset]),
            "role": str(call_roles[offset]), "branch_index": int(call_branches[offset]),
            "guess_symbol": int(call_guesses[offset]),
            "syndrome_valid": bool(call_valid[offset]),
            "raw_vector_index": None if vector_index < 0 else vector_index,
            "score_original_prior": float(call_scores[offset]),
            "iterations": int(call_iterations[offset]),
            "decoder_runtime_s": float(call_runtime[offset]),
            "wall_s": float(call_wall[offset]),
            "candidate_selected_call_index": int(call_candidate_indices[offset]),
        }

    baseline_indices = np.asarray(diagnostics["pair_baseline_call_index"], dtype=np.int64)
    candidate_indices = np.asarray(diagnostics["pair_candidate_selected_call_index"], dtype=np.int64)
    selected_variables = np.asarray(diagnostics["pair_selected_variable"], dtype=np.int64)
    if (baseline_indices.shape != (192,) or candidate_indices.shape != (192,)
            or selected_variables.shape != (192,)):
        raise ValueError("parent_pair_call_maps_mismatch")
    for pair_index, baseline_index in enumerate(baseline_indices):
        row = call_rows.get(int(baseline_index))
        if row is None or row["pair_index"] != pair_index or row["role"] != "baseline":
            raise ValueError("baseline_call_map_mismatch")
        candidate_index = int(candidate_indices[pair_index])
        candidate = call_rows.get(candidate_index)
        if candidate is None or candidate["pair_index"] != pair_index:
            raise ValueError("accepted_candidate_call_map_mismatch")
    for row in call_rows.values():
        if row["candidate_selected_call_index"] != int(candidate_indices[row["pair_index"]]):
            raise ValueError("call_candidate_pointer_mismatch")

    belief_call_index = np.asarray(diagnostics["belief_call_index"], dtype=np.int64)
    belief_provenance = np.asarray(diagnostics["baseline_failure_belief_provenance"]).astype(str)
    beliefs = np.asarray(diagnostics["baseline_failure_beliefs"], dtype=np.float64)
    selector_call_index = np.asarray(diagnostics["selector_call_index"], dtype=np.int64)
    selector_column = np.asarray(diagnostics["selector_selected_column"], dtype=np.int64)
    if (beliefs.shape != (len(belief_call_index), N, Q)
            or belief_provenance.shape != belief_call_index.shape
            or selector_column.shape != selector_call_index.shape
            or len(set(map(int, belief_call_index))) != len(belief_call_index)
            or len(set(map(int, selector_call_index))) != len(selector_call_index)
            or set(map(int, belief_call_index)) != set(map(int, selector_call_index))):
        raise ValueError("baseline_belief_selector_maps_mismatch")
    selector_by_call = {
        int(call_index): int(column)
        for call_index, column in zip(selector_call_index, selector_column)
    }
    belief_by_call = {int(call): {
        "beliefs": beliefs[index], "provenance": str(belief_provenance[index]),
        "selected_variable": selector_by_call[int(call)],
    } for index, call in enumerate(belief_call_index)}
    failure_pairs = []
    for pair_index, baseline_index in enumerate(baseline_indices):
        base = call_rows[int(baseline_index)]
        if not base["syndrome_valid"]:
            failure_pairs.append(pair_index)
            belief = belief_by_call.get(int(baseline_index))
            if belief is None or belief["provenance"] != "CHECK_UPDATED":
                raise ValueError("baseline_failure_beliefs_missing_or_wrong_provenance")
            if (belief["selected_variable"] != int(selected_variables[pair_index])
                    or not 0 <= int(selected_variables[pair_index]) < N):
                raise ValueError("accepted_selected_variable_mismatch")
    failure_count = len(failure_pairs)
    expected_failures = EXPECTED_FAILURES[parent_uuid]
    if failure_count != expected_failures:
        raise ValueError("baseline_failure_count_mismatch")
    if (sum(row["role"] == "baseline" for row in call_rows.values()) != 192
            or sum(row["role"] == "soft_prior" for row in call_rows.values()) != 6 * failure_count
            or len(call_rows) != 192 + 6 * failure_count
            or int(summary.get("baseline_calls", -1)) != 192):
        raise ValueError("parent_physical_call_count_mismatch")
    branches_by_pair: dict[int, list[dict[str, Any]]] = {i: [] for i in failure_pairs}
    for row in call_rows.values():
        if row["role"] == "soft_prior":
            branches_by_pair.setdefault(row["pair_index"], []).append(row)
    if int(summary.get("branch_calls", -1)) != 6 * failure_count:
        raise ValueError("parent_branch_call_count_mismatch")
    for pair_index in failure_pairs:
        rows = sorted(branches_by_pair.get(pair_index, []), key=lambda row: row["branch_index"])
        if (len(rows) != 6
                or [int(row["guess_symbol"]) for row in rows] != list(GUESSES)
                or [int(row["branch_index"]) for row in rows] != list(range(6))):
            raise ValueError("parent_branch_attempt_map_mismatch")

    truth = np.asarray(diagnostics["pair_truth"], dtype=np.int64)
    if truth.shape != (192, N):
        raise ValueError("parent_truth_shape_mismatch")
    return {
        "uuid": parent_uuid, "contract": parent_contract,
        "seed_namespace": namespace, "root": str(root_rel),
        "classification": classification, "failure_count": failure_count,
        "source_summary": summary,
        "diagnostics": diagnostics, "call_rows": call_rows,
        "call_position": call_position, "raw_position": raw_position,
        "branches_by_pair": branches_by_pair, "belief_by_call": belief_by_call,
    }, _source_map_fingerprint(diagnostics)


def _freeze_parent_selections(
        parent: Mapping[str, Any],
        ) -> tuple[dict[int, list[dict[str, Any]]], list[str]]:
    diagnostics = parent["diagnostics"]
    call_rows = parent["call_rows"]
    branches_by_pair = parent["branches_by_pair"]
    failure_beliefs = parent["belief_by_call"]
    baseline_indices = np.asarray(diagnostics["pair_baseline_call_index"], dtype=np.int64)
    accepted_candidates = np.asarray(
        diagnostics["pair_candidate_selected_call_index"], dtype=np.int64)
    selected_variables = np.asarray(diagnostics["pair_selected_variable"], dtype=np.int64)
    selected_by_k: dict[int, list[dict[str, Any]]] = {k: [] for k in K_VALUES}
    mismatches = []
    for pair_index, baseline_index in enumerate(baseline_indices):
        baseline_index = int(baseline_index)
        baseline = call_rows[baseline_index]
        failed = not bool(baseline["syndrome_valid"])
        ranked: list[int] = []
        allowed_probabilities: dict[int, float] = {}
        if failed:
            belief = failure_beliefs[baseline_index]
            ranked, allowed_probabilities = rank_allowed_guesses(
                belief["beliefs"], int(selected_variables[pair_index]))
        branch_rows = branches_by_pair.get(pair_index, [])
        for k in K_VALUES:
            guesses = ranked[:k] if failed else []
            choice = (choose_parent_candidate(baseline_index, guesses, branch_rows)
                      if failed else {
                          "candidate_call_index": baseline_index,
                          "selected_branch_index": None,
                          "selected_guess_symbol": None,
                          "selected_raw_vector_index": baseline["raw_vector_index"],
                          "fallback": False,
                      })
            if failed and choice["fallback"]:
                choice["selected_raw_vector_index"] = baseline["raw_vector_index"]
            retained = sorted(
                (row for row in branch_rows if int(row["guess_symbol"]) in set(guesses)),
                key=lambda row: int(row["branch_index"]))
            if len(retained) != (k if failed else 0):
                raise ValueError("retained_branch_attempt_count_mismatch")
            if k == 6:
                if int(choice["candidate_call_index"]) != int(accepted_candidates[pair_index]):
                    mismatches.append(
                        f"k6_parent_candidate_mismatch:pair={pair_index}:"
                        f"selected={choice['candidate_call_index']}:"
                        f"accepted={int(accepted_candidates[pair_index])}")
            selected_by_k[k].append({
                "pair_index": int(pair_index), "baseline_call_index": baseline_index,
                "baseline_syndrome_valid": bool(baseline["syndrome_valid"]),
                "selected_variable": int(selected_variables[pair_index]),
                "ranked_guesses": list(ranked),
                "allowed_probabilities": dict(allowed_probabilities),
                "topk_guesses": list(guesses),
                "retained_branch_call_indices": [int(row["call_index"]) for row in retained],
                "candidate_call_index": int(choice["candidate_call_index"]),
                "selected_branch_index": choice["selected_branch_index"],
                "selected_guess_symbol": choice["selected_guess_symbol"],
                "selected_raw_vector_index": choice["selected_raw_vector_index"],
                "fallback": bool(choice["fallback"]),
            })
    return selected_by_k, mismatches


def _evaluate_parent_profiles(
        parent: Mapping[str, Any],
        selections: Mapping[int, Sequence[Mapping[str, Any]]],
        ) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    diagnostics = parent["diagnostics"]
    call_rows = parent["call_rows"]
    raw_position = parent["raw_position"]
    raw_vectors = np.asarray(diagnostics["raw_x_hat"], dtype=np.int64)
    truths = np.asarray(diagnostics["pair_truth"], dtype=np.int64)
    graph_ids = np.asarray(diagnostics["pair_graph_id"], dtype=np.int64)
    streams = np.asarray(diagnostics["pair_stream"], dtype=np.int64)
    frames = np.asarray(diagnostics["pair_frame"], dtype=np.int64)
    seeds = np.asarray(diagnostics["pair_seed"], dtype=np.int64)
    all_profiles: dict[str, Any] = {}
    all_rows: list[dict[str, Any]] = []
    mismatches = []
    for k in K_VALUES:
        selections_for_k = list(selections[k])
        # All candidate decisions for this k have already been frozen before
        # truth is consulted here.
        rows: list[dict[str, Any]] = []
        retained_call_rows = []
        baseline_call_rows = []
        for selected in selections_for_k:
            pair_index = int(selected["pair_index"])
            base = call_rows[int(selected["baseline_call_index"])]
            chosen = call_rows[int(selected["candidate_call_index"])]
            base_index = base["raw_vector_index"]
            chosen_index = selected["selected_raw_vector_index"]
            if base_index is None or chosen_index is None:
                raise ValueError("selected_parent_vector_missing")
            if int(raw_position[int(base["call_index"])]) != int(base_index):
                raise ValueError("baseline_vector_reference_mismatch")
            if int(raw_position[int(chosen["call_index"])]) != int(chosen_index):
                raise ValueError("selected_vector_reference_mismatch")
            base_valid = bool(base["syndrome_valid"])
            candidate_valid = bool(chosen["syndrome_valid"])
            control_exact = base_valid and np.array_equal(raw_vectors[int(base_index)], truths[pair_index])
            candidate_exact = candidate_valid and np.array_equal(raw_vectors[int(chosen_index)], truths[pair_index])
            retained_indices = [int(x) for x in selected["retained_branch_call_indices"]]
            retained_call_rows.extend(call_rows[index] for index in retained_indices)
            baseline_call_rows.append(base)
            row = {
                "parent_uuid": parent["uuid"], "parent_contract": parent["contract"],
                "parent_seed_namespace": parent["seed_namespace"],
                "parent_root": parent["root"], "k": int(k),
                "pair_index": pair_index, "graph_id": int(graph_ids[pair_index]),
                "stream": int(streams[pair_index]), "frame": int(frames[pair_index]),
                "pair_seed": int(seeds[pair_index]),
                "control_call_index": int(base["call_index"]),
                "candidate_call_index": int(chosen["call_index"]),
                "selected_raw_vector_index": int(chosen_index),
                "selected_branch_index": selected["selected_branch_index"],
                "selected_guess_symbol": selected["selected_guess_symbol"],
                "ranked_guesses": list(selected["ranked_guesses"]),
                "topk_guesses": list(selected["topk_guesses"]),
                "retained_branch_call_indices": retained_indices,
                "selection_fallback_to_baseline": bool(selected["fallback"]),
                "control_syndrome_valid": base_valid,
                "candidate_syndrome_valid": candidate_valid,
                "control_exact": bool(control_exact),
                "candidate_exact": bool(candidate_exact),
                "delta_exact": int(bool(candidate_exact)) - int(bool(control_exact)),
                "control_valid_wrong": bool(base_valid and not control_exact),
                "candidate_valid_wrong": bool(candidate_valid and not candidate_exact),
                "control_syndrome_failed": not base_valid,
                "candidate_syndrome_failed": not candidate_valid,
            }
            rows.append(row)
            all_rows.append(row)
        retained_count = len(retained_call_rows)
        if len(baseline_call_rows) != 192:
            raise ValueError("profile_baseline_pair_count_mismatch")
        control_exact = sum(bool(row["control_exact"]) for row in rows)
        candidate_exact = sum(bool(row["candidate_exact"]) for row in rows)
        wrong_control = sum(bool(row["control_valid_wrong"]) for row in rows)
        wrong_candidate = sum(bool(row["candidate_valid_wrong"]) for row in rows)
        failed_control = sum(bool(row["control_syndrome_failed"]) for row in rows)
        failed_candidate = sum(bool(row["candidate_syndrome_failed"]) for row in rows)
        per_graph = {}
        for graph_id in GRAPH_IDS:
            graph_rows = [row for row in rows if row["graph_id"] == graph_id]
            c = sum(bool(row["control_exact"]) for row in graph_rows)
            r = sum(bool(row["candidate_exact"]) for row in graph_rows)
            per_graph[str(graph_id)] = {
                "control_exact": c, "candidate_exact": r, "delta_exact": r - c,
                "control_valid_wrong": sum(bool(row["control_valid_wrong"]) for row in graph_rows),
                "candidate_valid_wrong": sum(bool(row["candidate_valid_wrong"]) for row in graph_rows),
                "control_syndrome_failed": sum(bool(row["control_syndrome_failed"]) for row in graph_rows),
                "candidate_syndrome_failed": sum(bool(row["candidate_syndrome_failed"]) for row in graph_rows),
            }
        both = sum(bool(row["control_exact"] and row["candidate_exact"]) for row in rows)
        control_only = sum(bool(row["control_exact"] and not row["candidate_exact"]) for row in rows)
        candidate_only = sum(bool(row["candidate_exact"] and not row["control_exact"]) for row in rows)
        neither = len(rows) - both - control_only - candidate_only
        def total(field: str, calls: Sequence[Mapping[str, Any]]) -> float | int:
            return sum((int(row[field]) if field == "iterations" else float(row[field]))
                       for row in calls)
        candidate_calls = [*baseline_call_rows, *retained_call_rows]
        profile = {
            "k": int(k), "status": "COMPLETE", "classification": "POSTHOC_COUNTERFACTUAL_PROFILE",
            "completed_pairs": 192, "baseline_failures": parent["failure_count"],
            "control_exact": int(control_exact), "candidate_exact": int(candidate_exact),
            "delta_exact": int(candidate_exact - control_exact),
            "syndrome_valid_wrong_control": int(wrong_control),
            "syndrome_valid_wrong_candidate": int(wrong_candidate),
            "syndrome_failed_control": int(failed_control),
            "syndrome_failed_candidate": int(failed_candidate),
            "paired": {"both_exact": both, "candidate_only": candidate_only,
                       "control_only": control_only, "neither": neither},
            "per_graph": per_graph,
            "retained_branch_attempts": int(retained_count),
            "logical_control_calls": 192,
            "logical_candidate_calls": 192 + int(retained_count),
            "logical_control_iterations": int(total("iterations", baseline_call_rows)),
            "logical_candidate_iterations": int(total("iterations", candidate_calls)),
            "logical_control_decoder_runtime_s": float(total("decoder_runtime_s", baseline_call_rows)),
            "logical_candidate_decoder_runtime_s": float(total("decoder_runtime_s", candidate_calls)),
            "logical_control_recorded_wall_s": float(total("wall_s", baseline_call_rows)),
            "logical_candidate_recorded_wall_s": float(total("wall_s", candidate_calls)),
            "disclosure_bits_per_method": 192 * 260,
            "verification": "NOT_IMPLEMENTED", "undetected": "NOT_MEASURED",
            "profile_execution_decoder_calls": 0, "profile_execution_sampler_calls": 0,
            "profile_execution_search_calls": 0,
        }
        all_profiles[str(k)] = profile
    accepted = parent["source_summary"]
    profile_six = all_profiles["6"]
    for metric, accepted_key in (
            ("candidate_exact", "candidate_exact"),
            ("syndrome_valid_wrong_candidate", "syndrome_valid_wrong_candidate"),
            ("syndrome_failed_candidate", "syndrome_failed_candidate")):
        if int(profile_six[metric]) != int(accepted[accepted_key]):
            mismatches.append(
                f"k6_parent_{metric}_mismatch:{profile_six[metric]}!={accepted[accepted_key]}")
    return all_profiles, all_rows, mismatches


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_pair_records(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fields = (
        "parent_uuid", "parent_contract", "parent_seed_namespace", "parent_root", "k",
        "pair_index", "graph_id", "stream", "frame", "pair_seed", "control_call_index",
        "candidate_call_index", "selected_raw_vector_index", "selected_branch_index",
        "selected_guess_symbol", "ranked_guesses", "topk_guesses",
        "retained_branch_call_indices", "selection_fallback_to_baseline",
        "control_syndrome_valid", "candidate_syndrome_valid", "control_exact",
        "candidate_exact", "delta_exact", "control_valid_wrong", "candidate_valid_wrong",
        "control_syndrome_failed", "candidate_syndrome_failed",
    )
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(row[key], separators=(",", ":"))
                if isinstance(row.get(key), (list, dict)) else row.get(key)
                for key in fields
            })


def _null_profile_comparisons(profiles: Mapping[str, Any]) -> None:
    for parent_profile in profiles.values():
        for profile in parent_profile.values():
            profile["status"] = "INCOMPLETE"
            for key in (
                "control_exact", "candidate_exact", "delta_exact",
                "syndrome_valid_wrong_control", "syndrome_valid_wrong_candidate",
                "syndrome_failed_control", "syndrome_failed_candidate", "paired", "per_graph",
            ):
                profile[key] = None


def execute_batch(
        *, source_reader: Callable[[Path], Mapping[str, Any]],
        out_root: str | Path = OUT_ROOT_RELATIVE,
        repo_root: str | Path | None = None,
        now: Callable[[], float] = time.perf_counter,
        rss_fn: Callable[[], int | None] | None = None,
        command: str = COMMAND,
        ) -> dict[str, Any]:
    _require_frozen_root(out_root)
    root = _root_path(out_root, repo_root)
    if root.exists():
        raise FileExistsError(root)
    if not callable(source_reader):
        raise ValueError("an explicit source_reader callback is required")
    rss_fn = _rss_bytes if rss_fn is None else rss_fn
    started = float(now())
    root.mkdir(parents=True, exist_ok=False)
    log_path = root / "EXPLORATION_LOG.md"
    log_path.write_text(
        f"EXPLORE posthoc profile {BATCH_UUID}; no decoder or sampler calls.\n"
        f"Parents remain independent; source reader supplied only to execute.\n",
        encoding="utf-8")
    profiles: dict[str, dict[str, Any]] = {}
    pair_records: list[dict[str, Any]] = []
    parent_records: list[dict[str, Any]] = []
    resource_events: list[str] = []
    stop_reasons: list[str] = []
    source_reads = 0
    peak_rss = None
    status = "RUNNING"
    source_reference = None

    def resource_check(phase: str) -> bool:
        nonlocal peak_rss
        elapsed = max(float(now()) - started, 0.0)
        rss = rss_fn()
        if rss is not None:
            rss = int(rss)
            peak_rss = rss if peak_rss is None else max(peak_rss, rss)
        reasons = []
        if elapsed > WALL_CAP_S:
            reasons.append("total_wall_cap")
        if rss is not None and rss > RSS_CAP_BYTES:
            reasons.append("peak_rss_cap")
        for reason in reasons:
            resource_events.append(f"{phase}:{reason}")
            stop_reasons.append(reason)
        return bool(reasons)

    for spec in PARENT_SPECS:
        parent_uuid, parent_contract, namespace, parent_root, classification = spec
        try:
            source_reads += 1
            loaded = source_reader(_root_path(parent_root, repo_root))
            parent, source_reference = _validate_parent(loaded, spec, source_reference)
            frozen, selection_issues = _freeze_parent_selections(parent)
            parent_profiles, parent_rows, replay_issues = _evaluate_parent_profiles(parent, frozen)
            profiles[parent_uuid] = parent_profiles
            pair_records.extend(parent_rows)
            parent_issues = [*selection_issues, *replay_issues]
            if parent_issues:
                status = "STOP"
                stop_reasons.extend(f"{parent_uuid}:{reason}" for reason in parent_issues)
                parent_records.append({
                    "batch_uuid": parent_uuid, "contract": parent_contract,
                    "seed_namespace": namespace, "root": str(parent_root),
                    "classification": classification, "status": "STOP",
                    "completed_pairs": 192, "baseline_failures": parent["failure_count"],
                    "failure": parent_issues,
                })
                break
            parent_records.append({
                "batch_uuid": parent_uuid, "contract": parent_contract,
                "seed_namespace": namespace, "root": str(parent_root),
                "classification": classification, "status": "COMPLETE",
                "completed_pairs": 192, "baseline_failures": parent["failure_count"],
            })
        except (KeyError, TypeError, ValueError, IndexError, OSError) as exc:
            status = "STOP"
            stop_reasons.append(f"{parent_uuid}:{type(exc).__name__}:{exc}")
            parent_records.append({
                "batch_uuid": parent_uuid, "contract": parent_contract,
                "seed_namespace": namespace, "root": str(parent_root),
                "classification": classification, "status": "STOP",
                "failure": f"{type(exc).__name__}:{exc}",
            })
            break
        if resource_check(f"after_parent_{parent_uuid[:8]}"):
            status = "INCOMPLETE"
            break

    complete = status == "RUNNING" and len(parent_records) == len(PARENT_SPECS)
    if complete:
        status = "POSTHOC_COUNTERFACTUAL_PROFILE_COMPLETE"
    elif status == "RUNNING":
        status = "INCOMPLETE"
    if status != "POSTHOC_COUNTERFACTUAL_PROFILE_COMPLETE":
        _null_profile_comparisons(profiles)

    summary: dict[str, Any] = {
        "track": "EXPLORE", "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "status": status, "classification": "POSTHOC_COUNTERFACTUAL_COST_PROFILE",
        "parents": parent_records, "k_values": list(K_VALUES),
        "parent_profiles": profiles, "completed_parent_count": len(profiles),
        "pair_record_count": len(pair_records), "source_reads": source_reads,
        "profile_execution_decoder_calls": 0, "profile_execution_sampler_calls": 0,
        "profile_execution_graph_builds": 0, "profile_execution_search_calls": 0,
        "resource_events": resource_events, "stop_reasons": stop_reasons,
        "peak_rss_bytes": peak_rss, "total_wall_s": max(float(now()) - started, 0.0),
        "budget": {"wall_s": WALL_CAP_S, "rss_bytes": RSS_CAP_BYTES,
                   "artifact_bytes": ARTIFACT_CAP_BYTES},
        "cost_interpretation": "counterfactual logical calls/iterations and recorded parent wall/runtime; not measured pruned execution",
        "selection_truth_used": False,
        "disclosure_bits_per_method_frame": 260,
        "verification": "NOT_IMPLEMENTED", "undetected": "NOT_MEASURED",
    }
    manifest = {
        "track": "EXPLORE", "batch_uuid": BATCH_UUID, "contract": CONTRACT,
        "status": status, "classification": summary["classification"],
        "exact_command": command,
        "source_roots": [
            {"batch_uuid": spec[0], "contract": spec[1],
             "seed_namespace": spec[2], "root": str(spec[3]),
             "classification": spec[4]} for spec in PARENT_SPECS
        ],
        "k_values": list(K_VALUES), "allowed_guesses": list(GUESSES),
        "selection": {
            "ranking": "stable softmax over all 32 symbols at accepted selected variable; restrict to six frozen guesses",
            "probability_tie": "within 1e-12, smaller symbol first",
            "candidate_choice": "syndrome-valid stored branch maximizing original-prior score; within 1e-12, lower branch index",
            "truth_used_for_selection": False,
        },
        "accounting": {
            "logical_cost": "shared baseline once plus every retained top-k branch attempt",
            "replay_decoder_calls": 0, "replay_sampler_calls": 0,
            "disclosure_bits_per_method_frame": 260,
            "internal_branch_disclosure_bits": 0, "tag_bits": 0,
            "verification": "NOT_IMPLEMENTED", "undetected": "NOT_MEASURED",
        },
        "resource_events": resource_events, "stop_reasons": stop_reasons,
        "summary": summary,
    }
    summary_path = root / "summary.json"
    manifest_path = root / "manifest.json"
    csv_path = root / "pair_records.csv"
    _write_pair_records(csv_path, pair_records)
    _write_json(summary_path, summary)
    _write_json(manifest_path, manifest)
    checkpoint_over = resource_check("after_first_pass_artifacts")
    artifact_bytes = sum(path.stat().st_size for path in
                         (log_path, summary_path, manifest_path, csv_path))
    if artifact_bytes > ARTIFACT_CAP_BYTES:
        checkpoint_over = True
        resource_events.append("after_first_pass_artifacts:artifact_bytes_cap")
        stop_reasons.append("artifact_bytes_cap")
    if checkpoint_over:
        status = "INCOMPLETE"
        _null_profile_comparisons(profiles)
        summary.update({
            "status": status, "parent_profiles": profiles,
            "resource_events": resource_events, "stop_reasons": stop_reasons,
            "peak_rss_bytes": peak_rss,
            "total_wall_s": max(float(now()) - started, 0.0),
            "artifact_bytes": artifact_bytes,
        })
        manifest.update({"status": status, "parent_profiles": profiles,
                         "resource_events": resource_events, "stop_reasons": stop_reasons,
                         "summary": summary})
        _write_json(summary_path, summary)
        _write_json(manifest_path, manifest)
    else:
        summary["artifact_bytes"] = artifact_bytes
        summary["peak_rss_bytes"] = peak_rss
        summary["total_wall_s"] = max(float(now()) - started, 0.0)
        manifest["summary"] = summary
        _write_json(summary_path, summary)
        _write_json(manifest_path, manifest)
    with log_path.open("a", encoding="utf-8") as stream:
        stream.write(
            f"\nFINAL_STATUS={status}; parents={len(parent_records)}; "
            f"pair_records={len(pair_records)}; decoder_calls=0; sampler_calls=0; "
            f"resource_events={resource_events}; stop_reasons={stop_reasons}\n")
    summary["artifacts"] = {
        "manifest": str(manifest_path), "summary": str(summary_path),
        "pair_records": str(csv_path), "exploration_log": str(log_path),
    }
    return {
        "status": status, "summary": summary, "parent_profiles": profiles,
        "pair_records": pair_records, "source_reads": source_reads,
        "decoder_calls": 0, "sampler_calls": 0, "artifacts": summary["artifacts"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--t0", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--out-root", default=str(OUT_ROOT_RELATIVE))
    args = parser.parse_args(argv)
    if args.t0:
        result = verify_t0(out_root=args.out_root)
    elif args.dry_run:
        result = dry_run(out_root=args.out_root)
    else:
        result = execute_batch(source_reader=_read_parent, out_root=args.out_root)
    printable = result.get("summary", result)
    print(json.dumps({key: printable.get(key) for key in (
        "status", "batch_uuid", "classification", "completed_parent_count",
        "source_reads", "profile_execution_decoder_calls",
        "profile_execution_sampler_calls", "artifact_bytes", "stop_reasons")
        if key in printable}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
