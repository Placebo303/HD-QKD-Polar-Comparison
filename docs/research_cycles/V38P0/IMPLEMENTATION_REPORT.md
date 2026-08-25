# V38-P0 Implementation Report: Structured Low-Degree Architecture Triage

**Cycle ID**: V38P0  
**Lifecycle State**: `IMPLEMENTATION_CANDIDATE`  
**Repository**: `Placebo303/HD-QKD-Polar-pipeline`  
**Branch**: `formal-ir-mainline`  
**Accepted Plan SHA**: `1b3fb4b8d0fa14c127ab895b1bbb21eb77f3414d`  
**Plan Acceptance SHA**: `dbb6ea8cf102bd4ed9c5beb68c1d7432ee2005d6`  
**Predecessor Result SHA**: `67da7c64fa4150a66d020243d6292420903297fe`  
**Predecessor Review SHA**: `cc1483cd568ca41fb686c40492f40b5eed81f06c`  
**Development Execution Authorization**: `NOT_AUTHORIZED` (`development_execution_authorized: false`)  
**Formal Execution Authorization**: `NOT_AUTHORIZED` (`formal_execution_authorized: false`)  
**Scientific Promotion**: `NOT_GRANTED` (`scientific_promotion: false`)  

---

## 1. Implementation Summary

