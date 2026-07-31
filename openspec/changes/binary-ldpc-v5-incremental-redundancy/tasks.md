# Tasks: Binary LDPC v5 Incremental Redundancy

## Phase 1: Source partition and method

- [x] Implement and independently accept frozen packet
  `phase1-task-packet.md`.
- [x] Create the immutable production partition lock before any v5 decoding.
- [x] Main thread verifies role isolation, capacity, predecessor exclusion,
  source hashes, and no confirmation access from development APIs.

## Phase 2: Sacrificed development

- [x] Implement and independently accept frozen packet
  `phase2-task-packet.md`.
- [x] Prepare once, main review, execute once, and verify once.
- [x] Require a selected candidate meeting 510/512 in every real stratum or
  stop without synthetic output.

  Verified: V5-C2 selected (1536/1536 verified_success; 512/512 per stratum,
  zero fallback). Robustness (2026-08-01): E1 new-seed rerun 768/768,
  E3 model-consistent nominal-SER 0.2430 768/768, E2 OOD uniform-noise control
  0/1152 as expected. Two approved semantic-preserving speedup deviations
  (lock validated once + cached source lock + progress logs) recorded in the
  decision log with the single re-execute approval.

## Phase 3: Fresh synthetic confirmation

- [ ] Implement and accept the conditional synthetic package.
- [ ] Prepare once, main review, execute once, and verify once.
- [ ] Require 126/128 nominal and stress with zero forbidden failures.

## Phase 4: Sealed real qualification

- [ ] Implement and accept the conditional real package.
- [ ] Prepare once only after strict synthetic promotion.
- [ ] Main review, execute once, and read-only verify once.
- [ ] Require 126/128 in bw120, bw180, and bw200 with zero forbidden failures.

## Phase 5: Durable state

- [ ] Update handoff, decision log, project memory, comparison eligibility,
  and binary/nonbinary parallel status.
- [ ] Perform mandatory memory triage.
