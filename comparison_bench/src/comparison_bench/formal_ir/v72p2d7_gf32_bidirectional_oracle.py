"""D7-C bidirectional cross-layer oracle harness (frozen R1+A1; no execution).

Single-layer counterfactual diagnostic at the accepted n=64 GF32 operating
point: for one frozen paired block and f, four conditions are decoded once
each by the historical certified cold row-layered FFT-QSPA decoder:

- ``L1_MARGINAL``    P(U1 | B)
- ``L1_ORACLE_U2``   P(U1 | B, U2_true)
- ``L2_MARGINAL``    P(U2 | B)
- ``L2_ORACLE_U1``   P(U2 | B, U1_true)

16 blocks x 2 f x 4 conditions = 128 calls in the frozen order. Oracle
conditions are counterfactual diagnostics only: they are not protocol
recovery, do not count oracle truth as disclosure and support no FER /
leakage / key-rate claim. This module performs no scientific decoder call
unless explicitly authorized by a future frozen execution packet; tests
inject fake joint tensors, blocks, mothers, decoder, clock and RSS.

D5 (``v72p2d5_gf32_rate_mother``) is import-only upstream and is never
modified. Prior math is direct from the accepted joint table; no
decoder-returned belief ever flows to another layer.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

try:  # normal package import (repo-relative local source on sys.path)
    from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5
except ModuleNotFoundError:  # file-layout fallback: same sibling file only
    import importlib.util as _ilu

    _D5_PATH = Path(__file__).resolve().parent / "v72p2d5_gf32_rate_mother.py"
    _D5_SPEC = _ilu.spec_from_file_location("v72p2d5_gf32_rate_mother", str(_D5_PATH))
    if _D5_SPEC is None or _D5_SPEC.loader is None:
        raise ImportError("cannot load sibling v72p2d5_gf32_rate_mother at %s" % (_D5_PATH,))
    d5 = _ilu.module_from_spec(_D5_SPEC)
    sys.modules["v72p2d5_gf32_rate_mother"] = d5
    _D5_SPEC.loader.exec_module(d5)

# --------------------------------------------------------------------------
# Frozen constants (D7-C prereg R1; must not change without an OpenSpec
# revision)
# --------------------------------------------------------------------------
Q = 32                       # GF(2^5), poly 37
N = 64                       # symbols per block
BOB_DIM = 1024               # Bob alphabet (2^10)
N_A = 1024                   # Alice alphabet (32*U1+U2)
MODEL_F_ROOT = "workspace/v72p2d5_model_f_input/20260907_r1"

F_VALUES = (1.0, 1.2)
L1_ROWS = {1.0: 49, 1.2: 59}
L2_ROWS = {1.0: 43, 1.2: 52}
ROWS = {"L1": L1_ROWS, "L2": L2_ROWS}
LAYERS = ("L1", "L2")
BLOCK_SEEDS = tuple(range(2026091300, 2026091316))
L1_GRAPH_SEED = 2026090501
L2_GRAPH_SEED = 2026090502
L1_K_MIN = 49
L2_K_MIN = 43

CONDITIONS = ("L1_MARGINAL", "L1_ORACLE_U2", "L2_MARGINAL", "L2_ORACLE_U1")
CONDITION_LAYER = {
    "L1_MARGINAL": "L1",
    "L1_ORACLE_U2": "L1",
    "L2_MARGINAL": "L2",
    "L2_ORACLE_U1": "L2",
}

LAMBDA_STAR = 137.3823795883264
DECODER_FLOOR = 1e-15
MAX_ITER = 90
DAMPING_ALPHA = 1.0

MAX_CALLS = 128
PER_CALL_WATCHDOG_S = 120.0
STORED_WALL_LIMIT_S = 1500.0
OUTER_WATCHDOG_S = 1800.0
OUTER_GRACE_S = 30.0
RSS_LIMIT_BYTES = 2 * 1024**3

D7C_AUTH_KEY = "d7c_execution_authorized"
STATE_REL_PATH = ("docs/research_cycles/"
                  "V72P2D7-GF32-BIDIRECTIONAL-ORACLE/cycle_state.yaml")

# Frozen run terminals T1..T11 (exact strings, exact priority).
TERMINALS = (
    "D7_C_PRE_EXECUTION_BLOCKED",
    "D7_C_WATCHDOG_TIMEOUT_VOID",
    "D7_C_NONFINITE_OR_CRASH_BLOCKED",
    "D7_C_RESOURCE_OVERRUN",
    "D7_C_INCOMPLETE_CALL_MATRIX",
    "D7_C_BIDIRECTIONAL_DEPENDENCE",
    "D7_C_L1_DEPENDS_ON_U2",
    "D7_C_L2_DEPENDS_ON_U1",
    "D7_C_MARGINAL_REGION_EXISTS",
    "D7_C_ORACLE_NO_USEFUL_RECOVERY",
    "D7_C_MIXED_DIAGNOSTIC",
)
T_PRE_EXEC, T_WATCHDOG, T_CRASH, T_RESOURCE, T_INCOMPLETE = TERMINALS[:5]
T_BIDIRECTIONAL, T_L1_DEPENDS, T_L2_DEPENDS = TERMINALS[5:8]
T_MARGINAL_REGION, T_NO_RECOVERY, T_MIXED = TERMINALS[8:]

# Frozen stratum labels.
S_STRONG = "STRONG_ORACLE_LIFT"
S_NO_RECOVERY = "NO_ORACLE_RECOVERY"
S_MARGINAL = "MARGINAL_ALREADY_RECOVERS"
S_AMBIGUOUS = "AMBIGUOUS_ORACLE_EFFECT"
STRATUM_LABELS = (S_STRONG, S_NO_RECOVERY, S_MARGINAL, S_AMBIGUOUS)

PRIOR_ONLY_CURRENT_BELIEF = "PRIOR_ONLY_CURRENT_BELIEF"
CHECK_UPDATED_CURRENT_BELIEF = "CHECK_UPDATED_CURRENT_BELIEF"
CURRENT_BELIEF_LABELS = (PRIOR_ONLY_CURRENT_BELIEF, CHECK_UPDATED_CURRENT_BELIEF)

SIX_FILES = ("manifest.json", "decoder_records.csv", "paired_summary.csv",
             "summary.json", "report.md", "command_log.txt")
RECORD_FIELDS = [
    "call_idx", "f", "seed", "condition", "layer", "rows", "n", "exact",
    "syndrome_ok", "iterations", "status", "finite", "symbol_errors",
    "unsatisfied_checks", "wall_s", "rss_bytes", "belief_max_prob",
    "belief_mean_true_p", "belief_mean_entropy", "beliefs_conditioned",
    "current_belief_label",
]
PAIRED_FIELDS = [
    "f", "layer", "marginal_condition", "oracle_condition",
    "marginal_exact_count", "oracle_exact_count", "oracle_only_count",
    "marginal_only_count", "both_exact_count", "neither_exact_count",
    "paired_syndrome_ok_count", "paired_syndrome_disagreement_count",
    "nonfinite_count", "crash_count", "marginal_median_iterations",
    "oracle_median_iterations", "marginal_max_iterations",
    "oracle_max_iterations", "marginal_median_wall_s", "oracle_median_wall_s",
    "marginal_max_wall_s", "oracle_max_wall_s", "stratum_label",
]

# Formal/dev roots that must never be an output target (name-based guard).
PROTECTED_ROOTS = (
    "workspace/v72p2d5_g0/20260905_r2",
    "workspace/v72p2d5_g0_recovery/20260906_r1",
    "workspace/v72p2d5_model_f_input/20260907_r1",
    "workspace/v72p2d5_p0_cost/20260906_r1",
    "workspace/v72p2d5_g1/20260907_r2",
    "workspace/v72p2d5_g1/20260906_r1",                       # VOID retained
    "workspace/v72p2d5_structure/20260905_r2",
    "workspace/d6_graph_mother_r1_923a25897087495ab4605870e561f3cc",  # VOID
    "workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b",
    "workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964",
)
OUT_ROOT_PREFIX = "d7_c_bidirectional_oracle_"

_ESTIMATOR_ID = ("v72p2d5_gf32_rate_mother."
                 "prepare_model_f_prior_candidate(counts_ab, p_b)")
_DECODER_ID = "v35.decode_row_layered_fftqspa via d5.bind_historical_decoder()"
_MOTHER_EXPR = {
    "L1": ("build_dv3_nested_support(64,64,49,2026090501)"
           "+assign_gf32_coefficients(sup,2026090501,None,64)"),
    "L2": ("build_dv3_nested_support(64,64,43,2026090502)"
           "+assign_gf32_coefficients(sup,2026090502,None,64)"),
}
_CALL_ORDER = ("for f in [1.0, 1.2]: for seed in 2026091300..2026091315: "
               "L1_MARGINAL, L1_ORACLE_U2, L2_MARGINAL, L2_ORACLE_U1")

_EXECUTION_CONSUMED = False  # single-use guard within one process


class NotAuthorizedError(PermissionError):
    """Raised when a run is entered without the D7-C authorization key."""


class PreflightBlocked(ValueError):
    """Pre-first-call refusal; carries the frozen T1 terminal."""

    terminal = T_PRE_EXEC


# --------------------------------------------------------------------------
# State / path contract
# --------------------------------------------------------------------------

def repo_root_path(repo_root=None) -> Path:
    """Repository root derived from ``__file__`` (no cwd assumption)."""
    return Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[4]


def cycle_state_path(repo_root=None) -> Path:
    return repo_root_path(repo_root) / STATE_REL_PATH


def read_cycle_state(path) -> dict:
    """Parse the flat ``key: value`` D7-C cycle-state file (no YAML dep)."""
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
        return bool(dict(state).get(D7C_AUTH_KEY, False))
    except Exception:
        return False


def _require_authorized(authorized: bool) -> None:
    if not authorized:
        raise NotAuthorizedError(
            "D7-C execution is not authorized; refusing before any work")


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

    Pure path check (no side effects). DI/qualification roots are task-owned
    temp roots outside the repository and are not subject to this CLI gate.
    """
    cand = Path(str(out_root))
    if not cand.is_absolute():
        cand = repo_root_path(repo_root) / cand
    cand = cand.resolve()
    ws = (repo_root_path(repo_root) / "workspace").resolve()
    if cand.parent != ws:
        raise ValueError(
            "refusing out-root outside workspace/: %s" % (cand,))
    if not cand.name.startswith(OUT_ROOT_PREFIX) or cand.name == OUT_ROOT_PREFIX:
        raise ValueError(
            "refusing out-root name %r (expected %s<uuid>)" % (cand.name, OUT_ROOT_PREFIX))
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
    ``bytes = ru_maxrss * 1024``. Absence and non-numeric values return None
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
# Frozen identities / mother / block / joint preparation
# --------------------------------------------------------------------------

