"""V10 deterministic irregular PEG codebook construction
(``formal-nonbinary-ldpc-v10-de-peg-fftqspa``, additive layer; frozen
semantics per design section 9).

Contents:

- ``node_view_counts``: edge-view lambda -> integer node-view degree counts
  (``L_d = (lambda_d/d) / sum_j(lambda_j/j)``, largest-remainder adjustment
  to exactly ``n``);
- ``check_degree_counts``: concentrated rho -> integer check degree counts
  (largest-remainder adjustment to exactly ``m``);
- ``socket_consistency``: asserts ``sum count_d*d == sum count_j*j``
  (mismatch -> blocker);
- ``_reconcile_check_counts``: deterministic check-side socket
  reconciliation (2026-09-20 fix).  The variable-side realization from
  ``node_view_counts`` is kept as specified; the CHECK-side allocation
  from ``check_degree_counts`` (independent largest-remainder rounding,
  off by exactly 1 edge for some lambda/m/n combos) is adjusted to hit
  the exact variable-side socket total while keeping ``m`` unchanged.
  Rule: delta 0 -> input returned unchanged (already-consistent inputs
  are bit-identical); else count transfer within the existing support
  (move ``|delta|/gap`` checks between the extreme degrees when
  divisible, preserving the concentrated adjacent-degree shape);
  fallback single highest-degree check shift by ``delta`` (e.g.
  single-degree rho).  Donor shortage or a resulting degree < 2 raises
  ``ValueError`` — the ``socket_consistency`` guard still refuses
  genuinely non-representable requests;
- ``peg_construct``: deterministic irregular PEG over GF(1024).  Variable
  sockets are placed in node order; each socket picks the free check that
  maximizes the local girth (BFS distance from the variable), tie-break 1
  maximizes an ACE-like score (sum of (degree - 2) over the cycle variable
  nodes), tie-break 2 is a seeded-RNG deterministic pick
  (``numpy.random.default_rng(common.v10_seed(
  f"peg_tie:{seed}:v:{v}:s:{socket}"))`` permutation over the sorted tied
  candidates; first element wins — deterministic and unbiased, no hash layer).
  PEG priority (constructor fix, 2026-09-20): (1) candidates unreachable
  from the variable (cycle-free, new-component merge) are ALWAYS preferred
  over reachable (cycle-closing) candidates; (2) among reachable candidates,
  maximize BFS depth; (3) deterministic tie-break by largest free check
  degree, then max ACE score (reachable group only), then the seeded-RNG
  pick over the sorted tied list (exact policy, in this order).
  First-edge placement (no path yet) prefers the largest free degree, then the
  seeded tie-break.  Parallel edges are forbidden by construction (a check
  already adjacent to ``v`` is never re-selected).
  ``max_trials`` is a best-of-N cap: each trial derives its tie-break seed
  as ``seed + trial`` (trial 1-based: ``seed + (trial - 1)``), every trial
  runs to completion, and the kept graph is the successful trial with
  minimum ``four_cycles`` (ties -> lowest trial index); an early stop fires
  only on ``four_cycles == 0`` (unbeatable).  Failure trials count within
  the same cap; ``max_trials`` exhausted with no success -> frozen
  failure (``status == "frozen_failure"``).  Edge labels are uniform nonzero
  GF(1024) samples from a frozen seed (validated via GF2mField).
  ``min_girth`` is the true minimum cycle length over placed edges;
  unreachable (cycle-free) placements are never girth candidates; a graph
  with no cycle at all reports ``min_girth=None`` (sentinel meaning
  "acyclic — no cycle length exists").
- verification helpers: ``rank_GF1024`` (Gaussian elimination over GF(q)),
  ``syndrome_round_trip``, ``sparse_to_dense`` and ``peg_manifest``
  (construction parameters only).

Imports: standard library, numpy, ``nonbinary_v10_common`` and the accepted
field tables only.  Never imports any V8/V9 module.
"""
from __future__ import annotations

