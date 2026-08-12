# V10 Literature Crosswalk

## 1. Müller et al. — "Efficient Information Reconciliation for High-Dimensional QKD"
**Quantum Inf Process 23, 195 (2024), arXiv:2307.02225**

| Concept | V10 Location | Notes |
|---------|-------------|-------|
| QSC prior P(e=0)=1−p, P(e=a)=p/(q−1) | `nonbinary_v10_common.py` `qsc_channel_message` | Same formulation as V8/V9 |
| Syndrome Slepian–Wolf: Alice publishes s=Hx | `nonbinary_v10_fftqspa.py` error-domain | Design §10.1; same as V8/V9 accepted algebra |
| Edge-perspective λ/ρ degree distributions | `nonbinary_v10_de.py` `lambda_validate`, design §2.1 | K=8 representation consistent with Müller's sparse multi-degree approach |
| MC-DE with full-vector messages | Reuses V8/V9 MC-DE semantics (test-only oracle) | V10's DE optimizer calls MC-DE as fitness evaluator |
| DE optimization of λ | `nonbinary_v10_de.py` DE/rand/1/bin | V10 adds general DE instead of Müller's heuristic search; K=8 matches Müller's design space |
| Concentrated check distribution ρ at adjacent degrees | `nonbinary_v10_common.py` V8-60 formula | Same harmonic-exact formula as V8-60 corrected |
| Log-domain FFT-SPA decoder | `nonbinary_v10_fftqspa.py` | Design §10; flooding schedule per Müller reference |
| Finite-length PEG construction | `nonbinary_v10_peg.py` | Design §9; Müller's irregular PEG approach |
| Leakage L=m·log₂(q), efficiency β=L/(n·H(p)) | `nonbinary_v10_common.py` | Design §13; exact hard caps |
| **Difference**: Müller uses heuristic search + MC-DE; V10 adds formal DE/rand/1/bin | DE is a stronger optimizer, not a deviation from Müller's representation | — |
| **Difference**: Müller's PE search space is wider; V10's K=8 is a bounded sparse subset | The 8-degree constraint is Müller-consistent (paper uses 7 degrees for q=4) | — |

## 2. Storn & Price — "Differential Evolution"
**JOGO 11, 341–359 (1997), DOI 10.1023/A:1008202821328**

| Concept | V10 Location | Notes |
|---------|-------------|-------|
| DE/rand/1/bin variant | `nonbinary_v10_de.py` mutation/crossover | Frozen variant; design §3.1 |
| Standard DE parameters F, CR, pop_size, generations | `pre_run_plan.json` | Frozen before formal results |
| Binomial crossover | `nonbinary_v10_de.py` | Implemented in NumPy |
| Deterministic tie-break (replace only on strictly better) | `nonbinary_v10_de.py` selection | Project requirement; not in original DE |
| **Difference**: V10 adds hierarchical lexicographic objective instead of scalar | Required for ensemble optimization with gate screening | — |
| **Difference**: V10 adds checkpoint/resume | Engineering requirement | — |

## 3. Declercq & Fossorier — "Decoding Algorithms for NB-LDPC over GF(q)"
**IEEE TCOM 55, 633–643 (2007), DOI 10.1109/TCOMM.2007.894088**

| Concept | V10 Location | Notes |
|---------|-------------|-------|
| Fourier-domain QSPA (FFT-QSPA) | `nonbinary_v10_fftqspa.py` check_update_fft | Design §10.3 |
| GF(q) edge-label coefficient permutations | `nonbinary_v10_fftqspa.py` coefficient permutation | Multiplicative group action via GF2mField lookup tables |
| WHT-based check convolution | `nonbinary_v10_fftqspa.py` fwht_batched | XOR-order WHT per V9 accepted convention |
| Syndrome shift in check output | `nonbinary_v10_fftqspa.py` syndrome_shift | GF addition at convolution output |
| Probability normalization | `nonbinary_v10_fftqspa.py` stable log-normalization | Log-sum-exp with probability floor 1e-15 |
| **Not implemented**: EMS (Extended Min-Sum) | Deferred; listed as future complexity comparison only | EMS is explicitly forbidden in V10 scientific lane |
| **Not implemented**: ADMM, list decoding | Forbidden per design §10.6 | — |
| **Difference**: flooding schedule only (no layered in V10 science lane) | Layered deferred to future performance optimization | Design §10.2 |

