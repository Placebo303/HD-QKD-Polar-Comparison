# IR Method Comparison State - 2026-06-15

This note preserves the current decision-relevant state for the error-correction / information-reconciliation comparison work. It avoids duplicating the full repository inventory already recorded in `AGENT_PROJECT_MEMORY.md`.

## 1. Fixed Scope And Invariants

- The original Polar workflow is a frozen baseline.
- Do not modify, refactor, rename, move, or delete original Polar core code.
- New implementation work belongs in `comparison_bench/`.
- New comparison outputs must be additive under `comparison_bench/outputs_comparison/`.
- Do not convert `unavailable`, `reference`, `stub`, `decode_failed`, or failed verification states into `ok`.
- Do not hand-fill `beta_eff_empirical`; it must be derived from leakage and error inputs.

The comparison layer is built around the common contract:

- `FrameBatch`
- `IRRunConfig`
- `IRRunResult`

Candidate method families currently tracked:

- `polar_existing`
- `cascade_lite`
- `layered_ldpc_lite`
- `qldpc_reference`

## 2. Polar Existing Baseline

`polar_existing` is no longer a pure stub. It reads real Polar result tables through `polar_existing_bridge.py`.

Current semantics:

- explicit Polar result files may be provided;
- otherwise the bridge recursively searches the configured result root;
- existing Polar CSV outputs are preferred;
- outer CLI execution is possible only when explicitly configured;
- missing files must not be reported as success.

Important interpretation rule:

- `method_status=ok` for `polar_existing` means a real existing Polar result table was read successfully.
- It does not mean the comparison layer reran the original Polar algorithm.

Known data limitation:

- `leak_EC_actual_bits` and `runtime_s` can remain `NaN` for imported Polar results because the source Polar result files may not contain those fields.

Historical provenance:

- Legacy Windows real-data roots under `D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\...` are provenance only, not future defaults.
- A representative imported file was `polar_diag_summary.csv`.
- Companion files previously scanned for supplemental fields included `polar_e2e_results.csv`, `polar_e2e_results_refresh.csv`, `polar_layer_metrics.csv`, `*_tmp_grid_table.csv`, and `*_tmp_src_table.csv`.

## 3. Real-Data Frame Batch State

The comparison layer supports sidecar-to-`FrameBatch` conversion from:

- `a_eff.npy`
- `b_eff.npy`
- `sidecar_meta.json`

Historical representative sidecar point:

- legacy path pattern: `D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\...\sidecars\d8_bw180\blk0`
- `a_eff.npy`: shape `(256,)`
- `b_eff.npy`: shape `(256,)`
- `dimension=8`
- `bin_width_ps=180`
- `frame_len_symbols=64`
- produced 4 complete real-data frames

The later sidecar scan expanded to a real-data grid including:

- dimensions: `4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096`
- bin widths in ps: `20, 30, 40, 50, 60, 80, 100, 120, 150, 180, 200`

Known frame-batch artifact:

- `comparison_bench/outputs_comparison/real_sidecars_frame_batch.parquet`

## 4. Cascade Lite State

`cascade_lite` has moved from a backend-gated placeholder to an internally executable simplified Cascade-like baseline.

Current implementation characteristics:

- bit-mapped baseline;
- supports `gray` and `natural` mapping;
- multi-pass parity comparison;
- recursive bisection after parity mismatch;
- flips Bob bits;
- records approximate transcript statistics;
- decomposes leakage into parity disclosures, bisection disclosures, verification bits, and other disclosure bits.

Important interpretation rule:

- It is a real executable simplified Cascade baseline.
- It is not a full industrial Cascade transcript implementation.
- Notes may include `leakage_accounting=approximate_internal_transcript`.

Observed v3 representative sweep summary:

- files: `cascade_param_sweep_results.csv`, `cascade_leakage_diagnostics.csv`
- previously observed status counts: `ok = 179`, `no_verified_success = 141`
- one relatively strong observed configuration:
  - `block_size_schedule = 16,32,64,128`
  - `num_passes = 4`
  - `permutation_mode = seeded_random`
  - `seed = 1`

Current provisional conclusion:

- Among currently executable real-data routes, `cascade_lite` appears to be the most stable on representative points.
- This must remain qualified because the implementation is simplified and representative-point evidence is not automatically final paper-grade evidence.

## 5. Layered LDPC Lite State

`layered_ldpc_lite` moved from backend-gated placeholder to a real executable baseline using `ldpc.BpOsdDecoder` when available.

Important historical fix:

- A previous failure mode allowed results with `post_ir_ser > raw_ser` and zero success to be marked `ok`.
- Status rules were corrected to preserve failure states such as `experimental_failed`, `decode_failed`, `no_verified_success`, and `unavailable`.
- Pipeline-level guards should prevent failed results from being silently marked as `ok`.

Current implementation characteristics:

- independent bit-plane decoding;
- `ldpc.BpOsdDecoder`;
- configurable `parity_fraction`, `max_iter`, `osd_order`, `bp_method`, `mapping`, `llr_mode`, and `bitplane_rate_mode`;
- per-bitplane BER diagnostics;
- verification failure falls back to raw Bob and is counted as decode failure, not success.

Observed v3 representative sweep summary:

