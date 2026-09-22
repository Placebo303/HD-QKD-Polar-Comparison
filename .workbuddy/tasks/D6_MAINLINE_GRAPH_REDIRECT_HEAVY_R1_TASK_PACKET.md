# D6 Mainline Graph Redirect — Heavy R1

## 1. Hard prerequisite

This packet belongs in a separate session and must not begin until the main thread has accepted the result of:

`WORKFLOW_TWO_TIER_RESEARCH_SIMPLIFICATION_R1_TASK_PACKET.md`

Required durable marker: the accepted repository-wide workflow cycle/OpenSpec must state `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE` (or its explicitly documented compatibility alias `TWO_TIER_WORKFLOW_ACCEPTED`). If absent, return:

`BLOCKED_WORKFLOW_OPTIMIZATION_NOT_ACCEPTED`

Do not reinterpret this packet under the old per-arm ceremony. The prerequisite is a project-wide default for all future work; D6 is only its first consumer.

## 2. Route decision inherited from X1–X4

Accepted evidence:

- X1: the historical decoder produces `CHECK_UPDATED` beliefs on a satisfiable nontrivial probe; the provenance path is operational.
- X2: across three graph pairs at n=64/f=1.2, forward joint exact was 2/16, 2/16 and 1/16; reverse joint was 0/16 for all; graph-to-graph variation did not produce a qualitative recovery transition.
- X3: among 156 failed records, row-layered 360 rescued 1 and flooding 90 rescued 0; longer iteration/simple schedule replacement is not the main missing mechanism.
- X4: frozen n=256 G2 completed 1320/1320 calls within budget; for f=1.0/1.1/1.2, all 200 blocks per f had L1 exact=0, L2 exact=0, L1 syndrome-valid=0 and L2 syndrome-valid=0, with provenance and transfer invoked 200/200; grade `G2_CURRENT_CONFIGURATION_FAILED`.

### Why this packet does not continue D7-H

D7-H changes cross-layer alternation while retaining the code family and operating configuration whose base layers failed G2 at 0/600 syndrome-valid. X3 already showed that more iterations and the existing alternative schedule do not materially repair that base failure. X2 showed target-layer transfer information can move decisions, but joint recovery remains rare because the source/base layer is not decoded. Another alternation can produce an interesting n=64 mechanism signal without answering whether the underlying finite code is usable.

Therefore:

- current D7-H is `NOT_AUTHORIZED / NOT_RECOMMENDED`;
- the D5 current rate-mother configuration is closed as `G2_CURRENT_CONFIGURATION_FAILED`;
- the next orthogonal scientific variable is graph/code construction at the same Model-F, rows and decoder contract;
- D7-H may return only as a separately proposed new decoder architecture after a base graph/code candidate demonstrates nonzero, reproducible marginal syndrome-valid recovery.

## 3. Chosen mainline route

Resume the existing D6 R1d Option C eligible-only route instead of inventing another harness:

- `B0_D5_DV3_NATIVE`: failed D5 graph control;
- `B1_D5_DV3_COMMON_LABELS`: labeling/control arm;
- `T1_PEG_DV3`: sole new graph candidate.

Reuse `openspec/changes/v72p2d6-gf32-graph-mother-r1d-option-c/**`, the accepted A4/A6 optimized builders, and `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_R1D_READINESS_R1C_A5.md`.

Do not admit T2, T3, T4, M1 or M2: they are structurally invalid/ineligible or outside the zero-knob Option C route. Do not reuse the historical 184-call A2 root for scientific claims.

## 4. Track and authority

- Track: `EXPLORE_HEAVY` under the newly accepted two-tier workflow.
- This packet authorizes planning, reconciliation, implementation corrections, fake/injected tests, profiling and Pre-EXECUTE readiness.
- It does **not** authorize the real R1d decoder batch. Stop with the exact frozen command, fresh root and measured budget awaiting explicit user authorization.
- No real/raw/VAL data, n=1024 production validation, D7-H, G1/G2 rerun, promotion or push.

## 5. Scientific question

At unchanged Model-F, GF32 decomposition, row budgets, coefficients contract and historical row-layered decoder:

> Does the structurally eligible PEG-DV3 graph restore reproducible marginal syndrome-valid/exact recovery relative to the failed native/common-label controls, first at n=64 and then at n=128/n=256?

This is a graph/code-construction discriminator. Do not change priors, rows, decoder iterations, damping, cross-layer schedule or estimator in the same experiment.

## 6. Allowed files

