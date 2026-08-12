# Design: V8 Reference Reproduction and Mathematical Audit

## 1. Evidence Interpretation

The immutable V7 results remain unchanged:

- R1A: 0/4 at p=.20 and 0/4 at p=.30.
- R1B: 3/4 at p=.20 and 0/4 at p=.30.
- R2: 0/4 in both strata.
- R3: 0/4 in both strata; layer 0 never decoded.

Engineering acceptance and canary outcome are separate. T0-T3 passing means
the implementation met its frozen package tests; it does not prove that the
underlying scientific model matches the intended literature construction.

R1B is reclassified as an algorithmic diagnostic because its second channel
observation is synthesized from Alice rather than derived from the existing
Bob paired-symbol record or public disclosure. R2 is reclassified as a test of
the implemented scalar surrogate, not a rejection of full-vector nonbinary
density evolution.

## 2. Reconciliation Algebra

Use field addition throughout; in characteristic two, subtraction is the same
operation. Alice holds `x`, Bob holds `y`, and Alice publishes `s = H*x`.
Define `e = x + y`. Bob computes:

```text
d = s + H*y
  = H*x + H*y
  = H*(x+y)
  = H*e
```

The decoder estimates `e_hat` using the q-ary symmetric-channel prior centered
at zero and syndrome `d`, then reconstructs `x_hat = y + e_hat`. V8 must test
this equivalence exhaustively for tiny codes and randomly for bounded q=4/8
cases. No Alice truth may enter an iterative production decoder.

## 3. Independent Probability-Domain Oracle

The oracle is intentionally small and slow:

- direct GF addition/multiplication using the accepted field tables;
- direct enumeration/convolution for check-node messages;
- normalized probability vectors, not production log-domain approximations;
- brute-force posterior/MAP enumeration for tiny q=4 and q=8 codes;
- a one-check GF(1024) comparison against the production check update using
  deterministic sparse-support and dense vectors;
- strict finite/nonnegative/normalization checks.

Independence rule: the oracle may reuse immutable field arithmetic tables, but
must not import or call V1-V7 FFT/FWHT/check-update/decoder functions. Tests
must assert this import boundary.

## 4. Full-Vector Monte-Carlo Density Evolution

Each message is a length-q probability vector. For a q-ary symmetric channel
with error probability p and transmitted zero:

```text
P(Y=0|X=0) = 1-p
P(Y=a|X=0) = p/(q-1), a != 0
```

The implementation SHALL:

- accept edge-perspective `lambda_d` and `rho_d` distributions;
- provide explicitly named, tested node-to-edge conversion helpers;
- sample the actual variable/check degree for every update;
- draw incoming messages from the previous population according to the
  sampled degree;
- include a fresh channel message in every variable-node belief/update;
- use full-vector check convolution and variable multiplication;
- normalize and fail closed on NaN, infinity, negative mass, or zero mass;
- report mean message entropy in base q plus deterministic trace metadata;
- use seeded bounded populations/iterations suitable for unit tests.

The old R2 failure modes receive explicit regression tests: removing the
channel term or replacing sampled degree with a fixed `dv_max` must change the
golden trace and fail the relevant assertion.

## 5. Published Reproduction Gate

Before project adaptation, V8 must reproduce at least one published q-ary
QSC density-evolution threshold, degree vector, or finite reference result
within a tolerance frozen from numerical method and sample size before the
test is run.

Every imported parameter must record:

- paper title, authors, year, DOI/arXiv URL;
- exact page, section, table, figure, or equation;
- whether the distribution is node- or edge-perspective;
- field order, channel convention, rate, ensemble, and threshold definition;
- retrieval date and SHA256 of any locally retained public parameter extract.

If exact parameters or conventions cannot be obtained, the operator stops as
`implementation_blocked`. It must not guess, digitize an ambiguous plot without
an uncertainty contract, or substitute BSC/BEC vectors for the q-ary gate.

Primary references:

- Muller et al., *Non-binary LDPC codes for quantum key distribution*,
  arXiv:2307.02225: https://arxiv.org/abs/2307.02225
- Kasai et al., *Non-binary LDPC codes with multiplicative repetition*,
  arXiv:1004.5367: https://arxiv.org/abs/1004.5367

The 2025 CV-QKD multiplicative-repetition construction may be documented as a
future lead, but its virtual-channel assumptions must not be imported into the
current discrete-variable paired-symbol contract without a separate proof.

## 6. File Scope

Expected additive implementation files:

```text
comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_error_domain.py
comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_reference.py
comparison_bench/src/comparison_bench/formal_ir/nonbinary_v8_mcde.py
comparison_bench/tests/test_nonbinary_v8_error_domain.py
comparison_bench/tests/test_nonbinary_v8_reference.py
comparison_bench/tests/test_nonbinary_v8_mcde.py
openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/*
```

