"""D7-D flooding-vs-row-layered schedule discriminator core (frozen R1).

Holding every scientific input fixed, the harness decodes each frozen D7-C
identity twice -- once with the certified cold row-layered FFT-QSPA and once
with the independent cold flooding FFT-QSPA -- and records work-normalized
scalar evidence for the 8 ``(f, layer, condition)`` strata.  The only per-call
delta is the schedule; no damping (beyond row-layered ``damping_alpha=1.0``),
clipping, restart, min-sum, warm start, graph change, new prior, more
disclosure, cross-layer feedback or cross-layer APP is added.  D5 / v35 / D7-A
/ D7-C are import-only upstream and are never modified.

This module performs no scientific decoder call and reads no real Model-F
content unless explicitly authorized by a future frozen execution packet; tests
inject fake joint tensors, blocks, mothers, decoders, clock and RSS through the
DI boundary.  ``import``, ``--help``, ``--dry-run``, ``--verify`` and
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
# Frozen constants (D7-D prereg R1; must not change without an OpenSpec
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
CONDITIONS = d7c.CONDITIONS
CONDITION_LAYER = d7c.CONDITION_LAYER

LAMBDA_STAR = d7c.LAMBDA_STAR
DECODER_FLOOR = d7c.DECODER_FLOOR
MAX_ITER = d7c.MAX_ITER
DAMPING_ALPHA = d7c.DAMPING_ALPHA

SCHEDULES = ("ROW_LAYERED", "FLOODING")
IDENTITY_COUNT = 128
MAX_CALLS = 256

PER_CALL_WATCHDOG_S = 120.0
STORED_WALL_LIMIT_S = 1500.0
OUTER_WATCHDOG_S = 1800.0
OUTER_GRACE_S = 30.0
RSS_LIMIT_BYTES = 2 * 1024**3

D7D_AUTH_KEY = "d7d_execution_authorized"
STATE_REL_PATH = ("docs/research_cycles/"
                  "V72P2D7-GF32-SCHEDULE-DISCRIMINATOR/cycle_state.yaml")

# Frozen run terminals T1..T10 (exact strings, exact priority).
TERMINALS = (
    "D7_D_PRE_EXECUTION_BLOCKED",
    "D7_D_WATCHDOG_TIMEOUT_VOID",
    "D7_D_NONFINITE_OR_CRASH_BLOCKED",
    "D7_D_RESOURCE_OVERRUN",
    "D7_D_INCOMPLETE_CALL_MATRIX",
    "D7_D_FLOODING_ADVANTAGE",
    "D7_D_LAYERED_ADVANTAGE",
    "D7_D_SCHEDULE_DEPENDENT_MIXED",
    "D7_D_SCHEDULE_NO_EXACT_DIFFERENCE",
    "D7_D_SCHEDULE_EFFECT_INCONCLUSIVE",
)
(T_PRE_EXEC, T_WATCHDOG, T_CRASH, T_RESOURCE, T_INCOMPLETE, T_FLOODING_ADV,
 T_LAYERED_ADV, T_MIXED, T_NO_DIFF, T_INCONCLUSIVE) = TERMINALS

# Frozen stratum labels (first-match order in ``classify_stratum``).
S_FLOODING = "FLOODING_EXACT_ADVANTAGE"
S_LAYERED = "LAYERED_EXACT_ADVANTAGE"
S_TIE_HIGH = "EXACT_TIE_HIGH"
S_TIE_LOW = "EXACT_TIE_LOW"
S_MIXED = "MIXED_SCHEDULE_EFFECT"
STRATUM_LABELS = (S_FLOODING, S_LAYERED, S_TIE_HIGH, S_TIE_LOW, S_MIXED)

# Current-belief provenance labels (never "posterior" / "APP").
PRIOR_ONLY_CURRENT_BELIEF = d7c.PRIOR_ONLY_CURRENT_BELIEF
CHECK_UPDATED_CURRENT_BELIEF = d7c.CHECK_UPDATED_CURRENT_BELIEF
CURRENT_BELIEF_LABELS = d7c.CURRENT_BELIEF_LABELS

SEVEN_FILES = ("manifest.json", "decoder_records.csv", "paired_schedule.csv",
               "stratum_summary.csv", "summary.json", "report.md",
               "command_log.txt")

RECORD_FIELDS = [
    "call_idx", "identity_idx", "schedule", "f", "seed", "condition", "layer",
    "rows", "n", "exact", "syndrome_ok", "iterations", "status", "finite",
    "symbol_errors", "unsatisfied_checks", "wall_s", "rss_bytes",
    "check_node_updates", "check_edge_updates", "belief_max_prob",
    "belief_mean_true_p", "belief_mean_entropy", "beliefs_conditioned",
    "current_belief_label",
]
PAIRED_FIELDS = [
    "identity_idx", "f", "seed", "condition", "layer", "rows", "n",
    "layered_exact", "flooding_exact", "layered_only_exact",
    "flooding_only_exact", "both_exact", "neither_exact",
    "layered_syndrome_ok", "flooding_syndrome_ok",
    "layered_only_syndrome_ok", "flooding_only_syndrome_ok",
    "both_syndrome_ok", "neither_syndrome_ok", "iteration_diff",
    "check_update_diff", "edge_update_diff", "wall_ratio",
]
STRATUM_FIELDS = [
    "stratum_idx", "f", "layer", "condition", "blocks",
    "layered_exact_count", "flooding_exact_count",
    "layered_only_exact_count", "flooding_only_exact_count",
    "both_exact_count", "neither_exact_count",
    "layered_syndrome_ok_count", "flooding_syndrome_ok_count",
    "layered_only_syndrome_ok_count", "flooding_only_syndrome_ok_count",
    "both_syndrome_ok_count", "neither_syndrome_ok_count",
    "nonfinite_count", "crash_count", "layered_median_iterations",
    "flooding_median_iterations", "layered_median_check_updates",
    "flooding_median_check_updates", "layered_median_edge_updates",
    "flooding_median_edge_updates", "layered_median_wall_s",
    "flooding_median_wall_s", "stratum_label",
]

_ESTIMATOR_ID = d7c._ESTIMATOR_ID
_DECODER_IDS = {
    "ROW_LAYERED": ("v35.decode_row_layered_fftqspa(h, prior, syndrome, "
                    "max_iter=90, damping_alpha=1.0, warm_beliefs=None, "
                    "field=None)"),
    "FLOODING": ("v35.decode_flooding_fftqspa(h, prior, syndrome, "
                 "max_iter=90, field=None)"),
}
_MOTHER_EXPR = d7c._MOTHER_EXPR
_CALL_ORDER = ("for f in [1.0, 1.2]: for seed in 2026091300..2026091315: "
               "for condition in [L1_MARGINAL, L1_ORACLE_U2, L2_MARGINAL, "
               "L2_ORACLE_U1]: ROW_LAYERED; FLOODING")

# Formal/dev roots that must never be an output target (name-based guard).
PROTECTED_ROOTS = tuple(d7c.PROTECTED_ROOTS) + (
    "workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae",
    "workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964",
)
OUT_ROOT_PREFIX = "d7_d_schedule_discriminator_"

_EXECUTION_CONSUMED = False  # single-use guard within one process


class NotAuthorizedError(PermissionError):
    """Raised when a run is entered without the D7-D authorization key."""


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
    """Parse the flat ``key: value`` D7-D cycle-state file (no YAML dep)."""
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
        return bool(dict(state).get(D7D_AUTH_KEY, False))
    except Exception:
        return False


def _require_authorized(authorized: bool) -> None:
    if not authorized:
        raise NotAuthorizedError(
            "D7-D execution is not authorized; refusing before any work")


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
# Frozen identity table and 256-call matrix
# --------------------------------------------------------------------------

def frozen_identities() -> list:
    """All 128 frozen identities, D7-C order, with 1-based ``identity_idx``."""
    identities = []
    for k, ident in enumerate(d7c.frozen_identities(), start=1):
        identities.append({
            "identity_idx": k,
            "f": float(ident["f"]),
            "seed": int(ident["seed"]),
            "condition": ident["condition"],
            "layer": ident["layer"],
            "rows": int(ident["rows"]),
            "n": int(ident["n"]),
        })
    return identities


def frozen_call_matrix() -> list:
    """All 256 frozen calls in order; ``call_idx`` 1-based, schedule pairs."""
    calls = []
    for ident in frozen_identities():
        k = int(ident["identity_idx"])
        for offset, schedule in enumerate(SCHEDULES):
            call = dict(ident)
            del call["identity_idx"]
            call["call_idx"] = 2 * k - 1 + offset
            call["identity_idx"] = k
            call["schedule"] = schedule
            calls.append(call)
    return calls


def _row_degree_sums(mothers) -> dict:
    """Frozen disclosed-row degree sums per ``(layer, rows)`` for edge work."""
    out = {}
    for layer in LAYERS:
        mat = np.asarray(mothers[layer])
        out[layer] = {str(int(rows)): int(np.count_nonzero(mat[:int(rows)]))
                      for rows in sorted(set(ROWS[layer].values()))}
    return out


# --------------------------------------------------------------------------
# Narrow D7-C reuse: joint / prior / mother / estimator / block preparation
# --------------------------------------------------------------------------

build_joint = d7c.build_joint
condition_prior_qn = d7c.condition_prior_qn
decoder_prior = d7c.decoder_prior
build_mother = d7c.build_mother


def prepare_inputs(*, joint=None, model_f_root=None, model_f_loader=None,
                   block_sampler=None, mothers=None, repo=None) -> dict:
    """Frozen preparation order (D7-C reuse) plus the 256-call matrix.

    Model-F -> accepted estimator -> J -> mothers -> 16 blocks -> frozen
    identities and calls.  All inputs are injectable for fake qualification;
    the production path (``joint=None``) loads only the accepted Model-F root
    through the D5 loader chain.
    """
    try:
        ctx = d7c.prepare_inputs(
            joint=joint, model_f_root=model_f_root,
            model_f_loader=model_f_loader, block_sampler=block_sampler,
            mothers=mothers, repo=repo)
    except d7c.PreflightBlocked as exc:
        raise PreflightBlocked("%s: %s" % (T_PRE_EXEC, exc)) from exc
    ctx = dict(ctx)
    ctx["identities"] = frozen_identities()
    ctx["calls"] = frozen_call_matrix()
    ctx["row_degree_sums"] = _row_degree_sums(ctx["mothers"])
    if len(ctx["calls"]) != MAX_CALLS or len(ctx["identities"]) != IDENTITY_COUNT:
        raise AssertionError("frozen call matrix must be %d calls / %d identities"
                             % (MAX_CALLS, IDENTITY_COUNT))
    return ctx


# --------------------------------------------------------------------------
# Decoder dispatch (dual, DI) and lazy production bind
# --------------------------------------------------------------------------

def dispatch_schedule(schedule: str, decoder_fns, h_matrix, prior_pq,
                      syndrome):
    """Route one call to the schedule's decoder with the frozen three arrays."""
    if schedule not in SCHEDULES:
        raise ValueError("unknown schedule %r" % (schedule,))
    return decoder_fns[schedule](h_matrix, prior_pq, syndrome)


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


