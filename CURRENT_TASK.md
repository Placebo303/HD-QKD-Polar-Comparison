# CURRENT_TASK.md

## Current Task

Prepare the next real-information-reconciliation success-first work plan for `HD-QKD_Polar_Comparison`.

## Scope

- Keep agent rules centralized in `AGENTS.md`
- Keep durable decisions in `docs/decision-log.md`
- Keep reusable failures and fixes in `docs/troubleshooting.md`
- Use `openspec/` for any substantial change
- Use `docs/project-progress-plan-20260615.md` as the detailed current progress and next-plan document
- Use `docs/real-ir-success-first-plan-20260615.md` as the implementation handoff plan for other coding agents

## Stop Conditions

- Do not modify frozen baseline logic under `src/`, `experiments/`, or `tools/`
- Do not overwrite existing benchmark outputs under `results/` or `comparison_bench/outputs_comparison/` unless explicitly asked
- If a request changes behavior, architecture, prompt rules, tool semantics, or workflow rules, create/update an OpenSpec change first

## Current Status

- The `real-ir-success-first` change proposal has been successfully implemented and verified.
- The success metrics, classifier, representative subset, and diagnostic sweep integrations are complete.
- An audit run on the representative real-frame subset has been completed and documented in `docs/real-ir-success-audit-20260615.md`.

## Next Step

Perform the final information reconciliation method comparison and selection based on the audited evidence.