import math
from collections import deque
from numbers import Integral
from typing import Any, Mapping, Sequence

import numpy as np

from . import nonbinary_v10_common as common
from .nonbinary_field import GF2mField

__all__ = [
    "node_view_counts",
    "check_degree_counts",
    "socket_consistency",
    "peg_construct",
    "rank_GF1024",
    "syndrome_round_trip",
    "sparse_to_dense",
    "peg_manifest",
]

#: Default construction field: GF(1024) (production q).
_PEG_Q = 1024


# --------------------------------------------------------------------------- #
# degree counts
# --------------------------------------------------------------------------- #


def _largest_remainder(proportions: Sequence[float], total: int) -> list[int]:
    """Integer counts summing exactly to ``total`` from fractional
    proportions (largest-remainder method; ties broken by index order)."""
    counts = [int(math.floor(float(prop) * total)) for prop in proportions]
    remainder = total - sum(counts)
    fractions = [float(prop) * total - int(math.floor(float(prop) * total))
                 for prop in proportions]
    order = sorted(range(len(proportions)), key=lambda index: (-fractions[index], index))
    for index in range(remainder):
        counts[order[index % len(order)]] += 1
    return counts


def node_view_counts(lambda_edge: Mapping[Any, Any], n: int) -> dict[int, int]:
    """Edge-view lambda -> integer node-view degree counts summing to exactly
    ``n``.  Uses the mechanical conversion ``L_d = (lambda_d/d) / sum_j
    (lambda_j/j)`` (never edge fractions as node proportions) with a
    largest-remainder adjustment."""
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) < 1:
        raise ValueError("n must be a positive integer")
    n = int(n)
    node_hist = common.edge_to_node_hist(lambda_edge)
    degrees = sorted(node_hist)
    proportions = [node_hist[degree] for degree in degrees]
    counts = _largest_remainder(proportions, n)
    return {degree: count for degree, count in zip(degrees, counts)}


def check_degree_counts(rho_edge: Mapping[Any, Any], m: int) -> dict[int, int]:
    """Concentrated rho -> integer check degree counts summing to exactly
    ``m`` (largest-remainder adjustment)."""
    if isinstance(m, bool) or not isinstance(m, Integral) or int(m) < 1:
        raise ValueError("m must be a positive integer")
    m = int(m)
    if not isinstance(rho_edge, Mapping) or not rho_edge:
        raise ValueError("rho_edge must be a non-empty mapping")
    total = 0.0
    for degree, weight in rho_edge.items():
        if isinstance(degree, bool) or not isinstance(degree, Integral) or int(degree) < 2:
            raise ValueError("rho_edge degrees must be integers >= 2")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) \
                or not math.isfinite(float(weight)) or float(weight) < 0.0:
            raise ValueError("rho_edge weights must be finite and non-negative")
        total += float(weight)
    if not math.isfinite(total) or abs(total - 1.0) > 1e-9:
        raise ValueError("rho_edge weights must sum to 1 within 1e-9")
    degrees = sorted(int(d) for d in rho_edge)
    proportions = [float(rho_edge[degree]) for degree in degrees]
    counts = _largest_remainder(proportions, m)
    return {degree: count for degree, count in zip(degrees, counts)}


def socket_consistency(node_counts: Mapping[Any, Any], check_counts: Mapping[Any, Any]) -> int:
    """Assert ``sum count_d*d == sum count_j*j`` (total edge sockets equal);
    returns the total edge count.  Mismatch raises ``ValueError``."""
    var_sockets = sum(int(degree) * int(count) for degree, count in node_counts.items())
    check_sockets = sum(int(degree) * int(count) for degree, count in check_counts.items())
    if var_sockets != check_sockets:
        raise ValueError(
            f"socket mismatch: variable sockets {var_sockets} != check sockets {check_sockets}")
    return var_sockets


