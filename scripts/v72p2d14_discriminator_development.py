"""D14N calibrated L1/L2 discriminator runner — readiness paths.

Frozen command (design §6; requires a separate explicit authorization):

    .venv/bin/python scripts/v72p2d14_discriminator_development.py --n14-batch \\
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \\
      --out-root workspace/v72p2d14_discriminator/20260914_r1

Paths:

- ``--profile-only``: build the 18 frozen N graphs with the real
  builders, print structural metrics (components, structural/GF32 rank,
  four-cycles, girth, realized degree histograms, A1–A6 admission, wall
  time) plus the 288-identity plan summary and future-root absence, no
  decoder, no root;
- ``--n14-batch``: the frozen 288-call matrix (72 each L045, L055, L2-APP,
  L2-ORACLE; <=288 scientific calls, <=32 setup units); refuses unless
  ``--execution-authorized`` is passed (default false; refusal happens
  before any root creation, decoder binding or Model-F load) and requires
  the injected production decoder adapter plus transfer/oracle prior
  adapters, which only this runner constructs;
- ``--verify``: read-only recomputation of a completed six-file root with
  zero skip, zero decoder calls; exits FAIL on any partial or
  engineering-blocked root.

One fresh root per run; refuses overwrite and protected roots (single
process, no retry, no resume, no seed search, no adaptive stop).
Predecessor evidence is contextual only and can never enter the N gate:
decoder records carry ``batch_id == d14-discriminator-v1`` and the gate
constructor rejects anything else. The APP transfer source profile is NOT
frozen by this readiness change: ``--n14-batch`` takes no default and the
authorized runner change must freeze it explicitly.
"""
from __future__ import annotations

import argparse
import csv
import json
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))

from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d14n_calibrated_discriminator as n14)

EVIDENCE_FILES = n14.EVIDENCE_FILES
FROZEN_COMMAND = n14.FROZEN_COMMAND

DECODER_RECORD_COLUMNS = (
    "call_idx", "arm", "pair_idx", "l1_graph_seed", "l2_graph_seed",
    "block_seed", "batch_id", "exact", "syndrome_ok", "source_exact",
    "target_exact", "joint_exact", "undetected", "oracle", "graded",
    "belief_provenance", "iterations", "status",
    "residual_syndrome_weight",
    "wall_s", "crash", "error")
GRAPH_RECORD_COLUMNS = (
    "arm", "width", "graph_seed", "n", "m", "E", "status", "admitted",
    "failure_reason", "admission", "construction_wall_s")
ARM_SUMMARY_COLUMNS = (
    "arm", "scope", "pair_idx", "blocks", "exact_count",
    "syndrome_valid_count", "joint_exact_count", "undetected_count")


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
# arm summary rows (pooled + per-pair, graded arms and ungraded oracle kept
# distinct; undetected never merged into exact)
# --------------------------------------------------------------------------- #
def _arm_rows(records):
    rows = []
    for arm in n14.ARMS:
        pairs = sorted({int(rec["pair_idx"]) for rec in records
                        if rec["arm"] == arm})
        for pair_idx in pairs:
            scoped = [rec for rec in records
                      if rec["arm"] == arm
                      and int(rec["pair_idx"]) == pair_idx]
            rows.append({
                "arm": arm, "scope": "pair", "pair_idx": pair_idx,
                "blocks": len(scoped),
                "exact_count": sum(1 for rec in scoped if rec["exact"]),
                "syndrome_valid_count":
                    sum(1 for rec in scoped if rec["syndrome_ok"]),
                "joint_exact_count":
                    sum(1 for rec in scoped if rec["joint_exact"]),
                "undetected_count":
                    sum(1 for rec in scoped if rec["undetected"])})
        pooled = [rec for rec in records if rec["arm"] == arm]
        rows.append({
            "arm": arm, "scope": "pooled", "pair_idx": "POOLED",
            "blocks": len(pooled),
            "exact_count": sum(1 for rec in pooled if rec["exact"]),
            "syndrome_valid_count":
                sum(1 for rec in pooled if rec["syndrome_ok"]),
            "joint_exact_count":
                sum(1 for rec in pooled if rec["joint_exact"]),
            "undetected_count":
                sum(1 for rec in pooled if rec["undetected"])})
    return rows


