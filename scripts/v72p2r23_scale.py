"""R23 synthetic scale probe runner — readiness paths.

Frozen stage-1 ARGV (exact, venv only; default-safe dry-run):

    .venv/bin/python scripts/v72p2r23_scale.py --profile-only

Paths:

- ``--profile-only``: validate the frozen 96-call plan, print per-cell
  D9 geometry + budget meta + future-root absence; zero decoder calls,
  zero graph builds, zero filesystem writes;
- ``--r23-batch``: the frozen matrix (96 scientific calls max, 12 setup
  graphs built at R23c start with per-build sub-caps n128<=60 s /
  n1024<=300 s, 12/12 admission required before any decoder binding);
  refuses with rc2 unless ``--execution-authorized`` is passed (default
  false; refusal happens before any root creation or decoder bind) and
  requires the injected production decoder adapter, which only this
  runner constructs (synthetic oracle-only diagnostic: NO Model-F, NO
  prior chain, NO APP/L1/transfer);
- ``--verify``: read-only recomputation of a completed six-file root with
  zero skip, zero decoder calls; exits FAIL on any partial or
  engineering-blocked root.

One fresh root per run; refuses overwrite and protected roots (single
process, no retry, no resume, no seed search, no adaptive stop).
D19 reference graphs never enter the S gate: decoder records carry
``batch_id == r23-scale-s-v1`` and the gate constructor rejects
anything else.
"""
from __future__ import annotations

import argparse
import csv
import inspect
import json
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))

from comparison_bench.formal_ir import (  # noqa: E402
    v72p2r23_scale as r23)

EVIDENCE_FILES = r23.EVIDENCE_FILES
FROZEN_COMMAND = r23.FROZEN_COMMAND

DECODER_RECORD_COLUMNS = (
    "call_idx", "width", "n", "m", "ratio", "arm",
    "graph_seed", "block_seed", "batch_id", "exact",
    "syndrome_ok", "undetected", "oracle", "graded", "belief_provenance",
    "iterations", "status", "residual_syndrome_weight",
    "oracle_weight", "prior_mass_on_truth",
    "wall_s", "crash", "error", "disclosed_bits")
GRAPH_RECORD_COLUMNS = (
    "arm", "width", "ratio", "graph_seed", "n", "m", "E", "status",
    "admitted", "failure_reason", "admission", "construction_wall_s")
CELL_SUMMARY_COLUMNS = (
    "width", "ratio", "scope", "graph_ordinal", "blocks", "exact_count",
    "syndrome_valid_count", "undetected_count")


def _peak_rss_bytes():
    # Linux ru_maxrss is KiB; single-process aggregate = this process.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _log_line(message):
    return "[%s] %s" % (time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                      time.gmtime()), message)


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def _write_csv(path, columns, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})


def _read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _as_int(value):
    return int(str(value).strip())


def _as_float(value):
    return float(str(value).strip())


def _as_bool(value):
    text = str(value).strip().lower()
    if text in ("1", "true", "yes"):
        return True
    if text in ("0", "false", "no", ""):
        return False
    raise ValueError("not a boolean: %r" % (value,))


def _cell(value):
    return str(value if value is not None else "").strip()


# --------------------------------------------------------------------------- #
# cell summary rows (pooled + per-graph; exact/syndrome/undetected separate)
# --------------------------------------------------------------------------- #
def _cell_rows(records):
    rows = []
    for width in r23.WIDTHS:
        for ratio in r23.RATIOS:
            key = r23.RATIO_KEY[ratio]
            scoped = [rec for rec in records
                      if int(rec["width"]) == int(width)
                      and str(rec["ratio"]) == key]
            seeds = r23.GRAPH_SEEDS[(int(width), key)]
            for ordinal, seed in enumerate(seeds):
                cell = [rec for rec in scoped
                        if int(rec["graph_seed"]) == int(seed)]
                rows.append({
                    "width": width, "ratio": key, "scope": "graph",
                    "graph_ordinal": ordinal, "blocks": len(cell),
                    "exact_count": sum(1 for rec in cell if rec["exact"]),
                    "syndrome_valid_count":
                        sum(1 for rec in cell if rec["syndrome_ok"]),
                    "undetected_count":
                        sum(1 for rec in cell if rec["undetected"])})
            rows.append({
                "width": width, "ratio": key, "scope": "pooled",
                "graph_ordinal": "POOLED", "blocks": len(scoped),
                "exact_count": sum(1 for rec in scoped if rec["exact"]),
                "syndrome_valid_count":
                    sum(1 for rec in scoped if rec["syndrome_ok"]),
                "undetected_count":
                    sum(1 for rec in scoped if rec["undetected"])})
    return rows