def bind_schedule_decoders() -> dict:
    """Lazy production bind of both frozen decoder call shapes (no calls).

    ``ROW_LAYERED`` uses the accepted row-layered adapter shape with
    ``max_iter=90``, ``damping_alpha=1.0``, ``warm_beliefs=None``, ``field=None``.
    ``FLOODING`` uses the existing flooding signature with ``max_iter=90``,
    ``field=None`` and no invented damping/warm-start parameter.  Each wrapper
    exposes its exact production target as ``.target`` for bind qualification.
    """
    v35 = _load_v35()

    def row_layered(h_matrix, prior_pq, syndrome):
        return v35.decode_row_layered_fftqspa(
            h_matrix, prior_pq, syndrome, max_iter=MAX_ITER,
            damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)

    def flooding(h_matrix, prior_pq, syndrome):
        return v35.decode_flooding_fftqspa(
            h_matrix, prior_pq, syndrome, max_iter=MAX_ITER, field=None)

    row_layered.target = v35.decode_row_layered_fftqspa
    flooding.target = v35.decode_flooding_fftqspa
    return {"ROW_LAYERED": row_layered, "FLOODING": flooding}


# --------------------------------------------------------------------------
# Per-call evaluation (scalar work-normalized record)
# --------------------------------------------------------------------------

