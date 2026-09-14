"""D9 GF32 DE-decoder calibration runner — frozen ``--calibrate``.

Exact command (design §6; requires a separate explicit authorization):

    .venv/bin/python scripts/v72p2d9_de_decoder_calibration_development.py --calibrate \
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
      --out-root workspace/d9_de_decoder_calibration_10076f83-d752-4bac-9161-d8b0907d951b

Track ``EXPLORE_HEAVY``; claim ceiling is calibration-contract evidence under
the frozen CAL-only Model-F channel and decoder contract. This runner makes no
production/finite-length decoder call and reads no data outside the accepted
CAL-only Model-F artifact. One fresh root per run; refuses overwrite, protected
roots and partial/adapted runs (single process, no retry, no resume, no seed
search, no adaptive stop). Writes exactly six files; ``--verify`` recomputes
every stored call group from ``de_traces.csv`` with zero skip, rechecks the
stability/routing arithmetic and the deterministic graph audit, and requires
stored == recomputed.
"""

from __future__ import annotations

import argparse
import csv
import json
import resource
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))

import comparison_bench.formal_ir.v72p2d9_de_decoder_calibration as d9  # noqa: E402

EVIDENCE_FILES = ("manifest.json", "de_records.csv", "de_traces.csv",
                  "candidate_summary.csv", "summary.json", "command_log.txt")

DE_RECORD_COLUMNS = (
    "call_idx", "candidate_id", "condition", "population", "seed", "rate", "m",
    "converged", "iterations", "final_entropy_bits", "aut_30", "h5", "h10",
    "h15", "h60", "t_010", "t_001", "wall_s")
DE_TRACE_COLUMNS = ("candidate_id", "condition", "population", "seed",
                    "entropy_trace_bits", "channel_entropy_trace_bits")
CANDIDATE_SUMMARY_COLUMNS = (
    "candidate_id", "role", "stability", "s4000_f12", "s16000_f12",
    "s4000_f10", "worst_aut_30_p16000", "mean_aut_30_p16000",
    "worst_t_001_p16000", "aut30_ratio_dv3", "boundary_crossing", "eligible")
VERIFY_FIELDS = ("call_idx", "population", "rate", "m", "converged",
                 "iterations", "final_entropy_bits", "aut_30", "h5", "h10",
                 "h15", "h60", "t_010", "t_001")

FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d9_de_decoder_calibration_development.py "
    "--calibrate --model-f-root %s --out-root %s"
    % (d9.MODEL_F_INPUT_ROOT, d9.SOLVER_ROOT))

#: Protected roots: never written (D5/D6/D7/D8/A2/Model-F and formal outputs).
PROTECTED_NAME_PREFIXES = ("v72p2d5", "v72p2d6", "v72p2d7", "v72p2d8",
                           "d6_", "d7_", "d8_", "a2", "tmp_pytest")
PROTECTED_SUBTREES = ("comparison_bench/outputs_comparison", "results")

#: Setup units counted against ``max_setup_calls``: channel load, plan build,
#: primitive certification and graph audit (one each).
SETUP_UNITS = 4


def resolve_repo_path(value):
    """Relative paths anchor at the repository root (no cwd dependence)."""
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def refuse_out_root(out_root):
    """Refuse protected roots and any existing root; return the resolved path."""
    resolved = resolve_repo_path(out_root)
    if resolved.is_relative_to(ROOT):
        for name in resolved.relative_to(ROOT).parts:
            if name.startswith(PROTECTED_NAME_PREFIXES):
                raise ValueError("refusing protected root %s" % resolved)
    for subtree in PROTECTED_SUBTREES:
        protected = resolve_repo_path(subtree)
        if resolved == protected or protected in resolved.parents:
            raise ValueError("refusing protected root %s" % resolved)
    if resolved.exists():
        raise FileExistsError("refusing to overwrite existing root %s"
                              % resolved)
    return resolved


