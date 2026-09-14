"""V72P2D12 finite L1 degree refinement — readiness plan/runner/verifier.

Change: ``v72p2d12-finite-l1-degree``
Cycle: ``V72P2D12-FINITE-L1-DEGREE`` (successor refinement; NOT a correction)
Frozen authority: ``.workbuddy/tasks/D12_FINITE_L1_DEGREE_REFINEMENT_READINESS_TASK_PACKET.md``
(§1–§4) and ``openspec/changes/v72p2d12-finite-l1-degree/`` (proposal, design
§1–§8, tasks, delta spec). Track: implementation/readiness (zero scientific
decoder calls; no D12 batch, no L2, no D7-H, no real data, no commit/push).
The future batch (if ever authorized separately) is ``EXPLORE_HEAVY``.

Reuse contract (IMPORT — no duplication of construction/admission semantics):

- shared connectivity-first constructor: ``r2.build_degree_sequence_peg``;
- binding admission A1–A5: ``r2.structural_record`` (A6 replay mirrors the
  accepted ``r2.build_graph``/D11 ``build_l2_graph`` composition, applied to
  the frozen D12 cells — never to an R2/R3 cell);
- decoder path: ``r2.dispatch_l1`` (shared reference; admission gate before
  binding plus exact/syndrome/stop semantics);
- coefficient rule: ``r2.coefficient_seed`` /
  ``r2.coefficients_for_edges`` (``v10_seed`` of
  ``d10:coeff:{width}:{graph_seed}``);
- decoder contract constants (``max_iter=90``, ``damping_alpha=1.0``), field
  (``q=32, poly=37``), Model-F root, RSS budget and ``refuse_out_root``;
- R3 plan/seed/block structural pattern (``r3`` read-only: fresh-range
  precedent plus the import-time seed-disjointness guard below).

Added here (D12 successor deltas only): the three frozen arms (L045 λ2=0.45
frozen reference, L050/L055 challengers), the six frozen degree cells, fresh
graph/block seeds, the 216-calls-per-width / 432-call plan with both widths
always measured (no conditional progression), the verbatim ``STABLE`` /
``MATERIAL_BETTER`` gates plus ranking, ``SPLIT_WIDTH_CONFLICT``, the five
terminals, descriptive paired McNemar, the never-pool D12 batch boundary
(``D12WidthTallies`` built only from ``D12_BATCH_ID``-tagged D12 decoder
records), budgets (≤432 scientific, ≤62 setup, wall ≤1800 s, ≤120 s/call,
RSS <2 GiB, one process, no retry/resume/repair/seed search/adaptation) and
the 36-cell pre-decoder profile. There is no replacement-seed mechanism
anywhere in this module: admission failure blocks with no seed change.
A1/R3/D11 evidence is contextual only and structurally impossible to pool
into D12 gates.
"""
from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from typing import Any

from . import v72p2d10_mixed_degree_l1 as r2
from . import v72p2d10_r3_fresh_scaling as r3

__all__ = [
    "ARMS", "REFERENCE_ARM", "CHALLENGERS", "LAMBDA2", "ARM_ROLE",
    "D12_WIDTHS", "GRAPH_SEEDS", "BLOCK_SEEDS", "DEGREE_TABLE",
    "DECODER_MAX_ITER", "DAMPING_ALPHA", "MODEL_F_INPUT_ROOT",
    "PER_WIDTH_CALLS", "SCIENTIFIC_CALL_CEILING", "SETUP_CALL_CEILING",
    "SETUP_FIXED_UNITS", "WALL_BUDGET_S", "PER_CALL_BUDGET_S",
    "RSS_BUDGET_BYTES", "EVIDENCE_FILES", "FROZEN_COMMAND", "FUTURE_ROOT",
    "FUTURE_ROOT_UUID", "AUTHORIZATION", "CLAIM_CEILING", "D12_BATCH_ID",
    "STABLE_MIN_EXACT", "STABLE_GRAPHS_GE2_MIN", "MATERIAL_MARGIN_MIN",
    "MATERIAL_PAIR_WINS_MIN", "SPLIT_BEAT_MIN", "SPLIT_TRAIL_MAX",
    "T_SELECT_L050", "T_SELECT_L055", "T_RETAIN_L045",
    "T_SPLIT_AMBIGUOUS", "T_ENGINEERING_BLOCKED", "TERMINALS",
    "D12WidthTallies", "degree_cell", "build_graph", "dispatch_l1",
    "coefficient_seed", "refuse_out_root", "build_call_plan",
    "build_full_plan", "tallies_from_d12_records", "is_stable",
    "challenger_margin", "challenger_pair_wins", "is_material_better",
    "split_width_conflict", "route_terminal", "describe_paired",
    "execute_width", "profile_graphs",
]

