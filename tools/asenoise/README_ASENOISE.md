# ASENoise Tools

## Scripts

- `export_ttbin_cross_correlation.py`: export aligned cross-correlation CSV/JSON from `.ttbin` data.
- `run_asenoise_type0_corrected_subset.py`: run corrected Type0 E2E/Polar subset with channels `A=3,B=2`.
- `run_asenoise_routeA_replay.py`: run Route A estimate, smoke/full actual replay, compare, and final main-result standardization.
- `run_asenoise_type0_jti_dense.py`: generate dense JTI outputs for ASENoise inspection.

## Recommended Order

```powershell
python tools/asenoise/run_asenoise_type0_corrected_subset.py --timestamp <stamp>
python tools/asenoise/run_asenoise_routeA_replay.py estimate --timestamp <stamp>
python tools/asenoise/run_asenoise_routeA_replay.py replay --mode smoke --timestamp <stamp>
python tools/asenoise/run_asenoise_routeA_replay.py replay --mode full --timestamp <stamp>
python tools/asenoise/run_asenoise_routeA_replay.py finalize-main --input-csv <full_master.csv> --backup
```

## Outputs And Reporting

ASENoise outputs are written under each raw data dataset directory and aggregate files are written under `D:\Data\Raw Data\ASENoise_Type0`.

Default reporting columns:

- `PIE_main`
- `SKR_main_bps`
- `main_result_source=actual_ir_finite_key`

Shadow, estimate, `PIE_practical`, and `SKR_measured_bps` fields are diagnostics/proxies only.
