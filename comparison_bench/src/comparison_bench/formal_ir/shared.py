"""Small pure helpers shared by the future formal Cascade and LDPC runners."""
from __future__ import annotations

import hashlib
import importlib.metadata
import inspect
import json
import secrets
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np
import pandas as pd

FORMAL_ARTIFACTS = (
    "pre_run_plan.json", "formal_frame_outcomes.csv", "formal_transcript.jsonl",
    "formal_run_manifest.json", "formal_codebook_manifest.json", "formal_qualification_report.json",
)
FORMAL_STATUSES = (
    "preflight_unavailable", "invalid_input", "unsupported_domain", "backend_unavailable",
    "aborted_resource_limit", "decoder_error", "syndrome_inconsistent", "decode_failed",
    "verify_failed", "verified_success",
)
FORMAL_BP_OSD_FIXED_PARAMS = {
    "max_iter": 50, "bp_method": "minimum_sum", "ms_scaling_factor": 1.0,
    "schedule": "serial", "omp_thread_count": 1, "serial_schedule_order": list(range(64)),
    "osd_method": "OSD_0", "osd_order": 0,
}
_NON_ATTEMPTED = set(FORMAL_STATUSES[:4])
_PAYLOAD_KEYS = {
    "parity", "syndrome", "tag", "block_range", "subblock_range", "message_path",
    "source_event_id", "source_block_id", "source_path", "commitment", "matrix_id", "rate_id",
    "reason", "cap", "value", "note", "seed_id", "seed_bit_length", "derived_seed_hex", "derived_seed_id",
}
_BP_OSD_API_PARAMS = ("error_rate", "max_iter", "bp_method", "ms_scaling_factor", "schedule", "omp_thread_count", "serial_schedule_order", "osd_method", "osd_order")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _missing_bp_osd_api_params(api_description: str) -> list[str]:
    text = api_description.lower()
    return [name for name in _BP_OSD_API_PARAMS if name.lower() not in text]


def preflight_ldpc(*, dependency_version: str | None = None, api_description: str | None = None, decoder_constructor: Any = None) -> dict[str, Any]:
    """Fail closed without installing or importing an unpinned LDPC backend."""
    if dependency_version is None:
        try:
            version = importlib.metadata.version("ldpc")
        except importlib.metadata.PackageNotFoundError:
            version = None
    else:
        version = dependency_version
    description = api_description or ""
    constructor = decoder_constructor
    if version == "2.4.1" and constructor is None:
        try:
            from ldpc import BpOsdDecoder  # type: ignore[import-not-found]
        except (ImportError, AttributeError):
            pass
        else:
            constructor = BpOsdDecoder
            if not description:
                parts = [inspect.getdoc(BpOsdDecoder) or "", str(BpOsdDecoder)]
                try:
                    parts.append(str(inspect.signature(BpOsdDecoder)))
                except (TypeError, ValueError):
                    pass
                description = "\n".join(part for part in parts if part)
    missing_api_params = _missing_bp_osd_api_params(description) if version == "2.4.1" else list(_BP_OSD_API_PARAMS)
    probe_attempted = False
    probe_error_class = probe_error_message = None
    probe_ok = False
    if version == "2.4.1" and not missing_api_params and constructor is not None:
        probe_attempted = True
        h_probe = np.zeros((1, 64), dtype=np.uint8)
        h_probe[0, 0] = 1
        try:
            constructor(h_probe, **formal_bp_osd_params(0.1))
        except Exception as exc:  # fail closed on the backend's public constructor boundary
            probe_error_class = type(exc).__name__
            probe_error_message = str(exc)
        else:
            probe_ok = True
    api_available = not missing_api_params and probe_ok
    ok = version == "2.4.1" and api_available
    return {"status": "ok" if ok else "preflight_unavailable", "dependency": "ldpc", "required_version": "2.4.1", "installed_version": version, "api_available": api_available, "missing_api_params": missing_api_params, "constructor_probe_attempted": probe_attempted, "constructor_probe_ok": probe_ok, "probe_error_class": probe_error_class, "probe_error_message": probe_error_message}


