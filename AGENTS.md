# AGENTS.md — Repository-Level Agent Rules

These rules apply to all agents operating in this repository.

---

## 0. Repository Scope (READ FIRST — boundary rule)

- **This checkout (`HD-QKD_Polar_Comparison`) is the FORMAL IR / LDPC
  RESEARCH MAINLINE** (`main` branch): formal Cascade/LDPC methods,
  binary-LDPC v3+ long-frame work, and the nonbinary-LDPC ladder live and
  evolve here.
- **The sibling checkout `../HD-QKD_Polar_Release` is the BINARY POLAR
  MAINLINE** (branch `polar-mainline`): mature binary Polar usage, frozen
  baseline, security tooling. Do not advance Polar-mainline workstreams
  there from this repository, and do not merge `polar-mainline` into this
  `main`.
- Both checkouts historically shared one remote and one `main`, which
  caused a crosstalk incident (research content swept into the shared
  mainline, 2026-08-12..22). Keep research commits on this `main`; never
  sweep them into the sibling's branch again.

---

## 1. Project Identity

- **Project name**: `HD-QKD_Polar_Comparison`
- **Purpose**: Evaluate and compare information reconciliation (IR) methods for high-dimensional QKD data. The original Polar pipeline is a frozen baseline; the `comparison_bench/` layer adds a non-invasive comparison framework.
- **Main objective**: Discover, implement, and experimentally validate
  scientifically reasonable **high-performance information-reconciliation
  algorithms** for the actual HD-QKD data. The benchmark layer and frozen Polar
  baseline support this objective; they are not the objective themselves.

### 1.1 Strict First Principle: High-Performance Error Correction

- High-performance correction algorithms are the project's strict first
  principle. Prioritize algorithm hypotheses, implementations, and informative
  performance experiments over package maturity, generalized infrastructure,
  defensive hardening, exhaustive audit machinery, and verifier sophistication.
- Evaluate progress using the applicable combination of correction success/FER,
  leakage and reconciliation efficiency, throughput/runtime, memory/resource
  cost, and accepted-frame net secret-key yield.
- Engineering, audit, or verifier work may block algorithm work only when the
  unresolved issue can concretely cause a wrong numerical/scientific conclusion,
  irreproducible result, unauthorized expensive execution, or destructive
  overwrite of existing data. Otherwise record it as non-blocking or deferred.
- Use the shortest scientifically valid path: formulate the method, implement
  the smallest testable algorithm, measure it, and then decide the next method.
  Do not let research turns become packaging or adversarial-verifier projects.

---

## 2. Source of Truth

- **Chat history is not durable project memory.** It may be compacted or pruned at any time.
- **OpenSpec** is the source of truth for feature behavior and approved changes. All substantial feature work must go through the OpenSpec workflow.
- **AGENTS.md** (this file) is the source of truth for repository-level agent rules and responsibilities.
- **AGENT_PROJECT_MEMORY.md** is the durable project memory. It records observed structures, workflows, data policies, and constraints. Agents must consult it before making changes.
- **docs/decision-log.md** records durable decisions and rejected alternatives.
- **docs/troubleshooting.md** records reusable failure modes and their fixes.

---

## 3. Mandatory Processes