# --------------------------------------------------------------------------- #
# Frozen identifiers (packet §2; design §1/§4/§5)
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2d12-finite-l1-degree"
CYCLE_ID = "V72P2D12-FINITE-L1-DEGREE"
TRACK = "implementation/readiness"
CLAIM_CEILING = (
    "synthetic finite L1 degree comparison only; no forward/L2, FER, "
    "leakage, SKR, real-data, qualification, optimality, promotion, "
    "publication or D7-H claim"
)

ARMS = ("L045", "L050", "L055")
REFERENCE_ARM = "L045"
CHALLENGERS = ("L050", "L055")
LAMBDA2 = {"L045": 0.45, "L050": 0.50, "L055": 0.55}
ARM_ROLE = {"L045": "frozen_reference",
            "L050": "challenger", "L055": "challenger"}
D12_WIDTHS = (128, 256)

#: Fresh graph seeds (frozen; never searched or replaced).
GRAPH_SEEDS = {
    128: tuple(range(2026093001, 2026093007)),
    256: tuple(range(2026093101, 2026093107)),
}
#: Fresh block seeds (frozen; separate from graph seeds).
BLOCK_SEEDS = {
    128: tuple(range(2026093201, 2026093213)),
    256: tuple(range(2026093301, 2026093313)),
}

#: Frozen f1.2 realizations (packet §2 verbatim; D1202-verified EXACT).
DEGREE_TABLE = {
    ("L045", 128): {
        "n": 128, "m": 118, "var_counts": {2: 71, 3: 57},
        "check_counts": {2: 41, 3: 77}},
    ("L050", 128): {
        "n": 128, "m": 118, "var_counts": {2: 77, 3: 51},
        "check_counts": {2: 47, 3: 71}},
    ("L055", 128): {
        "n": 128, "m": 118, "var_counts": {2: 83, 3: 45},
        "check_counts": {2: 53, 3: 65}},
    ("L045", 256): {
        "n": 256, "m": 236, "var_counts": {2: 141, 3: 115},
        "check_counts": {2: 81, 3: 155}},
    ("L050", 256): {
        "n": 256, "m": 236, "var_counts": {2: 154, 3: 102},
        "check_counts": {2: 94, 3: 142}},
    ("L055", 256): {
        "n": 256, "m": 236, "var_counts": {2: 166, 3: 90},
        "check_counts": {2: 106, 3: 130}},
}

#: Import-time seed-separation guard (D1207): D12 seeds are fresh and
#: disjoint from every prior seed set (R2 graph/block, R3 graph/block).
_PRIOR_SEEDS = (
    {s for seeds in r2.GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in r2.BLOCK_SEEDS.values() for s in seeds}
    | {s for seeds in r3.GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in r3.BLOCK_SEEDS.values() for s in seeds})
_D12_GRAPH = {s for seeds in GRAPH_SEEDS.values() for s in seeds}
_D12_BLOCK = {s for seeds in BLOCK_SEEDS.values() for s in seeds}
if len(_D12_GRAPH) != 12 or len(_D12_BLOCK) != 24:
    raise ValueError("D12 frozen seed sets have wrong cardinality")
if not _D12_GRAPH.isdisjoint(_D12_BLOCK):
    raise ValueError("D12 graph/block seeds overlap")
if not _D12_GRAPH.isdisjoint(_PRIOR_SEEDS) \
        or not _D12_BLOCK.isdisjoint(_PRIOR_SEEDS):
    raise ValueError("D12 seed collides with a prior (R2/R3) seed")
del _PRIOR_SEEDS, _D12_GRAPH, _D12_BLOCK

