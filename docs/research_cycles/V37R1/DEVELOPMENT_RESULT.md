# Development Result: Cycle V37R1 (P1 Empirical-P DE Screening)

## 1. Provenance
- **Cycle ID**: V37R1
- **Lifecycle State**: DEVELOPMENT_RESULT_REVIEW_PENDING (Review Status = REVISE -> Corrected Audit Commit)
- **Repository**: Placebo303/HD-QKD-Polar-pipeline
- **Branch**: ormal-ir-mainline
- **Accepted Plan SHA**: 661e2878f96f9fb84291bd601ebd3eb6abfcfdd4
- **Accepted Implementation SHA**: 3a64d1e9ad11625f3eee1fa6cafb5d75c7eaca39
- **Development Authorization SHA**: ff235f240c4a88396fda4e20275cf2bb1856432
- **Output Directory**: comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v37_p1_de_20260825/run_01

---

## 2. Frozen Protocol
- **Field**: GF(32), primitive polynomial 37 (0b100101).
- **Block Reference**: n = 1024 symbols.
- **DE Parameters**: N_mc = 4000 samples, I_max = 60 iterations.
- **Convergence Criterion**: H(60) < 1e-4 bits/symbol.
- **Development Effect-Size Gate**: Delta_s <= -0.05 (at least 5% reduction in AUT_30 relative to matched baseline) on each source independently.
- **Source Rates & Check Numbers**:
  - 1M: m = 184 -> R = 1 - 184/1024 = 0.8203125
  - 1.5M: m = 190 -> R = 1 - 190/1024 = 0.814453125
  - 2M: m = 192 -> R = 1 - 192/1024 = 0.8125000
- **Candidate Search Space**:
  - Raw 0.05-simplex over degrees {2, 3, 4, 5}: 1,771 distributions.
  - P0 necessary forest-count gate (N2 <= 183): 547 distributions.
  - Check realizability cap (realized max_dc <= 20 across all 3 sources): 259 distributions.
  - Total evaluated configurations: 261 (259 finite candidates + 1 regular dv=2 baseline + 1 V36 positive control).
- **Seed Architecture**:
  - Screening seeds: 1M: (370101, 370102, 370103); 1.5M: (370201, 370202, 370203); 2M: (370301, 370302, 370303).
  - Confirmation seeds (disjoint): 1M: (370111, 370112, 370113); 1.5M: (370211, 370212, 370213); 2M: (370311, 370312, 370313).

---

## 3. Direct Evidence

### 3.1 Candidate & Run Accounting
- **Candidate Summary CSV Physical Lines**: 262 (1 header line + 261 data rows).
- **Candidate Summary Data Rows**: 261.
- **Unique Candidate IDs**: 261.
- **Trajectory CSV Runs**: 2,349 unique (stage, source, candidate_id, seed) runs.
- **Screening Runs**: 2,349 (261 configs x 3 sources x 3 seeds).
- **Confirmation Runs**: 0 (skipped conditionally; pass set size = 0).
- **Total Real DE Runs Executed**: 2,349.
- **Total Wallclock Runtime**: 3262.78 s (~54.38 min).

### 3.2 Matched Reference Baseline (dv=2 Regular)
- **Candidate ID**: aseline_dv2_regular (lambda = {2: 1.0}, N2=1024, dbar_v=2.000).
- **1M Mean AUT_30**: **73.608364** (seed AUT_30 values: 73.608364, 73.608364, 73.608364).
- **1.5M Mean AUT_30**: **59.377442** (seed AUT_30 values: 59.377442, 59.377442, 59.377442).
- **2M Mean AUT_30**: **59.450244** (seed AUT_30 values: 59.450244, 59.450244, 59.450244).
- **Overall Mean AUT_30**: **64.145350**.
- **Convergence**: **9 / 9** runs converged ((60) = 0.0 < 10^{-4}$).

