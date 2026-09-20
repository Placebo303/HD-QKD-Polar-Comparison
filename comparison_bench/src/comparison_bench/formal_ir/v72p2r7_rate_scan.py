"""R7 synthetic DE rate-scan for the frozen L020 winner (S7 task, EXPLORE).

Frozen scope (operator packet, this session): single candidate
``lam_d2_0.20_d3_0.80`` (D18 winner; D19 proposal S1 non-reopening, DO NOT
retune) over ``m in {100,104,...,128}`` at ``n=128``; D18 threshold
bracketing protocol verbatim; ledger every DE call against a 200 cap;
per-feasible-m arithmetic sheets (D19 precedent) + PEG admission predicate
(stated, not executed) + fresh R7-S7 seed plan (constructed NOTHING).

Protocol ID (reused EXACTLY, nothing redeclared):
  - V26 MC-DE kernel via ``d9.run_de_call`` (``max_iter=60``, tol ``1e-4``,
    streak 20); convergence ``S = #{H60 < 1e-4}`` over seeds;
  - D17 exact bracket rule (``S_LO_MAX=3``/``S_HI_MIN=6``; midpoint/h;
    ``DE_BRACKET``/``DE_SOFT_BRACKET``/``DE_ONE_SIDED_*``/``POP_UNSTABLE``);
  - replicates 8 seeds x pops ``{4000, 16000}`` (D18 Stage-C rule);
  - corrected D17 R2 production L2-oracle channel only (true-U1
    conditioned, XOR-centered U2, Model-F, GF32/poly37); L2-only dispatch;
  - D9 ``make_rho`` at the exact rate ``R = 1 - m/128`` + frozen socket
    gate (refuse+record, never replace).
Frozen forward-decoder context (no decoder calls in this scan):
``DECODER_MAX_ITER=90`` / ``DAMPING_ALPHA=1.0`` (D17 frozen values).

Synthetic DE evidence only; no FER/recovery claim. No real-data contact,
no graph construction, no decoder runs. One fresh additive root; no
commit/push.

R8 downward micro-extension (additive only): every entry point accepts an
optional ``grid``/``cap`` override (``None`` = frozen R7 defaults above).
The ``--m-grid``/``--de-cap`` runner flags thread exactly these through;
nothing else changes (winner, protocol, bar, seeds, pops, decoder
context).
"""

from __future__ import annotations

import csv
import json
import math
import time
from pathlib import Path

from comparison_bench.formal_ir import v72p2d17_descaling as d17
from comparison_bench.formal_ir import v72p2d18_l2_ensemble_de as d18
from comparison_bench.formal_ir import v72p2d9_de_decoder_calibration as d9

CHANGE_ID = "v72p2r7-rate-scan"
CYCLE_ID = "R7-S7"
TRACK = "EXPLORE"
CLAIM_CEILING = ("synthetic DE evidence only; no FER/recovery/leakage/SKR/"
                 "qualification/promotion/publication/optimality/"
                 "route-closure claim")
AUTHORIZATION = ("operator frozen-scan grant, this session: synthetic only, "
                 "L020-winner x m{100..128} DE scan, 200-call cap, fresh "
                 "additive workspace root only")

# L020 winner, frozen (D18 SELECT_ONE; D19 S1 non-reopening; never retuned).
WINNER_ID = "lam_d2_0.20_d3_0.80"
WINNER_X = 0.20
WINNER_PRIOR_DELTA_DE = 0.35149886536562214  # D18 reviewed lo89/hi94 (prior only)

R7_GRID_M = (100, 104, 108, 112, 116, 120, 124, 128)
R7_N = 128
R7_DE_SEEDS = tuple(range(2026094701, 2026094709))  # 4701..4708 (8, fresh)
R7_POPS = (4000, 16000)
R7_DE_CAP = 200
R7_PLANNED_CALLS = len(R7_GRID_M) * len(R7_DE_SEEDS) * len(R7_POPS)  # 128

# R8 downward micro-extension (additive override only; R7 defaults above
# are untouched). Same winner/protocol/bar; grid m in {88,92,96}, cap 60.
R8_GRID_M = (88, 92, 96)
R8_DE_CAP = 60
R8_PLANNED_CALLS = len(R8_GRID_M) * len(R7_DE_SEEDS) * len(R7_POPS)  # 48