Do not modify V1-V7 implementation or evidence files. A small additive audit
note and source manifest are preferred to expanding lifecycle infrastructure.

## 7. Post-V8 Decision

Only after all V8 gates pass may a separate V9 proposal choose a finite-length
GF(1024) construction. The leading V9 direction is paper-faithful syndrome
reconciliation with a reproduced ensemble and blind puncturing/shortening,
not another unvalidated decoder/post-processing permutation. V9 must use fresh
roots and fresh development/confirmation data.

---

## 8. V8-60 Correction Addendum (2026-08-04)

### 8.1 Audit finding

The accepted V8 `concentrated_check_distribution` built a two-point check
distribution by matching the *mean* degree: `w_lo = dc_hi - dc_mean`,
`w_hi = dc_mean - dc_lo` with `dc_mean = 1/((1-R)*sum lambda_i/i)`. For
edge-perspective degree distributions the ensemble rate is defined by the
harmonic integrals, not the mean:

```text
R = 1 - (sum_j rho_j/j) / (sum_i lambda_i/i)      (edge-perspective rate)
```

The mean-matched weights satisfy `w_lo/d_lo + w_hi/d_hi = 1/dc_mean +
O(1e-4 relative)` but not the exact equality, biasing the concentrated check
distribution used in the reproduction. This is a formula approximation inside
the construction; correcting it is not a parameter tuning.

### 8.2 Exact construction (replaces 4/design §4 check-distribution handling)

```text
integral_lambda = sum_i lambda_i / i
target          = (1 - rate) * integral_lambda
dc              = 1 / target
d_lo = floor(dc), d_hi = d_lo + 1           (d_lo >= 2, else raise)
integer dc      -> regular {d_lo: 1.0}
otherwise       -> w_lo = (target - 1/d_hi) / (1/d_lo - 1/d_hi)
                   w_hi = 1 - w_lo
```

The two-point distribution `{d_lo: w_lo, d_hi: w_hi}` then satisfies
`sum_j rho_j/j = target` to floating-point precision and the reconstructed
rate `1 - target/integral_lambda` equals the requested rate to <= 1e-12
(tested). For the reproduction config (q=4, R=0.75, variable degrees
{2,4,7,10,19,26,28}) the weights change from `{24: 0.6714106712,
25: 0.3285893288}` (mean-matched) to `{24: 0.6623423944, 25: 0.3376576056}`
(harmonic-exact); `dc_mean = 1/target = 24.3285893` is retained as the
node-perspective mean check degree.

### 8.3 Corrective reference run (V8-60.6)

- Frozen BEFORE the single run: q=4, R=0.75, published lambda (exponents
  {1,3,6,9,18,25,27} -> degrees {2,4,7,10,19,26,28}), DET published 0.069,
  n_samples 100000 and max_iter 150 (the paper's own MC-DE budget), seed
  2026080418 (unchanged frozen seed), p_lo 0.01, p_hi 0.12, p_tol 0.0025,
  entropy_tol 0.01, streak 20, tolerance 0.012.
- Tolerance arithmetic (auditable, replaces the invalid
  `0.005+0.003+0.0025=0.015` claim): published DET rounding to 3 decimals
  0.0005 + binary-search half-step p_tol/2 0.00125 + our MC-DE finite-sample
  threshold-estimate error at 100000 nodes 0.005 (conservative bound,
  explicit constant) + the paper's own MC-DE estimate error at its 100000
  nodes 0.005 (same bound) = 0.01175 <= 0.012. Frozen tolerance: 0.012.
- Execute the corrective search exactly once; record the full probe trace in
  `evidence/v8_reproduction_trace_corrected.json`. No rerun, no tuning.

### 8.4 Evidence discipline

- `evidence/v8_reproduction_trace.json` (original) is preserved
  byte-identical; its SHA256 is recorded and a sidecar annotation
  (`v8_reproduction_trace_precorrection_annotation.json`) marks it as the
  pre-correction approximate trace.
- `evidence/v8_engineering_acceptance.json` is NOT rewritten; a new additive
  `v8_acceptance_closeout_addendum.json` explicitly resolves its
  `A12 = blocked` status once the independent V8-60 review accepts.
- `evidence/v8_source_manifest.json` is regenerated for the corrected files
  with a recorded delta note (2 of 6 files change: the mcde module and its
  test; the original hashes remain in the original acceptance record).
- Corrected provenance (parameters, tolerance arithmetic, citation) lives in
  the corrective trace file and `evidence/v8_60_correction_evidence.json`;
  `evidence/v8_literature_provenance.json` remains the byte-identical record
  of the original freeze.

### 8.5 Non-goals

Identical to proposal V8-60 non-goals: no V9, no canary/development/
confirmation/real-data/N4/comparison, no official output, no dependency
change, no staging/committing/pushing, no rerun or tuning of any frozen
parameter.
