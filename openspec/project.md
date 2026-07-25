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
