"""Executable, fail-closed formal binary LDPC v3 frame protocol."""
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
from .codebook_long_v3 import canonical_matrix_bytes, generate_master, parse_matrix_bytes, prefix_rows
from .shared import canonical_event, locked_seed_bits, sha256_bytes, status_flags, toeplitz_tag, transcript_summary, verification_union_bound

METHOD = "ldpc_formal_v3"
N = 256
DIMENSION = 1024
MAPPING = "gray"
PREFIX_IDS = ("p050", "p0625", "p075", "p0875")
CANDIDATE_IDS = (1, 0, 1, 2, 0, 0, 1, 3, 2, 3)
SELECTION_BINDING_SHA256 = "1319938ff6c989642950d4e3f3dba7ae9d0cbea14eb0c1e3a90d826e4fbc3227"
DEFAULT_CAPS = {"wall_s": 10.0, "decoder_calls": 40, "events": 100}
_NON_ATTEMPTED = {"preflight_unavailable", "invalid_input", "unsupported_domain", "backend_unavailable"}


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _syndrome(h: np.ndarray, bits: np.ndarray) -> np.ndarray:
    return (np.asarray(h, dtype=np.uint8) @ np.asarray(bits, dtype=np.uint8) % 2).astype(np.uint8)


def _params(p_hat: float) -> dict[str, Any]:
    return {"error_rate": min(max(float(p_hat), 1e-4), .49), "max_iter": 50,
            "bp_method": "minimum_sum", "ms_scaling_factor": 1.0, "schedule": "serial",
            "omp_thread_count": 1, "serial_schedule_order": list(range(N)),
            "osd_method": "OSD_0", "osd_order": 0}


