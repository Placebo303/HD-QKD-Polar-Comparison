# D11 Canonical Forward APP Batch A1 — execution packet

## 1. Track and authorization

Track: `EXPLORE` with `EXPLORE_HEAVY` cost annotation. Repository/branch:
`HD-QKD_Polar_Comparison` / `formal-ir-v72p1-addendum-clean`.
Prerequisite: `D11_FORWARD_APP_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.

This packet freezes but does not itself authorize the run. The companion
`D11_FORWARD_APP_BATCH_A1_AUTHORIZED_PROMPT.md` explicitly names the one-time
grant; it becomes user authorization only when the user sends it.

## 2. Frozen run

Fresh root, which must be absent:
`workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`.

Exact command, once:

```text
.venv/bin/python scripts/v72p2d11_development.py --forward-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64
```

Use the accepted D11 OpenSpec unchanged: n128 first; n256 only iff n128 is
`D11_FORWARD_SIGNAL`; R3 L1 graph/block seeds and exact replay vectors; L2
seeds `2026092801..06`/`2026092901..06`; shared DV3 L2; CONTROL/MIX plus shared
ORACLE; canonical CHECK_UPDATED/q/APP semantics; exact/syndrome/source/target/
joint separation; frozen gate priorities and terminals. Maximum 360 calls per
width, 720 total.

Budgets: ≤720 scientific calls; ≤64 setup; ≤2400 s wall; ≤120 s/call; RSS
strictly <2147483648 B; one process. No retry/resume, repair, seed replacement/
search, tuning, adaptation or input change.

## 3. Pre-dispatch checks

Append a compact raw record to the D11 `EXPLORATION_LOG.md` before execution:

1. accepted readiness marker and `D11-R1110` verified/no blocker;
2. exact branch and scoped D11/R2/R3 paths unchanged;
3. future root absent, Model-F root present/CAL-only, R3 root unchanged;
4. exact command, seeds, graphs, calls, gates, priorities and budgets match;
5. inspect current d5 `_run_layered_block`: required kwargs including
   `on_blocked_transfer` exist; `"record"` preserves a blocked record rather
   than silently continuing; D11 imported helper identity still matches d5;
6. PROFILE_ONLY 36/36 A1--A6, 360/conditional-720 identities, zero decoder;
7. live unauthorized refusal returns rc2 before root/bind/Model-F load;
8. `py_compile` plus focused D11 and R3 tests pass in a fresh workspace
   basetemp (`-p no:cacheprovider`); no broad suite absent focused failure;
9. unrelated dirty files and prior evidence remain untouched.

Any mismatch stops before the authorized command and leaves the grant
unconsumed. Do not repair it under this execution packet.

## 4. Execute and review

Run the exact command once. The grant is consumed at command start. Retain any
partial/failed root; no repair or rerun is authorized. Record command, exit,
timestamps, calls/setup/resources, 36 graph admissions, L1 replay, provenance,
per-graph/pool source/target/joint exact and syndrome counts, oracle, every gate
clause, conditional dispatch and stored terminal.

Obtain one independent EXPLORE batch-end review with
`EVIDENCE_ACCESS: VERIFIED`. It must read the root and independently recompute:
completeness and identities; graph admission/shared-L2 equality; exact R3 replay;
CHECK_UPDATED fail-close; metric isolation; CONTROL/MIX/oracle counts; gate
priority; conditional n256; terminal; budgets; no retry/replacement/tuning; and
claim ceiling. Review failure blocks use and grants no rerun.

Append results/review to the single D11 log and perform memory triage. Do not
run D7-H, reverse feedback, mixed L2, real data, FER/leakage/SKR/qualification,
commit or push.

Return `D11_FORWARD_APP_BATCH_COMPLETE_REVIEWED_AWAITING_MAIN_ROUTE_DECISION`
only after a completed run and passing review. Otherwise return the exact
blocked terminal, raw evidence and one needed decision. Machine terminal is
evidence only and never self-authorizes the successor.
