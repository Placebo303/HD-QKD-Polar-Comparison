"""D7-F paired reverse-order cross-layer discriminator core (frozen R1).

Paired complete-two-layer mechanism discriminator on the exact D7-E frozen
identities: for every ``(f, seed)`` two ordered arms run, each a source
marginal decode followed by at most one gated cold target decode whose
prior mixes the transient source APP approximation ``q`` (rowwise softmax
of the current log belief) with the accepted joint Model-F conditional::

    FORWARD_L1_TO_L2:  decode L1 marginal
                       -> gate -> transient P(U2|B,s1) -> cold decode L2
    REVERSE_L2_TO_L1:  decode L2 marginal
                       -> gate -> transient P(U1|B,s2) -> cold decode L1

128 scheduled slots: 64 mandatory source-marginal decoder calls plus up to
64 provenance-eligible transfer calls.  A blocked second stage is a recorded
non-invocation (counted in the stratum/summary blocked counts and identified
by its source record carrying ``transfer_eligible=False`` with the scalar
``belief_provenance`` token), never a replacement, retry or fake result.
There is no transfer back to the source layer within either arm.

Row-layered only GF(32) poly 37, cold start, ``max_iter=90``,
``damping_alpha=1.0``.  No schedule comparison, no oracle prior or decoder
call, no second decoding pass per arm, no returned belief consumed by any
other call, no estimator change: the joint comes only through the accepted
``prepare_model_f_prior_candidate`` / ``build_f_model_concentration`` chain
with per-Bob-column smoothing.  D5 / D7-C / D7-E are import-only upstream
and are never modified; D7-D is not imported at all.  More than two stages
stay blocked pending a cavity/extrinsic-message contract; none is encoded
here.

This module performs no scientific decoder call and reads no real Model-F
content unless explicitly authorized by the frozen execution packet; tests
inject fake joint tensors, blocks, mothers, decoders, clock and RSS through
the DI boundary.  ``import``, ``--help``, ``--dry-run``, ``--verify`` and
unauthorized runs bind no decoder, read no Model-F and create no root.
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
        v72p2d7_gf32_cross_layer_discriminator as d7e,
    )
except ModuleNotFoundError:  # file-layout fallback: same sibling file only
    _D7E_PATH = (Path(__file__).resolve().parent
                 / "v72p2d7_gf32_cross_layer_discriminator.py")
    _D7E_SPEC = _ilu.spec_from_file_location(
        "v72p2d7_gf32_cross_layer_discriminator", str(_D7E_PATH))
    if _D7E_SPEC is None or _D7E_SPEC.loader is None:
        raise ImportError("cannot load sibling D7-E module at %s" % (_D7E_PATH,))
    d7e = _ilu.module_from_spec(_D7E_SPEC)
    sys.modules["v72p2d7_gf32_cross_layer_discriminator"] = d7e
    _D7E_SPEC.loader.exec_module(d7e)

d7c = d7e.d7c
d5 = d7c.d5

# --------------------------------------------------------------------------
# Frozen constants (D7-F prereg R1; must not change without an OpenSpec
# revision).  Identities / priors / mothers / estimator are the D7-C/D7-E
# contract reused through these narrow aliases.
# --------------------------------------------------------------------------
Q = d7e.Q
N = d7e.N
BOB_DIM = d7e.BOB_DIM
N_A = d7e.N_A
MODEL_F_ROOT = d7e.MODEL_F_ROOT

F_VALUES = d7e.F_VALUES
L1_ROWS = d7e.L1_ROWS
L2_ROWS = d7e.L2_ROWS
ROWS = d7e.ROWS
BLOCK_SEEDS = d7e.BLOCK_SEEDS
L1_GRAPH_SEED = d7e.L1_GRAPH_SEED
L2_GRAPH_SEED = d7e.L2_GRAPH_SEED
L1_K_MIN = d7e.L1_K_MIN
L2_K_MIN = d7e.L2_K_MIN

LAMBDA_STAR = d7e.LAMBDA_STAR
DECODER_FLOOR = d7e.DECODER_FLOOR
MAX_ITER = d7e.MAX_ITER
DAMPING_ALPHA = d7e.DAMPING_ALPHA

ARMS = ("FORWARD_L1_TO_L2", "REVERSE_L2_TO_L1")
SOURCE_LAYER = {"FORWARD_L1_TO_L2": "L1", "REVERSE_L2_TO_L1": "L2"}
TARGET_LAYER = {"FORWARD_L1_TO_L2": "L2", "REVERSE_L2_TO_L1": "L1"}
# D7-E direction tokens reused only as the mixer dispatch key.
ARM_TO_DIRECTION = {"FORWARD_L1_TO_L2": "L1_TO_L2",
                    "REVERSE_L2_TO_L1": "L2_TO_L1"}
# (condition, layer) per (arm, role); transfer priors are built, not looked
# up, so transfer conditions name the transfer only.
SLOT_ROLE = {
    ("FORWARD_L1_TO_L2", "SOURCE"): ("L1_MARGINAL", "L1"),
    ("FORWARD_L1_TO_L2", "TARGET"): ("L2_TRANSFER", "L2"),
    ("REVERSE_L2_TO_L1", "SOURCE"): ("L2_MARGINAL", "L2"),
    ("REVERSE_L2_TO_L1", "TARGET"): ("L1_TRANSFER", "L1"),
}
ROLE_ORDER = ("SOURCE", "TARGET")

SLOT_COUNT = 128
MANDATORY_CALLS = 64
MAX_CALLS = 128

PER_CALL_WATCHDOG_S = 120.0
STORED_WALL_LIMIT_S = 1500.0
OUTER_WATCHDOG_S = 1800.0
OUTER_GRACE_S = 30.0
RSS_LIMIT_BYTES = 2 * 1024**3

D7F_AUTH_KEY = "d7f_execution_authorized"
STATE_REL_PATH = ("docs/research_cycles/"
                  "V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR/cycle_state.yaml")

# Frozen run terminals T1..T10 (exact strings, exact priority).
TERMINALS = (
    "D7_F_PRE_EXECUTION_BLOCKED",
    "D7_F_WATCHDOG_TIMEOUT_VOID",
    "D7_F_NONFINITE_OR_CRASH_BLOCKED",
    "D7_F_RESOURCE_OVERRUN",
    "D7_F_INCOMPLETE_MATRIX_BLOCKED",
    "D7_F_PROVENANCE_COVERAGE_BLOCKED",
    "D7_F_REVERSE_ORDER_STRONG_LIFT",
    "D7_F_REVERSE_ORDER_WEAK_LIFT",
    "D7_F_REVERSE_ORDER_REGRESSION",
    "D7_F_NO_USEFUL_REVERSE_ORDER_LIFT",
)
(T_PRE_EXEC, T_WATCHDOG, T_CRASH, T_RESOURCE, T_INCOMPLETE, T_COVERAGE,
 T_STRONG, T_WEAK, T_REGRESSION, T_NO_LIFT) = TERMINALS

# Frozen paired stratum labels (first-match order in ``classify_stratum``).
S_COVERAGE = "COVERAGE_BLOCKED"
S_REGRESSION = "REVERSE_REGRESSION"
S_STRONG = "STRONG_REVERSE_LIFT"
S_WEAK = "WEAK_REVERSE_LIFT"
S_NONE = "NO_REVERSE_LIFT"
STRATUM_LABELS = (S_COVERAGE, S_REGRESSION, S_STRONG, S_WEAK, S_NONE)

COVERAGE_OK = "COVERAGE_OK"

# Accepted provenance token that alone admits a conditioned transfer prior.
# Pinned by tests to the accepted v35 token; the gate itself delegates to the
# accepted guard, never to this literal.
CHECK_UPDATED = "CHECK_UPDATED"

# Current-belief record labels (iterations-derived, never a provenance token).
PRIOR_ONLY_CURRENT_BELIEF = d7e.PRIOR_ONLY_CURRENT_BELIEF
CHECK_UPDATED_CURRENT_BELIEF = d7e.CHECK_UPDATED_CURRENT_BELIEF
CURRENT_BELIEF_LABELS = d7e.CURRENT_BELIEF_LABELS

# Named deterministic blocked-transfer reasons (no decoder call made).
ELIGIBLE = d7e.ELIGIBLE
BLOCK_SOURCE_CRASH = d7e.BLOCK_SOURCE_CRASH
BLOCK_SOURCE_NONFINITE = d7e.BLOCK_SOURCE_NONFINITE
BLOCK_SOURCE_BELIEF_SHAPE = d7e.BLOCK_SOURCE_BELIEF_SHAPE
BLOCK_PROVENANCE = d7e.BLOCK_PROVENANCE

SEVEN_FILES = ("manifest.json", "decoder_records.csv", "arm_pairs.csv",
               "stratum_summary.csv", "summary.json", "report.md",
               "command_log.txt")

RECORD_FIELDS = [
    "slot_idx", "f", "seed", "arm", "role", "condition", "layer",
    "rows", "n", "exact", "syndrome_ok", "iterations", "status", "finite",
    "symbol_errors", "unsatisfied_checks", "wall_s", "rss_bytes",
    "belief_max_prob", "belief_mean_true_p", "belief_mean_entropy",
    "beliefs_conditioned", "current_belief_label", "belief_provenance",
    "belief_shape_ok", "transfer_eligible",
]
PAIR_FIELDS = [
    "pair_idx", "f", "seed", "arm", "source_layer", "target_layer",
    "source_rows", "target_rows", "n", "source_slot_idx",
    "target_slot_idx", "source_provenance", "target_provenance",
    "source_exact", "target_exact", "l1_exact", "l1_syndrome_ok",
    "l2_exact", "l2_syndrome_ok", "both_layers_exact",
]
STRATUM_FIELDS = [
    "stratum_idx", "f", "blocks",
    "forward_eligible_count", "forward_blocked_count",
    "reverse_eligible_count", "reverse_blocked_count",
    "forward_both_exact_count", "reverse_both_exact_count",
    "candidate_only", "reference_only", "both", "neither",
    "nonfinite_count", "crash_count", "stratum_label", "coverage_status",
]

_ESTIMATOR_ID = d7e._ESTIMATOR_ID
_DECODER_IDS = {
    "SOURCE": ("v35.decode_row_layered_fftqspa(h, prior, syndrome, "
                "max_iter=90, damping_alpha=1.0, warm_beliefs=None, "
                "field=None)"),
    "TARGET": ("v35.decode_row_layered_fftqspa(h, prior, syndrome, "
                "max_iter=90, damping_alpha=1.0, warm_beliefs=None, "
                "field=None)"),
}
_MOTHER_EXPR = d7e._MOTHER_EXPR
_TRANSFER_DIRECTIONS = ("L1_TO_L2", "L2_TO_L1")
_CALL_ORDER = ("for f in [1.0, 1.2]: for seed in 2026091300..2026091315: "
               "FORWARD_L1_TO_L2_SOURCE_L1_MARGINAL, "
               "FORWARD_L1_TO_L2_TARGET_L2_TRANSFER, "
               "REVERSE_L2_TO_L1_SOURCE_L2_MARGINAL, "
               "REVERSE_L2_TO_L1_TARGET_L1_TRANSFER")

# Formal/dev roots that must never be an output target (name-based guard).
PROTECTED_ROOTS = tuple(d7e.PROTECTED_ROOTS) + (
    "workspace/d7_e_cross_layer_discriminator_"
    "faa5dc1c-d2d6-4329-b88d-68f2c1f51d5c",
)
OUT_ROOT_PREFIX = "d7_f_reverse_order_discriminator_"

_EXECUTION_CONSUMED = False  # single-use guard within one process


class NotAuthorizedError(PermissionError):
    """Raised when a run is entered without the D7-F authorization key."""


class PreflightBlocked(ValueError):
    """Pre-first-call refusal; carries the frozen T1 terminal."""

    terminal = T_PRE_EXEC


# --------------------------------------------------------------------------
# State / path contract
# --------------------------------------------------------------------------

def repo_root_path(repo_root=None) -> Path:
    """Repository root derived from ``__file__`` (no cwd assumption)."""
    return (Path(repo_root).resolve() if repo_root is not None
            else Path(__file__).resolve().parents[4])


def cycle_state_path(repo_root=None) -> Path:
    return repo_root_path(repo_root) / STATE_REL_PATH


def read_cycle_state(path) -> dict:
    """Parse the flat ``key: value`` D7-F cycle-state file (no YAML dep)."""
    state = {}
    with open(str(path), "r", encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if val.lower() in ("true", "false"):
                state[key] = val.lower() == "true"
            else:
                state[key] = val
    return state


def is_authorized(state) -> bool:
    try:
        return bool(dict(state).get(D7F_AUTH_KEY, False))
    except Exception:
        return False


def _require_authorized(authorized: bool) -> None:
    if not authorized:
        raise NotAuthorizedError(
            "D7-F execution is not authorized; refusing before any work")


def model_f_root_matches(value, repo_root=None) -> bool:
    """True iff ``value`` resolves to exactly the frozen Model-F root."""
    if value is None:
        return False
    cand = Path(str(value))
    if not cand.is_absolute():
        cand = repo_root_path(repo_root) / cand
    return cand.resolve() == (repo_root_path(repo_root) / MODEL_F_ROOT).resolve()


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
#
# Frozen A2 telemetry rule, reused verbatim from the accepted D7-E delta:
# the current-process peak RSS comes from ``VmHWM`` in ``/proc/self/status``
# (unit exactly ``kB``; ``bytes = value * 1024``).  Anything else yields None
# and the callers block under the existing resource terminal.

_PROC_SELF_STATUS_PATH = d7e._PROC_SELF_STATUS_PATH

parse_vmhwm_rss_bytes = d7e.parse_vmhwm_rss_bytes
_probe_rss_valid = d7e._probe_rss_valid


def _read_proc_self_status_text():
    """Raw ``/proc/self/status`` text, read once per call; None on failure."""
    try:
        with open(_PROC_SELF_STATUS_PATH, "r", encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return None


def get_rss_bytes():
    """Current-process peak RSS bytes from ``VmHWM``; None when unavailable.

    Fail-closed WSL/Linux probe: exactly one ASCII
    ``VmHWM: <positive integer> kB`` line yields ``value * 1024`` bytes;
    anything else yields None and the callers block under the existing
    resource terminal.
    """
    return parse_vmhwm_rss_bytes(_read_proc_self_status_text())


# --------------------------------------------------------------------------
# Frozen 128-slot matrix
# --------------------------------------------------------------------------

def frozen_slots() -> list:
    """All 128 frozen slots in the frozen order; ``slot_idx`` 1-based.

    Outer ``f`` in ``[1.0, 1.2]``, seeds ``2026091300..2026091315``
    ascending, four slots per ``(f, seed)``: forward source, forward target,
    reverse source, reverse target.
    """
    slots = []
    for f in F_VALUES:
        for seed in BLOCK_SEEDS:
            for arm in ARMS:
                for role in ROLE_ORDER:
                    condition, layer = SLOT_ROLE[(arm, role)]
                    slots.append({
                        "slot_idx": len(slots) + 1,
                        "f": float(f),
                        "seed": int(seed),
                        "arm": arm,
                        "role": role,
                        "condition": condition,
                        "layer": layer,
                        "rows": int(ROWS[layer][float(f)]),
                        "n": N,
                    })
    return slots


# --------------------------------------------------------------------------
# Narrow D7-E reuse: joint / prior / mother / estimator / block preparation
# --------------------------------------------------------------------------

build_joint = d7e.build_joint
condition_prior_qn = d7e.condition_prior_qn
decoder_prior = d7e.decoder_prior
build_mother = d7e.build_mother
_default_model_f_loader = d7e._default_model_f_loader


def prepare_inputs(*, joint=None, model_f_root=None, model_f_loader=None,
                   block_sampler=None, mothers=None, repo=None) -> dict:
    """Frozen preparation order (D7-C reuse via D7-E) plus the 128-slot matrix.

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
# Provenance gate (accepted BP Alternative A contract, lazy bind)
# --------------------------------------------------------------------------

