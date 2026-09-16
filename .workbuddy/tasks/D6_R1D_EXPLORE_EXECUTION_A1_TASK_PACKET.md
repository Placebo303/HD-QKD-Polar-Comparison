# D6 R1d EXPLORE execution authorization A1

## 1. Authority and current gate

- Repository: `D:\Code\HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`; do not switch.
- Track: `EXPLORE_HEAVY` (still the `EXPLORE` lifecycle).
- Accepted workflow marker: `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE` or compatibility alias `TWO_TIER_WORKFLOW_ACCEPTED`.
- Accepted readiness terminal: `D6_R1D_EXPLORE_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
- Sending the paired prompt verbatim from the user is the explicit authorization for exactly one frozen R1d batch invocation described below.

This authorization does not cover D7-H, G1/G2 reruns, T2/T3/T4/M1/M2, real/VAL/raw data, n1024, tuning, promotion, commit or push.

## 2. Read before acting

Read completely:

- `.workbuddy/tasks/D6_MAINLINE_GRAPH_REDIRECT_HEAVY_R1_TASK_PACKET.md`
- `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_R1D_HEAVY_R1_READINESS.md`
- `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_R1D_HEAVY_R1_READINESS_REVIEW.md`
- `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/EXPLORATION_LOG_R1D.md`
- `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/cycle_state.yaml`
- the accepted R1d execution packet referenced by the readiness record.

Trust the H45 reviewer-go independent reruns under the recorded evidence scope. Do not rerun the 343-test suite merely for ceremony.

## 3. Pre-dispatch checks

Before changing an authorization flag or creating the root, verify and append the raw outcome to `EXPLORATION_LOG_R1D.md`:

1. workflow and readiness markers above are present;
2. every D6 authorization key is false and `evidence_root`/`terminal` are null;
3. planned root is absent;
4. exact dispatch arms are `{B0_D5_DV3_NATIVE,B1_D5_DV3_COMMON_LABELS,T1_PEG_DV3}`;
5. Model-F root is `workspace/v72p2d5_model_f_input/20260907_r1`, CAL-only, and unmodified;
6. H45 verdict is `PASS_WITH_FINDINGS`, with F1–F3 fixed and F4 carried;
7. run only the smallest focused preflight needed to detect drift since H45: compile the changed runner and run the 14 R1d focused tests plus the 14 BP-compat tests with a fresh task-owned basetemp. Do not rerun broad suites unless this focused preflight fails for a concrete dependency reason.

Any mismatch is `BLOCKED_PRE_DISPATCH`; do not repair, substitute a root, or execute.

## 4. Exact frozen invocation

Authorize only this command, from repository root using the repository venv:

```text
.venv/bin/python scripts/v72p2d6_graph_mother_development.py --r1d --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d6_graph_mother_r1d_141730d1-5ed4-4a60-a935-50e8f24f872d --workers 18
```

The operator may apply only the readiness-recorded RSS pilot downgrade `18→14→12→8`. This is resource control, not a scientific variation. No other command, root, arm, seed, row, prior, coefficient, decoder, schedule or threshold substitution is authorized.

Frozen limits:

- ≤2500 total calls and ≤552 scientific calls;
- ≤43200 s total wall;
- 120 s per-call watchdog;
- aggregate RSS strictly below 2 GiB;
- no retry, resume, seed search, adaptive tuning or overwrite.

The conditional canary → confirmation/scaling sequence and terminal semantics are exactly those copied into the readiness record. A scientific negative is a valid completed EXPLORE result. Crash, nonfinite, invariant violation, unknown/over-limit RSS, watchdog, wall or chunk failure retains the partial root and stops without an algorithm conclusion.

## 5. Lifecycle writes

Immediately before the invocation, set only the minimum D6 R1d authorization state required by the existing runner and record that this A1 authorization is active. Immediately after exit or interruption, restore every execution authorization flag to false and record:

- command and exit code;
- start/end/wall and process ownership;
- actual workers and any allowed RSS downgrade;
- call counts and stages reached;
- output root and expected-file inventory;
- terminal or blocking status;
- the previously disclosed pre-fix test-machinery incident and H45 F4 upper-bound wording.

Do not rewrite historical D6/D7 evidence. Do not create a separate document per arm; keep the single append-only exploration log.

## 6. Batch-end independent review

After the invocation, dispatch one independent reviewer-go subagent with access to the actual root. The reviewer must independently:

- run the existing read-only verifier;
- recount stage/arm/width/seed/mode records and all advancement predicates;
- verify exact and syndrome-valid remain separate and residual syndrome weights are coherent;
- verify call/wall/watchdog/RSS/no-retry/no-overwrite limits;
- confirm B0/B1 controls and T1-only graph delta;
- inspect crash/nonfinite/resource precedence and retained partial evidence;
- adjudicate H45 F4 without inventing an exact historical incident count;
- state `EVIDENCE_ACCESS`, verdict, claim ceiling and blocking findings.

Trust a `VERIFIED` reviewer result within its stated scope; do not mechanically duplicate its test run. A blocking finding prevents result acceptance and route advancement.

## 7. Main-thread boundary and return

The operator/reviewer may append execution and review evidence and advance the D6 cycle only to:

- `D6_R1D_EXPLORE_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`, or
- an exact `D6_R1D_EXPLORE_BLOCKED_*` state.

They may not accept the scientific interpretation, choose the successor route, revive D7-H, commit or push. Memory triage remains deferred until main-thread result acceptance.

Return exactly `COMPLETE` or `BLOCKED` and report only deltas: pre-dispatch checks, exact command, exit, calls/stages/resources, terminal, primary per-arm results, root inventory, independent verdict/findings, authorization flags restored false, changed files, and commit/no-push state.

## 8. Why D7-H remains excluded

X4 showed zero syndrome-valid recovery for both base layers across 600 n256 blocks, while X3 recovered only 1/156 failures by increasing iterations and none with flooding-90. D7-H changes alternation without repairing this base graph/code failure. The next informative variable is therefore the frozen D6 graph construction discriminator. D7-H can be reconsidered only after a graph/code candidate shows reproducible marginal recovery; this A1 cannot revive it.
