"""Pure, sacrificed-only development selection for binary LDPC v4.

This module is deliberately in-memory.  The immutable package runner is a
separate concern; these functions neither read confirmation artefacts nor
write any output.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import time
from collections import Counter
from typing import Any, Mapping, Sequence

import numpy as np

from ..utils.bitops import symbols_to_bits
from .codebook_v4 import CANDIDATE_IDS, CONSTRUCTION_ID, CONSTRUCTION_VERSION, PLANE_IDS, candidate_entry, candidate_manifest, matrix_for
from .ldpc_v4_channel import DIMENSION, FRAME_LEN, STRESS_SCALE, plane_error_channel

ROLE = "sacrificed_development_only"
FRAME_COUNT = 512
STRATA = ("adjacent_nominal", "adjacent_stress_125")
READINESS_FLOOR = 495
_STATUSES = {
    "development_exact_success", "development_decode_failed",
    "development_syndrome_inconsistent", "development_decoder_error",
    "development_backend_unavailable", "development_timeout",
    "development_backend_mismatch", "development_malformed_output",
}
_FORBIDDEN = {
    "development_backend_unavailable", "development_decoder_error",
    "development_timeout", "development_backend_mismatch",
    "development_malformed_output", "source_error", "internal_error",
    "accounting_error", "unclassified_error",
}


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def canonical_development_policy() -> dict[str, Any]:
    base = {
        "dependency_version": "2.4.1", "input_vector_type": "syndrome",
        "max_iter": 50, "bp_method": "product_sum", "schedule": "serial",
        "omp_thread_count": 1, "serial_schedule_order": list(range(FRAME_LEN)),
        "osd_method": "OSD_0", "osd_order": 0,
    }
    return {**base, "policy_sha256": _sha(_compact(base))}


def _root(model_sha256: str, stratum: str, kind: str) -> tuple[int, str]:
    if stratum not in STRATA or kind not in {"bob", "delta"} or not isinstance(model_sha256, str) or len(model_sha256) != 64:
        raise ValueError("development root domain")
    domain = {
        "construction_id": CONSTRUCTION_ID, "construction_version": CONSTRUCTION_VERSION,
        "role": ROLE, "stratum_id": stratum, "kind": kind, "frame_count": FRAME_COUNT,
        "dimension": DIMENSION, "frame_len_symbols": FRAME_LEN, "channel_model_sha256": model_sha256,
    }
    raw = hashlib.sha256(_compact(domain)).digest()[:16]
    return int.from_bytes(raw, "big"), raw.hex()


def _model_sha(model: Mapping[str, Any]) -> str:
    digest = model.get("model_sha256") if isinstance(model, Mapping) else None
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("channel model hash")
    base = dict(model); base.pop("model_sha256", None)
    if _sha(_compact(base)) != digest:
        raise ValueError("channel model hash")
    probabilities = model.get("probabilities")
    if not isinstance(probabilities, Mapping) or set(probabilities) != set(STRATA):
        raise ValueError("channel model strata")
    return digest


def generate_sacrificed_development(model: Mapping[str, Any], stratum: str) -> dict[str, Any]:
    """Generate the frozen 512 q=1024 frames for one sacrificed stratum."""
    model_sha = _model_sha(model)
    bob_seed, bob_seed_hex = _root(model_sha, stratum, "bob")
    delta_seed, delta_seed_hex = _root(model_sha, stratum, "delta")
    bob = np.random.Generator(np.random.PCG64(bob_seed)).integers(
        0, DIMENSION, size=(FRAME_COUNT, FRAME_LEN), dtype=np.uint16
    )
    distribution = model["probabilities"][stratum]
    p_minus, p_plus = float(distribution["minus_one"]), float(distribution["plus_one"])
    if p_minus < 0 or p_plus < 0 or p_minus + p_plus >= 1:
        raise ValueError("development channel probabilities")
    uniforms = np.random.Generator(np.random.PCG64(delta_seed)).random(size=(FRAME_COUNT, FRAME_LEN), dtype=np.float64)
    delta = np.where(uniforms < p_minus, -1, np.where(uniforms < p_minus + p_plus, 1, 0)).astype(np.int8)
    alice = ((bob.astype(np.int16) + delta) % DIMENSION).astype(np.uint16)
    frame_ids = [f"v4dev_{stratum}_f{index:03d}" for index in range(FRAME_COUNT)]
    base = {
        "role": ROLE, "stratum_id": stratum, "frame_count": FRAME_COUNT,
        "dimension": DIMENSION, "frame_len_symbols": FRAME_LEN,
        "channel_model_sha256": model_sha, "bob_seed_hex": bob_seed_hex,
        "delta_seed_hex": delta_seed_hex, "frame_ids": frame_ids,
        "delta_counts": {"minus_one": int(np.count_nonzero(delta == -1)), "plus_one": int(np.count_nonzero(delta == 1)), "zero": int(np.count_nonzero(delta == 0))},
    }
    source = _compact(base) + b"\nBOB\n" + bob.tobytes(order="C") + b"\nALICE\n" + alice.tobytes(order="C")
    return {**base, "source_sha256": _sha(source), "bob_frames": bob, "alice_frames": alice}


def _syndrome(h: np.ndarray, bits: np.ndarray) -> np.ndarray:
    return (np.asarray(h, dtype=np.uint8) @ np.asarray(bits, dtype=np.uint8) % 2).astype(np.uint8)


def _backend(factory: Any) -> tuple[Any | None, str, str | None]:
    if factory is not None:
        return factory, "test_injected", None
    try:
        version = importlib.metadata.version("ldpc")
        if version != "2.4.1":
            return None, f"ldpc=={version}", "development_backend_mismatch"
    except importlib.metadata.PackageNotFoundError:
        return None, "ldpc_unavailable", "development_backend_unavailable"
    try:
        from ldpc import BpOsdDecoder  # type: ignore[import-not-found]
        return BpOsdDecoder, "ldpc==2.4.1", None
    except (ImportError, AttributeError):
        return None, "ldpc_unavailable", "development_backend_unavailable"


def evaluate_candidate(alice_frames: Any, bob_frames: Any, *, model: Mapping[str, Any], plane_id: int,
                       candidate_id: int, stratum: str, frame_ids: Sequence[str], decoder_factory: Any = None,
                       max_runtime_s: float | None = None, _clock: Any = time.perf_counter) -> list[dict[str, Any]]:
    """Evaluate one candidate on exactly one frozen 512-frame stratum."""
    model_sha = _model_sha(model)
    if plane_id not in PLANE_IDS or candidate_id not in CANDIDATE_IDS or stratum not in STRATA:
        raise ValueError("development candidate identity")
    if max_runtime_s is not None and (not isinstance(max_runtime_s, (int, float)) or isinstance(max_runtime_s, bool) or float(max_runtime_s) < 0):
        raise ValueError("development runtime cap")
    alice, bob = np.asarray(alice_frames), np.asarray(bob_frames)
    if (alice.shape != (FRAME_COUNT, FRAME_LEN) or bob.shape != (FRAME_COUNT, FRAME_LEN)
            or not np.issubdtype(alice.dtype, np.integer) or not np.issubdtype(bob.dtype, np.integer)
            or np.any(alice < 0) or np.any(alice >= DIMENSION) or np.any(bob < 0) or np.any(bob >= DIMENSION)):
        raise ValueError("development frame arrays")
    expected_ids = [f"v4dev_{stratum}_f{index:03d}" for index in range(FRAME_COUNT)]
    if list(frame_ids) != expected_ids:
        raise ValueError("development frame IDs")
    entry = candidate_entry(plane_id, candidate_id)
    policy = canonical_development_policy(); factory, backend, backend_status = _backend(decoder_factory)
    common = {"role": ROLE, "stratum_id": stratum, "plane_id": plane_id, "candidate_id": candidate_id,
              "channel_model_sha256": model_sha, "policy_sha256": policy["policy_sha256"],
              "matrix_sha256": entry["canonical_bytes_sha256"], "candidate_valid": entry["valid"], "backend_identity": backend}
    if factory is None:
        return [{**common, "frame_id": frame_id, "attempted": False, "status": backend_status,
                 "exact_match": False, "syndrome_bits_disclosed": 0, "runtime_s": 0.0} for frame_id in expected_ids]
    h = matrix_for(plane_id, candidate_id)
    a_bits = symbols_to_bits(alice.astype(np.int64), DIMENSION, "gray")[:, :, plane_id]
    b_bits = symbols_to_bits(bob.astype(np.int64), DIMENSION, "gray")[:, :, plane_id]
    kwargs = {key: policy[key] for key in ("max_iter", "bp_method", "schedule", "omp_thread_count", "serial_schedule_order", "osd_method", "osd_order")}
    results: list[dict[str, Any]] = []
    for frame_id, a, b, bob_symbols in zip(expected_ids, a_bits, b_bits, bob):
        started = _clock(); status = "development_decode_failed"; exact = False
        if max_runtime_s is not None and _clock() - started >= float(max_runtime_s):
            status = "development_timeout"
        else:
            try:
                error_channel = plane_error_channel(bob_symbols, plane_id, stratum, model)
                decoded = np.asarray(factory(h, error_channel=error_channel, **kwargs).decode(_syndrome(h, a) ^ _syndrome(h, b))).reshape(-1)
                if decoded.size != FRAME_LEN or np.any((decoded != 0) & (decoded != 1)):
                    status = "development_malformed_output"
                else:
                    decoded = decoded.astype(np.uint8)
                    if not np.array_equal(_syndrome(h, decoded), _syndrome(h, a) ^ _syndrome(h, b)):
                        status = "development_syndrome_inconsistent"
                    elif np.array_equal(b ^ decoded, a):
                        status = "development_exact_success"; exact = True
            except Exception:
                status = "development_decoder_error"
        elapsed = max(0.0, float(_clock() - started))
        if max_runtime_s is not None and elapsed >= float(max_runtime_s):
            status = "development_timeout"; exact = False
        results.append({**common, "frame_id": frame_id, "attempted": True, "status": status,
                        "exact_match": exact, "syndrome_bits_disclosed": int(h.shape[0]),
                        "runtime_s": elapsed})
    return results


def _select_plane(rows: Sequence[Mapping[str, Any]], plane_id: int) -> dict[str, Any]:
    """Strictly select a single candidate for one plane from its 4096 rows."""
    records = [dict(row) for row in rows]
    expected_count = len(CANDIDATE_IDS) * len(STRATA) * FRAME_COUNT
    if len(records) != expected_count or plane_id not in PLANE_IDS:
        raise ValueError("incomplete candidate selection grid")
    policy = canonical_development_policy()["policy_sha256"]
    groups: dict[int, dict[str, list[dict[str, Any]]]] = {candidate: {stratum: [] for stratum in STRATA} for candidate in CANDIDATE_IDS}
    for row in records:
        if (row.get("role") != ROLE or row.get("plane_id") != plane_id or row.get("candidate_id") not in CANDIDATE_IDS
                or row.get("stratum_id") not in STRATA or row.get("status") not in _STATUSES
                or row.get("policy_sha256") != policy or not isinstance(row.get("candidate_valid"), bool)
                or not isinstance(row.get("exact_match"), bool) or not isinstance(row.get("attempted"), bool)):
            raise ValueError("invalid development outcome")
        groups[int(row["candidate_id"])][str(row["stratum_id"])].append(row)
    aggregates: dict[str, Any] = {}
    for candidate in CANDIDATE_IDS:
        by_stratum = groups[candidate]
        if any(len(by_stratum[stratum]) != FRAME_COUNT for stratum in STRATA):
            raise ValueError("incomplete candidate stratum")
        successes: dict[str, int] = {}; status_counts: dict[str, int] = {}
        for stratum in STRATA:
            group = by_stratum[stratum]
            if [r.get("frame_id") for r in group] != [f"v4dev_{stratum}_f{i:03d}" for i in range(FRAME_COUNT)]:
                raise ValueError("noncanonical development order")
            if len({r.get("matrix_sha256") for r in group}) != 1 or len({r.get("channel_model_sha256") for r in group}) != 1:
                raise ValueError("development binding mismatch")
            if any(r["exact_match"] != (r["status"] == "development_exact_success") for r in group):
                raise ValueError("development success status mismatch")
            successes[stratum] = sum(r["status"] == "development_exact_success" for r in group)
            status_counts[stratum] = dict(sorted(Counter(str(r["status"]) for r in group).items()))
        entry = candidate_entry(plane_id, candidate)
        if any(row["matrix_sha256"] != entry["canonical_bytes_sha256"] or row["candidate_valid"] != entry["valid"] for group in by_stratum.values() for row in group):
            raise ValueError("candidate codebook binding")
        aggregates[str(candidate)] = {"candidate_valid": entry["valid"], "successes_by_stratum": successes,
                                      "total_successes": sum(successes.values()), "status_counts_by_stratum": status_counts}
    tuples = {candidate: (-min(item["successes_by_stratum"].values()), -item["total_successes"], candidate)
              for candidate, item in ((int(key), value) for key, value in aggregates.items())}
    selected, selection_tuple = min(tuples.items(), key=lambda item: item[1])
    base = {"role": ROLE, "plane_id": plane_id, "policy_sha256": policy, "aggregates": aggregates,
            "selected_candidate_id": selected, "selection_tuple": list(selection_tuple)}
    return {**base, "selection_sha256": _sha(_compact(base))}


def select_candidates(rows: Sequence[Mapping[str, Any]], channel_model: Mapping[str, Any], *,
                      codebook_manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Emit the exact frozen, self-hashed v4 selected-matrix binding."""
    model_sha = _model_sha(channel_model)
    manifest = dict(candidate_manifest() if codebook_manifest is None else codebook_manifest)
    manifest_sha = manifest.get("manifest_sha256")
    expected_manifest = candidate_manifest()
    if manifest != expected_manifest or not isinstance(manifest_sha, str):
        raise ValueError("candidate manifest binding")
    plane_selections: list[dict[str, Any]] = []
    for plane in PLANE_IDS:
        selected = _select_plane([row for row in rows if row.get("plane_id") == plane], plane)
        candidate = int(selected["selected_candidate_id"])
        entry = candidate_entry(plane, candidate)
        successes = selected["aggregates"][str(candidate)]["successes_by_stratum"]
        plane_selections.append({
            "plane_id": plane, "candidate_id": candidate,
            "canonical_bytes_sha256": entry["canonical_bytes_sha256"],
            "nominal_successes": int(successes["adjacent_nominal"]),
            "stress_successes": int(successes["adjacent_stress_125"]),
            "selection_key": list(selected["selection_tuple"]),
        })
    base = {
        "schema": "binary_ldpc_v4_selection_v1", "method_id": "ldpc_formal_v4",
        "codebook_manifest_sha256": manifest_sha, "channel_model_sha256": model_sha,
        "plane_selections": plane_selections,
    }
    return {**base, "selection_sha256": _sha(_compact(base))}


