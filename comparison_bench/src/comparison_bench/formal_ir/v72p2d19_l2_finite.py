"""V72P2D19 L2 finite-ensemble validation — readiness plan/graphs/gates.

Change: ``v72p2d19-l2-finite-ensemble-validation``
Frozen authority: ``.workbuddy/tasks/D19_L2_FINITE_ENSEMBLE_VALIDATION_READINESS_R1_TASK_PACKET.md``
(§§1–11) + ``openspec/changes/v72p2d19-l2-finite-ensemble-validation/``
(design §§2–9, delta spec, tasks). Track: implementation/readiness (zero
scientific decoder/DE calls; no D19 batch, no APP/D7-H/real data, no
commit/push).

Frozen matrix (implement EXACTLY; STOP on any drift need — F02 proved
arithmetic, do not re-amend):

- Single rate point m/n = 94/128, ``delta_L2=0.44915511536562214``; winner
  arm ``L020`` (``lam_d2_0.20_d3_0.80`` via ``d18.candidate_id_for_x``)
  against DV3 control. No near-tie arm (0.15/0.25 never enter).
- Four cells: n128/DV3 ``3^128`` E384 ``4^86+5^8``; n128/L020 ``2^35+3^93``
  E349 ``3^27+4^67``; n256/DV3 ``3^256`` E768 ``4^172+5^16``; n256/L020
  ``2^70+3^186`` E698 ``3^54+4^134``.
- Graph seeds n128 ``2026094401..4406``, n256 ``2026094407..4412``; block
  seeds n128 ``2026094501..4508``, n256 ``2026094511..4518``; disjointness
  proven at import (fail-closed). Both arms share graph-seed labels and
  the same eight source blocks per width; graphs stay arm-specific.
- Order width→graph→block→arm; n128 96 calls; n256 96 calls dispatched
  ONLY after a frozen n128 POSITIVE gate; max 192; controls never advance.
- L2 channel is true-U1-conditioned ORACLE, diagnostic-only, ungraded;
  no APP/transfer/L1 anywhere in this module.

Reuse contract (IMPORT — no duplication of construction/admission
semantics, no copied decoder/GF32 kernels):

- shared connectivity-first constructor: ``r2.build_degree_sequence_peg``;
- binding admission A1–A6: ``r2.structural_record`` (A6 replay mirrors the
  accepted ``r2.build_graph`` composition, applied to the frozen D19
  cells — never to a predecessor cell);
- L2 oracle dispatch: ``r2.dispatch_l1`` (shared reference) fed the
  remapped ``{"u1": u2, "prior": oracle_prior}`` block, then tagged
  ORACLE/ungraded (mirrors the accepted D16 oracle-cell semantics);
- coefficient primitive: ``common.v10_seed`` under the single frozen
  namespace ``d19:l2:coeff:{width}:{arm}:{graph_seed}`` (arm included
  because both arms share graph-seed labels; ``r2.coefficient_seed`` is
  NOT reused — its namespace lacks the arm and would collide);
- block sampling / oracle prior: the accepted ``d5.sample_matched_block``
  / ``d5.oracle_l2_prior`` true-conditioned path (bound by the authorized
  runner only; this module never loads Model-F content);
- winner provenance: frozen D18 strings (live cross-check in a
  subprocess test, so no fake path imports that chain);
- seed guard: named-union over R2/R3/D11/D12/D14N/D15/D16 sets plus a
  frozen D18-and-below numeric floor (provenance in code);
- descriptive Wilson helper: ``d15.wilson_interval`` (pure math,
  re-exported by reference, never reimplemented);
- root refusal: ``r2.refuse_out_root``; decoder contract
  (``max_iter=90``, ``damping 1.0``, cold start, q=32/poly37), Model-F
  root, RSS budget.

Added here (D19 deltas only): the four frozen cells, fresh D19 seeds, the
192-identity max plan with conditional n256 dispatch, the frozen width
gates plus four terminals, the oracle-dispatch tag, the paired b/c
helper, and the 24-object pre-decoder profile. There is no
replacement-seed mechanism anywhere in this module: admission failure
blocks with no seed change. This module never imports the production
decoder and never loads Model-F content.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from . import nonbinary_v10_common as common
from . import v72p2d10_mixed_degree_l1 as r2
from . import v72p2d10_r3_fresh_scaling as r3
from . import v72p2d11_forward_app as d11
from . import v72p2d12_finite_l1_degree as d12
from . import v72p2d14n_calibrated_discriminator as d14n
from . import v72p2d15_margin_curve as d15
from . import v72p2d16_matched_backoff as d16
from . import v72p2d5_gf32_rate_mother as d5

__all__ = [
    "CHANGE_ID", "CYCLE_ID", "TRACK", "CLAIM_CEILING",
    "WINNER_X", "WINNER_ID", "DV3_ID", "ARMS", "ARM_ROLE", "ARM_CANDIDATE",
    "WIDTHS", "ROWS", "BITS_PER_ROW", "DELTA_L2",
    "VAR_PROFILES", "CHECK_TABLE", "EDGE_TOTALS",
    "GRAPH_SEEDS", "BLOCK_SEEDS", "D19_BATCH_ID",
    "Q", "POLY", "DECODER_MAX_ITER", "DAMPING_ALPHA",
    "MODEL_F_INPUT_ROOT", "PRIOR_CHAIN", "DECODER_FLOOR",
    "SCIENTIFIC_CALL_CEILING", "SETUP_CALL_CEILING", "SETUP_FIXED_UNITS",
    "WALL_BUDGET_S", "PER_CALL_BUDGET_S", "RSS_BUDGET_BYTES",
    "POSITIVE", "NEGATIVE", "AMBIGUOUS", "ENGINEERING_BLOCKED",
    "T_SIGNAL_REPRODUCED", "T_NO_USEFUL_RECOVERY", "T_AMBIGUOUS",
    "T_ENGINEERING_BLOCKED", "TERMINALS",
    "EVIDENCE_FILES", "FUTURE_ROOT", "FUTURE_ROOT_UUID", "FROZEN_COMMAND",
    "AUTHORIZATION", "StructureNotAdmitted",
    "build_degree_sequence_peg", "structural_record", "dense_from_edges",
    "dispatch_l1", "refuse_out_root",
    "sample_matched_block", "oracle_l2_prior", "wilson_interval",
    "disclosed_bits", "degree_cell",
    "coefficient_seed", "coefficients_for_edges",
    "build_graph", "build_call_plan",
    "width_tally", "classify_width", "route_terminal",
    "run_l2_oracle_call", "execute_plan", "profile_graphs",
]

# --------------------------------------------------------------------------- #
# Frozen identifiers (packet §§1–3/§9; design §§1–3/§9; spec normative)
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2d19-l2-finite-ensemble-validation"
CYCLE_ID = "V72P2D19-L2-FINITE-ENSEMBLE"
TRACK = "implementation/readiness"
CLAIM_CEILING = (
    "synthetic finite-length L2-oracle-only diagnostic under the accepted "
    "true-U1-conditioned ORACLE prior and the frozen decoder contract; no "
    "optimality, FER, leakage, SKR, qualification, promotion, publication, "
    "route-closure, APP, L1, D7-H or real-data claim; grants no execution"
)

#: Single accepted arm: the D18 winner by frozen provenance (design §1
#: records the exact-string evidence; the live cross-check against
#: ``d18.candidate_id_for_x`` runs in a subprocess test so no fake path
#: ever imports the production-adjacent D18 chain).
WINNER_X = 0.20
WINNER_ID = "lam_d2_0.20_d3_0.80"
DV3_ID = "lam_d2_0.00_d3_1.00"

ARMS = ("DV3", "L020")
ARM_ROLE = {"DV3": "matched_control", "L020": "D18_selected_winner"}
ARM_CANDIDATE = {"DV3": DV3_ID, "L020": WINNER_ID}
WIDTHS = (128, 256)
ROWS = {128: 94, 256: 188}
BITS_PER_ROW = 5
DELTA_L2 = 0.44915511536562214

#: Frozen degree profiles (packet §2; F02-verified). Only the profile and
#: its implied sockets/checks differ between arms.
VAR_PROFILES = {
    ("DV3", 128): {3: 128},
    ("L020", 128): {2: 35, 3: 93},
    ("DV3", 256): {3: 256},
    ("L020", 256): {2: 70, 3: 186},
}
CHECK_TABLE = {
    ("DV3", 128): {4: 86, 5: 8},
    ("L020", 128): {3: 27, 4: 67},
    ("DV3", 256): {4: 172, 5: 16},
    ("L020", 256): {3: 54, 4: 134},
}
EDGE_TOTALS = {("DV3", 128): 384, ("L020", 128): 349,
               ("DV3", 256): 768, ("L020", 256): 698}

#: Frozen seeds (packet §3): 6 graph labels + 8 blocks per width.
GRAPH_SEEDS = {
    128: tuple(range(2026094401, 2026094407)),
    256: tuple(range(2026094407, 2026094413)),
}
BLOCK_SEEDS = {
    128: tuple(range(2026094501, 2026094509)),
    256: tuple(range(2026094511, 2026094519)),
}

#: Scope tag carried by every D19 decoder record. The gate constructor only
#: accepts records carrying this tag, so predecessor evidence (different
#: roots, schemas, seeds and no D19 batch tag) cannot enter the D19 gate.
D19_BATCH_ID = "d19-l2-finite-v1"

#: Decoder/field/prior contract reused from R2/D5/D15/D16 (no re-declaration).
Q = r2.Q
POLY = r2.POLY
DECODER_MAX_ITER = r2.DECODER_MAX_ITER
DAMPING_ALPHA = r2.DAMPING_ALPHA
MODEL_F_INPUT_ROOT = r2.MODEL_F_INPUT_ROOT
PRIOR_CHAIN = d15.PRIOR_CHAIN
DECODER_FLOOR = d5.DECODER_FLOOR

#: Shared constructor/admission/dispatch/root-refusal (import, not copy).
build_degree_sequence_peg = r2.build_degree_sequence_peg
structural_record = r2.structural_record
dense_from_edges = r2.dense_from_edges
dispatch_l1 = r2.dispatch_l1
refuse_out_root = r2.refuse_out_root
StructureNotAdmitted = r2.StructureNotAdmitted

#: Accepted Model-F sampling + true-conditioned L2 oracle path (import).
sample_matched_block = d5.sample_matched_block
oracle_l2_prior = d5.oracle_l2_prior

#: Descriptive Wilson helper reused by reference (pure math, no seeds).
wilson_interval = d15.wilson_interval

#: Budgets (packet §9; design §9): ≤192 scientific; ≤42 setup = 24 graph
#: objects + 16 width-specific block samples + 2 fixed plan/manifest;
#: wall ≤1800 s total; ≤120 s/call (checked between/after calls only).
SCIENTIFIC_CALL_CEILING = 192
SETUP_CALL_CEILING = 42
SETUP_FIXED_UNITS = 2  # plan build + manifest
WALL_BUDGET_S = 1800.0
PER_CALL_BUDGET_S = 120.0
RSS_BUDGET_BYTES = r2.RSS_BUDGET_BYTES

#: Per-width classification labels and terminals (packet §§6–7).
POSITIVE = "POSITIVE"
NEGATIVE = "NEGATIVE"
AMBIGUOUS = "AMBIGUOUS"
ENGINEERING_BLOCKED = "ENGINEERING_BLOCKED"

T_SIGNAL_REPRODUCED = "D19_L2_FINITE_SIGNAL_REPRODUCED"
T_NO_USEFUL_RECOVERY = "D19_L2_FINITE_NO_USEFUL_RECOVERY"
T_AMBIGUOUS = "D19_L2_FINITE_AMBIGUOUS"
T_ENGINEERING_BLOCKED = "D19_L2_FINITE_ENGINEERING_BLOCKED"
TERMINALS = (T_SIGNAL_REPRODUCED, T_NO_USEFUL_RECOVERY, T_AMBIGUOUS,
             T_ENGINEERING_BLOCKED)

FUTURE_ROOT_UUID = "5f2b8c1d-7a3e-4f90-b6d4-8e1a2c3d4f5a6b"
FUTURE_ROOT = "workspace/d19_l2_finite_ensemble_" + FUTURE_ROOT_UUID
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d19_finite_development.py "
    "--d19-batch --execution-authorized --model-f-root %s --out-root %s"
    % (MODEL_F_INPUT_ROOT, FUTURE_ROOT)
)
AUTHORIZATION = (
    "separate explicit user/main-thread authorization required before "
    "--d19-batch")

EVIDENCE_FILES = ("manifest.json", "decoder_records.csv",
                  "graph_records.csv", "arm_summary.csv", "summary.json",
                  "command_log.txt")

#: Fresh-range guard: D19 seeds are disjoint from every prior seed set
#: (R2/R3 graphs+blocks, D11 L1/L2 graphs+blocks, D12 graphs+blocks, D14N
#: graphs+blocks, D15 graphs+blocks, D16 cells) by named union, plus every
#: D18-stage/banned/D17/D9 seed by a frozen numeric floor: the live
#: ``d18.collect_prior_seeds()`` sets plus D18 stage seeds max out at
#: 2026094308 (provenance: D18 module ranges 4301..4308 / banned
#: 4001..4108 / D17 4200..4208 / D9 1601..1805; re-verified live by a
#: subprocess test so no fake path imports that chain). D19 graph seeds
#: start at 2026094401. Any collision fails closed at import (STOP,
#: packet §10).
_PRIOR_NAMED = (
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
    | set(d14n.BLOCK_SEEDS)
    | {s for seeds in d15.GRAPH_SEEDS.values() for s in seeds}
    | set(d15.BLOCK_SEEDS)
    | {s for seeds in d16.GRAPH_SEEDS.values() for s in seeds}
    | set(d16.BLOCK_SEEDS))
_D18_AND_BELOW_MAX = 2026094308
_D19_GRAPH = {s for seeds in GRAPH_SEEDS.values() for s in seeds}
_D19_BLOCK = {s for seeds in BLOCK_SEEDS.values() for s in seeds}
if len(_D19_GRAPH) != 12 or len(_D19_BLOCK) != 16:
    raise ValueError("D19 frozen seed sets have wrong cardinality")
if not _D19_GRAPH.isdisjoint(_D19_BLOCK):
    raise ValueError("D19 graph/block seeds overlap")
if not _D19_GRAPH.isdisjoint(_PRIOR_NAMED) \
        or not _D19_BLOCK.isdisjoint(_PRIOR_NAMED):
    raise ValueError("D19 seed collides with a prior named seed")
if min(_D19_GRAPH) <= _D18_AND_BELOW_MAX \
        or min(_D19_BLOCK) <= _D18_AND_BELOW_MAX:
    raise ValueError("D19 seed at/below the D18-and-below floor")
del _PRIOR_NAMED, _D19_GRAPH, _D19_BLOCK


# --------------------------------------------------------------------------- #
# Rate math (computed from frozen geometry, never copied as constants)
# --------------------------------------------------------------------------- #
def disclosed_bits(rows: int) -> int:
    """Disclosed bits for an integer row count (5 bits per row)."""
    return int(rows) * BITS_PER_ROW


# --------------------------------------------------------------------------- #
# Degree cells and graph construction (R2 path reused, never duplicated)
# --------------------------------------------------------------------------- #
def degree_cell(arm: str, width: int) -> dict[str, Any]:
    """Return the frozen D19 ``(n, m, var/check counts, E)`` cell + rate."""
    key = (str(arm), int(width))
    if key not in CHECK_TABLE or key not in VAR_PROFILES:
        raise KeyError("unknown D19 cell %r" % (key,))
    var_counts = dict(VAR_PROFILES[key])
    check_counts = dict(CHECK_TABLE[key])
    var_sockets = sum(int(d) * int(c) for d, c in var_counts.items())
    check_sockets = sum(int(d) * int(c) for d, c in check_counts.items())
    if sum(var_counts.values()) != int(width):
        raise ValueError("frozen cell %r variable counts do not sum to n"
                         % (key,))
    if sum(check_counts.values()) != ROWS[int(width)]:
        raise ValueError("frozen cell %r check counts do not sum to m"
                         % (key,))
    if var_sockets != check_sockets:
        raise ValueError("frozen cell %r socket mismatch" % (key,))
    if var_sockets != EDGE_TOTALS[key]:
        raise ValueError("frozen cell %r edge total != frozen E" % (key,))
    return {"n": int(width), "m": ROWS[int(width)],
            "var_counts": var_counts, "check_counts": check_counts,
            "E": var_sockets,
            "disclosed_bits": disclosed_bits(ROWS[int(width)])}


def coefficient_seed(width: int, arm: str, graph_seed: int) -> int:
    """Frozen coefficient stream seed (single D19 namespace, arm included)."""
    return common.v10_seed("d19:l2:coeff:%d:%s:%d"
                           % (int(width), str(arm), int(graph_seed)))


def coefficients_for_edges(edges: Sequence[Sequence[int]], width: int,
                           arm: str, graph_seed: int) -> list[int]:
    """One uniform nonzero GF32 draw per edge in sorted ``(v, c)`` order."""
    rng = np.random.default_rng(coefficient_seed(width, arm, graph_seed))
    out = []
    for _ in sorted((int(v), int(c)) for v, c in
                    (tuple(e) for e in edges)):
        coeff = int(rng.integers(1, Q))
        if coeff == 0:
            raise ValueError("coefficient sampler produced zero")
        out.append(coeff)
    return out


def build_graph(arm: str, width: int, graph_seed: int) -> dict[str, Any]:
    """Build one frozen D19 graph: PEG edges, coefficients, structure.

    Admission A1–A6 is decided before any decoder binding: A1–A5 from the
    structural record plus A6 deterministic replay equality (rebuilding
    ``(arm, width, graph_seed)`` reproduces the identical sorted edge list
    and coefficient stream). Any failure is retained with
    ``admitted=False`` and engineering-blocks the width; seeds are never
    altered, repaired or searched.
    """
    cell = degree_cell(str(arm), int(width))  # scope guard
    if int(graph_seed) not in GRAPH_SEEDS[int(width)]:
        raise ValueError("graph seed %r outside frozen D19 width %r"
                         % (graph_seed, int(width)))
    construction = r2.build_degree_sequence_peg(
        int(cell["n"]), int(cell["m"]), cell["var_counts"],
        cell["check_counts"], int(graph_seed))
    record: dict[str, Any] = {
        "arm": str(arm), "width": int(width),
        "graph_seed": int(graph_seed),
        "n": int(cell["n"]), "m": int(cell["m"]), "E": 0, "edges": [],
        "coefficients": [], "dense": None, "structure": None,
        "status": "construction_failed", "admitted": False,
        "failure_reason": construction.get("failure_reason", ""),
    }
    if construction["status"] != "ok":
        return record
    coefficients = coefficients_for_edges(construction["edges"], int(width),
                                          str(arm), int(graph_seed))
    dense = r2.dense_from_edges(int(cell["n"]), int(cell["m"]),
                                construction["edges"], coefficients)
    structure = r2.structural_record(dense, cell["var_counts"],
                                     cell["check_counts"])
    replay = r2.build_degree_sequence_peg(
        int(cell["n"]), int(cell["m"]), cell["var_counts"],
        cell["check_counts"], int(graph_seed))
    replay_coeffs = coefficients_for_edges(replay["edges"], int(width),
                                           str(arm), int(graph_seed))
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
# Plan: exact call identities (deterministic max 192-record plan)
# --------------------------------------------------------------------------- #
def build_call_plan(widths: Sequence[int] = WIDTHS) -> list[dict[str, Any]]:
    """Frozen paired call matrix: width → graph → block → arm.

    Both arms share graph-seed labels and the same eight source blocks per
    width (paired trials; arm innermost so pairs dispatch adjacently).
    ``call_idx`` is contiguous over the requested widths: n128-only is 96
    calls (0..95); the full max plan is 192 (n256 at 96..191). Built +
    validated before any decoder binding or Model-F load.
    """
    plan: list[dict[str, Any]] = []
    for width in widths:
        width = int(width)
        if width not in WIDTHS:
            raise KeyError("unknown D19 width %r" % (width,))
        for graph_seed in GRAPH_SEEDS[width]:
            for block_seed in BLOCK_SEEDS[width]:
                for arm in ARMS:
                    plan.append({
                        "call_idx": len(plan), "width": width,
                        "n": width, "m": ROWS[width], "arm": str(arm),
                        "role": ARM_ROLE[str(arm)],
                        "candidate_id": ARM_CANDIDATE[str(arm)],
                        "graph_seed": int(graph_seed),
                        "block_seed": int(block_seed),
                        "disclosed_bits": disclosed_bits(ROWS[width])})
    return plan


# --------------------------------------------------------------------------- #
# Gate tallies (exact-only) with a structural predecessor boundary
# --------------------------------------------------------------------------- #
def width_tally(records: Sequence[Mapping[str, Any]],
                width: int) -> dict[str, Any]:
    """Build the exact-only gate tally for one width from D19 records.

    Every contributing record must carry ``batch_id == D19_BATCH_ID`` and a
    frozen ``(arm, width, graph, block)`` identity; the width must
    contribute exactly its 2 arms x 6 graphs x 8 blocks with every row
    marked ORACLE/ungraded. Anything else raises, so non-D19 evidence
    cannot enter the gate. ``b``/``c`` are paired candidate-only /
    control-only exact outcomes over the 48 shared (graph, block) trials.
    """
    width = int(width)
    scoped = [r for r in records if int(r.get("width", -1)) == width]
    plan_keys = {(e["arm"], int(e["width"]), int(e["graph_seed"]),
                  int(e["block_seed"]))
                 for e in build_call_plan((width,))}
    seen = set()
    per_graph: dict[Any, dict[int, int]] = {}
    paired: dict[tuple[int, int], dict[str, bool]] = {}
    for record in scoped:
        if record.get("batch_id") != D19_BATCH_ID:
            raise ValueError("record without D19 batch tag cannot enter "
                             "the D19 gate: %r"
                             % ({k: record.get(k) for k in
                                 ("arm", "width", "graph_seed",
                                  "block_seed", "batch_id")},))
        if bool(record.get("oracle", False)) is not True \
                or bool(record.get("graded", True)) is not False:
            raise ValueError("D19 rows must be ORACLE/ungraded: %r"
                             % ({k: record.get(k) for k in
                                 ("arm", "oracle", "graded")},))
        key = (str(record.get("arm")), int(record["width"]),
               int(record["graph_seed"]), int(record["block_seed"]))
        if key not in plan_keys:
            raise ValueError("record identity outside frozen D19 plan: %r"
                             % (key,))
        if key in seen:
            raise ValueError("duplicate D19 record identity: %r" % (key,))
        seen.add(key)
        arm = key[0]
        if arm not in ARMS:
            raise ValueError("record arm outside D19 arms: %r" % (arm,))
        per_graph.setdefault(arm, {}).setdefault(key[2], 0)
        per_graph[arm][key[2]] += 1 if record["exact"] else 0
        paired.setdefault((key[2], key[3]), {})[arm] = bool(record["exact"])
    if seen != plan_keys:
        raise ValueError("D19 records cover %d/96 planned identities "
                         "(zero-skip)" % len(seen))
    m_g = [per_graph["L020"].get(s, 0) for s in GRAPH_SEEDS[width]]
    c_g = [per_graph["DV3"].get(s, 0) for s in GRAPH_SEEDS[width]]
    outcome = {"L020_only": 0, "DV3_only": 0}
    for pair in paired.values():
        if pair.get("L020") and not pair.get("DV3"):
            outcome["L020_only"] += 1
        elif pair.get("DV3") and not pair.get("L020"):
            outcome["DV3_only"] += 1
    return {"width": width, "M_g": m_g, "C_g": c_g,
            "M": sum(m_g), "C": sum(c_g),
            "b": outcome["L020_only"], "c": outcome["DV3_only"]}


def classify_width(tally: Mapping[str, Any],
                   engineering_reason: str = "") -> str:
    """Frozen per-width classification (packet §6; design §6).

    POSITIVE iff ALL five hold: ``M >= 30/48``; ≥5/6 graphs ``M_g >= 4/8``;
    L020 wins strictly on ≥5/6 graphs; ``b - c >= 12``; ``C <= 20/48``.
    NEGATIVE iff BOTH hold: ``M <= 16/48`` AND ``b - c <= 4``. Otherwise
    AMBIGUOUS. Exact only; thresholds are frozen literals, never adaptive.
    """
    if engineering_reason:
        return ENGINEERING_BLOCKED
    m_g = [int(v) for v in tally["M_g"]]
    c_g = [int(v) for v in tally["C_g"]]
    pooled_m, pooled_c = int(tally["M"]), int(tally["C"])
    if len(m_g) != 6 or len(c_g) != 6:
        raise ValueError("D19 width tally requires exactly 6 graphs")
    if any(v < 0 or v > 8 for v in m_g + c_g):
        raise ValueError("per-graph exact counts must lie in 0..8")
    if pooled_m != sum(m_g) or pooled_c != sum(c_g):
        raise ValueError("pooled counts != per-graph sums")
    discord = int(tally["b"]) - int(tally["c"])
    graphs_adequate = sum(1 for v in m_g if v >= 4)
    graphs_won = sum(1 for pair in zip(m_g, c_g) if pair[0] > pair[1])
    if pooled_m >= 30 and graphs_adequate >= 5 and graphs_won >= 5 \
            and discord >= 12 and pooled_c <= 20:
        return POSITIVE
    if pooled_m <= 16 and discord <= 4:
        return NEGATIVE
    return AMBIGUOUS


def route_terminal(n128: Mapping[str, Any],
                   n256: Mapping[str, Any] | None = None) -> str:
    """Frozen terminal routing (packet §7; design §7).

    n128 NEGATIVE, or n128 POSITIVE then n256 NEGATIVE, closes
    NO_USEFUL_RECOVERY; n128 + n256 POSITIVE closes SIGNAL_REPRODUCED; any
    entered width AMBIGUOUS closes AMBIGUOUS; contract/admission/resource
    failure — including a POSITIVE n128 with no n256 result (incomplete
    plan) — closes ENGINEERING_BLOCKED.
    """
    for result in ([n128] if n256 is None else [n128, n256]):
        if result.get("engineering_reason") \
                or result.get("classification") == ENGINEERING_BLOCKED:
            return T_ENGINEERING_BLOCKED
    n128_class = str(n128.get("classification"))
    if n128_class == NEGATIVE:
        return T_NO_USEFUL_RECOVERY
    if n128_class == AMBIGUOUS:
        return T_AMBIGUOUS
    if n128_class != POSITIVE:
        return T_ENGINEERING_BLOCKED
    if n256 is None:  # POSITIVE with no n256 result: incomplete plan
        return T_ENGINEERING_BLOCKED
    n256_class = str(n256.get("classification"))
    if n256_class == POSITIVE:
        return T_SIGNAL_REPRODUCED
    if n256_class == NEGATIVE:
        return T_NO_USEFUL_RECOVERY
    if n256_class == AMBIGUOUS:
        return T_AMBIGUOUS
    return T_ENGINEERING_BLOCKED


# --------------------------------------------------------------------------- #
# Dispatch: shared paired identities; ungraded ORACLE diagnostic
# --------------------------------------------------------------------------- #
def run_l2_oracle_call(graph: Mapping[str, Any], block: Mapping[str, Any],
                       entry: Mapping[str, Any], *, decode_fn, syndrome_fn,
                       oracle_prior_fn, call_idx: int) -> dict[str, Any]:
    """One L2 ORACLE call under true-U1 conditioning (diagnostic, ungraded).

    Reuses the shared ``r2.dispatch_l1`` kernel on the remapped block
    (``u2`` as the target word, oracle-composed prior), then tags the
    record ORACLE/ungraded under the D19 batch scope. Only exact counts
    enter the gate; syndrome-valid/undetected/iterations/residual are
    carried separately and never substitute for exact. ``oracle_prior_fn``
    is explicitly injected (the future authorized runner binds the
    accepted true-U1 conditional prior). No retry/resume/warm start.
    """
    if graph.get("dense") is None or not bool(graph.get("admitted")):
        raise StructureNotAdmitted(
            "refusing decoder binding for non-admitted D19 graph %r"
            % ({"arm": graph.get("arm"), "width": graph.get("width"),
                "graph_seed": graph.get("graph_seed")},))
    if decode_fn is None or not callable(decode_fn):
        raise ValueError("decode_fn must be explicitly injected")
    if syndrome_fn is None or not callable(syndrome_fn):
        raise ValueError("syndrome_fn must be explicitly injected")
    if oracle_prior_fn is None or not callable(oracle_prior_fn):
        raise ValueError("oracle_prior_fn must be explicitly injected "
                         "for L2 ORACLE")
    remapped = {"u1": np.asarray(block["u2"], dtype=np.int64),
                "prior": np.asarray(oracle_prior_fn(block),
                                    dtype=np.float64)}
    base = r2.dispatch_l1(
        graph, remapped,
        {"width": int(entry["width"]), "arm": str(entry["arm"]),
         "graph_seed": int(entry["graph_seed"]),
         "block_seed": int(entry["block_seed"])},
        decode_fn, syndrome_fn, call_idx=int(call_idx))
    base.update({
        "layer": "L2", "n": int(entry["n"]), "m": int(entry["m"]),
        "role": ARM_ROLE[str(entry["arm"])],
        "candidate_id": ARM_CANDIDATE[str(entry["arm"])],
        "batch_id": D19_BATCH_ID, "oracle": True, "graded": False,
        "belief_provenance": "ORACLE",
        "source_exact": False, "target_exact": bool(base["exact"]),
        "joint_exact": False, "undetected": False,
        "disclosed_bits": disclosed_bits(int(entry["m"])),
    })
    return base


def execute_plan(plan_n128: Sequence[Mapping[str, Any]],
                 plan_n256: Sequence[Mapping[str, Any]] | None,
                 graphs: Mapping[Any, Mapping[str, Any]],
                 blocks: Mapping[int, Mapping[int, Mapping[str, Any]]],
                 decode_fn, syndrome_fn, *,
                 oracle_prior_fn=None,
                 now=None, rss_fn=None,
                 wall_budget_s: float = WALL_BUDGET_S,
                 per_call_budget_s: float = PER_CALL_BUDGET_S,
                 rss_budget_bytes: int = RSS_BUDGET_BYTES,
                 call_ceiling: int = SCIENTIFIC_CALL_CEILING
                 ) -> dict[str, Any]:
    """Dispatch the frozen paired plan with conditional n256 progression.

    All six n128 graphs are admission-checked before any decoder binding;
    any failure engineering-blocks with zero decoder calls and no seed
    change. After n128, the frozen gate decides: n256 dispatches IFF n128
    is POSITIVE (controls never advance independently). Decoder crashes
    are retained, never retried. Resource checks run between/after calls
    only (no in-flight watchdog).
    """
    import time as _time

    now = now or _time.monotonic
    t0 = float(now())
    records: list[dict[str, Any]] = []
    width_results: list[dict[str, Any]] = []
    n256_dispatched = False
    failure: str | None = None

    def _admit(width: int, plan: Sequence[Mapping[str, Any]]) -> str | None:
        required: list[tuple[str, int]] = []
        for entry in plan:
            key = (str(entry["arm"]), int(entry["graph_seed"]))
            if key not in required:
                required.append(key)
        for arm, graph_seed in required:
            graph = graphs.get((arm, int(width), int(graph_seed)))
            if graph is None or not bool(graph.get("admitted")):
                return ("graph (arm=%s, width=%d, seed=%d) not admitted; "
                        "blocked without seed replacement"
                        % (arm, int(width), int(graph_seed)))
        return None

    def _dispatch(width: int,
                  plan: Sequence[Mapping[str, Any]]) -> str | None:
        for entry in plan:
            if len(records) >= int(call_ceiling):
                return "scientific call ceiling reached"
            graph = graphs[(str(entry["arm"]), int(width),
                            int(entry["graph_seed"]))]
            block = blocks[int(width)][int(entry["block_seed"])]
            call_t0 = float(now())
            record = run_l2_oracle_call(
                graph, block, entry, decode_fn=decode_fn,
                syndrome_fn=syndrome_fn, oracle_prior_fn=oracle_prior_fn,
                call_idx=len(records))
            record["wall_s"] = max(float(now()) - call_t0, 0.0)
            records.append(record)
            if record.get("crash"):
                return "decoder crash: %s" % record.get("error", "")
            if float(record["wall_s"]) > float(per_call_budget_s):
                return ("per-call wall budget exceeded: %.3f s"
                        % float(record["wall_s"]))
            if float(now()) - t0 > float(wall_budget_s):
                return "wall budget exceeded"
            if rss_fn is not None \
                    and int(rss_fn()) >= int(rss_budget_bytes):
                return "RSS budget exceeded"
        return None

    failure = _admit(128, plan_n128)
    if failure is None:
        failure = _dispatch(128, plan_n128)
    try:
        tally_n128 = width_tally(records, 128)
    except ValueError as exc:
        if failure is None:
            failure = "n128 tally not rebuildable: %s" % exc
        tally_n128 = {"width": 128, "M_g": [0] * 6, "C_g": [0] * 6,
                      "M": 0, "C": 0, "b": 0, "c": 0}
    class_n128 = classify_width(tally_n128, failure or "")
    width_results.append({"width": 128, "classification": class_n128,
                          "tally": tally_n128,
                          "engineering_reason": failure or ""})
    tally_n256: dict[str, Any] | None = None
    if failure is None and class_n128 == POSITIVE \
            and plan_n256 is not None:
        failure256: str | None = _admit(256, plan_n256)
        n256_before = len(records)
        if failure256 is None:
            failure256 = _dispatch(256, plan_n256)
        n256_dispatched = len(records) > n256_before
        try:
            tally_n256 = width_tally(records, 256)
        except ValueError as exc:
            if failure256 is None:
                failure256 = "n256 tally not rebuildable: %s" % exc
            tally_n256 = {"width": 256, "M_g": [0] * 6, "C_g": [0] * 6,
                          "M": 0, "C": 0, "b": 0, "c": 0}
        width_results.append(
            {"width": 256, "classification": classify_width(
                tally_n256, failure256 or ""),
             "tally": tally_n256,
             "engineering_reason": failure256 or ""})
    n128_result = width_results[0]
    n256_result = width_results[1] if len(width_results) > 1 else None
    return {
        "records": records,
        "width_results": width_results,
        "n256_dispatched": n256_dispatched,
        "terminal": route_terminal(n128_result, n256_result),
        "decoder_calls": len(records),
    }


# --------------------------------------------------------------------------- #
# Pre-decoder profile: all 24 future graphs, no decoder, no root
# --------------------------------------------------------------------------- #
def profile_graphs(build_fn=None, now=None) -> dict[str, Any]:
    """Bounded profile: build all 24 frozen D19 graphs, no decoder, no root.

    Reports per object the component count, structural/GF32 rank,
    four-cycle count, girth, realized degree histograms and the A1–A6
    admission outcome. A frozen seed that cannot produce an admitted
    graph is retained as-is; no replacement seed exists or is consumed
    (zero replacement seeds by construction).
    """
    import time as _time

    build_fn = build_fn or build_graph
    now = now or _time.perf_counter
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

    for width in WIDTHS:
        for arm in ARMS:
            for graph_seed in GRAPH_SEEDS[width]:
                start = float(now())
                graph = build_fn(arm, width, graph_seed)
                entry = _entry(graph, float(now()) - start)
                entries.append(entry)
                if not graph["admitted"]:
                    failures.append({"width": int(width), "arm": arm,
                                     "seed": int(graph_seed),
                                     "status": entry["status"],
                                     "failure_reason":
                                         entry["failure_reason"]})
    return {
        "graphs": entries,
        "seed_replacements": [],
        "replacement_seeds_used": 0,
        "frozen_seed_failures": failures,
        "wall_s": float(now()) - t0,
    }
