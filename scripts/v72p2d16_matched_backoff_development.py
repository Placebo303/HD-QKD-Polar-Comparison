"""D16 one-point matched-backoff discriminator runner — readiness paths.

Frozen command (design §6; requires a separate explicit authorization):

    .venv/bin/python scripts/v72p2d16_matched_backoff_development.py --d16-batch \\
      --execution-authorized \\
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \\
      --out-root workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a

Paths:

- ``--profile-only``: build the 12 frozen D16 graphs with the real
  builders, print structural metrics (components, structural/GF32 rank,
  four-cycles, girth, realized degree histograms, A1–A6 admission, wall
  time) plus the 96-identity plan summary and future-root absence, no
  decoder, no root;
- ``--d16-batch``: the frozen 96-call matrix (3 cells x 4 graphs x 8
  blocks; <=96 scientific calls, <=22 setup units); refuses unless
  ``--execution-authorized`` is passed (default false; refusal happens
  before any root creation, decoder binding or Model-F load) and requires
  the injected production decoder adapter plus the oracle prior adapter,
  which only this runner constructs (single-layer diagnostic: L1 dispatch
  plus the accepted true-conditioned L2 oracle path; no cross-layer arm);
- ``--verify``: read-only recomputation of a completed six-file root with
  zero skip, zero decoder calls; exits FAIL on any partial or
  engineering-blocked root.

One fresh root per run; refuses overwrite and protected roots (single
process, no retry, no resume, no seed search, no adaptive stop).
Predecessor evidence is contextual only and can never enter the D16 gate:
decoder records carry ``batch_id == d16-matched-backoff-v1`` and the gate
constructor rejects anything else.
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
    v72p2d16_matched_backoff as d16)

EVIDENCE_FILES = d16.EVIDENCE_FILES
FROZEN_COMMAND = d16.FROZEN_COMMAND

DECODER_RECORD_COLUMNS = (
    "call_idx", "point_idx", "layer", "arm", "rows", "disclosed_bits",
    "effective_factor", "graph_seed", "block_seed", "batch_id", "exact",
    "syndrome_ok", "undetected", "oracle", "graded", "belief_provenance",
    "iterations", "status", "residual_syndrome_weight",
    "wall_s", "crash", "error")
GRAPH_RECORD_COLUMNS = (
    "arm", "layer", "rows", "graph_seed", "n", "m", "E", "status",
    "admitted", "failure_reason", "admission", "construction_wall_s")
ARM_SUMMARY_COLUMNS = (
    "arm", "rows", "scope", "graph_ordinal", "blocks", "exact_count",
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
# arm summary rows (pooled + per-graph, graded L1 and ungraded oracle kept
# distinct; undetected never merged into exact)
# --------------------------------------------------------------------------- #
def _arm_rows(records):
    rows = []
    for profile, m in d16.CELLS:
        arm = profile if profile in d16.L1_PROFILES else d16.ORACLE_ARM
        scoped = [rec for rec in records
                  if rec["arm"] == arm and int(rec["rows"]) == int(m)]
        seeds = d16.GRAPH_SEEDS[(profile, int(m))]
        for ordinal, seed in enumerate(seeds):
            cell = [rec for rec in scoped
                    if int(rec["graph_seed"]) == int(seed)]
            rows.append({
                "arm": arm, "rows": m, "scope": "graph",
                "graph_ordinal": ordinal, "blocks": len(cell),
                "exact_count": sum(1 for rec in cell if rec["exact"]),
                "syndrome_valid_count":
                    sum(1 for rec in cell if rec["syndrome_ok"]),
                "undetected_count":
                    sum(1 for rec in cell if rec["undetected"])})
        rows.append({
            "arm": arm, "rows": m, "scope": "pooled",
            "graph_ordinal": "POOLED", "blocks": len(scoped),
            "exact_count": sum(1 for rec in scoped if rec["exact"]),
            "syndrome_valid_count":
                sum(1 for rec in scoped if rec["syndrome_ok"]),
            "undetected_count":
                sum(1 for rec in scoped if rec["undetected"])})
    return rows


def _cell_table_meta():
    return [{"profile": profile, "arm": profile
             if profile in d16.L1_PROFILES else d16.ORACLE_ARM,
             "layer": "L1" if profile in d16.L1_PROFILES else "L2",
             "n": d16.N, "m": int(m),
             "var_counts": dict(d16.VAR_PROFILES[profile]),
             "check_counts": dict(d16.CHECK_TABLE[(profile, int(m))]),
             "disclosed_bits": d16.disclosed_bits(m),
             "effective_factor": d16.effective_factor(
                 "L1" if profile in d16.L1_PROFILES else "L2", m)}
            for profile, m in d16.CELLS]


def _budget_meta():
    return {
        "scientific_calls": d16.SCIENTIFIC_CALL_CEILING,
        "setup_calls": d16.SETUP_CALL_CEILING,
        "wall_s": d16.WALL_BUDGET_S,
        "per_call_s": d16.PER_CALL_BUDGET_S,
        "rss_bytes": d16.RSS_BUDGET_BYTES,
        "processes": 1,
        "retry": False, "resume": False,
        "seed_search": False, "adaptive_stop": False,
    }


def _graph_row(graph, wall_s):
    structure = graph.get("structure") or {}
    return {
        "arm": graph["arm"],
        "layer": "L1" if graph["arm"] in d16.L1_PROFILES else "L2",
        "rows": graph["m"], "graph_seed": graph["graph_seed"],
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
_R2_RUNNER_PATH = ROOT / "scripts" / "v72p2d10_mixed_degree_l1_development.py"


def _load_r2_runner():
    # Reuse: the accepted CAL-only Model-F prior chain lives in the R2
    # runner; import it read-only by file path instead of copying (R2
    # files untouched; same pattern as the D11/D14/D15 runners). Lazy so
    # the fake/test path never enters this module.
    import importlib.util

    key = "v72p2d10_r2_runner_reuse_d16"
    loaded = sys.modules.get(key)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(key, str(_R2_RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def _require_signature(fn, required, name):
    """Inspect-only contract check: ``fn`` callable with ``required`` params.

    No call, no decode, no Model-F load — pure ``inspect.signature``.
    Raises before any root creation or decoder contact on mismatch.
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
    """Narrow binder: accepted helpers only, validated, zero calls.

    Returns the flat adapter dict consumed by :func:`run_authorized_batch`
    (``decode_fn``/``syndrome_fn``/``load_prior_fn``/``sample_fn`` plus the
    ``oracle_parts`` composition kit). Every entry reuses an accepted
    D11/D12/D14/D15/R2/D5 helper — no kernel copies, no alternate
    algorithms. Signatures are validated here, before any root creation,
    Model-F load, or decoder call. Resolving never invokes: decoder calls
    and Model-F content load happen only inside the authorized
    orchestrator after plan validation.
    """
    from comparison_bench.formal_ir import (  # lazy production bind
        v35_algorithm_development as v35)
    from comparison_bench.formal_ir import (  # accepted canonical helpers
        v72p2d5_gf32_rate_mother as d5)

    decode_fn = _require_signature(
        v35.decode_row_layered_fftqspa,
        ["h_matrix", "priors", "syndromes", "max_iter", "damping_alpha",
         "warm_beliefs", "field"], "decode_fn")
    syndrome_fn = _require_signature(
        v35.syndrome_of_gf32, ["matrix", "vector"], "syndrome_fn")
    conditionalize_fn = _require_signature(
        d5.conditionalize_f_to_p2, ["p_f"], "conditionalize_fn")
    oracle_mixer_fn = _require_signature(
        d5.oracle_l2_prior, ["p2", "bob_symbols", "u1_true"],
        "oracle_mixer_fn")

    load_prior_fn = _require_signature(
        _load_r2_runner().load_prior_chain, ["model_f_root"],
        "load_prior_fn")

    def sample_fn(p_b, p_f, p1, seed):
        # One matched block plus the frozen L1 prior line, mirroring the
        # accepted R2/D11/D14/D15 runner composition (sample_matched_block,
        # then _floor_renorm(p1[:, bob].T, DECODER_FLOOR)); carries u2 for
        # the ORACLE target leg, which R2's block helper lacks.
        import numpy as np

        block = d5.sample_matched_block(p_b, p_f, int(d16.N), int(seed))
        bob = np.asarray(block["bob"], dtype=np.int64)
        prior = d5._floor_renorm(
            np.asarray(p1)[:, bob].T, d5.DECODER_FLOOR)
        return {
            "bob": bob,
            "u1": np.asarray(block["u1"], dtype=np.int64),
            "u2": np.asarray(block["u2"], dtype=np.int64),
            "prior": np.asarray(prior, dtype=np.float64),
        }

    _require_signature(sample_fn, ["p_b", "p_f", "p1", "seed"], "sample_fn")
    return {
        "decode_fn": decode_fn,
        "syndrome_fn": syndrome_fn,
        "load_prior_fn": load_prior_fn,
        "sample_fn": sample_fn,
        "oracle_parts": {
            "conditionalize_fn": conditionalize_fn,
            "oracle_mixer_fn": oracle_mixer_fn,
        },
    }