def _belief_label(iterations: int) -> str:
    return (CHECK_UPDATED_CURRENT_BELIEF if int(iterations) > 0
            else PRIOR_ONLY_CURRENT_BELIEF)


def evaluate_call(identity: dict, h_prefix: np.ndarray, block: dict,
                  syndrome: np.ndarray, result, wall_s: float, rss_bytes) -> dict:
    """One completed call -> scalar record with isolated exact/syndrome/work."""
    layer = identity["layer"]
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
    rows = int(identity["rows"])
    completed = int(iterations)
    edge_degree_sum = int(np.count_nonzero(h_prefix))
    return {
        "call_idx": int(identity["call_idx"]),
        "identity_idx": int(identity["identity_idx"]),
        "schedule": identity["schedule"],
        "f": float(identity["f"]),
        "seed": int(identity["seed"]),
        "condition": identity["condition"],
        "layer": layer,
        "rows": rows,
        "n": int(identity["n"]),
        "exact": exact,
        "syndrome_ok": syndrome_ok,
        "iterations": completed,
        "status": str(status),
        "finite": finite,
        "symbol_errors": symbol_errors,
        "unsatisfied_checks": unsatisfied,
        "wall_s": float(wall_s),
        "rss_bytes": int(rss_bytes) if rss_bytes is not None else "",
        "check_node_updates": rows * completed,
        "check_edge_updates": edge_degree_sum * completed,
        "belief_max_prob": diagnostics["belief_max_prob"],
        "belief_mean_true_p": diagnostics["belief_mean_true_p"],
        "belief_mean_entropy": diagnostics["belief_mean_entropy"],
        "beliefs_conditioned": completed > 0,
        "current_belief_label": _belief_label(completed),
    }


