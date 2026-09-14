"""V72P2D11 canonical forward APP integration — readiness plan/runner/verifier.

Change: ``v72p2d11-forward-app``
Frozen authority: ``.workbuddy/tasks/D11_FORWARD_APP_INTEGRATION_READINESS_TASK_PACKET.md``
(§2) and ``openspec/changes/v72p2d11-forward-app/`` (design §1–§9, delta
spec). Track: implementation/readiness (zero scientific decoder calls);
the future batch is ``EXPLORE_HEAVY``. D7-H is explicitly out of scope.

Reuse contract (IMPORT — no duplication of message/admission semantics):

- transfer/provenance/q: ``d7e.transfer_prior_l1_to_l2``,
  ``d7e.build_transfer_prior``, ``d7e.check_source_eligibility``,
  ``d7e.softmax_source_q``, ``d7e.require_check_updated``;
- canonical q/APP/oracle/layered pattern: ``d5.canonical_source_q``,
  ``d5.app_fed_l2_prior``, ``d5.canonical_transfer_l2_prior``,
  ``d5.oracle_l2_prior``, ``d5._run_layered_block`` (the accepted one-block
  L1→L2 pattern D11 mirrors), ``d5._require_check_updated_provenance``;
- construction/admission/decoder path: ``r2.build_degree_sequence_peg``,
  ``r2.structural_record``, ``r2.coefficient_seed``,
  ``r2.coefficients_for_edges``, ``r2.dense_from_edges``,
  ``r2.dispatch_l1`` (reference path), ``r2.refuse_out_root``;
- L1 graphs/blocks/cells: ``r3.build_graph`` (accepted R3 seeds/blocks),
  ``r3.GRAPH_SEEDS`` / ``r3.BLOCK_SEEDS`` (shared references).

Added here (D11 successor deltas only): the frozen shared-DV3 L2 degree
cells and seeds, the 360-calls-per-width plan with conditional n256
dispatch, the L1 replay hard gate, the prioritized D11 gates plus the
eight terminals, call accounting, provenance fail-close, the six-file
never-overwrite output contract and the read-only verifier. There is no
replacement-seed mechanism anywhere: admission failure blocks with no
seed change. The L1 degree distribution is never applied to L2.
"""

from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from typing import Any

from . import v72p2d5_gf32_rate_mother as d5
from . import v72p2d7_gf32_cross_layer_discriminator as d7e
from . import v72p2d10_mixed_degree_l1 as r2
from . import v72p2d10_r3_fresh_scaling as r3

__all__ = [
    "CHANGE_ID", "CYCLE_ID", "TRACK", "CLAIM_CEILING",
    "D11_WIDTHS", "BRANCHES", "CONTROL", "MIX", "ORACLE",
    "CONTROL_ARM", "MIX_ARM", "SHARED_L2_ARM",
    "L1_GRAPH_SEEDS", "L1_BLOCK_SEEDS", "L2_GRAPH_SEEDS",
    "L2_DEGREE_TABLE", "REPLAY_MIX", "D11_BATCH_ID",
    "FORWARD_SIGNAL", "TRANSFER_BOTTLENECK", "L2_CODE_BOTTLENECK",
    "FORWARD_AMBIGUOUS", "ENGINEERING_BLOCKED", "NOT_RUN",
    "T_WIDE_RECOVERY", "T_N256_TRANSFER", "T_N256_L2", "T_N256_AMBIGUOUS",
    "T_N128_TRANSFER", "T_N128_L2", "T_N128_AMBIGUOUS",
    "T_ENGINEERING_BLOCKED", "TERMINALS",
    "JM_MIN", "MARGIN_MIN", "PAIR_WINS_MIN", "GRAPHS_GE1_MIN", "JC_MAX",
    "O_MIN", "TRANSFER_L1M_MIN", "TRANSFER_JM_MAX", "L2_O_MAX",
    "PER_WIDTH_CALLS", "SCIENTIFIC_CALL_CEILING", "SETUP_CALL_CEILING",
    "SETUP_UNITS", "WALL_BUDGET_S", "PER_CALL_BUDGET_S",
    "RSS_BUDGET_BYTES", "EVIDENCE_FILES", "FROZEN_COMMAND", "FUTURE_ROOT",
    "FUTURE_ROOT_UUID", "AUTHORIZATION",
    "transfer_prior_l1_to_l2", "build_transfer_prior",
    "check_source_eligibility", "softmax_source_q", "require_check_updated",
    "canonical_source_q", "app_fed_l2_prior", "canonical_transfer_l2_prior",
    "oracle_l2_prior", "run_layered_block",
    "require_check_updated_provenance", "bind_row_layered_decoders",
    "dispatch_l1", "refuse_out_root", "check_updated_token",
    "l2_degree_cell", "build_l1_graph", "build_l2_graph",
    "build_call_plan", "build_full_plan", "n256_permitted",
    "D11WidthTallies", "tallies_from_d11_records", "check_l1_replay",
    "classify_d11", "route_terminal", "describe_paired", "execute_width",
    "profile_graphs",
]

# --------------------------------------------------------------------------- #
# Frozen identifiers (packet §2; design §1/§8)
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2d11-forward-app"
CYCLE_ID = "V72P2D11-FORWARD-APP"
TRACK = "implementation/readiness"
CLAIM_CEILING = (
    "synthetic two-layer forward diagnostic only; no FER, leakage, SKR, "
    "real-data, qualification, promotion, optimality or D7-H claim"
)

