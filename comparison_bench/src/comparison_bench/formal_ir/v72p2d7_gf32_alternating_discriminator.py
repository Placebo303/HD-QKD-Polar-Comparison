"""D7-H minimal two-transfer alternating cross-layer discriminator core (R1A1).

Smallest alternating schedule built on the certified D7-G code-factor
extrinsic contract.  For every frozen ``(f, seed)`` identity a three-stage
chain runs once, sequentially, in the frozen order::

    STAGE 0  SOURCE_L1_MARGINAL    cold decode L1 from its channel marginal
                                   (the only unconditional mandatory call)
    STAGE 1  FORWARD_L1_TO_L2      invoked only if STAGE 0 yields finite,
                                   shape-valid, non-crashed, exact
                                   CHECK_EXTRINSIC; reference endpoint
                                   L1_exact AND L2_exact
    STAGE 2  BACKWARD_L2_TO_L1     invoked only if STAGE 1 yields the same
                                   admissible extrinsic; candidate endpoint
                                   L2_exact AND L1_return_exact

32 identities x 3 stages = 96 scheduled slots; 32 unconditional mandatory
STAGE 0 calls plus up to 2 gated calls per identity.  A blocked stage is a
recorded non-invocation (scalar accounting in ``arm_pairs.csv`` /
``stratum_summary.csv``), never a replacement, retry, or fabricated result,
and it blocks every downstream stage of that identity.  Nothing is
transferred back into a layer from its own posterior: the only transport
message is the explicit ``CHECK_EXTRINSIC`` code-factor extrinsic of the
previous stage, passed through the certified D7-G helper
``require_check_extrinsic_for_transfer``; the posterior
``softmax(final_beliefs)`` path is never a transfer message (cavity rule).

Row-layered only GF(32) poly 37, cold start, ``max_iter=90``,
``damping_alpha=1.0``.  No flooding, no oracle, no CAL/VAL, no real/raw, no
third transfer, no convergence iteration.  The joint comes only through the
accepted ``prepare_model_f_prior_candidate`` chain with per-Bob-column
smoothing; the legacy per-cell builder is statically and behaviorally
unreachable.  D5 / D7-C / D7-E / D7-F are import-only upstream and are never
modified.

This module performs no scientific decoder call and reads no real Model-F
content unless explicitly authorized; tests inject fake joint tensors,
blocks, mothers, decoders, clock and RSS through the DI boundary.
``import``, ``--help``, ``--dry-run``, ``--verify`` and unauthorized runs
bind no decoder, read no Model-F and create no root.
"""

from __future__ import annotations

import csv
import importlib.util as _ilu
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

try:  # normal package import (repo-relative local source on sys.path)
    from comparison_bench.formal_ir import (
        v72p2d7_gf32_reverse_order_discriminator as d7f,
    )
except ModuleNotFoundError:  # file-layout fallback: same sibling file only
    _D7F_PATH = (Path(__file__).resolve().parent
                 / "v72p2d7_gf32_reverse_order_discriminator.py")
    _D7F_SPEC = _ilu.spec_from_file_location(
        "v72p2d7_gf32_reverse_order_discriminator", str(_D7F_PATH))
    if _D7F_SPEC is None or _D7F_SPEC.loader is None:
        raise ImportError("cannot load sibling D7-F module at %s" % (_D7F_PATH,))
    d7f = _ilu.module_from_spec(_D7F_SPEC)
    sys.modules["v72p2d7_gf32_reverse_order_discriminator"] = d7f
    _D7F_SPEC.loader.exec_module(d7f)

d7e = d7f.d7e
d7c = d7f.d7c
d5 = d7f.d5

# --------------------------------------------------------------------------
# Frozen constants (D7-H R1A1 prereg; must not change without an OpenSpec
# revision).  Matrix / mothers / estimator / RSS telemetry are the accepted
# D7-C/D7-E/F contract reused through these narrow aliases.
# --------------------------------------------------------------------------
Q = d7f.Q
N = d7f.N
BOB_DIM = d7f.BOB_DIM
N_A = d7f.N_A
MODEL_F_ROOT = d7f.MODEL_F_ROOT

F_VALUES = d7f.F_VALUES
L1_ROWS = d7f.L1_ROWS
L2_ROWS = d7f.L2_ROWS
ROWS = d7f.ROWS
BLOCK_SEEDS = d7f.BLOCK_SEEDS
L1_GRAPH_SEED = d7f.L1_GRAPH_SEED
L2_GRAPH_SEED = d7f.L2_GRAPH_SEED
L1_K_MIN = d7f.L1_K_MIN
L2_K_MIN = d7f.L2_K_MIN

LAMBDA_STAR = d7f.LAMBDA_STAR
DECODER_FLOOR = d7f.DECODER_FLOOR
MAX_ITER = d7f.MAX_ITER
DAMPING_ALPHA = d7f.DAMPING_ALPHA

# Frozen three-stage chain: (stage, condition, layer, dispatch role).
STAGE_ORDER = ("SOURCE_L1_MARGINAL", "FORWARD_L1_TO_L2", "BACKWARD_L2_TO_L1")
STAGE_SPEC = {
    "SOURCE_L1_MARGINAL": (0, "L1_MARGINAL", "L1", "SOURCE"),
    "FORWARD_L1_TO_L2": (1, "L2_TRANSFER", "L2", "TARGET"),
    "BACKWARD_L2_TO_L1": (2, "L1_RETURN_TRANSFER", "L1", "TARGET"),
}
# Direction key of the certified D7-E/F mixer for the gated stages.
STAGE_DIRECTION = {1: "L1_TO_L2", 2: "L2_TO_L1"}
TRANSFER_DIRECTIONS = ("L1_TO_L2", "L2_TO_L1")
# Designated-syndrome owner of every invocation (L1 is decoded twice).
STAGE_LAYER = {0: "L1", 1: "L2", 2: "L1"}
SYNDROME_OWNER = {0: "L1", 1: "L2", 2: "L1"}

STAGE_COUNT = 3
IDENTITY_COUNT = len(F_VALUES) * len(BLOCK_SEEDS)
SLOT_COUNT = IDENTITY_COUNT * STAGE_COUNT
MANDATORY_CALLS = IDENTITY_COUNT       # STAGE 0 only; unconditional
MAX_CALLS = SLOT_COUNT                 # 32 x 3 hard cap
COMPLETE_CHAIN_MIN = 12                # coverage floor per f (12/16)

PER_CALL_WATCHDOG_S = 120.0
STORED_WALL_LIMIT_S = 1500.0
OUTER_WATCHDOG_S = 1800.0
OUTER_GRACE_S = 30.0
RSS_LIMIT_BYTES = 2 * 1024**3

D7H_AUTH_KEY = "d7h_execution_authorized"
STATE_REL_PATH = ("docs/research_cycles/"
                  "V72P2D7-GF32-ALTERNATING-DISCRIMINATOR/cycle_state.yaml")

# Frozen run terminals T1..T10 (exact strings, exact priority).
TERMINALS = (
    "D7_H_PRE_EXECUTION_BLOCKED",
    "D7_H_WATCHDOG_TIMEOUT_VOID",
    "D7_H_NONFINITE_OR_CRASH_BLOCKED",
    "D7_H_RESOURCE_OVERRUN",
    "D7_H_INCOMPLETE_MATRIX_BLOCKED",
    "D7_H_PROVENANCE_COVERAGE_BLOCKED",
    "D7_H_ALTERNATING_STRONG_LIFT",
    "D7_H_ALTERNATING_WEAK_LIFT",
    "D7_H_ALTERNATING_REGRESSION",
    "D7_H_NO_USEFUL_ALTERNATING_LIFT",
)
(T_PRE_EXEC, T_WATCHDOG, T_CRASH, T_RESOURCE, T_INCOMPLETE, T_COVERAGE,
 T_STRONG, T_WEAK, T_REGRESSION, T_NO_LIFT) = TERMINALS

# Frozen paired stratum labels (first-match order in ``classify_stratum``).
S_COVERAGE = "COVERAGE_BLOCKED"
S_REGRESSION = "ALTERNATING_REGRESSION"
S_STRONG = "STRONG_ALTERNATING_LIFT"
S_WEAK = "WEAK_ALTERNATING_LIFT"
S_NONE = "NO_ALTERNATING_LIFT"
STRATUM_LABELS = (S_COVERAGE, S_REGRESSION, S_STRONG, S_WEAK, S_NONE)

COVERAGE_OK = "COVERAGE_OK"

# Certified D7-G extrinsic-provenance tokens.  Pinned by tests to the
# accepted v35 tokens; the transfer gate itself delegates to the accepted
# lazy helper, never to these literals.
EXTRINSIC_NO_CHECK_EVIDENCE = "NO_CHECK_EVIDENCE"
EXTRINSIC_CHECK_EXTRINSIC = "CHECK_EXTRINSIC"
EXTRINSIC_WARM_START_UNSPECIFIED = "WARM_START_UNSPECIFIED"
EXTRINSIC_PROVENANCE_TOKENS = (
    EXTRINSIC_NO_CHECK_EVIDENCE,
    EXTRINSIC_CHECK_EXTRINSIC,
    EXTRINSIC_WARM_START_UNSPECIFIED,
)