def crash_record(identity: dict, exc: BaseException, wall_s: float,
                 rss_bytes) -> dict:
    """A decoder exception is an attempted-but-not-completed call (no retry)."""
    return {
        "call_idx": int(identity["call_idx"]),
        "identity_idx": int(identity["identity_idx"]),
        "schedule": identity["schedule"],
        "f": float(identity["f"]),
        "seed": int(identity["seed"]),
        "condition": identity["condition"],
        "layer": identity["layer"],
        "rows": int(identity["rows"]),
        "n": int(identity["n"]),
        "exact": False,
        "syndrome_ok": False,
        "iterations": "",
        "status": "crash:%s" % (type(exc).__name__,),
        "finite": False,
        "symbol_errors": "",
        "unsatisfied_checks": "",
        "wall_s": float(wall_s),
        "rss_bytes": int(rss_bytes) if rss_bytes is not None else "",
        "check_node_updates": 0,
        "check_edge_updates": 0,
        "belief_max_prob": "",
        "belief_mean_true_p": "",
        "belief_mean_entropy": "",
        "beliefs_conditioned": "",
        "current_belief_label": "",
    }


# --------------------------------------------------------------------------
# Sequential 256-call loop (no retry / resume / concurrency)
# --------------------------------------------------------------------------

def execute_calls(context: dict, decoder_fns, *, clock=None, rss_probe=None) -> dict:
    """Run the frozen 256-call matrix once, sequentially, stopping on the first
    higher-priority budget/validity stop.  No replacement, retry or resume."""
    clock = clock or time.perf_counter
    rss_probe = rss_probe or get_rss_bytes
    records = []
    stored_wall = 0.0
    stop = None
    for identity in context["calls"]:
        if len(records) >= MAX_CALLS:  # hard cap; matrix is exactly MAX_CALLS
            break
        seed = int(identity["seed"])
        layer = identity["layer"]
        block = context["blocks"][seed]
        h_prefix = context["mothers"][layer][:int(identity["rows"])]
        x_true = np.asarray(block["u1"] if layer == "L1" else block["u2"],
                            dtype=np.int64)
        prior_qn = condition_prior_qn(context["joint"], identity["condition"],
                                      block)
        prior_pq = decoder_prior(prior_qn)
        syndrome = d7c.d5._gf32_syndrome(h_prefix, x_true)

        t0 = clock()
        result, exc = None, None
        try:
            result = dispatch_schedule(identity["schedule"], decoder_fns,
                                       h_prefix, prior_pq, syndrome)
        except Exception as caught:  # isolated as a crash, never retried
            exc = caught
        wall = max(0.0, float(clock() - t0))
        rss_bytes, rss_valid = _probe_rss_valid(rss_probe)

        if exc is not None:
            record = crash_record(identity, exc, wall,
                                  rss_bytes if rss_valid else None)
        else:
            try:
                record = evaluate_call(identity, h_prefix, block, syndrome,
                                       result, wall,
                                       rss_bytes if rss_valid else None)
            except Exception as caught:
                record = crash_record(identity, caught, wall,
                                      rss_bytes if rss_valid else None)
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
# Paired schedule rows, strata and terminals (shared by run and verifier)
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