- files: `layered_ldpc_param_sweep_results.csv`, `failed_frame_diagnostics.csv`
- previously observed status counts: `ok = 40`, `decode_failed = 440`
- one relatively better observed configuration:
  - `parity_fraction = 0.67`
  - `max_iter = 20`
  - `osd_order = 0`
  - `llr_mode = bsc_estimated`
  - `bitplane_rate_mode = uniform`

Current provisional conclusion:

- Layered LDPC is now a real executable, diagnosable, sweepable baseline.
- It is not currently the most stable real-data route; failures remain concentrated around high raw SER regimes and some high-dimensional points.

## 6. qLDPC Reference State

`qldpc_reference` has moved beyond a simple placeholder toward a real reference-grade q-ary path.

New supporting module:

- `comparison_bench/src/comparison_bench/methods/qary_ldpc.py`

Reference path capabilities:

- internal GF(2^m) fallback;
- `make_gf(q)`;
- `make_qary_ldpc_h(...)`;
- `qary_syndrome(...)`;
- `qary_symbol_error_syndrome(...)`;
- `qary_hard_syndrome_bf(...)`;
- q-ary sparse H;
- q-ary syndrome and hard syndrome decoding;
- verification and leakage accounting.

Important interpretation rule:

- This is a reference-grade q-ary decoder path.
- It is not a full production qLDPC implementation.

Dependency state:

- `galois` was previously confirmed unavailable in the working environment.
- The current path primarily uses the internal `GF(2^m)` fallback.

Observed v3 summary:

- files: `qldpc_param_sweep_results.csv`, `qldpc_decoder_diagnostics.csv`
- previously observed synthetic status counts: `ok = 201`, `reference = 55`
- previously observed real-data representative counts: `ok = 58`, `reference = 102`
- backend status examples:
  - `qary_ldpc_reference_qary_hard_syndrome_bf_internal_gf2m_4`
  - `qary_ldpc_reference_qary_hard_syndrome_bf_internal_gf2m_8`
  - `qary_ldpc_reference_qary_hard_syndrome_bf_internal_gf2m_16`
  - `qary_ldpc_reference_qary_hard_syndrome_bf_internal_gf2m_32`
  - `qary_ldpc_reference_qary_hard_syndrome_bf_internal_gf2m_64`

Current provisional conclusion:

- qLDPC has advanced from a mod-q approximation direction to a real GF(q) syndrome / decoder reference flow.
- It remains research/reference-grade until stronger decoder and dependency status justify stronger claims.

## 7. v2 / v3 Output State

v2 real-data benchmark already covered:

- sidecar scan;
- `polar_existing`;
- `cascade_lite`;
- `layered_ldpc_lite`.

Known v2 outputs:

- `ir_benchmark_results.csv`
- `ir_frame_results.parquet`
- `ir_method_summary.csv`

v3 sweep infrastructure includes:

- append rows;
- append frame rows;
- parameter hash;
- skip existing;
- `force` mechanism;
- `run_errors_ir_v3.csv`;
- manifest writing.

Known v3 outputs:

- `cascade_param_sweep_results.csv`
- `cascade_param_sweep_frame_results.parquet`
- `cascade_leakage_diagnostics.csv`
- `layered_ldpc_param_sweep_results.csv`
- `layered_ldpc_param_sweep_frame_results.parquet`
- `failed_frame_diagnostics.csv`
- `qldpc_param_sweep_results.csv`
- `qldpc_param_sweep_frame_results.parquet`
- `qldpc_decoder_diagnostics.csv`
- `run_errors_ir_v3.csv`
- `ir_v3_run_manifest.json`

Known report tables:

- `report_tables_v3/cascade_best_by_point.csv`
- `report_tables_v3/layered_ldpc_best_by_point.csv`
- `report_tables_v3/qldpc_best_by_point.csv`
- `report_tables_v3/method_best_comparison_by_point.csv`
- `report_tables_v3/failure_region_summary.csv`
- `report_tables_v3/leakage_decomposition_summary.csv`
- `report_tables_v3/representative_points_for_group_meeting.csv`

## 8. Fragile Points

- Git staging/commit may fail with `.git/index.lock` permission errors; this has previously prevented checkpoint commits.
- Pytest cache write permission warnings can appear even when test logic passes.
- PowerShell profile / execution-policy warnings are usually environmental noise.
- `make_report_tables.py` previously failed on `bin_width_ps` NaN handling, then was fixed.
- The first v3 Cascade sweep once failed because the CLI glue did not pass `mapping`; after fixing, the rerun succeeded.
- `run_errors_ir_v3.csv` contains historical error records and must not be interpreted as the current total failure state without context.

## 9. Most Useful Next Directions

The next direction is now defined by `docs/real-ir-success-first-plan-20260615.md` and `openspec/changes/real-ir-success-first/`.

1. Define and enforce real IR success criteria: real paired-symbol input, protocol-allowed disclosure, independent verification, honest failure statuses, and leakage accounting.
2. Use a bounded representative real-frame subset before any broad sweep.
3. Establish Cascade-lite as the first non-Polar real-data success candidate, while retaining the simplified-Cascade caveat.
4. Perform focused Layered LDPC failure diagnostics over raw SER, frame length, `parity_fraction`, `llr_mode`, `bitplane_rate_mode`, and the bit-plane independence assumption.
5. Continue qLDPC only as a reference-grade q-ary feasibility probe until stronger decoder evidence exists.
