# Design: group-meeting-ir-large-comparison

## Overview

A multi-stage pipeline that (1) builds an expanded real-data frame subset from the existing batch, (2) runs Cascade/LDPC/qLDPC sweeps on it at multiple frame lengths, (3) imports Polar historical baseline, and (4) consolidates all results into 9 comparison CSVs + manifest + group meeting report.

## Goals

1. **Broader coverage**: d=8, d=16, d=32 across low/medium/high noise, ≥16 frames each
2. **Multi-frame-length**: 64, 128, 256 symbols for meaningful scalability analysis
3. **Traceable**: Full manifest with per-stage config snapshots and source hashes
4. **Honest semantics**: Cascade → "preferred non-Polar candidate", LDPC → "control baseline", qLDPC → "reference only", Polar → "historical imported baseline"

## Constraints

- No modifications to `src/`, `experiments/`, `tools/`
- All outputs under `comparison_bench/outputs_comparison/group_meeting_ir_20260615/`
- No overwriting existing sweep or benchmark outputs
- Do not run original Polar pipeline (use existing polar_existing bridge)
- qLDPC must stay `reference_only`

## Technical Approach

### Stage 1: Dataset Build

From `real_sidecars_frame_batch.parquet` (121 datasets, 64 symbols/frame, 64 frames/dataset):

1. Build expanded representative subset (16+ frames per dataset):
   - d=8: bw=50 (high), bw=120 (medium), bw=180 (low)
   - d=16: bw=60 (high), bw=100 (medium), bw=180 (low)
   - d=32: bw=60 (high), bw=100 (medium), bw=180 (low)
   - Plus d=8 bw=200 (very low noise) and d=32 bw=40 (very high noise) if available
   - Total: ~12 datasets × 16 frames = 192 frames

2. Build longer frames using `build_long_frames.py`:
   - Frame lengths: 128, 256 symbols
   - These reuse the same dataset_ids but with longer symbol windows

### Stage 2: IR Method Sweeps

Use existing sweep CLI infrastructure:

1. **Cascade-lite** (`run_cascade_param_sweep.py`):
   - Config: Same optimized configs used in previous real_ir_success_first sweep
   - Apply to all expanded datasets at all frame lengths

2. **Layered LDPC** (`run_layered_ldpc_param_sweep.py`):
   - Config: parity_fraction scan {0.5, 0.67, 0.8, 0.9, 1.0}
   - llr_mode: hard, bsc_estimated
   - bitplane_rate_mode: uniform
   - Apply to all expanded datasets at all frame lengths

3. **qLDPC reference** (`run_qldpc_param_sweep.py`):
   - Low-noise subset only (bw=180 points)
   - check_fraction: 0.33, 0.4, 0.5; row_weight: 3, 4

### Stage 3: Polar Existing Baseline

Use `polar_existing_bridge.py` to read historical results for the matching dataset_ids.
Results marked as "historical imported baseline" in reports.

### Stage 4: Analysis CSV Generation

CLI `make_group_meeting_package.py` consolidates all sweep outputs into 9 CSVs:

1. **success_rate_by_method.csv**: Per-method success stats grouped by dim/bw/frame_len
2. **leakage_by_method.csv**: Per-dataset leakage with accounting notes
3. **runtime_by_method.csv**: Per-dataset runtime and throughput
4. **cascade_best_config_by_dataset.csv**: Best cascade config per dataset (min leak)
5. **ldpc_parity_threshold.csv**: Min successful parity_fraction per dataset
6. **qldpc_reference_feasibility.csv**: Reference feasibility matrix
7. **beta_by_frame_length.csv**: Beta efficiency vs frame length
8. **failure_region_summary.csv**: Failure analysis by region/method
9. **method_recommendation_matrix.csv**: Final recommendations

### Stage 5: Manifest & Report

- `group_meeting_ir_manifest.json`: Auto-generated with hashes and configs
- `docs/group-meeting-ir-analysis-20260615.md`: 16-section report

## Alternatives Considered

### Alt 1: Use full 121-dataset batch
- **Pros**: Maximum coverage
- **Cons**: Sweep time would be prohibitive (days)
- **Decision**: 12-dataset expanded subset balances coverage with compute time

### Alt 2: Run separate analysis scripts, not a CLI
- **Pros**: Faster to write
- **Cons**: Not reproducible, hard to hand off
- **Decision**: Single `make_group_meeting_package.py` CLI for reproducibility

### Alt 3: Reuse existing sweep results only
- **Pros**: Zero compute time
- **Cons**: Only 6 datasets at 4 frames — insufficient for group meeting
- **Decision**: Run new sweeps on expanded data

## Impacted Files / Modules

| File | Action | Description |
|------|--------|-------------|
| `cli/make_group_meeting_package.py` | Create | Consolidation CLI for 9 CSVs + manifest |
| `tests/test_group_meeting_package.py` | Create | Tests for the package generator |
| `configs/cascade_groupmeeting.yaml` | Create | Cascade sweep config for expanded set |
| `configs/ldpc_groupmeeting.yaml` | Create | LDPC sweep config for expanded set |
| `configs/qldpc_groupmeeting.yaml` | Create | qLDPC sweep config (low-noise subset) |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Sweeps take too long | Medium | High | Limit to 12 datasets × 3 frame lengths; use 16 frames each |
| d=32 batch data not available | Low | Medium | Check batch first; fall back to d=8,d=16 only |
| Longer frames (256) have too few pairs | Medium | Medium | build_long_frames handles tail drops; check frame count per dataset |
| LDPC fails on all d=32 points | Medium | Low | Expected for high noise; document failure region |
| Polar bridge can't match dataset_ids | Medium | Low | Map via dimension+bin_width if dataset_id doesn't match 