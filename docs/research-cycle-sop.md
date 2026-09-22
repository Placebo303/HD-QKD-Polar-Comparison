# GitHub-centered ChatGPT/OpenCode research-cycle SOP

This is the default collaboration protocol for this research repository. It is
deliberately small: Git preserves provenance and recovery, ChatGPT plans and
reviews, OpenCode implements, and the user/main reviewer owns acceptance and
execution authority. Git commit identity is not an execution capability.

## 0. Manual handoff only

All ChatGPT/Codex ↔ OpenCode handoffs for this project are manual copy-paste
handoffs through the packet/prompt and operator-return files. Do not invoke an
automatic MCP/bridge callback loop, create a bridge-managed session, or treat
chat-to-chat delivery as durable project state. The globally installed bridge
and skills may remain installed, but this repository workflow does not call
them unless the user explicitly opts back in through a later workflow change.

## 1. First principle

The purpose of this workflow is to accelerate scientifically sound,
high-performance information-reconciliation algorithms. Correction success,
leakage, runtime/resource cost, and net accepted-frame key yield come first.
Packaging, generalized infrastructure, adversarial audit machinery, and mature
library conventions are deferred unless they prevent wrong science,
irreproducibility, unauthorized expensive work, or destructive overwrite.

## 2. Roles

| Role | Owns | Must not do |
|---|---|---|
| User/main reviewer | Scientific objective, thresholds, acceptance, formal execution authorization | Treat an agent's self-report as acceptance |
| ChatGPT | Plan critique, literature/scientific reasoning, read-only code/data review, claim boundaries | Silently assume a branch/SHA, edit through the GitHub reader, grant execution authority |
| OpenCode | Frozen implementation, focused tests, development runs, evidence organization | Change requirements, thresholds, seeds, or status; self-accept; start unauthorized formal runs |
| Git/GitHub | Versioned source of truth and exchange surface | Replace raw external data storage |

Chat output is not durable project state. A ChatGPT verdict or OpenCode return
becomes durable only after it is copied into the cycle documents and committed.

## 3. Lifecycle

```text
IDEA
  -> PLAN_CANDIDATE
  -> PLAN_ACCEPTED | PLAN_REVISE | CLOSED
  -> IMPLEMENTATION_CANDIDATE
  -> DEVELOPMENT_RESULT_REVIEW
  -> ACCEPTED | REVISE | CLOSED
  -> FORMAL_EXECUTION_AUTHORIZED   (only by explicit user authorization)
  -> FORMAL_RESULT_REVIEW
  -> CLOSED | SUCCESSOR_PROPOSED
```

Engineering acceptance, development evidence, formal execution, scientific
qualification, and promotion are separate claims. A test pass is not an
algorithm success; a residual improvement is not exact recovery; a development
result is not qualification. Machine terminal labels are scoped pre-registered
classifications, not immutable scientific facts; citations carry their scope
(D7-F corrigendum precedent,
`docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/D7_F_CORRIGENDUM_R1.md`).

The same lifecycle applies with one track selected (`AGENTS.md` §1.2). `DECIDE`
work follows the flow above. A bounded synthetic `EXPLORE` batch follows the
compressed flow:

```text
EXPLORE (bounded synthetic batch; AGENTS.md §1.2)
  IDEA
    -> one packet + paired prompt declaring EXPLORE and freezing the conditional arm sequence and authorization boundary
    -> one user authorization
    -> arms run serially while the preceding machine gate permits (at most one preregistered engineering repair + rerun)
    -> one append-only EXPLORATION_LOG.md per batch
    -> one independent batch-end review
    -> route decision (accept evidence / next batch / escalate to DECIDE)
```

## 4. Per-cycle files

Use the existing OpenSpec change as the plan and add one small cycle folder:

```text
openspec/changes/<change-name>/
  proposal.md
  design.md
  tasks.md
  specs/.../spec.md

docs/research_cycles/<cycle-id>/
  REVIEW_ENTRYPOINT.md
  EXECUTION_PACKET.md
  OPERATOR_RETURN.md
  RESULT_SUMMARY.md
  REVIEW_VERDICT.md
  cycle_state.yaml
```

Do not duplicate the complete specification in every file.
`REVIEW_ENTRYPOINT.md` is an index; `EXECUTION_PACKET.md` contains the exact
operator contract; result and verdict files contain deltas and evidence.

Recommended `cycle_state.yaml`:

```yaml
cycle_id: V37R1
state: PLAN_CANDIDATE
accepted_plan: false
implementation_accepted: false
development_execution_authorized: false
formal_execution_authorized: false
scientific_promotion: false
```

Commit IDs may be added to a result for provenance, but are not recursive
authorization gates and need not be embedded in lifecycle commits.

Compact alternatives to the full folder:

- **EXPLORE batch**: one packet+prompt pair in `.workbuddy/tasks/`; one fresh
  additive `workspace/` root or no-write transcript; one append-only
  `EXPLORATION_LOG.md` (attempts incl. failures, the preregistered engineering
  repair if used, final evidence, one batch-end review).
- **DECIDE gate compact option**: `PREREG_AND_AUTH.md`, `RESULT.md`,
  `INDEPENDENT_ACCEPTANCE.md` plus machine artifacts and `cycle_state.yaml`.
  One append-only record may replace per-state documents when unambiguous; no
  document reduction may drop a gate.

## 5. ChatGPT review sequence

1. Make the plan or implementation candidate available in the intended branch.
2. Copy the prompt from `docs/prompts/chatgpt-research-review.md`.
3. Fill repository, branch, cycle ID, `TRACK` (`EXPLORE | DECIDE`), review kind,
   and entrypoint. Use `REVIEW_KIND: EXPLORE_BATCH` for an EXPLORE batch-end
   review; DECIDE keeps `PLAN | IMPLEMENTATION | DEVELOPMENT_RESULT |
   FORMAL_RESULT`.
4. Require ChatGPT to inspect the scoped files and current diff rather than
   accepting a self-reported PASS.
5. Copy the returned fixed-schema review into `REVIEW_VERDICT.md`.
6. Commit corrections or acceptance as a separate milestone.

An EXPLORE review covers the frozen arm sequence and the single log and must
not demand per-arm files.

If ChatGPT cannot inspect the scoped files or evidence, its comments remain
advisory. A commit ID alone never makes a review valid.

## 6. OpenCode execution sequence

1. Start from the accepted plan and intended branch.
2. Copy the prompt from `docs/prompts/opencode-research-execution.md`.
3. OpenCode confirms the intended branch and declared `TRACK` (`EXPLORE` or
   `DECIDE`), reads the named packet, and checks only the scoped
   code/config/test files for unreviewed changes.
4. It changes only allowed files and runs only authorized development work.
   For `EXPLORE`, the operator continues between frozen arms only while the
   preceding machine gate permits, records each arm in the single log, and
   creates no per-arm packets, returns, or reviews.
5. It returns either `COMPLETE` or a concrete `BLOCKED` report.
6. Copy the result into `OPERATOR_RETURN.md`, inspect the diff, and push an
   implementation candidate for independent review.

The user manually carries the prompt to OpenCode and manually returns the
operator receipt to the main Codex/ChatGPT thread. Neither agent should call
the cross-agent bridge as a substitute for these steps.

Use at most two OpenCode workers and serialize work that touches the same file,
test root, output root, or Git state. Prefer exact paths and restricted `rg`;
do not use broad recursive scans on this Windows workspace.

### 6.1 Default review-to-next-packet loop

Every `COMPLETE` or `BLOCKED` operator return enters the same default loop:

```text
operator return
  -> main-thread proportional review
  -> ACCEPT | REWORK | BLOCKED | ROUTE_DECISION | CLOSED
  -> next task packet + paired prompt, when continuation is authorized
```

