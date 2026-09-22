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

## 10. R2 binding repair + fresh rerun freeze (R2-spec; no execution this call)

Authority: `.workbuddy/tasks/D17_DE_BINDING_REPAIR_R2_AND_RERUN_TASK_PACKET.md`
(§§1–7, sole authority for R2). Track for the future R2 batch:
`EXPLORE_HEAVY` (one bounded engineering repair + one fresh scientific rerun,
per packet §1). This call (R2-spec, planner, OpenSpec-only): zero `DE`/decoder
calls, no roots created, no commits, no push. Packet §§2/4/5 take precedence
on any conflict; STOP rules are fail-closed. `R204` scientific contract is
unchanged; only `R201–R203` engineering binding may be corrected once (§10.6).

### 10.1 A1 failure evidence by reference + immutability

- Predecessor terminal (accepted as failure evidence):
  `D17_DE_BATCH_ENGINEERING_BLOCKED_AWAITING_DECISION`.
- Failure signature (by reference, not re-executed this call): `0/240`
  scientific calls; `DE_CALL_FAILED@0` `TypeError` tuple-not-callable —
  `load_l1_channel` tuple passed as `channel_sampler`; `build_l1_sampler`
  never invoked on the production path. Latent L2-oracle dispatch gap:
  `conditionalize_f_to_p2` / `oracle_l2_prior` bound but dead on the A1 path.
- Failure-review verdict (by reference): `VERIFIED/PASS`; exact stored error
  and consumed A1 grant recorded in `docs/research_cycles/V72P2D17-DESCALING/EXPLORATION_LOG.md`
  per packet §5.1 (this spec does not duplicate the error string as evidence).
- A1 root (read-only, immutable failure evidence):
  `workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718`
  (six-file convention, present and unchanged per packet §5.2).
- Immutability rule: the A1 root SHALL NEVER be resumed, overwritten, repaired
  in place, or reused as `DE`/scaling-fit evidence beyond failure reference.
  No fallback to the A1 root after A2 start. A1 supplies no threshold or
  fit evidence (`0/240`).

### 10.2 R201 — L1 tuple-to-sampler binding (frozen)

- Call the accepted `load_l1_channel(model_f_root)` exactly once; require an
  exact three-item `(pb, p_f, p1)` result with finite, shape-compatible arrays.
- Call the already-bound accepted `build_l1_sampler(pb, p_f, p1)` exactly once.
- Require its return to be callable and, in the zero-scientific-call contract
  test, prove a tiny invocation returns finite normalized `(k,32)` centered
  rows. The tiny invocation is test/probe evidence, never a V26 `DE` call.

### 10.3 R202 — true-conditioned L2 oracle sampler (frozen)

- Build `p2` exactly once with the already-bound `conditionalize_f_to_p2(p_f)`.
- Add one minimal D17 adapter that samples `(A,B)` from the same
  `pb[B]*p_f[A,B]` joint as the accepted L1 sampler, sets `u1=A//32`,
  `u2=A%32`, obtains the prior EXCLUSIVELY through the bound
  `oracle_l2_prior(p2, B, u1)`, applies the accepted D9/D5 floor-normalize
  convention, and XOR-centers each row on true `u2` for the V26 consumer.
- Fail closed on nonfinite/invalid mass, incompatible shapes, non-callable
  result, or a row that is not finite, normalized, and `(k,32)`.
- V36/V37 empirical-count samplers are FORBIDDEN: their source channel is not
  the current Model-F candidate chain (reason recorded; no exception).

### 10.4 R203 — profile dispatch (frozen)

- `L1_L045` and `L1_L055` SHALL receive only the L1 callable;
  `L2_DV3_ORACLE` SHALL receive only the true-conditioned L2 callable.
- Dispatch is selected from the frozen plan entry's profile before every
  `run_de_call`; unknown/mislabelled profiles fail BEFORE a scientific call.
- Preserve dependency injection for fake tests, but represent the injected
  channels in a form that makes profile selection explicit. A single callable
  silently shared by all three production profiles is FORBIDDEN.

### 10.5 R204 — no other scientific change (frozen)

