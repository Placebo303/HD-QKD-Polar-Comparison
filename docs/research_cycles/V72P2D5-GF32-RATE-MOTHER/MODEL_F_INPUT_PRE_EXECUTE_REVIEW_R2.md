# V72P2D5 Model-F Input Pre-EXECUTE Review R2 (independent, read-only, PX11 rework)

- Repository: HD-QKD_Polar_Comparison (Comparison only; never Release)
- Branch: formal-ir-v72p1-addendum-clean (verified git rev-parse --abbrev-ref HEAD)
- Cycle: V72P2D5-GF32-RATE-MOTHER
- Change: formal-ir-v72p2d5-model-f-input-preparation
- Reviewer: independent_pre_execute_reviewer / reviewer-go
- Date: 2026-09-07 (R2, after PX11 path rework)
- Role: review-only, must not execute preparation. No auth granted here.
- Authorization in this task: false. Execution performed: false.
- Prior history preserved: MODEL_F_INPUT_PRE_EXECUTE_PACKET.md + MODEL_F_INPUT_PRE_EXECUTE_REVIEW.md (prior PRE_EXECUTE_REVIEW_FAIL on PX11) untouched; this R2 is additive only.

## 1. Lifecycle before (frozen, read from cycle_state.yaml)

- cycle_id: V72P2D5-GF32-RATE-MOTHER, state: IMPLEMENTATION_ACCEPTED_R2, plan_revision: R2_DV3, plan_accepted: true, implementation_accepted: true
- Model-F candidate main-accepted path; PX11 rework main-accepted (code + P01-P12 tests present in tree)
- structure_execution_authorized: false, g0_execution_authorized: false, g0_recovery_execution_authorized: false (recovery completed PASS, accepted true, evidence retained)
- p0_cost_execution_authorized: false, g1_execution_authorized: false, g2_execution_authorized: false, synthetic_execution_authorized: false, real_execution_authorized: false, formal_execution_authorized: false, scientific_promotion: false
- decoder_executed: true (historical structure/G0 context only; Model-F prepare executed false), cal_rows_read: 0, val_rows_read: 0
- Real CAL prep NOT AUTHORIZED / NOT EXECUTED. P0/G1/G2 NOT AUTHORIZED / NOT EXECUTED.
- next_gate: P0_PACKET_REVIEW. This R2 covers Model-F input prepare only; P0 still requires separate prepare review + explicit auth.

## 2. Files inspected (10 groups, actuals only)

1. AGENTS.md (359 lines; boundary section 0, gates section 3/10.3, no SHA-equality demand by default)
2. AGENT_PROJECT_MEMORY.md V72P2D5-only slice (R1 exception, R2_DV3 freeze, G0/structure context consulted; no edit in this task)
3. docs/research-cycle-sop.md (section 10 Pre-EXECUTE/Pre-RESULT gates; commit IDs provenance only)
4. openspec/changes/formal-ir-v72p2d5-model-f-input-preparation/: proposal.md (48 lines), design.md (98 lines incl section 8 PX11), tasks.md (36 lines incl PX11-R1), specs/spec.md (50 lines incl S-PATH-01..05)
5. Impl: comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py (269 lines) + scripts/v72p2d5_prepare_model_f_input.py (164 lines)
6. D5 consumer: comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py (checked prepare_model_f_prior, _load_model_f_input_or_blocked, run_p0_cost_synthetic/run_g1_synthetic/run_g2_synthetic, G0 fixture/tree preserved) + scripts/v72p2d5_gf32_rate_mother.py (103 lines)
7. Tests: comparison_bench/tests/test_v72p2d5_model_f_input.py (627 lines; M01-M18 + P01-P12) + comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py (3156 lines head-checked) + comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py (531 lines head-checked)
8. Registry: workspace/v72p2d3_real_registry_20260904.json (1045 lines; JSON load only)
9. History: MODEL_F_INPUT_PRE_EXECUTE_PACKET.md (104 lines, frozen) + MODEL_F_INPUT_PRE_EXECUTE_REVIEW.md (70 lines, prior FAIL on PX11) -- read only, not modified
10. docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml (41 lines; values quoted in section 1)

