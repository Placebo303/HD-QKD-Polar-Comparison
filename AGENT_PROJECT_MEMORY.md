# AGENT_PROJECT_MEMORY.md

## 2026-07-26 Nonbinary N3 evidence boundary

`nbldpc_formal_v1` completed its only frozen q=1024 synthetic N3 execution at
`comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_nbldpc_synthetic`.
Selected policy SHA `23a1b46300f1c841eed3ffc6f672840c7be17608260de6b09944cac74228983d`
was margin 7/scale 1.0/max_iter 10 with 32 checks in both strata. Confirmation
was non-promoted: p=.20 18/32 verified success and p=.30 5/32, both below the
31/32 gate; N4, reruns, and tuning are forbidden. The official strict verifier
failed only because post-execution whole-worktree git-status provenance drifted.
Source/CLI/contract hashes, commit, Python and NumPy matched; `_test_only=True`
diagnostic replay is not an official verifier pass. Preserve all seven artifacts.

## 1. Project Identity
- Project name: `HD-QKD_Polar_Comparison` [repo-observed]
- Research purpose: evaluate and compare information reconciliation (IR) methods for high-dimensional QKD data, while preserving the copied Polar pipeline as a frozen baseline and adding a separate comparison layer. [repo-observed]
- Main scientific/engineering objective: build a reproducible, non-invasive benchmark layer that can (a) read/import existing Polar results, (b) run executable comparison baselines on synthetic and real paired-symbol frame data, and (c) generate comparable CSV/Parquet/summary outputs without changing the original Polar workflow semantics. [repo-observed]
- Current maturity: mixed. The original Polar repository appears to be a mature replay/security/reporting codebase; `comparison_bench/` is an additive benchmark layer with working CLIs, tests, real-data imported Polar baseline, real-data/synthetic executable baselines, and v3 parameter-sweep/report outputs. [repo-observed]

## 2. Repository Structure Observed
- Top-level directories observed: `analysis/`, `comparison_bench/`, `docs/`, `experiments/`, `results/`, `src/`, `tools/`, `workspace/` [repo-observed]
- Top-level files observed: `README.md`, `requirements.txt`, `bootstrap_clone_clean.py`, `wsl-env.sh`, `LICENSE`, `.gitignore` [repo-observed]
- Original pipeline entrypoints:
  - `experiments/run_e2e_pipeline.py` [repo-observed]
  - `experiments/run_real_polar_max_pie.py` [repo-observed]
  - `experiments/run_golden_sweep_driver.py` [repo-observed]
  - `experiments/run_golden_sweep_four_datasets.py` [repo-observed]
- Original source areas:
  - `src/qkd_io/ttbin_pipeline.py` [repo-observed]
  - `src/workflow/coarse_grain_joint.py` [repo-observed]
  - `src/workflow/export_joint_sequence_sidecar.py` [repo-observed]
  - `src/workflow/llr_from_joint.py` [repo-observed]
  - `src/reconciliation/real_polar_sc_rescue.py` [repo-observed]
  - `src/reconciliation/cpp_scl_wrapper.py` [repo-observed]
  - `src/reconciliation/verification.py` [repo-observed]
  - `src/reconciliation/cpp_polar/` containing `.dll`, `.exe`, and C++ files [repo-observed]
- Original tooling area includes many audit/security/reporting scripts, for example:
  - `tools/longrun_build_replay_index.py` [repo-observed]
  - `tools/longrun_run_actual_ir_replay.py` [repo-observed]
  - `tools/longrun_build_finite_key_audit_table.py` [repo-observed]
  - `tools/longrun_build_security_master_table.py` [repo-observed]
  - `tools/minrerun_run_frame_audit.py` [repo-observed]
  - `tools/minrerun_rebuild_security_master_20dB.py` [repo-observed]
  - `tools/routeA_run_formal_cross_loss.py` [repo-observed]
- Comparison layer structure:
  - `comparison_bench/README.md` [repo-observed]
  - `comparison_bench/requirements-comparison.txt` [repo-observed]
  - `comparison_bench/configs/benchmark_realdata.yaml` [repo-observed]
  - `comparison_bench/configs/benchmark_synth.yaml` [repo-observed]
  - `comparison_bench/configs/cascade_param_sweep.yaml` [repo-observed]
  - `comparison_bench/configs/layered_ldpc_param_sweep.yaml` [repo-observed]
  - `comparison_bench/configs/qldpc_param_sweep.yaml` [repo-observed]
  - `comparison_bench/configs/ir_methods_v3_master.yaml` [repo-observed]
  - `comparison_bench/docs/architecture.md` [repo-observed]
  - `comparison_bench/docs/data_contract.md` [repo-observed]
  - `comparison_bench/docs/method_notes.md` [repo-observed]
  - `comparison_bench/src/comparison_bench/cli/` with:
    - `build_dataset.py` [repo-observed]
    - `run_benchmark.py` [repo-observed]
    - `compare_methods.py` [repo-observed]
    - `smoke_test.py` [repo-observed]
    - `run_cascade_param_sweep.py` [repo-observed]
    - `run_layered_ldpc_param_sweep.py` [repo-observed]
    - `run_qldpc_param_sweep.py` [repo-observed]
    - `run_ir_v3_master.py` [repo-observed]
    - `make_report_tables.py` [repo-observed]
  - `comparison_bench/src/comparison_bench/io/` with:
    - `pairs_loader.py` [repo-observed]
    - `dataset_builder.py` [repo-observed]
    - `polar_existing_bridge.py` [repo-observed]
    - `table_store.py` [repo-observed]
  - `comparison_bench/src/comparison_bench/methods/` with:
    - `cascade_lite.py` [repo-observed]
    - `layered_ldpc_lite.py` [repo-observed]
    - `qldpc_reference.py` [repo-observed]
    - `qary_ldpc.py` [repo-observed]
    - `polar_existing.py` [repo-observed]
    - `base.py` [repo-observed]
  - `comparison_bench/src/comparison_bench/pipeline/` with:
    - `run_ir_benchmark.py` [repo-observed]
    - `merge_with_security.py` [repo-observed]
  - `comparison_bench/src/comparison_bench/sweep/` with:
    - `runtime.py` [repo-observed]
    - `common.py` [repo-observed]
    - `rows.py` [repo-observed]
  - `comparison_bench/tests/` with six current test files [repo-observed]
- Historical context from prior work:
  - real-data imported Polar baseline was matched against a real result root under a legacy Windows data path. [memory-derived]
  - representative sidecar frame batches were built from real paired-symbol sidecar exports. [memory-derived]

## 3. Execution Environment
- Expected OS: Windows host environment is directly observed; WSL support is also explicitly provisioned via `wsl-env.sh`. [repo-observed]
- Expected Python/MATLAB/Octave/other runtime:
  - Python with `numpy`, `pandas`, `numba`, `tqdm` from root `requirements.txt` [repo-observed]
  - optional comparison dependencies: `pyyaml`, `pyarrow`, `pytest` from `comparison_bench/requirements-comparison.txt` [repo-observed]
  - compiled Polar binaries exist under `src/reconciliation/cpp_polar/` (`.dll`, `.exe`) [repo-observed]
  - MATLAB/Octave usage is [uncertain]; no current comparison harness file directly invokes them, but prior planning discussed possible external hooks. [memory-derived]
- Known environment constraints:
  - PowerShell profile loading emits execution-policy warnings in this environment. [memory-derived]
  - git commit/stage operations may fail due to `.git/index.lock` permission issues. [memory-derived]
  - pytest cache/temp directories can trigger permission-denied warnings. [memory-derived]
  - some outputs may fall back from parquet to pickle if parquet support is missing. [repo-observed]
