"""V72P2D10 mixed-degree L1 finite discriminator — frozen core (R2 connectivity-first).

Change: ``v72p2d10-mixed-degree-l1-finite-discriminator``
Cycle: ``V72P2D10-MIXED-DEGREE-L1``
Frozen authority: ``openspec/changes/v72p2d10-mixed-degree-l1-finite-discriminator/``
(``design.md`` §2–§8, delta spec) and
``.workbuddy/tasks/D10_MIXED_DEGREE_L1_CONNECTIVITY_R2_TASK_PACKET.md``.

Contents (R2; R1 F01–F12 evidence retained, batch never authorized):

- ``build_degree_sequence_peg``: one deterministic connectivity-first
  degree-sequence PEG shared by both arms (only the forced degree sequence
  differs). Phase A builds a seeded spanning backbone (a tree over all n+m
  Tanner nodes respecting exact target degrees); Phase B fills remaining
  sockets with the shared R1 PEG/ACE rule, reusing read-only the accepted
  ``nonbinary_v10_peg`` placement primitives (``_tie_pick`` / ``_bfs_distance``
  / ``_ace_score``) and ``nonbinary_v10_common.v10_seed``. One deterministic
  attempt per seed; parallel edges, degree overshoot, socket mismatch or a
  dead end return ``status="construction_failed"`` with no partial graph.
  Zero replacement seeds (the R1 replacement clause is retired).
- ``structural_rank``: deterministic maximum bipartite matching (Kuhn, fixed
  visitation order); admission requires all ``m`` checks covered.
- ``gf32_row_rank``: exact GF32 (poly 37) row rank with local fresh
  log/exp-table arithmetic (no new dependency); admission requires rank
  ``m``; failure records the cell and stops with no seed change.
- structural record with the retained G1–G6 measurement base plus binding
  admission A1–A6 (exact degrees/sockets, simple graph, single component,
  structural ``m``, GF32 ``m``, deterministic replay); four-cycle/girth/ACE
  stay reported diagnostics;
- the frozen plan, per-width POSITIVE/NEGATIVE/AMBIGUOUS/ENGINEERING_BLOCKED
  classification, conditional progression and terminal routing;
- ``execute_plan``: paired L1 dispatch on identical sampled blocks with an
  **injected** decoder/syndrome callable (no production decoder import in this
  module; a non-admitted graph raises before the decoder is bound);
- ``profile_graphs``: bounded pre-decoder R210 graph construction at all
  widths for both arms (no decoder, no root, no replacement).

Budgets and semantics are frozen in ``design.md`` §6; this module contains no
retry, no resume, no seed search and no adaptive stop. Batch authorization is
a CLI argument owned by the runner (``--execution-authorized``); no source
constant authorizes execution.
"""
from __future__ import annotations

import time
from collections import Counter, deque
from collections.abc import Mapping, Sequence
from numbers import Integral
from pathlib import Path
from typing import Any

import numpy as np

from . import nonbinary_v10_common as common
from . import nonbinary_v10_peg as v10peg
from . import v37_degree_feasibility as v37
from . import v72p2d5_gf32_rate_mother as d5
from . import v72p2d6_gf32_graph_mother as d6
from .nonbinary_field import GF2mField

__all__ = [
    "ARMS", "WIDTHS", "ARM_ROLE", "GRAPH_SEEDS", "BLOCK_SEEDS",
    "DEGREE_TABLE", "DECODER_MAX_ITER",
    "DAMPING_ALPHA", "SCIENTIFIC_CALL_CEILING", "SETUP_CALL_CEILING",
    "SETUP_FIXED_UNITS", "WALL_BUDGET_S", "PER_CALL_BUDGET_S",
    "RSS_BUDGET_BYTES", "EVIDENCE_FILES", "FROZEN_COMMAND", "FUTURE_ROOT",
    "FUTURE_ROOT_UUID", "AUTHORIZATION", "CLAIM_CEILING",
    "POSITIVE", "NEGATIVE", "AMBIGUOUS", "ENGINEERING_BLOCKED",
    "T_CANDIDATE_REPRODUCIBLE", "T_FINITE_SIZE_SIGNAL",
    "T_NO_MATERIAL_ADVANTAGE", "T_AMBIGUOUS", "T_ENGINEERING_BLOCKED",
    "T_NOT_RUN", "TERMINALS", "StructureNotAdmitted", "degree_cell",
    "build_degree_sequence_peg", "structural_rank", "gf32_row_rank",
    "coefficient_seed", "coefficients_for_edges",
    "dense_from_edges", "structural_record", "build_graph", "build_call_plan",
    "classify_width", "route_terminal", "dispatch_l1", "execute_plan",
    "profile_graphs", "refuse_out_root",
]

# --------------------------------------------------------------------------- #
# Frozen identifiers (design §1/§3/§4/§6/§8)
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2d10-mixed-degree-l1-finite-discriminator"
CYCLE_ID = "V72P2D10-MIXED-DEGREE-L1"
TRACK = "EXPLORE_HEAVY"
CLAIM_CEILING = (
    "synthetic finite-length L1-only diagnostic under the accepted CAL-only "
    "Model-F prior and the frozen decoder contract; no L2/APP, oracle-L2, "
    "FER, leakage, SKR, qualification, promotion or real-data claim, and no "
    "DE-to-decoder equivalence claim; D7-H is not revived by any D10 outcome"
)

Q = 32
POLY = 37
MODEL_F_INPUT_ROOT = "workspace/v72p2d5_model_f_input/20260907_r1"
FUTURE_ROOT_UUID = "b2dd13e4-6600-4e27-90df-5c9038cf2c34"
FUTURE_ROOT = "workspace/d10_mixed_degree_l1_" + FUTURE_ROOT_UUID
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py "
    "--batch --model-f-root %s --out-root %s" % (MODEL_F_INPUT_ROOT, FUTURE_ROOT)
)
AUTHORIZATION = (
    "separate explicit user/main-thread authorization required before --batch")
#: R206: batch authorization is the runner CLI argument --execution-authorized
#: (default false). No source constant authorizes execution.

EVIDENCE_FILES = ("manifest.json", "l1_records.csv", "graph_records.csv",
                  "arm_summary.csv", "summary.json", "command_log.txt")

