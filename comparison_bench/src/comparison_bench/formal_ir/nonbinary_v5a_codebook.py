"""NBLDPC5A: exact v3 48-row codebook plus one deterministic 8-row block.

Route A mother code.  Rows 0..47 are the exact frozen v3 ``NBLDPC3`` rows
(reconstructed deterministically, never imported from artifacts).  Rows
48..55 form extension block ``a=6`` with ``mask6 = (0,1,2,3,4,5)`` and shifts
``s6`` fixed by the frozen disjoint-shift-difference search:

  for every v3 block ``a`` (0..5) the set ``{s6[b] - s_a[b] mod 8 : b in
  mask_a ∩ mask6}`` has all-distinct values.

That condition is exactly what keeps any pair of rows sharing at most one
column position, so every prefix 32/40/48/56 has zero four-cycles.  (The
original frozen text used ``mask_a`` in full; that version is provably
unsatisfiable, and since the new block has no edges in columns 6,7 the
intersection is the exact 4-cycle-free condition — see ``_find_s6``.)  The
coefficient salt is the first non-negative integer for which every prefix has
full GF(1024) rank, minimum column degree >= 2, and passes the pair-proxy
check.  The accepted ``(s6, salt)`` are recorded in the canonical manifest and
never re-searched after acceptance time.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import asdict
from functools import lru_cache
from typing import Any, Mapping

import numpy as np

from .nonbinary_codebook import gf_rank
from .nonbinary_field import GF2mField
from . import nonbinary_v3 as v3

METHOD = "nbldpc_formal_v5a_multistage"
_SCHEMA, _MAGIC = "NBLDPC5A", b"NBLDPC5A\n"
_Q, _N, _Z = 1024, 64, 8
_PREFIXES = (32, 40, 48, 56)
_MASK6 = (0, 1, 2, 3, 4, 5)
_EXTENSION_BLOCK = 6
_COEFFICIENT_DERIVATION = "1 + int.from_bytes(SHA256(ASCII('NBLDPC5A|coef|{salt}|{row}|{col}')), 'big') mod 1023"


def _compact(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
def _sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()

@lru_cache(maxsize=1)
def _v3_cached() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    return v3.build_nbldpc_v3_codebook()

def _coefficient(salt: int, row: int, col: int) -> int:
    text = f"NBLDPC5A|coef|{salt}|{row}|{col}".encode("ascii")
    return 1 + int.from_bytes(hashlib.sha256(text).digest(), "big") % 1023

# Frozen accepted values found by the one-time acceptance search (T0).  The
# search is never re-run; these constants are part of the canonical identity.
_FROZEN_S6: tuple[int, ...] = (0, 3, 6, 7, 6, 0, 0, 0)
_FROZEN_SALT: int = 0

def _find_s6() -> tuple[int, ...]:
    """Lexicographically first s6 with disjoint shift differences vs every
    v3 block a=0..5, restricted to the columns the new block actually uses.

    The v5 design froze the condition over ``mask_a``; implementation proved
    that version unsatisfiable (constraint propagation over (Z/8)^8, two
    independent exhaustive runs).  The design's own justification — "keeps
    every pair of rows sharing at most one column position" — requires the
    intersection ``mask_a ∩ mask6``: the new row has no edge in columns 6,7,
    so it can never share a column there with any v3 row.  With the
    intersection the search is satisfiable (s6* below) and the structural
    checker still verifies zero four-cycles at every prefix.
    """
    # v3 shifts are positional per mask entry: shifts[a][k] pairs with
    # mask[a][k]; the difference uses the shift belonging to column b.  Blocks
    # are evaluated rarest-first with the accepted set unchanged: the
    # lexicographically first valid tuple wins.
    checks = sorted(range(6), key=lambda a: -len(tuple(b for b in v3._MASKS[a] if b in _MASK6)))
    for s6 in itertools.product(range(_Z), repeat=_Z):
        ok = True
        for a in checks:
            mask, shifts = v3._MASKS[a], v3._SHIFTS[a]
            entries = [(b, shifts[k]) for k, b in enumerate(mask) if b in _MASK6]
            if len({(s6[b] - s) % _Z for b, s in entries}) != len(entries):
                ok = False
                break
        if ok:
            return s6
    raise ValueError("codebook_invalid")

def _cycles(matrix: tuple[tuple[int, ...], ...]) -> int:
    supports = [set(i for i, x in enumerate(r) if x) for r in matrix]
    return sum(1 for i in range(len(supports)) for j in range(i) if len(supports[i] & supports[j]) >= 2)

def _degrees(matrix: tuple[tuple[int, ...], ...]) -> tuple[int, ...]:
    return tuple(sum(row[c] != 0 for row in matrix) for c in range(_N))

def _pair_proxy(matrix: tuple[tuple[int, ...], ...], field: GF2mField) -> bool:
    for left in range(_N):
        a = tuple(row[left] for row in matrix)
        if not any(a):
            return False
        for right in range(left + 1, _N):
            b = tuple(row[right] for row in matrix)
            if tuple(x != 0 for x in a) != tuple(x != 0 for x in b):
                continue
            pivot = next(i for i, x in enumerate(a) if x)
            ratio = field.mul(b[pivot], field.inverse(a[pivot]))
            if all(field.mul(x, ratio) == y for x, y in zip(a, b)):
                return False
    return True

def _structural_ok(matrices: Mapping[int, tuple[tuple[int, ...], ...]], field: GF2mField) -> bool:
    return all(gf_rank(matrices[c], field) == c and _cycles(matrices[c]) == 0
               and min(_degrees(matrices[c])) >= 2 and _pair_proxy(matrices[c], field)
               for c in _PREFIXES)

def _mother(salt: int, s6: tuple[int, ...], v3_matrices: Mapping[int, Any]) -> tuple[tuple[int, ...], ...]:
    rows = [tuple(int(x) for x in row) for row in v3_matrices[48]]
    for i in range(_Z):
        row = [0] * _N
        for b, shift in zip(_MASK6, s6):
            col = _Z * b + ((i + shift) % _Z)
            row[col] = _coefficient(salt, 48 + i, col)
        rows.append(tuple(row))
    return tuple(rows)

def _find_salt(s6: tuple[int, ...], v3_matrices: Mapping[int, Any]) -> tuple[int, dict[int, tuple[tuple[int, ...], ...]], GF2mField]:
    field = GF2mField.create(_Q)
    for salt in range(65536):
        mother = _mother(salt, s6, v3_matrices)
        matrices = {c: mother[:c] for c in _PREFIXES}
        if _structural_ok(matrices, field):
            return salt, matrices, field
    raise ValueError("codebook_invalid")

def _accepted() -> tuple[tuple[int, ...], int, dict[int, tuple[tuple[int, ...], ...]], GF2mField]:
    """Use the frozen accepted values; the search ran once at acceptance time."""
    s6 = _FROZEN_S6
    salt = _FROZEN_SALT
    if not s6 or salt < 0:
        raise ValueError("codebook_invalid: frozen search values missing")
    v3_manifest, v3_matrices = _v3_cached()
    field = GF2mField.create(_Q)
    mother = _mother(salt, s6, v3_matrices)
    matrices = {c: mother[:c] for c in _PREFIXES}
    if not _structural_ok(matrices, field):
        raise ValueError("codebook_invalid: frozen values fail structural contract")
    return s6, salt, matrices, field

def search_and_freeze() -> dict[str, Any]:
    """One-time acceptance search.  Records s6*/salt*; the results are then
    hardcoded into ``_FROZEN_S6``/``_FROZEN_SALT`` and never re-searched."""
    v3_manifest, v3_matrices = _v3_cached()
    s6 = _find_s6()
    salt, matrices, field = _find_salt(s6, v3_matrices)
    return {"s6": list(s6), "salt": salt,
            "entries": [{"check_count": c, "rank": gf_rank(matrices[c], field),
                         "cycle_count": _cycles(matrices[c]), "pair_proxy_passed": _pair_proxy(matrices[c], field)}
                        for c in _PREFIXES]}

def _canonical_bytes(field: GF2mField, s6: tuple[int, ...], salt: int,
                     matrices: Mapping[int, tuple[tuple[int, ...], ...]]) -> bytes:
    v3_manifest, _ = _v3_cached()
    header = {"canonical_schema": _SCHEMA, "construction_reference": "NBLDPC3 rows 0..47",
              "v3_manifest_id": v3_manifest["manifest_id"], "v3_accepted_salt": v3_manifest["accepted_salt"],
              "extension_block": _EXTENSION_BLOCK, "mask6": list(_MASK6), "s6": list(s6),
              "salt": salt, "q": _Q, "n": _N, "z": _Z,
              "shift_direction": v3._SHIFT_DIRECTION,
              "coefficient_derivation": _COEFFICIENT_DERIVATION,
              "prefixes": list(_PREFIXES), "field": asdict(field.spec)}
    out = bytearray(_MAGIC + _compact(header) + b"\n")
    for row in matrices[56]:
        for x in row:
            out.extend(int(x).to_bytes(2, "big"))
    return bytes(out)

def build_nbldpc_v5a_codebook() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    v3_manifest, _ = _v3_cached()
    s6, salt, matrices, field = _accepted()
    entries = [{"check_count": c, "rank": gf_rank(matrices[c], field),
                "cycle_count": _cycles(matrices[c]), "column_degrees": list(_degrees(matrices[c])),
                "pair_proxy_passed": _pair_proxy(matrices[c], field)} for c in _PREFIXES]
    canonical = _canonical_bytes(field, s6, salt, matrices)
    payload = {"method": METHOD, "canonical_schema": _SCHEMA, "canonical_magic": "NBLDPC5A\\n",
               "q": _Q, "n": _N, "z": _Z, "construction_reference": "NBLDPC3 rows 0..47",
               "v3_manifest_id": v3_manifest["manifest_id"], "v3_accepted_salt": v3_manifest["accepted_salt"],
               "extension_block": _EXTENSION_BLOCK, "mask6": list(_MASK6), "s6": list(s6),
               "salt": salt, "shift_direction": v3._SHIFT_DIRECTION,
               "coefficient_derivation": _COEFFICIENT_DERIVATION,
               "field": asdict(field.spec), "field_id": field.spec.field_id,
               "check_counts": list(_PREFIXES), "ordered_entries": entries,
               "canonical_sha256": _sha(canonical), "canonical_byte_length": len(canonical)}
    return dict(payload, manifest_id=_sha(_compact(payload))), matrices

def codebook() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    """Fresh manifest container over a cached deterministic reconstruction."""
    manifest, matrices = _codebook_cached()
    return dict(manifest), matrices

@lru_cache(maxsize=1)
def _codebook_cached() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    return build_nbldpc_v5a_codebook()

def verify_nbldpc_v5a_codebook(manifest: Mapping[str, Any], matrices: Mapping[int, Any]) -> dict[str, Any]:
    try:
        expected, expected_matrices = build_nbldpc_v5a_codebook()
        supplied = {c: tuple(tuple(int(x) for x in r) for r in matrices[c]) for c in _PREFIXES}
        if dict(manifest) != expected or tuple(matrices.keys()) != _PREFIXES or supplied != expected_matrices:
            raise ValueError("deterministic reconstruction mismatch")
        return {"status": "ok", "method": METHOD, "manifest_id": expected["manifest_id"],
                "check_counts": list(_PREFIXES)}
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return {"status": "codebook_invalid", "method": METHOD}
