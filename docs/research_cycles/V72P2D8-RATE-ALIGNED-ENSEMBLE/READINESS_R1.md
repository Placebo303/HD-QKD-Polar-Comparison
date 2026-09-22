# D8 rate-aligned GF32 ensemble feasibility — heavy R1 readiness

Status: `D8_DE_SWEEP_RESULT_ACCEPTED_ROUTE_TO_D9_CALIBRATION`
(readiness only; grants no execution, creates no root). E01–E12 complete:
E11 independent review `PASS_WITH_FINDINGS`; E12 applied the single scoped F1
correction (scoped re-review `PASS`). The future DE sweep still requires a
separate explicit authorization.
`independent_review_verdict: PASS_WITH_FINDINGS`
`independent_review_artifact: docs/research_cycles/V72P2D8-RATE-ALIGNED-ENSEMBLE/INDEPENDENT_REVIEW_R1.md`
`e12_correction: F1 applied (realized max check degree 4 ≤4/≤8 asserted; 15/15 tests)`
`carried_findings: F2_F3_F4`
`main_readiness_acceptance: true`
`next_gate: D8_DE_SWEEP_A1_EXPLICIT_AUTHORIZATION`
`sweep_result_accepted: true`
`sweep_terminal_accepted: D8_DE_BASELINE_NOT_CONVERGED`
`main_route_decision: D9_DE_DECODER_CALIBRATION_AND_THRESHOLD`
Track: `EXPLORE_HEAVY` (repository-wide two-tier workflow accepted:
`TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE`).
Authority: `.workbuddy/tasks/D8_RATE_ALIGNED_ENSEMBLE_FEASIBILITY_R1_TASK_PACKET.md`
(§3 sources, §4 six questions, §5 frozen scope, §6 allowed files, §7 E01–E12,
§9 STOP conditions).
Branch: `formal-ir-v72p1-addendum-clean` (not switched; no commit, no push).
Scope of this record: E01–E06 readiness/design only; no production code, no
decoder, no DE scientific sweep, no CAL/VAL/raw/real contact, no root created.
Production decoder calls: **0**. DE scientific calls: **0**.

D8 DE sweep A1 closure (appended 2026-09-13; prior readiness fields above unchanged):
`de_sweep_terminal: D8_DE_BASELINE_NOT_CONVERGED`
`de_sweep_root: workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405`
`de_sweep_calls: 126` / `de_sweep_exit_code: 0`
`de_sweep_review_verdict: PASS_WITH_FINDINGS`
`de_sweep_review_log_section: EXPLORATION_LOG.md#2026-09-13--d8-de-sweep-a1-batch-end-review`
`main_route_decision: PENDING`
`next_gate: D8_DE_RESULT_MAIN_ROUTE_DECISION`
`memory_triage: DEFERRED_UNTIL_MAIN_ROUTE_DECISION`
No commit, no push; no winner accepted.

## 1. E01 — Accepted D6 claim ceiling and route close (read-only)

Source: `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/`
(`cycle_state.yaml`, `EXPLORATION_LOG_R1D.md`, `D6_GRAPH_MOTHER_R1D_HEAVY_R1_READINESS.md`,
`D6_R1D_EXPLORE_A1_BATCH_END_REVIEW.md`). No D6/D7 file was edited.

- Lifecycle: `D6_R1D_EXPLORE_RESULT_ACCEPTED_GRAPH_REDIRECT_CLOSED`
  (`cycle_state.yaml:2`; acceptance 2026-09-13, `result_accepted: true`).
- Accepted facts (frozen B0/B1/T1 DV3 synthetic contract):
  L1 exact/syndrome **0/40**; L2-APP **5/40**; L2-oracle **35/40**;
  end-to-end APP exact **0/120**; T1 PEG-DV3 **silent at n64, n128, n256**
  (`EXPLORATION_LOG_R1D.md:351-368`; batch-end review
  `D6_R1D_EXPLORE_A1_BATCH_END_REVIEW.md:8,20`).
- Closed: only the **eligible-only DV3 topology substitution** under the frozen
  contract (`...:356-362`). NOT closed / NOT claimed: graph-family
  impossibility, T2/T3/T4/M1/M2 behavior, other degree distributions, n>256,
  real data, FER, leakage, qualification, promotion, D7-H revival.
