# PATH_MAP — S3 root organization

Tracked files were moved with `git mv` on 2026-10-04. Historical document bodies were left unchanged; references inside them may retain the old paths below.

## Versioned root reports and artifacts

| Old root paths | New path (same basename) |
|---|---|
| `V65_CHANNEL_COMPATIBILITY_REPORT.md`, `v65_channel_compatibility.json`, `v65_data_readiness.json`, `v65_data_registry.json` | `archive/v65_v72p0/v65/` |
| `V67_FEASIBILITY_REPORT.md`, `v67_acquisition_inventory.json`, `v67_data_registry.json`, `v67_feasibility_table.csv`, `v67_feasibility_table.json`, `v67_manifest.json`, `v67_spike_summary.json` | `archive/v65_v72p0/v67/` |
| `V68_BALANCED_REPORT.md`, `v68_data_registry.json`, `v68_manifest.json`, `v68_results.json`, `v68_table.csv`, `v68_table.json` | `archive/v65_v72p0/v68/` |
| `V69_THREE_LAYER_REPORT.md`, `v69_data_registry.json`, `v69_manifest.json`, `v69_results.json`, `v69_table.csv`, `v69_table.json` | `archive/v65_v72p0/v69/` |
| `V70_BINARY_SOFT_JOINT_REPORT.md`, `v70_data_registry.json`, `v70_manifest.json`, `v70_results.json`, `v70_table.csv`, `v70_table.json` | `archive/v65_v72p0/v70/` |
| `V70R1_PARAMETRIC_CHANNEL_REPORT.md`, `v70r1_manifest.json`, `v70r1_results.json`, `v70r1_table.csv`, `v70r1_table.json` | `archive/v65_v72p0/v70r1/` |
| `V71_AUDIT_REPORT.md`, `V71_KERNEL_REPORT.md`, `v71_audit_report.json`, `v71_data_registry.json`, `v71_manifest.json`, `v71_results.json`, `v71_table.csv`, `v71_table.json` | `archive/v65_v72p0/v71/` |
| `V72P0_BACKEND_AUDIT_REPORT.md`, `V72P0_SYN_REPORT.md`, `v72p0_backend_audit_report.json`, `v72p0_data_registry_synthetic.json`, `v72p0_manifest.json`, `v72p0_results.json`, `v72p0_table.csv`, `v72p0_table.json` | `archive/v65_v72p0/v72p0/` |
| `test_v68_spike_small.py`, `test_v69_three_layer_small.py`, `test_v70_binary_soft_joint_small.py`, `test_v70r1_parametric_channel_model_small.py`, `test_v71_soft_joint_factor_kernel_small.py`, `test_v72p0_soft_joint_binary_synthetic_small.py`, `test_v72p1_soft_joint_adapter_small.py`, `test_v72p2_real_smoke_small.py` | `archive/v65_v72p0/tests/` |

## Other tracked root paths

| Old path | New path |
|---|---|
| `tmp_v27r/` | `archive/legacy_tmp/tmp_v27r/` |
| `tmp_v28r/` | `archive/legacy_tmp/tmp_v28r/` |
| `v72p1_synthetic_qual/` | `archive/legacy_tmp/v72p1_synthetic_qual/` |
| `bootstrap_clone_clean.py`, `dsh-opencode-go-pro.patch.yml`, `总体判断.txt` | `archive/misc/` with the same basename |
| `HANDOFF.md`, `AGENT_HANDOFF.md`, `CURRENT_TASK.md` | `docs/archive/handoffs/` with the same basename |
| `REVIEW_CHECKLIST.md`, `RUN_COMMANDS.md` | `docs/` with the same basename |

Untracked and ignored root clutter moved to `workspace/_quarantine_20261004/` is enumerated in [QUARANTINE_MANIFEST.md](QUARANTINE_MANIFEST.md). No tracked file was deleted. No change to the path-producing source was made: the scanned Python sources only showed the correctly joined `Path("workspace/v30r_tests") / ...` test roots; the producer of the malformed root artifact was not located.


## S4 docs and closed-cycle moves (2026-10-04)

Only `git mv` was used for the tracked source paths below. Historical document bodies were not rewritten.

