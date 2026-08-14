"""V13 R3 code-only candidate — ``nbldpc_v13_r3_code_v1``.

Frozen by the 2026-08-14 amendment (decision-log entry): the ONLY change
versus the frozen V7 R1A baseline is one finite graph/rate property — the
degenerate frozen graph (85 disconnected 2-check components, Tanner girth 4,
per-component d_min 3) is replaced by a CONNECTED SIMPLE check graph with the
same n=256 / m=170 / rate / check-degree profile (168 x 3 + 2 x 4) / all
degree-2 variables, no parallel edges and check-graph girth >= 4 (Tanner
girth >= 8).  The prior (QSC p=.20), the decoder interface (flooding
FFT-QSPA), check count 170, max_iter 100 and every other V13 contract are
unchanged.

Construction: deterministic seeded random stub pairing; the frozen
``construction_seed`` is 20260818 — the smallest integer >= 20260814 whose
graph passes the frozen gates (simple: no self-loops, no parallel edges;
connected; check-graph girth >= 4; rank(H) = 170).  Construction, girth
certification and the census are read-only, deterministic and reproducible.

Decoding reuses the verified flooding mirror from the diagnostics module
(:func:`comparison_bench...nonbinary_v13_diagnostics._hooked_decode_flooding`),
whose element-for-element equivalence to the frozen V7 R1A decoder is proven
by the D03 hook-equivalence tests; only the matrix and its canonical manifest
differ.  No frozen V7 source is modified.
"""
from __future__ import annotations

import hashlib
import json
from itertools import count
from typing import Any, Mapping

import numpy as np

from .nonbinary_field import GF2mField
from .nonbinary_qspa import (_declared_dense_bytes, _symbols, qsc_symbol_priors)
from .nonbinary_v13_diagnostics import (_hooked_decode_flooding, _matrix_edges,
                                        _telemetry_summary)

R3_METHOD = "nbldpc_v13_r3_code_v1"
Q, N, M = 1024, 256, 170
P = 0.20
MAX_ITER = 100
SEED_SEARCH_START = 20260814
FROZEN_SEED = 20260818
CHECK_DEGREES = {3: 168, 4: 2}
CHECK_GRAPH_GIRTH_GATE = 4  # Tanner girth gate = 8


def _compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _check_graph_from_seed(seed: int) -> set[tuple[int, int]] | None:
    """Deterministic stub pairing -> simple check graph or None (reject)."""
    rng = np.random.default_rng(seed)
    stubs: list[int] = []
    for node in range(M):
        degree = 4 if node in (0, 1) else 3
        stubs.extend([node] * degree)
    rng.shuffle(stubs)
    edges: set[tuple[int, int]] = set()
    for a, b in zip(stubs[0::2], stubs[1::2]):
        if a == b:
            return None
        if a > b:
            a, b = b, a
        if (a, b) in edges:
            return None
        edges.add((a, b))
    return edges


def _graph_census(edges: set[tuple[int, int]]) -> dict[str, Any]:
    adj: dict[int, list[int]] = {i: [] for i in range(M)}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    seen: set[int] = set()
    components: list[int] = []
    for start in range(M):
        if start in seen:
            continue
        size = 0
        stack = [start]
        seen.add(start)
        while stack:
            u = stack.pop()
            size += 1
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        components.append(size)
    girth: int | None = None
    for start in range(M):
        depth = {start: 0}
        parent = {start: -1}
        queue = [start]
        while queue:
            u = queue.pop(0)
            for v in adj[u]:
                if v not in depth:
                    depth[v] = depth[u] + 1
                    parent[v] = u
                    queue.append(v)
                elif v != parent[u] and depth[v] <= depth[u]:
                    cycle = depth[u] + depth[v] + 1
                    if girth is None or cycle < girth:
                        girth = cycle
    return {"edge_count": len(edges), "component_count": len(components),
            "component_sizes": sorted(components, reverse=True),
            "connected": components == [M],
            "check_graph_girth": girth}


def _matrix_from_edges(edges: set[tuple[int, int]]) -> tuple[tuple[int, ...], ...]:
    """170 x 256 matrix: variable ``col`` connects its check pair with a
    deterministic nonzero GF(1024) coefficient (frozen rule)."""
    edges_sorted = sorted(edges)
    col_of: dict[tuple[int, int], int] = {}
    matrix = [[0] * N for _ in range(M)]
    for col, (a, b) in enumerate(edges_sorted):
        col_of[(a, b)] = col
        # deterministic frozen coefficient rule: nonzero and injective per row
        coeff_a = ((a + 1) * (col + 1) * 7) % 1023 + 1
        coeff_b = ((b + 1) * (col + 1) * 11) % 1023 + 1
        matrix[a][col] = coeff_a
        matrix[b][col] = coeff_b
    return tuple(tuple(row) for row in matrix)


def _rank_gf1024(matrix: Any, field: GF2mField) -> int:
    """Row rank of a 170 x 256 GF(1024) matrix (Gaussian elimination)."""
    rows = [list(row) for row in matrix]
    rank = 0
    pivot_col = 0
    while rank < len(rows) and pivot_col < len(rows[0]):
        pivot = None
        for r in range(rank, len(rows)):
            if rows[r][pivot_col] != 0:
                pivot = r
                break
        if pivot is None:
            pivot_col += 1
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inv = field.inverse(rows[rank][pivot_col])
        rows[rank] = [field.mul(v, inv) for v in rows[rank]]
        for r in range(len(rows)):
            if r != rank and rows[r][pivot_col] != 0:
                factor = rows[r][pivot_col]
                rows[r] = [field.add(a, field.mul(factor, b))
                           for a, b in zip(rows[r], rows[rank])]
        rank += 1
        pivot_col += 1
    return rank


