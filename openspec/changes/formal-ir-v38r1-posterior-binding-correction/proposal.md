# OpenSpec Proposal: formal-ir-v38r1-posterior-binding-correction

**Status**: `DEVELOPMENT_RESULT_ACCEPTED / FORMAL_NOT_AUTHORIZED`
**Domain**: Formal Information Reconciliation / Nonbinary LDPC research
**Change ID**: `formal-ir-v38r1-posterior-binding-correction`
**Predecessor cycle**: `V38P0`
**Accepted plan SHA**: `1b3fb4b8d0fa14c127ab895b1bbb21eb77f3414d`
**Accepted predecessor implementation SHA**: `41cad74cc6f50dad6bfed37e63bb188cbd294f77`
**Invalid predecessor result SHA**: `6a36914e2b9bfbc5fc7e78fc8eac5e8a42759bce`

## Why

The V38-P0 `run_01` decoder comparison used the wrong representation for Bob
in the empirical posterior call. `get_conditional_posterior_l2()` indexes the
1024-column Bob-symbol axis and therefore requires the complete symbol in
`0..1023`. V38 passed `u2_bob`, the low GF(32) component in `0..31`. Because the
same malformed prior was used for all three lanes, the 45 decoder records
cannot support the published `V38_NO_ROUTE_SIGNAL` conclusion.

## Scope

This change produces an implementation candidate only:

1. Correct one posterior argument binding from `u2_bob` to complete `bob`.
2. Add a parameter-capture test with Bob values greater than 31.
3. Add a fixed numerical sentinel proving wrong and correct posterior hard
   decisions differ and that the corrected call equals the V36 call.
4. Record V38-P0 invalidation and freeze a decoder-only V38R1 successor.
5. Provide a guarded decoder-only runner that reconstructs the nine frozen
   winners from the committed run_01 metrics and an additive run_02 writer.
6. Keep the test-only fake evaluator callable only through Python test
   functions, require the formal CLI to bind the real evaluator, and perform
   a decoder-free nine-matrix reconstruction preflight.

No execution is performed by this candidate. The runner is implemented for a
future separately authorized run, but production decoder execution, DE,
parameter tuning, seed search, run_02 creation, and promotion remain out of
scope for this implementation turn.

## Lifecycle

The candidate ends at `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`.
Independent review must accept the candidate before a new explicit user
`EXECUTE_AUTH` may authorize exactly one additive V38R1 `run_02`.
