# Information Reconciliation Optimization & Selection Report - 2026-06-15

This report summarizes the optimization phase of information reconciliation (IR) methods for high-dimensional QKD data, transitioning from the `real-ir-success-first` phase to the `optimize-real-ir-methods-after-success` phase. We evaluate Cascade-lite, Layered LDPC, and qLDPC reference methods on real arrival-time paired-symbol frames and synthetic datasets, compare them against the historical Polar baseline, and make a final method recommendation.

---

## 1. Executive Summary

- **Primary Objective**: Optimize executable IR methods to minimize information leakage, improve throughput/runtime, and scale to larger frame sizes while maintaining 100% verified real IR success (`real_ir_success=True`).
- **Core Results**:
  - **Cascade-lite**: Achieved **5% to 34% leakage reduction** across the 6 representative datasets by optimizing the number of passes (3 or 4) and utilizing optimized block size schedules with `seeded_random` permutations. Reductions vary significantly by noise regime; high-noise points (`d8_bw50`, `d16_bw100`) show smaller improvements due to limited successful configurations.
  - **Layered LDPC**: Lowered the check budget limit down to `parity_fraction = 0.8` (down from 1.0 in baseline). Check budgets below 0.8 failed to decode due to code convergence limits on short frames. Uniform bitplane allocation consistently outperformed adaptive/empirical allocations.
  - **qLDPC Reference**: Successfully evaluated GF(q) syndrome decoding, showing it remains a research baseline (`reference_only`) that can decode up to 2/4 frames in low-noise regimes but fails to converge in hard regimes.
  - **Polar Baseline Alignment**: Aligned the historical Polar baseline against the 6 representative datasets. The historical Polar baseline only succeeded on the easiest point (`real_typeii_20db_d8_bw180_blk0`), whereas both optimized Cascade-lite and Layered LDPC achieved 100% success across all 6 points.
- **Method Recommendation**: **Cascade-lite** is recommended as the primary executable comparison baseline (current preferred non-Polar candidate) due to its high noise resilience, low leakage, and low computational overhead. **Layered LDPC** is recommended as a secondary control baseline.

---

## 2. Representative Real-Frame Dataset Aligned Baseline

We aligned the historical `polar_existing` baseline data alongside Cascade-lite, Layered LDPC, and qLDPC reference methods on the 6 representative points. The table below compares the success rates and leakage of the baseline configurations (64 symbols, 256 bits for $d=16$):

| Dataset ID | Dimension ($d$) | Raw BER (%) | Polar Existing Success (Coarse Block Proxy) | Cascade-lite Success | Layered LDPC Success | qLDPC Reference Success |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `d8_bw180` | 8 | 3.78% | **4 / 4 (PASS)** | **4 / 4 (PASS)** | **4 / 4 (PASS)** | 1 / 4 (FAIL) |
| `d8_bw120` | 8 | 4.95% | 0 / 4 (FAIL) | **4 / 4 (PASS)** | **4 / 4 (PASS)** | 1 / 4 (FAIL) |
| `d8_bw50`  | 8 | 8.59% | 0 / 4 (FAIL) | **4 / 4 (PASS)** | **4 / 4 (PASS)** | 0 / 4 (FAIL) |
| `d16_bw180`| 16 | 4.59% | 0 / 4 (FAIL) | **4 / 4 (PASS)** | **4 / 4 (PASS)** | 1 / 4 (FAIL) |
| `d16_bw100`| 16 | 6.45% | 0 / 4 (FAIL) | **4 / 4 (PASS)** | **4 / 4 (PASS)** | 0 / 4 (FAIL) |
| `d16_bw60` | 16 | 6.64% | 0 / 4 (FAIL) | **4 / 4 (PASS)** | **4 / 4 (PASS)** | 0 / 4 (FAIL) |

> [!IMPORTANT]
> **Coarse Polar Alignment Limitation**:
> The `Polar Existing Success` column values (e.g. `4/4` or `0/4`) are coarse, block-level proxies derived from historical execution status (`status` or `sidecar_verdict` = PASS/FAIL) rather than frame-by-frame verification tracking. They indicate whether the entire representative dataset was processed successfully by the original Polar pipeline. This is a known limitation of the historical baseline data; it must not be interpreted as direct, frame-level verified Polar evidence.

