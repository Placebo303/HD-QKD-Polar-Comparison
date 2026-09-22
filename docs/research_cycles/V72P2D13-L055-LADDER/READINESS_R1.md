# D13 L055 failure decoder ladder — readiness record R1 (no execution)

Cycle: `V72P2D13-L055-LADDER` (decoder-dynamics diagnostic on frozen D12 failures; NOT a correction of any predecessor).
Authority: `.workbuddy/tasks/D13_L055_FAILURE_DECODER_LADDER_READINESS_TASK_PACKET.md` §1–§4 (frozen, sole authority).
Track: implementation/readiness (zero scientific calls; no D13 execution, no decoder calls, no root creation, no L2/D7-H, no real data, no commit/push).
The future batch (if ever authorized separately) is `EXPLORE`.
Branch: `formal-ir-v72p1-addendum-clean` (confirmed, no switch).
This call (D1310B): documentation-only — two new record files in this directory
(`READINESS_R1.md`, `EXPLORATION_LOG.md`), one pointer append to the D12 log, and the
D1304–D1310 checkbox update in the D13 OpenSpec `tasks.md`. No code edit, no D13 execution,
no decoder or scientific call, no root creation, no commit, no push.

Predecessor (immutable, read-only context, successes never enter the ladder):
`D12_L055_ACCEPTED_ROUTE_TO_D13_DECODER_LADDER`
(machine terminal `D12_SELECT_L055`, VERIFIED PASS_WITH_FINDINGS;
root `workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`, unmodified —
sizes/mtimes unchanged). The 88 L055 successes are excluded by construction.

## Frozen diagnostic summary (packet §2, transcribed)

Input root (read-only):
`workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`.
Select exactly its L055 records with `arm == L055 AND exact == false`:
30 at n128 (per-graph 5/5/7/4/5/4) and 26 at n256 (per-graph 5/3/5/4/4/5) = 56 total.
Every selected record: `iterations == 90`, `syndrome_ok == False`,
`converged_no_syndrome`, `CHECK_UPDATED` provenance; undetected 0.
Preserve graph/block identities, degree tables, coefficients, Model-F prior,
GF32/poly37 and cold initialization. No successful D12 record enters the ladder.

Reconstruct each input and first replay `ROW_LAYERED_90_ALPHA_1`. Every replay
must match the stored baseline fields relevant to exact, syndrome, iterations,
provenance and failure identity (`selection_identities == FROZEN_IDENTITY_SET`,
`validate_selection` empty). First mismatch blocks all ladder calls.

Then run exactly these three arms on every selected failure:

1. `ROW_LAYERED_360_ALPHA_1`;
2. `ROW_LAYERED_360_ALPHA_0_7`;
3. `FLOODING_360_ALPHA_1`.

Audit and reuse existing D7-X3 row-layered/flooding binders and D12 reconstruction;
do not implement another decoder. RL360 = row-layered with `max_iter` 360;
damping-0.7 is an existing tunable parameter only (NOT tuned); flooding-360 is the
accepted target (no damping by design). CHECK_UPDATED provenance is mandatory.
Exact, syndrome-valid and undetected remain separate (`is_rescue = exact AND
syndrome AND CHECK_UPDATED`). Total scientific ceiling:
56 baseline replay + 56×3 ladder = 224 calls.

Rescue gates per ladder arm (counts by width and total):
`MATERIAL_RESCUE` = total ≥12 and ≥4 at each width;
`MODEST_RESCUE` = total 3–11 with at least one rescue at each width;
`NO_RESCUE` = total ≤2; other asymmetric results are `RESCUE_AMBIGUOUS`.
Ranking (multiple MATERIAL arms): total rescues, then worst-width rescues,
then mean iterations among rescues, then fixed arm order above.
Non-material arms never rank.

Terminals: `D13_SELECT_RL360`, `D13_SELECT_RL360_DAMP07`,
`D13_SELECT_FLOOD360`, `D13_MODEST_DECODER_RESCUE`,
`D13_NO_MATERIAL_DECODER_RESCUE`, `D13_DECODER_RESCUE_AMBIGUOUS`, or explicit
engineering/resource blocked (`T_ENGINEERING_BLOCKED` has priority).
A selected arm requires MATERIAL_RESCUE.

Future root:
`workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`
(absent verified, before and after).
Budgets: ≤224 scientific calls; ≤8 setup; ≤1800 s wall; ≤120 s/call;
RSS <2147483648 B; one process; no retry/resume/repair/seed search/tuning.

Claim ceiling: frozen synthetic L1 decoder diagnostic only; no ensemble
optimality, forward/L2, FER/leakage/SKR, real data, D7-H or qualification.

## D1301–D1310 evidence table

