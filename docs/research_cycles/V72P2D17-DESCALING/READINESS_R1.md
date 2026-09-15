# D17 Current-Channel Asymptotic-to-Finite Scaling — Readiness R1

- Authority: `.workbuddy/tasks/D17_ASYMPTOTIC_FINITE_SCALING_READINESS_R1_TASK_PACKET.md` (§§1–§8, sole authority; §8 return contract).
- Track: documentation-only (no code, no DE/decoder execution, no root creation, no staging/commits, no push).
- Repo: `/mnt/d/Code/HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean` (do not switch; no commit/push in this call).
- Review: D17-R207, trusted VERIFIED — `EVIDENCE_ACCESS VERIFIED`, verdict `PASS_WITH_FINDINGS`, blocking none. Do not rerun.
- OpenSpec: `openspec/changes/v72p2d17-asymptotic-finite-scaling/` (`proposal.md`, `design.md`, `tasks.md`, `specs/de-scaling/spec.md`).
- Predecessor: `D16_MATCHED_BACKOFF_READINESS_ACCEPTED_AWAITING_EXPLICIT_AUTHORIZATION` (readiness valid; Batch A1 withdrawn — D16 is held-out validation, never the next gate).

## 1. Four-level hierarchy (never collapsed, packet §2 / design §1)

1. **L1 information limit**: generator conditional entropy `H_l` + disclosure gap `delta = 5m/n − H_l` (bits/symbol). Frozen: `H_L1 = 4.286720430201375`, `H_L2 = 3.222719884634378`; n128 loads `548.700215065776 / 412.508145233200` bits.
2. **L2 asymptotic ensemble limit**: current-channel MC-DE threshold per frozen ensemble/profile as `delta_DE` (or equivalent rate), from the frozen §4 grid under the frozen convergence rule. Never refit to finite data.
3. **L3 finite-length statistical backoff**: predeclared probit law (below), falsifiable by D16. Empirical calibration for this channel/decoder family, not a universal theorem.
4. **L4 finite graph/decoder residual**: rank, cycles, trapping/absorbing behavior, schedule, convergence deviations — measured AFTER the scaling prediction (§8); never folded into the backoff without a new preregistration.

DE convergence is not finite-code usability.

## 2. Channel verdict (R207 CHANNEL PASS)

- Exact Model-F candidate channel shared by D8–D16: generator `p_f(Alice=1024,Bob=1024)`, `A=32*U1+U2`, estimator `prepare_model_f_prior_candidate`/`build_f_model_concentration`, `LAMBDA_STAR=137.3823795883263870`; floor `max(p,1e-300)` pre-`log2`, no renormalization; joint `7.5094403148357545`.
- Decoder chain: `P1=sum_u2 P_F`, `P2=P_F/P1`; L1 marginal `q@P`; L2 oracle true-`U1` conditioning (diagnostic-only); decoder floor `_floor_renorm(1e-15)` with renormalization; `GF32/poly37`; row-layered cold `max_iter=90`, `damping=1.0`.
- Reuse-only via lazy bind on the authorized path: V26 kernel + D9 adapter, no new DE kernel. No `numba`/`njit`/decode-kernel strings in new sources; D9 ceiling intact (primitives `≤1.94e-16`; flooding↔row-layered and DE↔decoder-terminal non-equivalence); trajectory traces without equivalence claim.
- Four recorded distinctions (not mismatches): (i) D8–D12 CE-constant rows vs D14N+ generator rows join one `delta` axis (generator unchanged); (ii) legacy per-cell-`lam` estimator REJECTED (pre-D14 diagnostics only); (iii) V25/V26/V27 empirical-timestamp domain — kernel-reuse only; (iv) D8/D9 DE rate base (CE) differs from D17 (generator H) — D9 numbers do not transfer as thresholds.

## 3. Eligibility classes (R207 ELIGIBILITY PASS)

Audit 33 rows (30 cells + 3 BLANK); hand-spots F3/F16/F19b/H1/F14a match; D12/D14N/D15 pools match live roots; clusters preserved (bootstrap within cells, LOO by graph).

- **FIT** (single-layer only; graph clusters + root identity retained; exact binomial counts): D15 all 9 cells; D14N L045/L055/L2-ORACLE (leave-one-root-out sensitivity at D02); D12 L045/L055 n128+n256 (CE-f1.2 rows, same generator chain — D02 join-key check); D10-MIX/R3-MIX L045-profile cells (D02 row confirmation).
- **VALIDATION-ONLY**: D11 L1 replay (R3 duplicate, no double count); D11 L2-ORACLE (D02 true-conditioning audit); D16 (frozen predictions only, post-run falsification).
- **DESCRIPTIVE-ONLY**: non-D17 profiles (D10/R3-DV3, D12-L050); all APP/joint outcomes — APP/joint + misplaced-oracle refused (probed, excluded from single-layer fit by rule); D13 ladder; D8/D9 DE numbers; V25/V26/V27; Wilson/paired intervals.
- **L2 ORACLE**: enters ONLY the true-conditioned L2 model. L2-ORACLE predeclared one-parameter (`beta=0`) single-width primary.