- WSL migration notes:
  - `wsl-env.sh` sets `PROJECT_DATA_ROOT`, `PROJECT_RESULTS_ROOT`, `TMPDIR`, and `PIP_CACHE_DIR` to POSIX-style defaults. [repo-observed]
  - For WSL work, prefer `/mnt/...` or project-relative POSIX paths, not Windows absolute paths. [repo-observed]
  - Historical Windows data/result paths should be treated as provenance only, not future execution defaults. [repo-observed]

## 4. Main Workflows

### Workflow: original Polar end-to-end pipeline
- entrypoint: `experiments/run_e2e_pipeline.py` [repo-observed]
- input: raw `.ttbin`-derived or paired-sequence materialization inputs [repo-observed]
- output: Polar evaluation artifacts under repository result directories [repo-observed]
- safe smoke command: [uncertain]
- heavy command, if known: [uncertain]
- do-not-run-by-default commands:
  - `experiments/run_e2e_pipeline.py` on raw data, because this is the core heavy baseline workflow and should not be rerun casually. [repo-observed]

### Workflow: original real Polar sweep / max PIE
- entrypoint: `experiments/run_real_polar_max_pie.py` [repo-observed]
- input: cached grid/source tables or materialized real-data intermediates [memory-derived]
- output: Polar result tables such as `polar_diag_summary.csv`, `polar_e2e_results.csv`, or related CSVs [memory-derived]
- safe smoke command: [uncertain]
- heavy command, if known: [uncertain]
- do-not-run-by-default commands:
  - `experiments/run_real_polar_max_pie.py` against raw or large real-data inputs by default. [repo-observed]

### Workflow: replay / security / audit aggregation
- entrypoint:
  - `tools/longrun_build_replay_index.py` [repo-observed]
  - `tools/longrun_run_actual_ir_replay.py` [repo-observed]
  - `tools/longrun_build_finite_key_audit_table.py` [repo-observed]
  - `tools/longrun_build_security_master_table.py` [repo-observed]
- input: prior Polar logs/results and audit/replay inputs [repo-observed]
- output: audit/shadow/master security summaries under result directories [repo-observed]
- safe smoke command: [uncertain]
- heavy command, if known: [uncertain]
- do-not-run-by-default commands:
  - any `longrun_*` or `minrerun_*` scripts unless explicitly asked. [repo-observed]

### Workflow: real-data / synthetic comparison benchmark
- entrypoint:
  - `python -m comparison_bench.src.comparison_bench.cli.build_dataset` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.run_benchmark` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.compare_methods` [repo-observed]
- input:
  - paired symbol tables with normalized columns [repo-observed]
  - or sidecar directories containing `a_eff.npy`, `b_eff.npy`, and optional `sidecar_meta.json` [repo-observed]
  - benchmark YAML configs under `comparison_bench/configs/` [repo-observed]
- output:
  - `comparison_bench/outputs_comparison/ir_benchmark_results.csv` [repo-observed]
  - `comparison_bench/outputs_comparison/ir_frame_results.parquet` [repo-observed]
  - `comparison_bench/outputs_comparison/run_manifest.json` [repo-observed]
  - `comparison_bench/outputs_comparison/ir_method_summary.csv` [repo-observed]
- safe smoke command:
  - `python -m comparison_bench.src.comparison_bench.cli.smoke_test --config comparison_bench/configs/benchmark_synth.yaml` [repo-observed]
- heavy command, if known:
  - `python -m comparison_bench.src.comparison_bench.cli.run_benchmark --config comparison_bench/configs/benchmark_realdata.yaml` [repo-observed]
- do-not-run-by-default commands:
  - full real-data benchmark on all sidecars or all frames unless explicitly requested. [memory-derived]

### Workflow: v3 IR method parameter sweeps
- entrypoint:
  - `python -m comparison_bench.src.comparison_bench.cli.run_cascade_param_sweep --config comparison_bench/configs/cascade_param_sweep.yaml` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.run_layered_ldpc_param_sweep --config comparison_bench/configs/layered_ldpc_param_sweep.yaml` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.run_qldpc_param_sweep --config comparison_bench/configs/qldpc_param_sweep.yaml` [repo-observed]
  - `python -m comparison_bench.src.comparison_bench.cli.run_ir_v3_master --config comparison_bench/configs/ir_methods_v3_master.yaml` [repo-observed]
- input:
  - frame-batch parquet built under `comparison_bench/outputs_comparison/` [repo-observed]
  - sweep YAML configs [repo-observed]
- output:
  - `cascade_param_sweep_results.csv` and frame/diagnostic companions [repo-observed]
  - `layered_ldpc_param_sweep_results.csv` and frame/diagnostic companions [repo-observed]
  - `qldpc_param_sweep_results.csv` and frame/diagnostic companions [repo-observed]
  - `run_errors_ir_v3.csv` [repo-observed]
  - `ir_v3_run_manifest.json` [repo-observed]
- safe smoke command:
  - there is no dedicated tiny smoke CLI; the lightest current path is to restrict configs before running. [uncertain]
- heavy command, if known:
  - `python -m comparison_bench.src.comparison_bench.cli.run_ir_v3_master --config comparison_bench/configs/ir_methods_v3_master.yaml` [repo-observed]
- do-not-run-by-default commands:
  - v3 master runner or any full representative/all-point sweep in a fresh environment without confirming output policy first. [repo-observed]

### Workflow: v3 report table generation
- entrypoint: `python -m comparison_bench.src.comparison_bench.cli.make_report_tables --config comparison_bench/configs/ir_methods_v3_master.yaml` [repo-observed]
- input: existing v3 sweep CSV outputs [repo-observed]
- output: `comparison_bench/outputs_comparison/report_tables_v3/` CSV tables [repo-observed]
- safe smoke command: same as entrypoint, but only after sweep outputs already exist. [repo-observed]
- heavy command, if known: same as entrypoint; relatively lighter than the sweep commands. [repo-observed]
- do-not-run-by-default commands:
  - none obvious beyond not pointing it at incomplete/missing sweep outputs. [repo-observed]

## 5. Data and Result Policy
- raw data directories:
  - raw real data is external to the repo. Historical provenance includes a legacy Windows path under `D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s` [memory-derived, legacy Windows path]
  - WSL default logical data root is `PROJECT_DATA_ROOT=/mnt/d/Data` from `wsl-env.sh`. [repo-observed]
- result/output directories:
  - original result area: `results/` [repo-observed]
  - comparison result area: `comparison_bench/outputs_comparison/` [repo-observed]
- checkpoint directories:
  - `comparison_bench/outputs_comparison/` contains run manifests and append-only sweep outputs, effectively acting as benchmark checkpoints. [repo-observed]
  - external run/checkpoint roots may exist outside the repo; treat them as [uncertain] unless explicitly mounted. [uncertain]
- files/directories agents must not overwrite:
  - `results/` and anything under it unless explicitly requested. [repo-observed]
  - `comparison_bench/outputs_comparison/` existing benchmark results, diagnostics, manifests, test fixtures, or summaries unless explicitly requested. [repo-observed]
  - raw data outside the repo. [repo-observed]
  - original Polar outputs imported by `polar_existing` bridge. [repo-observed]
- preferred new-output naming convention:
  - new comparison outputs should stay under `comparison_bench/outputs_comparison/` and use additive names consistent with current patterns such as `*_results.csv`, `*_frame_results.parquet`, `*_diagnostics.csv`, `*_manifest.json`, or nested subdirectories like `report_tables_v3/`. [repo-observed]

