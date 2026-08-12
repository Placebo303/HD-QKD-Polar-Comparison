"""NBLDPC5B: deterministic 56-row nested-prefix mother code (Route B).

Route B redesigns the mother instead of extending the frozen v3 rows.  A
56-row mother is built from 7 blocks x 8 rows with frozen block masks
(row weights 6,6,6,4,4,6,4 — no full-column block):

  blocks = ((0,1,2,3,4,5), (0,1,2,3,6,7), (0,1,4,5,6,7),
            (0,2,4,6), (1,3,5,7), (0,1,2,3,4,5), (0,2,4,6))

Nested ordered prefixes 32/40/48/56 take the first 4/5/6/7 blocks.  For each
block ``a`` in order, its 8 shifts are enumerated lexicographically over
(Z/8)^8 (per-column shifts, exactly like the frozen v3/v5a shift convention);
the first tuple is accepted whose disjoint-shift-difference condition holds
against every already-fixed block: for every common column ``c`` in
``mask_a ∩ mask_b`` the values ``(s_a[c] - s_b[c]) mod 8`` are all distinct.
That condition keeps every pair of rows sharing at most one column position,
so every prefix has zero four-cycles.

Coefficients use ``1 + SHA256(ASCII("NBLDPC5B|coef|{salt}|{a}|{b}")) mod 1023``
where ``a`` is the block index and ``b`` the position inside the block mask.
``salt`` is enumerated from 0; a candidate is acceptable when every prefix
32/40/48/56 has full GF(1024) rank, zero four-cycles, minimum column degree
>= 2, and passes the pair-proxy check.

Distance-spectrum proxy (frozen): for each acceptable candidate compute exact
low-weight syndrome collision counts over the 56-row mother: weight-2
(C(64,2) = 2016 column pairs) and weight-3 (C(64,3) = 41664 column triples).
Among the first K=8 acceptable (salt, shifts) candidates the candidate with
the lexicographically minimal ``(w2_collisions, w3_collisions)`` is selected;
ties break by the smallest ``construction_seed`` (the candidate's 0-based
acceptance order).  The proxy prefers mothers with fewer short-weight
codewords, targeting the p=.30 tail.

The accepted (shifts, salt) and the proxy scores are recorded in the
canonical manifest and never re-searched after acceptance time.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import asdict
from functools import lru_cache
from typing import Any, Mapping

from .nonbinary_codebook import gf_rank
from .nonbinary_field import GF2mField

METHOD = "nbldpc_formal_v5b_mother"
_SCHEMA, _MAGIC = "NBLDPC5B", b"NBLDPC5B\n"
_Q, _N, _Z = 1024, 64, 8
_PREFIXES = (32, 40, 48, 56)
_BLOCK_MASKS = ((0, 1, 2, 3, 4, 5), (0, 1, 2, 3, 6, 7), (0, 1, 4, 5, 6, 7),
                (0, 2, 4, 6), (1, 3, 5, 7), (0, 1, 2, 3, 4, 5), (0, 2, 4, 6))
_K = 8
_SHIFT_DIRECTION = "col=8*b+((i+shift)%8)"
_COEFFICIENT_DERIVATION = "1 + int.from_bytes(SHA256(ASCII('NBLDPC5B|coef|{salt}|{a}|{b}')), 'big') mod 1023"
_CONSTRUCTION_SEED = 2026073105


def _compact(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
def _sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()

def _coefficient(salt: int, block: int, position: int) -> int:
    text = f"NBLDPC5B|coef|{salt}|{block}|{position}".encode("ascii")
    return 1 + int.from_bytes(hashlib.sha256(text).digest(), "big") % 1023

def _find_shifts() -> tuple[tuple[int, ...], ...]:
    """Lexicographically first per-column 8-shift tuple per block with
    disjoint shift differences vs every already-fixed block.

    The shift tuple is indexed by column (0..7), as in the frozen v3/v5a
    convention; the block mask selects which entries are used.
    """
    accepted: list[tuple[int, ...]] = []
    for mask in _BLOCK_MASKS:
        for candidate in itertools.product(range(_Z), repeat=_Z):
            ok = True
            for previous, prior_mask in zip(accepted, _BLOCK_MASKS[:len(accepted)]):
                common = [c for c in mask if c in prior_mask]
                if len({(candidate[c] - previous[c]) % _Z for c in common}) != len(common):
                    ok = False
                    break
            if ok:
                accepted.append(candidate)
                break
        else:
            raise ValueError("codebook_invalid: shift search exhausted")
    return tuple(accepted)

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

def _w2_collisions(matrix: tuple[tuple[int, ...], ...], field: GF2mField) -> int:
    """Exact weight-2 syndrome collisions: pairs of proportional columns."""
    columns = [tuple(row[c] for row in matrix) for c in range(_N)]
    count = 0
    for left in range(_N):
        a = columns[left]
        for right in range(left + 1, _N):
            b = columns[right]
            if tuple(x != 0 for x in a) != tuple(x != 0 for x in b):
                continue
            pivot = next(i for i, x in enumerate(a) if x)
            ratio = field.mul(b[pivot], field.inverse(a[pivot]))
            if all(field.mul(x, ratio) == y for x, y in zip(a, b)):
                count += 1
    return count

def _w3_collisions(matrix: tuple[tuple[int, ...], ...], field: GF2mField) -> int:
    """Exact weight-3 syndrome collisions: triples of linearly dependent
    columns (rank < 3 over GF(1024))."""
    columns = [tuple(row[c] for row in matrix) for c in range(_N)]
    count = 0
    for left in range(_N):
        for middle in range(left + 1, _N):
            for right in range(middle + 1, _N):
                if gf_rank((columns[left], columns[middle], columns[right]), field) < 3:
                    count += 1
    return count

def _mother(salt: int, shifts: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    rows: list[tuple[int, ...]] = []
    for a, (mask, shift_tuple) in enumerate(zip(_BLOCK_MASKS, shifts)):
        for i in range(_Z):
            row = [0] * _N
            for position, b in enumerate(mask):
                row[_Z * b + ((i + shift_tuple[b]) % _Z)] = _coefficient(salt, a, position)
            rows.append(tuple(row))
    return tuple(rows)

def _find_candidates(shifts: tuple[tuple[int, ...], ...], limit: int = _K) -> list[tuple[int, int, int]]:
    """One-time acceptance search: first ``limit`` acceptable (salt, shifts)
    candidates with their w2/w3 proxy scores, in ascending salt order."""
    field = GF2mField.create(_Q)
    found: list[tuple[int, int, int]] = []
    for salt in range(65536):
        mother = _mother(salt, shifts)
        matrices = {c: mother[:c] for c in _PREFIXES}
        if not _structural_ok(matrices, field):
            continue
        w2 = _w2_collisions(mother, field)
        w3 = _w3_collisions(mother, field)
        found.append((salt, w2, w3))
        if len(found) >= limit:
            return found
    raise ValueError("codebook_invalid: candidate search exhausted")

def _select_candidate(candidates: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    """Lexicographically minimal (w2, w3); ties break by the smallest
    construction_seed (0-based acceptance order = ascending salt)."""
    if len(candidates) != _K:
        raise ValueError("codebook_invalid: K candidate contract")
    return min(enumerate(candidates), key=lambda item: (item[1][1], item[1][2], item[0]))[1]

# Frozen accepted values found by the one-time acceptance search (T0).  The
# search is never re-run; these constants are part of the canonical identity.
_FROZEN_SHIFTS: tuple[tuple[int, ...], ...] = ((0, 0, 0, 0, 0, 0, 0, 0),
                                               (0, 1, 2, 3, 0, 0, 0, 0),
                                               (0, 2, 0, 0, 1, 3, 2, 3),
                                               (0, 0, 1, 0, 2, 0, 1, 0),
                                               (0, 0, 0, 1, 0, 2, 0, 0),
                                               (0, 3, 5, 1, 4, 7, 0, 0),
                                               (0, 0, 3, 0, 5, 0, 5, 0))
_FROZEN_SALT: int = 0
_FROZEN_W2: int = 0
_FROZEN_W3: int = 0

def _accepted() -> tuple[tuple[tuple[int, ...], ...], int, int, int, dict[int, tuple[tuple[int, ...], ...]], GF2mField]:
    if _FROZEN_SHIFTS is None or _FROZEN_SALT < 0:
        raise ValueError("codebook_invalid: frozen search values missing")
    field = GF2mField.create(_Q)
    mother = _mother(_FROZEN_SALT, _FROZEN_SHIFTS)
    matrices = {c: mother[:c] for c in _PREFIXES}
    if not _structural_ok(matrices, field):
        raise ValueError("codebook_invalid: frozen values fail structural contract")
    if _w2_collisions(mother, field) != _FROZEN_W2 or _w3_collisions(mother, field) != _FROZEN_W3:
        raise ValueError("codebook_invalid: frozen proxy scores fail reconstruction")
    return _FROZEN_SHIFTS, _FROZEN_SALT, _FROZEN_W2, _FROZEN_W3, matrices, field

def search_and_freeze() -> dict[str, Any]:
    """One-time acceptance search.  Records shifts*/salt*/w2*/w3*; the results
    are then hardcoded into the ``_FROZEN_*`` constants and never re-searched."""
    shifts = _find_shifts()
    candidates = _find_candidates(shifts)
    salt, w2, w3 = _select_candidate(candidates)
    field = GF2mField.create(_Q)
    mother = _mother(salt, shifts)
    matrices = {c: mother[:c] for c in _PREFIXES}
    return {"shifts": [list(s) for s in shifts], "salt": salt, "w2_collisions": w2,
            "w3_collisions": w3, "candidate_scores": [[s, a, b] for s, a, b in candidates],
            "entries": [{"check_count": c, "rank": gf_rank(matrices[c], field),
                         "cycle_count": _cycles(matrices[c]), "pair_proxy_passed": _pair_proxy(matrices[c], field)}
                        for c in _PREFIXES]}

def _canonical_bytes(field: GF2mField, shifts: tuple[tuple[int, ...], ...], salt: int,
                     matrices: Mapping[int, tuple[tuple[int, ...], ...]]) -> bytes:
    header = {"canonical_schema": _SCHEMA, "construction_seed": _CONSTRUCTION_SEED,
              "accepted_salt": salt, "base_masks": [list(x) for x in _BLOCK_MASKS],
              "shifts": [list(x) for x in shifts], "shift_direction": _SHIFT_DIRECTION,
              "coefficient_derivation": _COEFFICIENT_DERIVATION, "q": _Q, "n": _N, "z": _Z,
              "prefixes": list(_PREFIXES), "field": asdict(field.spec)}
    out = bytearray(_MAGIC + _compact(header) + b"\n")
    for row in matrices[56]:
        for x in row:
            out.extend(int(x).to_bytes(2, "big"))
    return bytes(out)

def build_nbldpc_v5b_codebook() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    shifts, salt, w2, w3, matrices, field = _accepted()
    entries = [{"check_count": c, "rank": gf_rank(matrices[c], field),
                "cycle_count": _cycles(matrices[c]), "column_degrees": list(_degrees(matrices[c])),
                "pair_proxy_passed": _pair_proxy(matrices[c], field)} for c in _PREFIXES]
    canonical = _canonical_bytes(field, shifts, salt, matrices)
    payload = {"method": METHOD, "canonical_schema": _SCHEMA, "canonical_magic": "NBLDPC5B\\n",
               "q": _Q, "n": _N, "z": _Z, "construction_seed": _CONSTRUCTION_SEED,
               "accepted_salt": salt, "base_masks": [list(x) for x in _BLOCK_MASKS],
               "shifts": [list(x) for x in shifts], "shift_direction": _SHIFT_DIRECTION,
               "coefficient_derivation": _COEFFICIENT_DERIVATION,
               "w2_collisions": w2, "w3_collisions": w3, "proxy": "exact_low_weight_syndrome_collisions",
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
    return build_nbldpc_v5b_codebook()

def verify_nbldpc_v5b_codebook(manifest: Mapping[str, Any], matrices: Mapping[int, Any]) -> dict[str, Any]:
    try:
        expected, expected_matrices = build_nbldpc_v5b_codebook()
        supplied = {c: tuple(tuple(int(x) for x in r) for r in matrices[c]) for c in _PREFIXES}
        if dict(manifest) != expected or tuple(matrices.keys()) != _PREFIXES or supplied != expected_matrices:
            raise ValueError("deterministic reconstruction mismatch")
        return {"status": "ok", "method": METHOD, "manifest_id": expected["manifest_id"],
                "check_counts": list(_PREFIXES)}
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return {"status": "codebook_invalid", "method": METHOD}
