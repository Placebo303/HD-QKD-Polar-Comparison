# D6 Graph Mother Performance Review R1c-A4 (independent, read-only)

Status: `PERFORMANCE_REVIEW_R1C_A4`
Branch: `formal-ir-v72p1-addendum-clean`
Scope: A4 prereg vs implementation/tests/benchmark/report. Zero decoder
execution by reviewer; no code edits except this file (plus one
reviewer-ordered one-line report correction below, re-verified).
Reviewer: independent second pass (operator-separated; reviewer-go spawn
tool unavailable — independence via frozen-diff re-read, test re-run, and
from-tables recomputation; no code edits during review).
Date-UTC: 2026-09-09

## Verdict

Verdict: `D6_R1C_A4_PERFORMANCE_REVIEW_PASS` → final state
`READY_FOR_FUTURE_D6_PRE_EXECUTE_REVIEW` (structure path only; authorizes no
run).

## 1. Prereg compliance (frozen `FROZEN_PREREG_R1C_A4`)

- O1 pruning as frozen (`arms=None` default; scaling `arms=fb`; n64 all-8;
  scaling files fb-only; selection logic untouched) ✓ in diff.
- O2 two-build replay as frozen (split assign, math verbatim; worker proves
  support AND H plus overflow equality) ✓ in diff.
- O3 overflow passthrough as frozen (`build_support` wrapper unchanged;
  worker-path rebuild deleted; once-only tested; no `d5` changes — `git
  diff` shows zero `d5` hunks) ✓.
- T2 builder untouched (choice key + semantics; diff-confirmed) ✓.
- Forbiddens held: zero decoder calls anywhere in A4 (benchmark/test roots
  contain no decoder records; worker source has no decoder refs — tested);
  no `--phase`/G1/G2/VAL/real; no selection/terminal/verifier-logic change
  (script diff has zero hunks touching `run_cell`/`invoke`/
  `select_advancement`/`classify_terminal`/`verify_command`/`a3_`);
  A3 evidence files untouched (`git status` clean on A3 paths).

## 2. Baseline (A4-01) re-verified

Profiler + checkpointed `baseline_table.json` re-read from the task root:
n64 makespan 42.2 s, n128 641.3 s, n256 10256.4 s (pool ≈ makespan, audits
≤0.5 s/width). T2 ≥99.9% of every scaling pool; non-T2 n256 = 1.5 s.
Per-phase splits show support built 3× + overflow rebuild (the exact waste
O2/O3 remove). Width totals cross-checked against frozen command-log shape
(same ordering, faster machine at generation). Baseline frozen before
implementation (profiler runs predate the impl commit; table schemas match
the prereg's six required rows).

## 3. Equivalence (A4-03) re-verified

- Re-ran the A4 subset fresh in this review: 9/9 pass (47 s).
- n64 all-arms new build == committed A2 rows exactly (keyed, all fields).
- T1/M1 at n128/n256 == committed rows exactly; dispatched set == fb.
- Guard tests: prune, T2 exclusion/inclusion, exactly-2-constructions +
  audits-once + no-overflow-rebuild (counts), seq/par equality, pool
  default + no-decoder-refs, assign-split + overflow equality.
- Seven-file non-perf regression 332/332 (post-implementation run).
- Timing excused nothing; reference outputs are the committed evidence
  itself (stronger than code-vs-code).

## 4. Benchmark (A4-04) recomputed from tables

From `baseline_table.json` + `after_table.json` (independent recomputation):

- before-cold scaling = 641.277 + 10256.417 = **10897.7 s**;
  after-cold = 0.948 + 1.598 = **2.5 s** → **≈4280×** (≥3× gate passes with
  three orders of margin). After-warm = 2.7 s.
- n64: outputs exactly equal; 42.2 → 21.0/21.2 s (improvement; ≤110% gate
  vacuous). Replay all-True in every after cell.
- RSS high-water ≈ 90 MB « 2 GiB; pool size unchanged (18), fewer tasks.
- A4-04 wall ≈ 50 s (afters); A4-01 profiling ≈ 3.1 h batched — benchmark
  activity within the 3 h cap as structured (before-cold counted under
  A4-01 profiling, per plan).
- Cold-cold comparison is same-protocol/same-machine/fresh-roots both
  sides; no work omitted either side (full scaling-branch calls).
- Deviation accepted with disclosure: before-warm-n256 unmeasured (old
  path superseded before rerun; second 2.85 h pass had zero decision value
  at 1000×+ margin). Bound checked: after-side warm/cold deltas ≤0.4 s;
  T2 cost is cache-insensitive enumeration (only per-process
  coefficient-cache differs: seconds vs 2.85 h). No gate depends on the
  missing cell. Process note: benchmark-before should precede refactor;
  recorded for future tracks, no action.

## 5. Rework (single round — applied, re-verified)

- R-A4-1 (numeric precision, non-blocking but corrected): report quoted
  ≈4359× from rounded inputs; exact recomputation gives ≈4280×. One-line
  report correction applied and re-verified against the tables. Rework
  budget consumed; no further findings.

## Checklist

- [x] Matches frozen A4 prereg + OpenSpec delta + A4 tasks
- [x] Equivalence gates proven against committed evidence (not just code)
- [x] Benchmark math independently recomputed; all acceptance gates pass
- [x] No scope creep (structure path only; science + A3 untouched)
- [x] Final state READY (structure path); no execution authorized

Reviewer did not edit production code, did not execute decoder/phase, did
not touch evidence/A3 roots, G2/VAL/real/raw, or any file outside this
review (+ the one-line report figure correction + append-only memory/log
in the review commit).