## 6. Schema and Interface Contract
- CSV columns that must not silently change:
  - normalized input columns: `frame_id`, `pair_idx`, `alice_symbol`, `bob_symbol` [repo-observed]
  - propagated metadata columns: `loss_db`, `dimension`, `bin_width_ps`, `n_eff_pairs`, `threshold_ps`, `effective_pairing_window_ps`, `processing_rule_version`, `pairing_path_tag` [repo-observed]
  - benchmark output columns include at least:
    - `dataset_id`, `data_mode`, `source_path`, `loss_db`, `dimension`, `bin_width_ps`, `n_eff_pairs`, `frame_len_symbols`, `frame_len_bits`, `method`, `method_variant`, `method_status`, `processing_rule_version`, `pairing_path_tag`, `threshold_ps`, `effective_pairing_window_ps`, `n_frames_total`, `n_frames_attempted`, `n_frames_success`, `n_frames_failed_decode`, `n_frames_failed_verify`, `accepted_frame_fraction`, `rejected_frame_fraction`, `raw_ser`, `raw_ber`, `post_ir_ser`, `post_ir_ber`, `leak_EC_actual_bits`, `leak_EC_per_frame`, `leak_EC_per_input_bit`, `beta_eff_empirical`, `runtime_s`, `throughput_input_bits_per_s`, `throughput_output_bits_per_s`, `notes`, `backend_status`, `error_message`, `real_ir_success`, `success_classification` [repo-observed]
  - frame-level output columns include at least:
    - `dataset_id`, `method`, `frame_idx`, `decode_success`, `verify_success`, `raw_frame_ser`, `raw_frame_ber`, `post_frame_ser`, `post_frame_ber`, `leak_bits_frame`, `iterations_used`, `runtime_ms` [repo-observed]
- JSON/YAML keys that must not silently change:
  - `datasets`, `methods`, `global` in benchmark YAMLs [repo-observed]
  - `output_dir`, `max_workers`, `frame_batch_path`, `polar_results_root`, `data_mode`, `frame_len_symbols`, `max_frames_per_dataset` in real-data benchmark YAML [repo-observed]
  - sweep config sections: `cascade`, `layered_ldpc`, `qldpc`, plus `cascade_config`, `layered_ldpc_config`, `qldpc_config` in the v3 master YAML [repo-observed]
- CLI arguments that must not silently change:
  - `build_dataset.py`: `--input`, `--output`, `--dimension`, `--frame-len-symbols`, `--dataset-id`, `--scan-sidecars` [repo-observed]
  - `build_representative_subset.py`: `--input`, `--output` [repo-observed]

  - `run_benchmark.py`: `--config` [repo-observed]
  - `compare_methods.py`: `--input`, `--output` [repo-observed]
  - `smoke_test.py`: `--config` [repo-observed]
  - `run_cascade_param_sweep.py`: `--config` [repo-observed]
  - `run_layered_ldpc_param_sweep.py`: `--config` [repo-observed]
  - `run_qldpc_param_sweep.py`: `--config` [repo-observed]
  - `run_ir_v3_master.py`: `--config` [repo-observed]
  - `make_report_tables.py`: `--config` [repo-observed]
- config keys that must not silently change:
  - method names: `polar_existing`, `cascade_lite`, `layered_ldpc_lite`, `qldpc_reference` [repo-observed]
  - v3 sweep keys including `block_size_schedule`, `num_passes`, `permutation_mode`, `seed`, `verify_mode`, `frame_caps`, `parity_fraction`, `max_iter`, `osd_order`, `bp_method`, `mapping`, `llr_mode`, `bitplane_rate_mode`, `check_fraction`, `row_weight`, `decoder`, `channel_model` [repo-observed]
- function signatures that must not silently change:
  - `FrameBatch`, `IRRunConfig`, `IRRunResult` dataclass fields in `comparison_bench/src/comparison_bench/types.py` [repo-observed]
  - `load_pairs_table(path: Path) -> pd.DataFrame` [repo-observed]
  - `normalize_pair_columns(df: pd.DataFrame) -> pd.DataFrame` [repo-observed]
  - `build_frame_batch(...) -> FrameBatch` [repo-observed]
  - `locate_existing_polar_outputs() -> list[Path]` and `run_polar_existing(batch: FrameBatch, cfg: IRRunConfig) -> IRRunResult` [repo-observed]
- output file naming conventions:
  - base benchmark outputs: `ir_benchmark_results.csv`, `ir_frame_results.parquet`, `run_manifest.json`, `ir_method_summary.csv` [repo-observed]
  - v3 outputs: `cascade_param_sweep_results.csv`, `layered_ldpc_param_sweep_results.csv`, `qldpc_param_sweep_results.csv`, `run_errors_ir_v3.csv`, `ir_v3_run_manifest.json`, `report_tables_v3/*.csv` [repo-observed]

## 7. Baseline and Scientific Semantics
- baseline algorithms:
  - original imported baseline: `polar_existing` [repo-observed]
  - executable classical baseline: `cascade_lite` [repo-observed]
  - executable binary LDPC baseline: `layered_ldpc_lite` [repo-observed]
  - q-ary reference baseline: `qldpc_reference` [repo-observed]
- current assumptions:
  - original Polar code is frozen and must be treated as read-only baseline logic. [repo-observed]
  - comparison layer is outer-wrapper only; it should read existing Polar outputs first and only use CLI mode if explicitly configured. [repo-observed]
  - `cascade_lite` is an internal simplified multi-pass parity/bisection baseline, not a full industrial Cascade transcript implementation. [repo-observed]
  - `layered_ldpc_lite` is a binary bit-plane baseline using `ldpc.BpOsdDecoder` when available, with explicit failure statuses rather than fake success. [repo-observed]
  - `qldpc_reference` currently represents a reference-grade q-ary decoder path, not a production qLDPC system. [memory-derived]
- high-risk variables:
  - `dimension` / `q` [repo-observed]
  - `bin_width_ps` [repo-observed]
  - `frame_len_symbols` [repo-observed]
  - `parity_fraction` [repo-observed]
  - `max_iter` [repo-observed]
  - `mapping` (`gray` vs `natural`) [repo-observed]
  - `llr_mode` and `bitplane_rate_mode` in layered LDPC sweeps [repo-observed]
  - `block_size_schedule`, `num_passes`, and `permutation_mode` in Cascade sweeps [repo-observed]
- known coupling/confounding factors:
  - raw SER and dimension are strongly coupled to decode success on real-data representative points. [memory-derived]
  - imported `polar_existing` point-level results are not always frame-identical to executable baseline frame subsets. [memory-derived]
  - leakage numbers are method-specific decompositions and should only be compared when the decomposition semantics remain consistent. [repo-observed]
  - sidecar-derived frame batches depend on `a_eff.npy` / `b_eff.npy` plus sidecar metadata, so path/layout assumptions matter. [repo-observed]
- metrics that must preserve meaning:
  - `raw_ser`, `raw_ber`, `post_ir_ser`, `post_ir_ber` [repo-observed]
  - `leak_EC_actual_bits`, `leak_EC_per_frame`, `leak_EC_per_input_bit` [repo-observed]
  - `accepted_frame_fraction`, `rejected_frame_fraction` [repo-observed]
  - `n_frames_success`, `n_frames_failed_decode`, `n_frames_failed_verify` [repo-observed]
  - `beta_eff_empirical` must remain derived from leakage and error inputs, not hand-filled. [repo-observed]

## 8. Known Issues and Fragile Points
- path issues:
  - original and comparison workflows have historical Windows-specific path usage; these must be translated deliberately for WSL. [repo-observed]
  - `polar_existing_bridge.py` still contains a legacy Windows default for `DEFAULT_POLAR_RESULTS_ROOT`; treat that as historical provenance, not a future path contract. [repo-observed, legacy Windows path]
- environment issues:
  - git commit/stage may fail because `.git/index.lock` cannot be created. [memory-derived]
  - PowerShell profile warnings are noisy but not necessarily fatal. [memory-derived]
  - optional parquet/YAML dependencies may be missing, causing fallback behavior. [repo-observed]
