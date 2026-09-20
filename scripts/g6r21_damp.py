"""R21 DAMP ladder runner — DECIDE-readiness (NOT execution).

R21b scope (frozen R21 packet, this session): readiness for the frozen R21
packet — damping ladder {0.5, 0.8} vs S1-shift 2/128 baseline, paired on
R9's exact 128 blocks (session 20260107_PPLN_1p5M, frames 2123..2186),
per-arm lift gate >= 6 vs baseline, sci<=256/setup<=8. R21b makes ZERO
real calls: no decoder calls, no symbol reads, no UUID root.

Execution shape (frozen): the S0 operating point ONLY — single-pass m100
(S1-shift point: graphs 4720/4721, shift prior eps=1e-4, cold 90-iters,
disclosure 564, T=64 tag, C/I/A=0). ONLY damping_alpha varies across
arms (0.5 / 0.8 new; 1.0 cold-default byte-identical path delegating to
frozen behavior, i.e. S1's frozen command holds for 1.0).

- P-pop: R9's exact paired pool, frames 2123..2186 (64 frames -> 128
  blocks, frame->block order, even/odd graphs). Allowlist ONLY that
  window (deep key-gate by import, Pre-EXECUTE business).
- P-op: n128/m100/L020, verbatim S7-arith sheet (E349, check {3:51,4:49},
  var {2:35,3:93}, rate 0.21875); same m100 graphs 4720/4721 as R9/S1
  (reuse by import, no new construction).
- P-dec: SHIFT prior from CAL TRAIN counts_ab via S1's built prior
  MECHANISM by import (load_shift_prior; eps asserted == 1e-4, never
  reimplemented here); cold single-pass; per-stage decode primitive is
  R11's run_one_stage by import (frozen damping call-site); damping
  1.0 passes the adapter decode through untouched (frozen kwargs),
  0.5/0.8 override ONLY the damping_alpha kwarg. Stage-m gate enforces
  S0 (m==100 in frozen R11 STAGE_MS); blind same-row retry forbidden
  (single stage by construction).
- P-acct: final-prefix disclosure via R11's helper by import
  (5*100+64=564, tag once, C/I/A=0); k_sym nominal 28 derived-only;
  beta derived-only (primary + L2 sensitivity, reported only).
- P-stop: UNDETECTED_STOP absolute (retain all, terminal); isolation:
  exact subset of accepted, undetected never merged.
- P-pair: primary paired baseline F imported READ-ONLY from the S1
  root (zero decode calls asserted; byte-identical post-import
  asserted); paired lift = arm_exact - F; lift gate >= 6 per arm.
- P-bud: sci<=256 (128 single-pass calls) / setup<=8.
- P-bias: paired same 128 blocks/graphs/prior across arms and
  baseline; full window (no selection); ONLY damping varies; recorded
  in manifest bias_controls.
- P-cmd: flags below; --execute-real refuses without
  --execution-authorized (rc=2) before any root/bind/load; invalid
  damping refused with zero calls.
- P-auth: separate explicit grant required; single invocation per arm.

Lineage (all by import, no copied kernels): R9 binds (parse/plan/tag/
decode adapters/verifier helpers/marginal prior/net_secret) via S1;
shift prior mechanism + graphs + plan + gate via S1; staged-loop stage
primitive + final-prefix accounting + honest-baseline import via R11;
decoder/syndrome/PEG/v10 kernels stay imported (v35, r2, common).

Forbidden: decoder calls on real data; symbol reads; creating the UUID
roots; editing frozen files; protected writes; commit/push.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import g6s1_shift as s1  # noqa: E402
import g6r11_adaptive as r11  # noqa: E402
from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as r2  # noqa: E402

# Frozen pins (fail fast if lineage drifts).
assert float(s1.FROZEN_EPS) == 1e-4
assert float(s1.DEFAULT_EPS) == 1e-4
assert tuple(r11.STAGE_MS) == (100, 108, 120)
assert tuple(r11.STAGE_IDS) == ("S0", "S1", "S2")
assert float(r11.DAMPING) == 1.0
assert tuple(s1.GRAPH_SEEDS) == (2026094720, 2026094721)

# Frozen identifiers (P-op/P-dec/P-pop/P-bud/P-cmd/P-pair/P-bias).
CHANGE_ID = "g6r21-damp"
CYCLE_ID = "G6R21-DAMP"
N = s1.N
M = s1.M
Q = s1.Q
MAX_ITER = s1.MAX_ITER
TAG_BITS = s1.TAG_BITS  # T=64
H_FROZEN = s1.H_FROZEN
H_L2 = s1.H_L2
K_SYM_NOMINAL = s1.K_SYM_NOMINAL  # SUPERSEDED by net_secret_bits (R16 correction): k-based retained double-charges parity; see V72P3R16-CORRECTION/
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
# Damping ladder: new arms + cold default (byte-identical frozen path).
DAMPING_ARMS = (0.5, 0.8)
COLD_DEFAULT_DAMPING = 1.0
ALLOWED_DAMPING = (0.5, 0.8, 1.0)
# S0 operating point (S1-shift point); the staged 100/108/120 set is the
# frozen R11 lineage reference — R21 executes S0 only, gated below.
STAGE_ID = "S0"
STAGE_M = 100
BASELINE_ROOT = "workspace/g6s1_shift_4105cfc2-3bbb-444a-9283-31403d43b7ff"
FUTURE_ROOTS = {
    0.5: "workspace/g6r21_damp_9f43bc04-0b0b-44a0-a0f9-3b66329c272f",
    0.8: "workspace/g6r21_damp_8dbeced5-7d77-478f-9dc6-0b992500bbcd",
}
COLD_REFERENCE_ROOT = BASELINE_ROOT  # 1.0 IS the S1-shift path
SCI_CEILING = 256  # 128 single-pass calls per arm
SETUP_CEILING = 8
LIFT_GATE = 6  # per-arm paired lift vs S1-shift baseline
EVIDENCE_FILES = tuple(s1.EVIDENCE_FILES)
BLOCK_COLUMNS = tuple(s1.BLOCK_COLUMNS)

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
bind_shift_adapters = s1.bind_production_adapters
final_prefix_disclosure = r11.final_prefix_disclosure
load_fixed_baseline = r11.load_fixed_baseline
run_frozen_stage = r11.run_one_stage


def _frozen_command(damping: float) -> str:
    """Frozen per-arm command; 1.0 delegates to S1's frozen command."""
    if float(damping) == COLD_DEFAULT_DAMPING:
        return s1.FROZEN_COMMAND
    return (
        ".venv/bin/python scripts/g6r21_damp.py --execute-real "
        "--execution-authorized --registry %s --session %s --frames %s "
        "--arm %s --prior-root %s --baseline-root %s --damping %s --out-dir %s"
        % (FROZEN_REGISTRY, FROZEN_SESSION, FROZEN_FRAMES, ARM,
           FROZEN_PRIOR_ROOT, BASELINE_ROOT, damping,
           FUTURE_ROOTS[float(damping)]))


