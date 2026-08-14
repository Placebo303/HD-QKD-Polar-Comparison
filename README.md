# High-Dimensional QKD Polar Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Research pipeline for high-dimensional QKD timing data, Polar-code information reconciliation, actual-IR replay, and finite-key security accounting.

## Current status

The default reporting line is:

```text
PRIMARY_REPORTING_MODE = actual_ir_reconciled_net_not_secure
PIE_main
SKR_main_bps
main_result_source = actual_ir_reconciled_net_not_secure
BETA_BASELINE_ROLE = comparison_only
NIU_2016_STATUS = not_supported_by_current_observables
```

`PIE_main` and `SKR_main_bps` are public-EC-only reconciled net metrics, not secret-key metrics. Route A correctness-side verification is formalized with per-block universal hashing. This is not a strict Zhong 2015 or full Niu 2016 proof instantiation.

Route B-lite is a completed archived study. Its LLR-only gains were local and unstable, so it is not part of the mainline.

See [AGENT_HANDOFF.md](AGENT_HANDOFF.md) for the current project state and [docs/CURRENT_MAINLINE.md](docs/CURRENT_MAINLINE.md) for maintained commands.

## Repository type and installation

This is a script repository, not an installable Python package. Run commands from the repository root.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Linux / WSL activation:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Additional runtime requirements:

- `.ttbin` ingestion requires the Swabian Instruments Time Tagger software and its `TimeTagger` Python module.
- The paper-grade path uses ordinary minimum-metric SCL; legacy CA-SCL remains comparison-only. The wrapper rebuilds the local C++17 library when needed and requires `g++`.
- `results/` and raw `.ttbin` data are not included in a fresh clone.

Verify the optional TimeTagger binding:

```powershell
python -c "import TimeTagger; print('TimeTagger available')"
```

## Main workflow

### 1. Extract and materialize timing data

Use a new output directory. The command reads real `.ttbin` data and may be long-running.

```powershell
python experiments\run_e2e_pipeline.py `
  --ttbin "PATH_TO_DATA.ttbin" `
  --dims "1024" `
  --bws "150" `
  --skip-polar `
  --force-align `
  --out-root "results\new_e2e_run"
```

`--acq-time` is retained only as a compatibility flag and is currently unused.

### 2. Run Polar evaluation from cached tables

```powershell
python experiments\run_real_polar_max_pie.py `
  --grid-table "results\new_e2e_run\_tmp_grid_table.csv" `
  --in-csv "results\new_e2e_run\_tmp_src_table.csv" `
  --out-csv "results\new_polar_run\polar_e2e_results.csv" `
  --prefer-sidecar-map-ser
```

### 3. Run Route A replay and security reporting

Current replay pipelines are under `pipelines/current/`. Security table builders are under `tools/security_reports/`.

```powershell
python pipelines\current\routeA_run_formal_cross_loss.py --help
python tools\security_reports\round2_build_finite_key_audit_table.py --help
```

Do not target an existing `results/authoritative/` directory with `--overwrite`.

## Cross-correlation export

```powershell
python tools\asenoise\export_ttbin_cross_correlation.py `
  --ttbin "PATH_TO_DATA.ttbin" `
  --ch-a 1 `
  --ch-b 5 `
  --bin-width-ps 10 `
  --max-lag-ps 10000 `
  --out-csv "results\cross_correlation.csv"
```

Lag convention: `lag_ps = t_B - t_A`.

## Result packs

`results/` is local artifact storage and is ignored by Git. Authority is defined by [docs/RESULTS_MANIFEST_20260427.md](docs/RESULTS_MANIFEST_20260427.md).

Current authoritative packs:

- `results/authoritative/_tmp_longrun_fresh_rerun`
- `results/authoritative/_tmp_minrerun_stageC_security_20dB`
- `results/authoritative/_tmp_minrerun_stageD_cross_loss`
- `results/authoritative/_tmp_routeA_correctness_formal_stageD_cross_loss`
- `results/authoritative/e2e_*_fullgrid_pairing_v2_candidate*`

Validate a transferred result set with:

```powershell
python tools\verify_authoritative_results.py --verify docs\AUTHORITATIVE_RESULTS_CHECKSUMS.json
```

## Layout

- `experiments/`: E2E and Polar entrypoints
- `src/`: timing, mapping, decoder, and verification code
- `pipelines/current/`: maintained replay pipelines
- `pipelines/archive/`: historical batch reruns
- `tools/security_reports/`: finite-key and reporting builders
- `tools/asenoise/`: ASENoise and cross-correlation tools
- `tools/diagnostics/`: non-authoritative diagnostics
- `tools/archive/routeB_lite/`: archived Route B-lite study
- `docs/`: result semantics, workflow, and scientific boundaries
- `tests/`: raw-data-free smoke tests

## Safe checks

```powershell
python -m unittest discover -s tests -v
python -m compileall -q src experiments pipelines tools analysis tests
```

These checks do not replace a raw-data E2E or full replay run.

## Key documents

- [Current mainline](docs/CURRENT_MAINLINE.md)
- [Project classification](docs/PROJECT_CLASSIFICATION_20260427.md)
- [Results manifest](docs/RESULTS_MANIFEST_20260427.md)
- [Results interpretation](docs/RESULTS_INTERPRETATION.md)
- [Security model](docs/SECURITY_MODEL.md)
- [Route A formal verification](docs/ROUTE_A_FORMAL_VERIFICATION_20260410.md)
- [Route A bit-plane interface](docs/ROUTE_A_BIT_PLANE_INTERFACE_20260414.md)
- [Archived Route B-lite summary](docs/archived_studies/routeB_lite/ROUTE_B_LITE_FINAL_SUMMARY_20260415.md)

## License

MIT
