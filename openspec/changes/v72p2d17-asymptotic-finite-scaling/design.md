# Design — D17 Current-Channel Asymptotic-to-Finite Scaling (D01 freeze)

Authority: `D17` packet §§2–§7. All numbers below are frozen preregistration;
nothing here authorizes execution. Symbols: `Phi` = standard normal CDF,
`z_q` = its `q`-quantile.

## 1. Four-level hierarchy (never collapsed)

- **L1 information limit**: generator conditional entropy `H_l`
  (bits/symbol), disclosure `d = 5m/n`, gap `delta = d − H_l`.
  Frozen: `H_L1 = 4.286720430201375`, `H_L2 = 3.222719884634378`;
  n128 loads `548.700215065776 / 412.508145233200` bits.
- **L2 asymptotic ensemble limit**: current-channel `MC-DE` threshold per
  frozen ensemble/profile as `delta_DE` (or equivalent rate), from the §4 grid
  under the frozen convergence rule. Never refit to finite data.
- **L3 finite-length statistical backoff** (predeclared, falsifiable by `D16`):

```text
p_success(n, delta) = Phi((delta - delta_DE - beta*n^(-2/3)) * sqrt(n/alpha)),  alpha > 0
```

Fit separately for L1 L045, L1 L055, L2 DV3 ORACLE. `delta_DE` fixed from the
reviewed `DE` result; fit `(alpha, beta)` by exact binomial likelihood over
graph clusters (§6). `DE` convergence is not finite-code usability.

- **L4 finite graph/decoder residual**: rank/admission, four-cycles/girth,
  iterations, residual syndrome, graph random effects — measured AFTER the
  scaling prediction (§8); never folded into the backoff term without a new
  preregistration.

## 2. Units, signs, monotonic limits (STOP check)

- Units: `H_l, d, delta, delta_DE, beta·n^(−2/3)` in bits/symbol; `n, m, rows`
  integers (symbols / checks); `alpha` in bits²·symbols (so
  `(delta)·sqrt(n/alpha)` is dimensionless); `p_success`, `epsilon`
  dimensionless probabilities.
- Signs: `dp/d(delta) > 0` strictly; at fixed `delta > delta_DE`,
  `p → 1` as `n → ∞`; `delta < delta_DE → 0`; `delta = delta_DE` gives
  `Phi(−beta·n^(−1/6)/sqrt(alpha)) → Phi(0) = 0.5`.
- Inversion for diagnostic target block-failure `epsilon`:

```text
delta*(n, eps) = delta_DE + beta*n^(-2/3) + z_{1-eps}*sqrt(alpha/n)
m*(n, eps)     = ceil(n*(H_l + delta*)/5)
backoff(n, eps)= m* − m0,  m0 = ceil(n*H_l/5)
```

- Frozen baselines `m0`: L1 `n64→55, n128→110, n256→220`; L2 `n64→42,
  n128→83, n256→166` (n128 values coincide with the `D14N/D15` frozen rows —
  consistency check, not a fit). `epsilon=0.10` primary, `0.01` sensitivity:
  modeling targets only, never project `FER` requirements.
- If implementation/fit violates these limits (e.g. `alpha ≤ 0`,
  non-monotone `p` in `delta`), STOP per packet §7; never patch by
  redefining units.

## 3. Evidence delta table + eligibility (A03/A04)

`delta = 5m/n − H_l` (generator `H_l`; spot recompute verified in
`proposal.md`; `D02` re-verifies every cell from roots).

