# Tasks: Binary LDPC v4 10 dB Transfer Qualification v1

## Phase 1: Frozen implementation packet

- [x] Freeze source, prerequisites, selection, isolation, gates, artifacts,
  stop rules, tests, and operator return conditions in `task-packet.md`.
- [x] Implement P1-01 through P1-08 without changing requirements.
- [x] Main thread independently accepts T0 through T3 and confirms no
  unauthorized production output exists.

## Phase 2: One production qualification

- [x] Retain the rejected v1 prepare as immutable `invalid_pre_execute`; it
  contains no outcomes and must never be executed.
- [x] Implement and accept `prepare-correction-v2.md` C2-01 through C2-T3.
- [x] Prepare v2 exactly once in a fresh additive output directory.
- [x] Main thread reconstructs and accepts the plan and source lock.
- [x] Execute exactly once and run the read-only verifier exactly once.
- [x] Retain the promoted or non-promoted nine-file package without tuning,
  deletion, overwrite, or rerun.

## Phase 3: Durable state

- [ ] Update handoff, decision log, project memory, and binary/nonbinary
  parallel handoff with exact hashes, outcomes, and claim boundaries.
- [ ] Perform mandatory memory triage.
