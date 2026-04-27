# Latest Results (2026-03-27)

## 1. Current Main Result Line

- `PRIMARY_REPORTING_MODE = actual_ir_finite_key`
- `BETA_BASELINE_ROLE = comparison_only`
- `NIU_2016_STATUS = not_supported_by_current_observables`

Current model layer:
- `zhang_2013_compatible_with_actual_ir_finite_key_calibrated_shadow`

## 2. Authoritative Result Directories

Fresh rerun full chain:
- [results/authoritative/_tmp_longrun_fresh_rerun](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_longrun_fresh_rerun)

Refined 20 dB frame-accounting result:
- [results/authoritative/_tmp_minrerun_stageC_security_20dB/security_calibrated_master_table_20dB_refined.csv](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_minrerun_stageC_security_20dB/security_calibrated_master_table_20dB_refined.csv)
- [results/authoritative/_tmp_minrerun_stageC_security_20dB/stageC_summary.txt](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_minrerun_stageC_security_20dB/stageC_summary.txt)

Refined cross-loss result:
- [results/authoritative/_tmp_minrerun_stageD_cross_loss/cross_loss_security_master_table_refined.csv](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_minrerun_stageD_cross_loss/cross_loss_security_master_table_refined.csv)
- [results/authoritative/_tmp_minrerun_stageD_cross_loss/stageD_summary.txt](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_minrerun_stageD_cross_loss/stageD_summary.txt)

## 3. Fresh Full Rerun Stage2 Results

| Loss | Actual leak rows | Surrogate rows | Mean PIE drop vs performance | Best actual point | Positive secure rows |
|---|---:|---:|---:|---|---:|
| 6 dB | 121 | 0 | 2.570555927257089 | d=4096, bw=200 | 74 |
| 10 dB | 121 | 0 | 2.5401159037518446 | d=4096, bw=200 | 76 |
| 16 dB | 121 | 0 | 2.4558566282459804 | d=4096, bw=200 | 79 |
| 20 dB | 121 | 0 | 2.438051531429902 | d=4096, bw=180 | 82 |

Source summaries:
- [full_6dB/stage2_security/stage2_summary.txt](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_longrun_fresh_rerun/full_6dB/stage2_security/stage2_summary.txt)
- [full_10dB/stage2_security/stage2_summary.txt](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_longrun_fresh_rerun/full_10dB/stage2_security/stage2_summary.txt)
- [full_16dB/stage2_security/stage2_summary.txt](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_longrun_fresh_rerun/full_16dB/stage2_security/stage2_summary.txt)
- [full_20dB/stage2_security/stage2_summary.txt](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_longrun_fresh_rerun/full_20dB/stage2_security/stage2_summary.txt)

## 4. Refined 20 dB Frame-Accounting Result

Refined summary:
- [stageC_summary.txt](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_minrerun_stageC_security_20dB/stageC_summary.txt)

Key facts:
- `fully_actual_rows = 121`
- `configured_budget_rows = 121`
- `mean_delta_PIE_secure_actual_ir = +0.00036946327628768554`
- `mean_delta_SKR_secure_actual_ir_bps = +13.51934680310145 bps`
- best point stayed at `d=4096, bw=180`
- high-dimensional anti-loss trend still visible

Interpretation:
- refined frame accounting improved provenance more than it changed the ranking
- the refined result is better for paper reporting because accepted/rejected frame accounting now comes from persisted sidecar occupancy diagnostics instead of surrogate clean-pair fraction

## 5. Refined Cross-Loss Result

Refined cross-loss summary:
- [stageD_summary.txt](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_minrerun_stageD_cross_loss/stageD_summary.txt)

Current refined best points:
- `6 dB`: `d=4096, bw=200`
- `10 dB`: `d=4096, bw=200`
- `16 dB`: `d=4096, bw=200`
- `20 dB`: `d=4096, bw=180`

Cross-loss fact:
- `cross_loss_positive_actual_rows = 312`

## 6. What Is Actual vs Configured vs Missing

Actual now includes:
- actual replay leak
- actual sidecar frame-level accounting from `occupancy_filter_summary.csv`

Still configured-budget, not transcript-level actual:
- `verification_bits_used_actual`
- `verification_source_tag`

Still not supported:
- strict Zhong 2015 proof
- Niu 2016 composable proof

## 7. Main-Text Safe Claims

Safe main-text claims now:
- actual-IR finite-key calibrated is the main result line
- beta baseline is comparison only
- performance proxy is engineering reference only
- high-dimensional anti-loss trend remains visible under the actual-IR finite-key line
- the best `(d, bw)` region remains in the high-d / high-bw corner on the current covered losses

Claims that still need caution:
- any statement implying transcript-level verification accounting
- any strict-composable proof wording
- any wording that upgrades this to strict Zhong or Niu 2016

