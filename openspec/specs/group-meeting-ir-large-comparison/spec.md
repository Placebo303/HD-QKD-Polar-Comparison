## Historical implemented scope — group-meeting-ir-large-comparison

This section preserves only the archived, reviewed scope named below. It does not change the archived source. Current repository AGENTS.md and reboot handoff R1–R9 take precedence. This historical merge grants no new execution, acceptance, qualification, promotion, publication, decoder work, or probe restart.

<!-- Source: openspec/changes/archive/2026-10-04-group-meeting-ir-large-comparison-completed/specs/spec.md -->

### R6: Output CSVs (9 files)
All under `comparison_bench/outputs_comparison/group_meeting_ir_20260615/`:
1. `success_rate_by_method.csv`
2. `leakage_by_method.csv`
3. `runtime_by_method.csv`
4. `cascade_best_config_by_dataset.csv`
5. `ldpc_parity_threshold.csv`
6. `qldpc_reference_feasibility.csv`
7. `beta_by_frame_length.csv`
8. `failure_region_summary.csv`
9. `method_recommendation_matrix.csv`

<!-- Source: openspec/changes/archive/2026-10-04-group-meeting-ir-large-comparison-completed/specs/spec.md -->

### R7: Manifest
- `group_meeting_ir_manifest.json` with:
  - timestamp, git commit, command list
  - Config snapshots (per stage)
  - Source/output file hashes
  - No-overwrite confirmation

<!-- Source: openspec/changes/archive/2026-10-04-group-meeting-ir-large-comparison-completed/specs/spec.md -->

### R8: Group Meeting Report
- `docs/group-meeting-ir-analysis-20260615.md` with 16 sections

<!-- Source: openspec/changes/archive/2026-10-04-group-meeting-ir-large-comparison-completed/specs/spec.md -->

### B1: No Overwrites
- All new outputs under `group_meeting_ir_20260615/`
- No modifications to `real_ir_success_first/` or `src/`, `experiments/`, `tools/`
- Additive naming only

<!-- Source: openspec/changes/archive/2026-10-04-group-meeting-ir-large-comparison-completed/specs/spec.md -->

### B2: Semantic Preservation
- `real_ir_success` and `success_classification` must be preserved
- qLDPC stays `reference_only`
- Polar existing labeled as historical baseline
- beta_eff_empirical derived, never hand-filled
- No conversion of `reference`, `decode_failed`, etc. to `ok`

<!-- Source: openspec/changes/archive/2026-10-04-group-meeting-ir-large-comparison-completed/specs/spec.md -->

### B3: Graceful Degradation
- If a sweep method fails on a dataset, record the failure, don't crash
- Missing source files produce warnings, not errors
