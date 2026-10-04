# ADDED Requirements

## Requirement: Fine CONTROL selector with fixed scientific mechanism
The probe SHALL use the exact seven-point frozen grid and new seed namespace
for batch d2d185a6, retaining all other scientific clauses from fd01. Only
CONTROL outcomes SHALL select the first eligible5..19/24 point; candidate
and independent192-pair holdout SHALL run only after all machine gates pass.

### Scenario: No eligible point or a failed gate
GIVEN the complete frozen grid has no eligible point, or a gate fails,
WHEN the terminal fires,
THEN retain attempts, mark unstarted comparisons unknown and STOP without
repair, rerun, parameter changes or a successor.

## Requirement: Reproducible bounded evidence
The probe SHALL preserve original code/output, use two additive files and
pure helpers without old-module mutation, and write only its fresh four-file
root/log. It SHALL record exact seeds/roles,260-bit disclosure, physical
verification unavailability, resource and call budgets. It SHALL not claim
FER/SKR/qualification/route outcomes. Independent batch-end review and main
acceptance SHALL precede evidence promotion.

### Scenario: Tests and dry-run
GIVEN no main scientific dispatch,
WHEN validation runs,
THEN use fake graph/candidate/decoder or pure mathematics only, with zero
empirical reads, actual scientific construction/decoding or production writes.
