# Tasks: V12 Nonbinary LDPC Real Micro-Feasibility

All items are initially unchecked. This newly proposed change has not
implemented code, prepared a real partition, or executed a decoder.

## Planning Freeze

- [x] **V12-P01** Bind and preserve the exact V7/V10/V11 predecessor meanings.
- [x] **V12-P02** Freeze sole route V12-R1: unchanged V7 R1A matrix, primary
  flooding FFT-QSPA, full 170-row syndrome, schedule, and iteration cap.
- [x] **V12-P03** Freeze the 10 dB q=1024 Gray bw200 contiguous-256 domain,
  four-frame sacrificed role, and no split/concatenation rule.
- [x] **V12-P04** Freeze the primary flooding schedule, conservative `p=.20`
  prior, and Alice-information boundary.
- [x] **V12-P05** Freeze cross-history identity/payload exclusion and source-
  blocked behavior.
- [x] **V12-P06** Freeze verification, transcript, accounting, gate, terminal
  states, lifecycle, and claim boundary.
- [x] **V12-P07** Obtain an independent read-only freeze review of the complete
  V12 packet, exact seven-file package, and seed-record contract before
  implementation. (Done: independent read-only review returned zero blocker
  and zero major findings; no decoder or real source was accessed.)

## Implementation — Initially Authorized After V12-P07

- [x] **V12-I01** Add immutable V7 R1 reconstruction/binding checks.
- [x] **V12-I02** Add the V12 method wrapper and prove the decoder cannot
  access Alice truth, frame-specific SER, or verification feedback.
- [x] **V12-I03** Add partition and exclusion-inventory preparation APIs that
  cannot call a decoder or expose production confirmation roles.
- [x] **V12-I04** Add transcript, Toeplitz verification, leakage accounting,
  denominator, failure, and terminal-state logic.
- [x] **V12-I05** Add separate plan/execute/read-only-verify lifecycle APIs;
  test-only execution requires an explicit fake runner.

## Engineering Acceptance — Initially Authorized After V12-P07

- [x] **V12-T0** Run compile/import, exact constants/reconstruction, and tiny
  syndrome/Toeplitz/accounting checks.
- [x] **V12-T1** Run focused unit, boundary, Alice-information, role,
  no-overwrite, failure, and tamper tests.
- [x] **V12-T2** Run a complete four-frame fake lifecycle and decoder-free
  replay under a fresh writable workspace root with pytest cache disabled.

> Stop and return to the main thread after V12-T2. Real-source access,
> production partitioning, T3, plan creation, and decoder execution are not
> authorized by the initial OpenCode packet.

## Main-Thread Acceptance Before Real Data

- [x] **V12-T3** Run scoped regression, task-file/source-manifest review,
  dirty-worktree scope review, frozen V1-V11/baseline checks, and prove the
  V12 production output root is absent.
- [x] **V12-RP01** Reconstruct and independently review the explicit historical
  real-package exclusion inventory without loading frame arrays.
- [x] **V12-RP02** Reconstruct the complete eligible source pool, exclude all
  historical frame/payload identities, freeze exactly four bw200 rows, and
  independently review the partition without decoding.
- [x] **V12-RP03** Prepare and independently review one complete no-decode
  production plan; record explicit main-thread execution authorization.

## One Real Execute and One Read-Only Verification

- [ ] **V12-X01** Execute all four denominator frames exactly once, retaining
  every outcome and failure without retry, replacement, resume, or tuning.
- [ ] **V12-X02** Verify exactly once without importing/calling a decoder and
  independently reconstruct identities, transcript, accounting, outcomes,
  gate, and terminal state.

## Final Decision and Durable State

- [x] **V12-D01** Record `source_partition_blocked`, `invalid_execution`,
  `failed_canary`, or `observed_real_correction` with the
  exact claim boundary and no automatic successor.
- [x] **V12-D02** Complete scoped final checks, decision log/handoff updates,
  and mandatory memory triage. (Done 2026-08-13: decision-log entry, handoff/
  CURRENT_TASK update, memory §42 triage)

## Stop Rule

Any planning, engineering, source, partition, lifecycle, accounting, replay,
or scientific failure freezes the evidence and stops V12. No failure permits
post-hoc parameter changes, a replacement frame, rerun, another route, more
frames/strata, qualification, or promotion.