def compute_paired_rows(records) -> list:
    """One frozen paired row per identity (128 rows, frozen order)."""
    by_key = {}
    for record in records:
        key = (float(record["f"]), int(record["seed"]), record["condition"],
               record["schedule"])
        by_key[key] = record
    rows = []
    for identity in frozen_identities():
        f = float(identity["f"])
        seed = int(identity["seed"])
        condition = identity["condition"]
        layered = by_key.get((f, seed, condition, "ROW_LAYERED"))
        flooding = by_key.get((f, seed, condition, "FLOODING"))

        def _flag(record, field):
            if record is None:
                return ""
            return bool(_as_bool(record[field]))

        l_exact = _flag(layered, "exact")
        f_exact = _flag(flooding, "exact")
        l_syn = _flag(layered, "syndrome_ok")
        f_syn = _flag(flooding, "syndrome_ok")
        present = layered is not None and flooding is not None
        row = {
            "identity_idx": int(identity["identity_idx"]),
            "f": f, "seed": seed, "condition": condition,
            "layer": identity["layer"], "rows": int(identity["rows"]),
            "n": int(identity["n"]),
            "layered_exact": l_exact, "flooding_exact": f_exact,
            "layered_only_exact": "",
            "flooding_only_exact": "",
            "both_exact": "",
            "neither_exact": "",
            "layered_syndrome_ok": l_syn, "flooding_syndrome_ok": f_syn,
            "layered_only_syndrome_ok": "",
            "flooding_only_syndrome_ok": "",
            "both_syndrome_ok": "",
            "neither_syndrome_ok": "",
            "iteration_diff": "",
            "check_update_diff": "",
            "edge_update_diff": "",
            "wall_ratio": "",
        }
        if present:
            lx, fx = bool(_as_bool(l_exact)), bool(_as_bool(f_exact))
            ls, fs = bool(_as_bool(l_syn)), bool(_as_bool(f_syn))
            row["layered_only_exact"] = bool(lx and not fx)
            row["flooding_only_exact"] = bool(fx and not lx)
            row["both_exact"] = bool(lx and fx)
            row["neither_exact"] = bool(not lx and not fx)
            row["layered_only_syndrome_ok"] = bool(ls and not fs)
            row["flooding_only_syndrome_ok"] = bool(fs and not ls)
            row["both_syndrome_ok"] = bool(ls and fs)
            row["neither_syndrome_ok"] = bool(not ls and not fs)
        if _record_complete(layered) and _record_complete(flooding):
            row["iteration_diff"] = (int(flooding["iterations"])
                                     - int(layered["iterations"]))
            row["check_update_diff"] = (int(flooding["check_node_updates"])
                                        - int(layered["check_node_updates"]))
            row["edge_update_diff"] = (int(flooding["check_edge_updates"])
                                       - int(layered["check_edge_updates"]))
        if layered is not None and flooding is not None:
            l_wall = _as_float(layered["wall_s"])
            f_wall = _as_float(flooding["wall_s"])
            if l_wall is not None and f_wall is not None and l_wall > 0:
                row["wall_ratio"] = float(f_wall / l_wall)
        rows.append(row)
    return rows


def classify_stratum(flooding_only_exact: int, layered_only_exact: int,
                     both_exact: int, neither_exact: int) -> str:
    """Frozen first-match stratum classification (prereg §9)."""
    if flooding_only_exact >= 4 and layered_only_exact <= 1:
        return S_FLOODING
    if layered_only_exact >= 4 and flooding_only_exact <= 1:
        return S_LAYERED
    if (both_exact >= 12 and flooding_only_exact <= 1
            and layered_only_exact <= 1):
        return S_TIE_HIGH
    if (neither_exact >= 12 and flooding_only_exact <= 1
            and layered_only_exact <= 1):
        return S_TIE_LOW
    return S_MIXED


def _median(values):
    if not values:
        return ""
    return float(np.median(values))


