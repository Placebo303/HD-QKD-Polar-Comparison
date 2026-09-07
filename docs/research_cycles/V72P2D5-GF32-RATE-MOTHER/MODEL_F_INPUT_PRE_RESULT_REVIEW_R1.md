# V72P2D5 Model-F Input Pre-Result Review R1

Reviewer: independent_pre_result_reviewer / reviewer-go
Repository: HD-QKD_Polar_Comparison
Branch: formal-ir-v72p1-addendum-clean
Cycle: V72P2D5-GF32-RATE-MOTHER
Change: formal-ir-v72p2d5-model-f-input-preparation
Date: 2026-09-07
Role: read-only artifact review
Authorization in this task: false. Execution performed: false.
No raw parquet row read authorized. No decoder authorized.
No hash copy normalize regenerate overwrite performed.

## 1. Task scope and read-only authority

- Objective: inspect and recompute actual Model-F artifact internal schema numerical lifecycle disclosure no-side-effect properties.
- Allowed: Get-Content rg git status diff check pathlib stat json.load numpy.load allow_pickle False NumPy readonly pyarrow metadata only loader py_compile specified pytest.
- Forbidden observed: no pandas.read_parquet real, no prepare verify CLI replay, no decoder P0 G1 G2, no Release, no write normalize, no commit push, no delete, no hash checksum copy, no solidification.
- Output discipline: exactly one additive review file. No RESULT_SUMMARY. No OPERATOR_RETURN. No run_01. No promotion. No status change. No P0 authorization.
- Lifecycle input: impl accepted, Pre-EXECUTE R2 PASS, user authorized ONE prepare plus ONE verify, operator reports both success, formal root exists, P0 G1 G2 stated unauthorized unexecuted. This review checks actuals independently.
## 2. Pre-review snapshot (no hash, no copy)

Formal root: workspace/v72p2d5_model_f_input/20260907_r1
Filecount: 2. Both regular files. No extra. No directory.

| filename | size_bytes | mtime_ns | kind |
| --- | --- | --- | --- |
| model_f_input.npz | 208467 | 1788718027043698800 | file |
| model_f_input_summary.json | 752 | 1788718027043698800 | file |

G0 preservation pre:

| root | filename | size_bytes | mtime_ns |
| --- | --- | --- | --- |
| workspace/v72p2d5_g0/20260905_r2 | execution_summary.json | 385 | 1788626074451921900 |
| workspace/v72p2d5_g0/20260905_r2 | report.md | 712 | 1788626074450889700 |
| workspace/v72p2d5_g0/20260905_r2 | results.json | 2512 | 1788626074450889700 |
| workspace/v72p2d5_g0/20260905_r2 | table.csv | 306 | 1788626074450889700 |
| workspace/v72p2d5_g0_recovery/20260906_r1 | execution_summary.json | 404 | 1788634063474539400 |
| workspace/v72p2d5_g0_recovery/20260906_r1 | report.md | 722 | 1788634063474031500 |
| workspace/v72p2d5_g0_recovery/20260906_r1 | results.json | 2531 | 1788634063472847300 |
| workspace/v72p2d5_g0_recovery/20260906_r1 | table.csv | 306 | 1788634063473496200 |

Method: pathlib stat only. No hash. No copy. No row read.
## 3. PR01 lifecycle

- Pre-EXECUTE R2 durable: MODEL_F_INPUT_PRE_EXECUTE_REVIEW_R2.md exists, verdict PRE_EXECUTE_REVIEW_PASS, PX01-PX20 all PASS on actuals after PX11 fix. Prior R1 FAIL on PX11 preserved. Packet frozen.
- Impl accepted: IMPLEMENTATION_ACCEPTANCE_R2.md verdict IMPLEMENTATION_ACCEPTED, scope T0_T1_ONLY, decoder 0 real, CAL 0, VAL 0, outputs 0, all authorized false.
- Cycle state actual: cycle_id V72P2D5-GF32-RATE-MOTHER, state IMPLEMENTATION_ACCEPTED_R2, plan_revision R2_DV3, plan_accepted true, implementation_accepted true, structure authorized false, g0 authorized false, g0 recovery authorized false with attempts 1 completed 1 result G0_RECOVERY_PASS accepted true, p0_cost false, g1 false, g2 false, synthetic false, real false, formal false, scientific_promotion false, decoder_executed true for historical structure G0 context only, cal_rows_read 0, val_rows_read 0, next_gate P0_PACKET_REVIEW.
- Operator 1 plus 1: stated as operator reported success for ONE prepare plus ONE verify after explicit auth. No durable OPERATOR_RETURN for Model-F found in cycle folder. Timestamps RSS counts for prepare verify are operator reported, not durable, and are labeled as such here. No second Model-F root found. Only one formal Model-F root exists. No retry evidence in Model-F root.
- Verdict PR01: PASS for Model-F prepare verify lifecycle. Downstream G1 anomaly is scored under PR16, not here.

