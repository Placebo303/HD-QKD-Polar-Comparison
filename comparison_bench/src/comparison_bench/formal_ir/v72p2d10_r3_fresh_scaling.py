"""V72P2D10 R3 fresh-graph scaling replication — readiness plan/runner/verifier.

Change: ``v72p2d10-r3-fresh-graph-scaling``
Cycle: ``V72P2D10-MIXED-DEGREE-L1`` (successor replication of accepted R2/A1)
Frozen authority: ``.workbuddy/tasks/D10_R3_FRESH_GRAPH_SCALING_READINESS_TASK_PACKET.md``
(§2–§4) and ``openspec/changes/v72p2d10-r3-fresh-graph-scaling/`` (design §1–§6,
delta spec). Track: implementation/readiness (zero scientific decoder calls).

R302 reuse contract (IMPORT/REUSE — no duplication of constructor logic):

- construction/admission: ``r2.build_graph`` (which owns the shared
  connectivity-first ``build_degree_sequence_peg``, the A1–A6 admission and
  the A6 replay check);
- decoder path: ``r2.dispatch_l1`` (which owns the admission gate before
  decoder binding plus exact/syndrome/stop semantics);
- coefficient rule: ``r2.coefficient_seed`` (``v10_seed`` of
  ``d10:coeff:{width}:{graph_seed}``);
- decoder contract constants (``max_iter=90``, ``damping_alpha=1.0``),
  field (``q=32, poly=37``), arms/roles and ``refuse_out_root``.

Added here (R3 successor deltas only): the frozen R3 degree cells (n128/n256,
cross-checked equal to the R2 cells at import), fresh graph/block seeds, the
144-calls-per-width plan with conditional n256 dispatch, the verbatim 6-clause
``R3_REPRODUCED`` gate plus ``R3_NEGATIVE``/``R3_AMBIGUOUS``, the six
terminals, descriptive paired McNemar, the never-pool A1 record boundary
(``R3WidthTallies`` built only from ``R3_BATCH_ID``-tagged R3 decoder
records), budgets (≤288 scientific, ≤50 setup, wall ≤1800 s, ≤120 s/call,
RSS <2 GiB, one process, no retry/resume/repair/seed search/adaptation) and
the 24-cell pre-decoder profile. There is no replacement-seed mechanism
anywhere in this module: admission failure blocks with no seed change.
"""
from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from typing import Any

from . import v72p2d10_mixed_degree_l1 as r2

__all__ = [
    "ARMS", "ARM_ROLE", "R3_WIDTHS", "GRAPH_SEEDS", "BLOCK_SEEDS",
    "DEGREE_TABLE", "DECODER_MAX_ITER", "DAMPING_ALPHA",
    "PER_WIDTH_CALLS", "SCIENTIFIC_CALL_CEILING", "SETUP_CALL_CEILING",
    "SETUP_FIXED_UNITS", "WALL_BUDGET_S", "PER_CALL_BUDGET_S",
    "RSS_BUDGET_BYTES", "EVIDENCE_FILES", "FROZEN_COMMAND", "FUTURE_ROOT",
    "FUTURE_ROOT_UUID", "AUTHORIZATION", "CLAIM_CEILING", "R3_BATCH_ID",
    "REPRODUCED", "NEGATIVE", "AMBIGUOUS", "ENGINEERING_BLOCKED",
    "NOT_RUN", "T_N128_NOT_REPRODUCED", "T_N128_AMBIGUOUS",
    "T_FINITE_WIDTH_DECAY", "T_N256_AMBIGUOUS",
    "T_WIDE_L1_SIGNAL_REPRODUCED", "T_ENGINEERING_BLOCKED", "TERMINALS",
    "R3_M_MIN", "R3_MARGIN_MIN", "R3_PAIR_WINS_MIN", "R3_GRAPHS_GE2_MIN",
    "R3_C_MAX", "R3_NEG_M_MAX", "R3_NEG_MARGIN_MAX",
    "R3WidthTallies", "degree_cell", "build_graph", "build_call_plan",
    "build_full_plan", "tallies_from_r3_records", "classify_r3",
    "n256_permitted", "route_terminal", "describe_paired", "execute_width",
    "profile_graphs", "refuse_out_root",
]

