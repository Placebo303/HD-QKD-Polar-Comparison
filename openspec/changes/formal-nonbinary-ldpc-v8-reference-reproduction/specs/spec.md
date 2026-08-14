# Delta Specification: Formal Nonbinary LDPC V8

## ADDED Requirements

### Requirement: V8 is reference-only

The system SHALL limit V8 to mathematics, independent reference computation,
published-result reproduction, and engineering tests.

#### Scenario: No scientific execution

- **WHEN** V8 is completed
- **THEN** no V8 canary, development, confirmation, real-data, N4, or formal
  comparison output SHALL exist
- **AND** no new V8 directory SHALL exist under the official formal-IR output
  root.

### Requirement: V7 evidence remains immutable and correctly scoped

The system SHALL preserve all V1-V7 artifacts and SHALL record that R1B is an
algorithmic diagnostic outside the single-Bob-observation IR contract and R2
tests only the implemented scalar surrogate.

#### Scenario: Audit does not rewrite evidence

- **WHEN** the V8 audit is recorded
- **THEN** no V7 source, plan, result, transcript, manifest, or evidence file
  SHALL be modified
- **AND** the audit SHALL distinguish engineering test success from scientific
  canary failure.

### Requirement: Error-domain equivalence is executable

The system SHALL implement and test `H*(x+y) = H*x + H*y` and reconstruction
`x_hat = y + e_hat` over supported characteristic-two fields.

#### Scenario: Tiny exhaustive equivalence

- **WHEN** all bounded tiny q=4 and q=8 vectors are evaluated
- **THEN** direct-coset and error-domain syndrome constraints SHALL agree
- **AND** correct error recovery SHALL reconstruct Alice exactly.

### Requirement: Independent oracle

The system SHALL provide a direct probability-domain oracle independent of
production FFT/FWHT check-update and decoder implementations.

#### Scenario: Production/reference agreement

- **WHEN** deterministic q=4/q=8 cases and bounded one-check q=1024 vectors are
  evaluated
- **THEN** production messages SHALL agree with the oracle within a frozen
  numerical tolerance
- **AND** brute-force tiny-code MAP results SHALL agree with reference BP where
  the test graph is cycle-free.

### Requirement: Full-vector MC-DE

The system SHALL perform q-ary symmetric-channel Monte-Carlo density evolution
using length-q messages, edge-perspective degree distributions, exact sampled
degrees, channel contributions, and base-q mean entropy.

#### Scenario: Old R2 approximations are detectable

- **WHEN** the channel contribution is removed or sampled degree is replaced by
  a fixed maximum degree
- **THEN** a deterministic regression SHALL fail or produce a trace that does
  not match the accepted golden trace.

### Requirement: Published q-ary reproduction precedes adaptation

The system SHALL reproduce at least one precisely sourced published q-ary QSC
configuration before proposing project-specific GF(1024) parameters.

#### Scenario: Source is incomplete

- **WHEN** the exact degree perspective, field/channel convention, or numerical
  target is unavailable or ambiguous
- **THEN** the task SHALL stop `implementation_blocked`
- **AND** no parameter SHALL be guessed and no project adaptation SHALL begin.

### Requirement: Reproducible engineering evidence

The system SHALL produce a source hash manifest, bounded test commands/results,
reference-parameter provenance, and an acceptance report for V8-A01..V8-A12.

#### Scenario: Acceptance

- **WHEN** independent review is requested
- **THEN** the reviewer SHALL be able to reconstruct scope, imports, test
  results, tolerances, citations, and absence of scientific output from disk.
