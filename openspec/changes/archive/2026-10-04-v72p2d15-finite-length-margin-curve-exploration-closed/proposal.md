# Proposal — D15 Paired Finite-Length Margin Curve (readiness, D1501)

- Repo: `HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean` (no switch, no commit, no push).
- Change: `v72p2d15-finite-length-margin-curve`.
- Track: `EXPLORE` readiness planning (this call: OpenSpec docs only; future batch `EXPLORE`).
- Authority: `.workbuddy/tasks/D15_FINITE_LENGTH_MARGIN_CURVE_READINESS_R1_TASK_PACKET.md`
  (§1–§3 frozen matrix, §5 budgets); `AGENTS.md` §1.2/§3/§5/§10.1.
- Accepted predecessor (verified PRESENT, exact-string search):
  `D14N_RESULT_ACCEPTED_MARGIN_CONFOUNDED_ROUTE_DEFERRED` — found in
  `docs/decision-log.md:4257`, `AGENT_PROJECT_MEMORY.md:3907`,
  `docs/research_cycles/D14_VALIDITY_RESET/EXPLORATION_LOG.md:292`.
  Verdict: PRESENT → proceed; had it been absent the task required STOP.
- Trusted context (read-only, not recomputed from raw data): R-audit generator
  entropies `H_L1=4.286720430201375` (load `548.700215065776`) /
  `H_L2=3.222719884634378` (load `412.508145233200`); D14N m=110 cells
  (L045 71/57/313 `2^17+3^93`; L055 83/45/301 `2^29+3^81`) + D12 m=118 cells;
  D11 L2 DV3 n128 table; R2 shared constructor + A1–A6; D11 oracle path
  (`oracle_l2_prior`); invalid-inference rejections §2 (transcribed verbatim below).
- This call: D1501 + D1502 only (planner, no production code). No code, no
  execution, no decoder calls (0), no commit, no push.

## Goal

Create the OpenSpec readiness artifacts (proposal, design, tasks, delta spec)
for the D15 paired finite-length margin curve, so D1503–D1510 implement exactly
the frozen packet contract: at n=128, compare L1 (L045, L055) and L2 (DV3
ORACLE single-layer diagnostic) at approximately the same effective disclosure
factors over three row points, estimating a small margin curve before any new
degree search. D1502 arithmetic (exact-rational recomputation of loads,
factors, sockets, allocations + constructor-feasibility screen) is completed in
this call and frozen in `design.md` §2–§3 — no contradiction found, so no STOP.

## Non-Goals (explicitly out of scope)

- New degree search, APP transfer/cross-layer alternation, D7-H revival.
- FER / leakage / SKR / real-data / qualification / promotion / optimality /
  publication claims; threshold fitting; L1-vs-L2 investment selection.
- n256 extension; generator change (rates/rows derived from actual generator
  entropy; generator NOT changed).
- Rerunning D12/D14N or pooling predecessor evidence (no predecessor pooling).
- Implementation (D1503–D1508), tests/profile (D1509), independent review
  (D1510), execution authorization, the real batch (all later calls).
- Any edit outside `openspec/changes/v72p2d15-finite-length-margin-curve/**`.

## Impact scope

- Allowed files: `openspec/changes/v72p2d15-finite-length-margin-curve/**`
  only (`proposal.md`, `design.md`, `tasks.md`, `specs/margin-curve/spec.md`).
- Forbidden: code/scripts/tests/roots/`AGENTS.md`/decision-log.
- Affected spec: new additive delta spec `margin-curve` (no existing spec modified).
- Frozen baseline (`src/`, `experiments/`, `tools/`) untouched; no output root created.

## Frozen matrix (summary; normative detail in design.md)

- n=128 only. H_L1 load `548.700215065776`; H_L2 load `412.508145233200`.
- L1 rows m=`110,114,118`, disclosed `550,570,590`, effective ≈`1.00237,1.03882,1.07527`.
- L2 rows m=`83,86,89`, disclosed `415,430,445`, effective ≈`1.00604,1.04240,1.07877`.
- Arms per point: L1 L045, L1 L055, L2 DV3 ORACLE single-layer diagnostic. NO APP arm.
- Variable profiles: L045 71/57/E313; L055 83/45/E301; L2 DV3 128 degree-3, E384.
- Check allocations: L045 m110 `2^17+3^93` / m114 `2^29+3^85` / m118 `2^41+3^77`;
  L055 m110 `2^29+3^81` / m114 `2^41+3^73` / m118 `2^53+3^65`;
  L2 m83 `4^31+5^52` / m86 `4^46+5^40` / m89 `4^61+5^28`.
- Seeds (fresh, frozen, absence-proven in design.md §6): 36 graph seeds
  `2026093801..3836` (4 per each of 9 cells, disjoint per cell) + 8 paired block
  seeds `2026093901..3908` (same 8 blocks feed all nine cells).
- Calls: 3 points × 3 arms × 4 graphs × 8 blocks = 288. Setup ceiling 46
  (36 graph objects + 8 block samples + 2 plan/manifest).
- Future root + command frozen in design.md §6, proven absent, never created here.

## Invalid inferences (packet §2, verbatim — audit must explicitly reject)

- D14N L1 1.002 versus L2 1.261 is not a layer comparison.
- `I <= disclosed bits` is not sufficient for decoding.
- One near-entropy point cannot prove a construction defect.
- D12 absolute success cannot be compared to D14N without the rate change;
  relative L055-versus-L045 evidence remains descriptive.

## Route vocabulary (summary; normative in design.md §5)

`MARGIN_CURVE_L1_SPECIFIC`, `MARGIN_CURVE_L2_SPECIFIC`,
`MARGIN_CURVE_FINITE_BACKOFF`, `MARGIN_CURVE_BOTH_WEAK`,
`MARGIN_CURVE_AMBIGUOUS`, `MARGIN_CURVE_ENGINEERING_BLOCKED`.
Conservative thresholds: highest matched-margin point + cross-point monotonic +
multi-graph support; no single pooled count closes route.

## Budgets (packet §5)

Scientific calls exactly/at most 288; setup exactly/at most 46; wall ≤1800 s;
per call ≤120 s; RSS strictly <2 GiB; one CPU process; no
retry/resume/repair/seed search/tuning/adaptive stop.

## Claim ceiling

Synthetic diagnostic only. Fit no asymptotic threshold from three points; select
no L1/L2 investment; revive no D7-H; make no FER/leakage/SKR/real-data/
qualification/optimality/publication claims.

## Acceptance criteria (this call)

- D1502 arithmetic proof table (loads/factors/sockets/allocs/feasibility) recomputed
  exact-rationally with zero contradiction; any contradiction would have forced STOP.
- Predecessor marker verdict PRESENT with raw evidence lines.
- Seed/root freeze + absence proof (`rg` disjoint from 24xx–37xx priors; exact
  candidate strings return zero hits; root absent).
- Four OpenSpec files created under the allowed dir only; tasks.md marks
  D1501+D1502 [x], D1503–D1510 packet-exact [ ].
- Zero code edits, zero execution, decoder calls 0, no commit/push.
