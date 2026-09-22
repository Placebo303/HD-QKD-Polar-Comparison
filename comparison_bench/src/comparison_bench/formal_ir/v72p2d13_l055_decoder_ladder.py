"""V72P2D13 L055 failure decoder ladder — selector/replay/ladder/gate/verifier.

Change: ``v72p2d13-l055-decoder-ladder``
Cycle: ``V72P2D13-L055-DECODER-LADDER`` (decoder-dynamics diagnostic on frozen
failures; NOT a code-ensemble change and NOT a correction of any predecessor)
Frozen authority: ``.workbuddy/tasks/D13_L055_FAILURE_DECODER_LADDER_READINESS_TASK_PACKET.md``
(§1–§4) and ``openspec/changes/v72p2d13-l055-decoder-ladder/`` (proposal,
design §1–§6, tasks, delta spec). Track: **implementation/readiness** (zero
scientific calls; no D13 execution, no decoder calls, no root creation, no
L2/D7-H, no real data, no commit/push). The future batch is ``EXPLORE``.

Reuse contract (IMPORT — no decoder duplication; semantic map in design §4):

- D12 reconstruction: ``d12.build_graph`` (frozen R2 construction/admission),
  ``d12.degree_cell``, ``d12.coefficient_seed``, ``d12.dispatch_l1`` reference,
  ``d12.refuse_out_root``, ``d12.Q/POLY/MODEL_F_INPUT_ROOT`` and the
  ``DECODER_MAX_ITER``/``DAMPING_ALPHA`` contract;
- RL90 binder: ``x3rl.bind_row_layered_decoders``
  (``v72p2d7_gf32_cross_layer_discriminator.py:666``, cold max_iter90);
- RL90/flooding-90 pair binder: ``x3sched.bind_schedule_decoders``
  (``v72p2d7_gf32_schedule_discriminator.py:431``);
- RL360: the same accepted row-layered target with ``max_iter=360``
  (``v35_algorithm_development.py:781-786``); no new decoder;
- damping-0.7: the EXISTING ``damping_alpha`` parameter
  (``v35_algorithm_development.py:786`` signature, ``:831`` read,
  ``:870-876`` damping branch, ``:939-954`` wrapper), NOT tuned;
- flooding-360: the accepted flooding target with ``max_iter=360``
  (``v35_algorithm_development.py:672-678``; no damping parameter by design);
- CHECK_UPDATED provenance (``v35_algorithm_development.py:524``, emitted
  ``:759``/``:777``/``:906``/``:932``); mandatory on every admitted return.

This module performs no scientific decoder call on import or on any
PLAN_ONLY/verify path: decoder entry is always an explicitly injected
callable (fakes in tests; accepted binders only under separate explicit
execution authorization via the runner).
"""
from __future__ import annotations

import csv
import json
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Callable

from . import v72p2d12_finite_l1_degree as d12
from . import v72p2d7_gf32_cross_layer_discriminator as x3rl
from . import v72p2d7_gf32_schedule_discriminator as x3sched

__all__ = [
    "CHANGE_ID", "CYCLE_ID", "TRACK", "CLAIM_CEILING",
    "INPUT_ROOT", "FUTURE_ROOT", "FUTURE_ROOT_UUID",
    "SELECT_ARM", "D12_BATCH_ID", "CHECK_UPDATED",
    "EXPECTED_N128", "EXPECTED_N256", "EXPECTED_TOTAL",
    "BASELINE_ITERATIONS", "REPLAY_ARM_ID", "LADDER_ARMS",
    "LADDER_CONFIG", "ARM_TERMINAL", "TERMINALS", "T_ENGINEERING_BLOCKED",
    "SCIENTIFIC_CALL_CEILING", "SETUP_CALL_CEILING",
    "WALL_BUDGET_S", "PER_CALL_BUDGET_S", "RSS_BUDGET_BYTES",
    "EVIDENCE_FILES", "FROZEN_COMMAND", "AUTHORIZATION",
    "BINDER_MAP", "FROZEN_IDENTITIES", "FROZEN_IDENTITY_SET",
    "select_l055_failures", "selection_identities", "validate_selection",
    "build_ladder_plan", "compare_replay", "is_rescue",
    "classify_rescues", "rank_material_arms", "route_terminal",
    "run_readiness", "write_root", "verify_root",
    "bind_production", "plan_only_metadata",
]

# --------------------------------------------------------------------------- #
# Frozen identifiers (packet §2; design §2–§3; spec REQ-D13-SEL/ROOT/BUDGET)
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2d13-l055-decoder-ladder"
CYCLE_ID = "V72P2D13-L055-DECODER-LADDER"
TRACK = "implementation/readiness"
CLAIM_CEILING = (
    "frozen synthetic L1 decoder diagnostic only; no ensemble optimality, "
    "forward/L2, FER/leakage/SKR, real-data, D7-H or qualification claim"
)

INPUT_ROOT = "workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450"
FUTURE_ROOT_UUID = "5c41b416-cacc-4b6e-892e-d8a59c53170e"
FUTURE_ROOT = "workspace/d13_l055_decoder_ladder_" + FUTURE_ROOT_UUID
D12_BATCH_ID = d12.D12_BATCH_ID
CHECK_UPDATED = "CHECK_UPDATED"

SELECT_ARM = "L055"
EXPECTED_N128 = 30
EXPECTED_N256 = 26
EXPECTED_TOTAL = 56
BASELINE_ITERATIONS = 90  # == d12.DECODER_MAX_ITER (frozen RL90 replay)

REPLAY_ARM_ID = "ROW_LAYERED_90_ALPHA_1"
LADDER_ARMS = ("ROW_LAYERED_360_ALPHA_1",
               "ROW_LAYERED_360_ALPHA_0_7",
               "FLOODING_360_ALPHA_1")
