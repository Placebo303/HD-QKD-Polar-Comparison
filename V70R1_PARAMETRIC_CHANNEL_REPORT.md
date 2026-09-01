# V70R1 Parametric Channel Model Check Report (R2 — 5 terminals, mechanical reclassification, DEVELOPMENT_RESULT_CANDIDATE)

**Lifecycle**: `DEVELOPMENT_RESULT_CANDIDATE / DECODER_FREE_EXECUTION_COMPLETE` / `V72_NOT_STARTED=true`
**Plan revision**: R2 mechanical — insert `REDUCES_VAL_CE` (`route==false && ΔCE>=0.10`), cost descriptive-only, **rerun=false**, values reused from `v70r1_results.json`
**Data**: `v70_data_registry.json` Stage2 `CAL1024/VAL256` frames, `Q=1024`, `N=1024`, `COLS=10240`, `TARGET_F_PLANNING=1.3`
**4SHA**: `accepted 0509d10ba78902b36f6bcf447f1ebfe289e03fc89b` / `initial 179916f7cfec0ea469683bb78083c3752700193d` / `contract 99e6b25f1e7d14ae5168acabc3e4c42e31dafd4d` / `current 36d493d82c640f3902c5a7dcd603fdcbb2b03aef` | **Data SHA** `84d62779`
**Execution**: `f_actual=NOT_MEASURED` `decoder_calls=0` `used_test=false` `used_val_in_selection=false` `ce_decomposition_claimed=false` `planning_f_is_not_achieved_f=true`

## Terminals (first-match, 5)

1. `V70R1_EVIDENCE_INVALID` — M0 mismatch V70 `<1e-9` / non-finite CE / λ boundary
2. `V70R1_TRANSLATION_INVARIANCE_REJECTED` — both M1 & M2 worse than M0 by >0.05
3. `V70R1_PARAMETRIC_MODEL_CHANGES_CAPACITY_ROUTE` — best parametric classification != table
4. `V70R1_PARAMETRIC_MODEL_REDUCES_VAL_CE` — `route_change==false && ΔCE>=0.10` (cost `sample_curve`/`estimation_cost_win` descriptive-only)
5. `V70R1_PARAMETRIC_MODEL_NO_VALUE` — otherwise

`best_parametric = argmin(CE_circulant, CE_parametric)`; `ΔCE = CE_table − CE_best`. Overall = first non-zero terminal in order.

## Per-session summary (mechanical reclassification, no rerun, rerun=false)

| source | session | CE_table | CE_circ | CE_param | ΔCE | best | route_change | estimation_cost_win | terminal |
|---|---|---|---|---|---|---|---|---|---|
| 1M | 20260123_1M_600k_0dB | 7.1500 | 6.7890 | 6.7871 | 0.3629 | parametric | false | true (descriptive-only) | V70R1_PARAMETRIC_MODEL_REDUCES_VAL_CE |
| 1p5M | 20260107_PPLN_1p5M | 7.5472 | 7.1830 | 7.1809 | 0.3663 | parametric | true | true (descriptive-only) | V70R1_PARAMETRIC_MODEL_CHANGES_CAPACITY_ROUTE |
| 2M | 20260123_2M_1p2M_0dB | 8.3901 | 8.0547 | 8.0531 | 0.3370 | parametric | false | true (descriptive-only) | V70R1_PARAMETRIC_MODEL_REDUCES_VAL_CE |

- `estimation_cost_win` and `sample_curve` are **descriptive-only**, do not trigger terminals. `R2 rerun=false`.
- `M0 cost=0` trigger: M0 never wins on cost; `estimation_cost_win` compares best_parametric vs table drift at 64 frames, descriptive-only, not a terminal.
- `V70_reproduction` reproduces V70 `CE_full_VAL` `<1e-9` for all sessions → not EVIDENCE_INVALID.
- No `TRANSLATION_INVARIANCE_REJECTED` (all parametric models beat table).

## Per-source × three-model complete table (9 fields per model)

9 fields per model: `CE_VAL` / `CE_CAL` / `cal_val_gap` / `MAP_acc` / `Fano_ub` / `required` / `gap` / `f_max` / `classification` (plus `n_params` for reference). All from `v70r1_results.json`, no rerun.

