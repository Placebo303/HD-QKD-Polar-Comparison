"""R23b weak-prior retest runner — readiness paths (NOT execution).

Frozen scope (planner return this session; Track EXPLORE-readiness):
W-scope 0.65-only default, conditional-0.72 OFF (second grant + extension
rule; flag default off, no auto-run); W-prior Model-F marginal,
decoder-input-only (read-only npz load, SAME path as R9
``workspace/v72p2d5_model_f_input/20260907_r1`` via the D5 loader);
W-graphs REUSE the R23 12 (same seeds/namespaces/builder; deterministic
rebuild happens at execution START as setup, never in readiness);
W-gate same frozen R23c-R1 text + calibration guard n128@0.65 <= 4/16
(trip -> regime-mismatch STOP); W-decoder cold 90/1.0 single-pass,
one call per planned identity, no retry; W-bud sci <= 64 / setup <= 8
(32/4 default + 32/4 conditional); W-bias independent blocks (fresh
per-graph block seeds, never the shared R23 pairing); W-auth default
no-execute rc2 no-write + fresh-root refusal.

Decode path: truth blocks STILL come from the oracle p=0.61 sampler
(unchanged); the prior FED TO THE DECODER is the tiled Model-F U2
population marginal INSTEAD of the oracle rows (block["prior"] is never
read on the decode path). Decode provenance must contain NO ORACLE token
(hard-fail assert in :func:`run_w_weak_call`).

Paths:

- ``--profile-only``: validate the frozen 32-call default plan, print
  per-cell D9 geometry + budget meta + future-root absence; zero decoder
  calls, zero graph builds, zero filesystem writes;
- ``--weak-batch``: the frozen matrix (32 scientific calls default, 64
  with ``--include-r72``; 4 setup graphs default, 8 extended; graphs
  rebuilt identically through the R23 import); refuses with rc2 unless
  ``--execution-authorized`` is passed (default false; refusal before any
  root creation, prior load, or decoder bind); ``--include-r72`` refuses
  with rc2 unless ``--extension-authorized`` is passed (default false);
- ``--verify``: read-only recomputation of a completed weak root with
  zero skip, zero decoder calls; exits FAIL on any partial or
  engineering-blocked root.

One fresh root per run; refuses overwrite and protected roots (single
process, no retry, no resume, no seed search, no adaptive stop). R23
oracle records can never enter the weak gate: decoder records carry
``batch_id == r23b-weak-w-v1`` with ``oracle == False`` and the weak
provenance token, and the tally constructor rejects anything else.
"""

from __future__ import annotations

import argparse
import csv
import inspect
import json
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))

from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d10_mixed_degree_l1 as r2)
from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d10_r3_fresh_scaling as r3)
from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d11_forward_app as d11)
from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d12_finite_l1_degree as d12)
from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d14n_calibrated_discriminator as d14n)
from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d15_margin_curve as d15)
from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d16_matched_backoff as d16)
from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d19_l2_finite as d19)
from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d5_model_f_input as d5)
from comparison_bench.formal_ir import (  # noqa: E402
    v72p2r23_scale as r23)

import numpy as np  # noqa: E402

# --------------------------------------------------------------------------- #
# Frozen identifiers
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2r23-weak-prior-retest"
CYCLE_ID = "V72P3R23-SCALE"
STEP = "R23b-readiness"
TRACK = "EXPLORE-readiness"
CLAIM_CEILING = (
    "synthetic weak-prior retest diagnostic under the frozen R23 graphs, "
    "the frozen oracle truth sampler, the Model-F U2 population marginal "
    "as decoder input only, and the frozen cold 90/1.0 decoder contract; "
    "no FER/leakage/SKR/qualification/promotion/publication/route-closure "
    "claim; R23b grants no execution and makes zero decoder calls"
)

#: Weak arm tag (distinct from the R23 oracle arm ``S``).
ARM = "W"
#: W-scope: 0.65-only default; 0.72 conditional (flag-gated, default off).
RATIOS_DEFAULT = (0.65,)
RATIO_EXTENSION = (0.72,)
RATIO_KEY = r23.RATIO_KEY
#: Scope tag carried by every weak decoder record. The tally accepts only
#: this tag, so R23 oracle evidence cannot enter the weak gate (and weak
#: records cannot enter the R23 gate: batch mismatch raises there too).
R23B_BATCH_ID = "r23b-weak-w-v1"
#: Exact decode-provenance token stamped on every weak record. The tally
#: requires this exact string; the decode path hard-fails on any ORACLE
#: token before stamping.
WEAK_PROVENANCE = "WEAK-MODEL-F-MARGINAL"

#: W-prior path: SAME artifact path as R9 (read-only npz load through the
#: D5 loader; decoder-input-only, never truth, never disclosure).
FROZEN_PRIOR_ROOT = "workspace/v72p2d5_model_f_input/20260907_r1"
assert FROZEN_PRIOR_ROOT == r2.MODEL_F_INPUT_ROOT
assert FROZEN_PRIOR_ROOT == d5.MODEL_F_FORMAL_ROOT

#: Decoder contract reused from R2 (no re-declaration): cold row-layered
#: 90/1.0, warm_beliefs=None, single-pass, one call per planned identity.
DECODER_MAX_ITER = r2.DECODER_MAX_ITER
DAMPING_ALPHA = r2.DAMPING_ALPHA
assert DECODER_MAX_ITER == 90 and DAMPING_ALPHA == 1.0

#: W-bias independent blocks: 8 FRESH seeds per (width, ratio, graph),
#: never the shared R23 pairing. Ranges sit above the R23 block maximum
#: (4884) inside the proven-free interval (4723, 5001); disjointness is
#: guarded fail-closed at import below.
WEAK_BLOCK_SEEDS = {
    (128, "r65", 0): tuple(range(2026094885, 2026094893)),
    (128, "r65", 1): tuple(range(2026094893, 2026094901)),
    (1024, "r65", 0): tuple(range(2026094901, 2026094909)),
    (1024, "r65", 1): tuple(range(2026094909, 2026094917)),
    (128, "r72", 0): tuple(range(2026094917, 2026094925)),
    (128, "r72", 1): tuple(range(2026094925, 2026094933)),
    (1024, "r72", 0): tuple(range(2026094933, 2026094941)),
    (1024, "r72", 1): tuple(range(2026094941, 2026094949)),
}

#: W-bud: sci <= 64 (32 default + 32 conditional), setup <= 8 (4 + 4).
#: Wall / per-call / per-build sub-caps reused from R23 unchanged.
SCIENTIFIC_CALL_CEILING = 64
SETUP_CALL_CEILING = 8
DEFAULT_CALLS = 32
DEFAULT_GRAPHS = 4
WALL_BUDGET_S = r23.WALL_BUDGET_S
PER_CALL_BUDGET_S = r23.PER_CALL_BUDGET_S
PER_BUILD_SUBCAP_S = dict(r23.PER_BUILD_SUBCAP_S)

#: W-gate calibration guard: n128@0.65 exact must stay <= 4/16 under the
#: weak prior; anything above trips a regime-mismatch STOP before the
#: frozen R23c-R1 text is applied.
CAL_ANCHOR = (128, "r65")
CAL_MAX_LO = 4
CELL_TRIALS = r23.CELL_TRIALS

WIN = r23.WIN
DEAD = r23.DEAD
INCONCLUSIVE = r23.INCONCLUSIVE
STOP = r23.STOP
CALIBRATION_STOP_REASON = "regime-mismatch: n128@0.65 exact > 4/16"