FROZEN_COMMANDS = {d: _frozen_command(d) for d in (0.5, 0.8)}


def validate_damping(damping) -> float:
    """Allowlist gate: ONLY {0.5, 0.8, 1.0}; else refuse (zero calls)."""
    if isinstance(damping, bool):
        raise ValueError("damping %r not an allowed arm" % (damping,))
    try:
        value = float(damping)
    except (TypeError, ValueError):
        raise ValueError("damping %r not an allowed arm" % (damping,))
    if value not in ALLOWED_DAMPING:
        raise ValueError("damping %r not an allowed arm %s"
                         % (damping, ALLOWED_DAMPING))
    return value


def check_stage_m(m: int) -> int:
    """Stage-m gate: R21 executes the frozen S0 point only (m==100)."""
    if int(m) != STAGE_M:
        raise ValueError("R21 executes S0 only: m=%r != frozen %d"
                         % (m, STAGE_M))
    if int(m) not in tuple(r11.STAGE_MS):
        raise ValueError("m=%r outside frozen staged set" % (m,))
    return int(m)


def run_one_block_damp(graph: dict, prior: np.ndarray, syndrome: np.ndarray,
                       ref_tag: bytes, truth_u2: np.ndarray, entry: dict,
                       decode_fn, syndrome_fn, tag_fn, call_idx: int,
                       damping: float) -> dict:
    """Single-pass S0 decode at the arm damping; truth used ONLY post-decision."""
    damping = validate_damping(damping)
    H = np.asarray(graph["dense"], dtype=np.uint8)
    if H.shape != (M, N):
        raise ValueError("R21 executes m100 S0 only: H %r" % (H.shape,))
    check_stage_m(int(graph.get("m", M)))
    if damping == COLD_DEFAULT_DAMPING:
        dec = decode_fn  # frozen path: kwargs untouched (damping 1.0)
    else:
        inner = decode_fn

        def dec(Hm, priors, syn, **kw):  # noqa: N803
            kw = dict(kw)
            kw["damping_alpha"] = float(damping)  # ONLY kwarg that varies
            return inner(Hm, priors, syn, **kw)

    srec = run_frozen_stage(H, prior, syndrome, ref_tag, truth_u2,
                            STAGE_ID, STAGE_M, dec, syndrome_fn, tag_fn,
                            call_idx)
    check_stage_m(int(srec.get("m", -1)))
    # Honest post-decision isolation (truth used ONLY here).
    truth = np.asarray(truth_u2, dtype=np.int64)
    cand = srec.get("_x_hat")
    accepted = bool(srec["accepted"])
    if not accepted:
        exact, undet = False, False
    elif cand is None:
        exact, undet = False, True  # fail closed
    else:
        exact = bool(np.array_equal(np.asarray(cand, dtype=np.int64), truth))
        undet = bool(not exact)
    rec: dict = {
        "call_idx": int(call_idx), "frame_id": int(entry["frame_id"]),
        "block_id": int(entry["block_id"]),
        "session_id": str(entry.get("session_id", "")),
        "arm": ARM, "candidate_id": CANDIDATE_ID,
        "graph_seed": int(entry["graph_seed"]), "n": N, "m": STAGE_M,
        "attempted": True, "finite": bool(srec["finite"]),
        "syndrome_match": bool(srec["syndrome_match"]),
        "tag_match": bool(srec["tag_match"]),
        "protocol_accepted": accepted,
        "verified_exact": exact, "undetected": undet,
        "outcome": "undetected" if undet else ("exact" if exact
                  else ("accepted" if accepted else "attempted")),
        "syndrome_bits": 5 * STAGE_M, "tag_bits": TAG_BITS,
        "control_bits": 0, "interaction_bits": 0, "auth_bits": 0,
        "disclosure_bits": final_prefix_disclosure(STAGE_M),
        "iters": int(srec["iters"]), "residual": int(srec["residual"]),
        "provenance": str(srec["provenance"]),
        "wall_s": float(srec.get("wall_s", 0.0)),
        "crash": bool(srec.get("crash", False)),
        "error": str(srec.get("error", ""))}
    assert (not exact) or accepted
    assert (not undet) or (accepted and not exact)
    return {c: rec.get(c, "") for c in BLOCK_COLUMNS}


