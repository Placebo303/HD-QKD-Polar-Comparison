"""D18 current-channel L2 ensemble DE — readiness/planning module (E02/E03/E05).

Authority: ``.workbuddy/tasks/D18_L2_ENSEMBLE_DE_READINESS_R1_TASK_PACKET.md``
(§§1-6, 8-9) and ``openspec/changes/v72p2d18-current-channel-l2-ensemble-de``
(``design.md`` §§2-6/8-9, ``specs/l2-ensemble-de/spec.md``). Packet §§2/4/5
take precedence on any conflict; STOP rules are fail-closed.

Track: ``implementation/readiness``. This module authorizes zero scientific
DE/decoder calls. The future DE batch track is ``EXPLORE_HEAVY`` and needs
one later explicit user grant plus Pre-EXECUTE; this packet grants none.

Adjudication first (packet §2, never relabel): D17's preregistered L055
result stands ``FALSIFIED`` (observed ``27/32 = 0.84375`` vs the
parameter-probability band ``[0.8899387155669418, 0.9955050869733582]``).
The miss is a mild model-calibration miss, not an L1-construction failure.
The latent-``p`` confidence band vs observed-count predictive interval
distinction is a forward methodology amendment only; D16 is NOT recomputed.
``T(p_lo)``/``T(p_hi)`` are descriptive test values, never verdict revisions.
Legacy ``D16_L2_DEGREE_SIGNAL`` stays secondary; the L2-ensemble route is a
main-thread decision.

Reuse map (this module imports; it does not copy):
  - corrected D17 R2 production channel builder + explicit L2-oracle
    dispatch: ``d17.build_production_channels``,
    ``d17.build_l2_oracle_sampler``, ``d17.bind_production_de``
    (true-U1 conditioned, XOR-centered on U2, current Model-F candidate,
    GF32/poly37);
  - V26 MC-DE kernel: ``d9.run_de_call`` (``max_iter=60``, tol ``1e-4``,
    streak 20);
  - D9 degree/rho mathematics: ``d9.make_rho``, ``d9.validate_lambda_edge``,
    ``d9.trajectory_metrics``; node apportionment
    ``v37f.calculate_node_degree_counts`` (largest remainder);
  - D17 rate/delta axis, convergence rule, budgets, verifier patterns:
    ``d17.rate_of``, ``d17.delta_of``, ``d17.check_allocation``,
    ``d17.bracket_delta_de`` rule (same flags/thresholds),
    ``d17.probe_fresh_root``, ``d17.verify_channel_identity``.
Rejected duplication: no DE kernel, Model-F loader, GF32 primitive,
channel sampler, or candidate enumerator is reimplemented here.
D8/D9 L1 outcomes and V26 historical numeric thresholds do NOT transfer.

Stdlib + NumPy only (imported helpers already satisfy this).
"""

from __future__ import annotations

import csv
import importlib
import json
import math
import time
from pathlib import Path

from comparison_bench.formal_ir import v72p2d17_descaling as d17
from comparison_bench.formal_ir import v72p2d9_de_decoder_calibration as d9
from comparison_bench.formal_ir import v37_degree_feasibility as v37f

# --------------------------------------------------------------------------- #
# Frozen identifiers
# --------------------------------------------------------------------------- #
CHANGE_ID = "v72p2d18-current-channel-l2-ensemble-de"
CYCLE_ID = "V72P2D18-L2-ENSEMBLE-DE"
TRACK = "implementation/readiness"
FUTURE_TRACK = "EXPLORE_HEAVY"
CLAIM_CEILING = (
    "synthetic DE evidence only; no FER/leakage/SKR/qualification/"
    "promotion/publication/optimality/route-closure claim; the winner "
    "selects a candidate for a later finite-L2 packet, never a validated "
    "code and never finite construction"
)
AUTHORIZATION = ("separate explicit user/main-thread authorization required "
                 "before --de-sweep (default false, fail-closed)")

# --------------------------------------------------------------------------- #
# Adjudication (packet §2 — recorded first, verbatim in scientific effect)
# --------------------------------------------------------------------------- #
P_LO = 0.8899387155669418
P_HI = 0.9955050869733582
L055_OBSERVED = (27, 32)  # 27/32 = 0.84375
L055_VERDICT = "FALSIFIED"  # frozen; never relabel after observing D16
L055_PER_GRAPH = (7, 7, 6, 7)
L045_OBSERVED = (25, 32)  # survived
L045_PER_GRAPH = (7, 6, 7, 5)
L2_ORACLE_OBSERVED = (9, 32)  # survived its own prediction [0, 0.5]
L2_ORACLE_PER_GRAPH = (3, 1, 2, 3)


def adjudication_record():
    """Frozen §2 record: verdict preserved, ceiling, forward-only amendment."""
    return {
        "l055_verdict": L055_VERDICT,
        "l055_observed": "%d/%d=%r" % (27, 32, 27 / 32),
        "parameter_probability_band": [P_LO, P_HI],
        "interpretation_ceiling": (
            "mild model-calibration miss, NOT an L1-construction failure: "
            "L055 27/32 per-graph [7,7,6,7]; L045 25/32 survived; "
            "L2-ORACLE 9/32 survived [0,0.5]"),
        "methodology_amendment": (
            "forward-only: confidence band for latent p_success vs "
            "predictive interval/tail for an observed Binomial(n,p) count; "
            "applies to future held-outs only; D16 verdict NOT recomputed"),
        "descriptive_tail_formula": (
            "T(p; y_obs=27, n=32) = P(X <= 27 | n=32, p)"),
        "legacy_signal": "D16_L2_DEGREE_SIGNAL directional-secondary only",
        "route": ("main-thread decision: pause L1, optimize L2 ensemble "
                  "under the exact current true-U1-conditioned channel, "
                  "then finite-L2 validation in a later packet"),
    }


def binomial_tail(p, y_obs=27, n=32):
    """Descriptive D16 tail ``T(p) = P(X <= 27 | n=32, p)`` (stdlib only).

    Description only; never a verdict revision. ``L055_VERDICT`` stays
    ``FALSIFIED`` regardless of these values.
    """
    p = float(p)
    if not 0.0 <= p <= 1.0:
        raise ValueError("p must be in [0,1], got %r" % (p,))
    return float(sum(math.comb(int(n), k) * p ** k * (1.0 - p) ** (int(n) - k)
                     for k in range(0, int(y_obs) + 1)))


