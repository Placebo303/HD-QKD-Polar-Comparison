"""NBLDPC7 R1B: mother-provenance-bound canonical codebook for
``nbldpc_formal_v7_r1b_mr1`` (one multiplicative repetition, rate 1/6).

R1B reuses the EXACT frozen R1A mother construction under a new identity:

| q     | n    | m    | variable degree | check degrees      | rate (mother) |
|-------|------|------|-----------------|--------------------|---------------|
| 1024  | 256  | 170  | exactly 2       | 168 x degree-3 + 2 x degree-4 | ~1/3 |

The mother matrix, its construction seed (``2026080400``), its edge rules and
its coefficient derivation are imported byte-for-byte from the frozen
``nonbinary_v7_r1a_codebook`` module.  The R1B canonical bytes and manifest
record the mother provenance hash (SHA256 of the R1A canonical bytes, frozen
value ``75f625bb...570608``) so the R1B identity is bound to the accepted
mother.

Repetition contract (frozen):

- exactly one multiplicative repetition per variable; effective rate 1/6;
- each variable gets an independently derived deterministic nonzero GF(1024)
  multiplier: ``1 + SHA256('NBLDPC7R1B|mult|{multiplier_seed}|{col}') % 1023``
  (the same SHA256-derivation discipline as the mother coefficients);
- the second observation of variable ``v`` is ``z_v = mult_v * x_v xor e_v``
  (an independent q-ary-symmetric error ``e_v``); the decoder never sees the
  raw repetition values as secret data, it only combines public evidence into
  the variable prior (see ``nonbinary_v7_r1b_long``);
- R1B is the final repetition depth: a second repetition would exceed the
  frozen 8.75-bit/symbol key-dependent disclosure ceiling (the same mother
  syndrome of 1700 bits stays, but the effective information per transmitted
  symbol falls below the frozen bound).

Canonical bytes are ``NBLDPC7R1B`` magic + compact header (schema,
construction version, q/n/m, field identity, mother provenance, edge rules,
coefficient and multiplier derivations, seeds) + row-major 16-bit big-endian
mother coefficients + the 16-bit big-endian multiplier list.  The manifest
records SHA256, GF rank, edge/degree metrics, mother provenance, the full
deterministic multiplier list and a multiplier-spec identity.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from functools import lru_cache
from typing import Any, Mapping

from .nonbinary_codebook import gf_rank
from .nonbinary_field import GF2mField
from . import nonbinary_v7_r1a_codebook as v7_cb

METHOD = "nbldpc_formal_v7_r1b_mr1"
_SCHEMA = "NBLDPC7R1B"
_MAGIC = b"NBLDPC7R1B\n"
_CONSTRUCTION_VERSION = 1
_Q, _N, _M = 1024, 256, 170
# EXACT R1A mother seed (frozen in the R1A engineering acceptance).
_FROZEN_SEED = v7_cb._FROZEN_SEED
# Frozen one-time acceptance choice for the repetition multiplier derivation.
_MULTIPLIER_SEED = 2026080401
_CHECK_DEGREE_HISTOGRAM = {3: 168, 4: 2}
# Mother-provenance freeze (R1A engineering acceptance, codebook_identity):
# SHA256 of the R1A canonical bytes and its byte length.  Recomputed and
# asserted at every build; drift fails closed.
_MOTHER_PROVENANCE_SHA256 = "75f625bbbe1ebd74b0cf8b0b3646fa1af9ce6e5a66562e07a75507d175570608"
_MOTHER_PROVENANCE_BYTE_LENGTH = 87793
_COEFFICIENT_DERIVATION = v7_cb._COEFFICIENT_DERIVATION
_FIRST_EDGE_RULE = v7_cb._FIRST_EDGE_RULE
_SECOND_EDGE_RULE = v7_cb._SECOND_EDGE_RULE
_MULTIPLIER_DERIVATION = ("1 + int.from_bytes(SHA256(ASCII('NBLDPC7R1B|mult|{seed}|{col}')), 'big') % 1023")
_REPETITION_DEPTH = 1
_EFFECTIVE_RATE = 1 / 6


def _compact(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def _multiplier(seed: int, col: int) -> int:
    text = f"NBLDPC7R1B|mult|{seed}|{col}".encode("ascii")
    return 1 + int.from_bytes(hashlib.sha256(text).digest(), "big") % 1023


@lru_cache(maxsize=1)
def _multipliers_cached() -> tuple[int, ...]:
    if isinstance(_MULTIPLIER_SEED, bool) or not isinstance(_MULTIPLIER_SEED, int):
        raise ValueError("multiplier_seed must be an integer")
    return tuple(_multiplier(_MULTIPLIER_SEED, col) for col in range(_N))


def multipliers() -> tuple[int, ...]:
    """The deterministic public per-variable GF(1024) repetition multipliers."""
    return _multipliers_cached()


def multiplier_spec_id() -> str:
    """SHA256 identity of the frozen multiplier spec (seed + derivation + list)."""
    spec = {"multiplier_seed": _MULTIPLIER_SEED, "derivation": _MULTIPLIER_DERIVATION,
            "count": _N, "multipliers": list(_multipliers_cached())}
    return _sha(_compact(spec))


def _check_degree_histogram(degrees: list[int]) -> dict[str, int]:
    histogram: dict[str, int] = {}
    for degree in degrees:
        histogram[str(degree)] = histogram.get(str(degree), 0) + 1
    return histogram


def _mother_provenance(matrix: tuple[tuple[int, ...], ...], field: GF2mField) -> tuple[str, int]:
    """Recompute the R1A canonical bytes of the supplied mother matrix and
    return (sha256, byte_length); fails closed if they drift from the frozen
    R1A identity."""
    canonical = v7_cb._canonical_bytes(matrix, field, seed=_FROZEN_SEED)
    sha256 = _sha(canonical)
    if sha256 != _MOTHER_PROVENANCE_SHA256 or len(canonical) != _MOTHER_PROVENANCE_BYTE_LENGTH:
        raise ValueError("NBLDPC7R1B mother provenance drift")
    return sha256, len(canonical)


def _canonical_bytes(matrix: tuple[tuple[int, ...], ...], multiplier_values: tuple[int, ...],
                     field: GF2mField, *, seed: int, multiplier_seed: int) -> bytes:
    header = {
        "canonical_schema": _SCHEMA, "construction_version": _CONSTRUCTION_VERSION,
        "method": METHOD, "q": _Q, "n": _N, "m": _M,
        "construction_seed": seed, "multiplier_seed": multiplier_seed,
        "mother_provenance_sha256": _MOTHER_PROVENANCE_SHA256,
        "mother_provenance_byte_length": _MOTHER_PROVENANCE_BYTE_LENGTH,
        "first_edge_rule": _FIRST_EDGE_RULE, "second_edge_rule": _SECOND_EDGE_RULE,
        "coefficient_derivation": _COEFFICIENT_DERIVATION,
        "multiplier_derivation": _MULTIPLIER_DERIVATION, "field": asdict(field.spec),
    }
    out = bytearray(_MAGIC + _compact(header) + b"\n")
    for row in matrix:
        for value in row:
            out.extend(int(value).to_bytes(2, "big"))
    for value in multiplier_values:
        out.extend(int(value).to_bytes(2, "big"))
    return bytes(out)


@lru_cache(maxsize=1)
def _codebook_cached() -> tuple[dict[str, Any], tuple[tuple[int, ...], ...]]:
    return build_nbldpc_v7_r1b_codebook()


def build_nbldpc_v7_r1b_codebook() -> tuple[dict[str, Any], tuple[tuple[int, ...], ...]]:
    """Reconstruct the frozen R1B codebook (mother + multipliers) and its
    canonical manifest.  The mother is the exact R1A construction: the raw
    (rows, check_degrees, parallel_edges, four_cycles) tuple is imported from
    the frozen R1A module, so reconstruction is byte-for-byte by construction.
    """
    field = GF2mField.create(_Q)
    matrix, check_degrees, parallel, four_cycles = v7_cb._matrix_cached(_FROZEN_SEED)
    matrix = tuple(tuple(int(value) for value in row) for row in matrix)
    rank = gf_rank(matrix, field)
    if rank != _M:
        raise ValueError("NBLDPC7R1B frozen mother lost full rank")
    column_degrees = [sum(row[col] != 0 for row in matrix) for col in range(_N)]
    if any(degree != 2 for degree in column_degrees):
        raise ValueError("NBLDPC7R1B variable degree contract violated")
    if parallel != 0:
        raise ValueError("NBLDPC7R1B parallel-edge contract violated")
    histogram = _check_degree_histogram(check_degrees)
    if dict(histogram) != {str(k): v for k, v in _CHECK_DEGREE_HISTOGRAM.items()}:
        raise ValueError("NBLDPC7R1B check-degree histogram contract violated")
    mother_sha, mother_len = _mother_provenance(matrix, field)
    multiplier_values = _multipliers_cached()
    if len(multiplier_values) != _N or any(not 1 <= int(v) < _Q for v in multiplier_values):
        raise ValueError("NBLDPC7R1B multiplier contract violated")
    canonical = _canonical_bytes(matrix, multiplier_values, field, seed=_FROZEN_SEED,
                                 multiplier_seed=_MULTIPLIER_SEED)
    payload = {
        "method": METHOD, "canonical_schema": _SCHEMA, "canonical_magic": "NBLDPC7R1B\\n",
        "construction_version": _CONSTRUCTION_VERSION, "q": _Q, "n": _N, "m": _M,
        "field": asdict(field.spec), "field_id": field.spec.field_id,
        "construction_seed": _FROZEN_SEED, "multiplier_seed": _MULTIPLIER_SEED,
        "coefficient_derivation": _COEFFICIENT_DERIVATION,
        "first_edge_rule": _FIRST_EDGE_RULE, "second_edge_rule": _SECOND_EDGE_RULE,
        "multiplier_derivation": _MULTIPLIER_DERIVATION,
        "edge_count": 2 * _N, "rank": rank, "cycle_count": four_cycles,
        "parallel_edges": parallel, "variable_degree_min": min(column_degrees),
        "variable_degree_max": max(column_degrees),
        "check_degree_histogram": histogram,
        "mother_provenance_sha256": mother_sha,
        "mother_provenance_byte_length": mother_len,
        "mother_codebook_manifest_id": v7_cb.build_nbldpc_v7_r1a_codebook()[0]["manifest_id"],
        "repetition_depth": _REPETITION_DEPTH, "effective_rate": _EFFECTIVE_RATE,
        "multiplier_spec_id": multiplier_spec_id(),
        "multiplier_count": len(multiplier_values),
        "multiplier_min": min(multiplier_values), "multiplier_max": max(multiplier_values),
        "multipliers": list(multiplier_values),
        "canonical_sha256": _sha(canonical), "canonical_byte_length": len(canonical),
    }
    return dict(payload, manifest_id=_sha(_compact(payload))), matrix


def codebook() -> tuple[dict[str, Any], tuple[tuple[int, ...], ...]]:
    """Fresh manifest container over a cached deterministic reconstruction."""
    manifest, matrix = _codebook_cached()
    return dict(manifest), matrix


def verify_nbldpc_v7_r1b_codebook(manifest: Mapping[str, Any], matrix: Any) -> dict[str, Any]:
    """Fail closed after independently reconstructing every NBLDPC7R1B contract
    value, including the mother-provenance binding."""
    try:
        if not isinstance(manifest, Mapping):
            raise ValueError("invalid codebook container")
        expected, expected_matrix = build_nbldpc_v7_r1b_codebook()
        supplied = tuple(tuple(int(x) for x in row) for row in matrix)
        if dict(manifest) != expected or supplied != expected_matrix:
            raise ValueError("deterministic reconstruction mismatch")
        # Independent mother-provenance binding on the supplied matrix.
        _mother_provenance(supplied, GF2mField.create(_Q))
        return {"status": "ok", "method": METHOD,
                "manifest_id": expected["manifest_id"], "check_count": _M}
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return {"status": "codebook_invalid", "method": METHOD}
