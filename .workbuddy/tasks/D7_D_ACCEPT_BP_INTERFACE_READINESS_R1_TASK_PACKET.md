# D7-D bounded acceptance + BP provenance interface readiness R1

Status: `MAIN_THREAD_FROZEN_HEAVY_PACKET_R1` (zero claim-bearing execution)

## 0. Main-thread ruling

Accept the reviewed D7-D run only as:

`D7_D_RESULT_ACCEPTED_SCHEDULE_EFFECT_INCONCLUSIVE`

The accepted facts are limited to the single UUID
`64660d16-397d-4ef3-8454-3066d27c12c7`: 256/256 paired calls completed;
row-layered exact `43/128`, flooding exact `40/128`, layered-only `3`,
flooding-only `0`, both `40`, neither `85`; no crash/nonfinite/watchdog;
stored terminal `D7_D_SCHEDULE_EFFECT_INCONCLUSIVE`; independent Pre-RESULT
`D7_D_PRE_RESULT_REVIEW_PASS_R1`; budgets passed.

Interpretation boundary:

- the frozen matrix establishes no preregistered flooding or layered advantage;
- `43 vs 40` and three layered-only pairs are reported, not promoted into a
  schedule-superiority claim;
- schedule choice is not supported as the dominant explanation of the current
  failures;
- D7-C's accepted bidirectional oracle dependence remains the stronger route
  evidence, but it does not prove that alternating/joint BP can bootstrap;
- no FER, leakage, key rate, qualification, promotion, general schedule
  equivalence or general NB-LDPC conclusion;
- R1d becomes `PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE`; it is not
  authorized or executed here;
- G1/G2 remain unauthorized; old D5/D6 checkboxes are historical accounting,
  not mandatory gates to future dimension generalization.

The next mainline action is Alternative A of the accepted layer-interface
proposal: explicit belief provenance plus fail-closed cross-layer consumers.
No forced extra sweep (Alternative B), warm-start mechanism, alternating/joint
decoder or scientific decoder run is authorized by this packet.

## 1. Baseline and hard boundaries

- Repository `HD-QKD_Polar_Comparison`; branch
  `formal-ir-v72p1-addendum-clean`.
- Expected entry HEAD `63a69f5767da` (accept the full resolved SHA from Git).
- D7-D result commit `63a69f57`, revocation `eba385bb`, authorization
  `7a3f0d92`; current gate `INDEPENDENT_D7_D_RESULT_ACCEPTANCE_R1`;
  `d7d_execution_authorized: false`, decoder/result true, Pre-RESULT PASS.
- D7-D/D7-C/D7-B/Model-F/G0/P0/G1/D6/structure/VOID evidence roots are
  immutable. Inspect only names/sizes/mtime unless a frozen review explicitly
  requires the D7-D result scalar files.
- No decoder invocation, no `--phase`, R1d, G1/G2, Model-F/CAL/VAL/parquet/
  real/raw/VOID-content read, scientific UUID, result root or push.
- Tiny in-memory unit/oracle fixtures are allowed; production decoder functions
  may run only on explicit tiny synthetic test fixtures. Tests must never bind
  a real artifact, formal root or production execution path.
- Preserve unrelated dirty files and CRLF churn. No clean/reset/checkout/stash/
  rebase/amend/broad stage. Every commit uses an explicit path allowlist.
- Read every file before editing. OpenSpec behavior changes precede code.

Only two returns: all A01-A20 complete, or a concrete blocker that changes the
frozen scientific/interface contract. Ordinary implementation choices, test
repairs within scope and long runtimes are delegated to the operator.

## 2. Phase A — independently verify and accept D7-D (A01-A04)

### A01 — result verification

Independently read the frozen packet, prereg, seven scalar files, operator
return and Pre-RESULT review. Recompute at minimum:

- 256 unique calls and 128 exact schedule pairs;
- all non-schedule inputs pair-identical;
- exact/syndrome isolation and `3/0/40/85` pairing;
- eight stratum labels;
- T1-T10 terminal replay;
- iterations/node/edge work arithmetic;
- 120/1500/1800+30 wall and `<2GiB` RSS gates;
- root immutability and all authorization false.