# --------------------------------------------------------------------------- #
# Frozen candidate family (packet §4)
# --------------------------------------------------------------------------- #
N_REF = 128
LAYER = "L2"  # D18 is L2-only; APP/joint/L1 never enter dispatch
GRID_M = (89, 94, 99, 104, 109)
STAGE_S_M = (94, 104)
DV3_X = 0.0
DV3_CONTROL_ID = "lam_d2_0.00_d3_1.00"
DV3_BASELINE_DELTA_DE = 0.5468113653656221  # D17 A2 trusted comparator
ELIGIBILITY_DELTA_DE = 0.5077488653656221  # one n128 row step (5/128) below
ROW_STEP = 5.0 / 128.0  # 0.0390625 per row step


def candidate_xs():
    """Exactly 21 points x = 0.00..1.00 step 0.05."""
    return tuple(round(i * 0.05, 2) for i in range(21))


def candidate_id_for_x(x):
    """Accepted D8/D9 ID form ``lam_d2_<x:.2f>_d3_<1-x:.2f>``."""
    return "lam_d2_%.2f_d3_%.2f" % (float(x), 1.0 - float(x))


def lambda_edge_for_x(x):
    """Edge-perspective ``lambda={2:x, 3:1-x}`` (validated; no CE/f label)."""
    x = float(x)
    if x == 0.0:
        return d9.validate_lambda_edge({3: 1.0})
    if x == 1.0:
        return d9.validate_lambda_edge({2: 1.0})
    return d9.validate_lambda_edge({2: x, 3: 1.0 - x})


def enumerate_candidates():
    """The frozen 21-candidate family in x-ascending order."""
    out = []
    for x in candidate_xs():
        out.append({"candidate_id": candidate_id_for_x(x), "x": x,
                    "lambda_edge": lambda_edge_for_x(x),
                    "is_dv3_control": candidate_id_for_x(x) == DV3_CONTROL_ID})
    return out


def rate_for_m(m):
    """Exact ensemble rate ``R = 1 - m/128`` (reused D17 helper)."""
    return d17.rate_of(int(m))


def delta_for_m(m):
    """Disclosure gap ``delta = 5m/128 - H_L2`` (reused D17 axis)."""
    return d17.delta_of(int(m), N_REF, LAYER)


def rho_for(candidate_id, m):
    """Frozen D9 rho: ``make_rho`` at the exact rate (never hand-set)."""
    lam = lambda_edge_for_x(_x_of(candidate_id))
    return {int(k): float(v)
            for k, v in d9.make_rho(rate_for_m(m), lam).items()}


def _x_of(candidate_id):
    for cand in enumerate_candidates():
        if cand["candidate_id"] == str(candidate_id):
            return cand["x"]
    raise KeyError("unknown D18 candidate %r" % (candidate_id,))


def node_counts_for(candidate_id):
    """Largest-remainder variable counts + socket total at n=128."""
    counts = v37f.calculate_node_degree_counts(
        lambda_edge_for_x(_x_of(candidate_id)), n=N_REF)
    n2 = int(counts.get(2, 0))
    n3 = int(counts.get(3, 0))
    return {"n2": n2, "n3": n3, "E": 2 * n2 + 3 * n3}