def _cell_table_meta():
    return [{"arm": r23.ARM, "n": int(width), "m": r23.ROWS[(width, key)],
             "ratio": key,
             "var_counts": dict(r23.degree_cell(width, key)["var_counts"]),
             "check_counts": dict(r23.degree_cell(width, key)[
                 "check_counts"]),
             "E": r23.degree_cell(width, key)["E"],
             "rate": r23.degree_cell(width, key)["rate"],
             "disclosed_bits": r23.disclosed_bits(
                 r23.ROWS[(width, key)])}
            for width in r23.WIDTHS for key in
            [r23.RATIO_KEY[r] for r in r23.RATIOS]]


def _budget_meta():
    return {
        "scientific_calls": r23.SCIENTIFIC_CALL_CEILING,
        "setup_calls": r23.SETUP_CALL_CEILING,
        "wall_s": r23.WALL_BUDGET_S,
        "per_call_s": r23.PER_CALL_BUDGET_S,
        "per_build_s": dict(r23.PER_BUILD_SUBCAP_S),
        "rss_bytes": r23.RSS_BUDGET_BYTES,
        "processes": 1,
        "retry": False, "resume": False,
        "seed_search": False, "adaptive_stop": False,
    }


def _graph_row(graph, wall_s):
    structure = graph.get("structure") or {}
    return {
        "arm": graph["arm"], "width": graph["width"],
        "ratio": graph["ratio"], "graph_seed": graph["graph_seed"],
        "n": graph["n"], "m": graph["m"], "E": graph["E"],
        "status": graph["status"], "admitted": bool(graph["admitted"]),
        "failure_reason": graph["failure_reason"],
        "admission": json.dumps((structure.get("admission") or {}),
                                sort_keys=True),
        "construction_wall_s": round(float(wall_s), 6),
    }


# --------------------------------------------------------------------------- #
# Production binder (narrow; resolve + signature-validate only)
# --------------------------------------------------------------------------- #
def _require_signature(fn, required, name):
    """Inspect-only contract check: ``fn`` callable with ``required`` params.

    No call, no decode — pure ``inspect.signature``. Raises before any root
    creation or decoder contact on mismatch.
    """
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


def bind_production_adapters():
    """Narrow binder: decoder kernels only, validated, zero calls.

    Synthetic path carries NO Model-F / prior chain: the oracle prior is
    composed in-module from frozen block seeds. Resolving never invokes:
    decoder calls happen only inside the authorized orchestrator after plan
    validation.
    """
    from comparison_bench.formal_ir import (  # lazy production bind
        v35_algorithm_development as v35)

    decode_fn = _require_signature(
        v35.decode_row_layered_fftqspa,
        ["h_matrix", "priors", "syndromes", "max_iter", "damping_alpha",
         "warm_beliefs", "field"], "decode_fn")
    syndrome_fn = _require_signature(
        v35.syndrome_of_gf32, ["matrix", "vector"], "syndrome_fn")
    return {
        "decode_fn": decode_fn,
        "syndrome_fn": syndrome_fn,
        "sample_fn": r23.sample_oracle_block,
        "build_fn": r23.build_graph,
    }


