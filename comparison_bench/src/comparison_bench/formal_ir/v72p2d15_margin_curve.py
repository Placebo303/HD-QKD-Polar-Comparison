"""V72P2D15 paired finite-length margin curve — readiness plan/graphs/gates.

Change: ``v72p2d15-finite-length-margin-curve``
Frozen authority: ``.workbuddy/tasks/D15_FINITE_LENGTH_MARGIN_CURVE_READINESS_R1_TASK_PACKET.md``
(§2 question + invalid-inference rejections, §3 frozen matrix, §4 D1503–D1509,
§5 budgets) + ``openspec/changes/v72p2d15-finite-length-margin-curve/``
(design with equations/reuse map/seeds/matrix/gates/budgets, delta spec,
tasks). Track: implementation/readiness (zero production/scientific decoder
calls; no D15 batch, no D7-H, no real data, no commit/push).

Frozen matrix (implement EXACTLY; STOP on any drift need — D1502 proved
arithmetic/feasibility, do not re-amend):

- n=128 only; bits per disclosed row 5; generator unchanged:
  ``H_L1 = 4.286720430201375`` load ``548.700215065776`` bits;
  ``H_L2 = 3.222719884634378`` load ``412.508145233200`` bits.
- Nine cells: L045 at m=110/114/118, L055 at m=110/114/118, L2 DV3 ORACLE
  at m=83/86/89. Disclosed bits 5m (L1 550/570/590; L2 415/430/445);
  effective factors are ALWAYS computed as disclosed/load (≈L1
  1.00237/1.03882/1.07527; L2 1.00604/1.04240/1.07877), never copied.
- Variable profiles: L045 71/57/E313; L055 83/45/E301; L2 128 degree-3/E384.
  Check allocations: L045 ``2^17+3^93`` / ``2^29+3^85`` / ``2^41+3^77``;
  L055 ``2^29+3^81`` / ``2^41+3^73`` / ``2^53+3^65``;
  L2 ``4^31+5^52`` / ``4^46+5^40`` / ``4^61+5^28``.
- 36 fresh graph seeds (4 disjoint seeds per cell) + 8 shared block seeds
  (the same 8 blocks feed all nine cells); 288-call plan; 46 setup units.
- Arms L045, L055, L2-ORACLE single-layer diagnostic only. There is NO
  cross-layer arm in this change: no import, parameter, closure, record
  field or manifest key for one exists anywhere in this module (see the
  no-APP proof test). The L2 leg uses the accepted true-conditioned
  single-layer oracle diagnostic only.

Reuse contract (IMPORT — no duplication of construction/admission
semantics, no copied decoder/GF32 kernels):

- shared connectivity-first constructor: ``r2.build_degree_sequence_peg``;
- binding admission A1–A6: ``r2.structural_record`` (A6 replay mirrors the
  accepted ``r2.build_graph``/D11 composition, applied to the frozen D15
  cells — never to a predecessor cell);
- L1 decoder path: ``r2.dispatch_l1`` (shared reference; admission gate
  before binding plus exact/syndrome semantics);
- coefficient rule: ``r2.coefficient_seed`` / ``r2.coefficients_for_edges``
  (``v10_seed`` of ``d10:coeff:{width}:{graph_seed}``);
- block sampling / Model-F prior chain / L1 prior line: the accepted
  ``d5.sample_matched_block``, ``d5.prepare_model_f_prior_candidate``,
  ``d5.marginalize_f_to_p1`` / ``d5._floor_renorm`` composition (bound by
  the authorized runner only; this module never loads Model-F content);
- L2 oracle diagnostic: the accepted ``d5.oracle_l2_prior`` true-conditioned
  path (injected by the authorized runner; records marked ORACLE/ungraded,
  excluded from grading except via the preregistered route vocabulary);
- root refusal: ``r2.refuse_out_root``; decoder contract
  (``max_iter=90``, ``damping 1.0``, cold start, q=32/poly37), Model-F root,
  RSS budget.

Added here (D15 deltas only): the nine frozen cells, fresh D15 seeds, the
288-record three-arm plan, the D15 gate predicates plus six terminals with
exact priority, the oracle dispatch skeleton with explicit injection, the
descriptive Wilson/paired-discordance/monotonicity helpers (fit NO
asymptotic threshold from three points), and the 36-object pre-decoder
profile. There is no replacement-seed mechanism anywhere in this module:
admission failure blocks with no seed change. This module never imports
the production decoder and never loads Model-F content.
"""
from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from typing import Any

from . import v72p2d10_mixed_degree_l1 as r2
from . import v72p2d10_r3_fresh_scaling as r3
from . import v72p2d11_forward_app as d11
from . import v72p2d12_finite_l1_degree as d12
from . import v72p2d14n_calibrated_discriminator as d14n
from . import v72p2d5_gf32_rate_mother as d5

