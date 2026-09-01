# V70R1 Parametric Channel Model Check Report (R2 — 5 terminals, mechanical reclassification)

**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` / `V72_NOT_STARTED=true`
**Plan revision**: R2 mechanical — insert `REDUCES_VAL_CE` (`route==false && ΔCE>=0.10`), cost descriptive-only, no rerun, values reused from `v70r1_results.json`
**Data**: `v70_data_registry.json` Stage2 `CAL1024/VAL256` frames, `Q=1024`, `N=1024`, `COLS=10240`, `TARGET_F_PLANNING=1.3`

## Terminals (first-match, 5)

1. `V70R1_EVIDENCE_INVALID` — M0 mismatch V70 `<1e-9` / non-finite CE / λ boundary
2. `V70R1_TRANSLATION_INVARIANCE_REJECTED` — both M1 & M2 worse than M0 by >0.05
3. `V70R1_PARAMETRIC_MODEL_CHANGES_CAPACITY_ROUTE` — best parametric classification != table
4. `V70R1_PARAMETRIC_MODEL_REDUCES_VAL_CE` — `route_change==false && ΔCE>=0.10` (cost `sample_curve`/`estimation_cost_win` descriptive-only)
5. `V70R1_PARAMETRIC_MODEL_NO_VALUE` — otherwise

`best_parametric = argmin(CE_circulant, CE_parametric)`; `ΔCE = CE_table − CE_best`. Overall = first non-zero terminal in order.

## Per-session (mechanical reclassification, no rerun)

| source | session | CE_table | CE_circ | CE_param | ΔCE | best | route_change | estimation_cost_win | terminal |
|---|---|---|---|---|---|---|---|---|---|
| 1M | 20260123_1M_600k_0dB | 7.1500 | 6.7890 | 6.7871 | 0.3629 | parametric | false | true (descriptive) | V70R1_PARAMETRIC_MODEL_REDUCES_VAL_CE |
| 1p5M | 20260107_PPLN_1p5M | 7.5472 | 7.1830 | 7.1809 | 0.3663 | parametric | true | true (descriptive) | V70R1_PARAMETRIC_MODEL_CHANGES_CAPACITY_ROUTE |
| 2M | 20260123_2M_1p2M_0dB | 8.3901 | 8.0547 | 8.0531 | 0.3370 | parametric | false | true (descriptive) | V70R1_PARAMETRIC_MODEL_REDUCES_VAL_CE |

- `estimation_cost_win` and `sample_curve` are **descriptive-only**, do not trigger terminals.
- `V70_reproduction` reproduces V70 `CE_full_VAL` `<1e-9` for all sessions → not EVIDENCE_INVALID.
- No `TRANSLATION_INVARIANCE_REJECTED` (all parametric models beat table).

## Aggregate

- `terminal_counts`: EVIDENCE_INVALID 0 / REJECTED 0 / CHANGES 1 / REDUCES_VAL_CE 2 / NO_VALUE 0
- `overall`: `V70R1_PARAMETRIC_MODEL_CHANGES_CAPACITY_ROUTE` (first non-zero is CHANGES)

## Sync

- `v70r1_results.json` per_session terminals and `terminal_counts` updated to 5 terminals + `plan_revision` R2
- `v70r1_table.csv/.json` rows sync'd (mechanical)
- `v70r1_manifest.json` guards R70R1-01..10 all true, counts 5
- No new decoder, no `run_01`, no `src/` change, no pairs rescan (`rg decode_ == 0`, `py_compile PASS`)
