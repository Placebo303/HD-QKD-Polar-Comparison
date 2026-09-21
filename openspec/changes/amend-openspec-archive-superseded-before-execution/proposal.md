# Amend OpenSpec Archive: Superseded-Before-Execution — Proposal

- Charter: `AGENTS.md` §3 (workflow-rule changes REQUIRE an OpenSpec change) + §6 (OpenSpec Workflow).
- Track: **— (no track gate: implementation-only/docs-only change, no execution)**. Per `AGENTS.md` §1.2 applicability matrix. This change authorizes no execution, opens no `.ttbin`, consumes no budget, and makes no FER/SKR/route/qualification/publication claim.
- Precedent: `openspec/changes/archive/2026-09-11-formal-ir-future-nbpolar-app-transfer-superseded/archive.md` (disposition `SUPERSEDED_DRAFT / NEVER_IMPLEMENTED / NEVER_EXECUTED`, originals retained verbatim, no review/implementation/evidence implied).
- Trigger: four V80 changes (`v80-p1-rate-adaptive-rescue`, `v80-p2-finite-length-decomposition`, `v80-p3-real-hfull-census`, `v80-x1-cross-source-cliff`) archived 2026-09-21 as superseded before any run, now under `openspec/changes/archive/2026-09-21-v80-*-superseded/` (a concurrent rename may still be in flight; whatever path exists is the evidence).

## The gap (precise)

`AGENTS.md` §6 currently documents exactly one archive case:

> `/opsx-archive <name>` — Archive a completed change (merge delta specs into main)

There is **no case for a change that was frozen but never granted and never executed** — i.e. superseded-before-execution.

## Why it matters

Merging the spec deltas of a never-implemented change into `openspec/specs/` promotes unimplemented SHALL requirements into the live specification. Live SHALLs read as current authority: future packets can cite them, and work that was never granted can appear authorized. The four V80 changes carried effective SHALLs in their `specs/*/spec.md` while only their `proposal.md` bore SUPERSEDE banners — a silent merge would have made those SHALLs binding. The correct action (taken 2026-09-21, now to be documented) is to archive them as superseded-before-execution **without** merging the deltas, with a disposition record, originals preserved verbatim.

## Scope (frozen)

- A documentation/workflow clarification ONLY: two archive dispositions, the non-merge rule, the naming convention, the `archive.md` disposition-record requirement, and the retained-clause-index rule for successors.
- No behavior change to any research code. No change to `src/`, `workspace/`, `results/`, `comparison_bench/outputs_comparison/`, or any existing `openspec/changes/` directory.
- No commit, push, PR, or execution authorization granted by this change.

## Affected specs

- `specs/amend-openspec-archive-superseded-before-execution/spec.md` (delta: archive disposition records; completed vs superseded-before-execution; non-merge rule; non-citability of archived frozen clauses; successor retained-clause index; original-file preservation).
- `AGENTS.md` §6 (a few added lines only; no restructuring).