- `next_gate`: `D8_RATE_ALIGNED_ENSEMBLE_FEASIBILITY`
  (`cycle_state.yaml:68`); D7-H remains `NOT_AUTHORIZED_NOT_RECOMMENDED`.
- Consequence used here: the next variable is the ensemble/degree distribution,
  not another DV3 topology, schedule or cross-layer alternation.

## 2. E02 — Historical DE engine inventory and ranking

Ranking criterion: mathematical compatibility with the D8 use (GF32 / poly 37,
probability-domain full-vector messages, check-update convention matching the
current decoder, ability to consume the current Model-F L1 prior, degree
parameterization, accepted evidence quality) — not age or convenience.

| # | module | channel/message representation | check update | coefficients | accepted evidence | verdict |
|---|---|---|---|---|---|---|
| 1 | `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v26_mcde.py` | arbitrary `(n,q)` **true-symbol-centered, row-normalized posterior population** (`_channel_rows_from_centered:123-139`; `run_mcde_posterior:243-326`); q∈{2,32,512}; probability domain | coefficient-permuted WHT XOR convolution `_check_update_coeff_jit:48-90`, `check_update_mcde_posterior:170-190`; kernels `variable_update_mcde:142-153`, `belief_update_mcde:156-167`, V14 `_variable_or_belief_jit`/`_wht_row_jit` (`nonbinary_v14_mcde.py:95-190`, `_FLOOR=1e-300` L84) | `build_gf_perm_table:93-114` via `GF2mField.create(32)` = m=5 poly `0b100101=37` (`nonbinary_field.py:14-18,62-64`); nonzero `inv(h)·y` permutation — identical convention to `v35_algorithm_development._check_update_log_batch:453-513` | V26 gate canonical `run_02` A02 GF32+GF32 30/30 @f=1.3; V27 gate `run_01` `pass_finite_budget_ready`; V37R1 2,349 DE runs (`DEVELOPMENT_RESULT_ACCEPTED`) | **SELECTED** |
| 2 | `nonbinary_v27_gate.py` | adapter/planner over V26; fixed `LAMBDA={2:1.0}` (L55); V25-source `channel_counts.npz` adapters (`nonbinary_v26_channel.py:247-281`); multistage L1/L2 | V26 unchanged | V26 unchanged | V27 gate PASS (`run_01`, 322.9 s) | Reused **concept** only: `layer_rate_rho:185-189` (`R=1-m/n`, `ρ=make_rho`). Rejected as the runner: V25 real-data-derived channel + fixed λ + gate-specific terminal semantics. |
| 3 | `v37_de_screening.py` | V26 kernel + true-predecessor-conditioned empirical sampler from V25 counts (`build_v37_channel_sampler:98-151`) | V26 unchanged | V26 unchanged | V37R1 `P1_NO_FINITE_FEASIBLE_DE_ADVANCE` (accepted development result) | Reused **metric definitions** only (`compute_trajectory_metrics:295-346`: AUT_30, H5/10/15/60, T_0.10/0.01). Rejected as the runner: hard-coded sources/m (n=1024, 184/190/192, R≈0.81), L2-conditioned sampler, V25 channel, and modification of accepted V37 code would be required. |
| 4 | `nonbinary_v14_mcde.py` | shift-invariant `w[delta]` structured error-domain channel or QSC (L324-328) | WHT convolution, all-unity coefficients, zero syndrome (`_check_update_jit:155-190`) | none | stage-0 mechanism regression (q=4, R=0.75, published proxy 0.069±0.012); q=1024 stage-2 | Rejected as primary: no nonzero edge coefficients; channel is a surrogate (QSC/structured), not the empirical 32-ary posterior. |
| 5 | `nonbinary_v9_mcde.py` | QSC/full-vector; semantic base (`parse_degree_hist:112-146`, `entropy_base_q:386-406`) | all-unity WHT convolution | none | V9 base semantics (read-only reference) | Rejected as primary (no coefficients, QSC only); retained as read-only helpers. |
| 6 | `nonbinary_v11_mcde.py` | SC-LDPC QSC MC-DE (chain/window coupling) | all-unity | none | V11 SC engineering evidence | Rejected: different ensemble family (spatially coupled) and channel; out of D8 scope. |
| 7 | `nonbinary_v10_de.py` | own MC-DE fitness + DE/rand/1/bin optimizer | all-unity | none | V10 optimizer evidence | Rejected: search optimizer violates bounded deterministic enumeration. |
| 8 | `nonbinary_v19_de_search.py` | warm-started rate ladder / extended degree probes over V18/V10 | all-unity/structured | none | V19 diagnostic | Rejected: search-oriented, structured channel, high-rate q=1024. |
| 9 | `nonbinary_v22_de_gate.py`, `nonbinary_v22b_mcde.py`, `nonbinary_v18_b2_structured_de.py` | V17 structured channel (`w`) harnesses / `DEGREE_MAX` wrapper | all-unity | none | diagnostic-only | Rejected: surrogate channel, engineering harnesses, `diagnostic_only` claim ceiling. |
| — | `v37_degree_feasibility.py` | not a DE engine: finite-length degree analyzer (`analyze_degree_feasibility:300+`; forest bound docstring L22-30) | — | — | V37P0 `REVIEW_ACCEPTED` | Reused read-only for the recorded finite-forest diagnostic (`N2`, `gamma_2`), not as a refusal gate. |