The main thread reviews the return before treating it as accepted. Check the
active packet's stable acceptance IDs, changed-file manifest, literal test and
execution evidence, lifecycle/authorization state, protected outputs, claim
ceiling, and remaining blocker. Scale the depth to scientific risk: a tiny
documentation correction does not require the same audit as decoder code or a
claim-bearing result.

After the review, **default to producing the next appropriate task package and
its companion prompt**. Do not wait for the user to repeat “continue” when the
next bounded step follows directly from an accepted route. Pause without a new
executable handoff only when:

- the current route is terminal or intentionally stopped;
- a concrete blocker still lacks evidence or a safe scoped remedy;
- the next route requires a scientific choice that belongs to the user/main
  reviewer;
- the next action is claim-bearing, costly, formal, destructive, or otherwise
  requires fresh explicit user authorization;
- no scientifically useful next step exists.

In the authorization case, it is still appropriate to produce a freeze or
Pre-EXECUTE review pair, but the prompt must stop before execution and must not
ask an operator to manufacture or infer authorization.

This default main-thread review does not imply two duplicative reviews. Use a
separate independent reviewer only where required by §10: for `DECIDE`, at
frozen-plan or risky implementation acceptance, or where the active packet names
a concrete independence need; for `EXPLORE`, the one batch-end review in §10.3.
Batch low-risk documentation and mechanical corrections into the next
milestone review.

For an `EXPLORE` batch, the loop runs once at batch end: one packet/prompt
covers the frozen arm sequence, and no per-arm packet or review is created.

### 6.2 Task-package types

Choose the smallest type that reaches the next evidence or decision gate:

| Type | Use | Normal stop point |
|---|---|---|
| `EXPLORE` / `ATTRIBUTION` | Bounded, non-formal hypothesis discrimination | Evidence summary and route decision |
| `PLAN` / `FREEZE` | OpenSpec, preregistration, thresholds, commands and budgets | Frozen candidate; no execution |
| `IMPLEMENT` / `REWORK` | Scoped code and tests for an accepted contract | Implementation candidate or exact blocker |
| `CODE_REVIEW` / `PACKET_REVIEW` | Independent read-only acceptance review | PASS/FAIL; no execution authority |
| `PRE_EXECUTE` | Fresh readiness review for a costly or claim-bearing run | Await explicit user authorization |
| `EXECUTE` | Exactly the explicitly authorized bounded invocation | Operator return; result not accepted |
| `PRE_RESULT` | Independent review of actual artifacts and semantics | PASS/FAIL before solidification |
| `ACCEPT` / `CLOSEOUT` | Record accepted scope, state transition and durable memory | Accepted milestone and next route |
| `ADDENDUM` | Narrow correction to a frozen packet or review | Superseding delta without silent reinterpretation |

Every packet declares exactly one track (`TRACK: EXPLORE` or `TRACK: DECIDE`)
before execution per `AGENTS.md` §1.2; `EXPLORE_HEAVY` is a cost annotation
only. `EXPLORE`/`ATTRIBUTION` packets are normally EXPLORE; `PRE_EXECUTE`,
`EXECUTE` and `PRE_RESULT` packets are DECIDE.

A single heavy packet may combine adjacent non-conflicting types—for example
`PLAN_IMPLEMENT_REVIEW`—when it has one coherent scope, all foreseeable
acceptance items are frozen up front, and no mandatory authorization or
independence gate is crossed internally. Never combine execution with its own
Pre-RESULT acceptance.

### 6.3 Location and standardized names

All new operational handoff pairs live in:

```text
.workbuddy/tasks/
```

Use one common stem and exactly two files:

```text
<CYCLE>_<STAGE>_<ACTION>_<REV>_TASK_PACKET.md
<CYCLE>_<STAGE>_<ACTION>_<REV>_PROMPT.md
```

Naming rules:

