# Project Classification 2026-04-27

## Current Partitions

- `mainline`: raw timing input through E2E extraction, symbol mapping, Polar IR replay, and Route A finite-key accounting.
- `ASENoise Type0`: ASENoise-specific channel correction, JTI/export utilities, and Route A actual replay reporting.
- `security_reports / Route A`: actual-IR replay, finite-key audit, and security master table builders.
- `Route B-lite archived study`: completed side study for richer binary channel / LLR modeling.
- `diagnostics / probes`: processing-rule, threshold, frame-span, root-cause, and proxy-security diagnostics.
- `pipelines`: current reproducible runners plus archived historical batch reruns.
- `results`: local result artifacts grouped as authoritative, supporting, diagnostics, and archive.
- `workspace historical artifacts`: old override-point run artifacts, not source-maintained mainline inputs.

## Current Mainline

`ttbin / timing input`
-> `qkd_io` parsing
-> E2E extraction
-> symbol mapping / sidecars
-> Polar IR actual replay
-> Route A finite-key security accounting
-> `PIE_main` / `SKR_main_bps`

## Main Result Semantics

Default reporting columns:

- `PIE_main`
- `SKR_main_bps`
- `main_result_source=actual_ir_finite_key`

The following are diagnostics or proxies only and must not be used as the default reporting line:

- `PIE_practical`
- `SKR_measured_bps`
- `PIE_raw`
- `PIE_clipped`
- estimate-only PIE
- shadow-only SKR
- proxy SKR

## Archived And Diagnostic Code

- `tools/diagnostics/` contains development diagnostics and probes. These scripts do not define default security results.
- `run_conservative_security_shadow.py` is historical/proxy security analysis and is not a default main result path.
- `tools/archive/routeB_lite/` and `docs/archived_studies/routeB_lite/` preserve Route B-lite as an archived study.

## Workspace Handling

`workspace/override_points` was migrated to `results/archive/workspace_override_points/`. Current mainline scripts do not depend on the old workspace path; the remaining demo helper now reads the archived fixture location explicitly.

## Results Handling

`results/` is local artifact storage and is ignored by git. Authority is determined by `docs/RESULTS_MANIFEST_20260427.md`, not by historical `_tmp_*` directory names.