## 4. PR02 root exact and PR03 NPZ keys

- PR02 PASS: formal root contains exactly 2 regular files, no extra, no directory, names exactly model_f_input.npz and model_f_input_summary.json. Verified via pathlib iterdir file check.
- PR03 PASS: numpy.load with allow_pickle False succeeds. Keys exactly counts_ab and p_b. No pickle. No object dtype. No rewrite performed. Loader and direct numpy.load agree on keys.
## 5. PR04 counts statistics

Recomputed via NumPy readonly, allow_pickle False, no copy of artifact:

- shape: (1024, 1024). Required (1024, 1024). PASS.
- dtype: int64. Required int64. PASS.
- sum: 262144. Required 262144. PASS.
- min: 0. Required min at least 0. PASS.
- max: 148. Recorded. Finite.
- nonzero: 139766. Zero: 908810. Neg: 0. Required neg 0. PASS.
- finite: true. Nonneg true.
- Orientation: shape alone does not prove Alice versus Bob. Orientation is proven via schema plus impl plus OpenSpec plus asymmetric tests, not via shape. See PR05.
- Verdict PR04: PASS.

## 6. PR05 axis orientation

- Impl: build_model_f_input reuses build_canonical_counts with axis Alice Bob, dims 1024 1024, bob_counts equals counts.sum axis0.
- Summary axis: ["Alice", "Bob"]. Consumer constant MODEL_F_INPUT_FORMAL_ROOT equals workspace/v72p2d5_model_f_input/20260907_r1. Consumer prepare_model_f_prior reuses build_f_model with axis0 Alice normalization, every P_F column sums to 1.
- Tests: M01 proves c_ab transpose equals c_ba, c_ab not equal c_ba, axis1 marginal write raises ValueError. M20 proves injected tables reach prepare_model_f_prior with shape 1024 1024. Asymmetric behavior confirmed. B comma A input would fail marginal check.
- Verdict PR05: PASS. B comma A would FAIL as required.
## 7. PR06 p_b statistics and PR07 marginal recomputation

- PR06 PASS:
  - shape: (1024,). Required (1024,). PASS.
  - dtype: float64. Required float64. PASS.
  - sum: 1.0. Required sum near 1. PASS.
  - min: 0.00075531005859375. Max: 0.001239776611328125. Finite true. Nonneg true.
- PR07 PASS:
  - Expected equals counts.sum axis0 divided by 262144. Recomputed live.
  - maxAbs: 0.0. L1: 0.0. allclose with atol 1e-12: true. Required maxAbs 0.0 unless float justifies within tolerance plus allclose true. Here exact 0.0, strongest result.
  - Wrong axis diagnostic axis1: maxAbs 0.000209808349609375. L1 0.06015777587890625. allclose wrong: false.
  - Distinguishable: true. Correct axis and wrong axis are separable. If identical the review would not fail on this alone and would rely on impl plus tests, but here they are distinguishable, stated honestly.
  - Verdict PR07: PASS.
## 8. PR08 summary JSON schema

Read via UTF-8 json.load, no rewrite:

- schema: v72p2d5_model_f_input_v1. Required v1. PASS.
- cycle: V72P2D5-GF32-RATE-MOTHER. PASS.
- session: 20260123_1M_600k_0dB. PASS.
- source: 1M. PASS.
- cal_start: 702. cal_end: 1725. n_frames: 1024. pairs_per_frame: 256. n_symbols: 262144. All PASS.
- axis: ["Alice", "Bob"]. dims: [1024, 1024]. PASS.
- mapping: symbol=low+32*high;high=U1;low=U2. PASS.
- field q: 32. poly: 37. PASS.
- lambda_star: 137.3823795883264. Required 137.3823795883264. PASS.
- selection: D4R2 nested-CV refit. PASS.
- cal_only: true. val_rows_read: 0. decoder_calls: 0. p0_calls: 0. formal: false. All PASS.
- status: MODEL_F_INPUT_CANDIDATE. Required CANDIDATE, loader also accepts ACCEPTED. Actual CANDIDATE, no status change performed. PASS.
- artifact_files: exactly ["model_f_input.npz", "model_f_input_summary.json"]. PASS.
- files exactly 2. No absolute paths. No hashes. No checksums. PASS.
- Verdict PR08: PASS.

