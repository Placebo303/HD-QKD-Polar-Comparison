## ADDED Requirements

### Requirement: Explicit code-factor extrinsic message

Every return of the certified GF32 row-layered decoder SHALL carry an
explicit code-factor extrinsic message defined up to a per-symbol-variable
additive constant as `L_code_ext(x) = L_post(x) - log(p_in(x))`, where
`p_in` is the exact normalized input prior used internally (floor 1e-15 +
renormalize, the v35 `priors_clean` rule) and `L_post` is the final log
belief. Transport normalization SHALL be stable softmax. The stored field
SHALL be row-normalized by subtracting log-sum-exp (never max: max leaves
an unknown scale and breaks direct comparability and exact
`softmax(log(p_in)+L_code_ext)` reconstruction).

#### Scenario: Cold return after at least one completed check sweep

- **WHEN** the cold decoder returns with ≥1 completed check sweep and
  finite shape-correct beliefs
- **THEN** `extrinsic_log_beliefs` holds the log-sum-exp-normalized
  extrinsic message and `extrinsic_provenance` is `CHECK_EXTRINSIC`.

#### Scenario: Iteration-0 return carries no check evidence

- **WHEN** the decoder returns at the initial-syndrome check with
  `iterations == 0`
- **THEN** `extrinsic_log_beliefs` is the neutral zero matrix and
  `extrinsic_provenance` is `NO_CHECK_EVIDENCE`
- **AND** the return is ineligible for cross-layer transfer.

#### Scenario: Warm start is fail-closed

- **WHEN** a non-`None` warm-start seed initializes the beliefs and no
  caller-supplied provenance exists
- **THEN** `extrinsic_provenance` is `WARM_START_UNSPECIFIED` with no
  usable extrinsic
- **AND** provenance is not inferred from `iterations`.

#### Scenario: Nonfinite or shape mismatch fails loud

- **WHEN** beliefs are nonfinite or shape-mismatched at extrinsic
  construction
- **THEN** construction fails loud or marks the return ineligible, and
  never silently repairs (no re-flooring, renormalization rescue, or
  fallback fill).

### Requirement: Extrinsic-provenance namespace is distinct from belief provenance

The tokens `NO_CHECK_EVIDENCE`, `CHECK_EXTRINSIC`,
`WARM_START_UNSPECIFIED` SHALL form the extrinsic-provenance namespace,
used only in the `extrinsic_provenance` field. Consumers SHALL NOT infer
extrinsic usability from `belief_provenance` or `iterations`. `None`/
absent SHALL mean unspecified/legacy and SHALL never be upgraded to
`CHECK_EXTRINSIC`.

#### Scenario: Legacy result without the new fields

- **WHEN** a legacy dict or fake result omits `extrinsic_log_beliefs` /
  `extrinsic_provenance`
- **THEN** any extrinsic-requiring consumer treats it as not usable and
  fails closed
- **AND** hard-decision-only and posterior-based consumers remain unaffected.

### Requirement: No persistence of beliefs or messages

No writer SHALL persist beliefs, priors, symbols, syndromes, vectors, or
extrinsic message arrays. Extrinsic arrays SHALL be transient
decoder-result fields only.

#### Scenario: Evidence root is written

- **WHEN** any scalar evidence root is written
- **THEN** it contains scalar-only fields and no belief/prior/message
  payloads.

### Requirement: Existing posterior semantics remain unchanged

The contract SHALL NOT change hard decisions, stopping, iteration counts,
`final_beliefs`, `belief_provenance`, decoder numerics, or current return
behavior beyond the additive optional fields. No consumer SHALL infer
extrinsic by subtracting an unknown/reconstructed prior, and NO consumer
SHALL auto-switch to the new field.

#### Scenario: Frozen-fixture comparison

- **WHEN** identical fixtures are decoded before and after adding the
  extrinsic fields
- **THEN** all existing result fields are identical
- **AND** the extrinsic fields are the only addition.

#### Scenario: Narrow helper rejects unusable extrinsic

- **WHEN** the helper receives `NO_CHECK_EVIDENCE`,
  `WARM_START_UNSPECIFIED`, missing/`None`/unknown provenance, missing
  arrays, wrong shapes, or nonfinite values
- **THEN** it fails closed before any cross-layer prior is computed
- **AND** only explicit finite shape-correct `CHECK_EXTRINSIC` is
  stably softmaxed for transport.

### Requirement: Independent certification before alternating execution

No multi-round alternating execution SHALL occur until the frozen matrices
pass independent certification: tree-exact distribution match (max-abs
≤ 1e-10) with negative direction/label controls; loopy 1–3-sweep match
against an independently coded recurrence (max-abs ≤ 1e-10, never vs MAP);
two-layer no-returned-evidence demonstration (posterior double-count
counterexample + forward/backward sum-product match + iteration-0
no-false-lift + warm rejection). If no deterministic counterexample or
exact match can be produced, work SHALL STOP with mathematical ambiguity;
tolerances SHALL NOT be loosened and posterior SHALL NOT be renamed as
extrinsic.

#### Scenario: Static inventory guards future consumers

- **WHEN** any production cross-layer consumer uses explicit extrinsic
- **THEN** it does so only under its own future OpenSpec, enforced by a
  static inventory test that fails otherwise.

### Requirement: D7-H stays unfrozen and unauthorized

This change SHALL NOT freeze, authorize, or implement D7-H or any
multi-round alternating execution.

#### Scenario: D7-H is considered

- **WHEN** a reviewer asks for alternating execution
- **THEN** the answer is that D7-H requires this contract's independent
  certification plus a new packet and explicit authorization.