Selected reuse path: **V26 kernel unchanged** + one thin D8 L1 Model-F channel
adapter + V27-style rate/ρ mapping + V37 metric definitions + V37P0 forest
diagnostic. Rejected alternatives all fail on at least one of: no nonzero edge
coefficients (V9/V10/V11/V14), surrogate channel rather than the empirical
32-ary posterior (V14/V17/V18/V22), search/optimizer behavior (V10/V19), or
real-data-derived channel and hard-coded high-rate sources (V27/V37 runners).

## 3. E03 — Model-F L1 marginal channel trace into the DE input

Every transformation (frozen; full table in `design.md` §2):

1. artifact `model_f_input.npz`: `counts_ab` (1024,1024) axis (Alice,Bob),
   `p_b` (1024,), `lambda_star=137.3823795883264` (accepted CAL-only,
   1024 frames × 256 pairs; `MODEL_F_INPUT_RESULT_ACCEPTANCE_R1.md` A01);
2. `pb = p_b / p_b.sum()` (`scripts/v72p2d6_graph_mother_development.py:791`);
3. `P_F = (counts_ab + λ*·p_global[:,None])/(n_b[None,:] + λ*)` — E2
   concentration backoff (`v72p2d5_gf32_rate_mother.py:275-306`), reached via
   `prepare_model_f_prior_candidate:2480-2507` (the D6-current prior);
4. `P1 = marginalize_f_to_p1(P_F)` — reshape (32,32,1024), sum U2 axis,
   renormalize (`:309-321`);
5. per-sample decoder prior `pr1 = _floor_renorm(P1[:,b].T, 1e-15)` — the exact
   D6 `run_cell` line (`scripts/v72p2d6_graph_mother_development.py:817`;
   floor/renorm `:346-351`);
6. DE input: draw `(b,a) ~ P_B(b)·P_F(a|b)`, `u = a//32`
   (`symbols_to_layers:401-406`), centered row `c[e] = pr1[u XOR e]`
   (V26 centering convention `nonbinary_v26_channel.py:275-280`).

Exactness: the DE consumes the **full 32-ary posterior rows**; centering is a
reindexing (`e = u XOR x`) that is an exact symmetry of the linear code
(`E = X - u_true` makes `Σ h_e X_e = s_r` homogeneous), so no scalar
reduction, no BSC/AWGN/q-SC substitution occurs. Residual modeling step: the
standard DE i.i.d.-population exchangeability, already present in the accepted
V26/V27/V37 line — not a new assumption. Prior-anchor decision (explicit): the
D8 channel anchors on the **E2 concentration backoff** because D6 R1d (the
accepted predecessor) used it; the D5 G2/X4 frozen per-cell pseudocount
variant (`build_f_model:247-272`, used by the D5 production phases
`:2995/3010/3033`) is recorded as an out-of-scope sensitivity variant — the
sweep varies the ensemble only, never the channel. No
`BLOCKED_CHANNEL_REPRESENTATION_DECISION` is required.

## 4. E04 — Rate/degree/check-row equations

