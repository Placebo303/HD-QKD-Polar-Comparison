# Binary LDPC v4 Backend Correction v1

## ADDED Requirements

### Requirement: Versioned production constructor compatibility

The corrected development evaluator SHALL pass the frozen Bob-conditioned
error channel to pinned `ldpc==2.4.1` as a length-256 Python list of finite
floats and SHALL leave every scientific and decoder-policy value unchanged.

#### Scenario: Correct production construction

- **WHEN** a valid v4 candidate, channel model, stratum, and Bob frame are used
- **THEN** the actual pinned decoder constructor accepts the list-valued
  `error_channel`
- **AND** the production evaluation does not report a constructor-caused
  `development_decoder_error`.

#### Scenario: Historical behavior remains immutable

- **WHEN** the correction is implemented
- **THEN** no historical v4 source file or output byte changes
- **AND** the old failed package remains identified as implementation evidence.

### Requirement: Fresh immutable development evidence

The correction SHALL create one independently versioned, no-overwrite
development package whose plan binds the predecessor package, correction
sources, unchanged inputs, exact execution order, denominators, and gate.

#### Scenario: Readiness

- **WHEN** execution and strict read-only verification complete
- **THEN** every one of 512 frames in each stratum remains in the denominator
- **AND** readiness is true only with at least 495 exact frame successes in
  each stratum and zero forbidden failures
- **AND** the verifier reports `decoder_reexecution=false`.

#### Scenario: Gate failure

- **WHEN** either readiness gate or integrity condition fails
- **THEN** the immutable package is retained
- **AND** no tuning, rerun, synthetic preparation, or real-data output occurs.

