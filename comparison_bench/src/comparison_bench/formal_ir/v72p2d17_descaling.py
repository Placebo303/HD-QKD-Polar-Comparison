"""D17 current-channel asymptotic-to-finite scaling — readiness (D02–D06).

Change: ``v72p2d17-asymptotic-finite-scaling``.
Frozen authority: ``.workbuddy/tasks/D17_ASYMPTOTIC_FINITE_SCALING_READINESS_R1_TASK_PACKET.md``
(§2 hierarchy, §4 B, §5 C, §6 D02–D06, §7 STOP) +
``openspec/changes/v72p2d17-asymptotic-finite-scaling/`` (``design.md``
audit tables F1–F19/H1–3, compatibility classes, holdout lock, frozen
15-point grid + seeds + convergence rule + future DE command/root/budgets,
probit law + identifiability + epsilon targets; ``specs/de-scaling/spec.md``).
Track: implementation/readiness. ZERO scientific DE/decoder calls here; no
DE batch, no D16 execution, no D7-H, no real data, no commit/push.

Four-level hierarchy (never collapsed): L1 generator entropy ``H_l`` +
gap ``delta = 5m/n − H_l``; L2 current-channel MC-DE threshold
``delta_DE`` (parameter slot from the reviewed DE result, never refit to
finite data); L3 predeclared probit backoff; L4 post-prediction residuals
(never folded into the backoff without a new preregistration).

Reuse contract (IMPORT, never copy; all predecessor access is LAZY so the
refusal and PROFILE_ONLY paths never bind the V26 kernel, the production
decoder, or Model-F content):

- V26 MC-DE kernel + D9 semantic adapter (``d9.make_rho`` /
  ``d9.run_de_call`` / ``d9.build_l1_sampler`` / ``d9.load_l1_channel`` /
  ``d9.graph_realization_cell``) — resolved only inside
  :func:`bind_production_de` on the explicitly authorized path, or not at
  all (tests inject fakes);
- D5 Model-F prior chain (``prepare_model_f_prior_candidate`` /
  ``build_f_model_concentration`` / ``marginalize_f_to_p1`` /
  ``conditionalize_f_to_p2`` / ``oracle_l2_prior`` / floor rules);
- D15/D16 frozen constants (``H_l``/loads, D16 cells/seeds/root);
- R2 root refusal + decoder contract (``refuse_out_root``, Q/poly/90/1.0).

Added here (D17 deltas only): frozen channel/decoder/DE-grid constants,
the 15-point × 2-pop × 8-seed plan builder, the bracket-midpoint
``delta_DE`` rule with edge flags, the audit artifact builder, the probit
scaling fit with the identifiability ladder, epsilon inversion to integer
row backoff, the blank D16 prediction schema + gates, the fake-injectable
DE batch orchestrator + read-only verifier. No new DE kernel, no new
dependency (NumPy + stdlib only).
"""

from __future__ import annotations

import csv
import importlib
import importlib.util as _ilu
import inspect
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent


def _load_sibling(name):
    """Package-first sibling import, then file path (lazy; authorized paths only)."""
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


def _repo_root():
    return Path(__file__).resolve().parents[4]


__all__ = [
    "CHANGE_ID", "CYCLE_ID", "TRACK", "CLAIM_CEILING",
    "H_L1", "H_L2", "LOAD_L1", "LOAD_L2", "LAMBDA_STAR",
    "PRIOR_FLOOR", "DECODER_FLOOR", "Q", "POLY",
    "DECODER_MAX_ITER", "DAMPING_ALPHA", "MODEL_F_INPUT_ROOT",
    "DE_MAX_ITER", "DE_ENTROPY_TOL_BITS", "DE_STREAK",
    "DE_PROFILES", "DE_GRID_M", "DE_SEEDS", "DE_POPULATIONS",
    "VAR_SIDES", "EDGE_TOTALS", "PROFILE_LAYER",
    "DE_CALL_CEILING", "SETUP_CEILING", "SETUP_UNITS",
    "WALL_BUDGET_S", "PER_CALL_BUDGET_S", "RSS_BUDGET_BYTES",
    "FUTURE_ROOT", "FROZEN_COMMAND", "AUTHORIZATION",
    "D16_CELLS", "D16_GRAPH_SEEDS", "D16_BLOCK_SEEDS", "BANNED_SEEDS",
    "D16_OFFICIAL_ROOT", "FAKE_SCRATCH_ROOT",
    "EPS_PRIMARY", "EPS_SENSITIVITY", "M0_BASELINE",
    "BOOTSTRAP_SEED", "BOOTSTRAP_B",
    "MODEL_NOT_IDENTIFIABLE",
    "EVIDENCE_FILES",
    "delta_of", "rate_of", "disclosed_bits", "baseline_m0",    "check_allocation", "degree_cell",
    "build_de_plan", "planned_de_calls", "expected_call_index",
    "bracket_delta_de",
    "phi", "p_success", "logistic_p", "check_monotonic_limits",
    "binomial_nll", "fit_profile", "cluster_bootstrap", "loo_range",
    "fit_with_ladder", "ndtri",
    "delta_star", "m_star", "row_backoff", "predict_interval",
    "classify_observation", "assert_fit_eligible",
    "assert_no_banned_seeds", "refuse_fake_scratch",
    "assert_d16_root_absent",
    "blank_prediction", "write_predictions",
    "residual_record", "assert_no_residual_covariates",
    "audit_rows", "build_audit_artifacts",
    "describe_plan", "run_de_batch", "write_de_root", "verify_de_root",
    "probe_fresh_root", "verify_channel_identity",
    "verify_seed_disjointness", "bind_production_de",
]

# --------------------------------------------------------------------------- #
# Frozen identifiers
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2d17-asymptotic-finite-scaling"
CYCLE_ID = "V72P2D17-ASYMPTOTIC-FINITE-SCALING"
TRACK = "implementation/readiness"
CLAIM_CEILING = (
    "empirical calibration for this channel/decoder family only; no "
    "universal theorem, no FER qualification, no D7-H/route-closure/"
    "publication claim; DE convergence is not finite-code usability; "
    "epsilon targets are modeling targets, never FER requirements"
)

# --------------------------------------------------------------------------- #
# Channel identity (frozen; proposal A01 verdict EXACT)
# --------------------------------------------------------------------------- #
H_L1 = 4.286720430201375
H_L2 = 3.222719884634378
LOAD_L1 = 548.700215065776
LOAD_L2 = 412.508145233200
LAMBDA_STAR = 137.3823795883263870
PRIOR_FLOOR = 1e-300  # max(p, 1e-300) pre-log2, no renormalization
CHANNEL_AXES = "p_f(Alice=1024,Bob=1024)"
CHANNEL_AXIS_RULE = "A=32*U1+U2"
PRIOR_ESTIMATOR = "prepare_model_f_prior_candidate"
PRIOR_TABLE = "build_f_model_concentration"
BITS_PER_ROW = 5
N_REF = 128

# --------------------------------------------------------------------------- #
# Decoder contract (frozen; reused from R2/D5, never re-declared numerically)
# --------------------------------------------------------------------------- #
Q = 32
POLY = 37
DECODER_MAX_ITER = 90
DAMPING_ALPHA = 1.0
DECODER_FLOOR = 1e-15  # _floor_renorm: floor + renormalization
L1_INPUT_LINE = "q@P (get_l1_app_prior_l2)"
L2_ORACLE_LINE = "oracle_l2_prior -> get_conditional_posterior_l2 (true-U1, diagnostic-only)"
MODEL_F_INPUT_ROOT = "workspace/v72p2d5_model_f_input/20260907_r1"

# --------------------------------------------------------------------------- #
# Frozen DE grid (design §4; bounded, non-adaptive, no outcome-driven change)
# --------------------------------------------------------------------------- #
DE_MAX_ITER = 60
DE_ENTROPY_TOL_BITS = 1e-4
DE_STREAK = 20
DE_CONVERGENCE_H = 1e-4  # S_pop = #{H60 < 1e-4} over 8 seeds
DE_PROFILES = ("L045", "L055", "L2")
PROFILE_LAYER = {"L045": "L1", "L055": "L1", "L2": "L2"}
DE_GRID_M = {
    "L045": (106, 110, 114, 118, 122),
    "L055": (116, 119, 122, 124, 126),
    "L2": (89, 94, 99, 104, 109),
}
DE_SEEDS = tuple(range(2026094201, 2026094209))
DE_POPULATIONS = (4000, 16000)
#: m-independent variable node sides (frozen D9 largest-remainder rule).
VAR_SIDES = {"L045": {2: 71, 3: 57}, "L055": {2: 83, 3: 45}, "L2": {3: 128}}
EDGE_TOTALS = {"L045": 313, "L055": 301, "L2": 384}

DE_CALL_CEILING = 240  # 3 profiles x 5 m x 8 seeds x 2 pops
SETUP_CEILING = 12
SETUP_UNITS = 4  # channel load, plan build, sampler build, manifest
WALL_BUDGET_S = 1200.0
PER_CALL_BUDGET_S = 300.0
RSS_BUDGET_BYTES = 2 * 1024 ** 3

