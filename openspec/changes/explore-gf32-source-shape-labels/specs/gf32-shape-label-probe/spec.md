# ADDED Requirements

## Requirement: Fixed sparse-shape synthetic label test
The probe SHALL implement exactly the frozen EXPLORE packet for UUID
fd01e03e-3832-4f01-bdb1-eecd744e4b40. Custom n128/m52 graph profile, six seeds,
2M-inspired marginal shape and CONTROL-only grid selector SHALL remain fixed.
The paired arm intervention SHALL be H0D labels only.

### Scenario: Valid profile and pilot point
GIVEN all six preflight checks and the first eligible CONTROL-only point,
WHEN candidates pass gauge/rank/score gates,
THEN run independent paired holdout and report per-graph/paired accounting.

### Scenario: Failed gate
GIVEN a structural/math/candidate/control-range/resource failure,
WHEN the gate fires,
THEN retain attempts and unstarted uncertainty, STOP without repair or tuning.

## Requirement: Bounded evidence and scope
The probe SHALL use fresh four-file root and one append-only log; each
attempted call discloses260 syndrome bits. It SHALL distinguish exact success,
syndrome-consistent wrong and unavailable physical verification, and forbid
real reads, array exports, FER/SKR/route/qualification claims. Independent
batch-end review and main acceptance SHALL precede evidence promotion.

### Scenario: Test or dry-run
GIVEN no --execute dispatch,
WHEN tests or dry-run are entered,
THEN use fake decoder or pure mathematics only and produce no scientific
output or real-input reads.
