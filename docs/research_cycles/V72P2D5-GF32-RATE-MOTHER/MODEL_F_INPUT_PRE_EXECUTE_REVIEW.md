# V72P2D5 Model-F Input Pre-EXECUTE Review (independent, read-only)

- Repository: HD-QKD_Polar_Comparison, Branch: formal-ir-v72p1-addendum-clean
- Cycle: V72P2D5-GF32-RATE-MOTHER, Change: formal-ir-v72p2d5-model-f-input-preparation
- Reviewer: independent pre-execute reviewer / packet author (reviewer-go with packet-author exception)
- Date: 2026-09-07
- Scope: confirm Model-F impl can safely read frozen CAL and generate sole formal artifact; freeze one real prepare/verify; stop at READY_FOR_EXECUTE_AUTH (no auth, no real prepare, no parquet row reads, no P0/G1/G2)
- Allowed runs in this task: py_compile 4 files; focused pytest 3 files; CLI --help; CLI unauth refusal; parquet metadata read-only. No real prepare, no pd.read_parquet load, no CAL/VAL row reads, no decoder, no P0/G1/G2, no formal root creation, no full pytest, no Release cmds, no git add/commit/push.

## Evidence summary (read-only)

- py_compile 4 files: PASS (comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py, scripts/v72p2d5_prepare_model_f_input.py, comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py, scripts/v72p2d5_gf32_rate_mother.py)
- Focused pytest 3 files (test_v72p2d5_model_f_input.py + test_v72p2d5_gf32_rate_mother.py + test_v72p2d4r2_cal_gf32_model_rate_audit.py): 181 passed 0 failed 1 warning (unknown cache_dir) 41.54s, basetemp workspace/v72p2d5_model_f_preexec_20260907a01. Baseline cited 179 passed 17.50s same warning; delta +2 with 0 failed is noted under PX05, not a blocker.
- CLI --help: requires --phase prepare|verify + --registry + --out-dir + --execution-authorized; verify --registry required but ignored per help text.
- CLI unauth refusal: prepare without --execution-authorized -> exit 3 refusing before any work; verify without flag -> exit 3. No reads/writes.
- Parquet metadata (pyarrow only, no row reads): comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet exists is-file, 545280 rows, 1 row-group, columns exactly [frame_id,pair_idx,alice_symbol,bob_symbol].
- Formal roots absent: workspace/v72p2d5_model_f_input/20260907_r1 False; workspace/v72p2d5_p0_cost/20260906_r1 False; workspace/v72p2d5_g1/20260906_r1 False; workspace/v72p2d5_g2/20260906_r1 False.
- Registry identity verified via json load (no parquet rows): schema/session/source/used_2m/columns/CAL 1024 702..1725 sorted nodup exact / VAL 1726..1729 zero intersect / parquet relative path.
- Path resolution probe (no row reads): (registry_parent / parquet_path).resolve() = D:/Code/HD-QKD_Polar_Comparison/workspace/comparison_bench/... exists False; repo-root relative exists True. Both relative and absolute registry invocations hit the wrong join. See PX11.

## PX01-PX28 (each PASS/FAIL + evidence + file:line)

