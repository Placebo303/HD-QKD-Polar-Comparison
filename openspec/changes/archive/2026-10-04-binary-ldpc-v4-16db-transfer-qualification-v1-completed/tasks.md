# Tasks: Binary LDPC v4 16 dB Transfer Qualification v1

## Phase 1: Source and Relocation Adapter

- [x] Add a versioned read-only 16 dB source/relocation module under
  `comparison_bench/`; do not modify the v3 bridge or frozen baseline.
- [x] Bind the exact raw, provenance-snapshot, sidecar, and baseline
  materializer-source hashes specified in `design.md`.
- [x] Reject each independently tampered pre-registered file hash before
  selection; recording a current hash without comparing it to the frozen
  value is insufficient.
- [x] Reconstruct the one-prefix path relocation, array/domain/framing
  contract, source-aware identities, payload uniqueness, and deterministic
  128-frame-per-stratum selection.

## Phase 2: Transfer Runner and Verifier

- Frozen operator packet:
  `phase2-task-packet.md` (`P2-C01`--`P2-T05`).
- Operational performance correction:
  `phase2-performance-correction.md` (`P2P-01`--`P2P-06`).
- [x] Add versioned conditional prepare/execute and read-only verifier CLIs.
- [x] Require the exact promoted corrected-v2 synthetic prerequisite and
  preserve all method, cap, transcript, leakage, status, and gate semantics.
- [x] Generate fresh isolated real roots/seeds and bind the exact 16 dB source
  lock before any decoding.
- [x] Complete and accept `P2P-01`--`P2P-06` so strict production prepare can
  finish without weakening replay.

## Phase 3: Focused Acceptance

- [x] Test exact source acceptance; path/hash/suffix/competing-source/
  provenance/metadata/array/tail/payload tampering; no-overwrite; capacity;
  deterministic selection; root/seed isolation; partial failure; accounting;
  transcript/public-payload tampering; and read-only reconstruction.
- [x] Main thread reviews requirement fidelity and runs focused plus
  binary-v1-v4/formal-real regression, compilation, frozen-directory diff,
  historical artifact/source hashes, and no-production-output checks.

## Phase 4: One 16 dB Transfer Qualification

- [x] Prepare exactly once and review the immutable source lock and plan.
- [x] Execute exactly once and verify exactly once.
- [ ] Require 126/128 in all three strata with zero forbidden failures.
- [x] Retain promoted or non-promoted evidence without tuning or rerun.

## Phase 5: Handoff and Memory

- [ ] Update handoff, project memory, decision log, and parallel-lane status
  with hashes, results, scope, and the still-blocked 20 dB route.
- [ ] Perform mandatory read-only memory triage.
