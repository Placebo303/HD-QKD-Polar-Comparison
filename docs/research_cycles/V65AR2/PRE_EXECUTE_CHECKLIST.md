# V65AR2 Pre-EXECUTE Checklist — DECODER_FREE first-match pipeline (corrected Stage0)

**Date**: 2026-08-31
**Accepted Plan SHA**: `70f9ed8ece53704374d37810a163a519e57be6e9` (frozen, no drift)
**Implementation SHA (old invalid)**: `3a6c4fac255c7094a357468140129c8149f6fa9d` (Stage0 misapplication, permanently `ENGINEERING_INVALID` per INVALID_RESULT_NOTE.md — no retroactive signing)
**Implementation SHA (reviewed)**: `ffe40e6643e2a1a4edc4a99063e8555d5670bc4d` (DECODER_FREE, corrected Stage0, 20/20) — independent rerun 15/15 PASS, complete 20/20 PASS
**New implementation SHA (post-verdict)**: `git rev-parse HEAD` after verdict commit — must equal `origin/formal-ir-mainline` (40-char), `git cat-file -e 70f9ed8` PASS; only `HEAD == origin` after re-derive authorizes EXECUTE_AUTH
**Branch**: `formal-ir-mainline`
**Data SHA**: `84d62779` (d=1024 bw=200 pairing=nearest legacy_v1 period 204800 gate 200 thr 40000)
**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — no decoder, no run_01

## Standard Gates (must all PASS before EXECUTE_AUTH; DECODER_FREE candidate)

| Gate | Check | Expected | Result |
|------|-------|----------|--------|
| G0 HEAD/origin binding | `git rev-parse HEAD == git rev-parse origin/formal-ir-mainline` (40-char, `git fetch` re-derived) | match | PASS — `ffe40e66 == ffe40e66` reviewed; post-verdict new SHA to be re-derived (`git rev-parse HEAD == origin/formal-ir-mainline`) before EXECUTE_AUTH |
| G0 Accepted Plan reachable | `git cat-file -e 70f9ed8ece53704374d37810a163a519e57be6e9` | 0 exit | PASS — plan commit exists |
| G0 Plan binding | `rg "70f9ed8" scripts/v65ar2_pipeline.py` == 2 hits (`ACCEPTED_PLAN_SHA` + header) | 2 hits | PASS |
| G0 Stale SHA | `rg "efd34ef"` (V55 stale constant) `scripts/ comparison_bench/tests/ docs/` == 0 hits; `rg "3a6c4fa"` as ACCEPTED_PLAN == 0 hits | 0 hits | PASS — only 70f9ed8 is accepted plan |
| G1 py_compile | `python -m py_compile scripts/v65ar2_pipeline.py comparison_bench/tests/test_v65ar2_pipeline.py` | PASS | PASS 2026-08-31 |
| G2 pytest 15+5 | `python -m pytest comparison_bench/tests/test_v65ar2_pipeline.py -v -p no:cacheprovider --basetemp workspace/v65ar2_test` | 20 passed (15 baseline +5 Stage0 isolation) | PASS 20/20 (see log) |
| G3 candidate order frozen | `rg "sort.*CE\|rank.*candidate\|sort.*candidate" scripts/` == 0 hits; `candidate_order == ["162148","2500K","160254"]` | 0 hits | PASS |
| G3 zero overlap | `check_frame_overlap` CAL∩VAL empty, CAL∪VAL∩TEST empty, forbidden disjoint; cross-stage `s0∩s1==0 s0∩s2==0 s1∩s2==0` in `run_pipeline` assert | verified by test 11,18,19 | PASS |
| G3 TEST non-participation | `used_test_in_estimation==False` every phase; `rg "TEST.*NLL\|TEST.*CE"` in estimator == 0; test 09,10 | True | PASS |
| G3 m not cap | `rg "min\(16" scripts/v65ar2_pipeline.py` == 0 hits; `ceil_rate = ceil(1.3*1024*CE/5)` raw, `m>=1024→FULL_DISCLOSURE` `m>frozen&&<1024→RATE_ADAPTATION` | 0 hits | PASS |
| G3 UNREACHABLE | Stage0 first-match `UNREACHABLE_FIRST_MATCH`, `UNREACHABLE_R`, Stage1 fail → Stage2 `UNREACHABLE_S1` (test 19) | verified | PASS |
| G3 decoder-free | `rg "decode_" scripts/v65ar2_pipeline.py` == 0 hits | 0 hits | PASS |
| G4 additive no overwrite | `if Path.exists(): raise FileExistsError` in phase_r + run_pipeline + _write_additive (6 sites) | fail-closed | PASS by code |
| G5 run_01 absent | `Test-Path comparison_bench/outputs_comparison/formal_ir_methods/v65ar2_pipeline/run_01` == False; `Test-Path v66*/run_01` == False | not exists | PASS |
| G6 Stage0 corrected | `run_stage0` no `hierarchical_estimate` call (monkeypatch boom test 16 PASS), extreme CE not affect (test 17 PASS), bad frame FAIL (test 18) | PASS | PASS |
| G7 forbidden propagation | `forb_s1=s0 all_triples`, `forb_s2=s0+s1`, `start_frame = max forbidden+1`, `check_frame_overlap(..., forbidden)` | PASS by test 11 | PASS |

