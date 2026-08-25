# V38-P0 Invalidation Review

**Cycle**: `V38P0`
**Result commit**: `6a36914e2b9bfbc5fc7e78fc8eac5e8a42759bce`
**Plan SHA**: `1b3fb4b8d0fa14c127ab895b1bbb21eb77f3414d`
**Accepted implementation SHA**: `41cad74cc6f50dad6bfed37e63bb188cbd294f77`
**Review status**: `V38_DIRECTION_EVIDENCE_INVALID`

## Finding

The V38-P0 decoder evidence is invalid for directional comparison. In
`evaluate_single_block()`, the posterior call was:

```python
get_conditional_posterior_l2(counts, u2_bob, u1_alice)
```

The second argument is required to be the complete Bob symbol `bob` in
`0..1023`, as used by the accepted V36 implementation. `u2_bob` is only the
low five-bit component in `0..31`. This is a shared input defect across every
lane and block.

## Evidence impact

- `run_01` decoder evidence is preserved but invalidated; it is not deleted,
  overwritten, or reinterpreted as a valid negative result.
- The reported `V38_NO_ROUTE_SIGNAL` terminal is invalidated.
- The 45 decoder records cannot support Lane A/B/C performance comparisons,
  the claim that low-degree routes fail, a `d_v >= 3` lower bound, or a claim
  that cycle-label optimization is ineffective.
- The 27/27 structural records remain bounded structural evidence: candidate
  generation and structural metrics were recorded, but they do not answer the
  decoder question.

## Lifecycle correction

`docs/research_cycles/V38P0/cycle_state.yaml` records
`DEVELOPMENT_RESULT_INVALID`, terminal state
`V38_DIRECTION_EVIDENCE_INVALID`, `formal_execution_authorized: false`, and
`scientific_promotion: false`. The historical
`development_execution_authorized: true` value is intentionally retained; the
run did execute once and must not be disguised as an unexecuted plan.

## Successor boundary

V38R1 is a decoder-only correction candidate. It freezes:

- the same 15 V36 A3 blocks;
- `max_iter=30`, `damping_alpha=1.0`, GF(32) polynomial `37`;
- the original triage thresholds;
- the nine run_01 winner IDs and construction seeds;
- exactly 45 future decoder calls, if separately authorized;
- additive output under `run_02`, with immutable invalid `run_01`.

The local `v38_winning_matrices.npz` is ignored by `*.npz` and is not a
committed or remote-authoritative input. A future run must reconstruct the nine
matrices deterministically from the accepted constructor and frozen winner
seeds; it must not depend on that local NPZ.

This review grants no implementation acceptance, execution authorization,
formal authorization, or scientific promotion.
