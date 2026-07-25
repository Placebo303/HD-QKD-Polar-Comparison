# AGENT_HANDOFF.md

## Current State

- Repository-level agent rules are in `AGENTS.md`
- Durable memory is in `AGENT_PROJECT_MEMORY.md`
- OpenSpec is initialized under `openspec/`
- Durable decisions live in `docs/decision-log.md`
- Reusable fixes live in `docs/troubleshooting.md`
- Detailed current progress and phased error-correction method-selection plan live in `docs/project-progress-plan-20260615.md`
- Real IR success-first implementation plan lives in `docs/real-ir-success-first-plan-20260615.md`
- Current method-state summary lives in `docs/ir-method-comparison-state-20260615.md`

## What Exists

- `openspec/project.md`
- `openspec/changes/`
- `openspec/specs/`
- `openspec/changes/real-ir-success-first/`

- The `real-ir-success-first` OpenSpec change has been successfully implemented, tested, and verified.
- Success classification columns `real_ir_success` and `success_classification` are fully integrated.
- A representative real-data subset has been created and evaluated.
- The audit report summarizing these baseline evaluations is documented in `docs/real-ir-success-audit-20260615.md`.

## Next Steps

- Final method selection is ready to be conducted based on the verified success evidence established in the audit report.
- Sweeps can be performed on the representative subset config `comparison_bench/configs/benchmark_representative.yaml` or expanded to larger datasets safely.

