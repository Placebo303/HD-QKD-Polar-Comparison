## ADDED Requirements

### Requirement: Explicit decoder belief provenance
Every return of the certified GF32 row-layered/flooding decoder SHALL carry an explicit `belief_provenance` token on the returned result (v35 `DecoderResult` field and adapter result dicts), using exactly `PRIOR_ONLY`, `CHECK_UPDATED`, or `WARM_START_UNSPECIFIED`. The field SHALL be additive with a default of `None` (unspecified/legacy); `None` SHALL never be upgraded to `CHECK_UPDATED`.

#### Scenario: Cold row-layered return with zero completed check sweeps
- **WHEN** the row-layered decoder returns at the initial-syndrome check with `iterations == 0`
- **THEN** `belief_provenance` is `PRIOR_ONLY`
- **AND** the returned beliefs are the floored/renormalized input log-prior with no check message.

#### Scenario: Return after at least one completed check sweep
- **WHEN** the row-layered or flooding decoder returns with `iterations > 0`
- **THEN** `belief_provenance` is `CHECK_UPDATED`.

#### Scenario: Warm start without explicit provenance
- **WHEN** a non-`None` warm-start seed initializes the beliefs and no caller-supplied provenance exists
- **THEN** `belief_provenance` is `WARM_START_UNSPECIFIED`
- **AND** provenance is not inferred from `iterations`.

### Requirement: Hard-decision semantics remain unchanged
The correction SHALL NOT redefine or patch v35 hard-decision stopping, and SHALL NOT change any existing result field (`x_hat`, `syndrome_ok`, `iterations`, `runtime_s`, `status`, `final_beliefs`) numerically.

#### Scenario: Frozen-fixture comparison
- **WHEN** identical fixtures are decoded before and after adding the provenance field
- **THEN** the hard-decision results are identical
- **AND** the provenance field is the only addition.

### Requirement: Cross-layer APP consumers fail closed on unconditioned provenance
A consumer that uses returned beliefs as cross-layer evidence SHALL carry explicit provenance and SHALL accept only `CHECK_UPDATED` (or explicitly stronger provenance) for computing a syndrome-conditioned APP input such as `P(U1|B,s1)`; `PRIOR_ONLY`, `WARM_START_UNSPECIFIED`, `None`, absent, or unknown SHALL fail closed before the cross-layer prior is computed.

#### Scenario: Iteration-0 prior reaches an APP-requiring consumer
- **WHEN** D5-style `_run_layered_block` (or any migrated equivalent) receives a `PRIOR_ONLY` L1 return
- **THEN** it refuses to forward `softmax(beliefs) @ P` as APP evidence
- **AND** it does not silently drop `s1` from the L2 conditioning set.

#### Scenario: Conditioned return passes the guard
- **WHEN** the L1 return carries `CHECK_UPDATED`
- **THEN** the existing `q @ P(U2|B,U1)` APP prior computation proceeds as before.

#### Scenario: Legacy result without the field
- **WHEN** a legacy dict or fake result omits `belief_provenance`
- **THEN** an APP-requiring consumer treats it as not conditioned and fails closed
- **AND** hard-decision-only consumers remain unaffected.

### Requirement: PRIOR_ONLY is never labeled conditioned posterior or APP
No artifact, record, plot, or claim SHALL label a `PRIOR_ONLY` return as a syndrome-conditioned posterior or APP. Iteration-0/current beliefs may be recorded only as `PRIOR_ONLY_CURRENT_BELIEF`.

#### Scenario: Diagnostic records an iteration-0 current belief
- **WHEN** a posterior-comparison diagnostic encounters a zero-sweep return
- **THEN** it records the value as current belief with `PRIOR_ONLY` provenance
- **AND** it does not apply a conditioned-posterior tolerance as a decoder verdict.

### Requirement: No retroactive change to historical results
The correction SHALL NOT alter D7-B R2 evidence, its frozen terminal `D7_B_RESOURCE_OVERRUN`, its accepted scope, D7-A results, or any historical v45–v55 artifact or number.

#### Scenario: Historical evidence is referenced
- **WHEN** the correction is implemented or reviewed
- **THEN** all historical records remain exactly as published
- **AND** no rerun or restatement is performed.

### Requirement: Implementation gating before cross-layer APP routes
Interface implementation SHALL be mandatory before the next sequential, alternating or joint cross-layer APP run, and SHALL NOT be required before D7-C single-layer oracle readiness/execution.

#### Scenario: D7-C single-layer oracle is prepared
- **WHEN** D7-C constructs its four priors directly from the frozen joint model
- **THEN** it requires no provenance interface
- **AND** it must not import or depend on the future interface-rework implementation.

### Requirement: D7-C single-layer boundary
D7-C SHALL record exact/syndrome/iterations and may record current-belief confidence, but SHALL never feed those beliefs into another layer and SHALL never call them conditioned posterior without provenance.

#### Scenario: D7-C records current-belief confidence
- **WHEN** a D7-C cell returns iteration-0 beliefs
- **THEN** the record is labeled with its provenance
- **AND** no cross-layer data flow uses the value.

### Requirement: Scope boundary for the sibling probability-domain decoder
This contract SHALL apply to the certified v35/D5 log-domain GF32 decoder path only; the sibling `nonbinary_v10_fftqspa.py` probability-domain decoder with its separate `"beliefs"` contract is out of scope.

#### Scenario: Sibling decoder is considered
- **WHEN** a reviewer enumerates `final_beliefs` consumers
- **THEN** the sibling is listed as excluded with the different-contract reason
- **AND** no change is required there by this change.