def run_authorized_batch(out_root: str, registry: str, session_id: str,
                         frames_spec: str, arm: str, prior_root: str,
                         baseline_root: str, damping: float, *,
                         adapters=None, reader_override=None,
                         tag_fn=None) -> dict:
    """Execute frozen 128-call damp matrix for one arm; returns bundle."""
    damping = validate_damping(damping)  # first: zero-call refusal
    resolved = r2.refuse_out_root(out_root)  # probe only; creates nothing
    frames = _pre_execute_check(registry, session_id, frames_spec, arm,
                                prior_root)
    plan = build_call_plan(frames)
    if adapters is None:
        adapters = bind_shift_adapters()
    else:
        adapters = dict(adapters)
    _hard_fail_oracle_app(adapters)
    for key in ("decode_fn", "syndrome_fn", "load_prior_fn"):
        if adapters.get(key) is None:
            raise ValueError("adapters %s must be injected" % key)
    decode_fn, syndrome_fn = adapters["decode_fn"], adapters["syndrome_fn"]
    if tag_fn is None:
        tag_fn = adapters.get("tag_fn", s1._candidate_tag)
    # Counting wrapper: proves sci accounting + zero baseline-decode calls.
    inner_decode = decode_fn
    calls: list[int] = []

    def counting_decode(H, priors, syn, **kw):
        calls.append(1)
        return inner_decode(H, priors, syn, **kw)

    decode_fn = counting_decode
    n_before_baseline = len(calls)
    baseline = load_fixed_baseline(baseline_root)
    assert len(calls) == n_before_baseline, "baseline import made decode calls"
    p_f = adapters["load_prior_fn"](prior_root)
    # Build graphs (setup) before any decode; admission required both.
    graphs = {}
    for seed in GRAPH_SEEDS:
        graph = adapters.get("build_fn", build_graph)(seed) \
            if "build_fn" in adapters else build_graph(seed)
        if not bool(graph.get("admitted")):
            raise RuntimeError("graph %r not admitted; ENGINEERING_BLOCKED"
                               % seed)
        graphs[int(seed)] = graph
    setup_calls = len(graphs) + 2  # graphs + plan + manifest
    if setup_calls > SETUP_CEILING:
        raise RuntimeError("setup %d > ceiling %d" % (setup_calls,
                                                      SETUP_CEILING))
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
        ref_tag = tag_fn(truth_u2)
        rec = run_one_block_damp(graph, prior, syn, ref_tag, truth_u2,
                                 {**entry, "session_id": session_id},
                                 decode_fn, syndrome_fn, tag_fn,
                                 entry["call_idx"], damping)
        records.append(rec)
        if rec["undetected"]:
            break  # UNDETECTED_STOP absolute (fail-closed)
    if len(calls) > SCI_CEILING:
        raise RuntimeError("scientific calls exceed ceiling")
    # Byte-identical post-import: baseline file unchanged by our run.
    post = hashlib.sha256(
        Path(baseline_root, "block_records.csv").read_bytes()).hexdigest()
    assert post == baseline["sha256"], "baseline mutated during run"
    terminal = "UNDETECTED_STOP" if any(r["undetected"] for r in records) \
        else ("COMPLETE_128" if len(records) == 128 else "ENGINEERING_BLOCKED")
    attempted = len(records)
    accepted = sum(1 for r in records if _to_bool(r["protocol_accepted"]))
    exact = sum(1 for r in records if _to_bool(r["verified_exact"]))
    undet = sum(1 for r in records if _to_bool(r["undetected"]))
    leak_sum = sum(int(r["disclosure_bits"]) for r in records)
    denom_primary = attempted * N * H_FROZEN if attempted else None
    denom_l2 = attempted * N * H_L2 if attempted else None
    beta_primary = (1.0 - leak_sum / denom_primary) if denom_primary else None
    beta_l2 = (1.0 - leak_sum / denom_l2) if denom_l2 else None
    reconciled = exact * K_SYM_NOMINAL * 5  # SUPERSEDED by net_secret_bits (R16 correction): k-based retained double-charges parity; see V72P3R16-CORRECTION/
    net_secret = net_secret_bits(accepted, leak_sum, N)
    lift = exact - int(baseline["F"])
    manifest = {
        "schema": "g6r21_damp_manifest_v1", "change_id": CHANGE_ID,
        "cycle": CYCLE_ID,
        "command": _frozen_command(damping),
        "registry": registry, "session_id": session_id, "frames": frames_spec,
        "arm": arm, "candidate_id": CANDIDATE_ID, "prior_root": prior_root,
        "prior": {"mode": PRIOR_MODE, "eps": FROZEN_EPS,
                  "source": "CAL TRAIN counts_ab shift-delta (counts_ab only)"},
        "damping": float(damping),
        "cold_default": bool(float(damping) == COLD_DEFAULT_DAMPING),
        "out_root": str(resolved),
        "operating_point": {"n": N, "m": M, "arm": ARM,
         "candidate_id": CANDIDATE_ID, "var_counts": dict(VAR_COUNTS),
         "check_counts": dict(CHECK_COUNTS), "E": EDGE_TOTAL},
        "stage": {"stage": STAGE_ID, "m": STAGE_M,
                  "lineage": "R11 staged set %s; R21 executes S0 only"
                  % (list(r11.STAGE_MS),)},
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": MAX_ITER, "damping_alpha": float(damping),
                    "schedule": "cold single-pass S0"},
        "disclosure": {"syndrome_bits": 5 * M, "tag_bits": TAG_BITS,
                       "control_bits": 0, "interaction_bits": 0, "auth_bits": 0,
                       "per_block": final_prefix_disclosure(STAGE_M)},
        "population_split": {"CAL": "702..1725 consumed", "selection": "empty",
                             "confirmation": "2123..2186 key-disjoint "
                                             "(paired with R9/S1)"},
        "key_disjointness": "confirmation disjoint from CAL/VAL",
        "SECURITY_MODEL": "generic-only", "graph_seeds": list(GRAPH_SEEDS),
        "coefficient_namespace": COEFF_NAMESPACE_TMPL % 2026094720,
        "domain_namespace": DOMAIN_NAMESPACE,
        "baseline": {"root": baseline["baseline_root"], "F": baseline["F"],
                     "sha256": baseline["sha256"],
                     "successes": baseline["successes"],
                     "import": "read-only, zero decode calls, "
                               "byte-identical post-import"},
        "paired_gate": {"lift": lift, "gate": LIFT_GATE,
                        "rule": "per-arm lift = arm_exact - F >= 6"},
        "bias_controls": {
            "paired_blocks": "2123..2186 both arms + baseline",
            "paired_graphs": list(GRAPH_SEEDS),
            "paired_prior": {"mode": PRIOR_MODE, "eps": FROZEN_EPS},
            "selection": "full window, no subsampling",
            "varied": "damping_alpha ONLY"},
        "budgets": {"scientific_calls": SCI_CEILING,
                    "setup_calls": SETUP_CEILING},
        "setup_calls": setup_calls, "evidence_files": list(EVIDENCE_FILES),
        "authorization": "separate explicit grant required for --execute-real",
    }
    summary = {
        "schema": "g6r21_damp_summary_v1", "terminal": terminal,
        "damping": float(damping),
        "cold_default": bool(float(damping) == COLD_DEFAULT_DAMPING),
        "prior_mode": PRIOR_MODE, "prior_eps": FROZEN_EPS,
        "attempted": attempted, "accepted": accepted, "exact": exact,
        "undetected": undet,
        "accepted_fraction": (accepted / attempted) if attempted else None,
        "exact_fraction": (exact / attempted) if attempted else None,
        "FER_proxy": ((attempted - exact) / attempted) if attempted else None,
        "disclosure_sum": leak_sum, "k_sym_nominal": K_SYM_NOMINAL,
        "reconciled_net_bits": reconciled,
        "net_secret_bits": net_secret,
        "reconciled_rate": (reconciled / (attempted * N * 5))
        if attempted else None,
        "beta_eff_empirical_primary": beta_primary,
        "beta_eff_empirical_l2_sensitivity": beta_l2,
        "H_frozen_primary": H_FROZEN, "H_L2_sensitivity": H_L2,
        "baseline_F": int(baseline["F"]), "paired_lift": lift,
        "lift_gate": LIFT_GATE,
        "lift_gate_pass": bool(undet == 0 and lift >= LIFT_GATE),
        "scientific_calls": len(calls), "setup_calls": setup_calls,
        "out_root": str(resolved)}
    return {"resolved": resolved, "manifest": manifest, "records": records,
            "summary": summary}