def _peak_rss_bytes():
    # Linux ru_maxrss is KiB; single-process aggregate = this process.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _log(logfh, message):
    logfh.write("%s %s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), message))
    logfh.flush()


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    return value if isinstance(value, str) else str(value)


def _write_csv(path, columns, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(columns),
                                extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _cell(row.get(column))
                             for column in columns})


def _read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _conditions_meta():
    return {
        condition: {
            "role": d9.CONDITION_ROLE[condition],
            "m": d9.condition_m(condition),
            "n": 64,
            "rate": 1.0 - d9.condition_m(condition) / 64.0,
            "populations": list(d9.CONDITION_POPULATIONS[condition]),
        }
        for condition in d9.CONDITIONS
    }


def _budgets_meta():
    return {"max_de_calls": d9.MAX_DE_CALLS,
            "max_setup_calls": d9.MAX_SETUP_CALLS,
            "wall_s": d9.WALL_BUDGET_S,
            "per_call_s": d9.PER_CALL_BUDGET_S,
            "rss_bytes": d9.RSS_BUDGET_BYTES,
            "processes": 1, "retry": False, "resume": False,
            "seed_search": False, "adaptive_stop": False}


def _de_parameters_meta():
    return {"q": d9.Q, "max_iter": d9.MAX_ITER,
            "entropy_tol_bits": d9.ENTROPY_TOL_BITS, "streak": d9.STREAK,
            "record_entropy": True, "record_channel_entropy": True}


def _cert_compact(cert):
    return {
        "schema": cert["schema"],
        "seed": cert["seed"],
        "pass": bool(cert["semantics_pass"]),
        "ensemble_path_equivalence": bool(cert["ensemble_path_equivalence"]),
        "claim_ceiling": cert["claim_ceiling"],
        "equivalence_claims": list(cert["equivalence_claims"]),
        "non_equivalence_diagnostics": list(cert["non_equivalence_diagnostics"]),
        "checks": {name: {"claim": check["claim"], "passed": check["passed"],
                          "max_abs_diff": check["max_abs_diff"]}
                   for name, check in cert["checks"].items()},
    }


def _audit_compact(audit):
    cells = []
    for cell in audit["cells"]:
        cells.append({
            "candidate_id": cell["candidate_id"],
            "condition": cell["condition"],
            "width": cell["width"],
            "m": cell["m"],
            "realizable": cell["realizable"],
            "n2": cell.get("n2"),
            "n3": cell.get("n3"),
            "E": cell.get("E"),
            "realized_max_check_degree": cell.get("realized_max_check_degree"),
            "N2_minus_m_minus_1": cell.get("N2_minus_m_minus_1"),
            "lambda2_realized": cell.get("lambda2_realized"),
            "exact_nominal": cell.get("exact_nominal"),
        })
    return {"schema": audit["schema"], "valid": bool(audit["valid"]),
            "cell_count": audit["cell_count"],
            "violation_count": audit["violation_count"], "cells": cells}


