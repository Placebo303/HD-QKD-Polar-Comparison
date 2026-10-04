# RUN_COMMANDS.md

Curated commands for this repository. Prefer smoke commands first.

> Use the repo venv for every command below: `source .venv/bin/activate`
> or prefix with `.venv/bin/python`. Bare `python`/`python3` uses the system
> interpreter without project deps. `wsl-env.sh` does not activate the venv.

## Smoke

```powershell
.venv/bin/python -m comparison_bench.src.comparison_bench.cli.smoke_test --config comparison_bench/configs/benchmark_synth.yaml
```

## Benchmark

```powershell
.venv/bin/python -m comparison_bench.src.comparison_bench.cli.build_dataset
.venv/bin/python -m comparison_bench.src.comparison_bench.cli.run_benchmark --config comparison_bench/configs/benchmark_realdata.yaml
.venv/bin/python -m comparison_bench.src.comparison_bench.cli.compare_methods --input <input> --output <output>
```

## V3 sweeps

```powershell
.venv/bin/python -m comparison_bench.src.comparison_bench.cli.run_cascade_param_sweep --config comparison_bench/configs/cascade_param_sweep.yaml
.venv/bin/python -m comparison_bench.src.comparison_bench.cli.run_layered_ldpc_param_sweep --config comparison_bench/configs/layered_ldpc_param_sweep.yaml
.venv/bin/python -m comparison_bench.src.comparison_bench.cli.run_qldpc_param_sweep --config comparison_bench/configs/qldpc_param_sweep.yaml
.venv/bin/python -m comparison_bench.src.comparison_bench.cli.run_ir_v3_master --config comparison_bench/configs/ir_methods_v3_master.yaml
```

## Do not run by default

- `experiments/run_e2e_pipeline.py` on raw data
- any `tools/longrun_*.py`
- any `tools/minrerun_*.py`
- any `tools/routeA_*.py`
