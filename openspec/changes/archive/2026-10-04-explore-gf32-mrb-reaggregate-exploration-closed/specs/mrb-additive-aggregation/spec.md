# ADDED Requirements

## Requirement: Additive source-preserving reaggregation
The EXPLORE diagnostic SHALL preserve original MRB rows and deficient summary,
rederive counts in a new root without scientific rerun, and explicitly separate
original scientific identity from reaggregation identity, per A1–A3.

### Scenario: Complete corrected aggregate
- GIVEN independently verified MRB lineage and source rows
- WHEN the bounded reducer completes under new independent gates
- THEN original UUID/contract/namespace and recomputed outcomes are recorded
  with new diagnostic provenance and the stored-boolean limitation.
