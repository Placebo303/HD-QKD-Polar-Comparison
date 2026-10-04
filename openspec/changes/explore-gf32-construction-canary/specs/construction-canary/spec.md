# ADDED Requirements

## Requirement: Bounded first-admitted construction
The EXPLORE canary SHALL use the same frozen max8 construction-seed protocol
for both fixed profiles, retain all actual diagnostics/matrices, and select
only the first commonly admitted pair at the same seed/j within each graph-ID
group. It SHALL obey packet C1–C4/caps,
execute no labels/decoder, and infer no performance or route claim.

### Scenario: Sequence exhausts
- WHEN none of all8 fixed paired attempts admits both profiles at the same j
- THEN the group SHALL be recorded EXHAUSTED and remaining fixed graph-ID
  groups SHALL continue, with no added seed or performance-dependent selection.
- AND completion SHALL require all6 groups selected or exhausted; a resource
  or unexpected-error STOP SHALL be INCOMPLETE.

### Scenario: Resource or unexpected failure
- WHEN the frozen limit or unexpected failure occurs
- THEN the next call SHALL stop and partial evidence SHALL be retained.

Authoritative selection is packet FROZEN v2: first common paired admitted
seed within each graph-ID group, both arms attempted after expected failure;
all unsuccessful and unselected actual matrices retained. Earlier independent
profile-selection wording is superseded before scientific execution.
