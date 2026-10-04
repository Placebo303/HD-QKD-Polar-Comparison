# Spec Delta: Real IR Success

## ADDED Requirements

### Requirement: Real IR success requires verification

A comparison method result MUST be classified as real IR success only when independent verification succeeds for the reconciled frame or frame group.

#### Scenario: Decoder improves error rate but verification fails

- **GIVEN** a method output has lower post-IR SER/BER than raw SER/BER
- **AND** independent verification fails
- **THEN** the result MUST NOT be classified as real IR success
- **AND** the failure status MUST remain visible.

#### Scenario: Decoder and verification succeed

- **GIVEN** a method output passes independent verification
- **AND** the method status is compatible with executable success
- **THEN** the result MAY be classified as real IR success
- **AND** leakage accounting status MUST be reported.

### Requirement: Status values remain honest

The comparison pipeline MUST preserve non-success statuses such as `reference`, `stub`, `unavailable`, `decode_failed`, `no_verified_success`, and `experimental_failed`.

#### Scenario: Reference implementation produces a diagnostic row

- **GIVEN** a method is labeled reference-grade
- **WHEN** it emits diagnostics
- **THEN** the output MUST NOT silently relabel the result as production `ok`.

### Requirement: Leakage and beta are not fabricated

`leak_EC_actual_bits` and `beta_eff_empirical` MUST be derived from protocol transcript/accounting and error inputs, or explicitly left unavailable/approximate with notes.

#### Scenario: Leakage is approximate

- **GIVEN** a method only has approximate transcript accounting
- **THEN** the approximation MUST be labeled in notes or diagnostics
- **AND** comparisons against exact leakage methods MUST document that semantic difference.

### Requirement: Representative real-frame validation precedes broad sweeps

Before broad real-data sweeps are used for final method selection, the project MUST validate candidate methods on a bounded representative real-frame set.

#### Scenario: A full sweep is requested before representative validation

- **GIVEN** representative validation has not been documented
- **THEN** the agent SHOULD stop and request/prepare the representative validation plan first
- **UNLESS** the user explicitly asks to run the full sweep and confirms output policy.

### Requirement: Original Polar baseline remains frozen

This change MUST NOT require changes to original Polar logic under `src/`, `experiments/`, or `tools/`.

#### Scenario: A needed fix appears to require original Polar edits

- **GIVEN** implementation appears to require changing original Polar workflow semantics
- **THEN** the agent MUST stop and return to planning/OpenSpec
- **AND** must not make the baseline edit under this change.

