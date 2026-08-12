"""Deterministic anchored column-weight-three HGF2V4 LDPC candidates.

This module is deliberately an in-memory construction audit.  It neither
reads experiment data nor writes qualification artefacts.
"""
from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from itertools import combinations
from typing import Any, Mapping

import numpy as np

CONSTRUCTION_ID = "binary_ldpc_anchored_cw3_v4"
CONSTRUCTION_VERSION = "1"
STATUS = "candidate_only_not_qualified"
BLOCK_LENGTH = 256
PLANE_IDS = tuple(range(10))
CANDIDATE_IDS = tuple(range(4))
ROW_COUNTS = (16, 16, 16, 24, 24, 32, 48, 80, 136, 192)
MAGIC = b"HGF2V4"


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_identity(plane_id: int, candidate_id: int) -> None:
    if plane_id not in PLANE_IDS or candidate_id not in CANDIDATE_IDS:
        raise ValueError("unsupported v4 codebook identity")


def row_count(plane_id: int) -> int:
    if plane_id not in PLANE_IDS:
        raise ValueError("unsupported v4 plane")
    return ROW_COUNTS[plane_id]


def construction_seed(plane_id: int, candidate_id: int) -> int:
    _validate_identity(plane_id, candidate_id)
    return 6000 + 100 * candidate_id + plane_id


def gf2_rank(matrix: np.ndarray) -> int:
    """Return exact GF(2) rank using integer row elimination."""
    h = np.asarray(matrix, dtype=np.uint8)
    if h.ndim != 2 or np.any((h != 0) & (h != 1)):
        raise ValueError("invalid binary matrix")
    basis: dict[int, int] = {}
    for packed in np.packbits(h, axis=1, bitorder="big"):
        value = int.from_bytes(packed.tobytes(), "big")
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return len(basis)


def _support_key(rows: np.ndarray) -> tuple[int, int, int]:
    return tuple(int(item) for item in rows.tolist())


def _validate_matrix(matrix: np.ndarray, plane_id: int | None = None) -> None:
    h = np.asarray(matrix, dtype=np.uint8)
    if h.ndim != 2 or h.shape[1] != BLOCK_LENGTH or np.any((h != 0) & (h != 1)):
        raise ValueError("invalid HGF2V4 matrix")
    if plane_id is not None and h.shape[0] != row_count(plane_id):
        raise ValueError("invalid HGF2V4 plane row count")
    if h.shape[0] not in set(ROW_COUNTS):
        raise ValueError("unsupported HGF2V4 dimensions")
    weights = h.sum(axis=0, dtype=np.int64)
    if not np.all(weights == 3):
        raise ValueError("HGF2V4 columns must have weight three")
    supports = [tuple(np.flatnonzero(h[:, col]).tolist()) for col in range(BLOCK_LENGTH)]
    if len(set(supports)) != BLOCK_LENGTH:
        raise ValueError("HGF2V4 duplicate column support")
    if np.any(h.sum(axis=1, dtype=np.int64) == 0):
        raise ValueError("HGF2V4 zero row")
    if plane_id is not None and not np.all(h[np.arange(h.shape[0]), np.arange(h.shape[0])] == 1):
        raise ValueError("HGF2V4 anchor failure")
    if gf2_rank(h) != h.shape[0]:
        raise ValueError("HGF2V4 rank failure")


def generate_candidate(plane_id: int, candidate_id: int) -> tuple[np.ndarray, int]:
    """Reconstruct one frozen candidate and return it with its accepted trial."""
    _validate_identity(plane_id, candidate_id)
    m = row_count(plane_id)
    base = construction_seed(plane_id, candidate_id)
    for trial in range(100):
        rng = np.random.Generator(np.random.PCG64(base + trial))
        h = np.zeros((m, BLOCK_LENGTH), dtype=np.uint8)
        seen: set[tuple[int, int, int]] = set()
        completed = True
        for col in range(BLOCK_LENGTH):
            picked: np.ndarray | None = None
            for _ in range(10_000):
                if col < m:
                    excluded = np.concatenate((np.arange(col, dtype=np.int64), np.arange(col + 1, m, dtype=np.int64)))
                    candidate = np.sort(np.concatenate((np.asarray([col], dtype=np.int64), rng.choice(excluded, size=2, replace=False))))
                else:
                    candidate = np.sort(rng.choice(np.arange(m, dtype=np.int64), size=3, replace=False))
                key = _support_key(candidate)
                if key not in seen:
                    picked = candidate
                    seen.add(key)
                    break
            if picked is None:
                completed = False
                break
            h[picked, col] = 1
        if completed and gf2_rank(h) == m:
            _validate_matrix(h, plane_id)
            return h, trial
    raise ValueError("v4 candidate construction exhausted frozen trials")


def matrix_for(plane_id: int, candidate_id: int) -> np.ndarray:
    """Return a detached reconstruction of one frozen candidate matrix."""
    return generate_candidate(plane_id, candidate_id)[0]


def canonical_matrix_bytes(matrix: np.ndarray, *, plane_id: int | None = None) -> bytes:
    h = np.asarray(matrix, dtype=np.uint8)
    _validate_matrix(h, plane_id)
    return MAGIC + np.asarray(h.shape, dtype="<u4").tobytes() + h.tobytes(order="C")


