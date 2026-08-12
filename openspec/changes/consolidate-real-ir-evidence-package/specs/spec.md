# Spec: Evidence Package CLI

## Requirements

### R1: Input Reading
- Read `cascade_param_sweep_results.csv` from `real_ir_success_first/`
- Read `layered_ldpc_param_sweep_results.csv` from `real_ir_success_first/`
- Read `qldpc_param_sweep_results.csv` from `real_ir_success_first/`
- Optionally read `scalability/ir_benchmark_results.csv` if present
- Optionally read `scalability_synth/ir_benchmark_results.csv` if present
- Read `ir_v3_run_manifest.json` from `real_ir_success_first/`

### R2: Selection Logic
- Cascade/LDPC optimized summaries must select minimum `leak_EC_actual_bits` **only** among `real_ir_success=True` rows
- qLDPC must remain `reference_only` unless the source row says otherwise
- If a source file is missing, skip that output (do not error)

### R3: Output Generation
All outputs go under `comparison_bench/outputs_comparison/expanded_real_ir_20260615/`:
- `cascade_optimized_summary.csv`
- `ldpc_optimized_summary.csv`
- `qldpc_reference_summary.csv`
- `scalability_summary.csv`
- `method_comparison_by_frame_len.csv`
- `failure_region_analysis.csv`
- `expanded_evidence_manifest.json`

### R4: Manifest
The manifest must include:
- Source file paths
- SHA-256 hashes of each source file
- Source manifest config snapshots (from `ir_v3_run_manifest.json`)
- Output file list
- Timestamp and git commit

### R5: No Overwrites
- Must not overwrite anything under `real_ir_success_first/`
- Must not run new sweeps
- If output directory exists, merge/overwrite only generated files

## Behavior

### B1: CLI Invocation
```bash
python -m comparison_bench.cli.make_expanded_evidence_package \
  --input-dir comparison_bench/outputs_comparison/real_ir_success_first \
  --output-dir comparison_bench/outputs_comparison/expanded_real_ir_20260615
```

### B2: Graceful Degradation
If a source file is missing, skip its corresponding output and log a warning.

### B3: Idempotency
Running twice produces identical outputs (same content, same hashes).

## Acceptance Criteria

- [x] AC1: `cascade_optimized_summary.csv` contains only `real_ir_success=True` rows with minimum `leak_EC_actual_bits` per `dataset_id`
- [x] AC2: `ldpc_optimized_summary.csv` contains only `real_ir_success=True` rows with minimum `leak_EC_actual_bits` per `dataset_id`
- [x] AC3: `qldpc_reference_summary.csv` preserves `success_classification` from source
- [x] AC4: `scalability_summary.csv` merges real and synthetic scalability data
- [x] AC5: `method_comparison_by_frame_len.csv` groups by `frame_len_symbols` with success counts and average metrics
- [x] AC6: `failure_region_analysis.csv` counts failures by method/dimension/bin_width
- [x] AC7: `expanded_evidence_manifest.json` contains source hashes and config snapshots
- [ ] AC8: pytest passes with ≥3 test cases covering selection correctness — test source has the cases, but its fixed tracked workspace fixture was not safely rerun.
- [ ] AC9: No source files are modified — current matching manifest hashes establish provenance after generation, not a before/after non-modification proof.
- [x] AC10: CLI runs without errors on existing real_ir_success_first data
