# D17 Current-Channel Asymptotic-to-Finite Scaling — Readiness R1

## 1. Identity and boundary

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Change: `v72p2d17-asymptotic-finite-scaling`
- Future scientific work: `EXPLORE`; this packet is implementation/readiness.
- D16 execution is superseded and unauthorized. Its exact m125/m94 cells,
  seeds and root are reserved as a held-out validation set and must not be read
  as outcomes because no root exists.
- This packet authorizes OpenSpec, read-only predecessor audit, model/runner
  implementation, fake/reduced PROFILE_ONLY tests, independent review and a
  scoped local commit. It authorizes zero scientific DE/decoder calls.
- No real data, FER qualification, D7-H, finite D16 run, push or route closure.

## 2. Scientific model hierarchy

Use this order and do not collapse its levels:

1. **Information limit**: actual candidate-generator conditional entropy
   `H_l` and disclosure gap
   `delta = 5m/n - H_l` in bits/symbol.
2. **Asymptotic BP/ensemble limit**: current-channel MC-DE threshold for each
   frozen ensemble/profile, expressed as `delta_DE` or equivalent rate.
3. **Finite-length statistical backoff**: an explicit predeclared scaling law
   mapping `(n, delta-delta_DE)` to block failure probability.
4. **Finite graph/decoder residual**: rank, cycles, trapping/absorbing behavior,
   schedule and convergence deviations measured after the scaling prediction.

DE convergence is not finite-code usability. The scaling law is an empirical
calibration for this channel/decoder family, not a universal theorem.

## 3. A01–A05 predecessor audit

- **A01 channel identity**: prove exact Model-F candidate prior/generator,
  axes, floor/renormalization and L1/L2 marginal/conditional channels used by
  D8–D16. Record any channel mismatch; do not combine incompatible evidence.
- **A02 DE inventory**: map V25/V26/V27 and D8/D9 by channel, layer, profile,
  rate definition, population, iterations and convergence metric. State exactly
  which V26 f1.3 conclusions transfer and which do not.
- **A03 finite inventory**: create one table from D10–D15 with n, layer,
  profile, rows, exact `delta`, graphs, blocks, exact/syndrome/undetected and
  decoder settings. Preserve graph clusters and root identity; never treat
  individual decoder rows as independent graphs.
- **A04 compatibility classes**: mark observations eligible for fitting,
  validation-only, or descriptive-only. Exclude APP/joint outcomes from the
  single-layer fit. L2 ORACLE may fit only the true-conditioned L2 model.
- **A05 D16 holdout lock**: record D16 inputs/seeds/root/command, prove its root
  absent, and prohibit those seeds from fitting or DE tuning.

## 4. B01–B05 current-channel asymptotic DE readiness

- Reuse the accepted V26 MC-DE kernel and D9 semantic adapter; no new DE kernel.
- Profiles: L1 L045, L1 L055 and L2 DV3 true-conditioned, each on the exact
  current candidate channel used by D15/D16.
- Parameterize rate by `delta` and derive ensemble rho from the exact rate;
  never use legacy CE labels as the independent variable.
- Planner must freeze a bounded coarse-plus-confirmation grid sufficient to
  bracket each profile's convergence transition. Grid points and confirmation
  seeds are fixed before execution; no outcome-driven extension or binary
  search. Include population-size stability at the selected bracket.
- Emit full trajectory summaries needed to define convergence, but make no
  DE↔row-layered trajectory equivalence claim beyond D9's certified primitives.
- Prepare a future DE batch command/root/budget with default-false authorization,
  PROFILE_ONLY and read-only verifier. Leave it absent and unauthorized.

## 5. C01–C07 finite-length scaling model

Implement the simplest predeclared model that can be falsified by D16:

```text
p_success(n, delta) = Phi((delta - delta_DE - beta*n^(-2/3)) * sqrt(n/alpha))
```

- Fit separately for L1 L045, L1 L055 and L2 DV3 ORACLE.
- `delta_DE` comes from the reviewed current-channel DE result; do not freely
  refit it to finite data. Fit `alpha>0` and `beta` using binomial likelihood
  with graph-cluster bootstrap or leave-one-graph-out uncertainty.
- If the available compatible widths/points cannot identify both parameters,
  downgrade explicitly to a one-parameter model (fix beta=0) or
  `MODEL_NOT_IDENTIFIABLE`; never report unstable coefficients as a correction.
- Compare probit against one logistic-link sensitivity fit, descriptive only.
  No generalized modeling framework or new dependency is required; NumPy and
  standard-library optimization/grid search are sufficient.
- Diagnostic target block-failure probabilities are `epsilon=0.10` primary and
  `epsilon=0.01` sensitivity. They are modeling targets, not project FER
  qualification requirements. Report the implied integer row backoff at
  n=64/128/256 with uncertainty intervals.
- Before any D16 execution, persist predictions for all three D16 arms:
  predicted success interval, expected graph dispersion, and falsification
  criteria. Do not revise them after observing D16.
- Separate residual diagnostics: rank/admission, four-cycles/girth, iterations,
  residual syndrome and graph random effects. These may explain deviations but
  are not folded into the universal backoff term without a new preregistration.

## 6. D01–D07 implementation and review

- **D01 OpenSpec first** with equations, units, data eligibility, DE grid,
  model identifiability, uncertainty and holdout rules.
- **D02 audit artifact**: compact CSV/JSON inventory plus report; read-only
  predecessor roots.
- **D03 DE adapter/runner**: current-channel three-profile plan, fake-injected
  tests, authorization refusal, fresh root and verifier; zero scientific calls.
- **D04 scaling module**: aggregate by graph and cell; exact binomial counts;
  deterministic fit/uncertainty; synthetic recovery tests against known
  parameters and non-identifiable fixtures.
- **D05 holdout record**: immutable D16 prediction schema and blank outcome
  fields; fail if D16 root exists before prediction freeze.
- **D06 focused validation**: compile, math/channel equivalence, plan/grid,
  fake DE, fit recovery, eligibility isolation, root absence and no-production.
- **D07 independent review**: actual artifact access; independently verify
  channel/DE identity, finite-data eligibility, equations/units, grid/budgets,
  identifiability logic, target-row inversion, D16 holdout isolation and zero
  scientific calls.

## 7. STOP conditions

STOP without scientific execution if:

- current L1/L2 channel identity cannot be made exact;
- required finite records cannot be joined without pooling incompatible roots;
- D16 root exists or its reserved identities appear in fit data;
- DE grid is outcome-adaptive or cannot bracket all three profiles within a
  bounded preregistration;
- model units/signs do not reproduce known monotonic limits;
- reviewer finds a blocking channel, eligibility, identifiability or holdout
  error.

Do not solve a STOP by running D16, adding graph searches or changing the model
after looking at held-out outcomes.

## 8. Return contract

Return only:

`D17_DE_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION`

with:

- V25–V27/D8–D16 channel-and-rate compatibility map;
- eligible finite dataset table and exclusions;
- exact three-profile DE grid, seeds, convergence rule, command/root/budgets;
- scaling equation, identifiability decision, uncertainty method and target
  epsilon interpretation;
- D16 holdout lock and prediction-record schema, still outcome-blank;
- tests/profile/fake/verifier and independent verdict;
- zero scientific calls, future roots absent, commit/no-push state.

Do not issue DE or D16 execution authorization. After acceptance, the main
thread will first authorize the asymptotic DE batch; scaling fit and frozen D16
prediction follow its reviewed result. D7-H remains closed.
