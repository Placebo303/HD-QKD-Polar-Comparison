# Review entrypoint: WORKFLOW-TWO-TIER-R1

- **Cycle ID**: `WORKFLOW-TWO-TIER-R1`
- **Lifecycle / terminal**: `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`
- **Change name**: `repository-wide-two-tier-research-workflow`
- **OpenSpec path**: `openspec/changes/repository-wide-two-tier-research-workflow/`
  (`proposal.md`, `design.md`, `tasks.md`,
  `specs/research-cycle-workflow/spec.md`)
- **Authority**: `.workbuddy/tasks/WORKFLOW_TWO_TIER_RESEARCH_SIMPLIFICATION_R1_TASK_PACKET.md`
  (frozen packet). The delta spec is the normative contract.
- **Main-thread acceptance**: accepted 2026-09-13 after independent
  `PASS_WITH_FINDINGS`; F1/F2/F3/F7 are applied, F4 is resolved by accepted
  memory triage, F5 is acknowledged, and F6 remains archive-time only. This
  acceptance activates the repository-wide workflow policy but grants no D6,
  decoder, real-data, or other execution authorization.

## Scope and dirty-worktree note

The worktree is dirty (many unrelated modified/untracked files). **No commit was
made and nothing was pushed**; the candidate is a working-tree change set
confined to the scoped manifest below. Pre-existing unrelated modifications in
these files were preserved byte-for-byte and are noted per file.

Authoritative scoped editable manifest:

- `AGENTS.md` (pre-existing unrelated edits: §8 venv interpreter + `Verify:`
  bullet; §10.2 manual copy-paste/no-bridge bullet — preserved)
- `docs/research-cycle-sop.md` (pre-existing edits: §0 manual handoff, §6/§10
  additions — preserved)
- `docs/prompts/chatgpt-research-review.md` (clean before this change)
- `docs/prompts/opencode-research-execution.md` (pre-existing manual-handoff
  paragraph — preserved)
- `docs/decision-log.md` (pre-existing 2026-09-12 manual-handoff entry preserved;
  the new 2026-09-13 entry is inserted above it)
- `openspec/changes/repository-wide-two-tier-research-workflow/design.md`
  (one wording fix in §8 only)
- new `docs/research_cycles/WORKFLOW-TWO-TIER-R1/REVIEW_ENTRYPOINT.md`
- new `docs/research_cycles/WORKFLOW-TWO-TIER-R1/cycle_state.yaml`

No other file was edited.

## Naming-discrepancy resolution

The OpenSpec change directory is `repository-wide-two-tier-research-workflow`,
which follows packet §2 "Change name". The packet §4 slug
`simplify-exploratory-vs-decision-research-workflow` is treated as a stale
working name and was not used.

## Acceptance checklist (expected one-line outcome)

- **W01** — OpenSpec change exists with proposal/design/tasks/delta spec; the
  delta spec is the normative contract. *(done before this review)*
- **W02** — Explicit supersession of the per-task review-frequency reading of
  `standardize-task-packet-review-loop`; extension of
  `research-cycle-sop-single-user-simplification`; paired packet+prompt and all
  DECIDE safety gates preserved (proposal §Supersession, decision-log entry).
- **W03** — `AGENTS.md`: §0 bullet, new §1.2 two-tier default + matrix,
  §3 track declaration, DECIDE-scoped Pre-EXECUTE/Pre-RESULT, §10.1/§10.3
  EXPLORE batch-end review.
- **W04** — SOP §3 EXPLORE flow, §4 compact options, §5/§6 track handling,
  §6.4 declared track, §9 checklist item, §10 DECIDE scoping.
- **W05** — Both reusable prompts carry `TRACK`; reviewer gets
  `EXPLORE_BATCH`; operator gets track-conditional artifacts and principles.
- **W06** — Compact DECIDE three-document option and EXPLORE single-log option
  documented; no new template file added.
