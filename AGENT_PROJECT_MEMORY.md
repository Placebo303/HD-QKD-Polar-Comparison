# AGENT_PROJECT_MEMORY.md

## 1. Project Identity

- Project name: High-Dimensional QKD Polar Pipeline. [repo-observed]
- Research purpose: End-to-end evaluation of high-dimensional QKD timing data with Polar-code information reconciliation and finite-key security accounting. [repo-observed]
- Main scientific/engineering objective: Preserve a reproducible mainline from `.ttbin` timing input through E2E extraction, symbol mapping, Polar IR actual replay, Route A finite-key security accounting, and final `PIE_main` / `SKR_main_bps` reporting. [repo-observed]
- Current maturity: Research pipeline with a declared current mainline, archived studies, diagnostics, and local result manifests; not a packaged library. [repo-observed]

## 2. Repository Structure Observed

- Root files: `README.md`, `requirements.txt`, `.gitignore`, `LICENSE`, `wsl-env.sh`, `bootstrap_clone_clean.py`. [repo-observed]
- Documentation:
  - `docs/CURRENT_MAINLINE.md`. [repo-observed]
  - `docs/PROJECT_CLASSIFICATION_20260427.md`. [repo-observed]
  - `docs/RESULTS_MANIFEST_20260427.md`. [repo-observed]
  - `docs/POLAR_CODE_MAINFLOW_20260327.md`. [repo-observed]
  - `docs/LATEST_RESULTS_20260327.md`. [repo-observed]
  - `docs/ROUTE_A_FORMAL_VERIFICATION_20260410.md`. [repo-observed]
  - `docs/ROUTE_A_BIT_PLANE_INTERFACE_20260414.md`. [repo-observed]
  - `docs/ROUTE_A_CORRECTNESS_BASELINE_20260410.md`. [repo-observed]
  - `docs/archived_studies/routeB_lite/`. [repo-observed]
- Main experiment entrypoints:
  - `experiments/run_e2e_pipeline.py`. [repo-observed]
  - `experiments/run_real_polar_max_pie.py`. [repo-observed]
  - `experiments/run_golden_sweep_driver.py`. [repo-observed]
  - `experiments/run_golden_sweep_four_datasets.py`. [repo-observed]
- Source packages:
  - `src/qkd_io/ttbin_pipeline.py`. [repo-observed]
  - `src/workflow/coarse_grain_joint.py`. [repo-observed]
  - `src/workflow/export_joint_sequence_sidecar.py`. [repo-observed]
  - `src/workflow/llr_from_joint.py`. [repo-observed]
  - `src/reconciliation/real_polar_sc_rescue.py`. [repo-observed]
  - `src/reconciliation/cpp_scl_wrapper.py`. [repo-observed]
  - `src/reconciliation/verification.py`. [repo-observed]
  - `src/reconciliation/run_nbldpc_demo_point.py`. [repo-observed]
- ASENoise tools:
  - `tools/asenoise/export_ttbin_cross_correlation.py`. [repo-observed]
  - `tools/asenoise/run_asenoise_type0_corrected_subset.py`. [repo-observed]
  - `tools/asenoise/run_asenoise_routeA_replay.py`. [repo-observed]
  - `tools/asenoise/run_asenoise_type0_jti_dense.py`. [repo-observed]
  - `tools/asenoise/README_ASENOISE.md`. [repo-observed]
- Security report tools:
  - `tools/security_reports/_security_round_common.py`. [repo-observed]
  - `tools/security_reports/_security_calibrated_common.py`. [repo-observed]
  - `tools/security_reports/_security_audit_common.py`. [repo-observed]
  - `tools/security_reports/_longrun_common.py`. [repo-observed]
  - `tools/security_reports/round2_build_finite_key_audit_table.py`. [repo-observed]
  - `tools/security_reports/round2_build_actual_ir_finite_key_shadow.py`. [repo-observed]
  - `tools/security_reports/round2_build_security_round2_summary.py`. [repo-observed]
  - `tools/security_reports/longrun_build_finite_key_audit_table.py`. [repo-observed]
  - `tools/security_reports/longrun_build_security_master_table.py`. [repo-observed]
  - `tools/security_reports/build_security_calibrated_summary.py`. [repo-observed]