ARMS = ("PEG_DV3_MATCHED", "PEG_DV23_LAM2_045")
ARM_ROLE = {"PEG_DV3_MATCHED": "matched_control",
            "PEG_DV23_LAM2_045": "D9_selected_candidate"}
WIDTHS = (64, 128, 256)

#: Frozen graph seeds (design §4.1): 3 per width, never result-adaptive.
GRAPH_SEEDS = {
    64: (2026092201, 2026092202, 2026092203),
    128: (2026092204, 2026092205, 2026092206),
    256: (2026092207, 2026092208, 2026092209),
}
#: Frozen block seeds (design §4.3): 8 per width, separate from graph seeds.
BLOCK_SEEDS = {
    64: tuple(range(2026092301, 2026092309)),
    128: tuple(range(2026092311, 2026092319)),
    256: tuple(range(2026092321, 2026092329)),
}
#: R2 (design §4.1): ZERO replacement seeds. The R1
#: ``PROFILE_REPLACEMENT_SEEDS`` clause is retired: it is not defined,
#: referenced or consumed anywhere in R2. Any construction/admission failure
#: at a frozen seed is retained as a record and engineering-blocks the width.

#: Exact f1.2 realizations of record (design §3, transcribed from D9 §5).
DEGREE_TABLE = {
    ("PEG_DV3_MATCHED", 64): {
        "n": 64, "m": 59, "var_counts": {3: 64},
        "check_counts": {3: 44, 4: 15}},
    ("PEG_DV3_MATCHED", 128): {
        "n": 128, "m": 118, "var_counts": {3: 128},
        "check_counts": {3: 88, 4: 30}},
    ("PEG_DV3_MATCHED", 256): {
        "n": 256, "m": 236, "var_counts": {3: 256},
        "check_counts": {3: 176, 4: 60}},
    ("PEG_DV23_LAM2_045", 64): {
        "n": 64, "m": 59, "var_counts": {3: 29, 2: 35},
        "check_counts": {3: 39, 2: 20}},
    ("PEG_DV23_LAM2_045", 128): {
        "n": 128, "m": 118, "var_counts": {3: 57, 2: 71},
        "check_counts": {3: 77, 2: 41}},
    ("PEG_DV23_LAM2_045", 256): {
        "n": 256, "m": 236, "var_counts": {3: 115, 2: 141},
        "check_counts": {3: 155, 2: 81}},
}

#: Decoder contract (design §4.5; production adapter injected by the runner).
DECODER_MAX_ITER = 90
DAMPING_ALPHA = 1.0

#: Budgets (design §6.1).
SCIENTIFIC_CALL_CEILING = 144
SETUP_CALL_CEILING = 44
SETUP_FIXED_UNITS = 2  # prior-chain load + plan build
WALL_BUDGET_S = 1800.0
PER_CALL_BUDGET_S = 120.0
RSS_BUDGET_BYTES = 2 * 1024 ** 3

#: Per-width classification labels and terminals (design §6.2/§6.4).
POSITIVE = "POSITIVE"
NEGATIVE = "NEGATIVE"
AMBIGUOUS = "AMBIGUOUS"
ENGINEERING_BLOCKED = "ENGINEERING_BLOCKED"

T_CANDIDATE_REPRODUCIBLE = "D10_L1_CANDIDATE_REPRODUCIBLE"
T_FINITE_SIZE_SIGNAL = "D10_L1_FINITE_SIZE_SIGNAL"
T_NO_MATERIAL_ADVANTAGE = "D10_L1_NO_MATERIAL_ADVANTAGE"
T_AMBIGUOUS = "D10_L1_AMBIGUOUS"
T_ENGINEERING_BLOCKED = "D10_L1_ENGINEERING_BLOCKED"
T_NOT_RUN = "D10_L1_NOT_RUN"
TERMINALS = (T_CANDIDATE_REPRODUCIBLE, T_FINITE_SIZE_SIGNAL,
             T_NO_MATERIAL_ADVANTAGE, T_AMBIGUOUS, T_ENGINEERING_BLOCKED,
             T_NOT_RUN)

#: Protected roots: never written (D9/D8/D7/D6/Model-F/A2/G2 subtrees and
#: formal outputs). The D10 future root is intentionally not matched.
PROTECTED_NAME_PREFIXES = ("v72p2d5", "v72p2d6", "v72p2d7", "v72p2d8",
                           "v72p2d9", "d6_", "d7_", "d8_", "d9_", "a2", "g2",
                           "tmp_pytest")
PROTECTED_SUBTREES = ("comparison_bench/outputs_comparison", "results")


class StructureNotAdmitted(ValueError):
    """Raised when a decoder dispatch is attempted for a non-admitted graph."""


# --------------------------------------------------------------------------- #
# Degree tables
# --------------------------------------------------------------------------- #
def degree_cell(arm: str, width: int) -> dict[str, Any]:
    """Return the frozen f1.2 ``(n, m, var_counts, check_counts)`` cell."""
    key = (str(arm), int(width))
    if key not in DEGREE_TABLE:
        raise KeyError("unknown D10 (arm, width) cell %r" % (key,))
    cell = DEGREE_TABLE[key]
    var_sockets = sum(int(d) * int(c) for d, c in cell["var_counts"].items())
    check_sockets = sum(int(d) * int(c)
                        for d, c in cell["check_counts"].items())
    if sum(cell["var_counts"].values()) != cell["n"]:
        raise ValueError("frozen cell %r variable counts do not sum to n" % (key,))
    if sum(cell["check_counts"].values()) != cell["m"]:
        raise ValueError("frozen cell %r check counts do not sum to m" % (key,))
    if var_sockets != check_sockets:
        raise ValueError("frozen cell %r socket mismatch" % (key,))
    return {"n": int(cell["n"]), "m": int(cell["m"]),
            "var_counts": dict(cell["var_counts"]),
            "check_counts": dict(cell["check_counts"]), "E": var_sockets}


def _validate_counts(counts: Mapping[Any, Any], total: int, side: str) -> dict[int, int]:
    if not isinstance(counts, Mapping) or not counts:
        raise ValueError("%s degree counts must be a non-empty mapping" % side)
    out: dict[int, int] = {}
    for degree, count in counts.items():
        if isinstance(degree, bool) or not isinstance(degree, Integral) \
                or int(degree) < 2:
            raise ValueError("%s degrees must be integers >= 2" % side)
        if isinstance(count, bool) or not isinstance(count, Integral) \
                or int(count) < 1:
            raise ValueError("%s degree counts must be positive integers" % side)
        out[int(degree)] = int(count)
    if sum(out.values()) != int(total):
        raise ValueError("%s degree counts do not sum to %d" % (side, int(total)))
    return out


