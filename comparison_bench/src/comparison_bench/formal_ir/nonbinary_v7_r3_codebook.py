"""NBLDPC7 R3: deterministic GF(32)xGF(32) multilevel codebooks for
``nbldpc_formal_v7_r3_gf32x2``.

Each natural 10-bit symbol is reversibly split into high and low 5-bit words
(``high = x >> 5``, ``low = x & 31``; ``join = (high << 5) | low``); the
mapping is frozen and exhaustively round-tripped for all 1024 symbols.  Two
GF(32) codes of n=1024 per stratum are built with the accepted NBLDPC7R2 PEG
discipline: layer 0 decodes the high words first; layer 1 decodes the low
words with priors restricted to Bob data, public model data and the verified
layer-0 output (see ``nonbinary_v7_r3_long``).

Per-stratum per-layer check-count freeze (V7-30 implementation note, exact
arithmetic): the accepted R2 check-count freeze (V7-20) applied per layer
with q=32 and 5-bit GF(32) checks -- ``m0 = m1 = ceil(1.15*H_32(p)/5 * 1024)``
with ``H_32(p) = h2(p) + p*log2(31)``:

| stratum | H_32(p)            | 1.15*H_32(p)/5*1024 | m0 = m1 | rate  | syndrome 5*(m0+m1) | bits/symbol (excl. tag) |
|---------|--------------------|---------------------|---------|-------|--------------------|-------------------------|
| p=.20   | 1.7127673569647375 | 403.39096791229485  | 404     | 0.605 | 4040               | 3.945                   |
| p=.30   | 2.367549792346755  | 557.6053270935077   | 558     | 0.455 | 5580               | 5.449                   |

Both strata stay below the frozen 8.75 bits/symbol ceiling.  The two layers
are symmetric because the natural high/low split exposes each 5-bit word to
the same frozen frame-error model; the layer rates 0.605 / 0.455 sit below
the GF(32) q-ary-symmetric capacity (3.287 / 2.632 bits per 5-bit word), so
the conditional layer model receives a genuine capacity test and the
sacrificed canary decides the empirical outcome.

Construction contract (frozen, no unbounded search after acceptance):

- Columns are processed in ascending order ``0..n-1``.  Every column receives
  exactly 3 incident edges (the frozen regular degree-3 ensemble, per layer).
- The first edge of a column chooses a minimum-degree check; ties are broken
  by a domain-separated SHA256 digest.
- Every later edge uses breadth-first PEG expansion rooted at the column's
  already-assigned check neighbours (maximum-depth frontier), then minimum
  check degree, then the same SHA256 tie-break.  Parallel edges are
  forbidden.
- Nonzero GF(32) coefficients are derived independently from
  domain-separated SHA256 over ``(seed, row, col)`` and reduced to ``1..31``.
- Full GF(32) row rank is required per layer; the frozen seeds below were
  found by a one-time bounded acceptance search (layer 1's seed is the first
  full-rank candidate at or after the seed following layer 0's seed) and are
  never re-searched at runtime.

Canonical bytes are ``NBLDPC7R3`` magic + compact header (schema,
construction version, q/n/m, field identity, stratum, layer, seeds, edge
rules, coefficient derivation, split mapping) + row-major 16-bit big-endian
coefficients.  The manifest records per-stratum per-layer SHA256, GF rank,
edge count, degree histograms, parallel-edge count, four-cycle count and the
full reconstruction parameters.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from functools import lru_cache
from typing import Any, Mapping

from .nonbinary_codebook import gf_rank
from .nonbinary_field import GF2mField

METHOD = "nbldpc_formal_v7_r3_gf32x2"
_SCHEMA = "NBLDPC7R3"
_MAGIC = b"NBLDPC7R3\n"
_CONSTRUCTION_VERSION = 1
_Q, _N = 32, 1024
# Frozen V7-30 per-stratum per-layer check-count freeze (exact arithmetic,
# see module docstring): m0 = m1 = ceil(1.15*H_32(p)/5*1024).
_CHECK_COUNTS = {0.20: 404, 0.30: 558}
# Frozen variable ensemble per layer: regular degree 3 (the frozen R2 DE
# selection), exactly 3*n = 3072 edges per layer matrix.
_DISTRIBUTIONS = {0.20: {"3": 1024}, 0.30: {"3": 1024}}
# Frozen one-time acceptance search results: per stratum the first full-rank
# construction seed for layer 0 and the next full-rank seed for layer 1.
# Search record (V7-30, one-time bounded acceptance search, never re-run):
# layer 0 -> 202608050001 (first candidate), layer 1 -> 202608050002 (first
# candidate after layer 0), for both strata (the matrices differ per stratum
# through the frozen check count m).
_FROZEN_SEEDS = {0.20: {0: 202608050001, 1: 202608050002},
                 0.30: {0: 202608050001, 1: 202608050002}}
_LAYER_LABELS = {0: "high", 1: "low"}
_FIRST_EDGE_RULE = "min_check_degree_then_domain_separated_sha256_tiebreak"
_PEG_EDGE_RULE = ("bfs_peg_max_local_girth_rooted_at_assigned_check_neighbors_"
                  "then_min_degree_then_domain_separated_sha256_tiebreak")
_COEFFICIENT_DERIVATION = "1 + int.from_bytes(SHA256(ASCII('NBLDPC7R3|coef|{seed}|{row}|{col}')), 'big') % 31"
_SPLIT_MAPPING = "natural: high = symbol >> 5, low = symbol & 31; join = (high << 5) | low"


def _compact(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def _coefficient(seed: int, row: int, col: int) -> int:
    text = f"NBLDPC7R3|coef|{seed}|{row}|{col}".encode("ascii")
    return 1 + int.from_bytes(hashlib.sha256(text).digest(), "big") % 31


def _tiebreak(candidates: list[int], label: str, seed: int, m: int, col: int) -> int:
    """Domain-separated SHA256 tie-break: the lexicographically smallest digest wins."""
    best, best_digest = None, None
    for candidate in candidates:
        domain = f"NBLDPC7R3|{label}|{seed}|{m}|{col}|{candidate}".encode("ascii")
        digest = hashlib.sha256(domain).digest()
        if best_digest is None or digest < best_digest:
            best, best_digest = candidate, digest
    assert best is not None
    return best


def split_symbol(symbol: Any) -> tuple[int, int]:
    """Frozen reversible natural split: ``(high, low) = (x >> 5, x & 31)``."""
    if isinstance(symbol, bool) or not isinstance(symbol, int):
        raise ValueError("symbol must be an integer")
    value = int(symbol)
    if not 0 <= value < 1024:
        raise ValueError("symbol outside the 10-bit natural domain")
    return value >> 5, value & 31


def join_symbol(high: Any, low: Any) -> int:
    """Exact inverse of :func:`split_symbol` (``(high << 5) | low``)."""
    high_value, low_value = int(high), int(low)
    if not 0 <= high_value < 32 or not 0 <= low_value < 32:
        raise ValueError("layer word outside the GF(32) domain")
    return (high_value << 5) | low_value


def split_vector(symbols: Any) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Split a 10-bit symbol vector into (high_words, low_words) tuples."""
    values = tuple(int(value) for value in symbols)
    if any(not 0 <= value < 1024 for value in values):
        raise ValueError("symbol outside the 10-bit natural domain")
    return tuple(value >> 5 for value in values), tuple(value & 31 for value in values)


