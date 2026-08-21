# AGENTS.md — Repository-Level Agent Rules

These rules apply to all agents operating in this repository.

---

## 0. Repository Scope (READ FIRST — boundary rule)

- **This checkout (`HD-QKD_Polar_Release`) is the BINARY POLAR MAINLINE.**
  Its mission is the mature binary Polar code line: the frozen baseline
  (`src/`, `experiments/`, `tools/`, `results/`), the security/replay
  tooling around it, and the non-invasive `comparison_bench/` bridge that
  READS Polar outputs.
- **The formal IR / binary-LDPC-v4+ / nonbinary-LDPC research line lives in
  the sibling working repository `../HD-QKD_Polar_Comparison`.** Do NOT
  open, advance, execute, or archive research-line OpenSpec changes here
  (`formal-nonbinary-ldpc-*`, `binary-ldpc-v4*`/`v5*`,
  `improve-formal-*`, `implement-formal-nonbinary-ldpc`,
  `speed-up-nbldpc-*`, ...). Historical copies of those documents in this
  checkout are crosstalk residue kept only for provenance.
- Both checkouts historically shared one remote and one `main`. This
  checkout maintains its own long-lived branch **`polar-mainline`**;
  never merge the research `main` into it.
- If a task seems to belong to the other repository, stop and say so
  instead of working around the boundary.

---

## 1. Project Identity

- **Project name**: `HD-QKD_Polar_Release` (binary Polar mainline)
- **Purpose**: Maintain and use the mature binary Polar code implementation for high-dimensional QKD: frozen end-to-end pipeline, security/finite-key analysis tooling, and reproducible result artifacts. The `comparison_bench/` layer stays as a read-oriented bridge that imports existing Polar results; its day-to-day research evolution is owned by the sibling repository.
- **Main objective**: Keep the original Polar workflow semantics stable and its results auditable; evolve only Polar-line workstreams (e.g., the bit-plane Route A-complete formalization defined in `总体判断.txt`).

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
  1. scientific and numerical correctness;
  2. explicit units, assumptions, and parameter definitions;
  3. readable calculations;
  4. reproducible random seeds where relevant;
  5. validation against known limits or small test cases;
  6. clear error messages for realistic input mistakes;
  7. minimal dependencies and minimal abstraction.
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
4. **Review three times by default.** Main-thread review occurs at
   specification freeze, complete candidate delivery, and independent
   acceptance. Avoid repeated full-file review after each small increment.
5. **Reuse before rebuilding.** A successor starts from the nearest accepted
   predecessor contract and an explicit delta list. Preserve unchanged
   artifact, transcript, provenance, invalid-run, replay, and no-overwrite
   semantics instead of creating a thinner replacement.
6. **Run tests in four tiers.** T0 is compile/import/structural/tiny-math
   checks; T1 is focused unit and tamper tests; T2 is complete fake/test-only
   qualification plus strict replay; T3 is cross-version or broad regression.
   Run T2/T3 only at milestones. Main acceptance also checks frozen
   directories/source hashes and absence of unauthorized production output.
7. **Freeze layered tamper evidence up front.** When verifiers are in scope,
   cover raw byte drift, semantic changes with local self-hashes recomputed,
   manifest/index links recomputed, and deep source/transcript/public-payload/
   leakage/accounting/gate reconstruction.
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

---

*This file is authoritative. If behavior diverges from what is written here, update this file via an OpenSpec change.*