def formal_bp_osd_params(error_rate: float) -> dict[str, Any]:
    """The only allowed R4 decoder configuration; callers supply locked p_hat."""
    if not 0 < float(error_rate) < 0.5:
        raise ValueError("formal LDPC error_rate must be in (0, .5)")
    return {"error_rate": float(error_rate), **FORMAL_BP_OSD_FIXED_PARAMS}


def status_flags(status: str) -> tuple[bool, bool]:
    if status not in FORMAL_STATUSES:
        raise ValueError(f"unknown formal status: {status}")
    return (status not in _NON_ATTEMPTED, status not in _NON_ATTEMPTED)


def validate_outcome(row: Mapping[str, Any]) -> None:
    required = {"dataset_id", "frame_id", "n_pairs", "pair_idx_sequence_sha256", "method", "attempted", "denominator_included", "status", "failure_reason", "dimension", "frame_len_symbols", "raw_ser", "verification_invoked", "verification_seed_id", "verification_tag_bits", "epsilon_ec", "key_dependent_disclosure_bits_total", "public_control_bits_total", "transcript_first_event_id", "transcript_last_event_id", "transcript_sha256", "runtime_s"}
    missing = required.difference(row)
    if missing:
        raise ValueError(f"formal outcome missing fields: {sorted(missing)}")
    attempted, denominator = status_flags(str(row["status"]))
    if (bool(row["attempted"]), bool(row["denominator_included"])) != (attempted, denominator):
        raise ValueError("attempted/denominator flags contradict status precedence")
    if int(row["n_pairs"]) != 64:
        raise ValueError("formal v1 requires exactly 64 pairs")
    if not bool(row["verification_invoked"]) and (int(row["verification_tag_bits"]) != 0 or float(row["epsilon_ec"]) != 0):
        raise ValueError("verification not invoked must disclose zero tag and epsilon")


def _bits(bits: Iterable[int], *, expected: int | None = None) -> np.ndarray:
    out = np.asarray(list(bits), dtype=np.uint8).reshape(-1)
    if np.any((out != 0) & (out != 1)) or (expected is not None and len(out) != expected):
        raise ValueError("expected a binary vector of the locked length")
    return out


def pack_bits_msb(bits: Iterable[int]) -> bytes:
    data = _bits(bits)
    return np.packbits(data, bitorder="big").tobytes()


def unpack_bits_msb(data: bytes, bit_length: int) -> np.ndarray:
    if bit_length < 0 or len(data) != (bit_length + 7) // 8:
        raise ValueError("packed bit length does not match bytes")
    all_bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8), bitorder="big")
    if len(all_bits) > bit_length and np.any(all_bits[bit_length:]):
        raise ValueError("unused low bits must be zero")
    return all_bits[:bit_length].astype(np.uint8)


def seed_record(seed_bits: Iterable[int]) -> dict[str, Any]:
    bits = _bits(seed_bits)
    packed = pack_bits_msb(bits)
    return {"seed_hex": packed.hex(), "seed_bit_length": int(len(bits)), "seed_id": sha256_bytes(packed)}