#: Frozen per-arm call shape (accepted targets; damping-0.7 is the existing
#: parameter value, NOT a tuning result).
LADDER_CONFIG = {
    "ROW_LAYERED_90_ALPHA_1": {"schedule": "row-layered", "max_iter": 90,
                               "damping_alpha": 1.0, "cold": True},
    "ROW_LAYERED_360_ALPHA_1": {"schedule": "row-layered", "max_iter": 360,
                                "damping_alpha": 1.0, "cold": True},
    "ROW_LAYERED_360_ALPHA_0_7": {"schedule": "row-layered", "max_iter": 360,
                                  "damping_alpha": 0.7, "cold": True},
    "FLOODING_360_ALPHA_1": {"schedule": "flooding", "max_iter": 360,
                             "damping_alpha": None, "cold": True},
}

T_SELECT_RL360 = "D13_SELECT_RL360"
T_SELECT_RL360_DAMP07 = "D13_SELECT_RL360_DAMP07"
T_SELECT_FLOOD360 = "D13_SELECT_FLOOD360"
T_MODEST = "D13_MODEST_DECODER_RESCUE"
T_NO_MATERIAL = "D13_NO_MATERIAL_DECODER_RESCUE"
T_AMBIGUOUS = "D13_DECODER_RESCUE_AMBIGUOUS"
T_ENGINEERING_BLOCKED = "D13_ENGINEERING_BLOCKED"
TERMINALS = (T_SELECT_RL360, T_SELECT_RL360_DAMP07, T_SELECT_FLOOD360,
             T_MODEST, T_NO_MATERIAL, T_AMBIGUOUS, T_ENGINEERING_BLOCKED)
ARM_TERMINAL = {
    "ROW_LAYERED_360_ALPHA_1": T_SELECT_RL360,
    "ROW_LAYERED_360_ALPHA_0_7": T_SELECT_RL360_DAMP07,
    "FLOODING_360_ALPHA_1": T_SELECT_FLOOD360,
}

#: Rescue gates (packet §2 verbatim; spec REQ-D13-GATE-01..05).
MATERIAL_MIN_TOTAL = 12
MATERIAL_MIN_WIDTH = 4
MODEST_MIN_TOTAL = 3
MODEST_MAX_TOTAL = 11
MODEST_MIN_WIDTH = 1
NO_RESCUE_MAX_TOTAL = 2

#: Budgets (packet §2: 56 replay + 56x3 ladder = 224; setup <= 8).
SCIENTIFIC_CALL_CEILING = 224
SETUP_CALL_CEILING = 8
SETUP_FIXED_UNITS = 2  # Model-F load + plan build (reconstruction reuses D12)
WALL_BUDGET_S = 1800.0
PER_CALL_BUDGET_S = 120.0
RSS_BUDGET_BYTES = d12.RSS_BUDGET_BYTES

EVIDENCE_FILES = ("manifest.json", "selection.csv", "replay_records.csv",
                  "ladder_records.csv", "summary.json", "command_log.txt")
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d13_development.py "
    "--d13-batch --model-f-root %s --out-root %s"
    % (d12.MODEL_F_INPUT_ROOT, FUTURE_ROOT)
)
AUTHORIZATION = (
    "separate explicit user/main-thread authorization required before "
    "--d13-batch (pass --execution-authorized only under that authorization)")

#: Binder semantic map (design §4): import-only, never reimplemented.
BINDER_MAP = {
    "d12_build_graph":
        "comparison_bench/src/comparison_bench/formal_ir/"
        "v72p2d12_finite_l1_degree.py:228 build_graph",
    "d12_shared_binding":
        "comparison_bench/src/comparison_bench/formal_ir/"
        "v72p2d12_finite_l1_degree.py:150-152 "
        "dispatch_l1/coefficient_seed/refuse_out_root",
    "d12_decoder_contract":
        "comparison_bench/src/comparison_bench/formal_ir/"
        "v72p2d12_finite_l1_degree.py:143-147 "
        "DECODER_MAX_ITER/DAMPING_ALPHA/MODEL_F_INPUT_ROOT/Q/POLY",
    "rl90_binder":
        "comparison_bench/src/comparison_bench/formal_ir/"
        "v72p2d7_gf32_cross_layer_discriminator.py:666 "
        "bind_row_layered_decoders",
    "schedule_pair_binder":
        "comparison_bench/src/comparison_bench/formal_ir/"
        "v72p2d7_gf32_schedule_discriminator.py:431 bind_schedule_decoders",
    "rl360_target":
        "comparison_bench/src/comparison_bench/formal_ir/"
        "v35_algorithm_development.py:781-786 decode_row_layered_fftqspa "
        "(called with max_iter=360)",
    "damping_param":
        "comparison_bench/src/comparison_bench/formal_ir/"
        "v35_algorithm_development.py:786/:831/:870-876 damping_alpha "
        "(existing parameter, NOT tuned)",
    "flooding360_target":
        "comparison_bench/src/comparison_bench/formal_ir/"
        "v35_algorithm_development.py:672-678 decode_flooding_fftqspa "
        "(called with max_iter=360; no damping parameter by design)",
    "provenance_token":
        "comparison_bench/src/comparison_bench/formal_ir/"
        "v35_algorithm_development.py:524 BELIEF_PROVENANCE_CHECK_UPDATED",
}

