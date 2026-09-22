# D10 R3 Fresh-Graph Scaling Batch A1 — execution packet

## 1. Track, prerequisite and authorization boundary

Track: `EXPLORE` with `EXPLORE_HEAVY` cost annotation. Repository/branch:
`HD-QKD_Polar_Comparison` / `formal-ir-v72p1-addendum-clean`.

Prerequisite:
`D10_R3_FRESH_GRAPH_SCALING_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
This packet freezes execution but does not itself authorize it. A user message
must explicitly authorize this batch, branch, root, seeds, conditional sequence
and budgets. The companion `...AUTHORIZED_PROMPT.md` is written so that the
user's act of sending it supplies that explicit grant.

## 2. Frozen command and contract

Fresh root, which must be absent:
`workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`.

Run exactly once after authorization:

```text
.venv/bin/python scripts/v72p2d10_r3_development.py --r3-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d
```

Frozen primary seeds:

- n128 graphs `2026092401..06`, blocks `2026092601..12`;
- n256 graphs `2026092501..06`, blocks `2026092701..12`.

Run 144 n128 calls first. Run 144 n256 calls iff n128 is `R3_REPRODUCED`.
A1 evidence remains contextual and unpooled. Use the accepted six-clause gate,
negative/ambiguous rules and six terminals verbatim. Exact is primary;
syndrome-valid remains separate. McNemar/intervals are descriptive only.

Budgets: ≤288 scientific calls; ≤50 setup; ≤1800 s wall; ≤120 s/call; RSS
strictly <2147483648 B; one process. No retry/resume, repair, seed replacement/
search, tuning, adaptation or changed scientific input.

## 3. Pre-dispatch checks

Append a compact raw record to the R3 `EXPLORATION_LOG.md` before execution:

1. accepted readiness marker and R310 verified review/no blocker;
2. exact branch and scoped R3/R2 files unchanged;
3. future root absent; Model-F CAL-only root present/unchanged; A1 root unchanged;
4. command, arms, degree tables, all seeds, gates and budgets match OpenSpec;
5. PROFILE_ONLY: 24/24 A1--A6, zero replacements, no decoder/root;
6. deferred live unauthorized `--r3-batch` refusal returns rc2 before write/
   bind/Model-F load;
7. `py_compile` and focused R3 plus R2 tests pass in one fresh basetemp;
8. no unrelated output or authorization is touched.

Any failure stops before the authorized command and leaves the grant unconsumed.

## 4. Execution, review and return

Run the exact command once. Authorization is consumed when it starts. Retain a
failed/partial root; A1 authorizes no repair or rerun. Record exact command,
exit/timestamps, call/setup/wall/per-call/RSS, 24 graph admissions, per-graph and
pooled exact/syndrome counts, gate clauses, progression and stored terminal.

Then obtain one independent EXPLORE batch-end review with
`EVIDENCE_ACCESS: VERIFIED`. It independently reads the root and recomputes
completeness, call identities, seed isolation, A1--A6, exact/syndrome separation,
per-graph/pool gates, A1 non-pooling, conditional n256 dispatch, terminal,
budgets, no retry/replacement/tuning and claim ceiling. Review failure blocks
use of evidence and grants no rerun.

Append everything to the single R3 log and perform memory triage. Do not run
L2/APP, D7-H, real data, qualification or publication calculations. Do not
commit/push unless requested.

Return `D10_R3_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION` only after
a completed run and passing review. Otherwise return the exact engineering/
resource/review blocker with raw evidence and one decision needed. Machine
terminals are evidence only and never self-select the next route.