F_BRACKET = "DE_BRACKET"
F_ONE_SIDED_LOW = "DE_ONE_SIDED_LOW"
F_ONE_SIDED_HIGH = "DE_ONE_SIDED_HIGH"
F_SOFT_BRACKET = "DE_SOFT_BRACKET"
F_POP_UNSTABLE = "POP_UNSTABLE"
S_LO_MAX = 3  # S <= 3/8 counts as unconverged side
S_HI_MIN = 6  # S >= 6/8 counts as converged side

FUTURE_ROOT = ("workspace/d17_current_channel_asymptotic_de_"
               "7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718")
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d17_scaling_development.py --de-batch "
    "--execution-authorized --model-f-root %s --out-root %s"
    % (MODEL_F_INPUT_ROOT, FUTURE_ROOT))
AUTHORIZATION = ("separate explicit user/main-thread authorization required "
                 "before --de-batch (default false, fail-closed)")

EVIDENCE_FILES = ("manifest.json", "de_plan.csv", "de_records.csv",
                  "de_traces.csv", "summary.json", "command_log.txt")

# --------------------------------------------------------------------------- #
# D16 holdout lock (frozen; proposal A05 / design §7)
# --------------------------------------------------------------------------- #
#: (profile, m, delta); L045/L055 share m125 disclosure, hence one delta.
D16_CELLS = (
    ("L045", 125, 0.596092069798625),
    ("L055", 125, 0.596092069798625),
    ("L2", 94, 0.449155115365622),
)
D16_GRAPH_SEEDS = tuple(range(2026094001, 2026094013))
D16_BLOCK_SEEDS = tuple(range(2026094101, 2026094109))
BANNED_SEEDS = frozenset(D16_GRAPH_SEEDS) | frozenset(D16_BLOCK_SEEDS)
D16_OFFICIAL_ROOT = ("workspace/d16_matched_backoff_discriminator_"
                     "b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a")
#: Fake-identity scratch: D1606 fake-runner basetemps carrying real D16
#: identities with FAKE outcomes. Never read as outcomes anywhere.
FAKE_SCRATCH_ROOT = "workspace/d16_align_20260915_a/"
#: Fake-proof signature (proposal A05): wall ~1e-5 s, iters 1,
#: all-converged_exact rows from test paths.
FAKE_WALL_MAX_S = 1e-3
FAKE_ITERS = 1

# --------------------------------------------------------------------------- #
# Scaling law constants (frozen; design §§2/5/6)
# --------------------------------------------------------------------------- #
N_EXP = -2.0 / 3.0  # beta * n^(-2/3) shift, bits/symbol
EPS_PRIMARY = 0.10
EPS_SENSITIVITY = 0.01
M0_BASELINE = {"L1": {64: 55, 128: 110, 256: 220},
               "L2": {64: 42, 128: 83, 256: 166}}
MODEL_NOT_IDENTIFIABLE = "MODEL_NOT_IDENTIFIABLE"
BOOTSTRAP_SEED = 2026094200
BOOTSTRAP_B = 2000
#: D04 deterministic search bounds (implementation choice; a future D04
#: packet may re-freeze them, but they never adapt to outcomes in a run).
ALPHA_BOUNDS = (1e-3, 1e3)
BETA_BOUNDS = (-1.5, 1.5)
NLL_FLAT_TOL = 1e-9
BOUND_FRAC_TOL = 0.5  # >50% of bootstrap refits on bounds -> degenerate

RESIDUAL_FIELDS = ("admission", "rank", "four_cycles", "girth",
                   "iterations", "residual_syndrome_weight",
                   "graph_random_effect")


# --------------------------------------------------------------------------- #
# Rate math (computed from the frozen loads, never copied as constants)
# --------------------------------------------------------------------------- #
def _h_of_layer(layer):
    key = str(layer)
    if key == "L1":
        return H_L1
    if key == "L2":
        return H_L2
    raise KeyError("unknown layer %r" % (layer,))


def disclosed_bits(rows):
    """Disclosed bits for an integer row count (5 bits per row)."""
    return int(rows) * BITS_PER_ROW


def rate_of(m, n=N_REF):
    """Exact ensemble rate ``R = 1 − m/n`` at the n128 reference."""
    return 1.0 - float(m) / float(n)


def delta_of(m, n, layer):
    """Disclosure gap ``delta = 5m/n − H_l`` in bits/symbol."""
    return disclosed_bits(m) / float(n) - _h_of_layer(layer)


def baseline_m0(layer, n):
    """Frozen integer rows at zero gap, recomputed (STOP on mismatch)."""
    got = int(math.ceil(float(n) * _h_of_layer(layer) / BITS_PER_ROW))
    want = M0_BASELINE[str(layer)][int(n)]
    if got != int(want):
        raise ValueError("m0 baseline drift: layer %s n=%d recomputed %d "
                         "!= frozen %d" % (layer, n, got, want))
    return got


def check_allocation(E, m):
    """Frozen D9 concentrated check allocation: flo=floor(E/m), b=E−flo·m
    ceils, a=m−b floors. Pure arithmetic; rho itself comes only from the
    lazy-bound ``make_rho`` (never reimplemented here)."""
    E, m = int(E), int(m)
    flo = E // m
    b = E - flo * m
    a = m - b
    if flo < 2 or a < 0 or b < 0:
        raise ValueError("infeasible concentrated allocation E=%d m=%d" % (E, m))
    alloc = {}
    if a:
        alloc[flo] = a
    alloc[flo + 1] = alloc.get(flo + 1, 0) + b
    if b == 0:
        alloc = {flo: m}
    if sum(alloc.values()) != m \
            or sum(d * c for d, c in alloc.items()) != E:
        raise ValueError("allocation balance mismatch E=%d m=%d" % (E, m))
    return alloc


def degree_cell(profile, m):
    """Frozen ``(n, m, var/check counts, E)`` DE cell + rate, verified."""
    key = str(profile)
    if key not in VAR_SIDES:
        raise KeyError("unknown DE profile %r" % (profile,))
    if int(m) not in DE_GRID_M[key]:
        raise KeyError("m=%r outside frozen %s grid %r"
                       % (m, key, DE_GRID_M[key]))
    layer = PROFILE_LAYER[key]
    var_counts = dict(VAR_SIDES[key])
    E = EDGE_TOTALS[key]
    if sum(var_counts.values()) != N_REF:
        raise ValueError("frozen %s variable counts do not sum to n" % key)
    if sum(d * c for d, c in var_counts.items()) != E:
        raise ValueError("frozen %s socket total != frozen E" % key)
    alloc = check_allocation(E, int(m))
    return {"profile": key, "layer": layer, "n": N_REF, "m": int(m),
            "var_counts": var_counts, "check_counts": alloc, "E": E,
            "rate": rate_of(m), "d": disclosed_bits(m) / float(N_REF),
            "delta": delta_of(m, N_REF, layer)}


# --------------------------------------------------------------------------- #
# DE plan (15 points x 2 pops x 8 seeds = 240 calls; frozen order)
# --------------------------------------------------------------------------- #
def build_de_plan():
    """Frozen plan: profile (L045, L055, L2) → m ascending → population
    ascending → seed ascending; ``call_idx`` 0..239 with no skips."""
    plan = []
    for profile in DE_PROFILES:
        for m in DE_GRID_M[profile]:
            cell = degree_cell(profile, m)
            for population in DE_POPULATIONS:
                for seed in DE_SEEDS:
                    plan.append({
                        "call_idx": len(plan),
                        "profile": profile,
                        "layer": cell["layer"],
                        "m": int(m),
                        "rate": cell["rate"],
                        "d": cell["d"],
                        "delta": cell["delta"],
                        "E": cell["E"],
                        "var_counts": dict(cell["var_counts"]),
                        "check_counts": dict(cell["check_counts"]),
                        "population": int(population),
                        "seed": int(seed),
                    })
    return plan


def planned_de_calls(plan=None):
    """Non-skippable call count (240 for the frozen matrix)."""
    return len(build_de_plan() if plan is None else plan)


def expected_call_index(plan=None):
    """Ordered (profile, m, population, seed) → call_idx mapping."""
    plan = build_de_plan() if plan is None else plan
    return {(e["profile"], e["m"], e["population"], e["seed"]): e["call_idx"]
            for e in plan}


def _bracket_from_counts(profile, s_by_m):
    """Bracket pair from one population's S counts (raises fail-closed)."""
    ms = list(DE_GRID_M[str(profile)])
    deltas = {m: delta_of(m, N_REF, PROFILE_LAYER[str(profile)]) for m in ms}
    los = [m for m in ms if int(s_by_m[m]) <= S_LO_MAX]
    his = [m for m in ms if int(s_by_m[m]) >= S_HI_MIN]
    if not los and his:
        lo = min(ms, key=lambda m: deltas[m])
        return {"delta_de": deltas[lo], "h": None, "flag": F_ONE_SIDED_LOW,
                "lo_m": None, "hi_m": lo}
    if not his and los:
        hi = max(ms, key=lambda m: deltas[m])
        return {"delta_de": deltas[hi], "h": None, "flag": F_ONE_SIDED_HIGH,
                "lo_m": hi, "hi_m": None}
    if not los or not his:
        raise ValueError("no ≤3/≥6 bracket pair for %s (recorded, never "
                         "re-gridded)" % (profile,))
    lo_m = max(los, key=lambda m: deltas[m])
    hi_m = min(his, key=lambda m: deltas[m])
    if not deltas[hi_m] > deltas[lo_m]:
        raise ValueError("non-monotone S bracket for %s (fail-closed)"
                         % (profile,))
    h = (deltas[hi_m] - deltas[lo_m]) / 2.0
    middle = [m for m in ms
              if S_LO_MAX < int(s_by_m[m]) < S_HI_MIN]
    flag = F_SOFT_BRACKET if middle else F_BRACKET
    return {"delta_de": (deltas[lo_m] + deltas[hi_m]) / 2.0, "h": h,
            "flag": flag, "lo_m": lo_m, "hi_m": hi_m}


