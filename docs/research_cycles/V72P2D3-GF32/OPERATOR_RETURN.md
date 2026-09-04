# V72P2D3-GF32 Operator Return (fail-closed)

- Cycle: `V72P2D3-GF32`, branch `formal-ir-v72p1-addendum-clean`, HEAD `8f44e5ff5bb697fa1eebf0b3c660d531dcafd7aa` (== remote at execution).
- Authorized invocation consumed: `1/1` (Pre-EXECUTE PASS authorized `real=true, formal=false, promotion=false`; post-run `completed=1`, `real=false`, `formal=false`, `promotion=false`).
- Production command (single invocation, no retry): `python scripts/v72p2d3_gf32_contrast.py --phase real --execute-real` with `registry/frames/matrices=None` (parquet never opened, true decoder never called, production root never created before gate).
- Exit: `2` fail-closed: `real chain needs injected registry/frames/matrices; parquet is never opened here` (runner production gate, `PermissionError` path).
- Zero files: `comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904/` absent; no `manifest.json/results.json/table.csv/report.md` fabricated; no `run_01`; D1/D2 and frozen baseline untouched.
- Authorization consumed, retry forbidden: single-invocation budget (`invocation600`) spent; failure `BLOCKED`, no rerun/tuning/resume per frozen packet.
- Pre-RESULT: `PASS` (fail-closed terminal confirmed; zero-file + no-claim verified). No scientific claim, no FER/SKR, no promotion.
- Lifecycle out: `BLOCKED_FAIL_CLOSED` (leaves `PRE_EXECUTE_PASSED`); `decoder_executed=false`.