def _reconcile_check_counts(check_counts: Mapping[Any, Any],
                            var_sockets: int) -> dict[int, int]:
    """Deterministic check-side socket reconciliation (2026-09-20 fix).

    Keeps the variable-side realization as specified and adjusts the
    CHECK-side allocation from :func:`check_degree_counts` (independent
    largest-remainder rounding, off by exactly 1 edge for some
    lambda/m/n combos, e.g. L-B 614 vs 615 and L-C 768 vs 769 at
    n=256/m=47) to hit exactly ``var_sockets`` total sockets while
    keeping the check count ``m`` unchanged.

    Rule (in order):
    1. ``delta = var_sockets - check_sockets``; ``delta == 0`` returns
       the input unchanged (already-consistent inputs are bit-identical).
    2. Count transfer within the existing support: with extreme degrees
       ``d_lo < d_hi`` and ``gap = d_hi - d_lo``, if ``delta`` is a
       multiple of ``gap``, move ``|delta| / gap`` checks from the donor
       extreme (``d_hi`` when ``delta < 0``, ``d_lo`` when ``delta > 0``)
       to the other extreme — this preserves the concentrated
       adjacent-degree support shape.
    3. Fallback single-check shift: change one check at the highest
       degree by ``delta`` (deterministic donor); used only when rule 2
       cannot apply (e.g. single-degree rho or indivisible delta).

    Donor shortage or a resulting check degree < 2 raises
    ``ValueError``; the :func:`socket_consistency` guard after this step
    still refuses genuinely non-representable requests (e.g.
    ``var_sockets < 2 * m``).
    """
    counts = {int(degree): int(count) for degree, count in check_counts.items()}
    total = sum(degree * count for degree, count in counts.items())
    delta = int(var_sockets) - total
    if delta == 0:
        return counts
    extremes = sorted(counts)
    d_lo, d_hi = extremes[0], extremes[-1]
    if d_hi != d_lo:
        gap = d_hi - d_lo
        if delta % gap == 0:
            need = abs(delta) // gap
            if delta < 0 and counts[d_hi] >= need:
                counts[d_hi] -= need
                counts[d_lo] += need
                return counts
            if delta > 0 and counts[d_lo] >= need:
                counts[d_lo] -= need
                counts[d_hi] += need
                return counts
    if counts[d_hi] < 1 or d_hi + delta < 2:
        raise ValueError(
            f"socket reconciliation impossible: variable sockets {int(var_sockets)} "
            f"vs check sockets {total} (delta {delta})")
    counts[d_hi] -= 1
    counts[d_hi + delta] = counts.get(d_hi + delta, 0) + 1
    if counts[d_hi] == 0:
        del counts[d_hi]
    return counts


# --------------------------------------------------------------------------- #
# GF(q) rank and syndrome helpers
# --------------------------------------------------------------------------- #


def rank_GF1024(field: GF2mField, matrix: Any) -> int:
    """Rank of a dense matrix over GF(q) by Gaussian elimination (RREF).

    Accepts a dense sequence of rows (sequence of symbol sequences); convert a
    sparse triple list with :func:`sparse_to_dense` first.  Deterministic.
    """
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    rows = [[int(value) for value in row] for row in matrix]
    if not rows:
        return 0
    q = field.q
    height, width = len(rows), len(rows[0])
    for row in rows:
        for value in row:
            field.mul(1, value)  # validates the symbol domain
    rank = 0
    for col in range(width):
        pivot = None
        for row_index in range(rank, height):
            if rows[row_index][col] != 0:
                pivot = row_index
                break
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        pivot_value = rows[rank][col]
        if pivot_value != 1:
            inverse = field.inverse(pivot_value)
            rows[rank] = [field.mul(value, inverse) for value in rows[rank]]
        for row_index in range(height):
            if row_index != rank and rows[row_index][col] != 0:
                factor = rows[row_index][col]
                pivot_row = rows[rank]
                rows[row_index] = [field.add(a, field.mul(factor, b))
                                   for a, b in zip(rows[row_index], pivot_row)]
        rank += 1
        if rank == height:
            break
    return rank