def bracket_delta_de(profile, s16000, s4000=None):
    """Frozen §4 convergence rule: bracket-midpoint at pop16000.

    ``s16000``/``s4000`` map ``m → S`` (converged seeds of 8). Returns the
    pop16000 bracket plus flags; a pop4000/pop16000 bracket disagreement
    appends ``POP_UNSTABLE`` (primary stays pop16000). Never re-grids.
    """
    primary = _bracket_from_counts(profile, s16000)
    flags = [primary["flag"]]
    if s4000 is not None:
        try:
            check = _bracket_from_counts(profile, s4000)
            if (check["lo_m"], check["hi_m"]) != (primary["lo_m"],
                                                  primary["hi_m"]):
                flags.append(F_POP_UNSTABLE)
        except ValueError:
            flags.append(F_POP_UNSTABLE)
    primary["flags"] = flags
    return primary


# --------------------------------------------------------------------------- #
# Scaling law (predeclared probit; delta_DE is a fixed parameter slot)
# --------------------------------------------------------------------------- #
def _phi_vec(x):
    arr = np.asarray(x, dtype=np.float64)
    erf = np.vectorize(math.erf)(arr / math.sqrt(2.0))
    return 0.5 * (1.0 + erf)


def phi(x):
    """Standard normal CDF (stdlib erf; scalar or array)."""
    if np.ndim(x) == 0:
        return 0.5 * (1.0 + math.erf(float(x) / math.sqrt(2.0)))
    return _phi_vec(x)


def p_success(n, delta, delta_de, alpha, beta):
    """``Phi((delta − delta_DE − beta·n^(−2/3))·sqrt(n/alpha))``, alpha > 0."""
    alpha = float(alpha)
    if not math.isfinite(alpha) or alpha <= 0.0:
        raise ValueError("alpha must be positive finite (STOP: units/sign)")
    nn = np.asarray(n, dtype=np.float64)
    dd = np.asarray(delta, dtype=np.float64)
    shift = dd - float(delta_de) - float(beta) * nn ** N_EXP
    return phi(shift * np.sqrt(nn / alpha))


def logistic_p(n, delta, delta_de, alpha_log, beta):
    """Descriptive-only logistic-link sensitivity (same fixed delta_DE)."""
    alpha_log = float(alpha_log)
    if not math.isfinite(alpha_log) or alpha_log <= 0.0:
        raise ValueError("alpha_log must be positive finite")
    n = float(n)
    z = (float(delta) - float(delta_de) - float(beta) * n ** N_EXP) \
        * math.sqrt(n / alpha_log)
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def check_monotonic_limits(delta_de, alpha, beta):
    """Frozen §2 STOP check: strict increase in delta; n→∞ limits; the
    delta=delta_DE slice. Raises (STOP) on any violation."""
    alpha = float(alpha)
    if not math.isfinite(alpha) or alpha <= 0.0:
        raise ValueError("STOP: alpha must be > 0, got %r" % (alpha,))
    for n in (64, 128, 256):
        grid = [delta_de + d for d in (-1.0, -0.1, 0.0, 0.1, 1.0)]
        ps = [float(p_success(n, d, delta_de, alpha, beta)) for d in grid]
        if not all(b > a for a, b in zip(ps, ps[1:])):
            raise ValueError("STOP: p not strictly increasing in delta "
                             "(n=%d)" % n)
        if not float(p_success(n, delta_de + 2.0, delta_de, alpha, beta)) > 0.99:
            raise ValueError("STOP: p ↛ 1 above threshold (n=%d)" % n)
        if not float(p_success(n, delta_de - 2.0, delta_de, alpha, beta)) < 0.01:
            raise ValueError("STOP: p ↛ 0 below threshold (n=%d)" % n)
    mid = float(p_success(128, delta_de, delta_de, alpha, 0.0))
    if abs(mid - 0.5) > 1e-12:
        raise ValueError("STOP: p(delta_DE) != 0.5 for beta=0")
    return True


def _cluster_arrays(clusters):
    n = np.array([float(c["n"]) for c in clusters], dtype=np.float64)
    d = np.array([float(c["delta"]) for c in clusters], dtype=np.float64)
    y = np.array([int(c["y"]) for c in clusters], dtype=np.float64)
    t = np.array([int(c["t"]) for c in clusters], dtype=np.float64)
    if np.any(y < 0) or np.any(t <= 0) or np.any(y > t):
        raise ValueError("clusters need 0 <= y <= t, t > 0")
    return n, d, y, t


def binomial_nll(clusters, delta_de, alpha, beta):
    """Exact per-graph-cluster binomial negative log-likelihood."""
    if delta_de is None:
        raise ValueError("delta_DE is a required parameter slot (never "
                         "refit to finite data)")
    n, d, y, t = _cluster_arrays(clusters)
    p = np.asarray(p_success(n, d, float(delta_de), alpha, beta),
                   dtype=np.float64)
    p = np.clip(p, 1e-12, 1.0 - 1e-12)  # ponytail: log guard only, not a model term
    return float(-np.sum(y * np.log(p) + (t - y) * np.log(1.0 - p)))


def _grid_fit(clusters, delta_de, beta_fixed=None):
    """Deterministic coarse-to-fine grid search (NumPy + stdlib only)."""
    la = np.linspace(math.log10(ALPHA_BOUNDS[0]),
                     math.log10(ALPHA_BOUNDS[1]), 25)
    if beta_fixed is None:
        lb = np.linspace(BETA_BOUNDS[0], BETA_BOUNDS[1], 31)
        best = (math.inf, None, None)
        for a in 10.0 ** la:
            for b in lb:
                v = binomial_nll(clusters, delta_de, float(a), float(b))
                if v < best[0]:
                    best = (v, float(a), float(b))
        alpha, beta = best[1], best[2]
        free_beta = True
    else:
        best = (math.inf, None)
        for a in 10.0 ** la:
            v = binomial_nll(clusters, delta_de, float(a), float(beta_fixed))
            if v < best[0]:
                best = (v, float(a))
        alpha, beta = best[1], float(beta_fixed)
        free_beta = False
    for _ in range(2):  # ponytail: fixed 2 refinements, no adaptive stopping rule
        la = np.linspace(math.log10(alpha) - 0.35, math.log10(alpha) + 0.35, 17)
        la = np.clip(la, math.log10(ALPHA_BOUNDS[0]),
                     math.log10(ALPHA_BOUNDS[1]))
        if free_beta:
            lb = np.linspace(beta - 0.2, beta + 0.2, 17)
            lb = np.clip(lb, BETA_BOUNDS[0], BETA_BOUNDS[1])
            best = (math.inf, alpha, beta)
            for a in 10.0 ** la:
                for b in lb:
                    v = binomial_nll(clusters, delta_de, float(a), float(b))
                    if v < best[0]:
                        best = (v, float(a), float(b))
            alpha, beta = best[1], best[2]
        else:
            best = (math.inf, alpha)
            for a in 10.0 ** la:
                v = binomial_nll(clusters, delta_de, float(a), beta)
                if v < best[0]:
                    best = (v, float(a))
            alpha = best[1]
    return {"alpha": float(alpha), "beta": float(beta),
            "nll": float(binomial_nll(clusters, delta_de, alpha, beta)),
            "beta_fixed": (None if free_beta else float(beta))}


def fit_profile(clusters, delta_de, *, beta_fixed=None):
    """Fit (alpha, beta) at fixed delta_DE; beta_fixed=0 gives one-param."""
    if not clusters:
        raise ValueError("no clusters to fit")
    if delta_de is None or not math.isfinite(float(delta_de)):
        raise ValueError("delta_DE must be a finite reviewed-DE value")
    prof = {c["profile"] for c in clusters}
    if len(prof) != 1:
        raise ValueError("fit exactly one profile at a time, got %r" % (prof,))
    return _grid_fit(clusters, float(delta_de), beta_fixed=beta_fixed)


def _on_bounds(fit):
    a_hit = fit["alpha"] <= ALPHA_BOUNDS[0] * 1.001 \
        or fit["alpha"] >= ALPHA_BOUNDS[1] * 0.999
    b_hit = fit["beta"] <= BETA_BOUNDS[0] + 1e-12 \
        or fit["beta"] >= BETA_BOUNDS[1] - 1e-12
    return a_hit, b_hit


