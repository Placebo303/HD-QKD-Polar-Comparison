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
constructor rejects anything else. The APP transfer source profile is
FROZEN to the L055 challenger L1 ``CHECK_UPDATED`` beliefs
(``APP_SOURCE_PROFILE``; design §9.2): each of the 72 shared-stream APP
calls decodes the DV3 L2 graph on the canonical forward-transfer prior
mixed from its paired cell's L055 L1 belief; sourcing from CONTROL, both
profiles, per-cell best-of, or the oracle prior is forbidden, and the
verifier rejects any root whose manifest/summary names another profile.
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
    v72p2d14n_calibrated_discriminator as n14)

EVIDENCE_FILES = n14.EVIDENCE_FILES
FROZEN_COMMAND = n14.FROZEN_COMMAND

#: Frozen APP transfer-source profile (design §9.2): the single shared
#: 72-call L2 APP stream is fed exclusively by the L055 challenger L1
#: CHECK_UPDATED beliefs, one per paired (pair, block) cell. The
#: orchestrator derives APP sources from the dispatched L055 cells only
#: and refuses any caller override naming another profile; the verifier
#: rejects roots naming another profile. R202+ SHALL NOT re-pick this.
APP_SOURCE_PROFILE = "L055"

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
# R202 production binder (narrow; resolve + signature-validate only)
# --------------------------------------------------------------------------- #
_R2_RUNNER_PATH = ROOT / "scripts" / "v72p2d10_mixed_degree_l1_development.py"


