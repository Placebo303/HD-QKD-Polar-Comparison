# V28R Design — independent degree-two finite matrices

## 1. Fixed code and accounting

`q=32`, `n=1024`, F03 natural MSB→LSB (`L1=5` bits, `L2=5` bits),
`m1=6`, and source-specific `m2={1M:194,1p5M:200,2M:202}`. Total public
leakage is `(m1+m2)*5+64` bits. The 64-bit tag is included once after both
layers, never between layers. V27 entropy values and source/delay IDs are
copied into `v28_config.json`; no source data file is opened.

## 2. Exact L1 graph

The ordered variable-column endpoint list is the 15 lexicographic pairs
`(i,j)` for `0<=i<j<6`, repeated exactly 68 times (1020 columns), followed by
`(0,1),(0,2),(1,3),(4,5)`. Each column has two nonzeros, giving 2048 edges
and 15 unique endpoint pairs. The row-degree histogram is `{341:4,342:2}`.

For column `j` and endpoint slot `0/1`, the coefficient is exactly
`_coefficient(32, 2026082001, j, endpoint_slot)`. Full GF(32) rank 6 is a
hard gate.

## 3. Exact independent L2 graphs

For each source separately, with `m` equal to 194, 200, or 202, construct the
ordered base list by iterating `k=1..5`, then `i=0..m-1`, emitting sorted
`(i,(i+k) mod m)` only once. Append the first `1024-len(base)` pairs
`(i,i+m//2)` in increasing `i`. The result is 1024 unique pairs, two
nonzeros per variable, 2048 edges, and no row-prefix relationship:

| source | m | row-degree histogram |
|---|---:|---|
| 1M | 194 | `{10:86,11:108}` |
| 1p5M | 200 | `{10:152,11:48}` |
| 2M | 202 | `{10:174,11:28}` |

L2 coefficients use `_coefficient(32, 2026082002, j, endpoint_slot)`. Rank
must equal the source's `m`; `layer_matrix` selects the source mapping rather
than slicing a mother matrix.

## 4. Bob-only sequential empirical decode

For observed 10-bit Bob symbols `B`, call V26 train
`posterior_rows("L1", B)`, converting `P(U1|B)` to the error prior
`P(E=e)=P(U=Y1+e)` by the GF(32) additive shift. Compute
`s_e=s_x+H*Y1` and call the existing `decode_fftqspa(prior_e,H,s_e,field,max_iter)`.

Only when L1 returns `success` and passes `H*x1_hat=s1`, call
`posterior_rows("L2", B, x1_hat)`. Apply the same shift with `Y2`, decode L2,
and require `H*x2_hat=s2`. If L1 fails, L2 is `not_run`. No Alice symbols,
top-K truth, or truth-derived posterior are accepted by this interface.

`decode_error_domain_posterior` is only this adapter around V10: it validates
an `(n,32)` prior, forms `s_e`, invokes V10, reconstructs `x_hat=Y+e_hat`,
and marks reconstruction false unless the public syndrome check passes.

## 5. Evidence, verifier, and boundaries

`run_v28_evidence` runs deterministic synthetic/noiseless blocks and a fixed
controlled-error smoke at representative nonzero columns. Controlled output
is labelled `fail_closed_only`; it is not a correction or FER result. The
default frozen run uses V26 train `channel_counts.npz`; it does not read
holdout/parquet/raw data.

`verify_v28` rebuilds all four matrices from config, checks coefficients,
pair order/uniqueness, edge and degree counts, rank, source/delay metadata,
leakage/tag, gate/manifest consistency, and reruns the noiseless sequential
path through a recording adapter. It proves that the second posterior call's
predecessor argument equals returned L1 `x1_hat` and persists
`readonly_verify.json`.

## 6. Lifecycle

V28R terminal success is `engineering_ready_for_retrospective_gate`. This does
not authorize V29 holdout FER; V29 remains a separate freeze review.
