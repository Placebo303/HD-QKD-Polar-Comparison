# Project Progress Plan - 2026-06-15

## 0. Project Objective

The purpose of this project is to execute and evaluate real information reconciliation / error-correction methods for high-dimensional arrival-time QKD data, then decide which method should be selected for the final system or paper pipeline.

The first-principles target is not to fit a reconciliation-efficiency number. A candidate method must first perform a real IR process:

- consume real paired Alice/Bob arrival-time symbols;
- use only protocol-allowed public information;
- correct Bob toward Alice;
- pass independent verification;
- account for actual public leakage;
- preserve failures honestly.

Only after real IR success is demonstrated should methods be compared on:

- correction effectiveness: decode success, verify success, post-IR SER/BER;
- efficiency: leakage, `beta_eff_empirical`, accepted-frame fraction, rejected-frame fraction;
- runtime performance: runtime, throughput, scalability with frame size and dimension;
- implementation readiness: dependency stability, reproducibility, failure modes, and integration risk;
- scientific defensibility: whether the method status supports the strength of the claim being made.

The final output should still be a ranked recommendation, but the next phase is "real IR success first."

## 1. Current Progress Snapshot

The project is in a partially consolidated method-comparison benchmark state.

- The original Polar pipeline is present and must be treated as a frozen baseline.
- The additive `comparison_bench/` layer exists with CLIs, configs, method wrappers, tests, and existing comparison outputs.
- OpenSpec has been initialized, but no active change proposal exists yet under `openspec/changes/`.
- Durable project rules and coordination files now exist: `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`, `CURRENT_TASK.md`, `RUN_COMMANDS.md`, `REVIEW_CHECKLIST.md`, and `AGENT_HANDOFF.md`.
- Existing comparison outputs include synthetic/real benchmark outputs, v3 sweep outputs, diagnostics, manifests, and report tables under `comparison_bench/outputs_comparison/`.
- The existing outputs are enough to seed a real-IR-success audit, but not enough to make a final method choice while most non-Polar methods still lack stable real-data verification success.
- The repository is not clean in git: several baseline files are already modified and many coordination/comparison files are untracked. Treat those as existing work and do not revert them.

## 2. Completed / Available Capabilities

### 2.1 Frozen Polar Baseline

Status: available, protected.

- Original workflow entrypoints remain under `experiments/`.
- Original replay/security/audit tooling remains under `tools/`.
- Existing Polar results are read from `results/` or imported through the comparison bridge.
- The baseline should not be edited or rerun on raw data unless explicitly requested.

### 2.2 Comparison Benchmark Layer

Status: implemented enough for smoke, real-frame import, method comparison, and v3 sweeps.

Available entrypoints:

- `python -m comparison_bench.src.comparison_bench.cli.build_dataset`
- `python -m comparison_bench.src.comparison_bench.cli.run_benchmark --config comparison_bench/configs/benchmark_realdata.yaml`
- `python -m comparison_bench.src.comparison_bench.cli.compare_methods`
- `python -m comparison_bench.src.comparison_bench.cli.smoke_test --config comparison_bench/configs/benchmark_synth.yaml`

Available method families:

- `polar_existing`
- `cascade_lite`
- `layered_ldpc_lite`
- `qldpc_reference`

### 2.3 V3 Sweep / Report Layer

Status: outputs exist; interpretation, fairness, and decision readiness still need audit.

Existing output families:

- `cascade_param_sweep_results.csv`
- `layered_ldpc_param_sweep_results.csv`
- `qldpc_param_sweep_results.csv`
- `run_errors_ir_v3.csv`
- `ir_v3_run_manifest.json`
- `report_tables_v3/`

### 2.4 Documentation / Agent Workflow

Status: initialized, but needs ongoing synchronization with implementation reality.

Available documents:

- `AGENTS.md`: repository-level agent rules
- `AGENT_PROJECT_MEMORY.md`: durable memory and observed contracts
- `docs/real-ir-success-first-plan-20260615.md`: next-phase plan centered on verified real IR success before final method selection
- `docs/ir-method-comparison-state-20260615.md`: current decision-relevant method state, v2/v3 output summary, and fragile points
- `docs/decision-log.md`: durable decisions
- `docs/troubleshooting.md`: reusable failure modes
- `RUN_COMMANDS.md`: curated safe and heavy commands
- `REVIEW_CHECKLIST.md`: review checklist
- `AGENT_HANDOFF.md`: short handoff state
- `openspec/project.md`: OpenSpec project context

## 3. Main Gaps

### 3.1 OpenSpec Must Track Real IR Success First

The active next change should be `real-ir-success-first`, not immediate final method selection.

Immediate need:

- Use `openspec/changes/real-ir-success-first/` to define success criteria, representative real-frame validation, Cascade-lite real success baseline work, LDPC diagnostics, and qLDPC reference feasibility.

### 3.2 Real IR Success Criteria Must Come Before Efficiency Comparison

The project needs explicit real-success rules before comparing efficiency. Otherwise the benchmark can produce leakage or beta numbers without proving that reconciliation actually succeeded.

Immediate need:

- Define real IR success as verified reconciliation on real paired-symbol frames.
- Require independent verification for success.
- Require leakage accounting or explicit approximate/unavailable labeling.
- Keep unverified improvement separate from success.
- Defer final method choice until at least one non-Polar path has verified real-data success.

### 3.3 Output Canonicality Is Not Fully Established

Existing outputs are present, but the repository still needs a documented audit deciding which outputs are:

- canonical current benchmark evidence,
- exploratory v3 artifacts,
- temporary pytest artifacts,
- stale or superseded runs.

Immediate need:

- Add a manifest-level inventory of existing output files.
- Record which files are safe to cite in reports.
- Record which files require rerun, regeneration, or exclusion.

### 3.4 Method Status Needs Scientific Review Under Real-Success Semantics

The method names exist, but the evidence level differs by method.

Immediate need:

- Use `docs/ir-method-comparison-state-20260615.md` as the current method-state starting point.
- Keep `cascade_lite` labeled as an executable simplified Cascade baseline, not a full industrial Cascade implementation.
- Keep `layered_ldpc_lite` labeled as executable and diagnosable, but currently less stable than Cascade on observed real-data representative sweeps.
- Keep `qldpc_reference` labeled as reference-grade unless status and diagnostics justify stronger language.
- Preserve all non-`ok` statuses and do not rewrite them into apparent success.
- Treat `cascade_lite` as the first non-Polar real-success candidate, `layered_ldpc_lite` as a failure-diagnosis target, and `qldpc_reference` as a q-ary feasibility probe.

### 3.5 Real-Data Reproducibility Needs A Narrow Safe Path

Real frame batches and sidecar-derived outputs exist, but the safe rerun path needs a bounded, additive configuration.

Immediate need:

- Define a representative, non-overwriting real-data validation run.
- Prefer a new output subdirectory or timestamped filenames under `comparison_bench/outputs_comparison/`.
- Avoid raw-data front-half reruns unless explicitly requested.

### 3.6 WSL / Path Discipline Needs Follow-Through

`wsl-env.sh` exists, but future harness docs should avoid legacy Windows absolute paths as defaults.

Immediate need:

- Update future run docs to use project-relative paths and WSL environment variables.
- Treat old Windows paths only as provenance.

### 3.7 Tests Need Current Verification

Tests exist, but no current test result was produced during this progress audit.

Immediate need:

- Run the synthetic smoke command.
- Run the comparison test suite if dependencies are available.
- Record exact test command, timestamp, and result in a durable document.

## 4. Recommended Plan

### Phase 0 - Freeze The Current Coordination State

Goal: make sure agents work from the same facts before feature work resumes.

Tasks:

1. Keep `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`, and this plan aligned.
2. Add this plan to `CURRENT_TASK.md`.
3. Do not modify `src/`, `experiments/`, or `tools/` while planning.
4. Do not overwrite `results/` or existing `comparison_bench/outputs_comparison/` files.