def compute_strata(records, paired_rows) -> list:
    """Eight frozen stratum rows (2 f x 4 conditions) with first-match labels."""
    strata = []
    for f in F_VALUES:
        for condition in CONDITIONS:
            layer = CONDITION_LAYER[condition]
            stratum_records = [r for r in records
                               if float(r["f"]) == float(f)
                               and r["condition"] == condition]
            layered = [r for r in stratum_records
                       if r["schedule"] == "ROW_LAYERED"]
            flooding = [r for r in stratum_records
                        if r["schedule"] == "FLOODING"]
            paired = [row for row in paired_rows
                      if float(row["f"]) == float(f)
                      and row["condition"] == condition]
            paired_full = [row for row in paired
                           if row["layered_exact"] != ""
                           and row["flooding_exact"] != ""]

            def _count(items, field):
                return int(sum(1 for row in items if _as_bool(row[field])))

            fo = _count(paired_full, "flooding_only_exact")
            lo = _count(paired_full, "layered_only_exact")
            both = _count(paired_full, "both_exact")
            neither = _count(paired_full, "neither_exact")
            nonfinite = int(sum(1 for r in stratum_records
                                if (not _as_bool(r["finite"]))
                                and not str(r["status"]).startswith("crash:")))
            crashes = int(sum(1 for r in stratum_records
                              if str(r["status"]).startswith("crash:")))
            complete = (len(layered) == len(BLOCK_SEEDS)
                        and len(flooding) == len(BLOCK_SEEDS)
                        and crashes == 0 and nonfinite == 0)
            label = (classify_stratum(fo, lo, both, neither) if complete else "")

            def _median_field(items, field, cast):
                return _median([v for v in (cast(r[field]) for r in items)
                                if v is not None])

            strata.append({
                "stratum_idx": len(strata) + 1,
                "f": float(f), "layer": layer, "condition": condition,
                "blocks": int(len(paired_full)),
                "layered_exact_count": _count(layered, "exact"),
                "flooding_exact_count": _count(flooding, "exact"),
                "layered_only_exact_count": lo,
                "flooding_only_exact_count": fo,
                "both_exact_count": both,
                "neither_exact_count": neither,
                "layered_syndrome_ok_count": _count(layered, "syndrome_ok"),
                "flooding_syndrome_ok_count": _count(flooding, "syndrome_ok"),
                "layered_only_syndrome_ok_count": _count(paired_full, "layered_only_syndrome_ok"),
                "flooding_only_syndrome_ok_count": _count(paired_full, "flooding_only_syndrome_ok"),
                "both_syndrome_ok_count": _count(paired_full, "both_syndrome_ok"),
                "neither_syndrome_ok_count": _count(paired_full, "neither_syndrome_ok"),
                "nonfinite_count": nonfinite,
                "crash_count": crashes,
                "layered_median_iterations": _median_field(layered, "iterations", _as_int),
                "flooding_median_iterations": _median_field(flooding, "iterations", _as_int),
                "layered_median_check_updates": _median_field(layered, "check_node_updates", _as_int),
                "flooding_median_check_updates": _median_field(flooding, "check_node_updates", _as_int),
                "layered_median_edge_updates": _median_field(layered, "check_edge_updates", _as_int),
                "flooding_median_edge_updates": _median_field(flooding, "check_edge_updates", _as_int),
                "layered_median_wall_s": _median_field(layered, "wall_s", _as_float),
                "flooding_median_wall_s": _median_field(flooding, "wall_s", _as_float),
                "stratum_label": label,
            })
    return strata


def _exact_flags_identical(paired_rows) -> bool:
    """True only when every identity pair is present and both flags agree."""
    if len(paired_rows) < IDENTITY_COUNT:
        return False
    for row in paired_rows:
        if row["layered_exact"] == "" or row["flooding_exact"] == "":
            return False
        if _as_bool(row["layered_exact"]) != _as_bool(row["flooding_exact"]):
            return False
    return True


def classify_terminal(agg: dict) -> str:
    """Frozen T1..T10 first-applicable terminal selection (prereg §9)."""
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
    labels = list((agg.get("strata") or {}).values())
    flooding = sum(1 for v in labels if v == S_FLOODING)
    layered = sum(1 for v in labels if v == S_LAYERED)
    if flooding >= 2 and layered == 0:
        return T_FLOODING_ADV
    if layered >= 2 and flooding == 0:
        return T_LAYERED_ADV
    if flooding >= 1 and layered >= 1:
        return T_MIXED
    if agg.get("exact_flags_identical"):
        return T_NO_DIFF
    return T_INCONCLUSIVE


