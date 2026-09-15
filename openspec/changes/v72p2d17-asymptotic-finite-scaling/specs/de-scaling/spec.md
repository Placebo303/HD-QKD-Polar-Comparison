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
