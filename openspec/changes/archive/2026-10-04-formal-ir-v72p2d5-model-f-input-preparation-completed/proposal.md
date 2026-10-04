# Proposal: V72P2D5 Model-F input preparation (comparison-only, implement-only)

- Change: `formal-ir-v72p2d5-model-f-input-preparation`
- Predecessor: `v72p2d5-p0-g1-g2-production-path` (P0/G1/G2 candidate, BLOCKED on missing CAL-TRAIN counts) + `formal-ir-v72p2d5-gf32-rate-mother-plan` (R2_DV3, frozen lambda) + `formal-ir-v72p2d4-cal-gf32-model-rate-audit` (D4R2 nested-CV selection)
- Cycle: `V72P2D5-GF32-RATE-MOTHER`
- Lifecycle: `MODEL_F_INPUT_IMPLEMENTATION_CANDIDATE / READY_FOR_INDEPENDENT_REVIEW / EXECUTE_NOT_AUTHORIZED`
- Branch: `formal-ir-v72p1-addendum-clean`

## Goal

Provide the canonical full-CAL refit input for Model-F after the frozen lambda selection, without executing any real preparation, decoder, P0/G1/G2, or VAL read in this change.

## Why

D4R2 selected model F with `lambda*=137.3823795883264` via nested-CV (lambda+stability only). P0/G1/G2 are BLOCKED as `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`: the accepted input (D4R2 F-model CAL-TRAIN canonical counts `(1024,1024)` + `P(B)` marginal on frozen `CAL702..1725` TRAIN) has no committed in-repo artifact. No G0 toy, uniform, or random distribution may substitute. This change defines the artifact, the prepare/consume split, and the implement-only candidate.

## Statistical contract (frozen)

- Nested-CV only selects lambda+stability; after freeze, P0/G1/G2 canonical input is a refit from full `CAL702..1725`, NOT an average of 4 outer TRAIN counts, NOT a TEST concatenation.
- `counts_ab[a,b]=#CAL pairs Alice=a Bob=b`; `bob_counts[b]=sum_a counts_ab`; `p_b=bob/sum`; require counts shape `(1024,1024)` nonneg int sum `262144`, bob `(1024,)` == counts.sum(axis0), `p_b (1024,)` >=0 sum1 == marginal/262144.
- P0/G1/G2 = matched synthetic gate; full-CAL refit is NOT a VAL leak (no VAL claim); future real single-point must use independent VAL/fresh; never read VAL here.

## Scope

- Define the two-file artifact (`model_f_input.npz` with only `counts_ab,p_b` + `model_f_input_summary.json` with frozen schema `v72p2d5_model_f_input_v1`) under the planned formal root `workspace/v72p2d5_model_f_input/20260907_r1/` (NEVER created here, only `tmp_path` tests).
- Add one builder (`build_model_f_input` on injected arrays only), one writer (`write_model_f_input`, no-overwrite, exactly 2 files), one reader (`load_model_f_input`, revalidating), one prepare/verify runner (`scripts/v72p2d5_prepare_model_f_input.py` with `--phase prepare/verify` + `--execution-authorized` choke), and a minimal D5 consumer (fixed-root load then `prepare_model_f_prior`, no new CLI flags).
- Implement-only: no real prepare, no VAL/decoder/P0 execution, no formal output creation in this change.

## Non-goals

- No real CAL/parquet read, no formal Model-F artifact generation, no P0/G1/G2 execution, no real-data results, no acceptance/promotion.
- No VAL read, no decoder call, no G0-toy reuse, no invented distribution.
- No overwrite of existing outputs; no hash/checksum/signature; no atomic/backup/lock machinery.
- No change to frozen experiments, thresholds, seeds, budgets, call counts, G2 grading, or `exact_failure_fraction` naming.
- No change to `AGENTS.md`, `AGENT_PROJECT_MEMORY.md`, `docs/decision-log.md`, `openspec/project.md`, roadmap, `cycle_state.yaml` authorizations, existing D4/D5 result docs, formal outputs, `src/**`, `experiments/**`, `tools/**`, or the sibling Release checkout.

## Acceptance

- Builder/writer/reader meet the frozen axis, shape, sum, marginal, and summary checks; transpose must fail; `p_b` is derived, never hand-filled.
- Prepare runner refuses while unauthorized (exit 3, zero reads/writes/imports); authorized path is implemented but NOT executed here (only fake/injected-loader tests).
- D5 consumer refuses while unauthorized before any artifact read; authorized fake load reaches `prepare_model_f_prior` then the phase runner; missing artifact stays BLOCKED.
- Focused tests prove the frozen matrix; existing D4/D5 expectations unchanged; formal Model-F/P0/G1/G2 roots absent; all `*_execution_authorized` stay false.

## Path rework addendum (PX11, frozen defect)

- Pre-EXECUTE review found `PX11 FAIL (BLOCKING)`: relative `parquet_path` joined to the registry parent yields `workspace/comparison_bench/...` (`exists False`) instead of the repo-root relative `comparison_bench/...` (`exists True`). Authorized prepare with the frozen command would fail before any CAL read.
- Rework contract (no registry edit, no absolute Windows freeze): relative SHALL resolve vs Comparison repo root from `__file__`; absolute SHALL resolve directly; no cwd, no search, no fallback; empty/missing/nonexistent SHALL fail before CAL read with no output; relative and absolute `--registry` invocations SHALL resolve to the same absolute parquet path.
- History and statistical contract unchanged: counts axis, shape, sum, marginal, lambda, session, CAL/VAL IDs, artifact schema, authorization gates, and Pre-EXECUTE packet/review verdict history stay as frozen.