- Every substantial task **must** end with memory triage (via the memory agent).
- If implementation reveals requirement ambiguity, **stop** and return to planner or OpenSpec instead of guessing.
- If a change modifies behavior, architecture, prompt rules, tool semantics, or workflow rules, **create or update an OpenSpec change first**.
- Before modifying any file, read it first. Never write to a file without reading its current contents.
- **Pre-EXECUTE review is mandatory before claim-bearing, real-data, expensive, irreversible, or formal decoder execution.** Verify the intended branch; scoped code/config/test/packet cleanliness; frozen inputs, thresholds, command, budget and stop rules; explicit user authorization; target-output absence; and focused tests. Git commit IDs are provenance, not execution locks: do not require `HEAD == origin == implementation SHA`, stale-SHA grep, hashes, or recursive self-binding by default. Documentation-only commits after code acceptance do not invalidate the code. Record the scoped checklist before execution.
- **Pre-RESULT review is mandatory before every development-result output is published or committed** (`OPERATOR_RETURN.md` / `RESULT_SUMMARY.md` / `run_01` solidification). An independent thread or reviewer must re-check the frozen plan thresholds, leakage-formula decomposition, `undetected` isolation (never merged into success/FER), per-source breakdown, disclosure accounting, and other plan-specified semantics against the actual artifacts. Issues trigger immediate rework; do not publish first and patch review later.
- **If either applicable review FAILs, execution/solidification is blocked.** Enter `revise-required` / rework, fix the scoped root cause, and re-review. Never submit `run_01` with a known review failure. Root cause: V55 reused a V54 template constant instead of checking the actual plan content.

---

## 4. Agent Constraints

| Agent | Constraint |
|-------|-----------|
| **Coder** (coder-fast, coder-doc) | Must not redefine requirements. Implement exactly what the tasks specify. |
| **Reviewer** (reviewer-go) | Must not edit files by default. Output findings, not patches. |
| **Planner** | Must not write production code. Produce proposals, designs, and task breakdowns. |
| **Memory** | Must not write temporary or speculative content into long-term memory. |
| **Orchestrator** | Must not perform large-scale code edits directly. Delegate to specialized agents. |

---

## 5. Project-Specific Rules

### 5.1 Baseline Protection
- The original Polar pipeline (`src/`, `experiments/`, `tools/`) is a **frozen baseline**. Do not modify its logic.
- The `comparison_bench/` layer is an **outer wrapper** only. It reads existing Polar outputs and adds separate comparison capabilities.
- Original Polar outputs imported by the `polar_existing` bridge must not be overwritten.

### 5.2 Output Policy
- **Do not overwrite** anything under `results/` or `comparison_bench/outputs_comparison/` unless explicitly asked.
- New comparison outputs should stay under `comparison_bench/outputs_comparison/` with additive naming.
- Test fixtures and temp pytest artifacts under `comparison_bench/outputs_comparison/` are not production outputs.

### 5.3 Schema Stability
- CSV column names, JSON/YAML keys, CLI argument names, config keys, and output file naming conventions documented in `AGENT_PROJECT_MEMORY.md` §6 must not silently change.
- Function signatures of core types (`FrameBatch`, `IRRunConfig`, `IRRunResult`) and key functions (`load_pairs_table`, `normalize_pair_columns`, `build_frame_batch`, `run_polar_existing`) must not silently change.

### 5.4 Path Discipline
- Prefer WSL/POSIX paths for future harness and agent docs.
- Legacy Windows paths (e.g., `D:\Data\Raw Data\QKD_Loss\...`) are **provenance only** — do not bake them into new defaults.
- The `wsl-env.sh` script sets `PROJECT_DATA_ROOT`, `PROJECT_RESULTS_ROOT`, etc. for WSL environments.

### 5.5 Scientific Semantics
- `beta_eff_empirical` must remain derived from leakage and error inputs, never hand-filled.
- `qldpc_reference` results must not be described as full industrial qLDPC results unless method status explicitly justifies it.
- Leakage numbers are method-specific; only compare when decomposition semantics remain consistent.
- Do not silently convert status values (`reference`, `stub`, `unavailable`, `decode_failed`, `no_verified_success`) into `ok`.

### 5.6 Commands That Must Not Be Run By Default
- Any `longrun_*`, `minrerun_*`, or `routeA_*` script under `tools/` unless explicitly requested.
- `experiments/run_e2e_pipeline.py` on raw data.
- Full real-data benchmark or v3 master sweep in a fresh environment without confirming output policy first.
- Safe smoke commands are listed in `AGENT_PROJECT_MEMORY.md` §4.

### 5.7 Research Code Engineering Policy

