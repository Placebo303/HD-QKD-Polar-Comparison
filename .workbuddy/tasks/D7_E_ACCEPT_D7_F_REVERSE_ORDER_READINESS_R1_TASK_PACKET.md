# D7-E Acceptance + D7-F Reverse-Order Readiness R1

## 0. Objective

Complete two ordered phases:

1. Accept the immutable D7-E result under a narrow directional diagnostic scope.
2. Freeze, implement, test, and independently review D7-F: a paired complete-two-layer discriminator comparing current forward order `L1→L2` with reverse order `L2→L1`.

This is a substantial autonomous readiness task but authorizes zero scientific decoder calls and no D7-F execution. Stop after independent Pre-EXECUTE PASS awaiting fresh authorization.

## 1. Main-thread scientific ruling

D7-E may be accepted only as:

`D7_E_RESULT_ACCEPTED_DIRECTIONAL_CROSS_LAYER_TRANSFER_DIAGNOSTIC`

Accepted observations:

- 192/192 frozen calls completed; 64/64 transfer slots eligible and invoked;
- `f=1.0`: both directions control `0/16`, transfer `0/16`;
- `f=1.2`, `L1_TO_L2`: control `0/16`, transfer `3/16`, `AMBIGUOUS_TRANSFER_EFFECT`;
- `f=1.2`, `L2_TO_L1`: control `3/16`, transfer `7/16`, four transfer-only, zero control-only, `STRONG_TRANSFER_LIFT`;
- no crash/nonfinite/watchdog; wall/RSS within frozen limits;
- integrity status `PASS_WITH_DISCLOSED_VERIFY_PROVENANCE_GAP`, retaining the original BLOCKED review and additive R18 closure.

Permitted inference: for this frozen synthetic Model-F/decoder/matrix/seed contract, useful transfer is direction-dependent and strongest in `L2_TO_L1` at `f=1.2`.

Forbidden inference: general cross-layer success, FER/leakage/key rate, qualification, real-data performance, proof that alternating decoding converges, or permission for R1d/G1/G2.

Route ruling: test whether the directional lift survives as complete two-layer recovery when reversing the sequential order. Do not implement a feedback cycle yet. Existing provenance proves a posterior consumed checks, but it does not expose cavity/extrinsic messages needed to prevent syndrome evidence from returning to its source layer.

## 2. Preconditions and STOP rules

- Branch `formal-ir-v72p1-addendum-clean`.
- Commit `40977a2c` is an ancestor of HEAD.
- D7-E seven-file root is immutable.
- D7-E state: attempts/completed `1/1`, auth false, terminal `D7_E_L2_TO_L1_TRANSFER_LIFT`, Pre-RESULT `PASS_WITH_DISCLOSED_VERIFY_PROVENANCE_GAP`, result accepted false, next gate `INDEPENDENT_D7_E_RESULT_ACCEPTANCE_R1`.
- All execution authorizations/promotion false; R1d/G2 absent.

Any mismatch or scientific ambiguity means STOP. Do not repair predecessor evidence.

## 3. Hard prohibitions

- Zero scientific decoder calls; fake/tiny certified-oracle tests only.
- No D7-E rerun/verify, R1d, `--phase`, formal G1/G2, CAL, VAL, real/raw, or VOID reads.
- No estimator/graph/mother/row/seed/damping/iteration/schedule/threshold search.
- No flooding, oracle truth input, forced sweep, warm start, alternating feedback, third decoder stage, joint factor graph, or generalized turbo framework.
- No persisted beliefs/priors/symbols/syndromes/vectors.
- Do not modify accepted D7-B/C/D/E roots or frozen `src/`, `experiments/`, `tools/`.
- No push, broad stage, reset, checkout, clean, stash, rebase, or amend.
- Do not request or infer execution authorization.

## 4. Phase A — accept D7-E

### A01 audit

