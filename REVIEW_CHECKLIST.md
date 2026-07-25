# REVIEW_CHECKLIST.md

Use this checklist when reviewing changes.

## Baseline protection

- [ ] `src/`, `experiments/`, and `tools/` logic is unchanged unless explicitly requested
- [ ] No existing outputs under `results/` are overwritten
- [ ] No existing benchmark outputs under `comparison_bench/outputs_comparison/` are overwritten

## Schema stability

- [ ] CSV column names are unchanged
- [ ] JSON/YAML keys are unchanged
- [ ] CLI arguments are unchanged
- [ ] Core dataclass/function signatures are unchanged

## Scientific meaning

- [ ] `beta_eff_empirical` remains derived, not hand-filled
- [ ] Status values are not silently collapsed to `ok`
- [ ] `qldpc_reference` is not oversold as production qLDPC
- [ ] Leakage comparisons respect decomposition semantics

## Workflow hygiene

- [ ] Any behavior/architecture/workflow change went through OpenSpec first
- [ ] Changes are minimal and additive
- [ ] Memory triage was completed for the task
