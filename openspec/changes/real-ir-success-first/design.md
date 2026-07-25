# Design: real-ir-success-first

## Design Principle

Real IR success is a protocol-level property, not just a metric row.

A method is useful only if it can take real Alice/Bob frames, disclose only accounted public information, produce a corrected Bob frame, and pass independent verification. The design should therefore add a success-classification layer around existing method outputs before expanding sweeps.

## Real IR Success Model

A method result should be classified using these concepts:

- `decode_success`: the decoder reports a correction attempt succeeded.
- `verify_success`: independent verification confirms Alice/Bob agreement.
- `real_ir_success`: true only when verification succeeds and method status is compatible with executable success.
- `leakage_accounted`: leakage fields are present or explicitly labeled approximate/unavailable.
- `status_honest`: failed/reference/unavailable states are preserved.

Suggested classification values:

- `real_ir_success`
- `decode_improved_but_unverified`
- `verified_failure`
- `decode_failed`
- `method_unavailable`
- `reference_only`
- `invalid_accounting`

These labels can be introduced as additive reporting columns or audit outputs. Existing schema names must not be silently changed.

## Representative Frame Strategy

Use a small representative set before any broad sweep.

Selection should cover:

- low, medium, and high raw SER regimes;
- more than one dimension when available;
- at least one historically tractable real sidecar-derived point;
- frame counts small enough for repeated iteration.

Preferred input source:

- existing frame-batch artifacts such as `comparison_bench/outputs_comparison/real_sidecars_frame_batch.parquet`.

If a new subset is written, use an additive path such as:

- `comparison_bench/outputs_comparison/real_ir_success_first/`

## Method-Specific Design

### Cascade Lite

Use as the first non-Polar real success candidate.

Required reporting:

- verified success by frame;
- transcript/leakage decomposition;
- parity/bisection/verification disclosure counts;
- configuration values such as block schedule, passes, permutation mode, mapping, and seed.

Do not claim full Cascade.

### Layered LDPC Lite

Use as failure-diagnosis target.

Required reporting:

- raw SER/BER bucket;
- dimension and frame length;
- bit-plane BER diagnostics;
- parity fraction;
- LLR mode;
- bitplane rate mode;
- decoder failure versus verification failure;
- post-IR error behavior.

Do not mark failed or unverified results as `ok`.

### qLDPC Reference

Use as q-ary feasibility probe.

Required reporting:

- q/dimension;
- GF backend status;
- syndrome weight;
- decoder attempt status;
- verification result;
- leakage accounting.

Keep `reference` wording unless the implementation becomes production-grade through a separate approved change.

## Output And Manifest Policy

- Do not overwrite existing standard outputs.
- Prefer new additive output subdirectories for this change.
- Every run used for evidence should have a config path, output path, timestamp, and manifest.
- Diagnostic outputs may be CSV/Parquet, but missing optional dependencies must be handled consistently with current table-store policy.

## Test Strategy

Tests should cover:

- verified success classification;
- decode failure classification;
- verification failure classification;
- reference/unavailable status preservation;
- leakage/beta consistency checks;
- representative config parsing if new configs are added.

Synthetic fixtures are acceptable for unit tests, but at least one documented smoke path should target existing real frame artifacts when available.

## Non-Goals

- Full raw-data regeneration.
- Full industrial Cascade.
- Production qLDPC.
- Replacing the original Polar pipeline.
- Hiding failures to produce comparable-looking tables.