def _manifest(out, model_f_root, plan, planned_calls, cert, audit):
    return {
        "schema": "v72p2d9_de_decoder_calibration_manifest_v1",
        "change_id": d9.CHANGE_ID,
        "cycle": d9.CYCLE_ID,
        "track": d9.TRACK,
        "claim_ceiling": d9.CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "model_f_root": str(model_f_root),
        "out_root": str(out),
        "l1_only": True,
        "field": {"q": d9.Q, "poly": d9.POLY,
                  "factory": "GF2mField.create(32)"},
        "channel": ("accepted CAL-only Model-F artifact -> E2 P_F -> P1 -> "
                    "floor_renorm(1e-15) -> per-sample true-symbol XOR "
                    "centering"),
        "conditions": _conditions_meta(),
        "seeds": list(d9.DE_SEEDS),
        "de_parameters": _de_parameters_meta(),
        "candidate_freeze": {
            "candidate_ids": [c["candidate_id"] for c in d9.enumerate_candidates()],
            "roles": {c["candidate_id"]: c["role"]
                      for c in d9.enumerate_candidates()},
            "count": len(d9.CANDIDATES),
            "baseline_candidate_id": d9.BASELINE_ID,
            "enumeration": "frozen 4-candidate matrix; no adaptation"},
        "matrix": {
            "f1.2_populations": list(d9.CONDITION_POPULATIONS["f1.2"]),
            "f1.0_populations": list(d9.CONDITION_POPULATIONS["f1.0"]),
            "plan_order": "candidate -> condition -> population -> seed",
            "planned_de_calls": int(planned_calls)},
        "stability_rule": {
            "observable": "H60 < 1e-4",
            "stable_converged": "S4000 == 8 and S16000 == 8",
            "stable_unconverged": "S4000 <= 6 and S16000 <= 6",
            "otherwise": "stability_ambiguous",
            "f1.0": "boundary diagnostic; never gates"},
        "selection_rule": {
            "margin": d9.ADVANCE_MARGIN,
            "requirement": ("semantics PASS, graph valid, DV3 "
                            "stable_unconverged, candidate stable_converged and "
                            "16000-sample worst-seed AUT_30 <= 0.95 x DV3"),
            "key": ["worst-seed AUT_30 p16000 asc",
                    "mean AUT_30 p16000 asc",
                    "worst T_0.01 p16000 asc",
                    "candidate ID lexicographic"]},
        "semantics": {"pass": bool(cert["semantics_pass"]),
                      "equivalence_claims": list(cert["equivalence_claims"]),
                      "non_equivalence_diagnostics":
                          list(cert["non_equivalence_diagnostics"])},
        "graph_valid": bool(audit["valid"]),
        "budgets": _budgets_meta(),
        "setup_units": SETUP_UNITS,
        "refusals": [
            {"candidate_id": entry["candidate_id"],
             "condition": entry["condition"],
             "population": entry["population"],
             "seed": entry["seed"],
             "reason": entry["refusal_reason"]}
            for entry in plan if entry["refused"]],
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": ("separate explicit user/main-thread authorization "
                          "required before --calibrate"),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _summary(out, model_f_root, terminal, reason, adv, calls, setup_calls,
             planned_calls, refusal_count, wall_s, peak_rss, cert, audit):
    return {
        "schema": "v72p2d9_de_decoder_calibration_summary_v1",
        "change_id": d9.CHANGE_ID,
        "cycle": d9.CYCLE_ID,
        "track": d9.TRACK,
        "claim_ceiling": d9.CLAIM_CEILING,
        "terminal": terminal,
        "terminal_reason": reason,
        "winner_candidate_id": adv["winner_candidate_id"],
        "eligible_candidate_ids": adv["eligible_candidate_ids"],
        "boundary_crossing_ids": adv["boundary_crossing_ids"],
        "baseline_candidate_id": d9.BASELINE_ID,
        "baseline_stability": adv["baseline_stability"],
        "semantics_pass": bool(cert["semantics_pass"]),
        "graph_valid": bool(audit["valid"]),
        "candidate_count": len(d9.CANDIDATES),
        "condition_count": len(d9.CONDITIONS),
        "de_calls": int(calls),
        "setup_calls": int(setup_calls),
        "planned_de_calls": int(planned_calls),
        "refusal_count": int(refusal_count),
        "wall_s": float(wall_s),
        "peak_rss_bytes": int(peak_rss),
        "seeds": list(d9.DE_SEEDS),
        "conditions": _conditions_meta(),
        "de_parameters": _de_parameters_meta(),
        "budgets": _budgets_meta(),
        "model_f_root": str(model_f_root),
        "out_root": str(out),
        "metric": {"H0_bits": d9.H0_BITS,
                   "aut_30": "sum_{t=0..30} H(t)",
                   "converged": "H60 < 1e-4",
                   "t_001": "first t with H(t) <= 0.01 else 61"},
        "semantics": _cert_compact(cert),
        "graph": _audit_compact(audit),
        "evidence_files": list(EVIDENCE_FILES),
    }


