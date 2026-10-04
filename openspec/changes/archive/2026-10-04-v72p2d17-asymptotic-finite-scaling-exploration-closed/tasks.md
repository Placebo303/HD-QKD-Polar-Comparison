# Tasks — D17 Current-Channel Asymptotic-to-Finite Scaling

Legend: `[x]` done this call (D01, planner, no production code, zero
scientific calls); `[ ]` packet-exact future work (each needs its own
packet/authorization; `DE` batch + any claim-bearing run additionally needs an
explicit user grant with Pre-`EXECUTE`/Pre-`RESULT`).

## Readiness audit + spec (this call)

- [x] **A01 channel identity** — exact Model-F candidate prior/generator,
  axes, floor/renormalization, L1/L2 marginal/conditional channels for `D8–D16`
  proven from the rate-mother chain + `R`-audit entropy record + `D8–D16`
  cycle docs. Evidence: `proposal.md` §A01 (verdict EXACT; four recorded
  distinctions; no STOP). Spot files: `entropy.json`, N-prereg §1, `D16`
  design §5, `D15` log pre-dispatch.
- [x] **A02 DE inventory** — `V25/V26/V27` + `D8/D9` mapped by channel, layer,
  profile, rate definition, population, iterations, convergence metric; exact
  transfer/no-transfer table for V26 f1.3 conclusions. Evidence: `proposal.md`
  §A02 + `design.md` §4 (kernel/adapter/method transfer; no numeric transfer).
- [x] **A03 finite inventory** — table `F1–F19` from `D10–D15` roots with `n`,
  layer, profile, rows, recomputed `delta` (3-spot hand recompute ✓),
  graphs/blocks, exact/syndrome/undetected, decoder settings; clusters + root
  identity preserved. Evidence: `design.md` §3 (`D12/D14N/D15` summaries
  re-read this call; `R3/D11` rows provisional → `D02` confirm).
- [x] **A04 compatibility classes** — FIT / validation-only / descriptive-only
  per observation; `APP`/joint excluded from single-layer fit; `L2 ORACLE`
  only in the true-conditioned `L2` model. Evidence: `design.md` §3 classes +
  join rule (cluster+root retention; `D02` join-key check).
- [x] **A05 D16 holdout lock** — cells/seeds/command/root/budgets recorded;
  official root proven absent (`File not found` this call); banned seeds
  `2026094001..4012` + `2026094101..4108` listed; fake-identity scratch
  (`workspace/d16_align_20260915_a/`) locked out with fake-proof; seed grep
  clean outside `D16` plan/test/spec files. Evidence: `proposal.md` §A05 +
  `design.md` §7 gate.
- [x] **D01 OpenSpec freeze** — this change (`proposal.md`, `design.md`,
  `tasks.md`, `specs/de-scaling/spec.md`): L1–L4 hierarchy + probit law with
  `delta_DE/alpha/beta`, binomial likelihood + cluster-bootstrap/`LOO`,
  logistic sensitivity (descriptive), `epsilon 0.10/0.01` + integer row-backoff
  inversion at `n=64/128/256`, units, eligibility, frozen 15-point `DE` grid
  (points/seeds/rule/command/root/budgets), identifiability logic (two-param →
  `beta=0` → `MODEL_NOT_IDENTIFIABLE`), uncertainty, holdout schema + blank
  fields + fail-if-exists, residual separation, post-prediction
  rank/cycle/schedule measurement, claim ceiling. B-grid bounded and
  non-adaptive (no extension/binary search).

## Future asymptotic DE readiness (packet §4 — [ ])

- [x] **B01** Reuse accepted V26 `MC-DE` kernel + `D9` semantic adapter with no
  new kernel; three profiles (L1 L045, L1 L055, L2 DV3 true-conditioned) on the
  exact current candidate channel (`D15/D16` channel).
- [x] **B02** Parameterize rate by `delta`; derive ensemble `rho` from the
  exact rate (frozen `D9` rule); never use legacy `CE` labels.
- [x] **B03** Execute the §4 frozen bounded coarse-plus-confirmation grid
  (only after explicit authorization): bracket each transition with fixed
  points/seeds; no outcome-driven extension or binary search; population
  stability (`4000` vs `16000`) at the bracket.
- [x] **B04** Emit full trajectory summaries for the convergence definition;
  no `DE`↔row-layered trajectory claim beyond `D9` certified primitives.
