"""Frozen sacrificed adjacent-bin channel model for formal binary LDPC v4.

This module deliberately consumes only the calibration records in a verified
v3 Phase-6 source lock.  It does not select, inspect, or decode confirmation
frames.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

import numpy as np

from ..utils.bitops import gray_encode, symbols_to_bits
from . import ldpc_v3_ttbin_data as _v3_data

DIMENSION = 1024
FRAME_LEN = 256
CALIBRATION_FRAMES = 64
TOTAL_SYMBOLS = FRAME_LEN * CALIBRATION_FRAMES
COUNTS = {"zero_count": 12403, "plus_one_count": 3865, "minus_one_count": 116}
SCHEMA = "binary_ldpc_v4_adjacent_channel_v1"
ROLE = "sacrificed_calibration_only"
MAPPING = "gray_msb_first"
STRESS_SCALE = 1.25


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _valid_hex(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _calibration_rows(lock: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = lock.get("selected_frames") if isinstance(lock, Mapping) else None
    if not isinstance(rows, list):
        raise ValueError("locked-data selected frames")
    selected = [row for row in rows if isinstance(row, Mapping) and row.get("role") == "calibration"]
    if len(selected) != CALIBRATION_FRAMES:
        raise ValueError("exactly 64 calibration frames required")
    if any(row.get("dataset_id") != "d1024_bw100" or row.get("bin_width_ps") != 100 for row in selected):
        raise ValueError("calibration source")
    keys = [(row.get("dataset_id"), row.get("frame_id")) for row in selected]
    if len(set(keys)) != CALIBRATION_FRAMES:
        raise ValueError("duplicate calibration frame")
    return sorted(selected, key=lambda row: str(row.get("selection_rank", "")))


def _calibration_arrays(lock: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray, list[Mapping[str, Any]]]:
    _v3_data.verify_locked_data(lock)
    rows = _calibration_rows(lock)
    arrays: list[tuple[np.ndarray, np.ndarray]] = []
    for row in rows:
        a, b = _v3_data.frame_arrays(lock, "calibration", "d1024_bw100", int(row["frame_id"]))
        if a.shape != (FRAME_LEN,) or b.shape != (FRAME_LEN,):
            raise ValueError("calibration frame shape")
        arrays.append((a, b))
    alice = np.concatenate([item[0] for item in arrays])
    bob = np.concatenate([item[1] for item in arrays])
    if alice.shape != (TOTAL_SYMBOLS,) or bob.shape != (TOTAL_SYMBOLS,):
        raise ValueError("calibration symbol count")
    if (not np.issubdtype(alice.dtype, np.integer) or not np.issubdtype(bob.dtype, np.integer)
            or np.any(alice < 0) or np.any(alice >= DIMENSION)
            or np.any(bob < 0) or np.any(bob >= DIMENSION)):
        raise ValueError("calibration symbol domain")
    return alice.astype(np.int64, copy=False), bob.astype(np.int64, copy=False), rows


def _model_counts(alice: np.ndarray, bob: np.ndarray) -> dict[str, int]:
    delta = ((alice - bob + DIMENSION // 2) % DIMENSION) - DIMENSION // 2
    if np.any(~np.isin(delta, (-1, 0, 1))):
        raise ValueError("adjacent-bin delta support")
    nonzero = delta != 0
    if np.any(nonzero):
        a_bits = symbols_to_bits(alice[nonzero], DIMENSION, "gray")
        b_bits = symbols_to_bits(bob[nonzero], DIMENSION, "gray")
        if np.any(np.count_nonzero(a_bits != b_bits, axis=1) != 1):
            raise ValueError("adjacent-bin Gray hamming property")
    return {"zero_count": int(np.count_nonzero(delta == 0)), "plus_one_count": int(np.count_nonzero(delta == 1)),
            "minus_one_count": int(np.count_nonzero(delta == -1))}


def _probabilities(counts: Mapping[str, int]) -> dict[str, dict[str, float]]:
    p_plus = counts["plus_one_count"] / TOTAL_SYMBOLS
    p_minus = counts["minus_one_count"] / TOTAL_SYMBOLS
    nominal = {"plus_one": p_plus, "minus_one": p_minus, "zero": counts["zero_count"] / TOTAL_SYMBOLS}
    stress = {"plus_one": p_plus * STRESS_SCALE, "minus_one": p_minus * STRESS_SCALE,
              "zero": 1.0 - (p_plus + p_minus) * STRESS_SCALE}
    if min(stress.values()) < 0.0 or not np.isclose(sum(stress.values()), 1.0, rtol=0.0, atol=1e-15):
        raise ValueError("stress probability contract")
    return {"adjacent_nominal": nominal, "adjacent_stress_125": stress}


def _validate_static_model(model: Mapping[str, Any]) -> None:
    required = {"schema", "role", "dimension", "mapping", "frame_len_symbols", "calibration_frame_count", "total_count",
                "zero_count", "plus_one_count", "minus_one_count", "sign_convention", "stress_scale", "probabilities",
                "source_lock_sha256", "source_manifest_sha256", "selected_frames_sha256", "calibration_bytes_sha256",
                "calibration_sha256", "source_main_ttbin_sha256", "source_chunk_ttbin_sha256", "model_sha256"}
    if set(model) != required:
        raise ValueError("channel model schema")
    if (model["schema"], model["role"], model["dimension"], model["mapping"], model["frame_len_symbols"],
            model["calibration_frame_count"], model["total_count"], model["sign_convention"], model["stress_scale"]) != (
                SCHEMA, ROLE, DIMENSION, MAPPING, FRAME_LEN, CALIBRATION_FRAMES, TOTAL_SYMBOLS,
                "signed_modular_alice_minus_bob", STRESS_SCALE):
        raise ValueError("channel model identity")
    counts = {key: model[key] for key in COUNTS}
    if counts != COUNTS or model["probabilities"] != _probabilities(COUNTS):
        raise ValueError("channel model probabilities")
    if any(not _valid_hex(model[key]) for key in required if key.endswith("sha256")):
        raise ValueError("channel model provenance")


def build_adjacent_channel_model(locked_data: Mapping[str, Any]) -> dict[str, Any]:
    """Reconstruct the immutable v4 model from the exact sacrificed 64 frames."""
    alice, bob, rows = _calibration_arrays(locked_data)
    counts = _model_counts(alice, bob)
    if counts != COUNTS:
        raise ValueError("frozen adjacent-bin calibration counts")
    selected = [{key: row[key] for key in ("dataset_id", "frame_id", "frame_identity", "selection_rank",
                                             "source_pair_start", "source_pair_end")} for row in rows]
    source_manifest = locked_data["source_manifest"]
    model: dict[str, Any] = {
        "schema": SCHEMA,
        "role": ROLE,
        "dimension": DIMENSION,
        "mapping": MAPPING,
        "frame_len_symbols": FRAME_LEN,
        "calibration_frame_count": CALIBRATION_FRAMES,
        "total_count": TOTAL_SYMBOLS,
        **counts,
        "sign_convention": "signed_modular_alice_minus_bob",
        "stress_scale": STRESS_SCALE,
        "probabilities": _probabilities(counts),
        "source_lock_sha256": locked_data["lock_sha256"],
        "source_manifest_sha256": locked_data["source_manifest_sha256"],
        "selected_frames_sha256": _sha(_compact(selected)),
        "calibration_bytes_sha256": _sha(alice.astype("<i8", copy=False).tobytes() + bob.astype("<i8", copy=False).tobytes()),
        "calibration_sha256": locked_data["calibration"]["calibration_sha256"],
        "source_main_ttbin_sha256": source_manifest["main_ttbin"]["sha256"],
        "source_chunk_ttbin_sha256": source_manifest["chunk_ttbin"]["sha256"],
    }
    model["model_sha256"] = _sha(_compact(model))
    return model


def verify_adjacent_channel_model(model: Mapping[str, Any], locked_data: Mapping[str, Any]) -> None:
    """Fail closed unless *model* is the exact reconstruction from the lock."""
    if not isinstance(model, Mapping):
        raise ValueError("channel model")
    _validate_static_model(model)
    candidate = dict(model)
    digest = candidate.pop("model_sha256", None)
    if not _valid_hex(digest) or _sha(_compact(candidate)) != digest:
        raise ValueError("channel model hash")
    rebuilt = build_adjacent_channel_model(locked_data)
    if dict(model) != rebuilt:
        raise ValueError("channel model reconstruction")


def plane_error_channel(bob_symbols: Any, plane_id: int, stratum: str, model: Mapping[str, Any], *, clip_for_backend: bool = True) -> np.ndarray:
    """Return Bob-conditioned error probabilities for one MSB-first Gray plane.

    The scientific model is unclipped.  Backend callers receive the mandated
    ``[1e-6, .49]`` clipping unless ``clip_for_backend=False`` is requested.
    """
    if not isinstance(plane_id, int) or isinstance(plane_id, bool) or not 0 <= plane_id < 10:
        raise ValueError("plane id")
    if not isinstance(model, Mapping):
        raise ValueError("channel model")
    _validate_static_model(model)
    base = dict(model); digest = base.pop("model_sha256")
    if _sha(_compact(base)) != digest:
        raise ValueError("channel model hash")
    probabilities = model.get("probabilities", {})
    if stratum not in {"adjacent_nominal", "adjacent_stress_125"} or not isinstance(probabilities, Mapping):
        raise ValueError("channel stratum")
    distribution = probabilities.get(stratum)
    if not isinstance(distribution, Mapping):
        raise ValueError("channel probabilities")
    p_plus, p_minus = distribution.get("plus_one"), distribution.get("minus_one")
    if any(not isinstance(value, (int, float)) or isinstance(value, bool) or not np.isfinite(value) or value < 0 for value in (p_plus, p_minus)):
        raise ValueError("channel probabilities")
    bob = np.asarray(bob_symbols)
    if bob.shape != (FRAME_LEN,) or not np.issubdtype(bob.dtype, np.integer) or np.any(bob < 0) or np.any(bob >= DIMENSION):
        raise ValueError("Bob symbols")
    gray_b = gray_encode(bob.astype(np.int64, copy=False))
    gray_plus = gray_encode((bob.astype(np.int64, copy=False) + 1) % DIMENSION)
    gray_minus = gray_encode((bob.astype(np.int64, copy=False) - 1) % DIMENSION)
    mask = np.int64(1 << (9 - plane_id))
    result = float(p_plus) * ((gray_plus & mask) != (gray_b & mask)) + float(p_minus) * ((gray_minus & mask) != (gray_b & mask))
    return np.clip(result.astype(np.float64, copy=False), 1e-6, .49) if clip_for_backend else result.astype(np.float64, copy=False)