def materialize_seed_record(bit_length: int) -> dict[str, Any]:
    if bit_length < 1:
        raise ValueError("seed bit length must be positive")
    packed = bytearray(secrets.token_bytes((bit_length + 7) // 8))
    unused_low_bits = (-bit_length) % 8
    if unused_low_bits:
        packed[-1] &= (0xFF << unused_low_bits) & 0xFF
    return seed_record(unpack_bits_msb(bytes(packed), bit_length))


def locked_seed_bits(record: Mapping[str, Any], expected_bit_length: int) -> np.ndarray:
    if set(("seed_hex", "seed_bit_length", "seed_id")).difference(record):
        raise ValueError("incomplete locked seed record")
    if int(record["seed_bit_length"]) != expected_bit_length:
        raise ValueError("locked seed has wrong bit length")
    raw = bytes.fromhex(str(record["seed_hex"]))
    if sha256_bytes(raw) != record["seed_id"]:
        raise ValueError("locked seed id mismatch")
    return unpack_bits_msb(raw, expected_bit_length)


def toeplitz_tag(bits: Iterable[int], seed_bits: Iterable[int], tag_bits: int = 64) -> bytes:
    x = _bits(bits)
    seed = _bits(seed_bits, expected=len(x) + tag_bits - 1)
    indices = np.arange(len(x))[None, :] - np.arange(tag_bits)[:, None] + tag_bits - 1
    tag = (seed[indices] @ x) % 2
    return pack_bits_msb(tag)


def verification_result(alice_bits: Iterable[int], bob_bits: Iterable[int], locked_seed: Mapping[str, Any], *, invoked: bool) -> dict[str, Any]:
    alice, bob = _bits(alice_bits), _bits(bob_bits)
    if len(alice) != len(bob):
        raise ValueError("verification vectors must have equal length")
    if not invoked:
        return {"verification_invoked": False, "verification_tag_bits": 0, "public_control_bits": 0, "epsilon_ec": 0.0, "verified": False}
    seed = locked_seed_bits(locked_seed, len(alice) + 63)
    return {"verification_invoked": True, "verification_tag_bits": 64, "public_control_bits": len(seed), "epsilon_ec": 2.0 ** -64, "verified": toeplitz_tag(alice, seed) == toeplitz_tag(bob, seed)}


def verification_union_bound(invoked_count: int) -> float:
    return min(1.0, max(0, int(invoked_count)) * 2.0 ** -64)


def validate_pair_table(table: pd.DataFrame, source_bytes: bytes | None = None) -> pd.DataFrame:
    required = {"dataset_id", "frame_id", "pair_idx", "alice_symbol", "bob_symbol"}
    missing = required.difference(table.columns)
    if missing:
        raise ValueError(f"formal lock source lacks: {sorted(missing)}")
    df = table.copy()
    if df[["dataset_id", "frame_id", "pair_idx"]].isnull().any().any() or df.duplicated(["dataset_id", "frame_id", "pair_idx"]).any():
        raise ValueError("atomic dataset_id:frame_id:pair_idx keys must be unique and present")
    for _, frame in df.groupby(["dataset_id", "frame_id"], sort=False):
        if len(frame) != 64 or frame["pair_idx"].tolist() != list(range(64)):
            raise ValueError("each formal frame must preserve ordered pair_idx 0..63 exactly")
    df["frame_key"] = df["dataset_id"].astype(str) + ":" + df["frame_id"].astype(str)
    df["atomic_pair_key"] = df["frame_key"] + ":" + df["pair_idx"].astype(str)
    df.attrs["source_sha256"] = sha256_bytes(source_bytes) if source_bytes is not None else None
    return df


def frame_provenance(locked_pairs: pd.DataFrame) -> list[dict[str, Any]]:
    checked = validate_pair_table(locked_pairs)
    return [{"frame_key": key, "pair_idx_sequence_sha256": sha256_bytes(",".join(map(str, frame["pair_idx"].tolist())).encode("ascii")), "atomic_pair_keys": frame["atomic_pair_key"].tolist()} for key, frame in checked.groupby("frame_key", sort=False)]


def canonical_event(event: Mapping[str, Any]) -> bytes:
    required = {"event_id", "frame_key", "method", "event_type", "direction", "parent_event_id", "pass_id", "key_dependent_bits", "public_control_bits", "payload"}
    missing = required.difference(event)
    if missing:
        raise ValueError(f"event missing fields: {sorted(missing)}")
    if event["direction"] not in {"alice_to_bob", "bob_local", "control"}:
        raise ValueError("invalid event direction")
    if "block_id" not in event and "plane_id" not in event:
        raise ValueError("event needs block_id or plane_id")
    payload = event["payload"]
    if not isinstance(payload, Mapping) or not set(payload).issubset(_PAYLOAD_KEYS):
        raise ValueError("event payload contains a non-public or secret field")
    if any(token in " ".join(map(str, payload)).lower() for token in ("raw_bit", "corrected_bit", "corrected_index", "key_bits")):
        raise ValueError("event payload leaks secret bits or corrected raw index")
    return (json.dumps(dict(event), sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def transcript_bytes(events: Iterable[Mapping[str, Any]]) -> bytes:
    return b"".join(canonical_event(event) for event in events)


def transcript_summary(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    materialized = list(events)
    payload = transcript_bytes(materialized)
    return {"transcript_sha256": sha256_bytes(payload), "key_dependent_disclosure_bits_total": sum(int(e["key_dependent_bits"]) for e in materialized), "public_control_bits_total": sum(int(e["public_control_bits"]) for e in materialized)}
