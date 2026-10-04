# Tasks: Formal Nonbinary LDPC v4 Incremental Redundancy

## Phase 0: Planning freeze

- [x] `V4-P0` Bind immutable v1-v3 evidence and exact reconstructed v3
  codebook; freeze allowed/forbidden scope.
- [x] `V4-P1` Freeze control/warm/restart policies, stage transitions,
  32→40 and 40→48 prefixes, state semantics, and terminal statuses.
- [x] `V4-P2` Freeze fresh roots, 64/128 role split, generation order,
  identity isolation, and two-attempt seed binding.
- [x] `V4-P3` Freeze stage/tag/decision transcript lineage, exact leakage,
  public control, conditional outcome epsilon, and protocol union bound.
- [x] `V4-P4` Freeze eligibility, selection, 63/64 readiness, confirmation
  non-materialization, and diagnostic non-selection.
- [x] `V4-P5` Freeze 128/128 promotion, finite-sample wording, no-rerun,
  no-tuning, and N4/sidecar/`.ttbin` hard gates.
- [x] `V4-P6` Freeze deterministic resources, monitoring-only wall time,
  artifacts, invalid-run retention, scoped provenance, official-root absence,
  and pre-run acceptance.

## Phase 1: Candidate implementation

- [x] `V4-I0` Implement pure v4 internal state, stage runner, warm extension,
  restart extension, diagnostic exclusion, and fail-closed binding.
- [x] `V4-I1` Implement exact two-attempt verification orchestration,
  transcript lineage, disclosure accounting, and terminal result schema.
- [x] `V4-I2` Prove candidate code cannot access Alice truth, cannot serialize
  decoder state, cannot extend twice, and cannot extend prohibited failures.

## Phase 2: Qualification implementation

- [x] `V4-I3` Implement plan-only, execute, invalid-run retention, selection,
  conditional confirmation, eight artifacts, and strict read-only replay.
- [x] `V4-I4` Prove roots/frames/arrays/atomic keys/seeds are fresh and
  confirmation material is absent until readiness.
- [x] `V4-I5` Implement deep byte/semantic/manifest/transcript/accounting/gate
  tamper rejection and forbidden-diagnostic rejection with explicit fake
  runners in tests.

## Phase 3: Main-thread acceptance before data

- [x] `V4-T0` Compile/import, exact codebook reuse, tiny-math state transition,
  diagnostic exclusion, deterministic resources, storage and accounting pass.
- [x] `V4-T1` Focused candidate/unit/tamper tests pass, including warm retain,
  restart reset, both allowed triggers, all forbidden triggers and caps.
- [x] `V4-T2` Complete fake qualification and strict replay pass under a fresh
  writable UUID root with pytest cache disabled.
- [x] `V4-T3` v1-v3 regression, independent reviewer, scoped task manifest,
  untracked hashes, frozen-directory checks, and no official v4 output pass.
- [x] `V4-A0` The fixed-seed non-qualification probe confirms operational
  practicality and deterministic work/memory bounds; main thread records
  acceptance before plan creation.

Acceptance evidence recorded 2026-07-31:

- T0-T2: `py_compile` passed and the focused v4 suite passed 20/20 with
  cache disabled; the suite includes complete fake execution, read-only replay,
  invalid partial retention, and layered tamper rejection.
- T3: the v1-v3 algorithm/structure regression passed 47/47; independent final
  review returned `NO_FINDINGS`; the five implementation/test files matched the
  frozen task manifest, frozen baseline directories were unchanged, and the
  official v4 root was absent. The older v3 qualification suite is not
  repeatable after its immutable official v3 package exists: its own historical
  identity guard rejects the reused v3 roots. That expected 14-failure result is
  retained and was not bypassed by editing old tests or evidence.
- A0: fixed seed `202607559999`, p=0.30, production stage 1 and forced
  warm/restart stage 2 all returned `syndrome_consistent` in two iterations.
  Observed times were 10.27 s, 14.66 s, and 16.02 s; peak traced Python memory
  was 6,455,226 bytes. This probe created no qualification artifact.

## Phase 4: Conditional synthetic execution

- [x] `V4-A1` Create the one no-overwrite plan, review it without decoding,
  execute at most once, and invoke strict read-only replay at most once.
- [ ] `V4-A2` If readiness is below 63/64 in either stratum, retain immutable
  development evidence and stop without confirmation.
- [x] `V4-A3` If confirmation is below 128/128 in either stratum, retain the
  immutable non-promotion and stop without N4.

Formal outcome recorded 2026-07-31:

- The one plan contained only 128 development frames, three policies, and 640
  unique development seed records; all historical identity intersections were
  empty. Execute ran once and exited 0 in 3,384 s. Strict read-only replay ran
  once and exited 0 in 3,524 s with `verified=True`, `run_status=completed`.
- Development readiness passed and selected `nbldpc_v4_ir_warm`: 64/64 at
  p=0.20 and 63/64 at p=0.30.
- Confirmation was 128/128 at p=0.20 and 120/128 at p=0.30, with eight
  `decode_failed` and zero prohibited failures. Therefore `promoted=false`.
  `V4-A2` was not applicable; `V4-A3` is the terminal gate. No rerun, tuning,
  N4, sidecar, or real `.ttbin` work is authorized by this change.

## Phase 5: Durable state

- [x] `V4-D0` Update handoff, current task, decision log and project memory
  with verified facts and explicit next boundary.
- [x] `V4-D1` Perform mandatory memory triage.