# --------------------------------------------------------------------------- #
# R2: connectivity-first deterministic degree-sequence PEG (one constructor)
# --------------------------------------------------------------------------- #
def _backbone_seed(seed: int) -> int:
    """Seeded backbone namespace derived from the frozen graph seed."""
    return int(common.v10_seed("d10:backbone:%d" % int(seed)))


def build_degree_sequence_peg(n: int, m: int, var_counts: Mapping[Any, Any],
                              check_counts: Mapping[Any, Any], seed: int,
                              field: GF2mField | None = None) -> dict[str, Any]:
    """Connectivity-first PEG honoring exact variable/check degree counts.

    One constructor shared by both arms; only the forced degree sequence
    input may differ. Phase A builds a deterministic spanning backbone (a
    tree over all ``n+m`` Tanner nodes: a seeded variable/check-order path
    covering every check plus one seeded attachment edge per leftover
    variable) consuming at most the exact target degree of each endpoint.
    Phase B fills all remaining sockets with the shared R1 PEG/ACE rule
    (free checks not already adjacent; max BFS depth, then max ACE score,
    then ``nonbinary_v10_peg._tie_pick`` over the sorted candidate list).
    One attempt per seed: a parallel edge, degree overshoot, socket
    mismatch or dead end returns ``status="construction_failed"`` with no
    partial graph. Count sequences that cannot satisfy socket balance raise
    before any placement.
    """
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) < 1:
        raise ValueError("n must be a positive integer")
    if isinstance(m, bool) or not isinstance(m, Integral) or int(m) < 1:
        raise ValueError("m must be a positive integer")
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    if field is not None and not isinstance(field, GF2mField):
        raise ValueError("field must be a pinned GF2mField or None")
    n, m, seed = int(n), int(m), int(seed)
    var = _validate_counts(var_counts, n, "variable")
    chk = _validate_counts(check_counts, m, "check")
    total_sockets = sum(d * c for d, c in var.items())
    if sum(d * c for d, c in chk.items()) != total_sockets:
        raise ValueError("socket mismatch: variable sockets != check sockets")

    # Degree-to-index convention (design §2.0 / B1 :306-321): decreasing
    # degree order, placement iterates variables 0..n-1 and sockets in order.
    var_degree_list: list[int] = []
    for degree in sorted(var, reverse=True):
        var_degree_list.extend([int(degree)] * int(var[degree]))
    check_degree_list: list[int] = []
    for degree in sorted(chk, reverse=True):
        check_degree_list.extend([int(degree)] * int(chk[degree]))
    var_degree_of = {v: var_degree_list[v] for v in range(n)}
    check_degree_of = {c: check_degree_list[c] for c in range(m)}

    var_adj: dict[int, list[int]] = {v: [] for v in range(n)}
    check_adj: dict[int, list[int]] = {n + c: [] for c in range(m)}
    used_var = {v: 0 for v in range(n)}
    used_check = {c: 0 for c in range(m)}
    check_free = {c: check_degree_of[c] for c in range(m)}
    edges: list[tuple[int, int]] = []
    min_girth: int | None = None
    failure_reason = ""

    def check_node(check: int) -> int:
        return n + int(check)

    def add_edge(variable: int, check: int, where: str) -> bool:
        nonlocal failure_reason
        variable, check = int(variable), int(check)
        if used_var[variable] >= var_degree_of[variable] \
                or used_check[check] >= check_degree_of[check]:
            failure_reason = ("%s degree overshoot at variable %d check %d"
                              % (where, variable, check))
            return False
        if check_node(check) in var_adj[variable]:
            failure_reason = ("%s parallel edge at variable %d check %d"
                              % (where, variable, check))
            return False
        var_adj[variable].append(check_node(check))
        check_adj[check_node(check)].append(variable)
        used_var[variable] += 1
        used_check[check] += 1
        check_free[check] -= 1
        edges.append((variable, check))
        return True

    # Phase A — spanning backbone: seeded permutation orders, then a path
    # c_q0-v_p0-c_q1-v_p1-...-c_q{m-1}-v_p{m-1} (every check covered, all
    # backbone degrees <= the exact targets since every target degree >= 2)
    # plus one seeded max-remaining-capacity attachment per leftover
    # variable. The result is a connected spanning tree (n+m-1 edges).
    bb_seed = _backbone_seed(seed)
    rng = np.random.default_rng(bb_seed)
    var_order = [int(v) for v in rng.permutation(n)]
    check_order = [int(c) for c in rng.permutation(m)]
    failed = False
    for i in range(m):
        if not add_edge(var_order[i], check_order[i], "backbone path"):
            failed = True
            break
    if not failed:
        for i in range(m - 1):
            if not add_edge(var_order[i], check_order[i + 1],
                            "backbone path"):
                failed = True
                break
    if not failed:
        for k, variable in enumerate(var_order[m:]):
            cands = [c for c in range(m) if check_free[c] > 0]
            if not cands:
                failure_reason = ("backbone attach found no free check for "
                                  "variable %d" % variable)
                failed = True
                break
            best = max(check_degree_of[c] - used_check[c] for c in cands)
            group = sorted(c for c in cands
                           if check_degree_of[c] - used_check[c] == best)
            pick = group[0] if len(group) == 1 else int(
                v10peg._tie_pick(bb_seed, int(variable), int(k), group))
            if not add_edge(variable, pick, "backbone attach"):
                failed = True
                break

    def capacity_tie(variable: int, socket: int,
                     candidates: Sequence[int]) -> int:
        best_free = max(check_free[c] for c in candidates)
        group = [c for c in candidates if check_free[c] == best_free]
        if len(group) == 1:
            return int(group[0])
        group.sort()
        return int(v10peg._tie_pick(seed, variable, socket, group))

    def select_check(variable: int, socket: int) -> int | None:
        free = [c for c in range(m) if check_free[c] > 0]
        if not free:
            return None
        existing = set(var_adj[variable])
        candidates = [c for c in free if check_node(c) not in existing]
        if not candidates:
            return None
        if not var_adj[variable]:
            return capacity_tie(variable, socket, candidates)
        # BFS mirror of B1 (:356-367); a per-candidate _bfs_distance call
        # would repeat the same BFS m times.
        distances: dict[int, int] = {variable: 0}
        parents: dict[int, int | None] = {variable: None}
        frontier = deque([variable])
        while frontier:
            node = frontier.popleft()
            neighbours = var_adj[node] if node < n else check_adj[node]
            for other in neighbours:
                if other not in distances:
                    distances[other] = distances[node] + 1
                    parents[other] = node
                    frontier.append(other)
        reachable = [c for c in candidates if check_node(c) in distances]
        if not reachable:
            return capacity_tie(variable, socket, candidates)
        max_depth = max(distances[check_node(c)] for c in reachable)
        group = [c for c in reachable
                 if distances[check_node(c)] == max_depth]
        if len(group) > 1:
            scores = {
                c: v10peg._ace_score(variable, check_node(c), parents,
                                     distances, var_degree_of, check_degree_of,
                                     n)
                for c in group}
            best = max(scores.values())
            group = [c for c in group if scores[c] == best]
        if len(group) == 1:
            return int(group[0])
        group.sort()
        return int(v10peg._tie_pick(seed, variable, socket, group))

    # Phase B — shared PEG/ACE fill over all remaining sockets.
    failed_at: dict[str, int] | None = None
    if not failed:
        for variable in range(n):
            while used_var[variable] < var_degree_of[variable]:
                socket = int(used_var[variable])
                check = select_check(variable, socket)
                if check is None:
                    failed_at = {"variable": int(variable),
                                 "socket": socket}
                    failure_reason = (
                        "no eligible check placement at variable %d socket %d"
                        % (variable, socket))
                    break
                if var_adj[variable]:
                    distance = v10peg._bfs_distance(
                        variable, check_node(check), n, var_adj, check_adj)
                    if distance > 0:
                        girth = distance + 1
                        min_girth = girth if min_girth is None \
                            else min(min_girth, girth)
                if not add_edge(variable, int(check), "fill"):
                    break
            if failed_at is not None or failure_reason:
                break

    if failed or failed_at is not None or failure_reason:
        if not failure_reason and failed_at is not None:
            failure_reason = (
                "no eligible check placement at variable %d socket %d"
                % (failed_at["variable"], failed_at["socket"]))
        return {
            "status": "construction_failed", "edges": [], "n": n, "m": m,
            "seed": seed, "E": total_sockets, "min_girth": None,
            "var_counts": {int(d): int(c) for d, c in var.items()},
            "check_counts": {int(d): int(c) for d, c in chk.items()},
            "failed_at": failed_at,
            "failure_reason": failure_reason,
        }
    edges.sort()
    return {
        "status": "ok", "edges": edges, "n": n, "m": m, "seed": seed,
        "E": total_sockets, "min_girth": min_girth,
        "var_counts": {int(d): int(c) for d, c in var.items()},
        "check_counts": {int(d): int(c) for d, c in chk.items()},
        "failed_at": None, "failure_reason": "",
    }