def cluster_bootstrap(clusters, delta_de, *, beta_fixed=None, B=BOOTSTRAP_B,
                      seed=BOOTSTRAP_SEED):
    """Graph-cluster bootstrap within profile, preserving (n, delta) cells."""
    cells = {}
    for i, c in enumerate(clusters):
        cells.setdefault((float(c["n"]), float(c["delta"])), []).append(i)
    rng = np.random.default_rng(int(seed))
    alphas, betas = [], []
    for _ in range(int(B)):
        idx = []
        for members in cells.values():
            idx.extend(rng.choice(members, size=len(members),
                                  replace=True).tolist())
        sub = [clusters[i] for i in idx]
        try:
            fit = _grid_fit(sub, float(delta_de), beta_fixed=beta_fixed)
        except ValueError:
            continue
        alphas.append(fit["alpha"])
        betas.append(fit["beta"])
    if not alphas:
        raise ValueError("bootstrap produced no refits")
    return {"alpha": np.array(alphas), "beta": np.array(betas),
            "B": int(B), "seed": int(seed), "n_ok": len(alphas)}


def _pct(arr, q):
    return float(np.percentile(np.asarray(arr, dtype=np.float64), q))


def loo_range(clusters, delta_de, *, beta_fixed=None):
    """Leave-one-graph-out refit range (graph identity = graph_id)."""
    ids = sorted({c["graph_id"] for c in clusters})
    if len(ids) < 2:
        raise ValueError("LOO needs >= 2 graphs")
    alphas, betas = [], []
    for gid in ids:
        sub = [c for c in clusters if c["graph_id"] != gid]
        fit = _grid_fit(sub, float(delta_de), beta_fixed=beta_fixed)
        alphas.append(fit["alpha"])
        betas.append(fit["beta"])
    return {"alpha_min": min(alphas), "alpha_max": max(alphas),
            "beta_min": min(betas), "beta_max": max(betas),
            "n_graphs": len(ids)}


def fit_with_ladder(clusters, delta_de, *, primary_one_param=False,
                    B=BOOTSTRAP_B, seed=BOOTSTRAP_SEED):
    """Identifiability ladder: two-param → one-param (beta=0) →
    MODEL_NOT_IDENTIFIABLE. Never reports unstable coefficients."""
    if delta_de is None:
        raise ValueError("delta_DE slot required (never refit to finite data)")
    ns = {float(c["n"]) for c in clusters}
    if primary_one_param or len(ns) < 2:
        fit = fit_profile(clusters, delta_de, beta_fixed=0.0)
        a_hit, _ = _on_bounds(fit)
        if a_hit:
            return {"model": MODEL_NOT_IDENTIFIABLE, "reason":
                    "one-param alpha on search bound", "fit": fit}
        return {"model": "one_param", "beta_fixed": 0.0, "fit": fit,
                "reason": ("predeclared single-width one-param primary"
                           if len(ns) < 2 else "requested one-param")}
    fit = fit_profile(clusters, delta_de)
    a_hit, b_hit = _on_bounds(fit)
    boot = cluster_bootstrap(clusters, delta_de, B=B, seed=seed)
    n_bound = int(np.sum((boot["alpha"] <= ALPHA_BOUNDS[0] * 1.001)
                         | (boot["alpha"] >= ALPHA_BOUNDS[1] * 0.999)))
    if a_hit or b_hit or n_bound / max(len(boot["alpha"]), 1) > BOUND_FRAC_TOL:
        down = fit_profile(clusters, delta_de, beta_fixed=0.0)
        da_hit, _ = _on_bounds(down)
        if da_hit:
            return {"model": MODEL_NOT_IDENTIFIABLE,
                    "reason": "alpha on bound after beta=0 downgrade",
                    "fit": down, "two_param_fit": fit}
        return {"model": "one_param", "beta_fixed": 0.0, "fit": down,
                "reason": "two-param unidentifiable (bound/degenerate "
                          "bootstrap)", "two_param_fit": fit}
    return {"model": "two_param", "fit": fit,
            "bootstrap": {"alpha_ci95": (_pct(boot["alpha"], 2.5),
                                        _pct(boot["alpha"], 97.5)),
                          "beta_ci95": (_pct(boot["beta"], 2.5),
                                        _pct(boot["beta"], 97.5)),
                          "B": boot["B"], "seed": boot["seed"]},
            "reason": "two-param identified"}


def ndtri(p):
    """Standard-normal quantile (Acklam approximation; stdlib only)."""
    p = float(p)
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02,
         -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02,
         -1.556989798598866e+02, 6.680131188771972e+01,
         -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01,
         2.445134137142996e+00, 3.754408661907416e+00]
    plow, phigh = 0.02425, 1.0 - 0.02425
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q
             + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    elif p > phigh:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q
              + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    else:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r
             + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r
                             + b[4]) * r + 1.0)
    # ponytail: two Newton steps lift Acklam (~1e-9) to machine precision.
    for _ in range(2):
        err = 0.5 * (1.0 + math.erf(x / math.sqrt(2.0))) - p
        x -= err * math.sqrt(2.0 * math.pi) * math.exp(0.5 * x * x)
    return x


def delta_star(n, eps, delta_de, alpha, beta):
    """``delta_DE + beta·n^(−2/3) + z_{1−eps}·sqrt(alpha/n)``."""
    return float(delta_de) + float(beta) * float(n) ** N_EXP \
        + ndtri(1.0 - float(eps)) * math.sqrt(float(alpha) / float(n))


def m_star(n, eps, delta_de, alpha, beta, layer):
    """Smallest integer rows reaching the epsilon target."""
    need = float(n) * (_h_of_layer(layer) + delta_star(n, eps, delta_de,
                                                       alpha, beta)) / BITS_PER_ROW
    return int(math.ceil(need - 1e-9))


def row_backoff(n, eps, delta_de, alpha, beta, layer):
    """Integer row backoff ``m* − m0`` with the frozen inversion."""
    m0 = baseline_m0(layer, int(n))
    return m_star(int(n), eps, delta_de, alpha, beta, layer) - m0


def predict_interval(n, delta, fits, delta_de_list):
    """Union band over bootstrap (alpha, beta) samples × delta_DE ± h."""
    lo, hi = math.inf, -math.inf
    for alpha, beta in fits:
        for dd in delta_de_list:
            p = float(p_success(n, delta, dd, alpha, beta))
            lo, hi = min(lo, p), max(hi, p)
    if not math.isfinite(lo):
        raise ValueError("empty prediction ensemble")
    return lo, hi


# --------------------------------------------------------------------------- #
# Data eligibility + holdout gates (fail-closed)
# --------------------------------------------------------------------------- #
def classify_observation(*, source, layer, profile, oracle=False, joint=False):
    """One compatibility class per observation (design §3).

    APP/joint outcomes are EXCLUDED from every single-layer fit; L2 ORACLE
    enters only the true-conditioned L2 model; non-D17 profiles are
    descriptive-only; D11 replay/oracle and D16 are validation-only.
    """
    src = str(source)
    if bool(joint) or str(profile) in ("APP", "JOINT") \
            or "APP" in str(profile):
        return "EXCLUDED_APP_JOINT"
    if src == "D16":
        return "VALIDATION_ONLY"  # held-out arms: predictions only, pre-run
    if bool(oracle):
        if str(layer) != "L2" or str(profile) not in ("L2", "L2-ORACLE",
                                                      "L2_ORACLE"):
            return "EXCLUDED_ORACLE_MISPLACED"
        return "FIT_L2" if src not in ("D11", "D16") else "VALIDATION_ONLY"
    if str(profile) in ("L045", "MIX-0.45", "MIX"):
        return "FIT_L045"
    if str(profile) == "L055":
        return "FIT_L055"
    if src in ("D11", "D16"):
        return "VALIDATION_ONLY"
    return "DESCRIPTIVE_ONLY"


def assert_no_banned_seeds(rows, *, seed_keys=("graph_seed", "block_seed")):
    """Fail-closed gate: any banned D16 seed in fit/DE inputs → hard FAIL."""
    hits = []
    for i, row in enumerate(rows):
        for key in seed_keys:
            if key in row and row[key] not in (None, ""):
                try:
                    s = int(row[key])
                except (TypeError, ValueError):
                    continue
                if s in BANNED_SEEDS:
                    hits.append((i, key, s))
    if hits:
        raise ValueError("banned D16 seed contact (fail-closed): %r" % (hits[:8],))
    return True


def _looks_like_fake(row):
    try:
        wall = float(row.get("wall_s", math.inf))
    except (TypeError, ValueError):
        wall = math.inf
    try:
        iters = int(row.get("iterations", -1))
    except (TypeError, ValueError):
        iters = -1
    return wall <= FAKE_WALL_MAX_S and iters == FAKE_ITERS


def refuse_fake_scratch(rows):
    """Refuse any row sourced from the d16_align fake scratch root.

    The scratch carries real D16 identities with FAKE outcomes (fake-proof:
    wall ~1e-5 s, iters 1); it must never enter fitting, DE tuning,
    verification globs, or prediction.
    """
    bad = [i for i, row in enumerate(rows)
           if FAKE_SCRATCH_ROOT.rstrip("/") in
           str(row.get("source_path", "")).replace("\\", "/")]
    if bad:
        raise ValueError(
            "fake-scratch contact at rows %r (source under %s; fake "
            "signature: wall_s<=%g and iterations==%d; outcomes never read)"
            % (bad[:8], FAKE_SCRATCH_ROOT, FAKE_WALL_MAX_S, FAKE_ITERS))
    return True