## 4. Bennatan & Burshtein — "Design and Analysis of Nonbinary LDPC Codes for Arbitrary Discrete-Memoryless Channels"
**arXiv:cs/0511040**

| Concept | V10 Location | Notes |
|---------|-------------|-------|
| Random nonzero edge labels | `nonbinary_v10_peg.py` edge label assignment | Uniform GF(1024)\{0} from frozen seed |
| Nonbinary channel symmetry for ensemble analysis | Reused in DE objective (channel symmetry) | QSC satisfies the paper's symmetry conditions |
| Ensemble weight enumerator | Not directly implemented | V10 uses MC-DE, not closed-form enumerator |
| **Difference**: Bennatan–Burshtein analysis is theoretical; V10 is implementation | Practical PEG construction, not asymptotic bounds | — |

## 5. Hu, Eleftheriou & Arnold — "Regular and Irregular Progressive Edge-Growth Tanner Graphs"
**IEEE TIT, DOI 10.1109/TIT.2004.839541**

| Concept | V10 Location | Notes |
|---------|-------------|-------|
| PEG construction (progressive edge growth) | `nonbinary_v10_peg.py` | Design §9.4 |
| Local girth maximization | Primary PEG objective | Select check maximizing shortest cycle length |
| ACE (Approximate Cycle EMD) | Secondary tie-break score | ACE-like metric for extrinsic message degree |
| Deterministic tie-break | Seeded-RNG permutation-based tie-break (amended 2026-08-06 from SHA-256) | Project-specific determinism requirement (not in original PEG) |
| Irregular PEG | Adapted for node-view degree counts from DE λ | Standard extension of regular PEG |
| **Difference**: V10 adds GF(1024) edge labels and rank check | Original PEG is for binary codes only | — |

## 6. Spatially-Coupled NB-LDPC — V11 Successors Only

### Wei et al. — "Spatially Coupled NB-LDPC Codes over GF(q)"
**arXiv:1403.3583**

- **V10 status**: NOT implemented. Registered as V11 NB-SC-LDPC successor direction.
- **Reason**: Wei et al. analyze BEC capacity-approaching behavior.
  BEC is not a GF(1024) QSC channel model. The paper's coupling constructions
  adapt binary SC-LDPC to nonbinary; V11 may explore this after V10 finite-length
  evaluation, but it cannot be claimed as V10 evidence.
- **What V10 does NOT claim**: Any spatially-coupled performance, BEC threshold,
  or capacity-approaching behavior for GF(1024).

### Huang et al. — "Spatially Coupled NB-LDPC Codes over the BI-AWGNC"
**arXiv:1408.2621**

- **V10 status**: NOT implemented. Registered as V11 NB-SC-LDPC successor direction.
- **Reason**: BIAWGNC is not GF(1024) QSC. The paper's analysis is specific
  to binary-input channels. V11 may reference its coupling methodology but
  must independently validate on GF(1024) QSC with fresh data.
- **What V10 does NOT claim**: Any BIAWGNC-derived threshold, any coupling
  gain for GF(1024) QSC.

## Summary: Crosswalk Coverage

| Reference | Directly used? | V10 module / location |
|-----------|---------------|----------------------|
| Müller et al. 2024 | Yes — ensemble representation, DE optimization, MC-DE, PEG, FFT-SPA, leakage | `nonbinary_v10_common.py`, `nonbinary_v10_de.py`, `nonbinary_v10_peg.py`, `nonbinary_v10_fftqspa.py` |
| Storn & Price 1997 | Yes — DE/rand/1/bin optimizer | `nonbinary_v10_de.py` |
| Declercq & Fossorier 2007 | Yes — FFT-QSPA decoder | `nonbinary_v10_fftqspa.py` |
| Bennatan & Burshtein | Yes — random edge labels, channel symmetry | `nonbinary_v10_peg.py` |
| Hu et al. 2005 | Yes — PEG construction | `nonbinary_v10_peg.py` |
| Wei 1403.3583 | No — V11 successor only | BEC not applicable to GF(1024) QSC |
| Huang 1408.2621 | No — V11 successor only | BIAWGNC not applicable to GF(1024) QSC |

GitHub repositories (Lcrypto/gfq_ldpc and others): read-only algorithm
reference only. V10 must not copy, vendor, or depend on any external
non-stdlib code. Only public interface contracts (algorithm steps) may be
referenced.