### Top-level docs by era

| Old path | New path |
|---|---|
| `docs/A1_ARITHMETIC_RECOMPUTE_20260921.md` | `docs/archive/v80/A1_ARITHMETIC_RECOMPUTE_20260921.md` |
| `docs/A1_ESTIMATOR_AND_SLOPE_VERIFICATION_20260921.md` | `docs/archive/v80/A1_ESTIMATOR_AND_SLOPE_VERIFICATION_20260921.md` |
| `docs/channel-aware-de-gate-proposal-20260816.md` | `docs/archive/v19_v72/channel-aware-de-gate-proposal-20260816.md` |
| `docs/CORRELATION_ALIGNMENT_CAPABILITY_20260921.md` | `docs/archive/v80/CORRELATION_ALIGNMENT_CAPABILITY_20260921.md` |
| `docs/CURRENT_MAINLINE.md` | `docs/archive/historical_2026/CURRENT_MAINLINE.md` |
| `docs/DATA_INVENTORY_20260921.md` | `docs/archive/v80/DATA_INVENTORY_20260921.md` |
| `docs/decoder-improvement-plan-20260816.md` | `docs/archive/v19_v72/decoder-improvement-plan-20260816.md` |
| `docs/expanded-real-ir-evidence-20260615.md` | `docs/archive/reports_202606/expanded-real-ir-evidence-20260615.md` |
| `docs/formal-ir-mathematical-method-map-v25-v44.md` | `docs/archive/v19_v72/formal-ir-mathematical-method-map-v25-v44.md` |
| `docs/github-publication-20260824.md` | `docs/archive/historical_2026/github-publication-20260824.md` |
| `docs/group-meeting-ir-analysis-20260615.md` | `docs/archive/reports_202606/group-meeting-ir-analysis-20260615.md` |
| `docs/H0_3_ISOLATION.md` | `docs/archive/historical_2026/H0_3_ISOLATION.md` |
| `docs/H0_4_INTERPRETER.md` | `docs/archive/historical_2026/H0_4_INTERPRETER.md` |
| `docs/hd-qkd-ir-comparison-owned-roadmap-20260907.md` | `docs/archive/reports_202609/hd-qkd-ir-comparison-owned-roadmap-20260907.md` |
| `docs/hd-qkd-ir-performance-roadmap-20260824.md` | `docs/archive/historical_2026/hd-qkd-ir-performance-roadmap-20260824.md` |
| `docs/hd-qkd-ir-roadmap-review-20260823.md` | `docs/archive/historical_2026/hd-qkd-ir-roadmap-review-20260823.md` |
| `docs/ir-method-comparison-state-20260615.md` | `docs/archive/reports_202606/ir-method-comparison-state-20260615.md` |
| `docs/ir-optimization-report-20260615.md` | `docs/archive/reports_202606/ir-optimization-report-20260615.md` |
| `docs/LATEST_RESULTS_20260327.md` | `docs/archive/historical_2026/LATEST_RESULTS_20260327.md` |
| `docs/memory-triage-20260615-progress-plan.md` | `docs/archive/reports_202606/memory-triage-20260615-progress-plan.md` |
| `docs/nbldpc-focus-plan-20260816.md` | `docs/archive/v19_v72/nbldpc-focus-plan-20260816.md` |
| `docs/nbldpc-v19-v23-review-summary-20260816.md` | `docs/archive/v19_v72/nbldpc-v19-v23-review-summary-20260816.md` |
| `docs/nbldpc-v21-bob-only-plan-20260816.md` | `docs/archive/v19_v72/nbldpc-v21-bob-only-plan-20260816.md` |
| `docs/nbldpc-v21-v24-closeout-and-successor-plan-20260817.md` | `docs/archive/v19_v72/nbldpc-v21-v24-closeout-and-successor-plan-20260817.md` |
| `docs/nbldpc-v24-gate-report-20260818.md` | `docs/archive/v19_v72/nbldpc-v24-gate-report-20260818.md` |
| `docs/nbldpc-v25-empirical-channel-and-factorization-plan-20260818.md` | `docs/archive/v19_v72/nbldpc-v25-empirical-channel-and-factorization-plan-20260818.md` |
| `docs/nbldpc-v25-empirical-channel-and-factorization-report-20260818.md` | `docs/archive/v19_v72/nbldpc-v25-empirical-channel-and-factorization-report-20260818.md` |
| `docs/nbldpc-v26-channel-informed-multilevel-de-report-20260819.md` | `docs/archive/v19_v72/nbldpc-v26-channel-informed-multilevel-de-report-20260819.md` |
| `docs/nbldpc-v29-retrospective-finite-code-report-20260820.md` | `docs/archive/v19_v72/nbldpc-v29-retrospective-finite-code-report-20260820.md` |
| `docs/nbldpc-v30r-projective-safe-finite-graph-report-20260820.md` | `docs/archive/v19_v72/nbldpc-v30r-projective-safe-finite-graph-report-20260820.md` |
| `docs/nbldpc-v31-closeout-audit-addendum-20260821.md` | `docs/archive/v19_v72/nbldpc-v31-closeout-audit-addendum-20260821.md` |
| `docs/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md` | `docs/archive/v19_v72/nbldpc-v31-deterministic-finite-graph-redesign-report-20260820.md` |
| `docs/nbldpc-v31-finite-graph-redesign-plan-20260820.md` | `docs/archive/v19_v72/nbldpc-v31-finite-graph-redesign-plan-20260820.md` |
| `docs/nbldpc-v32-main-review-verdict-20260822.md` | `docs/archive/v19_v72/nbldpc-v32-main-review-verdict-20260822.md` |
| `docs/nbldpc-v32-main-verdict-unit-correction-20260823.md` | `docs/archive/v19_v72/nbldpc-v32-main-verdict-unit-correction-20260823.md` |
| `docs/nbldpc-v32-operating-point-audit-correction-addendum-20260823.md` | `docs/archive/v19_v72/nbldpc-v32-operating-point-audit-correction-addendum-20260823.md` |
| `docs/nbldpc-v35-successor-plan-20260824.md` | `docs/archive/v19_v72/nbldpc-v35-successor-plan-20260824.md` |
| `docs/nbldpc-v36-empirical-graph-development.md` | `docs/archive/v19_v72/nbldpc-v36-empirical-graph-development.md` |
| `docs/nbldpc-v37-p0-degree-feasibility.md` | `docs/archive/v19_v72/nbldpc-v37-p0-degree-feasibility.md` |
| `docs/nbldpc-v37-p1-plan.md` | `docs/archive/v19_v72/nbldpc-v37-p1-plan.md` |
| `docs/nbldpc-v38-direction-screen-plan.md` | `docs/archive/v19_v72/nbldpc-v38-direction-screen-plan.md` |
| `docs/NBPOLAR_TRACK.md` | `docs/archive/historical_2026/NBPOLAR_TRACK.md` |
| `docs/nonbinary-ldpc-efficiency-roadmap-survey.md` | `docs/archive/v19_v72/nonbinary-ldpc-efficiency-roadmap-survey.md` |
| `docs/nonbinary-ldpc-v11-sc-de-plan.md` | `docs/archive/v19_v72/nonbinary-ldpc-v11-sc-de-plan.md` |
| `docs/nonbinary-ldpc-v13-existing-data-diagnostic-plan.md` | `docs/archive/v19_v72/nonbinary-ldpc-v13-existing-data-diagnostic-plan.md` |
| `docs/nonbinary-ldpc-v13-r3-fresh-data-intake-20260816-plan.md` | `docs/archive/v19_v72/nonbinary-ldpc-v13-r3-fresh-data-intake-20260816-plan.md` |
| `docs/nonbinary-ldpc-v13-r3-legacy-drift-audit-review-and-plan-20260816.md` | `docs/archive/v19_v72/nonbinary-ldpc-v13-r3-legacy-drift-audit-review-and-plan-20260816.md` |
| `docs/nonbinary-ldpc-v7-audit-v8-plan.md` | `docs/archive/v19_v72/nonbinary-ldpc-v7-audit-v8-plan.md` |
| `docs/nonbinary-ldpc-v9-plan.md` | `docs/archive/v19_v72/nonbinary-ldpc-v9-plan.md` |
| `docs/openspec-phase0-reconciliation-20260725.md` | `docs/archive/historical_2026/openspec-phase0-reconciliation-20260725.md` |
| `docs/POLAR_CODE_MAINFLOW_20260327.md` | `docs/archive/routes/POLAR_CODE_MAINFLOW_20260327.md` |
| `docs/POLAR_VS_LDPC_CROSS_REPO_COMPARISON_20260927.md` | `docs/archive/routes/POLAR_VS_LDPC_CROSS_REPO_COMPARISON_20260927.md` |
| `docs/PREALIGN_CENSUS_PREFLIGHT_20260921.md` | `docs/archive/v80/PREALIGN_CENSUS_PREFLIGHT_20260921.md` |
| `docs/PRIOR_COST_ACCOUNTING_AUDIT_20260921.md` | `docs/archive/v80/PRIOR_COST_ACCOUNTING_AUDIT_20260921.md` |
| `docs/PRIOR_COST_ACCOUNTING_DECISION_20260921.md` | `docs/archive/v80/PRIOR_COST_ACCOUNTING_DECISION_20260921.md` |
| `docs/PRIOR_COST_CLAIM_REVIEW_20260921.md` | `docs/archive/v80/PRIOR_COST_CLAIM_REVIEW_20260921.md` |
| `docs/project-progress-plan-20260615.md` | `docs/archive/reports_202606/project-progress-plan-20260615.md` |
| `docs/PROJECT_CLASSIFICATION_20260427.md` | `docs/archive/reports_202604/PROJECT_CLASSIFICATION_20260427.md` |
| `docs/real-ir-success-audit-20260615.md` | `docs/archive/reports_202606/real-ir-success-audit-20260615.md` |
| `docs/real-ir-success-first-plan-20260615.md` | `docs/archive/reports_202606/real-ir-success-first-plan-20260615.md` |
| `docs/RESEARCH_DIRECTION_REPORT_20260924.md` | `docs/archive/reports_202609/RESEARCH_DIRECTION_REPORT_20260924.md` |
| `docs/RESULTS_INTERPRETATION.md` | `docs/archive/historical_2026/RESULTS_INTERPRETATION.md` |
| `docs/RESULTS_MANIFEST_20260427.md` | `docs/archive/reports_202604/RESULTS_MANIFEST_20260427.md` |
| `docs/REVIEW_CHECKLIST.md` | `docs/archive/historical_2026/REVIEW_CHECKLIST.md` |
| `docs/route-a-diagnostic-conclusion-20260816.md` | `docs/archive/routes/route-a-diagnostic-conclusion-20260816.md` |
| `docs/route-b-c-d-next-steps-plan-20260819.md` | `docs/archive/routes/route-b-c-d-next-steps-plan-20260819.md` |
| `docs/route-b-m1-acceptance-20260816.md` | `docs/archive/routes/route-b-m1-acceptance-20260816.md` |
| `docs/route-b-m1-result-20260816.md` | `docs/archive/routes/route-b-m1-result-20260816.md` |
| `docs/route-b-m1b-result-20260816.md` | `docs/archive/routes/route-b-m1b-result-20260816.md` |
| `docs/route-b-m2-boundary-20260816.md` | `docs/archive/routes/route-b-m2-boundary-20260816.md` |
| `docs/route-b-m2-q32-highrate-result-20260816.md` | `docs/archive/routes/route-b-m2-q32-highrate-result-20260816.md` |
| `docs/route-b-m2-q32-moderate-result-20260816.md` | `docs/archive/routes/route-b-m2-q32-moderate-result-20260816.md` |
| `docs/route-b-m2-qsc-control-result-20260816.md` | `docs/archive/routes/route-b-m2-qsc-control-result-20260816.md` |
| `docs/route-b-m2-r06-parallel-result-20260816.md` | `docs/archive/routes/route-b-m2-r06-parallel-result-20260816.md` |
| `docs/route-b-m2-r061-r062-result-20260816.md` | `docs/archive/routes/route-b-m2-r061-r062-result-20260816.md` |
| `docs/route-b-m2-r063-result-20260816.md` | `docs/archive/routes/route-b-m2-r063-result-20260816.md` |
| `docs/route-b-m2-real-search-result-20260816.md` | `docs/archive/routes/route-b-m2-real-search-result-20260816.md` |
| `docs/route-b-m2-seeded-r062-r063-result-20260816.md` | `docs/archive/routes/route-b-m2-seeded-r062-r063-result-20260816.md` |
| `docs/route-c1-design-draft-20260816.md` | `docs/archive/routes/route-c1-design-draft-20260816.md` |
| `docs/ROUTE_A_BIT_PLANE_INTERFACE_20260414.md` | `docs/archive/routes/ROUTE_A_BIT_PLANE_INTERFACE_20260414.md` |
| `docs/ROUTE_A_CORRECTNESS_BASELINE_20260410.md` | `docs/archive/routes/ROUTE_A_CORRECTNESS_BASELINE_20260410.md` |
| `docs/ROUTE_A_FORMAL_VERIFICATION_20260410.md` | `docs/archive/routes/ROUTE_A_FORMAL_VERIFICATION_20260410.md` |
| `docs/RUN_COMMANDS.md` | `docs/archive/historical_2026/RUN_COMMANDS.md` |
| `docs/SECURITY_MODEL.md` | `docs/archive/historical_2026/SECURITY_MODEL.md` |
| `docs/SIBLING_PRIOR_PARAMETERIZATION_AUDIT_20260921.md` | `docs/archive/v80/SIBLING_PRIOR_PARAMETERIZATION_AUDIT_20260921.md` |
| `docs/three-way-ir-comparison-plan-20260816.md` | `docs/archive/routes/three-way-ir-comparison-plan-20260816.md` |
| `docs/TTBIN_ENV_SETUP_20260921.md` | `docs/archive/v80/TTBIN_ENV_SETUP_20260921.md` |
| `docs/TTBIN_INGEST_ROUTES_20260921.md` | `docs/archive/v80/TTBIN_INGEST_ROUTES_20260921.md` |
| `docs/TTBIN_MEMBER_SEMANTICS_20260921.md` | `docs/archive/v80/TTBIN_MEMBER_SEMANTICS_20260921.md` |
| `docs/TTBIN_READING_CROSSCHECK_20260921.md` | `docs/archive/v80/TTBIN_READING_CROSSCHECK_20260921.md` |
| `docs/v19-binary-mlc-prototype-result-20260816.md` | `docs/archive/v19_v72/v19-binary-mlc-prototype-result-20260816.md` |
| `docs/v19-ldpc-de-screener-result-20260816.md` | `docs/archive/v19_v72/v19-ldpc-de-screener-result-20260816.md` |
| `docs/v34-formal-execution-er1-closeout-20260824.md` | `docs/archive/v19_v72/v34-formal-execution-er1-closeout-20260824.md` |
| `docs/v34-p3-implementation-candidate-and-ox-alpha-handoff-20260824.md` | `docs/archive/v19_v72/v34-p3-implementation-candidate-and-ox-alpha-handoff-20260824.md` |
| `docs/v35-algorithm-development-report.md` | `docs/archive/v19_v72/v35-algorithm-development-report.md` |
| `docs/v49-distribution-shift-diagnosis-20260827.md` | `docs/archive/v19_v72/v49-distribution-shift-diagnosis-20260827.md` |
| `docs/v72p3-progress-and-issues-report-2026-09-19.md` | `docs/archive/v19_v72/v72p3-progress-and-issues-report-2026-09-19.md` |
| `docs/X1_ENTRY_BLOCKER_ASSESSMENT_20260921.md` | `docs/archive/v80/X1_ENTRY_BLOCKER_ASSESSMENT_20260921.md` |
| `docs/AUTHORITATIVE_RESULTS_CHECKSUMS.json` | `docs/archive/reports_202607/AUTHORITATIVE_RESULTS_CHECKSUMS.json` |

