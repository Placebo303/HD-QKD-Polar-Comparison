## ADDED Requirements

### Requirement: Operating-point skeleton is frozen as representative
The design SHALL freeze n128/m94/L020 `lam_d2_0.20_d3_0.80` as representative with n256 excluded, cold row-layered 90/1.0 Model-F prior, disclosure form syndrome470+tag+control+interaction, and no SKR claim.

#### Scenario: n256 proposed for this DECIDE
- **WHEN** n256 is proposed as confirmation operating point
- **THEN** it is rejected as excluded from this DECIDE.

### Requirement: Population split with key-disjointness and single STOP
CAL 702..1725 SHALL stay consumed, selection SHALL stay empty, VAL 1726..1729 SHALL stay ineligible, and confirmation SHALL be key-disjoint; unknown confirmation identity blocks execution.

#### Scenario: Confirmation execution without frozen population
- **WHEN** confirmation execution is requested before the user freezes the confirmation population
- **THEN** it STOPs with no run authorized.

### Requirement: Accounting isolates outcomes and blocks secure key
Outcome classes attempted/exact/accepted/undetected SHALL stay isolated with disclosure summed over attempted, `beta_eff_empirical` derived-only, per-session breakdown required, and secure-key output BLOCKED.

#### Scenario: Undetected verification failure occurs
- **WHEN** any undetected success-verification failure is recorded
- **THEN** UNDETECTED_STOP fires fail-closed and no success/FER claim absorbs it.

### Requirement: Go/no-go stays non-authorizing
This design SHALL authorize no run, decoder call, data access, tuning, or FER/SKR/qualification/promotion/publication claim; numeric cutoffs stay unfrozen for a future packet.

#### Scenario: Future run cites this change as authorization
- **WHEN** a run cites this change alone as its grant
- **THEN** it is refused pending its own packet plus grant with Pre-EXECUTE and Pre-RESULT.
