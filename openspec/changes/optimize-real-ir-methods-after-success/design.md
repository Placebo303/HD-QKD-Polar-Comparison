# Design: optimize-real-ir-methods-after-success

## Parameter Sweeps and Grids

To find the minimum leakage configuration for each method across raw SER regimes, we will scan the following parameter spaces.

### 1. Cascade-Lite Grid
- **num_passes**: `[2, 3, 4]` (test if 2 or 3 passes suffice for low/medium raw SER, reducing verification overhead).
- **block_size_schedule**: 
  - Standard: `[8, 4, 16, 13]`
  - Growth: `[12, 6, 24, 13]`
  - Bounded: `[16, 32, 64, 128]`
- **permutation_mode**: `['seeded_random', 'fixed']`

### 2. Layered LDPC Grid
- **parity_fraction**: `[1.0, 0.9, 0.8, 0.67, 0.50]`
- **llr_mode**: `['hard', 'bsc_estimated']`
- **bitplane_rate_mode**: `['uniform', 'adaptive']` (adaptive assigns parity checks proportionally to individual bitplane error rates).

### 3. qLDPC Reference Grid
- **check_fraction**: `[0.5, 0.4, 0.3]`
- **row_weight**: `[4, 3]`

---

## Scalability and Frame Size Design

QKD information reconciliation efficiency increases with block size. We will scale `frame_len_symbols` from 64 to 256, 512, and 1024 symbols.
- At larger frame sizes, the 128-bit CRC verification overhead becomes negligible, and empirical information efficiency is expected to be positive:
  $$\beta_{eff\_empirical} = 1 - \frac{leak}{n \cdot h(e)} > 0$$

---

## Output Isolation

All optimization result tables will be written to `comparison_bench/outputs_comparison/real_ir_success_first/` using unique additive names:
- `ir_optimize_results.csv`
- `ir_optimize_frame_results.parquet`
- `failed_plane_diagnostics.csv`
- `optimize_run_manifest.json`
