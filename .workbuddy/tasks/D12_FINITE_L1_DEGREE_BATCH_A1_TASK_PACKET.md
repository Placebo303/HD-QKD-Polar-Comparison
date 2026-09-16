# D12 Finite L1 Degree Batch A1 — execution packet

## 1. Track and grant boundary

Track: `EXPLORE` with `EXPLORE_HEAVY` cost annotation. Repository/branch:
`HD-QKD_Polar_Comparison` / `formal-ir-v72p1-addendum-clean`.
Prerequisite:
`D12_FINITE_L1_DEGREE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.

This packet freezes but does not authorize execution. The companion authorized
prompt becomes the user's explicit one-time grant only when the user sends it.

## 2. Frozen run

Fresh root, required absent:
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`.

Exact command, once:

```text
.venv/bin/python scripts/v72p2d12_development.py --d12-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450
```

Use accepted OpenSpec unchanged: L045/L050/L055; exact degree tables; n128
graphs `2026093001..06`, blocks `2026093201..12`; n256 graphs
`2026093101..06`, blocks `2026093301..12`; both widths always run; 432 L1
calls; exact primary with syndrome/undetected separate; frozen STABLE,
MATERIAL_BETTER, ranking, split and terminal rules. The L050/n256 seed
2026093101 four-cycle is retained and is not a replacement trigger.

Budgets: ≤432 scientific calls; ≤62 setup; ≤1800 s wall; ≤120 s/call; RSS
strictly <2147483648 B; one process. No retry/resume, repair, seed replacement/
search, tuning, adaptation or input change.

## 3. Pre-dispatch checks

Append a compact raw record to the D12 `EXPLORATION_LOG.md` before execution:

1. accepted marker and `D12-R1210` VERIFIED/PASS/no blocker;
2. exact branch and scoped D12/R2/R3 paths unchanged; unrelated dirt preserved;
3. future root absent, Model-F CAL-only root present/unchanged, predecessor roots
   untouched;
4. command, six degree cells, seeds, 432 identities, gates/ranking and budgets
   match OpenSpec;
5. PROFILE_ONLY: 36/36 A1--A6, deterministic, zero replacements/calls/root;
6. live unauthorized `--d12-batch` refusal rc2 before write/bind/Model-F load;
7. `py_compile` plus focused D12 and directly affected R2/R3 tests pass in a
   fresh workspace basetemp with `-p no:cacheprovider`;
8. execution state and unrelated outputs untouched.

Any mismatch stops before the authorized command and leaves the grant
unconsumed. No repair is permitted under A1.

## 4. Execute, review and return

Run the exact command once; authorization is consumed at command start. Retain
any failed/partial root. Record command/exit/timestamps, calls/setup/resources,
36 admissions, per-graph/width/arm exact and syndrome results, undetected,
paired discordances, every STABLE/MATERIAL/split/rank clause and terminal.

Then obtain one independent EXPLORE batch-end review with
`EVIDENCE_ACCESS: VERIFIED`. It independently reads the root and recomputes
completeness, identities, degree/admission, exact/syndrome/undetected isolation,
paired counts, selection/ties/split, terminal, budgets, zero replacement/retry/
tuning and claim ceiling. Review failure blocks use and grants no rerun.

Append evidence/review to the single D12 log and perform memory triage. Do not
run forward/L2, D7-H, real data or claim-bearing calculations. Do not commit or
push unless requested.

Return `D12_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION` only after a
completed run and passing review. Otherwise return the exact blocker with raw
evidence and one decision. The selected/retained machine terminal is evidence
only and never self-authorizes the next route.
