# V72P2D4-CAL-RATE PLAN_REVIEW (D4 R1)

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- HEAD: `a7a6ec62` (`HEAD == origin/formal-ir-v72p1-addendum-clean`)
- Change: `formal-ir-v72p2d4-cal-gf32-model-rate-audit`
- Cycle: `V72P2D4-CAL-RATE` / R1 implementation cycle `V72P2D4R1-CAL-GF32-MODEL-RATE`
- Verdict: `PLAN_ACCEPTED_R1`
- Lifecycle after this record: `PLAN_ACCEPTED / EXECUTE_NOT_AUTHORIZED`
- Date: `2026-09-05`

## 1. Review scope (read-only, 4 files)

1. `openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/proposal.md`
2. `openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/design.md`
3. `openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/tasks.md`
4. `openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/specs/spec.md`

No parquet read, no decoder call, no VAL read, no `run_01`, no formal output created during this review.

## 2. R1 revision: SELECT_DELTA 0.02 frozen per implementation

- Four artifacts uniformly state selection closeness as `Δ<0.02 bit/symbol` with frozen note `R1冻结：按实现SELECT_DELTA=0.02冻结，不可调`.
- This revises the prior `0.01` draft to match the R1 implementation constant `SELECT_DELTA=0.02` (`comparison_bench/src/comparison_bench/formal_ir/v72p2d4r1_cal_gf32_model_rate_audit.py:57`, test `t1_12_selection_delta002`).
- Frozen meaning: 0.02 is a fixed selection tie-break width for this audit only (simpler model wins when within 0.02 of the best fold-mean); it is not tunable, not learned from TEST/VAL/held-out, and does not change budgets, routes, or chain tolerances.
- All other frozen numbers unchanged: `F0=702..957/F1=958..1213/F2=1214..1469/F3=1470..1725`, `counts[a,b]` axis0 Alice/axis1 Bob, `symbol=low+32*high`, floor exact `1e-300`, chain `<1e-10`, R5 `6.422/5.083/11.505` with `REAL_CAL_EXACT_MATCH=false`, stability `std>0.10/range>0.20`, `N=1024/f∈{1.0,1.1,1.2,1.3}/rows=ceil(N*CE*f/5)`, history `16/200/216` rows, routes `A=fit@1.3/C=mismatch@1.0/B=fit@1.0∧mismatch@1.3`, `M3_EXIT_AMBIGUOUS` excluded.

## 3. Acceptance scope

This record accepts the R1-revised plan only. It does not accept a result or authorize execution beyond the already-completed CAL-only scalar audit files.

- `development_execution_authorized: false`
- `formal_execution_authorized: false`
- `real_execution_authorized: false`
- `scientific_promotion: false`

No decoder execution, VAL read, new matrix, checksum/hash/tag, or formal `run_01` authorized.