def sparse_to_dense(triples: Sequence[Sequence[int]], n: int, m: int,
                    field: GF2mField | None = None) -> np.ndarray:
    """Convert ``[(row, col, coeff), ...]`` to a dense (m, n) GF(q) matrix."""
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) < 1 \
            or isinstance(m, bool) or not isinstance(m, Integral) or int(m) < 1:
        raise ValueError("n and m must be positive integers")
    n, m = int(n), int(m)
    if field is None:
        field = GF2mField.create(_PEG_Q)
    matrix = np.zeros((m, n), dtype=np.int64)
    for row, col, coeff in triples:
        row, col, coeff = int(row), int(col), int(coeff)
        if not 0 <= row < m or not 0 <= col < n:
            raise ValueError("sparse triple out of bounds")
        field.mul(1, coeff)
        if coeff == 0:
            raise ValueError("edge coefficients must be nonzero")
        if matrix[row, col] != 0:
            raise ValueError("duplicate (row, col) in sparse representation")
        matrix[row, col] = coeff
    return matrix


def syndrome_round_trip(field: GF2mField, matrix: Any, seed: int,
                        n_samples: int = 8) -> dict[str, Any]:
    """Syndrome round-trip check: for random symbol vectors ``x``,
    ``syndrome(H, x)`` matches a re-computed dense pass, and the sparse pass
    equals the dense pass.  Deterministic (PCG64)."""
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    if isinstance(n_samples, bool) or not isinstance(n_samples, Integral) or int(n_samples) < 1:
        raise ValueError("n_samples must be a positive integer")
    dense = np.asarray(matrix, dtype=np.int64)
    if dense.ndim != 2:
        raise ValueError("matrix must be 2-D")
    m, n = dense.shape
    rng = np.random.default_rng(int(seed))
    failures = 0
    checked = 0
    for _ in range(int(n_samples)):
        x = rng.integers(0, field.q, size=n)
        expected = _syndrome_dense(field, dense, x)
        sparse = _syndrome_sparse(field, _dense_to_triples(dense), x)
        if list(sparse) != list(expected):
            failures += 1
        checked += 1
    return {"checked": checked, "failures": failures, "round_trip_ok": failures == 0}


def _syndrome_dense(field: GF2mField, dense: np.ndarray, x: Any) -> list[int]:
    vector = np.asarray(x, dtype=np.int64)
    m = dense.shape[0]
    out: list[int] = []
    for row_index in range(m):
        row = dense[row_index]
        nonzero = np.nonzero(row)[0]
        acc = 0
        for col in nonzero:
            acc = field.add(acc, field.mul(int(row[col]), int(vector[col])))
        out.append(acc)
    return out


def _syndrome_sparse(field: GF2mField, triples: Sequence[Sequence[int]], x: Any) -> list[int]:
    vector = np.asarray(x, dtype=np.int64)
    if not triples:
        return []
    m = max(int(row) for row, _, _ in triples) + 1
    acc = [0] * m
    for row, col, coeff in triples:
        acc[row] = field.add(acc[row], field.mul(int(coeff), int(vector[col])))
    return acc


def _dense_to_triples(dense: np.ndarray) -> list[tuple[int, int, int]]:
    triples: list[tuple[int, int, int]] = []
    for row in range(dense.shape[0]):
        for col in range(dense.shape[1]):
            if dense[row, col] != 0:
                triples.append((row, col, int(dense[row, col])))
    return triples


# --------------------------------------------------------------------------- #
# deterministic irregular PEG
# --------------------------------------------------------------------------- #


