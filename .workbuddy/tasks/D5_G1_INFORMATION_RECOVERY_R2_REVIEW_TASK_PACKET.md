# D5-G1-INFORMATION-RECOVERY-R2-REVIEW — independent scientific/code review

## 0. Role and verdict

Independently review the R2 attribution and additive backoff-prior candidate.
Do not accept implementer conclusions, formulas, test counts, or causal labels
without reading source/evidence and recomputing the decisive claims.

Return exactly one verdict:

- `G1_INFORMATION_RECOVERY_R2_REVIEW_PASS` — attribution and candidate are
  review-valid and may proceed to a separately planned candidate Model-F
  preparation/qualification chain; or
- `G1_INFORMATION_RECOVERY_R2_REVIEW_FAIL` — blocking findings and smallest
  required repair.

PASS is not production wiring, Model-F replacement, formal G1 authorization,
G1 rerun permission, G2 permission, result acceptance, or promotion.

## 1. Candidate baseline

- Repo `D:/Code/HD-QKD_Polar_Comparison`
- Branch `formal-ir-v72p1-addendum-clean`
- Expected HEAD `1d4fa9124afd57ec5ce03a786a4cdc2b2f55cc1d`
- R2 OpenSpec `88053563`
- Candidate implementation/tests `a93106f5`
- Attribution/evidence/gate `21576add`
- Lifecycle guard closeout `1d4fa912`
- Predecessor accepted negative result remains at
  `workspace/v72p2d5_g1/20260907_r2`
- R2 development evidence root
  `workspace/d5_g1_wide_attribution_r2_5c38a20ae60b41ceb0b6a0d7757aa2aa`
- Current gate `INDEPENDENT_G1_INFORMATION_RECOVERY_R2_REVIEW`

## 2. Hard prohibitions

- No CLI `--phase`, formal G1 rerun/resume, G2, n=1024, or real-data IR.
- No VAL read/use. CAL-TRAIN may be read only for independent recomputation of
  already claimed R2 quantities.
- No write/hash/delete/move/rename/overwrite under any formal evidence root.
- Do not open retained VOID-G1 contents.
- Do not edit production/tests/OpenSpec/existing docs/state/log/memory.
- No repair; findings only.
- No authorization or lifecycle change.
- No git write/push/reset/stash/checkout/clean/rebase/revert/amend/normalization.
- No new dependency or broad unrelated test suite.

