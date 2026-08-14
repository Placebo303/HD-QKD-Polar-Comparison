"""Pure in-memory ten-plane aggregation for sacrificed long-v3 development."""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from typing import Any, Mapping, Sequence

from .codebook_long_v3 import BLOCK_LENGTHS, CANDIDATE_IDS, PLANE_IDS, prefix_rows
from .long_v3_development import PREFIX_IDS, ROLE, canonical_development_policy, generate_sacrificed_development, select_candidate

FRAME_ROLE = "sacrificed_frame_development_only"
STOPPING_MODEL = "development_oracle_equivalent_terminal_not_tag_execution"
_ROW_FIELDS = {"n", "plane_id", "candidate_id", "stratum_id", "frame_id", "attempted", "status", "terminal_prefix_id", "rounds_attempted", "syndrome_bits_disclosed", "exact_match", "policy_id", "p_hat", "backend_identity", "runtime_s", "role", "source_sha256"}


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    copied = [dict(row) for row in rows]
    if len(copied) != 3840 or any(set(row) != _ROW_FIELDS for row in copied):
        raise ValueError("requires exactly 3840 typed development outcome rows")
    expected_grid = set()
    by_plane: dict[tuple[int, int], list[dict[str, Any]]] = {}
    sources: dict[tuple[int, int, str], dict[str, Any]] = {}
    for row in copied:
        n, plane, candidate, stratum = row["n"], row["plane_id"], row["candidate_id"], row["stratum_id"]
        if not (_is_int(n) and n in BLOCK_LENGTHS and _is_int(plane) and plane in PLANE_IDS and _is_int(candidate) and candidate in CANDIDATE_IDS and stratum in {"p001", "p002"}):
            raise ValueError("invalid development outcome identity")
        if row["role"] != ROLE or row["policy_id"] != canonical_development_policy(n)["policy_id"]:
            raise ValueError("noncanonical development role or policy")
        if not isinstance(row["runtime_s"], (int, float)) or isinstance(row["runtime_s"], bool) or not math.isfinite(float(row["runtime_s"])) or float(row["runtime_s"]) < 0:
            raise ValueError("invalid development runtime")
        if row["backend_identity"] != "ldpc==2.4.1" or not isinstance(row["source_sha256"], str):
            raise ValueError("invalid development provenance")
        expected_ids = [f"dev_n{n}_plane{plane:02d}_{stratum}_f{i:02d}" for i in range(16)]
        if row["frame_id"] not in expected_ids:
            raise ValueError("noncanonical development frame ID")
        index = expected_ids.index(row["frame_id"])
        key = (n, plane, candidate, stratum, index)
        if key in expected_grid:
            raise ValueError("duplicate development outcome")
        expected_grid.add(key)
        data_key = (n, plane, stratum)
        data = sources.get(data_key)
        if data is None:
            data = generate_sacrificed_development(n, plane, .01 if stratum == "p001" else .02)
            sources[data_key] = data
        if row["p_hat"] != data["p_hat"] or row["source_sha256"] != data["source_sha256"]:
            raise ValueError("development source provenance mismatch")
        by_plane.setdefault((n, plane), []).append(row)
    required = {(n, p, c, s, f) for n in BLOCK_LENGTHS for p in PLANE_IDS for c in CANDIDATE_IDS for s in ("p001", "p002") for f in range(16)}
    if expected_grid != required:
        raise ValueError("incomplete development outcome grid")
    for group in by_plane.values():
        select_candidate(group)
    return copied


def _validate_selections(rows: list[dict[str, Any]], selections: Sequence[Mapping[str, Any]]) -> dict[tuple[int, int], dict[str, Any]]:
    supplied = [dict(item) for item in selections]
    if len(supplied) != 30:
        raise ValueError("requires exactly 30 selections")
    selected: dict[tuple[int, int], dict[str, Any]] = {}
    for item in supplied:
        if not (_is_int(item.get("n")) and item["n"] in BLOCK_LENGTHS and _is_int(item.get("plane_id")) and item["plane_id"] in PLANE_IDS):
            raise ValueError("invalid selection identity")
        key = (item["n"], item["plane_id"])
        if key in selected:
            raise ValueError("duplicate selection")
        rebuilt = select_candidate([row for row in rows if (row["n"], row["plane_id"]) == key])
        if item != rebuilt:
            raise ValueError("selection does not reconstruct exactly")
        selected[key] = item
    if set(selected) != {(n, p) for n in BLOCK_LENGTHS for p in PLANE_IDS}:
        raise ValueError("incomplete selection grid")
    return selected


