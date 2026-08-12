"""Deterministic candidate-only HGF2V3 long-frame LDPC codebooks.

This offline component constructs diagnostics only.  It neither reads frame
data nor writes qualification or production artifacts.
"""
from __future__ import annotations

import copy
import hashlib
import json
from itertools import combinations
from functools import lru_cache
from typing import Any, Mapping

import numpy as np

CONSTRUCTION_ID = "binary_ldpc_protograph_accumulator_candidate_v3"
CONSTRUCTION_VERSION = "1"
STATUS = "candidate_only_not_qualified"
BLOCK_LENGTHS = (256, 512, 1024)
PLANE_IDS = tuple(range(10))
CANDIDATE_IDS = tuple(range(4))
PREFIX_FRACTIONS = (("p050", 1, 2), ("p0625", 5, 8), ("p075", 3, 4), ("p0875", 7, 8))
MAGIC = b"HGF2V3"
ACE_PROXY_DEFINITION = "column_pair_extrinsic_degree_v1"


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _gf2_rank(matrix: np.ndarray) -> int:
    """Exact GF(2) rank using packed integer row elimination."""
    basis: dict[int, int] = {}
    for row in np.packbits(matrix, axis=1, bitorder="big"):
        value = int.from_bytes(row.tobytes(), "big")
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return len(basis)


def _validate_identity(n: int, plane_id: int, candidate_id: int) -> None:
    if n not in BLOCK_LENGTHS or plane_id not in PLANE_IDS or candidate_id not in CANDIDATE_IDS:
        raise ValueError("unsupported long-frame codebook domain")


def _seed(n: int, plane_id: int, candidate_id: int) -> int:
    _validate_identity(n, plane_id, candidate_id)
    domain = {"construction_id": CONSTRUCTION_ID, "construction_version": CONSTRUCTION_VERSION,
              "n": n, "plane_id": plane_id, "candidate_id": candidate_id}
    return int.from_bytes(hashlib.sha256(_compact(domain)).digest()[:16], "big")