__all__ = [
    "CHANGE_ID", "CYCLE_ID", "TRACK", "CLAIM_CEILING",
    "N", "BITS_PER_ROW", "H_L1", "H_L2", "LOAD_L1", "LOAD_L2",
    "ROWS_L1", "ROWS_L2", "ARMS", "L1_PROFILES", "ORACLE_ARM",
    "ORACLE_PROFILE", "POINTS", "CELLS", "VAR_PROFILES", "EDGE_TOTALS",
    "CHECK_TABLE", "GRAPH_SEEDS", "BLOCK_SEEDS",
    "CELL_TRIALS", "GRAPH_TRIALS",
    "CELL_ADEQUATE_MIN", "ADEQUATE_GRAPHS_MIN", "ADEQUATE_GRAPH_MIN",
    "CELL_WEAK_MAX", "WEAK_GRAPHS_MIN", "WEAK_GRAPH_MAX",
    "Q", "POLY", "DECODER_MAX_ITER", "DAMPING_ALPHA",
    "MODEL_F_INPUT_ROOT", "PRIOR_CHAIN", "DECODER_FLOOR",
    "SCIENTIFIC_CALL_CEILING", "SETUP_CALL_CEILING", "SETUP_FIXED_UNITS",
    "WALL_BUDGET_S", "PER_CALL_BUDGET_S", "RSS_BUDGET_BYTES",
    "T_L1_SPECIFIC", "T_L2_SPECIFIC", "T_FINITE_BACKOFF", "T_BOTH_WEAK",
    "T_AMBIGUOUS", "T_ENGINEERING_BLOCKED", "TERMINALS",
    "EVIDENCE_FILES", "FUTURE_ROOT", "FROZEN_COMMAND", "AUTHORIZATION",
    "D15_BATCH_ID", "StructureNotAdmitted",
    "dispatch_l1", "coefficient_seed", "refuse_out_root",
    "sample_matched_block", "prepare_model_f_prior_candidate",
    "marginalize_f_to_p1", "floor_renorm", "oracle_l2_prior",
    "disclosed_bits", "effective_factor", "degree_cell",
    "build_l1_graph", "build_l2_graph", "build_call_plan",
    "D15Tallies", "tallies_from_d15_records",
    "is_cell_adequate", "is_cell_weak", "monotonicity_report",
    "wilson_interval", "describe_paired_l1", "route_terminal",
    "run_l2_oracle_cell", "execute_plan", "profile_graphs",
]

# --------------------------------------------------------------------------- #
# Frozen identifiers (packet §§1–3/§5; design §§2–3/§6–§8; spec normative)
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2d15-finite-length-margin-curve"
CYCLE_ID = "V72P2D15-FINITE-LENGTH-MARGIN-CURVE"
TRACK = "implementation/readiness"
CLAIM_CEILING = (
    "synthetic single-layer diagnostic only; no threshold fit, no L1/L2 "
    "investment selection, no D7-H/FER/leakage/SKR/real-data/qualification/"
    "optimality/publication claim; grants no execution"
)

N = 128
BITS_PER_ROW = 5

#: Frozen generator entropies and n128 loads (trusted inputs; the generator
#: itself is unchanged — D1502 recomputation CONFIRMED both products).
H_L1 = 4.286720430201375
H_L2 = 3.222719884634378
LOAD_L1 = 548.700215065776
LOAD_L2 = 412.508145233200

ROWS_L1 = (110, 114, 118)
ROWS_L2 = (83, 86, 89)

ARMS = ("L045", "L055", "L2_ORACLE")
L1_PROFILES = ("L045", "L055")
ORACLE_ARM = "L2_ORACLE"
ORACLE_PROFILE = "L2"

#: Three matched-margin row points; plan order is point ascending, arm
#: L045 → L055 → L2-ORACLE, graph ascending, block ascending.
POINTS = ((110, 110, 83), (114, 114, 86), (118, 118, 89))

#: Nine frozen cells as (profile, rows); the plan arm label for the L2
#: profile is ``L2_ORACLE``.
CELLS = (("L045", 110), ("L045", 114), ("L045", 118),
         ("L055", 110), ("L055", 114), ("L055", 118),
         ("L2", 83), ("L2", 86), ("L2", 89))

#: Variable profiles are m-independent (frozen D9 largest-remainder rule).
VAR_PROFILES = {"L045": {2: 71, 3: 57},
                "L055": {2: 83, 3: 45},
                "L2": {3: 128}}
EDGE_TOTALS = {"L045": 313, "L055": 301, "L2": 384}

#: Check allocations derived exactly (floor/ceil concentration; D1502 PASS).
CHECK_TABLE = {
    ("L045", 110): {2: 17, 3: 93},
    ("L045", 114): {2: 29, 3: 85},
    ("L045", 118): {2: 41, 3: 77},
    ("L055", 110): {2: 29, 3: 81},
    ("L055", 114): {2: 41, 3: 73},
    ("L055", 118): {2: 53, 3: 65},
    ("L2", 83): {4: 31, 5: 52},
    ("L2", 86): {4: 46, 5: 40},
    ("L2", 89): {4: 61, 5: 28},
}

#: Fresh seeds (frozen; never searched or replaced): 4 disjoint seeds per
#: cell (36 graphs), one shared 8-block set feeding all nine cells.
GRAPH_SEEDS = {
    ("L045", 110): (2026093801, 2026093802, 2026093803, 2026093804),
    ("L045", 114): (2026093805, 2026093806, 2026093807, 2026093808),
    ("L045", 118): (2026093809, 2026093810, 2026093811, 2026093812),
    ("L055", 110): (2026093813, 2026093814, 2026093815, 2026093816),
    ("L055", 114): (2026093817, 2026093818, 2026093819, 2026093820),
    ("L055", 118): (2026093821, 2026093822, 2026093823, 2026093824),
    ("L2", 83): (2026093825, 2026093826, 2026093827, 2026093828),
    ("L2", 86): (2026093829, 2026093830, 2026093831, 2026093832),
    ("L2", 89): (2026093833, 2026093834, 2026093835, 2026093836),
}
BLOCK_SEEDS = tuple(range(2026093901, 2026093909))

#: Trial geometry: 4 graphs x 8 blocks = 32 trials per cell.
CELL_TRIALS = 32
GRAPH_TRIALS = 8

#: Preregistered gate thresholds (design §7 conservative rules): a cell is
#: adequate only with multi-graph support (pool ≥24/32 AND ≥2 graphs ≥6/8);
#: weak only with multi-graph support (pool ≤16/32 AND ≥2 graphs ≤4/8).
#: The 17..23 middle zone is neither — it pushes toward AMBIGUOUS.
CELL_ADEQUATE_MIN = 24
ADEQUATE_GRAPHS_MIN = 2
ADEQUATE_GRAPH_MIN = 6
CELL_WEAK_MAX = 16
WEAK_GRAPHS_MIN = 2
WEAK_GRAPH_MAX = 4