require_check_updated = d7e.require_check_updated
belief_provenance_error = d7e.belief_provenance_error
check_source_eligibility = d7e.check_source_eligibility


def _result_provenance(result):
    """Extract the raw ``belief_provenance`` token (or ``None``) from one
    decoder return, mirroring the accepted result semantics."""
    if isinstance(result, dict):
        return result.get("belief_provenance")
    return getattr(result, "belief_provenance", None)


# --------------------------------------------------------------------------
# Transfer math (frozen formulas; transient q, never persisted)
# --------------------------------------------------------------------------

softmax_source_q = d7e.softmax_source_q
transfer_prior_l1_to_l2 = d7e.transfer_prior_l1_to_l2
transfer_prior_l2_to_l1 = d7e.transfer_prior_l2_to_l1
build_transfer_prior = d7e.build_transfer_prior


# --------------------------------------------------------------------------
# Decoder dispatch (dual roles, DI) and lazy production bind
# --------------------------------------------------------------------------

dispatch_decoder = d7e.dispatch_decoder
bind_row_layered_decoders = d7e.bind_row_layered_decoders


# --------------------------------------------------------------------------
# Per-call evaluation (scalar records; exact/syndrome isolation)
# --------------------------------------------------------------------------

_belief_label = d7e._belief_label
_source_belief_bundle = d7e._source_belief_bundle