- uppercase ASCII letters, digits and underscores only;
- `CYCLE` is the durable research identifier, such as `D7` or `V72P2D7`;
- `STAGE` identifies the bounded gate, such as `A`, `PRE_EXECUTE`, or
  `PRE_RESULT`;
- `ACTION` names the smallest useful work unit, such as
  `DECODER_CERTIFICATION`, `EASY_REGIME_FREEZE`, or `LAYER_INTERFACE_REWORK`;
- `REV` starts at `R1`; use `R2` for a full replacement and `A1`, `A2`, ... for
  a narrow addendum to an otherwise frozen package;
- the packet and prompt must have the identical stem;
- historical packet names remain valid; do not rename them only for style.

Examples:

```text
D7_A_DECODER_CERTIFICATION_R1_TASK_PACKET.md
D7_A_DECODER_CERTIFICATION_R1_PROMPT.md
D7_B_EASY_REGIME_FREEZE_R1_TASK_PACKET.md
D7_B_EASY_REGIME_FREEZE_R1_PROMPT.md
D7_B_EASY_REGIME_FREEZE_A1_TASK_PACKET.md
D7_B_EASY_REGIME_FREEZE_A1_PROMPT.md
```

OpenSpec remains the durable behavior contract under
`openspec/changes/<change-name>/`. Scientific reviews, execution packets,
operator returns, result summaries, and acceptance records remain under
`docs/research_cycles/<cycle-id>/`. Files in `.workbuddy/tasks/` are the
operational handoff surface and must point to those durable sources rather than
silently replacing them.

### 6.4 Required contents of a pair

The task packet is complete and authoritative for the delegated work. It must
state, as applicable:

- repository, branch, baseline and current lifecycle gate;
- declared track (`EXPLORE` or `DECIDE`, with `EXPLORE_HEAVY` allowed only as
  an EXPLORE cost annotation);
- objective, decision question and supported/unsupported claims;
- frozen inputs, parameters, seeds, thresholds, budget and stop rules;
- exact allowed and forbidden files, roots, commands and data roles;
- ordered work plan and stable acceptance IDs;
- required tests, reviews, artifacts, commits and no-push status;
- authorization boundary, hard STOP behavior, and fixed return schema;
- superseded packet/addendum relationship.

The companion prompt stays short. It must:

- point to the packet by absolute path;
- tell the operator to read it completely before acting;
- identify the intended autonomy level and the two return conditions
  (`COMPLETE` or one concrete `BLOCKED` decision);
- repeat only the highest-risk prohibitions and authorization boundary;
- require delta-only reporting;
- never carry scientific requirements that are absent from the packet.

When requirements change, revise the packet first and issue a paired `R2` or
`A<n>` prompt. A prompt-only correction may clarify invocation mechanics but
must not alter scientific scope, thresholds, data, commands, or acceptance.

## 7. Git milestone contract

Use coherent commits at scientific state transitions, not one commit per tiny
edit. Suggested subjects:

```text
docs(v37): freeze empirical-P graph experiment
feat(v37): implement finite-aware graph candidates
test(v37): cover DE and graph feasibility gates
data(v37): record paired development results
review(v37): close bounded experiment and next decision
```

Before every push:

```powershell
git status --short
git diff --check
git diff --cached --stat
git log -1 --oneline
```

The commit/PR should state:

- cycle ID and lifecycle status;
- the relevant commit ID when useful for later provenance;
- changed code/spec/test files;
- tests and development commands actually run;
- included data or result-summary path;
- omitted artifacts and why;
- allowed and forbidden scientific claims;
- whether formal execution is authorized.

Never force-push by default. If GitHub `main` contains an incompatible Polar or
other repository line, push this checkout to a clearly named formal-IR branch
instead of merging unrelated histories.

## 8. Data publication contract

Prefer committing compact text artifacts (`CSV`, `JSON`, `YAML`, `MD`) when
they are reasonably small and contain no private raw data. Raw `.ttbin`, large
matrices/arrays, binary caches, temporary trees, and replaceable bulky outputs
remain outside Git.