def _resolve_grid(grid):
    """None -> frozen R7 grid; otherwise the caller's tuple (verbatim)."""
    return R7_GRID_M if grid is None else tuple(int(m) for m in grid)


def _resolve_cap(cap):
    """None -> frozen R7 cap; otherwise the caller's int (verbatim)."""
    return R7_DE_CAP if cap is None else int(cap)

# T2 margin: frozen D18 one-row-step (design S5.3: eligibility is one n128
# row step below the reviewed DV3 threshold; 0.0390625 = 5/128). D19 adds
# no delta margin (count gates only).
MARGIN_DELTA = 0.0390625  # == d18.ROW_STEP; quoted, never re-derived

# T4 graph-seed pool (plan only; constructed NOTHING): <=3 graphs/m, <=9 total.
R7_GRAPH_SEED_POOL = tuple(range(2026094711, 2026094720))  # 4711..4719 (9)

FUTURE_ROOT = ("workspace/r7_rate_scan_"
               "719f77de-0e69-499f-80b4-397457c8958a")
FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2r7_rate_scan.py --de-sweep "
    "--execution-authorized --model-f-root %s --out-root %s"
    % (d17.MODEL_F_INPUT_ROOT, FUTURE_ROOT))

EVIDENCE_FILES = ("manifest.json", "de_plan.csv", "de_records.csv",
                  "de_traces.csv", "summary.json", "command_log.txt")

T_COMPLETE = "R7_S7_RATE_SCAN_COMPLETE"
T_INCOMPLETE_CAP = "R7_S7_INCOMPLETE_CAP"
T_ENGINEERING_BLOCKED = "R7_S7_ENGINEERING_BLOCKED"

# Explicit disjointness list (T4 seed plan; G6 4601/4602 included).
PRIOR_SEED_RANGES = {
    "d16_graphs": tuple(range(2026094001, 2026094013)),
    "d16_blocks": tuple(range(2026094101, 2026094109)),
    "d17_de": tuple(range(2026094201, 2026094209)),
    "d17_bootstrap": (2026094200,),
    "d18_de": tuple(range(2026094301, 2026094309)),
    "d19_graphs": tuple(range(2026094401, 2026094413)),
    "d19_blocks": tuple(range(2026094501, 2026094509)) + tuple(range(2026094511, 2026094519)),
    "g6_graphs": (2026094601, 2026094602),
}


def m124_equiv():
    """124-equivalent: disclosure gap delta at m=124, n=128, L2."""
    return d18.delta_for_m(124)


def bar_value():
    """T2 bar: 124-equivalent minus the frozen margin (strict inequality)."""
    return m124_equiv() - MARGIN_DELTA


def verify_seed_disjointness():
    """Prove R7 DE + graph seeds avoid every prior range incl. 4601/4602."""
    fresh = set(R7_DE_SEEDS) | set(R7_GRAPH_SEED_POOL)
    hits = {k: sorted(fresh & set(v)) for k, v in PRIOR_SEED_RANGES.items()}
    try:
        mod = d18.collect_prior_seeds()
        mod_hits = sorted(fresh & (set(mod["prior"]) | set(mod["banned"])
                                   | set(mod["d17"]) | set(mod["d9"])))
    except Exception:
        mod_hits = ["collect_failed"]
    ok = (all(not h for h in hits.values()) and not mod_hits
          and len(R7_DE_SEEDS) == 8 and len(R7_GRAPH_SEED_POOL) == 9
          and not (set(R7_DE_SEEDS) & set(R7_GRAPH_SEED_POOL)))
    return {"passed": bool(ok), "de_seeds": sorted(R7_DE_SEEDS),
            "graph_pool": sorted(R7_GRAPH_SEED_POOL), "range_hits": hits,
            "module_hits": mod_hits}