def join_vector(high_words: Any, low_words: Any) -> tuple[int, ...]:
    """Reconstruct the 10-bit symbols from parallel high/low word tuples."""
    high = tuple(int(value) for value in high_words)
    low = tuple(int(value) for value in low_words)
    if len(high) != len(low) or any(not 0 <= value < 32 for value in high + low):
        raise ValueError("layer words must be equal-length GF(32) vectors")
    return tuple((h << 5) | l for h, l in zip(high, low))


def column_degrees(stratum_p: float) -> list[int]:
    """Deterministic ascending-block assignment of the frozen distribution."""
    p = float(stratum_p)
    if p not in _DISTRIBUTIONS:
        raise ValueError("unknown NBLDPC7R3 stratum")
    distribution = _DISTRIBUTIONS[p]
    degrees: list[int] = []
    for key in sorted(distribution, key=int):
        degree = int(key)
        count = int(distribution[key])
        if count <= 0 or sum(int(v) for v in distribution.values()) != _N:
            raise ValueError("NBLDPC7R3 distribution contract violated")
        degrees.extend([degree] * count)
    if len(degrees) != _N:
        raise ValueError("NBLDPC7R3 column-degree count contract violated")
    return degrees


def _peg_frontier(column: int, variable_neighbors: list[set[int]],
                  check_neighbors: list[set[int]], first_checks: set[int]) -> set[int]:
    """Maximum-depth frontier of the BFS-PEG tree rooted at the variable's
    already-assigned check neighbours (the accepted R2 expansion)."""
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
                     m: int, seed: int, stratum_p: float, layer: int) -> bytes:
    header = {
        "canonical_schema": _SCHEMA, "construction_version": _CONSTRUCTION_VERSION,
        "method": METHOD, "q": _Q, "n": _N, "m": m,
        "stratum_p": stratum_p, "layer": layer, "layer_label": _LAYER_LABELS[layer],
        "construction_seed": seed,
        "variable_distribution": dict(_DISTRIBUTIONS[stratum_p]),
        "split_mapping": _SPLIT_MAPPING,
        "first_edge_rule": _FIRST_EDGE_RULE, "peg_edge_rule": _PEG_EDGE_RULE,
        "coefficient_derivation": _COEFFICIENT_DERIVATION, "field": asdict(field.spec),
    }
    out = bytearray(_MAGIC + _compact(header) + b"\n")
    for row in matrix:
        for value in row:
            out.extend(int(value).to_bytes(2, "big"))
    return bytes(out)


