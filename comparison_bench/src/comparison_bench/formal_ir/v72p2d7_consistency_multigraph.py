"""D7 root-cause R1: same-input consistency harness, frozen multi-graph
exploratory runner, and bounded reference ladder.

Frozen by ``openspec/changes/formal-ir-d7-root-cause-and-route-reset``
(design §§2, 5–6) for packet
``.workbuddy/tasks/D7_ROOT_CAUSE_AND_ROUTE_RESET_R1_TASK_PACKET.md``.

This module performs no production decoder call, no CAL/VAL read, and no
phase execution by itself. The consistency harness is pure in-memory math with
an injected decoder. The multi-graph runner refuses unless explicitly
authorized and refuses an existing output root. The reference ladder is
dormant until X3; its tiny enumeration paths are the only exact scoring.

D7 modules are frozen by the packet allowlist: the D7 side below calls the
accepted D7-C/D7-E functions as-is, and the comparison reports the measured
equivalence rather than re-implementing them.
"""

from __future__ import annotations

import csv
import importlib
import importlib.util as _ilu
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent


def _load_sibling(name):
    """Package-first import (both repo namespace layouts), then file fallback.

    The ``comparison_bench.src.comparison_bench`` layout is preferred so the
    new module shares the exact instance the repository test suite imports.
    """
    for mod_name in ("comparison_bench.src.comparison_bench.formal_ir."
                     + name,
                     "comparison_bench.formal_ir." + name):
        try:
            return importlib.import_module(mod_name)
        except ModuleNotFoundError:
            continue
    spec = _ilu.spec_from_file_location(name, str(_HERE / (name + ".py")))
    if spec is None or spec.loader is None:
        raise ImportError("cannot load sibling module %s" % (name,))
    module = _ilu.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


d5 = _load_sibling("v72p2d5_gf32_rate_mother")
d7c = _load_sibling("v72p2d7_gf32_bidirectional_oracle")
d7e = _load_sibling("v72p2d7_gf32_cross_layer_discriminator")


class NotAuthorizedError(PermissionError):
    """Raised when a runner is entered without explicit authorization."""


class PreflightBlocked(ValueError):
    """Raised before any decoder contact when frozen inputs are invalid."""


# --------------------------------------------------------------------------
# Frozen constants (packet §7 C/D)
# --------------------------------------------------------------------------
Q = 32
N_BLOCK = 64
GRAPH_PAIRS = ((2026090501, 2026090502),
               (2026091401, 2026091402),
               (2026091501, 2026091502))
BLOCK_SEEDS = tuple(range(2026091300, 2026091316))
F_VALUES = (1.2, 1.0)
F_ROWS = {1.2: {"L1": 59, "L2": 52}, 1.0: {"L1": 49, "L2": 43}}
L1_K_MIN = 49
L2_K_MIN = 43
MAX_ITER = 90
DAMPING_ALPHA = 1.0

# (arm_id, layer, condition, role); "SOURCE" marginals and gated "TARGET"
# transfers in the frozen within-block order.
ARM_SPECS = (
    ("L1_MARGINAL", "L1", "L1_MARGINAL", "SOURCE"),
    ("L1_TO_L2_TRANSFER", "L2", "L2_TRANSFER", "TARGET"),
    ("L2_MARGINAL", "L2", "L2_MARGINAL", "SOURCE"),
    ("L2_TO_L1_TRANSFER", "L1", "L1_TRANSFER", "TARGET"),
)
TRANSFER_ARM_SOURCE = {"L1_TO_L2_TRANSFER": "L1_MARGINAL",
                       "L2_TO_L1_TRANSFER": "L2_MARGINAL"}
TRANSFER_ARM_DIRECTION = {"L1_TO_L2_TRANSFER": "L1_TO_L2",
                          "L2_TO_L1_TRANSFER": "L2_TO_L1"}
ARM_IDS = tuple(spec[0] for spec in ARM_SPECS)
MAX_CALLS = len(GRAPH_PAIRS) * len(F_VALUES) * len(BLOCK_SEEDS) * len(ARM_SPECS)

PER_CALL_WATCHDOG_S = 120.0
RSS_LIMIT_BYTES = 2 * 1024**3

MODEL_F_ROOT = d5.MODEL_F_INPUT_FORMAL_ROOT
ESTIMATOR_ID = "prepare_model_f_prior_candidate;concentration_backoff"
DECODER_ID = ("row_layered_fftqspa;GF32_poly37;cold;max_iter=90;"
              "damping_alpha=1.0;warm_beliefs=None;field=None")

SCOPE_TAG = "EXPLORATORY_SYNTHETIC_SINGLE_IMPLEMENTATION"
T_ENGINEERING = "MULTIGRAPH_ENGINEERING_BLOCKED"
T_INCONCLUSIVE = "INCONCLUSIVE"
T_SENSITIVITY = "GRAPH_SENSITIVITY_OBSERVED"
T_NO_SENSITIVITY = "NO_GRAPH_SENSITIVITY_OBSERVED_IN_BOUNDED_SAMPLE"
TERMINALS = (T_SENSITIVITY, T_NO_SENSITIVITY, T_INCONCLUSIVE, T_ENGINEERING)

EVIDENCE_FILES = ("manifest.json", "call_records.csv", "block_pairs.csv",
                  "graph_summary.csv", "across_graph_summary.json",
                  "report.md", "command_log.txt")
OUT_ROOT_PREFIX = "d7_r1_multigraph_"

CALL_RECORD_FIELDS = (
    "slot_idx", "graph_idx", "l1_graph_seed", "l2_graph_seed", "f", "seed",
    "arm", "role", "layer", "condition", "rows", "n", "invoked", "status",
    "exact", "syndrome_ok", "iterations", "finite", "symbol_errors",
    "unsatisfied_checks", "provenance", "transfer_eligible",
    "transfer_block_reason", "wall_s", "rss_bytes",
)
BLOCK_PAIR_FIELDS = (
    "graph_idx", "f", "seed", "coverage_ok", "forward_both_exact",
    "reverse_both_exact", "l1_marginal_exact", "l1_marginal_eligible",
    "l1_to_l2_invoked", "l1_to_l2_exact", "l2_marginal_exact",
    "l2_marginal_eligible", "l2_to_l1_invoked", "l2_to_l1_exact",
)
GRAPH_SUMMARY_FIELDS = (
    "graph_idx", "f", "blocks", "forward_both_count", "reverse_both_count",
    "forward_only", "reverse_only", "both", "neither",
    "l1_marginal_exact_count", "l2_marginal_exact_count",
    "l1_to_l2_invoked_count", "l1_to_l2_exact_count",
    "l2_to_l1_invoked_count", "l2_to_l1_exact_count",
    "provenance_blocked_count", "mcnemar_exact_p", "wilson_lo", "wilson_hi",
)


# --------------------------------------------------------------------------
# Same-input consistency harness (packet §7 B01–B04)
# --------------------------------------------------------------------------
COMPARISON_ATOL = 1e-12

# Frozen comparison modes: probability tensors computed by algebraically
# identical formulas in different operation order use atol; everything else
# must be bitwise equal.
_ATOL_ITEMS = ("l1_input_prior", "l2_transfer_prior")


def _result_get(result, key, default=None):
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)


def _counters(res, h, x_true, syndrome):
    x_hat, reported, iterations, beliefs, status = d7c._parse_decoder_result(res)
    x_true = np.asarray(x_true, dtype=np.int64).ravel()
    if x_hat.shape != x_true.shape:
        raise ValueError("decoder x_hat shape %r != truth %r"
                         % (x_hat.shape, x_true.shape))
    observed = d5._gf32_syndrome(h, x_hat)
    unsatisfied = int(np.count_nonzero(
        observed != np.asarray(syndrome, dtype=np.int64)))
    reports_finite = getattr(res, "final_beliefs", None) is not None or (
        isinstance(res, dict) and res.get("final_beliefs") is not None)
    beliefs_finite = reports_finite and bool(
        np.all(np.isfinite(np.asarray(_result_get(res, "final_beliefs"),
                                      dtype=np.float64))))
    return {
        "exact": bool(np.array_equal(x_hat, x_true)),
        "syndrome_ok": bool(reported and unsatisfied == 0),
        "unsatisfied_checks": int(unsatisfied),
        "iterations": int(iterations),
        "finite": bool(np.all(np.isfinite(x_hat.astype(np.float64)))
                       and beliefs_finite),
    }


def first_mismatch(tensor, left, right, *, atol=COMPARISON_ATOL):
    """Localize the first unequal value of two tensors or counter mappings.

    Returns ``None`` when equal, else a dict naming the tensor, the reason
    (``"shape"`` or ``"value"``), the flat index (or mapping key), both
    values, and the maximum absolute difference.
    """
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            if (key not in left or key not in right
                    or left[key] != right[key]):
                return {"tensor": tensor, "reason": "value", "key": key,
                        "left": left.get(key), "right": right.get(key),
                        "max_abs_diff": None}
        return None
    a = np.asarray(left)
    b = np.asarray(right)
    exact = tensor not in _ATOL_ITEMS
    if a.shape != b.shape:
        return {"tensor": tensor, "reason": "shape",
                "left_shape": list(a.shape), "right_shape": list(b.shape),
                "max_abs_diff": None}
    if exact:
        if np.array_equal(a, b):
            return None
    elif np.allclose(a, b, rtol=0.0, atol=float(atol)):
        return None
    diff = np.abs(a.astype(np.float64) - b.astype(np.float64))
    if diff.size == 0:
        return None
    idx = int(np.argmax(diff))
    return {"tensor": tensor, "reason": "value", "flat_index": idx,
            "left": float(a.ravel()[idx]), "right": float(b.ravel()[idx]),
            "max_abs_diff": float(diff.max())}


