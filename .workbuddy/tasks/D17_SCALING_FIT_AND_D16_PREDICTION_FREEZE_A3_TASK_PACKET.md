# D17 Finite-Length Scaling Fit + D16 Prediction Freeze — A3 Task Packet

## 1. Identity, acceptance, and authorization

- Repository: `HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Change: `v72p2d17-asymptotic-finite-scaling` (additive fit-execution amendment)
- Batch: `D17_SCALING_FIT_AND_D16_PREDICTION_FREEZE_A3`
- Track: `EXPLORE`
- Accepted DE evidence:
  `D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION`.
- This packet and its companion prompt authorize the minimal fit entrypoint,
  read-only ingestion of the named finite roots and reviewed A2 DE root, one
  deterministic fit, persistence of outcome-blank D16 predictions, and one
  independent batch-end review.
- No DE or decoder call is authorized. D16 execution remains unauthorized.

## 2. Frozen inputs

### Reviewed asymptotic input

- DE root, read-only:
  `workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24`
- Fix `delta_DE` and local half-step `h` exactly to its independently reviewed
  brackets:
  - L045: `delta_DE=0.24452956979862517`, `h=0.078125`;
  - L055: `delta_DE=0.30312331979862517`, `h=0.05859375`;
  - L2 DV3 ORACLE: `delta_DE=0.5468113653656221`, `h=0.09765625`.
- Recompute them from the DE root before fitting. Literal/root disagreement is
  STOP; never average, refit, or substitute a D8/D9/V26 number.

### Finite roots, all read-only

- `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`
- `workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`
- `workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`
- `workspace/v72p2d14_discriminator/20260914_r1`
- `workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2`

Eligibility is exactly the accepted D17 table: L045 single-layer rows from
D10/R3/D12/D14N/D15; L055 single-layer rows from D12/D14N/D15; true-U1
L2-ORACLE rows from D14N/D15 only. Exclude controls, L050, APP/joint, D11,
D13, D16, fake scratch, DE records, and every outcome with a changed decoder.

## 3. Exact aggregation contract

- Read actual finite decoder/arm records, not the readiness table's pooled
  totals.
- Join each decoder row to its graph/cell metadata and aggregate to exactly one
  binomial cluster per `(source_root,profile,n,m,graph_seed)` with `y=exact`,
  `t=blocks`.
- Preserve root and graph identity. Never pool graphs, treat decoder rows as
  independent clusters, duplicate D11 replay rows, or combine exact with
  syndrome-valid/undetected.
- Recompute `delta=5m/n-H_layer` from the accepted generator entropy;
  stored-vs-recomputed mismatch is STOP.
- Every included cluster needs the frozen decoder semantics and exactly one
  eligibility class. D16/banned identities or fake scratch contact is STOP.
- Reconcile aggregated counts to accepted D10/R3/D12/D14N/D15 totals before
  fitting.

## 4. Frozen fit and uncertainty contract

```text
p_success(n,delta) = Phi((delta-delta_DE-beta*n^(-2/3))*sqrt(n/alpha))
```

- `delta_DE` is fixed from §2 and never optimized.
- L045/L055: two-parameter `(alpha>0,beta)` first, then the reviewed ladder to
  `beta=0`, then `MODEL_NOT_IDENTIFIABLE` if necessary.
- L2 DV3 ORACLE: predeclared one-parameter primary with `beta=0`; all eligible
  observations are n=128.
- Use exact graph-cluster binomial likelihood and the reviewed deterministic
  search.
- Every identifiable final model gets cluster bootstrap and leave-one-graph-out
  uncertainty. L045/L055 also get leave-one-root-out sensitivity, especially
  D14N-vs-D15. Prediction uses the wider union.
- Logistic-link fit is descriptive only and cannot change the selected model,
  `delta_DE`, or D16 predictions.
- Graph/rank/cycle/iteration/syndrome residuals cannot enter the fit.

If any final model is `MODEL_NOT_IDENTIFIABLE`, persist diagnostics but do not
create filled D16 predictions. Return the explicit terminal in §9; do not
substitute another model.

## 5. Row-backoff report

- For each identifiable profile at n=64/128/256 and epsilon 0.10/0.01:

```text
delta* = delta_DE + beta*n^(-2/3) + z_(1-eps)*sqrt(alpha/n)
m* = ceil(n*(H_layer+delta*)/5 - 1e-9)
backoff = m* - ceil(n*H_layer/5)
```

- Report point and wider uncertainty-union integer intervals; require
  `m*(0.01)>=m*(0.10)`.
- These are diagnostic modeled backoffs, not FER qualification targets.

## 6. D16 prediction freeze

Only if all three profiles identify:

- Prove the D16 official root absent:
  `workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`.
- Fill exactly L045 n128/m125, L055 n128/m125, and L2-ORACLE n128/m94.
- Persist DE-root/bracket provenance, model and identifiability, coefficient
  uncertainty, and prediction union over fit uncertainty and
  `{delta_DE-h,delta_DE,delta_DE+h}`.
- `expected_graph_dispersion` is an object with a deterministic model-based
  `binomial_8_trial_interval_95` and an
  `empirical_graph_residual_range_descriptive`. The latter does not alter the
  universal backoff fit.
- Keep `pool/per_graph/exact/syndrome/undetected/terminal` exactly `BLANK`.
- Frozen falsification: pool outside the 95% band is `FALSIFIED`; inside is
  `NOT_FALSIFIED`; engineering violation is `INCONCLUSIVE`; graph range is
  descriptive. Prediction files are never revised after D16 is observed.

## 7. Minimal implementation, root, and command

Amend the existing OpenSpec first. Add only the smallest fit/verify path to the
existing D17 module, runner, and focused tests; no new dependency or modeling
framework.

- Fresh fit root:
  `workspace/d17_finite_scaling_fit_5b6d71c8-9e42-4e64-b1c3-73a1f20d8e95`
- Freeze a fail-closed `--scaling-fit --execution-authorized` command. It must
  refuse before output creation/input reads when unauthorized and never
  overwrite.
- The exact command must name the DE root, five finite roots, and fit root; no
  glob discovery. Freeze it identically in code, OpenSpec, log, and prompt.
- Budget: zero DE/decoder/CAL/VAL calls; exactly six input roots; wall ≤300 s;
  RSS <2147483648 bytes; one CPU process; no retry/resume/tuning.
- Minimal evidence: manifest, graph-cluster table, fit/uncertainty result,
  row-backoff table, three outcome-blank prediction JSON files when all models
  identify, and command log. A read-only verifier recomputes aggregation,
  model selection, intervals, predictions, and blank-outcome gate.

## 8. Pre-dispatch and independent review

Before the single fit:

1. Accept A2 review and recompute its three brackets from root.
2. Prove all six inputs present/read-only, fit root absent, D16 root absent.
3. Freeze exact root list/command; prove no D16/fake/banned identity in inputs.
4. Run `py_compile` plus focused tests covering parameter recovery,
   non-identifiable terminal, graph-not-row aggregation, APP/undetected
   isolation, refusal, no-overwrite, prediction-blank, and fake full fit.
5. Record zero scientific calls and unused grant in the single D17 log.

Afterwards one independent reviewer with artifact access recomputes aggregation,
accepted totals, fixed `delta_DE`, likelihood/ladder, uncertainty, inversion,
prediction bands/dispersion, blank gate, verifier, resources, and input
immutability. Append one review to the D17 log. Do not repeat predecessor suites
without a concrete conflict.

## 9. Return contract

All three identify and predictions freeze:

`D17_SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN_AWAITING_D16_AUTHORIZATION`

Any model not identifiable:

`D17_SCALING_MODEL_NOT_IDENTIFIABLE_AWAITING_ROUTE_DECISION`

Engineering/review failure:

`D17_SCALING_FIT_ENGINEERING_BLOCKED_AWAITING_DECISION`

Report reconciliation, cluster counts, fixed `delta_DE/h`, models and
uncertainty, logistic sensitivity, row backoffs, predictions/blank status,
command/resources, root/verifier/reviewer, grant and no-retry/commit/push state.

Do not run D16, DE, decoder, real data, D7-H, or make FER/leakage/SKR/
qualification/optimality/publication/route-closure claims.