def evaluate_call(slot: dict, h_prefix: np.ndarray, block: dict,
                  syndrome: np.ndarray, result, wall_s: float,
                  rss_bytes) -> dict:
    """One completed call -> scalar record with isolated exact/syndrome."""
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
                      and np.all(np.isfinite(np.asarray(beliefs, dtype=np.float64))))
    finite = bool(finite_x and finite_bel)
    diagnostics = d7c._belief_diagnostics(beliefs, x_true, finite)
    bundle = _source_belief_bundle(result, int(x_true.shape[0]))
    provenance = bundle["provenance"]
    if slot["role"] == "SOURCE":
        eligible, _ = check_source_eligibility(
            status=status, finite=finite, belief_shape_ok=bundle["shape_ok"],
            provenance=provenance)
    else:
        eligible = ""
    return {
        "slot_idx": int(slot["slot_idx"]),
        "f": float(slot["f"]),
        "seed": int(slot["seed"]),
        "arm": slot["arm"],
        "role": slot["role"],
        "condition": slot["condition"],
        "layer": layer,
        "rows": int(slot["rows"]),
        "n": int(slot["n"]),
        "exact": exact,
        "syndrome_ok": syndrome_ok,
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
        "beliefs_conditioned": int(iterations) > 0,
        "current_belief_label": _belief_label(int(iterations)),
        "belief_provenance": provenance if isinstance(provenance, str) else "",
        "belief_shape_ok": bool(bundle["shape_ok"]),
        "transfer_eligible": eligible,
    }


