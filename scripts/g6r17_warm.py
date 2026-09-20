"""R17 WARM nested-prefix runner — DECIDE-readiness (NOT execution).

R17b scope (frozen R17 packet, this session): readiness for the frozen R17
packet — same pool/graphs/stages/accounting as R11-cold, plus a warm-start
arm that carries final beliefs S0->S1->S2 as decoder init. R17b makes ZERO
real calls: no construction, no decoder calls, no symbol reads, no pool
reads at all, no UUID root.

- P-pop: R9's exact paired pool (same as R11): session `20260107_PPLN_1p5M`,
  frames 2123..2186 (64 frames -> 128 blocks, frame->block order,
  even/odd mother). Allowlist ONLY that window (reused R11 plan gate).
- P-op: L020 mother m120 (E349, var {2:35,3:93}, check {2:11,3:109});
  nested prefixes rows 1..100 (S0) / 1..108 (S1) / 1..120 (S2).
  Per-prefix arithmetic is the verbatim R7 S7 sheet (DE PASS points, no
  interpolation): S0 {3:51,4:49} rate 0.21875; S1 {3:83,4:25} rate
  0.15625; S2 {2:11,3:109} rate 0.0625; E349 everywhere.
- P-dec: row-layered 90/1.0 per stage, syndrome+tag verify per stage;
  staged-new-parity-only (S1 adds rows 101..108, S2 adds rows 109..120);
  blind same-row retry FORBIDDEN (stage m strictly increases; enforced in
  code). Cold (--warm-start 0, default) delegates per-block to the frozen
  R11 staged loop (byte-identical). Warm (--warm-start 1) carries the
  prior stage's final beliefs (N,Q) as the next stage's init; S0 starts
  cold. Prior/syndrome/tag/verify rules are identical both paths, so warm
  changes trajectory only via init (no threshold retuning: bias guard).
- P-acct: nested-prefix disclosure helper charges the FINAL prefix
  only: 5*m_final+64 (564/604/664), tag once, C/I/A=0. Sum-over-stages
  accounting must FAIL verify. Disclosure sums include failures
  (exhausted charged 664). k_sym nominal per final = n-m_final
  (28/20/8, derived); beta derived-only; net_secret via R16 helper.
- P-stop: per-stage stopping (success->accept+record m_final;
  fail+stages-left->next stage; S2-fail->exhausted); UNDETECTED_STOP
  global break (retain all, terminal). Both paths.
- P-pair: fixed baseline F imported READ-ONLY from R9 artifacts (zero
  fixed decode calls asserted; byte-identical post-import asserted);
  paired lift = warm_exact - F; lift gate >= 4 (diagnostic-first, stated
  for R17c routing). R11-cold reference A imported READ-ONLY from R11
  artifacts (same zero-call/byte-identical asserts); lift_vs_cold =
  warm_exact - A is diagnostic-only (no gate).
- P-bud: sci<=384 (128 blocks x <=3 stages) / setup<=8. Both paths.
- P-cmd: flags below; --execute-real refuses without
  --execution-authorized (rc=2) before any root/bind/load.
- Construction = R17c START pre-phase as setup<=8 with admission gate:
  the R11c-admitted REUSED pair (seeds 4722/4723, g6r11 namespaces;
  deterministic rebuild = identical graphs; R11c admission artifacts
  valid by reference). R17b constructs NOTHING (admission predicate
  STATED in the R11 lineage module).

Lineage: R11 binds reused by import (no copied kernels): staged loop
(cold path), build_call_plan, build_mother, check_nested_prefixes,
final_prefix_disclosure, load_fixed_baseline, seed disjointness, arith
sheet, block/stage schemas. R9 binds reused transitively (parse_frames,
_pre_execute_check, _candidate_tag, marginal_l2_prior,
bind_production_adapters, _hard_fail_oracle_app, net_secret_bits).
Decoder/syndrome/PEG/v10 kernels reused by import (v35, r2, common).

Delta vs R11 (this file only): --warm-start {0|1} (default 0);
run_one_stage_warm (warm_beliefs passthrough + final_beliefs capture);
run_one_block_staged_warm (S0->S1->S2 belief carry); load_cold_reference
(R11 A anchor); mode-consistent manifest/summary/verifier/profile.

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

from comparison_bench.formal_ir import v72p2d10_mixed_degree_l1 as r2  # noqa: E402

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _load_lineage(name: str, filename: str):
    _spec = importlib.util.spec_from_file_location(
        name, str(_SCRIPTS_DIR / filename))
    assert _spec is not None and _spec.loader is not None
    mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(mod)
    return mod


g11 = _load_lineage("g6r11_adaptive_lineage", "g6r11_adaptive.py")
r9 = g11.r9

# Frozen identifiers (P-op/P-dec/P-pop/P-bud/P-cmd/P-pair) — via R11 import.
CHANGE_ID = "g6r17-warm"
CYCLE_ID = "G6R17-WARM"
N = g11.N
M_MOTHER = g11.M_MOTHER
Q = g11.Q
MAX_ITER = g11.MAX_ITER
DAMPING = g11.DAMPING
BITS_PER_ROW = g11.BITS_PER_ROW
TAG_BITS = g11.TAG_BITS
H_FROZEN = g11.H_FROZEN
H_L2 = g11.H_L2
EDGE_TOTAL = g11.EDGE_TOTAL
ARM = g11.ARM
CANDIDATE_ID = g11.CANDIDATE_ID
VAR_COUNTS = g11.VAR_COUNTS
CHECK_PROFILES = g11.CHECK_PROFILES
RATES = g11.RATES
DE_DELTAS = g11.DE_DELTAS
STAGE_IDS = g11.STAGE_IDS
STAGE_MS = g11.STAGE_MS
NEW_PARITY_ROWS = g11.NEW_PARITY_ROWS
K_SYM_NOMINAL = g11.K_SYM_NOMINAL
MOTHER_SEEDS = g11.MOTHER_SEEDS
DOMAIN_NAMESPACE = g11.DOMAIN_NAMESPACE
COEFF_NAMESPACE_TMPL = g11.COEFF_NAMESPACE_TMPL
FROZEN_REGISTRY = g11.FROZEN_REGISTRY
FROZEN_SESSION = g11.FROZEN_SESSION
FROZEN_FRAMES = g11.FROZEN_FRAMES
FROZEN_PRIOR_ROOT = g11.FROZEN_PRIOR_ROOT
BASELINE_ROOT = g11.BASELINE_ROOT
COLD_ROOT = "workspace/g6r11_adaptive_3c2b5b2e-897b-467e-a3e6-0cba005914ae"
FUTURE_ROOT_UUID = "47bfa9b9-e944-4bad-a105-69bc92a66045"
FUTURE_ROOT = "workspace/g6r17_warm_" + FUTURE_ROOT_UUID
SCI_CEILING = g11.SCI_CEILING
SETUP_CEILING = g11.SETUP_CEILING
PAIRED_LIFT_GATE = g11.PAIRED_LIFT_GATE
EVIDENCE_FILES = g11.EVIDENCE_FILES
BLOCK_COLUMNS = g11.BLOCK_COLUMNS
STAGE_COLUMNS = g11.STAGE_COLUMNS

# R16 true net reuses the canonical r9 helper (inherit by import, no duplicate).
net_secret_bits = r9.net_secret_bits
final_prefix_disclosure = g11.final_prefix_disclosure
check_nested_prefixes = g11.check_nested_prefixes
build_mother = g11.build_mother
build_call_plan = g11.build_call_plan
verify_seed_disjointness = g11.verify_seed_disjointness
arith_sheet = g11.arith_sheet

DECODER_SCHEDULE_COLD = ("cold row-layered per stage, staged-new-parity-only,"
                         " same-row retry forbidden")
DECODER_SCHEDULE_WARM = ("warm row-layered 90/1.0 per stage (S0 cold init;"
                         " S1/S2 init = prior-stage final beliefs (N,Q)),"
                         " staged-new-parity-only, same-row retry forbidden;"
                         " prior/syndrome/tag/verify/accounting identical")


def frozen_command(warm_start: int) -> str:
    """Canonical frozen ARGV for one mode (warm=1 is the R17c command)."""
    return (
        ".venv/bin/python scripts/g6r17_warm.py --execute-real "
        "--execution-authorized --warm-start %d --registry %s --session %s "
        "--frames %s --arm %s --prior-root %s --baseline-root %s "
        "--cold-root %s --out-dir %s"
        % (int(warm_start), FROZEN_REGISTRY, FROZEN_SESSION, FROZEN_FRAMES,
           ARM, FROZEN_PRIOR_ROOT, BASELINE_ROOT, COLD_ROOT, FUTURE_ROOT))


FROZEN_COMMAND = frozen_command(1)
FROZEN_COMMAND_COLD = frozen_command(0)


def run_one_stage_warm(prefix_H: np.ndarray, prior: np.ndarray,
                       syndrome: np.ndarray, ref_tag: bytes,
                       truth_u2: np.ndarray, stage_id: str, m: int,
                       decode_fn, syndrome_fn, tag_fn, call_idx: int,
                       warm_beliefs=None) -> tuple[dict, object]:
    """Single 90/1.0 decode at one nested prefix; truth post-only.

    Delta vs R11 cold init (g6r11_adaptive.py run_one_stage): the decode
    call carries warm_beliefs through instead of None; the decoder's
    final_beliefs are captured as the next stage's carry (None when
    absent/misshapen/non-finite -> next stage starts cold).
    """
    H = np.asarray(prefix_H, dtype=np.uint8)
    syn = np.asarray(syndrome, dtype=np.uint8)
    truth = np.asarray(truth_u2, dtype=np.int64)
    carry = None
    if isinstance(warm_beliefs, np.ndarray) \
            and warm_beliefs.shape == (N, Q) \
            and bool(np.all(np.isfinite(warm_beliefs))):
        carry = np.asarray(warm_beliefs, dtype=np.float64)
    t0 = time.perf_counter()
    rec: dict = {
        "call_idx": int(call_idx), "stage": stage_id, "m": int(m),
        "finite": False, "syndrome_match": False, "tag_match": False,
        "accepted": False, "iters": -1, "residual": -1, "provenance": "",
        "wall_s": 0.0, "crash": False, "error": ""}
    try:
        result = decode_fn(H, np.asarray(prior, dtype=np.float64), syn,
                           max_iter=MAX_ITER, damping_alpha=DAMPING,
                           warm_beliefs=carry, field=None)
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
        final = getattr(result, "final_beliefs", None)
        next_carry = None
        if isinstance(final, np.ndarray) and final.shape == (N, Q) \
                and bool(np.all(np.isfinite(final))):
            next_carry = np.asarray(final, dtype=np.float64)
        return rec, next_carry
    except Exception as exc:  # retained crash, never retried
        rec.update({"crash": True, "error": repr(exc)[:300],
                    "wall_s": time.perf_counter() - t0})
        return rec, None


def run_one_block_staged_warm(mother: dict, prior: np.ndarray,
                              truth_u2: np.ndarray, entry: dict,
                              decode_fn, syndrome_fn, tag_fn,
                              call_idx: int) -> tuple[dict, list[dict]]:
    """S0->S1->S2 warm loop; final beliefs carried as next-stage init."""
    if mother.get("dense") is None or not bool(mother.get("admitted")):
        raise r2.StructureNotAdmitted("non-admitted R17 mother")
    nested_ok, nested_reason = check_nested_prefixes(mother)
    if not nested_ok:
        raise ValueError("non-nested R17 mother: %s" % nested_reason)
    truth = np.asarray(truth_u2, dtype=np.int64)
    ref_tag = tag_fn(truth)
    stage_rows: list[dict] = []
    prev_m = 0
    carry = None  # S0 starts cold; S1/S2 init = prior final beliefs
    accepted_stage: int | None = None
    for pos, (stage_id, m) in enumerate(zip(STAGE_IDS, STAGE_MS)):
        if not int(m) > prev_m:  # blind same-row retry FORBIDDEN
            raise ValueError("non-increasing stage m (retry forbidden)")
        prev_m = int(m)
        prefix_H = np.asarray(mother["prefixes"][int(m)]["matrix"],
                              dtype=np.uint8)
        syn = np.asarray(syndrome_fn(prefix_H, truth), dtype=np.uint8)
        srec, carry = run_one_stage_warm(
            prefix_H, prior, syn, ref_tag, truth, stage_id, int(m),
            decode_fn, syndrome_fn, tag_fn, call_idx, warm_beliefs=carry)
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
    # candidate was retained by run_one_stage_warm (retention only, no extra
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


def load_cold_reference(cold_root: str) -> dict:
    """READ-ONLY import of the R11-cold same-pool reference A (zero calls)."""
    base = g11.load_fixed_baseline(cold_root)  # read-only; symbols untouched
    summary = json.loads(
        (Path(cold_root) / "summary.json").read_text(encoding="utf-8"))
    terminal = str(summary.get("terminal", ""))
    if terminal != "COMPLETE_128":
        raise ValueError("cold reference terminal %r not pairable" % terminal)
    if int(summary.get("accepted", -1)) != base["F"] \
            or int(summary.get("exact", -2)) != base["F"]:
        raise ValueError("cold reference summary != block import (not pairable)")
    return {"A": base["F"], "sha256": base["sha256"], "rows": base["rows"],
            "successes": base["successes"], "terminal": terminal,
            "cold_root": str(Path(cold_root))}


def run_authorized_batch(out_root: str, registry: str, session_id: str,
                         frames_spec: str, arm: str, prior_root: str,
                         baseline_root: str, cold_root: str = COLD_ROOT,
                         warm_start: int = 0, *,
                         adapters=None, reader_override=None,
                         tag_fn=None) -> dict:
    """Execute frozen 128-block staged matrix (cold or warm); returns bundle."""
    warm = bool(int(warm_start))
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
    # Counting wrapper: proves sci accounting + zero fixed/cold-decode calls.
    inner_decode = adapters["decode_fn"]
    calls: list[int] = []

    def counting_decode(H, priors, syn, **kw):
        calls.append(1)
        return inner_decode(H, priors, syn, **kw)

    decode_fn, syndrome_fn = counting_decode, adapters["syndrome_fn"]
    n_before_imports = len(calls)
    baseline = g11.load_fixed_baseline(baseline_root)
    cold = load_cold_reference(cold_root)
    assert len(calls) == n_before_imports, "fixed/cold import made decode calls"
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
    staged_fn = run_one_block_staged_warm if warm else g11.run_one_block_staged
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
        block, stages = staged_fn(
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
    # Byte-identical post-import: both references unchanged by our run.
    post = hashlib.sha256(
        Path(baseline_root, "block_records.csv").read_bytes()).hexdigest()
    assert post == baseline["sha256"], "baseline mutated during run"
    post_cold = hashlib.sha256(
        Path(cold_root, "block_records.csv").read_bytes()).hexdigest()
    assert post_cold == cold["sha256"], "cold reference mutated during run"
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
    reconciled = sum(int(K_SYM_NOMINAL[int(b["m_final"])]) * 5
                     for b in block_records if b["verified_exact"])
    net_secret = net_secret_bits(accepted, leak_sum, N)
    lift = exact - int(baseline["F"])
    lift_vs_cold = exact - int(cold["A"])
    manifest = {
        "schema": "g6r17_warm_manifest_v1", "change_id": CHANGE_ID,
        "cycle": CYCLE_ID, "command": frozen_command(1 if warm else 0),
        "warm_start": 1 if warm else 0,
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
                    "warm_start": 1 if warm else 0,
                    "schedule": DECODER_SCHEDULE_WARM if warm
                    else DECODER_SCHEDULE_COLD},
        "disclosure_rule": "final-prefix 5*m_final+64, tag once, C/I/A=0; "
                           "sum-over-stages FAILs verify",
        "baseline": {"root": baseline["baseline_root"], "F": baseline["F"],
                     "sha256": baseline["sha256"],
                     "successes": baseline["successes"],
                     "import": "read-only, zero fixed decode calls, "
                               "byte-identical post-import"},
        "cold_reference": {"root": cold["cold_root"], "A": cold["A"],
                           "sha256": cold["sha256"],
                           "terminal": cold["terminal"],
                           "import": "read-only, zero cold decode calls, "
                                     "byte-identical post-import"},
        "paired_gate": {"lift": None, "gate": PAIRED_LIFT_GATE,
                        "rule": "paired-diagnostic-first: lift = "
                                "warm_exact - F >= 4"},
        "paired_vs_cold": {"lift_vs_cold": None,
                           "rule": "diagnostic-only: warm_exact - A (no gate)"},
        "population_split": {"CAL": "702..1725 consumed", "selection": "empty",
                              "confirmation": "2123..2186 key-disjoint "
                                              "(paired with R9/R11)"},
        "SECURITY_MODEL": "generic-only",
        "mother_seeds": list(MOTHER_SEEDS),
        "coefficient_namespace": COEFF_NAMESPACE_TMPL % 2026094722,
        "domain_namespace": DOMAIN_NAMESPACE,
        "admission_predicate": g11.ADMISSION_PREDICATE,
        "budgets": {"scientific_calls": SCI_CEILING,
                    "setup_calls": SETUP_CEILING},
        "setup_calls": setup_calls, "evidence_files": list(EVIDENCE_FILES),
        "authorization": "separate explicit grant required for --execute-real",
    }
    summary = {
        "schema": "g6r17_warm_summary_v1", "terminal": terminal,
        "warm_start": 1 if warm else 0,
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
        "cold_A": int(cold["A"]), "lift_vs_cold": lift_vs_cold,
        "scientific_calls": len(calls), "setup_calls": setup_calls,
        "out_root": str(resolved)}
    manifest["paired_gate"]["lift"] = lift
    manifest["paired_vs_cold"]["lift_vs_cold"] = lift_vs_cold
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
    lines = ["# R17 WARM nested-prefix report (warm_start=%d)"
             % summary["warm_start"], "",
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
             "- cold_A/lift_vs_cold (diagnostic): %d/%d"
             % (summary["cold_A"], summary["lift_vs_cold"]),
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
    try:
        warm = int(manifest.get("warm_start", -1))
    except (TypeError, ValueError):
        warm = -1
    if warm not in (0, 1):
        print("VERIFY warm_start not 0/1")
        return False
    if manifest.get("command") != frozen_command(warm):
        print("VERIFY command != frozen (mode %d)" % warm)
        return False
    if int(summary.get("warm_start", -2)) != warm:
        print("VERIFY summary warm_start != manifest")
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
    # Cold-reference diagnostic recompute against manifest-recorded A.
    cold_a = int(manifest.get("cold_reference", {}).get("A", -1))
    if int(summary.get("cold_A", -2)) != cold_a:
        violations.append("cold_A != manifest")
    if int(summary.get("lift_vs_cold", -999999)) != exact - cold_a:
        violations.append("lift_vs_cold != exact - A")
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
    """R11 mother seeds/namespaces avoid the frozen ban set (via import)."""
    return g11.verify_seed_disjointness()


def profile_only() -> dict:
    """Pre-construction dry run: warm plan + proofs; zero everything."""
    frames = r9.parse_frames(FROZEN_FRAMES)
    plan = build_call_plan(frames)
    baseline = g11.load_fixed_baseline(BASELINE_ROOT)  # read-only, zero decode
    cold = load_cold_reference(COLD_ROOT)  # read-only, zero decode
    future = (ROOT / FUTURE_ROOT).resolve()
    disjoint = verify_seed_disjointness()
    return {
        "graphs_constructed": 0, "decoder_calls": 0, "model_f_loads": 0,
        "real_pool_reads": 0, "symbol_reads": 0,
        "warm_start": 1, "decoder_schedule": DECODER_SCHEDULE_WARM,
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
        "cold_reference": {"A": cold["A"], "sha256": cold["sha256"],
                           "terminal": cold["terminal"]},
        "admission_predicate": "STATED, NOT EXECUTED (R11 lineage; R17c setup<=8 gate)",
        "future_root": str(future), "future_root_absent": not future.exists(),
        "lift_gate": PAIRED_LIFT_GATE,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="R17 warm runner")
    parser.add_argument("--registry", default=FROZEN_REGISTRY)
    parser.add_argument("--session", default=FROZEN_SESSION)
    parser.add_argument("--frames", default=FROZEN_FRAMES)
    parser.add_argument("--arm", default=ARM)
    parser.add_argument("--prior-root", default=FROZEN_PRIOR_ROOT)
    parser.add_argument("--baseline-root", default=BASELINE_ROOT)
    parser.add_argument("--cold-root", default=COLD_ROOT)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--warm-start", type=int, choices=(0, 1), default=0)
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
            args.arm, args.prior_root, args.baseline_root, args.cold_root,
            int(args.warm_start),
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
    print("R17 warm_start=%d terminal=%s attempted=%d exact=%d accepted=%d "
          "undetected=%d lift=%d lift_vs_cold=%d"
          % (summary["warm_start"], summary["terminal"], summary["attempted"],
             summary["exact"], summary["accepted"], summary["undetected"],
             summary["paired_lift"], summary["lift_vs_cold"]))
    return 0 if summary["terminal"] == "COMPLETE_128" else 1


if __name__ == "__main__":
    raise SystemExit(main())
