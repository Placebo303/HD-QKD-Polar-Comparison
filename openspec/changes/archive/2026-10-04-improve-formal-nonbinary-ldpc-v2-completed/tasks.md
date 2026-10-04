# Tasks: Formal Nonbinary LDPC v2 Successor

## Phase 0: Planning freeze and preservation

- [x] Preserve v1 N3 as immutable non-promotion evidence; prohibit confirmation reuse, tuning, repair, and reruns.
- [x] Freeze the exact v2 identity/schema, output/run pattern, codebook construction, four candidate algorithms, resource caps, seeds, policy/grid, artifacts, statuses, gates, provenance rule, and N4 boundary in the approved design/spec.
- [x] Freeze the no-change boundary for Polar, `qldpc_reference`, existing outputs, and dependencies.

## Phase 1: Candidate-only implementation

- [x] Implement pure deterministic v2 codebook construction, canonical bytes, GF(q) rank/cycle verifier, and v1-control identity without output writes.
- [x] Implement the exact flooding, damping lambda=.5, and tempering exponent=.8 FFT-QSPA variants, preserving no-Alice-truth inputs and mapping/accounting semantics.
- [x] Add focused tests for K16 1-factorization/round-permutation/first-rotation reconstruction, alpha^48/B rank, all prefixes, zero 4-cycles, candidate IDs, numerical fail-closed behavior, resource caps, and no baseline/reference mutation.

## Phase 2: Qualification machinery implementation

- [x] Implement plan-only/create, execute, and read-only verify machinery with the frozen fresh generator, 703-bit CSPRNG seed records, no-overlap proof, exact integrity/performance status split, null no-eligible-policy selection, readiness stop, artifacts, and scoped provenance.
- [x] Add fake-runner tests for confirmation isolation, denominator retention, performance-failure eligibility, every integrity-failure exclusion, deterministic zero-eligible selection, readiness stop, promotion/non-promotion, tampering, no-overwrite, and unrelated-worktree-drift diagnostics.

## Phase 3: Pre-execution review

- [x] Run focused candidate/qualification tests and protected-root checks.
- [x] Create exactly one reviewed v2 plan-only artifact at the frozen additive root; verify hashes, candidate manifest, seed disjointness, selection isolation, caps, and zero decoder calls.
- [x] Obtain main-thread authorization before its sole execution.

## Phase 4: Synthetic execution and decision

- [x] Execute once, retain every outcome and invalid package, and run the strict read-only verifier.
- [x] Record the decision. If development readiness or either confirmation stratum fails, mark non-promotion and stop.
- [ ] Not applicable: synthetic development readiness failed, so N4 planning is forbidden; do not process `.ttbin` or real sidecars.

## Acceptance

- [x] v1 remains immutable/non-promoted and has no influence on v2 selection.
- [x] All v2 construction, candidate, seed, policy, transcript, and artifact bindings reconstruct exactly.
- [x] Strict verification binds scoped qualification sources/artifacts while reporting unrelated worktree drift diagnostically.
- [x] Synthetic promotion is only 31/32 in each stratum with all integrity gates; otherwise N4 and real-data work remain forbidden.