def gate_cell(E, m, rho):
    """Frozen socket gate: invalid/min-dc<2/max-dc>8/rho-unnormalized.

    Returns ``(executable, refusal_reason)``; refusals are recorded, the
    candidate is never replaced.
    """
    E, m = int(E), int(m)
    if E <= 0 or m <= 0:
        return False, "invalid_realization: non-positive E=%d m=%d" % (E, m)
    if E // m < 2:
        return False, "min_dc<2: floor=%d E=%d m=%d" % (E // m, E, m)
    if (E + m - 1) // m > 8:
        return False, "max_dc>8: ceil=%d E=%d m=%d" % ((E + m - 1) // m, E, m)
    try:
        alloc = d17.check_allocation(E, m)
    except ValueError:
        return False, "invalid_realization: infeasible allocation E=%d m=%d" % (E, m)
    if sorted(alloc)[0] < 2 or sorted(alloc)[-1] > 8:
        return False, "invalid_realization: allocation outside [2,8] E=%d m=%d" % (E, m)
    try:
        total = float(sum(float(v) for v in dict(rho).values()))
    except (TypeError, ValueError):
        return False, "rho_unnormalized: non-numeric rho"
    if not math.isfinite(total) or abs(total - 1.0) > 1e-9:
        return False, "rho_unnormalized: sum=%.17g" % (total,)
    if any((not math.isfinite(float(v))) or float(v) < 0.0
           for v in dict(rho).values()):
        return False, "rho_unnormalized: negative/non-finite weight"
    return True, None


def feasibility_table():
    """Deterministic 21 x 5 feasibility table (105 cells, rho via D9 rule)."""
    rows = []
    for cand in enumerate_candidates():
        counts = node_counts_for(cand["candidate_id"])
        for m in GRID_M:
            rho = rho_for(cand["candidate_id"], m)
            alloc = None
            try:
                alloc = d17.check_allocation(counts["E"], int(m))
            except ValueError:
                alloc = None
            executable, reason = gate_cell(counts["E"], int(m), rho)
            rows.append({
                "candidate_id": cand["candidate_id"], "x": cand["x"],
                "m": int(m), "rate": rate_for_m(m), "delta": delta_for_m(m),
                "n2": counts["n2"], "n3": counts["n3"], "E": counts["E"],
                "check_counts": dict(alloc) if alloc else {},
                "max_check_degree": max(alloc) if alloc else None,
                "rho": dict(rho), "executable": bool(executable),
                "refusal_reason": reason})
    return rows


# --------------------------------------------------------------------------- #
# Frozen two-stage non-searching plan (packet §5)
# --------------------------------------------------------------------------- #
STAGE_S_SEEDS = tuple(range(2026094301, 2026094305))  # 4301..4304 (4)
STAGE_C_SEEDS = tuple(range(2026094301, 2026094309))  # 4301..4308 (8)
STAGE_S_POP = 4000
STAGE_C_POPS = (4000, 16000)
DE_MAX_ITER = 60
DE_ENTROPY_TOL_BITS = 1e-4
DE_STREAK = 20

T_SELECT_ONE = "D18_L2_DE_SELECT_ONE_ENSEMBLE"
T_NO_IMPROVING = "D18_L2_DE_NO_IMPROVING_ENSEMBLE"
T_BASELINE_DRIFT = "D18_L2_DE_BASELINE_DRIFT"
T_ENGINEERING_BLOCKED = "D18_L2_DE_ENGINEERING_BLOCKED"


def build_stage_s_plan(feasibility=None):
    """Stage S: 21 x {94,104} x 4 seeds x pop4000 = at most 168 calls.

    Deterministic order: candidate_id ascending -> m ascending -> seed
    ascending. ``call_idx`` 0..167 with no skips; refused cells are flagged
    and never executed.
    """
    feas = {(r["candidate_id"], r["m"]): r
            for r in (feasibility if feasibility is not None
                      else feasibility_table())}
    plan = []
    for cand in enumerate_candidates():
        for m in STAGE_S_M:
            row = feas[(cand["candidate_id"], int(m))]
            for seed in STAGE_S_SEEDS:
                plan.append({
                    "call_idx": len(plan), "stage": "S",
                    "candidate_id": cand["candidate_id"], "layer": LAYER,
                    "m": int(m), "rate": row["rate"], "delta": row["delta"],
                    "population": STAGE_S_POP, "seed": int(seed),
                    "refused": not row["executable"],
                    "refusal_reason": row["refusal_reason"]})
    return plan


def stage_s_identity(entry):
    """Overlap identity reused by Stage C (never rerun)."""
    return (entry["candidate_id"], int(entry["m"]), int(entry["population"]),
            int(entry["seed"]))


def build_stage_c_plan(selected_ids, feasibility=None):
    """Stage C: selected 4 only, full 5-m grid, 8 seeds, pops {4000,16000}.

    320 identities; the 32 Stage-S identities of the selected candidates
    are flagged ``reused`` and SHALL never be rerun. Rank-only selection:
    no substitution, extension, search, or extra seed.
    """
    selected = sorted(str(c) for c in selected_ids)
    if len(selected) != 4 or len(set(selected)) != 4:
        raise ValueError("Stage C needs exactly 4 distinct selected ids")
    known = {c["candidate_id"] for c in enumerate_candidates()}
    for cid in selected:
        if cid not in known:
            raise ValueError("unknown D18 candidate %r" % (cid,))
    feas = {(r["candidate_id"], r["m"]): r
            for r in (feasibility if feasibility is not None
                      else feasibility_table())}
    s_identities = {stage_s_identity(e) for e in build_stage_s_plan(
        feasibility if feasibility is not None else feasibility_table())
        if e["candidate_id"] in set(selected)}
    plan = []
    for cid in selected:
        for m in GRID_M:
            row = feas[(cid, int(m))]
            for pop in STAGE_C_POPS:
                for seed in STAGE_C_SEEDS:
                    key = (cid, int(m), int(pop), int(seed))
                    plan.append({
                        "call_idx": len(plan), "stage": "C",
                        "candidate_id": cid, "layer": LAYER,
                        "m": int(m), "rate": row["rate"], "delta": row["delta"],
                        "population": int(pop), "seed": int(seed),
                        "refused": not row["executable"],
                        "refusal_reason": row["refusal_reason"],
                        "reused": key in s_identities})
    return plan


def stage_counts():
    """Frozen arithmetic: 168 / 320 / 32-overlap / 288-new / 456-total."""
    s = len(build_stage_s_plan())
    c = len(build_stage_c_plan(
        [c["candidate_id"] for c in enumerate_candidates()[:4]]))
    overlap = 4 * len(STAGE_S_M) * len(STAGE_S_SEEDS) * 1  # 32
    return {"stage_s_max": s, "stage_c_identities": c,
            "overlap_reused": overlap, "stage_c_new_max": c - overlap,
            "total_ceiling": s + (c - overlap)}


def summarize_stage_s(records):
    """Per-candidate Stage-S summaries: S_m94/S_m104 + worst H60s."""
    out = {}
    for cand in enumerate_candidates():
        cid = cand["candidate_id"]
        row = {"candidate_id": cid}
        for m in STAGE_S_M:
            got = [r for r in records if r["candidate_id"] == cid
                   and int(r["m"]) == int(m)]
            row["S_m%d" % m] = sum(1 for r in got if r["converged"])
            row["calls_m%d" % m] = len(got)
            row["worst_H60_m%d" % m] = max(
                (float(r["h60"]) for r in got), default=None)
        out[cid] = row
    return out


def rank_stage_s(summaries, executable_ids):
    """Frozen rank: (S_m94 DESC, S_m104 DESC, worst_H60_m94 ASC,
    worst_H60_m104 ASC, candidate_id ASC)."""
    rows = [summaries[cid] for cid in executable_ids if cid in summaries]
    for cid in executable_ids:
        if summaries[cid]["calls_m94"] != len(STAGE_S_SEEDS) or \
                summaries[cid]["calls_m104"] != len(STAGE_S_SEEDS):
            raise ValueError("candidate %s Stage-S incomplete" % (cid,))
    return [r["candidate_id"] for r in sorted(
        rows, key=lambda r: (-r["S_m94"], -r["S_m104"],
                             r["worst_H60_m94"], r["worst_H60_m104"],
                             r["candidate_id"]))]


def select_stage_s(summaries, executable_ids):
    """Exactly the top three non-DV3 plus DV3; <3 executable non-DV3 or a
    refused DV3 returns engineering-blocked (no family widening)."""
    ranked = rank_stage_s(
        summaries, [c for c in executable_ids if c in summaries])
    non_dv3 = [c for c in ranked if c != DV3_CONTROL_ID]
    if DV3_CONTROL_ID not in set(executable_ids):
        return {"selected": [], "terminal": T_ENGINEERING_BLOCKED,
                "reason": "DV3 control not executable"}
    if len(non_dv3) < 3:
        return {"selected": [], "terminal": T_ENGINEERING_BLOCKED,
                "reason": "fewer than three executable non-DV3"}
    return {"selected": non_dv3[:3] + [DV3_CONTROL_ID], "terminal": None,
            "reason": None}


def candidate_bracket(s16000, s4000=None):
    """D17's exact bracket rule over the frozen D18 5-m grid.

    Same ``S_LO_MAX/S_HI_MIN`` thresholds and same
    ``DE_BRACKET/DE_SOFT_BRACKET/DE_ONE_SIDED_*/POP_UNSTABLE`` flags;
    applied to one candidate (never re-gridded). Proven identical to
    ``d17.bracket_delta_de("L2", ...)`` for shared counts by test.
    """
    deltas = {m: delta_for_m(m) for m in GRID_M}
    los = [m for m in GRID_M if int(s16000[m]) <= d17.S_LO_MAX]
    his = [m for m in GRID_M if int(s16000[m]) >= d17.S_HI_MIN]
    if not los and his:
        lo = min(GRID_M, key=lambda m: deltas[m])
        primary = {"delta_de": deltas[lo], "h": None,
                   "flag": d17.F_ONE_SIDED_LOW, "lo_m": None, "hi_m": lo}
    elif not his and los:
        hi = max(GRID_M, key=lambda m: deltas[m])
        primary = {"delta_de": deltas[hi], "h": None,
                   "flag": d17.F_ONE_SIDED_HIGH, "lo_m": hi, "hi_m": None}
    elif not los or not his:
        raise ValueError("no <=3/>=6 bracket pair (recorded, never re-gridded)")
    else:
        lo_m = max(los, key=lambda m: deltas[m])
        hi_m = min(his, key=lambda m: deltas[m])
        if not deltas[hi_m] > deltas[lo_m]:
            raise ValueError("non-monotone S bracket (fail-closed)")
        h = (deltas[hi_m] - deltas[lo_m]) / 2.0
        middle = [m for m in GRID_M
                  if d17.S_LO_MAX < int(s16000[m]) < d17.S_HI_MIN]
        flag = d17.F_SOFT_BRACKET if middle else d17.F_BRACKET
        primary = {"delta_de": (deltas[lo_m] + deltas[hi_m]) / 2.0, "h": h,
                   "flag": flag, "lo_m": lo_m, "hi_m": hi_m}
    flags = [primary["flag"]]
    if s4000 is not None:
        try:
            check = candidate_bracket(s4000)
            if (check["lo_m"], check["hi_m"]) != (primary["lo_m"],
                                                  primary["hi_m"]):
                flags.append(d17.F_POP_UNSTABLE)
        except ValueError:
            flags.append(d17.F_POP_UNSTABLE)
    primary["flags"] = flags
    return primary


def decide(selected_ids, records_c, feasibility=None):
    """Eligibility + winner + terminal over the selected four.

    Brackets recomputed at pop16000 with D17's exact rules. Eligible iff
    clean stable ``DE_BRACKET`` + no refusal + ``delta_DE`` <= frozen
    threshold. Rank eligible non-DV3 by (delta_DE ASC, worst_H60_at_hi
    ASC, max_check_degree ASC, candidate_id ASC). One winner only.
    """
    feas = {(r["candidate_id"], r["m"]): r
            for r in (feasibility if feasibility is not None
                      else feasibility_table())}
    brackets, refused, s16_all, s4_all = {}, {}, {}, {}
    for cid in selected_ids:
        refused[cid] = [r for r in feas.values()
                        if r["candidate_id"] == cid and not r["executable"]]
        s16, s4 = {}, {}
        for m in GRID_M:
            got16 = [r for r in records_c if r["candidate_id"] == cid
                     and int(r["m"]) == int(m) and int(r["population"]) == 16000]
            got4 = [r for r in records_c if r["candidate_id"] == cid
                    and int(r["m"]) == int(m) and int(r["population"]) == 4000]
            s16[m] = sum(1 for r in got16 if r["converged"])
            s4[m] = sum(1 for r in got4 if r["converged"])
        s16_all[cid], s4_all[cid] = s16, s4
        try:
            brackets[cid] = candidate_bracket(s16, s4)
        except ValueError as ex:
            brackets[cid] = {"delta_de": None, "h": None, "flag": "NO_BRACKET",
                             "lo_m": None, "hi_m": None, "flags": ["NO_BRACKET"],
                             "error": str(ex)}
    dv3 = brackets[DV3_CONTROL_ID]
    drift = (dv3["flag"] != d17.F_BRACKET
             or d17.F_POP_UNSTABLE in dv3.get("flags", [])
             or (dv3["lo_m"], dv3["hi_m"]) != (94, 99))
    eligible = []
    for cid in selected_ids:
        if cid == DV3_CONTROL_ID:
            continue
        b = brackets[cid]
        if b["flag"] != d17.F_BRACKET:
            continue
        if d17.F_POP_UNSTABLE in b.get("flags", []):
            continue
        if refused[cid]:
            continue
        if b["delta_de"] is None or b["delta_de"] > ELIGIBILITY_DELTA_DE:
            continue
        hi = b["hi_m"]
        at_hi = [float(r["h60"]) for r in records_c
                 if r["candidate_id"] == cid and int(r["m"]) == int(hi)
                 and int(r["population"]) == 16000]
        max_dc = max(r["max_check_degree"] for r in feas.values()
                     if r["candidate_id"] == cid)
        eligible.append({"candidate_id": cid, "delta_de": b["delta_de"],
                         "worst_H60_at_hi": max(at_hi) if at_hi else None,
                         "max_check_degree": max_dc})
    eligible.sort(key=lambda e: (e["delta_de"], e["worst_H60_at_hi"],
                                 e["max_check_degree"], e["candidate_id"]))
    if drift:
        terminal = T_BASELINE_DRIFT
        winner = None
    elif eligible:
        terminal = T_SELECT_ONE
        winner = eligible[0]["candidate_id"]
    else:
        terminal = T_NO_IMPROVING
        winner = None
    return {"terminal": terminal, "winner_candidate_id": winner,
            "eligible": eligible, "brackets": brackets,
            "baseline_drift": bool(drift),
            "dv3_baseline": DV3_BASELINE_DELTA_DE}


# --------------------------------------------------------------------------- #
# Channel dispatch (L2-only; APP/joint/L1 never enter)
# --------------------------------------------------------------------------- #
def resolve_sampler(channel, profile="L2"):
    """Explicit per-call L2-oracle dispatch (fail-closed, pre-call).

    ``channel`` MUST map ``"L2"`` to the layer-tagged L2 oracle callable.
    Any APP/joint/L1 entry or shared callable is refused. D18 candidates
    are L2-only, so only ``"L2"`` resolves.
    """
    if str(profile) != "L2":
        raise ValueError("D18 is L2-only; refusing profile %r (no APP/joint/L1)"
                         % (profile,))
    if not isinstance(channel, dict) or "L2" not in channel:
        raise ValueError("channel must map 'L2' to the layer-tagged oracle")
    sampler = channel["L2"]
    if not callable(sampler):
        raise TypeError("L2 sampler must be callable")
    if getattr(sampler, "_d17_layer", None) != "L2":
        raise ValueError("L2 sampler must carry the explicit _d17_layer='L2' tag")
    for key, other in channel.items():
        if key != "L2" and other is sampler:
            raise ValueError("shared callable across profiles is forbidden")
    return sampler


def verify_reuse_identity():
    """Callable identity/signature + current-channel entropy constants.

    Proves the reused production path is identical to corrected D17
    (binder signatures, Q/POLY, H_L2, V26 params, channel constants).
    """
    bound_names = {"make_rho": ["rate", "lambda_edge"],
                   "de_call": ["lambda_edge", "rho_edge", "channel_sampler",
                               "seed", "n_samples"],
                   "load_channel": ["model_f_root"],
                   "build_sampler": ["pb", "p_f", "p1"],
                   "conditionalize": ["p_f"],
                   "oracle_mixer": ["p2", "bob_symbols", "u1_true"]}
    import inspect as _inspect
    bound = d17.bind_production_de()
    sig_ok = {}
    for name, required in bound_names.items():
        params = _inspect.signature(bound[name]).parameters
        sig_ok[name] = all(p in params for p in required)
    channel = d17.verify_channel_identity()
    checks = {
        "binder_signatures": all(sig_ok.values()),
        "channel_constants": bool(channel["passed"]),
        "Q_POLY": (d9.Q, d9.POLY) == (32, 37),
        "H_L2_identity": d17.H_L2 == 3.222719884634378,
        "V26_params": (d9.MAX_ITER, d9.ENTROPY_TOL_BITS, d9.STREAK) == (60, 1e-4, 20),
        "D18_kernel_params": (DE_MAX_ITER, DE_ENTROPY_TOL_BITS, DE_STREAK) == (60, 1e-4, 20),
        "L2_builder_identity": d17.build_l2_oracle_sampler is not None,
        "dv3_baseline_identity": DV3_BASELINE_DELTA_DE == d17.A3_DELTA_DE["L2"][0],
        "threshold_arithmetic": abs(
            (DV3_BASELINE_DELTA_DE - ROW_STEP) - ELIGIBILITY_DELTA_DE) < 1e-18,
    }
    return {"passed": all(checks.values()), "checks": checks,
            "signatures": sig_ok, "channel": channel}


# --------------------------------------------------------------------------- #
# E05 freeze: seeds / root / command / budgets
# --------------------------------------------------------------------------- #
FUTURE_ROOT = ("workspace/d18_l2_ensemble_de_"
               "98abed5a-af4f-4780-9e83-54cccba28901")
MODEL_F_INPUT_ROOT = d17.MODEL_F_INPUT_ROOT
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d18_ensemble_development.py --de-sweep "
    "--execution-authorized --model-f-root %s --out-root %s"
    % (MODEL_F_INPUT_ROOT, FUTURE_ROOT))
MAX_DE_CALLS = 456
MAX_SETUP_CALLS = 16
SETUP_UNITS = 4  # channel load, plan build, identity proof, feasibility audit
WALL_BUDGET_S = 1800.0
PER_CALL_BUDGET_S = 300.0
RSS_BUDGET_BYTES = 2 * 1024 ** 3

EVIDENCE_FILES = ("manifest.json", "de_plan.csv", "de_records.csv",
                  "de_traces.csv", "summary.json", "command_log.txt")
DE_RECORD_COLUMNS = ("call_idx", "stage", "candidate_id", "m", "rate",
                     "population", "seed", "converged", "iterations", "h60",
                     "reused", "wall_s")


def _sibling(name):
    return importlib.import_module("comparison_bench.formal_ir." + name)


def collect_prior_seeds():
    """All predecessor + banned + D17/D9 seed sets D18 must avoid."""
    r2 = _sibling("v72p2d10_mixed_degree_l1")
    r3 = _sibling("v72p2d10_r3_fresh_scaling")
    d11 = _sibling("v72p2d11_forward_app")
    d12 = _sibling("v72p2d12_finite_l1_degree")
    d14n = _sibling("v72p2d14n_calibrated_discriminator")
    d15 = _sibling("v72p2d15_margin_curve")
    d16 = _sibling("v72p2d16_matched_backoff")
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
    banned = set(d17.BANNED_SEEDS)
    d17seeds = set(d17.DE_SEEDS) | {d17.BOOTSTRAP_SEED}
    d9seeds = (set(d9.DE_SEEDS) | set(getattr(d9, "FRESH_SEEDS", ()))
               | set(getattr(d9, "D8_REPRODUCTION_SEEDS", ())))
    return {"prior": prior, "banned": banned, "d17": d17seeds, "d9": d9seeds}


def verify_seed_disjointness():
    """Prove D18 seeds disjoint from every prior/banned/D17/D9 seed."""
    sets = collect_prior_seeds()
    de = set(STAGE_C_SEEDS)
    hits = {k: sorted(de & v) for k, v in sets.items()}
    ok = all(not h for h in hits.values()) and len(de) == 8 \
        and set(STAGE_S_SEEDS) < de
    return {"passed": bool(ok), "de_seeds": sorted(de),
            "stage_s_seeds": sorted(STAGE_S_SEEDS), "hits": hits}


def describe_plan():
    """Pure plan/candidate arithmetic + absence proofs for PROFILE_ONLY.

    Zero DE/decoder calls; touches no kernel, binder, Model-F content,
    and creates no root.
    """
    feas = feasibility_table()
    table = [{"candidate_id": r["candidate_id"], "m": r["m"], "rate": r["rate"],
              "delta": r["delta"], "E": r["E"],
              "check_counts": r["check_counts"], "rho": r["rho"],
              "executable": r["executable"],
              "refusal_reason": r["refusal_reason"]} for r in feas]
    counts = stage_counts()
    return {
        "change_id": CHANGE_ID, "cycle": CYCLE_ID, "track": TRACK,
        "claim_ceiling": CLAIM_CEILING,
        "adjudication": adjudication_record(),
        "candidates": [c["candidate_id"] for c in enumerate_candidates()],
        "dv3_control": DV3_CONTROL_ID, "grid_m": list(GRID_M),
        "stage_s_m": list(STAGE_S_M),
        "stage_s_seeds": list(STAGE_S_SEEDS),
        "stage_c_seeds": list(STAGE_C_SEEDS),
        "stage_s_pop": STAGE_S_POP, "stage_c_pops": list(STAGE_C_POPS),
        "de_params": {"max_iter": DE_MAX_ITER,
                      "entropy_tol_bits": DE_ENTROPY_TOL_BITS,
                      "streak": DE_STREAK,
                      "convergence_rule": "S=#{H60<1e-4} over seeds"},
        "feasibility": table,
        "executable_cells": sum(1 for r in feas if r["executable"]),
        "refused_cells": sum(1 for r in feas if not r["executable"]),
        "counts": counts,
        "selection_rule": ("S_m94 DESC, S_m104 DESC, worst_H60_m94 ASC, "
                           "worst_H60_m104 ASC, candidate_id ASC; top-3 "
                           "non-DV3 + DV3"),
        "eligibility": ("clean stable DE_BRACKET + no refusal + delta_DE <= "
                        "%r" % (ELIGIBILITY_DELTA_DE,)),
        "terminals": [T_SELECT_ONE, T_NO_IMPROVING, T_BASELINE_DRIFT,
                      T_ENGINEERING_BLOCKED],
        "budgets": {"de_calls": MAX_DE_CALLS, "setup": MAX_SETUP_CALLS,
                    "wall_s": WALL_BUDGET_S, "per_call_s": PER_CALL_BUDGET_S,
                    "rss_bytes": RSS_BUDGET_BYTES, "processes": 1,
                    "retry": False, "resume": False, "seed_search": False,
                    "adaptive": False},
        "future_root": FUTURE_ROOT,
        "future_root_absent": not Path(FUTURE_ROOT).exists(),
        "frozen_command": FROZEN_COMMAND,
        "authorization": AUTHORIZATION,
        "de_calls": 0, "decoder_calls": 0,
    }


# --------------------------------------------------------------------------- #
# Sweep orchestrator (authorized path only; tests inject fakes)
# --------------------------------------------------------------------------- #
def _execute(entry, channel, de_call, rho):
    sampler = resolve_sampler(channel, entry.get("layer", "L2"))
    result = de_call(dict(lambda_edge_for_x(_x_of(entry["candidate_id"]))),
                     dict(rho), sampler, int(entry["seed"]),
                     int(entry["population"]))
    trace = [float(x) for x in result["entropy_trace_bits"]]
    metrics = d9.trajectory_metrics(trace)
    return trace, metrics


def run_de_sweep(out_root, model_f_root, *, channel=None, de_call=None,
                 rho_fn=None, now_fn=None, rss_fn=None, feasibility=None):
    """Execute Stage S then the mechanically selected Stage C (no writes).

    ``channel``/``de_call``/``rho_fn`` must be explicitly injected (fakes
    on the test path); any ``None`` production-binds inside, AFTER plan
    validation and the fresh-root probe. The 32 Stage-S identities of the
    selected candidates are reused, never rerun. Creates no files.
    """
    feas = feasibility_table() if feasibility is None else feasibility
    plan_s = build_stage_s_plan(feas)
    if len(plan_s) != 168:
        raise ValueError("Stage-S plan has %d entries, frozen 168" % len(plan_s))
    resolved = d17.probe_fresh_root(out_root)  # probe only; creates nothing
    bound = None
    if channel is None or de_call is None or rho_fn is None:
        bound = d17.bind_production_de()
        if channel is None:
            channel = d17.build_production_channels(model_f_root, bound=bound)
        if de_call is None:
            de_call = bound["de_call"]
        if rho_fn is None:
            rho_fn = (lambda cid, m: bound["make_rho"](
                rate_for_m(m), dict(lambda_edge_for_x(_x_of(cid)))))
    now = now_fn or time.monotonic
    rss_fn = rss_fn or (lambda: 0)
    t0 = float(now())
    log_lines = []
    records, traces = [], []
    engineering_reason = ""

    rhos = {}
    for row in feas:
        rhos[(row["candidate_id"], row["m"])] = dict(
            rho_fn(row["candidate_id"], row["m"]))

    for entry in plan_s:
        if entry["refused"]:
            continue
        start = float(now())
        try:
            trace, metrics = _execute(
                entry, channel, de_call,
                rhos[(entry["candidate_id"], entry["m"])])
        except Exception as exc:  # failure retention, no retry, stop
            engineering_reason = "DE_CALL_FAILED@S%d: %s: %s" % (
                entry["call_idx"], type(exc).__name__, exc)
            break
        wall = float(now()) - start
        records.append({
            "call_idx": entry["call_idx"], "stage": "S",
            "candidate_id": entry["candidate_id"], "m": entry["m"],
            "rate": entry["rate"], "population": entry["population"],
            "seed": entry["seed"], "converged": bool(metrics.converged),
            "iterations": len(trace), "h60": float(metrics.H60),
            "reused": False, "wall_s": wall})
        traces.append({
            "candidate_id": entry["candidate_id"], "m": entry["m"],
            "population": entry["population"], "seed": entry["seed"],
            "entropy_trace_bits": json.dumps(trace)})
        if wall > PER_CALL_BUDGET_S:
            engineering_reason = "PER_CALL_BUDGET@S%d" % entry["call_idx"]
            break

    refused_s = {f["candidate_id"] for f in feas
                 if f["m"] in STAGE_S_M and not f["executable"]}
    executable = sorted(c["candidate_id"] for c in enumerate_candidates()
                        if c["candidate_id"] not in refused_s)
    summaries = summarize_stage_s(records) if not engineering_reason else {}
    selection = {"selected": [], "terminal": T_ENGINEERING_BLOCKED,
                 "reason": engineering_reason or "plan incomplete"}
    if not engineering_reason:
        try:
            selection = select_stage_s(summaries, executable)
        except ValueError as exc:
            selection = {"selected": [], "terminal": T_ENGINEERING_BLOCKED,
                         "reason": str(exc)}

    plan_c, decision = [], None
    if selection["terminal"] is None:
        plan_c = build_stage_c_plan(selection["selected"], feas)
        reused_lookup = {(r["candidate_id"], r["m"], r["population"], r["seed"]): r
                         for r in records}
        for entry in plan_c:
            if entry["refused"] or entry["reused"]:
                continue
            start = float(now())
            try:
                trace, metrics = _execute(
                    entry, channel, de_call,
                    rhos[(entry["candidate_id"], entry["m"])])
            except Exception as exc:
                engineering_reason = "DE_CALL_FAILED@C%d: %s: %s" % (
                    entry["call_idx"], type(exc).__name__, exc)
                selection = {"selected": selection["selected"],
                             "terminal": T_ENGINEERING_BLOCKED,
                             "reason": engineering_reason}
                break
            wall = float(now()) - start
            records.append({
                "call_idx": entry["call_idx"], "stage": "C",
                "candidate_id": entry["candidate_id"], "m": entry["m"],
                "rate": entry["rate"], "population": entry["population"],
                "seed": entry["seed"], "converged": bool(metrics.converged),
                "iterations": len(trace), "h60": float(metrics.H60),
                "reused": False, "wall_s": wall})
            traces.append({
                "candidate_id": entry["candidate_id"], "m": entry["m"],
                "population": entry["population"], "seed": entry["seed"],
                "entropy_trace_bits": json.dumps(trace)})
            if wall > PER_CALL_BUDGET_S:
                engineering_reason = "PER_CALL_BUDGET@C%d" % entry["call_idx"]
                selection = {"selected": selection["selected"],
                             "terminal": T_ENGINEERING_BLOCKED,
                             "reason": engineering_reason}
                break
        if selection["terminal"] is None:
            for entry in plan_c:
                if entry["refused"] or not entry["reused"]:
                    continue
                src = reused_lookup.get(
                    (entry["candidate_id"], entry["m"], entry["population"],
                     entry["seed"]))
                if src is None:
                    selection = {"selected": selection["selected"],
                                 "terminal": T_ENGINEERING_BLOCKED,
                                 "reason": "overlap identity missing for rerun "
                                           "refusal check"}
                    break
            else:
                records_c = [r for r in records
                             if r["candidate_id"] in set(selection["selected"])]
                decision = decide(selection["selected"], records_c, feas)
                selection = {"selected": selection["selected"],
                             "terminal": decision["terminal"],
                             "reason": None, "decision": decision}

    terminal = selection["terminal"] or T_ENGINEERING_BLOCKED
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn())
    violations = []
    if wall_s > WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if peak_rss >= RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")
    manifest = {
        "schema": "v72p2d18_ensemble_de_manifest_v1",
        "change_id": CHANGE_ID, "cycle": CYCLE_ID, "track": FUTURE_TRACK,
        "claim_ceiling": CLAIM_CEILING, "command": FROZEN_COMMAND,
        "model_f_root": str(model_f_root), "out_root": str(resolved),
        "grid_m": list(GRID_M), "stage_s_m": list(STAGE_S_M),
        "stage_s_seeds": list(STAGE_S_SEEDS),
        "stage_c_seeds": list(STAGE_C_SEEDS),
        "populations": list(STAGE_C_POPS),
        "de_params": {"max_iter": DE_MAX_ITER,
                      "entropy_tol_bits": DE_ENTROPY_TOL_BITS,
                      "streak": DE_STREAK},
        "budgets": {"de_calls": MAX_DE_CALLS, "setup": MAX_SETUP_CALLS,
                    "wall_s": WALL_BUDGET_S, "per_call_s": PER_CALL_BUDGET_S,
                    "rss_bytes": RSS_BUDGET_BYTES, "processes": 1,
                    "retry": False, "resume": False, "seed_search": False,
                    "adaptive": False},
        "setup_calls": SETUP_UNITS,
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": AUTHORIZATION,
    }
    summary = {
        "schema": "v72p2d18_ensemble_de_summary_v1",
        "change_id": CHANGE_ID, "terminal": terminal,
        "engineering_reason": engineering_reason or selection.get("reason", ""),
        "selected": selection["selected"],
        "winner_candidate_id": (selection.get("decision") or {}).get(
            "winner_candidate_id"),
        "decision": selection.get("decision"),
        "scientific_calls": len(records),
        "planned_ceiling": MAX_DE_CALLS, "setup_calls": SETUP_UNITS,
        "wall_s": wall_s, "peak_rss_bytes": peak_rss,
        "budget_violations": violations,
        "model_f_root": str(model_f_root), "out_root": str(resolved),
    }
    return {"resolved": resolved, "manifest": manifest, "plan_s": plan_s,
            "plan_c": plan_c, "records": records, "traces": traces,
            "summary": summary, "log_lines": log_lines}


