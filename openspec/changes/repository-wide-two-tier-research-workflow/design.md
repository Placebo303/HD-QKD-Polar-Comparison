# Design: repository-wide two-tier research workflow

## 1. Tracks and eligibility

`EXPLORE` applies only when all five hold:

1. synthetic or already-approved non-sensitive development input;
2. fresh additive `workspace/` root or no-write probe;
3. bounded and reversible;
4. no FER/SKR/qualification/promotion/publication claim;
5. no destructive overwrite or new user-facing external action.

`DECIDE` applies when any one holds:

1. frozen route / life-death gate;
2. real/private/raw data;
3. expensive, formal, irreversible, or claim-bearing execution;
4. result intended for a report, publication, qualification, or promotion.

Real data, formal qualification, route-closing decisions, and
publication claims are always `DECIDE`, regardless of algorithm family
or estimated runtime.

## 2. Precedence

- The accepted two-tier policy is the default for every new research
  task, packet, OpenSpec change, experiment, and result in this
  repository. `AGENTS.md` is the authoritative applicability/precedence
  rule; the SOP and reusable prompts implement it.
- Historical evidence and completed cycles remain unchanged. Active
  future work inherits the new policy at its next safe boundary without
  one migration document per old cycle.
- An unexecuted old packet in conflict: the new policy governs process
  mechanics; its frozen scientific inputs, thresholds, budgets,
  no-overwrite rules, and authorization boundaries remain binding.
- Project areas may add stricter scientific requirements but may not
  reintroduce per-arm paperwork by renaming the cycle or method family.

## 3. EXPLORE batch protocol

- One packet + paired prompt carries the preregistration and the
  authorization boundary for one coherent exploratory batch.
- One user authorization covers a frozen sequence of conditional
  diagnostic arms. The operator may continue between arms without a new
  packet or independent review when the preceding machine gate permits.
- At most one preregistered engineering repair + rerun, only with
  unchanged scientific inputs, seeds, thresholds, data roles, and tested
  hypothesis; the failed attempt is retained in the same log.
- Multi-graph / multi-seed sampling is the default when graph/seed
  variability could confound the question.
- One result root (or no-write transcript) plus one append-only
  `EXPLORATION_LOG.md` (or equivalent) carries attempts, the engineering
  correction, final evidence, and the batch-end review.
- No per-arm authorization record, operator-return file,
  failure-verification file, repair-review file, or rerun-review file.
- Descriptive labels must carry their scope and must not become
  immutable predecessor facts merely because they are terminal strings.

## 4. DECIDE protocol

Keep all five: accepted preregistration/plan; Pre-EXECUTE with exact
command, budget, output absence, and explicit user authorization; one
execution/result record; independent Pre-RESULT; main-thread
acceptance/route decision. The compact three-document option
(`PREREG_AND_AUTH.md`, `RESULT.md`, `INDEPENDENT_ACCEPTANCE.md`) plus
machine artifacts is permitted. One append-only record may replace
per-lifecycle-state documents when unambiguous. No document reduction
may drop a gate.

## 5. Gate classification and escalation

- The packet classifies the batch `EXPLORE` or `DECIDE` before execution.
- Uncertainty defaults to `DECIDE` only when the concrete risk is named;
  calling a decoder alone does not force `DECIDE`.
- `EXPLORE` escalates to `DECIDE` before continuing on: real data,
  route-closing thresholds, publication claims, destructive output,
  materially higher cost, or any change to scientific inputs/hypothesis.
- Pre-RESULT is mandatory for `DECIDE` result publication. For `EXPLORE`,
  one independent batch-end review replaces per-arm review.
- A failed engineering probe is not an algorithm result. A failed
  `DECIDE` gate remains immutable evidence.

## 6. Commits and dirty worktrees

- Prefer one coherent scoped milestone commit per exploratory batch or
  decision gate, not one commit per document.
- Use explicit allowlist staging in dirty worktrees; never `git add -A`.
- Commit IDs are provenance, not authorization locks.

## 7. D7 process lesson (W07)

D7 X1–X3 collapse to one packet/prompt, machine roots, one append-only
log, and one review; X4 stays `DECIDE`. Machine terminal labels are
scoped pre-registered classifications, not immutable scientific facts:
`D7_F_REVERSE_ORDER_REGRESSION` remains the historical machine label of
the accepted D7-F single-graph (n=16 paired, 2 discordant pairs) result
per `D7_F_CORRIGENDUM_R1.md`; it does not license general mechanism
claims about other graphs, block lengths, decoders, or routes. Future
citations must carry the label's scope.

## 8. Applicability matrix (W11)

`AGENTS.md` §1.2 carries the authoritative applicability matrix
(synthetic diagnostics; synthetic route gates; real-data development;
parameter scans; formal qualification; publication/report numbers;
security calculations; implementation-only changes; documentation-only
changes). The SOP classifies from that matrix and repeats only the
escalation rule.

## 9. Authority references (W12)

`README.md`, `AGENT_PROJECT_MEMORY.md`, `AGENT_HANDOFF.md`, and
`docs/CURRENT_MAINLINE.md` are pointers/records, not workflow
authorities. They remain unchanged here; memory updates happen only at
accepted memory triage.

## 10. Terminals (W13)

- Candidate stop (W10): `TWO_TIER_WORKFLOW_CANDIDATE_AWAITING_MAIN_ACCEPTANCE`.
- Durable accepted terminal:
  `TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`.
- `TWO_TIER_WORKFLOW_ACCEPTED` may remain a compatibility alias for the
  D6 prerequisite. Main acceptance is not granted by this change.
