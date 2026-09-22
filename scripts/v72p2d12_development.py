"""D12 finite L1 degree refinement runner — readiness paths.

Frozen command (design §5; requires a separate explicit authorization):

    .venv/bin/python scripts/v72p2d12_development.py --d12-batch \\
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \\
      --out-root workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450

Paths:

- ``--profile-only``: build the 36 frozen D12 graphs with the real
  builders, print structural metrics (components, structural/GF32 rank,
  four-cycles, girth, A1–A6 admission, wall time) plus the 432-identity
  plan summary and future-root absence, no decoder, no root;
- ``--d12-batch``: n128 (216 paired calls) then n256 (216), both widths
  always measured (<=432 scientific calls, <=62 setup units); refuses
  unless ``--execution-authorized`` is passed (default false; refusal
  happens before any root creation, decoder binding or Model-F load) and
  requires the injected production decoder adapter, which only this runner
  constructs;
- ``--verify``: read-only recomputation of a completed six-file root with
  zero skip, zero decoder calls; exits FAIL on any partial or
  engineering-blocked root.

One fresh root per run; refuses overwrite, protected roots and partial/adapted
runs (single process, no retry, no resume, no seed search, no adaptive stop).
A1/R3/D11 evidence is contextual only and can never enter the D12 gate:
decoder records carry ``batch_id == d12-finite-l1-degree-v1`` and the gate
constructor rejects anything else.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))

from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d12_finite_l1_degree as d12)

_R2_RUNNER_PATH = ROOT / "scripts" / "v72p2d10_mixed_degree_l1_development.py"


def _load_r2_runner():
    # Reuse: prior-chain, block, CSV/JSON and parse helpers live in the R2
    # runner; import them read-only instead of copying (R2 files untouched).
    spec = importlib.util.spec_from_file_location(
        "v72p2d10_r2_runner_reuse_d12", str(_R2_RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["v72p2d10_r2_runner_reuse_d12"] = module
    spec.loader.exec_module(module)
    return module


_r2run = _load_r2_runner()

EVIDENCE_FILES = d12.EVIDENCE_FILES
FROZEN_COMMAND = d12.FROZEN_COMMAND

DECODER_RECORD_COLUMNS = (
    "call_idx", "width", "arm", "graph_seed", "block_seed", "batch_id",
    "exact", "syndrome_ok", "iterations", "status",
    "residual_syndrome_weight", "belief_provenance", "prior_mass_on_truth",
    "wall_s", "crash", "error")
GRAPH_RECORD_COLUMNS = _r2run.GRAPH_RECORD_COLUMNS
ARM_SUMMARY_COLUMNS = (
    "width", "arm", "scope", "graph_seed", "blocks", "exact_count",
    "syndrome_valid_count")


def _peak_rss_bytes():
    # Linux ru_maxrss is KiB; single-process aggregate = this process.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _arm_rows(records):
    rows = []
    for width in d12.D12_WIDTHS:
        for arm in d12.ARMS:
            for graph_seed in d12.GRAPH_SEEDS[width]:
                scoped = [rec for rec in records
                          if int(rec["width"]) == width and rec["arm"] == arm
                          and int(rec["graph_seed"]) == graph_seed]
                rows.append({
                    "width": width, "arm": arm, "scope": "graph",
                    "graph_seed": graph_seed, "blocks": len(scoped),
                    "exact_count": sum(1 for rec in scoped if rec["exact"]),
                    "syndrome_valid_count":
                        sum(1 for rec in scoped if rec["syndrome_ok"])})
            pooled = [rec for rec in records
                      if int(rec["width"]) == width and rec["arm"] == arm]
            rows.append({
                "width": width, "arm": arm, "scope": "pooled",
                "graph_seed": "POOLED", "blocks": len(pooled),
                "exact_count": sum(1 for rec in pooled if rec["exact"]),
                "syndrome_valid_count":
                    sum(1 for rec in pooled if rec["syndrome_ok"])})
    return rows


def _degree_table_meta():
    return {"%s:%d" % (arm, width): {
        "n": cell["n"], "m": cell["m"],
        "var_counts": cell["var_counts"],
        "check_counts": cell["check_counts"]}
        for (arm, width), cell in sorted(d12.DEGREE_TABLE.items())}


def _budget_meta():
    return {
        "scientific_calls": d12.SCIENTIFIC_CALL_CEILING,
        "setup_calls": d12.SETUP_CALL_CEILING,
        "wall_s": d12.WALL_BUDGET_S,
        "per_call_s": d12.PER_CALL_BUDGET_S,
        "rss_bytes": d12.RSS_BUDGET_BYTES,
        "processes": 1,
        "retry": False, "resume": False,
        "seed_search": False, "adaptive_stop": False,
    }


# --------------------------------------------------------------------------- #
# batch (both widths always measured; no conditional progression)
# --------------------------------------------------------------------------- #
def run_d12_batch(out_root, model_f_root, decode_fn, syndrome_fn, *,
                  build_graph_fn=None, load_prior_fn=None, sample_fn=None,
                  floor_fn=None, now_fn=None, rss_fn=None):
    """Execute and persist one authorized D12 batch (injected decoder).

    ``decode_fn``/``syndrome_fn`` are explicit injections supplied by the
    caller (the ``--d12-batch`` entrypoint constructs the production
    adapter). Both widths are always measured: 216 paired calls each.
    """
    resolved = d12.refuse_out_root(out_root)
    plan = d12.build_full_plan()
    build_graph_fn = build_graph_fn or d12.build_graph
    load_prior_fn = load_prior_fn or _r2run.load_prior_chain
    now = now_fn or time.monotonic
    rss_fn = rss_fn or _peak_rss_bytes
    t0 = float(now())
    log_lines = []

    def log(message):
        line = _r2run._log_line(message)
        log_lines.append(line)
        print(line)

    p_b, p_f, p1 = load_prior_fn(model_f_root)
    setup_calls = d12.SETUP_FIXED_UNITS
    log("prior chain loaded from %s" % model_f_root)
    blocks = {}
    for width in d12.D12_WIDTHS:
        blocks[width] = _r2run.prepare_blocks(
            p_b, p_f, p1, width, d12.BLOCK_SEEDS[width], sample_fn=sample_fn,
            floor_fn=floor_fn)
        setup_calls += len(d12.BLOCK_SEEDS[width])
        log("sampled matched blocks width=%d count=%d"
            % (width, len(d12.BLOCK_SEEDS[width])))
    graphs = {}
    graph_rows = []
    for width in d12.D12_WIDTHS:
        for arm in d12.ARMS:
            for graph_seed in d12.GRAPH_SEEDS[width]:
                start = float(now())
                graph = build_graph_fn(arm, width, graph_seed)
                graph_rows.append(
                    _r2run._graph_row(graph, float(now()) - start))
                graphs[(arm, width, graph_seed)] = graph
                setup_calls += 1
    admitted = sum(1 for row in graph_rows if row["admitted"])
    log("built %d graphs admitted=%d" % (len(graph_rows), admitted))
    if setup_calls != d12.SETUP_CALL_CEILING:
        raise RuntimeError("setup unit count %d != frozen %d"
                           % (setup_calls, d12.SETUP_CALL_CEILING))

    width_results = []
    records: list[dict] = []
    for width in d12.D12_WIDTHS:
        outcome = d12.execute_width(width, plan, graphs, blocks, decode_fn,
                                    syndrome_fn, now=now, rss_fn=rss_fn)
        records.extend(outcome["records"])
        tallies = outcome["tallies"]
        width_results.append({
            "width": width,
            "exact": {arm: list(tallies.exact[arm]) for arm in d12.ARMS},
            "pools": {arm: tallies.pool(arm) for arm in d12.ARMS},
            "paired": outcome["paired"],
            "stable": dict(outcome["stable"]),
            "classification": None,
            "engineering_reason": outcome["engineering_reason"],
            "decoder_calls": outcome["decoder_calls"]})
        log("width=%d pools=%s stable=%s reason=%s"
            % (width, width_results[-1]["pools"],
               width_results[-1]["stable"],
               outcome["engineering_reason"] or "none"))
    paired_pooled = d12.describe_paired(records, None)
    engineering_reason = "; ".join(
        "width %d: %s" % (w["width"], w["engineering_reason"])
        for w in width_results if w["engineering_reason"])
    t128 = d12.tallies_from_d12_records(records, 128)
    t256 = d12.tallies_from_d12_records(records, 256)
    p128 = d12.describe_paired(records, 128)
    p256 = d12.describe_paired(records, 256)
    terminal = d12.route_terminal(t128, t256, p128, p256,
                                 engineering_reason)
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn())
    budget_violations = []
    if len(records) > d12.SCIENTIFIC_CALL_CEILING:
        budget_violations.append("scientific calls exceed ceiling")
    if wall_s > d12.WALL_BUDGET_S:
        budget_violations.append("wall budget exceeded")
    if peak_rss >= d12.RSS_BUDGET_BYTES:
        budget_violations.append("RSS budget exceeded")
    log("widths_dispatched=%s terminal=%s"
        % ([w["width"] for w in width_results], terminal))

    resolved.mkdir(parents=True)
    _r2run._write_json(resolved / "manifest.json", {
        "schema": "v72p2d12_finite_l1_degree_manifest_v1",
        "change_id": d12.CHANGE_ID, "cycle": d12.CYCLE_ID,
        "claim_ceiling": d12.CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "model_f_root": str(model_f_root), "out_root": str(resolved),
        "l1_only": True, "batch_id": d12.D12_BATCH_ID,
        "field": {"q": d12.Q, "poly": d12.POLY,
                  "factory": "GF2mField.create(32)"},
        "arms": list(d12.ARMS), "arm_roles": dict(d12.ARM_ROLE),
        "lambda2": dict(d12.LAMBDA2),
        "reference_arm": d12.REFERENCE_ARM,
        "widths": list(d12.D12_WIDTHS),
        "degree_table": _degree_table_meta(),
        "graph_seeds": {str(w): list(d12.GRAPH_SEEDS[w])
                        for w in d12.D12_WIDTHS},
        "block_seeds": {str(w): list(d12.BLOCK_SEEDS[w])
                        for w in d12.D12_WIDTHS},
        "coefficient_rule":
            "v10_seed(d10:coeff:{width}:{graph_seed}) -> default_rng -> "
            "integers(1,32) per edge in sorted (variable, check) order",
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": d12.DECODER_MAX_ITER,
                    "damping_alpha": d12.DAMPING_ALPHA,
                    "warm_beliefs": None, "schedule": "cold row-layered"},
        "matrix": {"planned_calls": len(plan),
                   "shape": "3 arms x 2 widths x 6 graphs x 12 blocks",
                   "call_order": ("n128 then n256, both always measured; "
                                  "within a width reference then "
                                  "challengers -> graph seed asc -> "
                                  "block seed asc"),
                   "progress_rule": "none (no conditional progression)"},
        "budgets": _budget_meta(),
        "setup_calls": setup_calls,
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": d12.AUTHORIZATION,
        "predecessor_boundary": ("A1/R3/D11 evidence is contextual only; "
                                 "D12 gates accept only batch_id=%s records"
                                 % d12.D12_BATCH_ID),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    _r2run._write_csv(resolved / "decoder_records.csv",
                      DECODER_RECORD_COLUMNS, records)
    _r2run._write_csv(resolved / "graph_records.csv", GRAPH_RECORD_COLUMNS,
                      graph_rows)
    _r2run._write_csv(resolved / "arm_summary.csv", ARM_SUMMARY_COLUMNS,
                      _arm_rows(records))
    summary = {
        "schema": "v72p2d12_finite_l1_degree_summary_v1",
        "change_id": d12.CHANGE_ID, "cycle": d12.CYCLE_ID,
        "claim_ceiling": d12.CLAIM_CEILING,
        "terminal": terminal,
        "widths_dispatched": [w["width"] for w in width_results],
        "width_results": width_results,
        "paired_pooled": paired_pooled,
        "engineering_reason": engineering_reason,
        "scientific_calls": len(records),
        "planned_calls": len(plan),
        "setup_calls": setup_calls,
        "exact_count": sum(1 for rec in records if rec["exact"]),
        "syndrome_valid_count": sum(1 for rec in records
                                    if rec["syndrome_ok"]),
        "call_idx_first": 0 if records else None,
        "call_idx_last": len(records) - 1 if records else None,
        "wall_s": wall_s, "peak_rss_bytes": peak_rss,
        "budget_violations": budget_violations,
        "l1_only": True, "batch_id": d12.D12_BATCH_ID,
        "model_f_root": str(model_f_root),
        "out_root": str(resolved), "budgets": _budget_meta(),
    }
    _r2run._write_json(resolved / "summary.json", summary)
    log_lines.append(_r2run._log_line(
        "D12 terminal=%s calls=%d setup=%d wall_s=%.3f"
        % (terminal, len(records), setup_calls, wall_s)))
    with open(resolved / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("".join(line + "\n" for line in log_lines))
    return summary


# --------------------------------------------------------------------------- #
# verify (read-only; zero decoder calls; zero skip; fail-closed)
# --------------------------------------------------------------------------- #
def verify_root(out_root, build_graph_fn=None):
    """Recompute a completed D12 root from its evidence; fail-closed."""
    root = Path(out_root)
    build_graph_fn = build_graph_fn or d12.build_graph
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
    graph_rows = _r2run._read_csv(root / "graph_records.csv")
    decoder_rows = _r2run._read_csv(root / "decoder_records.csv")
    arm_rows = _r2run._read_csv(root / "arm_summary.csv")

    if manifest.get("batch_id") != d12.D12_BATCH_ID \
            or summary.get("batch_id") != d12.D12_BATCH_ID:
        violations.append("batch_id tag mismatch (predecessor boundary)")

    plan = d12.build_full_plan()
    plan_by_key = {(e["width"], e["arm"], e["graph_seed"], e["block_seed"]): e
                   for e in plan}
    checked = agreements = skipped = 0
    records: list[dict] = []
    for index, row in enumerate(decoder_rows):
        key = (_r2run._as_int(row["width"]), row["arm"],
               _r2run._as_int(row["graph_seed"]),
               _r2run._as_int(row["block_seed"]))
        entry = plan_by_key.get(key)
        if entry is None:
            violations.append("decoder row %d not in frozen plan: %s"
                              % (index, key))
        elif int(entry["call_idx"]) != index:
            violations.append("decoder row %d call_idx %s != planned %d"
                              % (index, row["call_idx"], entry["call_idx"]))
        if row.get("batch_id") != d12.D12_BATCH_ID:
            violations.append("decoder row %d batch_id tag missing" % index)
        ok = True
        crash = _r2run._as_bool(row["crash"])
        exact = _r2run._as_bool(row["exact"])
        syndrome_ok = _r2run._as_bool(row["syndrome_ok"])
        iterations = _r2run._as_int(row["iterations"])
        residual = _r2run._as_int(row["residual_syndrome_weight"])
        wall = _r2run._as_float(row["wall_s"])
        prior_mass = _r2run._as_float(row["prior_mass_on_truth"])
        if exact and not syndrome_ok:
            violations.append("decoder row %d exact without syndrome_ok "
                              "(metric isolation)" % index)
            ok = False
        if crash:
            if iterations != -1 or residual != -1 or exact or syndrome_ok:
                violations.append("decoder row %d crash record inconsistent"
                                  % index)
                ok = False
        else:
            if not 0 <= iterations <= d12.DECODER_MAX_ITER:
                violations.append("decoder row %d iterations out of range: %d"
                                  % (index, iterations))
                ok = False
            if residual < 0:
                violations.append("decoder row %d residual weight missing"
                                  % index)
                ok = False
            if not str(row["belief_provenance"]).strip():
                violations.append("decoder row %d provenance missing" % index)
                ok = False
        if not 0.0 <= prior_mass <= 1.0:
            violations.append("decoder row %d prior mass out of range"
                              % index)
            ok = False
        if not str(row["status"]).strip():
            violations.append("decoder row %d empty status" % index)
            ok = False
        if wall < 0.0 or wall > d12.PER_CALL_BUDGET_S:
            violations.append("decoder row %d per-call wall out of budget: %s"
                              % (index, row["wall_s"]))
            ok = False
        records.append({"call_idx": index, "width": key[0], "arm": key[1],
                        "graph_seed": key[2], "block_seed": key[3],
                        "batch_id": row.get("batch_id"),
                        "exact": exact, "syndrome_ok": syndrome_ok,
                        "crash": crash, "wall_s": wall})
        checked += 1
        if ok:
            agreements += 1

    # Both widths are always measured in D12 (no conditional progression).
    dispatched = []
    for record in records:
        if record["width"] not in dispatched:
            dispatched.append(record["width"])
    if dispatched != list(d12.D12_WIDTHS):
        violations.append("dispatched widths %s != always-measured %s"
                          % (dispatched, list(d12.D12_WIDTHS)))
    for width in d12.D12_WIDTHS:
        for entry in (e for e in plan if e["width"] == width):
            if entry["call_idx"] >= len(records) or not any(
                    rec["call_idx"] == entry["call_idx"] for rec in records):
                violations.append("planned call %d missing (zero-skip)"
                                  % entry["call_idx"])
                skipped += 1

    recomputed_arm_rows = _arm_rows(records)
    stored_arm_keys = {(row["width"], row["arm"], row["scope"],
                        row["graph_seed"]): row for row in arm_rows}
    for row in recomputed_arm_rows:
        key = (str(row["width"]), row["arm"], row["scope"],
               str(row["graph_seed"]))
        stored = stored_arm_keys.get(key)
        if stored is None:
            violations.append("arm_summary row missing: %s" % (key,))
            continue
        for column in ("blocks", "exact_count", "syndrome_valid_count"):
            if _r2run._as_int(stored[column]) != int(row[column]):
                violations.append("arm_summary %s %s stored=%s recomputed=%d"
                                  % (key, column, stored[column],
                                     int(row[column])))

    width_results = summary.get("width_results", [])
    try:
        t128 = d12.tallies_from_d12_records(records, 128)
        t256 = d12.tallies_from_d12_records(records, 256)
    except ValueError as exc:
        violations.append("tallies not rebuildable: %s" % exc)
        t128 = t256 = None
    if t128 is not None and t256 is not None:
        p128 = d12.describe_paired(records, 128)
        p256 = d12.describe_paired(records, 256)
        for result in width_results:
            width = int(result["width"])
            tallies = t128 if width == 128 else t256
            for arm in d12.ARMS:
                if list(tallies.exact[arm]) != result.get("exact", {}).get(
                        arm):
                    violations.append("width %d arm %s stored exact != "
                                      "recomputed" % (width, arm))
            for arm in d12.ARMS:
                if tallies.pool(arm) != result.get("pools", {}).get(arm):
                    violations.append("width %d arm %s stored pool != "
                                      "recomputed" % (width, arm))
            recomputed_stable = {
                arm: d12.is_stable(
                    tallies, arm, str(result.get("engineering_reason", "")))
                for arm in d12.ARMS}
            if recomputed_stable != result.get("stable"):
                violations.append("width %d stored stable != recomputed"
                                  % width)
            if result["engineering_reason"]:
                violations.append("width %d engineering-blocked (fail-closed)"
                                  % width)
        recomputed_reason = "; ".join(
            "width %d: %s" % (w["width"], w["engineering_reason"])
            for w in width_results if w["engineering_reason"])
        if d12.route_terminal(t128, t256, p128, p256,
                             recomputed_reason) != summary.get("terminal"):
            violations.append("terminal stored=%r recomputed mismatch"
                              % (summary.get("terminal"),))
        for challenger in d12.CHALLENGERS:
            for width, paired in ((128, p128), (256, p256)):
                stored = next(
                    (w["paired"][challenger] for w in width_results
                     if int(w["width"]) == width), None)
                for field in ("challenger_only", "reference_only",
                              "concordant", "trials"):
                    if stored is None or stored.get(field) != paired[
                            challenger][field]:
                        violations.append(
                            "width %d %s paired %s stored != recomputed"
                            % (width, challenger, field))
    if bool(summary.get("l1_only")) is not True \
            or bool(manifest.get("l1_only")) is not True:
        violations.append("l1_only flag not true")

    if len(decoder_rows) != int(summary.get("scientific_calls", -1)):
        violations.append("stored calls %d != summary %r"
                          % (len(decoder_rows),
                             summary.get("scientific_calls")))
    if len(decoder_rows) > d12.SCIENTIFIC_CALL_CEILING:
        violations.append("stored calls exceed scientific ceiling")
    if int(summary.get("setup_calls", -1)) != d12.SETUP_CALL_CEILING:
        violations.append("setup calls != frozen %d: %r"
                          % (d12.SETUP_CALL_CEILING,
                             summary.get("setup_calls")))
    if _r2run._as_float(summary.get("wall_s", -1.0)) > d12.WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if _r2run._as_int(summary.get("peak_rss_bytes", -1)) \
            >= d12.RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")
    max_call_wall = max((_r2run._as_float(rec["wall_s"])
                         for rec in decoder_rows), default=0.0)
    if max_call_wall > d12.PER_CALL_BUDGET_S:
        violations.append("per-call wall exceeds budget: %s" % max_call_wall)

    for row in graph_rows:
        graph = build_graph_fn(row["arm"], _r2run._as_int(row["width"]),
                               _r2run._as_int(row["graph_seed"]))
        key = (row["width"], row["arm"], row["graph_seed"])
        if graph["status"] != row["status"] \
                or bool(graph["admitted"]) != _r2run._as_bool(row["admitted"]) \
                or int(graph["E"]) != _r2run._as_int(row["E"]) \
                or str(graph["failure_reason"]) != row["failure_reason"]:
            violations.append("graph %s status/admission/E mismatch" % (key,))
            continue
        if str(row["status"]) != "ok" or not _r2run._as_bool(row["admitted"]):
            violations.append("graph %s not admitted (fail-closed)" % (key,))
            continue
        structure = graph.get("structure")
        if structure and str(row.get("admission", "")).strip():
            recomputed_admission = json.dumps(structure["admission"],
                                              sort_keys=True)
            if _r2run._cell(row.get("admission")) != recomputed_admission:
                violations.append("graph %s admission stored=%r recomputed=%r"
                                  % (key, row.get("admission"),
                                     recomputed_admission))

    print("VERIFY checked_calls=%d agreements=%d skipped=%d violations=%d"
          % (checked, agreements, skipped, len(violations)))
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    ok = not violations
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return ok


# --------------------------------------------------------------------------- #
# CLI (D1204: --d12-batch requires explicit --execution-authorized)
# --------------------------------------------------------------------------- #
def build_parser():
    parser = argparse.ArgumentParser(
        description="D12 finite L1 degree refinement runner")
    parser.add_argument("--d12-batch", action="store_true",
                        help="run the frozen 432-call D12 matrix (requires "
                             "--execution-authorized from a separate "
                             "explicit authorization)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for "
                             "--d12-batch; default false "
                             "(fail-closed, no-write/no-bind)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--profile-only", action="store_true",
                        help="pre-decoder graph construction profile (no "
                             "decoder, no root)")
    parser.add_argument("--model-f-root", default=d12.MODEL_F_INPUT_ROOT,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    return parser


def profile_only():
    """D1209 profile helper: real builders + full plan, no decoder, no root."""
    profile = d12.profile_graphs()
    plan = d12.build_full_plan()
    future = Path(d12.FUTURE_ROOT)
    resolved = future.resolve() if future.is_absolute() \
        else (ROOT / future).resolve()
    return {
        "graphs": profile["graphs"],
        "admitted": sum(1 for g in profile["graphs"] if g["admitted"]),
        "total_graphs": len(profile["graphs"]),
        "seed_replacements": profile["seed_replacements"],
        "replacement_seeds_used": profile["replacement_seeds_used"],
        "frozen_seed_failures": profile["frozen_seed_failures"],
        "plan_calls": len(plan),
        "plan_per_width": {str(w): len(d12.build_call_plan(w))
                           for w in d12.D12_WIDTHS},
        "future_root": str(resolved),
        "future_root_absent": not resolved.exists(),
        "decoder_calls": 0,
        "wall_s": profile["wall_s"],
    }


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--d12-batch", args.d12_batch),
                                        ("--verify", args.verify),
                                        ("--profile-only",
                                         args.profile_only)) if flag]
    if len(selected) != 1:
        parser.error("exactly one of --d12-batch, --verify or "
                     "--profile-only is required")
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
        return 0
    # D1204: refuse --d12-batch before root creation and before any decoder
    # binding or Model-F load while --execution-authorized is false.
    if args.d12_batch and not args.execution_authorized:
        print("refusing --d12-batch: %s (pass --execution-authorized only "
              "under a separate explicit authorization)"
              % d12.AUTHORIZATION, file=sys.stderr)
        return 2
    if args.out_root is None:
        parser.error("%s requires --out-root" % selected[0])
    if args.verify:
        return 0 if verify_root(args.out_root) else 1
    from comparison_bench.formal_ir import (  # lazy production adapter
        v35_algorithm_development as v35)
    summary = run_d12_batch(
        args.out_root, args.model_f_root,
        decode_fn=v35.decode_row_layered_fftqspa,
        syndrome_fn=v35.syndrome_of_gf32)
    print("D12 terminal=%s calls=%d setup=%d"
          % (summary["terminal"], summary["scientific_calls"],
             summary["setup_calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