#: Decoder/field/prior contract reused from R2/D5 (no re-declaration).
Q = r2.Q
POLY = r2.POLY
DECODER_MAX_ITER = r2.DECODER_MAX_ITER
DAMPING_ALPHA = r2.DAMPING_ALPHA
MODEL_F_INPUT_ROOT = r2.MODEL_F_INPUT_ROOT
PRIOR_CHAIN = "candidate_concentration_backoff"
DECODER_FLOOR = d5.DECODER_FLOOR

#: Shared L1 decoder binding, coefficient rule, root refusal (import).
dispatch_l1 = r2.dispatch_l1
coefficient_seed = r2.coefficient_seed
refuse_out_root = r2.refuse_out_root
StructureNotAdmitted = r2.StructureNotAdmitted

#: Accepted Model-F sampling/prior helpers + true-conditioned L2 oracle
#: path (import, not copy; bound by the authorized runner only).
sample_matched_block = d5.sample_matched_block
prepare_model_f_prior_candidate = d5.prepare_model_f_prior_candidate
marginalize_f_to_p1 = d5.marginalize_f_to_p1
floor_renorm = d5._floor_renorm
oracle_l2_prior = d5.oracle_l2_prior

#: Budgets (packet §5; design §8): ≤288 scientific; ≤46 setup = 36 graph
#: objects + 8 block samples + 2 fixed plan/manifest; wall ≤1800 s total;
#: ≤120 s/call (checked between/after calls, never interrupted).
SCIENTIFIC_CALL_CEILING = 288
SETUP_CALL_CEILING = 46
SETUP_FIXED_UNITS = 2  # plan build + manifest
WALL_BUDGET_S = 1800.0
PER_CALL_BUDGET_S = 120.0
RSS_BUDGET_BYTES = r2.RSS_BUDGET_BYTES

#: Six routing terminals (prereg design §7; first match wins).
T_L1_SPECIFIC = "MARGIN_CURVE_L1_SPECIFIC"
T_L2_SPECIFIC = "MARGIN_CURVE_L2_SPECIFIC"
T_FINITE_BACKOFF = "MARGIN_CURVE_FINITE_BACKOFF"
T_BOTH_WEAK = "MARGIN_CURVE_BOTH_WEAK"
T_AMBIGUOUS = "MARGIN_CURVE_AMBIGUOUS"
T_ENGINEERING_BLOCKED = "MARGIN_CURVE_ENGINEERING_BLOCKED"
TERMINALS = (T_ENGINEERING_BLOCKED, T_L1_SPECIFIC, T_L2_SPECIFIC,
             T_FINITE_BACKOFF, T_BOTH_WEAK, T_AMBIGUOUS)

FUTURE_ROOT = ("workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-"
               "a5c6-d7e8f9a0b1c2")
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d15_margin_curve_development.py "
    "--d15-batch --execution-authorized --model-f-root %s --out-root %s"
    % (MODEL_F_INPUT_ROOT, FUTURE_ROOT)
)
AUTHORIZATION = (
    "separate explicit user/main-thread authorization required before "
    "--d15-batch")

EVIDENCE_FILES = ("manifest.json", "decoder_records.csv",
                  "graph_records.csv", "arm_summary.csv", "summary.json",
                  "command_log.txt")

#: Scope tag carried by every D15 decoder record. The gate constructor only
#: accepts records carrying this tag, so predecessor evidence (different
#: roots, schemas, seeds and no D15 batch tag) cannot enter the D15 gate.
D15_BATCH_ID = "d15-margin-curve-v1"

#: Fresh-range guard: D15 seeds are disjoint from every prior seed set
#: (R2/R3 graphs+blocks, D11 L1/L2 graphs+blocks, D12 graphs+blocks, D14N
#: graphs+blocks).
_PRIOR_SEEDS = (
    {s for seeds in r2.GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in r2.BLOCK_SEEDS.values() for s in seeds}
    | {s for seeds in r3.GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in r3.BLOCK_SEEDS.values() for s in seeds}
    | {s for seeds in d11.L1_GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in d11.L1_BLOCK_SEEDS.values() for s in seeds}
    | {s for seeds in d11.L2_GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in d12.GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in d12.BLOCK_SEEDS.values() for s in seeds}
    | set(d14n.L1_GRAPH_SEEDS) | set(d14n.L2_GRAPH_SEEDS)
    | set(d14n.BLOCK_SEEDS))
_D15_GRAPH = {s for seeds in GRAPH_SEEDS.values() for s in seeds}
_D15_BLOCK = set(BLOCK_SEEDS)
if len(_D15_GRAPH) != 36 or len(_D15_BLOCK) != 8:
    raise ValueError("D15 frozen seed sets have wrong cardinality")
if not _D15_GRAPH.isdisjoint(_D15_BLOCK):
    raise ValueError("D15 graph/block seeds overlap")
if not _D15_GRAPH.isdisjoint(_PRIOR_SEEDS) \
        or not _D15_BLOCK.isdisjoint(_PRIOR_SEEDS):
    raise ValueError("D15 seed collides with a prior seed")
del _PRIOR_SEEDS, _D15_GRAPH, _D15_BLOCK


# --------------------------------------------------------------------------- #
# Rate math (computed from the frozen loads, never copied as constants)
# --------------------------------------------------------------------------- #
def disclosed_bits(rows: int) -> int:
    """Disclosed bits for an integer row count (5 bits per row)."""
    return int(rows) * BITS_PER_ROW


def effective_factor(layer: str, rows: int) -> float:
    """Exact effective disclosure factor disclosed/load for one cell."""
    key = str(layer)
    if key == "L1":
        return disclosed_bits(rows) / LOAD_L1
    if key == "L2":
        return disclosed_bits(rows) / LOAD_L2
    raise KeyError("unknown D15 layer %r" % (layer,))