D11_WIDTHS = (128, 256)
CONTROL, MIX, ORACLE = "CONTROL", "MIX", "ORACLE"
BRANCHES = (CONTROL, MIX, ORACLE)
#: L1 treatment arms per D11 branch (the only treatment difference).
CONTROL_ARM = "PEG_DV3_MATCHED"
MIX_ARM = "PEG_DV23_LAM2_045"
#: Record label for the shared L2 graph (one per pair, all three branches).
SHARED_L2_ARM = "SHARED_DV3_L2"

#: R3 L1 seeds/blocks reused by shared reference (never re-declared).
L1_GRAPH_SEEDS = r3.GRAPH_SEEDS
L1_BLOCK_SEEDS = r3.BLOCK_SEEDS

#: Frozen shared-DV3 L2 graph seeds (design §3; disjoint from every L1 seed).
L2_GRAPH_SEEDS = {
    128: tuple(range(2026092801, 2026092807)),
    256: tuple(range(2026092901, 2026092907)),
}

#: Frozen shared-DV3 L2 degree cells (design §3 verbatim).
L2_DEGREE_TABLE = {
    128: {"n": 128, "m": 104, "var_counts": {3: 128},
          "check_counts": {3: 32, 4: 72}},
    256: {"n": 256, "m": 208, "var_counts": {3: 256},
          "check_counts": {3: 64, 4: 144}},
}

#: L1 replay hard gate: per-graph L1 exact vectors (packet §2 verbatim).
REPLAY_MIX = {
    128: (4, 4, 2, 5, 3, 5),
    256: (6, 3, 5, 5, 6, 4),
}

#: Scope tag carried by every D11 decoder record (R3/A1 boundary analog).
D11_BATCH_ID = "d11-forward-app-v1"

#: Gate thresholds (packet §2 verbatim).
JM_MIN = 9
MARGIN_MIN = 6
PAIR_WINS_MIN = 4
GRAPHS_GE1_MIN = 3
JC_MAX = 3
O_MIN = 18
TRANSFER_L1M_MIN = 18
TRANSFER_JM_MAX = 3
L2_O_MAX = 6

#: Per-width labels and terminals (packet §2 verbatim).
FORWARD_SIGNAL = "D11_FORWARD_SIGNAL"
TRANSFER_BOTTLENECK = "D11_TRANSFER_BOTTLENECK"
L2_CODE_BOTTLENECK = "D11_L2_CODE_BOTTLENECK"
FORWARD_AMBIGUOUS = "D11_FORWARD_AMBIGUOUS"
ENGINEERING_BLOCKED = "ENGINEERING_BLOCKED"
NOT_RUN = "NOT_RUN"

T_WIDE_RECOVERY = "D11_FORWARD_APP_WIDE_RECOVERY"
T_N256_TRANSFER = "D11_N256_TRANSFER_BOTTLENECK"
T_N256_L2 = "D11_N256_L2_CODE_BOTTLENECK"
T_N256_AMBIGUOUS = "D11_N256_FORWARD_AMBIGUOUS"
T_N128_TRANSFER = "D11_N128_TRANSFER_BOTTLENECK"
T_N128_L2 = "D11_N128_L2_CODE_BOTTLENECK"
T_N128_AMBIGUOUS = "D11_N128_FORWARD_AMBIGUOUS"
T_ENGINEERING_BLOCKED = "D11_ENGINEERING_BLOCKED"
TERMINALS = (T_WIDE_RECOVERY, T_N256_TRANSFER, T_N256_L2, T_N256_AMBIGUOUS,
             T_N128_TRANSFER, T_N128_L2, T_N128_AMBIGUOUS,
             T_ENGINEERING_BLOCKED)

#: Budgets (packet §2: ≤720 scientific; ≤64 setup; wall ≤2400 s; ≤120 s/call).
PER_WIDTH_CALLS = 360
SCIENTIFIC_CALL_CEILING = 720
SETUP_CALL_CEILING = 64
#: 36 graph builds (24 L1 + 12 L2) + 24 block samples + load + plan.
SETUP_UNITS = 36 + 24 + 2
WALL_BUDGET_S = 2400.0
PER_CALL_BUDGET_S = 120.0
RSS_BUDGET_BYTES = r2.RSS_BUDGET_BYTES

FUTURE_ROOT_UUID = "7c1878b5-23a8-4fd8-a395-b5a33a58ea64"
FUTURE_ROOT = "workspace/d11_forward_app_" + FUTURE_ROOT_UUID
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d11_development.py "
    "--forward-batch --model-f-root %s --out-root %s"
    % (r2.MODEL_F_INPUT_ROOT, FUTURE_ROOT)
)
AUTHORIZATION = (
    "separate explicit user/main-thread authorization required before "
    "--forward-batch")

EVIDENCE_FILES = ("manifest.json", "decoder_records.csv",
                  "graph_records.csv", "arm_summary.csv", "summary.json",
                  "command_log.txt")

#: Decoder/field contract reused from R2 (no re-declaration).
DECODER_MAX_ITER = r2.DECODER_MAX_ITER
DAMPING_ALPHA = r2.DAMPING_ALPHA
MODEL_F_INPUT_ROOT = r2.MODEL_F_INPUT_ROOT