- data format issues:
  - sidecar directories are directory-based datasets, not flat CSV files. [repo-observed]
  - `load_pairs_table()` supports CSV, parquet/pickle, and sidecar directories; unsupported formats will fail. [repo-observed]
  - comparison outputs also contain test fixtures and temporary pytest artifacts under `comparison_bench/outputs_comparison/`; do not treat those as production outputs. [repo-observed]
- numerical/scientific interpretation risks:
  - `polar_existing` imported results may legitimately contain `NaN` for fields absent from source tables, especially leakage/runtime supplements. [memory-derived]
  - `qldpc_reference` results must not be described as full industrial qLDPC results unless method status and notes explicitly justify that. [repo-observed]
  - `cascade_lite` strong performance in representative sweeps should not be overinterpreted as final paper-grade evidence without broader sweeps. [memory-derived]
  - `layered_ldpc_lite` failure regions may reflect multiple causes: high raw SER, short frame length, parity allocation, or bit-plane independence assumptions. [memory-derived]
- long-running commands:
  - any `longrun_*`, `minrerun_*`, or `routeA_*` tooling under `tools/` [repo-observed]
  - real-data benchmark sweeps and `run_ir_v3_master` can be substantial even with representative subsets. [repo-observed]

## 9. Agent Operating Constraints
- minimal patch only. [repo-observed]
- no broad refactoring of original repository structure. [repo-observed]
- no raw data modification. [repo-observed]
- no result overwrite in `results/` or `comparison_bench/outputs_comparison/` unless explicitly asked. [repo-observed]
- no baseline semantic change to the copied Polar workflow. [repo-observed]
- no schema change unless explicitly requested. [repo-observed]
- WSL/POSIX path default for future harness and agent docs. [repo-observed]
- treat legacy Windows paths as provenance only; do not bake them into new harness defaults. [repo-observed]
- preserve current CLI names, config keys, output file names, and CSV field names. [repo-observed]
- do not silently convert `reference`, `stub`, `unavailable`, `decode_failed`, or `no_verified_success` into `ok`. [memory-derived]

## 10. Unknowns To Verify
- Which original `docs/` files inside this repo are authoritative versus copied from another upstream state. [uncertain]
- Whether MATLAB/Octave is actually required anywhere in this repository copy. [uncertain]
- Whether the original Polar front-half and replay/security scripts are fully runnable in WSL without binary/toolchain adjustments. [uncertain]
- Whether `src/reconciliation/cpp_polar/` binaries are Windows-only in practice or have a portable rebuild path documented elsewhere. [uncertain]
- Whether all existing v3 comparison outputs should be treated as canonical or as exploratory benchmark artifacts. [uncertain]
- Whether any additional AGENTS-style repository guidance already exists outside the scanned paths. [uncertain]
- Whether the external real raw-data root used historically is mounted in the target WSL environment. [uncertain]

## 11. Multi-Agent Workflow Files

### Created (2026-06-15)
- `AGENTS.md` — repository-level agent rules (baseline protection, output policy, schema stability, path discipline, agent constraints, OpenSpec workflow). [created]
- `docs/decision-log.md` — durable decisions and rejected alternatives. [created]
- `docs/troubleshooting.md` — reusable failure modes and fixes. [created]
- `openspec/project.md` — project-level context for OpenSpec change management. [created]
- `openspec/changes/real-ir-success-first/` — active change proposal details. [created]
- `CURRENT_TASK.md` — current active documentation/workflow task. [created]
- `RUN_COMMANDS.md` — curated smoke/benchmark/do-not-run command list. [created]
- `REVIEW_CHECKLIST.md` — review checklist for baseline protection and schema stability. [created]
- `AGENT_HANDOFF.md` — concise handoff note for the next agent. [created]
- `comparison_bench/src/comparison_bench/metrics/success.py` — success classification module. [created]
- `comparison_bench/src/comparison_bench/cli/build_representative_subset.py` — representative subset extractor. [created]
- `comparison_bench/configs/benchmark_representative.yaml` — representative subset benchmark config. [created]
- `comparison_bench/tests/test_success_classifier.py` — success classification unit tests. [created]
- `docs/real-ir-success-audit-20260615.md` — audit report summarizing baseline evaluations on representative frames. [created]

### Current OpenSpec state (verified 2026-07-25)
- Phase 0 reconciliation is `docs/openspec-phase0-reconciliation-20260725.md`.
  All five historical IR changes remain active: `real-ir-success-first` has
  32/34 evidenced tasks; optimization has 14/14 tasks but lacks its written
  512/1024-symbol evidence; expanded evidence has 19/20; evidence-package
  has 26/26 tasks but lacks clean direct fixed-path pytest and a before/after
  non-modification proof; group-meeting has 21/29 and lacks its frame-count,
  expected-config/test, and clean-full-suite requirements. Do not archive any
  historical change from artifact presence alone. [repo-observed]
- `final-ir-method-selection` was archived on 2026-07-25 at
  `openspec/changes/archive/2026-07-25-final-ir-method-selection/`; its
  canonical specification is `openspec/specs/final-ir-method-selection/spec.md`.
  It is the bounded comparison protocol that
  ranks only executable `cascade_lite` and `layered_ldpc_lite`; qLDPC remains
  `reference_only`, and `polar_existing` is historical, non-frame-identical
  context. It requires group-disjoint tuning/confirmation, one frozen global
  configuration per candidate, retained attempted failures, unranked
  method-specific leakage, bounded stopping, and a non-numerical Route A
  field-compatibility gate. [repo-observed]

### Final-IR authoritative evidence chain (verified 2026-07-25)
- v1 data lock is
  `comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/`.
  The locked domain is real d=1024, 64-symbol frames, dataset raw SER
  [0.20, 0.30), with 60 tuning frames from
  `real_typeii_20db_d1024_bw200_blk0` and 60 confirmation frames from
  `real_typeii_20db_d1024_bw180_blk0`; the groups are disjoint. Verify
  read-only with `python -m comparison_bench.src.comparison_bench.cli.lock_final_ir_data --verify --manifest comparison_bench/outputs_comparison/final_ir_method_selection/20260725_v1/data_lock_manifest.json`.
  [repo-observed]
- v1 Phase-3 outputs are invalid for decisions (`invalid_run_notice.json`).
  v2 is the sole authoritative bounded run:
  `.../20260725_v2/`; it froze Cascade `[12,6,24,13]`, 4 passes,
  seeded-random gray, and LDPC parity 1.0, 50 iterations,
  `bsc_estimated`/`uniform` gray before confirmation. It retained all 60
  attempts per candidate: Cascade 60/60 independently verified successes and
  LDPC 59/60. [repo-observed]
- v3 audit is superseded by its additive notice. v4 is authoritative:
  `.../20260725_v4_audit/`. Its read-only audit verifies the same 60 locked
  confirmation keys, frozen corrected-grid configurations, all status
  denominators, and evidence hashes. One Cascade-only discordance gives the
  pre-registered exact two-sided paired p-value 1.0 at alpha 0.05; outcome is
  strictly `no_decision`, not a winner. Claims do not extend beyond the locked
  domain, do not rank cross-method leakage, and do not select Polar or qLDPC.
  [repo-observed]
- The Route A compatibility gate is `fail`: comparison outcomes lack the
  documented universal-hash verification, leakage-accounting, and
  correctness-budget fields. No Route A numerical rerun or formal-proof claim
  was made. [repo-observed]
- Phase-5 verification: five-module `py_compile`, focused unittests 7/7,
  read-only v1/v4 verification, and safe comparison pytest 22/22 passed with
  `test_evidence_package.py` excluded because it writes a fixed tracked path.
  External pytest temp/permission behavior remains an infrastructure caveat;
  the six tracked `workspace/pytest-tmp/` deletions are pre-existing and must
  remain untouched. [repo-observed]