The accepted V38-P0 Structured Low-Degree Architecture Triage plan has been implemented in a dedicated additive module:
[`comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py`](file:///D:/Code/HD-QKD_Polar_Comparison/comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py).

### Core Components Implemented

1. **Deterministic PRNG & Sampling Contract**:
   - `get_substream_generator(base_seed, stream_id)`: Derived via `numpy.random.SeedSequence([S, 1])` (support), `SeedSequence([S, 2])` (coefficients), and `SeedSequence([S, 3])` (initial labels).
   - `sample_uniform_gf32_nonzero(rng, size)`: Uniform integer sampling from $\{1, 2, \dots, 31\}$ via `rng.integers(low=1, high=32, endpoint=False)`. Zero is never sampled.
   - `get_canonical_support_edges(binary_support)`: Sorted lexicographically `(check_index, variable_index)` for canonical coefficient assignments.

2. **Canonical Cycle Enumeration & Algebraic Degeneracy Classifier**:
   - `enumerate_canonical_simple_cycles(binary_support)`: Canonical simple cycles of lengths 4, 6, and 8 without duplicate rotations/reversals. Builds edge-to-incident-cycle lookup tables.
   - `compute_cycle_submatrix_rank(cycle, H)`: Constructs the $r \times r$ cycle-only submatrix over $\text{GF}(32)$ and computes its rank via direct Gaussian elimination.
   - `classify_cycle_algebraic_degeneracy(cycle, H)`: Classifies as `ALGEBRAICALLY_NONDEGENERATE` iff $\text{rank}_{\text{GF}(32)}(H_{\text{cycle}}) == r$, and `ALGEBRAICALLY_DEGENERATE` iff rank $< r$.

3. **Lane A (Controlled Label-Only Isolation Experiment)**:
   - `construct_lane_a_prototype(source, seed, max_sweeps=2)`: Uses exact frozen V31 binary support ($A_{\text{support}} = (H_{V31} \ne 0)$); pre-enumerates cycles; initializes labels in canonical edge order; performs incremental local search over `(degenerate_4, degenerate_6, degenerate_8)` with `MAX_SWEEPS = 2`; records `rank_after_sweep_1` as diagnostic; applies final GF(32) rank gate at completion.

4. **Lane B (High-Rate eIRA-like Dual-Diagonal Prototype)**:
   - `construct_lane_b_prototype(source, seed)`: $H = [H_{\text{info}} \mid H_{\text{parity}}]$; $H_{\text{parity}}$ is $m \times m$ lower-bidiagonal with unit entries (rank $m$, total parity edges $2m-1$); $H_{\text{info}}$ has degree 2 per column; sequential placement with degree-balancing prioritized over 4-cycle avoidance; total support edges = 2,047; coefficients assigned after support completion.

5. **Lane C (SC-Inspired Spatially Banded Prototype)**:
   - `construct_lane_c_prototype(source, seed)`: $L=8, w=2$, 128 variables per position; check allocation via edge-load vector `[128, 256, 256, 256, 256, 256, 256, 384]` (`[12, 23..23, 34]` for 1M; `[12, 24..24, 23, 35]` for 1.5M; `[12, 24..24, 36]` for 2M); analytical capacity gate (`LANE_C_CAPACITY_FEASIBLE`); position permutations generated sequentially in order $0..7$; total support edges = 2,048; coefficients assigned after support completion.

6. **Structural Prototype Selection**:
   - `select_structural_winner(prototypes)`: Filters valid candidates first; applies ordered tie-break: (1) lower degenerate 4-cycles, (2) lower degenerate 6-cycles, (3) lower degenerate 8-cycles, (4) lower support 4-cycles, (5) lower $d_{c,\max}$, (6) lower construction seed. Decoder metrics strictly excluded.

7. **Finite Development Evaluation & Triage Gates**:
   - `evaluate_single_block(...)`: Row-layered FFT-QSPA decoder ($I_{\max}=30, \alpha=1.0$, GF(32), oracle-L1 prior).
   - `aggregate_lane_results(...)`: Reuses frozen V36 A3 baseline ($0/15$ exact, median residual = 177).
   - `evaluate_triage_gate(...)`: Evaluates `LANE_PROMISING_DIRECTION_SIGNAL` (non-degradation $\le +0.05$ on all sources; exact count $> 0$, overall median $\le 150$, or improve $\ge 10$ and worsen $\le 3$).
   - `determine_v38_terminal_state(...)`: Evaluates `V38_SINGLE_ROUTE_SIGNAL`, `V38_MULTIPLE_ROUTE_SIGNALS`, `V38_NO_ROUTE_SIGNAL`, `V38_NO_STRUCTURAL_PROTOTYPE_READY`, `V38_DIRECTION_EVIDENCE_INVALID`.

---

## 2. Test Matrix Execution & Verification (T1 - T41)

All 41 implementation contract items and safety assertions are verified in [`comparison_bench/tests/test_v38_architecture_triage.py`](file:///D:/Code/HD-QKD_Polar_Comparison/comparison_bench/tests/test_v38_architecture_triage.py):

| Test ID | Description | Result |
| :--- | :--- | :---: |
| **T1** | Construction seed determinism across all 3 lanes | **PASS** |
| **T2** | All generated matrices have exact dimensions (184x1024, 190x1024, 192x1024) | **PASS** |
| **T3** | GF(32) row rank routine validates full-rank and rank-deficient fixtures | **PASS** |
| **T4** | Canonical simple cycle enumeration correctly deduplicates rotations/reversals | **PASS** |
| **T5** | Cycle submatrix rank classifies nondegenerate vs degenerate fixtures | **PASS** |
| **T6** | Lane A binary support is bit-identical to frozen V31 baseline | **PASS** |
| **T7** | Lane A modifies nonzero GF(32) labels only | **PASS** |
| **T8** | Lane A local search strictly obeys MAX_SWEEPS = 2 cap | **PASS** |
| **T9** | Lane B parity block is exact unit lower-bidiagonal matrix | **PASS** |
| **T10** | Lane B information columns all have degree exactly 2 | **PASS** |
| **T11** | Lane C all variable columns have degree exactly 2 | **PASS** |
| **T12** | Lane C all edges strictly respect L=8, w=2 coupling window | **PASS** |
| **T13** | No hidden construction retry beyond the 3 pre-registered seeds | **PASS** |
| **T14** | Structural prototype selection strictly ignores decoder performance | **PASS** |
| **T15** | Structurally invalid prototype is never selected | **PASS** |
| **T16** | One lane being STRUCTURAL_NOT_READY does not invalidate other READY lanes | **PASS** |
| **T17** | Exact V36 A3 block seeds are preserved (360101-360105, etc.) | **PASS** |
| **T18** | PROMISING_DIRECTION_SIGNAL branch tests (Crit A, B, C, >5% degradation failure) | **PASS** |
| **T19** | Zero baseline median relative-delta division-by-zero protection | **PASS** |
| **T20** | Pipeline correctly follows all overall terminal-state branches | **PASS** |
| **T21** | SHA provenance safety: verified predecessor SHAs exist | **PASS** |
| **T22** | Lane C positional capacity calculation matches frozen vectors | **PASS** |
| **T23** | Lane C old equal-allocation fixture correctly fails capacity sanity gate | **PASS** |
| **T24** | Lane C dc_max limit enforcement | **PASS** |
| **T25** | Lane B total support edge count == 2047 | **PASS** |
| **T26** | Lane B lower-bidiagonal parity block guarantees rank m | **PASS** |
| **T27** | PRNG uses PCG64 only and no hidden entropy | **PASS** |
| **T28** | Substream derivation is deterministic via SeedSequence | **PASS** |
| **T29** | Lane A cached incremental cycle objective matches brute-force recomputation | **PASS** |
| **T30** | Lane A final support remains bit-identical to V31 | **PASS** |
| **T31** | Lane A sweep-1 rank diagnostic behavior | **PASS** |
| **T32** | Criterion-B integer operational threshold (<=150) correctly interpreted | **PASS** |
| **T33** | Uniform GF(32) coefficient sampler values in 1..31 | **PASS** |
| **T34** | Canonical coefficient edge ordering independence | **PASS** |
| **T35** | Lane B parity coefficients consume zero coefficient-RNG draws | **PASS** |
| **T36** | Lane B support fully generated before H_info coefficient assignment | **PASS** |
| **T37** | Lane C support fully generated before coefficient assignment | **PASS** |
| **T38** | Lane C position permutations generated in order 0..7 and reused unchanged | **PASS** |
| **T39** | Lane A sweep-1 rank deficiency does not prematurely invalidate prototype | **PASS** |
| **T40** | Lane A final rank deficiency invalidates prototype | **PASS** |
| **T41** | Lane A zero-change early stop performs final-rank validation | **PASS** |
| **Safety** | Production seeds protected; fake_runner evaluation supported | **PASS** |

**Pytest Summary**: `26 passed in 247.43s` (with zero errors, zero warnings).

---

## 3. Execution Boundary & Non-Execution Assertion

- **Production Seeds Executed**: `0 / 27` (No production candidate from `381xxx`, `382xxx`, `383xxx` was constructed or evaluated).
- **Production Structural Prototypes Generated**: `0`
- **Production Decoder Runs**: `0 / 45`
- **Development Execution Authorization**: `NOT_GRANTED`
- **Formal Execution Authorization**: `NOT_GRANTED`
- **Scientific Promotion**: `NOT_GRANTED`
