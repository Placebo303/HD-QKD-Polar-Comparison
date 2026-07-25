# High-Dimensional QKD Polar Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> **End-to-end HD-QKD Polar-code workflow for high-dimensional quantum key distribution with time-bin encoding and Polar code error correction.**

This repository contains the complete HD-QKD Polar-code workflow, including:
- Pairing/materialization from `.ttbin` (Swabian TimeTagger)
- Polar-based information reconciliation evaluation
- Actual-IR replay auditing
- Finite-key calibrated Zhong-like security aggregation
- Layered secure PIE (Photon Information Efficiency) accounting

## Installation

```bash
# Clone repository
git clone <repo-url>
cd HD-QKD_Polar_Release

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `numpy` | Array operations |
| `pandas` | Data processing |
| `scipy` | Scientific computing |
| `polar-code` | Polar code encoder/decoder |
| `yfinance` | Market data (for sample data) |

### TimeTagger Setup

For `.ttbin` file support, install Swabian TimeTagger Python bindings:

```bash
# After installing Swabian TimeTagger software:
python -c "import TimeTagger; print('TimeTagger available')"
```

## Minimal Example

```bash
# Quick start with sample data
python experiments/run_e2e_pipeline.py \
    --data-provider sample \
    --dims 256 \
    --bws 150 \
    --acq-time 0.1

# With real data
python experiments/run_e2e_pipeline.py \
    --ttbin "PATH_TO_YOUR_DATA.ttbin" \
    --dims 1024 \
    --bws 150 \
    --acq-time 0.1
```

Expected output: the script parses time-tags, performs frame synchronization, calls the Polar decoder, and reports Secure Key Rate (SKR) and Practical Information Efficiency (PIE).

## Parameter Explanation

### Core Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--dims` | 1024 | Number of time-bin dimensions. Higher = more information capacity |
| `--bws` | 150 | Bin width in picoseconds. Smaller = higher resolution |
| `--acq-time` | 0.1 | Acquisition time in seconds. Longer = more statistics |
| `--data-provider` | yfinance | Data source: `sample`, `yfinance`, `local`, `stooq` |
| `--ttbin` | None | Path to TimeTagger binary file |

### Advanced Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--skip-llm` | False | Skip LLM analysis (faster execution) |
| `--simulate` | False | Use simulated data |
| `--forward-run` | False | Enable forward evaluation mode |
| `--operator-gate` | False | Enable human-in-the-loop review |

### How to Choose Values

- **dims**: Start with 256 for testing, use 1024 for production results
- **bws**: 150ps is typical. Reduce to 100ps for high-resolution analysis
- **acq-time**: 0.1s for quick tests, 1.0s+ for publication-quality results

## Known Issues

### yfinance Cache Pollution

The yfinance library may cache stale data, causing "No trading days after decision_date" errors.

**Solution**:
```bash
# Clear yfinance cache
rm -rf data/.yfinance-cache

# Or use sample data provider
python experiments/run_e2e_pipeline.py --data-provider sample
```

### MultiIndex Column Drift

yfinance output may have MultiIndex columns that break downstream processing.

**Solution**: The pipeline automatically normalizes columns to `Open/High/Low/Close/Volume`. If you encounter issues, check `src/data/yfinance_client.py`.

### Deterministic Evaluation Date

Historical fixture runs auto-adjust to the latest fixture trading date. If evaluation fails, pass an explicit date:

```bash
python experiments/run_e2e_pipeline.py --evaluation-date 2024-06-06
```

## Current Status

As of 2026-03-27, the current reporting line is:
- `PRIMARY_REPORTING_MODE = actual_ir_finite_key`
- default main result columns: `PIE_main`, `SKR_main_bps`
- default main result source: `PIE_secure_actual_ir`, `SKR_secure_actual_ir_bps`
- `PIE_practical` and `SKR_measured_bps` are diagnostic performance proxies only
- `BETA_BASELINE_ROLE = comparison_only`
- `NIU_2016_STATUS = not_supported_by_current_observables`

The authoritative latest results are **not** the older `_tmp_longrun_stage*` directories.
Use these instead:
- fresh full rerun root: [results/authoritative/_tmp_longrun_fresh_rerun](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_longrun_fresh_rerun)
- refined frame-accounting pass: [results/authoritative/_tmp_minrerun_stageC_security_20dB](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_minrerun_stageC_security_20dB)
- refined cross-loss pack: [results/authoritative/_tmp_minrerun_stageD_cross_loss](/D:/Code/HD-QKD_Polar_Release/results/authoritative/_tmp_minrerun_stageD_cross_loss)

## Main Documents

- latest workflow and run method:
  - [docs/CURRENT_MAINLINE.md](/D:/Code/HD-QKD_Polar_Release/docs/CURRENT_MAINLINE.md)
  - [docs/PROJECT_CLASSIFICATION_20260427.md](/D:/Code/HD-QKD_Polar_Release/docs/PROJECT_CLASSIFICATION_20260427.md)
  - [docs/POLAR_CODE_MAINFLOW_20260327.md](/D:/Code/HD-QKD_Polar_Release/docs/POLAR_CODE_MAINFLOW_20260327.md)
