# OpenSpec Tasks: formal-ir-v37-finite-feasible-empirical-p-de-screening

**Lifecycle**: PLAN_CANDIDATE
**State**: PLAN_FROZEN_PENDING_REVIEW (No execution authorized)

---

## Task Matrix

- [ ] **Task 1: Plan Review & Scientific Freeze**
  - Verify mathematical bounds ($N_2 \le 183 \implies \bar{d}_v \ge 2.8213$; cap $d_{c,\max} \le 20$).
  - Pre-register candidate grid (259 finite-feasible candidates with $N_2 \le 183, d_{c,\max} \le 20$).
  - Freeze matched DE evaluation parameters ($N=4000, I=60$, screening seeds and disjoint confirmation seeds).
  - Freeze primary trajectory metric ($\text{AUT}_{30}$), effect-size threshold ($\ge 5\%$), and two-stage screening/confirmation decision logic.

- [ ] **Task 2: P1 Core Module Implementation (Pending Approval)**
  - Implement `comparison_bench/src/comparison_bench/formal_ir/v37_de_screening.py`.
  - Implement grid generator incorporating `v37_degree_feasibility` filter and $d_{c,\max} \le 20$ cap.
  - Implement matched trajectory-recording empirical-P MC-DE runner.
  - Implement per-source ranking, $\text{AUT}_{30}$ calculation, deterministic tie-breaker, and confirmation protocol.

- [ ] **Task 3: P1 CLI & Reporting Implementation (Pending Approval)**
  - Implement `comparison_bench/src/comparison_bench/cli/run_v37_de_screening.py`.
  - Generate structured JSON summary, candidate trajectory CSVs, and screening/confirmation comparisons.

- [ ] **Task 4: P1 Unit Test Suite (Pending Approval)**
  - Implement `comparison_bench/tests/test_v37_de_screening.py`.
  - Validate candidate filtering, exact trajectory calculation, deterministic ranking, tie-breakers, and disjoint confirmation logic.

- [ ] **Task 5: Authorized Development Execution & Review (Pending Explicit Authorization)**
  - Run P1-A screening on 259 candidates + baseline + V36 positive control (2,349 runs).
  - Run P1-B confirmation on selected candidate + baseline using fresh disjoint seeds (18 runs).
  - Perform read-only verification of results.
  - Output milestone report and determine terminal state (`P1_DE_ADVANCE_CANDIDATE_FOUND`, `P1_SCREEN_SIGNAL_NOT_CONFIRMED`, or `P1_NO_FINITE_FEASIBLE_DE_ADVANCE`).
