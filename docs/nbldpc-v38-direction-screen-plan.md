# V38-P0 Structured Low-Degree Architecture Triage Plan

**Cycle ID**: V38P0
**Lifecycle State**: PLAN_CANDIDATE
**Repository**: Placebo303/HD-QKD-Polar-pipeline
**Branch**: formal-ir-mainline
**Predecessor Cycle**: V37R1 (Terminal: P1_NO_FINITE_FEASIBLE_DE_ADVANCE)
**Predecessor Result SHA**: 67da7c64fa4150a66d020243d6292420903297fe
**Predecessor Result Review SHA**: cc1483cd568ca41fb686c40492f40b5eed81f06c
**Development Execution Authorization**: NOT_GRANTED
**Formal Execution Authorization**: NOT_GRANTED
**Scientific Promotion**: NOT_GRANTED

---

## 1. Context and Objective

### 1.1 Problem Statement and Scope Boundaries
Cycle V37 established a definitive bounded negative result for unstructured single-edge irregular degree-distribution ensembles on the 0.05-simplex under the finite-length cycle-free forest constraint (N2 <= 183):
- **Direct Evidence**: 0 / 259 finite-feasible candidate distributions met the DE screening gate; 0 / 2,331 finite candidate DE runs converged (H(60) >= 1e-4); all 259 candidates had positive AUT_30 deltas (+109% to +160%) relative to the regular dv=2 baseline; lowest-AUT_30 candidate was located on the lowest-dbar_v boundary (lambda_2=0.10, lambda_3=0.90).
- **Interpretation / Hypothesis**: These observations are consistent with a structural tension involving the finite N2 constraint, increased average variable degree (dbar_v >= 2.857), increased check degrees (dc in [16, 20]), and empirical-P GF(32) message-passing behavior. (Note: V37 did not conduct a controlled causal experiment isolating check degree as an independent variable).

**Explicitly Closed as Out-of-Scope**:
- Finer single-edge simplex grid searches (e.g., step=0.025 or step=0.01).
- Re-running V37 candidates with more seeds or higher iteration caps (I_max).
- Post-hoc relaxation of the V37 5% effect-size gate.

### 1.2 Objective of V38-P0
To perform a controlled, multi-lane architectural triage across three concrete structured low-degree NB-LDPC design paradigms, identifying which architectural family produces a genuine finite-block error-reduction signal on the actual HD-QKD empirical channel before committing to a full optimization cycle.

---

## 2. Common Structural Definitions and Validity Rules

### 2.1 Common Exact Dimensions and Rates
- **Block Length**: n = 1024 symbols.
- **Field**: GF(32), primitive polynomial 37 (0b100101).
- **Source Dimensions**:
  - Source 1M: m = 184 checks -> realized rate k/n = (1024 - 184)/1024 = 0.8203125.
  - Source 1.5M: m = 190 checks -> realized rate k/n = (1024 - 190)/1024 = 0.814453125.
  - Source 2M: m = 192 checks -> realized rate k/n = (1024 - 192)/1024 = 0.8125000.
- **Dimension / Rate Validity**: A matrix is valid iff shape(H) == (m, 1024) AND rank_GF32(H) == m.

### 2.2 Algebraic Cycle Degeneracy Definition (Direct Submatrix Rank)
For every simple Tanner cycle of support length 2r (where r in {2, 3, 4} for cycle lengths 4, 6, 8):
- Enumerate the cycle canonically without duplicate rotations or reversals.
- Extract the r x r GF(32) cycle-only submatrix H_cycle formed by the r check nodes, r variable nodes, and only the edges participating in that simple cycle.
- Classify the cycle as **ALGEBRAICALLY_NONDEGENERATE** iff rank_GF32(H_cycle) == r.
- Classify the cycle as **ALGEBRAICALLY_DEGENERATE** iff rank_GF32(H_cycle) < r.
- Record by length: support_cycle_count, algebraically_nondegenerate_count, algebraically_degenerate_count, nondegenerate_fraction.

### 2.3 Common Hard Structural Validity Requirements
A prototype matrix must strictly satisfy all of the following:
1. Exact matrix shape (m, 1024).
2. Full row rank over GF(32): rank_GF32(H) == m.
3. No isolated variable nodes (column weight >= 1) and no isolated check nodes (row weight >= 1).
4. No duplicate Tanner edges.
5. All nonzero entries belong to GF(32) \ {0}.
6. Maximum check degree dc_max <= 16 across all rows (frozen gate; not relaxed).
If any hard requirement is violated, the prototype is designated STRUCTURALLY_INVALID and is never passed to decoding.