- latest results and authoritative output paths:
  - [docs/RESULTS_MANIFEST_20260427.md](/D:/Code/HD-QKD_Polar_Release/docs/RESULTS_MANIFEST_20260427.md)
  - [docs/LATEST_RESULTS_20260327.md](/D:/Code/HD-QKD_Polar_Release/docs/LATEST_RESULTS_20260327.md)
- Route A correctness formalization:
  - [docs/ROUTE_A_FORMAL_VERIFICATION_20260410.md](/D:/Code/HD-QKD_Polar_Release/docs/ROUTE_A_FORMAL_VERIFICATION_20260410.md)
  - [docs/ROUTE_A_BIT_PLANE_INTERFACE_20260414.md](/D:/Code/HD-QKD_Polar_Release/docs/ROUTE_A_BIT_PLANE_INTERFACE_20260414.md)

Route A correctness formalization uses per-block universal-hash verification
for `epsilon_EC_bound` budgeting. This is not a strict Zhong 2015 or full Niu
2016 proof instantiation.
- Route B-lite error-model audit:
  - [docs/archived_studies/routeB_lite/README.md](/D:/Code/HD-QKD_Polar_Release/docs/archived_studies/routeB_lite/README.md)

Route B-lite is completed as a diagnostic/validation route. It ran B1 error
audit, B2 channel-model diagnostics, B3 subset LLR-only ablation, and full
20dB LLR-only validation. The conclusion is a useful but limited/partial
negative result: local bin-width-dependent signals exist, but there is no
stable, broadly applicable gain. Do not expand it or migrate it to the
mainline without a new plan.

## Quick Start

```bash
# Ensure you are in the root of the repository
python experiments/run_e2e_pipeline.py \
    --ttbin "PATH_TO_YOUR_DATA.ttbin" \
    --dims 1024 \
    --bws 150 \
    --acq-time 0.1
```

Expected output: the script parses time-tags, performs frame synchronization, calls the Polar decoder, and reports Secure Key Rate (SKR) and Practical Information Efficiency (PIE).

## Export ttbin Cross-Correlation CSV

To generate a CSV table for plotting the channel cross-correlation from a `.ttbin` file:

```bash
python tools/asenoise/export_ttbin_cross_correlation.py \
    --ttbin "PATH_TO_YOUR_DATA.ttbin" \
    --ch-a 1 \
    --ch-b 5 \
    --bin-width-ps 10 \
    --max-lag-ps 10000 \
    --out-csv results/cross_correlation.csv
```

The lag convention is `lag_ps = t_B - t_A`. The CSV columns are `lag_center_ps`, `lag_left_ps`, `lag_right_ps`, `count`, and `count_rate_hz`.

## Main Entry Points

Front half:
- [experiments/run_e2e_pipeline.py](/D:/Code/HD-QKD_Polar_Release/experiments/run_e2e_pipeline.py)
- [experiments/run_real_polar_max_pie.py](/D:/Code/HD-QKD_Polar_Release/experiments/run_real_polar_max_pie.py)

Replay / security:
- [pipelines/current/longrun_build_replay_index.py](/D:/Code/HD-QKD_Polar_Release/pipelines/current/longrun_build_replay_index.py)
- [pipelines/current/longrun_run_actual_ir_replay.py](/D:/Code/HD-QKD_Polar_Release/pipelines/current/longrun_run_actual_ir_replay.py)
- [tools/security_reports/longrun_build_finite_key_audit_table.py](/D:/Code/HD-QKD_Polar_Release/tools/security_reports/longrun_build_finite_key_audit_table.py)
- [tools/security_reports/longrun_build_security_master_table.py](/D:/Code/HD-QKD_Polar_Release/tools/security_reports/longrun_build_security_master_table.py)

Route B-lite:
Route B-lite has been archived under [tools/archive/routeB_lite](/D:/Code/HD-QKD_Polar_Release/tools/archive/routeB_lite) and [docs/archived_studies/routeB_lite](/D:/Code/HD-QKD_Polar_Release/docs/archived_studies/routeB_lite). It is not a mainline entry.

Refined frame-accounting pass:
The historical minrerun scripts are archived in [pipelines/archive](/D:/Code/HD-QKD_Polar_Release/pipelines/archive). Current recommended commands are listed in [docs/CURRENT_MAINLINE.md](/D:/Code/HD-QKD_Polar_Release/docs/CURRENT_MAINLINE.md).

## Recommended Usage

If you only need the current best result package, read the existing outputs and do not rerun the physics front half.

If you need to reproduce the current workflow from raw data, use the split boundary flow described in [docs/POLAR_CODE_MAINFLOW_20260327.md](/D:/Code/HD-QKD_Polar_Release/docs/POLAR_CODE_MAINFLOW_20260327.md):
1. extraction/materialization with `--skip-polar`
2. Polar evaluation from cached `_tmp_grid_table.csv` and `_tmp_src_table.csv`
3. actual-IR replay and security aggregation
4. refined frame-accounting rebuild

## License

MIT
