# ADDED Requirements

## Requirement: Fixed admitted-source comparison
The EXPLORE probe SHALL read only fixed selected matrices from the accepted
common-seed canary, retain source provenance and run the frozen paired label/BP
comparison with a new frame namespace/identity. It SHALL follow packet A1–A5
and change no old artifact or legacy CLI default.

### Scenario: Legacy execution inputs omitted
- WHEN optional new execution inputs are omitted
- THEN existing degree CLI identity/root/frame plan/behavior SHALL be unchanged.

### Scenario: New batch inputs explicit
- WHEN the thin admitted-source CLI executes
- THEN all artifacts/root checks/seed maps SHALL use its same fixed local
  identity and plan, with no global mutation or prior namespace inheritance.

### Scenario: Source or label validation fails
- WHEN source provenance/profile or label admission fails
- THEN next calls SHALL stop, actual partial evidence SHALL be retained and
  complete performance totals SHALL be null, without fallback or rerun.
