# OpenSpec Design: formal-ir-v38r1-posterior-binding-correction

**Lifecycle**: `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Predecessor**: V38-P0 invalid result, `6a36914e2b9bfbc5fc7e78fc8eac5e8a42759bce`

## 1. Root-cause correction

`factorize_f03(alice, bob)` returns `(u1_alice, u2_alice, u1_bob,
u2_bob)`. The posterior API is `get_conditional_posterior_l2(counts, bob,
u1)`, where `bob` indexes the complete 1024-symbol observation axis. The
implementation delta is exactly:

```diff
- prior = get_conditional_posterior_l2(counts, u2_bob, u1_alice)
+ prior = get_conditional_posterior_l2(counts, bob, u1_alice)
```

No decoder, constructor, threshold, seed, schedule, or aggregation logic is
otherwise changed.

## 2. Test contract

- R1-05 monkeypatches the sampler and posterior, supplies Bob symbols above
  31, and asserts the captured posterior argument equals complete `bob` exactly.
- R1-06 builds a fixed count matrix with distinct high-probability entries for
  complete Bob and low-layer Bob. It asserts different posterior hard
  decisions, a large numerical difference, and exact equality between the
  corrected V38 call path and the V36 posterior function.
- Tests call `evaluate_single_block(..., fake_runner=True)` and therefore do
  not invoke the production decoder.

## 3. Frozen future V38R1 decoder-only successor

If independently accepted and separately authorized, V38R1 shall:

- reuse exactly the 15 V36 A3 blocks:
  - 1M: `360101..360105`;
  - 1p5M: `360201..360205`;
  - 2M: `360301..360305`;
- use `max_iter=30`, `damping_alpha=1.0`, GF(32) polynomial `37`;
- use the existing V38 triage thresholds without reinterpretation: every source
  median degradation `<= 5%`, then at least one of exact recovery `> 0`, overall
  median errors `<= 150`, or paired `improve_count >= 10` with
  `worsen_count <= 3`;
- reconstruct exactly the nine run_01 winner matrices from the accepted
  constructor and these frozen winner IDs/seeds:
  - Lane A: `381101`, `381201`, `381301`;
  - Lane B: `382103`, `382201`, `382301`;
  - Lane C: `383103`, `383203`, `383301`;
- make exactly 45 decoder calls (15 per lane);
- write only additive `comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_02/`;
- preserve run_01 as immutable invalid evidence.

The local `v38_winning_matrices.npz` is ignored by `*.npz`, was not committed,
and is not an authoritative remote input. Matrix reconstruction must not depend
on it.

## 4. Authorization boundary

This candidate does not authorize development or formal execution. The main
thread owns independent acceptance. A future `run_02` requires a new explicit
user authorization bound to the accepted V38R1 target SHA.