Retain exactly (all from §4, unchanged): all 15 row points (`§4` grid table);
seeds `2026094201..4208`; populations `4000/16000`; lambda/rho construction
(frozen D9 largest-remainder + concentrated floor/ceil rule); V26 kernel
(`max_iter=60`, `entropy_tol=1e-4` bits, `streak=20`); bracket / one-sided /
soft-bracket / `POP_UNSTABLE` / `delta_DE ± h` rules; plan order; `240`-call
and resource ceilings (`≤1200 s / ≤300 s between-call check / <2 GiB / 1-proc`,
setup `≤12`); claim ceiling (§9 + proposal claim ceiling); banned D16
identities (proposal `A05` + `design.md` §7 gate). No rate/grid/seed/budget/
rule change under the R2 repair.

### 10.6 Validation V1–V7 contracts (fakes/tiny probes only; no official R2 root)

1. `V1`: Reproduce A1 failure mechanically from persisted code/evidence; never
   modify, verify-as-complete, delete, or reuse the A1 root.
2. `V2`: Production binder resolves every accepted callable with zero V26
   `DE` calls.
3. `V3`: Stub the Model-F loader with finite asymmetric arrays and prove:
   loader result unpacked once; L1 builder returns a callable and receives
   `(pb,p_f,p1)`; L2 conditionalizer AND oracle mixer both actually invoked;
   L1 and L2 output rows are `(k,32)`, finite, normalized, centered on the
   respective true symbol, and observably non-identical on the asymmetric
   fixture.
4. `V4`: Fake the `DE` call over the complete 240-row plan and prove every L1
   entry receives the L1 sampler and every L2 entry receives the L2 sampler;
   swapped, missing, tuple, unknown-profile, invalid-shape, and nonfinite
   channels fail (fail-closed dispatch proof).
5. `V5`: Exercise the real production bind/signature/load/build/dispatch chain
   with V26 `run_de_call` replaced by a zero-call spy. It MUST load/build both
   samplers and stop before any scientific `DE` call (`run_de_call` spy count
   zero, explicit L2 oracle-mixer hit).
6. `V6`: `py_compile`; focused D17 tests including the new regression tests in
   one fresh writable basetemp. Broader predecessor suites only on a concrete
   compatibility conflict.
7. `V7`: Independent reviewer with actual file access confirms `R201–R204`
   and the zero-call production-chain proof. Findings recorded in the one D17
   log; no separate ceremonial document required.
- Gate: any test or review blocker is STOP before rerun.
- One-correction allowance: exactly one implementation correction within
  `R201–R203` is allowed before the reviewer closes the repair, PROVIDED the
  scientific contract `R204` is unchanged and the failed attempt stays in the
  log (retained, not overwritten).

### 10.7 A2 fresh root, command, budgets (frozen; unauthorized until pre-dispatch)

- A1 failed root (read-only): `workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718`.
- Fresh A2 result root (MUST be absent at pre-dispatch):
  `workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24`.
- Model-F root: `workspace/v72p2d5_model_f_input/20260907_r1` (unchanged).
- Exact command (once, only after all R2 validation passes):

```bash
.venv/bin/python scripts/v72p2d17_scaling_development.py --de-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24
```

- Exactly 240 scientific `DE` calls; setup at most 12. Wall at most 1200 s;
  per-call at most 300 s by the implemented between-call check; RSS strictly
  below 2147483648 bytes; one CPU process.
- No retry, resume, seed/grid extension, binary search, adaptive stop, or
  second engineering repair after command start.

### 10.8 Pre-dispatch P1–P8 (append raw evidence to the one D17 log)

`docs/research_cycles/V72P2D17-DESCALING/EXPLORATION_LOG.md`:

1. A1 failure-review `VERIFIED/PASS`, exact stored error, `0/240`, consumed
   grant; A1 six-file root present and unchanged.
2. Exact branch and scoped R2 diff. Preserve unrelated dirt. Record the R2
   implementation revision if committed, but do not require HEAD equality.
3. A2 root and D16 official root absent; Model-F root unchanged.
4. `R201–R203` focused tests and independent repair review PASS, no blocker.
5. Full frozen matrix equality to A1: 15 points, 240 identities, seeds,
   populations, rates/rhos, `DE` parameters, bracket rules, budgets, banned
   identities.
6. `PROFILE_ONLY` and unauthorized-refusal checks against fresh scratch roots;
   zero scientific calls and no official-root write.
7. Zero-call production bind/load/build/dual-dispatch proof, including an
   explicit L2 oracle-mixer hit and `run_de_call` spy count zero.
