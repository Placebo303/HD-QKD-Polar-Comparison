# V38R1 Implementation Candidate Report

**Cycle**: `V38R1`
**Change**: `formal-ir-v38r1-posterior-binding-correction`
**Lifecycle**: `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Predecessor invalid result**: `V38P0`, `6a36914e2b9bfbc5fc7e78fc8eac5e8a42759bce`

## Implemented delta

`evaluate_single_block()` now passes the complete Bob symbol array `bob` to
`get_conditional_posterior_l2()` instead of the low component `u2_bob`. This is
the minimum correction needed to restore the V36 posterior contract. No graph
construction, decoder schedule, threshold, seed, or aggregation logic changed.

Two targeted tests were added:

- `test_r1_05_evaluate_single_block_passes_complete_bob_to_posterior` captures
  the second posterior argument and checks exact equality to Bob symbols that
  include values above 31.
- `test_r1_06_corrected_prior_matches_v36_numeric_sentinel` constructs a fixed
  count sentinel where the wrong and correct bindings produce different hard
  decisions, then checks the corrected V38 call path against the V36 function.

## Frozen future execution contract

V38R1 is decoder-only and may not search or retune. If independently accepted
and separately authorized, it will use the 15 V36 A3 blocks, `max_iter=30`,
`damping_alpha=1.0`, GF(32) polynomial 37, and the existing thresholds: every
source median degradation `<= 5%`, plus exact recovery `> 0` or overall median
errors `<= 150` or paired `improve_count >= 10` with `worsen_count <= 3`. It
will use the nine run_01 winner IDs/seeds, exactly 45 decoder calls, and
additive output `run_02`. The invalid run_01 is immutable. The ignored local
`v38_winning_matrices.npz` is not authoritative; future matrices must be
reconstructed from the constructor and frozen seeds.

## Verification performed

The following checks were run without production execution:

```text
python -B -m py_compile comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py comparison_bench/tests/test_v38_architecture_triage.py
8 targeted V38 pytest tests passed (R1-05, R1-06, fake-runner safety,
authorization guard, and frozen-contract checks)
3 targeted V35 regression tests passed (seed/frozen-directory/CLI parser checks)
openspec validate: unavailable (`openspec` command is not installed)
```

The complete V38 Lane-A-heavy suite was not rerun in this candidate turn. No
real decoder, DE, run_02, tuning, or seed search was performed. Independent
implementation acceptance remains pending.
