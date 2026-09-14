"""V72P2D14N calibrated L1/L2 discriminator — readiness plan/graphs/gates.

Change: ``v72p2d14n-calibrated-l1-l2-discriminator``
Frozen authority: ``.workbuddy/tasks/D14N_CALIBRATED_DISCRIMINATOR_IMPLEMENTATION_R1_TASK_PACKET.md``
(§2 as amended) + ``openspec/changes/v72p2d14n-calibrated-l1-l2-discriminator/``
(design incl. §8 Freeze Amendment A1, delta spec, tasks N202–N205) +
``docs/research_cycles/D14_VALIDITY_RESET/N_DISCRIMINATOR_PREREG_R1.md``
(retained original; A1 supersedes ONLY the L1 check-allocation cells and the
setup count). Track: implementation/readiness (zero production/scientific
decoder calls; no N batch, no D7-H, no real data, no commit/push).

Amended freeze (implement EXACTLY; STOP on any further drift):

- n=128 only; L1 m=110; L045 var 71/57 E313 checks ``2^17+3^93``; L055 var
  83/45 E301 checks ``2^29+3^81`` (D9-rule recompute; supersedes the m=118
  strings ``2^41+3^77`` / ``2^53+3^65``); L2 DV3 m=104 E=384 ``3^32+4^72``.
- Seeds L1 ``2026093401..06`` / L2 ``2026093501..06`` / blocks
  ``2026093601..12``; 6 paired graphs x 12 blocks = 72 cells; 72 each
  L045/L055/L2-APP/L2-ORACLE = 288; 18 built objects / 12 seeds; setup ≤32.

Reuse contract (IMPORT — no duplication of construction/admission semantics):

- shared connectivity-first constructor: ``r2.build_degree_sequence_peg``;
- binding admission A1–A5: ``r2.structural_record`` (A6 replay mirrors the
  accepted ``r2.build_graph``/D11 ``build_l2_graph`` composition, applied to
  the frozen N cells — never to a predecessor cell);
- L1 decoder path: ``r2.dispatch_l1`` (shared reference; admission gate
  before binding plus exact/syndrome semantics);
- coefficient rule: ``r2.coefficient_seed`` / ``r2.coefficients_for_edges``
  (``v10_seed`` of ``d10:coeff:{width}:{graph_seed}``);
- provenance token/guard: ``v35.BELIEF_PROVENANCE_CHECK_UPDATED`` /
  ``v35.require_check_updated_provenance`` (lazy bind; this module never
  imports the production decoder at top level);
- decoder contract constants (``max_iter=90``, ``damping_alpha=1.0``), field
  (``q=32, poly=37``), Model-F root, RSS budget and ``refuse_out_root``.

Added here (N deltas only): the amended L1 cells, fresh N seeds, the
288-record four-arm plan, the N gate predicates plus six terminals with exact
priority, the source-agnostic L2 dispatch skeleton (transfer/oracle priors
are explicit injections; see ``run_l2_app_cell``), and the 18-object
pre-decoder profile. There is no replacement-seed mechanism anywhere in this
module: admission failure blocks with no seed change. This module never
imports the production decoder and never loads Model-F content.
"""
from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from typing import Any

from . import v72p2d10_mixed_degree_l1 as r2
from . import v72p2d10_r3_fresh_scaling as r3
from . import v72p2d11_forward_app as d11
from . import v72p2d12_finite_l1_degree as d12

__all__ = [
    "CHANGE_ID", "CYCLE_ID", "TRACK", "CLAIM_CEILING",
    "N", "M_L1", "M_L2", "ARMS", "L1_PROFILES", "L2_ARM", "ORACLE_ARM",
    "LAMBDA2", "DEGREE_TABLE", "L1_GRAPH_SEEDS", "L2_GRAPH_SEEDS",
    "BLOCK_SEEDS", "H_L1", "ENTROPY_LOAD_BITS", "DISCLOSED_BITS",
    "EFFECTIVE_FACTOR", "Q", "POLY", "DECODER_MAX_ITER", "DAMPING_ALPHA",
    "MODEL_F_INPUT_ROOT", "PRIOR_CHAIN", "SCIENTIFIC_CALL_CEILING",
    "SETUP_CALL_CEILING", "SETUP_FIXED_UNITS", "WALL_BUDGET_S",
    "PER_CALL_BUDGET_S", "RSS_BUDGET_BYTES", "L1_MIN_EXACT",
    "L1_GRAPHS_GE2_MIN", "ORACLE_MIN", "JOINT_MIN",
    "T_L1_CONSTRUCTION", "T_L2_DEGREE", "T_TRANSFER_BOTTLENECK",
    "T_SCALE_VALIDATION", "T_AMBIGUOUS", "T_ENGINEERING_BLOCKED",
    "TERMINALS", "EVIDENCE_FILES", "FUTURE_ROOT", "FROZEN_COMMAND",
    "AUTHORIZATION", "N14_BATCH_ID", "ProvenanceRefused",
    "StructureNotAdmitted",
    "dispatch_l1", "coefficient_seed", "refuse_out_root",
    "check_updated_token", "require_check_updated",
    "degree_cell", "build_l1_graph", "build_l2_graph",
    "build_call_plan", "N14Tallies", "tallies_from_n14_records",
    "is_l1_adequate", "is_oracle_adequate", "is_l2_joint_good",
    "describe_paired_l1", "route_terminal",
    "run_l2_app_cell", "run_l2_oracle_cell", "execute_plan",
    "profile_graphs",
]

