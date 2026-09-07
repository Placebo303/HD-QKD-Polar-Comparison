# V72P2D5 Model-F Input Pre-RESULT Review R2

Reviewer: independent_pre_result_reviewer / reviewer-go (independent session; did not author Model-F implementation, disposition record, or D5-DISPO-R1 packet)
Repository: HD-QKD_Polar_Comparison
Branch: formal-ir-v72p1-addendum-clean
Cycle: V72P2D5-GF32-RATE-MOTHER
Change: formal-ir-v72p2d5-model-f-input-preparation
Date: 2026-09-07
Role: read-only artifact review
Authorization in this task: false. Execution performed: false.
Prior verdict: MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md returned PRE_RESULT_REVIEW_FAIL on single blocker PR16. R1 is evidence, not authority; every number below was recomputed.

Question decided here: does the documentation-only disposition G1_UNAUTHORIZED_DISPOSITION_R1.md (VOID_RETAINED_IN_PLACE, commits b986ca11 / 7c59d375 / 20204726) clear PR16 for the purpose of accepting the Model-F input candidate, or does PR16 still block?

## 0. What was and was not executed (explicit)

- DID: pathlib stat on six workspace roots (pre- and post-test); numpy.load(allow_pickle=False) readonly recomputation on model_f_input.npz; json.load reads of model_f_input_summary.json and G1 JSON/md/csv; file reads of R1, disposition, incident, isolation evidence, test source, prod source (static only); git show HEAD:cycle_state.yaml; git show --stat / diff-tree for b986ca11, 7c59d375, 20204726; git status -sb; py_compile on 4 files; pytest on the 3 packet-listed test files with fresh additive basetemp workspace/v72p2d5_preresult_r2_20260907_r2; post-test re-stat of all protected roots; created exactly this ONE review file.
- DID NOT: no decoder run; no scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost|g1|g2; no scripts/v72p2d5_prepare_model_f_input.py invocation at all; no pandas.read_parquet (zero parquet row reads); no delete/move/rename/copy/normalize/hash/open-for-write under workspace/; no workspace/v72p2d5_p0_cost or workspace/v72p2d5_g2 creation; no edit to any .py, existing .md, cycle_state.yaml, decision-log, memory, openspec, or prior review; no git commit/push/add/reset/stash/checkout/clean/rebase/revert; no authorization change; no RESULT_SUMMARY / OPERATOR_RETURN / run_01; no fix of anything found.

## 1. Pre/post stat snapshots (stat only, no hash, no copy)

Pre-review (before pytest) and post-review (after pytest) are IDENTICAL. Single table serves both:

Formal Model-F root: workspace/v72p2d5_model_f_input/20260907_r1

| filename | size_bytes | mtime_ns | kind |
| --- | --- | --- | --- |
| model_f_input.npz | 208467 | 1788718027043698800 | file |
| model_f_input_summary.json | 752 | 1788718027043698800 | file |

G1 root: workspace/v72p2d5_g1/20260906_r1 (4 files, retained)

| filename | size_bytes | mtime_ns |
| --- | --- | --- |
| execution_summary.json | 267 | 1788719732911457700 |
| report.md | 146 | 1788719732911457700 |
| results.json | 2593 | 1788719732909954400 |
| table.csv | 126 | 1788719732909954400 |

G0 root: workspace/v72p2d5_g0/20260905_r2

| filename | size_bytes | mtime_ns |
| --- | --- | --- |
| execution_summary.json | 385 | 1788626074451921900 |
| report.md | 712 | 1788626074450889700 |
| results.json | 2512 | 1788626074450889700 |
| table.csv | 306 | 1788626074450889700 |

G0-recovery root: workspace/v72p2d5_g0_recovery/20260906_r1

| filename | size_bytes | mtime_ns |
| --- | --- | --- |
| execution_summary.json | 404 | 1788634063474539400 |
| report.md | 722 | 1788634063474031500 |
| results.json | 2531 | 1788634063472847300 |
| table.csv | 306 | 1788634063473496200 |

