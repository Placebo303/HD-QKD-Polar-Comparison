# Current Mainline

## Reporting Rule

The default reporting line is the Route A actual-IR reconciled net (public-EC-only, not a secret-key rate):

- `PIE_main`
- `SKR_main_bps`
- `main_result_source=actual_ir_reconciled_net_not_secure`
- `claim_boundary=public_ec_only_not_secure`

`PIE_practical`, `SKR_measured_bps`, shadow-only outputs, and estimate-only outputs are diagnostics. Legacy `PIE_secure_actual_ir` / `SKR_secure_actual_ir_bps` are blocked from scientific reporting (see `docs/decision-log.md` 2026-08-14).

## Recommended Entrypoints

Front half:

```powershell
python experiments/run_e2e_pipeline.py --ttbin <head.ttbin> --skip-polar --force-align --out-root <e2e_out>
python experiments/run_real_polar_max_pie.py --grid-table <e2e_out>\_tmp_grid_table.csv --in-csv <e2e_out>\_tmp_src_table.csv --out-csv <polar_out>\polar_e2e_results.csv --prefer-sidecar-map-ser
```

ASENoise Type0:

```powershell
python tools/asenoise/run_asenoise_type0_corrected_subset.py --timestamp <stamp>
python tools/asenoise/run_asenoise_routeA_replay.py replay --mode full --timestamp <stamp>
python tools/asenoise/run_asenoise_routeA_replay.py finalize-main --input-csv <full_master.csv> --backup
```

Security reports / Route A:

```powershell
python tools/security_reports/round2_build_finite_key_audit_table.py --input-dirs <candidate_dir> <actual_ir_dir> --output-dir <stage2_security> --overwrite
python tools/security_reports/round2_build_actual_ir_finite_key_shadow.py --output-dir <stage2_security> --overwrite
python tools/security_reports/round2_build_security_round2_summary.py --actual-ir-dir <stage2_security> --beta-baseline-dir <stage2_security> --output-dir <stage2_security> --overwrite
```

Current pipelines live in `pipelines/current/`. Historical batch scripts live in `pipelines/archive/` and are not maintained as default commands.

## Archived Studies

Route B-lite is an archived side study. It tested whether richer binary channel / LLR modeling should enter the mainline. The result was mixed and locally useful but not stable enough to replace Route A or to pollute the mainline. Its value is as evidence for future Route C / q-ary Polar discussions.

## Old Entrypoints

Old root-level `tools/routeB_*`, root `tools/round2_*`, and root `tools/run_asenoise_*` paths are intentionally not preserved as wrappers. Use the paths above.