# --------------------------------------------------------------------------- #
# Frozen identifiers (packet §2 as amended; design §8; spec normative)
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2d14n-calibrated-l1-l2-discriminator"
CYCLE_ID = "V72P2D14N-CALIBRATED-DISCRIMINATOR"
TRACK = "implementation/readiness"
CLAIM_CEILING = (
    "synthetic diagnostic only; routes the next investment (L1 construction "
    "vs L2 degree design); no FER, leakage, SKR, real-data, qualification, "
    "promotion, optimality, route-closure or D7-H claim; grants no execution"
)

N = 128
M_L1 = 110
M_L2 = 104

ARMS = ("L045", "L055", "L2_APP", "L2_ORACLE")
L1_PROFILES = ("L045", "L055")
L2_ARM = "L2_APP"
ORACLE_ARM = "L2_ORACLE"
LAMBDA2 = {"L045": 0.45, "L055": 0.55}

#: Amended degree cells (A1: variable counts STAND; check allocations
#: re-derived at m=110 via the frozen D9 floor/ceil rule).
DEGREE_TABLE = {
    "L045": {"n": 128, "m": 110, "var_counts": {2: 71, 3: 57},
             "check_counts": {2: 17, 3: 93}},
    "L055": {"n": 128, "m": 110, "var_counts": {2: 83, 3: 45},
             "check_counts": {2: 29, 3: 81}},
    "L2": {"n": 128, "m": 104, "var_counts": {3: 128},
           "check_counts": {3: 32, 4: 72}},
}

#: Fresh seeds (frozen; never searched or replaced).
L1_GRAPH_SEEDS = tuple(range(2026093401, 2026093407))
L2_GRAPH_SEEDS = tuple(range(2026093501, 2026093507))
BLOCK_SEEDS = tuple(range(2026093601, 2026093613))

#: Rate math (stated, never recomputed; provenance ``entropy.json``).
H_L1 = 4.286720430201375
ENTROPY_LOAD_BITS = 548.700215065776
DISCLOSED_BITS = 550
EFFECTIVE_FACTOR = 1.00237

#: Decoder/field/prior contract reused from R2/D5 (no re-declaration).
Q = r2.Q
POLY = r2.POLY
DECODER_MAX_ITER = r2.DECODER_MAX_ITER
DAMPING_ALPHA = r2.DAMPING_ALPHA
MODEL_F_INPUT_ROOT = r2.MODEL_F_INPUT_ROOT
PRIOR_CHAIN = "candidate_concentration_backoff"

#: Shared L1 decoder binding, coefficient rule and root refusal (import).
dispatch_l1 = r2.dispatch_l1
coefficient_seed = r2.coefficient_seed
refuse_out_root = r2.refuse_out_root
StructureNotAdmitted = r2.StructureNotAdmitted


class ProvenanceRefused(Exception):
    """Non-oracle transfer without ``CHECK_UPDATED`` provenance (fail-closed)."""


def check_updated_token() -> str:
    """Canonical ``CHECK_UPDATED`` token (lazy v35 bind; no decoder bind)."""
    from . import v35_algorithm_development as v35

    return v35.BELIEF_PROVENANCE_CHECK_UPDATED


def require_check_updated(provenance: str, consumer: str = "n14-l2-app") -> str:
    """Fail-closed provenance guard via the accepted v35 predicate."""
    from . import v35_algorithm_development as v35

    try:
        v35.require_check_updated_provenance(provenance, consumer=consumer)
    except Exception as exc:
        raise ProvenanceRefused(
            "refusing non-oracle transfer for %s: provenance %r is not "
            "CHECK_UPDATED" % (consumer, provenance)) from exc
    return str(provenance)


