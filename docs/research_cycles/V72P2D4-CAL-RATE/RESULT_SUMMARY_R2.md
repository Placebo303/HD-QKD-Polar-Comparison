# V72P2D4R2 RESULT_SUMMARY (CAL-only descriptive audit, route C, selected F)

- Cycle: `V72P2D4R2-CAL-GF32-MODEL-RATE` (plan cycle `V72P2D4-CAL-RATE`, D4 R2)
- HEAD: `bd78a67d` on `formal-ir-v72p1-addendum-clean`
- Output root: `comparison_bench/outputs_comparison/v72p2d4r2_cal_gf32_model_rate_audit_20260905/` (exactly 4 files: `manifest.json/audit.json/table.csv/report.md`)
- Status: `READY`, descriptive only; not a lower bound; not a failure verdict.
- Date: `2026-09-05`

## 1. Inputs

- Registry: `workspace/v72p2d3_real_registry_20260904.json` (CAL `702..1725`, 1024 frames).
- Rows: `n_read_rows=545280/n_retained_rows=262144/n_cal_frames=1024/n_cal_symbols=262144`.
- `decoder_calls=0/published_bits=0/formal=false/cal_only=true`.

## 2. R5 gate

- Same-fixture synthetic repro `passed=true`: `mean_ce_l1=6.422161237462124/mean_ce_l2_oracle=5.083351288530697/mean_ce_joint=11.50551252599282`, deltas `0.0`, chain `0.0`, root `R5_FIXTURE_REPRODUCED`, `real_cal_exact_match=false`.

## 3. Nested CV (frame-blocked, TEST never enters fit)

- Outer `TEST256/TRAIN768` (`n_train=196608/n_test=65536` symbols); inner grid-30 `selected_lam=137.3823795883264` on all 4 outer folds; `seen_frac=1.0` all folds/models.
- Fold-mean/std/range: G `9.999677/0.000309/0.000849`, F `7.162347/0.015850/0.042319`, L `7.343949/0.013794/0.035372`; all stable (`unstable=false`).
- Decomposition: `U->G 0.000323/G->F 2.837330/F->L -0.181602/U->selected 2.837653`; synthetic-vs-real gap is data-domain, not caliber.
- Selection: `F` (`ranking F/L/G`, reason `mean-minimal within 0.02: F`, `downgraded=false`); M3 `M3_EXIT_AMBIGUOUS` excluded; circulant `CIRCULANT_DEFERRED` excluded; uniform `5/5/10` descriptive only.

## 4. Budget and route (selected F mean, same caliber)

- Selected means: `L1 3.814742/L2 3.347605/Total 7.162347 bit/symbol`.
- `f=1.0` Total `7334.24 bit → 1467 rows` vs `216` (`margin -1251`); `f=1.3` Total `9534.52 bit → 1907 rows` vs `216` (`margin -1691`); every layer mismatches already at `f=1.0`.
- Route: `C` (`mismatch@1.0 some layer`, `fit_at_1_0=false/fit_at_1_3=false`) → stop; successor only backlog. `required>available` is only `MODEL_BUDGET_MISMATCH`.
- Walls: `prep 0.484s/g 17.266s/inv 17.766s` (limits `300/300/600s`); `peak_rss 169328640 bytes` (<2GiB).

## 5. Lifecycle out

`decoder_executed=false/VAL used for fitting=false/scientific_promotion=false`. R1 root (`v72p2d4r1_*`) remains prior evidence unchanged, not overwritten; Attempt-0 root (`v72p2d4_*`) remains untracked non-evidence (see `ATTEMPT_0_INVALID.md`). No rerun/tuning authorized by this record.
