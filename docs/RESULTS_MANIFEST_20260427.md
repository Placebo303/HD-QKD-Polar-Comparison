# Results Manifest 2026-04-27

`results/` is local artifact storage and is not tracked by git. This manifest defines which result directories are current.

The result artifacts are currently local-only and are not downloadable from this
Git repository. A recipient must obtain the `results/authoritative/` directory
through an approved file-transfer channel and then verify it against
`docs/AUTHORITATIVE_RESULTS_CHECKSUMS.json`.

## Authoritative

- `results/authoritative/e2e_*_fullgrid_pairing_v2_candidate*`
- `results/authoritative/_tmp_longrun_fresh_rerun`
- `results/authoritative/_tmp_minrerun_stageC_security_20dB`
- `results/authoritative/_tmp_minrerun_stageD_cross_loss`
- `results/authoritative/_tmp_routeA_correctness_formal_stageD_cross_loss`
- Current ASENoise Type0 Route A master result is external to the repository.
  Its historical source location remains provenance in prior run records; do not
  treat that machine-specific path as a runnable default. It is not covered by
  the repository-local authoritative checksum manifest.

## Supporting

- Replay indexes, stage summaries, and sidecar-backed candidate packs that directly support the authoritative results.
- `results/supporting/real_sequences`
- `results/supporting/e2e_pipeline_*` when used only to support historical comparison.

## Diagnostics

- Processing-rule experiments.
- Threshold probes.
- Occupancy/frame diagnostics.
- BW/d root-cause diagnostics.
- R3B tradeoff experiments.

## Historical

- Route B-lite result packs.
- Old longrun/minrerun stages superseded by authoritative results.
- Historical workspace override-point artifacts.

## Disposable

- Smoke runs.
- Quick checks.
- Bad CSV tests.
- Root-level temporary layer-failure CSVs and obsolete one-off outputs.

No authoritative result should be deleted during cleanup. Historical and disposable results may be archived or moved out of the working copy after review.

## Integrity And Transfer

The tracked checksum file contains one deterministic tree SHA-256 per
authoritative pack. Each tree digest covers every relative file path, file size,
and file SHA-256 in the pack.

Generate or refresh after an intentional authoritative result change:

```powershell
python tools\verify_authoritative_results.py `
  --write docs\AUTHORITATIVE_RESULTS_CHECKSUMS.json
```

Verify after copying a result set:

```powershell
python tools\verify_authoritative_results.py `
  --verify docs\AUTHORITATIVE_RESULTS_CHECKSUMS.json
```

On WSL or a machine where results are stored elsewhere, set
`PROJECT_RESULTS_ROOT` or pass `--root <path-to-authoritative>`.

The Git repository deliberately does not prescribe a cloud download URL because
no approved artifact host is configured. Publishing these data requires a
separate storage/access decision; do not invent or silently upload a result pack.
