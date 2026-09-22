# D7-A independent correctness review R1

Review mode: separate verification pass over the landed oracle/test source
(read in full), with representative values recomputed through
reviewer-written code that shares no logic with the oracle module
(full-product-then-reduce GF mult; convolution-form deg-2 check-SP), plus
direct production cross-checks. Limitation: single-operator context — no
second agent was available; mitigation is the structural independence of the
recomputation (different algorithms, seed 777 fixture) rather than re-running
the oracle. Green tests were not trusted on their own.

## Checks (§5 list)

- **Oracle independence**: oracle imports only `itertools`/`numpy`; no
  production table/FFT/check/syndrome/layered code; constants `Q=32` /
  poly 37 match declared `FIELD_Q`/`FIELD_POLY`/`_POLYNOMIALS[5]`. PASS.
- **Field polynomial/labels**: reviewer mult agrees 1024/1024; add is XOR;
  31/31 inverses. PASS.
- **Coefficient/syndrome directions**: reviewer convolution-SP == oracle
  enumeration exactly (0.0); production == both (2.1e-17); wrong-direction
  and wrong-shift variants both diverge > 1e-6. PASS.
- **Direct-SP enumeration completeness**: deg-2 full sweep + deg-3 sampled;
  worst 3.3e-16 ≤ 1e-10, no failing tuple. PASS.
- **Tree posterior equality**: ≤ 6.7e-16 across single-deg2/deg3/two-chain,
  satisfied + non-satisfied MAP. PASS.
- **Loopy schedule equivalence + iteration convention**: per-sweep match at
  max_iter=1,2,3 with `iterations==k` on both fixtures (≤ 7.2e-13); never
  BP-vs-MAP; no hook added. PASS.
- **Final-belief + L1→L2 APP semantics**: log-domain established;
  softmax correct (no double-exp); `q @ P` verified; Bob/U1 conditioning,
  axis, positivity, normalization, uniform fallback all verified with fake
  runner (historical decoder never on the bridge path). PASS.
- **Scope/roots/authorization/overclaim**: zero production diff; R1d/G2
  roots absent (metadata); all auth keys false; no Model-F/CAL/VAL/real/raw/
  VOID/`--phase` use; unrelated dirty tree preserved; no push. PASS.

## Verdict

`D7_A_DECODER_CERTIFICATION_PASS`

Non-blocking notes: (1) cycle-3 per-sweep error growth 1e-15→7e-13 across
sweeps is fp path divergence, margin ~140× under tol; (2) redundant softmax
ternary in `_run_layered_block` is cosmetic; (3) one pre-existing unrelated
hash-pin failure from CRLF churn (`qldpc_reference.py`), untouched by D7-A.
