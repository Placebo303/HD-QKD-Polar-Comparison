# D7-H Alternating Discriminator Readiness R1A1 — Heavy Task Packet

## 0. Outcome

Take D7-H from the current uncommitted freeze draft to a reviewed, executable-but-unauthorized candidate:

1. audit and correct the R1 freeze before it becomes authoritative;
2. commit the corrected OpenSpec/prereg/packet/state freeze;
3. implement the smallest two-transfer alternating discriminator;
4. close the accepted D7-G additive-field compatibility tripwire;
5. run focused and milestone tests;
6. obtain independent implementation and Pre-EXECUTE reviews;
7. stop at `D7_H_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`.

This packet authorizes implementation and test-only tiny/fake decoder work. It authorizes **zero D7-H scientific decoder calls**, no UUID, no result root, and no Model-F artifact read.

## 1. Current authoritative baseline

- Branch: `formal-ir-v72p1-addendum-clean`.
- Committed HEAD on entry should be `46141fcc` or a documentation-only descendant with no D7-G/D7-H semantic drift.
- D7-G accepted tokens:
  - `D7_G_EXTRINSIC_CONTRACT_REVIEW_PASS`
  - `D7_G_EXTRINSIC_INTEGRATION_READINESS_PASS`
- Accepted interface:
  - `L_code_ext = L_post - log(p_in)`, row-LSE normalized;
  - extrinsic provenance `NO_CHECK_EVIDENCE`, `CHECK_EXTRINSIC`, `WARM_START_UNSPECIFIED`;
  - only explicit finite shape-correct `CHECK_EXTRINSIC` is transferable;
  - flooding extrinsic deferred; existing consumers unwired.
- Committed D7-G gate: `D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE`.
- D7-E/F results are accepted only under their narrow diagnostic scopes.
- All execution authorizations false; no D7-H UUID/root; R1d/G2 absent.

Current uncommitted candidate paths are expected and must be treated as a **draft**, not accepted project state:

- `.workbuddy/tasks/D7_H_ALTERNATING_DISCRIMINATOR_PACKET_FREEZE_R1_{TASK_PACKET,PROMPT}.md`
- `docs/research_cycles/V72P2D7-GF32-ALTERNATING-DISCRIMINATOR/`
- `openspec/changes/v72p2d7-alternating-discriminator/`
- four additive D7-H linkage lines in D7-G `cycle_state.yaml`.

If production D7-H code, a D7-H workspace root, UUID, authorization, or scientific observation already exists, STOP.

## 2. R1A1 freeze correction — main-thread ruling

The draft incorrectly calls STAGE 1 mandatory. Correct every draft artifact before the freeze commit:

- STAGE 0 `SOURCE_L1_MARGINAL` is the only unconditional mandatory call.
- STAGE 1 `FORWARD_L1_TO_L2` is invoked only if STAGE 0 yields finite, shape-valid, non-crashed, exact `CHECK_EXTRINSIC`.
- STAGE 2 `BACKWARD_L2_TO_L1` is invoked only if STAGE 1 yields the same admissible extrinsic.
- `NO_CHECK_EVIDENCE`, including iteration-0 hard/syndrome success, blocks the next stage. Source hard exact is not an eligibility gate.
- A blocked stage is a scalar non-invocation; all downstream stages for that identity are blocked, never synthesized, replaced, retried, or resumed.
- Maximum remains `32 identities × 3 = 96`; minimum actual calls is 32. Do not call 64 calls “mandatory.”
- A complete paired outcome requires all three stages. Per-f coverage is the count of identities with all three stages invoked and finite/shape-valid.
- `COVERAGE_BLOCKED` applies when fewer than 12/16 complete paired identities exist for either reference or candidate comparison population. Since both endpoints share the chain, record one complete-chain coverage count plus explicit blocked-at-stage1/blocked-at-stage2 counts.

Correct the phrase “each decoder consumes its own syndrome exactly once” to:

- each **decode invocation** consumes its designated syndrome once;
- L1 is decoded twice across STAGE 0 and STAGE 2, but STAGE 1's outgoing code extrinsic removes its entire incoming prior, including STAGE 0's L1 evidence, before STAGE 2 consumes L1 syndrome again;
- tests must prove the returned prior is invariant to the removed STAGE 0 incoming-message component while remaining sensitive to STAGE 1's own check evidence.

No scientific parameter, identity, threshold, arm, terminal, or budget otherwise changes.

## 3. Hard prohibitions

