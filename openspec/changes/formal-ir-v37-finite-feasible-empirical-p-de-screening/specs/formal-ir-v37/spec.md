# Delta Specification: formal-ir-v37-finite-feasible-empirical-p-de-screening

## ADD: Section 37 — Finite-Feasible Empirical-P DE Candidate Screening

### 37.1 Finite-Length Feasibility Pre-Filter
1. Every degree distribution candidate $\lambda$ must be evaluated using `analyze_degree_feasibility` for $n=1024$ and $m \in \{184, 190, 192\}$.
2. Candidates with $N_2 > 183$ (the forest upper bound for $\min(m) = 184$) are strictly forbidden from candidate selection and promotion.
3. Candidates with realized maximum check degree $d_{c,\max} > 20$ across any of the three sources are excluded.

### 37.2 Matched Density Evolution Execution
1. Both the reference baseline ($\lambda = \{2: 1.0\}$), the exploratory positive control ($\lambda = \{2: 0.85, 4: 0.15\}$), and all candidate distributions must be evaluated under identical settings:
   - $N_{\text{mc}} = 4000$ Monte Carlo samples per iteration.
   - $I_{\max} = 60$ iterations.
   - Three independent pre-registered seeds per source:
     - 1M: `[370101, 370102, 370103]`
     - 1p5M: `[370201, 370202, 370203]`
     - 2M: `[370301, 370302, 370303]`
   - Source-specific empirical $P(A|B)$ channel law from V25 train counts.

### 37.3 Non-Saturated Metric & Advance Criteria
1. The primary ranking metric is the mean Area Under Entropy Trajectory over iterations $0 \le t \le 30$:
   $$\text{AUT}_{30} = \sum_{t=0}^{30} H(t)$$
2. A candidate achieves `P1_DE_ADVANCE_CANDIDATE_FOUND` if and only if:
   - $N_2 \le 183$
   - All 3 sources converge across all 3 seeds ($H(60) < 10^{-4}$)
   - $\text{AUT}_{30}(\text{candidate}) \le 0.95 \times \text{AUT}_{30}(\text{baseline})$ independently on each of the 3 sources (1M, 1p5M, 2M).
3. The exploratory control $\lambda = \{2: 0.85, 4: 0.15\}$ is evaluated for trajectory comparison only and tagged `finite_inadmissible=True`; it cannot be selected as an advancing candidate.
