"""V72P2D9 GF32 DE-decoder calibration — same-input primitive certification,
finite-graph realization audit and frozen stability routing.

Frozen contract: ``openspec/changes/v72p2d9-gf32-de-decoder-calibration/``
(``design.md`` §§1–7, ``specs/gf32-de-decoder-calibration/spec.md``);
requirement source ``.workbuddy/tasks/``
``D9_DE_DECODER_CALIBRATION_AND_THRESHOLD_R1_TASK_PACKET.md`` §§5–7.

This module is the thin D9 delta:
- V26/v35 primitive same-input comparisons (channel centering, coefficient
  direction, variable/check/belief updates), tiny-tree equality certification
  and explicitly-labelled loopy/schedule non-equivalence diagnostics;
- deterministic finite-graph node/check degree realization for the frozen
  λ candidates via the accepted V37-P0 helpers, failing clearly on
  unrealizable socket/forest cells;
- the frozen stability matrix (4 candidates x 8 seeds x populations), the
  frozen stability labels and the frozen selection/routing terminals;
- the future MC stability wrapper (``run_de_call``) around the unchanged V26
  kernel and the D8 L1 Model-F channel adapter shape.

Reuse-first (import only, never edit): the V26 MC-DE kernel
(``nonbinary_v26_mcde``) and its V14 kernels, ``nonbinary_v9_common``,
``v37_de_screening.compute_trajectory_metrics``, the accepted V37-P0
``v37_degree_feasibility`` helpers, the D5 Model-F prior chain
(``v72p2d5_gf32_rate_mother``) and artifact loader
(``v72p2d5_model_f_input``), the D6 L1 row budgets
(``v72p2d6_gf32_graph_mother``), the D7-A independent GF32 reference oracle
(``v72p2d7_gf32_decoder_certification``) and the v35 primitive helpers
(``_check_update_log_batch`` / FWHT tables) as read-only references.

No production/finite-length decoder entrypoint is imported or called: the
certification uses primitive kernels only, and the tiny-tree and loopy
recurrences are explicit certification references, never the production
decoder. No DE call happens at import or in the certification; no new
dependency, no generic DE framework, optimizer, graph library, checkpoint or
cache.
"""

from __future__ import annotations

import importlib
import importlib.util as _ilu
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent


