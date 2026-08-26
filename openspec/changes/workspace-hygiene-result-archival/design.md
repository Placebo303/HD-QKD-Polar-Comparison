# Design: workspace-hygiene-result-archival

## 0. Overview

Three small, independent moves: untrack one volatile manifest (G1), archive compact A-class summaries + one index under `comparison_bench/outputs_comparison/result_archive_summaries/` (G2), append one decision-log entry (G3). Ponytail discipline: no checksum layer, no backup system, no retry framework, no schema validation — Git already versions the summaries, and the raw outputs stay on disk. The only genuinely judgment-bearing logic is the A/B/C classification, which gets frozen criteria and a deterministic tiebreak; everything else is mechanical.

## 1. G1 Design — Untrack Volatile Manifest

**Failure mechanism being fixed**: the evidence test rewrites `"git_commit"` in `expanded_evidence_manifest.json` on every run, so a previously force-added file under an ignored directory (`workspace/` is blanket-ignored at `.gitignore` L20) shows a perpetual one-line noise diff.

**Mechanics**: `git rm --cached workspace/pytest-evidence-test/output/expanded_evidence_manifest.json` — removes it from the index only; the working-tree file survives and becomes plain ignored local data. The current unstaged "modified" state disappears with the commit.

**`.gitignore` entry**: add, next to the existing `workspace/` rule:

```
# Force-add guard: evidence-test manifest must stay untracked (workspace-hygiene-result-archival)
workspace/pytest-evidence-test/output/expanded_evidence_manifest.json
```

Strictly redundant while the L20 blanket rule stands — this is deliberate per D1: the explicit line documents why the file must never be force-added again and keeps protection if the blanket rule is ever narrowed. Marked as accepted redundancy, not an oversight.

**Scope discipline**: exactly this one path. If verification finds other tracked paths under `workspace/`, they are **reported only** (`git ls-files -- workspace/` output pasted into the completion report); handling them is out of scope by D1.

## 2. G2 Design — Selective Archival Policy

### 2.1 Live-status rule (frozen)

Classification input is captured at execution time via `git status --porcelain -- comparison_bench/outputs_comparison/`. The 38-entry reviewer list in proposal §Background Facts is orientation only; entries are added/removed from that live capture, never from memory of it.

### 2.2 A/B/C definitions (frozen)

A run directory or top-level entry `r` is classified:

- **A（结论承载型）** iff at least one of:
  - **A-crit-1**: referenced by selection results/tables inside `comparison_bench/outputs_comparison/final_ir_method_selection/`;
  - **A-crit-2**: cited by an existing `docs/decision-log.md` entry or directly evidencing its recorded conclusion;
  - **A-crit-3**: cited in `AGENT_PROJECT_MEMORY.md` as a conclusion-bearing result;
  - **A-crit-4**: implementer writes a one-line explicit reason that it directly supports an already-recorded conclusion (reason recorded in the classification table, reviewable).
- **C（半成品日志）**: any `*.partial_state.execution.log`.
- **B（中间诊断）**: everything else.
- **Tiebreak (deterministic)**: borderline → B. Under-classifying is cheap: append-only policy allows adding a summary later; deleting a wrongly-committed one does not.

The classification table (run dir → class → criterion hit → one-line justification) is written to `workspace/workspace-hygiene-result-archival/classification.md` (untracked scratch) and is the audit trail for what was and was not committed.

### 2.3 Archive artifact shape (frozen)

Root: `comparison_bench/outputs_comparison/result_archive_summaries/` — additive new subdir, consistent with the output policy ("new comparison outputs stay under outputs_comparison with additive naming"). Only these files become tracked:

- Per A-class run, mirroring the original relative path (e.g. `formal_ir_methods/<date_dir>/...`):
  - the run's metrics CSV verbatim copy (if present);
  - the run's `RUN_MANIFEST.json` (or equivalent manifest) verbatim copy;
  - if neither exists, one minimal hand-written `<run_name>.provenance.json`: `{run_dir, command, seed(s), data_identity, producing_git_commit, key_metrics}`.
