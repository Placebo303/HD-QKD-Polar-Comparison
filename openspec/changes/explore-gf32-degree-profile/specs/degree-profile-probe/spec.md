# ADDED Requirements

## Requirement: Matched degree-profile diagnostic
The EXPLORE probe SHALL compare two frozen degree profiles at fixed
n/m/rank/field/disclosure and matched prior/label process/decoder settings,
with profile-aware admission, shared errors and own arm syndromes. It SHALL
retain actual matrices/vectors/maps and costs under packet D1–D6 and its
single-attempt budgets/no-overwrite/no-rerun/claim ceiling.

### Scenario: Profile construction or execution fails
- WHEN any frozen construction/admission/error/resource condition fails
- THEN next calls SHALL stop, actual partial evidence SHALL be retained,
  and complete performance totals SHALL remain null.

### Scenario: Complete diagnostic
- WHEN all paired calls finish
- THEN independent actual review SHALL precede main acceptance, with no
  route closure/qualification/security/FER/real-channel claim.
