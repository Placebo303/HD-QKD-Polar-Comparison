# ADDED Requirements

## Requirement: Fixed DV2 descriptive support census

The CLI SHALL declare EXPLORE and use only mapped control constructor
supports of the accepted degree-admitted synthetic source. It SHALL report
normalized Laplacian spectrum and the frozen Fiedler sweep, with explicit
degeneracy and non-performance ceilings. No decoder or graph builder calls.

### Scenario: Complete census

- WHEN source checks and budget pass
- THEN six graph records retain adjacency, eigen and all prefix-cut evidence.

### Scenario: Partial or over-budget census

- WHEN a source/numeric/resource check fails
- THEN retain actual completed metrics and explicit INCOMPLETE state without
  input replacement, tuning, fabricated zeros or rerun.
