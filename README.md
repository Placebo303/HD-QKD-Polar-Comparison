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
- Route A correctness formalization:
  - [docs/ROUTE_A_FORMAL_VERIFICATION_20260410.md](/D:/Code/HD-QKD_Polar_Release/docs/ROUTE_A_FORMAL_VERIFICATION_20260410.md)
  - [docs/ROUTE_A_BIT_PLANE_INTERFACE_20260414.md](/D:/Code/HD-QKD_Polar_Release/docs/ROUTE_A_BIT_PLANE_INTERFACE_20260414.md)

Route A correctness formalization uses per-block universal-hash verification
for `epsilon_EC_bound` budgeting. This is not a strict Zhong 2015 or full Niu
2016 proof instantiation.
- Route B-lite error-model audit:
  - [docs/ROUTE_B_LITE_PLAN_20260415.md](/D:/Code/HD-QKD_Polar_Release/docs/ROUTE_B_LITE_PLAN_20260415.md)
  - [docs/ROUTE_B_LITE_STATUS_20260415.md](/D:/Code/HD-QKD_Polar_Release/docs/ROUTE_B_LITE_STATUS_20260415.md)
  - [docs/ROUTE_B_LITE_FINAL_SUMMARY_20260415.md](/D:/Code/HD-QKD_Polar_Release/docs/ROUTE_B_LITE_FINAL_SUMMARY_20260415.md)

Route B-lite is completed as a diagnostic/validation route. It ran B1 error
audit, B2 channel-model diagnostics, B3 subset LLR-only ablation, and full
20dB LLR-only validation. The conclusion is a useful but limited/partial
negative result: local bin-width-dependent signals exist, but there is no
stable, broadly applicable gain. Do not expand it or migrate it to the
mainline without a new plan.

## Main Entry Points

Front half:
- [experiments/run_e2e_pipeline.py](/D:/Code/HD-QKD_Polar_Release/experiments/run_e2e_pipeline.py)
- [experiments/run_real_polar_max_pie.py](/D:/Code/HD-QKD_Polar_Release/experiments/run_real_polar_max_pie.py)

Replay / security:
- [tools/longrun_build_replay_index.py](/D:/Code/HD-QKD_Polar_Release/tools/longrun_build_replay_index.py)
- [tools/longrun_run_actual_ir_replay.py](/D:/Code/HD-QKD_Polar_Release/tools/longrun_run_actual_ir_replay.py)
- [tools/longrun_build_finite_key_audit_table.py](/D:/Code/HD-QKD_Polar_Release/tools/longrun_build_finite_key_audit_table.py)
- [tools/longrun_build_security_master_table.py](/D:/Code/HD-QKD_Polar_Release/tools/longrun_build_security_master_table.py)

Route B-lite:
- [tools/routeB_build_error_audit.py](/D:/Code/HD-QKD_Polar_Release/tools/routeB_build_error_audit.py)
- [tools/routeB_build_channel_model_table.py](/D:/Code/HD-QKD_Polar_Release/tools/routeB_build_channel_model_table.py)
- [tools/routeB_select_ab_subset.py](/D:/Code/HD-QKD_Polar_Release/tools/routeB_select_ab_subset.py)
- [tools/routeB_run_b3_subset_ablation.py](/D:/Code/HD-QKD_Polar_Release/tools/routeB_run_b3_subset_ablation.py)
- [tools/routeB_run_full20dB_llr_ablation.py](/D:/Code/HD-QKD_Polar_Release/tools/routeB_run_full20dB_llr_ablation.py)

The current B3 gate output is [results/_tmp_routeB_lite_b3_subset_ablation](/D:/Code/HD-QKD_Polar_Release/results/_tmp_routeB_lite_b3_subset_ablation).
The full 20dB LLR-only validation output is [results/_tmp_routeB_lite_full20dB_llr_ablation](/D:/Code/HD-QKD_Polar_Release/results/_tmp_routeB_lite_full20dB_llr_ablation).

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
