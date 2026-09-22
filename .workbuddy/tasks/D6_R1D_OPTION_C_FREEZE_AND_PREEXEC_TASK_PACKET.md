# D6 R1d — Option C ruling, eligible-only implementation and Pre-EXECUTE freeze

## 0. Main-thread ruling

The main thread selects **Option C** from
`D6_GRAPH_MOTHER_REPAIR_STUDY_R1C_A5.md`:

- no SC or M knob lift;
- SC and accumulator families are structurally inadmissible as frozen;
- R1d candidate set is exactly
  `{B0_D5_DV3_NATIVE, B1_D5_DV3_COMMON_LABELS, T1_PEG_DV3}`;
- T2 remains excluded and recorded only as a rank-bound result;
- no R1c-A2 decoder call or root may be reused as successor evidence.

The main thread also approves evidence schema revision for new R1d roots:

- add `row_degree_min`;
- add `rows_below_degree_2`;
- add an explicit eligible-semantics/schema version marker;
- historical A2 files remain immutable and retain their old schema.

This ruling authorizes planning, OpenSpec, implementation, tests, independent
code review, and independent Pre-EXECUTE review. It does **not** authorize R1d
decoder execution.

## 1. Baseline

- Repository: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Expected HEAD: `85a5551d`
- Current gate:
  `D6_GRAPH_MOTHER_R1C_A5A6_COMPLETE_AWAITING_MAIN_THREAD_RULING`
- A3 historical result: immutable, recomputed
  `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED`; never reused
- A5 validity and repair reviews: PASS eligible-only branch
- A6 performance review: PASS
- All authorization keys false; G2 absent; no R1d root exists

Known unrelated dirty paths, V35/perf-v38 work, and CRLF churn remain untouched.

## 2. Objective

Turn Option C into the smallest execution-ready R1d candidate and freeze one
complete Pre-EXECUTE packet. Preserve the accepted A5/A6 implementation and
avoid reopening SC/M/T2 research.

R1d asks only:

> Under the unchanged E2 prior, decoder, rows, seeds, schedule, and thresholds,
> does the structurally valid T1 PEG mother improve over B0/B1 controls without
> invariant failures?

It does not ask whether SC, accumulator, or T2 can be repaired.

## 3. Frozen scientific contract

- Arms exactly B0, B1, T1; no dynamic additions.
- n64 blind structure validity precedes decoder dispatch.
- Existing canary seeds `2026091000..03`, confirmation seeds
  `2026091010..25`, and scaling seeds `2026091100..03` remain unchanged.
- Existing rows, E2 prior, coefficient stream, cold historical GF32 decoder,
  max_iter=90, damping=1.0, L1→APP-L2, oracle diagnostic-only, exact/syndrome
  separation, and no-retry remain unchanged.
- Dispatch is allowed only where the accepted A5 validity matrix says both
  frozen eligibility and I1 pass. Any proposed cell outside that subset is a
  pre-dispatch hard failure, not a skipped scientific observation.
- B0/B1 are controls and cannot win advancement. T1 is the sole new arm.
- Scaling fallback, if reached, is T1 only. There is no M fallback.
- Existing registered thresholds and stop-at-first-signal width remain. Do not
  add power, success-rate, or tuning thresholds.
- Budgets remain <=2500 total setup+scientific calls, <=12h, <=120s/call,
  aggregate RSS <2GiB, no retry.
- Requested workers 18 with reviewed RSS-only downgrade 18→14→12→8.
- Output is one fresh `workspace/d6_graph_mother_r1d_<uuid>/` root, refuses
  overwrite, scalar-only.

Before implementation, explicitly enumerate the resulting R1d cell schedule
and prove every cell is in the A5 valid subset. If the unchanged scientific
schedule demands an invalid cell, STOP with the exact conflict; do not silently
drop or replace it.

## 4. OpenSpec and durable ruling

Create a new R1d OpenSpec change or a clearly isolated R1d delta in the existing
D6 change. It must record Option C, rejected A/B reasons, exact candidate set,
validity-subset dispatch, schema version, terminal priority, fresh-root/no-reuse
rule, execution schedule, budgets, tests, and lifecycle gates.

Create:

- `D6_GRAPH_MOTHER_OPTION_C_ACCEPTANCE_R1.md`
- `D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_R1.md`

Append the ruling to decision log and project memory. Commit this planning
layer separately before implementation. No authorization field changes.

## 5. Minimal implementation

Implement only what R1d needs:

- explicit eligible-only arm inventory B0/B1/T1;
- validity-matrix/I1 fail-closed dispatch guard;
- T1-only scaling fallback;
- schema-v2 fields and version marker for new roots;
- crash/nonfinite/invariant precedence from A3/A5;
- stored and independently recomputed terminal agreement;
- A4/A6 optimized structure path without output changes;
- a distinct R1d runner mode or entrypoint that cannot overwrite or treat A2
  roots as inputs.

Do not leave dead SC/M/T2 execution branches reachable from R1d config. Reuse
shared helpers where simple; do not create a generalized framework.

## 6. Tests and evidence

Add focused tests proving:

- arm set is exactly B0/B1/T1;
- SC/M/T2 cannot dispatch under R1d;
- T1-only fallback and B0/B1 control semantics;
- every frozen schedule cell is validity+I1 eligible;
- one invalid cell fails before decoder binding;
- schema-v2 fields are present and recomputable;
- old A2 schema remains readable and immutable;
- attempted crash/nonfinite overrides scientific labels;
- no A2/VOID/formal root reuse;
- sequential/parallel deterministic equality;
- fake end-to-end runner produces and verifies the exact new schema with zero
  production decoder calls.

Run py_compile, focused D6 tests, and the established seven-file non-perf suite
with fresh task-owned basetemps. Perf-v38 is unnecessary unless its scoped
dependency changed.

## 7. Independent reviews

Obtain a read-only implementation review. Blocking findings may receive one
scoped rework cycle. Then obtain a fresh independent Pre-EXECUTE review that
checks:

- branch, scoped diff, Option C decision and exact candidate set;
- complete schedule against the validity matrix;
- code/tests and A4/A6 performance path;
- fresh R1d target absence and old-root no-reuse;
- all authorization keys false and G2 absent;
- exact future command, workers, budgets, watchdog and stop rules;
- protected-root metadata and dirty-tree scope;
- claim ceiling and mandatory Pre-RESULT review.

Allowed final readiness verdict:

`D6_R1D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`

The review cannot grant authorization.

## 8. Commits and stop point

Use separate scoped local commits for:

1. Option C/OpenSpec/execution-packet freeze;
2. implementation and tests;
3. independent implementation review and Pre-EXECUTE review;
4. append-only closeout if needed.

No push. Do not create an R1d output root. Do not run a real decoder or any
`--phase`. Finish with all authorization keys false and a gate that clearly
awaits explicit R1d authorization.

## 9. Return

Report deltas only: ruling files, exact schedule/validity proof, implementation
files, schema-v2 fields, tests, reviews, commit SHAs, target-root absence,
protected-root equality, authorization state, G2 absence and no push.

End exactly:

`Option C 已落地：D6 R1d 仅保留 B0/B1/T1 并完成独立 Pre-EXECUTE；R1d 尚未授权、未执行，历史 A2 根未复用，G2 未授权、未执行。`