def assert_fit_eligible(row):
    """Eligibility isolation for one finite-data row (raises on exclusion)."""
    cls = classify_observation(source=row.get("source", ""),
                               layer=row.get("layer", ""),
                               profile=row.get("profile", ""),
                               oracle=bool(row.get("oracle", False)),
                               joint=bool(row.get("joint", False)))
    if cls in ("EXCLUDED_APP_JOINT", "EXCLUDED_ORACLE_MISPLACED"):
        raise ValueError("row excluded from single-layer fit: %s (%r)"
                         % (cls, row))
    if cls not in ("FIT_L045", "FIT_L055", "FIT_L2"):
        raise ValueError("row not FIT class: %s (%r)" % (cls, row))
    assert_no_banned_seeds([row])
    refuse_fake_scratch([row])
    if str(row.get("source", "")) == "D16":
        raise ValueError("D16 rows are validation-only (held out)")
    return cls


def assert_d16_root_absent(root=None):
    """Prove the D16 official root absent (fail if it exists)."""
    path = Path(root) if root is not None \
        else _repo_root() / D16_OFFICIAL_ROOT
    if path.exists():
        raise FileExistsError("D16 root exists — holdout violated: %s" % path)
    return path


def blank_prediction(profile, m):
    """Immutable D16 prediction schema with BLANK outcome fields."""
    key = str(profile)
    layer = PROFILE_LAYER.get(key, "L2")
    if (key, int(m)) not in [(p, mm) for p, mm, _ in D16_CELLS]:
        raise KeyError("unknown D16 arm %r" % ((profile, m),))
    delta = next(dd for p, mm, dd in D16_CELLS if p == key and mm == int(m))
    return {
        "schema": "d16_holdout_prediction_v1",
        "profile": key, "n": N_REF, "m": int(m), "delta": delta,
        "delta_DE": {"value": "$PRED", "source_de_root": "$PRED",
                     "flags": "$PRED"},
        "model": {"link": "probit", "alpha": "$PRED", "beta": "$PRED",
                  "alpha_ci": "$PRED", "beta_ci_or_fixed": "$PRED"},
        "prediction": {"p_success_interval_95": "$PRED",
                       "expected_graph_dispersion": "$PRED",
                       "n_graphs": 4, "trials_per_graph": 8},
        "falsification": {
            "rule": "pool outside 95% band -> FALSIFIED; inside -> "
                    "NOT_FALSIFIED; engineering_violation -> INCONCLUSIVE; "
                    "per-graph range descriptive"},
        "outcome": {"pool": "BLANK", "per_graph": "BLANK", "exact": "BLANK",
                    "syndrome": "BLANK", "undetected": "BLANK",
                    "terminal": "BLANK"},
        "gate": {"fail_if_d16_root_exists": True,
                 "predictions_frozen_before_run": True},
        "layer": layer,
    }


def write_predictions(out_dir, predictions):
    """Persist blank D16 predictions BEFORE any D16 execution.

    Fails if the D16 root exists (prediction freeze comes first, always).
    Creates nothing outside ``out_dir``.
    """
    assert_d16_root_absent()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    names = []
    for pred in predictions:
        if pred.get("schema") != "d16_holdout_prediction_v1":
            raise ValueError("not a D16 holdout prediction record")
        for field in ("pool", "per_graph", "exact", "syndrome",
                      "undetected", "terminal"):
            if pred.get("outcome", {}).get(field) != "BLANK":
                raise ValueError("prediction outcome not blank (freeze "
                                 "before run): %r" % (field,))
        name = "d16_prediction_%s_m%d.json" % (pred["profile"], pred["m"])
        with open(out / name, "w", encoding="utf-8") as fh:
            json.dump(pred, fh, indent=2, sort_keys=True)
            fh.write("\n")
        names.append(name)
    return sorted(names)


def residual_record(**fields):
    """L4 residual-diagnostic record skeleton (post-prediction only)."""
    rec = {k: fields.get(k) for k in RESIDUAL_FIELDS}
    rec["descriptive_only"] = True
    return rec


def assert_no_residual_covariates(fit_inputs):
    """Residuals explain deviations; they never enter the backoff term."""
    bad = [k for k in RESIDUAL_FIELDS
           if any(k in row for row in fit_inputs)]
    if bad:
        raise ValueError("residual covariates must not enter the fit: %r"
                         % (bad,))
    return True


# --------------------------------------------------------------------------- #
# D02 audit artifact (compact CSV/JSON inventory + report; read-only)
# --------------------------------------------------------------------------- #
#: (fid, root, n, layer, profile, m, graphs, blocks, exact, syndrome,
#:  undetected, klass, note). m=None rows are non-fit summaries.
AUDIT_SOURCE_ROWS = (
    ("F1", "D10-A1", 64, "L1", "MIX-0.45", 59, 3, 8, 20, 20, 0, "FIT_L045", ""),
    ("F2", "D10-A1", 64, "L1", "DV3", 59, 3, 8, 1, 1, 0, "DESCRIPTIVE_ONLY",
     "non-D17 profile"),
    ("F3", "D10-A1", 128, "L1", "MIX-0.45", 118, 3, 8, 10, 10, 0, "FIT_L045", ""),
    ("F4", "D10-A1", 128, "L1", "DV3", 118, 3, 8, 0, 0, 0, "DESCRIPTIVE_ONLY",
     "non-D17 profile"),
    ("F5", "D10-R3", 128, "L1", "MIX-0.45", 118, 6, 12, 23, 23, 0, "FIT_L045",
     "PROVISIONAL_D02_ROW_CONFIRM"),
    ("F6", "D10-R3", 128, "L1", "DV3", 118, 6, 12, 0, 0, 0, "DESCRIPTIVE_ONLY",
     "non-D17 profile"),
    ("F7", "D10-R3", 256, "L1", "MIX-0.45", 236, 6, 12, 29, 29, 0, "FIT_L045",
     "PROVISIONAL_D02_ROW_CONFIRM"),
    ("F8", "D10-R3", 256, "L1", "DV3", 236, 6, 12, 0, 0, 0, "DESCRIPTIVE_ONLY",
     "non-D17 profile"),
    ("F9", "D11", None, "L1", "REPLAY", None, None, None, None, None, None,
     "VALIDATION_ONLY", "R3 duplicate; no double count"),
    ("F10", "D11", None, "L1/L2", "APP/JOINT+ORACLE", None, None, None, None,
     None, None, "EXCLUDED_OR_VALIDATION",
     "APP/joint EXCLUDED from fit; oracle validation-only (D02 audit)"),
    ("F11a", "D12", 128, "L1", "L045", 118, 6, 12, 26, 26, 0, "FIT_L045",
     "D02 join-key check"),
    ("F11b", "D12", 128, "L1", "L050", 118, 6, 12, 39, 39, 0, "DESCRIPTIVE_ONLY",
     "non-D17 profile"),
    ("F11c", "D12", 128, "L1", "L055", 118, 6, 12, 42, 42, 0, "FIT_L055",
     "D02 join-key check"),
    ("F12a", "D12", 256, "L1", "L045", 236, 6, 12, 33, 33, 0, "FIT_L045",
     "D02 join-key check"),
    ("F12b", "D12", 256, "L1", "L050", 236, 6, 12, 35, 35, 0, "DESCRIPTIVE_ONLY",
     "non-D17 profile"),
    ("F12c", "D12", 256, "L1", "L055", 236, 6, 12, 46, 46, 0, "FIT_L055",
     "D02 join-key check"),
    ("F13", "D13", None, "L1", "L055-LADDER", None, None, None, None, None,
     None, "DESCRIPTIVE_ONLY", "varied decoder"),
    ("F14a", "D14N", 128, "L1", "L045", 110, 6, 12, 3, 3, 0, "FIT_L045",
     "leave-one-root-out sensitivity at D02"),
    ("F14b", "D14N", 128, "L1", "L055", 110, 6, 12, 7, 7, 0, "FIT_L055",
     "leave-one-root-out sensitivity at D02"),
    ("F15", "D14N", 128, "L2", "L2-APP", 104, 6, 12, 7, 7, 0,
     "EXCLUDED_APP_JOINT", "APP/joint excluded"),
    ("F16", "D14N", 128, "L2", "L2-ORACLE", 104, 6, 12, 63, 63, 0, "FIT_L2",
     "leave-one-root-out sensitivity at D02"),
    ("F17a", "D15", 128, "L1", "L045", 110, 4, 8, 0, 0, 0, "FIT_L045", ""),
    ("F17b", "D15", 128, "L1", "L045", 114, 4, 8, 6, 6, 0, "FIT_L045", ""),
    ("F17c", "D15", 128, "L1", "L045", 118, 4, 8, 19, 19, 0, "FIT_L045", ""),
    ("F18a", "D15", 128, "L1", "L055", 110, 4, 8, 1, 1, 0, "FIT_L055", ""),
    ("F18b", "D15", 128, "L1", "L055", 114, 4, 8, 13, 13, 0, "FIT_L055", ""),
    ("F18c", "D15", 128, "L1", "L055", 118, 4, 8, 22, 22, 0, "FIT_L055", ""),
    ("F19a", "D15", 128, "L2", "L2-ORACLE", 83, 4, 8, 0, 0, 0, "FIT_L2", ""),
    ("F19b", "D15", 128, "L2", "L2-ORACLE", 86, 4, 8, 0, 0, 0, "FIT_L2", ""),
    ("F19c", "D15", 128, "L2", "L2-ORACLE", 89, 4, 8, 0, 0, 0, "FIT_L2", ""),
    ("H1", "D16", 128, "L1", "L045", 125, 4, 8, None, None, None,
     "VALIDATION_ONLY", "held out; prediction frozen before run"),
    ("H2", "D16", 128, "L1", "L055", 125, 4, 8, None, None, None,
     "VALIDATION_ONLY", "held out; prediction frozen before run"),
    ("H3", "D16", 128, "L2", "L2-ORACLE", 94, 4, 8, None, None, None,
     "VALIDATION_ONLY", "held out; prediction frozen before run"),
)

