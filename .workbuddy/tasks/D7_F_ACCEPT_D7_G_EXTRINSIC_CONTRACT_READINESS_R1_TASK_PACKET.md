# D7-F Acceptance + D7-G Extrinsic Contract Readiness R1

## 0. Objective

Execute a substantial zero-production-run milestone:

1. Independently accept D7-F under a narrow reverse-order-regression diagnostic scope.
2. Specify and certify a code-factor extrinsic-message contract that can support future alternating cross-layer BP without returning a layer's incoming evidence back to itself.
3. Implement the smallest backwards-compatible decoder/interface support, tests, and independent reviews.
4. Stop at `D7_G_EXTRINSIC_CONTRACT_ACCEPTED_AWAITING_D7_H_PACKET_FREEZE`.

No D7-G/H scientific experiment is authorized. Tiny in-memory certification calls are allowed; Model-F/CAL/VAL/real artifacts are not.

## 1. Main-thread rulings

### 1.1 D7-F acceptance

Accept only as:

`D7_F_RESULT_ACCEPTED_REVERSE_ORDER_REGRESSION_DIAGNOSTIC`

Accepted facts:

- 128/128 calls completed with zero blocked/retry/crash/nonfinite/watchdog;
- `f=1.0`: forward and reverse both-layer exact `0/16`;
- `f=1.2`: forward both-layer exact `2/16` (seeds 1302/1304), reverse `0/16`;
- reverse-vs-forward table `candidate_only=0`, `reference_only=2`, `both=0`, `neither=14`;
- forward source exact 3 and target exact 3 overlap on only 2 identities;
- reverse source L2 exact 0 while target L1 exact 7, so target lift does not produce joint recovery;
- terminal `D7_F_REVERSE_ORDER_REGRESSION` is internally consistent.

Permitted inference: reversing a single sequential pass does not convert D7-E's directional target lift into complete two-layer recovery under this frozen synthetic contract.

Forbidden inference: L2→L1 transfer is useless, alternating cannot work, general NB-LDPC failure, FER/leakage/key rate, qualification, or R1d/G1/G2 permission.

### 1.2 D7-G mathematical contract

Treat each layer decoder as a component factor in a factor graph. For a cold decoder with normalized positive input prior `p_in(x)` and final log belief `L_post(x)`, define the outgoing code-factor extrinsic message only up to a per-symbol-variable additive constant:

`L_code_ext(x) = L_post(x) - log(p_in(x))`.

Normalize for transport with stable softmax. This removes the entire incoming prior—including channel and cross-layer evidence—from the outgoing message, leaving only the decoder's accumulated parity-check evidence under its BP recurrence.

Contract boundaries:

- It is a BP factor message, not a calibrated exact posterior and not MAP truth.
- Valid only for cold start after at least one completed check sweep and finite shape-correct beliefs.
- Iteration 0 emits no usable check evidence: neutral zeros plus provenance `NO_CHECK_EVIDENCE`, and is ineligible for cross-layer transfer.
- Warm-start extrinsic remains `WARM_START_UNSPECIFIED` and fail-closed.
- Existing `final_beliefs` and `belief_provenance` semantics remain unchanged for current consumers.
- No consumer may infer extrinsic by subtracting an unknown/reconstructed prior; the decoder result must carry an explicit optional extrinsic field and provenance.
- No multi-round alternating execution is allowed until this contract passes independent certification.

## 2. Preconditions

- Branch `formal-ir-v72p1-addendum-clean`.
- D7-F result commit `8e3bdbee` and authorization/revocation commits are ancestors in order.
- D7-F state: attempts/completed `1/1`, auth false, terminal `D7_F_REVERSE_ORDER_REGRESSION`, Pre-RESULT PASS, result accepted false, next gate result acceptance.
- D7-F root immutable; D7-E and protected roots unchanged; R1d/G2 absent; all auth/promotion false.

Mismatch → STOP without repair.

## 3. Hard prohibitions

