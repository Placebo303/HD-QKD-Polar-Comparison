# Spec — DE-to-finite scaling (delta requirement set)

Scope: `D17` readiness freeze (planner, no code). Normative language
(`SHALL`/`SHALL NOT`) binds `D02–D07` implementation and `D07` review. Packet
§§2/5/7 take precedence on any conflict; STOP rules are fail-closed.

## Channel and rate definitions

- REQ-DE-SCALE-01: The channel SHALL be the exact Model-F candidate channel:
  estimator `prepare_model_f_prior_candidate`/`build_f_model_concentration`,
  `LAMBDA_STAR=137.3823795883263870`, floor `max(p,1e-300)` pre-`log2` without
  renormalization, axes `p_f(Alice=1024,Bob=1024)`, `A=32*U1+U2`,
  `H_L1=4.286720430201375`, `H_L2=3.222719884634378` bits/symbol.
- REQ-DE-SCALE-02: Rate SHALL be parameterized by `delta = 5m/n − H_l`
  (bits/symbol) with generator `H_l`. Legacy `CE` labels SHALL NOT be used as
  the independent variable anywhere.
- REQ-DE-SCALE-03: Ensemble `rho` SHALL be derived from the exact `(n,m)` by
  the frozen `D9` rule (largest-remainder node counts + concentrated
  floor/ceil check allocation). `D8/D9` numeric thresholds and `V25/V26/V27`
  domain numbers SHALL NOT enter as evidence.

## Scaling model

- REQ-DE-SCALE-04: The fitted law SHALL be exactly
  `p_success(n,delta) = Phi((delta − delta_DE − beta·n^(−2/3))·sqrt(n/alpha))`
  with `alpha > 0`, fit separately for L1 L045, L1 L055, L2 DV3 ORACLE.
- REQ-DE-SCALE-05: `delta_DE` SHALL come only from the reviewed
  current-channel `DE` result under the frozen §4 convergence rule and SHALL
  NOT be refit to finite data.
- REQ-DE-SCALE-06: Likelihood SHALL be exact per-graph-cluster binomial with
  graph + root identity retained; decoder rows SHALL NOT be treated as
  independent graphs.
- REQ-DE-SCALE-07: Uncertainty SHALL combine graph-cluster bootstrap AND
  leave-one-graph-out refits (report both, predict with the wider); `D16`
  prediction bands SHALL union the `delta_DE ± h` granularity sensitivity.
- REQ-DE-SCALE-08: Identifiability ladder SHALL be two-parameter →
  one-parameter (`beta=0`) → `MODEL_NOT_IDENTIFIABLE`; L2 DV3 ORACLE SHALL
  default to one-parameter primary. Unstable coefficients SHALL NOT be
  reported as a correction.
- REQ-DE-SCALE-09: The logistic-link fit SHALL be descriptive-only; no model
  selection between links.
- REQ-DE-SCALE-10: `epsilon=0.10/0.01` SHALL be treated as diagnostic modeling
  targets (never `FER` qualification); row backoff SHALL be reported as
  integers at `n=64/128/256` with uncertainty intervals via the frozen
  inversion (`design.md` §2).

## DE grid

- REQ-DE-SCALE-11: The `DE` batch SHALL run exactly the 15 frozen
  (profile, `m`) points (`design.md` §4) at pops `{4000, 16000}` with seeds
  `2026094201..4208` — `240` calls + setup `≤12`, budgets
  `≤1200 s / ≤300 s / <2 GiB / 1-proc`, no retry/resume/seed-search/adaptive.
- REQ-DE-SCALE-12: No outcome-driven grid extension, binary search, or seed
  replacement SHALL occur; one-sided/soft-bracket/population flags SHALL be
  recorded per the frozen edge rules, never re-gridded.

## Data eligibility and holdout

- REQ-DE-SCALE-13: `APP`/joint outcomes SHALL be excluded from every
  single-layer fit; `L2 ORACLE` data SHALL enter only the true-conditioned
  `L2` model; non-`D17` profiles SHALL be descriptive-only.
