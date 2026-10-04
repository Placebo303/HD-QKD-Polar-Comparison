# ADDED Requirements

## Requirement: Fixed-budget top6 symbol experiment
The EXPLORE probe SHALL compare numeric-order MRB to existing belief-top6
MRB at the same256 candidate budget,retaining T1–T3 science/accounting/limits.

### Scenario: Frozen paired comparison
- GIVEN accepted comparator reconstruction and independent new gates
- WHEN the new command executes once with fresh samples
- THEN true recovery,syndrome-valid wrong,cost and correct metadata are
  reported separately for allgraphs without pooling or qualification.

### Scenario: Shared runner with unchanged legacy defaults
- GIVEN E1's explicit two-arm callbacks and top6 batch identity/context
- WHEN the top6 entry uses the shared runner with its actual summary
- THEN both arms rescue only raw syndrome failures and all metadata/costs
  reflect their actual rows; omitted new options retain legacy candidate-only
  behavior and its original CSV header without global mutation.
