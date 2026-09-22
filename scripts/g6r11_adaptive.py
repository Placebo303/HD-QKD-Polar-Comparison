"""R11 ADAPTIVE nested-prefix runner — DECIDE-readiness (NOT execution).

R11b scope (frozen R11 packet, this session): readiness for the frozen R11
packet — M-mother m120, S0-S2 = 100/108/120 nested prefixes, cumulative
final-prefix accounting, no-retry-rewrite, paired-diagnostic-first on R9's
128 blocks with >=4 lift gate, sci<=384. R11b makes ZERO real calls:
no construction, no decoder calls, no symbol reads, no UUID root.

- P-pop: R9's exact paired pool (quote R9 PREREG): session
  `20260107_PPLN_1p5M`, frames 2123..2186 (64 frames -> 128 blocks,
  frame->block order, even/odd mother). Allowlist ONLY that window.
- P-op: L020 mother m120 (E349, var {2:35,3:93}, check {2:11,3:109});
  nested prefixes rows 1..100 (S0) / 1..108 (S1) / 1..120 (S2).
  Per-prefix arithmetic is the verbatim R7 S7 sheet (DE PASS points, no
  interpolation): S0 {3:51,4:49} rate 0.21875; S1 {3:83,4:25} rate
  0.15625; S2 {2:11,3:109} rate 0.0625; E349 everywhere.
- P-dec: cold row-layered 90/1.0 per stage, syndrome+tag verify per
  stage; staged-new-parity-only (S1 adds rows 101..108, S2 adds rows
  109..120); blind same-row retry FORBIDDEN (stage m strictly
  increases; enforced in code).
- P-acct: nested-prefix disclosure helper charges the FINAL prefix
  only: 5*m_final+64 (564/604/664), tag once, C/I/A=0. Sum-over-stages
  accounting must FAIL verify. Disclosure sums include failures
  (exhausted charged 664). k_sym nominal per final = n-m_final
  (28/20/8, derived); beta derived-only.
- P-stop: per-stage stopping (success->accept+record m_final;
  fail+stages-left->next stage; S2-fail->exhausted); UNDETECTED_STOP
  global break (retain all, terminal).
- P-pair: fixed baseline F imported READ-ONLY from R9 artifacts
  (zero fixed decode calls asserted; byte-identical post-import
  asserted); paired lift = adaptive_exact - F; lift gate >= 4
  (diagnostic-first, stated for R11c routing).
- P-bud: sci<=384 (128 blocks x <=3 stages) / setup<=8.
- P-cmd: flags below; --execute-real refuses without
  --execution-authorized (rc=2) before any root/bind/load.
- Construction = R11c START pre-phase as setup<=8 with admission gate:
  non-admitted mother -> ENGINEERING_BLOCKED, zero decoder calls.
  R11b constructs NOTHING (admission predicate STATED below).

Lineage: R9 binds reused by import (no copied kernels): parse_frames,
_pre_execute_check, _candidate_tag, marginal_l2_prior,
bind_production_adapters, _hard_fail_oracle_app, disclosed_bits formula.
Decoder/syndrome/PEG/v10 kernels reused by import (v35, r2, common).

Forbidden: decoder calls on real data; symbol reads; creating the UUID
root; constructing mother graphs NOW; editing frozen files; protected
writes; commit/push.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "comparison_bench" / "src"))

from comparison_bench.formal_ir import nonbinary_v10_common as common  # noqa: E402
from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as r2  # noqa: E402

_SCRIPTS_DIR = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "g6r9_confirm_lineage", str(_SCRIPTS_DIR / "g6r9_confirm.py"))
assert _spec is not None and _spec.loader is not None
r9 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r9)

# Frozen identifiers (P-op/P-dec/P-pop/P-bud/P-cmd/P-pair).
CHANGE_ID = "g6r11-adaptive"
CYCLE_ID = "G6R11-ADAPTIVE"
N = 128
M_MOTHER = 120
Q = 32
MAX_ITER = 90
DAMPING = 1.0
BITS_PER_ROW = 5
TAG_BITS = 64
H_FROZEN = r9.H_FROZEN
H_L2 = r9.H_L2
EDGE_TOTAL = 349
ARM = r9.ARM
CANDIDATE_ID = r9.CANDIDATE_ID
VAR_COUNTS = {2: 35, 3: 93}  # verbatim R7 S7 (all prefixes)
# Verbatim R7 S7 check splits (DE PASS points, no interpolation).
CHECK_PROFILES = {100: {3: 51, 4: 49}, 108: {3: 83, 4: 25},
                  120: {2: 11, 3: 109}}
RATES = {100: 0.21875, 108: 0.15625, 120: 0.0625}
DE_DELTAS = {100: 0.6835301153656221, 108: 0.9960301153656221,
             120: 1.4647801153656221}  # frozen forward context only
STAGE_IDS = ("S0", "S1", "S2")
STAGE_MS = (100, 108, 120)
assert tuple(sorted(STAGE_MS)) == STAGE_MS and len(set(STAGE_MS)) == 3
NEW_PARITY_ROWS = (100, 8, 12)  # S0 base rows; S1 +rows 101..108; S2 +109..120
K_SYM_NOMINAL = {m: N - m for m in STAGE_MS}  # 28/20/8, derived  # SUPERSEDED by net_secret_bits (R16 correction): k-based retained double-charges parity; see V72P3R16-CORRECTION/
assert K_SYM_NOMINAL == {100: 28, 108: 20, 120: 8}
# Fresh mother seeds: first free >= 4722 (ban: 4601/4602, 4701..4708,
# 4711..4719, 4720/4721 + D8/D9/D12/D16/D19 namespaces; proven in T4/tests).
MOTHER_SEEDS = (2026094722, 2026094723)
DOMAIN_NAMESPACE = "g6r11-domain"
COEFF_NAMESPACE_TMPL = "g6r11:coeff:n128:L020:120:%d"
FROZEN_REGISTRY = r9.FROZEN_REGISTRY
FROZEN_SESSION = r9.FROZEN_SESSION
FROZEN_FRAMES = r9.FROZEN_FRAMES
FROZEN_PRIOR_ROOT = r9.FROZEN_PRIOR_ROOT
BASELINE_ROOT = "workspace/g6r9_confirm_3f9a1c2e-7b4d-4e8a-9c1f-2d5e6a7b8c9d"
FUTURE_ROOT_UUID = "3c2b5b2e-897b-467e-a3e6-0cba005914ae"
FUTURE_ROOT = "workspace/g6r11_adaptive_" + FUTURE_ROOT_UUID
SCI_CEILING = 384  # 128 blocks x <=3 stages
SETUP_CEILING = 8
PAIRED_LIFT_GATE = 4  # paired-diagnostic-first: adaptive_exact - F >= 4
EVIDENCE_FILES = ("manifest.json", "block_records.csv", "stage_records.csv",
                  "summary.json", "report.md")
BLOCK_COLUMNS = tuple(r9.BLOCK_COLUMNS) + (
    "m_final", "stage", "stages_attempted", "new_parity_rows")
STAGE_COLUMNS = (
    "call_idx", "frame_id", "block_id", "session_id", "stage", "m",
    "new_parity_rows", "cumulative_disclosure_bits", "finite",
    "syndrome_match", "tag_match", "accepted", "iters", "residual",
    "provenance")
ADMISSION_PREDICATE = (
    "STATED, NOT EXECUTED (R11b): at R11c START as setup<=8, build one "
    "m120 mother per seed via the accepted D10-R2 "
    "connectivity-first build_degree_sequence_peg with the frozen m120 "
    "profile (var {2:35,3:93}, check {2:11,3:109}, E349); one "
    "deterministic coefficient namespace "
    "v10_seed('g6r11:coeff:n128:L020:120:{graph_seed}'), uniform nonzero "
    "GF32 in sorted-edge order; require accepted A1-A6 gates (exact "
    "variable/check degrees, one component, full structural rank 120, "
    "full GF32 rank 120, deterministic replay) on the mother; nested "
    "prefixes are row slices 1..100/1..108/1..120 (realized prefix row "
    "degrees recorded, never gating); any non-admitted mother -> "
    "ENGINEERING_BLOCKED, zero decoder calls.")
FROZEN_COMMAND = (
    ".venv/bin/python scripts/g6r11_adaptive.py --execute-real "
    "--execution-authorized --registry %s --session %s --frames %s "
    "--arm %s --prior-root %s --baseline-root %s --out-dir %s"
    % (FROZEN_REGISTRY, FROZEN_SESSION, FROZEN_FRAMES, ARM,
       FROZEN_PRIOR_ROOT, BASELINE_ROOT, FUTURE_ROOT))


def final_prefix_disclosure(m_final: int) -> int:
    """Nested-prefix disclosure: 5*m_final + 64 tag once, C/I/A=0."""
    if int(m_final) not in STAGE_MS:
        raise ValueError("m_final %r not a frozen nested prefix" % m_final)
    return int(m_final) * BITS_PER_ROW + TAG_BITS


# R16 true net reuses the canonical r9 helper (inherit by import, no duplicate).
net_secret_bits = r9.net_secret_bits


def coefficient_seed(graph_seed: int) -> int:
    """Fresh coefficient stream (single R11 namespace, mother m120)."""
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


def check_nested_prefixes(mother: dict) -> tuple[bool, str]:
    """Nested row-order gate: slices (0,m) for strictly increasing m."""
    prefixes = mother.get("prefixes", {})
    ms = [int(m) for m in STAGE_MS]
    if sorted(ms) != ms or len(set(ms)) != len(ms):
        return False, "stages not strictly increasing"
    for prev, cur in zip((0,) + tuple(ms[:-1]), ms):
        if not cur > prev:
            return False, "blind same-row retry forbidden"
    for m in ms:
        pre = prefixes.get(m)
        if pre is None:
            return False, "prefix m=%d missing" % m
        if tuple(pre.get("rows", ())) != (0, int(m)):
            return False, "prefix m=%d not rows 1..%d" % (m, m)
    return True, ""


def build_mother(graph_seed: int) -> dict:
    """Build one frozen m120 mother + nested prefix slices (R11c setup)."""
    if int(graph_seed) not in MOTHER_SEEDS:
        raise ValueError("mother seed %r outside frozen R11 pair" % graph_seed)
    var = dict(VAR_COUNTS)
    check = {int(k): int(v) for k, v in CHECK_PROFILES[M_MOTHER].items()}
    construction = r2.build_degree_sequence_peg(
        N, M_MOTHER, var, check, int(graph_seed))
    record: dict = {
        "arm": ARM, "width": N, "graph_seed": int(graph_seed),
        "n": N, "m": M_MOTHER, "E": 0, "edges": [], "coefficients": [],
        "dense": None, "structure": None, "prefixes": {},
        "status": "construction_failed", "admitted": False,
        "failure_reason": construction.get("failure_reason", ""),
    }
    if construction["status"] != "ok":
        return record
    coeffs = coefficients_for_edges(construction["edges"], int(graph_seed))
    dense = r2.dense_from_edges(N, M_MOTHER, construction["edges"], coeffs)
    structure = r2.structural_record(dense, var, check)
    replay = r2.build_degree_sequence_peg(
        N, M_MOTHER, var, check, int(graph_seed))
    replay_coeffs = coefficients_for_edges(replay["edges"], int(graph_seed))
    replay_ok = bool(replay["status"] == "ok"
                     and replay["edges"] == construction["edges"]
                     and replay_coeffs == coeffs)
    structure["admission"]["A6_deterministic_replay"] = replay_ok
    structure["admitted"] = bool(all(structure["admission"].values()))
    failed = [k for k, v in structure["admission"].items() if not v]
    prefixes = {int(m): {"m": int(m), "rows": (0, int(m)),
                         "matrix": np.asarray(dense)[:int(m), :]}
                for m in STAGE_MS}
    nested_ok, nested_reason = check_nested_prefixes({"prefixes": prefixes})
    admitted = bool(structure["admitted"] and nested_ok)
    record.update({
        "E": len(construction["edges"]), "edges": construction["edges"],
        "coefficients": coeffs, "dense": dense, "structure": structure,
        "prefixes": prefixes, "status": "ok", "admitted": admitted,
        "failure_reason": "" if admitted else "admission failed: %s"
        % ",".join(failed + ([] if nested_ok else [nested_reason])),
    })
    return record


def build_call_plan(frame_ids: list[int]) -> list[dict]:
    """Frozen 128-call plan: frame->block->mother even/odd, staged S0-S2."""
    frames = [int(f) for f in frame_ids]
    if len(frames) != 64 or frames[0] != 2123 or frames[-1] != 2186:
        raise ValueError("R11 plan requires exactly frames 2123..2186")
    plan = []
    for frame_idx, frame_id in enumerate(frames):
        for block_pos in (0, 1):
            global_block = frame_idx * 2 + block_pos
            plan.append({
                "call_idx": global_block, "frame_id": int(frame_id),
                "block_id": int(global_block),
                "graph_seed": int(MOTHER_SEEDS[global_block % 2]),
                "arm": ARM, "candidate_id": CANDIDATE_ID, "n": N,
                "stages": list(STAGE_MS)})
    return plan


def run_one_stage(prefix_H: np.ndarray, prior: np.ndarray,
                   syndrome: np.ndarray, ref_tag: bytes,
                   truth_u2: np.ndarray, stage_id: str, m: int,
                   decode_fn, syndrome_fn, tag_fn, call_idx: int) -> dict:
    """Single cold 90/1.0 decode at one nested prefix; truth post-only."""
    H = np.asarray(prefix_H, dtype=np.uint8)
    syn = np.asarray(syndrome, dtype=np.uint8)
    truth = np.asarray(truth_u2, dtype=np.int64)
    t0 = time.perf_counter()
    rec: dict = {
        "call_idx": int(call_idx), "stage": stage_id, "m": int(m),
        "finite": False, "syndrome_match": False, "tag_match": False,
        "accepted": False, "iters": -1, "residual": -1, "provenance": "",
        "wall_s": 0.0, "crash": False, "error": ""}
    try:
        result = decode_fn(H, np.asarray(prior, dtype=np.float64), syn,
                           max_iter=MAX_ITER, damping_alpha=DAMPING,
                           warm_beliefs=None, field=None)
        x_hat = np.asarray(result.x_hat, dtype=np.int64).ravel()
        prov = str(getattr(result, "belief_provenance", "") or "")
        if "ORACLE" in prov.upper() or "APP" in prov.upper():
            raise ValueError("ORACLE/APP provenance on real path: %r" % prov)
        finite = bool(x_hat.shape == (N,) and np.all((x_hat >= 0) & (x_hat < 32))
                      and 0 <= int(result.iterations) <= MAX_ITER
                      and np.all(np.isfinite(prior)))
        syn_match = bool(np.array_equal(np.asarray(syndrome_fn(H, x_hat)), syn))
        tag_match = bool(tag_fn(x_hat) == bytes(ref_tag))
        accepted = bool(finite and syn_match and tag_match)
        residual = int(np.count_nonzero(np.asarray(syndrome_fn(H, x_hat)) != syn))
        rec.update({
            "finite": finite, "syndrome_match": syn_match,
            "tag_match": tag_match, "accepted": accepted,
            "iters": int(result.iterations), "residual": residual,
            "provenance": prov, "wall_s": time.perf_counter() - t0,
            # Retained candidate for honest post-decision isolation
            # (retention only; stripped before any write).
            "_x_hat": np.asarray(x_hat, dtype=np.int64).copy()})
        assert (not accepted) or (finite and syn_match and tag_match)
        return rec
    except Exception as exc:  # retained crash, never retried
        rec.update({"crash": True, "error": repr(exc)[:300],
                    "wall_s": time.perf_counter() - t0})
        return rec


def run_one_block_staged(mother: dict, prior: np.ndarray,
                         truth_u2: np.ndarray, entry: dict,
                         decode_fn, syndrome_fn, tag_fn,
                         call_idx: int) -> tuple[dict, list[dict]]:
    """S0->S1->S2 staged loop; same-row retry forbidden by construction."""
    if mother.get("dense") is None or not bool(mother.get("admitted")):
        from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as _r2
        raise _r2.StructureNotAdmitted("non-admitted R11 mother")
    nested_ok, nested_reason = check_nested_prefixes(mother)
    if not nested_ok:
        raise ValueError("non-nested R11 mother: %s" % nested_reason)
    truth = np.asarray(truth_u2, dtype=np.int64)
    ref_tag = tag_fn(truth)
    stage_rows: list[dict] = []
    prev_m = 0
    accepted_stage: int | None = None
    for pos, (stage_id, m) in enumerate(zip(STAGE_IDS, STAGE_MS)):
        if not int(m) > prev_m:  # blind same-row retry FORBIDDEN
            raise ValueError("non-increasing stage m (retry forbidden)")
        prev_m = int(m)
        prefix_H = np.asarray(mother["prefixes"][int(m)]["matrix"],
                              dtype=np.uint8)
        syn = np.asarray(syndrome_fn(prefix_H, truth), dtype=np.uint8)
        srec = run_one_stage(prefix_H, prior, syn, ref_tag, truth,
                             stage_id, int(m), decode_fn, syndrome_fn,
                             tag_fn, call_idx)
        srec.update({
            "frame_id": int(entry["frame_id"]),
            "block_id": int(entry["block_id"]),
            "session_id": str(entry.get("session_id", "")),
            "new_parity_rows": int(NEW_PARITY_ROWS[pos]),
            "cumulative_disclosure_bits": final_prefix_disclosure(int(m))})
        stage_rows.append(srec)
        if srec["accepted"]:
            accepted_stage = pos
            break
    if accepted_stage is None:
        m_final, stage_id = int(STAGE_MS[-1]), "exhausted"
        stages_attempted = len(STAGE_MS)
    else:
        m_final = int(STAGE_MS[accepted_stage])
        stage_id = STAGE_IDS[accepted_stage]
        stages_attempted = accepted_stage + 1
    # Honest post-decision isolation (truth used ONLY here): the accepted
    # candidate was retained by run_one_stage (retention only, no extra
    # decode call); exact iff it equals truth. Never merged otherwise.
    last = stage_rows[-1]
    cand = last.get("_x_hat")
    if not bool(last["accepted"]):
        exact, undet = False, False
    elif cand is None:
        exact, undet = False, True  # fail closed
    else:
        exact = bool(np.array_equal(np.asarray(cand, dtype=np.int64), truth))
        undet = bool(not exact)
    block: dict = {
        "call_idx": int(call_idx), "frame_id": int(entry["frame_id"]),
        "block_id": int(entry["block_id"]),
        "session_id": str(entry.get("session_id", "")),
        "arm": ARM, "candidate_id": CANDIDATE_ID,
        "graph_seed": int(entry["graph_seed"]), "n": N, "m": m_final,
        "attempted": True, "finite": bool(last["finite"]),
        "syndrome_match": bool(last["syndrome_match"]),
        "tag_match": bool(last["tag_match"]),
        "protocol_accepted": bool(last["accepted"]),
        "verified_exact": exact, "undetected": undet,
        "outcome": "undetected" if undet else ("exact" if exact
                  else ("accepted" if last["accepted"] else
                        ("exhausted" if accepted_stage is None
                         else "attempted"))),
        "syndrome_bits": 5 * m_final, "tag_bits": TAG_BITS,
        "control_bits": 0, "interaction_bits": 0, "auth_bits": 0,
        "disclosure_bits": final_prefix_disclosure(m_final),
        "iters": int(last["iters"]), "residual": int(last["residual"]),
        "provenance": str(last["provenance"]), "wall_s": 0.0, "crash": False,
        "error": "", "m_final": m_final, "stage": stage_id,
        "stages_attempted": stages_attempted,
        "new_parity_rows": int(sum(NEW_PARITY_ROWS[:stages_attempted]))}
    assert (not exact) or bool(last["accepted"])
    assert (not undet) or (bool(last["accepted"]) and not exact)
    return block, stage_rows


def load_fixed_baseline(baseline_root: str) -> dict:
    """READ-ONLY import of R9 fixed baseline F (zero decode calls)."""
    root = Path(baseline_root)
    csv_path = root / "block_records.csv"
    raw = csv_path.read_bytes()  # read-only; symbols never touched
    digest = hashlib.sha256(raw).hexdigest()
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    if len(rows) != 128:
        raise ValueError("baseline %s rows %d != 128" % (csv_path, len(rows)))
    accepted = [rr for rr in rows if str(rr.get("protocol_accepted")) == "True"]
    exact = [rr for rr in rows if str(rr.get("verified_exact")) == "True"]
    undet = [rr for rr in rows if str(rr.get("undetected")) == "True"]
    if undet:
        raise ValueError("baseline has undetected rows (not pairable)")
    if len(accepted) != len(exact):
        raise ValueError("baseline accepted != exact (not pairable)")
    return {"F": len(exact), "sha256": digest, "rows": len(rows),
            "successes": [(int(rr["call_idx"]), int(rr["frame_id"]))
                          for rr in exact],
            "baseline_root": str(root)}


def run_authorized_batch(out_root: str, registry: str, session_id: str,
                         frames_spec: str, arm: str, prior_root: str,
                         baseline_root: str, *,
                         adapters=None, reader_override=None,
                         tag_fn=None) -> dict:
    """Execute frozen 128-block staged matrix; returns bundle."""
    resolved = r2.refuse_out_root(out_root)  # probe only; creates nothing
    pre_execute = (adapters or {}).get("pre_execute_fn") \
        if adapters else None
    frames = (pre_execute or r9._pre_execute_check)(
        registry, session_id, frames_spec, arm, prior_root)
    plan = build_call_plan(frames)
    if adapters is None:
        adapters = r9.bind_production_adapters()
    else:
        adapters = dict(adapters)
    r9._hard_fail_oracle_app(adapters)
    for key in ("decode_fn", "syndrome_fn", "load_prior_fn"):
        if adapters.get(key) is None:
            raise ValueError("adapters %s must be injected" % key)
    if tag_fn is None:
        tag_fn = adapters.get("tag_fn", r9._candidate_tag)
    # Counting wrapper: proves sci accounting + zero fixed-decode calls.
    inner_decode = adapters["decode_fn"]
    calls: list[int] = []

    def counting_decode(H, priors, syn, **kw):
        calls.append(1)
        return inner_decode(H, priors, syn, **kw)

    decode_fn, syndrome_fn = counting_decode, adapters["syndrome_fn"]
    n_before_baseline = len(calls)
    baseline = load_fixed_baseline(baseline_root)
    assert len(calls) == n_before_baseline, "fixed import made decode calls"
    p_f = adapters["load_prior_fn"](prior_root)
    # Build mothers (setup) before any decode; admission required both.
    mothers = {}
    for seed in MOTHER_SEEDS:
        mother = adapters.get("build_fn", build_mother)(seed) \
            if "build_fn" in adapters else build_mother(seed)
        if not bool(mother.get("admitted")):
            raise RuntimeError("mother %r not admitted; ENGINEERING_BLOCKED"
                               % seed)
        nested_ok, nested_reason = check_nested_prefixes(mother)
        if not nested_ok:
            raise RuntimeError("mother %r non-nested (%s); "
                               "ENGINEERING_BLOCKED" % (seed, nested_reason))
        mothers[int(seed)] = mother
    setup_calls = len(mothers) + 2  # mothers + plan + manifest
    if setup_calls > SETUP_CEILING:
        raise RuntimeError("setup %d > ceiling %d" % (setup_calls,
                                                      SETUP_CEILING))
    import pandas as pd
    session = [s for s in json.loads((ROOT / registry).read_text())["sessions"]
               if s["session_id"] == session_id][0] \
        if reader_override is None else {"provenance": None,
                                         "session_id": session_id}
    if reader_override is None:
        pairs_path = ROOT / session["provenance"]
        frame = pd.read_parquet(
            str(pairs_path),
            columns=["frame_id", "pair_idx", "alice_symbol", "bob_symbol"],
            filters=[("frame_id", "in", frames)])
    else:
        frame = reader_override(frames)
    block_records: list[dict] = []
    stage_records: list[dict] = []
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
        prior = r9.marginal_l2_prior(p_f, bob_block)
        mother = mothers[int(entry["graph_seed"])]
        block, stages = run_one_block_staged(
            mother, prior, truth_u2, {**entry, "session_id": session_id},
            decode_fn, syndrome_fn, tag_fn, entry["call_idx"])
        block_records.append(block)
        for srec in stages:
            srec = dict(srec)
            srec.pop("_x_hat", None)  # retained candidate never written
            row = {c: srec.get(c, "") for c in STAGE_COLUMNS}
            row.update({
                "frame_id": block["frame_id"], "block_id": block["block_id"],
                "session_id": block["session_id"]})
            stage_records.append(row)
        if block["undetected"]:
            break  # UNDETECTED_STOP absolute (fail-closed)
    if len(calls) > SCI_CEILING:
        raise RuntimeError("scientific calls exceed ceiling")
    # Byte-identical post-import: baseline file unchanged by our run.
    post = hashlib.sha256(
        Path(baseline_root, "block_records.csv").read_bytes()).hexdigest()
    assert post == baseline["sha256"], "baseline mutated during run"
    terminal = "UNDETECTED_STOP" if any(b["undetected"] for b in block_records) \
        else ("COMPLETE_128" if len(block_records) == 128
              else "ENGINEERING_BLOCKED")
    attempted = len(block_records)
    accepted = sum(1 for b in block_records if b["protocol_accepted"])
    exact = sum(1 for b in block_records if b["verified_exact"])
    undet = sum(1 for b in block_records if b["undetected"])
    leak_sum = sum(int(b["disclosure_bits"]) for b in block_records)
    per_stage = {s: sum(1 for b in block_records
                        if b["stage"] == s and b["verified_exact"])
                 for s in STAGE_IDS}
    denom_primary = attempted * N * H_FROZEN if attempted else None
    denom_l2 = attempted * N * H_L2 if attempted else None
    beta_primary = (1.0 - leak_sum / denom_primary) if denom_primary else None
    beta_l2 = (1.0 - leak_sum / denom_l2) if denom_l2 else None
    reconciled = sum(int(K_SYM_NOMINAL[int(b["m_final"])]) * 5  # SUPERSEDED by net_secret_bits (R16 correction): k-based retained double-charges parity; see V72P3R16-CORRECTION/
                     for b in block_records if b["verified_exact"])
    net_secret = net_secret_bits(accepted, leak_sum, N)
    lift = exact - int(baseline["F"])
    manifest = {
        "schema": "g6r11_adaptive_manifest_v1", "change_id": CHANGE_ID,
        "cycle": CYCLE_ID, "command": FROZEN_COMMAND,
        "registry": registry, "session_id": session_id, "frames": frames_spec,
        "arm": arm, "candidate_id": CANDIDATE_ID, "prior_root": prior_root,
        "out_root": str(resolved),
        "operating_point": {
            "n": N, "m_mother": M_MOTHER, "arm": ARM,
            "candidate_id": CANDIDATE_ID, "var_counts": dict(VAR_COUNTS),
            "check_profiles": {str(k): dict(v)
                               for k, v in CHECK_PROFILES.items()},
            "E": EDGE_TOTAL, "rates": {str(k): v for k, v in RATES.items()},
            "stages": [{"stage": s, "m": m,
                        "rows": "1..%d" % m,
                        "new_parity_rows": int(npr),
                        "disclosure": final_prefix_disclosure(m),
                        "k_sym_nominal": int(K_SYM_NOMINAL[m])}
                       for s, m, npr in zip(STAGE_IDS, STAGE_MS,
                                            NEW_PARITY_ROWS)]},
        "nested_row_order": "1..100/1..108/1..120",
        "decoder": {"adapter": "v35.decode_row_layered_fftqspa",
                    "max_iter": MAX_ITER, "damping_alpha": DAMPING,
                    "schedule": "cold row-layered per stage, "
                                "staged-new-parity-only, same-row retry "
                                "forbidden"},
        "disclosure_rule": "final-prefix 5*m_final+64, tag once, C/I/A=0; "
                           "sum-over-stages FAILs verify",
        "baseline": {"root": baseline["baseline_root"], "F": baseline["F"],
                     "sha256": baseline["sha256"],
                     "successes": baseline["successes"],
                     "import": "read-only, zero fixed decode calls, "
                               "byte-identical post-import"},
        "paired_gate": {"lift": None, "gate": PAIRED_LIFT_GATE,
                        "rule": "paired-diagnostic-first: lift = "
                                "adaptive_exact - F >= 4"},
        "population_split": {"CAL": "702..1725 consumed", "selection": "empty",
                              "confirmation": "2123..2186 key-disjoint "
                                              "(paired with R9)"},
        "SECURITY_MODEL": "generic-only",
        "mother_seeds": list(MOTHER_SEEDS),
        "coefficient_namespace": COEFF_NAMESPACE_TMPL % 2026094722,
        "domain_namespace": DOMAIN_NAMESPACE,
        "admission_predicate": ADMISSION_PREDICATE,
        "budgets": {"scientific_calls": SCI_CEILING,
                    "setup_calls": SETUP_CEILING},
        "setup_calls": setup_calls, "evidence_files": list(EVIDENCE_FILES),
        "authorization": "separate explicit grant required for --execute-real",
    }
    summary = {
        "schema": "g6r11_adaptive_summary_v1", "terminal": terminal,
        "attempted": attempted, "accepted": accepted, "exact": exact,
        "undetected": undet,
        "per_stage_exact": per_stage,
        "exhausted": sum(1 for b in block_records if b["stage"] == "exhausted"),
        "accepted_fraction": (accepted / attempted) if attempted else None,
        "exact_fraction": (exact / attempted) if attempted else None,
        "FER_proxy": ((attempted - exact) / attempted) if attempted else None,
        "disclosure_sum": leak_sum,
        "reconciled_net_bits": reconciled,
        "net_secret_bits": net_secret,
        "reconciled_rate": (reconciled / (attempted * N * 5))
        if attempted else None,
        "beta_eff_empirical_primary": beta_primary,
        "beta_eff_empirical_l2_sensitivity": beta_l2,
        "H_frozen_primary": H_FROZEN, "H_L2_sensitivity": H_L2,
        "baseline_F": int(baseline["F"]), "paired_lift": lift,
        "lift_gate": PAIRED_LIFT_GATE,
        "lift_gate_pass": bool(undet == 0 and lift >= PAIRED_LIFT_GATE),
        "scientific_calls": len(calls), "setup_calls": setup_calls,
        "out_root": str(resolved)}
    manifest["paired_gate"]["lift"] = lift
    return {"resolved": resolved, "manifest": manifest,
            "block_records": block_records, "stage_records": stage_records,
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
        for row in bundle["block_records"]:
            writer.writerow({c: row.get(c, "") for c in BLOCK_COLUMNS})
    with (resolved / "stage_records.csv").open("w", newline="",
                                               encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(STAGE_COLUMNS))
        writer.writeheader()
        for row in bundle["stage_records"]:
            writer.writerow({c: row.get(c, "") for c in STAGE_COLUMNS})
    (resolved / "summary.json").write_text(
        json.dumps(bundle["summary"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    summary = bundle["summary"]
    lines = ["# R11 ADAPTIVE nested-prefix report", "",
             "- terminal: `%s`" % summary["terminal"],
             "- attempted/exact/accepted/undetected: %d/%d/%d/%d"
             % (summary["attempted"], summary["exact"],
                summary["accepted"], summary["undetected"]),
             "- per_stage_exact: %s" % summary["per_stage_exact"],
             "- disclosure_sum: %d" % summary["disclosure_sum"],
             "- baseline_F/paired_lift/gate: %d/%d/>=%d (%s)"
             % (summary["baseline_F"], summary["paired_lift"],
                summary["lift_gate"],
                "PASS" if summary["lift_gate_pass"] else "FAIL"),
             "- beta_primary: %s" % summary["beta_eff_empirical_primary"],
             "- reconciled_net_bits: %d" % summary["reconciled_net_bits"]]
    (resolved / "report.md").write_text("\n".join(lines) + "\n",
                                        encoding="utf-8")
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
    brows = list(csv.DictReader(
        (root / "block_records.csv").read_text(encoding="utf-8").splitlines()))
    srows = list(csv.DictReader(
        (root / "stage_records.csv").read_text(encoding="utf-8").splitlines()))
    violations: list[str] = []
    if len(brows) != 128:
        if not any(_to_bool(rr.get("undetected")) for rr in brows):
            violations.append("partial root %d != 128" % len(brows))
    attempted = len(brows)
    accepted = sum(1 for rr in brows if _to_bool(rr.get("protocol_accepted")))
    exact = sum(1 for rr in brows if _to_bool(rr.get("verified_exact")))
    undet = sum(1 for rr in brows if _to_bool(rr.get("undetected")))
    stage_ms_seen: dict[int, list[int]] = {}
    for rr in brows:
        acc, ex, ud = (_to_bool(rr.get("protocol_accepted")),
                       _to_bool(rr.get("verified_exact")),
                       _to_bool(rr.get("undetected")))
        syn, tag, fin = (_to_bool(rr.get("syndrome_match")),
                         _to_bool(rr.get("tag_match")),
                         _to_bool(rr.get("finite")))
        try:
            m_final = int(rr.get("m_final", -1))
        except (TypeError, ValueError):
            m_final = -1
        if m_final not in STAGE_MS:
            violations.append("m_final not a frozen prefix")
        if ex and not acc:
            violations.append("exact without accepted")
        if ud and (not acc or ex):
            violations.append("undetected merged")
        if acc and not (fin and syn and tag):
            violations.append("accepted without finite+syndrome+tag")
        if m_final in STAGE_MS:
            if int(rr.get("disclosure_bits", -1)) != final_prefix_disclosure(m_final):
                violations.append("disclosure != final-prefix 5m+64")
            if int(rr.get("syndrome_bits", -1)) != 5 * m_final:
                violations.append("syndrome split != 5*m_final")
            if int(rr.get("tag_bits", -1)) != TAG_BITS:
                violations.append("tag != 64")
        if int(rr.get("control_bits", 0)) != 0 \
                or int(rr.get("interaction_bits", 0)) != 0 \
                or int(rr.get("auth_bits", 0)) != 0:
            violations.append("C/I/A != 0")
        stage = str(rr.get("stage", ""))
        if acc and stage == "exhausted":
            violations.append("accepted but exhausted")
        if not acc and stage in STAGE_IDS:
            violations.append("unaccepted but staged-accepted")
        if stage not in STAGE_IDS and stage != "exhausted":
            violations.append("unknown stage %r" % stage)
        try:
            s_attempted = int(rr.get("stages_attempted", -1))
        except (TypeError, ValueError):
            s_attempted = -1
        expect_attempts = (STAGE_IDS.index(stage) + 1) if stage in STAGE_IDS \
            else len(STAGE_MS)
        if s_attempted != expect_attempts:
            violations.append("stages_attempted != stage order")
        stage_ms_seen[int(rr.get("block_id", -1))] = []
    for sr in srows:
        try:
            m = int(sr.get("m", -1))
        except (TypeError, ValueError):
            m = -1
        if m not in STAGE_MS:
            violations.append("stage m not frozen")
            continue
        try:
            bid = int(sr.get("block_id", -1))
        except (TypeError, ValueError):
            violations.append("stage block_id bad")
            continue
        stage_ms_seen.setdefault(bid, []).append(m)
        if str(sr.get("stage", "")) != STAGE_IDS[STAGE_MS.index(m)]:
            violations.append("stage id != m order")
        if int(sr.get("cumulative_disclosure_bits", -1)) != \
                final_prefix_disclosure(m):
            violations.append("stage cumulative != final-prefix")
    for bid, ms in stage_ms_seen.items():
        if sorted(ms) != list(STAGE_MS[:len(ms)]) or len(set(ms)) != len(ms):
            violations.append("block %d stages not S0.. prefix order" % bid)
    # Accepted only at the final attempted stage (else loop kept going).
    for sr in srows:
        if _to_bool(sr.get("accepted")):
            try:
                bid = int(sr.get("block_id", -1))
            except (TypeError, ValueError):
                continue
            ms = stage_ms_seen.get(bid, [])
            if not ms or int(sr.get("m", -1)) != ms[-1]:
                violations.append("accepted non-final stage")
    leak_sum = sum(int(rr.get("disclosure_bits", 0)) for rr in brows)
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
    per_stage = {s: sum(1 for rr in brows
                        if str(rr.get("stage")) == s and _to_bool(
                            rr.get("verified_exact")))
                 for s in STAGE_IDS}
    if dict(summary.get("per_stage_exact", {})) != per_stage:
        violations.append("per_stage_exact != recomputed")
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
    # Paired lift recompute against manifest-recorded baseline F.
    base_f = int(manifest.get("baseline", {}).get("F", -1))
    if int(summary.get("baseline_F", -2)) != base_f:
        violations.append("baseline_F != manifest")
    if int(summary.get("paired_lift", -999999)) != exact - base_f:
        violations.append("paired_lift != exact - F")
    if bool(summary.get("lift_gate_pass")) != bool(
            undet == 0 and (exact - base_f) >= PAIRED_LIFT_GATE):
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


def verify_seed_disjointness() -> dict:
    """Prove mother seeds/namespaces avoid the frozen ban set."""
    banned_seeds = ({2026094601, 2026094602}
                    | set(range(2026094701, 2026094709))
                    | set(range(2026094711, 2026094720))
                    | {2026094720, 2026094721})
    banned_namespaces = {
        "d10:backbone", "d10:coeff", "peg_tie", "peg_labels",
        "de:init", "de:mut", "d19:l2:coeff", "r7s7:l2:coeff",
        "g6r1-domain", "g6r9-domain", "g6r1:coeff", "g6r9:coeff",
    }
    namespaces = {DOMAIN_NAMESPACE,
                  COEFF_NAMESPACE_TMPL % 2026094722,
                  COEFF_NAMESPACE_TMPL % 2026094723}
    seed_hits = sorted(set(MOTHER_SEEDS) & banned_seeds)
    ns_hits = sorted(n for n in namespaces
                     if any(b in n for b in banned_namespaces))
    ok = (not seed_hits and not ns_hits
          and min(MOTHER_SEEDS) >= 2026094722
          and len(set(MOTHER_SEEDS)) == 2)
    return {"passed": bool(ok), "mother_seeds": list(MOTHER_SEEDS),
            "seed_hits": seed_hits, "namespaces": sorted(namespaces),
            "namespace_hits": ns_hits}


def arith_sheet() -> list[dict]:
    """Per-prefix arithmetic sheet (R7 S7 verbatim + nested disclosure)."""
    sheet = []
    for pos, m in enumerate(STAGE_MS):
        check = {int(k): int(v) for k, v in CHECK_PROFILES[m].items()}
        assert sum(check.values()) == m
        assert sum(d * c for d, c in check.items()) == EDGE_TOTAL
        sheet.append({
            "stage": STAGE_IDS[pos], "m": int(m), "n": N, "arm": CANDIDATE_ID,
            "variable_counts": dict(VAR_COUNTS), "E": EDGE_TOTAL,
            "check_counts": check, "rate": RATES[m],
            "nominal_disclosure_bits": final_prefix_disclosure(m),
            "k_sym_nominal": int(K_SYM_NOMINAL[m]),
            "rows": "1..%d" % m, "new_parity_rows": int(NEW_PARITY_ROWS[pos]),
            "de_delta_context": DE_DELTAS[m]})
    return sheet


def profile_only() -> dict:
    """Pre-construction dry run: plan + sheet + proofs; zero everything."""
    frames = r9.parse_frames(FROZEN_FRAMES)
    plan = build_call_plan(frames)
    baseline = load_fixed_baseline(BASELINE_ROOT)  # read-only, zero decode
    future = (ROOT / FUTURE_ROOT).resolve()
    disjoint = verify_seed_disjointness()
    return {
        "graphs_constructed": 0, "decoder_calls": 0, "model_f_loads": 0,
        "real_pool_reads": 0, "symbol_reads": 0,
        "plan_calls": len(plan), "plan_order": "frame->block->mother even/odd",
        "max_stage_calls": len(plan) * len(STAGE_MS),
        "budgets": {"scientific_calls": SCI_CEILING,
                    "setup_calls": len(MOTHER_SEEDS) + 2,
                    "setup_ceiling": SETUP_CEILING},
        "budget_ok": len(plan) * len(STAGE_MS) <= SCI_CEILING
        and (len(MOTHER_SEEDS) + 2) <= SETUP_CEILING,
        "arith_sheet": arith_sheet(),
        "nested_row_order": "1..100/1..108/1..120",
        "seed_disjointness": disjoint,
        "baseline": {"F": baseline["F"], "sha256": baseline["sha256"],
                     "successes": baseline["successes"]},
        "admission_predicate": "STATED, NOT EXECUTED (R11c setup<=8 gate)",
        "future_root": str(future), "future_root_absent": not future.exists(),
        "lift_gate": PAIRED_LIFT_GATE,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="R11 adaptive runner")
    parser.add_argument("--registry", default=FROZEN_REGISTRY)
    parser.add_argument("--session", default=FROZEN_SESSION)
    parser.add_argument("--frames", default=FROZEN_FRAMES)
    parser.add_argument("--arm", default=ARM)
    parser.add_argument("--prior-root", default=FROZEN_PRIOR_ROOT)
    parser.add_argument("--baseline-root", default=BASELINE_ROOT)
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
            args.arm, args.prior_root, args.baseline_root,
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
    print("R11 terminal=%s attempted=%d exact=%d accepted=%d undetected=%d "
          "lift=%d" % (summary["terminal"], summary["attempted"],
                       summary["exact"], summary["accepted"],
                       summary["undetected"], summary["paired_lift"]))
    return 0 if summary["terminal"] == "COMPLETE_128" else 1


if __name__ == "__main__":
    raise SystemExit(main())