# --------------------------------------------------------------------------- #
# R203: deterministic structural rank (maximum bipartite matching)
# --------------------------------------------------------------------------- #
def structural_rank(n: int, m: int,
                    edges: Sequence[Sequence[int]]) -> int:
    """Maximum bipartite-matching cardinality over checks (deterministic).

    Kuhn augmenting-path search with fixed visitation order (checks
    ``0..m-1``, neighbours sorted ascending); seeded only by the structure
    itself — no randomness. Admission requires the result to equal ``m``.
    """
    n, m = int(n), int(m)
    adj: list[list[int]] = [[] for _ in range(m)]
    for variable, check in edges:
        variable, check = int(variable), int(check)
        if not 0 <= variable < n or not 0 <= check < m:
            raise ValueError("edge (%d, %d) outside (%d, %d)"
                             % (variable, check, n, m))
        adj[check].append(variable)
    for neighbours in adj:
        neighbours.sort()
    match_var: list[int] = [-1] * n

    def augment(check: int, seen: list[bool]) -> bool:
        for variable in adj[check]:
            if seen[variable]:
                continue
            seen[variable] = True
            if match_var[variable] == -1 \
                    or augment(match_var[variable], seen):
                match_var[variable] = check
                return True
        return False

    rank = 0
    for check in range(m):
        if augment(check, [False] * n):
            rank += 1
    return int(rank)


# --------------------------------------------------------------------------- #
# R204: exact GF32 (poly 37) row rank with fresh local arithmetic
# --------------------------------------------------------------------------- #
def _gf32_mul_raw(a: int, b: int) -> int:
    """GF(32)/poly-37 (0b100101) multiply by peasant steps (exact)."""
    result, aa, bb = 0, int(a), int(b)
    while bb:
        if bb & 1:
            result ^= aa
        bb >>= 1
        aa <<= 1
        if aa & 0x20:
            aa ^= 0x25
    return result & 0x1F


_GF32_ALOG = [0] * 63
_GF32_LOG = [0] * 32
_gf32_gen = 1
for _gf32_i in range(63):
    _GF32_ALOG[_gf32_i] = _gf32_gen
    _gf32_gen = _gf32_mul_raw(_gf32_gen, 2)
for _gf32_i in range(31):
    _GF32_LOG[_GF32_ALOG[_gf32_i]] = _gf32_i
assert len(set(_GF32_ALOG[:31])) == 31  # 2 is primitive mod x^5+x^2+1
del _gf32_gen, _gf32_i


def _gf32_inv(s: int) -> int:
    s = int(s)
    if s == 0:
        raise ValueError("GF(32) inverse of zero is undefined")
    return int(_GF32_ALOG[(31 - _GF32_LOG[s]) % 31])


def _gf32_mul_scalar_vec(row: np.ndarray, s: int) -> np.ndarray:
    s = int(s)
    row = np.asarray(row, dtype=np.int64)
    if s == 0:
        return np.zeros_like(row)
    if s == 1:
        return row.copy()
    out = np.zeros_like(row)
    nz = row != 0
    out[nz] = np.asarray(_GF32_ALOG, dtype=np.int64)[
        (np.asarray(_GF32_LOG, dtype=np.int64)[row[nz]]
         + _GF32_LOG[s]) % 31]
    return out