Any discrepancy with §0 is STOP. Do not repair artifacts.

### A02 — acceptance document

Create:

`docs/research_cycles/V72P2D7-GF32-SCHEDULE-DISCRIMINATOR/D7_D_RESULT_ACCEPTANCE_R1.md`

It must reproduce §0, the paired table, eight strata, resource facts, supported
and unsupported claims, and explicitly state that INCONCLUSIVE has no frozen
automatic successor; this main-thread ruling selects BP provenance next.

### A03 — D7-D state

Update only factual acceptance fields in the D7-D `cycle_state.yaml`:

- `d7d_result_accepted: true`
- `d7d_accepted_scope: SCHEDULE_EFFECT_INCONCLUSIVE`
- acceptance document path
- `next_gate: BP_INTERFACE_PROVENANCE_IMPLEMENTATION`

Keep every authorization/promotion false. Do not alter stored terminal or run
facts.

### A04 — durable route decision

Append narrowly to `docs/decision-log.md` and `AGENT_PROJECT_MEMORY.md`:

- D7-D bounded acceptance and exact pair counts;
- no schedule-superiority claim;
- BP Alternative A is next;
- R1d is optional/paused, not a mainline gate;
- G2 remains unauthorized;
- dimension/bw expansion waits for a working provenance-safe fixed-dimension
  mechanism and, for more than two layers, a separate mathematical/leakage
  contract.

Commit Phase A exactly:

`docs(d7-d): accept inconclusive schedule discriminator and route to BP provenance`

## 3. Phase B — documentation authority reconciliation (A05-A08)

### A05 — CURRENT_MAINLINE

Replace the obsolete 2026-08-24 NB-LDPC status section of
`docs/CURRENT_MAINLINE.md` with a compact current route ledger through D7-D:

1. D5 fixed rate-mother path stopped within tested scope;
2. D6 graph/mother A2 structurally blocked; R1d Option C frozen but optional;
3. D7-A decoder certification PASS;
4. D7-B hard-decision easy region observed, with RSS/belief limitations;
5. D7-C bounded bidirectional dependence accepted;
6. D7-D schedule effect inconclusive;
7. active gate is BP provenance implementation;
8. after BP, freeze a provenance-safe cross-layer mechanism discriminator;
9. only then consider dimension/bw expansion.

Do not rewrite unrelated reporting/entrypoint/archive sections unless needed to
remove a direct contradiction. This document is status, not authorization.

### A06 — V35 conflict disposition

The uncommitted working-copy rewrite of
`docs/v35-algorithm-development-report.md` claiming
`NB_CANDIDATE_DEVELOPMENT_READY` is rejected. The authoritative content is the
committed corrected report at entry HEAD, whose bounded status includes
`NO_NB_CANDIDATE_FOR_TESTED_HAND_DESIGNED_CONFIGURATION` and
`PROTOCOL_PARTIAL_A4_NOT_EXECUTED`.

Record the rejected rewrite and reason in a short append to
`docs/troubleshooting.md`, then restore that report's content exactly to the
entry-HEAD version. Do not preserve the false numerical table as an active
report and do not create a backup framework. Verify its content diff is empty.

### A07 — checkbox semantics

Audit only active D7/D6/D5 OpenSpec changes. Update checkboxes only where direct
commit/artifact evidence proves completion. Do not turn stale unchecked tasks
into new work, and do not rewrite archived V62/V63/V64 histories merely to make
counts green. Add one short rule to `docs/CURRENT_MAINLINE.md`: active gate and
accepted cycle documents outrank aggregate checkbox counts; stale historical
checkboxes are bookkeeping, not execution authorization.

### A08 — documentation review and commit

An independent docs reviewer checks that no claim exceeds accepted evidence,
the V35 conflict is gone, D7-D execution is reflected, and no stale gate is
present. Create:

`docs/research_cycles/V72P2D7-GF32-SCHEDULE-DISCRIMINATOR/D7_D_MAINLINE_RECONCILIATION_REVIEW_R1.md`

Allowed verdict: `D7_D_MAINLINE_RECONCILIATION_REVIEW_PASS` or FAIL. PASS then
commit only reconciled docs/OpenSpec checkbox files and review:

