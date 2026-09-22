# V65AR2 Review Entrypoint — first-match/stop-on-failure pipeline (DECODER_FREE)

**Cycle**: `V65AR2` (first-match-pipeline)
**Change ID**: `formal-ir-v65ar2-first-match-pipeline`
**Repository**: `Placebo303/HD-QKD_Polar_Comparison`
**Branch**: `formal-ir-mainline`
**Lifecycle state**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`
**Accepted Plan SHA**: `70f9ed8ece53704374d37810a163a519e57be6e9` (frozen; `git cat-file -e 70f9ed8` PASS, `rg 70f9ed8` 1 hit in script, no drift)
**Implementation SHA (reviewed)**: `ffe40e6643e2a1a4edc4a99063e8555d5670bc4d` (DECODER_FREE, corrected Stage0, 20/20) — old `3a6c4fac255c7094a357468140129c8149f6fa9d` permanently `ENGINEERING_INVALID` per `INVALID_RESULT_NOTE.md` (no retroactive signing, no elimination effect)
**Implementation SHA (post-verdict)**: `git rev-parse HEAD` after verdict commit — must equal `origin/formal-ir-mainline` (40-char), new SHA to be re-derived post-push; reviewed binding `ffe40e66 == ffe40e66` PASS
**Predecessor**: `formal-ir-v65-new-session-channel-compatibility` `V65` `9625afb4 PLAN_REVISE_REQUIRED`
**Data SHA**: `84d62779` (d=1024 bw=200 pairing=nearest legacy_v1 period 204800 gate 200 thr 40000)
**Decoder status**: `DECODER_FREE` — `rg "decode_" scripts/v65ar2_pipeline.py` 0 hits, no `run_01` created

## What to review (reading order)

1. `openspec/changes/formal-ir-v65ar2-first-match-pipeline/proposal.md` — frozen candidate order `162148→2500K→160254` first-match, tier A/B/C frozen, Phase R additive
2. `openspec/changes/formal-ir-v65ar2-first-match-pipeline/design.md` — Phase R additive sidecar, Stage0 4+4 materialization-only, Stage1 256/64, Stage2 1024/256+TEST32
3. `openspec/changes/formal-ir-v65ar2-first-match-pipeline/specs/spec.md` — G1-8 incl. G7-aux, rate branches
4. `openspec/changes/formal-ir-v65ar2-first-match-pipeline/tasks.md` — 4-phase pipeline tasks
5. `openspec/changes/formal-ir-v65ar2-first-match-pipeline/INVALID_RESULT_NOTE.md` — old 3a6c4fa Stage0 misapplication, ENGINEERING_INVALID, no elimination effect
6. `scripts/v65ar2_pipeline.py` (corrected) — Stage0 materialization-only, no CE/lambda/m; Stage1/2 real estimator
7. `comparison_bench/tests/test_v65ar2_pipeline.py` — 15+5=20 tests (Stage0 isolation + Stage1 CE/lambda)
8. `docs/research_cycles/V65AR2/PRE_EXECUTE_CHECKLIST.md` — HEAD/origin, plan reachable, stale 0 hits, py_compile, tests, additive, overlap

## Corrected implementation vs old run

- **Old SHA `3a6c4fa` INVALID**: Stage0 executed `hierarchical_estimate`/`CE1/CE2`/`lambda`/`unseen`/`m1/m2` and `G2-G8` on 8-frame sample and used `m_req` to fail candidates. Plan-frozen Stage0 is strictly materialization-only (`Phase R PASS + 8×256 pairs + symbols 0..1023 + mapping legacy_v1/period 204800 + forbidden overlap`). Old `STAGE0_NO_CANDIDATE` has no elimination effect; retained as `ENGINEERING_INVALID`, **no retroactive signing**.
- **Corrected SHA**: `run_stage0` no longer calls `hierarchical_estimate`/`CE`/`lambda`/`m`; Stage1 alone runs `256+64` estimator. Verified by 5 new tests: monkey-patch boom, extreme CE still PASS, bad frame FAIL, first-match UNREACHABLE, Stage1 CE/lambda/rate.

## Scope of the frozen plan (DECODER_FREE)

- Candidates `162148(A) → 2500K(B) → 160254(C)` frozen first-match; `selected = first Stage0 PASS`; no CE-optimal substitution.
- Phase R: per candidate `raw TTBin + acquisition_routing.yaml contract` additive sidecar (`delay/peak/sigma/gate/threshold/frame_anchor/mapping`), `rg "decode_" 0 hits`, `raw_untouched`, no conflicting sidecar reuse, no channel-pair search.
- Pipeline: `Phase R PASS → Stage0 8 frames (4+4) materialization → Stage1 256/64 estimator → Stage2 1024/256+TEST32 seal`; any FAIL → subsequent `UNREACHABLE`, stop-on-failure.
- Estimator (Stage1/2): `C_ab 1024×1024 → P_global → λ 4-fold CV [1e-2,1e4] 50-grid+Brent → P_λ* → H_cal + CE1/CE2/CE_full chain |CE_full-CE1-CE2|<1e-9 → m=ceil(1.3*1024*CE/5)` no cap.
- Rate branches (Stage1/2): `m≥1024 → FULL_DISCLOSURE_LAYER`, `m>frozen but <1024 → RATE_ADAPTATION_REQUIRED`, else `WITHIN_FROZEN_BUDGET`; not candidate FAIL.
- TEST32: 32 frames identity only (`sealed_at`, blocks 8 pairs 8192), `used_test_in_estimation==False` every phase.
- Outputs additive: `if exists → FileExistsError` (no overwrite), no `run_01` in this change.

## Specific reviewer questions

1. Is candidate order `162148→2500K→160254` frozen first-match and `rg "sort.*CE" 0 hits` (no statistical reorder) verified?
2. Is Stage0 strictly materialization-only (no estimator/CE/lambda/m) and first-match `UNREACHABLE_FIRST_MATCH` correct per corrected code and tests 16-19?
3. Is Stage1 the sole estimator for `CE/lambda/m/rate` per test 20 and design §5?
4. Is Phase R true histogram peak (centered bins, median refine, product sign check) not forced `peak==delay`, additive, fail-closed?
5. Is cross-stage zero overlap (`CAL∪VAL∪TEST` disjoint, disjoint from V13..V65 forbidden) and TEST non-participation verified?
6. Is `m_req` uncapped (`rg "min(16" 0 hits`) and additive no-overwrite enforced?
7. Does old `3a6c4fa` INVALID note correctly block retroactive signing of `STAGE0_NO_CANDIDATE`?

## Claim boundary

No execution authorized by this plan. `DECODER_FREE` — no `decode_*` calls, no `run_01`, no FER/threshold/SKR/security claims. Even after future `EXECUTE_AUTH`, results are bounded development evidence on TTBin materialization.

## Verification hints

```
git fetch && git rev-parse HEAD && git rev-parse origin/formal-ir-mainline  # must match
git cat-file -e 70f9ed8ece53704374d37810a163a519e57be6e9 && echo ok
rg "70f9ed8" scripts/v65ar2_pipeline.py  # 2 hits (ACCEPTED_PLAN_SHA + comment)
rg "efd34ef" scripts/ comparison_bench/tests/ docs/  # 0 hits (no stale V55 constant)
python -m py_compile scripts/v65ar2_pipeline.py comparison_bench/tests/test_v65ar2_pipeline.py
python -m pytest comparison_bench/tests/test_v65ar2_pipeline.py -v -p no:cacheprovider --basetemp workspace/v65ar2_test  # 20 passed 15+5
Test-Path docs/research_cycles/V65AR2/PRE_EXECUTE_CHECKLIST.md  # exists
Test-Path comparison_bench/outputs_comparison/formal_ir_methods/v65ar2_pipeline/run_01  # expect False
```
