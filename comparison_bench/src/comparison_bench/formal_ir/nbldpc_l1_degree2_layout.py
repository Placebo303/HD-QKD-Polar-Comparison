"""NB-LDPC L1 degree-2-directed layout — Stage-1 frozen bundle.

Change: ``add-nbldpc-l1-degree2-layout``
Stage-1 is implementation-only: construction + schema + fake-only checks.
Zero scientific decoder calls, zero benchmark/sweep/replay, zero real-data
contact. Frozen authority: ``openspec/changes/add-nbldpc-l1-degree2-layout/``
(``proposal.md``, ``design.md`` §1–§8, ``tasks.md``, delta spec).

Contents:

- ``l055_degree_cell``: frozen L055 ``(n, m, var_counts, check_counts)`` cells
  (n128: n2=83/n3=45/E=301/checks 2^53+3^65/m=118; n256: n2=166/n3=90/E=602/
  checks 2^106+3^130/m=236).
- ``build_d2_directed_peg``: candidate constructor. Phase A is the IDENTICAL
  seeded spanning backbone of the accepted ``r2.build_degree_sequence_peg``
  (same ``_backbone_seed`` namespace, same seeded permutations, same attach
  rule), so equal seeds share the backbone. Phase B diverges only here: d3
  sockets first (index order, shared PEG/ACE rule verbatim), then d2 sockets
  last in seeded-permutation order
  (``v10_seed("nbldpc-l1-d2order:{seed}")``) with the frozen directed
  priority: unreachable cycle-free merges first (shared capacity/tie rule);
  among reachable candidates max BFS depth, then min d2 short-cycle
  participation (``four`` = 4-cycles the edge would close whose opposite
  variable is degree-2; ``six`` = 6-cycles through the edge touching another
  degree-2 variable), then max ACE (shared ``_ace_score``), then the seeded
  tie-break (shared ``_tie_pick``). One attempt per seed; any parallel edge,
  overshoot, socket mismatch or dead end returns
  ``status="construction_failed"`` with no partial graph and no seed change.
  Same seed gives the same sorted edge table (A6 replay).
- ``build_control_l1`` / ``build_candidate_l1``: L055 graph records with
  A1–A6 admission owned by ``r2.structural_record`` plus edge/coefficient
  replay equality (no new predicates; four-cycle/girth/ACE stay diagnostics).
- Coefficients/matrix conversion: ALIASED from ``r2`` (frozen
  ``d10:coeff:{width}:{graph_seed}`` stream, sorted ``(v, c)`` order, one
  ``integers(1, 32)`` per edge). Pairing ceiling: control/candidate edge sets
  differ, so the shared stream rule yields same-distribution,
  sorted-position-paired draws, not socket-identity pairing.
- GF32/symbol helpers: ``gf32_add``/``gf32_mul`` (pinned GF(32)/poly-37 field
  tables), ``gf32_syndrome``/``syndrome_ok`` (same arithmetic as the frozen
  syndrome), ``symbols_to_layers``/``layers_to_symbols`` (delegated to
  ``d5``), ``disclosure_bits`` (5 bits per GF32 row + additive fields),
  ``classify_frame``/``is_success`` (F-4 schema reservation; ``accepted_wrong``
  isolated, never merged into success; ``resource_abort`` never success).
- ``RESULT_SCHEMA_COLUMNS`` / ``STATUS_VALUES``: frozen Stage-2 record
  reservation (no data produced in Stage-1).
- ``profile_graphs``: bounded PROFILE_ONLY pre-decoder construction over the
  frozen ``GRAPH_SEEDS`` (no decoder, no root, no replacement).

This module never imports the production decoder.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from numbers import Integral
from typing import Any

import numpy as np

from . import nonbinary_v10_common as common
from . import nonbinary_v10_peg as v10peg
from . import v72p2d5_gf32_rate_mother as d5
from . import v72p2d10_mixed_degree_l1 as r2
from .nonbinary_field import GF2mField

__all__ = [
    "CHANGE_ID", "CYCLE_ID", "TRACK", "CLAIM_CEILING",
    "Q", "POLY", "DECODER_MAX_ITER", "DAMPING_ALPHA",
    "WIDTHS", "ARMS", "CONTROL_ARM", "CANDIDATE_ARM",
    "L055_DEGREE_TABLE", "GRAPH_SEEDS", "L2_GRAPH_SEED_MAP",
    "RESULT_SCHEMA_COLUMNS", "STATUS_VALUES",
    "structural_record", "structural_rank", "gf32_row_rank",
    "coefficient_seed", "coefficients_for_edges", "dense_from_edges",
    "refuse_out_root",
    "l055_degree_cell", "d2_order", "d2_cycle_participation",
    "build_d2_directed_peg", "build_control_l1", "build_candidate_l1",
    "gf32_add", "gf32_mul", "gf32_syndrome", "syndrome_ok",
    "symbols_to_layers", "layers_to_symbols",
    "disclosure_bits", "classify_frame", "is_success",
    "profile_graphs",
]

CHANGE_ID = "add-nbldpc-l1-degree2-layout"
CYCLE_ID = "NBLDPC-PARALLEL-STRUCTURED-RECOVERY-DRAFT/R1"
TRACK = "implementation-only"
CLAIM_CEILING = (
    "frozen construction bundle only; no FER, leakage, SKR, qualification, "
    "promotion, publication, real-data or optimality claim"
)

Q = 32
POLY = 37
DECODER_MAX_ITER = r2.DECODER_MAX_ITER
DAMPING_ALPHA = r2.DAMPING_ALPHA

WIDTHS = (128, 256)
CONTROL_ARM = "CONTROL_L055_PEG"
CANDIDATE_ARM = "CANDIDATE_L055_D2DIR"
ARMS = (CONTROL_ARM, CANDIDATE_ARM)

#: Frozen L055 f1.2 realizations (transcribed from D12 degree_cell).
L055_DEGREE_TABLE = {
    128: {"n": 128, "m": 118, "var_counts": {2: 83, 3: 45},
          "check_counts": {2: 53, 3: 65}},
    256: {"n": 256, "m": 236, "var_counts": {2: 166, 3: 90},
          "check_counts": {2: 106, 3: 130}},
}

#: Frozen PROFILE_ONLY graph seeds (Stage-1; never searched or replaced).
#: Fresh namespace 20260937xx in the idle gap 2026093613..2026093800
#: (D14N block ends 3612, D15 graph starts 3801). The 40xx/41xx range is
#: abandoned: it collides with D16 (graphs 4001-4012 / blocks 4101-4108).
GRAPH_SEEDS = {
    128: (2026093701, 2026093702, 2026093703,
          2026093704, 2026093705, 2026093706),
    256: (2026093711, 2026093712, 2026093713,
          2026093714, 2026093715, 2026093716),
}

#: Frozen Stage-2 L2 1-1 rotation (new seeds, reordered): n128 3701-3706 map
#: to D11-L2 graphs 2801-2806; n256 3711-3716 map to 2901-2906. Keys/values
#: are full 8-digit seeds.
L2_GRAPH_SEED_MAP = {
    2026093701: 2026092801,
    2026093702: 2026092802,
    2026093703: 2026092803,
    2026093704: 2026092804,
    2026093705: 2026092805,
    2026093706: 2026092806,
    2026093711: 2026092901,
    2026093712: 2026092902,
    2026093713: 2026092903,
    2026093714: 2026092904,
    2026093715: 2026092905,
    2026093716: 2026092906,
}

_PRIOR_GRAPH_SEEDS = (
    {s for seeds in r2.GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in r2.BLOCK_SEEDS.values() for s in seeds})
try:
    from . import v72p2d10_r3_fresh_scaling as _r3
    _PRIOR_GRAPH_SEEDS |= {s for seeds in _r3.GRAPH_SEEDS.values()
                           for s in seeds}
    _PRIOR_GRAPH_SEEDS |= {s for seeds in _r3.BLOCK_SEEDS.values()
                           for s in seeds}
    del _r3
except ImportError:
    pass
try:
    from . import v72p2d11_forward_app as _d11
    _PRIOR_GRAPH_SEEDS |= {s for seeds in _d11.L2_GRAPH_SEEDS.values()
                           for s in seeds}
    del _d11
except ImportError:
    pass
try:
    from . import v72p2d12_finite_l1_degree as _d12
    _PRIOR_GRAPH_SEEDS |= {s for seeds in _d12.GRAPH_SEEDS.values()
                           for s in seeds}
    _PRIOR_GRAPH_SEEDS |= {s for seeds in _d12.BLOCK_SEEDS.values()
                           for s in seeds}
    del _d12
except ImportError:
    pass


def _prior_range(lo: int, hi: int) -> set[int]:
    """Expand an inclusive 4-digit suffix range to full 8-digit seeds."""
    return {2026090000 + s for s in range(int(lo), int(hi) + 1)}


# Integer-domain full prior set (fail-closed at import; a collision raises
# ValueError). Ranges are inclusive 4-digit suffixes; each is expanded with
# the 202609 prefix before comparison so magnitudes match.
for _lo, _hi in (
    # R2 graphs / blocks
    (2201, 2209), (2301, 2308), (2311, 2318), (2321, 2328),
    # R3 graphs / blocks
    (2401, 2406), (2501, 2506), (2601, 2612), (2701, 2712),
    # D11 L2 graphs (D11 L1 reuses R3)
    (2801, 2806), (2901, 2906),
    # D12 graphs / blocks (D13 reuses D12)
    (3001, 3006), (3101, 3106), (3201, 3212), (3301, 3312),
    # D14N L1 / L2 / blocks
    (3401, 3406), (3501, 3506), (3601, 3612),
    # D15 graphs / blocks
    (3801, 3836), (3901, 3908),
    # D16 graphs / blocks (this module's 40xx/41xx collision source)
    (4001, 4012), (4101, 4108),
    # D17 (4200 single handled below) / D18
    (4201, 4208), (4301, 4308),
    # D19 graphs / blocks
    (4401, 4412), (4501, 4508), (4511, 4518),
    # G6/R7
    (4601, 4602), (4701, 4708), (4711, 4723),
    # R23 graphs / blocks / weak blocks
    (4801, 4816), (4831, 4884), (4885, 4948),
    # S1
    (4951, 4952),
    # V80 large intervals
    (5501, 5560), (5601, 5840), (6401, 6640),
    (7001, 7440), (7501, 7564),
    # Early literals (0501-0502 -> 501-502, 0510-0517 -> 510-517)
    (501, 502), (510, 517), (1300, 1315),
    (1601, 1603), (1801, 1805),
):
    _PRIOR_GRAPH_SEEDS |= _prior_range(_lo, _hi)
del _lo, _hi
# Single-point priors (same 202609 prefix).
_PRIOR_GRAPH_SEEDS |= {2026090000 + s for s in (
    4200,  # D17
    5001, 8001, 9001,  # CLI literals
    2001, 2011, 6801, 6811,  # V80 singles
    1401, 1501, 1727,  # early literals
)}
_MINE = {s for seeds in GRAPH_SEEDS.values() for s in seeds}
if len(_MINE) != 12:
    raise ValueError("frozen GRAPH_SEEDS must hold exactly 12 seeds")
if not _MINE.isdisjoint(_PRIOR_GRAPH_SEEDS):
    raise ValueError("frozen GRAPH_SEEDS collide with a prior seed set")
if set(L2_GRAPH_SEED_MAP) != _MINE:
    raise ValueError("L2_GRAPH_SEED_MAP keys must equal GRAPH_SEEDS set")
del _PRIOR_GRAPH_SEEDS, _MINE, _prior_range

#: Frozen Stage-2 output schema reservation (order frozen; no data in Stage-1).
RESULT_SCHEMA_COLUMNS = (
    "u1_exact", "u2_exact", "pair_exact",
    "syn_l1", "syn_l2", "syn_joint",
    "verify_accept", "accepted_wrong",
    "status",
    "l1_syn_bits", "l2_syn_bits", "extra_parity_bits",
    "verify_tag_bits", "other_public_bits",
    "rounds", "wall_s", "rss_b",
)
STATUS_VALUES = ("ok", "nonconverged", "resource_abort")

#: Reuse aliases (IMPORT — no duplication of admission/coefficient semantics).
structural_record = r2.structural_record
structural_rank = r2.structural_rank
gf32_row_rank = r2.gf32_row_rank
coefficient_seed = r2.coefficient_seed
coefficients_for_edges = r2.coefficients_for_edges
dense_from_edges = r2.dense_from_edges
refuse_out_root = r2.refuse_out_root

_FIELD = GF2mField.create(32)


# --------------------------------------------------------------------------- #
# L055 degree cells
# --------------------------------------------------------------------------- #
def l055_degree_cell(width: int) -> dict[str, Any]:
    """Return the frozen L055 ``(n, m, var_counts, check_counts)`` cell."""
    width = int(width)
    if width not in L055_DEGREE_TABLE:
        raise KeyError("unknown L055 width %r" % (width,))
    cell = L055_DEGREE_TABLE[width]
    var_sockets = sum(int(d) * int(c) for d, c in cell["var_counts"].items())
    check_sockets = sum(int(d) * int(c)
                        for d, c in cell["check_counts"].items())
    if sum(cell["var_counts"].values()) != cell["n"]:
        raise ValueError("frozen L055 cell variable counts do not sum to n")
    if sum(cell["check_counts"].values()) != cell["m"]:
        raise ValueError("frozen L055 cell check counts do not sum to m")
    if var_sockets != check_sockets:
        raise ValueError("frozen L055 cell socket mismatch")
    return {"n": int(cell["n"]), "m": int(cell["m"]),
            "var_counts": dict(cell["var_counts"]),
            "check_counts": dict(cell["check_counts"]), "E": var_sockets}


def _validate_counts(counts: Mapping[Any, Any], total: int,
                     side: str) -> dict[int, int]:
    if not isinstance(counts, Mapping) or not counts:
        raise ValueError("%s degree counts must be a non-empty mapping" % side)
    out: dict[int, int] = {}
    for degree, count in counts.items():
        if isinstance(degree, bool) or not isinstance(degree, Integral) \
                or int(degree) < 2:
            raise ValueError("%s degrees must be integers >= 2" % side)
        if isinstance(count, bool) or not isinstance(count, Integral) \
                or int(count) < 1:
            raise ValueError("%s degree counts must be positive integers"
                             % side)
        out[int(degree)] = int(count)
    if sum(out.values()) != int(total):
        raise ValueError("%s degree counts do not sum to %d"
                         % (side, int(total)))
    return out


# --------------------------------------------------------------------------- #
# d2 order + d2 short-cycle participation (frozen §3)
# --------------------------------------------------------------------------- #
def d2_order(seed: int, d2_vars: Sequence[int]) -> list[int]:
    """Seeded permutation order for delayed degree-2 placement.

    Derived from ``v10_seed("nbldpc-l1-d2order:{seed}")``; deterministic in
    the seed. The candidate places d3 sockets first (index order) and d2
    sockets last in this order.
    """
    order = sorted(int(v) for v in d2_vars)
    rng = np.random.default_rng(
        common.v10_seed("nbldpc-l1-d2order:%d" % int(seed)))
    return [int(v) for v in rng.permutation(order)] if order else []


def d2_cycle_participation(variable: int, check: int, n: int,
                           var_adj: Mapping[int, Sequence[int]],
                           check_adj: Mapping[int, Sequence[int]],
                           var_degree_of: Mapping[int, int]
                           ) -> tuple[int, int]:
    """Count short cycles a candidate edge would close via degree-2 nodes.

    ``four``: 4-cycles ``v-c-v'-c'`` closed by the edge whose opposite
    variable ``v'`` is degree-2 (d2–d2 loop proxy).
    ``six``: 6-cycles ``v-c'-v'-c''-v''-c`` closed by the edge that touch at
    least one degree-2 variable other than ``v`` itself.
    Both are exact enumerations over the current (small-degree) adjacency;
    deterministic. A parallel edge (``check`` already adjacent) reports
    ``(0, 0)`` — the caller refuses parallel edges before ranking.
    """
    variable, check = int(variable), int(check)
    node_c = n + check
    if node_c in set(var_adj.get(variable, ())):
        return (0, 0)
    d2 = {v for v in range(n) if int(var_degree_of[v]) == 2}

    def neighbours(node: int) -> tuple[int, ...]:
        if node < n:
            return tuple(int(x) for x in var_adj.get(node, ()))
        return tuple(int(x) for x in check_adj.get(node, ()))

    # 4-cycles: pairs (c' in N(v), v' in N(c)) with v' adjacent c'.
    four = 0
    n_v = set(neighbours(variable))
    n_c = set(neighbours(node_c))
    for c_node in n_v:
        for v2 in n_c:
            if v2 == variable:
                continue
            if c_node in set(neighbours(v2)) and v2 in d2:
                four += 1

    # 6-cycles: paths v-c'-v'-c''-v'' with v'' in N(c), all nodes distinct,
    # touching a d2 variable other than v.
    six = 0
    seen: set[tuple[int, int, int]] = set()
    for c1 in n_v:
        for v1 in neighbours(c1):
            if v1 == variable:
                continue
            for c2 in neighbours(v1):
                if c2 == c1:
                    continue
                for v2 in neighbours(c2):
                    if v2 in (variable, v1):
                        continue
                    if v2 not in n_c:
                        continue
                    key = (int(v1), int(c2), int(v2))
                    if key in seen:
                        continue
                    seen.add(key)
                    if v1 in d2 or v2 in d2:
                        six += 1
    return (int(four), int(six))


# --------------------------------------------------------------------------- #
# Candidate constructor (F-1)
# --------------------------------------------------------------------------- #
def _backbone_seed(seed: int) -> int:
    """Seeded backbone namespace (identical to the accepted R2 rule)."""
    return int(common.v10_seed("d10:backbone:%d" % int(seed)))


def build_d2_directed_peg(n: int, m: int, var_counts: Mapping[Any, Any],
                          check_counts: Mapping[Any, Any], seed: int
                          ) -> dict[str, Any]:
    """Degree-2-directed PEG honoring exact variable/check degree counts.

    Phase A is the accepted R2 spanning backbone verbatim (seeded path over
    all ``n+m`` Tanner nodes plus one seeded max-capacity attachment per
    leftover variable). Phase B places degree-3 sockets first in index order
    with the shared PEG/ACE rule, then degree-2 sockets last in
    ``d2_order`` with the frozen directed priority (design §3): unreachable
    cycle-free merges first (shared capacity/tie rule); among reachable
    candidates max BFS depth, then min d2-cycle participation ``(four, six)``,
    then max ACE, then the seeded tie-break. One attempt per seed; any
    parallel edge, overshoot, socket mismatch or dead end returns
    ``status="construction_failed"`` with no partial graph and no seed change.
    """
    if isinstance(n, bool) or not isinstance(n, Integral) or int(n) < 1:
        raise ValueError("n must be a positive integer")
    if isinstance(m, bool) or not isinstance(m, Integral) or int(m) < 1:
        raise ValueError("m must be a positive integer")
    if isinstance(seed, bool) or not isinstance(seed, Integral):
        raise ValueError("seed must be an integer")
    n, m, seed = int(n), int(m), int(seed)
    var = _validate_counts(var_counts, n, "variable")
    chk = _validate_counts(check_counts, m, "check")
    total_sockets = sum(d * c for d, c in var.items())
    if sum(d * c for d, c in chk.items()) != total_sockets:
        raise ValueError("socket mismatch: variable sockets != check sockets")

    var_degree_list: list[int] = []
    for degree in sorted(var, reverse=True):
        var_degree_list.extend([int(degree)] * int(var[degree]))
    check_degree_list: list[int] = []
    for degree in sorted(chk, reverse=True):
        check_degree_list.extend([int(degree)] * int(chk[degree]))
    var_degree_of = {v: var_degree_list[v] for v in range(n)}
    check_degree_of = {c: check_degree_list[c] for c in range(m)}
    d2_vars = [v for v in range(n) if var_degree_of[v] == 2]
    d3_vars = [v for v in range(n) if var_degree_of[v] != 2]

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

    # Phase A — accepted R2 backbone verbatim.
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

    def _bfs_from(variable: int
                  ) -> tuple[dict[int, int], dict[int, int | None]]:
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
        return distances, parents

    def _shared_pick(variable: int, socket: int,
                     candidates: Sequence[int],
                     distances: Mapping[int, int],
                     parents: Mapping[int, int | None]) -> int:
        reachable = [c for c in candidates if check_node(c) in distances]
        if not reachable:
            best_free = max(check_free[c] for c in candidates)
            group = [c for c in candidates if check_free[c] == best_free]
            if len(group) == 1:
                return int(group[0])
            group.sort()
            return int(v10peg._tie_pick(seed, variable, socket, group))
        max_depth = max(distances[check_node(c)] for c in reachable)
        group = [c for c in reachable
                 if distances[check_node(c)] == max_depth]
        if len(group) > 1:
            scores = {
                c: v10peg._ace_score(variable, check_node(c), parents,
                                     distances, var_degree_of,
                                     check_degree_of, n)
                for c in group}
            best = max(scores.values())
            group = [c for c in group if scores[c] == best]
        if len(group) == 1:
            return int(group[0])
        group.sort()
        return int(v10peg._tie_pick(seed, variable, socket, group))

    def _directed_pick(variable: int, socket: int,
                       candidates: Sequence[int],
                       distances: Mapping[int, int],
                       parents: Mapping[int, int | None]) -> int:
        unreachable = [c for c in candidates
                       if check_node(c) not in distances]
        if unreachable:
            best_free = max(check_free[c] for c in unreachable)
            group = [c for c in unreachable if check_free[c] == best_free]
            if len(group) == 1:
                return int(group[0])
            group.sort()
            return int(v10peg._tie_pick(seed, variable, socket, group))
        reachable = [c for c in candidates if check_node(c) in distances]
        if not reachable:
            best_free = max(check_free[c] for c in candidates)
            group = [c for c in candidates if check_free[c] == best_free]
            if len(group) == 1:
                return int(group[0])
            group.sort()
            return int(v10peg._tie_pick(seed, variable, socket, group))
        max_depth = max(distances[check_node(c)] for c in reachable)
        group = [c for c in reachable
                 if distances[check_node(c)] == max_depth]
        if len(group) > 1:
            parts = {c: d2_cycle_participation(
                variable, c, n, var_adj, check_adj, var_degree_of)
                for c in group}
            best_part = min(parts.values())
            group = [c for c in group if parts[c] == best_part]
        if len(group) > 1:
            scores = {
                c: v10peg._ace_score(variable, check_node(c), parents,
                                     distances, var_degree_of,
                                     check_degree_of, n)
                for c in group}
            best = max(scores.values())
            group = [c for c in group if scores[c] == best]
        if len(group) == 1:
            return int(group[0])
        group.sort()
        return int(v10peg._tie_pick(seed, variable, socket, group))

    def _select(variable: int, socket: int, directed: bool) -> int | None:
        free = [c for c in range(m) if check_free[c] > 0]
        if not free:
            return None
        existing = set(var_adj[variable])
        candidates = [c for c in free if check_node(c) not in existing]
        if not candidates:
            return None
        if not var_adj[variable]:
            best_free = max(check_free[c] for c in candidates)
            group = [c for c in candidates if check_free[c] == best_free]
            if len(group) == 1:
                return int(group[0])
            group.sort()
            return int(v10peg._tie_pick(seed, variable, socket, group))
        distances, parents = _bfs_from(variable)
        if directed:
            return _directed_pick(variable, socket, candidates, distances,
                                  parents)
        return _shared_pick(variable, socket, candidates, distances, parents)

    # Phase B1 — d3 sockets first (shared rule); B2 — d2 sockets last
    # (seeded-permutation order, directed rule).
    failed_at: dict[str, int] | None = None
    if not failed:
        for variable in d3_vars:
            while used_var[variable] < var_degree_of[variable]:
                socket = int(used_var[variable])
                check = _select(variable, socket, directed=False)
                if check is None:
                    failed_at = {"variable": int(variable), "socket": socket}
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
                if not add_edge(variable, int(check), "fill d3"):
                    break
            if failed_at is not None or failure_reason:
                break
    if not failed and failed_at is None and not failure_reason:
        for variable in d2_order(seed, d2_vars):
            while used_var[variable] < var_degree_of[variable]:
                socket = int(used_var[variable])
                check = _select(variable, socket, directed=True)
                if check is None:
                    failed_at = {"variable": int(variable), "socket": socket}
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
                if not add_edge(variable, int(check), "fill d2"):
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
# Graph records (A1–A6 owned by r2; no new predicates)
# --------------------------------------------------------------------------- #
def _admit(width: int, arm: str, graph_seed: int,
           construction: Mapping[str, Any], cell: Mapping[str, Any]
           ) -> dict[str, Any]:
    record: dict[str, Any] = {
        "arm": str(arm), "width": int(width),
        "graph_seed": int(graph_seed),
        "n": cell["n"], "m": cell["m"], "E": 0, "edges": [],
        "coefficients": [], "dense": None, "structure": None,
        "status": "construction_failed", "admitted": False,
        "failure_reason": str(construction.get("failure_reason", "")),
    }
    if construction["status"] != "ok":
        return record
    coefficients = r2.coefficients_for_edges(construction["edges"],
                                            int(width), int(graph_seed))
    dense = r2.dense_from_edges(cell["n"], cell["m"],
                                construction["edges"], coefficients)
    structure = r2.structural_record(dense, cell["var_counts"],
                                     cell["check_counts"])
    structure["admission"]["A6_deterministic_replay"] = False
    structure["admitted"] = False
    record.update({
        "E": len(construction["edges"]), "edges": construction["edges"],
        "coefficients": coefficients, "dense": dense,
        "structure": structure, "status": "ok",
    })
    return record


def _replay_ok(build_fn, cell: Mapping[str, Any], width: int,
               graph_seed: int, edges: Sequence[Sequence[int]],
               coefficients: Sequence[int]) -> bool:
    replay = build_fn(cell["n"], cell["m"], cell["var_counts"],
                      cell["check_counts"], int(graph_seed))
    replay_coeffs = r2.coefficients_for_edges(replay["edges"], int(width),
                                              int(graph_seed))
    return bool(replay["status"] == "ok"
                and list(replay["edges"]) == list(edges)
                and list(replay_coeffs) == list(coefficients))


def build_control_l1(width: int, graph_seed: int) -> dict[str, Any]:
    """Build one control (existing degree-sequence PEG) L055 graph record."""
    cell = l055_degree_cell(width)
    construction = r2.build_degree_sequence_peg(
        cell["n"], cell["m"], cell["var_counts"], cell["check_counts"],
        int(graph_seed))
    record = _admit(width, CONTROL_ARM, graph_seed, construction, cell)
    if record["status"] != "ok":
        return record
    replay_ok = _replay_ok(r2.build_degree_sequence_peg, cell, width,
                           graph_seed, record["edges"],
                           record["coefficients"])
    record["structure"]["admission"]["A6_deterministic_replay"] = replay_ok
    record["structure"]["admitted"] = bool(
        all(record["structure"]["admission"].values()))
    failed = [k for k, v in record["structure"]["admission"].items()
              if not v]
    record["admitted"] = bool(record["structure"]["admitted"])
    record["failure_reason"] = "" if record["admitted"] \
        else "admission failed: %s" % ",".join(failed)
    return record


def build_candidate_l1(width: int, graph_seed: int) -> dict[str, Any]:
    """Build one candidate (d2-directed) L055 graph record.

    Same L055 cell, same frozen coefficient rule and same A1–A6 admission as
    the control; only the Phase-B layout differs (design §3).
    """
    cell = l055_degree_cell(width)
    construction = build_d2_directed_peg(
        cell["n"], cell["m"], cell["var_counts"], cell["check_counts"],
        int(graph_seed))
    record = _admit(width, CANDIDATE_ARM, graph_seed, construction, cell)
    if record["status"] != "ok":
        return record
    replay_ok = _replay_ok(build_d2_directed_peg, cell, width, graph_seed,
                           record["edges"], record["coefficients"])
    record["structure"]["admission"]["A6_deterministic_replay"] = replay_ok
    record["structure"]["admitted"] = bool(
        all(record["structure"]["admission"].values()))
    failed = [k for k, v in record["structure"]["admission"].items()
              if not v]
    record["admitted"] = bool(record["structure"]["admitted"])
    record["failure_reason"] = "" if record["admitted"] \
        else "admission failed: %s" % ",".join(failed)
    return record


# --------------------------------------------------------------------------- #
# GF32 / symbol-mapping wrappers (same pinned arithmetic as the frozen path)
# --------------------------------------------------------------------------- #
def gf32_add(a: int, b: int) -> int:
    """GF(32)/poly-37 addition (XOR)."""
    return int(_FIELD.add(int(a), int(b)))


def gf32_mul(a: int, b: int) -> int:
    """GF(32)/poly-37 multiplication (pinned field tables)."""
    return int(_FIELD.mul(int(a), int(b)))


def gf32_syndrome(dense: Any, word: Any) -> list[int]:
    """Syndrome vector of a symbol word under a dense GF32 matrix."""
    h = np.asarray(dense, dtype=np.int64)
    x = np.asarray(word, dtype=np.int64).ravel()
    if h.ndim != 2 or x.shape != (h.shape[1],):
        raise ValueError("word length must match matrix width")
    out: list[int] = []
    for row in range(h.shape[0]):
        acc = 0
        for col in np.flatnonzero(h[row]):
            acc = _FIELD.add(acc, _FIELD.mul(int(h[row, col]),
                                             int(x[col])))
        out.append(int(acc))
    return out


def syndrome_ok(dense: Any, word: Any, syndrome: Any) -> bool:
    """True iff the word's syndrome equals the reference syndrome."""
    return list(int(v) for v in np.asarray(syndrome).ravel()) == \
        gf32_syndrome(dense, word)


