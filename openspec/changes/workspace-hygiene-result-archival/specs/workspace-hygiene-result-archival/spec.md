# Spec: workspace-hygiene-result-archival

## Scope

This delta spec freezes a repository-hygiene change: untrack exactly one volatile test manifest (tracking-policy change) and introduce a selective archival policy for untracked experiment outputs under `comparison_bench/outputs_comparison/` (archival-policy change), plus one decision-log record of the retention policy. It deletes nothing, reruns nothing, and touches no frozen baseline.

In scope:
- Untracking `workspace/pytest-evidence-test/output/expanded_evidence_manifest.json` + an explicit `.gitignore` entry.
- A/B/C classification of live-untracked outputs; tracked compact summaries + one index file for A-class only.
- One appended entry in `docs/decision-log.md` recording the D2 retention policy.
- Quiet-period gating of all git write operations.

Out of scope:
- Any deletion or overwrite under `comparison_bench/outputs_comparison/**` or `workspace/**`.
- Any tracking change beyond the single D1 path; handling of other tracked `workspace/` artifacts (report-only).
- Committing raw parquet/binaries/whole run directories; any new experiment run; any schema change; edits to frozen zones, `AGENT_PROJECT_MEMORY.md`, or existing OpenSpec changes.

## Definitions

- **D1/D2/D3**: frozen user decisions as stated verbatim in `proposal.md §Frozen User Decisions`.
- **Quiet period**: main-thread confirmation that no other agent/task is running AND two consecutive `git status --porcelain` captures ≥60 s apart are byte-identical. Required before every git write operation.
- **Live inventory**: output of `git status --porcelain -- comparison_bench/outputs_comparison/` captured at execution time (T0.2); the proposal's background-facts list is orientation only.
- **A-class** / **B-class** / **C-class**: per design §2.2 (A-crit-1..4; C = `*.partial_state.execution.log`; B = remainder; borderline → B).
- **Archive root**: `comparison_bench/outputs_comparison/result_archive_summaries/` (new, additive, tracked).
- **Index**: `result_archive_summaries/index.csv`, column set per design §2.3.

## Requirements (SHALL)

### Tracking Policy

- **SHALL-T1** — The system SHALL remove exactly one path from git tracking: `workspace/pytest-evidence-test/output/expanded_evidence_manifest.json`, via `git rm --cached` (working-tree copy preserved). No other path SHALL be untracked.
- **SHALL-T2** — `.gitignore` SHALL gain one explicit entry for that exact path with a one-line comment naming this change.
- **SHALL-T3** — Verification SHALL confirm via `git ls-files -- workspace/` that the manifest is untracked and the working-tree file still exists.
- **SHALL-T4** — Any OTHER tracked path discovered under `workspace/` SHALL be reported only; no action SHALL be taken on it within this change.

### Archival Policy

- **SHALL-A1** — Classification SHALL be performed against the live inventory captured at execution time, never against a remembered list.
- **SHALL-A2** — A/B/C assignment SHALL follow design §2.2 criteria with the deterministic tiebreak (borderline → B); the full classification table (run_dir | class | criterion | justification) SHALL be recorded in `workspace/workspace-hygiene-result-archival/classification.md`.
- **SHALL-A3** — Only A-class runs SHALL be committed, and only as compact summaries: verbatim copies of each run's metrics CSV and run manifest, or a minimal provenance JSON when neither exists (`{run_dir, command, seed(s), data_identity, producing_git_commit, key_metrics}`).
- **SHALL-A4** — One total index `result_archive_summaries/index.csv` SHALL map every archived run directory → conclusion → provenance using the frozen column set.
- **SHALL-A5** — No commit SHALL contain any file >1 MB, any parquet/npz/pkl/h5/ttbin file, or any whole run directory; only enumerated files from the classification table SHALL be staged.
- **SHALL-A6** — B-class and C-class entries SHALL NOT be committed, deleted, or moved; they remain local with unlimited retention (D2).

### Retention Decision Record

- **SHALL-R1** — `docs/decision-log.md` SHALL receive exactly one appended entry, template-compliant (Date/Decision/Context/Alternatives considered/Consequences), dated the execution date, recording the D2 policy: B/C data kept locally forever, nothing under `outputs_comparison/` ever deleted, append-only reaffirmed.
- **SHALL-R2** — No other `docs/` path and no part of `AGENT_PROJECT_MEMORY.md` SHALL be modified by this change.

### Execution Gating

- **SHALL-G1** — Every git write operation (`rm --cached` / `add` / `commit`) SHALL be preceded by a fresh quiet-period pass, with command outputs and timestamps retained as evidence.
- **SHALL-G2** — On gate failure the operation SHALL abort and report a blocker with both status captures; autonomous waiting-and-retrying beyond one round SHALL be forbidden.

### Integrity Constraints

- **SHALL-I1** — `src/**`, `experiments/**`, `tools/**`, `results/**`, all existing OpenSpec changes, and all pre-existing files under `comparison_bench/outputs_comparison/**` SHALL remain byte-identical; the change SHALL produce zero deletions anywhere.
- **SHALL-I2** — Commits SHALL follow the frozen plan C1→C2→C3 (untrack+ignore → summaries+index → decision-log), each scoped to its task group.
- **SHALL-I3** — No CSV column name, JSON/YAML key, CLI argument, config key, or core function signature documented in `AGENT_PROJECT_MEMORY.md` §6 SHALL change (new files introduce new names only).

## Acceptance Mapping

| Area | Requirements | Verified by |
|---|---|---|
| Tracking policy (D1) | SHALL-T1..T4 | T2.2–T2.3 command outputs |
| Archival policy (A/B/C, summaries, index, guards) | SHALL-A1..A6 | classification.md + T3.2 staged-set check |
| Retention record | SHALL-R1..R2 | T4.2 review + T4.3 diff |
| Quiet-period gating | SHALL-G1..G2 | T0/T2.1/T3.3/T4.3 gate evidence |
| Integrity constraints | SHALL-I1..I3 | T5.1 full-status check |