Absent (both pre and post): workspace/v72p2d5_p0_cost/20260906_r1 exists False; workspace/v72p2d5_g2/20260906_r1 exists False.

Method: pathlib stat only. Pre/post equality verified field-by-field after the pytest run.

## 2. C01 Model-F root exact + NPZ keys — PASS

- Formal root contains exactly 2 regular files, named model_f_input.npz and model_f_input_summary.json. No extra, no directory. PASS.
- numpy.load(allow_pickle=False) succeeds; keys exactly [counts_ab, p_b]; neither dtype is object. PASS.
- Agreement with R1: R1 PR02/PR03 record the same 2-file root and exact keys. AGREE.

## 3. C02 counts_ab statistics — PASS

Recomputed readonly via NumPy (allow_pickle=False):

- shape: (1024, 1024). Required (1024, 1024). PASS.
- dtype: int64. Required int64. PASS.
- sum: 262144. Required 262144. PASS.
- min: 0. Required >= 0. PASS.
- max: 148. Recorded, finite.
- nonzero: 139766. Zero: 908810. Negatives: 0. Required 0. PASS.
- finite: true. Nonneg: true.
- Agreement with R1: R1 PR04 records shape (1024,1024), int64, sum 262144, min 0, max 148, nonzero 139766, neg 0. AGREE on every value (zero count 908810 derived identically: 1048576-139766).

## 4. C03 p_b statistics + marginal identity + wrong-axis diagnostic — PASS

- shape: (1024,). dtype: float64. sum: 1.0. min: 0.00075531005859375. max: 0.001239776611328125. finite: true. nonneg: true. All PASS.
- Marginal identity p_b == counts_ab.sum(axis=0)/counts_ab.sum(): maxAbs 0.0, L1 0.0, allclose(atol=1e-12) true. PASS (exact, strongest result).
- Wrong-axis diagnostic (axis=1): maxAbs 0.000209808349609375, L1 0.06015777587890625, allclose false. Distinguishable from correct axis: true. PASS.
- Agreement with R1: R1 PR06/PR07 record identical sum/min/max and identical maxAbs/L1 for both axes. AGREE on every value.

## 5. C04 summary JSON schema + internal agreement — PASS

Read via UTF-8 json.load, no rewrite. Fields:

- schema v72p2d5_model_f_input_v1; cycle V72P2D5-GF32-RATE-MOTHER; session 20260123_1M_600k_0dB; source 1M. PASS.
- cal_start 702, cal_end 1725, n_frames 1024, pairs_per_frame 256, n_symbols 262144. Arithmetic: 1725-702+1 = 1024 frames; 1024*256 = 262144 = counts sum = n_symbols. PASS.
- axis ["Alice", "Bob"]; dims [1024, 1024] == counts shape. PASS.
- mapping symbol=low+32*high;high=U1;low=U2; field q 32 poly 37. PASS.
- lambda_star 137.3823795883264. selection D4R2 nested-CV refit. PASS.
- cal_only true; val_rows_read 0; decoder_calls 0; p0_calls 0; formal false; status MODEL_F_INPUT_CANDIDATE. All PASS (zeros are prep metadata, not performance claims).
- artifact_files exactly ["model_f_input.npz", "model_f_input_summary.json"] == directory listing. PASS. No absolute paths, no hashes.
- Agreement with R1: R1 PR08/PR09/PR10 record the same values and equalities. AGREE.

## 6. C05 disposition record existence + consistency + on-disk match — PASS