def crash_record(slot: dict, exc: BaseException, wall_s: float,
                 rss_bytes) -> dict:
    """A decoder exception is an attempted-but-not-completed call (no retry)."""
    return {
        "slot_idx": int(slot["slot_idx"]),
        "f": float(slot["f"]),
        "seed": int(slot["seed"]),
        "arm": slot["arm"],
        "role": slot["role"],
        "condition": slot["condition"],
        "layer": slot["layer"],
        "rows": int(slot["rows"]),
        "n": int(slot["n"]),
        "exact": False,
        "syndrome_ok": False,
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
        "belief_shape_ok": False,
        "transfer_eligible": False,
    }


# --------------------------------------------------------------------------
# Sequential 128-slot loop (no retry / resume / concurrency)
# --------------------------------------------------------------------------

def execute_slots(context: dict, decoder_fns, *, clock=None,
                  rss_probe=None) -> dict:
    """Run the frozen 128-slot matrix once, sequentially, stopping on the
    first higher-priority budget/validity stop.

    Mandatory source slots always invoke their decoder; target slots invoke
    the target decoder exactly when the cached source return of the same arm
    is eligible, otherwise they are recorded non-invocations (no call, no
    wall cost).  No replacement, retry or resume.  Nothing is transferred
    back to the source layer: each target consumes only its own syndrome and
    its posterior is never reused.
    """
    clock = clock or time.perf_counter
    rss_probe = rss_probe or get_rss_bytes
    records = []
    sources = {}
    stored_wall = 0.0
    stop = None
    for slot in context["slots"]:
        if len(records) >= MAX_CALLS:  # hard cap; matrix holds 128 slots
            break
        f = float(slot["f"])
        seed = int(slot["seed"])
        arm = slot["arm"]
        role = slot["role"]
        layer = slot["layer"]
        block = context["blocks"][seed]
        h_prefix = context["mothers"][layer][:int(slot["rows"])]
        x_true = np.asarray(block["u1"] if layer == "L1" else block["u2"],
                            dtype=np.int64)
        key = "SOURCE" if role == "SOURCE" else "TARGET"

        if role == "TARGET":
            src = sources[(f, seed, arm)]
            eligible, _ = check_source_eligibility(
                status=src["record"]["status"],
                finite=src["record"]["finite"],
                belief_shape_ok=src["shape_ok"],
                provenance=src["provenance"])
            if not eligible:
                continue  # blocked: recorded non-invocation, never a call
            q = softmax_source_q(src["beliefs"])  # transient, never persisted
            prior_pq = build_transfer_prior(context["joint"],
                                            ARM_TO_DIRECTION[arm],
                                            block["bob"], q)
            syndrome = d5._gf32_syndrome(h_prefix, x_true)
        else:
            prior_qn = condition_prior_qn(context["joint"],
                                          slot["condition"], block)
            prior_pq = decoder_prior(prior_qn)
            syndrome = d5._gf32_syndrome(h_prefix, x_true)

        t0 = clock()
        result, exc = None, None
        try:
            result = dispatch_decoder(key, decoder_fns, h_prefix, prior_pq,
                                      syndrome)
        except Exception as caught:  # isolated as a crash, never retried
            exc = caught
        wall = max(0.0, float(clock() - t0))
        rss_bytes, rss_valid = _probe_rss_valid(rss_probe)

        if exc is not None:
            record = crash_record(slot, exc, wall,
                                  rss_bytes if rss_valid else None)
        else:
            try:
                record = evaluate_call(slot, h_prefix, block, syndrome,
                                       result, wall,
                                       rss_bytes if rss_valid else None)
            except Exception as caught:
                record = crash_record(slot, caught, wall,
                                      rss_bytes if rss_valid else None)
        if role == "SOURCE" and exc is None:
            try:
                bundle = _source_belief_bundle(result, int(x_true.shape[0]))
            except Exception:
                bundle = {"beliefs": None, "provenance": None,
                          "shape_ok": False}
            sources[(f, seed, arm)] = {
                "beliefs": bundle["beliefs"],
                "provenance": bundle["provenance"],
                "shape_ok": bundle["shape_ok"],
                "record": record,
            }
        elif role == "SOURCE":
            sources[(f, seed, arm)] = {
                "beliefs": None, "provenance": None, "shape_ok": False,
                "record": record,
            }
        records.append(record)
        stored_wall += wall
        if wall > PER_CALL_WATCHDOG_S:
            stop = T_WATCHDOG
        elif str(record["status"]).startswith("crash:") or not record["finite"]:
            stop = T_CRASH
        elif (stored_wall > STORED_WALL_LIMIT_S or not rss_valid
              or rss_bytes >= RSS_LIMIT_BYTES):
            stop = T_RESOURCE
        if stop is not None:
            break
    return {"records": records, "stop": stop, "stored_wall_s": stored_wall}


