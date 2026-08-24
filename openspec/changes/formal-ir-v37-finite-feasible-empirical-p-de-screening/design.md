# OpenSpec Design: formal-ir-v37-finite-feasible-empirical-p-de-screening

**Lifecycle**: PLAN_CANDIDATE  
**Parent Baseline**: `a258c5a7549f33f43a32b193b134f1ca0df15aea` (V37-P0R1 accepted)  

---

## 1. Mathematical Grounding & Candidate Grid

### 1.1 Degree-2 Forest Feasibility Constraint (P0 Integration)
For block length $n=1024$ and check dimensions $m \in \{184, 190, 192\}$, a cycle-free degree-2 subgraph across all three sources requires:
$$N_2 \le \min(m) - 1 = 183$$
where $N_2$ is computed via largest-remainder integer apportionment from node-perspective distribution $L_2 = (\lambda_2 / 2) / \sum_j (\lambda_j / j)$.

Because $L_2 \le 183 / 1024 \approx 0.1787$, the average variable degree is strictly bounded below:
$$\bar{d}_v = \sum_d d \cdot L_d \ge 2 \cdot L_2 + 3 \cdot (1 - L_2) = 3 - L_2 \ge 2.8213$$
This implies average check degrees $\bar{d}_c = E / m \in [15.5, 20.0]$.

### 1.2 Candidate Space
- Variable degrees: $d_v \in \{2, 3, 4, 5\}$, $\sum \lambda_d = 1.0$ on a $0.05$ grid.
  - Raw simplex grid: 1,771 distributions.
  - Filter 1 (P0 Forest Feasibility): $N_2 \le 183 \implies$ 547 distributions.
  - Filter 2 (Check Realizability): $d_{c,\max} \le 20 \implies$ **259 pre-registered candidates**.

---

## 2. Matched Empirical-P Density Evolution Protocol

### 2.1 Fixed Experimental Configuration
- **Channel Model**: Source-specific train empirical joint counts $N_{ab}$ from `load_v25_channel_counts()`, yielding true conditional posterior $P(A|B)$.
- **Field**: $\text{GF}(32)$, primitive polynomial $37$ (`0b100101`).
- **Sample Population**: $N_{\text{mc}} = 4000$ Monte Carlo samples per iteration.
- **Iteration Limit**: $I_{\max} = 60$ iterations.
- **Source Seeds**:
  - 1M: `[370101, 370102, 370103]`
  - 1p5M: `[370201, 370202, 370203]`
  - 2M: `[370301, 370302, 370303]`
- **Check Degree Distribution**: Computed using exact harmonic concentrated check degree formula for each source rate ($R = 1 - m/1024$).

### 2.2 Non-Saturated Trajectory Metrics
Because converging distributions reach numerical zero ($< 10^{-100}$), ranking relies on the convergence trajectory:

1. **Primary Ranking Metric**: Area Under the Entropy Trajectory ($\text{AUT}_{30}$):
   $$\text{AUT}_{30} = \sum_{t=0}^{30} H(t)$$
   where $H(t)$ is the mean conditional entropy (bits/symbol) at iteration $t$.
2. **Secondary Diagnostic Metrics**:
   - Early-iteration entropy: $H(t=5), H(t=10), H(t=15)$.
   - Threshold iterations: $T_{0.10} = \min \{t : H(t) \le 0.10\}$, $T_{0.01} = \min \{t : H(t) \le 0.01\}$.
   - Final entropy $H(I_{\max})$ (convergence flag only: $\text{converged} \iff H(60) < 10^{-4}$).

### 2.3 Reference Controls
- **Matched Baseline**: Regular $d_v=2$ ($\lambda = \{2: 1.0\}$) run with the identical $N=4000, I=60$, 3 seeds/source.
- **Exploratory Positive Control**: V36 candidate $\lambda = \{2: 0.85, 4: 0.15\}$ ($N_2=941$), evaluated under the same settings with flag `finite_inadmissible=True` (cannot be advanced or promoted).

---

## 3. Decision Logic & Stop Conditions

### 3.1 Per-Source Advance Gate
A candidate $C$ passes the V37-P1 DE gate if and only if:
1. $N_2(C) \le 183$ (P0 feasibility passed).
2. $C$ converges on all 3 sources across all 3 seeds ($H(60) < 10^{-4}$).
3. For **every source** $s \in \{\text{1M}, \text{1p5M}, \text{2M}\}$:
   $$\overline{\text{AUT}}_{30}(s, C) \le \overline{\text{AUT}}_{30}(s, \text{baseline}) \times 0.95 \quad (\ge 5\% \text{ improvement})$$

### 3.2 Deterministic Tie-Breaker
If multiple candidates pass:
1. Mean $\text{AUT}_{30}$ across all sources (ascending)
2. Mean $H(t=10)$ across all sources (ascending)
3. $N_2$ count (ascending, favoring lower degree-2 mass)
4. Canonical `candidate_id` string (lexicographic)

### 3.3 Terminal States
- `P1_DE_ADVANCE_CANDIDATE_FOUND`: Best candidate satisfies per-source $\ge 5\%$ improvement.
- `P1_NO_FINITE_FEASIBLE_DE_ADVANCE`: No candidate passing $N_2 \le 183$ achieves per-source advance.
- `P1_DE_EVIDENCE_INVALID`: Discrepancy in execution or missing required artifacts.