# --------------------------------------------------------------------------- #
# Reuse map (design §5): canonical helpers imported unchanged.
# Any reimplementation of transfer/provenance/oracle/admission semantics
# here is explicitly rejected; D11 code below is plan, gates and wiring.
# --------------------------------------------------------------------------- #
transfer_prior_l1_to_l2 = d7e.transfer_prior_l1_to_l2
build_transfer_prior = d7e.build_transfer_prior
check_source_eligibility = d7e.check_source_eligibility
softmax_source_q = d7e.softmax_source_q
require_check_updated = d7e.require_check_updated
canonical_source_q = d5.canonical_source_q
app_fed_l2_prior = d5.app_fed_l2_prior
canonical_transfer_l2_prior = d5.canonical_transfer_l2_prior
oracle_l2_prior = d5.oracle_l2_prior
run_layered_block = d5._run_layered_block
require_check_updated_provenance = d5._require_check_updated_provenance
bind_row_layered_decoders = d7e.bind_row_layered_decoders
dispatch_l1 = r2.dispatch_l1
refuse_out_root = r2.refuse_out_root
#: L1 construction/admission path (accepted R3 seeds/blocks; no seed change).
build_l1_graph = r3.build_graph


def _load_v35():
    """Lazy production v35 bind (never on import); same discipline as D7-E."""
    from . import v35_algorithm_development as v35
    return v35


def check_updated_token() -> str:
    """The canonical ``CHECK_UPDATED`` provenance token (lazy v35 bind)."""
    return _load_v35().BELIEF_PROVENANCE_CHECK_UPDATED


# --------------------------------------------------------------------------- #
# Shared L2 degree cells and construction (accepted constructor, L2 cells)
# --------------------------------------------------------------------------- #
def l2_degree_cell(width: int) -> dict[str, Any]:
    """Return the frozen shared-DV3 L2 ``(n, m, var_counts, check_counts)``.

    Arithmetic closure is re-verified, not hand-trusted: n128
    ``32+72=104=m``, ``32·3+72·4=384=E=128·3``; n256 ``64+144=208=m``,
    ``64·3+144·4=768=E=256·3``. The L1 degree distribution is never
    applied here: L2 variables are all degree 3 by construction.
    """
    width = int(width)
    if width not in L2_DEGREE_TABLE:
        raise KeyError("unknown D11 L2 width %r" % (width,))
    cell = L2_DEGREE_TABLE[width]
    var_sockets = sum(int(d) * int(c)
                      for d, c in cell["var_counts"].items())
    check_sockets = sum(int(d) * int(c)
                        for d, c in cell["check_counts"].items())
    if sum(cell["var_counts"].values()) != cell["n"]:
        raise ValueError("frozen L2 cell variable counts do not sum to n")
    if sum(cell["check_counts"].values()) != cell["m"]:
        raise ValueError("frozen L2 cell check counts do not sum to m")
    if var_sockets != check_sockets:
        raise ValueError("frozen L2 cell socket mismatch")
    if set(cell["var_counts"]) != {3}:
        raise ValueError("L2 cell must be DV3 (L1 profile never applies)")
    return {"n": int(cell["n"]), "m": int(cell["m"]),
            "var_counts": dict(cell["var_counts"]),
            "check_counts": dict(cell["check_counts"]), "E": var_sockets}


