# Polar Code Main Flow (2026-03-27)

## 1. Scope

This document describes the **current main Polar-code workflow** in this repository.
It is the latest recommended run method and result interpretation as of 2026-03-27.
For the maintained 2026-04-27 layout and Route A formal correctness entrypoints,
start with [CURRENT_MAINLINE.md](CURRENT_MAINLINE.md). Paths below have been
updated to the current layout, but the result discussion remains the 2026-03-27 baseline.

Current reporting hierarchy:
- `actual-IR finite-key calibrated`: main result
- `literature-beta finite-key baseline`: comparison only
- `performance proxy`: engineering reference only

This workflow does **not** claim:
- strict Zhong 2015 security proof
- Niu 2016 composable proof

Current model layer:
- `zhang_2013_compatible_with_actual_ir_finite_key_calibrated_shadow`

## 2. Authoritative Output Roots

Latest authoritative outputs:
- fresh rerun full chain:
  - [results/authoritative/_tmp_longrun_fresh_rerun](../results/authoritative/_tmp_longrun_fresh_rerun)
- refined 20 dB frame-accounting rebuild:
  - [results/authoritative/_tmp_minrerun_stageC_security_20dB](../results/authoritative/_tmp_minrerun_stageC_security_20dB)
- refined cross-loss pack:
  - [results/authoritative/_tmp_minrerun_stageD_cross_loss](../results/authoritative/_tmp_minrerun_stageD_cross_loss)

Older `_tmp_longrun_stage*` trees are legacy intermediate packs and should not be treated as the preferred latest baseline.

## 3. Main Flow

### Stage 0: Smoke validation
Purpose:
- prove that the split-boundary wrapper preserves current logic before a full rerun

Script:
- [pipelines/archive/longrun_validate_smoke_subset.py](../pipelines/archive/longrun_validate_smoke_subset.py)

Validated result:
- [results/authoritative/_tmp_longrun_fresh_rerun/smoke_20dB/validation/smoke_compare_summary.txt](../results/authoritative/_tmp_longrun_fresh_rerun/smoke_20dB/validation/smoke_compare_summary.txt)
- exact agreement on the tested 40-point subset:
  - `max_abs_delta_map_ser = 0`
  - `max_abs_delta_PIE_practical = 0`
  - `max_abs_delta_SKR_measured_bps = 0`

### Stage 1: Front half extraction/materialization
Purpose:
- parse ttbin
- perform pairing/materialization
- write sidecars, `_tmp_grid_table.csv`, `_tmp_src_table.csv`
- do **not** run Polar yet

Primary entrypoint:
- [experiments/run_e2e_pipeline.py](../experiments/run_e2e_pipeline.py)

Recommended mode:
- `--skip-polar`

Why:
- it establishes a clean cache boundary between front-half physics/materialization and back-half Polar/security work
- this was the main acceleration change used in the latest reruns

### Stage 2: Polar evaluation
Purpose:
- evaluate all `(dimension, bin_width_ps)` points from the cached front-half outputs
- write:
  - `polar_e2e_results.csv`
  - `polar_diag_summary.csv`
  - `polar_layer_metrics.csv`

Primary entrypoint:
- [experiments/run_real_polar_max_pie.py](../experiments/run_real_polar_max_pie.py)

Required replay metadata emitted by the current version:
- `decoder_mode_best`
- `k_best`
- `rate_best`
- `crc_bits`
- `frozen_count_best`
- `layer_block_symbols`

### Stage 3: Actual-IR replay
Purpose:
- replay Polar reconciliation at block level using the cached sidecar sequences
- produce actual replay leak and block success/fail logs

Primary tools:
- [pipelines/current/longrun_build_replay_index.py](../pipelines/current/longrun_build_replay_index.py)
- [pipelines/current/longrun_run_actual_ir_replay.py](../pipelines/current/longrun_run_actual_ir_replay.py)
- [tools/security_reports/longrun_build_actual_ir_logs_index.py](../tools/security_reports/longrun_build_actual_ir_logs_index.py)

Current replay provenance tags:
- `actual_ir_replay_with_configured_verification`
- blocked/missing states are explicit; no silent fallback is used in replay outputs

### Stage 4: Finite-key actual-IR security aggregation
Purpose:
- build the main security table from actual replay leak plus Zhong-like calibrated finite-key penalty

Primary tools:
- [tools/security_reports/longrun_build_finite_key_audit_table.py](../tools/security_reports/longrun_build_finite_key_audit_table.py)
- [tools/security_reports/longrun_build_actual_ir_finite_key_shadow.py](../tools/security_reports/longrun_build_actual_ir_finite_key_shadow.py)
- [tools/security_reports/longrun_build_beta_baseline_shadow.py](../tools/security_reports/longrun_build_beta_baseline_shadow.py)
- [tools/security_reports/longrun_build_security_master_table.py](../tools/security_reports/longrun_build_security_master_table.py)