### Formal IR qualification evidence chain (verified 2026-07-25)
- Formal candidates are additive under
  `comparison_bench/src/comparison_bench/formal_ir/`; the
  frozen Polar pipeline and the `cascade_lite`/`layered_ldpc_lite` methods and
  their evidence remain unchanged. [repo-observed]
- The sole authoritative synthetic qualification is
  `comparison_bench/outputs_comparison/formal_ir_methods/20260725_v3_synthetic/`.
  Its strict read-only report promotes `cascade_formal_v1` in both strata
  (32/32 `verified_success` at p=.01 and p=.02). It does not promote
  `ldpc_formal_v1` (29/32 and 14/32); all 21 retained non-successes are
  `verify_failed`, with zero unclassified/internal/provenance/accounting
  failures. [repo-observed]
- The invalid real v1 root received only its additive invalid-lock notice and
  made zero formal-method calls. The sole authoritative real qualification is
  `comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade/`:
  its strict verifier accepts exactly seven artifacts, its preflight passed
  29 tests with exit 0, and Cascade achieved 60/60 requested confirmation
  frames as `verified_success`, with union bound `3.2526065174565133e-18` and
  zero unclassified/internal/provenance/accounting failures. The resulting
  promotion is limited to d=1024, 64 symbols, bw120, frame SER `[.20,.30)`;
  LDPC was not run on real data. [repo-observed]
- Read-only verification commands (do not rerun the qualification runners):
  `python -m comparison_bench.src.comparison_bench.cli.run_formal_synthetic_qualification --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260725_v3_synthetic --verify`
  and
  `python -m comparison_bench.src.comparison_bench.cli.run_formal_real_qualification --output-dir comparison_bench/outputs_comparison/formal_ir_methods/20260725_v2_real_cascade --verify`.
  [repo-observed]
- Before any frame-identical Polar/Cascade/LDPC comparison, a separate
  LDPC-improvement OpenSpec change must obtain fresh synthetic and real LDPC
  promotion. Do not substitute a lite method or tune on confirmation data.
  [repo-observed]

### Formal LDPC v2 improvement evidence (verified 2026-07-26)
- Archived change is
  `openspec/changes/archive/2026-07-26-improve-formal-ldpc-v2/`. Additive
  `ldpc_formal_v2` freezes
  nine policies: rate margin 0/1/2 crossed with `OSD_0/0`, `OSD_CS/1`, and
  `OSD_CS/2`. The n=64 nested codebook has 16 masters per plane and selected
  prefix matrices 32/40/48/56. Its structural screening is a proxy, not
  verified decoding evidence. [repo-observed]
- The v1 integration root `20260725_v1_ldpc_v2_synthetic` is invalid: the
  v1 codebook verifier makes all 576 policy outcomes plus 64 associated
  outcomes `unsupported_domain`. Its seven artifacts remain immutable and an
  additive invalid notice records the exclusion. [repo-observed]
- Fresh v2 plan SHA256 is
  `c0770b5b1c80c277448ca832b01a5dd6d8413df78870fa040c6546d0098ede18`, with
  zero old/new CSPRNG overlap. Strict verification passed. Development results
  are 26/64 (margin 0), 33/64 (margin 1), and 56/64 (margin 2), identical for
  every OSD variant; the selected policy is rate margin 2 with `OSD_0/0`.
  [repo-observed]
- Confirmation records 28/32 at p=.01 and 29/32 at p=.02, seven
  `verify_failed`, and verification invoked for all 64 outcomes, with zero
  unclassified/internal/provenance/accounting failures. Status is
  `non_promoted`; no real lock or run is authorized, and confirmation must not
  be used to tune. [repo-observed]
- Artifact SHA256 prefixes: plan `c077...`, codebook `360b77...`, outcomes
  `9adb0...`, policy `303919...`, transcript `4b438...`, manifest `d185fc...`,
  report `53fbe5...`. Final checks: v2-focused 25 passed plus 5 subtests,
  general 52 passed/11 skipped, formal-real 12 passed, strict verification
  passed, and frozen `src/`, `experiments/`, `tools/`, and `results/` diff is
  empty. Terra low only implemented frozen tasks and specified tests; the main
  thread retained planning and acceptance. [repo-observed]
- Short- and medium-term engineering work is complete with reproducible
  evidence, but LDPC has not met promotion; the fair three-method comparison
  remains blocked. [repo-observed]

## 11. Parallel Binary and Nonbinary LDPC Direction (2026-07-26)

- Binary and nonbinary LDPC are now planned as independent parallel research
  lanes. The detailed handoff is
  `comparison_bench/docs/ldpc_parallel_handoff.md`. [repo-observed]
- Binary starts from immutable, non-promoted `ldpc_formal_v2` evidence and
  targets longer frames, deterministic QC/PEG/protograph families,
  incremental redundancy, and per-bit-plane soft information. Existing
  confirmation evidence cannot be used for tuning. [repo-observed]
- Nonbinary N0 field-backend work is implemented under the independent
  `nbldpc_formal_v1` identity in
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_field.py`.
  It pins deterministic polynomial-basis GF(2^m) arithmetic for powers-of-two
  q through 1024, canonical field metadata/IDs, and a read-only fail-closed
  preflight. `qldpc_reference` remains unchanged and reference-grade.
  This proves field-backend feasibility only, not decoder feasibility,
  qualification, promotion, or comparison readiness. [repo-observed]
- The two lanes require separate OpenSpec changes, codebooks,
  development/confirmation splits, artifacts, leakage accounting, verifiers,
  and promotion decisions. Only independently promoted methods may enter a
  later frame-identical comparison. [repo-observed]

## 12. Binary LDPC Long-Frame v3 Phase 1 (2026-07-26)

- Active OpenSpec change:
  `openspec/changes/binary-ldpc-long-frame-and-ir-v3/`. [repo-observed]
- Candidate-only `codebook_long_v3.py` supports n=256/512/1024, ten planes,
  four deterministic candidates, and nested 1/2, 5/8, 3/4, 7/8 check
  prefixes. HGF2V3 bytes and a reconstruction-verified manifest bind all 120
  candidate identities. [repo-observed]
- Actual-rank, no-zero/duplicate-column, weight-bound, exact 4-cycle, and
  `column_pair_extrinsic_degree_v1` proxy tests passed. Main-thread evidence:
  focused 4 passed in 10.88 s; v2 regression 7 passed/1 skipped in 81.41 s;
  compilation/diff checks passed and frozen directories were unchanged.
  [repo-observed]
- Phase 1 is engineering evidence only: no FER, candidate selection, decoder,
  confirmation/real data, qualification, or promotion. Next freeze a
  sacrificed-development FER evaluation contract. [repo-observed]

## 13. Binary LDPC Long-Frame v3 Phase 2 (2026-07-26)

- `long_v3_development.py` implements exact sacrificed p=.01/.02 generation,
  canonical seed/source hashes, pinned BP+OSD-0 metadata, four-prefix
  incremental evaluation, retained statuses, and exact four-candidate
  selection. It is in-memory and writes no result artifact. [repo-observed]
- Selection is frozen as worst-stratum successes, total successes, syndrome
  disclosure, then candidate ID. Runtime and structural proxies are excluded.
  Tests independently verify the data/policy/selection hash preimages and
  fail-closed malformed-grid behavior. [repo-observed]
- Main-thread evidence: focused 5 passed in 0.53 s; Phase1/v2 regression
  11 passed/1 skipped in 92.68 s; compilation and frozen-directory checks
  passed. [repo-observed]
- Phase 2 used injected test decoders only. No pinned-backend development
  sweep, candidate FER evidence, selection, confirmation, real data,
  qualification, or promotion exists yet. Next freeze a bounded backend
  preflight/pilot. [repo-observed]

## 14. Binary LDPC Long-Frame v3 Phase 3A Pilot (2026-07-26)

- A single in-memory pinned-backend pilot ran exactly once at
  n=256/plane0/candidate0/p=.01 on 16 sacrificed frames. Backend was
  `ldpc==2.4.1`; exit 0; stderr empty; process 0.3227008000249043 s; external
  wall 1.0 s. [repo-observed]
- Outcomes were 16/16 exact success, terminal p050=15/p0625=1, and 2080 total
  syndrome bits. No file was written and no candidate was selected.
  [repo-observed]
- This clears one-slice backend feasibility only. It is not comparative FER,
  n=512/1024 evidence, qualification, or promotion. Next freeze an immutable,
  verifier-bound full sacrificed-development sweep contract. [repo-observed]

## 15. Binary LDPC Long-Frame v3 Phase 3B Tooling (2026-07-26)

- Additive runner/verifier tooling now freezes a 3840-row, 30-selection
  sacrificed-development grid with prepare/execute no-overwrite lifecycle,
  six canonical artifacts, code/backend/hash DAG, failure finalization, and
  production/test isolation. [repo-observed]
- Read-only verification reconstructs deterministic source provenance and the
  accepted candidate-selection function, but does not rerun LDPC decoding.
  Its success is artifact integrity only. [repo-observed]
- Main-thread evidence: Phase3B focused 3 passed in 12.30 s; all long-v3
  12 passed in 12.94 s; v2 regression 7 passed/1 skipped in 81.34 s;
  compilation/diff/frozen-directory checks passed. Test artifacts are under
  `workspace/formal_long_v3_phase3b_tests_run3`. [repo-observed]
- No production plan or 3840-row sweep exists yet. Next create and inspect one
  fresh plan, then separately authorize its single execution. [repo-observed]

## 16. Binary LDPC Long-Frame v3 Phase 3C Development Evidence (2026-07-26)

- Immutable development root:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_long_v3_development/`.
  Execute ran once in 28.9 s with 3840 outcomes/30 selections; strict verifier
  ran once in 11.2 s, exit 0, without decoder reexecution. [repo-observed]
