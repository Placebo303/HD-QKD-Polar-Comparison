# V37-P1 Scientific Plan: Finite-Feasible Empirical-P DE Candidate Screening

**Date**: 2026-08-24
**Lifecycle**: PLAN_CANDIDATE
**Parent / Baseline SHA**: `a258c5a7549f33f43a32b193b134f1ca0df15aea` (V37-P0R1 accepted; provenance recorded in `docs/research_cycles/V37P0/REVIEW_VERDICT.md`)
**Execution Authorization**: NOT_GRANTED (Read and write plan documents only)

---

## 1. Scientific Context & Hypothesis

### 1.1 Problem Statement
In V36, the candidate edge distribution $\lambda_2=0.85, \lambda_4=0.15$ was selected by DE screening. However, finite-length degree feasibility analysis (accepted in V37-P0R1) proved that this distribution requires $N_2 = 941$ degree-2 variable nodes for $n=1024$. Connecting 941 degree-2 edges across $m \in \{184, 190, 192\}$ check nodes forces an unavoidable degree-2 cycle rank lower bound of $758/752/750$, making a zero-degree-2-cycle graph mathematically impossible.

Furthermore, V36 A1 evaluated candidates against an unmatched baseline, relied on saturated final entropy ($\sim 3 \times 10^{-296}$ bits/symbol), and lacked disjoint confirmation seeds to rule out selection bias.

### 1.2 Scientific Question
Can an empirical-P irregular NB-LDPC degree distribution that passes the necessary finite-length degree-2 forest-count feasibility condition retain or improve early-stage cumulative entropy decay relative to the matched regular $d_v=2$ baseline, without relying on a mathematically impossible degree-2 topology?

### 1.3 Scientific Hypothesis
Under the empirical timestamp channel law $P(A|B)$, finite-feasible degree distributions satisfying the necessary forest-count condition $N_2 \le 183$ (which guarantees the mathematical possibility of a cycle-free degree-2 subgraph across all $m \ge 184$) can achieve lower cumulative early-iteration entropy (measured via Area Under Trajectory $\text{AUT}_{30}$) than the matched regular $d_v=2$ baseline across all three operational sources (1M, 1.5M, 2M) under matched DE screening and confirmation.

---

## 2. Pre-Registered Candidate Grid & Mathematical Grounding

### 2.1 Raw Grid Specification
- **Variable Degrees**: $d_v \in \{2, 3, 4, 5\}$
- **Simplex Grid Step**: $\lambda_d \in \{0.00, 0.05, 0.10, \dots, 1.00\}$ with $\sum_{d=2}^5 \lambda_d = 1.0$.
- **Total Raw Distributions**: **1,771 distributions**.

### 2.2 P0 Necessary Forest-Count Feasibility Gate
Every candidate is evaluated using the accepted V37-P0 analyzer (`analyze_degree_feasibility`) for block length $n=1024$ and target check node counts $m \in \{184, 190, 192\}$:
- **Forest Upper Bound Necessary Condition**:
  A shared candidate intended to allow a cycle-free degree-2 subgraph across all three sources must satisfy:
  $$N_2 \le \min(m) - 1 = 183$$
  where $N_2$ is the exact integer apportionment from largest-remainder (Hamilton) allocation.
- **Distributions satisfying $N_2 \le 183$**: **547 distributions** (out of 1,771).
- **Mathematical Bound on Variable & Check Degrees**:
  Because $L_2 \le 183/1024 \approx 0.1787$, the theoretical lower bound on average variable degree is:
  $$\bar{d}_v = \sum_d d \cdot L_d \ge 2 \cdot L_2 + 3 \cdot (1 - L_2) = 3 - L_2 \ge 2.8213$$
  Across the 547 candidates passing $N_2 \le 183$, the actual range is $\bar{d}_v \in [2.8571, 5.0000]$ and total sockets $E \in [2926, 5120]$.
  For $m=184$, the mean check degree is $\bar{d}_c \in [15.9022, 27.8261]$.
  *Crucially*: $N_2 \le 183$ alone does *not* restrict check degrees $\le 20$.

### 2.3 Additional Pre-Registered Design Cap: Maximum Check Degree
To prevent excessively high check degrees and decoder complexity while accommodating $\bar{d}_v \ge 2.82$, we pre-register an explicit search cap on realized maximum check degree:
$$d_{c,\max} \le 20$$
where $d_{c,\max}$ is evaluated using P0's exact integer floor/ceil check-degree allocation algorithm across all three sources ($m \in \{184, 190, 192\}$).
- **Distributions satisfying $N_2 \le 183$ AND $d_{c,\max} \le 20$**: **259 pre-registered candidates**.

