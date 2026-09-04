# V72P2D3-GF32 Independent Implementation Review

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Cycle: `V72P2D3-GF32`
- Review kind: `IMPLEMENTATION_REVIEW_LOGIC_ONLY`
- Accepted plan Git revision: `e0cf5c6772e26c8de561584941e2fe6eea62666e`
- Reviewed implementation Git revision: `12d66ce0ce44310984129217d9f563eab35c245a`
- Base SHA: `e094f7e548380db4bfcbc1fe73472e670c32379a`
- Verdict: `IMPLEMENTATION_ACCEPTED`
- Lifecycle after this record: `IMPLEMENTATION_ACCEPTED / EXECUTE_NOT_AUTHORIZED`

## 1. Review binding

Read-only review bound to the implementation revision above. The
implementation change contains exactly these three files:

1. `comparison_bench/src/comparison_bench/formal_ir/v72p2d3_gf32_contrast.py`
2. `scripts/v72p2d3_gf32_contrast.py`
3. `comparison_bench/tests/test_v72p2d3_gf32_contrast.py`

No `src/`, `experiments/`, `tools/`, `results/`, V72P1/D1/D2 accepted file,
or existing comparison output was changed by the reviewed commit.

## 2. Logic evidence (no execution, no parquet, no formal directory)

- Test file declares **42** `def test_` units (prior 40 + 2 new
  fake-E2E real-entry chain tests: `test_fake_e2e_real_chain_workspace_20_checks`
  + `test_real_chain_guards_and_bans`), including
  `r6_19_n1024_frozen_nested_cold_true_kernel` covering n=1024
  frozen nested geometry with cold start through the true v35 kernel path.
- New real-entry chain (`require_real_gate` / `validate_registry` /
  `validate_frame_bundle` / `fit_cal_prior_from_frames` /
  `assemble_block_frames` / `validate_nested_matrices` / `run_real_contrast`
  + runner `run_real_orchestration`) keeps the frozen 11-step production order
  (gate -> registry -> CAL/VAL validate -> fit -> assemble block -> A reuse
  -> words -> matrices -> syndromes -> true kernel -> reassemble -> posthoc
  -> four files) on injected fakes only: single VAL block 1726..1729,
  CAL 702..1725, Arm A read-only reuse, word direction bound to v35
  `factorize_f03`, GF32 syndromes Alice-side via `syndrome_of_gf32`,
  production `decode_fn=None` (true v35 kernel, cold each stage, max90 /
  damping1.0), fake `decode_fn` explicit test-only, budgets prep300 / G300 /
  invocation600 / RSS2GiB, four-file schema, workspace-only with production
  root rejected, no parquet import, no real decoder run.
- Worktree qualification for the reviewed revision: `py_compile` OK on all
  three files and `pytest
  comparison_bench/tests/test_v72p2d3_gf32_contrast.py` **42 passed**;
  production contrast root
  `comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904/`
  absent. This review does not accept any synthetic or real-data result.

## 3. Lifecycle

```yaml
implementation_review: PASS
development_execution_authorized: false
formal_execution_authorized: false
real_execution_authorized: false
decoder_executed: false
scientific_promotion: false
```

*Implementation acceptance only. No execution authorized.*