- PX01 branch formal-ir-v72p1-addendum-clean: PASS. Evidence: git rev-parse --abbrev-ref HEAD = formal-ir-v72p1-addendum-clean.
- PX02 Comparison not Release: PASS. Evidence: workdir D:/Code/HD-QKD_Polar_Comparison; no Release modify/execute; boundary AGENTS.md:7-21 respected.
- PX03 Model-F OpenSpec complete no conflict: PASS. Evidence: openspec/changes/formal-ir-v72p2d5-model-f-input-preparation/proposal.md:1-42 (goal/contract/scope), design.md:1-92 (dataflow/canonical/artifact/runner/consumer), tasks.md:1-32 (T1-T6 allowlist), specs/spec.md:1-42 (S-MF/S-MB/S-MW/S-ML/S-MR/S-MC/S-SP); lambda 137.3823795883264 matches D4R2 RESULT_SUMMARY_R2.md:23 and mother PLAN_FREEZE.md:17-18; CAL 702..1725 matches RESULT_SUMMARY_R2.md:11; axis (Alice,Bob) matches PLAN_FREEZE.md:54-57. No conflict with R2_DV3 thresholds/seeds/budgets.
- PX04 impl candidate independent review PASS: PASS (scoped). Evidence: docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/IMPLEMENTATION_REVIEW_R2.md:79-83 verdict PASS (scoped) for mother R2; D4R2 docs/research_cycles/V72P2D4-CAL-RATE/IMPLEMENTATION_REVIEW_R2.md:9 verdict R2_IMPLEMENTATION_ACCEPTED; Model-F focused tests 181 passed 0 failed (see summary); py_compile PASS. Note: Model-F has no separate formal IMPLEMENTATION_REVIEW doc yet (lifecycle READY_FOR_INDEPENDENT_REVIEW per proposal.md:6); this pre-execute static review covers R03/R04 loader/builder semantics except the PX11 path defect which is recorded as the single blocker, not as an impl-logic PASS override.
- PX05 main 179 passed: PASS with note. Evidence: focused 3-file run 181 passed 0 failed 1 warning (unknown cache_dir). Baseline 179 passed same warning; +2 is additive test growth in dirty tree (comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py modified, git status M), 0 failed, warning identical. Not a pre-execute blocker.
- PX06 registry identity: PASS. Evidence: workspace/v72p2d3_real_registry_20260904.json:1035 schema v72p2d3_real_registry_v1; :1036 session 20260123_1M_600k_0dB; :1037 source 1M; :1038 used_2m false; :1028-1033 columns exactly frame_id/pair_idx/alice_symbol/bob_symbol. Verified via json load.
- PX07 CAL 702..1725: PASS. Evidence: workspace/v72p2d3_real_registry_20260904.json:2-1027 cal_frame_ids len 1024 min 702 max 1725 sorted True nodup True exact list(range(702,1726)) True; scripts/v72p2d5_prepare_model_f_input.py:91-93 enforces cal_ids==list(range(702,1726)).
- PX08 VAL 1726..1729 zero intersect: PASS. Evidence: workspace/v72p2d3_real_registry_20260904.json:1039-1044 val [1726,1727,1728,1729]; intersect CAL = set(); scripts/v72p2d5_prepare_model_f_input.py:94-96 enforces val==[1726,1727,1728,1729] never fit.
- PX09 parquet reachable: PASS. Evidence: comparison_bench/outputs_comparison/v55_intake_20260828/pairs/20260123_1M_600k_0dB/pairs.parquet exists True is-file, pyarrow 545280 rows 1 row-group; registry parquet_path workspace/v72p2d3_real_registry_20260904.json:1034 is repo-root relative inside Comparison tree.
- PX10 schema 4 cols: PASS. Evidence: pyarrow schema names [frame_id,pair_idx,alice_symbol,bob_symbol]; registry columns match; scripts/v72p2d5_prepare_model_f_input.py:100 cols same 4.
- PX11 relative resolve correct: FAIL (BLOCKING). Evidence: scripts/v72p2d5_prepare_model_f_input.py:97-99 if not absolute: parquet_path=(Path(registry_path).parent / parquet_path).resolve(). With frozen registry workspace/v72p2d3_real_registry_20260904.json + frozen prepare --registry workspace/... --out-dir workspace/v72p2d5_model_f_input/20260907_r1, join = workspace/comparison_bench/outputs_comparison/.../pairs.parquet. Probe: registry_parent_join exists False; repo-root join exists True; absolute-registry join also False (D:/.../workspace/comparison_bench/...). Windows Path.resolve expected and confirmed. Real parquet lives at repo-root relative, not under workspace/. Authorized prepare would FileNotFound before any CAL read, yielding INPUT_BLOCKED/PREP_FAILED instead of MODEL_F_INPUT_PREPARED. No fix applied per boundary (prod code frozen). Single decisive blocker.
- PX12 loader CAL-only: PASS (logic). Evidence: scripts/v72p2d5_prepare_model_f_input.py:101-108 pd.read_parquet(parquet_path,columns=cols); :102 keep=df[df[frame_id].isin(cal_ids)]; :103-104 require len 262144; :105-107 alice/bob/frames from keep only; no VAL-as-model path; run_prepare :111-120 loader->build->write only. Path bug in PX11 does not alter CAL-only filter semantics once path is corrected.
- PX13 axis Alice,Bob: PASS. Evidence: comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py:100 build_canonical_counts(alice,bob,q=Q); :108 bob_counts=counts.sum(axis=0); :160 axis [Alice,Bob]; design.md:22-30 frozen; test M01 comparison_bench/tests/test_v72p2d5_model_f_input.py:55-68 transpose must fail.
- PX14 p_b marginal: PASS. Evidence: comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py:108-115 bob/262144 sum1 1e-8; :147-149 expect marginal recheck atol 1e-12; no p_b param per :78 signature; tests M06 :143-157 and M14 :300-307.
- PX15 lambda 137.3823795883264: PASS. Evidence: comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py:44 LAMBDA_STAR; :124 lambda_star; :212 check; docs/research_cycles/V72P2D4-CAL-RATE/RESULT_SUMMARY_R2.md:23 selected_lam same value; test M11 :255 and M15 :310-326.
- PX16 formal Model-F absent: PASS. Evidence: Test-Path workspace/v72p2d5_model_f_input/20260907_r1 False pre-exec.
- PX17 P0/G1/G2 absent: PASS. Evidence: Test-Path workspace/v72p2d5_p0_cost/20260906_r1 False; workspace/v72p2d5_g1/20260906_r1 False; workspace/v72p2d5_g2/20260906_r1 False.
- PX18 no-overwrite: PASS. Evidence: comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py:238-239 if exists raise FileExistsError before write; :240 mkdir exist_ok False; :245-247 must be exactly 2 files else RuntimeError; test M08 :169-181 second write refuses first unchanged.
- PX19 only 2 files: PASS. Evidence: comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py:48-49 NPZ_NAME/JSON_NAME; :241-244 savez_compressed + json; :245-247 names=={NPZ,JSON}; :254-263 load requires exactly 2; tests M07 :160-166 and M09 :184-208.
- PX20 decoder/P0 zero: PASS. Evidence: comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py contains no decode/P0 import/call; :174 decoder_calls 0 p0_calls 0; scripts/v72p2d5_prepare_model_f_input.py:119-120 returns decoder 0 p0 0 val 0; :123-127 verify no decoder/parquet; tests M17 :359-381 and M18 :384-404.
- PX21 VAL zero: PASS. Evidence: comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py:171 val_rows_read 0; :218-219 check 0; builder takes only CAL arrays :78; loader rejects VAL for fitting :94-96; tests M17 :376 val 0.
- PX22 wall/RSS frozen: PASS. Evidence: packet freezes invocation 1 CAL 262144 VAL 0 decoder 0 P0/G1/G2 0 wall <=300s RSS <2GiB; impl has no watchdog framework (only outer timeout note per mother historical_g0_decoder docstring); builder is 262k-row in-mem counts, consistent with budget. No hard-killer in runner, recorded as outer observes timeout.
- PX23 unique prepare frozen: PASS. Evidence: scripts/v72p2d5_prepare_model_f_input.py:58-72 build_parser requires --phase/--registry/--out-dir + --execution-authorized, choices prepare/verify, no extra params; frozen prepare python scripts/v72p2d5_prepare_model_f_input.py --phase prepare --registry workspace/v72p2d3_real_registry_20260904.json --out-dir workspace/v72p2d5_model_f_input/20260907_r1 --execution-authorized verified via --help.
- PX24 unique verify frozen: PASS (as-is). Evidence: same parser requires --registry even for verify (ignored per help and run_verify(out_dir) only :123-127); frozen verify python scripts/v72p2d5_prepare_model_f_input.py --phase verify --registry workspace/v72p2d3_real_registry_20260904.json --out-dir workspace/v72p2d5_model_f_input/20260907_r1 --execution-authorized; verify-only reads 2 files revalidates no parquet/write/decoder/P0 per comparison_bench/src/comparison_bench/formal_ir/v72p2d5_model_f_input.py:251-269 and test M18. No new flags invented.
- PX25 P0/G1/G2 still unauthorized: PASS. Evidence: docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml:17 p0 false; :18 g1 false; :19 g2 false; :20 synthetic false; :21 real false; :22 formal false; :8 structure false; :11-12 g0/g0-recovery false. Prepare auth must not imply P0 per packet.
- PX26 Release zero: PASS. Evidence: no Release path modify/execute; workdir Comparison only; git status shows no ../HD-QKD_Polar_Release ops.
- PX27 no rerun/resume/tuning: PASS. Evidence: writer no overwrite/merge/resume/retry per PX18-19; no second command; lambda/seeds frozen; no tuning path in builder/runner.
- PX28 no real prepare in this task: PASS. Evidence: only py_compile, focused pytest with fresh basetemp, --help, unauth refusals (exit 3), pyarrow metadata; no --execution-authorized real prepare; formal roots still absent; no CAL/VAL row reads via pd.read_parquet.