8. Exact fresh-root command and unused A2 grant.
- Any failure is STOP. Do not fall back to the A1 root or a common L1/L2
  sampler.

### 10.9 Batch-end review scope + return terminals

- Independent reviewer MUST verify: repair provenance, pre-dispatch proof,
  one-shot A2 grant, fresh root, exact command, no retry, A1 immutability;
  independently recount all 240 rows and confirm profile-specific L1/L2
  sampler dispatch from artifacts/code; recompute per-profile/m/population
  convergence, brackets, flags, `delta_DE`; run the read-only verifier;
  confirm D16 absent/outcome-blank, banned identities absent, Model-F
  unchanged, no decoder/CAL/VAL/real-data path ran; check resource ceilings;
  append `EVIDENCE_ACCESS`, verdict, blockers, findings to the single D17 log.
- Review failure blocks use of A2 evidence and grants no rerun.
- Terminals: on A2 completion + review pass,
  `D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION` (with repair
  delta; chain/L2 proofs; tests + repair review; command/exit/timestamps;
  calls/setup/wall/max-call/RSS/process; per-profile/m/population
  convergence; brackets/flags/`delta_DE`; both root inventories with A1
  unchanged; verifier + batch-end verdict; authorization consumption;
  no retry/commit/push state). On any implementation/pre-dispatch/execution/
  review failure, retain evidence and return one exact
  `D17_DE_R2_*_BLOCKED_AWAITING_DECISION` terminal with the single decision
  needed.
- Post-R2 prohibitions (unchanged, except as explicitly superseded by the A3
  one-shot grant in §11.1): do not run the scaling fit, write D16
  predictions, run D16, revive D7-H, select a route, or make
  FER/leakage/SKR/qualification/optimality/publication claims.

## 11. A3 scaling fit + D16 prediction freeze (A3-spec; no execution this call)

Authority: `.workbuddy/tasks/D17_SCALING_FIT_AND_D16_PREDICTION_FREEZE_A3_TASK_PACKET.md`
(§§1–9, sole authority for A3). Track for the future A3 batch: `EXPLORE`
(one bounded deterministic fit + one independent batch-end review, per packet
§1). This call (A3-spec, planner, OpenSpec-only): zero `DE`/decoder/`CAL`/
`VAL` calls, no roots created, no commits, no push. Packet §§3/4/5 take
precedence on any conflict; STOP rules are fail-closed. Readiness §§1–10
unchanged; the §10 post-R2 prohibition on the scaling fit is superseded only
to the extent of the §11.1 one-shot grant (spec now; execution only after A3
pre-dispatch PASS + explicit grant).

### 11.1 Acceptance + one-shot grant scope (packet §1)

- Main-thread acceptance recorded (stated in the authorizing prompt):
  `D17_DE_R2_COMPLETE_REVIEWED_AWAITING_SCALING_FIT_DECISION`.
- Accepted `DE` evidence: the reviewed A2 root
  `workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24`
  with the §11.2 brackets.
- This packet + companion prompt authorize ONLY: the minimal fit entrypoint
  (§11.3), read-only ingestion of the six named roots (§11.2) and the reviewed
  A2 `DE` root, one deterministic fit (§11.5), persistence of outcome-blank
  `D16` predictions (§11.7), and one independent batch-end review (§11.8).
- No `DE` or decoder call is authorized. `D16` execution remains unauthorized.

### 11.2 Frozen inputs + fixed brackets (packet §2)

- `DE` root, read-only:
  `workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24`.
- Fix `delta_DE` and local half-step `h` exactly to the independently reviewed
  brackets (recompute from the `DE` root before fitting):
  - L045: `delta_DE=0.24452956979862517`, `h=0.078125`;
  - L055: `delta_DE=0.30312331979862517`, `h=0.05859375`;
  - L2 DV3 ORACLE: `delta_DE=0.5468113653656221`, `h=0.09765625`.
- Literal/root disagreement is STOP; never average, refit, or substitute a
  `D8`/`D9`/`V26` number.
- Finite roots, all read-only (exactly five, fixed order):
  1. `workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34`
     (`D10-A1`);
  2. `workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d`
     (`D10-R3`);
  3. `workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450`
     (`D12`);
  4. `workspace/v72p2d14_discriminator/20260914_r1` (`D14N`);
  5. `workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2`
     (`D15`).
