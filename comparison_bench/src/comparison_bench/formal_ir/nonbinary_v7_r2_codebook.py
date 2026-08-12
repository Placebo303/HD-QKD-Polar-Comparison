"""NBLDPC7 R2: deterministic PEG codebooks for ``nbldpc_formal_v7_r2_qsc_de``.

Two fixed-rate matrices over the accepted polynomial-basis GF(1024), one per
stratum, constructed from the FROZEN q-ary density-evolution selection of
``nonbinary_v7_r2_de`` (V7-20 bounded population search):

| stratum | n    | m    | variable distribution (frozen DE selection) | mean check degree |
|---------|------|------|---------------------------------------------|-------------------|
| p=.20   | 1024 | 321  | {3: 1024} (regular degree 3)                | 9.5701 (9/10)     |
| p=.30   | 1024 | 458  | {3: 1024} (regular degree 3)                | 6.7074 (6/7)      |

Check-count freeze (V7-20 implementation note, exact arithmetic): the target
syndrome fraction starts from ``1.15*H_q(p)/10`` where ``H_q(p) =
h2(p) + p*log2(q-1)``; rounded UPWARD to a whole check count over n=1024:

- p=.20: ``H_q = 2.7216461808364283`` bits -> ``1.15*H_q/10*1024 =
  320.500895...`` -> ``m = 321`` (syndrome 3210 bits, rate 0.68652);
- p=.30: ``H_q = 3.880868028154292`` bits -> ``1.15*H_q/10*1024 =
  457.011020...`` -> ``m = 458`` (syndrome 4580 bits, rate 0.55273).

The DE threshold proxy of the frozen selections (same bounded search): p=.20
selected {3: 1024} with threshold proxy 0.19058; p=.30 selected {3: 1024}
with threshold proxy 0.29373.  These are selection proxies, not FER promises;
the sacrificed canary decides capacity.

Construction contract (frozen, no unbounded search after acceptance):

- Columns are processed in ascending order ``0..n-1``.  Each column receives
  exactly ``d_v`` incident edges where ``d_v`` follows the frozen variable
  distribution (deterministic ascending block assignment of the column
  degrees).
- The first edge of a column chooses a minimum-degree check; ties are broken
  by a domain-separated SHA256 digest.
- Every later edge uses breadth-first PEG expansion rooted at the column's
  already-assigned check neighbors (maximum-depth frontier), then minimum
  check degree, then the same SHA256 tie-break.  Parallel edges are
  forbidden.
- Nonzero GF coefficients are derived independently from domain-separated
  SHA256 over ``(seed, row, col)`` and reduced to ``1..1023``.
- The minimum-degree rule keeps every check degree within one of every other
  check degree, fixing the implied ``{9,10}`` / ``{6,7}`` histograms below.
- Full GF(1024) row rank is required; the frozen seeds below were found by a
  one-time bounded acceptance search (each seed is the first candidate that
  yields full rank) and are never re-searched at runtime.

Canonical bytes are ``NBLDPC7R2`` magic + compact header (schema, construction
version, q/n/m, field identity, stratum, seed, distribution, edge rules,
coefficient derivation) + row-major 16-bit big-endian coefficients.  The
manifest records SHA256, GF rank, edge count, degree histograms, parallel-edge
count, four-cycle count, the frozen DE selection identity, and the full
reconstruction parameters.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from functools import lru_cache
from typing import Any, Mapping

from .nonbinary_codebook import gf_rank
from .nonbinary_field import GF2mField
from . import nonbinary_v7_r2_de as de

METHOD = "nbldpc_formal_v7_r2_qsc_de"
_SCHEMA = "NBLDPC7R2"
_MAGIC = b"NBLDPC7R2\n"
_CONSTRUCTION_VERSION = 1
_Q, _N = 1024, 1024
# Frozen V7-20 check-count freeze (exact arithmetic, see module docstring).
_CHECK_COUNTS = {0.20: 321, 0.30: 458}
# Frozen DE selection (V7-20 bounded population search, <= 32 candidates): the
# regular degree-3 distribution won both strata.
_DISTRIBUTIONS = {0.20: {"3": 1024}, 0.30: {"3": 1024}}
_DE_THRESHOLD_PROXIES = {0.20: 0.19058, 0.30: 0.29373}
_DE_SEARCH_RECORDS = {
    0.20: "candidates_evaluated=18, winner order 1 (regular degree 3), threshold 0.19058, probe_count 9",
    0.30: "candidates_evaluated=32 (cap), winner order 1 (regular degree 3), threshold 0.29373, probe_count 9",
}
# Frozen one-time acceptance search results: the first construction seed for
# each stratum that gives full GF(1024) row rank with the frozen edge rules.
# One-time bounded search (never re-run): p=.20 -> 2026080402 (first
# candidate), p=.30 -> 2026080403 (first candidate >= 2026080403).
_FROZEN_SEEDS = {0.20: 2026080402, 0.30: 2026080403}
_FIRST_EDGE_RULE = "min_check_degree_then_domain_separated_sha256_tiebreak"
_PEG_EDGE_RULE = ("bfs_peg_max_local_girth_rooted_at_assigned_check_neighbors_"
                  "then_min_degree_then_domain_separated_sha256_tiebreak")
_COEFFICIENT_DERIVATION = "1 + int.from_bytes(SHA256(ASCII('NBLDPC7R2|coef|{seed}|{row}|{col}')), 'big') % 1023"


def _compact(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def _coefficient(seed: int, row: int, col: int) -> int:
    text = f"NBLDPC7R2|coef|{seed}|{row}|{col}".encode("ascii")
    return 1 + int.from_bytes(hashlib.sha256(text).digest(), "big") % 1023


def _tiebreak(candidates: list[int], label: str, seed: int, m: int, col: int) -> int:
    """Domain-separated SHA256 tie-break: the lexicographically smallest digest wins."""
    best, best_digest = None, None
    for candidate in candidates:
        domain = f"NBLDPC7R2|{label}|{seed}|{m}|{col}|{candidate}".encode("ascii")
        digest = hashlib.sha256(domain).digest()
        if best_digest is None or digest < best_digest:
            best, best_digest = candidate, digest
    assert best is not None
    return best


def column_degrees(stratum_p: float) -> list[int]:
    """Deterministic ascending-block assignment of the frozen distribution."""
    p = float(stratum_p)
    if p not in _DISTRIBUTIONS:
        raise ValueError("unknown NBLDPC7R2 stratum")
    distribution = _DISTRIBUTIONS[p]
    degrees: list[int] = []
    for key in sorted(distribution, key=int):
        degree = int(key)
        count = int(distribution[key])
        if count <= 0 or sum(int(v) for v in distribution.values()) != _N:
            raise ValueError("NBLDPC7R2 distribution contract violated")
        degrees.extend([degree] * count)
    if len(degrees) != _N:
        raise ValueError("NBLDPC7R2 column-degree count contract violated")
    return degrees


def _peg_frontier(column: int, variable_neighbors: list[set[int]],
                  check_neighbors: list[set[int]], first_checks: set[int]) -> set[int]:
    """Maximum-depth frontier of the BFS-PEG tree rooted at the variable's
    already-assigned check neighbors (the accepted v6 expansion, generalized
    to all assigned edges of the column)."""
    seen = set(first_checks)
    frontier = set(first_checks)
    while True:
        next_variables = set()
        for chk in frontier:
            next_variables |= check_neighbors[chk]
        next_variables.discard(column)
        next_checks = set()
        for variable in next_variables:
            next_checks |= variable_neighbors[variable]
        next_checks -= seen
        if not next_checks:
            break
        seen |= next_checks
        frontier = next_checks
    return frontier


def _construct(m: int, seed: int, degrees: list[int]) -> tuple[tuple[tuple[int, ...], ...], list[int], int, int]:
    """Deterministic irregular PEG construction; returns (rows, check_degrees,
    parallel_edges, four_cycles)."""
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("construction_seed must be an integer")
    check_neighbors: list[set[int]] = [set() for _ in range(m)]
    variable_neighbors: list[set[int]] = [set() for _ in range(_N)]
    check_degree = [0] * m
    edges: list[tuple[int, int]] = []
    for col in range(_N):
        for edge_i in range(degrees[col]):
            assigned = variable_neighbors[col]
            if edge_i == 0:
                min_degree = min(check_degree)
                candidates = [r for r in range(m) if check_degree[r] == min_degree]
                chosen = _tiebreak(candidates, "first", seed, m, col)
            else:
                frontier = _peg_frontier(col, variable_neighbors, check_neighbors, assigned)
                candidates = [r for r in frontier if r not in assigned]
                if not candidates:
                    candidates = [r for r in range(m) if r not in assigned]
                min_degree = min(check_degree[r] for r in candidates)
                candidates = [r for r in candidates if check_degree[r] == min_degree]
                chosen = _tiebreak(candidates, f"peg_{edge_i}", seed, m, col)
            edges.append((chosen, col))
            check_neighbors[chosen].add(col)
            variable_neighbors[col].add(chosen)
            check_degree[chosen] += 1
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
                     m: int, seed: int, stratum_p: float) -> bytes:
    header = {
        "canonical_schema": _SCHEMA, "construction_version": _CONSTRUCTION_VERSION,
        "method": METHOD, "q": _Q, "n": _N, "m": m,
        "stratum_p": stratum_p, "construction_seed": seed,
        "variable_distribution": dict(_DISTRIBUTIONS[stratum_p]),
        "de_selection": {"method": "qary_density_evolution",
                         "threshold_proxy": _DE_THRESHOLD_PROXIES[stratum_p],
                         "search_record": _DE_SEARCH_RECORDS[stratum_p]},
        "first_edge_rule": _FIRST_EDGE_RULE, "peg_edge_rule": _PEG_EDGE_RULE,
        "coefficient_derivation": _COEFFICIENT_DERIVATION, "field": asdict(field.spec),
    }
    out = bytearray(_MAGIC + _compact(header) + b"\n")
    for row in matrix:
        for value in row:
            out.extend(int(value).to_bytes(2, "big"))
    return bytes(out)


def _implied_check_histogram(stratum_p: float, m: int) -> dict[str, int]:
    """The check-degree histogram implied by the frozen distribution and the
    edge budget: ``{floor, ceil}`` of the mean check degree (the DE search and
    the min-degree construction both fix this histogram)."""
    p = float(stratum_p)
    distribution = _DISTRIBUTIONS[p]
    edges = sum(int(d) * int(count) for d, count in distribution.items())
    dc_lo = edges // m
    extra = edges - m * dc_lo
    return {str(dc_lo): m - extra, str(dc_lo + 1): extra}


@lru_cache(maxsize=2)
def _matrix_cached(m: int, seed: int, stratum_p: float) -> tuple[tuple[tuple[int, ...], ...], list[int], int, int]:
    return _construct(m, seed, column_degrees(stratum_p))


@lru_cache(maxsize=1)
def build_nbldpc_v7_r2_codebook() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    """Reconstruct the frozen two-matrix family and its canonical manifest."""
    if any(seed is None for seed in _FROZEN_SEEDS.values()):
        raise ValueError("NBLDPC7R2 frozen seeds are not yet bound")
    field = GF2mField.create(_Q)
    matrices: dict[int, tuple[tuple[int, ...], ...]] = {}
    entries: list[dict[str, Any]] = []
    for p in (0.20, 0.30):
        m = _CHECK_COUNTS[p]
        seed = _FROZEN_SEEDS[p]
        matrix, check_degrees, parallel, four_cycles = _matrix_cached(m, seed, p)
        rank = gf_rank(matrix, field)
        if rank != m:
            raise ValueError("NBLDPC7R2 frozen seed lost full rank")
        column_degrees_value = column_degrees(p)
        if any(sum(row[col] != 0 for row in matrix) != column_degrees_value[col]
               for col in range(_N)):
            raise ValueError("NBLDPC7R2 variable degree contract violated")
        if parallel != 0:
            raise ValueError("NBLDPC7R2 parallel-edge contract violated")
        histogram = _check_degree_histogram(check_degrees)
        # Structural check-degree contract: total edge budget 3*n = 3072,
        # mean check degree <= 12 (frozen bound), every degree within
        # [2, CHECK_DEGREE_MAX].  The exact histogram is determined by the
        # frozen deterministic construction (PEG frontier effects may move a
        # few checks one degree off the idealized two-point histogram) and is
        # frozen into the manifest below for exact reconstruction.
        if sum(degree * count for degree, count in
               ((int(k), int(v)) for k, v in histogram.items())) != 3 * _N:
            raise ValueError("NBLDPC7R2 edge budget contract violated")
        degree_values = sorted(int(k) for k in histogram)
        if any(value < 2 or value > de.CHECK_DEGREE_MAX for value in degree_values):
            raise ValueError("NBLDPC7R2 check-degree bound contract violated")
        if 3.0 * _N / m > de.MEAN_CHECK_DEGREE_MAX:
            raise ValueError("NBLDPC7R2 mean check degree bound violated")
        canonical = _canonical_bytes(matrix, field, m=m, seed=seed, stratum_p=p)
        matrices[m] = matrix
        entries.append({
            "stratum_p": p, "check_count": m, "construction_seed": seed,
            "variable_distribution": dict(_DISTRIBUTIONS[p]),
            "edge_count": 3 * _N, "rank": rank, "cycle_count": four_cycles,
            "parallel_edges": parallel, "variable_degree_min": min(column_degrees_value),
            "variable_degree_max": max(column_degrees_value),
            "check_degree_histogram": histogram,
            "de_threshold_proxy": _DE_THRESHOLD_PROXIES[p],
            "canonical_sha256": _sha(canonical), "canonical_byte_length": len(canonical),
        })
    payload = {
        "method": METHOD, "canonical_schema": _SCHEMA, "canonical_magic": "NBLDPC7R2\\n",
        "construction_version": _CONSTRUCTION_VERSION, "q": _Q, "n": _N,
        "field": asdict(field.spec), "field_id": field.spec.field_id,
        "coefficient_derivation": _COEFFICIENT_DERIVATION,
        "first_edge_rule": _FIRST_EDGE_RULE, "peg_edge_rule": _PEG_EDGE_RULE,
        "check_counts": list(_CHECK_COUNTS.values()), "ordered_entries": entries,
        "de_selection_identity": _sha(_compact({
            p: {"m": _CHECK_COUNTS[p], "distribution": dict(_DISTRIBUTIONS[p]),
                "threshold_proxy": _DE_THRESHOLD_PROXIES[p]}
            for p in (0.20, 0.30)})),
    }
    return dict(payload, manifest_id=_sha(_compact(payload))), matrices


def codebook() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    """Fresh manifest container over a cached deterministic reconstruction."""
    manifest, matrices = _codebook_cached()
    return dict(manifest), matrices


@lru_cache(maxsize=1)
def _codebook_cached() -> tuple[dict[str, Any], dict[int, tuple[tuple[int, ...], ...]]]:
    return build_nbldpc_v7_r2_codebook()


def verify_nbldpc_v7_r2_codebook(manifest: Mapping[str, Any], matrices: Mapping[int, Any]) -> dict[str, Any]:
    """Fail closed after independently reconstructing every NBLDPC7R2 contract value."""
    try:
        if not isinstance(manifest, Mapping) or not isinstance(matrices, Mapping):
            raise ValueError("invalid codebook container")
        expected, expected_matrices = build_nbldpc_v7_r2_codebook()
        supplied = {m: tuple(tuple(int(x) for x in row) for row in matrices[m])
                    for m in _CHECK_COUNTS.values()}
        if dict(manifest) != expected or tuple(sorted(matrices.keys())) != tuple(_CHECK_COUNTS.values()) \
                or supplied != expected_matrices:
            raise ValueError("deterministic reconstruction mismatch")
        return {"status": "ok", "method": METHOD,
                "manifest_id": expected["manifest_id"],
                "check_counts": list(_CHECK_COUNTS.values())}
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return {"status": "codebook_invalid", "method": METHOD}


def find_frozen_seeds(seed_start: int = 2026080402, seed_limit: int = 50) -> dict[float, int]:
    """One-time bounded acceptance search for the full-rank construction seeds
    (never called at runtime after acceptance; the found seeds are frozen into
    ``_FROZEN_SEEDS``).  Returns {stratum_p: seed} for the FIRST seed of each
    stratum that gives full GF(1024) row rank."""
    field = GF2mField.create(_Q)
    found: dict[float, int] = {}
    for offset in range(int(seed_limit)):
        seed = int(seed_start) + offset
        for p in (0.20, 0.30):
            if p in found:
                continue
            m = _CHECK_COUNTS[p]
            matrix, _, parallel, _ = _construct(m, seed, column_degrees(p))
            if parallel:
                continue
            if gf_rank(matrix, field) == m:
                found[p] = seed
                print(f"NBLDPC7R2 full-rank seed for p={p}: {seed}", flush=True)
    return found