AUDIT_COLUMNS = ("fid", "root", "n", "layer", "profile", "m",
                 "d_bits_per_sym", "delta", "graphs", "blocks", "trials",
                 "exact", "syndrome_ok", "undetected", "class", "note")


def audit_rows():
    """F-table with d/delta mechanically recomputed from the frozen H."""
    rows = []
    for fid, root, n, layer, profile, m, g, b, y, s, u, klass, note in \
            AUDIT_SOURCE_ROWS:
        if m is None:
            d = delta = trials = ""
        else:
            d = disclosed_bits(m) / float(n)
            delta = d - _h_of_layer(layer)
            trials = int(g) * int(b)
            d = round(d, 5)
            delta = round(delta, 5)
        rows.append({"fid": fid, "root": root, "n": n, "layer": layer,
                     "profile": profile, "m": m, "d_bits_per_sym": d,
                     "delta": delta, "graphs": g, "blocks": b,
                     "trials": trials, "exact": y, "syndrome_ok": s,
                     "undetected": u, "class": klass, "note": note})
    return rows


def build_audit_artifacts(out_dir):
    """Write the compact CSV/JSON inventory + report (no predecessor writes).

    R3/D11 row confirmations and leave-one-root-out sensitivity stay
    PROVISIONAL here (packet-exact future D02 authorization); the builder
    itself only reads the frozen table and recomputes d/delta.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = audit_rows()
    with open(out / "d17_audit_inventory.csv", "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(AUDIT_COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow({c: ("" if row[c] is None else row[c])
                             for c in AUDIT_COLUMNS})
    payload = {
        "schema": "v72p2d17_audit_inventory_v1",
        "change_id": CHANGE_ID,
        "channel": {"H_L1": H_L1, "H_L2": H_L2, "load_l1_bits": LOAD_L1,
                    "load_l2_bits": LOAD_L2,
                    "lambda_star": LAMBDA_STAR,
                    "prior_floor": PRIOR_FLOOR, "prior_renorm": False,
                    "axes": CHANNEL_AXES, "axis_rule": CHANNEL_AXIS_RULE,
                    "estimator": PRIOR_ESTIMATOR, "table": PRIOR_TABLE},
        "decoder": {"q": Q, "poly": POLY, "max_iter": DECODER_MAX_ITER,
                    "damping": DAMPING_ALPHA, "floor": DECODER_FLOOR,
                    "floor_renorm": True, "l1_input": L1_INPUT_LINE,
                    "l2_oracle": L2_ORACLE_LINE,
                    "model_f_root": MODEL_F_INPUT_ROOT},
        "de_transfer": {
            "reuse": ["V26 MC-DE kernel", "D9 semantic adapter",
                      "D9 degree-realization rule",
                      "D9 8-seed stability methodology"],
            "no_numeric_transfer": ["D9 thresholds/verdicts",
                                    "D8 outcomes", "V25/V26/V27 numbers"],
            "reason": "different rate base (CE vs generator-H, n128-m)"},
        "join_keys": ["model_f_root", "candidate-chain estimator",
                      "decoder contract"],
        "provisional": ["D10-R3/D11 row confirmation",
                        "D12 CE-f1.2 join-key check",
                        "D14N-vs-D15 leave-one-root-out sensitivity"],
        "holdout": {"d16_root": D16_OFFICIAL_ROOT,
                    "d16_root_absent": not
                    (_repo_root() / D16_OFFICIAL_ROOT).exists(),
                    "banned_graph_seeds": list(D16_GRAPH_SEEDS),
                    "banned_block_seeds": list(D16_BLOCK_SEEDS),
                    "fake_scratch": FAKE_SCRATCH_ROOT},
        "rows": rows,
    }
    with open(out / "d17_audit_inventory.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    fit = [r for r in rows if r["class"].startswith("FIT_")]
    lines = [
        "D17 audit inventory (readiness; read-only, no predecessor writes)",
        "change: %s" % CHANGE_ID,
        "channel: H_L1=%.15g H_L2=%.15g (candidate generator; floor "
        "max(p,1e-300) pre-log2, no renorm)" % (H_L1, H_L2),
        "decoder: GF32/poly37 cold 90/1.0, floor 1e-15 + renorm",
        "rows: %d total, %d FIT-class cells; D16 holdout: 3 arms BLANK" % (
            len(rows), len(fit)),
        "provisional (packet-exact future D02): R3/D11 row confirmation, "
        "D12 join-key check, leave-one-root-out sensitivity",
        "claim ceiling: %s" % CLAIM_CEILING,
    ]
    with open(out / "d17_audit_report.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return ["d17_audit_inventory.csv", "d17_audit_inventory.json",
            "d17_audit_report.txt"]


# --------------------------------------------------------------------------- #
# Plan description (PROFILE_ONLY content; no kernel, no root, no decoder)
# --------------------------------------------------------------------------- #
def describe_plan():
    """Pure plan/grid arithmetic + absence proofs for PROFILE_ONLY."""
    plan = build_de_plan()
    future = (_repo_root() / FUTURE_ROOT)
    cells = []
    for profile in DE_PROFILES:
        for m in DE_GRID_M[profile]:
            cell = degree_cell(profile, m)
            cells.append({"profile": profile, "m": int(m),
                          "rate": cell["rate"], "delta": cell["delta"],
                          "check_counts": cell["check_counts"],
                          "E": cell["E"]})
    return {
        "change_id": CHANGE_ID,
        "grid_points": len(cells),
        "planned_de_calls": len(plan),
        "seeds": list(DE_SEEDS),
        "populations": list(DE_POPULATIONS),
        "max_iter": DE_MAX_ITER, "entropy_tol_bits": DE_ENTROPY_TOL_BITS,
        "streak": DE_STREAK,
        "convergence_rule": "S_pop=#{H60<1e-4} over 8 seeds; delta_DE = "
                            "bracket midpoint at pop16000 (frozen edge flags)",
        "cells": cells,
        "budgets": {"de_calls": DE_CALL_CEILING, "setup": SETUP_CEILING,
                    "wall_s": WALL_BUDGET_S, "per_call_s": PER_CALL_BUDGET_S,
                    "rss_bytes": RSS_BUDGET_BYTES, "processes": 1},
        "future_root": str(future),
        "future_root_absent": not future.exists(),
        "frozen_command": FROZEN_COMMAND,
        "authorization": AUTHORIZATION,
        "de_calls": 0,
        "decoder_calls": 0,
    }


# --------------------------------------------------------------------------- #
# Production binder (authorized path only; lazy; signature-checked, zero calls)
# --------------------------------------------------------------------------- #
def _require_signature(fn, required, name):
    if not callable(fn):
        raise TypeError("production adapter %r is not callable" % (name,))
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError) as exc:
        raise TypeError("production adapter %r has no valid signature: %s"
                        % (name, exc)) from exc
    missing = [p for p in required if p not in params]
    if missing:
        raise TypeError("production adapter %r signature %s lacks %s"
                        % (name, sorted(params), missing))
    return fn


def bind_production_de():
    """Narrow binder: accepted V26 kernel + D9 adapter only (authorized path).

    Resolving never invokes: DE calls and Model-F content load happen only
    inside the authorized orchestrator after plan validation.
    """
    d9 = _load_sibling("v72p2d9_de_decoder_calibration")
    d5 = _load_sibling("v72p2d5_gf32_rate_mother")
    make_rho = _require_signature(
        d9.make_rho, ["rate", "lambda_edge"], "make_rho")
    de_call = _require_signature(
        d9.run_de_call,
        ["lambda_edge", "rho_edge", "channel_sampler", "seed", "n_samples"],
        "run_de_call")
    load_channel = _require_signature(
        d9.load_l1_channel, ["model_f_root"], "load_channel")
    build_sampler = _require_signature(
        d9.build_l1_sampler, ["pb", "p_f", "p1"], "build_sampler")
    conditionalize = _require_signature(
        d5.conditionalize_f_to_p2, ["p_f"], "conditionalize")
    oracle_mixer = _require_signature(
        d5.oracle_l2_prior, ["p2", "bob_symbols", "u1_true"], "oracle_mixer")
    return {"make_rho": make_rho, "de_call": de_call,
            "load_channel": load_channel, "build_sampler": build_sampler,
            "conditionalize": conditionalize, "oracle_mixer": oracle_mixer}


def probe_fresh_root(out_root):
    """Fresh-root probe via the accepted R2 refusal (lazy; creates nothing)."""
    r2 = _load_sibling("v72p2d10_mixed_degree_l1")
    return r2.refuse_out_root(out_root)


# --------------------------------------------------------------------------- #
# Batch orchestrator (plan-first; injected fakes on the test path)
# --------------------------------------------------------------------------- #
_LAMBDA_EDGE = {"L045": {2: 0.45, 3: 0.55}, "L055": {2: 0.55, 3: 0.45},
                "L2": {3: 1.0}}


def run_de_batch(out_root, model_f_root, *, channel=None, de_call=None,
                 rho_fn=None, now_fn=None, rss_fn=None):
    """Execute the frozen 240-call DE matrix; return the bundle (no writes).

    ``channel``/``de_call``/``rho_fn`` must be explicitly injected (fakes on
    the test path); ``None`` production-binds inside, AFTER plan validation
    and the fresh-root probe. Creates no files or directories.
    """
    plan = build_de_plan()
    if len(plan) != DE_CALL_CEILING:
        raise ValueError("plan has %d calls, frozen %d"
                         % (len(plan), DE_CALL_CEILING))
    index = expected_call_index(plan)
    if sorted(index.values()) != list(range(DE_CALL_CEILING)):
        raise ValueError("plan call_idx not 0..239 without skips")
    resolved = probe_fresh_root(out_root)  # probe only; creates nothing
    bound = bind_production_de() if (channel is None or de_call is None
                                     or rho_fn is None) else None
    if bound is not None:
        channel = channel or bound["load_channel"](model_f_root)
        de_call = de_call or bound["de_call"]
        rho_fn = rho_fn or (lambda profile, m:
                            bound["make_rho"](rate_of(m),
                                              dict(_LAMBDA_EDGE[profile])))
    if channel is None or de_call is None or rho_fn is None:
        raise ValueError("channel/de_call/rho_fn must be explicitly injected "
                         "(V26 kernel and Model-F content are never loaded "
                         "without them)")
    now = now_fn or time.monotonic
    rss_fn = rss_fn or (lambda: 0)
    t0 = float(now())
    log_lines = []

    def log(message):
        line = "[%s] %s" % (time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime()), message)
        log_lines.append(line)

    rhos = {}
    for profile in DE_PROFILES:
        for m in DE_GRID_M[profile]:
            rhos[(profile, int(m))] = {int(k): float(v) for k, v in
                                       dict(rho_fn(profile, int(m))).items()}
    log("plan validated calls=%d; rho identities bound per cell" % len(plan))
    setup_calls = SETUP_UNITS
    records, traces = [], []
    engineering_reason = ""
    for entry in plan:
        start = float(now())
        try:
            result = de_call(dict(_LAMBDA_EDGE[entry["profile"]]),
                             dict(rhos[(entry["profile"], entry["m"])]),
                             channel, int(entry["seed"]),
                             int(entry["population"]))
            trace = [float(x) for x in result["entropy_trace_bits"]]
            final = trace[-1]
            converged = bool(final < DE_CONVERGENCE_H)
            crash, error = False, ""
        except Exception as exc:  # failure retention, no retry, stop
            engineering_reason = "DE_CALL_FAILED@%d: %s: %s" % (
                entry["call_idx"], type(exc).__name__, exc)
            log(engineering_reason)
            break
        wall = float(now()) - start
        records.append({
            "call_idx": entry["call_idx"], "profile": entry["profile"],
            "layer": entry["layer"], "m": entry["m"], "rate": entry["rate"],
            "delta": entry["delta"], "population": entry["population"],
            "seed": entry["seed"], "E": entry["E"],
            "rho": json.dumps(rhos[(entry["profile"], entry["m"])],
                              sort_keys=True),
            "converged": converged, "final_entropy_bits": final,
            "wall_s": wall, "crash": crash, "error": error})
        traces.append({
            "profile": entry["profile"], "m": entry["m"],
            "population": entry["population"], "seed": entry["seed"],
            "entropy_trace_bits": json.dumps(trace),
            "channel_entropy_trace_bits": json.dumps(
                [float(x) for x in result.get("channel_entropy_trace_bits",
                                              [5.0] * len(trace))])})
        if float(now()) - t0 > WALL_BUDGET_S:
            engineering_reason = "WALL_BUDGET_EXCEEDED@%d" % entry["call_idx"]
            log(engineering_reason)
            break
    s_table = {}
    for profile in DE_PROFILES:
        for m in DE_GRID_M[profile]:
            for pop in DE_POPULATIONS:
                got = [r for r in records if r["profile"] == profile
                       and r["m"] == int(m) and r["population"] == pop]
                s_table["%s:m%d:p%d" % (profile, int(m), pop)] = {
                    "S": sum(1 for r in got if r["converged"]),
                    "calls": len(got)}
    brackets = {}
    if len(records) == DE_CALL_CEILING and not engineering_reason:
        for profile in DE_PROFILES:
            s16 = {m: s_table["%s:m%d:p16000" % (profile, m)]["S"]
                   for m in DE_GRID_M[profile]}
            s4 = {m: s_table["%s:m%d:p4000" % (profile, m)]["S"]
                  for m in DE_GRID_M[profile]}
            brackets[profile] = bracket_delta_de(profile, s16, s4)
        terminal = "DE_COMPLETE"
    else:
        terminal = "DE_ENGINEERING_BLOCKED"
        if not engineering_reason:
            engineering_reason = "PARTIAL_PLAN"
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn())
    violations = []
    if wall_s > WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if peak_rss >= RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")
    manifest = {
        "schema": "v72p2d17_de_batch_manifest_v1",
        "change_id": CHANGE_ID, "cycle": CYCLE_ID,
        "claim_ceiling": CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "model_f_root": str(model_f_root), "out_root": str(resolved),
        "grid": {p: list(DE_GRID_M[p]) for p in DE_PROFILES},
        "seeds": list(DE_SEEDS), "populations": list(DE_POPULATIONS),
        "de_params": {"max_iter": DE_MAX_ITER,
                      "entropy_tol_bits": DE_ENTROPY_TOL_BITS,
                      "streak": DE_STREAK},
        "budgets": {"de_calls": DE_CALL_CEILING, "setup": SETUP_CEILING,
                    "wall_s": WALL_BUDGET_S, "per_call_s": PER_CALL_BUDGET_S,
                    "rss_bytes": RSS_BUDGET_BYTES, "processes": 1,
                    "retry": False, "resume": False, "seed_search": False,
                    "adaptive": False},
        "setup_calls": setup_calls,
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": AUTHORIZATION,
    }
    summary = {
        "schema": "v72p2d17_de_batch_summary_v1",
        "change_id": CHANGE_ID, "terminal": terminal,
        "engineering_reason": engineering_reason,
        "s_table": s_table, "brackets": brackets,
        "scientific_calls": len(records), "planned_calls": len(plan),
        "setup_calls": setup_calls, "wall_s": wall_s,
        "peak_rss_bytes": peak_rss, "budget_violations": violations,
        "model_f_root": str(model_f_root), "out_root": str(resolved),
    }
    log("terminal=%s calls=%d wall_s=%.3f" % (terminal, len(records), wall_s))
    return {"resolved": resolved, "manifest": manifest, "plan": plan,
            "records": records, "traces": traces, "summary": summary,
            "log_lines": log_lines}


DE_PLAN_COLUMNS = ("call_idx", "profile", "layer", "m", "rate", "delta",
                   "E", "var_counts", "check_counts", "population", "seed")
DE_RECORD_COLUMNS = ("call_idx", "profile", "layer", "m", "rate", "delta",
                     "population", "seed", "E", "rho", "converged",
                     "final_entropy_bits", "wall_s", "crash", "error")
DE_TRACE_COLUMNS = ("profile", "m", "population", "seed",
                    "entropy_trace_bits", "channel_entropy_trace_bits")


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _write_csv(path, columns, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            out = {}
            for col in columns:
                value = row.get(col, "")
                out[col] = json.dumps(value, sort_keys=True) \
                    if isinstance(value, dict) else value
            writer.writerow(out)


def _read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_de_root(bundle):
    """Persist one orchestrator bundle to its fresh root (never overwrite)."""
    resolved = bundle["resolved"]
    resolved.mkdir(parents=True)
    _write_json(resolved / "manifest.json", bundle["manifest"])
    _write_csv(resolved / "de_plan.csv", DE_PLAN_COLUMNS, bundle["plan"])
    _write_csv(resolved / "de_records.csv", DE_RECORD_COLUMNS,
               bundle["records"])
    _write_csv(resolved / "de_traces.csv", DE_TRACE_COLUMNS, bundle["traces"])
    _write_json(resolved / "summary.json", bundle["summary"])
    with open(resolved / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("".join(line + "\n" for line in bundle["log_lines"]))
    return bundle["summary"]


def verify_de_root(out_root, *, rho_fn=None):
    """Read-only recomputation of a completed DE root (zero DE calls).

    Recomputes plan/grid/identities, S counts from traces, and the bracket
    rule. ``rho_fn`` (injected fakes in tests) enables exact rho-identity
    recomputation; without it, rho is checked present-and-finite only, so
    the CLI verifier never loads the V26 kernel.
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
    manifest = json.loads((root / "manifest.json").read_text("utf-8"))
    summary = json.loads((root / "summary.json").read_text("utf-8"))
    plan_rows = _read_csv(root / "de_plan.csv")
    record_rows = _read_csv(root / "de_records.csv")
    trace_rows = _read_csv(root / "de_traces.csv")
    if manifest.get("command") != FROZEN_COMMAND:
        violations.append("manifest command != frozen command")
    if manifest.get("change_id") != CHANGE_ID:
        violations.append("manifest change_id mismatch")

    plan = build_de_plan()
    if len(plan_rows) != len(plan):
        violations.append("stored plan rows %d != frozen %d"
                          % (len(plan_rows), len(plan)))
    for stored, entry in zip(plan_rows, plan):
        for key in ("call_idx", "profile", "layer", "m", "population",
                    "seed"):
            if str(stored[key]) != str(entry[key]):
                violations.append("plan row %s %s %r != frozen %r"
                                  % (stored.get("call_idx"), key,
                                     stored.get(key), entry[key]))
        for key in ("rate", "delta"):
            if abs(float(stored[key]) - float(entry[key])) > 1e-12:
                violations.append("plan row %s %s drift" % (
                    stored.get("call_idx"), key))
        if int(stored["E"]) != int(entry["E"]):
            violations.append("plan row %s E drift" % stored.get("call_idx"))

    if len(record_rows) != len(plan):
        violations.append("stored calls %d != frozen plan %d (zero-skip)"
                          % (len(record_rows), len(plan)))
    s_check: dict[str, dict[int, int]] = {}
    for index, row in enumerate(record_rows):
        if int(row["call_idx"]) != index:
            violations.append("record %d call_idx drift" % index)
        trace = [t for t in trace_rows
                 if t["profile"] == row["profile"] and int(t["m"]) == int(
                     row["m"]) and int(t["population"]) == int(
                     row["population"]) and int(t["seed"]) == int(row["seed"])]
        if len(trace) != 1:
            violations.append("record %d trace join != 1" % index)
            continue
        entropy = [float(x) for x in json.loads(
            trace[0]["entropy_trace_bits"])]
        if abs(entropy[-1] - float(row["final_entropy_bits"])) > 1e-12:
            violations.append("record %d final entropy != trace tail" % index)
        expect = entropy[-1] < DE_CONVERGENCE_H
        if expect != (str(row["converged"]).strip().lower() in
                      ("1", "true", "yes")):
            violations.append("record %d S-count bit != trace" % index)
        key = (row["profile"], int(row["population"]))
        s_check.setdefault(key, {})
        if expect:
            s_check[key][int(row["m"])] = s_check[key].get(int(row["m"]),
                                                           0) + 1
        if float(row["wall_s"]) < 0.0 \
                or float(row["wall_s"]) > PER_CALL_BUDGET_S:
            violations.append("record %d per-call wall out of budget" % index)
        if rho_fn is not None:
            want = {int(k): float(v) for k, v in
                    dict(rho_fn(row["profile"], int(row["m"]))).items()}
            have = {int(k): float(v) for k, v in
                    json.loads(row["rho"]).items()}
            if set(have) != set(want) or any(
                    abs(have[k] - want[k]) > 1e-12 for k in want):
                violations.append("record %d rho != recomputed" % index)
        else:
            try:
                have = {int(k): float(v) for k, v in
                        json.loads(row["rho"]).items()}
            except (TypeError, ValueError):
                violations.append("record %d rho not present/finite" % index)
                have = {}
            if not have or not all(math.isfinite(v) for v in have.values()):
                violations.append("record %d rho not present/finite" % index)
    stored_s = summary.get("s_table", {})
    for profile in DE_PROFILES:
        for m in DE_GRID_M[profile]:
            for pop in DE_POPULATIONS:
                key = "%s:m%d:p%d" % (profile, int(m), pop)
                got = s_check.get((profile, pop), {}).get(int(m), 0)
                if stored_s.get(key, {}).get("S") != got:
                    violations.append("S table %s stored != recomputed" % key)
    if summary.get("engineering_reason"):
        violations.append("engineering-blocked root (fail-closed)")
    if summary.get("terminal") != "DE_COMPLETE":
        violations.append("terminal != DE_COMPLETE")
    if int(summary.get("scientific_calls", -1)) != len(record_rows):
        violations.append("summary calls != stored records")
    if int(summary.get("setup_calls", -1)) != SETUP_UNITS:
        violations.append("setup calls != frozen %d" % SETUP_UNITS)
    if float(summary.get("wall_s", -1.0)) > WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if int(summary.get("peak_rss_bytes", -1)) >= RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")
    print("VERIFY checked_calls=%d violations=%d"
          % (len(record_rows), len(violations)))
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    ok = not violations
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return ok


