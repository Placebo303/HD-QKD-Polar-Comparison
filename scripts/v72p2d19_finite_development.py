"""D19 L2 finite-ensemble validation runner — readiness paths.

Frozen command (design §9; requires a separate explicit authorization):

    .venv/bin/python scripts/v72p2d19_finite_development.py --d19-batch \\
      --execution-authorized \\
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \\
      --out-root workspace/d19_l2_finite_ensemble_5f2b8c1d-7a3e-4f90-b6d4-8e1a2c3d4f5a6b

Paths:

- ``--profile-only``: build the 24 frozen D19 graphs with the real
  builders, print structural metrics (components, structural/GF32 rank,
  four-cycles, girth, realized degree histograms, A1–A6 admission, wall
  time) plus the 192-identity max-plan summary and future-root absence, no
  decoder, no root;
- ``--d19-batch``: the frozen matrix (n128 96 calls; n256 96 calls
  dispatched ONLY after a frozen n128 POSITIVE gate; <=192 scientific
  calls, <=42 setup units); refuses unless ``--execution-authorized`` is
  passed (default false; refusal happens before any root creation,
  decoder binding or Model-F load) and requires the injected production
  decoder adapter plus the oracle prior adapter, which only this runner
  constructs (L2-oracle-only diagnostic: the accepted true-U1-conditioned
  path on both arms; no APP/L1/transfer);
- ``--verify``: read-only recomputation of a completed six-file root with
  zero skip, zero decoder calls; exits FAIL on any partial or
  engineering-blocked root.

One fresh root per run; refuses overwrite and protected roots (single
process, no retry, no resume, no seed search, no adaptive stop).
Predecessor evidence is contextual only and can never enter the D19 gate:
decoder records carry ``batch_id == d19-l2-finite-v1`` and the gate
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
    v72p2d19_l2_finite as d19)

EVIDENCE_FILES = d19.EVIDENCE_FILES
FROZEN_COMMAND = d19.FROZEN_COMMAND

DECODER_RECORD_COLUMNS = (
    "call_idx", "width", "n", "m", "layer", "arm", "role",
    "candidate_id", "graph_seed", "block_seed", "batch_id", "exact",
    "syndrome_ok", "undetected", "oracle", "graded", "belief_provenance",
    "iterations", "status", "residual_syndrome_weight",
    "wall_s", "crash", "error", "disclosed_bits")
GRAPH_RECORD_COLUMNS = (
    "arm", "width", "graph_seed", "n", "m", "E", "status",
    "admitted", "failure_reason", "admission", "construction_wall_s")
ARM_SUMMARY_COLUMNS = (
    "arm", "width", "scope", "graph_ordinal", "blocks", "exact_count",
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
# arm summary rows (pooled + per-graph; exact/syndrome/undetected separate)
# --------------------------------------------------------------------------- #
def _arm_rows(records):
    rows = []
    for width in d19.WIDTHS:
        for arm in d19.ARMS:
            scoped = [rec for rec in records
                      if rec["arm"] == arm
                      and int(rec["width"]) == int(width)]
            seeds = d19.GRAPH_SEEDS[int(width)]
            for ordinal, seed in enumerate(seeds):
                cell = [rec for rec in scoped
                        if int(rec["graph_seed"]) == int(seed)]
                rows.append({
                    "arm": arm, "width": width, "scope": "graph",
                    "graph_ordinal": ordinal, "blocks": len(cell),
                    "exact_count": sum(1 for rec in cell if rec["exact"]),
                    "syndrome_valid_count":
                        sum(1 for rec in cell if rec["syndrome_ok"]),
                    "undetected_count":
                        sum(1 for rec in cell if rec["undetected"])})
            rows.append({
                "arm": arm, "width": width, "scope": "pooled",
                "graph_ordinal": "POOLED", "blocks": len(scoped),
                "exact_count": sum(1 for rec in scoped if rec["exact"]),
                "syndrome_valid_count":
                    sum(1 for rec in scoped if rec["syndrome_ok"]),
                "undetected_count":
                    sum(1 for rec in scoped if rec["undetected"])})
    return rows


def _cell_table_meta():
    return [{"arm": arm, "role": d19.ARM_ROLE[arm],
             "candidate_id": d19.ARM_CANDIDATE[arm],
             "n": int(width), "m": d19.ROWS[int(width)],
             "var_counts": dict(d19.VAR_PROFILES[(arm, int(width))]),
             "check_counts": dict(d19.CHECK_TABLE[(arm, int(width))]),
             "E": d19.EDGE_TOTALS[(arm, int(width))],
             "disclosed_bits": d19.disclosed_bits(d19.ROWS[int(width)])}
            for width in d19.WIDTHS for arm in d19.ARMS]


def _budget_meta():
    return {
        "scientific_calls": d19.SCIENTIFIC_CALL_CEILING,
        "setup_calls": d19.SETUP_CALL_CEILING,
        "wall_s": d19.WALL_BUDGET_S,
        "per_call_s": d19.PER_CALL_BUDGET_S,
        "rss_bytes": d19.RSS_BUDGET_BYTES,
        "processes": 1,
        "retry": False, "resume": False,
        "seed_search": False, "adaptive_stop": False,
    }


def _graph_row(graph, wall_s):
    structure = graph.get("structure") or {}
    return {
        "arm": graph["arm"], "width": graph["width"],
        "graph_seed": graph["graph_seed"],
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
    # files untouched; same pattern as the D11/D14/D15/D16 runners). Lazy
    # so the fake/test path never enters this module.
    import importlib.util

    key = "v72p2d10_r2_runner_reuse_d19"
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
    R2/D5 helper — no kernel copies, no alternate algorithms. Signatures
    are validated here, before any root creation, Model-F load, or decoder
    call. Resolving never invokes: decoder calls and Model-F content load
    happen only inside the authorized orchestrator after plan validation.
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

    def sample_fn(p_b, p_f, p1, seed, width):
        # One matched source block per frozen block seed and width; carries
        # u2 for the ORACLE target leg. The oracle prior is composed
        # per-call from the loaded p2 (true-U1-conditioned), never here.
        block = d5.sample_matched_block(p_b, p_f, int(width), int(seed))
        import numpy as np

        return {
            "bob": np.asarray(block["bob"], dtype=np.int64),
            "u1": np.asarray(block["u1"], dtype=np.int64),
            "u2": np.asarray(block["u2"], dtype=np.int64),
        }

    _require_signature(sample_fn, ["p_b", "p_f", "p1", "seed", "width"],
                       "sample_fn")
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
def _validate_call_plan(plan, widths):
    """Contract-check the frozen plan BEFORE binding/loading/decoding.

    Frozen order (width ascending; graphs ascending; blocks ascending; arm
    DV3 then L020 adjacent pairs; ``call_idx`` contiguous) with frozen
    cells, seeds and block pairing. Any deviation raises before any
    adapter is bound, Model-F content loads, or the root is touched.
    """
    widths = [int(w) for w in widths]
    if len(plan) != 96 * len(widths):
        raise ValueError("plan has %d calls, frozen %d"
                         % (len(plan), 96 * len(widths)))
    pos = 0
    for width in widths:
        for graph_seed in d19.GRAPH_SEEDS[width]:
            for block_seed in d19.BLOCK_SEEDS[width]:
                for arm in d19.ARMS:
                    entry = plan[pos]
                    pos += 1
                    if entry.get("call_idx") != pos - 1 \
                            or int(entry.get("width", -1)) != width \
                            or int(entry.get("n", -1)) != width \
                            or int(entry.get("m", -1)) \
                            != d19.ROWS[width] \
                            or entry.get("arm") != arm \
                            or entry.get("role") != d19.ARM_ROLE[arm] \
                            or entry.get("candidate_id") \
                            != d19.ARM_CANDIDATE[arm] \
                            or int(entry.get("graph_seed", -1)) \
                            != int(graph_seed) \
                            or int(entry.get("block_seed", -1)) \
                            != int(block_seed) \
                            or int(entry.get("disclosed_bits", -1)) \
                            != d19.disclosed_bits(d19.ROWS[width]):
                        raise ValueError(
                            "plan identity/order violated at position %d: %r"
                            % (pos - 1, entry))
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
# Batch orchestrator (plan-first; conditional n256; no filesystem writes)
# --------------------------------------------------------------------------- #
def run_authorized_batch(out_root, model_f_root, *, adapters=None,
                         build_fn=None, now_fn=None, rss_fn=None):
    """Execute the frozen D19 matrix and return the evidence bundle (writes).

    ``adapters`` is a flat dict with ``decode_fn``/``syndrome_fn``/
    ``load_prior_fn``/``sample_fn`` plus either the production
    ``oracle_parts`` composition kit (binder-supplied) or a direct
    ``oracle_prior_fn``; ``None`` production-binds inside, AFTER plan
    validation and the refuse probe. ``build_fn`` may arrive explicitly
    or inside ``adapters`` (fake builders travel with the fake adapter
    dict on the test path); defaults to the frozen real builder. Returns
    the bundle consumed by :func:`write_batch_root`; creates no files and
    no directories.
    """
    plan_n128 = d19.build_call_plan((128,))
    plan_n256 = d19.build_call_plan((256,))
    _validate_call_plan(plan_n128, (128,))
    _validate_call_plan(plan_n256, (256,))
    resolved = d19.refuse_out_root(out_root)  # probe only; creates nothing
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
    build_fn = build_fn or inj.pop("build_fn", None) or d19.build_graph
    now = now_fn or time.monotonic
    rss_fn = rss_fn or _peak_rss_bytes
    t0 = float(now())
    log_lines = []

    def log(message):
        line = _log_line(message)
        log_lines.append(line)
        print(line)

    p_b, p_f, p1 = load_prior_fn(model_f_root)
    setup_calls = d19.SETUP_FIXED_UNITS
    log("prior chain loaded from %s" % model_f_root)
    if oracle_parts is not None:
        oracle_prior_fn = _compose_oracle(oracle_parts, p_f)
        log("composed oracle closure over p2")
    blocks: dict[int, dict[int, Any]] = {}
    for width in d19.WIDTHS:
        blocks[int(width)] = {}
        for block_seed in d19.BLOCK_SEEDS[int(width)]:
            blocks[int(width)][int(block_seed)] = sample_fn(
                p_b, p_f, p1, block_seed, int(width))
    setup_calls += sum(len(d19.BLOCK_SEEDS[w]) for w in d19.WIDTHS)
    log("sampled source blocks count=%d"
        % sum(len(v) for v in blocks.values()))
    graphs, graph_rows = {}, []
    for width in d19.WIDTHS:
        for arm in d19.ARMS:
            for graph_seed in d19.GRAPH_SEEDS[int(width)]:
                start = float(now())
                graph = build_fn(arm, int(width), int(graph_seed))
                graphs[(arm, int(width), int(graph_seed))] = graph
                graph_rows.append(_graph_row(graph, float(now()) - start))
                setup_calls += 1
    admitted = sum(1 for row in graph_rows if row["admitted"])
    log("built %d graphs admitted=%d" % (len(graph_rows), admitted))
    if setup_calls != d19.SETUP_CALL_CEILING:
        raise RuntimeError("setup unit count %d != frozen %d"
                           % (setup_calls, d19.SETUP_CALL_CEILING))

    outcome = d19.execute_plan(
        plan_n128, plan_n256, graphs, blocks, decode_fn, syndrome_fn,
        oracle_prior_fn=oracle_prior_fn, now=now, rss_fn=rss_fn)
    records = outcome["records"]
    width_results = outcome["width_results"]
    # Frozen-order identity gate: every dispatched record must match the
    # frozen plan entry at its position. Any deviation is a contract STOP.
    full_plan = plan_n128 + plan_n256
    for pos, record in enumerate(records):
        entry = full_plan[pos]
        for key in ("width", "arm", "graph_seed", "block_seed"):
            if str(record[key]) != str(entry[key]):
                raise RuntimeError(
                    "dispatch order violated at position %d: %r != %r"
                    % (pos, {k: record.get(k) for k in
                             ("arm", "width", "block_seed")}, entry))
        record["call_idx"] = pos
    log("dispatched=%d n256=%s"
        % (len(records), outcome["n256_dispatched"]))

    per_width: dict[str, Any] = {}
    for result in width_results:
        width = int(result["width"])
        tally = result["tally"]
        exact = int(tally["M"] + tally["C"])
        lo, hi = d19.wilson_interval(int(tally["M"]), 48)
        per_width["n%d" % width] = {
            "classification": result["classification"],
            "M": int(tally["M"]), "C": int(tally["C"]),
            "M_g": [int(v) for v in tally["M_g"]],
            "C_g": [int(v) for v in tally["C_g"]],
            "b": int(tally["b"]), "c": int(tally["c"]),
            "discord": int(tally["b"]) - int(tally["c"]),
            "wilson_M_lo": lo, "wilson_M_hi": hi,
            "descriptive_only": True,
            "engineering_reason": result["engineering_reason"]}
    terminal = outcome["terminal"]
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn())
    budget_violations = []
    if len(records) > d19.SCIENTIFIC_CALL_CEILING:
        budget_violations.append("scientific calls exceed ceiling")
    if wall_s > d19.WALL_BUDGET_S:
        budget_violations.append("wall budget exceeded")
    if peak_rss >= d19.RSS_BUDGET_BYTES:
        budget_violations.append("RSS budget exceeded")
    log("terminal=%s" % terminal)

    # Manifest precedent (D11/D12/D14/D15/D16): the manifest retains the
    # frozen scientific command identity; authorization lives in the CLI
    # flag plus the separate explicit authorization, never in this string.
    manifest = {
        "schema": "v72p2d19_l2_finite_manifest_v1",
        "change_id": d19.CHANGE_ID, "cycle": d19.CYCLE_ID,
        "claim_ceiling": d19.CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "model_f_root": str(model_f_root), "out_root": str(resolved),
        "batch_id": d19.D19_BATCH_ID,
        "field": {"q": d19.Q, "poly": d19.POLY,
                  "factory": "GF2mField.create(32)"},
        "arms": list(d19.ARMS),
        "arm_role": dict(d19.ARM_ROLE),
        "arm_candidate": dict(d19.ARM_CANDIDATE),
        "delta_L2": d19.DELTA_L2,
        "widths": list(d19.WIDTHS),
        "rows": {str(w): d19.ROWS[int(w)] for w in d19.WIDTHS},
        "cells": _cell_table_meta(),
        "graph_seeds": {str(w): list(d19.GRAPH_SEEDS[int(w)])
                        for w in d19.WIDTHS},
        "block_seeds": {str(w): list(d19.BLOCK_SEEDS[int(w)])
                        for w in d19.WIDTHS},
        "coefficient_rule":
            "v10_seed(d19:l2:coeff:{width}:{arm}:{graph_seed}) -> "
            "default_rng -> integers(1,32) per edge in sorted (variable, "
            "check) order",
        "prior_chain": d19.PRIOR_CHAIN,
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": d19.DECODER_MAX_ITER,
                    "damping_alpha": d19.DAMPING_ALPHA,
                    "warm_beliefs": None, "schedule": "cold row-layered"},
        "matrix": {"planned_calls": 192,
                    "shape": "2 widths x 2 arms x 6 graphs x 8 blocks",
                    "call_order": ("width ascending; graphs ascending; "
                                   "blocks ascending; arm DV3 then L020"),
                    "progress_rule": "n256 dispatches iff n128 POSITIVE; "
                                     "controls never advance independently"},
        "budgets": _budget_meta(),
        "setup_calls": setup_calls,
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": d19.AUTHORIZATION,
        "predecessor_boundary": ("predecessor evidence is contextual only; "
                                 "the D19 gate accepts only batch_id=%s "
                                 "records" % d19.D19_BATCH_ID),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    arm_rows = _arm_rows(records)
    summary = {
        "schema": "v72p2d19_l2_finite_summary_v1",
        "change_id": d19.CHANGE_ID, "cycle": d19.CYCLE_ID,
        "claim_ceiling": d19.CLAIM_CEILING,
        "terminal": terminal,
        "per_width": per_width,
        "n256_dispatched": bool(outcome["n256_dispatched"]),
        "scientific_calls": len(records),
        "planned_calls": 192,
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
        "batch_id": d19.D19_BATCH_ID,
        "model_f_root": str(model_f_root),
        "out_root": str(resolved), "budgets": _budget_meta(),
    }
    log_lines.append(_log_line(
        "D19 terminal=%s calls=%d setup=%d wall_s=%.3f"
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
def verify_root(out_root, build_fn=None):
    """Recompute a completed D19 root from its evidence; fail-closed."""
    root = Path(out_root)
    build_fn = build_fn or d19.build_graph
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

    if manifest.get("batch_id") != d19.D19_BATCH_ID \
            or summary.get("batch_id") != d19.D19_BATCH_ID:
        violations.append("batch_id tag mismatch (predecessor boundary)")
    if manifest.get("command") != FROZEN_COMMAND:
        violations.append("manifest command != frozen command")

    plan_n128 = d19.build_call_plan((128,))
    plan_n256 = d19.build_call_plan((256,))
    plan_by_idx = {e["call_idx"]: e for e in plan_n128}
    plan_by_idx.update({96 + e["call_idx"]: e for e in plan_n256})
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
        for key in ("width", "arm", "graph_seed", "block_seed"):
            if str(row[key]) != str(entry[key]):
                violations.append("decoder row %d %s %r != planned %r"
                                  % (index, key, row[key], entry[key]))
        if row.get("batch_id") != d19.D19_BATCH_ID:
            violations.append("decoder row %d batch_id tag missing" % index)
        if int(row["disclosed_bits"]) != d19.disclosed_bits(
                _as_int(row["m"])):
            violations.append("decoder row %d disclosed != 5m" % index)
        if row.get("role") != d19.ARM_ROLE.get(row.get("arm")):
            violations.append("decoder row %d role != frozen arm role"
                              % index)
        if row.get("candidate_id") \
                != d19.ARM_CANDIDATE.get(row.get("arm")):
            violations.append("decoder row %d candidate != frozen arm "
                              "candidate" % index)
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
        # never merged into exact; every row is ORACLE/ungraded L2.
        if exact and not syndrome_ok:
            problems.append("exact without syndrome_ok (metric isolation)")
        if undetected and exact:
            problems.append("undetected merged into exact")
        if not oracle or graded:
            problems.append("D19 row must be oracle/ungraded")
        if str(row["belief_provenance"]).strip() != "ORACLE":
            problems.append("ORACLE provenance must be ORACLE")
        if row["layer"] != "L2":
            problems.append("D19 row must read layer L2")
        if crash:
            if iterations != -1 or residual != -1 or exact or syndrome_ok \
                    or undetected:
                problems.append("crash record inconsistent")
        else:
            if not 0 <= iterations <= d19.DECODER_MAX_ITER:
                problems.append("iterations out of range: %d" % iterations)
            if residual < 0:
                problems.append("residual weight missing")
        if str(row["status"]).strip() in ("",):
            problems.append("empty status")
        if wall < 0.0 or wall > d19.PER_CALL_BUDGET_S:
            problems.append("per-call wall out of budget: %s"
                            % row["wall_s"])
        for problem in problems:
            violations.append("decoder row %d %s" % (index, problem))
        records.append({"call_idx": index, "width": _as_int(row["width"]),
                        "arm": row["arm"],
                        "graph_seed": _as_int(row["graph_seed"]),
                        "block_seed": _as_int(row["block_seed"]),
                        "batch_id": row.get("batch_id"),
                        "exact": exact, "syndrome_ok": syndrome_ok,
                        "undetected": undetected, "oracle": oracle,
                        "graded": graded, "crash": crash, "wall_s": wall})

    # Conditional width geometry: n128-only roots are complete ONLY when
    # n128 is not POSITIVE; a POSITIVE n128 requires the full 192.
    n128_records = [r for r in records if r["width"] == 128]
    n256_records = [r for r in records if r["width"] == 256]
    try:
        tally_n128 = d19.width_tally(n128_records, 128)
        class_n128 = d19.classify_width(
            tally_n128, summary.get("per_width", {}).get(
                "n128", {}).get("engineering_reason", ""))
    except ValueError as exc:
        violations.append("n128 tally not rebuildable: %s" % exc)
        tally_n128, class_n128 = None, d19.ENGINEERING_BLOCKED
    if class_n128 == d19.POSITIVE:
        if len(decoder_rows) != 192:
            violations.append("POSITIVE n128 requires full 192 calls "
                              "(zero-skip); stored %d" % len(decoder_rows))
        try:
            tally_n256 = d19.width_tally(n256_records, 256)
            class_n256 = d19.classify_width(
                tally_n256, summary.get("per_width", {}).get(
                    "n256", {}).get("engineering_reason", ""))
        except ValueError as exc:
            violations.append("n256 tally not rebuildable: %s" % exc)
            tally_n256, class_n256 = None, d19.ENGINEERING_BLOCKED
    else:
        tally_n256, class_n256 = None, None
        if len(decoder_rows) != 96:
            violations.append("non-POSITIVE n128 root must carry exactly "
                              "96 calls; stored %d" % len(decoder_rows))
        if n256_records:
            violations.append("n256 records without POSITIVE n128 "
                              "(controls never advance)")

    # Shared paired identities per entered width: both arms carry the same
    # 8 blocks on every graph.
    for width, tally in ((128, tally_n128), (256, tally_n256)):
        if tally is None:
            continue
        for arm in d19.ARMS:
            for seed in d19.GRAPH_SEEDS[width]:
                got = sorted(rec["block_seed"] for rec in records
                             if rec["arm"] == arm
                             and rec["width"] == width
                             and rec["graph_seed"] == int(seed))
                if got != sorted(int(s)
                                 for s in d19.BLOCK_SEEDS[width]):
                    violations.append("width %d cell %s graph %d blocks %s "
                                      "!= shared 8 (pairing)"
                                      % (width, arm, int(seed), got))

    recomputed_arm_rows = _arm_rows(records)
    stored_arm_keys = {(row["arm"], row["width"], row["scope"],
                        row["graph_ordinal"]): row for row in arm_rows}
    for row in recomputed_arm_rows:
        key = (row["arm"], str(row["width"]), row["scope"],
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

    if tally_n128 is not None:
        stored_n128 = summary.get("per_width", {}).get("n128", {})
        for key in ("M", "C", "b", "c"):
            if int(stored_n128.get(key, -1)) != int(tally_n128[key]):
                violations.append("stored n128 %s != recomputed" % key)
        if stored_n128.get("classification") != class_n128:
            violations.append("stored n128 gate != recomputed")
    if tally_n256 is not None:
        stored_n256 = summary.get("per_width", {}).get("n256", {})
        for key in ("M", "C", "b", "c"):
            if int(stored_n256.get(key, -1)) != int(tally_n256[key]):
                violations.append("stored n256 %s != recomputed" % key)
        if stored_n256.get("classification") != class_n256:
            violations.append("stored n256 gate != recomputed")
    n128_result = {"width": 128, "classification": class_n128,
                   "engineering_reason": summary.get("per_width", {}).get(
                       "n128", {}).get("engineering_reason", "")}
    n256_result = None
    if tally_n256 is not None:
        n256_result = {
            "width": 256, "classification": class_n256,
            "engineering_reason": summary.get("per_width", {}).get(
                "n256", {}).get("engineering_reason", "")}
    elif class_n128 == d19.POSITIVE:
        n256_result = {"width": 256,
                       "classification": d19.ENGINEERING_BLOCKED,
                       "engineering_reason": "missing n256 leg"}
    if d19.route_terminal(n128_result, n256_result) \
            != summary.get("terminal"):
        violations.append("terminal stored=%r recomputed mismatch"
                          % (summary.get("terminal"),))
    if summary.get("per_width", {}).get("n128", {}).get(
            "engineering_reason") \
            or summary.get("per_width", {}).get(
                "n256", {}).get("engineering_reason"):
        violations.append("engineering-blocked root (fail-closed)")
    if summary.get("n256_dispatched") not in (True, False):
        violations.append("n256_dispatched flag missing")
    elif bool(summary.get("n256_dispatched")) != (tally_n256 is not None):
        violations.append("n256_dispatched flag != stored legs")
    if len(decoder_rows) != int(summary.get("scientific_calls", -1)):
        violations.append("stored calls %d != summary %r"
                          % (len(decoder_rows),
                             summary.get("scientific_calls")))
    if len(decoder_rows) > d19.SCIENTIFIC_CALL_CEILING:
        violations.append("stored calls exceed scientific ceiling")
    if int(summary.get("setup_calls", -1)) != d19.SETUP_CALL_CEILING:
        violations.append("setup calls != frozen %d: %r"
                          % (d19.SETUP_CALL_CEILING,
                             summary.get("setup_calls")))
    if _as_float(summary.get("wall_s", -1.0)) > d19.WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if _as_int(summary.get("peak_rss_bytes", -1)) \
            >= d19.RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")
    max_call_wall = max((rec["wall_s"] for rec in records), default=0.0)
    if max_call_wall > d19.PER_CALL_BUDGET_S:
        violations.append("per-call wall exceeds budget: %s" % max_call_wall)

    for row in graph_rows:
        seed = _as_int(row["graph_seed"])
        width = _as_int(row["width"])
        if row["arm"] not in d19.ARMS or width not in d19.WIDTHS:
            violations.append("graph arm/width outside D19 cells: %r"
                              % ((row["arm"], row["width"]),))
            continue
        graph = build_fn(row["arm"], width, seed)
        key = (row["arm"], row["width"], row["graph_seed"])
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
    if len(graph_rows) != 24:
        violations.append("graph rows %d != 24 built objects"
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
        description="D19 L2 finite-ensemble validation runner")
    parser.add_argument("--d19-batch", action="store_true",
                        help="run the frozen D19 matrix (requires "
                             "--execution-authorized from a separate "
                             "explicit authorization)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for "
                             "--d19-batch; default false "
                             "(fail-closed, no-write/no-bind)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--profile-only", action="store_true",
                        help="pre-decoder graph construction profile (no "
                             "decoder, no root)")
    parser.add_argument("--model-f-root", default=d19.MODEL_F_INPUT_ROOT,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    return parser


def profile_only():
    """Pre-decoder profile: real builders + max plan, no decoder, no root."""
    profile = d19.profile_graphs()
    plan = d19.build_call_plan((128, 256))
    future = Path(d19.FUTURE_ROOT)
    resolved = future.resolve() if future.is_absolute() \
        else (ROOT / future).resolve()
    per_cell = {}
    for entry in profile["graphs"]:
        per_cell["%s:n%d:%d" % (entry["arm"], entry["width"],
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
        "plan_per_width": {
            "n128": sum(1 for x in plan if x["width"] == 128),
            "n256": sum(1 for x in plan if x["width"] == 256)},
        "future_root": str(resolved),
        "future_root_absent": not resolved.exists(),
        "decoder_calls": 0,
        "wall_s": profile["wall_s"],
    }


def main(argv=None, *, adapters_override=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--d19-batch", args.d19_batch),
                                        ("--verify", args.verify),
                                        ("--profile-only",
                                         args.profile_only)) if flag]
    if len(selected) != 1:
        parser.error("exactly one of --d19-batch, --verify or "
                     "--profile-only is required")
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
        return 0
    # Refuse --d19-batch before root creation and before any decoder
    # binding or Model-F load while --execution-authorized is false.
    if args.d19_batch and not args.execution_authorized:
        print("refusing --d19-batch: %s (pass --execution-authorized only "
              "under a separate explicit authorization)"
              % d19.AUTHORIZATION, file=sys.stderr)
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
    print("D19 terminal=%s calls=%d setup=%d n256=%s"
          % (summary["terminal"], summary["scientific_calls"],
             summary["setup_calls"], summary["n256_dispatched"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