- Eligibility is exactly the accepted `D17` table: L045 single-layer rows from
  `D10`/`R3`/`D12`/`D14N`/`D15`; L055 single-layer rows from `D12`/`D14N`/
  `D15`; true-`U1` L2-ORACLE rows from `D14N`/`D15` only. Exclude controls,
  L050, `APP`/joint, `D11`, `D13`, `D16`, fake scratch, `DE` records, and every
  outcome with a changed decoder.

### 11.3 Fit entrypoint, exact command, budgets (packet §7)

- Amend the existing OpenSpec first (this §11). Implementation adds only the
  smallest fit/verify path to the existing `D17` module, runner, and focused
  tests; no new dependency or modeling framework.
- Fresh fit root (MUST be absent at pre-dispatch; absence verified this call —
  read returned `File not found`):
  `workspace/d17_finite_scaling_fit_5b6d71c8-9e42-4e64-b1c3-73a1f20d8e95`.
- Fail-closed `--scaling-fit --execution-authorized` entrypoint on the existing
  runner (`scripts/v72p2d17_scaling_development.py`, which currently exposes
  `--de-batch`/`--verify`/`--profile-only`): default-false authorization; it
  SHALL refuse before output creation and before input reads when unauthorized,
  and SHALL never overwrite.
- Exact command (frozen; names the `DE` root, all five finite roots in §11.2
  order, and the fit root; no glob discovery; frozen identically in code,
  OpenSpec, log, and prompt — implementation SHALL expose exactly
  `--scaling-fit`, `--execution-authorized`, repeatable `--finite-root` in
  this order, `--de-root`, `--out-root`):

```bash
.venv/bin/python scripts/v72p2d17_scaling_development.py --scaling-fit --execution-authorized --de-root workspace/d17_current_channel_asymptotic_de_r2_61fce6d0-07ad-4b67-a1a2-ef7fc1b74b24 --finite-root workspace/d10_mixed_degree_l1_b2dd13e4-6600-4e27-90df-5c9038cf2c34 --finite-root workspace/d10_r3_fresh_graph_scaling_4d39ed0e-3cbb-49f6-a1df-1dcc10868a8d --finite-root workspace/d12_finite_l1_degree_94fb9d22-cadc-47f4-a96e-b2170bdba450 --finite-root workspace/v72p2d14_discriminator/20260914_r1 --finite-root workspace/d15_finite_margin_curve_8c1e4f2a-9b3d-4e7a-a5c6-d7e8f9a0b1c2 --out-root workspace/d17_finite_scaling_fit_5b6d71c8-9e42-4e64-b1c3-73a1f20d8e95
```

- Budget: zero `DE`/decoder/`CAL`/`VAL` calls; exactly six input roots; wall
  `≤300 s`; `RSS <2147483648` bytes; one CPU process; no retry/resume/tuning.
- Minimal evidence: manifest, graph-cluster table, fit/uncertainty result,
  row-backoff table, three outcome-blank prediction `JSON` files when all
  models identify, and command log. A read-only verifier recomputes
  aggregation, model selection, intervals, predictions, and the blank-outcome
  gate.

### 11.4 Aggregation contract (packet §3, verbatim freeze)

- Read actual finite decoder/arm records, not the readiness table's pooled
  totals.
- Join each decoder row to its graph/cell metadata and aggregate to exactly one
  binomial cluster per `(source_root,profile,n,m,graph_seed)` with `y=exact`,
  `t=blocks`.
- Preserve root and graph identity. Never pool graphs, treat decoder rows as
  independent clusters, duplicate `D11` replay rows, or combine exact with
  syndrome-valid/undetected.
- Recompute `delta=5m/n-H_layer` from the accepted generator entropy;
  stored-vs-recomputed mismatch is STOP.
- Every included cluster needs the frozen decoder semantics and exactly one
  eligibility class. `D16`/banned identities or fake scratch contact is STOP.
- Reconcile aggregated counts to accepted `D10`/`R3`/`D12`/`D14N`/`D15` totals
  before fitting.

### 11.5 Fit + uncertainty contract (packet §4, frozen)

```text
p_success(n,delta) = Phi((delta-delta_DE-beta*n^(-2/3))*sqrt(n/alpha))
```

- `delta_DE` is fixed from §11.2 and never optimized.
- L045/L055: two-parameter `(alpha>0,beta)` first, then the reviewed ladder to
  `beta=0`, then `MODEL_NOT_IDENTIFIABLE` if necessary.
