"""V72P2D8 rate-aligned GF32 ensemble feasibility — thin L1 Model-F adapter.

Frozen contract:
``openspec/changes/v72p2d8-rate-aligned-gf32-ensemble-feasibility/``
(``design.md`` §§1–6, ``specs/rate-aligned-gf32-ensemble-feasibility/spec.md``).

Reuse-first (import only, never copy, never edit):
``nonbinary_v26_mcde`` (accepted V26 MC-DE kernel), ``nonbinary_v14_mcde``
kernels via V26, ``nonbinary_v9_common`` helpers, the accepted D5 Model-F prior
chain (``v72p2d5_gf32_rate_mother``), the frozen Model-F artifact loader
(``v72p2d5_model_f_input``), the accepted D6 L1 row budgets
(``v72p2d6_gf32_graph_mother``), the V37 trajectory metrics
(``v37_de_screening.compute_trajectory_metrics``) and the V37-P0 forest
diagnostic (``v37_degree_feasibility.analyze_degree_feasibility``).

Only the D8 delta lives here: the L1-only Model-F channel sampler, the frozen
bounded candidate grid, the V27-style rate/ρ helper and the advancement /
terminal arithmetic. No production decoder call. No L2. No new dependency.
"""

from __future__ import annotations

import importlib
import importlib.util as _ilu
import math
import sys
from collections.abc import Mapping
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

#: V27-equivalent ρ binding (``nonbinary_v27_gate.layer_rate_rho``).
make_rho = v26.make_rho

# --------------------------------------------------------------------------- #
# Frozen identifiers
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2d8-rate-aligned-gf32-ensemble-feasibility"
CYCLE_ID = "V72P2D8-RATE-ALIGNED-ENSEMBLE"
TRACK = "EXPLORE_HEAVY"
CLAIM_CEILING = (
    "DE-only synthetic asymptotic evidence under the frozen CAL-only Model-F "
    "channel and decoder contract; no finite-length/FER/leakage/SKR/"
    "qualification/promotion/real-data claim; advancement authorizes only the "
    "next finite-length task packet and does not revive D7-H"
)

Q = 32
POLY = 37
N_BOB = 1024
LAMBDA_STAR = 137.3823795883264
DECODER_FLOOR = 1e-15
MODEL_F_INPUT_ROOT = "workspace/v72p2d5_model_f_input/20260907_r1"
SOLVER_ROOT = "workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405"

#: Frozen DE parameters (V37R1 values) and seeds.
N_SAMPLES = 4000
MAX_ITER = 60
ENTROPY_TOL_BITS = 1e-4
STREAK = 20
H0_BITS = 5.0
DE_SEEDS = (2026091601, 2026091602, 2026091603)

#: L1-only rate conditions, primary first.
CONDITIONS = ("f1.2", "f1.0")
CONDITION_ROLE = {"f1.2": "primary", "f1.0": "secondary"}

#: Bounded deterministic candidate grid (hard cap 21).
CANDIDATE_STEP = 0.05
CANDIDATE_COUNT = 21
BASELINE_ID = "lam_d2_0.00_d3_1.00"
FOREST_WIDTHS = (64, 128, 256)
ADVANCE_MARGIN = 0.95

#: Budgets (design §6).
MAX_DE_CALLS = 126
MAX_SETUP_CALLS = 20
WALL_BUDGET_S = 1800.0
PER_CALL_BUDGET_S = 120.0
RSS_BUDGET_BYTES = 2 * 1024 ** 3

T_ADVANCE = "D8_DE_ADVANCE_ONE_ENSEMBLE"
T_NO_ADVANCE = "D8_DE_NO_ADVANCE"
T_BASELINE = "D8_DE_BASELINE_NOT_CONVERGED"
T_INVALID = "D8_DE_EVIDENCE_INVALID"
T_RESOURCE = "D8_DE_RESOURCE_BLOCKED"
T_NOT_RUN = "D8_DE_NOT_RUN"
TERMINALS = (T_ADVANCE, T_NO_ADVANCE, T_BASELINE, T_INVALID, T_RESOURCE,
             T_NOT_RUN)


# --------------------------------------------------------------------------- #
# Rate / candidate enumeration
# --------------------------------------------------------------------------- #
def condition_m(condition, width=64):
    """L1 disclosed rows ``m`` of a condition at a registered width (D6 table)."""
    if condition not in d6.F_POINTS:
        raise KeyError("unknown condition %r" % (condition,))
    if int(width) not in d6.ROW_BUDGETS:
        raise KeyError("unknown width %r" % (width,))
    return int(d6.ROW_BUDGETS[int(width)]["L1"][d6.F_POINTS[condition]])