### 3.3 Exploratory Positive Control (V36 lambda={2: 0.85, 4: 0.15})
- **Candidate ID**: positive_control_v36 (N2=941, finite_inadmissible=True, non-promotable reference).
- **1M Mean AUT_30**: **79.979189** (Delta_1M = **+8.65%** relative to baseline).
- **1.5M Mean AUT_30**: **84.545534** (Delta_1.5M = **+42.39%** relative to baseline).
- **2M Mean AUT_30**: **80.240504** (Delta_2M = **+34.97%** relative to baseline).
- **Overall Mean AUT_30**: **81.588409**.
- **Convergence**: **9 / 9** runs converged ((60) = 0.0 < 10^{-4}$).

### 3.4 Finite Candidate Convergence Audit
- **Total Finite Candidate Runs**: 259 configs x 3 sources x 3 seeds = **2,331 runs**.
- **Converged Finite Runs ((60) < 10^{-4}$)**: **0 / 2,331** (0.0%).
- **Non-Converged Finite Runs ((60) \ge 10^{-4}$)**: **2,331 / 2,331** (100.0%).
- **Candidate-Level Convergence Breakdown**:
  - Candidates with ALL 9 runs converged: **0 / 259**.
  - Candidates with at least 1 non-converged run: **259 / 259**.
  - Candidates with 0 converged runs: **259 / 259**.
- **Source-Level Breakdown**:
  - 1M: 0 / 777 converged (777 non-converged).
  - 1.5M: 0 / 777 converged (777 non-converged).
  - 2M: 0 / 777 converged (777 non-converged).
- *Observation*: For all 259 finite-feasible candidates, entropy at iteration 60 remained near .96 \sim 5.0$ bits/symbol (asymptotic decoding threshold was not reached under empirical noise levels).

### 3.5 Lowest-AUT_30 Finite Candidates
- **Lowest-AUT_30 Finite Candidate Among All 259**: lam_d2_0.10_d3_0.90_d4_0.00_d5_0.00 (did not satisfy convergence gate; all_seeds_converged = False).
- **Lowest-AUT_30 Fully Converged Finite Candidate**: **NONE** (0 finite candidates converged).

