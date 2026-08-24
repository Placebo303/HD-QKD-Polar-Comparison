# OpenSpec Tasks: formal-ir-v37-finite-feasible-empirical-p-de-screening

**Lifecycle**: PLAN_CANDIDATE  
**State**: PLAN_FROZEN_PENDING_REVIEW (No execution authorized)

---

## Task Matrix

- [ ] **Task 1: Plan Review & Scientific Freeze**
  - Verify mathematical bounds ($N_2 \le 183 \implies \bar{d}_v \ge 2.8213$).
  - Pre-register candidate grid (259 finite-feasible candidates with $N_2 \le 183, d_{c,\max} \le 20$).
  - Freeze matched DE evaluation parameters ($N=4000, I=60$, 3 seeds/source).
  - Freeze primary trajectory metric ($\text{AUT}_{30}$) and per-source $\ge 5\%$ threshold.

- [ ] **Task 2: P1 Core Module Implementation (Pending Approval)**
  - Implement `comparison_bench/src/comparison_bench/formal_ir/v37_de_screening.py`.
  - Implement grid generator incorporating `v37_degree_feasibility` filter.
  - Implement matched trajectory-recording empirical-P MC-DE runner.
  - Implement per-source ranking, $\text{AUT}_{30}$ calculation, and deterministic tie-breaker.

- [ ] **Task 3: P1 CLI & Reporting Implementation (Pending Approval)**
  - Implement `comparison_bench/src/comparison_bench/cli/run_v37_de_screening.py`.
  - Generate structured JSON summary and CSV candidate trajectory metrics.

- [ ] **Task 4: P1 Unit Test Suite (Pending Approval)**
  - Implement `comparison_bench/tests/test_v37_de_screening.py`.
  - Validate candidate filtering, exact trajectory calculation, deterministic ranking, and tie-breakers.

- [ ] **Task 5: Authorized Development Execution & Review (Pending Explicit Authorization)**
  - Run matched DE screening on 259 candidates + baseline + V36 positive control.
  - Perform read-only verification of results.
  - Output milestone report and determine terminal state (`P1_DE_ADVANCE_CANDIDATE_FOUND` or `P1_NO_FINITE_FEASIBLE_DE_ADVANCE`).
