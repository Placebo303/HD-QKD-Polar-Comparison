# V37-P1 Scientific Plan: Finite-Feasible Empirical-P DE Candidate Screening

**Date**: 2026-08-24  
**Lifecycle**: PLAN_CANDIDATE  
**Parent / Baseline SHA**: `a258c5a7549f33f43a32b193b134f1ca0df15aea` (V37-P0R1 accepted)  
**Execution Authorization**: NOT_GRANTED (Read and write plan documents only)

---

## 1. Scientific Context & Hypothesis

### 1.1 Problem Statement
In V36, the candidate edge distribution $\lambda_2=0.85, \lambda_4=0.15$ was selected by DE screening. However, finite-length degree feasibility analysis (accepted in V37-P0R1) proved that this distribution requires $N_2 = 941$ degree-2 variable nodes for $n=1024$. Connecting 941 degree-2 edges across $m \in \{184, 190, 192\}$ check nodes forces an unavoidable degree-2 cycle rank lower bound of $758/752/750$, making a zero-degree-2-cycle graph mathematically impossible.

Furthermore, V36 A1 evaluated candidates against an unmatched baseline and relied on saturated final entropy ($\sim 3 \times 10^{-296}$ bits/symbol), which is ineffective for ranking fast-converging distributions.

### 1.2 Scientific Question
Can a finite-length-admissible empirical-P irregular NB-LDPC degree distribution retain or improve the useful DE convergence behavior seen in V36, without relying on a mathematically impossible degree-2 topology?

### 1.3 Scientific Hypothesis
Under the empirical timestamp channel law $P(A|B)$, finite-feasible degree distributions satisfying $N_2 \le 183$ (which guarantees the mathematical possibility of a cycle-free degree-2 subgraph on $m \ge 184$) can achieve faster non-saturated convergence (measured via early-iteration Area Under Trajectory) than the regular $d_v=2$ baseline across all three operational sources (1M, 1.5M, 2M) under matched DE settings.

---

## 2. Pre-Registered Candidate Grid & P0 Feasibility Filter

### 2.1 Raw Grid Specification
- **Variable Degrees**: $d_v \in \{2, 3, 4, 5\}$
- **Simplex Grid Step**: $\lambda_d \in \{0.00, 0.05, 0.10, \dots, 1.00\}$ with $\sum_{d=2}^5 \lambda_d = 1.0$.
- **Total Raw Distributions**: **1,771 distributions**.

### 2.2 P0 Finite-Length Feasibility Filter
Every candidate is evaluated using the accepted V37-P0 analyzer (`analyze_degree_feasibility`) for block length $n=1024$ and target check node counts $m \in \{184, 190, 192\}$:
1. **Forest Upper Bound Gate**:
   A shared candidate intended to allow a cycle-free degree-2 subgraph across all three sources must satisfy:
   $$N_2 \le \min(m) - 1 = 183$$
   where $N_2$ is the exact integer apportionment from largest-remainder (Hamilton) allocation.
   - **Distributions satisfying $N_2 \le 183$**: **547 distributions** (out of 1,771).
   - *Mathematical Consequence*: Because $L_2 \le 183/1024 \approx 0.1787$, the average variable degree is strictly bounded below by $\bar{d}_v \ge 2.8213$, which yields average check degrees $\bar{d}_c \in [15.5, 20.0]$.
2. **Check Degree Realizability Gate**:
   To prevent excessive check degrees while accommodating $\bar{d}_v \ge 2.82$, we require realized maximum check degree:
   $$d_{c,\max} \le 20$$
   - **Distributions satisfying $N_2 \le 183$ AND $d_{c,\max} \le 20$**: **259 pre-registered candidates**.

---

## 3. Corrected Matched Density Evolution Protocol

### 3.1 Repairing V36 A1 Deficiencies
1. **Identical DE Execution Settings**:
   - Channel law: Source-specific train empirical posterior $P(A|B)$ from V25 (`load_v25_channel_counts()`).
   - Field: $\text{GF}(32)$, polynomial $37$.
   - Sample count: $N_{\text{mc}} = 4000$ per iteration.
   - Iteration budget: $I_{\max} = 60$ iterations.
   - Seeds: Three independent pre-registered seeds per source:
     - 1M: `[370101, 370102, 370103]`
     - 1p5M: `[370201, 370202, 370203]`
     - 2M: `[370301, 370302, 370303]`
   - Check distribution: Harmonic-exact concentrated check distribution $\rho$ matched to exact rate $R = 1 - m/1024$.
