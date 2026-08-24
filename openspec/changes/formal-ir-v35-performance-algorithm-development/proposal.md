# OpenSpec Proposal: formal-ir-v35-performance-algorithm-development (V35R1 Corrected)

**Status**: POST_RUN_REVIEWED / PROTOCOL_PARTIAL_A4_NOT_EXECUTED / SCIENTIFIC_PROMOTION_NOT_GRANTED  
**Domain**: Formal Information Reconciliation (IR) / Nonbinary & Binary Error Correction  
**Change ID**: `formal-ir-v35-performance-algorithm-development`  
**Working Directory**: `comparison_bench/src/comparison_bench/formal_ir/`  
**Output Root**: `comparison_bench/outputs_comparison/nonbinary_diagnostics/v35_algorithm_development/run_02/`  

---

## 1. Why

Prior finite-control diagnostics (V34) established that matching the channel empirical joint distribution $P(A, B)$ on the fixed V31 quasi-cyclic baseline graph ($d_v=2$, $N=1024$) with standard flooding FFT-QSPA yields 0/20 frame recovery across all three HD-QKD noise regimes (1M, 1.5M, 2M), with post-decoding symbol error counts stalling around 168–181 errors per block.

V35 investigates progressive error correction on empirical HD-QKD data across three core nonbinary stages:
1. **Stage A1 (Decoder Schedules on TRUE Baseline)**: Evaluate Flooding, Row-Layered, and Damped Row-Layered ($\alpha=0.5$) FFT-QSPA on the true frozen V31 baseline matrices ($d_v=2$, $N=1024$, $M=184/190/192$).
2. **Stage A2 (Hand-Designed Mixed-Degree Protograph)**: Design variable-degree protographs ($d_v \in [2, 5]$, average degree $\bar{d}_v = 3.09375 \in [2.2, 3.2]$, fraction of degree-2 edges $\lambda_2 = 0.0808 \le 0.35$, zero degree-1 variable nodes, strictly **zero degree-2 cycles**) deterministically lifted ($Z=32$) to eliminate 4-cycles and achieve full GF(32) row rank (192).
3. **Stage A3 (Rate-Adaptive Incremental Syndrome Hierarchy with Clean Cold-Starts)**: Construct nested parity-check rows ($S0: +0\text{b}, S1: +40\text{b}, S2: +80\text{b}, S3: +160\text{b}$) evaluated independently from fresh channel priors to avoid message double-counting artifacts.
4. **Stage A4 (Binary Multilevel Coding Fallback)**: Required by the frozen progression rule after A3 failed, but not executed in `run_02`. The retained run is therefore an A1--A3 partial protocol result, not a completed four-stage terminal result.

---

## 2. Bindings & Development Matrix

- **Empirical Channel Distribution**: V25 joint count arrays $N_{ab}$ loaded from `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz`.
- **Baseline QC Matrices**: Loaded from `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/matrix_payloads.json` (packet `m1_16_n1024_n1024|QC-cyclic-projective`).
- **Development Seed Matrix (15 Blocks)**:
  - `1M`: `350101`, `350102`, `350103`, `350104`, `350105`
  - `1p5M`: `350201`, `350202`, `350203`, `350204`, `350205`
  - `2M`: `350301`, `350302`, `350303`, `350304`, `350305`
- **Field & Factorization**: $\text{GF}(32) = \text{GF}(2^5)$ with primitive polynomial $p(x) = x^5 + x^2 + 1$ (37), natural MSB-to-LSB split ($U_1 = \text{Alice} \gg 5 \in [0, 32)$, $U_2 = \text{Alice} \& 31 \in [0, 32)$).
- **Verification Tag**: 64-bit SHA-256 tag.
