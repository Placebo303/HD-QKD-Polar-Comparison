# Tasks: optimize-real-ir-methods-after-success

## 1. Grid Configuration & Config File
- [x] Create Cascade, LDPC, and qLDPC sweep configs under `comparison_bench/configs/` (replacing the proposed combined `benchmark_optimize.yaml`).

## 2. Cascade-Lite Optimization
- [x] Refine transcript leakage accounting in `cascade_lite.py` to count actual disclosed bits exactly.
- [x] Run Cascade sweeps scanning passes and block size schedules on the representative real frames.
- [x] Record lowest-leakage configurations that maintain 100% verification success.

## 3. Layered LDPC Sweep
- [x] Run LDPC sweeps lowering `parity_fraction` down to 0.5.
- [x] Compare `llr_mode` and `bitplane_rate_mode`.
- [x] Record the minimum parity fraction required for verified success across regimes.

## 4. qLDPC Reference Optimization
- [x] Run qLDPC reference sweeps on low-noise representative datasets (`bw180_blk0`).
- [x] Identify if custom check fractions or row weights yield stable verification success.

## 5. Scalability Sweep
- [x] Run benchmark sweeps on larger frame sizes (`frame_len_symbols = 128, 256, 2048`).
  - Reconciliation note: this proves the task wording, but does not fulfill the separate spec requirement for 512/1024-symbol support.
- [x] Verify and analyze empirical efficiency ($\beta_{eff}$) behavior (confirmed that it remains clamped to 0.0 due to verification/CRC overhead on short/medium blocks, as detailed in Section 6 of the report).

## 6. Polar Baseline Reference Alignment
- [x] Ensure polar results are aligned on the representative points and missing fields are accounted.

## 7. Report Generation
- [x] Run full pytest validation suite.
- [x] Write the final selection report `docs/ir-optimization-report-20260615.md`.