#### Top 10 Finite Candidates Ranked by Overall Mean AUT_30
| Rank | Candidate ID | $\lambda_2$ | $\lambda_3$ | $\lambda_4$ | $\lambda_5$ | $ | $\bar{d}_v$ | {c,184}$ | {c,190}$ | {c,192}$ | 1M AUT_30 ($\Delta$) | 1.5M AUT_30 ($\Delta$) | 2M AUT_30 ($\Delta$) | Overall AUT_30 | Converged? | Screening Pass? |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | lam_d2_0.10_d3_0.90_d4_0.00_d5_0.00 | 0.10 | 0.90 | 0.00 | 0.00 | 146 | 2.857 | 16 | 16 | 16 | 153.997 (+109.2%) | 154.117 (+159.6%) | 154.091 (+159.2%) | **154.068452** | False | False |
| 2 | lam_d2_0.10_d3_0.85_d4_0.05_d5_0.00 | 0.10 | 0.85 | 0.05 | 0.00 | 148 | 2.892 | 17 | 16 | 16 | 154.101 (+109.4%) | 154.186 (+159.7%) | 154.176 (+159.3%) | **154.154431** | False | False |
| 3 | lam_d2_0.10_d3_0.85_d4_0.00_d5_0.05 | 0.10 | 0.85 | 0.00 | 0.05 | 149 | 2.913 | 17 | 16 | 16 | 154.142 (+109.4%) | 154.239 (+159.8%) | 154.215 (+159.4%) | **154.198669** | False | False |
| 4 | lam_d2_0.10_d3_0.80_d4_0.10_d5_0.00 | 0.10 | 0.80 | 0.10 | 0.00 | 150 | 2.927 | 17 | 16 | 16 | 154.179 (+109.5%) | 154.271 (+159.8%) | 154.257 (+159.5%) | **154.235522** | False | False |
| 5 | lam_d2_0.05_d3_0.95_d4_0.00_d5_0.00 | 0.05 | 0.95 | 0.00 | 0.00 | 75 | 2.927 | 17 | 16 | 16 | 154.172 (+109.5%) | 154.286 (+159.8%) | 154.258 (+159.5%) | **154.238570** | False | False |
| 6 | lam_d2_0.10_d3_0.80_d4_0.05_d5_0.05 | 0.10 | 0.80 | 0.05 | 0.05 | 151 | 2.948 | 17 | 16 | 16 | 154.219 (+109.5%) | 154.322 (+159.9%) | 154.294 (+159.5%) | **154.278412** | False | False |
| 7 | lam_d2_0.10_d3_0.75_d4_0.15_d5_0.00 | 0.10 | 0.75 | 0.15 | 0.00 | 152 | 2.963 | 17 | 16 | 16 | 154.255 (+109.6%) | 154.354 (+160.0%) | 154.337 (+159.6%) | **154.315203** | False | False |
| 8 | lam_d2_0.05_d3_0.90_d4_0.05_d5_0.00 | 0.05 | 0.90 | 0.05 | 0.00 | 76 | 2.963 | 17 | 16 | 16 | 154.259 (+109.6%) | 154.358 (+160.0%) | 154.341 (+159.6%) | **154.319436** | False | False |
| 9 | lam_d2_0.10_d3_0.80_d4_0.00_d5_0.10 | 0.10 | 0.80 | 0.00 | 0.10 | 152 | 2.970 | 17 | 17 | 16 | 154.265 (+109.6%) | 154.371 (+160.0%) | 154.341 (+159.6%) | **154.325407** | False | False |
| 10 | lam_d2_0.10_d3_0.75_d4_0.10_d5_0.05 | 0.10 | 0.75 | 0.10 | 0.05 | 153 | 2.985 | 17 | 17 | 16 | 154.296 (+109.6%) | 154.395 (+160.0%) | 154.373 (+159.7%) | **154.354512** | False | False |

### 3.6 Delta Audit Across Complete Finite Set
- **1M Deltas**: min = **+1.092119** (+109.2%), median = **+1.102275** (+110.2%), max = **+1.103946** (+110.4%). Count($\Delta_{1\text{M}} < 0$) = **0**, Count($\Delta_{1\text{M}} \le -0.05$) = **0**.
- **1.5M Deltas**: min = **+1.595550** (+159.6%), median = **+1.606756** (+160.7%), max = **+1.608497** (+160.8%). Count($\Delta_{1.5\text{M}} < 0$) = **0**, Count($\Delta_{1.5\text{M}} \le -0.05$) = **0**.
- **2M Deltas**: min = **+1.591928** (+159.2%), median = **+1.603493** (+160.3%), max = **+1.605282** (+160.5%). Count($\Delta_{2\text{M}} < 0$) = **0**, Count($\Delta_{2\text{M}} \le -0.05$) = **0**.
- **Verified Invariant**: Candidates with $\Delta > 0$ on ALL THREE sources = **259 / 259** (100.0%).

### 3.7 Screening Gate Result & P1-B Decision
- **Screening PASS Set Size**: **0**.
- **P1-B Confirmation Decision**: Because the screening pass set is empty, P1-B confirmation on fresh seeds was **skipped conditionally** in accordance with the frozen protocol.
- **Confirmation Runs**: **0**.

---

## 4. Independently Recomputable Derivations

1. **Screening Gate Failure**:
   - Total finite candidates evaluated = 259.
   - Number meeting $\Delta_s \le -0.05$ on all 3 sources with all 9 runs converged = **0**.
2. **Terminal State Determination**:
   - Under the pre-registered V37-P1 decision logic, an empty screening pass set yields strictly:
     \text{Terminal State} = \mathbf{P1\_NO\_FINITE\_FEASIBLE\_DE\_ADVANCE}

---

## 5. Scientific Interpretation & Hypotheses

> [!NOTE]
> The following analysis represents scientific interpretation and hypotheses consistent with the observed data, not controlled causal proofs.