def frozen_identities() -> list:
    """All 128 frozen call identities in the frozen order.

    Identity tuple: ``(f, seed, condition, layer, rows, n=64)``; call index is
    1-based in the same order.
    """
    identities = []
    for f in F_VALUES:
        for seed in BLOCK_SEEDS:
            for condition in CONDITIONS:
                layer = CONDITION_LAYER[condition]
                identities.append({
                    "call_idx": len(identities) + 1,
                    "f": float(f),
                    "seed": int(seed),
                    "condition": condition,
                    "layer": layer,
                    "rows": int(ROWS[layer][float(f)]),
                    "n": N,
                })
    return identities


def build_joint(p_f) -> np.ndarray:
    """``J[u1,u2,b] = P_F(32*u1+u2 | b)`` from the accepted ``(1024,1024)`` P_F."""
    pf = np.asarray(p_f, dtype=np.float64)
    if pf.shape != (N_A, BOB_DIM):
        raise PreflightBlocked(
            "accepted Model-F P_F must have shape (1024, 1024), got %r" % (pf.shape,))
    joint = pf.reshape(Q, Q, BOB_DIM)
    _validate_joint(joint)
    return joint


def _validate_joint(joint) -> None:
    j = np.asarray(joint, dtype=np.float64)
    if j.shape != (Q, Q, BOB_DIM):
        raise PreflightBlocked(
            "joint tensor must have shape (32,32,1024), got %r" % (j.shape,))
    if not np.all(np.isfinite(j)) or np.any(j < 0):
        raise PreflightBlocked("joint tensor must be finite and nonnegative")
    col = j.sum(axis=(0, 1))
    if not np.all(np.abs(col - 1.0) <= 1e-8):
        raise PreflightBlocked("every joint Bob column must sum to 1 within 1e-8")