#: Decoder/field contract reused from R2 (no re-declaration).
DECODER_MAX_ITER = r2.DECODER_MAX_ITER
DAMPING_ALPHA = r2.DAMPING_ALPHA
MODEL_F_INPUT_ROOT = r2.MODEL_F_INPUT_ROOT
Q = r2.Q
POLY = r2.POLY

#: Shared decoder binding, coefficient rule and root refusal (import, not copy).
dispatch_l1 = r2.dispatch_l1
coefficient_seed = r2.coefficient_seed
refuse_out_root = r2.refuse_out_root

#: Budgets (packet §2: ≤432 scientific; ≤62 setup = 36 builds + 24 block
#: samples + Model-F load + plan build; wall ≤1800 s; ≤120 s/call).
PER_WIDTH_CALLS = 216
SCIENTIFIC_CALL_CEILING = 432
SETUP_CALL_CEILING = 62
SETUP_FIXED_UNITS = 2  # Model-F load + plan build
WALL_BUDGET_S = 1800.0
PER_CALL_BUDGET_S = 120.0
RSS_BUDGET_BYTES = r2.RSS_BUDGET_BYTES

#: Gate thresholds (packet §2 verbatim).
STABLE_MIN_EXACT = 18
STABLE_GRAPHS_GE2_MIN = 5
MATERIAL_MARGIN_MIN = 6
MATERIAL_PAIR_WINS_MIN = 4
SPLIT_BEAT_MIN = 6
SPLIT_TRAIL_MAX = 2

#: Terminals (packet §2 verbatim + explicit engineering/resource blocked).
T_SELECT_L050 = "D12_SELECT_L050"
T_SELECT_L055 = "D12_SELECT_L055"
T_RETAIN_L045 = "D12_RETAIN_L045_NO_MATERIAL_GAIN"
T_SPLIT_AMBIGUOUS = "D12_FINITE_DEGREE_SPLIT_AMBIGUOUS"
T_ENGINEERING_BLOCKED = "D12_ENGINEERING_BLOCKED"
TERMINALS = (T_SELECT_L050, T_SELECT_L055, T_RETAIN_L045,
             T_SPLIT_AMBIGUOUS, T_ENGINEERING_BLOCKED)

FUTURE_ROOT_UUID = "94fb9d22-cadc-47f4-a96e-b2170bdba450"
FUTURE_ROOT = "workspace/d12_finite_l1_degree_" + FUTURE_ROOT_UUID
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d12_development.py "
    "--d12-batch --model-f-root %s --out-root %s"
    % (MODEL_F_INPUT_ROOT, FUTURE_ROOT)
)
AUTHORIZATION = (
    "separate explicit user/main-thread authorization required before "
    "--d12-batch")

EVIDENCE_FILES = ("manifest.json", "decoder_records.csv",
                  "graph_records.csv", "arm_summary.csv", "summary.json",
                  "command_log.txt")

#: Scope tag carried by every D12 decoder record. The gate constructor only
#: accepts records carrying this tag, so A1/R3/D11 evidence (different
#: roots, schemas, widths, seeds and no D12 batch tag) is structurally
#: impossible to pool into D12 arithmetic.
D12_BATCH_ID = "d12-finite-l1-degree-v1"


# --------------------------------------------------------------------------- #
# Degree cells and graph construction (R2 path reused, never duplicated)
# --------------------------------------------------------------------------- #
def degree_cell(arm: str, width: int) -> dict[str, Any]:
    """Return the frozen D12 ``(n, m, var_counts, check_counts)`` cell."""
    key = (str(arm), int(width))
    if key not in DEGREE_TABLE:
        raise KeyError("unknown D12 (arm, width) cell %r" % (key,))
    cell = DEGREE_TABLE[key]
    var_sockets = sum(int(d) * int(c) for d, c in cell["var_counts"].items())
    check_sockets = sum(int(d) * int(c)
                        for d, c in cell["check_counts"].items())
    if sum(cell["var_counts"].values()) != cell["n"]:
        raise ValueError("frozen cell %r variable counts do not sum to n"
                         % (key,))
    if sum(cell["check_counts"].values()) != cell["m"]:
        raise ValueError("frozen cell %r check counts do not sum to m"
                         % (key,))
    if var_sockets != check_sockets:
        raise ValueError("frozen cell %r socket mismatch" % (key,))
    return {"n": int(cell["n"]), "m": int(cell["m"]),
            "var_counts": dict(cell["var_counts"]),
            "check_counts": dict(cell["check_counts"]), "E": var_sockets}


