## ADDED Requirements

### Requirement: D19 STOP stays immutable
The terminal `D19_L2_FINITE_ENGINEERING_BLOCKED` with frozen seed `2026094408` SHALL stay closed; no seed-stream, population, statistic, or budget change SHALL rewrite the old STOP.

#### Scenario: Seed replacement proposed as same-population fix
- **WHEN** a 4408 replacement is proposed under the frozen packet
- **THEN** it is rejected and directed to a new amendment/packet.

### Requirement: D18 winner stays a non-optimal representative
`lam_d2_0.20_d3_0.80` SHALL remain the single L2 finite-validation representative by frozen tie-break with the 0.15/0.20/0.25 near-tie family closed to extra arms.

#### Scenario: Extra near-tie arm proposed
- **WHEN** an extra 0.15/0.25 arm is proposed inside this prep
- **THEN** it is refused as reopening the frozen tie-break.

### Requirement: Q1-Q3-first ordering gates any amendment
Manual Astra first-chat on Q1-Q3 with the 4-file manifest and verbatim return plus independent A1-A7 check SHALL precede any v72p2d19 amendment packet; pipeline yield SHALL score inadmissible cells as zero-yield, never silently dropped.

#### Scenario: New seed set proposed before Astra return
- **WHEN** a new seed set, admission rule, statistic, or budget is proposed before Astra's Q1-Q3 return
- **THEN** prep STOPs and no amendment change is opened.

### Requirement: Prep authorizes nothing executable
This prep SHALL authorize no D19 execution, decoder/DE call, constructor redesign, new seed, T=72 batch, real-data touch, claim, or commit/push.

#### Scenario: Execution requested citing prep approval
- **WHEN** execution is requested citing autonomous-advance approval or this prep
- **THEN** it is refused pending its own explicit grant with Pre-EXECUTE.
