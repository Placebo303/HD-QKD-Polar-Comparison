# D5-G1-PRE-RESULT-REVIEW-R1 — independent review of the sole G1 attempt

## 0. Scope and verdict

Independently review the recorded output of the sole authorized frozen G1
attempt. This is a read-only scientific/lifecycle review, not execution and not
result acceptance.

Return exactly one verdict:

- `G1_PRE_RESULT_REVIEW_PASS` — the recorded outcome is internally coherent
  and ready for a separate main-thread result-acceptance decision; or
- `G1_PRE_RESULT_REVIEW_FAIL` — name every blocking inconsistency and stop.

A PASS does not turn the outcome into `G1_TREND_PASS`, authorize another G1
attempt, authorize G2, establish FER/leakage/key rate, qualify a method, or
promote anything.

## 1. Fixed evidence and expected lifecycle

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Pre-execution baseline: `6494b623`
- Authorization commit: `f4d577fb6b53cc58a23ada532331a5df3fac357f`
- Consumed-attempt return commit:
  `58c68961a1dedad58f52145e9f23942f2c476e4a`
- Accepted implementation:
  `cf61ee63f5b76b0223838717b1344e0e7c3867ee`
- Frozen packet:
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_EXECUTE_PACKET_R1.md`
- Pre-EXECUTE review:
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_EXECUTE_REVIEW_R1.md`
- Authorization record:
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_AUTHORIZATION_RECORD_R1.md`
- Operator return:
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_OPERATOR_RETURN_R1.md`
- Result root: `workspace/v72p2d5_g1/20260907_r2`
- Retained VOID root: `workspace/v72p2d5_g1/20260906_r1`
- G2 root must be absent.

Expected current lifecycle:

- all nine `*_execution_authorized` false;
- `scientific_promotion: false`;
- `next_gate: INDEPENDENT_G1_PRE_EXECUTE_REVIEW` unchanged;
- no G1 result-accepted/qualified/promoted field added;
- exactly two commits after `6494b623` with the scoped manifests above;
- new G1 root has exactly four files;
- G2 remains absent.

Any lifecycle or provenance mismatch is blocking.

## 2. Hard prohibitions

- No decoder invocation and no CLI `--phase` of any kind.
- No retry, rerun, resume, replacement root, or parameter change.
- No Model-F prepare/verify and no CAL/VAL/parquet/raw-row read.
- Do not open, hash, interpret, or cite any file inside retained VOID-G1.
- Do not modify/delete/move/rename/overwrite/normalize/hash any `workspace/`
  evidence.
- Do not edit `.py`, existing `.md`, OpenSpec, cycle state, decision log, or
  memory.
- No git add/commit/push/reset/stash/checkout/clean/rebase/revert/amend.
- Do not repair findings.
- Do not accept the result or change lifecycle state.

