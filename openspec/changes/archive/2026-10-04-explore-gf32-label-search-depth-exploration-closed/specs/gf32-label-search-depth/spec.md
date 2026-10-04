## ADDED Requirements

### Requirement: Fixed-graph search depth comparison
The EXPLORE runner SHALL compare accepted onepass labels to at most eight
deterministic coordinate sweeps using the same check-entropy objective,
fixed graph/source/prior/decoder and new192 paired synthetic samples. It
SHALL stop search at a no-change sweep and record its search trajectory.

#### Scenario: Completed paired batch
- WHEN all frozen gates pass and384calls complete
- THEN exact+syndrome counts, per-graph gains, four states and260bits per call
  SHALL be reported with the unchanged practical screen and claim ceiling.

#### Scenario: Incomplete or stopped batch
- WHEN a frozen admission/resource/exception gate stops execution
- THEN attempts SHALL be retained without retry and comparison aggregates
  SHALL remain unknown until the complete frozen denominator exists.

#### Scenario: Authorization and scientific bounds
- WHEN implementation review passes and main dispatch occurs
- THEN only the quoted one-shot grant SHALL permit the exact fresh-root run,
  with no real inputs, extra frames, automatic successor or route promotion.
