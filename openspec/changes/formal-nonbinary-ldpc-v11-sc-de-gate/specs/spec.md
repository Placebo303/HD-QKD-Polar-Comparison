# Delta Specification: V11 Spatially Coupled DE Gate

## ADDED Requirements

### Requirement: Published QSC reference reproduction

The system SHALL reproduce the declared q=4 and q=16 uncoupled and coupled
SMP-DE thresholds within absolute tolerance .002 before GF(1024) scientific
execution.

#### Scenario: Reference mismatch

- **WHEN** any reference threshold misses tolerance or its provenance cannot be
  reconstructed
- **THEN** the state SHALL be `failed_reference`
- **AND** no GF(1024) formal plan SHALL execute

### Requirement: Equal-rate coupled control

The system SHALL compare spatially coupled and uncoupled ensembles at the same
effective terminated rate, using the same frozen V10 S1/S3 variable-node
distribution and paired stochastic inputs.

#### Scenario: Termination rate mismatch

- **WHEN** reconstructed coupled effective rate differs from its control by
  more than `1e-12`
- **THEN** that result SHALL be invalid and SHALL NOT satisfy a gate

### Requirement: Frozen finite geometry set

The formal execution SHALL contain only G1 `(w=1,L=32,W=8)`, G2
`(w=2,L=32,W=16)`, and G3 `(w=2,L=32,W=32)`.

#### Scenario: Result-dependent geometry change

- **WHEN** a geometry, window, chain length, edge-spreading rule, or budget is
  changed after review
- **THEN** the existing execution authorization SHALL be void
- **AND** a new plan and review SHALL be required

### Requirement: Conservative dual gate

A geometry SHALL be declared `ready_for_finite_length` only when both S1 and
S3 meet their absolute thresholds and each shows paired gain of at least .002
over its uncoupled control, with every engineering, resource, lifecycle, and
replay requirement satisfied.

#### Scenario: No geometry passes

- **WHEN** no frozen geometry satisfies the complete dual gate
- **THEN** the state SHALL be `failed_coupling`
- **AND** the best or closest geometry SHALL NOT be promoted

### Requirement: Authorization boundary

V11 SHALL stop at an ensemble-level gate decision.

#### Scenario: Coupled DE passes

- **WHEN** one or more frozen geometries pass
- **THEN** the result MAY be described only as `ready_for_finite_length`
- **AND** protograph lifting, finite matrices, windowed FFT-QSPA, canary,
  development, real-data, qualification, and promotion SHALL require a new
  OpenSpec change
