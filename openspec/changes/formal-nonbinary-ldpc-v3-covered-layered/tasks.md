# Tasks: Formal Nonbinary LDPC v3 Covered Layered Successor

## Phase 0: Planning freeze

- [x] Preserve v1/v2 as immutable evidence and quantify the v2 prefix-coverage diagnostic without making a causal claim.
- [x] Freeze v3 identity, fixed verified shifts plus finite coefficient search, canonicalization, rank/cycle/coverage/distance-proxy preflight, exact row-layered updates, two candidates, fresh roots, policies, gates, caps, artifacts and N4 boundary.
- [x] Record the read-only failed independent SHA-shift salt probe; it is planning validation only and has no production/output/data artifact.
- [x] Freeze the no-change boundary: Polar, `qldpc_reference`, prior formal source and outputs remain untouched.

## Phase 1: Candidate-only engineering

- [x] Implement pure v3 codebook construction and fail-closed preflight; test all prefixes, canonical reconstruction, tampering, rank, zero 4-cycles, coverage and weight-1/2 proxy.
- [x] Implement full-message layered FFT-QSPA with the exact per-row extrinsic/product/damped-message/belief-update equations and two damping values; test a q=4 brute-force check, row-layered ordering, numerical failures, caps and absence of Alice truth.

## Phase 2: Qualification machinery

- [x] Implement plan-only, execute and read-only verifier with fresh generator roots, CSPRNG records, no-overwrite artifacts, scoped provenance, accounting and invalid-run retention.
- [x] Test fake-run, denominator retention, zero-eligible null selection, confirmation non-materialization/isolation, tamper rejection and strict replay.

## Phase 3: Main-thread acceptance before data

- [x] Main reviews implementation and verifies focused/cross-version tests, scoped diff and frozen boundaries before authorizing a single plan-only creation.
- [x] Do not generate development or confirmation data in this change until Phase 3 acceptance is explicitly recorded.

Acceptance recorded 2026-07-30: T0 compile passed; T1 candidate tests passed
5/5; T2 candidate/qualification tests passed 23/23; T3 nonbinary predecessor
regression passed 42/42. Independent reviewer returned `NO_FINDINGS` after
R6/R1/R5 closure. A non-qualification p=.30/checks=40/max_iter=12 probe used
seed 202607429999 and completed both candidates in 3.531/3.859 seconds with
4,456,448 declared bytes. Frozen directories were unchanged and the official
v3 output root was absent.

## Phase 4: Conditional synthetic execution

- [x] After authorization, create one no-overwrite plan, execute it once, and strictly replay it read-only.
- [x] If development readiness fails or no policy is eligible, stop as `non_promoted_development`; do not create confirmation material.
- [x] If promotion fails, retain evidence and stop; N4 requires promoted confirmation plus a new approved OpenSpec change.

Execution recorded 2026-07-30: the sole no-overwrite plan, sole execute, and
sole strict read-only replay completed at
`comparison_bench/outputs_comparison/formal_ir_methods/20260728_v3_nbldpc_synthetic/`.
The selected `nbldpc_formal_v3_layered_l075` margin-8 policy used 32/40
checks. Development achieved 23/24 at p=.20 and 24/24 at p=.30, so the sealed
confirmation material was created. Confirmation achieved 32/32 at p=.20 and
30/32 at p=.30, with zero prohibited failures. The frozen 31/32-per-stratum
gate therefore failed by one p=.30 frame. Strict verification returned
`verified=True`, `run_status=completed`, `promoted=False`. Preserve the
package without rerun or tuning; N4, sidecar access, and `.ttbin` processing
remain forbidden.
