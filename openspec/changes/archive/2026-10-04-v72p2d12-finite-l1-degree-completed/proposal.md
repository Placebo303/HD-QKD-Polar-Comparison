# Proposal — D12 finite L1 degree refinement (readiness, D1201)

- Change: `v72p2d12-finite-l1-degree`
- Cycle: `V72P2D12-FINITE-L1-DEGREE` (successor refinement; NOT a correction of any predecessor)
- Track: **implementation/readiness** (zero scientific calls; no D12 batch, no L2, no D7-H, no real data, no commit/push). The future batch is `EXPLORE_HEAVY`.
- Authority (read fully first, frozen):
  `.workbuddy/tasks/D12_FINITE_L1_DEGREE_REFINEMENT_READINESS_TASK_PACKET.md`
  (§1–§4), `AGENTS.md` §1.2/§3/§5/§10.1.
- Predecessor (immutable, read-only context, never pooled into D12):
  `D11_FORWARD_APP_WIDE_RECOVERY_ACCEPTED_ROUTE_TO_D12_L1_REFINEMENT`
  (machine terminal `D11_FORWARD_APP_WIDE_RECOVERY`, VERIFIED PASS_WITH_FINDINGS;
  root `workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`).
  A1/R3/D11 evidence is contextual only and SHALL never enter D12 gate arithmetic.
- Branch: `formal-ir-v72p1-addendum-clean` (do not switch; no commit, no push).

## Goal

D11 shows that forward APP preserves nearly every mixed-L1 success. The next
limiting variable is L1 exact recovery. Build the smallest finite comparison of
the three already justified D9 degree mixes: λ2=0.45 baseline, 0.50 challenger,
0.55 challenger. Do not reopen a broad grid, change decoder schedule, touch L2,
or run D7-H. This change freezes the complete D12 contract (three arms, exact
degree cells, fresh seeds, shared connectivity-first constructor + A1–A6,
coefficient rule, Model-F CAL-only L1 prior, decoder contract, 432-identity
plan, frozen STABLE / MATERIAL_BETTER gates, ranking, terminals, future root,
budgets, claim ceiling) BEFORE any behavior edit, so D1203–D1210 can implement
readiness with zero scientific decoder calls.

## Non-Goals (hard prohibitions)

- No scientific decoder call in this change or any D1201–D1210 readiness step
  (zero D12 batch calls, zero L2 execution, zero D7-H revival, zero real-data
  contact). This task authorizes OpenSpec work, audit reads, and (for
  successors) focused fake tests and no-decoder graph profiling only.
- No broad degree-grid search, no decoder-schedule change, no L2 work, no D7-H.
- No rerun, modification, re-thresholding, or pooling of A1/R3/D11 evidence;
  predecessors stay contextual-only.
- No seed search, replacement, repair, resume, retry, adaptation, or tuning;
  fresh seeds are never searched or replaced.
- No FER/leakage/SKR/qualification/promotion/publication/real-data/optimality
  claim; claim ceiling is a finite L1 comparison only.
- No modification of predecessor roots, frozen baselines, `AGENTS.md`, or
  decision-log; no commit or push; no future-root creation in readiness.
- This change grants NO execution; the future batch still needs separate
  explicit authorization naming batch/branch/root/seeds/budgets.

## Impact Scope

- ADDED: `openspec/changes/v72p2d12-finite-l1-degree/` only (`proposal.md`,
  `design.md`, `tasks.md`, `specs/finite-l1-degree/spec.md`).
- READ-ONLY references: D12 packet §1–§4; D9 design §5 + D9 root `summary.json`
  `graph.cells`; D10 R1 `READINESS_R1.md` F03; R2 constructor/decoder path
  (`v72p2d10_mixed_degree_l1.py`); R3 plan/seed/block pattern
  (`v72p2d10_r3_fresh_scaling.py`); Model-F L1 prior chain; v35 row-layered
  decoder contract; D11 root (context only).
- FORBIDDEN: all code/scripts/tests/roots/results/predecessor
  artifacts/`AGENTS.md`/decision-log. A NEW additive change is used
  (preferred): D12 is a successor refinement, not a predecessor correction —
  existing changes are NOT amended.

## Frozen scientific design (packet §2, transcribed exactly)

L1-only, f1.2, widths n128 and n256, both always measured. Six fresh graph
seeds and 12 fresh paired block seeds per width:

- n128 graphs `2026093001..06`, blocks `2026093201..12`;
- n256 graphs `2026093101..06`, blocks `2026093301..12`.

