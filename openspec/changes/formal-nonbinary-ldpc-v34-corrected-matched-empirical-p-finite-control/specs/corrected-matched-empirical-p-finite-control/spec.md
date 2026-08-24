# Corrected matched empirical-P finite control specification

## ADDED Requirements

### Requirement: Single-variable matched empirical control

The V34 diagnostic SHALL replace only V32 B1's SER-matched uniform-substitution
generator with direct source-specific train empirical-joint `P(A,B)` sampling.
It SHALL retain the frozen V31 packet, GF(32)/F03 identity, V32 oracle-L1
decoder path, block length, decoder schedule, and success predicate.

#### Scenario: Generator and posterior are matched

- **WHEN** a V34 block is generated for one source
- **THEN** all 1024 `(A,B)` pairs are iid draws from that source's frozen train
  empirical joint table
- **AND** the L2 posterior is derived from the same table
- **AND** no QSC, aggregate-SER substitution, smoothing, holdout, or source
  pooling is used.

### Requirement: Oracle-L1 finite L2 diagnostic

The diagnostic SHALL NOT decode L1. It SHALL use true U1 only for the declared
oracle conditioning of `P(U2|B,U1)` and SHALL label this truth use as
non-operational and non-qualifying.

#### Scenario: Block success is mechanically checked

- **WHEN** one L2 block decode completes
- **THEN** success requires exact L2 recovery, valid syndrome, valid tag, and no
  false accept
- **AND** all four components are persisted for read-only reconstruction.

### Requirement: Frozen bounded matrix and exact-once execution

Before implementation, FR1 and the main thread SHALL freeze the RNG/draw order,
fresh seeds, source order, 20 blocks per source, decoder constants, source PASS
threshold, terminal mapping, and output root. An official execution SHALL
require a separate explicit user authorization bound to the accepted HEAD and
frozen matrix.

#### Scenario: Official root already exists

- **WHEN** execute observes the frozen `run_01` root already exists
- **THEN** it refuses before any decoder call
- **AND** it does not resume, overwrite, create `run_02`, or add seeds.

#### Scenario: Ordinary decoding failure occurs

- **WHEN** a block completes without satisfying the success predicate
- **THEN** the failure is recorded
- **AND** the remaining frozen blocks continue without tuning.

#### Scenario: Binding or evidence failure occurs

- **WHEN** an input drifts, probability is invalid, output collides, decoder
  identity fails, or execution is interrupted
- **THEN** the retained official evidence is INCONCLUSIVE
- **AND** no automatic rerun or successor is authorized.

### Requirement: Independent replay and narrow claims

ER1 SHALL independently reconstruct the frozen input identities, all attempted
ordinals, per-source success totals, terminal mapping, and protected-root
status without invoking the decoder.

#### Scenario: Control passes

- **WHEN** every source meets the frozen threshold and ER1 accepts
- **THEN** the only supported positive claim is success of this corrected
  matched empirical-P finite control for one packet, oracle L1, decoder, and
  bounded block sample
- **AND** no FER, key-rate, real-data qualification, operational, promotion,
  or general NB-LDPC claim is made.

