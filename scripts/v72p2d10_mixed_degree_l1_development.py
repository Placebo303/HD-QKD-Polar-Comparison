"""D10 mixed-degree L1 finite discriminator runner — L1-only paths.

Frozen command (design §8; requires a separate explicit authorization):

    .venv/bin/python scripts/v72p2d10_mixed_degree_l1_development.py --batch \
      --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
      --out-root workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34

Paths:

- ``--profile-only``: build the 18 frozen two-arm graphs with the real
  builders, print structural metrics (components, structural/GF32 rank,
  four-cycles, girth, A1–A6 admission, wall time), no decoder, no root;
- ``--batch``: the frozen 2 arms x 3 widths x 3 graphs x 8 paired blocks L1
  matrix (<=144 scientific calls, <=44 setup units); refuses unless
  ``--execution-authorized`` is passed (default false; refusal happens
  before any root creation and before any decoder binding) and requires the
  injected production decoder adapter, which only this runner constructs;
- ``--verify``: read-only recomputation of a completed six-file root with
  zero skip, zero decoder calls; exits FAIL on any partial or
  engineering-blocked root.

One fresh root per run; refuses overwrite, protected roots and partial/adapted
runs (single process, no retry, no resume, no seed search, no adaptive stop).
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

from comparison_bench.formal_ir import (  # noqa: E402
    v72p2d10_mixed_degree_l1 as d10)

EVIDENCE_FILES = d10.EVIDENCE_FILES
FROZEN_COMMAND = d10.FROZEN_COMMAND

L1_RECORD_COLUMNS = (
    "call_idx", "width", "arm", "graph_seed", "block_seed", "exact",
    "syndrome_ok", "iterations", "status", "residual_syndrome_weight",
    "belief_provenance", "prior_mass_on_truth", "wall_s", "crash", "error")
GRAPH_RECORD_COLUMNS = (
    "width", "arm", "graph_seed", "status", "admitted", "n", "m", "E",
    "variable_degree_histogram", "check_degree_histogram", "var_sockets",
    "check_sockets", "duplicate_edges", "empty_checks", "min_check_degree",
    "rank", "structural_rank", "gf32_rank", "connected_components",
    "largest_component_fraction",
    "isolated_variables", "degree2_N2", "degree2_forest_bound",
    "degree2_cycle_rank_lower_bound", "degree2_forest_feasible",
    "four_cycles", "four_cycle_variable_incidence_max", "girth",
    "girth_reason", "gates", "admission", "failure_reason",
    "construction_wall_s")
ARM_SUMMARY_COLUMNS = (
    "width", "arm", "scope", "graph_seed", "blocks", "exact_count",
    "syndrome_valid_count")


def _peak_rss_bytes():
    # Linux ru_maxrss is KiB; single-process aggregate = this process.
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    return value if isinstance(value, str) else str(value)


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


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


def _as_int(value):
    return int(float(value))


def _as_float(value):
    return float(value)


def _as_bool(value):
    return str(value).strip() == "True"


def _log_line(message):
    return "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), message)


# --------------------------------------------------------------------------- #
# prior chain and blocks (design §4.3/§4.4; runner-side, no decoder)
# --------------------------------------------------------------------------- #
def load_prior_chain(model_f_root):
    """Accepted CAL-only Model-F chain: counts/P(B) -> E2 P_F -> P1."""
    path = Path(model_f_root) / "model_f_input.npz"
    npz = np.load(path)
    counts0 = np.asarray(npz["counts_ab"], dtype=np.float64)
    pb0 = np.asarray(npz["p_b"], dtype=np.float64)
    pb0 = pb0 / pb0.sum()
    pb, pf = d10.d5.prepare_model_f_prior_candidate(counts0, pb0)
    p1 = np.asarray(d10.d5.marginalize_f_to_p1(pf), dtype=np.float64)
    return pb, pf, p1


def prepare_blocks(p_b, p_f, p1, width, block_seeds, sample_fn=None,
                   floor_fn=None):
    """Sample each matched block once and prepare the frozen L1 prior line.

    Same block object is used by both arms and all graphs at the width:
    ``priors = _floor_renorm(p1[:, block["bob"]].T, DECODER_FLOOR)``.
    """
    sample_fn = sample_fn or d10.d5.sample_matched_block
    floor_fn = floor_fn or d10.d5._floor_renorm
    blocks = {}
    for block_seed in block_seeds:
        block = sample_fn(p_b, p_f, int(width), int(block_seed))
        bob = np.asarray(block["bob"], dtype=np.int64)
        prior = floor_fn(p1[:, bob].T, d10.d5.DECODER_FLOOR)
        blocks[int(block_seed)] = {
            "bob": bob,
            "u1": np.asarray(block["u1"], dtype=np.int64),
            "prior": np.asarray(prior, dtype=np.float64),
        }
    return blocks


# --------------------------------------------------------------------------- #
# evidence rows
# --------------------------------------------------------------------------- #
def _graph_row(graph, construction_wall_s):
    structure = graph.get("structure")
    row = {
        "width": graph["width"], "arm": graph["arm"],
        "graph_seed": graph["graph_seed"], "status": graph["status"],
        "admitted": bool(graph["admitted"]), "n": graph["n"],
        "m": graph["m"], "E": graph["E"],
        "failure_reason": graph["failure_reason"],
        "construction_wall_s": round(float(construction_wall_s), 6),
    }
    if structure:
        row.update({
            "variable_degree_histogram":
                json.dumps(structure["variable_degree_histogram"],
                           sort_keys=True),
            "check_degree_histogram":
                json.dumps(structure["check_degree_histogram"],
                           sort_keys=True),
            "var_sockets": structure["var_sockets"],
            "check_sockets": structure["check_sockets"],
            "duplicate_edges": structure["duplicate_edges"],
            "empty_checks": structure["empty_checks"],
            "min_check_degree": structure["min_check_degree"],
            "rank": structure["rank"],
            "structural_rank": structure["structural_rank"],
            "gf32_rank": structure["gf32_rank"],
            "connected_components": structure["connected_components"],
            "largest_component_fraction":
                structure["largest_component_fraction"],
            "isolated_variables": structure["isolated_variables"],
            "degree2_N2": structure["degree2"]["N2"],
            "degree2_forest_bound": structure["degree2"]["forest_bound"],
            "degree2_cycle_rank_lower_bound":
                structure["degree2"]["cycle_rank_lower_bound"],
            "degree2_forest_feasible":
                structure["degree2"]["is_forest_feasible"],
            "four_cycles": structure["four_cycles"],
            "four_cycle_variable_incidence_max":
                structure["four_cycle_variable_incidence_max"],
            "girth": structure["girth"],
            "girth_reason": structure["girth_reason"],
            "gates": json.dumps(structure["gates"], sort_keys=True),
            "admission": json.dumps(structure["admission"], sort_keys=True),
        })
    return row


def _l1_rows(records):
    return [dict(record) for record in records]


def _arm_rows(records):
    rows = []
    for width in d10.WIDTHS:
        for arm in d10.ARMS:
            for graph_seed in d10.GRAPH_SEEDS[width]:
                scoped = [r for r in records
                          if int(r["width"]) == width and r["arm"] == arm
                          and int(r["graph_seed"]) == graph_seed]
                rows.append({
                    "width": width, "arm": arm, "scope": "graph",
                    "graph_seed": graph_seed, "blocks": len(scoped),
                    "exact_count": sum(1 for r in scoped if r["exact"]),
                    "syndrome_valid_count":
                        sum(1 for r in scoped if r["syndrome_ok"])})
            pooled = [r for r in records
                      if int(r["width"]) == width and r["arm"] == arm]
            rows.append({
                "width": width, "arm": arm, "scope": "pooled",
                "graph_seed": "POOLED", "blocks": len(pooled),
                "exact_count": sum(1 for r in pooled if r["exact"]),
                "syndrome_valid_count":
                    sum(1 for r in pooled if r["syndrome_ok"])})
    return rows


def _degree_table_meta():
    table = {}
    for (arm, width), cell in sorted(d10.DEGREE_TABLE.items()):
        table["%s:%d" % (arm, width)] = {
            "n": cell["n"], "m": cell["m"],
            "var_counts": cell["var_counts"],
            "check_counts": cell["check_counts"]}
    return table


def _budget_meta():
    return {
        "scientific_l1_calls": d10.SCIENTIFIC_CALL_CEILING,
        "setup_calls": d10.SETUP_CALL_CEILING,
        "wall_s": d10.WALL_BUDGET_S,
        "per_call_s": d10.PER_CALL_BUDGET_S,
        "rss_bytes": d10.RSS_BUDGET_BYTES,
        "processes": 1,
        "retry": False, "resume": False,
        "seed_search": False, "adaptive_stop": False,
    }


# --------------------------------------------------------------------------- #
# batch
# --------------------------------------------------------------------------- #
def run_l1_batch(out_root, model_f_root, decode_fn, syndrome_fn, *,
                 plan=None, build_graph_fn=None, load_prior_fn=None,
                 sample_fn=None, floor_fn=None, now_fn=None, rss_fn=None):
    """Execute and persist one authorized D10 L1 batch (injected decoder).

    ``decode_fn``/``syndrome_fn`` are explicit injections supplied by the
    caller (the ``--batch`` entrypoint constructs the production adapter).
    """
    resolved = d10.refuse_out_root(out_root)
    plan = d10.build_call_plan() if plan is None else list(plan)
    build_graph_fn = build_graph_fn or d10.build_graph
    load_prior_fn = load_prior_fn or load_prior_chain
    now = now_fn or time.monotonic
    rss_fn = rss_fn or _peak_rss_bytes
    t0 = float(now())
    log_lines = []

    def log(message):
        line = _log_line(message)
        log_lines.append(line)
        print(line)

    p_b, p_f, p1 = load_prior_fn(model_f_root)
    setup_calls = d10.SETUP_FIXED_UNITS
    log("prior chain loaded from %s" % model_f_root)
    blocks = {}
    for width in d10.WIDTHS:
        blocks[width] = prepare_blocks(
            p_b, p_f, p1, width, d10.BLOCK_SEEDS[width], sample_fn=sample_fn,
            floor_fn=floor_fn)
        setup_calls += len(d10.BLOCK_SEEDS[width])
        log("sampled matched blocks width=%d count=%d"
            % (width, len(d10.BLOCK_SEEDS[width])))
    graphs = {}
    graph_rows = []
    for width in d10.WIDTHS:
        for arm in d10.ARMS:
            for graph_seed in d10.GRAPH_SEEDS[width]:
                start = float(now())
                graph = build_graph_fn(arm, width, graph_seed)
                graph_rows.append(_graph_row(graph, float(now()) - start))
                graphs[(arm, width, graph_seed)] = graph
                setup_calls += 1
    admitted = sum(1 for row in graph_rows if row["admitted"])
    log("built %d graphs admitted=%d" % (len(graph_rows), admitted))
    if setup_calls != d10.SETUP_CALL_CEILING:
        raise RuntimeError("setup unit count %d != frozen %d"
                           % (setup_calls, d10.SETUP_CALL_CEILING))

    outcome = d10.execute_plan(plan, graphs, blocks, decode_fn, syndrome_fn,
                               now=now, rss_fn=rss_fn)
    records = outcome["records"]
    width_results = outcome["width_results"]
    terminal = outcome["terminal"]
    wall_s = float(now()) - t0
    peak_rss = int(rss_fn())
    budget_violations = []
    if len(records) > d10.SCIENTIFIC_CALL_CEILING:
        budget_violations.append("scientific calls exceed ceiling")
    if wall_s > d10.WALL_BUDGET_S:
        budget_violations.append("wall budget exceeded")
    if peak_rss >= d10.RSS_BUDGET_BYTES:
        budget_violations.append("RSS budget exceeded")
    log("dispatched width_results=%s terminal=%s"
        % ([r["classification"] for r in width_results], terminal))

    resolved.mkdir(parents=True)
    _write_json(resolved / "manifest.json", {
        "schema": "v72p2d10_mixed_degree_l1_manifest_v1",
        "change_id": d10.CHANGE_ID, "cycle": d10.CYCLE_ID,
        "track": d10.TRACK, "claim_ceiling": d10.CLAIM_CEILING,
        "command": FROZEN_COMMAND,
        "model_f_root": str(model_f_root), "out_root": str(resolved),
        "l1_only": True,
        "field": {"q": d10.Q, "poly": d10.POLY,
                  "factory": "GF2mField.create(32)"},
        "arms": list(d10.ARMS), "arm_roles": dict(d10.ARM_ROLE),
        "widths": list(d10.WIDTHS),
        "degree_table": _degree_table_meta(),
        "graph_seeds": {str(w): list(d10.GRAPH_SEEDS[w])
                        for w in d10.WIDTHS},
        "block_seeds": {str(w): list(d10.BLOCK_SEEDS[w])
                        for w in d10.WIDTHS},
        "coefficient_rule":
            "v10_seed(d10:coeff:{width}:{graph_seed}) -> default_rng -> "
            "integers(1,32) per edge in sorted (variable, check) order",
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": d10.DECODER_MAX_ITER,
                    "damping_alpha": d10.DAMPING_ALPHA,
                    "warm_beliefs": None, "schedule": "cold row-layered"},
        "matrix": {"planned_calls": len(plan),
                   "shape": "2 arms x 3 widths x 3 graphs x 8 blocks",
                   "call_order": ("width -> control then candidate -> graph "
                                  "seed asc -> block seed asc"),
                   "progress_rule": "n64 -> n128 -> n256 only on POSITIVE"},
        "budgets": _budget_meta(),
        "setup_calls": setup_calls,
        "evidence_files": list(EVIDENCE_FILES),
        "authorization": d10.AUTHORIZATION,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    _write_csv(resolved / "l1_records.csv", L1_RECORD_COLUMNS,
               _l1_rows(records))
    _write_csv(resolved / "graph_records.csv", GRAPH_RECORD_COLUMNS,
               graph_rows)
    _write_csv(resolved / "arm_summary.csv", ARM_SUMMARY_COLUMNS,
               _arm_rows(records))
    summary = {
        "schema": "v72p2d10_mixed_degree_l1_summary_v1",
        "change_id": d10.CHANGE_ID, "cycle": d10.CYCLE_ID,
        "track": d10.TRACK, "claim_ceiling": d10.CLAIM_CEILING,
        "terminal": terminal, "terminal_reason": outcome["stop_reason"],
        "widths_dispatched": [r["width"] for r in width_results],
        "width_classifications":
            {str(r["width"]): r["classification"] for r in width_results},
        "width_results": width_results,
        "scientific_l1_calls": len(records),
        "planned_l1_calls": len(plan),
        "setup_calls": setup_calls,
        "exact_count": sum(1 for r in records if r["exact"]),
        "syndrome_valid_count": sum(1 for r in records
                                    if r["syndrome_ok"]),
        "call_idx_first": 0 if records else None,
        "call_idx_last": len(records) - 1 if records else None,
        "wall_s": wall_s, "peak_rss_bytes": peak_rss,
        "budget_violations": budget_violations,
        "budget_stop": outcome["width_results"][-1]["engineering_reason"]
        if width_results
        and width_results[-1]["classification"] == d10.ENGINEERING_BLOCKED
        else "",
        "l1_only": True, "model_f_root": str(model_f_root),
        "out_root": str(resolved), "budgets": _budget_meta(),
    }
    _write_json(resolved / "summary.json", summary)
    log_lines.append(_log_line(
        "D10_L1 terminal=%s calls=%d setup=%d wall_s=%.3f"
        % (terminal, len(records), setup_calls, wall_s)))
    with open(resolved / "command_log.txt", "w", encoding="utf-8") as fh:
        fh.write("".join(line + "\n" for line in log_lines))
    return summary


# --------------------------------------------------------------------------- #
# verify (read-only; zero decoder calls; zero skip)
# --------------------------------------------------------------------------- #
def verify_root(out_root, build_graph_fn=None):
    """Recompute a completed root from its evidence; no decoder, zero skip."""
    root = Path(out_root)
    build_graph_fn = build_graph_fn or d10.build_graph
    violations = []
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
    l1_rows = _read_csv(root / "l1_records.csv")
    arm_rows = _read_csv(root / "arm_summary.csv")

    plan = d10.build_call_plan()
    plan_by_key = {(e["width"], e["arm"], e["graph_seed"], e["block_seed"]): e
                   for e in plan}
    checked = 0
    agreements = 0
    skipped = 0
    records = []
    for index, row in enumerate(l1_rows):
        key = (_as_int(row["width"]), row["arm"], _as_int(row["graph_seed"]),
               _as_int(row["block_seed"]))
        entry = plan_by_key.get(key)
        if entry is None:
            violations.append("l1 row %d not in frozen plan: %s"
                              % (index, key))
        elif int(entry["call_idx"]) != index:
            violations.append("l1 row %d call_idx %s != planned %d"
                              % (index, row["call_idx"],
                                 entry["call_idx"]))
        ok = True
        crash = _as_bool(row["crash"])
        exact = _as_bool(row["exact"])
        syndrome_ok = _as_bool(row["syndrome_ok"])
        iterations = _as_int(row["iterations"])
        residual = _as_int(row["residual_syndrome_weight"])
        wall = _as_float(row["wall_s"])
        prior_mass = _as_float(row["prior_mass_on_truth"])
        if exact and not syndrome_ok:
            violations.append("l1 row %d exact without syndrome_ok" % index)
            ok = False
        if crash:
            if iterations != -1 or residual != -1 or exact or syndrome_ok:
                violations.append("l1 row %d crash record inconsistent"
                                  % index)
                ok = False
        else:
            if not 0 <= iterations <= d10.DECODER_MAX_ITER:
                violations.append("l1 row %d iterations out of range: %d"
                                  % (index, iterations))
                ok = False
            if residual < 0:
                violations.append("l1 row %d residual syndrome weight missing"
                                  % index)
                ok = False
            if not str(row["belief_provenance"]).strip():
                violations.append("l1 row %d provenance missing" % index)
                ok = False
        if not 0.0 <= prior_mass <= 1.0:
            violations.append("l1 row %d prior mass out of range" % index)
            ok = False
        if not str(row["status"]).strip():
            violations.append("l1 row %d empty status" % index)
            ok = False
        if wall < 0.0 or wall > d10.PER_CALL_BUDGET_S:
            violations.append("l1 row %d per-call wall out of budget: %s"
                              % (index, row["wall_s"]))
            ok = False
        records.append({"call_idx": index, "width": key[0], "arm": key[1],
                        "graph_seed": key[2], "block_seed": key[3],
                        "exact": exact, "syndrome_ok": syndrome_ok,
                        "crash": crash, "wall_s": wall})
        checked += 1
        if ok:
            agreements += 1

    dispatched = []
    for record in records:
        if record["width"] not in dispatched:
            dispatched.append(record["width"])
    if dispatched != [w for w in d10.WIDTHS if w in dispatched]:
        violations.append("dispatched width order invalid: %s" % dispatched)
    for width in dispatched:
        for entry in (e for e in plan if e["width"] == width):
            if not any(r["call_idx"] == entry["call_idx"] for r in records):
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
            if _as_int(stored[column]) != int(row[column]):
                violations.append("arm_summary %s %s stored=%s recomputed=%d"
                                  % (key, column, stored[column],
                                     int(row[column])))

    width_results = summary.get("width_results", [])
    for result in width_results:
        width = int(result["width"])
        mix = d10._width_counts(records, width, d10.ARMS[1])
        dv3 = d10._width_counts(records, width, d10.ARMS[0])
        reason = str(result.get("engineering_reason", ""))
        recomputed = d10.classify_width(mix, dv3, reason)
        if recomputed != result["classification"]:
            violations.append("width %d classification stored=%s recomputed=%s"
                              % (width, result["classification"], recomputed))
        if mix != result.get("mix_counts") or dv3 != result.get("dv3_counts"):
            violations.append("width %d stored counts != recomputed" % width)
        # R207 fail-closed: an engineering-blocked width fails the root.
        if result["classification"] == d10.ENGINEERING_BLOCKED:
            violations.append("width %d engineering-blocked (fail-closed)"
                              % width)
    if d10.route_terminal(width_results, d10.WIDTHS) != summary.get("terminal"):
        violations.append("terminal stored=%r recomputed=%r"
                          % (summary.get("terminal"),
                             d10.route_terminal(width_results, d10.WIDTHS)))
    if bool(summary.get("l1_only")) is not True \
            or bool(manifest.get("l1_only")) is not True:
        violations.append("l1_only flag not true")

    if len(l1_rows) != int(summary.get("scientific_l1_calls", -1)):
        violations.append("stored calls %d != summary %r"
                          % (len(l1_rows), summary.get("scientific_l1_calls")))
    if len(l1_rows) > d10.SCIENTIFIC_CALL_CEILING:
        violations.append("stored calls exceed scientific ceiling")
    if not 0 <= int(summary.get("setup_calls", -1)) \
            <= d10.SETUP_CALL_CEILING:
        violations.append("setup calls outside budget: %r"
                          % summary.get("setup_calls"))
    if _as_float(summary.get("wall_s", -1.0)) > d10.WALL_BUDGET_S:
        violations.append("wall budget exceeded")
    if _as_int(summary.get("peak_rss_bytes", -1)) >= d10.RSS_BUDGET_BYTES:
        violations.append("RSS budget exceeded")
    max_call_wall = max((_as_float(r["wall_s"]) for r in l1_rows),
                        default=0.0)
    if max_call_wall > d10.PER_CALL_BUDGET_S:
        violations.append("per-call wall exceeds budget: %s" % max_call_wall)

    for row in graph_rows:
        graph = build_graph_fn(row["arm"], _as_int(row["width"]),
                               _as_int(row["graph_seed"]))
        key = (row["width"], row["arm"], row["graph_seed"])
        if graph["status"] != row["status"] \
                or bool(graph["admitted"]) != _as_bool(row["admitted"]) \
                or int(graph["E"]) != _as_int(row["E"]) \
                or str(graph["failure_reason"]) != row["failure_reason"]:
            violations.append("graph %s status/admission/E mismatch" % (key,))
            continue
        # R207 fail-closed: any partial or engineering-blocked graph fails
        # the root, including a mid-width engineering-blocked root by design.
        if str(row["status"]) != "ok" or not _as_bool(row["admitted"]):
            violations.append("graph %s not admitted (fail-closed)" % (key,))
            continue
        structure = graph.get("structure")
        if not structure:
            continue
        recomputed = {
            "variable_degree_histogram":
                json.dumps(structure["variable_degree_histogram"],
                           sort_keys=True),
            "check_degree_histogram":
                json.dumps(structure["check_degree_histogram"],
                           sort_keys=True),
            "var_sockets": structure["var_sockets"],
            "check_sockets": structure["check_sockets"],
            "duplicate_edges": structure["duplicate_edges"],
            "empty_checks": structure["empty_checks"],
            "min_check_degree": structure["min_check_degree"],
            "rank": structure["rank"],
            "structural_rank": structure["structural_rank"],
            "gf32_rank": structure["gf32_rank"],
            "connected_components": structure["connected_components"],
            "isolated_variables": structure["isolated_variables"],
            "degree2_N2": structure["degree2"]["N2"],
            "degree2_cycle_rank_lower_bound":
                structure["degree2"]["cycle_rank_lower_bound"],
            "four_cycles": structure["four_cycles"],
            "girth": structure["girth"],
            "gates": json.dumps(structure["gates"], sort_keys=True),
            "admission": json.dumps(structure["admission"], sort_keys=True),
        }
        for column, value in recomputed.items():
            if _cell(row.get(column)) != _cell(value):
                violations.append("graph %s %s stored=%r recomputed=%r"
                                  % (key, column, row.get(column), value))

    print("VERIFY checked_calls=%d agreements=%d skipped=%d violations=%d"
          % (checked, agreements, skipped, len(violations)))
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    ok = not violations
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return ok


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser():
    parser = argparse.ArgumentParser(
        description="D10 mixed-degree L1 finite discriminator runner")
    parser.add_argument("--batch", action="store_true",
                        help="run the frozen 144-call L1 batch (requires "
                             "--execution-authorized from a separate "
                             "explicit authorization)")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False,
                        help="explicit execution authorization for --batch; "
                             "default false (fail-closed, no-write/no-bind)")
    parser.add_argument("--verify", action="store_true",
                        help="read-only recomputation of a completed root")
    parser.add_argument("--profile-only", action="store_true",
                        help="pre-decoder graph construction profile (no "
                             "decoder, no root)")
    parser.add_argument("--model-f-root", default=d10.MODEL_F_INPUT_ROOT,
                        help="accepted CAL-only Model-F artifact root")
    parser.add_argument("--out-root", default=None,
                        help="fresh output root (must not exist)")
    return parser


def profile_only():
    """F09 profile helper: real builders, no decoder, no root."""
    return d10.profile_graphs()


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [name for name, flag in (("--batch", args.batch),
                                        ("--verify", args.verify),
                                        ("--profile-only",
                                         args.profile_only)) if flag]
    if len(selected) != 1:
        parser.error("exactly one of --batch, --verify or --profile-only "
                     "is required")
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
        return 0
    # R206: refuse --batch before root creation and before any decoder
    # binding while --execution-authorized is false (default).
    if args.batch and not args.execution_authorized:
        print("refusing --batch: %s (pass --execution-authorized only "
              "under a separate explicit authorization)"
              % d10.AUTHORIZATION, file=sys.stderr)
        return 2
    if args.out_root is None:
        parser.error("%s requires --out-root" % selected[0])
    if args.verify:
        return 0 if verify_root(args.out_root) else 1
    from comparison_bench.formal_ir import (  # lazy production adapter
        v35_algorithm_development as v35)
    summary = run_l1_batch(
        args.out_root, args.model_f_root,
        decode_fn=v35.decode_row_layered_fftqspa,
        syndrome_fn=v35.syndrome_of_gf32)
    print("D10_L1 terminal=%s calls=%d setup=%d"
          % (summary["terminal"], summary["scientific_l1_calls"],
             summary["setup_calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