# --------------------------------------------------------------------------- #
# Read-only identity checks against live predecessors (tests/review only)
# --------------------------------------------------------------------------- #
def verify_channel_identity():
    """Prove the frozen channel/decoder constants against live modules."""
    d15 = _load_sibling("v72p2d15_margin_curve")
    d5 = _load_sibling("v72p2d5_gf32_rate_mother")
    r2 = _load_sibling("v72p2d10_mixed_degree_l1")
    checks = {
        "H_L1": d15.H_L1 == H_L1,
        "H_L2": d15.H_L2 == H_L2,
        "LOAD_L1": d15.LOAD_L1 == LOAD_L1,
        "LOAD_L2": d15.LOAD_L2 == LOAD_L2,
        "PRIOR_CHAIN": d15.PRIOR_CHAIN == "candidate_concentration_backoff",
        "LAMBDA_STAR": d5.LAMBDA_STAR == LAMBDA_STAR,
        "DECODER_FLOOR": d5.DECODER_FLOOR == DECODER_FLOOR,
        "Q": r2.Q == Q,
        "POLY": r2.POLY == POLY,
        "DECODER_MAX_ITER": r2.DECODER_MAX_ITER == DECODER_MAX_ITER,
        "DAMPING_ALPHA": r2.DAMPING_ALPHA == DAMPING_ALPHA,
        "MODEL_F_ROOT": r2.MODEL_F_INPUT_ROOT == MODEL_F_INPUT_ROOT,
    }
    return {"passed": all(checks.values()), "checks": checks}


