## ADDED Requirements

### Requirement: D6 worker unpacks the six-value decoder result with provenance transport
The D6 worker SHALL unpack exactly
`(exact, syndrome_ok, iterations, finite, beliefs, provenance)` from
`core._decode_block` and SHALL carry `provenance` in the IPC result dict.
Beliefs SHALL remain transient IPC only (present only when the task sets
`return_beliefs` and the value is non-`None`); the persisted CSV schema
`DECODER_FIELDNAMES` SHALL be unchanged.

#### Scenario: Six-value success path
- **WHEN** the decoder returns six values with a `CHECK_UPDATED` token
- **THEN** the worker result carries `belief_provenance == "CHECK_UPDATED"`
- **AND** beliefs are present iff `return_beliefs` was set.

#### Scenario: Five-value incompatible decoder
- **WHEN** the decoder returns five values (pre-BP shape)
- **THEN** warmup reports ready=false / warm=fail naming the shape
- **AND** any task-path error keeps the loud `ValueError` arity signature
  rather than a bare scientific failure.

### Requirement: D6 warmup fails loudly on incompatible decoder-result shape
Setup/warmup SHALL explicitly validate the six-value decoder-result shape
and SHALL NOT report ready on an incompatible shape.

#### Scenario: Compatible decoder
- **WHEN** warmup decodes the tiny fixture and gets six values
- **THEN** hello carries `ready=true` and `warmup=ok`.

#### Scenario: Incompatible decoder
- **WHEN** warmup gets any other shape (or the warmup call raises)
- **THEN** hello carries `ready=false` and `warmup=fail:<reason>`.

### Requirement: D6 parent requires CHECK_UPDATED before APP mixing
`run_cell` SHALL call the accepted `require_check_updated_provenance`
helper (lazy import, no V35 change) before `q` construction and
`app_fed_l2_prior`. Exactly `CHECK_UPDATED` proceeds down the existing
APP path numerically unchanged.

#### Scenario: CHECK_UPDATED pass-through
- **WHEN** the L1 return carries `CHECK_UPDATED`
- **THEN** `softmax(bel)` → `app_fed_l2_prior` → L2-APP decode runs
- **AND** mixer/L2 spies observe exactly one APP computation.

#### Scenario: Refused provenance classes
- **WHEN** the L1 return carries `PRIOR_ONLY`, `WARM_START_UNSPECIFIED`,
  missing/`None`, or an unknown token
- **THEN** no `q` is constructed, `app_fed_l2_prior` is never called, and
  no L2-APP decode is dispatched (no budget consumed)
- **AND** the L2-APP slot holds a deterministic provenance-blocked record:
  `call_idx=-1`, `crash=False`, stable
  `provenance-blocked:belief_provenance=<token>` error marker.

### Requirement: No scientific or schema drift
The repair SHALL NOT change arms, seeds, rows, mothers, schedules,
estimators, thresholds, budgets, watchdog, terminals, `DECODER_FIELDNAMES`,
or any existing scientific constant; non-BP records stay byte/field
compatible; historical A2 roots stay immutable; no R1d execution occurs.

#### Scenario: Frozen dispatch/matrix pin
- **WHEN** the repaired runner is inspected
- **THEN** `R1D_ARMS`, `R1D_VALID_SUBSET`, `ARMS`, `MODES`, `POINTS`, and
  `DECODER_FIELDNAMES` equal their frozen values.