- REQ-DE-SCALE-14: Fit inputs SHALL fail closed on any banned-`D16`-seed
  presence (`2026094001..4012`, `2026094101..4108`) and on any row sourced
  from `workspace/d16_align_20260915_a/` fake scratch or the `D16` official
  root.
- REQ-DE-SCALE-15: `D16` predictions for all three arms (interval, expected
  graph dispersion, falsification criteria) SHALL be persisted outcome-blank
  before any `D16` execution and SHALL NOT be revised after observing `D16`;
  the `D05` implementation SHALL fail if the `D16` root exists before
  prediction freeze.

## Residuals, limits, ceiling

- REQ-DE-SCALE-16: Rank/admission, four-cycles/girth, iterations, residual
  syndrome, and graph random effects SHALL be measured post-prediction and
  SHALL NOT enter the backoff term without a new preregistration.
- REQ-DE-SCALE-17: Implementation SHALL reproduce the frozen monotonic limits
  (`design.md` §2); violation SHALL STOP the line.
- REQ-DE-SCALE-18: Results SHALL be stated as empirical calibration for this
  channel/decoder family (no universal theorem, no `FER` qualification, no
  `D7-H`/route-closure claim). `D16` execution and the `DE` batch SHALL each
  require separate explicit authorization.

## R2 binding repair + rerun (A1 failure reference; packet precedence)

Scope: `R201–R204` engineering repair + `V1–V7` validation + `A2` fresh rerun.
Normative language binds the R2 operator and reviewer. Packet
`D17_DE_BINDING_REPAIR_R2_AND_RERUN_TASK_PACKET.md` §§2/4/5 takes precedence
on any conflict. `design.md` §10 is the frozen R2 elaboration. A1 (`0/240`,
`DE_CALL_FAILED@0` tuple-not-callable) supplies failure reference only.

- REQ-DE-R2-01 (A1 immutability): The A1 root
  (`workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718`)
  SHALL remain read-only and SHALL NEVER be resumed, overwritten, repaired in
  place, or reused as `DE`/scaling-fit evidence beyond failure reference. A1
  SHALL contribute zero threshold/fit rows.
- REQ-DE-R2-02 (R201 L1 binding): The implementation SHALL call the accepted
  `load_l1_channel(model_f_root)` exactly once, require an exact three-item
  `(pb, p_f, p1)` finite shape-compatible result, call the bound
  `build_l1_sampler(pb, p_f, p1)` exactly once, require a callable return,
  and prove in a zero-scientific-call contract test that a tiny invocation
  returns finite normalized `(k,32)` centered rows. The tiny invocation SHALL
  NEVER count as a V26 `DE` call.
- REQ-DE-R2-03 (R202 L2 oracle): The implementation SHALL build `p2` exactly
  once via the bound `conditionalize_f_to_p2(p_f)`; sample `(A,B)` from the
  same `pb[B]*p_f[A,B]` joint as L1 with `u1=A//32`, `u2=A%32`; obtain the
  prior EXCLUSIVELY via the bound `oracle_l2_prior(p2, B, u1)`; apply the
  accepted D9/D5 floor-normalize convention; XOR-center each row on true `u2`.
  It SHALL fail closed on nonfinite/invalid mass, incompatible shapes,
  non-callable result, or any row not finite/normalized/`(k,32)`. V36/V37
  empirical-count samplers SHALL NOT be reused (wrong source channel).
- REQ-DE-R2-04 (R203 dispatch): `L1_L045`/`L1_L055` SHALL receive only the L1
  callable and `L2_DV3_ORACLE` SHALL receive only the L2 callable; dispatch
  SHALL be selected from the frozen plan entry's profile before every
  `run_de_call`; unknown/mislabelled profiles SHALL fail before any scientific
  call. Dependency injection for fakes SHALL keep channels explicit; a single
  callable silently shared by all three production profiles SHALL NOT exist.