def gf32_row_rank(dense: np.ndarray) -> int:
    """Exact row rank over GF(32)/poly-37 by vectorized forward elimination."""
    a = np.asarray(dense, dtype=np.int64).copy()
    if a.ndim != 2:
        raise ValueError("rank input must be 2-D")
    m, n = a.shape
    alog = np.asarray(_GF32_ALOG, dtype=np.int64)
    ltab = np.asarray(_GF32_LOG, dtype=np.int64)
    rank = 0
    for col in range(n):
        hits = np.flatnonzero(a[rank:, col])
        if hits.shape[0] == 0:
            continue
        pivot = rank + int(hits[0])
        if pivot != rank:
            a[[rank, pivot]] = a[[pivot, rank]]
        inv = _gf32_inv(int(a[rank, col]))
        if inv != 1:
            a[rank] = _gf32_mul_scalar_vec(a[rank], inv)
        sub = a[rank + 1:]
        if sub.shape[0]:
            factor = sub[:, col]
            live = factor != 0
            prow_live = a[rank] != 0
            if bool(np.any(live)) and bool(np.any(prow_live)):
                lp = np.zeros(n, dtype=np.int64)
                lp[prow_live] = ltab[a[rank, prow_live]]
                add = alog[(lp[None, :] + ltab[factor][:, None]) % 31]
                add[~live[:, None] | ~prow_live[None, :]] = 0
                sub ^= add
        rank += 1
        if rank == m:
            break
    return int(rank)


# --------------------------------------------------------------------------- #
# coefficients (frozen R1 rule; R204 uses it unchanged)
# --------------------------------------------------------------------------- #
def coefficient_seed(width: int, graph_seed: int) -> int:
    """Frozen coefficient stream seed ``d10:coeff:{width}:{graph_seed}``."""
    return common.v10_seed("d10:coeff:%d:%d" % (int(width), int(graph_seed)))


def coefficients_for_edges(edges: Sequence[Sequence[int]], width: int,
                           graph_seed: int) -> list[int]:
    """One uniform nonzero GF32 draw per edge in sorted ``(v, c)`` order."""
    rng = np.random.default_rng(coefficient_seed(width, graph_seed))
    out = []
    for _ in edges:
        coeff = int(rng.integers(1, Q))
        if coeff == 0:
            raise ValueError("coefficient sampler produced zero")
        out.append(coeff)
    return out


def dense_from_edges(n: int, m: int, edges: Sequence[Sequence[int]],
                     coefficients: Sequence[int]) -> np.ndarray:
    """Dense ``(m, n)`` GF32 matrix with ``H[check, variable] = coeff``."""
    if len(edges) != len(coefficients):
        raise ValueError("edges and coefficients must share length")
    dense = np.zeros((int(m), int(n)), dtype=np.int64)
    for (variable, check), coeff in zip(edges, coefficients):
        row, col, coeff = int(check), int(variable), int(coeff)
        if coeff <= 0 or coeff >= Q:
            raise ValueError("edge coefficients must be nonzero GF32 symbols")
        if dense[row, col] != 0:
            raise ValueError("duplicate (check, variable) edge")
        dense[row, col] = coeff
    return dense


# --------------------------------------------------------------------------- #
# structural record (G1-G6 measurement base + R205 binding admission A1-A6)
# --------------------------------------------------------------------------- #
def _hist(values: Sequence[int]) -> dict[int, int]:
    """Degree histogram over present (nonzero-degree) nodes only."""
    counter = Counter(int(value) for value in values)
    counter.pop(0, None)
    return {int(d): int(c) for d, c in sorted(counter.items())}


def structural_record(dense: np.ndarray,
                      expected_var_counts: Mapping[Any, Any],
                      expected_check_counts: Mapping[Any, Any]
                      ) -> dict[str, Any]:
    """Measure the frozen structural gates/diagnostics and R205 admission.

    G1–G6 (retained measurement base): variable histogram, check histogram,
    socket balance, simple/no-duplicate edge, no empty check with min degree
    >= 2 and equal to the frozen minimum, degree-2 forest feasibility.
    A1–A5 (binding, checked here): exact degrees/socket balance, simple
    graph, exactly one component over all ``n+m`` Tanner nodes, deterministic
    structural rank ``m``, exact GF32 rank ``m``. A6 (deterministic replay)
    is checked by ``build_graph``. Four-cycle count, girth and ACE values
    are reported diagnostics and never gate admission.
    """
    H = np.asarray(dense)
    if H.ndim != 2 or H.size == 0:
        raise ValueError("dense matrix must be a non-empty 2-D array")
    m, n = H.shape
    present = H != 0
    var_hist = _hist([int(x) for x in present.sum(axis=0)])
    check_hist = _hist([int(x) for x in present.sum(axis=1)])
    E = int(np.count_nonzero(H))
    rows, cols = np.nonzero(present)
    unique_edges = {(int(c), int(r)) for r, c in zip(rows, cols)}
    duplicate_edges = int(E - len(unique_edges))
    empty_checks = int(m - sum(check_hist.values()))
    min_check_degree = int(min(check_hist)) if check_hist else 0
    var_sockets = sum(d * c for d, c in var_hist.items())
    check_sockets = sum(d * c for d, c in check_hist.items())
    exp_var = {int(d): int(c) for d, c in sorted(expected_var_counts.items())}
    exp_check = {int(d): int(c)
                 for d, c in sorted(expected_check_counts.items())}
    exp_E = sum(d * c for d, c in exp_var.items())

    degree2 = v37.analyze_degree2_subgraph(var_hist.get(2, 0), m)
    audit = d5.audit_prefix(H, m)
    girth, girth_reason = d6.compute_girth(H)
    row_min, rows_below_2 = d6.check_I1_row_degree(H, m)
    match_rank = structural_rank(n, m, list(unique_edges))
    field_rank = gf32_row_rank(H)

    gates = {
        "G1_variable_degree_histogram": bool(var_hist == exp_var),
        "G2_check_degree_histogram": bool(check_hist == exp_check),
        "G3_socket_balance": bool(var_sockets == check_sockets == E
                                  and E == exp_E),
        "G4_simple_no_duplicate_edge": bool(duplicate_edges == 0),
        "G5_no_empty_check_min_degree": bool(
            empty_checks == 0 and row_min >= 2
            and row_min == min(exp_check) and rows_below_2 == 0),
        "G6_degree2_forest_feasible": bool(degree2["is_forest_feasible"]),
    }
    admission = {
        "A1_exact_degrees_socket_balance": bool(
            var_hist == exp_var and check_hist == exp_check
            and var_sockets == check_sockets == E and E == exp_E),
        "A2_simple_graph_min_degree": bool(
            duplicate_edges == 0 and empty_checks == 0
            and min_check_degree == min(exp_check)),
        "A3_single_component": bool(audit["connected_components"] == 1),
        "A4_structural_rank_m": bool(match_rank == m),
        "A5_gf32_rank_m": bool(field_rank == m),
    }
    return {
        "variable_degree_histogram": var_hist,
        "check_degree_histogram": check_hist,
        "E": E,
        "var_sockets": int(var_sockets),
        "check_sockets": int(check_sockets),
        "duplicate_edges": duplicate_edges,
        "empty_checks": empty_checks,
        "min_check_degree": min_check_degree,
        "rows_below_degree_2": int(rows_below_2),
        "rank": int(audit["rank"]),
        "structural_rank": int(match_rank),
        "gf32_rank": int(field_rank),
        "connected_components": int(audit["connected_components"]),
        "largest_component_fraction":
            float(audit["largest_component_fraction"]),
        "isolated_variables": int(audit["isolated_variables"]),
        "degree2": {
            "N2": int(degree2["N2"]),
            "forest_bound": int(degree2["forest_bound"]),
            "cycle_rank_lower_bound": int(degree2["cycle_rank_lower_bound"]),
            "is_forest_feasible": bool(degree2["is_forest_feasible"]),
        },
        "four_cycles": int(audit["four_cycles"]),
        "four_cycle_variable_incidence_max":
            int(audit["four_cycle_variable_incidence_max"]),
        "girth": None if girth is None else int(girth),
        "girth_reason": girth_reason or "",
        "gates": gates,
        "admission": admission,
        "admitted": bool(all(admission.values())),
    }


