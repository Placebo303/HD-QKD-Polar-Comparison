# V72P2D4-CAL-RATE PLAN_REVIEW R2 (D4 U/G/F/L revision, independent)

- Repository: `HD-QKD_Polar_Comparison`
- Change: `formal-ir-v72p2d4-cal-gf32-model-rate-audit`
- Cycle: `V72P2D4-CAL-RATE` / R2 implementation cycle `V72P2D4R2-*` (unassigned)
- Prior state: `RESULT_REVISE_REQUIRED` / `r1_verdict CANDIDATE_NOT_ACCEPTED` / `next_gate D4R2_INDEPENDENT_PLAN_REVIEW` (see `cycle_state.yaml`, `R1_CORRIGENDUM.md`)
- Review kind: `R2_INDEPENDENT_PLAN_REVIEW_CAL_ONLY` (read-only, 4 files, no parquet/VAL/decoder/output)
- Verdict: `PLAN_ACCEPTED_R2`
- Lifecycle after this record: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` (no execution authorized by this record)
- Date: `2026-09-05`

## 1. Review scope (read-only, exactly 4 files)

1. `openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/proposal.md`
2. `openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/design.md`
3. `openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/tasks.md`
4. `openspec/changes/formal-ir-v72p2d4-cal-gf32-model-rate-audit/specs/spec.md`

No VAL read, no decoder call, no `run_01`, no formal output created during this review. Git SHA pin (`HEAD == origin == implementation SHA`, `ACCEPTED_PLAN_SHA` re-derivation, `rg` stale-SHA 0 hits) is deferred to the R2 implementation thread's pre-EXECUTE review per `AGENTS.md` §10.3; this record binds plan text only.

## 2. Item-by-item (required freeze terms — all PASS)

- [PASS] U uniform 5/5/10 reference: all 4 files state `P=1/1024`, `CE_L1/CE_L2/CE_joint=5/5/10 bit/symbol` exact (`log2 32=5/log2 1024=10`), key `uniform_reference_descriptive`, excluded from selection/budget/route.
- [PASS] G train marginal: all 4 files pin `P_G(a)=count_TRAIN(A=a)/n_TRAIN`, B-independent, simplest candidate.
- [PASS] F full hierarchical single lambda grid30 inner-selected: all 4 files state full `P(A|B)` column-normalized, single Laplace/backoff/shrink coefficient, selected from 30-pt grid by inner TRAIN fit + inner held-out CE only.
- [PASS] L two-layer hierarchical Ponytail same lambda mean joint target: all 4 files state `P(U1|B)*P(U2|U1,B)` V54 caliber (`CE_L2_oracle` with true `U1`, budget-diagnostic only), Ponytail reuses same outer-fold F-selected lambda (no independent search), objective mean joint CE.
- [PASS] Circulant DEFERRED: all 4 files record `CIRCULANT_DEFERRED`, removed from audit, excluded from selection/budget/route; successor only backlog.
- [PASS] Lambda grid30 outer forbidden: all 4 files state grid30 SHALL only inner, SHALL NOT touch outer TEST for tuning/early-stop/selection (`grid30 outer 禁入`); violation = `BLOCKED`; tamper intent preserved (outer-TEST perturbation leaves selection unchanged).
- [PASS] Delta fixed 0.02 written before implementation: all 4 files freeze `SELECT_DELTA=0.02` pre-implementation, non-tunable, with explicit note correcting R1 post-hoc rewrite violation (`R1_CORRIGENDUM.md` §4: prior `0.01` frozen vs `0.02` implementation).
- [PASS] Frame folds F0-F3: all 4 files freeze `F0=702..957/F1=958..1213/F2=1214..1469/F3=1470..1725` (256 frames each), outer `TEST 256/TRAIN 768`, 3 deterministic inner folds of 256 frames each (frame-ordered, no shuffle/row-random/VAL), with full mechanical assertions (disjoint/cover/256/FULL-1024/256-pairs).
- [PASS] Scientific U→G/G→F/F→L decomposition: all 4 files require reporting `U→G` (marginal vs uniform), `G→F` (full-dependence), `F→L` (hierarchy) plus `U→selected` total, same caliber bit/symbol, descriptive only (no lower-bound/failure verdict).
- [PASS] Selection G/F/L+U reference rule: all 4 files state selection over G/F/L only by `mean(CE_joint)` minimal + `Δ<0.02` simple-priority `G<F<L` + stability downgrade (`std>0.10` or `max-min>0.20` bit/symbol); U reference only; M3-exited/circulant-deferred excluded; no auto-conversion to matrix/decoder params.
- [PASS] Budget f four tiers rows ceil/5 vs 16/200/216: all 4 files freeze `N=1024`, `f∈{1.0,1.1,1.2,1.3}`, `rows=ceil(N*CE*f/5)` (GF32 5 bit/row), vs history `16/200/216` rows (`80/1000/1080` bit, `1080/1024=1.0546875`); `required>available` only `MODEL_BUDGET_MISMATCH`; L1-shortfall SHALL NOT be patched by L2 alone.

## 3. Standing freeze terms (re-verified, all PASS)

- [PASS] Canonical `counts[a,b]` axis0 Alice/axis1 Bob unique, no implicit transpose; `symbol=low+32*high`, `U1=high/U2=low/bit0=LSB`, no Gray/permutation.
- [PASS] Chain `|CE_joint-CE_L1-CE_L2_oracle|<1e-10` per-fold and mean, else `BLOCKED`; floor exact `1e-300` (normalize then `max(P,1e-300)`, log-only).
- [PASS] R5 gate `6.422/5.083/11.505` same-fixture repro, each `|Δ|<1e-6` plus chain `<1e-10`, `REAL_CAL_EXACT_MATCH=false` (synthetic provenance), failure = `BLOCKED` with caliber/data-domain/implementation root cause, no tuning-to-fit.
- [PASS] Routes A/B/C mutually exclusive exhaustive on selected-model mean same caliber (`A=fit@1.3`, `C=mismatch@1.0`, `B=fit@1.0∧mismatch@1.3`); A does not authorize real diagnostics; B/C pause generalization.
- [PASS] Prohibitions: VAL reads 0, decoder calls 0, no new matrix, no checksum/hash/tag/signature, no formal output/`run_01`, no execution authorization.
- [PASS] Four-file consistency: proposal/design/tasks/spec agree on U/G/F/L identities, `M3_EXIT_AMBIGUOUS` + `CIRCULANT_DEFERRED` exclusions, delta-0.02 pre-freeze, grid30-outer ban, folds, decomposition, selection, budget, routes, BLOCKED stops.

## 4. Delta vs R1 (for R2 implementer)

- R1 `M0/M1/M2` → R2 `G/F/L` (U takes over uniform-descriptive with explicit 5/5/10; G=M0-equivalent; F upgrades old fixed-`lam=1.0` full model to grid-30 inner-selected; L narrows old independent grid-30 layered search to Ponytail reuse of F lambda).
- `SELECT_DELTA` stays numerically `0.02` but authority changes from post-hoc implementation match to pre-implementation plan freeze.
- `CIRCULANT_DEFERRED` is new explicit exclusion (was implicit backlog); `M3_EXIT_AMBIGUOUS` retained.
- R1 numeric evidence (`RESULT_SUMMARY.md` M2 `6.978821` joint, route C) is not invalidated as arithmetic but is not R2 evidence; R2 must re-run under the new F/L lambda semantics on a fresh additive root, never overwrite `v72p2d4r1_*`.

## 5. Acceptance scope

This record accepts the R2-revised plan text only. It does not accept any result, authorize development/formal/real execution, VAL read, decoder call, new matrix, or `run_01`. Next gate: R2 frozen implementation (audit script + focused test, at most one each, Ponytail lite) followed by independent implementation review and pre-EXECUTE review before any CAL-only run.
