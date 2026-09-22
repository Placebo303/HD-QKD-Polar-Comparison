# V65AR2 Pre-EXECUTE Verdict — REVISE_REQUIRED_BINDING resolved

**Date**: 2026-08-31
**Cycle**: `V65AR2` (first-match-pipeline, DECODER_FREE)
**Accepted Plan SHA**: `70f9ed8ece53704374d37810a163a519e57be6e9` (frozen; `git cat-file -e 70f9ed8` PASS, `rg 70f9ed8` 2 hits in `scripts/v65ar2_pipeline.py`, `rg efd34ef` 0 hits)
**Reviewed Implementation SHA**: `ffe40e6643e2a1a4edc4a99063e8555d5670bc4d` (DECODER_FREE, corrected Stage0)
**Old Implementation SHA**: `3a6c4fac255c7094a357468140129c8149f6fa9d` — permanently `ENGINEERING_INVALID` per `INVALID_RESULT_NOTE.md` (Stage0 misapplication: executed `hierarchical_estimate`/`CE`/`lambda`/`m` on 8-frame sample; plan-frozen Stage0 is materialization-only; old `STAGE0_NO_CANDIDATE` has no elimination effect, no retroactive signing, no `run_01` built from it)
**Branch**: `formal-ir-mainline`
**Data SHA**: `84d62779` (d=1024 bw=200 pairing=nearest legacy_v1 period 204800 gate 200 thr 40000)
**Reviewer**: independent read-only (separate thread, no file edits except this verdict, no decoder invocation)

## Verdict

**code PASS / scientific PASS** — `ffe40e6643e2a1a4edc4a99063e8555d5670bc4d` reviewed, ready for `HEAD == origin/formal-ir-mainline` re-derive; `EXECUTE_AUTH` only after new SHA binding.

## Binding

- `REVIEW_ENTRYPOINT.md --head` and `PRE_EXECUTE_CHECKLIST.md G0` updated to `ffe40e6643e2a1a4edc4a99063e8555d5670bc4d` (this verdict commit).
- Old `3a6c4fa` permanently invalid — not a valid ACCEPTED implementation, no drift allowed (`rg "3a6c4fa" as ACCEPTED_PLAN == 0 hits; only `70f9ed8` is accepted plan; `rg "efd34ef"` 0 hits).
- Post-verdict: `git fetch && git rev-parse HEAD == git rev-parse origin/formal-ir-mainline` (40-char) must be re-derived and recorded; only `HEAD == origin` after push authorizes `EXECUTE_AUTH`. Pre-push `ffe40e66 == ffe40e66` binding already PASS.

## Independent Rerun

- **15/15 independent rerun PASS** — separate thread re-executed `python -m pytest comparison_bench/tests/test_v65ar2_pipeline.py -v -p no:cacheprovider` on `ffe40e66` without using prior logs; all 15 baseline+isolation checks reproduced.
- **Complete 20/20 PASS** — full suite `15 baseline + 5 Stage0 isolation` = 20 passed, 0 failed:
  - `test_01_raw_missing_fail_closed` … `test_15_cli_no_dryrun_fake_additive_no_overwrite` (15 baseline)
  - `test_16_stage0_estimator_monkeypatch_no_call` (Stage0 no `hierarchical_estimate` call — monkeypatch boom)
  - `test_17_stage0_extreme_ce_not_affect` (extreme CE still PASS — Stage0 not using estimator)
  - `test_18_stage0_bad_frame_fails` (bad frame FAIL — materialization fail-closed)
  - `test_19_stage0_first_match_unreachable` (first-match `UNREACHABLE_FIRST_MATCH`/`UNREACHABLE_R`/`UNREACHABLE_S1`)
  - `test_20_stage1_runs_ce_lambda_rate` (Stage1 sole estimator `CE/lambda/m/rate`)
- `py_compile` PASS (`scripts/v65ar2_pipeline.py`, `comparison_bench/tests/test_v65ar2_pipeline.py`).
- `rg "decode_" scripts/v65ar2_pipeline.py` 0 hits — `DECODER_FREE` confirmed; no `run_01` created.

## Code Review (code PASS)

- Candidate order frozen `162148→2500K→160254` first-match; `rg "sort.*CE|rank.*candidate|sort.*candidate"` 0 hits — PASS.
- Stage0 strictly materialization-only (`Phase R PASS + 8×256 pairs + symbols 0..1023 + mapping legacy_v1/period 204800 + forbidden overlap`); no `hierarchical_estimate`/`CE1/CE2`/`lambda`/`unseen`/`m1/m2`/`G2-G8` — PASS (tests 16,17,18).
- Stage1 sole estimator `256/64` → `C_ab 1024×1024 → P_global → λ 4-fold CV [1e-2,1e4] 50-grid+Brent → P_λ* → H_cal+CE1/CE2/CE_full |CE_full-CE1-CE2|<1e-9 → m=ceil(1.3*1024*CE/5)` uncapped (`rg "min(16" 0 hits`) — PASS (test 20).
- Phase R true histogram peak (centered bins, median refine, product sign check), not `peak==delay`; additive, fail-closed (`raw_untouched`, `if exists → FileExistsError`) — PASS.
- Cross-stage zero overlap (`CAL∪VAL∪TEST` disjoint, `s0∩s1==0 s0∩s2==0 s1∩s2==0`, disjoint from V13..V65 forbidden) and `used_test_in_estimation==False` every phase — PASS (test 11,18,19).
- Additive no-overwrite (6 sites `FileExistsError`) and `run_01` absent (`Test-Path .../v65ar2_pipeline/run_01` False) — PASS.

## Scientific Review (scientific PASS)

- Plan `70f9ed8` scope respected: `DECODER_FREE` — no FER/threshold/SKR/security claims; even after future `EXECUTE_AUTH`, bounded development evidence on TTBin materialization only.
- Leakage decomposition consistent: `CE` chain verified, `m` uncapped, rate branches `FULL_DISCLOSURE_LAYER`/`RATE_ADAPTATION_REQUIRED`/`WITHIN_FROZEN_BUDGET` not conflated with candidate FAIL.
- Old `3a6c4fa` correction correctly isolates engineering invalidity; no elimination effect retroactively applied — scientific boundary preserved.

## Gate Summary

| Gate | Result |
|------|--------|
| G0 HEAD/origin binding (`ffe40e66 == ffe40e66` reviewed, post-verdict re-derive required) | PASS |
| G0 Accepted Plan reachable (`70f9ed8` 2 hits, `efd34ef` 0 hits) | PASS |
| G1 py_compile | PASS |
| G2 pytest 20/20 (15/15 independent rerun reproduced) | PASS |
| G3 candidate/overlap/TEST/m/UNREACHABLE/decoder-free | PASS |
| G4 additive no-overwrite | PASS |
| G5 run_01 absent | PASS |
| G6 Stage0 corrected | PASS |
| G7 forbidden propagation | PASS |

## Authorization Condition

Only after `git fetch && git rev-parse HEAD == git rev-parse origin/formal-ir-mainline` re-derived on the new verdict SHA (post-push) may main thread grant `EXECUTE_AUTH`. No execution authorized by this verdict alone.

**Reviewer signature**: read-only, no decoder execution, no `run_01`, no code edits beyond this verdict file (other two docs updated per binding fix).
