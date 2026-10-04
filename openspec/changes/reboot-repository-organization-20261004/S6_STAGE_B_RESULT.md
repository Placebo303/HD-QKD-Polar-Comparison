# Stage B — live OpenSpec delta merge

Completed rows covered: 101 / 101.
Manifest rows: 930; included title rows: 343; omitted title rows: 587.
Archived source spec files with included clauses: 38.
Live destination spec files written: 38.

Only exact full scopes or expressly named title/section scopes from the frozen disposition table were copied. Ambiguous partials and absent deltas are recorded as zero-merge. The existing synth-batch-runner timing/stop clause was already equivalent, so it was not duplicated.

Every added section says it is historical accepted scope, that AGENTS.md and reboot handoff R1–R9 take precedence, and that it grants no new execution, acceptance, qualification, promotion, publication, decoder work, or probe restart.

No tests or scientific runs were performed; this task is documentation-only.

## Retained script failures

The first dry-run failed before writing: PowerShell here-string piped to wsl.exe -e bash -lc "cd /mnt/d/Code/HD-QKD_Polar_Comparison && .venv/bin/python -". Traceback: File "<stdin>", line 223, in <module>; KeyError: selected.
The oversized inline retry failed to create a process (Windows OS error 206: file name or extension too long). The first saved script draft then failed AST parsing with SyntaxError at line 114 (unterminated selector string) and, after that draft-only edit, at line 293 (unmatched closing bracket). No source spec was written by those attempts.

## Live destination files

- openspec/specs/consolidate-real-ir-evidence-package/spec.md
- openspec/specs/corrected-matched-empirical-p-finite-control/spec.md
- openspec/specs/degree2-layout/spec.md
- openspec/specs/finite-l1-degree/spec.md
- openspec/specs/formal-ir-comparison-owned-end-to-end-roadmap/spec.md
- openspec/specs/formal-ir-v38r1-posterior-binding-correction/spec.md
- openspec/specs/formal-ir-v40-decoder-cap-diagnostic/spec.md
- openspec/specs/formal-ir-v42-conditional-realism-diagnostic/spec.md
- openspec/specs/formal-ir-v43-soft-marginal-diagnostic/spec.md
- openspec/specs/formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation/spec.md
- openspec/specs/formal-ir-v65ar2-first-match-pipeline/spec.md
- openspec/specs/formal-ir-v67-multisession-feasibility-map/spec.md
- openspec/specs/formal-ir-v68-balanced-gf32-bit-partition/spec.md
- openspec/specs/formal-ir-v72p2-val-descriptive-smoke/spec.md
- openspec/specs/formal-ir-v72p2d2-orthogonal-oneblock-triage/spec.md
- openspec/specs/formal-ir-v72p2d3-gf32-contrast/spec.md
- openspec/specs/formal-ir-v72p2d4-cal-gf32-model-rate-audit/spec.md
- openspec/specs/formal-ir-v72p2d5-model-f-input-preparation/spec.md
- openspec/specs/formal-nonbinary-ldpc-v13-existing-data-diagnostics/spec.md
- openspec/specs/formal-nonbinary-ldpc-v13-r3-legacy-drift-audit/spec.md
- openspec/specs/formal-nonbinary-ldpc-v14-efficiency-gate/spec.md
- openspec/specs/formal-nonbinary-ldpc-v25-empirical-timestamp-channel-and-multilevel-factorization-gate/spec.md
- openspec/specs/formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate/spec.md
- openspec/specs/formal-nonbinary-ldpc-v5-multistage-ir/spec.md
- openspec/specs/formal-nonbinary-ldpc-v6-long-block/spec.md
- openspec/specs/formal-nonbinary-ldpc-v7-successor-ladder/spec.md
- openspec/specs/formal-nonbinary-ldpc-v8-reference-reproduction/spec.md
- openspec/specs/forward-app/spec.md
- openspec/specs/gf32-bidirectional-oracle/spec.md
- openspec/specs/gf32-de-decoder-calibration/spec.md
- openspec/specs/group-meeting-ir-large-comparison/spec.md
- openspec/specs/m2-accounting-replay/spec.md
- openspec/specs/mixed-degree-l1-finite-discriminator/spec.md
- openspec/specs/r3-fresh-graph-scaling/spec.md
- openspec/specs/rate-aligned-gf32-ensemble-feasibility/spec.md
- openspec/specs/research-cycle-workflow/spec.md
- openspec/specs/speed-up-nbldpc-v5-runtime-wrapper/spec.md
- openspec/specs/workflow/spec.md