def parse_matrix_bytes(raw: bytes, *, plane_id: int | None = None) -> np.ndarray:
    if not isinstance(raw, bytes) or len(raw) < len(MAGIC) + 8 or raw[:len(MAGIC)] != MAGIC:
        raise ValueError("invalid HGF2V4 header")
    m, n = np.frombuffer(raw[len(MAGIC):len(MAGIC) + 8], dtype="<u4")
    if int(n) != BLOCK_LENGTH or int(m) not in set(ROW_COUNTS) or len(raw) != len(MAGIC) + 8 + int(m) * int(n):
        raise ValueError("invalid HGF2V4 dimensions")
    h = np.frombuffer(raw[len(MAGIC) + 8:], dtype=np.uint8).reshape(int(m), int(n)).copy()
    _validate_matrix(h, plane_id)
    return h


def _four_cycles(h: np.ndarray) -> int:
    overlap = np.asarray(h, dtype=np.int64).T @ np.asarray(h, dtype=np.int64)
    upper = overlap[np.triu_indices(BLOCK_LENGTH, 1)]
    return int(np.sum(upper * (upper - 1) // 2))


def _syndrome_ints(h: np.ndarray) -> list[int]:
    return [int.from_bytes(row.tobytes(), "big") for row in np.packbits(h, axis=0, bitorder="big").T]


def _low_weight_witnesses(h: np.ndarray) -> dict[str, list[list[int]]]:
    """Find exact weight-3 and weight-4 kernel witnesses (up to one each)."""
    syndromes = _syndrome_ints(h)
    pair_map: dict[int, list[tuple[int, int]]] = {}
    weight3: list[list[int]] = []
    weight4: list[list[int]] = []
    single_map = {value: index for index, value in enumerate(syndromes)}
    for left, right in combinations(range(BLOCK_LENGTH), 2):
        value = syndromes[left] ^ syndromes[right]
        single = single_map.get(value)
        if single is not None and single != left and single != right:
            weight3 = [[left, right, single]]
            break
    for left, right in combinations(range(BLOCK_LENGTH), 2):
        value = syndromes[left] ^ syndromes[right]
        for previous in pair_map.get(value, []):
            if not ({left, right} & set(previous)):
                weight4 = [[previous[0], previous[1], left, right]]
                break
        if weight4:
            break
        pair_map.setdefault(value, []).append((left, right))
    return {"weight_3_witnesses": weight3, "weight_4_witnesses": weight4}


def structural_diagnostics(matrix: np.ndarray) -> dict[str, Any]:
    h = np.asarray(matrix, dtype=np.uint8)
    _validate_matrix(h)
    row_weights = h.sum(axis=1, dtype=np.int64)
    low = _low_weight_witnesses(h)
    return {
        "rank": gf2_rank(h), "shape": [int(h.shape[0]), int(h.shape[1])],
        "column_weight_min": int(h.sum(axis=0).min()), "column_weight_max": int(h.sum(axis=0).max()),
        "row_weight_min": int(row_weights.min()), "row_weight_max": int(row_weights.max()),
        "four_cycles": _four_cycles(h), **low,
        "low_weight_search": "exact_weight_3_and_4_kernel_witness_search",
    }


def candidate_entry(plane_id: int, candidate_id: int) -> dict[str, Any]:
    h, trial = generate_candidate(plane_id, candidate_id)
    diagnostics = structural_diagnostics(h)
    valid = not (plane_id in (8, 9) and (diagnostics["weight_3_witnesses"] or diagnostics["weight_4_witnesses"]))
    raw = canonical_matrix_bytes(h, plane_id=plane_id)
    return {
        "plane_id": plane_id, "candidate_id": candidate_id, "construction_seed": construction_seed(plane_id, candidate_id),
        "accepted_trial": trial, "shape": [row_count(plane_id), BLOCK_LENGTH], "rank": gf2_rank(h),
        "valid": valid, "canonical_bytes_sha256": _sha(raw), "structural_diagnostics": diagnostics,
    }


@lru_cache(maxsize=1)
def _manifest_cached() -> dict[str, Any]:
    candidates = [candidate_entry(plane_id, candidate_id) for plane_id in PLANE_IDS for candidate_id in CANDIDATE_IDS]
    base = {
        "construction_id": CONSTRUCTION_ID, "construction_version": CONSTRUCTION_VERSION, "status": STATUS,
        "domain": {"block_length": BLOCK_LENGTH, "plane_ids": list(PLANE_IDS), "candidate_ids": list(CANDIDATE_IDS), "row_counts": list(ROW_COUNTS)},
        "candidates": candidates,
    }
    return {**base, "manifest_sha256": _sha(_compact(base))}


def candidate_manifest() -> dict[str, Any]:
    return copy.deepcopy(_manifest_cached())


def verify_candidate_manifest(manifest: Mapping[str, Any]) -> None:
    supplied = dict(manifest)
    digest = supplied.pop("manifest_sha256", None)
    if not isinstance(digest, str) or digest != _sha(_compact(supplied)):
        raise ValueError("candidate manifest hash mismatch")
    expected = _manifest_cached()
    if supplied != {key: value for key, value in expected.items() if key != "manifest_sha256"}:
        raise ValueError("candidate manifest does not match deterministic reconstruction")