- This repository contains local research and data-analysis code, not a production service.
- Use the simplest implementation that is scientifically correct, readable, and reproducible.
- Do not add the following unless the task explicitly requires them:
  - SHA-256, MD5, checksums, signatures, or integrity manifests
  - atomic file replacement or transactional writes
  - backup and rollback systems
  - file locking or concurrency protection
  - elaborate schema validation
  - retry frameworks
  - security hardening for untrusted input
  - compatibility layers for hypothetical environments
  - custom caching or artifact versioning
  - excessive exception handling that hides errors
- Assume:
  - inputs are trusted local research files;
  - the user controls the execution environment;
  - scripts are run manually on a single machine;
  - failed computations can normally be rerun;
  - Git is used for source-code version control.
- Prioritize:
  1. high-performance correction-method progress and informative measurement;
  2. scientific and numerical correctness;
  3. explicit units, assumptions, and parameter definitions;
  4. readable calculations;
  5. reproducible random seeds where relevant;
  6. validation against known limits or small test cases;
  7. clear error messages for realistic input mistakes;
  8. minimal dependencies and minimal abstraction.
- Before adding any defensive mechanism, identify the concrete failure mode it prevents. If no realistic failure mode exists in this repository, omit it.
- Do not generalize a one-off research script into a production framework unless explicitly requested.

---

## 6. OpenSpec Workflow

This project uses OpenSpec for feature and change management.

### Directory Structure
```
openspec/
  project.md            ← project-level context for all changes
  specs/                ← current (merged) specifications
  changes/              ← active change proposals (each in its own directory)
    <change-name>/
      proposal.md       ← what, why, scope, affected specs
      design.md         ← architecture / data-model decisions
      tasks.md          ← ordered implementation tasks
      specs/            ← delta specs for this change
```

### Slash Commands
- `/opsx-propose <name>` — Create a complete proposal/specs/design/tasks
- `/opsx-explore <topic>` — Enter explore mode (requirements clarification)
- `/opsx-apply <name>` — Start/continue implementing a change from its tasks
- `/opsx-archive <name>` — Archive a completed change (merge delta specs into main)

### Custom Commands
- `/implement-change <name>` — Full pipeline: planner → coder-fast → reviewer-go → memory triage
- `/review-change <name>` — Lightweight review by reviewer-go
- `/sync-memory <name-or-topic>` — Memory triage by memory agent
- `/finish-change <name>` — Finalize change, decide if archivable

---

## 7. Key Workflows

### Original Polar End-to-End Pipeline
- **Entrypoint**: `experiments/run_e2e_pipeline.py`
- **Do not run** on raw data casually. This is the core heavy baseline workflow.

### Real/Synthetic Comparison Benchmark
- **Entrypoints**:
  - `python -m comparison_bench.src.comparison_bench.cli.build_dataset`
  - `python -m comparison_bench.src.comparison_bench.cli.run_benchmark`
  - `python -m comparison_bench.src.comparison_bench.cli.compare_methods`
- **Safe smoke**: `python -m comparison_bench.src.comparison_bench.cli.smoke_test --config comparison_bench/configs/benchmark_synth.yaml`
- **Outputs**: `comparison_bench/outputs_comparison/ir_benchmark_results.csv`, `ir_frame_results.parquet`, `run_manifest.json`

### V3 Parameter Sweeps
- **Entrypoints**: `run_cascade_param_sweep.py`, `run_layered_ldpc_param_sweep.py`, `run_qldpc_param_sweep.py`, `run_ir_v3_master.py`
- **All under**: `python -m comparison_bench.src.comparison_bench.cli.<entrypoint> --config <config>`

### Replay / Security / Audit Aggregation
- **Entrypoints**: `tools/longrun_*.py`, `tools/minrerun_*.py`
- **Do not run** unless explicitly requested.

---

## 8. Execution Environment

