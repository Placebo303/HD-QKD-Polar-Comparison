"""Fail-closed formal LDPC-v2 decoder/rate-policy contract.

This module is deliberately separate from :mod:`ldpc`: v1 remains immutable.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import numpy as np

from ..utils.bitops import frame_symbol_error_rate, symbols_to_bits
from .ldpc import N, RATES, _input, _selection_hash, _syndrome, select_rate
from .codebook_v2 import verify_v2_codebook_entry
from .shared import (
    locked_seed_bits,
    preflight_ldpc,
    sha256_bytes,
    toeplitz_tag,
    transcript_summary,
    validate_outcome,
    verification_result,
)

METHOD = "ldpc_formal_v2"
ORDERED_RATES = ("r050", "r0375", "r025", "r0125")
DECODERS = (("OSD_0", 0), ("OSD_CS", 1), ("OSD_CS", 2))
DECODER_COMPLEXITY = {("OSD_0", 0): 0, ("OSD_CS", 1): 1, ("OSD_CS", 2): 2}
DEFAULT_CAPS = {"wall_s": 5.0}
_FIXED = {
    "max_iter": 50, "bp_method": "minimum_sum", "ms_scaling_factor": 1.0,
    "schedule": "serial", "omp_thread_count": 1, "serial_schedule_order": list(range(N)),
}


def _compact_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_policy(*, rate_margin: int, osd_method: str, osd_order: int) -> dict[str, Any]:
    """Return one pre-registered policy with its compact-JSON identifier."""
    if rate_margin not in (0, 1, 2) or (osd_method, osd_order) not in DECODERS:
        raise ValueError("policy is outside the frozen v2 grid")
    policy = {"rate_margin": rate_margin, **_FIXED, "osd_method": osd_method, "osd_order": osd_order}
    return {**policy, "policy_id": sha256_bytes(_compact_json(policy))}


def policy_grid() -> list[dict[str, Any]]:
    return [canonical_policy(rate_margin=margin, osd_method=method, osd_order=order)
            for margin in (0, 1, 2) for method, order in DECODERS]


def validate_policy(policy: Mapping[str, Any]) -> dict[str, Any]:
    try:
        canonical = canonical_policy(rate_margin=int(policy["rate_margin"]), osd_method=str(policy["osd_method"]), osd_order=int(policy["osd_order"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid frozen v2 policy") from exc
    if dict(policy) != canonical:
        raise ValueError("frozen policy is not canonical")
    return canonical


def decoder_params(policy: Mapping[str, Any], p_hat: float) -> dict[str, Any]:
    selected = validate_policy(policy)
    if not math.isfinite(float(p_hat)) or not 0 <= float(p_hat) < .5:
        raise ValueError("frozen p_hat outside [0,.5)")
    return {"error_rate": min(max(float(p_hat), 1e-4), .49), **{key: selected[key] for key in _FIXED},
            "osd_method": selected["osd_method"], "osd_order": selected["osd_order"]}


def effective_rate(p_hat: float, rate_margin: int) -> str:
    if not math.isfinite(float(p_hat)) or not 0 <= float(p_hat) < .5:
        raise ValueError("frozen p_hat outside [0,.5)")
    if rate_margin not in (0, 1, 2):
        raise ValueError("invalid rate margin")
    base = select_rate(float(p_hat))
    if base not in ORDERED_RATES:
        raise ValueError("base rate outside frozen ordered rates")
    return ORDERED_RATES[min(ORDERED_RATES.index(base) + rate_margin, len(ORDERED_RATES) - 1)]


def probe_constructors(*, decoder_factory: Callable[..., Any] | None = None, dependency_version: str | None = None) -> list[dict[str, Any]]:
    """Probe exactly the three included constructors; unsupported choices stay recorded."""
    factory = decoder_factory
    if factory is None:
        try:
            from ldpc import BpOsdDecoder  # type: ignore[import-not-found]
        except (ImportError, AttributeError):
            factory = None
        else:
            factory = BpOsdDecoder
    if dependency_version is None:
        try:
            version = importlib.metadata.version("ldpc")
        except importlib.metadata.PackageNotFoundError:
            version = None
    else:
        version = dependency_version
    h = np.zeros((1, N), dtype=np.uint8); h[0, 0] = 1
    records = []
    for policy in policy_grid()[0:3]:
        # one policy per decoder pair is enough; the three rate margins do not affect construction
        probe = {"policy_id": policy["policy_id"], "osd_method": policy["osd_method"], "osd_order": policy["osd_order"],
                 "dependency_version": version, "supported": False,
                 "error_class": None, "error_message": None}
        if version == "2.4.1" and factory is not None:
            try:
                factory(h, **decoder_params(policy, .1))
            except Exception as exc:
                probe["error_class"], probe["error_message"] = type(exc).__name__, str(exc)
            else:
                probe["supported"] = True
        else:
            probe["error_class"], probe["error_message"] = "BackendUnavailable", "ldpc==2.4.1 constructor unavailable"
        records.append(probe)
    return records


def select_global_policy(policy_outcomes: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    """Select once from sacrificed outcomes, with the specified total ordering."""
    grid = {policy["policy_id"]: policy for policy in policy_grid()}
    if set(policy_outcomes) != set(grid):
        raise ValueError("selection needs exactly the nine frozen policies")
    ranked = []
    for policy_id, outcomes in policy_outcomes.items():
        policy = grid[policy_id]
        if not outcomes:
            raise ValueError("each policy needs sacrificed outcomes")
        successes = sum(str(row.get("status")) == "verified_success" for row in outcomes)
        disclosure = sum(int(row["key_dependent_disclosure_bits_total"]) for row in outcomes)
        runtime_ns = sum(int(row["runtime_ns"]) if "runtime_ns" in row else int(round(float(row["runtime_s"]) * 1e9)) for row in outcomes)
        complexity = DECODER_COMPLEXITY[(policy["osd_method"], policy["osd_order"])]
        ranked.append(((-successes, disclosure, complexity, policy_id), policy_id, {"verified_successes": successes, "key_dependent_disclosure_bits_total": disclosure, "decoder_complexity": complexity, "runtime_ns": runtime_ns}))
    ranked.sort(key=lambda item: item[0])
    _, selected_id, aggregate = ranked[0]
    return {"selected_policy": grid[selected_id], "selection_tuple": [-aggregate["verified_successes"], aggregate["key_dependent_disclosure_bits_total"], aggregate["decoder_complexity"], selected_id],
            "aggregates": {pid: agg for _, pid, agg in ranked}}


def _valid_plane(record: Any, selection_hash: str, mapping: str) -> tuple[float, str] | None:
    if not isinstance(record, Mapping): return None
    p_hat, errors, total = record.get("p_hat"), record.get("errors"), record.get("total_bits")
    if not isinstance(errors, int) or isinstance(errors, bool) or not isinstance(total, int) or isinstance(total, bool) or total <= 0 or not 0 <= errors <= total:
        return None
    if not isinstance(p_hat, (int, float)) or isinstance(p_hat, bool) or not math.isfinite(float(p_hat)) or not 0 <= float(p_hat) < .5:
        return None
    if not math.isclose(float(p_hat), errors / total, rel_tol=0., abs_tol=1e-15) or record.get("selected_input_sha256") != selection_hash or record.get("mapping") != mapping:
        return None
    return float(p_hat), select_rate(float(p_hat))


def _run_ldpc_formal_v2_for_test(alice_symbols: Any, bob_symbols: Any, *, dimension: int,
        frozen_calibration: Mapping[str, Any], frozen_policy: Mapping[str, Any],
        codebook_entries: Mapping[tuple[str, int], Mapping[str, Any]], codebook_bytes: Mapping[tuple[str, int], bytes],
        screening_manifest: Mapping[str, Any],
        dataset_id: str = "synthetic", frame_id: str = "0", mapping: str = "gray", locked_seed: Mapping[str, Any] | None = None,
        _caps: Mapping[str, float] | None = None, _clock: Callable[[], float] = time.monotonic,
        _decoder_factory: Callable[..., Any] | None = None, _preflight: Mapping[str, Any] | None = None) -> dict[str, Any]:
    started = _clock(); events: list[dict[str, Any]] = []; key = f"{dataset_id}:{frame_id}"; raw_ser = float("nan")
    limits = {**DEFAULT_CAPS, **(_caps or {})}; next_id = 1
    def add(kind: str, direction: str, plane: int, payload: dict[str, Any], kb: int = 0, cb: int = 0) -> None:
        nonlocal next_id
        events.append({"event_id": next_id, "frame_key": key, "method": METHOD, "event_type": kind, "direction": direction, "parent_event_id": None, "pass_id": -1, "plane_id": plane, "key_dependent_bits": kb, "public_control_bits": cb, "payload": payload}); next_id += 1
    def finish(status: str, failure: str, decoded: np.ndarray | None = None, invoke: bool = False, rates: list[str] | None = None, ids: list[str] | None = None) -> dict[str, Any]:
        ver = {"verification_invoked": False, "verification_tag_bits": 0, "epsilon_ec": 0.0}
        if invoke and _clock() - started >= float(limits["wall_s"]): status, failure, invoke = "aborted_resource_limit", "wall_s", False
        if invoke and decoded is not None:
            ver = verification_result(alice.reshape(-1), decoded.reshape(-1), locked_seed, invoked=True)
            seed = locked_seed_bits(locked_seed, alice.size + 63)
            add("VERIFICATION_SEED", "control", -1, {"seed_id": locked_seed["seed_id"], "seed_bit_length": len(seed)}, cb=len(seed))
            add("VERIFICATION_TAG", "alice_to_bob", -1, {"tag": toeplitz_tag(alice.reshape(-1), seed).hex()}, kb=64)
            if not ver["verified"]: status, failure = "verify_failed", "toeplitz_mismatch"
            if _clock() - started >= float(limits["wall_s"]): status, failure = "aborted_resource_limit", "wall_s"
        if status == "aborted_resource_limit": add("ABORT", "control", -1, {"cap": failure, "reason": "resource_limit"}, cb=1)
        summary = transcript_summary(events); syndrome_bits = sum(event["key_dependent_bits"] for event in events if event["event_type"] == "SYNDROME")
        out = {"dataset_id": dataset_id, "frame_id": str(frame_id), "n_pairs": 64, "pair_idx_sequence_sha256": hashlib.sha256(b",".join(str(i).encode() for i in range(64))).hexdigest(), "method": METHOD,
               "attempted": status not in {"preflight_unavailable", "invalid_input", "unsupported_domain", "backend_unavailable"}, "denominator_included": status not in {"preflight_unavailable", "invalid_input", "unsupported_domain", "backend_unavailable"}, "status": status, "failure_reason": failure,
               "dimension": dimension, "frame_len_symbols": 64, "raw_ser": raw_ser, "verification_invoked": ver["verification_invoked"], "verification_seed_id": locked_seed["seed_id"] if ver["verification_invoked"] else "", "verification_tag_bits": ver["verification_tag_bits"], "epsilon_ec": ver["epsilon_ec"],
               "key_dependent_disclosure_bits_total": summary["key_dependent_disclosure_bits_total"], "public_control_bits_total": summary["public_control_bits_total"], "transcript_first_event_id": events[0]["event_id"] if events else None, "transcript_last_event_id": events[-1]["event_id"] if events else None, "transcript_sha256": summary["transcript_sha256"], "runtime_s": max(0., _clock() - started), "ldpc_syndrome_bits": syndrome_bits, "verification_tag_bits_component": ver["verification_tag_bits"], "rate_ids": rates or [], "codebook_ids": ids or [], "policy_id": policy["policy_id"] if "policy" in locals() else "", "calibration_source_sha256": frozen_calibration.get("source_sha256", ""), "mapping": mapping, "leakage_comparison_policy": "method_specific_not_cross_ranked"}
        validate_outcome(out); return {"outcome": out, "events": events, "decoded_bits": None if decoded is None else decoded.copy()}
    try:
        policy = validate_policy(frozen_policy)
        if not isinstance(dimension, int) or dimension < 2 or dimension > 1024 or dimension & (dimension - 1):
            return finish("unsupported_domain", "q must be 2^m, m=1..10")
        if mapping not in {"gray", "natural"} or locked_seed is None: raise ValueError("mapping and locked seed required")
        alice, bob = _input(alice_symbols, dimension, mapping), _input(bob_symbols, dimension, mapping); locked_seed_bits(locked_seed, alice.size + 63)
    except (TypeError, ValueError) as exc:
        return finish("invalid_input", str(exc))
    raw_ser = frame_symbol_error_rate(np.asarray(alice_symbols), np.asarray(bob_symbols)); check = dict(_preflight) if _preflight is not None else preflight_ldpc()
    if check.get("status") != "ok": return finish("preflight_unavailable", "ldpc pinned dependency/API unavailable")
    if frozen_calibration.get("calibration_role") != "sacrificed_tuning_only" or frozen_calibration.get("mapping") != mapping or frozen_calibration.get("dimension") != dimension or not frozen_calibration.get("source_sha256"):
        return finish("unsupported_domain", "frozen calibration contract mismatch")
    cal = frozen_calibration.get("datasets", {}).get(str(dataset_id)); frames = cal.get("ordered_frame_keys") if isinstance(cal, Mapping) else None; planes = cal.get("planes") if isinstance(cal, Mapping) else None
    selection_hash = cal.get("selection_sha256") if isinstance(cal, Mapping) else None
    expected = _selection_hash(str(frozen_calibration["source_sha256"]), str(dataset_id), frames, mapping, dimension) if isinstance(frames, list) and all(isinstance(item, str) for item in frames) else ""
    if not isinstance(frames, list) or not frames or len(set(frames)) != len(frames) or cal.get("keys_count") != len(frames) or selection_hash != expected or not isinstance(planes, Mapping):
        return finish("unsupported_domain", "invalid frozen dataset calibration provenance")
    decoded = bob.copy(); rates: list[str] = []; ids: list[str] = []
    for plane_index in range(alice.shape[1]):
        if _clock() - started >= float(limits["wall_s"]): return finish("aborted_resource_limit", "wall_s", decoded, rates=rates, ids=ids)
        item = _valid_plane(planes.get(str(plane_index)), str(selection_hash), mapping)
        if item is None: return finish("unsupported_domain", "missing or inconsistent frozen plane calibration", decoded, rates=rates, ids=ids)
        p_hat, _base = item
        try: rate = effective_rate(p_hat, int(policy["rate_margin"])); h = verify_v2_codebook_entry(codebook_entries[(rate, plane_index)], codebook_bytes[(rate, plane_index)], screening_manifest)
        except (KeyError, ValueError) as exc: return finish("unsupported_domain", f"codebook: {exc}", decoded, rates=rates, ids=ids)
        rates.append(rate); ids.append(str(codebook_entries[(rate, plane_index)]["sha256"]))
        add("MATRIX_SELECTOR", "control", plane_index, {"matrix_id": ids[-1]}, cb=256); add("RATE_SELECTOR", "control", plane_index, {"rate_id": rate}, cb=len(rate.encode("ascii")) * 8)
        syndrome = _syndrome(h, alice[:, plane_index]); delta = syndrome ^ _syndrome(h, bob[:, plane_index]); add("SYNDROME", "alice_to_bob", plane_index, {"syndrome": np.packbits(syndrome, bitorder="big").tobytes().hex()}, kb=len(syndrome))
        try:
            factory = _decoder_factory
            if factory is None:
                from ldpc import BpOsdDecoder  # type: ignore[import-not-found]
                factory = BpOsdDecoder
            error = np.asarray(factory(h, **decoder_params(policy, p_hat)).decode(delta), dtype=np.uint8).reshape(-1) % 2
        except Exception as exc:
            return finish("aborted_resource_limit", "wall_s", decoded, rates=rates, ids=ids) if _clock() - started >= float(limits["wall_s"]) else finish("decoder_error", type(exc).__name__, decoded, rates=rates, ids=ids)
        if error.size != N: return finish("decoder_error", "decoder returned wrong length", decoded, rates=rates, ids=ids)
        if not np.array_equal(_syndrome(h, error), delta): return finish("syndrome_inconsistent", "decoder error syndrome mismatch", decoded, rates=rates, ids=ids)
        decoded[:, plane_index] = bob[:, plane_index] ^ error
        corrected = _syndrome(h, decoded[:, plane_index])
        if not np.array_equal(corrected, syndrome): return finish("syndrome_inconsistent", "corrected plane syndrome mismatch", decoded, rates=rates, ids=ids)
        add("PLANE_CONSISTENCY", "bob_local", plane_index, {"commitment": sha256_bytes(np.packbits(corrected, bitorder="big").tobytes())})
    return finish("verified_success", "", decoded, True, rates, ids)


def run_ldpc_formal_v2(alice_symbols: Any, bob_symbols: Any, *, dimension: int, frozen_calibration: Mapping[str, Any], frozen_policy: Mapping[str, Any], codebook_entries: Mapping[tuple[str, int], Mapping[str, Any]], codebook_bytes: Mapping[tuple[str, int], bytes], screening_manifest: Mapping[str, Any], dataset_id: str = "synthetic", frame_id: str = "0", mapping: str = "gray", locked_seed: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _run_ldpc_formal_v2_for_test(alice_symbols, bob_symbols, dimension=dimension, frozen_calibration=frozen_calibration, frozen_policy=frozen_policy, codebook_entries=codebook_entries, codebook_bytes=codebook_bytes, screening_manifest=screening_manifest, dataset_id=dataset_id, frame_id=frame_id, mapping=mapping, locked_seed=locked_seed)