- One total index `result_archive_summaries/index.csv`, columns:
  `run_dir,class,criterion,summary_files,conclusion_ref,decision_log_ref,memory_ref,seed,command,producing_git_commit,notes`
  (one row per archived run; `class` column also lets future readers see B/C exist but were intentionally not committed).

**Size guard (concrete failure mode: accidental large-binary commit)**: any single file >1 MB is excluded; parquet/npz/pkl/h5/ttbin extensions excluded outright. Whole-directory commits forbidden — only enumerated files are staged.

### 2.4 B/C handling (D2)

Not staged, not deleted, not moved. They remain untracked local data with unlimited retention. Nothing anywhere in this change may issue a delete against `outputs_comparison/**`.

## 3. G3 Design — Decision-Log Record

Append one entry to `docs/decision-log.md` using the file's own Template (Date / Decision / Context / Alternatives considered / Consequences), dated the execution date. Content records D2: B/C experiment data kept locally forever, nothing under `outputs_comparison/` ever deleted, append-only policy reaffirmed, rejected alternative = committing all raw outputs (noise + large binaries) and pruning old runs (destroys reproducibility provenance). This is the change's single permitted `docs/` touch; `AGENT_PROJECT_MEMORY.md` stays untouched — memory triage conclusions go through the memory-agent workflow instead.

## 4. Quiet-Period Gate (operational definition, frozen)

Before EACH git write operation (`rm --cached`, `add`, `commit` — three separate commits, three gate passes):

1. Main thread confirms no other agent/task is running (no active subagent, no background longrun/minrerun/routeA process);
2. Two consecutive `git status --porcelain` captures, ≥60 s apart, are byte-identical;
3. Any instability → abort that operation, report blocker with both status outputs; do not proceed, do not "wait it out" autonomously.

Gate confirmation (commands + timestamps + outputs) is recorded in the task completion evidence.

## 5. Commit Plan & Script Strategy

**Commits (frozen order, each gated per §4)**:

| # | Content | Message style |
|---|---|---|
| C1 | index deletion of the manifest + `.gitignore` entry | follow prevailing style read from `git log --oneline -15` at execution time; must mention the change name |
| C2 | `result_archive_summaries/**` (+ script if implemented) | same |
| C3 | `docs/decision-log.md` entry | same |

**Script (optional)**: if the A-class set makes manual copying tedious, add `comparison_bench/src/comparison_bench/cli/make_result_archive_summaries.py` — matching the existing `make_expanded_evidence_package.py` convention location. Constraints: stdlib + pandas only; walks only the classified A-run dirs read-only; writes only under `result_archive_summaries/`; idempotent (re-runnable, overwrites only its own prior outputs); no defensive machinery per the research-code engineering policy. If A-class count ≤3, skip the script and copy manually — fewer moving parts wins.

## 6. Rejected Alternatives (for the record)

- *Commit everything untracked*: floods history with parquet/binaries; contradicts compact-evidence practice in docs/research-cycle-sop.md.
- *Prune B/C after archiving*: destroys provenance; explicitly forbidden by D2.
- *Untrack all of workspace/*: scope creep beyond D1; blanket ignore rule already covers the future.
- *One combined commit*: mixes hygiene, data-policy record, and archival evidence; separate commits keep revert paths clean.

## 7. Verification Design

Read-only checks, no new tooling:

- G1: `git ls-files -- workspace/` must not contain the manifest; working-tree file still exists; report-only scan for other tracked workspace paths.
- G2: staged file list == classification table's A-set enumerated files; no file >1 MB; no forbidden extension; index.csv rows == archived runs.
- Final: `git status --porcelain` matches the expected delta exactly (openspec four files, `.gitignore`, decision-log, archive additions); zero deletions under `outputs_comparison/`; frozen zones byte-identical.