Read committed D7-E scalar artifacts, original review, transcript appendix, and R18 addendum. Independently recompute the four strata and terminal. Confirm §1 exactly.

### A02 acceptance document

Create `D7_E_RESULT_ACCEPTANCE_R1.md` containing lifecycle/root identity, four 2x2 tables, provenance/resource facts, disclosed transcript gap, exact accepted label, permitted inference, unsupported-claims ceiling, and D7-F route.

### A03 state and durable route

Set only factual acceptance fields and `next_gate: D7_F_REVERSE_ORDER_PACKET_FREEZE`; append concise accepted facts/routing to decision-log and memory. Keep all authorization false. Commit Phase A separately.

## 5. Phase B — freeze D7-F before implementation

Create OpenSpec change `v72p2d7-reverse-order-cross-layer-discriminator` and cycle directory `V72P2D7-GF32-REVERSE-ORDER-DISCRIMINATOR`.

Freeze preregistration and execution packet before result-bearing implementation.

### B01 identities

- `f=[1.0,1.2]`; seeds `2026091300..2026091315`, frozen order.
- Same corrected per-Bob-column concentration estimator, accepted Model-F root, D7-C/D7-E block identity, H/mother prefixes, rows, GF32 polynomial 37, cold row-layered decoder, `max_iter=90`, `damping=1.0`.
- No oracle, flooding, CAL/VAL, real/raw, or graph/mother changes.

### B02 paired arms

For every `(f,seed)` execute arms in this order:

1. `FORWARD_L1_TO_L2`: decode L1 marginal; if finite/non-crash/shape-valid and provenance exactly `CHECK_UPDATED`, derive transient `P(U2|B,s1)` and cold-decode L2.
2. `REVERSE_L2_TO_L1`: decode L2 marginal; under the same gate derive transient `P(U1|B,s2)` and cold-decode L1.

Source exact is not an eligibility gate. An ineligible second stage is a blocked non-call, never replaced. There is no transfer back to the source layer.

Maximum slots: `32 identities × 4 = 128` calls.

### B03 outcome accounting

For each arm persist scalar-only:

- first/second stage eligibility and provenance;
- L1 exact/syndrome and L2 exact/syndrome separately;
- `both_layers_exact = L1_exact AND L2_exact` only;
- calls, blocked, crash/nonfinite, iterations/work, wall, RSS.

Never merge syndrome success into exact success.

### B04 evidence-use contract

Each target starts cold from the transfer prior and consumes its own syndrome once. No target posterior is fed back, blended, multiplied, or reused. Tests must prove the first-stage syndrome is consumed only by its source decoder and the second-stage syndrome only by its target decoder.

Explicitly document that >2-stage alternating remains blocked pending a cavity/extrinsic-message contract capable of excluding returned syndrome evidence.

### B05 paired label per f

Across the same 16 seeds compare reverse candidate C with forward reference R:

- `candidate_only`: C both-exact and R not;
- `reference_only`: R both-exact and C not;
- `both`, `neither`.

First-match label:

1. `COVERAGE_BLOCKED` if either arm has fewer than 12/16 complete eligible paired outcomes;
2. `REVERSE_REGRESSION` if `reference_only>=2` and `candidate_only==0`;
3. `STRONG_REVERSE_LIFT` if `candidate_only>=4` and `reference_only==0`;
4. `WEAK_REVERSE_LIFT` if `candidate_only>reference_only` but strong is not met;
5. `NO_REVERSE_LIFT` otherwise.

These are synthetic diagnostic labels, not FER thresholds.

### B06 terminal priority

1. `D7_F_PRE_EXECUTION_BLOCKED`
2. `D7_F_WATCHDOG_TIMEOUT_VOID`
3. `D7_F_NONFINITE_OR_CRASH_BLOCKED`
4. `D7_F_RESOURCE_OVERRUN`
5. `D7_F_INCOMPLETE_MATRIX_BLOCKED`
6. `D7_F_PROVENANCE_COVERAGE_BLOCKED`
7. `D7_F_REVERSE_ORDER_STRONG_LIFT` if either f is strong and the other does not regress
8. `D7_F_REVERSE_ORDER_WEAK_LIFT` if either f is weak and neither regresses
9. `D7_F_REVERSE_ORDER_REGRESSION`
10. `D7_F_NO_USEFUL_REVERSE_ORDER_LIFT`

