# Delta Specification: formal-ir-v38r1-posterior-binding-correction

## R1.1 Invalid predecessor evidence

The V38-P0 result commit `6a36914e2b9bfbc5fc7e78fc8eac5e8a42759bce` SHALL be
classified as `V38_DIRECTION_EVIDENCE_INVALID`. Its 45 decoder records SHALL be
preserved immutably but SHALL NOT support `V38_NO_ROUTE_SIGNAL`, lane
performance conclusions, a `d_v >= 3` lower bound, or a conclusion that cycle
optimization is ineffective. The 27/27 structural records MAY remain bounded
structural evidence.

## R1.2 Posterior binding

`evaluate_single_block()` SHALL call
`get_conditional_posterior_l2(counts, bob, u1_alice)` with complete Bob symbols
in `0..1023`. It SHALL NOT pass `u2_bob` as the second argument.

## R1.3 Tests

The candidate SHALL include:

1. a capture test that supplies and observes Bob symbols greater than 31 and
   proves the exact complete-symbol argument is forwarded;
2. a numerical sentinel in which the wrong low-layer and correct complete-Bob
   calls have materially different posterior hard decisions; and
3. an equality check showing the corrected V38 call path matches the V36
   complete-Bob call element by element.

These tests SHALL use fake/test-only execution and SHALL NOT invoke a production
decoder.

## R1.4 V38R1 successor freeze

Any future authorized successor SHALL reuse the same 15 V36 A3 blocks,
`max_iter=30`, `damping_alpha=1.0`, GF(32) polynomial `37`, and the existing
thresholds: every source median degradation `<= 5%`, plus exact recovery `> 0`
or overall median errors `<= 150` or paired `improve_count >= 10` with
`worsen_count <= 3`. It SHALL use the nine run_01 winner IDs/seeds and
reconstruct those matrices from
the accepted constructor and seeds, perform exactly 45 decoder calls, and write
only additive `run_02`. The existing run_01 SHALL remain immutable invalid
evidence. The ignored local NPZ SHALL NOT be an input dependency.

## R1.5 Lifecycle

This change SHALL stop at
`IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`. Independent acceptance and
a new explicit user `EXECUTE_AUTH` bound to the accepted target SHA are required
before any run_02 decoder execution.

## R1.6 Guarded runner and writer

The change SHALL provide `run_v38r1_development()` with a default-deny
authorization guard. With explicit authorization it SHALL reconstruct exactly
nine frozen winners from the committed run_01 structural metrics, issue exactly
45 calls using the frozen 15 blocks and decoder parameters, and reuse the V38
aggregation and terminal-gate functions. The test-only `fake_runner` path SHALL
be supported.

`scripts/execute_v38r1_development.py` SHALL require the explicit
`--development-execution-authorized` flag, call only the V38R1 runner and its
writer, and write only fixed additive `run_02` evidence. If the output path
already exists it SHALL fail closed without overwriting. The writer SHALL emit
nine winner metrics, 45 block records in CSV/JSON, and a summary JSON, and SHALL
not emit or read `v38_winning_matrices.npz`.
