# Delta Specification: formal-ir-v37-finite-feasible-empirical-p-de-screening

## ADD: Section 37 — Finite-Feasible Empirical-P DE Candidate Screening

### 37.1 Finite-Length Feasibility Pre-Filter
1. Every degree distribution candidate $\lambda$ must be evaluated using `analyze_degree_feasibility` for $n=1024$ and $m \in \{184, 190, 192\}$.
2. Candidates with $N_2 > 183$ (the forest upper bound for $\min(m) = 184$) are strictly forbidden from candidate selection and promotion.
3. Candidates with realized maximum check degree $d_{c,\max} > 20$ across any of the three sources are excluded by the pre-registered search cap.

### 37.2 Matched Density Evolution Execution
1. Both the reference baseline ($\lambda = \{2: 1.0\}$), the exploratory positive control ($\lambda = \{2: 0.85, 4: 0.15\}$), and all candidate distributions must be evaluated under identical settings:
   - $N_{\text{mc}} = 4000$ Monte Carlo samples per iteration.
   - $I_{\max} = 60$ iterations.
   - Source-specific empirical $P(A|B)$ channel law from V25 train counts.
   - P1-A Screening seeds:
     - 1M: `[370101, 370102, 370103]`
     - 1p5M: `[370201, 370202, 370203]`
     - 2M: `[370301, 370302, 370303]`
   - P1-B Confirmation seeds (disjoint fresh seeds for candidate and baseline):
     - 1M: `[370111, 370112, 370113]`
     - 1p5M: `[370211, 370212, 370213]`
     - 2M: `[370311, 370312, 370313]`

### 37.3 Non-Saturated Metric & Advance Criteria
1. The primary ranking metric is the mean Area Under Entropy Trajectory over iterations $0 \le t \le 30$:
   $$\text{AUT}_{30} = \sum_{t=0}^{30} H(t)$$
2. A candidate achieves `P1_DE_ADVANCE_CANDIDATE_FOUND` if and only if:
   - $N_2 \le 183$ and $d_{c,\max} \le 20$.
   - All 3 sources converge across all seeds ($H(60) < 10^{-4}$).
   - In P1-A screening: $\overline{\text{AUT}}_{30,\text{screen}}(\text{candidate}) \le 0.95 \times \overline{\text{AUT}}_{30,\text{screen}}(\text{baseline})$ independently on each of the 3 sources.
   - In P1-B confirmation: $\overline{\text{AUT}}_{30,\text{confirm}}(\text{candidate}) \le 0.95 \times \overline{\text{AUT}}_{30,\text{confirm}}(\text{baseline})$ independently on each of the 3 sources.
3. The exploratory control $\lambda = \{2: 0.85, 4: 0.15\}$ is evaluated for trajectory comparison only and tagged `finite_inadmissible=True`; it cannot be selected as an advancing candidate.
