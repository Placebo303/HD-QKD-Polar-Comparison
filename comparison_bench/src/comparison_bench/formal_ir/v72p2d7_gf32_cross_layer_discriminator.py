"""D7-E provenance-safe cross-layer transfer discriminator core (frozen R1).

Single-pass, two-direction mechanism discriminator on the exact D7-C frozen
identities: for each ``(f, seed)`` a source-layer marginal decode is followed
by a target-layer marginal control decode and, only when the source return
carries exactly ``CHECK_UPDATED`` belief provenance, one cold target-layer
transfer decode whose prior mixes the transient source APP approximation
``q`` (rowwise softmax of the current log belief) with the accepted joint
Model-F conditional.  Per ``(f, seed)`` the exact slot order is::

    L1_TO_L2_SOURCE_L1_MARGINAL
    L1_TO_L2_TARGET_L2_CONTROL_MARGINAL
    L1_TO_L2_TARGET_L2_TRANSFER       # invoked only if source CHECK_UPDATED
    L2_TO_L1_SOURCE_L2_MARGINAL
    L2_TO_L1_TARGET_L1_CONTROL_MARGINAL
    L2_TO_L1_TARGET_L1_TRANSFER       # invoked only if source CHECK_UPDATED

192 scheduled slots: 128 mandatory source/control decoder calls plus up to 64
provenance-eligible transfer calls.  A blocked transfer slot is a recorded
non-invocation (counted in the stratum/summary blocked counts and identified
by its source record carrying ``transfer_eligible=False`` with the scalar
``belief_provenance`` token), never a replacement, retry or fake result.

Row-layered only GF(32) poly 37, cold start, ``max_iter=90``,
``damping_alpha=1.0``.  No schedule comparison, no oracle prior or decoder
call, no second decoding pass, no cross-layer returned belief consumed by any
other layer, no estimator change: the joint comes only through the accepted
``prepare_model_f_prior_candidate`` / ``build_f_model_concentration`` chain
with per-Bob-column smoothing.  D5 / D7-C are import-only upstream and are
never modified; D7-D is not imported at all.

This module performs no scientific decoder call and reads no real Model-F
content unless explicitly authorized by a future frozen execution packet;
tests inject fake joint tensors, blocks, mothers, decoders, clock and RSS
through the DI boundary.  ``import``, ``--help``, ``--dry-run``,
``--verify`` and unauthorized runs bind no decoder, read no Model-F and
create no root.
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
        v72p2d7_gf32_bidirectional_oracle as d7c,
    )
except ModuleNotFoundError:  # file-layout fallback: same sibling file only
    _D7C_PATH = (Path(__file__).resolve().parent
                 / "v72p2d7_gf32_bidirectional_oracle.py")
    _D7C_SPEC = _ilu.spec_from_file_location(
        "v72p2d7_gf32_bidirectional_oracle", str(_D7C_PATH))
    if _D7C_SPEC is None or _D7C_SPEC.loader is None:
        raise ImportError("cannot load sibling D7-C oracle at %s" % (_D7C_PATH,))
    d7c = _ilu.module_from_spec(_D7C_SPEC)
    sys.modules["v72p2d7_gf32_bidirectional_oracle"] = d7c
    _D7C_SPEC.loader.exec_module(d7c)

# --------------------------------------------------------------------------
# Frozen constants (D7-E prereg R1; must not change without an OpenSpec
# revision).  Identities / priors / mothers / estimator are the D7-C contract
# reused through these narrow aliases.
# --------------------------------------------------------------------------
Q = d7c.Q
N = d7c.N
BOB_DIM = d7c.BOB_DIM
N_A = d7c.N_A
MODEL_F_ROOT = d7c.MODEL_F_ROOT

F_VALUES = d7c.F_VALUES
L1_ROWS = d7c.L1_ROWS
L2_ROWS = d7c.L2_ROWS
ROWS = d7c.ROWS
LAYERS = d7c.LAYERS
BLOCK_SEEDS = d7c.BLOCK_SEEDS
L1_GRAPH_SEED = d7c.L1_GRAPH_SEED
L2_GRAPH_SEED = d7c.L2_GRAPH_SEED
L1_K_MIN = d7c.L1_K_MIN
L2_K_MIN = d7c.L2_K_MIN

LAMBDA_STAR = d7c.LAMBDA_STAR
DECODER_FLOOR = d7c.DECODER_FLOOR
MAX_ITER = d7c.MAX_ITER
DAMPING_ALPHA = d7c.DAMPING_ALPHA

DIRECTIONS = ("L1_TO_L2", "L2_TO_L1")
SOURCE_LAYER = {"L1_TO_L2": "L1", "L2_TO_L1": "L2"}
TARGET_LAYER = {"L1_TO_L2": "L2", "L2_TO_L1": "L1"}
# (condition, layer) per (direction, role); transfer priors are built, not
# looked up, so transfer conditions name the transfer only.
SLOT_ROLE = {
    ("L1_TO_L2", "SOURCE"): ("L1_MARGINAL", "L1"),
    ("L1_TO_L2", "CONTROL"): ("L2_MARGINAL", "L2"),
    ("L1_TO_L2", "TRANSFER"): ("L2_TRANSFER", "L2"),
    ("L2_TO_L1", "SOURCE"): ("L2_MARGINAL", "L2"),
    ("L2_TO_L1", "CONTROL"): ("L1_MARGINAL", "L1"),
    ("L2_TO_L1", "TRANSFER"): ("L1_TRANSFER", "L1"),
}
ROLE_ORDER = ("SOURCE", "CONTROL", "TRANSFER")

SLOT_COUNT = 192
MANDATORY_CALLS = 128
MAX_CALLS = 192

PER_CALL_WATCHDOG_S = 120.0
STORED_WALL_LIMIT_S = 1500.0
OUTER_WATCHDOG_S = 1800.0
OUTER_GRACE_S = 30.0
RSS_LIMIT_BYTES = 2 * 1024**3

D7E_AUTH_KEY = "d7e_execution_authorized"
STATE_REL_PATH = ("docs/research_cycles/"
                  "V72P2D7-GF32-CROSS-LAYER-DISCRIMINATOR/cycle_state.yaml")

# Frozen run terminals T1..T12 (exact strings, exact priority).
TERMINALS = (
    "D7_E_PRE_EXECUTION_BLOCKED",
    "D7_E_WATCHDOG_TIMEOUT_VOID",
    "D7_E_NONFINITE_OR_CRASH_BLOCKED",
    "D7_E_RESOURCE_OVERRUN",
    "D7_E_INCOMPLETE_CORE_CALL_MATRIX",
    "D7_E_PROVENANCE_COVERAGE_BLOCKED",
    "D7_E_BIDIRECTIONAL_TRANSFER_LIFT",
    "D7_E_L1_TO_L2_TRANSFER_LIFT",
    "D7_E_L2_TO_L1_TRANSFER_LIFT",
    "D7_E_TRANSFER_REGRESSION",
    "D7_E_NO_USEFUL_TRANSFER_RECOVERY",
    "D7_E_MIXED_TRANSFER_DIAGNOSTIC",
)
(T_PRE_EXEC, T_WATCHDOG, T_CRASH, T_RESOURCE, T_INCOMPLETE, T_COVERAGE,
 T_BIDIRECTIONAL, T_L1_TO_L2, T_L2_TO_L1, T_REGRESSION, T_NO_RECOVERY,
 T_MIXED) = TERMINALS

# Frozen stratum labels (first-match order in ``classify_stratum``).
S_STRONG = "STRONG_TRANSFER_LIFT"
S_REGRESSION = "TRANSFER_REGRESSION"
S_NO_RECOVERY = "NO_TRANSFER_RECOVERY"
S_CONTROL = "CONTROL_ALREADY_RECOVERS"
S_AMBIGUOUS = "AMBIGUOUS_TRANSFER_EFFECT"
STRATUM_LABELS = (S_STRONG, S_REGRESSION, S_NO_RECOVERY, S_CONTROL,
                  S_AMBIGUOUS)

COVERAGE_OK = "COVERAGE_OK"
COVERAGE_BLOCKED = "PROVENANCE_COVERAGE_BLOCKED"

# Accepted provenance token that alone admits a conditioned transfer prior.
# Pinned by tests to the accepted v35 token; the gate itself delegates to the
# accepted guard, never to this literal.
CHECK_UPDATED = "CHECK_UPDATED"

# Current-belief record labels (iterations-derived, never a provenance token).
PRIOR_ONLY_CURRENT_BELIEF = d7c.PRIOR_ONLY_CURRENT_BELIEF
CHECK_UPDATED_CURRENT_BELIEF = d7c.CHECK_UPDATED_CURRENT_BELIEF
CURRENT_BELIEF_LABELS = d7c.CURRENT_BELIEF_LABELS

# Named deterministic blocked-transfer reasons (no decoder call made).
ELIGIBLE = "ELIGIBLE"
BLOCK_SOURCE_CRASH = "SOURCE_CRASH"
BLOCK_SOURCE_NONFINITE = "SOURCE_NONFINITE"
BLOCK_SOURCE_BELIEF_SHAPE = "SOURCE_BELIEF_SHAPE_INVALID"
BLOCK_PROVENANCE = "PROVENANCE_BLOCKED"

SEVEN_FILES = ("manifest.json", "decoder_records.csv", "transfer_pairs.csv",
               "stratum_summary.csv", "summary.json", "report.md",
               "command_log.txt")

RECORD_FIELDS = [
    "slot_idx", "f", "seed", "direction", "role", "condition", "layer",
    "rows", "n", "exact", "syndrome_ok", "iterations", "status", "finite",
    "symbol_errors", "unsatisfied_checks", "wall_s", "rss_bytes",
    "belief_max_prob", "belief_mean_true_p", "belief_mean_entropy",
    "beliefs_conditioned", "current_belief_label", "belief_provenance",
    "belief_shape_ok", "transfer_eligible",
]
PAIR_FIELDS = [
    "pair_idx", "f", "seed", "direction", "source_layer", "target_layer",
    "rows", "n", "control_slot_idx", "transfer_slot_idx",
    "control_exact", "transfer_exact", "control_only_exact",
    "transfer_only_exact", "both_exact", "neither_exact",
    "control_syndrome_ok", "transfer_syndrome_ok",
    "control_only_syndrome_ok", "transfer_only_syndrome_ok",
    "both_syndrome_ok", "neither_syndrome_ok",
    "source_exact", "source_provenance",
]
STRATUM_FIELDS = [
    "stratum_idx", "f", "direction", "source_layer", "target_layer",
    "blocks", "eligible_count", "blocked_count",
    "control_exact_count", "transfer_exact_count",
    "control_only_exact_count", "transfer_only_exact_count",
    "both_exact_count", "neither_exact_count",
    "control_syndrome_ok_count", "transfer_syndrome_ok_count",
    "control_only_syndrome_ok_count", "transfer_only_syndrome_ok_count",
    "both_syndrome_ok_count", "neither_syndrome_ok_count",
    "nonfinite_count", "crash_count", "stratum_label", "coverage_status",
]

_ESTIMATOR_ID = d7c._ESTIMATOR_ID
_DECODER_IDS = {
    "SOURCE": ("v35.decode_row_layered_fftqspa(h, prior, syndrome, "
                "max_iter=90, damping_alpha=1.0, warm_beliefs=None, "
                "field=None)"),
    "TARGET": ("v35.decode_row_layered_fftqspa(h, prior, syndrome, "
                "max_iter=90, damping_alpha=1.0, warm_beliefs=None, "
                "field=None)"),
}
_MOTHER_EXPR = d7c._MOTHER_EXPR
_CALL_ORDER = ("for f in [1.0, 1.2]: for seed in 2026091300..2026091315: "
               "L1_TO_L2_SOURCE_L1_MARGINAL, "
               "L1_TO_L2_TARGET_L2_CONTROL_MARGINAL, "
               "L1_TO_L2_TARGET_L2_TRANSFER, "
               "L2_TO_L1_SOURCE_L2_MARGINAL, "
               "L2_TO_L1_TARGET_L1_CONTROL_MARGINAL, "
               "L2_TO_L1_TARGET_L1_TRANSFER")

# Formal/dev roots that must never be an output target (name-based guard).
PROTECTED_ROOTS = tuple(d7c.PROTECTED_ROOTS) + (
    "workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae",
    "workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964",
)
OUT_ROOT_PREFIX = "d7_e_cross_layer_discriminator_"

_EXECUTION_CONSUMED = False  # single-use guard within one process


class NotAuthorizedError(PermissionError):
    """Raised when a run is entered without the D7-E authorization key."""


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
    """Parse the flat ``key: value`` D7-E cycle-state file (no YAML dep)."""
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
        return bool(dict(state).get(D7E_AUTH_KEY, False))
    except Exception:
        return False


def _require_authorized(authorized: bool) -> None:
    if not authorized:
        raise NotAuthorizedError(
            "D7-E execution is not authorized; refusing before any work")


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
# RSS (stdlib resource only; explicit Linux KiB -> bytes)
# --------------------------------------------------------------------------

def _read_ru_maxrss():
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def get_rss_bytes():
    """Current-process RSS bytes from ``ru_maxrss`` KiB; None when unavailable.

    Explicit WSL/Linux conversion: ``ru_maxrss`` is KiB on Linux, so
    ``bytes = ru_maxrss * 1024``.  Absence and non-numeric values return None
    (the preflight then blocks); the probe is stdlib-only.
    """
    try:
        raw = _read_ru_maxrss()
    except Exception:
        return None
    try:
        return int(raw) * 1024
    except Exception:
        return None


def _probe_rss_valid(probe):
    """Return (int_bytes, True) only for finite positive numeric probes."""
    try:
        raw = probe()
    except Exception:
        return None, False
    if raw is None:
        return None, False
    try:
        value = float(raw)
    except Exception:
        return None, False
    if not math.isfinite(value) or value <= 0:
        return None, False
    return int(value), True


# --------------------------------------------------------------------------
# Frozen 192-slot matrix
# --------------------------------------------------------------------------

def frozen_slots() -> list:
    """All 192 frozen slots in the frozen order; ``slot_idx`` 1-based.

    Outer ``f`` in ``[1.0, 1.2]``, seeds ``2026091300..2026091315``
    ascending, six slots per ``(f, seed)`` in the frozen role order for
    ``L1_TO_L2`` then ``L2_TO_L1``.
    """
    slots = []
    for f in F_VALUES:
        for seed in BLOCK_SEEDS:
            for direction in DIRECTIONS:
                for role in ROLE_ORDER:
                    condition, layer = SLOT_ROLE[(direction, role)]
                    slots.append({
                        "slot_idx": len(slots) + 1,
                        "f": float(f),
                        "seed": int(seed),
                        "direction": direction,
                        "role": role,
                        "condition": condition,
                        "layer": layer,
                        "rows": int(ROWS[layer][float(f)]),
                        "n": N,
                    })
    return slots


# --------------------------------------------------------------------------
# Narrow D7-C reuse: joint / prior / mother / estimator / block preparation
# --------------------------------------------------------------------------

build_joint = d7c.build_joint
condition_prior_qn = d7c.condition_prior_qn
decoder_prior = d7c.decoder_prior
build_mother = d7c.build_mother
_default_model_f_loader = d7c._default_model_f_loader


def prepare_inputs(*, joint=None, model_f_root=None, model_f_loader=None,
                   block_sampler=None, mothers=None, repo=None) -> dict:
    """Frozen preparation order (D7-C reuse) plus the 192-slot matrix.

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
    ctx["slots"] = frozen_slots()
    if len(ctx["slots"]) != SLOT_COUNT:
        raise AssertionError("frozen slot matrix must hold %d slots"
                             % (SLOT_COUNT,))
    return ctx