def build_graph(arm: str, width: int, graph_seed: int) -> dict[str, Any]:
    """Build one frozen two-arm graph: PEG edges, coefficients, structure.

    Admission A1–A6 is decided before any decoder binding: A1–A5 from the
    structural record plus A6 deterministic replay equality (rebuilding
    ``(arm, width, graph_seed)`` reproduces the identical sorted edge list
    and coefficient stream). Any failure is retained with
    ``admitted=False`` and engineering-blocks the width; seeds are never
    altered, repaired or searched.
    """
    cell = degree_cell(arm, width)
    construction = build_degree_sequence_peg(
        cell["n"], cell["m"], cell["var_counts"], cell["check_counts"],
        int(graph_seed))
    record: dict[str, Any] = {
        "arm": str(arm), "width": int(width), "graph_seed": int(graph_seed),
        "n": cell["n"], "m": cell["m"], "E": 0, "edges": [],
        "coefficients": [], "dense": None, "structure": None,
        "status": "construction_failed", "admitted": False,
        "failure_reason": construction.get("failure_reason", ""),
    }
    if construction["status"] != "ok":
        return record
    coefficients = coefficients_for_edges(construction["edges"], width,
                                          graph_seed)
    dense = dense_from_edges(cell["n"], cell["m"], construction["edges"],
                             coefficients)
    structure = structural_record(dense, cell["var_counts"],
                                  cell["check_counts"])
    replay = build_degree_sequence_peg(
        cell["n"], cell["m"], cell["var_counts"], cell["check_counts"],
        int(graph_seed))
    replay_coeffs = coefficients_for_edges(replay["edges"], width,
                                           graph_seed)
    replay_ok = bool(replay["status"] == "ok"
                     and replay["edges"] == construction["edges"]
                     and replay_coeffs == coefficients)
    structure["admission"]["A6_deterministic_replay"] = replay_ok
    structure["admitted"] = bool(all(structure["admission"].values()))
    failed = [name for name, ok in structure["admission"].items() if not ok]
    record.update({
        "E": len(construction["edges"]), "edges": construction["edges"],
        "coefficients": coefficients, "dense": dense, "structure": structure,
        "status": "ok", "admitted": bool(structure["admitted"]),
        "failure_reason": "" if structure["admitted"]
        else "admission failed: %s" % ",".join(failed),
    })
    return record


# --------------------------------------------------------------------------- #
# plan, classification, progression, terminals
# --------------------------------------------------------------------------- #
def build_call_plan(widths: Sequence[int] = WIDTHS
                    ) -> list[dict[str, Any]]:
    """Frozen paired call matrix: width -> control/candidate -> graph -> block.

    The full plan is 2 arms x 3 widths x 3 graph seeds x 8 blocks = 144 calls
    (48 per width) with contiguous ``call_idx`` over the execution order.
    """
    plan: list[dict[str, Any]] = []
    idx = 0
    for width in widths:
        width = int(width)
        for arm in ARMS:
            for graph_seed in GRAPH_SEEDS[width]:
                for block_seed in BLOCK_SEEDS[width]:
                    plan.append({
                        "call_idx": idx, "width": width, "arm": arm,
                        "graph_seed": int(graph_seed),
                        "block_seed": int(block_seed)})
                    idx += 1
    return plan


def classify_width(mix_counts: Sequence[Mapping[str, Any]],
                   dv3_counts: Sequence[Mapping[str, Any]],
                   engineering_reason: str = "") -> str:
    """Frozen per-width classification (design §6.2).

    ``mix_counts``/``dv3_counts`` are per-graph ``{"exact", "syndrome",
    "blocks"}`` mappings (3 graphs). Pooled counts alone are never sufficient;
    a single rescued block cannot satisfy the exact rule.
    """
    if engineering_reason:
        return ENGINEERING_BLOCKED
    mix_S = [int(c["syndrome"]) for c in mix_counts]
    mix_E = [int(c["exact"]) for c in mix_counts]
    dv3_S = sum(int(c["syndrome"]) for c in dv3_counts)
    dv3_E = sum(int(c["exact"]) for c in dv3_counts)
    S_pool, E_pool = sum(mix_S), sum(mix_E)
    reproducible = all(s >= 3 for s in mix_S)
    exact_multi = sum(1 for e in mix_E if e >= 2) >= 2
    pooled_ok = S_pool >= 12 and E_pool >= 6
    control_quiet = dv3_S <= 3 and dv3_E <= 1
    if reproducible and exact_multi and pooled_ok and control_quiet:
        return POSITIVE
    if E_pool <= 2 and S_pool <= 4:
        return NEGATIVE
    return AMBIGUOUS


