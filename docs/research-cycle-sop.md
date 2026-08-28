# GitHub-centered ChatGPT/OpenCode research-cycle SOP

This is the default collaboration protocol for this research repository. It is
deliberately small: GitHub preserves state, ChatGPT plans and reviews, OpenCode
implements, and the user/main reviewer owns acceptance and execution authority.

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
accepted_plan_sha: null
implementation_sha: null
development_execution_authorized: false
formal_execution_authorized: false
scientific_promotion: false
```

Do not record a commit's own SHA inside that same commit. Put the target SHA in
the handoff prompt; record it in the next verdict/return commit.

## 5. ChatGPT review sequence

1. Push the plan or implementation candidate to GitHub with a normal push.
2. Copy the prompt from `docs/prompts/chatgpt-research-review.md`.
3. Fill repository, branch, target SHA, cycle ID, review kind, and entrypoint.
4. Require ChatGPT to report whether it could verify the target SHA.
5. Copy the returned fixed-schema review into `REVIEW_VERDICT.md`.
6. Commit corrections or acceptance as a separate milestone.

If ChatGPT cannot verify the requested commit, its comments remain advisory and
the verdict cannot be `ACCEPT`. Provide the PR diff and key compact artifacts
directly in chat if necessary.

## 6. OpenCode execution sequence

1. Start from the accepted plan SHA.
2. Copy the prompt from `docs/prompts/opencode-research-execution.md`.
3. OpenCode first confirms `git rev-parse HEAD` and reads the named packet.
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

The commit/PR must state:

- cycle ID and lifecycle status;
- parent/accepted-plan SHA when applicable;
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

- Is the target SHA explicit?
- Are requirements and thresholds frozen before implementation?
- Can each headline number be traced to a committed artifact or calculation?
- Are development and validation data roles distinguished?
- Are negative, partial, invalid, and skipped stages retained?
- Are oracle assumptions and non-end-to-end boundaries explicit?
- Does the report avoid promoting residual improvement to exact recovery?
- Is formal execution still blocked unless the user explicitly authorized it?

## 10. Pre-EXECUTE / Pre-RESULT review gates (mandatory — V55 `efd34ef` fix)

No formal decoder execution and no development-result publication without a
recorded review. "Publish first, review later" is forbidden.

### 10.1 Pre-EXECUTE review — before every formal decoder execution

Applies to every production `run_01` / `EXECUTE_AUTH` execution. On the exact
implementation SHA, verify and record in cycle docs:

1. `HEAD == origin/<branch> == implementation SHA` (no drift)
2. `ACCEPTED_PLAN_SHA` equals the accepted plan SHA — re-derive from `git log`
   / `cycle_state.yaml`; `rg <stale-SHA>` (e.g. reused template constant
   `efd34ef`) returns 0 hits
3. Target `run_01` does not already exist under the output root (no overwrite)
4. Budget, gate thresholds, and `cycle_state` authorizations match the frozen plan
5. `py_compile` + plan-specified critical tests PASS

FAIL → execution blocked, enter `revise-required`/rework, fix on a new SHA, re-review.

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