def layer_rate_rho(m_i, block_len, lambda_edge):
    """V27-equivalent: ``R = 1 - m/n`` and ``rho = make_rho(R, lambda)``."""
    rate = 1.0 - m_i / block_len
    rho = make_rho(rate, lambda_edge)
    return float(rate), {int(k): float(v) for k, v in rho.items()}


def validate_lambda_edge(lambda_edge):
    """Candidate compatibility: edge-perspective λ over degrees {2,3}, unit mass.

    Positive finite weights only; any degree-1, negative, non-unit-sum or
    out-of-support entry is refused (raise), never silently dropped.
    """
    if not isinstance(lambda_edge, Mapping) or not lambda_edge:
        raise ValueError("lambda_edge must be a non-empty degree mapping")
    clean = {}
    total = 0.0
    for degree, weight in lambda_edge.items():
        if isinstance(degree, bool):
            raise ValueError("lambda support must be a subset of {2,3}")
        try:
            degree_i = int(degree)
        except (TypeError, ValueError):
            raise ValueError("lambda support must be a subset of {2,3}, got %r"
                             % (degree,))
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
    """The 21 frozen IDs in ascending λ2; zero-weight degrees are dropped."""
    out = []
    for i in range(CANDIDATE_COUNT):
        lam2 = round(CANDIDATE_STEP * i, 2)
        lam3 = round(1.0 - lam2, 2)
        lambda_edge = {}
        if lam2 > 0.0:
            lambda_edge[2] = lam2
        if lam3 > 0.0:
            lambda_edge[3] = lam3
        out.append({
            "candidate_id": "lam_d2_%.2f_d3_%.2f" % (lam2, lam3),
            "lambda2": lam2,
            "lambda3": lam3,
            "lambda_edge": validate_lambda_edge(lambda_edge),
        })
    return out


def _forest_cell(lambda_edge, width, m):
    report = v37f.analyze_degree_feasibility(lambda_edge, n=int(width),
                                             m_values=[int(m)])
    n2 = int(report["degree2_analysis"]["N2"])
    return {"N": int(width), "m": int(m), "N2": n2,
            "gamma2": max(0, n2 - (int(m) - 1))}


def build_candidate_plan(conditions=CONDITIONS):
    """42 frozen (candidate, condition) entries in plan order; refusals recorded.

    A pair whose ``make_rho`` raises is recorded with its reason (Refused=True)
    and excluded from advancement; it is never silently dropped or substituted.
    """
    plan = []
    for cand in enumerate_candidates():
        for condition in conditions:
            entry = {
                "candidate_id": cand["candidate_id"],
                "lambda2": cand["lambda2"],
                "lambda_edge": dict(cand["lambda_edge"]),
                "condition": condition,
                "role": CONDITION_ROLE[condition],
                "m": condition_m(condition),
                "refused": False,
                "refusal_reason": None,
                "rho": None,
                "forest": {},
            }
            try:
                entry["rate"], entry["rho"] = layer_rate_rho(
                    entry["m"], 64, entry["lambda_edge"])
            except Exception as ex:  # recorded refusal, never a silent drop
                entry["refused"] = True
                entry["refusal_reason"] = "%s: %s" % (type(ex).__name__, ex)
                entry["rate"] = None
            for width in FOREST_WIDTHS:
                cell = _forest_cell(entry["lambda_edge"], width,
                                    condition_m(condition, width))
                entry["forest"][str(width)] = cell
            plan.append(entry)
    return plan


# --------------------------------------------------------------------------- #
# L1 Model-F channel
# --------------------------------------------------------------------------- #
def build_l1_channel_from_counts(counts_ab, p_b):
    """Frozen chain (design §2): injected counts/p_b → ``pb`` → E2 ``P_F`` → ``P1``."""
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
    if p_f.shape[0] % Q != 0 or p1.shape[1] != p_f.shape[1] or pb.shape[0] != p_f.shape[1]:
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