def feasibility_table(grid=None):
    """One frozen L020 row per grid m (D19-precedent arithmetic)."""
    grid = _resolve_grid(grid)
    counts = d18.node_counts_for(WINNER_ID)
    rows = []
    for m in grid:
        rho = d18.rho_for(WINNER_ID, int(m))
        try:
            alloc = d17.check_allocation(counts["E"], int(m))
        except ValueError:
            alloc = None
        executable, reason = d18.gate_cell(counts["E"], int(m), rho)
        rows.append({
            "candidate_id": WINNER_ID, "m": int(m),
            "rate": d18.rate_for_m(m), "delta": d18.delta_for_m(m),
            "n2": counts["n2"], "n3": counts["n3"], "E": counts["E"],
            "check_counts": dict(alloc) if alloc else {},
            "max_check_degree": max(alloc) if alloc else None,
            "rho": dict(rho), "executable": bool(executable),
            "refusal_reason": reason})
    return rows


def build_r7_plan(feasibility=None, grid=None):
    """128-call matrix: m asc -> pop asc -> seed asc; call_idx 0..127."""
    grid = _resolve_grid(grid)
    feas = {(r["candidate_id"], r["m"]): r
            for r in (feasibility if feasibility is not None
                      else feasibility_table(grid))}
    plan = []
    for m in grid:
        row = feas[(WINNER_ID, int(m))]
        for pop in R7_POPS:
            for seed in R7_DE_SEEDS:
                plan.append({
                    "call_idx": len(plan), "candidate_id": WINNER_ID,
                    "layer": d18.LAYER, "m": int(m), "rate": row["rate"],
                    "delta": row["delta"], "population": int(pop),
                    "seed": int(seed),
                    "refused": not row["executable"],
                    "refusal_reason": row["refusal_reason"]})
    return plan


def r7_bracket(s16000, s4000=None, grid=R7_GRID_M):
    """D17 exact bracket rule over the R7 grid (verbatim constants/flags).

    Proven identical to ``d17.bracket_delta_de`` / ``d18.candidate_bracket``
    on their own grids by test; never re-gridded adaptively.
    """
    deltas = {m: d18.delta_for_m(int(m)) for m in grid}
    los = [m for m in grid if int(s16000[m]) <= d17.S_LO_MAX]
    his = [m for m in grid if int(s16000[m]) >= d17.S_HI_MIN]
    if not los and his:
        lo = min(grid, key=lambda m: deltas[m])
        primary = {"delta_de": deltas[lo], "h": None,
                   "flag": d17.F_ONE_SIDED_LOW, "lo_m": None, "hi_m": lo}
    elif not his and los:
        hi = max(grid, key=lambda m: deltas[m])
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
        middle = [m for m in grid
                  if d17.S_LO_MAX < int(s16000[m]) < d17.S_HI_MIN]
        flag = d17.F_SOFT_BRACKET if middle else d17.F_BRACKET
        primary = {"delta_de": (deltas[lo_m] + deltas[hi_m]) / 2.0, "h": h,
                   "flag": flag, "lo_m": lo_m, "hi_m": hi_m}
    flags = [primary["flag"]]
    if s4000 is not None:
        try:
            check = r7_bracket(s4000, grid=grid)
            if (check["lo_m"], check["hi_m"]) != (primary["lo_m"],
                                                  primary["hi_m"]):
                flags.append(d17.F_POP_UNSTABLE)
        except ValueError:
            flags.append(d17.F_POP_UNSTABLE)
    primary["flags"] = flags
    return primary


def apply_bar(bracket, s16000, s4000, feasibility=None, grid=None):
    """T2 bar: PASS(m) iff threshold strictly below (124-equiv - margin).

    ``threshold`` is the T1 recomputed bracket ``delta_de``; per-m
    bracketing additionally requires the converged side (S>=6) on both
    pops at m and every larger grid m. Fail-closed: NO_BRACKET threshold
    (None) never passes.
    """
    grid = _resolve_grid(grid)
    feas = ({(r["candidate_id"], r["m"]): r for r in feasibility}
            if feasibility is not None
            else {(r["candidate_id"], r["m"]): r
                  for r in feasibility_table(grid)})
    threshold = bracket.get("delta_de")
    bar = bar_value()
    bar_holds = (threshold is not None
                 and math.isfinite(float(threshold))
                 and float(threshold) < float(bar))  # STRICT, direction exact
    per_m = {}
    for m in grid:
        tail = [x for x in grid if x >= m]
        ok = all(feas[(WINNER_ID, int(x))]["executable"]
                 and int(s16000[x]) >= d17.S_HI_MIN
                 and int(s4000[x]) >= d17.S_HI_MIN for x in tail)
        per_m[int(m)] = bool(bar_holds and ok)
    feasible = [m for m in grid if per_m[int(m)]]
    return {"threshold": threshold, "m124_equiv": m124_equiv(), "bar": bar,
            "margin_delta": MARGIN_DELTA, "bar_holds": bool(bar_holds),
            "pass": {str(k): v for k, v in per_m.items()},
            "min_m": min(feasible) if feasible else None,
            "terminal_m": (min(feasible) if feasible
                           else "NO-FEASIBLE-m")}