#: Budgets (amended: ≤288 scientific; ≤32 setup = 18 constructions + 12
#: block samples + 2 fixed plan/manifest; wall ≤1800 s; ≤120 s/call).
SCIENTIFIC_CALL_CEILING = 288
SETUP_CALL_CEILING = 32
SETUP_FIXED_UNITS = 2  # plan build + manifest
WALL_BUDGET_S = 1800.0
PER_CALL_BUDGET_S = 120.0
RSS_BUDGET_BYTES = r2.RSS_BUDGET_BYTES

#: Gate thresholds (prereg §7 verbatim).
L1_MIN_EXACT = 18
L1_GRAPHS_GE2_MIN = 5
ORACLE_MIN = 18
JOINT_MIN = 9

#: Six routing terminals (prereg §7 verbatim labels; first match wins).
T_L1_CONSTRUCTION = "N_ROUTE_L1_CONSTRUCTION"
T_L2_DEGREE = "N_ROUTE_L2_DEGREE"
T_TRANSFER_BOTTLENECK = "N_TRANSFER_BOTTLENECK_RECORDED"
T_SCALE_VALIDATION = "N_ROUTE_SCALE_VALIDATION"
T_AMBIGUOUS = "N_ROUTE_AMBIGUOUS"
T_ENGINEERING_BLOCKED = "N_ROUTE_BLOCKED_ENGINEERING"
TERMINALS = (T_ENGINEERING_BLOCKED, T_L1_CONSTRUCTION, T_L2_DEGREE,
             T_TRANSFER_BOTTLENECK, T_SCALE_VALIDATION, T_AMBIGUOUS)

FUTURE_ROOT = "workspace/v72p2d14_discriminator/20260914_r1"
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d14_discriminator_development.py "
    "--n14-batch --model-f-root %s --out-root %s"
    % (MODEL_F_INPUT_ROOT, FUTURE_ROOT)
)
AUTHORIZATION = (
    "separate explicit user/main-thread authorization required before "
    "--n14-batch")

EVIDENCE_FILES = ("manifest.json", "decoder_records.csv",
                  "graph_records.csv", "arm_summary.csv", "summary.json",
                  "command_log.txt")

#: Scope tag carried by every N decoder record. The gate constructor only
#: accepts records carrying this tag, so predecessor evidence (different
#: roots, schemas, seeds and no N batch tag) cannot enter the N gate.
N14_BATCH_ID = "d14-discriminator-v1"

#: Fresh-range guard: N seeds are disjoint from every prior seed set
#: (R2/R3 graphs+blocks, D11 L1/L2 graphs+blocks, D12 graphs+blocks).
_PRIOR_SEEDS = (
    {s for seeds in r2.GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in r2.BLOCK_SEEDS.values() for s in seeds}
    | {s for seeds in r3.GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in r3.BLOCK_SEEDS.values() for s in seeds}
    | {s for seeds in d11.L1_GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in d11.L1_BLOCK_SEEDS.values() for s in seeds}
    | {s for seeds in d11.L2_GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in d12.GRAPH_SEEDS.values() for s in seeds}
    | {s for seeds in d12.BLOCK_SEEDS.values() for s in seeds})
_N_L1 = set(L1_GRAPH_SEEDS)
_N_L2 = set(L2_GRAPH_SEEDS)
_N_BLOCK = set(BLOCK_SEEDS)
if len(_N_L1) != 6 or len(_N_L2) != 6 or len(_N_BLOCK) != 12:
    raise ValueError("N frozen seed sets have wrong cardinality")
if not _N_L1.isdisjoint(_N_L2) or not _N_L1.isdisjoint(_N_BLOCK) \
        or not _N_L2.isdisjoint(_N_BLOCK):
    raise ValueError("N graph/block seeds overlap")
if not _N_L1.isdisjoint(_PRIOR_SEEDS) \
        or not _N_L2.isdisjoint(_PRIOR_SEEDS) \
        or not _N_BLOCK.isdisjoint(_PRIOR_SEEDS):
    raise ValueError("N seed collides with a prior seed")
del _PRIOR_SEEDS, _N_L1, _N_L2, _N_BLOCK


# --------------------------------------------------------------------------- #
# Degree cells and graph construction (R2 path reused, never duplicated)
# --------------------------------------------------------------------------- #
def degree_cell(profile: str) -> dict[str, Any]:
    """Return the frozen N ``(n, m, var_counts, check_counts, E)`` cell."""
    key = str(profile)
    if key not in DEGREE_TABLE:
        raise KeyError("unknown N profile %r" % (key,))
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