# --------------------------------------------------------------------------
# Arm pairs, strata and terminals (shared by run and verifier)
# --------------------------------------------------------------------------

def _as_bool(value) -> bool:
    if value in (True, "True", "true", 1):
        return True
    return False


def _as_float(value):
    if value in ("", None):
        return None
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def _as_int(value):
    if value in ("", None):
        return None
    try:
        return int(value)
    except Exception:
        return None


def _record_complete(record) -> bool:
    """Non-crash, finite, parseable-completed call."""
    if record is None:
        return False
    if str(record.get("status", "")).startswith("crash:"):
        return False
    return (bool(_as_bool(record.get("finite")))
            and _as_int(record.get("iterations")) is not None)


def compute_arm_pairs(records) -> list:
    """One row per eligible arm present in ``records``.

    Rows join the source and target records sharing ``(f, seed, arm)``; the
    source exact flag rides along as context only and never gates anything.
    ``l1_*``/``l2_*`` are the layer view of the same two outcomes and
    ``both_layers_exact`` is their AND only.
    """
    sources, targets = {}, {}
    for record in records:
        key = (float(record["f"]), int(record["seed"]), record["arm"])
        if record["role"] == "SOURCE":
            sources[key] = record
        elif record["role"] == "TARGET":
            targets[key] = record
    rows = []
    for key in sorted(sources):
        source = sources[key]
        if not _as_bool(source.get("transfer_eligible")):
            continue
        target = targets.get(key)
        if target is None:
            continue  # truncated run: the verifier judges the missing row

        def _flag(record, field):
            return bool(_as_bool(record[field]))

        s_exact, t_exact = _flag(source, "exact"), _flag(target, "exact")
        s_syn, t_syn = _flag(source, "syndrome_ok"), _flag(target, "syndrome_ok")
        f, seed, arm = key
        if arm == "FORWARD_L1_TO_L2":
            l1_exact, l1_syn, l2_exact, l2_syn = s_exact, s_syn, t_exact, t_syn
        else:
            l1_exact, l1_syn, l2_exact, l2_syn = t_exact, t_syn, s_exact, s_syn
        rows.append({
            "pair_idx": len(rows) + 1,
            "f": f, "seed": seed, "arm": arm,
            "source_layer": SOURCE_LAYER[arm],
            "target_layer": TARGET_LAYER[arm],
            "source_rows": int(source["rows"]),
            "target_rows": int(target["rows"]),
            "n": int(source["n"]),
            "source_slot_idx": int(source["slot_idx"]),
            "target_slot_idx": int(target["slot_idx"]),
            "source_provenance": source.get("belief_provenance", ""),
            "target_provenance": target.get("belief_provenance", ""),
            "source_exact": s_exact,
            "target_exact": t_exact,
            "l1_exact": l1_exact,
            "l1_syndrome_ok": l1_syn,
            "l2_exact": l2_exact,
            "l2_syndrome_ok": l2_syn,
            "both_layers_exact": bool(l1_exact and l2_exact),
        })
    return rows


def classify_stratum(*, forward_eligible, reverse_eligible, candidate_only,
                     reference_only) -> str:
    """Frozen first-match paired label per f (prereg B05).

    ``candidate_only`` counts seeds where the reverse arm alone recovers both
    layers exactly; ``reference_only`` the mirror.  These are synthetic
    diagnostic labels, not FER thresholds.
    """
    if int(forward_eligible) < 12 or int(reverse_eligible) < 12:
        return S_COVERAGE
    if int(reference_only) >= 2 and int(candidate_only) == 0:
        return S_REGRESSION
    if int(candidate_only) >= 4 and int(reference_only) == 0:
        return S_STRONG
    if int(candidate_only) > int(reference_only):
        return S_WEAK
    return S_NONE


