# D6 Graph Mother Implementation Review R1c-A3 (independent, read-only)

Status: `IMPLEMENTATION_REVIEW_R1C_A3`
Branch: `formal-ir-v72p1-addendum-clean`
Scope: A3 prereg (`D6_GRAPH_MOTHER_PREREG_R1C_A3.md`) vs code vs tests vs
forensic reconstruction. No decoder execution, no evidence edits, no phase.
Reviewer edits only this file.
Reviewer: independent second pass (operator-separated; reviewer-go spawn tool
unavailable in this environment — independence via post-commit frozen-diff
re-read against prereg/forensics; no code edits during review except the
single returned rework below, re-verified after).
Date-UTC: 2026-09-09

## Verdict

Verdict: `D6_R1C_A3_IMPLEMENTATION_REVIEW_PASS` (after one rework round,
re-verified; rework budget consumed).

## What was reviewed

- `D6_GRAPH_MOTHER_PREREG_R1C_A3.md` (8 frozen rules + A3-00 split).
- `R1C_parallel_revision.md` A3 delta + `tasks.md` A3/A4 tasks.
- `D6_GRAPH_MOTHER_FORENSIC_R1C_A3.md` + `forensic_table.txt` (184 rows).
- Diff of `scripts/v72p2d6_graph_mother_development.py` (verifier path only:
  A3 constants, 5 pure helpers, check-3 key, check-14 rewrite, A3-08 INFO).
- `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py` (10 new
  `test_r1c_a3_*`).
- Test evidence: focused D6 42/42; seven-file non-perf 323/323; perf-v38
  skipped (no scoped dependency — mother module untouched; recorded choice).

## Rule-by-rule verification

1. Identity `(n,arm,seed,point,mode)`: check-3 keys include `n` ✓; forensic
   184/184 unique under new key vs 144 + 40 dup groups under old key ✓;
   tests `n_identity` (cross-width valid) + `true_duplicate_fails` ✓.
2. Canary-only recompute: `a3_stage_partitions` binds canary to `n==64` +
   canary seeds; per-cell `a3_cell_app` matches pipeline
   (`L1.exact and L2-APP.exact`, missing ⇒ False); `f12_iter` totals
   recomputed with `max(iter,0)` matching pipeline `iter_total` ✓; test
   `canary_isolation` (scaling rows present, canary still exact) ✓.
3. Scaling per-width: scaling seeds grouped by width; fallback dispatch
   equality vs `best_T`/`best_M`; per-width sig + advancing via frozen
   `select_advancement` with order rebuilt from structure CSV
   (`a3_ssum_from_structure`, same audit fields as `_structural_key`);
   stop-at-first-width (`first_sig_width`); confirmation-width expectation
   ✓; test `scaling_stages_ordered` ✓. Forensic scaling arms = fallbacks ✓.
4. Confirmation at selected width; empty ⇒ `INFO EMPTY_NOT_EVIDENCE`;
   counts + crashes/nonfinite/disagreements recomputed and compared; test
   `empty_confirmation_not_safety` proves both directions (empty passes with
   label; stored-nonempty-with-zero-rows fails) ✓.
5. Crash precedence over counted rows only; `call_idx=-1` excluded (flush
   never persists them; verifier counts `idx>=0`) ✓; test
   `placeholders_ignored` ✓.
6. Degree substring ⇒ `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED`; other
   crash/nonfinite ⇒ `D6_GRAPH_ATTEMPTED_CELL_INVALID`; clean ⇒ None
   (stored stands) ✓; test `crash_overrides_topology` (mechanical PASS +
   recomputed BLOCKED + agreement False) ✓.
7. Read-only: verify path performs only reads + stdout; no writer called;
   test `verify_readonly` proves byte-identity of all six files ✓.
8. Both terminals + agreement printed; `a3_compare_terminals` always returns
   recomputed as governing ✓; test `disagreement_fail_closed` ✓. A3-00
   split honored: 15 checks gate exit; agreement is INFO (prevents A3-05
   self-block; semantic gate stays at A3-06) ✓.

## Forensic cross-check

All 8 packet items present. Decisive points independently re-verified:
40 old-key dup groups all T1/M1 cross-width; partitions 104/40/40/0/0;
canary + advancing recompute match stored; scaling sig zero at both widths
(per-row exacts never coincide L1+APP — consistent with `advancing=[]`);
recomputed `STRUCTURE_INVARIANT_BLOCKED` vs stored topology, agree=False.
Source: M1 integer proof (rmax=3/zero_rows=0/sumsq=364 ⇒ ≥4 deg-1 rows,
code-independent) + structure-only rebuild (every dispatched T3/M1 slice
min-degree 1; all succeeding slices ≥2) + builder identity across
`15f1de79` (2-line fsync-only mother diff, verified) + arm-perfect
correlation with same-pool success elsewhere. `NOT_VERIFIABLE` not needed;
no guessing used. One correction: report says "T3 arithmetic inconclusive,
rebuild decisive" — accurate as written.

## Scope / prohibition check

- Touched production: verifier path of the one allowed script only; mother
  module, execution generation (`run_cell`/`invoke`/builders/pipeline),
  historical artifacts: untouched (diff-confirmed). Import-time effects of
  new helpers: none (pure defs + string constants).
- Zero decoder calls in tests (explicit fakes + `tmp_path`); no `--phase`,
  G1/G2, VAL/real, VOID, science-param change; evidence root unedited.
- CRLF note: git warns LF→CRLF on next touch of the script; pre-existing
  repo convention, no action (exact-path staging only).

## Rework (single round — returned, applied, re-verified)

- B-A3-1 (fail-closed completeness, blocking): scaling widths outside
  `{128,256}` (e.g. a scaling seed at n64) sat in `parts["scaling"]` but no
  loop branch inspected them — silent pass. Fix: `order_ok=False` when
  `set(parts["scaling"]) - {"128","256"}` nonempty. Re-verified: focused
  42/42 green after fix. Rework budget consumed; further findings would be
  STOP, none remain.

## Checklist

- [x] Matches frozen A3 prereg (8 rules + A3-00 split)
- [x] Tests prove each rule (10/10 mapped, 42/42 + 323/323 green)
- [x] Forensic reconstruction supports the classification
- [x] No scope creep (verifier-only; execution byte-identical by
  construction)
- [x] docs/decision-log.md + memory: deferred to A3-07 closeout (append-only)

Reviewer did not edit code, did not execute decoder/phase, did not touch
the evidence root, G2/VAL/real/raw, or any file outside this review.