# --------------------------------------------------------------------------- #
# Plan validation (frozen order + identity, before bind/build/decode)
# --------------------------------------------------------------------------- #
def _validate_call_plan(plan):
    """Contract-check the frozen 96-plan BEFORE binding/building/decoding.

    Frozen order (width ascending; ratio ascending; graphs ascending;
    blocks ascending) with frozen cells, seeds and oracle pairing; arm S
    throughout. Any deviation raises before any adapter is bound, any
    graph is built, or the root is touched.
    """
    if len(plan) != 96:
        raise ValueError("plan has %d calls, frozen 96" % len(plan))
    pos = 0
    for width in r23.WIDTHS:
        for ratio in r23.RATIOS:
            key = r23.RATIO_KEY[ratio]
            m = r23.ROWS[(width, key)]
            for graph_seed in r23.GRAPH_SEEDS[(width, key)]:
                for block_seed in r23.BLOCK_SEEDS[(width, key)]:
                    entry = plan[pos]
                    pos += 1
                    if entry.get("call_idx") != pos - 1 \
                            or int(entry.get("width", -1)) != width \
                            or int(entry.get("n", -1)) != width \
                            or int(entry.get("m", -1)) != m \
                            or str(entry.get("ratio", "")) != key \
                            or entry.get("arm") != r23.ARM \
                            or int(entry.get("graph_seed", -1)) \
                            != int(graph_seed) \
                            or int(entry.get("block_seed", -1)) \
                            != int(block_seed) \
                            or int(entry.get("disclosed_bits", -1)) \
                            != r23.disclosed_bits(m):
                        raise ValueError(
                            "plan identity/order violated at position %d: %r"
                            % (pos - 1, entry))
    if pos != len(plan):
        raise ValueError("plan order check covered %d/%d entries"
                         % (pos, len(plan)))
    return plan