### 5.1 Structural Tension in High-Rate Finite Irregular NB-LDPC
- **Large Optimization Distance**: The performance gap between candidate distributions ($\Delta \approx +109\% \sim +160\%$) and baseline is over an order of magnitude larger than the $-5\%$ improvement gate. This indicates a structural regime gap rather than a grid resolution artifact.
- **Boundary Saturation at Lowest Variable Degree**: The lowest-AUT_30 distribution sits precisely at the lowest allowed variable-degree boundary ($\lambda_2=0.10, \lambda_3=0.90, \lambda_4=0, \lambda_5=0$). Increasing higher-degree fractions ($\lambda_4, \lambda_5$) strictly increases $\bar{d}_v$ and check degrees $, monotonically degrading DE trajectory behavior.
- **Structural Hypothesis**: Under high code rates ( \approx 0.8125 - 0.8203$), the relationship $\bar{d}_c = \bar{d}_v / (1 - R) \approx 5.3 \bar{d}_v$ couples variable degree to check degree. When the finite-length forest gate ( \le 183$) bounds $\lambda_2 \le 0.10$, average variable degree is constrained to $\bar{d}_v \ge 2.857$, resulting in check degrees  \in [16, 20]$. In GF(32) message passing, higher check degrees are hypothesized to severely inflate check-node message convolution uncertainty, impeding early-iteration mutual information flow.
- **Positive Control Context**: Even the V36 positive control ($\lambda_2=0.85, \lambda_4=0.15, N_2=941$), which has abundant degree-2 variables, exhibited $+8.65\%$ to $+42.39\%$ higher $\text{AUT}_{30}$ than regular =2$, indicating that adjusting single-edge polynomial weights alone is insufficient.

### 5.2 Architectural Roadmap for V38+
- **Direction Abandoned**: Unstructured single-edge irregular $\lambda$-distribution simplex tuning. Finer grid resolution searches (e.g., step=0.025) are closed.
- **Candidate Structured Directions**:
  1. **Protograph / Multi-Edge-Type (MET) NB-LDPC** (Primary Candidate): Utilizing MET structures to enforce controlled degree-2 chains, accumulators, and topological constraints, achieving low effective variable degrees without random cycle explosion.
  2. **Near-=2$ Structured Topology + GF(32) Edge Coefficient Optimization**: Preserving the strong DE convergence of low-degree regular graphs while resolving finite-length girth, rank deficiency, and trapping sets through algebraic edge labeling.
  3. **Non-Binary Spatially-Coupled LDPC (SC-NB-LDPC)** (Fallback Architecture): Leveraging spatial coupling threshold saturation on protographs.

---

## 6. Claim Boundary

### Allowed Statements
- Within the pre-registered V37R1 candidate space (degrees $\{2, 3, 4, 5\}$ on 0.05-simplex, necessary forest-count gate  \le 183$, realized check degree cap {c,\max} \le 20$) under the source-specific V25 TRAIN empirical-P GF(32) DE protocol, **no candidate satisfied the pre-registered screening gate (0 / 259 passed)**.
- The experiment concludes stage P1 with terminal state P1_NO_FINITE_FEASIBLE_DE_ADVANCE.

### Forbidden Statements
- Do NOT claim that non-binary LDPC or irregular LDPC is generally impossible or inferior.
- Do NOT claim finite-block decoding failure, FER results, or key-rate conclusions (no finite decoding was performed).
- Do NOT claim Tanner-graph realizability or non-realizability results.
- Do NOT assert check degree as a proven causal mechanism without controlled causal experiments.
- Do NOT claim formal scientific promotion.

---

## 7. Review Status
- **Review Kind**: DEVELOPMENT_RESULT (Correction Audit)
- **Terminal State**: P1_NO_FINITE_FEASIBLE_DE_ADVANCE (Supported by recomputed raw evidence)
- **Lifecycle State**: DEVELOPMENT_RESULT_REVIEW_PENDING
