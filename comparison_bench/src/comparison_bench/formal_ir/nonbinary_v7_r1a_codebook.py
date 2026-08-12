"""NBLDPC7 R1A: deterministic degree-2 PEG ``(2,3)`` mother for
``nbldpc_formal_v7_r1a_mr0``.

One fixed-rate mother over the accepted polynomial-basis GF(1024):

| q     | n    | m    | variable degree | check degrees      | rate |
|-------|------|------|-----------------|--------------------|------|
| 1024  | 256  | 170  | exactly 2       | 168 x degree-3 + 2 x degree-4 | ~1/3 |

Check-count freeze (authoritative, V7-00 implementation note): nominal rate
1/3 with ``n=256`` variables and ``(dv,dc)=(2,3)`` gives ``n-k = 256 - 256/1.5
= 170.67``; the natural freeze is ``m=170`` checks (``10*(n-k)`` rounded to a
whole check count), which fixes ``k=86`` information symbols and rate
``86/256 = 0.3359``.  The total edge budget ``2*n = 512`` over 170 checks is
``512 = 168*3 + 2*4``, so exactly 168 check nodes have degree 3 and 2 have
degree 4.  Syndrome disclosure is ``10*m = 1700`` bits.

Construction contract (frozen, no unbounded search after acceptance):

- Columns are processed in ascending order ``0..n-1``.  Every variable gets
  exactly two incident edges.
- The first edge of a column chooses a minimum-degree check; ties are broken
  by a domain-separated SHA256 digest.
- The second edge uses breadth-first PEG expansion rooted at the first-edge
  check to maximize local girth (the maximum-depth frontier), then minimum
  check degree, then the same SHA256 tie-break.  Parallel edges are forbidden.
- Nonzero GF coefficients are derived independently from domain-separated
  SHA256 over ``(seed, row, col)`` and reduced to ``1..1023``.
- The minimum-degree rule keeps every check degree within one of every other
  check degree, which over the frozen 512-edge budget fixes the histogram
  ``{3: 168, 4: 2}`` below.
- Full GF(1024) row rank (170) is required; the frozen seed ``2026080400``
  below is the first candidate found by a one-time bounded acceptance search
  and is never re-searched at runtime.

Canonical bytes are ``NBLDPC7`` magic + compact header (schema, construction
version, q/n/m, field identity, seed, edge rules, coefficient derivation) +
row-major 16-bit big-endian coefficients.  The manifest records SHA256, GF
rank, edge count, degree histograms, parallel-edge count, four-cycle count
and the full reconstruction parameters.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from functools import lru_cache
from typing import Any, Mapping

from .nonbinary_codebook import gf_rank
from .nonbinary_field import GF2mField

METHOD = "nbldpc_formal_v7_r1a_mr0"
_SCHEMA = "NBLDPC7"
_MAGIC = b"NBLDPC7\n"
_CONSTRUCTION_VERSION = 1
_Q, _N, _M = 1024, 256, 170
# Frozen one-time acceptance search result: the first construction seed giving
# full GF(1024) row rank (170) under the frozen edge rules.  Never re-searched.
_FROZEN_SEED = 2026080400
_CHECK_DEGREE_HISTOGRAM = {3: 168, 4: 2}
_FIRST_EDGE_RULE = "min_check_degree_then_domain_separated_sha256_tiebreak"
_SECOND_EDGE_RULE = "bfs_peg_max_local_girth_then_min_degree_then_domain_separated_sha256_tiebreak"
_COEFFICIENT_DERIVATION = "1 + int.from_bytes(SHA256(ASCII('NBLDPC7|coef|{seed}|{row}|{col}')), 'big') % 1023"


def _compact(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def _coefficient(seed: int, row: int, col: int) -> int:
    text = f"NBLDPC7|coef|{seed}|{row}|{col}".encode("ascii")
    return 1 + int.from_bytes(hashlib.sha256(text).digest(), "big") % 1023


def _tiebreak(candidates: list[int], label: str, seed: int, m: int, col: int) -> int:
    """Domain-separated SHA256 tie-break: the lexicographically smallest digest wins."""
    best, best_digest = None, None
    for candidate in candidates:
        domain = f"NBLDPC7|{label}|{seed}|{m}|{col}|{candidate}".encode("ascii")
        digest = hashlib.sha256(domain).digest()
        if best_digest is None or digest < best_digest:
            best, best_digest = candidate, digest
    assert best is not None
    return best


def _construct(seed: int) -> tuple[tuple[tuple[int, ...], ...], list[int], int, int]:
    """Deterministic degree-2 PEG construction; returns (rows, check_degrees,
    parallel_edges, four_cycles)."""
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("construction_seed must be an integer")
    check_neighbors: list[set[int]] = [set() for _ in range(_M)]
    variable_neighbors: list[set[int]] = [set() for _ in range(_N)]
    check_degree = [0] * _M
    edges: list[tuple[int, int]] = []
    for col in range(_N):
        min_degree = min(check_degree)
        first = _tiebreak([r for r in range(_M) if check_degree[r] == min_degree],
                          "first", seed, _M, col)
        # Breadth-first PEG expansion rooted at the first-edge check.  The
        # maximum-depth frontier maximizes local girth for the new second
        # edge; the depth-0 frontier (the graph is still too small) falls
        # back to a plain minimum-degree scan.
        seen = {first}
        frontier = {first}
        while True:
            next_variables = set()
            for chk in frontier:
                next_variables |= check_neighbors[chk]
            next_variables.discard(col)
            next_checks = set()
            for variable in next_variables:
                next_checks |= variable_neighbors[variable]
            next_checks -= seen
            if not next_checks:
                break
            seen |= next_checks
            frontier = next_checks
        candidates = [r for r in frontier if r != first]
        if not candidates:
            candidates = [r for r in range(_M) if r != first]
        min_degree_2 = min(check_degree[r] for r in candidates)
        second = _tiebreak([r for r in candidates if check_degree[r] == min_degree_2],
                           "second", seed, _M, col)
        for edge_check in (first, second):
            edges.append((edge_check, col))
            check_neighbors[edge_check].add(col)
            variable_neighbors[col].add(edge_check)
            check_degree[edge_check] += 1
    rows: list[tuple[int, ...]] = []
    for row in range(_M):
        values = [0] * _N
        for edge_row, col in edges:
            if edge_row == row:
                values[col] = _coefficient(seed, row, col)
        rows.append(tuple(values))
    matrix = tuple(rows)
    parallel = len(edges) - len(set(edges))
    supports = [set(i for i, value in enumerate(row) if value) for row in matrix]
    four_cycles = sum(1 for i in range(_M) for j in range(i) if len(supports[i] & supports[j]) >= 2)
    return matrix, check_degree, parallel, four_cycles


def _check_degree_histogram(degrees: list[int]) -> dict[str, int]:
    histogram: dict[str, int] = {}
    for degree in degrees:
        histogram[str(degree)] = histogram.get(str(degree), 0) + 1
    return histogram


def _canonical_bytes(matrix: tuple[tuple[int, ...], ...], field: GF2mField, *, seed: int) -> bytes:
    header = {
        "canonical_schema": _SCHEMA, "construction_version": _CONSTRUCTION_VERSION,
        "method": METHOD, "q": _Q, "n": _N, "m": _M,
        "construction_seed": seed,
        "first_edge_rule": _FIRST_EDGE_RULE, "second_edge_rule": _SECOND_EDGE_RULE,
        "coefficient_derivation": _COEFFICIENT_DERIVATION, "field": asdict(field.spec),
    }
    out = bytearray(_MAGIC + _compact(header) + b"\n")
    for row in matrix:
        for value in row:
            out.extend(int(value).to_bytes(2, "big"))
    return bytes(out)


@lru_cache(maxsize=1)
def _matrix_cached(seed: int) -> tuple[tuple[tuple[int, ...], ...], list[int], int, int]:
    return _construct(seed)


@lru_cache(maxsize=1)
def build_nbldpc_v7_r1a_codebook() -> tuple[dict[str, Any], tuple[tuple[int, ...], ...]]:
    """Reconstruct the frozen R1A mother matrix and its canonical manifest."""
    field = GF2mField.create(_Q)
    matrix, check_degrees, parallel, four_cycles = _matrix_cached(_FROZEN_SEED)
    rank = gf_rank(matrix, field)
    if rank != _M:
        raise ValueError("NBLDPC7 frozen seed lost full rank")
    column_degrees = [sum(row[col] != 0 for row in matrix) for col in range(_N)]
    if any(degree != 2 for degree in column_degrees):
        raise ValueError("NBLDPC7 variable degree contract violated")
    if parallel != 0:
        raise ValueError("NBLDPC7 parallel-edge contract violated")
    histogram = _check_degree_histogram(check_degrees)
    if dict(histogram) != {str(k): v for k, v in _CHECK_DEGREE_HISTOGRAM.items()}:
        raise ValueError("NBLDPC7 check-degree histogram contract violated")
    canonical = _canonical_bytes(matrix, field, seed=_FROZEN_SEED)
    payload = {
        "method": METHOD, "canonical_schema": _SCHEMA, "canonical_magic": "NBLDPC7\\n",
        "construction_version": _CONSTRUCTION_VERSION, "q": _Q, "n": _N, "m": _M,
        "field": asdict(field.spec), "field_id": field.spec.field_id,
        "construction_seed": _FROZEN_SEED,
        "coefficient_derivation": _COEFFICIENT_DERIVATION,
        "first_edge_rule": _FIRST_EDGE_RULE, "second_edge_rule": _SECOND_EDGE_RULE,
        "edge_count": 2 * _N, "rank": rank, "cycle_count": four_cycles,
        "parallel_edges": parallel, "variable_degree_min": min(column_degrees),
        "variable_degree_max": max(column_degrees),
        "check_degree_histogram": histogram,
        "canonical_sha256": _sha(canonical), "canonical_byte_length": len(canonical),
    }
    return dict(payload, manifest_id=_sha(_compact(payload))), matrix


def codebook() -> tuple[dict[str, Any], tuple[tuple[int, ...], ...]]:
    """Fresh manifest container over a cached deterministic reconstruction."""
    manifest, matrix = _codebook_cached()
    return dict(manifest), matrix


@lru_cache(maxsize=1)
def _codebook_cached() -> tuple[dict[str, Any], tuple[tuple[int, ...], ...]]:
    return build_nbldpc_v7_r1a_codebook()


def verify_nbldpc_v7_r1a_codebook(manifest: Mapping[str, Any], matrix: Any) -> dict[str, Any]:
    """Fail closed after independently reconstructing every NBLDPC7 contract value."""
    try:
        if not isinstance(manifest, Mapping):
            raise ValueError("invalid codebook container")
        expected, expected_matrix = build_nbldpc_v7_r1a_codebook()
        supplied = tuple(tuple(int(x) for x in row) for row in matrix)
        if dict(manifest) != expected or supplied != expected_matrix:
            raise ValueError("deterministic reconstruction mismatch")
        return {"status": "ok", "method": METHOD,
                "manifest_id": expected["manifest_id"], "check_count": _M}
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return {"status": "codebook_invalid", "method": METHOD}
