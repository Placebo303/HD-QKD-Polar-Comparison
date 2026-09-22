# Simplify the single-user research-cycle SOP

## Why

The repository's SHA-equality gates turned Git provenance into a recursive
authorization ceremony: recording a review changed `HEAD`, which immediately
invalidated the just-recorded equality. This delayed algorithm experiments
without preventing a concrete scientific or overwrite failure.

## What changes

- Review the intended branch, scoped files, frozen scientific contract, tests,
  authorization, and output non-overwrite state.
- Treat commit IDs as optional provenance, not as execution locks.
- Remove mandatory `HEAD == origin == implementation SHA`, stale-SHA grep, and
  self-referential commit binding from the default workflow.
- Keep independent scientific review, explicit execution authorization,
  additive outputs, failure retention, and Pre-RESULT review.
- Permit exact revision locking only when multiple writers, ambiguous Git
  state, destructive operations, or a demonstrated evidence-integrity incident
  creates a concrete need.

## Scope

Workflow documentation and handoff templates only. No algorithm, decoder,
dataset, result, or lifecycle authorization is changed by this proposal.