Exit criteria:

- Current task points to this progress plan.
- Handoff notes mention that detailed planning lives here.

### Phase 1 - Use OpenSpec Change For Real IR Success First

Goal: define how the benchmark will establish verified real IR success before final method selection.

Suggested change name:

- `real-ir-success-first`

Proposed scope:

- define real IR success criteria,
- select bounded representative real-frame operating points,
- establish Cascade-lite as first non-Polar real-success candidate,
- diagnose Layered LDPC failures,
- probe qLDPC reference feasibility,
- inventory existing comparison outputs,
- define safe rerun policy,
- specify validation commands and audit outputs.

Required OpenSpec files:

- `openspec/changes/real-ir-success-first/proposal.md`
- `openspec/changes/real-ir-success-first/design.md`
- `openspec/changes/real-ir-success-first/tasks.md`
- `openspec/changes/real-ir-success-first/specs/real-ir-success/spec.md`

Exit criteria:

- Tasks are concrete enough for coder/reviewer agents.
- No implementation ambiguity remains.
- Real success criteria are explicit before additional benchmarking.

### Phase 2 - Define Real IR Success Classification

Goal: make success/failure classification explicit and auditable.

Classification columns:

- method: `polar_existing`, `cascade_lite`, `layered_ldpc_lite`, `qldpc_reference`, and any future candidate;
- method status: `ok`, `reference`, `stub`, `unavailable`, `decode_failed`, `no_verified_success`, or other preserved status;
- `verify_success`;
- `real_ir_success`;
- post-IR SER/BER;
- leakage per input bit;
- `beta_eff_empirical`;
- runtime and throughput;
- leakage/accounting status;
- diagnostic bucket.

Suggested diagnostic buckets:

- `real_ir_success`
- `decode_improved_but_unverified`
- `verified_failure`
- `decode_failed`
- `method_unavailable`
- `reference_only`
- `invalid_accounting`

### Phase 3 - Representative Real-Frame Set

Goal: choose a small real-data set for iteration before broad sweeps.

Tasks:

1. Inventory existing frame-batch artifacts without traversing pytest temp directories.
2. Prefer `real_sidecars_frame_batch.parquet` or known sidecar-derived batches.
3. Select low/medium/high raw SER regimes where possible.
4. Include at least one tractable point and more than one dimension if available.
5. Write any new subset only under an additive path such as `comparison_bench/outputs_comparison/real_ir_success_first/`.

Exit criteria:

- Representative frames are documented with dimensions, bin widths, frame counts, and raw SER/BER.
- The subset can be reconstructed from config/manifest.
- The subset is small enough for rapid coding-agent iteration.

### Phase 4 - Cascade Lite Real Success Baseline

Goal: establish the first non-Polar verified real-data IR path.

Tasks:

1. Run or adapt Cascade-lite on the representative real-frame set.
2. Preserve transcript/leakage decomposition.
3. Record frame-level verification success and failures.
4. Identify the smallest stable configuration family, if any.
5. Document simplified-Cascade limitations.

Exit criteria:

- At least one real-data frame group has verified non-Polar success, or blockers are explicit.
- Leakage accounting is present and labeled.
- Failed frames remain failed.

### Phase 5 - Layered LDPC Failure Diagnostics

Goal: explain LDPC failures instead of only sweeping parameters.

Tasks:

1. Analyze raw SER/BER, frame length, dimension, parity fraction, LLR mode, and bitplane rate mode.
2. Add/emit per-bitplane diagnostics where available.
3. Distinguish decoder failure from verification failure.
4. Decide whether LDPC remains a serious candidate, diagnostic baseline, or deferred direction.

Exit criteria:

- LDPC failure modes are bucketed and actionable.
- No failed LDPC result is marked `ok`.

### Phase 6 - qLDPC Reference Feasibility Probe

Goal: test whether the q-ary reference path can verify on easy real frames.

Tasks:

1. Start with low-noise / low raw SER representative frames.
2. Use the current internal GF(2^m) fallback unless dependency work is explicitly assigned.
3. Preserve reference-grade labeling.
4. Record syndrome weight, decoder status, verification result, and leakage.