- G1_UNAUTHORIZED_DISPOSITION_R1.md exists (92 lines). Internally consistent: subject root, 4-file table, status INVALID_UNAUTHORIZED_TEST_TRIGGERED additionally and permanently VOID, D03 citation bar, D04 retention rationale (incident I08 no-delete/move + user rejection of deletion/relocation), D05 root-cause pointer, D06 lifecycle effect (auth stays false, PR16 addressed by RECORD with clearance deferred to independent re-review). PASS.
- Recorded size/mtime_ns vs disk right now: 267/1788719732911457700, 146/1788719732911457700, 2593/1788719732909954400, 126/1788719732909954400 — match the §1 post-stat exactly. PASS.
- G1 JSON content confirms the voided numbers: phase g1, passed true, decoder_calls 440, per-f 100 attempted each with app_exact 0 / app_failure 1.0 / oracle 0. These numbers are quarantined by the disposition, not endorsed here. PASS (observation only).

## 7. C06 G1/G0 roots + P0/G2 absence — PASS (with dispositioned exception recorded)

- G1 root still exactly 4 files, unmodified (sizes/mtimes identical to disposition D01/D07 and to R1 §12). The physical presence that R1 scored as PR16 FAIL is unchanged AND is now covered by an explicit user-authorized VOID record. Scored under C09 verdict reasoning, not as a fresh Model-F defect.
- G0 and G0-recovery roots unmodified (match R1 §2 pre snapshot field-by-field). PASS.
- P0 and G2 roots still absent. PASS.

## 8. C07 citation bar + log/memory fidelity — PASS

- Disposition D03 bars citation explicitly: the four files "MUST NOT be cited by any future RESULT_SUMMARY, report, table, decision entry, or promotion argument"; "NOT a G1 result, NOT a performance measurement"; future authorized G1 "MUST use a NEW output root and MUST NOT reuse, compare against, or overwrite this one"; G1 authorization is not consumed/satisfied. No path is left by which these numbers can later be read as a result without violating the record. PASS.
- docs/decision-log.md (2026-09-07 entry, VOID_RETAINED_IN_PLACE, PR16 addressed by record only, clearance requires independent re-review, no P0 authorization) matches the disposition without overstatement. PASS.
- AGENT_PROJECT_MEMORY.md (2026-09-07 entry: VOID, forensic-only, R1 FAIL sole blocker PR16, I09 cause, 165/165 repair pointer, auth stays false, re-review required, new-root requirement) matches the disposition without overstatement. PASS.

## 9. C08 lifecycle at HEAD + commits + push state — PASS

cycle_state.yaml AT HEAD (git show HEAD:...) — worktree file is identical:

- structure_execution_authorized false; g0_execution_authorized false; g0_recovery_execution_authorized false (attempts 1, completed 1, result G0_RECOVERY_PASS, accepted true); p0_cost_execution_authorized false; g1_execution_authorized false; g2_execution_authorized false; synthetic_execution_authorized false; real_execution_authorized false; formal_execution_authorized false; implementation_authorized false; implementation_accepted true; scientific_promotion false; decoder_executed true (historical structure/G0 context only, unchanged by disposition); cal_rows_read 0; val_rows_read 0; next_gate P0_PACKET_REVIEW. PASS — no authorization granted or implied by the disposition.

Commits:

- b986ca11 (Model-F candidate + prepare/verify runner): 7 files, all under comparison_bench/src, comparison_bench/tests, openspec model-f-input-preparation, scripts/v72p2d5_prepare_model_f_input.py. No workspace/ path committed. Message matches content. PASS.
- 7c59d375 (P0/G1/G2 mother-prefix candidate + isolation repair): 7 files, all under formal_ir core, rate_mother tests, openspec production-path, scripts/v72p2d5_gf32_rate_mother.py (docstring + synthetic-runner mapping only). No workspace/ path committed. No .py change beyond the P0/G1/G2 prefix-slice candidate, the test containment repair, and the CLI runner mapping. Message matches content. PASS.
- 20204726 (docs-only: memory, decision-log, cycle packets, disposition, incident, isolation evidence, R1 review, cycle_state, mother-plan OpenSpec sync, project.md): 20 files, docs/openspec only. No workspace/ path committed. No .py change. cycle_state.yaml diff is the R2 amendment context (11-line change, auth flags untouched). Message matches content. PASS.
- git status -sb: branch formal-ir-v72p1-addendum-clean, ahead 3 (the three local commits above), nothing pushed. The ahead-3 state is the expected local-only disposition landing; no push was performed by or for this review. PASS.