FUTURE_ROOT_UUID = "73ef80ff-332e-4569-870f-cae33c41a89f"
FUTURE_ROOT = "workspace/r23b_weak_" + FUTURE_ROOT_UUID
#: Frozen stage-1 ARGV (exact, venv only): dry-run profile, no-write.
FROZEN_STAGE1_ARGV = [".venv/bin/python",
                      "scripts/v72p2r23_scale_weak.py",
                      "--profile-only"]
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2r23_scale_weak.py --weak-batch "
    "--execution-authorized --out-root %s" % FUTURE_ROOT)
AUTHORIZATION = (
    "separate explicit user/main-thread authorization required before "
    "--weak-batch")
EXTENSION_AUTHORIZATION = (
    "separate explicit user/main-thread authorization required before "
    "--include-r72 (conditional 0.72 arm; default off, no auto-run)")

EVIDENCE_FILES = r23.EVIDENCE_FILES

DECODER_RECORD_COLUMNS = (
    "call_idx", "width", "n", "m", "ratio", "arm",
    "graph_seed", "block_seed", "batch_id", "exact",
    "syndrome_ok", "undetected", "oracle", "graded", "belief_provenance",
    "iterations", "status", "residual_syndrome_weight",
    "oracle_weight", "prior_mass_on_truth",
    "wall_s", "crash", "error", "disclosed_bits")
GRAPH_RECORD_COLUMNS = (
    "arm", "width", "ratio", "graph_seed", "n", "m", "E", "status",
    "admitted", "failure_reason", "admission", "construction_wall_s")
CELL_SUMMARY_COLUMNS = (
    "width", "ratio", "scope", "graph_ordinal", "blocks", "exact_count",
    "syndrome_valid_count", "undetected_count")

#: Fresh-range guard (fail-closed at import): 64 weak block seeds,
#: internally disjoint, disjoint from the R23 12+48 seeds and from every
#: prior named seed set (same composition as the R23 guard), sandwiched
#: in the proven-free interval (2026094723, 2026095001).
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
_R23_SEEDS = ({s for seeds in r23.GRAPH_SEEDS.values() for s in seeds}
              | {s for seeds in r23.BLOCK_SEEDS.values() for s in seeds})
_WEAK_BLOCK = {s for seeds in WEAK_BLOCK_SEEDS.values() for s in seeds}
if len(_WEAK_BLOCK) != 64:
    raise ValueError("weak block seeds have wrong cardinality")
if any(len(WEAK_BLOCK_SEEDS[key]) != 8 for key in WEAK_BLOCK_SEEDS):
    raise ValueError("every weak (width, ratio, graph) group holds 8 seeds")
if not _WEAK_BLOCK.isdisjoint(_R23_SEEDS):
    raise ValueError("weak block seed collides with an R23 seed")
if not _WEAK_BLOCK.isdisjoint(_PRIOR_NAMED):
    raise ValueError("weak block seed collides with a prior named seed")
if min(_WEAK_BLOCK) <= 2026094723 or max(_WEAK_BLOCK) >= 2026095001:
    raise ValueError("weak block seed outside the proven-free interval")
del _PRIOR_NAMED, _R23_SEEDS, _WEAK_BLOCK


def _active_ratios(include_r72: bool) -> tuple:
    ratios = list(RATIOS_DEFAULT)
    if include_r72:
        ratios.append(RATIO_EXTENSION[0])
    return tuple(ratios)


def _graph_ordinals(width: int, ratio_key: str) -> tuple:
    return tuple(range(len(r23.GRAPH_SEEDS[(int(width), str(ratio_key))])))


# --------------------------------------------------------------------------- #
# W-prior: Model-F U2 population marginal (read-only, decoder-input-only)
# --------------------------------------------------------------------------- #
def load_weak_marginal(prior_root):
    """Load the Model-F U2 population marginal from the frozen npz root.

    Read-only reload through the D5 loader (SAME path as R9: exactly the
    two frozen files, revalidated). The decoder-input prior is the Bob
    marginal ``p_b`` folded over the high bits to U2 (low 5 bits),
    floored at 1e-15 and renormalized — one 32-vector, identical for
    every position, carrying no per-block truth information. Never used
    for truth sampling, disclosure, or gating (decoder-input-only).
    """
    bundle = d5.load_model_f_input(prior_root)
    p_b = np.asarray(bundle["p_b"], dtype=np.float64).ravel()
    if p_b.shape != (1024,):
        raise ValueError("Model-F p_b must have shape (1024,)")
    marginal = np.zeros(32, dtype=np.float64)
    for high in range(32):
        marginal += p_b[np.arange(32) + 32 * high]
    if not np.all(np.isfinite(marginal)) or marginal.sum() <= 0.0:
        raise ValueError("Model-F U2 marginal is not a distribution")
    marginal = np.maximum(marginal, 1e-15)
    marginal /= marginal.sum()
    return marginal


def weak_prior_for_block(width: int, marginal_32) -> np.ndarray:
    """Tile the 32-vector marginal across all ``n`` positions (n, 32)."""
    marginal = np.asarray(marginal_32, dtype=np.float64).ravel()
    if marginal.shape != (32,):
        raise ValueError("weak marginal must have shape (32,)")
    if not np.all(np.isfinite(marginal)) or np.any(marginal <= 0.0):
        raise ValueError("weak marginal rows must be positive and finite")
    if abs(float(marginal.sum()) - 1.0) > 1e-9:
        raise ValueError("weak marginal must sum to 1")
    return np.tile(marginal, (int(width), 1))


# --------------------------------------------------------------------------- #
# Decode path: oracle truth, weak prior (NO ORACLE token allowed downstream)
# --------------------------------------------------------------------------- #
def run_w_weak_call(graph, block, marginal_32, entry, *, decode_fn,
                    syndrome_fn, call_idx: int) -> dict:
    """One weak-prior call: oracle truth in, Model-F marginal to decoder.

    Truth ``u`` (and the descriptive ``weight``) still come from the
    oracle p=0.61 sampler; ``block["prior"]`` (oracle rows) is NEVER read
    here — the decoder receives only the tiled weak marginal. The
    decoder-returned provenance is hard-checked for any ORACLE token
    (case-insensitive) BEFORE the weak token is stamped; a violation
    raises instead of recording. No retry/resume/warm start.
    """
    from comparison_bench.formal_ir import (  # local: reuse kernel by import
        v72p2d10_mixed_degree_l1 as _r2)

    if graph.get("dense") is None or not bool(graph.get("admitted")):
        raise _r2.StructureNotAdmitted(
            "refusing decoder binding for non-admitted weak graph %r"
            % ({"width": graph.get("width"), "ratio": graph.get("ratio"),
                "graph_seed": graph.get("graph_seed")},))
    if decode_fn is None or not callable(decode_fn):
        raise ValueError("decode_fn must be explicitly injected")
    if syndrome_fn is None or not callable(syndrome_fn):
        raise ValueError("syndrome_fn must be explicitly injected")
    n = int(entry["n"])
    remapped = {"u1": np.asarray(block["u"], dtype=np.int64),
                "prior": weak_prior_for_block(n, marginal_32)}
    base = _r2.dispatch_l1(
        graph, remapped,
        {"width": int(entry["width"]), "arm": str(entry["arm"]),
         "graph_seed": int(entry["graph_seed"]),
         "block_seed": int(entry["block_seed"])},
        decode_fn, syndrome_fn, call_idx=int(call_idx))
    decoder_provenance = str(base.get("belief_provenance") or "")
    if "ORACLE" in decoder_provenance.upper():
        raise AssertionError(
            "ORACLE token on the weak decode path (call %d): %r"
            % (int(call_idx), decoder_provenance))
    base.update({
        "n": n, "m": int(entry["m"]),
        "ratio": str(entry["ratio"]),
        "batch_id": R23B_BATCH_ID, "oracle": False, "graded": False,
        "belief_provenance": WEAK_PROVENANCE,
        "undetected": False,
        "oracle_weight": int(block.get("weight", -1)),
        "disclosed_bits": r23.disclosed_bits(int(entry["m"])),
    })
    return base


