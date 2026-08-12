# Delta Specification: V12 Nonbinary LDPC Real Micro-Feasibility

## ADDED Requirements

### Requirement: Sole finite nonbinary route

The system SHALL use only the reconstructed V7 R1A GF(1024), `n=256`,
`m=170` degree-2 PEG matrix, its primary undamped flooding FFT-QSPA route, the
frozen `p=.20` QSC prior, and all 170 checks active.

#### Scenario: Result-dependent method change

- **WHEN** a prefix, matrix, coefficient, degree profile, schedule, iteration
  cap, prior, decoder, or fallback is changed after review
- **THEN** the V12 execution authorization SHALL be void
- **AND** the existing four-frame partition SHALL NOT be reused

### Requirement: Compatible real frame contract

The system SHALL use exactly four fresh, contiguous 256-symbol frames from the
10 dB Type-II q=1024 Gray bw200 source domain.

#### Scenario: Incompatible or reused frame

- **WHEN** a frame is split, concatenated, incomplete, untraceable, present in
  historical frame/payload identities, or borrowed from an existing role
- **THEN** it SHALL NOT enter the V12 partition
- **AND** fewer than four eligible rows SHALL yield `source_partition_blocked`

### Requirement: Frozen information boundary

The decoder SHALL receive only Bob symbols, the reviewed stratum-level QSC
prior, the public full syndrome, and frozen decoder constants.

#### Scenario: Alice-derived decoder input

- **WHEN** Alice truth, frame-specific SER, an error location, a verification
  result, or V5 confirmation information can influence decoding or selection
- **THEN** the run SHALL be `invalid_execution`

### Requirement: Independent verification and actual accounting

The system SHALL distinguish syndrome consistency from exact verified
correction and SHALL reconstruct every disclosed syndrome, tag, and seed bit
from the transcript. Local outcome events SHALL carry zero disclosure bits.

#### Scenario: Syndrome-only convergence

- **WHEN** a decoded word is syndrome-consistent but its independent tag or
  offline exact-equality check fails
- **THEN** the outcome SHALL NOT be `verified_success`

#### Scenario: Leakage mismatch

- **WHEN** the 1700-bit full syndrome, an invoked 64-bit tag, or its
  conditionally emitted 2623-bit public seed is omitted or misclassified
- **THEN** the run SHALL be `invalid_execution`

### Requirement: Exact lifecycle and denominator

The production lifecycle SHALL separate implementation, fake testing, T3,
source/partition preparation, production-plan review, one four-frame execute,
and one decoder-free read-only verification.

#### Scenario: Retry or missing denominator

- **WHEN** a frame is retried, resumed, replaced, omitted, or decoded more than
  once
- **THEN** the run SHALL be `invalid_execution`

### Requirement: Exact production artifact set

The future approved production package SHALL contain only the seven artifacts
declared in the V12 design, SHALL prepare exclusion/partition/plan artifacts
without decoding, and SHALL bind four unique fresh 2623-bit seed records before
execution.

#### Scenario: Artifact or seed ambiguity

- **WHEN** an artifact is missing/extra, an exclusion path is unclassified, a
  seed record lacks `seed_hex`, `seed_bit_length`, or `seed_id`, or a seed ID
  is duplicate or collides with discoverable formal evidence
- **THEN** production execution SHALL remain unauthorized

### Requirement: Narrow micro-feasibility gate

The system SHALL declare `observed_real_correction` only with at least one of
four independently verified successes, zero forbidden failures, valid
accounting, and successful decoder-free replay.

#### Scenario: No verified correction

- **WHEN** all four complete valid outcomes fail independent verification
- **THEN** the terminal state SHALL be `failed_canary`
- **AND** no replacement, tuning, rerun, or automatic successor SHALL occur

#### Scenario: Gate passes

- **WHEN** the complete micro-feasibility gate passes
- **THEN** the claim SHALL be limited to an observed exact correction in this
  four-frame bw200 tractability canary
- **AND** FER, generalization, qualification, promotion, and formal comparison
  SHALL remain unestablished
