# RUN_COMMANDS.md

Curated commands for this repository. Prefer smoke commands first.

## Smoke

```powershell
python -m comparison_bench.src.comparison_bench.cli.smoke_test --config comparison_bench/configs/benchmark_synth.yaml
```

## Benchmark

```powershell
python -m comparison_bench.src.comparison_bench.cli.build_dataset
python -m comparison_bench.src.comparison_bench.cli.run_benchmark --config comparison_bench/configs/benchmark_realdata.yaml
python -m comparison_bench.src.comparison_bench.cli.compare_methods --input <input> --output <output>
```

## V3 sweeps

```powershell
python -m comparison_bench.src.comparison_bench.cli.run_cascade_param_sweep --config comparison_bench/configs/cascade_param_sweep.yaml
python -m comparison_bench.src.comparison_bench.cli.run_layered_ldpc_param_sweep --config comparison_bench/configs/layered_ldpc_param_sweep.yaml
python -m comparison_bench.src.comparison_bench.cli.run_qldpc_param_sweep --config comparison_bench/configs/qldpc_param_sweep.yaml
python -m comparison_bench.src.comparison_bench.cli.run_ir_v3_master --config comparison_bench/configs/ir_methods_v3_master.yaml
```

## Do not run by default

- `experiments/run_e2e_pipeline.py` on raw data
- any `tools/longrun_*.py`
- any `tools/minrerun_*.py`
- any `tools/routeA_*.py`