`docs(nbldpc): reconcile authoritative mainline after D7-D`

FAIL stops before BP code.

## 4. Phase C — activate Alternative A OpenSpec (A09-A10)

Authoritative change:

`openspec/changes/v72p2d7-layer-interface-belief-provenance/`

### A09 — delta freeze

Update proposal/design/spec/tasks before code to record:

- D7-D accepted INCONCLUSIVE and does not change the provenance contract;
- exact enum remains `PRIOR_ONLY`, `CHECK_UPDATED`,
  `WARM_START_UNSPECIFIED`;
- missing/None/unknown provenance fails closed for conditioned cross-layer APP;
- Alternative A only; B remains a separate future scientific decision; C
  remains rejected;
- `CHECK_UPDATED` means a BP APP approximation incorporating check messages,
  not a calibrated exact posterior;
- no hard-decision stopping change and no historical result reinterpretation;
- the implementation subset in §5 and PV-01-PV-14 acceptance matrix;
- dormant historical v45-v55 paths must either carry the same fail-closed guard
  before future execution or be explicitly blocked at their cross-layer entry;
  they are not rerun here.

### A10 — implementation allowlist

Behavioral edits are limited to the minimum files required by BP-01-BP-05 and
tests, selected from:

- `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d3_gf32_contrast.py`
- `comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py`
- historical v45-v55 cross-layer consumer modules named in the accepted
  proposal, only for additive provenance propagation/fail-closed guards
- `scripts/execute_v64_fresh_verify.py`
- directly corresponding tests under `comparison_bench/tests/`

Do not touch frozen `src/`, `experiments/`, `tools/`, sibling
`nonbinary_v10_fftqspa.py`, D7-A/C/D scientific logic or any evidence root.

Commit OpenSpec delta before production code:

`docs(d7): activate belief-provenance Alternative A after D7-D`

## 5. Phase D — BP-01 through BP-08 implementation (A11-A16)

### A11 — producer contract (BP-01)

- Append defaulted `belief_provenance: str | None = None` to `DecoderResult` so
  existing positional construction remains compatible.
- Cold row-layered iteration 0: `PRIOR_ONLY`.
- Cold row-layered after one or more completed sweeps: `CHECK_UPDATED`.
- Flooding returns: `CHECK_UPDATED`.
- Any warm-seeded return without explicit carried provenance:
  `WARM_START_UNSPECIFIED`; never infer it from iterations.
- Do not change `x_hat`, syndrome, iterations, status, beliefs, stopping,
  damping, normalization or numerical recurrence.

### A12 — active plumbing and fail-closed boundary (BP-02/BP-03)

Carry provenance through D5 `_decode_block` and all three adapter dicts without
removing or renaming existing keys. `_run_layered_block` may call
`app_fed_l2_prior` only when L1 provenance is exactly `CHECK_UPDATED`.
`PRIOR_ONLY`, missing, None, unknown and `WARM_START_UNSPECIFIED` must raise a
specific fail-closed error before L2 prior construction or L2 decode.

### A13 — remaining consumers (BP-04)

Migrate the live/likely reusable cross-layer boundaries in `v72p2d3`, shell
adapter and V64 runner. For historical v45-v55 modules, use the smallest
scientifically honest treatment: additive propagation/guard where localized;
if safe migration would alter a frozen historical contract, add a direct
fail-closed execution guard and document that future reactivation needs its own
OpenSpec. Never recompute or reinterpret historical outputs.

### A14 — labels and warm-start boundary (BP-05/BP-06)

Future diagnostics must label iteration-zero belief comparisons as
`PRIOR_ONLY_CURRENT_BELIEF`; hard-decision success and belief calibration stay
separate. Do not implement forced sweep or warm-start propagation. Preserve
`WARM_START_UNSPECIFIED` as a refusal token for conditioned cross-layer APP.

### A15 — tests PV-01-PV-14

Implement every frozen PV test, including:

- exact producer token mapping and warm-start negative;
- hard-decision/numerical byte-for-byte or array-exact equivalence on frozen
  tiny fixtures except the additive field;