## 10. C09 py_compile + pytest — PASS

- py_compile on all four packet-listed files (v72p2d5_model_f_input.py, v72p2d5_gf32_rate_mother.py, scripts/v72p2d5_prepare_model_f_input.py, scripts/v72p2d5_gf32_rate_mother.py): exit 0. PASS.
- pytest (fresh additive basetemp workspace/v72p2d5_preresult_r2_20260907_r2, -p no:cacheprovider, --tb=line, -q), literal summary line:

  195 passed, 1 warning in 27.16s

  (warning literal: PytestConfigWarning Unknown config option: cache_dir.) Failing test ids: none.
- Collection: 195 total (test_v72p2d5_model_f_input.py 31 + test_v72p2d5_gf32_rate_mother.py 134 + test_v72p2d4_cal_gf32_model_rate_audit.py 30).
- Relation to R1: R1 recorded 5 failed / 186 passed (191 total) on the pre-rework tests. DISAGREEMENT is expected and explained, not a conflict: commit 7c59d375 rewrote the 5 absence-gate tests to be lifecycle-independent (M24/P12 now assert P0/G2 absence + Model-F/G1 snapshot preservation with G1 explicitly INVALID_UNAUTHORIZED; M19/M21/P0G1G2_i now use absent-tmp roots + binder/writer booms + BLOCKED) and added 4 tests (test_M21_param_missing_isolation x3 params + test_TIS_static_authorized_synthetic_isolation x1): 191 + 4 = 195. All 5 formerly-failing checks now pass in their rewritten form; core Model-F tests (M01-M18, P01-P11, M20) pass as in R1.
- Post-test re-stat: all five protected roots byte-identical to §1; P0/G2 still absent; basetemp contains only additive tmp dirs. PASS.

## 11. C10 isolation repair vs recurrence risk — PASS for Model-F scope, residual risk recorded

- Read SAFE A (unauthorized False chokes; M19, P0G1G2_e), SAFE B (authorized True only with injected counts_ab + p_b + explicit FakeDecoder + tmp out_dir; M20 reaches 440 fake calls into tmp only, formal G1 snapshot unchanged), SAFE C (authorized True bare only in allowlisted M21 loop / M21-param / P0G1G2_i with absent-tmp root + binder/writer booms expecting MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS, tmp empty, real roots unchanged), and the TIS AST static guard (covers direct mod.run_*, getattr-parametrized runner, and fn loop-vars; asserts boom + BLOCKED + absent_model_f + bind_historical_decoder + writer-evidence markers on every non-SAFE-B authorized call; forbids --execution-authorized literals, *_execution_authorized true literals, and STATE_PATH writes / yaml dumps in tests). Claims in TEST_ISOLATION_REWORK_EVIDENCE_R1.md verified against test source. PASS.
- Honest limit (decides recurrence risk): production defaults are UNCHANGED — run_g1_synthetic (and P0/G2 equivalents) with bare authorized=True still binds the historical decoder and writes the formal root (target = G1_FORMAL_ROOT if out_dir is None; decoder = bind_historical_decoder() if decode_fn is None). Recurrence prevention is therefore test-side only. A future bare authorized call from any new, non-guarded entry path would re-trigger the incident; the TIS test catches it only when the suite runs. This does NOT block Model-F input acceptance (no such call occurred in this review; all 195 tests pass; formal roots untouched), but it is a binding constraint on future P0/G1/G2 packets: they must re-verify isolation and must never issue bare authorized calls. Recorded as remaining risk R-R1 below, not as a Model-F defect.

## 12. C11 additive discipline + review authority — PASS

