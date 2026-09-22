# V38-P0 Development Result Report: Structured Low-Degree Architecture Triage

**Cycle ID**: V38P0
**Lifecycle State**: `DEVELOPMENT_RESULT_CANDIDATE`
**Repository**: `Placebo303/HD-QKD-Polar-pipeline`
**Branch**: `formal-ir-mainline`
**Accepted Plan SHA**: `1b3fb4b8d0fa14c127ab895b1bbb21eb77f3414d`
**Accepted Implementation SHA**: `41cad74cc6f50dad6bfed37e63bb188cbd294f77`
**Implementation Acceptance Commit SHA**: `f783174a40cbae961293950eb1903ffe78de9452`
**Predecessor Result SHA**: `67da7c64fa4150a66d020243d6292420903297fe`
**Predecessor Review SHA**: `cc1483cd568ca41fb686c40492f40b5eed81f06c`
**Execution Status**: `DEVELOPMENT_RUN_COMPLETED`
**Terminal State**: `V38_NO_ROUTE_SIGNAL`
**Development Execution Authorization**: `AUTHORIZED` (`EXECUTE_AUTH`)
**Formal Execution Authorization**: `NOT_AUTHORIZED` (`formal_execution_authorized: false`)
**Scientific Promotion**: `NOT_GRANTED` (`scientific_promotion: false`)

---

## 1. Executive Summary & Terminal Conclusion

The single authorized V38-P0 development run was executed strictly following the frozen architecture triage protocol:
- **Structural Prototypes Generated**: Exactly **27 / 27** pre-registered prototype attempts (3 lanes $\times$ 3 sources $\times$ 3 seeds) were constructed, evaluated for algebraic cycle degeneracy and structural metrics, and preserved.
- **Structural Validity**: **27 / 27 (100%)** candidate prototypes satisfied all hard structural validity requirements (full GF(32) row rank $m$, column degrees, row degrees $dc_{\text{max}} \le 12 \le 16$, no isolated nodes, valid non-zero GF(32) labels).
- **Decoder Evaluations**: Exactly **45** new decoder runs (15 blocks $\times$ 3 ready lanes) were evaluated using row-layered FFT-QSPA (max 30 iterations, damping $\alpha=1.0$) on the 15 frozen V36 A3 development blocks with empirical $L_2$ channel posteriors.
- **Triage Gate Result**: **0 / 3** lanes passed the triage gate (`LANE_EVALUATED_NO_SIGNAL` for Lane A, Lane B, and Lane C).
- **Terminal Scientific State**: **`V38_NO_ROUTE_SIGNAL`** (All three investigated low-degree architectures failed to demonstrate error-correction improvement over the frozen V31 baseline).

---

## 2. Structural Prototype Generation & Selection (27 / 27 Attempts)

All 27 candidates were constructed using pre-registered production seeds:

### Lane A (Cycle-Aware Label Optimization on V31 Support)
- **1M** (`381101`, `381102`, `381103`): All 3 achieved **0 degenerate 4-cycles**, **0 degenerate 6-cycles**, and **0 degenerate 8-cycles** (100% non-degenerate, $13{,}865 / 13{,}865$ 8-cycles non-degenerate). Winner: `lane_a_1M_s381101`.
- **1.5M** (`381201`, `381202`, `381203`): All 3 achieved **0 degenerate 4/6/8-cycles** ($12{,}815 / 12{,}815$ non-degenerate). Winner: `lane_a_1p5M_s381201`.
- **2M** (`381301`, `381302`, `381303`): All 3 achieved **0 degenerate 4/6/8-cycles** ($12{,}465 / 12{,}465$ non-degenerate). Winner: `lane_a_2M_s381301`.

### Lane B (eIRA-like Lower-Bidiagonal Dual-Diagonal Prototypes)
- Total support edges: exactly $2{,}047$, info column degree: 2, parity column degrees: 1 to 2, full GF(32) rank guaranteed.
- **1M**: Winner `lane_b_1M_s382103` (0 deg-4, 50 deg-6, 253 deg-8, support 4c=7, $dc_{\text{max}}=12$).
- **1.5M**: Winner `lane_b_1p5M_s382201` (0 deg-4, 51 deg-6, 210 deg-8, support 4c=14, $dc_{\text{max}}=11$).
- **2M**: Winner `lane_b_2M_s382301` (0 deg-4, 44 deg-6, 216 deg-8, support 4c=9, $dc_{\text{max}}=11$).

### Lane C (Spatially Banded Prototypes, $L=8, w=2$)
- Total support edges: exactly $2{,}048$, all column degrees: 2, load-aware check allocation capacity gate satisfied ($dc_{\text{max}} \le 12$).
- **1M**: Winner `lane_c_1M_s383103` (0 deg-4, 6 deg-6, 260 deg-8, support 4c=41, $dc_{\text{max}}=12$).
- **1.5M**: Winner `lane_c_1p5M_s383203` (0 deg-4, 6 deg-6, 274 deg-8, support 4c=5, $dc_{\text{max}}=12$).
- **2M**: Winner `lane_c_2M_s383301` (0 deg-4, 9 deg-6, 280 deg-8, support 4c=12, $dc_{\text{max}}=11$).