def build_l2_graph(width: int, graph_seed: int) -> dict[str, Any]:
    """Build one shared connected/full-rank DV3 L2 graph for a pair.

    Same accepted connectivity-first path as ``r2.build_graph`` (one
    deterministic attempt, A1–A5 from the structural record plus A6
    deterministic replay equality of the edge list and coefficient
    stream), applied to the frozen L2 cell — never to an L1 cell. Any
    failure is retained with ``admitted=False``; seeds are never
    altered, repaired or searched.
    """
    width, graph_seed = int(width), int(graph_seed)
    cell = l2_degree_cell(width)  # scope guard; raises outside L2 widths
    if graph_seed not in L2_GRAPH_SEEDS[width]:
        raise ValueError("graph seed %r outside frozen D11 L2 set for "
                         "width %d" % (graph_seed, width))
    construction = r2.build_degree_sequence_peg(
        cell["n"], cell["m"], cell["var_counts"], cell["check_counts"],
        graph_seed)
    record: dict[str, Any] = {
        "arm": SHARED_L2_ARM, "width": width, "graph_seed": graph_seed,
        "n": cell["n"], "m": cell["m"], "E": 0, "edges": [],
        "coefficients": [], "dense": None, "structure": None,
        "status": "construction_failed", "admitted": False,
        "failure_reason": construction.get("failure_reason", ""),
    }
    if construction["status"] != "ok":
        return record
    coefficients = r2.coefficients_for_edges(construction["edges"], width,
                                             graph_seed)
    dense = r2.dense_from_edges(cell["n"], cell["m"],
                                construction["edges"], coefficients)
    structure = r2.structural_record(dense, cell["var_counts"],
                                     cell["check_counts"])
    replay = r2.build_degree_sequence_peg(
        cell["n"], cell["m"], cell["var_counts"], cell["check_counts"],
        graph_seed)
    replay_coeffs = r2.coefficients_for_edges(replay["edges"], width,
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
# Plan: exact call identities, conditional dispatch
# --------------------------------------------------------------------------- #
def build_call_plan(width: int) -> list[dict[str, Any]]:
    """Frozen paired call matrix for one width: 72 cells x 5 calls = 360.

    One shared L2 graph per ``(graph_seed)`` pair: per ``(graph, block)``
    cell the calls are CONTROL L1, CONTROL L2, MIX L1, MIX L2 and one
    shared ORACLE L2 (diagnostic, true-L1 conditional prior). Order:
    graph seeds ascending, block seeds ascending, branches CONTROL →
    MIX → ORACLE; ``call_idx`` is contiguous over the width (0..359).
    """
    width = int(width)
    if width not in D11_WIDTHS:
        raise KeyError("unknown D11 width %r" % (width,))
    plan: list[dict[str, Any]] = []
    for graph_seed in L1_GRAPH_SEEDS[width]:
        for block_seed in L1_BLOCK_SEEDS[width]:
            for branch, layer in ((CONTROL, "L1"), (CONTROL, "L2"),
                                  (MIX, "L1"), (MIX, "L2"),
                                  (ORACLE, "L2")):
                plan.append({
                    "call_idx": len(plan), "width": width, "branch": branch,
                    "layer": layer, "graph_seed": int(graph_seed),
                    "block_seed": int(block_seed)})
    return plan


def build_full_plan() -> list[dict[str, Any]]:
    """Both widths concatenated (n128 first); at most 720 scientific calls."""
    plan = build_call_plan(128)
    base = len(plan)
    for entry in build_call_plan(256):
        plan.append(dict(entry, call_idx=base + entry["call_idx"]))
    return plan


def n256_permitted(n128_classification: str) -> bool:
    """n256 is dispatched if and only if n128 is ``D11_FORWARD_SIGNAL``."""
    return str(n128_classification) == FORWARD_SIGNAL


# --------------------------------------------------------------------------- #
# Gate arithmetic: metric isolation is structural (exact/syndrome/joint kept
# distinct; syndrome-only rows never substitute for exact).
# --------------------------------------------------------------------------- #
class D11WidthTallies:
    """Isolated counts for one D11 width (six graph pairs, 12 blocks each).

    ``mix_joint``/``ctrl_joint`` are per-graph joint both-exact counts;
    ``mix_l1``/``ctrl_l1`` are per-graph L1 source-exact counts (the replay
    gate reads these, never the joints); ``oracle_exact`` is the pooled
    shared-oracle L2 exact count (0..72); ``transfers_blocked`` counts
    non-oracle L2 rows whose transfer did not invoke (provenance refusal).
    Only exact counts enter the gate; syndrome-valid counts are carried
    separately by the records and never substitute for exact.
    """

    def __init__(self, width: int, mix_joint: Sequence[int],
                 ctrl_joint: Sequence[int], oracle_exact: int,
                 mix_l1: Sequence[int], ctrl_l1: Sequence[int],
                 transfers_blocked: int = 0,
                 all_check_updated: bool = False) -> None:
        width = int(width)
        mix_joint = tuple(int(v) for v in mix_joint)
        ctrl_joint = tuple(int(v) for v in ctrl_joint)
        mix_l1 = tuple(int(v) for v in mix_l1)
        ctrl_l1 = tuple(int(v) for v in ctrl_l1)
        if width not in D11_WIDTHS:
            raise ValueError("unknown D11 width %r" % (width,))
        for name, vec in (("mix_joint", mix_joint),
                          ("ctrl_joint", ctrl_joint), ("mix_l1", mix_l1),
                          ("ctrl_l1", ctrl_l1)):
            if len(vec) != 6:
                raise ValueError("D11 tallies require exactly 6 graph pairs")
            if any(v < 0 or v > 12 for v in vec):
                raise ValueError("per-graph counts for %s must lie in 0..12"
                                 % name)
        oracle_exact = int(oracle_exact)
        if oracle_exact < 0 or oracle_exact > 72:
            raise ValueError("oracle pool must lie in 0..72")
        self.width = width
        self.mix_joint = mix_joint
        self.ctrl_joint = ctrl_joint
        self.oracle_exact = oracle_exact
        self.mix_l1 = mix_l1
        self.ctrl_l1 = ctrl_l1
        self.transfers_blocked = int(transfers_blocked)
        self.all_check_updated = bool(all_check_updated)

    @property
    def joint_mix(self) -> int:
        """Pooled MIX joint both-exact ``J_M`` (72 paired cells)."""
        return sum(self.mix_joint)

    @property
    def joint_ctrl(self) -> int:
        """Pooled CONTROL joint both-exact ``J_C`` (72 paired cells)."""
        return sum(self.ctrl_joint)

    @property
    def mix_l1_pool(self) -> int:
        """Pooled MIX L1 source-exact count (72 paired cells)."""
        return sum(self.mix_l1)


def tallies_from_d11_records(records: Sequence[Mapping[str, Any]],
                             width: int) -> D11WidthTallies:
    """Build gate tallies exclusively from D11 decoder records of one width.

    Every contributing record must carry ``batch_id == D11_BATCH_ID`` and a
    frozen ``(branch, layer, graph_seed, block_seed)`` identity; each of the
    72 ``(graph, block)`` cells must contribute exactly the five planned
    rows (CONTROL L1/L2, MIX L1/L2, shared ORACLE L2). Joint counts are
    ``L1-exact AND L2-exact`` per cell; syndrome-only rows never count as
    exact. Anything else raises, so non-D11 evidence cannot enter the gate.
    """
    width = int(width)
    scoped = [r for r in records if int(r["width"]) == width]
    if not scoped:
        raise ValueError("no D11 decoder records for width %d" % width)
    for record in scoped:
        if record.get("batch_id") != D11_BATCH_ID:
            raise ValueError("record without D11 batch tag cannot enter "
                             "the D11 gate: %r"
                             % ({k: record.get(k) for k in
                                 ("width", "branch", "layer", "graph_seed",
                                  "block_seed", "batch_id")},))
        if record.get("branch") not in BRANCHES:
            raise ValueError("record branch outside D11 branches: %r"
                             % (record.get("branch"),))
        if record.get("layer") not in ("L1", "L2"):
            raise ValueError("record layer outside {L1, L2}: %r"
                             % (record.get("layer"),))
        if int(record["graph_seed"]) not in L1_GRAPH_SEEDS[width]:
            raise ValueError("record graph seed outside frozen D11 set")
        if int(record["block_seed"]) not in L1_BLOCK_SEEDS[width]:
            raise ValueError("record block seed outside frozen D11 set")
    mix_joint, ctrl_joint, mix_l1, ctrl_l1 = [], [], [], []
    oracle_exact = 0
    blocked = 0
    all_updated = True
    for graph_seed in L1_GRAPH_SEEDS[width]:
        mj = cj = ml = cl = 0
        for block_seed in L1_BLOCK_SEEDS[width]:
            cell = [r for r in scoped
                    if int(r["graph_seed"]) == graph_seed
                    and int(r["block_seed"]) == block_seed]
            want = {(CONTROL, "L1"), (CONTROL, "L2"), (MIX, "L1"),
                    (MIX, "L2"), (ORACLE, "L2")}
            if {(r["branch"], r["layer"]) for r in cell} != want \
                    or len(cell) != 5:
                raise ValueError("cell (width=%d, graph=%d, block=%d) does "
                                 "not hold exactly the 5 planned rows"
                                 % (width, graph_seed, block_seed))

            def row(branch: str, layer: str) -> Mapping[str, Any]:
                matches = [r for r in cell if r["branch"] == branch
                           and r["layer"] == layer]
                assert len(matches) == 1
                return matches[0]

            c_l1, c_l2 = row(CONTROL, "L1"), row(CONTROL, "L2")
            m_l1, m_l2 = row(MIX, "L1"), row(MIX, "L2")
            o_l2 = row(ORACLE, "L2")
            for branch_row in (c_l1, c_l2, m_l1, m_l2, o_l2):
                if branch_row["exact"] and not branch_row["syndrome_ok"]:
                    raise ValueError("row claims exact without syndrome_ok")
            cl += 1 if c_l1["exact"] else 0
            ml += 1 if m_l1["exact"] else 0
            cj += 1 if (c_l1["exact"] and c_l2["exact"]) else 0
            mj += 1 if (m_l1["exact"] and m_l2["exact"]) else 0
            oracle_exact += 1 if o_l2["exact"] else 0
            for l2_row in (c_l2, m_l2):
                invoked = l2_row.get("transfer_invoked")
                prov = l2_row.get("transfer_provenance")
                if invoked is not True:
                    blocked += 1
                    all_updated = False
                elif prov != check_updated_token():
                    all_updated = False
        mix_joint.append(mj)
        ctrl_joint.append(cj)
        mix_l1.append(ml)
        ctrl_l1.append(cl)
    return D11WidthTallies(width, mix_joint, ctrl_joint, oracle_exact,
                           mix_l1, ctrl_l1, blocked, all_updated)


def check_l1_replay(width: int, mix_l1_per_graph: Sequence[int],
                    ctrl_l1_per_graph: Sequence[int]) -> str:
    """L1 replay hard gate: ``""`` when the width replays R3 exactly.

    MIX per-graph L1 exact must equal the frozen R3 vector and CONTROL
    must be all zero; any deviation returns the engineering reason (the
    caller engineering-blocks before interpretation). No seed change.
    """
    width = int(width)
    mix = tuple(int(v) for v in mix_l1_per_graph)
    ctrl = tuple(int(v) for v in ctrl_l1_per_graph)
    if width not in D11_WIDTHS:
        raise ValueError("unknown D11 width %r" % (width,))
    if len(mix) != 6 or len(ctrl) != 6:
        raise ValueError("replay gate requires exactly 6 graph pairs")
    if mix != REPLAY_MIX[width]:
        return ("L1 replay mismatch at width %d: MIX L1 exact %s != frozen "
                "R3 %s" % (width, mix, REPLAY_MIX[width]))
    if any(v != 0 for v in ctrl):
        return ("L1 replay mismatch at width %d: CONTROL L1 exact %s != "
                "all zero" % (width, ctrl))
    return ""


def classify_d11(tallies: D11WidthTallies,
                 engineering_reason: str = "") -> str:
    """Frozen per-width gate (packet §2 verbatim) with frozen priority.

    ``D11_FORWARD_SIGNAL`` iff ALL of: ``J_M>=9``; ``J_M-J_C>=6``; MIX
    wins on ≥4/6 pairs; ≥3/6 MIX graphs have ``J_Mg>=1``; ``J_C<=3``;
    ``O>=18``; all 72 MIX and 72 CONTROL transfers CHECK_UPDATED; no
    engineering/resource violation. ``D11_TRANSFER_BOTTLENECK`` iff MIX L1
    exact ≥18, ``J_M<=3``, ``O>=18``. ``D11_L2_CODE_BOTTLENECK`` iff
    ``O<=6``; otherwise ``D11_FORWARD_AMBIGUOUS``. Priority (highest
    first): engineering block, L2-code bottleneck, forward signal,
    transfer bottleneck, ambiguous. Only ``D11WidthTallies`` instances are
    accepted, so non-D11 evidence cannot be classified.
    """
    if not isinstance(tallies, D11WidthTallies):
        raise TypeError("classify_d11 accepts only D11WidthTallies "
                        "(non-D11 evidence cannot enter the D11 gate)")
    if engineering_reason or tallies.transfers_blocked:
        return ENGINEERING_BLOCKED
    joint_m, joint_c = tallies.joint_mix, tallies.joint_ctrl
    oracle = tallies.oracle_exact
    if oracle <= L2_O_MAX:
        return L2_CODE_BOTTLENECK
    pair_wins = sum(1 for mj, cj in zip(tallies.mix_joint,
                                       tallies.ctrl_joint) if mj > cj)
    graphs_ge1 = sum(1 for mj in tallies.mix_joint if mj >= 1)
    if joint_m >= JM_MIN and joint_m - joint_c >= MARGIN_MIN \
            and pair_wins >= PAIR_WINS_MIN \
            and graphs_ge1 >= GRAPHS_GE1_MIN and joint_c <= JC_MAX \
            and oracle >= O_MIN and tallies.all_check_updated:
        return FORWARD_SIGNAL
    if tallies.mix_l1_pool >= TRANSFER_L1M_MIN \
            and joint_m <= TRANSFER_JM_MAX and oracle >= O_MIN:
        return TRANSFER_BOTTLENECK
    return FORWARD_AMBIGUOUS


def route_terminal(n128_classification: str,
                   n256_classification: str | None = None) -> str:
    """Frozen terminal routing (packet §2 verbatim labels)."""
    n128 = str(n128_classification)
    if n128 == ENGINEERING_BLOCKED:
        return T_ENGINEERING_BLOCKED
    if n256_classification is not None \
            and str(n256_classification) == ENGINEERING_BLOCKED:
        return T_ENGINEERING_BLOCKED
    if n128 == FORWARD_SIGNAL:
        if n256_classification is None:
            return T_ENGINEERING_BLOCKED
        n256 = str(n256_classification)
        if n256 == FORWARD_SIGNAL:
            return T_WIDE_RECOVERY
        if n256 == TRANSFER_BOTTLENECK:
            return T_N256_TRANSFER
        if n256 == L2_CODE_BOTTLENECK:
            return T_N256_L2
        if n256 == FORWARD_AMBIGUOUS:
            return T_N256_AMBIGUOUS
        return T_ENGINEERING_BLOCKED
    if n128 == TRANSFER_BOTTLENECK:
        return T_N128_TRANSFER
    if n128 == L2_CODE_BOTTLENECK:
        return T_N128_L2
    if n128 == FORWARD_AMBIGUOUS:
        return T_N128_AMBIGUOUS
    return T_ENGINEERING_BLOCKED


def describe_paired(records: Sequence[Mapping[str, Any]],
                    width: int) -> dict[str, Any]:
    """Descriptive paired discordances + exact one-sided McNemar (no gating).

    For each paired ``(graph, block)`` cell let ``b`` count (MIX joint,
    CONTROL not) and ``c`` count (CONTROL joint, MIX not). The one-sided
    exact p-value is ``P(Bin(b+c, 1/2) >= b)``. Reported descriptively
    only; p-values never override the frozen gate.
    """
    width = int(width)
    scoped = [r for r in records if int(r["width"]) == width]
    discord_b = discord_c = concord = 0
    for graph_seed in L1_GRAPH_SEEDS[width]:
        for block_seed in L1_BLOCK_SEEDS[width]:
            cell = [r for r in scoped
                    if int(r["graph_seed"]) == graph_seed
                    and int(r["block_seed"]) == block_seed]
            l1 = {br: [r for r in cell if r["branch"] == br and r["layer"] == "L1"][0]
                  for br in (CONTROL, MIX)}
            l2 = {br: [r for r in cell if r["branch"] == br and r["layer"] == "L2"][0]
                  for br in (CONTROL, MIX)}
            mix_ok = bool(l1[MIX]["exact"] and l2[MIX]["exact"])
            ctrl_ok = bool(l1[CONTROL]["exact"] and l2[CONTROL]["exact"])
            if mix_ok and not ctrl_ok:
                discord_b += 1
            elif ctrl_ok and not mix_ok:
                discord_c += 1
            else:
                concord += 1
    trials = discord_b + discord_c
    p_value = (sum(math.comb(trials, k) for k in range(discord_b, trials + 1))
               / 2.0 ** trials) if trials else 1.0
    return {"width": width, "discordant_mix_only": discord_b,
            "discordant_ctrl_only": discord_c,
            "concordant": concord, "trials": trials,
            "mcnemar_one_sided_p": p_value,
            "descriptive_only": True}


class _CallCeilingExceeded(RuntimeError):
    """Internal: per-width scientific call ceiling reached (no retry)."""


# --------------------------------------------------------------------------- #
# Width execution: admission sweep first, then the canonical layered pattern
# --------------------------------------------------------------------------- #
def execute_width(width: int, plan: Sequence[Mapping[str, Any]],
                  graphs_l1: Mapping[Any, Mapping[str, Any]],
                  graphs_l2: Mapping[Any, Mapping[str, Any]],
                  priors: Sequence[Any],
                  blocks: Mapping[int, Mapping[str, Any]],
                  decode_fn, *, now=None, rss_fn=None,
                  wall_budget_s: float = WALL_BUDGET_S,
                  per_call_budget_s: float = PER_CALL_BUDGET_S,
                  rss_budget_bytes: int = RSS_BUDGET_BYTES,
                  call_ceiling: int = PER_WIDTH_CALLS) -> dict[str, Any]:
    """Execute one width (72 cells, 360 scientific calls) forward-only.

    Admission sweep first: all 12 L1 graphs plus the 6 shared L2 graphs
    must be admitted, else the width engineering-blocks with zero decoder
    calls and no seed replacement. Each cell then runs CONTROL and MIX
    through the canonical ``d5._run_layered_block`` (fail-closed L1 gate,
    mixer, L2 decode; the MIX call additionally carries the shared
    diagnostic oracle on the same L2 graph), with an explicitly injected
    ``decode_fn(h, prior, syndrome, layer=None)`` — this module never
    imports the production decoder. Decoder crashes are retained, never
    retried. The L1 replay hard gate and provenance fail-close are
    enforced before grading: any deviation engineering-blocks the width.
    """
    width = int(width)
    now = now or time.monotonic
    p1, p2 = priors
    if decode_fn is None or not callable(decode_fn):
        raise ValueError("decode_fn must be explicitly injected")
    t_width = float(now())
    failure: str | None = None
    for arm in (CONTROL_ARM, MIX_ARM):
        for graph_seed in L1_GRAPH_SEEDS[width]:
            graph = graphs_l1.get((arm, width, graph_seed))
            if graph is None or not bool(graph.get("admitted")):
                failure = ("L1 graph (arm=%s, width=%d, seed=%d) not "
                           "admitted; blocked without seed replacement"
                           % (arm, width, graph_seed))
                break
        if failure is not None:
            break
    if failure is None:
        for graph_seed in L2_GRAPH_SEEDS[width]:
            graph = graphs_l2.get((width, graph_seed))
            if graph is None or not bool(graph.get("admitted")):
                failure = ("shared L2 graph (width=%d, seed=%d) not "
                           "admitted; blocked without seed replacement"
                           % (width, graph_seed))
                break
    calls = [0]
    call_walls: list[float] = []

    def counting_decode(h, prior, syndrome, layer=None):
        if calls[0] >= int(call_ceiling):
            raise _CallCeilingExceeded("per-width scientific call ceiling "
                                       "reached")
        start = float(now())
        try:
            return decode_fn(h, prior, syndrome, layer=layer)
        finally:
            calls[0] += 1
            call_walls.append(max(float(now()) - start, 0.0))

    width_plan = [e for e in plan if int(e["width"]) == width]
    cells = sorted({(int(e["graph_seed"]), int(e["block_seed"]))
                    for e in width_plan})
    #: Pairing: the i-th L1 graph pair shares the i-th L2 graph (one
    #: shared DV3 L2 per pair across CONTROL, MIX and ORACLE).
    l2_for_l1 = {int(l1): int(l2) for l1, l2 in
                 zip(L1_GRAPH_SEEDS[width], L2_GRAPH_SEEDS[width])}
    blocked_transfers = 0
    records: list[dict[str, Any]] = []
    if failure is None:
        for graph_seed, block_seed in cells:
            h1c = graphs_l1[(CONTROL_ARM, width, graph_seed)]["dense"]
            h1m = graphs_l1[(MIX_ARM, width, graph_seed)]["dense"]
            # One shared L2 graph object for CONTROL, MIX and ORACLE.
            h2 = graphs_l2[(width, l2_for_l1[int(graph_seed)])]["dense"]
            block = blocks[int(block_seed)]
            base = len(call_walls)
            try:
                out_c = d5._run_layered_block(
                    counting_decode, h1c, h2, p1, p2, block, False,
                    on_blocked_transfer="record")
                out_m = d5._run_layered_block(
                    counting_decode, h1m, h2, p1, p2, block, True,
                    on_blocked_transfer="record")
            except _CallCeilingExceeded as exc:
                failure = str(exc)
                break
            except Exception as exc:  # retained crash record; never retried
                records.append({
                    "call_idx": len(records), "width": width,
                    "branch": MIX, "layer": "L1", "graph_seed": graph_seed,
                    "block_seed": block_seed, "batch_id": D11_BATCH_ID,
                    "exact": False, "syndrome_ok": False, "iterations": -1,
                    "belief_provenance": "", "transfer_invoked": "",
                    "transfer_provenance": "", "crash": True,
                    "error": repr(exc)[:300], "wall_s": 0.0})
                failure = "decoder crash: %s" % repr(exc)[:200]
                break
            walls = call_walls[base:]

            def pop_wall() -> float:
                return float(walls.pop(0)) if walls else 0.0

            for branch, out in ((CONTROL, out_c), (MIX, out_m)):
                if not out["transfer_invoked"]:
                    blocked_transfers += 1
                records.append({
                    "call_idx": len(records), "width": width,
                    "branch": branch, "layer": "L1",
                    "graph_seed": graph_seed, "block_seed": block_seed,
                    "batch_id": D11_BATCH_ID,
                    "exact": bool(out["app_l1_exact"]),
                    "syndrome_ok": bool(out["app_l1_syndrome_ok"]),
                    "iterations": int(out["app_l1_iterations"]),
                    "belief_provenance": out["app_l1_provenance"] or "",
                    "transfer_invoked": "", "transfer_provenance": "",
                    "crash": False, "error": "", "wall_s": pop_wall()})
                if out["transfer_invoked"]:
                    records.append({
                        "call_idx": len(records), "width": width,
                        "branch": branch, "layer": "L2",
                        "graph_seed": graph_seed, "block_seed": block_seed,
                        "batch_id": D11_BATCH_ID,
                        "exact": bool(out["app_l2_exact"]),
                        "syndrome_ok": bool(out["app_l2_syndrome_ok"]),
                        "iterations": int(out["app_l2_iterations"]),
                        "belief_provenance": "",
                        "transfer_invoked": True,
                        "transfer_provenance": out["app_l1_provenance"] or "",
                        "crash": False, "error": "",
                        "wall_s": pop_wall()})
                else:
                    records.append({
                        "call_idx": len(records), "width": width,
                        "branch": branch, "layer": "L2",
                        "graph_seed": graph_seed, "block_seed": block_seed,
                        "batch_id": D11_BATCH_ID,
                        "exact": False, "syndrome_ok": False, "iterations": 0,
                        "belief_provenance": "",
                        "transfer_invoked": False,
                        "transfer_provenance":
                            "BLOCKED:%s" % out["transfer_blocked_reason"],
                        "crash": False, "error": "",
                        "wall_s": 0.0})
                if "oracle_exact" in out:
                    records.append({
                        "call_idx": len(records), "width": width,
                        "branch": ORACLE, "layer": "L2",
                        "graph_seed": graph_seed, "block_seed": block_seed,
                        "batch_id": D11_BATCH_ID,
                        "exact": bool(out["oracle_exact"]),
                        "syndrome_ok": bool(out["oracle_syndrome_ok"]),
                        "iterations": int(out["oracle_iterations"]),
                        "belief_provenance": "",
                        "transfer_invoked": "", "transfer_provenance":
                            "ORACLE",
                        "crash": False, "error": "",
                        "wall_s": pop_wall()})
            if walls:
                failure = "internal call-accounting drift"
                break
            if float(now()) - t_width > float(wall_budget_s):
                failure = "wall budget exceeded"
                break
            if rss_fn is not None \
                    and int(rss_fn()) >= int(rss_budget_bytes):
                failure = "RSS budget exceeded"
                break
            if any(float(r["wall_s"]) > float(per_call_budget_s)
                   for r in records[-5:]):
                failure = "per-call wall budget exceeded"
                break
    if failure is None:
        if blocked_transfers:
            failure = ("transfer provenance fail-closed: %d non-oracle "
                       "transfer(s) not CHECK_UPDATED" % blocked_transfers)
            tallies = D11WidthTallies(width, (0,) * 6, (0,) * 6, 0,
                                     (0,) * 6, (0,) * 6)
        else:
            try:
                tallies = tallies_from_d11_records(records, width)
            except ValueError as exc:
                failure = "tally construction failed: %s" % exc
                tallies = D11WidthTallies(width, (0,) * 6, (0,) * 6, 0,
                                         (0,) * 6, (0,) * 6)
            else:
                replay_reason = check_l1_replay(width, tallies.mix_l1,
                                                tallies.ctrl_l1)
                if replay_reason:
                    failure = replay_reason
    else:
        tallies = D11WidthTallies(width, (0,) * 6, (0,) * 6, 0,
                                 (0,) * 6, (0,) * 6)
    classification = classify_d11(tallies, failure or "")
    return {
        "width": width,
        "records": records,
        "decoder_calls": int(calls[0]),
        "mix_joint": list(tallies.mix_joint),
        "ctrl_joint": list(tallies.ctrl_joint),
        "mix_l1": list(tallies.mix_l1),
        "ctrl_l1": list(tallies.ctrl_l1),
        "oracle_exact": tallies.oracle_exact,
        "transfers_blocked": tallies.transfers_blocked,
        "all_check_updated": tallies.all_check_updated,
        "paired": describe_paired(records, width)
        if failure is None and records else None,
        "classification": classification,
        "engineering_reason": failure or "",
    }


# --------------------------------------------------------------------------- #
# Pre-decoder profile: all 36 future graphs, no decoder, no root
# --------------------------------------------------------------------------- #
def profile_graphs(build_l1_fn=None, build_l2_fn=None, now=None
                   ) -> dict[str, Any]:
    """Bounded profile: build all 36 frozen D11 graphs, no decoder, no root.

    Reports per graph the A1–A6 admission outcome, ranks, four-cycles and
    wall time; verifies deterministic replay construction (rebuild
    equality is owned by the builders' A6 check, reported here), the
    360-per-width / conditional-720 plan identities, zero decoder calls
    and the absent future root. A frozen seed that cannot produce an
    admitted graph is retained as-is; no replacement seed exists or is
    consumed (zero replacement seeds by construction).
    """
    from pathlib import Path
    build_l1_fn = build_l1_fn or build_l1_graph
    build_l2_fn = build_l2_fn or build_l2_graph
    now = now or time.perf_counter
    t0 = float(now())
    entries: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    def describe(graph: Mapping[str, Any], graph_seed: int,
                 start: float) -> None:
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
                "four_cycles": int(structure["four_cycles"]),
                "girth": structure["girth"],
                "girth_reason": str(structure["girth_reason"]),
            })
        entries.append(entry)
        if graph["status"] == "construction_failed" \
                or not graph["admitted"]:
            failures.append({
                "width": int(graph["width"]), "arm": str(graph["arm"]),
                "seed": int(graph_seed),
                "status": str(graph["status"]),
                "admitted": bool(graph["admitted"]),
                "failure_reason": str(graph["failure_reason"])})

    for width in D11_WIDTHS:
        for arm in (CONTROL_ARM, MIX_ARM):
            for graph_seed in L1_GRAPH_SEEDS[width]:
                start = float(now())
                describe(build_l1_fn(arm, width, graph_seed), graph_seed,
                         start)
        for graph_seed in L2_GRAPH_SEEDS[width]:
            start = float(now())
            describe(build_l2_fn(width, graph_seed), graph_seed, start)
    plan_n128 = build_call_plan(128)
    plan_full = build_full_plan()
    repo_root = Path(__file__).resolve().parents[4]
    return {
        "l1_graphs": 24, "l2_graphs": 12,
        "graphs": entries,
        "seed_replacements": [],
        "replacement_seeds_used": 0,
        "frozen_seed_failures": failures,
        "plan_n128_calls": len(plan_n128),
        "plan_full_calls": len(plan_full),
        "decoder_calls": 0,
        "future_root": FUTURE_ROOT,
        "future_root_absent": not (repo_root / FUTURE_ROOT).exists(),
        "wall_s": float(now()) - t0,
    }
