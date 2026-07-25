# AGENTS.md — Repository-Level Agent Rules

These rules apply to all agents operating in this repository.

---

## 1. Project Identity

- **Project name**: `HD-QKD_Polar_Comparison`
- **Purpose**: Evaluate and compare information reconciliation (IR) methods for high-dimensional QKD data. The original Polar pipeline is a frozen baseline; the `comparison_bench/` layer adds a non-invasive comparison framework.
- **Main objective**: Build a reproducible benchmark layer that reads/imports existing Polar results, runs executable comparison baselines (cascade, binary LDPC, q-ary LDPC reference) on synthetic and real paired-symbol frame data, and generates comparable CSV/Parquet/summary outputs without changing the original Polar workflow semantics.

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

---

*This file is authoritative. If behavior diverges from what is written here, update this file via an OpenSpec change.*