### 2.4 Frozen PRNG & Substream Derivation Rules
- **RNG Engine**: numpy.random.Generator with numpy.random.PCG64 exclusively.
- **Substream Derivation**: For a base construction seed S, derive deterministic substreams using SeedSequence:
  - Support RNG: SeedSequence([S, 1])
  - Coefficient RNG: SeedSequence([S, 2])
  - Initial-label RNG: SeedSequence([S, 3])
- **No Hidden Seeds**: No Python hash(), no time/OS entropy, no random module.
- **Frozen Orderings**: At prototype initialization, generate exactly one seeded permutation of check indices within each eligible check set to resolve ties throughout placement (no new permutation draws per column).

---

## 3. Three Concrete Architecture Lanes

### 3.1 Lane A: Near-dv=2 + GF(32) Cycle-Aware Edge Labeling (Controlled Label-Only Isolation Experiment)
- **Purpose**: Controlled label-only isolation experiment to determine whether changing GF(32) coefficients alone on the existing low-degree V31 binary support provides finite-block benefit.
- **Binary Support Binding**: Lane A SHALL use the exact accepted V31 QC baseline binary support A_support(src) = (H_V31(src) != 0). The support matrix is bit-identical across all 3 Lane-A seeds (all column weights = 2, exactly 2,048 edges, row weights in [10, 12]).
- **Pre-Enumerated Support Cycles**: Enumerate canonical simple Tanner cycles of lengths 4, 6, 8 ONCE per frozen V31 support/source. Construct edge-to-incident-cycles lookup tables.
- **Coefficient Initialization**: Assign every existing edge a nonzero GF(32) entry from the PCG64 initial-label RNG (SeedSequence([S, 3])).
- **Deterministic Local Search Algorithm**:
  - **Lexicographic Objective**: (degenerate_4_cycles, degenerate_6_cycles, degenerate_8_cycles).
  - **Incremental Update**: When evaluating candidate coefficients for an edge, recompute degeneracy only for incident cycles; unaffected cycles retain cached states.
  - **Canonical Edge Order**: Fixed once by sorting edge index pairs (check_index, variable_index).
  - **Sweeps**: Exactly MAX_SWEEPS = 2. In each sweep, visit every edge once; test all 31 nonzero GF(32) integer values (1..31); select the coefficient minimizing the objective; ties choose the lowest GF(32) integer value.
  - Stop early if an entire sweep produces 0 coefficient updates.
  - Global GF(32) row rank is verified once after each full sweep and after the final sweep as a hard validity gate (not inside per-trial local objective).
- **Lane-Specific Validity**: Bit-identical support to V31, full GF(32) row rank, dc_max <= 16.

### 3.2 Lane B: eIRA-like Dual-Diagonal Structured NB-LDPC Prototype
- **Purpose**: Test whether structural partitioning of variable classes (information vs. parity accumulator chain) provides low effective check degrees and convergence without random degree-2 cycle explosion.
- **Matrix Partition**: H_B = [H_info | H_parity] where H_info is m x (1024 - m) and H_parity is m x m.
- **Parity Structure**: H_parity is fixed as a deterministic lower-bidiagonal matrix (diagonal entries = 1, first subdiagonal entries = 1, all others = 0). This guarantees rank_GF32(H_parity) == m and total parity edges = 2m - 1. (All existing parity entries = GF(32) element 1).
- **Total Support Edges & Degree Sanity**: Total edges = 2(1024 - m) + 2m - 1 = 2,047 edges. Mean check degrees: 1M = 11.125, 1.5M = 10.774, 2M = 10.661 (analytically compatible with dc_max <= 16).
- **Information Support Placement (Sequential for column j in 0..1024-m-1)**:
  - Initialize each check degree from H_parity.
  - **First Edge**: Eligible set = all m checks. Select check with minimum current total degree (ties: frozen check permutation).
  - **Second Edge**: Eligible set = all m checks except first selected check. Find minimum current total degree in eligible set. Among checks at that minimum degree, prefer candidates that create zero new support 4-cycles; ties choose earliest in frozen check permutation. (Never move to a higher-degree check solely to avoid a 4-cycle).
- **Information Coefficients**: Assign deterministic nonzero GF(32) entries from the coefficient RNG (SeedSequence([S, 2])). (No label search in Lane B).
- **Lane-Specific Validity**: All information columns degree 2, dual-diagonal parity pattern (parity endpoint degree 1 is an explicit structural feature of eIRA), full GF(32) row rank, dc_max <= 16.