- No D7-F rerun/verify and no D7-G/H production/scientific run.
- No Model-F, CAL, VAL, real/raw, VOID, R1d, `--phase`, formal G1/G2.
- No tuning of code, graph, mother, rows, estimator, damping, iterations, thresholds, schedules, or seeds.
- No joint decoder, alternating experiment, performance sweep, warm-start activation, or persisted beliefs/messages.
- Do not alter accepted result roots or frozen baseline `src/`, `experiments/`, `tools/`.
- No push, broad stage, reset, checkout, clean, stash, rebase, or amend.
- If exact extrinsic semantics cannot be certified independently, STOP; do not weaken tolerances or rename posterior as extrinsic.

## 4. Phase A — D7-F acceptance

Independently recompute the two per-f paired tables, source/target overlap, labels, terminal, resources, verifier transcript, and lifecycle from committed scalar artifacts.

Create `D7_F_RESULT_ACCEPTANCE_R1.md` with the exact accepted label/facts/inference ceiling in §1.1. Update D7-F state acceptance fields and route to `D7_G_EXTRINSIC_CONTRACT_PROPOSAL`. Append narrow accepted facts to decision-log/memory. Keep every authorization false. Commit separately.

## 5. Phase B — OpenSpec and certification preregistration

Create OpenSpec change `v72p2d7-code-factor-extrinsic-contract` and cycle directory `V72P2D7-GF32-EXTRINSIC-CONTRACT`.

Before implementation, freeze:

- exact formulas and normalization conventions;
- enum values `NO_CHECK_EVIDENCE`, `CHECK_EXTRINSIC`, `WARM_START_UNSPECIFIED`;
- optional result fields `extrinsic_log_beliefs` and `extrinsic_provenance` (names may change only if an existing project convention makes them impossible; otherwise fixed);
- no persistence rule;
- cold/iteration-0/warm behavior;
- direct-enumeration and independent-recurrence certification matrices;
- tolerances no looser than existing D7-A numerical certification unless justified before results;
- compatibility and consumer migration rules;
- D7-H remains not frozen/not authorized.

Commit preregistration/OpenSpec before behavior implementation.

## 6. Phase C — smallest backwards-compatible implementation

### C01 producer

Extend the Comparison-owned decoder result and row-layered cold path to return explicit check-extrinsic log messages:

- after ≥1 complete sweep: `final_beliefs - normalized_log_input_prior`, row-normalized by subtracting log-sum-exp or max as frozen;
- iteration 0: neutral zero matrix, provenance `NO_CHECK_EVIDENCE`;
- warm start: no usable extrinsic, provenance `WARM_START_UNSPECIFIED`;
- nonfinite/shape mismatch: fail-loud or ineligible, never silently repaired.

Do not change hard decisions, stopping, iteration counts, `final_beliefs`, existing provenance, decoder numerics, or current return behavior beyond additive optional fields.

If the implementation cannot recover the exact normalized input prior used internally without duplicating numerical cleaning rules, refactor that normalization once and prove byte/numeric equivalence; do not reimplement it inconsistently.

### C02 interface helpers

Add a narrow helper that accepts only explicit `CHECK_EXTRINSIC`, softmaxes it stably, and rejects `NO_CHECK_EVIDENCE`, warm/unknown provenance, missing arrays, wrong shapes, or nonfinite values.

Do not wire this helper into D5/D6/D7 production execution yet. Existing posterior-based one-pass D7-E/F behavior remains immutable.

### C03 flooding scope

Row-layered is mandatory. Flooding may receive the same additive fields only if this is necessary to keep `DecoderResult` construction coherent and can be certified cheaply; otherwise mark flooding extrinsic `DEFERRED` without changing its existing outputs. Do not broaden into a schedule project.

## 7. Phase D — independent scientific certification

Use a new independent oracle module that does not import the production check-update/extrinsic helper.

### D01 algebra and invariance

- scaling/normalization invariance of `p_in`;
- `softmax(L_post-log(p_in))` invariant to row constants;
- reconstruct `softmax(log(p_in)+L_code_ext)` and match `softmax(L_post)`;
- deterministic rejection of zeros/nonfinite/shape mismatch under frozen cleaning semantics.

### D02 exact tree factor-message oracle