# --------------------------------------------------------------------------- #
# Frozen 56-identity list (design §3; tuples of
# (width, graph_seed, stored per-width call_idx, block_seed))
# --------------------------------------------------------------------------- #
FROZEN_IDENTITIES: tuple[tuple[int, int, int, int], ...] = (
    (128, 2026093001, 149, 2026093206), (128, 2026093001, 150, 2026093207),
    (128, 2026093001, 151, 2026093208), (128, 2026093001, 152, 2026093209),
    (128, 2026093001, 155, 2026093212),
    (128, 2026093002, 161, 2026093206), (128, 2026093002, 162, 2026093207),
    (128, 2026093002, 163, 2026093208), (128, 2026093002, 164, 2026093209),
    (128, 2026093002, 167, 2026093212),
    (128, 2026093003, 168, 2026093201), (128, 2026093003, 171, 2026093204),
    (128, 2026093003, 174, 2026093207), (128, 2026093003, 175, 2026093208),
    (128, 2026093003, 176, 2026093209), (128, 2026093003, 178, 2026093211),
    (128, 2026093003, 179, 2026093212),
    (128, 2026093004, 183, 2026093204), (128, 2026093004, 186, 2026093207),
    (128, 2026093004, 187, 2026093208), (128, 2026093004, 191, 2026093212),
    (128, 2026093005, 197, 2026093206), (128, 2026093005, 198, 2026093207),
    (128, 2026093005, 199, 2026093208), (128, 2026093005, 200, 2026093209),
    (128, 2026093005, 203, 2026093212),
    (128, 2026093006, 204, 2026093201), (128, 2026093006, 209, 2026093206),
    (128, 2026093006, 211, 2026093208), (128, 2026093006, 215, 2026093212),
    (256, 2026093101, 146, 2026093303), (256, 2026093101, 148, 2026093305),
    (256, 2026093101, 149, 2026093306), (256, 2026093101, 151, 2026093308),
    (256, 2026093101, 153, 2026093310),
    (256, 2026093102, 158, 2026093303), (256, 2026093102, 160, 2026093305),
    (256, 2026093102, 165, 2026093310),
    (256, 2026093103, 169, 2026093302), (256, 2026093103, 170, 2026093303),
    (256, 2026093103, 172, 2026093305), (256, 2026093103, 173, 2026093306),
    (256, 2026093103, 177, 2026093310),
    (256, 2026093104, 181, 2026093302), (256, 2026093104, 182, 2026093303),
    (256, 2026093104, 184, 2026093305), (256, 2026093104, 189, 2026093310),
    (256, 2026093105, 193, 2026093302), (256, 2026093105, 194, 2026093303),
    (256, 2026093105, 197, 2026093306), (256, 2026093105, 201, 2026093310),
    (256, 2026093106, 205, 2026093302), (256, 2026093106, 206, 2026093303),
    (256, 2026093106, 208, 2026093305), (256, 2026093106, 209, 2026093306),
    (256, 2026093106, 213, 2026093310),
)
FROZEN_IDENTITY_SET = frozenset(FROZEN_IDENTITIES)


# --------------------------------------------------------------------------- #
# Scalar coercions (CSV strings or native values)
# --------------------------------------------------------------------------- #
def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("true", "1", "yes"):
        return True
    if text in ("false", "0", "no", ""):
        return False
    raise ValueError("not a boolean: %r" % (value,))


def _as_int(value: Any) -> int:
    return int(str(value).strip())


