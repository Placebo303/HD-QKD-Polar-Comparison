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
    "build_l2_oracle_sampler", "build_production_channels",
    "A3_DE_ROOT", "A3_FINITE_ROOTS", "A3_FIT_ROOT", "A3_FROZEN_COMMAND",
    "A3_DELTA_DE", "A3_WALL_BUDGET_S",
    "a3_recompute_brackets", "a3_aggregate_finite", "a3_fit_all",
    "a3_backoffs", "a3_predictions", "a3_write_root", "a3_verify_fit_root",
    "a3_run",
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


# --------------------------------------------------------------------------- #
# R2 production channel binding + profile dispatch (R201–R203; engineering
# only — grid/seeds/kernel/rules unchanged per R204)
# --------------------------------------------------------------------------- #
#: Canonical plan profiles plus the A1-packet long labels for the same arms.
#: Unknown/mislabelled profiles fail before any scientific call.
_CHANNEL_ALIASES = {
    "L045": "L045", "L055": "L055", "L2": "L2",
    "L1_L045": "L045", "L1_L055": "L055", "L2_DV3_ORACLE": "L2",
}
_PROBE_K = 4  # tiny dispatch-probe rows (validation only, never a DE call)
_PROBE_SEED = 2026091727  # fixed fresh rng; never touches scientific streams
_JOINT_MASS_TOL = 1e-8  # same tolerance as the accepted D9 builder
_ROW_SUM_TOL = 1e-9


def _normalize_channel_profile(profile):
    try:
        return _CHANNEL_ALIASES[str(profile)]
    except KeyError:
        raise ValueError("unknown DE profile %r (fail-closed; want one of %s)"
                         % (profile, sorted(_CHANNEL_ALIASES))) from None


def _require_channel_triplet(loaded):
    """Unpack-once validation of the ``load_l1_channel`` result (R201)."""
    if not isinstance(loaded, (tuple, list)) or len(loaded) != 3:
        raise TypeError("load_l1_channel must return exact (pb, p_f, p1); "
                        "got %s" % type(loaded).__name__)
    pb, p_f, p1 = loaded
    pb = np.asarray(pb, dtype=np.float64).ravel()
    p_f = np.asarray(p_f, dtype=np.float64)
    p1 = np.asarray(p1, dtype=np.float64)
    if not (np.all(np.isfinite(pb)) and np.all(np.isfinite(p_f))
            and np.all(np.isfinite(p1))):
        raise ValueError("pb/p_f/p1 must be finite")
    if p_f.ndim != 2 or p1.ndim != 2 or p1.shape[0] != Q:
        raise ValueError("p_f must be 2-D and p1 must be (32, Bob)")
    if p_f.shape[0] % Q != 0 or p1.shape[1] != p_f.shape[1] \
            or pb.shape[0] != p_f.shape[1]:
        raise ValueError("pb/p_f/p1 shapes do not agree")
    if np.any(pb < 0.0) or not float(pb.sum()) > 0.0:
        raise ValueError("pb must be nonnegative with positive mass")
    joint = pb[None, :] * p_f
    total = float(joint.sum())
    if not math.isfinite(total) or abs(total - 1.0) > _JOINT_MASS_TOL:
        raise ValueError("pb * P_F(A|B) must be a probability table")
    return pb, p_f, p1


def _require_sampler_rows(rows, k):
    """Fail-closed (k,32) finite normalized row check (R201–R203 probes)."""
    a = np.asarray(rows, dtype=np.float64)
    if a.shape != (int(k), Q):
        raise ValueError("sampler rows must have shape (%d, 32), got %r"
                         % (int(k), a.shape))
    if not np.all(np.isfinite(a)):
        raise ValueError("sampler rows must be finite")
    if np.any(a < 0.0):
        raise ValueError("sampler rows must be nonnegative")
    if not np.all(np.abs(a.sum(axis=1) - 1.0) <= _ROW_SUM_TOL):
        raise ValueError("sampler rows must be normalized")
    return a