# --------------------------------------------------------------------------
# Provenance gate (accepted BP Alternative A contract, lazy bind)
# --------------------------------------------------------------------------

def require_check_updated(provenance, *, consumer="D7-E transfer gate"):
    """Fail closed unless ``provenance`` is exactly ``CHECK_UPDATED``.

    Delegates to the accepted D5 provenance helper (which lazily binds the
    accepted v35 guard); prior-only, missing/``None``/unknown and warm-start
    tokens all raise.  No decoder is bound or called here.
    """
    return d7c.d5._require_check_updated_provenance(
        provenance, consumer=consumer)


def belief_provenance_error():
    """The accepted refusal type (lazy v35 bind; never at import)."""
    return _load_v35().UnconditionedBeliefProvenanceError


def _result_provenance(result):
    """Extract the raw ``belief_provenance`` token (or ``None``) from one
    decoder return, mirroring the accepted six-value result semantics."""
    if isinstance(result, dict):
        return result.get("belief_provenance")
    return getattr(result, "belief_provenance", None)


def check_source_eligibility(*, status, finite, belief_shape_ok,
                             provenance):
    """Pure scalar gate: may this source belief feed one transfer call?

    Returns ``(eligible, reason)`` with a named deterministic reason.
    Source exactness never gates.  Refusals happen before any mixer or
    target-decoder contact; unexpected error types propagate loudly instead
    of being sold as blocks.
    """
    if str(status).startswith("crash:"):
        return False, BLOCK_SOURCE_CRASH
    if not bool(finite):
        return False, BLOCK_SOURCE_NONFINITE
    if not bool(belief_shape_ok):
        return False, BLOCK_SOURCE_BELIEF_SHAPE
    try:
        require_check_updated(provenance)
    except Exception as exc:
        if isinstance(exc, belief_provenance_error()):
            return False, BLOCK_PROVENANCE
        raise
    return True, ELIGIBLE