def build_mother(layer: str) -> np.ndarray:
    """Frozen D5-native mother: support + GF32 coefficients, in memory only."""
    if layer == "L1":
        support = d5.build_dv3_nested_support(N, N, L1_K_MIN, L1_GRAPH_SEED)
        return d5.assign_gf32_coefficients(support, L1_GRAPH_SEED, None, N)
    if layer == "L2":
        support = d5.build_dv3_nested_support(N, N, L2_K_MIN, L2_GRAPH_SEED)
        return d5.assign_gf32_coefficients(support, L2_GRAPH_SEED, None, N)
    raise ValueError("unknown layer %r" % (layer,))


def _validate_mother(h, layer: str) -> np.ndarray:
    arr = np.asarray(h)
    if arr.shape != (N, N):
        raise PreflightBlocked(
            "mother %s must have shape (64,64), got %r" % (layer, arr.shape))
    if np.any(arr < 0) or np.any(arr >= Q):
        raise PreflightBlocked("mother %s values must lie in 0..31" % (layer,))
    return arr


def _normalize_block(block) -> dict:
    try:
        bob = np.asarray(block["bob"], dtype=np.int64).reshape(-1)
        u1 = np.asarray(block["u1"], dtype=np.int64).reshape(-1)
        u2 = np.asarray(block["u2"], dtype=np.int64).reshape(-1)
    except Exception as exc:
        raise PreflightBlocked("block must expose bob/u1/u2 arrays: %r" % (exc,))
    if not (bob.shape == u1.shape == u2.shape == (N,)):
        raise PreflightBlocked("block arrays must all have shape (64,)")
    if np.any(bob < 0) or np.any(bob >= BOB_DIM):
        raise PreflightBlocked("block bob values out of range")
    if np.any(u1 < 0) or np.any(u1 >= Q) or np.any(u2 < 0) or np.any(u2 >= Q):
        raise PreflightBlocked("block u1/u2 values out of range")
    return {"bob": bob, "u1": u1, "u2": u2,
            "alice": (u1 * Q + u2).astype(np.int64)}


def _default_model_f_loader(root):
    """Production Model-F load: D5 sibling loader chain; metadata only extras."""
    counts_ab, p_b = d5._load_model_f_input_or_blocked()
    files = []
    try:
        root_path = Path(str(root))
        files = sorted(
            (p.name, int(p.stat().st_size))
            for p in root_path.iterdir() if p.is_file())
    except Exception:
        files = []
    return {"counts_ab": counts_ab, "p_b": p_b, "files": files}


def _normalize_model_f(loaded):
    if isinstance(loaded, dict):
        missing = [k for k in ("counts_ab", "p_b") if k not in loaded]
        if missing:
            raise PreflightBlocked("model-F loader result missing %r" % (missing,))
        return loaded["counts_ab"], loaded["p_b"], list(loaded.get("files", []))
    try:
        counts_ab, p_b = loaded[0], loaded[1]
    except Exception as exc:
        raise PreflightBlocked("model-F loader result not usable: %r" % (exc,))
    files = list(loaded[2]) if len(loaded) > 2 else []
    return counts_ab, p_b, files


def prepare_inputs(*, joint=None, model_f_root=None, model_f_loader=None,
                   block_sampler=None, mothers=None, repo=None):
    """Frozen preparation order: Model-F -> estimator -> J -> mothers -> blocks.

    Returns the frozen context used by the call loop. All inputs are
    injectable for fake qualification; the production path (joint=None) loads
    only the accepted Model-F root through the D5 loader chain.
    """
    model_f_files = []
    p_b_out = None
    p_f = None
    if joint is None:
        if not model_f_root_matches(model_f_root, repo_root=repo):
            raise PreflightBlocked(
                "%s: --model-f-root must equal %s" % (T_PRE_EXEC, MODEL_F_ROOT))
        loader = model_f_loader or _default_model_f_loader
        resolved_root = (repo_root_path(repo) / MODEL_F_ROOT).resolve()
        counts_ab, p_b_cal, model_f_files = _normalize_model_f(loader(resolved_root))
        p_b_out, p_f = d5.prepare_model_f_prior_candidate(counts_ab, p_b_cal)
        joint = build_joint(p_f)
    else:
        _validate_joint(joint)
        joint = np.asarray(joint, dtype=np.float64)

    if mothers is None:
        mothers = {"L1": build_mother("L1"), "L2": build_mother("L2")}
    mothers = {layer: _validate_mother(mothers[layer], layer) for layer in LAYERS}

    sampler = block_sampler or d5.sample_matched_block
    blocks = {}
    for seed in BLOCK_SEEDS:
        blocks[int(seed)] = _normalize_block(sampler(p_b_out, p_f, N, int(seed)))

    identities = frozen_identities()
    if len(identities) != MAX_CALLS:
        raise AssertionError("frozen identity count must be %d" % (MAX_CALLS,))
    return {"joint": joint, "mothers": mothers, "blocks": blocks,
            "identities": identities, "model_f_files": model_f_files,
            "p_b": p_b_out, "p_f": p_f}


