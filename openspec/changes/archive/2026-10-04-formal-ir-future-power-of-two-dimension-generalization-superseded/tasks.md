# Tasks: Power-of-Two Dimension Generalization

**Lifecycle**: `BACKLOG_PLAN / IMPLEMENTATION_NOT_AUTHORIZED / EXECUTE_NOT_AUTHORIZED`

## A. Entry and freeze

- [ ] Confirm the accepted NB-LDPC baseline and V62 result; record full SHAs.
- [ ] Select exactly one first new dimension and freeze `layer_bits`, mapping,
  field polynomials, `N=1024`, source strata, workload, and gates before coding.
- [ ] Reuse the V25 factorization registry; document any rejected split by field
  support, complexity, or attribution, not decoder outcomes.

## B. Minimal implementation

- [ ] Introduce a small `PowerOfTwoLayerSpec`/equivalent data structure; remove
  only dimension-specific constants needed by the selected experiment.
- [ ] Implement bijective pack/unpack and general layer posterior construction.
- [ ] Reuse the existing `GF(2^m)` backend where supported; add no new field
  implementation unless the selected `q` requires it.
- [ ] Construct new per-layer matrices and incremental rows for the selected
  dimension; verify rank, nesting, rate, and leakage.
- [ ] Keep the `[5,5], d=1024, N=1024` path numerically compatible.

## C. Tests and evidence

- [ ] T0/T1 tests from design: bijection, normalization, chain rule, field,
  noiseless decode, leakage, and GF32 compatibility anchor.
- [ ] Produce a decoder-free complexity table for `d=256/512/1024/4096` with
  posterior storage, message size, expected calls, and unsupported reasons.
- [ ] Independent implementation review before any real decoder call.
- [ ] Execute only the single frozen dimension workload after explicit auth.
- [ ] Pre-RESULT review and bounded interpretation; do not generalize one result
  to all `2^n` dimensions.

## D. Stop rules

- [ ] Stop if current NB-LDPC/V62 dependency is not accepted.
- [ ] Stop on unsupported field/FFT memory before constructing a large sweep.
- [ ] Do not vary block length during the first dimension experiment.
- [ ] Do not automatically start the NB-Polar backlog plan.