def symbols_to_layers(symbols: Any) -> tuple[Any, Any]:
    """Split full symbols ``A`` into ``(U1, U2)`` (delegated to ``d5``)."""
    return d5.symbols_to_layers(symbols)


def layers_to_symbols(u1: Any, u2: Any) -> Any:
    """Join ``(U1, U2)`` into full symbols ``A`` (delegated to ``d5``)."""
    return d5.layers_to_symbols(u1, u2)


# --------------------------------------------------------------------------- #
# F-4 schema reservation: disclosure + frame classification (no data in S1)
# --------------------------------------------------------------------------- #
def disclosure_bits(m1: int, m2: int, extra_parity_bits: int = 0,
                    verify_tag_bits: int = 0,
                    other_public_bits: int = 0) -> dict[str, int]:
    """Public-cost decomposition for one frame (attempted frames included).

    GF32 rows disclose one full symbol (5 bits) each: ``l1_syn_bits = 5*m1``,
    ``l2_syn_bits = 5*m2``. Failed/aborted frames keep their sent messages on
    the ledger (no refund).
    """
    for name, value in (("m1", m1), ("m2", m2),
                        ("extra_parity_bits", extra_parity_bits),
                        ("verify_tag_bits", verify_tag_bits),
                        ("other_public_bits", other_public_bits)):
        if isinstance(value, bool) or not isinstance(value, Integral) \
                or int(value) < 0:
            raise ValueError("%s must be a nonnegative integer" % name)
    l1 = 5 * int(m1)
    l2 = 5 * int(m2)
    total = l1 + l2 + int(extra_parity_bits) + int(verify_tag_bits) \
        + int(other_public_bits)
    return {"l1_syn_bits": l1, "l2_syn_bits": l2,
            "extra_parity_bits": int(extra_parity_bits),
            "verify_tag_bits": int(verify_tag_bits),
            "other_public_bits": int(other_public_bits),
            "total_public_bits": total}


