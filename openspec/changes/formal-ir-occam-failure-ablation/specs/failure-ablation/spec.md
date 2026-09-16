## ADDED Requirements

### Requirement: Retrospective capped-policy analysis
The analysis SHALL reconstruct verified recovery and resource accounting only from the V64 early-stop semantics and recorded terminal stages, on identical blocks across caps.

#### Scenario: A block first verifies at delta16
- **WHEN** the policy is capped at delta8
- **THEN** report no verified recovery, three decoder calls and base disclosure plus 40 bits
- **AND** do not invent its delta8 residual or exactness.

### Requirement: Separate scientific outcomes
The analysis SHALL separate verified exact recovery, unverified outcomes and accepted-but-wrong outcomes, including source denominators and disclosure of rejected blocks.

#### Scenario: A final accepted block is not exact
- **WHEN** the terminal stage is within the cap
- **THEN** count it as undetected and never as verified exact recovery.

### Requirement: No new decoder execution
The script SHALL read existing compact artifacts and print statistics without invoking decoder or raw-data code or changing input artifacts.

#### Scenario: Follow-up needs unrecorded trajectories
- **WHEN** residuals at earlier stages are required
- **THEN** mark them unavailable and propose a separately gated experiment.