# --------------------------------------------------------------------------- #
# DE call wrapper and trajectory metrics
# --------------------------------------------------------------------------- #
def run_de_call(lambda_edge, rho_edge, channel_sampler, seed):
    """One V26 MC-DE call with the frozen D8 parameters (unchanged kernel)."""
    return v26.run_mcde_posterior(
        q=Q, lambda_edge=lambda_edge, rho_edge=rho_edge,
        channel_sampler=channel_sampler, n_samples=N_SAMPLES,
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
# Aggregation / advancement / terminals
# --------------------------------------------------------------------------- #
def aggregate_candidate_conditions(records, plan, *, allow_partial=False,
                                   seeds=DE_SEEDS):
    """Per (candidate, condition) rows in plan order; raises on missing calls."""
    by_key = {}
    for rec in records:
        by_key.setdefault((rec["candidate_id"], rec["condition"]), {})[
            int(rec["seed"])] = rec
    rows = []
    for entry in plan:
        key = (entry["candidate_id"], entry["condition"])
        forest = entry.get("forest") or {}
        row = {
            "candidate_id": entry["candidate_id"],
            "condition": entry["condition"],
            "role": entry["role"],
            "rate": entry["rate"],
            "m": entry.get("m"),
            "refused": bool(entry["refused"]),
            "refusal_reason": entry["refusal_reason"],
            "n_seeds": 0,
            "seeds_converged": 0,
            "worst_aut_30": None,
            "mean_aut_30": None,
            "worst_t_001": None,
            "aut30_ratio_baseline": None,
            "eligible": False,
            "N2_n64": forest.get("64", {}).get("N2"),
            "N2_n128": forest.get("128", {}).get("N2"),
            "N2_n256": forest.get("256", {}).get("N2"),
            "gamma2_n64": forest.get("64", {}).get("gamma2"),
            "gamma2_n128": forest.get("128", {}).get("gamma2"),
            "gamma2_n256": forest.get("256", {}).get("gamma2"),
        }
        if not entry["refused"]:
            calls = by_key.get(key, {})
            missing = [s for s in seeds if s not in calls]
            if missing and not allow_partial:
                raise ValueError("missing DE calls for %s: %s" % (key, missing))
            recs = [calls[s] for s in seeds if s in calls]
            if recs:
                row["n_seeds"] = len(recs)
                row["seeds_converged"] = sum(1 for r in recs if r["converged"])
                row["worst_aut_30"] = max(float(r["aut_30"]) for r in recs)
                row["mean_aut_30"] = (sum(float(r["aut_30"]) for r in recs)
                                      / len(recs))
                row["worst_t_001"] = max(int(r["t_001"]) for r in recs)
        rows.append(row)
    return rows


def compute_advancement(records, plan, seeds=DE_SEEDS):
    """Frozen advancement/terminal decision (design §5) over complete records."""
    rows = aggregate_candidate_conditions(records, plan, allow_partial=False,
                                          seeds=seeds)
    by_id = {}
    for row in rows:
        by_id.setdefault(row["candidate_id"], {})[row["condition"]] = row
    base_rows = by_id[BASELINE_ID]
    result = {
        "rows": rows,
        "terminal": None,
        "winner_candidate_id": None,
        "eligible_candidate_ids": [],
        "baseline_converged": False,
        "baseline_primary_worst_aut_30": None,
    }
    if any(row["refused"] for row in base_rows.values()):
        result["terminal"] = T_INVALID
        return result
    base_primary = next(row for row in base_rows.values()
                        if row["role"] == "primary")
    base_aut = float(base_primary["worst_aut_30"])
    base_conv = all(row["seeds_converged"] == len(seeds)
                    for row in base_rows.values())
    result["baseline_primary_worst_aut_30"] = base_aut
    result["baseline_converged"] = bool(base_conv)
    eligible = []
    if base_conv:
        for cid, conds in by_id.items():
            if cid == BASELINE_ID:
                continue
            if any(row["refused"] for row in conds.values()):
                continue
            if any(row["seeds_converged"] != len(seeds)
                   for row in conds.values()):
                continue
            primary = next(row for row in conds.values()
                           if row["role"] == "primary")
            if base_aut <= 0.0 or primary["worst_aut_30"] <= ADVANCE_MARGIN * base_aut:
                eligible.append(primary)
    eligible_ids = [row["candidate_id"] for row in eligible]
    for row in rows:
        row["eligible"] = row["candidate_id"] in eligible_ids
        if row["refused"] or row["worst_aut_30"] is None or base_aut <= 0.0:
            row["aut30_ratio_baseline"] = None
        else:
            row["aut30_ratio_baseline"] = row["worst_aut_30"] / base_aut
    result["eligible_candidate_ids"] = eligible_ids
    if not base_conv:
        result["terminal"] = T_BASELINE
        return result
    if eligible:
        winner = min(eligible, key=lambda row: (
            row["worst_aut_30"], row["mean_aut_30"], row["worst_t_001"],
            row["candidate_id"]))
        result["terminal"] = T_ADVANCE
        result["winner_candidate_id"] = winner["candidate_id"]
    else:
        result["terminal"] = T_NO_ADVANCE
    return result