Current 2026-03-27 result state:
- all four losses have `121/121 actual replay leak`
- current stage2 fresh summaries:
  - [full_6dB/stage2_security/stage2_summary.txt](../results/authoritative/_tmp_longrun_fresh_rerun/full_6dB/stage2_security/stage2_summary.txt)
  - [full_10dB/stage2_security/stage2_summary.txt](../results/authoritative/_tmp_longrun_fresh_rerun/full_10dB/stage2_security/stage2_summary.txt)
  - [full_16dB/stage2_security/stage2_summary.txt](../results/authoritative/_tmp_longrun_fresh_rerun/full_16dB/stage2_security/stage2_summary.txt)
  - [full_20dB/stage2_security/stage2_summary.txt](../results/authoritative/_tmp_longrun_fresh_rerun/full_20dB/stage2_security/stage2_summary.txt)

### Stage 5: Minimal rerun refined frame-accounting pass
Purpose:
- reuse the fresh rerun outputs
- do **not** rerun the physics front half
- upgrade frame accounting from surrogate clean-pair fraction to actual sidecar occupancy accounting

Primary tools:
- [pipelines/archive/minrerun_audit_frame_accounting_inputs.py](../pipelines/archive/minrerun_audit_frame_accounting_inputs.py)
- [pipelines/archive/minrerun_patch_actual_ir_replay_logs.py](../pipelines/archive/minrerun_patch_actual_ir_replay_logs.py)
- [pipelines/archive/minrerun_run_frame_audit.py](../pipelines/archive/minrerun_run_frame_audit.py)
- [pipelines/archive/minrerun_rebuild_security_master_20dB.py](../pipelines/archive/minrerun_rebuild_security_master_20dB.py)
- [pipelines/archive/minrerun_build_cross_loss_refined_summary.py](../pipelines/archive/minrerun_build_cross_loss_refined_summary.py)

Actual frame-accounting source:
- sidecar `occupancy_filter_summary.csv`

Refined frame definitions currently used:
- `candidate_frame_count := n_frames_total`
- `accepted_frame_count := n_frames_clean_single_single`
- `rejected_frame_count := candidate_frame_count - accepted_frame_count`
- `frame_success_rate := accepted_frame_count / candidate_frame_count`
- `accepted_frame_fraction_source_tag := actual_sidecar_occupancy_summary`
- `frame_success_rate_source_tag := actual_sidecar_occupancy_summary`

## 4. Recommended Run Methods

### A. If you need the current latest results only
Do not rerun anything. Read:
- [results/authoritative/_tmp_minrerun_stageC_security_20dB](../results/authoritative/_tmp_minrerun_stageC_security_20dB)
- [results/authoritative/_tmp_minrerun_stageD_cross_loss](../results/authoritative/_tmp_minrerun_stageD_cross_loss)

### B. If you need a fresh full rerun from raw data
Use the split-boundary flow:
1. front half with `run_e2e_pipeline.py --skip-polar`
2. Polar with `run_real_polar_max_pie.py`
3. actual replay and security aggregation
4. refined frame-accounting pass

This was the exact strategy used to generate:
- [results/authoritative/_tmp_longrun_fresh_rerun](../results/authoritative/_tmp_longrun_fresh_rerun)
- [results/authoritative/_tmp_minrerun_stageC_security_20dB](../results/authoritative/_tmp_minrerun_stageC_security_20dB)
- [results/authoritative/_tmp_minrerun_stageD_cross_loss](../results/authoritative/_tmp_minrerun_stageD_cross_loss)

### C. If you only need to refine frame accounting
Do not touch raw ttbin or full Polar search.
Run only the `minrerun_*` tools against the fresh rerun outputs.

## 5. Runtime Notes

The main hotspot is still fullgrid Polar evaluation in [run_real_polar_max_pie.py](../experiments/run_real_polar_max_pie.py).

The latest acceleration changes that are already in use are:
- front-half / back-half cache boundary via `--skip-polar`
- single-layer 15-thread CPU scheduling
- replay metadata emitted directly in fresh rerun `polar_layer_metrics.csv`
- `a_eff/b_eff` hot paths switched to `mmap_mode="r"`

## 6. Current Caveats

Still not actual transcript-level or strict-composable:
- `verification_bits_used_actual` is still derived from configured CRC budget on current fresh rerun outputs
- `verification_source_tag` therefore remains `configured_budget` or mixed `actual_replay;configured_budget`
- no strict Zhong 2015 claim
- no Niu 2016 composable claim

Use this wording instead:
- `actual replay leak + actual sidecar frame-level accounting + finite-key calibrated Zhong-like security`

