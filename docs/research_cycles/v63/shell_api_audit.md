# Shell API Audit — V63 NB-LDPC Polar Shell Integration (READ-ONLY)

**HEAD**: 5602f11c65b2590254e89a1b95c7384f4bbbfd38 (origin/formal-ir-mainline)
**Date**: 2026-08-30
**Scope**: Poll 10 shell components file/function/signature, verify read-only (git diff src==0, experiments==0, tools==0)
**Verdict**: PASS — all listed APIs are read-only reusable, no signature mutation required (R63-02).

| # | Component | File | Function / Class | Signature | Reuse Mode | Notes |
|---|---|---|---|---|---|---|
| 1 | TTBin读取 | src/qkd_io/ttbin_pipeline.py | _read_ttbin_timetags (via src/reconciliation/run_nbldpc_demo_point.py) | def _read_ttbin_timetags(path: Path) -> TTBinEvents | READ_ONLY import | Returns time_ps/channel; shell reads only |
| 2 | 通道选择 | src/qkd_io/ttbin_pipeline.py | resolve_point_sources() | def resolve_point_sources(point: dict) -> dict | READ_ONLY | Channel selection A1/B5 per point metadata |
| 3 | delay/pairing | experiments/run_e2e_pipeline.py | _extract_one_point(d,bw) + pairing_mode nearest | def _extract_one_point(d: int, bw: int) -> dict | READ_ONLY | Pairing policy nearest, bin_width 200ps, legacy_v1 |
| 4 | symbol materialization | comparison_bench/src/comparison_bench/io/dataset_builder.py | build_frame_batch | def build_frame_batch(df, dataset_id, dimension, frame_len_symbols) -> FrameBatch | READ_ONLY | Materializes 1024 symbols per block, validates [0,1024) |
| 5 | session/source/frame provenance | comparison_bench/src/comparison_bench/io/pairs_loader.py | load_pairs_table / normalize_pair_columns + FrameBatch.metadata | def load_pairs_table(path) -> DataFrame; def normalize_pair_columns(df) -> DataFrame | READ_ONLY | Preserves source, block_id, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024 |
| 6 | 参数估计分层 | src/workflow/coarse_grain_joint.py | compute_delta_distribution_from_joint_sparse | def compute_delta_distribution_from_joint_sparse(joint_counts_sparse, dimension, with_prob) | READ_ONLY | H(A|B) estimation for stratification only |
| 7 | verification/丢帧 | formal_ir/v35_algorithm_development.py | compute_tag_64 | def compute_tag_64(empty: bytes, x2: ndarray) -> int | READ_ONLY | L2-only tag_scope, syndrome_ok and tag_ok, undetected isolation |
| 8 | PA | src/reconciliation/pa.py (via experiments PA segment) | run_pa / pa_key_length (proxy) | def run_pa(reconciled_symbols, leak_bits) -> bytes (proxy: leak=actual_disclosure_bits) | READ_ONLY input swapped | Shell swaps input to NbLdpc actual_disclosure_bits (1064/1094/1104 etc), tag 64 already included |
| 9 | 认证开销报告 | experiments/run_e2e_pipeline.py + pipeline/run_ir_benchmark.py | _result_row / _frame_rows | def _result_row(result, batch) -> dict | READ_ONLY | Reports leakage, runtime, throughput; shell adds stage_used |
| 10 | Polar PIE/SKR 参数参考 | comparison_bench/src/comparison_bench/io/polar_existing_bridge.py | benchmark_rows_from_polar_output + compute_beta_eff_empirical | def benchmark_rows_from_polar_output(path) -> DataFrame; def compute_beta_eff_empirical(leak, raw_ber, n) -> float | READ_ONLY POLAR_REFERENCE_PROXY | beta derived, never hand-filled; shadow proxy only |

Checks:
- git diff -- src/ ==0 : PASS
- git diff -- experiments/ ==0 : PASS
- git diff -- tools/ ==0 : PASS
- git diff -- comparison_bench/src/comparison_bench/methods/base.py ==0 : PASS (R63-02, IRRunResult frozen)
- R63-01 s=32*u1+u2 exact factorization documented, reconciled_symbols full 10-bit
- R63-04 DOMAIN_CALIBRATION_REQUIRED gate precedes PA/proxy

Conclusion: All 10 shell APIs are traceable, read-only reusable, no signature change. Adapter will import them via comparison_bench/io and src read-only paths; PA leakage source will be rejected if Polar leak_EC is used (Phase4 fake test verifies).
