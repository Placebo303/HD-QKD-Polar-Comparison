# V72P2D3-GF32 Operator Return R2 (production unreachable, fail-closed)

- Cycle: `V72P2D3-GF32`, R2 execution_cycle `V72P2D3_GF32_R2_DECODER`, branch `formal-ir-v72p1-addendum-clean`, HEAD `a393f83960c8434495fd0b43fb831dc7cf0442ce` (== remote at record).
- R2 production unreachable: single production entry attempted, failed before prep: `invocation 1 / prep 0 / decoder 0`, exit `2` fail-closed; true kernel never entered, no decoder consumption (`decoder_execution_attempts=0`, `r2_attempts=0`, `r2_completed=0`).
- Zero files: `comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904/` absent; no `manifest.json/results.json/table.csv/report.md` fabricated; no `run_01`; D1/D2 and frozen baseline untouched.
- Authorization: `real_execution_authorized=false`, `r2_real_execution_authorized=false`, `formal=false`, `promotion=false`; no retry/rerun/tuning/resume.
- Pre-RESULT: `BLOCKED` (production-unreachable terminal confirmed; zero-file + no-claim verified). No scientific claim, no FER/SKR, no promotion.
- Lifecycle out: `BLOCKED_PROD_UNREACHABLE` (`decoder_executed=false`, `syndrome_published_bits=0`).