- This review created exactly ONE new file (this document). No .py / existing .md / cycle_state / log / memory / openspec / prior-review edit. No commit, no push, no status change, no P0 authorization, no RESULT_SUMMARY / OPERATOR_RETURN / run_01. Only additive side effect besides this file: the packet-authorized pytest basetemp workspace/v72p2d5_preresult_r2_20260907_r2/ (tmp dirs only, separate from all formal roots). PASS.
- No result accepted, no promotion granted, Model-F status remains MODEL_F_INPUT_CANDIDATE with formal false. PASS.

## 13. Verdict reasoning on PR16 (the single R1 blocker)

R1 PR16 required formal-root absence; the G1 root physically persists, so a literal re-application of R1 PR16 would still read FAIL. This review judges PR16 by its INTENT — no unauthorized execution contaminating the Model-F acceptance chain — against the intervening explicit user decision:

1. The contamination vectors are closed by record: the G1 numbers are permanently VOID, barred from every citation surface (D03), consume no authorization (D06), and any future G1 must use a new root with no reuse or comparison.
2. The lifecycle is unchanged and clean: every *_execution_authorized false, scientific_promotion false, next_gate P0_PACKET_REVIEW, no P0 authorization granted or implied.
3. The Model-F artifact — the actual acceptance subject — recomputes exactly as R1 recorded (C01-C04 all PASS, every value AGREE) and is byte-identical before and after this review.
4. The defect cannot recur through the accepted artifact: the isolation repair is verified (C10, 195/195), and the residual prod-default risk is fenced to future phase packets, not to this acceptance.
5. The alternative (FAIL) would demand reversal of an explicit, reasoned user decision (delete/move both rejected on record) while adding zero scientific protection to the Model-F claim.

PR16 is therefore CLEARED BY RECORD for the purpose of Model-F input acceptance. The physical retention is forensic evidence, not a result.

## 14. Closing verdict block

- Verdict: PRE_RESULT_REVIEW_PASS — the Model-F input candidate is READY_FOR_MAIN_RESULT_ACCEPTANCE.
- Plain statement: this readiness signal is NOT itself a result acceptance, and it is NOT a P0 authorization. Acceptance of the main result and any P0/G1/G2 authorization remain separate, explicitly authorized steps. All *_execution_authorized stay false; next_gate stays P0_PACKET_REVIEW.
- Strongest evidence-backed claim: the frozen Model-F CAL input (CAL702..1725, 1024 frames x 256 pairs = 262144 symbols) is internally consistent with canonical Alice-Bob orientation and exactly derived P(B) marginal (axis-0 maxAbs 0.0; wrong axis distinguishable), with agreeing summary metadata and untouched G0/G1 snapshots.
- Explicitly NOT claimed: no FER, no leakage, no SKR, no net key, no qualification, no method verdict on NB-LDPC or the dv3 mother, no G1 performance conclusion (the voided app_exact 0 / app_failure 1.0 / oracle 0 numbers carry zero scientific meaning), no P0 authorization.
- Remaining risks: R-R1 prod-side bare-authorized defaults unchanged (test-side guard only; future phase packets must re-verify isolation). R-R2 M24/P12 no longer assert global formal-root absence (lifecycle-independent snapshots instead); unexpected new formal outputs rely on per-test snapshot comparisons, not a global gate.
- Checklist:
  - [x] Matches OpenSpec spec for Model-F artifact scope (G1 presence dispositioned VOID by explicit record, barred from all citation surfaces).
  - [x] Tests pass (literal 195 passed, 0 failed; R1 delta explained by the authorized isolation rework).
  - [x] No scope creep (this review: one review file + packet-authorized basetemp only; pre-existing G1 root dispositioned, not created here).
  - [ ] docs/decision-log.md or docs/troubleshooting.md needs update? No update performed in this task (edit forbidden); the disposition is already recorded in both decision-log and project memory. No further entry required by this review.