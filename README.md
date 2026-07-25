# HD-QKD Polar Comparison

This repository contains the current HD-QKD Polar comparison workspace, including:
- the frozen Polar baseline
- the non-invasive `comparison_bench/` comparison layer
- workflow and result documentation

## Current Status

As of 2026-03-27, the current reporting line is:
- `PRIMARY_REPORTING_MODE = actual_ir_finite_key`
- `BETA_BASELINE_ROLE = comparison_only`
- `NIU_2016_STATUS = not_supported_by_current_observables`

The authoritative latest results are **not** the older `_tmp_longrun_stage*` directories.
Use these instead:
- frozen baseline outputs: `results/`
- comparison outputs: `comparison_bench/outputs_comparison/`

## Main Documents

- latest workflow and run method:
  - [docs/POLAR_CODE_MAINFLOW_20260327.md](docs/POLAR_CODE_MAINFLOW_20260327.md)
- latest results and authoritative output paths:
  - [docs/LATEST_RESULTS_20260327.md](docs/LATEST_RESULTS_20260327.md)
- Route A correctness formalization:
  - [docs/ROUTE_A_FORMAL_VERIFICATION_20260410.md](docs/ROUTE_A_FORMAL_VERIFICATION_20260410.md)
  - [docs/ROUTE_A_BIT_PLANE_INTERFACE_20260414.md](docs/ROUTE_A_BIT_PLANE_INTERFACE_20260414.md)

Route A correctness formalization uses per-block universal-hash verification
for `epsilon_EC_bound` budgeting. This is not a strict Zhong 2015 or full Niu
2016 proof instantiation.

## Main Entry Points

Front half:
- [experiments/run_e2e_pipeline.py](experiments/run_e2e_pipeline.py)
- [experiments/run_real_polar_max_pie.py](experiments/run_real_polar_max_pie.py)

Replay / security:
- [tools/longrun_build_replay_index.py](tools/longrun_build_replay_index.py)
- [tools/longrun_run_actual_ir_replay.py](tools/longrun_run_actual_ir_replay.py)
- [tools/longrun_build_finite_key_audit_table.py](tools/longrun_build_finite_key_audit_table.py)
- [tools/longrun_build_security_master_table.py](tools/longrun_build_security_master_table.py)

Refined frame-accounting pass:
- [tools/minrerun_audit_frame_accounting_inputs.py](tools/minrerun_audit_frame_accounting_inputs.py)
- [tools/minrerun_run_frame_audit.py](tools/minrerun_run_frame_audit.py)
- [tools/minrerun_rebuild_security_master_20dB.py](tools/minrerun_rebuild_security_master_20dB.py)
- [tools/minrerun_build_cross_loss_refined_summary.py](tools/minrerun_build_cross_loss_refined_summary.py)

## Recommended Usage

If you only need the current best result package, read the existing outputs and do not rerun the physics front half.

If you need to reproduce the current workflow from raw data, use the split boundary flow described in [docs/POLAR_CODE_MAINFLOW_20260327.md](docs/POLAR_CODE_MAINFLOW_20260327.md):
1. extraction/materialization with `--skip-polar`
2. Polar evaluation from cached `_tmp_grid_table.csv` and `_tmp_src_table.csv`
3. actual-IR replay and security aggregation
4. refined frame-accounting rebuild

## License

MIT