# --------------------------------------------------------------------------- #
# Batch orchestrator (plan-first; 12/12 admission; no filesystem writes)
# --------------------------------------------------------------------------- #
def run_authorized_batch(out_root, *, adapters=None,
                         now_fn=None, rss_fn=None):
    """Execute the frozen R23 matrix and return the evidence bundle (writes).

    ``adapters`` is a flat dict with ``decode_fn``/``syndrome_fn``/
    ``sample_fn``/``build_fn``; ``None`` production-binds inside, AFTER plan
    validation and the refuse probe. Returns the bundle consumed by
    :func:`write_batch_root`; creates no files and no directories.
    """
    plan = r23.build_call_plan()
    _validate_call_plan(plan)
    resolved = r23.refuse_out_root(out_root)  # probe only; creates nothing
    if adapters is None:
        inj = bind_production_adapters()
    else:
        inj = dict(adapters)
    missing = [key for key in ("decode_fn", "syndrome_fn", "sample_fn",
                               "build_fn") if inj.get(key) is None]
    if missing:
        raise ValueError("adapters %s must be explicitly injected "
                         "(no decoder is bound without them)" % (missing,))
    decode_fn = inj["decode_fn"]
    syndrome_fn = inj["syndrome_fn"]
    sample_fn = inj["sample_fn"]
    build_fn = inj["build_fn"]
    now = now_fn or time.monotonic
    rss_fn = rss_fn or _peak_rss_bytes
    t0 = float(now())
    log_lines = []

    def log(message):
        line = _log_line(message)
        log_lines.append(line)
        print(line)

    graphs, graph_rows = {}, []
    for width in r23.WIDTHS:
        for ratio in r23.RATIOS:
            key = r23.RATIO_KEY[ratio]
            for graph_seed in r23.GRAPH_SEEDS[(width, key)]:
                start = float(now())
                graph = build_fn(int(width), key, int(graph_seed))
                graphs[(int(width), key, int(graph_seed))] = graph
                graph_rows.append(_graph_row(graph, float(now()) - start))
    admitted = sum(1 for row in graph_rows if row["admitted"])
    log("built %d graphs admitted=%d" % (len(graph_rows), admitted))
    build_violations = r23.check_build_budgets(graph_rows)
    if len(graph_rows) != r23.SETUP_CALL_CEILING:
        raise RuntimeError("setup graph count %d != frozen %d"
                           % (len(graph_rows), r23.SETUP_CALL_CEILING))
    blocks = {}
    for width in r23.WIDTHS:
        for ratio in r23.RATIOS:
            key = r23.RATIO_KEY[ratio]
            cell_blocks = {}
            for block_seed in r23.BLOCK_SEEDS[(width, key)]:
                cell_blocks[int(block_seed)] = sample_fn(
                    int(width), key, int(block_seed))
            blocks[(int(width), key)] = cell_blocks
    log("sampled oracle blocks count=%d"
        % sum(len(v) for v in blocks.values()))

    outcome = r23.execute_plan(plan, graphs, blocks, decode_fn, syndrome_fn,
                               now=now, rss_fn=rss_fn)
    records = outcome["records"]
    engineering_reason = outcome["failure"]
    # Frozen-order identity gate: every dispatched record must match the
    # frozen plan entry at its position. Any deviation is a contract STOP.
    for pos, record in enumerate(records):
        entry = plan[pos]
        for key in ("width", "ratio", "graph_seed", "block_seed"):
            if str(record[key]) != str(entry[key]):
                raise RuntimeError(
                    "dispatch order violated at position %d: %r != %r"
                    % (pos, {k: record.get(k) for k in
                             ("width", "ratio", "block_seed")}, entry))
        record["call_idx"] = pos
    log("dispatched=%d" % len(records))

    cell_results = []
    for width in r23.WIDTHS:
        for ratio in r23.RATIOS:
            key = r23.RATIO_KEY[ratio]
            try:
                tally = r23.cell_tally(records, int(width), key)
            except ValueError as exc:
                if not engineering_reason:
                    engineering_reason = ("cell tally not rebuildable: %s"
                                          % exc)
                tally = {"width": int(width), "ratio": key,
                         "E_g": [0] * r23.GRAPHS_PER_CELL, "E": 0}
            cell_results.append({"width": int(width), "ratio": key,
                                 "tally": tally,
                                 "engineering_reason": engineering_reason})
    # Frozen R23c-R1 batch gate: terminal ONLY from the anchor cells
    # (n1024@r65, n128@r65), the gap, and batch undetected. Per-cell
    # tallies stay descriptive diagnostics.
    anchor = {"%d:%s" % (c["width"], c["ratio"]): c for c in cell_results}
    e_hi = int(anchor["1024:r65"]["tally"]["E"])
    e_lo = int(anchor["128:r65"]["tally"]["E"])
    undetected_total = sum(1 for rec in records if rec["undetected"])
    terminal = r23.route_scaling_gate(e_hi, e_lo, undetected_total,
                                      engineering_reason)
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn())
    budget_violations = list(build_violations)
    if len(records) > r23.SCIENTIFIC_CALL_CEILING:
        budget_violations.append("scientific calls exceed ceiling")
    if wall_s > r23.WALL_BUDGET_S:
        budget_violations.append("wall budget exceeded")
    if peak_rss >= r23.RSS_BUDGET_BYTES:
        budget_violations.append("RSS budget exceeded")
    log("terminal=%s" % terminal)

    manifest = {
        "schema": "v72p2r23_scale_manifest_v1",
        "change_id": r23.CHANGE_ID, "cycle": r23.CYCLE_ID,
        "claim_ceiling": r23.CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "out_root": str(resolved),
        "batch_id": r23.R23_BATCH_ID,
        "field": {"q": r23.Q, "factory": "GF2mField.create(32)"},
        "arm": r23.ARM,
        "channel": {"family": "q-ary-symmetric", "p": r23.P_ERR,
                    "oracle": "truth-conditioned U2",
                    "prior_chain": "none (synthetic; Model-F not carried)"},
        "lambda_s": dict(r23.LAMBDA_S),
        "widths": list(r23.WIDTHS),
        "ratios": list(r23.RATIOS),
        "rows": {"%d:%s" % (w, r23.RATIO_KEY[r]): r23.ROWS[(w, r23.RATIO_KEY[r])]
                 for w in r23.WIDTHS for r in r23.RATIOS},
        "cells": _cell_table_meta(),
        "graph_seeds": {"%d:%s" % (w, r23.RATIO_KEY[r]):
                        list(r23.GRAPH_SEEDS[(w, r23.RATIO_KEY[r])])
                        for w in r23.WIDTHS for r in r23.RATIOS},
        "block_seeds": {"%d:%s" % (w, r23.RATIO_KEY[r]):
                        list(r23.BLOCK_SEEDS[(w, r23.RATIO_KEY[r])])
                        for w in r23.WIDTHS for r in r23.RATIOS},
        "coefficient_rule":
            "v10_seed(r23:scale:coeff:{width}:{ratio}:{graph_seed}) -> "
            "default_rng -> integers(1,32) per edge in sorted (variable, "
            "check) order",
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": r23.DECODER_MAX_ITER,
                    "damping_alpha": r23.DAMPING_ALPHA,
                    "warm_beliefs": None, "schedule": "cold single-pass",
                    "retry": False},
        "matrix": {"planned_calls": 96,
                   "shape": ("2 widths x 3 ratios x 2 graphs x 8 blocks, "
                             "single arm S"),
                   "call_order": ("width ascending; ratio ascending; "
                                  "graphs ascending; blocks ascending"),
                   "admission": "12/12 required before any decoder binding"},
        "budgets": _budget_meta(),
        "setup_graphs": len(graph_rows),
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": r23.AUTHORIZATION,
        "predecessor_boundary": ("predecessor evidence is contextual only; "
                                 "the S gate accepts only batch_id=%s "
                                 "records" % r23.R23_BATCH_ID),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    cell_rows = _cell_rows(records)
    per_cell = {}
    for cell in cell_results:
        tally = cell["tally"]
        per_cell["%d:%s" % (cell["width"], cell["ratio"])] = {
            "E": int(tally["E"]),
            "E_g": [int(v) for v in tally["E_g"]],
            "exact_frac": "%d/16" % int(tally["E"]),
            "descriptive_only": True,
            "engineering_reason": cell["engineering_reason"]}
    summary = {
        "schema": "v72p2r23_scale_summary_v1",
        "change_id": r23.CHANGE_ID, "cycle": r23.CYCLE_ID,
        "claim_ceiling": r23.CLAIM_CEILING,
        "terminal": terminal,
        "per_cell": per_cell,
        "scientific_calls": len(records),
        "planned_calls": 96,
        "setup_graphs": len(graph_rows),
        "exact_count": sum(1 for rec in records if rec["exact"]),
        "syndrome_valid_count": sum(1 for rec in records
                                    if rec["syndrome_ok"]),
        "undetected_count": sum(1 for rec in records
                                if rec["undetected"]),
        "call_idx_first": 0 if records else None,
        "call_idx_last": len(records) - 1 if records else None,
        "wall_s": wall_s, "peak_rss_bytes": peak_rss,
        "budget_violations": budget_violations,
        "batch_id": r23.R23_BATCH_ID,
        "out_root": str(resolved), "budgets": _budget_meta(),
    }
    log_lines.append(_log_line(
        "R23 terminal=%s calls=%d setup=%d wall_s=%.3f"
        % (terminal, len(records), len(graph_rows), wall_s)))
    return {
        "resolved": resolved,
        "manifest": manifest,
        "records": records,
        "graph_rows": graph_rows,
        "cell_rows": cell_rows,
        "summary": summary,
        "log_lines": log_lines,
    }