# --------------------------------------------------------------------------- #
# Frozen identifiers (packet §2; design §1/§4/§5)
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2d10-r3-fresh-graph-scaling"
CYCLE_ID = "V72P2D10-MIXED-DEGREE-L1"
CLAIM_CEILING = (
    "synthetic finite-length L1-only diagnostic under the accepted CAL-only "
    "Model-F prior and the frozen decoder contract; no L2/APP, FER, "
    "leakage, SKR, qualification, promotion, publication or real-data claim, "
    "and no DE-to-decoder equivalence claim; D7-H is not revived by any R3 "
    "outcome"
)

#: Same two arms as R2 (shared reference, not a re-declaration).
ARMS = r2.ARMS
ARM_ROLE = r2.ARM_ROLE
R3_WIDTHS = (128, 256)

#: Fresh graph seeds (frozen; never searched or replaced).
GRAPH_SEEDS = {
    128: tuple(range(2026092401, 2026092407)),
    256: tuple(range(2026092501, 2026092507)),
}
#: Fresh block seeds (frozen; separate from graph seeds).
BLOCK_SEEDS = {
    128: tuple(range(2026092601, 2026092613)),
    256: tuple(range(2026092701, 2026092713)),
}

#: Frozen n128/n256 realizations (design §3 verbatim).
DEGREE_TABLE = {
    ("PEG_DV3_MATCHED", 128): {
        "n": 128, "m": 118, "var_counts": {3: 128},
        "check_counts": {3: 88, 4: 30}},
    ("PEG_DV3_MATCHED", 256): {
        "n": 256, "m": 236, "var_counts": {3: 256},
        "check_counts": {3: 176, 4: 60}},
    ("PEG_DV23_LAM2_045", 128): {
        "n": 128, "m": 118, "var_counts": {3: 57, 2: 71},
        "check_counts": {3: 77, 2: 41}},
    ("PEG_DV23_LAM2_045", 256): {
        "n": 256, "m": 236, "var_counts": {3: 115, 2: 141},
        "check_counts": {3: 155, 2: 81}},
}

#: Import-time drift guard: the R3 cells must equal the accepted R2 cells.
for _key, _cell in DEGREE_TABLE.items():
    _frozen = dict(_cell)
    _r2 = r2.degree_cell(*_key)
    if _r2["n"] != _frozen["n"] or _r2["m"] != _frozen["m"] \
            or _r2["var_counts"] != _frozen["var_counts"] \
            or _r2["check_counts"] != _frozen["check_counts"]:
        raise ValueError("R3 degree cell %r drifted from accepted R2" % (_key,))
del _key, _cell, _frozen, _r2

#: Decoder/field contract reused from R2 (no re-declaration).
DECODER_MAX_ITER = r2.DECODER_MAX_ITER
DAMPING_ALPHA = r2.DAMPING_ALPHA
MODEL_F_INPUT_ROOT = r2.MODEL_F_INPUT_ROOT

#: Budgets (packet §2: ≤288 scientific; ≤50 setup = 24 builds + 24 block
#: samples + Model-F load + plan build; wall ≤1800 s; ≤120 s/call).
PER_WIDTH_CALLS = 144
SCIENTIFIC_CALL_CEILING = 288
SETUP_CALL_CEILING = 50
SETUP_FIXED_UNITS = 2  # Model-F load + plan build
WALL_BUDGET_S = 1800.0
PER_CALL_BUDGET_S = 120.0
RSS_BUDGET_BYTES = r2.RSS_BUDGET_BYTES

#: Gate thresholds (packet §2 verbatim).
R3_M_MIN = 18
R3_MARGIN_MIN = 12
R3_PAIR_WINS_MIN = 5
R3_GRAPHS_GE2_MIN = 4
R3_C_MAX = 6
R3_NEG_M_MAX = 6
R3_NEG_MARGIN_MAX = 3