def _joint_from_pf(p_f):
    pf = np.asarray(p_f, dtype=np.float64)
    if pf.ndim != 2 or pf.shape[1] < 1:
        raise PreflightBlocked("p_f must be a 2-D (Alice, B) table")
    return pf.reshape(pf.shape[0] // Q, Q, pf.shape[1])


def compare_same_input(*, p_f, block, h1, h2, beliefs, decode_fn,
                       atol=COMPARISON_ATOL):
    """Compare the legacy-G1-compatible and D7 transfer paths on one input.

    Same in-memory graph (``h1``/``h2``), block, priors (``p_f``) and
    injected decoder (``decode_fn``, deterministic) for both paths. Returns a
    report with each compared tensor, its comparison mode, the maximum
    absolute difference, and the localized first mismatch (or ``None``).
    Performs no write and binds no decoder.
    """
    pf = np.asarray(p_f, dtype=np.float64)
    joint = _joint_from_pf(pf)
    bob = np.asarray(block["bob"], dtype=np.int64).ravel()
    u1 = np.asarray(block["u1"], dtype=np.int64).ravel()
    u2 = np.asarray(block["u2"], dtype=np.int64).ravel()
    h1 = np.asarray(h1, dtype=np.int64)
    h2 = np.asarray(h2, dtype=np.int64)
    bel = np.asarray(beliefs, dtype=np.float64)

    # Legacy-G1-compatible path (accepted D5 formulas through the canonical
    # source conversion and the canonical transfer implementation).
    p1 = d5.marginalize_f_to_p1(pf)
    p2 = d5.conditionalize_f_to_p2(pf)
    g1_prior1 = d5._floor_renorm(p1[:, bob].T, d5.DECODER_FLOOR)
    g1_syn1 = d5._gf32_syndrome(h1, u1)
    g1_res1 = decode_fn(h1, g1_prior1, g1_syn1, layer=None)
    g1_q = d5.canonical_source_q(bel)
    g1_prior2 = d5.canonical_transfer_l2_prior(p2, bob, g1_q)
    g1_syn2 = d5._gf32_syndrome(h2, u2)
    g1_res2 = decode_fn(h2, g1_prior2, g1_syn2, layer=None)

    # D7 certified chain path (accepted D7-C/D7-E functions as-is).
    d7_prior1 = d7c.decoder_prior(
        d7c.condition_prior_qn(joint, "L1_MARGINAL", block))
    d7_syn1 = d7c.d5._gf32_syndrome(h1, u1)
    d7_res1 = decode_fn(h1, d7_prior1, d7_syn1)
    d7_q = d7e.softmax_source_q(bel)
    d7_prior2 = d7e.build_transfer_prior(joint, "L1_TO_L2", bob, d7_q)
    d7_syn2 = d7c.d5._gf32_syndrome(h2, u2)
    d7_res2 = decode_fn(h2, d7_prior2, d7_syn2)

    g1_c1 = _counters(g1_res1, h1, u1, g1_syn1)
    d7_c1 = _counters(d7_res1, h1, u1, d7_syn1)
    g1_c2 = _counters(g1_res2, h2, u2, g1_syn2)
    d7_c2 = _counters(d7_res2, h2, u2, d7_syn2)
    items = {
        "l1_input_prior": (g1_prior1, d7_prior1),
        "q": (g1_q, d7_q),
        "l2_transfer_prior": (g1_prior2, d7_prior2),
        "l1_syndrome": (g1_syn1, d7_syn1),
        "l2_syndrome": (g1_syn2, d7_syn2),
        "l1_decoded_target": (g1_c1, d7_c1),
        "l2_decoded_target": (g1_c2, d7_c2),
        "l1_counters": (g1_c1, d7_c1),
        "l2_counters": (g1_c2, d7_c2),
    }
    report = {"ok": True, "atol": float(atol), "items": {},
              "first_mismatch": None}
    for name, (left, right) in items.items():
        mismatch = first_mismatch(name, left, right, atol=atol)
        max_diff = None
        if not isinstance(left, dict) and not isinstance(right, dict):
            a = np.asarray(left)
            b = np.asarray(right)
            if a.shape == b.shape and a.size:
                max_diff = float(np.max(np.abs(a.astype(np.float64)
                                              - b.astype(np.float64))))
        report["items"][name] = {
            "mode": "atol" if name in _ATOL_ITEMS else "exact",
            "equal": mismatch is None,
            "max_abs_diff": max_diff,
        }
        if mismatch is not None and report["first_mismatch"] is None:
            report["first_mismatch"] = mismatch
            report["ok"] = False
    return report


def g1_layered_capture(*, p_f, block, h1, h2, decode_results):
    """Run the accepted G1 ``_run_layered_block`` with a recording fake.

    ``decode_results`` is the exact sequence of returns the fake yields
    (L1 then L2). Returns the captured decoder inputs and the accepted
    per-layer counter record. No write, no production decoder.
    """
    pf = np.asarray(p_f, dtype=np.float64)
    p1 = d5.marginalize_f_to_p1(pf)
    p2 = d5.conditionalize_f_to_p2(pf)
    seq = list(decode_results)
    calls = []

    def fake(h, prior, syndrome, layer=None):
        if len(calls) >= len(seq):
            raise AssertionError("capture fake called more than %d times"
                                 % (len(seq),))
        calls.append({"prior": np.asarray(prior, dtype=np.float64).copy(),
                      "syndrome": np.asarray(syndrome, dtype=np.int64).copy(),
                      "shape": tuple(np.shape(h))})
        return seq[len(calls) - 1]

    out = d5._run_layered_block(fake, h1, h2, p1, p2, block, False)
    return {"calls": calls, "counters": out}


# --------------------------------------------------------------------------
# Multi-graph frozen matrix (packet §7 C01–C07)
# --------------------------------------------------------------------------
def frozen_slots():
    """The frozen 384-slot matrix in execution order."""
    slots = []
    idx = 0
    for graph_idx, (l1_seed, l2_seed) in enumerate(GRAPH_PAIRS):
        for f in F_VALUES:
            for seed in BLOCK_SEEDS:
                for arm, layer, condition, role in ARM_SPECS:
                    slots.append({
                        "slot_idx": idx,
                        "graph_idx": int(graph_idx),
                        "l1_graph_seed": int(l1_seed),
                        "l2_graph_seed": int(l2_seed),
                        "f": float(f),
                        "seed": int(seed),
                        "arm": arm,
                        "role": role,
                        "layer": layer,
                        "condition": condition,
                        "rows": int(F_ROWS[float(f)][layer]),
                        "n": int(N_BLOCK),
                    })
                    idx += 1
    return slots


def build_mother_for_pair(l1_seed, l2_seed):
    """Frozen D5-native mothers for one graph pair (same builders as D7-C)."""
    support1 = d5.build_dv3_nested_support(N_BLOCK, N_BLOCK, L1_K_MIN,
                                           int(l1_seed))
    support2 = d5.build_dv3_nested_support(N_BLOCK, N_BLOCK, L2_K_MIN,
                                           int(l2_seed))
    h1 = d5.assign_gf32_coefficients(support1, int(l1_seed), None, N_BLOCK)
    h2 = d5.assign_gf32_coefficients(support2, int(l2_seed), None, N_BLOCK)
    return {"L1": np.asarray(h1), "L2": np.asarray(h2)}


def _default_model_f_loader(root):
    counts_ab, p_b = d5._load_model_f_input_or_blocked()
    return {"counts_ab": counts_ab, "p_b": p_b, "files": []}


def _validate_joint(joint):
    j = np.asarray(joint, dtype=np.float64)
    if j.ndim != 3 or j.shape[0] != Q or j.shape[1] != Q or j.shape[2] < 1:
        raise PreflightBlocked(
            "joint tensor must have shape (32, 32, B>=1), got %r"
            % (j.shape,))
    if not np.all(np.isfinite(j)) or np.any(j < 0):
        raise PreflightBlocked("joint tensor must be finite and nonnegative")
    col = j.sum(axis=(0, 1))
    if not np.all(np.abs(col - 1.0) <= 1e-8):
        raise PreflightBlocked(
            "every joint Bob column must sum to 1 within 1e-8")
    return j


def _validate_mother(h, layer):
    arr = np.asarray(h)
    if arr.ndim != 2 or arr.shape[1] != N_BLOCK:
        raise PreflightBlocked(
            "mother %s must have shape (rows, 64), got %r" % (layer, arr.shape))
    if np.any(arr < 0) or np.any(arr >= Q):
        raise PreflightBlocked("mother %s values must lie in 0..31" % (layer,))
    return arr


def _validate_block(block):
    bob = np.asarray(block["bob"], dtype=np.int64).reshape(-1)
    u1 = np.asarray(block["u1"], dtype=np.int64).reshape(-1)
    u2 = np.asarray(block["u2"], dtype=np.int64).reshape(-1)
    if not (bob.shape == u1.shape == u2.shape == (N_BLOCK,)):
        raise PreflightBlocked("block arrays must all have shape (64,)")
    if np.any(u1 < 0) or np.any(u1 >= Q) or np.any(u2 < 0) or np.any(u2 >= Q):
        raise PreflightBlocked("block u1/u2 values must lie in 0..31")
    return {"bob": bob, "u1": u1, "u2": u2,
            "alice": (u1 * Q + u2).astype(np.int64)}


def prepare_multigraph_context(*, joint=None, blocks=None, mothers=None,
                               model_f_root=None, model_f_loader=None,
                               repo_root=None):
    """Resolve the frozen context; production loads only the accepted Model-F.

    Tests inject ``joint``, ``blocks`` and ``mothers`` directly; the
    production path (``joint is None``) loads the accepted Model-F root
    through the accepted D5 loader chain and derives blocks with the accepted
    D5 sampler. No decoder is bound or called here.
    """
    if joint is None:
        if not d7c.model_f_root_matches(model_f_root, repo_root=repo_root):
            raise PreflightBlocked(
                "model_f_root must equal %s" % (MODEL_F_ROOT,))
        loader = model_f_loader or _default_model_f_loader
        loaded = loader(repo_root_path(repo_root) / MODEL_F_ROOT)
        if isinstance(loaded, dict):
            counts = loaded.get("counts_ab")
            p_b_cal = loaded.get("p_b")
        else:
            counts, p_b_cal = loaded[0], loaded[1]
        p_b, p_f = d5.prepare_model_f_prior_candidate(counts, p_b_cal)
        joint = _joint_from_pf(p_f)
        if blocks is None:
            blocks = {int(seed): d5.sample_matched_block(
                p_b, p_f, N_BLOCK, int(seed)) for seed in BLOCK_SEEDS}
    joint = _validate_joint(joint)
    if blocks is None:
        raise PreflightBlocked(
            "blocks are required when joint is injected (tests) / Model-F is "
            "not loaded")
    blocks = {int(seed): _validate_block(blocks[int(seed)])
              for seed in BLOCK_SEEDS}
    if mothers is None:
        mothers = [build_mother_for_pair(*pair) for pair in GRAPH_PAIRS]
    if len(mothers) != len(GRAPH_PAIRS):
        raise PreflightBlocked("mothers must hold one entry per graph pair")
    mothers = [{layer: _validate_mother(mothers[g][layer], layer)
                for layer in ("L1", "L2")} for g in range(len(GRAPH_PAIRS))]
    return {"joint": joint, "blocks": blocks, "mothers": mothers,
            "slots": frozen_slots()}


def repo_root_path(repo_root=None):
    if repo_root is not None:
        return Path(repo_root)
    return d5._model_f_repo_root()


def _probe_rss(rss_probe):
    value = rss_probe()
    if value is None:
        return None
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


def _source_eligible(record):
    if record.get("crashed"):
        return False, "SOURCE_CRASH"
    if not bool(record.get("finite")):
        return False, "SOURCE_NONFINITE"
    if not bool(record.get("belief_shape_ok")):
        return False, "SOURCE_BELIEF_SHAPE"
    try:
        d7e.require_check_updated(record.get("provenance"))
    except Exception as exc:
        # The accepted refusal type is resolved lazily inside the D7 gate.
        if type(exc).__name__ == "UnconditionedBeliefProvenanceError":
            return False, d7e.BLOCK_PROVENANCE
        raise
    return True, "ELIGIBLE"


def _empty_record(slot, reason):
    record = {field: "" for field in CALL_RECORD_FIELDS}
    record.update({
        "slot_idx": int(slot["slot_idx"]),
        "graph_idx": int(slot["graph_idx"]),
        "l1_graph_seed": int(slot["l1_graph_seed"]),
        "l2_graph_seed": int(slot["l2_graph_seed"]),
        "f": float(slot["f"]),
        "seed": int(slot["seed"]),
        "arm": slot["arm"],
        "role": slot["role"],
        "layer": slot["layer"],
        "condition": slot["condition"],
        "rows": int(slot["rows"]),
        "n": int(slot["n"]),
        "invoked": False,
        "status": "blocked:%s" % (reason,),
        "exact": False,
        "syndrome_ok": False,
        "iterations": 0,
        "finite": True,
        "transfer_eligible": False,
    })
    return record


def _crash_record(slot, exc, wall_s, rss_bytes):
    record = _empty_record(slot, "crash:%s" % (type(exc).__name__,))
    record.update({"status": "crash:%s" % (type(exc).__name__,),
                   "finite": False, "wall_s": float(wall_s),
                   "rss_bytes": int(rss_bytes) if rss_bytes is not None else "",
                   "crashed": True})
    return record


def _evaluate_record(slot, h, prior, syndrome, x_true, result, wall_s,
                     rss_bytes):
    x_hat, reported, iterations, beliefs, status = d7c._parse_decoder_result(
        result)
    x_true = np.asarray(x_true, dtype=np.int64).ravel()
    if x_hat.shape != x_true.shape:
        raise ValueError("decoder x_hat shape %r != truth %r"
                         % (x_hat.shape, x_true.shape))
    observed = d5._gf32_syndrome(h, x_hat)
    unsatisfied = int(np.count_nonzero(
        observed != np.asarray(syndrome, dtype=np.int64)))
    exact = bool(np.array_equal(x_hat, x_true))
    syndrome_ok = bool(reported and unsatisfied == 0)
    finite_x = bool(np.all(np.isfinite(x_hat.astype(np.float64))))
    finite_bel = bool(beliefs is not None and np.all(
        np.isfinite(np.asarray(beliefs, dtype=np.float64))))
    provenance = _result_get(result, "belief_provenance")
    belief_shape_ok = bool(
        beliefs is not None
        and np.asarray(beliefs).shape == np.asarray(prior).shape)
    record = _empty_record(slot, "")
    record.update({
        "invoked": True,
        "status": str(status),
        "exact": exact,
        "syndrome_ok": syndrome_ok,
        "iterations": int(iterations),
        "finite": bool(finite_x and finite_bel),
        "symbol_errors": int(np.count_nonzero(x_hat != x_true)),
        "unsatisfied_checks": int(unsatisfied),
        "provenance": provenance if isinstance(provenance, str) else "",
        "wall_s": float(wall_s),
        "rss_bytes": int(rss_bytes) if rss_bytes is not None else "",
        "crashed": False,
        "belief_shape_ok": belief_shape_ok,
        "_beliefs": beliefs,
    })
    return record


def execute_multigraph(context, decoder_fns, *, clock=None, rss_probe=None,
                       wall_budget_s=None):
    """Run the frozen 384-slot matrix once, sequentially, with no retries.

    Source marginals always invoke their decoder. A transfer slot invokes the
    target decoder only when the same-block source return is non-crash,
    finite, shape-valid and exactly ``CHECK_UPDATED``; otherwise it is
    recorded as a blocked non-invocation. No replacement, retry, or resume.
    """
    clock = clock or time.perf_counter
    rss_probe = rss_probe or d5._rss_bytes
    records = []
    sources = {}
    stored_wall = 0.0
    calls = 0
    stop_reason = None
    for slot in context["slots"]:
        if wall_budget_s is not None and stored_wall > float(wall_budget_s):
            stop_reason = "WALL_BUDGET_EXHAUSTED"
            break
        graph_idx = int(slot["graph_idx"])
        seed = int(slot["seed"])
        block = context["blocks"][seed]
        layer = slot["layer"]
        h = context["mothers"][graph_idx][layer][:int(slot["rows"])]
        x_true = block["u1"] if layer == "L1" else block["u2"]
        syndrome = d5._gf32_syndrome(h, x_true)

        if slot["role"] == "TARGET":
            key = (graph_idx, float(slot["f"]), seed,
                   TRANSFER_ARM_SOURCE[slot["arm"]])
            src = sources.get(key)
            if src is None:
                records.append(_empty_record(slot, "SOURCE_MISSING"))
                continue
            eligible, reason = _source_eligible(src["record"])
            if not eligible:
                blocked = _empty_record(slot, reason)
                blocked["transfer_block_reason"] = reason
                records.append(blocked)
                continue
            q = d7e.softmax_source_q(src["beliefs"])
            prior = d7e.build_transfer_prior(
                context["joint"], TRANSFER_ARM_DIRECTION[slot["arm"]],
                block["bob"], q)
        else:
            prior_qn = d7c.condition_prior_qn(context["joint"],
                                              slot["condition"], block)
            prior = d7c.decoder_prior(prior_qn)

        t0 = clock()
        result = None
        exc = None
        try:
            result = decoder_fns[slot["role"]](h, prior, syndrome)
        except Exception as caught:  # isolated as a crash, never retried
            exc = caught
        wall = max(0.0, float(clock() - t0))
        rss = _probe_rss(rss_probe)
        calls += 1
        stored_wall += wall

        if exc is not None:
            record = _crash_record(slot, exc, wall, rss)
        else:
            try:
                record = _evaluate_record(slot, h, prior, syndrome, x_true,
                                          result, wall, rss)
            except Exception as caught:
                record = _crash_record(slot, caught, wall, rss)
        records.append(record)
        if slot["role"] == "SOURCE" and not record.get("crashed"):
            sources[(graph_idx, float(slot["f"]), seed, slot["arm"])] = {
                "record": record, "beliefs": record.get("_beliefs")}
        if rss is not None and rss >= RSS_LIMIT_BYTES:
            stop_reason = "RSS_CEILING_EXCEEDED"
            break
    return {"records": records, "calls": int(calls),
            "wall_seconds": float(stored_wall), "stop_reason": stop_reason,
            "slots_total": len(context["slots"])}


def build_block_pairs(records):
    """Join the four arm records of every (graph, f, seed) block."""
    by_key = {}
    for rec in records:
        key = (int(rec["graph_idx"]), float(rec["f"]), int(rec["seed"]))
        by_key.setdefault(key, {})[rec["arm"]] = rec
    rows = []
    for (graph_idx, f, seed), arms in sorted(
            by_key.items(), key=lambda kv: (kv[0][0], -kv[0][1], kv[0][2])):
        l1m = arms.get("L1_MARGINAL")
        l12 = arms.get("L1_TO_L2_TRANSFER")
        l2m = arms.get("L2_MARGINAL")
        l21 = arms.get("L2_TO_L1_TRANSFER")
        present = [l1m, l12, l2m, l21]

        def _inv(rec):
            return bool(rec is not None and rec.get("invoked")
                        and not rec.get("crashed"))

        def _exact(rec):
            return bool(_inv(rec) and rec.get("exact"))

        def _elig(rec):
            return int(bool(rec is not None and rec.get("invoked")
                            and rec.get("provenance") == "CHECK_UPDATED"))

        coverage_ok = all(
            r is not None and r.get("invoked") and not r.get("crashed")
            and bool(r.get("finite")) for r in present)
        forward = bool(_exact(l1m) and _exact(l12))
        reverse = bool(_exact(l2m) and _exact(l21))
        rows.append({
            "graph_idx": graph_idx, "f": f, "seed": seed,
            "coverage_ok": coverage_ok,
            "forward_both_exact": forward, "reverse_both_exact": reverse,
            "l1_marginal_exact": _exact(l1m), "l1_marginal_eligible": _elig(l1m),
            "l1_to_l2_invoked": _inv(l12), "l1_to_l2_exact": _exact(l12),
            "l2_marginal_exact": _exact(l2m), "l2_marginal_eligible": _elig(l2m),
            "l2_to_l1_invoked": _inv(l21), "l2_to_l1_exact": _exact(l21),
        })
    return rows


def mcnemar_exact_two_sided(forward_only, reverse_only):
    """Exact two-sided McNemar/binomial p-value (stdlib only)."""
    b = int(forward_only)
    c = int(reverse_only)
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / float(2 ** n)
    return float(min(1.0, 2.0 * tail))


def wilson_interval(k, n, z=1.959963984540054):
    """Wilson 95% interval; ``(None, None)`` when the denominator is zero."""
    n = int(n)
    if n <= 0:
        return (None, None)
    p = float(k) / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = (z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
            / denom)
    return (float(max(0.0, center - half)), float(min(1.0, center + half)))


def build_graph_summary(block_rows):
    """Descriptive per-(graph, f) summary; no pooled claim."""
    rows = []
    keys = sorted({(int(r["graph_idx"]), float(r["f"])) for r in block_rows},
                  key=lambda k: (k[0], -k[1]))
    for graph_idx, f in keys:
        subset = [r for r in block_rows
                  if r["graph_idx"] == graph_idx and r["f"] == f]
        forward = [r for r in subset if r["forward_both_exact"]]
        reverse = [r for r in subset if r["reverse_both_exact"]]
        forward_only = sum(1 for r in subset
                           if r["forward_both_exact"]
                           and not r["reverse_both_exact"])
        reverse_only = sum(1 for r in subset
                           if r["reverse_both_exact"]
                           and not r["forward_both_exact"])
        both = sum(1 for r in subset
                   if r["forward_both_exact"] and r["reverse_both_exact"])
        neither = len(subset) - forward_only - reverse_only - both
        p_value = mcnemar_exact_two_sided(forward_only, reverse_only)
        lo, hi = wilson_interval(forward_only, forward_only + reverse_only)
        rows.append({
            "graph_idx": graph_idx, "f": f, "blocks": len(subset),
            "forward_both_count": len(forward),
            "reverse_both_count": len(reverse),
            "forward_only": forward_only, "reverse_only": reverse_only,
            "both": both, "neither": neither,
            "l1_marginal_exact_count": sum(
                1 for r in subset if r["l1_marginal_exact"]),
            "l2_marginal_exact_count": sum(
                1 for r in subset if r["l2_marginal_exact"]),
            "l1_to_l2_invoked_count": sum(
                1 for r in subset if r["l1_to_l2_invoked"]),
            "l1_to_l2_exact_count": sum(
                1 for r in subset if r["l1_to_l2_exact"]),
            "l2_to_l1_invoked_count": sum(
                1 for r in subset if r["l2_to_l1_invoked"]),
            "l2_to_l1_exact_count": sum(
                1 for r in subset if r["l2_to_l1_exact"]),
            "provenance_blocked_count": sum(
                1 for r in subset
                if (r["l1_to_l2_invoked"] is False
                    or r["l2_to_l1_invoked"] is False)),
            "mcnemar_exact_p": p_value,
            "wilson_lo": lo, "wilson_hi": hi,
        })
    return rows


def classify_multigraph_terminal(graph_rows, block_rows, stop_reason=None):
    """Frozen terminal rule (design §5.4), primary f = 1.2 only."""
    if stop_reason:
        return T_ENGINEERING
    primary = [r for r in block_rows if float(r["f"]) == 1.2]
    if len(primary) != len(GRAPH_PAIRS) * len(BLOCK_SEEDS):
        return T_INCONCLUSIVE
    if not all(bool(r["coverage_ok"]) for r in primary):
        return T_INCONCLUSIVE
    vectors = []
    for graph_idx in range(len(GRAPH_PAIRS)):
        subset = [r for r in primary if int(r["graph_idx"]) == graph_idx]
        vectors.append((sum(1 for r in subset
                            if r["forward_both_exact"]
                            and not r["reverse_both_exact"]),
                        sum(1 for r in subset
                            if r["reverse_both_exact"]
                            and not r["forward_both_exact"]),
                        sum(1 for r in subset
                            if r["forward_both_exact"]
                            and r["reverse_both_exact"]),
                        sum(1 for r in subset
                            if not r["forward_both_exact"]
                            and not r["reverse_both_exact"])))
    if len(set(vectors)) > 1:
        return T_SENSITIVITY
    return T_NO_SENSITIVITY


def build_across_graph_summary(graph_rows, block_rows, exec_result):
    terminal = classify_multigraph_terminal(
        graph_rows, block_rows, stop_reason=exec_result.get("stop_reason"))
    primary = [r for r in graph_rows if float(r["f"]) == 1.2]
    sanity = [r for r in graph_rows if float(r["f"]) == 1.0]
    return {
        "cycle_id": "V72P2D7-ROOT-CAUSE-RESET",
        "scope": SCOPE_TAG,
        "terminal": terminal,
        "primary_f": 1.2,
        "graph_pairs": [list(pair) for pair in GRAPH_PAIRS],
        "block_seeds": [int(s) for s in BLOCK_SEEDS],
        "per_graph_primary": primary,
        "per_graph_sanity_f_1_0": sanity,
        "stop_reason": exec_result.get("stop_reason"),
        "decoder_calls": int(exec_result.get("calls", 0)),
        "stored_wall_seconds": float(exec_result.get("wall_seconds", 0.0)),
        "slots_total": int(exec_result.get("slots_total", 0)),
        "slots_recorded": len(exec_result.get("records", [])),
        "statistics_note": (
            "descriptive only: raw paired discordant counts per graph and f; "
            "exact two-sided McNemar p; Wilson 95% interval; no pass/fail "
            "from p-values; no pooled claim"),
    }


def validate_out_root(out_root, repo_root=None):
    """Fresh additive ``workspace`` evidence root; never an existing path."""
    path = Path(out_root)
    if path.exists():
        raise FileExistsError("refusing to overwrite evidence root: %s"
                              % (path,))
    if not path.name.startswith(OUT_ROOT_PREFIX):
        raise ValueError("evidence root name must start with %r, got %r"
                         % (OUT_ROOT_PREFIX, path.name))
    repo = Path(repo_root) if repo_root is not None else repo_root_path()
    workspace = (repo / "workspace").resolve()
    resolved = path.resolve()
    if workspace not in resolved.parents:
        raise ValueError("evidence root must live under %s" % (workspace,))
    return path


def write_multigraph_evidence(out_root, result, command_str=""):
    """Write the seven frozen scalar files into one fresh root."""
    root = Path(out_root)
    if root.exists():
        raise FileExistsError("refusing to overwrite evidence root: %s"
                              % (root,))
    root.mkdir(parents=True)
    manifest = result["manifest"]
    records = result["records"]
    block_rows = result["block_rows"]
    graph_rows = result["graph_rows"]
    across = result["across"]
    with open(root / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    with open(root / "call_records.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(CALL_RECORD_FIELDS),
                                extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)
    with open(root / "block_pairs.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(BLOCK_PAIR_FIELDS),
                                extrasaction="ignore")
        writer.writeheader()
        for row in block_rows:
            writer.writerow(row)
    with open(root / "graph_summary.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(GRAPH_SUMMARY_FIELDS),
                                extrasaction="ignore")
        writer.writeheader()
        for row in graph_rows:
            writer.writerow(row)
    with open(root / "across_graph_summary.json", "w",
              encoding="utf-8") as fh:
        json.dump(across, fh, indent=2, sort_keys=True)
    report = [
        "# D7 R1 multi-graph exploratory diagnostic",
        f"terminal: {across['terminal']}",
        f"scope: {across['scope']}",
        f"primary_f: {across['primary_f']}",
        f"decoder_calls: {across['decoder_calls']}",
        f"slots_total: {across['slots_total']}",
        f"stop_reason: {across['stop_reason']}",
        "## per-graph primary f=1.2",
    ]
    for row in across["per_graph_primary"]:
        report.append(
            "graph %d: forward_only=%d reverse_only=%d both=%d neither=%d "
            "mcnemar_p=%s" % (row["graph_idx"], row["forward_only"],
                              row["reverse_only"], row["both"],
                              row["neither"], row["mcnemar_exact_p"]))
    report.append("## sanity f=1.0")
    for row in across["per_graph_sanity_f_1_0"]:
        report.append(
            "graph %d: forward_only=%d reverse_only=%d both=%d neither=%d"
            % (row["graph_idx"], row["forward_only"], row["reverse_only"],
               row["both"], row["neither"]))
    report.append("")
    report.append(across["statistics_note"])
    with open(root / "report.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(report) + "\n")
    with open(root / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("command: %s\n" % (command_str,))
        fh.write("terminal: %s\n" % (across["terminal"],))
        fh.write("decoder_calls: %d\n" % (across["decoder_calls"],))
        fh.write("slots_total: %d\n" % (across["slots_total"],))
        fh.write("stop_reason: %s\n" % (across["stop_reason"],))
    return list(EVIDENCE_FILES)


def run_multigraph_diagnostic(*, out_root, authorized=False, joint=None,
                              blocks=None, mothers=None, decoder_fns=None,
                              model_f_root=None, model_f_loader=None,
                              repo_root=None, wall_budget_s=None,
                              clock=None, rss_probe=None, command_str=""):
    """Authorized multi-graph run; refuses before any work when unauthorized.

    Tests inject ``joint``/``blocks``/``mothers``/``decoder_fns`` and never
    reach ``bind_row_layered_decoders`` or the Model-F loader.
    """
    if not authorized:
        raise NotAuthorizedError(
            "multi-graph execution is not authorized; refusing before "
            "Model-F read, decoder bind, or root creation")
    validate_out_root(out_root, repo_root=repo_root)
    context = prepare_multigraph_context(
        joint=joint, blocks=blocks, mothers=mothers,
        model_f_root=model_f_root, model_f_loader=model_f_loader,
        repo_root=repo_root)
    if decoder_fns is None:
        decoder_fns = d7e.bind_row_layered_decoders()
    exec_result = execute_multigraph(context, decoder_fns, clock=clock,
                                     rss_probe=rss_probe,
                                     wall_budget_s=wall_budget_s)
    block_rows = build_block_pairs(exec_result["records"])
    graph_rows = build_graph_summary(block_rows)
    across = build_across_graph_summary(graph_rows, block_rows, exec_result)
    manifest = {
        "cycle_id": "V72P2D7-ROOT-CAUSE-RESET",
        "change_name": "formal-ir-d7-root-cause-and-route-reset",
        "phase": "X2_MULTIGRAPH_EXPLORATORY",
        "terminal": across["terminal"],
        "scope": SCOPE_TAG,
        "graph_pairs": [list(pair) for pair in GRAPH_PAIRS],
        "block_seeds": [int(s) for s in BLOCK_SEEDS],
        "f_values": [float(f) for f in F_VALUES],
        "rows": {str(f): dict(F_ROWS[f]) for f in F_VALUES},
        "arms": list(ARM_IDS),
        "max_calls": int(MAX_CALLS),
        "decoder_calls": int(exec_result["calls"]),
        "model_f_root": MODEL_F_ROOT,
        "model_f_root_checked": model_f_root is not None,
        "estimator": ESTIMATOR_ID,
        "decoder": DECODER_ID,
        "max_iter": int(MAX_ITER),
        "damping_alpha": float(DAMPING_ALPHA),
        "wall_budget_s": (None if wall_budget_s is None
                          else float(wall_budget_s)),
        "output_files": list(EVIDENCE_FILES),
        "no_overwrite": True,
    }
    result = {"manifest": manifest, "records": exec_result["records"],
              "block_rows": block_rows, "graph_rows": graph_rows,
              "across": across}
    write_multigraph_evidence(out_root, result, command_str=command_str)
    return {"terminal": across["terminal"], "out_root": str(out_root),
            "decoder_calls": int(exec_result["calls"]),
            "stop_reason": exec_result["stop_reason"],
            "across": across}


# --------------------------------------------------------------------------
# Bounded reference ladder (packet §7 D01–D05; dormant until X3)
# --------------------------------------------------------------------------
LADDER_ARM_IDS = ("ROW_LAYERED_90", "ROW_LAYERED_360", "FLOODING_90")
LADDER_CEILING_ITER = 360
EXACT_ENUM_MAX_STATES = 32768


def residual_syndrome_weight(h, x_hat, syndrome):
    """Number of unsatisfied check rows for one candidate."""
    observed = d5._gf32_syndrome(h, np.asarray(x_hat, dtype=np.int64).ravel())
    return int(np.count_nonzero(
        observed != np.asarray(syndrome, dtype=np.int64).ravel()))


def exact_posterior_scores(h, prior, syndrome, candidates, *,
                           max_states=EXACT_ENUM_MAX_STATES):
    """Exact posterior over syndrome-consistent candidates by enumeration.

    Posterior ``p(x) proportional to prior_prob(x)`` on
    ``{x : H x = syndrome}`` (hard check factors). Enumerates ``q**n`` states
    and refuses above ``max_states``. Rank is competition rank (1 + strictly
    greater posterior mass). Tiny-fixture only; never an ML claim.
    """
    h = np.asarray(h, dtype=np.int64)
    prior = np.asarray(prior, dtype=np.float64)
    if prior.ndim != 2:
        raise ValueError("prior must be 2-D (n, q)")
    n = int(prior.shape[0])
    q = int(prior.shape[1])
    if q ** n > int(max_states):
        raise ValueError("exact enumeration needs q**n <= %d, got %d**%d"
                         % (int(max_states), q, n))
    syndrome = np.asarray(syndrome, dtype=np.int64).ravel()
    valid = []
    for idx in range(q ** n):
        x = np.array(np.unravel_index(idx, (q,) * n), dtype=np.int64)
        if np.array_equal(d5._gf32_syndrome(h, x), syndrome):
            mass = float(np.prod([prior[i, x[i]] for i in range(n)]))
            valid.append((mass, x))
    total = float(sum(mass for mass, _ in valid))
    if total <= 0.0:
        raise ValueError("no positive-mass syndrome-consistent candidate")
    out = {}
    for cand in candidates:
        x = np.asarray(cand, dtype=np.int64).ravel()
        if x.shape != (n,):
            out[tuple(x.tolist())] = None
            continue
        mass = float(np.prod([prior[i, x[i]] for i in range(n)]))
        consistent = bool(np.array_equal(d5._gf32_syndrome(h, x), syndrome))
        rank = 1 + sum(1 for m, _ in valid if m > mass)
        out[tuple(x.tolist())] = {
            "posterior": float(mass / total) if consistent else 0.0,
            "prior_prob": mass,
            "syndrome_consistent": consistent,
            "rank": int(rank) if consistent else None,
        }
    return out


def bind_reference_ladder_decoders():
    """Lazy production bind (no calls) of the existing decoder entry points.

    Row-layered at 90 and at the frozen 360 ceiling, plus the existing
    flooding schedule at 90; all accept the same ``(H, prior, syndrome)``
    contract. No new decoder family is created.
    """
    v35 = d7e._load_v35()

    def row_layered_90(h, prior, syndrome):
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=MAX_ITER,
            damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)

    def row_layered_360(h, prior, syndrome):
        return v35.decode_row_layered_fftqspa(
            h, prior, syndrome, max_iter=LADDER_CEILING_ITER,
            damping_alpha=DAMPING_ALPHA, warm_beliefs=None, field=None)

    def flooding_90(h, prior, syndrome):
        return v35.decode_flooding_fftqspa(
            h, prior, syndrome, max_iter=MAX_ITER, field=None)

    return {"ROW_LAYERED_90": row_layered_90,
            "ROW_LAYERED_360": row_layered_360,
            "FLOODING_90": flooding_90}


def reference_ladder_arms():
    """Frozen ladder arm order (D02)."""
    return (
        {"arm_id": "ROW_LAYERED_90", "schedule": "ROW_LAYERED",
         "max_iter": MAX_ITER},
        {"arm_id": "ROW_LAYERED_360", "schedule": "ROW_LAYERED",
         "max_iter": LADDER_CEILING_ITER},
        {"arm_id": "FLOODING_90", "schedule": "FLOODING",
         "max_iter": MAX_ITER},
    )


def run_reference_ladder(*, h, prior, syndrome, x_true, decoder_fns,
                         arm_ids=LADDER_ARM_IDS, f=None, seed=None,
                         clock=None, rss_probe=None, authorized=False):
    """Run the three-arm ladder on one already-failing frozen f=1.2 call.

    D05 scope is enforced when ``f``/``seed`` are supplied: only the frozen
    f=1.2 primary and the frozen block seeds are accepted, and no seed is
    replaced. Reporting only; no adaptive selection.
    """
    if not authorized:
        raise NotAuthorizedError(
            "reference ladder is not authorized; X3 grant required")
    if f is not None and float(f) != 1.2:
        raise ValueError("reference ladder applies only to frozen f=1.2")
    if seed is not None and int(seed) not in BLOCK_SEEDS:
        raise ValueError("reference ladder applies only to frozen block seeds")
    if decoder_fns is None:
        decoder_fns = bind_reference_ladder_decoders()
    clock = clock or time.perf_counter
    rss_probe = rss_probe or d5._rss_bytes
    prior = np.asarray(prior, dtype=np.float64)
    syndrome = np.asarray(syndrome)
    arm_max_iter = {spec["arm_id"]: int(spec["max_iter"])
                    for spec in reference_ladder_arms()}
    x_true = np.asarray(x_true, dtype=np.int64).ravel()
    arms = []
    baseline = None
    for arm_id in arm_ids:
        t0 = clock()
        result = decoder_fns[arm_id](h, prior, syndrome)
        wall = max(0.0, float(clock() - t0))
        rss = _probe_rss(rss_probe)
        x_hat, reported, iterations, beliefs, status = d7c._parse_decoder_result(
            result)
        x_hat = np.asarray(x_hat, dtype=np.int64).ravel()
        residual = residual_syndrome_weight(h, x_hat, syndrome)
        syndrome_ok = bool(reported and residual == 0)
        finite = bool(np.all(np.isfinite(x_hat.astype(np.float64)))
                      and beliefs is not None
                      and np.all(np.isfinite(np.asarray(beliefs,
                                                        dtype=np.float64))))
        scores = None
        computable = False
        try:
            scores = exact_posterior_scores(
                h, prior, syndrome, [x_true, x_hat])
            computable = True
        except ValueError:
            scores = None
        current_exact = bool(np.array_equal(x_hat, x_true))
        if baseline is None:
            baseline = (syndrome_ok, current_exact)
        arms.append({
            "arm_id": arm_id,
            "max_iter": int(arm_max_iter.get(arm_id, MAX_ITER)),
            "exact": current_exact,
            "syndrome_ok": syndrome_ok,
            "residual_syndrome_weight": residual,
            "iterations": int(iterations),
            "finite": finite,
            "status": str(status),
            "posterior_scores": scores,
            "posterior_score_computable": computable,
            "changed_vs_current": bool(
                current_exact != baseline[1] or syndrome_ok != baseline[0]),
            "wall_s": wall,
            "rss_bytes": int(rss) if rss is not None else None,
            "scope_label": "STRONG_REFERENCE_DIAGNOSTIC",
        })
    return {"arms": arms, "ladder_ceiling_iter": LADDER_CEILING_ITER}


# --------------------------------------------------------------------------
# X1 historical provenance probe record (packet §7 P01–P02)
# --------------------------------------------------------------------------
X1_RESOLVED_HISTORICAL_IDENTITY = "historical_g0_decoder"
X1_PROBE_FAILED_LABEL = "X1_PROVENANCE_PROBE_FAILED"


def historical_provenance_probe_record(report):
    """One JSON-ready X1 probe record (exactly one decoder call, no writes).

    ``report`` is the return of ``d5.probe_historical_decoder_provenance``.
    Exit 0 is allowed only for exact ``CHECK_UPDATED`` + finite + shape-valid
    beliefs and ``iterations >= 1`` (packet P02).
    """
    iterations = report.get("iterations")
    iterations_ok = (isinstance(iterations, int)
                     and not isinstance(iterations, bool)
                     and iterations >= 1)
    ok = bool(report.get("accepted_check_updated")
              and report.get("beliefs_finite")
              and report.get("belief_shape_ok")
              and iterations_ok)
    return {
        "mode": "historical_provenance_probe",
        "resolved_decoder_identity": (
            X1_RESOLVED_HISTORICAL_IDENTITY
            if report.get("resolved_is_historical") else "injected_or_unresolved"),
        "resolved_is_historical": bool(report.get("resolved_is_historical")),
        "provenance": report.get("provenance"),
        "accepted_check_updated": bool(report.get("accepted_check_updated")),
        "iterations": iterations,
        "belief_shape_ok": bool(report.get("belief_shape_ok")),
        "beliefs_finite": bool(report.get("beliefs_finite")),
        "decoder_calls": 1,
        "writes": 0,
        "ok": ok,
    }


# --------------------------------------------------------------------------
# X3 failed-record reference ladder (packet §7 P03–P06; dormant until X3)
# --------------------------------------------------------------------------
X3_X2_ROOT = "workspace/d7_r1_multigraph_20260913_r1"
X3_OUT_ROOT = "workspace/d7_r1_reference_ladder_20260913_r1"
X3_OUT_ROOT_PREFIX = "d7_r1_reference_ladder_"
X3_MAX_SELECTED = 192
X3_LADDER_CALL_CEILING = 576          # 192 selected records x 3 ladder arms
X3_RECONSTRUCTION_CALL_CEILING = 96   # <=96 unique source slots (3 x 16 x 2)
X3_EVIDENCE_FILES = ("manifest.json", "selected_records.csv",
                     "ladder_records.csv", "paired_summary.csv",
                     "summary.json", "report.md", "command_log.txt")
X3_TERMINAL_NOT_APPLICABLE = "X3_NOT_APPLICABLE_NO_FAILED_CALLS"
X3_TERMINAL_MISMATCH = "X3_BASELINE_REPLAY_MISMATCH_BLOCKED"
X3_TERMINAL_COMPLETED = "X3_REFERENCE_LADDER_COMPLETED"
X3_TERMINAL_ENGINEERING = "X3_ENGINEERING_BLOCKED"
X3_CLAIM_LABEL = "STRONG_REFERENCE_DIAGNOSTIC"
X3_REPLAY_FIELDS = ("exact", "syndrome_ok", "iterations", "finite",
                    "symbol_errors", "unsatisfied_checks", "provenance",
                    "status")
X3_SELECTED_FIELDS = (
    "record_idx", "slot_idx", "graph_idx", "l1_graph_seed", "l2_graph_seed",
    "f", "seed", "arm", "role", "layer", "condition", "rows", "n",
    "prior_kind", "stored_status", "stored_exact", "stored_syndrome_ok",
    "stored_iterations", "stored_finite", "stored_provenance",
)
X3_LADDER_FIELDS = (
    "row_kind", "record_idx", "record_slot_idx", "graph_idx", "f", "seed",
    "arm", "role", "layer", "condition", "rows", "prior_kind", "ladder_arm",
    "input_source", "baseline_replay_match", "exact", "syndrome_ok",
    "residual_syndrome_weight", "iterations", "finite", "status",
    "symbol_errors", "unsatisfied_checks", "provenance", "changed_vs_current",
    "wall_s", "rss_bytes", "mismatch_field", "mismatch_stored",
    "mismatch_replay",
)
X3_PAIRED_FIELDS = (
    "record_idx", "slot_idx", "graph_idx", "f", "seed", "arm", "role",
    "layer", "condition", "rows", "prior_kind", "baseline_exact",
    "baseline_syndrome_ok", "arm_360_exact", "arm_360_syndrome_ok",
    "arm_360_changed", "flooding_exact", "flooding_syndrome_ok",
    "flooding_changed", "baseline_replay_match", "reconstruction_calls",
    "ladder_calls",
)


def _csv_flag(value):
    return str(value).strip().lower() == "true"


def is_failed_f12_record(rec):
    """Selector predicate (P03): f=1.2, executed, non-crash, finite, not exact."""
    try:
        f_value = float(rec.get("f"))
    except (TypeError, ValueError):
        return False
    if abs(f_value - 1.2) > 1e-9:
        return False
    if not _csv_flag(rec.get("invoked")) or _csv_flag(rec.get("crashed")):
        return False
    if str(rec.get("status", "")).startswith("crash:"):
        return False
    if not _csv_flag(rec.get("finite")):
        return False
    return not _csv_flag(rec.get("exact"))


def select_failed_x2_records(records):
    """Every failed f=1.2 call record in slot order; no dedup, no replacement."""
    selected = [rec for rec in records if is_failed_f12_record(rec)]
    selected.sort(key=lambda rec: int(rec["slot_idx"]))
    return selected


def _prior_kind(rec):
    return "TRANSFER" if rec.get("role") == "TARGET" else "MARGINAL"


def _source_arm_id(rec):
    if rec.get("role") == "SOURCE":
        return rec["arm"]
    return TRANSFER_ARM_SOURCE[rec["arm"]]


def _source_slot_key(rec):
    return (int(rec["graph_idx"]), float(rec["f"]), int(rec["seed"]),
            _source_arm_id(rec))


def plan_x3_calls(selected):
    """Frozen call plan recorded before any decoder is bound (P04).

    Three ladder arms per selected record; a selected TARGET record needs its
    source marginal beliefs reconstructed.  When the source slot is itself a
    selected SOURCE record its ladder baseline already supplies those beliefs
    (processed first in slot order); otherwise the deterministic source replay
    is one reconstruction call, cached per source slot.  Reconstruction calls
    are therefore bounded by the 96 f=1.2 source slots.
    """
    ladder = 3 * len(selected)
    selected_source_keys = {_source_slot_key(rec) for rec in selected
                            if rec.get("role") == "SOURCE"}
    reconstruction_keys = set()
    for rec in selected:
        if rec.get("role") == "TARGET":
            key = _source_slot_key(rec)
            if key not in selected_source_keys:
                reconstruction_keys.add(key)
    return {
        "selected_records": len(selected),
        "ladder_calls": int(ladder),
        "reconstruction_calls": int(len(reconstruction_keys)),
        "total_calls": int(ladder + len(reconstruction_keys)),
        "max_selected_records": int(X3_MAX_SELECTED),
        "ladder_call_ceiling": int(X3_LADDER_CALL_CEILING),
        "reconstruction_call_ceiling": int(X3_RECONSTRUCTION_CALL_CEILING),
    }


def _guard_x3_plan(plan):
    if plan["selected_records"] > X3_MAX_SELECTED:
        raise PreflightBlocked(
            "selected %d records exceeds the frozen %d"
            % (plan["selected_records"], X3_MAX_SELECTED))
    if plan["ladder_calls"] > X3_LADDER_CALL_CEILING:
        raise PreflightBlocked(
            "ladder plan %d exceeds the frozen %d"
            % (plan["ladder_calls"], X3_LADDER_CALL_CEILING))
    if plan["reconstruction_calls"] > X3_RECONSTRUCTION_CALL_CEILING:
        raise PreflightBlocked(
            "reconstruction plan %d exceeds the frozen %d"
            % (plan["reconstruction_calls"], X3_RECONSTRUCTION_CALL_CEILING))


def validate_x3_x2_root(x2_root, repo_root=None):
    """The X2 root must be exactly the frozen (repo-anchored) literal."""
    expected = (repo_root_path(repo_root) / X3_X2_ROOT).resolve()
    actual = Path(str(x2_root))
    if not actual.is_absolute():
        actual = repo_root_path(repo_root) / actual
    actual = actual.resolve()
    if actual != expected:
        raise ValueError("x2-root must be exactly %s, got %s"
                         % (expected, actual))
    if not actual.is_dir():
        raise FileNotFoundError("x2-root does not exist: %s" % (actual,))
    return actual


def validate_x3_out_root(out_root, repo_root=None):
    """Fresh additive reference-ladder evidence root; never an existing path."""
    repo = repo_root_path(repo_root)
    path = Path(str(out_root))
    if not path.is_absolute():
        path = repo / path
    if path.exists():
        raise FileExistsError("refusing to overwrite evidence root: %s"
                              % (path,))
    if not path.name.startswith(X3_OUT_ROOT_PREFIX):
        raise ValueError("evidence root name must start with %r, got %r"
                         % (X3_OUT_ROOT_PREFIX, path.name))
    workspace = (repo / "workspace").resolve()
    if workspace not in path.resolve().parents:
        raise ValueError("evidence root must live under %s" % (workspace,))
    return path


def read_x2_root(x2_root):
    """Read the immutable X2 root's manifest and call records."""
    root = Path(str(x2_root))
    with open(root / "manifest.json", "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    with open(root / "call_records.csv", "r", encoding="utf-8",
              newline="") as fh:
        records = list(csv.DictReader(fh))
    return {"manifest": manifest, "records": records, "root": str(root)}


def validate_x2_manifest(manifest):
    """Refuse a root that was not produced by the frozen X2 contract."""
    if manifest.get("cycle_id") != "V72P2D7-ROOT-CAUSE-RESET":
        raise PreflightBlocked(
            "x2 manifest cycle_id mismatch: %r"
            % (manifest.get("cycle_id"),))
    pairs = [tuple(int(v) for v in pair)
             for pair in manifest.get("graph_pairs", [])]
    if pairs != [tuple(pair) for pair in GRAPH_PAIRS]:
        raise PreflightBlocked("x2 manifest graph_pairs mismatch: %r"
                               % (pairs,))
    if [int(v) for v in manifest.get("block_seeds", [])] != list(BLOCK_SEEDS):
        raise PreflightBlocked("x2 manifest block_seeds mismatch")
    if [float(v) for v in manifest.get("f_values", [])] != list(F_VALUES):
        raise PreflightBlocked("x2 manifest f_values mismatch")
    if list(manifest.get("arms", [])) != list(ARM_IDS):
        raise PreflightBlocked("x2 manifest arms mismatch")
    if manifest.get("model_f_root") != MODEL_F_ROOT:
        raise PreflightBlocked("x2 manifest model_f_root mismatch: %r"
                               % (manifest.get("model_f_root"),))
    return manifest


def _slot_for_row(rec):
    return {
        "slot_idx": int(rec["slot_idx"]),
        "graph_idx": int(rec["graph_idx"]),
        "l1_graph_seed": int(rec["l1_graph_seed"]),
        "l2_graph_seed": int(rec["l2_graph_seed"]),
        "f": float(rec["f"]),
        "seed": int(rec["seed"]),
        "arm": rec["arm"],
        "role": rec["role"],
        "layer": rec["layer"],
        "condition": rec["condition"],
        "rows": int(rec["rows"]),
        "n": int(rec["n"]),
    }


def x3_reconstruct_marginal_call(context, rec):
    """H/prior/syndrome/truth of one marginal (SOURCE) X2 call (P05)."""
    slot = _slot_for_row(rec)
    block = context["blocks"][slot["seed"]]
    h = context["mothers"][slot["graph_idx"]][slot["layer"]][:slot["rows"]]
    x_true = block["u1"] if slot["layer"] == "L1" else block["u2"]
    syndrome = d5._gf32_syndrome(h, x_true)
    prior_qn = d7c.condition_prior_qn(context["joint"], slot["condition"], block)
    return {"slot": slot, "block": block, "h": h,
            "prior": d7c.decoder_prior(prior_qn), "syndrome": syndrome,
            "x_true": x_true}


def x3_reconstruct_transfer_call(context, rec, source_beliefs):
    """H/prior/syndrome/truth of one TARGET call from replayed source beliefs."""
    slot = _slot_for_row(rec)
    block = context["blocks"][slot["seed"]]
    h = context["mothers"][slot["graph_idx"]][slot["layer"]][:slot["rows"]]
    x_true = block["u1"] if slot["layer"] == "L1" else block["u2"]
    syndrome = d5._gf32_syndrome(h, x_true)
    q = d7e.softmax_source_q(source_beliefs)
    prior = d7e.build_transfer_prior(
        context["joint"], TRANSFER_ARM_DIRECTION[slot["arm"]], block["bob"], q)
    return {"slot": slot, "block": block, "h": h, "prior": prior,
            "syndrome": syndrome, "x_true": x_true}


def _replay_mismatch(replay, stored):
    for field in X3_REPLAY_FIELDS:
        left = str(replay.get(field, ""))
        right = str(stored.get(field, ""))
        if left != right:
            return {"field": field, "replay": left, "stored": right}
    return None


def _selected_row(record_idx, rec):
    row = {"record_idx": int(record_idx), "prior_kind": _prior_kind(rec)}
    for field in X3_SELECTED_FIELDS:
        if field in row:
            continue
        if field in rec:
            row[field] = rec[field]
    row["stored_status"] = rec.get("status", "")
    row["stored_exact"] = rec.get("exact", "")
    row["stored_syndrome_ok"] = rec.get("syndrome_ok", "")
    row["stored_iterations"] = rec.get("iterations", "")
    row["stored_finite"] = rec.get("finite", "")
    row["stored_provenance"] = rec.get("provenance", "")
    return row


def _ladder_row(*, row_kind, record_idx, rec, evaluated, call, ladder_arm,
                input_source, baseline_match, changed_vs_current,
                mismatch=None):
    return {
        "row_kind": row_kind,
        "record_idx": int(record_idx),
        "record_slot_idx": int(rec["slot_idx"]),
        "graph_idx": int(rec["graph_idx"]),
        "f": rec.get("f"),
        "seed": int(rec["seed"]),
        "arm": rec.get("arm"),
        "role": rec.get("role"),
        "layer": rec.get("layer"),
        "condition": rec.get("condition"),
        "rows": rec.get("rows"),
        "prior_kind": _prior_kind(rec),
        "ladder_arm": ladder_arm,
        "input_source": input_source,
        "baseline_replay_match": baseline_match,
        "exact": evaluated.get("exact"),
        "syndrome_ok": evaluated.get("syndrome_ok"),
        "residual_syndrome_weight": evaluated.get("unsatisfied_checks"),
        "iterations": evaluated.get("iterations"),
        "finite": evaluated.get("finite"),
        "status": evaluated.get("status"),
        "symbol_errors": evaluated.get("symbol_errors"),
        "unsatisfied_checks": evaluated.get("unsatisfied_checks"),
        "provenance": evaluated.get("provenance"),
        "changed_vs_current": changed_vs_current,
        "wall_s": call.get("wall_s"),
        "rss_bytes": ("" if call.get("rss_bytes") is None
                      else int(call["rss_bytes"])),
        "mismatch_field": "" if mismatch is None else mismatch["field"],
        "mismatch_stored": "" if mismatch is None else mismatch["stored"],
        "mismatch_replay": "" if mismatch is None else mismatch["replay"],
    }


def _write_csv(path, fields, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fields),
                                extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_reference_ladder_selected(*, x2_root, out_root, authorized=False,
                                  repo_root=None, context=None,
                                  model_f_loader=None, decoder_fns=None,
                                  clock=None, rss_probe=None,
                                  wall_budget_s=None, command_str=""):
    """X3 failed-record reference ladder over the immutable X2 root.

    Refuses before reading X2, binding a decoder, or creating a root when
    ``authorized`` is false.  With a selection, the actual selected records
    are written before any decoder is bound; the baseline ``ROW_LAYERED_90``
    replay of every selected record must match the stored X2 record or the
    run stops at ``X3_BASELINE_REPLAY_MISMATCH_BLOCKED``.
    """
    if not authorized:
        raise NotAuthorizedError(
            "reference ladder is not authorized; X3 grant required")
    x2_path = validate_x3_x2_root(x2_root, repo_root=repo_root)
    out_path = validate_x3_out_root(out_root, repo_root=repo_root)
    x2 = read_x2_root(x2_path)
    validate_x2_manifest(x2["manifest"])
    selected = select_failed_x2_records(x2["records"])
    plan = plan_x3_calls(selected)
    _guard_x3_plan(plan)

    out_path.mkdir(parents=True)
    _write_csv(out_path / "selected_records.csv", X3_SELECTED_FIELDS,
               [_selected_row(idx, rec) for idx, rec in enumerate(selected)])

    clock = clock or time.perf_counter
    rss_probe = rss_probe or d5._rss_bytes
    ladder_rows = []
    paired_rows = []
    stop = None
    stored_wall = 0.0
    peak_rss = None

    def _call(decoder, h, prior, syndrome):
        nonlocal stored_wall, peak_rss
        t0 = clock()
        try:
            result = decoder(h, prior, syndrome)
            crash = None
        except Exception as exc:  # isolated as a crash, never retried
            result, crash = None, exc
        wall = max(0.0, float(clock() - t0))
        rss = _probe_rss(rss_probe)
        stored_wall += wall
        if rss is not None:
            peak_rss = rss if peak_rss is None else max(peak_rss, rss)
        return {"result": result, "crash": crash, "wall_s": wall,
                "rss_bytes": rss}

    def _evaluate(rec, inp, call):
        return _evaluate_record(_slot_for_row(rec), inp["h"], inp["prior"],
                                inp["syndrome"], inp["x_true"], call["result"],
                                call["wall_s"], call["rss_bytes"])

    if selected:
        if decoder_fns is None:
            decoder_fns = bind_reference_ladder_decoders()
        if context is None:
            context = prepare_multigraph_context(
                model_f_root=x2["manifest"]["model_f_root"],
                model_f_loader=model_f_loader, repo_root=repo_root)
        source_index = {_source_slot_key(rec): rec for rec in x2["records"]
                        if rec.get("role") == "SOURCE"}
        source_cache = {}
        terminal = X3_TERMINAL_COMPLETED
        for idx, rec in enumerate(selected):
            if (peak_rss is not None and peak_rss >= RSS_LIMIT_BYTES):
                terminal, stop = (X3_TERMINAL_ENGINEERING,
                                  {"reason": "RSS_CEILING_EXCEEDED"})
                break
            if wall_budget_s is not None and stored_wall > float(wall_budget_s):
                terminal, stop = (X3_TERMINAL_ENGINEERING,
                                  {"reason": "WALL_BUDGET_EXHAUSTED"})
                break
            reconstruct_calls = 0
            try:
                if rec.get("role") == "TARGET":
                    key = _source_slot_key(rec)
                    cached = source_cache.get(key)
                    if cached is None:
                        src_rec = source_index.get(key)
                        if src_rec is None:
                            raise PreflightBlocked(
                                "stored source record missing for %r" % (key,))
                        src_inp = x3_reconstruct_marginal_call(context, src_rec)
                        call = _call(decoder_fns["ROW_LAYERED_90"],
                                     src_inp["h"], src_inp["prior"],
                                     src_inp["syndrome"])
                        reconstruct_calls += 1
                        if call["crash"] is not None:
                            raise RuntimeError(
                                "source reconstruction call crashed: %r"
                                % (call["crash"],))
                        src_eval = _evaluate(src_rec, src_inp, call)
                        mismatch = _replay_mismatch(src_eval, src_rec)
                        eligible, reason = _source_eligible(src_eval)
                        ladder_rows.append(_ladder_row(
                            row_kind="SOURCE_RECONSTRUCTION", record_idx=idx,
                            rec=src_rec, evaluated=src_eval, call=call,
                            ladder_arm="ROW_LAYERED_90",
                            input_source="source_marginal_replay",
                            baseline_match=(mismatch is None),
                            changed_vs_current=False, mismatch=mismatch))
                        if mismatch is not None:
                            terminal, stop = (X3_TERMINAL_MISMATCH,
                                              dict(mismatch, where="source_reconstruction",
                                                   source_slot_idx=src_rec["slot_idx"]))
                            break
                        if not eligible:
                            terminal, stop = (
                                X3_TERMINAL_MISMATCH,
                                {"where": "source_reconstruction",
                                 "reason": reason,
                                 "source_slot_idx": src_rec["slot_idx"]})
                            break
                        cached = {"record": src_eval,
                                  "beliefs": src_eval.get("_beliefs")}
                        source_cache[key] = cached
                    inp = x3_reconstruct_transfer_call(context, rec,
                                                       cached["beliefs"])
                else:
                    inp = x3_reconstruct_marginal_call(context, rec)
            except Exception as exc:
                terminal, stop = (X3_TERMINAL_MISMATCH,
                                  {"where": "reconstruction",
                                   "record_idx": int(idx),
                                   "error": repr(exc)})
                break
            arm_results = {}
            baseline_eval = None
            ladder_calls_used = 0
            for arm_id in LADDER_ARM_IDS:
                if (clock is not None and wall_budget_s is not None
                        and stored_wall > float(wall_budget_s)):
                    terminal, stop = (X3_TERMINAL_ENGINEERING,
                                      {"reason": "WALL_BUDGET_EXHAUSTED"})
                    break
                call = _call(decoder_fns[arm_id], inp["h"], inp["prior"],
                             inp["syndrome"])
                ladder_calls_used += 1
                if call["crash"] is not None:
                    terminal, stop = (X3_TERMINAL_MISMATCH,
                                      {"where": "ladder_call_crash",
                                       "record_idx": int(idx),
                                       "arm": arm_id,
                                       "error": repr(call["crash"])})
                    break
                try:
                    evaluated = _evaluate(rec, inp, call)
                except Exception as exc:
                    terminal, stop = (X3_TERMINAL_MISMATCH,
                                      {"where": "ladder_evaluation",
                                       "record_idx": int(idx),
                                       "arm": arm_id, "error": repr(exc)})
                    break
                arm_results[arm_id] = evaluated
                if arm_id == "ROW_LAYERED_90":
                    baseline_eval = evaluated
                    mismatch = _replay_mismatch(evaluated, rec)
                    ladder_rows.append(_ladder_row(
                        row_kind="LADDER", record_idx=idx, rec=rec,
                        evaluated=evaluated, call=call, ladder_arm=arm_id,
                        input_source="record_input",
                        baseline_match=(mismatch is None),
                        changed_vs_current=False, mismatch=mismatch))
                    if mismatch is not None:
                        terminal, stop = (X3_TERMINAL_MISMATCH,
                                          dict(mismatch, where="record_baseline",
                                               record_idx=int(idx)))
                        break
                    if rec.get("role") == "SOURCE":
                        source_cache[_source_slot_key(rec)] = {
                            "record": evaluated,
                            "beliefs": evaluated.get("_beliefs")}
                else:
                    changed = (
                        _csv_flag(rec.get("exact")) != bool(evaluated["exact"])
                        or _csv_flag(rec.get("syndrome_ok"))
                        != bool(evaluated["syndrome_ok"]))
                    ladder_rows.append(_ladder_row(
                        row_kind="LADDER", record_idx=idx, rec=rec,
                        evaluated=evaluated, call=call, ladder_arm=arm_id,
                        input_source="record_input", baseline_match="",
                        changed_vs_current=changed))
                if call["rss_bytes"] is not None and \
                        int(call["rss_bytes"]) >= RSS_LIMIT_BYTES:
                    terminal, stop = (X3_TERMINAL_ENGINEERING,
                                      {"reason": "RSS_CEILING_EXCEEDED"})
                    break
            if terminal != X3_TERMINAL_COMPLETED:
                break
            paired_rows.append(_paired_row(idx, rec, baseline_eval,
                                           arm_results, reconstruct_calls,
                                           ladder_calls_used))
    else:
        terminal = X3_TERMINAL_NOT_APPLICABLE

    ladder_calls_total = sum(1 for row in ladder_rows
                             if row["row_kind"] == "LADDER")
    reconstruction_calls_total = len(ladder_rows) - ladder_calls_total
    summary = {
        "cycle_id": "V72P2D7-ROOT-CAUSE-RESET",
        "change_name": "formal-ir-d7-root-cause-and-route-reset",
        "phase": "X3_REFERENCE_LADDER",
        "terminal": terminal,
        "claim_label": X3_CLAIM_LABEL,
        "scope": X3_CLAIM_LABEL,
        "x2_root": str(x2_path),
        "out_root": str(out_path),
        "selector": ("f=1.2 call records with invoked=true, status not crash, "
                     "finite=true, exact=false; no replacement, no dedup"),
        "plan": plan,
        "selected_records": int(len(selected)),
        "ladder_calls": int(ladder_calls_total),
        "reconstruction_calls": int(reconstruction_calls_total),
        "total_calls": int(ladder_calls_total + reconstruction_calls_total),
        "stored_wall_seconds": float(stored_wall),
        "peak_rss_bytes": peak_rss,
        "stop": stop,
        "output_files": list(X3_EVIDENCE_FILES),
        "no_overwrite": True,
    }
    manifest = {
        "cycle_id": "V72P2D7-ROOT-CAUSE-RESET",
        "change_name": "formal-ir-d7-root-cause-and-route-reset",
        "phase": "X3_REFERENCE_LADDER",
        "terminal": terminal,
        "claim_label": X3_CLAIM_LABEL,
        "x2_root": str(x2_path),
        "model_f_root": x2["manifest"]["model_f_root"],
        "selector": summary["selector"],
        "arms": list(LADDER_ARM_IDS),
        "plan": plan,
        "selected_records": int(len(selected)),
        "ladder_calls": int(ladder_calls_total),
        "reconstruction_calls": int(reconstruction_calls_total),
        "total_calls": int(ladder_calls_total + reconstruction_calls_total),
        "wall_budget_s": (None if wall_budget_s is None
                          else float(wall_budget_s)),
        "stop": stop,
        "output_files": list(X3_EVIDENCE_FILES),
        "no_overwrite": True,
        "baseline_gate": ("ROW_LAYERED_90 replay equality against the stored "
                          "X2 record (first mismatch stops the run)"),
    }
    with open(out_path / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    _write_csv(out_path / "ladder_records.csv", X3_LADDER_FIELDS, ladder_rows)
    _write_csv(out_path / "paired_summary.csv", X3_PAIRED_FIELDS, paired_rows)
    with open(out_path / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    report = [
        "# D7 R1 X3 failed-record reference ladder",
        "terminal: %s" % terminal,
        "claim: %s (strong reference diagnostic only)" % X3_CLAIM_LABEL,
        "x2_root: %s" % x2_path,
        "selected_records: %d" % len(selected),
        "ladder_calls: %d" % ladder_calls_total,
        "reconstruction_calls: %d" % reconstruction_calls_total,
        "total_calls: %d" % (ladder_calls_total + reconstruction_calls_total),
        "stop: %r" % (stop,),
        "",
        "Arms are ROW_LAYERED_90 / ROW_LAYERED_360 / FLOODING_90 on each",
        "reconstructed failed call; the baseline arm must reproduce the",
        "stored X2 record or the run stops immediately.",
    ]
    with open(out_path / "report.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(report) + "\n")
    with open(out_path / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("command: %s\n" % (command_str,))
        fh.write("terminal: %s\n" % terminal)
        fh.write("selected_records: %d\n" % len(selected))
        fh.write("ladder_calls: %d\n" % ladder_calls_total)
        fh.write("reconstruction_calls: %d\n" % reconstruction_calls_total)
        fh.write("stop: %r\n" % (stop,))
    return {"terminal": terminal, "out_root": str(out_path),
            "selected_records": int(len(selected)),
            "ladder_calls": int(ladder_calls_total),
            "reconstruction_calls": int(reconstruction_calls_total),
            "total_calls": int(ladder_calls_total + reconstruction_calls_total),
            "plan": plan, "stop": stop}


def _paired_row(record_idx, rec, baseline_eval, arm_results,
                reconstruction_calls, ladder_calls_used):
    baseline_exact = bool(baseline_eval["exact"]) if baseline_eval else ""
    baseline_syndrome = (bool(baseline_eval["syndrome_ok"])
                         if baseline_eval else "")
    arm_360 = arm_results.get("ROW_LAYERED_360")
    flooding = arm_results.get("FLOODING_90")

    def _changed(evaluated):
        if evaluated is None:
            return ""
        return bool(
            _csv_flag(rec.get("exact")) != bool(evaluated["exact"])
            or _csv_flag(rec.get("syndrome_ok"))
            != bool(evaluated["syndrome_ok"]))

    return {
        "record_idx": int(record_idx),
        "slot_idx": int(rec["slot_idx"]),
        "graph_idx": int(rec["graph_idx"]),
        "f": rec.get("f"),
        "seed": int(rec["seed"]),
        "arm": rec.get("arm"),
        "role": rec.get("role"),
        "layer": rec.get("layer"),
        "condition": rec.get("condition"),
        "rows": rec.get("rows"),
        "prior_kind": _prior_kind(rec),
        "baseline_exact": baseline_exact,
        "baseline_syndrome_ok": baseline_syndrome,
        "arm_360_exact": ("" if arm_360 is None else bool(arm_360["exact"])),
        "arm_360_syndrome_ok": ("" if arm_360 is None
                                else bool(arm_360["syndrome_ok"])),
        "arm_360_changed": _changed(arm_360),
        "flooding_exact": ("" if flooding is None else bool(flooding["exact"])),
        "flooding_syndrome_ok": ("" if flooding is None
                                 else bool(flooding["syndrome_ok"])),
        "flooding_changed": _changed(flooding),
        "baseline_replay_match": bool(baseline_eval is not None),
        "reconstruction_calls": int(reconstruction_calls),
        "ladder_calls": int(ladder_calls_used),
    }


# --------------------------------------------------------------------------
# X4 G2 bridge (packet §7 P08–P09; one authorized call into the frozen root)
# --------------------------------------------------------------------------
D5_EXECUTION_FLAG_KEYS = (
    "structure_execution_authorized", "g0_execution_authorized",
    "g0_recovery_execution_authorized", "p0_cost_execution_authorized",
    "g1_execution_authorized", "g2_execution_authorized",
    "synthetic_execution_authorized", "real_execution_authorized",
    "formal_execution_authorized",
)


def run_g2_bridge(*, d7_state, d5_state, repo_root=None, run_g2_fn=None,
                  frozen_root=None):
    """X4 bridge: require the X4 grant and all D5 execution flags false.

    Calls the existing ``run_g2_synthetic(authorized=True)`` exactly once
    (or the injected test runner) and writes only the frozen fresh G2 root.
    Never sets or writes the D5 ``g2_execution_authorized`` flag.
    """
    if not bool(d7_state.get("x4_g2_execution_authorized", False)):
        raise NotAuthorizedError(
            "X4 G2 execution is not authorized; refusing before any work")
    for key in D5_EXECUTION_FLAG_KEYS:
        if bool(d5_state.get(key, False)):
            raise NotAuthorizedError(
                "D5 execution flag %r must remain false for the X4 bridge"
                % (key,))
    if frozen_root is not None:
        root = Path(str(frozen_root))
    else:
        base = Path(repo_root) if repo_root is not None else Path(".")
        root = base / d5.G2_FORMAL_ROOT
    if root.exists():
        raise FileExistsError("refusing to overwrite G2 root: %s" % (root,))
    runner = run_g2_fn
    if runner is None:
        def runner():
            return d5.run_g2_synthetic(authorized=True)
    result = runner()
    result = result if isinstance(result, dict) else {}
    return {
        "out_root": str(root),
        "grade": result.get("grade"),
        "passed": bool(result.get("passed", False)),
        "decoder_calls": int(result.get("decoder_calls", 0)),
        "wall_seconds": result.get("wall_seconds"),
        "peak_rss_bytes": result.get("peak_rss_bytes"),
        "runtime_status": result.get("runtime_status"),
    }