- REQ-DE-R2-05 (R204 freeze): The 15 points, seeds `2026094201..4208`, pops
  `4000/16000`, lambda/rho construction, V26 kernel (`60/1e-4/20`),
  bracket/flag/`delta_DE` rules, plan order, `240/12` ceilings, resource
  budgets, claim ceiling, and banned D16 identities SHALL remain exactly per
  `design.md` §§4/10.5. No scientific change under R2 repair.
- REQ-DE-R2-06 (validation + one correction): `V1–V7` per `design.md` §10.6
  SHALL all pass with zero scientific calls and no official R2 root write
  before rerun; any blocker SHALL STOP before rerun. At most one correction
  within `R201–R203` with unchanged `R204` and retained failed attempt SHALL
  be allowed before the reviewer closes the repair.
- REQ-DE-R2-07 (A2 + gates + terminals): The A2 root
  (`workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24`)
  SHALL be absent at pre-dispatch; the exact frozen command SHALL run at most
  once with exactly 240 scientific calls, setup `≤12`, `≤1200 s / ≤300 s /
  <2 GiB / 1-proc`, no retry/resume/extension/search/adaptive/second-repair.
  Pre-dispatch `P1–P8` and the batch-end review per `design.md` §§10.8–10.9
  SHALL pass; review failure SHALL block use of A2 evidence with no rerun.
  Return SHALL be exactly
  `D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION` on pass or one
  exact `D17_DE_R2_*_BLOCKED_AWAITING_DECISION` terminal on any failure.

## A3 finite-length scaling fit + D16 prediction freeze (packet §§1–9 precedence)

Scope: one-shot `EXPLORE` fit-execution amendment. Normative language binds
the A3 operator and reviewer. Packet
`D17_SCALING_FIT_AND_D16_PREDICTION_FREEZE_A3_TASK_PACKET.md` §§3/4/5 takes
precedence on any conflict. `design.md` §11 is the frozen A3 elaboration. No
`DE`/decoder call is authorized; `D16` execution remains unauthorized.

- REQ-DE-A3-01 (acceptance + grant): Main-thread acceptance of
  `D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION` SHALL be recorded
  (stated in the authorizing prompt). The A3 grant SHALL cover ONLY the minimal
  fit entrypoint, read-only ingestion of the six §11.2 roots, one deterministic
  fit, persistence of outcome-blank `D16` predictions, and one independent
  batch-end review.
- REQ-DE-A3-02 (inputs + brackets): `delta_DE`/`h` SHALL be fixed exactly to
  L045 `0.24452956979862517`/`0.078125`, L055 `0.30312331979862517`/
  `0.05859375`, L2-ORACLE `0.5468113653656221`/`0.09765625`, recomputed from
  the A2 `DE` root before fitting; literal/root disagreement SHALL STOP, with
  no averaging, refitting, or `D8`/`D9`/`V26` substitution. Finite inputs SHALL
  be exactly the five §11.2 roots in fixed order with the §11.2 eligibility
  classes (L045: `D10`/`R3`/`D12`/`D14N`/`D15`; L055: `D12`/`D14N`/`D15`;
  L2-ORACLE true-`U1`: `D14N`/`D15` only; controls/L050/`APP`/joint/`D11`/
  `D13`/`D16`/fake/`DE`/changed-decoder outcomes excluded).
- REQ-DE-A3-03 (entrypoint + command + budgets): The implementation SHALL add
  only the smallest fit/verify path to the existing `D17` module, runner, and
  focused tests, exposing exactly the §11.3 frozen command (fail-closed
  `--scaling-fit --execution-authorized`, default-false refusal before output
  creation and input reads, never-overwrite, no glob discovery, byte-identical
  in code/OpenSpec/log/prompt). The fit SHALL consume zero `DE`/decoder/`CAL`/
  `VAL` calls, exactly six input roots, wall `≤300 s`, `RSS <2147483648` bytes,
  one CPU process, no retry/resume/tuning. Evidence SHALL be manifest,
  graph-cluster table, fit/uncertainty result, row-backoff table, three
  outcome-blank prediction `JSON` files when all models identify, command log,
  plus a read-only verifier recomputing aggregation/selection/intervals/
  predictions/blank-gate.