def compute_strata(records, arm_rows) -> list:
    """Two frozen stratum rows (one per f) with first-match labels.

    Candidate/reference counts run over the same 16 seeds; a seed whose arm
    is ineligible or incomplete counts as not-both-exact.  Thin arms report
    ``COVERAGE_BLOCKED``, never a relabeled stratum.
    """
    strata = []
    for f in F_VALUES:
        stratum_records = [r for r in records if float(r["f"]) == float(f)]
        fwd_sources = [r for r in stratum_records
                       if r["role"] == "SOURCE"
                       and r["arm"] == "FORWARD_L1_TO_L2"]
        rev_sources = [r for r in stratum_records
                       if r["role"] == "SOURCE"
                       and r["arm"] == "REVERSE_L2_TO_L1"]
        fwd_eligible = int(sum(1 for r in fwd_sources
                               if _as_bool(r.get("transfer_eligible"))))
        rev_eligible = int(sum(1 for r in rev_sources
                               if _as_bool(r.get("transfer_eligible"))))
        pairs = [row for row in arm_rows if float(row["f"]) == float(f)]
        fwd_both = {int(row["seed"]): _as_bool(row["both_layers_exact"])
                    for row in pairs if row["arm"] == "FORWARD_L1_TO_L2"}
        rev_both = {int(row["seed"]): _as_bool(row["both_layers_exact"])
                    for row in pairs if row["arm"] == "REVERSE_L2_TO_L1"}
        candidate_only = reference_only = both = neither = 0
        for seed in BLOCK_SEEDS:
            cand = bool(rev_both.get(int(seed), False))
            ref = bool(fwd_both.get(int(seed), False))
            if cand and not ref:
                candidate_only += 1
            elif ref and not cand:
                reference_only += 1
            elif cand and ref:
                both += 1
            else:
                neither += 1
        crashes = int(sum(1 for r in stratum_records
                          if str(r["status"]).startswith("crash:")))
        nonfinite = int(sum(1 for r in stratum_records
                            if (not _as_bool(r["finite"]))
                            and not str(r["status"]).startswith("crash:")))
        label = classify_stratum(
            forward_eligible=fwd_eligible, reverse_eligible=rev_eligible,
            candidate_only=candidate_only, reference_only=reference_only)
        strata.append({
            "stratum_idx": len(strata) + 1,
            "f": float(f),
            "blocks": len(BLOCK_SEEDS),
            "forward_eligible_count": fwd_eligible,
            "forward_blocked_count": int(len(BLOCK_SEEDS) - len(
                [r for r in fwd_sources])) + int(len(
                    [r for r in fwd_sources
                     if not _as_bool(r.get("transfer_eligible"))])),
            "reverse_eligible_count": rev_eligible,
            "reverse_blocked_count": int(len(BLOCK_SEEDS) - len(
                [r for r in rev_sources])) + int(len(
                    [r for r in rev_sources
                     if not _as_bool(r.get("transfer_eligible"))])),
            "forward_both_exact_count": int(sum(
                1 for v in fwd_both.values() if v)),
            "reverse_both_exact_count": int(sum(
                1 for v in rev_both.values() if v)),
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
    """Frozen T1..T10 first-applicable terminal selection (prereg B06)."""
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


def _eligible_by_stratum_arm(records) -> dict:
    out = {(float(f), arm): 0 for f in F_VALUES for arm in ARMS}
    for record in records:
        if record.get("role") != "SOURCE":
            continue
        if _as_bool(record.get("transfer_eligible")):
            out[(float(record["f"]), record["arm"])] += 1
    return out


def _mandatory_present(records) -> int:
    return int(sum(1 for r in records if r.get("role") == "SOURCE"))


def terminal_from_records(records, arm_rows, stratum_rows) -> str:
    """Recompute the run terminal from scalar records + arm/stratum rows."""
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
    coverage = any(count < 12
                   for count in _eligible_by_stratum_arm(records).values())
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
# Seven-file writer and verifier
# --------------------------------------------------------------------------

def _scalar(value):
    if value is None:
        return ""
    if isinstance(value, (bool, str)):
        return value
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value)
    raise ValueError("non-scalar evidence value of type %s"
                     % (type(value).__name__,))


def _record_row(record: dict, fields) -> dict:
    extra = set(record) - set(fields)
    if extra:
        raise ValueError("record has unknown fields %r" % (sorted(extra),))
    return {k: _scalar(record.get(k, "")) for k in fields}


def _jsonable(value):
    if isinstance(value, (bool, str, int, float)):
        return value
    if value is None:
        return None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    raise ValueError("non-JSON-serializable evidence value %r" % (type(value),))


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
        fh.write("# D7-F paired reverse-order cross-layer discriminator\n\n")
        fh.write("terminal: %s\n" % (summary.get("terminal"),))
        fh.write("calls_completed: %s\n" % (summary.get("calls_completed"),))
        fh.write("transfer_invoked: %s\n" % (summary.get("transfer_invoked"),))
        fh.write("transfer_blocked: %s\n" % (summary.get("transfer_blocked"),))
        fh.write("stored_wall_s: %s\n" % (summary.get("stored_wall_s"),))
        for row in stratum_rows:
            fh.write("f=%s: %s (%s)\n" % (
                row["f"], row["stratum_label"], row["coverage_status"]))
    with open(out / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write((command_str or "") + "\n")
        fh.write("terminal: %s\n" % (summary.get("terminal"),))
        fh.write("calls_completed: %s\n" % (summary.get("calls_completed"),))
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
        "model_f_root": MODEL_F_ROOT,
        "estimator": _ESTIMATOR_ID,
        "lambda_star": LAMBDA_STAR,
        "n": N,
        "f_values": [float(f) for f in F_VALUES],
        "arms": list(ARMS),
        "transfer_directions": list(_TRANSFER_DIRECTIONS),
        "block_seeds": [int(s) for s in BLOCK_SEEDS],
        "max_calls": MAX_CALLS,
        "mandatory_calls": MANDATORY_CALLS,
        "per_call_watchdog_s": PER_CALL_WATCHDOG_S,
        "stored_wall_limit_s": STORED_WALL_LIMIT_S,
        "outer_watchdog_s": OUTER_WATCHDOG_S,
        "outer_grace_s": OUTER_GRACE_S,
        "rss_limit_bytes": RSS_LIMIT_BYTES,
        "decoder_floor": DECODER_FLOOR,
        "max_iter": MAX_ITER,
        "damping_alpha": DAMPING_ALPHA,
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
    for key in ("slot_idx", "arm", "role", "condition", "layer",
                "rows", "n", "seed"):
        if str(record.get(key)) != str(expected[key]):
            problems.append(prefix + "identity %s mismatch" % (key,))
            return
    if _as_float(record.get("f")) != float(expected["f"]):
        problems.append(prefix + "identity f mismatch")
        return
    crash = str(record["status"]).startswith("crash:")
    if crash:
        if record["current_belief_label"] != "":
            problems.append(prefix + "crash record must carry an empty belief label")
        if _as_bool(record["finite"]):
            problems.append(prefix + "crash record must be nonfinite")
        if _as_bool(record.get("transfer_eligible")):
            problems.append(prefix + "crash record must not be transfer eligible")
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
        problems.append(prefix + "symbol_errors/unsatisfied_checks not parseable")
        return
    if exact != (symbol_errors == 0):
        problems.append(prefix + "exact must equal symbol_errors == 0")
    if exact and unsatisfied != 0:
        problems.append(prefix + "exact record must have zero unsatisfied checks")
    if _as_bool(record["syndrome_ok"]) and unsatisfied != 0:
        problems.append(prefix + "syndrome_ok record must have zero unsatisfied checks")
    wall = _as_float(record["wall_s"])
    if wall is None or wall < 0:
        problems.append(prefix + "wall_s must be a nonnegative number")
    rss = record["rss_bytes"]
    if rss not in ("", None) and (_as_int(rss) is None or _as_int(rss) <= 0):
        problems.append(prefix + "rss_bytes must be positive or empty")
    provenance = record.get("belief_provenance", "")
    if not isinstance(provenance, str):
        problems.append(prefix + "belief_provenance must be a scalar string")
        return
    shape_ok = _as_bool(record.get("belief_shape_ok"))
    recomputed_eligible, _ = check_source_eligibility(
        status=record["status"], finite=_as_bool(record["finite"]),
        belief_shape_ok=shape_ok,
        provenance=(provenance if provenance != "" else None))
    # The recompute path above never binds a decoder: the guard raises for
    # every non-admitting token before any mixer contact.
    if record["role"] == "SOURCE":
        if _as_bool(record.get("transfer_eligible")) != recomputed_eligible:
            problems.append(prefix + "transfer_eligible does not recompute "
                            "from the provenance gate")
    elif record.get("transfer_eligible") not in ("", None, False, "False"):
        problems.append(prefix + "only source rows carry transfer_eligible")
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
    if key in ("arm", "role", "condition", "layer", "stratum_label",
               "coverage_status", "source_provenance", "target_provenance",
               "source_layer", "target_layer"):
        return str(a) == str(b)
    if key == "f" or key.endswith("_wall_s"):
        fa, fb = _as_float(a), _as_float(b)
        return fa is not None and fb is not None and abs(fa - fb) <= 1e-9
    if key.endswith("_exact") or key.endswith("_syndrome_ok"):
        return _as_bool(a) == _as_bool(b)
    ia, ib = _as_int(a), _as_int(b)
    if ia is not None and ib is not None:
        return ia == ib
    return str(a) == str(b)


def _rows_equal_scalar(left, right, fields) -> bool:
    return all(_scalar_equal(key, left.get(key), right.get(key))
               for key in fields)


def _expected_walk(records, slots):
    """Walk file records against frozen slots; blocked targets are the only
    skippable slots.  Returns ``(problems, matched, stop_pos)`` where
    ``stop_pos`` is the first slot position carrying a stop condition."""
    problems = []
    by_slot = {}
    for record in records:
        slot_idx = _as_int(record.get("slot_idx"))
        if slot_idx is None:
            problems.append("record with unparseable slot_idx")
            continue
        if slot_idx in by_slot:
            problems.append("duplicate slot_idx %s" % (slot_idx,))
        by_slot[slot_idx] = record
    eligible = {}
    for record in records:
        if record.get("role") == "SOURCE":
            eligible[(float(record["f"]), int(record["seed"]),
                      record["arm"])] = _as_bool(
                          record.get("transfer_eligible"))
    matched = 0
    stop_pos = None
    stored = 0.0
    for position, slot in enumerate(slots):
        record = by_slot.get(int(slot["slot_idx"]))
        if record is None:
            if slot["role"] == "TARGET" and not eligible.get(
                    (float(slot["f"]), int(slot["seed"]),
                     slot["arm"]), False):
                continue  # blocked slot: recorded non-invocation
            if stop_pos is None:
                problems.append("slot %d (%s %s %s) has no record without "
                                "an earlier stop" % (
                                    slot["slot_idx"], slot["arm"],
                                    slot["role"], slot["condition"]))
            continue
        matched += 1
        _check_record_semantics(record, slot, problems)
        wall = _as_float(record.get("wall_s")) or 0.0
        stored += wall
        crash = (str(record["status"]).startswith("crash:")
                 or not _as_bool(record["finite"]))
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
    return problems, matched, stop_pos


def verify_root(out_root) -> dict:
    """Read-only verification of a seven-file root (no decoder, no Model-F).

    Recomputes schema, slot order, mandatory 64 calls, eligible transfer
    invocation count, uniqueness, no replacement, arm identity, provenance
    gate, exact/syndrome isolation, both-layers AND rule, syndrome
    single-consumption, two labels, terminal, wall/RSS and the manifest
    contract from the seven files alone.
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
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
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
    if len(records) > MAX_CALLS:
        problems.append("records exceed the %d-call cap" % (MAX_CALLS,))
    slots = frozen_slots()
    walk_problems, matched, stop_pos = _expected_walk(records, slots)
    problems.extend(walk_problems)
    mandatory = _mandatory_present(records)
    if mandatory < MANDATORY_CALLS:
        if summary.get("terminal") not in (T_WATCHDOG, T_CRASH, T_RESOURCE,
                                           T_INCOMPLETE):
            problems.append("truncated core matrix without a stop terminal")
    if stop_pos is not None:
        allowed = [r for r in records
                   if _as_int(r.get("slot_idx")) is not None
                   and _as_int(r.get("slot_idx")) <= slots[stop_pos]["slot_idx"]]
        if len(allowed) != len(records):
            problems.append("records present after the stop position")
    recomputed_paired = compute_arm_pairs(records)
    if len(paired) != len(recomputed_paired):
        problems.append("arm_pairs.csv row count %d != recomputed %d"
                        % (len(paired), len(recomputed_paired)))
    else:
        for actual, expected in zip(paired, recomputed_paired):
            if not _rows_equal_scalar(actual, expected, PAIR_FIELDS):
                problems.append(
                    "arm row f=%s seed=%s %s does not recompute"
                    % (actual.get("f"), actual.get("seed"),
                       actual.get("arm")))
    for row in paired:
        if row.get("source_provenance") != CHECK_UPDATED:
            problems.append("arm row f=%s seed=%s %s has non-admitting "
                            "source provenance %r"
                            % (row.get("f"), row.get("seed"),
                               row.get("arm"),
                               row.get("source_provenance")))
        l1 = _as_bool(row.get("l1_exact"))
        l2 = _as_bool(row.get("l2_exact"))
        if _as_bool(row.get("both_layers_exact")) != bool(l1 and l2):
            problems.append("arm row f=%s seed=%s %s both_layers_exact "
                            "is not the AND of l1/l2 exact"
                            % (row.get("f"), row.get("seed"),
                               row.get("arm")))
    recomputed_strata = compute_strata(records, recomputed_paired)
    if len(strata) != 2:
        problems.append("stratum_summary.csv row count %d != 2" % (len(strata),))
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
    if _as_int(summary.get("calls_completed")) != len(records):
        problems.append("summary calls_completed != record count")
    if _as_int(summary.get("calls_attempted")) != len(records):
        problems.append("summary calls_attempted != record count")
    if _as_int(summary.get("mandatory_completed")) != mandatory:
        problems.append("summary mandatory_completed != mandatory count")
    if _as_int(summary.get("transfer_invoked")) != sum(
            1 for r in records if r["role"] == "TARGET"):
        problems.append("summary transfer_invoked != target row count")
    eligible_total = sum(1 for r in records
                         if r["role"] == "SOURCE"
                         and _as_bool(r.get("transfer_eligible")))
    source_total = sum(1 for r in records if r["role"] == "SOURCE")
    if _as_int(summary.get("transfer_blocked")) != (source_total - eligible_total):
        # blocked second stages == source slots whose gate refused.
        problems.append("summary transfer_blocked does not recompute")
    expected_labels = [
        {"stratum_idx": int(row["stratum_idx"]), "f": float(row["f"]),
         "stratum_label": row["stratum_label"]}
        for row in recomputed_strata]
    if summary.get("strata") != expected_labels:
        problems.append("summary strata labels do not recompute")
    stored = sum(v for v in (_as_float(r["wall_s"]) for r in records)
                 if v is not None)
    if _as_float(summary.get("stored_wall_s")) is None or abs(
            float(summary.get("stored_wall_s")) - stored) > 1e-9:
        problems.append("summary stored_wall_s does not recompute")
    for key, value in (("retries", 0), ("reruns", 0), ("resumes", 0)):
        if summary.get(key) != value:
            problems.append("summary %s must be 0" % (key,))
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

def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _build_manifest(*, out_root, model_f_files, authorization_consumed,
                    command_str, start_utc, end_utc, pid) -> dict:
    name = Path(out_root).name
    uuid = (name[len(OUT_ROOT_PREFIX):]
            if name.startswith(OUT_ROOT_PREFIX) else "")
    return {
        "change": "v72p2d7-reverse-order-cross-layer-discriminator",
        "contract": "R1",
        "out_root_name": name,
        "uuid": uuid,
        "estimator": _ESTIMATOR_ID,
        "lambda_star": LAMBDA_STAR,
        "model_f_root": MODEL_F_ROOT,
        "model_f_files": list(model_f_files),
        "n": N,
        "f_values": [float(f) for f in F_VALUES],
        "arms": list(ARMS),
        "transfer_directions": list(_TRANSFER_DIRECTIONS),
        "l1_rows": {"1.0": L1_ROWS[1.0], "1.2": L1_ROWS[1.2]},
        "l2_rows": {"1.0": L2_ROWS[1.0], "1.2": L2_ROWS[1.2]},
        "block_seeds": [int(s) for s in BLOCK_SEEDS],
        "graph_seeds": {"L1": L1_GRAPH_SEED, "L2": L2_GRAPH_SEED},
        "mothers": dict(_MOTHER_EXPR),
        "decoder_ids": dict(_DECODER_IDS),
        "max_iter": MAX_ITER,
        "damping_alpha": DAMPING_ALPHA,
        "decoder_floor": DECODER_FLOOR,
        "max_calls": MAX_CALLS,
        "mandatory_calls": MANDATORY_CALLS,
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


def _build_summary(loop, records, paired, strata, terminal) -> dict:
    sources = [r for r in records if r["role"] == "SOURCE"]
    eligible = sum(1 for r in sources
                   if _as_bool(r.get("transfer_eligible")))
    return {
        "terminal": terminal,
        "strata": [
            {"stratum_idx": int(row["stratum_idx"]), "f": float(row["f"]),
             "stratum_label": row["stratum_label"]}
            for row in strata],
        "slots_scheduled": SLOT_COUNT,
        "mandatory_completed": _mandatory_present(records),
        "transfer_invoked": int(sum(1 for r in records
                                    if r["role"] == "TARGET")),
        "transfer_blocked": int(len(sources) - eligible),
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


def run_reverse_order_discriminator(*, out_root, model_f_root=None,
                                    decoder_fns=None, model_f_loader=None,
                                    joint=None, block_sampler=None, mothers=None,
                                    state=None, state_reader=None, clock=None,
                                    rss_probe=None, command_str="",
                                    repo_root=None) -> dict:
    """One frozen sequential run (production bind only when ``decoder_fns``
    is None and the authorization key is true)."""
    global _EXECUTION_CONSUMED
    if _EXECUTION_CONSUMED:
        raise NotAuthorizedError("D7-F authorization already consumed (no reuse)")
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
            "%s: RSS measurement must be finite and positive before the first "
            "scientific call (got %r)" % (T_PRE_EXEC, rss0))

    context = prepare_inputs(joint=joint, model_f_root=model_f_root,
                             model_f_loader=model_f_loader,
                             block_sampler=block_sampler, mothers=mothers,
                             repo=repo)

    production = decoder_fns is None
    if production:
        decoder_fns = bind_row_layered_decoders()
        _EXECUTION_CONSUMED = True

    start_utc = _utc_now()
    loop = execute_slots(context, decoder_fns, clock=clock, rss_probe=rss_probe)
    records = loop["records"]
    paired = compute_arm_pairs(records)
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
