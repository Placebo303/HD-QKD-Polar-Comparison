# Information Reconciliation Comparison Benchmark

This directory is an additive comparison layer. It is not the original Polar main workflow. The copied Polar pipeline in `src/`, `tools/`, and `experiments/` is treated as a frozen baseline.

The benchmark connects to Polar only by reading existing result files or, when explicitly configured, calling the existing Polar CLI from an outer wrapper. It does not move, rename, rewrite, or inject benchmark logic into the Polar implementation.

For the bounded frame-identical final executable-candidate workflow, see
[`docs/final_ir_method_selection_runbook.md`](docs/final_ir_method_selection_runbook.md).

## Method Status

- `polar_existing`: production baseline wrapper. It first reads existing Polar outputs such as `real_polar_max_pie_grid.csv`, `polar_e2e_results.csv`, `actual_ir_point_table.csv`, or `polar_diag_summary.csv`.
- `cascade_lite`: executable only after a supported Cascade backend is installed and wired. Until then it reports `method_status=unavailable` and does not fake leakage or decode success.
- `layered_ldpc_lite`: executable only after a supported LDPC backend is installed and wired. Until then it reports `method_status=unavailable`.
- `qldpc_reference`: reference stub. It reserves hooks for synthetic, MATLAB/Octave, and non-binary LDPC integrations and reports `method_status=stub` by default.

## Install

The root environment is unchanged. Optional comparison dependencies are listed separately:

```powershell
python -m pip install -r comparison_bench/requirements-comparison.txt
```

The code can run the synthetic smoke path without PyYAML or pyarrow by using built-in fallbacks for the simple bundled YAML and local frame table storage.

## Synthetic Smoke

```powershell
python -m comparison_bench.src.comparison_bench.cli.smoke_test --config comparison_bench/configs/benchmark_synth.yaml
```

This writes only under `comparison_bench/outputs_comparison/`:

- `ir_benchmark_results.csv`
- `ir_frame_results.parquet`
- `run_manifest.json`
- `ir_method_summary.csv`

## Real Data Benchmark

Prepare a paired table with `frame_id`, `pair_idx`, `alice_symbol`, and `bob_symbol` columns, or supported aliases documented in `docs/data_contract.md`.

```powershell
python -m comparison_bench.src.comparison_bench.cli.build_dataset --input INPUT.csv --output comparison_bench/outputs_comparison/frame_batch.parquet --dimension 8 --frame-len-symbols 256
python -m comparison_bench.src.comparison_bench.cli.run_benchmark --config comparison_bench/configs/benchmark_realdata.yaml
python -m comparison_bench.src.comparison_bench.cli.compare_methods --input comparison_bench/outputs_comparison/ir_benchmark_results.csv --output comparison_bench/outputs_comparison/ir_method_summary.csv
```

## Merge With Security CSV

Use `comparison_bench.src.comparison_bench.pipeline.merge_with_security.merge_ir_with_security`. The merge is read-only with respect to the old security pipeline and joins on available shared keys including `dataset_id`, `loss_db`, `dimension`, `bin_width_ps`, `threshold_ps`, and `effective_pairing_window_ps`.
# Formal nonbinary N3 evidence note

The `nbldpc_formal_v1` synthetic N3 package is non-promoted (18/32 at p=.20,
5/32 at p=.30; gate 31/32). Its official strict verifier is unverifiable after
execution because live worktree provenance drifted. This is not real-data,
production, or cross-method evidence; N4 remains unauthorized.

## Formal nonbinary v2 evidence note

`nbldpc_formal_v2` stopped at development readiness. Its selected
tempered+damped QC48 policy achieved 0/24 at p=.20 and 5/24 at p=.30, below
the frozen 22/24 floor in both strata. The immutable eight-artifact package
passed strict full replay, but confirmation was never generated or executed.
This is not confirmation FER, real-data, production, or comparison evidence;
N4, sidecar reads, and raw `.ttbin` processing remain forbidden.