def _load_sibling(name):
    """Package-first sibling import (both repo namespace layouts), then file."""
    for mod_name in ("comparison_bench.src.comparison_bench.formal_ir." + name,
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
mfi = _load_sibling("v72p2d5_model_f_input")
d6 = _load_sibling("v72p2d6_gf32_graph_mother")
v9 = _load_sibling("nonbinary_v9_common")
v26 = _load_sibling("nonbinary_v26_mcde")
v37 = _load_sibling("v37_de_screening")
v37f = _load_sibling("v37_degree_feasibility")
v35 = _load_sibling("v35_algorithm_development")
d7a = _load_sibling("v72p2d7_gf32_decoder_certification")

#: V27-equivalent ρ binding (unchanged V26 harmonic-exact concentrate).
make_rho = v26.make_rho

__all__ = [
    "CHANGE_ID", "CYCLE_ID", "TRACK", "CLAIM_CEILING",
    "Q", "POLY", "MODEL_F_INPUT_ROOT", "SOLVER_ROOT",
    "DE_SEEDS", "D8_REPRODUCTION_SEEDS", "FRESH_SEEDS",
    "POPULATIONS_PRIMARY", "POPULATION_DIAGNOSTIC",
    "N_SAMPLES_PRIMARY", "N_SAMPLES_LARGE", "N_SAMPLES_DIAGNOSTIC",
    "MAX_ITER", "ENTROPY_TOL_BITS", "STREAK", "H0_BITS",
    "CONDITIONS", "CONDITION_ROLE", "CONDITION_POPULATIONS",
    "BASELINE_ID", "F1_0_CROSSING_MIN", "ADVANCE_MARGIN",
    "GRAPH_WIDTHS", "CANDIDATES", "TERMINALS",
    "T_SELECT", "T_STABILITY", "T_BASELINE_CONVERGED", "T_SEMANTICS",
    "T_GRAPH", "T_INVALID", "T_RESOURCE", "T_NOT_RUN",
    "STABLE_CONVERGED", "STABLE_UNCONVERGED", "STABILITY_AMBIGUOUS",
    "CLAIM_EQUIVALENCE_CERTIFIED", "CLAIM_NON_EQUIVALENCE_DIAGNOSTIC",
    "CLAIM_MISMATCH_DIAGNOSTIC", "CERT_ATOL", "CERT_SEED",
    "MAX_DE_CALLS", "MAX_SETUP_CALLS", "WALL_BUDGET_S",
    "PER_CALL_BUDGET_S", "RSS_BUDGET_BYTES",
    "condition_m", "enumerate_candidates", "validate_lambda_edge",
    "layer_rate_rho", "build_plan", "planned_de_calls",
    "expected_call_index", "de_center_row", "run_de_call",
    "trajectory_metrics", "aggregate_stability", "compute_routing",
    "exact_nominal_sockets", "graph_realization_cell",
    "audit_graph_realization", "GraphRealizationError",
    "certify_primitives", "certify_channel_centering",
    "certify_coefficient_direction",
    "build_l1_channel_from_counts", "load_l1_channel", "build_l1_sampler",
]

# --------------------------------------------------------------------------- #
# Frozen identifiers (design §1/§6; spec)
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2d9-gf32-de-decoder-calibration"
CYCLE_ID = "V72P2D9-DE-DECODER-CALIBRATION"
TRACK = "EXPLORE_HEAVY"
CLAIM_CEILING = (
    "calibration-contract evidence under the frozen CAL-only Model-F channel "
    "and decoder contract; no finite-length/FER/leakage/SKR/qualification/"
    "promotion/real-data claim; a selection authorizes only the next "
    "finite-length synthetic task packet and does not revive D7-H"
)

Q = 32
POLY = 37
N_BOB = 1024
LAMBDA_STAR = 137.3823795883264
DECODER_FLOOR = 1e-15
MODEL_F_INPUT_ROOT = "workspace/v72p2d5_model_f_input/20260907_r1"
SOLVER_ROOT = (
    "workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b")

D8_REPRODUCTION_SEEDS = (2026091601, 2026091602, 2026091603)
FRESH_SEEDS = (2026091801, 2026091802, 2026091803, 2026091804, 2026091805)
DE_SEEDS = D8_REPRODUCTION_SEEDS + FRESH_SEEDS

N_SAMPLES_PRIMARY = 4000
N_SAMPLES_LARGE = 16000
N_SAMPLES_DIAGNOSTIC = 4000
POPULATIONS_PRIMARY = (N_SAMPLES_PRIMARY, N_SAMPLES_LARGE)
POPULATION_DIAGNOSTIC = N_SAMPLES_DIAGNOSTIC

MAX_ITER = 60
ENTROPY_TOL_BITS = 1e-4
STREAK = 20
H0_BITS = 5.0

CONDITIONS = ("f1.2", "f1.0")
CONDITION_ROLE = {"f1.2": "primary_gate", "f1.0": "boundary_diagnostic"}
CONDITION_POPULATIONS = {"f1.2": POPULATIONS_PRIMARY,
                         "f1.0": (POPULATION_DIAGNOSTIC,)}

BASELINE_ID = "lam_d2_0.00_d3_1.00"
F1_0_CROSSING_MIN = 7
ADVANCE_MARGIN = 0.95

GRAPH_WIDTHS = (64, 128, 256)

#: Frozen 4-candidate matrix (design §6): DV3 reference + mandatory D8
#: replicates 0.45/0.50 + 0.55 upper-flank control. No other point.
CANDIDATES = (
    {"candidate_id": "lam_d2_0.00_d3_1.00", "lambda2": 0.0,
     "role": "baseline_reference", "lambda_edge": {3: 1.0}},
    {"candidate_id": "lam_d2_0.45_d3_0.55", "lambda2": 0.45,
     "role": "mandatory_d8_replicate", "lambda_edge": {2: 0.45, 3: 0.55}},
    {"candidate_id": "lam_d2_0.50_d3_0.50", "lambda2": 0.50,
     "role": "mandatory_d8_replicate", "lambda_edge": {2: 0.50, 3: 0.50}},
    {"candidate_id": "lam_d2_0.55_d3_0.45", "lambda2": 0.55,
     "role": "upper_flank_control", "lambda_edge": {2: 0.55, 3: 0.45}},
)

#: Budgets (design §6).
MAX_DE_CALLS = 96
MAX_SETUP_CALLS = 12
WALL_BUDGET_S = 1200.0
PER_CALL_BUDGET_S = 300.0
RSS_BUDGET_BYTES = 2 * 1024 ** 3

#: Stability labels (design §6).
STABLE_CONVERGED = "stable_converged"
STABLE_UNCONVERGED = "stable_unconverged"
STABILITY_AMBIGUOUS = "stability_ambiguous"

#: Terminals (design §6/§7; spec).
T_SELECT = "D9_DE_CALIBRATION_SELECT_ONE"
T_STABILITY = "D9_DE_STABILITY_NOT_CONFIRMED"
T_BASELINE_CONVERGED = "D9_DE_BASELINE_CONVERGED_REVIEW"
T_SEMANTICS = "D9_SEMANTICS_BLOCKED"
T_GRAPH = "D9_GRAPH_REALIZATION_INVALID"
T_INVALID = "D9_DE_EVIDENCE_INVALID"
T_RESOURCE = "D9_DE_RESOURCE_BLOCKED"
T_NOT_RUN = "D9_DE_NOT_RUN"
TERMINALS = (T_SELECT, T_STABILITY, T_BASELINE_CONVERGED, T_SEMANTICS,
             T_GRAPH, T_INVALID, T_RESOURCE, T_NOT_RUN)

#: Certification claim labels (design §2–§3).
CLAIM_EQUIVALENCE_CERTIFIED = "EQUIVALENCE_CERTIFIED"
CLAIM_NON_EQUIVALENCE_DIAGNOSTIC = "NON_EQUIVALENCE_DIAGNOSTIC"
CLAIM_MISMATCH_DIAGNOSTIC = "MISMATCH_DIAGNOSTIC"
CERT_ATOL = 1e-12
#: Certification fixture seed: outside the frozen DE seed set, fixed.
CERT_SEED = 2026091401


# --------------------------------------------------------------------------- #
# Rate / plan enumeration (frozen matrix)
# --------------------------------------------------------------------------- #
def condition_m(condition, width=64):
    """L1 disclosed rows ``m`` of a condition at a registered width (D6 table)."""
    if condition not in d6.F_POINTS:
        raise KeyError("unknown condition %r" % (condition,))
    if int(width) not in d6.ROW_BUDGETS:
        raise KeyError("unknown width %r" % (width,))
    return int(d6.ROW_BUDGETS[int(width)]["L1"][d6.F_POINTS[condition]])


def validate_lambda_edge(lambda_edge):
    """Candidate compatibility: edge-perspective λ over degrees {2,3}, unit mass.

    Positive finite weights only; any degree-1, negative, non-unit-sum or
    out-of-support entry is refused (raise), never silently dropped.
    """
    if not isinstance(lambda_edge, dict) or not lambda_edge:
        raise ValueError("lambda_edge must be a non-empty degree mapping")
    clean = {}
    total = 0.0
    for degree, weight in lambda_edge.items():
        if isinstance(degree, bool):
            raise ValueError("lambda support must be a subset of {2,3}")
        degree_i = int(degree)
        if degree_i != degree or degree_i not in (2, 3):
            raise ValueError("lambda support must be a subset of {2,3}, got %r"
                             % (degree,))
        w = float(weight)
        if not math.isfinite(w) or w <= 0.0:
            raise ValueError("lambda weights must be positive and finite, got %r"
                             % (weight,))
        clean[degree_i] = w
        total += w
    if abs(total - 1.0) > 1e-9:
        raise ValueError("lambda weights must sum to 1, got %.17g" % total)
    return clean


def enumerate_candidates():
    """The 4 frozen candidates in frozen order (validated copies)."""
    out = []
    for cand in CANDIDATES:
        out.append({
            "candidate_id": cand["candidate_id"],
            "lambda2": float(cand["lambda2"]),
            "role": cand["role"],
            "lambda_edge": validate_lambda_edge(dict(cand["lambda_edge"])),
        })
    return out


def layer_rate_rho(m_i, block_len, lambda_edge):
    """``R = 1 - m/n`` and the V26 harmonic-exact ρ for that rate."""
    rate = 1.0 - m_i / block_len
    rho = make_rho(rate, lambda_edge)
    return float(rate), {int(k): float(v) for k, v in rho.items()}


def build_plan():
    """Frozen 96-entry (candidate, condition, population, seed) plan in order.

    Order: candidate → condition (f1.2 then f1.0) → population (ascending) →
    seed (frozen order). A pair whose ``make_rho`` raises is recorded with its
    reason (``refused=True``) and excluded from the call count; it is never
    silently dropped or substituted. No adaptive rule exists here.
    """
    plan = []
    for cand in enumerate_candidates():
        for condition in CONDITIONS:
            for population in CONDITION_POPULATIONS[condition]:
                for seed in DE_SEEDS:
                    entry = {
                        "candidate_id": cand["candidate_id"],
                        "lambda2": cand["lambda2"],
                        "lambda_edge": dict(cand["lambda_edge"]),
                        "role": cand["role"],
                        "condition": condition,
                        "population": int(population),
                        "seed": int(seed),
                        "m": condition_m(condition),
                        "refused": False,
                        "refusal_reason": None,
                        "rate": None,
                        "rho": None,
                    }
                    try:
                        entry["rate"], entry["rho"] = layer_rate_rho(
                            entry["m"], 64, entry["lambda_edge"])
                    except Exception as ex:  # recorded refusal, never a drop
                        entry["refused"] = True
                        entry["refusal_reason"] = "%s: %s" % (type(ex).__name__, ex)
                    plan.append(entry)
    return plan


def planned_de_calls(plan=None):
    """Number of non-refused calls in the frozen plan (96 for the matrix)."""
    plan = build_plan() if plan is None else plan
    return sum(1 for entry in plan if not entry["refused"])


def expected_call_index(plan=None):
    """Ordered key→call_idx mapping of the frozen plan (0-based, no skips)."""
    plan = build_plan() if plan is None else plan
    index = {}
    for entry in plan:
        if entry["refused"]:
            continue
        key = (entry["candidate_id"], entry["condition"],
               int(entry["population"]), int(entry["seed"]))
        index[key] = len(index)
    return index


# --------------------------------------------------------------------------- #
# L1 Model-F channel (reused D8 adapter shape, unchanged semantics)
# --------------------------------------------------------------------------- #
def build_l1_channel_from_counts(counts_ab, p_b):
    """Frozen chain (design §1): injected counts/p_b → ``pb`` → E2 ``P_F`` → ``P1``."""
    counts = np.asarray(counts_ab, dtype=np.float64)
    pb = np.asarray(p_b, dtype=np.float64).ravel()
    if pb.size == 0 or not np.all(np.isfinite(pb)) or np.any(pb < 0.0):
        raise ValueError("p_b must be finite and nonnegative")
    total = float(pb.sum())
    if total <= 0.0:
        raise ValueError("p_b must have positive mass")
    pb_norm = pb / total
    pb_out, p_f = d5.prepare_model_f_prior_candidate(counts, pb_norm)
    p1 = np.asarray(d5.marginalize_f_to_p1(p_f), dtype=np.float64)
    return (np.asarray(pb_out, dtype=np.float64),
            np.asarray(p_f, dtype=np.float64), p1)


def load_l1_channel(model_f_root):
    """Read-only load of the accepted CAL-only Model-F artifact, then the chain."""
    data = mfi.load_model_f_input(model_f_root)
    return build_l1_channel_from_counts(data["counts_ab"], data["p_b"])


def build_l1_sampler(pb, p_f, p1):
    """``(n, 32)`` true-symbol-centered posterior rows drawn from the channel.

    Draws ``(b,a) ~ P_B(b)·P_F(a|b)``, then ``c[e] = floor_renorm(P1[:,b])[u XOR e]``
    with ``u = a // 32`` (V26 centering convention, 32-ary rows preserved).
    """
    pb = np.asarray(pb, dtype=np.float64).ravel()
    p_f = np.asarray(p_f, dtype=np.float64)
    p1 = np.asarray(p1, dtype=np.float64)
    if p_f.ndim != 2 or p1.ndim != 2 or p1.shape[0] != Q:
        raise ValueError("p_f must be 2-D and p1 must be (32, Bob)")
    if p_f.shape[0] % Q != 0 or p1.shape[1] != p_f.shape[1] \
            or pb.shape[0] != p_f.shape[1]:
        raise ValueError("pb/p_f/p1 shapes do not agree")
    n_bob = p_f.shape[1]
    joint = pb[None, :] * p_f
    total = float(joint.sum())
    if not math.isfinite(total) or abs(total - 1.0) > 1e-8:
        raise ValueError("pb * P_F(A|B) must be a probability table")
    flat = joint.ravel()
    idx = np.arange(Q, dtype=np.int64)

    def sampler(n, rng):
        pick = rng.choice(flat.size, size=int(n), p=flat)
        a = (pick // n_bob).astype(np.int64)
        b = (pick % n_bob).astype(np.int64)
        u = a // Q
        rows = d5._floor_renorm(p1[:, b].T, DECODER_FLOOR)
        centered = np.empty((int(n), Q), dtype=np.float64)
        for i in range(int(n)):
            centered[i] = rows[i, idx ^ u[i]]
        return centered

    return sampler


def de_center_row(prior_row, u):
    """V26 true-symbol centering: ``out[e] = prior_row[u XOR e]`` (true symbol ⇒ 0)."""
    prior = np.asarray(prior_row, dtype=np.float64)
    if prior.shape != (Q,):
        raise ValueError("prior_row must be a length-32 probability row")
    u = int(u)
    if not 0 <= u < Q:
        raise ValueError("u must be a GF(32) symbol in 0..31")
    return prior[np.arange(Q, dtype=np.int64) ^ u]


# --------------------------------------------------------------------------- #
# DE call wrapper and trajectory metrics (unchanged V26 kernel / V37 metrics)
# --------------------------------------------------------------------------- #
def run_de_call(lambda_edge, rho_edge, channel_sampler, seed, n_samples):
    """One V26 MC-DE call with the frozen D9 parameters (kernel unchanged)."""
    return v26.run_mcde_posterior(
        q=Q, lambda_edge=lambda_edge, rho_edge=rho_edge,
        channel_sampler=channel_sampler, n_samples=int(n_samples),
        max_iter=MAX_ITER, seed=int(seed), entropy_tol_bits=ENTROPY_TOL_BITS,
        streak=STREAK, record_entropy=True, record_channel_entropy=True)


def trajectory_metrics(entropy_trace_bits):
    """V37 metric definitions on a 1-based DE entropy trace (H(0)=5.0)."""
    trace = [float(x) for x in entropy_trace_bits]
    if not trace or not all(math.isfinite(x) for x in trace):
        raise ValueError("entropy trace must be non-empty and finite")
    return v37.compute_trajectory_metrics(
        trace, h0=H0_BITS, max_aut_iter=30, target_len=MAX_ITER,
        convergence_tol=ENTROPY_TOL_BITS)


# --------------------------------------------------------------------------- #
# Stability aggregation and frozen routing
# --------------------------------------------------------------------------- #
_GROUP_FIELDS = (("f1.2", "s4000_f12"), ("f1.2", "s16000_f12"),
                 ("f1.0", "s4000_f10"))


def _group_records(records):
    groups = {}
    for rec in records:
        key = (rec["candidate_id"], rec["condition"], int(rec["population"]))
        groups.setdefault(key, {})[int(rec["seed"])] = rec
    return groups


def aggregate_stability(records, *, allow_partial=False):
    """Per-candidate S4000/S16000 stability rows in frozen candidate order.

    ``S(pop)`` counts the 8 frozen seeds with ``H60 < 1e-4`` for the primary
    f1.2 condition; the f1.0 boundary diagnostic is reported but never gates.
    Missing seeds raise unless ``allow_partial``; a partially-run group reports
    the count over the seeds that exist and ``None`` when none exist.
    """
    groups = _group_records(records)
    rows = []
    for cand in enumerate_candidates():
        cid = cand["candidate_id"]
        row = {
            "candidate_id": cid,
            "role": cand["role"],
            "s4000_f12": None,
            "s16000_f12": None,
            "s4000_f10": None,
            "stability": None,
            "boundary_crossing": False,
            "worst_aut_30_p16000": None,
            "mean_aut_30_p16000": None,
            "worst_t_001_p16000": None,
            "aut30_ratio_dv3": None,
            "eligible": False,
        }
        for condition, field in _GROUP_FIELDS:
            population = (N_SAMPLES_PRIMARY
                          if field in ("s4000_f12", "s4000_f10")
                          else N_SAMPLES_LARGE)
            group = groups.get((cid, condition, population), {})
            present = [s for s in DE_SEEDS if s in group]
            missing = [s for s in DE_SEEDS if s not in group]
            if missing and not allow_partial:
                raise ValueError("missing DE calls for (%s, %s, %s): %s"
                                 % (cid, condition, population, missing))
            if present:
                row[field] = sum(1 for s in present if group[s]["converged"])
        if row["s4000_f12"] is not None and row["s16000_f12"] is not None:
            if row["s4000_f12"] == len(DE_SEEDS) \
                    and row["s16000_f12"] == len(DE_SEEDS):
                row["stability"] = STABLE_CONVERGED
            elif row["s4000_f12"] <= 6 and row["s16000_f12"] <= 6:
                row["stability"] = STABLE_UNCONVERGED
            else:
                row["stability"] = STABILITY_AMBIGUOUS
        if cid != BASELINE_ID and row["s4000_f10"] is not None \
                and row["s4000_f10"] >= F1_0_CROSSING_MIN:
            row["boundary_crossing"] = True
        group16 = groups.get((cid, "f1.2", N_SAMPLES_LARGE), {})
        if group16 and len(group16) == len(DE_SEEDS):
            worst = [float(group16[s]["aut_30"]) for s in DE_SEEDS]
            row["worst_aut_30_p16000"] = max(worst)
            row["mean_aut_30_p16000"] = sum(worst) / len(worst)
            row["worst_t_001_p16000"] = max(int(group16[s]["t_001"])
                                            for s in DE_SEEDS)
        rows.append(row)
    base = next(row for row in rows if row["candidate_id"] == BASELINE_ID)
    base_worst = base["worst_aut_30_p16000"]
    for row in rows:
        if row["worst_aut_30_p16000"] is not None and base_worst:
            row["aut30_ratio_dv3"] = row["worst_aut_30_p16000"] / base_worst
    return rows


def compute_routing(semantics_pass, graph_valid, records, *,
                    allow_partial=False):
    """Frozen routing terminals (design §6) over complete records.

    Order: semantics certification → degree realization → DV3 stability →
    eligible selection. f1.0 never gates; a crossing is reported only.
    """
    rows = aggregate_stability(records, allow_partial=allow_partial)
    result = {
        "rows": rows,
        "terminal": None,
        "winner_candidate_id": None,
        "eligible_candidate_ids": [],
        "boundary_crossing_ids": [],
        "baseline_stability": None,
        "semantics_pass": bool(semantics_pass),
        "graph_valid": bool(graph_valid),
    }
    if not semantics_pass:
        result["terminal"] = T_SEMANTICS
        return result
    if not graph_valid:
        result["terminal"] = T_GRAPH
        return result
    by_id = {row["candidate_id"]: row for row in rows}
    base = by_id[BASELINE_ID]
    result["baseline_stability"] = base["stability"]
    result["boundary_crossing_ids"] = [row["candidate_id"] for row in rows
                                       if row["boundary_crossing"]]
    if base["stability"] == STABLE_CONVERGED:
        result["terminal"] = T_BASELINE_CONVERGED
        return result
    if base["stability"] != STABLE_UNCONVERGED:
        result["terminal"] = T_STABILITY
        return result
    base_worst = float(base["worst_aut_30_p16000"])
    eligible = []
    for row in rows:
        if row["candidate_id"] == BASELINE_ID:
            continue
        if row["stability"] != STABLE_CONVERGED:
            continue
        worst = row["worst_aut_30_p16000"]
        if worst is None:
            continue
        if base_worst <= 0.0 or float(worst) <= ADVANCE_MARGIN * base_worst:
            eligible.append(row)
    eligible_ids = [row["candidate_id"] for row in eligible]
    for row in rows:
        row["eligible"] = row["candidate_id"] in eligible_ids
    result["eligible_candidate_ids"] = eligible_ids
    if eligible:
        winner = min(eligible, key=lambda row: (
            row["worst_aut_30_p16000"], row["mean_aut_30_p16000"],
            row["worst_t_001_p16000"], row["candidate_id"]))
        result["terminal"] = T_SELECT
        result["winner_candidate_id"] = winner["candidate_id"]
    else:
        result["terminal"] = T_STABILITY
    return result


# --------------------------------------------------------------------------- #
# Finite-graph degree/socket realization audit (design §5)
# --------------------------------------------------------------------------- #
class GraphRealizationError(ValueError):
    """A finite-graph degree/socket realization cell is not realizable."""


def exact_nominal_sockets(lambda2, width):
    """Exact nominal-λ node/socket counts: ``n2 = 3kn/(k+40)``, ``E = 3n - n2``.

    ``lambda2 = k/20`` for integer ``k``; returns exact ``Fraction`` strings so
    non-integer nominal socket counts are flagged as exact numbers.
    """
    width = int(width)
    lam2 = float(lambda2)
    k = int(round(lam2 * 20.0))
    if abs(lam2 * 20.0 - k) > 1e-9 or not 0 <= k <= 20:
        raise ValueError("lambda2 must be a frozen k/20 point, got %r" % (lam2,))
    n2 = Fraction(3 * k * width, k + 40)
    sockets = Fraction(3 * width) - n2
    return {"n2_exact": str(n2), "E_exact": str(sockets),
            "n2_integral": n2.denominator == 1,
            "E_integral": sockets.denominator == 1}


def graph_realization_cell(lambda_edge, width, m, *, candidate_id=None,
                           condition=None):
    """Deterministic finite-graph realization of one (λ, n, m) cell.

    Reuses the accepted V37-P0 apportionment (largest remainder, tie by
    ascending degree), the floor/ceil check allocation and the degree-2 forest
    bound. Raises :class:`GraphRealizationError` with the exact violations when
    a socket count is unrealizable (socket allocation or forced degree-2
    cycle); the frozen matrix never raises.
    """
    width, m = int(width), int(m)
    clean = validate_lambda_edge(lambda_edge)
    counts = v37f.calculate_node_degree_counts(clean, n=width)
    n2 = int(counts.get(2, 0))
    n3 = int(counts.get(3, 0))
    sockets = int(v37f.calculate_total_sockets(counts))
    alloc = v37f.calculate_check_degree_allocation(sockets, m)
    degree2 = v37f.analyze_degree2_subgraph(n2, m)
    violations = []
    if sum(int(v) for v in counts.values()) != width:
        violations.append("node counts do not sum to n=%d" % width)
    if sockets != 2 * n2 + 3 * n3:
        violations.append("socket total %d != 2*n2+3*n3" % sockets)
    if not alloc["is_socket_allocation_feasible"]:
        violations.append("socket allocation infeasible: dc_floor=%d < 2"
                          % alloc["dc_floor"])
    if alloc["n_checks_floor"] + alloc["n_checks_ceil"] != m:
        violations.append("check counts do not sum to m=%d" % m)
    if (alloc["dc_floor"] * alloc["n_checks_floor"]
            + alloc["dc_ceil"] * alloc["n_checks_ceil"]) != sockets:
        violations.append("check socket balance mismatch")
    if int(alloc["realized_max_check_degree"]) > 8:
        violations.append("realized max check degree %d > 8"
                          % alloc["realized_max_check_degree"])
    if not degree2["is_forest_feasible"]:
        violations.append("forced degree-2 cycle component: N2=%d > m-1=%d"
                          % (n2, m - 1))
    if violations:
        raise GraphRealizationError("%s at n=%d m=%d: %s"
                                    % (candidate_id or "candidate", width, m,
                                       "; ".join(violations)))
    lambda2_hat = 2.0 * n2 / sockets
    lambda_hat = ({3: 1.0} if n2 == 0
                  else {2: lambda2_hat, 3: 3.0 * n3 / sockets})
    allocated = {int(d): int(c)
                 for d, c in alloc["check_degree_allocation"].items()}
    rho_hat = {d: d * c / sockets for d, c in allocated.items()}
    rate = v9.reconstructed_rate(lambda_hat, rho_hat)
    expected_rate = 1.0 - m / width
    if abs(rate - expected_rate) > 1e-12:
        raise GraphRealizationError(
            "realized rate %.17g != 1 - m/n %.17g" % (rate, expected_rate))
    conc = v9.concentrated_check_distribution(expected_rate, clean)
    return {
        "candidate_id": candidate_id,
        "condition": condition,
        "width": width,
        "m": m,
        "n2": n2,
        "n3": n3,
        "E": sockets,
        "lambda2_realized": float(lambda2_hat),
        "lambda_edge_realized": {int(d): float(w) for d, w in lambda_hat.items()},
        "check_degree_allocation": allocated,
        "realized_max_check_degree": int(alloc["realized_max_check_degree"]),
        "rho_realized": {int(d): float(w) for d, w in rho_hat.items()},
        "de_rho": {int(d): float(w)
                   for d, w in v26.concentrated_rho_to_hist(conc).items()},
        "mean_check_degree_exact": float(alloc["mean_check_degree_exact"]),
        "N2_minus_m_minus_1": int(degree2["cycle_rank_lower_bound"]),
        "forest_feasible": bool(degree2["is_forest_feasible"]),
        "rate_realized": float(rate),
        "rate_error": float(abs(rate - expected_rate)),
        "exact_nominal": exact_nominal_sockets(clean.get(2, 0.0), width),
    }


def audit_graph_realization():
    """All frozen candidates × conditions × widths; valid iff every cell holds."""
    cells = []
    for cand in enumerate_candidates():
        for condition in CONDITIONS:
            for width in GRAPH_WIDTHS:
                m = condition_m(condition, width)
                try:
                    cell = graph_realization_cell(
                        cand["lambda_edge"], width, m,
                        candidate_id=cand["candidate_id"], condition=condition)
                except GraphRealizationError as ex:
                    cells.append({
                        "candidate_id": cand["candidate_id"],
                        "condition": condition, "width": int(width), "m": int(m),
                        "realizable": False, "violations": [str(ex)]})
                else:
                    cell["realizable"] = True
                    cell["violations"] = []
                    cells.append(cell)
    bad = [cell for cell in cells if not cell["realizable"]]
    return {
        "schema": "v72p2d9_graph_realization_audit_v1",
        "candidate_count": len(CANDIDATES),
        "widths": list(GRAPH_WIDTHS),
        "cell_count": len(cells),
        "cells": cells,
        "valid": not bad,
        "violation_count": len(bad),
    }


# --------------------------------------------------------------------------- #
# Same-input primitive certification (design §2–§3; packet §5)
# --------------------------------------------------------------------------- #
#: Tiny certification graphs: a 3-variable star tree (one degree-3 check, so a
#: single flooding round is exact BP — diameter 2) and a 2-variable 4-cycle
#: loopy graph. The loopy comparison is a labelled diagnostic only.
_TREE_H = np.array([[1, 2, 3]], dtype=np.uint8)
_TREE_SYNDROME = np.zeros(1, dtype=np.uint8)
_LOOPY_H = np.array([[1, 1], [1, 2]], dtype=np.uint8)
_LOOPY_SYNDROME = np.array([5, 7], dtype=np.uint8)


def _clean_rows(probs):
    """Elementwise floor ``1e-15`` + row normalization (v35 prior rule)."""
    p = np.maximum(np.asarray(probs, dtype=np.float64), DECODER_FLOOR)
    return p / p.sum(axis=-1, keepdims=True)


def _softmax_rows(log_rows):
    shifted = (np.asarray(log_rows, dtype=np.float64)
               - np.max(log_rows, axis=-1, keepdims=True))
    exp = np.exp(shifted)
    return exp / exp.sum(axis=-1, keepdims=True)


def _field():
    return v35.GF2mField.create(Q)


def _field_tables():
    return v35._get_gf32_tables(_field())


def _v26_check_all_targets(messages, coeffs, perm):
    """V26 check kernel for every target edge of one check (n=dc samples).

    Rows are in the V26 y-domain (outgoing coefficient absorbed as identity).
    """
    dc = len(messages)
    if dc < 2:
        raise ValueError("check degree must be >= 2")
    v2c = np.asarray(messages, dtype=np.float64)
    draws = np.full(dc, dc - 1, dtype=np.int64)
    idx = np.empty((dc - 1, dc), dtype=np.int64)
    coeff = np.empty((dc - 1, dc), dtype=np.int64)
    for target in range(dc):
        others = [j for j in range(dc) if j != target]
        for slot, j in enumerate(others):
            idx[slot, target] = j
            coeff[slot, target] = int(coeffs[j])
    return v26._check_update_coeff_jit(v2c, draws, idx, coeff, perm)


def _v35_check_all_targets(messages, coeffs, syndrome=0):
    """v35 production check primitive for every target edge of one check."""
    tables = _field_tables()
    logs = [np.log(np.maximum(np.asarray(m, dtype=np.float64), DECODER_FLOOR))
            for m in messages]
    outs = v35._check_update_log_batch(
        logs, [int(c) for c in coeffs], int(syndrome), _field(), tables)
    return np.asarray([np.exp(o) for o in outs], dtype=np.float64)


def _tiny_priors(seed, n):
    rng = np.random.default_rng(int(seed))
    priors = rng.random((int(n), Q)) * 2.0 + 0.05
    return priors / priors.sum(axis=1, keepdims=True)


def certify_channel_centering(seed=CERT_SEED):
    """Decoder prior row vs the DE centered channel row (design §2a).

    Checks the true symbol at index 0, the XOR reindexing identity, the
    elementwise floor/normalize commutation with that permutation and that the
    V26 consumer accepts the centered row unchanged.
    """
    rng = np.random.default_rng(int(seed))
    p1 = rng.random((Q, 4)) * 1.5 + 0.05
    p1 = p1 / p1.sum(axis=0, keepdims=True)
    b, u = 2, 9
    prior = d5._floor_renorm(p1[:, b].T, DECODER_FLOOR)
    centered = de_center_row(prior, u)
    deindexed = _clean_rows(prior[None, :])[0][np.arange(Q) ^ u]
    cen_clean = _clean_rows(centered[None, :])[0]
    v26_consumed = v26._channel_rows_from_centered(centered[None, :])[0]
    perm_diff = float(np.max(np.abs(cen_clean - deindexed)))
    mass_error = float(abs(centered.sum() - 1.0))
    true_symbol = float(centered[0]) == float(prior[u])
    consumer_diff = float(np.max(np.abs(v26_consumed - centered)))
    max_abs = max(perm_diff, mass_error, consumer_diff)
    return {
        "claim": CLAIM_EQUIVALENCE_CERTIFIED,
        "passed": bool(true_symbol and max_abs <= CERT_ATOL),
        "max_abs_diff": max_abs,
        "detail": ("DE row = decoder prior row XOR-reindexed by the true symbol "
                   "(true symbol at index 0); floor/renorm commutes elementwise "
                   "with the reindexing"),
    }


def certify_coefficient_direction():
    """V26 and v35 coefficient/permutation direction identity (design §2b).

    Checks ``perm[h, y] = inv(h)·y`` against the v35 production tables, the
    exact scaled-array identity ``tmp[y] = msg[inv(h)·y]`` ⇔
    ``scaled[mul(h, v)] = msg[v]``, and that the outgoing coset shift
    ``syn ⊕ coeff·s`` is a bijection.
    """
    perm, nonzero = v26.build_gf_perm_table(Q)
    mul, add, inv = _field_tables()
    rng = np.random.default_rng(CERT_SEED + 3)
    probes = [rng.random(Q) for _ in range(3)]
    max_abs = 0.0
    for h in nonzero:
        h_int = int(h)
        for y in range(Q):
            if int(perm[h_int, y]) != int(mul[int(inv[h_int]), y]):
                raise AssertionError("perm table direction mismatch")
        for probe in probes:
            tmp = probe[perm[h_int]]
            scaled = np.empty(Q, dtype=np.float64)
            scaled[mul[h_int, :]] = probe
            max_abs = max(max_abs, float(np.max(np.abs(tmp - scaled))))
    for syn in (0, 5, 31):
        for coeff in (1, 3, 17, 31):
            shifted = add[syn, mul[coeff, :]]
            if len({int(x) for x in shifted}) != Q:
                raise AssertionError("outgoing coset shift is not a bijection")
    return {
        "claim": CLAIM_EQUIVALENCE_CERTIFIED,
        "passed": max_abs <= CERT_ATOL,
        "max_abs_diff": max_abs,
        "detail": ("incoming permutation direction identity and outgoing coset "
                   "shift bijection; the V26 ensemble absorption of the outgoing "
                   "coefficient remains the frozen approximation (design §2b)"),
    }


def _certify_check_updates(seed):
    rng = np.random.default_rng(int(seed) + 1)
    perm, _ = v26.build_gf_perm_table(Q)
    mul = _field_tables()[0]
    diffs_v35 = {}
    diffs_sp = {}
    for dc in (2, 3, 4):
        messages = _clean_rows(rng.random((dc, Q)) * 2.0 + 0.05)
        coeffs = [1, 3, 7, 17][:dc]
        v26_rows = _v26_check_all_targets(messages, coeffs, perm)
        v35_rows = _v35_check_all_targets(messages, coeffs, syndrome=0)
        for target in range(dc):
            rel = v26_rows[target][mul[coeffs[target], :].astype(np.int64)]
            diffs_v35["dc%d_t%d" % (dc, target)] = float(
                np.max(np.abs(rel - v35_rows[target])))
        if dc <= 3:
            sp = d7a.direct_check_to_var([m for m in messages], coeffs, 0)
            for target in range(dc):
                diffs_sp["dc%d_t%d" % (dc, target)] = float(
                    np.max(np.abs(v35_rows[target] - sp[target])))
    max_v35 = max(diffs_v35.values())
    max_sp = max(diffs_sp.values())
    return (
        {"claim": CLAIM_EQUIVALENCE_CERTIFIED, "passed": max_v35 <= CERT_ATOL,
         "max_abs_diff": max_v35, "case_count": len(diffs_v35),
         "detail": ("V26 kernel vs v35 primitive on identical messages and "
                    "coefficients; the per-message outgoing-coefficient "
                    "permutation is exact, the ensemble absorption is not "
                    "claimed")},
        {"claim": CLAIM_EQUIVALENCE_CERTIFIED, "passed": max_sp <= CERT_ATOL,
         "max_abs_diff": max_sp, "case_count": len(diffs_sp),
         "detail": "v35 primitive vs D7-A direct sum-product enumeration (deg 2/3)"},
    )


def _certify_variable_belief(seed):
    rng = np.random.default_rng(int(seed) + 2)
    n, dv = 4, 3
    channel = _clean_rows(rng.random((n, Q)) * 2.0 + 0.05)

    def product_reference(row_pool, count):
        ref = np.empty((n, Q), dtype=np.float64)
        for i in range(n):
            acc = np.log(channel[i])
            for d in range(count):
                acc = acc + np.log(row_pool[i * count + d])
            ref[i] = _softmax_rows(acc[None, :])[0]
        return ref

    var_rows = _clean_rows(rng.random((n * (dv - 1), Q)) * 2.0 + 0.05)
    idx_var = np.zeros((dv - 1, n), dtype=np.int64)
    for i in range(n):
        for d in range(dv - 1):
            idx_var[d, i] = i * (dv - 1) + d
    got_var = v26._variable_or_belief_jit(
        var_rows, channel, np.full(n, dv - 1, dtype=np.int64), idx_var)
    max_var = float(np.max(np.abs(got_var - product_reference(var_rows, dv - 1))))

    bel_rows = _clean_rows(rng.random((n * dv, Q)) * 2.0 + 0.05)
    idx_bel = np.zeros((dv, n), dtype=np.int64)
    for i in range(n):
        for d in range(dv):
            idx_bel[d, i] = i * dv + d
    got_bel = v26._variable_or_belief_jit(
        bel_rows, channel, np.full(n, dv, dtype=np.int64), idx_bel)
    max_bel = float(np.max(np.abs(got_bel - product_reference(bel_rows, dv))))
    return (
        {"claim": CLAIM_EQUIVALENCE_CERTIFIED, "passed": max_var <= CERT_ATOL,
         "max_abs_diff": max_var, "case_count": n,
         "detail": ("V26 variable kernel (channel x dv-1 incoming) equals the "
                    "v35 flooding log-sum algebra on identical inputs")},
        {"claim": CLAIM_EQUIVALENCE_CERTIFIED, "passed": max_bel <= CERT_ATOL,
         "max_abs_diff": max_bel, "case_count": n,
         "detail": ("V26 belief kernel (channel x all incident) equals the v35 "
                    "flooding belief log-sum on identical inputs; the DE entropy "
                    "observable and the decoder terminal remain different "
                    "questions")},
    )


def _primitive_flooding_posterior(h_matrix, priors, syndrome, max_iter):
    """Certification reference: synchronous flooding BP from the v35 check
    primitive and the documented log-sum belief algebra.

    This is the same-input reference for tiny-tree equality and labelled loopy
    diagnostics; it is never the production decoder entrypoint.
    """
    mat = np.asarray(h_matrix, dtype=np.int64)
    m, n = mat.shape
    syn = np.asarray(syndrome, dtype=np.int64).reshape(-1)
    if syn.shape[0] != m:
        raise ValueError("syndrome length mismatch")
    prior = _clean_rows(priors)
    if prior.shape != (n, Q):
        raise ValueError("priors must be (n, 32)")
    edges = [[c for c in range(n) if mat[r, c]] for r in range(m)]
    coeffs = [[int(mat[r, c]) for c in edges[r]] for r in range(m)]
    for row in edges:
        if len(row) < 2:
            raise ValueError("check degree >= 2 required")
    position = {(r, c): p for r in range(m) for p, c in enumerate(edges[r])}
    log_prior = np.log(prior)
    u = [[np.zeros(Q, dtype=np.float64) for _ in row] for row in edges]
    beliefs = log_prior.copy()
    field = _field()
    tables = _field_tables()
    for _ in range(int(max_iter)):
        u_new = [None] * m
        for r in range(m):
            in_msgs = [beliefs[c] - u[r][position[(r, c)]]
                       for c in edges[r]]
            u_new[r] = v35._check_update_log_batch(
                in_msgs, coeffs[r], int(syn[r]), field, tables)
        beliefs = log_prior.copy()
        for r in range(m):
            for p, c in enumerate(edges[r]):
                u[r][p] = u_new[r][p]
                beliefs[c] = beliefs[c] + u[r][p]
    return _softmax_rows(beliefs)


def _certify_tree(seed):
    priors = _tiny_priors(int(seed) + 4, 3)
    exact = np.asarray(d7a.exact_posterior(_TREE_H, priors, _TREE_SYNDROME),
                       dtype=np.float64)
    perm, _ = v26.build_gf_perm_table(Q)
    mul = _field_tables()[0]
    m_checks, n_vars = _TREE_H.shape
    edges = [[c for c in range(n_vars) if _TREE_H[r, c]]
             for r in range(m_checks)]
    coeffs = [[int(_TREE_H[r, c]) for c in edges[r]] for r in range(m_checks)]
    check_msgs = {}
    max_check = 0.0
    for r in range(m_checks):
        messages = [priors[c] for c in edges[r]]
        sp = d7a.direct_check_to_var(messages, coeffs[r],
                                     int(_TREE_SYNDROME[r]))
        v26_rows = _v26_check_all_targets(messages, coeffs[r], perm)
        for target, c in enumerate(edges[r]):
            check_msgs[(r, c)] = np.asarray(sp[target], dtype=np.float64)
            rel = v26_rows[target][mul[coeffs[r][target], :].astype(np.int64)]
            max_check = max(max_check,
                            float(np.max(np.abs(rel - sp[target]))))
    incident = [[r for r in range(m_checks) if c in edges[r]]
                for c in range(n_vars)]
    max_incident = max(len(row) for row in incident)
    c2v_rows = []
    idx = np.zeros((max_incident, n_vars), dtype=np.int64)
    for c in range(n_vars):
        for d, r in enumerate(incident[c]):
            c2v_rows.append(check_msgs[(r, c)])
            idx[d, c] = len(c2v_rows) - 1
    c2v = np.asarray(c2v_rows, dtype=np.float64)
    draws = np.array([len(row) for row in incident], dtype=np.int64)
    belief = v26._variable_or_belief_jit(c2v, priors, draws, idx)
    flood = _primitive_flooding_posterior(_TREE_H, priors, _TREE_SYNDROME, 1)
    max_belief = float(np.max(np.abs(belief - exact)))
    max_flood = float(np.max(np.abs(flood - exact)))
    max_belief_flood = float(np.max(np.abs(belief - flood)))
    return (
        {"claim": CLAIM_EQUIVALENCE_CERTIFIED, "passed": max_check <= CERT_ATOL,
         "max_abs_diff": max_check,
         "detail": "V26 check kernel vs D7-A direct SP on the star tree"},
        {"claim": CLAIM_EQUIVALENCE_CERTIFIED, "passed": max_belief <= CERT_ATOL,
         "max_abs_diff": max_belief,
         "detail": "V26 belief product vs exact star-tree posterior"},
        {"claim": CLAIM_EQUIVALENCE_CERTIFIED, "passed": max_flood <= CERT_ATOL,
         "max_abs_diff": max_flood,
         "detail": "v35 primitive flooding (1 round) vs exact star-tree posterior"},
        {"claim": CLAIM_EQUIVALENCE_CERTIFIED,
         "passed": max_belief_flood <= CERT_ATOL,
         "max_abs_diff": max_belief_flood,
         "detail": "V26 belief vs v35 primitive flooding on the star tree"},
    )


def _diagnose_loopy(seed):
    priors = _tiny_priors(int(seed) + 5, 2)
    exact = np.asarray(d7a.exact_posterior(_LOOPY_H, priors, _LOOPY_SYNDROME),
                       dtype=np.float64)
    flood = _primitive_flooding_posterior(_LOOPY_H, priors, _LOOPY_SYNDROME, 2)
    sweeps, iterations, _ = d7a.row_layered_reference(
        _LOOPY_H, priors, _LOOPY_SYNDROME, 2)
    if sweeps:
        row_layered = _softmax_rows(sweeps[-1])
    else:
        row_layered = _softmax_rows(np.log(_clean_rows(priors)))
    return (
        {"claim": CLAIM_NON_EQUIVALENCE_DIAGNOSTIC, "passed": None,
         "max_abs_diff": float(np.max(np.abs(flood - exact))),
         "detail": ("loopy flooding vs exact enumeration: non-equivalence "
                    "diagnostic, never promoted to an equivalence claim")},
        {"claim": CLAIM_NON_EQUIVALENCE_DIAGNOSTIC, "passed": None,
         "max_abs_diff": float(np.max(np.abs(row_layered - flood))),
         "row_layered_iterations": int(iterations),
         "detail": ("loopy flooding vs row-layered schedules: non-equivalence "
                    "diagnostic; no trajectory or terminal equivalence is "
                    "claimed (design §2f)")},
    )


def certify_primitives(seed=CERT_SEED):
    """Same-input primitive certification report (design §3; packet §5)."""
    checks = {}
    checks["channel_centering"] = certify_channel_centering(seed)
    checks["coefficient_direction"] = certify_coefficient_direction()
    (checks["check_update_v26_vs_v35"],
     checks["check_update_v35_vs_direct_sp"]) = _certify_check_updates(seed)
    (checks["variable_update_v26_vs_logsum"],
     checks["belief_update_v26_vs_logsum"]) = _certify_variable_belief(seed)
    (checks["tree_v26_check_vs_direct_sp"],
     checks["tree_v26_belief_vs_exact"],
     checks["tree_v35_flooding_vs_exact"],
     checks["tree_v26_belief_vs_v35_flooding"]) = _certify_tree(seed)
    (checks["loopy_flooding_vs_exact"],
     checks["loopy_flooding_vs_row_layered"]) = _diagnose_loopy(seed)
    checks["de_metric_vs_decoder_terminal"] = {
        "claim": CLAIM_MISMATCH_DIAGNOSTIC,
        "passed": None,
        "max_abs_diff": None,
        "detail": ("DE terminal = mean bits/symbol check entropy below 1e-4 for "
                   "20 consecutive iterations; decoder terminal = exact syndrome "
                   "equality; no certified bridge exists (design §2e/§2g)"),
    }
    equivalence = [name for name, check in checks.items()
                   if check["claim"] == CLAIM_EQUIVALENCE_CERTIFIED]
    diagnostics = [name for name, check in checks.items()
                   if check["claim"] != CLAIM_EQUIVALENCE_CERTIFIED]
    semantics_pass = all(checks[name]["passed"] for name in equivalence)
    return {
        "schema": "v72p2d9_primitive_certification_v1",
        "seed": int(seed),
        "semantics_pass": bool(semantics_pass),
        "checks": checks,
        "equivalence_claims": equivalence,
        "non_equivalence_diagnostics": diagnostics,
        "ensemble_path_equivalence": False,
        "claim_ceiling": (
            "primitive same-input equality, coefficient direction and tree-only "
            "posteriors; flooding-DE vs row-layered trajectory equivalence, "
            "DE-terminal vs decoder-terminal equivalence and finite-length/FER "
            "claims are NOT established"),
    }