## 4. Frozen DE grid (R207 GRID PASS)

n128-reference integer-`m`; exact `R = 1 − m/128`, `d = 5m/128`, `delta = d − H_l`; `rho` from exact `(n,m)` by frozen D9 rule (never legacy CE labels). 15 points:

| Profile | m points | delta points | Rationale |
|---|---|---|---|
| L1 L045 (71/57/E313) | 106, 110, 114, 118, 122 | −0.14610, +0.01015, +0.16640, +0.32265, +0.47890 | brackets D9-converged +0.323 from below |
| L1 L055 (83/45/E301) | 116, 119, 122, 124, 126 | +0.24453, +0.36172, +0.47890, +0.55703, +0.63515 | D9 unconverged @+0.323; extends up; capped at m126/R0.015625, lowest positive n128 rate — one-sided-high contingent predeclared |
| L2 DV3 oracle (0/128/E384) | 89, 94, 99, 104, 109 | +0.25384, +0.44916, +0.64447, +0.83978, +1.03509 | brackets finite 0/32 @+0.254 vs 63/72 @+0.840 |

- Seeds `2026094201..4208` (8; absence proven repo-wide); pops `{4000 coarse, 16000 confirmation/stability}`; V26 `max_iter=60/tol=1e-4/streak=20`.
- Budget: `3·5·8·2 = 240 DE` calls + setup `≤12`; wall `≤1200 s`, per-call `≤300 s`, `RSS <2 GiB`, 1 proc, no retry/resume/seed-search/adaptive. Non-adaptive: no binary-search/extend strings.
- Convergence: `S_pop = #{H60 < 1e-4}`; `delta_DE` = midpoint of predeclared bracket pair at pop16000 (edge/flag rules frozen: `DE_ONE_SIDED_LOW/HIGH`, `DE_SOFT_BRACKET`, `POP_UNSTABLE` — never re-grid). Granularity half-step `h`; prediction intervals union over `{delta_DE − h, delta_DE, delta_DE + h}`.
- Future command (frozen, unauthorized string only): `.venv/bin/python scripts/v72p2d17_scaling_development.py --de-batch --execution-authorized --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718`.
- Future root: `workspace/d17_current_channel_asymptotic_de_7e4b2a1d-9c3f-4d8e-a1b2-c3d4e5f60718` — ABSENT (this call). Default-false auth; `PROFILE_ONLY` rc=0 + refusal rc=2 (reviewer ran).

## 5. Scaling law + identifiability + epsilon targets (R207 EQUATIONS/IDENTIFIABILITY/INVERSION PASS)

```text
p_success(n, delta) = Phi((delta - delta_DE - beta*n^(-2/3)) * sqrt(n/alpha)),  alpha > 0
```

- Fit separately for L1 L045, L1 L055, L2 DV3 ORACLE. `delta_DE` fixed from reviewed DE result; never refit to finite data.
- Units: `H_l, d, delta, delta_DE, beta·n^(−2/3)` bits/symbol; `alpha` bits²·symbols; `p_success`, `epsilon` dimensionless. Signs/monotonic limits verified: increasing in delta/n; 0/1 at ±∞; `Phi(0)=0.5` at threshold.
- Likelihood: exact per-graph-cluster binomial; deterministic multi-start (NumPy/stdlib only). Uncertainty: cluster bootstrap AND leave-one-graph-out (report both, predict with wider); D14N-vs-D15 leave-one-root-out sensitivity at D02.
- Identifiability ladder: two-parameter → one-parameter (`beta=0`) → `MODEL_NOT_IDENTIFIABLE`; never report unstable coefficients. L2 single-width → one-param primary. Fixture recovers `0.6219/0.25` (within 35%/0.15); all-zero → `MODEL_NOT_IDENTIFIABLE`; ladder always returns model+reason with CI, never bare coefficients; logistic descriptive-only.
- Inversion (frozen): `delta*(n,eps) = delta_DE + beta·n^(−2/3) + z_{1−eps}·sqrt(alpha/n)`; `m* = ceil(n·(H_l+delta*)/5)`; `backoff = m* − m0` with `m0 = ceil(n·H_l/5)` (L1 n64→55/n128→110/n256→220; L2 n64→42/n128→83/n256→166). Fixture backoffs L1 n64 4/5, n128 7/8, n256 11/14; `ceil(need−1e-9)`; m0 recomputed with STOP-on-drift.
- Targets: `epsilon=0.10` primary / `0.01` sensitivity — diagnostic modeling targets, never project FER qualification. `delta_DE None → ValueError`; NLL hand-check 1e-9; `ndtri` machine precision (first-run fix in-scope); integer rows with intervals, `eps0.01 ≥ eps0.10`, union band; diagnostic-not-qualification labeling.

## 6. Holdout lock (R207 HOLDOUT PASS)