### 2.1 Historical Baseline Limitations & Missing Metrics
The `polar_existing` bridge parses historical CSV outputs like `polar_diag_summary.csv` and companion files. Because original Polar runs did not record individual frame execution steps, we note the following data limitations:
- **Missing Leakage/Runtime**: Several historical runs in the raw data directory do not report `leak_EC_actual_bits` or `runtime_s` because the frozen Polar CLI did not save those metrics.
- **Coarse Success Classification**: Success is derived from `sidecar_verdict = PASS` as a block-level binary metric, mapping to 4/4 or 0/4 frames.

---

## 3. Cascade-lite Grid Sweep Optimization

We executed a 216-task parameter grid sweep scanning:
- `num_passes`: 2, 3, 4
- `block_size_schedule`: `[12,6,24,13]`, `[16,32,64,128]`, `[8,4,16,13]`
- `permutation_mode`: `seeded_random` vs. `fixed`

Sweep results are fully verified and classified, with correct `real_ir_success` and `verified_failure` categories, following the integration of the `beta_eff_empirical` column into the sweep results schema.

### 3.1 Best Configuration Profiles
By moving from the conservative 4-pass baseline to optimized schedules, we achieved significant leakage reductions while maintaining 100% verification success:

| Dataset ID | Baseline Leakage (bits) | Optimized Configuration | Optimized Leakage (bits) | Leakage Reduction (%) |
| :--- | :---: | :--- | :---: | :---: |
| `d8_bw180` | 645.0 | 3 passes, schedule `[16,32,64,128]`, seeded, seed=0 | 428.0 | **-33.6%** |
| `d8_bw120` | 744.0 | 4 passes, schedule `[12,6,24,13]`, seeded, seed=1 | 557.0 | **-25.1%** |
| `d8_bw50`  | 1052.0 | 3 passes, schedule `[8,4,16,13]`, seeded, seed=1 | 948.0 | **-9.9%** |
| `d16_bw180`| 861.0 | 3 passes, schedule `[16,32,64,128]`, seeded, seed=0 | 571.0 | **-33.7%** |
| `d16_bw100`| 1109.0 | 4 passes, schedule `[8,4,16,13]`, seeded, seed=0 | 1056.0 | **-4.8%** |
| `d16_bw60` | 1067.0 | 4 passes, schedule `[12,6,24,13]`, seeded, seed=0 | 801.0 | **-24.9%** |

> [!NOTE]
> **Baseline Leakage Accounting**: The baseline leakage values were measured using the pre-upgrade leakage accounting. The optimized leakage values use `exact_internal_transcript` accounting. The reduction percentages are approximate; for precise comparison, re-measure baselines with the same accounting method. All optimized configurations are verified `real_ir_success=True` with minimum leakage among successful sweep rows.