# --------------------------------------------------------------------------
# Transfer math (frozen R09 formulas; transient q, never persisted)
# --------------------------------------------------------------------------

def softmax_source_q(log_beliefs) -> np.ndarray:
    """Transient source APP approximation: rowwise softmax of one
    ``CHECK_UPDATED`` current log belief, shape ``(n, 32)``."""
    bel = np.asarray(log_beliefs, dtype=np.float64)
    if bel.ndim != 2 or bel.shape[1] != Q:
        raise ValueError("source log belief must have shape (n, 32), got %r"
                         % (bel.shape,))
    if not np.all(np.isfinite(bel)):
        raise ValueError("source log belief must be finite")
    return d7c._softmax_rows(bel)


def _transfer_conditional(joint, bob, axis: str) -> np.ndarray:
    """Per-position conditional slice from the accepted joint.

    ``axis="U2|U1"`` returns ``cond[i,u1,u2] = P(U2|b_i,u1)``;
    ``axis="U1|U2"`` returns ``cond[i,u2,u1] = P(U1|b_i,u2)``; zero-mass
    slices fall back to uniform ``1/32`` (the accepted D5 convention).
    """
    j = np.asarray(joint, dtype=np.float64)
    if j.ndim != 3 or j.shape[0] != Q or j.shape[1] != Q:
        raise ValueError("joint must have shape (32, 32, B), got %r"
                         % (j.shape,))
    bob = np.asarray(bob, dtype=np.int64).reshape(-1)
    n = int(bob.shape[0])
    if np.any(bob < 0) or np.any(bob >= j.shape[2]):
        raise ValueError("bob symbols out of range for joint Bob dim")
    if axis == "U2|U1":
        seg = j[:, :, bob].transpose(2, 0, 1)  # (n, u1, u2)
    elif axis == "U1|U2":
        seg = j[:, :, bob].transpose(2, 1, 0)  # (n, u2, u1)
    else:
        raise ValueError("unknown conditional axis %r" % (axis,))
    mass = seg.sum(axis=2, keepdims=True)
    return np.where(mass > 0, seg / np.maximum(mass, 1e-300), 1.0 / Q)