def write_de_root(bundle):
    """Never-overwrite writer: exactly the six evidence files."""
    out = Path(str(bundle["resolved"]))
    if out.exists():
        raise FileExistsError("refusing to overwrite existing root %s" % out)
    out.mkdir(parents=True)
    logfh = open(out / "command_log.txt", "w", encoding="utf-8")
    try:
        with open(out / "manifest.json", "w", encoding="utf-8") as fh:
            json.dump(bundle["manifest"], fh, indent=2, sort_keys=True)
            fh.write("\n")
        with open(out / "de_plan.csv", "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh, fieldnames=["stage", "call_idx", "candidate_id", "m",
                                "population", "seed", "refused", "reused"])
            writer.writeheader()
            for entry in bundle["plan_s"] + bundle["plan_c"]:
                writer.writerow({k: entry.get(k, "") for k in
                                 ["stage", "call_idx", "candidate_id", "m",
                                  "population", "seed", "refused", "reused"]})
        with open(out / "de_records.csv", "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(DE_RECORD_COLUMNS))
            writer.writeheader()
            for rec in bundle["records"]:
                writer.writerow({k: rec.get(k, "") for k in DE_RECORD_COLUMNS})
        with open(out / "de_traces.csv", "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh, fieldnames=["candidate_id", "m", "population", "seed",
                                "entropy_trace_bits"])
            writer.writeheader()
            for tr in bundle["traces"]:
                writer.writerow(tr)
        with open(out / "summary.json", "w", encoding="utf-8") as fh:
            json.dump(bundle["summary"], fh, indent=2, sort_keys=True)
            fh.write("\n")
        logfh.write("terminal=%s calls=%d\n" % (
            bundle["summary"]["terminal"],
            bundle["summary"]["scientific_calls"]))
    finally:
        logfh.close()
    names = sorted(p.name for p in out.iterdir())
    if names != sorted(EVIDENCE_FILES):
        raise RuntimeError("root must contain exactly %s, got %s"
                           % (sorted(EVIDENCE_FILES), names))
    return bundle["summary"]


