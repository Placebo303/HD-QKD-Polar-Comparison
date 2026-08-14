# Tasks: Binary LDPC v4 Backend Correction v1

## Phase 1: Frozen Correction

- [x] Add the versioned development evaluator with the sole production change
  of converting the float64 error channel to a Python list at the pinned
  decoder constructor boundary.
- [x] Add a production-constructor regression covering ndarray rejection,
  list acceptance, exact parameter shape/range, and one non-constructor-error
  development decode.
- [x] Do not edit historical v4 source, tests, or output artifacts.

## Phase 2: Versioned Immutable Package

- [x] Add v2 prepare/execute and read-only verifier CLIs with versioned
  identities, predecessor hashes, scoped source hashes, seven artifacts,
  no-overwrite/no-resume behavior, exact failure retention, and
  `decoder_reexecution=false`.
- [x] Add focused package tests for completed/non-ready, ready reconstruction,
  backend exception, cap/partial finalization, overwrite, predecessor/source/
  model/matrix/selection/outcome/run/report tampering, and verifier read-only
  behavior.

## Phase 3: Main-Thread Acceptance

- [x] Main thread reviews requirement fidelity and rejects any matrix, channel,
  policy, selection, gate, status, or evidence-scope drift.
- [x] Run focused correction tests and the existing v4, v1-v3, formal-real,
  and nonbinary regressions.
- [x] Run compilation, `git diff --check`, and frozen
  `src/`, `experiments/`, `tools/`, `results/`, historical v4 source, and
  historical output difference/hash checks.

## Phase 4: One Fresh Development Qualification

- [x] Main thread prepares and audits one fresh v2 production plan.
- [x] Execute exactly once and run the read-only verifier exactly once.
- [x] Require at least 495/512 exact frame successes in both strata and zero
  forbidden failures for readiness.
- [x] Preserve any failed/non-ready package; do not tune, rerun, or create
  synthetic/real production output in this change.
  The package passed at 510/512 nominal and 511/512 stress with zero forbidden
  failures. It remains immutable, and this change created no synthetic or real
  production output.

## Phase 5: Handoff and Memory

- [x] Update `AGENT_HANDOFF.md`, `docs/decision-log.md`,
  `AGENT_PROJECT_MEMORY.md`, and the binary/nonbinary handoff with exact
  commands, hashes, results, limitations, and next action.
- [x] Perform mandatory read-only memory triage.
