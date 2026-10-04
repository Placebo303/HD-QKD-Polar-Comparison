## ADDED Requirements

### Requirement: bounded residual-ranked whole-sweep probe
The research runner SHALL implement frozen R1–R5 with natural-reference control and an independent residual-ranked candidate, fixed inputs and fresh seeds, a strict first-frame natural-mode equality canary, original kernel math, explicit scoring versus applied-update costs, partial retention and independent acceptance. It SHALL not modify default decoder behavior.

#### Scenario: residual sweep
- WHEN the candidate starts a sweep
- THEN score every row from its fixed starting state, sort raw probability residual descending with exact row ties, and recompute each committed row using the latest state.

#### Scenario: equality or resource gate fails
- WHEN first-frame equality fails or a frozen resource cap is exceeded
- THEN retain actual partial evidence, stop without rerun/resume, and leave full comparisons/classification null for INCOMPLETE.
