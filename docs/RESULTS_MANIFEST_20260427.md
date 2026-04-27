# Results Manifest 2026-04-27

`results/` is local artifact storage and is not tracked by git. This manifest defines which result directories are current.

## Authoritative

- `results/authoritative/e2e_*_fullgrid_pairing_v2_candidate*`
- `results/authoritative/_tmp_longrun_fresh_rerun`
- `results/authoritative/_tmp_minrerun_stageC_security_20dB`
- `results/authoritative/_tmp_minrerun_stageD_cross_loss`
- `results/authoritative/_tmp_routeA_correctness_formal_stageD_cross_loss`
- Current ASENoise Type0 Route A master results under the raw data root: `D:\Data\Raw Data\ASENoise_Type0\asenoise_type0_routeA_actual_replay_full_master_20260427_154500.csv`

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