### 2.4 Semantic Scope of $N_2 \le 183$
$N_2 \le 183$ is a *necessary* condition that removes the edge-count forest obstruction. It guarantees that the degree-2 subgraph is not mathematically blocked from being a forest. It does *not* constitute a constructive proof that a zero-degree-2-cycle Tanner graph exists under full variable sequences, check allocations, and PEG/lifting constraints. Full cycle-free realizability is to be evaluated during downstream graph construction (P2).

---

## 3. Corrected Matched Density Evolution Protocol

### 3.1 Repairing V36 A1 Deficiencies
1. **Identical DE Execution Settings**:
   - Channel law: Source-specific train empirical posterior $P(A|B)$ from V25 (`load_v25_channel_counts()`).
   - Field: $\text{GF}(32)$, polynomial $37$ (`0b100101`).
   - Sample count: $N_{\text{mc}} = 4000$ per iteration.
   - Iteration budget: $I_{\max} = 60$ iterations.
   - Check distribution: Harmonic-exact concentrated check distribution $\rho$ matched to exact rate $R = 1 - m/1024$.
2. **Two-Stage Screening and Confirmation (Preventing Selection Bias / Winner's Curse)**:
   - **P1-A Screening Stage**:
     - 259 pre-registered candidates + 1 matched baseline + 1 positive control ($V36$, $\lambda=\{2:0.85, 4:0.15\}$, tagged `finite_inadmissible=True`).
     - 3 independent screening seeds per source:
       - 1M: `[370101, 370102, 370103]`
       - 1p5M: `[370201, 370202, 370203]`
       - 2M: `[370301, 370302, 370303]`
     - Select best candidate $C^*$ based on primary metric and tie-breakers.
   - **P1-B Confirmation Stage**:
     - Evaluate $C^*$ and the matched baseline on 3 completely fresh, disjoint confirmation seeds per source:
       - 1M: `[370111, 370112, 370113]`
       - 1p5M: `[370211, 370212, 370213]`
       - 2M: `[370311, 370312, 370313]`
     - Confirmation independently verifies that $C^*$ satisfies the per-source advance threshold.
3. **Matched Controls**:
   - **Matched Baseline**: Regular $d_v=2$ ($\lambda = \{2: 1.0\}$) evaluated under the identical $N=4000, I=60$, screening and confirmation seeds.
   - **Exploratory Positive Control**: V36 candidate $\lambda = \{2: 0.85, 4: 0.15\}$ ($N_2=941$), evaluated under the same settings with flag `finite_inadmissible=True` (reference only; non-promotable).
4. **Per-Source First Comparison**:
   - No aggregate-only averaging. Every candidate must beat the baseline independently on source 1M ($m=184$), 1.5M ($m=190$), and 2M ($m=192$).

### 3.2 Non-Saturated Trajectory Metrics
Because final entropy saturates to $< 10^{-100}$ bits/symbol on converging distributions, ranking relies on the convergence trajectory:

1. **Primary Ranking Metric**: Area Under Entropy Trajectory over the first 30 iterations ($\text{AUT}_{30}$):
   $$\text{AUT}_{30} = \sum_{t=0}^{30} H(t)$$
   Lower $\text{AUT}_{30}$ indicates lower cumulative early-iteration entropy (capturing faster initial entropy reduction, though not necessarily pointwise lower at every single iteration).
2. **Secondary Diagnostic Metrics**:
   - Early-iteration entropy at fixed checkpoints: $H(t=5), H(t=10), H(t=15)$.
   - Threshold iterations: $T_{0.10} = \min \{t : H(t) \le 0.10\}$, $T_{0.01} = \min \{t : H(t) \le 0.01\}$.
   - Final entropy $H(60)$ (convergence status flag only: $\text{converged} \iff H(60) < 10^{-4}$).
   - Paired relative difference per source:
     $$\Delta_s = \frac{\overline{\text{AUT}}_{30}(s, \text{candidate}) - \overline{\text{AUT}}_{30}(s, \text{baseline})}{\overline{\text{AUT}}_{30}(s, \text{baseline})}$$
     along with individual per-seed paired differences.
3. **Development Effect-Size Threshold**:
   - The threshold of $\ge 5\%$ ($\Delta_s \le -0.05$) is pre-registered as a practical development effect-size gate (not a theoretical or statistical significance claim).
4. **Deterministic Tie-Breaker**:
   1. Mean $\text{AUT}_{30}$ across all 3 sources (ascending)
   2. Mean $H(t=10)$ across all 3 sources (ascending)
   3. $N_2$ count (ascending, favoring lower degree-2 variable mass)
   4. Canonical `candidate_id` string (lexicographic)

---

## 4. Decision Logic & Stop / Advance Gates

### 4.1 Advance Gate
A candidate achieves `P1_DE_ADVANCE_CANDIDATE_FOUND` if and only if:
1. $N_2 \le 183$ and $d_{c,\max} \le 20$ (P0 feasibility and design cap passed).
2. All 3 sources converge across all screening and confirmation seeds ($H(60) < 10^{-4}$).
3. In **P1-A Screening**, for **every source** $s \in \{\text{1M}, \text{1p5M}, \text{2M}\}$:
   $$\overline{\text{AUT}}_{30,\text{screen}}(s, C^*) \le \overline{\text{AUT}}_{30,\text{screen}}(s, \text{baseline}) \times 0.95 \quad (\ge 5\% \text{ reduction})$$
4. In **P1-B Confirmation**, for **every source** $s \in \{\text{1M}, \text{1p5M}, \text{2M}\}$ on fresh confirmation seeds:
   $$\overline{\text{AUT}}_{30,\text{confirm}}(s, C^*) \le \overline{\text{AUT}}_{30,\text{confirm}}(s, \text{baseline}) \times 0.95 \quad (\ge 5\% \text{ reduction})$$

### 4.2 Terminal States
- **`P1_DE_ADVANCE_CANDIDATE_FOUND`**:
  Best candidate satisfies per-source $\ge 5\%$ reduction in both screening and confirmation. Authorizes *proposing* (not executing) a V37-P2 finite-graph design.
- **`P1_SCREEN_SIGNAL_NOT_CONFIRMED`**:
  A candidate met the screening threshold but failed to confirm on fresh seeds.
- **`P1_NO_FINITE_FEASIBLE_DE_ADVANCE`**:
  No candidate passing $N_2 \le 183, d_{c,\max} \le 20$ achieved the screening advance threshold. Closes the tested degree-$\{2, 3, 4, 5\}$, $0.05$-simplex-grid, $N_2 \le 183, d_{c,\max} \le 20$ candidate set under the frozen empirical-P DE protocol.
- **`P1_DE_EVIDENCE_INVALID`**:
  Execution anomaly, seed divergence, or missing artifacts.

---

## 5. Scope Guard & Resource Estimates

- **P1 is DE-Only**:
  - No PEG matrix generation, protograph lifting, Tanner graph construction, finite decoder execution, FER, or exact recovery runs are included in P1.
- **Resource Estimates**:
  - P1-A Screening: 261 configs (259 feasible + 1 baseline + 1 positive control) $\times$ 3 sources $\times$ 3 seeds = 2,349 runs.
  - P1-B Confirmation: 2 configs ($C^*$ + baseline) $\times$ 3 sources $\times$ 3 seeds = 18 runs.
  - Total MC-DE runs: **2,367 runs** ($\approx 120\text{--}240$ seconds wallclock).

---

## 6. Scientific Claim Boundaries

| Claim | Allowed? | Rationale |
|---|---|---|
| Identified degree distribution achieves lower cumulative early-iteration entropy ($\text{AUT}_{30}$) under empirical-P channel | **Allowed** (if PASS) | Directly measured by matched $\text{AUT}_{30}$ across all 3 sources in screening and confirmation |
| Identified degree distribution passes the necessary degree-2 forest-count feasibility condition ($N_2 \le 183$) | **Allowed** (if PASS) | Directly verified by $N_2 \le 183$ via V37-P0 analyzer |
| Cycle-free Tanner graph realizability is proved | **FORBIDDEN** | $N_2 \le 183$ is a necessary condition; graph realizability requires P2 constructive evidence |
| Pointwise faster convergence at every iteration | **FORBIDDEN** | $\text{AUT}_{30}$ measures cumulative trajectory area, not pointwise strict inequality |
| Finite code success, FER superiority, or key rate improvement | **FORBIDDEN** | P1 is asymptotic DE only; finite decoding is out of scope |
| General failure of NB-LDPC, MET, or protograph approaches | **FORBIDDEN** | If negative, closes only the tested $\{2, 3, 4, 5\}$, $0.05$-simplex, $N_2 \le 183, d_{c,\max} \le 20$ candidate set |
| Cycle rank causally explains decoder failure | **FORBIDDEN** | Cycle rank is a topological property, not an established causal error mechanism |
