# Route B-lite Status (2026-04-15)

## Fixed Baseline And Boundaries

Route B-lite uses the Route A formal cross-loss baseline:

```text
results/_tmp_routeA_correctness_formal_stageD_cross_loss
```

Correctness is not a B-lite variable. Verification remains `uhv1_per_block`, `epsilon_EC_bound` remains the universal-hash union bound, and `eps_cor_total` remains the Route A formal correctness split. B-lite only studies error-model diagnostics and LLR-only replay ablation inside the existing binary Polar workflow.

Do not describe B-lite as q-ary Polar, a nonbinary decoder, full channel-aware Polar construction, density evolution, Gaussian approximation construction, or mainline model migration.

## Completed State

B1 error audit, B2 channel model diagnostics, and B3 very-small subset validation are complete. The B3 subset result was positive but limited:

```text
selected_points = 12
improvement_points = 8
degradation_points = 2
mean_delta_decoder_fail_rate_oracle = -0.0408266842
mean_delta_block_success = 0.0408266842
mean_delta_SKR_secure_actual_ir_bps = 325.6918293
correctness_same_epsilon_EC_bound = 1
subset_decision = GO_FULL_20DB
```

This is only enough to justify full 20dB validation. It is not enough to justify cross-loss expansion or mainline migration.

## Scientific Interpretation

B1/B2 show that bit-plane asymmetric binary capacity deltas are small, while symbol-level offset-like structure is strong. The subset replay still showed local positive signal from fixed-order LLR-only ablation. Therefore full 20dB validation is required before deciding whether the replay-level signal is real and stable.

The current hypothesis is narrow: asymmetric LLRs may help the existing fixed polar-weight order in some 20dB regions. This is not evidence that the dominant channel model has been solved.

## Full 20dB Gate

Run:

```powershell
python tools\routeB_run_full20dB_llr_ablation.py --audit-dir results\_tmp_routeB_lite_error_audit --routeA-cross-loss-dir results\_tmp_routeA_correctness_formal_stageD_cross_loss --output-dir results\_tmp_routeB_lite_full20dB_llr_ablation --workers 4 --overwrite
```

The runner compares `bsc_legacy` against `asym_binary_v1` on all 121 20dB points with fixed `k_best`, fixed frozen ordering, and unchanged universal-hash verification. It tries workers `4`, then `2`, then `1` if needed.

Expected outputs:

```text
results/_tmp_routeB_lite_full20dB_llr_ablation/routeB_full20dB_compare.csv
results/_tmp_routeB_lite_full20dB_llr_ablation/routeB_full20dB_summary.md
results/_tmp_routeB_lite_full20dB_llr_ablation/routeB_full20dB_runtime.csv
results/_tmp_routeB_lite_full20dB_llr_ablation/routeB_full20dB_point_notes.csv
```

## Decision Table

Use exactly one final label:

```text
STOP_AT_FULL_20DB
GO_EXPAND_LLR_ONLY
GO_WIDER_VALIDATION_BUT_NOT_MAINLINE
```

Choose `STOP_AT_FULL_20DB` if most points are flat or worse, security-rate changes are negligible, runtime cost is too high, or correctness columns differ.

Choose `GO_WIDER_VALIDATION_BUT_NOT_MAINLINE` if 20dB shows a real but region-concentrated signal that justifies more validation but not broad use.

Choose `GO_EXPAND_LLR_ONLY` only if full 20dB shows stable majority improvement in decoder fail and block success, positive PIE/SKR movement, acceptable runtime, few fallbacks, and unchanged correctness.

## Full 20dB Result Recorded This Turn

Completed output:

```text
results/_tmp_routeB_lite_full20dB_llr_ablation
```

Core result:

```text
point_count = 121
improvement_points = 47
degradation_points = 46
tie_points = 28
mean_delta_decoder_fail_rate_oracle = -0.0055077111
median_delta_decoder_fail_rate_oracle = 0.0
mean_delta_block_success = 0.0055077111
median_delta_block_success = 0.0
mean_delta_PIE_secure_actual_ir = 0.0011274283
mean_delta_SKR_secure_actual_ir_bps = 195.0026791
median_delta_SKR_secure_actual_ir_bps = 0.0
max_abs_delta_epsilon_EC_bound = 0.0
max_abs_delta_lambda_ver_bits_actual = 0.0
max_abs_delta_leak_EC_actual_bits = 0.0
fallback_points = 14
runtime_ratio_new_over_old = 1.0149960574
```

Interpretation: the signal is not globally stable enough for mainline migration or all-point application. It is strongly bin-width structured: `50/180/200 ps` are positive in 20dB, while `100/120 ps` are negative. The full 20dB gate therefore supports `GO_WIDER_VALIDATION_BUT_NOT_MAINLINE`, not `GO_EXPAND_LLR_ONLY`.

## Wider Validation Attempt

A band-limited wider validation was attempted for `50/180/200 ps`. Both the full `6/10/16/20 dB` attempt and the partial `10/16/20 dB` attempt timed out after 3600 seconds before producing complete loss-level point tables. These directories are blocked runtime records, not scientific compare results:

```text
results/_tmp_routeB_lite_wider_llr_validation
results/_tmp_routeB_lite_wider_llr_validation_10_16_20
```

The authoritative completed decision for now remains the full 20dB gate: `GO_WIDER_VALIDATION_BUT_NOT_MAINLINE`.
