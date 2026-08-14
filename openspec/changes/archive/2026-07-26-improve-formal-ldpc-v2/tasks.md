# Tasks: Improve Formal LDPC v2

## Phase 1: Backend and Development Contract

- [x] Probe and freeze exact `ldpc==2.4.1` constructors for OSD-0/0 and
  OSD-CS/1,2; record unsupported variants without fallback. BP+LSD and OSD-E
  are explicitly excluded.
- [x] Add `ldpc_formal_v2` as an additive identity while preserving all v1
  public behavior and evidence.
- [x] Implement the exact nine-policy grid, compact-JSON policy hash, global
  deterministic selection tuple `(successes, disclosure, frozen decoder
  complexity, policy_id)`, diagnostic-only runtime, and frozen rate-margin
  mapping using sacrificed calibration only.
- [x] Add tests proving global-policy freezing, no per-frame oracle, exact
  decoder parameters, disclosure accounting, and retained failure statuses.

## Phase 2: Deterministic Candidate Codebooks

- [x] Implement 16 deterministic nested 56x64 master candidates per plane,
  four exact prefixes, canonical HGF2V1 encoding, and domain-separated seeds.
- [x] Implement rank, duplicate/zero-column, weight, 4-cycle, and sacrificed
  64-vector low-weight probe metrics plus exhaustive weight-1/2 syndrome
  collision counts. Name the proxy `probe_unique_syndrome_count`; do not label
  it decoded or verified success.
- [x] Persist an additive screening manifest and select one master candidate
  per plane by the frozen lexicographic score; prove hash, nesting, and
  no-overwrite behavior.

## Phase 3: Fresh Qualification

- [x] Preserve v1 invalid integration run bytes and add its exact
  `invalid_run_notice.json`; fix v2-specific entry validation and use only the
  fresh v2 run ID/seeds from design.
- [x] Add a dedicated v2 runner with explicit fresh `--output-dir`, exact
  seeds/order/caps and seven-artifact failure-finalized contract from design;
  do not branch or modify the v1 runner.
- [x] Add a strict read-only verifier reconstructing generation, calibration,
  screening/codebook/policy selection, seed binding, transcript/disclosure,
  denominators, and promotion gates.
- [x] Freeze and independently review a fresh synthetic plan before execution.
- [x] Materialize the screened codebook, run the sacrificed nine-policy grid,
  and freeze one global policy before confirmation.
- [x] Run v2 confirmation exactly once and verify its complete seven-artifact
  hash/transcript DAG.
- [x] Require at least 31/32 verified successes in both p=.01 and p=.02 with
  zero unclassified/internal/provenance/accounting failures.
  - Observed: 28/32 and 29/32, zero unclassified/internal/provenance/accounting
    failures. The gate was applied and v2 is non-promoted.
- [x] If and only if promoted, create and review a fresh real LDPC lock.
  - Not authorized: the synthetic gate failed, so no real lock was created.
- [x] Run one fresh real qualification and require 60/60 verified successes.
  - Not run by design because synthetic promotion is a prerequisite.

## Phase 4: Review and Handoff

- [x] Main thread, not Terra, performs specification interpretation, plan
  changes, acceptance decisions, and final scientific review.
- [x] Run focused tests, safe comparison regression, `git diff --check`, frozen
  directory diff checks, and read-only artifact verifiers.
- [x] Record bounded decisions and limitations in the decision log, project
  memory, and `AGENT_HANDOFF.md`.
- [x] Archive only after verified evidence supports every checked task.
