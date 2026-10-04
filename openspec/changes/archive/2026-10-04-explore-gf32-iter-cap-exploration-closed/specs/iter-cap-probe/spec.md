# ADDED Requirements

## Requirement: Fixed-input BP iteration-cap comparison
The EXPLORE probe SHALL retain I1–I3 science,change only max_iter90vs250,
capture same-return raw vectors and report exact and syndrome separately.

### Scenario: Complete paired evidence
- GIVEN frozen fresh paired synthetic inputs and independent dispatch
- WHEN both caps execute once
- THEN full pergraph/pair/transitions/costs and independently checkable vectors
  are retained within the finite synthetic ceiling,without route promotion.

### Scenario: Prefix or resource inconsistency
- GIVEN a numerical/prefix/resource/exception STOP
- WHEN partial evidence is retained
- THEN original and resource reasons remain visible,complete totals unknown,
  and no continuation or scientific rerun occurs.
