# Proposal: Power-of-Two Dimension Generalization

**Lifecycle**: `BACKLOG_PLAN / IMPLEMENTATION_NOT_AUTHORIZED / EXECUTE_NOT_AUTHORIZED`

## Why

The accepted NB-LDPC research line currently couples two different quantities to
1024: the physical alphabet dimension `d=1024=2^10` and the reconciliation block
length `N=1024`.  The method itself is multilevel over `GF(2^r)` and is not
mathematically restricted to either value, but the current posterior tables,
`32x32` factorization, field polynomial, matrices, leakage accounting, and frame
registry are specialized to them.

After the current NB-LDPC/Polar reference comparison is closed, add one reusable
dimension contract for arbitrary `d=2^n` without changing the accepted `d=1024`
evidence or pretending that one matrix transfers between dimensions.

## Scope

- Separate `dimension_bits=n`, layer factorization `layer_bits=[r1,...,rL]`, and
  block length `N`.
- Support a general bijection between one `d=2^n` symbol and multilevel symbols
  `U_i in GF(2^ri)`, with `sum(ri)=n`.
- Parameterize field arithmetic, empirical channel counts/posteriors, matrices,
  syndrome/leakage accounting, APP transfer, verification, and conditional
  incremental disclosure.
- Preserve the existing `n=10, layer_bits=[5,5], N=1024` path byte-for-byte as
  the compatibility anchor.
- Validate dimension generalization first at fixed `N=1024`; investigate other
  block lengths only after the dimension-only comparison passes.

## Initial validation ladder

1. Even split: `d=256 [4,4]`, `d=1024 [5,5]`, `d=4096 [6,6]`.
2. Unequal split: `d=512 [5,4]` or `[4,5]`, selected before outcomes.
3. General registry: reuse V25 factorization forms for arbitrary `2^n`, including
   more than two layers when a supported field-size or complexity bound requires it.
4. Only after the above: hold `d` fixed and test `N in {512,1024,2048}` as a
   separate factor.

## Non-goals

- No decoder run, matrix construction, or data conversion in this backlog turn.
- No claim that GF32 matrices, code rates, or leakage transfer to another field.
- No simultaneous tuning of dimension, block length, graph, labels, and decoder.
- No modification of the frozen Polar baseline or current V62 artifacts.

## Entry gate

Implementation may start only after the current best NB-LDPC result and V62
comparison are accepted and the user explicitly opens this backlog item.

