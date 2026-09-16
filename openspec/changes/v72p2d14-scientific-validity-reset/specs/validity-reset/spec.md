# Spec delta: D14 Scientific Validity Reset R1 (P-spec, planning only)

Authority: `.workbuddy/tasks/D14_SCIENTIFIC_VALIDITY_RESET_R1_TASK_PACKET.md`
§1–§8 (frozen). Track `EXPLORE` (packet §1). This delta constrains successor
Phases P, C, R, N and their reviews. It merges or replaces no accepted plan;
on conflict the frozen packet and the accepted D5/D8–D13 terminals govern.
No execution, no authorization, and no hypothesis-as-constant promotion occur
under this change.

## VR-P (prior-selection correction; code + focused tests; NO execution)

- VR-P-01: `run_p0_cost_synthetic`, `run_g1_synthetic`, and
  `run_g2_synthetic` (in
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`,
  currently the `prepare_model_f_prior(_c, _b)` sites at :2996/:3011/:3034 —
  successor verifies by symbol) SHALL call
  `prepare_model_f_prior_candidate(_c, _b)` with identical arguments and
  identical `(pb, pf)` return contract. No signature, threshold, seed, budget,
  phase-runner, decoder-binding, or writer change SHALL accompany the switch.
- VR-P-02: The stale docstring on `prepare_model_f_prior` (:2452, "Sole
  production source of `(p_b, p_f)` …") SHALL be reworded to
  historical-reconstruction-only, naming the candidate chain as the production
  selection; the stale docstring on `prepare_model_f_prior_candidate` (:2488,
  "Production phases keep calling `prepare_model_f_prior`.") SHALL be reworded
  to state the candidate is the production selection for P0/G1/G2. No other
  semantic change to either function SHALL occur.
- VR-P-03: Legacy `prepare_model_f_prior` and `build_f_model` SHALL be
  retained behavior-identical (historical artifact reconstruction needs the
  identity). They SHALL NOT be deleted, renamed, or re-smoothed.
- VR-P-04: Focused tests (additive cases in
  `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` only) SHALL, per
  entrypoint: spy/monkeypatch both estimators and prove the candidate is
  called exactly once while the legacy estimator (poisoned to raise) is never
  called; use a fake `decode_fn` and an explicit `out_dir` under `tmp_path`
  (zero production decoder, fresh scratch only); assert the selected prior is
  finite, column-normalized, non-uniform on the accepted Model-F fixture, and
  bitwise/numerically equal to direct candidate output on the same injected
  tables; and include a static anti-return assert that the three entrypoint
  bodies contain no `prepare_model_f_prior(` call, with patterns requiring `(`
  immediately after the legacy stem so `prepare_model_f_prior_candidate(`
  never matches. Fake Model-F tables SHALL be test-only injected, never
  written to formal roots, never claimed as CAL-TRAIN.
- VR-P-05: NO P0/G1/G2 execution SHALL occur: decoder calls 0, no formal-root
  creation or modification (snapshot proof), no `cycle_state.yaml`
  authorization change, no CAL/VAL/real-data read in code or tests.

## VR-C (G2/X4 corrigendum; docs only; NO execution)

- VR-C-01: One new additive file SHALL be created:
  `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/G2_PRIOR_CONFIG_CORRIGENDUM_R1.md`
  (following the `D7_F_CORRIGENDUM_R1.md` additive pattern). It SHALL rewrite
  no historical artifact and change no historical terminal string.
- VR-C-02: One append-only pointer block SHALL be added to each of the D5
  root-cause record
  (`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_WIDE_ATTRIBUTION_R2.md`)
  and the D7 root-cause reset record
  (`docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/OPERATOR_RETURN_R1.md`),
  each linking to the §VR-C-01 file. Historical body lines SHALL stay
  byte-identical.
- VR-C-03: The corrigendum SHALL state all of: (a)
  `workspace/v72p2d5_g2/20260906_r1` preserved unchanged (4 files, 1320/1320
  calls); (b) `G2_CURRENT_CONFIGURATION_FAILED` retained as the literal,
  accurate grade of the executed configuration; (c) that configuration tested
  the rejected per-cell prior (X4/`run_g2_synthetic` → `prepare_model_f_prior`)
  and is invalid as evidence for n=256 finite-length feasibility or route
  closure; (d) supersession of the scientific inference only, not the recorded
  execution; (e) no claim that the prior defect is the unique cause of all
  failures.
- VR-C-04: Stale D5/D7 status fields (`cycle_state.yaml`) and decision/memory
  pointers (`docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md`) SHALL be
  updated additively only (append-only entries pointing at the corrigendum);
  no historical line SHALL be rewritten.
- VR-C-05: Unchanged-root proof (root file listing + grade-string presence +
  scoped `git status` showing the root and record bodies untouched) SHALL be
  recorded before C-review.

## VR-R (rate-calibration audit; module + no-decoder run)

- VR-R-01: One small additive module SHALL be created:
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d14_rate_calibration_audit.py`,
  plus thin runner `scripts/v72p2d14_rate_calibration_audit.py`, plus additive
  tests `comparison_bench/tests/test_v72p2d14_rate_calibration_audit.py`. The
  module SHALL reuse (never copy) the accepted D8–D12 input and sampling
  helpers and SHALL record its exact import map in its docstring. Math-fixture
  tests SHALL prove the entropy/CE/self-information equations; no-write/refusal
  checks SHALL run in fresh basetemps.
- VR-R-02: The audit SHALL read only the accepted CAL-only Model-F artifact
  (`workspace/v72p2d5_model_f_input/20260907_r1/`) and the immutable synthetic
  records enumerated in `milestone_inventory.md` §5. VAL/real/raw reads SHALL
  NOT occur.
- VR-R-03: The audit SHALL compute and persist, on the frozen fresh root
  `workspace/v72p2d14_rate_audit/20260914_r1/` (proven absent before the run;
  never overwritten) as CSV/JSON plus one concise `report.md`: (a) L1/L2
  generator entropy with equations, axes, units (bits),
  floor/renormalization order, and estimator identity; (b) CE constants with
  provenance and, for every frozen f/width/layer row, rows, disclosed bits,
  generator entropy load, nominal factor, and effective factor; (c) per-block
  self-information for the frozen D12 and D11 block identities joined on the
  stored identity fields to exact/syndrome outcomes with `undetected` kept
  isolated and never merged into success/FER; (d) quantile-binned success
  counts and correlations as descriptive diagnostics; (e) explicit separation
  of expected information load from finite-code/decoder success — `I <=
  disclosed bits` SHALL never be labeled sufficient for decoding; (f) a
  cross-check of L1 4.2867 / L2 3.2227 / 0.890 / 0.979 / 1.068 reporting exact
  reproduced values or the mismatch with its cause. Hypothesis numbers SHALL
  NOT be copied as constants.
- VR-R-04: The run SHALL make zero decoder calls, create zero new random
  blocks, perform zero seed search, and SHALL record wall time and peak RSS.
  Breaching the frozen single-phase ceilings (3600 s / 2 GiB) SHALL STOP the
  run as out-of-scope and force re-scoping, never tuning.

## VR-N (next-experiment freeze; docs only; NO code, NO run)

- VR-N-01: `docs/research_cycles/D14_VALIDITY_RESET/N_DISCRIMINATOR_PREREG_R1.md`
  (frozen, unauthorized) SHALL be written solely from reviewed R evidence and
  SHALL fix: the rate/row-vs-generator choice (entropy-derived rates/rows on
  the actual generator, or a generator change to match the chosen CE, with the
  choice and its why stated); the arm set (L055 plus its frozen control on L1,
  plus an L2 DV3/oracle diagnostic on the true-U1 prior that never gates
  PASS); paired blocks with multiple graph seeds; a batch sized only to decide
  whether the next investment belongs to L1 construction or L2 degree design;
  preregistered thresholds, exact call list, fresh root path (proven absent),
  exact command, budgets within the frozen ceilings, and the claim ceiling
  (synthetic diagnostic only).
- VR-N-02: The packet SHALL carry terminal
  `READY_AWAITING_EXPLICIT_AUTHORIZATION` and SHALL grant no execution. D7-H
  SHALL NOT be revived by this packet (packet §7: reconsideration only after
  calibrated single-layer and forward baselines show alternating transfer
  addresses the remaining bottleneck).
- VR-N-03: No N implementation code and no N execution SHALL occur under this
  change; any future runner belongs to a later authorized change.

## VR-S (boundaries; binding on P/C/R/N)

- VR-S-01: This change SHALL NOT execute P0/G1/G2, bind a production decoder,
  run a DE sweep, touch real data, resample CAL/VAL, run a D7-H or L2 decoder
  batch, rerun G1/G2, push, qualify, or publish (packet §1).
- VR-S-02: Frozen D5 plans, seeds, budgets, call counts, G2 four-state
  grading, `exact_failure_fraction` naming, STRUCTURE/G0 behavior, and all
  D8–D13 terminals SHALL NOT change. `src/`, `experiments/`, `tools/`,
  `results/`, existing `workspace/` roots, `AGENTS.md`, and
  `cycle_state.yaml` authorizations SHALL NOT be touched beyond the additive
  status lines §VR-C-04 permits.
- VR-S-03: Any review FAIL SHALL block its phase (revise-required, fix the
  scoped root cause, re-review). Blocking inconsistency STOPs readiness; the
  return string §proposal-claim-ceiling is emitted only on full pass.