Arms and exact node counts from the accepted D9 realization rule:

| width | arm | n2 | n3 | E | checks |
|---|---|---:|---:|---:|---|
| 128 | L045 | 71 | 57 | 313 | `2^41+3^77` |
| 128 | L050 | 77 | 51 | 307 | `2^47+3^71` |
| 128 | L055 | 83 | 45 | 301 | `2^53+3^65` |
| 256 | L045 | 141 | 115 | 627 | `2^81+3^155` |
| 256 | L050 | 154 | 102 | 614 | `2^94+3^142` |
| 256 | L055 | 166 | 90 | 602 | `2^106+3^130` |

Require the accepted shared connectivity-first constructor, A1--A6, coefficient
rule, Model-F CAL-only L1 prior, GF32/poly37 and decoder max_iter=90/damping=1.0/
cold. Only forced degree counts differ. No replacement/search/adaptation.

Plan: 3 arms × 6 graphs × 12 blocks × 2 widths = 432 L1 calls. Exact is
primary; syndrome-valid and undetected remain separate. Report per-graph,
per-width and pooled paired discordances.

An arm is `STABLE(w)` when exact ≥18/72, at least 5/6 graphs have ≥2 exact,
and no engineering/resource violation. L045 is the frozen reference.

A challenger is `MATERIAL_BETTER` only if, at both widths: it is STABLE; exact
is at least L045+6; pooled challenger-only discordance exceeds L045-only; and
it has higher per-graph exact on at least 4/6 graph pairs.

Selection:

- if exactly one challenger is MATERIAL_BETTER, select it;
- if both are, rank by total exact, then worst-width exact, then smaller λ2;
- if neither is and there is no split-width conflict, retain L045;
- `SPLIT_WIDTH_CONFLICT` when a challenger beats L045 by ≥6 at one width but
  trails by >2 at the other, or widths favor opposing challengers.

Terminals: `D12_SELECT_L050`, `D12_SELECT_L055`,
`D12_RETAIN_L045_NO_MATERIAL_GAIN`, `D12_FINITE_DEGREE_SPLIT_AMBIGUOUS`, or
an explicit engineering/resource blocked terminal. Descriptive p-values do not
override the frozen selection.

Future root:
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`.
Budgets: ≤432 scientific calls; ≤62 setup (=36 graphs+24 block samples+2);
≤1800 s wall; ≤120 s/call; RSS <2147483648 B; one process; no retry/resume/
repair/seed search/tuning.

Claim ceiling: synthetic finite L1 degree comparison only; no forward/L2,
FER/leakage/SKR, real-data, qualification, optimality or D7-H claim.

## Acceptance Criteria (D1201–D1202)

- D1201: this OpenSpec change exists with packet §2 frozen verbatim (widths,
  seeds, six-cell table, constructor/A1–A6/coeff rule, Model-F prior,
  GF32/poly37, max_iter=90/damping=1.0/cold, forced-counts-only difference,
  432-identity plan, exact/syndrome/undetected isolation, STABLE rule,
  MATERIAL_BETTER 4-clause at both widths, ranking, retain-L045,
  SPLIT_WIDTH_CONFLICT verbatim, five terminals + eng-blocked, descriptive
  p-values note, future root, budgets, claim ceiling); `tasks.md` shows
  D1201+D1202 `[x]`, D1203–D1210 `[ ]` packet-exact.
- D1202: six D12 degree cells recomputed from the accepted D9 rule and matching
  the packet table EXACTLY (rule + arithmetic per cell recorded in `design.md`);
  exact import map with `path:line` for the R2 shared
  constructor/admission/coeff/decoder path, the R3 plan/seed/block pattern, the
  Model-F L1 prior chain, and the v35 row-layered decoder contract; explicit
  duplicate-framework/message-semantics rejection; seed/root absence scan raw
  output recorded with no collision. Any mismatch → STOP with BLOCKED + raw
  evidence (packet STOP: D9 table mismatch).
- D1203–D1210 remain `[ ]`, packet-exact, for successor execution.
- Zero scientific calls; zero decoder calls; no root created; no commit/push.
- STOP on requirement ambiguity, D9 table mismatch, seed drift, admission
  failure, need for replacement/search, decoder/scientific entry, root
  creation, failed review or conflicting dirty edits.

## Tasks

See `tasks.md`: D1201+D1202 `[x]` (this change), D1203–D1210 `[ ]`
packet-exact for successors. If any task cannot be clearly specified, flag it
as needing exploration (`/opsx-explore`); no task here is small enough to
implement directly outside the frozen pipeline.