# --------------------------------------------------------------------------- #
# Plan validation + oracle composition
# --------------------------------------------------------------------------- #
def _validate_call_plan(plan):
    """Contract-check the complete 96 plan BEFORE binding/loading/decoding.

    Frozen order (L045, L055, L2-ORACLE; graphs ascending; blocks
    ascending; ``call_idx`` 0..95) with frozen cells, seeds and block
    pairing. Any deviation raises before any adapter is bound, Model-F
    content loads, or the root is touched.
    """
    if len(plan) != d16.SCIENTIFIC_CALL_CEILING:
        raise ValueError("plan has %d calls, frozen %d"
                         % (len(plan), d16.SCIENTIFIC_CALL_CEILING))
    pos = 0
    for profile, rows in (("L045", 125), ("L055", 125), ("L2", 94)):
        arm = profile if profile in d16.L1_PROFILES else d16.ORACLE_ARM
        layer = "L1" if profile in d16.L1_PROFILES else "L2"
        cell_calls = 0
        for graph_seed in d16.GRAPH_SEEDS[(profile, int(rows))]:
            for block_seed in d16.BLOCK_SEEDS:
                entry = plan[pos]
                pos += 1
                cell_calls += 1
                if entry.get("call_idx") != pos - 1 \
                        or int(entry.get("point_idx", -1)) != 1 \
                        or entry.get("layer") != layer \
                        or entry.get("arm") != arm \
                        or int(entry.get("rows", -1)) != int(rows) \
                        or int(entry.get("graph_seed", -1)) \
                        != int(graph_seed) \
                        or int(entry.get("block_seed", -1)) \
                        != int(block_seed) \
                        or int(entry.get("disclosed_bits", -1)) \
                        != d16.disclosed_bits(rows):
                    raise ValueError(
                        "plan identity/order violated at position %d: %r"
                        % (pos - 1, entry))
        if cell_calls != 32:
            raise ValueError("plan cell %r carries %d calls, frozen 32"
                             % ((arm, rows), cell_calls))
    if pos != len(plan):
        raise ValueError("plan order check covered %d/%d entries"
                         % (pos, len(plan)))
    return plan


