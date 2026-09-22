# V72P2D3-GF32 Operator Return R4 (final-write mismatch, blocked)

- Cycle: `V72P2D3-GF32`, R4 execution_cycle `V72P2D3_GF32_R4_DECODER`, branch `formal-ir-v72p1-addendum-clean`, HEAD `10d5e8e3f16fd5204b2a27d88008f501032b5e1d` (== remote at record).
- R4 result: `BLOCKED_FINAL_WRITE_MISMATCH`: single production invocation attempted; entry guard passed but final-write gate refused (`入口过终写拒`), command exit `2`; true kernel never entered, no decoder consumption (`decoder_execution_attempts=0`, `r4_attempts=0`, `r4_completed=0`).
- 全零: `comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904/` absent; no `manifest.json/results.json/table.csv/report.md` fabricated; no `run_01`; decoder `0` / data `0` / disclosure `0` (`syndrome_published_bits=0`); D1/D2 and frozen baseline untouched.
- Authorization: `real_execution_authorized=false`, `r4_real_execution_authorized=false`, `formal=false`, `promotion=false`; 不重试 (no retry/rerun/tuning/resume).
- Pre-RESULT: `FAIL` (final-write-mismatch terminal confirmed; zero-file + no-claim verified). 无结论: no scientific claim, no FER/SKR, no promotion.
- Lifecycle out: `PLAN_REVISE_REQUIRED`; next gate `R5_MATH_INTERFACE_AND_RATE_AUDIT`.
- R2/R3 preserved: `OPERATOR_RETURN_R2.md` / `OPERATOR_RETURN_R3.md` and all `r2_*` / `r3_*` state untouched; no code change.
