# Repository-Wide Two-Tier Research Workflow Simplification R1

## 1. Purpose

Replace the current one-size-fits-all research ceremony with two explicit tracks as the **repository-wide permanent default for all future research cycles**:

- **EXPLORE**: synthetic, fresh workspace output, bounded cost, no claim-bearing promotion;
- **DECIDE**: route gate, real data, expensive/irreversible execution, publication number, qualification or promotion.

This is not a D7 closeout convenience and not a D6-only exception. It governs all subsequent work in `HD-QKD_Polar_Comparison`, including NB-LDPC, NB-Polar preparation in this checkout, synthetic development, real-data validation, parameter scans, security/qualification work, algorithm comparisons, and future routes not yet named. D7 is evidence motivating the change; D6 is only its first consumer.

This workflow change must finish and be accepted before the separate D6 heavy-mainline packet may start.

Observed motivation from the completed D7 X1–X4 cycle: 24 cycle documents plus 6 task/prompt documents (about 3556 lines / 197 KB) accompanied about 44 minutes of decoder computation. X1 alone was a seconds-scale probe but accumulated separate failure, fix, rerun, authorization and multiple review records. The process remained scientifically safe but materially over-ceremonial.

## 2. Authority and boundaries

- Repository: `D:\Code\HD-QKD_Polar_Comparison`
- Branch: record the active intended branch; do not switch.
- Change name: `repository-wide-two-tier-research-workflow`
- Packet type: `WORKFLOW_PLAN_IMPLEMENT_REVIEW`
- No decoder, CAL/VAL, real-data, D6, D7-H, G1/G2, or formal execution.
- No cleanup, deletion, history rewriting, broad formatting, commit squashing, push, or modification of scientific results.
- Use Ponytail `lite`: implement the smallest durable rule set; do not build a workflow engine.

## 3. Source files to read first

- `AGENTS.md` §§1.1, 3, 6, 10.1–10.3
- `docs/research-cycle-sop.md` §§3, 6, 10
- `openspec/changes/standardize-task-packet-review-loop/**`
- `openspec/changes/research-cycle-sop-single-user-simplification/**`
- `docs/prompts/chatgpt-research-review.md`
- `docs/prompts/opencode-research-execution.md`
- D7 process evidence under `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/`

## 4. Allowed files

- new `openspec/changes/simplify-exploratory-vs-decision-research-workflow/**`
- `AGENTS.md`
- `docs/research-cycle-sop.md`
- `docs/prompts/chatgpt-research-review.md`
- `docs/prompts/opencode-research-execution.md`
- at most one small reusable exploratory template under `docs/prompts/` if the two existing prompts cannot express the distinction cleanly
- `docs/decision-log.md` (one concise decision entry)
- `AGENT_PROJECT_MEMORY.md` only for final accepted memory triage
- `docs/research_cycles/WORKFLOW-TWO-TIER-R1/**` with at most three files: `REVIEW_ENTRYPOINT.md`, `REVIEW_VERDICT.md`, `cycle_state.yaml`
- this task/prompt pair

Do not edit another file without returning `BLOCKED` with the exact need.

## 5. Required design

### 5.0 Repository-wide applicability and precedence

- The accepted two-tier policy becomes the default for every new research task, packet, OpenSpec change, experiment and result in this repository.
- `AGENTS.md` is the authoritative applicability/precedence rule; the SOP and reusable prompts implement it consistently.
- Every future task packet must declare exactly one track: `EXPLORE` or `DECIDE`. `EXPLORE_HEAVY` is an EXPLORE cost annotation, not a third lifecycle.
- Existing historical evidence and completed cycles remain unchanged. Active future work inherits the new policy at its next safe boundary; it does not need one migration document per old cycle.
- Project areas may add stricter scientific requirements, but may not reintroduce per-arm paperwork merely by using a different cycle name or method family.
- If an old packet conflicts with the accepted repository-wide policy and has not yet executed, the new policy governs process mechanics; its frozen scientific inputs, thresholds, budgets, no-overwrite rules and authorization boundaries remain binding.
- Real data, formal qualification, route-closing decisions and publication claims remain DECIDE regardless of algorithm family or estimated runtime.

### 5.1 EXPLORE track

Use only when all are true:

- synthetic or already-approved non-sensitive development input;
- fresh additive `workspace/` root or no-write probe;
- bounded and reversible;
- no FER/SKR/qualification/promotion/publication claim;
- no destructive overwrite or new user-facing external action.

Required artifacts for one coherent exploratory batch:

1. one task packet + paired prompt containing the preregistration and authorization boundary;
2. one result root or no-write transcript;
3. one append-only `EXPLORATION_LOG.md` or equivalent result record containing attempts, any engineering correction, final evidence and one batch-end review.

Rules:

- one user authorization may cover a frozen sequence of conditional diagnostic arms;
- the operator may continue between arms without a new packet or independent review when the preceding machine gate permits it;
- one engineering repair + rerun may be preregistered when scientific inputs, seeds, thresholds, data roles and tested hypothesis remain unchanged; preserve the failed attempt in the same log;
- independent review occurs once at the batch end, unless a failure would change scientific inputs or expand scope;
- multi-graph or multi-seed sampling is the default when graph/seed variability could confound the question;
- descriptive labels must include their scope and must not become immutable scientific predecessor facts merely because they are terminal strings;
- no separate authorization record, operator-return file, failure-verification file, repair-review file and rerun-review file for each small arm. Put the necessary facts in the single log.

### 5.2 DECIDE track

Use when any is true:

- frozen route/life-death gate;
- real/private/raw data;
- expensive, formal, irreversible or claim-bearing execution;
- result intended for a report, publication, qualification or promotion.

Keep:

1. accepted preregistration/plan;
2. Pre-EXECUTE review with exact command, budget, output absence and explicit user authorization;
3. one execution/result record;
4. independent Pre-RESULT review;
5. main-thread acceptance/route decision.

These may be three compact documents (`PREREG_AND_AUTH.md`, `RESULT.md`, `INDEPENDENT_ACCEPTANCE.md`) plus machine artifacts. Do not require a distinct document for each lifecycle state when one append-only record is unambiguous.

### 5.3 Gate classification and escalation

- The task packet must classify the batch `EXPLORE` or `DECIDE` before execution.
- Uncertainty defaults to DECIDE only when the concrete risk is named; do not default upward merely because a decoder is called.
- EXPLORE escalates to DECIDE before continuing if it reaches real data, route-closing thresholds, publication claims, destructive output, materially higher cost, or a change to scientific inputs/hypothesis.
- Pre-RESULT remains mandatory for DECIDE. For EXPLORE, one independent batch-end review replaces per-arm review.
- A failed engineering probe is not an algorithm result. A failed DECIDE gate remains immutable evidence.

### 5.4 Commits and dirty worktrees

- Prefer one coherent scoped milestone commit per exploratory batch or decision gate, not one commit per document.
- Use explicit allowlist staging in dirty worktrees; never `git add -A`.
- Git commit IDs are provenance, not authorization locks.

## 6. Required repository changes

- **W01**: create the complete OpenSpec proposal/design/tasks/delta spec before editing workflow rules.
- **W02**: supersede, do not silently contradict, `standardize-task-packet-review-loop`; preserve paired task packet + prompt as the handoff surface.
- **W03**: amend AGENTS.md scope, mandatory processes and §10 so the two tracks are the repository-wide default, EXPLORE batch-end review is explicitly valid, and the existing “Pre-RESULT before every development-result output” wording applies to DECIDE, not every synthetic diagnostic arm.
- **W04**: update the SOP lifecycle, task types, artifact expectations, authorization loop and examples.
- **W05**: update the two reusable prompts so operators/reviewers must name the track and apply the matching evidence contract.
- **W06**: add the compact DECIDE three-document option and EXPLORE single-log option; do not add more than one new template.
- **W07**: record the D7 process lesson and the rule that machine terminal labels are not automatically scientific facts.
- **W08**: remove or reconcile conflicting text across the edited files; scoped `rg` must show no remaining unconditional per-arm independent-review requirement.
- **W09**: run Markdown/link/path consistency checks and `git diff --check`; no numerical/decoder tests.
- **W10**: obtain one independent workflow review. Stop at `TWO_TIER_WORKFLOW_CANDIDATE_AWAITING_MAIN_ACCEPTANCE`; do not self-accept or start D6.
- **W11**: add a compact repository-wide applicability matrix covering at least synthetic diagnostics, synthetic route gates, real-data development, parameter scans, formal qualification, publication/report numbers, security calculations, implementation-only changes and documentation-only changes.
- **W12**: inspect all repository-level workflow authorities and reusable generic prompts named in Section 3 plus `README.md`/`AGENT_PROJECT_MEMORY.md` references discovered by scoped `rg`; either update an allowed authoritative file or list the exact non-authoritative historical reference that remains intentionally unchanged. Do not scan or rewrite every historical cycle.
- **W13**: make the durable accepted terminal exactly `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`; the shorter marker `TWO_TIER_WORKFLOW_ACCEPTED` may be retained as a compatibility alias for the D6 prerequisite.

## 7. Acceptance criteria

- The distinction is based on concrete scientific/operational risk, not file names or agent identity.
- The policy explicitly applies to every future project route, not only D7/D6 or the current task chain.
- EXPLORE can execute a frozen conditional batch with one authorization and one batch-end review.
- DECIDE retains explicit user authorization, Pre-EXECUTE, independent Pre-RESULT and main acceptance.
- Real data, route-closing gates and publication claims cannot be mislabeled EXPLORE.
- Failure retention, no-overwrite, exact/syndrome/undetected separation and reproducibility are not weakened.
- The new rules would reduce the completed D7 X1–X3 record to one packet/prompt, machine roots and one append-only log plus one review, while leaving X4 under DECIDE.
- Total new workflow-cycle documents do not exceed the three files permitted in Section 4.
- No production code, experiment or result changes.
- A reviewer can take an arbitrary future task (NB-LDPC, NB-Polar, scan, real-data or security) and classify it from the applicability matrix without inventing a third track.

## 8. STOP conditions

- Any proposal weakens user-only authorization for DECIDE, no-overwrite, real-data protection, claim boundaries or independent Pre-RESULT review.
- Existing rules cannot be reconciled without changing a file outside Section 4.
- The change starts building automation, schema engines, databases, signing/hashing systems or generalized workflow software.
- Independent review fails or finds a route by which a DECIDE task can silently enter EXPLORE.
- D6/mainline work starts before main-thread workflow acceptance.

Return `BLOCKED` with the exact conflict and one decision needed. Do not partially activate contradictory rules.

## 9. Return contract

Return exactly `COMPLETE` or `BLOCKED`.

`COMPLETE` must list acceptance IDs W01–W13, changed files, repository-wide authority/conflict scans, applicability-matrix checks, independent verdict, document count, explicitly preserved safety gates, commit/no-push state, and terminal `TWO_TIER_WORKFLOW_CANDIDATE_AWAITING_MAIN_ACCEPTANCE`.