When data cannot be committed, `RESULT_SUMMARY.md` must include:

- input dataset identity and role (train/development/validation);
- sample/block counts and exclusions;
- seeds and frozen parameters;
- command and code/plan SHA;
- output schema and authoritative local/external location;
- primary per-source and aggregate metrics;
- failures, partial records, and status counts;
- omitted files with size/type and omission reason;
- the narrow claims supported and explicitly unsupported;
- reproduction or retrieval instructions.

Do not replace a useful data summary with integrity machinery. Git already
versions committed evidence; add hashes only when a concrete transfer or
scientific-identity failure requires them.

## 9. Minimal acceptance checklist

A research milestone is ready for review when all answers are yes:

- Are the reviewed files and current scoped diff explicit?
- Is the declared track correct for the work, and are the matching gates applied?
- Are requirements and thresholds frozen before implementation?
- Can each headline number be traced to a committed artifact or calculation?
- Are development and validation data roles distinguished?
- Are negative, partial, invalid, and skipped stages retained?
- Are oracle assumptions and non-end-to-end boundaries explicit?
- Does the report avoid promoting residual improvement to exact recovery?
- Is formal execution still blocked unless the user explicitly authorized it?

## 10. Pre-EXECUTE / Pre-RESULT review gates

No `DECIDE` formal/claim-bearing decoder execution and no `DECIDE`
development-result publication without a recorded review. "Publish first,
review later" is forbidden.

### 10.1 Pre-EXECUTE review — before claim-bearing or costly execution

Applies to real-data, formal, expensive, irreversible, or claim-bearing runs.
Verify and record:

1. intended repository and branch are active;
2. scoped code, tests, configuration, and packet have no unreviewed staged or
   unstaged changes;
3. frozen inputs, data roles, seeds, thresholds, command, budget, and stop rules
   match the accepted plan;
4. the target output directory does not already exist;
5. focused `py_compile` and plan-critical tests pass;
6. the user explicitly authorized this bounded run.

Commit IDs are optional provenance. Do not require remote equality, exact
implementation-SHA equality, stale-SHA grep, hashes, or a commit that records
its own ID. Documentation-only commits after code acceptance do not invalidate
the code. Exact revision locking is allowed only when the packet names a
concrete multi-writer, destructive, release, or evidence-integrity risk.

Active packets written before 2026-09-06 inherit this rule: conflicting
SHA/remote-equality clauses are non-binding unless they state such a concrete
exception. Their scientific scope, command, inputs, budgets, stop rules,
authorization, and no-overwrite requirements remain binding.

FAIL means the run stops until the scoped issue is corrected and reviewed.

### 10.2 Pre-RESULT review — before every `DECIDE` development-result output

Applies before any `OPERATOR_RETURN.md` / `RESULT_SUMMARY.md` / `run_01`
solidification or commit. An **independent thread or reviewer** re-checks the
actual artifacts against the frozen plan:

- plan thresholds and gate semantics
- leakage-formula decomposition and disclosure accounting
- `undetected` isolation (never merged into success/FER)
- per-source breakdown and other plan-specified semantics

Any issue → immediate rework; do not publish then patch review. FAIL blocks
solidification — never submit `run_01` with a known review failure.

Root cause prompting this gate: V55 repeatedly bound `ACCEPTED_PLAN_SHA` to the
V54 template constant `efd34ef` without replacement.

The corrective lesson is to inspect the actual scientific contract and scoped
files, not to add another layer of SHA ceremony.

### 10.3 Review frequency

Do not require an independent reviewer after every documentation commit or
tiny unchanged-scope correction. Use a focused self-check for low-risk edits
and batch them into the next milestone review. For `DECIDE`, independent review remains
mandatory at plan acceptance, before applicable claim-bearing/costly execution,
and before claim-bearing result solidification. For `EXPLORE`, one independent
batch-end review replaces per-arm review; per-arm review is not required when
the single append-only log is unambiguous.

