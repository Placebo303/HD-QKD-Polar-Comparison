# Tasks: Formal Nonbinary LDPC v6 Long-Block Development

## 0. Freeze and preflight

- [x] V6-00 Read `AGENTS.md`, project memory, this change, and the OpenCode
  packet completely; record current HEAD and scoped dirty-worktree inventory.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)
- [x] V6-01 Confirm the allowed/forbidden file manifest and prove that no
  official v6 output directory exists.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)
- [x] V6-02 Write a short implementation note resolving message layout,
  allocation bound, canonical codebook bytes, and exact reusable v5 APIs;
  stop on any ambiguity rather than changing the spec.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)

## 1. Codebook and oracle

- [x] V6-10 Implement deterministic `(1024,320)` and `(1024,480)` degree-2
  PEG construction and canonical manifests.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)
- [x] V6-11 Implement reconstruction, GF-rank, degree, parallel-edge, and
  four-cycle checks.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)
- [x] V6-12 Add exhaustive GF(4)/GF(8) oracle vectors for coefficient
  permutations, check convolution, syndrome orientation, and hard decisions.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)

## 2. Decoder core

- [x] V6-20 Implement bounded n=1024 layered FFT-QSPA in a new additive
  module using the accepted field semantics.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)
- [x] V6-21 Enforce normalization, invalid-number, allocation, iteration, and
  fail-closed contracts.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)
- [x] V6-22 Bind syndrome consistency, Toeplitz verification, disclosure, and
  status accounting without a fallback path.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)

## 3. Development harness, not official execution

- [x] V6-30 Add a development-only runner API and CLI whose default action is
  plan preparation, never execute.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)
- [x] V6-31 Add fake-runner plan/execute/replay tests under a fresh
  `workspace/<task>/<uuid>` root; prove no production decoder is entered.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)
- [x] V6-32 Add layered tamper tests for bytes, semantic self-hashes,
  manifest links, source identity, transcript, leakage, and gate rebuilding.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)

## 4. Acceptance tiers

- [x] V6-40 T0: compile/import, deterministic construction, tiny math,
  canonical reconstruction, rank/degree/allocation assertions.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)
- [x] V6-41 T1: focused oracle, planted-error, invalid-boundary, and tamper
  tests.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)
- [x] V6-42 T2: complete fake development package plus strict read-only fake
  replay using an explicit fake runner.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)
- [x] V6-43 T3: targeted v5 nonbinary regression and frozen-source/hash audit;
  prove no official v6 output exists.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)
- [x] V6-44 Produce an additive engineering acceptance JSON that maps every
  V6 ID to command, exit code, evidence path, and source hash.
  (2026-08-02: implemented + accepted — evidence/v6_engineering_acceptance.json
  (HEAD a9c3c5d8696ad9fa967e2d5d8b9905c5a55c8344; tiers T0 16 / T1 38 / T2 6 /
  T3 51 all passed).)

## 5. Main-thread gate

- [x] V6-50 Independent review accepts or rejects the engineering candidate.
  (2026-08-02: independent review ACCEPTED — 7/7 checklist PASS, 0 blocking
  findings; see evidence/v6_50_review_acceptance.json.)
- [x] V6-51 Only after acceptance, create a separate reviewed sacrificed
  development plan with fresh roots; do not materialize confirmation.
  (2026-08-02: main-thread decision — no large-scale development run; a small
  sacrificed 8-frame canary plan (4 p=.20 + 4 p=.30, fixed codebooks, lambda
  .75, 50 iterations, workers=1, fresh roots/seeds, no confirmation) is staged
  first; creation/review/execution sequencing per main-thread direction.
  Canary staged and read-only reviewed READY-FOR-SINGLE-EXECUTION
  (evidence/v6_51_canary_plan_evidence.json), then executed exactly once and
  strict-replayed exactly once (both exit 0;
  evidence/v6_51_canary_execution_addendum.json). Result: 0/4 verified
  success in BOTH strata — all 8 frames decode_failed at max_iter=50, zero
  forbidden statuses; package retained in
  workspace/nbldpc_v6_canary_b01c42a5dee14ed0913e78d60944cc38/canary_plan;
  no official root created.)
- [x] V6-52 After development, choose exactly one successor: qualification,
  n=4096, multiplicative repetition, or GF(32)xGF(32) multilevel coding.
  (2026-08-02: pre-registered decision gates — any stratum 0/4 → stop the
  long-block baseline, do NOT go to n=4096, prefer multiplicative repetition
  (2,3) mother code; both strata >= 1/4 → run 16+16 sacrificed development
  observing waterfall/iteration distribution/runtime; only stable high success
  → new qualification change. n=4096 not recommended at this point.
  GATE FIRED 2026-08-02: canary is 0/4 in both strata, so the degree-2
  n=1024 long-block baseline is stopped and n=4096 is not taken. Chosen
  successor: multiplicative repetition (2,3) mother code — a new OpenSpec
  change must be proposed before any implementation.)
- [x] V6-53 Perform project-memory triage after actual implementation; do not
  record speculative results as completed evidence.
  (2026-08-02: memory triage done — AGENT_PROJECT_MEMORY.md section 33.)