| # | Root | n | Layer/arm | m | d (bits/sym) | delta | Graphs×blocks (trials) | exact / synd / undet | Class |
|---|---|---|---|---|---|---|---|---|---|
| F1 | D10-A1 | 64 | L1 MIX-0.45 | 59 | 4.609375 | +0.32265 | 3×8 (24) | 20/20/0 | FIT L045 |
| F2 | D10-A1 | 64 | L1 DV3 | 59 | 4.609375 | +0.32265 | 3×8 (24) | 1/1/0 | descriptive (non-D17 profile) |
| F3 | D10-A1 | 128 | L1 MIX-0.45 | 118 | 4.609375 | +0.32265 | 3×8 (24) | 10/10/0 | FIT L045 |
| F4 | D10-A1 | 128 | L1 DV3 | 118 | 4.609375 | +0.32265 | 3×8 (24) | 0/0/0 | descriptive |
| F5 | D10-R3 | 128 | L1 MIX-0.45 | 118 | 4.609375 | +0.32265 | 6×12 (72) | 23/23/0 | FIT L045 (D02 row confirm) |
| F6 | D10-R3 | 128 | L1 DV3 | 118 | 4.609375 | +0.32265 | 6×12 (72) | 0/0/0 | descriptive |
| F7 | D10-R3 | 256 | L1 MIX-0.45 | 236 | 4.609375 | +0.32265 | 6×12 (72) | 29/29/0 | FIT L045 (D02 row confirm) |
| F8 | D10-R3 | 256 | L1 DV3 | 236 | 4.609375 | +0.32265 | 6×12 (72) | 0/0/0 | descriptive |
| F9 | D11 | 128/256 | L1 replay (=R3) | — | — | — | — | EQUAL R3 | validation-only (duplicate, no double count) |
| F10 | D11 | 128/256 | APP/joint + oracle | — | — | — | 288 transfers | J 22/23, 28/29; O 43/72, 64/72 | APP/joint EXCLUDED from fit; oracle validation-only (D02 true-conditioning audit) |
| F11 | D12 | 128 | L1 L045/L050/L055 | 118 | 4.609375 | +0.32265 | 6×12 (72/arm) | 26/39/42 | FIT L045 + FIT L055; L050 descriptive |
| F12 | D12 | 256 | L1 L045/L050/L055 | 236 | 4.609375 | +0.32265 | 6×12 (72/arm) | 33/35/46 | FIT L045 + FIT L055; L050 descriptive |
| F13 | D13 | 128/256 | L055 ladder (varied decoder) | — | — | — | 56 fail + 168 | rescues 3+1+0, und 0 | descriptive-only |
| F14 | D14N | 128 | L1 L045/L055 | 110 | 4.296875 | +0.01015 | 6×12 (72/arm) | 3/7, und 0 | FIT (leave-one-root-out sensitivity at D02) |
| F15 | D14N | 128 | L2-APP joint | 104 | — | — | 72 | 7 | EXCLUDED (APP/joint) |
| F16 | D14N | 128 | L2-ORACLE | 104 | 4.0625 | +0.83978 | 6×12 (72) | 63/63/0 | FIT L2 (leave-one-root-out sensitivity at D02) |
| F17 | D15 | 128 | L1 L045 | 110/114/118 | 4.29688/4.45313/4.60938 | +0.01015/+0.16640/+0.32265 | 4×8 (32/cell) | 0/6/19 | FIT L045 |
| F18 | D15 | 128 | L1 L055 | 110/114/118 | same | same | 4×8 (32/cell) | 1/13/22 | FIT L055 |
| F19 | D15 | 128 | L2-ORACLE | 83/86/89 | 3.24219/3.35938/3.47656 | +0.01947/+0.13666/+0.25384 | 4×8 (32/cell) | 0/0/0 | FIT L2 |
| H1-3 | D16 | 128 | L045/L055 m125; L2 m94 | 125/94 | 4.88281/3.67188 | +0.59609/+0.44916 | 4×8 (32/cell) | BLANK (held out) | validation-only (frozen predictions, §7) |

Join rule: FIT cells aggregate decoder rows to exact binomial counts `(y_g,
t_g)` per graph cluster `g`; graph identity + root identity retained as
grouping keys; `D02` join-key check per root (`model_f_root` +
candidate-chain estimator + decoder contract) before any pooling. `D12`
`CE`-f1.2 rows are same-generator disclosures (proposal `A01`-(i)), hence
joinable with cluster retention; `D15` packet §2 rate-change caveat is
satisfied exactly by the `delta` axis. `D02` must confirm `R3/D11` row counts
from manifests (provisional above).

## 4. Frozen DE grid (B; all points/seeds/rules fixed now — no outcome-driven change)

- Kernel: accepted V26 `MC-DE` + `D9` semantic adapter, unchanged
  (`max_iter=60`, `entropy_tol=1e-4` bits, `streak=20`); no new kernel.