#: Per-width labels and terminals (packet §2 verbatim).
REPRODUCED = "R3_REPRODUCED"
NEGATIVE = "R3_NEGATIVE"
AMBIGUOUS = "R3_AMBIGUOUS"
ENGINEERING_BLOCKED = "ENGINEERING_BLOCKED"
NOT_RUN = "NOT_RUN"

T_N128_NOT_REPRODUCED = "D10_R3_N128_NOT_REPRODUCED"
T_N128_AMBIGUOUS = "D10_R3_N128_AMBIGUOUS"
T_FINITE_WIDTH_DECAY = "D10_R3_FINITE_WIDTH_DECAY"
T_N256_AMBIGUOUS = "D10_R3_N256_AMBIGUOUS"
T_WIDE_L1_SIGNAL_REPRODUCED = "D10_R3_WIDE_L1_SIGNAL_REPRODUCED"
T_ENGINEERING_BLOCKED = "D10_R3_ENGINEERING_BLOCKED"
TERMINALS = (T_N128_NOT_REPRODUCED, T_N128_AMBIGUOUS, T_FINITE_WIDTH_DECAY,
             T_N256_AMBIGUOUS, T_WIDE_L1_SIGNAL_REPRODUCED,
             T_ENGINEERING_BLOCKED)

FUTURE_ROOT_UUID = "4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d"
FUTURE_ROOT = "workspace/d10_r3_fresh_graph_scaling_" + FUTURE_ROOT_UUID
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d10_r3_development.py "
    "--r3-batch --model-f-root %s --out-root %s"
    % (MODEL_F_INPUT_ROOT, FUTURE_ROOT)
)
AUTHORIZATION = (
    "separate explicit user/main-thread authorization required before "
    "--r3-batch")
#: R303: batch authorization is the runner CLI argument --execution-authorized
#: (default false). No source constant authorizes execution.

EVIDENCE_FILES = ("manifest.json", "decoder_records.csv",
                  "graph_records.csv", "arm_summary.csv", "summary.json",
                  "command_log.txt")

#: Scope tag carried by every R3 decoder record. The gate constructor only
#: accepts records carrying this tag, so A1 evidence (a different root,
#: schema and batch) is structurally impossible to pool into R3 arithmetic.
R3_BATCH_ID = "d10-r3-fresh-v1"

#: Never-overwrite root refusal reused from R2 (same depth, same repo root).
refuse_out_root = r2.refuse_out_root


# --------------------------------------------------------------------------- #
# Degree cells and graph construction (R2 path reused, never duplicated)
# --------------------------------------------------------------------------- #
def degree_cell(arm: str, width: int) -> dict[str, Any]:
    """Return the frozen R3 ``(n, m, var_counts, check_counts)`` cell."""
    key = (str(arm), int(width))
    if key not in DEGREE_TABLE:
        raise KeyError("unknown R3 (arm, width) cell %r" % (key,))
    cell = DEGREE_TABLE[key]
    var_sockets = sum(int(d) * int(c) for d, c in cell["var_counts"].items())
    check_sockets = sum(int(d) * int(c)
                        for d, c in cell["check_counts"].items())
    if var_sockets != check_sockets:
        raise ValueError("frozen cell %r socket mismatch" % (key,))
    return {"n": int(cell["n"]), "m": int(cell["m"]),
            "var_counts": dict(cell["var_counts"]),
            "check_counts": dict(cell["check_counts"]), "E": var_sockets}


def build_graph(arm: str, width: int, graph_seed: int) -> dict[str, Any]:
    """Build one frozen R3 graph via the accepted R2 construction/admission.

    Scope-guards the R3 ``(arm, width)`` cell, then delegates to
    ``r2.build_graph`` (shared connectivity-first PEG + A1–A6 + A6 replay).
    Any failure is retained with ``admitted=False``; seeds are never
    altered, repaired or searched.
    """
    degree_cell(arm, width)  # scope guard; raises outside R3 cells
    if int(graph_seed) not in GRAPH_SEEDS[int(width)]:
        raise ValueError("graph seed %r outside frozen R3 set for width %d"
                         % (graph_seed, int(width)))
    return r2.build_graph(str(arm), int(width), int(graph_seed))


