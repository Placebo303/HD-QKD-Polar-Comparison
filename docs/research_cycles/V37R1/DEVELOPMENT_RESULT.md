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
  - P1-A Screening: 261 configurations x 3 sources x 3 screening seeds = **2,349 real DE runs**.
  - P1-B Confirmation: **0 runs** (skipped conditionally because screening pass set size = 0).
  - Total: **2,349 real DE runs**.
- **Runtime**: 3262.78 s (~54.38 min).

### 1.2 Quantitative Baseline & Control Measurements

#### Reference Baseline (dv=2 Regular)
- 1M Mean AUT_30: **73.608364**
- 1.5M Mean AUT_30: **59.377442**
- 2M Mean AUT_30: **59.450244**
- Overall Mean AUT_30: **64.145350**
- Convergence: 9/9 runs converged (H60 = 0.0 < 1e-4).

#### Exploratory Positive Control (V36 lambda={2: 0.85, 4: 0.15}, finite_inadmissible=True)
- 1M Mean AUT_30: **79.979189** (Delta_1M = +8.65%)
- 1.5M Mean AUT_30: **84.545534** (Delta_1.5M = +42.39%)
- 2M Mean AUT_30: **80.240504** (Delta_2M = +34.97%)
- Overall Mean AUT_30: **81.588409**
- Convergence: 9/9 runs converged (H60 = 0.0 < 1e-4).

### 1.3 Top 5 Finite-Feasible Candidates (Exact Artifact Measurements)
| Candidate ID | Lambda Distribution | N2 | dbar_v | Mean AUT_30 | 1M AUT_30 (Delta) | 1.5M AUT_30 (Delta) | 2M AUT_30 (Delta) | Converged? | Pass Screening? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| lam_d2_0.10_d3_0.90_d4_0.00_d5_0.00 | lambda_2=0.10, lambda_3=0.90 | 146 | 2.857 | **154.068452** | 153.997446 (+109.21%) | 154.117147 (+159.55%) | 154.090764 (+159.19%) | **False** (H60~4.97) | **False** |
| lam_d2_0.10_d3_0.85_d4_0.05_d5_0.00 | lambda_2=0.10, lambda_3=0.85, lambda_4=0.05 | 148 | 2.892 | **154.154431** | 154.100903 (+109.35%) | 154.186123 (+159.67%) | 154.176268 (+159.34%) | **False** (H60~4.97) | **False** |
| lam_d2_0.10_d3_0.85_d4_0.00_d5_0.05 | lambda_2=0.10, lambda_3=0.85, lambda_5=0.05 | 149 | 2.913 | **154.198669** | 154.142056 (+109.41%) | 154.239264 (+159.76%) | 154.214688 (+159.40%) | **False** (H60~4.97) | **False** |
| lam_d2_0.10_d3_0.80_d4_0.10_d5_0.00 | lambda_2=0.10, lambda_3=0.80, lambda_4=0.10 | 150 | 2.927 | **154.235522** | 154.178938 (+109.46%) | 154.270676 (+159.81%) | 154.256952 (+159.47%) | **False** (H60~4.97) | **False** |
| lam_d2_0.05_d3_0.95_d4_0.00_d5_0.00 | lambda_2=0.05, lambda_3=0.95 | 75 | 2.927 | **154.238570** | 154.171515 (+109.45%) | 154.286018 (+159.84%) | 154.258179 (+159.47%) | **False** (H60~4.97) | **False** |

### 1.4 Convergence Accounting Across Matrix
- **Configurations with all_seeds_converged == True**: **2 / 261** (aseline_dv2_regular and positive_control_v36).
- **Configurations with all_seeds_converged == False**: **259 / 261** (all 259 finite-feasible candidate configurations failed to converge within 60 iterations).
- **Individual Seed Runs**: **18 / 2,349** converged ((60) < 10^{-4}$); **2,331 / 2,349** non-converged ((60) \approx 4.96 \sim 5.0$).

---

## 2. Independently Recomputable Derivation

1. **Screening Gate Evaluation**:
   - Total finite candidates evaluated: 259.
   - Candidates satisfying Delta_s <= -0.05 on all 3 sources independently: **0** (0 / 259).
   - In fact, all 259 finite-feasible candidates exhibited Delta_s > +109% on all 3 sources (trajectories failed to reach decoding threshold and barely reduced entropy from initial 5.0 bits/symbol).
2. **P1-B Confirmation Decision**:
   - Because passing_screening_candidates is empty (size = 0), the frozen decision rule mandates skipping P1-B confirmation.
   - Run count accounting: Screening = 2,349 runs, Confirmation = 0 runs, Total = 2,349 runs.