@lru_cache(maxsize=8)
def _matrix_cached(m: int, seed: int, stratum_p: float) -> tuple[tuple[tuple[int, ...], ...], list[int], int, int]:
    return _construct(m, seed, column_degrees(stratum_p))


@lru_cache(maxsize=8)
def _rank_cached(m: int, seed: int, stratum_p: float) -> int:
    # Deterministic rank of the frozen construction; cached so per-frame
    # codebook verification does not re-run Gaussian elimination.  The result
    # is a pure function of (m, seed, stratum_p).
    matrix, _, _, _ = _matrix_cached(m, seed, stratum_p)
    return gf_rank(matrix, GF2mField.create(_Q))


@lru_cache(maxsize=1)
def build_nbldpc_v7_r3_codebook() -> tuple[dict[str, Any], dict[tuple[int, int], tuple[tuple[int, ...], ...]]]:
    """Reconstruct the frozen four-matrix multilevel family and its canonical
    manifest (per stratum, two GF(32) matrices: layer 0 high, layer 1 low)."""
    if any(seed is None for seeds in _FROZEN_SEEDS.values() for seed in seeds.values()):
        raise ValueError("NBLDPC7R3 frozen seeds are not yet bound")
    field = GF2mField.create(_Q)
    matrices: dict[tuple[int, int], tuple[tuple[int, ...], ...]] = {}
    entries: list[dict[str, Any]] = []
    for p in (0.20, 0.30):
        m = _CHECK_COUNTS[p]
        column_degrees_value = column_degrees(p)
        entry: dict[str, Any] = {"stratum_p": p, "check_count": m, "check_count_total": 2 * m,
                                 "variable_distribution": dict(_DISTRIBUTIONS[p]),
                                 "variable_degree_min": min(column_degrees_value),
                                 "variable_degree_max": max(column_degrees_value)}
        for layer in (0, 1):
            seed = _FROZEN_SEEDS[p][layer]
            matrix, check_degrees, parallel, four_cycles = _matrix_cached(m, seed, p)
            rank = _rank_cached(m, seed, p)
            if rank != m:
                raise ValueError("NBLDPC7R3 frozen seed lost full rank")
            if any(sum(row[col] != 0 for row in matrix) != column_degrees_value[col]
                   for col in range(_N)):
                raise ValueError("NBLDPC7R3 variable degree contract violated")
            if parallel != 0:
                raise ValueError("NBLDPC7R3 parallel-edge contract violated")
            histogram = _check_degree_histogram(check_degrees)
            if sum(degree * count for degree, count in
                   ((int(k), int(v)) for k, v in histogram.items())) != 3 * _N:
                raise ValueError("NBLDPC7R3 edge budget contract violated")
            degree_values = sorted(int(k) for k in histogram)
            if any(value < 2 for value in degree_values) or 3.0 * _N / m > 12.0:
                raise ValueError("NBLDPC7R3 check-degree bound contract violated")
            canonical = _canonical_bytes(matrix, field, m=m, seed=seed, stratum_p=p, layer=layer)
            matrices[(m, layer)] = matrix
            entry[f"construction_seed_{layer}"] = seed
            entry[f"rank_{layer}"] = rank
            entry[f"cycle_count_{layer}"] = four_cycles
            entry[f"parallel_edges_{layer}"] = parallel
            entry[f"check_degree_histogram_{layer}"] = histogram
            entry[f"canonical_sha256_{layer}"] = _sha(canonical)
            entry[f"canonical_byte_length_{layer}"] = len(canonical)
        entry["edge_count"] = 3 * _N
        entry["syndrome_disclosure_bits_layer"] = 5 * m
        entry["syndrome_disclosure_bits_total"] = 5 * 2 * m
        entries.append(entry)
    payload = {
        "method": METHOD, "canonical_schema": _SCHEMA, "canonical_magic": "NBLDPC7R3\\n",
        "construction_version": _CONSTRUCTION_VERSION, "q": _Q, "n": _N,
        "field": asdict(field.spec), "field_id": field.spec.field_id,
        "split_mapping": _SPLIT_MAPPING,
        "coefficient_derivation": _COEFFICIENT_DERIVATION,
        "first_edge_rule": _FIRST_EDGE_RULE, "peg_edge_rule": _PEG_EDGE_RULE,
        "check_counts": list(_CHECK_COUNTS.values()), "ordered_entries": entries,
        "split_roundtrip_sha256": _sha(_compact({"high": list(range(32)), "low": list(range(32))})),
    }
    return dict(payload, manifest_id=_sha(_compact(payload))), matrices


