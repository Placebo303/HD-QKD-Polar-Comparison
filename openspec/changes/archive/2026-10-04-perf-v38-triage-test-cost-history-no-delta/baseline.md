# Task 1 freeze record — perf-v38-triage-test-cost (no code change)

Date (UTC): 2026-09-08. Branch: formal-ir-v72p1-addendum-clean.
Runner: `python -u -m pytest -p no:cacheprovider --durations=20 --basetemp=workspace/perf-v38/<uuid>`,
`PYTHONPATH=comparison_bench/src` (old-style `comparison_bench.formal_ir` imports in v38/v39 files).

## 1. `--collect-only` — 38 T0 cases confirmed

`comparison_bench/tests/test_v38_architecture_triage.py`: **38 tests collected in 0.31s** (list §4).
Sibling T1 file `comparison_bench/tests/test_v39_lanec_robustness.py`: 29 tests.

## 2. Symbol清单 (file:line, frozen)

- `load_v31` = `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py:226`
  `load_v31_qc_baseline_matrices` (JSON `matrix_payloads.json` → 3× uint8 arrays).
  Re-exported by `v38_architecture_triage.py`. Sibling loader `load_v25_channel_counts` (:205).
- source support/cycles =
  `v38_architecture_triage.py:208 get_canonical_support_edges`,
  `:229 enumerate_canonical_simple_cycles` (lengths 4/6/8 + edge→cycle map),
  `:331 compute_cycle_submatrix_rank`, `:350 classify_cycle_algebraic_degeneracy`.
- rank = `v35_algorithm_development.py:159 compute_gf32_rank`
  (exact GF(32) Gaussian elimination; hot loop, see profile §5).
- fake runner = `v38_architecture_triage.py:976 evaluate_single_block(..., fake_runner=False)`
  and `:1362 run_v38r1_development(..., fake_runner=False)` (+ `:1231 run_v38_development`).
  `raw_errors` analogue in this cost center = `errors_initial` key (int count of initial L2
  symbol errors; shape/contract fixed, see R4 row). Production default `fake_runner=False`
  never enters fake; `scripts/execute_v38r1_development.py main` binds `fake_runner=False`
  (guarded by test_r1_20).
- 编排 fixtures: v38 test file has no module fixtures (inline `monkeypatch` + `_fresh_workspace_test_root`
  under `workspace/v38r1_tests/<label>_<uuid>`); orchestration inputs are the frozen constants
  `LANE_PRODUCTION_SEEDS` / `V36_A3_BLOCK_SEEDS` / `V31_BASELINE_REFERENCE`.

## 3. 三档 -k 名单 (frozen)

Slow (5, by measured duration §5) → `@pytest.mark.slow` in Task 6 (P4):

- `test_t1_construction_seed_determinism` (77.43s)
- `test_t6_t7_t8_lane_a_support_and_search` (74.41s)
- `test_t30_t31_lane_a_rank_semantics` (74.10s)
- `test_production_orchestration_all_27_attempts_and_fail_closed` (641.11s)
- `test_orchestration_not_ready_lane_gets_zero_decoder_runs` (633.67s)

Tiers:

- **T0** (default lane, gate wall < 60s): v38 file minus the 5 slow = **33 tests**.
  Baseline wall ≈ 10–15s (sum of non-slow shards: S1 ~2.2s + S2 ~1.1s + S3 ~1.4s + S4 ~0.1s).
- **T1**: full v38 file (**38 tests**), single lane, same-job double run (cold + warm).
  Baseline wall ≈ **1506s** (shard sum S1 79.64 + S2 75.63 + S3 75.54 + S4 1275.16).
- **Full**: v38 (38) + v39 (29). Slow piece baseline = the 5 above; v39 file baseline 6.84s
  (28 passed + 1 pre-existing env failure `test_sha_binding_exact_equality`, which asserts
  HEAD == origin/formal-ir-mainline and fails on this branch regardless of code — unrelated).

T0 -k expression (pre-mark baseline form; post-P4 equivalent = `-m "not slow"`):