# Named deterministic gate verdicts / blocked reasons (scalar accounting).
ELIGIBLE = "ELIGIBLE"
BLOCK_STAGE_CRASH = "STAGE_CRASH"
BLOCK_STAGE_NONFINITE = "STAGE_NONFINITE"
BLOCK_NO_CHECK_EVIDENCE = "EXTRINSIC_NO_CHECK_EVIDENCE"
BLOCK_WARM_START = "EXTRINSIC_WARM_START_UNSPECIFIED"
BLOCK_SHAPE_OR_NONFINITE = "EXTRINSIC_SHAPE_OR_NONFINITE"
BLOCK_UNKNOWN = "EXTRINSIC_UNKNOWN_OR_MISSING"

SEVEN_FILES = ("manifest.json", "decoder_records.csv", "arm_pairs.csv",
               "stratum_summary.csv", "summary.json", "report.md",
               "command_log.txt")

RECORD_FIELDS = [
    "slot_idx", "f", "seed", "stage", "stage_name", "role", "condition",
    "layer", "rows", "n", "exact", "syndrome_ok", "syndrome_owner",
    "iterations", "status", "finite", "symbol_errors", "unsatisfied_checks",
    "wall_s", "rss_bytes", "belief_max_prob", "belief_mean_true_p",
    "belief_mean_entropy", "beliefs_conditioned", "current_belief_label",
    "belief_provenance", "extrinsic_provenance", "extrinsic_shape_ok",
    "transfer_eligible", "transfer_block_reason",
]
PAIR_FIELDS = [
    "pair_idx", "f", "seed", "identity", "n", "l1_rows", "l2_rows",
    "decoder_config",
    "stage0_slot_idx", "stage1_slot_idx", "stage2_slot_idx",
    "stage0_transfer_eligible", "stage0_block_reason",
    "stage1_transfer_eligible", "stage1_block_reason",
    "chain_complete", "blocked_at_stage1", "blocked_at_stage2",
    "l1_exact", "l1_syndrome_ok", "l2_exact", "l2_syndrome_ok",
    "l1_return_exact", "l1_return_syndrome_ok",
    "reference_both_layers_exact", "candidate_both_layers_exact",
]
STRATUM_FIELDS = [
    "stratum_idx", "f", "blocks",
    "stage0_invoked", "stage1_invoked", "stage2_invoked",
    "complete_chain_count", "blocked_at_stage1", "blocked_at_stage2",
    "candidate_only", "reference_only", "both", "neither",
    "nonfinite_count", "crash_count", "stratum_label", "coverage_status",
]

CHANGE_NAME = "v72p2d7-alternating-discriminator"
_ESTIMATOR_ID = d7f._ESTIMATOR_ID
_MOTHER_EXPR = d7f._MOTHER_EXPR
_DECODER_IDS = dict(d7f._DECODER_IDS)
_DECODER_CONFIG = ("row_layered_fftqspa;GF32_poly37;cold;max_iter=90;"
                   "damping_alpha=1.0;warm_beliefs=None;field=None")
_CALL_ORDER = ("for f in [1.0, 1.2]: for seed in 2026091300..2026091315: "
               "SOURCE_L1_MARGINAL, "
               "FORWARD_L1_TO_L2 (gated on STAGE 0 CHECK_EXTRINSIC), "
               "BACKWARD_L2_TO_L1 (gated on STAGE 1 CHECK_EXTRINSIC)")

# Formal/dev roots that must never be an output target (name-based guard).
PROTECTED_ROOTS = tuple(d7f.PROTECTED_ROOTS) + (
    "workspace/d7_d_schedule_discriminator_"
    "64660d16-397d-4ef3-8454-3066d27c12c7",
    "workspace/d7_f_reverse_order_discriminator_"
    "b6d62184-fd15-483d-947e-01ea66ddc13c",
)
OUT_ROOT_PREFIX = "d7_h_alternating_discriminator_"

_EXECUTION_CONSUMED = False  # single-use guard within one process


class NotAuthorizedError(PermissionError):
    """Raised when a run is entered without the D7-H authorization key."""


class PreflightBlocked(ValueError):
    """Pre-first-call refusal; carries the frozen T1 terminal."""

    terminal = T_PRE_EXEC


# --------------------------------------------------------------------------
# State / path contract
# --------------------------------------------------------------------------

def repo_root_path(repo_root=None) -> Path:
    """Repository root derived from ``__file__`` (no cwd assumption)."""
    return d7f.repo_root_path(repo_root)


def cycle_state_path(repo_root=None) -> Path:
    return repo_root_path(repo_root) / STATE_REL_PATH


read_cycle_state = d7f.read_cycle_state


def is_authorized(state) -> bool:
    try:
        return bool(dict(state).get(D7H_AUTH_KEY, False))
    except Exception:
        return False


def _require_authorized(authorized: bool) -> None:
    if not authorized:
        raise NotAuthorizedError(
            "%s: D7-H execution is not authorized; refusing before decoder "
            "bind, Model-F read, or root creation" % (T_PRE_EXEC,))


model_f_root_matches = d7f.model_f_root_matches


def validate_production_out_root(out_root, repo_root=None) -> Path:
    """Frozen CLI root contract: direct fresh child ``workspace/<prefix><uuid>``.

    Pure path check (no side effects).  DI/qualification roots are task-owned
    temp roots outside the repository and are not subject to this CLI gate.
    """
    cand = Path(str(out_root))
    if not cand.is_absolute():
        cand = repo_root_path(repo_root) / cand
    cand = cand.resolve()
    ws = (repo_root_path(repo_root) / "workspace").resolve()
    if cand.parent != ws:
        raise ValueError("refusing out-root outside workspace/: %s" % (cand,))
    if not cand.name.startswith(OUT_ROOT_PREFIX) or cand.name == OUT_ROOT_PREFIX:
        raise ValueError(
            "refusing out-root name %r (expected %s<uuid>)"
            % (cand.name, OUT_ROOT_PREFIX))
    return cand


def _refuse_protected(out_root: Path, repo: Path) -> None:
    try:
        rp = Path(out_root).resolve()
    except Exception:
        raise ValueError("refusing unresolvable out_root %r" % (str(out_root),))
    for rel in PROTECTED_ROOTS:
        if rp == (repo / rel).resolve():
            raise ValueError("refusing protected root %s" % (rel,))
    for rel in ("comparison_bench/outputs_comparison", "results"):
        base = (repo / rel).resolve()
        if rp == base or str(rp).startswith(str(base) + os.sep):
            raise ValueError("refusing formal/outputs tree %s" % (rel,))


# --------------------------------------------------------------------------
# RSS (Linux/WSL VmHWM only; fail closed, stdlib-only, no fallback)
# --------------------------------------------------------------------------

_PROC_SELF_STATUS_PATH = d7f._PROC_SELF_STATUS_PATH
parse_vmhwm_rss_bytes = d7f.parse_vmhwm_rss_bytes
_probe_rss_valid = d7f._probe_rss_valid