- missing/None/unknown/prior-only refusal before mixer and L2 decoder spies;
- CHECK_UPDATED pass-through reproducing the previous q-at-P calculation;
- adapter propagation and dormant-entry fail-closed behavior;
- D7-B labeling separation without rerunning D7-B;
- D7-C import-graph independence;
- no real root/artifact reads and no production execution from tests.

Add a static inventory test that fails if a production `final_beliefs` to
cross-layer mixer path lacks explicit provenance handling. Keep it narrowly
focused on the accepted inventory; do not build a generic policy framework.

### A16 — test tiers

Run separately, with fresh task-owned basetemps and `-p no:cacheprovider`:

1. py_compile/import and focused BP/PV tests;
2. affected v35/D5/v72p2d3/shell/V64 tests;
3. D7-A/B/C/D regression relevant to decoder/interface independence;
4. one milestone suite covering the established D5-D7 files.

Known stale root-absence tests must be converted only if they are in affected
scope, using lifecycle-aware snapshot invariance; never skip/xFAIL/delete for
green. A pre-existing unrelated failure may be isolated only with exact ID and
proof it existed before this code.

Commit code and tests only after all required tests pass:

`feat(d7): add fail-closed belief provenance for cross-layer APP`

## 6. Phase E — independent reviews and closeout (A17-A20)

### A17 — independent implementation review

Reviewer must not edit. Create
`D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_R1.md` under the D7-B cycle directory.
Independently inspect every producer return, every active consumer, PV-01-PV-14,
inventory coverage, numerical equivalence, no-retroactivity and D7-C/D7-D
independence. Verdict only:

- `D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_PASS`
- `D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_FAIL`

One scoped code rework is allowed on FAIL, followed by a fresh review; no
scientific execution.

### A18 — readiness review

After implementation PASS, a separate reviewer creates
`D7_BP_INTERFACE_READINESS_REVIEW_R1.md`. It verifies:

- Alternative A exactly, B/C absent;
- no hard-decision/numerical/stopping drift;
- all cross-layer entrypoints fail closed unless `CHECK_UPDATED`;
- warm-start refusal;
- no real artifacts/decoder run;
- tests and protected roots;
- R1d/G1/G2 remain unauthorized;
- next scientific work requires a new prereg/packet and explicit authorization.

Verdict only `D7_BP_INTERFACE_READINESS_REVIEW_PASS` or FAIL.

### A19 — final state and roadmap

On both PASS verdicts:

- mark BP-01-BP-05, BP-07 and BP-08 complete; BP-06 complete only as a frozen
  non-implementation boundary (`WARM_START_DEFERRED`);
- update the D7-B interface cycle state or create a minimal dedicated state if
  none exists: implementation accepted, reviews PASS, all execution authority
  false;
- set the authoritative route to
  `D7_E_PROVENANCE_SAFE_CROSS_LAYER_DISCRIMINATOR_PACKET_FREEZE`;
- append factual completion to decision-log and memory;
- state that R1d remains optional/paused and D7-E is not yet frozen or
  authorized.

### A20 — closeout commit and return

Commit only review/closeout/docs/state files:

`docs(d7): accept BP provenance readiness and open D7-E packet freeze`

No D7-E implementation or execution in this packet. No push.

Report delta only:

1. A01-A20 table;
2. D7-D accepted scope and exact route inference;
3. documentation/V35 disposition and authoritative gate;
4. BP producer/consumer file manifest and enum mapping;
5. PV-01-PV-14 plus tiered literal test summaries;
6. independent review verdicts;
7. commit SHAs and scoped manifests;
8. protected-root equality/auth/no-push;
9. remaining limitations and next gate.

Success ending:

`D7-D 已按“schedule effect inconclusive”受限接受；权威主线与 V35 冲突已收口，BP-01…BP-08 Alternative A provenance 接口已实现并通过独立评审；下一门为 D7-E provenance-safe cross-layer discriminator 包冻结，R1d 继续可选暂停，G1/G2 均未授权。`

Blocker ending:

`STOP — D7-D/BP 收口包命中具体 blocker；未跨越失败门、未执行任何科学任务，正式根与授权状态保持不变。`
