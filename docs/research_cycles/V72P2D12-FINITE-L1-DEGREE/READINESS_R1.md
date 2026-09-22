# D12 finite L1 degree refinement — readiness record R1 (no execution)

Cycle: `V72P2D12-FINITE-L1-DEGREE` (successor refinement; NOT a correction of any predecessor).
Authority: `.workbuddy/tasks/D12_FINITE_L1_DEGREE_REFINEMENT_READINESS_TASK_PACKET.md` §1–§4 (frozen, sole authority).
Track: implementation/readiness (zero scientific calls; no D12 batch, no L2, no D7-H, no real data, no commit/push).
The future batch (if ever authorized separately) is `EXPLORE_HEAVY`.
Branch: `formal-ir-v72p1-addendum-clean` (confirmed, no switch).
This call (D1210B): documentation-only — two new record files in this directory
(`READINESS_R1.md`, `EXPLORATION_LOG.md`), one pointer append to the D11 log, and the
D1210 checkbox update in the D12 OpenSpec `tasks.md`. No code edit, no D12 execution,
no decoder or scientific call, no root creation, no commit, no push.

Predecessor (immutable, read-only context, never pooled into D12):
`D11_FORWARD_APP_WIDE_RECOVERY_ACCEPTED_ROUTE_TO_D12_L1_REFINEMENT`
(machine terminal `D11_FORWARD_APP_WIDE_RECOVERY`, VERIFIED PASS_WITH_FINDINGS;
root `workspace/d11_forward_app_7c1878b5-23a8-4fd8-a395-b5a33a58ea64`).
A1/R3/D11 evidence is contextual only and SHALL never enter D12 gate arithmetic.

## Frozen design summary (packet §2, transcribed)

L1-only, f1.2, widths n128 and n256, both always measured. Six fresh graph seeds and
12 fresh paired block seeds per width:

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

Shared contract (only forced degree counts differ; no replacement/search/adaptation):
accepted shared connectivity-first constructor `build_degree_sequence_peg`, A1–A6
admission before decoder binding, frozen coefficient rule
(`COEFF_SEED = v10_seed(f"d10:coeff:{width}:{graph_seed}")`), Model-F CAL-only L1
prior chain, GF32/poly37, decoder `max_iter=90` / `damping_alpha=1.0` / cold.

Plan: 3 arms × 6 graphs × 12 blocks × 2 widths = 432 L1 call identities. Exact is
primary; syndrome-valid and undetected remain separate. Report per-graph, per-width
and pooled paired discordances.

Gates: an arm is `STABLE(w)` when exact ≥18/72, at least 5/6 graphs have ≥2 exact,
and no engineering/resource violation (L045 frozen reference). A challenger is
`MATERIAL_BETTER` only if, at both widths: it is STABLE; exact is at least L045+6;
pooled challenger-only discordance exceeds L045-only; and it has higher per-graph
exact on at least 4/6 graph pairs. Selection: exactly one MATERIAL_BETTER → select
it; both → rank by total exact, then worst-width exact, then smaller λ2; neither
with no split-width conflict → retain L045; `SPLIT_WIDTH_CONFLICT` when a challenger
beats L045 by ≥6 at one width but trails by >2 at the other, or widths favor opposing
challengers. Terminals: `D12_SELECT_L050`, `D12_SELECT_L055`,
`D12_RETAIN_L045_NO_MATERIAL_GAIN`, `D12_FINITE_DEGREE_SPLIT_AMBIGUOUS`, or an
explicit engineering/resource blocked terminal. Descriptive p-values do not override
the frozen selection.