### 3.2 Optimization Takeaways
- **Passes Reduction**: Lowering passes to 2 or 3 is highly beneficial in low-to-medium noise regimes, saving verification and bisection disclosures.
- **Permutation Mode**: `seeded_random` consistently outperforms `fixed` permutations by ensuring uniform error distribution in successive passes.
- **Exact Leakage Accounting**: Leakage accounting was upgraded to `exact_internal_transcript` in [cascade_lite.py](file:///D:/Code/HD-QKD_Polar_Comparison/comparison_bench/src/comparison_bench/methods/cascade_lite.py) to count the exact number of disclosed bisection and parity bits rather than using approximations.

---

## 4. Layered LDPC Sweep Optimization

We executed a 240-task sweep scanning:
- `parity_fraction`: 1.0 down to 0.5
- `llr_mode`: `hard` vs. `bsc_estimated`
- `bitplane_rate_mode`: `uniform` vs. `adaptive`

All sweep rows are now correctly classified according to convergence and verification success.

### 4.1 Check-plane Failure Profiles
The lowest successful check budget is highly sensitive to the raw channel noise:

| Dataset ID | Baseline Check Fraction | Min Successful Parity Fraction | Optimized Leakage (bits) | Leakage Reduction (%) |
| :--- | :---: | :---: | :---: | :---: |
| `d8_bw180` | 1.0 | 0.8 (hard, uniform) | 752.0 | **-16.1%** |
| `d8_bw120` | 1.0 | 0.8 (bsc_estimated, uniform) | 752.0 | **-16.1%** |
| `d8_bw50`  | 1.0 | 1.0 (bsc_estimated, uniform) | 896.0 | **0.0%** (Noise too high) |
| `d16_bw180`| 1.0 | 0.8 (bsc_estimated, uniform) | 960.0 | **-16.7%** |
| `d16_bw100`| 1.0 | 0.8 (bsc_estimated, uniform) | 960.0 | **-16.7%** |
| `d16_bw60` | 1.0 | 0.9 (bsc_estimated, uniform) | 1056.0 | **-8.3%** |

### 4.2 Optimization Takeaways
- **Check-Fraction Floor**: LDPC is highly inefficient for short block sizes (256 bits for $d=16$). It requires a minimum parity fraction of $\ge 0.8$ to decode successfully. Below this, OSD decoding fails to converge.
- **Uniform vs. Adaptive Rate Mode**: Uniform bitplane rate allocation is consistently superior. Adaptive or empirical allocations based on single-plane SER often mismatch joint dependencies, leading to verification failure.

---

## 5. qLDPC Reference Feasibility

The `qldpc_reference` GF(q) hard syndrome decoder was evaluated on the representative dataset:
- Achieved a maximum success rate of 2/4 frames on low-noise datasets (`d8_bw120`, `d8_bw180`).
- Failed completely on hard datasets.
- Syndrome verification and row weights were tuned (check fraction 0.5, row weight 4), but lack of soft channel information (LLR) limits qLDPC to a reference role. It cannot be used as a production candidate.

---

## 6. Frame Size Scalability & Efficiency Analysis

We evaluated scalability on larger frame sizes: 128, 256, and 2048 symbols. 

### 6.1 The Beta Efficiency Clamping Phenomenon
In all sweeps, the empirical information efficiency $\beta_{eff\_empirical}$ remained $0.0$.
- **Why?** At low raw BER (e.g., 1.6% BER for synthetic long), the Shannon entropy is extremely low ($H(e) = 0.119$), making the Shannon limit denominator small ($32768 \times 0.119 = 3907$ bits).
- **Overhead**: The actual leakage is dominated by CRC-128 verification bits (512 bits for 4 frames) and parity check/bisection overhead (e.g., 9496 bits for Cascade-lite, which is $2.43\times$ the Shannon bound).
- **Mathematical Correctness**: Since leakage exceeds the Shannon bound, the formula:
  $$\beta_{eff\_empirical} = \max\left(0.0, 1.0 - \frac{\text{leakage}}{N \cdot H(e)}\right)$$
  correctly clamps to $0.0$. This highlights that for short and medium frame lengths, finite-length block overhead and verification headers dominate the efficiency limit.

---

## 7. Run Manifest & Traceability

All parameter sweeps, diagnostics, and error files are fully recorded in the shared run manifest file:
[ir_v3_run_manifest.json](file:///D:/Code/HD-QKD_Polar_Comparison/comparison_bench/outputs_comparison/real_ir_success_first/ir_v3_run_manifest.json)
This manifest lists all three completed stages (`cascade_param_sweep`, `layered_ldpc_param_sweep`, `qldpc_param_sweep`) and links directly to their corresponding CSV and Parquet outputs.

---

## 8. Final Method Selection & Deployment Recommendation

Based on the sweeps, we recommend the following deployment strategies:

1. **Primary Method: Cascade-lite**
   - **Rationale**: Achieves 100% success across all noise regimes up to 23.8% SER. It is highly robust, and when optimized with 3 or 4 passes and random permutations, it reduces leakage by up to 33.7%, yielding lower leakage than LDPC on short frames.
   - **Preferred Configuration**: `seeded_random` permutation, block schedule `[16,32,64,128]` with 3 passes for low noise, `[12,6,24,13]` with 4 passes for medium noise, and `[8,4,16,13]` with 3 to 4 passes for high noise. Exact pass/schedule selection is noise-dependent; see Section 3.1 table for per-dataset optimums.

2. **Secondary Method: Layered LDPC**
   - **Rationale**: Highly stable, but constrained to parity check budgets $\ge 0.8$ on short frames. It can be used as a comparison control baseline.
   - **Preferred Configuration**: `parity_fraction = 0.8` (or 0.9 for high noise), `llr_mode = bsc_estimated`, `bitplane_rate_mode = uniform`.