Only one durable new file is allowed:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_RESULT_REVIEW_R1.md`

No pytest basetemp is needed. This review reads the frozen scalar evidence and
current source; it does not rerun qualification or computation.

## 3. Pre-review snapshot

Before opening the new G1 files, record:

1. branch, HEAD, relevant commit manifests, and content-diff state;
2. lifecycle fields and all authorization values;
3. top-level name/size/mtime snapshots of P0, VOID-G1, new G1, G2, G0,
   G0-recovery, Model-F, and structure roots.

Do not read VOID-G1 contents. Its top-level stat snapshot is hygiene only.

## 4. Independent review matrix

### R01 — authorization and attempt lifecycle

Verify from commit diffs and records:

- the user's exact authorization is present;
- `f4d577fb` contains only unchanged Pre-EXECUTE review, authorization record,
  and the single false→true G1 authorization flip;
- `58c68961` contains only operator return and true→false restoration;
- no other authorization or lifecycle field changed;
- exactly one frozen command invocation is recorded;
- no retry/rerun/resume or G2/P0/other phase occurred;
- the key is false now and the attempt is consumed.

### R02 — immutable run identity

Cross-check packet, authorization record, operator return, current code, and
artifact metadata for:

- phase/root/width/f order/rows/mother reuse;
- graph and block seeds;
- 100 paired blocks per `f`, oracle first 20 diagnostic only;
- cold historical GF32, max_iter 90, damping 1.0;
- Model-F accepted input identity;
- L1→L2 sequence and exactly 440 calls;
- exact watchdog command and one invocation;
- exactly four no-overwrite files.

Any evidence that parameters changed or the wrong root was used is blocking.

### R03 — artifact structure and cross-file coherence

Open only the four files in `20260907_r2`. Verify:

- exactly `results.json`, `table.csv`, `report.md`, and
  `execution_summary.json`, with no subdirectory;
- JSON is finite and schema fields are present;
- CSV has exactly the expected two `f` rows and matching scalar values;
- report and execution summary faithfully state the same outcome, pass flag,
  counts, wall/resource status, and nonclaims;
- no raw symbols, priors, beliefs, decoder traces, per-block samples, CAL/VAL
  rows, or secret material is persisted;
- files refer only to the new valid root and do not cite VOID-G1 evidence.

List every scalar used in the review. Do not silently coerce missing or invalid
values.

### R04 — count and iteration arithmetic

Independently recompute from persisted scalars:

- attempted = 100 for each `f`;
- APP calls = 100 × 2 levels × 2 `f` = 400;
- oracle calls = 20 × 1 level × 2 `f` = 40;
- total calls = 440;
- `app_failure_fraction = 1 - app_exact_count / attempted`;
- exact/syndrome/nonfinite counts are within denominators;
- `app_iterations_max <= 180`;
- APP iteration totals are within `attempted × 180`;
- oracle iteration totals are within `20 × 90`;
- run peak RSS equals the max per-f peak when all samples are known.

Expected literal candidate values are evidence to verify, not assumptions:

- both `f`: attempted 100, APP exact 0, rate 0.0, failure 1.0,
  APP syndrome 0, APP iteration total 18000/max 180, oracle exact 0,
  oracle syndrome 0, oracle iterations 1800, nonfinite 0;
- decoder calls 440; run peak RSS 115142656.

### R05 — exact, syndrome, and oracle isolation

This is a mandatory scientific-semantic gate:

- APP exact count alone determines APP exact rate/failure fraction;
- syndrome satisfaction is recorded separately and is never merged into exact
  success or used to reduce failure fraction;
- oracle records are diagnostic only and never enter APP trend/pass;
- nonfinite/crash records cannot be counted as exact;
- zero exact and zero syndrome must remain literal zero, not be relabeled as
  FER, undetected success, decoder correctness, or data-quality evidence.

Inspect the current aggregation/classification source as needed. Any conflation
of exact, syndrome, oracle, crash, or nonfinite semantics is blocking.

### R06 — signal and terminal outcome

Recompute the frozen signal exactly:

```text
zero nonfinite
AND APP rates nondecreasing
AND top APP exact count > 0
AND (top exact count > low exact count OR both counts == attempted)
```

For the literal `0,0` APP exact counts, monotonicity alone is insufficient:
`top > 0` is false. Require signal false,
`outcome=G1_COMPLETED_NO_SIGNAL_FAIL`, and `passed=false`.

Verify the seven-outcome precedence from the frozen packet and confirm no
50%/90% threshold or post-hoc reinterpretation was introduced.

### R07 — time and resource gates

Verify independently:

- stored entrypoint wall = `238.86517630005255 s` and is finite/`<=900`;
- operator outer wall = `239.110 s` and is finite/`<=900`;
- exit 0 and not watchdog 124;
- outer wall exceeds stored wall by a plausible nonnegative wrapper overhead;
- run peak RSS = 115142656, known, positive, equal to max per-f peak, and
  `<2147483648`;
- neither wall nor RSS overrides the no-signal outcome;
- resource success does not convert no-signal into trend pass.

If operator wall were over 900, it would override stored pass in review. It is
not; verify rather than assume.

### R08 — frozen-output/no-overwrite and protected roots

Compare pre/post top-level name/size/mtime snapshots. Require:

- new G1 root unchanged throughout this review;
- VOID-G1 unchanged and unopened;
- all other protected roots unchanged;
- G2 absent throughout;
- no second valid G1 root and no partial/retry root;
- no tracked/staged content change introduced by the reviewer.

### R09 — claim boundary

The strongest permissible conclusion is:

> The sole authorized frozen synthetic G1 attempt completed within the frozen
> wall and RSS gates, produced an internally coherent four-file scalar record,
> and correctly classified zero APP exact successes at both f values as
> `G1_COMPLETED_NO_SIGNAL_FAIL` with `passed=false`.

Explicitly reject claims of real-data FER, decoder correctness, leakage,
efficiency, key rate, qualification, promotion, method success, G2 readiness,
or permission for another attempt.

## 5. Review method

Use small read-only stdlib scripts for JSON/CSV parsing and arithmetic. Read
current source and exact commit diffs. Do not run pytest, compile, a probe, or
the phase: they cannot change the recorded result and would expand the review
without resolving a result-semantic question.

Record raw outputs sufficient to reproduce every arithmetic check. If a value
is absent or contradictory, mark FAIL; do not repair or infer it.

## 6. Final snapshot and report

Repeat all lifecycle and protected-root snapshots after review. Require exact
equality and G2 absence.

Create only `G1_PRE_RESULT_REVIEW_R1.md` with:

1. role, evidence baseline, and non-acceptance statement;
2. R01–R09 PASS/FAIL table with concrete evidence;
3. complete literal scalar table for run and both `f` values;
4. independent count/iteration/failure/RSS/wall arithmetic;
5. exact/syndrome/oracle/nonfinite isolation findings;
6. signal recomputation and seven-outcome consistency;
7. four-file cross-coherence and prohibited-payload scan;
8. pre/post protected-root and lifecycle equality;
9. commands run and explicitly not run;
10. blocking and non-blocking findings;
11. explicit strongest permissible claim and all nonclaims;
12. final verdict token.

Do not commit or push the report and do not update lifecycle state.

## 7. Stop conditions

Immediately STOP with the failing ID and raw evidence, without repair, if:

- provenance/lifecycle differs from §1;
- any file is missing, extra, malformed, nonfinite, or mutually inconsistent;
- exact/syndrome/oracle/nonfinite semantics are conflated;
- arithmetic, signal, outcome, passed flag, wall, RSS, or call count disagrees;
- protected evidence changes or G2 appears;
- review would require a decoder rerun or source edit to reach a verdict.

## 8. Return format

Report:

1. verdict;
2. R01–R09 status;
3. literal run/per-f scalar table;
4. arithmetic and signal/outcome recomputation;
5. exact/syndrome/oracle isolation result;
6. four-file coherence and prohibited-payload result;
7. pre/post root/lifecycle equality;
8. blocking/non-blocking findings;
9. true/false prohibited-action checklist;
10. sole created review file and no commit/push confirmation.

End exactly:

`G1 结果仅按“完成但无信号失败”候选接受性完成复审；本复审不是结果接受，不授权重跑或 G2。`

