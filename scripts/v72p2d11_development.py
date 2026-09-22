"""D11 canonical forward APP integration runner — readiness paths.

Frozen command (design §8; requires a separate explicit authorization):

    .venv/bin/python scripts/v72p2d11_development.py --forward-batch \\
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \\
      --out-root workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64

Paths:

- ``--profile-only``: build the 36 frozen D11 graphs (24 L1 + 12 shared
  L2) with the real builders, print A1–A6 admission, plan identities
  (360/width, conditional 720), zero decoder calls and future-root
  absence to stdout; no decoder, no root;
- ``--forward-batch``: n128 first (72 cells, 360 scientific calls), n256
  (360) if and only if n128 is ``D11_FORWARD_SIGNAL`` (≤720 scientific
  calls, ≤64 setup units); refuses unless ``--execution-authorized`` is
  passed (default false; refusal happens before any root creation,
  decoder binding or Model-F load) and requires the injected production
  decoder adapter, which only this runner constructs;
- ``--verify``: read-only recomputation of a completed six-file root with
  zero skip, zero decoder calls; exits FAIL on any partial or
  engineering-blocked root.

One fresh root per run; refuses overwrite, protected roots and partial
runs (single process, no retry, no resume, no seed search, no adaptive
stop). D7-H is out of scope: only the forward L1→L2 leg is ever invoked.
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
    v72p2d11_forward_app as d11)

_R2_RUNNER_PATH = ROOT / "scripts" / "v72p2d10_mixed_degree_l1_development.py"


def _load_r2_runner():
    # Reuse: prior-chain, block, CSV/JSON and parse helpers live in the R2
    # runner; import them read-only instead of copying (R2 files untouched).
    spec = importlib.util.spec_from_file_location(
        "v72p2d10_r2_runner_reuse_d11", str(_R2_RUNNER_PATH))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["v72p2d10_r2_runner_reuse_d11"] = module
    spec.loader.exec_module(module)
    return module


_r2run = _load_r2_runner()

EVIDENCE_FILES = d11.EVIDENCE_FILES
FROZEN_COMMAND = d11.FROZEN_COMMAND

DECODER_RECORD_COLUMNS = (
    "call_idx", "width", "branch", "layer", "graph_seed", "block_seed",
    "batch_id", "exact", "syndrome_ok", "iterations", "belief_provenance",
    "transfer_invoked", "transfer_provenance", "crash", "error", "wall_s")
GRAPH_RECORD_COLUMNS = _r2run.GRAPH_RECORD_COLUMNS
ARM_SUMMARY_COLUMNS = (
    "width", "branch", "layer", "scope", "graph_seed", "blocks",
    "exact_count", "syndrome_valid_count")


def _peak_rss_bytes():
    # Linux ru_maxrss is KiB; single-process aggregate = this process.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def prepare_paired_blocks(p_b, p_f, p1, width, block_seeds, sample_fn=None):
    """Sample each paired block once for both layers (shared block object).

    Same ``(bob, u1, u2)`` block feeds the L1 source arm and the shared L2
    target/oracle; the L1 prior line mirrors the accepted R2 runner
    (``_floor_renorm(p1[:, bob].T, DECODER_FLOOR)``). The L2 prior is built
    per cell by the canonical transfer/oracle helpers, never here.
    """
    sample_fn = sample_fn or d11.d5.sample_matched_block
    floor_fn = d11.d5._floor_renorm
    blocks = {}
    for block_seed in block_seeds:
        block = sample_fn(p_b, p_f, int(width), int(block_seed))
        bob = np.asarray(block["bob"], dtype=np.int64)
        prior = floor_fn(p1[:, bob].T, d11.d5.DECODER_FLOOR)
        blocks[int(block_seed)] = {
            "bob": bob,
            "u1": np.asarray(block["u1"], dtype=np.int64),
            "u2": np.asarray(block["u2"], dtype=np.int64),
            "prior": np.asarray(prior, dtype=np.float64),
        }
    return blocks


def _arm_rows(records):
    rows = []
    for width in d11.D11_WIDTHS:
        for branch, layer in ((d11.CONTROL, "L1"), (d11.CONTROL, "L2"),
                              (d11.MIX, "L1"), (d11.MIX, "L2"),
                              (d11.ORACLE, "L2")):
            for graph_seed in d11.L1_GRAPH_SEEDS[width]:
                scoped = [rec for rec in records
                          if int(rec["width"]) == width
                          and rec["branch"] == branch
                          and rec["layer"] == layer
                          and int(rec["graph_seed"]) == graph_seed]
                rows.append({
                    "width": width, "branch": branch, "layer": layer,
                    "scope": "graph", "graph_seed": graph_seed,
                    "blocks": len(scoped),
                    "exact_count": sum(1 for rec in scoped if rec["exact"]),
                    "syndrome_valid_count":
                        sum(1 for rec in scoped if rec["syndrome_ok"])})
            pooled = [rec for rec in records
                      if int(rec["width"]) == width
                      and rec["branch"] == branch
                      and rec["layer"] == layer]
            rows.append({
                "width": width, "branch": branch, "layer": layer,
                "scope": "pooled", "graph_seed": "POOLED",
                "blocks": len(pooled),
                "exact_count": sum(1 for rec in pooled if rec["exact"]),
                "syndrome_valid_count":
                    sum(1 for rec in pooled if rec["syndrome_ok"])})
    return rows


def _degree_table_meta():
    return {
        "L1:%s:%d" % (arm, width): {
            "n": cell["n"], "m": cell["m"],
            "var_counts": cell["var_counts"],
            "check_counts": cell["check_counts"]}
        for (arm, width), cell in sorted(d11.r3.DEGREE_TABLE.items())} | {
        "L2:%d" % width: {
            "n": cell["n"], "m": cell["m"],
            "var_counts": cell["var_counts"],
            "check_counts": cell["check_counts"]}
        for width, cell in sorted(d11.L2_DEGREE_TABLE.items())}


def _budget_meta():
    return {
        "scientific_calls": d11.SCIENTIFIC_CALL_CEILING,
        "setup_calls": d11.SETUP_CALL_CEILING,
        "wall_s": d11.WALL_BUDGET_S,
        "per_call_s": d11.PER_CALL_BUDGET_S,
        "rss_bytes": d11.RSS_BUDGET_BYTES,
        "processes": 1,
        "retry": False, "resume": False,
        "seed_search": False, "adaptive_stop": False,
    }


# --------------------------------------------------------------------------- #
# batch (conditional n128 -> gate -> n256)
# --------------------------------------------------------------------------- #
def run_forward_batch(out_root, model_f_root, decode_fn, *,
                      build_l1_fn=None, build_l2_fn=None, load_prior_fn=None,
                      sample_fn=None, now_fn=None, rss_fn=None):
    """Execute and persist one authorized D11 batch (injected decoder).

    ``decode_fn(h, prior, syndrome, layer=None)`` is explicitly injected
    by the caller (the ``--forward-batch`` entrypoint constructs the
    production adapter). n256 is dispatched iff n128 classifies
    ``D11_FORWARD_SIGNAL``. Forward leg only; D7-H is never invoked.
    """
    resolved = d11.refuse_out_root(out_root)
    plan = d11.build_full_plan()
    build_l1_fn = build_l1_fn or d11.build_l1_graph
    build_l2_fn = build_l2_fn or d11.build_l2_graph
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
    p2 = d11.d5.conditionalize_f_to_p2(p_f)
    setup_calls = 2  # Model-F load + plan build
    log("prior chain loaded from %s" % model_f_root)
    blocks = {}
    for width in d11.D11_WIDTHS:
        blocks[width] = prepare_paired_blocks(
            p_b, p_f, p1, width, d11.L1_BLOCK_SEEDS[width],
            sample_fn=sample_fn)
        setup_calls += len(d11.L1_BLOCK_SEEDS[width])
        log("sampled paired blocks width=%d count=%d"
            % (width, len(d11.L1_BLOCK_SEEDS[width])))
    graphs_l1, graphs_l2 = {}, {}
    graph_rows = []
    for width in d11.D11_WIDTHS:
        for arm in (d11.CONTROL_ARM, d11.MIX_ARM):
            for graph_seed in d11.L1_GRAPH_SEEDS[width]:
                start = float(now())
                graph = build_l1_fn(arm, width, graph_seed)
                graph_rows.append(
                    _r2run._graph_row(graph, float(now()) - start))
                graphs_l1[(arm, width, graph_seed)] = graph
                setup_calls += 1
        for graph_seed in d11.L2_GRAPH_SEEDS[width]:
            start = float(now())
            graph = build_l2_fn(width, graph_seed)
            graph_rows.append(
                _r2run._graph_row(graph, float(now()) - start))
            graphs_l2[(width, graph_seed)] = graph
            setup_calls += 1
    admitted = sum(1 for row in graph_rows if row["admitted"])
    log("built %d graphs admitted=%d" % (len(graph_rows), admitted))
    if setup_calls > d11.SETUP_CALL_CEILING:
        raise RuntimeError("setup unit count %d exceeds frozen ceiling %d"
                           % (setup_calls, d11.SETUP_CALL_CEILING))

    width_results = []
    records: list[dict] = []
    priors = (p1, p2)
    n128 = d11.execute_width(128, plan, graphs_l1, graphs_l2, priors,
                             blocks[128], decode_fn, now=now, rss_fn=rss_fn)
    records.extend(n128["records"])
    width_results.append({k: n128[k] for k in
                          ("width", "mix_joint", "ctrl_joint", "mix_l1",
                           "ctrl_l1", "oracle_exact", "transfers_blocked",
                           "all_check_updated", "paired", "classification",
                           "engineering_reason", "decoder_calls")})
    log("n128 classification=%s JM=%d JC=%d O=%d"
        % (n128["classification"], sum(n128["mix_joint"]),
           sum(n128["ctrl_joint"]), n128["oracle_exact"]))
    n256 = None
    if d11.n256_permitted(n128["classification"]):
        n256 = d11.execute_width(256, plan, graphs_l1, graphs_l2, priors,
                                 blocks[256], decode_fn, now=now,
                                 rss_fn=rss_fn)
        records.extend(n256["records"])
        width_results.append({k: n256[k] for k in
                              ("width", "mix_joint", "ctrl_joint", "mix_l1",
                               "ctrl_l1", "oracle_exact", "transfers_blocked",
                               "all_check_updated", "paired",
                               "classification", "engineering_reason",
                               "decoder_calls")})
        log("n256 classification=%s JM=%d JC=%d O=%d"
            % (n256["classification"], sum(n256["mix_joint"]),
               sum(n256["ctrl_joint"]), n256["oracle_exact"]))
    else:
        log("n256 not dispatched (n128=%s)" % n128["classification"])
    terminal = d11.route_terminal(
        n128["classification"],
        n256["classification"] if n256 is not None else None)
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn())
    scientific_calls = sum(w["decoder_calls"] for w in width_results)
    budget_violations = []
    if scientific_calls > d11.SCIENTIFIC_CALL_CEILING:
        budget_violations.append("scientific calls exceed ceiling")
    if wall_s > d11.WALL_BUDGET_S:
        budget_violations.append("wall budget exceeded")
    if peak_rss >= d11.RSS_BUDGET_BYTES:
        budget_violations.append("RSS budget exceeded")
    log("dispatched width_results=%s terminal=%s"
        % ([w["classification"] for w in width_results], terminal))

    resolved.mkdir(parents=True)
    _r2run._write_json(resolved / "manifest.json", {
        "schema": "v72p2d11_forward_app_manifest_v1",
        "change_id": d11.CHANGE_ID, "cycle": d11.CYCLE_ID,
        "claim_ceiling": d11.CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "model_f_root": str(model_f_root), "out_root": str(resolved),
        "forward_only": True, "d7h": "out_of_scope",
        "batch_id": d11.D11_BATCH_ID,
        "field": {"q": 32, "poly": 37,
                  "factory": "GF2mField.create(32)"},
        "branches": list(d11.BRANCHES),
        "l1_arms": {"CONTROL": d11.CONTROL_ARM, "MIX": d11.MIX_ARM},
        "shared_l2_arm": d11.SHARED_L2_ARM,
        "widths": list(d11.D11_WIDTHS),
        "degree_table": _degree_table_meta(),
        "l1_graph_seeds": {str(w): list(d11.L1_GRAPH_SEEDS[w])
                           for w in d11.D11_WIDTHS},
        "l1_block_seeds": {str(w): list(d11.L1_BLOCK_SEEDS[w])
                           for w in d11.D11_WIDTHS},
        "l2_graph_seeds": {str(w): list(d11.L2_GRAPH_SEEDS[w])
                           for w in d11.D11_WIDTHS},
        "replay_gate": {str(w): {"mix": list(d11.REPLAY_MIX[w]),
                                 "control": [0] * 6}
                        for w in d11.D11_WIDTHS},
        "coefficient_rule":
            "v10_seed(d10:coeff:{width}:{graph_seed}) -> default_rng -> "
            "integers(1,32) per edge in sorted (variable, check) order",
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": d11.DECODER_MAX_ITER,
                    "damping_alpha": d11.DAMPING_ALPHA,
                    "warm_beliefs": None, "schedule": "cold row-layered"},
        "matrix": {"planned_calls": len(plan),
                   "shape": "72 cells x 5 calls per width",
                   "call_order": ("n128 first, n256 iff "
                                  "D11_FORWARD_SIGNAL(n128); within a width "
                                  "graph seed asc -> block seed asc -> "
                                  "CONTROL L1/L2, MIX L1/L2, ORACLE L2"),
                   "progress_rule": "n128 -> n256 only on "
                                    "D11_FORWARD_SIGNAL"},
        "budgets": _budget_meta(),
        "setup_calls": setup_calls,
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": d11.AUTHORIZATION,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    _r2run._write_csv(resolved / "decoder_records.csv",
                      DECODER_RECORD_COLUMNS, records)
    _r2run._write_csv(resolved / "graph_records.csv", GRAPH_RECORD_COLUMNS,
                      graph_rows)
    _r2run._write_csv(resolved / "arm_summary.csv", ARM_SUMMARY_COLUMNS,
                      _arm_rows(records))
    summary = {
        "schema": "v72p2d11_forward_app_summary_v1",
        "change_id": d11.CHANGE_ID, "cycle": d11.CYCLE_ID,
        "claim_ceiling": d11.CLAIM_CEILING,
        "terminal": terminal,
        "widths_dispatched": [w["width"] for w in width_results],
        "width_classifications":
            {str(w["width"]): w["classification"] for w in width_results},
        "width_results": width_results,
        "scientific_calls": scientific_calls,
        "planned_calls": len(plan),
        "setup_calls": setup_calls,
        "exact_count": sum(1 for rec in records if rec["exact"]),
        "syndrome_valid_count": sum(1 for rec in records
                                    if rec["syndrome_ok"]),
        "call_idx_first": 0 if records else None,
        "call_idx_last": len(records) - 1 if records else None,
        "wall_s": wall_s, "peak_rss_bytes": peak_rss,
        "budget_violations": budget_violations,
        "forward_only": True, "batch_id": d11.D11_BATCH_ID,
        "model_f_root": str(model_f_root),
        "out_root": str(resolved), "budgets": _budget_meta(),
    }
    _r2run._write_json(resolved / "summary.json", summary)
    log_lines.append(_r2run._log_line(
        "D11 terminal=%s calls=%d setup=%d wall_s=%.3f"
        % (terminal, scientific_calls, setup_calls, wall_s)))
    with open(resolved / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("".join(line + "\n" for line in log_lines))
    return summary


# --------------------------------------------------------------------------- #
# verify (read-only; zero decoder calls; zero skip; fail-closed)
# --------------------------------------------------------------------------- #
def verify_root(out_root, build_l1_fn=None, build_l2_fn=None):
    """Recompute a completed D11 root from its evidence; fail-closed."""
    root = Path(out_root)
    build_l1_fn = build_l1_fn or d11.build_l1_graph
    build_l2_fn = build_l2_fn or d11.build_l2_graph
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

    if manifest.get("batch_id") != d11.D11_BATCH_ID \
            or summary.get("batch_id") != d11.D11_BATCH_ID:
        violations.append("batch_id tag mismatch (non-D11 boundary)")

    plan = d11.build_full_plan()
    plan_by_key = {(e["width"], e["branch"], e["layer"], e["graph_seed"],
                    e["block_seed"]): e for e in plan}
    checked = agreements = 0
    records: list[dict] = []
    for index, row in enumerate(decoder_rows):
        key = (_r2run._as_int(row["width"]), row["branch"], row["layer"],
               _r2run._as_int(row["graph_seed"]),
               _r2run._as_int(row["block_seed"]))
        entry = plan_by_key.get(key)
        if entry is None:
            violations.append("decoder row %d not in frozen plan: %s"
                              % (index, key))
        elif int(entry["call_idx"]) != index:
            violations.append("decoder row %d call_idx %s != planned %d"
                              % (index, row["call_idx"], entry["call_idx"]))
        if row.get("batch_id") != d11.D11_BATCH_ID:
            violations.append("decoder row %d batch_id tag missing" % index)
        ok = True
        crash = _r2run._as_bool(row["crash"])
        exact = _r2run._as_bool(row["exact"])
        syndrome_ok = _r2run._as_bool(row["syndrome_ok"])
        iterations = _r2run._as_int(row["iterations"])
        wall = _r2run._as_float(row["wall_s"])
        if exact and not syndrome_ok:
            violations.append("decoder row %d exact without syndrome_ok "
                              "(metric isolation)" % index)
            ok = False
        if crash:
            if iterations != -1 or exact or syndrome_ok:
                violations.append("decoder row %d crash record inconsistent"
                                  % index)
                ok = False
        else:
            if row["branch"] == d11.ORACLE or (
                    row["layer"] == "L2"
                    and _r2run._cell(row.get("transfer_invoked")) == "True"):
                if not 0 <= iterations <= d11.DECODER_MAX_ITER:
                    violations.append("decoder row %d iterations out of "
                                      "range: %d" % (index, iterations))
                    ok = False
            if not str(row["belief_provenance"]).strip() \
                    and row["layer"] == "L1" and not crash:
                violations.append("decoder row %d L1 provenance missing"
                                  % index)
                ok = False
            if row["layer"] == "L2" and row["branch"] != d11.ORACLE:
                prov = str(row.get("transfer_provenance"))
                if _r2run._cell(row.get("transfer_invoked")) != "True" \
                        or prov != d11.check_updated_token():
                    violations.append("decoder row %d non-oracle transfer "
                                      "not CHECK_UPDATED (fail-closed)"
                                      % index)
                    ok = False
        if wall < 0.0 or wall > d11.PER_CALL_BUDGET_S:
            violations.append("decoder row %d per-call wall out of budget: %s"
                              % (index, row["wall_s"]))
            ok = False
        records.append({"call_idx": index, "width": key[0],
                        "branch": key[1], "layer": key[2],
                        "graph_seed": key[3], "block_seed": key[4],
                        "batch_id": row.get("batch_id"),
                        "exact": exact, "syndrome_ok": syndrome_ok,
                        "transfer_invoked": _r2run._as_bool(
                            row.get("transfer_invoked")),
                        "transfer_provenance": str(
                            row.get("transfer_provenance")),
                        "crash": crash, "wall_s": wall})
        checked += 1
        if ok:
            agreements += 1

    dispatched = []
    for record in records:
        if record["width"] not in dispatched:
            dispatched.append(record["width"])
    if dispatched != [w for w in d11.D11_WIDTHS if w in dispatched]:
        violations.append("dispatched width order invalid: %s" % dispatched)
    for width in dispatched:
        for entry in (e for e in plan if e["width"] == width):
            if entry["call_idx"] >= len(records):
                violations.append("planned call %d missing (zero-skip)"
                                  % entry["call_idx"])
    if 256 in dispatched and 128 not in dispatched:
        violations.append("n256 dispatched without n128")

    recomputed_arm_rows = _arm_rows(records)
    stored_arm_keys = {(row["width"], row["branch"], row["layer"],
                        row["scope"], row["graph_seed"]): row
                       for row in arm_rows}
    for row in recomputed_arm_rows:
        key = (str(row["width"]), row["branch"], row["layer"], row["scope"],
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
            tallies = d11.tallies_from_d11_records(records, width)
        except ValueError as exc:
            violations.append("width %d tallies not rebuildable: %s"
                              % (width, exc))
            continue
        if tallies.transfers_blocked:
            violations.append("width %d has blocked transfers (fail-closed)"
                              % width)
        replay_reason = d11.check_l1_replay(width, tallies.mix_l1,
                                            tallies.ctrl_l1)
        if replay_reason:
            violations.append("width %d replay gate fails: %s"
                              % (width, replay_reason))
        recomputed = d11.classify_d11(
            tallies, str(result.get("engineering_reason", "")))
        if recomputed != result["classification"]:
            violations.append("width %d classification stored=%s recomputed=%s"
                              % (width, result["classification"], recomputed))
        for field in ("mix_joint", "ctrl_joint", "mix_l1", "ctrl_l1"):
            if list(getattr(tallies, field)) != result.get(field):
                violations.append("width %d stored %s != recomputed"
                                  % (width, field))
        if tallies.oracle_exact != result.get("oracle_exact"):
            violations.append("width %d stored oracle != recomputed" % width)
        if result["classification"] == d11.ENGINEERING_BLOCKED:
            violations.append("width %d engineering-blocked (fail-closed)"
                              % width)
    if 256 in dispatched and n128_class != d11.FORWARD_SIGNAL:
        violations.append("n256 dispatched without D11_FORWARD_SIGNAL(n128)")
    if d11.route_terminal(
            width_results[0]["classification"] if width_results else "NONE",
            width_results[1]["classification"] if len(width_results) > 1
            else None) != summary.get("terminal"):
        violations.append("terminal stored=%r recomputed mismatch"
                          % (summary.get("terminal"),))
    if bool(summary.get("forward_only")) is not True \
            or bool(manifest.get("forward_only")) is not True:
        violations.append("forward_only flag not true")

    if len(decoder_rows) != int(summary.get("scientific_calls", -1)):
        violations.append("stored calls %d != summary %r"
                          % (len(decoder_rows),
                             summary.get("scientific_calls")))
    if len(decoder_rows) > d11.SCIENTIFIC_CALL_CEILING:
        violations.append("stored calls exceed scientific ceiling")
    if int(summary.get("setup_calls", -1)) > d11.SETUP_CALL_CEILING:
        violations.append("setup calls exceed frozen ceiling")
    if _r2run._as_float(summary.get("wall_s", -1.0)) > d11.WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if _r2run._as_int(summary.get("peak_rss_bytes", -1)) \
            >= d11.RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")

    l2_seeds = {s for seeds in d11.L2_GRAPH_SEEDS.values() for s in seeds}
    for row in graph_rows:
        arm, width = row["arm"], _r2run._as_int(row["width"])
        seed = _r2run._as_int(row["graph_seed"])
        if arm == d11.SHARED_L2_ARM:
            if seed not in l2_seeds:
                violations.append("L2 graph seed outside frozen set: %s"
                                  % (seed,))
                continue
            graph = build_l2_fn(width, seed)
        else:
            graph = build_l1_fn(arm, width, seed)
        key = (width, arm, seed)
        if graph["status"] != row["status"] \
                or bool(graph["admitted"]) != _r2run._as_bool(row["admitted"]) \
                or int(graph["E"]) != _r2run._as_int(row["E"]) \
                or str(graph["failure_reason"]) != row["failure_reason"]:
            violations.append("graph %s status/admission/E mismatch" % (key,))
            continue
        if str(row["status"]) != "ok" or not _r2run._as_bool(row["admitted"]):
            violations.append("graph %s not admitted (fail-closed)" % (key,))
            continue

    print("VERIFY checked_calls=%d agreements=%d violations=%d"
          % (checked, agreements, len(violations)))
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    ok = not violations
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return ok


# --------------------------------------------------------------------------- #
# CLI (D1104: --forward-batch requires explicit --execution-authorized)
# --------------------------------------------------------------------------- #
def build_parser():
    parser = argparse.ArgumentParser(
        description="D11 canonical forward APP integration runner")
    parser.add_argument("--forward-batch", action="store_true",
                        help="run the frozen conditional 360->720-call D11 "
                             "matrix (requires --execution-authorized from a "
                             "separate explicit authorization)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for "
                             "--forward-batch; default false "
                             "(fail-closed, no-write/no-bind)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--profile-only", action="store_true",
                        help="pre-decoder graph construction profile (no "
                             "decoder, no root)")
    parser.add_argument("--model-f-root", default=d11.MODEL_F_INPUT_ROOT,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    return parser


def profile_only():
    """D1109 profile helper: real builders, no decoder, no root."""
    return d11.profile_graphs()


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--forward-batch", args.forward_batch),
                                        ("--verify", args.verify),
                                        ("--profile-only",
                                         args.profile_only)) if flag]
    if len(selected) != 1:
        parser.error("exactly one of --forward-batch, --verify or "
                     "--profile-only is required")
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
        return 0
    # D1104: refuse --forward-batch before root creation and before any
    # decoder binding or Model-F load while --execution-authorized is false.
    if args.forward_batch and not args.execution_authorized:
        print("refusing --forward-batch: %s (pass --execution-authorized "
              "only under a separate explicit authorization)"
              % d11.AUTHORIZATION, file=sys.stderr)
        return 2
    if args.out_root is None:
        parser.error("%s requires --out-root" % selected[0])
    if args.verify:
        return 0 if verify_root(args.out_root) else 1
    from comparison_bench.formal_ir import (  # lazy production adapter
        v35_algorithm_development as v35)

    bound = d11.bind_row_layered_decoders()["TARGET"]

    def production_decode(h, prior, syndrome, layer=None):
        return bound(h, prior, syndrome)

    production_decode.target = v35.decode_row_layered_fftqspa
    summary = run_forward_batch(
        args.out_root, args.model_f_root, production_decode)
    print("D11 terminal=%s calls=%d setup=%d"
          % (summary["terminal"], summary["scientific_calls"],
             summary["setup_calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