# --------------------------------------------------------------------------
# Prior math (frozen exact formulas; transpose only at the decoder boundary)
# --------------------------------------------------------------------------

def _normalized_oracle_slice(raw: np.ndarray) -> np.ndarray:
    """Normalize an oracle slice over its layer axis; zero mass -> uniform."""
    r = np.asarray(raw, dtype=np.float64)
    mass = r.sum(axis=0, keepdims=True)
    out = np.full_like(r, 1.0 / Q)
    if r.shape[1]:
        good = (mass[0] > 0)
        if bool(good.any()):
            out[:, good] = r[:, good] / mass[0, good][None, :]
    return out


def condition_prior_qn(joint, condition: str, block) -> np.ndarray:
    """One prior over the condition's layer axis, shape ``(32, n)``.

    ``L1_MARGINAL[:,i] = sum_u2 J[:,u2,b_i]``;
    ``L1_ORACLE_U2[:,i] = J[:,u2_true_i,b_i]`` normalized over u1;
    ``L2_MARGINAL[:,i] = sum_u1 J[u1,:,b_i]``;
    ``L2_ORACLE_U1[:,i] = J[u1_true_i,:,b_i]`` normalized over u2.
    Marginals keep possibly-zero entries (the boundary floors them once).
    """
    j = np.asarray(joint, dtype=np.float64)
    if j.ndim != 3 or j.shape[0] != Q or j.shape[1] != Q:
        raise ValueError("joint must have shape (32,32,B)")
    bob = np.asarray(block["bob"], dtype=np.int64).reshape(-1)
    if condition == "L1_MARGINAL":
        return j[:, :, bob].sum(axis=1)
    if condition == "L2_MARGINAL":
        return j[:, :, bob].sum(axis=0)
    if condition == "L1_ORACLE_U2":
        u2 = np.asarray(block["u2"], dtype=np.int64).reshape(-1)
        return _normalized_oracle_slice(j[:, u2, bob])
    if condition == "L2_ORACLE_U1":
        u1 = np.asarray(block["u1"], dtype=np.int64).reshape(-1)
        # Advanced indices around a slice land first: j[u1,:,bob] is (n, 32).
        return _normalized_oracle_slice(j[u1, :, bob].T)
    raise ValueError("unknown condition %r" % (condition,))


def decoder_prior(prior_qn) -> np.ndarray:
    """Transpose to ``(position, q)`` and apply the single frozen floor."""
    return d5._floor_renorm(np.asarray(prior_qn, dtype=np.float64).T, DECODER_FLOOR)


# --------------------------------------------------------------------------
# Decoder result parsing / per-call evaluation
# --------------------------------------------------------------------------

def _softmax_rows(log_beliefs) -> np.ndarray:
    b = np.asarray(log_beliefs, dtype=np.float64)
    m = b.max(axis=1, keepdims=True)
    e = np.exp(b - m)
    return e / e.sum(axis=1, keepdims=True)


def _parse_decoder_result(res):
    """Standardize dict/DecoderResult into (x_hat, syndrome_ok, iterations,
    beliefs, status). Missing required fields raise (isolated as a crash)."""
    if isinstance(res, dict):
        x_raw = res.get("x_hat")
        reported = bool(res.get("syndrome_ok", False))
        it_raw = res.get("iterations")
        beliefs = res.get("final_beliefs", res.get("beliefs"))
        status = str(res.get("status", "ok"))
    else:
        x_raw = getattr(res, "x_hat", None)
        reported = bool(getattr(res, "syndrome_ok", False))
        it_raw = getattr(res, "iterations", None)
        beliefs = getattr(res, "final_beliefs", None)
        status = str(getattr(res, "status", "ok"))
    if x_raw is None or it_raw is None:
        raise ValueError("decoder result missing x_hat/iterations")
    x_hat = np.asarray(x_raw, dtype=np.int64).reshape(-1)
    iterations = int(it_raw)
    if iterations < 0:
        raise ValueError("decoder iterations must be nonnegative")
    if beliefs is not None:
        bel = np.asarray(beliefs, dtype=np.float64)
        if bel.ndim == 2 and bel.shape[1] != Q and bel.shape[0] == Q:
            bel = bel.T
        beliefs = bel
    return x_hat, reported, iterations, beliefs, status


def _belief_diagnostics(beliefs, x_true: np.ndarray, finite: bool) -> dict:
    """Scalar-only diagnostics from softmax(final_beliefs) of the single call."""
    if beliefs is None or not finite:
        return {"belief_max_prob": "", "belief_mean_true_p": "",
                "belief_mean_entropy": ""}
    q = _softmax_rows(beliefs)
    true_p = q[np.arange(q.shape[0]), x_true]
    with np.errstate(divide="ignore", invalid="ignore"):
        ent = -(q * np.log2(np.maximum(q, 1e-300))).sum(axis=1)
    return {"belief_max_prob": float(np.max(q)),
            "belief_mean_true_p": float(np.mean(true_p)),
            "belief_mean_entropy": float(np.mean(ent))}


