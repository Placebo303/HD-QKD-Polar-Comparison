# GitHub-centered ChatGPT/OpenCode research-cycle SOP

This is the default collaboration protocol for this research repository. It is
deliberately small: Git preserves provenance and recovery, ChatGPT plans and
reviews, OpenCode implements, and the user/main reviewer owns acceptance and
execution authority. Git commit identity is not an execution capability.

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
result is not qualification.

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

## 5. ChatGPT review sequence

1. Make the plan or implementation candidate available in the intended branch.
2. Copy the prompt from `docs/prompts/chatgpt-research-review.md`.
3. Fill repository, branch, cycle ID, review kind, and entrypoint.
4. Require ChatGPT to inspect the scoped files and current diff rather than
   accepting a self-reported PASS.
5. Copy the returned fixed-schema review into `REVIEW_VERDICT.md`.
6. Commit corrections or acceptance as a separate milestone.

If ChatGPT cannot inspect the scoped files or evidence, its comments remain
advisory. A commit ID alone never makes a review valid.

## 6. OpenCode execution sequence

1. Start from the accepted plan and intended branch.
2. Copy the prompt from `docs/prompts/opencode-research-execution.md`.
3. OpenCode confirms the intended branch, reads the named packet, and checks
   only the scoped code/config/test files for unreviewed changes.
4. It changes only allowed files and runs only authorized development work.
5. It returns either `COMPLETE` or a concrete `BLOCKED` report.
6. Copy the result into `OPERATOR_RETURN.md`, inspect the diff, and push an
   implementation candidate for independent review.

Use at most two OpenCode workers and serialize work that touches the same file,
test root, output root, or Git state. Prefer exact paths and restricted `rg`;
do not use broad recursive scans on this Windows workspace.

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
- Are requirements and thresholds frozen before implementation?
- Can each headline number be traced to a committed artifact or calculation?
- Are development and validation data roles distinguished?
- Are negative, partial, invalid, and skipped stages retained?
- Are oracle assumptions and non-end-to-end boundaries explicit?
- Does the report avoid promoting residual improvement to exact recovery?
- Is formal execution still blocked unless the user explicitly authorized it?

## 10. Pre-EXECUTE / Pre-RESULT review gates

No formal decoder execution and no development-result publication without a
recorded review. "Publish first, review later" is forbidden.

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

### 10.2 Pre-RESULT review — before every development-result output

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
and batch them into the next milestone review. Independent review remains
mandatory at plan acceptance, before applicable claim-bearing/costly execution,
and before claim-bearing result solidification.