# --------------------------------------------------------------------------- #
# Plan: exact call identities, conditional dispatch (R305)
# --------------------------------------------------------------------------- #
def build_call_plan(width: int) -> list[dict[str, Any]]:
    """Frozen paired call matrix for one width: 2 arms x 6 graphs x 12 blocks.

    Order: control arm first, graph seeds ascending, block seeds ascending;
    ``call_idx`` is contiguous over the width (0..143).
    """
    width = int(width)
    if width not in R3_WIDTHS:
        raise KeyError("unknown R3 width %r" % (width,))
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
    """Both widths concatenated (n128 first); at most 288 scientific calls."""
    plan = build_call_plan(128)
    base = len(plan)
    for entry in build_call_plan(256):
        plan.append(dict(entry, call_idx=base + entry["call_idx"]))
    return plan


def n256_permitted(n128_classification: str) -> bool:
    """n256 is dispatched if and only if n128 is ``R3_REPRODUCED``."""
    return str(n128_classification) == REPRODUCED


# --------------------------------------------------------------------------- #
# Gate arithmetic with a structural A1 boundary (R305)
# --------------------------------------------------------------------------- #
class R3WidthTallies:
    """Exact-count tallies for one R3 width (six graph pairs, 12 blocks each).

    Only exact counts enter the gate; syndrome-valid counts are carried for
    separate reporting and never substitute for exact. Instances can only be
    built from ``R3_BATCH_ID``-tagged R3 decoder records (see
    ``tallies_from_r3_records``), so A1 evidence cannot reach the gate.
    """

    def __init__(self, width: int, mix_exact: Sequence[int],
                 dv3_exact: Sequence[int]) -> None:
        width = int(width)
        mix_exact = tuple(int(v) for v in mix_exact)
        dv3_exact = tuple(int(v) for v in dv3_exact)
        if width not in R3_WIDTHS:
            raise ValueError("unknown R3 width %r" % (width,))
        if len(mix_exact) != 6 or len(dv3_exact) != 6:
            raise ValueError("R3 tallies require exactly 6 graph pairs")
        if any(v < 0 or v > 12 for v in mix_exact + dv3_exact):
            raise ValueError("per-graph exact counts must lie in 0..12")
        self.width = width
        self.mix_exact = mix_exact
        self.dv3_exact = dv3_exact

    @property
    def mix_pool(self) -> int:
        """Fresh-width MIX exact pool ``M`` (72 paired blocks)."""
        return sum(self.mix_exact)

    @property
    def dv3_pool(self) -> int:
        """Fresh-width DV3 exact pool ``C`` (72 paired blocks)."""
        return sum(self.dv3_exact)


def tallies_from_r3_records(records: Sequence[Mapping[str, Any]],
                            width: int) -> R3WidthTallies:
    """Build gate tallies exclusively from R3 decoder records of one width.

    Every contributing record must carry ``batch_id == R3_BATCH_ID`` and a
    frozen ``(arm, width, graph_seed, block_seed)`` identity; exactly 12
    paired blocks per graph pair are required. A1 records (different root,
    schema, widths, seeds and no R3 batch tag) fail this constructor, so
    A1 evidence is structurally impossible to pool into R3 gates.
    """
    width = int(width)
    scoped = [r for r in records if int(r["width"]) == width]
    if not scoped:
        raise ValueError("no R3 decoder records for width %d" % width)
    for record in scoped:
        if record.get("batch_id") != R3_BATCH_ID:
            raise ValueError("record without R3 batch tag cannot enter "
                             "the R3 gate: %r"
                             % ({k: record.get(k) for k in
                                 ("width", "arm", "graph_seed",
                                  "block_seed", "batch_id")},))
        if record.get("arm") not in ARMS:
            raise ValueError("record arm outside R3 arms: %r"
                             % (record.get("arm"),))
        if int(record["graph_seed"]) not in GRAPH_SEEDS[width]:
            raise ValueError("record graph seed outside frozen R3 set")
        if int(record["block_seed"]) not in BLOCK_SEEDS[width]:
            raise ValueError("record block seed outside frozen R3 set")
    mix_exact, dv3_exact = [], []
    for graph_seed in GRAPH_SEEDS[width]:
        for arm, bucket in (("PEG_DV23_LAM2_045", mix_exact),
                            ("PEG_DV3_MATCHED", dv3_exact)):
            rows = [r for r in scoped
                    if r["arm"] == arm and int(r["graph_seed"]) == graph_seed]
            if len(rows) != 12:
                raise ValueError(
                    "graph pair (arm=%s, width=%d, seed=%d) contributes "
                    "%d blocks, want exactly 12" % (arm, width, graph_seed,
                                                    len(rows)))
            if sorted(int(r["block_seed"]) for r in rows) \
                    != sorted(BLOCK_SEEDS[width]):
                raise ValueError("unpaired block identities at graph pair "
                                 "(arm=%s, width=%d, seed=%d)" % (arm, width,
                                                                  graph_seed))
            bucket.append(sum(1 for r in rows if r["exact"]))
    return R3WidthTallies(width, mix_exact, dv3_exact)