def evaluate_call(identity: dict, h_prefix: np.ndarray, block: dict,
                  syndrome: np.ndarray, result, wall_s: float, rss_bytes) -> dict:
    """One completed call -> scalar record with isolated exact/syndrome."""
    x_true = np.asarray(block["u1"] if identity["layer"] == "L1" else block["u2"],
                        dtype=np.int64)
    x_hat, reported, iterations, beliefs, status = _parse_decoder_result(result)
    if x_hat.shape != x_true.shape:
        raise ValueError("decoder x_hat shape %r != truth %r" % (x_hat.shape, x_true.shape))
    exact = bool(np.array_equal(x_hat, x_true))
    observed = d5._gf32_syndrome(h_prefix, x_hat)
    unsatisfied = int(np.count_nonzero(observed != np.asarray(syndrome, dtype=np.int64)))
    syndrome_ok = bool(reported and unsatisfied == 0)
    symbol_errors = int(np.count_nonzero(x_hat != x_true))
    finite_x = bool(np.all(np.isfinite(x_hat.astype(np.float64))))
    finite_bel = bool(beliefs is not None
                      and np.all(np.isfinite(np.asarray(beliefs, dtype=np.float64))))
    finite = bool(finite_x and finite_bel)
    diagnostics = _belief_diagnostics(beliefs, x_true, finite)
    conditioned = bool(iterations > 0)
    label = CHECK_UPDATED_CURRENT_BELIEF if conditioned else PRIOR_ONLY_CURRENT_BELIEF
    return {
        "call_idx": int(identity["call_idx"]),
        "f": float(identity["f"]),
        "seed": int(identity["seed"]),
        "condition": identity["condition"],
        "layer": identity["layer"],
        "rows": int(identity["rows"]),
        "n": int(identity["n"]),
        "exact": bool(exact),
        "syndrome_ok": bool(syndrome_ok),
        "iterations": int(iterations),
        "status": str(status),
        "finite": bool(finite),
        "symbol_errors": int(symbol_errors),
        "unsatisfied_checks": int(unsatisfied),
        "wall_s": float(wall_s),
        "rss_bytes": int(rss_bytes) if rss_bytes is not None else "",
        **diagnostics,
        "beliefs_conditioned": conditioned,
        "current_belief_label": label,
    }


def crash_record(identity: dict, exc: BaseException, wall_s: float,
                 rss_bytes) -> dict:
    """A decoder exception is an attempted-but-not-completed call."""
    rec = {
        "call_idx": int(identity["call_idx"]),
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
        "belief_max_prob": "",
        "belief_mean_true_p": "",
        "belief_mean_entropy": "",
        "beliefs_conditioned": "",
        "current_belief_label": "",
    }
    return rec


# --------------------------------------------------------------------------
# Sequential 128-call loop (no retry / resume / concurrency)
# --------------------------------------------------------------------------

def execute_calls(context: dict, decode_fn, *, clock=None, rss_probe=None) -> dict:
    """Run the frozen call loop once, sequentially, stopping on the first
    higher-priority budget/validity stop. No replacement, retry or resume."""
    clock = clock or time.perf_counter
    rss_probe = rss_probe or get_rss_bytes
    records = []
    stored_wall = 0.0
    stop = None
    for identity in context["identities"]:
        seed = int(identity["seed"])
        layer = identity["layer"]
        block = context["blocks"][seed]
        h_prefix = context["mothers"][layer][:int(identity["rows"])]
        x_true = np.asarray(block["u1"] if layer == "L1" else block["u2"],
                            dtype=np.int64)
        prior_qn = condition_prior_qn(context["joint"], identity["condition"], block)
        prior_pq = decoder_prior(prior_qn)
        syndrome = d5._gf32_syndrome(h_prefix, x_true)

        t0 = clock()
        result, exc = None, None
        try:
            result = decode_fn(h_prefix, prior_pq, syndrome)
        except Exception as caught:  # isolated as a crash, never retried
            exc = caught
        wall = max(0.0, float(clock() - t0))
        rss_bytes, rss_valid = _probe_rss_valid(rss_probe)

        if exc is not None:
            record = crash_record(identity, exc, wall, rss_bytes if rss_valid else None)
        else:
            try:
                record = evaluate_call(identity, h_prefix, block, syndrome,
                                       result, wall, rss_bytes if rss_valid else None)
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
# Paired summary / strata / terminals (shared by run and verifier)
# --------------------------------------------------------------------------

def marginal_oracle_conditions(layer: str):
    if layer == "L1":
        return "L1_MARGINAL", "L1_ORACLE_U2"
    if layer == "L2":
        return "L2_MARGINAL", "L2_ORACLE_U1"
    raise ValueError("unknown layer %r" % (layer,))


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


def classify_stratum(marginal_exact: int, oracle_exact: int, oracle_only: int,
                     marginal_only: int, crash_count: int,
                     nonfinite_count: int) -> str:
    """Frozen first-match stratum classification (prereg §10)."""
    if (oracle_only >= 4 and marginal_only <= 1 and oracle_exact >= 4
            and crash_count == 0 and nonfinite_count == 0):
        return S_STRONG
    if oracle_exact <= 1 and marginal_exact <= 1:
        return S_NO_RECOVERY
    if marginal_exact >= 12:
        return S_MARGINAL
    return S_AMBIGUOUS


