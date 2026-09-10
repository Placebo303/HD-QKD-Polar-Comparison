# D7-D flooding certification R1 (F01–F08)

- Status: **PASS** — all eight required items pass; no counterexample exists;
  `decode_flooding_fftqspa` is not patched.
- Scope authority: D7-D task packet §5, prereg `D7_D_PREREG_R1.md` §6. This
  gate is separate from the ten run terminals and precedes readiness.
- Fixtures: tiny synthetic in-memory graphs only (q=32 GF(2^5), polynomial
  poly 37, n_vars ≤ 4, check degree 2–3). Independent ground truth is the
  accepted D7-A oracle
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_decoder_certification.py`
  (`direct_check_to_var`, `exact_posterior`, `syndrome_reference`).
- Tolerance: max-abs ≤ `1e-10` on probabilities/posteriors.
- Evidence: `comparison_bench/tests/test_v72p2d7_gf32_schedule_discriminator.py`
  tests `test_f01`–`test_f08`; command
  `python -m pytest comparison_bench/tests/test_v72p2d7_gf32_schedule_discriminator.py -k test_f0 -q`.
  Observed run: 8 passed.

## Interpretation of "no production decoder call" (packet §11)

The §11 boundary forbids production-scale / scientific decoder execution and
real Model-F content. Packet §5 explicitly requires tiny synthetic
production-decoder contacts for F01–F05: these tests call the existing
`v35.decode_flooding_fftqspa` on ≤4-variable in-memory graphs. They are the
intended certification contacts, not a production call: no Model-F, no
evidence root, no 64-symbol production graph and no scientific configuration
is touched. The frozen 256-call D7-D path remains untriggered by every test.

## F01–F08 results

| Item | Required check | Result | Evidence (observed) |
|------|----------------|--------|---------------------|
| F01 | Direct check update remains the certified kernel (reuse D7-A enumeration/check oracle) | PASS | `v35._check_update_log_batch` vs `oracle.direct_check_to_var`: deg-2 `(1,c)` sweep c∈{1,2,7,13,29,31} × syndrome∈{0,5,17,31} and deg-3 triples, nonzero coefficients; max-abs error 2.776e-17 ≤ 1e-10 |
| F02 | Single-check full posterior equals exact enumeration within 1e-10 | PASS | deg-2 `H=[[1,7]]`, skewed prior peak 17, syndrome 5: max-abs 6.661e-16; deg-3 `H=[[1,2,13]]`, syndrome 17: 4.441e-16; softmax rows normalized |
| F03 | Two-check tree full posterior/MAP equals exact enumeration after sufficient flooding iterations | PASS | chain `H=[[1,2,0],[0,3,1]]`, seed-2026091002 random prior, perturbed syndrome; returned 2 sweeps; posterior max-abs 1.388e-16; `x_hat` equals enumeration MAP |
| F04 | One flooding iteration matches an independently written flooding recurrence | PASS | 3-cycle `H=[[2,1,0],[0,3,1],[1,0,5]]`, prior peak 9, syndrome (5,0,17), `max_iter=1`: max-abs 1.166e-15 (deg-3 single check also ≤1e-10). The recurrence is written in the test from the flooding schedule definition and uses the D7-A check oracle, not production code |
| F05 | Iterations 1/2/3 on a small cycle match independent per-iteration beliefs within 1e-10 (loopy BP vs independent BP, never MAP) | PASS | 3-cycle: sweeps 1/2/3 returned exactly 1/2/3 with max-abs 1.17e-15 / 2.22e-16 / 1.16e-13; 4-var deg-3 fixture: 1.25e-16 / 1.11e-16 / 2.91e-16. Comparison is per-iteration BP-to-BP; no MAP comparison |
| F06 | Nonzero coefficients and syndromes with negative-direction controls | PASS | `H=[[3,7]]`, syndrome 17: production vs correct recurrence 2.22e-16; vs wrong coefficient direction 1.667e-01 (>1e-6); vs wrong syndrome shift 1.667e-01 (>1e-6); coefficients and syndrome nonzero |
| F07 | Cold start, normalization, stopping, `final_beliefs` current-state semantics explicit, including iteration-0 `PRIOR_ONLY` | PASS | flooding signature has no `damping_alpha`/`warm_beliefs`; first sweep equals independent recurrence seeded by `log(clean(prior))`; unnormalized prior gives identical output (delta 0.0); non-converging 3-cycle sweeps exactly `max_iter` with `status ≠ converged_exact`; `final_beliefs` equals the returned sweep's current state, not the prior; `_belief_label(0)=PRIOR_ONLY_CURRENT_BELIEF`, `_belief_label(3)=CHECK_UPDATED_CURRENT_BELIEF`; row-layered cold initial-syndrome match returns `iterations=0`, `converged_exact` |
| F08 | No real Model-F, production evidence or formal root is read | PASS | Model-F loaders (`d7c.d5._load_model_f_input_or_blocked`, `d7c._default_model_f_loader`) poisoned to raise during the F contacts and never invoked; Model-F root metadata unchanged; no `workspace/d7_d_schedule_discriminator_*` root; `_EXECUTION_CONSUMED` false; formal-root/protected list includes the accepted Model-F root |

## Certification statements

- No F item failed; no minimal counterexample needed and none preserved.
- `v35_algorithm_development.py`, `v72p2d5_gf32_rate_mother.py`, the D7-A
  oracle and the D7-C module are read-only and unmodified by this
  certification.
- The F04/F05 independent recurrences are test-local; they call only the
  D7-A oracle check update, never production decoder internals.
- Certification gate verdict: **F01–F08 PASS**, D7-D readiness may continue to
  implementation/qualification review.