## 9. PR09 mapping field and PR10 arithmetic

- PR09 PASS: mapping symbol equals low plus 32 times high, high equals U1, low equals U2. Field q32 poly37 matches D5. No transpose. No reversal. Consistent across impl summary OpenSpec D5 consumer.
- PR10 PASS: 1024 times 256 equals 262144. counts sum equals n_symbols. Denominator equals sum. Dims equal shape. n equals sum. File list equals directory listing. All equalities hold: 1024 frames, 256 per frame, 262144 total, shape 1024 1024, sum 262144.
## 10. PR11 registry plus PR12 loader plus PR13 no rerun

- PR11 PASS via metadata only, no raw reread, not authorized to read rows:
  - schema: v72p2d3_real_registry_v1. PASS.
  - session: 20260123_1M_600k_0dB. source 1M. used_2m false. PASS.
  - cal_frame_ids len 1024 exactly list range 702 to 1726 sorted nodup. PASS.
  - val_frame_ids [1726, 1727, 1728, 1729]. Zero intersect CAL. PASS.
  - columns [frame_id, pair_idx, alice_symbol, bob_symbol]. PASS.
  - parquet_path repo-root relative comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet. PASS.
  - pyarrow metadata only: rows 545280, row_groups 1, cols 4, num_columns 4. No pandas.read_parquet executed in review. No CAL VAL row load. Stated as not authorized and not performed.
- PR12 PASS: existing loader load_model_f_input run on formal root succeeds, returns same values shape 1024 1024 int64 sum 262144 and 1024 float64 sum 1.0 status CANDIDATE. No create. No alter. CANDIDATE accepted as required.
- PR13 PASS: CLI verify NOT rerun. Auth consumed, so verify replay is forbidden. Inspected impl read-only. Relied on operator verify plus loader only. No prepare verify CLI invocation in this review. Confirmed via command history: only loader, py_compile, specified pytest, stat, json.load, numpy.load, pyarrow metadata.
## 11. PR14 post-review immutability plus PR15 G0 preservation

- PR14 PASS: post-review names sizes mtime unchanged for Model-F root.
  - model_f_input.npz 208467 mtime 1788718027043698800 unchanged true.
  - model_f_input_summary.json 752 mtime 1788718027043698800 unchanged true.
  - filecount still 2. No extra. No rewrite. No normalize.
- PR15 PASS: G0 unchanged, no hash, no copy.
  - workspace/v72p2d5_g0/20260905_r2 4 files sizes mtime unchanged true.
  - workspace/v72p2d5_g0_recovery/20260906_r1 4 files sizes mtime unchanged true.
  - Values match pre snapshot exactly. See Section 2 for full table.
## 12. PR16 absence plus PR17 decoder counts

- PR16 FAIL BLOCKING:
  - workspace/v72p2d5_p0_cost/20260906_r1 exists False. Expected absent. PASS for P0.
  - workspace/v72p2d5_g1/20260906_r1 exists True. Expected absent. FAIL for G1.
  - workspace/v72p2d5_g2/20260906_r1 exists False. Expected absent. PASS for G2.
  - G1 formal root contains 4 files: execution_summary.json 267 mtime 1788719732911457700, report.md 146 mtime 1788719732911457700, results.json 2593 mtime 1788719732909954400, table.csv 126 mtime 1788719732909954400.
  - G1 JSON reports phase g1, passed true, decoder_calls 440, formal_root workspace/v72p2d5_g1/20260906_r1, 100 attempted per f, app_exact 0, app_failure 1.0. Cycle state still shows g1_execution_authorized false, next_gate P0_PACKET_REVIEW. No P0 packet review. No Model-F acceptance. No explicit G1 auth on record.
  - This review created no G1 output. G1 mtime 2026-09-06 18:35:32 is after Model-F 18:07:07 and before this review. It is unauthorized downstream execution beyond the authorized ONE prepare plus ONE verify.
  - Evidence: pathlib exists True for G1 formal root plus 4 file stats plus JSON decoder_calls 440 plus cycle_state g1 false.