Frozen equations and worked arithmetic in `design.md` §3. Summary:
`R = 1 - m/n` with the accepted D6 rows (n64 L1 (49,59,64), L2 (43,52,64);
n128/n256 exactly ×2/×4), giving R = 5/64 = 0.078125 at f1.2 for all widths;
`f = 5m/(n·H_L1)`, `H_L1 = 3.814742` (D5/D4 frozen CE); ensemble identities
`dbar_v = 1/Σλ_j/j`, `dbar_c = 1/Σρ_i/i`, `m/n = dbar_v/dbar_c`; concentrated
two-point `ρ` via `concentrated_check_distribution`
(`nonbinary_v9_common.py:207-247`). Hand checks: regular DV3 n64 f1.2 →
`ρ={3:11/16, 4:5/16}`; regular DV3 n64 f1.0 → `ρ={3:1/16, 4:15/16}`; tiny
ensembles (n=8,m=5,λ={2:1}) → `ρ={3:3/4, 4:1/4}` and (n=9,m=6,λ={3:1}) →
`ρ={4:4/9, 5:5/9}`. D5 provenance contrast recorded: D5 `_rows_required` gives
n256 L1/L2 235/206 while the accepted D6 successor sets are 236/208 (exactly
rate-aligned); D8 freezes the D6 sets. STOP §9 "rate mapping cannot be
reconciled" is **not** triggered: the mapping is reconciled against the
accepted D6 row budgets and is exactly n-proportional.

## 5. E05 — Frozen candidate enumeration/selection rule

`design.md` §4: λ support `{2,3}`, `λ2 ∈ {0.00,0.05,…,1.00}` (21 candidates,
hard cap 21), canonical IDs, ascending order, regular-DV3 baseline included,
dv2 endpoint included; `ρ = make_rho(R, λ)` derived, never searched;
compatibility constraints (min check degree ≥2, simple graph, accepted
coefficient stream, realized dc ≤ 8); refusals recorded; no adaptation to
observed outcomes; V37P0 forest diagnostic recorded only.

## 6. E06 — Artifacts, future root/command/budget (left absent/unauthorized)

OpenSpec change (created before any behavior edit):
`openspec/changes/v72p2d8-rate-aligned-gf32-ensemble-feasibility/`
(`proposal.md`, `design.md`, `tasks.md`,
`specs/rate-aligned-gf32-ensemble-feasibility/spec.md`).
Cycle docs: this record + `EXPLORATION_LOG.md`; one decision-log entry.

Fresh future root UUID: `5edf0630-f357-4a7e-b4c5-9ba955021405` —
`workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405/`
verified **absent** at freeze time. Exact future command (do not run):

```text
.venv/bin/python scripts/v72p2d8_rate_aligned_ensemble_development.py --de-sweep \
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
  --out-root workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405
```

Budgets: ≤126 DE calls (21×2×3) + ≤20 setup, wall ≤1800 s, per-call ≤120 s,
RSS <2 GiB strict, single process, no retry/resume/seed search. Seeds
`2026091601..2026091603` (verified not present in any existing source).
All authorization flags remain false; the sweep is unexecuted and unauthorized.

## 7. Answers to packet §4

1. **Nearest DE implementation**: `nonbinary_v26_mcde.run_mcde_posterior`
   (GF32/poly 37 via `GF2mField.create(32)`, full probability vectors,
   coefficient-permuted WHT convolution matching `v35` `_check_update_log_batch`,
   arbitrary centered posterior-population channel), with V14 kernels and V9
   helpers; accepted V26/V27/V37 evidence.
2. **Channel representability**: yes — exact 32-ary rows from the accepted
   CAL-only Model-F artifact through the E2 `P_F` → `P1` → `1e-15` floor chain,
   XOR-centered per sample; no scalar surrogate; only the standard accepted DE
   i.i.d.-population assumption remains.
3. **Rate/check-row mapping**: `R = 1 - m/n` on the accepted D6 rate-aligned
   rows; R(f1.2)=5/64 at all widths; `ρ` from the concentrated formula;
   D5 ceil contrast recorded and reconciled (D6 successor sets govern).
4. **Minimal candidate family**: variable-edge-perspective λ over `{2,3}` on a
   0.05 grid (21 candidates), fixed Model-F/GF32/rows/decoder semantics,
   ρ derived from the fixed rate; baseline regular DV3 included.
5. **DE observable/threshold**: check-population entropy trajectory →
   `AUT_30`/`H60`; advancement = H60<1e-4 on all seeds in both conditions plus
   a ≥5% `AUT_30` improvement over regular DV3 on f1.2; a silent grid closes
   only the frozen support/grid and routes to a broader proposal or an
   explicit channel/decoder mismatch analysis, never "NB-LDPC impossible".
