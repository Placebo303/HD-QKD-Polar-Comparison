# CURRENT_TASK.md

## Repository Role

This is the **binary Polar mainline** (branch `polar-mainline`). The formal
IR / NB-LDPC research line lives in `../HD-QKD_Polar_Comparison` and must
not be advanced here. Research-era content that previously accumulated in
this file was retired to git history on 2026-08-22 (crosstalk cleanup).

## Current Task — Route A-complete: bit-plane Polar-IR formalization

Strategy source: `总体判断.txt` (repo root). Mainline order is fixed:
Route A-complete → Route B-lite → Route C feasibility-only.

### Phase 0 — Baseline freeze (partially done)

- PRIMARY_REPORTING_MODE = actual_ir_finite_key
- BETA_BASELINE_ROLE = comparison_only
- NIU_2016_STATUS = not_supported_by_current_observables
- Remaining: baseline version note, workflow note, assumptions note;
  confirm authoritative result directories.

### Phase 1 — Engineering completion (work packages A1–A4)

- A1 bit-plane interface formalization: symbol→bit-plane mapping, layer
  ordering/indexing/naming, per-layer I/O tables, leak_EC accounting,
  beta_eff strictly as a derived metric.
- A2 verification chain: verification_bits_used_actual, pass/fail flags,
  configured-budget vs actual-transcript separation, block/point source
  tags.
- A3 epsilon_EC accounting: reconciliation verification failure-probability
  definition, auditable inputs, relation to eps_sec/eps_cor,
  epsilon_EC_source_tag.
- A4 security interface: bit-plane IR output into the actual-IR finite-key
  security master table, per-point provenance, old-vs-new compare table.

### Phase 2 — Paper-facing comparison (WP5)

leak_EC / epsilon_EC / SKR / finite-key drop / runtime versus existing IR
baselines, tabulated by loss / d / bw; main-text and supplementary figure
plan.

## Verified Health (2026-08-22, pre-separation baseline)

- Checkpoint `6a58adb`: working tree clean; frozen baseline untouched.
- All modules byte-compile; safe smoke passes; scoped regression subset
  74 passed / 2 failed (both failures are session-sandbox TEMP
  PermissionErrors in multiworker parallel tests — environment artifact).

## Pending Environment Actions (non-code)

- Push `main` (`6a58adb`) and `polar-mainline` from an unrestricted
  terminal (session git hits schannel SEC_E_NO_CREDENTIALS).
- Elevated-terminal cleanup of ACL-locked pytest temp dirs (23 root
  `pytest-cache-files-*`, `tmpw7zl0atk/`, locked `workspace/*.tmp`);
  exact script recorded in AGENT_PROJECT_MEMORY.md 2026-08-22 entry.

## Stop Conditions

- Do not modify frozen baseline logic under `src/`, `experiments/`, or `tools/`
- Do not overwrite existing benchmark outputs under `results/` or
  `comparison_bench/outputs_comparison/` unless explicitly asked
- Do not advance research-line OpenSpec changes here (see AGENTS.md §0)