def classify_r3(tallies: R3WidthTallies, engineering_reason: str = "") -> str:
    """Frozen per-width gate (packet §2 verbatim).

    ``R3_REPRODUCED`` iff ALL of: (1) ``M >= 18``; (2) ``M - C >= 12``;
    (3) MIX wins on ≥5 of 6 graph pairs; (4) ≥4 of 6 MIX graphs have
    ``M_g >= 2``; (5) ``C <= 6``; (6) no engineering/resource violation.
    ``R3_NEGATIVE`` iff ``M <= 6`` OR ``M - C <= 3`` (no engineering block);
    otherwise ``R3_AMBIGUOUS``. Only ``R3WidthTallies`` instances are
    accepted, so non-R3 evidence cannot be classified.
    """
    if not isinstance(tallies, R3WidthTallies):
        raise TypeError("classify_r3 accepts only R3WidthTallies "
                        "(A1 evidence cannot enter the R3 gate)")
    if engineering_reason:
        return ENGINEERING_BLOCKED
    mix_pool, dv3_pool = tallies.mix_pool, tallies.dv3_pool
    margin = mix_pool - dv3_pool
    pair_wins = sum(1 for mix_g, dv3_g in zip(tallies.mix_exact,
                                             tallies.dv3_exact)
                    if mix_g > dv3_g)
    graphs_ge2 = sum(1 for mix_g in tallies.mix_exact if mix_g >= 2)
    if mix_pool >= R3_M_MIN and margin >= R3_MARGIN_MIN \
            and pair_wins >= R3_PAIR_WINS_MIN \
            and graphs_ge2 >= R3_GRAPHS_GE2_MIN and dv3_pool <= R3_C_MAX:
        return REPRODUCED
    if mix_pool <= R3_NEG_M_MAX or margin <= R3_NEG_MARGIN_MAX:
        return NEGATIVE
    return AMBIGUOUS


def route_terminal(n128_classification: str,
                   n256_classification: str | None = None) -> str:
    """Frozen terminal routing (packet §2 verbatim)."""
    n128 = str(n128_classification)
    if n128 == ENGINEERING_BLOCKED:
        return T_ENGINEERING_BLOCKED
    if n256_classification is not None \
            and str(n256_classification) == ENGINEERING_BLOCKED:
        return T_ENGINEERING_BLOCKED
    if n128 == NEGATIVE:
        return T_N128_NOT_REPRODUCED
    if n128 == AMBIGUOUS:
        return T_N128_AMBIGUOUS
    if n128 != REPRODUCED:
        return T_ENGINEERING_BLOCKED
    if n256_classification is None:
        return T_ENGINEERING_BLOCKED
    n256 = str(n256_classification)
    if n256 == NEGATIVE:
        return T_FINITE_WIDTH_DECAY
    if n256 == AMBIGUOUS:
        return T_N256_AMBIGUOUS
    if n256 == REPRODUCED:
        return T_WIDE_L1_SIGNAL_REPRODUCED
    return T_ENGINEERING_BLOCKED