def route_terminal(width_results: Sequence[Mapping[str, Any]],
                   planned_widths: Sequence[int] = WIDTHS) -> str:
    """Frozen terminal routing (design §6.4); ENGINEERING_BLOCKED overrides."""
    if not width_results:
        return T_NOT_RUN
    if any(str(r["classification"]) == ENGINEERING_BLOCKED
           for r in width_results):
        return T_ENGINEERING_BLOCKED
    last = width_results[-1]
    classification = str(last["classification"])
    if classification == POSITIVE:
        if int(last["width"]) == int(max(planned_widths)):
            return T_CANDIDATE_REPRODUCIBLE
        # A POSITIVE width continues progression; only a truncated plan can
        # stop here, which cannot claim reproducibility.
        return T_AMBIGUOUS
    if classification == NEGATIVE:
        if any(str(r["classification"]) == POSITIVE
               for r in width_results[:-1]):
            return T_FINITE_SIZE_SIGNAL
        return T_NO_MATERIAL_ADVANTAGE
    return T_AMBIGUOUS


# --------------------------------------------------------------------------- #
# dispatch and execution
# --------------------------------------------------------------------------- #
def dispatch_l1(graph: Mapping[str, Any], block: Mapping[str, Any],
                entry: Mapping[str, Any], decode_fn, syndrome_fn,
                *, call_idx: int) -> dict[str, Any]:
    """One L1 call with an injected decoder, gated before decoder binding.

    The R205 admission gate (A1–A6) is checked first: a graph that failed
    construction or any admission predicate raises ``StructureNotAdmitted``
    before the decoder adapter is constructed or called. ``decode_fn`` and
    ``syndrome_fn`` must be explicitly injected; this module never imports
    the production decoder. Decoder exceptions are retained as ``crash``
    records, never retried.
    """
    if graph.get("dense") is None or not bool(graph.get("admitted")):
        raise StructureNotAdmitted(
            "refusing decoder binding for non-admitted graph %r"
            % ({"arm": graph.get("arm"), "width": graph.get("width"),
                "graph_seed": graph.get("graph_seed")},))
    if decode_fn is None or not callable(decode_fn):
        raise ValueError("decode_fn must be explicitly injected")
    if syndrome_fn is None or not callable(syndrome_fn):
        raise ValueError("syndrome_fn must be explicitly injected")
    H = np.asarray(graph["dense"], dtype=np.uint8)
    u1 = np.asarray(block["u1"], dtype=np.int64)
    prior = np.asarray(block["prior"], dtype=np.float64)
    t0 = time.perf_counter()
    try:
        syn = np.asarray(syndrome_fn(H, u1), dtype=np.uint8)
        result = decode_fn(H, prior, syn, max_iter=DECODER_MAX_ITER,
                           damping_alpha=DAMPING_ALPHA, warm_beliefs=None,
                           field=None)
        x_hat = np.asarray(result.x_hat)
        syndrome_ok = bool(result.syndrome_ok)
        exact = bool(syndrome_ok and x_hat.shape == u1.shape
                     and np.array_equal(x_hat, u1))
        residual = int(np.count_nonzero(np.asarray(syndrome_fn(H, x_hat))
                                        != syn))
        return {
            "call_idx": int(call_idx), "width": int(entry["width"]),
            "arm": str(entry["arm"]), "graph_seed": int(entry["graph_seed"]),
            "block_seed": int(entry["block_seed"]),
            "exact": exact, "syndrome_ok": syndrome_ok,
            "iterations": int(result.iterations), "status": str(result.status),
            "residual_syndrome_weight": residual,
            "belief_provenance": getattr(result, "belief_provenance", None),
            "prior_mass_on_truth": float(np.mean(prior[np.arange(len(u1)),
                                                        u1])),
            "crash": False, "error": "",
            "wall_s": time.perf_counter() - t0,
        }
    except Exception as exc:  # retained crash record; never retried
        return {
            "call_idx": int(call_idx), "width": int(entry["width"]),
            "arm": str(entry["arm"]), "graph_seed": int(entry["graph_seed"]),
            "block_seed": int(entry["block_seed"]),
            "exact": False, "syndrome_ok": False, "iterations": -1,
            "status": "crash", "residual_syndrome_weight": -1,
            "belief_provenance": "", "prior_mass_on_truth":
                float(np.mean(prior[np.arange(len(u1)), u1])),
            "crash": True, "error": repr(exc)[:300],
            "wall_s": time.perf_counter() - t0,
        }


def _width_counts(records: Sequence[Mapping[str, Any]], width: int, arm: str
                  ) -> list[dict[str, Any]]:
    rows = [r for r in records
            if int(r["width"]) == int(width) and str(r["arm"]) == arm]
    out = []
    for graph_seed in GRAPH_SEEDS[int(width)]:
        graph_rows = [r for r in rows if int(r["graph_seed"]) == graph_seed]
        out.append({
            "graph_seed": int(graph_seed), "blocks": len(graph_rows),
            "exact": int(sum(1 for r in graph_rows if r["exact"])),
            "syndrome": int(sum(1 for r in graph_rows if r["syndrome_ok"])),
        })
    return out


