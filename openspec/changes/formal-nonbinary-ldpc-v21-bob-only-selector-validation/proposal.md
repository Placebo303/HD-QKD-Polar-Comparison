# Proposal: formal-nonbinary-ldpc-v21-bob-only-selector-validation

> Status: DRAFT — prepared from V20 audit; awaiting task-packet acceptance.

## What
Validate Bob-only executable decoding strategies for q=1024 nonbinary LDPC at
f≤1.3. Unlike V20, candidate generation/selection must not access Alice; Alice is
only used for final offline metrics. Report executable FER separately from oracle
list coverage.

## Why
V20 audit showed:
- `31/64` is an oracle-aided best-of cascade upper bound.
- `40/96` is top-4 oracle list coverage.
- standalone bounded4 `30/64` is an unverified Bob-only estimate.
The reported numbers cannot be interpreted as executable decoder FER until a
Bob-only selector is implemented and verified.

## Scope
- Add V21 modules under `comparison_bench/` only.
- Implement and compare S0 BP-only, S1 bounded4-only, S2 BP-first-fallback-bounded4.
- Add semantic verifier ensuring decoder selection does not access Alice.
- Use fresh synthetic seeds; do not reuse V19/V20 tuning frames.
- Record syndrome_bits, public_bits, verification_bits, f_total.

## Out of scope
- Modifying frozen `src/`, `experiments/`, `tools/`, `results/`.
- Fresh/promotion/qualification claims.
- Unbounded tuning/rerunning of V19/V20 evidence.
- Real-data legacy execution unless separately authorized.

## Claim boundary
`diagnostic_only` until a Bob-only success is independently verified.