- Diagnostics and probes:
  - `tools/diagnostics/`. [repo-observed]
  - Examples include `run_fixed_threshold_probe.py`, `run_fixed_threshold_bw_probe.py`, `run_conservative_security_shadow.py`, `audit_security_model_lineage.py`, and `compare_processing_rule_versions.py`. [repo-observed]
- Archived studies:
  - `tools/archive/routeB_lite/`. [repo-observed]
  - `docs/archived_studies/routeB_lite/`. [repo-observed]
- Pipelines:
  - `pipelines/current/`. [repo-observed]
  - `pipelines/archive/`. [repo-observed]
- Local artifact directories:
  - `results/` exists locally and is ignored by git. [repo-observed]
  - `workspace/` exists locally and is ignored by git. [repo-observed]
  - `analysis/mentor_progress_pack/` contains analysis helper scripts and generated cache was observed. [repo-observed]

## 3. Execution Environment

- Expected OS: WSL/POSIX is the target default for future harness generation. Windows PowerShell was used historically during local development. [memory-derived]
- Expected Python/MATLAB/Octave/other runtime:
  - Python runtime is required. [repo-observed]
  - `requirements.txt` lists `numpy`, `pandas`, `numba`, and `tqdm`. [repo-observed]
  - `.ttbin` ingestion may require the external `TimeTagger` Python module/runtime; this is not listed in `requirements.txt`. [memory-derived]
  - MATLAB/Octave requirements are not confirmed from the scanned files. [uncertain]
- Known environment constraints:
  - Large raw timing files and result artifacts are not source-controlled. [repo-observed]
  - Full E2E, Polar, and Route A replay commands can be long-running. [memory-derived]
  - `results/`, `workspace/`, cache files, and large binary/scientific data formats are ignored by `.gitignore`. [repo-observed]
- WSL migration notes:
  - Use POSIX-relative paths from the repository root in harness files. [repo-observed]
  - Do not embed local Windows absolute paths as runnable defaults. [memory-derived]
  - Historical Windows paths may appear in existing docs; treat them as legacy Windows paths, not WSL execution paths. [repo-observed]

## 4. Main Workflows

### Data Preprocessing / E2E Extraction

- entrypoint: `experiments/run_e2e_pipeline.py`. [repo-observed]
- input: `.ttbin` timing file, dimensions via `--dims`, bin widths via `--bws`, optional TTBin channel overrides and alignment flags. [repo-observed]
- output: E2E output root with temporary grid/source tables such as `_tmp_grid_table.csv` and `_tmp_src_table.csv`, sidecars, and diagnostics. [repo-observed]
- safe smoke command: `python experiments/run_e2e_pipeline.py --help`. [repo-observed]
- heavy command, if known: `python experiments/run_e2e_pipeline.py --ttbin <head.ttbin> --skip-polar --force-align --out-root <e2e_out> --dims <dims> --bws <bws>`. [repo-observed]
- do-not-run-by-default commands: Any command using large `.ttbin` data, many dimensions/bin widths, high `--jobs`, or full ASENoise batch data roots. [memory-derived]

### Polar Evaluation

- entrypoint: `experiments/run_real_polar_max_pie.py`. [repo-observed]
- input: `--grid-table`, `--in-csv`, optional `--only-points`, Polar code length `--N`, frame count `--frames`, visibility `--visibility`, and decoder controls. [repo-observed]
- output: Polar result CSV from `--out-csv`, plus diagnostic/layer CSVs written by the script. [repo-observed]
- safe smoke command: `python experiments/run_real_polar_max_pie.py --help`. [repo-observed]
- heavy command, if known: `python experiments/run_real_polar_max_pie.py --grid-table <e2e_out>/_tmp_grid_table.csv --in-csv <e2e_out>/_tmp_src_table.csv --out-csv <polar_out>/polar_e2e_results.csv --prefer-sidecar-map-ser`. [repo-observed]
- do-not-run-by-default commands: Full-grid Polar runs with many points, high `--jobs`, or result overwrite behavior. [memory-derived]

### ASENoise Cross-Correlation / JTI / Corrected Subset

