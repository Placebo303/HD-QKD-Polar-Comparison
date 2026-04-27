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

## B3 LLR-only Stop/Go Gate

Run the current very-small subset gate with:

```powershell
python tools\routeB_run_b3_subset_ablation.py --audit-dir results\_tmp_routeB_lite_error_audit --routeA-cross-loss-dir results\_tmp_routeA_correctness_formal_stageD_cross_loss --output-dir results\_tmp_routeB_lite_b3_subset_ablation --workers 2
```

Outputs:

```text
results/_tmp_routeB_lite_b3_subset_ablation/routeB_b3_subset_compare.csv
results/_tmp_routeB_lite_b3_subset_ablation/routeB_b3_subset_summary.md
results/_tmp_routeB_lite_b3_subset_ablation/routeB_b3_subset_runtime.csv
results/_tmp_routeB_lite_b3_subset_ablation/routeB_b3_subset_point_notes.csv
```

Current gate result from the 12-point subset is `GO_FULL_20DB`: proceed only to full 20 dB validation, not to immediate cross-loss promotion or mainline migration.

## Full 20dB Validation Gate

The next gate is full 20dB LLR-only validation over all 121 points. The only intended variable is the LLR model:

```text
baseline = bsc_legacy
ablation = asym_binary_v1
verification = uhv1_per_block
epsilon_EC_bound = universal_hash_union_bound
eps_cor_total = unchanged from Route A formal correctness
frozen ordering = unchanged
k_best = unchanged
```

Run:

```powershell
python tools\routeB_run_full20dB_llr_ablation.py --audit-dir results\_tmp_routeB_lite_error_audit --routeA-cross-loss-dir results\_tmp_routeA_correctness_formal_stageD_cross_loss --output-dir results\_tmp_routeB_lite_full20dB_llr_ablation --workers 4 --overwrite
```

The runner first tries `workers=4`, then falls back to `2`, then `1` if the replay output is incomplete or a child process fails. The output files are:

```text
results/_tmp_routeB_lite_full20dB_llr_ablation/routeB_full20dB_compare.csv
results/_tmp_routeB_lite_full20dB_llr_ablation/routeB_full20dB_summary.md
results/_tmp_routeB_lite_full20dB_llr_ablation/routeB_full20dB_runtime.csv
results/_tmp_routeB_lite_full20dB_llr_ablation/routeB_full20dB_point_notes.csv
```

Stop/go is decided from the full 20dB result, not from the 12-point subset. The allowed final labels are:

```text
STOP_AT_FULL_20DB
GO_EXPAND_LLR_ONLY
GO_WIDER_VALIDATION_BUT_NOT_MAINLINE
```

Even if the full 20dB gate is positive, it only supports wider LLR-only validation. It does not support q-ary Polar, nonbinary decoding, channel-aware construction, or mainline migration.

## Full 20dB Gate Result

Completed output:

```text
results/_tmp_routeB_lite_full20dB_llr_ablation
```

Decision: `GO_WIDER_VALIDATION_BUT_NOT_MAINLINE`.

The result is mixed globally (`47` improved, `46` degraded, `28` tied) with zero median deltas, but it has a clear bin-width structure. `50/180/200 ps` are positive at 20dB; `100/120 ps` are negative. This does not justify all-point application or mainline migration.

Band-limited wider validation was attempted but is runtime-blocked in this turn:

```text
results/_tmp_routeB_lite_wider_llr_validation
results/_tmp_routeB_lite_wider_llr_validation_10_16_20
```

## Final Completed Status

Route B-lite is complete and should no longer be treated as an active expansion track.

Final classification:

```text
B-lite = completed
conclusion = limited / partial negative result
next_action = stop expanding B-lite; return main effort to Route A / mainline
```

The completed route includes B1 error audit, B2 channel-model diagnostics, B3 subset LLR-only ablation, and B3 full 20dB LLR-only validation. The final interpretation is that simple bit-plane `asym_binary_v1` LLR replacement under fixed polar-weight order has local value but is not stable enough for broad use. It does not justify `GO_EXPAND_LLR_ONLY`, all-point application, or mainline migration.

Use `docs/ROUTE_B_LITE_FINAL_SUMMARY_20260415.md` as the authoritative short handoff page for future agents.
