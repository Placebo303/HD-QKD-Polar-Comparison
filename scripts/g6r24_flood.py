"""R24 FLOOD single-arm runner — DECIDE-readiness (NOT execution).

R24b scope (frozen R24 packet, this session): readiness for the frozen
R24 packet — single flooding arm vs S1-shift 2/128 baseline, paired on
R9's EXACT 128 blocks (session 20260107_PPLN_1p5M, frames 2123..2186,
graphs 4720/4721 even-odd reused, shift prior eps=1e-4, cold 90-iters,
disclosure 564, T=64 tag, C/I/A=0). R24b makes ZERO real calls: no
decoder calls, no symbol reads, no UUID root.

- P-pop: R9's exact paired pool, frames 2123..2186 (64 frames -> 128
  blocks, frame->block order, even/odd graphs). Allowlist ONLY that
  window (deep key-gate by import, Pre-EXECUTE business).
- P-op: n128/m100/L020 lam_d2_0.20_d3_0.80, verbatim S7-arith sheet:
  E349, check {3:51,4:49}, var {2:35,3:93}, rate 0.21875. Same graphs
  4720/4721 as R9/S1 (reuse by import, no new construction).
- P-dec: SHIFT prior from CAL TRAIN counts_ab via S1's mechanism by
  import (load_shift_prior; eps asserted == 1e-4, never reimplemented);
  cold flooding single-pass, max_iter=90, field=None (same-field-as-S1),
  disclosure_i=5*rows+64=564, control=interaction=auth=0. Flooding call
  shape verbatim v35.decode_flooding_fftqspa(h, prior, syndrome,
  max_iter=90, field=None); NO damping/warm kwargs — passing them
  hard-fails (TypeError).
- P-acct: attempted/exact/accepted/undetected isolated; disclosure sums
  include failures; k_sym nominal 28 derived-only; beta derived-only
  (primary + L2 sensitivity, reported only, never gated); net_secret
  via R16 helper by import.
- P-gate (F-gates): exact>=6 FLOOD-HELPS / exact<=3 NO-FLOOD-GAIN /
  4-5 MARGINAL / undetected UNDETECTED_STOP absolute (fail-closed).
- P-bud: sci<=128/setup<=8; wall 1800+120s / RSS 2GiB / 1-proc / no-retry.
- P-cmd: flags below; --execute-real refuses without
  --execution-authorized (rc=2) BEFORE any root/bind/load; invalid
  --schedule refused with zero calls.
- P-tests: delta FAKE-fixture tests only (see tests/test_g6r24_flood.py).
- P-stop: any violation STOP + retain + single decision needed.
- P-auth: separate explicit grant; single invocation; no second attempt.
- P-bias: paired same 128 blocks/graphs/prior as S1; full window (no
  selection); ONLY schedule varies (layered->flooding); recorded in
  manifest bias_controls.

Reuse: S1/R9 binds by import (no copied kernels) — parse/graph/plan/
tag/decode adapters/verifier helpers/marginal prior/shift loader;
D10-R2 builder/admission/refusal; D16/v35 decoder kernel (lazy bind,
no duplicate); D7 schedule discriminator freeze string (read-only).

Forbidden: decoder calls on real data; symbol reads; creating the UUID
root before grant; editing frozen runners/tests; touching
src/experiments/tools/results/outputs_comparison/prior roots/R9/R20/S1
roots; commit/push.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import g6s1_shift as s1  # noqa: E402
from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as r2  # noqa: E402

# Frozen pins (fail fast if lineage drifts).
assert float(s1.FROZEN_EPS) == 1e-4
assert float(s1.DEFAULT_EPS) == 1e-4
assert int(s1.MAX_ITER) == 90
assert int(s1.N) == 128 and int(s1.M) == 100
assert tuple(s1.GRAPH_SEEDS) == (2026094720, 2026094721)
assert int(s1.TAG_BITS) == 64
assert s1.disclosed_bits(100) == 564

# Frozen identifiers (P-op/P-dec/P-pop/P-bud/P-cmd).
CHANGE_ID = "g6r24-flood"
CYCLE_ID = "G6R24-FLOOD"
N = s1.N
M = s1.M
Q = s1.Q
MAX_ITER = s1.MAX_ITER
TAG_BITS = s1.TAG_BITS  # T=64
H_FROZEN = s1.H_FROZEN
H_L2 = s1.H_L2
K_SYM_NOMINAL = s1.K_SYM_NOMINAL  # SUPERSEDED by net_secret_bits (R16 correction)
VAR_COUNTS = dict(s1.VAR_COUNTS)
CHECK_COUNTS = dict(s1.CHECK_COUNTS)
EDGE_TOTAL = s1.EDGE_TOTAL
ARM = s1.ARM
CANDIDATE_ID = s1.CANDIDATE_ID
GRAPH_SEEDS = tuple(s1.GRAPH_SEEDS)
DOMAIN_NAMESPACE = s1.DOMAIN_NAMESPACE
COEFF_NAMESPACE_TMPL = s1.COEFF_NAMESPACE_TMPL
FROZEN_REGISTRY = s1.FROZEN_REGISTRY
FROZEN_SESSION = s1.FROZEN_SESSION
FROZEN_FRAMES = s1.FROZEN_FRAMES
FROZEN_PRIOR_ROOT = s1.FROZEN_PRIOR_ROOT
PRIOR_MODE = s1.PRIOR_MODE
FROZEN_EPS = float(s1.FROZEN_EPS)
SCHEDULE = "FLOODING"
SCHEDULE_TOKEN = "FLOODING-90-cold"
FLOOD_CALL_SHAPE = ("v35.decode_flooding_fftqspa(h, prior, syndrome, "
                    "max_iter=90, field=None)")
FUTURE_ROOT_UUID = "249d335a-1c8a-4ad5-9c92-cfa93c7b9684"
FUTURE_ROOT = "workspace/g6r24_flood_" + FUTURE_ROOT_UUID
SCI_CEILING = 128
SETUP_CEILING = 8
F_GATE_HELP_GE = 6
F_GATE_NOGAIN_LE = 3
BASELINE_S1_EXACT = 2  # stated S1-shift 2/128
BASELINE_S1_ATTEMPTED = 128
EVIDENCE_FILES = tuple(s1.EVIDENCE_FILES)
BLOCK_COLUMNS = tuple(s1.BLOCK_COLUMNS)
FROZEN_COMMAND = (
    ".venv/bin/python scripts/g6r24_flood.py --execute-real "
    "--execution-authorized --registry %s --session %s --frames %s "
    "--arm %s --prior-root %s --schedule %s --out-dir %s"
    % (FROZEN_REGISTRY, FROZEN_SESSION, FROZEN_FRAMES, ARM,
       FROZEN_PRIOR_ROOT, SCHEDULE, FUTURE_ROOT))

# Direct binds reused by import (no copies, no duplicate kernels).
parse_frames = s1.parse_frames
disclosed_bits = s1.disclosed_bits
net_secret_bits = s1.net_secret_bits
_to_bool = s1._to_bool
build_call_plan = s1.build_call_plan
_pre_execute_check = s1._pre_execute_check
marginal_l2_prior = s1.marginal_l2_prior
_hard_fail_oracle_app = s1._hard_fail_oracle_app
load_shift_prior = s1.load_shift_prior
build_graph = s1.build_graph
_candidate_tag = s1._candidate_tag


def validate_schedule(schedule) -> str:
    """Allowlist gate: ONLY 'FLOODING'; else refuse (zero calls)."""
    if isinstance(schedule, bool):
        raise ValueError("schedule %r not frozen FLOODING" % (schedule,))
    if str(schedule) != SCHEDULE:
        raise ValueError("schedule %r not frozen FLOODING" % (schedule,))
    return SCHEDULE


def f_gate(exact: int, undetected: int) -> str:
    """F-decision gate on absolute exact (paired lift reported separately)."""
    if int(undetected) > 0:
        return "UNDETECTED_STOP"
    if int(exact) >= F_GATE_HELP_GE:
        return "FLOOD-HELPS"
    if int(exact) <= F_GATE_NOGAIN_LE:
        return "NO-FLOOD-GAIN"
    return "MARGINAL"  # 4-5


def run_one_block_flood(graph: dict, prior: np.ndarray, syndrome: np.ndarray,
                        ref_tag: bytes, truth_u2: np.ndarray, entry: dict,
                        decode_fn, syndrome_fn, call_idx: int) -> dict:
    """Single-pass cold flooding decode; truth used ONLY post-decision."""
    if graph.get("dense") is None or not bool(graph.get("admitted")):
        raise r2.StructureNotAdmitted("non-admitted R24 graph")
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
        "syndrome_bits": 5 * M, "tag_bits": TAG_BITS, "control_bits": 0,
        "interaction_bits": 0, "auth_bits": 0,
        "disclosure_bits": disclosed_bits(M), "iters": -1, "residual": -1,
        "provenance": "", "wall_s": 0.0, "crash": False, "error": ""}
    try:
        # Verbatim flooding call shape: NO damping/warm kwargs.
        result = decode_fn(H, prior, syn, max_iter=MAX_ITER, field=None)
        x_hat = np.asarray(result.x_hat, dtype=np.int64).ravel()
        prov = str(getattr(result, "belief_provenance", "") or "")
        if "ORACLE" in prov.upper() or "APP" in prov.upper():
            raise ValueError("ORACLE/APP provenance on real path: %r" % prov)
        finite = bool(x_hat.shape == (N,) and np.all((x_hat >= 0) & (x_hat < 32))
                      and 0 <= int(result.iterations) <= MAX_ITER
                      and np.all(np.isfinite(prior)))
        syn_match = bool(np.array_equal(np.asarray(syndrome_fn(H, x_hat)), syn))
        tag_match = bool(_candidate_tag(x_hat) == bytes(ref_tag))
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
        assert (not exact) or accepted
        assert (not undet) or (accepted and not exact)
        return rec
    except Exception as exc:  # retained crash, never retried
        rec.update({"crash": True, "error": repr(exc)[:300],
                    "outcome": "attempted",
                    "wall_s": time.perf_counter() - t0})
        return rec


def bind_production_adapters():
    """Lazy production bind (flooding decoder + syndrome + shift loader), zero calls."""
    import inspect as _inspect
    from comparison_bench.formal_ir import v35_algorithm_development as v35

    def _req(fn, params, name):
        if not callable(fn):
            raise TypeError("adapter %r not callable" % name)
        missing = [p for p in params if p not in _inspect.signature(fn).parameters]
        if missing:
            raise TypeError("adapter %r lacks %s" % (name, missing))
        return fn
    target = _req(v35.decode_flooding_fftqspa,
                  ["h_matrix", "priors", "syndromes", "max_iter", "field"],
                  "decode_fn")
    sig_params = list(_inspect.signature(target).parameters.keys())
    if "damping_alpha" in sig_params or "warm_beliefs" in sig_params:
        raise TypeError("flooding must not carry damping/warm params: %r" % sig_params)
    syndrome_fn = _req(v35.syndrome_of_gf32, ["matrix", "vector"], "syndrome_fn")

    def flood_decode(h_matrix, priors, syndromes, max_iter=MAX_ITER,
                     field=None, **kw):
        if "damping_alpha" in kw or "warm_beliefs" in kw:
            raise TypeError("flooding takes no damping/warm kwargs")
        return target(h_matrix, priors, syndromes, max_iter=max_iter, field=field)

    flood_decode.target = target  # type: ignore[attr-defined]
    flood_decode.call_shape = FLOOD_CALL_SHAPE  # type: ignore[attr-defined]

    def load_prior_fn(prior_root: str):
        return load_shift_prior(prior_root, FROZEN_EPS)

    return {"decode_fn": flood_decode, "syndrome_fn": syndrome_fn,
            "load_prior_fn": load_prior_fn}


def run_authorized_batch(out_root: str, registry: str, session_id: str,
                         frames_spec: str, arm: str, prior_root: str,
                         schedule: str = SCHEDULE, *,
                         adapters=None, reader_override=None) -> dict:
    """Execute frozen 128-call flooding matrix; returns bundle (writes separately)."""
    schedule = validate_schedule(schedule)  # first: zero-call refusal
    resolved = r2.refuse_out_root(out_root)  # probe only; creates nothing
    frames = _pre_execute_check(registry, session_id, frames_spec, arm, prior_root)
    plan = build_call_plan(frames)
    if adapters is None:
        adapters = bind_production_adapters()
    else:
        adapters = dict(adapters)
    _hard_fail_oracle_app(adapters)
    for key in ("decode_fn", "syndrome_fn", "load_prior_fn"):
        if adapters.get(key) is None:
            raise ValueError("adapters %s must be injected" % key)
    decode_fn, syndrome_fn = adapters["decode_fn"], adapters["syndrome_fn"]
    p_f = adapters["load_prior_fn"](prior_root)
    graphs = {}
    for seed in GRAPH_SEEDS:
        graph = adapters.get("build_fn", build_graph)(seed) \
            if "build_fn" in adapters else build_graph(seed)
        if not bool(graph.get("admitted")):
            raise RuntimeError("graph %r not admitted; ENGINEERING_BLOCKED" % seed)
        graphs[int(seed)] = graph
    setup_calls = len(graphs) + 2  # graphs + plan + manifest
    if setup_calls > SETUP_CEILING:
        raise RuntimeError("setup %d > ceiling %d" % (setup_calls, SETUP_CEILING))
    import pandas as pd
    session = [s for s in json.loads((ROOT / registry).read_text())["sessions"]
               if s["session_id"] == session_id][0]
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
        prior = marginal_l2_prior(p_f, bob_block)
        graph = graphs[int(entry["graph_seed"])]
        H = np.asarray(graph["dense"], dtype=np.uint8)
        syn = np.asarray(syndrome_fn(H, truth_u2), dtype=np.uint8)
        ref_tag = _candidate_tag(truth_u2)
        rec = run_one_block_flood(graph, prior, syn, ref_tag, truth_u2,
                                  {**entry, "session_id": session_id},
                                  decode_fn, syndrome_fn, entry["call_idx"])
        records.append(rec)
        if rec["undetected"]:
            break  # UNDETECTED_STOP absolute (fail-closed)
    if len(records) > SCI_CEILING:
        raise RuntimeError("scientific calls exceed ceiling")
    terminal = "UNDETECTED_STOP" if any(r["undetected"] for r in records) \
        else ("COMPLETE_128" if len(records) == 128 else "ENGINEERING_BLOCKED")
    attempted = len(records)
    accepted = sum(1 for r in records if r["protocol_accepted"])
    exact = sum(1 for r in records if r["verified_exact"])
    undet = sum(1 for r in records if r["undetected"])
    leak_sum = sum(int(r["disclosure_bits"]) for r in records)
    denom_primary = attempted * N * H_FROZEN if attempted else None
    denom_l2 = attempted * N * H_L2 if attempted else None
    beta_primary = (1.0 - leak_sum / denom_primary) if denom_primary else None
    beta_l2 = (1.0 - leak_sum / denom_l2) if denom_l2 else None
    reconciled = exact * K_SYM_NOMINAL * 5  # SUPERSEDED by net_secret_bits (R16 correction)
    net_secret = net_secret_bits(accepted, leak_sum, N)
    gate = f_gate(exact, undet)
    lift = int(exact) - int(BASELINE_S1_EXACT)
    manifest = {
        "schema": "g6r24_flood_manifest_v1", "change_id": CHANGE_ID,
        "cycle": CYCLE_ID, "command": FROZEN_COMMAND,
        "registry": registry, "session_id": session_id, "frames": frames_spec,
        "arm": arm, "candidate_id": CANDIDATE_ID, "prior_root": prior_root,
        "prior": {"mode": PRIOR_MODE, "eps": FROZEN_EPS,
                  "source": "CAL TRAIN counts_ab shift-delta (counts_ab only)"},
        "schedule": schedule, "schedule_token": SCHEDULE_TOKEN,
        "call_shape": FLOOD_CALL_SHAPE,
        "out_root": str(resolved), "operating_point": {"n": N, "m": M, "arm": ARM,
        "candidate_id": CANDIDATE_ID, "var_counts": dict(VAR_COUNTS),
        "check_counts": dict(CHECK_COUNTS), "E": EDGE_TOTAL},
        "decoder": {"adapter": "v35.decode_flooding_fftqspa",
                    "call_shape": FLOOD_CALL_SHAPE,
                    "max_iter": MAX_ITER, "field": None,
                    "schedule": "cold flooding single-pass",
                    "schedule_token": SCHEDULE_TOKEN},
        "disclosure": {"syndrome_bits": 5 * M, "tag_bits": TAG_BITS,
                       "control_bits": 0, "interaction_bits": 0, "auth_bits": 0,
                       "per_block": disclosed_bits(M)},
        "population_split": {"CAL": "702..1725 consumed", "selection": "empty",
                             "confirmation": "2123..2186 key-disjoint (paired with R9/S1)"},
        "key_disjointness": "confirmation disjoint from CAL/VAL",
        "SECURITY_MODEL": "generic-only", "graph_seeds": list(GRAPH_SEEDS),
        "coefficient_namespace": COEFF_NAMESPACE_TMPL % 2026094720,
        "domain_namespace": DOMAIN_NAMESPACE,
        "f_gates": {"help_ge": F_GATE_HELP_GE, "nogain_le": F_GATE_NOGAIN_LE,
                    "marginal": "4-5",
                    "rule": "exact>=6 FLOOD-HELPS / exact<=3 NO-FLOOD-GAIN / "
                            "4-5 MARGINAL / undetected UNDETECTED_STOP"},
        "baseline_s1": {"exact": BASELINE_S1_EXACT,
                        "attempted": BASELINE_S1_ATTEMPTED,
                        "note": "S1-shift 2/128 stated; paired lift reported only"},
        "bias_controls": {
            "paired_blocks": "2123..2186 both arms + baseline",
            "paired_graphs": list(GRAPH_SEEDS),
            "paired_prior": {"mode": PRIOR_MODE, "eps": FROZEN_EPS},
            "selection": "full window, no subsampling",
            "varied": "schedule ONLY (layered->flooding)"},
        "budgets": {"scientific_calls": SCI_CEILING, "setup_calls": SETUP_CEILING},
        "setup_calls": setup_calls, "evidence_files": list(EVIDENCE_FILES),
        "authorization": "separate explicit grant required for --execute-real",
    }
    summary = {
        "schema": "g6r24_flood_summary_v1", "terminal": terminal,
        "f_gate": gate, "schedule": schedule, "schedule_token": SCHEDULE_TOKEN,
        "prior_mode": PRIOR_MODE, "prior_eps": FROZEN_EPS,
        "attempted": attempted, "accepted": accepted, "exact": exact,
        "undetected": undet, "accepted_fraction": (accepted / attempted) if attempted else None,
        "exact_fraction": (exact / attempted) if attempted else None,
        "FER_proxy": ((attempted - exact) / attempted) if attempted else None,
        "disclosure_sum": leak_sum, "k_sym_nominal": K_SYM_NOMINAL,
        "reconciled_net_bits": reconciled,
        "net_secret_bits": net_secret,
        "reconciled_rate": (reconciled / (attempted * N * 5)) if attempted else None,
        "beta_eff_empirical_primary": beta_primary,
        "beta_eff_empirical_l2_sensitivity": beta_l2,
        "H_frozen_primary": H_FROZEN, "H_L2_sensitivity": H_L2,
        "baseline_s1_exact": BASELINE_S1_EXACT, "paired_lift": lift,
        "scientific_calls": attempted, "setup_calls": setup_calls,
        "out_root": str(resolved)}
    return {"resolved": resolved, "manifest": manifest, "records": records,
            "summary": summary}


def write_batch_root(bundle: dict) -> dict:
    """Persist bundle to fresh root (never overwrite)."""
    resolved = bundle["resolved"]
    resolved.mkdir(parents=True)
    (resolved / "manifest.json").write_text(
        json.dumps(bundle["manifest"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (resolved / "block_records.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(BLOCK_COLUMNS))
        writer.writeheader()
        for row in bundle["records"]:
            writer.writerow({c: row.get(c, "") for c in BLOCK_COLUMNS})
    (resolved / "summary.json").write_text(
        json.dumps(bundle["summary"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = bundle["summary"]
    lines = ["# R24 FLOOD m100 report", "",
             "- terminal: `%s`" % summary["terminal"],
             "- f_gate: `%s`" % summary["f_gate"],
             "- schedule: `%s` (%s)"
             % (summary["schedule"], summary["schedule_token"]),
             "- prior: `%s` (eps=%s)"
             % (summary["prior_mode"], summary["prior_eps"]),
             "- attempted/exact/accepted/undetected: %d/%d/%d/%d"
             % (summary["attempted"], summary["exact"],
                summary["accepted"], summary["undetected"]),
             "- paired_lift vs S1-shift 2/128: %d" % summary["paired_lift"],
             "- disclosure_sum: %d" % summary["disclosure_sum"],
             "- beta_primary: %s" % summary["beta_eff_empirical_primary"],
             "- net_secret_bits: %d" % summary["net_secret_bits"]]
    (resolved / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def verify_root(out_root: str) -> bool:
    """Read-only recomputation; FAIL on partial/engineering-blocked."""
    root = Path(out_root)
    if not root.is_dir():
        print("VERIFY root missing: %s" % root)
        return False
    names = sorted(p.name for p in root.iterdir())
    if names != sorted(EVIDENCE_FILES):
        print("VERIFY files mismatch: %s" % names)
        return False
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    if manifest.get("command") != FROZEN_COMMAND:
        print("VERIFY command != frozen")
        return False
    if (manifest.get("prior") or {}).get("mode") != PRIOR_MODE:
        print("VERIFY prior mode != shift-delta")
        return False
    if abs(float((manifest.get("prior") or {}).get("eps", -1)) - FROZEN_EPS) > 0:
        print("VERIFY prior eps != frozen")
        return False
    if manifest.get("schedule") != SCHEDULE:
        print("VERIFY schedule != FLOODING")
        return False
    if not str(manifest.get("schedule_token", "")).startswith("FLOODING-"):
        print("VERIFY schedule_token != FLOODING-*")
        return False
    if manifest.get("call_shape") != FLOOD_CALL_SHAPE:
        print("VERIFY call_shape != frozen flooding shape")
        return False
    dec = manifest.get("decoder") or {}
    if dec.get("adapter") != "v35.decode_flooding_fftqspa":
        print("VERIFY decoder adapter != flooding")
        return False
    if dec.get("call_shape") != FLOOD_CALL_SHAPE:
        print("VERIFY decoder call_shape != frozen")
        return False
    if int(dec.get("max_iter", -1)) != MAX_ITER:
        print("VERIFY decoder max_iter != 90")
        return False
    if dec.get("field") is not None:
        print("VERIFY decoder field != None (same-field-as-S1)")
        return False
    if not str(dec.get("schedule_token", "")).startswith("FLOODING-"):
        print("VERIFY decoder schedule_token != FLOODING-*")
        return False
    if "damping_alpha" in dec or "warm_beliefs" in dec:
        print("VERIFY decoder carries damping/warm (forbidden)")
        return False
    if summary.get("schedule") != SCHEDULE:
        print("VERIFY summary schedule != FLOODING")
        return False
    if not str(summary.get("schedule_token", "")).startswith("FLOODING-"):
        print("VERIFY summary schedule_token != FLOODING-*")
        return False
    if summary.get("prior_mode") != PRIOR_MODE:
        print("VERIFY summary prior_mode != shift-delta")
        return False
    if abs(float(summary.get("prior_eps", -1)) - FROZEN_EPS) > 0:
        print("VERIFY summary prior_eps != frozen")
        return False
    rows = list(csv.DictReader((root / "block_records.csv").read_text(encoding="utf-8").splitlines()))
    violations: list[str] = []
    if len(rows) not in (128,):
        if not any(_to_bool(r.get("undetected")) for r in rows):
            violations.append("partial root %d != 128" % len(rows))
    attempted = len(rows)
    accepted = sum(1 for r in rows if _to_bool(r.get("protocol_accepted")))
    exact = sum(1 for r in rows if _to_bool(r.get("verified_exact")))
    undet = sum(1 for r in rows if _to_bool(r.get("undetected")))
    for r in rows:
        acc, ex, ud = _to_bool(r.get("protocol_accepted")), _to_bool(r.get("verified_exact")), _to_bool(r.get("undetected"))
        syn, tag, fin = _to_bool(r.get("syndrome_match")), _to_bool(r.get("tag_match")), _to_bool(r.get("finite"))
        if ex and not acc:
            violations.append("exact without accepted")
        if ud and (not acc or ex):
            violations.append("undetected merged")
        if acc and not (fin and syn and tag):
            violations.append("accepted without finite+syndrome+tag")
        if int(r.get("disclosure_bits", -1)) != disclosed_bits(M):
            violations.append("disclosure != 5m+64")
        if int(r.get("syndrome_bits", -1)) != 5 * M or int(r.get("tag_bits", -1)) != TAG_BITS:
            violations.append("syndrome/tag split != 500/64")
        if int(r.get("control_bits", 0)) != 0 or int(r.get("interaction_bits", 0)) != 0:
            violations.append("control/interaction != 0")
        if int(r.get("auth_bits", 0)) != 0:
            violations.append("auth != 0")
    leak_sum = sum(int(r.get("disclosure_bits", 0)) for r in rows)
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
    if summary.get("net_secret_bits", None) is None or int(summary.get("net_secret_bits")) != net_secret_bits(accepted, leak_sum, N):
        violations.append("net_secret_bits != recomputed")
    denom_p = attempted * N * H_FROZEN if attempted else 0
    denom_l = attempted * N * H_L2 if attempted else 0
    beta_p = (1.0 - leak_sum / denom_p) if denom_p else None
    beta_l = (1.0 - leak_sum / denom_l) if denom_l else 0
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
    if summary.get("f_gate") != f_gate(exact, undet):
        violations.append("f_gate != recomputed")
    if int(summary.get("baseline_s1_exact", -1)) != BASELINE_S1_EXACT:
        violations.append("baseline_s1_exact != 2")
    if int(summary.get("paired_lift", -999999)) != exact - BASELINE_S1_EXACT:
        violations.append("paired_lift != exact - 2")
    if undet > 0:
        violations.append("undetected>0 UNDETECTED_STOP")
    if summary.get("terminal") == "ENGINEERING_BLOCKED":
        violations.append("engineering-blocked root")
    print("VERIFY checked=%d violations=%d" % (attempted, len(violations)))
    for violation in violations[:20]:
        print("  VIOLATION %s" % violation)
    ok = not violations
    print("VERIFY %s" % ("PASS" if ok else "FAIL"))
    return ok


def profile_only(schedule: str = SCHEDULE) -> dict:
    """Pre-decoder dry run on FAKE pool only: 128-call plan, zero decoder."""
    schedule = validate_schedule(schedule)  # refusal before any I/O
    graphs = [build_graph(seed) for seed in GRAPH_SEEDS]
    admitted = sum(1 for g in graphs if g["admitted"])
    frames = parse_frames(FROZEN_FRAMES)
    plan = build_call_plan(frames)
    future = (ROOT / FUTURE_ROOT).resolve()
    # Byte-identical baseline asserts by import (code only, zero pool reads).
    import g6r9_confirm as _r9
    import g6r20_uniform as _r20
    r9_match = (tuple(_r9.GRAPH_SEEDS) == GRAPH_SEEDS and _r9.N == N
                and _r9.M == M and _r9.disclosed_bits(100) == 564)
    r20_match = (tuple(_r20.GRAPH_SEEDS) == GRAPH_SEEDS and _r20.N == N
                 and _r20.M == M and _r20.TAG_BITS == TAG_BITS)
    s1_match = (tuple(s1.GRAPH_SEEDS) == GRAPH_SEEDS and s1.FROZEN_EPS == FROZEN_EPS
                and s1.PRIOR_MODE == PRIOR_MODE)
    return {
        "graphs": [{"seed": g["graph_seed"], "n": g["n"], "m": g["m"],
                    "E": g["E"], "admitted": g["admitted"],
                    "status": g["status"]} for g in graphs],
        "admitted": admitted, "total_graphs": len(graphs),
        "plan_calls": len(plan),
        "plan_order": "frame->block->graph even/odd",
        "schedule": schedule, "schedule_token": SCHEDULE_TOKEN,
        "call_shape": FLOOD_CALL_SHAPE,
        "prior_mode": PRIOR_MODE, "prior_eps": FROZEN_EPS,
        "f_gates": {"help_ge": F_GATE_HELP_GE, "nogain_le": F_GATE_NOGAIN_LE,
                    "marginal": "4-5"},
        "baselines": {"s1_shift_exact": BASELINE_S1_EXACT,
                      "s1_shift_attempted": BASELINE_S1_ATTEMPTED,
                      "s1_match": bool(s1_match),
                      "r9_match": bool(r9_match),
                      "r20_match": bool(r20_match),
                      "note": "stated + byte-identical by import; zero pool reads"},
        "budgets": {"scientific_calls": len(plan), "sci_ceiling": SCI_CEILING,
                    "setup_calls": len(graphs) + 2, "setup_ceiling": SETUP_CEILING},
        "budget_ok": len(plan) <= SCI_CEILING and (len(graphs) + 2) <= SETUP_CEILING,
        "future_root": str(future), "future_root_absent": not future.exists(),
        "decoder_calls": 0, "model_f_loads": 0, "real_pool_reads": 0,
        "symbol_reads": 0,
        "domain_namespace": DOMAIN_NAMESPACE,
        "coefficient_namespace": COEFF_NAMESPACE_TMPL % 2026094720,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="R24 FLOOD m100 thin runner")
    parser.add_argument("--registry", default=FROZEN_REGISTRY)
    parser.add_argument("--session", default=FROZEN_SESSION)
    parser.add_argument("--frames", default=FROZEN_FRAMES)
    parser.add_argument("--arm", default=ARM)
    parser.add_argument("--prior-root", default=FROZEN_PRIOR_ROOT)
    parser.add_argument("--schedule", default=SCHEDULE)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--profile-only", action="store_true")
    parser.add_argument("--execute-real", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--execution-authorized", action="store_true", default=False)
    return parser


def main(argv=None, *, adapters_override=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = [n for n, f in (("--profile-only", args.profile_only),
                               ("--execute-real", args.execute_real),
                               ("--verify", args.verify)) if f]
    if len(selected) != 1:
        parser.error("exactly one of --profile-only/--execute-real/--verify required")
    try:
        schedule = validate_schedule(args.schedule)
    except ValueError as exc:
        parser.error(str(exc))
    if args.profile_only:
        print(json.dumps(profile_only(schedule), indent=2, sort_keys=True))
        return 0
    if args.verify:
        if args.out_dir is None:
            parser.error("--verify requires --out-dir")
        return 0 if verify_root(args.out_dir) else 1
    # --execute-real refuses without grant BEFORE any root/bind/load (rc=2).
    if not args.execution_authorized:
        print("refusing --execute-real without --execution-authorized "
              "(zero decoder calls)", file=sys.stderr)
        return 2
    if args.out_dir is None:
        parser.error("--execute-real requires --out-dir")
    try:
        bundle = run_authorized_batch(
            args.out_dir, args.registry, args.session, args.frames,
            args.arm, args.prior_root, schedule, adapters=adapters_override)
    except FileExistsError as exc:
        print("PRE_EXECUTION_BLOCKED existing root: %s" % exc, file=sys.stderr)
        return 2
    except ValueError as exc:
        if "PRE_EXECUTION_BLOCKED" in str(exc):
            print(str(exc), file=sys.stderr)
            return 2
        raise
    summary = write_batch_root(bundle)
    print("R24 terminal=%s f_gate=%s attempted=%d exact=%d accepted=%d undetected=%d lift=%d"
          % (summary["terminal"], summary["f_gate"], summary["attempted"], summary["exact"],
             summary["accepted"], summary["undetected"], summary["paired_lift"]))
    return 0 if summary["terminal"] == "COMPLETE_128" else 1


if __name__ == "__main__":
    raise SystemExit(main())