def _find_frozen_graph() -> tuple[int, set[tuple[int, int]], dict[str, Any]]:
    """Search seeds upward from SEED_SEARCH_START; freeze the FIRST graph that
    passes every gate (simple, connected, check-girth >= 4)."""
    for seed in count(SEED_SEARCH_START):
        edges = _check_graph_from_seed(seed)
        if edges is None:
            continue
        census = _graph_census(edges)
        if not census["connected"] or census["check_graph_girth"] is None \
                or census["check_graph_girth"] < CHECK_GRAPH_GIRTH_GATE:
            continue
        return seed, edges, census
    raise RuntimeError("unreachable")  # count() is unbounded


def build_r3_codebook() -> tuple[dict[str, Any], tuple[tuple[int, ...], ...]]:
    """Deterministically construct the frozen R3 codebook and its canonical
    manifest.  Fails closed unless every frozen gate holds."""
    seed, edges, census = _find_frozen_graph()
    if seed != FROZEN_SEED:
        raise ValueError(f"frozen construction seed drift: {seed}")
    matrix = _matrix_from_edges(edges)
    field = GF2mField.create(Q)
    rank = _rank_gf1024(matrix, field)
    if rank != M:
        raise ValueError(f"R3 matrix rank {rank} != {M}")
    check_deg: dict[str, int] = {}
    for row in matrix:
        key = str(sum(1 for v in row if v))
        check_deg[key] = check_deg.get(key, 0) + 1
    var_deg: dict[str, int] = {}
    for col in range(N):
        key = str(sum(1 for r in range(M) if matrix[r][col]))
        var_deg[key] = var_deg.get(key, 0) + 1
    if {int(k): v for k, v in check_deg.items()} != CHECK_DEGREES \
            or var_deg != {"2": N}:
        raise ValueError("R3 degree profile drift")
    canonical = _compact({"method": R3_METHOD, "q": Q, "n": N, "m": M,
                          "construction_seed": seed, "matrix": matrix})
    manifest = {
        "canonical_schema": "NBLDPC13R3",
        "method": R3_METHOD, "q": Q, "n": N, "m": M,
        "construction_seed": seed,
        "seed_search_start": SEED_SEARCH_START,
        "check_degree_histogram": check_deg,
        "variable_degree_histogram": var_deg,
        "edge_count": census["edge_count"],
        "tanner_girth": 2 * census["check_graph_girth"],
        "check_graph_girth": census["check_graph_girth"],
        "component_count": census["component_count"],
        "rank": rank,
        "canonical_sha256": hashlib.sha256(canonical).hexdigest(),
    }
    return manifest, matrix


def verify_r3_codebook(manifest: Mapping[str, Any], matrix: Any) -> dict[str, Any]:
    """Read-only reconstruction check: the supplied codebook must equal the
    frozen construction field for field."""
    expected_manifest, expected_matrix = build_r3_codebook()
    if dict(manifest) != expected_manifest:
        return {"status": "failed", "reason": "manifest mismatch",
                "method": R3_METHOD}
    if tuple(tuple(int(v) for v in row) for row in matrix) != expected_matrix:
        return {"status": "failed", "reason": "matrix mismatch",
                "method": R3_METHOD}
    return {"status": "ok", "method": R3_METHOD,
            "manifest_id": expected_manifest["canonical_sha256"]}


def decode_r3_frame(bob_symbols: Any, syndrome: Any, manifest: Mapping[str, Any],
                    matrices: Any, *, check_count: int = M, p: float = P,
                    max_iter: int = MAX_ITER, hook: bool = True) -> dict[str, Any]:
    """Decode one n=256 frame with the R3 candidate (flooding FFT-QSPA,
    QSC p prior, same math as the frozen V7 R1A decoder — only the graph
    differs).  ``hook=True`` returns the D03 aggregate telemetry alongside
    the original result (element-for-element equivalence guaranteed by the
    shared verified mirror).  Public inputs only; Alice truth is never passed
    here (the caller computes the disclosed syndrome and the post-decode
    exact check offline)."""
    expected, expected_matrix = build_r3_codebook()
    if dict(manifest) != expected:
        raise ValueError("R3 manifest binding mismatch")
    if tuple(tuple(int(v) for v in row) for row in matrices) != expected_matrix:
        raise ValueError("R3 matrix binding mismatch")
    field = GF2mField.create(Q)
    bob = _symbols(bob_symbols, Q, expected=N)
    disclosed = _symbols(syndrome, Q, expected=check_count)
    if len(expected_matrix) != check_count:
        raise ValueError("check count mismatch")
    priors = qsc_symbol_priors(bob, Q, p)
    checks, variables = _matrix_edges(expected_matrix)
    edge_count = sum(map(len, checks))
    declared = _declared_dense_bytes(N, edge_count, Q)
    codebook_id = expected["canonical_sha256"]
    result, records, decoded_words = _hooked_decode_flooding(
        bob, disclosed, expected_matrix, checks, variables, priors, field,
        check_count, codebook_id, declared, max_iter=int(max_iter))
    if not hook:
        return {"hook": False, "result": result, "telemetry": None}
    return {"hook": True, "result": result,
            "telemetry": _telemetry_summary(records, result, decoded_words)}