def verify_seed_disjointness():
    """Prove DE seeds disjoint from every prior + the banned D16 sets."""
    r2 = _load_sibling("v72p2d10_mixed_degree_l1")
    r3 = _load_sibling("v72p2d10_r3_fresh_scaling")
    d11 = _load_sibling("v72p2d11_forward_app")
    d12 = _load_sibling("v72p2d12_finite_l1_degree")
    d14n = _load_sibling("v72p2d14n_calibrated_discriminator")
    d15 = _load_sibling("v72p2d15_margin_curve")
    d16 = _load_sibling("v72p2d16_matched_backoff")
    prior = (
        {s for seeds in r2.GRAPH_SEEDS.values() for s in seeds}
        | {s for seeds in r2.BLOCK_SEEDS.values() for s in seeds}
        | {s for seeds in r3.GRAPH_SEEDS.values() for s in seeds}
        | {s for seeds in r3.BLOCK_SEEDS.values() for s in seeds}
        | {s for seeds in d11.L1_GRAPH_SEEDS.values() for s in seeds}
        | {s for seeds in d11.L1_BLOCK_SEEDS.values() for s in seeds}
        | {s for seeds in d11.L2_GRAPH_SEEDS.values() for s in seeds}
        | {s for seeds in d12.GRAPH_SEEDS.values() for s in seeds}
        | {s for seeds in d12.BLOCK_SEEDS.values() for s in seeds}
        | set(d14n.L1_GRAPH_SEEDS) | set(d14n.L2_GRAPH_SEEDS)
        | set(d14n.BLOCK_SEEDS)
        | {s for seeds in d15.GRAPH_SEEDS.values() for s in seeds}
        | set(d15.BLOCK_SEEDS)
        | {s for seeds in d16.GRAPH_SEEDS.values() for s in seeds}
        | set(d16.BLOCK_SEEDS))
    de = set(DE_SEEDS)
    d16_all = ({s for seeds in d16.GRAPH_SEEDS.values() for s in seeds}
               | set(d16.BLOCK_SEEDS))
    ok = de.isdisjoint(prior) and de.isdisjoint(d16_all) \
        and set(D16_GRAPH_SEEDS) == {s for seeds in d16.GRAPH_SEEDS.values()
                                     for s in seeds} \
        and set(D16_BLOCK_SEEDS) == set(d16.BLOCK_SEEDS) \
        and BANNED_SEEDS == d16_all and len(de) == 8
    return {"passed": bool(ok), "de_seeds": sorted(de),
            "prior_count": len(prior),
            "de_hits_prior": sorted(de & prior),
            "de_hits_d16": sorted(de & d16_all)}