def codebook() -> tuple[dict[str, Any], dict[tuple[int, int], tuple[tuple[int, ...], ...]]]:
    """Fresh manifest container over a cached deterministic reconstruction."""
    manifest, matrices = _codebook_cached()
    return dict(manifest), matrices


@lru_cache(maxsize=1)
def _codebook_cached() -> tuple[dict[str, Any], dict[tuple[int, int], tuple[tuple[int, ...], ...]]]:
    return build_nbldpc_v7_r3_codebook()


def verify_nbldpc_v7_r3_codebook(manifest: Mapping[str, Any], matrices: Mapping[Any, Any]) -> dict[str, Any]:
    """Fail closed after independently reconstructing every NBLDPC7R3 contract value."""
    try:
        if not isinstance(manifest, Mapping) or not isinstance(matrices, Mapping):
            raise ValueError("invalid codebook container")
        expected, expected_matrices = build_nbldpc_v7_r3_codebook()
        expected_keys = {(m, layer) for p, m in _CHECK_COUNTS.items() for layer in (0, 1)}
        supplied = {(int(m), int(layer)): tuple(tuple(int(x) for x in row) for row in matrices[(m, layer)])
                    for m, layer in expected_keys}
        if dict(manifest) != expected or tuple(sorted(matrices.keys())) != tuple(sorted(expected_keys)) \
                or supplied != expected_matrices:
            raise ValueError("deterministic reconstruction mismatch")
        return {"status": "ok", "method": METHOD,
                "manifest_id": expected["manifest_id"],
                "check_count_total": sum(_CHECK_COUNTS.values())}
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return {"status": "codebook_invalid", "method": METHOD}


def find_frozen_seeds(seed_start: int = 202608050001, seed_limit: int = 50) -> dict[float, dict[int, int]]:
    """One-time bounded acceptance search for the full-rank construction seeds
    (never called at runtime after acceptance; the found seeds are frozen into
    ``_FROZEN_SEEDS``).  Per stratum, layer 0 receives the FIRST seed with full
    GF(32) row rank and layer 1 the next seed with full rank.  Returns
    ``{stratum_p: {layer: seed}}``."""
    field = GF2mField.create(_Q)
    found: dict[float, dict[int, int]] = {}
    for p in (0.20, 0.30):
        m = _CHECK_COUNTS[p]
        per_layer: dict[int, int] = {}
        for layer in (0, 1):
            for offset in range(int(seed_limit)):
                seed = int(seed_start) + offset
                if seed in per_layer.values() or any(seed in values for values in found.values()):
                    continue
                matrix, _, parallel, _ = _matrix_cached(m, seed, p)
                if parallel:
                    continue
                if gf_rank(matrix, field) == m:
                    per_layer[layer] = seed
                    print(f"NBLDPC7R3 full-rank seed for p={p} layer={layer}: {seed}", flush=True)
                    break
            if layer not in per_layer:
                raise ValueError("NBLDPC7R3 acceptance search exhausted the seed budget")
        found[p] = per_layer
    return found