def _degree_table_meta():
    return {profile: {
        "n": cell["n"], "m": cell["m"],
        "var_counts": cell["var_counts"],
        "check_counts": cell["check_counts"]}
        for profile, cell in sorted(n14.DEGREE_TABLE.items())}


def _budget_meta():
    return {
        "scientific_calls": n14.SCIENTIFIC_CALL_CEILING,
        "setup_calls": n14.SETUP_CALL_CEILING,
        "wall_s": n14.WALL_BUDGET_S,
        "per_call_s": n14.PER_CALL_BUDGET_S,
        "rss_bytes": n14.RSS_BUDGET_BYTES,
        "processes": 1,
        "retry": False, "resume": False,
        "seed_search": False, "adaptive_stop": False,
    }


def _graph_row(graph, wall_s):
    structure = graph.get("structure") or {}
    return {
        "arm": graph["arm"], "width": graph["width"],
        "graph_seed": graph["graph_seed"], "n": graph["n"],
        "m": graph["m"], "E": graph["E"], "status": graph["status"],
        "admitted": bool(graph["admitted"]),
        "failure_reason": graph["failure_reason"],
        "admission": json.dumps((structure.get("admission") or {}),
                                sort_keys=True),
        "construction_wall_s": round(float(wall_s), 6),
    }