- `openspec/changes/v72p2d6-gf32-graph-mother-r1d-option-c/**`
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d6_gf32_graph_mother.py`
- its existing D6 runner script
- focused D6 graph-mother tests
- `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/**`
- `docs/decision-log.md` for one route-reconciliation entry
- `AGENT_PROJECT_MEMORY.md` only at accepted memory triage
- one EXPLORE log/result template required by the newly accepted workflow
- this packet/prompt pair

Read existing files before editing. STOP before expanding this list.

## 7. Forbidden scope

- No D7-H implementation or execution.
- No new graph framework, generalized optimizer, DE framework, cache, checkpoint system or integrity machinery.
- No scientific reuse of invalid/blocked D6 A2 decoder records.
- No SC/accumulator/T2 arms and no repair-menu reopening.
- No seed search, adaptive graph selection, tuning after observation, retry/resume or output overwrite.
- No edits to frozen baseline `src/`, `experiments`, historical `tools`, D7/G2 result roots, Model-F root or sibling repositories.
- Preserve unrelated dirty-worktree content; exact allowlist staging only, no `git add -A`.

## 8. Heavy work plan

### H0 — close predecessor state

- **H01**: independently re-read X2/X3/X4 raw artifacts and verify the four inherited bullet points in Section 2.
- **H02**: add an additive D7 acceptance/route-close record: X1–X4 accepted; D5 G2 status becomes `G2_CURRENT_CONFIGURATION_FAILED`; runtime becomes measured 2141.9420988290076 s; D7-H remains unauthorized.
- **H03**: update D6 predecessor references from the old D5 decomposition terminal to the accepted G2/current-configuration failure without rewriting D6 history.

### H1 — audit and reconcile existing R1d implementation

- **H11**: verify current branch, actual D6 code, R1d OpenSpec, A5 validity matrix and cycle state; report exact drift.
- **H12**: prove the dispatch set is exactly B0/B1/T1 and every dispatched cell belongs to `R1D_VALID_SUBSET` and passes live I1 row-degree checks.
- **H13**: verify B0/B1 reproduce their intended D5 control identities and T1 is the only changed graph variable; identify any unintended coefficient/prior/row/decoder difference.
- **H14**: verify the A4/A6 performance path is byte/numerically equivalent to the accepted slow reference on tiny/n64 cases; do not rerun the old 10,897-second benchmark.
- **H15**: resolve stale lifecycle/test-world-state assertions only where they block the fresh R1d run; use snapshot/non-mutation semantics, never delete historical evidence.

### H2 — minimum implementation correction

- **H21**: make only corrections required by H11–H15. No new abstraction if existing R1d functions suffice.
- **H22**: expose per-layer marginal `exact`, `syndrome_ok`, residual syndrome weight, iterations, finite status, graph identity and row/I1 metrics in additive records.
- **H23**: ensure controls and T1 use identical Model-F input, block seeds, rows, decoder (`max_iter=90`, damping=1.0, cold), coefficient-stream contract and call order.
- **H24**: preserve fresh-root/no-overwrite, max-call, wall/RSS and external watchdog behavior.

### H3 — frozen exploratory batch design

Use the existing R1d frozen science unless an actual inconsistency is found:

- canary seeds `2026091000..2026091003`;
- confirmation seeds `2026091010..2026091025`;
- scaling seeds `2026091100..2026091103`;
- n64 rows L1 `(49,59,64)`, L2 `(43,52,64)`;
- n128/n256 only for structurally eligible T1 scaling cells already frozen in R1d;
- max 2500 calls, wall 43200 s, per-call watchdog 120 s, RSS <2 GiB;
- no retries.

Under the new EXPLORE workflow, use one prereg/packet, one fresh result root, one append-only exploration log, and one independent batch-end review. Conditional canary→confirmation→scaling transitions must use the already frozen R1d thresholds; do not create per-arm task packets or reviews.

- **H31**: state the exact transition thresholds and terminal semantics by reference plus a compact literal table; ambiguity is STOP, not planner invention.
- **H32**: choose and record one exact fresh UUID output root; confirm absent.
- **H33**: freeze the exact repo-venv command, external watchdog/process ownership, maximum calls and expected files.
- **H34**: guarantee an early negative canary stops confirmation/scaling without being mislabeled graph-family impossibility.
- **H35**: guarantee a positive T1 result is only exploratory graph-candidate evidence, not FER/qualification/real-data success.

### H4 — validation and readiness

- **H41 T0**: compile/import, constants, arm inventory, exact dispatch-set and tiny math.
- **H42 T1**: structural validity, control identity, T1-only delta, fake decoder call matrix, conditional transitions, crash/nonfinite/resource precedence, no-overwrite and historical-root protection.
- **H43**: run a bounded performance smoke with fake/no-op decoder and real graph builders only; no production decoder calls.
- **H44**: use fresh `workspace/<task>/<uuid>` basetemps; do not touch inaccessible legacy pytest roots.
- **H45**: obtain one independent implementation + Pre-EXECUTE readiness review under the accepted EXPLORE workflow.
- **H46**: stop at `D6_R1D_EXPLORE_READY_AWAITING_EXPLICIT_AUTHORIZATION` with zero production decoder/CAL/VAL calls.

## 9. Route decisions after future execution

Freeze these interpretations before execution:

- **T1 reproducibly restores marginal syndrome-valid/exact recovery at n64 and retains signal at n128/n256** → propose T1-based cross-layer successor; D7-H is still not automatically revived.
- **T1 helps n64 but collapses with length** → graph candidate incomplete; analyze scaling/degree structure before any real data.
- **T1 does not materially beat B0/B1 at n64** → close eligible-only DV3 graph redirect; next mainline proposal must change ensemble/degree distribution or use rate-aligned DE, not add alternations.
- Structural/engineering invalidity → `BLOCKED`, no algorithm conclusion.

Do not invent numeric success thresholds; copy the accepted R1d thresholds exactly in H31. If they conflict with X4 semantics or the new workflow, STOP for main-thread ruling.

## 10. STOP conditions

- `TWO_TIER_WORKFLOW_ACCEPTED` absent.
- D7 X2/X3/X4 raw evidence does not support Section 2.
- Existing R1d thresholds/dispatch set are ambiguous or internally inconsistent.
- Any proposed run varies graph plus prior/rows/decoder/schedule simultaneously.
- Any invalid cell can reach the decoder.
- Required change exceeds Section 6, touches protected evidence, or needs a new dependency/framework.
- A test or independent review fails after one scoped correction attempt.
- Production decoder is reached before explicit later authorization.

Return the exact raw blocker and one decision needed; do not start a substitute route.

## 11. Return contract

Return exactly `COMPLETE` or `BLOCKED`.

`COMPLETE` must report H01–H46, inherited-evidence verification, exact graph-only delta, changed files, tests/profiling, production call count zero, frozen transition table/command/root/budget, independent verdict, commit/no-push state, and terminal `D6_R1D_EXPLORE_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