def _tie_pick(seed: int, variable: int, socket: int,
              candidates: Sequence[int]) -> int:
    """Deterministic, unbiased tie-break: seed a PCG64 RNG from the frozen
    v10_seed derivation for this (seed, variable, socket) and return the first
    element of the RNG permutation over the sorted candidate list."""
    group = sorted(int(c) for c in candidates)
    rng = np.random.default_rng(
        common.v10_seed(f"peg_tie:{int(seed)}:v:{int(variable)}:s:{int(socket)}"))
    return group[int(rng.permutation(len(group))[0])]


def peg_construct(n: int, m: int, lambda_edge: Mapping[Any, Any],
                  rho_edge: Mapping[Any, Any], seed: int, max_trials: int = 20,
                  field: GF2mField | None = None,
                  edge_label_seed: int | None = None) -> dict[str, Any]:
    """Deterministic irregular PEG construction over GF(1024).

    Degree realization: variable side via ``node_view_counts`` (kept as
    specified); check side via ``check_degree_counts`` plus the
    deterministic ``_reconcile_check_counts`` adjustment to the exact
    variable-side socket total (no-op for already-consistent inputs —
    their constructions are bit-identical); ``socket_consistency``
    remains the fail-closed guard for non-representable requests.

    Returns a dict with ``status`` ("ok" or "frozen_failure"), ``triples``
    (sorted ``(row, col, coeff)`` list), ``n``, ``m``, ``trials_used`` and
    diagnostics (degree sequences, socket totals, parallel-edge count, rank,
    min girth, four-cycle count).  On trial-cap exhaustion the construction
    returns ``frozen_failure`` — never a partial success.
    """
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) < 1 \
            or isinstance(m, bool) or not isinstance(m, Integral) or int(m) < 1:
        raise ValueError("n and m must be positive integers")
    n, m = int(n), int(m)
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    if isinstance(max_trials, bool) or not isinstance(max_trials, Integral) or int(max_trials) < 1:
        raise ValueError("max_trials must be a positive integer")
    if field is None:
        field = GF2mField.create(_PEG_Q)
    if not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField")
    var_counts = node_view_counts(lambda_edge, n)
    check_counts = check_degree_counts(rho_edge, m)
    var_sockets = sum(int(degree) * int(count) for degree, count in var_counts.items())
    check_counts = _reconcile_check_counts(check_counts, var_sockets)
    total_sockets = socket_consistency(var_counts, check_counts)
    edge_seed = common.v10_seed(f"peg_labels:{int(seed)}") if edge_label_seed is None \
        else int(edge_label_seed)
    label_rng = np.random.default_rng(edge_seed)
    # Per-variable degree sequence: degrees assigned to variable indices
    # 0..n-1 in DECREASING degree order (standard PEG practice — high-degree
    # variables are placed first while the graph is still sparse), with the
    # index order of placement itself untouched (v = 0..n-1).
    var_degree_list: list[int] = []
    for degree in sorted(var_counts, reverse=True):
        var_degree_list.extend([int(degree)] * int(var_counts[degree]))
    if len(var_degree_list) != n:
        raise ValueError("variable degree counts do not sum to n")
    var_degree_of = {int(v): var_degree_list[v] for v in range(n)}
    check_degree_list: list[int] = []
    for degree in sorted(check_counts, reverse=True):
        check_degree_list.extend([int(degree)] * int(check_counts[degree]))
    if len(check_degree_list) != m:
        raise ValueError("check degree counts do not sum to m")
    check_degree_of = {int(c): check_degree_list[c] for c in range(m)}
    if sum(var_degree_of.values()) != total_sockets or sum(check_degree_of.values()) != total_sockets:
        raise ValueError("degree counts do not satisfy socket consistency")

    var_sockets = {int(v): var_degree_of[v] for v in range(n)}
    check_free = {int(c): check_degree_of[c] for c in range(m)}
    # Node-id scheme: variable v keeps id v (0..n-1); check c gets the offset
    # node id n + c.  ``node < n`` then unambiguously separates the two sides
    # of the bipartite graph during BFS.
    var_adj: dict[int, list[int]] = {int(v): [] for v in range(n)}
    check_adj: dict[int, list[int]] = {n + int(c): [] for c in range(m)}

    def check_node(check: int) -> int:
        return n + int(check)

    def free_checks() -> list[int]:
        return [c for c in range(m) if check_free[c] > 0]

    def select_check(variable: int, socket: int, tie_seed: int) -> int | None:
        return _select_check(n, m, var_adj, check_adj, check_free,
                             var_degree_of, check_degree_of,
                             int(variable), int(socket), int(tie_seed))

    # D3 fix (constructor rework 2026-09-20): deterministic best-of-N.
    # Every trial runs the full placement with a per-trial tie-break seed
    # ``tie_seed = seed + (trial - 1)`` (trial 1-based, so trial 1 replays
    # the legacy single-trial stream exactly).  The kept graph is the
    # successful trial with minimum four-cycle count (ties -> lowest trial
    # index).  An early stop fires only on four_cycles == 0 (unbeatable).
    # Failure trials count within the same ``max_trials`` cap.
    best_triples: list[tuple[int, int, int]] = []
    best_girth: int | None = None
    best_four: int | None = None
    trials_used = 0
    status = "frozen_failure"
    triples: list[tuple[int, int, int]] = []
    min_girth: int | None = None
    for trial in range(1, int(max_trials) + 1):
        trials_used = trial
        tie_seed = int(seed) + (trial - 1)
        var_sockets = {int(v): var_degree_of[v] for v in range(n)}
        check_free = {int(c): check_degree_of[c] for c in range(m)}
        var_adj = {int(v): [] for v in range(n)}
        check_adj = {n + int(c): [] for c in range(m)}
        triples = []
        min_girth = None
        failed = False
        for variable in range(n):
            for socket in range(var_sockets[variable]):
                check = select_check(variable, socket, tie_seed)
                if check is None:
                    failed = True
                    break
                # D2 fix: local girth of the new edge is distance + 1 ONLY
                # when a path already exists (distance > 0).  Unreachable
                # (distance -1, cycle-free merge) is NEVER a girth
                # candidate.  A graph with no cycle at all keeps
                # min_girth=None (sentinel: "acyclic").
                existing = set(var_adj[variable])
                if existing:
                    distance = _bfs_distance(variable, check_node(check), n, var_adj, check_adj)
                    if distance > 0:
                        girth = distance + 1
                        min_girth = girth if min_girth is None else min(min_girth, girth)
                var_adj[variable].append(check_node(check))
                check_adj[check_node(check)].append(variable)
                check_free[check] -= 1
                triples.append((variable, check, 0))
            if failed:
                break
        if failed or len(triples) != total_sockets:
            continue
        four = _count_four_cycles_var_check(triples)
        if best_four is None or four < best_four:
            best_four = four
            best_triples = list(triples)
            best_girth = min_girth
            if best_four == 0:
                break
    if best_four is None:
        return {
            "status": "frozen_failure",
            "triples": [], "n": n, "m": m, "trials_used": trials_used,
            "max_trials": int(max_trials), "seed": int(seed),
            "total_sockets": total_sockets, "min_girth": None,
            "rank": None, "parallel_edges": None,
            "reason": f"no eligible check placement within {int(max_trials)} trials",
        }
    status = "ok"
    triples = best_triples
    min_girth = best_girth

    # Edge labels: uniform nonzero GF(1024) samples from the frozen seed.
    labeled: list[tuple[int, int, int]] = []
    for variable, check, _ in triples:
        coeff = int(label_rng.integers(1, field.q))  # uniform over nonzero symbols
        field.mul(1, coeff)
        if coeff == 0:
            raise ValueError("edge label sampler produced zero")
        labeled.append((int(check), int(variable), coeff))
    labeled.sort()
    parallel_edges = _parallel_edge_count(labeled)
    dense = sparse_to_dense(labeled, n, m, field)
    rank = rank_GF1024(field, dense.tolist())
    four_cycles = _count_four_cycles_var_check(
        [(col, row) for row, col, _ in labeled])
    return {
        "status": "ok",
        "triples": labeled, "n": n, "m": m, "trials_used": trials_used,
        "max_trials": int(max_trials), "seed": int(seed),
        "edge_label_seed": edge_seed,
        "total_sockets": total_sockets, "min_girth": min_girth,
        "four_cycles": four_cycles,
        "rank": rank, "parallel_edges": parallel_edges,
        "var_counts": {int(k): int(v) for k, v in var_counts.items()},
        "check_counts": {int(k): int(v) for k, v in check_counts.items()},
    }