- Channel: exact current candidate channel — L1 marginal `P1` for L045/L055;
  true-conditioned `P2|U1` oracle path for L2 DV3 (same adapters as `D15`).
- Rate: integer `m` at n128 reference; exact `R = 1 − m/128`;
  `d = 5m/128`; `delta = d − H_l`; ensemble `rho` derived from exact `(n,m)`
  by the frozen `D9` rule (largest-remainder node counts +
  concentrated check allocation `flo=floor(E/m)`, `b=E−flo·m` ceils,
  `a=m−b` floors) — never legacy `CE` labels. Node sides are
  `m`-independent: L045 `71/57/E313`, L055 `83/45/E301`, L2-DV3 `0/128/E384`.
  Worked: L045 m110 → `2^17+3^93` ✓ (matches `D14N`); L055 m122
  (`E=301`) → `2^65+3^57`; L2 m99 (`E=384`) → `3^12+4^87`. `D03` emits the
  full 15-cell table mechanically + verifier.
- Coarse-plus-confirmation (pop `4000` coarse + pop `16000` confirmation/
  stability, same 8 seeds throughout):

| Profile | m points | delta points | R points | Rationale |
|---|---|---|---|---|
| L1 L045 | 106, 110, 114, 118, 122 | −0.14610, +0.01015, +0.16640, +0.32265, +0.47890 | .171875–.046875 | brackets D9-converged `+0.323` from below |
| L1 L055 | 116, 119, 122, 124, 126 | +0.24453, +0.36172, +0.47890, +0.55703, +0.63515 | .09375–.015625 | D9 unconverged `@+0.323`; extends up; capped at lowest positive n128 rate (one-sided-high contingent) |
| L2 DV3 oracle | 89, 94, 99, 104, 109 | +0.25384, +0.44916, +0.64447, +0.83978, +1.03509 | .304688–.148438 | brackets finite `0/32 @+0.254` vs `63/72 @+0.840` |

- Seeds: `2026094201..4208` (8; repo-wide absence proven this call;
  disjoint from all priors and the banned `D16` `40xx/41xx` sets).
- Convergence (frozen): `S_pop = #{H60 < 1e-4}` over 8 seeds;
  `delta_DE` = midpoint of (highest-`delta` point with `S_16000 ≤ 3/8`,
  lowest-`delta` point with `S_16000 ≥ 6/8`). Edge rules: all `≥6/8` →
  `delta_DE ≤` lowest grid `delta` (`DE_ONE_SIDED_LOW`); all `≤3/8` →
  `delta_DE ≥` highest grid `delta` (`DE_ONE_SIDED_HIGH`; for L055 the cap
  `m126` is the physical `R ≥ 0` bound); soft middle counts use the nearest
  `≤3/≥6` pair (`DE_SOFT_BRACKET`). Pop4000/pop16000 bracket disagreement →
  `POP_UNSTABLE`, primary stays pop16000. Flags flow into uncertainty/ceiling;
  never trigger re-gridding.
- `delta_DE` granularity: half local grid step `h`; prediction intervals take
  the union over fits at `{delta_DE − h, delta_DE, delta_DE + h}`
  (predeclared sensitivity, §6).
- Trajectory summaries: per-call entropy traces (`de_traces` convention)
  recorded for the convergence definition; no `DE`↔row-layered trajectory
  claim beyond `D9` certified primitives.
- Budget: `3·5·8·2 = 240 DE` calls + setup `≤12`; wall `≤1200 s`,
  per-call `≤300 s` (checked between/after calls, never interrupted),
  `RSS < 2147483648 B`, 1 CPU proc, no retry/resume/seed-search/adaptive.
- Future batch (absent, unauthorized string only):

```text
.out-root workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718
```

Full: `.venv/bin/python scripts/v72p2d17_scaling_development.py --de-batch
--execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1
--out-root workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718`
(`D03` builds the runner with `--profile-only`/`--verify`, default-false auth,
refusal-before-root/bind/`Model-F`-load, read-only verifier; `D03` re-proves
root absence. Note: `D9` f1.0-`mu` gate criterion does not apply to `DE` grid
points — the grid intentionally spans sub-entropy disclosures to bracket.)

## 5. Identifiability logic (frozen)

