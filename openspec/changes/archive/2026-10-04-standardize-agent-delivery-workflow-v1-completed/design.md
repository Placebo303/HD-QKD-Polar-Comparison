# Design: Standardized Agent Delivery Workflow v1

The main thread owns planning, requirements, thresholds, task freezing,
acceptance, and scientific conclusions. An implementation subagent is an
operator only.

Before delegation, the main thread freezes one task packet containing allowed
and forbidden files, functionality, test matrix, commands, artifacts, stop
rules, and return conditions. The operator continues until all frozen items
are complete, or returns one concrete blocker with the failing command,
traceback, attempted remedies, and the single decision required.

Intermediate “not complete” reports are not task completion. Reviews occur at
specification freeze, complete candidate delivery, and independent
acceptance. Acceptance items have stable IDs. Successor work starts from the
nearest accepted predecessor with an exact delta list.

Tests run as T0 compile/structural checks, T1 focused unit/tamper checks, T2
complete fake qualification plus strict replay, and T3 cross-version
regression. T2/T3 run only at milestones. Test-only execution and verification
name fake runners explicitly.

Evidence validation distinguishes raw-byte tampering, re-signed local fields,
re-signed artifact indexes, and deep cross-artifact reconstruction. Windows
tests use additive workspace roots with pytest cache disabled. Long-running
processes are terminated only by their identified owner. Dirty-worktree review
uses an explicit file manifest, untracked hashes, frozen-directory diffs, and
official output-root checks.

Scientific gates, prepare/review/execute separation, immutable failure
retention, and no-rerun/no-tuning rules remain unchanged.
