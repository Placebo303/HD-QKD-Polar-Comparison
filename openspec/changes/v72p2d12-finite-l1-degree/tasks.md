# Tasks — D12 finite L1 degree refinement (readiness D1201–D1210)

Packet: `.workbuddy/tasks/D12_FINITE_L1_DEGREE_REFINEMENT_READINESS_TASK_PACKET.md`
(sole authority; §1–§4 frozen). Track: implementation/readiness (zero
scientific calls; no D12 batch, no L2, no D7-H, no real data, no commit/push).
Branch `formal-ir-v72p1-addendum-clean` (do not switch; no commit, no push).
Predecessor immutable: `D11_FORWARD_APP_WIDE_RECOVERY_ACCEPTED_ROUTE_TO_D12_L1_REFINEMENT`
(root `workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`,
terminal `D11_FORWARD_APP_WIDE_RECOVERY`, VERIFIED PASS_WITH_FINDINGS;
read-only context, A1/R3/D11 evidence never pooled into D12).

- [x] D1201: create D12 OpenSpec proposal/design/tasks/spec before behavior edits.
- [x] D1202: audit and import D9 exact realization plus D10 R2/R3 construction,
  prior and decoder paths; no duplicate framework or message semantics.
- [x] D1203: implement thin additive plan/runner/verifier with frozen tables, seeds,
  432 identities, gates, ranking and terminals.
- [x] D1204: default-false explicit execution flag; unauthorized refusal before
  root creation, decoder binding or Model-F load.
- [x] D1205: enforce all 36 graphs A1--A6 before decoder binding; zero replacements.
- [x] D1206: never-overwrite minimal root and fail-closed verifier independently
  recomputing identities, metrics, gates/rank and terminal.
- [x] D1207: focused tests for exact tables, seed separation, shared construction,
  all gate/tie/split boundaries, exact/syndrome/undetected isolation, budgets,
  no-write refusal and verifier; decoder entry fake-injected only.
- [x] D1208: `py_compile` plus focused D12 and directly affected D10 tests in a
  fresh workspace basetemp; no broad suite absent focused external failure.
- [x] D1209: PROFILE_ONLY all 36 graphs and full plan; require 36/36 A1--A6,
  deterministic replay, zero replacements/calls and absent future root.
- [x] D1210: one independent reviewer-go readiness review with
  `EVIDENCE_ACCESS: VERIFIED`, recomputing degree math/admission, isolation,
  gates/ranking, budgets and no-production boundary; append one log/readiness
  record and perform memory triage.

D1201 evidence (this task): new additive change
`openspec/changes/v72p2d12-finite-l1-degree/` (`proposal.md`, `design.md`,
`tasks.md`, `specs/finite-l1-degree/spec.md`); frozen L1-only f1.2 n128+n256
always measured; fresh seeds n128 graphs `2026093001..06` blocks
`2026093201..12`, n256 graphs `2026093101..06` blocks `2026093301..12`
(absence-scan recorded in `design.md` §7; no collision); six cells table
(L050 n128 77/51/307 `2^47+3^71`; L055 n128 83/45/301 `2^53+3^65`; L050 n256
154/102/614 `2^94+3^142`; L055 n256 166/90/602 `2^106+3^130`; L045 cells as in
D10 R1); shared constructor + A1-A6 + coeff rule + Model-F CAL-only L1 prior +
GF32/poly37 + max_iter90/damping1.0/cold; only forced degree counts differ; no
replacement/search/adaptation; plan 432 identities (3×6×12×2); exact primary +
syndrome/undetected separate + paired discordances; STABLE rule;
MATERIAL_BETTER 4-clause (both widths) + ranking (total, worst-width, smaller
λ2) + retain-L045 + SPLIT_WIDTH_CONFLICT verbatim; five terminals +
eng-blocked; descriptive p-values; future root
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`
(absent verified); budgets ≤432/≤62/1800s/120s/RSS<2GiB/1-proc/
no-retry-resume-repair-search-tune; claim ceiling (finite L1 comparison only).
Allowed files: `openspec/changes/v72p2d12-finite-l1-degree/**` only.
Zero decoder calls; no commit/push.

D1202 evidence (this task): D9-recomputation raw evidence (rule + arithmetic
per cell) in `design.md` §2 — all six cells EXACT, no mismatch; import map
(`path:line`) + duplication rejection in `design.md` §6; seed/root absence scan
raw output in `design.md` §7 — no collision; preserved-items checklist in
`design.md` §8. Audit found all accepted paths — no BLOCKED condition met.

Gate: return `D12_FINITE_L1_DEGREE_READY_AWAITING_EXPLICIT_AUTHORIZATION`
only when D1201–D1210 pass with zero scientific calls and no blocker
(packet §4). STOP on requirement ambiguity, D9 table mismatch, seed drift,
admission failure, need for replacement/search, decoder/scientific entry, root
creation, failed review, or conflicting dirty edits. Do not execute D12,
change predecessors, touch L2/D7-H, commit or push.