def arith_sheet(row):
    """Per-m arithmetic sheet (D19 precedent: rescaled counts + accounting)."""
    m = int(row["m"])
    rho = dict(row["rho"])
    alloc = dict(row["check_counts"])
    e_rho = {d: c * d / row["E"] for d, c in alloc.items()}
    return {
        "m": m, "n": R7_N, "arm": WINNER_ID,
        "variable_counts": {"2": row["n2"], "3": row["n3"]},
        "E": row["E"], "check_counts": alloc,
        "rate": row["rate"], "disclosed_bits_per_symbol": 5.0 * m / R7_N,
        "delta": row["delta"],
        "rho_edge_nominal": {str(k): v for k, v in rho.items()},
        "rho_edge_realized_check_alloc": {str(k): v for k, v in e_rho.items()},
        "mean_check_degree": row["E"] / m,
        "max_check_degree": row["max_check_degree"],
        "decoder_context": {"max_iter": d17.DECODER_MAX_ITER,
                            "damping": d17.DAMPING_ALPHA,
                            "note": "frozen forward context only; "
                                    "zero decoder calls in R7"},
        "peg_admission_predicate": (
            "STATED, NOT EXECUTED: reuse the accepted D10-R2 "
            "connectivity-first build_degree_sequence_peg with the frozen "
            "degree profile above; one deterministic coefficient namespace "
            "v10_seed('r7s7:l2:coeff:{m}:{graph_seed}'), uniform nonzero "
            "GF32 in sorted-edge order; require accepted A1-A6 gates (exact "
            "variable/check degrees, one component, full structural rank m, "
            "full GF32 rank m, deterministic replay) before any binding; "
            "four-cycle/girth recorded, never gating; any invalid graph -> "
            "engineering-blocked, zero replacement seeds."),
    }


def describe_plan(grid=None, cap=None):
    """Zero-call profile: feasibility + plan + budget + absence proofs."""
    grid = _resolve_grid(grid)
    cap = _resolve_cap(cap)
    feas = feasibility_table(grid)
    plan = build_r7_plan(feas, grid)
    planned = len(plan)
    return {
        "change_id": CHANGE_ID, "cycle": CYCLE_ID, "track": TRACK,
        "claim_ceiling": CLAIM_CEILING,
        "winner": {"candidate_id": WINNER_ID, "x": WINNER_X,
                   "prior_delta_de": WINNER_PRIOR_DELTA_DE,
                   "frozen_note": "D18 winner; D19 S1 non-reopening; "
                                  "never retuned"},
        "grid_m": list(grid), "n": R7_N,
        "de_seeds": list(R7_DE_SEEDS), "pops": list(R7_POPS),
        "de_kernel": {"max_iter": d18.DE_MAX_ITER,
                      "entropy_tol_bits": d18.DE_ENTROPY_TOL_BITS,
                      "streak": d18.DE_STREAK,
                      "convergence_rule": "S=#{H60<1e-4} over seeds",
                      "protocol": "D18-StageC/D17-bracket verbatim"},
        "decoder_context": {"max_iter": d17.DECODER_MAX_ITER,
                            "damping": d17.DAMPING_ALPHA,
                            "decoder_calls_planned": 0},
        "feasibility": [{"m": r["m"], "executable": r["executable"],
                         "refusal_reason": r["refusal_reason"],
                         "E": r["E"], "check_counts": r["check_counts"]}
                        for r in feas],
        "planned_calls": planned,
        "cap": cap,
        "within_cap": planned <= cap,
        "dv3_reference": ("DROPPED at profile: same-grid DV3 needs 128 "
                          "more calls (256 > 200 cap); reference-only, "
                          "never winner"),
        "t2_bar": {"m124_equiv": m124_equiv(), "margin_delta": MARGIN_DELTA,
                   "bar": bar_value(),
                   "rule": "PASS(m) iff threshold < bar, strictly, and m "
                           "plus all larger grid m bracketed-converged"},
        "graph_seed_pool": list(R7_GRAPH_SEED_POOL),
        "seed_disjointness": verify_seed_disjointness(),
        "future_root": FUTURE_ROOT,
        "future_root_absent": not Path(FUTURE_ROOT).exists(),
        "frozen_command": FROZEN_COMMAND,
        "authorization": AUTHORIZATION,
        "de_calls": 0, "decoder_calls": 0, "graphs_constructed": 0,
    }