def describe_paired(records: Sequence[Mapping[str, Any]],
                    width: int) -> dict[str, Any]:
    """Descriptive paired discordances + exact one-sided McNemar (no gating).

    For each paired ``(graph, block)`` call let ``b`` count
    (MIX exact, DV3 not) and ``c`` count (MIX not, DV3 exact). The one-sided
    exact p-value is ``P(Bin(b+c, 1/2) >= b)``. Reported descriptively only;
    p-values never override the frozen gate.
    """
    width = int(width)
    scoped = [r for r in records if int(r["width"]) == width]
    discord_b = discord_c = concord = 0
    for graph_seed in GRAPH_SEEDS[width]:
        for block_seed in BLOCK_SEEDS[width]:
            mix = [r for r in scoped if r["arm"] == "PEG_DV23_LAM2_045"
                   and int(r["graph_seed"]) == graph_seed
                   and int(r["block_seed"]) == block_seed]
            dv3 = [r for r in scoped if r["arm"] == "PEG_DV3_MATCHED"
                   and int(r["graph_seed"]) == graph_seed
                   and int(r["block_seed"]) == block_seed]
            if len(mix) != 1 or len(dv3) != 1:
                raise ValueError("unpaired R3 calls at width=%d seed=%d "
                                 "block=%d" % (width, graph_seed, block_seed))
            mix_ok, dv3_ok = bool(mix[0]["exact"]), bool(dv3[0]["exact"])
            if mix_ok and not dv3_ok:
                discord_b += 1
            elif dv3_ok and not mix_ok:
                discord_c += 1
            else:
                concord += 1
    trials = discord_b + discord_c
    p_value = (sum(math.comb(trials, k) for k in range(discord_b, trials + 1))
               / 2.0 ** trials) if trials else 1.0
    return {"width": width, "discordant_mix_only": discord_b,
            "discordant_dv3_only": discord_c,
            "concordant": concord, "trials": trials,
            "mcnemar_one_sided_p": p_value,
            "descriptive_only": True}


# --------------------------------------------------------------------------- #
# Width execution: admission sweep first, then the R2 decoder path (R304)
# --------------------------------------------------------------------------- #
def execute_width(width: int, plan: Sequence[Mapping[str, Any]],
                  graphs: Mapping[Any, Mapping[str, Any]],
                  blocks: Mapping[int, Mapping[str, Any]],
                  decode_fn, syndrome_fn, *, now=None, rss_fn=None,
                  wall_budget_s: float = WALL_BUDGET_S,
                  per_call_budget_s: float = PER_CALL_BUDGET_S,
                  rss_budget_bytes: int = RSS_BUDGET_BYTES,
                  call_ceiling: int = PER_WIDTH_CALLS) -> dict[str, Any]:
    """Execute one width (144 paired calls) through ``r2.dispatch_l1``.

    R304: all 12 graphs of the width are admission-checked before any
    decoder binding; any failure engineering-blocks the width with zero
    decoder calls and no seed replacement. ``decode_fn``/``syndrome_fn``
    must be explicitly injected; this module never imports the production
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
            record["batch_id"] = R3_BATCH_ID
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
    tallies = tallies_from_r3_records(records, width) if records \
        else R3WidthTallies(width, (0,) * 6, (0,) * 6)
    classification = classify_r3(tallies, failure or "")
    return {
        "width": width,
        "records": records,
        "mix_exact": list(tallies.mix_exact),
        "dv3_exact": list(tallies.dv3_exact),
        "mix_pool": tallies.mix_pool,
        "dv3_pool": tallies.dv3_pool,
        "paired": describe_paired(records, width) if records else None,
        "classification": classification,
        "engineering_reason": failure or "",
    }


# --------------------------------------------------------------------------- #
# R309 pre-decoder profile: all 24 future graphs, no decoder, no root
# --------------------------------------------------------------------------- #
def profile_graphs(build_fn=None, now=None) -> dict[str, Any]:
    """Bounded profile: build all 24 frozen R3 graphs, no decoder, no root.

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
    for width in R3_WIDTHS:
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