# --------------------------------------------------------------------------- #
# Plan: exact call identities (deterministic 32/64-record plan)
# --------------------------------------------------------------------------- #
def build_weak_plan(include_r72: bool = False) -> list:
    """Frozen weak matrix: width -> ratio -> graph -> block (arm W).

    Default 32 calls (2 widths x r65 x 2 graphs x 8 independent blocks);
    64 with the conditional 0.72 arm. Graphs carry the R23 seeds
    identically; blocks use the fresh per-graph weak seeds (independent
    trials, never shared across graphs). ``call_idx`` is contiguous.
    Built + validated before any decoder binding or root touch.
    """
    plan: list = []
    for width in r23.WIDTHS:
        for ratio in _active_ratios(include_r72):
            key = RATIO_KEY[ratio]
            m = r23.ROWS[(width, key)]
            for ordinal, graph_seed in enumerate(
                    r23.GRAPH_SEEDS[(width, key)]):
                for block_seed in WEAK_BLOCK_SEEDS[(width, key, ordinal)]:
                    plan.append({
                        "call_idx": len(plan), "width": int(width),
                        "n": int(width), "m": int(m), "ratio": key,
                        "arm": ARM, "graph_seed": int(graph_seed),
                        "block_seed": int(block_seed),
                        "disclosed_bits": r23.disclosed_bits(m)})
    return plan


def _validate_weak_plan(plan, include_r72: bool = False) -> list:
    """Contract-check the frozen weak plan BEFORE binding/building/decoding.

    Frozen order (width ascending; ratio ascending; graphs ascending;
    blocks ascending) with frozen cells, R23 graph seeds and per-graph
    independent weak block groups; arm W throughout. Any deviation raises
    before any adapter is bound, any graph is built, or the root is
    touched.
    """
    want = DEFAULT_CALLS + (DEFAULT_CALLS if include_r72 else 0)
    if len(plan) != want:
        raise ValueError("weak plan has %d calls, frozen %d"
                         % (len(plan), want))
    pos = 0
    for width in r23.WIDTHS:
        for ratio in _active_ratios(include_r72):
            key = RATIO_KEY[ratio]
            m = r23.ROWS[(width, key)]
            for ordinal, graph_seed in enumerate(
                    r23.GRAPH_SEEDS[(width, key)]):
                for block_seed in WEAK_BLOCK_SEEDS[(width, key, ordinal)]:
                    entry = plan[pos]
                    pos += 1
                    if entry.get("call_idx") != pos - 1 \
                            or int(entry.get("width", -1)) != width \
                            or int(entry.get("n", -1)) != width \
                            or int(entry.get("m", -1)) != m \
                            or str(entry.get("ratio", "")) != key \
                            or entry.get("arm") != ARM \
                            or int(entry.get("graph_seed", -1)) \
                            != int(graph_seed) \
                            or int(entry.get("block_seed", -1)) \
                            != int(block_seed) \
                            or int(entry.get("disclosed_bits", -1)) \
                            != r23.disclosed_bits(m):
                        raise ValueError(
                            "weak plan identity/order violated at %d: %r"
                            % (pos - 1, entry))
    if pos != len(plan):
        raise ValueError("weak plan order check covered %d/%d entries"
                         % (pos, len(plan)))
    return plan


def execute_weak_plan(plan, graphs, blocks, marginal_32, decode_fn,
                      syndrome_fn, *, now=None, rss_fn=None,
                      wall_budget_s: float = WALL_BUDGET_S,
                      per_call_budget_s: float = PER_CALL_BUDGET_S,
                      rss_budget_bytes: int = r2.RSS_BUDGET_BYTES,
                      call_ceiling: int = SCIENTIFIC_CALL_CEILING) -> dict:
    """Dispatch the frozen weak plan with admission-first binding.

    All setup graphs are admission-checked before ANY decoder binding; any
    failure engineering-blocks with zero decoder calls and no seed change.
    One decoder call per planned identity; decoder crashes are retained,
    never retried. Resource checks run between/after calls only.
    """
    import time as _time

    now = now or _time.monotonic
    t0 = float(now())
    records: list = []
    required: list = []
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
            record = run_w_weak_call(
                graph, block, marginal_32, entry, decode_fn=decode_fn,
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
# Weak gate: exact-only tallies + calibration guard, undetected never merged
# --------------------------------------------------------------------------- #
def weak_cell_tally(records, width: int, ratio_key: str) -> dict:
    """Exact-only tally for one 16-trial weak cell from weak records.

    Every contributing record must carry ``batch_id == R23B_BATCH_ID``,
    ``oracle is False`` and the exact weak provenance token; the cell must
    contribute exactly 2 graphs x 8 independent blocks matching the frozen
    weak plan (per-graph groups). Anything else raises, so non-weak
    evidence (incl. R23 oracle rows) cannot enter the gate.
    """
    width, ratio_key = int(width), str(ratio_key)
    scoped = [r for r in records if int(r.get("width", -1)) == width
              and str(r.get("ratio", "")) == ratio_key]
    # Rebuild the plan keys for the cell from the frozen plans (default
    # cells come from the 32-plan; conditional r72 cells from the 64-plan).
    plan_keys = set()
    for candidate in (build_weak_plan(include_r72=False),
                      build_weak_plan(include_r72=True)):
        for e in candidate:
            if int(e["width"]) == width and str(e["ratio"]) == ratio_key:
                plan_keys.add((int(e["width"]), str(e["ratio"]),
                               int(e["graph_seed"]), int(e["block_seed"])))
    seen = set()
    per_graph: dict = {}
    for record in scoped:
        if record.get("batch_id") != R23B_BATCH_ID:
            raise ValueError("record without weak batch tag cannot enter "
                             "the weak gate: %r"
                             % ({k: record.get(k) for k in
                                 ("width", "ratio", "graph_seed",
                                  "block_seed", "batch_id")},))
        if bool(record.get("oracle", True)) is not False:
            raise ValueError("weak rows must be non-oracle: %r"
                             % ({k: record.get(k) for k in
                                 ("arm", "oracle", "graded")},))
        if str(record.get("belief_provenance", "")) != WEAK_PROVENANCE:
            raise ValueError("weak rows must carry the weak provenance "
                             "token: %r"
                             % (record.get("belief_provenance"),))
        key = (int(record["width"]), str(record["ratio"]),
               int(record["graph_seed"]), int(record["block_seed"]))
        if key not in plan_keys:
            raise ValueError("record identity outside frozen weak plan: %r"
                             % (key,))
        if key in seen:
            raise ValueError("duplicate weak record identity: %r" % (key,))
        seen.add(key)
        per_graph.setdefault(key[2], 0)
        per_graph[key[2]] += 1 if record["exact"] else 0
    if seen != plan_keys:
        raise ValueError("weak records cover %d/16 planned identities "
                         "(zero-skip)" % len(seen))
    ordered = r23.GRAPH_SEEDS[(width, ratio_key)]
    e_g = [per_graph.get(s, 0) for s in ordered]
    return {"width": width, "ratio": ratio_key, "E_g": e_g,
            "E": sum(e_g)}


def route_weak_gate(e_hi: int, e_lo: int, undetected_total: int,
                    engineering_reason: str = "") -> str:
    """Weak batch gate: calibration guard, then the frozen R23c-R1 text.

    ``e_hi`` = exact count n1024@r65 (/16); ``e_lo`` = exact count
    n128@r65 (/16); ``gap = e_hi - e_lo``. STOP iff ``engineering_reason``
    is non-empty or batch ``undetected_total > 0`` (absolute, frozen
    text) or the calibration guard trips (``e_lo > 4``: regime-mismatch
    under the weak prior). Otherwise the frozen text applies literally:
    WIN iff ``e_hi >= 6`` AND ``gap >= +4``; DEAD iff ``e_hi <= 2`` OR
    ``gap < +4``; else INCONCLUSIVE. Exact only; thresholds are frozen
    literals, never adaptive.
    """
    if engineering_reason:
        return STOP
    e_hi, e_lo, undetected_total = int(e_hi), int(e_lo), int(undetected_total)
    if not 0 <= e_hi <= CELL_TRIALS or not 0 <= e_lo <= CELL_TRIALS:
        raise ValueError("anchor exact counts must lie in 0..16")
    if undetected_total > 0:
        return STOP
    if e_lo > CAL_MAX_LO:
        return STOP
    return r23.route_scaling_gate(e_hi, e_lo, undetected_total, "")


# --------------------------------------------------------------------------- #
# Root refusal (R2 base + explicit weak protected names)
# --------------------------------------------------------------------------- #
#: Never-written roots by name (R23 root, D19 future root, Model-F prior
#: root, registry anchors). The weak future root itself is refused iff it
#: already exists (never overwrite); absence is proven, not created, in
#: R23b-readiness.
R23B_PROTECTED_NAMES = frozenset({
    "r23_scale_a3f1c9d2-4b7e-4f2a-9e1d-8c5f6a7b9d0e",
    "d19_l2_finite_ensemble_5f2b8c1d-7a3e-4f90-b6d4-8e1a2c3d4f5a6b",
    "v72p2d5_model_f_input",
    "v71_data_registry.json",
    "v67_data_registry.json",
})


def refuse_out_root(out_root):
    """Refuse protected roots and any existing root; return resolved path."""
    resolved = r23.refuse_out_root(out_root)
    for part in resolved.parts:
        if part in R23B_PROTECTED_NAMES:
            raise ValueError("refusing protected root %s" % resolved)
    return resolved


def _peak_rss_bytes():
    # Linux ru_maxrss is KiB; single-process aggregate = this process.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _log_line(message):
    return "[%s] %s" % (time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                      time.gmtime()), message)


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _write_csv(path, columns, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})