### 3.3 Lane C: SC-Inspired Finite Spatially Banded Prototype
- **Purpose**: Test whether spatial localization / band-diagonal coupling provides a useful finite-block signal on the empirical channel. (SC-inspired finite prototype, not optimized SC-NB-LDPC).
- **Spatial Configuration**: L = 8 spatial positions (p = 0..7), coupling width w = 2.
- **Variable Allocation**: Exactly 128 variables per position (pos_v(j) = floor(8 * j / 1024)). Total edges = 1024 * 2 = 2,048. Mean check degrees: 1M = 11.130, 1.5M = 10.779, 2M = 10.667.
- **Positional Edge Load Vector**: LOAD_VECTOR = [128, 256, 256, 256, 256, 256, 256, 384] (pos 0 receives 128 edges; pos 1..6 receive 256 edges each; pos 7 receives 128 from pos 6 + 256 from pos 7 = 384 edges).
- **Frozen Check Allocations (Largest-Remainder Allocation by Edge Load)**:
  - **Source 1M (m=184)**: [12, 23, 23, 23, 23, 23, 23, 34] (12 + 6*23 + 34 = 184)
  - **Source 1.5M (m=190)**: [12, 24, 24, 24, 24, 24, 23, 35] (12 + 5*24 + 23 + 35 = 190)
  - **Source 2M (m=192)**: [12, 24, 24, 24, 24, 24, 24, 36] (12 + 6*24 + 36 = 192)
- **Capacity Sanity Gate (LANE_C_CAPACITY_FEASIBLE)**: For every position p in 0..7, require expected_support_edges(p) <= 16 * checks(p). (Max load/check at pos 7: 1M = 384/34 = 11.29; 1.5M = 384/35 = 10.97; 2M = 384/36 = 10.67; all <= 16).
- **Support Placement (Sequential for column j in 0..1023 at position p)**:
  - For p < 7: Edge 1 connects to check position p (minimum current total degree; zero-4-cycle preference within minimum-degree set; frozen check permutation). Edge 2 connects to check position p+1 (minimum current total degree; zero-4-cycle preference within minimum-degree set; frozen check permutation).
  - For p = 7: Both edges connect to distinct checks within check position 7. (Never select a higher-degree check solely to avoid a 4-cycle).
- **Coefficients**: Assign deterministic nonzero GF(32) entries from the coefficient RNG (SeedSequence([S, 2])). (No label search in Lane C).
- **Lane-Specific Validity**: Every variable column degree 2, exact spatial allocation within coupling window, full GF(32) row rank, dc_max <= 16.
- **Fallback Status**: If all 3 seeds fail structural requirements, the lane status is LANE_STRUCTURAL_NOT_READY (does NOT invalidate other lanes).

---

## 4. Construction Seeds and Prototype Selection Protocol

### 4.1 Pre-Registered Construction Seeds
Exactly 3 deterministic construction seeds are pre-registered per lane and source rate:

| Lane | Source 1M (m=184) | Source 1.5M (m=190) | Source 2M (m=192) |
| :--- | :---: | :---: | :---: |
| **Lane A** (Near-dv=2 + GF(32) Labels) | 381101, 381102, 381103 | 381201, 381202, 381203 | 381301, 381302, 381303 |
| **Lane B** (eIRA-like Dual-Diagonal) | 382101, 382102, 382103 | 382201, 382202, 382203 | 382301, 382302, 382303 |
| **Lane C** (Spatially Banded Prototype) | 383101, 383102, 383103 | 383201, 383202, 383203 | 383301, 383302, 383303 |

- **Seed Scope**: Each seed controls all stochastic/permutation choices for that prototype. No adaptive retries, no hidden seeds, exactly 3 attempts per lane/source (27 prototypes maximum across matrix).

### 4.2 Structural Prototype Selection (Prior to Decoding)
For each lane and source:
1. Filter out any prototypes that violate hard structural validity.
2. If 0 valid prototypes remain for a source, source status = STRUCTURAL_PROTOTYPE_NOT_READY.
3. If >= 1 valid prototype remains, select exactly one using the **Ordered Structural Tie-Break Rule**:
   - (1) Lower algebraically degenerate 4-cycle count
   - (2) Lower algebraically degenerate 6-cycle count
   - (3) Lower algebraically degenerate 8-cycle count
   - (4) Lower total support 4-cycle count
   - (5) Lower maximum check degree (dc_max)
   - (6) Lower construction seed (deterministic tie-breaker)
- **Constraint**: Decoder metrics MUST NOT participate in prototype selection.

---

## 5. Common Finite Evaluation Protocol

