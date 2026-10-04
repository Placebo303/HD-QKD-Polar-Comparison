# Tasks: Binary LDPC v4 Corrected Qualification v2

## Phase 1: Versioned Corrected Prerequisite

- [x] Update the four never-instantiated conditional runner/verifier files to
  v2 package identities and the corrected development-v2 prerequisite.
- [x] Preserve generator bytes, formal method, matrices, channel, selection,
  caps, statuses, denominators, 126/128 gates, transcript, and accounting.
- [x] Update focused synthetic/real tests to build a corrected-v2 development
  prerequisite and reject failed-v1 or tampered-v2 substitution.

## Phase 2: Strict Tooling Acceptance

- [x] Test synthetic success/non-promotion, fresh-root isolation, full
  artifact/DAG/public-payload tampering, failure finalization, cap,
  no-overwrite, and read-only verification.
- [x] Test real prerequisite blocking, source capacity failure, exclusion and
  disjointness, order, lock/source/seed/transcript tampering, retained
  denominators, failure finalization, no-overwrite, and read-only verification.
- [x] Main thread reviews requirement fidelity and runs focused plus
  v1-v4/formal-real/nonbinary regressions, compilation, diff checks, and
  historical source/output hash checks.

## Phase 3: One Fresh Synthetic Qualification

- [x] Main thread prepares and audits one fresh 128+128 synthetic plan.
- [x] Execute exactly once and verify exactly once.
- [x] Require at least 126/128 verified successes in both strata and zero
  forbidden failures before any real lock/plan may exist.
- [x] On failure, preserve the package and stop without tuning or rerun.
  The package promoted at 127/128 nominal and 126/128 stress with zero
  forbidden failures, so the failure stop did not apply. The promoted
  immutable package also must not be rerun or used for tuning.

## Phase 4: Real Data Sufficiency

- [x] Record current 85/128 eligible-frame capacity and 43-frame deficit in
  each of bw120, bw180, and bw200.
- [x] Audit local 20 dB candidates and reject the `TypeII_776.1nm_3s - 副本`
  tree as new capacity because both `.ttbin` SHA256 values duplicate the
  registered acquisition.
- [x] Implement the frozen no-overwrite source-extension builder/verifier and
  source-aware real candidate pool without modifying the historical v3 bridge.
- [x] Test distinct-acquisition intake, copied-raw rejection, exact three-
  stratum provenance, hash/metadata/array/tail tampering, payload duplication,
  deterministic selection, capacity-before-output, and read-only verification.
- [x] Main thread reviews requirement fidelity and runs focused plus binary
  v1-v4/formal-real regressions before accepting the intake implementation.
- [ ] After synthetic promotion, obtain and validate at least 43 additional
  eligible complete frames per stratum, preferably at least 64 supplied.
- [ ] Freeze a traceable extended source manifest and prove domain consistency,
  source hashes, exact framing, and identity non-overlap before real prepare.

## Phase 5: One Real `.ttbin` Qualification

- [ ] Only after Phases 3-4 pass, create and audit one fresh real lock/plan.
- [ ] Execute 384 frames exactly once and verify exactly once.
- [ ] Require at least 126/128 verified successes in all three strata and zero
  forbidden failures.
- [ ] Preserve a failed/non-promoted package without tuning or rerun.

## Phase 6: Handoff and Memory

- [ ] Update handoff, decision log, project memory, and binary/nonbinary
  parallel handoff with commands, hashes, results, scope, and next action.
- [ ] Perform mandatory read-only memory triage.
