# Tasks

## Phase 0: Freeze N0

- [x] Define the independent `nbldpc_formal_v1` identity and preserve
  `qldpc_reference` unchanged.
- [x] Freeze the q=2..1024 power-of-two field domain, polynomial-basis symbol
  encoding, metadata, statuses, and no-fallback rule.
- [x] Freeze a bounded read-only preflight and its acceptance tests.

## Phase 1: Implement N0

- [x] Add the deterministic GF(2^m) field specification and arithmetic module
  under `comparison_bench/src/comparison_bench/formal_ir/`.
- [x] Add a read-only preflight for supported-domain, field-ID, arithmetic,
  inverse, distributivity, and determinism checks.
- [x] Re-export only the new field/preflight public API from
  `formal_ir.__init__`.
- [x] Add focused tests covering q=2, q=256, q=1024, unsupported q, expected
  field-ID mismatch, full nonzero multiplicative cycles, and no mutation of
  `qldpc_reference`.

## Phase 2: Review And Handoff

- [x] Run the focused nonbinary tests and the existing qLDPC reference test.
- [x] Review the diff for frozen-baseline, output, dependency, and identity
  violations.
- [x] Record verified N0 state and the next N1/N2 backlog in the handoff,
  decision log, project memory, and OpenSpec task state.
- [x] Perform memory triage; do not record speculative decoder choices as
  durable facts.

## Acceptance

- [x] The preflight returns `ok` for q=2, 4, 8, 16, 32, 64, 128, 256, 512,
  and 1024 using one deterministic internal backend and unique canonical field
  IDs.
- [x] The q=1024 nonzero powers form one cycle of length 1023 and every
  nonzero element has a verified multiplicative inverse.
- [x] Unsupported q and expected-field-ID mismatch fail closed without a
  fallback.
- [x] `qldpc_reference` source, dispatch, status, and tests remain unchanged.
- [x] No outputs, experiments, qualification claims, or new dependencies are
  created by this change.

## Phase 3: Freeze N1

- [x] Freeze an n=64, 32-row mother matrix and exact 16/24/32 nested prefix
  family for every N0-supported q.
- [x] Freeze the cyclic/protograph-style topology, SHA256-derived shifts and
  nonzero coefficients, identity parity half, and construction seed semantics.
- [x] Freeze GF(q) Gaussian-elimination rank, canonical bytes, codebook IDs,
  top-level manifest ID, verifier statuses, and no-repair/no-fallback rules.

## Phase 4: Implement N1

- [x] Add pure deterministic GF(q) rank and codebook-family construction under
  `comparison_bench/src/comparison_bench/formal_ir/`.
- [x] Add canonical codebook bytes, ordered top-level manifest generation, and
  fail-closed in-memory verification.
- [x] Re-export only the frozen N1 public API from `formal_ir.__init__`.
- [x] Add focused tests for q=2 and q=1024 determinism, 16/24/32 prefix
  identity and full GF(q) row rank, canonical byte/hash stability, manifest
  round-trip verification, and tampered field/matrix/hash rejection.

## Phase 5: N1 Review And Handoff

- [x] Run N0+N1 focused tests and the existing qLDPC reference test.
- [x] Review frozen-baseline, output, dependency, method-identity, GF(q)-rank,
  prefix, and canonicalization boundaries.
- [x] Record verified N1 state and the remaining N2 decoder/accounting backlog
  in handoff, decision log, project memory, and OpenSpec tasks.
- [x] Perform memory triage without recording structural screening as decoder
  or qualification evidence.

## N1 Acceptance

- [x] q=1024 construction is deterministic and all 16/24/32 matrices are exact
  prefixes of one 32x64 mother matrix with GF(q) ranks 16/24/32.
- [x] Canonical bytes cover the complete field representation, construction,
  dimensions, topology, coefficients, seed, and ordering; codebook and
  manifest IDs reproduce exactly.
- [x] Tampered field IDs, coefficients, ranks, prefix metadata, codebook IDs,
  or manifest IDs fail closed without repair or fallback.
- [x] N0 behavior and `qldpc_reference` remain unchanged; no outputs,
  dependencies, decoder calls, experiments, or qualification claims are added.

## Phase 6: Freeze N2

- [x] Select bounded full-message FFT-QSPA as the first feasibility decoder
  and document why EMS tail/list rules remain a later alternative.
- [x] Freeze verified-N1-only inputs, q-ary symmetric priors, syndrome/coset
  direction, no-Alice-truth decoder API, deterministic flooding schedule, and
  q/n/check/iteration/memory caps.
- [x] Freeze dense message ordering, GF coefficient permutations,
  Walsh-Hadamard normalization/roundoff behavior, result statuses, and
  syndrome-consistency-only success semantics.
- [x] Freeze MSB-first symbol mapping, separate Toeplitz verification, exact
  syndrome/tag disclosure bits, and separate public-control accounting.

