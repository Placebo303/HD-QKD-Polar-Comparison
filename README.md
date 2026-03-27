# High-Dimensional QKD Polar Pipeline

This repository contains the current end-to-end HD-QKD Polar-code workflow, including:
- pairing/materialization from `.ttbin`
- Polar-based information reconciliation evaluation
- actual-IR replay auditing
- finite-key calibrated Zhong-like security aggregation

## Current Status

As of 2026-03-27, the current reporting line is:
- `PRIMARY_REPORTING_MODE = actual_ir_finite_key`
- `BETA_BASELINE_ROLE = comparison_only`
- `NIU_2016_STATUS = not_supported_by_current_observables`

The authoritative latest results are **not** the older `_tmp_longrun_stage*` directories.
Use these instead:
- fresh full rerun root: [results/_tmp_longrun_fresh_rerun](/D:/Code/HD-QKD_Polar_Release/results/_tmp_longrun_fresh_rerun)
- refined frame-accounting pass: [results/_tmp_minrerun_stageC_security_20dB](/D:/Code/HD-QKD_Polar_Release/results/_tmp_minrerun_stageC_security_20dB)
- refined cross-loss pack: [results/_tmp_minrerun_stageD_cross_loss](/D:/Code/HD-QKD_Polar_Release/results/_tmp_minrerun_stageD_cross_loss)

## Main Documents

- latest workflow and run method:
  - [docs/POLAR_CODE_MAINFLOW_20260327.md](/D:/Code/HD-QKD_Polar_Release/docs/POLAR_CODE_MAINFLOW_20260327.md)
- latest results and authoritative output paths:
  - [docs/LATEST_RESULTS_20260327.md](/D:/Code/HD-QKD_Polar_Release/docs/LATEST_RESULTS_20260327.md)

## Main Entry Points

Front half:
- [experiments/run_e2e_pipeline.py](/D:/Code/HD-QKD_Polar_Release/experiments/run_e2e_pipeline.py)
- [experiments/run_real_polar_max_pie.py](/D:/Code/HD-QKD_Polar_Release/experiments/run_real_polar_max_pie.py)

Replay / security:
- [tools/longrun_build_replay_index.py](/D:/Code/HD-QKD_Polar_Release/tools/longrun_build_replay_index.py)
- [tools/longrun_run_actual_ir_replay.py](/D:/Code/HD-QKD_Polar_Release/tools/longrun_run_actual_ir_replay.py)
- [tools/longrun_build_finite_key_audit_table.py](/D:/Code/HD-QKD_Polar_Release/tools/longrun_build_finite_key_audit_table.py)
- [tools/longrun_build_security_master_table.py](/D:/Code/HD-QKD_Polar_Release/tools/longrun_build_security_master_table.py)

Refined frame-accounting pass:
- [tools/minrerun_audit_frame_accounting_inputs.py](/D:/Code/HD-QKD_Polar_Release/tools/minrerun_audit_frame_accounting_inputs.py)
- [tools/minrerun_run_frame_audit.py](/D:/Code/HD-QKD_Polar_Release/tools/minrerun_run_frame_audit.py)
- [tools/minrerun_rebuild_security_master_20dB.py](/D:/Code/HD-QKD_Polar_Release/tools/minrerun_rebuild_security_master_20dB.py)
- [tools/minrerun_build_cross_loss_refined_summary.py](/D:/Code/HD-QKD_Polar_Release/tools/minrerun_build_cross_loss_refined_summary.py)

## Recommended Usage

If you only need the current best result package, read the existing outputs and do not rerun the physics front half.

If you need to reproduce the current workflow from raw data, use the split boundary flow described in [docs/POLAR_CODE_MAINFLOW_20260327.md](/D:/Code/HD-QKD_Polar_Release/docs/POLAR_CODE_MAINFLOW_20260327.md):
1. extraction/materialization with `--skip-polar`
2. Polar evaluation from cached `_tmp_grid_table.csv` and `_tmp_src_table.csv`
3. actual-IR replay and security aggregation
4. refined frame-accounting rebuild

## License

MIT