def _execute(entry, channel, de_call, rho):
    sampler = d18.resolve_sampler(channel, entry.get("layer", "L2"))
    result = de_call(dict(d18.lambda_edge_for_x(WINNER_X)),
                     dict(rho), sampler, int(entry["seed"]),
                     int(entry["population"]))
    trace = [float(x) for x in result["entropy_trace_bits"]]
    metrics = d9.trajectory_metrics(trace)
    return trace, metrics


def run_r7_sweep(out_root, model_f_root, *, channel=None, de_call=None,
                 rho_fn=None, now_fn=None, rss_fn=None, feasibility=None,
                 grid=None, cap=None):
    """Execute the frozen 128-call matrix with a per-call cap ledger."""
    grid = _resolve_grid(grid)
    cap = _resolve_cap(cap)
    expected = len(grid) * len(R7_DE_SEEDS) * len(R7_POPS)
    feas = feasibility_table(grid) if feasibility is None else feasibility
    plan = build_r7_plan(feas, grid)
    if len(plan) != expected:
        raise ValueError("R7 plan has %d entries, frozen %d"
                         % (len(plan), expected))
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
                d18.rate_for_m(m), dict(d18.lambda_edge_for_x(WINNER_X))))
    now = now_fn or time.monotonic
    rss_fn = rss_fn or (lambda: 0)
    t0 = float(now())
    records, traces = [], []
    ledger = {"cap": cap, "consumed": 0}
    halted = ""
    rhos = {(row["candidate_id"], row["m"]): dict(
        rho_fn(row["candidate_id"], row["m"])) for row in feas}
    for entry in plan:
        if entry["refused"]:
            continue
        if ledger["consumed"] >= ledger["cap"]:
            halted = ("CAP_HIT@call_idx%d: ledger %d/%d, halted, partial "
                      "table retained" % (entry["call_idx"],
                                          ledger["consumed"], ledger["cap"]))
            break
        start = float(now())
        try:
            trace, metrics = _execute(
                entry, channel, de_call,
                rhos[(entry["candidate_id"], entry["m"])])
        except Exception as exc:  # failure retention, no retry, stop
            halted = halted or ("DE_CALL_FAILED@call_idx%d: %s: %s"
                                % (entry["call_idx"],
                                   type(exc).__name__, exc))
            break
        wall = float(now()) - start
        ledger["consumed"] += 1  # EVERY DE call ledgered
        records.append({
            "call_idx": entry["call_idx"], "candidate_id": entry["candidate_id"],
            "m": entry["m"], "rate": entry["rate"],
            "population": entry["population"], "seed": entry["seed"],
            "converged": bool(metrics.converged),
            "iterations": len(trace), "h60": float(metrics.H60),
            "wall_s": wall, "ledger_after": ledger["consumed"]})
        traces.append({
            "candidate_id": entry["candidate_id"], "m": entry["m"],
            "population": entry["population"], "seed": entry["seed"],
            "entropy_trace_bits": json.dumps(trace)})
        if wall > 300.0:
            halted = halted or ("PER_CALL_BUDGET@call_idx%d" % entry["call_idx"])
            break
    wall_s = float(now()) - t0
    s16 = {m: sum(1 for r in records if int(r["m"]) == m
                  and int(r["population"]) == 16000 and r["converged"])
           for m in grid}
    s4 = {m: sum(1 for r in records if int(r["m"]) == m
                 and int(r["population"]) == 4000 and r["converged"])
          for m in grid}
    complete = (not halted and len(records) ==
                sum(1 for e in plan if not e["refused"]))
    try:
        bracket = r7_bracket(s16, s4, grid=grid)
    except ValueError as exc:
        bracket = {"delta_de": None, "h": None, "flag": "NO_BRACKET",
                   "lo_m": None, "hi_m": None, "flags": ["NO_BRACKET"],
                   "error": str(exc)}
    bar = apply_bar(bracket, s16, s4, feas, grid)
    if halted.startswith("CAP_HIT"):
        terminal, min_m = T_INCOMPLETE_CAP, "INCOMPLETE-cap"
    elif not complete:
        terminal, min_m = T_ENGINEERING_BLOCKED, None
    else:
        terminal, min_m = T_COMPLETE, bar["min_m"]
    table = {str(m): {"s16000": s16[m], "s4000": s4[m],
                      "delta": d18.delta_for_m(m),
                      "pass": bar["pass"][str(m)]} for m in grid}
    return {
        "out_root": str(out_root), "model_f_root": str(model_f_root),
        "grid": list(grid), "cap": cap, "planned_calls": expected,
        "plan": plan, "records": records, "traces": traces,
        "ledger": ledger, "halted": halted, "wall_s": wall_s,
        "feasibility": feas, "s16000": s16, "s4000": s4,
        "bracket": bracket, "bar": bar, "table": table,
        "terminal": terminal, "min_m": min_m,
        "protocol": "D18-StageC/D17-bracket verbatim",
        "de_calls": ledger["consumed"], "decoder_calls": 0,
        "graphs_constructed": 0,
    }


