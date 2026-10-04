## ADDED Requirements

### Requirement: Local shifted-source overlap diagnostic
The EXPLORE probe SHALL compute frozen iid source Bhattacharyya overlaps
for acceptedunitcycle codeword orbits without graph/decoder execution,
preserving nonunitnull,unitzero,duplicate and partial semantics.

#### Scenario: Complete overlap inventory
- WHEN acceptedcensus iscomplete and allrows processed
- THEN pergraph/perlength local overlap diagnostics SHALL be reported
  with no errorprobability/FER or route interpretation.

#### Scenario: STOP or incomplete input
- WHEN frozen witness/input/resource gates fail
- THEN attempts SHALL be retained,no retry and fullbatch totalsunknown.

#### Scenario: Execution authority
- WHEN independentimplementationPASS/acceptedpredecessor/maindispatch
- THEN ongoing user grant SHALL cover only this frozen synthetic diagnostic.
