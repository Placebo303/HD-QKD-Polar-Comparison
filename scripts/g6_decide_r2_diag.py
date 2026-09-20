"""G6 DECIDE R2 DIAG thin runner — frozen diagnostic contrast (readiness only).

Frozen R2 scope (D2 packet delegation this session). Track DECIDE-readiness
(NOT execution). Branch formal-ir-v72p1-addendum-clean.

- Same frozen contract as R1: pool P-2M-tail (registry v71_data_registry.json,
  session 20260123_2M_1p2M_0dB, frames 2093..2156, 64 frames key-disjoint from
  CAL 702..1725 / VAL 1726..1981), op L020-n128/m94 (2^35+3^93/E349/3^27+4^67),
  K=2 graphs 4601/4602 rebuilt via the SAME accepted D10-R2 builder with the
  SAME frozen seeds/namespaces (deterministic; admission 2/2 required, no new
  seeds). Reuse: r1 graph/precheck/decision/binds, D10-R2 builder/admission/
  refusal, v35/D16 decoder kernels (lazy bind, no duplicate kernels).
- 3 new flags: --prior-mode {model_f|uniform} (uniform bypasses the Model-F
  loader entirely), --max-iter {90|300} ONLY, --audit-only (A0: forces 0
  decoder calls; truth read ONLY post-decision).
- Arm map (frozen ORTHOGONAL, main-thread ruling): A1=(uniform,90) isolates
  the PRIOR effect holding iterations at R1 level; A2=(model_f,300) isolates
  the ITERATION effect holding the prior fixed. R1 already supplies the
  (model_f,90) cell; (uniform,300) is intentionally never run.
- Fail-closed admission: ANY (prior-mode,max-iter) combo outside
  {(uniform,90),(model_f,300)} -> PRE_EXECUTION_BLOCKED with ZERO decoder
  calls (checked in validate_diag_flags before the first call, not at
  verify). In particular (model_f,90) is refused (R1 replica must not burn
  calls) and (uniform,300) is refused (confounded cell, never run).
- Modes (exactly one required): --profile-only / --execute-real / --audit-only
  / --verify. --execute-real and --audit-only refuse rc=2 without
  --execution-authorized (zero decoder calls on refusal).
- Fresh root: workspace/g6r2_diag_c4a1d2e6-9b3f-4e7a-8c5d-2f6a0e1b3d4c with
  parent manifest.json + summary.json plus per-arm subdirs A1/A2/A0, each
  with block_records.csv + summary.json (+ report.md optional). --verify
  recomputes the parent aggregate across the triple AND each arm singly.
  Budgets sci<=256/setup<=8 enforced with refusal.
- F-gate: UNDETECTED_STOP absolute; exact/accepted/undetected isolation;
  ORACLE/APP hard-fail; disclosure sums include failures; beta derived-only.

Forbidden: decode/analyze real symbols or truth in R6b (code-path
construction only; truth-column handling on FAKE fixtures only); create the
UUID root; edit R1 runner/tests; touch src/experiments/tools/results/
outputs_comparison/R1 root; commit/push.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import g6_decide_r1 as r1  # noqa: E402
from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as d10r2  # noqa: E402

# Frozen identifiers (pool/op/graphs reuse R1 exactly; root/budgets are R2).
CHANGE_ID = "g6-decide-r2-diag"
CYCLE_ID = "G6-DECIDE-R2-DIAG"
N = r1.N
M = r1.M
Q = r1.Q
DAMPING = r1.DAMPING
ARM = r1.ARM
CANDIDATE_ID = r1.CANDIDATE_ID
GRAPH_SEEDS = r1.GRAPH_SEEDS
H_FROZEN = r1.H_FROZEN
H_L2 = r1.H_L2
K_SYM_NOMINAL = r1.K_SYM_NOMINAL
PRIOR_MODEL_F = "model_f"
PRIOR_UNIFORM = "uniform"
PRIOR_MODES = (PRIOR_MODEL_F, PRIOR_UNIFORM)
MAX_ITERS_ALLOWED = (90, 300)
FROZEN_A1 = (PRIOR_UNIFORM, 90)
FROZEN_A2 = (PRIOR_MODEL_F, 300)
FROZEN_ARMS = (FROZEN_A1, FROZEN_A2)
FROZEN_REGISTRY = r1.FROZEN_REGISTRY
FROZEN_SESSION = r1.FROZEN_SESSION
FROZEN_FRAMES = r1.FROZEN_FRAMES
FROZEN_PRIOR_ROOT = r1.FROZEN_PRIOR_ROOT
FROZEN_R1_ROOT = "workspace/g6_decide_r1_" + r1.FUTURE_ROOT_UUID
FUTURE_ROOT_UUID = "c4a1d2e6-9b3f-4e7a-8c5d-2f6a0e1b3d4c"
FUTURE_ROOT = "workspace/g6r2_diag_" + FUTURE_ROOT_UUID
ARM_SUBDIRS = ("A1", "A2", "A0")
SCI_CEILING = 256
SETUP_CEILING = 8
EVIDENCE_FILES = ("block_records.csv", "summary.json")
PARENT_FILES = ("manifest.json", "summary.json")
BLOCK_COLUMNS = tuple(r1.BLOCK_COLUMNS) + (
    "arm_id", "prior_mode", "max_iter", "true_weight", "r1_residual")

FROZEN_COMMAND_A1 = (
    ".venv/bin/python scripts/g6_decide_r2_diag.py --execute-real "
    "--execution-authorized --prior-mode uniform --max-iter 90 "
    "--registry %s --session %s --frames %s --arm %s --prior-root %s "
    "--out-dir %s/A1"
    % (FROZEN_REGISTRY, FROZEN_SESSION, FROZEN_FRAMES, ARM,
       FROZEN_PRIOR_ROOT, FUTURE_ROOT))
FROZEN_COMMAND_A2 = (
    ".venv/bin/python scripts/g6_decide_r2_diag.py --execute-real "
    "--execution-authorized --prior-mode model_f --max-iter 300 "
    "--registry %s --session %s --frames %s --arm %s --prior-root %s "
    "--out-dir %s/A2"
    % (FROZEN_REGISTRY, FROZEN_SESSION, FROZEN_FRAMES, ARM,
       FROZEN_PRIOR_ROOT, FUTURE_ROOT))
FROZEN_COMMAND_A0 = (
    ".venv/bin/python scripts/g6_decide_r2_diag.py --audit-only "
    "--execution-authorized --r1-root %s --registry %s --session %s "
    "--frames %s --arm %s --out-dir %s/A0"
    % (FROZEN_R1_ROOT, FROZEN_REGISTRY, FROZEN_SESSION, FROZEN_FRAMES,
       ARM, FUTURE_ROOT))
FROZEN_COMMAND_VERIFY = (
    ".venv/bin/python scripts/g6_decide_r2_diag.py --verify --out-dir %s"
    % FUTURE_ROOT)
FROZEN_COMMANDS = {"A1": FROZEN_COMMAND_A1, "A2": FROZEN_COMMAND_A2,
                   "A0": FROZEN_COMMAND_A0}


def validate_diag_flags(prior_mode, max_iter) -> tuple[str, int]:
    """Fail-closed admission: ONLY {(uniform,90),(model_f,300)} admitted.

    Anything else -> PRE_EXECUTION_BLOCKED with zero decoder calls (this
    check runs before the first call). (model_f,90) is the R1 replica and
    must not burn calls; (uniform,300) is the confounded never-run cell.
    """
    pm = str(prior_mode).strip().lower() if prior_mode is not None else ""
    if pm not in PRIOR_MODES:
        raise ValueError("PRE_EXECUTION_BLOCKED: prior-mode %r not in %r"
                         % (prior_mode, list(PRIOR_MODES)))
    try:
        k = int(max_iter.strip()) if isinstance(max_iter, str) else int(max_iter)
    except (TypeError, ValueError):
        raise ValueError("PRE_EXECUTION_BLOCKED: max-iter %r not an int"
                         % (max_iter,))
    if k not in MAX_ITERS_ALLOWED:
        raise ValueError("PRE_EXECUTION_BLOCKED: max-iter %r not in %r"
                         % (max_iter, list(MAX_ITERS_ALLOWED)))
    if (pm, k) not in FROZEN_ARMS:
        raise ValueError("PRE_EXECUTION_BLOCKED: (%s,%d) is not a frozen "
                         "R2 arm; admitted %r (zero decoder calls)"
                         % (pm, k, [list(a) for a in FROZEN_ARMS]))
    return pm, k


def arm_id_for(prior_mode: str, max_iter: int) -> str:
    """Frozen orthogonal arms: (uniform,90)->A1, (model_f,300)->A2."""
    pm, k = validate_diag_flags(prior_mode, max_iter)
    if (pm, k) == FROZEN_A1:
        return "A1"
    if (pm, k) == FROZEN_A2:
        return "A2"
    raise ValueError("PRE_EXECUTION_BLOCKED: (%s,%d) is not a frozen R2 arm"
                     % (pm, k))


def build_graph(graph_seed: int) -> dict:
    """Rebuild one frozen G6 graph (same builder/seeds/namespaces as R1)."""
    if int(graph_seed) not in GRAPH_SEEDS:
        raise ValueError("PRE_EXECUTION_BLOCKED: graph seed %r outside "
                         "frozen G6 pair" % (graph_seed,))
    return r1.build_graph(int(graph_seed))


def build_uniform_prior(n: int = N, q: int = Q) -> np.ndarray:
    """Prior-free uniform prior (1/q everywhere); no Model-F loader involved."""
    return np.full((int(n), int(q)), 1.0 / float(q), dtype=np.float64)


def run_diag_block(graph: dict, prior: np.ndarray, syndrome: np.ndarray,
                   ref_tag: bytes, truth_u2: np.ndarray, entry: dict,
                   decode_fn, syndrome_fn, call_idx: int, max_iter: int,
                   arm_id: str, prior_mode: str) -> dict:
    """Single-pass cold max_iter/1.0 decode; truth used ONLY post-decision."""
    if graph.get("dense") is None or not bool(graph.get("admitted")):
        raise d10r2.StructureNotAdmitted("non-admitted G6 graph")
    H = np.asarray(graph["dense"], dtype=np.uint8)
    prior = np.asarray(prior, dtype=np.float64)
    syn = np.asarray(syndrome, dtype=np.uint8)
    truth = np.asarray(truth_u2, dtype=np.int64)
    t0 = time.perf_counter()
    rec: dict = {
        "call_idx": int(call_idx), "frame_id": int(entry["frame_id"]),
        "block_id": int(entry["block_id"]), "session_id": str(entry.get("session_id", "")),
        "arm": ARM, "candidate_id": CANDIDATE_ID,
        "graph_seed": int(entry["graph_seed"]), "n": N, "m": M,
        "attempted": True, "finite": False, "syndrome_match": False,
        "tag_match": False, "protocol_accepted": False,
        "verified_exact": False, "undetected": False, "outcome": "attempted",
        "syndrome_bits": 5 * M, "tag_bits": r1.TAG_BITS, "control_bits": 0,
        "interaction_bits": 0, "auth_bits": 0,
        "disclosure_bits": r1.disclosed_bits(M), "iters": -1, "residual": -1,
        "provenance": "", "wall_s": 0.0, "crash": False, "error": "",
        "arm_id": arm_id, "prior_mode": prior_mode, "max_iter": int(max_iter),
        "true_weight": -1, "r1_residual": -1}
    try:
        result = decode_fn(H, prior, syn, max_iter=int(max_iter),
                           damping_alpha=DAMPING, warm_beliefs=None, field=None)
        x_hat = np.asarray(result.x_hat, dtype=np.int64).ravel()
        prov = str(getattr(result, "belief_provenance", "") or "")
        if "ORACLE" in prov.upper() or "APP" in prov.upper():
            raise ValueError("ORACLE/APP provenance on real path: %r" % prov)
        finite = bool(x_hat.shape == (N,) and np.all((x_hat >= 0) & (x_hat < 32))
                      and 0 <= int(result.iterations) <= int(max_iter)
                      and np.all(np.isfinite(prior)))
        syn_match = bool(np.array_equal(np.asarray(syndrome_fn(H, x_hat)), syn))
        tag_match = bool(r1._candidate_tag(x_hat) == bytes(ref_tag))
        accepted = bool(finite and syn_match and tag_match)
        exact = bool(accepted and x_hat.shape == truth.shape and np.array_equal(x_hat, truth))
        undet = bool(accepted and not exact)
        residual = int(np.count_nonzero(np.asarray(syndrome_fn(H, x_hat)) != syn))
        rec.update({
            "finite": finite, "syndrome_match": syn_match, "tag_match": tag_match,
            "protocol_accepted": accepted, "verified_exact": exact,
            "undetected": undet,
            "outcome": "undetected" if undet else ("exact" if exact
                      else ("accepted" if accepted else "attempted")),
            "iters": int(result.iterations), "residual": residual,
            "provenance": prov, "wall_s": time.perf_counter() - t0})
        # Isolation: exact subset of accepted; undetected never merged.
        assert (not exact) or accepted
        assert (not undet) or (accepted and not exact)
        return rec
    except Exception as exc:  # retained crash, never retried
        rec.update({"crash": True, "error": repr(exc)[:300],
                    "outcome": "attempted",
                    "wall_s": time.perf_counter() - t0})
        return rec


def _beta_pair(attempted: int, leak_sum: int) -> tuple:
    denom_p = attempted * N * H_FROZEN if attempted else None
    denom_l = attempted * N * H_L2 if attempted else None
    beta_p = (1.0 - leak_sum / denom_p) if denom_p else None
    beta_l = (1.0 - leak_sum / denom_l) if denom_l else None
    return beta_p, beta_l


def _decode_bundle(resolved, manifest_extra: dict, records: list[dict],
                   setup_calls: int, arm_id: str, prior_mode: str,
                   max_iter: int) -> dict:
    attempted = len(records)
    accepted = sum(1 for x in records if x["protocol_accepted"])
    exact = sum(1 for x in records if x["verified_exact"])
    undet = sum(1 for x in records if x["undetected"])
    leak_sum = sum(int(x["disclosure_bits"]) for x in records)
    beta_p, beta_l = _beta_pair(attempted, leak_sum)
    reconciled = exact * K_SYM_NOMINAL * 5
    residual_hist = {str(k): v for k, v in
                     sorted(Counter(int(x["residual"]) for x in records).items())}
    manifest = {
        "schema": "g6_decide_r2_diag_manifest_v1", "change_id": CHANGE_ID,
        "cycle": CYCLE_ID, "command": FROZEN_COMMANDS[arm_id],
        "mode": "decode", "arm_id": arm_id, "prior_mode": prior_mode,
        "max_iter": int(max_iter),
        "out_root": str(resolved),
        "operating_point": {"n": N, "m": M, "arm": ARM,
        "candidate_id": CANDIDATE_ID, "var_counts": dict(r1.VAR_COUNTS),
        "check_counts": dict(r1.CHECK_COUNTS), "E": r1.EDGE_TOTAL},
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": int(max_iter), "damping_alpha": DAMPING,
                    "schedule": "cold row-layered single-pass"},
        "disclosure": {"syndrome_bits": 5 * M, "tag_bits": r1.TAG_BITS,
                       "control_bits": 0, "interaction_bits": 0, "auth_bits": 0,
                       "per_block": r1.disclosed_bits(M)},
        "population_split": {"CAL": "702..1725 consumed", "selection": "empty",
                             "confirmation": "2093..2156 key-disjoint"},
        "key_disjointness": "confirmation disjoint from CAL/VAL/V55-2M",
        "SECURITY_MODEL": "generic-only", "graph_seeds": list(GRAPH_SEEDS),
        "domain_namespace": r1.DOMAIN_NAMESPACE,
        "budgets": {"scientific_calls": SCI_CEILING, "setup_calls": SETUP_CEILING},
        "setup_calls": setup_calls, "evidence_files": list(EVIDENCE_FILES),
        "authorization": "separate explicit grant required for --execute-real",
    }
    manifest.update(manifest_extra)
    summary = {
        "schema": "g6_decide_r2_diag_summary_v1", "mode": "decode",
        "terminal": "UNDETECTED_STOP" if undet else
        ("COMPLETE_128" if attempted == 128 else "ENGINEERING_BLOCKED"),
        "arm_id": arm_id, "prior_mode": prior_mode, "max_iter": int(max_iter),
        "attempted": attempted, "accepted": accepted, "exact": exact,
        "undetected": undet,
        "accepted_fraction": (accepted / attempted) if attempted else None,
        "exact_fraction": (exact / attempted) if attempted else None,
        "FER_proxy": ((attempted - exact) / attempted) if attempted else None,
        "disclosure_sum": leak_sum, "k_sym_nominal": K_SYM_NOMINAL,
        "reconciled_net_bits": reconciled,
        "reconciled_rate": (reconciled / (attempted * N * 5)) if attempted else None,
        "beta_eff_empirical_primary": beta_p,
        "beta_eff_empirical_l2_sensitivity": beta_l,
        "H_frozen_primary": H_FROZEN, "H_L2_sensitivity": H_L2,
        "scientific_calls": attempted, "setup_calls": setup_calls,
        "decoder_calls": attempted, "audit_blocks": 0,
        "per_arm": {arm_id: {"attempted": attempted, "accepted": accepted,
                             "exact": exact, "undetected": undet,
                             "disclosure_sum": leak_sum}},
        "diag_histograms": {"residual_hist": residual_hist},
        "out_root": str(resolved)}
    return {"resolved": resolved, "manifest": manifest, "records": records,
            "summary": summary}


def run_diag_arm(out_dir: str, registry: str, session_id: str,
                 frames_spec: str, arm: str, prior_root: str,
                 prior_mode: str = PRIOR_MODEL_F, max_iter: int = 90, *,
                 adapters=None, reader_override=None,
                 frames_override=None) -> dict:
    """Execute one frozen 128-call decode arm (A1=uniform/90 prior-effect,
    A2=model_f/300 iteration-effect).

    frames_override is a FAKE-test seam (bypasses the real Pre-EXECUTE
    registry/parquet key-check); None means the real gate.
    """
    prior_mode, max_iter = validate_diag_flags(prior_mode, max_iter)
    arm_id = arm_id_for(prior_mode, max_iter)
    resolved = d10r2.refuse_out_root(out_dir)  # probe only; creates nothing
    if frames_override is not None:
        frames = [int(f) for f in frames_override]
    else:
        frames = r1._pre_execute_check(registry, session_id, frames_spec, arm,
                                       prior_root)
    if len(frames) != 64:
        raise ValueError("PRE_EXECUTION_BLOCKED: G6 plan requires 64 frames")
    plan = r1.build_call_plan(frames)
    if adapters is None:
        adapters = r1.bind_production_adapters()
    else:
        adapters = dict(adapters)
    r1._hard_fail_oracle_app(adapters)
    decode_fn, syndrome_fn = adapters.get("decode_fn"), adapters.get("syndrome_fn")
    if decode_fn is None or syndrome_fn is None:
        raise ValueError("adapters decode_fn/syndrome_fn must be injected")
    if prior_mode == PRIOR_UNIFORM:
        # Uniform bypasses the Model-F loader entirely (never called).
        p_uniform = build_uniform_prior()
        p_f = None
    else:
        load_prior_fn = adapters.get("load_prior_fn")
        if load_prior_fn is None:
            raise ValueError("model_f prior requires load_prior_fn")
        p_uniform = None
        p_f = load_prior_fn(prior_root)
    graphs = {}
    for seed in GRAPH_SEEDS:
        if "build_fn" in adapters:
            graph = adapters["build_fn"](seed)
        else:
            graph = build_graph(seed)
        if not bool(graph.get("admitted")):
            raise RuntimeError("graph %r not admitted; ENGINEERING_BLOCKED" % seed)
        graphs[int(seed)] = graph
    setup_calls = len(graphs) + 2  # graphs + plan + manifest
    if setup_calls > SETUP_CEILING:
        raise RuntimeError("setup %d > ceiling %d" % (setup_calls, SETUP_CEILING))
    import pandas as pd
    session = [s for s in json.loads((ROOT / registry).read_text())["sessions"]
               if s["session_id"] == session_id][0] \
        if frames_override is None else {"provenance": "fake.parquet",
                                         "session_id": session_id}
    pairs_path = ROOT / session["provenance"]
    reader = reader_override or pd.read_parquet
    frame = reader(str(pairs_path), columns=["frame_id", "pair_idx",
                                             "alice_symbol", "bob_symbol"],
                   filters=[("frame_id", "in", frames)])
    records = []
    for entry in plan:
        fid = int(entry["frame_id"])
        sel = frame.loc[frame["frame_id"] == fid].copy()
        if len(sel) != 256:
            raise ValueError("PRE_EXECUTION_BLOCKED: frame %d rows %d != 256"
                             % (fid, len(sel)))
        sel = sel.sort_values("pair_idx", kind="stable")
        alice_full = sel["alice_symbol"].to_numpy(dtype=np.int64)
        bob_full = sel["bob_symbol"].to_numpy(dtype=np.int64)
        alice_u2_full = alice_full % 32
        pos = entry["block_id"] % 2
        sl = slice(pos * 128, (pos + 1) * 128)
        truth_u2 = alice_u2_full[sl]
        bob_block = bob_full[sl]
        if prior_mode == PRIOR_UNIFORM:
            assert p_f is None  # loader bypassed; decoder gets 1/32
            prior = p_uniform
        else:
            prior = r1.marginal_l2_prior(p_f, bob_block)
        graph = graphs[int(entry["graph_seed"])]
        H = np.asarray(graph["dense"], dtype=np.uint8)
        syn = np.asarray(syndrome_fn(H, truth_u2), dtype=np.uint8)
        ref_tag = r1._candidate_tag(truth_u2)
        rec = run_diag_block(graph, prior, syn, ref_tag, truth_u2,
                             {**entry, "session_id": session_id},
                             decode_fn, syndrome_fn, entry["call_idx"],
                             max_iter, arm_id, prior_mode)
        records.append(rec)
        if rec["undetected"]:
            break  # UNDETECTED_STOP absolute (fail-closed)
    if len(records) > SCI_CEILING:
        raise RuntimeError("scientific calls exceed ceiling")
    return _decode_bundle(resolved, {"registry": registry, "session_id": session_id,
                                     "frames": frames_spec, "arm": arm,
                                     "candidate_id": CANDIDATE_ID,
                                     "prior_root": prior_root},
                          records, setup_calls, arm_id, prior_mode, max_iter)


def run_audit_batch(out_dir: str, r1_root: str, registry: str, session_id: str,
                    frames_spec: str, arm: str, *,
                    adapters=None, reader_override=None,
                    frames_override=None,
                    r1_records_override=None) -> dict:
    """A0 audit: 0 decoder calls; R1 decisions loaded first, truth read after.

    Per-block true error weight (nnz of truth U2) + truth-syndrome-weight
    recompute (same graphs/kernels, never a decoder). A counting decode_fn in
    adapters, if present, is never invoked (proven by the 0 counter).
    """
    resolved = d10r2.refuse_out_root(out_dir)  # probe only; creates nothing
    if r1_records_override is not None:
        r1rows = [dict(x) for x in r1_records_override]
    else:
        r1dir = Path(r1_root) if Path(r1_root).is_absolute() else ROOT / r1_root
        block_csv = r1dir / "block_records.csv"
        if not r1dir.is_dir() or not block_csv.is_file():
            raise ValueError("PRE_EXECUTION_BLOCKED: r1 root %r lacks evidence"
                             % (r1_root,))
        r1rows = list(csv.DictReader(block_csv.read_text(encoding="utf-8").splitlines()))
    if not r1rows:
        raise ValueError("PRE_EXECUTION_BLOCKED: r1 root has no block records")
    if frames_override is not None:
        frames = [int(f) for f in frames_override]
    else:
        # Pool gate only (frame_id column); prior-root identity frozen, no load.
        frames = r1._pre_execute_check(registry, session_id, frames_spec, arm,
                                       FROZEN_PRIOR_ROOT)
    if adapters is None:
        adapters = r1.bind_production_adapters()
    else:
        adapters = dict(adapters)
    r1._hard_fail_oracle_app(adapters)
    syndrome_fn = adapters.get("syndrome_fn")
    if syndrome_fn is None:
        raise ValueError("adapters syndrome_fn must be injected")
    guard = {"decoder_calls": 0}

    def _forbidden_decode(*a, **k):
        guard["decoder_calls"] += 1
        raise AssertionError("audit path must not decode")

    if adapters.get("decode_fn") is not None:
        adapters["decode_fn"] = _forbidden_decode
    graphs = {}
    for seed in GRAPH_SEEDS:
        if "build_fn" in adapters:
            graph = adapters["build_fn"](seed)
        else:
            graph = build_graph(seed)
        if not bool(graph.get("admitted")):
            raise RuntimeError("graph %r not admitted; ENGINEERING_BLOCKED" % seed)
        graphs[int(seed)] = graph
    setup_calls = len(graphs) + 2
    if setup_calls > SETUP_CEILING:
        raise RuntimeError("setup %d > ceiling %d" % (setup_calls, SETUP_CEILING))
    # Truth read POST-decision (R1 decisions above; truth never feeds a decoder).
    import pandas as pd
    session = [s for s in json.loads((ROOT / registry).read_text())["sessions"]
               if s["session_id"] == session_id][0] \
        if frames_override is None else {"provenance": "fake.parquet",
                                         "session_id": session_id}
    pairs_path = ROOT / session["provenance"]
    reader = reader_override or pd.read_parquet
    frame = reader(str(pairs_path), columns=["frame_id", "pair_idx",
                                             "alice_symbol"],
                   filters=[("frame_id", "in", frames)])
    by_frame: dict[int, object] = {}
    for fid in {int(x["frame_id"]) for x in r1rows}:
        sel = frame.loc[frame["frame_id"] == fid].copy()
        if len(sel) != 256:
            raise ValueError("PRE_EXECUTION_BLOCKED: frame %d rows %d != 256"
                             % (fid, len(sel)))
        by_frame[fid] = sel.sort_values("pair_idx", kind="stable")
    records = []
    for idx, row in enumerate(r1rows):
        fid = int(row["frame_id"])
        bid = int(row["block_id"])
        seed = int(row["graph_seed"])
        if seed not in graphs:
            raise ValueError("PRE_EXECUTION_BLOCKED: r1 graph_seed %r outside "
                             "frozen pair" % (seed,))
        sel = by_frame[fid]
        alice_full = sel["alice_symbol"].to_numpy(dtype=np.int64)
        truth_u2 = (alice_full % 32)[(bid % 2) * 128:(bid % 2 + 1) * 128]
        true_w = int(np.count_nonzero(truth_u2))
        H = np.asarray(graphs[seed]["dense"], dtype=np.uint8)
        syn_w = int(np.count_nonzero(np.asarray(syndrome_fn(H, truth_u2))))
        records.append({
            "call_idx": idx, "frame_id": fid, "block_id": bid,
            "session_id": session_id, "arm": ARM, "candidate_id": CANDIDATE_ID,
            "graph_seed": seed, "n": N, "m": M,
            "attempted": False, "finite": False, "syndrome_match": False,
            "tag_match": False, "protocol_accepted": False,
            "verified_exact": False, "undetected": False, "outcome": "audit",
            "syndrome_bits": 0, "tag_bits": 0, "control_bits": 0,
            "interaction_bits": 0, "auth_bits": 0, "disclosure_bits": 0,
            "iters": -1, "residual": syn_w, "provenance": "AUDIT_POST_DECISION",
            "wall_s": 0.0, "crash": False, "error": "",
            "arm_id": "A0", "prior_mode": "none", "max_iter": -1,
            "true_weight": true_w, "r1_residual": int(row.get("residual", -1))})
    if len(records) > SCI_CEILING:
        raise RuntimeError("audit blocks exceed ceiling")
    true_hist = {str(k): v for k, v in
                 sorted(Counter(x["true_weight"] for x in records).items())}
    syn_hist = {str(k): v for k, v in
                sorted(Counter(int(x["residual"]) for x in records).items())}
    manifest = {
        "schema": "g6_decide_r2_diag_manifest_v1", "change_id": CHANGE_ID,
        "cycle": CYCLE_ID, "command": FROZEN_COMMAND_A0,
        "mode": "audit", "arm_id": "A0", "prior_mode": "none",
        "max_iter": None, "r1_root": str(r1_root),
        "registry": registry, "session_id": session_id, "frames": frames_spec,
        "arm": arm, "candidate_id": CANDIDATE_ID,
        "out_root": str(resolved),
        "operating_point": {"n": N, "m": M, "arm": ARM,
        "candidate_id": CANDIDATE_ID, "var_counts": dict(r1.VAR_COUNTS),
        "check_counts": dict(r1.CHECK_COUNTS), "E": r1.EDGE_TOTAL},
        "disclosure": {"syndrome_bits": 0, "tag_bits": 0,
                       "control_bits": 0, "interaction_bits": 0, "auth_bits": 0,
                       "per_block": 0},
        "population_split": {"CAL": "702..1725 consumed", "selection": "empty",
                             "confirmation": "2093..2156 key-disjoint"},
        "key_disjointness": "confirmation disjoint from CAL/VAL/V55-2M",
        "SECURITY_MODEL": "generic-only", "graph_seeds": list(GRAPH_SEEDS),
        "domain_namespace": r1.DOMAIN_NAMESPACE,
        "budgets": {"scientific_calls": SCI_CEILING, "setup_calls": SETUP_CEILING},
        "setup_calls": setup_calls, "evidence_files": list(EVIDENCE_FILES),
        "decoder_calls": 0,
        "authorization": "separate explicit grant required for --audit-only",
    }
    summary = {
        "schema": "g6_decide_r2_diag_summary_v1", "mode": "audit",
        "terminal": "AUDIT_COMPLETE",
        "arm_id": "A0", "prior_mode": "none", "max_iter": None,
        "attempted": 0, "accepted": 0, "exact": 0, "undetected": 0,
        "accepted_fraction": None, "exact_fraction": None, "FER_proxy": None,
        "disclosure_sum": 0, "k_sym_nominal": K_SYM_NOMINAL,
        "reconciled_net_bits": 0, "reconciled_rate": None,
        "beta_eff_empirical_primary": None,
        "beta_eff_empirical_l2_sensitivity": None,
        "H_frozen_primary": H_FROZEN, "H_L2_sensitivity": H_L2,
        "scientific_calls": 0, "setup_calls": setup_calls,
        "decoder_calls": int(guard["decoder_calls"]), "audit_blocks": len(records),
        "per_arm": {"A0": {"audited": len(records), "decoder_calls": 0,
                           "attempted": 0, "accepted": 0, "exact": 0,
                           "undetected": 0, "disclosure_sum": 0}},
        "diag_histograms": {"true_weight_hist": true_hist,
                            "truth_syn_weight_hist": syn_hist},
        "out_root": str(resolved)}
    assert summary["decoder_calls"] == 0  # counter-enforced, never decoded
    return {"resolved": resolved, "manifest": manifest, "records": records,
            "summary": summary}


def write_arm_root(bundle: dict) -> dict:
    """Persist one arm bundle (block_records.csv + summary.json + report.md).

    No manifest.json at arm level; the parent root holds manifest.json.
    report.md is optional evidence (verifier never requires it).
    """
    resolved = bundle["resolved"]
    resolved.mkdir(parents=True)
    with (resolved / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(BLOCK_COLUMNS))
        writer.writeheader()
        for row in bundle["records"]:
            writer.writerow({c: row.get(c, "") for c in BLOCK_COLUMNS})
    (resolved / "summary.json").write_text(
        json.dumps(bundle["summary"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = bundle["summary"]
    lines = ["# G6 DECIDE R2 DIAG report (%s)" % summary.get("arm_id", "?"), "",
             "- mode/prior/max_iter: `%s/%s/%s`"
             % (summary.get("arm_id"), summary.get("prior_mode"),
                summary.get("max_iter")),
             "- terminal: `%s`" % summary["terminal"],
             "- attempted/accepted/exact/undetected: %d/%d/%d/%d"
             % (summary.get("attempted", 0), summary.get("accepted", 0),
                summary.get("exact", 0), summary.get("undetected", 0)),
             "- decoder_calls: %d" % summary.get("decoder_calls", -1),
             "- audit_blocks: %d" % summary.get("audit_blocks", 0),
             "- disclosure_sum: %d" % summary.get("disclosure_sum", 0),
             "- diag_histograms: %s"
             % json.dumps(summary.get("diag_histograms", {}), sort_keys=True)]
    (resolved / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


PER_ARM_KEYS = ("attempted", "accepted", "exact", "undetected",
                "disclosure_sum", "decoder_calls", "audit_blocks",
                "terminal", "prior_mode", "max_iter")


def _per_arm_entry(summary: dict) -> dict:
    """Fixed honest-field projection of one arm summary (write == verify)."""
    return {k: summary.get(k) for k in PER_ARM_KEYS}


def _parent_terminal(t1: str, t2: str, t0: str, undet: int) -> str:
    if undet > 0:
        return "UNDETECTED_STOP"
    if t1 == "COMPLETE_128" and t2 == "COMPLETE_128" \
            and t0 == "AUDIT_COMPLETE":
        return "COMPLETE_256_AUDITED"
    return "ENGINEERING_BLOCKED"


def write_diag_root(parent_out: str, arm_bundles: dict) -> dict:
    """Assemble the frozen parent root: manifest+summary plus A1/A2/A0 subdirs.

    arm_bundles maps each of A1/A2/A0 to its run bundle. Fresh parent root
    only (refuse existing). Returns the parent summary.
    """
    if set(arm_bundles) != set(ARM_SUBDIRS):
        raise ValueError("PRE_EXECUTION_BLOCKED: diag root needs exactly "
                         "A1/A2/A0, got %r" % sorted(arm_bundles))
    resolved = d10r2.refuse_out_root(parent_out)  # probe only; creates nothing
    resolved.mkdir(parents=True)
    sums: dict[str, dict] = {}
    for arm in ARM_SUBDIRS:
        bundle = arm_bundles[arm]
        sub = resolved / arm
        summ = dict(bundle["summary"])
        summ["out_root"] = str(sub)
        write_arm_root({"resolved": sub, "manifest": bundle.get("manifest", {}),
                        "records": bundle["records"], "summary": summ})
        sums[arm] = summ
    s1, s2, s0 = sums["A1"], sums["A2"], sums["A0"]
    undet = int(s1["undetected"]) + int(s2["undetected"]) \
        + int(s0["undetected"])
    psum = {
        "schema": "g6_decide_r2_diag_parent_summary_v1",
        "terminal": _parent_terminal(str(s1["terminal"]), str(s2["terminal"]),
                                     str(s0["terminal"]), undet),
        "attempted": int(s1["attempted"]) + int(s2["attempted"]),
        "accepted": int(s1["accepted"]) + int(s2["accepted"]),
        "exact": int(s1["exact"]) + int(s2["exact"]),
        "undetected": undet,
        "disclosure_sum": int(s1["disclosure_sum"]) + int(s2["disclosure_sum"]),
        "decoder_calls": int(s1["decoder_calls"]) + int(s2["decoder_calls"]),
        "audit_blocks": int(s0["audit_blocks"]),
        "per_arm": {a: _per_arm_entry(sums[a]) for a in ARM_SUBDIRS},
        "arm_terminals": {a: sums[a]["terminal"] for a in ARM_SUBDIRS},
        "out_root": str(resolved)}
    pman = {
        "schema": "g6_decide_r2_diag_parent_manifest_v1",
        "change_id": CHANGE_ID, "cycle": CYCLE_ID,
        "frozen_argv": {"A1": FROZEN_COMMAND_A1, "A2": FROZEN_COMMAND_A2,
                        "A0": FROZEN_COMMAND_A0,
                        "verify": FROZEN_COMMAND_VERIFY},
        "arms": list(ARM_SUBDIRS),
        "graph_seeds": list(GRAPH_SEEDS),
        "domain_namespace": r1.DOMAIN_NAMESPACE,
        "budgets": {"scientific_calls": SCI_CEILING,
                    "setup_calls": SETUP_CEILING},
        "evidence_layout": "parent manifest.json+summary.json; A1/A2/A0 "
                           "subdirs block_records.csv+summary.json "
                           "(+report.md optional)",
        "out_root": str(resolved)}
    (resolved / "manifest.json").write_text(
        json.dumps(pman, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (resolved / "summary.json").write_text(
        json.dumps(psum, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return psum


def _to_bool(value) -> bool:
    return r1._to_bool(value)


def _check_decode_rows(rows: list[dict], arm_id: str, prior_mode: str,
                       max_iter: int, violations: list[str]) -> None:
    for row in rows:
        acc = _to_bool(row.get("protocol_accepted"))
        ex = _to_bool(row.get("verified_exact"))
        ud = _to_bool(row.get("undetected"))
        syn = _to_bool(row.get("syndrome_match"))
        tag = _to_bool(row.get("tag_match"))
        fin = _to_bool(row.get("finite"))
        if ex and not acc:
            violations.append("exact without accepted")
        if ud and (not acc or ex):
            violations.append("undetected merged")
        if acc and not (fin and syn and tag):
            violations.append("accepted without finite+syndrome+tag")
        if int(row.get("disclosure_bits", -1)) != r1.disclosed_bits(M):
            violations.append("disclosure != 5m+64")
        if int(row.get("syndrome_bits", -1)) != 5 * M \
                or int(row.get("tag_bits", -1)) != r1.TAG_BITS:
            violations.append("syndrome/tag split != 470/64")
        if int(row.get("control_bits", 0)) != 0 \
                or int(row.get("interaction_bits", 0)) != 0:
            violations.append("control/interaction != 0")
        if str(row.get("arm_id", "")) != arm_id:
            violations.append("arm_id != %s" % arm_id)
        if str(row.get("prior_mode", "")) != prior_mode:
            violations.append("prior_mode != %s" % prior_mode)
        if int(row.get("max_iter", -999)) != int(max_iter):
            violations.append("max_iter != %d" % int(max_iter))


def _verify_single_arm(path: Path) -> bool:
    """Verify one arm dir (block_records.csv + summary.json; report optional)."""
    try:
        summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
        rows = list(csv.DictReader((path / "block_records.csv").read_text(
            encoding="utf-8").splitlines()))
    except (OSError, ValueError, KeyError) as exc:
        print("VERIFY[%s] unreadable: %s" % (path, exc))
        return False
    violations: list[str] = []
    arm_id = str(summary.get("arm_id", ""))
    mode = str(summary.get("mode", ""))
    if arm_id not in ARM_SUBDIRS:
        violations.append("unknown arm_id %r" % arm_id)
    if mode == "audit" or arm_id == "A0":
        if mode != "audit" or arm_id != "A0":
            violations.append("A0 mode/arm mismatch")
        for row in rows:
            if str(row.get("outcome", "")) != "audit":
                violations.append("A0 outcome != audit")
            if _to_bool(row.get("attempted")) or _to_bool(row.get("undetected")) \
                    or _to_bool(row.get("verified_exact")) \
                    or _to_bool(row.get("protocol_accepted")):
                violations.append("A0 honest counts violated")
            if int(row.get("true_weight", -1)) < 0:
                violations.append("A0 true_weight missing")
        if int(summary.get("decoder_calls", -1)) != 0:
            violations.append("A0 summary decoder_calls != 0")
        if int(summary.get("attempted", -1)) != 0:
            violations.append("A0 attempted != 0")
        if int(summary.get("audit_blocks", -1)) != len(rows):
            violations.append("audit_blocks != nrows")
        hists = summary.get("diag_histograms", {})
        true_hist = {str(k): v for k, v in
                     sorted(Counter(int(x["true_weight"]) for x in rows).items())}
        syn_hist = {str(k): v for k, v in
                    sorted(Counter(int(x["residual"]) for x in rows).items())}
        if hists.get("true_weight_hist") != true_hist:
            violations.append("true_weight_hist != recomputed")
        if hists.get("truth_syn_weight_hist") != syn_hist:
            violations.append("truth_syn_weight_hist != recomputed")
        if summary.get("terminal") != "AUDIT_COMPLETE":
            violations.append("A0 terminal != AUDIT_COMPLETE")
    else:
        if mode != "decode" or arm_id not in ("A1", "A2"):
            violations.append("unknown mode/arm %r/%r" % (mode, arm_id))
            prior_mode, max_iter, flags_ok = "", -1, False
        else:
            prior_mode = str(summary.get("prior_mode", ""))
            max_iter = int(summary.get("max_iter", -1))
            flags_ok = True
            try:
                validate_diag_flags(prior_mode, max_iter)
            except ValueError:
                flags_ok = False
                violations.append("flags not admitted")
            # Frozen orthogonal combos only: A1=(uniform,90), A2=(model_f,300).
            if flags_ok and (prior_mode, max_iter) != (
                    FROZEN_A1 if arm_id == "A1" else FROZEN_A2):
                violations.append("arm/flag combo not frozen")
        if len(rows) != 128:
            violations.append("partial arm %d != 128" % len(rows))
        _check_decode_rows(rows, arm_id, prior_mode, max_iter, violations)
        attempted = len(rows)
        accepted = sum(1 for x in rows if _to_bool(x.get("protocol_accepted")))
        exact = sum(1 for x in rows if _to_bool(x.get("verified_exact")))
        undet = sum(1 for x in rows if _to_bool(x.get("undetected")))
        leak_sum = sum(int(x.get("disclosure_bits", 0)) for x in rows)
        if int(summary.get("attempted", -1)) != attempted:
            violations.append("attempted != recomputed")
        if int(summary.get("accepted", -1)) != accepted:
            violations.append("accepted != recomputed")
        if int(summary.get("exact", -1)) != exact:
            violations.append("exact != recomputed")
        if int(summary.get("undetected", -1)) != undet:
            violations.append("undetected != recomputed")
        if int(summary.get("disclosure_sum", -1)) != leak_sum:
            violations.append("disclosure_sum != recomputed")
        if int(summary.get("decoder_calls", -1)) != attempted:
            violations.append("decoder_calls != attempted")
        beta_p, beta_l = _beta_pair(attempted, leak_sum)
        if summary.get("beta_eff_empirical_primary") is None and beta_p is not None:
            violations.append("beta primary missing")
        elif beta_p is not None and abs(float(summary["beta_eff_empirical_primary"]) - beta_p) > 1e-12:
            violations.append("beta primary != recomputed")
        if abs(float(summary.get("beta_eff_empirical_l2_sensitivity", 0)) - beta_l) > 1e-12:
            violations.append("beta l2 != recomputed")
        if float(summary.get("H_frozen_primary", 0)) != H_FROZEN:
            violations.append("H_frozen != 3.347605")
        if float(summary.get("H_L2_sensitivity", 0)) != H_L2:
            violations.append("H_L2 != 3.222719884634378")
        resid_hist = {str(k): v for k, v in
                      sorted(Counter(int(x.get("residual", -999)) for x in rows).items())}
        if summary.get("diag_histograms", {}).get("residual_hist") != resid_hist:
            violations.append("residual_hist != recomputed")
        per = summary.get("per_arm", {}).get(arm_id, {})
        if (per.get("attempted"), per.get("accepted"), per.get("exact"),
                per.get("undetected"), per.get("disclosure_sum")) != \
                (attempted, accepted, exact, undet, leak_sum):
            violations.append("per_arm != recomputed")
        if undet > 0:
            violations.append("undetected>0 UNDETECTED_STOP")
        if summary.get("terminal") == "ENGINEERING_BLOCKED":
            violations.append("engineering-blocked root")
    print("VERIFY[%s] checked=%d violations=%d" % (arm_id or "?", len(rows),
                                                  len(violations)))
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    print("VERIFY[%s] %s" % (arm_id or "?", "PASS" if not violations else "FAIL"))
    return not violations


def _verify_parent(root: Path) -> bool:
    """Verify parent manifest/summary + recomputed triple aggregate."""
    violations: list[str] = []
    try:
        pman = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        psum = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("VERIFY parent unreadable: %s" % exc)
        return False
    if pman.get("frozen_argv") != {"A1": FROZEN_COMMAND_A1,
                                   "A2": FROZEN_COMMAND_A2,
                                   "A0": FROZEN_COMMAND_A0,
                                   "verify": FROZEN_COMMAND_VERIFY}:
        violations.append("parent frozen_argv != frozen A1/A2/A0/verify")
    if pman.get("arms") != list(ARM_SUBDIRS):
        violations.append("parent arms != [A1,A2,A0]")
    oks = {a: _verify_single_arm(root / a) for a in ARM_SUBDIRS}
    sums: dict[str, dict] = {}
    for a in ARM_SUBDIRS:
        try:
            sums[a] = json.loads((root / a / "summary.json").read_text(
                encoding="utf-8"))
        except (OSError, ValueError):
            violations.append("arm %s summary unreadable" % a)
    if len(sums) == len(ARM_SUBDIRS):
        s1, s2, s0 = sums["A1"], sums["A2"], sums["A0"]
        exp = {
            "attempted": int(s1["attempted"]) + int(s2["attempted"]),
            "accepted": int(s1["accepted"]) + int(s2["accepted"]),
            "exact": int(s1["exact"]) + int(s2["exact"]),
            "undetected": int(s1["undetected"]) + int(s2["undetected"])
            + int(s0["undetected"]),
            "disclosure_sum": int(s1["disclosure_sum"])
            + int(s2["disclosure_sum"]),
            "decoder_calls": int(s1["decoder_calls"]) + int(s2["decoder_calls"]),
            "audit_blocks": int(s0["audit_blocks"]),
            "terminal": _parent_terminal(str(s1["terminal"]),
                                         str(s2["terminal"]),
                                         str(s0["terminal"]),
                                         int(s1["undetected"])
                                         + int(s2["undetected"])
                                         + int(s0["undetected"])),
            "per_arm": {a: _per_arm_entry(sums[a]) for a in ARM_SUBDIRS},
            "arm_terminals": {a: sums[a]["terminal"] for a in ARM_SUBDIRS}}
        for key, value in exp.items():
            if psum.get(key) != value:
                violations.append("parent %s != recomputed aggregate" % key)
        if psum.get("terminal") == "ENGINEERING_BLOCKED":
            violations.append("engineering-blocked parent")
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    for a in ARM_SUBDIRS:
        print("VERIFY aggregate arm %s: %s" % (a, "PASS" if oks[a] else "FAIL"))
    ok = not violations and all(oks.values())
    print("VERIFY aggregate %s" % ("PASS" if ok else "FAIL"))
    return ok


def verify_diag_root(out_root: str) -> bool:
    """Verify one arm dir (CSV+summary) or the parent (manifest+summary+triple)."""
    root = Path(out_root)
    if not root.is_dir():
        print("VERIFY root missing: %s" % root)
        return False
    files = {p.name for p in root.iterdir() if p.is_file()}
    subs = {p.name for p in root.iterdir() if p.is_dir()}
    if "block_records.csv" in files and "summary.json" in files:
        return _verify_single_arm(root)
    if {"manifest.json", "summary.json"} <= files \
            and set(ARM_SUBDIRS) <= subs:
        return _verify_parent(root)
    print("VERIFY layout != arm-dir nor parent+triple: files=%s subs=%s"
          % (sorted(files), sorted(subs)))
    return False


def profile_only() -> dict:
    """Pre-decoder dry run on FAKE pool only: A1+A2 128-call plans, zero calls."""
    graphs = [build_graph(seed) for seed in GRAPH_SEEDS]
    admitted = sum(1 for g in graphs if g["admitted"])
    frames = r1.parse_frames(FROZEN_FRAMES)
    plan_a1 = r1.build_call_plan(frames)
    plan_a2 = r1.build_call_plan(frames)
    future = (ROOT / FUTURE_ROOT).resolve()
    setup = len(graphs) + 2
    sci = len(plan_a1) + len(plan_a2)
    return {
        "graphs": [{"seed": g["graph_seed"], "n": g["n"], "m": g["m"],
                    "E": g["E"], "admitted": g["admitted"],
                    "status": g["status"]} for g in graphs],
        "admitted": admitted, "total_graphs": len(graphs),
        "arms": {
            "A1": {"prior_mode": FROZEN_A1[0], "max_iter": FROZEN_A1[1],
                   "calls": len(plan_a1), "order": "frame->block->graph even/odd"},
            "A2": {"prior_mode": FROZEN_A2[0], "max_iter": FROZEN_A2[1],
                   "calls": len(plan_a2), "order": "frame->block->graph even/odd"}},
        "plan_calls": sci,
        "plan_order": "frame->block->graph even/odd",
        "budgets": {"scientific_calls": sci, "sci_ceiling": SCI_CEILING,
                    "setup_calls": setup, "setup_ceiling": SETUP_CEILING},
        "budget_ok": sci <= SCI_CEILING and setup <= SETUP_CEILING,
        "future_root": str(future), "future_root_absent": not future.exists(),
        "decoder_calls": 0, "model_f_loads": 0, "real_pool_reads": 0,
        "domain_namespace": r1.DOMAIN_NAMESPACE,
        "coefficient_namespace": r1.COEFF_NAMESPACE_TMPL % 2026094601,
        "frozen_argv": {"A1": FROZEN_COMMAND_A1, "A2": FROZEN_COMMAND_A2,
                        "A0": FROZEN_COMMAND_A0,
                        "verify": FROZEN_COMMAND_VERIFY},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="G6 DECIDE R2 DIAG thin runner")
    parser.add_argument("--registry", default=FROZEN_REGISTRY)
    parser.add_argument("--session", default=FROZEN_SESSION)
    parser.add_argument("--frames", default=FROZEN_FRAMES)
    parser.add_argument("--arm", default=ARM)
    parser.add_argument("--prior-root", default=FROZEN_PRIOR_ROOT)
    parser.add_argument("--r1-root", default=FROZEN_R1_ROOT)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--prior-mode", default=PRIOR_MODEL_F)
    parser.add_argument("--max-iter", default=90, type=int)
    parser.add_argument("--profile-only", action="store_true")
    parser.add_argument("--execute-real", action="store_true")
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--execution-authorized", action="store_true", default=False)
    return parser


def main(argv=None, *, adapters_override=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [n for n, f in (("--profile-only", args.profile_only),
                               ("--execute-real", args.execute_real),
                               ("--audit-only", args.audit_only),
                               ("--verify", args.verify)) if f]
    if len(selected) != 1:
        parser.error("exactly one of --profile-only/--execute-real/"
                     "--audit-only/--verify required")
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
        return 0
    if args.verify:
        if args.out_dir is None:
            parser.error("--verify requires --out-dir")
        return 0 if verify_diag_root(args.out_dir) else 1
    # --execute-real/--audit-only refuse without grant BEFORE anything (rc=2).
    if not args.execution_authorized:
        print("refusing %s without --execution-authorized "
              "(zero decoder calls)"
              % ("--audit-only" if args.audit_only else "--execute-real"),
              file=sys.stderr)
        return 2
    if args.out_dir is None:
        parser.error("--execute-real/--audit-only requires --out-dir")
    try:
        if args.audit_only:
            bundle = run_audit_batch(
                args.out_dir, args.r1_root, args.registry, args.session,
                args.frames, args.arm, adapters=adapters_override)
        else:
            prior_mode, max_iter = validate_diag_flags(args.prior_mode,
                                                       args.max_iter)
            bundle = run_diag_arm(
                args.out_dir, args.registry, args.session, args.frames,
                args.arm, args.prior_root, prior_mode, max_iter,
                adapters=adapters_override)
    except FileExistsError as exc:
        print("PRE_EXECUTION_BLOCKED existing root: %s" % exc, file=sys.stderr)
        return 2
    except ValueError as exc:
        if "PRE_EXECUTION_BLOCKED" in str(exc):
            print(str(exc), file=sys.stderr)
            return 2
        raise
    summary = write_arm_root(bundle)
    if summary.get("arm_id") == "A0":
        print("G6-DIAG audit_blocks=%d decoder_calls=%d"
              % (summary["audit_blocks"], summary["decoder_calls"]))
        return 0 if summary["terminal"] == "AUDIT_COMPLETE" else 1
    print("G6-DIAG arm=%s terminal=%s attempted=%d exact=%d accepted=%d "
          "undetected=%d" % (summary["arm_id"], summary["terminal"],
                             summary["attempted"], summary["exact"],
                             summary["accepted"], summary["undetected"]))
    return 0 if summary["terminal"] == "COMPLETE_128" else 1


if __name__ == "__main__":
    raise SystemExit(main())