## Final verdict

Verdict: PRE_EXECUTE_REVIEW_FAIL (BLOCKED)

Blocking issue:
- PX11 parquet relative resolution vs registry dir vs repo root. scripts/v72p2d5_prepare_model_f_input.py:97-99 joins registry parent, producing workspace/comparison_bench/... which does not exist, while frozen registry parquet_path is repo-root relative and exists at comparison_bench/... . Authorized prepare with frozen command would fail before CAL read. Requires rework (resolve relative to repo ROOT, not registry parent, or freeze absolute path) + re-review. Do NOT fix prod code in review; do NOT authorize; do NOT execute real prepare.

Non-blocking suggestions:
- Record frozen verify with --registry as-is (parser requires it though ignored); do not invent registry-less verify.
- Note focused count 181 vs baseline 179 (+2, 0 failed) from dirty test growth; no action unless strict count gate is imposed.
- Outer timeout observation for wall <=300s should be explicit in future EXECUTE_AUTH (no watchdog framework per policy).

Checklist:
- [x] Matches OpenSpec spec (except PX11 path defect blocks execution)
- [x] Tests pass (181 passed 0 failed; path defect not covered by fake-loader tests M17 which inject loader)
- [ ] No scope creep (review stayed to Model-F prepare/verify; dirty worktree out-of-scope preserved, no clean/reset)
- [ ] docs/decision-log.md or docs/troubleshooting.md needs update? No update in this task (forbidden to modify); recommend logging PX11 resolver defect in troubleshooting via separate change if desired.

Review PASS is not exec auth. Execution authorized: false. Execution performed: false. Ready for execute auth: false (blocked on PX11 rework).