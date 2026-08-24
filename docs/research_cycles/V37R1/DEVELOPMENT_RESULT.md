# Development Result: Cycle V37R1 (P1 Empirical-P DE Screening)

**Cycle ID**: V37R1  
**Lifecycle State**: DEVELOPMENT_RESULT_REVIEW_PENDING  
**Repository**: Placebo303/HD-QKD-Polar-pipeline  
**Branch**: ormal-ir-mainline  
**Accepted Plan SHA**: 661e2878f96f9fb84291bd601ebd3eb6abfcfdd4  
**Accepted Implementation SHA**: 3a64d1e9ad11625f3eee1fa6cafb5d75c7eaca39  
**Development Authorization SHA**: ff235f240c4a88396fda4e20275cf2bb1856432  
**Terminal State**: P1_NO_FINITE_FEASIBLE_DE_ADVANCE  
**Output Directory**: comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v37_p1_de_20260825/run_01  

---

## 1. Direct Evidence

### 1.1 Execution Accounting & Parameters
- **Field**: GF(32), primitive polynomial 37 (0b100101).
- **Block Reference**: n = 1024 symbols.
- **DE Sample Size**: N_mc = 4000, I_max = 60 iterations.
- **Convergence Threshold**: H(60) < 1e-4 bits/symbol.
- **Effect-Size Gate**: Delta_s <= -0.05 (at least 5% reduction in AUT_30 relative to matched baseline) on each source independently.
- **Source Rates & Check Numbers**:
  - 1M: m = 184 -> R = 1 - 184/1024 = 0.8203125
  - 1.5M: m = 190 -> R = 1 - 190/1024 = 0.814453125
  - 2M: m = 192 -> R = 1 - 192/1024 = 0.8125000
- **Candidate Universe**:
  - Raw 0.05-simplex over degrees {2, 3, 4, 5}: 1,771 candidates.
  - P0 necessary forest-count feasibility (N2 <= 183): 547 candidates.
  - Check degree cap (realized max_dc <= 20 for all 3 sources): 259 candidates.
  - Controls: 1 matched regular dv=2 baseline + 1 V36 exploratory positive control (N2=941, finite_inadmissible=True).
  - Total evaluated configurations: 261 configurations.
- **Real DE Runs Executed**:
  - P1-A Screening: 261 configurations x 3 sources x 3 screening seeds = 2,349 real DE runs.
  - P1-B Confirmation: 0 runs (skipped conditionally because screening pass set size = 0).
  - Total: 2,349 real DE runs.
- **Runtime**: 3262.78 s (~54.38 min).

### 1.2 Quantitative Baseline & Top Candidate Measurements

#### Reference Baseline (dv=2 Regular)
- 1M Mean AUT_30: **73.608364**
- 1.5M Mean AUT_30: **59.377442**
- 2M Mean AUT_30: **59.450244**
- Overall Mean AUT_30: **64.145350**
- Convergence: 9/9 runs converged (H60 < 1e-4).

#### Exploratory Positive Control (V36 lambda={2: 0.85, 4: 0.15}, finite_inadmissible=True)
- 1M Mean AUT_30: **79.979189** (Delta_1M = +8.65%)
- 1.5M Mean AUT_30: **84.545534** (Delta_1.5M = +42.39%)
- 2M Mean AUT_30: **80.240504** (Delta_2M = +34.97%)
- Overall Mean AUT_30: **81.588409**