def classify_frame(*, u1_exact: bool, u2_exact: bool,
                   syn_l1: bool, syn_l2: bool, verify_accept: bool,
                   status: str, disclosure: Mapping[str, int] | None = None,
                   rounds: int = 0, wall_s: float = 0.0,
                   rss_b: int | None = None) -> dict[str, Any]:
    """Classify one frame into the frozen F-4 record (schema only).

    ``pair_exact`` = ``u1_exact and u2_exact``; ``syn_joint`` = ``syn_l1 and
    syn_l2``; ``accepted_wrong`` (undetected) = ``verify_accept and not
    pair_exact`` — isolated in its own column, never merged into success.
    ``status`` ∈ {``ok``, ``nonconverged``, ``resource_abort``}; a
    ``resource_abort`` is never success and never zero-failure.
    """
    if status not in STATUS_VALUES:
        raise ValueError("unknown frame status %r" % (status,))
    pair = bool(u1_exact and u2_exact)
    accepted_wrong = bool(verify_accept and not pair)
    rec: dict[str, Any] = {
        "u1_exact": bool(u1_exact), "u2_exact": bool(u2_exact),
        "pair_exact": pair,
        "syn_l1": bool(syn_l1), "syn_l2": bool(syn_l2),
        "syn_joint": bool(syn_l1 and syn_l2),
        "verify_accept": bool(verify_accept),
        "accepted_wrong": accepted_wrong,
        "status": str(status),
        "l1_syn_bits": 0, "l2_syn_bits": 0, "extra_parity_bits": 0,
        "verify_tag_bits": 0, "other_public_bits": 0,
        "rounds": int(rounds), "wall_s": float(wall_s),
        "rss_b": None if rss_b is None else int(rss_b),
    }
    if disclosure is not None:
        for key in ("l1_syn_bits", "l2_syn_bits", "extra_parity_bits",
                    "verify_tag_bits", "other_public_bits"):
            rec[key] = int(disclosure.get(key, 0))
    if set(rec) != set(RESULT_SCHEMA_COLUMNS):
        raise ValueError("frame record drifts from RESULT_SCHEMA_COLUMNS")
    return rec