- All 3840 per-plane candidate outcomes were
  `development_exact_success`. Selected per-plane mean syndrome bits:
  n256 129.0/134.6, n512 260.4/280.4, n1024 541.6/635.2 for p001/p002.
  [repo-observed]
- The current per-plane terminal is chosen using Alice-truth exact equality.
  This is a sacrificed-development oracle and not a deployable stopping signal;
  its leakage and 100% result are not qualification evidence. [repo-observed]
- Next aggregate ten planes into global incremental rounds with one
  frame-wide Toeplitz verification tag, count slowest-plane syndrome/tag
  leakage, then select the formal length/policy before fresh confirmation.
  [repo-observed]

## 17. Binary LDPC Long-Frame v3 Phase 4 Frame Development (2026-07-26)

- Ten-plane read-only aggregation produced 96 q=1024 development frames and
  modeled one 64-bit frame-wide Toeplitz tag over at most four global rounds.
  Aggregation SHA256 is
  `029e33c42f254e40725a370065d30196216501085d5def5f0f0c935aca6c933c`.
  [repo-observed]
- All lengths retained 16/16 success in both strata. Mean frame key-disclosure
  fractions p001/p002: n256 .5640625/.68125; n512 .590625/.7546875; n1024
  .6625/.8421875. [repo-observed]
- Frozen development choice is n=256 with tuple
  `[-16,-32,.68125,.62265625,256]`. This is sacrificed-development design
  selection only; the stopping tag was modeled, not executed. [repo-observed]
- Next implement actual n256 ten-plane formal decoding, locked Toeplitz
  seed/tag, transcript, caps and fail-closed statuses before any fresh
  qualification. [repo-observed]

## 18. Binary LDPC Long-Frame v3 Phase 5 Formal Method (2026-07-26)

- `formal_ir/ldpc_v3.py` implements `ldpc_formal_v3` for exactly q=1024,
  n=256 and ten MSB-first Gray planes with frozen candidates
  `[1,0,1,2,0,0,1,3,2,3]`. [repo-observed]
- It reconstructs canonical long-v3 matrices, validates a self-hashed
  sacrificed calibration, requires `ldpc==2.4.1`, and decodes all ten planes
  in four possible synchronous incremental-syndrome rounds. [repo-observed]
- One 64-bit frame-wide Toeplitz tag is disclosed once and checked only after
  complete rounds. The decoder receives no tag/match or Alice truth. Strict
  transcript validation binds terminal prefix, syndrome/tag/seed disclosure,
  epsilon, caps, backend and frozen selection. [repo-observed]
- Main-thread evidence: focused 6 passed in 2.15 s; long-v3 regression 13
  passed in 16.12 s; v2 regression 7 passed/1 skipped in 81.27 s;
  compilation/diff/frozen-directory checks passed. [repo-observed]
- This accepts method engineering only. No confirmation runner/artifact,
  strict package verifier, qualification, promotion, real-data result, or fair
  comparison eligibility exists. Phase 6 must be planned and frozen before
  execution. [repo-observed]

## 19. Binary LDPC v3 Phase 6 TTBIN Bridge and Synthetic Stop (2026-07-26)

- Phase 6A read-only bridge binds the real 20 dB main/chunk TTBIN and exact
  q=1024 sidecars, selects 64 bw100 calibration plus 32 each bw120/180/200
  reserved confirmation frames, and reconstructs source/lock/calibration
  hashes. Calibration plane p_hat ranges from .000366 to .122620.
  [repo-observed]
- Immutable synthetic package
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/`
  was prepared, executed, and strictly verified exactly once. Verification
  accepted 64 outcomes and returned `decoder_reexecution=false`.
  [repo-observed]
- Calibrated confirmation achieved 3/32 and 1.25x stress achieved 1/32 versus
  31/32 gates. The other 60 outcomes are `verify_failed`; forbidden
  internal/provenance/accounting failures are zero. [repo-observed]
- Binary v3 is non-promoted. Phase 6C real tooling/output was not created and
  is locked. Do not tune or retry from confirmation. A successor requires a
  new OpenSpec improvement and fresh synthetic confirmation. [repo-observed]
- Nonbinary N1 is implemented in
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_codebook.py` as a
  pure in-memory n=64 family: one deterministic 32x64 mother matrix and exact
  16/24/32 ordered prefixes, with three SHA256-derived cyclic shifts,
  explicit nonzero GF(q) coefficients, an identity parity half, and rank
  calculated with the pinned N0 GF(q) arithmetic. [repo-observed]
- Canonical `NBLDPC1` bytes include the full field representation,
  construction, dimensions, topology, coefficients, seed, and ordering.
  Golden codebook/manifest SHA256 tests plus reconstruction-based tamper
  checks cover field, coefficient, rank, prefix, codebook-ID, and manifest-ID
  drift. Focused N0+N1+qLDPC tests passed 22/22; the selected
  formal/nonbinary/qLDPC regression passed 29/29. [repo-observed]
- N1 is structural rank/hash evidence only. It does not establish a soft
  decoder, distance/FER performance, qualification, promotion, outputs, or
  comparison readiness. N2 must freeze decoder and formal accounting
  contracts before implementation or dependency selection. [repo-observed]
- Nonbinary N2 is implemented in
  `comparison_bench/src/comparison_bench/formal_ir/nonbinary_qspa.py` as a pure
  full-message probability-domain FFT-QSPA feasibility decoder. It consumes
  Bob symbols, Alice's public syndrome, and verified N1 codebooks; its public
  decoder signature has no Alice truth or callback. q=4 coefficient/coset
  check updates match brute-force convolution, and q=1024 executes inside the
  frozen n=64/check/iteration/16-MiB declared dense-message bounds.
  [repo-observed]
