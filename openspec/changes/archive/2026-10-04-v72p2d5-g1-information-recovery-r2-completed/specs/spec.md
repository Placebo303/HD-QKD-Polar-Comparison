# Delta spec: candidate backoff prior path

## REQ-R2-01 (backoff formula)

`build_f_model_concentration` SHALL compute
`P(a|b) = (counts[a,b] + lam * p_global[a]) / (n_b[b] + lam)` with
`n_b[b] = sum_a counts[a,b]` and `p_global[a] = sum_b counts[a,b] / total`,
for finite-nonnegative 2-D `(Alice, Bob)` counts and finite-positive scalar
`lam`. It SHALL NOT add `lam` per cell.

## REQ-R2-02 (normalization)

Every output column SHALL sum to 1 within 1e-12; violation SHALL raise, never
silently renormalize. An all-zero column SHALL fall back to `p_global`.

## REQ-R2-03 (candidate prepare contract)

`prepare_model_f_prior_candidate` SHALL accept injected `(counts_ab, p_b)`
only, default `lam = LAMBDA_STAR` (frozen D4R2 nested-CV selection; no new
search), perform no file read, reference no formal root, and return
`(p_b, p_f)` satisfying the existing phase checks (P_F columns sum to 1
within 1e-8, `P(B)` sums to 1 within 1e-8, Alice dim a nonzero multiple of
32).

## REQ-R2-04 (frozen preservation)

No frozen symbol, constant, seed, threshold, authorization, or accepted
artifact SHALL change. Production phases SHALL keep calling
`prepare_model_f_prior`.

## REQ-R2-05 (validation)

Compile, focused tests, the exact three-file D5 suite, and candidate
development diagnostics SHALL be green before review. Exploratory decoder
success SHALL NOT be recorded as formal evidence.