def compute_paired_rows(records) -> list:
    """One frozen paired row per (f, layer) stratum (4 rows, frozen order)."""
    rows = []
    for f in F_VALUES:
        for layer in LAYERS:
            marginal_cond, oracle_cond = marginal_oracle_conditions(layer)
            marginal = [r for r in records
                        if float(r["f"]) == float(f) and r["condition"] == marginal_cond]
            oracle = [r for r in records
                      if float(r["f"]) == float(f) and r["condition"] == oracle_cond]
            m_by_seed = {int(r["seed"]): r for r in marginal}
            o_by_seed = {int(r["seed"]): r for r in oracle}
            pair_seeds = sorted(set(m_by_seed) & set(o_by_seed))

            marginal_exact = sum(1 for r in marginal if _as_bool(r["exact"]))
            oracle_exact = sum(1 for r in oracle if _as_bool(r["exact"]))
            oracle_only = sum(1 for s in pair_seeds
                              if _as_bool(o_by_seed[s]["exact"])
                              and not _as_bool(m_by_seed[s]["exact"]))
            marginal_only = sum(1 for s in pair_seeds
                                if _as_bool(m_by_seed[s]["exact"])
                                and not _as_bool(o_by_seed[s]["exact"]))
            both_exact = sum(1 for s in pair_seeds
                             if _as_bool(m_by_seed[s]["exact"])
                             and _as_bool(o_by_seed[s]["exact"]))
            neither_exact = len(pair_seeds) - oracle_only - marginal_only - both_exact
            paired_syndrome_ok = sum(1 for s in pair_seeds
                                     if _as_bool(m_by_seed[s]["syndrome_ok"])
                                     and _as_bool(o_by_seed[s]["syndrome_ok"]))
            paired_syndrome_disagreement = sum(
                1 for s in pair_seeds
                if _as_bool(m_by_seed[s]["syndrome_ok"])
                != _as_bool(o_by_seed[s]["syndrome_ok"]))
            all_calls = marginal + oracle
            crash_count = sum(1 for r in all_calls
                              if str(r["status"]).startswith("crash:"))
            nonfinite_count = sum(
                1 for r in all_calls
                if (not _as_bool(r["finite"]))
                and not str(r["status"]).startswith("crash:"))
            complete = (len(marginal) == len(BLOCK_SEEDS)
                        and len(oracle) == len(BLOCK_SEEDS)
                        and crash_count == 0 and nonfinite_count == 0)
            label = ""
            if complete:
                label = classify_stratum(
                    marginal_exact, oracle_exact, oracle_only, marginal_only,
                    crash_count, nonfinite_count)

            def _iters(items):
                return [v for v in (_as_int(r["iterations"]) for r in items)
                        if v is not None]

            def _walls(items):
                return [v for v in (_as_float(r["wall_s"]) for r in items)
                        if v is not None]

            def _extremes(items):
                vals = _iters(items)
                if not vals:
                    return "", ""
                return float(np.median(vals)), float(max(vals))

            m_med_it, m_max_it = _extremes(marginal)
            o_med_it, o_max_it = _extremes(oracle)
            m_walls, o_walls = _walls(marginal), _walls(oracle)
            rows.append({
                "f": float(f), "layer": layer,
                "marginal_condition": marginal_cond,
                "oracle_condition": oracle_cond,
                "marginal_exact_count": int(marginal_exact),
                "oracle_exact_count": int(oracle_exact),
                "oracle_only_count": int(oracle_only),
                "marginal_only_count": int(marginal_only),
                "both_exact_count": int(both_exact),
                "neither_exact_count": int(neither_exact),
                "paired_syndrome_ok_count": int(paired_syndrome_ok),
                "paired_syndrome_disagreement_count": int(paired_syndrome_disagreement),
                "nonfinite_count": int(nonfinite_count),
                "crash_count": int(crash_count),
                "marginal_median_iterations": m_med_it,
                "oracle_median_iterations": o_med_it,
                "marginal_max_iterations": m_max_it,
                "oracle_max_iterations": o_max_it,
                "marginal_median_wall_s": (float(np.median(m_walls)) if m_walls else ""),
                "oracle_median_wall_s": (float(np.median(o_walls)) if o_walls else ""),
                "marginal_max_wall_s": (float(max(m_walls)) if m_walls else ""),
                "oracle_max_wall_s": (float(max(o_walls)) if o_walls else ""),
                "stratum_label": label,
            })
    return rows


def classify_terminal(agg: dict) -> str:
    """Frozen T1..T11 first-applicable terminal selection (prereg §10)."""
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
    labels = agg.get("strata") or {}
    strong = {(f, layer): labels.get((f, layer)) == S_STRONG
              for f in F_VALUES for layer in LAYERS}
    if any(strong[(f, "L1")] and strong[(f, "L2")] for f in F_VALUES):
        return T_BIDIRECTIONAL
    strong_l1 = any(strong[(f, "L1")] for f in F_VALUES)
    strong_l2 = any(strong[(f, "L2")] for f in F_VALUES)
    if strong_l1 and not strong_l2:
        return T_L1_DEPENDS
    if strong_l2 and not strong_l1:
        return T_L2_DEPENDS
    if any(v == S_MARGINAL for v in labels.values()):
        return T_MARGINAL_REGION
    if labels and all(v == S_NO_RECOVERY for v in labels.values()):
        return T_NO_RECOVERY
    return T_MIXED


def terminal_from_records(records, paired_rows) -> str:
    """Recompute the run terminal from scalar records + paired rows only."""
    watchdog = any((_as_float(r["wall_s"]) or 0.0) > PER_CALL_WATCHDOG_S
                   for r in records)
    crash = any(str(r["status"]).startswith("crash:") or not _as_bool(r["finite"])
                for r in records)
    stored = sum(v for v in (_as_float(r["wall_s"]) for r in records) if v is not None)
    rss_over = False
    for r in records:
        value = _as_float(r["rss_bytes"])
        if value is not None and value >= RSS_LIMIT_BYTES:
            rss_over = True
        if value is None and not str(r["status"]).startswith("crash:"):
            rss_over = True
    resource = bool(stored > STORED_WALL_LIMIT_S or rss_over)
    labels = {(float(row["f"]), row["layer"]): row.get("stratum_label", "")
              for row in paired_rows}
    return classify_terminal({
        "pre_blocked": False,
        "watchdog_timeout": bool(watchdog),
        "crash_nonfinite": bool(crash),
        "resource_overrun": resource,
        "incomplete": len(records) < MAX_CALLS,
        "strata": labels,
    })


# --------------------------------------------------------------------------
# Six-file writer and verifier
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
    raise ValueError("non-scalar evidence value of type %s" % (type(value).__name__,))


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