- entrypoint: `tools/asenoise/export_ttbin_cross_correlation.py`. [repo-observed]
- input: `.ttbin`, channel args `--ch-a` / `--ch-b`, or `--auto-channels`; optional `--auto-align`. [repo-observed]
- output: cross-correlation CSV from `--out-csv`, optional summary JSON from `--out-json`. [repo-observed]
- safe smoke command: `python tools/asenoise/export_ttbin_cross_correlation.py --help`. [repo-observed]
- heavy command, if known: any command that reads real `.ttbin` acquisition data. [memory-derived]
- do-not-run-by-default commands: ASENoise batch commands over full raw data roots. [memory-derived]

- entrypoint: `tools/asenoise/run_asenoise_type0_corrected_subset.py`. [repo-observed]
- input: ASENoise data root, dimensions, bin widths, workers/jobs, dataset filter, overwrite flag. [repo-observed]
- output: Per-dataset E2E/Polar/security directories and aggregate manifest/master files. [repo-observed]
- safe smoke command: `python tools/asenoise/run_asenoise_type0_corrected_subset.py --help`. [repo-observed]
- heavy command, if known: Corrected ASENoise subset rerun over all datasets. [memory-derived]
- do-not-run-by-default commands: full ASENoise rerun with high `--workers` / `--jobs` or `--overwrite`. [memory-derived]

### Route A Actual Replay

- entrypoint: `tools/asenoise/run_asenoise_routeA_replay.py`. [repo-observed]
- input: subcommands including `estimate`, `replay`, `compare`, and `finalize-main`; source timestamp or explicit CSV inputs. [repo-observed]
- output: Route A estimate/replay master tables, comparison tables, and finalized main CSV with `PIE_main`, `SKR_main_bps`, and `main_result_source`. [repo-observed]
- safe smoke command: `python tools/asenoise/run_asenoise_routeA_replay.py --help`. [repo-observed]
- heavy command, if known: `python tools/asenoise/run_asenoise_routeA_replay.py replay --mode full --timestamp <stamp>`. [repo-observed]
- do-not-run-by-default commands: Full replay, high shard/worker counts, and any `--overwrite` replay run. [memory-derived]

### Security Report / Table Generation

- entrypoint: `tools/security_reports/round2_build_finite_key_audit_table.py`. [repo-observed]
- input: `--input-dirs`, `--franson-visibility`, `--eps-sec`, `--eps-cor`, `--output-dir`. [repo-observed]
- output: `finite_key_audit_point_table.csv`. [repo-observed]
- safe smoke command: `python tools/security_reports/round2_build_finite_key_audit_table.py --help`. [repo-observed]
- heavy command, if known: finite-key aggregation over large actual-IR result directories. [memory-derived]
- do-not-run-by-default commands: overwrite runs targeting authoritative result directories. [memory-derived]

- entrypoint: `tools/security_reports/longrun_build_security_master_table.py`. [repo-observed]
- input: `--actual-ir-dir`, `--beta-baseline-dir`, optional `--performance-proxy-input-dirs`, `--output-dir`. [repo-observed]
- output: security master table with final reporting semantics. [repo-observed]
- safe smoke command: `python tools/security_reports/longrun_build_security_master_table.py --help`. [repo-observed]
- heavy command, if known: full longrun master table construction over authoritative replay outputs. [memory-derived]
- do-not-run-by-default commands: commands with `--overwrite` against current authoritative output roots. [memory-derived]

### Plotting / Analysis

- entrypoint: `analysis/mentor_progress_pack/plot_progress_evidence.py`. [repo-observed]
- input: progress-pack analysis data files. [uncertain]
- output: plots or evidence artifacts. [uncertain]
- safe smoke command: `python analysis/mentor_progress_pack/plot_progress_evidence.py --help` if the script implements argparse. [uncertain]
- heavy command, if known: none confirmed. [uncertain]
- do-not-run-by-default commands: any analysis command writing into tracked docs or unversioned results without an explicit new output directory. [memory-derived]

## 5. Data and Result Policy

- raw data directories:
  - Raw `.ttbin` timing data is external and must not be committed. [repo-observed]
  - ASENoise raw data was historically under a local Windows directory; treat that location only as a legacy Windows path, not a portable execution path. [memory-derived]