- **OS**: Windows host; WSL support via `wsl-env.sh`
- **Python dependencies**: `numpy`, `pandas`, `numba`, `tqdm` (root `requirements.txt`)
- **Optional comparison deps**: `pyyaml`, `pyarrow`, `pytest` (`comparison_bench/requirements-comparison.txt`)
- **Known constraints**:
  - PowerShell profile may emit execution-policy warnings (non-fatal)
  - `.git/index.lock` permission issues may block git operations
  - Pytest cache/temp directories trigger permission-denied warnings (benign)
  - Some outputs may fall back from Parquet to pickle if Parquet support is missing

---

## 9. Repository Structure (Key Areas)

```
HD-QKD_Polar_Comparison/
  AGENTS.md                          ← this file
  AGENT_PROJECT_MEMORY.md            ← durable project memory
  README.md                          ← project overview
  requirements.txt                   ← root Python dependencies
  .gitignore
  docs/                              ← workflow/results documentation
  openspec/                          ← OpenSpec change management
  src/                               ← original Polar source (frozen)
  experiments/                       ← original Polar experiment scripts (frozen)
  tools/                             ← replay/security/audit scripts (frozen)
  results/                           ← original Polar outputs (read-only)
  analysis/                          ← analysis artifacts
  comparison_bench/                  ← non-invasive comparison layer
    configs/                         ← benchmark config YAMLs
    docs/                            ← comparison architecture/docs
    src/comparison_bench/
      cli/                           ← benchmark CLIs
      io/                            ← data loading / output
      methods/                       ← IR method implementations
      pipeline/                      ← benchmark pipeline
      sweep/                         ← parameter sweep infrastructure
    outputs_comparison/              ← comparison results (append-only)
    tests/                           ← comparison test suite
  workspace/                         ← scratch / temp workspace
```

---

## 10. Agent Handoff Protocol

When handing off work between agents, reference:
1. The current change name (if under OpenSpec)
2. Which task in `tasks.md` is in-progress or next
3. What outputs/manifests already exist
4. Any blockers or unknowns discovered
5. This `AGENTS.md` for project rules

### 10.1 Project-Wide Delegation And Acceptance Workflow

This workflow is the default for all substantial delegated implementation:

1. **Freeze one complete task packet before delegation.** The main thread
   specifies allowed and forbidden files, exact functionality, the complete
   test/evidence matrix, commands, artifacts, stop rules, and return
   conditions. Give acceptance items stable IDs; subagents report those IDs
   instead of restating the specification. Do not add foreseeable acceptance
   requirements one at a time during implementation.
2. **Keep ownership separated.** The main thread owns planning, requirements,
   thresholds, OpenSpec, acceptance, and scientific conclusions. A designated
   implementation subagent is an operator only and must not change those
   decisions or mark its own work accepted.
3. **Use only two operator return conditions.** The operator returns after all
   frozen items are complete, or on a concrete blocker with the failing
   command, exact error/traceback, attempted remedies, and the single decision
   needed from the main thread. “Still incomplete” is not a completion report.
4. **Review in proportion to scientific risk.** Use freeze, candidate, and
   independent-acceptance reviews for irreversible or claim-bearing scientific
   execution. For low-risk algorithm iteration, use focused numerical review;
   do not let review ceremony displace algorithm work. Do not require an
   independent reviewer after every docs-only commit or tiny unchanged-scope
   correction; batch them into the next milestone review.
5. **Reuse before rebuilding.** A successor starts from the nearest accepted
   predecessor contract and an explicit delta list. Preserve unchanged
   artifact, transcript, provenance, invalid-run, replay, and no-overwrite
   semantics instead of creating a thinner replacement.
6. **Run tests in four tiers.** T0 is compile/import/structural/tiny-math
   checks; T1 is focused unit and tamper tests; T2 is complete fake/test-only
   qualification plus strict replay; T3 is cross-version or broad regression.
   Run T2/T3 only at milestones. Main acceptance also checks frozen
   directories/source hashes and absence of unauthorized production output.
7. **Use tamper evidence only when scientifically necessary.** When a verifier
   is explicitly in scope and a concrete evidence-integrity failure could alter
   a scientific conclusion, cover the necessary drift layers. Do not expand an
   algorithm task into adversarial tamper engineering by default.
