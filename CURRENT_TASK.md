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

## Active Run — OpenSpec change `fix-candidate-loss-namespace`: Phase 4 rerun RUNNING (since 2026-08-26T01:52:41+08:00)

The Stage 0 rerun TERMINATED on 2026-08-25 (cross-loss shared sequence-pool
contamination) is fully recorded in AGENT_PROJECT_MEMORY.md (2026-08-25
entry) and `results/paper_grade_v4_rate_search_fix/DATA_PROVENANCE_INCIDENT_20260825.md`;
its forensic artifacts stay untouched. The formerly "pending decision"
rebuild scope is now the approved change below.

### Decisions (user-approved 2026-08-25, recorded in proposal.md/tasks.md)

- Q1 = re-verify the 16dB shared 56 cells (via full rebuild); Q2 = full
  grid, all 121 cells/tier; Q3 = quarantine-rename the old shared pool to
  `real_sequences_quarantined_20260825` (**T5.3, not yet executed, needs
  explicit authorization**); Q4 = `*_lossfix_v1` naming.
- Feasibility verified: four tiers' raw ttbin (+ `.1` shards) all on disk
  at `D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\`; materialization/gate
  tooling in-repo (`tools/materialize_loss_namespaced_candidates.py`,
  `tools/verify_candidate_namespace_gates.py`); extraction chain
  deterministic (byte-identical same-input reproduction).

### Phase 0–3 DONE

- Affected-cell exact census: 10∩16=56, 6∩16=56, 6∩10=40, 6dB union=67,
  three-tier union=94; 20dB shares 0 (`evidence/affected_cells.csv`).
- Materialization complete: 10dB×121 + 6dB×121 + 16dB×121 (83 rebuilt +
  38 backfilled byte-for-byte from old authoritative, sha256 proof in
  `backfill_from_old_authoritative_MANIFEST.csv`).
- Gates G0–G4 all PASS: G2 final = 1452 cross-tier array comparisons,
  0 collisions; G3 final = zero hash-level exact equality + strict tier-mean
  ordering (per-cell inversions diagnostic-only, no threshold — criteria
  reached after three revisions, lesson in AGENT_PROJECT_MEMORY.md
  2026-08-26 entry); G4 = 484 sidecar provenance fields pass.
- Frozen-baseline touch surface (all reviewed, default behavior unchanged):
  `export_joint_sequence_sidecar.py` +optional `pool_root` param,
  `run_e2e_pipeline.py` +passthrough flag,
  `routeA_run_formal_cross_loss.py` +new `--candidate-dirs` flag.

### Phase 4 RUNNING

- 10dB → 6dB → 16dB serial separated processes; output root (NEW path)
  `results/paper_grade_v4_rate_search_fix/four_loss_parts_frames300_lossfix_v1/`.
- Parallelism frozen: workers=12 / metric-jobs=12 / shards=16 (20 logical
  cores; user directive: use available cores). Science params frozen:
  frames300 / seed20260228 / tag-bits64. First tier 10dB main PID 9876
  (launcher PID 23336); liveness checks at t≈60s/300s passed (15 python
  processes, sustained full load).
- Monitoring entry points: task root
  `workspace/fix-candidate-loss-namespace/p4_20260826_020352/`
  (`launcher.log`, `launcher_err.log`, `liveness_300s.txt`, per-tier
  `loss_*_pid.txt` and `loss_*_stdout.log` / `loss_*_stderr.log`) and launch
  record `openspec/changes/fix-candidate-loss-namespace/evidence/phase4_launch_record.md`.

### Remaining after each tier completes

1. Per-tier validation check: validator passes 121/121.
2. T5 closeout: T5.1 cross-tier verification + v3 trend comparison →
   T5.2 old-vs-new report → T5.3 execute Q3 quarantine rename (explicit
   authorization required) → T5.4 decision-log/memory/CURRENT_TASK updates
   (closes the old Pending-decision item) → T5.5 memory triage +
   `/finish-change`.
- 20dB reuses existing artifacts (referenced only); no rerun.

## Verified Health (2026-08-22, pre-separation baseline)

- Checkpoint `6a58adb`: working tree clean; frozen baseline untouched.
- All modules byte-compile; safe smoke passes; scoped regression subset
  74 passed / 2 failed (both failures are session-sandbox TEMP
  PermissionErrors in multiworker parallel tests — environment artifact).

## Pending Environment Actions (non-code)

- ~~Push `main` and `polar-mainline`~~ DONE 2026-08-22: `polar-mainline`
  synced with `origin/polar-mainline` at `6f33a26`; side branches
  `codex/feat/polar-diagnostics-occupancy`, `project-restructure-20260427`
  pushed.
- Elevated-terminal cleanup of ACL-locked pytest temp dirs (23 root
  `pytest-cache-files-*`, `tmpw7zl0atk/`, locked `workspace/*.tmp`);
  exact script recorded in AGENT_PROJECT_MEMORY.md 2026-08-22 entry.

## Stop Conditions

- Do not modify frozen baseline logic under `src/`, `experiments/`, or `tools/`
- Do not overwrite existing benchmark outputs under `results/` or
  `comparison_bench/outputs_comparison/` unless explicitly asked
- Do not advance research-line OpenSpec changes here (see AGENTS.md §0)
