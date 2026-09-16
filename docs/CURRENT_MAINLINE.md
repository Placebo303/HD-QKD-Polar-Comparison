# Current Mainline

## Formal-IR research mainline — current route ledger (through D7-D + BP provenance interface)

This document is **status, not authorization**. The active gate and accepted
cycle documents outrank aggregate checkbox counts; stale historical checkboxes
are bookkeeping, not execution authorization.

The strict first principle is high-performance error correction for actual
HD-QKD data. The frozen Polar line below is a comparison baseline; active
algorithm work lives under `comparison_bench/`, OpenSpec, and the NB-LDPC
research cycle documents.

Current route ledger (each item is a bounded conclusion already accepted in its
own cycle document; no new claim is added here):

1. **D5 — fixed rate-mother path stopped within tested scope.** The two-layer
   rate-mother BP path is accepted as stopped for the tested configuration.
2. **D6 — graph/mother successor structurally blocked.** The graph/mother A2
   path is structurally blocked; R1d Option C is frozen but optional/paused
   (`PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE`) and is not a
   mainline gate.
3. **D7-A — decoder certification PASS.**
4. **D7-B — hard-decision easy region observed**, with RSS/belief limitations
   recorded; no belief-calibration claim.
5. **D7-C — bounded bidirectional dependence accepted** as a diagnostic; it
   does not prove that alternating/joint BP can bootstrap.
6. **D7-D — schedule effect inconclusive** (`D7_D_SCHEDULE_EFFECT_INCONCLUSIVE`,
   accepted as `D7_D_RESULT_ACCEPTED_SCHEDULE_EFFECT_INCONCLUSIVE`); no
   schedule-superiority claim.
7. **Active gate — D7-E provenance-safe cross-layer discriminator frozen
   awaiting explicit authorization.** BP provenance Alternative A is
   implemented and dual-reviewed
   (`D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_PASS`,
   `D7_BP_INTERFACE_READINESS_REVIEW_PASS`); D7-E is frozen at `f82804f6`
   with implementation review `D7_E_IMPLEMENTATION_REVIEW_PASS` and
   Pre-EXECUTE `D7_E_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`
   recorded — nothing executed, no UUID, no result root. D6 R1d
   BP-provenance compat is repaired and re-reviewed but R1d stays
   optional/paused; G1/G2 remain unauthorized.
8. **After D7-E is frozen and authorized**, run the provenance-safe cross-layer
   mechanism discriminator before any further cross-layer APP work; that run
   needs its own prereg/packet and explicit Pre-EXECUTE.
9. **Only then** consider dimension/bandwidth expansion; expansion stays gated,
   and for more than two layers a separate mathematical/leakage contract is
   required.

## NB-Polar successor boundary (2026-09-11)

An independent native q-ary NB-Polar plan is now initialized in the sibling
worktree D:\Code\HD-QKD_Polar_Comparison-nbpolar. The canonical documents
are docs/nbpolar/DOCUMENT_INDEX.md and OpenSpec change
formal-ir-nbpolar-mvp. This is a plan candidate only: there is no production
decoder, real-data execution, result root, or qualification claim.

The old hybrid APP-transfer draft is archived under
openspec/changes/archive/2026-09-11-formal-ir-future-nbpolar-app-transfer-superseded/.
The active Comparison route remains D7-E; NB-Polar planning neither changes
nor authorizes D7-E, D7-D, D7-C, D6, or D5 work.

Earlier bounded V-series states superseded by the ledger above: V34 matched
empirical-P fixed-packet bounded failure (ER1 accepted); V35R1 closed only the
tested hand-designed NB configuration
(`NO_NB_CANDIDATE_FOR_TESTED_HAND_DESIGNED_CONFIGURATION`,
`PROTOCOL_PARTIAL_A4_NOT_EXECUTED`); V36 showed a real exploratory residual
decrease with no exact recovery and no accepted finite-graph advance.

Use `docs/research-cycle-sop.md` for the next plan -> ChatGPT review -> OpenCode
implementation -> result-review loop. No successor or formal run is currently
authorized by this status document.

## Reporting Rule

The default reporting line is Route A actual-IR finite-key:

- `PIE_main`
- `SKR_main_bps`
- `main_result_source=actual_ir_finite_key`

`PIE_practical`, `SKR_measured_bps`, shadow-only outputs, and estimate-only outputs are diagnostics.

## Recommended Entrypoints

Front half:

```powershell
python experiments/run_e2e_pipeline.py --ttbin <head.ttbin> --skip-polar --force-align --out-root <e2e_out>
python experiments/run_real_polar_max_pie.py --grid-table <e2e_out>\_tmp_grid_table.csv --in-csv <e2e_out>\_tmp_src_table.csv --out-csv <polar_out>\polar_e2e_results.csv --prefer-sidecar-map-ser
```

ASENoise Type0:

```powershell
python tools/asenoise/run_asenoise_type0_corrected_subset.py --timestamp <stamp>
python tools/asenoise/run_asenoise_routeA_replay.py replay --mode full --timestamp <stamp>
python tools/asenoise/run_asenoise_routeA_replay.py finalize-main --input-csv <full_master.csv> --backup
```

Security reports / Route A:

```powershell
python tools/security_reports/round2_build_finite_key_audit_table.py --input-dirs <candidate_dir> <actual_ir_dir> --output-dir <stage2_security> --overwrite
python tools/security_reports/round2_build_actual_ir_finite_key_shadow.py --output-dir <stage2_security> --overwrite
python tools/security_reports/round2_build_security_round2_summary.py --actual-ir-dir <stage2_security> --beta-baseline-dir <stage2_security> --output-dir <stage2_security> --overwrite
```

Current pipelines live in `pipelines/current/`. Historical batch scripts live in `pipelines/archive/` and are not maintained as default commands.

## Archived Studies

Route B-lite is an archived side study. It tested whether richer binary channel / LLR modeling should enter the mainline. The result was mixed and locally useful but not stable enough to replace Route A or to pollute the mainline. Its value is as evidence for future Route C / q-ary Polar discussions.

## Old Entrypoints

Old root-level `tools/routeB_*`, root `tools/round2_*`, and root `tools/run_asenoise_*` paths are intentionally not preserved as wrappers. Use the paths above.
