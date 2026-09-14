"""D10 R3 fresh-graph scaling replication runner — readiness paths.

Frozen command (design §5; requires a separate explicit authorization):

    .venv/bin/python scripts/v72p2d10_r3_development.py --r3-batch \\
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \\
      --out-root workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d

Paths:

- ``--profile-only``: build the 24 frozen R3 graphs with the real builders,
  print structural metrics (components, structural/GF32 rank, four-cycles,
  girth, A1–A6 admission, wall time), no decoder, no root;
- ``--r3-batch``: n128 first (144 paired calls), n256 (144) if and only if
  n128 is ``R3_REPRODUCED`` (<=288 scientific calls, <=50 setup units);
  refuses unless ``--execution-authorized`` is passed (default false; refusal
  happens before any root creation, decoder binding or Model-F load) and
  requires the injected production decoder adapter, which only this runner
  constructs;
- ``--verify``: read-only recomputation of a completed six-file root with
  zero skip, zero decoder calls; exits FAIL on any partial or
  engineering-blocked root.

One fresh root per run; refuses overwrite, protected roots and partial/adapted
runs (single process, no retry, no resume, no seed search, no adaptive stop).
A1 evidence is contextual only and can never enter the R3 gate: decoder
records carry ``batch_id == d10-r3-fresh-v1`` and the gate constructor
rejects anything else.
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
    v72p2d10_r3_fresh_scaling as r3)

_R2_RUNNER_PATH = ROOT / "scripts" / "v72p2d10_mixed_degree_l1_development.py"


def _load_r2_runner():
    # R302 reuse: prior-chain, block, CSV/JSON and parse helpers live in the
    # R2 runner; import them read-only instead of copying (R2 files untouched).
    spec = importlib.util.spec_from_file_location(
        "v72p2d10_r2_runner_reuse", str(_R2_RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["v72p2d10_r2_runner_reuse"] = module
    spec.loader.exec_module(module)
    return module


_r2run = _load_r2_runner()

EVIDENCE_FILES = r3.EVIDENCE_FILES
FROZEN_COMMAND = r3.FROZEN_COMMAND

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
    for width in r3.R3_WIDTHS:
        for arm in r3.ARMS:
            for graph_seed in r3.GRAPH_SEEDS[width]:
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
        for (arm, width), cell in sorted(r3.DEGREE_TABLE.items())}


def _budget_meta():
    return {
        "scientific_calls": r3.SCIENTIFIC_CALL_CEILING,
        "setup_calls": r3.SETUP_CALL_CEILING,
        "wall_s": r3.WALL_BUDGET_S,
        "per_call_s": r3.PER_CALL_BUDGET_S,
        "rss_bytes": r3.RSS_BUDGET_BYTES,
        "processes": 1,
        "retry": False, "resume": False,
        "seed_search": False, "adaptive_stop": False,
    }


# --------------------------------------------------------------------------- #
# batch (conditional n128 -> gate -> n256)
# --------------------------------------------------------------------------- #
def run_r3_batch(out_root, model_f_root, decode_fn, syndrome_fn, *,
                 build_graph_fn=None, load_prior_fn=None, sample_fn=None,
                 floor_fn=None, now_fn=None, rss_fn=None):
    """Execute and persist one authorized D10 R3 batch (injected decoder).

    ``decode_fn``/``syndrome_fn`` are explicit injections supplied by the
    caller (the ``--r3-batch`` entrypoint constructs the production adapter).
    n256 is dispatched if and only if n128 classifies ``R3_REPRODUCED``.
    """
    resolved = r3.refuse_out_root(out_root)
    plan = r3.build_full_plan()
    build_graph_fn = build_graph_fn or r3.build_graph
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
    setup_calls = r3.SETUP_FIXED_UNITS
    log("prior chain loaded from %s" % model_f_root)
    blocks = {}
    for width in r3.R3_WIDTHS:
        blocks[width] = _r2run.prepare_blocks(
            p_b, p_f, p1, width, r3.BLOCK_SEEDS[width], sample_fn=sample_fn,
            floor_fn=floor_fn)
        setup_calls += len(r3.BLOCK_SEEDS[width])
        log("sampled matched blocks width=%d count=%d"
            % (width, len(r3.BLOCK_SEEDS[width])))
    graphs = {}
    graph_rows = []
    for width in r3.R3_WIDTHS:
        for arm in r3.ARMS:
            for graph_seed in r3.GRAPH_SEEDS[width]:
                start = float(now())
                graph = build_graph_fn(arm, width, graph_seed)
                graph_rows.append(
                    _r2run._graph_row(graph, float(now()) - start))
                graphs[(arm, width, graph_seed)] = graph
                setup_calls += 1
    admitted = sum(1 for row in graph_rows if row["admitted"])
    log("built %d graphs admitted=%d" % (len(graph_rows), admitted))
    if setup_calls != r3.SETUP_CALL_CEILING:
        raise RuntimeError("setup unit count %d != frozen %d"
                           % (setup_calls, r3.SETUP_CALL_CEILING))

    width_results = []
    records: list[dict] = []
    n128 = r3.execute_width(128, plan, graphs, blocks, decode_fn,
                            syndrome_fn, now=now, rss_fn=rss_fn)
    records.extend(n128["records"])
    width_results.append({k: n128[k] for k in
                          ("width", "mix_exact", "dv3_exact", "mix_pool",
                           "dv3_pool", "paired", "classification",
                           "engineering_reason")})
    log("n128 classification=%s M=%d C=%d"
        % (n128["classification"], n128["mix_pool"], n128["dv3_pool"]))
    n256 = None
    if r3.n256_permitted(n128["classification"]):
        # Same block/graph dicts restricted by the width-144 plan slice.
        n256 = r3.execute_width(256, plan, graphs, blocks, decode_fn,
                                syndrome_fn, now=now, rss_fn=rss_fn)
        records.extend(n256["records"])
        width_results.append({k: n256[k] for k in
                              ("width", "mix_exact", "dv3_exact", "mix_pool",
                               "dv3_pool", "paired", "classification",
                               "engineering_reason")})
        log("n256 classification=%s M=%d C=%d"
            % (n256["classification"], n256["mix_pool"], n256["dv3_pool"]))
    else:
        log("n256 not dispatched (n128=%s)" % n128["classification"])
    terminal = r3.route_terminal(
        n128["classification"],
        n256["classification"] if n256 is not None else None)
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn())
    budget_violations = []
    if len(records) > r3.SCIENTIFIC_CALL_CEILING:
        budget_violations.append("scientific calls exceed ceiling")
    if wall_s > r3.WALL_BUDGET_S:
        budget_violations.append("wall budget exceeded")
    if peak_rss >= r3.RSS_BUDGET_BYTES:
        budget_violations.append("RSS budget exceeded")
    log("dispatched width_results=%s terminal=%s"
        % ([w["classification"] for w in width_results], terminal))

    resolved.mkdir(parents=True)
    _r2run._write_json(resolved / "manifest.json", {
        "schema": "v72p2d10_r3_fresh_scaling_manifest_v1",
        "change_id": r3.CHANGE_ID, "cycle": r3.CYCLE_ID,
        "claim_ceiling": r3.CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "model_f_root": str(model_f_root), "out_root": str(resolved),
        "l1_only": True, "batch_id": r3.R3_BATCH_ID,
        "field": {"q": r3.r2.Q, "poly": r3.r2.POLY,
                  "factory": "GF2mField.create(32)"},
        "arms": list(r3.ARMS), "arm_roles": dict(r3.ARM_ROLE),
        "widths": list(r3.R3_WIDTHS),
        "degree_table": _degree_table_meta(),
        "graph_seeds": {str(w): list(r3.GRAPH_SEEDS[w])
                        for w in r3.R3_WIDTHS},
        "block_seeds": {str(w): list(r3.BLOCK_SEEDS[w])
                        for w in r3.R3_WIDTHS},
        "coefficient_rule":
            "v10_seed(d10:coeff:{width}:{graph_seed}) -> default_rng -> "
            "integers(1,32) per edge in sorted (variable, check) order",
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": r3.DECODER_MAX_ITER,
                    "damping_alpha": r3.DAMPING_ALPHA,
                    "warm_beliefs": None, "schedule": "cold row-layered"},
        "matrix": {"planned_calls": len(plan),
                   "shape": "2 arms x 2 widths x 6 graphs x 12 blocks",
                   "call_order": ("n128 first, n256 iff R3_REPRODUCED(n128); "
                                  "within a width control then candidate -> "
                                  "graph seed asc -> block seed asc"),
                   "progress_rule": "n128 -> n256 only on R3_REPRODUCED"},
        "budgets": _budget_meta(),
        "setup_calls": setup_calls,
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": r3.AUTHORIZATION,
        "a1_boundary": ("A1 evidence is contextual only; R3 gates accept "
                        "only batch_id=%s records" % r3.R3_BATCH_ID),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    _r2run._write_csv(resolved / "decoder_records.csv",
                      DECODER_RECORD_COLUMNS, records)
    _r2run._write_csv(resolved / "graph_records.csv", GRAPH_RECORD_COLUMNS,
                      graph_rows)
    _r2run._write_csv(resolved / "arm_summary.csv", ARM_SUMMARY_COLUMNS,
                      _arm_rows(records))
    summary = {
        "schema": "v72p2d10_r3_fresh_scaling_summary_v1",
        "change_id": r3.CHANGE_ID, "cycle": r3.CYCLE_ID,
        "claim_ceiling": r3.CLAIM_CEILING,
        "terminal": terminal,
        "widths_dispatched": [w["width"] for w in width_results],
        "width_classifications":
            {str(w["width"]): w["classification"] for w in width_results},
        "width_results": width_results,
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
        "l1_only": True, "batch_id": r3.R3_BATCH_ID,
        "model_f_root": str(model_f_root),
        "out_root": str(resolved), "budgets": _budget_meta(),
    }
    _r2run._write_json(resolved / "summary.json", summary)
    log_lines.append(_r2run._log_line(
        "D10_R3 terminal=%s calls=%d setup=%d wall_s=%.3f"
        % (terminal, len(records), setup_calls, wall_s)))
    with open(resolved / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("".join(line + "\n" for line in log_lines))
    return summary


# --------------------------------------------------------------------------- #
# verify (read-only; zero decoder calls; zero skip; fail-closed)
# --------------------------------------------------------------------------- #
def verify_root(out_root, build_graph_fn=None):
    """Recompute a completed R3 root from its evidence; fail-closed."""
    root = Path(out_root)
    build_graph_fn = build_graph_fn or r3.build_graph
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

    if manifest.get("batch_id") != r3.R3_BATCH_ID \
            or summary.get("batch_id") != r3.R3_BATCH_ID:
        violations.append("batch_id tag mismatch (A1 boundary)")

    plan = r3.build_full_plan()
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
        if row.get("batch_id") != r3.R3_BATCH_ID:
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
            violations.append("decoder row %d exact without syndrome_ok"
                              % index)
            ok = False
        if crash:
            if iterations != -1 or residual != -1 or exact or syndrome_ok:
                violations.append("decoder row %d crash record inconsistent"
                                  % index)
                ok = False
        else:
            if not 0 <= iterations <= r3.DECODER_MAX_ITER:
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
        if wall < 0.0 or wall > r3.PER_CALL_BUDGET_S:
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

    dispatched = []
    for record in records:
        if record["width"] not in dispatched:
            dispatched.append(record["width"])
    if dispatched != [w for w in r3.R3_WIDTHS if w in dispatched]:
        violations.append("dispatched width order invalid: %s" % dispatched)
    for width in dispatched:
        for entry in (e for e in plan if e["width"] == width):
            if entry["call_idx"] >= len(records) or not any(
                    rec["call_idx"] == entry["call_idx"] for rec in records):
                violations.append("planned call %d missing (zero-skip)"
                                  % entry["call_idx"])
                skipped += 1
    # Conditional dispatch: n256 present iff n128 classified REPRODUCED.
    if 256 in dispatched and 128 not in dispatched:
        violations.append("n256 dispatched without n128")

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
    n128_class = None
    for result in width_results:
        width = int(result["width"])
        if width == 128:
            n128_class = result["classification"]
        try:
            tallies = r3.tallies_from_r3_records(records, width)
        except ValueError as exc:
            violations.append("width %d tallies not rebuildable: %s"
                              % (width, exc))
            continue
        recomputed = r3.classify_r3(
            tallies, str(result.get("engineering_reason", "")))
        if recomputed != result["classification"]:
            violations.append("width %d classification stored=%s recomputed=%s"
                              % (width, result["classification"], recomputed))
        if list(tallies.mix_exact) != result.get("mix_exact") \
                or list(tallies.dv3_exact) != result.get("dv3_exact"):
            violations.append("width %d stored counts != recomputed" % width)
        if result["classification"] == r3.ENGINEERING_BLOCKED:
            violations.append("width %d engineering-blocked (fail-closed)"
                              % width)
    if 256 in dispatched and n128_class != r3.REPRODUCED:
        violations.append("n256 dispatched without R3_REPRODUCED(n128)")
    if r3.route_terminal(
            width_results[0]["classification"] if width_results else "NONE",
            width_results[1]["classification"] if len(width_results) > 1
            else None) != summary.get("terminal"):
        violations.append("terminal stored=%r recomputed=%r"
                          % (summary.get("terminal"),
                             r3.route_terminal(
                                 width_results[0]["classification"]
                                 if width_results else "NONE",
                                 width_results[1]["classification"]
                                 if len(width_results) > 1 else None)))
    if bool(summary.get("l1_only")) is not True \
            or bool(manifest.get("l1_only")) is not True:
        violations.append("l1_only flag not true")

    if len(decoder_rows) != int(summary.get("scientific_calls", -1)):
        violations.append("stored calls %d != summary %r"
                          % (len(decoder_rows),
                             summary.get("scientific_calls")))
    if len(decoder_rows) > r3.SCIENTIFIC_CALL_CEILING:
        violations.append("stored calls exceed scientific ceiling")
    if int(summary.get("setup_calls", -1)) != r3.SETUP_CALL_CEILING:
        violations.append("setup calls != frozen %d: %r"
                          % (r3.SETUP_CALL_CEILING,
                             summary.get("setup_calls")))
    if _r2run._as_float(summary.get("wall_s", -1.0)) > r3.WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if _r2run._as_int(summary.get("peak_rss_bytes", -1)) \
            >= r3.RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")
    max_call_wall = max((_r2run._as_float(rec["wall_s"])
                         for rec in decoder_rows), default=0.0)
    if max_call_wall > r3.PER_CALL_BUDGET_S:
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
# CLI (R303: --r3-batch requires explicit --execution-authorized)
# --------------------------------------------------------------------------- #
def build_parser():
    parser = argparse.ArgumentParser(
        description="D10 R3 fresh-graph scaling replication runner")
    parser.add_argument("--r3-batch", action="store_true",
                        help="run the frozen conditional 144->288-call R3 "
                             "matrix (requires --execution-authorized from a "
                             "separate explicit authorization)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for "
                             "--r3-batch; default false "
                             "(fail-closed, no-write/no-bind)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--profile-only", action="store_true",
                        help="pre-decoder graph construction profile (no "
                             "decoder, no root)")
    parser.add_argument("--model-f-root", default=r3.MODEL_F_INPUT_ROOT,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    return parser


def profile_only():
    """R309 profile helper: real builders, no decoder, no root."""
    return r3.profile_graphs()


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--r3-batch", args.r3_batch),
                                        ("--verify", args.verify),
                                        ("--profile-only",
                                         args.profile_only)) if flag]
    if len(selected) != 1:
        parser.error("exactly one of --r3-batch, --verify or --profile-only "
                     "is required")
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
        return 0
    # R303: refuse --r3-batch before root creation and before any decoder
    # binding or Model-F load while --execution-authorized is false.
    if args.r3_batch and not args.execution_authorized:
        print("refusing --r3-batch: %s (pass --execution-authorized only "
              "under a separate explicit authorization)"
              % r3.AUTHORIZATION, file=sys.stderr)
        return 2
    if args.out_root is None:
        parser.error("%s requires --out-root" % selected[0])
    if args.verify:
        return 0 if verify_root(args.out_root) else 1
    from comparison_bench.formal_ir import (  # lazy production adapter
        v35_algorithm_development as v35)
    summary = run_r3_batch(
        args.out_root, args.model_f_root,
        decode_fn=v35.decode_row_layered_fftqspa,
        syndrome_fn=v35.syndrome_of_gf32)
    print("D10_R3 terminal=%s calls=%d setup=%d"
          % (summary["terminal"], summary["scientific_calls"],
             summary["setup_calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
