# D7-A — design

## System under test

- `v35_algorithm_development.py`: `GF2mField` GF32 tables (via
  `_get_gf32_tables`), `syndrome_of_gf32`, `fwht_batched`,
  `_check_update_log_batch`, `decode_row_layered_fftqspa` (damping,
  cold/warm start, stopping, `final_beliefs`), `DecoderResult`.
- `v72p2d5_gf32_rate_mother.py`: `_softmax_rows`, `_floor_renorm`,
  `app_fed_l2_prior`, `_decode_block`, `_run_layered_block`
  (L1→soft-APP→L2 bridge, absent-belief fallback).

Declared field facts (independently checked, imported as constants only):
`FIELD_Q=32`, `FIELD_POLY=37` (`0b100101`), `FIELD_ID=c3a3660…`.

## Independent oracle (`v72p2d7_gf32_decoder_certification.py`)

Slow-by-design, plain loops, NumPy only:

1. **Field**: `gf32_mul_independent(a, b)` from polynomial 37 by bitwise
   shift-and-reduce; `gf32_add` = XOR; inverse by brute-force search;
   reference mul/add/inv tables built from these. No import of production
   tables, FFT/Walsh helper, check-update helper, syndrome-offset helper,
   or row-layered code.
2. **Direct check-SP** (`direct_check_to_var`): for a single check with
   degree 2 or 3, coefficients, syndrome, and incoming probability vectors,
   enumerate all `32^deg` assignments; outgoing message to edge `t` at value
   `v` is proportional to the sum of product-of-incoming over assignments
   with `sum_j c_j x_j + c_t v = s`. Floor `1e-15` + renormalize, same as
   production convention, then compare in probability domain.
3. **Exact tiny posterior** (`exact_posterior`): enumerate all `32^n`
   assignments with `H x = s` (n ≤ 3 variables in fixtures), weight by prior
   product, normalize per variable.
4. **Independent row-layered recurrence** (`row_layered_reference`): same
   schedule as production — cold-start log beliefs from floored priors;
   rows processed in index order; per row, extrinsic
   `v_{c→r} = beliefs[c] − u_{r→c}^{old}`, direct-SP check update in
   probability domain via the oracle, immediate
   `beliefs[c] −= u_old; beliefs[c] += u_new`; damping fixed at 1.0
   (undamped path only); hard decision + syndrome check after each full
   sweep. Returns beliefs after each sweep.

## Iteration-count convention (frozen)

One iteration = one complete row sweep over all `m` rows in index order.
Production `iterations=k` means beliefs are post-`k`-sweep; `iterations=0`
means the initial MAP already satisfied the syndrome (early return).
Loopy comparisons use fixtures whose initial MAP does **not** satisfy the
syndrome, so `max_iter=1,2,3` yields post-sweep-1/2/3 beliefs with no early
stop. No trace hook is planned.

## Comparison plan

- **Arithmetic**: oracle tables vs production `_get_gf32_tables` elementwise;
  plus spot identities (commutativity, `a·1=a`, `a·a⁻¹=1`, distributivity).
- **Check update**: production `_check_update_log_batch` (softmaxed to
  probabilities by the test) vs oracle `direct_check_to_var` over the frozen
  matrix: all 32 field elements × all 31 nonzero multipliers × syndromes
  {0} ∪ nonzero sample × deg {2,3} × coefficients {1 + ≥3 nontrivial} ×
  ordinary + skewed priors. Max-abs error per family; tol 1e-10.
- **Direction traps**: oracle self-tests that fail under one deliberately
  wrong coefficient-permutation direction and one deliberately wrong
  syndrome shift (negative controls).
- **Tree**: single checks (deg 2/3) and one two-check tree; production
  `decode_row_layered_fftqspa` final beliefs (softmaxed) vs oracle
  `exact_posterior`; tol 1e-10 max-abs; MAP equality secondary only.
- **Loopy**: one small cycle with nontrivial labels; production beliefs at
  `max_iter=1,2,3` (softmaxed) vs oracle `row_layered_reference`
  post-sweep-1/2/3; tol 1e-10. Records first divergent sweep/node/symbol on
  mismatch.
- **L1→L2**: establish `final_beliefs` = log-domain beliefs from code
  (log-prior init + additive log updates); verify `_softmax_rows` on tiny
  arrays (axis, positivity, normalization); verify `app_fed_l2_prior`
  `q @ P` against explicit einsum on tiny arrays (Bob indexing, U1
  conditioning, floor+renorm); verify `_run_layered_block` bridge with an
  injected **fake** decode_fn (never the historical decoder): correct-shape
  log beliefs → softmaxed `q` feeds L2; absent beliefs → uniform fallback.
  Any mismatch is a correctness finding.

## Failure handling

On any mismatch: freeze the minimal counterexample (fixture, expected,
actual, max error), stop downstream attribution, complete an independent
FAIL review, and close with `D7_A_SCOPED_CORRECTNESS_REWORK_PROPOSAL`.
No production patch in this task.