2. **Matched Controls**:
   - **Matched Baseline**: Regular $d_v=2$ ($\lambda = \{2: 1.0\}$) evaluated under the identical $N=4000, I=60$, 3 seeds/source protocol.
   - **Exploratory Positive Control**: V36 candidate $\lambda = \{2: 0.85, 4: 0.15\}$ ($N_2=941$), evaluated under the same settings with flag `finite_inadmissible=True` (cannot be selected as advancing candidate).
3. **Per-Source First Comparison**:
   - No aggregate-only averaging. Every candidate must beat the baseline independently on source 1M ($m=184$), 1.5M ($m=190$), and 2M ($m=192$).

### 3.2 Non-Saturated Trajectory Metrics
Because final entropy saturates to $< 10^{-100}$ bits/symbol on converging distributions, ranking relies on the convergence trajectory:

1. **Primary Ranking Metric**: Area Under Entropy Trajectory over the first 30 iterations ($\text{AUT}_{30}$):
   $$\text{AUT}_{30} = \sum_{t=0}^{30} H(t)$$
   (Lower $\text{AUT}_{30}$ indicates strictly faster early-stage convergence).
2. **Secondary Diagnostic Metrics**:
   - Early-iteration entropy at fixed checkpoints: $H(t=5), H(t=10), H(t=15)$.
   - Threshold iterations: $T_{0.10} = \min \{t : H(t) \le 0.10\}$, $T_{0.01} = \min \{t : H(t) \le 0.01\}$.
   - Final entropy $H(60)$ (convergence status flag only: $\text{converged} \iff H(60) < 10^{-4}$).
3. **Deterministic Tie-Breaker**:
   1. Mean $\text{AUT}_{30}$ across all 3 sources (ascending)
   2. Mean $H(t=10)$ across all 3 sources (ascending)
   3. $N_2$ count (ascending, favoring lower degree-2 variable mass)
   4. Canonical `candidate_id` string (lexicographic)

---

## 4. Decision Logic & Stop / Advance Gates

### 4.1 Advance Gate
A candidate achieves `P1_DE_ADVANCE_CANDIDATE_FOUND` if and only if:
1. $N_2 \le 183$ and $d_{c,\max} \le 20$ (P0 feasibility passed).
2. All 3 sources converge across all 3 seeds ($H(60) < 10^{-4}$).
3. For **every source** $s \in \{\text{1M}, \text{1p5M}, \text{2M}\}$:
   $$\overline{\text{AUT}}_{30}(s, \text{candidate}) \le \overline{\text{AUT}}_{30}(s, \text{baseline}) \times 0.95 \quad (\ge 5\% \text{ improvement})$$

### 4.2 Terminal States
- **`P1_DE_ADVANCE_CANDIDATE_FOUND`**:
  At least one finite-feasible candidate achieves $\ge 5\%$ per-source trajectory improvement over the matched baseline. Authorizes *proposing* (not executing) a V37-P2 finite-graph design.
- **`P1_NO_FINITE_FEASIBLE_DE_ADVANCE`**:
  No candidate passing $N_2 \le 183$ achieves per-source advance. Closes this bounded $\{2, 3, 4, 5\}$ single-edge candidate family without overclaiming failure of MET, protographs, or NB-LDPC generally.
- **`P1_DE_EVIDENCE_INVALID`**:
  Execution anomaly, seed divergence, or missing artifacts.

---

## 5. Scope Guard & P1 Boundaries

- **P1 is DE-Only**:
  - No PEG matrix generation, protograph lifting, Tanner graph construction, finite decoder execution, FER, or exact recovery runs are included in P1.
- **Resource Estimates**:
  - Total evaluations: 259 feasible candidates $+ 1$ baseline $+ 1$ positive control $= 261$ configurations.
  - Total MC-DE runs: $261 \times 3 \text{ sources} \times 3 \text{ seeds} = 2,349$ runs.
  - Estimated runtime: $\approx 120\text{--}240$ seconds ($\sim 2\text{--}4$ minutes).

---

## 6. Scientific Claim Boundaries

| Claim | Allowed? | Rationale |
|---|---|---|
| Identified degree distribution achieves faster asymptotic DE trajectory decay under empirical-P channel | **Allowed** (if PASS) | Directly measured by matched $\text{AUT}_{30}$ across all 3 sources |
| Identified degree distribution is finite-length cycle-free degree-2 admissible | **Allowed** (if PASS) | Directly proved by $N_2 \le 183$ via V37-P0 analyzer |
| Finite code success, FER superiority, or key rate improvement | **FORBIDDEN** | P1 is asymptotic DE only; finite decoding is out of scope |
| General failure of NB-LDPC, MET, or protograph approaches | **FORBIDDEN** | P1 evaluates only bounded single-edge degree distributions over $\{2, 3, 4, 5\}$ |
| Cycle rank causally explains decoder failure | **FORBIDDEN** | Cycle rank is a topological property, not an established causal error mechanism |