No automatic successor is encoded.

### B07 resources/output

- max 128 calls; per-call 120 s; stored wall ≤1500 s; outer `timeout -k 30 1800`;
- `.venv/bin/python` only;
- accepted `/proc/self/status` `VmHWM`, strict `<2 GiB`, fail-closed;
- sequential, one fresh UUID, no overwrite/retry/resume;
- seven scalar text files plus independent read-only verifier.

Freeze exact command with `<uuid>` and mark `NOT_AUTHORIZED`. Commit Phase B separately.

## 6. Phase C — minimal implementation

Add one Comparison-owned formal-IR module, one test file, and one thin script. Reuse D7-E loaders, corrected estimator, transfer functions, provenance/RSS/scalar/verifier conventions through narrow imports; do not copy an entire predecessor module.

No change to v35, D5, D6, or D7-A/B/C/D/E production code. If unavoidable, STOP.

Require lazy binding and DI. Import/help/dry-run/unauthorized/verifier/tests must not read real Model-F, call/bind a real decoder, or create a scientific root.

## 7. Phase D — tests

At minimum cover:

- exact 128-call matrix/order and cap;
- arm transitions and blocked non-calls;
- source exact not an eligibility gate;
- only exact `CHECK_UPDATED` transfers;
- each syndrome consumed once, no target feedback;
- both-layer exact truth table and syndrome isolation;
- paired-label boundaries and terminal priority;
- RSS boundaries/fail-closed behavior;
- scalar-only schema/forbidden payloads;
- writer/verifier tamper cases;
- protected-root/no-overwrite refusal;
- external-cwd decoder/loader sentinel;
- dry-run and unauthorized refusal;
- D7-E/BP provenance regression.

Run focused tests and one milestone regression. Trust independent reviewer-go results; do not duplicate full suites. No perf-v38 or scientific decoder.

## 8. Phase E — independent reviews

Implementation verdict: `D7_F_IMPLEMENTATION_REVIEW_PASS` or `...FAIL`.

Review identity, evidence-use/no-feedback proof, state machine, pairing, labels, terminals, resources, schema, verifier, lazy binding, and scope.

After PASS, perform fresh Pre-EXECUTE review: `.venv`/environment, exact command, one live `VmHWM`, timeout, root absence, auth false, protected roots, dry-run, refusal, external-cwd sentinel, focused tests, frozen packet.

Pre-EXECUTE verdict: `D7_F_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION` or `...FAIL`.

Neither grants authorization.

## 9. Phase F — closeout

For dual PASS: close tasks with evidence; set state/gate `D7_F_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`; keep authorization/attempts/decoder/result/acceptance/promotion false/zero; append only durable readiness facts after memory triage; commit scoped changes locally; do not push. STOP without requesting authorization.

## 10. Return

Delta only:

1. D7-E acceptance audit/scope and four strata.
2. D7-F identities, 128-call arithmetic, arms, evidence-use contract, labels, terminals, budgets.
3. Changed files and ordered SHAs.
4. Focused/milestone test summaries.
5. Independent verdicts/findings.
6. Root equality, no D7-F root/UUID, auth/state/no-push.
7. Risks and exact next gate.

End: `D7-E 已按方向性跨层 transfer diagnostic 受限接受；D7-F forward-vs-reverse complete-two-layer discriminator 已完成冻结、实现和独立 Pre-EXECUTE，尚未授权、未执行；多轮 alternating 仍等待可验证 extrinsic/cavity 合同，R1d、G1、G2 均未授权。`
