# V64 Pre-EXECUTE Checklist — 24 blocks 8/source 48-96 hard cap96

**Accepted Plan SHA**: `760cb2967c7f5d5548a68f056458ef89398de3f2` (no drift, `rg 760cb296` 1+ hits)
**Implementation SHA**: `07804284f5a32eb4569d2d5cfbd413ecb7ca46ff` (HEAD == origin/formal-ir-mainline — must equal --authorized-target-sha at EXECUTE)
**Branch**: `formal-ir-mainline`
**Data SHA**: `84d62779` (d=1024 bw=200 pairing=nearest legacy_v1)
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — DECODE_FORBIDDEN until authorized

## Standard Gates (must PASS before EXECUTE_AUTH)

| Gate | Check | Expected | Result |
|------|-------|----------|--------|
| G0 HEAD/origin binding | `git rev-parse HEAD == origin/formal-ir-mainline == --authorized-target-sha == 07804284f5a32eb4569d2d5cfbd413ecb7ca46ff` | 40-char match | PASS |
| G0 Accepted Plan | `ACCEPTED_PLAN_SHA == 760cb2967c7f5d5548a68f056458ef89398de3f2` in `v64_full_symbol_verification.py` + `execute_v64_fresh_verify.py` | 1 hit each, `rg 119ba151` 0 hits | PASS (verified) |
| G1 py_compile | `python -m py_compile v64_full_symbol_verification.py execute_v64_fresh_verify.py generate_v64_fresh_registry.py` | PASS | PASS |
| G2 pytest | `pytest test_v64_instrumentation.py -p no:cacheprovider --basetemp workspace/v64_final` 12 passed (48-96, 24/8, gap>=4, SHA binding, no fallback, tmp_path partial retention) | 12 passed | PASS (12/12) |
| G3 scoped dirty | `git status --porcelain` filtered SCOPED_TRACKED (`v64_full_symbol_verification.py`,`execute_v64_fresh_verify.py`,`generate_v64_fresh_registry.py`,`v54*`, `v38*`,`v35*`) == empty | empty | PASS (staged only) |
| G4 registry | `build_v64_fresh_registry() ==24, per-source 8, gap>=4, zero overlap V48-V63, K2>=24` | 24 blocks, gap>=4 | PASS (24, 8/source, starts [74..384] etc) |
| G5 run_01 absent | `Test-Path comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/run_01` == False | not exists | PASS (run_01 absent) |
| G6 budget | `48-96 hard cap96 97th reject, L2 24-72, per-block 2-4` | code enforces | PASS (48-96) |
| G7 additive output | `if output_root.exists(): BLOCKED` | fail-closed | PASS by code |
| G8 domain | `84d62779`, `BLOCK_LENGTH 1024`, `pairs 1024`, `H rank/nested` | PASS | PASS (decoder-free preflight) |

## Budget/Gate Sync (24-block)

- Budget: `L1 24 + base24 + stage1<=24 + stage2<=24 =48-96 hard cap96 (L2 24-72) 97th reject`
- Gate: `exact_full >=19/24 overall (79.17%) and per-source >=6/8 (75%) and undetected_full==0 and all exact tag_ok_full==True`
- Records denominator: `overall/24 per_source 8`
- Registry: `v64_fresh_registry.json authoritative 24-block, deterministic_four_consecutive_frames_heldout_fresh_v64, gap>=4, zero overlap V48-V63`

## Preserved Invariants (not changed)

- Decoder frozen `90/1.0 poly37`, `TRAIN prior`, `H1-16 rank16`, `Lane C m2 184/190/192`, `H_inc1/2 8x1024 det`, `H_total 200/206/208 nested`, `independence 8`, `row<=16 col<=1 E~96`
- Tag single 64-bit, leak `5*m_total+64` double-checked `stage1-base=40 stage2-stage1=40` base `1064/1094/1104` +40/+80
- `same_decode_single_tag` dual `tag_ok_l2` + `tag_ok_full` from `s_hat=32*u1+u2` canonical, not double calls/leak
- `DECODE_FORBIDDEN` until `EXECUTE_AUTH --execution-authorized --authorized-target-sha <implementation SHA>`

## How to re-verify

```
git fetch origin && git rev-parse HEAD && git rev-parse origin/formal-ir-mainline
rg 760cb296 -- comparison_bench/src/comparison_bench/formal_ir/v64_full_symbol_verification.py scripts/execute_v64_fresh_verify.py
python -m py_compile comparison_bench/src/comparison_bench/formal_ir/v64_full_symbol_verification.py scripts/execute_v64_fresh_verify.py
python -m pytest comparison_bench/tests/test_v64_instrumentation.py -v -p no:cacheprovider --basetemp workspace/v64_final
python -c "import sys; sys.path.insert(0,'comparison_bench/src'); from comparison_bench.formal_ir.v64_full_symbol_verification import build_v64_fresh_registry; print(len(build_v64_fresh_registry()))"
Test-Path comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/run_01  # expect False
```