- **W07** — D7 lesson recorded: machine terminal labels are scoped
  pre-registered classifications, not immutable facts (SOP §3,
  decision-log entry).
- **W08** — Scoped `rg` shows no remaining unconditional per-arm
  independent-review requirement; all matches are track-scoped.
- **W09** — Markdown/link/path consistency and `git diff --check` run; no
  numerical/decoder tests.
- **W10** — One independent workflow review (this entrypoint); no
  self-acceptance, no D6 start. **PENDING.**
- **W11** — Authoritative applicability matrix in `AGENTS.md` §1.2 covering all
  named work types.
- **W12** — Repository-level workflow authorities inspected; intentionally
  unchanged non-authoritative references listed below.
- **W13** — Durable accepted terminal
  `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`; alias
  `TWO_TIER_WORKFLOW_ACCEPTED`.

## Review commands

Track declaration and remaining-conflict scan:

```sh
rg -n "TRACK|EXPLORE_HEAVY|EXPLORATION_LOG" \
  AGENTS.md docs/research-cycle-sop.md docs/prompts/*.md

rg -n "before every development-result|only where required by §10|per-arm" \
  AGENTS.md docs/research-cycle-sop.md \
  docs/prompts/chatgpt-research-review.md \
  docs/prompts/opencode-research-execution.md
```

Scoped whitespace/conflict check:

```sh
git diff --check -- AGENTS.md docs/research-cycle-sop.md \
  docs/prompts/chatgpt-research-review.md \
  docs/prompts/opencode-research-execution.md \
  docs/decision-log.md \
  openspec/changes/repository-wide-two-tier-research-workflow
```

## W12: intentionally unchanged non-authoritative references

These are pointers/records, not workflow authorities; they are intentionally
left unchanged. `AGENT_PROJECT_MEMORY.md` is updated only at accepted memory
triage, not during this candidate.

- `README.md` lines ~134–138 — recommended-usage pointer to the SOP.
- `AGENT_PROJECT_MEMORY.md` — the 2026-08-28 Pre-RESULT/no-exception entry and
  the 2026-09-05 coder-fast → reviewer-go rule; both remain as historical
  records.
- `AGENT_HANDOFF.md` line 13 — collaboration-SOP pointer.
- `docs/CURRENT_MAINLINE.md` line 68 — pointer to the SOP review loop.

## Safety gates preserved

Explicit user-only authorization for DECIDE, no-overwrite, real-data
protection, claim boundaries, independent Pre-RESULT, failure retention,
exact/syndrome/`undetected` separation, and reproducibility are unchanged.

## Post-review corrections (after REVIEW_VERDICT.md)

Applied within the same scoped files immediately after the independent review:
- F1: `tasks.md` W02–W13 checked to match `cycle_state.yaml`.
- F2: `AGENTS.md` §1.2 synthetic-route-gate row now states the route-closing decision itself is DECIDE.
- F3: SOP §6.1/§10.3 review-frequency wording is now `DECIDE`-qualified.
- F7: fixed nested bold in the `AGENTS.md` §3 Pre-RESULT bullet.

Carried to main acceptance / memory triage:
- F4: `AGENT_PROJECT_MEMORY.md` entries (2026-08-28 Pre-RESULT/no-exception; 2026-09-05 coder-fast → reviewer-go) to be annotated at accepted memory triage.
- F5: packet naming deviation acknowledged — packet §2 change name used; packet §4 slug was a stale working name.
- F6: archive-time track qualifier for `research-cycle-sop-single-user-simplification` when it is archived.

Verdict: `PASS_WITH_FINDINGS` (`REVIEW_VERDICT.md`); no rework gate.

## Main-thread acceptance

Accepted on 2026-09-13 with terminal
`TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`; compatibility alias
`TWO_TIER_WORKFLOW_ACCEPTED` is valid for successor prerequisite checks.
The packet §2 change name `repository-wide-two-tier-research-workflow` is
authoritative; the packet §4 slug is stale. No commit or push was made, and no
scientific execution is authorized by this acceptance.
