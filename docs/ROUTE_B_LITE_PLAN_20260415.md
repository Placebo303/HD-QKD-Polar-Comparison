# Route B-lite Plan (2026-04-15)

Route B-lite starts from the Route A formal correctness baseline and stays inside the binary Polar framework. It is not a full channel-aware Polar construction.

## Current Baseline

Use this Route A formal cross-loss pack as the fixed input:

```text
results/_tmp_routeA_correctness_formal_stageD_cross_loss
```

It covers `6/10/16/20 dB` with `484/484` formal rows and keeps `uhv1_per_block` verification and `epsilon_EC_bound` correctness budgeting.

## B-lite Scope

B1 is an error-model audit from `a_eff/b_eff` and Route A replay logs. B2 builds asymmetric binary channel model tables and capacity diagnostics. B3 only selects a very-small A/B subset for a later fixed-order model-aware replay ablation.

B-lite does not claim:

```text
channel-aware Polar construction completed
density evolution implemented
Gaussian approximation construction implemented
q-ary Polar implemented
```

## Bias And Prior Boundary

B-lite v1 uses same-point modeling and replay evaluation:

```text
modeling_sample_source_tag = same_routeA_formal_sidecar_a_eff_b_eff
eval_sample_source_tag = routeA_formal_replay_blocks_same_point
sample_reuse_bias_risk_tag = same_a_eff_b_eff_for_model_and_eval
```

Layer-level sample gates reduce optimistic bias but do not eliminate it. Default gates are `n_pairs_modeling >= 4096` and `min_conditional_count >= 512`; a conservative `8192/1024` sensitivity count is reported in the summary.

The B2 main line is `uniform_prior_asym_mi`, matching the intended uniform-prior decoder model diagnostic. `empirical_prior_asym_mi` is audit-only and must not be mixed with decoder-gain claims.

Capacity deltas are model diagnostics only. They do not imply replay, block success, PIE, or SKR improvement.

## Commands

Build B1 audit:

```powershell
python tools\routeB_build_error_audit.py --routeA-cross-loss-dir results\_tmp_routeA_correctness_formal_stageD_cross_loss --output-dir results\_tmp_routeB_lite_error_audit --workers 8
```

Build B2 channel model tables:

```powershell
python tools\routeB_build_channel_model_table.py --audit-dir results\_tmp_routeB_lite_error_audit
```

Select B3 very-small A/B subset:

```powershell
python tools\routeB_select_ab_subset.py --audit-dir results\_tmp_routeB_lite_error_audit --target-size 12
```

## Outputs

```text
results/_tmp_routeB_lite_error_audit/routeB_layer_confusion_table.csv
results/_tmp_routeB_lite_error_audit/routeB_symbol_offset_table.csv
results/_tmp_routeB_lite_error_audit/routeB_point_error_summary.csv
results/_tmp_routeB_lite_error_audit/routeB_model_diagnosis_table.csv
results/_tmp_routeB_lite_error_audit/routeB_error_audit_summary.txt
results/_tmp_routeB_lite_error_audit/routeB_channel_model_layer_table.csv
results/_tmp_routeB_lite_error_audit/routeB_bsc_vs_asym_capacity_compare.csv
results/_tmp_routeB_lite_error_audit/routeB_channel_model_summary.txt
results/_tmp_routeB_lite_error_audit/routeB_ab_subset_manifest.csv
```

## Next Step Boundary

Only implement model-aware replay after inspecting the B3 subset manifest. The first replay ablation should be LLR-only with fixed `k_best` and fixed polar-weight information-set order. LLR+k adaptation is only justified if the LLR-only subset improves replay outcomes.