# --------------------------------------------------------------------------- #
# Selection (spec REQ-D13-SEL-01..04)
# --------------------------------------------------------------------------- #
def select_l055_failures(
        records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Select exactly ``arm == L055 AND exact == false`` (no successes).

    The input root is never modified here: selection is a pure filter over
    already-read rows.
    """
    selected = []
    for row in records:
        if str(row.get("arm")) != SELECT_ARM:
            continue
        if _as_bool(row.get("exact")):
            continue  # successes never enter the ladder
        selected.append({
            "call_idx": _as_int(row.get("call_idx")),
            "width": _as_int(row.get("width")),
            "arm": SELECT_ARM,
            "graph_seed": _as_int(row.get("graph_seed")),
            "block_seed": _as_int(row.get("block_seed")),
            "batch_id": str(row.get("batch_id", "")),
            "exact": False,
            "syndrome_ok": _as_bool(row.get("syndrome_ok")),
            "iterations": _as_int(row.get("iterations")),
            "status": str(row.get("status", "")),
            "belief_provenance": str(row.get("belief_provenance", "")),
        })
    selected.sort(key=lambda r: (r["width"], r["graph_seed"],
                                 r["call_idx"], r["block_seed"]))
    return selected


def selection_identities(
        selected: Sequence[Mapping[str, Any]]) -> frozenset:
    return frozenset((int(r["width"]), int(r["graph_seed"]),
                      int(r["call_idx"]), int(r["block_seed"]))
                     for r in selected)


def validate_selection(
        selected: Sequence[Mapping[str, Any]]) -> list[str]:
    """Fail-closed check of the frozen 56-identity selection."""
    violations: list[str] = []
    n128 = sum(1 for r in selected if int(r["width"]) == 128)
    n256 = sum(1 for r in selected if int(r["width"]) == 256)
    if len(selected) != EXPECTED_TOTAL:
        violations.append("selection count %d != frozen %d"
                          % (len(selected), EXPECTED_TOTAL))
    if n128 != EXPECTED_N128 or n256 != EXPECTED_N256:
        violations.append("selection width split n128=%d n256=%d != frozen "
                          "%d/%d" % (n128, n256, EXPECTED_N128,
                                     EXPECTED_N256))
    if selection_identities(selected) != FROZEN_IDENTITY_SET:
        violations.append("selection identities != frozen 56-identity list "
                          "(design §3)")
    for index, row in enumerate(selected):
        if _as_bool(row.get("exact")):
            violations.append("selection row %d carries a success" % index)
        if _as_bool(row.get("syndrome_ok")):
            violations.append("selection row %d syndrome_ok (undetected "
                              "excluded from selection)" % index)
        if _as_int(row.get("iterations")) != BASELINE_ITERATIONS:
            violations.append("selection row %d iterations %r != frozen 90"
                              % (index, row.get("iterations")))
        if str(row.get("belief_provenance")) != CHECK_UPDATED:
            violations.append("selection row %d provenance %r != "
                              "CHECK_UPDATED" % (index,
                                                 row.get("belief_provenance")))
        if str(row.get("batch_id")) != D12_BATCH_ID:
            violations.append("selection row %d batch_id tag missing" % index)
    return violations


# --------------------------------------------------------------------------- #
# Ladder plan — built BEFORE any decoder binding (D1304 structural rule)
# --------------------------------------------------------------------------- #
def build_ladder_plan(
        selected: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Build the frozen 224-entry call plan (56 replay + 56x3 ladder).

    Pure constructor: no decoder binding, no Model-F load, no root access.
    Replays come first in selection order; ladder entries follow per
    failure in the fixed arm order of REQ-D13-ARM-01.
    """
    ordered = sorted(selected,
                     key=lambda r: (int(r["width"]), int(r["graph_seed"]),
                                    int(r["call_idx"]), int(r["block_seed"])))
    plan: list[dict[str, Any]] = []
    for position, row in enumerate(ordered):
        plan.append({
            "plan_idx": len(plan), "kind": "replay",
            "decoder_arm": REPLAY_ARM_ID,
            "width": int(row["width"]), "arm": SELECT_ARM,
            "graph_seed": int(row["graph_seed"]),
            "block_seed": int(row["block_seed"]),
            "call_idx": int(row["call_idx"]),
            "replay_position": position,
        })
    for row in ordered:
        for ladder_arm in LADDER_ARMS:
            plan.append({
                "plan_idx": len(plan), "kind": "ladder",
                "decoder_arm": ladder_arm,
                "width": int(row["width"]), "arm": SELECT_ARM,
                "graph_seed": int(row["graph_seed"]),
                "block_seed": int(row["block_seed"]),
                "call_idx": int(row["call_idx"]),
            })
    return plan


# --------------------------------------------------------------------------- #
# Strict RL90 replay comparator (spec REQ-D13-REPLAY-01..04)
# --------------------------------------------------------------------------- #
_REPLAY_FIELDS = ("exact", "syndrome_ok", "iterations", "belief_provenance")
_IDENTITY_FIELDS = ("width", "arm", "graph_seed", "block_seed", "call_idx")


def compare_replay(stored: Mapping[str, Any],
                   observed: Mapping[str, Any]) -> str | None:
    """Return ``None`` on strict match, else the first mismatching field.

    CHECK_UPDATED provenance is mandatory: any observed return without it
    is a mismatch (never admitted as evidence).
    """
    for field in _IDENTITY_FIELDS:
        if str(observed.get(field)) != str(stored.get(field)):
            return field
    if _as_bool(observed.get("exact")) != _as_bool(stored.get("exact")):
        return "exact"
    if _as_bool(observed.get("syndrome_ok")) != _as_bool(
            stored.get("syndrome_ok")):
        return "syndrome_ok"
    if _as_int(observed.get("iterations")) != _as_int(
            stored.get("iterations")):
        return "iterations"
    if str(observed.get("belief_provenance")) != CHECK_UPDATED:
        return "belief_provenance"
    if str(observed.get("belief_provenance")) != str(
            stored.get("belief_provenance")):
        return "belief_provenance"
    return None


def is_rescue(result: Mapping[str, Any]) -> bool:
    """A rescue is exact AND syndrome-valid AND CHECK_UPDATED.

    Exact/syndrome-valid/undetected stay separate: undetected
    (``exact=false, syndrome_ok=true``) and exact-without-syndrome are
    never rescues.
    """
    return bool(_as_bool(result.get("exact"))
                and _as_bool(result.get("syndrome_ok"))
                and str(result.get("belief_provenance")) == CHECK_UPDATED)


# --------------------------------------------------------------------------- #
# Rescue gates, ranking, terminals (packet §2 verbatim; spec REQ-D13-GATE/RANK)
# --------------------------------------------------------------------------- #
def classify_rescues(total: int, n128: int, n256: int) -> str:
    total, n128, n256 = int(total), int(n128), int(n256)
    if total >= MATERIAL_MIN_TOTAL and n128 >= MATERIAL_MIN_WIDTH \
            and n256 >= MATERIAL_MIN_WIDTH:
        return "MATERIAL_RESCUE"
    if MODEST_MIN_TOTAL <= total <= MODEST_MAX_TOTAL \
            and n128 >= MODEST_MIN_WIDTH and n256 >= MODEST_MIN_WIDTH:
        return "MODEST_RESCUE"
    if total <= NO_RESCUE_MAX_TOTAL:
        return "NO_RESCUE"
    return "RESCUE_AMBIGUOUS"


def _arm_order_index(arm: str) -> int:
    return LADDER_ARMS.index(arm)


def rank_material_arms(
        arm_stats: Sequence[Mapping[str, Any]]) -> list[str]:
    """Rank MATERIAL arms by total, then worst-width, then mean-iterations
    among rescues, then the fixed arm order (packet §2 verbatim)."""
    material = [s for s in arm_stats
                if classify_rescues(s["total"], s["n128"], s["n256"])
                == "MATERIAL_RESCUE"]

    def key(stat: Mapping[str, Any]):
        mean_iter = stat.get("mean_iter")
        return (-int(stat["total"]),
                -min(int(stat["n128"]), int(stat["n256"])),
                float(mean_iter) if mean_iter is not None else float("inf"),
                _arm_order_index(str(stat["arm"])))

    return [str(s["arm"]) for s in sorted(material, key=key)]


def route_terminal(arm_results: Mapping[str, Mapping[str, Any]] | Sequence,
                   engineering_reason: str = "") -> str:
    """Route to exactly one of the seven terminals (spec REQ-D13-TERM-01/02).

    A selected arm requires MATERIAL_RESCUE.
    """
    if str(engineering_reason or "").strip():
        return T_ENGINEERING_BLOCKED
    stats = (list(arm_results.values()) if isinstance(arm_results, Mapping)
             else list(arm_results))
    gates = {str(s["arm"]): classify_rescues(s["total"], s["n128"], s["n256"])
             for s in stats}
    ranked = rank_material_arms(stats)
    if ranked:
        return ARM_TERMINAL[ranked[0]]
    if any(g == "MODEST_RESCUE" for g in gates.values()):
        return T_MODEST
    if any(g == "RESCUE_AMBIGUOUS" for g in gates.values()):
        return T_AMBIGUOUS
    return T_NO_MATERIAL


def summarize_arm(ladder_results: Sequence[Mapping[str, Any]],
                  arm: str) -> dict[str, Any]:
    scoped = [r for r in ladder_results if str(r.get("ladder_arm")) == arm]
    rescued = [r for r in scoped if is_rescue(r)]
    n128 = sum(1 for r in rescued if int(r["width"]) == 128)
    n256 = sum(1 for r in rescued if int(r["width"]) == 256)
    iters = [_as_int(r["iterations"]) for r in rescued]
    mean_iter = (sum(iters) / len(iters)) if iters else None
    return {"arm": arm, "calls": len(scoped), "total": len(rescued),
            "n128": n128, "n256": n256, "mean_iter": mean_iter,
            "gate": classify_rescues(len(rescued), n128, n256)}


# --------------------------------------------------------------------------- #
# Readiness dispatcher — plan first, first-mismatch stop (D1304)
# --------------------------------------------------------------------------- #
def run_readiness(selected: Sequence[Mapping[str, Any]],
                  replay_fn: Callable[[Mapping[str, Any]], Mapping[str, Any]],
                  ladder_fns: Mapping[str, Callable],
                  *, now_fn: Callable[[], float] | None = None,
                  rss_fn: Callable[[], int] | None = None,
                  engineering_reason: str = "") -> dict[str, Any]:
    """Execute the frozen ladder over injected decoder entry points.

    The full 224-entry plan is built BEFORE any injected callable runs.
    The first replay mismatch blocks ALL ladder calls. ``replay_fn`` and
    ``ladder_fns`` are explicit injections (fakes in tests; accepted
    binders only under separate explicit execution authorization).
    """
    ordered = sorted(selected,
                     key=lambda r: (int(r["width"]), int(r["graph_seed"]),
                                    int(r["call_idx"]), int(r["block_seed"])))
    plan = build_ladder_plan(ordered)  # built before any binding/call
    if len(plan) > SCIENTIFIC_CALL_CEILING:
        raise RuntimeError("plan %d exceeds ceiling %d"
                           % (len(plan), SCIENTIFIC_CALL_CEILING))
    now = now_fn or time.monotonic
    t0 = float(now())
    replay_results: list[dict[str, Any]] = []
    blocked: dict[str, Any] | None = None
    for position, stored in enumerate(ordered):
        observed = dict(replay_fn(dict(stored)))
        mismatch = compare_replay(stored, observed)
        replay_results.append({
            "width": int(stored["width"]), "arm": SELECT_ARM,
            "graph_seed": int(stored["graph_seed"]),
            "block_seed": int(stored["block_seed"]),
            "call_idx": int(stored["call_idx"]),
            "replay_arm": REPLAY_ARM_ID,
            "exact": _as_bool(observed.get("exact")),
            "syndrome_ok": _as_bool(observed.get("syndrome_ok")),
            "iterations": _as_int(observed.get("iterations")),
            "belief_provenance": str(observed.get("belief_provenance", "")),
            "wall_s": float(observed.get("wall_s", 0.0)),
            "match": mismatch is None, "mismatch_field": mismatch or "",
        })
        if mismatch is not None and blocked is None:
            blocked = {"replay_position": position,
                       "width": int(stored["width"]),
                       "graph_seed": int(stored["graph_seed"]),
                       "block_seed": int(stored["block_seed"]),
                       "call_idx": int(stored["call_idx"]),
                       "mismatch_field": mismatch}
            break  # FIRST mismatch blocks all ladder calls
    ladder_results: list[dict[str, Any]] = []
    if blocked is None:
        for stored in ordered:
            for ladder_arm in LADDER_ARMS:
                fn = ladder_fns[ladder_arm]
                observed = dict(fn(dict(stored)))
                ladder_results.append({
                    "width": int(stored["width"]), "arm": SELECT_ARM,
                    "graph_seed": int(stored["graph_seed"]),
                    "block_seed": int(stored["block_seed"]),
                    "call_idx": int(stored["call_idx"]),
                    "ladder_arm": ladder_arm,
                    "exact": _as_bool(observed.get("exact")),
                    "syndrome_ok": _as_bool(observed.get("syndrome_ok")),
                    "iterations": _as_int(observed.get("iterations")),
                    "belief_provenance": str(
                        observed.get("belief_provenance", "")),
                    "wall_s": float(observed.get("wall_s", 0.0)),
                })
    arm_stats = [summarize_arm(ladder_results, arm) for arm in LADDER_ARMS]
    ranking = rank_material_arms(arm_stats)
    terminal = (T_ENGINEERING_BLOCKED if engineering_reason
                else (T_ENGINEERING_BLOCKED if blocked is not None
                      else route_terminal({s["arm"]: s for s in arm_stats})))
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn()) if rss_fn is not None else 0
    scientific_calls = len(replay_results) + len(ladder_results)
    return {
        "plan_calls": len(plan), "replay_calls": len(replay_results),
        "ladder_calls": len(ladder_results),
        "scientific_calls": scientific_calls,
        "blocked": blocked, "replay_results": replay_results,
        "ladder_results": ladder_results, "arm_stats": arm_stats,
        "ranking": ranking, "terminal": terminal,
        "engineering_reason": engineering_reason or "",
        "wall_s": wall_s, "peak_rss_bytes": peak_rss,
    }


