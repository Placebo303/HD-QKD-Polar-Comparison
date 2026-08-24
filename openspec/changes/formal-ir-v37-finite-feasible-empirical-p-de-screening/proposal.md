# OpenSpec Proposal: formal-ir-v37-finite-feasible-empirical-p-de-screening

**Status**: PLAN_CANDIDATE  
**Domain**: Formal Information Reconciliation (IR) / Nonbinary LDPC Research Mainline  
**Change ID**: `formal-ir-v37-finite-feasible-empirical-p-de-screening`  
**Parent / Accepted Baseline SHA**: `a258c5a7549f33f43a32b193b134f1ca0df15aea` (V37-P0R1)  
**Execution Authorization**: NOT_GRANTED (Plan documents only)

---

## 1. Why

In V36, empirical-P density evolution (DE) screening selected candidate $\lambda_2=0.85, \lambda_4=0.15$, but this distribution maps to $N_2 = 941$ degree-2 variables for block length $n=1024$. Over $m \in \{184, 190, 192\}$ check nodes, this forced an unavoidable degree-2 cycle rank of at least $750\text{--}758$, violating the zero-cycle structural gate and causing downstream finite-graph advance failure. Furthermore, V36 A1 evaluated candidates against an unmatched baseline and relied on saturated final entropy ($\sim 3 \times 10^{-296}$).

V37-P1 designs a mathematically sound, corrected DE screening experiment. It incorporates the accepted V37-P0 degree feasibility filter ($N_2 \le 183$) as a mandatory pre-condition, evaluates all candidates against a strictly matched baseline under identical empirical-P settings, and replaces saturated final entropy with non-saturated trajectory metrics (Area Under Trajectory $\text{AUT}_{30}$).

---

## 2. Scientific Question

Can a finite-length-admissible empirical-P irregular NB-LDPC degree distribution retain or improve the useful DE convergence behavior seen in V36, without relying on a mathematically impossible degree-2 topology?

---

## 3. Scope and Boundaries

- **Block Length & Rates**:
  - $n = 1024$
  - 1M: $m_2 = 184$, $R = 1 - 184/1024 = 0.8203125$
  - 1p5M: $m_2 = 190$, $R = 1 - 190/1024 = 0.814453125$
  - 2M: $m_2 = 192$, $R = 1 - 192/1024 = 0.8125$
- **Mandatory Finite-Length Gate**:
  - $N_2 \le \min(m) - 1 = 183$, evaluated via V37-P0 integer node apportionment.
- **Search Universe**:
  - Degrees $d_v \in \{2, 3, 4, 5\}$ on a $0.05$ simplex grid (1,771 raw distributions).
  - Pre-filtered by $N_2 \le 183$ (547 distributions) and $d_{c,\max} \le 20$ (259 pre-registered candidates).
- **Matched Baseline & Controls**:
  - Baseline: True V31/V36 regular $d_v=2$ distribution ($\lambda = \{2: 1.0\}$) evaluated under identical settings.
  - Exploratory Positive Control: V36 candidate $\lambda=\{2: 0.85, 4: 0.15\}$, explicitly marked `finite_inadmissible=True` (reference only; non-promotable).
- **Evaluation Discipline**:
  - Per-source evaluation first; matched seeds, iterations ($I=60$), sample count ($N=4000$).
  - Primary ranking: Area Under Entropy Trajectory ($\text{AUT}_{30}$).
- **Stop / Advance Gates**:
  - `P1_DE_ADVANCE_CANDIDATE_FOUND`: Finite-feasible candidate improves $\text{AUT}_{30}$ by $\ge 5\%$ on all three sources over matched baseline. Proposes (does not execute) V37-P2 finite-graph design.
  - `P1_NO_FINITE_FEASIBLE_DE_ADVANCE`: No candidate meets per-source threshold. Closes this bounded family.
