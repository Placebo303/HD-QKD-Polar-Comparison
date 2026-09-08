# Design: candidate backoff prior path (additive, nonformal)

## Defect (frozen, referenced not modified)

`build_f_model(counts_ab, lam)` computes `sm = counts + lam` cell-wise, then
normalizes each Bob column along `axis0` (Alice). With the frozen
`LAMBDA_STAR = 137.3823795883264` on the accepted `(1024, 1024)` counts
(`n_b ≈ 256` per column), every column receives `1024 * lam ≈ 140,680`
pseudo-observations: prior fraction 99.82%, MI ≈ 0.0004 bits, truth mass
≈ 1/32. D4R2 `build_f` selected the same scalar as a total per-column
concentration: `P(a|b) = (counts[a,b] + lam * p_global[a]) / (n_b[b] + lam)`
(`p_global` = full-CAL Alice marginal): 137 added per column, prior fraction
34.9%, MI ≈ 2.48 bits, outer held-out joint CE 7.162347.

## Candidate math (frozen D4R2 formula, new location)

`build_f_model_concentration(counts_ab, lam=LAMBDA_STAR)`:

- `counts_ab`: `(1024, 1024)` finite nonnegative `(Alice, Bob)`; `lam` finite
  positive scalar (total concentration per Bob column, NOT per cell).
- `n_b[b] = sum_a counts`; `p_global[a] = sum_b counts / total`.
- `P(a|b) = (counts[a,b] + lam * p_global[a]) / (n_b[b] + lam)`; every column
  sums to 1 within 1e-12 (asserted, not silently fixed).
- Zero-data column (`n_b[b] == 0`, impossible for accepted input but possible
  for injected tests) falls back to `p_global` (the lam-weighted limit).

`prepare_model_f_prior_candidate(counts_ab=None, p_b=None, lam=LAMBDA_STAR)`:

- Same shape/contract checks as `prepare_model_f_prior` (P_F columns sum to
  1 within 1e-8, `P(B)` sums to 1 within 1e-8, Alice dim multiple of 32).
- Injected tables only; no file read, no formal-root reference, no decoder.
- Returns `(p_b, p_f)` consumable by the existing `_ce_stats`,
  `marginalize_f_to_p1`, `conditionalize_f_to_p2` helpers unchanged.

## Isolation

- New names only; no edit to any frozen symbol, constant, or docstring.
- No I/O, no `pathlib`, no `sys.path`, no authorization logic in the new code.
- Chain-split equivalence with D4R2 `build_f` output: maxerr < 1e-12
  (same formula; asserted in tests via an in-test reimplementation, not by
  importing the audit module's file reader).

## Non-design (explicitly refused)

- No lam re-selection (frozen D4R2 nested-CV value reused; no VAL, no search).
- No disclosure-row change, no mother change, no decoder change.
- No production wiring: phases keep calling `prepare_model_f_prior`.