def _check_mixer_q(q, n: int) -> np.ndarray:
    arr = np.asarray(q, dtype=np.float64)
    if arr.shape != (n, Q):
        raise ValueError("source q must have shape (%d, 32), got %r"
                         % (n, arr.shape))
    if not np.all(np.isfinite(arr)) or np.any(arr < 0):
        raise ValueError("source q must be finite and nonnegative")
    return arr


def transfer_prior_l1_to_l2(joint, bob, q1) -> np.ndarray:
    """``P_transfer(U2|B) = sum_u1 q1(u1) P(U2|B,u1)``; ``(n, 32)`` decoder
    prior with the single accepted floor/renorm applied once."""
    n = int(np.asarray(bob, dtype=np.int64).reshape(-1).shape[0])
    q = _check_mixer_q(q1, n)
    cond = _transfer_conditional(joint, bob, "U2|U1")
    out = np.einsum("nu,nuv->nv", q, cond)
    return d7c.d5._floor_renorm(out, DECODER_FLOOR)


def transfer_prior_l2_to_l1(joint, bob, q2) -> np.ndarray:
    """``P_transfer(U1|B) = sum_u2 q2(u2) P(U1|B,u2)``; ``(n, 32)`` decoder
    prior with the single accepted floor/renorm applied once."""
    n = int(np.asarray(bob, dtype=np.int64).reshape(-1).shape[0])
    q = _check_mixer_q(q2, n)
    cond = _transfer_conditional(joint, bob, "U1|U2")
    out = np.einsum("nu,nuv->nv", q, cond)
    return d7c.d5._floor_renorm(out, DECODER_FLOOR)