def _cell_layer(profile: str) -> str:
    if str(profile) in L1_PROFILES:
        return "L1"
    if str(profile) == ORACLE_PROFILE:
        return "L2"
    raise KeyError("unknown D15 profile %r" % (profile,))


def _plan_arm(profile: str) -> str:
    if str(profile) in L1_PROFILES:
        return str(profile)
    if str(profile) == ORACLE_PROFILE:
        return ORACLE_ARM
    raise KeyError("unknown D15 profile %r" % (profile,))


# --------------------------------------------------------------------------- #
# Degree cells and graph construction (R2 path reused, never duplicated)
# --------------------------------------------------------------------------- #
def degree_cell(profile: str, rows: int) -> dict[str, Any]:
    """Return the frozen D15 ``(n, m, var/check counts, E)`` cell + rate."""
    key = (str(profile), int(rows))
    if key not in CHECK_TABLE:
        raise KeyError("unknown D15 cell %r" % (key,))
    layer = _cell_layer(str(profile))
    var_counts = dict(VAR_PROFILES[str(profile)])
    check_counts = dict(CHECK_TABLE[key])
    var_sockets = sum(int(d) * int(c) for d, c in var_counts.items())
    check_sockets = sum(int(d) * int(c) for d, c in check_counts.items())
    if sum(var_counts.values()) != N:
        raise ValueError("frozen cell %r variable counts do not sum to n"
                         % (key,))
    if sum(check_counts.values()) != int(rows):
        raise ValueError("frozen cell %r check counts do not sum to m"
                         % (key,))
    if var_sockets != check_sockets:
        raise ValueError("frozen cell %r socket mismatch" % (key,))
    if var_sockets != EDGE_TOTALS[str(profile)]:
        raise ValueError("frozen cell %r edge total != frozen E" % (key,))
    return {"n": N, "m": int(rows), "layer": layer,
            "var_counts": var_counts, "check_counts": check_counts,
            "E": var_sockets, "disclosed_bits": disclosed_bits(rows),
            "effective_factor": effective_factor(layer, rows)}