def _select_check(n: int, m: int,
                  var_adj: Mapping[int, Sequence[int]],
                  check_adj: Mapping[int, Sequence[int]],
                  check_free: Mapping[int, int],
                  var_degree_of: Mapping[int, int],
                  check_degree_of: Mapping[int, int],
                  variable: int, socket: int, tie_seed: int) -> int | None:
    """One PEG edge decision (module-level core; closure-free for testing).

    Priority (exact tie-break policy, in order): (1) unreachable
    (cycle-free) candidates always beat reachable ones — among them, prefer
    the largest free check degree, then the seeded-RNG pick over the sorted
    tied list; (2) among reachable candidates, maximize BFS depth, then
    largest free degree, then max ACE score, then the seeded-RNG pick;
    (3) first-edge / all-unreachable placements use largest free degree,
    then the seeded-RNG pick.  Parallel edges are never selected.
    """
    variable, socket, tie_seed = int(variable), int(socket), int(tie_seed)
    free = [c for c in range(m) if check_free[c] > 0]
    if not free:
        return None

    def check_node(check: int) -> int:
        return n + int(check)

    existing = set(var_adj[variable])
    candidates = [c for c in free if check_node(c) not in existing]
    if not candidates:
        return None
    if not var_adj[variable]:
        best_free = max(check_free[c] for c in candidates)
        group = [c for c in candidates if check_free[c] == best_free]
        if len(group) == 1:
            return group[0]
        group.sort()
        return _tie_pick(tie_seed, variable, socket, group)
    distances: dict[int, int] = {variable: 0}
    parents: dict[int, int | None] = {variable: None}
    frontier: deque[int] = deque([variable])
    while frontier:
        node = frontier.popleft()
        neighbours = var_adj[node] if node < n else check_adj[node]
        for other in neighbours:
            if other not in distances:
                distances[other] = distances[node] + 1
                parents[other] = node
                frontier.append(other)
    # D1: unreachable (cycle-free merge) beats any reachable candidate.
    unreachable = [c for c in candidates if check_node(c) not in distances]
    if unreachable:
        best_free = max(check_free[c] for c in unreachable)
        group = [c for c in unreachable if check_free[c] == best_free]
        if len(group) == 1:
            return group[0]
        group.sort()
        return _tie_pick(tie_seed, variable, socket, group)
    reachable = [c for c in candidates if check_node(c) in distances]
    if not reachable:
        best_free = max(check_free[c] for c in candidates)
        group = [c for c in candidates if check_free[c] == best_free]
        if len(group) == 1:
            return group[0]
        group.sort()
        return _tie_pick(tie_seed, variable, socket, group)
    max_depth = max(distances[check_node(c)] for c in reachable)
    group = [c for c in reachable if distances[check_node(c)] == max_depth]
    if len(group) > 1:
        best_free = max(check_free[c] for c in group)
        group = [c for c in group if check_free[c] == best_free]
    if len(group) > 1:
        scores: dict[int, float] = {}
        for c in group:
            scores[c] = _ace_score(variable, check_node(c), parents,
                                   distances, var_degree_of,
                                   check_degree_of, n)
        best_score = max(scores.values())
        group = [c for c in group if scores[c] == best_score]
    if len(group) == 1:
        return group[0]
    group.sort()
    return _tie_pick(tie_seed, variable, socket, group)