def _load_r2_runner():
    # Reuse: the accepted CAL-only Model-F prior chain lives in the R2
    # runner; import it read-only by file path instead of copying (R2
    # files untouched; same pattern as the D11 runner). Lazy so the
    # fake/test path never enters this module (see R205 proof).
    import importlib.util

    key = "v72p2d10_r2_runner_reuse_n14"
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
    """R202 narrow binder: accepted helpers only, validated, zero calls.

    Returns the flat adapter dict consumed by :func:`run_authorized_batch`
    (``decode_fn``/``syndrome_fn``/``load_prior_fn``/``sample_fn``/
    ``provenance_guard_fn`` plus the ``transfer_parts`` composition kit and
    the frozen ``app_source_profile``). Every entry reuses an accepted
    D11/D12/D14/R2/D5/v35 helper — no kernel copies, no alternate
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
    guard_fn = _require_signature(
        n14.require_check_updated, ["provenance", "consumer"],
        "provenance_guard_fn")
    source_q_fn = _require_signature(
        d5.canonical_source_q, ["log_beliefs"], "source_q_fn")
    transfer_mixer_fn = _require_signature(
        d5.canonical_transfer_l2_prior, ["p2", "bob_symbols", "q_l1"],
        "transfer_mixer_fn")
    oracle_mixer_fn = _require_signature(
        d5.oracle_l2_prior, ["p2", "bob_symbols", "u1_true"],
        "oracle_mixer_fn")
    conditionalize_fn = _require_signature(
        d5.conditionalize_f_to_p2, ["p_f"], "conditionalize_fn")

    load_prior_fn = _require_signature(
        _load_r2_runner().load_prior_chain, ["model_f_root"],
        "load_prior_fn")

    def sample_fn(p_b, p_f, p1, seed):
        # One matched block plus the frozen L1 prior line, mirroring the
        # accepted R2/D11 runner composition (sample_matched_block, then
        # _floor_renorm(p1[:, bob].T, DECODER_FLOOR)); carries u2 for the
        # APP/ORACLE target leg, which R2's block helper lacks.
        import numpy as np

        block = d5.sample_matched_block(p_b, p_f, int(n14.N), int(seed))
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
    if APP_SOURCE_PROFILE != "L055" \
            or APP_SOURCE_PROFILE not in n14.L1_PROFILES:
        raise ValueError("frozen APP source profile broken: %r"
                         % (APP_SOURCE_PROFILE,))
    return {
        "decode_fn": decode_fn,
        "syndrome_fn": syndrome_fn,
        "load_prior_fn": load_prior_fn,
        "sample_fn": sample_fn,
        "provenance_guard_fn": guard_fn,
        "transfer_parts": {
            "source_q_fn": source_q_fn,
            "transfer_mixer_fn": transfer_mixer_fn,
            "oracle_mixer_fn": oracle_mixer_fn,
            "conditionalize_fn": conditionalize_fn,
        },
        "app_source_profile": APP_SOURCE_PROFILE,
    }


# --------------------------------------------------------------------------- #
# R203 plan validation, transfer composition, L055-fed APP derivation
# --------------------------------------------------------------------------- #
def _validate_call_plan(plan):
    """Contract-check the complete 288 plan BEFORE binding/loading/decoding.

    Frozen order (L045, L055, L2-APP, L2-ORACLE; pairs ascending; blocks
    ascending; ``call_idx`` 0..287) with frozen seeds and pairing. Any
    deviation raises before any adapter is bound, Model-F content loads,
    or the root is touched.
    """
    if len(plan) != n14.SCIENTIFIC_CALL_CEILING:
        raise ValueError("plan has %d calls, frozen %d"
                         % (len(plan), n14.SCIENTIFIC_CALL_CEILING))
    for arm in n14.ARMS:
        if sum(1 for e in plan if e["arm"] == arm) != 72:
            raise ValueError("plan arm %r does not carry 72 calls" % (arm,))
    pos = 0
    for arm in n14.ARMS:
        for pair_idx, (l1_seed, l2_seed) in enumerate(
                zip(n14.L1_GRAPH_SEEDS, n14.L2_GRAPH_SEEDS), start=1):
            for block_seed in n14.BLOCK_SEEDS:
                entry = plan[pos]
                pos += 1
                if entry.get("call_idx") != pos - 1 \
                        or entry.get("arm") != arm \
                        or int(entry.get("pair_idx", -1)) != pair_idx \
                        or int(entry.get("l1_graph_seed", -1)) != l1_seed \
                        or int(entry.get("l2_graph_seed", -1)) != l2_seed \
                        or int(entry.get("block_seed", -1)) \
                        != int(block_seed):
                    raise ValueError(
                        "plan identity/order violated at position %d: %r"
                        % (pos - 1, entry))
    if pos != len(plan):
        raise ValueError("plan order check covered %d/%d entries"
                         % (pos, len(plan)))
    return plan


def _compose_transfer_pair(transfer_parts, p_f):
    """Compose the production transfer/oracle closures over the loaded p2.

    Wiring only: ``q = canonical_source_q(belief)`` then the canonical
    ``q @ P`` mixer (D5), exactly the accepted ``_run_layered_block``
    composition; the oracle leg conditions on the true L1 symbols. No
    decoder contact, no root, pure closures.
    """
    import numpy as np

    p2 = transfer_parts["conditionalize_fn"](p_f)

    def transfer_fn(belief, block):
        q = transfer_parts["source_q_fn"](belief)
        return transfer_parts["transfer_mixer_fn"](
            p2, np.asarray(block["bob"], dtype=np.int64), q)

    def oracle_prior_fn(block):
        return transfer_parts["oracle_mixer_fn"](
            p2, np.asarray(block["bob"], dtype=np.int64),
            np.asarray(block["u1"], dtype=np.int64))

    return transfer_fn, oracle_prior_fn


def _derive_l055_app_sources(l1_entries, captured, l1_records):
    """Derive the 72 shared-stream APP sources from dispatched L055 cells.

    Frozen APP←L055 wiring (design §9.2): on a clean L1 phase
    ``captured[i]`` is the decoder return of ``l1_entries[i]`` in order
    (single-threaded, in-order, exactly one decoder call per L1 entry —
    asserted here). Beliefs flow through with provenance untouched (the
    Phase-B guard fail-closes on anything but ``CHECK_UPDATED``); a
    nonfinite or malformed L055 belief STOPS before any APP dispatch.
    """
    import numpy as np

    if len(captured) != len(l1_entries) \
            or len(l1_records) != len(l1_entries):
        raise RuntimeError("L1 phase lost calls: %d results for %d entries"
                           % (len(captured), len(l1_entries)))
    sources: dict = {}
    for entry, result, record in zip(l1_entries, captured, l1_records):
        if entry["arm"] != "L055":
            continue
        belief = getattr(result, "final_beliefs", None)
        if belief is not None:
            belief = np.asarray(belief, dtype=np.float64)
            if belief.shape != (n14.N, n14.Q) \
                    or not np.all(np.isfinite(belief)):
                raise ValueError(
                    "nonfinite/malformed L055 belief at pair=%d block=%d: "
                    "refusing APP derivation"
                    % (int(entry["pair_idx"]),
                       int(entry["block_seed"])))
        key = (int(entry["pair_idx"]), int(entry["block_seed"]))
        sources[key] = {
            "belief": belief,
            "provenance": getattr(result, "belief_provenance", None),
            "source_exact": bool(record["exact"]),
        }
    if len(sources) != 72:
        raise RuntimeError("APP derivation covered %d/72 L055 cells"
                           % len(sources))
    return sources


# --------------------------------------------------------------------------- #
# R203 batch orchestrator (plan-first; L055-fed APP; no filesystem writes)
# --------------------------------------------------------------------------- #
def run_authorized_batch(out_root, model_f_root, *, adapters=None,
                         build_l1_fn=None, build_l2_fn=None,
                         app_sources=None, app_source_profile=None,
                         now_fn=None, rss_fn=None):
    """Execute the frozen N batch and return the evidence bundle (no writes).

    ``adapters`` is a flat dict with ``decode_fn``/``syndrome_fn``/
    ``load_prior_fn``/``sample_fn`` plus either the production
    ``transfer_parts`` composition kit (binder-supplied) or direct
    ``transfer_fn``/``oracle_prior_fn``; ``None`` production-binds inside,
    AFTER plan validation and the refuse probe (R203 order). An optional
    ``provenance_guard_fn`` overrides the accepted default guard
    (test machinery only). ``app_sources`` given selects the legacy
    single-phase dispatch (explicit sources + profile, as N202–N209);
    ``None`` derives the 72 sources from the dispatched L055 cells
    (frozen APP←L055, design §9.2) and refuses any profile override
    naming another L1 arm. ``build_l1_fn``/``build_l2_fn`` may arrive
    explicitly or inside ``adapters`` (fake builders travel with the
    fake adapter dict on the R205 path); both default to the frozen
    real builders. Returns the bundle consumed by
    :func:`write_batch_root`; creates no files and no directories.
    """
    plan = n14.build_call_plan()
    _validate_call_plan(plan)
    resolved = n14.refuse_out_root(out_root)  # probe only; creates nothing
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
    guard_fn = inj.get("provenance_guard_fn")
    if app_sources is not None:
        if inj.get("transfer_fn") is None \
                or inj.get("oracle_prior_fn") is None:
            raise ValueError(
                "transfer_fn and oracle_prior_fn must be explicitly "
                "injected for L2 APP/ORACLE (no frozen default)")
        if app_source_profile not in n14.L1_PROFILES:
            raise ValueError("app_sources and a frozen app_source_profile "
                             "(an N L1 profile) must be explicitly injected")
        derive_sources = False
        transfer_fn = inj["transfer_fn"]
        oracle_prior_fn = inj["oracle_prior_fn"]
    else:
        if app_source_profile is not None \
                and app_source_profile != APP_SOURCE_PROFILE:
            raise ValueError(
                "refusing APP source re-pick %r: frozen to %r "
                "(design §9.2)" % (app_source_profile,
                                   APP_SOURCE_PROFILE))
        app_source_profile = APP_SOURCE_PROFILE
        derive_sources = True
        transfer_fn = inj.get("transfer_fn")
        oracle_prior_fn = inj.get("oracle_prior_fn")
        transfer_parts = inj.get("transfer_parts")
        if transfer_parts is not None and (
                transfer_fn is not None or oracle_prior_fn is not None):
            raise ValueError("transfer_parts and direct transfer_fn/ "
                             "oracle_prior_fn are mutually exclusive")
        if transfer_parts is None and (
                transfer_fn is None or oracle_prior_fn is None):
            raise ValueError(
                "transfer_fn and oracle_prior_fn must be explicitly "
                "injected for the L055-fed APP/ORACLE legs "
                "(no frozen default)")
    build_l1_fn = build_l1_fn or inj.pop("build_l1_fn", None) \
        or n14.build_l1_graph
    build_l2_fn = build_l2_fn or inj.pop("build_l2_fn", None) \
        or n14.build_l2_graph
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
    if derive_sources:
        transfer_parts = inj.get("transfer_parts")
        if transfer_parts is not None:
            transfer_fn, oracle_prior_fn = _compose_transfer_pair(
                transfer_parts, p_f)
            log("composed L055-fed transfer/oracle closures over p2")
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

    engineering_reason = ""
    if not derive_sources:
        outcome = n14.execute_plan(
            plan, graphs_l1, graphs_l2, blocks, decode_fn, syndrome_fn,
            transfer_fn=transfer_fn, oracle_prior_fn=oracle_prior_fn,
            app_sources=app_sources,
            provenance_guard_fn=guard_fn, now=now, rss_fn=rss_fn)
        records = outcome["records"]
        engineering_reason = outcome["engineering_reason"]
    else:
        # Two-phase frozen dispatch: L1 arms first (capturing the L055
        # decoder returns in call order), then the APP/ORACLE legs on
        # sources derived from those L055 cells only. No extra decoder
        # calls: 144 L1 + 144 APP/ORACLE = 288.
        l1_entries = [e for e in plan if e["arm"] in n14.L1_PROFILES]
        tail_entries = [e for e in plan
                        if e["arm"] not in n14.L1_PROFILES]
        captured: list = []

        def capturing_decode(H, prior, syn, **kw):
            result = decode_fn(H, prior, syn, **kw)
            captured.append(result)
            return result

        outcome_a = n14.execute_plan(
            l1_entries, graphs_l1, graphs_l2, blocks, capturing_decode,
            syndrome_fn, transfer_fn=transfer_fn,
            oracle_prior_fn=oracle_prior_fn, app_sources=None,
            provenance_guard_fn=guard_fn, now=now, rss_fn=rss_fn)
        engineering_reason = outcome_a["engineering_reason"]
        if engineering_reason:
            records = outcome_a["records"]
        else:
            app_sources = _derive_l055_app_sources(
                l1_entries, captured, outcome_a["records"])
            log("derived L055-fed APP sources count=%d" % len(app_sources))
            outcome_b = n14.execute_plan(
                tail_entries, graphs_l1, graphs_l2, blocks, decode_fn,
                syndrome_fn, transfer_fn=transfer_fn,
                oracle_prior_fn=oracle_prior_fn, app_sources=app_sources,
                provenance_guard_fn=guard_fn, now=now, rss_fn=rss_fn)
            engineering_reason = outcome_b["engineering_reason"]
            records = outcome_a["records"] + outcome_b["records"]
    # Frozen-order identity gate plus the global call index: each phase
    # stamps its own 0-based positions, so re-stamp the concatenated
    # records to the single frozen 0..287 order (identity for the
    # single-phase path). Any order deviation is a contract STOP.
    for pos, (record, entry) in enumerate(zip(records, plan)):
        for key in ("arm", "pair_idx", "l1_graph_seed", "l2_graph_seed",
                    "block_seed"):
            if str(record[key]) != str(entry[key]):
                raise RuntimeError(
                    "dispatch order violated at position %d: %r != %r"
                    % (pos, {k: record.get(k) for k in
                             ("arm", "pair_idx", "block_seed")}, entry))
        record["call_idx"] = pos
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

    # Manifest precedent (D11/D12): the manifest retains the flag-free
    # scientific command identity (FROZEN_COMMAND carries no
    # --execution-authorized flag); authorization lives in the CLI flag
    # plus the separate explicit authorization, never in this string.
    manifest = {
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
    }
    arm_rows = _arm_rows(records)
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
    log_lines.append(_log_line(
        "N terminal=%s calls=%d setup=%d wall_s=%.3f"
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
# R204 never-overwrite writer (one mkdir + six files; no computation)
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


def run_n14_batch(out_root, model_f_root, decode_fn, syndrome_fn, *,
                  build_l1_fn=None, build_l2_fn=None, load_prior_fn=None,
                  sample_fn=None, transfer_fn=None, oracle_prior_fn=None,
                  app_sources=None, app_source_profile=None,
                  now_fn=None, rss_fn=None):
    """Legacy injected batch entry (N202–N209 fake-runner contract).

    Thin wrapper preserving the accepted single-phase behavior when
    explicit ``app_sources`` are supplied: forwards the injections as an
    adapter dict, then exactly one orchestrator call plus one
    never-overwrite writer. Production and R205 paths go through
    ``main()`` → :func:`run_authorized_batch` instead.
    """
    return write_batch_root(run_authorized_batch(
        out_root, model_f_root,
        adapters={"decode_fn": decode_fn, "syndrome_fn": syndrome_fn,
                  "load_prior_fn": load_prior_fn, "sample_fn": sample_fn,
                  "transfer_fn": transfer_fn,
                  "oracle_prior_fn": oracle_prior_fn},
        build_l1_fn=build_l1_fn, build_l2_fn=build_l2_fn,
        app_sources=app_sources, app_source_profile=app_source_profile,
        now_fn=now_fn, rss_fn=rss_fn))


# --------------------------------------------------------------------------- #
# verify (read-only; zero decoder calls; zero skip; fail-closed)
# --------------------------------------------------------------------------- #
def verify_root(out_root, build_l1_fn=None, build_l2_fn=None,
                check_updated_token_value=None):
    """Recompute a completed N root from its evidence; fail-closed.

    ``check_updated_token_value`` overrides the accepted v35-backed token
    lookup (test machinery only; ``None`` selects the lazy production
    token, which binds the v35 module on first use).
    """
    root = Path(out_root)
    build_l1_fn = build_l1_fn or n14.build_l1_graph
    build_l2_fn = build_l2_fn or n14.build_l2_graph
    if check_updated_token_value is None:
        check_updated_token_value = n14.check_updated_token()
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
    if manifest.get("app_source_profile") != APP_SOURCE_PROFILE \
            or summary.get("app_source_profile") != APP_SOURCE_PROFILE:
        violations.append("app_source_profile must be the frozen %r "
                          "(design §9.2 forbids CONTROL/both/best-of/oracle)"
                          % (APP_SOURCE_PROFILE,))
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
                    str(check_updated_token_value):
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


def main(argv=None, *, adapters_override=None):
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
    # R204 authorized true branch: exactly one batch-orchestrator call
    # plus one never-overwrite writer (replaces the readiness SystemExit).
    # adapters_override carries test-machinery fakes only; None
    # production-binds inside the orchestrator, after plan validation.
    bundle = run_authorized_batch(
        args.out_root, args.model_f_root, adapters=adapters_override)
    summary = write_batch_root(bundle)
    print("N terminal=%s calls=%d setup=%d"
          % (summary["terminal"], summary["scientific_calls"],
             summary["setup_calls"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
