"""R9 CONFIRM m100 thin runner — DECIDE-readiness (NOT execution).

R9b scope (frozen PREREG_AND_AUTH.md, docs/research_cycles/V72P3R9-CONFIRM).
Choice rationale (one line): R1/R2diag runners are frozen (no edits), so this
is a new file carrying the accepted G6-DECIDE-R1 pattern with m100
substitution (verbatim S7-arith sheet counts, never m94 numbers).

- P-pop: registry v71_data_registry.json, session 20260107_PPLN_1p5M,
  frames 2123..2186 (64 frames, arithmetically disjoint from CAL 702..1725
  and VAL 1726..1981; parquet presence deferred to --execute-real
  Pre-EXECUTE key-gate — R9b performs zero real-data reads).
- P-op: n128/m100/L020 lam_d2_0.20_d3_0.80, verbatim S7-arith sheet:
  E349, check {3:51,4:49}, var {2:35,3:93}, rate 0.21875.
- P-dec: Model-F marginal prior (read-only npz), cold row-layered 90/1.0
  single-pass, disclosure_i=5*rows+64=564, control=interaction=auth=0.
- P-acct: attempted/exact/accepted/undetected isolated; disclosure sums
  include failures; k_sym nominal 28 (= n-m = 128-100, no shortening
  modeled — same n-m rule as G6 m94 k=34; PREREG-UNKNOWN frozen here with
  rationale, never hand-filled); beta derived-only.
- P-gate: UNDETECTED_STOP absolute; ENGINEERING_BLOCKED for infra.
- P-bud: sci<=128/setup<=16.
- P-cmd: flags below; --execute-real refuses without --execution-authorized.
- P-tests: delta FAKE-fixture tests only (see tests/test_g6r9_confirm.py).
- P-stop: any violation STOP + retain + single decision needed.
- P-auth: R9b consumes NO execution (zero real calls here); R9c execution
  needs the frozen ARGV + separate grant + Pre-EXECUTE + Pre-RESULT.

Prior-root freeze: same artifact path as R1
(workspace/v72p2d5_model_f_input/20260907_r1) with the cross-session caveat
already disclosed (prior trained outside P-1p5M; read-only marginal use).

Reuse: D10-R2 builder/admission/refusal (import, no copy); D16/v35
decoder kernel (lazy bind, no duplicate); Model-F npz read-only.

Forbidden: any real-data reads in R9b (registry text + code only);
create the UUID root; edit frozen runners/tests; touch
src/experiments/tools/results/outputs_comparison/prior roots; commit/push.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))

from comparison_bench.formal_ir import nonbinary_v10_common as common  # noqa: E402
from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as r2  # noqa: E402

# Frozen identifiers (P-pop/P-op/P-dec/P-bud/P-cmd).
CHANGE_ID = "g6r9-confirm"
CYCLE_ID = "G6R9-CONFIRM"
N = 128
M = 100
Q = 32
POLY = 37
MAX_ITER = 90
DAMPING = 1.0
BITS_PER_ROW = 5
TAG_BITS = 64
H_FROZEN = 3.347605
H_L2 = 3.222719884634378
K_SYM_NOMINAL = 28  # frozen: n-m = 128-100, no shortening modeled (G6 rule: 128-94=34)  # SUPERSEDED by net_secret_bits (R16 correction): k-based retained double-charges parity; see V72P3R16-CORRECTION/
VAR_COUNTS = {2: 35, 3: 93}  # verbatim S7-arith m100 sheet
CHECK_COUNTS = {3: 51, 4: 49}  # verbatim S7-arith m100 sheet
EDGE_TOTAL = 349  # 3*51+4*49 = 2*35+3*93
ARM = "L020"
CANDIDATE_ID = "lam_d2_0.20_d3_0.80"
# Fresh seeds: first free >= 4720; ban list D8/D9/D12/D16/D19 namespaces,
# G6 2026094601/4602, R7 DE 2026094701..4708, R7 pool 2026094711..4719.
GRAPH_SEEDS = (2026094720, 2026094721)
# Fresh namespaces (frozen exact strings; proven absent before use).
DOMAIN_NAMESPACE = "g6r9-domain"
COEFF_NAMESPACE_TMPL = "g6r9:coeff:n128:L020:%d"
FROZEN_REGISTRY = "v71_data_registry.json"
FROZEN_SESSION = "20260107_PPLN_1p5M"
FROZEN_FRAMES = "2123..2186"
FROZEN_PRIOR_ROOT = "workspace/v72p2d5_model_f_input/20260907_r1"
FUTURE_ROOT_UUID = "3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d"
FUTURE_ROOT = "workspace/g6r9_confirm_" + FUTURE_ROOT_UUID
SCI_CEILING = 128
SETUP_CEILING = 16
EVIDENCE_FILES = ("manifest.json", "block_records.csv", "summary.json", "report.md")
BLOCK_COLUMNS = (
    "call_idx", "frame_id", "block_id", "session_id", "arm", "candidate_id",
    "graph_seed", "n", "m", "attempted", "finite", "syndrome_match",
    "tag_match", "protocol_accepted", "verified_exact", "undetected",
    "outcome", "syndrome_bits", "tag_bits", "control_bits",
    "interaction_bits", "auth_bits", "disclosure_bits", "iters",
    "residual", "provenance", "wall_s", "crash", "error")
FROZEN_COMMAND = (
    ".venv/bin/python scripts/g6r9_confirm.py --execute-real "
    "--execution-authorized --registry %s --session %s --frames %s "
    "--arm %s --prior-root %s --out-dir %s"
    % (FROZEN_REGISTRY, FROZEN_SESSION, FROZEN_FRAMES, ARM,
       FROZEN_PRIOR_ROOT, FUTURE_ROOT))


def parse_frames(spec: str) -> list[int]:
    """Parse frozen frame spec '2123..2186' (inclusive) to ID list."""
    text = str(spec).strip()
    if ".." in text:
        start_s, end_s = text.split("..", 1)
        start, end = int(start_s), int(end_s)
    elif "-" in text and text.count("-") == 1:
        start_s, end_s = text.split("-", 1)
        start, end = int(start_s), int(end_s)
    else:
        raise ValueError("frames spec must be 'START..END': %r" % spec)
    if end < start:
        raise ValueError("frames END before START: %r" % spec)
    return list(range(start, end + 1))


def disclosed_bits(rows: int) -> int:
    """Disclosure per block: 5*rows + 64 tag (control/interaction/auth 0)."""
    return int(rows) * BITS_PER_ROW + TAG_BITS


def net_secret_bits(accepted: int, disclosure_sum: int, n: int = N) -> int:
    """R16 true net: accepted*5*n - disclosure_sum (exhausted/unaccepted -disclosure_i)."""
    return int(accepted) * 5 * int(n) - int(disclosure_sum)


def coefficient_seed(graph_seed: int) -> int:
    """Fresh coefficient stream (single R9 namespace, arm/width frozen)."""
    return common.v10_seed(COEFF_NAMESPACE_TMPL % int(graph_seed))


def coefficients_for_edges(edges, graph_seed: int) -> list[int]:
    """One uniform nonzero GF32 draw per edge in sorted order (fresh ns)."""
    rng = np.random.default_rng(coefficient_seed(graph_seed))
    out = []
    for _ in sorted((int(v), int(c)) for v, c in (tuple(e) for e in edges)):
        coeff = int(rng.integers(1, Q))
        if coeff == 0:
            raise ValueError("coefficient sampler produced zero")
        out.append(coeff)
    return out


def build_graph(graph_seed: int) -> dict:
    """Build one frozen R9 graph via D10-R2 builder + fresh coefficients."""
    if int(graph_seed) not in GRAPH_SEEDS:
        raise ValueError("graph seed %r outside frozen R9 pair" % graph_seed)
    construction = r2.build_degree_sequence_peg(
        N, M, dict(VAR_COUNTS), dict(CHECK_COUNTS), int(graph_seed))
    record: dict = {
        "arm": ARM, "width": N, "graph_seed": int(graph_seed),
        "n": N, "m": M, "E": 0, "edges": [], "coefficients": [],
        "dense": None, "structure": None, "status": "construction_failed",
        "admitted": False, "failure_reason": construction.get("failure_reason", ""),
    }
    if construction["status"] != "ok":
        return record
    coeffs = coefficients_for_edges(construction["edges"], int(graph_seed))
    dense = r2.dense_from_edges(N, M, construction["edges"], coeffs)
    structure = r2.structural_record(dense, dict(VAR_COUNTS), dict(CHECK_COUNTS))
    replay = r2.build_degree_sequence_peg(
        N, M, dict(VAR_COUNTS), dict(CHECK_COUNTS), int(graph_seed))
    replay_coeffs = coefficients_for_edges(replay["edges"], int(graph_seed))
    replay_ok = bool(replay["status"] == "ok"
                     and replay["edges"] == construction["edges"]
                     and replay_coeffs == coeffs)
    structure["admission"]["A6_deterministic_replay"] = replay_ok
    structure["admitted"] = bool(all(structure["admission"].values()))
    failed = [k for k, v in structure["admission"].items() if not v]
    record.update({
        "E": len(construction["edges"]), "edges": construction["edges"],
        "coefficients": coeffs, "dense": dense, "structure": structure,
        "status": "ok", "admitted": bool(structure["admitted"]),
        "failure_reason": "" if structure["admitted"]
        else "admission failed: %s" % ",".join(failed),
    })
    return record


def build_call_plan(frame_ids: list[int]) -> list[dict]:
    """Frozen 128-call plan: frame->block->graph even/odd, single-arm.

    Each frame yields 2 blocks (first/second 128 U2 symbols); global block
    index even/odd selects graph 4720/4721. One call per block (no pooling).
    """
    frames = [int(f) for f in frame_ids]
    if len(frames) != 64:
        raise ValueError("R9 plan requires exactly 64 frames, got %d" % len(frames))
    plan = []
    for frame_idx, frame_id in enumerate(frames):
        for block_pos in (0, 1):
            global_block = frame_idx * 2 + block_pos
            graph_seed = GRAPH_SEEDS[global_block % 2]
            plan.append({
                "call_idx": global_block, "frame_id": int(frame_id),
                "block_id": int(global_block), "graph_seed": int(graph_seed),
                "arm": ARM, "candidate_id": CANDIDATE_ID, "n": N, "m": M,
                "disclosed_bits": disclosed_bits(M)})
    return plan


def _candidate_tag(u2vec: np.ndarray) -> bytes:
    return hashlib.sha256(np.asarray(u2vec, dtype=np.int64).tobytes()).digest()[:8]


def marginal_l2_prior(p_f: np.ndarray, bob_full: np.ndarray) -> np.ndarray:
    """Marginal P(U2|B)=sum_U1 P_F marginal, floor 1e-15, renorm (Bob only)."""
    pf = np.asarray(p_f, dtype=np.float64)
    bob = np.asarray(bob_full, dtype=np.int64).ravel()
    if pf.shape != (1024, 1024):
        raise ValueError("p_f must be (1024,1024)")
    if bob.shape != (N,) or np.any(bob < 0) or np.any(bob >= 1024):
        raise ValueError("bob_full must be (128,) in 0..1023")
    # ponytail: O(n*q) scan, vectorize if widths grow.
    reshaped = pf.reshape(32, 32, 1024)
    marginal = reshaped.sum(axis=0)  # (U2=32, B=1024)
    prior = marginal[:, bob].T  # (128,32)
    prior = np.maximum(prior, 1e-15)
    prior /= prior.sum(axis=1, keepdims=True)
    return prior


def _hard_fail_oracle_app(adapters: dict) -> None:
    for key in adapters:
        low = str(key).lower()
        if "oracle" in low or low == "app" or "app_" in low or "transfer" in low:
            raise ValueError("ORACLE/APP/transfer forbidden on R9 real path: %r" % key)
    for bad in ("oracle_prior_fn", "oracle_parts", "app_prior_fn", "transfer_fn"):
        if adapters.get(bad) is not None:
            raise ValueError("ORACLE/APP/transfer forbidden on R9 real path: %s" % bad)


def run_one_block(graph: dict, prior: np.ndarray, syndrome: np.ndarray,
                   ref_tag: bytes, truth_u2: np.ndarray, entry: dict,
                   decode_fn, syndrome_fn, call_idx: int) -> dict:
    """Single-pass cold 90/1.0 decode; truth used ONLY post-decision."""
    if graph.get("dense") is None or not bool(graph.get("admitted")):
        raise r2.StructureNotAdmitted("non-admitted R9 graph")
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
        result = decode_fn(H, prior, syn, max_iter=MAX_ITER,
                           damping_alpha=DAMPING, warm_beliefs=None, field=None)
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
        # Isolation: exact subset of accepted; undetected never merged.
        assert (not exact) or accepted
        assert (not undet) or (accepted and not exact)
        return rec
    except Exception as exc:  # retained crash, never retried
        rec.update({"crash": True, "error": repr(exc)[:300],
                    "outcome": "attempted",
                    "wall_s": time.perf_counter() - t0})
        return rec


def _pre_execute_check(registry_path: str, session_id: str,
                       frames_spec: str, arm: str, prior_root: str) -> list[int]:
    """Pre-EXECUTE gate BEFORE any decode: mismatch -> PRE_EXECUTION_BLOCKED.

    Checks frozen registry/session/frames/arm/prior-root identity, CAL
    702..1725 and VAL start, window disjointness from CAL/VAL, and parquet
    frame_id presence (frame_id column ONLY, never alice/bob).
    """
    if str(registry_path) != FROZEN_REGISTRY:
        raise ValueError("PRE_EXECUTION_BLOCKED: registry %r != frozen %r"
                         % (registry_path, FROZEN_REGISTRY))
    if str(session_id) != FROZEN_SESSION:
        raise ValueError("PRE_EXECUTION_BLOCKED: session %r != frozen %r"
                         % (session_id, FROZEN_SESSION))
    if str(frames_spec) != FROZEN_FRAMES:
        raise ValueError("PRE_EXECUTION_BLOCKED: frames %r != frozen %r"
                         % (frames_spec, FROZEN_FRAMES))
    if str(arm) != ARM:
        raise ValueError("PRE_EXECUTION_BLOCKED: arm %r != frozen %r" % (arm, ARM))
    if str(prior_root) != FROZEN_PRIOR_ROOT:
        raise ValueError("PRE_EXECUTION_BLOCKED: prior-root mismatch")
    frames = parse_frames(frames_spec)
    if len(frames) != 64 or frames[0] != 2123 or frames[-1] != 2186:
        raise ValueError("PRE_EXECUTION_BLOCKED: window != 2123..2186")
    reg_path = ROOT / registry_path if not Path(registry_path).is_absolute() \
        else Path(registry_path)
    registry = json.loads(reg_path.read_text(encoding="utf-8"))
    sessions = [s for s in registry.get("sessions", [])
                if s.get("session_id") == session_id]
    if len(sessions) != 1:
        raise ValueError("PRE_EXECUTION_BLOCKED: session not unique")
    session = sessions[0]
    cal = [int(x) for x in session.get("stage2_CAL_frame_ids", [])]
    if cal != list(range(702, 1726)):
        raise ValueError("PRE_EXECUTION_BLOCKED: CAL != 702..1725")
    val = [int(x) for x in session.get("stage2_VAL_frame_ids", [])]
    if val[:4] != [1726, 1727, 1728, 1729]:
        raise ValueError("PRE_EXECUTION_BLOCKED: VAL start != 1726..1729")
    if set(frames) & set(cal):
        raise ValueError("PRE_EXECUTION_BLOCKED: window overlaps CAL")
    if set(frames) & set(val):
        raise ValueError("PRE_EXECUTION_BLOCKED: window overlaps VAL")
    # Key-check parquet frame_id column ONLY (never alice/bob).
    import pyarrow.parquet as pq
    pairs_path = ROOT / session["provenance"] if not Path(session["provenance"]).is_absolute() \
        else Path(session["provenance"])
    pf = pq.ParquetFile(str(pairs_path))
    cols = [str(f.name) for f in pf.schema]
    if "frame_id" not in cols:
        raise ValueError("PRE_EXECUTION_BLOCKED: no frame_id column")
    table = pf.read(columns=["frame_id"])
    present = set(table.column("frame_id").to_pylist())
    missing = [f for f in frames if f not in present]
    if missing:
        raise ValueError("PRE_EXECUTION_BLOCKED: frames missing %r" % missing[:5])
    return frames


def bind_production_adapters():
    """Lazy production bind (decoder + syndrome + prior loader), zero calls."""
    import inspect as _inspect
    from comparison_bench.formal_ir import v35_algorithm_development as v35
    from comparison_bench.formal_ir import v72p2d5_gf32_rate_mother as d5

    def _req(fn, params, name):
        if not callable(fn):
            raise TypeError("adapter %r not callable" % name)
        missing = [p for p in params if p not in _inspect.signature(fn).parameters]
        if missing:
            raise TypeError("adapter %r lacks %s" % (name, missing))
        return fn
    decode_fn = _req(v35.decode_row_layered_fftqspa,
                     ["h_matrix", "priors", "syndromes", "max_iter",
                      "damping_alpha", "warm_beliefs", "field"], "decode_fn")
    syndrome_fn = _req(v35.syndrome_of_gf32, ["matrix", "vector"], "syndrome_fn")

    def load_prior_fn(prior_root: str):
        import numpy as _np
        root = ROOT / prior_root if not Path(prior_root).is_absolute() else Path(prior_root)
        data = _np.load(str(root / "model_f_input.npz"))
        counts = _np.asarray(data["counts_ab"])
        p_b = _np.asarray(data["p_b"], dtype=float)
        _, p_f = d5.prepare_model_f_prior_candidate(counts_ab=counts, p_b=p_b)
        return p_f
    return {"decode_fn": decode_fn, "syndrome_fn": syndrome_fn,
            "load_prior_fn": load_prior_fn}


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
        "schema": "g6r9_confirm_manifest_v1", "change_id": CHANGE_ID,
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
        "population_split": {"CAL": "702..1725 consumed", "selection": "empty",
                             "confirmation": "2123..2186 key-disjoint"},
        "key_disjointness": "confirmation disjoint from CAL/VAL",
        "SECURITY_MODEL": "generic-only", "graph_seeds": list(GRAPH_SEEDS),
        "coefficient_namespace": COEFF_NAMESPACE_TMPL % 2026094720,
        "domain_namespace": DOMAIN_NAMESPACE,
        "budgets": {"scientific_calls": SCI_CEILING, "setup_calls": SETUP_CEILING},
        "setup_calls": setup_calls, "evidence_files": list(EVIDENCE_FILES),
        "authorization": "separate explicit grant required for --execute-real",
    }
    summary = {
        "schema": "g6r9_confirm_summary_v1", "terminal": terminal,
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
    lines = ["# R9 CONFIRM m100 report", "",
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


def _to_bool(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes")


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
        # because exact/syndrome/tag isolation requires full 128 for R9).
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
    parser = argparse.ArgumentParser(description="R9 CONFIRM m100 thin runner")
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
    print("R9 terminal=%s attempted=%d exact=%d accepted=%d undetected=%d"
          % (summary["terminal"], summary["attempted"], summary["exact"],
             summary["accepted"], summary["undetected"]))
    return 0 if summary["terminal"] == "COMPLETE_128" else 1


if __name__ == "__main__":
    raise SystemExit(main())