- No real/production D7-H decoder call, D7-H execution command, UUID, or result root.
- No Model-F binary/content read, CAL, VAL, real/raw, VOID, R1d, any `--phase`, formal G1/G2.
- No estimator, graph, mother, row, seed, decoder, damping, iteration, label, terminal, threshold, or budget tuning.
- No third transfer, additional cycle, convergence claim, flooding, oracle truth, warm-start activation, joint decoder, concurrency, retry, or performance sweep.
- Do not modify accepted D7-E/F/G roots or frozen baseline `src/`, `experiments/`, `tools/`.
- Do not wire D7-G extrinsic into D5/D6/D7-E/F production paths.
- No push, broad stage, reset, checkout, clean, stash, rebase, or amend.
- Preserve unrelated dirty/EOL worktree state.

## 4. Phase A — audit, correct, and freeze

### A01 draft audit

Read every current draft artifact and report all occurrences of mandatory/gated/call-count/coverage/syndrome-once wording. Confirm no code/root/UUID/auth exists.

### A02 R1A1 correction

Apply §2 consistently to:

- freeze task packet and prompt;
- D7-H prereg and cycle state;
- OpenSpec proposal/design/tasks/spec.

Add `D7_H_PACKET_REVIEW_R1A1.md`, whose independent reviewer checks:

- D7-G contract correctly supports exactly two transfers;
- stage gating/call arithmetic/coverage are internally consistent;
- candidate/reference endpoints are paired on identical `(f,seed)`;
- no-returned-evidence claim is limited to the certified extrinsic contract;
- labels/terminal/resources are unchanged and complete;
- no scientific execution or implementation exists.

Unique verdict: `D7_H_PACKET_REVIEW_PASS_R1A1` or `...FAIL_R1A1`.

FAIL → STOP. PASS → commit the corrected freeze, including the packet pair, OpenSpec, prereg/state, packet review, and D7-G linkage. Use exact path staging; force-add `.workbuddy` only if ignored. No push.

## 5. Frozen D7-H scientific contract

### B01 matrix

- `f=[1.0,1.2]` in order; seeds `2026091300..2026091315`.
- `n=64`; L1 rows 49/59; L2 rows 43/52.
- accepted D5-native mothers/graph seeds and corrected per-Bob-column concentration Model-F from the fixed accepted root.
- row-layered GF32 polynomial 37, cold start, `max_iter=90`, `damping=1.0`.

### B02 chain

Per identity:

1. STAGE 0: cold L1 marginal decode; reference L1 result.
2. If admissible, transport L1 `CHECK_EXTRINSIC` through the fixed joint Model-F and cold-decode L2; reference endpoint is STAGE0 L1 + STAGE1 L2.
3. If admissible, transport L2 `CHECK_EXTRINSIC` back and cold-decode L1; candidate endpoint is STAGE1 L2 + STAGE2 L1-return.

The returned prior must use explicit code extrinsic only—never `final_beliefs`, reconstructed prior subtraction, source hard truth, oracle, or warm state.

### B03 paired labels per f

On complete-chain identities only:

1. `COVERAGE_BLOCKED` if complete-chain coverage <12/16;
2. `ALTERNATING_REGRESSION` if reference-only ≥2 and candidate-only=0;
3. `STRONG_ALTERNATING_LIFT` if candidate-only ≥4 and reference-only=0;
4. `WEAK_ALTERNATING_LIFT` if candidate-only>reference-only;
5. `NO_ALTERNATING_LIFT` otherwise.

Both-layer exact is logical AND only; syndrome remains separate.

### B04 terminal priority

Preserve draft ten-terminal first-match order from PRE_EXECUTION_BLOCKED through NO_USEFUL_ALTERNATING_LIFT. No automatic post-result route.

### B05 resources/output

- max 96 calls; per-call 120 s; stored wall ≤1500 s; outer `timeout -k 30 1800`;
- sequential; `.venv/bin/python`; `/proc/self/status` unique `VmHWM`, strict `<2GiB`, fail-closed;
- one fresh direct-child UUID root, no overwrite/retry/resume;
- exactly seven scalar text files plus independent read-only verifier;
- no beliefs/priors/extrinsic arrays/symbols/syndromes/block vectors persisted.

## 6. Phase B — minimal implementation