def verify_de_root(out_root, rho_fn=None):
    """Read-only recomputation from ``de_traces.csv`` (zero DE calls).

    Recomputes H60/converged per group, Stage-S rank/selection, brackets,
    eligibility, and the terminal; FAILs on any mismatch, partial plan, or
    engineering-blocked root. Writes nothing.
    """
    out = Path(str(out_root))
    if not out.is_dir():
        print("VERIFY FAIL missing root %s" % out)
        return False
    violations = []
    try:
        names = sorted(p.name for p in out.iterdir())
    except OSError as ex:
        print("VERIFY FAIL unreadable root: %r" % (ex,))
        return False
    if names != sorted(EVIDENCE_FILES):
        violations.append("root files %s" % (names,))
        print("VERIFY FAIL root files %s" % (names,))
        return False
    try:
        with open(out / "de_traces.csv", newline="", encoding="utf-8") as fh:
            traces = list(csv.DictReader(fh))
        with open(out / "de_records.csv", newline="", encoding="utf-8") as fh:
            records = list(csv.DictReader(fh))
        with open(out / "summary.json", encoding="utf-8") as fh:
            summary = json.load(fh)
    except (OSError, ValueError) as ex:
        print("VERIFY FAIL unreadable evidence: %r" % (ex,))
        return False

    feas = feasibility_table()
    plan_s = build_stage_s_plan(feas)
    expected_s = {(e["candidate_id"], e["m"], e["population"], e["seed"])
                  for e in plan_s if not e["refused"]}
    stored_keys = [(r["candidate_id"], int(r["m"]), int(r["population"]),
                    int(r["seed"])) for r in records]
    if len(set(stored_keys)) != len(stored_keys):
        violations.append("duplicate record identities (overlap rerun?)")
    trace_keys = set()
    recomputed = []
    for tr in traces:
        key = (tr["candidate_id"], int(tr["m"]), int(tr["population"]),
               int(tr["seed"]))
        trace_keys.add(key)
        matches = [r for r in records if (r["candidate_id"], int(r["m"]),
                                          int(r["population"]), int(r["seed"])) == key]
        if len(matches) != 1:
            violations.append("trace without exactly one record: %s" % (key,))
            continue
        try:
            trace = json.loads(tr["entropy_trace_bits"])
            metrics = d9.trajectory_metrics([float(x) for x in trace])
        except (ValueError, TypeError) as ex:
            violations.append("unrecomputable trace %s: %r" % (key, ex))
            continue
        stored = matches[0]
        if stored["converged"] != str(bool(metrics.converged)):
            violations.append("converged mismatch %s" % (key,))
        if abs(float(stored["h60"]) - float(metrics.H60)) > 1e-12:
            violations.append("h60 mismatch %s" % (key,))
        recomputed.append({"candidate_id": key[0], "m": key[1],
                           "population": key[2], "seed": key[3],
                           "converged": bool(metrics.converged),
                           "h60": float(metrics.H60),
                           "stage": stored.get("stage", "")})
    for key in expected_s:
        if key not in trace_keys and summary.get("terminal") != T_ENGINEERING_BLOCKED:
            violations.append("missing Stage-S identity %s" % (key,))
    for r in records:
        if "exact" in r or "syndrome" in r or "undetected" in r:
            violations.append("forbidden exact/syndrome/undetected column")

    if summary.get("terminal") != T_ENGINEERING_BLOCKED:
        try:
            rec_s = [r for r in recomputed if r.get("stage") == "S"]
            if not rec_s:
                rec_s = [r for r in recomputed
                         if r["population"] == STAGE_S_POP
                         and r["m"] in STAGE_S_M]
            summaries = summarize_stage_s(
                [{"candidate_id": r["candidate_id"], "m": r["m"],
                  "converged": r["converged"], "h60": r["h60"]}
                 for r in rec_s])
            refused_s = {f["candidate_id"] for f in feas
                         if f["m"] in STAGE_S_M and not f["executable"]}
            executable = sorted(
                c["candidate_id"] for c in enumerate_candidates()
                if c["candidate_id"] not in refused_s)
            selection = select_stage_s(summaries, executable)
            if selection["selected"] != list(summary.get("selected", [])):
                violations.append("selection mismatch stored=%r recomputed=%r"
                                  % (summary.get("selected"),
                                     selection["selected"]))
            decision = selection.get("decision")
            if selection["terminal"] is None:
                records_c = [r for r in recomputed
                             if r["candidate_id"] in set(selection["selected"])]
                decision = decide(selection["selected"], records_c, feas)
                if decision["terminal"] != summary.get("terminal"):
                    violations.append("terminal mismatch stored=%r recomputed=%r"
                                      % (summary.get("terminal"),
                                         decision["terminal"]))
                if decision.get("winner_candidate_id") != summary.get(
                        "winner_candidate_id"):
                    violations.append("winner mismatch")
        except (ValueError, KeyError) as ex:
            violations.append("recomputation failed: %r" % (ex,))
    else:
        violations.append("engineering-blocked root never verifies PASS")
    ok = not violations
    print("VERIFY %s violations=%d" % ("PASS" if ok else "FAIL", len(violations)))
    for v in violations[:20]:
        print("  VIOLATION %s" % v)
    return ok
