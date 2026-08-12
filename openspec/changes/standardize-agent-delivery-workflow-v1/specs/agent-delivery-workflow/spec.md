# Agent Delivery Workflow

## ADDED Requirements

### Requirement: Complete frozen task packet

Delegated implementation SHALL begin only after the main thread freezes the
complete scope, test matrix, artifacts, commands, stop rules, and return
conditions. Acceptance items SHALL have stable IDs.

### Requirement: Difference-first reuse

A successor SHALL begin from the nearest accepted predecessor and an explicit
delta list. Unchanged artifact, transcript, provenance, invalid-run, replay,
and no-overwrite semantics SHALL be preserved.

### Requirement: Operator return conditions

An implementation operator SHALL return only a complete candidate or a
concrete blocker with reproducible evidence. A partial-status summary SHALL
not be treated as completion.

### Requirement: Bounded review cadence

The main thread SHALL normally review at specification freeze, complete
candidate delivery, and independent acceptance rather than after each small
implementation increment.

### Requirement: Layered evidence testing

Where artifact verification is in scope, tests SHALL distinguish byte drift,
locally re-signed semantic changes, re-signed indexes/manifests, and deep
cross-artifact reconstruction.

Tests SHALL use T0 compile/structural, T1 focused unit/tamper, T2 complete fake
qualification/replay, and T3 cross-version stages. T2/T3 SHALL run only at
milestones. Test-only execution and verification SHALL explicitly provide fake
runners and SHALL NOT enter production decoding, raw-data, long-run, or
evidence-output paths implicitly.

### Requirement: Safe efficient operation

Known Windows ACL environments SHALL use additive non-production workspace
roots with pytest cache disabled. An agent SHALL terminate only a process it
launched and positively identified. Dirty-worktree acceptance SHALL inspect
the task file manifest, untracked hashes, frozen-directory diffs, and official
output-root state.

### Requirement: Compact handoff

Handoffs SHALL report the change, deliverable, acceptance IDs, files, tests,
outputs, blocker, and next action without repeating durable project context.