def build_transfer_prior(joint, direction: str, bob, q) -> np.ndarray:
    """Direction-dispatched mixer entry point (the fail-closed spy boundary:
    reached only after ``check_source_eligibility`` passes)."""
    if direction == "L1_TO_L2":
        return transfer_prior_l1_to_l2(joint, bob, q)
    if direction == "L2_TO_L1":
        return transfer_prior_l2_to_l1(joint, bob, q)
    raise ValueError("unknown direction %r" % (direction,))


# --------------------------------------------------------------------------
# Decoder dispatch (dual roles, DI) and lazy production bind
# --------------------------------------------------------------------------

def dispatch_decoder(key: str, decoder_fns, h_matrix, prior_pq, syndrome):
    """Route one call to the role decoder with the frozen three arrays."""
    if key not in ("SOURCE", "TARGET"):
        raise ValueError("unknown decoder key %r" % (key,))
    try:
        fn = decoder_fns[key]
    except Exception as exc:
        raise ValueError("decoder_fns missing key %r" % (key,)) from exc
    return fn(h_matrix, prior_pq, syndrome)


def _load_v35():
    """Lazy production v35 bind (never on import); package-first, file fallback."""
    try:
        from comparison_bench.formal_ir import v35_algorithm_development as v35
    except ModuleNotFoundError:
        v35_path = (Path(__file__).resolve().parent
                    / "v35_algorithm_development.py")
        spec = _ilu.spec_from_file_location(
            "comparison_bench.formal_ir.v35_algorithm_development",
            str(v35_path))
        if spec is None or spec.loader is None:
            raise ImportError("cannot load sibling v35 module at %s" % (v35_path,))
        v35 = _ilu.module_from_spec(spec)
        sys.modules[spec.name] = v35
        spec.loader.exec_module(v35)
    return v35


def bind_row_layered_decoders() -> dict:
    """Lazy production bind of the frozen row-layered call shape (no calls).

    Both roles use the accepted cold row-layered shape with ``max_iter=90``,
    unit damping and no warm start.  Each
    wrapper exposes its exact production target as ``.target`` for bind
    qualification.
    """
    v35 = _load_v35()

    def source(h_matrix, prior_pq, syndrome):
        return v35.decode_row_layered_fftqspa(
            h_matrix, prior_pq, syndrome, max_iter=MAX_ITER,
            damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)

    def target(h_matrix, prior_pq, syndrome):
        return v35.decode_row_layered_fftqspa(
            h_matrix, prior_pq, syndrome, max_iter=MAX_ITER,
            damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)

    source.target = v35.decode_row_layered_fftqspa
    target.target = v35.decode_row_layered_fftqspa
    return {"SOURCE": source, "TARGET": target}


# --------------------------------------------------------------------------
# Per-call evaluation (scalar records; exact/syndrome isolation)
# --------------------------------------------------------------------------

def _belief_label(iterations: int) -> str:
    return (CHECK_UPDATED_CURRENT_BELIEF if int(iterations) > 0
            else PRIOR_ONLY_CURRENT_BELIEF)


def _source_belief_bundle(result, n_pos: int) -> dict:
    """Parsed source belief triple: orientation-fixed array (or ``None``),
    raw provenance token and the scalar shape verdict."""
    try:
        _, _, _, beliefs, _ = d7c._parse_decoder_result(result)
    except Exception:
        return {"beliefs": None, "provenance": _result_provenance(result),
                "shape_ok": False}
    provenance = _result_provenance(result)
    shape_ok = bool(
        beliefs is not None
        and np.asarray(beliefs).shape == (int(n_pos), Q)
        and np.all(np.isfinite(np.asarray(beliefs, dtype=np.float64))))
    return {"beliefs": beliefs if shape_ok else None,
            "provenance": provenance, "shape_ok": shape_ok}


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
    observed = d7c.d5._gf32_syndrome(h_prefix, x_hat)
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
        "direction": slot["direction"],
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
        "direction": slot["direction"],
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
# Sequential 192-slot loop (no retry / resume / concurrency)
# --------------------------------------------------------------------------