def aggregate_frame_development(rows: Sequence[Mapping[str, Any]], selection_binding: Mapping[str, Any],
                                channel_model: Mapping[str, Any]) -> dict[str, Any]:
    """Aggregate selected plane outcomes into exact q=1024 frame readiness."""
    copied = [dict(row) for row in rows]
    if len(copied) != len(PLANE_IDS) * len(CANDIDATE_IDS) * len(STRATA) * FRAME_COUNT:
        raise ValueError("incomplete development outcome grid")
    rebuilt_binding = select_candidates(copied, channel_model)
    if not isinstance(selection_binding, Mapping) or dict(selection_binding) != rebuilt_binding:
        raise ValueError("selection binding does not reconstruct")
    selected = {item["plane_id"]: item for item in rebuilt_binding["plane_selections"]}
    lookup = {(int(row["plane_id"]), int(row["candidate_id"]), str(row["stratum_id"]), str(row["frame_id"])): row for row in copied}
    frame_outcomes: list[dict[str, Any]] = []; aggregate: dict[str, Any] = {}
    for stratum in STRATA:
        stratum_rows: list[dict[str, Any]] = []
        for index in range(FRAME_COUNT):
            frame_id = f"v4dev_{stratum}_f{index:03d}"
            planes = [lookup[(plane, selected[plane]["candidate_id"], stratum, frame_id)] for plane in PLANE_IDS]
            statuses = [str(row["status"]) for row in planes]
            if len(planes) != 10:
                raise ValueError("missing selected plane result")
            frame_status = "development_frame_exact_success" if all(status == "development_exact_success" for status in statuses) else "development_frame_failed"
            row = {"role": ROLE, "stratum_id": stratum, "frame_id": frame_id,
                   "selected_candidate_ids": [selected[p]["candidate_id"] for p in PLANE_IDS],
                   "plane_statuses": statuses, "status": frame_status,
                   "exact_success": frame_status == "development_frame_exact_success",
                   "syndrome_bits_disclosed": 584 if all(bool(p["attempted"]) for p in planes) else 0,
                   "verification_tag_bits": 0, "key_dependent_disclosure_bits_total": 584 if all(bool(p["attempted"]) for p in planes) else 0}
            stratum_rows.append(row); frame_outcomes.append(row)
        status_counts = Counter(status for item in stratum_rows for status in item["plane_statuses"])
        forbidden = sum(status_counts.get(status, 0) for status in _FORBIDDEN)
        aggregate[stratum] = {"denominator_frames": FRAME_COUNT,
                              "frame_exact_successes": sum(item["exact_success"] for item in stratum_rows),
                              "plane_status_counts": dict(sorted(status_counts.items())),
                              "forbidden_failure_count": forbidden}
    ready = (all(item["frame_exact_successes"] >= READINESS_FLOOR and item["denominator_frames"] == FRAME_COUNT and item["forbidden_failure_count"] == 0 for item in aggregate.values())
             and all(candidate_entry(plane, selected[plane]["candidate_id"])["valid"] for plane in PLANE_IDS))
    base = {"role": ROLE, "frame_count_per_stratum": FRAME_COUNT, "readiness_floor": READINESS_FLOOR,
            "selection_binding_sha256": rebuilt_binding["selection_sha256"], "frame_outcomes": frame_outcomes,
            "stratum_aggregates": aggregate, "ready_for_synthetic_prepare": ready}
    return {**base, "aggregation_sha256": _sha(_compact(base))}