def write_batch_root(bundle: dict) -> dict:
    """Persist bundle to fresh root (never overwrite)."""
    resolved = bundle["resolved"]
    resolved.mkdir(parents=True)
    (resolved / "manifest.json").write_text(
        json.dumps(bundle["manifest"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    with (resolved / "block_records.csv").open("w", newline="",
                                               encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(BLOCK_COLUMNS))
        writer.writeheader()
        for row in bundle["records"]:
            writer.writerow({c: row.get(c, "") for c in BLOCK_COLUMNS})
    (resolved / "summary.json").write_text(
        json.dumps(bundle["summary"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    summary = bundle["summary"]
    lines = ["# R21 DAMP m100 report (damping=%s)" % summary["damping"], "",
             "- terminal: `%s`" % summary["terminal"],
             "- prior: `%s` (eps=%s)"
             % (summary["prior_mode"], summary["prior_eps"]),
             "- attempted/exact/accepted/undetected: %d/%d/%d/%d"
             % (summary["attempted"], summary["exact"],
                summary["accepted"], summary["undetected"]),
             "- disclosure_sum: %d" % summary["disclosure_sum"],
             "- baseline_F/paired_lift/gate: %d/%d/>=%d (%s)"
             % (summary["baseline_F"], summary["paired_lift"],
                summary["lift_gate"],
                "PASS" if summary["lift_gate_pass"] else "FAIL"),
             "- beta_primary: %s" % summary["beta_eff_empirical_primary"],
             "- net_secret_bits: %d" % summary["net_secret_bits"]]
    (resolved / "report.md").write_text("\n".join(lines) + "\n",
                                        encoding="utf-8")
    return summary


def verify_root(out_root: str, damping: float) -> bool:
    """Read-only recomputation for one arm; FAIL on any mismatch."""
    damping = validate_damping(damping)
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
    if manifest.get("command") != _frozen_command(damping):
        print("VERIFY command != frozen arm command")
        return False
    if abs(float(manifest.get("damping", -1)) - float(damping)) > 0:
        print("VERIFY manifest damping != arm")
        return False
    if abs(float(summary.get("damping", -1)) - float(damping)) > 0:
        print("VERIFY summary damping != arm")
        return False
    if bool(manifest.get("cold_default")) != bool(
            float(damping) == COLD_DEFAULT_DAMPING):
        print("VERIFY cold_default != recomputed")
        return False
    if (manifest.get("prior") or {}).get("mode") != PRIOR_MODE:
        print("VERIFY prior mode != shift-delta")
        return False
    if abs(float((manifest.get("prior") or {}).get("eps", -1))
           - FROZEN_EPS) > 0:
        print("VERIFY prior eps != frozen")
        return False
    if summary.get("prior_mode") != PRIOR_MODE:
        print("VERIFY summary prior_mode != shift-delta")
        return False
    if abs(float(summary.get("prior_eps", -1)) - FROZEN_EPS) > 0:
        print("VERIFY summary prior_eps != frozen")
        return False
    dec = manifest.get("decoder") or {}
    if abs(float(dec.get("damping_alpha", -1)) - float(damping)) > 0:
        print("VERIFY decoder damping != arm")
        return False
    rows = list(csv.DictReader(
        (root / "block_records.csv").read_text(encoding="utf-8").splitlines()))
    violations: list[str] = []
    if len(rows) != 128:
        if not any(_to_bool(r.get("undetected")) for r in rows):
            violations.append("partial root %d != 128" % len(rows))
    attempted = len(rows)
    accepted = sum(1 for r in rows if _to_bool(r.get("protocol_accepted")))
    exact = sum(1 for r in rows if _to_bool(r.get("verified_exact")))
    undet = sum(1 for r in rows if _to_bool(r.get("undetected")))
    for r in rows:
        acc, ex, ud = (_to_bool(r.get("protocol_accepted")),
                       _to_bool(r.get("verified_exact")),
                       _to_bool(r.get("undetected")))
        syn, tag, fin = (_to_bool(r.get("syndrome_match")),
                         _to_bool(r.get("tag_match")),
                         _to_bool(r.get("finite")))
        if ex and not acc:
            violations.append("exact without accepted")
        if ud and (not acc or ex):
            violations.append("undetected merged")
        if acc and not (fin and syn and tag):
            violations.append("accepted without finite+syndrome+tag")
        try:
            m_val = int(r.get("m", -1))
        except (TypeError, ValueError):
            m_val = -1
        if m_val != STAGE_M:  # staged-m gate: S0 only
            violations.append("m != frozen S0 100")
        if int(r.get("disclosure_bits", -1)) != final_prefix_disclosure(STAGE_M):
            violations.append("disclosure != 5m+64")
        if int(r.get("syndrome_bits", -1)) != 5 * STAGE_M \
                or int(r.get("tag_bits", -1)) != TAG_BITS:
            violations.append("syndrome/tag split != 500/64")
        if int(r.get("control_bits", 0)) != 0 \
                or int(r.get("interaction_bits", 0)) != 0 \
                or int(r.get("auth_bits", 0)) != 0:
            violations.append("control/interaction/auth != 0")
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
    if summary.get("net_secret_bits", None) is None or int(
            summary.get("net_secret_bits")) != net_secret_bits(
            accepted, leak_sum, N):
        violations.append("net_secret_bits != recomputed")
    denom_p = attempted * N * H_FROZEN if attempted else 0
    denom_l = attempted * N * H_L2 if attempted else 0
    beta_p = (1.0 - leak_sum / denom_p) if denom_p else None
    beta_l = (1.0 - leak_sum / denom_l) if denom_l else 0
    if summary.get("beta_eff_empirical_primary") is None and beta_p is not None:
        violations.append("beta primary missing")
    elif beta_p is not None and abs(
            float(summary["beta_eff_empirical_primary"]) - beta_p) > 1e-12:
        violations.append("beta primary != recomputed")
    if abs(float(summary.get("beta_eff_empirical_l2_sensitivity", 0))
           - beta_l) > 1e-12:
        violations.append("beta l2 != recomputed")
    base_f = int(manifest.get("baseline", {}).get("F", -1))
    if int(summary.get("baseline_F", -2)) != base_f:
        violations.append("baseline_F != manifest")
    if int(summary.get("paired_lift", -999999)) != exact - base_f:
        violations.append("paired_lift != exact - F")
    if bool(summary.get("lift_gate_pass")) != bool(
            undet == 0 and (exact - base_f) >= LIFT_GATE):
        violations.append("lift_gate_pass != recomputed")
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


def profile_only(damping: float) -> dict:
    """Pre-execution dry run for one arm: plan + proofs; zero everything."""
    damping = validate_damping(damping)  # refusal before any I/O
    frames = parse_frames(FROZEN_FRAMES)
    plan = build_call_plan(frames)
    baseline = load_fixed_baseline(BASELINE_ROOT)  # read-only, zero decode
    out = FUTURE_ROOTS.get(float(damping), COLD_REFERENCE_ROOT)
    future = (ROOT / out).resolve()
    sci = len(plan)
    setup = len(GRAPH_SEEDS) + 2
    return {
        "damping": float(damping),
        "cold_default": bool(float(damping) == COLD_DEFAULT_DAMPING),
        "graphs_constructed": 0, "decoder_calls": 0, "model_f_loads": 0,
        "real_pool_reads": 0, "symbol_reads": 0,
        "plan_calls": sci, "plan_order": "frame->block->graph even/odd",
        "prior_mode": PRIOR_MODE, "prior_eps": FROZEN_EPS,
        "stage": {"stage": STAGE_ID, "m": STAGE_M,
                  "lineage": "R11 staged set %s; R21 executes S0 only"
                  % (list(r11.STAGE_MS),)},
        "budgets": {"scientific_calls": SCI_CEILING,
                    "setup_calls": setup,
                    "setup_ceiling": SETUP_CEILING},
        "budget_ok": sci <= SCI_CEILING and setup <= SETUP_CEILING,
        "baseline": {"F": baseline["F"], "sha256": baseline["sha256"],
                     "successes": baseline["successes"]},
        "paired_gate": {"gate": LIFT_GATE,
                        "rule": "per-arm lift = arm_exact - F >= 6"},
        "bias_controls": {
            "paired_blocks": "2123..2186 both arms + baseline",
            "paired_graphs": list(GRAPH_SEEDS),
            "paired_prior": {"mode": PRIOR_MODE, "eps": FROZEN_EPS},
            "selection": "full window, no subsampling",
            "varied": "damping_alpha ONLY"},
        "future_root": str(future), "future_root_absent": not future.exists(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="R21 DAMP ladder runner")
    parser.add_argument("--registry", default=FROZEN_REGISTRY)
    parser.add_argument("--session", default=FROZEN_SESSION)
    parser.add_argument("--frames", default=FROZEN_FRAMES)
    parser.add_argument("--arm", default=ARM)
    parser.add_argument("--prior-root", default=FROZEN_PRIOR_ROOT)
    parser.add_argument("--baseline-root", default=BASELINE_ROOT)
    parser.add_argument("--damping", type=float, default=0.5,
                        choices=[0.5, 0.8, 1.0])
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--profile-only", action="store_true")
    parser.add_argument("--execute-real", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--execution-authorized", action="store_true",
                        default=False)
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
        damping = validate_damping(args.damping)
    except ValueError as exc:
        parser.error(str(exc))
    if args.profile_only:
        print(json.dumps(profile_only(damping), indent=2, sort_keys=True))
        return 0
    if args.verify:
        if args.out_dir is None:
            parser.error("--verify requires --out-dir")
        return 0 if verify_root(args.out_dir, damping) else 1
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
            args.arm, args.prior_root, args.baseline_root, damping,
            adapters=adapters_override)
    except FileExistsError as exc:
        print("PRE_EXECUTION_BLOCKED existing root: %s" % exc, file=sys.stderr)
        return 2
    except ValueError as exc:
        if "PRE_EXECUTION_BLOCKED" in str(exc):
            print(str(exc), file=sys.stderr)
            return 2
        raise
    summary = write_batch_root(bundle)
    print("R21 damping=%s terminal=%s attempted=%d exact=%d accepted=%d "
          "undetected=%d lift=%d" % (summary["damping"], summary["terminal"],
                                     summary["attempted"], summary["exact"],
                                     summary["accepted"],
                                     summary["undetected"],
                                     summary["paired_lift"]))
    return 0 if summary["terminal"] == "COMPLETE_128" else 1


if __name__ == "__main__":
    raise SystemExit(main())