Exit criteria:

- qLDPC either verifies on an easy real frame or produces a clear blocker.
- The result distinguishes q-ary feasibility from production qLDPC readiness.

### Phase 7 - Output Inventory And Canonicality Audit

Goal: establish exactly what evidence exists and what can be cited.

Tasks:

1. Inventory top-level files in `comparison_bench/outputs_comparison/`.
2. Read `run_manifest.json` and `ir_v3_run_manifest.json`.
3. Summarize row counts and method statuses for:
   - `ir_benchmark_results.csv`
   - `ir_method_summary.csv`
   - `cascade_param_sweep_results.csv`
   - `layered_ldpc_param_sweep_results.csv`
   - `qldpc_param_sweep_results.csv`
   - `run_errors_ir_v3.csv`
4. Identify pytest/temp directories and exclude them from report evidence.
5. Write an audit note under `docs/` without changing any output files.

Exit criteria:

- A human can tell which existing CSVs are current evidence.
- Stale, exploratory, and temp artifacts are clearly labeled.
- Existing outputs are mapped into real-success classification or explicitly excluded.

### Phase 8 - Safe Smoke And Test Verification

Goal: verify the code path without expensive or destructive reruns.

Commands to prefer:

```powershell
python -m comparison_bench.src.comparison_bench.cli.smoke_test --config comparison_bench/configs/benchmark_synth.yaml
```

Then, if dependencies are available:

```powershell
python -m pytest comparison_bench/tests
```

Constraints:

- Confirm output policy before running if the smoke command would overwrite existing standard output names.
- Prefer additive or temp output configuration when possible.
- Do not run raw-data front-half, full real-data benchmark, v3 master sweep, or `longrun_*`/`minrerun_*` scripts by default.

Exit criteria:

- Current smoke/test status is recorded with exact commands.
- Any failures are added to `docs/troubleshooting.md` only if reusable.

### Phase 9 - Final Method Selection After Real Success

Goal: select a method only after real-success evidence exists.

Tasks:

1. Start from `docs/ir-method-comparison-state-20260615.md` and `docs/real-ir-success-first-plan-20260615.md`.
2. Compare only methods with compatible real-success evidence.
3. Use verified success first, then leakage/beta/runtime as second-order criteria.
4. Keep Polar imported baseline distinct from executable comparison methods.
5. Update method notes only if claims are currently too strong or unclear.

Exit criteria:

- Each method has a documented evidence level.
- Report language does not overclaim qLDPC or simplified Cascade status.
- Each method is assigned a provisional recommendation tier.

## 5. Immediate Next Actions

1. Use `docs/real-ir-success-first-plan-20260615.md` as the next implementation plan.
2. Implement from OpenSpec change `real-ir-success-first`.
3. Define and test real-success classification before broad reruns.
4. Select representative real frames.
5. Establish Cascade-lite as the first non-Polar real-success candidate.
6. Diagnose Layered LDPC failures.
7. Probe qLDPC reference feasibility.
8. Record evidence in a new `docs/real-ir-success-audit-YYYYMMDD.md`.
9. Defer `docs/ir-method-selection-YYYYMMDD.md` until real-success evidence is sufficient.

## 6. Commands To Avoid Unless Explicitly Requested

- `experiments/run_e2e_pipeline.py` on raw data.
- Any `tools/longrun_*.py`.
- Any `tools/minrerun_*.py`.
- Any `tools/routeA_*.py`.
- Full real-data benchmark across all sidecars.
- Full v3 master sweep in a fresh environment.

## 7. Working Status Labels

Use these labels in future audit docs:

- `ready`: verified in current environment and safe to cite.
- `available_unverified`: file or capability exists, but was not rerun or audited in the current pass.
- `exploratory`: useful evidence, but not final report-grade.
- `blocked`: cannot proceed without data, dependency, or user decision.
- `do_not_rerun_by_default`: expensive, destructive, or baseline-sensitive.