8. **Never invoke production work implicitly from tests.** Test-only
   execute/verify calls must explicitly pass a fake runner. A default
   production decoder, raw-data pipeline, long run, or evidence-output path
   must not be entered accidentally.
9. **Use a known writable test root on Windows.** Use a fresh additive
   `workspace/<task>/<uuid>` root and `pytest -p no:cacheprovider` when ACL
   failures are known. Do not spend task time deleting inaccessible legacy
   temp/cache directories. Test paths remain separate from production roots.
10. **Own long-running processes.** Record command/cell IDs. Terminate only a
    process launched and positively identified by the current task.
11. **Review dirty worktrees by scope.** Preserve unrelated changes. Check the
    explicit task-file manifest, hashes for untracked files, frozen-directory
    diffs, and official output-root existence; unscoped `git diff` is not
    sufficient.
12. **Report deltas only.** Handoffs and subagent messages state changed files,
   commands/results, concrete blockers, and remaining frozen items; do not
   repeat the full project history.

These efficiency rules never merge or weaken scientific lifecycle gates.
Qualification still requires separate prepare, main-thread review, execute,
and read-only verify stages, with immutable failure retention and all
pre-registered no-rerun/no-tuning rules intact.

### 10.2 GitHub-Centered ChatGPT/OpenCode Exchange

- Use `docs/research-cycle-sop.md` for every new research cycle. GitHub is the
  durable exchange surface; chat history is not project state.
- ChatGPT performs planning and read-only scientific review. OpenCode performs
  frozen implementation, focused tests, and only explicitly authorized
  development runs. Neither may grant its own acceptance, formal-execution
  authorization, qualification, or promotion.
- Every handoff names the repository, branch/PR, cycle ID, entrypoint document,
  scoped files, lifecycle state, and allowed action. If the reviewer cannot
  inspect the actual scoped files/evidence, its result is advisory. A commit ID
  may be included for provenance but is not an authorization token.
- Every research milestone commit/PR includes the applicable OpenSpec, code,
  tests, and compact machine-readable data. If raw/large/binary/private data
  cannot be committed, include a result summary with provenance, seeds,
  commands, primary metrics, omitted artifacts/reasons, and reproduction or
  retrieval instructions.
- Use the copy-paste prompts under `docs/prompts/` and preserve agent returns in
  the cycle documents. Report deltas; do not paste growing chat histories.
- Publish with ordinary non-force pushes. If a remote branch carries an
  incompatible Polar or sibling-checkout line, push a clearly named formal-IR
  branch instead of merging crosstalk or force-updating that branch.

### 10.3 Pre-EXECUTE / Pre-RESULT Review Gates (Mandatory)

- **Pre-EXECUTE** (claim-bearing/costly/formal execution): verify intended branch, scoped code/config/test/packet cleanliness, frozen scientific contract, explicit user authorization, target-output absence, and focused tests. Do not require remote/SHA equality or stale-SHA searches unless a named concrete multi-writer, destructive, release, or evidence-integrity risk justifies that exception. Checklist recorded in cycle docs; FAIL blocks execution.
- **Pre-RESULT** (development-result publication): independent thread/reviewer re-checks plan thresholds, leakage-formula decomposition, `undetected` isolation, per-source breakdown, disclosure accounting and plan-specified semantics against actual artifacts before any `OPERATOR_RETURN.md` / `RESULT_SUMMARY.md` / `run_01` commit. Issues → immediate rework; never publish-then-patch. FAIL blocks solidification.
- Apply each gate where its scope above requires it. Existing packets inherit
  this rule: SHA/remote-equality clauses are non-binding unless a concrete
  exception risk is stated. Scientific scope, authorization, tests, stop rules,
  and no-overwrite checks remain binding.

---

*This file is authoritative. If behavior diverges from what is written here, update this file via an OpenSpec change.*