- `syndrome_consistent` is deliberately separate from locked Toeplitz
  verification. Symbols map to fixed-width MSB-first bits; syndrome
  disclosure is checks*log2(q), invoked verification tags add their exact
  length, and public-control bits remain separate. N0-N2 plus qLDPC tests
  passed 35/35; selected formal verification/Cascade/LDPC regressions passed
  17 with 2 skipped. [repo-observed]
- N2 is bounded engineering feasibility only. It does not prove general
  correction, FER/performance, calibration, synthetic/real qualification,
  promotion, outputs, production readiness, or comparison eligibility. N3
  requires planner-owned pre-registration before execution. [repo-observed]

## 20. Nonbinary LDPC v2 Development Non-Readiness (2026-07-26)

- `nbldpc_formal_v2` Phase 1/2 was accepted with 21 focused tests; the joint
  N0-N3/v2/formal regression passed 86 with 8 skipped. [repo-observed]
- The immutable root
  `comparison_bench/outputs_comparison/formal_ir_methods/20260726_v2_nbldpc_synthetic/`
  contains one reviewed plan (112 frames, 24 policies, 1216 unique seeds,
  overlap zero), one execution, and one successful strict full replay.
  [repo-observed]
- The selected tempered+damped QC48 policy used margin 8, max_iter 10, and
  32/40 checks for p=.20/.30. Development achieved 0/24 and 5/24 verified
  successes against a 22/24-per-stratum readiness floor. Confirmation was
  never generated or executed. [repo-observed]
- Status is `non_promoted_development`, not confirmation FER or real-data
  evidence. No rerun, tuning, N4 sidecar adapter, or `.ttbin` processing is
  authorized. [repo-observed]

## 21. Binary LDPC v4 Development Backend Stop (2026-07-27)

- `binary-ldpc-adjacent-channel-v4` implements deterministic adjacent-channel
  modeling, 40 anchored sparse binary codebooks, a fixed 648-bit formal
  method, immutable development/synthetic/real packages, and read-only
  source/transcript/gate verifiers. Focused main-thread acceptance passed
  15+8+3+4 tests; cross-version regression passed 119 with 10 skipped.
  [repo-observed]
