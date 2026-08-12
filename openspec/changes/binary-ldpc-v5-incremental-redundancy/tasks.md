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

- [x] Implement the conditional synthetic package (P3-01--P3-09, T0--T2
  complete; independent main-thread acceptance pending review of the
  complete candidate and the official prepare).
- [x] Prepare once, main review, execute once, and verify once.

  Plan sha256 `c91171dc…17c10ab` (2026-08-01), production dev verify passed,
  execute 256/256 attempts (~45 s), read-only verify `status=verified`,
  `run_status=completed`, `decoder_reexecution=false`.
- [x] Require 126/128 nominal and stress with zero forbidden failures.

  Met: nominal 128/128, stress 128/128, forbidden failures 0,
  `promoted=true`, `ready_for_real_qualification=true`.

## Phase 4: Sealed real qualification

- [x] Implement and accept the conditional real package.
- [x] Prepare once only after strict synthetic promotion.
- [x] Main review, execute once, and read-only verify once.
- [x] Require 126/128 in bw120, bw180, and bw200 with zero forbidden failures.

  Official result (2026-08-12):
  `comparison_bench/outputs_comparison/formal_ir_methods/20260801_v2_binary_ldpc_v5_real/`
  (ten files, run_id=`binary_ldpc_v5_real_qualification_v1`, plan_sha256
  `a79cd16f19b968364a4c46fb4887f933eeb472e45c19d098a938ae5dc58ad01b`).
  Report: `promoted=true`, `run_status=completed`,
  `decoder_reexecution=false`. 384/384 total verified_success: bw120, bw180,
  and bw200 each 128/128 with zero forbidden failures — all layers passed.
  Execute ~5m12s, read-only verify ~4m29s, run in a detached background
  process. Chain: partition lock (20260731) → v5 dev (V5-C2, 1536/1536) →
  v5 synthetic (256/256) → v5 real (384/384), each once with read-only
  verification. CSV role uses the frozen encoder's allowed `real` value
  (contract literal `real_confirmation` is rejected by the encoder; Phase 3
  precedent). Three latent bugs masked by test mocks were found and fixed
  during implementation (synthetic_dir directory semantics, generator
  empty-dict check, missing root_id); these fixes are semantic-preserving.

## Phase 5: Durable state

- [x] Update handoff, decision log, project memory, comparison eligibility,
  and binary/nonbinary parallel status.

  Done 2026-08-12: AGENT_HANDOFF.md current-state updated (binary LDPC v5
  Phase 4 REAL PROMOTED, 384/384), docs/decision-log.md entry
  `2026-08-12: Binary LDPC v5 sealed real qualification promoted on real
  10 dB ttbin` appended, AGENT_PROJECT_MEMORY.md binary LDPC section updated
  (v5 real promotion complete; v4 real transfers retained as failure
  evidence; comparison eligibility: v5 10 dB domain eligible, other
  domains/methods unchanged), parallel status updated.
- [x] Perform mandatory memory triage.

  Done 2026-08-12: memory triage completed. Persisted: AGENT_PROJECT_MEMORY.md
  section 31 gained two reusable process lessons (detached background process
  pattern for long prepare/execute/verify stages; test mocks masking
  production-path defects — keep a real-path smoke instead of mocking core
  functions). Discarded: no speculative or new numeric content; all hashes,
  counts, and timings remain exactly as recorded in the sealed package.
