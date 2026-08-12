"""NBLDPC6: deterministic degree-2 PEG codebooks for ``nbldpc_formal_v6_long``.

Two fixed-rate matrices over the accepted polynomial-basis GF(1024):

| stratum | n    | m    | variable degree | check degrees |
|---------|------|------|-----------------|---------------|
| p=.20   | 1024 | 320  | exactly 2       | 6 or 7        |
| p=.30   | 1024 | 480  | exactly 2       | 4 or 5        |

Construction contract (frozen, no unbounded search after acceptance):

- Columns are processed in ascending order ``0..n-1``.  Every variable gets
  exactly two incident edges.
- The first edge of a column chooses a minimum-degree check; ties are broken
  by a domain-separated SHA256 digest.
- The second edge uses breadth-first PEG expansion rooted at the first-edge
  check to maximize local girth (the maximum-depth frontier), then minimum
  check degree, then the same SHA256 tie-break.  Parallel edges are
  forbidden.
- Nonzero GF coefficients are derived independently from domain-separated
  SHA256 over ``(seed, row, col)`` and reduced to ``1..1023``.
- The minimum-degree rule keeps every check degree within one of every other
  check degree, and the total edge budget ``2*n`` fixes the frozen
  ``{6,7}`` / ``{4,5}`` histograms below.
- Full GF(1024) row rank is required; the frozen seeds below were found by a
  one-time bounded acceptance search (each seed is the first candidate that
  yields full rank) and are never re-searched at runtime.

Canonical bytes are ``NBLDPC6`` magic + compact header (schema, construction
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

METHOD = "nbldpc_formal_v6_long"
_SCHEMA = "NBLDPC6"
_MAGIC = b"NBLDPC6\n"
_CONSTRUCTION_VERSION = 1
_Q, _N = 1024, 1024
_CHECK_COUNTS = (320, 480)
# Frozen one-time acceptance search results: the first construction seed for
# each check count that gives full GF(1024) row rank with the frozen edge
# rules below.  The search is never re-run after acceptance.
_FROZEN_SEEDS = {320: 2026080200, 480: 2026080300}
_STRATUM_P = {320: 0.20, 480: 0.30}
_FIRST_EDGE_RULE = "min_check_degree_then_domain_separated_sha256_tiebreak"
_SECOND_EDGE_RULE = "bfs_peg_max_local_girth_then_min_degree_then_domain_separated_sha256_tiebreak"
_COEFFICIENT_DERIVATION = "1 + int.from_bytes(SHA256(ASCII('NBLDPC6|coef|{seed}|{row}|{col}')), 'big') % 1023"


def _compact(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def _coefficient(seed: int, row: int, col: int) -> int:
    text = f"NBLDPC6|coef|{seed}|{row}|{col}".encode("ascii")
    return 1 + int.from_bytes(hashlib.sha256(text).digest(), "big") % 1023


def _tiebreak(candidates: list[int], label: str, seed: int, m: int, col: int) -> int:
    """Domain-separated SHA256 tie-break: the lexicographically smallest digest wins."""
    best, best_digest = None, None
    for candidate in candidates:
        domain = f"NBLDPC6|{label}|{seed}|{m}|{col}|{candidate}".encode("ascii")
        digest = hashlib.sha256(domain).digest()
        if best_digest is None or digest < best_digest:
            best, best_digest = candidate, digest
    assert best is not None
    return best


def _construct(m: int, seed: int) -> tuple[tuple[tuple[int, ...], ...], list[int], int, int]:
    """Deterministic degree-2 PEG construction; returns (rows, check_degrees,
    parallel_edges, four_cycles)."""
    if m not in _CHECK_COUNTS:
        raise ValueError("invalid NBLDPC6 check count")
    check_neighbors: list[set[int]] = [set() for _ in range(m)]
    variable_neighbors: list[set[int]] = [set() for _ in range(_N)]
    check_degree = [0] * m
    edges: list[tuple[int, int]] = []
    for col in range(_N):
        min_degree = min(check_degree)
        first = _tiebreak([r for r in range(m) if check_degree[r] == min_degree],
                          "first", seed, m, col)
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
            candidates = [r for r in range(m) if r != first]
        min_degree_2 = min(check_degree[r] for r in candidates)
        second = _tiebreak([r for r in candidates if check_degree[r] == min_degree_2],
                           "second", seed, m, col)
        for edge_check in (first, second):
            edges.append((edge_check, col))
            check_neighbors[edge_check].add(col)
            variable_neighbors[col].add(edge_check)
            check_degree[edge_check] += 1
    rows: list[tuple[int, ...]] = []
    for row in range(m):
        values = [0] * _N
        for edge_row, col in edges:
            if edge_row == row:
                values[col] = _coefficient(seed, row, col)
        rows.append(tuple(values))
    matrix = tuple(rows)
    parallel = len(edges) - len(set(edges))
    supports = [set(i for i, value in enumerate(row) if value) for row in matrix]
    four_cycles = sum(1 for i in range(m) for j in range(i) if len(supports[i] & supports[j]) >= 2)
    return matrix, check_degree, parallel, four_cycles


def _check_degree_histogram(degrees: list[int]) -> dict[str, int]:
    histogram: dict[str, int] = {}
    for degree in degrees:
        histogram[str(degree)] = histogram.get(str(degree), 0) + 1
    return histogram


def _canonical_bytes(matrix: tuple[tuple[int, ...], ...], field: GF2mField, *,
                     m: int, seed: int) -> bytes:
    header = {
        "canonical_schema": _SCHEMA, "construction_version": _CONSTRUCTION_VERSION,
        "method": METHOD, "q": _Q, "n": _N, "m": m,
        "stratum_p": _STRATUM_P[m], "construction_seed": seed,
        "first_edge_rule": _FIRST_EDGE_RULE, "second_edge_rule": _SECOND_EDGE_RULE,
        "coefficient_derivation": _COEFFICIENT_DERIVATION, "field": asdict(field.spec),
    }
    out = bytearray(_MAGIC + _compact(header) + b"\n")
    for row in matrix:
        for value in row:
            out.extend(int(value).to_bytes(2, "big"))
    return bytes(out)


@lru_cache(maxsize=2)
def _matrix_cached(m: int, seed: int) -> tuple[tuple[tuple[int, ...], ...], list[int], int, int]:
    return _construct(m, seed)


@lru_cache(maxsize=1)
def build_nbldpc_v6_codebook() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    """Reconstruct the frozen two-matrix family and its canonical manifest."""
    field = GF2mField.create(_Q)
    matrices: dict[int, tuple[tuple[int, ...], ...]] = {}
    entries: list[dict[str, Any]] = []
    for m in _CHECK_COUNTS:
        seed = _FROZEN_SEEDS[m]
        matrix, check_degrees, parallel, four_cycles = _matrix_cached(m, seed)
        rank = gf_rank(matrix, field)
        if rank != m:
            raise ValueError("NBLDPC6 frozen seed lost full rank")
        column_degrees = [sum(row[col] != 0 for row in matrix) for col in range(_N)]
        if any(degree != 2 for degree in column_degrees):
            raise ValueError("NBLDPC6 variable degree contract violated")
        if parallel != 0:
            raise ValueError("NBLDPC6 parallel-edge contract violated")
        histogram = _check_degree_histogram(check_degrees)
        degree_values = sorted(map(int, histogram))
        if len(histogram) != 2 or degree_values[1] != degree_values[0] + 1:
            raise ValueError("NBLDPC6 check-degree balance contract violated")
        canonical = _canonical_bytes(matrix, field, m=m, seed=seed)
        matrices[m] = matrix
        entries.append({
            "stratum_p": _STRATUM_P[m], "check_count": m, "construction_seed": seed,
            "edge_count": 2 * _N, "rank": rank, "cycle_count": four_cycles,
            "parallel_edges": parallel, "variable_degree_min": min(column_degrees),
            "variable_degree_max": max(column_degrees),
            "check_degree_histogram": histogram,
            "canonical_sha256": _sha(canonical), "canonical_byte_length": len(canonical),
        })
    payload = {
        "method": METHOD, "canonical_schema": _SCHEMA, "canonical_magic": "NBLDPC6\\n",
        "construction_version": _CONSTRUCTION_VERSION, "q": _Q, "n": _N,
        "field": asdict(field.spec), "field_id": field.spec.field_id,
        "coefficient_derivation": _COEFFICIENT_DERIVATION,
        "first_edge_rule": _FIRST_EDGE_RULE, "second_edge_rule": _SECOND_EDGE_RULE,
        "check_counts": list(_CHECK_COUNTS), "ordered_entries": entries,
    }
    return dict(payload, manifest_id=_sha(_compact(payload))), matrices


def codebook() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    """Fresh manifest container over a cached deterministic reconstruction."""
    manifest, matrices = _codebook_cached()
    return dict(manifest), matrices


@lru_cache(maxsize=1)
def _codebook_cached() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    return build_nbldpc_v6_codebook()


def verify_nbldpc_v6_codebook(manifest: Mapping[str, Any], matrices: Mapping[int, Any]) -> dict[str, Any]:
    """Fail closed after independently reconstructing every NBLDPC6 contract value."""
    try:
        if not isinstance(manifest, Mapping) or not isinstance(matrices, Mapping):
            raise ValueError("invalid codebook container")
        expected, expected_matrices = build_nbldpc_v6_codebook()
        supplied = {m: tuple(tuple(int(x) for x in row) for row in matrices[m])
                    for m in _CHECK_COUNTS}
        if dict(manifest) != expected or tuple(matrices.keys()) != _CHECK_COUNTS \
                or supplied != expected_matrices:
            raise ValueError("deterministic reconstruction mismatch")
        return {"status": "ok", "method": METHOD,
                "manifest_id": expected["manifest_id"], "check_counts": list(_CHECK_COUNTS)}
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return {"status": "codebook_invalid", "method": METHOD}