def is_success(record: Mapping[str, Any]) -> bool:
    """Success = pair exact AND verify accept AND not accepted-wrong.

    ``accepted_wrong`` (undetected) and ``resource_abort`` never count as
    success; syndrome-only agreement never substitutes for exact recovery.
    """
    if record.get("status") == "resource_abort":
        return False
    return bool(record.get("pair_exact")) \
        and bool(record.get("verify_accept")) \
        and not bool(record.get("accepted_wrong"))


# --------------------------------------------------------------------------- #
# PROFILE_ONLY pre-decoder construction (no decoder, no root, no replacement)
# --------------------------------------------------------------------------- #
def profile_graphs(widths: Sequence[int] = WIDTHS) -> dict[str, Any]:
    """Bounded PROFILE_ONLY: build frozen control/candidate graphs, no decoder.

    Records per cell the A1–A6 admission outcome, ranks and wall time. A
    frozen seed that cannot produce an admitted graph is retained as-is; no
    replacement seed exists or is consumed.
    """
    import time
    now = time.perf_counter
    t0 = float(now())
    entries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    builders = ((CONTROL_ARM, build_control_l1),
                (CANDIDATE_ARM, build_candidate_l1))
    for width in widths:
        width = int(width)
        if width not in GRAPH_SEEDS:
            raise KeyError("unknown Stage-1 width %r" % (width,))
        for arm, build_fn in builders:
            for graph_seed in GRAPH_SEEDS[width]:
                start = float(now())
                graph = build_fn(width, graph_seed)
                wall = float(now()) - start
                entry: dict[str, Any] = {
                    "width": width, "arm": arm, "seed": int(graph_seed),
                    "status": str(graph["status"]),
                    "admitted": bool(graph["admitted"]),
                    "construction_wall_s": round(float(wall), 6),
                    "failure_reason": str(graph["failure_reason"]),
                    "n": int(graph["n"]), "m": int(graph["m"]),
                    "E": int(graph["E"]),
                }
                structure = graph.get("structure")
                if structure:
                    entry.update({
                        "structural_rank":
                            int(structure["structural_rank"]),
                        "gf32_rank": int(structure["gf32_rank"]),
                        "admission": {str(k): bool(v) for k, v in
                                      structure["admission"].items()},
                        "connected_components":
                            int(structure["connected_components"]),
                        "four_cycles": int(structure["four_cycles"]),
                        "girth": structure["girth"],
                    })
                entries.append(entry)
                if graph["status"] == "construction_failed" \
                        or not graph["admitted"]:
                    failures.append({
                        "width": width, "arm": arm,
                        "seed": int(graph_seed),
                        "status": str(graph["status"]),
                        "admitted": bool(graph["admitted"]),
                        "failure_reason": str(graph["failure_reason"])})
    return {
        "graphs": entries,
        "seed_replacements": [],
        "replacement_seeds_used": 0,
        "frozen_seed_failures": failures,
        "decoder_calls": 0,
        "wall_s": float(now()) - t0,
    }