def write_root(out_root, manifest, records, paired, summary, command_str=""):
    """Write exactly the six frozen scalar files into a fresh root."""
    rows = [_record_row(r, RECORD_FIELDS) for r in records]
    paired_rows = [_record_row(r, PAIRED_FIELDS) for r in paired]
    out = Path(out_root)
    if out.exists():
        if out.is_dir() and any(p.is_dir() for p in out.iterdir()):
            raise ValueError("no subdirectories allowed in evidence root")
        raise FileExistsError("refusing overwrite of existing root %s" % (out,))
    out.mkdir(parents=True, exist_ok=False)
    for name in SIX_FILES:
        if (out / name).exists():
            raise FileExistsError("refusing overwrite %s" % (name,))
    with open(out / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(_jsonable(manifest), fh, indent=2, sort_keys=True)
    with open(out / "decoder_records.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=RECORD_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    with open(out / "paired_summary.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=PAIRED_FIELDS)
        writer.writeheader()
        for row in paired_rows:
            writer.writerow(row)
    with open(out / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(_jsonable(summary), fh, indent=2, sort_keys=True)
    with open(out / "report.md", "w", encoding="utf-8") as fh:
        fh.write("# D7-C bidirectional oracle run\n\n")
        fh.write("terminal: %s\n" % (summary.get("terminal"),))
        fh.write("calls_completed: %s\n" % (summary.get("calls_completed"),))
        fh.write("stored_wall_s: %s\n" % (summary.get("stored_wall_s"),))
        for row in paired_rows:
            fh.write("f=%s %s: %s (marginal %s/%d, oracle %s/%d)\n" % (
                row["f"], row["layer"], row["stratum_label"],
                row["marginal_exact_count"], len(BLOCK_SEEDS),
                row["oracle_exact_count"], len(BLOCK_SEEDS)))
    with open(out / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write((command_str or "") + "\n")
        fh.write("terminal: %s\n" % (summary.get("terminal"),))
        fh.write("calls_completed: %s\n" % (summary.get("calls_completed"),))
        fh.write("stored_wall_s: %s\n" % (summary.get("stored_wall_s"),))
    return sorted(SIX_FILES)


def _read_records(path):
    with open(str(path), "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != RECORD_FIELDS:
            raise ValueError("decoder_records.csv schema mismatch: %r" % (reader.fieldnames,))
        return list(reader)


def _read_paired(path):
    with open(str(path), "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != PAIRED_FIELDS:
            raise ValueError("paired_summary.csv schema mismatch: %r" % (reader.fieldnames,))
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
        "max_calls": MAX_CALLS,
        "per_call_watchdog_s": PER_CALL_WATCHDOG_S,
        "stored_wall_limit_s": STORED_WALL_LIMIT_S,
        "outer_watchdog_s": OUTER_WATCHDOG_S,
        "outer_grace_s": OUTER_GRACE_S,
        "rss_limit_bytes": RSS_LIMIT_BYTES,
        "decoder_floor": DECODER_FLOOR,
        "max_iter": MAX_ITER,
        "damping_alpha": DAMPING_ALPHA,
        "six_files": list(SIX_FILES),
        "terminal_priority": list(TERMINALS),
        "call_order": _CALL_ORDER,
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
    if manifest.get("decoder") != _DECODER_ID:
        problems.append("manifest decoder mismatch")


def _check_record_semantics(record, expected, problems):
    idx = record.get("call_idx", "?")
    prefix = "record %s: " % (idx,)
    for key in ("call_idx", "f", "seed", "condition", "layer", "rows", "n"):
        if str(record.get(key)) != str(expected[key]) and not (
                key == "f" and _as_float(record.get(key)) == float(expected[key])):
            problems.append(prefix + "identity %s mismatch" % (key,))
            return
    if not (str(record["status"]).startswith("crash:")
            or (_as_int(record["iterations"]) is not None)):
        problems.append(prefix + "status/iterations not parseable")
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
    conditioned = _as_bool(record["beliefs_conditioned"])
    if conditioned != (iterations > 0):
        problems.append(prefix + "beliefs_conditioned must equal iterations > 0")
    label = record["current_belief_label"]
    expected_label = CHECK_UPDATED_CURRENT_BELIEF if iterations > 0 else PRIOR_ONLY_CURRENT_BELIEF
    if label != expected_label:
        problems.append(prefix + "current_belief_label %r must be %r" % (label, expected_label))
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
    for key, hi in (("belief_max_prob", 1.0), ("belief_mean_true_p", 1.0)):
        value = _as_float(record[key])
        if value is not None and not (0.0 <= value <= hi + 1e-12):
            problems.append(prefix + "%s out of range" % (key,))
    entropy = _as_float(record["belief_mean_entropy"])
    if entropy is not None and not (-1e-9 <= entropy <= math.log2(Q) + 1e-9):
        problems.append(prefix + "belief_mean_entropy out of range")


def _rows_equal_scalar(left, right) -> bool:
    for key in PAIRED_FIELDS:
        a, b = left.get(key), right.get(key)
        if key == "f":
            if _as_float(a) != _as_float(b):
                return False
        elif key in ("layer", "marginal_condition", "oracle_condition", "stratum_label"):
            if str(a) != str(b):
                return False
        else:
            fa, fb = _as_float(a), _as_float(b)
            if fa is None or fb is None:
                if str(a) != str(b):
                    return False
            elif abs(fa - fb) > 1e-9:
                return False
    return True


def verify_root(out_root) -> dict:
    """Read-only verification of a six-file root (no decoder, no Model-F).

    Recomputes schema, identity uniqueness/order, pair matching, counts and
    outcomes, stratum labels and the run terminal from the six files alone.
    """
    out = Path(out_root)
    problems = []
    if not out.is_dir():
        return {"ok": False, "problems": ["root missing: %s" % (out,)], "records": 0}
    entries = sorted(p.name for p in out.iterdir())
    if entries != sorted(SIX_FILES):
        problems.append("files %r != %r" % (entries, sorted(SIX_FILES)))
    if any(p.is_dir() for p in out.iterdir()):
        problems.append("subdirectories present")
    try:
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "problems": problems + ["json: %r" % (exc,)], "records": 0}
    records, paired = [], []
    try:
        records = _read_records(out / "decoder_records.csv")
        paired = _read_paired(out / "paired_summary.csv")
    except Exception as exc:
        return {"ok": False, "problems": problems + ["csv: %r" % (exc,)], "records": 0}

    _check_manifest_contract(manifest, problems)
    if len(records) > MAX_CALLS:
        problems.append("records exceed the %d-call cap" % (MAX_CALLS,))
    identities = frozen_identities()
    for position, record in enumerate(records):
        if position >= len(identities):
            problems.append("record %d beyond the frozen identity table" % (position + 1,))
            break
        _check_record_semantics(record, identities[position], problems)
    if len(records) < MAX_CALLS:
        terminal_now = summary.get("terminal")
        if terminal_now not in (T_WATCHDOG, T_CRASH, T_RESOURCE, T_INCOMPLETE):
            problems.append("truncated call matrix without a stop terminal")

    recomputed_paired = compute_paired_rows(records)
    if len(paired) != len(recomputed_paired):
        problems.append("paired_summary.csv row count %d != 4" % (len(paired),))
    else:
        for actual, expected in zip(paired, recomputed_paired):
            if not _rows_equal_scalar(actual, expected):
                problems.append(
                    "paired row f=%s %s does not recompute" % (actual.get("f"), actual.get("layer")))
    recomputed_terminal = terminal_from_records(records, recomputed_paired)
    if summary.get("terminal") != recomputed_terminal:
        problems.append("summary terminal %r != recomputed %r"
                        % (summary.get("terminal"), recomputed_terminal))
    if _as_int(summary.get("calls_completed")) != len(records):
        problems.append("summary calls_completed != record count")
    expected_labels = [{"f": float(row["f"]), "layer": row["layer"],
                        "stratum_label": row["stratum_label"]}
                       for row in recomputed_paired]
    if summary.get("strata") != expected_labels:
        problems.append("summary strata labels do not recompute")
    stored = sum(v for v in (_as_float(r["wall_s"]) for r in records) if v is not None)
    if _as_float(summary.get("stored_wall_s")) is None or abs(
            float(summary.get("stored_wall_s")) - stored) > 1e-9:
        problems.append("summary stored_wall_s does not recompute")
    for key in ("report.md", "command_log.txt"):
        try:
            if not (out / key).read_text(encoding="utf-8").strip():
                problems.append("%s is empty" % (key,))
        except Exception:
            problems.append("%s is unreadable" % (key,))
    return {"ok": not problems, "problems": problems, "records": len(records),
            "terminal": summary.get("terminal")}


# --------------------------------------------------------------------------
# Run + lazy production decoder bind
# --------------------------------------------------------------------------

def bind_historical_decoder():
    """Lazy production bind of the accepted D5 adapter (never on import)."""
    return d5.bind_historical_decoder()


def _build_manifest(*, out_root, model_f_files, authorization_consumed,
                    command_str, start_utc, pid) -> dict:
    name = Path(out_root).name
    uuid = name[len(OUT_ROOT_PREFIX):] if name.startswith(OUT_ROOT_PREFIX) else ""
    return {
        "change": "v72p2d7-gf32-bidirectional-oracle",
        "contract": "R1+A1",
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
        "decoder": _DECODER_ID,
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
        "six_files": list(SIX_FILES),
        "terminal_priority": list(TERMINALS),
        "command": command_str,
        "start_utc": start_utc,
        "pid": int(pid),
        "authorization_consumed": bool(authorization_consumed),
        "retries": 0,
        "reruns": 0,
        "resumes": 0,
    }


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def run_bidirectional_oracle(*, out_root, model_f_root=None, decode_fn=None,
                             model_f_loader=None, joint=None, block_sampler=None,
                             mothers=None, state=None, state_reader=None,
                             clock=None, rss_probe=None, command_str="",
                             repo_root=None) -> dict:
    """One frozen sequential run (production bind only when ``decode_fn`` is
    None and the authorization key is true)."""
    global _EXECUTION_CONSUMED
    if _EXECUTION_CONSUMED:
        raise NotAuthorizedError("D7-C authorization already consumed (no reuse)")
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

    production = decode_fn is None
    if production:
        decode_fn = bind_historical_decoder()
        _EXECUTION_CONSUMED = True

    start_utc = _utc_now()
    loop = execute_calls(context, decode_fn, clock=clock, rss_probe=rss_probe)
    records = loop["records"]
    paired = compute_paired_rows(records)
    terminal = terminal_from_records(records, paired)
    summary = {
        "terminal": terminal,
        "strata": [{"f": float(row["f"]), "layer": row["layer"],
                    "stratum_label": row["stratum_label"]} for row in paired],
        "calls_attempted": len(records),
        "calls_completed": len(records),
        "calls_remaining": int(MAX_CALLS - len(records)),
        "nonfinite_count": int(sum(1 for r in records
                                   if (not _as_bool(r["finite"]))
                                   and not str(r["status"]).startswith("crash:"))),
        "crash_count": int(sum(1 for r in records
                               if str(r["status"]).startswith("crash:"))),
        "watchdog_timeouts": int(sum(1 for r in records
                                     if (_as_float(r["wall_s"]) or 0.0) > PER_CALL_WATCHDOG_S)),
        "stored_wall_s": float(loop["stored_wall_s"]),
        "peak_rss_bytes": (max([v for v in (_as_int(r["rss_bytes"]) for r in records)
                                if v is not None], default="")),
        "stop_terminal": loop["stop"] or "",
        "retries": 0,
        "reruns": 0,
        "resumes": 0,
    }
    manifest = _build_manifest(
        out_root=out, model_f_files=context["model_f_files"],
        authorization_consumed=production, command_str=command_str,
        start_utc=start_utc, pid=os.getpid())
    write_root(out, manifest, records, paired, summary, command_str=command_str)
    return {"out_root": str(out), "terminal": terminal,
            "summary": summary, "records": len(records)}
