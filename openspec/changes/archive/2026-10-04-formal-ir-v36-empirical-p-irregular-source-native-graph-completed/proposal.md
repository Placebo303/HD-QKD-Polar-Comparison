# OpenSpec Proposal: formal-ir-v36-empirical-p-irregular-source-native-graph

**Status**: POST_RUN_REVIEWED / A1_DE_SELECTION_NOT_ACCEPTED / A2_STRUCTURAL_GATE_FAILED / NO_FINITE_GRAPH_ADVANCE  
**Domain**: Formal Information Reconciliation (IR) / Nonbinary LDPC Development  
**Change ID**: `formal-ir-v36-empirical-p-irregular-source-native-graph`  
**Working Directory**: `comparison_bench/src/comparison_bench/formal_ir/`  
**Output Root**: `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v36_empirical_graph_development/run_01/`  

---

## 1. Why

Prior finite-length diagnostics (V34 matched empirical-P control and V35 hand-designed protograph) demonstrated that:
1. On the regular $d_v=2$ baseline graph, schedule modifications cannot overcome finite-length trapping structures (residual errors stall at $175.93 \pm 16.54$).
2. Hand-designed protographs with high average degree ($\bar{d}_v \approx 3.09$) and high check degrees without empirical-P density evolution optimization significantly degrade performance (residual errors increase to $245.87 \pm 19.00$).
3. Submatrix truncation ($H[:184]$) reintroduces degree-2 cycle vulnerabilities.

V36 establishes an empirical-P-guided irregular LDPC pipeline to screen degree distribution candidates over $\text{GF}(32)$, construct source-native finite PEG graphs ($N=1024, m_2 \in \{184, 190, 192\}$), evaluate paired finite decoding against the V31 baseline, and conditionally test moderate-degree incremental syndrome.

---

## 2. Scope and Boundaries

- **Exact Rates**:
  - 1M: $R = 1 - 184/1024 = 0.8203125$ ($m_2 = 184$)
  - 1p5M: $R = 1 - 190/1024 = 0.814453125$ ($m_2 = 190$)
  - 2M: $R = 1 - 192/1024 = 0.8125$ ($m_2 = 192$)
- **Degree Distribution Search Space**:
  - Variable degrees $d_v \in \{2, 3, 4, 5\}$, $\lambda_1 = 0$, $\sum \lambda_d = 1$, weights on $0.05$ grid.
  - Average variable degree $\bar{d}_v = 1 / \sum (\lambda_d / d) \in [2.15, 2.55]$.
  - Check degrees $\rho$ concentrated around $10\text{--}14$, maximum check degree $\le 16$.
- **Source-Native Construction**:
  - Independent PEG construction for 1M ($184 \times 1024$), 1.5M ($190 \times 1024$), and 2M ($192 \times 1024$). No truncation.
- **Development Seeds**:
  - A0 iteration diagnostic: 1M `360101..360103`, 1p5M `360201..360203`, 2M `360301..360303` (9 blocks).
  - A3 paired development screen: 1M `360101..360105`, 1p5M `360201..360205`, 2M `360301..360305` (15 blocks).
- **Terminal States**:
  - `DE_SHORTLIST_READY` / `NO_DE_ADVANCE` / `DE_EVIDENCE_INVALID`
  - `FINITE_GRAPH_ADVANCE` / `NO_FINITE_GRAPH_ADVANCE`
  - `NB_DEVELOPMENT_CANDIDATE_FOUND` / `FINITE_GRAPH_ADVANCE_NO_EXACT` / `NO_INCREMENTAL_ADVANCE` / `EVIDENCE_INVALID`
