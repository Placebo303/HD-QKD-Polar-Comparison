# Tasks: real-ir-success-first

## 0. Coordination

- [x] Read `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`, `docs/ir-method-comparison-state-20260615.md`, and `docs/real-ir-success-first-plan-20260615.md`.
- [x] Confirm no task requires modifying original Polar logic under `src/`, `experiments/`, or `tools/`.
- [x] Choose additive output paths before running any command that writes outputs.

## 1. Define Real IR Success Contract

- [x] Add a documented real IR success classifier in the comparison layer or reporting layer.
- [x] Ensure `real_ir_success` requires independent verification success.
- [x] Ensure decode improvement without verification is not counted as success.
- [x] Preserve `reference`, `stub`, `unavailable`, `decode_failed`, `no_verified_success`, and related statuses.
- [x] Add tests for verified success, decode failure, verification failure, and reference/unavailable cases.

## 2. Build Representative Real-Frame Subset

- [x] Inventory existing frame-batch artifacts under `comparison_bench/outputs_comparison/` without recursive traversal into pytest temp directories.
- [x] Select a small representative subset covering raw SER regimes and at least one tractable point.
- [x] Write any new subset only under an additive path such as `comparison_bench/outputs_comparison/real_ir_success_first/`.
- [x] Record source artifact, filters, frame counts, dimensions, bin widths, and raw SER/BER summary.

## 3. Cascade Lite Real Success Baseline

- [x] Run or configure Cascade-lite on the representative real-frame subset.
- [x] Capture frame-level verification success and failure.
- [x] Capture leakage decomposition and relevant configuration values.
- [x] Identify the smallest stable configuration family, if one exists.
- [x] Document that this is simplified Cascade, not full industrial Cascade.

## 4. Layered LDPC Failure Diagnostics

- [x] Run or analyze Layered LDPC on the same representative subset.
- [x] Bucket failures by raw SER/BER, dimension, frame length, parity fraction, LLR mode, and bitplane rate mode.
- [x] Include per-bitplane diagnostics where available.
- [x] Distinguish decoder failure from verification failure.
- [x] Recommend whether LDPC should continue as candidate, diagnostic baseline, or deferred work.

## 5. qLDPC Reference Feasibility

- [x] Run or analyze qLDPC reference on the easiest representative real frames.
- [x] Preserve reference-grade labeling.
- [x] Report GF backend, syndrome weight, decoder status, verification result, and leakage.
- [x] State whether q-ary feasibility is demonstrated or blocked.

## 6. Evidence Audit

- [x] Write a docs audit summarizing representative inputs, commands/configs, outputs, and method status distribution.
- [x] Do not treat historical `run_errors_ir_v3.csv` rows as current state without timestamps/manifests.
- [x] Explicitly list blockers and non-selected methods.

## 7. Review

- [ ] Verify no original Polar baseline semantics changed — current reconciliation did not establish a historical change-by-change immutable-baseline audit.
- [ ] Verify no existing outputs were overwritten — manifests demonstrate additive destinations, but do not prove every historical write was non-overwriting.
- [x] Verify success requires verification.
- [x] Verify leakage and beta are not fabricated.
- [x] Verify failures remain visible in outputs and docs.