def summarize(bundle):
    """S7 return IDs + T4 sheets/seed plan (arithmetic only, zero calls)."""
    grid = _resolve_grid(bundle.get("grid", R7_GRID_M))
    feas = bundle["feasibility"]
    feasible_ms = [m for m in grid
                   if bundle["bar"]["pass"][str(m)]]
    sheets = [arith_sheet(r) for r in feas
              if int(r["m"]) in feasible_ms and r["executable"]]
    covered = feasible_ms[:3]  # <=3 m's x <=3 graphs = <=9 total
    assignment, pool = {}, list(R7_GRAPH_SEED_POOL)
    for m in covered:
        assignment[str(m)], pool = pool[:3], pool[3:]
    dv3 = {"ran": False, "status": "NOT-RUN-reference-only",
           "reason": "same-grid DV3 needs %d more calls; %d+%d=%d > %d "
                     "cap; no narrowing tricks; never winner"
                     % (bundle.get("planned_calls", R7_PLANNED_CALLS),
                        bundle["ledger"]["consumed"],
                        bundle.get("planned_calls", R7_PLANNED_CALLS),
                        bundle["ledger"]["consumed"]
                        + bundle.get("planned_calls", R7_PLANNED_CALLS),
                        bundle["ledger"]["cap"])}
    return {
        "cycle": CYCLE_ID, "track": TRACK, "claim_ceiling": CLAIM_CEILING,
        "terminal": bundle["terminal"],
        "s7_table": bundle["table"], "s7_bracket": bundle["bracket"],
        "s7_min": bundle["min_m"], "s7_ledger": bundle["ledger"],
        "s7_arith": {"sheets": sheets,
                     "graph_assignment": assignment,
                     "graph_pool": list(R7_GRAPH_SEED_POOL),
                     "seed_disjointness": verify_seed_disjointness(),
                     "graphs_constructed": 0},
        "s7_dv3": dv3,
        "protocol": bundle["protocol"],
        "prior_crosscheck": {
            "d18_winner_delta_de": WINNER_PRIOR_DELTA_DE,
            "r2diag_anchor": "TRUTH weight mean 123.70 (range 119-128); "
                             "m=94 ~30 symbols short -> 124 sufficiency "
                             "edge plausibility ONLY (V72P3G6-R2DIAG "
                             "DIAG_REPORT row-1 reading)"},
        "de_calls": bundle["de_calls"], "decoder_calls": 0,
        "graphs_constructed": 0, "wall_s": bundle["wall_s"],
        "halted": bundle["halted"],
    }