- PR17 PASS for Model-F scope, noted G1 anomaly:
  - Review decoder 0. P0 0. G1 0. G2 0 executed in this review. No decoder artifact created here.
  - Model-F JSON zeros are prep metadata, not performance: val_rows_read 0, decoder_calls 0, p0_calls 0, formal false. Confirmed not performance claims. No syndrome. No FER. No SKR in Model-F files.
  - G1 artifact with 440 decoder calls exists outside review scope and is the PR16 blocker. It is not counted as review decoder execution.
## 13. PR18 disclosure plus PR19 undetected isolation plus PR20 claim boundary

- PR18 PASS for Model-F disclosure accounting:
  - Disclosure table, all NOT_APPLICABLE or NOT_COMPUTED, confirmed not zero-valued:
  - syndrome: NOT_APPLICABLE. No syndrome stored in NPZ or JSON.
  - verification: NOT_COMPUTED. No verification hash stored.
  - other disclosure: NOT_APPLICABLE. No P_F P1 P2 beliefs stored.
  - total leakage: NOT_COMPUTED. No leakage number in Model-F files.
  - blocks: NOT_APPLICABLE. No block results in Model-F files.
  - undetected: NOT_APPLICABLE. No decoding, so no undetected class.
  - per-source breakdown: NOT_APPLICABLE. Single CAL refit input, no per-source split here.
  - FER: NOT_COMPUTED. No FER stored.
  - net secure: NOT_COMPUTED. No net key stored.
  - Confirm not zero-valued: JSON contains no 0.0 leakage, no 0 FER, no 0 syndrome count presented as measurement. Zeros present are only val_rows_read 0 decoder_calls 0 p0_calls 0 as prep metadata.
- PR19 PASS: undetected isolation holds. No decoding occurred in Model-F prepare scope, so no success, no FER, no failed, no undetected. No merge. No performance conclusion drawn from Model-F input alone.
- PR20 PASS for boundary observance in this review:
  - Strongest allowed: frozen Model-F CAL input internally consistent canonical Alice Bob derived marginal.
  - Forbidden and not claimed: NB works, P0 pass, success, FER, leakage, net, SKR, qualification, optimal. None claimed here. G1 artifact performance numbers are not endorsed here and are unauthorized.
## 14. PR21 compile and test evidence

- py_compile 4 files: exit 0. Files: comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py, scripts/v72p2d5_prepare_model_f_input.py, comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py, scripts/v72p2d5_gf32_rate_mother.py. PASS.
- pytest 3 files authoritative: comparison_bench/tests/test_v72p2d5_model_f_input.py plus test_v72p2d5_gf32_rate_mother.py plus test_v72p2d4_cal_gf32_model_rate_audit.py with --basetemp workspace/v72p2d5_model_f_preresult_r1_20260907c03 -q --tb=line.
- Literal: 5 failed, 186 passed, 1 warning in 333.06s. Warning literal: PytestConfigWarning Unknown config option cache_dir.
- Failed list literal:
  - test_M24_formal_roots_absent in test_v72p2d5_model_f_input.py line 409 assert not True for MODEL_F formal root.
  - test_P12_formal_roots_absent in test_v72p2d5_model_f_input.py line 624 same.
  - test_P0G1G2_i_g0_recovery_structure_regression in test_v72p2d5_gf32_rate_mother.py line 3066 Failed DID NOT RAISE ValueError.
  - test_M19_d5_unauthorized_artifact_zero line 3118 assert not True for MODEL_F formal root.
  - test_M21_d5_missing_artifact_blocked_no_toy line 3147 assert not True for MODEL_F formal root.
- Focused Model-F file only: 2 failed, 29 passed in 2.14s with basetemp c02a. Same 2 absence tests. Core M01-M18 plus P01-P11 plus M20 all pass. M20 authorized fake load reaches runner PASS in 1.07s. M19 M21 singles each FAIL only on absence assert, as expected post-prepare.
- No prepare verify CLI replay. No copy. Basetemp not equal formal root. Production root still exactly 2 files. Test roots are additive workspace/v72p2d5_model_f_preresult_r1_20260907c01 plus c02a plus c02c plus c02e plus c03. Dirt preserved.
- Interpretation: 186 core pass proves builder writer reader marginal summary resolver consumer fake paths. 5 failures are pre-execution absence gates that must flip after successful prepare, plus one control-flow flip where BLOCKED is no longer raised because the artifact now exists. They do not indicate Model-F internal inconsistency. Scored as PR21 procedure PASS with literal failures documented, but overall review still FAIL due to PR16 G1 blocker. Checklist Tests pass is therefore unchecked.
## 15. PR22 additive discipline plus PR23 authority plus checklist