## Phase 7: Implement N2

- [x] Add pure q-ary symmetric priors, GF(q) syndrome, bounded FFT-QSPA coset
  decoding, and deterministic resource/status diagnostics.
- [x] Add MSB-first symbol conversion, exact disclosure accounting, and a thin
  wrapper around the existing locked Toeplitz verification result.
- [x] Re-export only the frozen N2 public API from `formal_ir.__init__`.
- [x] Add focused tests for q=4 transform/coefficient semantics, no-error and
  correctable parity-symbol cases, q=1024 bounded execution, no-Alice decoder
  signature, syndrome-consistent versus verified distinction, iteration and
  resource failure, mapping, accounting, and Toeplitz behavior.

## Phase 8: N2 Review And Handoff

- [x] Run N0-N2 focused tests, existing qLDPC reference tests, and selected
  formal-verification regressions.
- [x] Review truth isolation, exact syndrome direction, GF coefficient
  permutation, numerical fail-closed behavior, caps, mapping, accounting,
  frozen baselines, outputs, dependencies, and status claims.
- [x] Record verified N2 feasibility and the remaining N3 pre-registration
  backlog in handoff, decision log, project memory, and OpenSpec tasks.
- [x] Perform memory triage without recording unit-test decoding as FER,
  qualification, promotion, or real-data evidence.

## N2 Acceptance

- [x] The decoder accepts no Alice truth, reconstructs only from Bob priors and
  Alice syndrome, and reports `syndrome_consistent` separately from formal
  Toeplitz verification.
- [x] q=1024 uses the verified N1 family within frozen iteration/storage caps,
  with deterministic results and no decoder/backend/lower-q fallback.
- [x] GF coefficient permutations and Walsh-Hadamard check convolution agree
  with brute-force q=4 check-node probabilities within a frozen tolerance.
- [x] MSB-first mapping preserves leading zeros; disclosure is exactly
  `checks*log2(q) + invoked_tag_bits`, with public control separate.
- [x] N0/N1 and `qldpc_reference` remain unchanged; no outputs, dependencies,
  qualification data, performance claims, promotion, or comparison are added.

## Phase 9: N3 Pre-Registration

- [x] Freeze sacrificed development and immutable confirmation generation,
  seeds, frame ordering, no-overlap proof, and source/code/config hashes.
- [x] Freeze supported q/frame/check/channel strata, one global development
  policy, FER and disclosure metrics, statistical promotion gates, runtime/
  memory caps, and exact stop rules before any run.
- [x] Freeze additive artifact names, transcript/status schema, strict
  read-only verifier, invalid-run handling, and non-promotion path.
- [x] Review the complete N3 plan before authorizing data generation or a
  synthetic qualification runner.

## Phase 10: Implement N3 Runner And Verifier

- [x] Add a plan-only/execute/verify CLI and pure qualification helpers using
  exactly the frozen N3 generation, policy, resource, status, transcript,
  artifact, invalid-run, and gate contracts.
- [x] Add tests proving plan-only makes zero decoder calls; generation and
  policy selection reconstruct exactly; confirmation cannot influence
  selection; every requested failure remains in the denominator.
- [x] Add strict verifier tamper tests for plan/generator/frame order, seed
  overlap/binding, codebook/policy hashes, transcript/disclosure, status
  precedence, outcome denominators, artifact DAG, gate/report, and invalid-run
  non-promotion.
- [x] Add deterministic fake-runner tests for promoted, non-promoted,
  per-frame exception/resource-cap, complete-run-cap, and rerun/no-overwrite
  paths without executing the real q=1024 grid.

## Phase 11: N3 Pre-Execution Review

- [x] Run N0-N3 focused tests and selected formal regressions.
- [x] Create the sole plan-only artifact at the frozen additive root and review
  exact hashes, seeds, zero overlap, policies, caps, provenance, and decoder-
  call count before execution.
- [x] Run the strict verifier in plan-only mode and independently confirm that
  the output root contains only `pre_run_plan.json`.
- [x] Authorize exactly one execution only if every pre-execution check passes.

## Phase 12: N3 Execute, Verify, And Handoff

- [x] Execute the frozen plan once, preserving any failure or invalid package.
- [ ] Strictly verify all seven artifacts read-only and independently recompute
  the development selection and confirmation gates.
- [x] Record non-promoted status without tuning confirmation or
  authorizing N4 unless both strata pass.
- [x] Complete memory triage and update durable handoff/decision/task state.

> Official strict verification is **failed/unverifiable**, not complete: live
> whole-worktree `git_status_sha256` drifted after execution. The plan and all
> source/CLI/contract hashes, git commit, and Python/NumPy matched; a diagnostic
> `_test_only=True` read-only replay verified content and gates but is not an
> official strict-verifier pass. The immutable package remains non-promoted;
> N4 is forbidden and no rerun/tuning is authorized.