# --------------------------------------------------------------------------- #
# Never-overwrite writer (one mkdir + six files; no computation)
# --------------------------------------------------------------------------- #
def write_batch_root(bundle):
    """Persist one orchestrator bundle to its fresh root (never overwrite).

    Creates the probed-fresh directory and writes exactly the six frozen
    evidence files. An existing root raises ``FileExistsError`` here as
    well as at the orchestrator probe — nothing is ever overwritten.
    """
    resolved = bundle["resolved"]
    resolved.mkdir(parents=True)
    _write_json(resolved / "manifest.json", bundle["manifest"])
    _write_csv(resolved / "decoder_records.csv",
               DECODER_RECORD_COLUMNS, bundle["records"])
    _write_csv(resolved / "graph_records.csv", GRAPH_RECORD_COLUMNS,
               bundle["graph_rows"])
    _write_csv(resolved / "cell_summary.csv", CELL_SUMMARY_COLUMNS,
               bundle["cell_rows"])
    _write_json(resolved / "summary.json", bundle["summary"])
    with open(resolved / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("".join(line + "\n" for line in bundle["log_lines"]))
    return bundle["summary"]


# --------------------------------------------------------------------------- #
# verify (read-only; zero decoder calls; zero skip; fail-closed)
# --------------------------------------------------------------------------- #
def verify_root(out_root, build_fn=None):
    """Recompute a completed R23 root from its evidence; fail-closed."""
    root = Path(out_root)
    build_fn = build_fn or r23.build_graph
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
    graph_rows = _read_csv(root / "graph_records.csv")
    decoder_rows = _read_csv(root / "decoder_records.csv")
    cell_rows = _read_csv(root / "cell_summary.csv")

    if manifest.get("batch_id") != r23.R23_BATCH_ID \
            or summary.get("batch_id") != r23.R23_BATCH_ID:
        violations.append("batch_id tag mismatch (predecessor boundary)")
    if manifest.get("command") != FROZEN_COMMAND:
        violations.append("manifest command != frozen command")

    plan = r23.build_call_plan()
    plan_by_idx = {e["call_idx"]: e for e in plan}
    records: list[dict] = []
    for index, row in enumerate(decoder_rows):
        entry = plan_by_idx.get(index)
        problems: list[str] = []
        if entry is None:
            violations.append("decoder row %d beyond frozen plan" % index)
            continue
        if _as_int(row["call_idx"]) != index:
            violations.append("decoder row %d call_idx %s != planned %d"
                              % (index, row["call_idx"], index))
        for key in ("width", "ratio", "graph_seed", "block_seed"):
            if str(row[key]) != str(entry[key]):
                violations.append("decoder row %d %s %r != planned %r"
                                  % (index, key, row[key], entry[key]))
        if row.get("batch_id") != r23.R23_BATCH_ID:
            violations.append("decoder row %d batch_id tag missing" % index)
        if int(row["disclosed_bits"]) != r23.disclosed_bits(
                _as_int(row["m"])):
            violations.append("decoder row %d disclosed != 5m" % index)
        if row.get("arm") != r23.ARM:
            violations.append("decoder row %d arm != frozen S" % index)
        exact = _as_bool(row["exact"])
        syndrome_ok = _as_bool(row["syndrome_ok"])
        undetected = _as_bool(row["undetected"])
        oracle = _as_bool(row["oracle"])
        graded = _as_bool(row["graded"])
        iterations = _as_int(row["iterations"])
        residual = _as_int(row["residual_syndrome_weight"])
        weight = _as_int(row["oracle_weight"])
        wall = _as_float(row["wall_s"])
        crash = _as_bool(row["crash"])
        width = _as_int(row["width"])
        # Metric isolation: exact never without syndrome_ok; undetected
        # never merged into exact; every row is ORACLE/ungraded S.
        if exact and not syndrome_ok:
            problems.append("exact without syndrome_ok (metric isolation)")
        if undetected and exact:
            problems.append("undetected merged into exact")
        if not oracle or graded:
            problems.append("R23 row must be oracle/ungraded")
        if str(row["belief_provenance"]).strip() != "ORACLE":
            problems.append("ORACLE provenance must be ORACLE")
        if not 0 <= weight <= width:
            problems.append("oracle weight outside 0..n: %d" % weight)
        if crash:
            if iterations != -1 or residual != -1 or exact or syndrome_ok \
                    or undetected:
                problems.append("crash record inconsistent")
        else:
            if not 0 <= iterations <= r23.DECODER_MAX_ITER:
                problems.append("iterations out of range: %d" % iterations)
            if residual < 0:
                problems.append("residual weight missing")
        if str(row["status"]).strip() in ("",):
            problems.append("empty status")
        if wall < 0.0 or wall > r23.PER_CALL_BUDGET_S:
            problems.append("per-call wall out of budget: %s"
                            % row["wall_s"])
        for problem in problems:
            violations.append("decoder row %d %s" % (index, problem))
        records.append({"call_idx": index, "width": width,
                        "ratio": row["ratio"],
                        "graph_seed": _as_int(row["graph_seed"]),
                        "block_seed": _as_int(row["block_seed"]),
                        "batch_id": row.get("batch_id"),
                        "exact": exact, "syndrome_ok": syndrome_ok,
                        "undetected": undetected, "oracle": oracle,
                        "graded": graded, "crash": crash, "wall_s": wall})

    # Zero-skip: a complete root carries exactly the 96 planned calls.
    if len(decoder_rows) != 96:
        violations.append("stored calls %d != frozen 96 (zero-skip)"
                          % len(decoder_rows))

    # Shared paired identities per cell: both graphs carry the same
    # 8 oracle blocks.
    for width in r23.WIDTHS:
        for ratio in r23.RATIOS:
            key = r23.RATIO_KEY[ratio]
            for seed in r23.GRAPH_SEEDS[(width, key)]:
                got = sorted(rec["block_seed"] for rec in records
                             if rec["width"] == width
                             and rec["ratio"] == key
                             and rec["graph_seed"] == int(seed))
                if got != sorted(int(s)
                                 for s in r23.BLOCK_SEEDS[(width, key)]):
                    violations.append("cell %d:%s graph %d blocks %s "
                                      "!= shared 8 (pairing)"
                                      % (width, key, int(seed), got))

    recomputed_cell_rows = _cell_rows(records)
    stored_keys = {(row["width"], row["ratio"], row["scope"],
                    row["graph_ordinal"]): row for row in cell_rows}
    for row in recomputed_cell_rows:
        key = (str(row["width"]), row["ratio"], row["scope"],
               str(row["graph_ordinal"]))
        stored = stored_keys.get(key)
        if stored is None:
            violations.append("cell_summary row missing: %s" % (key,))
            continue
        for column in ("blocks", "exact_count", "syndrome_valid_count",
                       "undetected_count"):
            if _as_int(stored[column]) != int(row[column]):
                violations.append("cell_summary %s %s stored=%s recomputed=%d"
                                  % (key, column, stored[column],
                                     int(row[column])))

    # Gate recompute: descriptive per-cell tallies + frozen anchor rule.
    recomputed_E = {}
    for width in r23.WIDTHS:
        for ratio in r23.RATIOS:
            key = r23.RATIO_KEY[ratio]
            stored_cell = summary.get("per_cell", {}).get(
                "%d:%s" % (width, key), {})
            try:
                tally = r23.cell_tally(records, int(width), key)
            except ValueError as exc:
                violations.append("cell %d:%s tally not rebuildable: %s"
                                  % (width, key, exc))
                continue
            for tally_key in ("E",):
                if int(stored_cell.get(tally_key, -1)) != int(tally[tally_key]):
                    violations.append("stored %d:%s %s != recomputed"
                                      % (width, key, tally_key))
            if [int(v) for v in stored_cell.get("E_g", [])] != \
                    [int(v) for v in tally["E_g"]]:
                violations.append("stored %d:%s E_g != recomputed"
                                  % (width, key))
            recomputed_E["%d:%s" % (width, key)] = int(tally["E"])
    stored_hi = summary.get("per_cell", {}).get("1024:r65", {})
    stored_lo = summary.get("per_cell", {}).get("128:r65", {})
    recomputed_undetected = sum(1 for rec in records if rec["undetected"])
    engineering = stored_hi.get("engineering_reason", "") or \
        stored_lo.get("engineering_reason", "")
    if "1024:r65" not in recomputed_E or "128:r65" not in recomputed_E:
        violations.append("anchor cells missing for gate recompute")
    elif r23.route_scaling_gate(recomputed_E["1024:r65"],
                                recomputed_E["128:r65"],
                                recomputed_undetected,
                                engineering) != summary.get("terminal"):
        violations.append("terminal stored=%r recomputed mismatch"
                          % (summary.get("terminal"),))
    if any(c.get("engineering_reason")
           for c in summary.get("per_cell", {}).values()):
        violations.append("engineering-blocked root (fail-closed)")
    if len(decoder_rows) != int(summary.get("scientific_calls", -1)):
        violations.append("stored calls %d != summary %r"
                          % (len(decoder_rows),
                             summary.get("scientific_calls")))
    if len(decoder_rows) > r23.SCIENTIFIC_CALL_CEILING:
        violations.append("stored calls exceed scientific ceiling")
    if int(summary.get("setup_graphs", -1)) != r23.SETUP_CALL_CEILING:
        violations.append("setup graphs != frozen %d: %r"
                          % (r23.SETUP_CALL_CEILING,
                             summary.get("setup_graphs")))
    if _as_float(summary.get("wall_s", -1.0)) > r23.WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if _as_int(summary.get("peak_rss_bytes", -1)) \
            >= r23.RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")
    max_call_wall = max((rec["wall_s"] for rec in records), default=0.0)
    if max_call_wall > r23.PER_CALL_BUDGET_S:
        violations.append("per-call wall exceeds budget: %s" % max_call_wall)

    for row in graph_rows:
        seed = _as_int(row["graph_seed"])
        width = _as_int(row["width"])
        ratio = row["ratio"]
        if row["arm"] != r23.ARM or width not in r23.WIDTHS \
                or (width, ratio) not in r23.GRAPH_SEEDS \
                or seed not in r23.GRAPH_SEEDS[(width, ratio)]:
            violations.append("graph arm/width/ratio/seed outside R23 "
                              "cells: %r" % ((row["arm"], row["width"],
                                              ratio, row["graph_seed"]),))
            continue
        graph = build_fn(width, ratio, seed)
        key = (width, ratio, row["graph_seed"])
        if graph["status"] != row["status"] \
                or bool(graph["admitted"]) != _as_bool(row["admitted"]) \
                or int(graph["E"]) != _as_int(row["E"]) \
                or str(graph["failure_reason"]) != row["failure_reason"]:
            violations.append("graph %s status/admission/E mismatch" % (key,))
            continue
        if str(row["status"]) != "ok" or not _as_bool(row["admitted"]):
            violations.append("graph %s not admitted (fail-closed)" % (key,))
            continue
        structure = graph.get("structure")
        if structure and _cell(row.get("admission")):
            recomputed_admission = json.dumps(structure["admission"],
                                              sort_keys=True)
            if _cell(row.get("admission")) != recomputed_admission:
                violations.append("graph %s admission stored != recomputed"
                                  % (key,))
    if len(graph_rows) != 12:
        violations.append("graph rows %d != 12 built objects"
                          % len(graph_rows))
    build_violations = r23.check_build_budgets(graph_rows)
    violations.extend("build sub-cap: %s" % v for v in build_violations)

    print("VERIFY checked_calls=%d violations=%d"
          % (len(decoder_rows), len(violations)))
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    ok = not violations
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return ok


# --------------------------------------------------------------------------- #
# CLI (default-false batch refusal before write/bind/build)
# --------------------------------------------------------------------------- #
def build_parser():
    parser = argparse.ArgumentParser(
        description="R23 synthetic scale probe runner")
    parser.add_argument("--r23-batch", action="store_true",
                        help="run the frozen R23 matrix (requires "
                             "--execution-authorized from a separate "
                             "explicit authorization)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for "
                             "--r23-batch; default false "
                             "(fail-closed, no-write/no-bind)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--profile-only", action="store_true",
                        help="frozen plan + budget dry-run (no decoder, "
                             "no graph builds, no root)")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    return parser


def profile_only():
    """Dry-run profile: frozen plan + D9 geometry + budgets, nothing else."""
    plan = r23.build_call_plan()
    _validate_call_plan(plan)
    future = Path(r23.FUTURE_ROOT)
    resolved = future.resolve() if future.is_absolute() \
        else (ROOT / future).resolve()
    cells = []
    for width in r23.WIDTHS:
        for ratio in r23.RATIOS:
            key = r23.RATIO_KEY[ratio]
            cell = r23.degree_cell(width, key)
            cells.append({
                "width": width, "ratio": key, "n": cell["n"], "m": cell["m"],
                "E": cell["E"], "rate": cell["rate"],
                "disclosed_bits": cell["disclosed_bits"],
                "graphs": len(r23.GRAPH_SEEDS[(width, key)]),
                "blocks": len(r23.BLOCK_SEEDS[(width, key)]),
                "calls": (len(r23.GRAPH_SEEDS[(width, key)])
                          * len(r23.BLOCK_SEEDS[(width, key)]))})
    return {
        "cells": cells,
        "plan_calls": len(plan),
        "per_cell_calls": r23.CELL_TRIALS,
        "budgets": _budget_meta(),
        "future_root": str(resolved),
        "future_root_absent": not resolved.exists(),
        "decoder_calls": 0,
        "graph_builds": 0,
    }


def main(argv=None, *, adapters_override=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--r23-batch", args.r23_batch),
                                        ("--verify", args.verify),
                                        ("--profile-only",
                                         args.profile_only)) if flag]
    if len(selected) != 1:
        parser.error("exactly one of --r23-batch, --verify or "
                     "--profile-only is required")
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
        return 0
    # Refuse --r23-batch before root creation and before any decoder
    # binding or graph build while --execution-authorized is false.
    if args.r23_batch and not args.execution_authorized:
        print("refusing --r23-batch: %s (pass --execution-authorized only "
              "under a separate explicit authorization)"
              % r23.AUTHORIZATION, file=sys.stderr)
        return 2
    if args.out_root is None:
        parser.error("%s requires --out-root" % selected[0])
    if args.verify:
        return 0 if verify_root(args.out_root) else 1
    # Authorized true branch: exactly one batch-orchestrator call plus one
    # never-overwrite writer. adapters_override carries test-machinery
    # fakes only; None production-binds inside the orchestrator, after
    # plan validation.
    bundle = run_authorized_batch(
        args.out_root, adapters=adapters_override)
    summary = write_batch_root(bundle)
    print("R23 terminal=%s calls=%d setup=%d"
          % (summary["terminal"], summary["scientific_calls"],
             summary["setup_graphs"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
