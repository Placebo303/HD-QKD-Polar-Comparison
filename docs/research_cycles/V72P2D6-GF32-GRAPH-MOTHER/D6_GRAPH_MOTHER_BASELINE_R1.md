# D6 baseline gate record R1 (D6-B01, read-only evidence)

Date (UTC): 2026-09-08. Operator: strong autonomous operator, packet R1.

- Branch: `formal-ir-v72p1-addendum-clean` (confirmed via
  `git branch --show-current`).
- HEAD: `821388d6fd2a50fc24559c8b9c3895de89ae32a9` (confirmed via
  `git rev-parse HEAD`).
- Appendix commit `821388d6`: `git show --stat HEAD` = 1 file
  (`.../TEST_EVIDENCE_APPENDIX.log`, 191 insertions).
- D5 `cycle_state.yaml` (`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/`):
  `d5_current_path_stopped: true`,
  `d5_decomposition_successor_terminal: DECOMPOSITION_NO_N64_RECOVERY`,
  `next_gate: D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL`.
- Nine execution authorization keys all false:
  `implementation_authorized`, `structure_execution_authorized`,
  `g0_execution_authorized`, `g0_recovery_execution_authorized`,
  `g1_execution_authorized`, `g2_execution_authorized`,
  `synthetic_execution_authorized`, `real_execution_authorized`,
  `formal_execution_authorized`; `scientific_promotion: false`.
- G2 absent: `workspace/v72p2d5_g2*` glob empty; no `workspace/d6_graph_mother_r1_*` root exists yet.
- Protected roots metadata-only snapshot (name/size/mtime_ns + direct
  children; contents never opened or hashed):
  - `workspace/v72p2d5_g1/20260907_r2`: size 0, mtime_ns
    1788806390516340700; children `execution_summary.json`, `report.md`,
    `results.json`, `table.csv`.
  - `workspace/v72p2d5_model_f_input/20260907_r1`: size 0, mtime_ns
    1788718027043698800; children `model_f_input.npz`,
    `model_f_input_summary.json`.
  - `workspace/v72p2d5_g0/20260905_r2`: size 0, mtime_ns
    1788626074451921900; children `execution_summary.json`, `report.md`,
    `results.json`, `table.csv`.
  - `workspace/v72p2d5_structure/20260905_r2`: children
    `execution_summary.json`, `report.md`, `results.json`, `table.csv`.
    (`workspace/v72p2d5_p0` absent; P0 cost evidence lives under the D5
    cycle per `p0_cost_result_accepted: true`, scope COST_MEASUREMENT_ONLY.)
- Scope cleanliness: `git diff --numstat` 0 lines, `git diff --cached
  --numstat` 0 lines. Porcelain shows 1887 tracked-modified paths, all
  pre-existing EOL (LF→CRLF) churn, informational per packet; no staged
  changes.
- Exact untracked allowlist at HEAD (88 paths, preserved, never staged
  except the D6/OpenSpec paths created by this task): `.workbuddy/`,
  `V65_CHANNEL_COMPATIBILITY_REPORT.md`,
  `comparison_bench/configs/cascade_beta_opt_small.yaml`,
  `comparison_bench/outputs_comparison/{cascade_beta_opt,
  cascade_single_eval_20260829_184106_fa434a,
  cascade_single_eval_20260829_184133_b930da,
  cascade_single_real_test_20260830,
  cascade_single_tuning_20260829_183839_fcb2d9, formal_ir_methods/*,
  nonbinary_diagnostics/nbldpc_v32_finite_de_bridge/run_01/per_block.jsonl,
  transfer_evaluation/20260812_v1_v5c2_evaluation_only/*,
  v55_intake_20260828/, v72p2d4_cal_gf32_model_rate_audit_20260905/}`,
  `comparison_bench/src/comparison_bench/{analysis/,
  cli/run_cascade_beta_sweep.py, cli/run_cascade_longframe.py,
  formal_ir/v72p2d4_cal_gf32_model_rate_audit.py, methods/cascade/,
  methods/cascade_single_kernel.py}`,
  `comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py`,
  `docs/hd-qkd-ir-comparison-owned-roadmap-20260907.md`,
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_*_PROMPT.md +
  D5_*_TASK_PACKET.md` (8 task/prompt files),
  `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/` (packet + prompt),
  `openspec/changes/{cascade-beta-optimal-path,
  formal-ir-comparison-owned-end-to-end-roadmap,
  formal-ir-future-nbpolar-app-transfer,
  formal-ir-future-power-of-two-dimension-generalization,
  formal-ir-occam-failure-ablation,
  formal-ir-v56-input-contract-reconstruction/{calibration_verification.json,
  verification_manifest.json},
  formal-ir-v56d1-raw-a2-diagnosis/diagnosis_raw_a2.json,
  formal-ir-v56d2-calibration/v56d2_calibration.json,
  formal-ir-v65ar2-first-match-pipeline/INVALID_RESULT_NOTE.md}`,
  `outputs_comparison/`, `scripts/{analyze_v64_stage_ablation.py,
  v72p2d4_cal_gf32_model_rate_audit.py}`,
  `v65_channel_compatibility.json`, `v65_data_readiness.json`,
  `v65_data_registry.json`, `v72p1_synthetic_qual/`.
  (New in this commit, staged exactly: `openspec/changes/
  v72p2d6-gf32-graph-mother-successor/` (4 files),
  `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/{cycle_state.yaml,
  D6_GRAPH_MOTHER_PREREG_R1.md, D6_GRAPH_MOTHER_BASELINE_R1.md}`.)

Verdict: D6-B01 PASS. No STOP condition met.
