# Research-cycle workflow delta

## Requirement: Git SHALL be provenance, not the default execution gate

The workflow SHALL NOT require `HEAD == origin == implementation SHA`, a
stale-SHA grep, a checksum, or a commit containing its own identifier before a
single-user local research run.

### Scenario: Review records advance HEAD

- **WHEN** accepted code is followed only by review or lifecycle documentation
- **THEN** the run MAY proceed after scoped code/config cleanliness is verified
- **AND** the documentation commit SHALL NOT invalidate the accepted code

## Requirement: Pre-EXECUTE SHALL check scientific and overwrite risks

Before a claim-bearing or costly run, the reviewer SHALL verify the intended
branch, scoped file cleanliness, frozen command/inputs/thresholds, focused
tests, explicit user authorization, and absence of the target output.

### Scenario: A scoped file changed after review

- **WHEN** code, configuration, tests, or the execution packet has an unreviewed change
- **THEN** execution SHALL stop for focused review

## Requirement: Stronger revision locks SHALL be exceptional

Exact revision locking MAY be required only when the packet names a concrete
multi-writer, destructive, release, or evidence-integrity risk it prevents.

## Requirement: Review frequency SHALL follow scientific risk

Documentation-only commits and tiny unchanged-scope fixes SHALL NOT each
require independent review. Independent review remains required at plan
acceptance and at applicable Pre-EXECUTE and Pre-RESULT milestones.

## Requirement: Existing packets SHALL inherit the simplified Git rule

An active packet's SHA or remote-equality clause SHALL be non-binding unless it
names a concrete escalation risk. Its scientific scope, authorization, tests,
stop rules, and output protections SHALL remain binding.

## Requirement: Result semantics SHALL remain protected

Failures, partial results, skipped stages, leakage, and undetected outcomes
SHALL remain explicit. Existing outputs SHALL NOT be overwritten. Claim-bearing
results SHALL receive independent Pre-RESULT review before solidification.
