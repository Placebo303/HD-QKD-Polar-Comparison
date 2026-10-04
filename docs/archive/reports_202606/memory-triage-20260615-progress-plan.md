# Memory Triage - 2026-06-15 Progress Plan

## Confirmed Facts Added By This Turn

- Current progress and error-correction method-selection plan details are documented in `docs/project-progress-plan-20260615.md`.
- `CURRENT_TASK.md` now points to `docs/project-progress-plan-20260615.md`.
- `AGENT_HANDOFF.md` now points to `docs/project-progress-plan-20260615.md`.
- Earlier recommended next OpenSpec change `select-ir-error-correction-method` is superseded by `real-ir-success-first`.
- `docs/ir-method-comparison-state-20260615.md` preserves the current decision-relevant method status, v2/v3 output state, and fragile points.
- Later clarification changed the next active direction from immediate final method selection to real IR success first.
- `docs/real-ir-success-first-plan-20260615.md` and `openspec/changes/real-ir-success-first/` now define the next implementation handoff for other agents.

## Why This Matters

This keeps the current progress snapshot separate from transient chat history and gives the next agent a durable path for first making non-Polar methods achieve verified real-data IR success, then comparing IR / error-correction methods for final selection.

## Follow-Up Memory Action

If `AGENT_PROJECT_MEMORY.md` is later normalized or rewritten, add the same confirmed facts there under the multi-agent workflow section.