- [x] **B05** Future `DE` batch command/root/budget with default-false
  authorization, `PROFILE_ONLY`, read-only verifier; root absent + unauthorized
  until the separately authorized run.

## Future finite-length scaling model (packet §5 — [ ])

- [x] **C01** Implement the predeclared probit law; fit separately per profile;
  `delta_DE` fixed from the reviewed `DE` result (never refit to finite data).
- [x] **C02** Fit `alpha>0`, `beta` by binomial likelihood with
  graph-cluster bootstrap / leave-one-graph-out uncertainty.
- [x] **C03** Apply the identifiability ladder (two-param → `beta=0` →
  `MODEL_NOT_IDENTIFIABLE`); never report unstable coefficients.
- [x] **C04** Logistic-link sensitivity fit, descriptive-only; NumPy/stdlib
  only, no new dependency.
- [x] **C05** Report implied integer row backoff at `n=64/128/256` with
  uncertainty for `epsilon=0.10` (primary) / `0.01` (sensitivity) —
  modeling targets, not `FER` qualification.
- [x] **C06** Persist all three `D16`-arm predictions (interval, expected graph
  dispersion, falsification criteria) before any `D16` execution; never revise
  after observing `D16`.
- [x] **C07** Separate residual diagnostics (rank/admission, four-cycles/girth,
  iterations, residual syndrome, graph random effects); not folded into the
  backoff without a new preregistration.

## Future implementation + review (packet §6 — [ ])

- [x] **D02** Audit artifact: compact `CSV`/`JSON` inventory (`F1–F19` +
  join keys) + report; read-only predecessor roots; confirm `R3/D11` rows;
  leave-one-root-out sensitivity.
- [x] **D03** `DE` adapter/runner: current-channel three-profile plan,
  fake-injected tests, authorization refusal, fresh root + verifier; zero
  scientific calls until authorized.
- [x] **D04** Scaling module: graph-aggregated exact binomial counts,
  deterministic fit/uncertainty, synthetic recovery tests (known parameters +
  non-identifiable fixtures), fail-closed banned-seed gate.
- [x] **D05** Holdout record: immutable `D16` prediction schema + blank outcome
  fields; fail if `D16` root exists before prediction freeze.
- [x] **D06** Focused validation: compile, math/channel equivalence, plan/grid,
  fake `DE`, fit recovery, eligibility isolation, root absence, no-production.
- [x] **D07** Independent review with actual artifact access: channel/`DE`
  identity, finite-data eligibility, equations/units, grid/budgets,
  identifiability logic, target-row inversion, `D16` holdout isolation, zero
  scientific calls. Any blocking finding → STOP.

## R2-spec amendment (this call, planner, OpenSpec-only)

- [x] **R2-SPEC** Amend this change (`design.md` new §10 + `specs/de-scaling/spec.md`
  R2 deltas `REQ-DE-R2-01..07` + this task list): record A1 failure evidence by
  reference (`DE_CALL_FAILED@0` tuple-not-callable, `0/240`, retained root
  `workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718`,
  review `VERIFIED/PASS`) with A1-root immutability; freeze `R201–R204`,
  validation `V1–V7` + one-correction allowance, A2 root/command/budgets,
  pre-dispatch `P1–P8`, batch-end scope, return terminals. Authority:
  `.workbuddy/tasks/D17_DE_BINDING_REPAIR_R2_AND_RERUN_TASK_PACKET.md` §§1–5.
  Zero `DE`/decoder calls; no code/scripts/tests/roots edits; no commit/push.
  Branch `formal-ir-v72p1-addendum-clean` unchanged.

## R2 binding repair + rerun (packet §§2–7 — [ ] future operator work, not this call)

Each needs the packet + companion prompt authorization; A2 additionally needs
pre-dispatch PASS. `R204` scientific contract unchanged.

- [ ] **R201 L1 tuple-to-sampler** — `load_l1_channel` once → exact 3-item
  finite shape-compatible `(pb,p_f,p1)` → `build_l1_sampler` once → callable →
  tiny-invocation `(k,32)` finite-normalized-centered proof in zero-call
  contract test (never a V26 `DE` call). Evidence: `design.md` §10.2 +
  `REQ-DE-R2-02`.