def _read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _as_int(value):
    return int(str(value).strip())


def _as_float(value):
    return float(str(value).strip())


def _as_bool(value):
    text = str(value).strip().lower()
    if text in ("1", "true", "yes"):
        return True
    if text in ("0", "false", "no", ""):
        return False
    raise ValueError("not a boolean: %r" % (value,))


def _cell(value):
    return str(value if value is not None else "").strip()


# --------------------------------------------------------------------------- #
# cell summary rows (pooled + per-graph; exact/syndrome/undetected separate)
# --------------------------------------------------------------------------- #
def _cell_rows(records, include_r72: bool = False):
    rows = []
    for width in r23.WIDTHS:
        for ratio in _active_ratios(include_r72):
            key = RATIO_KEY[ratio]
            scoped = [rec for rec in records
                      if int(rec["width"]) == int(width)
                      and str(rec["ratio"]) == key]
            seeds = r23.GRAPH_SEEDS[(int(width), key)]
            for ordinal, seed in enumerate(seeds):
                cell = [rec for rec in scoped
                        if int(rec["graph_seed"]) == int(seed)]
                rows.append({
                    "width": width, "ratio": key, "scope": "graph",
                    "graph_ordinal": ordinal, "blocks": len(cell),
                    "exact_count": sum(1 for rec in cell if rec["exact"]),
                    "syndrome_valid_count":
                        sum(1 for rec in cell if rec["syndrome_ok"]),
                    "undetected_count":
                        sum(1 for rec in cell if rec["undetected"])})
            rows.append({
                "width": width, "ratio": key, "scope": "pooled",
                "graph_ordinal": "POOLED", "blocks": len(scoped),
                "exact_count": sum(1 for rec in scoped if rec["exact"]),
                "syndrome_valid_count":
                    sum(1 for rec in scoped if rec["syndrome_ok"]),
                "undetected_count":
                    sum(1 for rec in scoped if rec["undetected"])})
    return rows


def _cell_table_meta(include_r72: bool = False):
    return [{"arm": ARM, "n": int(width), "m": r23.ROWS[(width, key)],
             "ratio": key,
             "var_counts": dict(r23.degree_cell(width, key)["var_counts"]),
             "check_counts": dict(r23.degree_cell(width, key)[
                 "check_counts"]),
             "E": r23.degree_cell(width, key)["E"],
             "rate": r23.degree_cell(width, key)["rate"],
             "disclosed_bits": r23.disclosed_bits(
                 r23.ROWS[(width, key)])}
            for width in r23.WIDTHS for key in
            [RATIO_KEY[r] for r in _active_ratios(include_r72)]]


def _budget_meta():
    return {
        "scientific_calls": SCIENTIFIC_CALL_CEILING,
        "setup_calls": SETUP_CALL_CEILING,
        "wall_s": WALL_BUDGET_S,
        "per_call_s": PER_CALL_BUDGET_S,
        "per_build_s": dict(PER_BUILD_SUBCAP_S),
        "rss_bytes": r2.RSS_BUDGET_BYTES,
        "processes": 1,
        "retry": False, "resume": False,
        "seed_search": False, "adaptive_stop": False,
    }


def _graph_row(graph, wall_s):
    structure = graph.get("structure") or {}
    return {
        "arm": graph["arm"], "width": graph["width"],
        "ratio": graph["ratio"], "graph_seed": graph["graph_seed"],
        "n": graph["n"], "m": graph["m"], "E": graph["E"],
        "status": graph["status"], "admitted": bool(graph["admitted"]),
        "failure_reason": graph["failure_reason"],
        "admission": json.dumps((structure.get("admission") or {}),
                                sort_keys=True),
        "construction_wall_s": round(float(wall_s), 6),
    }


# --------------------------------------------------------------------------- #
# Production binder (narrow; resolve + signature-validate only)
# --------------------------------------------------------------------------- #
def _require_signature(fn, required, name):
    """Inspect-only contract check: ``fn`` callable with ``required`` params.

    No call, no decode — pure ``inspect.signature``. Raises before any root
    creation or decoder contact on mismatch.
    """
    if not callable(fn):
        raise TypeError("production adapter %r is not callable" % (name,))
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError) as exc:
        raise TypeError("production adapter %r has no valid signature: %s"
                        % (name, exc)) from exc
    missing = [p for p in required if p not in params]
    if missing:
        raise TypeError("production adapter %r signature %s lacks %s"
                        % (name, sorted(params), missing))
    return fn


def bind_production_adapters(prior_root: str = FROZEN_PRIOR_ROOT) -> dict:
    """Narrow binder: decoder kernels + frozen Model-F marginal, zero calls.

    The prior root must equal the frozen R9 path exactly (read-only npz
    load, decoder-input-only); anything else refuses before binding.
    Resolving never invokes: decoder calls happen only inside the
    authorized orchestrator after plan validation.
    """
    if str(prior_root) != FROZEN_PRIOR_ROOT:
        raise ValueError("refusing prior root %r (frozen %r)"
                         % (prior_root, FROZEN_PRIOR_ROOT))
    from comparison_bench.formal_ir import (  # lazy production bind
        v35_algorithm_development as v35)

    decode_fn = _require_signature(
        v35.decode_row_layered_fftqspa,
        ["h_matrix", "priors", "syndromes", "max_iter", "damping_alpha",
         "warm_beliefs", "field"], "decode_fn")
    syndrome_fn = _require_signature(
        v35.syndrome_of_gf32, ["matrix", "vector"], "syndrome_fn")
    return {
        "decode_fn": decode_fn,
        "syndrome_fn": syndrome_fn,
        "sample_fn": r23.sample_oracle_block,
        "build_fn": r23.build_graph,
        "marginal_32": load_weak_marginal(prior_root),
    }


