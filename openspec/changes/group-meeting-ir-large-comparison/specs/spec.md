# Spec: Large IR Comparison for Group Meeting

## Requirements

### R1: Expanded Dataset
- Build an expanded representative subset from `real_sidecars_frame_batch.parquet` covering:
  - Dimensions: d=8, d=16, d=32
  - Bin widths (noise regimes): low (180ps), medium (100-120ps), high (50-60ps), each at least 1 point
  - At least 16 frames per dataset (batch has 64 available)
  - Frame lengths: 64, 128, 256 symbols (using build_long_frames.py from 64-symbol base)

### R2: Cascade-Lite Sweep
- Use optimized configs from previous optimization report:
  - Permutation modes: seeded_random
  - num_passes: 3, 4
  - Block schedules: [16,32,64,128], [12,6,24,13], [8,4,16,13]
  - Apply to all datasets at all frame lengths

### R3: Layered LDPC Sweep
- Parity threshold scan:
  - parity_fraction: 0.5, 0.67, 0.8, 0.9, 1.0
  - llr_mode: hard, bsc_estimated
  - bitplane_rate_mode: uniform
  - Apply to all datasets at all frame lengths

### R4: qLDPC Reference
- Run on low-noise subset only (d=8,d=16 at bw=180):
  - check_fraction: 0.33, 0.4, 0.5
  - row_weight: 3, 4
- Report n_frames_success/attempted; keep reference_only classification

### R5: Polar Existing Baseline
- Read historical results via polar_existing bridge for the same dataset_ids
- Mark clearly as "historical imported baseline, not same-run rerun"

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

### R7: Manifest
- `group_meeting_ir_manifest.json` with:
  - timestamp, git commit, command list
  - Config snapshots (per stage)
  - Source/output file hashes
  - No-overwrite confirmation

### R8: Group Meeting Report
- `docs/group-meeting-ir-analysis-20260615.md` with 16 sections

## Behavior

### B1: No Overwrites
- All new outputs under `group_meeting_ir_20260615/`
- No modifications to `real_ir_success_first/` or `src/`, `experiments/`, `tools/`
- Additive naming only

### B2: Semantic Preservation
- `real_ir_success` and `success_classification` must be preserved
- qLDPC stays `reference_only`
- Polar existing labeled as historical baseline
- beta_eff_empirical derived, never hand-filled
- No conversion of `reference`, `decode_failed`, etc. to `ok`

### B3: Graceful Degradation
- If a sweep method fails on a dataset, record the failure, don't crash
- Missing source files produce warnings, not errors

## Acceptance Criteria

- [ ] AC1: Expanded subset has ≥10 datasets (d=8,d=16,d=32, ≥3 noise regimes, ≥16 frames each)
- [ ] AC2: Longer-frame subsets at 128, 256 exist for all expanded datasets
- [ ] AC3: Cascade sweep runs on all datasets at all frame lengths
- [ ] AC4: LDPC sweep runs on all datasets at all frame lengths
- [ ] AC5: qLDPC reference runs on low-noise subset
- [ ] AC6: All 9 CSVs are generated with correct columns
- [ ] AC7: Manifest has source hashes, config snapshots, timestamp
- [ ] AC8: Group meeting report covers all 16 sections
- [ ] AC9: All 39 existing tests pass
- [ ] AC10: No modifications to src/, experiments/, tools/