Future root:
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`.
Budgets: ≤432 scientific calls; ≤62 setup (=36 graphs + 24 block samples + 2);
≤1800 s wall; ≤120 s/call; RSS <2147483648 B; one process; no retry/resume/repair/
seed search/tuning.

Claim ceiling: synthetic finite L1 degree comparison only; no forward/L2,
FER/leakage/SKR, real-data, qualification, optimality or D7-H claim.

## D1201–D1210 readiness table (trusted evidence, not rerun here)

| Task | Evidence |
|---|---|
| D1201 | OpenSpec change `v72p2d12-finite-l1-degree` (4 files: `proposal.md`, `design.md`, `tasks.md`, `specs/finite-l1-degree/spec.md`) with packet §2 frozen verbatim, before behavior edits. |
| D1202 | D9 exact realization audit + D10 R2/R3 construction, prior and decoder path import map; no duplicate framework or message semantics. |
| D1203 | Thin additive plan/runner/verifier (3 new code files + R2/R3 reuse) with frozen tables, seeds, 432 identities, gates, ranking and terminals. |
| D1204 | Default-false explicit execution flag; unauthorized refusal (exit 2) before root creation, decoder binding or Model-F load. |
| D1205 | All 36 graphs A1–A6 enforced before decoder binding; zero replacements. |
| D1206 | Never-overwrite minimal root and fail-closed verifier independently recomputing identities, metrics, gates/rank and terminal. |
| D1207 | Focused tests (exact tables, seed separation, shared construction, all gate/tie/split boundaries, exact/syndrome/undetected isolation, budgets, no-write refusal, verifier; decoder entry fake-injected only). |
| D1208 | `py_compile` PASS plus focused D12 (26/26) and directly affected D10 R2/R3 (41/41 = 18+23) tests in fresh basetemps. |
| D1209 | PROFILE_ONLY all 36 graphs + full plan: 36/36 A1–A6 admitted, zero replacements, deterministic replay identical (wall ~2.35 s), future root absent, decoder calls 0. |
| D1210 | Independent reviewer-go readiness review `D12-R1210`: `EVIDENCE_ACCESS VERIFIED`, `VERDICT PASS`, BLOCKING none (detail below). |

## D1210 verdict/findings (trusted VERIFIED, not rerun)

- `REVIEW_ID D12-R1210`, `EVIDENCE_ACCESS VERIFIED`, `VERDICT PASS`, BLOCKING none.
- PASS degree math: all six cells independently recomputed from the D9 rule
  (L045 71/57/313 `2^41+3^77` + 141/115/627 `2^81+3^155`; L050 77/51/307
  `2^47+3^71` + 154/102/614 `2^94+3^142`; L055 83/45/301 `2^53+3^65` +
  166/90/602 `2^106+3^130`); socket balance holds; min check degree 2, max 3.
- PASS admission: 36/36 A1–A6 admitted, zero replacements, replay identical
  (wall ~2.38 s); n128 comp1/118/118/4cyc0/girth6–10; n256 comp1/236/236;
  L050-2026093101 4cyc1/girth4 retained (diagnostics-only per spec); L055 girth
  ≤14; own-code recompute 0 fails.
- PASS isolation: one shared builder (forced counts only differ); `dispatch_l1`
  is R2 `dispatch_l1`; exact/syndrome separate; D12 tallies exact-only +
  `batch_id` gate (R3-like/wrong-tag refused); D11/A1/R3 unpoolable.
- PASS gates: STABLE / MATERIAL 4-clause / ranking / retain / SPLIT / five
  terminals / engineering-override, all edges including ties verified; McNemar
  descriptive-only.
- PASS budgets: 432/62/1800/120/2GiB/1-proc/no-retry in code + spec; refusal
  exit 2 pre-root/bind/Model-F (reviewer ran it); `py_compile` PASS.
- PASS no-production: zero v35 import in module (lazy post-auth only); D11 root
  untouched; scoped additive-only; decoder/scientific calls 0.
- TEST_RERUN: D12 26/26 + R2/R3 41/41 (18+23) in reviewer basetemps; total 67.
- Non-blocking: (a) broad dirty worktree (reconfirm at execution preflight);
  (b) "41" label = 18+23; (c) wall gate applies at execution.
- Recommendation: `D12_FINITE_L1_DEGREE_READY_AWAITING_EXPLICIT_AUTHORIZATION`.

## Authorization state

- D12 execution authorized: false. D12 batch grant: none.
- Future root absent (verified this call; see verification below).
- Decoder calls 0; scientific calls 0; no commit/push.
- This readiness record grants no execution.

## Terminal

- `D12_FINITE_L1_DEGREE_READY_AWAITING_EXPLICIT_AUTHORIZATION` (grants no execution).
- Preflight note: broad dirty worktree was noted non-blocking by the reviewer;
  execution preflight must reconfirm the tree state before any batch grant is consumed.

## Next gate

A separate explicit batch grant naming batch/branch/root/seeds/budgets is required
before any D12 execution. No authorization was granted by readiness or by the R1210
review.

## Claim boundary

Synthetic finite L1 degree comparison only. No forward/L2, FER/leakage/SKR,
real-data, qualification, optimality, promotion, publication or D7-H claim is made
or implied by this readiness record.

## 2026-09-14 — main-thread readiness acceptance

`D12_FINITE_L1_DEGREE_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.
The independent `D12-R1210` VERIFIED/PASS review is accepted without repeating
its 67 tests or recomputations. The single four-cycle/girth-4 graph remains an
accepted diagnostic-only frozen cell; it must not be replaced. The dirty-tree
note is carried to execution preflight. This accepts readiness only and grants
no execution. Next packet:
`.workbuddy/tasks/D12_FINITE_L1_DEGREE_BATCH_A1_TASK_PACKET.md`.