### 5.1 Fixed V36 Development Blocks (Exact Repository Binding)
Evaluation uses the exact same 15 fixed development blocks established in V36:
- **Source 1M** (m=184): Seeds 360101, 360102, 360103, 360104, 360105 (5 blocks).
- **Source 1.5M** (m=190): Seeds 360201, 360202, 360203, 360204, 360205 (5 blocks).
- **Source 2M** (m=192): Seeds 360301, 360302, 360303, 360304, 360305 (5 blocks).
- **Channel**: Source-specific V25 TRAIN empirical counts with oracle-L1 prior conditioning (factorize_f03, get_conditional_posterior_l2).

### 5.2 Frozen V31 Reference Binding and Policy
- **Artifact**: comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v31_20260820/run_01/matrix_payloads.json (packet_id: m1_16_n1024_n1024|QC-cyclic-projective).
- **Loader**: load_v31_qc_baseline_matrices() in comparison_bench.formal_ir.v35_algorithm_development.
- **Reference Benchmark Values (15 blocks, max_iter=30)**:
  - 1M: errors [166, 177, 171, 178, 162], mean = 170.8, median = 171.0, exact = 0/5.
  - 1.5M: errors [167, 199, 187, 148, 178], mean = 175.8, median = 178.0, exact = 0/5.
  - 2M: errors [164, 189, 183, 184, 169], mean = 177.8, median = 183.0, exact = 0/5.
  - Overall: mean = 174.80, median = 177.0, exact_count_reference = 0 / 15.
- **Reference Policy**: REUSE_EXISTING_V36_A3 (all decoder settings, counts, seeds, and prior are identical). Max new decoder runs = **45** (15 Lane A + 15 Lane B + 15 Lane C).

### 5.3 Decoder Setup
- Row-layered FFT-QSPA decoder, max_iter = 30, damping_alpha = 1.0, GF(32) polynomial 37.
- Note: Development diagnostic only; not Bob-only end-to-end reconciliation; not FER qualification.

---

## 6. Metrics and Direction-Screen Decision Gate

### 6.1 Block-Level and Aggregate Metrics
- **Block Record**: errors_initial, errors_final, exact_l2 (bool), syndrome_ok, iterations, status, runtime_s.
- **Derived**: paired_absolute_delta = errors_final_lane - errors_final_reference. Outcome = IMPROVE (delta < 0), EQUAL (delta == 0), WORSEN (delta > 0).
- **Aggregate per Ready Lane**: exact_recovery_count / 15, mean_errors_final, median_errors_final, improve_count, equal_count, worsen_count, worst_single_block_degradation.
- **Source-Specific Relative Delta**: median_delta_s = (median_errors_lane_s - median_errors_reference_s) / median_errors_reference_s.
- **Overall Median Improvement**: overall_median_improvement = (median_reference - median_lane) / median_reference.

### 6.2 Lane Status Definitions
- LANE_READY: All 3 source prototypes structurally valid.
- LANE_STRUCTURAL_NOT_READY: At least one source failed structural construction.
- LANE_EVALUATED_NO_SIGNAL: Evaluated on decoder, did not meet triage gate.
- LANE_PROMISING_DIRECTION_SIGNAL: Satisfied all triage conditions.

### 6.3 PROMISING_DIRECTION_SIGNAL Triage Gate
A READY lane achieves LANE_PROMISING_DIRECTION_SIGNAL iff:
1. **Structural Validity**: All 3 source matrices are structurally valid and full GF(32) row rank.
2. **Non-Degradation**: Every source satisfies median_delta_s <= +0.05 (no source median degrades by > 5%).
3. **Error Reduction (At Least One)**:
   - **Criterion A**: exact_count_lane > exact_count_reference (since reference = 0/15, equivalent to >= 1/15).
   - **Criterion B**: overall_median_improvement >= 0.15 (Formula threshold: 177 * 0.85 = 150.45; integer operational threshold: median_errors_lane <= 150 vs. baseline 177.0).
   - **Criterion C**: improve_count >= 10 AND worsen_count <= 3.

---

## 7. Route Selection and Overall Terminal States

- **V38_SINGLE_ROUTE_SIGNAL**: Exactly one lane satisfies LANE_PROMISING_DIRECTION_SIGNAL. That lane is recommended as eligible for successor-cycle planning/review in V39.
- **V38_MULTIPLE_ROUTE_SIGNALS**: Multiple lanes satisfy LANE_PROMISING_DIRECTION_SIGNAL. All surviving lanes are eligible for successor research without premature elimination.
- **V38_NO_ROUTE_SIGNAL**: No lane satisfies LANE_PROMISING_DIRECTION_SIGNAL, but >= 1 lane was validly evaluated. (Indicates that none of the tested prototypes provide an advantage over V31 baseline on these development blocks).
- **V38_NO_STRUCTURAL_PROTOTYPE_READY**: All 3 lanes are LANE_STRUCTURAL_NOT_READY. (Structural construction failure; not decoder evidence).
- **V38_DIRECTION_EVIDENCE_INVALID**: Shared experiment/provenance integrity failure (e.g., wrong blocks, corrupted baseline, decoder mismatch, seed misuse).