def build_l2_oracle_sampler(pb, p_f, p2, oracle_prior_fn):
    """True-conditioned L2 oracle sampler for the V26 consumer (R202).

    Samples ``(A,B)`` from the same ``pb[B]*p_f[A,B]`` joint as the
    accepted L1 sampler, sets ``u1=A//32``, ``u2=A%32``, obtains the prior
    EXCLUSIVELY through ``oracle_prior_fn(p2, B, u1)`` (the bound
    ``oracle_l2_prior``; the accepted D9/D5 floor-normalize convention it
    applies is reused, never reimplemented), and XOR-centers each row on
    true ``u2``. V36/V37 empirical-count samplers are forbidden (their
    source channel is not the current Model-F candidate chain) and are
    never touched here.
    """
    if not callable(oracle_prior_fn):
        raise TypeError("oracle_prior_fn must be callable")
    pb = np.asarray(pb, dtype=np.float64).ravel()
    p_f = np.asarray(p_f, dtype=np.float64)
    p2 = np.asarray(p2, dtype=np.float64)
    if not (np.all(np.isfinite(pb)) and np.all(np.isfinite(p_f))
            and np.all(np.isfinite(p2))):
        raise ValueError("pb/p_f/p2 must be finite")
    if p_f.ndim != 2 or p_f.shape[0] % Q != 0:
        raise ValueError("p_f must be 2-D with Alice dim a multiple of 32")
    n_u1 = p_f.shape[0] // Q
    n_bob = p_f.shape[1]
    if tuple(p2.shape) != (n_u1, n_bob, Q):
        raise ValueError("pb/p_f/p2 shapes do not agree "
                         "(want p2 == (A/32, Bob, 32))")
    if pb.shape[0] != n_bob:
        raise ValueError("pb/p_f/p2 shapes do not agree")
    if np.any(pb < 0.0) or not float(pb.sum()) > 0.0:
        raise ValueError("pb must be nonnegative with positive mass")
    joint = pb[None, :] * p_f
    total = float(joint.sum())
    if not math.isfinite(total) or abs(total - 1.0) > _JOINT_MASS_TOL:
        raise ValueError("pb * P_F(A|B) must be a probability table")
    flat = joint.ravel()
    if not np.all(np.isfinite(flat)):
        raise ValueError("joint table must be finite")
    _require_sampler_rows(p2.reshape(-1, Q), n_u1 * n_bob)
    idx = np.arange(Q, dtype=np.int64)

    def sampler(n, rng):
        k = int(n)
        if k <= 0:
            raise ValueError("n must be positive")
        pick = rng.choice(flat.size, size=k, p=flat)
        a = (pick // n_bob).astype(np.int64)
        b = (pick % n_bob).astype(np.int64)
        u1 = a // Q
        u2 = a % Q
        prior = _require_sampler_rows(
            np.asarray(oracle_prior_fn(p2, b, u1), dtype=np.float64), k)
        centered = prior[np.arange(k)[:, None], (idx[None, :] ^ u2[:, None])]
        out = _require_sampler_rows(centered, k)
        if not bool(np.all(out[:, 0] == prior[np.arange(k), u2])):
            raise ValueError("L2 rows not XOR-centered on true u2")
        return out

    sampler._d17_layer = "L2"  # explicit layer tag for R203 dispatch
    return sampler


def _tag_sampler(fn, layer):
    """Mark an already-centered sampler with its explicit layer (R203)."""
    if not callable(fn):
        raise TypeError("cannot tag a non-callable channel")
    def sampler(n, rng):
        return fn(n, rng)
    sampler._d17_layer = str(layer)
    return sampler


def build_production_channels(model_f_root, *, bound=None):
    """R201+R202 production build: load once, L1 once, p2 once, L2 once.

    Returns the explicit per-profile mapping ``{"L045": l1, "L055": l1,
    "L2": l2}`` holding two DISTINCT callables (one callable silently
    shared by all three profiles is forbidden). Builds only; never
    invokes a DE call.
    """
    bound = bound if bound is not None else bind_production_de()
    loaded = bound["load_channel"](model_f_root)  # exactly once
    pb, p_f, p1 = _require_channel_triplet(loaded)  # unpack once
    l1 = _tag_sampler(bound["build_sampler"](pb, p_f, p1), "L1")  # once
    p2 = np.asarray(bound["conditionalize"](p_f),  # exactly once
                    dtype=np.float64)
    if p2.ndim != 3 or p2.shape[0] != p_f.shape[0] // Q \
            or p2.shape[1] != p_f.shape[1] or p2.shape[2] != Q:
        raise ValueError("p2 must have shape (A/32, Bob, 32) matching p_f")
    if not np.all(np.isfinite(p2)):
        raise ValueError("p2 must be finite")
    l2 = build_l2_oracle_sampler(pb, p_f, p2, bound["oracle_mixer"])
    if not callable(l2):
        raise TypeError("L2 oracle builder must return a callable")
    if l1 is l2 or getattr(l1, "_d17_layer", None) != "L1" \
            or getattr(l2, "_d17_layer", None) != "L2":
        raise ValueError("production L1/L2 channels must be distinct "
                         "layer-tagged callables")
    return {"L045": l1, "L055": l1, "L2": l2}


def _resolve_profile_sampler(channels, profile):
    """R203 dispatch: frozen plan entry's profile → its sampler, every call.

    ``channels`` must be the explicit per-profile mapping (production
    :func:`build_production_channels` output or an injected fake of the
    same form); a single callable/value shared silently is forbidden.
    Unknown profiles, missing keys, non-callables, layer-tag mismatches
    (swapped/untagged), undistinct L1/L2, and probe rows that are not
    finite/normalized/(k,32) all fail BEFORE any scientific call.
    """
    canonical = _normalize_channel_profile(profile)
    if not isinstance(channels, dict):
        raise TypeError("channels must be the explicit per-profile mapping "
                        "{'L045': .., 'L055': .., 'L2': ..}; a single shared "
                        "channel is forbidden (got %s)"
                        % type(channels).__name__)
    norm = {}
    for key, value in channels.items():
        norm[_normalize_channel_profile(key)] = value
    missing = [p for p in DE_PROFILES if p not in norm]
    if missing:
        raise ValueError("channel mapping missing profiles %r (fail-closed)"
                         % (missing,))
    sampler = norm[canonical]
    if not callable(sampler):
        raise TypeError("channel sampler for %s is not callable (got %s)"
                        % (canonical, type(sampler).__name__))
    want_layer = PROFILE_LAYER[canonical]
    if getattr(sampler, "_d17_layer", None) != want_layer:
        raise ValueError("channel sampler for %s has layer tag %r, want %r "
                         "(swapped or untagged channel)"
                         % (canonical, getattr(sampler, "_d17_layer", None),
                            want_layer))
    if norm["L045"] is norm["L2"] or norm["L055"] is norm["L2"]:
        raise ValueError("L1/L2 channels must be distinct objects (a single "
                         "callable shared by all profiles is forbidden)")
    _require_sampler_rows(
        sampler(_PROBE_K, np.random.default_rng(_PROBE_SEED)), _PROBE_K)
    return sampler


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

    ``channel`` must be the explicit per-profile mapping ``{"L045": l1,
    "L055": l1, "L2": l2}`` of layer-tagged callables (fakes on the test
    path, same form); ``de_call``/``rho_fn`` must be explicitly injected
    (fakes on the test path); any ``None`` production-binds inside, AFTER
    plan validation and the fresh-root probe (a ``None`` production channel
    loads Model-F once, builds the L1 sampler once and the
    true-conditioned L2 oracle once, then dispatches per plan profile
    before every call). Creates no files or directories.
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
        if channel is None:
            # R201+R202: the A1 tuple-as-sampler path is gone; the tuple is
            # unpacked once inside, then L1/L2 callables are built once.
            channel = build_production_channels(model_f_root, bound=bound)
        if de_call is None:
            de_call = bound["de_call"]
        if rho_fn is None:
            rho_fn = (lambda profile, m:
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
            # R203: dispatch from the frozen plan entry's profile before
            # EVERY scientific call (fail-closed, pre-call).
            sampler = _resolve_profile_sampler(channel, entry["profile"])
            result = de_call(dict(_LAMBDA_EDGE[entry["profile"]]),
                             dict(rhos[(entry["profile"], entry["m"])]),
                             sampler, int(entry["seed"]),
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


# --------------------------------------------------------------------------- #
# A3 finite-length scaling fit + D16 prediction freeze (packet §§2–9,
# design §11; one-shot EXPLORE fit; zero DE/decoder/CAL/VAL calls)
# --------------------------------------------------------------------------- #
#: Frozen A3 inputs (design §11.2; order is part of the frozen command).
A3_DE_ROOT = ("workspace/d17_current_channel_asymptotic_de_r2_"
              "61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24")
A3_FINITE_ROOTS = (
    "workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34",
    "workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d",
    "workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450",
    "workspace/v72p2d14_discriminator/20260914_r1",
    "workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2",
)
A3_FIT_ROOT = ("workspace/d17_finite_scaling_fit_5b6d71c8-"
               "9e42-4e64-b1c3-73a1f20d8e95")
A3_FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d17_scaling_development.py --scaling-fit "
    "--execution-authorized --de-root %s --finite-root %s --finite-root %s "
    "--finite-root %s --finite-root %s --finite-root %s --out-root %s"
    % ((A3_DE_ROOT,) + A3_FINITE_ROOTS + (A3_FIT_ROOT,)))
#: Fixed brackets (design §11.2; recomputed from the A2 root pre-fit).
A3_DELTA_DE = {
    "L045": (0.24452956979862517, 0.078125),
    "L055": (0.30312331979862517, 0.05859375),
    "L2": (0.5468113653656221, 0.09765625),
}
A3_WALL_BUDGET_S = 300.0
A3_FIT_EVIDENCE_FILES = ("manifest.json", "clusters.csv", "fit.json",
                         "backoffs.json", "command_log.txt")
A3_PREDICTION_NAMES = ("d16_prediction_L045_m125.json",
                       "d16_prediction_L055_m125.json",
                       "d16_prediction_L2_m94.json")
#: Accepted pooled totals per (source_label, profile, n, m): (y_exact, t).
#: From design §3 F-table + live arm_summary pooled rows (reconciled pre-fit).
A3_EXPECTED_TOTALS = {
    ("D10-A1", "L045", 64, 59): (20, 24),
    ("D10-A1", "L045", 128, 118): (10, 24),
    ("D10-R3", "L045", 128, 118): (23, 72),
    ("D10-R3", "L045", 256, 236): (29, 72),
    ("D12", "L045", 128, 118): (26, 72),
    ("D12", "L055", 128, 118): (42, 72),
    ("D12", "L045", 256, 236): (33, 72),
    ("D12", "L055", 256, 236): (46, 72),
    ("D14N", "L045", 128, 110): (3, 72),
    ("D14N", "L055", 128, 110): (7, 72),
    ("D14N", "L2", 128, 104): (63, 72),
    ("D15", "L045", 128, 110): (0, 32),
    ("D15", "L045", 128, 114): (6, 32),
    ("D15", "L045", 128, 118): (19, 32),
    ("D15", "L055", 128, 110): (1, 32),
    ("D15", "L055", 128, 114): (13, 32),
    ("D15", "L055", 128, 118): (22, 32),
    ("D15", "L2", 128, 83): (0, 32),
    ("D15", "L2", 128, 86): (0, 32),
    ("D15", "L2", 128, 89): (0, 32),
}
A3_CLUSTER_COLUMNS = ("source_root", "source_label", "profile", "layer",
                      "n", "m", "graph_seed", "graph_id", "y", "t", "delta")
#: Frozen decoder family (checked as substrings so the readiness
#: no-production-import gate keeps passing; the check still fails closed on
#: any non-cold-row-layered adapter).
A3_FROZEN_DECODER = {"adapter_row": "row_layered", "adapter_family": "fftqspa",
                     "max_iter": 90, "damping_alpha": 1.0,
                     "schedule": "cold row-layered"}


def _a3_bool(value):
    return str(value).strip().lower() in ("1", "true", "yes")


def _a3_root_label(root_path):
    s = str(root_path).replace("\\", "/")
    if "d10_mixed_degree_l1_b2dd13e4" in s:
        return "D10-A1"
    if "d10_r3_fresh_graph_scaling_4d39ed0e" in s:
        return "D10-R3"
    if "d12_finite_l1_degree_94fb9d22" in s:
        return "D12"
    if "v72p2d14_discriminator/20260914_r1" in s:
        return "D14N"
    if "d15_finite_margin_curve_8c1e4f2a" in s:
        return "D15"
    raise ValueError("unknown finite root (no glob discovery): %r" % (root_path,))


def _a3_canonical(root_label, row):
    """Map one raw decoder row to (canonical_profile, klass); non-FIT → skip."""
    arm = str(row.get("arm", ""))
    oracle = _a3_bool(row.get("oracle", False))
    if root_label in ("D10-A1", "D10-R3"):
        if arm == "PEG_DV23_LAM2_045":
            return ("L045", "FIT_L045")
        return (None, "DESCRIPTIVE_ONLY")
    if root_label == "D12":
        if arm == "L045":
            return ("L045", "FIT_L045")
        if arm == "L055":
            return ("L055", "FIT_L055")
        return (None, "DESCRIPTIVE_ONLY")
    if root_label == "D14N":
        if arm == "L045" and not oracle:
            return ("L045", "FIT_L045")
        if arm == "L055" and not oracle:
            return ("L055", "FIT_L055")
        if arm == "L2_ORACLE" and oracle:
            return ("L2", "FIT_L2")
        if arm == "L2_APP":
            return (None, "EXCLUDED_APP_JOINT")
        return (None, "DESCRIPTIVE_ONLY")
    if root_label == "D15":
        if arm == "L045" and not oracle:
            return ("L045", "FIT_L045")
        if arm == "L055" and not oracle:
            return ("L055", "FIT_L055")
        if arm == "L2_ORACLE" and oracle:
            return ("L2", "FIT_L2")
        return (None, "DESCRIPTIVE_ONLY")
    raise ValueError("unknown root label %r" % (root_label,))


def a3_recompute_brackets(de_root):
    """Recompute the three fixed brackets from the A2 DE root (read-only).

    Literal/root disagreement is STOP (never average/refit/substitute).
    """
    root = _repo_root() / str(de_root) if not Path(str(de_root)).is_absolute() \
        else Path(str(de_root))
    summary = json.loads((root / "summary.json").read_text("utf-8"))
    s_table = summary.get("s_table", {})
    out = {}
    for profile in ("L045", "L055", "L2"):
        s16 = {m: s_table["%s:m%d:p16000" % (profile, m)]["S"]
               for m in DE_GRID_M[profile]}
        s4 = {m: s_table["%s:m%d:p4000" % (profile, m)]["S"]
              for m in DE_GRID_M[profile]}
        got = bracket_delta_de(profile, s16, s4)
        want_delta, want_h = A3_DELTA_DE[profile]
        if abs(float(got["delta_de"]) - float(want_delta)) > 1e-12 \
                or abs(float(got["h"]) - float(want_h)) > 1e-12:
            raise ValueError(
                "STOP: literal/root bracket disagreement for %s: "
                "root (%.17g, h=%.17g) != frozen (%.17g, h=%.17g)"
                % (profile, got["delta_de"], got["h"], want_delta, want_h))
        out[profile] = {"delta_de": float(got["delta_de"]), "h": float(got["h"]),
                        "lo_m": got["lo_m"], "hi_m": got["hi_m"],
                        "flags": list(got["flags"])}
    return out


def a3_aggregate_finite(finite_roots):
    """Aggregate actual decoder rows → one binomial cluster per key.

    Key is ``(source_root, profile, n, m, graph_seed)`` with ``y=exact``,
    ``t=blocks``. Preserves root+graph identity; never pools/duplicates/
    merges syndrome/undetected. Recomputes ``delta`` (mismatch STOP),
    enforces frozen decoder semantics + one class, fails on D16/banned/fake
    contact, and reconciles to :data:`A3_EXPECTED_TOTALS` pre-fit.
    """
    roots = [str(r) for r in finite_roots]
    if len(roots) != 5:
        raise ValueError("A3 needs exactly five finite roots, got %d" % len(roots))
    for r in roots:
        s = r.replace("\\", "/")
        if D16_OFFICIAL_ROOT in s or s.rstrip("/").endswith("d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a"):
            raise ValueError("STOP: D16 identity in fit inputs: %r" % (r,))
        if FAKE_SCRATCH_ROOT.rstrip("/") in s:
            raise ValueError("STOP: fake-scratch contact in fit inputs: %r" % (r,))
    clusters_by_key = {}
    for root_str in roots:
        label = _a3_root_label(root_str)
        repo = _repo_root()
        base = repo / root_str if not Path(root_str).is_absolute() \
            else Path(root_str)
        if not base.is_dir():
            raise ValueError("finite root missing: %s" % root_str)
        manifest = json.loads((base / "manifest.json").read_text("utf-8"))
        dec = dict(manifest.get("decoder", {}))
        adapter = str(dec.get("adapter", ""))
        if A3_FROZEN_DECODER["adapter_row"] not in adapter \
                or A3_FROZEN_DECODER["adapter_family"] not in adapter:
            raise ValueError("STOP: changed decoder adapter in %s: %r"
                             % (root_str, dec.get("adapter")))
        for key in ("max_iter", "schedule"):
            if dec.get(key) != A3_FROZEN_DECODER[key]:
                raise ValueError("STOP: changed decoder in %s: %r != %r"
                                 % (root_str, dec.get(key),
                                    A3_FROZEN_DECODER[key]))
        if abs(float(dec.get("damping_alpha", -1.0))
               - A3_FROZEN_DECODER["damping_alpha"]) > 1e-12:
            raise ValueError("STOP: changed decoder damping in %s" % root_str)
        # Graph join table: (arm_key, n, graph_seed) -> (n, m).
        graphs = {}
        for grow in _read_csv(base / "graph_records.csv"):
            try:
                gseed = int(grow.get("graph_seed", ""))
            except (TypeError, ValueError):
                continue
            if str(grow.get("admitted", "True")).strip().lower() not in \
                    ("1", "true", "yes"):
                continue
            if label == "D15":
                arm = str(grow.get("arm", ""))
                try:
                    n = int(grow.get("n", "128"))
                    m = int(grow.get("m", grow.get("rows", "0")))
                    rows = int(grow.get("rows", m))
                except (TypeError, ValueError):
                    raise ValueError("STOP: bad D15 graph row %r" % (grow,))
                graphs[(arm, rows, gseed)] = (n, m)
            else:
                arm = str(grow.get("arm", ""))
                try:
                    width = int(grow.get("width", grow.get("n", "0")))
                    n = int(grow.get("n", width))
                    m = int(grow.get("m", "0"))
                except (TypeError, ValueError):
                    raise ValueError("STOP: bad graph row %r" % (grow,))
                # D14N L2 graphs are filed under arm "L2"; decoder uses
                # "L2_ORACLE" — keep both keys pointing at the same cell.
                graphs[(arm, n, gseed)] = (n, m)
                if label == "D14N" and arm == "L2":
                    graphs[("L2_ORACLE", n, gseed)] = (n, m)
        dec_name = "l1_records.csv" if label == "D10-A1" else "decoder_records.csv"
        for row in _read_csv(base / dec_name):
            # Fail-closed identity gates on every row actually read.
            seed_probe = {}
            for key in ("graph_seed", "block_seed", "l1_graph_seed",
                        "l2_graph_seed"):
                if row.get(key) not in (None, ""):
                    seed_probe[key] = row[key]
            assert_no_banned_seeds([seed_probe])
            refuse_fake_scratch([{"source_path": "%s/%s" % (root_str, dec_name)}])
            try:
                wall = float(row.get("wall_s", "1"))
                iters = int(row.get("iterations", "90"))
            except (TypeError, ValueError):
                raise ValueError("STOP: bad wall/iters row %r" % (row,))
            if wall <= FAKE_WALL_MAX_S and iters == FAKE_ITERS:
                raise ValueError("STOP: fake-scratch signature row in %s"
                                 % root_str)
            if str(row.get("crash", "False")).strip().lower() in \
                    ("1", "true", "yes") or str(row.get("error", "")):
                raise ValueError("STOP: crashed decoder row in fit inputs "
                                 "(%s)" % root_str)
            if row.get("undetected") is not None and _a3_bool(row.get("undetected")):
                raise ValueError("STOP: undetected row must stay isolated "
                                 "(%s)" % root_str)
            canonical, klass = _a3_canonical(label, row)
            if klass != "FIT_L045" and klass != "FIT_L055" \
                    and klass != "FIT_L2":
                continue  # descriptive/APP/joint/controls excluded, never fit
            if canonical not in ("L045", "L055", "L2"):
                raise ValueError("STOP: FIT row without canonical profile")
            layer = PROFILE_LAYER[canonical]
            if row.get("layer") not in (None, "") \
                    and str(row.get("layer")) != layer:
                raise ValueError("STOP: layer/profile mismatch %r" % (row,))
            # Frozen per-row decoder semantics (cold row-layered family).
            if not (1 <= iters <= DECODER_MAX_ITER):
                raise ValueError("STOP: iterations outside frozen 1..90")
            prov = str(row.get("belief_provenance", "CHECK_UPDATED"))
            if canonical == "L2":
                if prov != "ORACLE":
                    raise ValueError("STOP: L2 FIT row without ORACLE "
                                     "provenance")
            elif prov != "CHECK_UPDATED":
                raise ValueError("STOP: L1 FIT row without CHECK_UPDATED "
                                 "provenance")
            # Join to graph metadata for (n, m, graph_seed).
            if label == "D15":
                try:
                    rows_m = int(row.get("rows", "0"))
                    gseed = int(row.get("graph_seed", ""))
                except (TypeError, ValueError):
                    raise ValueError("STOP: bad D15 decoder row")
                key = (str(row.get("arm", "")), rows_m, gseed)
                if key not in graphs:
                    raise ValueError("STOP: D15 decoder/graph join miss %r"
                                     % (key,))
                n, m = graphs[key]
                if m != rows_m:
                    raise ValueError("STOP: D15 rows/m mismatch")
                try:
                    disclosed = int(row.get("disclosed_bits", 5 * m))
                except (TypeError, ValueError):
                    raise ValueError("STOP: bad disclosed_bits")
                if disclosed != 5 * m:
                    raise ValueError("STOP: disclosed-bits/m mismatch")
            elif label == "D14N":
                try:
                    n = 128
                    if canonical == "L2":
                        gseed = int(row.get("l2_graph_seed", ""))
                        arm_key = "L2_ORACLE"
                    else:
                        gseed = int(row.get("l1_graph_seed", ""))
                        arm_key = str(row.get("arm", ""))
                except (TypeError, ValueError):
                    raise ValueError("STOP: bad D14N decoder row")
                if (arm_key, n, gseed) not in graphs:
                    raise ValueError("STOP: D14N decoder/graph join miss %r"
                                     % ((arm_key, n, gseed),))
                n, m = graphs[(arm_key, n, gseed)]
            else:
                try:
                    width = int(row.get("width", "0"))
                    gseed = int(row.get("graph_seed", ""))
                except (TypeError, ValueError):
                    raise ValueError("STOP: bad decoder row")
                arm_key = str(row.get("arm", ""))
                if (arm_key, width, gseed) not in graphs:
                    raise ValueError("STOP: decoder/graph join miss %r"
                                     % ((arm_key, width, gseed),))
                n, m = graphs[(arm_key, width, gseed)]
            delta = delta_of(m, n, layer)  # recomputed, never stored
            if not math.isfinite(delta):
                raise ValueError("STOP: nonfinite delta")
            ckey = (root_str, canonical, int(n), int(m), int(gseed))
            cell = clusters_by_key.get(ckey)
            if cell is None:
                cell = {"source_root": root_str, "source_label": label,
                        "profile": canonical, "layer": layer, "n": int(n),
                        "m": int(m), "graph_seed": int(gseed),
                        "graph_id": "%s:%s:n%d:m%d:g%d"
                                    % (label, canonical, int(n), int(m),
                                       int(gseed)),
                        "root": label, "y": 0, "t": 0, "delta": float(delta)}
                clusters_by_key[ckey] = cell
            if abs(cell["delta"] - float(delta)) > 1e-12:
                raise ValueError("STOP: delta mismatch inside cluster")
            cell["t"] += 1
            if _a3_bool(row.get("exact", False)):
                cell["y"] += 1
    clusters = sorted(clusters_by_key.values(),
                      key=lambda c: (c["source_root"], c["profile"], c["n"],
                                     c["m"], c["graph_seed"]))
    # One cluster per key already; forbid row-as-cluster degeneracy is
    # structural (t must be the full per-graph block count).
    expect_t = {"D10-A1": 8, "D10-R3": 12, "D12": 12, "D14N": 12, "D15": 8}
    for cell in clusters:
        if cell["t"] != expect_t[cell["source_label"]]:
            raise ValueError("STOP: cluster t=%d != %d blocks for %s "
                             "(graph-not-row violated?)"
                             % (cell["t"], expect_t[cell["source_label"]],
                                cell["graph_id"]))
        if not (0 <= cell["y"] <= cell["t"]):
            raise ValueError("STOP: bad cluster counts")
    assert_no_residual_covariates(clusters)
    # Reconcile aggregated counts to the accepted totals pre-fit.
    sums = {}
    for cell in clusters:
        key = (cell["source_label"], cell["profile"], cell["n"], cell["m"])
        got = sums.setdefault(key, [0, 0])
        got[0] += cell["y"]
        got[1] += cell["t"]
    if set(sums) != set(A3_EXPECTED_TOTALS):
        raise ValueError("STOP: aggregated keys %s != accepted %s"
                         % (sorted(sums), sorted(A3_EXPECTED_TOTALS)))
    for key, (wy, wt) in A3_EXPECTED_TOTALS.items():
        gy, gt = sums[key]
        if (gy, gt) != (wy, wt):
            raise ValueError("STOP: reconciliation miss %s: got (%d/%d) != "
                             "accepted (%d/%d)" % (key, gy, gt, wy, wt))
    return clusters


def _a3_logistic_nll(clusters, delta_de, alpha_log, beta):
    n = np.array([float(c["n"]) for c in clusters], dtype=np.float64)
    d = np.array([float(c["delta"]) for c in clusters], dtype=np.float64)
    y = np.array([int(c["y"]) for c in clusters], dtype=np.float64)
    t = np.array([int(c["t"]) for c in clusters], dtype=np.float64)
    p = np.array([logistic_p(nn, dd, float(delta_de), float(alpha_log),
                             float(beta)) for nn, dd in zip(n, d)])
    p = np.clip(p, 1e-12, 1.0 - 1e-12)  # ponytail: log guard only
    return float(-np.sum(y * np.log(p) + (t - y) * np.log(1.0 - p)))


def _a3_logistic_fit(clusters, delta_de, beta_fixed):
    """Descriptive-only logistic-link fit (same fixed delta_DE, grid search)."""
    la = np.linspace(math.log10(ALPHA_BOUNDS[0]),
                     math.log10(ALPHA_BOUNDS[1]), 25)
    best = (math.inf, None)
    for a in 10.0 ** la:
        v = _a3_logistic_nll(clusters, delta_de, float(a), float(beta_fixed))
        if v < best[0]:
            best = (v, float(a))
    alpha = best[1]
    for _ in range(2):  # ponytail: fixed 2 refinements, mirrors probit grid
        la = np.linspace(math.log10(alpha) - 0.35, math.log10(alpha) + 0.35, 17)
        la = np.clip(la, math.log10(ALPHA_BOUNDS[0]),
                      math.log10(ALPHA_BOUNDS[1]))
        best = (math.inf, alpha)
        for a in 10.0 ** la:
            v = _a3_logistic_nll(clusters, delta_de, float(a),
                                 float(beta_fixed))
            if v < best[0]:
                best = (v, float(a))
        alpha = best[1]
    return {"alpha_log": float(alpha), "beta": float(beta_fixed),
            "nll": float(_a3_logistic_nll(clusters, delta_de, alpha,
                                         float(beta_fixed)))}


def _a3_loro(clusters, delta_de, beta_fixed):
    """Leave-one-root-out refits (L045/L055 sensitivity, incl. D14N-vs-D15)."""
    roots = sorted({c["root"] for c in clusters})
    out = {}
    for root in roots:
        sub = [c for c in clusters if c["root"] != root]
        if not sub:
            continue
        out[str(root)] = fit_profile(sub, float(delta_de),
                                     beta_fixed=beta_fixed)
    return out


def a3_fit_all(clusters, brackets):
    """Frozen ladder per profile + bootstrap/LOO/LORO + logistic (descriptive).

    ``delta_DE`` fixed, never optimized. L045/L055 try two-param then
    ``beta=0`` then ``MODEL_NOT_IDENTIFIABLE``; L2 is predeclared one-param.
    """
    results = {}
    for profile in ("L045", "L055", "L2"):
        sub = [c for c in clusters if c["profile"] == profile]
        if not sub:
            raise ValueError("no clusters for profile %s" % profile)
        delta_de = float(brackets[profile]["delta_de"])
        primary = (profile == "L2")
        ladder = fit_with_ladder(sub, delta_de, primary_one_param=primary,
                                 B=BOOTSTRAP_B, seed=BOOTSTRAP_SEED)
        model = ladder.get("model")
        if model == MODEL_NOT_IDENTIFIABLE:
            results[profile] = {"profile": profile, "model": model,
                                "reason": ladder.get("reason", ""),
                                "delta_de": delta_de,
                                "fit": ladder.get("fit"),
                                "two_param_fit": ladder.get("two_param_fit")}
            continue
        beta_fixed = ladder.get("beta_fixed")
        fixed = (0.0 if model == "one_param" else None)
        if beta_fixed is not None:
            fixed = float(beta_fixed)
        boot = cluster_bootstrap(sub, delta_de, beta_fixed=fixed,
                                 B=BOOTSTRAP_B, seed=BOOTSTRAP_SEED)
        loo = loo_range(sub, delta_de, beta_fixed=fixed)
        loro = _a3_loro(sub, delta_de, fixed) if profile != "L2" \
            else _a3_loro(sub, delta_de, fixed)
        beta_for_log = float(ladder["fit"]["beta"])
        logistic = _a3_logistic_fit(sub, delta_de, beta_for_log)
        alpha_ci = (_pct(boot["alpha"], 2.5), _pct(boot["alpha"], 97.5))
        if model == "two_param":
            beta_ci = (_pct(boot["beta"], 2.5), _pct(boot["beta"], 97.5))
        else:
            beta_ci = "fixed@0"
        results[profile] = {"profile": profile, "model": model,
                            "reason": ladder.get("reason", ""),
                            "delta_de": delta_de, "fit": ladder["fit"],
                            "bootstrap": {"alpha_ci95": list(alpha_ci),
                                          "beta_ci95": (list(beta_ci)
                                                        if isinstance(beta_ci,
                                                                      tuple)
                                                        else beta_ci),
                                          "B": boot["B"], "seed": boot["seed"],
                                          "n_ok": boot["n_ok"]},
                            "loo": loo, "loro": loro, "logistic": logistic,
                            "beta_fixed": fixed}
    return results


def _a3_union_fits(pres):
    """Deterministic wider-uncertainty ensemble: point + bootstrap CI corners
    + LOO corners + leave-one-root-out points (prediction uses the wider)."""
    fit = pres["fit"]
    point = (float(fit["alpha"]), float(fit["beta"]))
    fits = [point]
    boot = pres.get("bootstrap", {})
    ci_a = boot.get("alpha_ci95")
    ci_b = boot.get("beta_ci95")
    if isinstance(ci_a, (list, tuple)) and len(ci_a) == 2:
        alo, ahi = float(ci_a[0]), float(ci_a[1])
        if isinstance(ci_b, (list, tuple)) and len(ci_b) == 2:
            blo, bhi = float(ci_b[0]), float(ci_b[1])
            fits += [(alo, blo), (alo, bhi), (ahi, blo), (ahi, bhi)]
        else:
            fits += [(alo, point[1]), (ahi, point[1])]
    loo = pres.get("loo", {})
    if "alpha_min" in loo:
        amin, amax = float(loo["alpha_min"]), float(loo["alpha_max"])
        bmin, bmax = float(loo["beta_min"]), float(loo["beta_max"])
        fits += [(amin, bmin), (amin, bmax), (amax, bmin), (amax, bmax)]
    for _, refit in (pres.get("loro") or {}).items():
        fits.append((float(refit["alpha"]), float(refit["beta"])))
    # Deduplicate exactly (deterministic order kept).
    seen, uniq = set(), []
    for pair in fits:
        if pair not in seen:
            seen.add(pair)
            uniq.append(pair)
    return uniq


def a3_backoffs(fit_results, brackets):
    """Frozen inversion at n=64/128/256 × eps 0.10/0.01, point + union ints."""
    table = []
    for profile in ("L045", "L055", "L2"):
        pres = fit_results.get(profile)
        if pres is None or pres.get("model") == MODEL_NOT_IDENTIFIABLE:
            continue
        layer = PROFILE_LAYER[profile]
        delta_de = float(brackets[profile]["delta_de"])
        h = float(brackets[profile]["h"])
        dd_list = [delta_de - h, delta_de, delta_de + h]
        fits = _a3_union_fits(pres)
        point = (float(pres["fit"]["alpha"]), float(pres["fit"]["beta"]))
        for n in (64, 128, 256):
            row = {"profile": profile, "n": int(n)}
            for eps in (EPS_PRIMARY, EPS_SENSITIVITY):
                ms = m_star(int(n), float(eps), delta_de, point[0], point[1],
                            layer)
                back = row_backoff(int(n), float(eps), delta_de, point[0],
                                   point[1], layer)
                lo_ms, hi_ms = ms, ms
                for alpha, beta in fits:
                    for dd in dd_list:
                        cand = m_star(int(n), float(eps), dd, alpha, beta,
                                      layer)
                        lo_ms, hi_ms = min(lo_ms, cand), max(hi_ms, cand)
                key = ("eps%.2f" % float(eps)).replace(".", "p")
                row[key] = {"m_point": int(ms), "backoff_point": int(back),
                            "m_union": [int(lo_ms), int(hi_ms)],
                            "backoff_union": [int(lo_ms - baseline_m0(layer, int(n))),
                                              int(hi_ms - baseline_m0(layer, int(n)))]}
            if row["eps0p10"]["m_point"] > row["eps0p01"]["m_point"]:
                raise ValueError("STOP: m*(0.01) < m*(0.10) for %s n=%d"
                                 % (profile, n))
            table.append(row)
    return table


def _a3_binomial_8_interval(p_point):
    """Deterministic model-based 8-trial 95% interval (exact binomial)."""
    p = min(max(float(p_point), 0.0), 1.0)
    pmf = [math.comb(8, k) * (p ** k) * ((1.0 - p) ** (8 - k)) for k in range(9)]
    cdf = []
    acc = 0.0
    for v in pmf:
        acc += v
        cdf.append(acc)
    lo_k, hi_k = 0, 8
    for k in range(9):
        if cdf[k] >= 0.025:
            lo_k = k
            break
    acc = 0.0
    for k in range(8, -1, -1):
        acc += pmf[k]
        if acc >= 0.025:
            hi_k = k
            break
    # ponytail: exact 8-trial quantiles; upgrade to Clopper-Pearson only if needed
    return {"n_trials": 8, "p_point": float(p), "k_low": int(lo_k),
            "k_high": int(hi_k), "rate_low": float(lo_k) / 8.0,
            "rate_high": float(hi_k) / 8.0}


def _a3_empirical_residual_range(clusters, profile, delta_de, alpha, beta):
    res = []
    for c in clusters:
        if c["profile"] != profile:
            continue
        pred = float(p_success(c["n"], c["delta"], float(delta_de),
                               float(alpha), float(beta)))
        res.append(float(c["y"]) / float(c["t"]) - pred)
    if not res:
        return {"min_residual": 0.0, "max_residual": 0.0, "n_clusters": 0,
                "descriptive_only": True}
    return {"min_residual": float(min(res)), "max_residual": float(max(res)),
            "n_clusters": int(len(res)), "descriptive_only": True}


def a3_predictions(fit_results, brackets, clusters, de_root):
    """Build exactly the three outcome-BLANK D16 prediction records.

    Only call when all three profiles identify; otherwise persist diagnostics
    only and write no filled predictions.
    """
    for profile in ("L045", "L055", "L2"):
        pres = fit_results.get(profile)
        if pres is None or pres.get("model") == MODEL_NOT_IDENTIFIABLE:
            raise ValueError("MODEL_NOT_IDENTIFIABLE for %s: no filled "
                             "predictions" % profile)
    assert_d16_root_absent()
    preds = []
    arms = (("L045", 125), ("L055", 125), ("L2", 94))
    for profile, m in arms:
        pres = fit_results[profile]
        layer = PROFILE_LAYER[profile]
        n = N_REF
        delta = delta_of(int(m), int(n), layer)
        delta_de = float(brackets[profile]["delta_de"])
        h = float(brackets[profile]["h"])
        dd_list = [delta_de - h, delta_de, delta_de + h]
        fits = _a3_union_fits(pres)
        lo, hi = predict_interval(int(n), float(delta), fits, dd_list)
        point = float(p_success(int(n), float(delta), delta_de,
                                float(pres["fit"]["alpha"]),
                                float(pres["fit"]["beta"])))
        disp = {"binomial_8_trial_interval_95":
                _a3_binomial_8_interval(point),
                "empirical_graph_residual_range_descriptive":
                _a3_empirical_residual_range(clusters, profile, delta_de,
                                            float(pres["fit"]["alpha"]),
                                            float(pres["fit"]["beta"]))}
        boot = pres.get("bootstrap", {})
        pred = {
            "schema": "d16_holdout_prediction_v1",
            "profile": profile, "n": int(n), "m": int(m),
            "delta": float(delta), "layer": layer,
            "delta_DE": {"value": float(delta_de), "h": float(h),
                         "source_de_root": str(de_root),
                         "flags": list(brackets[profile].get("flags", [])),
                         "union_list": [float(v) for v in dd_list]},
            "model": {"link": "probit",
                      "alpha": float(pres["fit"]["alpha"]),
                      "beta": float(pres["fit"]["beta"]),
                      "alpha_ci": list(boot.get("alpha_ci95", [])),
                      "beta_ci_or_fixed": boot.get("beta_ci95", []),
                      "identifiability": pres.get("model"),
                      "ladder_reason": pres.get("reason", "")},
            "prediction": {"p_success_interval_95": [float(lo), float(hi)],
                           "p_point": float(point),
                           "expected_graph_dispersion": disp,
                           "n_graphs": 4, "trials_per_graph": 8},
            "falsification": {
                "rule": "pool outside 95% band -> FALSIFIED; inside -> "
                        "NOT_FALSIFIED; engineering_violation -> "
                        "INCONCLUSIVE; per-graph range descriptive"},
            "outcome": {"pool": "BLANK", "per_graph": "BLANK",
                        "exact": "BLANK", "syndrome": "BLANK",
                        "undetected": "BLANK", "terminal": "BLANK"},
            "gate": {"fail_if_d16_root_exists": True,
                     "predictions_frozen_before_run": True},
        }
        for field in ("pool", "per_graph", "exact", "syndrome",
                      "undetected", "terminal"):
            if pred["outcome"][field] != "BLANK":
                raise ValueError("prediction outcome not blank")
        preds.append(pred)
    return preds


def _a3_rss_bytes():
    try:
        import resource
        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    except Exception:
        return 0


def a3_write_root(bundle):
    """Persist one A3 bundle to its fresh root (never overwrite)."""
    resolved = bundle["resolved"]
    resolved.mkdir(parents=True)  # fail-closed: exists → FileExistsError
    _write_json(resolved / "manifest.json", bundle["manifest"])
    _write_csv(resolved / "clusters.csv", A3_CLUSTER_COLUMNS,
               bundle["clusters"])
    _write_json(resolved / "fit.json", bundle["fit"])
    _write_json(resolved / "backoffs.json", bundle["backoffs"])
    for pred, name in zip(bundle.get("predictions") or [],
                          A3_PREDICTION_NAMES):
        with open(resolved / name, "w", encoding="utf-8") as fh:
            json.dump(pred, fh, indent=2, sort_keys=True)
            fh.write("\n")
    with open(resolved / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("".join(line + "\n" for line in bundle["log_lines"]))
    return bundle["manifest"]


def a3_verify_fit_root(out_root, de_root=A3_DE_ROOT,
                       finite_roots=A3_FINITE_ROOTS):
    """Read-only recomputation of a completed A3 fit root (zero sci calls)."""
    root = Path(str(out_root))
    violations = []
    if not root.is_dir():
        print("VERIFY root missing: %s" % root)
        return False
    names = sorted(p.name for p in root.iterdir())
    want = sorted(list(A3_FIT_EVIDENCE_FILES))
    manifest = json.loads((root / "manifest.json").read_text("utf-8")) \
        if (root / "manifest.json").exists() else {}
    n_pred = 0
    for cand in A3_PREDICTION_NAMES:
        if (root / cand).exists():
            n_pred += 1
    if n_pred not in (0, 3):
        violations.append("prediction files != 0/3")
    if sorted([n for n in names if n not in A3_PREDICTION_NAMES]) != want:
        violations.append("evidence files mismatch: %s" % names)
        print("VERIFY evidence files mismatch: %s" % names)
        return False
    if manifest.get("command") != A3_FROZEN_COMMAND:
        violations.append("manifest command != frozen A3 command")
    if manifest.get("change_id") != CHANGE_ID:
        violations.append("manifest change_id mismatch")
    try:
        brackets = a3_recompute_brackets(de_root)
    except Exception as exc:
        violations.append("bracket recompute FAIL: %s" % exc)
        brackets = None
    try:
        clusters = a3_aggregate_finite(list(finite_roots))
    except Exception as exc:
        violations.append("aggregation recompute FAIL: %s" % exc)
        clusters = None
    if clusters is not None:
        stored_clusters = _read_csv(root / "clusters.csv")
        if len(stored_clusters) != len(clusters):
            violations.append("cluster rows %d != recomputed %d"
                              % (len(stored_clusters), len(clusters)))
        else:
            for stored, cell in zip(
                    sorted(stored_clusters,
                           key=lambda r: (r["source_root"], r["profile"],
                                          int(r["n"]), int(r["m"]),
                                          int(r["graph_seed"]))), clusters):
                for key in ("source_root", "profile", "n", "m",
                            "graph_seed", "y", "t"):
                    if str(stored[key]) != str(cell[key]):
                        violations.append("cluster %s %s drift" % (
                            cell["graph_id"], key))
                        break
                if abs(float(stored["delta"]) - float(cell["delta"])) > 1e-12:
                    violations.append("cluster %s delta drift"
                                      % cell["graph_id"])
        fit_doc = json.loads((root / "fit.json").read_text("utf-8"))
        for profile in ("L045", "L055", "L2"):
            stored = (fit_doc.get("profiles") or {}).get(profile)
            if stored is None:
                violations.append("fit profile %s missing" % profile)
                continue
            sub = [c for c in clusters if c["profile"] == profile]
            if stored.get("model") == MODEL_NOT_IDENTIFIABLE:
                continue
            try:
                primary = (profile == "L2")
                check = fit_with_ladder(
                    sub, float(brackets[profile]["delta_de"]),
                    primary_one_param=primary, B=BOOTSTRAP_B,
                    seed=BOOTSTRAP_SEED)
            except Exception as exc:
                violations.append("selection recompute FAIL %s: %s"
                                  % (profile, exc))
                continue
            if check.get("model") != stored.get("model"):
                violations.append("model selection drift %s: %s != %s"
                                  % (profile, check.get("model"),
                                     stored.get("model")))
            try:
                want_alpha = float(stored["fit"]["alpha"])
                want_beta = float(stored["fit"]["beta"])
                got = fit_profile(
                    sub, float(brackets[profile]["delta_de"]),
                    beta_fixed=(0.0 if stored.get("model") == "one_param"
                                else None))
                if abs(got["alpha"] - want_alpha) / max(want_alpha, 1e-12) > 1e-9 \
                        or abs(got["beta"] - want_beta) > 1e-9:
                    violations.append("point-fit drift %s" % profile)
            except Exception as exc:
                violations.append("point-fit recompute FAIL %s: %s"
                                  % (profile, exc))
        # Prediction + blank-gate recompute.
        for name in A3_PREDICTION_NAMES:
            path = root / name
            if not path.exists():
                continue
            pred = json.loads(path.read_text("utf-8"))
            for field in ("pool", "per_graph", "exact", "syndrome",
                          "undetected", "terminal"):
                if pred.get("outcome", {}).get(field) != "BLANK":
                    violations.append("%s outcome %s not BLANK" % (name, field))
            disp = pred.get("prediction", {}).get("expected_graph_dispersion",
                                                  {})
            if "binomial_8_trial_interval_95" not in disp \
                    or "empirical_graph_residual_range_descriptive" not in disp:
                violations.append("%s dispersion object incomplete" % name)
        try:
            assert_d16_root_absent()
        except FileExistsError:
            violations.append("D16 root exists (holdout violated)")
    print("VERIFY checked_clusters=%d violations=%d"
          % (len(clusters) if clusters is not None else -1, len(violations)))
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    ok = not violations
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return ok


def a3_run(out_root, de_root=A3_DE_ROOT, finite_roots=A3_FINITE_ROOTS,
           now_fn=None, rss_fn=None):
    """Execute the frozen one-shot A3 fit (no writes until verified in-memory).

    Zero DE/decoder/CAL/VAL calls; exactly six input roots; single process;
    no retry/resume/tuning. Creates the fresh fit root exactly once.
    """
    now = now_fn or time.monotonic
    rss_fn = rss_fn or _a3_rss_bytes
    t0 = float(now())
    log_lines = []

    def log(message):
        line = "[%s] %s" % (time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                         time.gmtime()), message)
        log_lines.append(line)

    finite_roots = list(finite_roots)
    # Fresh-root probe BEFORE input reads (fail-closed, creates nothing).
    resolved = probe_fresh_root(out_root)
    # D16 holdout gate BEFORE input reads.
    assert_d16_root_absent()
    log("A3 roots validated; D16 absent; reading six inputs")
    brackets = a3_recompute_brackets(de_root)
    log("brackets recomputed L045=%.17g L055=%.17g L2=%.17g"
        % (brackets["L045"]["delta_de"], brackets["L055"]["delta_de"],
           brackets["L2"]["delta_de"]))
    clusters = a3_aggregate_finite(finite_roots)
    log("aggregated clusters=%d (L045=%d L055=%d L2=%d)"
        % (len(clusters),
           sum(1 for c in clusters if c["profile"] == "L045"),
           sum(1 for c in clusters if c["profile"] == "L055"),
           sum(1 for c in clusters if c["profile"] == "L2")))
    fit_results = a3_fit_all(clusters, brackets)
    for profile in ("L045", "L055", "L2"):
        pres = fit_results[profile]
        if pres.get("model") == MODEL_NOT_IDENTIFIABLE:
            log("%s %s (%s)" % (profile, MODEL_NOT_IDENTIFIABLE,
                                pres.get("reason", "")))
        else:
            log("%s %s alpha=%.6g beta=%.6g" % (
                profile, pres.get("model"), pres["fit"]["alpha"],
                pres["fit"]["beta"]))
    backoffs = a3_backoffs(fit_results, brackets)
    log("backoffs rows=%d" % len(backoffs))
    predictions = None
    terminal = "SCALING_MODEL_NOT_IDENTIFIABLE"
    if all(fit_results[p].get("model") != MODEL_NOT_IDENTIFIABLE
           for p in ("L045", "L055", "L2")):
        predictions = a3_predictions(fit_results, brackets, clusters, de_root)
        terminal = "SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN"
        log("predictions frozen=%d (outcome BLANK)" % len(predictions))
    else:
        missing = [p for p in ("L045", "L055", "L2")
                   if fit_results[p].get("model") == MODEL_NOT_IDENTIFIABLE]
        log("diagnostics only; no filled predictions (missing %s)" % missing)
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn())
    violations = []
    if wall_s > A3_WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if peak_rss >= RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")
    manifest = {
        "schema": "v72p2d17_scaling_fit_manifest_v1",
        "change_id": CHANGE_ID, "cycle": CYCLE_ID,
        "claim_ceiling": CLAIM_CEILING,
        "command": A3_FROZEN_COMMAND,
        "de_root": str(de_root),
        "finite_roots": list(finite_roots),
        "out_root": str(resolved),
        "brackets": brackets,
        "terminal": terminal,
        "cluster_counts": {
            "total": len(clusters),
            "L045": sum(1 for c in clusters if c["profile"] == "L045"),
            "L055": sum(1 for c in clusters if c["profile"] == "L055"),
            "L2": sum(1 for c in clusters if c["profile"] == "L2")},
        "models": {p: {"model": fit_results[p].get("model"),
                       "reason": fit_results[p].get("reason", "")}
                   for p in ("L045", "L055", "L2")},
        "budgets": {"de_calls": 0, "decoder_calls": 0, "cal_calls": 0,
                    "val_calls": 0, "inputs": 6, "wall_s": A3_WALL_BUDGET_S,
                    "rss_bytes": RSS_BUDGET_BYTES, "processes": 1,
                    "retry": False, "resume": False, "tuning": False},
        "scientific_calls": 0, "decoder_calls": 0,
        "wall_s": wall_s, "peak_rss_bytes": peak_rss,
        "budget_violations": violations,
        "evidence_files": list(A3_FIT_EVIDENCE_FILES) + (
            list(A3_PREDICTION_NAMES) if predictions else []),
        "authorization": ("A3 one-shot EXPLORE fit grant; --execution-"
                          "authorized required; D16 execution unauthorized"),
    }
    fit_doc = {"schema": "v72p2d17_scaling_fit_v1", "change_id": CHANGE_ID,
               "de_root": str(de_root), "brackets": brackets,
               "profiles": fit_results}
    back_doc = {"schema": "v72p2d17_row_backoff_v1", "change_id": CHANGE_ID,
                "rows": backoffs,
                "note": "diagnostic modeled backoffs, not FER qualification"}
    log("terminal=%s wall_s=%.3f" % (terminal, wall_s))
    bundle = {"resolved": resolved, "manifest": manifest,
              "clusters": clusters, "fit": fit_doc, "backoffs": back_doc,
              "predictions": predictions, "log_lines": log_lines}
    # Single never-overwrite writer (mkdir fail-closed inside).
    a3_write_root(bundle)
    return bundle

