# ADDED Requirements

## Requirement: Fixed bounded syndrome rescue
The EXPLORE probe SHALL keep graph/source/BP fixed and rescue only raw
syndrome failures using the frozen capped MRB order0/1 candidate set and
matched-prior selection, as defined in R1–R4 of its authority packet.

### Scenario: Candidate chosen without truth access
- GIVEN raw BP fails the original syndrome
- WHEN bounded MRB returns valid original-coordinate candidates
- THEN all candidates are scored with the same effective input prior,
  deterministic best is rechecked, and true recovery is measured separately.

### Scenario: Invalid or incomplete execution
- GIVEN numerical, resource or input failure
- WHEN the frozen batch encounters it
- THEN evidence is retained, further calls stop, and full performance stays
  unknown rather than being tuned, resumed or promoted without review.