def run_calibration(model_f_root, out_root, *, channel=None, de_call=None,
                    certify=None, graph_audit=None):
    """Run the frozen 96-call calibration into a fresh root; returns the summary.

    ``channel``/``de_call``/``certify``/``graph_audit`` are test seams only: the
    CLI path uses the accepted artifact, the unchanged V26 kernel, the
    deterministic primitive certification and the frozen graph audit.
    """
    out = refuse_out_root(out_root)
    model_f_root = resolve_repo_path(model_f_root)
    de_call = d9.run_de_call if de_call is None else de_call
    certify = d9.certify_primitives if certify is None else certify
    graph_audit = d9.audit_graph_realization if graph_audit is None \
        else graph_audit
    out.mkdir(parents=True)
    logfh = open(out / "command_log.txt", "w", encoding="utf-8")
    t0 = time.perf_counter()
    deadline = t0 + d9.WALL_BUDGET_S
    calls = 0
    setup_calls = 0
    records = []
    traces = []
    terminal = None
    terminal_reason = None
    peak_rss = _peak_rss_bytes()
    try:
        _log(logfh, "change=%s cycle=%s track=%s" % (d9.CHANGE_ID, d9.CYCLE_ID,
                                                     d9.TRACK))
        _log(logfh, "claim_ceiling=%s" % d9.CLAIM_CEILING)
        _log(logfh, "command=%s" % FROZEN_COMMAND)
        cert = certify()
        setup_calls += 1
        semantics_pass = bool(cert["semantics_pass"])
        _log(logfh, "semantics_pass=%s equivalence_claims=%d diagnostics=%d "
             "ensemble_path_equivalence=%s"
             % (semantics_pass, len(cert["equivalence_claims"]),
                len(cert["non_equivalence_diagnostics"]),
                cert["ensemble_path_equivalence"]))
        for name in cert["equivalence_claims"]:
            check = cert["checks"][name]
            _log(logfh, "cert %s pass=%s max_abs=%.3g"
                 % (name, check["passed"], check["max_abs_diff"]))
        audit = graph_audit()
        setup_calls += 1
        graph_valid = bool(audit["valid"])
        _log(logfh, "graph_valid=%s cells=%d violations=%d"
             % (graph_valid, audit["cell_count"], audit["violation_count"]))
        plan = d9.build_plan()
        setup_calls += 1
        refusals = [entry for entry in plan if entry["refused"]]
        planned_calls = d9.planned_de_calls(plan)
        _log(logfh, "candidates=%d plan=%d refusals=%d planned_de_calls=%d"
             % (len(d9.CANDIDATES), len(plan), len(refusals), planned_calls))
        for entry in refusals:
            _log(logfh, "refused %s %s p=%s seed=%s: %s"
                 % (entry["candidate_id"], entry["condition"],
                    entry["population"], entry["seed"],
                    entry["refusal_reason"]))
        if channel is None:
            pb, p_f, p1 = d9.load_l1_channel(model_f_root)
        else:
            pb, p_f, p1 = (np.asarray(part, dtype=np.float64)
                           for part in channel)
        setup_calls += 1
        _log(logfh, "channel model_f_root=%s pb=%s p_f=%s p1=%s lambda_star=%r"
             % (model_f_root, pb.shape, p_f.shape, p1.shape, d9.LAMBDA_STAR))
        sampler = d9.build_l1_sampler(pb, p_f, p1)
        _write_json(out / "manifest.json",
                    _manifest(out, model_f_root, plan, planned_calls, cert,
                              audit))
        stop = False
        if not semantics_pass:
            terminal = d9.T_SEMANTICS
            terminal_reason = "primitive semantics certification failed"
            stop = True
        elif not graph_valid:
            terminal = d9.T_GRAPH
            terminal_reason = "degree realization audit invalid (%d violations)" \
                % audit["violation_count"]
            stop = True
        if not stop:
            for entry in plan:
                if stop:
                    break
                if entry["refused"]:
                    continue
                if calls >= d9.MAX_DE_CALLS:
                    terminal = d9.T_RESOURCE
                    terminal_reason = "de call cap %d reached" % d9.MAX_DE_CALLS
                    break
                if time.perf_counter() > deadline:
                    terminal = d9.T_RESOURCE
                    terminal_reason = "wall budget %.0fs exceeded" \
                        % d9.WALL_BUDGET_S
                    break
                call_t0 = time.perf_counter()
                try:
                    result = de_call(entry["lambda_edge"], entry["rho"],
                                     sampler, int(entry["seed"]),
                                     int(entry["population"]))
                    trace = [float(x) for x in result["entropy_trace_bits"]]
                    metrics = d9.trajectory_metrics(trace)
                except Exception as ex:  # no retry by contract
                    terminal = d9.T_INVALID
                    terminal_reason = "%s: %s" % (type(ex).__name__, ex)
                    _log(logfh, "DE call failed %s %s p=%s seed=%s: %s"
                         % (entry["candidate_id"], entry["condition"],
                            entry["population"], entry["seed"],
                            terminal_reason))
                    break
                wall = time.perf_counter() - call_t0
                calls += 1
                records.append({
                    "call_idx": calls - 1,
                    "candidate_id": entry["candidate_id"],
                    "condition": entry["condition"],
                    "population": int(entry["population"]),
                    "seed": int(entry["seed"]),
                    "rate": entry["rate"],
                    "m": entry["m"],
                    "converged": bool(metrics.converged),
                    "iterations": len(trace),
                    "final_entropy_bits": trace[-1],
                    "aut_30": float(metrics.AUT_30),
                    "h5": float(metrics.H5),
                    "h10": float(metrics.H10),
                    "h15": float(metrics.H15),
                    "h60": float(metrics.H60),
                    "t_010": int(metrics.T_010),
                    "t_001": int(metrics.T_001),
                    "wall_s": float(wall)})
                traces.append({
                    "candidate_id": entry["candidate_id"],
                    "condition": entry["condition"],
                    "population": int(entry["population"]),
                    "seed": int(entry["seed"]),
                    "entropy_trace_bits": trace,
                    "channel_entropy_trace_bits": [
                        float(x) for x in
                        result.get("channel_entropy_trace_bits", [])]})
                peak_rss = max(peak_rss, _peak_rss_bytes())
                _log(logfh, "call=%d/%d %s %s p=%s seed=%s converged=%s iters=%d "
                     "H60=%.6g wall=%.3fs peak_rss=%.1fMiB"
                     % (calls, planned_calls, entry["candidate_id"],
                        entry["condition"], entry["population"], entry["seed"],
                        bool(metrics.converged), len(trace),
                        float(metrics.H60), wall, peak_rss / 1024.0 ** 2))
                if wall > d9.PER_CALL_BUDGET_S:
                    terminal = d9.T_RESOURCE
                    terminal_reason = "per-call wall %.3fs > %.0fs" % (
                        wall, d9.PER_CALL_BUDGET_S)
                    break
                if peak_rss >= d9.RSS_BUDGET_BYTES:
                    terminal = d9.T_RESOURCE
                    terminal_reason = "peak RSS %d >= %d bytes" % (
                        peak_rss, d9.RSS_BUDGET_BYTES)
                    break
        if terminal is None:
            try:
                adv = d9.compute_routing(semantics_pass, graph_valid, records)
            except Exception as ex:
                terminal = d9.T_INVALID
                terminal_reason = "%s: %s" % (type(ex).__name__, ex)
                adv = {"rows": d9.aggregate_stability(records,
                                                      allow_partial=True),
                       "terminal": terminal, "winner_candidate_id": None,
                       "eligible_candidate_ids": [], "boundary_crossing_ids": [],
                       "baseline_stability": None}
            else:
                terminal = adv["terminal"]
        else:
            adv = {"rows": d9.aggregate_stability(records, allow_partial=True),
                   "terminal": terminal, "winner_candidate_id": None,
                   "eligible_candidate_ids": [], "boundary_crossing_ids": [],
                   "baseline_stability": None}
        wall_s = time.perf_counter() - t0
        _write_csv(out / "de_records.csv", DE_RECORD_COLUMNS, records)
        _write_csv(out / "de_traces.csv", DE_TRACE_COLUMNS, traces)
        _write_csv(out / "candidate_summary.csv", CANDIDATE_SUMMARY_COLUMNS,
                   adv["rows"])
        summary = _summary(out, model_f_root, terminal, terminal_reason, adv,
                           calls, setup_calls, planned_calls, len(refusals),
                           wall_s, peak_rss, cert, audit)
        _write_json(out / "summary.json", summary)
        _log(logfh, "terminal=%s reason=%s winner=%s de_calls=%d setup=%d "
             "wall=%.3fs peak_rss=%d"
             % (terminal, terminal_reason, adv["winner_candidate_id"], calls,
                setup_calls, wall_s, peak_rss))
        names = sorted(path.name for path in out.iterdir())
        if names != sorted(EVIDENCE_FILES):
            raise RuntimeError("root must contain exactly %s, got %s"
                               % (sorted(EVIDENCE_FILES), names))
        return summary
    finally:
        logfh.close()