def _compose_oracle(oracle_parts, p_f):
    """Compose the production oracle closure over the loaded p2.

    Wiring only: condition the Model-F joint to the L2 marginal, then the
    accepted true-L1 conditional prior per block (diagnostic-only). No
    decoder contact, no root, pure closure.
    """
    import numpy as np

    p2 = oracle_parts["conditionalize_fn"](p_f)

    def oracle_prior_fn(block):
        return oracle_parts["oracle_mixer_fn"](
            p2, np.asarray(block["bob"], dtype=np.int64),
            np.asarray(block["u1"], dtype=np.int64))

    return oracle_prior_fn


# --------------------------------------------------------------------------- #
# Batch orchestrator (plan-first; single phase; no filesystem writes)
# --------------------------------------------------------------------------- #
def run_authorized_batch(out_root, model_f_root, *, adapters=None,
                         build_l1_fn=None, build_l2_fn=None,
                         now_fn=None, rss_fn=None):
    """Execute the frozen D16 batch and return the evidence bundle (no writes).

    ``adapters`` is a flat dict with ``decode_fn``/``syndrome_fn``/
    ``load_prior_fn``/``sample_fn`` plus either the production
    ``oracle_parts`` composition kit (binder-supplied) or a direct
    ``oracle_prior_fn``; ``None`` production-binds inside, AFTER plan
    validation and the refuse probe. ``build_l1_fn``/``build_l2_fn`` may
    arrive explicitly or inside ``adapters`` (fake builders travel with the
    fake adapter dict on the test path); both default to the frozen real
    builders. Returns the bundle consumed by :func:`write_batch_root`;
    creates no files and no directories.
    """
    plan = d16.build_call_plan()
    _validate_call_plan(plan)
    resolved = d16.refuse_out_root(out_root)  # probe only; creates nothing
    if adapters is None:
        inj = bind_production_adapters()
    else:
        inj = dict(adapters)
    missing = [key for key in ("decode_fn", "syndrome_fn", "load_prior_fn",
                               "sample_fn") if inj.get(key) is None]
    if missing:
        raise ValueError("adapters %s must be explicitly injected "
                         "(Model-F content is never loaded and no decoder "
                         "is bound without them)" % (missing,))
    decode_fn = inj["decode_fn"]
    syndrome_fn = inj["syndrome_fn"]
    load_prior_fn = inj["load_prior_fn"]
    sample_fn = inj["sample_fn"]
    oracle_prior_fn = inj.get("oracle_prior_fn")
    oracle_parts = inj.get("oracle_parts")
    if oracle_parts is not None and oracle_prior_fn is not None:
        raise ValueError("oracle_parts and direct oracle_prior_fn are "
                         "mutually exclusive")
    if oracle_parts is None and oracle_prior_fn is None:
        raise ValueError("oracle_prior_fn must be explicitly injected "
                         "for L2 ORACLE (no frozen default)")
    build_l1_fn = build_l1_fn or inj.pop("build_l1_fn", None) \
        or d16.build_l1_graph
    build_l2_fn = build_l2_fn or inj.pop("build_l2_fn", None) \
        or d16.build_l2_graph
    now = now_fn or time.monotonic
    rss_fn = rss_fn or _peak_rss_bytes
    t0 = float(now())
    log_lines = []

    def log(message):
        line = _log_line(message)
        log_lines.append(line)
        print(line)

    p_b, p_f, p1 = load_prior_fn(model_f_root)
    setup_calls = d16.SETUP_FIXED_UNITS
    log("prior chain loaded from %s" % model_f_root)
    if oracle_parts is not None:
        oracle_prior_fn = _compose_oracle(oracle_parts, p_f)
        log("composed oracle closure over p2")
    blocks = {}
    for block_seed in d16.BLOCK_SEEDS:
        blocks[int(block_seed)] = sample_fn(p_b, p_f, p1, block_seed)
    setup_calls += len(d16.BLOCK_SEEDS)
    log("sampled matched blocks count=%d" % len(d16.BLOCK_SEEDS))
    graphs_l1, graphs_l2, graph_rows = {}, {}, []
    for profile, rows in d16.CELLS:
        for graph_seed in d16.GRAPH_SEEDS[(profile, int(rows))]:
            start = float(now())
            if profile in d16.L1_PROFILES:
                graph = build_l1_fn(profile, int(rows), int(graph_seed))
                graphs_l1[(profile, int(rows),
                           int(graph_seed))] = graph
            else:
                graph = build_l2_fn(int(rows), int(graph_seed))
                graphs_l2[(int(rows), int(graph_seed))] = graph
            graph_rows.append(_graph_row(graph, float(now()) - start))
            setup_calls += 1
    admitted = sum(1 for row in graph_rows if row["admitted"])
    log("built %d graphs admitted=%d" % (len(graph_rows), admitted))
    if setup_calls != d16.SETUP_CALL_CEILING:
        raise RuntimeError("setup unit count %d != frozen %d"
                           % (setup_calls, d16.SETUP_CALL_CEILING))

    outcome = d16.execute_plan(
        plan, graphs_l1, graphs_l2, blocks, decode_fn, syndrome_fn,
        oracle_prior_fn=oracle_prior_fn, now=now, rss_fn=rss_fn)
    records = outcome["records"]
    engineering_reason = outcome["engineering_reason"]
    # Frozen-order identity gate: every dispatched record must match the
    # frozen plan entry at its position. Any deviation is a contract STOP.
    for pos, (record, entry) in enumerate(zip(records, plan)):
        for key in ("point_idx", "layer", "arm", "rows", "graph_seed",
                    "block_seed"):
            if str(record[key]) != str(entry[key]):
                raise RuntimeError(
                    "dispatch order violated at position %d: %r != %r"
                    % (pos, {k: record.get(k) for k in
                             ("arm", "rows", "block_seed")}, entry))
        record["call_idx"] = pos
    log("dispatched=%d reason=%s"
        % (len(records), engineering_reason or "none"))

    try:
        tallies = d16.tallies_from_d16_records(records)
    except ValueError:
        tallies = d16.D16Tallies(
            {(p if p in d16.L1_PROFILES else d16.ORACLE_ARM, int(m)):
             [0, 0, 0, 0] for p, m in d16.CELLS})
    per_cell: dict[str, Any] = {}
    for profile, m in d16.CELLS:
        arm = profile if profile in d16.L1_PROFILES else d16.ORACLE_ARM
        vec = list(tallies.per_graph(arm, int(m)))
        exact = int(sum(vec))
        lo, hi = d16.wilson_interval(exact, d16.CELL_TRIALS)
        per_cell["%s:m%d" % (arm, int(m))] = {
            "pool": exact, "per_graph": vec,
            "adequate": bool(d16.is_cell_adequate(tallies, arm, int(m))),
            "weak": bool(d16.is_cell_weak(tallies, arm, int(m))),
            "wilson_lo": lo, "wilson_hi": hi,
            "descriptive_only": True}
    seeds_045 = d16.GRAPH_SEEDS[("L045", 125)]
    seeds_055 = d16.GRAPH_SEEDS[("L055", 125)]
    ref, chal = {}, {}
    for r in records:
        if int(r["rows"]) != 125:
            continue
        if r["arm"] == "L045" \
                and int(r["graph_seed"]) in seeds_045:
            ref[(seeds_045.index(int(r["graph_seed"])),
                 int(r["block_seed"]))] = bool(r["exact"])
        elif r["arm"] == "L055" \
                and int(r["graph_seed"]) in seeds_055:
            chal[(seeds_055.index(int(r["graph_seed"])),
                  int(r["block_seed"]))] = bool(r["exact"])
    try:
        paired = {"m125": d16.describe_paired_l1(ref, chal)}
    except ValueError:
        paired = {"m125": {"challenger_only": 0, "reference_only": 0,
                           "concordant": 0, "trials": 0, "cells": 32,
                           "descriptive_only": True}}
    terminal = d16.route_terminal(tallies, engineering_reason)
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn())
    budget_violations = []
    if len(records) > d16.SCIENTIFIC_CALL_CEILING:
        budget_violations.append("scientific calls exceed ceiling")
    if wall_s > d16.WALL_BUDGET_S:
        budget_violations.append("wall budget exceeded")
    if peak_rss >= d16.RSS_BUDGET_BYTES:
        budget_violations.append("RSS budget exceeded")
    log("terminal=%s" % terminal)

    # Manifest precedent (D11/D12/D14/D15): the manifest retains the frozen
    # scientific command identity; authorization lives in the CLI flag plus
    # the separate explicit authorization, never in this string.
    manifest = {
        "schema": "v72p2d16_matched_backoff_manifest_v1",
        "change_id": d16.CHANGE_ID, "cycle": d16.CYCLE_ID,
        "claim_ceiling": d16.CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "model_f_root": str(model_f_root), "out_root": str(resolved),
        "batch_id": d16.D16_BATCH_ID,
        "field": {"q": d16.Q, "poly": d16.POLY,
                  "factory": "GF2mField.create(32)"},
        "arms": list(d16.ARMS),
        "l1_profiles": list(d16.L1_PROFILES),
        "width": d16.N, "rows_l1": list(d16.ROWS_L1),
        "rows_l2": list(d16.ROWS_L2),
        "cells": _cell_table_meta(),
        "graph_seeds": {("%s:m%d" % (p, int(m))): list(
            d16.GRAPH_SEEDS[(p, int(m))]) for p, m in d16.CELLS},
        "block_seeds": list(d16.BLOCK_SEEDS),
        "coefficient_rule":
            "v10_seed(d10:coeff:{width}:{graph_seed}) -> default_rng -> "
            "integers(1,32) per edge in sorted (variable, check) order",
        "prior_chain": d16.PRIOR_CHAIN,
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": d16.DECODER_MAX_ITER,
                    "damping_alpha": d16.DAMPING_ALPHA,
                    "warm_beliefs": None, "schedule": "cold row-layered"},
        "matrix": {"planned_calls": len(plan),
                   "shape": "3 cells x 4 graphs x 8 blocks",
                   "call_order": ("L045 then L055 then L2-ORACLE; graphs "
                                  "ascending; blocks ascending"),
                   "progress_rule": "none (no conditional progression)"},
        "budgets": _budget_meta(),
        "setup_calls": setup_calls,
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": d16.AUTHORIZATION,
        "predecessor_boundary": ("predecessor evidence is contextual only; "
                                 "the D16 gate accepts only batch_id=%s "
                                 "records" % d16.D16_BATCH_ID),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    arm_rows = _arm_rows(records)
    summary = {
        "schema": "v72p2d16_matched_backoff_summary_v1",
        "change_id": d16.CHANGE_ID, "cycle": d16.CYCLE_ID,
        "claim_ceiling": d16.CLAIM_CEILING,
        "terminal": terminal,
        "pools": {key: value["pool"] for key, value in
                  sorted(per_cell.items())},
        "per_graph": {key: value["per_graph"] for key, value in
                      sorted(per_cell.items())},
        "per_cell": per_cell,
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
        "batch_id": d16.D16_BATCH_ID,
        "model_f_root": str(model_f_root),
        "out_root": str(resolved), "budgets": _budget_meta(),
    }
    log_lines.append(_log_line(
        "D16 terminal=%s calls=%d setup=%d wall_s=%.3f"
        % (terminal, len(records), setup_calls, wall_s)))
    return {
        "resolved": resolved,
        "manifest": manifest,
        "records": records,
        "graph_rows": graph_rows,
        "arm_rows": arm_rows,
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
    _write_csv(resolved / "arm_summary.csv", ARM_SUMMARY_COLUMNS,
               bundle["arm_rows"])
    _write_json(resolved / "summary.json", bundle["summary"])
    with open(resolved / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("".join(line + "\n" for line in bundle["log_lines"]))
    return bundle["summary"]


# --------------------------------------------------------------------------- #
# verify (read-only; zero decoder calls; zero skip; fail-closed)
# --------------------------------------------------------------------------- #
def verify_root(out_root, build_l1_fn=None, build_l2_fn=None,
                check_updated_token_value=None):
    """Recompute a completed D16 root from its evidence; fail-closed.

    ``check_updated_token_value`` is accepted for CLI-shape parity with the
    D11/D14/D15 verifiers and ignored: D16 has no cross-layer leg, so L1
    rows need only a non-empty provenance while ORACLE rows must read
    ORACLE.
    """
    root = Path(out_root)
    build_l1_fn = build_l1_fn or d16.build_l1_graph
    build_l2_fn = build_l2_fn or d16.build_l2_graph
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

    if manifest.get("batch_id") != d16.D16_BATCH_ID \
            or summary.get("batch_id") != d16.D16_BATCH_ID:
        violations.append("batch_id tag mismatch (predecessor boundary)")
    if manifest.get("command") != FROZEN_COMMAND:
        violations.append("manifest command != frozen command")

    plan = d16.build_call_plan()
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
        for key in ("point_idx", "layer", "arm", "rows", "graph_seed",
                    "block_seed"):
            if str(row[key]) != str(entry[key]):
                violations.append("decoder row %d %s %r != planned %r"
                                  % (index, key, row[key], entry[key]))
        if row.get("batch_id") != d16.D16_BATCH_ID:
            violations.append("decoder row %d batch_id tag missing" % index)
        if int(row["disclosed_bits"]) != d16.disclosed_bits(
                _as_int(row["rows"])):
            violations.append("decoder row %d disclosed != 5m" % index)
        if abs(_as_float(row["effective_factor"])
               - d16.effective_factor(row["layer"],
                                      _as_int(row["rows"]))) > 1e-9:
            violations.append("decoder row %d factor != disclosed/load"
                              % index)
        exact = _as_bool(row["exact"])
        syndrome_ok = _as_bool(row["syndrome_ok"])
        undetected = _as_bool(row["undetected"])
        oracle = _as_bool(row["oracle"])
        graded = _as_bool(row["graded"])
        iterations = _as_int(row["iterations"])
        residual = _as_int(row["residual_syndrome_weight"])
        wall = _as_float(row["wall_s"])
        crash = _as_bool(row["crash"])
        # Metric isolation: exact never without syndrome_ok; undetected
        # never merged into exact.
        if exact and not syndrome_ok:
            problems.append("exact without syndrome_ok (metric isolation)")
        if undetected and exact:
            problems.append("undetected merged into exact")
        if row["arm"] == d16.ORACLE_ARM:
            if not oracle or graded:
                problems.append("ORACLE row must be oracle/ungraded")
            if str(row["belief_provenance"]).strip() != "ORACLE":
                problems.append("ORACLE provenance must be ORACLE")
            if row["layer"] != "L2":
                problems.append("ORACLE row must read layer L2")
        else:
            if oracle:
                problems.append("non-ORACLE arm marked oracle")
            if not graded:
                problems.append("non-ORACLE arm must be graded")
            if row["layer"] != "L1":
                problems.append("L1 row must read layer L1")
            if not str(row["belief_provenance"]).strip():
                problems.append("provenance missing")
        if crash:
            if iterations != -1 or residual != -1 or exact or syndrome_ok \
                    or undetected:
                problems.append("crash record inconsistent")
        else:
            if not 0 <= iterations <= d16.DECODER_MAX_ITER:
                problems.append("iterations out of range: %d" % iterations)
            if residual < 0:
                problems.append("residual weight missing")
        if str(row["status"]).strip() in ("",):
            problems.append("empty status")
        if wall < 0.0 or wall > d16.PER_CALL_BUDGET_S:
            problems.append("per-call wall out of budget: %s"
                            % row["wall_s"])
        for problem in problems:
            violations.append("decoder row %d %s" % (index, problem))
        records.append({"call_idx": index, "point_idx": _as_int(
            row["point_idx"]), "layer": row["layer"], "arm": row["arm"],
            "rows": _as_int(row["rows"]),
            "graph_seed": _as_int(row["graph_seed"]),
            "block_seed": _as_int(row["block_seed"]),
            "batch_id": row.get("batch_id"),
            "exact": exact, "syndrome_ok": syndrome_ok,
            "undetected": undetected, "oracle": oracle,
            "graded": graded, "crash": crash, "wall_s": wall})
    if len(decoder_rows) != len(plan):
        violations.append("stored calls %d != frozen plan %d (zero-skip)"
                          % (len(decoder_rows), len(plan)))

    # Shared paired identities: every block feeds all three cells, and every
    # (cell, graph) carries exactly its 8 blocks.
    for profile, m in d16.CELLS:
        arm = profile if profile in d16.L1_PROFILES else d16.ORACLE_ARM
        for seed in d16.GRAPH_SEEDS[(profile, int(m))]:
            got = sorted(rec["block_seed"] for rec in records
                         if rec["arm"] == arm and rec["rows"] == int(m)
                         and rec["graph_seed"] == int(seed))
            if got != sorted(int(s) for s in d16.BLOCK_SEEDS):
                violations.append("cell %s m%d graph %d blocks %s != "
                                  "shared 8 (pairing)"
                                  % (arm, int(m), int(seed), got))

    recomputed_arm_rows = _arm_rows(records)
    stored_arm_keys = {(row["arm"], row["rows"], row["scope"],
                        row["graph_ordinal"]): row for row in arm_rows}
    for row in recomputed_arm_rows:
        key = (row["arm"], str(row["rows"]), row["scope"],
               str(row["graph_ordinal"]))
        stored = stored_arm_keys.get(key)
        if stored is None:
            violations.append("arm_summary row missing: %s" % (key,))
            continue
        for column in ("blocks", "exact_count", "syndrome_valid_count",
                       "undetected_count"):
            if _as_int(stored[column]) != int(row[column]):
                violations.append("arm_summary %s %s stored=%s recomputed=%d"
                                  % (key, column, stored[column],
                                     int(row[column])))

    try:
        tallies = d16.tallies_from_d16_records(records)
        gate_ok = True
    except ValueError as exc:
        violations.append("tallies not rebuildable: %s" % exc)
        gate_ok = False
    if gate_ok:
        stored_pools = summary.get("pools", {})
        for profile, m in d16.CELLS:
            arm = profile if profile in d16.L1_PROFILES else d16.ORACLE_ARM
            if tallies.pool(arm, int(m)) != stored_pools.get(
                    "%s:m%d" % (arm, int(m))):
                violations.append("stored pool %s:m%d != recomputed"
                                  % (arm, int(m)))
        if d16.route_terminal(
                tallies, summary.get("engineering_reason", "")) != \
                summary.get("terminal"):
            violations.append("terminal stored=%r recomputed mismatch"
                              % (summary.get("terminal"),))
    if summary.get("engineering_reason"):
        violations.append("engineering-blocked root (fail-closed)")
    if len(decoder_rows) != int(summary.get("scientific_calls", -1)):
        violations.append("stored calls %d != summary %r"
                          % (len(decoder_rows),
                             summary.get("scientific_calls")))
    if len(decoder_rows) > d16.SCIENTIFIC_CALL_CEILING:
        violations.append("stored calls exceed scientific ceiling")
    if int(summary.get("setup_calls", -1)) != d16.SETUP_CALL_CEILING:
        violations.append("setup calls != frozen %d: %r"
                          % (d16.SETUP_CALL_CEILING,
                             summary.get("setup_calls")))
    if _as_float(summary.get("wall_s", -1.0)) > d16.WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if _as_int(summary.get("peak_rss_bytes", -1)) \
            >= d16.RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")
    max_call_wall = max((rec["wall_s"] for rec in records), default=0.0)
    if max_call_wall > d16.PER_CALL_BUDGET_S:
        violations.append("per-call wall exceeds budget: %s" % max_call_wall)

    for row in graph_rows:
        seed = _as_int(row["graph_seed"])
        m = _as_int(row["rows"])
        if row["arm"] in d16.L1_PROFILES:
            if row["layer"] != "L1":
                violations.append("graph %s layer != L1"
                                  % (row["arm"],))
                continue
            graph = build_l1_fn(row["arm"], m, seed)
        elif row["arm"] == d16.ORACLE_ARM:
            if row["layer"] != "L2":
                violations.append("graph %s layer != L2"
                                  % (row["arm"],))
                continue
            graph = build_l2_fn(m, seed)
        else:
            violations.append("graph arm outside D16 arms: %r"
                              % (row["arm"],))
            continue
        key = (row["arm"], row["rows"], row["graph_seed"])
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
        description="D16 one-point matched-backoff discriminator runner")
    parser.add_argument("--d16-batch", action="store_true",
                        help="run the frozen 96-call D16 matrix (requires "
                             "--execution-authorized from a separate "
                             "explicit authorization)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for "
                             "--d16-batch; default false "
                             "(fail-closed, no-write/no-bind)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--profile-only", action="store_true",
                        help="pre-decoder graph construction profile (no "
                             "decoder, no root)")
    parser.add_argument("--model-f-root", default=d16.MODEL_F_INPUT_ROOT,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    return parser


def profile_only():
    """Pre-decoder profile: real builders + full plan, no decoder, no root."""
    profile = d16.profile_graphs()
    plan = d16.build_call_plan()
    future = Path(d16.FUTURE_ROOT)
    resolved = future.resolve() if future.is_absolute() \
        else (ROOT / future).resolve()
    per_cell = {}
    for entry in profile["graphs"]:
        per_cell["%s:m%d:%d" % (entry["arm"], entry["rows"],
                                entry["seed"])] = {
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
        "per_cell": per_cell,
        "plan_calls": len(plan),
        "plan_per_cell": {"%s:m%d" % (
            e["arm"], e["rows"]): sum(
                1 for x in plan if x["arm"] == e["arm"]
                and x["rows"] == e["rows"])
            for e in plan[:3]},
        "future_root": str(resolved),
        "future_root_absent": not resolved.exists(),
        "decoder_calls": 0,
        "wall_s": profile["wall_s"],
    }


def main(argv=None, *, adapters_override=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--d16-batch", args.d16_batch),
                                        ("--verify", args.verify),
                                        ("--profile-only",
                                         args.profile_only)) if flag]
    if len(selected) != 1:
        parser.error("exactly one of --d16-batch, --verify or "
                     "--profile-only is required")
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
        return 0
    # Refuse --d16-batch before root creation and before any decoder
    # binding or Model-F load while --execution-authorized is false.
    if args.d16_batch and not args.execution_authorized:
        print("refusing --d16-batch: %s (pass --execution-authorized only "
              "under a separate explicit authorization)"
              % d16.AUTHORIZATION, file=sys.stderr)
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
        args.out_root, args.model_f_root, adapters=adapters_override)
    summary = write_batch_root(bundle)
    print("D16 terminal=%s calls=%d setup=%d"
          % (summary["terminal"], summary["scientific_calls"],
             summary["setup_calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