def execute_slots(context: dict, decoder_fns, *, clock=None,
                  rss_probe=None) -> dict:
    """Run the frozen 192-slot matrix once, sequentially, stopping on the
    first higher-priority budget/validity stop.

    Mandatory source/control slots always invoke their decoder; transfer
    slots invoke the target decoder exactly when the cached source return is
    eligible, otherwise they are recorded non-invocations (no call, no wall
    cost).  No replacement, retry or resume.
    """
    clock = clock or time.perf_counter
    rss_probe = rss_probe or get_rss_bytes
    records = []
    sources = {}
    stored_wall = 0.0
    stop = None
    for slot in context["slots"]:
        if len(records) >= MAX_CALLS:  # hard cap; matrix holds 192 slots
            break
        f = float(slot["f"])
        seed = int(slot["seed"])
        direction = slot["direction"]
        role = slot["role"]
        layer = slot["layer"]
        block = context["blocks"][seed]
        h_prefix = context["mothers"][layer][:int(slot["rows"])]
        x_true = np.asarray(block["u1"] if layer == "L1" else block["u2"],
                            dtype=np.int64)
        key = "SOURCE" if role == "SOURCE" else "TARGET"

        if role == "TRANSFER":
            src = sources[(f, seed, direction)]
            eligible, _ = check_source_eligibility(
                status=src["record"]["status"],
                finite=src["record"]["finite"],
                belief_shape_ok=src["shape_ok"],
                provenance=src["provenance"])
            if not eligible:
                continue  # blocked: recorded non-invocation, never a call
            q = softmax_source_q(src["beliefs"])  # transient, never persisted
            prior_pq = build_transfer_prior(context["joint"], direction,
                                            block["bob"], q)
            syndrome = d7c.d5._gf32_syndrome(h_prefix, x_true)
        else:
            prior_qn = condition_prior_qn(context["joint"],
                                          slot["condition"], block)
            prior_pq = decoder_prior(prior_qn)
            syndrome = d7c.d5._gf32_syndrome(h_prefix, x_true)

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
            sources[(f, seed, direction)] = {
                "beliefs": bundle["beliefs"],
                "provenance": bundle["provenance"],
                "shape_ok": bundle["shape_ok"],
                "record": record,
            }
        elif role == "SOURCE":
            sources[(f, seed, direction)] = {
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
# Transfer pairs, strata and terminals (shared by run and verifier)
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


def compute_transfer_pairs(records) -> list:
    """One row per eligible control/transfer pair present in ``records``.

    Pairs join on the shared ``(f, seed, direction)`` identity; the source
    exact flag rides along as context only and never gates anything.
    """
    sources, controls, transfers = {}, {}, {}
    for record in records:
        key = (float(record["f"]), int(record["seed"]),
               record["direction"])
        if record["role"] == "SOURCE":
            sources[key] = record
        elif record["role"] == "CONTROL":
            controls[key] = record
        elif record["role"] == "TRANSFER":
            transfers[key] = record
    rows = []
    for key in sorted(sources):
        source = sources[key]
        if not _as_bool(source.get("transfer_eligible")):
            continue
        control = controls.get(key)
        transfer = transfers.get(key)
        if control is None or transfer is None:
            continue  # truncated run: the verifier judges the missing row

        def _flag(record, field):
            return bool(_as_bool(record[field]))

        c_exact, t_exact = _flag(control, "exact"), _flag(transfer, "exact")
        c_syn, t_syn = _flag(control, "syndrome_ok"), _flag(transfer, "syndrome_ok")
        f, seed, direction = key
        rows.append({
            "pair_idx": len(rows) + 1,
            "f": f, "seed": seed, "direction": direction,
            "source_layer": SOURCE_LAYER[direction],
            "target_layer": TARGET_LAYER[direction],
            "rows": int(control["rows"]), "n": int(control["n"]),
            "control_slot_idx": int(control["slot_idx"]),
            "transfer_slot_idx": int(transfer["slot_idx"]),
            "control_exact": c_exact, "transfer_exact": t_exact,
            "control_only_exact": bool(c_exact and not t_exact),
            "transfer_only_exact": bool(t_exact and not c_exact),
            "both_exact": bool(c_exact and t_exact),
            "neither_exact": bool(not c_exact and not t_exact),
            "control_syndrome_ok": c_syn, "transfer_syndrome_ok": t_syn,
            "control_only_syndrome_ok": bool(c_syn and not t_syn),
            "transfer_only_syndrome_ok": bool(t_syn and not c_syn),
            "both_syndrome_ok": bool(c_syn and t_syn),
            "neither_syndrome_ok": bool(not c_syn and not t_syn),
            "source_exact": _flag(source, "exact"),
            "source_provenance": source.get("belief_provenance", ""),
        })
    return rows


def classify_stratum(*, eligible, transfer_only_exact, control_only_exact,
                     transfer_exact, control_exact,
                     crash_nonfinite) -> str:
    """Frozen first-match stratum classification (prereg R11).

    Returns ``""`` exactly when the stratum is coverage-blocked
    (``eligible < 12``); the caller records the coverage reason.
    """
    if eligible < 12:
        return ""
    if (transfer_only_exact >= 4 and control_only_exact <= 1
            and transfer_exact >= 4 and crash_nonfinite == 0):
        return S_STRONG
    if control_only_exact >= 4 and transfer_only_exact <= 1:
        return S_REGRESSION
    if transfer_exact <= 1 and control_exact <= 1:
        return S_NO_RECOVERY
    if control_exact >= 12:
        return S_CONTROL
    return S_AMBIGUOUS


def compute_strata(records, paired_rows) -> list:
    """Four frozen stratum rows (2 f x 2 directions) with first-match labels."""
    strata = []
    for f in F_VALUES:
        for direction in DIRECTIONS:
            stratum_records = [r for r in records
                               if float(r["f"]) == float(f)
                               and r["direction"] == direction]
            sources = [r for r in stratum_records if r["role"] == "SOURCE"]
            eligible = int(sum(1 for r in sources
                               if _as_bool(r.get("transfer_eligible"))))
            blocked = int(len(sources) - eligible)
            paired = [row for row in paired_rows
                      if float(row["f"]) == float(f)
                      and row["direction"] == direction]

            def _count(items, field):
                return int(sum(1 for row in items if _as_bool(row[field])))

            crashes = int(sum(1 for r in stratum_records
                              if str(r["status"]).startswith("crash:")))
            nonfinite = int(sum(1 for r in stratum_records
                                if (not _as_bool(r["finite"]))
                                and not str(r["status"]).startswith("crash:")))
            label = classify_stratum(
                eligible=eligible,
                transfer_only_exact=_count(paired, "transfer_only_exact"),
                control_only_exact=_count(paired, "control_only_exact"),
                transfer_exact=_count(paired, "transfer_exact"),
                control_exact=_count(paired, "control_exact"),
                crash_nonfinite=crashes + nonfinite)
            strata.append({
                "stratum_idx": len(strata) + 1,
                "f": float(f), "direction": direction,
                "source_layer": SOURCE_LAYER[direction],
                "target_layer": TARGET_LAYER[direction],
                "blocks": len(BLOCK_SEEDS),
                "eligible_count": eligible,
                "blocked_count": blocked,
                "control_exact_count": _count(paired, "control_exact"),
                "transfer_exact_count": _count(paired, "transfer_exact"),
                "control_only_exact_count": _count(paired, "control_only_exact"),
                "transfer_only_exact_count": _count(paired, "transfer_only_exact"),
                "both_exact_count": _count(paired, "both_exact"),
                "neither_exact_count": _count(paired, "neither_exact"),
                "control_syndrome_ok_count": _count(paired, "control_syndrome_ok"),
                "transfer_syndrome_ok_count": _count(paired, "transfer_syndrome_ok"),
                "control_only_syndrome_ok_count": _count(
                    paired, "control_only_syndrome_ok"),
                "transfer_only_syndrome_ok_count": _count(
                    paired, "transfer_only_syndrome_ok"),
                "both_syndrome_ok_count": _count(paired, "both_syndrome_ok"),
                "neither_syndrome_ok_count": _count(paired, "neither_syndrome_ok"),
                "nonfinite_count": nonfinite,
                "crash_count": crashes,
                "stratum_label": label,
                "coverage_status": (COVERAGE_BLOCKED if eligible < 12
                                    else COVERAGE_OK),
            })
    return strata


def classify_terminal(agg: dict) -> str:
    """Frozen T1..T12 first-applicable terminal selection (prereg R12)."""
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
    strong = {(f, direction): labels.get((f, direction)) == S_STRONG
              for f in F_VALUES for direction in DIRECTIONS}
    if any(strong[(f, "L1_TO_L2")] and strong[(f, "L2_TO_L1")]
           for f in F_VALUES):
        return T_BIDIRECTIONAL
    strong_l12 = any(strong[(f, "L1_TO_L2")] for f in F_VALUES)
    strong_l21 = any(strong[(f, "L2_TO_L1")] for f in F_VALUES)
    if strong_l12 and not strong_l21:
        return T_L1_TO_L2
    if strong_l21 and not strong_l12:
        return T_L2_TO_L1
    if (any(v == S_REGRESSION for v in labels.values())
            and not any(v == S_STRONG for v in labels.values())):
        return T_REGRESSION
    if labels and all(v == S_NO_RECOVERY for v in labels.values()):
        return T_NO_RECOVERY
    return T_MIXED


def _eligible_by_stratum(records) -> dict:
    out = {(float(f), direction): 0
           for f in F_VALUES for direction in DIRECTIONS}
    for record in records:
        if record.get("role") != "SOURCE":
            continue
        if _as_bool(record.get("transfer_eligible")):
            out[(float(record["f"]), record["direction"])] += 1
    return out


def _mandatory_present(records) -> int:
    return int(sum(1 for r in records if r.get("role") in ("SOURCE", "CONTROL")))


def terminal_from_records(records, paired_rows, stratum_rows) -> str:
    """Recompute the run terminal from scalar records + pair/stratum rows."""
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
    labels = {(float(row["f"]), row["direction"]): row.get("stratum_label", "")
              for row in stratum_rows}
    coverage = any(count < 12
                   for count in _eligible_by_stratum(records).values())
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
    with open(out / "transfer_pairs.csv", "w", encoding="utf-8",
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
        fh.write("# D7-E provenance-safe cross-layer discriminator\n\n")
        fh.write("terminal: %s\n" % (summary.get("terminal"),))
        fh.write("calls_completed: %s\n" % (summary.get("calls_completed"),))
        fh.write("transfer_invoked: %s\n" % (summary.get("transfer_invoked"),))
        fh.write("transfer_blocked: %s\n" % (summary.get("transfer_blocked"),))
        fh.write("stored_wall_s: %s\n" % (summary.get("stored_wall_s"),))
        for row in stratum_rows:
            fh.write("f=%s %s: %s (%s)\n" % (
                row["f"], row["direction"], row["stratum_label"],
                row["coverage_status"]))
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
            raise ValueError("transfer_pairs.csv schema mismatch: %r"
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
        "directions": list(DIRECTIONS),
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
    for key in ("slot_idx", "direction", "role", "condition", "layer",
                "rows", "n", "seed"):
        if key == "f":
            continue
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
    if key in ("direction", "role", "condition", "layer", "stratum_label",
               "coverage_status", "source_provenance"):
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
    """Walk file records against frozen slots; blocked transfers are the only
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
                      record["direction"])] = _as_bool(
                          record.get("transfer_eligible"))
    matched = 0
    stop_pos = None
    stored = 0.0
    for position, slot in enumerate(slots):
        record = by_slot.get(int(slot["slot_idx"]))
        if record is None:
            if slot["role"] == "TRANSFER" and not eligible.get(
                    (float(slot["f"]), int(slot["seed"]),
                     slot["direction"]), False):
                continue  # blocked slot: recorded non-invocation
            if stop_pos is None:
                problems.append("slot %d (%s %s %s) has no record without "
                                "an earlier stop" % (
                                    slot["slot_idx"], slot["direction"],
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

    Recomputes schema, slot order, mandatory 128 calls, eligible transfer
    invocation count, uniqueness, no replacement, pair identity, provenance
    gate, exact/syndrome isolation, four labels, terminal, wall/RSS and the
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
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "problems": problems + ["json: %r" % (exc,)],
                "records": 0}
    records, paired, strata = [], [], []
    try:
        records = _read_records(out / "decoder_records.csv")
        paired = _read_paired(out / "transfer_pairs.csv")
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
    recomputed_paired = compute_transfer_pairs(records)
    if len(paired) != len(recomputed_paired):
        problems.append("transfer_pairs.csv row count %d != recomputed %d"
                        % (len(paired), len(recomputed_paired)))
    else:
        for actual, expected in zip(paired, recomputed_paired):
            if not _rows_equal_scalar(actual, expected, PAIR_FIELDS):
                problems.append(
                    "pair row f=%s seed=%s %s does not recompute"
                    % (actual.get("f"), actual.get("seed"),
                       actual.get("direction")))
    for row in paired:
        if row.get("source_provenance") != CHECK_UPDATED:
            problems.append("pair row f=%s seed=%s %s has non-admitting "
                            "source provenance %r"
                            % (row.get("f"), row.get("seed"),
                               row.get("direction"),
                               row.get("source_provenance")))
    recomputed_strata = compute_strata(records, recomputed_paired)
    if len(strata) != 4:
        problems.append("stratum_summary.csv row count %d != 4" % (len(strata),))
    else:
        for actual, expected in zip(strata, recomputed_strata):
            if not _rows_equal_scalar(actual, expected, STRATUM_FIELDS):
                problems.append(
                    "stratum row %s (%s %s) does not recompute"
                    % (actual.get("stratum_idx"), actual.get("f"),
                       actual.get("direction")))
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
            1 for r in records if r.get("role") == "TRANSFER"):
        problems.append("summary transfer_invoked != transfer row count")
    eligible_total = sum(1 for r in records
                         if r.get("role") == "SOURCE"
                         and _as_bool(r.get("transfer_eligible")))
    source_total = sum(1 for r in records if r.get("role") == "SOURCE")
    if _as_int(summary.get("transfer_blocked")) != (source_total - eligible_total):
        # blocked transfer slots == source slots whose gate refused.
        problems.append("summary transfer_blocked does not recompute")
    expected_labels = [
        {"stratum_idx": int(row["stratum_idx"]), "f": float(row["f"]),
         "direction": row["direction"],
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
        "change": "v72p2d7-provenance-safe-cross-layer-discriminator",
        "contract": "R1",
        "out_root_name": name,
        "uuid": uuid,
        "estimator": _ESTIMATOR_ID,
        "lambda_star": LAMBDA_STAR,
        "model_f_root": MODEL_F_ROOT,
        "model_f_files": list(model_f_files),
        "n": N,
        "f_values": [float(f) for f in F_VALUES],
        "l1_rows": {"1.0": L1_ROWS[1.0], "1.2": L1_ROWS[1.2]},
        "l2_rows": {"1.0": L2_ROWS[1.0], "1.2": L2_ROWS[1.2]},
        "directions": list(DIRECTIONS),
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
             "direction": row["direction"],
             "stratum_label": row["stratum_label"]}
            for row in strata],
        "slots_scheduled": SLOT_COUNT,
        "mandatory_completed": _mandatory_present(records),
        "transfer_invoked": int(sum(1 for r in records
                                    if r["role"] == "TRANSFER")),
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


def run_cross_layer_discriminator(*, out_root, model_f_root=None,
                                  decoder_fns=None, model_f_loader=None,
                                  joint=None, block_sampler=None, mothers=None,
                                  state=None, state_reader=None, clock=None,
                                  rss_probe=None, command_str="",
                                  repo_root=None) -> dict:
    """One frozen sequential run (production bind only when ``decoder_fns``
    is None and the authorization key is true)."""
    global _EXECUTION_CONSUMED
    if _EXECUTION_CONSUMED:
        raise NotAuthorizedError("D7-E authorization already consumed (no reuse)")
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
    paired = compute_transfer_pairs(records)
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