def _compose_graph(cell: Mapping[str, Any], graph_seed: int,
                   arm_label: str) -> dict[str, Any]:
    """One construction path: accepted PEG + coefficients + A1–A6 admission.

    Shared by both layer families; only the frozen cell (and hence the
    forced degree/socket profile) differs. Any failure is retained with
    ``admitted=False``; seeds are never altered, repaired or searched.
    """
    construction = r2.build_degree_sequence_peg(
        int(cell["n"]), int(cell["m"]), cell["var_counts"],
        cell["check_counts"], int(graph_seed))
    record: dict[str, Any] = {
        "arm": str(arm_label), "width": N, "graph_seed": int(graph_seed),
        "n": int(cell["n"]), "m": int(cell["m"]), "E": 0, "edges": [],
        "coefficients": [], "dense": None, "structure": None,
        "status": "construction_failed", "admitted": False,
        "failure_reason": construction.get("failure_reason", ""),
    }
    if construction["status"] != "ok":
        return record
    coefficients = r2.coefficients_for_edges(construction["edges"], N,
                                             int(graph_seed))
    dense = r2.dense_from_edges(int(cell["n"]), int(cell["m"]),
                                construction["edges"], coefficients)
    structure = r2.structural_record(dense, cell["var_counts"],
                                     cell["check_counts"])
    replay = r2.build_degree_sequence_peg(
        int(cell["n"]), int(cell["m"]), cell["var_counts"],
        cell["check_counts"], int(graph_seed))
    replay_coeffs = r2.coefficients_for_edges(replay["edges"], N,
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


def build_l1_graph(profile: str, rows: int, graph_seed: int) -> dict[str, Any]:
    """Build one frozen D15 L1 graph (L045 control or L055 challenger)."""
    if str(profile) not in L1_PROFILES:
        raise KeyError("unknown D15 L1 profile %r" % (profile,))
    cell = degree_cell(str(profile), int(rows))  # scope guard
    if int(graph_seed) not in GRAPH_SEEDS[(str(profile), int(rows))]:
        raise ValueError("graph seed %r outside frozen D15 cell %r"
                         % (graph_seed, (str(profile), int(rows))))
    return _compose_graph(cell, int(graph_seed), str(profile))


def build_l2_graph(rows: int, graph_seed: int) -> dict[str, Any]:
    """Build one frozen D15 DV3 L2 graph (ORACLE diagnostic only)."""
    cell = degree_cell(ORACLE_PROFILE, int(rows))  # scope guard
    if int(graph_seed) not in GRAPH_SEEDS[(ORACLE_PROFILE, int(rows))]:
        raise ValueError("graph seed %r outside frozen D15 cell %r"
                         % (graph_seed, (ORACLE_PROFILE, int(rows))))
    return _compose_graph(cell, int(graph_seed), ORACLE_ARM)


# --------------------------------------------------------------------------- #
# Plan: exact call identities (deterministic 288-record plan, D1504)
# --------------------------------------------------------------------------- #
def build_call_plan() -> list[dict[str, Any]]:
    """Frozen paired call matrix: 9 cells x 4 graphs x 8 blocks = 288.

    The same 8 block seeds feed all nine cells (paired blocks). Order:
    point ascending, arm L045 → L055 → L2-ORACLE, graph ascending, block
    ascending; ``call_idx`` contiguous 0..287. Built + validated before any
    decoder binding or Model-F load.
    """
    plan: list[dict[str, Any]] = []
    for point_idx, point_rows in enumerate(POINTS, start=1):
        for profile, rows in zip(("L045", "L055", "L2"), point_rows):
            layer = _cell_layer(profile)
            for graph_seed in GRAPH_SEEDS[(profile, int(rows))]:
                for block_seed in BLOCK_SEEDS:
                    plan.append({
                        "call_idx": len(plan), "point_idx": int(point_idx),
                        "layer": layer, "arm": _plan_arm(profile),
                        "rows": int(rows),
                        "disclosed_bits": disclosed_bits(rows),
                        "effective_factor": effective_factor(layer, rows),
                        "graph_seed": int(graph_seed),
                        "block_seed": int(block_seed)})
    return plan


# --------------------------------------------------------------------------- #
# Gate tallies with a structural predecessor boundary
# --------------------------------------------------------------------------- #
class D15Tallies:
    """Exact-count tallies for the D15 gate (per cell pool + per graph).

    Only exact counts enter the gate; syndrome-valid counts are carried
    separately by the records and never substitute for exact. Instances can
    only be built from ``D15_BATCH_ID``-tagged D15 decoder records (see
    ``tallies_from_d15_records``).
    """

    def __init__(self, cell_graph_counts: Mapping[Any, Sequence[int]]
                 ) -> None:
        if set(cell_graph_counts) != {(_plan_arm(p), int(m))
                                      for p, m in CELLS}:
            raise ValueError("D15 tallies require exactly the nine frozen "
                             "cells")
        pools: dict[Any, int] = {}
        graphs: dict[Any, tuple[int, ...]] = {}
        for key, vec in cell_graph_counts.items():
            vec = tuple(int(v) for v in vec)
            if len(vec) != 4:
                raise ValueError("D15 cells require exactly 4 graphs: %r"
                                 % (key,))
            if any(v < 0 or v > GRAPH_TRIALS for v in vec):
                raise ValueError("per-graph exact counts must lie in 0..8: "
                                 "%r" % (key,))
            graphs[key] = vec
            pools[key] = sum(vec)
        self._pools = pools
        self._graphs = graphs

    def pool(self, arm: str, rows: int) -> int:
        """Exact pool for one frozen cell (32 paired trials)."""
        return int(self._pools[(str(arm), int(rows))])

    def per_graph(self, arm: str, rows: int) -> tuple[int, ...]:
        """Per-graph exact vector for one frozen cell (4 x 0..8)."""
        return tuple(self._graphs[(str(arm), int(rows))])

    def cells(self) -> tuple[Any, ...]:
        """The nine frozen ``(arm, rows)`` cell keys."""
        return tuple(sorted(self._pools))


def tallies_from_d15_records(
        records: Sequence[Mapping[str, Any]]) -> D15Tallies:
    """Build gate tallies exclusively from D15 decoder records.

    Every contributing record must carry ``batch_id == D15_BATCH_ID`` and a
    frozen ``(arm, rows, graph, block)`` identity; each of the nine cells
    must contribute exactly its 4 graphs x 8 blocks; ORACLE rows must be
    marked ungraded and never enter a graded pool. Anything else raises, so
    non-D15 evidence cannot enter the gate.
    """
    if not records:
        raise ValueError("no D15 decoder records")
    plan_keys = {(e["arm"], int(e["rows"]), int(e["graph_seed"]),
                  int(e["block_seed"])) for e in build_call_plan()}
    seen = set()
    counts: dict[Any, dict[int, int]] = {}
    for record in records:
        if record.get("batch_id") != D15_BATCH_ID:
            raise ValueError("record without D15 batch tag cannot enter "
                             "the D15 gate: %r"
                             % ({k: record.get(k) for k in
                                 ("arm", "rows", "graph_seed",
                                  "block_seed", "batch_id")},))
        key = (str(record.get("arm")), int(record["rows"]),
               int(record["graph_seed"]), int(record["block_seed"]))
        if key not in plan_keys:
            raise ValueError("record identity outside frozen D15 plan: %r"
                             % (key,))
        if key in seen:
            raise ValueError("duplicate D15 record identity: %r" % (key,))
        seen.add(key)
        arm = key[0]
        if arm == ORACLE_ARM:
            if bool(record.get("graded", True)):
                raise ValueError("ORACLE record must be ungraded")
        elif arm in L1_PROFILES:
            if not bool(record.get("graded", False)):
                raise ValueError("L1 record must be graded")
        else:
            raise ValueError("record arm outside D15 arms: %r" % (arm,))
        cell = (arm, key[1])
        counts.setdefault(cell, {}).setdefault(key[2], 0)
        counts[cell][key[2]] += 1 if record["exact"] else 0
    if seen != plan_keys:
        raise ValueError("D15 records cover %d/288 planned identities "
                         "(zero-skip)" % len(seen))
    ordered: dict[Any, list[int]] = {}
    for profile, rows in CELLS:
        arm = _plan_arm(profile)
        seeds = GRAPH_SEEDS[(profile, int(rows))]
        ordered[(arm, int(rows))] = [counts[(arm, int(rows))].get(s, 0)
                                    for s in seeds]
    return D15Tallies(ordered)


def is_cell_adequate(tallies: D15Tallies, arm: str, rows: int) -> bool:
    """Frozen adequate-cell predicate (pool + multi-graph support)."""
    if not isinstance(tallies, D15Tallies):
        raise TypeError("cell predicates accept only D15Tallies")
    vec = tallies.per_graph(str(arm), int(rows))
    return sum(vec) >= CELL_ADEQUATE_MIN \
        and sum(1 for v in vec if v >= ADEQUATE_GRAPH_MIN) \
        >= ADEQUATE_GRAPHS_MIN


def is_cell_weak(tallies: D15Tallies, arm: str, rows: int) -> bool:
    """Frozen weak-cell predicate (pool + multi-graph support)."""
    if not isinstance(tallies, D15Tallies):
        raise TypeError("cell predicates accept only D15Tallies")
    vec = tallies.per_graph(str(arm), int(rows))
    return sum(vec) <= CELL_WEAK_MAX \
        and sum(1 for v in vec if v <= WEAK_GRAPH_MAX) >= WEAK_GRAPHS_MIN


def _arm_pools(tallies: D15Tallies, arm: str,
               rows_seq: Sequence[int]) -> list[int]:
    return [tallies.pool(str(arm), int(m)) for m in rows_seq]


def monotonicity_report(tallies: D15Tallies) -> dict[str, Any]:
    """Cross-point monotonicity per arm (reported, never repaired).

    Pools are ordered by ascending rows within each arm; any decrease step
    is a violation. The routing gate requires non-decreasing pools for its
    layer-specific and finite-backoff claims; a violation falls through to
    a weaker terminal — it is never smoothed, dropped or re-scored.
    """
    if not isinstance(tallies, D15Tallies):
        raise TypeError("monotonicity accepts only D15Tallies")
    arms: dict[str, Sequence[int]] = {
        "L045": ROWS_L1, "L055": ROWS_L1, ORACLE_ARM: ROWS_L2}
    report: dict[str, Any] = {"arms": {}, "violations": []}
    for arm, rows_seq in arms.items():
        pools = _arm_pools(tallies, arm, rows_seq)
        steps = [{"from_rows": int(a), "to_rows": int(b),
                  "from_pool": int(x), "to_pool": int(y),
                  "non_decreasing": bool(y >= x)}
                 for a, b, x, y in zip(rows_seq, rows_seq[1:],
                                       pools, pools[1:])]
        bad = [s for s in steps if not s["non_decreasing"]]
        report["arms"][arm] = {
            "rows": [int(m) for m in rows_seq], "pools": pools,
            "non_decreasing": not bad, "steps": steps}
        for step in bad:
            report["violations"].append({"arm": arm, **step})
    report["all_non_decreasing"] = not report["violations"]
    return report


def wilson_interval(exact: int, trials: int, z: float = 1.96
                    ) -> tuple[float, float]:
    """95% Wilson score interval for one cell pool (descriptive only).

    Never gating: the route vocabulary sees only exact counts plus the
    preregistered thresholds. Reported so a future audit can read margin
    uncertainty without refitting anything.
    """
    k = int(exact)
    n = int(trials)
    if not 0 <= k <= n or n <= 0:
        raise ValueError("wilson needs 0 <= exact <= trials, trials > 0")
    z = float(z)
    center = (k + z * z / 2.0) / (n + z * z)
    half = z * math.sqrt(k * (n - k) / float(n) + z * z / 4.0) / (n + z * z)
    return (max(0.0, center - half), min(1.0, center + half))


def describe_paired_l1(
        l045_by_trial: Mapping[tuple[int, int], bool],
        l055_by_trial: Mapping[tuple[int, int], bool]) -> dict[str, Any]:
    """Descriptive paired L055-only/L045-only discordances (never gating).

    Inputs map ``(graph_ordinal, block_seed)`` to exact over the 32
    block-matched trials of one row point (same m, same 8 blocks, graph
    ordinals in frozen seed order on both sides). Reported descriptively
    only; the routing gate never sees it.
    """
    challenger_only = reference_only = concordant = 0
    for ordinal in range(4):
        for block_seed in BLOCK_SEEDS:
            key = (int(ordinal), int(block_seed))
            try:
                chal_ok = bool(l055_by_trial[key])
                ref_ok = bool(l045_by_trial[key])
            except KeyError:
                raise ValueError("unpaired D15 L1 trials at ordinal=%d "
                                 "block=%d" % key) from None
            if chal_ok and not ref_ok:
                challenger_only += 1
            elif ref_ok and not chal_ok:
                reference_only += 1
            else:
                concordant += 1
    return {"challenger_only": challenger_only,
            "reference_only": reference_only,
            "concordant": concordant,
            "trials": challenger_only + reference_only,
            "cells": 32, "descriptive_only": True}


def route_terminal(tallies: D15Tallies, engineering_reason: str = "") -> str:
    """Frozen terminal routing (prereg design §7, first match wins).

    Only graded exact pools plus the preregistered cell predicates enter;
    L045/L055 discordances, Wilson intervals and monotonicity magnitudes
    are descriptive only and structurally cannot reach this function. The
    highest matched-margin point (L1-m118 / L2-m89) anchors every
    layer-specific claim; cross-point monotonic evidence and multi-graph
    support (inside the cell predicates) are REQUIRED; no single pooled
    count closes the route.
    """
    if not isinstance(tallies, D15Tallies):
        raise TypeError("route_terminal accepts only D15Tallies "
                        "(non-D15 evidence cannot enter the D15 gate)")
    if engineering_reason:
        return T_ENGINEERING_BLOCKED
    mono = monotonicity_report(tallies)
    l1_high_weak = is_cell_weak(tallies, "L045", 118) \
        and is_cell_weak(tallies, "L055", 118)
    l1_high_ok = is_cell_adequate(tallies, "L045", 118) \
        and is_cell_adequate(tallies, "L055", 118)
    l2_high_weak = is_cell_weak(tallies, ORACLE_ARM, 89)
    l2_high_ok = is_cell_adequate(tallies, ORACLE_ARM, 89)
    l1_mono = mono["arms"]["L045"]["non_decreasing"] \
        and mono["arms"]["L055"]["non_decreasing"]
    l2_mono = mono["arms"][ORACLE_ARM]["non_decreasing"]
    if l1_high_weak and l2_high_ok and l1_mono:
        return T_L1_SPECIFIC
    if l2_high_weak and l1_high_ok and l2_mono:
        return T_L2_SPECIFIC
    low_weak = is_cell_weak(tallies, "L045", 110) \
        and is_cell_weak(tallies, "L055", 110) \
        and is_cell_weak(tallies, ORACLE_ARM, 83)
    high_ok = l1_high_ok and l2_high_ok
    if low_weak and high_ok and mono["all_non_decreasing"]:
        return T_FINITE_BACKOFF
    if all(is_cell_weak(tallies, arm, rows)
           for arm, rows in tallies.cells()):
        return T_BOTH_WEAK
    return T_AMBIGUOUS


# --------------------------------------------------------------------------- #
# Dispatch: shared paired identities; ungraded ORACLE diagnostic
# --------------------------------------------------------------------------- #
def _tag_l1(record: Mapping[str, Any], entry: Mapping[str, Any]) -> dict:
    out = dict(record)
    out.update({
        "point_idx": int(entry["point_idx"]), "layer": "L1",
        "arm": str(entry["arm"]), "rows": int(entry["rows"]),
        "disclosed_bits": int(entry["disclosed_bits"]),
        "effective_factor": float(entry["effective_factor"]),
        "graph_seed": int(entry["graph_seed"]),
        "block_seed": int(entry["block_seed"]),
        "batch_id": D15_BATCH_ID, "oracle": False, "graded": True,
        "source_exact": bool(record["exact"]),
        "target_exact": False, "joint_exact": False,
        "undetected": False,
    })
    return out


def run_l2_oracle_cell(l2_graph: Mapping[str, Any],
                       block: Mapping[str, Any],
                       entry: Mapping[str, Any], *, decode_fn, syndrome_fn,
                       oracle_prior_fn, call_idx: int) -> dict[str, Any]:
    """One L2 ORACLE call under true-L1 conditioning (diagnostic, ungraded).

    ``oracle_prior_fn`` is explicitly injected (the future authorized
    runner binds the accepted true-L1 conditional prior). Records are
    marked ``ORACLE``/ungraded and excluded from all graded pools; only
    the pooled oracle-exact count enters the gate via the cell predicates.
    """
    if l2_graph.get("dense") is None or not bool(l2_graph.get("admitted")):
        raise StructureNotAdmitted(
            "refusing decoder binding for non-admitted L2 graph %r"
            % ({"graph_seed": l2_graph.get("graph_seed")},))
    if decode_fn is None or not callable(decode_fn):
        raise ValueError("decode_fn must be explicitly injected")
    if syndrome_fn is None or not callable(syndrome_fn):
        raise ValueError("syndrome_fn must be explicitly injected")
    if oracle_prior_fn is None or not callable(oracle_prior_fn):
        raise ValueError("oracle_prior_fn must be explicitly injected")
    import numpy as np

    H = np.asarray(l2_graph["dense"], dtype=np.uint8)
    u2 = np.asarray(block["u2"], dtype=np.int64)
    prior = np.asarray(oracle_prior_fn(block), dtype=np.float64)
    t0 = time.perf_counter()
    try:
        syn = np.asarray(syndrome_fn(H, u2), dtype=np.uint8)
        result = decode_fn(H, prior, syn, max_iter=DECODER_MAX_ITER,
                           damping_alpha=DAMPING_ALPHA, warm_beliefs=None,
                           field=None)
        x_hat = np.asarray(result.x_hat)
        syndrome_ok = bool(result.syndrome_ok)
        exact = bool(syndrome_ok and x_hat.shape == u2.shape
                     and np.array_equal(x_hat, u2))
        residual = int(np.count_nonzero(np.asarray(syndrome_fn(H, x_hat))
                                        != syn))
        return {
            "call_idx": int(call_idx), "point_idx": int(entry["point_idx"]),
            "layer": "L2", "arm": ORACLE_ARM, "rows": int(entry["rows"]),
            "disclosed_bits": int(entry["disclosed_bits"]),
            "effective_factor": float(entry["effective_factor"]),
            "graph_seed": int(entry["graph_seed"]),
            "block_seed": int(entry["block_seed"]),
            "batch_id": D15_BATCH_ID, "oracle": True, "graded": False,
            "exact": exact, "syndrome_ok": syndrome_ok,
            "source_exact": False, "target_exact": exact,
            "joint_exact": False, "undetected": False,
            "iterations": int(result.iterations),
            "status": str(result.status),
            "residual_syndrome_weight": residual,
            "belief_provenance": "ORACLE",
            "crash": False, "error": "",
            "wall_s": time.perf_counter() - t0,
        }
    except Exception as exc:  # retained crash record; never retried
        return {
            "call_idx": int(call_idx), "point_idx": int(entry["point_idx"]),
            "layer": "L2", "arm": ORACLE_ARM, "rows": int(entry["rows"]),
            "disclosed_bits": int(entry["disclosed_bits"]),
            "effective_factor": float(entry["effective_factor"]),
            "graph_seed": int(entry["graph_seed"]),
            "block_seed": int(entry["block_seed"]),
            "batch_id": D15_BATCH_ID, "oracle": True, "graded": False,
            "exact": False, "syndrome_ok": False,
            "source_exact": False, "target_exact": False,
            "joint_exact": False, "undetected": False,
            "iterations": -1, "status": "crash",
            "residual_syndrome_weight": -1,
            "belief_provenance": "ORACLE",
            "crash": True, "error": repr(exc)[:300],
            "wall_s": time.perf_counter() - t0,
        }


def execute_plan(plan: Sequence[Mapping[str, Any]],
                 graphs_l1: Mapping[Any, Mapping[str, Any]],
                 graphs_l2: Mapping[Any, Mapping[str, Any]],
                 blocks: Mapping[int, Mapping[str, Any]],
                 decode_fn, syndrome_fn, *,
                 oracle_prior_fn=None,
                 now=None, rss_fn=None,
                 wall_budget_s: float = WALL_BUDGET_S,
                 per_call_budget_s: float = PER_CALL_BUDGET_S,
                 rss_budget_bytes: int = RSS_BUDGET_BYTES,
                 call_ceiling: int = SCIENTIFIC_CALL_CEILING
                 ) -> dict[str, Any]:
    """Dispatch the frozen plan through injected decoders (fake-testable).

    All 36 graphs are admission-checked before any decoder binding; any
    failure engineering-blocks with zero decoder calls and no seed change.
    Each block object is shared across all nine cells (paired blocks).
    Decoder crashes are retained, never retried.
    """
    now = now or time.monotonic
    t0 = float(now())
    failure: str | None = None
    for profile, rows in CELLS:
        for graph_seed in GRAPH_SEEDS[(profile, int(rows))]:
            if profile in L1_PROFILES:
                graph = graphs_l1.get((profile, int(rows),
                                       int(graph_seed)))
            else:
                graph = graphs_l2.get((int(rows), int(graph_seed)))
            if graph is None or not bool(graph.get("admitted")):
                failure = ("graph (profile=%s, rows=%d, seed=%d) not "
                           "admitted; blocked without seed replacement"
                           % (profile, int(rows), int(graph_seed)))
                break
        if failure is not None:
            break
    records: list[dict[str, Any]] = []
    if failure is None:
        for entry in plan:
            if len(records) >= int(call_ceiling):
                failure = "scientific call ceiling reached"
                break
            arm = str(entry["arm"])
            call_t0 = float(now())
            if arm in L1_PROFILES:
                graph = graphs_l1[(arm, int(entry["rows"]),
                                   int(entry["graph_seed"]))]
                record = _tag_l1(
                    r2.dispatch_l1(
                        graph, blocks[int(entry["block_seed"])], {
                            "width": N, "arm": arm,
                            "graph_seed": int(entry["graph_seed"]),
                            "block_seed": int(entry["block_seed"])},
                        decode_fn, syndrome_fn,
                        call_idx=len(records)),
                    entry)
            elif arm == ORACLE_ARM:
                if oracle_prior_fn is None:
                    raise ValueError(
                        "oracle_prior_fn must be explicitly injected "
                        "for L2 ORACLE")
                record = run_l2_oracle_cell(
                    graphs_l2[int(entry["rows"]),
                              int(entry["graph_seed"])],
                    blocks[int(entry["block_seed"])], entry,
                    decode_fn=decode_fn, syndrome_fn=syndrome_fn,
                    oracle_prior_fn=oracle_prior_fn,
                    call_idx=len(records))
            else:
                raise ValueError("plan arm outside D15 arms: %r" % (arm,))
            record["wall_s"] = max(float(now()) - call_t0, 0.0)
            records.append(record)
            if record.get("crash"):
                failure = "decoder crash: %s" % record.get("error", "")
            elif float(record["wall_s"]) > float(per_call_budget_s):
                failure = ("per-call wall budget exceeded: %.3f s"
                           % float(record["wall_s"]))
            elif float(now()) - t0 > float(wall_budget_s):
                failure = "wall budget exceeded"
            elif rss_fn is not None \
                    and int(rss_fn()) >= int(rss_budget_bytes):
                failure = "RSS budget exceeded"
            if failure is not None:
                break
    return {
        "records": records,
        "engineering_reason": failure or "",
        "decoder_calls": len(records),
    }


# --------------------------------------------------------------------------- #
# Pre-decoder profile: all 36 future graphs, no decoder, no root
# --------------------------------------------------------------------------- #
def profile_graphs(build_l1_fn=None, build_l2_fn=None,
                   now=None) -> dict[str, Any]:
    """Bounded profile: build all 36 frozen D15 graphs, no decoder, no root.

    Reports per object the component count, structural/GF32 rank,
    four-cycle count, girth, realized degree histograms and the A1–A6
    admission outcome. A frozen seed that cannot produce an admitted
    graph is retained as-is; no replacement seed exists or is consumed
    (zero replacement seeds by construction).
    """
    build_l1_fn = build_l1_fn or build_l1_graph
    build_l2_fn = build_l2_fn or build_l2_graph
    now = now or time.perf_counter
    t0 = float(now())
    entries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    def _entry(graph: Mapping[str, Any], wall: float) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "arm": str(graph["arm"]), "width": int(graph["width"]),
            "seed": int(graph["graph_seed"]),
            "n": int(graph["n"]), "m": int(graph["m"]),
            "E": int(graph["E"]), "status": str(graph["status"]),
            "admitted": bool(graph["admitted"]),
            "construction_wall_s": round(float(wall), 6),
            "failure_reason": str(graph["failure_reason"]),
        }
        structure = graph.get("structure")
        if structure:
            entry.update({
                "variable_degree_histogram": {
                    str(k): int(v) for k, v in
                    structure["variable_degree_histogram"].items()},
                "check_degree_histogram": {
                    str(k): int(v) for k, v in
                    structure["check_degree_histogram"].items()},
                "rank": int(structure["rank"]),
                "structural_rank": int(structure["structural_rank"]),
                "gf32_rank": int(structure["gf32_rank"]),
                "admission": {str(k): bool(v) for k, v in
                              structure["admission"].items()},
                "connected_components":
                    int(structure["connected_components"]),
                "min_check_degree": int(structure["min_check_degree"]),
                "four_cycles": int(structure["four_cycles"]),
                "girth": structure["girth"],
            })
        return entry

    for profile, rows in CELLS:
        for graph_seed in GRAPH_SEEDS[(profile, int(rows))]:
            start = float(now())
            if profile in L1_PROFILES:
                graph = build_l1_fn(profile, int(rows), int(graph_seed))
            else:
                graph = build_l2_fn(int(rows), int(graph_seed))
            entry = _entry(graph, float(now()) - start)
            entry["rows"] = int(rows)
            entry["layer"] = _cell_layer(profile)
            entries.append(entry)
            if not graph["admitted"]:
                failures.append({"family": entry["layer"],
                                 "profile": profile, "rows": int(rows),
                                 "seed": int(graph_seed),
                                 "status": entry["status"],
                                 "failure_reason": entry["failure_reason"]})
    return {
        "graphs": entries,
        "seed_replacements": [],
        "replacement_seeds_used": 0,
        "frozen_seed_failures": failures,
        "wall_s": float(now()) - t0,
    }