6. **Known-limit/tiny reproduction**: yes, planned in E08/E09 — existing
   accepted V26/V27/V37 regressions plus D8 tiny checks (unit-coefficient
   cross-kernel equality with V14 `_check_update_jit`, tiny hand ensembles,
   synthetic sampler equality, baseline reproduction). Not run in this
   readiness call (no DE/decoder execution).

## 8. Limitations carried (explicit)

- V26 DE is a flooding-style variable→check→belief population MC-DE; the
  finite-length decoder is row-layered (`decode_row_layered_fftqspa`). The DE
  is an ensemble screen, not a finite-length predictor; this limits any
  inference from DE convergence to decoder behavior.
- Population draws are i.i.d. with replacement; per-check true-symbol
  consistency of a realized codeword is not represented (standard DE).
- Check-update floors differ (kernel `1e-300`; decoder `1e-15`) — numerical
  representation, not a convention change.
- DE results use the CAL-only Model-F prior; no VAL/real-data read.
- D7-H remains `NOT_AUTHORIZED / NOT_RECOMMENDED`; not revived by readiness.

## 9. State

All authorization keys false; no root created; no commit, no push. E01–E06
complete. Next: E07–E12 (implementation, focused tests, bounded perf smoke,
independent reviewer-go review, at most one scoped correction) ending at
`D8_RATE_ALIGNED_ENSEMBLE_READY_AWAITING_EXPLICIT_AUTHORIZATION`. The future
DE sweep requires a separate explicit user/main-thread authorization.

## 10. E07–E10 implementation/verification delta (2026-09-13; no execution)

- E07 implemented (allowed files only): adapter
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d8_rate_aligned_ensemble.py`
  (L1 Model-F sampler from the accepted CAL-only artifact through
  `pb = p_b/p_b.sum()` → E2 `P_F` → `P1` → `floor_renorm(...,1e-15)` →
  per-sample XOR centering; V27-equivalent `R = 1-m/n` / `make_rho`; 21-ID
  deterministic grid with recorded `make_rho` refusals; V37
  `compute_trajectory_metrics` reuse; V37-P0 `N2`/`gamma_2` recorded-only
  forest diagnostic; unchanged V26 `run_mcde_posterior` wrapper with the frozen
  parameters) and runner
  `scripts/v72p2d8_rate_aligned_ensemble_development.py`
  (`--de-sweep`/`--verify`, six-file fresh root, protected/existing-root
  refusal, ≤126 DE + ≤20 setup, wall ≤1800 s, per-call ≤120 s, RSS <2 GiB
  strict, single process, no retry/resume/adaptive stop; frozen terminals and
  rank key). V26/V27/V37/V14/V9/v35 untouched (import only).
- E08 focused tests
  `comparison_bench/tests/test_v72p2d8_rate_aligned_ensemble.py`; E09 T0/T1:
  `py_compile` + import/constants PASS; `.venv/bin/python -m pytest
  comparison_bench/tests/test_v72p2d8_rate_aligned_ensemble.py -q
  -p no:cacheprovider --basetemp=workspace/d8_tests_<uuid>` → **14 passed,
  0 failed**. No broad suite rerun.
- E09 PROFILE_ONLY bounded smoke (4 DE calls, never sweep evidence, no root
  written): channel load 0.050 s; per-call wall 1.987 s (first call incl.
  JIT), 0.840 s, 0.801 s, 0.815 s; peak RSS 239.3 MiB; future root absent
  after profiling.
- E10 FROZEN_MATCH PASS: `--de-sweep --model-f-root
  workspace/v72p2d5_model_f_input/20260907_r1 --out-root
  workspace/d8_rate_aligned_ensemble_5edf0630-f357-4a7e-b4c5-9ba955021405`
  identical to `design.md` §6; defaults/flags, seeds
  `2026091601..2026091603`, 21 candidates (42 pairs, 126 calls), budgets
  126/20/1800 s/120 s/2 GiB and stop rules verified in code; future root
  verified absent.
- Production decoder calls: **0**. DE scientific calls: **0** (4 PROFILE_ONLY
  calls counted separately; they are not evidence and were not written
  anywhere). No commit, no push. All authorization flags remain false.
- Next: E11 independent reviewer-go implementation + readiness review, then at
  most one scoped E12 correction ending at
  `D8_RATE_ALIGNED_ENSEMBLE_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
