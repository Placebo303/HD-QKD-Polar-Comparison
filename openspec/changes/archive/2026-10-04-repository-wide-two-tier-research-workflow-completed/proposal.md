# Proposal: repository-wide two-tier research workflow

## Why

The completed D7 X1–X4 cycle was scientifically safe but materially
over-ceremonial: ~24 cycle documents plus 6 task/prompt documents
(~3556 lines / 197 KB) accompanied ~44 minutes of decoder computation.
X1 alone was a seconds-scale probe but accumulated separate failure, fix,
rerun, authorization, and multiple review records. One-size-fits-all
ceremony delays algorithm work without preventing a concrete scientific
or overwrite failure (see `AGENTS.md` §1.1).

## What changes

- Make `EXPLORE` / `DECIDE` the repository-wide default for every future
  research task, packet, OpenSpec change, experiment, and result.
- Every task packet declares exactly one track before execution.
  `EXPLORE_HEAVY` is a cost annotation on `EXPLORE`, not a third lifecycle.
- `EXPLORE` (synthetic, bounded, reversible, no claim-bearing promotion):
  one user authorization covers a frozen conditional arm sequence; one
  append-only log carries attempts, the preregistered engineering
  correction, final evidence, and one batch-end review.
- `DECIDE` (route gate, real data, expensive/irreversible execution,
  publication number, qualification, promotion) keeps: accepted
  preregistration/plan, Pre-EXECUTE with exact command, budget, output
  absence and explicit user authorization, one execution/result record,
  independent Pre-RESULT, and main-thread acceptance. A compact
  three-document option (`PREREG_AND_AUTH.md`, `RESULT.md`,
  `INDEPENDENT_ACCEPTANCE.md`) plus machine artifacts is permitted.
- Add a repository-wide applicability matrix so any future task
  (NB-LDPC, NB-Polar, scan, real-data, security) classifies without
  inventing a third track.
- Durable accepted terminal for this workflow change:
  `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`.

## Supersession (W02)

This change explicitly supersedes the review-frequency / per-task
granularity reading of `standardize-task-packet-review-loop` and extends
`research-cycle-sop-single-user-simplification`. It preserves the paired
task packet + prompt as the handoff surface and preserves all `DECIDE`
safety gates: explicit user-only authorization, Pre-EXECUTE,
independent Pre-RESULT, main-thread acceptance, failure retention,
no-overwrite, real-data protection, and claim boundaries.

## Scope

Files this change modifies (later tasks; W01 creates only this OpenSpec
change):

- `openspec/changes/repository-wide-two-tier-research-workflow/**`
- `AGENTS.md` (scope, mandatory processes, §10)
- `docs/research-cycle-sop.md` (lifecycle, task types, artifacts,
  authorization loop, examples)
- `docs/prompts/chatgpt-research-review.md`
- `docs/prompts/opencode-research-execution.md`
- at most one small reusable exploratory template under `docs/prompts/`
- `docs/decision-log.md` (one concise entry)
- `AGENT_PROJECT_MEMORY.md` (final accepted memory triage only)
- `docs/research_cycles/WORKFLOW-TWO-TIER-R1/**` (at most
  `REVIEW_ENTRYPOINT.md`, `REVIEW_VERDICT.md`, `cycle_state.yaml`)
- the authorizing task/prompt pair itself

## Non-goals

- No automation, workflow engine, schema engine, or database.
- No hashing/signing or integrity-manifest machinery.
- No historical rewrite: completed cycles and evidence stay unchanged.
- No decoder execution, CAL/VAL, real-data, formal, or D6 work.
- No cleanup, deletion, formatting sweep, commit squashing, or push.