- Held-out cells (n128): L045 m125 (`Δ+0.59609`); L055 m125 (same disclosure); L2-ORACLE m94 (`Δ+0.44916`). All outcome fields BLANK.
- Banned seeds (barred from fitting and DE tuning): graphs `2026094001..4012`, blocks `2026094101..4108` — refused on all four edges (probed). Fake-identity scratch `workspace/d16_align_20260915_a/` barred from every fit/verify/predict path (fail-closed seed-presence gate at D02/D04); scratch never opened (substring refusal only).
- D16 root `workspace/d16_matched_backoff_discriminator_b7c2d4e6-8f1a-4c3d-9e5b-2a4f6c8d0e1a` — ABSENT (this call); existing-path `FileExistsError` preserved.
- D05 prediction schema (values filled only after reviewed fit; blank until freeze): `{d16_holdout_prediction_v1, profile, n=128, m, delta, delta_DE{value, source_de_root, flags}, model{link, alpha, beta, alpha_ci, beta_ci_or_fixed}, prediction{p_success_interval_95, expected_graph_dispersion, n_graphs=4, trials_per_graph=8}, falsification{pool outside 95% band → FALSIFIED; inside → NOT_FALSIFIED; engineering_violation → INCONCLUSIVE; per-graph range descriptive}, outcome{pool/per_graph/exact/syndrome/undetected/terminal: BLANK}, gate{fail_if_d16_root_exists: true, predictions_frozen_before_run: true}}`. D05 fails if D16 root exists before prediction freeze. D16 short-circuit fix in-scope (holdout enforcement).
- Blank schema: 3 BLANK + gate flags; non-blank → `ValueError`.

## 7. B/C/D02–D06 evidence table (R207 ZERO-CALLS + TEST_RERUN)

| Item | Evidence |
|---|---|
| B01 kernel/adapter reuse | V26 kernel + D9 adapter reuse-only, lazy bind on authorized path; no new kernel |
| B02 delta/rate rule | `delta`-parameterized; `rho` from exact rate by frozen D9 rule; no CE labels |
| B03 frozen grid | 15 pts + seeds + rule + budgets frozen (§4 above); non-adaptive |
| B04 trajectories | per-call summaries recorded; no DE↔row-layered claim beyond D9 primitives |
| B05 future batch | command/root/budgets frozen, default-false auth; PROFILE_ONLY + read-only verifier; root absent |
| C01 predeclared law | probit law, per-profile, `delta_DE` fixed from reviewed DE |
| C02 likelihood/uncertainty | binomial + cluster bootstrap / LOO, report both, wider predicts |
| C03 identifiability | ladder two-param → beta=0 → MODEL_NOT_IDENTIFIABLE; L2 one-param primary |
| C04 logistic sensitivity | descriptive-only; NumPy/stdlib, no new dep |
| C05 row backoff | integer inversion at n=64/128/256 with intervals, eps 0.10/0.01 |
| C06 D16 predictions | three-arm outcome-blank freeze before any D16 run; never revised after |
| C07 residuals | rank/cycles/iterations/syndrome/graph effects post-prediction only |
| D02 audit artifact | compact CSV/JSON inventory + report; read-only predecessor roots; R3/D11 confirm; leave-one-root-out |
| D03 DE adapter/runner | three-profile plan, fake-injected tests, auth refusal, fresh root + verifier; zero scientific calls |
| D04 scaling module | graph-aggregated binomial counts, deterministic fit/uncertainty, synthetic + non-identifiable fixtures, fail-closed banned-seed gate |
| D05 holdout record | immutable schema + blank outcome fields; fail if D16 root exists |
| D06 focused validation | compile, math/channel equivalence, plan/grid, fake DE, fit recovery, eligibility isolation, root absence, no-production |

Zero-calls: fakes/bind-fail on readiness paths; no v26 modules (pandas-numba false positives only); NO_VAL_READS; counters 0; D16 + D17 future roots absent. Test rerun: 30/30 reviewer own basetemp (12.98 s).

## 8. D07 verdict + findings

- Verdict: `PASS_WITH_FINDINGS`, blocking none.
- First-run fixes IN-SCOPE (minimal diff, no new dep): D16 short-circuit (holdout enforcement) + `ndtri` precision (epsilon-0.01 requirement).
- Non-blocking (no code change now): `_looks_like_fake()` unwired; D16-rows message order (fail-closed); `fit_profile` in `__all__` (document as ladder-internal); scoped commit = 7 D17 files only.
- Recommendation: `D17_DE_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION`; no DE/D16 authorization; D7-H closed.

## 9. Authorization state (all-false)

- DE calls: 0. Decoder calls: 0. No scientific execution authorized by this record or by D17-R207.
- Future DE root absent; D16 official root absent. Frozen commands remain unauthorized strings.
- COMMIT_PUSH: none (commit is a separate call, not this one).

## 10. Terminal + next gate + claim boundary

- Terminal: `D17_DE_SCALING_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
- Next gate: separate explicit DE-batch authorization first (+ Pre-EXECUTE); scaling fit + frozen D16 prediction follow the reviewed DE result. D16 prediction freeze precedes any D16 run.
- Claim boundary: empirical calibration for this channel/decoder family only. No FER qualification, leakage/SKR, real-data, promotion, publication, optimality, D7-H revival, or route-closure claim. `epsilon` targets are modeling targets, not FER requirements.

(End of file)
