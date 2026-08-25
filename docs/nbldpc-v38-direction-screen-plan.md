# V38-P0 Structured Low-Degree Architecture Triage Plan

**Cycle ID**: V38P0  
**Lifecycle State**: PLAN_CANDIDATE  
**Repository**: Placebo303/HD-QKD-Polar-pipeline  
**Branch**: formal-ir-mainline  
**Predecessor Cycle**: V37R1 (Terminal: P1_NO_FINITE_FEASIBLE_DE_ADVANCE, SHA 67da7c649646b9c9910d52489ae476ceae7fdb57)  
**Development Execution Authorization**: NOT_GRANTED  
**Formal Execution Authorization**: NOT_GRANTED  
**Scientific Promotion**: NOT_GRANTED  

---

## 1. Context and Objective

### 1.1 Problem Statement and Scope Boundaries
Cycle V37 established a definitive bounded negative result for unstructured single-edge irregular degree-distribution ensembles under the finite-length cycle-free forest constraint (N2 <= 183):
- **0 / 259** finite-feasible candidate distributions met the DE screening gate.
- **0 / 2,331** finite candidate DE runs converged (entropy remained ~ 4.96 to 5.0 bits/symbol at iteration 60).
- Top candidate AUT_30 values were +109% to +160% higher than the matched regular dv=2 baseline.

This large gap indicates a fundamental structural conflict: high code rate (R ~ 0.8125 to 0.8203) and N2 <= 183 force dbar_v >= 2.857 and check degrees dc in [16, 20], which in GF(32) cause check-node message convolution uncertainty to explode and stall early-iteration mutual information propagation.

**Explicitly Closed as Out-of-Scope**:
- Finer single-edge simplex grid searches (e.g., step=0.025 or step=0.01).
- Re-running V37 candidates with more seeds or higher iteration caps (I_max).
- Post-hoc relaxation of the V37 5% effect-size gate.

### 1.2 Objective of V38-P0
To perform a controlled, multi-lane architectural triage across three structured low-degree NB-LDPC design paradigms, identifying which architectural family produces a genuine finite-block error-reduction signal on the actual HD-QKD empirical channel before committing to a full optimization cycle.

---

## 2. Three Architecture Lanes

### Lane A: Near-dv=2 + GF(32) Cycle-Aware Edge Labeling
- **Hypothesis**: The strict cycle-free forest requirement (N2 <= 183) was overly restrictive. A low-column-weight topology close to dv=2 can be retained with graph cycles, provided non-zero GF(32) edge labels are algebraically selected to cancel harmful short cycles.
- **Core Construction**: Near-dv=2 binary support graphs where non-zero GF(32) edge weights are assigned to satisfy the non-zero determinant / full-rank cycle condition for lengths 4, 6, and 8 (and optionally length 10 if computationally tractable).
- **Support Reference**: The existing accepted V31 finite reference topology may be utilized as an immutable binary support reference for a label-only subexperiment.
- **Structural Metrics**: Short cycle counts (lengths 4, 6, 8), count and fraction of algebraically cancelled cycles by length, GF(32) matrix row rank, check degree distribution.
- **Scientific Scope Limit**: Isolates whether algebraic coefficient assignment alone can rescue low-degree finite graphs without changing binary support.

### Lane B: High-Rate eIRA / Protograph / MET-like Structured Low-Degree
- **Hypothesis**: Explicitly partitioning edges and variable nodes into structural classes (e.g., information variables vs. dual-diagonal parity accumulator chains) provides low effective check degrees and high convergence without uncontrolled random degree-2 cycle explosion.
- **Core Construction**: Minimal deterministic exact-rate prototypes (n=1024, m in {184, 190, 192}) incorporating a structured parity component (eIRA / dual-diagonal chain).
- **Edge and Variable Classes**: Explicitly separates information-variable edges, parity-variable edges, structured accumulator chain edges, and cross-coupling edges.
- **Structural Requirements**: Exact block dimensions, full row rank over GF(32), low maximum check degree, deterministic non-adaptive construction (no decoder-in-the-loop search).
- **Scientific Scope Limit**: Route-feasibility prototype only, not a fully optimized MET design.

### Lane C: SC-Inspired Spatially Banded Low-Degree NB-LDPC Prototype
- **Hypothesis**: Spatial coupling / band-diagonal parity structure localized along the block length provides threshold improvement and localized error protection.
- **Core Construction**: Minimal spatially banded / coupled low-column-weight GF(32) prototype at exact block dimensions (n=1024, m in {184, 190, 192}).
- **Structural Metrics**: Coupling / band width, check-degree profile by spatial position, short cycle counts, GF(32) row rank, boundary effects.
- **Fallback Rule**: If exact-rate construction requires ad-hoc puncturing or shortening that obscures comparison interpretability, Lane C will be designated STRUCTURAL_PROTOTYPE_NOT_READY rather than forcing an invalid matrix.
- **Scientific Scope Limit**: Spatially banded finite prototype only, not a claim of optimized SC-NB-LDPC threshold saturation.

---

## 3. Common Construction and Prototype Selection Protocol

### 3.1 Pre-Registered Construction Seeds
For each lane and source rate, exactly 3 deterministic construction seeds are pre-registered:

| Lane | Source 1M (m=184) | Source 1.5M (m=190) | Source 2M (m=192) |
| :--- | :---: | :---: | :---: |
| **Lane A** (Near-dv=2 + GF(32) Labels) | 381101, 381102, 381103 | 381201, 381202, 381203 | 381301, 381302, 381303 |
| **Lane B** (eIRA / Protograph / MET-like) | 382101, 382102, 382103 | 382201, 382202, 382203 | 382301, 382302, 382303 |
| **Lane C** (Spatially Banded Prototype) | 383101, 383102, 383103 | 383201, 383202, 383203 | 383301, 383302, 383303 |

### 3.2 Structural Prototype Selection (Prior to Decoding)
All 3 candidate prototypes per source and lane are generated and evaluated structurally **before** decoding. Decoder performance is strictly prohibited from participating in prototype selection.

**Ordered Structural Tie-Break Rule**:
1. Valid GF(32) full row rank (m = rank_GF32(H)).
2. Lowest number of uncancelled length-4 cycles.
3. Lowest number of uncancelled length-6 cycles.
4. Lowest number of uncancelled length-8 cycles.
5. Lowest maximum check degree (dc_max).
6. Lowest construction seed (deterministic tie-breaker).

---

## 4. Common Finite Evaluation Protocol

### 4.1 Fixed Development Blocks (Exact Repository Binding)
Evaluation uses the exact same 15 fixed development blocks established in V36:
- **Source 1M** (m=184): Seeds 360101, 360102, 360103, 360104, 360105 (5 blocks).
- **Source 1.5M** (m=190): Seeds 360201, 360202, 360203, 360204, 360205 (5 blocks).
- **Source 2M** (m=192): Seeds 360301, 360302, 360303, 360304, 360305 (5 blocks).
- **Total Workload**: 15 blocks total.

### 4.2 Decoder and Channel Setup
- **Field**: GF(32), primitive polynomial 37 (0b100101).
- **Channel**: Source-specific V25 TRAIN empirical count matrices with oracle-L1 conditioning (Alice x1 true prior conditioning).
- **Decoder**: Row-layered FFT-QSPA decoder, max_iter = 30, damping_alpha = 1.0.
- **Reference Baseline**: Accepted V31 QC baseline matrices (evaluated on all 15 blocks).
- **Maximum Workload**: 15 blocks (V31 baseline) + 15 blocks (Lane A winner) + 15 blocks (Lane B winner) + 15 blocks (Lane C winner) = **maximum 60 finite decoder runs**.

---

## 5. Metrics and Direction-Screen Decision Gate

### 5.1 Block-Level and Aggregate Metrics
- **Block-Level**: Exact L2 recovery (bool), initial symbol errors, final L2 residual symbol errors (iter 30), residual reduction, decoder iterations, status, runtime.
- **Aggregate**: Exact recovery count / 15, per-source exact count / 5, overall mean/median L2 residual, per-source mean/median residual, paired improve/equal/worsen counts vs V31 reference, paired relative residual delta, worst single-block degradation.

### 5.2 PROMISING_DIRECTION_SIGNAL Gate
A lane achieves PROMISING_DIRECTION_SIGNAL if and only if all of the following conditions are met:
1. **Structural Validity**: All 3 source matrices are structurally valid and achieve full row rank over GF(32).
2. **Non-Degradation**: No source has a worse median L2 residual than V31 by more than 5%.
3. **Error Reduction (At Least One)**:
   - **Criterion A**: Exact recovery count increases over V31 (i.e., >= 1 / 15).
   - **Criterion B**: Overall median L2 residual improves by >= 15% relative to V31.
   - **Criterion C**: At least 10 / 15 paired blocks improve and no more than 3 / 15 worsen.

---

## 6. Route Selection and Terminal States

- **V38_SINGLE_ROUTE_SIGNAL**: Exactly one lane satisfies PROMISING_DIRECTION_SIGNAL. That lane is designated as the primary architecture for full optimization in V39.
- **V38_MULTIPLE_ROUTE_SIGNALS**: Multiple lanes satisfy PROMISING_DIRECTION_SIGNAL. All surviving lanes are deepened in successor research without premature elimination.
- **V38_NO_ROUTE_SIGNAL**: No lane satisfies PROMISING_DIRECTION_SIGNAL. Indicates that none of the tested structured prototypes provide an advantage over the V31 baseline on these development blocks.
- **V38_DIRECTION_EVIDENCE_INVALID**: Construction failure, incomplete execution, or unresolvable protocol mismatch.

---

## 7. Scientific Boundaries and Prohibitions

### Allowed Claims upon Signal
- Lane A signal supports that cycle-aware GF(32) labeling on low-degree topology warrants deeper investigation.
- Lane B signal supports that eIRA / protograph / MET-like structured low-degree design warrants deeper investigation.
- Lane C signal supports that spatially banded structures warrant dedicated SC-NB-LDPC investigation.

### Strictly Forbidden Claims
- Do NOT claim frame error rate (FER), asymptotic threshold superiority, secret key rate, or security improvements.
- Do NOT claim formal exact recovery qualification from 15 development blocks.
- Do NOT claim general superiority or universal impossibility of any NB-LDPC class.
- Do NOT execute development DE, finite graph construction, or decoder runs during this planning phase.