def aggregate_frame_development(outcome_rows: Sequence[Mapping[str, Any]], selections: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate the frozen 3840-row development grid without decoding or I/O."""
    rows = _validate_rows(outcome_rows)
    selected = _validate_selections(rows, selections)
    lookup = {(row["n"], row["plane_id"], row["candidate_id"], row["stratum_id"], int(row["frame_id"][-2:])): row for row in rows}
    outcomes: list[dict[str, Any]] = []
    aggregates: dict[str, Any] = {}
    for n in BLOCK_LENGTHS:
        by_stratum: dict[str, list[dict[str, Any]]] = {"p001": [], "p002": []}
        for stratum in ("p001", "p002"):
            for index in range(16):
                candidates = [selected[(n, plane)]["selected_candidate_id"] for plane in PLANE_IDS]
                planes = [lookup[(n, plane, candidates[plane], stratum, index)] for plane in PLANE_IDS]
                rounds = max(int(row["rounds_attempted"]) for row in planes)
                if rounds > 4:
                    raise ValueError("invalid plane round accounting")
                terminal = "" if rounds == 0 else PREFIX_IDS[rounds - 1]
                success = all(row["status"] == "development_exact_success" for row in planes)
                syndrome = 0 if rounds == 0 else 10 * prefix_rows(n)[terminal]
                tag = 64 if rounds else 0
                seed = 10 * n + 63 if rounds else 0
                outcome = {"n": n, "stratum_id": stratum, "frame_index": index, "selected_candidate_ids": candidates,
                           "plane_terminal_prefix_ids": [row["terminal_prefix_id"] for row in planes],
                           "plane_rounds_attempted": [row["rounds_attempted"] for row in planes],
                           "status": "development_frame_success" if success else "development_frame_failed",
                           "global_terminal_prefix_id": terminal, "global_rounds_attempted": rounds, "input_bits": 10 * n,
                           "syndrome_bits_disclosed": syndrome, "verification_tag_bits": tag,
                           "key_dependent_disclosure_bits_total": syndrome + tag, "public_toeplitz_seed_bits": seed,
                           "epsilon_ec_union_bound": rounds * 2.0 ** -64,
                           "key_disclosure_per_input_bit": (syndrome + tag) / (10 * n)}
                outcomes.append(outcome); by_stratum[stratum].append(outcome)
        successes = {s: sum(row["status"] == "development_frame_success" for row in by_stratum[s]) for s in by_stratum}
        means = {s: sum(row["key_disclosure_per_input_bit"] for row in by_stratum[s]) / 16 for s in by_stratum}
        terminal_counts = {s: dict(sorted(Counter(row["global_terminal_prefix_id"] for row in by_stratum[s]).items())) for s in by_stratum}
        aggregates[str(n)] = {"successes_by_stratum": successes, "terminal_prefix_counts_by_stratum": terminal_counts,
                              "mean_key_disclosure_per_input_bit_by_stratum": means,
                              "worst_stratum_mean_key_disclosure_per_input_bit": max(means.values()),
                              "overall_mean_key_disclosure_per_input_bit": sum(means.values()) / 2}
    tuples = {n: [-min(aggregates[str(n)]["successes_by_stratum"].values()), -sum(aggregates[str(n)]["successes_by_stratum"].values()), aggregates[str(n)]["worst_stratum_mean_key_disclosure_per_input_bit"], aggregates[str(n)]["overall_mean_key_disclosure_per_input_bit"], n] for n in BLOCK_LENGTHS}
    selected_length = min(tuples, key=lambda n: tuples[n])
    base = {"role": FRAME_ROLE, "stopping_model": STOPPING_MODEL, "plane_count": 10, "verification_tag_bits": 64,
            "tag_reuse_max_checks": 4, "frame_outcome_count": 96, "frame_outcomes": outcomes,
            "length_aggregates": aggregates, "selected_length": selected_length, "length_selection_tuple": tuples[selected_length]}
    return {**base, "aggregation_sha256": hashlib.sha256(_compact(base)).hexdigest()}