- L2 DV3 ORACLE: predeclared one-parameter primary with `beta=0`; all eligible
  observations are n=128.
- Use exact graph-cluster binomial likelihood and the reviewed deterministic
  search.
- Every identifiable final model gets cluster bootstrap and leave-one-graph-out
  uncertainty. L045/L055 also get leave-one-root-out sensitivity, especially
  `D14N`-vs-`D15`. Prediction uses the wider union.
- Logistic-link fit is descriptive only and cannot change the selected model,
  `delta_DE`, or `D16` predictions.
- Graph/rank/cycle/iteration/syndrome residuals cannot enter the fit.
- If any final model is `MODEL_NOT_IDENTIFIABLE`, persist diagnostics but do
  not create filled `D16` predictions. Return the explicit terminal in §11.9;
  do not substitute another model.

### 11.6 Row-backoff report (packet §5, frozen)

- For each identifiable profile at n=64/128/256 and epsilon 0.10/0.01:

```text
delta* = delta_DE + beta*n^(-2/3) + z_(1-eps)*sqrt(alpha/n)
m* = ceil(n*(H_layer+delta*)/5 - 1e-9)
backoff = m* - ceil(n*H_layer/5)
```

- Report point and wider uncertainty-union integer intervals; require
  `m*(0.01)>=m*(0.10)`.
- These are diagnostic modeled backoffs, not `FER` qualification targets.

### 11.7 D16 prediction freeze (packet §6, frozen)

Only if all three profiles identify:

- Prove the `D16` official root absent:
  `workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a`
  (absence verified this call — read returned `File not found`).
- Fill exactly L045 n128/m125, L055 n128/m125, and L2-ORACLE n128/m94.
- Persist `DE`-root/bracket provenance, model and identifiability, coefficient
  uncertainty, and prediction union over fit uncertainty and
  `{delta_DE-h,delta_DE,delta_DE+h}`.
- `expected_graph_dispersion` is an object with a deterministic model-based
  `binomial_8_trial_interval_95` and an
  `empirical_graph_residual_range_descriptive`. The latter does not alter the
  universal backoff fit.
- Keep `pool/per_graph/exact/syndrome/undetected/terminal` exactly `BLANK`.
- Frozen falsification: pool outside the 95% band is `FALSIFIED`; inside is
  `NOT_FALSIFIED`; engineering violation is `INCONCLUSIVE`; graph range is
  descriptive. Prediction files are never revised after `D16` is observed.

### 11.8 Pre-dispatch + independent review (packet §8)

Before the single fit:

1. Accept A2 review and recompute its three brackets from root.
2. Prove all six inputs present/read-only, fit root absent, `D16` root absent.
3. Freeze exact root list/command; prove no `D16`/fake/banned identity in
   inputs.
4. Run `py_compile` plus focused tests covering parameter recovery,
   non-identifiable terminal, graph-not-row aggregation, `APP`/undetected
   isolation, refusal, no-overwrite, prediction-blank, and fake full fit.
5. Record zero scientific calls and unused grant in the single `D17` log.

Afterwards one independent reviewer with artifact access recomputes
aggregation, accepted totals, fixed `delta_DE`, likelihood/ladder,
uncertainty, inversion, prediction bands/dispersion, blank gate, verifier,
resources, and input immutability. Append one review to the `D17` log. Do not
repeat predecessor suites without a concrete conflict.

### 11.9 Return terminals (packet §9, three-way branch)

All three identify and predictions freeze:

`D17_SCALING_FIT_COMPLETE_PREDICTIONS_FROZEN_AWAITING_D16_AUTHORIZATION`

Any model not identifiable (`MODEL_NOT_IDENTIFIABLE` → diagnostics only, no
filled predictions):

`D17_SCALING_MODEL_NOT_IDENTIFIABLE_AWAITING_ROUTE_DECISION`

Engineering/review failure:

`D17_SCALING_FIT_ENGINEERING_BLOCKED_AWAITING_DECISION`

Report reconciliation, cluster counts, fixed `delta_DE/h`, models and
uncertainty, logistic sensitivity, row backoffs, predictions/blank status,
command/resources, root/verifier/reviewer, grant and no-retry/commit/push
state. Do not run `D16`, `DE`, decoder, real data, `D7-H`, or make
`FER`/leakage/`SKR`/qualification/optimality/publication/route-closure claims.