def _recompute_rows(records, allow_partial):
    rows = []
    for rec in records:
        rows.append({
            "candidate_id": rec["candidate_id"],
            "condition": rec["condition"],
            "population": int(rec["population"]),
            "seed": int(rec["seed"]),
            "converged": bool(rec["converged"]),
            "aut_30": float(rec["aut_30"]),
            "t_001": int(rec["t_001"]),
        })
    return rows


def verify_command(out_root):
    """Recompute every stored group from ``de_traces.csv`` (zero skip).

    Also rechecks stability/routing arithmetic, the deterministic graph audit
    and the semantics-block internal consistency against the stored evidence.
    """
    out = resolve_repo_path(out_root)
    if not out.is_dir():
        print("VERIFY FAIL missing root %s" % out)
        return False
    violations = []
    names = sorted(path.name for path in out.iterdir())
    if names != sorted(EVIDENCE_FILES):
        violations.append("root files %s" % names)
    try:
        traces = _read_csv(out / "de_traces.csv")
        records = _read_csv(out / "de_records.csv")
        candidate_rows = _read_csv(out / "candidate_summary.csv")
        with open(out / "summary.json", encoding="utf-8") as fh:
            summary = json.load(fh)
    except Exception as ex:
        print("VERIFY FAIL unreadable evidence: %r" % (ex,))
        return False

    plan = d9.build_plan()
    expected_idx = d9.expected_call_index(plan)
    expected_calls = d9.planned_de_calls(plan)
    terminal = summary.get("terminal")
    full_required = terminal in (d9.T_SELECT, d9.T_STABILITY,
                                 d9.T_BASELINE_CONVERGED)

    records_by_key = {}
    for record in records:
        key = (record["candidate_id"], record["condition"],
               int(record["population"]), int(record["seed"]))
        records_by_key.setdefault(key, []).append(record)

    checked = agreements = skipped = 0
    recomputed_records = []
    trace_keys = set()
    for trace_row in traces:
        key = (trace_row["candidate_id"], trace_row["condition"],
               int(trace_row["population"]), int(trace_row["seed"]))
        trace_keys.add(key)
        stored_list = records_by_key.get(key, [])
        if len(stored_list) != 1:
            violations.append("trace without exactly one record: %s" % (key,))
            skipped += 1
            continue
        stored = stored_list[0]
        call_idx = expected_idx.get(key)
        if call_idx is None:
            violations.append("call outside the frozen plan: %s" % (key,))
            skipped += 1
            continue
        try:
            trace = json.loads(trace_row["entropy_trace_bits"])
            metrics = d9.trajectory_metrics(trace)
        except Exception as ex:
            violations.append("unrecomputable trace %s: %r" % (key, ex))
            skipped += 1
            continue
        recomputed = {
            "call_idx": call_idx,
            "population": key[2],
            "rate": stored["rate"],
            "m": stored["m"],
            "converged": bool(metrics.converged),
            "iterations": len(trace),
            "final_entropy_bits": trace[-1] if trace else None,
            "aut_30": metrics.AUT_30,
            "h5": metrics.H5,
            "h10": metrics.H10,
            "h15": metrics.H15,
            "h60": metrics.H60,
            "t_010": metrics.T_010,
            "t_001": metrics.T_001,
        }
        checked += 1
        ok = True
        for field in VERIFY_FIELDS:
            if _cell(recomputed[field]) != _cell(stored.get(field)):
                violations.append("%s field %s stored=%r recomputed=%r"
                                  % (key, field, stored.get(field),
                                     _cell(recomputed[field])))
                ok = False
        if ok:
            agreements += 1
        recomputed_records.append({
            "candidate_id": key[0], "condition": key[1], "population": key[2],
            "seed": key[3], "converged": recomputed["converged"],
            "aut_30": recomputed["aut_30"], "t_001": recomputed["t_001"]})
    for record in records:
        key = (record["candidate_id"], record["condition"],
               int(record["population"]), int(record["seed"]))
        if key not in trace_keys:
            violations.append("record without trace: %s" % (key,))
    if full_required:
        if len(records) != expected_calls:
            violations.append("stored calls %d != planned %d"
                              % (len(records), expected_calls))
        if len(traces) != expected_calls:
            violations.append("stored traces %d != planned %d"
                              % (len(traces), expected_calls))
    else:
        if int(summary.get("de_calls", -1)) != len(records):
            violations.append("stored calls %d != summary de_calls %r"
                              % (len(records), summary.get("de_calls")))
        if len(records) > expected_calls:
            violations.append("stored calls %d exceed planned %d"
                              % (len(records), expected_calls))

    sem = summary.get("semantics", {})
    graph = summary.get("graph", {})
    try:
        if terminal in (d9.T_SELECT, d9.T_STABILITY, d9.T_BASELINE_CONVERGED,
                        d9.T_SEMANTICS, d9.T_GRAPH):
            adv = d9.compute_routing(bool(sem.get("pass")),
                                     bool(graph.get("valid")),
                                     _recompute_rows(recomputed_records,
                                                     not full_required),
                                     allow_partial=not full_required)
        elif terminal is None:
            adv = None
        else:
            adv = {"rows": d9.aggregate_stability(
                _recompute_rows(recomputed_records, True), allow_partial=True),
                "terminal": terminal, "winner_candidate_id": None,
                "eligible_candidate_ids": [], "boundary_crossing_ids": [],
                "baseline_stability": None}
    except Exception as ex:
        violations.append("routing recomputation failed: %r" % (ex,))
        adv = None

    if adv is not None:
        for field in ("terminal", "winner_candidate_id",
                      "eligible_candidate_ids", "boundary_crossing_ids",
                      "baseline_stability"):
            if summary.get(field) != adv[field]:
                violations.append("summary %s stored=%r recomputed=%r"
                                  % (field, summary.get(field), adv[field]))
        stored_rows = {row["candidate_id"]: row for row in candidate_rows}
        recomputed_rows = {row["candidate_id"]: row for row in adv["rows"]}
        if set(stored_rows) != set(recomputed_rows):
            violations.append("candidate_summary keys differ")
        for cid in sorted(set(stored_rows) & set(recomputed_rows)):
            for column in CANDIDATE_SUMMARY_COLUMNS:
                if _cell(stored_rows[cid].get(column)) != \
                        _cell(recomputed_rows[cid].get(column)):
                    violations.append(
                        "candidate_summary %s %s stored=%r recomputed=%r"
                        % (cid, column, stored_rows[cid].get(column),
                           _cell(recomputed_rows[cid].get(column))))
        for field, expected_value in (
                ("de_calls", len(records)),
                ("planned_de_calls", expected_calls),
                ("refusal_count",
                 sum(1 for entry in plan if entry["refused"])),
                ("candidate_count", len(d9.CANDIDATES))):
            if int(summary.get(field, -1)) != expected_value:
                violations.append("summary %s stored=%r recomputed=%r"
                                  % (field, summary.get(field),
                                     expected_value))
        if not 0 <= int(summary.get("setup_calls", -1)) <= d9.MAX_SETUP_CALLS:
            violations.append("setup_calls outside budget: %r"
                              % summary.get("setup_calls"))

    checks = sem.get("checks", {})
    equivalence = sem.get("equivalence_claims", [])
    labelled = {name for name, check in checks.items()
                if check.get("claim") == d9.CLAIM_EQUIVALENCE_CERTIFIED}
    if set(equivalence) != labelled:
        violations.append("semantics equivalence_claims do not match labels")
    if bool(sem.get("pass")) != all(bool(checks[name]["passed"])
                                    for name in equivalence):
        violations.append("semantics pass flag inconsistent with checks")

    audit = d9.audit_graph_realization()
    if bool(graph.get("valid")) != bool(audit["valid"]):
        violations.append("graph valid stored=%r recomputed=%r"
                          % (graph.get("valid"), audit["valid"]))
    stored_cells = {(cell["candidate_id"], cell["condition"], cell["width"]):
                    cell for cell in graph.get("cells", [])}
    for cell in audit["cells"]:
        key = (cell["candidate_id"], cell["condition"], cell["width"])
        stored = stored_cells.get(key)
        if stored is None:
            violations.append("graph cell missing: %s" % (key,))
            continue
        if not cell.get("realizable", False):
            if stored.get("realizable") is not False:
                violations.append("graph %s realizable stored=%r "
                                  "recomputed=False"
                                  % (key, stored.get("realizable")))
            continue
        for field in ("n2", "n3", "E", "realized_max_check_degree",
                      "N2_minus_m_minus_1"):
            if int(stored.get(field, -1)) != int(cell.get(field, -2)):
                violations.append("graph %s %s stored=%r recomputed=%r"
                                  % (key, field, stored.get(field),
                                     cell.get(field)))
        if abs(float(stored.get("lambda2_realized", -1.0))
               - float(cell["lambda2_realized"])) > 1e-12:
            violations.append("graph %s lambda2_realized mismatch" % (key,))

    groups_total = len(d9.CANDIDATES) * 3
    groups_complete = 0
    for cand in d9.CANDIDATES:
        for condition, population in (("f1.2", 4000), ("f1.2", 16000),
                                      ("f1.0", 4000)):
            count = sum(1 for trace_row in traces
                        if (trace_row["candidate_id"] == cand["candidate_id"]
                            and trace_row["condition"] == condition
                            and int(trace_row["population"]) == population))
            if count == len(d9.DE_SEEDS):
                groups_complete += 1
            elif full_required:
                violations.append("group (%s, %s, %s) stored %d != expected %d"
                                  % (cand["candidate_id"], condition, population,
                                     count, len(d9.DE_SEEDS)))
    print("VERIFY checked_calls=%d agreements=%d skipped=%d groups=%d/%d "
          "violations=%d" % (checked, agreements, skipped, groups_complete,
                             groups_total, len(violations)))
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    ok = not violations
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return ok


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="D9 GF32 DE-decoder calibration runner")
    parser.add_argument("--calibrate", action="store_true",
                        help="run the frozen 96-call calibration batch (requires "
                             "separate explicit authorization)")
    parser.add_argument("--verify", action="store_true",
                        help="recompute a completed root from de_traces.csv")
    parser.add_argument("--model-f-root", default=d9.MODEL_F_INPUT_ROOT,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--out-root", required=True,
                        help="fresh output root (must not exist)")
    args = parser.parse_args(argv)
    if args.verify:
        return 0 if verify_command(args.out_root) else 1
    if not args.calibrate:
        parser.error("one of --calibrate or --verify is required")
    try:
        summary = run_calibration(args.model_f_root, args.out_root)
    except (ValueError, FileExistsError) as ex:
        print(str(ex), file=sys.stderr)
        return 2
    print("D9_DE_CALIBRATION terminal=%s winner=%s de_calls=%d setup=%d"
          % (summary["terminal"], summary["winner_candidate_id"],
             summary["de_calls"], summary["setup_calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

