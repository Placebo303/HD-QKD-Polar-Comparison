# D5 G1 information-recovery R2 acceptance R1

- repo: `HD-QKD_Polar_Comparison`
- branch: `formal-ir-v72p1-addendum-clean`
- HEAD: `1d4fa9124afd57ec5ce03a786a4cdc2b2f55cc1d`
- candidate chain: `88053563→a93106f5→21576add→1d4fa912`
- review: `G1_INFORMATION_RECOVERY_R2_REVIEW_R1.md`, verdict `G1_INFORMATION_RECOVERY_R2_REVIEW_PASS`
- gate in: `INDEPENDENT_G1_INFORMATION_RECOVERY_R2_REVIEW`
- gate out: `G1_L1_ESTIMATOR_DISCRIMINATOR_IN_PROGRESS`

## Accepted verbatim block (only scope accepted)

```text
G1_INFORMATION_RECOVERY_R2_ACCEPTED
scope: ADDITIVE_NONFORMAL_BACKOFF_PRIOR_CANDIDATE
terminal_class: LAMBDA_APPLICATION_CONTRACT_DEFECT
formal_g1_result_changed: false
production_wiring_changed: false
```

## Decisive formula and provenance

- D4R2-F estimation (selected, frozen): `P(a|b) = (counts[a,b] + lam * p_global[a]) / (n_b[b] + lam)`, `lam* = 137.3823795883264` total concentration per Bob column, `p_global` = full-CAL Alice marginal. Inner 3-fold CV on F joint CE over grid30 `logspace(-2, 3)`; all 4 outer folds selected the same value.
- Accepted consumer (`build_f_model`): `sm = counts + lam` cell-wise, then column-normalize along `axis0`. Same scalar applied to 1,048,576 cells: `1024 * lam ≈ 140,680` added per column vs `n_b ≈ 256` observed (99.82% prior).
- Candidate (additive, commit `a93106f5`): `build_f_model_concentration` + `prepare_model_f_prior_candidate` implement the backoff form on the same counts; frozen symbols, constants, seeds, thresholds, authorizations, phases, and accepted artifacts untouched; production phases keep calling `prepare_model_f_prior`.
- Provenance: OpenSpec `v72p2d5-g1-information-recovery-r2` (proposal/design/tasks/specs before code, `88053563`); evidence root `workspace/d5_g1_wide_attribution_r2_5c38a20ae60b41ceb0b6a0d7757aa2aa/` (53 development calls, CAL-only); lifecycle closeout `1d4fa912`.

## Old vs candidate values (like-for-like, same counts + same functional)

- Old consumer: CE `4.999985322023371 + 4.999659312231358 = 9.999644634254839`, MI `0.0003553306407582113`, truth mass `~0.03124`.
- Candidate in-sample: CE `4.286720430201375 + 3.222719884634378 = 7.5094403148357545`, MI `2.48306874956704`, truth mass `0.25444987775455336` (L1 `0.096` / L2-oracle `~0.25`), column-normalization maxerr `2.93e-14`, split maxerr `2.22e-16`.
- D4 held-out (frozen reference, not a candidate claim): `3.8147422680157206 + 3.347605161943064 = 7.162347429958785`. `7.5094 ≠ 7.162347` is explained: different population / different functional / refit optimism; the like-for-like isolation is `10.0 → 7.51`.
- Prior strength: `Q*lam = 140679.55669844622`, prior fraction `0.998183566972047`, dominance `549.5295183533055`, column maxerr `4.06e-14`.

## Three-call independent confirmation (review C08, seeds `2026090600..03`)

- Review root `workspace/d5_g1_r2_review_7f3a9c1e2b4d4f60/` (cleaned); square `Hsq[:64]` seed `2026090801`, rank `64`; n `64`; frozen `max_iter 90`; `120s` watchdog.
- call1 old + Hsq: oracle-L2 false/false, unconverged, 90 iters, `0.5698s`, tmass `0.031245495554821028`.
- call2 candidate + same Hsq/seed: oracle-L2 true/true, converged early, 10 iters, `0.0637s`, tmass `0.21866977384250286`.
- call3 candidate + frozen H2[:43]: oracle-L2 false/false, unconverged, 90 iters, `0.4516s`.
- Consistent with w2/w4b per-number; R1 29 calls / R2 53 calls audit summaries consistent.

## L1 and disclosure limitations (binding)

- C1 L1 truth mass `0.096` fails at every disclosure including square (0/12 at 49/59/square); L1-at-64 is the binding constraint and the named L1 discriminator question.
- C1 oracle-L2 recovers at square (4/4, 3–10 iters) and partially at H2[:52] (2/4; pass mass `0.28`, fail mass `0.22–0.24`); frozen H2[:43] stays 0/4. L2-only success at 52–64 rows is near-zero rate, not an operating point.
- R1's `FINITE_LENGTH_DISCLOSURE_INSUFFICIENT` is carried as downstream secondary, superseded as primary.

## Nonclaims (all explicit)

- This acceptance does not replace the accepted Model-F artifact or the accepted formal G1 result (`workspace/v72p2d5_g1/20260907_r2`, `G1_COMPLETED_NO_SIGNAL_FAIL`, `passed=false`).
- It does not authorize a G1 rerun/resume, production wiring change, Model-F substitution, formal re-execution, G2 readiness, qualification, or promotion.
- Development results are not formal evidence and cannot authorize G2.
- No VAL was read or used; canonical CAL-TRAIN only.
- No seed search, unconstrained sweep, model zoo, or decoder-success selection was performed.

## Lifecycle effect

```yaml
g1_information_recovery_r2_review: PASS_R1
g1_information_recovery_r2_candidate_accepted: true
g1_information_recovery_r2_implementation: a93106f5
g1_information_recovery_r2_terminal_class: LAMBDA_APPLICATION_CONTRACT_DEFECT
next_gate: G1_L1_ESTIMATOR_DISCRIMINATOR_IN_PROGRESS
```

All authorizations remain false; G2 remains absent; formal roots unchanged.