For tiny GF32 degree-2/3 tree checks, enumerate assignments independently. Compare the normalized outgoing code-factor message for each variable against exact `P(syndrome constraints | x_i)` marginalized over other variables and their priors. Compare distributions, not only MAP.

Require multiple coefficients, nonzero syndromes, asymmetric priors, and negative direction/label controls.

### D03 loopy recurrence oracle

For a tiny loopy graph, compare emitted extrinsic after each of 1–3 complete row-layered sweeps against an independently coded recurrence's sum of check-to-variable messages. Do not compare loopy BP against exact MAP.

### D04 no-returned-evidence demonstration

Build a tiny two-layer tree factor graph with channel factor `P(U1,U2|B)` and two syndrome factors. Demonstrate:

1. posterior-based back-transfer double-counts the originating syndrome in a constructed counterexample;
2. explicit code-extrinsic transfer matches independent sum-product factor messages for one forward and one backward update within tolerance;
3. iteration-0 neutral extrinsic cannot create a false lift;
4. warm/unknown provenance is rejected.

This is the decisive certification. If no deterministic counterexample or exact match can be produced, STOP and return the mathematical ambiguity.

## 8. Phase E — tests and compatibility

Add tests covering:

- every new enum/field at all decoder return sites;
- cold iteration 0, cold ≥1, max-iter, exception/nonfinite, and warm paths;
- reconstruction identity and normalization;
- tree exact oracle and loopy independent recurrence;
- posterior double-count negative control;
- no-returned-evidence exact factor-graph match;
- helper rejection matrix;
- existing BP provenance guards unchanged;
- existing D7-E/F outputs and frozen roots untouched;
- current consumers compile and retain prior behavior;
- static inventory preventing cross-layer consumers from using explicit extrinsic without their own future OpenSpec.

Run focused certification, decoder/BP interface suite, D7-A certification, and one milestone regression. Tiny synthetic decoder calls only. Trust independent reviewer-go results; no duplicated full suite or perf-v38.

## 9. Phase F — independent reviews

### F01 mathematical/implementation review

Reviewer independently derives the factor-message formula, inspects the oracle's independence, reruns decisive tiny cases, and verifies no change to existing hard decisions/posteriors.

Unique verdict: `D7_G_EXTRINSIC_CONTRACT_REVIEW_PASS` or `...FAIL`.

### F02 integration-readiness review

After F01 PASS, independently confirm:

- API is additive/backwards compatible;
- all existing cross-layer consumers remain on their prior contracts;
- no D7-H runner/root/UUID/authorization exists;
- no scientific artifacts were read/written;
- a future D7-H can consume only explicit `CHECK_EXTRINSIC` and cannot use posterior fallback.

Unique verdict: `D7_G_EXTRINSIC_INTEGRATION_READINESS_PASS` or `...FAIL`.

Neither review authorizes D7-H.

## 10. Phase G — closeout

For dual PASS:

- mark tasks complete with evidence;
- create `D7_G_EXTRINSIC_CONTRACT_ACCEPTANCE_R1.md` accepting only the interface/certification, not an algorithm result;
- set next gate `D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE`;
- keep D7-H not frozen/not authorized and every execution authorization false;
- append durable contract/limitation facts after memory triage;
- commit scoped changes locally, no push.

STOP. Do not implement or freeze D7-H in this task.

## 11. Return

Delta only:

1. D7-F acceptance audit, tables, scope, and route.
2. Exact extrinsic formula/API/provenance contract.
3. Tree/loopy/two-layer independent certification numerical maxima and negative control.
4. Proof existing hard decisions/final beliefs are unchanged.
5. Changed paths and ordered SHAs.
6. Focused/milestone tests.
7. Independent verdicts/findings.
8. Protected roots, no D7-H root/UUID, all auth false, no push.
9. Residual mathematical limitations and exact next gate.

End: `D7-F 已按 reverse-order regression diagnostic 受限接受；D7-G code-factor extrinsic 合同已完成独立数学认证与接口评审，尚未冻结或授权 D7-H；R1d、G1、G2 均未授权。`