| ID | Status | Evidence |
|---|---|---|
| D1301 | [x] | OpenSpec change `v72p2d13-l055-decoder-ladder` (4 files: `proposal.md`, `design.md`, `tasks.md`, `specs/l055-decoder-ladder/spec.md`) with packet §2 frozen verbatim, before behavior edits. |
| D1302 | [x] | Selector predicate `arm == L055 AND exact == false` over D12 `decoder_records.csv`, own CSV recompute → 56 (n128 30, n256 26); all `iterations == 90`, `syndrome_ok == False`, `converged_no_syndrome`, `CHECK_UPDATED`; undetected 0; three-source corroboration (`arm_summary.csv` pooled 42/72 n128 + 46/72 n256, `summary.json` pools, direct row audit); `selection_identities == FROZEN_IDENTITY_SET`, `validate_selection` empty. |
| D1303 | [x] | Semantic map (`path:line`) + duplication rejection in `design.md` §4: D12 `build_graph` + R2 construction/admission/coeff/prior/dispatch-cold path, R2-runner prior/block loaders, D12 production decoder bind, accepted D7-E RL90 binder + D7-D schedule RL90/flooding-90 binder; RL360 via parametrizable `max_iter`, damping-0.7 existing param (NOT tuned), flooding-360 accepted target, CHECK_UPDATED provenance. All required binders accepted. |
| D1304 | [x] | Thin additive selector/replay/ladder/gate/verifier (`comparison_bench/src/comparison_bench/formal_ir/v72p2d13_l055_decoder_ladder.py` + `scripts/v72p2d13_development.py` runner, D12/X3 reuse, no decoder duplication); plan built before any binding; `compare_replay` checks identity+exact+syndrome+iterations+mandatory-CHECK_UPDATED; first replay mismatch stops later calls (break + blocked gate). |
| D1305 | [x] | Explicit default-false CLI execution flag; refusal (rc=2) fires before root creation, decoder binding or Model-F load; refusal path verified. |
| D1306 | [x] | Fresh never-overwrite minimal future root; verifier independently checks selection, replay, calls, rescues, ranking, terminal and budgets; schedule-pair and provenance emissions confirmed. |
| D1307 | [x] | 16 focused fake tests (`comparison_bench/tests/test_v72p2d13_l055_decoder_ladder.py`): exact selection, exclusion of successes, 56+168 accounting, first-mismatch stop, provenance, all rescue boundaries (MATERIAL/MODEST/NO/AMBIGUOUS incl. asymmetric cases + ties), ranking (total→worst-width→mean-iter→fixed-order), exact/syndrome/undetected isolation, unauthorized refusal. 16/16 PASS in own basetemp. |
| D1308 | [x] | `py_compile` 3/3 PASS; D13 16/16 PASS in fresh workspace basetemp; broad suites declined per trust rule (D12+X3 combined 88+8 failure adjudicated PLAUSIBLE pre-existing/environmental — 7 leftover `workspace/d7_*` dirs + v35 order pollution — not D13-attributable). |
| D1309 | [x] | PLAN_ONLY reconstruction metadata for all 56 with zero decoder calls (×2 runs, rc=0, byte-identical, 56 identities, plan 224, decoder 0); input root unchanged; future root absent before and after. |
| D1310 | [x] | Independent reviewer-go readiness review, `EVIDENCE_ACCESS: VERIFIED`, VERDICT PASS_WITH_FINDINGS, BLOCKING none (this record). Recomputed selection, frozen replay contract, decoder bindings (RL90, RL360, damping-0.7-as-existing, flooding-360), gates/rank, budgets (224/8/1800/120/2GiB/1-proc/no-retry) and no-production boundary (`v35` absent from `sys.modules` after import/plan/refusal; D12 sizes/mtimes unchanged; future root absent). Non-blocking: (a) D1304–D1310 checkboxes flipped in this docs-only call after acceptance; (b) broad dirty worktree preserved, noted for awareness; (c) D13 refusal test vacuous second clause — test-isolation debt, same family as prior cycles. |

## Authorization state

- D13 execution authorized: **false**.
- Decoder calls made: **0**. Scientific calls made: **0**.
- Future root `workspace/d13_l055_decoder_ladder_5c41b416-cacc-4b6e-892e-d8a59c53170e`: **absent**.
- Commit/push performed: **none**.

## Terminal

`D13_L055_DECODER_LADDER_READY_AWAITING_EXPLICIT_AUTHORIZATION`

## Next gate

The D13 batch requires a separate explicit batch grant naming batch/branch/root,
seeds and budgets. Readiness and the R1310 review grant no authorization.
D7-H, L2 and real data remain out of scope.

## Main-thread readiness acceptance — 2026-09-14

Main-thread review accepts D1301–D1310 and the independent `D13-R1310`
`EVIDENCE_ACCESS: VERIFIED` / `PASS_WITH_FINDINGS` verdict. The three findings
are non-blocking and remain carried to the batch-end review; the unrelated
D12+X3 environmental failures are not a D13 gate and shall not be rerun merely
for ceremony.

Accepted terminal:
`D13_L055_DECODER_LADDER_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION`.

This acceptance freezes readiness only. It does not authorize execution,
change the 56-instance selector, tune a decoder, revive D7-H, or make any L2,
FER, leakage, SKR, real-data, qualification, or optimality claim.

## Claim boundary

Frozen synthetic L1 decoder diagnostic only (≤224 calls on the 56 frozen L055
failures). No ensemble-optimality, forward-app, FER/leakage/SKR, real-data,
D7-H or qualification claim is authorized by this record.