## Test log (20 passed, Stage0 isolation 5)

```
test_01_raw_missing_fail_closed PASSED
test_02_contract_missing PASSED
test_03_channel_ambiguity PASSED
test_04_candidate_specific_timing_channel PASSED
test_05_stage0_real_8x256 PASSED
test_06_first_match_stop PASSED
test_07_stage1_real_estimate PASSED
test_08_stage2_real_estimate PASSED
test_09_test_loader_unreachable PASSED
test_10_test_insufficient_32 PASSED
test_11_frame_overlap_injection PASSED
test_12_model_not_stable PASSED
test_13_rate_adaptation PASSED
test_14_full_disclosure PASSED
test_15_cli_no_dryrun_fake_additive_no_overwrite PASSED
test_16_stage0_estimator_monkeypatch_no_call PASSED
test_17_stage0_extreme_ce_not_affect PASSED
test_18_stage0_bad_frame_fails PASSED
test_19_stage0_first_match_unreachable PASSED
test_20_stage1_runs_ce_lambda_rate PASSED
```

Run: `python -m pytest comparison_bench/tests/test_v65ar2_pipeline.py -v -p no:cacheprovider --basetemp workspace/v65ar2_test` — 31s, 0 failed.

## Preserved invariants

- Old run `3a6c4fa` stays `ENGINEERING_INVALID` (Stage0 misapplication); no retroactive signing, no `run_01` built from it.
- `DECODER_FREE` — no `decode_*`, no `run_01` creation in this change; only `docs/research_cycles/V65AR2/` + `scripts/` + `tests/` modified.
- Additive outputs: existing target `FileExistsError` (no overwrite of `results/` or `comparison_bench/outputs_comparison/`).
- Frame discipline: `FRAME 256 pairs`, `BLOCK 4×256`, `legacy_v1` mapping, `period 204800`.

## How to re-verify

```
git fetch && git rev-parse HEAD && git rev-parse origin/formal-ir-mainline  # must match
git cat-file -e 70f9ed8ece53704374d37810a163a519e57be6e9 && echo plan_ok
rg "70f9ed8" scripts/v65ar2_pipeline.py
rg "efd34ef" scripts/ comparison_bench/tests/ docs/   # expect 0
python -m py_compile scripts/v65ar2_pipeline.py comparison_bench/tests/test_v65ar2_pipeline.py
python -m pytest comparison_bench/tests/test_v65ar2_pipeline.py -v -p no:cacheprovider --basetemp workspace/v65ar2_test
Test-Path comparison_bench/outputs_comparison/formal_ir_methods/v65ar2_pipeline/run_01  # expect False
```