Allowed read-only cmds used: git status/diff/diff --check, python grep/inspect probes, Get-Content/Test-Path, import/AST probes, pyarrow metadata only, py_compile, specified pytest, --help + unauth probes. Forbidden (not done): authorized prepare, pandas.read_parquet row load, CAL/VAL row load, artifact create, decoder call, P0/G1/G2 run, Release ops, commit/push, cleanup.

## 3. PX01-PX20 (PASS/FAIL + evidence)

- PX01 repo/ownership + frozen baseline untouched: PASS. HEAD=formal-ir-v72p1-addendum-clean, workdir D:/Code/HD-QKD_Polar_Comparison, no Release modify/execute. git diff --name-only -- src/ experiments/ tools/ empty. git diff --check clean (LF warnings only, benign).
- PX02 session CAL/VAL, no TEST concat: PASS. Registry schema=v72p2d3_real_registry_v1, session_id=20260123_1M_600k_0dB, source_label=1M, used_2m=false, columns=[frame_id,pair_idx,alice_symbol,bob_symbol], cal_frame_ids len 1024 exactly list(range(702,1726)) sorted nodup, val_frame_ids=[1726,1727,1728,1729] zero intersect. Loader scripts/v72p2d5_prepare_model_f_input.py:101-110 enforces cal==range(702,1726) + val==[1726..1729] (reject-check only, never fit). Builder takes only CAL arrays; no TEST path.
- PX03 lambda frozen refit: PASS. LAMBDA_STAR=137.3823795883264 in v72p2d5_model_f_input.py:44, returned :124, checked :212, summary lambda_star same, selection=D4R2 nested-CV refit. Matches D4R2 + R2_DV3 plan. No tuning path.
- PX04 counts (1024,1024) Alice,Bob sum 262144 no transpose: PASS. build_model_f_input:100 reuses build_canonical_counts(alice,bob,q=1024), asserts shape==(1024,1024), nonneg, sum==262144, axis=[Alice,Bob], dims=[1024,1024]. Test M01 proves c_ab.T==c_ba, c_ab!=c_ba, axis1-marginal write raises.
- PX05 p_b marginal/262144 (1024,) sum1 derived: PASS. bob_counts=counts.sum(axis=0), p_b=bob/262144.0 (:108-115), recheck ==marginal/262144 atol=1e-12 (:147-149), sum==1 tol 1e-8, float64 (1024,). Builder signature (alice_symbols,bob_symbols,frame_ids) has no p_b param; M06 + M14 enforce derived-not-handfilled.
- PX06 output root exactly 2 files allow_pickle False no-overwrite validate-before-mkdir no checksum: PASS. MODEL_F_FORMAL_ROOT=workspace/v72p2d5_model_f_input/20260907_r1, NPZ=model_f_input.npz, JSON=model_f_input_summary.json. write:238-240 validates in-mem before mkdir, exists->FileExistsError before write, mkdir(parents=True,exist_ok=False), savez_compressed keys exactly counts_ab/p_b, load requires allow_pickle=False both sides (:260 + tests M10). Post-write names==NPZ,JSON else RuntimeError. No sha/md5/checksum/atomic/backup/lock strings (verified).
- PX07 summary v1 no decoder/FER/qual claims: PASS. _build_summary:153-177 + _check_summary:180-229 enforce schema=v72p2d5_model_f_input_v1, cycle/session/source/CAL 702..1725/1024/256/262144, axis/dims/mapping symbol=low+32*high;high=U1;low=U2, field q32 poly37, lambda, cal_only=true, val_rows_read=0, decoder_calls=0, p0_calls=0, formal=false, status=CANDIDATE (loader also accepts ACCEPTED), artifact_files exactly 2 names. M11 + M15 cover. No FER/SKR/QUALIFIED text in artifact path.
- PX08 prepare/consume split no auto-P0 no G0-toy: PASS. Prepare run_prepare:123-132 = loader->build_model_f_input->write only. D5 _load_model_f_input_or_blocked = injected tables or fixed-root load_model_f_input else MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS; then sole prepare_model_f_prior (reuses build_f_model) then phase runner. run_p0/g1/g2_synthetic segments contain no G0/read_parquet/CAL; model_f_input.py G0 hit is only docstring ban line :5. No --model-input-root flag (frozen CLI forbids new flags; fixed root documented in design section 5).
- PX09 unauth exit3 before registry/path/parquet/mkdir/model/decoder/P0, flags false: PASS. main:144-148 returns 3 before any work when --execution-authorized absent. Probed: prepare unauth exit 3, verify unauth exit 3, root still absent, zero model_f_input.npz created. M16/P10 monkeypatch loader/mkdir/resolver zero calls. D5 _require_authorized raises NotAuthorizedError for p0-cost/g1/g2 when false (probed direct calls). cycle_state all authorized=false (section 1).
- PX10 no decoder bind/call decoder0 p00 no P0 roots: PASS. model_f_input.py imports only json/pathlib/numpy + build_canonical_counts; decode hits are docstring/counter lines only (:5,:81,:172,:220,:252); p0 hits are p0_calls counter lines only. Prepare returns decoder_calls=0,p0_calls=0,val_rows_read=0; verify docstring no decoder/parquet. No bind_historical_decoder/_load_g0_decoder in Model-F files. P0/G1/G2 roots absent (section 7). No decoder executed in this review.
- PX11 corrected resolution: PASS (rework verified). ROOT=_HERE.parents[1] from __file__ (:21-22); _resolve_parquet_path:75-86 validates non-empty string (ValueError), joins ROOT when not absolute else direct, resolve(), requires is_file() else FileNotFoundError, returns absolute. No cwd/getcwd/chdir, no (Path(registry_path).parent join (grep absent), no search/fallback, no D-hardcode, registry_path absent from resolver source, read_parquet/pandas absent from resolver source. _load_cal_arrays:111 calls resolver before any pd.read_parquet/mkdir/write. Probes: correct D:/Code/HD-QKD_Polar_Comparison/comparison_bench/.../pairs.parquet exists True is_file True; wrong .../workspace/comparison_bench/.../pairs.parquet exists False; relative + absolute --registry resolve to same absolute (same=True); empty/whitespace/None/non-string -> ValueError; nonexistent -> FileNotFoundError with zero read/mkdir (P07 pattern). Tests P01-P12 all pass (part of 191).
- PX12 parquet metadata only: PASS. pyarrow only: rows=545280, row_groups=1, cols=[frame_id,pair_idx,alice_symbol,bob_symbol], num_columns=4. No pandas.read_parquet executed in review; no CAL/VAL row load.
- PX13 exact future prepare command: PASS. Frozen single prepare: python scripts/v72p2d5_prepare_model_f_input.py --phase prepare --registry workspace/v72p2d3_real_registry_20260904.json --out-dir workspace/v72p2d5_model_f_input/20260907_r1 --execution-authorized. Verify follow-up (read-only): same with --phase verify. Parser build_parser:58-72 requires --phase(prepare,verify) + --registry + --out-dir + --execution-authorized choke; --help exit 0 confirms; no lambda/seed/f/degree/family overrides.
- PX14 budget 1 invocation no retry CAL262144 VAL0 decoder0 P00 wall300s RSS2GiB fail stops: PASS. Packet freezes 1 prepare (verify read-only follow-up, not second prepare), CAL=262144 VAL-as-model=0 decoder=0 P0/G1/G2=0, wall<=300s RSS<2GiB, no retry/resume/merge framework in code, failures -> PREP_FAILED/INPUT_BLOCKED/RESOURCE_BLOCKED + exit 3 / FileExistsError/FileNotFoundError/ValueError stops. Builder is 262k-row in-mem counts, consistent with budget.
- PX15 roots absent + G0 recovery present unchanged: PASS. Test-Path False: workspace/v72p2d5_model_f_input/20260907_r1, workspace/v72p2d5_p0_cost/20260906_r1, workspace/v72p2d5_g1/20260906_r1, workspace/v72p2d5_g2/20260906_r1. G0 workspace/v72p2d5_g0/20260905_r2 True, 4 files: execution_summary.json 385, report.md 712, results.json 2512, table.csv 306. G0-recovery workspace/v72p2d5_g0_recovery/20260906_r1 True, 4 files: execution_summary.json 404, report.md 722, results.json 2531, table.csv 306. Names/sizes/mtime_ns recorded in section 8; no hash/copy performed.
- PX16 compile/test with fresh basetemp: PASS. See section 4 literal.
- PX17 --help + unauth documented codes zero outputs, no authorized probe: PASS. --help exit 0 (usage + 4 flags). Unauth prepare exit 3 (phase prepare is not authorized; refusing before any work); unauth verify exit 3 same; root still False; no model_f_input.npz under workspace target. No --execution-authorized probe executed.
- PX18 scoped dirt vs pre-existing: PASS (dirty alone not blocker). Tracked M 11 files are pre-existing/out-of-scope deltas (AGENT_PROJECT_MEMORY, decision-log, cycle_state, mother-plan 4, project.md, D5 impl/test/CLI). Scoped Model-F path-rework set = 6 files: comparison_bench/src/.../v72p2d5_model_f_input.py (new), scripts/v72p2d5_prepare_model_f_input.py (new), comparison_bench/tests/test_v72p2d5_model_f_input.py (new, incl P01-P12), comparison_bench/src/.../v72p2d5_gf32_rate_mother.py (M, consumer), scripts/v72p2d5_gf32_rate_mother.py (M), comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py (M) + OpenSpec formal-ir-v72p2d5-model-f-input-preparation/ (new). No HEAD==origin/SHA-equality demand, no revert, unrelated outputs preserved.
- PX19 independence: PASS. Inspected actual file bytes/AST/imports, ran own py_compile/pytest/help/unauth/metadata/path probes; discrepancies: none blocking. LF/CRLF warnings benign. Prior R1 181 passed vs R2 191 passed is additive P01-P12 growth (+10 incl M/P), 0 failed, same Unknown cache_dir warning -- expected, not a mismatch.
- PX20 authority: PASS. No real prep/auth/P0/decoder executed; verdict is only READY_FOR_USER_EXECUTION_AUTHORIZATION recommendation. Auth remains explicit user decision.

## 4. Actual compile/test output summary (literal, authoritative for R2)

- python -m py_compile comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py scripts/v72p2d5_prepare_model_f_input.py comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py scripts/v72p2d5_gf32_rate_mother.py -> exit=0
- python -m pytest -p no:cacheprovider comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py --basetemp workspace/v72p2d5_model_f_preexecute_r2_20260907b01 -q -> 191 passed, 1 warning in 18.90s
- Warning literal: PytestConfigWarning: Unknown config option: cache_dir (same as R1 baseline warning class)
- Basetemp workspace/v72p2d5_model_f_preexecute_r2_20260907b01 was absent before run (False), created by pytest as test-only root; production root still absent. Do not copy prior 181 passed claims -- above is the R2-observed result.

## 5. Resolved correct + incorrect paths (probed, no row reads)

- Correct (repo-root from __file__): D:/Code/HD-QKD_Polar_Comparison/comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet -> exists True, is_file True
- Incorrect (registry-parent join): D:/Code/HD-QKD_Polar_Comparison/workspace/comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet -> exists False
- Registry raw: comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet (repo-root relative, inside Comparison tree)
- ROOT-from-file: D:/Code/HD-QKD_Polar_Comparison; (ROOT/raw).is_file True
- Relative --registry vs absolute --registry resolve to same absolute (same=True)
- Empty/whitespace/None/non-string -> ValueError; nonexistent relative -> FileNotFoundError before read_parquet/mkdir/write

## 6. Parquet metadata (pyarrow only, no pandas.read_parquet)

- Path: comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet
- rows=545280, row_groups=1, cols=[frame_id,pair_idx,alice_symbol,bob_symbol], num_columns=4
- Post-filter contract (code, not probed by rows): keep CAL IDs must be 262144 rows, 256/frame; VAL 0 rows as model.

## 7. Formal absence (pre-exec required)

- workspace/v72p2d5_model_f_input/20260907_r1: False
- workspace/v72p2d5_p0_cost/20260906_r1: False
- workspace/v72p2d5_g1/20260906_r1: False
- workspace/v72p2d5_g2/20260906_r1: False

## 8. G0 preservation (no hash/copy, names/sizes/mtime_ns only)

- workspace/v72p2d5_g0/20260905_r2: True -- execution_summary.json 385 mtime 1788626074451921900, report.md 712 mtime 1788626074450889700, results.json 2512 mtime 1788626074450889700, table.csv 306 mtime 1788626074450889700
- workspace/v72p2d5_g0_recovery/20260906_r1: True -- execution_summary.json 404 mtime 1788634063474539400, report.md 722 mtime 1788634063474031500, results.json 2531 mtime 1788634063472847300, table.csv 306 mtime 1788634063473496200
- G0 fixture helpers (build_g0_fixture, build_g0_tree_fixture, tree/exhaustive checks) still present in D5 core; no G0-toy wired into Model-F prepare/consume.

## 9. Exact future command (frozen, NOT executed here)

- Prepare (single authorized invocation, needs explicit user EXECUTE_AUTH after this R2 PASS):
- python scripts/v72p2d5_prepare_model_f_input.py --phase prepare --registry workspace/v72p2d3_real_registry_20260904.json --out-dir workspace/v72p2d5_model_f_input/20260907_r1 --execution-authorized
- Verify (read-only follow-up):
- python scripts/v72p2d5_prepare_model_f_input.py --phase verify --registry workspace/v72p2d3_real_registry_20260904.json --out-dir workspace/v72p2d5_model_f_input/20260907_r1 --execution-authorized
- No extra flags. No second prepare. --registry required even for verify (ignored per help; recorded as-is).

## 10. Budget (frozen)

- Invocation: 1 prepare only (verify is read-only follow-up). No retry/resume/tuning without new Pre-EXECUTE review + re-auth.
- CAL rows 262144, VAL rows as model 0, decoder calls 0, P0 calls 0
- wall<=300s, RSS<2GiB. Runner has no hard killer/watchdog (ponytail-lite; outer caller observes timeout).
- Stop on: CAL drift, retained!=262144, non-256 frame, symbol range, axis/marginal/sum/lambda/session mismatch, root exists, parquet missing/schema mismatch, timeout/RSS exceed, any VAL-as-model or decoder/P0 entry. Failure -> PREP_FAILED/INPUT_BLOCKED/RESOURCE_BLOCKED, retained, no rollback machinery.

## 11. Confirmation (this review executed nothing claim-bearing)

- execution_performed: false, cal_rows_read: 0, val_rows_read: 0, decoder_calls: 0, p0_calls: 0, execution_authorized: false (all authorized=false per section 1)
- commit: false, push: false, formal outputs created: false, registry changed: false, Release touched: false
- Existing reviews/packet unmodified; this R2 file is the sole additive record.
- next: EXPLICIT_USER_EXECUTION_AUTHORIZATION (user must explicitly authorize the section 9 prepare; this review does not grant it; P0/G1/G2 remain unauthorized regardless).

## 12. One verdict

- Verdict: PRE_EXECUTE_REVIEW_PASS / READY_FOR_USER_EXECUTION_AUTHORIZATION
- Scope: Model-F input prepare only (workspace/v72p2d5_model_f_input/20260907_r1). No P0/G1/G2, no decoder performance, no FER/SKR/qualification/promotion claim.
- Blocker: none. PX01-PX20 all PASS on actuals after PX11 fix.

Checklist:
- [x] Matches OpenSpec spec (S-MF/S-MB/S-MW/S-ML/S-MR/S-MC/S-PATH/S-SP all PASS)
- [x] Tests pass (191 passed 1 warning, py_compile exit 0)
- [x] No scope creep (review stayed to Model-F prepare/verify; dirty worktree preserved)
- [ ] docs/decision-log.md or docs/troubleshooting.md needs update? No update in this task (forbidden); if desired, log PX11 resolver fix via separate change.

Review PASS is not exec auth. Execution authorized: false. Execution performed: false. Ready for execute auth: true (pending explicit user authorization).