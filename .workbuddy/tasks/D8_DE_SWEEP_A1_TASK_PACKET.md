# D8 rate-aligned GF32 ensemble DE sweep — authorization A1

## 1. Authorization

- Repository: `D:\Code\HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`; do not switch.
- Track: `EXPLORE_HEAVY`.
- Required accepted readiness marker:
  `D8_RATE_ALIGNED_ENSEMBLE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
- Sending the paired prompt verbatim from the user authorizes exactly one
  execution of the frozen D8 DE sweep below.

No production/finite-length decoder, D7-H, CAL/VAL/raw/real-data run, n1024,
candidate-grid change, retry/resume, commit or push is authorized.

## 2. Frozen contract

Read completely before acting:

- `.workbuddy/tasks/D8_RATE_ALIGNED_ENSEMBLE_FEASIBILITY_R1_TASK_PACKET.md`;
- `openspec/changes/v72p2d8-rate-aligned-gf32-ensemble-feasibility/**`;
- `docs/research_cycles/V72P2D8-RATE-ALIGNED-ENSEMBLE/READINESS_R1.md`;
- `docs/research_cycles/V72P2D8-RATE-ALIGNED-ENSEMBLE/EXPLORATION_LOG.md`;
- `docs/research_cycles/V72P2D8-RATE-ALIGNED-ENSEMBLE/INDEPENDENT_REVIEW_R1.md`.

Scientific matrix:

- V26 MC-DE kernel unchanged, q=32/poly 37, full 32-ary Model-F L1 channel;
- lambda support `{2,3}`, lambda2 `0.00..1.00` step `0.05`, exactly 21
  deterministic candidates including regular-DV3;
- f1.2/R=5/64 primary and f1.0/R=15/64 secondary;
- seeds `2026091601`, `2026091602`, `2026091603`;
- `n_samples=4000`, `max_iter=60`, entropy tolerance `1e-4`, streak 20;
- exactly 21×2×3 = 126 maximum scientific DE calls;
- advancement and deterministic ranking exactly as frozen in OpenSpec/readiness.

No observed outcome may alter the candidate set, seed set, ordering, stopping
rule or threshold.

## 3. Pre-dispatch

Append raw results to the single `EXPLORATION_LOG.md` and STOP on mismatch:

1. accepted readiness marker present and future sweep still unexecuted;
2. all execution/promotion authorization flags false;
3. exact future root absent;
4. Model-F root is the accepted CAL-only
   `workspace/v72p2d5_model_f_input/20260907_r1` and unchanged;
5. implemented plan is exactly 21 candidates ×2 conditions ×3 seeds;
6. F1 is resolved and F2–F4 are explicitly carried;
7. run only `py_compile` for adapter/runner and the 15 focused D8 tests in a
   fresh task-owned basetemp. Trust the existing independent math/test review;
   do not rerun unrelated suites or the 56-check audit.

Mismatch terminal: `D8_DE_BLOCKED_PRE_DISPATCH`; no repair or substitute run.

## 4. Exact command and limits

From repository root, execute exactly once:

```text
.venv/bin/python scripts/v72p2d8_rate_aligned_ensemble_development.py --de-sweep --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405
```

Limits: ≤126 DE calls, implemented setup count 0 and frozen ceiling ≤20,
wall ≤1800 s, post-call wall ≤120 s per call, RSS <2 GiB strict, one process,
no retry/resume/seed search/overwrite.

The 120 s rule is not an interrupting watchdog: it is checked between/after
calls. If a call returns over 120 s, retain the root and stop before another
call with the registered resource terminal. Do not claim that an in-flight call
was forcibly terminated.

DE coefficient semantics are the V26 random nonzero-coefficient ensemble.
Finite-length coefficient-stream seeds are not used or tested by this sweep.

## 5. Failure and partial-root handling

- A completed scientific `NO_ADVANCE` or baseline-nonconvergence result is a
  valid EXPLORE outcome, not an engineering failure.
- On crash, nonfinite, resource breach or incomplete evidence, retain the
  partial root and stop. Normal `--verify` is expected to fail closed on a
  partial root; record its raw output, then have the independent reviewer
  inspect the present files without repairing, deleting or rerunning.
- No implementation repair or second scientific invocation is authorized by
  A1. A repair requires a new main-thread addendum.

## 6. Batch-end review

After completion or early stop, dispatch one independent reviewer-go subagent
with actual-root access. It must:

- execute the read-only `--verify` command and preserve raw output;
- independently recount candidates, conditions, seeds, calls and traces;
- recompute each candidate summary, convergence state, DV3 comparison,
  advancement predicate, rank key and stored terminal;
- verify channel/rate markers, no adaptive search, budgets, RSS and no retry;
- distinguish post-call timing enforcement from a watchdog;
- distinguish DE coefficient-ensemble semantics from finite-length streams;
- inspect partial evidence directly if normal verification fails closed;
- report `EVIDENCE_ACCESS`, verdict, findings and exact claim ceiling.

Trust a `VERIFIED` review within scope; do not duplicate its computations for
ceremony. Any blocking finding prevents mainline advancement.

## 7. Return boundary

Append execution and review to the existing single exploration log. Advance
only to:

- `D8_DE_SWEEP_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`, or
- an exact `D8_DE_SWEEP_BLOCKED_*` state.

Do not self-accept a winner, authorize finite-length construction/decoding,
revive D7-H, update long-term memory, commit or push.

Return exactly `COMPLETE` or `BLOCKED`, reporting pre-dispatch checks, exact
command/exit, calls/resources/root inventory, terminal, DV3 baseline, advancing
candidates and deterministic winner if any, independent verdict/findings,
authorization flags false, changed files and no-commit/no-push state.
