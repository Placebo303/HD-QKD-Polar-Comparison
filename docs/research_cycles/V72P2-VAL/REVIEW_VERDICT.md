# V72P2 main review record

## Plan preparation, 2026-09-03

Main independently inspected the accepted V72P1 source/records, four OpenSpec artifacts, SOP and adapter code; luna_worker independently inspected prior/data registry and source existence without reading parquet. Live git ls-remote confirms base cd0b0e77c5cedbf3ac74d271cff3d6649f7043fc; tracked diff was empty before this new plan.

The bounded proposal follows the user's plan/execute delegation. Two successor corrections are explicit: first warm residual previously used magnitude; returned run_decoder APP previously used pre-update sums. Historical V72P1 acceptance is preserved as historical evidence, not proof these new semantics were already tested. No other algorithm optimization is included.

Awaiting plan commit binding. Implementation and real execution are not yet released. The main reviewer will record acceptance of this exact plan in the next milestone; the worker cannot selfaccept.

## Plan acceptance, 2026-09-03

Target plan SHA: a97b23cee38a83d32ad67cd56d6c722b7e8e3de6.
Main independently verified live remote equals local HEAD at this SHA following the user's explicit "允许推送并继续" authorization. Eight-file plan manifest only; no real data included. Verdict: PLAN_ACCEPTED for the bounded design and packet. Prior/CAL separation, fixed36VAL IDs, actual iteration accounting, current-candidate verification, monotonic disclosure and narrow adapter correction have been reviewed against source.

Release: luna_worker may implement the four listed Python files and run the frozen synthetic/fake tests. Real-data decoding remains unreleased until main Pre-EXECUTE. Acceptance here is the main reviewer's decision under the user's delegation, not an operator self-PASS. This record will be committed with the implementation candidate, per packet.

## Candidate review and explicit timing amendment

Main read the runner, focused tests and adapter diff. An operator's out-of-scope _factor_batch_numba optimization was discovered and removed; the final adapter diff is restricted to run_decoder (23 added/4 removed). The optimized diagnostic timing is excluded. Completed-iteration accounting on numeric failure and nonzero cross-block-reset tests are included. T0 compile/diff-check exit0; combined regression exit1 with29 passed/1 failed in66.77s. The failure is solely historical P1C one-iteration1.046s versus <1s, not the overall50.891s versus a30s bound. Actual three/ten-iteration1.297/1.313s pass. Main independently parsed workspace/v72p1_rework_tests/9651abe2/v72p1_results.json: finite/nonzero/hard_bits_ok/ck_ok true,72 checkpoints,144 total iterations; residuals and maxLLR finite/in bounds.

Main approves the explicit V72P2 plan amendment under AGENTS first principle: preserve and disclose that timing regression, keep all numerical gates and real deadlines, no optimization/timing-success claim. The old test remains FAILED. The corrected final readout requires additional local-factor work. Plan amendment and candidate code will be bound to their new committed SHA before any real read/decoder invocation. Pre-EXECUTE remains pending.
