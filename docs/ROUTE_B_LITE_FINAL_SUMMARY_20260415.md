# Route B-lite Final Summary (2026-04-15)

## Final Status

Route B-lite is complete. It should now be treated as an archived diagnostic/validation route, not an active optimization track.

Final classification:

```text
B-lite = completed
conclusion = limited / partial negative result
next_action = stop expanding B-lite; return main effort to Route A / mainline
```

This is not a failed route. B-lite completed its intended job: it quantified BSC mismatch, tested a lightweight asymmetric binary LLR hypothesis, and showed that the hypothesis has local value but is not strong or stable enough for broad application.

## Fixed Baseline And Non-Negotiable Boundaries

B-lite starts from the Route A formal correctness baseline:

```text
results/_tmp_routeA_correctness_formal_stageD_cross_loss
```

Correctness was not changed by B-lite:

```text
verification = uhv1_per_block
epsilon_EC_bound = universal-hash union bound
eps_cor_total = unchanged Route A formal correctness split
correctness_budget_changed_by_B_lite = no
```

B-lite only studied error-model diagnostics and fixed-order LLR-only ablation. It did not implement or claim:

```text
q-ary Polar
nonbinary decoder
density evolution
Gaussian approximation construction
full channel-aware Polar construction
mainline model migration
```

## Completed Work

B1 error audit is complete. It built layer confusion, symbol offset, point error summary, and model diagnosis outputs under explicit same-point modeling/evaluation bias tags.

B2 channel model diagnostics are complete. It built asymmetric binary model tables and BSC-vs-asym capacity diagnostics with uniform-prior and empirical-prior lines separated.

B3 subset LLR-only ablation is complete. The 12-point subset showed local and reproducible positive signal, enough to justify full 20dB validation but not enough for mainline migration or cross-loss full expansion.

B3 full 20dB LLR-only validation is complete. The result was mixed globally and did not support all-point application.

Wider validation was attempted for the 20dB-positive band widths, but the attempted cross-loss runs timed out before producing complete loss-level point tables. These attempts are runtime-blocked records, not scientific compare results.

## Key Results

B1/B2 scientific finding:

```text
bit-plane asymmetric binary mismatch = measurable but not strong dominant effect
symbol-level offset-like structure = stronger and more widespread
capacity_delta_asym_minus_bsc = small at system level
```

B3 subset result:

```text
selected_points = 12
improvement_points = 8
degradation_points = 2
mean_delta_decoder_fail_rate_oracle = -0.0408266842
mean_delta_block_success = 0.0408266842
mean_delta_SKR_secure_actual_ir_bps = 325.6918293
subset_decision = enough for full 20dB gate only
```

B3 full 20dB result:

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

The full 20dB result has a real bin-width-dependent structure: `50/180/200 ps` are positive at 20dB, while `100/120 ps` are negative. This is useful scientific information, but it is not broad enough to justify applying `asym_binary_v1` everywhere.

## Final Interpretation

B-lite showed that fixed-order `asym_binary_v1` LLRs can help in selected regions, but the effect is not globally stable. The full 20dB gate has nearly equal improved and degraded point counts, and median deltas are zero. Therefore the observed gains are local, not a system-wide replay improvement.

Because correctness columns are unchanged, this is a clean negative/limited conclusion about the LLR model itself rather than a budget-accounting artifact.

## What Not To Do Next

Do not run full cross-loss B3 by default.

Do not apply `asym_binary_v1` to all points.

Do not migrate `asym_binary_v1` into the main reporting line.

Do not describe B-lite as channel-aware Polar construction.

Do not spend further mainline effort on B-lite unless a new plan specifically targets symbol-level offset modeling or true reliability-order construction.

## Relationship To Mainline

Route A remains the main correctness/security baseline. B-lite is an archived side study that informs future modeling decisions. Its practical contribution is to rule out simple bit-plane asymmetric binary LLR replacement as a broadly useful mainline upgrade under the current fixed polar-weight order.

If this route is revisited, the next scientifically meaningful direction is not more all-point `asym_binary_v1` replay. It should start from symbol-level offset structure or from a genuine channel-aware reliability-order construction plan.

## Reusable Status Summary

```text
Route B-lite is completed. It kept Route A correctness unchanged (`uhv1_per_block`, universal-hash `epsilon_EC_bound`, unchanged `eps_cor_total`) and only studied error-model diagnostics plus fixed-order LLR-only ablation. B1/B2 found that bit-plane asymmetric binary mismatch is measurable but not the dominant structure; symbol-level offset-like mismatch is stronger. B3 subset showed local reproducible gains, but full 20dB validation was mixed: 47 improved, 46 degraded, 28 tied, with zero median improvement and unchanged correctness columns. The final conclusion is limited / partial negative: useful local signal, but not stable enough to support `GO_EXPAND_LLR_ONLY`, all-point application, or mainline migration. Stop expanding B-lite and return main effort to Route A / mainline.
```
