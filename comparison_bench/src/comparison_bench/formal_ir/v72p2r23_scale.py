"""V72P2R23 synthetic scale probe (S-regime) — readiness plan/graphs/gates.

Track: EXPLORE-readiness (NOT execution; zero decoder calls in R23b).
Frozen authority: R23 packet (planner return this session): S-regime
``p=0.61`` q-ary-symmetric U2 oracle; S-grid ``m/n`` {0.65, 0.72, 0.78} ->
n128 ``m`` {83, 92, 100} + n1024 ``m`` {666, 737, 799}; S-N 16
blocks/arm/ratio = 2 graphs x 8 blocks (96 scientific calls max);
S-gate-SYNTH (FROZEN R23c-R1 packet text EXACTLY): SCALING-WIN iff
n1024@0.65 exact-frac >=6/16 AND (n1024@0.65 - n128@0.65) >=+4/16 AND
undetected==0; SCALING-DEAD iff n1024@0.65 <=2/16 OR gap<+4/16; else
INCONCLUSIVE; undetected>0 -> STOP absolute. Per-cell exact counts stay
as diagnostics only; the batch terminal comes ONLY from this rule.
S-decoder cold 90/1.0
oracle-only; S-bud per-call 300 s + total 3600 s + per-build sub-caps
n128<=60 s / n1024<=300 s; scratch root
``workspace/r23_scale_a3f1c9d2-4b7e-4f2a-9e1d-8c5f6a7b9d0e``.

Single arm ``S`` (DV3-regular; assumption C2 flagged for planner
confirmation). The D9 rule is reused BY IMPORT
(``d9.graph_realization_cell``); the D10-R2 connectivity-first PEG
constructor, admission composition, dispatch kernel, coefficient
conventions and root refusal are reused BY IMPORT (``r2.*``); the cold
90/1.0 contract is reused BY IMPORT (``r2.DECODER_MAX_ITER`` /
``r2.DAMPING_ALPHA``); the decoder kernels are NEVER imported here
(runner-binds-only). D19 n128-m94 graphs are retained as a
byte-identical import REFERENCE only (``d19_reference_build``) and can
never enter the S gate (batch_id mismatch raises).

Synthetic oracle path (NO tag/prior, Model-F NOT carried): disclosure =
syndrome bits ``5m`` only per block. Oracle prior rows are the exact
q-ary-symmetric truth-conditioned rows (``1-p`` on truth, ``p/31``
elsewhere); per-block error weight is a direct ``rng.binomial(n, p)``
draw, descriptive only (no Hutch estimator). No warm start, no damping
variant, no DV3 arm, no retry, no resume, no seed search.
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
from . import v72p2d19_l2_finite as d19
from . import v72p2d9_de_decoder_calibration as d9

__all__ = [
    "CHANGE_ID", "CYCLE_ID", "TRACK", "CLAIM_CEILING",
    "ARMS", "ARM", "RATIOS", "RATIO_KEY", "WIDTHS", "ROWS",
    "LAMBDA_S", "P_ERR", "Q", "BITS_PER_ROW",
    "GRAPH_SEEDS", "BLOCK_SEEDS", "R23_BATCH_ID",
    "DECODER_MAX_ITER", "DAMPING_ALPHA",
    "SCIENTIFIC_CALL_CEILING", "SETUP_CALL_CEILING",
    "WALL_BUDGET_S", "PER_CALL_BUDGET_S", "PER_BUILD_SUBCAP_S",
    "ANCHOR_HI", "ANCHOR_LO", "WIN_MIN_HI", "WIN_MIN_GAP", "DEAD_MAX_HI",
    "WIN", "DEAD", "INCONCLUSIVE", "STOP",
    "EVIDENCE_FILES", "FUTURE_ROOT", "FUTURE_ROOT_UUID",
    "FROZEN_COMMAND", "FROZEN_STAGE1_ARGV", "AUTHORIZATION",
    "StructureNotAdmitted",
    "build_degree_sequence_peg", "structural_record", "dense_from_edges",
    "dispatch_l1", "graph_realization_cell",
    "disclosed_bits", "degree_cell",
    "coefficient_seed", "coefficients_for_edges",
    "build_graph", "build_call_plan", "sample_oracle_block",
    "run_s_oracle_call", "execute_plan",
    "cell_tally", "route_scaling_gate",
    "check_build_budgets", "refuse_out_root",
    "d19_reference_build",
]

# --------------------------------------------------------------------------- #
# Frozen identifiers
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2r23-synthetic-scale"
CYCLE_ID = "V72P2R23-SCALE"
TRACK = "EXPLORE-readiness"
CLAIM_CEILING = (
    "synthetic scale diagnostic under the frozen q-ary-symmetric U2 oracle "
    "and the frozen cold 90/1.0 decoder contract; no FER/leakage/SKR/"
    "qualification/promotion/publication/route-closure claim; "
    "R23b grants no execution and makes zero decoder calls"
)

ARM = "S"
ARMS = ("S",)
RATIOS = (0.65, 0.72, 0.78)
RATIO_KEY = {0.65: "r65", 0.72: "r72", 0.78: "r78"}
WIDTHS = (128, 1024)
#: m = round(n * ratio): 128 -> {83, 92, 100}; 1024 -> {666, 737, 799}.
ROWS = {
    (128, "r65"): 83, (128, "r72"): 92, (128, "r78"): 100,
    (1024, "r65"): 666, (1024, "r72"): 737, (1024, "r78"): 799,
}
for _w in WIDTHS:
    for _r in RATIOS:
        assert ROWS[(_w, RATIO_KEY[_r])] == int(round(_w * _r)), \
            "frozen m != round(n*ratio) for (%r, %r)" % (_w, _r)
del _w, _r

#: C2 (flagged): single-arm S variable profile is DV3-regular
#: (``lambda_edge = {3: 1.0}``); the only profile fully determined by the
#: frozen packet without extra parameters. Planner/main-thread to confirm
#: before R23c; a change re-cuts the B1 tables through the same D9 import.
LAMBDA_S = {3: 1.0}
#: Frozen q-ary-symmetric error probability (S-regime U2 oracle).
P_ERR = 0.61
Q = r2.Q
BITS_PER_ROW = 5

#: Frozen graph seeds: 2 per (width, ratio) = 12 total. Fresh 48xx picks;
#: absence/disjointness proven in the R23b return (E23b-seeds) and guarded
#: live below (fail-closed at import).
GRAPH_SEEDS = {
    (128, "r65"): (2026094801, 2026094802),
    (128, "r72"): (2026094803, 2026094804),
    (128, "r78"): (2026094805, 2026094806),
    (1024, "r65"): (2026094811, 2026094812),
    (1024, "r72"): (2026094813, 2026094814),
    (1024, "r78"): (2026094815, 2026094816),
}
#: Frozen oracle block-seed scheme: 8 per (width, ratio), shared across the
#: 2 graphs (paired trials); disjoint sub-ranges from the graph seeds.
BLOCK_SEEDS = {
    (128, "r65"): tuple(range(2026094831, 2026094839)),
    (128, "r72"): tuple(range(2026094839, 2026094847)),
    (128, "r78"): tuple(range(2026094847, 2026094855)),
    (1024, "r65"): tuple(range(2026094861, 2026094869)),
    (1024, "r72"): tuple(range(2026094869, 2026094877)),
    (1024, "r78"): tuple(range(2026094877, 2026094885)),
}

#: Scope tag carried by every R23 decoder record. The gate accepts only
#: this tag, so D19 (or any predecessor) evidence cannot enter the S gate.
R23_BATCH_ID = "r23-scale-s-v1"

#: Decoder contract reused from R2 (no re-declaration): cold row-layered
#: 90/1.0, warm_beliefs=None, single-pass, one call per planned identity.
DECODER_MAX_ITER = r2.DECODER_MAX_ITER
DAMPING_ALPHA = r2.DAMPING_ALPHA
assert DECODER_MAX_ITER == 90 and DAMPING_ALPHA == 1.0

#: Budgets (frozen): <=96 scientific (2 widths x 3 ratios x 2 graphs x
#: 8 blocks); <=12 setup (12 graph objects); wall <=3600 s total;
#: <=300 s/call; per-build sub-caps n128<=60 s / n1024<=300 s (checked at
#: R23c setup over recorded construction_wall_s).
SCIENTIFIC_CALL_CEILING = 96
SETUP_CALL_CEILING = 12
WALL_BUDGET_S = 3600.0
PER_CALL_BUDGET_S = 300.0
PER_BUILD_SUBCAP_S = {128: 60.0, 1024: 300.0}
RSS_BUDGET_BYTES = r2.RSS_BUDGET_BYTES

#: Shared constructor/admission/dispatch/D9-rule (import, not copy).
build_degree_sequence_peg = r2.build_degree_sequence_peg
structural_record = r2.structural_record
dense_from_edges = r2.dense_from_edges
dispatch_l1 = r2.dispatch_l1
graph_realization_cell = d9.graph_realization_cell
StructureNotAdmitted = r2.StructureNotAdmitted

#: FROZEN R23c-R1 gate literals (packet text EXACTLY; no D19 scaling):
#: anchor cells n1024@r65 (hi) and n128@r65 (lo); WIN iff hi>=6/16 AND
#: gap>=+4/16 AND batch undetected==0; DEAD iff hi<=2/16 OR gap<+4/16;
#: else INCONCLUSIVE; undetected>0 -> STOP absolute.
ANCHOR_HI = (1024, "r65")
ANCHOR_LO = (128, "r65")
WIN_MIN_HI = 6
WIN_MIN_GAP = 4
DEAD_MAX_HI = 2
CELL_TRIALS = 16
GRAPHS_PER_CELL = 2
BLOCKS_PER_GRAPH = 8

WIN = "WIN"
DEAD = "DEAD"
INCONCLUSIVE = "INCONCLUSIVE"
STOP = "STOP"

FUTURE_ROOT_UUID = "a3f1c9d2-4b7e-4f2a-9e1d-8c5f6a7b9d0e"
FUTURE_ROOT = "workspace/r23_scale_" + FUTURE_ROOT_UUID
#: Frozen stage-1 ARGV (exact, venv only): dry-run profile, no-write.
FROZEN_STAGE1_ARGV = [".venv/bin/python", "scripts/v72p2r23_scale.py",
                      "--profile-only"]
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2r23_scale.py --r23-batch "
    "--execution-authorized --out-root %s" % FUTURE_ROOT)
AUTHORIZATION = (
    "separate explicit user/main-thread authorization required before "
    "--r23-batch")

EVIDENCE_FILES = ("manifest.json", "decoder_records.csv",
                  "graph_records.csv", "cell_summary.csv", "summary.json",
                  "command_log.txt")

#: Fresh-range guard (fail-closed at import): 12 graph + 48 block seeds,
#: internally disjoint, disjoint from every prior named seed set
#: (R2/R3 graphs+blocks, D11 L1/L2 graphs+blocks, D12, D14N, D15, D16,
#: D19) plus frozen literals (D8/D9 DE+cert, R7 DE+pool, G6 graphs+mothers,
#: v22/v23 CLI default seeds), sandwiched in the proven-free interval
#: (2026094723, 2026095001).
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
    | set(d16.BLOCK_SEEDS)
    | {s for seeds in d19.GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in d19.BLOCK_SEEDS.values() for s in seeds}
    | {2026091401, 2026091601, 2026091602, 2026091603,
       2026091801, 2026091802, 2026091803, 2026091804, 2026091805,
       2026094601, 2026094602}
    | set(range(2026094701, 2026094709)) | set(range(2026094711, 2026094720))
    | {2026094720, 2026094721, 2026094722, 2026094723}
    | {2026095001, 2026098001, 2026099001})
_R23_GRAPH = {s for seeds in GRAPH_SEEDS.values() for s in seeds}
_R23_BLOCK = {s for seeds in BLOCK_SEEDS.values() for s in seeds}
if len(_R23_GRAPH) != 12 or len(_R23_BLOCK) != 48:
    raise ValueError("R23 frozen seed sets have wrong cardinality")
if not _R23_GRAPH.isdisjoint(_R23_BLOCK):
    raise ValueError("R23 graph/block seeds overlap")
if not _R23_GRAPH.isdisjoint(_PRIOR_NAMED) \
        or not _R23_BLOCK.isdisjoint(_PRIOR_NAMED):
    raise ValueError("R23 seed collides with a prior named seed")
if min(_R23_GRAPH) <= 2026094723 or max(_R23_BLOCK) >= 2026095001:
    raise ValueError("R23 seed outside the proven-free interval")
del _PRIOR_NAMED, _R23_GRAPH, _R23_BLOCK


# --------------------------------------------------------------------------- #
# Rate math + D9 tables (computed through the D9 import, never hand-filled)
# --------------------------------------------------------------------------- #
def disclosed_bits(rows: int) -> int:
    """Disclosed bits per block: syndrome bits ``5m`` only.

    Synthetic oracle path has no tag/prior: Model-F is not carried, so no
    prior disclosure is added. Stated explicitly per the frozen packet.
    """
    return int(rows) * BITS_PER_ROW


def degree_cell(width: int, ratio_key: str) -> dict[str, Any]:
    """Frozen S ``(n, m, var/check counts, E)`` cell via the D9 rule.

    Calls ``d9.graph_realization_cell`` (import-reuse: largest-remainder
    node apportionment + concentrated floor/ceil check allocation); raises
    ``d9.GraphRealizationError`` on any unrealizable cell.
    """
    width, ratio_key = int(width), str(ratio_key)
    if (width, ratio_key) not in ROWS:
        raise KeyError("unknown R23 cell %r" % ((width, ratio_key),))
    m = ROWS[(width, ratio_key)]
    cell = graph_realization_cell(dict(LAMBDA_S), width, m,
                                  candidate_id="R23-S-DV3")
    var_counts = {3: width}
    check_counts = {int(d): int(c)
                    for d, c in cell["check_degree_allocation"].items()}
    if cell["n3"] != width or cell["E"] != 3 * width:
        raise ValueError("D9 cell broke DV3 regularity for %r"
                         % ((width, ratio_key),))
    return {"n": width, "m": m, "ratio_key": ratio_key,
            "var_counts": var_counts, "check_counts": check_counts,
            "E": int(cell["E"]),
            "rate": 1.0 - m / width,
            "disclosed_bits": disclosed_bits(m)}


# --------------------------------------------------------------------------- #
# Graph construction (R2 path reused, never duplicated)
# --------------------------------------------------------------------------- #
def coefficient_seed(width: int, ratio_key: str, graph_seed: int) -> int:
    """Frozen coefficient stream seed (single R23 namespace)."""
    return common.v10_seed("r23:scale:coeff:%d:%s:%d"
                           % (int(width), str(ratio_key), int(graph_seed)))


def coefficients_for_edges(edges: Sequence[Sequence[int]], width: int,
                           ratio_key: str, graph_seed: int) -> list[int]:
    """One uniform nonzero GF32 draw per edge in sorted ``(v, c)`` order."""
    rng = np.random.default_rng(coefficient_seed(width, ratio_key,
                                                 graph_seed))
    out = []
    for _ in sorted((int(v), int(c)) for v, c in
                    (tuple(e) for e in edges)):
        coeff = int(rng.integers(1, Q))
        if coeff == 0:
            raise ValueError("coefficient sampler produced zero")
        out.append(coeff)
    return out


def build_graph(width: int, ratio_key: str, graph_seed: int,
                *, peg_fn=None) -> dict[str, Any]:
    """Build one frozen R23 graph: PEG edges, coefficients, structure.

    Admission A1–A6 before any decoder binding: A1–A5 from the structural
    record plus A6 deterministic replay equality. Any failure is retained
    with ``admitted=False`` and engineering-blocks the cell at R23c setup;
    seeds are never altered, repaired or searched. ``peg_fn`` defaults to
    the frozen R2 constructor (fake-injectable on the test path only).
    """
    cell = degree_cell(int(width), str(ratio_key))  # scope guard
    if int(graph_seed) not in GRAPH_SEEDS[(int(width), str(ratio_key))]:
        raise ValueError("graph seed %r outside frozen R23 cell %r"
                         % (graph_seed, (int(width), str(ratio_key))))
    peg = peg_fn or build_degree_sequence_peg
    construction = peg(int(cell["n"]), int(cell["m"]), cell["var_counts"],
                       cell["check_counts"], int(graph_seed))
    record: dict[str, Any] = {
        "arm": ARM, "width": int(width), "ratio": str(ratio_key),
        "graph_seed": int(graph_seed),
        "n": int(cell["n"]), "m": int(cell["m"]), "E": 0, "edges": [],
        "coefficients": [], "dense": None, "structure": None,
        "status": "construction_failed", "admitted": False,
        "failure_reason": construction.get("failure_reason", ""),
    }
    if construction["status"] != "ok":
        return record
    coefficients = coefficients_for_edges(construction["edges"], int(width),
                                          str(ratio_key), int(graph_seed))
    dense = dense_from_edges(int(cell["n"]), int(cell["m"]),
                             construction["edges"], coefficients)
    structure = structural_record(dense, cell["var_counts"],
                                  cell["check_counts"])
    replay = peg(int(cell["n"]), int(cell["m"]), cell["var_counts"],
                 cell["check_counts"], int(graph_seed))
    replay_coeffs = coefficients_for_edges(replay["edges"], int(width),
                                           str(ratio_key), int(graph_seed))
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
# Synthetic q-ary-symmetric U2 oracle sampler (NO prior chain, NO Model-F)
# --------------------------------------------------------------------------- #
def sample_oracle_block(width: int, ratio_key: str,
                        seed: int) -> dict[str, Any]:
    """One synthetic oracle block: uniform truth + truth-conditioned rows.

    Truth ``u`` is uniform over GF32 (seeded); each prior row carries
    ``1-p`` on truth and ``p/31`` elsewhere (exact q-ary-symmetric oracle,
    ``p=0.61``). ``weight`` is a direct ``rng.binomial(n, p)`` draw —
    descriptive only, never a gate (no Hutch estimator). Deterministic
    per frozen block seed.
    """
    n = int(width)
    if (n, str(ratio_key)) not in ROWS:
        raise KeyError("unknown R23 cell %r" % ((n, str(ratio_key)),))
    rng = np.random.default_rng(int(seed))
    truth = np.asarray(rng.integers(0, Q, n), dtype=np.int64)
    prior = np.full((n, Q), P_ERR / (Q - 1), dtype=np.float64)
    prior[np.arange(n), truth] = 1.0 - P_ERR
    return {"u": truth, "prior": prior,
            "weight": int(rng.binomial(n, P_ERR)),
            "n": n, "ratio": str(ratio_key), "block_seed": int(seed)}


# --------------------------------------------------------------------------- #
# Plan: exact call identities (deterministic 96-record plan)
# --------------------------------------------------------------------------- #
def build_call_plan() -> list[dict[str, Any]]:
    """Frozen 96-call matrix: width -> ratio -> graph -> block (arm S).

    Both graphs of a cell share the same eight oracle blocks (paired).
    ``call_idx`` is contiguous 0..95. Built + validated before any decoder
    binding or root touch.
    """
    plan: list[dict[str, Any]] = []
    for width in WIDTHS:
        for ratio in RATIOS:
            key = RATIO_KEY[ratio]
            m = ROWS[(width, key)]
            for graph_seed in GRAPH_SEEDS[(width, key)]:
                for block_seed in BLOCK_SEEDS[(width, key)]:
                    plan.append({
                        "call_idx": len(plan), "width": int(width),
                        "n": int(width), "m": int(m), "ratio": key,
                        "arm": ARM, "graph_seed": int(graph_seed),
                        "block_seed": int(block_seed),
                        "disclosed_bits": disclosed_bits(m)})
    return plan


# --------------------------------------------------------------------------- #
# Dispatch: shared paired identities; ungraded ORACLE diagnostic
# --------------------------------------------------------------------------- #
def run_s_oracle_call(graph: Mapping[str, Any], block: Mapping[str, Any],
                      entry: Mapping[str, Any], *, decode_fn, syndrome_fn,
                      call_idx: int) -> dict[str, Any]:
    """One S-oracle call under the synthetic truth-conditioned prior.

    Reuses the shared ``r2.dispatch_l1`` kernel on the remapped block,
    then tags the record ORACLE/ungraded under the R23 batch scope. Only
    exact counts enter the gate; syndrome-valid/undetected/iterations/
    residual/oracle-weight are carried separately and never substitute
    for exact. No retry/resume/warm start.
    """
    if graph.get("dense") is None or not bool(graph.get("admitted")):
        raise StructureNotAdmitted(
            "refusing decoder binding for non-admitted R23 graph %r"
            % ({"width": graph.get("width"), "ratio": graph.get("ratio"),
                "graph_seed": graph.get("graph_seed")},))
    if decode_fn is None or not callable(decode_fn):
        raise ValueError("decode_fn must be explicitly injected")
    if syndrome_fn is None or not callable(syndrome_fn):
        raise ValueError("syndrome_fn must be explicitly injected")
    remapped = {"u1": np.asarray(block["u"], dtype=np.int64),
                "prior": np.asarray(block["prior"], dtype=np.float64)}
    base = dispatch_l1(
        graph, remapped,
        {"width": int(entry["width"]), "arm": str(entry["arm"]),
         "graph_seed": int(entry["graph_seed"]),
         "block_seed": int(entry["block_seed"])},
        decode_fn, syndrome_fn, call_idx=int(call_idx))
    base.update({
        "n": int(entry["n"]), "m": int(entry["m"]),
        "ratio": str(entry["ratio"]),
        "batch_id": R23_BATCH_ID, "oracle": True, "graded": False,
        "belief_provenance": "ORACLE",
        "undetected": False,
        "oracle_weight": int(block.get("weight", -1)),
        "disclosed_bits": disclosed_bits(int(entry["m"])),
    })
    return base


def execute_plan(plan: Sequence[Mapping[str, Any]],
                 graphs: Mapping[Any, Mapping[str, Any]],
                 blocks: Mapping[Any, Mapping[Any, Mapping[str, Any]]],
                 decode_fn, syndrome_fn, *,
                 now=None, rss_fn=None,
                 wall_budget_s: float = WALL_BUDGET_S,
                 per_call_budget_s: float = PER_CALL_BUDGET_S,
                 rss_budget_bytes: int = RSS_BUDGET_BYTES,
                 call_ceiling: int = SCIENTIFIC_CALL_CEILING
                 ) -> dict[str, Any]:
    """Dispatch the frozen 96-plan with 12/12 admission-first binding.

    All 12 graphs are admission-checked before ANY decoder binding; any
    failure engineering-blocks with zero decoder calls and no seed change
    (4408-class path). Decoder crashes are retained, never retried.
    Resource checks run between/after calls only.
    """
    import time as _time

    now = now or _time.monotonic
    t0 = float(now())
    records: list[dict[str, Any]] = []
    required: list[tuple[int, str, int]] = []
    for entry in plan:
        key = (int(entry["width"]), str(entry["ratio"]),
               int(entry["graph_seed"]))
        if key not in required:
            required.append(key)
    failure: str | None = None
    for width, ratio, graph_seed in required:
        graph = graphs.get((width, ratio, graph_seed))
        if graph is None or not bool(graph.get("admitted")):
            failure = ("graph (width=%d, ratio=%s, seed=%d) not admitted; "
                       "blocked without seed replacement"
                       % (width, ratio, graph_seed))
            break
    if failure is None:
        for entry in plan:
            if len(records) >= int(call_ceiling):
                failure = "scientific call ceiling reached"
                break
            graph = graphs[(int(entry["width"]), str(entry["ratio"]),
                            int(entry["graph_seed"]))]
            block = blocks[(int(entry["width"]), str(entry["ratio"]))][
                int(entry["block_seed"])]
            call_t0 = float(now())
            record = run_s_oracle_call(
                graph, block, entry, decode_fn=decode_fn,
                syndrome_fn=syndrome_fn, call_idx=len(records))
            record["wall_s"] = max(float(now()) - call_t0, 0.0)
            records.append(record)
            if record.get("crash"):
                failure = "decoder crash: %s" % record.get("error", "")
                break
            if float(record["wall_s"]) > float(per_call_budget_s):
                failure = ("per-call wall budget exceeded: %.3f s"
                           % float(record["wall_s"]))
                break
            if float(now()) - t0 > float(wall_budget_s):
                failure = "wall budget exceeded"
                break
            if rss_fn is not None \
                    and int(rss_fn()) >= int(rss_budget_bytes):
                failure = "RSS budget exceeded"
                break
    return {"records": records, "failure": failure or "",
            "decoder_calls": len(records)}


# --------------------------------------------------------------------------- #
# SYNTH gate: exact-only tallies, undetected never merged
# --------------------------------------------------------------------------- #
def cell_tally(records: Sequence[Mapping[str, Any]], width: int,
               ratio_key: str) -> dict[str, Any]:
    """Exact-only tally for one 16-trial cell from R23 records.

    Every contributing record must carry ``batch_id == R23_BATCH_ID`` and
    the frozen ``(width, ratio, graph, block)`` identity; the cell must
    contribute exactly 2 graphs x 8 blocks with every row ORACLE/ungraded.
    Anything else raises, so non-R23 evidence (incl. D19 reference graphs)
    cannot enter the gate.
    """
    width, ratio_key = int(width), str(ratio_key)
    scoped = [r for r in records if int(r.get("width", -1)) == width
              and str(r.get("ratio", "")) == ratio_key]
    plan_keys = {(int(e["width"]), str(e["ratio"]), int(e["graph_seed"]),
                  int(e["block_seed"]))
                 for e in build_call_plan()
                 if int(e["width"]) == width and str(e["ratio"]) == ratio_key}
    seen = set()
    per_graph: dict[int, int] = {}
    for record in scoped:
        if record.get("batch_id") != R23_BATCH_ID:
            raise ValueError("record without R23 batch tag cannot enter "
                             "the S gate: %r"
                             % ({k: record.get(k) for k in
                                 ("width", "ratio", "graph_seed",
                                  "block_seed", "batch_id")},))
        if bool(record.get("oracle", False)) is not True \
                or bool(record.get("graded", True)) is not False:
            raise ValueError("R23 rows must be ORACLE/ungraded: %r"
                             % ({k: record.get(k) for k in
                                 ("arm", "oracle", "graded")},))
        key = (int(record["width"]), str(record["ratio"]),
               int(record["graph_seed"]), int(record["block_seed"]))
        if key not in plan_keys:
            raise ValueError("record identity outside frozen R23 plan: %r"
                             % (key,))
        if key in seen:
            raise ValueError("duplicate R23 record identity: %r" % (key,))
        seen.add(key)
        per_graph.setdefault(key[2], 0)
        per_graph[key[2]] += 1 if record["exact"] else 0
    if seen != plan_keys:
        raise ValueError("R23 records cover %d/16 planned identities "
                         "(zero-skip)" % len(seen))
    ordered = GRAPH_SEEDS[(width, ratio_key)]
    e_g = [per_graph.get(s, 0) for s in ordered]
    return {"width": width, "ratio": ratio_key, "E_g": e_g,
            "E": sum(e_g)}


def route_scaling_gate(e_hi: int, e_lo: int, undetected_total: int,
                       engineering_reason: str = "") -> str:
    """Frozen R23c-R1 batch gate (packet text EXACTLY).

    ``e_hi`` = exact count n1024@r65 (/16); ``e_lo`` = exact count
    n128@r65 (/16); ``gap = e_hi - e_lo``. STOP iff ``engineering_reason``
    is non-empty (deviation/admission/budget contract breach) or batch
    ``undetected_total > 0`` (absolute); WIN iff ``e_hi >= 6`` AND
    ``gap >= +4`` (with undetected==0 already established); DEAD iff
    ``e_hi <= 2`` OR ``gap < +4``; else INCONCLUSIVE. Exact only;
    thresholds are frozen literals, never adaptive. Per-cell tallies stay
    descriptive diagnostics and never route the terminal.
    """
    if engineering_reason:
        return STOP
    e_hi, e_lo, undetected_total = int(e_hi), int(e_lo), int(undetected_total)
    if not 0 <= e_hi <= CELL_TRIALS or not 0 <= e_lo <= CELL_TRIALS:
        raise ValueError("anchor exact counts must lie in 0..16")
    if undetected_total > 0:
        return STOP
    gap = e_hi - e_lo
    if e_hi >= WIN_MIN_HI and gap >= WIN_MIN_GAP:
        return WIN
    if e_hi <= DEAD_MAX_HI or gap < WIN_MIN_GAP:
        return DEAD
    return INCONCLUSIVE


def check_build_budgets(graph_rows: Sequence[Mapping[str, Any]]
                        ) -> list[str]:
    """Per-build sub-cap audit over recorded ``construction_wall_s``.

    Returns violation strings (empty = within sub-caps); R23c setup gate.
    """
    violations = []
    for row in graph_rows:
        cap = PER_BUILD_SUBCAP_S.get(int(row["width"]))
        if cap is None:
            violations.append("row outside R23 widths: %r" % (row,))
        elif float(row["construction_wall_s"]) > float(cap):
            violations.append("build over sub-cap: width=%s seed=%s %.3fs"
                              % (row["width"], row.get("graph_seed"),
                                 float(row["construction_wall_s"])))
    return violations


# --------------------------------------------------------------------------- #
# D19 reference (byte-identical import REFERENCE only, never graded)
# --------------------------------------------------------------------------- #
def d19_reference_build(arm: str, graph_seed: int) -> dict[str, Any]:
    """Rebuild one frozen D19 n128-m94 graph through the D19 import.

    Reference only: the returned object is never admitted to the S gate
    (``cell_tally`` rejects its batch tag). Byte-identity against a direct
    ``d19.build_graph`` call is asserted in tests.
    """
    if str(arm) not in d19.ARMS or int(graph_seed) not in d19.GRAPH_SEEDS[128]:
        raise ValueError("outside frozen D19 n128 reference: %r"
                         % ((arm, graph_seed),))
    return d19.build_graph(str(arm), 128, int(graph_seed))


# --------------------------------------------------------------------------- #
# Root refusal (R2 base + explicit R23 protected names)
# --------------------------------------------------------------------------- #
#: Never-written roots by name (D19 future root, Model-F prior root,
#: registry/evidence anchors). The R23 future root itself is refused iff it
#: already exists (never overwrite); absence is proven, not created, in R23b.
R23_PROTECTED_NAMES = frozenset({
    "d19_l2_finite_ensemble_5f2b8c1d-7a3e-4f90-b6d4-8e1a2c3d4f5a6b",
    "v72p2d5_model_f_input",
    "v71_data_registry.json",
    "v67_data_registry.json",
})


def refuse_out_root(out_root):
    """Refuse protected roots and any existing root; return resolved path."""
    resolved = r2.refuse_out_root(out_root)
    for part in resolved.parts:
        if part in R23_PROTECTED_NAMES:
            raise ValueError("refusing protected root %s" % resolved)
    return resolved
