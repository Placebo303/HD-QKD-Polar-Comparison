# Delta: Formal IR Methods

## ADDED Requirements

### Requirement: Additive LDPC v2 Identity

The system SHALL implement `ldpc_formal_v2` without changing
`ldpc_formal_v1`, its artifacts, or its qualification conclusions.

#### Scenario: V1 remains reproducible

- **WHEN** v2 code is installed
- **THEN** all v1 golden codebook hashes and focused tests remain unchanged
- **AND** no existing result path is overwritten

### Requirement: Frozen Development-Only Policy Selection

The v2 rate margin, decoder method, and decoder order SHALL be selected from a
pre-registered grid using sacrificed development frames only and SHALL be
frozen before confirmation.

The grid SHALL contain exactly nine policies: rate margins `{0,1,2}` crossed
with `(OSD_0,0)`, `(OSD_CS,1)`, and `(OSD_CS,2)`. Rate margin SHALL advance
through `[r050,r0375,r025,r0125]` toward more checks and cap at `r0125`.

#### Scenario: Confirmation cannot choose a policy

- **WHEN** confirmation frames are evaluated
- **THEN** every frame uses one globally frozen configuration
- **AND** Alice confirmation truth cannot update rates, matrices, or decoder
  parameters

### Requirement: Deterministic Screened Short-Block Codebook

The system SHALL generate exactly 16 deterministic 56x64 master candidates per
plane, screen all 32/40/48/56-row prefixes, select one master per plane, encode
the selected 40 prefixes, and retain the full selection audit trail.

#### Scenario: Repeated screening is reproducible

- **WHEN** screening is repeated with the same generator version, inputs, and
  seeds
- **THEN** candidate metrics, selected IDs, canonical bytes, and manifest hash
  are identical
- **AND** each plane's four selected matrices are row-prefix nested

### Requirement: Promotion Before Real Use

V2 SHALL NOT receive a real-data lock unless a fresh synthetic qualification
achieves at least 31/32 verified successes in each p=.01 and p=.02 stratum
with zero unclassified/internal/provenance/accounting failures.