```text
comparison_bench/tests/test_v38_architecture_triage.py
  --deselect ...::test_t1_construction_seed_determinism
  --deselect ...::test_t6_t7_t8_lane_a_support_and_search
  --deselect ...::test_t30_t31_lane_a_rank_semantics
  --deselect ...::test_production_orchestration_all_27_attempts_and_fail_closed
  --deselect ...::test_orchestration_not_ready_lane_gets_zero_decoder_runs
```

## 4. T0 38-case list (collect-only order)

test_t1_construction_seed_determinism, test_t2_all_matrices_exact_dimensions,
test_t3_gf32_rank_validation, test_t4_canonical_simple_cycle_enumeration,
test_t4_oracle_cycle_enumeration_comparison, test_t5_cycle_submatrix_rank_classification,
test_t6_t7_t8_lane_a_support_and_search, test_lane_a_tie_break_rules,
test_t9_t10_t25_t26_t35_lane_b_properties, test_t11_t12_t38_lane_c_properties,
test_t22_t23_t24_lane_c_capacity_calculation, test_t13_no_hidden_retry_seeds,
test_t14_structural_selection_ignores_decoder, test_t15_structurally_invalid_prototype_never_selected,
test_t16_structural_not_ready_does_not_invalidate_other_lanes, test_t17_exact_v36_a3_block_seeds,
test_t21_real_git_sha_verification, test_order_invariant_block_pairing,
test_block_set_integrity_validation, test_t18_t19_t32_triage_gate_branches,
test_t20_terminal_state_branches, test_t27_t28_prng_contract,
test_t29_lane_a_incremental_objective_matches_brute_force, test_t30_t31_lane_a_rank_semantics,
test_t33_t34_coefficient_sampling_and_edge_order, test_t36_t37_support_before_coefficients,
test_t39_t40_t41_lane_a_behavioral_rank_and_early_stop, test_production_orchestrator_guard,
test_production_orchestration_all_27_attempts_and_fail_closed,
test_orchestration_not_ready_lane_gets_zero_decoder_runs, test_production_seeds_protected_constants,
test_safety_fake_runner_evaluation, test_r1_05_evaluate_single_block_passes_complete_bob_to_posterior,
test_r1_06_corrected_prior_matches_v36_numeric_sentinel,
test_r1_14_reconstructs_exact_nine_winners_and_rejects_metric_drift,
test_r1_15_runner_guard_and_exactly_45_fake_calls,
test_r1_16_r1_17_writer_outputs_additive_files_and_rejects_existing,
test_r1_20_formal_cli_has_no_fake_runner_and_binds_false

## 5. Baseline `--durations=20` top tables

S1 (6 tests, wall 79.64s): t1 77.43s, t2 1.88s, rest < 0.005s.
S2 (10 tests, wall 75.63s): t6t7t8 74.41s, t11t12 0.53s, t9t10 0.26s, tie_break 0.04s,
t22t23t24 0.01s, rest < 0.005s.
S3 (11 tests, wall 75.54s): t30t31 74.10s, t36t37 0.80s, t21 0.32s, rest < 0.005s.
S4 (11 tests, wall 1275.16s): prod_orch 641.11s, orch_not_ready 633.67s, rest ≤ 0.01s.
v39 (29 tests, wall 6.84s): t1t2_recon 1.61s, integrity_failure_path 1.45s, t7_fake_e2e 1.35s,
t15_cli 0.77s, sha_binding 0.35s, rest ≤ 0.28s.

Profile (single lane-A construction, 47.4s): 3,784,850 × `compute_gf32_rank` on r×r
cycle submatrices = 37.0s (78%); `enumerate_canonical_simple_cycles` 2 calls = 0.24s;
`load_v31` 1 call = 0.20s (JSON parse). Conclusion: P2 (rank) + P0 (cycles/classify cache)
attack the dominant cost; P1 removes repeat JSON parses across tests; P3 skips unused
prior/syndrome work on the fake path; P4 splits the 5 slows out of the default lane.

## 6. Rollback

Pure record, no code touched. No rollback needed.