### Closed research cycles

| Old path | New path |
|---|---|
| `docs/research_cycles/NBLDPC-GF32-BATCHED-FWHT-20261002/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-BATCHED-FWHT-20261002/` |
| `docs/research_cycles/NBLDPC-GF32-CONSTRUCTION-CANARY-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-CONSTRUCTION-CANARY-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-CYCLE-SOURCE-OVERLAP-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-CYCLE-SOURCE-OVERLAP-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-DAMPING-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-DAMPING-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-DEGREE-ADMITTED-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-DEGREE-ADMITTED-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-DEGREE-PROFILE-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-DEGREE-PROFILE-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-EDGE-LABEL-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-EDGE-LABEL-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-EDGE-STATE-20261004/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-EDGE-STATE-20261004/` |
| `docs/research_cycles/NBLDPC-GF32-EDGE-STATE-R2-20261004/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-EDGE-STATE-R2-20261004/` |
| `docs/research_cycles/NBLDPC-GF32-ENDPOINT-ABLATION-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-ENDPOINT-ABLATION-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-FULL-SOFTPRIOR-EFFICIENCY-20261002/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-FULL-SOFTPRIOR-EFFICIENCY-20261002/` |
| `docs/research_cycles/NBLDPC-GF32-GLOBAL-CENSUS-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-GLOBAL-CENSUS-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-INCREMENTAL-SYNDROME-20261004/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-INCREMENTAL-SYNDROME-20261004/` |
| `docs/research_cycles/NBLDPC-GF32-INDEPENDENT-REPLICA-DRAFT/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-INDEPENDENT-REPLICA-DRAFT/` |
| `docs/research_cycles/NBLDPC-GF32-ITER-CAP-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-ITER-CAP-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-JOINT-CHECK2-20261002/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-JOINT-CHECK2-20261002/` |
| `docs/research_cycles/NBLDPC-GF32-JOINT-TOP2-20261002/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-JOINT-TOP2-20261002/` |
| `docs/research_cycles/NBLDPC-GF32-JOINT-TOP3-20261004/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-JOINT-TOP3-20261004/` |
| `docs/research_cycles/NBLDPC-GF32-KERNEL-HOTSPOTS-20261002/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-KERNEL-HOTSPOTS-20261002/` |
| `docs/research_cycles/NBLDPC-GF32-LABEL-MECHANISM-20260930/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-LABEL-MECHANISM-20260930/` |
| `docs/research_cycles/NBLDPC-GF32-MIXED05-20261002/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-MIXED05-20261002/` |
| `docs/research_cycles/NBLDPC-GF32-MRB-REACHABILITY-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-MRB-REACHABILITY-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-MRB-REAGGREGATE-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-MRB-REAGGREGATE-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-MRB-RESCUE-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-MRB-RESCUE-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-MRB-TOP6-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-MRB-TOP6-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-RANK2-FALLBACK-20261002/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-RANK2-FALLBACK-20261002/` |
| `docs/research_cycles/NBLDPC-GF32-RESIDUAL-SWEEP-20261004/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-RESIDUAL-SWEEP-20261004/` |
| `docs/research_cycles/NBLDPC-GF32-ROW-ORDER-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-ROW-ORDER-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-SEARCH-DEPTH-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-SEARCH-DEPTH-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-SHAPE-FINE-DRAFT/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-SHAPE-FINE-DRAFT/` |
| `docs/research_cycles/NBLDPC-GF32-SHAPE-LABEL-20260930/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-SHAPE-LABEL-20260930/` |
| `docs/research_cycles/NBLDPC-GF32-SHORT-CYCLE-CENSUS-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-SHORT-CYCLE-CENSUS-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-SOFT-PRIOR-COST-PROFILE-20261002/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-SOFT-PRIOR-COST-PROFILE-20261002/` |
| `docs/research_cycles/NBLDPC-GF32-SOFT-PRIOR-REPLICA-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-SOFT-PRIOR-REPLICA-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-SOFT-PRIOR-RESCUE-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-SOFT-PRIOR-RESCUE-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-SOURCE-AWARE-LABEL-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-SOURCE-AWARE-LABEL-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-SOURCE-AWARE-LABEL-R2-20261001/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-SOURCE-AWARE-LABEL-R2-20261001/` |
| `docs/research_cycles/NBLDPC-GF32-SOURCE-MAPPING-DRAFT/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-SOURCE-MAPPING-DRAFT/` |
| `docs/research_cycles/NBLDPC-GF32-TOP3-RUNTIME-20261003/` | `docs/research_cycles/_closed/nbldpc_gf32_microprobes_20260930_1004/NBLDPC-GF32-TOP3-RUNTIME-20261003/` |
| `docs/research_cycles/M0-REALFRAME/` | `docs/research_cycles/_closed/m0_m3d/M0-REALFRAME/` |
| `docs/research_cycles/M1-FINITE-LENGTH/` | `docs/research_cycles/_closed/m0_m3d/M1-FINITE-LENGTH/` |
| `docs/research_cycles/M2-REALCOMP/` | `docs/research_cycles/_closed/m0_m3d/M2-REALCOMP/` |
| `docs/research_cycles/M2-HDCASCADE-SYNTH/` | `docs/research_cycles/_closed/m0_m3d/M2-HDCASCADE-SYNTH/` |
| `docs/research_cycles/M2-LAYEREDBIN-SYNTH/` | `docs/research_cycles/_closed/m0_m3d/M2-LAYEREDBIN-SYNTH/` |
| `docs/research_cycles/M3A-NESTED-200P8/` | `docs/research_cycles/_closed/m0_m3d/M3A-NESTED-200P8/` |
| `docs/research_cycles/M3B-NESTED-PAIRED/` | `docs/research_cycles/_closed/m0_m3d/M3B-NESTED-PAIRED/` |
| `docs/research_cycles/M3C-REAL-U2-2M/` | `docs/research_cycles/_closed/m0_m3d/M3C-REAL-U2-2M/` |
| `docs/research_cycles/M3D-ITER250-SYNTH/` | `docs/research_cycles/_closed/m0_m3d/M3D-ITER250-SYNTH/` |
| `docs/research_cycles/CHAN-QUALITY-SURVEY/` | `docs/research_cycles/_closed/chan_quality_btrack_ctrack/CHAN-QUALITY-SURVEY/` |
| `docs/research_cycles/CROSS-BATCH-AUDIT-20260929/` | `docs/research_cycles/_closed/chan_quality_btrack_ctrack/CROSS-BATCH-AUDIT-20260929/` |
| `docs/research_cycles/PROXY-NONSTATIONARY-FAITHFULNESS/` | `docs/research_cycles/_closed/chan_quality_btrack_ctrack/PROXY-NONSTATIONARY-FAITHFULNESS/` |
| `docs/research_cycles/N2048-BUDGET-RECALC/` | `docs/research_cycles/_closed/v80_nbldpc_jan21/N2048-BUDGET-RECALC/` |
| `docs/research_cycles/N2048-GAIN-SWEEP/` | `docs/research_cycles/_closed/v80_nbldpc_jan21/N2048-GAIN-SWEEP/` |
| `docs/research_cycles/POLAR-SCALING-BOUND/` | `docs/research_cycles/_closed/v80_nbldpc_jan21/POLAR-SCALING-BOUND/` |
| `docs/research_cycles/N2048-RESIDUAL-SOURCE/` | `docs/research_cycles/_closed/v80_nbldpc_jan21/N2048-RESIDUAL-SOURCE/` |
| `docs/research_cycles/PERPLANE-BINARY-LDPC/` | `docs/research_cycles/_closed/joint_pricing_stage0_u1_proxy/PERPLANE-BINARY-LDPC/` |
| `docs/research_cycles/JOINT-PRICING/` | `docs/research_cycles/_closed/joint_pricing_stage0_u1_proxy/JOINT-PRICING/` |
| `docs/research_cycles/JOINT-PRICING-R2/` | `docs/research_cycles/_closed/joint_pricing_stage0_u1_proxy/JOINT-PRICING-R2/` |
| `docs/research_cycles/PROXY-RECALIBRATION/` | `docs/research_cycles/_closed/joint_pricing_stage0_u1_proxy/PROXY-RECALIBRATION/` |
| `docs/research_cycles/PROXY-RECAL-R2/` | `docs/research_cycles/_closed/joint_pricing_stage0_u1_proxy/PROXY-RECAL-R2/` |
| `docs/research_cycles/U1-CEILING-PROBE/` | `docs/research_cycles/_closed/joint_pricing_stage0_u1_proxy/U1-CEILING-PROBE/` |