| source | model | CE_VAL | CE_CAL | cal_val_gap | MAP_acc | Fano_ub | required | gap | f_max | class | n_params |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1M | M0 table | 7.1500 | 5.8225 | 1.3275 | 0.4115 | 6.8612 | 9519 | 721 | 1.3899 | FEASIBLE | 1048577 |
| 1M | M1 circulant | 6.7890 | 6.7439 | 0.0451 | 0.4115 | 6.8612 | 9038 | 1202 | 1.4638 | FEASIBLE | 1025 |
| 1M | M2 parametric | 6.7871 | 6.7479 | 0.0393 | 0.4115 | 6.8612 | 9036 | 1204 | 1.4642 | FEASIBLE | 4 |
| 1p5M | M0 table | 7.5472 | 6.1345 | 1.4127 | 0.3705 | 7.2455 | 10047 | 193 | 1.3167 | MARGINAL | 1048577 |
| 1p5M | M1 circulant | 7.1830 | 7.1343 | 0.0487 | 0.3705 | 7.2455 | 9563 | 677 | 1.3835 | FEASIBLE | 1025 |
| 1p5M | M2 parametric | 7.1809 | 7.1382 | 0.0427 | 0.3705 | 7.2455 | 9560 | 680 | 1.3839 | FEASIBLE | 4 |
| 2M | M0 table | 8.3901 | 7.1103 | 1.2799 | 0.2748 | 8.0993 | 11169 | -929 | 1.1844 | NO_INFORMATION_MARGIN | 1048577 |
| 2M | M1 circulant | 8.0547 | 8.0301 | 0.0246 | 0.2748 | 8.0993 | 10723 | -483 | 1.2338 | NO_INFORMATION_MARGIN | 1025 |
| 2M | M2 parametric | 8.0531 | 8.0339 | 0.0193 | 0.2748 | 8.0993 | 10721 | -481 | 1.2340 | NO_INFORMATION_MARGIN | 4 |

Formulas: `required=ceil(1.3·1024·CE_VAL)` not capped; `gap=10240-required`; `f_max=(10240-64)/(1024·CE_VAL)` channel ceiling independent of planning f; `Fano_ub` diagnostic only, not H estimate; `n_params` = 1048577 / 1025 / 4.

## Sample curve (descriptive-only)

`sample_curve` at CAL prefixes 32/64/128/256/512/1024 frames → same VAL CE; descriptive-only, not terminal. M0 drift 0.95/0.81/0.67 at 64 frames vs parametric ≈0, but not used for decision (M0 cost descriptive-only).

## terminal_priority_note / PRE_RESULT_ORDERING_DEVIATION

first-match ordering `EVIDENCE_INVALID(1) > REJECTED(2) > CHANGES(3) > REDUCES(4) > NO_VALUE(5)` determines overall as first `terminal_counts>0`, not majority count. This run: `CHANGES=1, REDUCES=2, NO_VALUE=0` — majority would be `REDUCES`, but ordering gives `overall=CHANGES`. Recorded as `terminal_priority_note: CHANGES(1) precedes REDUCES(2)` and `PRE_RESULT_ORDERING_DEVIATION: true` in `v70r1_results.json` and `v70r1_manifest.json`. Guard R70R1-08 enforces this ordering.

## Aggregate

- `terminal_counts`: EVIDENCE_INVALID 0 / REJECTED 0 / CHANGES 1 / REDUCES_VAL_CE 2 / NO_VALUE 0
- `overall`: `V70R1_PARAMETRIC_MODEL_CHANGES_CAPACITY_ROUTE` (first non-zero is CHANGES, see ordering deviation above)

## Sync

- `v70r1_results.json` lifecycle `DEVELOPMENT_RESULT_CANDIDATE / DECODER_FREE_EXECUTION_COMPLETE`, `f_actual=NOT_MEASURED`, `decoder_calls=0`, `used_test=false`, `V72_NOT_STARTED=true`, `4SHA 0509d10b/179916f7/99e6b25f/36d493d8`, `rerun=false`, `terminal_priority_note` + `PRE_RESULT_ORDERING_DEVIATION=true` recorded, 5 terminals + `plan_revision` R2
- `v70r1_table.csv/.json` rows sync'd (mechanical, 9-field table above is expanded view)
- `v70r1_manifest.json` guards R70R1-01..10 all true, counts 5, `f_actual=NOT_MEASURED`, `decoder_calls=0`, `terminal_priority_note` + `PRE_RESULT_ORDERING_DEVIATION`
- No new decoder, no `run_01`, no `src/` change, no pairs rescan (`rg decode_ == 0`, `py_compile PASS`)
