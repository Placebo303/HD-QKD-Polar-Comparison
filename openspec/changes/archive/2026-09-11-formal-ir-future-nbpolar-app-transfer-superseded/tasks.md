# Tasks: NB-Polar APP Transfer and Conditional Rescue

**Lifecycle**: `BACKLOG_PLAN / IMPLEMENTATION_NOT_AUTHORIZED / EXECUTE_NOT_AUTHORIZED`

## A. Entry and backend audit

- [ ] Confirm accepted NB-LDPC/V62 dependency and record full SHAs.
- [ ] Audit current and sibling read-only Polar code for q-ary transform,
  construction, SCL/list output, soft beliefs, and incremental disclosure.
- [ ] Decide one implementation route: native GF32 Polar or five-bit multilevel
  Polar.  Record why the other is deferred; do not implement both.
- [ ] Freeze kernel, construction dataset, rate/leakage, list size, posterior
  extraction, verification, blocks, workload, and gates before decoder work.

## B. Minimal Phase-1 implementation

- [ ] Implement NB-Polar upper-layer encode/disclosure/decode only in the
  comparison layer; do not modify Polar Release.
- [ ] Expose normalized `q(U1)` with no Alice-truth input and deterministic
  list-to-posterior rules.
- [ ] Feed the same `q(U1)` mixture contract into the frozen NB-LDPC lower layer.
- [ ] Preserve a paired accepted NB-LDPC reference on identical blocks and
  exact disclosure decomposition.

## C. Validation

- [ ] T0: noiseless, uniform, delta, normalization, symmetry, frozen-set,
  disclosure, and verification tests.
- [ ] T1: synthetic matched-channel test demonstrating that APP is not a hard
  one-hot alias and that Alice truth is absent from priors.
- [ ] Decoder-free complexity estimate and backend readiness verdict.
- [ ] Independent review, then one small paired development execution after
  explicit authorization.
- [ ] Pre-RESULT review with per-source/full-exact/disclosure/runtime reporting.

## D. Conditional successors

- [ ] Open Phase 2 only after `NBPOLAR_APP_TRANSFER_SIGNAL`; freeze exactly one
  conditional-disclosure mechanism.
- [ ] Open full NB-Polar lower-layer work only after Phase 2 evidence and a new
  OpenSpec/authorization.
- [ ] Stop on backend-not-ready or no retained signal; do not compensate with a
  kernel/list/rate grid search.
- [ ] Do not automatically start dimension generalization.

