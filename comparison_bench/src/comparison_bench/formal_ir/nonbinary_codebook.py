"""Pure N1 deterministic nonbinary LDPC structural codebook contract."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from numbers import Integral
from typing import Any, Mapping

from .nonbinary_field import GF2mField, get_field_spec


_MAGIC = b"NBLDPC1\n"
_CHECK_COUNTS = (16, 24, 32)
_N = 64
_MOTHER_ROWS = 32
_INFO_COLUMNS = 32
_DEFAULT_SEED = 2026072601
_TOPOLOGY = "three_shift_cyclic_information_half_plus_identity_parity_half"
_COEFFICIENT_DERIVATION = "1+sha256_ascii_NBLDPC1_coef_q_seed_row_edge_mod_q_minus_1"


def _compact(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _seed(seed: int) -> int:
    if isinstance(seed, bool) or not isinstance(seed, Integral) or not 0 <= int(seed) < 2**64:
        raise ValueError("construction_seed must be a non-boolean integer in [0, 2^64)")
    return int(seed)


def _shifts(seed: int) -> tuple[int, int, int]:
    chosen: list[int] = []
    for slot in range(3):
        attempt = 0
        while True:
            domain = f"NBLDPC1|shift|{seed}|{slot}|{attempt}".encode("ascii")
            shift = int.from_bytes(hashlib.sha256(domain).digest(), "big") % _INFO_COLUMNS
            if shift not in chosen:
                chosen.append(shift)
                break
            attempt += 1
    return tuple(chosen)  # type: ignore[return-value]


def _coefficient(q: int, seed: int, row: int, edge: int) -> int:
    domain = f"NBLDPC1|coef|{q}|{seed}|{row}|{edge}".encode("ascii")
    return 1 + int.from_bytes(hashlib.sha256(domain).digest(), "big") % (q - 1)


def gf_rank(matrix: Any, field: GF2mField) -> int:
    """Return Gaussian-elimination rank using only the pinned GF(q) backend."""
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    try:
        rows = [list(row) for row in matrix]
    except TypeError as exc:
        raise ValueError("matrix must be rectangular") from exc
    if not rows:
        return 0
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("matrix must be rectangular")
    work = [[field._symbol(value) for value in row] for row in rows]
    rank = 0
    for column in range(width):
        pivot = next((index for index in range(rank, len(work)) if work[index][column]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        inverse = field.inverse(work[rank][column])
        work[rank] = [field.mul(value, inverse) for value in work[rank]]
        for index, row in enumerate(work):
            if index != rank and row[column]:
                factor = row[column]
                work[index] = [field.sub(value, field.mul(factor, pivot_value)) for value, pivot_value in zip(row, work[rank])]
        rank += 1
        if rank == len(work):
            break
    return rank


def _matrix(q: int, seed: int, shifts: tuple[int, int, int]) -> tuple[tuple[int, ...], ...]:
    rows: list[tuple[int, ...]] = []
    for row in range(_MOTHER_ROWS):
        values = [0] * _N
        for edge, shift in enumerate(shifts):
            values[(row + shift) % _INFO_COLUMNS] = _coefficient(q, seed, row, edge)
        values[_INFO_COLUMNS + row] = 1
        rows.append(tuple(values))
    return tuple(rows)


def _header(field: GF2mField, checks: int, seed: int, shifts: tuple[int, int, int]) -> dict[str, Any]:
    return {
        "coefficient_derivation": _COEFFICIENT_DERIVATION,
        "coefficient_encoding": "unsigned_16_bit_big_endian",
        "construction_seed": seed,
        "field": asdict(field.spec),
        "field_id": field.spec.field_id,
        "matrix_ordering": "row_major",
        "method": field.spec.method,
        "mother_dimensions": [_MOTHER_ROWS, _N],
        "n": _N,
        "q": field.q,
        "rate_check_count": checks,
        "schema": "NBLDPC1",
        "topology": _TOPOLOGY,
        "ordered_circulant_shifts": list(shifts),
    }


def _canonical_bytes(matrix: tuple[tuple[int, ...], ...], field: GF2mField, checks: int, seed: int, shifts: tuple[int, int, int]) -> bytes:
    if len(matrix) != checks or any(len(row) != _N for row in matrix):
        raise ValueError("invalid NBLDPC1 matrix dimensions")
    payload = bytearray(_MAGIC + _compact(_header(field, checks, seed, shifts)) + b"\n")
    for row in matrix:
        for value in row:
            payload.extend(field._symbol(value).to_bytes(2, "big"))
    return bytes(payload)


def _manifest_payload(field: GF2mField, seed: int, shifts: tuple[int, int, int], matrices: Mapping[int, tuple[tuple[int, ...], ...]]) -> dict[str, Any]:
    entries = []
    for checks in _CHECK_COUNTS:
        matrix = matrices[checks]
        raw = _canonical_bytes(matrix, field, checks, seed, shifts)
        entries.append({
            "byte_length": len(raw), "check_count": checks, "codebook_id": _sha256(raw),
            "prefix_of_check_count": _MOTHER_ROWS, "rank": gf_rank(matrix, field),
        })
    return {
        "construction_seed": seed,
        "field": asdict(field.spec),
        "field_id": field.spec.field_id,
        "frozen_family": {"canonical_magic": "NBLDPC1\\n", "canonical_schema": "NBLDPC1", "check_counts": list(_CHECK_COUNTS), "coefficient_derivation": _COEFFICIENT_DERIVATION, "coefficient_encoding": "unsigned_16_bit_big_endian", "matrix_ordering": "row_major", "mother_dimensions": [_MOTHER_ROWS, _N], "n": _N, "ordered_circulant_shifts": list(shifts), "topology": _TOPOLOGY},
        "method": field.spec.method,
        "ordered_entries": entries,
        "prefix_relationship": "each_entry_is_the_exact_ordered_row_prefix_of_the_32x64_mother_matrix",
        "q": field.q,
        "schema": "NBLDPC1-manifest",
    }


def build_nonbinary_codebook_family(q: int, *, construction_seed: int = _DEFAULT_SEED) -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    """Build the frozen in-memory N1 family; no decoder or filesystem is used."""
    seed = _seed(construction_seed)
    field = GF2mField(get_field_spec(q))
    shifts = _shifts(seed)
    mother = _matrix(field.q, seed, shifts)
    matrices = {checks: tuple(mother[:checks]) for checks in _CHECK_COUNTS}
    payload = _manifest_payload(field, seed, shifts, matrices)
    manifest = dict(payload, manifest_id=_sha256(_compact(payload)))
    return manifest, matrices


def verify_nonbinary_codebook_family(manifest: Mapping[str, Any], matrices: Mapping[int, Any]) -> dict[str, Any]:
    """Fail closed after independently reconstructing every N1 contract value."""
    try:
        if not isinstance(manifest, Mapping) or not isinstance(matrices, Mapping):
            raise ValueError("invalid family container")
        q = manifest.get("q")
        field = GF2mField(get_field_spec(q))
    except (KeyError, TypeError, ValueError):
        return {"status": "unsupported_domain", "method": "nbldpc_formal_v1"}
    try:
        seed = _seed(manifest.get("construction_seed"))
        expected_manifest, expected_matrices = build_nonbinary_codebook_family(field.q, construction_seed=seed)
        if manifest != expected_manifest:
            raise ValueError("manifest deterministic reconstruction mismatch")
        if tuple(matrices.keys()) != _CHECK_COUNTS:
            raise ValueError("matrix check-count order mismatch")
        supplied = {checks: tuple(tuple(row) for row in matrices[checks]) for checks in _CHECK_COUNTS}
        if supplied != expected_matrices:
            raise ValueError("matrix deterministic reconstruction mismatch")
        for checks in _CHECK_COUNTS:
            if gf_rank(supplied[checks], field) != checks:
                raise ValueError("GF(q) rank mismatch")
        return {"status": "ok", "method": field.spec.method, "field_id": field.spec.field_id, "manifest_id": expected_manifest["manifest_id"], "check_counts": list(_CHECK_COUNTS)}
    except (KeyError, TypeError, ValueError, OverflowError):
        return {"status": "codebook_invalid", "method": field.spec.method}