def terminal_from_records(records, paired_rows, stratum_rows) -> str:
    """Recompute the run terminal from scalar records + paired/stratum rows."""
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
    labels = {(float(row["f"]), row["condition"]): row.get("stratum_label", "")
              for row in stratum_rows}
    return classify_terminal({
        "pre_blocked": False,
        "watchdog_timeout": bool(watchdog),
        "crash_nonfinite": bool(crash),
        "resource_overrun": resource,
        "incomplete": len(records) < MAX_CALLS,
        "strata": labels,
        "exact_flags_identical": _exact_flags_identical(paired_rows),
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
    paired_rows = [_record_row(r, PAIRED_FIELDS) for r in paired]
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
    with open(out / "paired_schedule.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=PAIRED_FIELDS)
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
        fh.write("# D7-D flooding-vs-row-layered schedule discriminator\n\n")
        fh.write("terminal: %s\n" % (summary.get("terminal"),))
        fh.write("calls_completed: %s\n" % (summary.get("calls_completed"),))
        fh.write("stored_wall_s: %s\n" % (summary.get("stored_wall_s"),))
        for row in stratum_rows:
            fh.write("f=%s %s %s: %s\n" % (
                row["f"], row["condition"], row["layer"],
                row["stratum_label"]))
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
        if reader.fieldnames != PAIRED_FIELDS:
            raise ValueError("paired_schedule.csv schema mismatch: %r"
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
        "conditions": list(CONDITIONS),
        "block_seeds": [int(s) for s in BLOCK_SEEDS],
        "schedules": list(SCHEDULES),
        "max_calls": MAX_CALLS,
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
    missing = [layer for layer in LAYERS
               if not isinstance(manifest.get("row_degree_sums", {}).get(layer), dict)]
    if missing:
        problems.append("manifest row_degree_sums missing %r" % (missing,))


def _check_record_semantics(record, expected, problems, row_degree_sums):
    idx = record.get("call_idx", "?")
    prefix = "record %s: " % (idx,)
    for key in ("call_idx", "identity_idx", "schedule", "f", "seed",
                "condition", "layer", "rows", "n"):
        if key == "f":
            if _as_float(record.get(key)) != float(expected[key]):
                problems.append(prefix + "identity %s mismatch" % (key,))
                return
        elif str(record.get(key)) != str(expected[key]):
            problems.append(prefix + "identity %s mismatch" % (key,))
            return
    crash = str(record["status"]).startswith("crash:")
    if crash:
        if record["current_belief_label"] != "":
            problems.append(prefix + "crash record must carry an empty belief label")
        if _as_bool(record["finite"]):
            problems.append(prefix + "crash record must be nonfinite")
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
    rows = int(expected["rows"])
    node_updates = _as_int(record["check_node_updates"])
    if node_updates is None or node_updates != rows * iterations:
        problems.append(prefix + "check_node_updates must equal rows * iterations")
    edge_degree = row_degree_sums.get(expected["layer"], {}).get(str(rows))
    edge_updates = _as_int(record["check_edge_updates"])
    if edge_degree is None:
        problems.append(prefix + "row_degree_sums missing for %s/%s"
                        % (expected["layer"], rows))
    elif edge_updates is None or edge_updates != int(edge_degree) * iterations:
        problems.append(prefix + "check_edge_updates must equal row degrees * iterations")
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
    if key in ("schedule", "condition", "layer", "stratum_label"):
        return str(a) == str(b)
    if (key in ("f", "wall_ratio") or key.endswith("_wall_s")
            or key.endswith("_iterations") or key.endswith("_updates")):
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


def verify_root(out_root) -> dict:
    """Read-only verification of a seven-file root (no decoder, no Model-F).

    Recomputes schema, call identity/order/uniqueness, pair matching, paired
    outcomes, work arithmetic consistency, all eight stratum labels and the run
    terminal from the seven files alone.
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
        paired = _read_paired(out / "paired_schedule.csv")
        strata = _read_strata(out / "stratum_summary.csv")
    except Exception as exc:
        return {"ok": False, "problems": problems + ["csv: %r" % (exc,)],
                "records": 0}

    _check_manifest_contract(manifest, problems)
    row_degree_sums = manifest.get("row_degree_sums", {})
    if len(records) > MAX_CALLS:
        problems.append("records exceed the %d-call cap" % (MAX_CALLS,))
    matrix = frozen_call_matrix()
    seen = set()
    for position, record in enumerate(records):
        if position >= len(matrix):
            problems.append("record %d beyond the frozen call matrix"
                            % (position + 1,))
            break
        _check_record_semantics(record, matrix[position], problems,
                                row_degree_sums)
        call_idx = _as_int(record.get("call_idx"))
        if call_idx is not None:
            if call_idx in seen:
                problems.append("duplicate call_idx %s" % (call_idx,))
            seen.add(call_idx)
    if len(records) < MAX_CALLS:
        if summary.get("terminal") not in (T_WATCHDOG, T_CRASH, T_RESOURCE,
                                           T_INCOMPLETE):
            problems.append("truncated call matrix without a stop terminal")
    recomputed_paired = compute_paired_rows(records)
    if len(paired) != IDENTITY_COUNT:
        problems.append("paired_schedule.csv row count %d != %d"
                        % (len(paired), IDENTITY_COUNT))
    else:
        for actual, expected in zip(paired, recomputed_paired):
            if not _rows_equal_scalar(actual, expected, PAIRED_FIELDS):
                problems.append(
                    "paired row identity_idx=%s does not recompute"
                    % (actual.get("identity_idx"),))
    recomputed_strata = compute_strata(records, recomputed_paired)
    if len(strata) != 8:
        problems.append("stratum_summary.csv row count %d != 8" % (len(strata),))
    else:
        for actual, expected in zip(strata, recomputed_strata):
            if not _rows_equal_scalar(actual, expected, STRATUM_FIELDS):
                problems.append(
                    "stratum row %s (%s) does not recompute"
                    % (actual.get("stratum_idx"), actual.get("condition")))
    recomputed_terminal = terminal_from_records(
        records, recomputed_paired, recomputed_strata)
    if summary.get("terminal") != recomputed_terminal:
        problems.append("summary terminal %r != recomputed %r"
                        % (summary.get("terminal"), recomputed_terminal))
    if _as_int(summary.get("calls_completed")) != len(records):
        problems.append("summary calls_completed != record count")
    if _as_int(summary.get("calls_attempted")) != len(records):
        problems.append("summary calls_attempted != record count")
    expected_labels = [
        {"stratum_idx": int(row["stratum_idx"]), "f": float(row["f"]),
         "layer": row["layer"], "condition": row["condition"],
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


def _build_manifest(*, out_root, model_f_files, row_degree_sums,
                    authorization_consumed, command_str, start_utc, end_utc,
                    pid) -> dict:
    name = Path(out_root).name
    uuid = (name[len(OUT_ROOT_PREFIX):]
            if name.startswith(OUT_ROOT_PREFIX) else "")
    return {
        "change": "v72p2d7-gf32-schedule-discriminator",
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
        "conditions": list(CONDITIONS),
        "block_seeds": [int(s) for s in BLOCK_SEEDS],
        "graph_seeds": {"L1": L1_GRAPH_SEED, "L2": L2_GRAPH_SEED},
        "mothers": dict(_MOTHER_EXPR),
        "schedules": list(SCHEDULES),
        "decoder_ids": dict(_DECODER_IDS),
        "row_degree_sums": _jsonable(row_degree_sums),
        "max_iter": MAX_ITER,
        "damping_alpha": DAMPING_ALPHA,
        "decoder_floor": DECODER_FLOOR,
        "max_calls": MAX_CALLS,
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
    return {
        "terminal": terminal,
        "strata": [
            {"stratum_idx": int(row["stratum_idx"]), "f": float(row["f"]),
             "layer": row["layer"], "condition": row["condition"],
             "stratum_label": row["stratum_label"]}
            for row in strata],
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


def run_schedule_discriminator(*, out_root, model_f_root=None,
                               decoder_fns=None, model_f_loader=None,
                               joint=None, block_sampler=None, mothers=None,
                               state=None, state_reader=None, clock=None,
                               rss_probe=None, command_str="",
                               repo_root=None) -> dict:
    """One frozen sequential run (production bind only when ``decoder_fns`` is
    None and the authorization key is true)."""
    global _EXECUTION_CONSUMED
    if _EXECUTION_CONSUMED:
        raise NotAuthorizedError("D7-D authorization already consumed (no reuse)")
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
        decoder_fns = bind_schedule_decoders()
        _EXECUTION_CONSUMED = True

    start_utc = _utc_now()
    loop = execute_calls(context, decoder_fns, clock=clock, rss_probe=rss_probe)
    records = loop["records"]
    paired = compute_paired_rows(records)
    strata = compute_strata(records, paired)
    terminal = terminal_from_records(records, paired, strata)
    summary = _build_summary(loop, records, paired, strata, terminal)
    manifest = _build_manifest(
        out_root=out, model_f_files=context["model_f_files"],
        row_degree_sums=context["row_degree_sums"],
        authorization_consumed=production, command_str=command_str,
        start_utc=start_utc, end_utc=_utc_now(), pid=os.getpid())
    write_root(out, manifest, records, paired, strata, summary,
               command_str=command_str)
    return {"out_root": str(out), "terminal": terminal,
            "summary": summary, "records": len(records)}
