# V63 Pre-EXECUTE Checklist — Formal Implementation 10390cfa → HEAD (4-blocking fixed)

**Date**: 2026-08-30
**Predecessor implementation SHA**: 10390cfa52f2b5e3e6c7c382cfb2d4c316471218 (FAIL/REVISE_REQUIRED — 4 blocking)
**Accepted Plan SHA**: 397c1bb6d60cdf6dfa00d34bfae2eb1ca231d20a (frozen, no drift)
**New implementation SHA**: `git rev-parse HEAD` at push time — must equal `origin/formal-ir-mainline`; current HEAD b4d94e66718a2b77b411e7271745788ee875f9a6, final HEAD after amend/push to be verified via `git rev-parse HEAD == origin/formal-ir-mainline`
**Lifecycle**: PLAN_REVISION_CANDIDATE → PRODUCTION_IMPLEMENTATION — 4 blocking fixed, EXECUTE_AUTH still required for real decoder

## Blocking Fix Verification

| # | Blocking | Fix | Evidence |
|---|----------|-----|----------|
| 1 | synthetic fallback random generation in `_load_entry` | Removed fallback; `execute_v63_shell_smoke.py` and `execute_v63_shell_development.py` now fail-closed: missing parquet / read exception / row count !=1024 → `EVIDENCE_INVALID` (RuntimeError) — no random Alice/Bob | `grep -n "EVIDENCE_INVALID" scripts/execute_v63_shell_*.py` shows 3 throws per file; `grep -n "random\|rng.integers" scripts/execute_v63_shell_*.py` returns 0 for loader |
| 2 | test imports `comparison_bench.src.comparison_bench...`遮蔽 | Unified to `from comparison_bench.methods... / pipeline... / types...` with `sys.path.insert(0, comparison_bench/src)` in test header; `pythonpath`冲突消除 | `rg "comparison_bench.src.comparison_bench" tests/` → 0 hits; `pytest -p no:cacheprovider --basetemp workspace/v63_preexec_test` → 12 passed |
| 3 | `decoder_calls // len(ents)` truncation | Mechanical per-stage mapping `base=2 delta8=3 delta16=4` per `stage_used`; per-batch `assert sum(per_block_calls)==shell.decoder_calls`; global `assert sum(records decoder_calls)==total_calls` before summary; fake runner also `sum(map)` | `grep -n "calls_map" scripts/execute_v63*.py` and `comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py`; tests still 12 passed |
| 4 | V63P0 docs still decoder-free spike | This checklist + DELIVERY.md §Pre-EXECUTE + REVIEW_VERDICT.md §Pre-EXECUTE added; records new SHA, Accepted Plan, HEAD/origin, py_compile, parquet 9/9, run_smoke absence, 18-36 budget | This file + updated DELIVERY.md + REVIEW_VERDICT.md |

## Standard Pre-EXECUTE Gates (must all PASS before EXECUTE_AUTH)

| Gate | Command / Check | Result |
|------|-----------------|--------|
| G0 HEAD/origin binding | `git rev-parse HEAD` == `git rev-parse origin/formal-ir-mainline` (40-char) | PASS pre-push `git rev-parse HEAD` b4d94e66… ; post-push must re-derive and match checklist | 
| G0 Accepted Plan binding | `grep ACCEPTED_PLAN_SHA` == `397c1bb6d60cdf6dfa00d34bfae2eb1ca231d20a` in adapter + CLI | PASS — `rg 397c1bb6` 2 hits in adapter/scripts; fail-closed on drift |
| G1 py_compile | `python -m py_compile comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py comparison_bench/src/comparison_bench/pipeline/shell_integration.py scripts/execute_v63_shell_smoke.py scripts/execute_v63_shell_development.py` | PASS 2026-08-30 |
| G2 pytest standard | `python -m pytest tests/test_v63_shell_adapter.py -v -p no:cacheprovider --basetemp workspace/v63_preexec_<uuid>` | PASS 12 passed (T1-T12) 2026-08-30 |
| G3 scoped dirty | `git status --porcelain` filtered SCOPED_TRACKED (`nbldpc_shell_adapter.py`, `shell_integration.py`, `v54_...`, `v38_...`, `v35_...`) == empty | PASS — only untracked outputs remain |
| G4 parquet 9/9 readable | Load `type2_1M/pairs.parquet` etc, filter by `v63_smoke_registry.json` frame_ids → 1024 rows per block | PASS 9/9 (see log below) |
| G5 run_smoke absent | `Test-Path comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_smoke` == False | PASS — not exists |
| G6 budget | Smoke hard cap `SMOKE_HARD_CAP=36` (9 L1 + 9 base + ≤9 stage1 + ≤9 stage2 = 18-36); Dev `360` | PASS — code asserts 18-36 / 180-360 |
| G7 additive output | Output root exists → BLOCKED; scripts `mkdir(parents=True, exist_ok=False)` | PASS by code inspection |

## Preserved Passed Items (not regressed)

- Real V54 three-stage L1 q reuse: `q=softmax(BP) → P(U2)` via `get_l1_app_prior_l2`, `H1/LaneC/H_joint1/H_total` frozen nested, verification-only incremental — unchanged
- SHA binding enforcement in both CLIs (`HEAD != authorized` / `origin != authorized` → BLOCKED)
- Three-tier leakage tag single count `base 1064/1094/1104 delta8 +40 delta16 +40 tag 64 L2-only` — unchanged
- No auto domain calibration: `domain_check(is_new_or_incompatible=True) → DOMAIN_CALIBRATION_REQUIRED` — unchanged
- Output root防覆盖: `if output_root.exists(): BLOCKED` — unchanged

## Parquet 9/9 Log (2026-08-30)

```
v63_smoke_1M_0018 1M 1024
v63_smoke_1M_0245 1M 1024
v63_smoke_1M_0392 1M 1024
v63_smoke_1p5M_0004 1p5M 1024
v63_smoke_1p5M_0333 1p5M 1024
v63_smoke_1p5M_0546 1p5M 1024
v63_smoke_2M_0004 2M 1024
v63_smoke_2M_0403 2M 1024
v63_smoke_2M_0721 2M 1024
ok 9/9
```

## How to re-verify (standard command)

```
python -m py_compile comparison_bench/src/comparison_bench/methods/nbldpc_shell_adapter.py comparison_bench/src/comparison_bench/pipeline/shell_integration.py scripts/execute_v63_shell_*.py tests/test_v63_shell_adapter.py
python -m pytest tests/test_v63_shell_adapter.py -v -p no:cacheprovider --basetemp workspace/v63_preexec_test
git rev-parse HEAD; git rev-parse origin/formal-ir-mainline; rg 397c1bb6
Test-Path comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_smoke
```

## Lifecycle Update

- Prior DELIVERY.md / REVIEW_VERDICT.md were `DECODER_FREE_SPIKE` (5602f11c/397c1bb6 plan only, no real decoder). This checklist upgrades V63P0 to `PRODUCTION_IMPLEMENTATION` — real V54 L1APP+Δ8+Δ8 wiring, explicit fake_runner, fail-closed evidence, mechanical accounting. `EXECUTE_NOT_AUTHORIZED` remains until main thread grants `EXECUTE_AUTH` with exact new SHA binding.