def _compose_graph(cell: Mapping[str, Any], graph_seed: int,
                   arm_label: str) -> dict[str, Any]:
    """One construction path: accepted PEG + coefficients + A1–A6 admission.

    Shared by both arm families; only the frozen cell (and hence the forced
    degree/socket profile) differs. Any failure is retained with
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


def build_l1_graph(profile: str, graph_seed: int) -> dict[str, Any]:
    """Build one frozen N L1 graph (L045 control or L055 challenger)."""
    cell = degree_cell(str(profile))  # scope guard; raises outside N cells
    if str(profile) not in L1_PROFILES:
        raise KeyError("unknown N L1 profile %r" % (profile,))
    if int(graph_seed) not in L1_GRAPH_SEEDS:
        raise ValueError("graph seed %r outside frozen N L1 set"
                         % (graph_seed,))
    return _compose_graph(cell, int(graph_seed), str(profile))


def build_l2_graph(graph_seed: int) -> dict[str, Any]:
    """Build one shared frozen N DV3 L2 graph (APP + ORACLE share it)."""
    if int(graph_seed) not in L2_GRAPH_SEEDS:
        raise ValueError("graph seed %r outside frozen N L2 set"
                         % (graph_seed,))
    return _compose_graph(degree_cell("L2"), int(graph_seed), "L2")


# --------------------------------------------------------------------------- #
# Plan: exact call identities (deterministic 288-record plan, N202)
# --------------------------------------------------------------------------- #
def build_call_plan() -> list[dict[str, Any]]:
    """Frozen paired call matrix: 4 arms x 6 pairs x 12 blocks = 288 calls.

    Pair ``i`` (1..6) binds L1 seed ``L1_GRAPH_SEEDS[i-1]`` with L2 seed
    ``L2_GRAPH_SEEDS[i-1]``; the same 12 block seeds feed all four arms, so
    every ``(pair, block)`` cell carries one L045, one L055, one L2-APP and
    one L2-ORACLE identity. Order: L045, L055, L2-APP, L2-ORACLE; pairs
    ascending; blocks ascending; ``call_idx`` contiguous 0..287. Built
    before any decoder binding or Model-F load.
    """
    plan: list[dict[str, Any]] = []
    for arm in ARMS:
        for pair_idx, (l1_seed, l2_seed) in enumerate(
                zip(L1_GRAPH_SEEDS, L2_GRAPH_SEEDS), start=1):
            for block_seed in BLOCK_SEEDS:
                plan.append({
                    "call_idx": len(plan), "arm": arm,
                    "pair_idx": int(pair_idx),
                    "l1_graph_seed": int(l1_seed),
                    "l2_graph_seed": int(l2_seed),
                    "block_seed": int(block_seed)})
    return plan


# --------------------------------------------------------------------------- #
# Gate arithmetic with a structural predecessor boundary
# --------------------------------------------------------------------------- #
class N14Tallies:
    """Exact-count tallies for the N gate (L055 / oracle / APP-joint only).

    Only exact counts enter the gate; syndrome-valid counts are carried
    separately by the records and never substitute for exact. L045 pooled
    exact and paired discordances are descriptive only and cannot reach
    this object. Instances can only be built from ``N14_BATCH_ID``-tagged
    N decoder records (see ``tallies_from_n14_records``).
    """

    def __init__(self, l045_exact: Sequence[int],
                 l055_exact: Sequence[int],
                 app_joint: Sequence[int], oracle_pool: int) -> None:
        vectors = {}
        for name, vec in (("L045", l045_exact), ("L055", l055_exact),
                          ("L2_APP", app_joint)):
            vec = tuple(int(v) for v in vec)
            if len(vec) != 6:
                raise ValueError("N tallies require exactly 6 pairs per arm")
            if any(v < 0 or v > 12 for v in vec):
                raise ValueError("per-pair exact counts must lie in 0..12")
            vectors[name] = vec
        oracle_pool = int(oracle_pool)
        if not 0 <= oracle_pool <= 72:
            raise ValueError("oracle pool must lie in 0..72")
        self.l045_exact = vectors["L045"]
        self.l055_exact = vectors["L055"]
        self.app_joint = vectors["L2_APP"]
        self.oracle_pool = oracle_pool

    def pool(self, arm: str) -> int:
        """Exact pool for one graded arm (72 paired cells)."""
        if str(arm) == ORACLE_ARM:
            return int(self.oracle_pool)
        if str(arm) == L2_ARM:
            return sum(self.app_joint)
        return sum({"L045": self.l045_exact,
                    "L055": self.l055_exact}[str(arm)])


def tallies_from_n14_records(
        records: Sequence[Mapping[str, Any]]) -> N14Tallies:
    """Build gate tallies exclusively from N decoder records.

    Every contributing record must carry ``batch_id == N14_BATCH_ID`` and a
    frozen ``(arm, pair, block)`` identity; each of the 24 ``(arm, pair)``
    groups must contribute exactly the 12 paired blocks; ORACLE rows must
    be marked ungraded and never enter the graded pools. Anything else
    raises, so non-N evidence cannot enter the gate.
    """
    if not records:
        raise ValueError("no N decoder records")
    plan_keys = {(e["arm"], e["pair_idx"], e["block_seed"])
                 for e in build_call_plan()}
    seen = set()
    l045: dict[int, int] = {}
    l055: dict[int, int] = {}
    joint: dict[int, int] = {}
    oracle = 0
    for record in records:
        if record.get("batch_id") != N14_BATCH_ID:
            raise ValueError("record without N batch tag cannot enter the "
                             "N gate: %r"
                             % ({k: record.get(k) for k in
                                 ("arm", "pair_idx", "block_seed",
                                  "batch_id")},))
        key = (record.get("arm"), int(record["pair_idx"]),
               int(record["block_seed"]))
        if key not in plan_keys:
            raise ValueError("record identity outside frozen N plan: %r"
                             % (key,))
        if key in seen:
            raise ValueError("duplicate N record identity: %r" % (key,))
        seen.add(key)
        arm, pair = key[0], key[1]
        if arm == ORACLE_ARM:
            if bool(record.get("graded", True)):
                raise ValueError("ORACLE record must be ungraded")
            oracle += 1 if record["exact"] else 0
        elif arm in ("L045", "L055"):
            if not bool(record.get("graded", False)):
                raise ValueError("L1 record must be graded")
            store = l045 if arm == "L045" else l055
            store[pair] = store.get(pair, 0) + (1 if record["exact"] else 0)
        elif arm == L2_ARM:
            if not bool(record.get("graded", False)):
                raise ValueError("APP record must be graded")
            joint[pair] = joint.get(pair, 0) \
                + (1 if record["joint_exact"] else 0)
        else:
            raise ValueError("record arm outside N arms: %r" % (arm,))
    if seen != plan_keys:
        raise ValueError("N records cover %d/288 planned identities "
                         "(zero-skip)" % len(seen))
    pairs = sorted(range(1, 7))
    return N14Tallies(
        [l045.get(p, 0) for p in pairs], [l055.get(p, 0) for p in pairs],
        [joint.get(p, 0) for p in pairs], oracle)


def _check_vector(vec: Sequence[int]) -> tuple[int, ...]:
    vec = tuple(int(v) for v in vec)
    if len(vec) != 6 or any(v < 0 or v > 12 for v in vec):
        raise ValueError("N gate vectors require six per-pair counts 0..12")
    return vec


def is_l1_adequate(l055_exact: Sequence[int],
                   engineering_reason: str = "") -> bool:
    """Frozen ``L1-ADEQUATE(L055)`` (prereg §7 verbatim)."""
    if engineering_reason:
        return False
    vec = _check_vector(l055_exact)
    return sum(vec) >= L1_MIN_EXACT \
        and sum(1 for v in vec if v >= 2) >= L1_GRAPHS_GE2_MIN


def is_oracle_adequate(oracle_pool: int,
                       engineering_reason: str = "") -> bool:
    """Frozen ``ORACLE-ADEQUATE`` (prereg §7 verbatim)."""
    if engineering_reason:
        return False
    return int(oracle_pool) >= ORACLE_MIN


def is_l2_joint_good(joint_pool: int,
                     engineering_reason: str = "") -> bool:
    """Frozen ``L2-JOINT-GOOD`` (prereg §7 verbatim)."""
    if engineering_reason:
        return False
    return int(joint_pool) >= JOINT_MIN


def describe_paired_l1(
        l045_by_cell: Mapping[tuple[int, int], bool],
        l055_by_cell: Mapping[tuple[int, int], bool]) -> dict[str, Any]:
    """Descriptive paired L055-only/L045-only discordances (never gating).

    Inputs map ``(pair_idx, block_seed)`` to exact over the 72 shared
    cells. Reported descriptively only; the routing gate never sees it.
    """
    challenger_only = reference_only = concordant = 0
    for pair_idx, (l1_seed, _l2_seed) in enumerate(
            zip(L1_GRAPH_SEEDS, L2_GRAPH_SEEDS), start=1):
        for block_seed in BLOCK_SEEDS:
            key = (int(pair_idx), int(block_seed))
            try:
                chal_ok = bool(l055_by_cell[key])
                ref_ok = bool(l045_by_cell[key])
            except KeyError:
                raise ValueError("unpaired N L1 calls at pair=%d block=%d"
                                 % key) from None
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
            "cells": 72, "descriptive_only": True}


def route_terminal(tallies: N14Tallies,
                   engineering_reason: str = "") -> str:
    """Frozen terminal routing (prereg §7 verbatim, first match wins).

    Only the graded exact pools enter; L045 discordances are descriptive
    only and structurally cannot reach this function. Priority is
    exhaustive over the boolean inputs, so ``N_ROUTE_AMBIGUOUS`` is
    retained as the frozen else-label and is unreachable by construction.
    """
    if not isinstance(tallies, N14Tallies):
        raise TypeError("route_terminal accepts only N14Tallies "
                        "(non-N evidence cannot enter the N gate)")
    if engineering_reason:
        return T_ENGINEERING_BLOCKED
    l1_ok = is_l1_adequate(tallies.l055_exact)
    oracle_ok = is_oracle_adequate(tallies.oracle_pool)
    joint_ok = is_l2_joint_good(sum(tallies.app_joint))
    if not l1_ok:
        return T_L1_CONSTRUCTION
    if not joint_ok and not oracle_ok:
        return T_L2_DEGREE
    if oracle_ok and not joint_ok:
        return T_TRANSFER_BOTTLENECK
    if joint_ok:
        return T_SCALE_VALIDATION
    return T_AMBIGUOUS


# --------------------------------------------------------------------------- #
# Dispatch: shared paired identities; provenance-gated APP; ungraded ORACLE
# --------------------------------------------------------------------------- #
def _tag_l1(record: Mapping[str, Any], entry: Mapping[str, Any]) -> dict:
    out = dict(record)
    out.update({
        "arm": str(entry["arm"]), "pair_idx": int(entry["pair_idx"]),
        "l1_graph_seed": int(entry["l1_graph_seed"]),
        "l2_graph_seed": int(entry["l2_graph_seed"]),
        "block_seed": int(entry["block_seed"]),
        "batch_id": N14_BATCH_ID, "oracle": False, "graded": True,
        "source_exact": bool(record["exact"]),
        "target_exact": False, "joint_exact": False,
        "undetected": False,
    })
    return out


def run_l2_app_cell(l2_graph: Mapping[str, Any], block: Mapping[str, Any],
                    entry: Mapping[str, Any], *, belief,
                    provenance: str, source_exact: bool,
                    decode_fn, syndrome_fn, transfer_fn,
                    call_idx: int) -> dict[str, Any]:
    """One L2 APP call on forward-transfer beliefs (fail-closed, injected).

    ``belief``/``provenance``/``source_exact`` arrive as explicit caller
    inputs: this readiness module freezes neither which L1 profile sources
    the shared APP stream nor the transfer-prior construction — the future
    authorized runner binds the accepted canonical transfer helper. The
    only frozen rule enforced here: a non-``CHECK_UPDATED`` provenance
    raises ``ProvenanceRefused`` before any decoder contact (uniform/
    prior-only fallback forbidden). ``decode_fn``/``syndrome_fn``/
    ``transfer_fn`` must be explicitly injected; this module never imports
    the production decoder.
    """
    if l2_graph.get("dense") is None or not bool(l2_graph.get("admitted")):
        raise StructureNotAdmitted(
            "refusing decoder binding for non-admitted L2 graph %r"
            % ({"graph_seed": l2_graph.get("graph_seed")},))
    require_check_updated(str(provenance))
    if decode_fn is None or not callable(decode_fn):
        raise ValueError("decode_fn must be explicitly injected")
    if syndrome_fn is None or not callable(syndrome_fn):
        raise ValueError("syndrome_fn must be explicitly injected")
    if transfer_fn is None or not callable(transfer_fn):
        raise ValueError("transfer_fn must be explicitly injected")
    import numpy as np

    H = np.asarray(l2_graph["dense"], dtype=np.uint8)
    u2 = np.asarray(block["u2"], dtype=np.int64)
    prior = np.asarray(transfer_fn(belief, block), dtype=np.float64)
    t0 = time.perf_counter()
    try:
        syn = np.asarray(syndrome_fn(H, u2), dtype=np.uint8)
        result = decode_fn(H, prior, syn, max_iter=DECODER_MAX_ITER,
                           damping_alpha=DAMPING_ALPHA, warm_beliefs=None,
                           field=None)
        x_hat = np.asarray(result.x_hat)
        syndrome_ok = bool(result.syndrome_ok)
        target_exact = bool(syndrome_ok and x_hat.shape == u2.shape
                            and np.array_equal(x_hat, u2))
        joint_exact = bool(source_exact) and target_exact
        residual = int(np.count_nonzero(np.asarray(syndrome_fn(H, x_hat))
                                        != syn))
        return {
            "call_idx": int(call_idx), "arm": L2_ARM,
            "pair_idx": int(entry["pair_idx"]),
            "l1_graph_seed": int(entry["l1_graph_seed"]),
            "l2_graph_seed": int(entry["l2_graph_seed"]),
            "block_seed": int(entry["block_seed"]),
            "batch_id": N14_BATCH_ID, "oracle": False, "graded": True,
            "exact": joint_exact, "syndrome_ok": syndrome_ok,
            "source_exact": bool(source_exact),
            "target_exact": target_exact, "joint_exact": joint_exact,
            "undetected": False,
            "iterations": int(result.iterations),
            "status": str(result.status),
            "residual_syndrome_weight": residual,
            "belief_provenance": getattr(
                result, "belief_provenance", "CHECK_UPDATED"),
            "crash": False, "error": "",
            "wall_s": time.perf_counter() - t0,
        }
    except Exception as exc:  # retained crash record; never retried
        return {
            "call_idx": int(call_idx), "arm": L2_ARM,
            "pair_idx": int(entry["pair_idx"]),
            "l1_graph_seed": int(entry["l1_graph_seed"]),
            "l2_graph_seed": int(entry["l2_graph_seed"]),
            "block_seed": int(entry["block_seed"]),
            "batch_id": N14_BATCH_ID, "oracle": False, "graded": True,
            "exact": False, "syndrome_ok": False,
            "source_exact": bool(source_exact),
            "target_exact": False, "joint_exact": False,
            "undetected": False, "iterations": -1,
            "status": "crash", "residual_syndrome_weight": -1,
            "belief_provenance": "CHECK_UPDATED",
            "crash": True, "error": repr(exc)[:300],
            "wall_s": time.perf_counter() - t0,
        }


def run_l2_oracle_cell(l2_graph: Mapping[str, Any],
                       block: Mapping[str, Any],
                       entry: Mapping[str, Any], *, decode_fn, syndrome_fn,
                       oracle_prior_fn, call_idx: int) -> dict[str, Any]:
    """One L2 ORACLE call under true-L1 conditioning (diagnostic, ungraded).

    ``oracle_prior_fn`` is explicitly injected (the future authorized
    runner binds the accepted true-L1 conditional prior). Records are
    marked ``ORACLE``/ungraded and excluded from all graded pools; only
    the pooled oracle-exact count enters ``ORACLE-ADEQUATE``.
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
            "call_idx": int(call_idx), "arm": ORACLE_ARM,
            "pair_idx": int(entry["pair_idx"]),
            "l1_graph_seed": int(entry["l1_graph_seed"]),
            "l2_graph_seed": int(entry["l2_graph_seed"]),
            "block_seed": int(entry["block_seed"]),
            "batch_id": N14_BATCH_ID, "oracle": True, "graded": False,
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
            "call_idx": int(call_idx), "arm": ORACLE_ARM,
            "pair_idx": int(entry["pair_idx"]),
            "l1_graph_seed": int(entry["l1_graph_seed"]),
            "l2_graph_seed": int(entry["l2_graph_seed"]),
            "block_seed": int(entry["block_seed"]),
            "batch_id": N14_BATCH_ID, "oracle": True, "graded": False,
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
                 graphs_l2: Mapping[int, Mapping[str, Any]],
                 blocks: Mapping[int, Mapping[str, Any]],
                 decode_fn, syndrome_fn, *,
                 transfer_fn=None, oracle_prior_fn=None,
                 app_sources: Mapping[tuple[int, int], Mapping[str, Any]
                                      ] | None = None,
                 now=None, rss_fn=None,
                 wall_budget_s: float = WALL_BUDGET_S,
                 per_call_budget_s: float = PER_CALL_BUDGET_S,
                 rss_budget_bytes: int = RSS_BUDGET_BYTES,
                 call_ceiling: int = SCIENTIFIC_CALL_CEILING
                 ) -> dict[str, Any]:
    """Dispatch the frozen plan through injected decoders (fake-testable).

    All 18 graphs are admission-checked before any decoder binding; any
    failure engineering-blocks with zero decoder calls and no seed change.
    Each ``(pair, block)`` cell shares its block and graph identities
    across the four arms. ``app_sources`` maps ``(pair_idx, block_seed)``
    to ``{"belief", "provenance", "source_exact"}`` for the APP stream
    (explicit injection; no frozen default). A provenance refusal retains
    a refusal record and engineering-blocks with no decoder contact.
    Decoder crashes are retained, never retried.
    """
    now = now or time.monotonic
    t0 = float(now())
    failure: str | None = None
    for pair_idx, (l1_seed, l2_seed) in enumerate(
            zip(L1_GRAPH_SEEDS, L2_GRAPH_SEEDS), start=1):
        for profile in L1_PROFILES:
            graph = graphs_l1.get((profile, int(l1_seed)))
            if graph is None or not bool(graph.get("admitted")):
                failure = ("graph (profile=%s, seed=%d) not admitted; "
                           "blocked without seed replacement"
                           % (profile, int(l1_seed)))
                break
        if failure is not None:
            break
        l2_graph = graphs_l2.get(int(l2_seed))
        if l2_graph is None or not bool(l2_graph.get("admitted")):
            failure = ("L2 graph (seed=%d) not admitted; blocked without "
                       "seed replacement" % int(l2_seed))
            break
    records: list[dict[str, Any]] = []
    if failure is None:
        for entry in plan:
            if len(records) >= int(call_ceiling):
                failure = "scientific call ceiling reached"
                break
            arm = str(entry["arm"])
            call_t0 = float(now())
            try:
                if arm in L1_PROFILES:
                    graph = graphs_l1[(arm, int(entry["l1_graph_seed"]))]
                    record = _tag_l1(
                        r2.dispatch_l1(
                            graph, blocks[int(entry["block_seed"])], {
                                "width": N, "arm": arm,
                                "graph_seed": int(entry["l1_graph_seed"]),
                                "block_seed": int(entry["block_seed"])},
                            decode_fn, syndrome_fn,
                            call_idx=len(records)),
                        entry)
                elif arm == L2_ARM:
                    if transfer_fn is None:
                        raise ValueError(
                            "transfer_fn must be explicitly injected "
                            "for L2 APP")
                    source = (app_sources or {}).get(
                        (int(entry["pair_idx"]),
                         int(entry["block_seed"])))
                    if source is None:
                        raise ValueError(
                            "APP source missing at pair=%d block=%d "
                            "(no frozen default)" % (
                                int(entry["pair_idx"]),
                                int(entry["block_seed"])))
                    record = run_l2_app_cell(
                        graphs_l2[int(entry["l2_graph_seed"])],
                        blocks[int(entry["block_seed"])], entry,
                        belief=source["belief"],
                        provenance=str(source["provenance"]),
                        source_exact=bool(source["source_exact"]),
                        decode_fn=decode_fn, syndrome_fn=syndrome_fn,
                        transfer_fn=transfer_fn, call_idx=len(records))
                elif arm == ORACLE_ARM:
                    if oracle_prior_fn is None:
                        raise ValueError(
                            "oracle_prior_fn must be explicitly injected "
                            "for L2 ORACLE")
                    record = run_l2_oracle_cell(
                        graphs_l2[int(entry["l2_graph_seed"])],
                        blocks[int(entry["block_seed"])], entry,
                        decode_fn=decode_fn, syndrome_fn=syndrome_fn,
                        oracle_prior_fn=oracle_prior_fn,
                        call_idx=len(records))
                else:
                    raise ValueError("plan arm outside N arms: %r" % (arm,))
            except ProvenanceRefused as exc:
                record = {
                    "call_idx": len(records), "arm": arm,
                    "pair_idx": int(entry["pair_idx"]),
                    "l1_graph_seed": int(entry["l1_graph_seed"]),
                    "l2_graph_seed": int(entry["l2_graph_seed"]),
                    "block_seed": int(entry["block_seed"]),
                    "batch_id": N14_BATCH_ID, "oracle": False,
                    "graded": True, "exact": False, "syndrome_ok": False,
                    "source_exact": False, "target_exact": False,
                    "joint_exact": False, "undetected": False,
                    "iterations": -1, "status": "provenance_refused",
                    "residual_syndrome_weight": -1,
                    "belief_provenance": "",
                    "crash": False, "error": repr(exc)[:300],
                    "wall_s": max(float(now()) - call_t0, 0.0),
                }
                records.append(record)
                failure = "provenance refusal: %s" % exc
                break
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
# Pre-decoder profile: all 18 future graphs, no decoder, no root
# --------------------------------------------------------------------------- #
def profile_graphs(build_l1_fn=None, build_l2_fn=None,
                   now=None) -> dict[str, Any]:
    """Bounded profile: build all 18 frozen N graphs, no decoder, no root.

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

    for profile in L1_PROFILES:
        for graph_seed in L1_GRAPH_SEEDS:
            start = float(now())
            graph = build_l1_fn(profile, int(graph_seed))
            entry = _entry(graph, float(now()) - start)
            entries.append(entry)
            if not graph["admitted"]:
                failures.append({"family": "L1", "profile": profile,
                                 "seed": int(graph_seed),
                                 "status": entry["status"],
                                 "failure_reason": entry["failure_reason"]})
    for graph_seed in L2_GRAPH_SEEDS:
        start = float(now())
        graph = build_l2_fn(int(graph_seed))
        entry = _entry(graph, float(now()) - start)
        entries.append(entry)
        if not graph["admitted"]:
            failures.append({"family": "L2", "profile": "L2",
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