- result/output directories:
  - `results/` is local artifact storage and ignored by git. [repo-observed]
  - `workspace/` is local artifact storage and ignored by git. [repo-observed]
  - `logs/`, `tmp/`, and `_tmp*/` are ignored by git. [repo-observed]
- checkpoint directories:
  - No model checkpoint directory was confirmed in the scanned tree. [uncertain]
  - Large checkpoint-like formats `*.pkl` and `*.joblib` are ignored. [repo-observed]
- files/directories agents must not overwrite:
  - Raw `.ttbin` data. [repo-observed]
  - Authoritative result directories documented in `docs/RESULTS_MANIFEST_20260427.md`. [repo-observed]
  - Any external raw-data root. [memory-derived]
  - Existing `results/authoritative/` contents unless the user explicitly requests a controlled rerun. [repo-observed]
  - Existing finalized ASENoise Route A master CSVs; use new timestamped outputs instead. [memory-derived]
- preferred new-output naming convention:
  - Use a new explicit output root under ignored local artifact storage. [repo-observed]
  - Prefer timestamped output names for new ASENoise and Route A runs. [repo-observed]
  - For WSL harnesses, use relative paths such as `results/<new_run_name>` or `outputs/<new_run_name>` only when the directory is ignored and user-approved. [memory-derived]

## 6. Schema and Interface Contract

- CSV columns that must not be silently changed:
  - Main reporting: `PIE_main`, `SKR_main_bps`, `main_result_source`. [repo-observed]
  - Actual-IR finite-key source columns: `PIE_secure_actual_ir`, `SKR_secure_actual_ir_bps`. [repo-observed]
  - Diagnostic/proxy columns: `PIE_practical`, `SKR_measured_bps`, `PIE_raw`, `PIE_clipped`. [repo-observed]
  - Common point keys: `dimension`, `bin_width_ps`, `loss_db`, `dataset_label`, `noise`. [repo-observed]
  - Security/audit fields observed in docs/code: `epsilon_EC_bound_formula_tag`, `leak_EC_source_tag`, `actual_coverage_tag`, `DeltaFK_calibrated`, `chi_E_calibrated`. [repo-observed]
  - Cross-correlation output columns: `lag_center_ps`, `lag_left_ps`, `lag_right_ps`, `count`, `count_rate_hz`. [repo-observed]
  - Replay/index filenames imply stable tables: `replay_index_point_table.csv`, `replay_index_layer_table.csv`, `actual_ir_block_table.csv`, `actual_ir_point_table.csv`. [repo-observed]
- JSON/YAML keys:
  - Cross-correlation optional summary JSON exists, but exact stable keys were not fully audited. [uncertain]
  - ASENoise run manifests exist historically, but exact stable keys were not fully audited. [uncertain]
- CLI arguments that must not be silently renamed:
  - E2E: `--ttbin`, `--dims`, `--bws`, `--force-align`, `--grid-table`, `--out-root`, `--jobs`, `--N`, `--frames`, `--visibility`, `--disable-scl`, `--acq-time`, `--skip-polar`. [repo-observed]
  - Polar: `--jobs`, `--N`, `--frames`, `--fer-thresh`, `--sc-margin`, `--scl-margins`, `--scl-batch`, `--seed`, `--visibility`, `--disable-scl`, `--in-csv`, `--grid-table`, `--out-csv`, `--only-points`, `--prefer-sidecar-map-ser`. [repo-observed]
  - ASENoise cross-correlation: `--ttbin`, `--ch-a`, `--ch-b`, `--auto-channels`, `--auto-align`, `--center-lag-ps`, `--align-search-range-ps`, `--align-bin-width-ps`, `--bin-width-ps`, `--max-lag-ps`, `--chunk-size`, `--include-non-timetags`, `--out-csv`, `--out-json`. [repo-observed]
  - ASENoise batch: `--data-root`, `--dims`, `--bws`, `--workers`, `--jobs`, `--timestamp`, `--datasets`, `--overwrite`. [repo-observed]
  - Route A replay: subcommands `estimate`, `replay`, `compare`, `finalize-main`; key args include `--source-timestamp`, `--input-csv`, `--timestamp`, `--mode`, `--shards`, `--workers`, `--backup`. [repo-observed]
  - Route A/security: `--input-dirs`, `--actual-ir-dir`, `--beta-baseline-dir`, `--performance-proxy-input-dirs`, `--output-dir`, `--franson-visibility`, `--eps-sec`, `--eps-cor`, `--overwrite`. [repo-observed]