# --------------------------------------------------------------------------- #
# Batch orchestrator (plan-first; admission-first; no filesystem writes)
# --------------------------------------------------------------------------- #
def run_authorized_batch(out_root, *, adapters=None, marginal_32=None,
                         prior_root: str = FROZEN_PRIOR_ROOT,
                         include_r72: bool = False,
                         extension_authorized: bool = False,
                         now_fn=None, rss_fn=None):
    """Execute the frozen weak matrix and return the evidence bundle.

    ``adapters`` is a flat dict with ``decode_fn``/``syndrome_fn``/
    ``sample_fn``/``build_fn``; ``None`` production-binds inside, AFTER
    plan validation, the extension gate and the refuse probe.
    ``marginal_32`` carries the weak 32-vector on the fake path (the
    production path loads it read-only from the frozen prior root).
    Returns the bundle consumed by :func:`write_batch_root`; creates no
    files and no directories.
    """
    plan = build_weak_plan(include_r72=include_r72)
    _validate_weak_plan(plan, include_r72=include_r72)
    if include_r72 and not extension_authorized:
        raise ValueError(
            "refusing conditional 0.72 arm: %s" % EXTENSION_AUTHORIZATION)
    resolved = refuse_out_root(out_root)  # probe only; creates nothing
    if adapters is None:
        inj = bind_production_adapters(prior_root)
        marginal = inj["marginal_32"]
    else:
        inj = dict(adapters)
        if str(prior_root) != FROZEN_PRIOR_ROOT:
            raise ValueError("refusing prior root %r (frozen %r)"
                             % (prior_root, FROZEN_PRIOR_ROOT))
        marginal = marginal_32
    missing = [key for key in ("decode_fn", "syndrome_fn", "sample_fn",
                               "build_fn") if inj.get(key) is None]
    if missing:
        raise ValueError("adapters %s must be explicitly injected "
                         "(no decoder is bound without them)" % (missing,))
    if marginal is None:
        raise ValueError("marginal_32 must be supplied on the fake path "
                         "(production loads it from the frozen prior root)")
    decode_fn = inj["decode_fn"]
    syndrome_fn = inj["syndrome_fn"]
    sample_fn = inj["sample_fn"]
    build_fn = inj["build_fn"]
    now = now_fn or time.monotonic
    rss_fn = rss_fn or _peak_rss_bytes
    t0 = float(now())
    log_lines = []

    def log(message):
        line = _log_line(message)
        log_lines.append(line)
        print(line)

    setup_expected = DEFAULT_GRAPHS + (DEFAULT_GRAPHS if include_r72 else 0)
    graphs, graph_rows = {}, []
    for width in r23.WIDTHS:
        for ratio in _active_ratios(include_r72):
            key = RATIO_KEY[ratio]
            for graph_seed in r23.GRAPH_SEEDS[(width, key)]:
                start = float(now())
                graph = build_fn(int(width), key, int(graph_seed))
                graphs[(int(width), key, int(graph_seed))] = graph
                graph_rows.append(_graph_row(graph, float(now()) - start))
    admitted = sum(1 for row in graph_rows if row["admitted"])
    log("built %d graphs admitted=%d" % (len(graph_rows), admitted))
    build_violations = r23.check_build_budgets(graph_rows)
    if len(graph_rows) != setup_expected:
        raise RuntimeError("setup graph count %d != frozen %d"
                           % (len(graph_rows), setup_expected))
    blocks = {}
    for width in r23.WIDTHS:
        for ratio in _active_ratios(include_r72):
            key = RATIO_KEY[ratio]
            cell_blocks = {}
            for ordinal in _graph_ordinals(width, key):
                for block_seed in WEAK_BLOCK_SEEDS[(width, key, ordinal)]:
                    cell_blocks[int(block_seed)] = sample_fn(
                        int(width), key, int(block_seed))
            blocks[(int(width), key)] = cell_blocks
    log("sampled oracle-truth blocks count=%d (independent per graph)"
        % sum(len(v) for v in blocks.values()))

    outcome = execute_weak_plan(plan, graphs, blocks, marginal, decode_fn,
                                syndrome_fn, now=now, rss_fn=rss_fn)
    records = outcome["records"]
    engineering_reason = outcome["failure"]
    # Frozen-order identity gate: every dispatched record must match the
    # frozen plan entry at its position. Any deviation is a contract STOP.
    for pos, record in enumerate(records):
        entry = plan[pos]
        for key in ("width", "ratio", "graph_seed", "block_seed"):
            if str(record[key]) != str(entry[key]):
                raise RuntimeError(
                    "dispatch order violated at position %d: %r != %r"
                    % (pos, {k: record.get(k) for k in
                             ("width", "ratio", "block_seed")}, entry))
        record["call_idx"] = pos
    log("dispatched=%d" % len(records))

    cell_results = []
    for width in r23.WIDTHS:
        for ratio in _active_ratios(include_r72):
            key = RATIO_KEY[ratio]
            try:
                tally = weak_cell_tally(records, int(width), key)
            except ValueError as exc:
                if not engineering_reason:
                    engineering_reason = ("cell tally not rebuildable: %s"
                                          % exc)
                tally = {"width": int(width), "ratio": key,
                         "E_g": [0] * r23.GRAPHS_PER_CELL, "E": 0}
            cell_results.append({"width": int(width), "ratio": key,
                                 "tally": tally,
                                 "engineering_reason": engineering_reason})
    # Weak batch gate: terminal ONLY from the anchor cells (n1024@r65,
    # n128@r65), the gap, batch undetected and the calibration guard.
    # Per-cell tallies stay descriptive diagnostics.
    anchor = {"%d:%s" % (c["width"], c["ratio"]): c for c in cell_results}
    e_hi = int(anchor["1024:r65"]["tally"]["E"])
    e_lo = int(anchor["128:r65"]["tally"]["E"])
    undetected_total = sum(1 for rec in records if rec["undetected"])
    terminal = route_weak_gate(e_hi, e_lo, undetected_total,
                               engineering_reason)
    calibration_tripped = bool(e_lo > CAL_MAX_LO)
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn())
    budget_violations = list(build_violations)
    if len(records) > SCIENTIFIC_CALL_CEILING:
        budget_violations.append("scientific calls exceed ceiling")
    if wall_s > WALL_BUDGET_S:
        budget_violations.append("wall budget exceeded")
    if peak_rss >= r2.RSS_BUDGET_BYTES:
        budget_violations.append("RSS budget exceeded")
    log("terminal=%s" % terminal)

    manifest = {
        "schema": "v72p2r23b_weak_manifest_v1",
        "change_id": CHANGE_ID, "cycle": CYCLE_ID, "step": STEP,
        "claim_ceiling": CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "out_root": str(resolved),
        "batch_id": R23B_BATCH_ID,
        "field": {"q": r23.Q, "factory": "GF2mField.create(32)"},
        "arm": ARM,
        "channel": {"family": "q-ary-symmetric", "p": r23.P_ERR,
                    "oracle": "truth-conditioned U2 (truth blocks only)",
                    "prior_chain": "Model-F U2 population marginal, "
                                   "decoder-input-only"},
        "prior": {"root": FROZEN_PRIOR_ROOT,
                  "loader": "v72p2d5_model_f_input.load_model_f_input "
                            "(read-only, SAME path as R9)",
                  "marginal": "p_b folded over high bits to U2, "
                              "floor 1e-15, renormalized, tiled per block",
                  "decoder_input_only": True},
        "lambda_s": dict(r23.LAMBDA_S),
        "widths": list(r23.WIDTHS),
        "ratios": list(_active_ratios(include_r72)),
        "rows": {"%d:%s" % (w, RATIO_KEY[r]): r23.ROWS[(w, RATIO_KEY[r])]
                 for w in r23.WIDTHS for r in _active_ratios(include_r72)},
        "cells": _cell_table_meta(include_r72=include_r72),
        "graph_seeds": {"%d:%s" % (w, RATIO_KEY[r]):
                        list(r23.GRAPH_SEEDS[(w, RATIO_KEY[r])])
                        for w in r23.WIDTHS
                        for r in _active_ratios(include_r72)},
        "block_seeds": {"%d:%s:graph%d" % (w, RATIO_KEY[r], o):
                        list(WEAK_BLOCK_SEEDS[(w, RATIO_KEY[r], o)])
                        for w in r23.WIDTHS
                        for r in _active_ratios(include_r72)
                        for o in _graph_ordinals(w, RATIO_KEY[r])},
        "block_bias": "independent per graph (fresh seeds, never shared)",
        "coefficient_rule":
            "v10_seed(r23:scale:coeff:{width}:{ratio}:{graph_seed}) -> "
            "default_rng -> integers(1,32) per edge in sorted (variable, "
            "check) order (REUSED R23 graphs, rebuilt identically)",
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": DECODER_MAX_ITER,
                    "damping_alpha": DAMPING_ALPHA,
                    "warm_beliefs": None, "schedule": "cold single-pass",
                    "retry": False},
        "matrix": {"planned_calls": len(plan),
                   "shape": ("2 widths x %d ratio(s) x 2 graphs x "
                             "8 independent blocks, single arm W"
                             % len(_active_ratios(include_r72))),
                   "call_order": ("width ascending; ratio ascending; "
                                  "graphs ascending; blocks ascending"),
                   "admission": "setup-first binding (4/4 default, "
                                "8/8 extended) before any decoder binding"},
        "budgets": _budget_meta(),
        "setup_graphs": len(graph_rows),
        "calibration": {"anchor": "128:r65", "max_exact": CAL_MAX_LO,
                        "tripped": calibration_tripped},
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": AUTHORIZATION,
        "extension_authorization": EXTENSION_AUTHORIZATION,
        "conditional_r72": bool(include_r72),
        "predecessor_boundary": ("predecessor evidence is contextual only; "
                                 "the weak gate accepts only batch_id=%s "
                                 "non-oracle records with the weak "
                                 "provenance token" % R23B_BATCH_ID),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    cell_rows = _cell_rows(records, include_r72=include_r72)
    per_cell = {}
    for cell in cell_results:
        tally = cell["tally"]
        per_cell["%d:%s" % (cell["width"], cell["ratio"])] = {
            "E": int(tally["E"]),
            "E_g": [int(v) for v in tally["E_g"]],
            "exact_frac": "%d/16" % int(tally["E"]),
            "descriptive_only": True,
            "engineering_reason": cell["engineering_reason"]}
    summary = {
        "schema": "v72p2r23b_weak_summary_v1",
        "change_id": CHANGE_ID, "cycle": CYCLE_ID, "step": STEP,
        "claim_ceiling": CLAIM_CEILING,
        "terminal": terminal,
        "per_cell": per_cell,
        "calibration": {"e_lo_128_r65": e_lo, "max_allowed": CAL_MAX_LO,
                        "tripped": calibration_tripped,
                        "reason": CALIBRATION_STOP_REASON
                        if calibration_tripped else ""},
        "scientific_calls": len(records),
        "planned_calls": len(plan),
        "setup_graphs": len(graph_rows),
        "exact_count": sum(1 for rec in records if rec["exact"]),
        "syndrome_valid_count": sum(1 for rec in records
                                    if rec["syndrome_ok"]),
        "undetected_count": sum(1 for rec in records
                                if rec["undetected"]),
        "call_idx_first": 0 if records else None,
        "call_idx_last": len(records) - 1 if records else None,
        "wall_s": wall_s, "peak_rss_bytes": peak_rss,
        "budget_violations": budget_violations,
        "batch_id": R23B_BATCH_ID,
        "conditional_r72": bool(include_r72),
        "out_root": str(resolved), "budgets": _budget_meta(),
    }
    log_lines.append(_log_line(
        "R23b terminal=%s calls=%d setup=%d wall_s=%.3f"
        % (terminal, len(records), len(graph_rows), wall_s)))
    return {
        "resolved": resolved,
        "manifest": manifest,
        "records": records,
        "graph_rows": graph_rows,
        "cell_rows": cell_rows,
        "summary": summary,
        "log_lines": log_lines,
    }


