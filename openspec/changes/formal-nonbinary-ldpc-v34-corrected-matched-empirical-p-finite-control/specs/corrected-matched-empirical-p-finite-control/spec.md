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
- **AND** one block SHALL initialize `Generator(PCG64(seed))` once and make one
  C-order `choice(1024*1024, size=1024, replace=True, p=p)` call only.
- **AND** NumPy SHALL be exactly version `2.4.0`, recorded in the manifest and
  matched by exact integer-array equality to design `V34-PCG64-REF1` for
  `idx`, `A`, and `B` before any decoder call.

#### Scenario: Empirical probability preflight fails

- **WHEN** a source matrix is not `(1024,1024)`, contains negative/non-finite
  values, has a non-positive/non-finite total, or cannot form a valid normalized
  float64 probability vector
- **THEN** execution stops before the first block as INCONCLUSIVE
- **AND** no smoothing, fallback, skipping, or resampling is permitted.

### Requirement: Oracle-L1 finite L2 diagnostic

The diagnostic SHALL NOT decode L1. It SHALL use true U1 only for the declared
oracle conditioning of `P(U2|B,U1)` and SHALL label this truth use as
non-operational and non-qualifying.

#### Scenario: Block success is mechanically checked

- **WHEN** one L2 block decode completes
- **THEN** success requires exact L2 recovery, valid syndrome, valid tag, and no
  false accept
- **AND** all four components are persisted for read-only reconstruction.
- **AND** `>=19/20` is interpreted only as the V32 mechanical discriminator,
  never a confidence threshold, FER estimate, or qualification criterion.

#### Scenario: Decoder code is reused

- **WHEN** V34 invokes V28R `decode_error_domain_posterior` through the V32
  oracle ProductionRunner path with `max_iter=30` and `streak=20`
- **THEN** it SHALL supply only V31 packet matrices with m2=184/190/192
- **AND** it SHALL NOT load V28R's m2=194/200/202 matrices.
- **AND** max_iter=30 SHALL be identified as a comparability binding, not a
  decoder-adequacy claim; a 200-iteration arm requires a new successor.

### Requirement: Frozen bounded matrix and exact-once execution

Before implementation, FR1 and the main thread SHALL freeze the RNG/draw order,
fresh seeds `340101..340120`, `340201..340220`, `340301..340320`, source-major
order, 20 blocks per source, decoder constants, source PASS threshold
`successes>=19/20`, terminal mapping, and output root. An official execution SHALL
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
- **AND** ordinary failure requires a complete finite legal decoder return but
  failure of exact recovery or syndrome/tag validation.

#### Scenario: Binding or evidence failure occurs

- **WHEN** an input drifts, probability is invalid, output collides, decoder
  or code identity fails, an interface result is exceptional/malformed/non-finite,
  or execution is interrupted
- **THEN** the retained official evidence is INCONCLUSIVE
- **AND** no resume, retry, replacement seed, `run_02`, or successor is authorized.

### Requirement: Independent replay and narrow claims

ER1 SHALL independently reconstruct the frozen input identities, all attempted
ordinals, per-source success totals, terminal mapping, and protected-root
status without invoking the decoder.

The 20 blocks per source SHALL be described as iid only conditional on the
frozen empirical table, fixed packet, and fixed decoder configuration. They
SHALL NOT be used to estimate or claim general finite-block FER.

#### Scenario: Control passes

- **WHEN** every source meets the frozen threshold and ER1 accepts
- **THEN** the only supported positive claim is success of this corrected
  matched empirical-P finite control for one packet, oracle L1, decoder, and
  bounded block sample
- **AND** no FER, key-rate, real-data qualification, operational, promotion,
  or general NB-LDPC claim is made.
