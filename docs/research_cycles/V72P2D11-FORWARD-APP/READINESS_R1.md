# D11 canonical forward APP integration — readiness R1 (no execution)

Authority: `.workbuddy/tasks/D11_FORWARD_APP_INTEGRATION_READINESS_TASK_PACKET.md` §3 (D1101–D1110) + §4 (STOP/return).
Track for this record: documentation-only (no code, no execution, no decoder/scientific calls, no root creation, no commit/push).
Branch: `formal-ir-v72p1-addendum-clean` (no switch).
Review: `REVIEW_ID D11-R1110`, `EVIDENCE_ACCESS VERIFIED`, trusted, not rerun.

## Predecessor (immutable)

- Accepted route: `D10_R3_WIDE_L1_SIGNAL_ACCEPTED_ROUTE_TO_D11_FORWARD_APP`.
- Machine terminal (immutable): `D10_R3_WIDE_L1_SIGNAL_REPRODUCED` (n128 MIX 23/72 + n256 MIX 29/72 vs DV3 0/72, both `R3_REPRODUCED`).
- Evidence root: `workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d` (six-file root, batch-end review `D10-R3-B1-REVIEW` VERIFIED PASS).
- R3 L1 evidence is reused for replay only, never pooled with D11 metrics.

## Frozen design summary (packet §2)

- Widths: n128 first; n256 only iff n128 is `D11_FORWARD_SIGNAL`.
- L1 reuse (exact replay gate): n128 graphs `2026092401..06` + blocks `2026092601..12`; n256 graphs `2026092501..06` + blocks `2026092701..12`. Per-graph exact must equal R3 MIX n128 `[4,4,2,5,3,5]` / n256 `[6,3,5,5,6,4]`, CONTROL all zero; mismatch is engineering-blocked before interpretation.
- L2 (one shared connected/full-rank DV3 graph per pair): n128 seeds `2026092801..06`, m=104, E=384, checks `3^32+4^72`; n256 seeds `2026092901..06`, m=208, E=768, checks `3^64+4^144`. Connectivity-first constructor, A1–A6, frozen coefficient rule, GF32/poly37, Model-F prior chain, max_iter=90/damping=1.0/cold, canonical CHECK_UPDATED provenance/q/APP helpers. D5/D7 forward-transfer and D6 oracle definitions reused; no reimplemented message semantics.
- Branches (only treatment difference is L1 degree profile): CONTROL = DV3 L1 → shared DV3 L2 APP decoder; MIX = λ2=0.45 mixed L1 → same shared DV3 L2 APP decoder; ORACLE = same L2 graph/block with accepted true-L1 conditional prior, once per graph/block, shared diagnostically, excluded from arm grading.
- Cells/calls: 72 L1+L2 paired cells per width; 72 CONTROL-L1 + 72 CONTROL-L2 + 72 MIX-L1 + 72 MIX-L2 + 72 shared ORACLE-L2 = 360 per width, max 720.
- Metric isolation: exact / syndrome-valid / L1-source-exact / L2-target-exact / joint-both-exact kept distinct; `undetected` never merged into success.
- Fail-close: every non-oracle transfer provenance must be `CHECK_UPDATED`; uniform/prior-only fallback forbidden.
- Gates: `D11_FORWARD_SIGNAL(w)` iff `J_M>=9`, `J_M-J_C>=6`, MIX wins ≥4/6 pairs, ≥3/6 MIX graphs `J_Mg>=1`, `J_C<=3`, `O>=18`, all 144 non-oracle transfers CHECK_UPDATED, no engineering/resource violation. Bottlenecks: `D11_TRANSFER_BOTTLENECK(w)` (MIX L1 exact ≥18, `J_M<=3`, `O>=18`); `D11_L2_CODE_BOTTLENECK(w)` (`O<=6`); else `D11_FORWARD_AMBIGUOUS(w)`. Priority: engineering block > L2-code bottleneck > forward signal > transfer bottleneck > ambiguous.
- Terminals: both-signal → `D11_FORWARD_APP_WIDE_RECOVERY`; n128-signal + n256-other → corresponding `D11_N256_*`; n128-stop → corresponding `D11_N128_*`; else explicit engineering/resource blocked terminal.
- Future root: `workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64` (absent at readiness).
- Budgets: ≤720 scientific calls; ≤64 setup units; ≤2400 s wall; ≤120 s/call; RSS <2147483648 B; one process; no retry/resume/repair/seed search/tuning.
- Claim ceiling: synthetic two-layer forward diagnostic only; no FER, leakage, SKR, real-data, qualification, promotion, optimality, or D7-H claim.

## D1101–D1110