- Sole production development evidence:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260727_v1_binary_ldpc_v4_development/`.
  Plan content SHA256 is
  `af644e2f4a3dab596f34350b18ecfb1df56cb46b93670cb16e89f3ca1ae67c5e`.
  The read-only verifier returned verified/completed with
  `decoder_reexecution=false`, but readiness was false. [repo-observed]
- Nominal and stress each retained 512 denominators, zero frame successes,
  and 5,120 selected-plane `development_decoder_error` outcomes. This is an
  implementation failure and must not be interpreted as FER or code quality.
  [repo-observed]
- A no-decode diagnostic confirmed the backend mismatch: `ldpc==2.4.1`
  rejects NumPy-array `error_channel` with `expected list`, while the same
  vector converted by `.tolist()` constructs. The formal v4 path converts it;
  the frozen development path did not. [repo-observed]
- No v4 production synthetic or real directory exists. The frozen stop rule
  forbids editing/tuning/rerunning this package. A continuation needs a new
  versioned OpenSpec implementation-correction lane and fresh evidence; fair
  Cascade/LDPC/Polar comparison remains blocked. [decision]

## 22. Binary LDPC v4 Backend Correction Readiness (2026-07-27)

- `binary-ldpc-v4-backend-correction-v1` added only versioned development
  files. It converts the frozen Bob-conditioned float64 error channel to a
  Python list at the `ldpc==2.4.1` constructor boundary; historical v4 source
  and evidence hashes remain unchanged. [repo-observed]
- Immutable corrected package:
  `comparison_bench/outputs_comparison/formal_ir_methods/20260727_v2_binary_ldpc_v4_development/`.
  Plan content SHA256 is
  `1e208832ac421e69c0488d33e39953755ba487c25f9bf9db43bdda79cc53daaf`.
  Prepare/execute/read-only verification each ran once; verification returned
  completed/verified, `decoder_reexecution=false`, and readiness true.
  [repo-observed]
- Frozen development results are 510/512 adjacent nominal and 511/512
  adjacent stress, with zero forbidden failures. Selected candidates are
  `[0,0,0,0,0,0,2,0,2,2]`. This clears only the 495/512 sacrificed-
  development screen. [repo-observed]
- No corrected-v4 synthetic or real production output was created. Synthetic
  qualification still requires a fresh main-thread plan audit and one
  independent execution; comparison eligibility and real `.ttbin` claims
  remain unestablished. [decision]

## 23. Binary LDPC v4 Corrected Synthetic Promotion (2026-07-28)

- Immutable package
  `comparison_bench/outputs_comparison/formal_ir_methods/20260728_v2_binary_ldpc_v4_synthetic/`
  strictly verified with 256 outcomes, no decoder reexecution, and promotion:
  nominal 127/128, stress 126/128, zero forbidden failures. [repo-observed]
- Plan content SHA256 is
  `02a198ea4d03ae4d7dad7db6e2b4099e85f5b75c0d8acad34e8449d67cb769fb`.
  Fresh roots/seeds have zero overlap with v3 and development. Do not rerun or
  tune from this confirmation. [repo-observed]
- Real qualification remains unrun. Current bw120/bw180/bw200 sidecars each
  have 117 complete frames; excluding 32 v3-reserved identities leaves 85,
  below the frozen 128 by 43 per stratum. Real prepare must remain blocked
  until traceable same-domain source data fills that deficit. [decision]
- Prefer at least 64 newly supplied complete frames per real stratum to absorb
  duplicate/incomplete rejection. Preserve 128 denominators and 126/128 gates;
  do not reuse reserved frames or weaken the claim to fit current data.
  [decision]

## 24. Binary LDPC v4 Real-Source Intake Acceptance (2026-07-28)

- The only other local 20 dB tree is a byte-identical raw-capture copy. Its
  main/chunk SHA256 pair equals the registered capture, so it is not new
  statistical capacity. [repo-observed]
- The Phase 4 intake layer now builds and reconstructs a no-overwrite,
  self-hashed multi-acquisition source extension. It rejects duplicate raw
  pairs and frame payloads, binds exact q=1024 bw120/bw180/bw200 sidecars,
  counts only complete 256-symbol frames, and performs no decoding.
  [repo-observed]
- Main acceptance passed 3 source, 5 real, 7 bridge/source, and 25
  backend/development/formal-real tests. Historical v3/development source
  hashes remain exact and no real production directory exists.
  [repo-observed]
- Real prepare remains unauthorized until a genuinely distinct 20 dB
  acquisition supplies enough validated capacity and a main-thread-reviewed
  extension manifest. The 128 denominators and 126/128 gate remain frozen.
  [decision]

## 25. Project-Wide Delegation Workflow (2026-07-29)

- Substantial delegated implementation starts from one complete frozen task
  packet: file scope, functionality, full test/evidence matrix, commands,
  artifacts, stop rules, and return conditions. [decision]
- The main thread owns planning, requirements, thresholds, OpenSpec,
  acceptance, and scientific conclusions. The implementation subagent is an
  operator and returns only a complete candidate or a concrete reproducible
  blocker; partial “still incomplete” reports are not completion. [decision]
- Main review normally occurs at spec freeze, complete candidate delivery, and
  independent acceptance. Tests progress from focused development to combined
  focused candidate to main regression/compile/frozen-hash/no-output review.
  [decision]
- Verifier acceptance matrices must pre-register byte drift, locally re-signed
  semantic tampering, re-signed manifest/index tampering, and deep
  cross-artifact reconstruction. Known Windows ACL failures require an
  explicitly writable non-production test root. [decision]
- These coordination optimizations do not alter prepare/review/execute/verify,
  immutable failure retention, scientific thresholds, or no-rerun/no-tuning
  boundaries. [decision]
- Acceptance items use stable IDs. Successor evidence machinery starts from
  the nearest accepted predecessor and an explicit delta list. [decision]
- Tests use T0 compile/structural, T1 focused, T2 fake qualification/replay,
  and T3 regression stages; T2/T3 run only at milestones and test-only calls
  explicitly pass fake runners. [decision]
- Windows tests use additive workspace UUID roots with pytest cache disabled.
  Process termination requires positive ownership; dirty-worktree acceptance
  includes untracked hashes, frozen diffs, and output-root checks. [decision]
- Handoffs report only changed files, commands/results, concrete blockers, and
  remaining acceptance IDs; they do not repeat durable project context.
  [decision]

## 26. Binary LDPC v4 16 dB Transfer Result (2026-07-29)

- The sole 16 dB transfer package completed and strictly verified with all 384
  outcomes: bw120 125/128, bw180 128/128, bw200 128/128, and zero forbidden
  failures. Because every layer required 126/128, the package is immutable
  `non_promoted_transfer`. [repo-observed]
- Read-only verification reported no decoder reexecution and changed none of
  the nine files. Plan content SHA256 is
  `ddbf41983d866ce5d320404323ff319b64a867f8f8c32185a890ab7baf97b2da`;
  source-lock content SHA256 is
  `5c654377751cea776a203269b8213959313aa9a0be738935816d36b52181ea87`.
  [repo-observed]
- The 16 dB evidence must not be tuned or rerun and does not promote 16 dB or
  20 dB. A separately scoped unchanged-method 10 dB transfer is frozen under
  `binary-ldpc-v4-10db-transfer-qualification-v1`; if promoted, its claim is
  limited to that independent 10 dB acquisition. [decision]

## 27. Binary LDPC v4 10 dB v1 Prepare Rejection (2026-07-29)

- The v1 10 dB prepare was rejected before execute because validation included
  its own newly written plan in the prior-real root set. It contains exactly
  plan and lock, no outcomes. Preserve it as `invalid_pre_execute`; plan file
  SHA256 is `dae9d27a068bf9b15f25ae684bd3cf290623524b0e92af8989869579b0ac523c`
  and lock file SHA256 is
  `6596316074b0e473de26ba44a87556016f23b082dc36239e06a65fa4e7d11baf`.
  [repo-observed]
- A versioned correction must exclude only the current plan from prior-plan
  discovery while continuing to bind and forbid the invalid v1 roots/seeds.
  No scientific inputs or gates may change. [decision]

## 28. Binary LDPC v4 10 dB v2 Result and v5 Route (2026-07-29)

- The corrected v2 10 dB package strictly verified all 384 outcomes but was
  non-promoted: bw120 125/128, bw180 127/128, bw200 128/128, zero forbidden
  failures. Plan content SHA256 is
  `c6f3592ac24fd32ac136d16f06fd88157757216a81c40643e86d0ba3882af2f6`.
  [repo-observed]
- All four failures were retained `verify_failed` after complete syndrome
  disclosure and Toeplitz mismatch. v4 fixed-rate robustness, not source,
  backend, accounting, or resource failure, is the remaining issue.
  [repo-observed]
- Do not test progressively easier losses until one passes. The v5 route
  pre-locks disjoint unused 10 dB development and confirmation frames, screens
  frozen stronger-OSD/incremental-redundancy policies on development, then
  requires fresh synthetic promotion before one sealed real qualification.
  [decision]

## 29. Nonbinary LDPC v3 Covered-Layered Result (2026-07-30)

- The sole v3 synthetic package was planned once, executed once, and strictly
  replay-verified once. The selected layered-l075 margin-8 policy used 32/40
  checks and passed development readiness at 23/24 for p=.20 and 24/24 for
  p=.30. [repo-observed]
- Sealed confirmation was materialized only after readiness and achieved
  32/32 for p=.20 and 30/32 for p=.30, with zero prohibited failures. The
  frozen 31/32-per-stratum gate failed by one p=.30 frame, so the package is
  immutable synthetic non-promotion evidence. [repo-observed]
- Strict verification returned `verified=True`, `run_status=completed`,
  `promoted=False`. Plan SHA256 is
  `0f35b8679166599efb294caee21822156ba971bec6271875cf55516523cfdee1`;
  selected-policy SHA256 is
  `6193f92af05c1d3a5145cbe31c95a4d20f1eaf5a09970936613c326cc1c59a28`.
  [repo-observed]
- Do not rerun, tune confirmation, overwrite evidence, build N4, access
  sidecars, or process `.ttbin`. Real-data work requires promoted synthetic
  confirmation and a new approved OpenSpec change. [decision]

## 30. Nonbinary LDPC v4 Incremental-Redundancy Result (2026-07-31)

- The sole v4 IR package was planned, executed, and strictly replay-verified
  once. Verification returned `verified=True`, `run_status=completed`,
  `promoted=False`. [repo-observed]
- Development selected `nbldpc_v4_ir_warm`: 64/64 at p=.20 and 63/64 at
  p=.30. Sealed confirmation achieved 128/128 and 120/128; all eight misses
  were p=.30 `decode_failed`, with zero prohibited failures. [repo-observed]
- The package is immutable at
  `comparison_bench/outputs_comparison/formal_ir_methods/20260731_v4_nbldpc_ir_synthetic/`.
  Do not rerun, tune, overwrite, build N4, access sidecars, or process `.ttbin`.
  Any successor requires new OpenSpec, fresh synthetic splits, and a
  pre-registered method change. [decision]
- Reusable process lesson: historical qualification suites whose own official
  roots now exist can correctly reject a test replay as identity reuse. Retain
  that evidence and use isolated algorithm regressions; never edit immutable
  outputs or weaken freshness guards merely to make an old suite green.
  [repo-observed]

## 31. Binary LDPC v5 Phase 2 Development and Phase 3 Synthetic Confirmation (2026-08-01)
- Phase 2 sacrificed development selected V5-C2: 1536/1536 verified success
  (512/stratum across bw120/bw180/bw200 real 10 dB frames), zero forbidden
  failures, 1 round, no fallback. Leakage 648 bits/frame = 2.531 b/symbol =
  0.253 b/input bit (h1 syndrome 584 + verification 64); real raw SER
  bw120 0.1228 / bw180 0.0833 / bw200 0.0767; 204.7 s total. Package immutable
  at comparison_bench/outputs_comparison/formal_ir_methods/
  20260731_v1_binary_ldpc_v5_development/. [repo-observed]
- Robustness evidence committed to comparison_bench/docs/ldpc_v5_robustness/:
  E1 new-seed rerun 768/768, E3 model-consistent (SER 0.243) 768/768,
  E2 uniform OOD control 0/1152 as expected. [repo-observed]
- Phase 3 fresh synthetic confirmation (2026-08-01): 256/256 verified success
  (nominal 128/128 + stress_125 128/128), zero forbidden failures,
  promoted=true, ready_for_real_qualification=true, decoder_reexecution=false.
  Package immutable at .../20260801_v1_binary_ldpc_v5_synthetic/; plan sha256
  c91171dcdde8c1cf5fb31cc21cbad72115756fff034763ce93c75cbef17c10ab. [repo-observed]
- Phase 4 sealed real qualification will use the partition lock confirmation
  partition (128 frames/stratum, role_rank 0--127, never decoded before;
  development used ranks 128--639), gate 126/128 per stratum, zero forbidden
  failures. tasks.md Phase 3 complete; Phase 4 proposal drafted, not yet
  implemented. [decision]
- Polar numerical comparison remains blocked: results/ is empty in this
  checkout and polar_existing imports are historical, non-frame-identical,
  leakage NaN. No Polar-vs-v5 numeric claim is supportable. [repo-observed]
