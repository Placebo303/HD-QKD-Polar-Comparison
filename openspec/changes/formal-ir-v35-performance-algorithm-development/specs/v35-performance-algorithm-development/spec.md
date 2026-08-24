# OpenSpec Spec: v35-performance-algorithm-development

## Requirement 1: Progressive Four-Stage Exploration

### Scenario 1.1: Automated Stage Progression
- **GIVEN** 15 empirical development blocks (3 sources × 5 seeds: `350101..350105`, `350201..350205`, `350301..350305`) drawn from V25 empirical joint laws,
- **WHEN** the V35 development runner executes,
- **THEN** Stage A1 (Decoder Schedules on baseline graph), Stage A2 (Empirical-P Protograph), and Stage A3 (Rate-Adaptive Incremental Syndrome) execute sequentially on all 15 blocks.

### Scenario 1.2: Conditional Stage A4 Trigger
- **GIVEN** execution of Stage A3 completes across all 15 blocks,
- **WHEN** any of the 3 sources (1M, 1.5M, 2M) achieves fewer than 3 exact recoveries out of 5 blocks,
- **THEN** Stage A4 (Binary Multilevel Coding Fallback) MUST execute across all 15 blocks.
- **AND** if all 3 sources achieve $\ge 3/5$ exact recoveries with 0 false accepts, Stage A4 is marked `SKIPPED_NOT_NEEDED`.

---

## Requirement 2: Decoder Numerical Correctness and Integrity

### Scenario 2.1: Message Normalization and Finite Bound Invariants
- **GIVEN** any FFT-QSPA schedule (Flooding, Row-Layered, Damped Row-Layered $\alpha=0.5$),
- **WHEN** check-to-variable and variable-to-check updates are performed,
- **THEN** probability-domain messages MUST satisfy $\sum_{s=0}^{31} P(s) = 1.0 \pm 10^{-12}$, $P(s) \ge 0$, and log-domain messages MUST be finite and non-NaN.

### Scenario 2.2: Syndrome Check Strict Verification
- **GIVEN** a decoded symbol candidate $\hat{x} \in \text{GF}(32)^N$ or bit candidate $\hat{\mathbf{b}}$,
- **WHEN** checking convergence,
- **THEN** `syndrome_ok` MUST be `True` if and only if $H \hat{x} \equiv s \pmod{\text{GF}(32)}$ (or $H \hat{\mathbf{b}} \equiv s \pmod 2$).

---

## Requirement 3: Protograph & Deterministic Lifting Invariants

### Scenario 3.1: Variable Degree Distribution and Chains
- **GIVEN** the Stage A2 protograph base matrix $B$,
- **WHEN** computing graph metrics,
- **THEN** variable node degrees MUST be in $[2, 5]$, average variable degree $\bar{d}_v \in [2.2, 3.2]$, fraction of degree-2 edges $\lambda_2 \le 0.35$, with zero degree-1 variable nodes ($\lambda_1 = 0$), and no protograph cycles consisting solely of degree-2 variable nodes.

### Scenario 3.2: Girth and Cycle Invariants
- **GIVEN** the lifted parity-check matrix $H \in \text{GF}(32)^{M \times 1024}$ ($Z=32$),
- **WHEN** computing Tanner graph cycles,
- **THEN** the graph MUST contain zero parallel edges and zero 4-cycles (girth $\ge 6$).

---

## Requirement 4: Incremental Syndrome Hierarchy and State Transfer

### Scenario 4.1: Nested Parity-Check Hierarchy
- **GIVEN** incremental redundancy stages $S0, S1, S2, S3$,
- **WHEN** evaluating parity-check matrices,
- **THEN** $H_{S0} \subset H_{S1} \subset H_{S2} \subset H_{S3}$ with syndrome bit disclosures increasing by exactly $+0, +40, +80, +160$ bits.

### Scenario 4.2: Warm-Started Message Passing and Early Stopping
- **GIVEN** transition from stage $S_k \to S_{k+1}$,
- **WHEN** initializing the decoder at stage $S_{k+1}$,
- **THEN** the converged variable belief vector from stage $S_k$ MUST be preserved as the initial prior, and decoding MUST terminate immediately upon verified exact frame recovery.

---

## Requirement 5: Non-Destructive Boundary & Terminal State Declaration

### Scenario 5.1: Zero False Accepts Invariant
- **GIVEN** all evaluated blocks in the official run,
- **WHEN** comparing `tag_ok` and `exact_l2`,
- **THEN** `false_accept` ($\text{tag\_ok} \land \neg\text{exact\_l2}$) MUST be exactly 0.

### Scenario 5.2: Definitive Terminal Status
- **GIVEN** pipeline execution completion,
- **WHEN** writing output manifests,
- **THEN** exactly one terminal status MUST be declared from: `NB_CANDIDATE_DEVELOPMENT_READY`, `BINARY_MLC_CANDIDATE_DEVELOPMENT_READY`, `NO_CANDIDATE_SUCCESS`.