def _valid_hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _validate_calibration(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {"calibration_role", "dimension", "mapping", "frame_len_symbols", "source_sha256", "planes", "calibration_sha256"}:
        raise ValueError("calibration contract keys")
    base = dict(value); digest = base.pop("calibration_sha256")
    if not _valid_hex64(digest) or sha256_bytes(_compact(base)) != digest:
        raise ValueError("calibration hash")
    if (base["calibration_role"], base["dimension"], base["mapping"], base["frame_len_symbols"]) != ("sacrificed_tuning_only", DIMENSION, MAPPING, N) or not _valid_hex64(base["source_sha256"]):
        raise ValueError("calibration identity")
    planes = base["planes"]
    if not isinstance(planes, list) or len(planes) != 10:
        raise ValueError("calibration planes")
    for plane_id, row in enumerate(planes):
        if not isinstance(row, Mapping) or set(row) != {"plane_id", "errors", "total_bits", "p_hat"} or row["plane_id"] != plane_id:
            raise ValueError("calibration plane schema")
        errors, total, p = row["errors"], row["total_bits"], row["p_hat"]
        if any(isinstance(x, bool) for x in (errors, total)) or not isinstance(errors, int) or not isinstance(total, int) or not 0 <= errors <= total or total <= 0:
            raise ValueError("calibration counts")
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(float(p)) or not 0 <= float(p) < .5 or not math.isclose(float(p), errors / total, rel_tol=0.0, abs_tol=1e-15):
            raise ValueError("calibration p_hat")
    return dict(value)


def _codebooks() -> list[dict[str, np.ndarray]]:
    books = []
    for plane, candidate in enumerate(CANDIDATE_IDS):
        master = generate_master(N, plane, candidate)
        prefixes: dict[str, np.ndarray] = {}
        for prefix, rows in prefix_rows(N).items():
            # Canonical round trip is part of the frozen domain validation.
            h = master[:rows]
            parsed = parse_matrix_bytes(canonical_matrix_bytes(h))
            if not np.array_equal(parsed, h):
                raise ValueError("codebook canonical round trip")
            prefixes[prefix] = parsed
        books.append(prefixes)
    return books


def _production_preflight(h: np.ndarray, p_hat: float) -> dict[str, Any]:
    try:
        version = importlib.metadata.version("ldpc")
        if version != "2.4.1":
            return {"status": "preflight_unavailable", "dependency_version": version, "backend_name": ""}
        from ldpc import BpOsdDecoder  # type: ignore[import-not-found]
        BpOsdDecoder(h, **_params(p_hat))
        return {"status": "ok", "dependency_version": "2.4.1", "backend_name": "ldpc.BpOsdDecoder"}
    except Exception:
        return {"status": "preflight_unavailable", "dependency_version": "", "backend_name": ""}


def _validate_outcome_v3(row: Mapping[str, Any], events: list[Mapping[str, Any]] | None = None) -> None:
    required = {"dataset_id", "frame_id", "n_pairs", "pair_idx_sequence_sha256", "method", "attempted", "denominator_included", "status", "failure_reason", "dimension", "frame_len_symbols", "raw_ser", "verification_invoked", "verification_seed_id", "verification_tag_bits", "epsilon_ec", "key_dependent_disclosure_bits_total", "public_control_bits_total", "transcript_first_event_id", "transcript_last_event_id", "transcript_sha256", "runtime_s", "global_rounds_attempted", "verification_check_count", "terminal_prefix_id", "ldpc_syndrome_bits", "verification_tag_bits_component", "selection_binding_sha256", "candidate_ids", "calibration_sha256", "mapping", "leakage_comparison_policy", "backend_name", "backend_version"}
    if set(row) != required: raise ValueError("v3 outcome keys")
    string_keys = {"dataset_id", "frame_id", "pair_idx_sequence_sha256", "method", "status", "failure_reason", "verification_seed_id", "transcript_sha256", "terminal_prefix_id", "selection_binding_sha256", "calibration_sha256", "mapping", "leakage_comparison_policy", "backend_name", "backend_version"}
    integer_keys = {"n_pairs", "dimension", "frame_len_symbols", "verification_tag_bits", "key_dependent_disclosure_bits_total", "public_control_bits_total", "global_rounds_attempted", "verification_check_count", "ldpc_syndrome_bits", "verification_tag_bits_component"}
    if any(not isinstance(row[k], str) for k in string_keys) or any(not isinstance(row[k], int) or isinstance(row[k], bool) for k in integer_keys): raise ValueError("v3 exact types")
    if row["method"] != METHOD or row["n_pairs"] != N or row["dimension"] != DIMENSION or row["frame_len_symbols"] != N or row["mapping"] != MAPPING or row["pair_idx_sequence_sha256"] != sha256_bytes(",".join(str(i) for i in range(N)).encode("ascii")): raise ValueError("v3 identity")
    if row["candidate_ids"] != list(CANDIDATE_IDS) or row["selection_binding_sha256"] != SELECTION_BINDING_SHA256 or not _valid_hex64(row["calibration_sha256"]): raise ValueError("v3 binding")
    if not isinstance(row["attempted"], bool) or not isinstance(row["denominator_included"], bool) or not isinstance(row["verification_invoked"], bool): raise ValueError("v3 booleans")
    attempted, denom = status_flags(str(row["status"]))
    if (row["attempted"], row["denominator_included"]) != (attempted, denom): raise ValueError("status flags")
    if not isinstance(row["runtime_s"], (int, float)) or isinstance(row["runtime_s"], bool) or not math.isfinite(float(row["runtime_s"])) or float(row["runtime_s"]) < 0 or not isinstance(row["raw_ser"], (int, float)) or isinstance(row["raw_ser"], bool) or (not math.isnan(float(row["raw_ser"])) and (not math.isfinite(float(row["raw_ser"])) or float(row["raw_ser"]) < 0)): raise ValueError("runtime/raw ser")
    if row["leakage_comparison_policy"] != "method_specific_not_cross_ranked": raise ValueError("leakage policy")
    if not attempted:
        if events or row["verification_invoked"] or any(row[k] != 0 for k in ("verification_tag_bits", "epsilon_ec", "key_dependent_disclosure_bits_total", "public_control_bits_total", "global_rounds_attempted", "verification_check_count", "ldpc_syndrome_bits")) or row["terminal_prefix_id"] != "": raise ValueError("non-attempted accounting")
        return
    if not row["verification_invoked"] or row["verification_tag_bits"] != 64 or row["verification_tag_bits_component"] != 64 or row["public_control_bits_total"] != 2623 or not _valid_hex64(row["verification_seed_id"]) or row["backend_version"] != "2.4.1" or not row["backend_name"]: raise ValueError("verification accounting")
    if isinstance(row["epsilon_ec"], bool) or not isinstance(row["epsilon_ec"], (int, float)) or not math.isfinite(float(row["epsilon_ec"])) or row["verification_check_count"] < 0 or row["global_rounds_attempted"] < row["verification_check_count"] or row["epsilon_ec"] != verification_union_bound(row["verification_check_count"]): raise ValueError("round accounting")
    if row["global_rounds_attempted"] > 4 or row["verification_check_count"] > 4 or (row["terminal_prefix_id"] and row["terminal_prefix_id"] not in PREFIX_IDS): raise ValueError("terminal domain")
    if row["terminal_prefix_id"] and row["terminal_prefix_id"] != PREFIX_IDS[row["global_rounds_attempted"] - 1]: raise ValueError("terminal prefix relationship")
    if row["status"] in {"verified_success", "verify_failed"}:
        expected_rounds = PREFIX_IDS.index(row["terminal_prefix_id"]) + 1
        if row["global_rounds_attempted"] != expected_rounds or row["verification_check_count"] != expected_rounds or row["ldpc_syndrome_bits"] != 10 * prefix_rows(N)[row["terminal_prefix_id"]]: raise ValueError("terminal success/failure relationship")
    if row["key_dependent_disclosure_bits_total"] != row["ldpc_syndrome_bits"] + 64: raise ValueError("key disclosure relationship")
    if events is not None:
        summary = transcript_summary(events)
        if summary["transcript_sha256"] != row["transcript_sha256"] or summary["key_dependent_disclosure_bits_total"] != row["key_dependent_disclosure_bits_total"] or summary["public_control_bits_total"] != row["public_control_bits_total"]: raise ValueError("transcript accounting")
        if events and [e["event_id"] for e in events] != list(range(1, len(events) + 1)): raise ValueError("event ids")
        if (row["transcript_first_event_id"], row["transcript_last_event_id"]) != ((1, len(events)) if events else (None, None)): raise ValueError("event boundaries")
        for event in events:
            canonical_event(event)
            if event["method"] != METHOD or event["frame_key"] != f"{row['dataset_id']}:{row['frame_id']}" or event["parent_event_id"] is not None or not isinstance(event["pass_id"], int) or not isinstance(event.get("plane_id"), int): raise ValueError("event schema")
        if attempted:
            if len(events) < 2 or [(events[0]["event_type"], events[0]["direction"], events[0]["pass_id"], events[0]["plane_id"], events[0]["key_dependent_bits"], events[0]["public_control_bits"], set(events[0]["payload"])), (events[1]["event_type"], events[1]["direction"], events[1]["pass_id"], events[1]["plane_id"], events[1]["key_dependent_bits"], events[1]["public_control_bits"], set(events[1]["payload"]))] != [("VERIFICATION_SEED", "control", -1, -1, 0, 2623, {"seed_id", "seed_bit_length"}), ("VERIFICATION_TAG", "alice_to_bob", -1, -1, 64, 0, {"tag"})]: raise ValueError("tag event order")
            if sum(e["event_type"] == "VERIFICATION_SEED" for e in events) != 1 or sum(e["event_type"] == "VERIFICATION_TAG" for e in events) != 1: raise ValueError("tag event multiplicity")
            if events[0]["payload"]["seed_id"] != row["verification_seed_id"] or events[0]["payload"]["seed_bit_length"] != 2623 or not isinstance(events[0]["payload"]["seed_bit_length"], int) or not isinstance(events[1]["payload"]["tag"], str) or len(events[1]["payload"]["tag"]) != 16 or any(c not in "0123456789abcdef" for c in events[1]["payload"]["tag"]): raise ValueError("seed/tag payload")
            syndromes = [e for e in events if e["event_type"] == "SYNDROME"]
            checks = [e for e in events if e["event_type"] == "FRAME_TAG_CHECK"]
            if len(checks) != row["verification_check_count"] or sum(e["key_dependent_bits"] for e in syndromes) != row["ldpc_syndrome_bits"] or row["key_dependent_disclosure_bits_total"] != row["ldpc_syndrome_bits"] + 64: raise ValueError("event disclosure relationship")
            for event in syndromes:
                expected_bits = (128, 32, 32, 32)[event["pass_id"]] if event["pass_id"] in range(4) else -1
                syndrome_hex = event["payload"].get("syndrome") if set(event["payload"]) == {"syndrome"} else None
                if event["direction"] != "alice_to_bob" or event["plane_id"] not in range(10) or event["pass_id"] not in range(4) or event["key_dependent_bits"] != expected_bits or event["public_control_bits"] != 0 or not isinstance(syndrome_hex, str) or len(syndrome_hex) != (expected_bits + 7) // 8 * 2 or any(c not in "0123456789abcdef" for c in syndrome_hex): raise ValueError("syndrome event schema")
            for index, event in enumerate(checks):
                if (event["direction"], event["pass_id"], event["plane_id"], event["key_dependent_bits"], event["public_control_bits"], set(event["payload"])) != ("bob_local", index, -1, 0, 0, {"value"}) or event["payload"]["value"] not in {"match", "mismatch"}: raise ValueError("tag-check event schema")
            body = [event for event in events[2:] if event["event_type"] != "ABORT"]
            cursor = 0
            for pass_id in range(row["verification_check_count"]):
                for plane in range(10):
                    if cursor >= len(body) or body[cursor]["event_type"] != "SYNDROME" or body[cursor]["pass_id"] != pass_id or body[cursor]["plane_id"] != plane: raise ValueError("syndrome event order")
                    cursor += 1
                if cursor >= len(body) or body[cursor]["event_type"] != "FRAME_TAG_CHECK" or body[cursor]["pass_id"] != pass_id: raise ValueError("tag-check event order")
                cursor += 1
            for plane, event in enumerate(body[cursor:]):
                if event["event_type"] != "SYNDROME" or event["pass_id"] != row["global_rounds_attempted"] - 1 or event["plane_id"] != plane: raise ValueError("partial round event order")


def validate_outcome_v3(row: Mapping[str, Any], events: list[Mapping[str, Any]] | None = None) -> None:
    """Strict public validator for the v3 outcome and optional transcript."""
    _validate_outcome_v3(row, events)


def run_ldpc_formal_v3(alice_symbols: Any, bob_symbols: Any, *, frozen_calibration: Mapping[str, Any], selection_binding_sha256: str = SELECTION_BINDING_SHA256, dimension: int = DIMENSION, mapping: str = MAPPING, locked_seed: Mapping[str, Any] | None = None, dataset_id: str = "synthetic", frame_id: str = "0", _caps: Mapping[str, float] | None = None, _clock: Callable[[], float] = time.monotonic, _decoder_factory: Callable[..., Any] | None = None, _preflight: Mapping[str, Any] | None = None) -> dict[str, Any]:
    started = _clock(); events: list[dict[str, Any]] = []; limits = {**DEFAULT_CAPS, **dict(_caps or {})}; key = f"{dataset_id}:{frame_id}"; next_id = 1
    def add(kind: str, direction: str, pass_id: int, plane: int, payload: dict[str, Any], kb: int = 0, cb: int = 0) -> bool:
        nonlocal next_id
        if len(events) >= int(limits["events"]): return False
        event = {"event_id": next_id, "frame_key": key, "method": METHOD, "event_type": kind, "direction": direction, "parent_event_id": None, "pass_id": pass_id, "plane_id": plane, "key_dependent_bits": kb, "public_control_bits": cb, "payload": payload}
        canonical_event(event); events.append(event); next_id += 1; return True
    raw_ser = float("nan"); books: list[dict[str, np.ndarray]] = []; calibration_hash = str(frozen_calibration.get("calibration_sha256", "")) if isinstance(frozen_calibration, Mapping) else ""
    backend_name = backend_version = ""; rounds = checks = syndrome_bits = calls = 0; terminal = ""; decoded: np.ndarray | None = None
    def finish(status: str, reason: str) -> dict[str, Any]:
        nonlocal terminal
        if status == "aborted_resource_limit" and len(events) < int(limits["events"]): add("ABORT", "control", max(0, rounds - 1), -1, {"cap": reason, "reason": "resource_limit"})
        summary = transcript_summary(events); attempted = status not in _NON_ATTEMPTED
        outcome = {"dataset_id": str(dataset_id), "frame_id": str(frame_id), "n_pairs": N, "pair_idx_sequence_sha256": sha256_bytes(",".join(str(i) for i in range(N)).encode("ascii")), "method": METHOD, "attempted": attempted, "denominator_included": attempted, "status": status, "failure_reason": reason, "dimension": DIMENSION, "frame_len_symbols": N, "raw_ser": raw_ser, "verification_invoked": attempted, "verification_seed_id": str(locked_seed.get("seed_id", "")) if attempted and locked_seed else "", "verification_tag_bits": 64 if attempted else 0, "epsilon_ec": verification_union_bound(checks) if attempted else 0.0, "key_dependent_disclosure_bits_total": summary["key_dependent_disclosure_bits_total"], "public_control_bits_total": summary["public_control_bits_total"], "transcript_first_event_id": events[0]["event_id"] if events else None, "transcript_last_event_id": events[-1]["event_id"] if events else None, "transcript_sha256": summary["transcript_sha256"], "runtime_s": max(0.0, _clock() - started), "global_rounds_attempted": rounds, "verification_check_count": checks, "terminal_prefix_id": terminal, "ldpc_syndrome_bits": syndrome_bits, "verification_tag_bits_component": 64 if attempted else 0, "selection_binding_sha256": SELECTION_BINDING_SHA256, "candidate_ids": list(CANDIDATE_IDS), "calibration_sha256": calibration_hash, "mapping": MAPPING, "leakage_comparison_policy": "method_specific_not_cross_ranked", "backend_name": backend_name, "backend_version": backend_version}
        _validate_outcome_v3(outcome, events); return {"outcome": outcome, "events": events, "decoded_bits": None if decoded is None else decoded.copy()}
    try:
        if (not all(name in limits and isinstance(limits[name], (int, float)) and not isinstance(limits[name], bool) and float(limits[name]) >= 0 for name in ("wall_s", "decoder_calls", "events")) or int(limits["events"]) < 2):
            raise ValueError("invalid caps")
        a, b = np.asarray(alice_symbols), np.asarray(bob_symbols)
        if dimension != DIMENSION or mapping != MAPPING or a.shape != (N,) or b.shape != (N,) or not np.issubdtype(a.dtype, np.integer) or not np.issubdtype(b.dtype, np.integer) or np.any(a < 0) or np.any(a >= DIMENSION) or np.any(b < 0) or np.any(b >= DIMENSION) or locked_seed is None or not isinstance(dataset_id, str) or not isinstance(frame_id, (str, int)):
            raise ValueError("v3 input domain")
        seed = locked_seed_bits(locked_seed, N * 10 + 63)
    except Exception as exc:
        return finish("invalid_input", str(exc))
    raw_ser = frame_symbol_error_rate(a, b)
    try:
        _validate_calibration(frozen_calibration)
        if selection_binding_sha256 != SELECTION_BINDING_SHA256: raise ValueError("selection binding")
        books = _codebooks()
    except Exception as exc:
        return finish("unsupported_domain", str(exc))
    check = dict(_preflight) if _preflight is not None else _production_preflight(books[0]["p050"], float(frozen_calibration["planes"][0]["p_hat"]))
    if _preflight is not None and (set(check) != {"status", "dependency_version", "backend_name"} or check.get("status") != "ok" or check.get("dependency_version") != "2.4.1" or not isinstance(check.get("backend_name"), str) or not check["backend_name"]): return finish("preflight_unavailable", "invalid injected preflight")
    if check.get("status") != "ok" or check.get("dependency_version") != "2.4.1": return finish("preflight_unavailable", "ldpc pinned dependency/API unavailable")
    backend_name, backend_version = str(check.get("backend_name", "test_injected")), str(check["dependency_version"])
    factory = _decoder_factory
    if factory is None:
        try:
            from ldpc import BpOsdDecoder  # type: ignore[import-not-found]
            factory = BpOsdDecoder
        except Exception: return finish("preflight_unavailable", "ldpc constructor unavailable")
    alice = symbols_to_bits(a.astype(np.int64), DIMENSION, MAPPING).astype(np.uint8)
    bob = symbols_to_bits(b.astype(np.int64), DIMENSION, MAPPING).astype(np.uint8).copy()
    alice_flat = alice.reshape(-1); tag = toeplitz_tag(alice_flat, seed).hex()
    if not add("VERIFICATION_SEED", "control", -1, -1, {"seed_id": locked_seed["seed_id"], "seed_bit_length": 2623}, cb=2623) or not add("VERIFICATION_TAG", "alice_to_bob", -1, -1, {"tag": tag}, kb=64): return finish("aborted_resource_limit", "events")
    for round_id, prefix in enumerate(PREFIX_IDS):
        rounds += 1; rows = prefix_rows(N)[prefix]; prior = 0 if round_id == 0 else prefix_rows(N)[PREFIX_IDS[round_id - 1]]
        for plane in range(10):
            if _clock() - started >= float(limits["wall_s"]): return finish("aborted_resource_limit", "wall_s")
            if calls >= int(limits["decoder_calls"]): return finish("aborted_resource_limit", "decoder_calls")
            h = books[plane][prefix]; syndrome = _syndrome(h, alice[:, plane]); delta = syndrome ^ _syndrome(h, bob[:, plane]); extension = syndrome[prior:]
            if not add("SYNDROME", "alice_to_bob", round_id, plane, {"syndrome": np.packbits(extension, bitorder="big").tobytes().hex()}, kb=len(extension)): return finish("aborted_resource_limit", "events")
            syndrome_bits += len(extension)
            try:
                calls += 1; err = np.asarray(factory(h, **_params(float(frozen_calibration["planes"][plane]["p_hat"]))).decode(delta)).reshape(-1)
            except Exception: terminal = prefix; return finish("decoder_error", "decoder exception")
            if err.size != N or np.any((err != 0) & (err != 1)): terminal = prefix; return finish("decoder_error", "nonbinary decoder error")
            err = err.astype(np.uint8)
            if not np.array_equal(_syndrome(h, err), delta): terminal = prefix; return finish("syndrome_inconsistent", "decoder syndrome mismatch")
            bob[:, plane] ^= err
        checks += 1; terminal = prefix
        bob_tag = toeplitz_tag(bob.reshape(-1), seed).hex(); matched = bob_tag == tag
        if not add("FRAME_TAG_CHECK", "bob_local", round_id, -1, {"value": "match" if matched else "mismatch"}): return finish("aborted_resource_limit", "events")
        if matched: decoded = bob; return finish("verified_success", "")
    decoded = bob; return finish("verify_failed", "toeplitz_mismatch")