def execute_plan(plan: Sequence[Mapping[str, Any]],
                 graphs: Mapping[Any, Mapping[str, Any]],
                 blocks: Mapping[int, Mapping[int, Mapping[str, Any]]],
                 decode_fn, syndrome_fn, *, now=None, rss_fn=None,
                 wall_budget_s: float = WALL_BUDGET_S,
                 per_call_budget_s: float = PER_CALL_BUDGET_S,
                 rss_budget_bytes: int = RSS_BUDGET_BYTES,
                 call_ceiling: int = SCIENTIFIC_CALL_CEILING
                 ) -> dict[str, Any]:
    """Execute the deterministic plan with paired identical blocks.

    Structural gates are re-checked for every graph of a width before its
    first call; a non-admitted graph engineering-blocks the width with no
    decoder dispatch (no replacement). Widths advance only under POSITIVE and
    stop otherwise. Budget and crash stops are recorded as engineering blocks;
    ``now``/``rss_fn`` are injectable and resource checks run between/after
    calls only (no in-flight watchdog).
    """
    now = now or time.monotonic
    t_batch = float(now())
    records: list[dict[str, Any]] = []
    width_results: list[dict[str, Any]] = []
    planned_widths: list[int] = []
    for entry in plan:
        if int(entry["width"]) not in planned_widths:
            planned_widths.append(int(entry["width"]))
    failure: str | None = None
    for width in planned_widths:
        width_plan = [e for e in plan if int(e["width"]) == width]
        required: list[tuple[str, int]] = []
        for entry in width_plan:
            key = (str(entry["arm"]), int(entry["graph_seed"]))
            if key not in required:
                required.append(key)
        failure = None
        for arm, graph_seed in required:
            graph = graphs.get((arm, width, graph_seed))
            if graph is None or not bool(graph.get("admitted")):
                failure = ("graph (arm=%s, width=%d, seed=%d) not admitted"
                           % (arm, width, graph_seed))
                break
        if failure is None:
            for entry in width_plan:
                if len(records) >= int(call_ceiling):
                    failure = "scientific L1 call ceiling reached"
                    break
                graph = graphs[(str(entry["arm"]), width,
                                int(entry["graph_seed"]))]
                block = blocks[width][int(entry["block_seed"])]
                call_t0 = float(now())
                record = dispatch_l1(graph, block, entry, decode_fn,
                                     syndrome_fn, call_idx=len(records))
                record["wall_s"] = max(float(now()) - call_t0, 0.0)
                records.append(record)
                if record["crash"]:
                    failure = "decoder crash: %s" % record["error"]
                elif float(record["wall_s"]) > float(per_call_budget_s):
                    failure = ("per-call wall budget exceeded: %.3f s"
                               % float(record["wall_s"]))
                elif float(now()) - t_batch > float(wall_budget_s):
                    failure = "wall budget exceeded"
                elif rss_fn is not None \
                        and int(rss_fn()) >= int(rss_budget_bytes):
                    failure = "RSS budget exceeded"
                if failure is not None:
                    break
        mix_counts = _width_counts(records, width, ARMS[1])
        dv3_counts = _width_counts(records, width, ARMS[0])
        classification = classify_width(mix_counts, dv3_counts,
                                        failure or "")
        width_results.append({
            "width": int(width), "classification": classification,
            "mix_counts": mix_counts, "dv3_counts": dv3_counts,
            "engineering_reason": failure or "",
        })
        if failure is not None:
            break
        if classification != POSITIVE:
            break
    return {
        "records": records,
        "width_results": width_results,
        "terminal": route_terminal(width_results, planned_widths),
        "stop_reason": (width_results[-1]["engineering_reason"]
                        if width_results
                        and width_results[-1]["classification"]
                        == ENGINEERING_BLOCKED
                        else ("progression complete" if width_results
                              else "empty plan")),
    }


# --------------------------------------------------------------------------- #
# R210 pre-decoder profile (real builders; no decoder, no root, no reseed)
# --------------------------------------------------------------------------- #
def _profile_entry(graph: Mapping[str, Any], seed: int, wall_s: float
                   ) -> dict[str, Any]:
    entry = {
        "width": int(graph["width"]), "arm": str(graph["arm"]),
        "seed": int(seed), "status": str(graph["status"]),
        "admitted": bool(graph["admitted"]),
        "construction_wall_s": round(float(wall_s), 6),
        "failure_reason": str(graph["failure_reason"]),
    }
    structure = graph.get("structure")
    if structure:
        entry.update({
            "rank": int(structure["rank"]),
            "structural_rank": int(structure["structural_rank"]),
            "gf32_rank": int(structure["gf32_rank"]),
            "admission": {str(k): bool(v)
                          for k, v in structure["admission"].items()},
            "connected_components": int(structure["connected_components"]),
            "largest_component_fraction":
                float(structure["largest_component_fraction"]),
            "min_check_degree": int(structure["min_check_degree"]),
            "degree2_N2": int(structure["degree2"]["N2"]),
            "degree2_cycle_rank_lower_bound":
                int(structure["degree2"]["cycle_rank_lower_bound"]),
            "four_cycles": int(structure["four_cycles"]),
            "girth": structure["girth"],
            "girth_reason": str(structure["girth_reason"]),
        })
    return entry


def profile_graphs(build_fn=None, now=None) -> dict[str, Any]:
    """Bounded R210 profile: build all 18 frozen graphs, no decoder, no root.

    Records per cell the component count, largest-component fraction,
    structural rank, GF32 rank, four-cycle count, girth and wall time, plus
    the A1–A6 admission outcome. A frozen seed that cannot produce an
    admitted graph is retained as-is; no replacement seed exists or is
    consumed (zero replacement seeds by construction).
    """
    build_fn = build_fn or build_graph
    now = now or time.perf_counter
    t0 = float(now())
    entries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for width in WIDTHS:
        for arm in ARMS:
            for graph_seed in GRAPH_SEEDS[width]:
                start = float(now())
                graph = build_fn(arm, width, graph_seed)
                wall = float(now()) - start
                entries.append(_profile_entry(graph, graph_seed, wall))
                if graph["status"] == "construction_failed" \
                        or not graph["admitted"]:
                    failures.append({
                        "width": int(width), "arm": arm,
                        "seed": int(graph_seed),
                        "status": str(graph["status"]),
                        "admitted": bool(graph["admitted"]),
                        "failure_reason": str(graph["failure_reason"])})
    return {
        "graphs": entries,
        "seed_replacements": [],
        "replacement_seeds_used": 0,
        "frozen_seed_failures": failures,
        "wall_s": float(now()) - t0,
    }


# --------------------------------------------------------------------------- #
# root refusal
# --------------------------------------------------------------------------- #
def refuse_out_root(out_root) -> Any:
    """Refuse protected roots and any existing root; return the resolved path."""
    root = Path(__file__).resolve().parents[4]
    path = Path(out_root)
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    if resolved.is_relative_to(root):
        for name in resolved.relative_to(root).parts:
            if name.startswith(PROTECTED_NAME_PREFIXES):
                raise ValueError("refusing protected root %s" % resolved)
    for subtree in PROTECTED_SUBTREES:
        anchor = (root / subtree).resolve()
        if resolved == anchor or anchor in resolved.parents:
            raise ValueError("refusing protected root %s" % resolved)
    if resolved.exists():
        raise FileExistsError("refusing to overwrite existing root %s"
                              % resolved)
    return resolved