## Included archived source files

- openspec/changes/archive/2026-10-04-add-nbldpc-l1-degree2-layout-completed/specs/degree2-layout/spec.md
- openspec/changes/archive/2026-10-04-consolidate-real-ir-evidence-package-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-comparison-owned-end-to-end-roadmap-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v38r1-posterior-binding-correction-completed/specs/formal-ir-v38r1-posterior-binding-correction/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v40-decoder-cap-diagnostic-completed/specs/formal-ir-v40-decoder-cap-diagnostic/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v42-conditional-realism-diagnostic-completed/specs/formal-ir-v42-conditional-realism-diagnostic/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v43-soft-marginal-diagnostic-completed/specs/formal-ir-v43-soft-marginal-diagnostic/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v65ar2-first-match-pipeline-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v67-multisession-feasibility-map-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v68-balanced-gf32-bit-partition-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v72p2-val-descriptive-smoke-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v72p2d2-orthogonal-oneblock-triage-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v72p2d3-gf32-contrast-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v72p2d4-cal-gf32-model-rate-audit-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-ir-v72p2d5-model-f-input-preparation-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v13-existing-data-diagnostics-completed/specs/formal-nonbinary-ldpc-v13-existing-data-diagnostics/spec.md
- openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v13-r3-legacy-drift-audit-completed/specs/formal-nonbinary-ldpc-v13-r3-legacy-drift-audit/spec.md
- openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v14-efficiency-gate-completed/specs/formal-nonbinary-ldpc-v14-efficiency-gate/spec.md
- openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v25-empirical-timestamp-channel-and-multilevel-factorization-gate-completed/specs/formal-nonbinary-ldpc-v25-empirical-timestamp-channel-and-multilevel-factorization-gate/spec.md
- openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate-completed/specs/formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate/spec.md
- openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v34-corrected-matched-empirical-p-finite-control-completed/specs/corrected-matched-empirical-p-finite-control/spec.md
- openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v5-multistage-ir-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v6-long-block-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v7-successor-ladder-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-formal-nonbinary-ldpc-v8-reference-reproduction-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-group-meeting-ir-large-comparison-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-m2real-accounting-replay-completed/specs/m2-accounting-replay/spec.md
- openspec/changes/archive/2026-10-04-repository-wide-two-tier-research-workflow-completed/specs/research-cycle-workflow/spec.md
- openspec/changes/archive/2026-10-04-research-cycle-github-chatgpt-opencode-handoff-completed/specs/workflow/spec.md
- openspec/changes/archive/2026-10-04-speed-up-nbldpc-v5-runtime-wrapper-completed/specs/spec.md
- openspec/changes/archive/2026-10-04-v72p2d10-mixed-degree-l1-finite-discriminator-completed/specs/mixed-degree-l1-finite-discriminator/spec.md
- openspec/changes/archive/2026-10-04-v72p2d10-r3-fresh-graph-scaling-completed/specs/r3-fresh-graph-scaling/spec.md
- openspec/changes/archive/2026-10-04-v72p2d11-forward-app-completed/specs/forward-app/spec.md
- openspec/changes/archive/2026-10-04-v72p2d12-finite-l1-degree-completed/specs/finite-l1-degree/spec.md
- openspec/changes/archive/2026-10-04-v72p2d7-gf32-bidirectional-oracle-completed/specs/gf32-bidirectional-oracle/spec.md
- openspec/changes/archive/2026-10-04-v72p2d8-rate-aligned-gf32-ensemble-feasibility-completed/specs/rate-aligned-gf32-ensemble-feasibility/spec.md
- openspec/changes/archive/2026-10-04-v72p2d9-gf32-de-decoder-calibration-completed/specs/gf32-de-decoder-calibration/spec.md