def _count_four_cycles_var_check(triples: Sequence[Sequence[int]]) -> int:
    """Count 4-cycles over ``(variable, check)`` triples (pre-label order).

    Each 4-cycle {v1,v2,c1,c2} is counted once: for every check pair
    co-occurring at ``k`` variables, add C(k,2).  Deterministic.
    """
    pair_counts: dict[tuple[int, int], int] = {}
    var_checks: dict[int, list[int]] = {}
    for variable, check, *_ in triples:
        var_checks.setdefault(int(variable), []).append(int(check))
    for checks in var_checks.values():
        ordered = sorted(set(checks))
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                key = (ordered[i], ordered[j])
                pair_counts[key] = pair_counts.get(key, 0) + 1
    return sum(k * (k - 1) // 2 for k in pair_counts.values())


def _bfs_distance(source: int, target: int, n: int,
                  var_adj: Mapping[int, Sequence[int]],
                  check_adj: Mapping[int, Sequence[int]]) -> int:
    distances = {source: 0}
    frontier = deque([source])
    while frontier:
        node = frontier.popleft()
        if node == target:
            return distances[node]
        neighbours = var_adj[node] if node < n else check_adj[node]
        for other in neighbours:
            if other not in distances:
                distances[other] = distances[node] + 1
                frontier.append(other)
    return -1  # unreachable


def _ace_score(variable: int, check: int, parents: Mapping[int, int | None],
               distances: Mapping[int, int],
               var_degree_of: Mapping[int, int],
               check_degree_of: Mapping[int, int], n: int) -> float:
    """ACE-like score of the cycle created by the new edge (variable, check):
    ``(d_v - 2) + sum over the path's intermediate variable nodes of (d_w-2)``
    (check degrees do not enter the ACE cycle metric; larger is better).
    Node ids follow the offset scheme (check nodes are >= n)."""
    score = float(var_degree_of[variable] - 2)
    node = check
    while node is not None and parents[node] is not None:
        node = parents[node]  # parent is a variable node (odd distance)
        if node is None or node == variable:
            break
        if node < n:
            score += float(var_degree_of[node] - 2)
        node = parents[node]
    return score


def _parallel_edge_count(triples: Sequence[Sequence[int]]) -> int:
    seen: set[tuple[int, int]] = set()
    duplicates = 0
    for row, col, _ in triples:
        pair = (int(row), int(col))
        if pair in seen:
            duplicates += 1
        seen.add(pair)
    return duplicates


# --------------------------------------------------------------------------- #
# manifest (construction parameters only)
# --------------------------------------------------------------------------- #


def peg_manifest(construction: Mapping[str, Any]) -> dict[str, Any]:
    """Manifest for a PEG construction result: schema, status and all
    construction parameters.  No self-hash / source-hash fields (per the
    2026-08-06 protocol amendment)."""
    triples = construction.get("triples", [])
    return {
        "schema": "v10_peg_manifest_v1",
        "n": construction.get("n"),
        "m": construction.get("m"),
        "seed": construction.get("seed"),
        "edge_label_seed": construction.get("edge_label_seed"),
        "max_trials": construction.get("max_trials"),
        "trials_used": construction.get("trials_used"),
        "status": construction.get("status"),
        "rank": construction.get("rank"),
        "parallel_edges": construction.get("parallel_edges"),
        "total_sockets": construction.get("total_sockets"),
        "var_counts": construction.get("var_counts"),
        "check_counts": construction.get("check_counts"),
        "triples_count": len(triples),
    }