# --------------------------------------------------------------------------- #
# Production binder (accepted targets only; called solely under explicit auth)
# --------------------------------------------------------------------------- #
def bind_production() -> dict[str, Callable]:
    """Bind the four frozen call shapes from the accepted binders unchanged.

    RL90 replays the accepted cold row-layered shape (max_iter90); RL360 and
    damping-0.7 call the same accepted row-layered target with ``max_iter=360``
    (damping is the existing parameter, NOT tuned); flooding-360 calls the
    accepted flooding target with ``max_iter=360``. Each wrapper exposes its
    exact production target as ``.target``.
    """
    rl_binds = x3rl.bind_row_layered_decoders()
    sched_binds = x3sched.bind_schedule_decoders()
    rl_target = rl_binds["TARGET"].target
    flood_target = sched_binds["FLOODING"].target

    def replay_rl90(h_matrix, prior_pq, syndrome):
        return rl_target(h_matrix, prior_pq, syndrome, max_iter=90,
                         damping_alpha=1.0, warm_beliefs=None, field=None)

    def rl360(h_matrix, prior_pq, syndrome):
        return rl_target(h_matrix, prior_pq, syndrome, max_iter=360,
                         damping_alpha=1.0, warm_beliefs=None, field=None)

    def rl360_damp07(h_matrix, prior_pq, syndrome):
        return rl_target(h_matrix, prior_pq, syndrome, max_iter=360,
                         damping_alpha=0.7, warm_beliefs=None, field=None)

    def flood360(h_matrix, prior_pq, syndrome):
        return flood_target(h_matrix, prior_pq, syndrome, max_iter=360,
                            field=None)

    replay_rl90.target = rl_target  # type: ignore[attr-defined]
    rl360.target = rl_target  # type: ignore[attr-defined]
    rl360_damp07.target = rl_target  # type: ignore[attr-defined]
    flood360.target = flood_target  # type: ignore[attr-defined]
    return {REPLAY_ARM_ID: replay_rl90,
            "ROW_LAYERED_360_ALPHA_1": rl360,
            "ROW_LAYERED_360_ALPHA_0_7": rl360_damp07,
            "FLOODING_360_ALPHA_1": flood360}


