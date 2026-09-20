"""R10 CTRL m100 thin runner — DECIDE-readiness (NOT execution).

R10b2 scope (this increment): readiness only, zero real calls. Branch
formal-ir-v72p1-addendum-clean. Standing autonomy covers new file + fake
tests only; run grant separate, NOT consumed here.

- P-pop: session 20260123_1M_600k_0dB, frames 1983..2046 (64 frames;
  2046-1983+1=64). Allowlist EXACTLY {(20260123_1M_600k_0dB,
  1983..2046)} — anything else (incl R9 P-1p5M 2123..2186 and R1 P-2M
  2093..2156, shifted 1982..2045, overflow 1983..2047, wrong session)
  -> PRE_EXECUTION_BLOCKED with ZERO calls. This runner serves R10 only.
- P-op/graphs: SAME m100 graphs 4720/4721 as R9 (reuse by import, no new
  construction: no new seeds, no new namespaces; admission via the same
  D10-R2 builder path).
- P-dec: cold row-layered 90/1.0 single-pass, Model-F marginal prior
  (read-only npz, same prior path as R9), disclosure_i=5*rows+64=564,
  control=interaction=auth=0.
- P-acct: attempted/exact/accepted/undetected isolated; disclosure sums
  include failures; k_sym nominal 28 (= n-m = 128-100, derived-only,
  never hand-filled); beta derived-only (primary + L2 sensitivity).
- P-gate: UNDETECTED_STOP absolute; ENGINEERING_BLOCKED for infra;
  ORACLE/APP/transfer hard-fail.
- P-bud: sci<=128/setup<=16.
- P-cmd: flags below; --execute-real refuses without
  --execution-authorized (rc=2) BEFORE any root/bind/load.
- P-tests: delta FAKE-fixture tests only (see tests/test_g6r10_ctrl.py).
- P-stop: any violation STOP + retain + single decision needed.
- P-auth: R10b2 consumes NO execution (zero real calls here); R10c
  execution needs the frozen ARGV + separate grant + Pre-EXECUTE +
  Pre-RESULT.

Readiness note: _pre_execute_check enforces frozen identities + exact
allowlist + window shape with ZERO file I/O (no registry/parquet reads).
Deeper 1M registry CAL/VAL + parquet frame_id presence is verified at
execution Pre-EXECUTE under the R10c grant, not in readiness.

Reuse: r9 binds by import (no copy) — parse/graph/plan/prior/decode
adapters/verifier helpers; D10-R2 builder/admission/refusal; D16/v35
decoder kernel (lazy bind, no duplicate); Model-F npz read-only.

Forbidden: any decoder calls or symbol reads in R10b2; create the UUID
root; edit frozen runners/tests (incl scripts/g6r9_confirm.py); touch
src/experiments/tools/results/outputs_comparison/prior roots;
commit/push.
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

import g6r9_confirm as r9  # noqa: E402
from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as r2  # noqa: E402

# Frozen identifiers (P-pop/P-op/P-dec/P-bud/P-cmd). Graph/op/dec values
# aliased from R9 (same m100 operating point, reuse by import).
CHANGE_ID = "g6r10-ctrl"
CYCLE_ID = "G6R10-CTRL"
N = r9.N
M = r9.M
Q = r9.Q
POLY = r9.POLY
MAX_ITER = r9.MAX_ITER
DAMPING = r9.DAMPING
BITS_PER_ROW = r9.BITS_PER_ROW
TAG_BITS = r9.TAG_BITS
H_FROZEN = r9.H_FROZEN
H_L2 = r9.H_L2
K_SYM_NOMINAL = r9.K_SYM_NOMINAL  # SUPERSEDED by net_secret_bits (R16 correction): k-based retained double-charges parity; see V72P3R16-CORRECTION/
VAR_COUNTS = dict(r9.VAR_COUNTS)
CHECK_COUNTS = dict(r9.CHECK_COUNTS)
EDGE_TOTAL = r9.EDGE_TOTAL
ARM = r9.ARM
CANDIDATE_ID = r9.CANDIDATE_ID
GRAPH_SEEDS = tuple(r9.GRAPH_SEEDS)
DOMAIN_NAMESPACE = r9.DOMAIN_NAMESPACE
COEFF_NAMESPACE_TMPL = r9.COEFF_NAMESPACE_TMPL
FROZEN_REGISTRY = r9.FROZEN_REGISTRY
FROZEN_SESSION = "20260123_1M_600k_0dB"
FROZEN_FRAMES = "1983..2046"
FROZEN_PRIOR_ROOT = r9.FROZEN_PRIOR_ROOT
ALLOWED_PAIRS = frozenset({(FROZEN_SESSION, FROZEN_FRAMES)})
FUTURE_ROOT_UUID = "6f2b8c1d-4a3e-4f9a-b7c2-d5e6f8a9b0c1"
FUTURE_ROOT = "workspace/g6r10_ctrl_" + FUTURE_ROOT_UUID
SCI_CEILING = r9.SCI_CEILING
SETUP_CEILING = r9.SETUP_CEILING
EVIDENCE_FILES = tuple(r9.EVIDENCE_FILES)
BLOCK_COLUMNS = tuple(r9.BLOCK_COLUMNS)
FROZEN_COMMAND = (
    ".venv/bin/python scripts/g6r10_ctrl.py --execute-real "
    "--execution-authorized --registry %s --session %s --frames %s "
    "--arm %s --prior-root %s --out-dir %s"
    % (FROZEN_REGISTRY, FROZEN_SESSION, FROZEN_FRAMES, ARM,
       FROZEN_PRIOR_ROOT, FUTURE_ROOT))

# Direct binds reused by import (no copies, no duplicate kernels).
parse_frames = r9.parse_frames
disclosed_bits = r9.disclosed_bits
# R16 true net reuses the canonical r9 helper (inherit by import, no duplicate).
net_secret_bits = r9.net_secret_bits
marginal_l2_prior = r9.marginal_l2_prior
_candidate_tag = r9._candidate_tag
_hard_fail_oracle_app = r9._hard_fail_oracle_app
run_one_block = r9.run_one_block
bind_production_adapters = r9.bind_production_adapters
_to_bool = r9._to_bool
build_call_plan = r9.build_call_plan


def build_graph(graph_seed: int) -> dict:
    """Rebuild one frozen R10 graph (same pair/builder/namespaces as R9)."""
    if int(graph_seed) not in GRAPH_SEEDS:
        raise ValueError("PRE_EXECUTION_BLOCKED: graph seed %r outside "
                         "frozen R10 pair" % (graph_seed,))
    return r9.build_graph(int(graph_seed))


def _check_allowlist(session_id: str, frames_spec: str) -> None:
    """Exact (session,frames) allowlist: R10 pair only, else BLOCKED."""
    if (str(session_id), str(frames_spec)) not in ALLOWED_PAIRS:
        raise ValueError(
            "PRE_EXECUTION_BLOCKED: (session,frames) %r not in frozen "
            "R10 allowlist %r (this runner serves R10 only; zero calls)"
            % ((str(session_id), str(frames_spec)), sorted(ALLOWED_PAIRS)))


def _pre_execute_check(registry_path: str, session_id: str,
                       frames_spec: str, arm: str, prior_root: str) -> list[int]:
    """Pre-EXECUTE gate BEFORE any decode/bind/load: mismatch -> BLOCKED.

    Zero file I/O (no registry/parquet reads in readiness). Checks frozen
    registry identity, exact R10 (session,frames) allowlist, arm/prior
    identity, and window shape 1983..2046 (64 frames). Deeper 1M registry
    CAL/VAL + parquet frame_id presence is an execution Pre-EXECUTE item
    (R10c grant), not readiness.
    """
    if str(registry_path) != FROZEN_REGISTRY:
        raise ValueError("PRE_EXECUTION_BLOCKED: registry %r != frozen %r"
                         % (registry_path, FROZEN_REGISTRY))
    _check_allowlist(session_id, frames_spec)
    if str(arm) != ARM:
        raise ValueError("PRE_EXECUTION_BLOCKED: arm %r != frozen %r" % (arm, ARM))
    if str(prior_root) != FROZEN_PRIOR_ROOT:
        raise ValueError("PRE_EXECUTION_BLOCKED: prior-root mismatch")
    frames = parse_frames(frames_spec)
    if len(frames) != 64 or frames[0] != 1983 or frames[-1] != 2046:
        raise ValueError("PRE_EXECUTION_BLOCKED: window != 1983..2046")
    return frames


def run_authorized_batch(out_root: str, registry: str, session_id: str,
                         frames_spec: str, arm: str, prior_root: str, *,
                         adapters=None, reader_override=None) -> dict:
    """Execute frozen 128-call matrix; returns bundle (writes separately)."""
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
    # Build graphs (setup) before any decode; admission required both.
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
    # Load selected pairs: verifier holds Alice, decoder sees Bob+syndrome.
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
        # Split full 10-bit to U1/U2; L2 target is U2 (low).
        alice_u2_full = alice_full % 32
        # 2 blocks per frame: first/second 128.
        pos = entry["block_id"] % 2
        sl = slice(pos * 128, (pos + 1) * 128)
        truth_u2 = alice_u2_full[sl]
        bob_block = bob_full[sl]
        prior = marginal_l2_prior(p_f, bob_block)
        graph = graphs[int(entry["graph_seed"])]
        H = np.asarray(graph["dense"], dtype=np.uint8)
        syn = np.asarray(syndrome_fn(H, truth_u2), dtype=np.uint8)
        ref_tag = _candidate_tag(truth_u2)
        rec = run_one_block(graph, prior, syn, ref_tag, truth_u2,
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
    # beta derived-only (never hand-filled); primary + sensitivity.
    denom_primary = attempted * N * H_FROZEN if attempted else None
    denom_l2 = attempted * N * H_L2 if attempted else None
    beta_primary = (1.0 - leak_sum / denom_primary) if denom_primary else None
    beta_l2 = (1.0 - leak_sum / denom_l2) if denom_l2 else None
    reconciled = exact * K_SYM_NOMINAL * 5  # SUPERSEDED by net_secret_bits (R16 correction): k-based retained double-charges parity; see V72P3R16-CORRECTION/
    net_secret = net_secret_bits(accepted, leak_sum, N)
    manifest = {
        "schema": "g6r10_ctrl_manifest_v1", "change_id": CHANGE_ID,
        "cycle": CYCLE_ID, "command": FROZEN_COMMAND,
        "registry": registry, "session_id": session_id, "frames": frames_spec,
        "arm": arm, "candidate_id": CANDIDATE_ID, "prior_root": prior_root,
        "out_root": str(resolved), "operating_point": {"n": N, "m": M, "arm": ARM,
        "candidate_id": CANDIDATE_ID, "var_counts": dict(VAR_COUNTS),
        "check_counts": dict(CHECK_COUNTS), "E": EDGE_TOTAL},
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": MAX_ITER, "damping_alpha": DAMPING,
                    "schedule": "cold row-layered single-pass"},
        "disclosure": {"syndrome_bits": 5 * M, "tag_bits": TAG_BITS,
                       "control_bits": 0, "interaction_bits": 0, "auth_bits": 0,
                       "per_block": disclosed_bits(M)},
        "population_split": {"CAL": "TBD-at-execution-Pre-EXECUTE",
                             "selection": "empty",
                             "confirmation": "1983..2046 key-disjoint"},
        "key_disjointness": "confirmation disjointness verified at execution Pre-EXECUTE",
        "SECURITY_MODEL": "generic-only", "graph_seeds": list(GRAPH_SEEDS),
        "coefficient_namespace": COEFF_NAMESPACE_TMPL % 2026094720,
        "domain_namespace": DOMAIN_NAMESPACE,
        "budgets": {"scientific_calls": SCI_CEILING, "setup_calls": SETUP_CEILING},
        "setup_calls": setup_calls, "evidence_files": list(EVIDENCE_FILES),
        "authorization": "separate explicit grant required for --execute-real",
    }
    summary = {
        "schema": "g6r10_ctrl_summary_v1", "terminal": terminal,
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
    lines = ["# R10 CTRL m100 report", "",
             "- terminal: `%s`" % summary["terminal"],
             "- attempted/exact/accepted/undetected: %d/%d/%d/%d"
             % (summary["attempted"], summary["exact"],
                summary["accepted"], summary["undetected"]),
             "- disclosure_sum: %d" % summary["disclosure_sum"],
             "- beta_primary: %s" % summary["beta_eff_empirical_primary"],
             "- beta_l2_sensitivity: %s" % summary["beta_eff_empirical_l2_sensitivity"],
             "- reconciled_net_bits: %d" % summary["reconciled_net_bits"]]
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
    rows = list(csv.DictReader((root / "block_records.csv").read_text(encoding="utf-8").splitlines()))
    violations: list[str] = []
    if len(rows) not in (128,):
        # Partial roots fail (UNDETECTED_STOP early exit is still FAIL here
        # because exact/syndrome/tag isolation requires full 128 for R10).
        # An early UNDETECTED_STOP root is retained but verify FAILs.
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
    # beta recomputation (primary + sensitivity, derived-only).
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


def profile_only() -> dict:
    """Pre-decoder dry run on FAKE pool only: 128-call plan, zero decoder."""
    graphs = [build_graph(seed) for seed in GRAPH_SEEDS]
    admitted = sum(1 for g in graphs if g["admitted"])
    frames = parse_frames(FROZEN_FRAMES)
    plan = build_call_plan(frames)
    future = (ROOT / FUTURE_ROOT).resolve()
    return {
        "graphs": [{"seed": g["graph_seed"], "n": g["n"], "m": g["m"],
                    "E": g["E"], "admitted": g["admitted"],
                    "status": g["status"]} for g in graphs],
        "admitted": admitted, "total_graphs": len(graphs),
        "plan_calls": len(plan),
        "plan_order": "frame->block->graph even/odd",
        "budgets": {"scientific_calls": len(plan), "sci_ceiling": SCI_CEILING,
                    "setup_calls": len(graphs) + 2, "setup_ceiling": SETUP_CEILING},
        "budget_ok": len(plan) <= SCI_CEILING and (len(graphs) + 2) <= SETUP_CEILING,
        "future_root": str(future), "future_root_absent": not future.exists(),
        "decoder_calls": 0, "model_f_loads": 0, "real_pool_reads": 0,
        "domain_namespace": DOMAIN_NAMESPACE,
        "coefficient_namespace": COEFF_NAMESPACE_TMPL % 2026094720,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="R10 CTRL m100 thin runner")
    parser.add_argument("--registry", default=FROZEN_REGISTRY)
    parser.add_argument("--session", default=FROZEN_SESSION)
    parser.add_argument("--frames", default=FROZEN_FRAMES)
    parser.add_argument("--arm", default=ARM)
    parser.add_argument("--prior-root", default=FROZEN_PRIOR_ROOT)
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
    if args.profile_only:
        print(json.dumps(profile_only(), indent=2, sort_keys=True))
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
            args.arm, args.prior_root, adapters=adapters_override)
    except FileExistsError as exc:
        print("PRE_EXECUTION_BLOCKED existing root: %s" % exc, file=sys.stderr)
        return 2
    except ValueError as exc:
        if "PRE_EXECUTION_BLOCKED" in str(exc):
            print(str(exc), file=sys.stderr)
            return 2
        raise
    summary = write_batch_root(bundle)
    print("R10 terminal=%s attempted=%d exact=%d accepted=%d undetected=%d"
          % (summary["terminal"], summary["attempted"], summary["exact"],
             summary["accepted"], summary["undetected"]))
    return 0 if summary["terminal"] == "COMPLETE_128" else 1


if __name__ == "__main__":
    raise SystemExit(main())
