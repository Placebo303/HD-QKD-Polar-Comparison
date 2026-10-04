# ADDED Requirements

## Requirement: Post-BP order-1 reachability diagnostic
The EXPLORE diagnostic SHALL retain R1–R3 science and measure GF32 symbol
distance in the actual MRB permuted free coordinates only after raw BP.

### Scenario: Independently reproducible distance
- GIVEN frozen synthetic source, fixed accepted H and returned BP beliefs
- WHEN distance/truth reconstruction is recorded with compact synthetic arrays
- THEN independent review can derive the actual basis and counts without
  new decoding, and D>=2 excludes only that basis's order<=1 candidates.

### Scenario: Bounded incomplete attempt
- GIVEN a numerical/resource/error STOP
- WHEN partial artifacts are retained
- THEN full diagnostic histograms remain unknown and no rerun/resume occurs.