# Re-exported D12 reconstruction entry (import, not copy).
build_graph = d12.build_graph


# --------------------------------------------------------------------------- #
# Minimal never-overwrite root writer + fail-closed verifier (D1306)
# --------------------------------------------------------------------------- #
SELECTION_COLUMNS = ("call_idx", "width", "arm", "graph_seed", "block_seed",
                     "batch_id", "exact", "syndrome_ok", "iterations",
                     "status", "belief_provenance")
REPLAY_COLUMNS = ("width", "arm", "graph_seed", "block_seed", "call_idx",
                  "replay_arm", "exact", "syndrome_ok", "iterations",
                  "belief_provenance", "wall_s", "match", "mismatch_field")
LADDER_COLUMNS = ("width", "arm", "graph_seed", "block_seed", "call_idx",
                  "ladder_arm", "exact", "syndrome_ok", "iterations",
                  "belief_provenance", "wall_s")


def _write_csv(path: Path, columns: Sequence[str],
               rows: Sequence[Mapping[str, Any]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _budget_meta() -> dict[str, Any]:
    return {
        "scientific_calls": SCIENTIFIC_CALL_CEILING,
        "setup_calls": SETUP_CALL_CEILING,
        "wall_s": WALL_BUDGET_S,
        "per_call_s": PER_CALL_BUDGET_S,
        "rss_bytes": RSS_BUDGET_BYTES,
        "processes": 1,
        "retry": False, "resume": False, "repair": False,
        "seed_search": False, "tuning": False,
    }


def write_root(out_root: str | Path, *,
               selection: Sequence[Mapping[str, Any]],
               outcome: Mapping[str, Any],
               model_f_root: str,
               setup_calls: int,
               log_lines: Sequence[str] | None = None) -> dict[str, Any]:
    """Persist one fresh minimal D13 root; refuse any overwrite.

    ``outcome`` is the ``run_readiness`` result. Never overwrites: an
    existing path raises via the shared refusal (imported, not copied).
    """
    resolved = d12.refuse_out_root(out_root)
    violations = validate_selection(selection)
    if violations:
        raise ValueError("refusing root write: %s" % violations[0])
    summary = {
        "schema": "v72p2d13_l055_decoder_ladder_summary_v1",
        "change_id": CHANGE_ID, "cycle": CYCLE_ID,
        "claim_ceiling": CLAIM_CEILING,
        "terminal": outcome["terminal"],
        "selection": {"total": len(selection),
                      "n128": sum(1 for r in selection
                                  if int(r["width"]) == 128),
                      "n256": sum(1 for r in selection
                                  if int(r["width"]) == 256)},
        "arm_stats": list(outcome["arm_stats"]),
        "ranking": list(outcome["ranking"]),
        "blocked": outcome["blocked"],
        "replay_calls": outcome["replay_calls"],
        "ladder_calls": outcome["ladder_calls"],
        "scientific_calls": outcome["scientific_calls"],
        "planned_calls": outcome["plan_calls"],
        "setup_calls": int(setup_calls),
        "engineering_reason": outcome.get("engineering_reason", ""),
        "wall_s": float(outcome.get("wall_s", 0.0)),
        "peak_rss_bytes": int(outcome.get("peak_rss_bytes", 0)),
        "budget_violations": [],
        "l1_only": True, "batch_id": D12_BATCH_ID,
        "model_f_root": str(model_f_root),
        "input_root": INPUT_ROOT,
        "out_root": str(resolved), "budgets": _budget_meta(),
    }
    if outcome["scientific_calls"] > SCIENTIFIC_CALL_CEILING:
        summary["budget_violations"].append(
            "scientific calls exceed ceiling")
    if int(setup_calls) > SETUP_CALL_CEILING:
        summary["budget_violations"].append("setup calls exceed ceiling")
    if float(outcome.get("wall_s", 0.0)) > WALL_BUDGET_S:
        summary["budget_violations"].append("wall budget exceeded")
    if int(outcome.get("peak_rss_bytes", 0)) >= RSS_BUDGET_BYTES:
        summary["budget_violations"].append("RSS budget exceeded")
    resolved.mkdir(parents=True)
    _write_json(resolved / "manifest.json", {
        "schema": "v72p2d13_l055_decoder_ladder_manifest_v1",
        "change_id": CHANGE_ID, "cycle": CYCLE_ID,
        "claim_ceiling": CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "model_f_root": str(model_f_root), "out_root": str(resolved),
        "input_root": INPUT_ROOT, "l1_only": True,
        "batch_id": D12_BATCH_ID,
        "field": {"q": d12.Q, "poly": d12.POLY,
                  "factory": "GF2mField.create(32)"},
        "selection_arm": SELECT_ARM,
        "selection_count": len(selection),
        "replay_arm": REPLAY_ARM_ID,
        "ladder_arms": list(LADDER_ARMS),
        "ladder_config": {k: dict(v) for k, v in LADDER_CONFIG.items()},
        "binder_map": dict(BINDER_MAP),
        "budgets": _budget_meta(),
        "setup_calls": int(setup_calls),
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": AUTHORIZATION,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    _write_csv(resolved / "selection.csv", SELECTION_COLUMNS, selection)
    _write_csv(resolved / "replay_records.csv", REPLAY_COLUMNS,
               outcome["replay_results"])
    _write_csv(resolved / "ladder_records.csv", LADDER_COLUMNS,
               outcome["ladder_results"])
    _write_json(resolved / "summary.json", summary)
    lines = list(log_lines or []) + [
        "D13 terminal=%s replay=%d ladder=%d setup=%d"
        % (outcome["terminal"], outcome["replay_calls"],
           outcome["ladder_calls"], int(setup_calls))]
    with open(resolved / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("".join(line + "\n" for line in lines))
    return summary


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def verify_root(out_root: str | Path) -> bool:
    """Read-only fail-closed recomputation of a completed D13 root.

    Zero decoder calls. Checks selection, replay, calls, rescues, ranking,
    terminal and budgets. Prints ``VERIFY ...`` lines; returns pass/fail.
    """
    root = Path(out_root)
    violations: list[str] = []
    if not root.is_dir():
        print("VERIFY root missing: %s" % root)
        return False
    names = sorted(p.name for p in root.iterdir())
    if names != sorted(EVIDENCE_FILES):
        print("VERIFY evidence files mismatch: %s" % names)
        return False
    try:
        manifest = json.loads((root / "manifest.json").read_text("utf-8"))
        summary = json.loads((root / "summary.json").read_text("utf-8"))
        selection = _read_csv_rows(root / "selection.csv")
        replay_rows = _read_csv_rows(root / "replay_records.csv")
        ladder_rows = _read_csv_rows(root / "ladder_records.csv")
    except Exception as exc:
        print("VERIFY unreadable evidence: %r" % (exc,))
        return False

    if manifest.get("change_id") != CHANGE_ID \
            or manifest.get("input_root") != INPUT_ROOT:
        violations.append("manifest change/input-root mismatch")
    if manifest.get("batch_id") != D12_BATCH_ID \
            or summary.get("batch_id") != D12_BATCH_ID:
        violations.append("batch_id tag mismatch (predecessor boundary)")
    if list(manifest.get("ladder_arms", [])) != list(LADDER_ARMS):
        violations.append("manifest ladder arms != frozen three arms")
    if summary.get("terminal") not in TERMINALS:
        violations.append("summary terminal %r not in frozen terminals"
                          % (summary.get("terminal"),))

    stored_by_key = {(int(r["width"]), int(r["graph_seed"]),
                      int(r["call_idx"]), int(r["block_seed"])): r
                     for r in selection}
    violations.extend(validate_selection(selection))

    if len(replay_rows) != EXPECTED_TOTAL:
        violations.append("replay rows %d != frozen 56" % len(replay_rows))
    replay_mismatch = 0
    for index, row in enumerate(replay_rows):
        key = (int(row["width"]), int(row["graph_seed"]),
               int(row["call_idx"]), int(row["block_seed"]))
        stored = stored_by_key.get(key)
        if stored is None:
            violations.append("replay row %d not in frozen selection" % index)
            continue
        observed = {"width": row["width"], "arm": row["arm"],
                    "graph_seed": row["graph_seed"],
                    "block_seed": row["block_seed"],
                    "call_idx": row["call_idx"],
                    "exact": row["exact"], "syndrome_ok": row["syndrome_ok"],
                    "iterations": row["iterations"],
                    "belief_provenance": row["belief_provenance"]}
        mismatch = compare_replay(stored, observed)
        if mismatch is not None:
            replay_mismatch += 1
            if replay_mismatch == 1:
                violations.append("replay row %d mismatch on %s "
                                  "(first mismatch blocks ladder)"
                                  % (index, mismatch))
        try:
            wall = float(row.get("wall_s", "0") or 0.0)
        except ValueError:
            violations.append("replay row %d wall_s not numeric" % index)
            wall = 0.0
        if wall < 0.0 or wall > PER_CALL_BUDGET_S:
            violations.append("replay row %d per-call wall out of budget"
                              % index)

    if replay_mismatch == 0 and len(ladder_rows) != EXPECTED_TOTAL * 3:
        violations.append("ladder rows %d != frozen 168"
                          % len(ladder_rows))
    if replay_mismatch > 0 and ladder_rows:
        violations.append("ladder calls present despite replay block")
    ladder_norm: list[dict[str, Any]] = []
    for index, row in enumerate(ladder_rows):
        key = (int(row["width"]), int(row["graph_seed"]),
               int(row["call_idx"]), int(row["block_seed"]))
        if key not in stored_by_key:
            violations.append("ladder row %d not in frozen selection" % index)
        if str(row.get("ladder_arm")) not in LADDER_ARMS:
            violations.append("ladder row %d arm %r not frozen"
                              % (index, row.get("ladder_arm")))
        try:
            exact = _as_bool(row.get("exact"))
            syndrome_ok = _as_bool(row.get("syndrome_ok"))
            iterations = _as_int(row.get("iterations"))
        except ValueError:
            violations.append("ladder row %d non-scalar metric" % index)
            continue
        if str(row.get("belief_provenance")) != CHECK_UPDATED:
            violations.append("ladder row %d provenance %r != CHECK_UPDATED"
                              % (index, row.get("belief_provenance")))
        if exact and not syndrome_ok:
            violations.append("ladder row %d exact without syndrome_ok "
                              "(metric isolation)" % index)
        max_iter = LADDER_CONFIG[str(row.get("ladder_arm"))]["max_iter"] \
            if str(row.get("ladder_arm")) in LADDER_CONFIG else 360
        if not 0 <= iterations <= max_iter:
            violations.append("ladder row %d iterations out of range" % index)
        try:
            wall = float(row.get("wall_s", "0") or 0.0)
        except ValueError:
            violations.append("ladder row %d wall_s not numeric" % index)
            wall = 0.0
        if wall < 0.0 or wall > PER_CALL_BUDGET_S:
            violations.append("ladder row %d per-call wall out of budget"
                              % index)
        ladder_norm.append({"width": int(row["width"]),
                            "ladder_arm": str(row.get("ladder_arm")),
                            "exact": exact, "syndrome_ok": syndrome_ok,
                            "iterations": iterations,
                            "belief_provenance": str(
                                row.get("belief_provenance"))})

    recomputed_stats = [summarize_arm(ladder_norm, arm)
                        for arm in LADDER_ARMS]
    for stat in recomputed_stats:
        stored = next((s for s in summary.get("arm_stats", [])
                       if s.get("arm") == stat["arm"]), None)
        if stored is None:
            violations.append("summary arm_stats missing %s" % stat["arm"])
            continue
        for field in ("total", "n128", "n256", "calls", "gate"):
            if stored.get(field) != stat[field]:
                violations.append("summary %s %s stored=%r recomputed=%r"
                                  % (stat["arm"], field, stored.get(field),
                                     stat[field]))
    if list(summary.get("ranking", [])) != rank_material_arms(
            recomputed_stats):
        violations.append("summary ranking stored != recomputed")
    expected_terminal = route_terminal(
        {s["arm"]: s for s in recomputed_stats},
        summary.get("engineering_reason", ""))
    if replay_mismatch > 0:
        if summary.get("terminal") != T_ENGINEERING_BLOCKED:
            violations.append("blocked replay requires %s, stored=%r"
                              % (T_ENGINEERING_BLOCKED,
                                 summary.get("terminal")))
    elif summary.get("terminal") != expected_terminal:
        violations.append("terminal stored=%r recomputed=%r"
                          % (summary.get("terminal"), expected_terminal))

    scientific = int(summary.get("scientific_calls", -1))
    if scientific != len(replay_rows) + len(ladder_rows):
        violations.append("summary scientific_calls %r != stored rows"
                          % summary.get("scientific_calls"))
    if scientific > SCIENTIFIC_CALL_CEILING:
        violations.append("stored calls exceed scientific ceiling")
    setup_calls = summary.get("setup_calls")
    if not isinstance(setup_calls, int) or isinstance(setup_calls, bool) \
            or not 0 <= setup_calls <= SETUP_CALL_CEILING:
        violations.append("setup calls %r outside 0..%d"
                          % (setup_calls, SETUP_CALL_CEILING))
    try:
        wall_s = float(summary.get("wall_s", -1.0))
    except (TypeError, ValueError):
        wall_s = -1.0
    if wall_s < 0.0 or wall_s > WALL_BUDGET_S:
        violations.append("wall budget exceeded or missing")
    try:
        peak_rss = int(summary.get("peak_rss_bytes", -1))
    except (TypeError, ValueError):
        peak_rss = -1
    if peak_rss < 0 or peak_rss >= RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded or missing")
    if bool(summary.get("l1_only")) is not True:
        violations.append("l1_only flag not true")
    if summary.get("budget_violations"):
        violations.append("root carries budget violations: %r"
                          % (summary.get("budget_violations"),))

    print("VERIFY checked_selection=%d checked_replay=%d checked_ladder=%d "
          "violations=%d" % (len(selection), len(replay_rows),
                             len(ladder_rows), len(violations)))
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    ok = not violations
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return ok


# --------------------------------------------------------------------------- #
# PLAN_ONLY reconstruction metadata (D1309: stdout only, zero decoder calls)
# --------------------------------------------------------------------------- #
def plan_only_metadata(input_root: str | Path = INPUT_ROOT) -> dict[str, Any]:
    """Read-only reconstruction metadata for all 56 (no decoder, no root).

    Reads the frozen D12 ``decoder_records.csv`` read-only, selects the 56,
    and reports deterministic per-identity reconstruction metadata (degree
    cell, coefficient seed, Model-F prior-chain descriptor, GF32/poly37,
    cold init) plus the 224-entry plan summary. Binds no decoder, loads no
    Model-F chain, creates no root.
    """
    root = Path(input_root)
    records: list[dict[str, str]] = []
    if root.is_dir():
        with open(root / "decoder_records.csv", newline="",
                  encoding="utf-8") as fh:
            records = list(csv.DictReader(fh))
    selected = select_l055_failures(records)
    violations = validate_selection(selected)
    plan = build_ladder_plan(selected) if not violations else []
    identities = []
    for width, graph_seed, call_idx, block_seed in sorted(
            selection_identities(selected)):
        cell = d12.degree_cell(SELECT_ARM, int(width))
        identities.append({
            "width": int(width), "arm": SELECT_ARM,
            "graph_seed": int(graph_seed), "call_idx": int(call_idx),
            "block_seed": int(block_seed),
            "degree": {"n": cell["n"], "m": cell["m"], "E": cell["E"],
                       "var_counts": cell["var_counts"],
                       "check_counts": cell["check_counts"]},
            "coefficient_seed": int(d12.coefficient_seed(int(width),
                                                         int(graph_seed))),
            "coefficient_rule": "v10_seed(d10:coeff:{width}:{graph_seed})",
            "prior": {"chain": "accepted CAL-only Model-F chain "
                               "(descriptor only; chain NOT loaded)",
                      "model_f_root": d12.MODEL_F_INPUT_ROOT},
            "field": {"q": d12.Q, "poly": d12.POLY,
                      "factory": "GF2mField.create(32)"},
            "init": {"warm_beliefs": None, "schedule": "cold"},
            "baseline": {"exact": False, "syndrome_ok": False,
                         "iterations": BASELINE_ITERATIONS,
                         "belief_provenance": CHECK_UPDATED},
        })
    future = Path(FUTURE_ROOT)
    return {
        "change_id": CHANGE_ID, "mode": "PLAN_ONLY",
        "input_root": str(input_root), "input_root_exists": root.is_dir(),
        "selection": {"total": len(selected),
                      "n128": sum(1 for r in selected
                                  if int(r["width"]) == 128),
                      "n256": sum(1 for r in selected
                                  if int(r["width"]) == 256)},
        "identities": identities,
        "plan_calls": len(plan),
        "replay_calls": len([e for e in plan if e["kind"] == "replay"]),
        "ladder_calls": len([e for e in plan if e["kind"] == "ladder"]),
        "decoder_calls": 0,
        "future_root": FUTURE_ROOT,
        "future_root_absent": not future.exists(),
        "claim_ceiling": CLAIM_CEILING,
        "violations": violations,
    }
