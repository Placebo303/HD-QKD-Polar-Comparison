# ADDED Requirements

## Requirement: Bounded paired edge-state exploration
The EXPLORE batch SHALL keep full-six cold and seeded arms independent, rebase retained baseline C2V to the branch prior, verify zero-state reference equivalence before scientific comparison, and retain actual vectors, states and partial outcomes. It SHALL use the frozen packet and independent batch-end acceptance; no new default, security or qualification claim follows.

### Scenario: Equivalence gate fails
- WHEN a zero-state baseline differs from the reference beyond the frozen tolerance or decision/status/iteration semantics
- THEN retain the mismatch and stop, without continuing the scientific arms or producing full-batch comparison numbers.

### Scenario: Branch prior changes
- WHEN a full-six branch uses a guessed one-hot prior row
- THEN initialize beliefs from the cleaned branch prior plus saved baseline C2V, subtract each old edge message for its extrinsic input, and score outputs using the original prior.