# --------------------------------------------------------------------------- #
# Never-overwrite writer (one mkdir + six files; no computation)
# --------------------------------------------------------------------------- #
def write_batch_root(bundle):
    """Persist one orchestrator bundle to its fresh root (never overwrite).

    Creates the probed-fresh directory and writes exactly the six frozen
    evidence files. An existing root raises ``FileExistsError`` here as
    well as at the orchestrator probe — nothing is ever overwritten.
    """
    resolved = bundle["resolved"]
    resolved.mkdir(parents=True)
    _write_json(resolved / "manifest.json", bundle["manifest"])
    _write_csv(resolved / "decoder_records.csv",
               DECODER_RECORD_COLUMNS, bundle["records"])
    _write_csv(resolved / "graph_records.csv", GRAPH_RECORD_COLUMNS,
               bundle["graph_rows"])
    _write_csv(resolved / "cell_summary.csv", CELL_SUMMARY_COLUMNS,
               bundle["cell_rows"])
    _write_json(resolved / "summary.json", bundle["summary"])
    with open(resolved / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("".join(line + "\n" for line in bundle["log_lines"]))
    return bundle["summary"]


# --------------------------------------------------------------------------- #
# verify (read-only; zero decoder calls; zero skip; fail-closed)
# --------------------------------------------------------------------------- #
def verify_root(out_root, build_fn=None):
    """Recompute a completed weak root from its evidence; fail-closed."""
    root = Path(out_root)
    build_fn = build_fn or r23.build_graph
    violations: list = []
    if not root.is_dir():
        print("VERIFY root missing: %s" % root)
        return False
    names = sorted(p.name for p in root.iterdir())
    if names != sorted(EVIDENCE_FILES):
        print("VERIFY evidence files mismatch: %s" % names)
        return False
    manifest = json.loads((root / "manifest.json").read_text("utf-8"))
    summary = json.loads((root / "summary.json").read_text("utf-8"))
    graph_rows = _read_csv(root / "graph_records.csv")
    decoder_rows = _read_csv(root / "decoder_records.csv")
    cell_rows = _read_csv(root / "cell_summary.csv")

    if manifest.get("batch_id") != R23B_BATCH_ID \
            or summary.get("batch_id") != R23B_BATCH_ID:
        violations.append("batch_id tag mismatch (predecessor boundary)")
    include_r72 = bool(manifest.get("conditional_r72", False))
    planned = DEFAULT_CALLS + (DEFAULT_CALLS if include_r72 else 0)
    setup_expected = DEFAULT_GRAPHS + (DEFAULT_GRAPHS if include_r72 else 0)

    plan = build_weak_plan(include_r72=include_r72)
    plan_by_idx = {e["call_idx"]: e for e in plan}
    records: list = []
    for index, row in enumerate(decoder_rows):
        entry = plan_by_idx.get(index)
        problems: list = []
        if entry is None:
            violations.append("decoder row %d beyond frozen plan" % index)
            continue
        if _as_int(row["call_idx"]) != index:
            violations.append("decoder row %d call_idx %s != planned %d"
                              % (index, row["call_idx"], index))
        for key in ("width", "ratio", "graph_seed", "block_seed"):
            if str(row[key]) != str(entry[key]):
                violations.append("decoder row %d %s %r != planned %r"
                                  % (index, key, row[key], entry[key]))
        if row.get("batch_id") != R23B_BATCH_ID:
            violations.append("decoder row %d batch_id tag missing" % index)
        if int(row["disclosed_bits"]) != r23.disclosed_bits(
                _as_int(row["m"])):
            violations.append("decoder row %d disclosed != 5m" % index)
        if row.get("arm") != ARM:
            violations.append("decoder row %d arm != frozen W" % index)
        exact = _as_bool(row["exact"])
        syndrome_ok = _as_bool(row["syndrome_ok"])
        undetected = _as_bool(row["undetected"])
        oracle = _as_bool(row["oracle"])
        graded = _as_bool(row["graded"])
        iterations = _as_int(row["iterations"])
        residual = _as_int(row["residual_syndrome_weight"])
        weight = _as_int(row["oracle_weight"])
        wall = _as_float(row["wall_s"])
        crash = _as_bool(row["crash"])
        width = _as_int(row["width"])
        # Metric isolation: exact never without syndrome_ok; undetected
        # never merged into exact; every row is non-oracle with the exact
        # weak provenance token (any ORACLE token fails closed).
        if exact and not syndrome_ok:
            problems.append("exact without syndrome_ok (metric isolation)")
        if undetected and exact:
            problems.append("undetected merged into exact")
        if oracle:
            problems.append("weak row must be non-oracle")
        if graded:
            problems.append("weak row must be ungraded diagnostic")
        if str(row["belief_provenance"]).strip() != WEAK_PROVENANCE:
            problems.append("weak provenance token != %r"
                            % (WEAK_PROVENANCE,))
        if "ORACLE" in str(row["belief_provenance"]).upper():
            problems.append("ORACLE token on weak decode path")
        if not 0 <= weight <= width:
            problems.append("oracle truth weight outside 0..n: %d" % weight)
        if crash:
            if iterations != -1 or residual != -1 or exact or syndrome_ok \
                    or undetected:
                problems.append("crash record inconsistent")
        else:
            if not 0 <= iterations <= DECODER_MAX_ITER:
                problems.append("iterations out of range: %d" % iterations)
            if residual < 0:
                problems.append("residual weight missing")
        if str(row["status"]).strip() in ("",):
            problems.append("empty status")
        if wall < 0.0 or wall > PER_CALL_BUDGET_S:
            problems.append("per-call wall out of budget: %s"
                            % row["wall_s"])
        for problem in problems:
            violations.append("decoder row %d %s" % (index, problem))
        records.append({"call_idx": index, "width": width,
                        "ratio": row["ratio"],
                        "graph_seed": _as_int(row["graph_seed"]),
                        "block_seed": _as_int(row["block_seed"]),
                        "batch_id": row.get("batch_id"),
                        "exact": exact, "syndrome_ok": syndrome_ok,
                        "undetected": undetected, "oracle": oracle,
                        "graded": graded,
                        "belief_provenance": row.get("belief_provenance"),
                        "crash": crash, "wall_s": wall})

    # Zero-skip: a complete root carries exactly the planned calls.
    if len(decoder_rows) != planned:
        violations.append("stored calls %d != frozen %d (zero-skip)"
                          % (len(decoder_rows), planned))

    # Independent blocks per cell: each graph carries its own frozen 8,
    # and the two groups are disjoint.
    for width in r23.WIDTHS:
        for ratio in _active_ratios(include_r72):
            key = RATIO_KEY[ratio]
            groups = []
            for ordinal, seed in enumerate(r23.GRAPH_SEEDS[(width, key)]):
                got = sorted(rec["block_seed"] for rec in records
                             if rec["width"] == width
                             and rec["ratio"] == key
                             and rec["graph_seed"] == int(seed))
                want = sorted(int(s) for s in
                              WEAK_BLOCK_SEEDS[(width, key, ordinal)])
                if got != want:
                    violations.append("cell %d:%s graph %d blocks %s "
                                      "!= frozen independent 8"
                                      % (width, key, int(seed), got))
                groups.append(set(got))
            if len(groups) == 2 and not groups[0].isdisjoint(groups[1]):
                violations.append("cell %d:%s graphs share blocks "
                                  "(independence)" % (width, key))

    recomputed_cell_rows = _cell_rows(records, include_r72=include_r72)
    stored_keys = {(row["width"], row["ratio"], row["scope"],
                    row["graph_ordinal"]): row for row in cell_rows}
    for row in recomputed_cell_rows:
        key = (str(row["width"]), row["ratio"], row["scope"],
               str(row["graph_ordinal"]))
        stored = stored_keys.get(key)
        if stored is None:
            violations.append("cell_summary row missing: %s" % (key,))
            continue
        for column in ("blocks", "exact_count", "syndrome_valid_count",
                       "undetected_count"):
            if _as_int(stored[column]) != int(row[column]):
                violations.append("cell_summary %s %s stored=%s recomputed=%d"
                                  % (key, column, stored[column],
                                     int(row[column])))

    # Gate recompute: descriptive per-cell tallies + calibration guard +
    # frozen anchor rule.
    recomputed_E = {}
    for width in r23.WIDTHS:
        for ratio in _active_ratios(include_r72):
            key = RATIO_KEY[ratio]
            stored_cell = summary.get("per_cell", {}).get(
                "%d:%s" % (width, key), {})
            try:
                tally = weak_cell_tally(records, int(width), key)
            except ValueError as exc:
                violations.append("cell %d:%s tally not rebuildable: %s"
                                  % (width, key, exc))
                continue
            if int(stored_cell.get("E", -1)) != int(tally["E"]):
                violations.append("stored %d:%s E != recomputed"
                                  % (width, key))
            if [int(v) for v in stored_cell.get("E_g", [])] != \
                    [int(v) for v in tally["E_g"]]:
                violations.append("stored %d:%s E_g != recomputed"
                                  % (width, key))
            recomputed_E["%d:%s" % (width, key)] = int(tally["E"])
    stored_hi = summary.get("per_cell", {}).get("1024:r65", {})
    stored_lo = summary.get("per_cell", {}).get("128:r65", {})
    recomputed_undetected = sum(1 for rec in records if rec["undetected"])
    engineering = stored_hi.get("engineering_reason", "") or \
        stored_lo.get("engineering_reason", "")
    if "1024:r65" not in recomputed_E or "128:r65" not in recomputed_E:
        violations.append("anchor cells missing for gate recompute")
    elif route_weak_gate(recomputed_E["1024:r65"],
                         recomputed_E["128:r65"],
                         recomputed_undetected,
                         engineering) != summary.get("terminal"):
        violations.append("terminal stored=%r recomputed mismatch"
                          % (summary.get("terminal"),))
    stored_cal = summary.get("calibration", {})
    if int(stored_cal.get("e_lo_128_r65", -1)) != recomputed_E.get(
            "128:r65", -1):
        violations.append("calibration cell stored != recomputed")
    if bool(stored_cal.get("tripped", False)) != \
            (recomputed_E.get("128:r65", 0) > CAL_MAX_LO):
        violations.append("calibration trip stored != recomputed")
    if any(c.get("engineering_reason")
           for c in summary.get("per_cell", {}).values()):
        violations.append("engineering-blocked root (fail-closed)")
    if len(decoder_rows) != int(summary.get("scientific_calls", -1)):
        violations.append("stored calls %d != summary %r"
                          % (len(decoder_rows),
                             summary.get("scientific_calls")))
    if len(decoder_rows) > SCIENTIFIC_CALL_CEILING:
        violations.append("stored calls exceed scientific ceiling")
    if int(summary.get("setup_graphs", -1)) != setup_expected:
        violations.append("setup graphs != frozen %d: %r"
                          % (setup_expected, summary.get("setup_graphs")))
    if _as_float(summary.get("wall_s", -1.0)) > WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if _as_int(summary.get("peak_rss_bytes", -1)) \
            >= r2.RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")
    max_call_wall = max((rec["wall_s"] for rec in records), default=0.0)
    if max_call_wall > PER_CALL_BUDGET_S:
        violations.append("per-call wall exceeds budget: %s" % max_call_wall)

    # Reviewer-mandated repair (option b, PASS-WITH-REWORK): the R23
    # production builder stamps reused graphs with arm 'S' per the frozen
    # REUSE design (W-graphs REUSE the R23 12 identically), so demanding
    # arm == 'W' here FAILs valid production evidence. Widen the
    # GRAPH-ROW predicate ONLY to also accept the R23-builder 'S' stamp
    # where (width, ratio, seed) is in the frozen r23.GRAPH_SEEDS set
    # (n128 4801/4802 + n1024 4811/4812 at r65, plus the frozen r72/r78
    # pairs from the R23 manifest — membership test below is the exact
    # frozen set, unknown seeds/widths/arms still fail closed). DECODER
    # rows still require arm 'W' + batch r23b-weak-w-v1 + WEAK token +
    # non-oracle (strict, unchanged).
    for row in graph_rows:
        seed = _as_int(row["graph_seed"])
        width = _as_int(row["width"])
        ratio = row["ratio"]
        if row["arm"] not in (ARM, r23.ARM) \
                or width not in r23.WIDTHS \
                or (width, ratio) not in r23.GRAPH_SEEDS \
                or seed not in r23.GRAPH_SEEDS[(width, ratio)]:
            violations.append("graph arm/width/ratio/seed outside weak "
                              "cells: %r" % ((row["arm"], row["width"],
                                              ratio, row["graph_seed"]),))
            continue
        graph = build_fn(width, ratio, seed)
        key = (width, ratio, row["graph_seed"])
        if graph["status"] != row["status"] \
                or bool(graph["admitted"]) != _as_bool(row["admitted"]) \
                or int(graph["E"]) != _as_int(row["E"]) \
                or str(graph["failure_reason"]) != row["failure_reason"]:
            violations.append("graph %s status/admission/E mismatch" % (key,))
            continue
        if str(row["status"]) != "ok" or not _as_bool(row["admitted"]):
            violations.append("graph %s not admitted (fail-closed)" % (key,))
            continue
        structure = graph.get("structure")
        if structure and _cell(row.get("admission")):
            recomputed_admission = json.dumps(structure["admission"],
                                              sort_keys=True)
            if _cell(row.get("admission")) != recomputed_admission:
                violations.append("graph %s admission stored != recomputed"
                                  % (key,))
    if len(graph_rows) != setup_expected:
        violations.append("graph rows %d != %d built objects"
                          % (len(graph_rows), setup_expected))
    build_violations = r23.check_build_budgets(graph_rows)
    violations.extend("build sub-cap: %s" % v for v in build_violations)

    print("VERIFY checked_calls=%d violations=%d"
          % (len(decoder_rows), len(violations)))
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    ok = not violations
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return ok


# --------------------------------------------------------------------------- #
# CLI (default-false batch refusal before write/bind/build)
# --------------------------------------------------------------------------- #
def build_parser():
    parser = argparse.ArgumentParser(
        description="R23b weak-prior retest runner (readiness)")
    parser.add_argument("--weak-batch", action="store_true",
                        help="run the frozen weak matrix (requires "
                             "--execution-authorized from a separate "
                             "explicit authorization)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for "
                             "--weak-batch; default false "
                             "(fail-closed, no-write/no-bind)")
    parser.add_argument("--include-r72", action="store_true",
                        default=False,
                        help="conditional 0.72 arm (default off; requires "
                             "--extension-authorized, no auto-run)")
    parser.add_argument("--extension-authorized", action="store_true",
                        default=False,
                        help="explicit second authorization for "
                             "--include-r72; default false")
    parser.add_argument("--prior-root", default=FROZEN_PRIOR_ROOT,
                        help="Model-F prior root (must equal the frozen "
                             "R9 path)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--profile-only", action="store_true",
                        help="frozen plan + budget dry-run (no decoder, "
                             "no graph builds, no root)")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    return parser


def profile_only():
    """Dry-run profile: frozen plan + D9 geometry + budgets, nothing else."""
    plan = build_weak_plan(include_r72=False)
    _validate_weak_plan(plan, include_r72=False)
    future = Path(FUTURE_ROOT)
    resolved = future.resolve() if future.is_absolute() \
        else (ROOT / future).resolve()
    cells = []
    for width in r23.WIDTHS:
        for ratio in RATIOS_DEFAULT:
            key = RATIO_KEY[ratio]
            cell = r23.degree_cell(width, key)
            n_graphs = len(r23.GRAPH_SEEDS[(width, key)])
            n_blocks = len(WEAK_BLOCK_SEEDS[(width, key, 0)])
            cells.append({
                "width": width, "ratio": key, "n": cell["n"], "m": cell["m"],
                "E": cell["E"], "rate": cell["rate"],
                "disclosed_bits": cell["disclosed_bits"],
                "graphs": n_graphs,
                "blocks_per_graph": n_blocks,
                "independent_blocks": True,
                "calls": n_graphs * n_blocks})
    return {
        "cells": cells,
        "plan_calls": len(plan),
        "per_cell_calls": CELL_TRIALS,
        "conditional_r72": False,
        "extended_plan_calls": len(build_weak_plan(include_r72=True)),
        "budgets": _budget_meta(),
        "prior_root": FROZEN_PRIOR_ROOT,
        "calibration": {"anchor": "%d:%s" % CAL_ANCHOR,
                        "max_exact": CAL_MAX_LO},
        "future_root": str(resolved),
        "future_root_absent": not resolved.exists(),
        "decoder_calls": 0,
        "graph_builds": 0,
    }


def main(argv=None, *, adapters_override=None, marginal_override=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--weak-batch", args.weak_batch),
                                        ("--verify", args.verify),
                                        ("--profile-only",
                                         args.profile_only)) if flag]
    if len(selected) != 1:
        parser.error("exactly one of --weak-batch, --verify or "
                     "--profile-only is required")
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
        return 0
    # Refuse --weak-batch before root creation and before any prior load,
    # decoder binding or graph build while --execution-authorized is false.
    if args.weak_batch and not args.execution_authorized:
        print("refusing --weak-batch: %s (pass --execution-authorized only "
              "under a separate explicit authorization)"
              % AUTHORIZATION, file=sys.stderr)
        return 2
    # The conditional 0.72 arm needs its own second grant; default off.
    if args.include_r72 and not args.extension_authorized:
        print("refusing --include-r72: %s (pass --extension-authorized "
              "only under a separate explicit authorization)"
              % EXTENSION_AUTHORIZATION, file=sys.stderr)
        return 2
    if args.out_root is None:
        parser.error("%s requires --out-root" % selected[0])
    if args.verify:
        return 0 if verify_root(args.out_root) else 1
    # Authorized true branch: exactly one batch-orchestrator call plus one
    # never-overwrite writer. adapters_override/marginal_override carry
    # test-machinery fakes only; None production-binds inside the
    # orchestrator, after plan validation.
    bundle = run_authorized_batch(
        args.out_root, adapters=adapters_override,
        marginal_32=marginal_override, prior_root=args.prior_root,
        include_r72=args.include_r72,
        extension_authorized=args.extension_authorized)
    summary = write_batch_root(bundle)
    print("R23b terminal=%s calls=%d setup=%d"
          % (summary["terminal"], summary["scientific_calls"],
             summary["setup_graphs"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