---

## 8. Implementation Test Matrix (Mandatory for Next Phase)

The future implementation phase must implement and pass the following 32 focused tests (T1-T32):
- **T1**: Construction seed determinism across all 3 lanes.
- **T2**: All generated matrices have exact dimensions (184x1024, 190x1024, 192x1024).
- **T3**: GF(32) row rank routine correctly validates known full-rank and rank-deficient test fixtures.
- **T4**: Canonical simple cycle enumeration correctly deduplicates rotations and reversals.
- **T5**: Cycle submatrix rank routine correctly classifies known nondegenerate and degenerate GF(32) fixtures.
- **T6**: Lane A binary support is bit-identical to frozen V31 baseline.
- **T7**: Lane A modifies nonzero GF(32) labels only.
- **T8**: Lane A local search strictly obeys the MAX_SWEEPS = 2 cap.
- **T9**: Lane B parity block is exact lower-bidiagonal full-rank matrix.
- **T10**: Lane B information columns all have degree exactly 2.
- **T11**: Lane C all variable columns have degree exactly 2.
- **T12**: Lane C all edges strictly respect the L=8, w=2 spatial coupling window.
- **T13**: No hidden construction retry beyond the 3 pre-registered seeds.
- **T14**: Structural prototype selection strictly ignores decoder performance.
- **T15**: A structurally invalid lane/source is never passed to decoding.
- **T16**: One lane being STRUCTURAL_NOT_READY does not invalidate execution of other READY lanes.
- **T17**: Exact V36 A3 block seeds are used (360101-360105, 360201-360205, 360301-360305).
- **T18**: PROMISING_DIRECTION_SIGNAL branch tests (Criterion A, B, C, and >5% degradation failure).
- **T19**: Zero baseline median relative-delta division-by-zero protection.
- **T20**: Pipeline correctly follows all overall terminal-state branches (SINGLE_ROUTE, MULTIPLE_ROUTE, NO_ROUTE, NO_STRUCTURAL_READY, INVALID).
- **T21**: SHA provenance safety: no nonexistent predecessor SHA.
- **T22**: Lane C positional capacity calculation matches frozen vectors (1M: [12,23,23,23,23,23,23,34], 1.5M: [12,24,24,24,24,24,23,35], 2M: [12,24,24,24,24,24,24,36]).
- **T23**: Lane C old equal-allocation fixture correctly fails positional capacity sanity gate.
- **T24**: Lane C dc_max can never pass a matrix violating positional capacity.
- **T25**: Lane B total support edge count == 2047.
- **T26**: Lane B lower-bidiagonal parity block guarantees rank m.
- **T27**: PRNG uses PCG64 only and no hidden entropy.
- **T28**: Substream derivation is deterministic via SeedSequence.
- **T29**: Lane A cached incremental cycle objective exactly matches brute-force full recomputation on small fixtures.
- **T30**: Lane A final support remains bit-identical to V31.
- **T31**: Lane A global GF(32) rank checked after sweep/final result, not for every coefficient trial.
- **T32**: Criterion-B integer operational threshold (<=150) is correctly interpreted.

---

## 9. Scientific Boundaries and Prohibitions

### Allowed Claims upon Signal
- Lane A signal supports that cycle-aware GF(32) labeling on low-degree support merits deeper study. (Do NOT claim graph cycles were removed or that all degree-2 cycles are safe).
- Lane B signal supports that the tested eIRA-like dual-diagonal prototype merits deeper study. (Do NOT call this a general MET-LDPC or optimized protograph result).
- Lane C signal supports that the tested L=8, w=2 spatially banded prototype merits deeper study. (Do NOT claim SC threshold saturation or asymptotic SC gain).

### Strictly Forbidden Claims
- Do NOT claim frame error rate (FER), asymptotic threshold superiority, secret key rate, or security improvements.
- Do NOT claim formal exact recovery qualification from 15 development blocks.
- Do NOT claim general superiority or universal impossibility of any NB-LDPC class.
- Do NOT execute development DE, finite graph construction, or decoder runs during this planning phase.
