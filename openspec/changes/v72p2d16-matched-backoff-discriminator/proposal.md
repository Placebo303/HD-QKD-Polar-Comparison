# Proposal — D16 One-Point Matched-Backoff Discriminator (readiness, D1601)

- Repo: `HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean` (do not switch, no commit/push).
- Change: `v72p2d16-matched-backoff-discriminator`.
- Track: `EXPLORE` readiness planning (this call: OpenSpec docs only; future batch `EXPLORE`).
- Authority (read fully first): `.workbuddy/tasks/D16_MATCHED_BACKOFF_DISCRIMINATOR_READINESS_R1_TASK_PACKET.md` (§1–§6), `AGENTS.md` §1.2/§3/§5/§10.1.
- Predecessor (verified PRESENT by exact-string search):
  `D15_RESULT_ACCEPTED_ROUTE_TO_ONE_POINT_BACKOFF_DISCRIMINATOR` — found in
  `docs/decision-log.md:4290`, `docs/research_cycles/V72P2D15-MARGIN-CURVE/EXPLORATION_LOG.md:192`,
  `.workbuddy/tasks/D16_MATCHED_BACKOFF_DISCRIMINATOR_READINESS_R1_TASK_PACKET.md:10`.
  Verdict: PRESENT → proceed; had it been absent the task required STOP + BLOCKED.
- Trusted context (read-only, not recomputed from raw data): R-audit generator
  loads `L1 548.700215065776` / `L2 412.508145233200` bits; D15 9-cell precedent
  (L2 min-dc-4/n2=0 gate-compatible, 36/36 admitted); R2/D15 shared constructor +
  A1–A6; D15 oracle path; D16 packet frozen matrix.
- This call: D1601 + D1602 only (planner, no production code). No code, no
  execution, no decoder calls (0), no commit, no push.

## Goal

Create the OpenSpec readiness artifacts (proposal, design, tasks, delta spec)
for the D16 one-point matched-backoff discriminator, so D1603–D1609 implement
exactly the frozen packet contract: at n=128 and one matched effective
disclosure factor near 1.139, test whether L055 becomes ADEQUATE while
true-conditioned L2 DV3 ORACLE remains WEAK — closing the gap between the D15
high point and the D14N over-disclosed L2 result without a new degree search.
D1602 arithmetic (exact-rational recomputation of factors, sockets, allocations
+ constructor-feasibility screen) is completed in this call and frozen in
`design.md` §2–§3 — no contradiction found, so no STOP.

## Non-Goals (explicitly out of scope)

- New degree search, APP/forward-transfer/cross-layer alternation, D7-H revival.
- FER / leakage / SKR / real-data / qualification / promotion / optimality /
  publication claims; threshold fitting; L1-vs-L2 investment selection.
- n256 extension; generator change (rows derived from frozen integer m;
  generator NOT changed).
- Rerunning D15/D14N or pooling predecessor evidence (no predecessor pooling).
- Implementation (D1603–D1608), freeze-execution (D1609), execution
  authorization, the real batch (all later calls).
- Any edit outside `openspec/changes/v72p2d16-matched-backoff-discriminator/**`.

## Impact scope

- Allowed files: `openspec/changes/v72p2d16-matched-backoff-discriminator/**`
  only (`proposal.md`, `design.md`, `tasks.md`, `specs/matched-backoff/spec.md`).
- Forbidden: code/scripts/tests/roots/`AGENTS.md`/decision-log.
- Affected spec: new additive delta spec `matched-backoff` (no existing spec modified).
- Frozen baseline (`src/`, `experiments/`, `tools/`) untouched; no output root created.

## Frozen matrix (summary; normative detail in design.md)

- n=128 only. Load L1 `548.700215065776`; m=125; disclosed 625 bits; exact factor
  `1.1390555039696448`. Load L2 `412.508145233200`; m=94; disclosed 470 bits;
  exact factor `1.1393714413428093`. Absolute gap `0.00031593737316448767`.
- Arms: L1 L045, L1 L055, L2 DV3 ORACLE single-layer diagnostic. NO APP arm.
- Variable profiles: L045 71/57/E313; L055 83/45/E301; L2 DV3 128 degree-3, E384.
- Check allocations: L045 m125 `2^62+3^63`; L055 m125 `2^74+3^51`;
  L2 m94 `4^86+5^8`.
- Seeds (fresh, frozen, absence-proven in design.md §6): 12 graph seeds
  L045 `2026094001..04`, L055 `2026094005..08`, L2 `2026094009..12`
  (4 per cell, disjoint per cell) + 8 shared block seeds `2026094101..08`
  (same 8 blocks feed all three cells).
- Calls: 3 arms × 4 graphs × 8 blocks = exactly 96. Setup exactly 22
  (12 graph objects + 8 block samples + 2 plan/manifest).
- Future root + command frozen in design.md §6, proven absent, never created here.

## Predicates and terminals (summary; normative in design.md §5)

Reuse D15 cell predicates independently per 32-trial arm (ADEQUATE ≥24/32 +
≥2 graphs ≥6/8; WEAK ≤16/32 + ≥2 graphs ≤4/8; else MIDDLE). L045 descriptive
only. Gate on L055 + L2 ORACLE, first match:

`D16_ENGINEERING_BLOCKED`, `D16_L2_DEGREE_SIGNAL`, `D16_L1_CONSTRUCTION_SIGNAL`,
`D16_MATCHED_BACKOFF_SUFFICIENT`, `D16_BOTH_WEAK`, `D16_AMBIGUOUS`.

Paired L055/L045 discordances + Wilson intervals descriptive only.

## Budgets (packet §6)

Scientific calls exactly/at most 96; setup exactly/at most 22; wall ≤900 s;
per call ≤120 s; RSS strictly <2 GiB; one CPU process; no
retry/resume/repair/seed search/tuning/adaptive stop.

## Claim ceiling

Synthetic diagnostic only. Select no L1/L2 investment; revive no D7-H; make no
FER/leakage/SKR/real-data/qualification/optimality/publication claims. Stored
terminals remain evidence awaiting main-thread adjudication.

## Acceptance criteria (this call)

- D1602 arithmetic proof table (factors/sockets/allocs/feasibility) recomputed
  exact-rationally by hand with zero contradiction; any contradiction would have
  forced STOP.
- Predecessor marker verdict PRESENT with raw evidence lines.
- Seed/root/command freeze + absence proof (`rg` disjoint from all priors;
  exact candidate strings return zero hits except the packet's own two lines;
  root absent).
- Four OpenSpec files created under the allowed dir only; tasks.md marks
  D1601+D1602 [x], D1603–D1609 packet-exact [ ].
- Zero code edits, zero execution, decoder calls 0, no commit/push.