def write_r7_root(bundle):
    """Persist the six-file evidence root (single write burst, no overwrite)."""
    out = Path(bundle["out_root"])
    if out.exists():
        raise ValueError("refusing overwrite of existing root %s" % (out,))
    out.mkdir(parents=True)
    summary = summarize(bundle)
    files = {}
    manifest = {"cycle": CYCLE_ID, "terminal": bundle["terminal"],
                "protocol": bundle["protocol"],
                "frozen_command": FROZEN_COMMAND,
                "authorization": AUTHORIZATION,
                "grid": bundle.get("grid", list(R7_GRID_M)),
                "planned_calls": bundle.get("planned_calls",
                                            R7_PLANNED_CALLS),
                "cap": bundle.get("cap", R7_DE_CAP),
                "claim_ceiling": CLAIM_CEILING}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2,
                                                  sort_keys=True))
    with (out / "de_plan.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["call_idx", "candidate_id", "m",
                                           "rate", "population", "seed",
                                           "refused", "refusal_reason"])
        w.writeheader()
        for e in bundle["plan"]:
            w.writerow({k: e[k] for k in w.fieldnames})
    with (out / "de_records.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["call_idx", "candidate_id", "m",
                                           "rate", "population", "seed",
                                           "converged", "iterations", "h60",
                                           "wall_s", "ledger_after"])
        w.writeheader()
        for r in bundle["records"]:
            w.writerow({k: r[k] for k in w.fieldnames})
    with (out / "de_traces.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["candidate_id", "m", "population",
                                           "seed", "entropy_trace_bits"])
        w.writeheader()
        for t in bundle["traces"]:
            w.writerow({k: t[k] for k in w.fieldnames})
    (out / "summary.json").write_text(json.dumps(summary, indent=2,
                                                 sort_keys=True))
    (out / "command_log.txt").write_text(
        "terminal=%s calls=%d min_m=%s\n" % (bundle["terminal"],
                                             bundle["ledger"]["consumed"],
                                             summary["s7_min"]))
    for name in EVIDENCE_FILES:
        files[name] = str(out / name)
    summary["s7_files"] = files
    (out / "summary.json").write_text(json.dumps(summary, indent=2,
                                                 sort_keys=True))
    return summary


def verify_r7_root(out_root, rho_fn=None, grid=None):
    """Read-only recomputation of a completed root (zero DE calls)."""
    out = Path(out_root)
    for name in EVIDENCE_FILES:
        if not (out / name).is_file():
            return False
    import csv as _csv
    if grid is None:  # infer R8-style roots from their own table keys
        try:
            _stored = json.loads((out / "summary.json").read_text())
            grid = tuple(sorted(int(m) for m in _stored["s7_table"]))
        except Exception:
            grid = R7_GRID_M
    grid = _resolve_grid(grid)
    with (out / "de_records.csv").open() as fh:
        records = list(_csv.DictReader(fh))
    s16 = {m: sum(1 for r in records if int(r["m"]) == m
                  and int(r["population"]) == 16000
                  and str(r["converged"]) == "True") for m in grid}
    s4 = {m: sum(1 for r in records if int(r["m"]) == m
                 and int(r["population"]) == 4000
                 and str(r["converged"]) == "True") for m in grid}
    try:
        bracket = r7_bracket(s16, s4, grid=grid)
    except ValueError:
        bracket = {"delta_de": None, "flag": "NO_BRACKET", "flags": ["NO_BRACKET"],
                   "lo_m": None, "hi_m": None, "h": None}
    summary = json.loads((out / "summary.json").read_text())
    bar = apply_bar(bracket, s16, s4, grid=grid)
    stored = summary["s7_bracket"]
    if summary["terminal"] != T_COMPLETE:
        return True  # partial/blocked roots carry their own halted record
    return (stored["flag"] == bracket["flag"]
            and stored.get("lo_m") == bracket.get("lo_m")
            and stored.get("hi_m") == bracket.get("hi_m")
            and summary["s7_ledger"]["consumed"] == len(records)
            and summary["s7_ledger"]["consumed"] <= summary["s7_ledger"]["cap"]
            and summary["s7_min"] == bar["min_m"])
