# Tasks: consolidate-real-ir-evidence-package

## Implementation

- [x] 1.1 Create CLI skeleton: `comparison_bench/src/comparison_bench/cli/make_expanded_evidence_package.py` with argparse, `--input-dir`, `--output-dir` args, and `main()` entry point
- [x] 1.2 Implement `compute_file_hash(path) -> str` helper using `hashlib.sha256`
- [x] 1.3 Implement `get_git_commit() -> str` helper using `subprocess.run(["git", "rev-parse", "--short", "HEAD"])`
- [x] 1.4 Implement `load_csv(input_dir, filename) -> pd.DataFrame | None` with graceful degradation (return None if missing)
- [x] 1.5 Implement `make_cascade_optimized(df) -> pd.DataFrame`: filter `real_ir_success=True`, group by `dataset_id`, select min `leak_EC_actual_bits`
- [x] 1.6 Implement `make_ldpc_optimized(df) -> pd.DataFrame`: same pattern as cascade
- [x] 1.7 Implement `make_qldpc_reference(df) -> pd.DataFrame`: group by `dataset_id, q, frame_len_symbols`, select max `n_frames_success`, preserve `success_classification`
- [x] 1.8 Implement `make_scalability_summary(real_df, synth_df) -> pd.DataFrame`: concat, deduplicate by `dataset_id`
- [x] 1.9 Implement `make_method_comparison(cascade_df, ldpc_df, scalability_df) -> pd.DataFrame`: group by `frame_len_symbols`, count successes, average metrics
- [x] 1.10 Implement `make_failure_analysis(cascade_df, ldpc_df) -> pd.DataFrame`: filter `real_ir_success=False`, group by method/dimension/bin_width, count
- [x] 1.11 Implement `make_manifest(input_dir, output_dir, output_files) -> dict`: compute source hashes, read source manifest, build manifest dict
- [x] 1.12 Implement `write_outputs(output_dir, outputs_dict)`: write all CSVs and manifest JSON
- [x] 1.13 Wire up `main()`: parse args, load inputs, generate outputs, write, print summary
- [x] 1.14 Add docstrings and type hints to all functions

## Verification

- [x] 2.1 Create `tests/test_evidence_package.py` with pytest fixtures for temp input/output dirs
- [x] 2.2 Test `compute_file_hash` returns deterministic SHA-256
- [x] 2.3 Test `make_cascade_optimized` selects correct min-leakage row per dataset_id
- [x] 2.4 Test `make_ldpc_optimized` selects correct min-leakage row per dataset_id
- [x] 2.5 Test `make_qldpc_reference` preserves `success_classification` from source
- [x] 2.6 Test `make_scalability_summary` merges real + synthetic without duplicates
- [x] 2.7 Test `make_method_comparison` groups correctly by frame_len_symbols
- [x] 2.8 Test `make_failure_analysis` counts failures by method/dimension/bin_width
- [x] 2.9 Test `make_manifest` includes source hashes and config snapshots
- [x] 2.10 Test CLI end-to-end: run on existing real_ir_success_first data, verify outputs exist
- [x] 2.11 Test idempotency: run twice, verify identical outputs
- [x] 2.12 Run `python -m pytest comparison_bench/tests -q` and confirm all pass

## Verification Notes
- CLI runs successfully on existing real_ir_success_first data, generates 7 output files including cascade_optimized_summary.csv with 6 correct rows, manifest with source hashes and git commit.
- All 37 tests pass (22 new + 15 existing). New tests cover: compute_file_hash, load_csv, make_cascade_optimized, make_ldpc_optimized, make_qldpc_reference, make_scalability_summary, make_method_comparison, make_failure_analysis, make_manifest, write_outputs, end-to-end CLI, idempotency, graceful degradation. Full test suite passes with 0 failures.