Implement only:

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_alternating_discriminator.py`
- `comparison_bench/tests/test_v72p2d7_gf32_alternating_discriminator.py`
- `scripts/v72p2d7_gf32_alternating_discriminator.py`

Reuse D7-E/F loaders, estimator, RSS, scalar/writer/verifier conventions and D7-G explicit helper by narrow imports. Do not copy predecessor modules wholesale and do not build a generic alternating framework.

Requirements:

- lazy binding + DI;
- unauthorized refusal before decoder bind, Model-F read, UUID/root creation;
- import/help/dry-run/verifier/tests are zero-real-decoder and zero-real-Model-F;
- exact 96-slot dry-run schedule includes gated slots as planned slots;
- runtime creates records only for invoked decoder calls and separate blocked-stage scalar accounting;
- direct foreground command/exit capture contract retained for future operator packet;
- writer fail-loud/no-overwrite; verifier independently recomputes schedule, gates, endpoints, labels, terminal, budgets, schema, and no-returned-evidence scalar invariants.

## 7. Phase C — close the accepted D7-G compatibility tripwire

The accepted D7-G review identified one stale test that pins the old full `DecoderResult` field list. Update only that test to assert:

- legacy first six positional fields unchanged;
- `belief_provenance` remains in place;
- additive optional `extrinsic_log_beliefs` and `extrinsic_provenance` are present with accepted defaults;
- legacy positional construction remains compatible.

Do not change production behavior or weaken any numerical assertion. This is lifecycle maintenance for an accepted additive API, not a green-by-deletion exception.

## 8. Phase D — focused tests

At minimum cover:

- 32 mandatory STAGE0, gated STAGE1/STAGE2, maximum 96, exact order;
- blocked-at-stage1 and blocked-at-stage2 cascades with no fabricated calls;
- iteration-0 `NO_CHECK_EVIDENCE` blockage even when hard/syndrome exact;
- source exact not an eligibility gate when `CHECK_EXTRINSIC` exists;
- helper-only extrinsic transport; posterior path poison test;
- returned-prior cavity invariance to STAGE0 incoming evidence and sensitivity to STAGE1 check evidence;
- each invocation gets exactly one designated syndrome; L1's two invocations distinguished;
- reference/candidate endpoint identity and AND semantics;
- coverage threshold and all paired-label boundaries;
- all terminal priorities;
- RSS/wall/call-cap fail-closed boundaries;
- scalar schema/forbidden-payload scan;
- writer/verifier tamper cases;
- external-cwd exact decoder/loader sentinel, dry-run, help, unauthorized refusal;
- protected-root/no-overwrite guards;
- D7-G 48 certification tests and repaired BP provenance compatibility test.

Run py_compile, focused D7-H tests, D7-G certification, BP interface suites, and one non-perf milestone regression. Independent reviewer-go results are accepted; do not rerun identical full suites ceremonially. Tiny fake/in-memory decoder only.

## 9. Phase E — independent reviews

### E01 implementation review

Unique verdict `D7_H_IMPLEMENTATION_REVIEW_PASS_R1A1` or `...FAIL_R1A1`.

Review gating/call arithmetic, cavity evidence exclusion, endpoint pairing, labels/terminal, resources, schema/verifier, lazy binding, test sufficiency, API compatibility, and exact file scope.

### E02 Pre-EXECUTE review

Only after E01 PASS. Independently verify:

- committed freeze precedes implementation and no scientific observation;
- exact implementation/packet consistency;
- `.venv/bin/python`, environment, timeout, one live VmHWM;
- no D7-H root/UUID and all auth false;
- protected roots/R1d/G2 state;
- dry-run exact 96 planned slots;
- unauthorized refusal and external-cwd decoder/loader sentinel;
- focused tests and no stale D7-G field-list failure;
- exact future command.

Unique verdict `D7_H_PRE_EXECUTE_REVIEW_PASS_R1A1_AWAITING_EXPLICIT_AUTHORIZATION` or `...FAIL_R1A1`.

Neither review authorizes execution.

## 10. Phase F — closeout

For dual PASS:

- close OpenSpec implementation/review tasks with evidence;
- set D7-H state/gate `D7_H_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`;
- set plan/implementation accepted facts only as supported;
- keep every execution authorization false, attempts/completed zero, decoder/result/acceptance/promotion false, no UUID/root;
- append only durable readiness facts after memory triage;
- commit exact scoped files locally, no push.

STOP. Do not request or infer authorization.

## 11. Return format

Delta only:

1. Current committed baseline and disposition of the uncommitted draft.
2. Every R1A1 semantic correction and packet-review verdict.
3. Frozen matrix, stage gates, 96-call maximum/minimum, coverage, endpoints, labels, terminals, resources.
4. Implementation/test files and ordered commit SHAs.
5. Focused/milestone literal test summaries, including D7-G tripwire closure.
6. Cavity/no-returned-evidence proof and negative controls.
7. Independent implementation/Pre-EXECUTE verdicts.
8. Protected roots, no D7-H root/UUID, auth/state/no-push.
9. Remaining limitations and exact next gate.

End: `D7-H 两次 transfer 的 alternating discriminator 已完成 R1A1 冻结修正、最小实现与独立 Pre-EXECUTE；尚未授权、未执行，不支持 alternating convergence 声明，R1d、G1、G2 均未授权。`
