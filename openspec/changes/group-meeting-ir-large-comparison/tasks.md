# Tasks: group-meeting-ir-large-comparison

## Stage 1 — Dataset Build

- [ ] 1.1 Build expanded representative subset script (`cli/build_groupmeeting_dataset.py`):
  - Select datasets: d=8 (bw=50,120,180,200), d=16 (bw=60,100,180), d=32 (bw=60,100,180,40)
  - Extract 16 frames per dataset (all 64 avail, use first 16)
  - Write to `group_meeting_ir_20260615/groupmeeting_subset.parquet`
- [ ] 1.2 Build longer-frame subsets:
  - Run `build_long_frames.py --flen 128` on groupmeeting_subset
  - Run `build_long_frames.py --flen 256` on groupmeeting_subset

## Stage 2 — Sweep Configs

- [ ] 2.1 Create `configs/cascade_groupmeeting.yaml`:
  - frame_batch_path points to the 64, 128, 256 subsets
  - Configs: 3 schedules × 2 passes = 6 configs per dataset
- [ ] 2.2 Create `configs/ldpc_groupmeeting.yaml`:
  - 5 parity_fractions × 2 llr_modes = 10 configs per dataset
- [ ] 2.3 Create `configs/qldpc_groupmeeting.yaml`:
  - Low-noise subset (bw=180 points only), 3 check_fractions × 2 row_weights = 6 configs

## Stage 3 — Execute Sweeps

- [ ] 3.1 Run Cascade sweep: `python -m comparison_bench.cli.run_cascade_param_sweep --config configs/cascade_groupmeeting.yaml`
- [ ] 3.2 Run LDPC sweep: `python -m comparison_bench.cli.run_layered_ldpc_param_sweep --config configs/ldpc_groupmeeting.yaml`
- [ ] 3.3 Run qLDPC sweep: `python -m comparison_bench.cli.run_qldpc_param_sweep --config configs/qldpc_groupmeeting.yaml`

## Stage 4 — Analysis Package Generator

- [ ] 4.1 Create `cli/make_group_meeting_package.py` skeleton with argparse (`--input-dir`, `--output-dir`)
- [ ] 4.2 Implement `make_success_rate_by_method()` — AC1
- [ ] 4.3 Implement `make_leakage_by_method()` — AC2
- [ ] 4.4 Implement `make_runtime_by_method()` — AC3
- [ ] 4.5 Implement `make_cascade_best_config_by_dataset()` — AC4
- [ ] 4.6 Implement `make_ldpc_parity_threshold()` — AC5
- [ ] 4.7 Implement `make_qldpc_reference_feasibility()` — AC6
- [ ] 4.8 Implement `make_beta_by_frame_length()` — AC7
- [ ] 4.9 Implement `make_failure_region_summary()` — AC8
- [ ] 4.10 Implement `make_method_recommendation_matrix()` — AC9
- [ ] 4.11 Implement `make_manifest()` with source hashes and config snapshots
- [ ] 4.12 Wire up `main()`: load existing sweeps + polar_existing -> generate 9 CSVs + manifest
- [ ] 4.13 Run CLI to verify all 9 CSVs + manifest generated correctly

## Stage 5 — Report

- [ ] 5.1 Write `docs/group-meeting-ir-analysis-20260615.md` with all 16 sections
- [ ] 5.2 Verify all numbers in report match generated CSVs

## Stage 6 — Verification

- [ ] 6.1 Run `python -m pytest comparison_bench/tests -q` and confirm all pass
- [ ] 6.2 Verify no files in `src/`, `experiments/`, `tools/` were modified
- [ ] 6.3 Verify all outputs are under `group_meeting_ir_20260615/`
- [ ] 6.4 Verify qLDPC rows have `success_classification=reference_only`
- [ ] 6.5 Verify Polar existing rows are labeled as historical baseline
- [ ] 6.6 Create `tests/test_group_meeting_package.py` with at least 3 test cases
