# V72P2D4R1 RESULT_SUMMARY (CAL-only descriptive audit, route C)

- Cycle: `V72P2D4R1-CAL-GF32-MODEL-RATE` (plan cycle `V72P2D4-CAL-RATE`, D4 R1)
- HEAD: `a7a6ec62` on `formal-ir-v72p1-addendum-clean`
- Output root: `comparison_bench/outputs_comparison/v72p2d4r1_cal_gf32_model_rate_audit_20260905/` (exactly 4 files: `manifest.json/audit.json/table.csv/report.md`)
- Status: `READY`, descriptive only; not a lower bound; not a failure verdict.
- Date: `2026-09-05`

## 1. Inputs

- Registry: `workspace/v72p2d3_real_registry_20260904.json` (CAL `702..1725`, 1024 frames).
- Rows: `n_read_rows=545280/n_retained_rows=262144/n_cal_frames=1024/n_cal_symbols=262144`.
- `decoder_calls=0/published_bits=0/formal=false/cal_only=true`.

## 2. R5 gate

- Same-fixture synthetic repro `passed=true`: `mean_ce_l1=6.422161237462124/mean_ce_l2_oracle=5.083351288530697/mean_ce_joint=11.50551252599282`, deltas `0.0`, chain `0.0`, root `R5_FIXTURE_REPRODUCED`, `real_cal_exact_match=false`.

## 3. Nested CV (frame-blocked, TEST never enters fit)

- Outer `TEST256/TRAIN768` (`n_train=196608/n_test=65536` symbols); inner grid-30 `selected_lam=18.873918221350976` on all 4 outer folds; `seen_frac=1.0` all folds/models.
- Fold-mean/std/range: M0 `9.999677/0.000309/0.000849`, M1 `9.991036/0.025195/0.067051`, M2 `6.978821/0.018226/0.047530`; all stable (`unstable=false`).
- Decomposition: `B-dependence M0→M1 gain 0.008641`, `hierarchy M1→M2 gain 3.012215`, `total M0→selected 3.020856`; synthetic-vs-real gap is data-domain, not caliber.
- Selection: `M2` (`ranking M2/M1/M0`, reason `mean-minimal within 0.02: M2`, `downgraded=false`); M3 `M3_EXIT_AMBIGUOUS` excluded; uniform `10.0` descriptive only.

## 4. Budget and route (selected M2 mean, same caliber)

- Selected means: `L1 3.795171/L2 3.183651/Total 6.978821 bit/symbol`.
- `f=1.0` Total `7146.31 bit → 1430 rows` vs `216` (`margin -1214`); `f=1.3` Total `9290.21 bit → 1859 rows` vs `216` (`margin -1643`); every layer mismatches already at `f=1.0`.
- Route: `C` (`mismatch@1.0 some layer`, `fit_at_1_0=false/fit_at_1_3=false`) → stop; successor only backlog (`d=256,[4,4]` first). `required>available` is only `MODEL_BUDGET_MISMATCH`.
- Walls: `prep 0.562s/g 10.125s/inv 10.703s` (limits `300/300/600s`); `peak_rss 168968192 bytes` (<2GiB).

## 5. Lifecycle out

`decoder_executed=false/VAL used for fitting=false/scientific_promotion=false`. Old Attempt-0 root (`v72p2d4_cal_...`) remains untracked non-evidence (see `ATTEMPT_0_INVALID.md`). No rerun/tuning authorized by this record.