- Attempt two-parameter `(alpha, beta)` fit per profile by default.
- Predeclared downgrade: L2 DV3 ORACLE is single-width (n128) with
  `0/96` low + one high point → primary fit is ONE-parameter (`beta=0`);
  two-parameter only as a `D02/D04` diagnostic.
- If the compatible widths/points cannot identify the attempted parameters
  (non-convergent optimizer over multiple starts, unbounded/degenerate
  bootstrap CI, or `alpha` hitting bounds), downgrade explicitly to
  (`beta=0`) or report `MODEL_NOT_IDENTIFIABLE`. Never report unstable
  coefficients as a correction.
- Logistic-link sensitivity (`p = logit⁻¹((delta−delta_DE−beta·n^(−2/3))·
  sqrt(n/alpha_log))`, same fixed `delta_DE`) is descriptive-only; no model
  selection between links.

## 6. Likelihood + uncertainty (frozen)

- Likelihood: `y_g ~ Binomial(t_g, p(n_g, delta_g; theta))` per graph cluster
  `g`; maximize `Σ_g [y_g log p + (t_g−y_g) log(1−p)]` (constants dropped).
  NumPy + stdlib optimization/grid search only; deterministic multi-start;
  seeds fixed at `D04`.
- Uncertainty: graph-cluster bootstrap (resample graphs with replacement
  within profile, preserving `(width, delta)` cell structure; refit; 95%
  percentiles) AND leave-one-graph-out refit range; report both, take the
  wider for prediction intervals. `D14N`-vs-`D15` leave-one-root-out
  sensitivity at `D02`.
- Prediction intervals: bootstrap percentile band ∪ `delta_DE ± h`
  sensitivity union (§4). `D16` falsification uses these bands (§7).

## 7. Holdout rules + D05 prediction schema (frozen)

- `D16` cells/seeds/command/root/budgets per proposal `A05`; official root
  proven absent; banned seeds `2026094001..4012` + `2026094101..4108` barred
  from fitting and `DE` tuning; fake-identity scratch
  (`workspace/d16_align_20260915_a/`) barred from every fit/verify/predict
  path (fail-closed seed-presence gate at `D02/D04`: any banned-seed hit in
  fit inputs → hard FAIL).
- `D05` record schema (values filled only after the reviewed fit; `$PRED`
  = prediction, fields blank until freeze):

```text
{d16_holdout_prediction_v1, profile, n=128, m, delta, delta_DE{value, source_de_root, flags},
 model{link, alpha, beta, alpha_ci, beta_ci_or_fixed},
 prediction{p_success_interval_95, expected_graph_dispersion, n_graphs=4, trials_per_graph=8},
 falsification{rule: pool outside 95% band -> FALSIFIED; inside -> NOT_FALSIFIED;
               engineering_violation -> INCONCLUSIVE; per-graph range descriptive},
 outcome{pool: BLANK, per_graph: BLANK, exact: BLANK, syndrome: BLANK,
         undetected: BLANK, terminal: BLANK},
 gate{fail_if_d16_root_exists: true, predictions_frozen_before_run: true}}
```

- Before any `D16` execution, persist predictions for all three arms; never
  revise after observing `D16`. `D05` implementation fails if the `D16` root
  exists before prediction freeze.

## 8. Residual-diagnostic separation (L4, post-prediction only)

After the scaling prediction is frozen, measure (never fold into the backoff
without a new preregistration): admission/rank residuals (all roots are
`A1–A6`-admitted; report per-cell four-cycle/girth diagnostics from
`graph_records`), iteration distributions (`max_iter=90` saturation),
residual syndrome weight on failures, and graph random effects (cluster
variance from §6). These may explain deviations; they are not covariates.

## 9. Rejected alternatives (recorded)

Outcome-adaptive grid extension/binary search (rejected: permissionless
precision); refitting `delta_DE` to finite data (rejected: collapses L2/L3);
`APP`/joint data in single-layer fits (rejected: transfer confound);
pooling graphs across roots without identity (rejected: hides batch effects);
reusing `D9` numeric thresholds as `delta_DE` (rejected: different rate base);
`V`-domain numbers as evidence (rejected: different channel); new `DE`
kernel/optimizer dependency (rejected: reuse suffices); `FER` qualification
use of `epsilon` targets (rejected: modeling targets only).