def prefix_rows(n: int) -> dict[str, int]:
    if n not in BLOCK_LENGTHS:
        raise ValueError("unsupported block length")
    return {name: n * numerator // denominator for name, numerator, denominator in PREFIX_FRACTIONS}


def generate_master(n: int, plane_id: int, candidate_id: int) -> np.ndarray:
    """Return the exact deterministic (7n/8) x n master construction."""
    _validate_identity(n, plane_id, candidate_id)
    m0, t, mmax = n // 2, n // 8, 7 * n // 8
    h = np.zeros((mmax, n), dtype=np.uint8)
    h[np.arange(mmax), np.arange(mmax)] = 1
    rng = np.random.Generator(np.random.PCG64(_seed(n, plane_id, candidate_id)))
    p = rng.permutation(m0)
    for j in range(m0):
        h[p[j], m0 + j] = 1
        h[p[(j + 1) % m0], m0 + j] = 1
    shifts = [int(rng.integers(0, t)) for _ in range(3)]
    for layer, shift in enumerate(shifts):
        for j in range(t):
            h[m0 + layer * t + j, mmax + ((j + shift) % t)] = 1
    _validate_prefixes(h, known_full_rank=True)
    return h


def canonical_matrix_bytes(matrix: np.ndarray) -> bytes:
    h = np.asarray(matrix, dtype=np.uint8)
    if h.ndim != 2 or h.shape[1] not in BLOCK_LENGTHS or h.shape[0] not in prefix_rows(int(h.shape[1])).values() or np.any((h != 0) & (h != 1)):
        raise ValueError("invalid HGF2V3 matrix")
    return MAGIC + np.asarray(h.shape, dtype="<u4").tobytes() + h.tobytes(order="C")


def parse_matrix_bytes(raw: bytes) -> np.ndarray:
    if len(raw) < len(MAGIC) + 8 or raw[:len(MAGIC)] != MAGIC:
        raise ValueError("invalid HGF2V3 header")
    m, n = np.frombuffer(raw[len(MAGIC):len(MAGIC) + 8], dtype="<u4")
    if int(n) not in BLOCK_LENGTHS or int(m) not in prefix_rows(int(n)).values() or len(raw) != len(MAGIC) + 8 + int(m) * int(n):
        raise ValueError("invalid HGF2V3 dimensions")
    h = np.frombuffer(raw[len(MAGIC) + 8:], dtype=np.uint8).reshape(int(m), int(n)).copy()
    if np.any((h != 0) & (h != 1)):
        raise ValueError("invalid HGF2V3 values")
    _validate_prefix(h)
    return h


def _structural_diagnostics(matrix: np.ndarray, *, known_full_rank: bool = False) -> dict[str, Any]:
    """Return structural proxies only; this reports no decoding evidence."""
    h = np.asarray(matrix, dtype=np.uint8)
    if h.ndim != 2 or h.shape[1] not in BLOCK_LENGTHS or np.any((h != 0) & (h != 1)):
        raise ValueError("invalid prefix matrix")
    row_weights = h.sum(axis=1, dtype=np.int64)
    column_weights = h.sum(axis=0, dtype=np.int64)
    overlaps: dict[tuple[int, int], int] = {}
    for row in h:
        support = np.flatnonzero(row)
        for left, right in combinations(support.tolist(), 2):
            pair = (left, right) if left < right else (right, left)
            overlaps[pair] = overlaps.get(pair, 0) + 1
    cycle_pairs = [(pair, count) for pair, count in overlaps.items() if count >= 2]
    if cycle_pairs:
        values = [max(int(column_weights[left]) - 2, 0) + max(int(column_weights[right]) - 2, 0)
                  for (left, right), _ in cycle_pairs]
        multiplicities = [count * (count - 1) // 2 for _, count in cycle_pairs]
        ace_min = min(values)
        ace_sum = sum(value * multiplicity for value, multiplicity in zip(values, multiplicities))
    else:
        ace_min, ace_sum = None, 0
    columns = np.ascontiguousarray(h.T)
    return {"rank": int(h.shape[0] if known_full_rank else _gf2_rank(h)), "zero_columns": int(np.count_nonzero(column_weights == 0)),
            "duplicate_columns": int(h.shape[1] - len(np.unique(columns, axis=0))),
            "row_weight_min": int(row_weights.min()), "row_weight_max": int(row_weights.max()),
            "column_weight_min": int(column_weights.min()), "column_weight_max": int(column_weights.max()),
            "four_cycles": int(sum(count * (count - 1) // 2 for _, count in cycle_pairs)), "ace_4cycle_proxy_min": ace_min,
            "ace_4cycle_proxy_sum": ace_sum, "ace_4cycle_proxy_definition": ACE_PROXY_DEFINITION,
            "diagnostics_scope": "structural_proxies_only_not_decoding_or_qualification_evidence"}


def structural_diagnostics(matrix: np.ndarray) -> dict[str, Any]:
    """Return structural proxies only; this reports no decoding evidence."""
    return _structural_diagnostics(matrix)


def _validate_prefix(h: np.ndarray, *, known_full_rank: bool = False) -> None:
    metrics = _structural_diagnostics(h, known_full_rank=known_full_rank)
    m = h.shape[0]
    if (metrics["rank"] != m or metrics["zero_columns"] != 0 or metrics["duplicate_columns"] != 0
            or not (2 <= metrics["row_weight_min"] <= metrics["row_weight_max"] <= 3)
            or not (1 <= metrics["column_weight_min"] <= metrics["column_weight_max"] <= 5)):
        raise ValueError(f"long-frame prefix violates frozen structural bounds: {metrics}")


def _validate_prefixes(master: np.ndarray, *, known_full_rank: bool = False) -> None:
    for rows in prefix_rows(int(master.shape[1])).values():
        _validate_prefix(master[:rows], known_full_rank=known_full_rank)


def candidate_entry(n: int, plane_id: int, candidate_id: int) -> dict[str, Any]:
    master = generate_master(n, plane_id, candidate_id)
    prefixes: dict[str, Any] = {}
    for prefix_id, rows in prefix_rows(n).items():
        h = master[:rows]
        raw = canonical_matrix_bytes(h)
        prefixes[prefix_id] = {"m_checks": rows, "n": n, "shape": [rows, n],
                                "canonical_bytes_sha256": hashlib.sha256(raw).hexdigest(),
                                "structural_diagnostics": _structural_diagnostics(h, known_full_rank=True)}
    return {"n": n, "plane_id": plane_id, "candidate_id": candidate_id,
            "construction_seed_hex": f"{_seed(n, plane_id, candidate_id):032x}", "prefixes": prefixes}


@lru_cache(maxsize=1)
def _manifest_cached() -> dict[str, Any]:
    candidates = [candidate_entry(n, plane, candidate) for n in BLOCK_LENGTHS for plane in PLANE_IDS for candidate in CANDIDATE_IDS]
    base = {"construction_id": CONSTRUCTION_ID, "construction_version": CONSTRUCTION_VERSION,
            "status": STATUS, "domain": {"block_lengths": list(BLOCK_LENGTHS), "plane_ids": list(PLANE_IDS),
            "candidate_ids": list(CANDIDATE_IDS), "prefix_fractions": [{"id": name, "numerator": num, "denominator": den} for name, num, den in PREFIX_FRACTIONS]},
            "candidates": candidates}
    return {**base, "manifest_sha256": hashlib.sha256(_compact(base)).hexdigest()}


def candidate_manifest() -> dict[str, Any]:
    """Return the complete in-memory, deterministic candidate-only manifest."""
    return copy.deepcopy(_manifest_cached())


def verify_candidate_manifest(manifest: Mapping[str, Any]) -> None:
    supplied = dict(manifest)
    digest = supplied.pop("manifest_sha256", None)
    if not isinstance(digest, str) or digest != hashlib.sha256(_compact(supplied)).hexdigest():
        raise ValueError("candidate manifest hash mismatch")
    if supplied != {key: value for key, value in _manifest_cached().items() if key != "manifest_sha256"}:
        raise ValueError("candidate manifest does not match deterministic construction")
