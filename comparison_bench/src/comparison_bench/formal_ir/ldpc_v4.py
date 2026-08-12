"""Fail-closed formal adjacent-channel binary LDPC v4 frame method."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import time
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np

from ..utils.bitops import frame_symbol_error_rate, symbols_to_bits
from .codebook_v4 import BLOCK_LENGTH, CANDIDATE_IDS, PLANE_IDS, candidate_manifest, matrix_for, row_count
from .ldpc_v4_channel import plane_error_channel
from .shared import canonical_event, locked_seed_bits, sha256_bytes, status_flags, toeplitz_tag, transcript_summary

METHOD = "ldpc_formal_v4"
DIMENSION = 1024
MAPPING = "gray"
N = BLOCK_LENGTH
SYNDROME_BITS = 584
DISCLOSURE_BITS = 648
DEFAULT_CAPS = {"wall_s": 5.0, "decoder_calls": 10, "events": 32}
_NON_ATTEMPTED = {"invalid_input", "unsupported_domain", "backend_unavailable"}


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(value: Any) -> str:
    return hashlib.sha256(_compact(value)).hexdigest()


def _hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _syndrome(h: np.ndarray, bits: np.ndarray) -> np.ndarray:
    return (np.asarray(h, dtype=np.uint8) @ np.asarray(bits, dtype=np.uint8) % 2).astype(np.uint8)


def decoder_policy() -> dict[str, Any]:
    base = {"dependency": "ldpc==2.4.1", "max_iter": 50, "bp_method": "product_sum", "schedule": "serial",
            "omp_thread_count": 1, "serial_schedule_order": list(range(N)), "osd_method": "OSD_0", "osd_order": 0,
            "input_vector_type": "syndrome", "error_channel": "bob_conditioned_per_position"}
    return {**base, "policy_sha256": _sha(base)}


def _decoder_params(error_channel: np.ndarray) -> dict[str, Any]:
    policy = decoder_policy()
    # ldpc 2.4.1's Cython boundary requires a Python list here; values retain
    # the frozen float64 per-position channel in the original input order.
    return {key: policy[key] for key in ("max_iter", "bp_method", "schedule", "omp_thread_count", "serial_schedule_order", "osd_method", "osd_order")} | {"error_channel": np.asarray(error_channel, dtype=np.float64).tolist()}


def validate_selection_binding(binding: Mapping[str, Any], channel_model: Mapping[str, Any]) -> list[int]:
    """Strictly validate the frozen v4 selected-candidate binding."""
    if not isinstance(binding, Mapping):
        raise ValueError("selection binding")
    required = {"schema", "method_id", "codebook_manifest_sha256", "channel_model_sha256", "plane_selections", "selection_sha256"}
    if set(binding) != required:
        raise ValueError("selection binding schema")
    base = dict(binding); digest = base.pop("selection_sha256")
    if binding["schema"] != "binary_ldpc_v4_selection_v1" or binding["method_id"] != METHOD or not _hex64(digest) or _sha(base) != digest:
        raise ValueError("selection binding identity")
    if binding["channel_model_sha256"] != channel_model.get("model_sha256"):
        raise ValueError("selection channel binding")
    manifest = candidate_manifest()
    if binding["codebook_manifest_sha256"] != manifest["manifest_sha256"]:
        raise ValueError("selection codebook binding")
    rows = binding["plane_selections"]
    if not isinstance(rows, list) or len(rows) != 10:
        raise ValueError("selection planes")
    manifest_rows = {(row["plane_id"], row["candidate_id"]): row for row in manifest["candidates"]}
    selected: list[int] = []
    fields = {"plane_id", "candidate_id", "canonical_bytes_sha256", "nominal_successes", "stress_successes", "selection_key"}
    for plane, row in enumerate(rows):
        if not isinstance(row, Mapping) or set(row) != fields or row.get("plane_id") != plane:
            raise ValueError("selection plane schema")
        candidate = row.get("candidate_id")
        nominal, stress = row.get("nominal_successes"), row.get("stress_successes")
        if candidate not in CANDIDATE_IDS or any(not isinstance(x, int) or isinstance(x, bool) or not 0 <= x <= 512 for x in (nominal, stress)):
            raise ValueError("selection values")
        expected_key = [-min(nominal, stress), -(nominal + stress), candidate]
        if row.get("selection_key") != expected_key:
            raise ValueError("selection key")
        entry = manifest_rows[(plane, candidate)]
        if not entry["valid"] or row.get("canonical_bytes_sha256") != entry["canonical_bytes_sha256"]:
            raise ValueError("selection candidate binding")
        selected.append(candidate)
    return selected


def _preflight(h: np.ndarray, error_channel: np.ndarray) -> dict[str, Any]:
    try:
        if importlib.metadata.version("ldpc") != "2.4.1":
            return {"status": "backend_unavailable", "dependency_version": ""}
        from ldpc import BpOsdDecoder  # type: ignore[import-not-found]
        BpOsdDecoder(h, **_decoder_params(error_channel))
        return {"status": "ok", "dependency_version": "2.4.1", "backend_name": "ldpc.BpOsdDecoder"}
    except Exception:
        return {"status": "backend_unavailable", "dependency_version": ""}


def validate_outcome_v4(row: Mapping[str, Any], events: list[Mapping[str, Any]] | None = None) -> None:
    required = {"dataset_id", "frame_id", "n_pairs", "pair_idx_sequence_sha256", "method", "attempted", "denominator_included", "status", "failure_reason", "dimension", "frame_len_symbols", "raw_ser", "verification_invoked", "verification_seed_id", "verification_tag_bits", "epsilon_ec", "key_dependent_disclosure_bits_total", "public_control_bits_total", "transcript_first_event_id", "transcript_last_event_id", "transcript_sha256", "runtime_s", "decoder_call_count", "verification_check_count", "ldpc_syndrome_bits", "verification_tag_bits_component", "selection_sha256", "channel_model_sha256", "codebook_manifest_sha256", "policy_sha256", "mapping", "leakage_comparison_policy", "backend_name", "backend_version"}
    if set(row) != required or row["method"] != METHOD or row["n_pairs"] != N or row["dimension"] != DIMENSION or row["frame_len_symbols"] != N or row["mapping"] != MAPPING:
        raise ValueError("v4 outcome identity")
    if row["pair_idx_sequence_sha256"] != sha256_bytes(",".join(str(i) for i in range(N)).encode("ascii")) or not all(_hex64(row[key]) for key in ("selection_sha256", "channel_model_sha256", "codebook_manifest_sha256", "policy_sha256", "transcript_sha256")):
        raise ValueError("v4 outcome hashes")
    if not all(isinstance(row[key], bool) for key in ("attempted", "denominator_included", "verification_invoked")):
        raise ValueError("v4 outcome flags")
    attempted, denominator = status_flags(str(row["status"]))
    if (row["attempted"], row["denominator_included"]) != (attempted, denominator) or (str(row["status"]) in _NON_ATTEMPTED) != (not attempted):
        raise ValueError("v4 status flags")
    if row["leakage_comparison_policy"] != "method_specific_not_cross_ranked" or not isinstance(row["runtime_s"], (int, float)) or isinstance(row["runtime_s"], bool) or not math.isfinite(float(row["runtime_s"])) or float(row["runtime_s"]) < 0:
        raise ValueError("v4 outcome scalar")
    if not attempted:
        if events or any(row[k] != 0 for k in ("verification_tag_bits", "epsilon_ec", "key_dependent_disclosure_bits_total", "public_control_bits_total", "decoder_call_count", "verification_check_count", "ldpc_syndrome_bits")):
            raise ValueError("v4 nonattempted accounting")
        return
    if row["decoder_call_count"] > 10 or row["verification_check_count"] not in (0, 1) or row["verification_tag_bits"] not in (0, 64) or row["verification_tag_bits_component"] != row["verification_tag_bits"]:
        raise ValueError("v4 verification accounting")
    complete = row["status"] in {"verified_success", "verify_failed"}
    if complete and (row["verification_invoked"] is not True or row["verification_seed_id"] == "" or row["verification_tag_bits"] != 64 or row["public_control_bits_total"] != 2623 or row["epsilon_ec"] != 2.0 ** -64 or row["verification_check_count"] != 1):
        raise ValueError("v4 completed verification accounting")
    if complete and (row["ldpc_syndrome_bits"] != SYNDROME_BITS or row["key_dependent_disclosure_bits_total"] != DISCLOSURE_BITS):
        raise ValueError("v4 disclosure accounting")
    if not complete and (row["verification_invoked"] or row["verification_seed_id"] != "" or row["verification_tag_bits"] != 0 or row["epsilon_ec"] != 0.0 or row["verification_check_count"] != 0 or row["public_control_bits_total"] != 0):
        raise ValueError("v4 early-failure verification accounting")
    if events is not None:
        summary = transcript_summary(events)
        if summary["transcript_sha256"] != row["transcript_sha256"] or len(events) > 32:
            raise ValueError("v4 transcript summary")
        if [event["event_id"] for event in events] != list(range(1, len(events) + 1)) or (row["transcript_first_event_id"], row["transcript_last_event_id"]) != (1, len(events)):
            raise ValueError("v4 transcript ids")
        for event in events:
            canonical_event(event)
            if event["method"] != METHOD or event["frame_key"] != f"{row['dataset_id']}:{row['frame_id']}" or event["parent_event_id"] is not None:
                raise ValueError("v4 transcript event")
        syndrome_events = [event for event in events if event["event_type"] == "SYNDROME"]
        if [(event["plane_id"], event["key_dependent_bits"]) for event in syndrome_events] != list(enumerate([row_count(p) for p in PLANE_IDS]))[:len(syndrome_events)]:
            raise ValueError("v4 syndrome order")
        seed_events = [event for event in events if event["event_type"] == "VERIFICATION_SEED"]
        tag_events = [event for event in events if event["event_type"] == "VERIFICATION_TAG"]
        check_events = [event for event in events if event["event_type"] == "FRAME_TAG_CHECK"]
        expected_verification_events = 1 if complete else 0
        if len(seed_events) != expected_verification_events or len(tag_events) != expected_verification_events or len(check_events) != row["verification_check_count"]:
            raise ValueError("v4 verification events")
        if complete and [event["event_type"] for event in events] != ["SYNDROME"] * 10 + ["VERIFICATION_SEED", "VERIFICATION_TAG", "FRAME_TAG_CHECK"]:
            raise ValueError("v4 completed event order")


def run_ldpc_formal_v4(alice_symbols: Any, bob_symbols: Any, *, channel_model: Mapping[str, Any], selection_binding: Mapping[str, Any], locked_seed: Mapping[str, Any] | None, dataset_id: str = "synthetic", frame_id: str = "0", dimension: int = DIMENSION, mapping: str = MAPPING, stratum: str = "adjacent_nominal", _caps: Mapping[str, float] | None = None, _clock: Callable[[], float] = time.monotonic, _decoder_factory: Callable[..., Any] | None = None, _preflight_result: Mapping[str, Any] | None = None) -> dict[str, Any]:
    started = _clock(); events: list[dict[str, Any]] = []; caps = {**DEFAULT_CAPS, **dict(_caps or {})}; next_id = 1; calls = checks = 0
    raw_ser = float("nan"); decoded: np.ndarray | None = None; backend_name = backend_version = ""
    def add(kind: str, direction: str, plane: int, payload: dict[str, Any], kb: int = 0, cb: int = 0) -> bool:
        nonlocal next_id
        if len(events) >= int(caps["events"]): return False
        event = {"event_id": next_id, "frame_key": f"{dataset_id}:{frame_id}", "method": METHOD, "event_type": kind, "direction": direction, "parent_event_id": None, "pass_id": 0, "plane_id": plane, "key_dependent_bits": kb, "public_control_bits": cb, "payload": payload}
        canonical_event(event); events.append(event); next_id += 1; return True
    def finish(status: str, reason: str) -> dict[str, Any]:
        attempted = status not in _NON_ATTEMPTED
        if status == "aborted_resource_limit" and len(events) < int(caps.get("events", 0)): add("ABORT", "control", -1, {"cap": reason, "reason": "resource_limit"})
        summary = transcript_summary(events)
        tag_bits = sum(event["key_dependent_bits"] for event in events if event["event_type"] == "VERIFICATION_TAG")
        out = {"dataset_id": str(dataset_id), "frame_id": str(frame_id), "n_pairs": N, "pair_idx_sequence_sha256": sha256_bytes(",".join(str(i) for i in range(N)).encode("ascii")), "method": METHOD, "attempted": attempted, "denominator_included": attempted, "status": status, "failure_reason": reason, "dimension": DIMENSION, "frame_len_symbols": N, "raw_ser": raw_ser, "verification_invoked": checks == 1, "verification_seed_id": str(locked_seed.get("seed_id", "")) if tag_bits and locked_seed else "", "verification_tag_bits": tag_bits, "epsilon_ec": 2.0 ** -64 if checks else 0.0, "key_dependent_disclosure_bits_total": summary["key_dependent_disclosure_bits_total"], "public_control_bits_total": summary["public_control_bits_total"], "transcript_first_event_id": events[0]["event_id"] if events else None, "transcript_last_event_id": events[-1]["event_id"] if events else None, "transcript_sha256": summary["transcript_sha256"], "runtime_s": max(0.0, _clock() - started), "decoder_call_count": calls, "verification_check_count": checks, "ldpc_syndrome_bits": sum(event["key_dependent_bits"] for event in events if event["event_type"] == "SYNDROME"), "verification_tag_bits_component": tag_bits, "selection_sha256": str(selection_binding.get("selection_sha256", "0" * 64)) if isinstance(selection_binding, Mapping) else "0" * 64, "channel_model_sha256": str(channel_model.get("model_sha256", "0" * 64)) if isinstance(channel_model, Mapping) else "0" * 64, "codebook_manifest_sha256": str(selection_binding.get("codebook_manifest_sha256", "0" * 64)) if isinstance(selection_binding, Mapping) else "0" * 64, "policy_sha256": decoder_policy()["policy_sha256"], "mapping": MAPPING, "leakage_comparison_policy": "method_specific_not_cross_ranked", "backend_name": backend_name, "backend_version": backend_version}
        validate_outcome_v4(out, events); return {"outcome": out, "events": events, "decoded_bits": None if decoded is None else decoded.copy()}
    try:
        if set(caps) != set(DEFAULT_CAPS) or any(isinstance(caps[key], bool) or not isinstance(caps[key], (int, float)) or caps[key] < 0 for key in caps) or int(caps["events"]) < 2:
            raise ValueError("caps")
        a, b = np.asarray(alice_symbols), np.asarray(bob_symbols)
        if dimension != DIMENSION or mapping != MAPPING or stratum not in {"adjacent_nominal", "adjacent_stress_125"} or a.shape != (N,) or b.shape != (N,) or not np.issubdtype(a.dtype, np.integer) or not np.issubdtype(b.dtype, np.integer) or np.any(a < 0) or np.any(a >= DIMENSION) or np.any(b < 0) or np.any(b >= DIMENSION) or not isinstance(dataset_id, str) or not isinstance(frame_id, (str, int)):
            raise ValueError("input domain")
        seed = locked_seed_bits(locked_seed, 2623) if locked_seed is not None else (_ for _ in ()).throw(ValueError("locked seed"))
    except Exception as exc:
        return finish("invalid_input", str(exc))
    raw_ser = frame_symbol_error_rate(a, b)
    try:
        # Model self-hash is validated here; lock reconstruction belongs to the caller's immutable package verifier.
        base = dict(channel_model); digest = base.pop("model_sha256")
        if not _hex64(digest) or _sha(base) != digest: raise ValueError("channel model hash")
        selected = validate_selection_binding(selection_binding, channel_model)
    except Exception as exc:
        return finish("unsupported_domain", str(exc))
    first_channel = plane_error_channel(b, 0, stratum, channel_model)
    check = dict(_preflight_result) if _preflight_result is not None else _preflight(matrix_for(0, selected[0]), first_channel)
    if check.get("status") != "ok" or check.get("dependency_version") != "2.4.1": return finish("backend_unavailable", "ldpc pinned dependency/API unavailable")
    backend_name, backend_version = str(check.get("backend_name", "test_injected")), "2.4.1"
    factory = _decoder_factory
    if factory is None:
        try:
            from ldpc import BpOsdDecoder  # type: ignore[import-not-found]
            factory = BpOsdDecoder
        except Exception: return finish("backend_unavailable", "ldpc constructor unavailable")
    alice = symbols_to_bits(a.astype(np.int64), DIMENSION, MAPPING).astype(np.uint8); bob = symbols_to_bits(b.astype(np.int64), DIMENSION, MAPPING).astype(np.uint8).copy()
    for plane in PLANE_IDS:
        if _clock() - started >= float(caps["wall_s"]): return finish("aborted_resource_limit", "wall_s")
        if calls >= int(caps["decoder_calls"]): return finish("aborted_resource_limit", "decoder_calls")
        h = matrix_for(plane, selected[plane]); syndrome = _syndrome(h, alice[:, plane]); delta = syndrome ^ _syndrome(h, bob[:, plane])
        if not add("SYNDROME", "alice_to_bob", plane, {"syndrome": np.packbits(syndrome, bitorder="big").tobytes().hex()}, kb=len(syndrome)): return finish("aborted_resource_limit", "events")
        try:
            calls += 1; error = np.asarray(factory(h, **_decoder_params(plane_error_channel(b, plane, stratum, channel_model))).decode(delta)).reshape(-1)
        except Exception:
            return finish("aborted_resource_limit", "wall_s") if _clock() - started >= float(caps["wall_s"]) else finish("decoder_error", "decoder exception")
        if _clock() - started >= float(caps["wall_s"]): return finish("aborted_resource_limit", "wall_s")
        if error.size != N or np.any((error != 0) & (error != 1)): return finish("decoder_error", "malformed decoder output")
        error = error.astype(np.uint8)
        if not np.array_equal(_syndrome(h, error), delta): return finish("syndrome_inconsistent", "decoder syndrome mismatch")
        bob[:, plane] ^= error
    if _clock() - started >= float(caps["wall_s"]): return finish("aborted_resource_limit", "wall_s")
    tag = toeplitz_tag(alice.reshape(-1), seed).hex()
    if not add("VERIFICATION_SEED", "control", -1, {"seed_id": locked_seed["seed_id"], "seed_bit_length": 2623}, cb=2623) or not add("VERIFICATION_TAG", "alice_to_bob", -1, {"tag": tag}, kb=64): return finish("aborted_resource_limit", "events")
    decoded = bob
    matched = toeplitz_tag(bob.reshape(-1), seed).hex() == tag; checks = 1
    if not add("FRAME_TAG_CHECK", "bob_local", -1, {"value": "match" if matched else "mismatch"}): return finish("aborted_resource_limit", "events")
    return finish("verified_success" if matched else "verify_failed", "" if matched else "toeplitz_mismatch")