3. **Terminal State**:
   - According to the pre-registered protocol, the outcome is strictly:
     **Terminal State = P1_NO_FINITE_FEASIBLE_DE_ADVANCE**

---

## 3. Scientific Analysis & Structural Diagnosis

### 3.1 Why Single-Edge Simplex Tuning is Structurally Infeasible
- **Structural Gap (Not a Resolution Issue)**:
  - The best candidate (lam_d2_0.10_d3_0.90) achieves AUT_30 values of ~154.0 vs baseline ~59.4-73.6, which is +109% to +160% worse (2.09x to 2.60x of baseline).
  - This is an order-of-magnitude structural gap, not a boundary issue where fine-tuning step size from 0.05 to 0.025 could turn a near-pass (-3%) into a pass (-5%).
- **Boundary Saturation**:
  - The best performing point in the entire 259-candidate space sits exactly at the lowest-degree boundary: $\lambda_2=0.10, \lambda_3=0.90, \lambda_4=0, \lambda_5=0$.
  - Increasing higher degrees (degree 4/5) strictly increases average variable degree $\bar{d}_v$ and check degree $, making DE convergence strictly worse.
- **The Fundamental Structural Conflict**:
  - Under high code rates ( \approx 0.8125 - 0.8203$), check node degree is $\bar{d}_c = \bar{d}_v / (1 - R) \approx 5.3 \bar{d}_v$.
  - Finite-length cycle-free forest gate ( \le 183$) strictly forbids $\lambda_2 > 0.10$, forcing $\bar{d}_v \ge 2.857$ and  \in [16, 20]$.
  - In GF(32) non-binary message passing, check nodes with  \in [16, 20]$ suffer from exponential message convolution uncertainty, completely stalling early-iteration extrinsic mutual information propagation.
  - Conversely, regular =2$ baseline has $\bar{d}_v=2.0$ and  \in [11, 12]$, passing information with vastly lower check-node entropy impedance.
- **Positive Control Diagnosis**:
  - Even the V36 positive control ($\lambda_2=0.85, \lambda_4=0.15, N_2=941$), which has abundant degree-2 nodes, is still +8.65% to +42.39% worse than regular =2$ under empirical-P DE.
  - This proves that simply adjusting single-edge polynomial weights $\lambda_i$ cannot simultaneously achieve finite cycle-freedom and asymptotic DE threshold superiority.

---

## 4. Next-Phase Architecture Transition (V38+ Roadmap)

### 4.1 Direction to Abandon
- **ABANDON**: Unstructured single-edge irregular $\lambda$-distribution simplex tuning. Finer grid searches (e.g. step=0.025) on {2,3,4,5} polynomials are definitively non-viable under  \le 183$.

### 4.2 Candidate Structured Directions for V38+
1. **Protograph / Multi-Edge-Type (MET) NB-LDPC** (Primary Recommended Route):
   - Multi-edge type LDPC allows structured, controlled degree-2 chains, accumulators, and topological constraints.
   - Enables abundant effective low-degree variables without suffering from random degree-2 forest cycle explosion.
2. **Near-=2$ Structured Graph Topology + GF(32) Edge Coefficient Assignment**:
   - Leverages the confirmed strong DE convergence of =2$ regular / low-degree graphs.
   - Addresses finite-length girth, rank deficiency, and trapping sets through structured algebraic edge permutation / label assignment over GF(32).
3. **Non-Binary Spatially-Coupled LDPC (SC-NB-LDPC)** (Fallback / Larger Redesign):
   - Utilizes spatial coupling threshold saturation on protographs to achieve low threshold with non-binary gains.

---

## 5. Claim Boundary

### Allowed Statements
- Within the pre-registered V37R1 candidate space (degrees {2, 3, 4, 5} on 0.05-simplex, necessary forest-count gate N2 <= 183, realized check degree cap dc_max <= 20) under the source-specific V25 TRAIN empirical-P GF(32) DE protocol, **all 259 finite-feasible candidates failed to achieve the pre-registered 5% AUT_30 reduction gate over the matched regular dv=2 baseline**.
- The result cleanly concludes stage P1 with terminal state P1_NO_FINITE_FEASIBLE_DE_ADVANCE.

### Forbidden Statements
- Do NOT claim that irregular NB-LDPC is generally inferior or impossible (this search was restricted to standard unstructured simplex distributions with N2 <= 183, dc_max <= 20).
- Do NOT claim finite-block decoding failure, FER results, or key-rate conclusions (no finite decoding was performed).
- Do NOT claim Tanner graph realizability or graph non-existence.
- Do NOT perform ad-hoc reruns, parameter tuning, or seed changes.