# --------------------------------------------------------------------------- #
# batch (frozen 288-call matrix; injected production adapters only)
# --------------------------------------------------------------------------- #
def run_n14_batch(out_root, model_f_root, decode_fn, syndrome_fn, *,
                  build_l1_fn=None, build_l2_fn=None, load_prior_fn=None,
                  sample_fn=None, transfer_fn=None, oracle_prior_fn=None,
                  app_sources=None, app_source_profile=None,
                  now_fn=None, rss_fn=None):
    """Execute and persist one authorized N batch (injected adapters).

    ``decode_fn``/``syndrome_fn``/``transfer_fn``/``oracle_prior_fn``/
    ``load_prior_fn``/``sample_fn`` are explicit injections supplied by
    the caller (the ``--n14-batch`` entrypoint constructs the production
    adapters). ``app_sources`` maps ``(pair_idx, block_seed)`` to
    ``{"belief", "provenance", "source_exact"}`` for the shared APP
    stream and ``app_source_profile`` names the sourcing L1 profile for
    the manifest; neither has a default — the authorized runner change
    must freeze the APP source explicitly.
    """
    resolved = n14.refuse_out_root(out_root)
    plan = n14.build_call_plan()
    build_l1_fn = build_l1_fn or n14.build_l1_graph
    build_l2_fn = build_l2_fn or n14.build_l2_graph
    if load_prior_fn is None or sample_fn is None:
        raise ValueError("load_prior_fn and sample_fn must be explicitly "
                         "injected (Model-F content is never loaded without "
                         "them)")
    if app_sources is None or app_source_profile not in n14.L1_PROFILES:
        raise ValueError("app_sources and a frozen app_source_profile "
                         "(an N L1 profile) must be explicitly injected")
    now = now_fn or time.monotonic
    rss_fn = rss_fn or _peak_rss_bytes
    t0 = float(now())
    log_lines = []

    def log(message):
        line = _log_line(message)
        log_lines.append(line)
        print(line)

    p_b, p_f, p1 = load_prior_fn(model_f_root)
    setup_calls = n14.SETUP_FIXED_UNITS
    log("prior chain loaded from %s" % model_f_root)
    blocks = {}
    for block_seed in n14.BLOCK_SEEDS:
        blocks[int(block_seed)] = sample_fn(p_b, p_f, p1, block_seed)
    setup_calls += len(n14.BLOCK_SEEDS)
    log("sampled matched blocks count=%d" % len(n14.BLOCK_SEEDS))
    graphs_l1, graphs_l2, graph_rows = {}, {}, []
    for profile in n14.L1_PROFILES:
        for graph_seed in n14.L1_GRAPH_SEEDS:
            start = float(now())
            graph = build_l1_fn(profile, int(graph_seed))
            graph_rows.append(_graph_row(graph, float(now()) - start))
            graphs_l1[(profile, int(graph_seed))] = graph
            setup_calls += 1
    for graph_seed in n14.L2_GRAPH_SEEDS:
        start = float(now())
        graph = build_l2_fn(int(graph_seed))
        graph_rows.append(_graph_row(graph, float(now()) - start))
        graphs_l2[int(graph_seed)] = graph
        setup_calls += 1
    admitted = sum(1 for row in graph_rows if row["admitted"])
    log("built %d graphs admitted=%d" % (len(graph_rows), admitted))
    if setup_calls != n14.SETUP_CALL_CEILING:
        raise RuntimeError("setup unit count %d != frozen %d"
                           % (setup_calls, n14.SETUP_CALL_CEILING))

    outcome = n14.execute_plan(
        plan, graphs_l1, graphs_l2, blocks, decode_fn, syndrome_fn,
        transfer_fn=transfer_fn, oracle_prior_fn=oracle_prior_fn,
        app_sources=app_sources, now=now, rss_fn=rss_fn)
    records = outcome["records"]
    engineering_reason = outcome["engineering_reason"]
    log("dispatched=%d reason=%s"
        % (len(records), engineering_reason or "none"))

    try:
        tallies = n14.tallies_from_n14_records(records)
    except ValueError:
        tallies = n14.N14Tallies((0,) * 6, (0,) * 6, (0,) * 6, 0)
    l045_by_cell = {(int(rec["pair_idx"]), int(rec["block_seed"])):
                    bool(rec["exact"]) for rec in records
                    if rec["arm"] == "L045"}
    l055_by_cell = {(int(rec["pair_idx"]), int(rec["block_seed"])):
                    bool(rec["exact"]) for rec in records
                    if rec["arm"] == "L055"}
    try:
        paired = n14.describe_paired_l1(l045_by_cell, l055_by_cell)
    except ValueError:
        paired = {"challenger_only": 0, "reference_only": 0,
                  "concordant": 0, "trials": 0, "cells": 72,
                  "descriptive_only": True}
    terminal = n14.route_terminal(tallies, engineering_reason)
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn())
    budget_violations = []
    if len(records) > n14.SCIENTIFIC_CALL_CEILING:
        budget_violations.append("scientific calls exceed ceiling")
    if wall_s > n14.WALL_BUDGET_S:
        budget_violations.append("wall budget exceeded")
    if peak_rss >= n14.RSS_BUDGET_BYTES:
        budget_violations.append("RSS budget exceeded")
    log("terminal=%s" % terminal)

    resolved.mkdir(parents=True)
    _write_json(resolved / "manifest.json", {
        "schema": "v72p2d14n_calibrated_discriminator_manifest_v1",
        "change_id": n14.CHANGE_ID, "cycle": n14.CYCLE_ID,
        "claim_ceiling": n14.CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "model_f_root": str(model_f_root), "out_root": str(resolved),
        "batch_id": n14.N14_BATCH_ID,
        "field": {"q": n14.Q, "poly": n14.POLY,
                  "factory": "GF2mField.create(32)"},
        "arms": list(n14.ARMS),
        "l1_profiles": list(n14.L1_PROFILES),
        "lambda2": dict(n14.LAMBDA2),
        "width": n14.N, "m_l1": n14.M_L1, "m_l2": n14.M_L2,
        "degree_table": _degree_table_meta(),
        "l1_graph_seeds": list(n14.L1_GRAPH_SEEDS),
        "l2_graph_seeds": list(n14.L2_GRAPH_SEEDS),
        "block_seeds": list(n14.BLOCK_SEEDS),
        "coefficient_rule":
            "v10_seed(d10:coeff:{width}:{graph_seed}) -> default_rng -> "
            "integers(1,32) per edge in sorted (variable, check) order",
        "prior_chain": n14.PRIOR_CHAIN,
        "app_source_profile": app_source_profile,
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": n14.DECODER_MAX_ITER,
                    "damping_alpha": n14.DAMPING_ALPHA,
                    "warm_beliefs": None, "schedule": "cold row-layered"},
        "matrix": {"planned_calls": len(plan),
                   "shape": "4 arms x 6 pairs x 12 blocks",
                   "call_order": ("L045 then L055 then L2-APP then "
                                  "L2-ORACLE; pairs ascending; blocks "
                                  "ascending"),
                   "progress_rule": "none (no conditional progression)"},
        "budgets": _budget_meta(),
        "setup_calls": setup_calls,
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": n14.AUTHORIZATION,
        "predecessor_boundary": ("predecessor evidence is contextual only; "
                                 "the N gate accepts only batch_id=%s "
                                 "records" % n14.N14_BATCH_ID),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    _write_csv(resolved / "decoder_records.csv",
               DECODER_RECORD_COLUMNS, records)
    _write_csv(resolved / "graph_records.csv", GRAPH_RECORD_COLUMNS,
               graph_rows)
    _write_csv(resolved / "arm_summary.csv", ARM_SUMMARY_COLUMNS,
               _arm_rows(records))
    summary = {
        "schema": "v72p2d14n_calibrated_discriminator_summary_v1",
        "change_id": n14.CHANGE_ID, "cycle": n14.CYCLE_ID,
        "claim_ceiling": n14.CLAIM_CEILING,
        "terminal": terminal,
        "pools": {"L045": tallies.pool("L045"),
                  "L055": tallies.pool("L055"),
                  "L2_APP_joint": tallies.pool(n14.L2_ARM),
                  "L2_ORACLE": tallies.pool(n14.ORACLE_ARM)},
        "per_pair": {"L045": list(tallies.l045_exact),
                     "L055": list(tallies.l055_exact),
                     "L2_APP_joint": list(tallies.app_joint),
                     "L2_ORACLE_pool": tallies.oracle_pool},
        "paired_l1_discordance": paired,
        "engineering_reason": engineering_reason,
        "scientific_calls": len(records),
        "planned_calls": len(plan),
        "setup_calls": setup_calls,
        "exact_count": sum(1 for rec in records if rec["exact"]),
        "syndrome_valid_count": sum(1 for rec in records
                                    if rec["syndrome_ok"]),
        "undetected_count": sum(1 for rec in records
                                if rec["undetected"]),
        "call_idx_first": 0 if records else None,
        "call_idx_last": len(records) - 1 if records else None,
        "wall_s": wall_s, "peak_rss_bytes": peak_rss,
        "budget_violations": budget_violations,
        "batch_id": n14.N14_BATCH_ID,
        "app_source_profile": app_source_profile,
        "model_f_root": str(model_f_root),
        "out_root": str(resolved), "budgets": _budget_meta(),
    }
    _write_json(resolved / "summary.json", summary)
    log_lines.append(_log_line(
        "N terminal=%s calls=%d setup=%d wall_s=%.3f"
        % (terminal, len(records), setup_calls, wall_s)))
    with open(resolved / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("".join(line + "\n" for line in log_lines))
    return summary


# --------------------------------------------------------------------------- #
# verify (read-only; zero decoder calls; zero skip; fail-closed)
# --------------------------------------------------------------------------- #
def verify_root(out_root, build_l1_fn=None, build_l2_fn=None):
    """Recompute a completed N root from its evidence; fail-closed."""
    root = Path(out_root)
    build_l1_fn = build_l1_fn or n14.build_l1_graph
    build_l2_fn = build_l2_fn or n14.build_l2_graph
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
    arm_rows = _read_csv(root / "arm_summary.csv")

    if manifest.get("batch_id") != n14.N14_BATCH_ID \
            or summary.get("batch_id") != n14.N14_BATCH_ID:
        violations.append("batch_id tag mismatch (predecessor boundary)")
    if manifest.get("command") != FROZEN_COMMAND:
        violations.append("manifest command != frozen command")
    if manifest.get("app_source_profile") not in n14.L1_PROFILES \
            or summary.get("app_source_profile") not in n14.L1_PROFILES:
        violations.append("app_source_profile missing or outside N L1 arms")
    if manifest.get("app_source_profile") != summary.get(
            "app_source_profile"):
        violations.append("app_source_profile manifest/summary mismatch")

    plan = n14.build_call_plan()
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
        for key in ("arm", "pair_idx", "l1_graph_seed", "l2_graph_seed",
                    "block_seed"):
            if str(row[key]) != str(entry[key]):
                violations.append("decoder row %d %s %r != planned %r"
                                  % (index, key, row[key], entry[key]))
        if row.get("batch_id") != n14.N14_BATCH_ID:
            violations.append("decoder row %d batch_id tag missing" % index)
        exact = _as_bool(row["exact"])
        syndrome_ok = _as_bool(row["syndrome_ok"])
        source_exact = _as_bool(row["source_exact"])
        target_exact = _as_bool(row["target_exact"])
        joint_exact = _as_bool(row["joint_exact"])
        undetected = _as_bool(row["undetected"])
        oracle = _as_bool(row["oracle"])
        graded = _as_bool(row["graded"])
        iterations = _as_int(row["iterations"])
        residual = _as_int(row["residual_syndrome_weight"])
        wall = _as_float(row["wall_s"])
        crash = _as_bool(row["crash"])
        # Metric isolation: exact never without syndrome_ok; undetected
        # never merged into exact; APP exact == joint == source&target.
        if exact and not syndrome_ok:
            problems.append("exact without syndrome_ok (metric isolation)")
        if undetected and exact:
            problems.append("undetected merged into exact")
        if row["arm"] == n14.L2_ARM:
            if joint_exact != (source_exact and target_exact):
                problems.append("APP joint != source&target")
            if exact != joint_exact:
                problems.append("APP exact != joint")
        if row["arm"] == n14.ORACLE_ARM:
            if not oracle or graded:
                problems.append("ORACLE row must be oracle/ungraded")
            if str(row["belief_provenance"]).strip() != "ORACLE":
                problems.append("ORACLE provenance must be ORACLE")
        else:
            if oracle:
                problems.append("non-ORACLE arm marked oracle")
            if not graded:
                problems.append("non-ORACLE arm must be graded")
            if not str(row["belief_provenance"]).strip():
                problems.append("provenance missing")
            elif row["arm"] == n14.L2_ARM and str(
                    row["belief_provenance"]).strip() != \
                    n14.check_updated_token():
                problems.append("APP provenance must be CHECK_UPDATED")
        if crash:
            if iterations != -1 or residual != -1 or exact or syndrome_ok \
                    or joint_exact or target_exact:
                problems.append("crash record inconsistent")
        else:
            if not 0 <= iterations <= n14.DECODER_MAX_ITER:
                problems.append("iterations out of range: %d" % iterations)
            if residual < 0:
                problems.append("residual weight missing")
        if str(row["status"]).strip() in ("",):
            problems.append("empty status")
        if str(row["status"]).strip() == "provenance_refused":
            problems.append("provenance refusal retained (fail-closed)")
        if wall < 0.0 or wall > n14.PER_CALL_BUDGET_S:
            problems.append("per-call wall out of budget: %s"
                            % row["wall_s"])
        for problem in problems:
            violations.append("decoder row %d %s" % (index, problem))
        records.append({"call_idx": index, "arm": row["arm"],
                        "pair_idx": _as_int(row["pair_idx"]),
                        "l1_graph_seed": _as_int(row["l1_graph_seed"]),
                        "l2_graph_seed": _as_int(row["l2_graph_seed"]),
                        "block_seed": _as_int(row["block_seed"]),
                        "batch_id": row.get("batch_id"),
                        "exact": exact, "syndrome_ok": syndrome_ok,
                        "source_exact": source_exact,
                        "target_exact": target_exact,
                        "joint_exact": joint_exact,
                        "undetected": undetected, "oracle": oracle,
                        "graded": graded, "crash": crash, "wall_s": wall})
    if len(decoder_rows) != len(plan):
        violations.append("stored calls %d != frozen plan %d (zero-skip)"
                          % (len(decoder_rows), len(plan)))

    # Shared paired identities: every (pair, block) cell feeds all arms.
    for pair_idx in range(1, 7):
        for block_seed in n14.BLOCK_SEEDS:
            arms = sorted(rec["arm"] for rec in records
                          if rec["pair_idx"] == pair_idx
                          and rec["block_seed"] == int(block_seed))
            if arms != sorted(n14.ARMS):
                violations.append("cell pair=%d block=%d arms %s != all "
                                  "four (sharing)" % (pair_idx, block_seed,
                                                      arms))

    recomputed_arm_rows = _arm_rows(records)
    stored_arm_keys = {(row["arm"], row["scope"], row["pair_idx"]): row
                       for row in arm_rows}
    for row in recomputed_arm_rows:
        key = (row["arm"], row["scope"], str(row["pair_idx"]))
        stored = stored_arm_keys.get(key)
        if stored is None:
            violations.append("arm_summary row missing: %s" % (key,))
            continue
        for column in ("blocks", "exact_count", "syndrome_valid_count",
                       "joint_exact_count", "undetected_count"):
            if _as_int(stored[column]) != int(row[column]):
                violations.append("arm_summary %s %s stored=%s recomputed=%d"
                                  % (key, column, stored[column],
                                     int(row[column])))

    try:
        tallies = n14.tallies_from_n14_records(records)
        gate_ok = True
    except ValueError as exc:
        violations.append("tallies not rebuildable: %s" % exc)
        gate_ok = False
    if gate_ok:
        if tallies.pool("L045") != summary.get("pools", {}).get("L045"):
            violations.append("stored L045 pool != recomputed")
        if tallies.pool("L055") != summary.get("pools", {}).get("L055"):
            violations.append("stored L055 pool != recomputed")
        if tallies.pool(n14.L2_ARM) != summary.get("pools", {}).get(
                "L2_APP_joint"):
            violations.append("stored APP joint pool != recomputed")
        if tallies.pool(n14.ORACLE_ARM) != summary.get("pools", {}).get(
                "L2_ORACLE"):
            violations.append("stored ORACLE pool != recomputed")
        if list(tallies.l055_exact) != summary.get("per_pair", {}).get(
                "L055"):
            violations.append("stored L055 per-pair != recomputed")
        if n14.route_terminal(
                tallies, summary.get("engineering_reason", "")) != \
                summary.get("terminal"):
            violations.append("terminal stored=%r recomputed mismatch"
                              % (summary.get("terminal"),))
        l045_cells = {(r["pair_idx"], r["block_seed"]): r["exact"]
                      for r in records if r["arm"] == "L045"}
        l055_cells = {(r["pair_idx"], r["block_seed"]): r["exact"]
                      for r in records if r["arm"] == "L055"}
        recomputed_paired = n14.describe_paired_l1(l045_cells, l055_cells)
        for field in ("challenger_only", "reference_only", "concordant",
                      "trials"):
            if summary.get("paired_l1_discordance", {}).get(field) != \
                    recomputed_paired[field]:
                violations.append("paired discordance %s stored != "
                                  "recomputed" % field)
    if summary.get("engineering_reason"):
        violations.append("engineering-blocked root (fail-closed)")
    if len(decoder_rows) != int(summary.get("scientific_calls", -1)):
        violations.append("stored calls %d != summary %r"
                          % (len(decoder_rows),
                             summary.get("scientific_calls")))
    if len(decoder_rows) > n14.SCIENTIFIC_CALL_CEILING:
        violations.append("stored calls exceed scientific ceiling")
    if int(summary.get("setup_calls", -1)) != n14.SETUP_CALL_CEILING:
        violations.append("setup calls != frozen %d: %r"
                          % (n14.SETUP_CALL_CEILING,
                             summary.get("setup_calls")))
    if _as_float(summary.get("wall_s", -1.0)) > n14.WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if _as_int(summary.get("peak_rss_bytes", -1)) \
            >= n14.RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")
    max_call_wall = max((rec["wall_s"] for rec in records), default=0.0)
    if max_call_wall > n14.PER_CALL_BUDGET_S:
        violations.append("per-call wall exceeds budget: %s" % max_call_wall)

    for row in graph_rows:
        seed = _as_int(row["graph_seed"])
        if row["arm"] in n14.L1_PROFILES:
            graph = build_l1_fn(row["arm"], seed)
        elif row["arm"] == "L2":
            graph = build_l2_fn(seed)
        else:
            violations.append("graph arm outside N families: %r"
                              % (row["arm"],))
            continue
        key = (row["arm"], row["graph_seed"])
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
    if len(graph_rows) != 18:
        violations.append("graph rows %d != 18 built objects"
                          % len(graph_rows))

    print("VERIFY checked_calls=%d violations=%d"
          % (len(decoder_rows), len(violations)))
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    ok = not violations
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return ok


# --------------------------------------------------------------------------- #
# CLI (default-false batch refusal before write/bind/load)
# --------------------------------------------------------------------------- #
def build_parser():
    parser = argparse.ArgumentParser(
        description="D14N calibrated L1/L2 discriminator runner")
    parser.add_argument("--n14-batch", action="store_true",
                        help="run the frozen 288-call N matrix (requires "
                             "--execution-authorized from a separate "
                             "explicit authorization)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for "
                             "--n14-batch; default false "
                             "(fail-closed, no-write/no-bind)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--profile-only", action="store_true",
                        help="pre-decoder graph construction profile (no "
                             "decoder, no root)")
    parser.add_argument("--model-f-root", default=n14.MODEL_F_INPUT_ROOT,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    return parser


def profile_only():
    """Pre-decoder profile: real builders + full plan, no decoder, no root."""
    profile = n14.profile_graphs()
    plan = n14.build_call_plan()
    future = Path(n14.FUTURE_ROOT)
    resolved = future.resolve() if future.is_absolute() \
        else (ROOT / future).resolve()
    degree_counts = {}
    for entry in profile["graphs"]:
        degree_counts["%s:%d" % (entry["arm"], entry["seed"])] = {
            "n": entry["n"], "m": entry["m"], "E": entry["E"],
            "variable_degree_histogram":
                entry.get("variable_degree_histogram"),
            "check_degree_histogram":
                entry.get("check_degree_histogram"),
            "admitted": entry["admitted"]}
    return {
        "graphs": profile["graphs"],
        "admitted": sum(1 for g in profile["graphs"] if g["admitted"]),
        "total_graphs": len(profile["graphs"]),
        "seed_replacements": profile["seed_replacements"],
        "replacement_seeds_used": profile["replacement_seeds_used"],
        "frozen_seed_failures": profile["frozen_seed_failures"],
        "degree_counts": degree_counts,
        "plan_calls": len(plan),
        "plan_per_arm": {arm: sum(1 for e in plan if e["arm"] == arm)
                         for arm in n14.ARMS},
        "future_root": str(resolved),
        "future_root_absent": not resolved.exists(),
        "decoder_calls": 0,
        "wall_s": profile["wall_s"],
    }


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--n14-batch", args.n14_batch),
                                        ("--verify", args.verify),
                                        ("--profile-only",
                                         args.profile_only)) if flag]
    if len(selected) != 1:
        parser.error("exactly one of --n14-batch, --verify or "
                     "--profile-only is required")
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
        return 0
    # Refuse --n14-batch before root creation and before any decoder
    # binding or Model-F load while --execution-authorized is false.
    if args.n14_batch and not args.execution_authorized:
        print("refusing --n14-batch: %s (pass --execution-authorized only "
              "under a separate explicit authorization)"
              % n14.AUTHORIZATION, file=sys.stderr)
        return 2
    if args.out_root is None:
        parser.error("%s requires --out-root" % selected[0])
    if args.verify:
        return 0 if verify_root(args.out_root) else 1
    raise SystemExit(
        "production --n14-batch adapters (decoder/transfer/oracle/prior) "
        "belong to a later authorized change; this readiness change "
        "supplies only --profile-only and --verify")


if __name__ == "__main__":
    sys.exit(main())