- [ ] **R202 L2 oracle adapter** — `p2` once via `conditionalize_f_to_p2`;
  joint `pb[B]*p_f[A,B]` sampling; `u1=A//32`, `u2=A%32`; prior EXCLUSIVELY
  via `oracle_l2_prior(p2,B,u1)`; D9/D5 floor-normalize; XOR-center on true
  `u2`; fail-closed; V36/V37 forbidden with reason. Evidence: §10.3 +
  `REQ-DE-R2-03`.
- [ ] **R203 profile dispatch** — L1 profiles ← L1 callable only; L2 ← L2
  callable only; frozen-plan-profile selection before every `run_de_call`;
  unknown/mislabelled fail pre-scientific-call; DI preserved for fakes but
  channels explicit; single shared callable forbidden. Evidence: §10.4 +
  `REQ-DE-R2-04`.
- [ ] **R204 freeze check** — 15 points, seeds `2026094201..08`, pops
  `4000/16000`, lambda/rho, kernel `60/1e-4/20`, bracket/flag/`delta_DE`
  rules, plan order, `240/12` ceilings + resource budgets, claim ceiling,
  banned D16 — all unchanged. Evidence: §10.5 + `REQ-DE-R2-05`.
- [ ] **V1–V7 validation** — (1) A1 mechanical reproduction from persisted
  evidence; (2) zero-call binder resolution; (3) stub-loader
  unpack/build/invoke/non-identical-rows proof; (4) 240-row fake dispatch with
  swapped/missing/tuple/unknown/shape/nonfinite failures; (5) real-chain
  zero-call spy with L2-mixer hit + `run_de_call` count zero; (6) `py_compile`
  + focused tests in fresh basetemp; (7) scoped repair review. One correction
  within `R201–R203`, contract unchanged, failed attempt in log. Evidence:
  §10.6 + `REQ-DE-R2-06`. Any blocker → STOP before rerun.
- [ ] **A2 fresh rerun** — fresh root
  `workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24`
  (absent); exact frozen command; `240/12/1200s/300s/2GiB/1-proc`; no
  retry/resume/extension/search/adaptive/second-repair. Evidence: §10.7 +
  `REQ-DE-R2-07`.
- [ ] **P1–P8 pre-dispatch** — append raw evidence to the one D17 log (A1
  `VERIFIED/PASS` + error + `0/240` + grant + six-file root; branch + scoped
  diff; A2/D16 absence + Model-F unchanged; tests + repair review PASS; frozen
  matrix equality; `PROFILE_ONLY` + refusal checks; zero-call dual-dispatch
  proof; command + unused grant). Any failure → STOP. Evidence: §10.8.
- [ ] **Batch-end review + terminal** — independent scope per §10.9
  (provenance, recount 240, dispatch confirm, convergence/`delta_DE`
  recompute, verifier, D16/Model-F/no-decoder checks, ceilings,
  `EVIDENCE_ACCESS` in log). Return
  `D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION` or one
  `D17_DE_R2_*_BLOCKED_AWAITING_DECISION`. No fit/D16/route/claim follow-on.

## A3-spec amendment (this call, planner, OpenSpec-only)

- [x] **A3-SPEC** Amend this change (`design.md` new §11 + `specs/de-scaling/spec.md`
  A3 deltas `REQ-DE-A3-01..08` + this task list): record main-thread acceptance
  of `D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION` (stated in the
  authorizing prompt) + A3 one-shot grant scope (minimal entrypoint, six named
  roots read-only, one deterministic fit, outcome-blank predictions, one
  batch-end review; no `DE`/decoder call; `D16` execution unauthorized); freeze
  the `--scaling-fit --execution-authorized` entrypoint contract
  (default-false refusal pre-output/input-reads, never-overwrite), the exact
  frozen command naming the A2 `DE` root + five finite roots in fixed order +
  fit root `workspace/d17_finite_scaling_fit_5b6d71c8-9e42-4e64-b1c3-73a1f20d8e95`
  (absence verified this call; no glob discovery; byte-identical in
  code/OpenSpec/log/prompt), budgets (zero `DE`/decoder/`CAL`/`VAL`, six
  inputs, `300s` wall, `RSS<2GiB`, 1 proc, no retry/resume/tuning), the §3
  aggregation / §4 fit / §5 backoff / §6 prediction-freeze contracts, fixed
  `delta_DE/h` (L045 `0.24452956979862517`/`0.078125`; L055
  `0.30312331979862517`/`0.05859375`; L2 `0.5468113653656221`/`0.09765625`),
  pre-dispatch 1–5 + review scope + three §9 terminals. Authority:
  `.workbuddy/tasks/D17_SCALING_FIT_AND_D16_PREDICTION_FREEZE_A3_TASK_PACKET.md`
  §§1–9. Zero scientific calls; no code/scripts/tests/roots edits; no
  commit/push. Branch `formal-ir-v72p1-addendum-clean` unchanged. Absence
  re-verified this call: fit root `File not found`; `D16` official root
  `File not found`.

