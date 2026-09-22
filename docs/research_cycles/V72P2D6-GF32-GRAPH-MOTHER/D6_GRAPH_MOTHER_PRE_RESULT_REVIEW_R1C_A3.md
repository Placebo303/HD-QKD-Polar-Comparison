# D6 Graph Mother Pre-RESULT Review R1c-A3 (independent, read-only)

Status: `PRE_RESULT_REVIEW_R1C_A3`
Branch: `formal-ir-v72p1-addendum-clean`
Out-root: `workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b`
Revision: R1c-A3
Reviewer: independent second pass (operator-separated, read-only; reviewer-go
spawn tool unavailable — independence via fresh re-read of files/evidence,
no inheritance of the A2 conclusion; reviewer edits only this file).
Date-UTC: 2026-09-09
Scope: corrected keys/stages, all 184 records, crash precedence,
stored-vs-recomputed terminal, call/wall/RSS/no-retry accounting, six-file
immutability, protected roots, authorizations false, G2 absence. No decoder
execution, no edits except this file.

## Verdict

Verdict: `D6_R1C_A3_PRE_RESULT_REVIEW_PASS_BLOCKED_RUN`

The degree failures invalidate the scientific terminal. This permits
solidifying the run as an implementation/structure-blocked development
attempt — never as topology evidence. No verdict here authorizes rerun,
resume, retry, or successor execution.

## 1. Corrected verifier (A3-05, single run, read-only, zero decoder calls)

Command (once, no `--model-f-root`, no `--workers`):

```powershell
python scripts/v72p2d6_graph_mother_development.py --out-root workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b --verify
```

Exit 0, `VERIFY PASS`. All 15 checks PASS (literal output re-verified):

- six-files; call_idx-continuous n=184; **semantic-key-no-dup n=184**
  (was FAIL — now keyed with `n`); calls-consistent 184; le-2500
  (sci=184 setup=18); effective-le-requested 18/18; rss-strict
  agg=1697669120; wall-budget 8349.6; terminal-replay (stored string);
  timeout-watchdog n=184; pid-present pids=18; seed-domain n=184; coverage
  5 arms; **scaling-recompute adv=[] w=64** (was FAIL — now stage-separated);
  manifest-consistent itmax=90.
- Decision-layer INFO (non-gating, frozen A3-00 split):
  `stored-terminal D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY`;
  `recomputed-terminal D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED
  degree-invariant:64`; `terminal-agreement False governs=
  D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED`;
  `confirmation-stage EMPTY_NOT_EVIDENCE`.

## 2. Records (independently recomputed from the six files)

- 184 rows, `call_idx` 1..184 continuous; corrected identity
  `(n,arm,seed,point,mode)` 184 unique (old n-agnostic key 144 + 40 dup
  groups, all T1/M1 cross-width — matches forensic table).
- attempted 184, skipped 0; crash=True 64 = nonfinite 64, identical rows;
  all 64 carry `ValueError('Check node requires degree >= 2')`; zero other
  errors. Crash map: `(64,T3)` 16, `(64,M1)` 16, `(128,M1)` 16, `(256,M1)`
  16 — arm-perfect.
- Stages: canary 104 (n64 + canary seeds, 5 arms, no scaling-seed
  contamination); scaling-n128 40 + scaling-n256 40 (arms T1+M1 = frozen
  `best_T`/`best_M`); confirmation 0 rows (EMPTY, not safety); outside all
  seed domains 0.
- Canary per-cell app recompute and `select_advancement` ⇒ `[]` = stored;
  scaling sig zero at both widths (per-row exacts never coincide L1+APP in
  one cell) ⇒ no confirmation dispatch, width stays 64. Selection/
  advancement/stop-width logic consistent with stored scalars.
- Crash precedence (frozen rule 5+6): 64 attempted degree rows ⇒ stored
  topology label is unsupported; recomputed
  `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED` governs (fail-closed); agreement
  False honestly reported, not rewritten.

## 3. Degree-failure source (forensic, no decoder calls)

- Raised at `v35_algorithm_development.py:465` (`dc<2`): dispatched H slices
  contain check rows of degree <2.
- M1: code-independent integer proof from frozen scalars (`zero_rows=0`,
  `rmax=3`, `sumsq=364` over k=64 ⇒ ≥4 degree-1 rows necessarily; holds at
  every dispatched M1 prefix).
- T3+M1: structure-only rebuild (`build_support`, deterministic; builder
  code identical between generation commit `15f1de79` and HEAD — that
  commit's mother diff is 2-line fsync-only): every dispatched T3/M1 slice
  has min row degree 1; all succeeding slices (T1 all widths, B0) have min
  ≥2 (negative controls).
- Transport/precondition excluded: same 18-worker pool + decoder binary
  delivered 120 clean rows for B0/B1/T1; `determinism_ok=True` everywhere;
  L1+oracle crash identically per cell. Random corruption cannot produce an
  arm-perfect pattern.
- Source verdict: **invalid frozen graph structure** (degree-1 check rows
  admitted by audits gating on `zero_rows`/`eligible` but never on minimum
  check degree). No guessing; `NOT_VERIFIABLE` not needed.

## 4. Accounting / immutability / boundaries

- Calls 184+18=202 ≤ 2500; wall 8349.6 ≤ 43200, chunks 3.2/3.0/7.2 s, no
  block; req=eff=18, aggregate 1697669120 < 2 GiB; respawn 0, timeouts 0,
  per-call max 3.65 s ≤ 120, watchdog all True ⇒ no retry/respawn.
- Six files byte-present with A2-recorded sizes; mtimes unchanged
  (15:17:52 / 12:59:11 / 15:17:43) ⇒ A3-05 verify wrote nothing; root
  immutable and uncommitted.
- Protected roots: Model-F metadata only (752 / 208467 bytes, 2026-09-07);
  VOID roots name-only (never opened); no formal writes; no second root.
- `cycle_state.yaml`: every execution key false
  (`development_decoder_authorized false`, …, `scientific_promotion false`,
  `g2_execution_authorized false`); `evidence_root`/`terminal` null.
- G2 absent (no D6 G2 artifact); no VAL/real/raw; CAL-only boundary kept.
- Claim ceiling: the strongest allowed solidification is
  "implementation/structure-blocked development attempt at the frozen
  T3/M1 prefixes". Any topology-no-recovery, FER, leakage, or key-rate
  claim from this root is forbidden.

## 5. Why not FAIL / why not SCIENTIFIC

- Not FAIL: the A2 verifier defects are repaired and mechanically proven
  (15/15 PASS on the immutable root); stages/keys/counts all reconcile; the
  terminal disagreement is reported fail-closed per the frozen contract
  rather than hidden — the exact behavior A3 was chartered to produce.
- Not SCIENTIFIC: 64 attempted invariant crashes precede any scientific
  label; confirmation is empty; scaling shows zero end-to-end APP cells.
  Nothing in this root supports a topology or recovery claim.

## Checklist

- [x] Matches frozen A3 prereg + OpenSpec A3 delta + A3 tasks
- [x] Corrected verifier output independently re-verified (15 PASS + INFO)
- [x] All 184 records, precedence, stored-vs-recomputed re-verified
- [x] Accounting, immutability, protected roots, auth false, G2 absent
- [x] No scope creep (this file only)

Reviewer did not edit code, did not execute decoder/phase, did not modify
the evidence root, did not read VOID contents or formal roots beyond
existence/names/sizes/mtime, did not touch G2/VAL/real/raw.