- REQ-DE-A3-04 (aggregation): Clusters SHALL be exactly one binomial
  `(y=exact,t=blocks)` per `(source_root,profile,n,m,graph_seed)` from actual
  decoder/arm records (never pooled totals), with root+graph identity
  preserved; pooling graphs, row-as-cluster treatment, `D11`-replay
  duplication, and exact+syndrome/undetected merging SHALL NOT occur.
  `delta=5m/n-H_layer` SHALL be recomputed from accepted generator entropy
  (mismatch STOP). Every cluster SHALL carry frozen decoder semantics and
  exactly one eligibility class; `D16`/banned/fake contact SHALL STOP. Counts
  SHALL reconcile to accepted `D10`/`R3`/`D12`/`D14N`/`D15` totals pre-fit.
- REQ-DE-A3-05 (fit + uncertainty): The law SHALL be exactly
  `p_success(n,delta)=Phi((delta-delta_DE-beta*n^(-2/3))*sqrt(n/alpha))` with
  `delta_DE` fixed (never optimized); ladder SHALL be two-parameter →
  `beta=0` → `MODEL_NOT_IDENTIFIABLE`, with L2-ORACLE predeclared one-parameter
  (`beta=0`, all n=128); likelihood SHALL be exact graph-cluster binomial with
  the reviewed deterministic search. Every identifiable final model SHALL get
  cluster bootstrap AND leave-one-graph-out (L045/L055 additionally
  leave-one-root-out incl. `D14N`-vs-`D15`); prediction SHALL use the wider
  union. Logistic-link SHALL be descriptive-only. Residuals SHALL NOT enter the
  fit. Any `MODEL_NOT_IDENTIFIABLE` final model SHALL persist diagnostics only
  with no filled predictions.
- REQ-DE-A3-06 (backoff): Row backoff SHALL follow the frozen inversion
  (`delta*`/`m*`/`backoff` per `design.md` §11.6) at n=64/128/256 and epsilon
  0.10/0.01 with point + wider uncertainty-union integer intervals, requiring
  `m*(0.01)>=m*(0.10)`, labeled diagnostic (never `FER` qualification).
- REQ-DE-A3-07 (prediction freeze): Only if all three profiles identify, the
  operator SHALL prove the `D16` official root
  (`workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`)
  absent and fill exactly L045 n128/m125, L055 n128/m125, L2-ORACLE n128/m94
  with `DE`-root/bracket provenance, model/identifiability, coefficient
  uncertainty, and the fit-uncertainty ∪ `{delta_DE-h,delta_DE,delta_DE+h}`
  union. `expected_graph_dispersion` SHALL be an object with deterministic
  `binomial_8_trial_interval_95` + descriptive
  `empirical_graph_residual_range_descriptive` (never altering the fit).
  `pool/per_graph/exact/syndrome/undetected/terminal` SHALL be exactly `BLANK`.
  Falsification SHALL be pool-outside-95% → `FALSIFIED`, inside →
  `NOT_FALSIFIED`, engineering violation → `INCONCLUSIVE`, graph range
  descriptive; prediction files SHALL NEVER be revised after `D16` is observed.
- REQ-DE-A3-08 (gates + terminals): Pre-dispatch 1–5 and the independent review
  per `design.md` §11.8 SHALL pass (recomputing aggregation, accepted totals,
  fixed `delta_DE`, likelihood/ladder, uncertainty, inversion, bands/
  dispersion, blank gate, verifier, resources, input immutability; one review
  appended to the single `D17` log). Return SHALL be exactly
  `D17_SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN_AWAITING_D16_AUTHORIZATION` on
  full identify+freeze,
  `D17_SCALING_MODEL_NOT_IDENTIFIABLE_AWAITING_ROUTE_DECISION` on any
  non-identifiable model (diagnostics only, no filled predictions), or
  `D17_SCALING_FIT_ENGINEERING_BLOCKED_AWAITING_DECISION` on
  engineering/review failure.