- PR22 PASS in part, with G1 exception noted:
  - Only additive review file created by this review: MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md. No code test OpenSpec cycle change. Release untouched. No commit. No push. Dirt preserved. Basetemp not equal formal.
  - No RESULT_SUMMARY. No OPERATOR_RETURN. No run_01. No promotion created here.
  - Exception: unauthorized G1 formal root already existed before this review and is not created here. It violates additive discipline for the cycle and is the PR16 blocker.
- PR23 PASS for review authority:
  - No status change. No result accept. No P0 authorization. Status remains MODEL_F_INPUT_CANDIDATE. formal false.
  - This review grants only readiness signal if blockers clear. With PR16 FAIL, signal is not READY_FOR_MAIN_RESULT_ACCEPTANCE.
  - Only READY_FOR_MAIN_RESULT_ACCEPTANCE would apply after G1 disposition plus re-review. Not granted here.
- Checklist:
  - [x] Matches OpenSpec spec for Model-F artifact S-MF S-MB S-MW S-ML S-MR S-MC S-PATH S-SP, except downstream G1 violates S-SP formal roots absent.
  - [ ] Tests pass. Literal 5 failed 186 passed. Core 186 pass, 5 are expected post-prepare flips. Unchecked due to literal failures.
  - [ ] No scope creep. Model-F scope clean, but G1 unauthorized execution is scope creep. Unchecked.
  - [ ] docs decision-log.md or docs troubleshooting.md needs update. No update in this task, forbidden to edit. Separate change could log G1 anomaly and absence-test staleness.
## 16. Conclusion and verdict

- Model-F artifact internal consistency: PASS. Root exact 2 files. Keys exact. Counts shape dtype sum min max nonzero zero neg finite PASS. Axis Alice Bob PASS. p_b shape dtype sum finite nonneg PASS. Marginal maxAbs 0.0 L1 0.0 allclose true PASS. Wrong axis distinguishable PASS. JSON schema status session CAL frames lambda val0 decoder0 p00 formal false PASS. Mapping field arithmetic PASS. Registry loader no-rerun PASS. Immutability G0 PASS. Disclosure undetected claim PASS. Compile PASS. Core tests 186 PASS.
- Lifecycle blocker: PR16 FAIL. G1 formal root workspace/v72p2d5_g1/20260906_r1 exists True with 4 files and decoder_calls 440 while g1_execution_authorized false and next_gate P0_PACKET_REVIEW. P0 False. G2 False. G1 True. Roots not all absent.
- Additional literal: PR21 shows 5 failed 186 passed. Failures are absence-gate flips after prepare, documented, not artifact corruption. Review decoder 0. P0 0. Raw rows 0. Artifact modified false. Cleanup false. Commit false. Push false. Prod Release false.
- Strongest claim allowed here: frozen Model-F CAL input internally consistent canonical Alice Bob derived marginal. No NB works. No P0 pass. No success FER leakage net SKR qualification optimal claim.
- Verdict: PRE_RESULT_REVIEW_FAIL. Candidate not READY_FOR_MAIN_RESULT_ACCEPTANCE until single decision is executed and re-review passes.
- Exact blocker: unauthorized G1 formal output present at workspace/v72p2d5_g1/20260906_r1 with decoder_calls 440 despite explicit unauthorized state.
- Failing check: PR16. Supporting literal: PR21 5 failed 186 passed.
- Evidence: G1 exists True plus 4 file sizes mtime plus JSON decoder_calls 440 plus cycle_state g1_execution_authorized false. Model-F unchanged true. G0 unchanged true. Raw rows 0. Review decoder 0. P00 for review. Cleanup false. Commit false. Push false.
- Single decision required from main thread: disposition the unauthorized G1 root via explicit authorized path or quarantine removal with record, plus update or scope the 5 stale absence tests for post-prepare state, then order independent re-review. Do not solidify run_01. Do not publish RESULT_SUMMARY. Do not authorize P0 until re-review passes.
