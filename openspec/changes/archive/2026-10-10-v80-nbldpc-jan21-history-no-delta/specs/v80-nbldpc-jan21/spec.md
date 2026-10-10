## ADDED Requirements

### Requirement: Planning record authorizes no execution
The change SHALL record the V80 program plan, S0 GO result, and q-prior without authorizing execution or consuming budget.

#### Scenario: S1 execution requested under this change
- **WHEN** S1 DE execution is requested citing this change alone
- **THEN** it is refused pending an explicit grant plus Pre-EXECUTE.

### Requirement: S1 ensemble efficiency gate
S1 SHALL optimize DE ensembles on the unchanged V26 kernel over m-grid 24–31 at n=256 with gate f_ens <= 1.15 per arm including the flip rule.

#### Scenario: S1 arm adjudication
- **WHEN** an S1 arm reports f_ens above 1.15
- **THEN** the arm fails the gate and does not advance to S2.

### Requirement: S2 construction gate with ban
S2 SHALL build PEG/improved-PEG codes excluding three-shift-cyclic GF(32) mothers, with synthetic gate FER <= 5% at efficiency <= 1.3.

#### Scenario: Banned mother proposed
- **WHEN** a three-shift-cyclic GF(32) mother is proposed for S2
- **THEN** it is excluded before any FER evaluation.

### Requirement: S3 real-data confirmation needs separate prereg
S3 Jan-21 real-data work SHALL require a separate DECIDE prereg with authorization plus Pre-EXECUTE and Pre-RESULT; this change makes no SKR/qualification claim.

#### Scenario: S3 execution requested
- **WHEN** Jan-21 real-data execution is requested without the S3 prereg
- **THEN** it is refused as unauthorized under this change.
