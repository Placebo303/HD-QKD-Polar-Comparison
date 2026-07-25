# AGENT_PROJECT_MEMORY.md

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

### Still Pending
- None. The coordination docs, benchmark config, subset building, success contract integration, baseline diagnostics, unit tests, and audit run are fully complete.