| ID | Requirement (packet §3) | Evidence / result |
|---|---|---|
| D1101 | OpenSpec proposal/design/tasks/spec before behavior edits | Change `openspec/changes/v72p2d11-forward-app/` present with equations, priorities, seeds, calls, terminals, rationale — PASS (R1110 scope check) |
| D1102 | Audit nearest accepted forward-APP/provenance/oracle helpers; reuse map, no semantic duplication | 16/16 def symbols present, 17/17 is-identical imports (transfer/provenance/q-APP/oracle/admission/coeff/decoder), no new message interface, reverse leg never invoked, L1 seed into build_l2_graph refused, L2 DV3-only guard — PASS |
| D1103 | Thin additive plan/runner/verifier reusing D10 R2/R3 + D5/D7 helpers | Additive footprint; no reimplemented semantics — PASS |
| D1104 | Explicit default-false execution CLI flag; refuse before root/decoder/Model-F | v35 lazy-only; refusal precedes root/bind/Model-F-load; refusal exit 2 no-write — PASS |
| D1105 | L1/L2 A1–A6 + exact R3 L1 replay before grading; no seed replacement | REPLAY_MIX verbatim (n128 `[4,4,2,5,3,5]`, n256 `[6,3,5,5,6,4]`, CONTROL zeros); R3 shared references; mismatch → eng-blocked — PASS |
| D1106 | Call accounting, provenance fail-close, gate priorities, conditional n256, never-overwrite output, fail-closed read-only verifier | 8-clause signal + both bottlenecks + ambiguous + priority (eng>L2>signal>transfer>ambiguous) + 8 terminals + conditional n256 + 360/720 identities functionally verified — PASS |
| D1107 | Focused tests (tables/seeds, shared-L2 identity, call ceiling, replay mismatch, provenance refusal, isolation, gate/terminal boundaries, conditional dispatch, no-write refusal; fake-injected production) | Focused D11 tests in fresh basetemp per packet — PASS (R1110 scope check) |
| D1108 | `py_compile` + focused D11 and directly affected predecessor tests in fresh basetemp | Fresh-basetemp run per packet; no broad suite absent focused external failure — PASS (R1110 scope check) |
| D1109 | PROFILE_ONLY all future L1/L2 graphs + plan (A1–A6, deterministic replay, 360→720 identities, zero decoder calls, root absent) | PROFILE 36/36 (L2 12/12 + L1 24/24) A1–A6, plan 360/720, decoder 0, root absent, 3.3 s — PASS |
| D1110 | Independent readiness review (`EVIDENCE_ACCESS: VERIFIED`) + one log/readiness record + memory triage | `REVIEW_ID D11-R1110` VERIFIED `PASS_WITH_FINDINGS`, BLOCKING none (this record + `EXPLORATION_LOG.md` are the appended record; memory triage separate) — PASS |

R1110 cross-cutting (trusted VERIFIED, not rerun): branch confirmed no switch; isolation (one shared L2/pair across CONTROL/MIX/ORACLE — 6 distinct/width, CONTROL/MIX share, L1 distinct; oracle once per cell riding MIX, excluded from arm grading; exact/syndrome/joint distinct); budgets (720/64/2400/120/2GiB/1-proc/no-retry in code+spec+manifest); no-production (zero scientific calls, no D7-H). TEST_RERUN 33/33 in own basetemp `/tmp/d11-r1110-review`.

R1110 non-blocking findings: (a) dirty worktree incl. 323-line v72p2d5 change adding kwargs to `_run_layered_block` that D11 depends on (`on_blocked_transfer="record"`) — reconfirm d5 tree state at Pre-EXECUTE; (b) operator `/tmp` basetemps adjudicated non-blocking (all claims independently re-verified); (c) 23 R3 tests not re-run (ceremonial per trust rule).

## Authorization state (this record)

- D11 execution authorized: false. Explicit authorization granted: none.
- Future root `workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`: absent (`ls: cannot access ... No such file or directory`).
- Decoder calls: 0. Scientific calls: 0. Commit/push: none.

## Terminal

`D11_FORWARD_APP_READY_AWAITING_EXPLICIT_AUTHORIZATION` (grants no execution).

Pre-EXECUTE note: reconfirm the v72p2d5 dirty-tree state (finding (a) above) before any authorized batch — the D11 dependency kwargs must be as-reviewed.

Next gate: a separate explicit batch grant naming batch/branch/root/seeds/budgets is required before any D11 execution. Readiness and R1110 grant nothing.

Claim boundary: synthetic two-layer forward diagnostic only; no FER/leakage/SKR/real-data/qualification/promotion/optimality/D7-H claim. D7-H remains closed.

## 2026-09-14 — main-thread readiness acceptance

`D11_FORWARD_APP_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
The independent `D11-R1110` review is accepted without duplicate testing.
All D1101--D1110 requirements pass; the dirty-tree dependency finding is
carried as a concrete execution preflight check of `_run_layered_block` and its
`on_blocked_transfer="record"` behavior. This accepts readiness only and grants
no execution. Next packet:
`.workbuddy/tasks/D11_FORWARD_APP_BATCH_A1_TASK_PACKET.md`.