## A3 scaling fit + prediction freeze (packet §§2–9 — [ ] future operator work, not this call)

Each needs the packet + companion prompt authorization; the single fit
additionally needs pre-dispatch PASS. `EXPLORE` one-shot grant.

- [ ] **A3-IMPL fit/verify path** — smallest fit/verify addition to the existing
  `D17` module, runner (`--scaling-fit` per §11.3 frozen command), and focused
  tests; no new dependency or modeling framework. Evidence: §11.3 +
  `REQ-DE-A3-03`.
- [ ] **A3-AGG aggregation** — actual decoder/arm records → one binomial cluster
  per `(source_root,profile,n,m,graph_seed)` (`y=exact`, `t=blocks`);
  root+graph identity; no pooling/duplication/replay/syndrome-merge; `delta`
  recomputed (mismatch STOP); frozen decoder semantics + one class per cluster;
  `D16`/banned/fake contact STOP; reconcile to accepted totals pre-fit.
  Evidence: §11.4 + `REQ-DE-A3-04`.
- [ ] **A3-FIT fit + uncertainty** — fixed `delta_DE`; ladder two-param →
  `beta=0` → `MODEL_NOT_IDENTIFIABLE`; L2 predeclared one-param; cluster
  likelihood + deterministic search; bootstrap+`LOO` (+leave-one-root-out for
  L045/L055, union prediction); logistic descriptive-only; residuals excluded.
  Evidence: §11.5 + `REQ-DE-A3-05`.
- [ ] **A3-BACKOFF row-backoff report** — frozen inversion at n=64/128/256,
  epsilon 0.10/0.01, point + union integer intervals, `m*(0.01)>=m*(0.10)`,
  diagnostic labeling. Evidence: §11.6 + `REQ-DE-A3-06`.
- [ ] **A3-PRED prediction freeze** — `D16` root absent proof; exactly 3 arms
  L045/L055/L2-ORACLE n128 m125/m94; provenance/uncertainty/union content;
  `expected_graph_dispersion` object (`binomial_8_trial_interval_95` +
  `empirical_graph_residual_range_descriptive`); `pool/per_graph/exact/
  syndrome/undetected/terminal` exactly `BLANK`; falsification rule;
  never-revise-after-observed. Evidence: §11.7 + `REQ-DE-A3-07`.
- [ ] **A3 pre-dispatch 1–5** — A2 review accept + bracket recompute; six inputs
  present/read-only + fit/`D16` absent; frozen root list/command + no
  `D16`/fake/banned identity; `py_compile` + focused tests (recovery,
  non-identifiable terminal, graph-not-row, `APP`/undetected isolation,
  refusal, no-overwrite, prediction-blank, fake full fit); zero calls + unused
  grant in the single `D17` log. Any failure → STOP. Evidence: §11.8.
- [ ] **A3 batch-end review + terminal** — independent scope per §11.8
  (aggregation, accepted totals, fixed `delta_DE`, likelihood/ladder,
  uncertainty, inversion, bands/dispersion, blank gate, verifier, resources,
  input immutability; one review in the `D17` log). Return exactly
  `D17_SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN_AWAITING_D16_AUTHORIZATION` on
  full identify+freeze,
  `D17_SCALING_MODEL_NOT_IDENTIFIABLE_AWAITING_ROUTE_DECISION` on any
  non-identifiable model (diagnostics only, no filled predictions), or
  `D17_SCALING_FIT_ENGINEERING_BLOCKED_AWAITING_DECISION` on
  engineering/review failure. No `D16`/`DE`/decoder/real-data/`D7-H`/
  `FER`/leakage/`SKR`/qualification/optimality/publication/route-closure
  follow-on.
