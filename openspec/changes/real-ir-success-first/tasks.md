# Tasks: real-ir-success-first

## 0. Coordination

- [ ] Read `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`, `docs/ir-method-comparison-state-20260615.md`, and `docs/real-ir-success-first-plan-20260615.md`.
- [ ] Confirm no task requires modifying original Polar logic under `src/`, `experiments/`, or `tools/`.
- [ ] Choose additive output paths before running any command that writes outputs.

## 1. Define Real IR Success Contract

- [ ] Add a documented real IR success classifier in the comparison layer or reporting layer.
- [ ] Ensure `real_ir_success` requires independent verification success.
- [ ] Ensure decode improvement without verification is not counted as success.
- [ ] Preserve `reference`, `stub`, `unavailable`, `decode_failed`, `no_verified_success`, and related statuses.
- [ ] Add tests for verified success, decode failure, verification failure, and reference/unavailable cases.

## 2. Build Representative Real-Frame Subset

- [ ] Inventory existing frame-batch artifacts under `comparison_bench/outputs_comparison/` without recursive traversal into pytest temp directories.
- [ ] Select a small representative subset covering raw SER regimes and at least one tractable point.
- [ ] Write any new subset only under an additive path such as `comparison_bench/outputs_comparison/real_ir_success_first/`.
- [ ] Record source artifact, filters, frame counts, dimensions, bin widths, and raw SER/BER summary.

## 3. Cascade Lite Real Success Baseline

- [ ] Run or configure Cascade-lite on the representative real-frame subset.
- [ ] Capture frame-level verification success and failure.
- [ ] Capture leakage decomposition and relevant configuration values.
- [ ] Identify the smallest stable configuration family, if one exists.
- [ ] Document that this is simplified Cascade, not full industrial Cascade.

## 4. Layered LDPC Failure Diagnostics

- [ ] Run or analyze Layered LDPC on the same representative subset.
- [ ] Bucket failures by raw SER/BER, dimension, frame length, parity fraction, LLR mode, and bitplane rate mode.
- [ ] Include per-bitplane diagnostics where available.
- [ ] Distinguish decoder failure from verification failure.
- [ ] Recommend whether LDPC should continue as candidate, diagnostic baseline, or deferred work.

## 5. qLDPC Reference Feasibility

- [ ] Run or analyze qLDPC reference on the easiest representative real frames.
- [ ] Preserve reference-grade labeling.
- [ ] Report GF backend, syndrome weight, decoder status, verification result, and leakage.
- [ ] State whether q-ary feasibility is demonstrated or blocked.

## 6. Evidence Audit

- [ ] Write a docs audit summarizing representative inputs, commands/configs, outputs, and method status distribution.
- [ ] Do not treat historical `run_errors_ir_v3.csv` rows as current state without timestamps/manifests.
- [ ] Explicitly list blockers and non-selected methods.

## 7. Review

- [ ] Verify no original Polar baseline semantics changed.
- [ ] Verify no existing outputs were overwritten.
- [ ] Verify success requires verification.
- [ ] Verify leakage and beta are not fabricated.
- [ ] Verify failures remain visible in outputs and docs.