def _read_proc_self_status_text():
    """Raw ``/proc/self/status`` text, read once per call; None on failure."""
    try:
        with open(_PROC_SELF_STATUS_PATH, "r", encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return None


def get_rss_bytes():
    """Current-process peak RSS bytes from ``VmHWM``; None when unavailable."""
    return parse_vmhwm_rss_bytes(_read_proc_self_status_text())


# --------------------------------------------------------------------------
# Frozen 96-slot chain matrix
# --------------------------------------------------------------------------

def frozen_slots() -> list:
    """All 96 frozen slots in the frozen order; ``slot_idx`` 1-based.

    Outer ``f`` in ``[1.0, 1.2]``, seeds ``2026091300..2026091315``
    ascending, three stages per ``(f, seed)`` in ``STAGE_ORDER``.
    """
    slots = []
    for f in F_VALUES:
        for seed in BLOCK_SEEDS:
            for stage_name in STAGE_ORDER:
                stage, condition, layer, role = STAGE_SPEC[stage_name]
                slots.append({
                    "slot_idx": len(slots) + 1,
                    "f": float(f),
                    "seed": int(seed),
                    "stage": int(stage),
                    "stage_name": stage_name,
                    "role": role,
                    "condition": condition,
                    "layer": layer,
                    "rows": int(ROWS[layer][float(f)]),
                    "n": N,
                    "gated": bool(stage > 0),
                })
    return slots


# --------------------------------------------------------------------------
# Narrow D7-C reuse: joint / prior / mother / estimator / block preparation
# --------------------------------------------------------------------------

condition_prior_qn = d7f.condition_prior_qn
decoder_prior = d7f.decoder_prior
build_mother = d7f.build_mother
build_joint = d7f.build_joint
_default_model_f_loader = d7f._default_model_f_loader


def prepare_inputs(*, joint=None, model_f_root=None, model_f_loader=None,
                   block_sampler=None, mothers=None, repo=None) -> dict:
    """Frozen preparation order (D7-C reuse) plus the 96-slot chain matrix.

    Model-F -> accepted estimator -> J -> mothers -> 16 blocks -> frozen
    slots.  All inputs are injectable for fake qualification; the production
    path (``joint=None``) loads only the accepted Model-F root through the
    D5 loader chain.
    """
    try:
        ctx = d7c.prepare_inputs(
            joint=joint, model_f_root=model_f_root,
            model_f_loader=model_f_loader, block_sampler=block_sampler,
            mothers=mothers, repo=repo)
    except d7c.PreflightBlocked as exc:
        raise PreflightBlocked("%s: %s" % (T_PRE_EXEC, exc)) from exc
    ctx = dict(ctx)
    ctx.pop("identities", None)
    ctx["slots"] = frozen_slots()
    if len(ctx["slots"]) != SLOT_COUNT:
        raise AssertionError("frozen slot matrix must hold %d slots"
                             % (SLOT_COUNT,))
    return ctx


# --------------------------------------------------------------------------
# Certified D7-G transfer helper (lazy bind; never at import)
# --------------------------------------------------------------------------

_load_v35 = d7e._load_v35


def unusable_extrinsic_error():
    """The accepted refusal type (lazy v35 bind; never at import)."""
    return _load_v35().UnusableExtrinsicError


def require_check_extrinsic_for_transfer(extrinsic_log_beliefs,
                                         extrinsic_provenance, *,
                                         consumer, expected_n=None):
    """Certified D7-G gate: only explicit finite shape-correct
    ``CHECK_EXTRINSIC`` is stably softmaxed for transport; everything else
    raises ``UnusableExtrinsicError`` before any cross-layer prior exists."""
    return _load_v35().require_check_extrinsic_for_transfer(
        extrinsic_log_beliefs, extrinsic_provenance, consumer=consumer,
        expected_n=expected_n, q=Q)


def _result_extrinsic(result):
    """Raw ``(extrinsic_log_beliefs, extrinsic_provenance)`` of one return."""
    if isinstance(result, dict):
        return (result.get("extrinsic_log_beliefs"),
                result.get("extrinsic_provenance"))
    return (getattr(result, "extrinsic_log_beliefs", None),
            getattr(result, "extrinsic_provenance", None))


def extrinsic_shape_ok(extrinsic_log_beliefs, n_pos) -> bool:
    """Scalar shape/finite verdict mirroring the helper's array conditions."""
    if extrinsic_log_beliefs is None:
        return False
    try:
        arr = np.asarray(extrinsic_log_beliefs, dtype=np.float64)
    except Exception:
        return False
    return bool(arr.ndim == 2 and arr.shape == (int(n_pos), Q)
                and np.all(np.isfinite(arr)))


def extrinsic_block_reason(provenance) -> str:
    if provenance == EXTRINSIC_NO_CHECK_EVIDENCE:
        return BLOCK_NO_CHECK_EVIDENCE
    if provenance == EXTRINSIC_WARM_START_UNSPECIFIED:
        return BLOCK_WARM_START
    if provenance == EXTRINSIC_CHECK_EXTRINSIC:
        return BLOCK_SHAPE_OR_NONFINITE
    return BLOCK_UNKNOWN


def chain_gate(*, status, finite, extrinsic_log_beliefs,
               extrinsic_provenance, expected_n, consumer):
    """One stage's output gate -> ``(transport_q or None, eligible, reason)``.

    Fail-closed: crash/nonfinite scalars block first; then the certified
    D7-G helper is the sole authority for the message.  Source hard exact is
    not consulted anywhere.  Unexpected error types propagate loudly.
    """
    if str(status).startswith("crash:"):
        return None, False, BLOCK_STAGE_CRASH
    if not bool(finite):
        return None, False, BLOCK_STAGE_NONFINITE
    try:
        q = require_check_extrinsic_for_transfer(
            extrinsic_log_beliefs, extrinsic_provenance, consumer=consumer,
            expected_n=expected_n)
    except unusable_extrinsic_error():
        return None, False, extrinsic_block_reason(extrinsic_provenance)
    return q, True, ELIGIBLE


# --------------------------------------------------------------------------
# Transfer math (frozen D7-E formula; transient q, never persisted) and
# decoder dispatch (dual roles, DI) with lazy production bind
# --------------------------------------------------------------------------

build_transfer_prior = d7f.build_transfer_prior
transfer_prior_l1_to_l2 = d7f.transfer_prior_l1_to_l2
transfer_prior_l2_to_l1 = d7f.transfer_prior_l2_to_l1

dispatch_decoder = d7f.dispatch_decoder
bind_row_layered_decoders = d7f.bind_row_layered_decoders


# --------------------------------------------------------------------------
# Per-call evaluation (scalar records; exact/syndrome isolation)
# --------------------------------------------------------------------------

_result_provenance = d7f._result_provenance
_belief_label = d7f._belief_label
_as_bool = d7f._as_bool
_as_float = d7f._as_float
_as_int = d7f._as_int
_scalar = d7f._scalar
_record_row = d7f._record_row
_jsonable = d7f._jsonable
_utc_now = d7f._utc_now


def evaluate_call(slot: dict, h_prefix: np.ndarray, block: dict,
                  syndrome: np.ndarray, result, wall_s: float,
                  rss_bytes) -> dict:
    """One completed call -> scalar record with isolated exact/syndrome.

    ``transfer_eligible`` / ``transfer_block_reason`` are filled by the
    chain loop from the certified gate; this function only extracts the
    scalar extrinsic verdict of the return.
    """
    layer = slot["layer"]
    x_true = np.asarray(block["u1"] if layer == "L1" else block["u2"],
                        dtype=np.int64)
    x_hat, reported, iterations, beliefs, status = d7c._parse_decoder_result(result)
    if x_hat.shape != x_true.shape:
        raise ValueError("decoder x_hat shape %r != truth %r"
                         % (x_hat.shape, x_true.shape))
    exact = bool(np.array_equal(x_hat, x_true))
    observed = d5._gf32_syndrome(h_prefix, x_hat)
    unsatisfied = int(np.count_nonzero(
        observed != np.asarray(syndrome, dtype=np.int64)))
    syndrome_ok = bool(reported and unsatisfied == 0)
    symbol_errors = int(np.count_nonzero(x_hat != x_true))
    finite_x = bool(np.all(np.isfinite(x_hat.astype(np.float64))))
    finite_bel = bool(beliefs is not None
                      and np.all(np.isfinite(np.asarray(beliefs,
                                                        dtype=np.float64))))
    finite = bool(finite_x and finite_bel)
    diagnostics = d7c._belief_diagnostics(beliefs, x_true, finite)
    extrinsic, extrinsic_prov = _result_extrinsic(result)
    provenance = _result_provenance(result)
    return {
        "slot_idx": int(slot["slot_idx"]),
        "f": float(slot["f"]),
        "seed": int(slot["seed"]),
        "stage": int(slot["stage"]),
        "stage_name": slot["stage_name"],
        "role": slot["role"],
        "condition": slot["condition"],
        "layer": layer,
        "rows": int(slot["rows"]),
        "n": int(slot["n"]),
        "exact": exact,
        "syndrome_ok": syndrome_ok,
        "syndrome_owner": layer,
        "iterations": int(iterations),
        "status": str(status),
        "finite": finite,
        "symbol_errors": symbol_errors,
        "unsatisfied_checks": unsatisfied,
        "wall_s": float(wall_s),
        "rss_bytes": int(rss_bytes) if rss_bytes is not None else "",
        "belief_max_prob": diagnostics["belief_max_prob"],
        "belief_mean_true_p": diagnostics["belief_mean_true_p"],
        "belief_mean_entropy": diagnostics["belief_mean_entropy"],
        "beliefs_conditioned": bool(int(iterations) > 0),
        "current_belief_label": _belief_label(int(iterations)),
        "belief_provenance": provenance if isinstance(provenance, str) else "",
        "extrinsic_provenance": (extrinsic_prov
                                 if isinstance(extrinsic_prov, str) else ""),
        "extrinsic_shape_ok": bool(extrinsic_shape_ok(
            extrinsic, int(x_true.shape[0]))),
        "transfer_eligible": "",
        "transfer_block_reason": "",
    }


def crash_record(slot: dict, exc: BaseException, wall_s: float,
                 rss_bytes) -> dict:
    """A decoder exception is an attempted-but-not-completed call (no retry)."""
    return {
        "slot_idx": int(slot["slot_idx"]),
        "f": float(slot["f"]),
        "seed": int(slot["seed"]),
        "stage": int(slot["stage"]),
        "stage_name": slot["stage_name"],
        "role": slot["role"],
        "condition": slot["condition"],
        "layer": slot["layer"],
        "rows": int(slot["rows"]),
        "n": int(slot["n"]),
        "exact": False,
        "syndrome_ok": False,
        "syndrome_owner": slot["layer"],
        "iterations": "",
        "status": "crash:%s" % (type(exc).__name__,),
        "finite": False,
        "symbol_errors": "",
        "unsatisfied_checks": "",
        "wall_s": float(wall_s),
        "rss_bytes": int(rss_bytes) if rss_bytes is not None else "",
        "belief_max_prob": "",
        "belief_mean_true_p": "",
        "belief_mean_entropy": "",
        "beliefs_conditioned": "",
        "current_belief_label": "",
        "belief_provenance": "",
        "extrinsic_provenance": "",
        "extrinsic_shape_ok": False,
        "transfer_eligible": False,
        "transfer_block_reason": BLOCK_STAGE_CRASH,
    }


def _stop_after(record, stored_wall_s, rss_valid, rss_bytes, wall):
    """Frozen stop priority after one recorded call (watchdog/crash/resource)."""
    if wall > PER_CALL_WATCHDOG_S:
        return T_WATCHDOG
    if str(record["status"]).startswith("crash:") or not record["finite"]:
        return T_CRASH
    if (stored_wall_s > STORED_WALL_LIMIT_S or not rss_valid
            or rss_bytes >= RSS_LIMIT_BYTES):
        return T_RESOURCE
    return None


# --------------------------------------------------------------------------
# Sequential 96-slot chain loop (no retry / resume / concurrency)
# --------------------------------------------------------------------------

def execute_chain(context: dict, decoder_fns, *, clock=None,
                  rss_probe=None) -> dict:
    """Run the frozen 96-slot chain once, sequentially, stopping on the first
    higher-priority budget/validity stop.

    Every identity invokes its STAGE 0 decoder exactly once.  A gated stage
    is invoked only when the cached transport distribution of the same
    identity's previous stage exists (gate passed); otherwise it is a
    recorded non-invocation (no call, no wall cost) and downstream stages
    cascade.  No replacement, retry or resume.  Nothing is transferred back
    from a stage to its own layer: each gated prior consumes only the
    previous stage's certified ``CHECK_EXTRINSIC`` transport.
    """
    clock = clock or time.perf_counter
    rss_probe = rss_probe or get_rss_bytes
    records = []
    transport = {}  # (f, seed) -> q of the most recently completed stage
    stored_wall = 0.0
    stop = None
    for slot in context["slots"]:
        if len(records) >= MAX_CALLS:  # hard cap; matrix holds 96 slots
            break
        f = float(slot["f"])
        seed = int(slot["seed"])
        stage = int(slot["stage"])
        layer = slot["layer"]
        key = (f, seed)
        block = context["blocks"][seed]
        h_prefix = context["mothers"][layer][:int(slot["rows"])]
        x_true = np.asarray(block["u1"] if layer == "L1" else block["u2"],
                            dtype=np.int64)
        if stage > 0:
            q_prev = transport.get(key)
            if q_prev is None:
                continue  # blocked: recorded non-invocation, never a call
            prior_pq = build_transfer_prior(context["joint"],
                                            STAGE_DIRECTION[stage],
                                            block["bob"], q_prev)
        else:
            prior_qn = condition_prior_qn(context["joint"], slot["condition"],
                                          block)
            prior_pq = decoder_prior(prior_qn)
        syndrome = d5._gf32_syndrome(h_prefix, x_true)

        t0 = clock()
        result, exc = None, None
        try:
            result = dispatch_decoder(slot["role"], decoder_fns, h_prefix,
                                      prior_pq, syndrome)
        except Exception as caught:  # isolated as a crash, never retried
            exc = caught
        wall = max(0.0, float(clock() - t0))
        rss_bytes, rss_valid = _probe_rss_valid(rss_probe)

        if exc is not None:
            record = crash_record(slot, exc, wall,
                                  rss_bytes if rss_valid else None)
            transport[key] = None
        else:
            try:
                record = evaluate_call(slot, h_prefix, block, syndrome,
                                       result, wall,
                                       rss_bytes if rss_valid else None)
            except Exception as caught:
                record = crash_record(slot, caught, wall,
                                      rss_bytes if rss_valid else None)
                transport[key] = None
            else:
                extrinsic, extrinsic_prov = _result_extrinsic(result)
                q, eligible, reason = chain_gate(
                    status=record["status"], finite=record["finite"],
                    extrinsic_log_beliefs=extrinsic,
                    extrinsic_provenance=extrinsic_prov,
                    expected_n=int(record["n"]),
                    consumer="D7-H %s" % (slot["stage_name"],))
                record["transfer_eligible"] = bool(eligible)
                record["transfer_block_reason"] = reason
                transport[key] = q if eligible else None
        records.append(record)
        stored_wall += wall
        stop = _stop_after(record, stored_wall, rss_valid, rss_bytes, wall)
        if stop is not None:
            break
    return {"records": records, "stop": stop, "stored_wall_s": stored_wall}


# --------------------------------------------------------------------------
# Chain rows, strata and terminals (shared by run and verifier)
# --------------------------------------------------------------------------

def _record_complete(record) -> bool:
    """Non-crash, finite, parseable-completed call."""
    if record is None:
        return False
    if str(record.get("status", "")).startswith("crash:"):
        return False
    return (bool(_as_bool(record.get("finite")))
            and _as_int(record.get("iterations")) is not None)


def recompute_transfer_eligible(record) -> bool:
    """Scalar recomputation of one stage's output gate from its record."""
    if str(record.get("status", "")).startswith("crash:"):
        return False
    if not _as_bool(record.get("finite")):
        return False
    if record.get("extrinsic_provenance") != EXTRINSIC_CHECK_EXTRINSIC:
        return False
    return _as_bool(record.get("extrinsic_shape_ok"))


def recompute_block_reason(record) -> str:
    """Scalar recomputation of the recorded gate verdict/reason."""
    if str(record.get("status", "")).startswith("crash:"):
        return BLOCK_STAGE_CRASH
    if not _as_bool(record.get("finite")):
        return BLOCK_STAGE_NONFINITE
    provenance = record.get("extrinsic_provenance", "")
    if provenance != EXTRINSIC_CHECK_EXTRINSIC:
        return extrinsic_block_reason(provenance)
    if not _as_bool(record.get("extrinsic_shape_ok")):
        return BLOCK_SHAPE_OR_NONFINITE
    return ELIGIBLE


def compute_chain_rows(records) -> list:
    """One reference/candidate row per identity in the frozen matrix order.

    Blocked-at-stage1 counts gate refusals of STAGE 0 (STAGE 1 never
    invoked); blocked-at-stage2 counts STAGE 2 non-invocations, including
    the cascade of a stage-1 block.  A crashed or truncated stage is neither
    a fabricated call nor a gate block: it is excluded from every invocation
    count and the run terminal judges it.  L1 is decoded twice (STAGE 0 and
    STAGE 2) and both designated-syndrome outcomes are recorded separately.
    """
    by_identity = {}
    for record in records:
        key = (float(record["f"]), int(record["seed"]))
        by_identity.setdefault(key, {})[int(record["stage"])] = record
    rows = []
    for f in F_VALUES:
        for seed in BLOCK_SEEDS:
            f = float(f)
            stages = by_identity.get((f, int(seed)), {})
            s0, s1, s2 = stages.get(0), stages.get(1), stages.get(2)
            complete = all(_record_complete(rec) for rec in (s0, s1, s2))
            blocked1 = bool(
                s0 is not None and _record_complete(s0)
                and not _as_bool(s0["transfer_eligible"]) and s1 is None)
            blocked2 = bool(
                blocked1 or (s1 is not None and _record_complete(s1)
                             and not _as_bool(s1["transfer_eligible"])
                             and s2 is None))
            l1_exact = bool(s0 is not None and _as_bool(s0["exact"]))
            l1_syn = bool(s0 is not None and _as_bool(s0["syndrome_ok"]))
            l2_exact = bool(s1 is not None and _as_bool(s1["exact"]))
            l2_syn = bool(s1 is not None and _as_bool(s1["syndrome_ok"]))
            l1r_exact = bool(s2 is not None and _as_bool(s2["exact"]))
            l1r_syn = bool(s2 is not None and _as_bool(s2["syndrome_ok"]))
            rows.append({
                "pair_idx": len(rows) + 1,
                "f": f,
                "seed": int(seed),
                "identity": ("f=%s;seed=%d;n=%d;L1_rows=%d;L2_rows=%d"
                             % (f, int(seed), N, L1_ROWS[f], L2_ROWS[f])),
                "n": N,
                "l1_rows": int(L1_ROWS[f]),
                "l2_rows": int(L2_ROWS[f]),
                "decoder_config": _DECODER_CONFIG,
                "stage0_slot_idx": (int(s0["slot_idx"])
                                    if s0 is not None else ""),
                "stage1_slot_idx": (int(s1["slot_idx"])
                                    if s1 is not None else ""),
                "stage2_slot_idx": (int(s2["slot_idx"])
                                    if s2 is not None else ""),
                "stage0_transfer_eligible": (
                    _as_bool(s0["transfer_eligible"])
                    if s0 is not None and _record_complete(s0) else ""),
                "stage0_block_reason": (
                    s0["transfer_block_reason"] if blocked1 else ""),
                "stage1_transfer_eligible": (
                    _as_bool(s1["transfer_eligible"])
                    if s1 is not None and _record_complete(s1) else ""),
                "stage1_block_reason": (
                    s1["transfer_block_reason"]
                    if (s1 is not None and _record_complete(s1)
                        and not _as_bool(s1["transfer_eligible"])
                        and s2 is None) else ""),
                "chain_complete": complete,
                "blocked_at_stage1": blocked1,
                "blocked_at_stage2": blocked2,
                "l1_exact": l1_exact,
                "l1_syndrome_ok": l1_syn,
                "l2_exact": l2_exact,
                "l2_syndrome_ok": l2_syn,
                "l1_return_exact": l1r_exact,
                "l1_return_syndrome_ok": l1r_syn,
                "reference_both_layers_exact": bool(l1_exact and l2_exact),
                "candidate_both_layers_exact": bool(l2_exact and l1r_exact),
            })
    return rows


def classify_stratum(*, complete_chain_count, candidate_only,
                     reference_only) -> str:
    """Frozen first-match paired label per f (R1A1 packet 8).

    Labels are computed on complete three-stage chains only; coverage below
    12/16 short-circuits.  Synthetic diagnostic labels, not FER thresholds.
    """
    if int(complete_chain_count) < COMPLETE_CHAIN_MIN:
        return S_COVERAGE
    if int(reference_only) >= 2 and int(candidate_only) == 0:
        return S_REGRESSION
    if int(candidate_only) >= 4 and int(reference_only) == 0:
        return S_STRONG
    if int(candidate_only) > int(reference_only):
        return S_WEAK
    return S_NONE


def compute_strata(records, chain_rows) -> list:
    """Two frozen stratum rows (one per f) with first-match labels."""
    strata = []
    for f in F_VALUES:
        f = float(f)
        f_records = [r for r in records if float(r["f"]) == f]
        f_rows = [row for row in chain_rows if float(row["f"]) == f]
        complete = [row for row in f_rows if _as_bool(row["chain_complete"])]
        candidate_only = reference_only = both = neither = 0
        for row in complete:
            cand = _as_bool(row["candidate_both_layers_exact"])
            ref = _as_bool(row["reference_both_layers_exact"])
            if cand and not ref:
                candidate_only += 1
            elif ref and not cand:
                reference_only += 1
            elif cand and ref:
                both += 1
            else:
                neither += 1
        crashes = int(sum(1 for r in f_records
                          if str(r["status"]).startswith("crash:")))
        nonfinite = int(sum(1 for r in f_records
                            if (not _as_bool(r["finite"]))
                            and not str(r["status"]).startswith("crash:")))
        label = classify_stratum(complete_chain_count=len(complete),
                                 candidate_only=candidate_only,
                                 reference_only=reference_only)
        strata.append({
            "stratum_idx": len(strata) + 1,
            "f": f,
            "blocks": len(BLOCK_SEEDS),
            "stage0_invoked": int(sum(1 for r in f_records
                                      if int(r["stage"]) == 0)),
            "stage1_invoked": int(sum(1 for r in f_records
                                      if int(r["stage"]) == 1)),
            "stage2_invoked": int(sum(1 for r in f_records
                                      if int(r["stage"]) == 2)),
            "complete_chain_count": len(complete),
            "blocked_at_stage1": int(sum(
                1 for row in f_rows if _as_bool(row["blocked_at_stage1"]))),
            "blocked_at_stage2": int(sum(
                1 for row in f_rows if _as_bool(row["blocked_at_stage2"]))),
            "candidate_only": candidate_only,
            "reference_only": reference_only,
            "both": both,
            "neither": neither,
            "nonfinite_count": nonfinite,
            "crash_count": crashes,
            "stratum_label": label,
            "coverage_status": (S_COVERAGE if label == S_COVERAGE
                                else COVERAGE_OK),
        })
    return strata


def classify_terminal(agg: dict) -> str:
    """Frozen T1..T10 first-applicable terminal selection."""
    if agg.get("pre_blocked"):
        return T_PRE_EXEC
    if agg.get("watchdog_timeout"):
        return T_WATCHDOG
    if agg.get("crash_nonfinite"):
        return T_CRASH
    if agg.get("resource_overrun"):
        return T_RESOURCE
    if agg.get("incomplete"):
        return T_INCOMPLETE
    if agg.get("coverage_blocked"):
        return T_COVERAGE
    labels = agg.get("strata") or {}
    strong = {float(f): labels.get(float(f)) == S_STRONG for f in F_VALUES}
    weak = {float(f): labels.get(float(f)) == S_WEAK for f in F_VALUES}
    regress = {float(f): labels.get(float(f)) == S_REGRESSION
               for f in F_VALUES}
    ordered = [float(f) for f in F_VALUES]
    if any(strong[f] and not regress[other]
           for f in ordered for other in ordered if other != f):
        return T_STRONG
    if any(weak.values()) and not any(regress.values()):
        return T_WEAK
    if any(regress.values()):
        return T_REGRESSION
    return T_NO_LIFT


def _mandatory_present(records) -> int:
    return int(sum(1 for r in records if int(r["stage"]) == 0))


def terminal_from_records(records, chain_rows, stratum_rows) -> str:
    """Recompute the run terminal from scalar records + chain/stratum rows."""
    watchdog = any((_as_float(r["wall_s"]) or 0.0) > PER_CALL_WATCHDOG_S
                   for r in records)
    crash = any(str(r["status"]).startswith("crash:") or not _as_bool(r["finite"])
                for r in records)
    stored = sum(v for v in (_as_float(r["wall_s"]) for r in records)
                 if v is not None)
    rss_over = False
    for r in records:
        value = _as_float(r["rss_bytes"])
        if value is not None and value >= RSS_LIMIT_BYTES:
            rss_over = True
        if value is None and not str(r["status"]).startswith("crash:"):
            rss_over = True
    resource = bool(stored > STORED_WALL_LIMIT_S or rss_over)
    labels = {float(row["f"]): row.get("stratum_label", "")
              for row in stratum_rows}
    coverage = any(int(row["complete_chain_count"]) < COMPLETE_CHAIN_MIN
                   for row in stratum_rows)
    return classify_terminal({
        "pre_blocked": False,
        "watchdog_timeout": bool(watchdog),
        "crash_nonfinite": bool(crash),
        "resource_overrun": resource,
        "incomplete": _mandatory_present(records) < MANDATORY_CALLS,
        "coverage_blocked": bool(coverage),
        "strata": labels,
    })


# --------------------------------------------------------------------------
# Seven-file writer and read-only verifier
# --------------------------------------------------------------------------

def write_root(out_root, manifest, records, paired, strata, summary,
               command_str="") -> list:
    """Write exactly the seven frozen scalar files into a fresh root."""
    rows = [_record_row(r, RECORD_FIELDS) for r in records]
    paired_rows = [_record_row(r, PAIR_FIELDS) for r in paired]
    stratum_rows = [_record_row(r, STRATUM_FIELDS) for r in strata]
    out = Path(out_root)
    if out.exists():
        if out.is_dir() and any(p.is_dir() for p in out.iterdir()):
            raise ValueError("no subdirectories allowed in evidence root")
        raise FileExistsError("refusing overwrite of existing root %s" % (out,))
    out.mkdir(parents=True, exist_ok=False)
    for name in SEVEN_FILES:
        if (out / name).exists():
            raise FileExistsError("refusing overwrite %s" % (name,))
    with open(out / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(_jsonable(manifest), fh, indent=2, sort_keys=True)
    with open(out / "decoder_records.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=RECORD_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    with open(out / "arm_pairs.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=PAIR_FIELDS)
        writer.writeheader()
        for row in paired_rows:
            writer.writerow(row)
    with open(out / "stratum_summary.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=STRATUM_FIELDS)
        writer.writeheader()
        for row in stratum_rows:
            writer.writerow(row)
    with open(out / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(_jsonable(summary), fh, indent=2, sort_keys=True)
    with open(out / "report.md", "w", encoding="utf-8") as fh:
        fh.write("# D7-H minimal two-transfer alternating discriminator\n\n")
        fh.write("terminal: %s\n" % (summary.get("terminal"),))
        fh.write("stage0_completed: %s\n" % (summary.get("stage0_completed"),))
        fh.write("stage1_invoked: %s\n" % (summary.get("stage1_invoked"),))
        fh.write("stage2_invoked: %s\n" % (summary.get("stage2_invoked"),))
        fh.write("complete_chain_count: %s\n"
                 % (summary.get("complete_chain_count"),))
        fh.write("blocked_at_stage1: %s\n"
                 % (summary.get("blocked_at_stage1"),))
        fh.write("blocked_at_stage2: %s\n"
                 % (summary.get("blocked_at_stage2"),))
        fh.write("stored_wall_s: %s\n" % (summary.get("stored_wall_s"),))
        for row in stratum_rows:
            fh.write("f=%s: %s (%s)\n" % (
                row["f"], row["stratum_label"], row["coverage_status"]))
    with open(out / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write((command_str or "") + "\n")
        fh.write("outer_timeout: timeout -k %d %d\n"
                 % (OUTER_GRACE_S, OUTER_WATCHDOG_S))
        fh.write("terminal: %s\n" % (summary.get("terminal"),))
        fh.write("calls_attempted: %s\n"
                 % (summary.get("calls_attempted"),))
        fh.write("stored_wall_s: %s\n" % (summary.get("stored_wall_s"),))
    return sorted(SEVEN_FILES)


def _read_records(path):
    with open(str(path), "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != RECORD_FIELDS:
            raise ValueError("decoder_records.csv schema mismatch: %r"
                             % (reader.fieldnames,))
        return list(reader)


def _read_paired(path):
    with open(str(path), "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != PAIR_FIELDS:
            raise ValueError("arm_pairs.csv schema mismatch: %r"
                             % (reader.fieldnames,))
        return list(reader)


def _read_strata(path):
    with open(str(path), "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != STRATUM_FIELDS:
            raise ValueError("stratum_summary.csv schema mismatch: %r"
                             % (reader.fieldnames,))
        return list(reader)


def _check_manifest_contract(manifest, problems):
    expected = {
        "change": CHANGE_NAME,
        "contract": "R1",
        "estimator": _ESTIMATOR_ID,
        "lambda_star": LAMBDA_STAR,
        "model_f_root": MODEL_F_ROOT,
        "n": N,
        "f_values": [float(f) for f in F_VALUES],
        "stage_order": list(STAGE_ORDER),
        "transfer_directions": list(TRANSFER_DIRECTIONS),
        "block_seeds": [int(s) for s in BLOCK_SEEDS],
        "identity_count": IDENTITY_COUNT,
        "max_calls": MAX_CALLS,
        "mandatory_calls": MANDATORY_CALLS,
        "complete_chain_min": COMPLETE_CHAIN_MIN,
        "per_call_watchdog_s": PER_CALL_WATCHDOG_S,
        "stored_wall_limit_s": STORED_WALL_LIMIT_S,
        "outer_watchdog_s": OUTER_WATCHDOG_S,
        "outer_grace_s": OUTER_GRACE_S,
        "rss_limit_bytes": RSS_LIMIT_BYTES,
        "decoder_floor": DECODER_FLOOR,
        "max_iter": MAX_ITER,
        "damping_alpha": DAMPING_ALPHA,
        "decoder_config": _DECODER_CONFIG,
        "seven_files": list(SEVEN_FILES),
        "terminal_priority": list(TERMINALS),
        "call_order": _CALL_ORDER,
        "decoder_ids": dict(_DECODER_IDS),
    }
    for key, value in expected.items():
        if key not in manifest:
            problems.append("manifest missing %s" % (key,))
        elif manifest[key] != value:
            problems.append("manifest %s != frozen value" % (key,))
    if manifest.get("l1_rows") != {"1.0": L1_ROWS[1.0], "1.2": L1_ROWS[1.2]}:
        problems.append("manifest l1_rows mismatch")
    if manifest.get("l2_rows") != {"1.0": L2_ROWS[1.0], "1.2": L2_ROWS[1.2]}:
        problems.append("manifest l2_rows mismatch")
    if manifest.get("graph_seeds") != {"L1": L1_GRAPH_SEED, "L2": L2_GRAPH_SEED}:
        problems.append("manifest graph_seeds mismatch")
    if manifest.get("mothers") != _MOTHER_EXPR:
        problems.append("manifest mothers mismatch")


def _check_record_semantics(record, expected, problems):
    idx = record.get("slot_idx", "?")
    prefix = "record %s: " % (idx,)
    for key in ("slot_idx", "stage", "stage_name", "role", "condition",
                "layer", "rows", "n", "seed"):
        if str(record.get(key)) != str(expected[key]):
            problems.append(prefix + "identity %s mismatch" % (key,))
            return
    if _as_float(record.get("f")) != float(expected["f"]):
        problems.append(prefix + "identity f mismatch")
        return
    if record.get("syndrome_owner") != expected["layer"]:
        problems.append(prefix + "syndrome_owner must be the designated layer")
    provenance = record.get("extrinsic_provenance", "")
    if not isinstance(provenance, str):
        problems.append(prefix + "extrinsic_provenance must be a scalar string")
        return
    crash = str(record["status"]).startswith("crash:")
    if crash:
        if record["current_belief_label"] != "":
            problems.append(prefix + "crash record must carry an empty "
                                    "belief label")
        if _as_bool(record["finite"]):
            problems.append(prefix + "crash record must be nonfinite")
        if _as_bool(record.get("transfer_eligible")):
            problems.append(prefix + "crash record must not be transfer "
                                    "eligible")
        if record.get("transfer_block_reason") != BLOCK_STAGE_CRASH:
            problems.append(prefix + "crash record reason must be STAGE_CRASH")
        if record.get("extrinsic_shape_ok") not in ("", None, False, "False"):
            problems.append(prefix + "crash record must not carry a shape "
                                    "verdict")
        return
    iterations = _as_int(record["iterations"])
    if iterations is None or iterations < 0 or iterations > MAX_ITER:
        problems.append(prefix + "iterations out of range")
        return
    conditioned = _as_bool(record["beliefs_conditioned"])
    if conditioned != (iterations > 0):
        problems.append(prefix + "beliefs_conditioned must equal iterations > 0")
    label = record["current_belief_label"]
    expected_label = _belief_label(iterations)
    if label != expected_label:
        problems.append(prefix + "current_belief_label %r must be %r"
                        % (label, expected_label))
    if "posterior" in label.lower() or "app" in label.lower():
        problems.append(prefix + "posterior/APP label token is forbidden")
    exact = _as_bool(record["exact"])
    symbol_errors = _as_int(record["symbol_errors"])
    unsatisfied = _as_int(record["unsatisfied_checks"])
    if symbol_errors is None or unsatisfied is None:
        problems.append(prefix + "symbol_errors/unsatisfied_checks not "
                                "parseable")
        return
    if exact != (symbol_errors == 0):
        problems.append(prefix + "exact must equal symbol_errors == 0")
    if exact and unsatisfied != 0:
        problems.append(prefix + "exact record must have zero unsatisfied "
                                "checks")
    if _as_bool(record["syndrome_ok"]) and unsatisfied != 0:
        problems.append(prefix + "syndrome_ok record must have zero "
                                "unsatisfied checks")
    wall = _as_float(record["wall_s"])
    if wall is None or wall < 0:
        problems.append(prefix + "wall_s must be a nonnegative number")
    rss = record["rss_bytes"]
    if rss not in ("", None) and (_as_int(rss) is None or _as_int(rss) <= 0):
        problems.append(prefix + "rss_bytes must be positive or empty")
    recomputed = recompute_transfer_eligible(record)
    if _as_bool(record.get("transfer_eligible")) != recomputed:
        problems.append(prefix + "transfer_eligible does not recompute from "
                                "the CHECK_EXTRINSIC gate")
    if record.get("transfer_block_reason") != recompute_block_reason(record):
        problems.append(prefix + "transfer_block_reason does not recompute")
    for key, hi in (("belief_max_prob", 1.0), ("belief_mean_true_p", 1.0)):
        value = _as_float(record[key])
        if value is not None and not (0.0 <= value <= hi + 1e-12):
            problems.append(prefix + "%s out of range" % (key,))
    entropy = _as_float(record["belief_mean_entropy"])
    if entropy is not None and not (-1e-9 <= entropy <= math.log2(Q) + 1e-9):
        problems.append(prefix + "belief_mean_entropy out of range")


def _empty_scalar(value) -> bool:
    return value in ("", None)


def _scalar_equal(key: str, a, b) -> bool:
    if _empty_scalar(a) or _empty_scalar(b):
        return _empty_scalar(a) and _empty_scalar(b)
    if key in ("stage_name", "role", "condition", "layer", "stratum_label",
               "coverage_status", "identity", "decoder_config"):
        return str(a) == str(b)
    if key == "f" or key.endswith("_wall_s"):
        fa, fb = _as_float(a), _as_float(b)
        return fa is not None and fb is not None and abs(fa - fb) <= 1e-9
    if (key.endswith("_exact") or key.endswith("_syndrome_ok")
            or key.endswith("_transfer_eligible") or key == "chain_complete"
            or key.startswith("blocked_at_")):
        # CSV booleans may be written as bool or as int 0/1 (counts).
        return _flag(a) == _flag(b)
    ia, ib = _as_int(a), _as_int(b)
    if ia is not None and ib is not None:
        return ia == ib
    return str(a) == str(b)


def _flag(value) -> bool:
    if _as_bool(value):
        return True
    return _as_int(value) == 1


def _rows_equal_scalar(left, right, fields) -> bool:
    return all(_scalar_equal(key, left.get(key), right.get(key))
               for key in fields)


def _verify_walk(records, slots, problems):
    """Walk file records against frozen slots; blocked stages are the only
    skippable slots.  Returns nothing; appends every problem."""
    slot_map = {int(s["slot_idx"]): s for s in slots}
    by_slot = {}
    for record in records:
        idx = _as_int(record.get("slot_idx"))
        if idx is None or idx not in slot_map:
            problems.append("record with unknown slot_idx %r" % (idx,))
            continue
        if idx in by_slot:
            problems.append("duplicate slot_idx %s" % (idx,))
        by_slot[idx] = record
        _check_record_semantics(record, slot_map[idx], problems)
    idxs = [_as_int(r.get("slot_idx")) for r in records
            if _as_int(r.get("slot_idx")) is not None]
    if idxs != sorted(idxs):
        problems.append("records are not in frozen slot order")
    if idxs != sorted(set(idxs)):
        problems.append("slot_idx values repeat")
    groups = {}
    for record in records:
        key = (float(record["f"]), int(record["seed"]))
        groups.setdefault(key, {})[int(record["stage"])] = record
    for key, stages in groups.items():
        s0, s1 = stages.get(0), stages.get(1)
        if s1 is not None and not (
                s0 is not None and _record_complete(s0)
                and _as_bool(s0["transfer_eligible"])):
            problems.append("stage 1 invoked without an eligible completed "
                            "stage 0 at %r" % (key,))
        s2 = stages.get(2)
        if s2 is not None and not (
                s1 is not None and _record_complete(s1)
                and _as_bool(s1["transfer_eligible"])):
            problems.append("stage 2 invoked without an eligible completed "
                            "stage 1 at %r" % (key,))
    stored = 0.0
    stop_pos = None
    for position, record in enumerate(records):
        wall = _as_float(record.get("wall_s")) or 0.0
        stored += wall
        crash = (str(record.get("status", "")).startswith("crash:")
                 or not _as_bool(record.get("finite")))
        rss = _as_float(record.get("rss_bytes"))
        resource = bool(stored > STORED_WALL_LIMIT_S or rss is None
                        or (rss is not None and rss >= RSS_LIMIT_BYTES))
        if stop_pos is None:
            if wall > PER_CALL_WATCHDOG_S:
                stop_pos = position
            elif crash:
                stop_pos = position
            elif resource:
                stop_pos = position
    if stop_pos is not None and stop_pos != len(records) - 1:
        problems.append("records present after the first stop condition")


def _check_summary(summary, records, chain_rows, strata, problems):
    def _sum(field):
        return sum(1 for r in records if int(r["stage"]) == field)
    checks = [
        ("calls_attempted", len(records)),
        ("calls_completed", len(records)),
        ("calls_remaining", int(MAX_CALLS - len(records))),
        ("slots_scheduled", SLOT_COUNT),
        ("identities", IDENTITY_COUNT),
        ("stage0_completed", _sum(0)),
        ("stage1_invoked", _sum(1)),
        ("stage2_invoked", _sum(2)),
        ("complete_chain_count", int(sum(
            1 for row in chain_rows if _as_bool(row["chain_complete"])))),
        ("blocked_at_stage1", int(sum(
            1 for row in chain_rows if _as_bool(row["blocked_at_stage1"])))),
        ("blocked_at_stage2", int(sum(
            1 for row in chain_rows if _as_bool(row["blocked_at_stage2"])))),
        ("nonfinite_count", int(sum(
            1 for r in records
            if (not _as_bool(r["finite"]))
            and not str(r["status"]).startswith("crash:")))),
        ("crash_count", int(sum(1 for r in records
                                if str(r["status"]).startswith("crash:")))),
        ("watchdog_timeouts", int(sum(
            1 for r in records
            if (_as_float(r["wall_s"]) or 0.0) > PER_CALL_WATCHDOG_S))),
    ]
    for key, value in checks:
        if _as_int(summary.get(key)) != value:
            problems.append("summary %s does not recompute" % (key,))
    stored = sum(v for v in (_as_float(r["wall_s"]) for r in records)
                 if v is not None)
    if _as_float(summary.get("stored_wall_s")) is None or abs(
            float(summary.get("stored_wall_s")) - stored) > 1e-9:
        problems.append("summary stored_wall_s does not recompute")
    peak = max([v for v in (_as_int(r["rss_bytes"]) for r in records)
                if v is not None], default="")
    if summary.get("peak_rss_bytes") != peak:
        problems.append("summary peak_rss_bytes does not recompute")
    expected_labels = [
        {"stratum_idx": int(row["stratum_idx"]), "f": float(row["f"]),
         "stratum_label": row["stratum_label"]}
        for row in strata]
    if summary.get("strata") != expected_labels:
        problems.append("summary strata labels do not recompute")
    expected_stop = ""
    stored_run = 0.0
    for record in records:
        wall = _as_float(record.get("wall_s")) or 0.0
        stored_run += wall
        crash = (str(record.get("status", "")).startswith("crash:")
                 or not _as_bool(record.get("finite")))
        rss = _as_float(record.get("rss_bytes"))
        resource = bool(stored_run > STORED_WALL_LIMIT_S or rss is None
                        or (rss is not None and rss >= RSS_LIMIT_BYTES))
        if wall > PER_CALL_WATCHDOG_S:
            expected_stop = T_WATCHDOG
            break
        if crash:
            expected_stop = T_CRASH
            break
        if resource:
            expected_stop = T_RESOURCE
            break
    if summary.get("stop_terminal") != expected_stop:
        problems.append("summary stop_terminal does not recompute")
    for key, value in (("retries", 0), ("reruns", 0), ("resumes", 0)):
        if summary.get(key) != value:
            problems.append("summary %s must be 0" % (key,))


def _check_no_returned_evidence(records, pairs, problems):
    """Scalar invariants of the cavity rule, recomputed from the files.

    STAGE 2 may only exist behind a completed eligible STAGE 1 whose output
    was explicit ``CHECK_EXTRINSIC``; the L1 return is a distinct L1
    invocation with its own designated syndrome, and the reference/candidate
    endpoints share STAGE 1's L2 outcome rather than re-decoding it.
    """
    groups = {}
    for record in records:
        key = (float(record["f"]), int(record["seed"]))
        groups.setdefault(key, {})[int(record["stage"])] = record
    for key, stages in groups.items():
        s0, s1, s2 = stages.get(0), stages.get(1), stages.get(2)
        if s2 is None:
            continue
        if s1 is None or not _record_complete(s1) or not _as_bool(
                s1["transfer_eligible"]):
            problems.append("stage 2 present without an eligible completed "
                            "stage 1 at %r" % (key,))
        if s1 is not None and s1.get("extrinsic_provenance") != \
                EXTRINSIC_CHECK_EXTRINSIC:
            problems.append("stage 2 present without explicit "
                            "CHECK_EXTRINSIC stage 1 at %r" % (key,))
        if s2.get("layer") != "L1" or s2.get("syndrome_owner") != "L1":
            problems.append("stage 2 must be the L1 return decode at %r"
                            % (key,))
        if s1 is not None and s1.get("layer") != "L2":
            problems.append("stage 1 must be the L2 decode at %r" % (key,))
        if s0 is not None and s2.get("rows") != s0.get("rows"):
            problems.append("stage 0/2 L1 designated-syndrome row count "
                            "mismatch at %r" % (key,))
        if s0 is not None and s1 is not None and s0.get("n") != s1.get("n"):
            problems.append("identity n mismatch across stages at %r" % (key,))
    for pair in pairs:
        stage1_present = not _empty_scalar(pair.get("stage1_slot_idx"))
        if _as_bool(pair.get("chain_complete")) and not stage1_present:
            problems.append("complete pair without a stage 1 slot")
        if _as_bool(pair.get("candidate_both_layers_exact")) and not (
                _as_bool(pair.get("l2_exact"))
                and _as_bool(pair.get("l1_return_exact"))):
            problems.append("candidate both-layers must be the AND of l2 and "
                            "l1_return")


def _scan_scalar_text(out, problems):
    for name in ("decoder_records.csv", "arm_pairs.csv",
                 "stratum_summary.csv"):
        try:
            path = out / name
            with open(str(path), "r", encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    for key, value in row.items():
                        if value is None:
                            problems.append("%s: missing cell %s"
                                            % (name, key))
                            continue
                        if any(ch in value for ch in "[]{}"):
                            problems.append("%s: non-scalar payload in %s"
                                            % (name, key))
                        if "array(" in value or "dtype" in value:
                            problems.append("%s: array payload token in %s"
                                            % (name, key))
        except Exception as exc:
            problems.append("%s: unreadable (%r)" % (name, exc))


def verify_root(out_root) -> dict:
    """Read-only verification of a seven-file root (no decoder, no Model-F).

    Recomputes schema, frozen slot order, the unconditional STAGE 0 count,
    invoked STAGE 1/STAGE 2 counts, uniqueness, no replacement, pair
    identity, the CHECK_EXTRINSIC gate, exact/syndrome isolation, both-layer
    AND rules, per-invocation designated-syndrome accounting, the
    no-returned-evidence rule, labels, terminal, wall/RSS budgets and the
    manifest contract from the seven files alone.
    """
    out = Path(out_root)
    problems = []
    if not out.is_dir():
        return {"ok": False, "problems": ["root missing: %s" % (out,)],
                "records": 0}
    entries = sorted(p.name for p in out.iterdir())
    if entries != sorted(SEVEN_FILES):
        problems.append("files %r != %r" % (entries, sorted(SEVEN_FILES)))
    if any(p.is_dir() for p in out.iterdir()):
        problems.append("subdirectories present")
    try:
        manifest = json.loads((out / "manifest.json").read_text(
            encoding="utf-8"))
        summary = json.loads((out / "summary.json").read_text(
            encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "problems": problems + ["json: %r" % (exc,)],
                "records": 0}
    records, paired, strata = [], [], []
    try:
        records = _read_records(out / "decoder_records.csv")
        paired = _read_paired(out / "arm_pairs.csv")
        strata = _read_strata(out / "stratum_summary.csv")
    except Exception as exc:
        return {"ok": False, "problems": problems + ["csv: %r" % (exc,)],
                "records": 0}

    _check_manifest_contract(manifest, problems)
    _scan_scalar_text(out, problems)
    if len(records) > MAX_CALLS:
        problems.append("records exceed the %d-call cap" % (MAX_CALLS,))
    slots = frozen_slots()
    _verify_walk(records, slots, problems)
    mandatory = _mandatory_present(records)
    if mandatory < MANDATORY_CALLS:
        if summary.get("terminal") not in (T_WATCHDOG, T_CRASH, T_RESOURCE,
                                           T_INCOMPLETE):
            problems.append("truncated core matrix without a stop terminal")
    recomputed_paired = compute_chain_rows(records)
    if len(paired) != len(recomputed_paired):
        problems.append("arm_pairs.csv row count %d != recomputed %d"
                        % (len(paired), len(recomputed_paired)))
    else:
        for actual, expected in zip(paired, recomputed_paired):
            if not _rows_equal_scalar(actual, expected, PAIR_FIELDS):
                problems.append(
                    "arm row f=%s seed=%s does not recompute"
                    % (actual.get("f"), actual.get("seed")))
    recomputed_strata = compute_strata(records, recomputed_paired)
    if len(strata) != 2:
        problems.append("stratum_summary.csv row count %d != 2"
                        % (len(strata),))
    else:
        for actual, expected in zip(strata, recomputed_strata):
            if not _rows_equal_scalar(actual, expected, STRATUM_FIELDS):
                problems.append(
                    "stratum row %s (f=%s) does not recompute"
                    % (actual.get("stratum_idx"), actual.get("f")))
    recomputed_terminal = terminal_from_records(
        records, recomputed_paired, recomputed_strata)
    if summary.get("terminal") != recomputed_terminal:
        problems.append("summary terminal %r != recomputed %r"
                        % (summary.get("terminal"), recomputed_terminal))
    _check_summary(summary, records, recomputed_paired, recomputed_strata,
                   problems)
    _check_no_returned_evidence(records, recomputed_paired, problems)
    for key in ("report.md", "command_log.txt"):
        try:
            if not (out / key).read_text(encoding="utf-8").strip():
                problems.append("%s is empty" % (key,))
        except Exception:
            problems.append("%s is unreadable" % (key,))
    return {"ok": not problems, "problems": problems, "records": len(records),
            "terminal": summary.get("terminal")}


# --------------------------------------------------------------------------
# Manifest / summary builders and one-shot run
# --------------------------------------------------------------------------

def _build_manifest(*, out_root, model_f_files, authorization_consumed,
                    command_str, start_utc, end_utc, pid) -> dict:
    name = Path(out_root).name
    uuid = (name[len(OUT_ROOT_PREFIX):]
            if name.startswith(OUT_ROOT_PREFIX) else "")
    return {
        "change": CHANGE_NAME,
        "contract": "R1",
        "out_root_name": name,
        "uuid": uuid,
        "estimator": _ESTIMATOR_ID,
        "lambda_star": LAMBDA_STAR,
        "model_f_root": MODEL_F_ROOT,
        "model_f_files": list(model_f_files),
        "n": N,
        "f_values": [float(f) for f in F_VALUES],
        "stage_order": list(STAGE_ORDER),
        "transfer_directions": list(TRANSFER_DIRECTIONS),
        "l1_rows": {"1.0": L1_ROWS[1.0], "1.2": L1_ROWS[1.2]},
        "l2_rows": {"1.0": L2_ROWS[1.0], "1.2": L2_ROWS[1.2]},
        "block_seeds": [int(s) for s in BLOCK_SEEDS],
        "identity_count": IDENTITY_COUNT,
        "graph_seeds": {"L1": L1_GRAPH_SEED, "L2": L2_GRAPH_SEED},
        "mothers": dict(_MOTHER_EXPR),
        "decoder_ids": dict(_DECODER_IDS),
        "decoder_config": _DECODER_CONFIG,
        "max_iter": MAX_ITER,
        "damping_alpha": DAMPING_ALPHA,
        "decoder_floor": DECODER_FLOOR,
        "max_calls": MAX_CALLS,
        "mandatory_calls": MANDATORY_CALLS,
        "complete_chain_min": COMPLETE_CHAIN_MIN,
        "per_call_watchdog_s": PER_CALL_WATCHDOG_S,
        "stored_wall_limit_s": STORED_WALL_LIMIT_S,
        "outer_watchdog_s": OUTER_WATCHDOG_S,
        "outer_grace_s": OUTER_GRACE_S,
        "rss_limit_bytes": RSS_LIMIT_BYTES,
        "call_order": _CALL_ORDER,
        "seven_files": list(SEVEN_FILES),
        "terminal_priority": list(TERMINALS),
        "command": command_str,
        "start_utc": start_utc,
        "end_utc": end_utc,
        "pid": int(pid),
        "authorization_consumed": bool(authorization_consumed),
        "retries": 0,
        "reruns": 0,
        "resumes": 0,
    }


def _build_summary(loop, records, chain_rows, strata, terminal) -> dict:
    def _stage_count(stage):
        return int(sum(1 for r in records if int(r["stage"]) == stage))
    return {
        "terminal": terminal,
        "strata": [
            {"stratum_idx": int(row["stratum_idx"]), "f": float(row["f"]),
             "stratum_label": row["stratum_label"]}
            for row in strata],
        "slots_scheduled": SLOT_COUNT,
        "identities": IDENTITY_COUNT,
        "stage0_completed": _stage_count(0),
        "stage1_invoked": _stage_count(1),
        "stage2_invoked": _stage_count(2),
        "complete_chain_count": int(sum(
            1 for row in chain_rows if _as_bool(row["chain_complete"]))),
        "blocked_at_stage1": int(sum(
            1 for row in chain_rows if _as_bool(row["blocked_at_stage1"]))),
        "blocked_at_stage2": int(sum(
            1 for row in chain_rows if _as_bool(row["blocked_at_stage2"]))),
        "calls_attempted": len(records),
        "calls_completed": len(records),
        "calls_remaining": int(MAX_CALLS - len(records)),
        "nonfinite_count": int(sum(
            1 for r in records
            if (not _as_bool(r["finite"]))
            and not str(r["status"]).startswith("crash:"))),
        "crash_count": int(sum(1 for r in records
                               if str(r["status"]).startswith("crash:"))),
        "watchdog_timeouts": int(sum(
            1 for r in records
            if (_as_float(r["wall_s"]) or 0.0) > PER_CALL_WATCHDOG_S)),
        "stored_wall_s": float(loop["stored_wall_s"]),
        "peak_rss_bytes": max(
            [v for v in (_as_int(r["rss_bytes"]) for r in records)
             if v is not None], default=""),
        "stop_terminal": loop["stop"] or "",
        "retries": 0,
        "reruns": 0,
        "resumes": 0,
    }


def run_alternating_discriminator(*, out_root, model_f_root=None,
                                  decoder_fns=None, model_f_loader=None,
                                  joint=None, block_sampler=None, mothers=None,
                                  state=None, state_reader=None, clock=None,
                                  rss_probe=None, command_str="",
                                  repo_root=None) -> dict:
    """One frozen sequential run (production bind only when ``decoder_fns``
    is None and the authorization key is true)."""
    global _EXECUTION_CONSUMED
    if _EXECUTION_CONSUMED:
        raise NotAuthorizedError("D7-H authorization already consumed "
                                 "(no reuse)")
    repo = repo_root_path(repo_root)
    out = Path(out_root)

    if state is None:
        state = (state_reader or read_cycle_state)(cycle_state_path(repo))
    _require_authorized(is_authorized(state))

    if out.exists():
        raise FileExistsError("refusing overwrite of existing root %s" % (out,))
    _refuse_protected(out, repo)

    rss_probe = rss_probe or get_rss_bytes
    rss0, rss0_valid = _probe_rss_valid(rss_probe)
    if not rss0_valid:
        raise PreflightBlocked(
            "%s: RSS measurement must be finite and positive before the "
            "first scientific call (got %r)" % (T_PRE_EXEC, rss0))

    context = prepare_inputs(joint=joint, model_f_root=model_f_root,
                             model_f_loader=model_f_loader,
                             block_sampler=block_sampler, mothers=mothers,
                             repo=repo)

    production = decoder_fns is None
    if production:
        decoder_fns = bind_row_layered_decoders()
        _EXECUTION_CONSUMED = True

    start_utc = _utc_now()
    loop = execute_chain(context, decoder_fns, clock=clock,
                         rss_probe=rss_probe)
    records = loop["records"]
    paired = compute_chain_rows(records)
    strata = compute_strata(records, paired)
    terminal = terminal_from_records(records, paired, strata)
    summary = _build_summary(loop, records, paired, strata, terminal)
    manifest = _build_manifest(
        out_root=out, model_f_files=context["model_f_files"],
        authorization_consumed=production, command_str=command_str,
        start_utc=start_utc, end_utc=_utc_now(), pid=os.getpid())
    write_root(out, manifest, records, paired, strata, summary,
               command_str=command_str)
    return {"out_root": str(out), "terminal": terminal,
            "summary": summary, "records": len(records)}
