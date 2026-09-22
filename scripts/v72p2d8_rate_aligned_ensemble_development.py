"""D8 rate-aligned GF32 ensemble feasibility runner — frozen ``--de-sweep``.

Exact command (design §6; requires a separate explicit authorization):

    .venv/bin/python scripts/v72p2d8_rate_aligned_ensemble_development.py --de-sweep \
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
      --out-root workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405

Track ``EXPLORE_HEAVY``; claim ceiling DE-only synthetic asymptotic under the
frozen CAL-only Model-F channel and decoder contract. This runner makes no
production decoder call and reads no data outside the accepted CAL-only Model-F
artifact. One fresh root per run; refuses overwrite, protected roots, and
partial/adapted runs (single process, no retry, no resume, no adaptive stop).
Writes exactly six files; ``--verify`` recomputes every stored candidate group
from ``de_traces.csv`` with zero skip and requires stored == recomputed.
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

import comparison_bench.formal_ir.v72p2d8_rate_aligned_ensemble as d8  # noqa: E402

EVIDENCE_FILES = ("manifest.json", "de_records.csv", "de_traces.csv",
                  "candidate_summary.csv", "summary.json", "command_log.txt")

DE_RECORD_COLUMNS = (
    "call_idx", "candidate_id", "condition", "seed", "rate", "m", "converged",
    "iterations", "final_entropy_bits", "aut_30", "h5", "h10", "h15", "h60",
    "t_010", "t_001", "wall_s")
DE_TRACE_COLUMNS = ("candidate_id", "condition", "seed", "entropy_trace_bits",
                    "channel_entropy_trace_bits")
CANDIDATE_SUMMARY_COLUMNS = (
    "candidate_id", "condition", "role", "rate", "m", "refused",
    "refusal_reason", "n_seeds", "seeds_converged", "worst_aut_30",
    "mean_aut_30", "worst_t_001", "aut30_ratio_baseline", "eligible",
    "N2_n64", "N2_n128", "N2_n256", "gamma2_n64", "gamma2_n128", "gamma2_n256")
VERIFY_FIELDS = ("call_idx", "rate", "m", "converged", "iterations",
                 "final_entropy_bits", "aut_30", "h5", "h10", "h15", "h60",
                 "t_010", "t_001")

FROZEN_COMMAND = (
    ".venv/bin/python scripts/v72p2d8_rate_aligned_ensemble_development.py "
    "--de-sweep --model-f-root %s --out-root %s"
    % (d8.MODEL_F_INPUT_ROOT, d8.SOLVER_ROOT))

#: Protected roots: never written (D6/A2/D7/Model-F/G2 and formal outputs).
PROTECTED_NAME_PREFIXES = ("v72p2d5", "v72p2d6", "v72p2d7", "d6_", "d7_",
                           "a2", "tmp_pytest")
PROTECTED_SUBTREES = ("comparison_bench/outputs_comparison", "results")


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
    meta = {}
    for condition in d8.CONDITIONS:
        m = d8.condition_m(condition)
        meta[condition] = {"role": d8.CONDITION_ROLE[condition], "m": m,
                           "n": 64, "rate": 1.0 - m / 64.0}
    return meta


def _budgets_meta():
    return {"max_de_calls": d8.MAX_DE_CALLS,
            "max_setup_calls": d8.MAX_SETUP_CALLS,
            "wall_s": d8.WALL_BUDGET_S,
            "per_call_s": d8.PER_CALL_BUDGET_S,
            "rss_bytes": d8.RSS_BUDGET_BYTES,
            "processes": 1, "retry": False, "resume": False,
            "adaptive_stop": False}


def _de_parameters_meta():
    return {"q": d8.Q, "n_samples": d8.N_SAMPLES, "max_iter": d8.MAX_ITER,
            "entropy_tol_bits": d8.ENTROPY_TOL_BITS, "streak": d8.STREAK,
            "record_entropy": True, "record_channel_entropy": True}


def _manifest(out, model_f_root, plan, planned_calls):
    return {
        "schema": "v72p2d8_rate_aligned_ensemble_manifest_v1",
        "change_id": d8.CHANGE_ID,
        "cycle": d8.CYCLE_ID,
        "track": d8.TRACK,
        "claim_ceiling": d8.CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "model_f_root": str(model_f_root),
        "out_root": str(out),
        "l1_only": True,
        "field": {"q": d8.Q, "poly": d8.POLY,
                  "factory": "GF2mField.create(32)"},
        "channel": "accepted CAL-only Model-F artifact -> E2 P_F -> P1 -> "
                   "floor_renorm(1e-15) -> per-sample true-symbol XOR centering",
        "conditions": _conditions_meta(),
        "seeds": list(d8.DE_SEEDS),
        "de_parameters": _de_parameters_meta(),
        "candidate_freeze": {
            "support": [2, 3], "step": d8.CANDIDATE_STEP,
            "count": d8.CANDIDATE_COUNT, "hard_cap": d8.CANDIDATE_COUNT,
            "id_format": "lam_d2_<lambda2:.2f>_d3_<lambda3:.2f>",
            "enumeration": "ascending lambda2; no adaptation",
            "baseline_candidate_id": d8.BASELINE_ID},
        "advancement": {
            "margin": d8.ADVANCE_MARGIN,
            "key": ["primary worst-seed AUT_30 asc",
                    "primary mean AUT_30 asc",
                    "primary worst-seed T_0.01 asc",
                    "candidate ID lexicographic"],
            "requirement": "all seeds converged (H60 < 1e-4) in both "
                           "conditions"},
        "budgets": _budgets_meta(),
        "planned_de_calls": int(planned_calls),
        "refusals": [
            {"candidate_id": entry["candidate_id"],
             "condition": entry["condition"],
             "reason": entry["refusal_reason"]}
            for entry in plan if entry["refused"]],
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": "separate explicit user/main-thread authorization "
                         "required before --de-sweep",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _summary(out, model_f_root, terminal, reason, adv, calls, setup_calls,
             planned_calls, refusal_count, wall_s, peak_rss):
    return {
        "schema": "v72p2d8_rate_aligned_ensemble_summary_v1",
        "change_id": d8.CHANGE_ID,
        "cycle": d8.CYCLE_ID,
        "track": d8.TRACK,
        "claim_ceiling": d8.CLAIM_CEILING,
        "terminal": terminal,
        "terminal_reason": reason,
        "winner_candidate_id": adv["winner_candidate_id"],
        "eligible_candidate_ids": adv["eligible_candidate_ids"],
        "baseline_candidate_id": d8.BASELINE_ID,
        "baseline_converged": adv["baseline_converged"],
        "baseline_primary_worst_aut_30": adv["baseline_primary_worst_aut_30"],
        "candidate_count": d8.CANDIDATE_COUNT,
        "condition_count": len(d8.CONDITIONS),
        "de_calls": int(calls),
        "setup_calls": int(setup_calls),
        "planned_de_calls": int(planned_calls),
        "refusal_count": int(refusal_count),
        "wall_s": float(wall_s),
        "peak_rss_bytes": int(peak_rss),
        "seeds": list(d8.DE_SEEDS),
        "conditions": _conditions_meta(),
        "de_parameters": _de_parameters_meta(),
        "budgets": _budgets_meta(),
        "model_f_root": str(model_f_root),
        "out_root": str(out),
        "metric": {"H0_bits": d8.H0_BITS,
                   "aut_30": "sum_{t=0..30} H(t)",
                   "converged": "H60 < 1e-4",
                   "t_001": "first t with H(t) <= 0.01 else 61"},
        "evidence_files": list(EVIDENCE_FILES),
    }


def run_de_sweep(model_f_root, out_root, *, channel=None, de_call=None):
    """Run the frozen L1 DE sweep into a fresh root; returns the summary dict.

    ``channel``/``de_call`` are test seams only: the CLI path uses the accepted
    artifact and the unchanged V26 kernel.
    """
    out = refuse_out_root(out_root)
    model_f_root = resolve_repo_path(model_f_root)
    de_call = d8.run_de_call if de_call is None else de_call
    out.mkdir(parents=True)
    logfh = open(out / "command_log.txt", "w", encoding="utf-8")
    t0 = time.perf_counter()
    deadline = t0 + d8.WALL_BUDGET_S
    calls = 0
    setup_calls = 0
    records = []
    traces = []
    terminal = None
    terminal_reason = None
    peak_rss = _peak_rss_bytes()
    try:
        _log(logfh, "change=%s cycle=%s track=%s" % (d8.CHANGE_ID, d8.CYCLE_ID,
                                                     d8.TRACK))
        _log(logfh, "claim_ceiling=%s" % d8.CLAIM_CEILING)
        _log(logfh, "command=%s" % FROZEN_COMMAND)
        if channel is None:
            pb, p_f, p1 = d8.load_l1_channel(model_f_root)
        else:
            pb, p_f, p1 = (np.asarray(part, dtype=np.float64)
                           for part in channel)
        _log(logfh, "channel model_f_root=%s pb=%s p_f=%s p1=%s lambda_star=%r"
             % (model_f_root, pb.shape, p_f.shape, p1.shape, d8.LAMBDA_STAR))
        sampler = d8.build_l1_sampler(pb, p_f, p1)
        plan = d8.build_candidate_plan()
        candidates = {entry["candidate_id"] for entry in plan}
        refusals = [entry for entry in plan if entry["refused"]]
        planned_calls = (len(plan) - len(refusals)) * len(d8.DE_SEEDS)
        _log(logfh, "candidates=%d pairs=%d refusals=%d planned_de_calls=%d"
             % (len(candidates), len(plan), len(refusals), planned_calls))
        for entry in refusals:
            _log(logfh, "refused %s %s: %s" % (entry["candidate_id"],
                                               entry["condition"],
                                               entry["refusal_reason"]))
        _write_json(out / "manifest.json",
                    _manifest(out, model_f_root, plan, planned_calls))
        stop = False
        for entry in plan:
            if stop:
                break
            if entry["refused"]:
                continue
            for seed in d8.DE_SEEDS:
                if calls >= d8.MAX_DE_CALLS:
                    terminal = d8.T_RESOURCE
                    terminal_reason = "de call cap %d reached" % d8.MAX_DE_CALLS
                    stop = True
                    break
                if time.perf_counter() > deadline:
                    terminal = d8.T_RESOURCE
                    terminal_reason = "wall budget %.0fs exceeded" % d8.WALL_BUDGET_S
                    stop = True
                    break
                call_t0 = time.perf_counter()
                try:
                    result = de_call(entry["lambda_edge"], entry["rho"],
                                     sampler, int(seed))
                    trace = [float(x) for x in result["entropy_trace_bits"]]
                    metrics = d8.trajectory_metrics(trace)
                except Exception as ex:  # no retry by contract
                    terminal = d8.T_INVALID
                    terminal_reason = "%s: %s" % (type(ex).__name__, ex)
                    _log(logfh, "DE call failed %s %s seed=%d: %s"
                         % (entry["candidate_id"], entry["condition"], seed,
                            terminal_reason))
                    stop = True
                    break
                wall = time.perf_counter() - call_t0
                calls += 1
                records.append({
                    "call_idx": calls - 1,
                    "candidate_id": entry["candidate_id"],
                    "condition": entry["condition"],
                    "seed": int(seed),
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
                    "seed": int(seed),
                    "entropy_trace_bits": trace,
                    "channel_entropy_trace_bits": [
                        float(x) for x in
                        result.get("channel_entropy_trace_bits", [])]})
                peak_rss = max(peak_rss, _peak_rss_bytes())
                _log(logfh, "call=%d/%d %s %s seed=%d converged=%s iters=%d "
                     "H60=%.6g wall=%.3fs peak_rss=%.1fMiB"
                     % (calls, planned_calls, entry["candidate_id"],
                        entry["condition"], seed, bool(metrics.converged),
                        len(trace), float(metrics.H60), wall,
                        peak_rss / 1024.0 ** 2))
                if wall > d8.PER_CALL_BUDGET_S:
                    terminal = d8.T_RESOURCE
                    terminal_reason = "per-call wall %.3fs > %.0fs" % (
                        wall, d8.PER_CALL_BUDGET_S)
                    stop = True
                    break
                if peak_rss >= d8.RSS_BUDGET_BYTES:
                    terminal = d8.T_RESOURCE
                    terminal_reason = "peak RSS %d >= %d bytes" % (
                        peak_rss, d8.RSS_BUDGET_BYTES)
                    stop = True
                    break
        partial_adv = {
            "rows": d8.aggregate_candidate_conditions(records, plan,
                                                      allow_partial=True),
            "terminal": terminal,
            "winner_candidate_id": None,
            "eligible_candidate_ids": [],
            "baseline_converged": False,
            "baseline_primary_worst_aut_30": None,
        }
        if terminal is None:
            try:
                adv = d8.compute_advancement(records, plan)
            except Exception as ex:
                terminal = d8.T_INVALID
                terminal_reason = "%s: %s" % (type(ex).__name__, ex)
                partial_adv["terminal"] = terminal
                adv = partial_adv
            else:
                terminal = adv["terminal"]
        else:
            adv = partial_adv
        wall_s = time.perf_counter() - t0
        _write_csv(out / "de_records.csv", DE_RECORD_COLUMNS, records)
        _write_csv(out / "de_traces.csv", DE_TRACE_COLUMNS, traces)
        _write_csv(out / "candidate_summary.csv", CANDIDATE_SUMMARY_COLUMNS,
                   adv["rows"])
        summary = _summary(out, model_f_root, terminal, terminal_reason, adv,
                           calls, setup_calls, planned_calls, len(refusals),
                           wall_s, peak_rss)
        _write_json(out / "summary.json", summary)
        _log(logfh, "terminal=%s reason=%s winner=%s de_calls=%d wall=%.3fs "
             "peak_rss=%d" % (terminal, terminal_reason,
                              adv["winner_candidate_id"], calls, wall_s,
                              peak_rss))
        names = sorted(path.name for path in out.iterdir())
        if names != sorted(EVIDENCE_FILES):
            raise RuntimeError("root must contain exactly %s, got %s"
                               % (sorted(EVIDENCE_FILES), names))
        return summary
    finally:
        logfh.close()


def verify_command(out_root):
    """Recompute every stored group from ``de_traces.csv`` (zero skip)."""
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

    plan = d8.build_candidate_plan()
    expected_idx = {}
    expected_calls = 0
    for entry in plan:
        if entry["refused"]:
            continue
        for seed in d8.DE_SEEDS:
            expected_idx[(entry["candidate_id"], entry["condition"],
                          int(seed))] = expected_calls
            expected_calls += 1

    records_by_key = {}
    for record in records:
        key = (record["candidate_id"], record["condition"],
               int(record["seed"]))
        records_by_key.setdefault(key, []).append(record)

    checked = agreements = skipped = 0
    recomputed_records = []
    trace_keys = set()
    for trace_row in traces:
        key = (trace_row["candidate_id"], trace_row["condition"],
               int(trace_row["seed"]))
        trace_keys.add(key)
        stored = records_by_key.get(key, [])
        if len(stored) != 1:
            violations.append("trace without exactly one record: %s" % (key,))
            skipped += 1
            continue
        stored = stored[0]
        call_idx = expected_idx.get(key)
        if call_idx is None:
            violations.append("call outside the frozen plan: %s" % (key,))
            skipped += 1
            continue
        try:
            trace = json.loads(trace_row["entropy_trace_bits"])
            metrics = d8.trajectory_metrics(trace)
        except Exception as ex:
            violations.append("unrecomputable trace %s: %r" % (key, ex))
            skipped += 1
            continue
        recomputed = {
            "call_idx": call_idx,
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
        call_ok = True
        for field in VERIFY_FIELDS:
            if _cell(recomputed[field]) != _cell(stored.get(field)):
                violations.append("%s field %s stored=%r recomputed=%r"
                                  % (key, field, stored.get(field),
                                     _cell(recomputed[field])))
                call_ok = False
        if call_ok:
            agreements += 1
        recomputed_records.append({
            "call_idx": call_idx,
            "candidate_id": key[0], "condition": key[1], "seed": key[2],
            "converged": recomputed["converged"],
            "aut_30": recomputed["aut_30"],
            "t_001": recomputed["t_001"],
        })
    for record in records:
        key = (record["candidate_id"], record["condition"],
               int(record["seed"]))
        if key not in trace_keys:
            violations.append("record without trace: %s" % (key,))
    if len(records) != expected_calls:
        violations.append("stored calls %d != planned %d"
                          % (len(records), expected_calls))
    if len(traces) != expected_calls:
        violations.append("stored traces %d != planned %d"
                          % (len(traces), expected_calls))

    terminal = summary.get("terminal")
    try:
        if terminal in (d8.T_ADVANCE, d8.T_NO_ADVANCE, d8.T_BASELINE):
            adv = d8.compute_advancement(recomputed_records, plan)
        else:
            adv = {"rows": d8.aggregate_candidate_conditions(
                recomputed_records, plan, allow_partial=False),
                "terminal": terminal, "winner_candidate_id": None,
                "eligible_candidate_ids": [],
                "baseline_converged": summary.get("baseline_converged"),
                "baseline_primary_worst_aut_30":
                    summary.get("baseline_primary_worst_aut_30")}
    except Exception as ex:
        violations.append("advancement recomputation failed: %r" % (ex,))
        adv = None

    if adv is not None:
        if terminal in (d8.T_ADVANCE, d8.T_NO_ADVANCE, d8.T_BASELINE):
            for field in ("terminal", "winner_candidate_id",
                          "eligible_candidate_ids", "baseline_converged",
                          "baseline_primary_worst_aut_30"):
                if summary.get(field) != adv[field]:
                    violations.append("summary %s stored=%r recomputed=%r"
                                      % (field, summary.get(field),
                                         adv[field]))
        stored_rows = {(row["candidate_id"], row["condition"]): row
                       for row in candidate_rows}
        recomputed_rows = {(row["candidate_id"], row["condition"]): row
                           for row in adv["rows"]}
        if set(stored_rows) != set(recomputed_rows):
            violations.append("candidate_summary keys differ")
        for key in sorted(set(stored_rows) & set(recomputed_rows)):
            for column in CANDIDATE_SUMMARY_COLUMNS:
                if _cell(stored_rows[key].get(column)) != \
                        _cell(recomputed_rows[key].get(column)):
                    violations.append(
                        "candidate_summary %s %s stored=%r recomputed=%r"
                        % (key, column, stored_rows[key].get(column),
                           _cell(recomputed_rows[key].get(column))))
        for field, expected_value in (
                ("de_calls", len(records)),
                ("setup_calls", 0),
                ("planned_de_calls", expected_calls),
                ("refusal_count", sum(1 for entry in plan
                                      if entry["refused"])),
                ("candidate_count",
                 len({entry["candidate_id"] for entry in plan}))):
            if int(summary.get(field, -1)) != expected_value:
                violations.append("summary %s stored=%r recomputed=%r"
                                  % (field, summary.get(field),
                                     expected_value))

    groups_total = len(plan)
    groups_complete = 0
    for entry in plan:
        key = (entry["candidate_id"], entry["condition"])
        count = sum(1 for trace_row in traces
                    if (trace_row["candidate_id"],
                        trace_row["condition"]) == key)
        want = 0 if entry["refused"] else len(d8.DE_SEEDS)
        if count == want:
            groups_complete += 1
        else:
            violations.append("group %s stored %d != expected %d"
                              % (key, count, want))
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
        description="D8 rate-aligned GF32 ensemble feasibility runner")
    parser.add_argument("--de-sweep", action="store_true",
                        help="run the frozen 126-call L1 DE sweep (requires "
                             "separate explicit authorization)")
    parser.add_argument("--verify", action="store_true",
                        help="recompute a completed root from de_traces.csv")
    parser.add_argument("--model-f-root", default=d8.MODEL_F_INPUT_ROOT,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--out-root", required=True,
                        help="fresh output root (must not exist)")
    args = parser.parse_args(argv)
    if args.verify:
        return 0 if verify_command(args.out_root) else 1
    if not args.de_sweep:
        parser.error("one of --de-sweep or --verify is required")
    try:
        summary = run_de_sweep(args.model_f_root, args.out_root)
    except (ValueError, FileExistsError) as ex:
        print(str(ex), file=sys.stderr)
        return 2
    print("D8_DE_SWEEP terminal=%s winner=%s de_calls=%d"
          % (summary["terminal"], summary["winner_candidate_id"],
             summary["de_calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