Only one durable new file is allowed:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_INFORMATION_RECOVERY_R2_REVIEW_R1.md`

Temporary review scripts/results may use one unique nonformal
`workspace/d5_g1_r2_review_<uuid>/` and must be removed after validated-path
cleanup. Never use a formal root.

## 3. Provenance and scope review

### C01 — commit manifests

Verify all four commits and exact path manifests. Require:

- OpenSpec precedes code;
- implementation changes only the D5 core and its test;
- candidate is additive: existing `build_f_model`,
  `prepare_model_f_prior`, phase wiring, constants, seeds, thresholds,
  authorizations, roots, and accepted artifacts are unchanged;
- evidence commit contains only allowed R2 docs/state append/evidence paths;
- guard closeout changes only the test and existing OpenSpec tasks;
- current content matches committed candidate with no scoped residual diff.

The unchecked T5 delivery box in `tasks.md`, if still present while commits and
no-push evidence are independently verified, is a clerical non-blocking finding
to correct during later acceptance. Any substantive unchecked requirement is
blocking.

### C02 — lifecycle and protected evidence

Verify all authorizations false, promotion false, current gate exact, G2
absent, accepted G1 result unchanged, and protected-root top-level
name/size/mtime snapshots stable before/after review. Do not read VOID content.

## 4. Mathematical contract review

### C03 — recover the D4 lambda meaning

Read the actual D4R2 implementation/evidence that selected
`lambda*=137.3823795883264`. Establish from code—not prose—whether lambda is:

- total concentration per Bob column;
- a per-cell pseudocount;
- or another quantity.

Write the exact D4 formula, axes, fold population, objective, and units. Confirm
whether `p_global` is the appropriate Alice marginal from the corresponding
training population. A provenance ambiguity that changes the formula is
blocking.

### C04 — old consumer defect arithmetic

Independently recompute on accepted counts:

- cell count, total observations, per-column count scale;
- pseudo-mass added by `counts + lambda` per cell;
- prior fraction and dominance ratio;
- old consumer column normalization;
- old channel CE/MI and truth-prior mass.

Verify that the defect is application of the selected scalar, not merely a
preference between two smoothers. Check the claim that the same counts and same
functional isolate the smoothing axis.

### C05 — candidate formula and limits

Audit `build_f_model_concentration` line by line:

```text
n_b[b] = sum_a counts[a,b]
p_global[a] = sum_b counts[a,b] / total
P(a|b) = (counts[a,b] + lambda*p_global[a]) / (n_b[b]+lambda)
```

Require finite nonnegative 2-D counts, positive finite lambda, nonzero total,
column normalization, and correct zero-column fallback. Check dtype behavior,
shape, axes, broadcast, and numerical tolerance. Independently compare the
candidate cell-for-cell with D4's actual builder on multiple deterministic
tables including a zero column and full 1024×1024 accepted counts.

Audit `prepare_model_f_prior_candidate`: injected-only behavior, P(B)/P_F
shape and normalization, no file/formal-root/decoder access, and no accidental
production call site.

### C06 — D4-vs-consumer discrepancy

Rebuild the discrepancy table with like-for-like labels. Verify separately:

- D4 held-out CE `3.814742 + 3.347605 = 7.162347`;
- old full-count consumer CE approximately `5+5=10`;
- candidate same-full-count in-sample CE approximately `4.2867+3.2227=7.5094`;
- why 7.5094 need not equal held-out 7.162347;
- accepted-vs-candidate MI and truth mass.

Do not treat held-out and in-sample quantities as identical. Any wrong axis,
population, functional, or sum is blocking.

## 5. Causal evidence review

### C07 — CAL/VAL boundary and estimator selection

Inspect command log and scripts. Require all row reads to be canonical
CAL-TRAIN frames 702..1725 and zero VAL use. Verify lambda/grid/folds reproduce
the frozen D4 selection rather than post-hoc tuning on decoder outcomes.

### C08 — square/frontier evidence

Audit R1+R2 scripts and scalar JSONs for paired seeds, one-axis changes, call
accounting, rank, exact, syndrome, iterations, wall, and RSS. Independently run
a fresh minimal confirmation in the review temp root:

1. old accepted prior + square oracle-L2 on one frozen seed;
2. candidate prior + same square/seed;
3. candidate prior + frozen H2 prefix on the same seed.

Maximum 3 decoder calls. Inject decoder/prior/matrix/output explicitly; no CLI,
formal root, or production phase wiring. Use 120 s watchdog per call. This is
development confirmation only. Require the first two to reproduce the claimed
old-vs-candidate discrimination; treat the third as diagnostic, not a pass
threshold.

If nondeterministic or inconsistent with persisted evidence, FAIL.

### C09 — causal classification

Determine whether evidence supports
`LAMBDA_APPLICATION_CONTRACT_DEFECT` as the earliest primary cause while
carrying disclosure/mother insufficiency as secondary. Explicitly test these
alternatives:

- axis/consumer mismatch other than smoothing;
- genuine CAL near-independence;
- decoder/GF32/matrix failure at full determination;
- APP propagation as sole cause;
- iteration cap as sole cause;
- disclosure shortage as sole upstream cause.

Do not claim the candidate solves L1 or produces a useful operating point. L1
failure through square disclosure and L2 recovery only near 52–64 rows remain
binding limitations.

## 6. Code and test review

### C10 — tests are meaningful

Inspect all eight R2 tests. Require exact-formula comparison, defect pin,
frozen old behavior pin, invalid limits, zero-column fallback, chain split,
frozen lambda basis, and isolation. Tests must fail for the relevant wrong
implementations, not merely restate production output.

Review the guard closeout: legitimate G1 root is snapshot-compared, all prior
assertions survive, and T1_23 catches snapshot-is-None without becoming a broad
fragile framework.

### C11 — fresh execution

Run:

1. py_compile on the changed core and D5 scripts;
2. focused R2 + lifecycle guard tests;
3. exact three-file D5 suite with unique `workspace/` basetemp and
   `-p no:cacheprovider`.

Require zero failures. The known `cache_dir` warning is benign. Record literal
commands and summaries. Remove only validated review-owned temp paths.

### C12 — candidate scope and next-step fitness

Confirm this is intentionally an injected, nonformal candidate—not yet a
replacement artifact builder or phase consumer. State exactly what remains
before any new formal G1 run:

- candidate acceptance;
- candidate Model-F preparation packet and independent review;
- additive new artifact root, no overwrite;
- CAL-only preparation and Pre-RESULT acceptance;
- L1 discriminator/operating-point decision;
- only then a newly frozen formal experiment and separate authorization.

## 7. Verdict rules

Blocking FAIL includes: wrong lambda provenance; formula/axis/population error;
VAL leakage; old production path silently rewired; formal artifact modified;
causal claim not reproduced; square discrimination fails; missing isolation;
test failure; or overclaim that R2 already fixes G1.

PASS may carry clerical T5 cleanup and disclosed L1/disclosure limitations.

## 8. Report and return

Create only `G1_INFORMATION_RECOVERY_R2_REVIEW_R1.md` with C01–C12 table,
formula/provenance derivation, independent discrepancy numbers, three-call
confirmation, causal alternatives, code/test findings, root/lifecycle
equality, blocking/non-blocking findings, exact next prerequisites, commands,
and final verdict.

Do not commit or push.

Return: verdict; C01–C12 counts; decisive lambda evidence; independent numeric
table; three-call results; focused/full pytest lines; findings; protected-root
equality; prohibited-action checklist; sole report path.

End exactly:

`R2 信息恢复候选评审完成；正式 G1 负结果未改写、未重跑，G2 未授权。`