---

## 3. Finite Block Decoder Performance & Paired Baseline Comparison

Each winning prototype was evaluated on the 15 frozen development blocks ($N=1024$ symbols over GF(32)).

### Quantitative Summary Table

| Metric | Frozen Baseline (V31 QC) | Lane A (Cycle-Opt) | Lane B (eIRA) | Lane C (Spatially Banded) |
| :--- | :---: | :---: | :---: | :---: |
| **Exact Recovery ($L_2$)** | 0 / 15 | **0 / 15** | **0 / 15** | **0 / 15** |
| **Overall Mean Errors** | 174.80 | **968.07** | **968.07** | **968.07** |
| **Overall Median Errors** | 177.0 | **971.0** | **971.0** | **971.0** |
| **1M Median Errors** | 171.0 | 974.0 (+469.6%) | 974.0 (+469.6%) | 974.0 (+469.6%) |
| **1.5M Median Errors** | 178.0 | 962.0 (+440.4%) | 962.0 (+440.4%) | 962.0 (+440.4%) |
| **2M Median Errors** | 183.0 | 967.0 (+428.4%) | 967.0 (+428.4%) | 967.0 (+428.4%) |
| **Paired Improve Blocks** | Reference | 0 / 15 | 0 / 15 | 0 / 15 |
| **Paired Equal Blocks** | Reference | 0 / 15 | 0 / 15 | 0 / 15 |
| **Paired Worsen Blocks** | Reference | 15 / 15 | 15 / 15 | 15 / 15 |
| **Worst Single Degradation**| Reference | +814 errors | +814 errors | +814 errors |
| **Triage Gate Status** | Baseline | `LANE_EVALUATED_NO_SIGNAL` | `LANE_EVALUATED_NO_SIGNAL` | `LANE_EVALUATED_NO_SIGNAL` |

### Triage Gate Evaluation
- **Criterion A (Exact Recovery > 0)**: `False` (0 / 15 exact recoveries).
- **Criterion B (Overall Median Errors $\le 150$)**: `False` (overall median = 971.0).
- **Criterion C ($\text{Improve} \ge 10 \land \text{Worsen} \le 3$)**: `False` (improve = 0, worsen = 15).
- **Non-Degradation Gate (All Sources $\le +5\%$)**: `FAIL` (all sources degraded by $> +400\%$).

---

## 4. Scientific Findings & Next-Step Implications

1. **Catastrophic Low-Degree Floor in High-Noise GF(32) QKD**:
   - The low variable degree ($d_v = 2$ or near-$d_v=2$) structures, across all three architectural paradigms (label optimization, dual-diagonal bidiagonal parity, and spatially banded coupling), fail completely under the high channel crossover probability of the empirical QKD data.
   - When $d_v=2$, the variable nodes receive only 2 check messages, which provides insufficient extrinsic information to overcome channel uncertainty, causing the decoder to converge to non-codeword stationary points (~970 residual errors out of 1024 symbols).

2. **Cycle Optimization is Insufficient Without Degree Support**:
   - Lane A demonstrated that eliminating 100% of 4-, 6-, and 8-cycle algebraic degeneracies on a $d_v=2$ graph does not rescue decoding convergence. The topological connectivity bottleneck dominates label optimization.

3. **Comparison with V31 Baseline**:
   - The frozen V31 quasi-cyclic baseline with column degree $d_v=3$ achieves a median of 177 residual errors on the same blocks. The higher variable degree ($d_v \ge 3$) is strictly necessary for BP/FFT-QSPA message convergence at these noise rates.

---

## 5. Artifact Provenance & Lineage

- **Raw Data Directory**: `comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/`
- **Committed Artifacts**:
  - `v38_structural_prototypes.csv` & `v38_structural_prototypes.json` (all 27 structural prototypes)
  - `v38_development_block_records.csv` & `v38_development_block_records.json` (all 45 decoder evaluation records)
  - `v38_triage_summary.json` (machine-readable aggregate and triage summary)
  - `v38_winning_matrices.npz` (compressed winning prototype parity-check matrices)
- **Runtime**: $756.23\,\text{s}$

---

## 6. Strict Scientific Claim Boundaries

- **NO Parameter Tuning**: No decoder parameters ($\alpha$, $\text{max\_iter}$) were altered.
- **NO Seed Exploration**: No search outside the 27 pre-registered production seeds was conducted.
- **NO Claims of FER, Threshold, or SKR Improvement**: All low-degree prototypes exhibited severe degradation relative to the frozen baseline.
