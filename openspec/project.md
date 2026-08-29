# OpenSpec Project Context

## Project: HD-QKD_Polar_Comparison

### Summary
Evaluate and compare Information Reconciliation (IR) methods for high-dimensional Quantum Key Distribution (QKD). The original Polar pipeline is a frozen baseline; `comparison_bench/` adds a non-invasive comparison layer.

### Tech Stack
- **Language**: Python 3
- **Core deps**: `numpy`, `pandas`, `numba`, `tqdm`
- **Optional deps**: `pyyaml`, `pyarrow`, `pytest`
- **Scientific domain**: QKD post-processing, IR, error correction codes

### Architecture
- **Frozen baseline**: `src/`, `experiments/`, `tools/` (original Polar pipeline — do not modify)
- **Comparison layer**: `comparison_bench/` (outer wrapper, reads Polar outputs, adds new baselines)
- **Data**: raw data external to repo; processed outputs under `results/` (read-only) and `comparison_bench/outputs_comparison/` (append-only)

### Key Constraints
- Original Polar code is frozen; only `comparison_bench/` is mutable
- Schema stability: CSV columns, config keys, CLI args, function signatures must not silently change (see AGENT_PROJECT_MEMORY.md §6)
- Scientific semantics: `beta_eff_empirical` must be derived, status values must be preserved, leakage comparisons require consistent decomposition
- Path discipline: prefer WSL/POSIX paths; legacy Windows paths are provenance only

### Known Risks
- Compiled Polar binaries (`src/reconciliation/cpp_polar/`) may be Windows-only
- Parquet output may fall back to pickle
- Long-running commands must not be run casually

### Release Strategy (polar-mainline vs Latest, 2026-08-29)

- **Branch mainline (Source of Truth)**: `polar-mainline` — L0 干净基线（`src/experiments/tools` 冻结，`results/` ignored，381 文件）。永不 merge `polar-v1.0-aggressive-adaptive`，仅 tag 同步（详见 `workspace/dual_repo_tidy_plan_20260829.md §5.5`）。
- **GitHub Latest (mature out-of-box)**: `polar-v1.0-aggressive-adaptive`（别名 `polar-v1.0-adaptive`，`--latest` 标记）。内容 = `aggressive 4×121（9.31/9.51/9.59/9.59 PIE max）` + `adaptive 72 候选（4×18 scan_*）` + `4×121 择优重跑（adaptive_v1/full_121_*_best）`；门冻结 `T0.5 point0.10/sc/max0 + G_scan 0.17m`。
- **Release checklist Step 2 tag**: `polar-v1.0-aggressive-adaptive`（取代旧 `polar-v1.0-aggressive`），`gh release create --latest`；校验 `isLatest=true`。
- **附件（Latest 必须含）**: `paper_grade_aggressive_v1_*.tar.gz` + `adaptive_v1_*.tar.gz`（全量 scan + full_121_best + _adaptive_vs_frozen*.csv）+ `gates_frozen.json`（含 T0.5 + auto_scan_v1）+ `four_loss_report.pdf` + `SHA256SUMS`。
- **L0 纯版**: `polar-mainline-v1.0` — GitHub **Pre-release** 次位（`--prerelease`），仅 `gates_frozen` + `README`，不含 tar，供审计对照；非 Latest。
- **README Quick Start**: 指向 `adaptive_v1` 开箱 `python tools/auto_ir_scan.py --help`（或 `--pool-root results/adaptive_v1 --workers max(2,cpu-2)`），非 L0 旧流水线。
