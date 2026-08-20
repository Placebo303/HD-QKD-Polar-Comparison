# Spec — v28r_gf32_finite_code

## Requirement: exact degree-two matrices

The implementation MUST build the frozen L1 and independent per-source L2
pair lists and assign two nonzero coefficients per variable column using the
specified `_coefficient` call. It MUST report exact dimensions, 2048 edges,
column degree two, prescribed row histograms, pair uniqueness, and full GF(32)
rank. L2 MUST NOT be obtained by row-prefix slicing.

### Scenario: frozen topology

- **Given** `q=32`, `n=1024`, the V28R config, and the pinned field.
- **When** matrices are rebuilt.
- **Then** all L1/L2 shape, degree, pair, coefficient, and rank contracts pass
  independently for all three sources.

## Requirement: Bob-only empirical sequential decoding

The implementation MUST convert V26 train posterior rows to error-domain
priors, decode L1 first, and only after a verified L1 result call L2 with the
returned `x1_hat`. Alice symbols MUST NOT be accepted by this API.

### Scenario: L1 failure

- **Given** an invalid or non-convergent L1 decode.
- **When** the sequential interface returns.
- **Then** L2 has status `not_run` and no substitute predecessor is passed.

### Scenario: L1 success

- **Given** a successful L1 decode and its returned `x1_hat`.
- **When** L2 posterior rows are requested.
- **Then** the second call receives exactly that returned value and the decoder
  requires the L2 public syndrome check.

## Requirement: tag, leakage, and evidence

The tag MUST be `SHA256(bytes(x1)||bytes(x2))[:8]` represented as 16 hex
characters. Leakage MUST be `(m1+m2)*5+64` bits. Controlled errors MUST be
labelled fail-closed-only and MUST NOT be presented as FER/correction success.

## Requirement: independent verifier and lifecycle

The verifier MUST reconstruct rather than trust persisted matrices, rerun the
sequential smoke, verify the L2 predecessor argument, and write
`readonly_verify.json`. Only an all-pass run may emit
`engineering_ready_for_retrospective_gate`; V29 holdout FER is out of scope.