- config keys:
  - No central YAML/TOML config file was observed. [repo-observed]
  - Constants in scripts such as default dimensions, bin widths, visibility, epsilon budgets, and worker counts are part of scientific behavior and should not be changed silently. [repo-observed]
- function signatures:
  - Internal function signatures were not fully audited. [uncertain]
  - Avoid changing public functions in `src/qkd_io`, `src/workflow`, and `src/reconciliation` without tests and explicit user request. [memory-derived]
- output file naming conventions:
  - E2E temporary tables: `_tmp_grid_table.csv`, `_tmp_src_table.csv`. [repo-observed]
  - Polar output: `polar_e2e_results.csv` when following current docs. [repo-observed]
  - Security outputs: `finite_key_audit_point_table.csv`, `actual_ir_finite_key_point_table.csv`, `round2_security_master_table.csv`, `security_calibrated_master_table.csv`, `cross_loss_security_master_table.csv`. [repo-observed]
  - ASENoise Route A comparison/finalization outputs include `routeA_actual_vs_shadow_point_table.csv` and master CSVs. [repo-observed]

## 7. Baseline and Scientific Semantics

- baseline algorithms:
  - Mainline uses Polar-code information reconciliation and Route A actual-IR finite-key accounting. [repo-observed]
  - Route B-lite is archived and not a default baseline. [repo-observed]
  - Beta-baseline outputs are comparison-only. [repo-observed]
- current assumptions:
  - Default reporting source is `actual_ir_finite_key`. [repo-observed]
  - `PIE_main` and `SKR_main_bps` are the reporting line. [repo-observed]
  - `PIE_practical` and `SKR_measured_bps` are diagnostics/proxies only. [repo-observed]
  - Franson visibility defaults appear as `0.95` in security and Polar commands. [repo-observed]
  - Niu 2016 strict proof instantiation is not supported by current observables. [repo-observed]
- high-risk variables:
  - Detector channel IDs and auto-alignment behavior. [memory-derived]
  - `dimension` and `bin_width_ps`. [repo-observed]
  - Polar code length `--N`, frame count `--frames`, decoder mode, SCL settings, and visibility. [repo-observed]
  - `franson_visibility`, `eps-sec`, `eps-cor`, finite-key correction terms, and verification tag bits. [repo-observed]
  - `loss_db`, `dataset_label`, and `noise` semantics in master tables. [repo-observed]
- known coupling/confounding factors:
  - Timing alignment affects cross-correlation, JTI construction, symbol mapping, and downstream Polar/security results. [memory-derived]
  - Sidecar map serialization and mapping sanity affect actual replay. [repo-observed]
  - Actual IR replay leakage and verification/correctness accounting affect final `PIE_main` / `SKR_main_bps`. [repo-observed]
  - Shadow or estimate-only outputs can look plausible but are not the default reporting line. [repo-observed]
- metrics that must preserve meaning:
  - `PIE_main`: main reportable PIE from actual-IR finite-key line. [repo-observed]
  - `SKR_main_bps`: main reportable secure key rate from actual-IR finite-key line. [repo-observed]
  - `PIE_secure_actual_ir` and `SKR_secure_actual_ir_bps`: source security metrics for main reporting. [repo-observed]
  - `PIE_practical` and `SKR_measured_bps`: performance diagnostics only. [repo-observed]
  - `raw_ser`, `near_neighbor_frac`, `n_pairs_actual`, and frame diagnostics are diagnostic context, not final security metrics. [repo-observed]

## 8. Known Issues and Fragile Points

- path issues:
  - Historical docs contain Windows absolute paths; do not copy them into WSL harnesses as executable defaults. [repo-observed]
  - Old root-level `tools/routeB_*`, `tools/round2_*`, and `tools/run_asenoise_*` wrappers are intentionally absent. [repo-observed]
  - `results/` and `workspace/` are ignored local artifact directories and should not be assumed present in a fresh clone. [repo-observed]