def build_graph(arm: str, width: int, graph_seed: int) -> dict[str, Any]:
    """Build one frozen D12 graph via the accepted R2 construction/admission.

    Same accepted connectivity-first path as ``r2.build_graph`` (one
    deterministic attempt via ``r2.build_degree_sequence_peg``, A1–A5 from
    ``r2.structural_record`` plus A6 deterministic replay equality of the
    edge list and coefficient stream — the D11 ``build_l2_graph``
    composition precedent for novel frozen cells), applied to the frozen
    D12 cell. All three arms share this one builder; only the forced
    degree/socket profile differs. Any failure is retained with
    ``admitted=False``; seeds are never altered, repaired or searched.
    """
    degree_cell(arm, width)  # scope guard; raises outside D12 cells
    if int(graph_seed) not in GRAPH_SEEDS[int(width)]:
        raise ValueError("graph seed %r outside frozen D12 set for width %d"
                         % (graph_seed, int(width)))
    cell = degree_cell(str(arm), int(width))
    construction = r2.build_degree_sequence_peg(
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
    coefficients = r2.coefficients_for_edges(construction["edges"],
                                            int(width), int(graph_seed))
    dense = r2.dense_from_edges(cell["n"], cell["m"],
                               construction["edges"], coefficients)
    structure = r2.structural_record(dense, cell["var_counts"],
                                     cell["check_counts"])
    replay = r2.build_degree_sequence_peg(
        cell["n"], cell["m"], cell["var_counts"], cell["check_counts"],
        int(graph_seed))
    replay_coeffs = r2.coefficients_for_edges(replay["edges"], int(width),
                                              int(graph_seed))
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
# Plan: exact call identities, both widths always measured (D1203)
# --------------------------------------------------------------------------- #
def build_call_plan(width: int) -> list[dict[str, Any]]:
    """Frozen paired call matrix for one width: 3 arms x 6 graphs x 12 blocks.

    Order: reference arm first, graph seeds ascending, block seeds
    ascending; ``call_idx`` is contiguous over the width (0..215).
    """
    width = int(width)
    if width not in D12_WIDTHS:
        raise KeyError("unknown D12 width %r" % (width,))
    plan: list[dict[str, Any]] = []
    for arm in ARMS:
        for graph_seed in GRAPH_SEEDS[width]:
            for block_seed in BLOCK_SEEDS[width]:
                plan.append({
                    "call_idx": len(plan), "width": width, "arm": arm,
                    "graph_seed": int(graph_seed),
                    "block_seed": int(block_seed)})
    return plan


def build_full_plan() -> list[dict[str, Any]]:
    """Both widths concatenated (n128 first); exactly 432 scientific calls."""
    plan = build_call_plan(128)
    base = len(plan)
    for entry in build_call_plan(256):
        plan.append(dict(entry, call_idx=base + entry["call_idx"]))
    return plan


# --------------------------------------------------------------------------- #
# Gate arithmetic with a structural predecessor boundary (D1203)
# --------------------------------------------------------------------------- #
class D12WidthTallies:
    """Exact-count tallies for one D12 width (three arms, six graphs each).

    Only exact counts enter the gate; syndrome-valid counts are carried
    separately by the records and never substitute for exact. Instances can
    only be built from ``D12_BATCH_ID``-tagged D12 decoder records (see
    ``tallies_from_d12_records``), so A1/R3/D11 evidence cannot reach the
    gate.
    """

    def __init__(self, width: int, l045_exact: Sequence[int],
                 l050_exact: Sequence[int],
                 l055_exact: Sequence[int]) -> None:
        width = int(width)
        if width not in D12_WIDTHS:
            raise ValueError("unknown D12 width %r" % (width,))
        vectors = {}
        for arm, vec in (("L045", l045_exact), ("L050", l050_exact),
                         ("L055", l055_exact)):
            vec = tuple(int(v) for v in vec)
            if len(vec) != 6:
                raise ValueError("D12 tallies require exactly 6 graphs "
                                 "per arm")
            if any(v < 0 or v > 12 for v in vec):
                raise ValueError("per-graph exact counts must lie in 0..12")
            vectors[arm] = vec
        self.width = width
        self.exact = vectors

    def pool(self, arm: str) -> int:
        """Exact pool for one arm (72 paired blocks)."""
        return sum(self.exact[str(arm)])


def tallies_from_d12_records(records: Sequence[Mapping[str, Any]],
                             width: int) -> D12WidthTallies:
    """Build gate tallies exclusively from D12 decoder records of one width.

    Every contributing record must carry ``batch_id == D12_BATCH_ID`` and a
    frozen ``(arm, width, graph_seed, block_seed)`` identity; each of the
    18 ``(arm, graph)`` pairs must contribute exactly the 12 paired blocks.
    Anything else raises, so non-D12 evidence cannot enter the gate.
    """
    width = int(width)
    scoped = [r for r in records if int(r["width"]) == width]
    if not scoped:
        raise ValueError("no D12 decoder records for width %d" % width)
    for record in scoped:
        if record.get("batch_id") != D12_BATCH_ID:
            raise ValueError("record without D12 batch tag cannot enter "
                             "the D12 gate: %r"
                             % ({k: record.get(k) for k in
                                 ("width", "arm", "graph_seed",
                                  "block_seed", "batch_id")},))
        if record.get("arm") not in ARMS:
            raise ValueError("record arm outside D12 arms: %r"
                             % (record.get("arm"),))
        if int(record["graph_seed"]) not in GRAPH_SEEDS[width]:
            raise ValueError("record graph seed outside frozen D12 set")
        if int(record["block_seed"]) not in BLOCK_SEEDS[width]:
            raise ValueError("record block seed outside frozen D12 set")
    vectors = {}
    for arm in ARMS:
        per_graph = []
        for graph_seed in GRAPH_SEEDS[width]:
            rows = [r for r in scoped
                    if r["arm"] == arm and int(r["graph_seed"]) == graph_seed]
            if len(rows) != 12:
                raise ValueError(
                    "pair (arm=%s, width=%d, seed=%d) contributes "
                    "%d blocks, want exactly 12" % (arm, width, graph_seed,
                                                    len(rows)))
            if sorted(int(r["block_seed"]) for r in rows) \
                    != sorted(BLOCK_SEEDS[width]):
                raise ValueError("unpaired block identities at pair "
                                 "(arm=%s, width=%d, seed=%d)" % (arm, width,
                                                                  graph_seed))
            per_graph.append(sum(1 for r in rows if r["exact"]))
        vectors[arm] = per_graph
    return D12WidthTallies(width, vectors["L045"], vectors["L050"],
                           vectors["L055"])


def is_stable(tallies: D12WidthTallies, arm: str,
              engineering_reason: str = "") -> bool:
    """Frozen ``STABLE(w)`` gate (packet §2 verbatim).

    Exact ≥18/72, at least 5/6 graphs have ≥2 exact, and no
    engineering/resource violation. Only ``D12WidthTallies`` instances are
    accepted, so non-D12 evidence cannot be graded.
    """
    if not isinstance(tallies, D12WidthTallies):
        raise TypeError("is_stable accepts only D12WidthTallies "
                        "(non-D12 evidence cannot enter the D12 gate)")
    if engineering_reason:
        return False
    vec = tallies.exact[str(arm)]
    return sum(vec) >= STABLE_MIN_EXACT \
        and sum(1 for v in vec if v >= 2) >= STABLE_GRAPHS_GE2_MIN


def challenger_margin(tallies: D12WidthTallies, challenger: str) -> int:
    """Challenger exact pool minus the frozen-reference pool at one width."""
    if str(challenger) not in CHALLENGERS:
        raise ValueError("unknown D12 challenger %r" % (challenger,))
    return tallies.pool(challenger) - tallies.pool(REFERENCE_ARM)


def challenger_pair_wins(tallies: D12WidthTallies, challenger: str) -> int:
    """Graphs where the challenger has higher per-graph exact than L045."""
    if str(challenger) not in CHALLENGERS:
        raise ValueError("unknown D12 challenger %r" % (challenger,))
    return sum(1 for c, r in zip(tallies.exact[str(challenger)],
                                tallies.exact[REFERENCE_ARM]) if c > r)


def is_material_better(t128: D12WidthTallies, t256: D12WidthTallies,
                       p128: Mapping[str, Any], p256: Mapping[str, Any],
                       challenger: str, engineering_reason: str = "") -> bool:
    """Frozen ``MATERIAL_BETTER`` gate (packet §2 verbatim, both widths).

    At both widths: the challenger is STABLE; its exact is at least
    L045+6; its pooled challenger-only discordance exceeds L045-only; and
    it has higher per-graph exact on at least 4/6 graph pairs.
    """
    if str(challenger) not in CHALLENGERS:
        raise ValueError("unknown D12 challenger %r" % (challenger,))
    if engineering_reason:
        return False
    for tallies, paired in ((t128, p128), (t256, p256)):
        if not isinstance(tallies, D12WidthTallies):
            raise TypeError("is_material_better accepts only "
                            "D12WidthTallies")
        if not is_stable(tallies, challenger):
            return False
        if challenger_margin(tallies, challenger) < MATERIAL_MARGIN_MIN:
            return False
        disc = paired[str(challenger)]
        if not disc["challenger_only"] > disc["reference_only"]:
            return False
        if challenger_pair_wins(tallies, challenger) \
                < MATERIAL_PAIR_WINS_MIN:
            return False
    return True


def split_width_conflict(t128: D12WidthTallies,
                         t256: D12WidthTallies) -> bool:
    """Frozen ``SPLIT_WIDTH_CONFLICT`` (packet §2 verbatim).

    True when a challenger beats L045 by ≥6 at one width but trails by >2
    at the other, or when the widths favor opposing challengers (the
    strictly preferred challenger differs by width).
    """
    for tallies in (t128, t256):
        if not isinstance(tallies, D12WidthTallies):
            raise TypeError("split_width_conflict accepts only "
                            "D12WidthTallies")
    margins = {c: (challenger_margin(t128, c), challenger_margin(t256, c))
               for c in CHALLENGERS}
    for challenger in CHALLENGERS:
        m128, m256 = margins[challenger]
        if (m128 >= SPLIT_BEAT_MIN and m256 < -SPLIT_TRAIL_MAX) \
                or (m256 >= SPLIT_BEAT_MIN and m128 < -SPLIT_TRAIL_MAX):
            return True
    preferred = {}
    for width, tallies in ((128, t128), (256, t256)):
        pools = {c: tallies.pool(c) for c in CHALLENGERS}
        preferred[width] = max(pools, key=lambda c: pools[c]) \
            if pools["L050"] != pools["L055"] else None
    return preferred[128] is not None and preferred[128] != preferred[256]


def route_terminal(t128: D12WidthTallies, t256: D12WidthTallies,
                   p128: Mapping[str, Any], p256: Mapping[str, Any],
                   engineering_reason: str = "") -> str:
    """Frozen terminal routing (packet §2 verbatim).

    Exactly one MATERIAL_BETTER challenger → select it; both → rank by
    total exact, then worst-width exact, then smaller λ2; neither with no
    split-width conflict → retain L045; split conflict → ambiguous; any
    engineering/resource reason → blocked terminal.
    """
    for tallies in (t128, t256):
        if not isinstance(tallies, D12WidthTallies):
            raise TypeError("route_terminal accepts only D12WidthTallies "
                            "(non-D12 evidence cannot enter the D12 gate)")
    if engineering_reason:
        return T_ENGINEERING_BLOCKED
    material = {c: is_material_better(t128, t256, p128, p256, c)
                for c in CHALLENGERS}
    winners = [c for c in CHALLENGERS if material[c]]
    if len(winners) == 1:
        return T_SELECT_L050 if winners[0] == "L050" else T_SELECT_L055
    if len(winners) == 2:
        keyed = sorted(
            CHALLENGERS,
            key=lambda c: (-(t128.pool(c) + t256.pool(c)),
                           -min(t128.pool(c), t256.pool(c)), LAMBDA2[c]))
        return T_SELECT_L050 if keyed[0] == "L050" else T_SELECT_L055
    if split_width_conflict(t128, t256):
        return T_SPLIT_AMBIGUOUS
    return T_RETAIN_L045


def describe_paired(records: Sequence[Mapping[str, Any]],
                    width: int | None) -> dict[str, Any]:
    """Descriptive paired discordances + exact one-sided McNemar (no gating).

    For each challenger and each paired ``(graph, block)`` call let ``b``
    count (challenger exact, L045 not) and ``c`` count (L045 exact,
    challenger not). The one-sided exact p-value is
    ``P(Bin(b+c, 1/2) >= b)``. ``width=None`` pools both widths. Reported
    descriptively only; p-values never override the frozen gate.
    """
    scoped = [r for r in records
              if width is None or int(r["width"]) == int(width)]
    out: dict[str, Any] = {"width": "pooled" if width is None else int(width)}
    for challenger in CHALLENGERS:
        discord_b = discord_c = concord = 0
        for w in D12_WIDTHS:
            if width is not None and int(w) != int(width):
                continue
            for graph_seed in GRAPH_SEEDS[w]:
                for block_seed in BLOCK_SEEDS[w]:
                    rows = [r for r in scoped
                            if int(r["width"]) == w
                            and int(r["graph_seed"]) == graph_seed
                            and int(r["block_seed"]) == block_seed]
                    chal = [r for r in rows if r["arm"] == challenger]
                    ref = [r for r in rows if r["arm"] == REFERENCE_ARM]
                    if len(chal) != 1 or len(ref) != 1:
                        raise ValueError("unpaired D12 calls at width=%d "
                                         "seed=%d block=%d"
                                         % (w, graph_seed, block_seed))
                    chal_ok, ref_ok = bool(chal[0]["exact"]), \
                        bool(ref[0]["exact"])
                    if chal_ok and not ref_ok:
                        discord_b += 1
                    elif ref_ok and not chal_ok:
                        discord_c += 1
                    else:
                        concord += 1
        trials = discord_b + discord_c
        p_value = (sum(math.comb(trials, k)
                       for k in range(discord_b, trials + 1))
                   / 2.0 ** trials) if trials else 1.0
        out[challenger] = {"challenger_only": discord_b,
                           "reference_only": discord_c,
                           "concordant": concord, "trials": trials,
                           "mcnemar_one_sided_p": p_value,
                           "descriptive_only": True}
    return out


# --------------------------------------------------------------------------- #
# Width execution: admission sweep first, then the R2 decoder path (D1205)
# --------------------------------------------------------------------------- #
def execute_width(width: int, plan: Sequence[Mapping[str, Any]],
                  graphs: Mapping[Any, Mapping[str, Any]],
                  blocks: Mapping[int, Mapping[str, Any]],
                  decode_fn, syndrome_fn, *, now=None, rss_fn=None,
                  wall_budget_s: float = WALL_BUDGET_S,
                  per_call_budget_s: float = PER_CALL_BUDGET_S,
                  rss_budget_bytes: int = RSS_BUDGET_BYTES,
                  call_ceiling: int = PER_WIDTH_CALLS) -> dict[str, Any]:
    """Execute one width (216 paired calls) through ``r2.dispatch_l1``.

    All 18 graphs of the width are admission-checked before any decoder
    binding; any failure engineering-blocks the width with zero decoder
    calls and no seed replacement. ``decode_fn``/``syndrome_fn`` must be
    explicitly injected; this module never imports the production
    decoder. Decoder crashes are retained, never retried.
    """
    width = int(width)
    now = now or time.monotonic
    t_width = float(now())
    width_plan = [e for e in plan if int(e["width"]) == width]
    failure: str | None = None
    for arm in ARMS:
        for graph_seed in GRAPH_SEEDS[width]:
            graph = graphs.get((arm, width, graph_seed))
            if graph is None or not bool(graph.get("admitted")):
                failure = ("graph (arm=%s, width=%d, seed=%d) not admitted; "
                           "blocked without seed replacement"
                           % (arm, width, graph_seed))
                break
        if failure is not None:
            break
    records: list[dict[str, Any]] = []
    if failure is None:
        for entry in width_plan:
            if len(records) >= int(call_ceiling):
                failure = "per-width scientific call ceiling reached"
                break
            graph = graphs[(str(entry["arm"]), width,
                            int(entry["graph_seed"]))]
            block = blocks[width][int(entry["block_seed"])]
            call_t0 = float(now())
            record = r2.dispatch_l1(graph, block, entry, decode_fn,
                                    syndrome_fn, call_idx=len(records))
            record["wall_s"] = max(float(now()) - call_t0, 0.0)
            record["batch_id"] = D12_BATCH_ID
            records.append(record)
            if record["crash"]:
                failure = "decoder crash: %s" % record["error"]
            elif float(record["wall_s"]) > float(per_call_budget_s):
                failure = ("per-call wall budget exceeded: %.3f s"
                           % float(record["wall_s"]))
            elif float(now()) - t_width > float(wall_budget_s):
                failure = "wall budget exceeded"
            elif rss_fn is not None \
                    and int(rss_fn()) >= int(rss_budget_bytes):
                failure = "RSS budget exceeded"
            if failure is not None:
                break
    if records:
        tallies = tallies_from_d12_records(records, width)
        paired = describe_paired(records, width)
    else:
        tallies = D12WidthTallies(width, (0,) * 6, (0,) * 6, (0,) * 6)
        # No calls ran (admission block): zero discordances by construction.
        paired = {
            "width": width,
            "L050": {"challenger_only": 0, "reference_only": 0,
                     "concordant": 0, "trials": 0,
                     "mcnemar_one_sided_p": 1.0, "descriptive_only": True},
            "L055": {"challenger_only": 0, "reference_only": 0,
                     "concordant": 0, "trials": 0,
                     "mcnemar_one_sided_p": 1.0, "descriptive_only": True}}
    return {
        "width": width,
        "records": records,
        "tallies": tallies,
        "paired": paired,
        "stable": {arm: is_stable(tallies, arm, failure or "")
                   for arm in ARMS},
        "engineering_reason": failure or "",
        "decoder_calls": len(records),
    }


# --------------------------------------------------------------------------- #
# D1209 pre-decoder profile: all 36 future graphs, no decoder, no root
# --------------------------------------------------------------------------- #
def profile_graphs(build_fn=None, now=None) -> dict[str, Any]:
    """Bounded profile: build all 36 frozen D12 graphs, no decoder, no root.

    Reports per cell the component count, structural/GF32 rank, four-cycle
    count, girth and wall time plus the A1–A6 admission outcome. A frozen
    seed that cannot produce an admitted graph is retained as-is; no
    replacement seed exists or is consumed (zero replacement seeds by
    construction).
    """
    build_fn = build_fn or build_graph
    now = now or time.perf_counter
    t0 = float(now())
    entries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for width in D12_WIDTHS:
        for arm in ARMS:
            for graph_seed in GRAPH_SEEDS[width]:
                start = float(now())
                graph = build_fn(arm, width, graph_seed)
                wall = float(now()) - start
                entry: dict[str, Any] = {
                    "width": int(graph["width"]),
                    "arm": str(graph["arm"]),
                    "seed": int(graph_seed),
                    "status": str(graph["status"]),
                    "admitted": bool(graph["admitted"]),
                    "construction_wall_s": round(float(wall), 6),
                    "failure_reason": str(graph["failure_reason"]),
                }
                structure = graph.get("structure")
                if structure:
                    entry.update({
                        "rank": int(structure["rank"]),
                        "structural_rank": int(structure["structural_rank"]),
                        "gf32_rank": int(structure["gf32_rank"]),
                        "admission": {str(k): bool(v) for k, v in
                                      structure["admission"].items()},
                        "connected_components":
                            int(structure["connected_components"]),
                        "largest_component_fraction":
                            float(structure["largest_component_fraction"]),
                        "min_check_degree":
                            int(structure["min_check_degree"]),
                        "degree2_N2": int(structure["degree2"]["N2"]),
                        "degree2_cycle_rank_lower_bound": int(
                            structure["degree2"]["cycle_rank_lower_bound"]),
                        "four_cycles": int(structure["four_cycles"]),
                        "girth": structure["girth"],
                        "girth_reason": str(structure["girth_reason"]),
                    })
                entries.append(entry)
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