#### Top 5 Finite-Feasible Candidates (Ranked by Overall Mean AUT_30)
| Candidate ID | Lambda Distribution | N2 | dbar_v | Mean AUT_30 | Delta_1M | Delta_1.5M | Delta_2M | Pass Screening? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| lam_d2_0.10_d3_0.90_d4_0.00_d5_0.00 | lambda_2=0.10, lambda_3=0.90 | 146 | 2.857 | 154.5330 | +110.57% | +160.22% | +159.19% | **False** |
| lam_d2_0.10_d3_0.85_d4_0.05_d5_0.00 | lambda_2=0.10, lambda_3=0.85, lambda_4=0.05 | 148 | 2.899 | 154.6186 | +110.66% | +160.37% | +159.34% | **False** |
| lam_d2_0.10_d3_0.85_d4_0.00_d5_0.05 | lambda_2=0.10, lambda_3=0.85, lambda_5=0.05 | 149 | 2.927 | 154.6568 | +110.69% | +160.44% | +159.40% | **False** |
| lam_d2_0.10_d3_0.80_d4_0.10_d5_0.00 | lambda_2=0.10, lambda_3=0.80, lambda_4=0.10 | 150 | 2.941 | 154.6997 | +110.74% | +160.52% | +159.47% | **False** |
| lam_d2_0.05_d3_0.95_d4_0.00_d5_0.00 | lambda_2=0.05, lambda_3=0.95 | 75 | 2.927 | 154.7042 | +110.74% | +160.52% | +159.47% | **False** |

---

## 2. Independently Recomputable Derivation

1. **Screening Gate Evaluation**:
   - Total finite candidates evaluated: 259.
   - Candidates satisfying Delta_s <= -0.05 on all 3 sources independently: **0** (0 / 259).
   - In fact, all 259 finite-feasible candidates exhibited Delta_s > 0 on all 3 sources (trajectories decreased entropy significantly more slowly than the dv=2 regular baseline).
2. **P1-B Confirmation Decision**:
   - Because passing_screening_candidates is empty (size = 0), the frozen decision rule mandates skipping P1-B confirmation.
   - Run count accounting: Screening = 2,349 runs, Confirmation = 0 runs, Total = 2,349 runs.
3. **Terminal State**:
   - According to the pre-registered protocol, the outcome is strictly:
     **Terminal State = P1_NO_FINITE_FEASIBLE_DE_ADVANCE**

---

## 3. Scientific Interpretation

- **Mechanism of Slow Early Convergence in High-Rate Finite Irregular NB-LDPC**:
  - For high code rates (R in [0.8125, 0.8203]), the average check degree is dbar_c = dbar_v / (1 - R).
  - When N2 <= 183 is enforced (limiting lambda_2 <= 0.10), the average variable degree is constrained to dbar_v in [2.8571, 5.0000].
  - Consequently, check node degrees are elevated to dc in [16, 20]. In GF(32) non-binary sum-product check-node update convolutions over dc in [16, 20], incoming message uncertainties compound heavily, retarding early-iteration extrinsic mutual information propagation.
  - In contrast, the regular dv=2 baseline has dbar_v = 2.0, yielding much lower check degrees (dc in [11, 12]) and significantly faster early-iteration entropy reduction (lower AUT_30).
- **V36 Positive Control Behavior**:
  - The V36 distribution (lambda_2=0.85, lambda_4=0.15) has dbar_v = 2.162 and dbar_c in [12, 13], but its N2 = 941 >> 183 makes it structurally cycle-heavy in finite length n=1024, m in {184, 190, 192}. Under empirical-P DE, it also exhibits higher AUT_30 than regular dv=2 across all sources.

---

## 4. Claim Boundary

### Allowed Statements
- Within the pre-registered V37R1 candidate space (degrees {2, 3, 4, 5} on 0.05-simplex, necessary forest-count gate N2 <= 183, realized check degree cap dc_max <= 20) under the source-specific V25 TRAIN empirical-P GF(32) DE protocol, **no candidate achieved the pre-registered 5% AUT_30 reduction gate over the matched regular dv=2 baseline**.
- The result cleanly concludes stage P1 with terminal state P1_NO_FINITE_FEASIBLE_DE_ADVANCE.

### Forbidden Statements
- Do NOT claim that irregular NB-LDPC is generally inferior or impossible (this search was restricted to standard unstructured simplex distributions with N2 <= 183, dc_max <= 20).
- Do NOT claim finite-block decoding failure, FER results, or key-rate conclusions (no finite decoding was performed).
- Do NOT claim Tanner graph realizability or graph non-existence.
- Do NOT perform ad-hoc reruns, parameter tuning, or seed changes.