- environment issues:
  - `TimeTagger` may be required for `.ttbin` workflows but is not listed in `requirements.txt`. [memory-derived]
  - PowerShell wildcard behavior differs from POSIX shells for `python -m py_compile *.py`; WSL harnesses should use POSIX-safe commands. [memory-derived]
  - Python cache directories were observed locally; harnesses should ignore/remove them, not commit them. [repo-observed]
- data format issues:
  - `.ttbin` files are large external raw data and not portable. [repo-observed]
  - Sidecar tables and map serialization are part of downstream correctness; do not regenerate them in-place unless explicitly requested. [memory-derived]
  - CSV column names are part of the interface contract. [repo-observed]
- numerical/scientific interpretation risks:
  - Do not report proxy/shadow/estimate metrics as final secure results. [repo-observed]
  - Do not change Franson visibility, epsilon budgets, leakage accounting, or verification tag assumptions without recording the scientific reason. [repo-observed]
  - Route B-lite showed unstable/local gains and should not be folded into mainline by default. [repo-observed]
- long-running commands:
  - Full E2E extraction over `.ttbin` data can be long-running. [memory-derived]
  - Full Polar grid evaluation can be long-running. [memory-derived]
  - Full Route A actual replay can run for many hours depending on dataset size and worker count. [memory-derived]

## 9. Agent Operating Constraints

- Use minimal patches only. [memory-derived]
- Do not perform broad refactors without explicit user request. [memory-derived]
- Do not modify raw data. [memory-derived]
- Do not overwrite existing results. [memory-derived]
- Do not run full experiments by default. [memory-derived]
- Do not change baseline scientific semantics. [repo-observed]
- Do not change CSV schemas, CLI arguments, JSON keys, function signatures, or output file naming conventions unless explicitly requested. [memory-derived]
- Default to WSL/POSIX relative paths in new harness files. [memory-derived]
- Do not reintroduce compatibility wrappers for old moved paths unless explicitly requested. [repo-observed]
- Do not commit `results/`, `workspace/`, raw data, cache files, checkpoints, or large scientific data formats. [repo-observed]
- Prefer safe smoke checks such as `--help`, `python -m py_compile`, and narrowly scoped dry-run-style commands. [memory-derived]

## 10. Unknowns To Verify

- Confirm in the WSL clone whether `TimeTagger` is installed or must be provided externally. [uncertain]
- Confirm whether any C++/SCL decoder binaries or build steps are required by `src/reconciliation/cpp_scl_wrapper.py`. [uncertain]
- Confirm exact `run_e2e_pipeline.py` TTBin channel override argument names before writing executable harness commands. [uncertain]
- Confirm whether `experiments/run_golden_sweep_driver.py` and `experiments/run_golden_sweep_four_datasets.py` remain current or historical. [uncertain]
- Confirm exact JSON manifest keys for ASENoise and cross-correlation summaries before schema-locking them. [uncertain]
- Confirm whether `analysis/mentor_progress_pack/` should be treated as maintained analysis or historical local tooling. [uncertain]
- Confirm whether local `results/authoritative/` exists in the WSL copy; it is ignored by git and may not be present after clone. [repo-observed]
- Confirm whether `workspace/override_points` archive artifacts are available in WSL if demo helper tests need them. [uncertain]
- Confirm test coverage and any preferred smoke tests beyond `py_compile`. [uncertain]

## 11. Recommended Harness Files To Generate

- `AGENTS.md`: Repository operating rules for future agents, with WSL/POSIX path defaults and no-result-overwrite policy. [memory-derived]
- `CURRENT_TASK.md`: A short, mutable task state file for the current Roo Code objective. [memory-derived]
- `RUN_COMMANDS.md`: Curated smoke commands, safe validation commands, and explicitly marked heavy commands. [memory-derived]
- `REVIEW_CHECKLIST.md`: Checklist for schema stability, scientific semantics, no raw/result writes, and no accidental large-file staging. [memory-derived]
- `AGENT_HANDOFF.md`: Human-readable summary of the last completed task, open risks, changed files, and next recommended verification steps. [memory-derived]
