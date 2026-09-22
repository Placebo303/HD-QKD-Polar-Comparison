# D7-D implementation review R1 (independent)

- Reviewed revision: HEAD `43f071868a497b4ca5fd1f2db7eaea3a08146651`
  (`feat(d7-d): implement schedule discriminator with flooding certification`).
  The commit adds exactly four files (1395 + 1535 + 104 + 50 lines, 0 deletions).
- Reviewer: independent implementation reviewer (reviewer-go); did not author the
  reviewed implementation.
- Authority: `D7_C_ACCEPT_D7_D_SCHEDULE_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`
  sections 4-12 and 14; `D7_D_PREREG_R1.md`; `D7_D_EXECUTION_PACKET_R1.md`
  (commit `3a05899`); D7-C template module/test/runner; `v35_algorithm_development.py`
  L529/L636; `v72p2d7_gf32_decoder_certification.py` (D7-A oracle).
- Verdict: **D7_D_IMPLEMENTATION_REVIEW_PASS**.
- Method: source inspection plus independent re-execution. All reviewer commands
  ran with a fresh `/tmp` basetemp and `-p no:cacheprovider`. No D7-D scientific
  call, no Model-F binary content read, no output root, no UUID, no
  authorization change, no push.
- Commands and observed results:
  - `python -m pytest comparison_bench/tests/test_v72p2d7_gf32_schedule_discriminator.py -k "test_f0" -q -p no:cacheprovider --basetemp=/tmp/d7d_review_f08b`
    -> `8 passed, 22 deselected` in 2.90 s.
  - `... test_v72p2d7_gf32_schedule_discriminator.py -q -p no:cacheprovider --basetemp=/tmp/d7d_review_full`
    -> `30 passed` (22 S-items + 8 F-items; collection = 30 tests) in 114.33 s.
  - `... test_v72p2d7_gf32_bidirectional_oracle.py -q -p no:cacheprovider --basetemp=/tmp/d7c_review_raw`
    -> `1 failed, 19 passed` in 57.16 s (only the stale `test_c19`, section 8).
  - Certification subset re-run around a stat of `workspace/.pytest_cache`:
    cache untouched, `workspace/` listing untouched.

## 1. Flooding certification F01-F08

Source inspection confirms the F matrices are real, independent checks:

- F01 exercises the production kernel `v35._check_update_log_batch` against
  `oracle.direct_check_to_var` (D7-A enumeration oracle) on deg-2 and deg-3
  checks with nonzero coefficients and multiple syndromes; the `TOL = 1e-10`
  assert is real.
- F02/F03 compare full softmax posteriors against `oracle.exact_posterior`
  (assignment enumeration) with `<= 1e-10` asserts; F03 also pins
  `res.iterations >= 2` and compares the MAP to the enumerated MAP.
- F04/F05 use `_indep_flooding`, a test-local recurrence written from the
  flooding schedule definition. It calls only `numpy` and the D7-A
  `direct_check_to_var` oracle; it never calls `_check_update_log_batch`,
  `decode_flooding_fftqspa` or any production internals. F05 sweeps 1/2/3 on
  two fixtures and pins `res.iterations == k` so an early production stop cannot
  mask a mismatch; comparisons are loopy-BP-to-BP, never MAP.
- F06 negative controls `_wrong_direction_check` (coefficient inverse) and
  `_wrong_shift_check` (syndrome shift) are asserted to differ from production
  by `> 1e-6`; the fixture has only nonzero coefficients/syndrome.
- F07 pins the flooding signature (no `damping_alpha`, no `warm_beliefs`), cold
  start seeded by `log(clean(prior))`, unnormalized-prior invariance, exact
  `max_iter` stopping with `status != converged_exact`, current-state
  `final_beliefs` at sweeps 1/2/3, and iteration-0 `PRIOR_ONLY` both for
  `_belief_label(0)` and a real `decode_row_layered_fftqspa` cold
  initial-syndrome match (`iterations=0`, `converged_exact`).
- F08 poisons `d5._load_model_f_input_or_blocked` and
  `d7c._default_model_f_loader` to raise, runs the tiny F contacts, and asserts
  Model-F root metadata unchanged, no `workspace/d7_d_schedule_discriminator_*`
  root, `_EXECUTION_CONSUMED` false, and the Model-F root in `PROTECTED_ROOTS`.

Reviewer reproduction of the certification doc numbers (importing the test's own
fixtures; no repo writes):

| Item | Doc value | Observed |
|------|-----------|----------|
| F01 deg-2 sweep | 2.776e-17 | 2.2204e-16 (max at (1,c=1,syn=0,t=0)); see section 11 |
| F02 `H=[[1,7]]` | 6.661e-16 | 6.661e-16 |
| F03 | 1.388e-16, 2 sweeps, MAP equal | 1.3878e-16, 2 sweeps, MAP equal, syndrome_ok |
| F04 cycle | 1.166e-15 | 1.166e-15 (deg-3 fixture 8.88e-16) |
| F05 fixture 1 | 1.17e-15 / 2.22e-16 / 1.16e-13 | 1.166e-15 / 2.220e-16 / 1.157e-13 |
| F05 fixture 2 | 1.25e-16 / 1.11e-16 / 2.91e-16 | 1.249e-16 / 1.110e-16 / 2.914e-16 |
| F06 | wrong-direction 1.667e-01 | correct 2.22e-16, wrong_c 1.667e-01, wrong_s 1.667e-01 |
| F07 | unnormalized delta 0.0; sweeps=3, not converged | delta 0.0; 3 sweeps; `converged_no_syndrome` |

Reviewer-written cross-check on fixtures not used by the test suite (own
recurrence, `/tmp` only): F02-style error 6.9e-17, F04-style 1.25e-16,
F05-style 5.6e-16, all `<= 1e-10`. Certification verdict **F01-F08 PASS**
confirmed; no counterexample needed; flooding is not patched.

## 2. Work-normalized arithmetic

- `evaluate_call` computes `check_node_updates = rows * completed_iterations`
  and `check_edge_updates = nnz(H_prefix) * completed_iterations`;
  iteration-0 is exactly 0. `_row_degree_sums(mothers)` stores, per layer and
  disclosed-rows value, `nnz(mother[:rows])`, i.e. the sum of the disclosed-row
  degrees used by the verifier.
- Reviewer explicit-matrix check (49 rows, `nnz=4`): iterations 0/1/7/90 give
  node/edge updates 0/0, 49/4, 343/28, 4410/360. Reviewer `compute_paired_rows`
  checks: `wall_ratio` empty when the layered wall is 0 or non-finite;
  `iteration_diff`/`check_update_diff`/`edge_update_diff` empty when either
  record is a crash, non-finite or non-complete; only complete pairs produce
  differences.
- No winner-from-iterations: no `winner` field exists; `classify_stratum` and
  `classify_terminal` consume exact-count flags only; S09 inverts iteration
  differences and observes identical terminal and strata.
- Provenance: `PRIOR_ONLY_CURRENT_BELIEF` at iteration 0 else
  `CHECK_UPDATED_CURRENT_BELIEF`; `_check_record_semantics` rejects
  `posterior`/`app` label tokens; no "posterior" wording for current beliefs
  anywhere in the core/runner.

## 3. Exact pairing, matrix and D7-C contract

- 128 identities (16 seeds x 2 f x 4 conditions) and 256 calls with
  `call_idx = 2k-1 / 2k`; schedule order `("ROW_LAYERED", "FLOODING")`; order
  `for f: for seed: for condition: ROW_LAYERED; FLOODING`. S02 pins first/last
  identities (rows 49 / 52) and stride-4 condition blocks.
- S03 captures decoder inputs per schedule: `H_prefix`, `prior_pq`, `syndrome`
  arrays are byte-identical within each pair; shapes `(rows,64)`, `(64,32)`,
  `(rows,)`.
- Constants are direct D7-C aliases (`d7d.X is d7c.X` where scalar): estimator
  id, `LAMBDA_STAR=137.3823795883264`, `DECODER_FLOOR=1e-15`, `MAX_ITER=90`,
  rows/mothers/seeds, prior functions. `prepare_inputs` delegates to
  `d7c.prepare_inputs` (H03 `prepare_model_f_prior_candidate` ->
  `build_f_model_concentration`, four direct priors, 16 seeds, sampling once per
  seed).
- Reviewer spy on `bind_schedule_decoders()`: ROW_LAYERED calls
  `max_iter=90, damping_alpha=1.0, warm_beliefs=None, field=None`; FLOODING
  calls `max_iter=90, field=None` with no damping/warm-start parameter.
- Note (non-blocking, section 11): ROW_LAYERED binds
  `v35.decode_row_layered_fftqspa` directly instead of going through
  `d5.bind_historical_decoder()`; it is the same underlying function with the
  same kwargs (D5's `_load_g0_decoder()` returns that exact function).

## 4. Classifications and terminals

- `classify_stratum` first-match order matches prereg section 9 exactly
  (flooding >= 4/<=1, layered >= 4/<=1, tie-high both >= 12/<=1 each, tie-low
  neither >= 12/<=1 each, else mixed); boundary cases in S10 pass
  (e.g. `(4,1,12,0)->FLOODING`, `(3,0,13,0)->MIXED`, `(0,0,0,16)->TIE_LOW`).
- `TERMINALS` is the exact ten-string priority; `classify_terminal` is
  first-applicable T1..T10; T6 = `flooding>=2 and layered==0`, T7 the converse,
  T8 both directions, T9 requires all 128 pairs present and equal flags.
  S11 covers every single-flag stop, full priority ordering with all stops set,
  and T6/T7/T8/T9/T10 boundaries.
- All eight strata are always emitted (2 f x 4 conditions); a label is assigned
  only when all 32 stratum calls are complete, non-crash and finite, otherwise
  partial counts + empty label, exactly as prereg section 9 requires.

## 5. Writer / verifier / schema

- Writer emits exactly the seven frozen files into a fresh root; refuses an
  existing root (even empty), any subdirectory, and non-scalars/unknown record
  fields; CSV field header order equals the frozen field lists.
- `verify_root` reads only the seven files: checks the file manifest, schema
  headers, per-position identity/order against `frozen_call_matrix()`,
  duplicate `call_idx`, crash-record consistency, `iterations` in 0..90,
  `beliefs_conditioned == iterations>0`, label correctness, exact ==
  symbol_errors==0, syndrome consistency, node/edge update arithmetic against
  the manifest's frozen row-degree sums, belief ranges, then independently
  recomputes paired rows, all eight strata and the terminal, plus summary
  counts/wall/retries. It never binds a decoder or loads Model-F.
- S16 detects appended duplicate, missing line, unpaired call, tampered
  exact/syndrome/edge-update/paired/stratum/terminal/manifest values and an
  extra file; a legitimately truncated watchdog root still verifies. Reviewer
  spot checks of pair suppression and the T9 completeness gate agree.

## 6. Isolation

- Import/`--help`/`--dry-run`/`--verify`/unauthorized paths bind no decoder and
  read no Model-F. Reviewer ran the runner from `/tmp`: `--help` exit 0;
  `--dry-run` printed the header plus exactly 256 call lines (first two
  ROW_LAYERED/FLOODING of identity 1); an unauthorized run with a valid target
  name returned 3 with `D7-D execution is not authorized` and created no root.
  S17 additionally proves `v35_algorithm_development` is absent from
  `sys.modules` after `--dry-run`.
- Production binds are lazy: `_load_v35` and `bind_schedule_decoders` are only
  reached when `decoder_fns is None` and the authorization key is true; the
  single-use `_EXECUTION_CONSUMED` guard is set only on a production bind.
- The 256-call scientific path is unreachable from tests: every
  `run_schedule_discriminator` call injects fake decoders; the only production
  decoder contacts are the tiny `<=4`-variable F01-F05/F07 certification
  fixtures. S18 external-cwd sentinels prove `dispatch_schedule` routes to the
  two schedules with the exact bound production targets and frozen array shapes
  without calling them.
- S22 static scan found no cross-layer APP, CAL/VAL/raw/phase, R1d/G1/G2,
  `prepare_model_f_prior(`/`build_f_model(` or workspace/results path in the
  core or runner.

## 7. S01-S22 and suite counts

All 22 S-items exist and assert what packet section 11 requires: S01 doc +
F-matrix; S02 matrix/order; S03 pairing; S04 estimator/priors; S05
rows/mothers/seeds; S06 exact/syndrome separation; S07 iteration-0 provenance;
S08 work arithmetic; S09 no iteration winner; S10 strata boundaries; S11
terminals; S12 hard cap/no retry; S13 120/1500/1800/2GiB gates; S14 stdlib RSS
fail-closed; S15 seven-file schema; S16 verifier tamper matrix; S17 isolation;
S18 dual sentinels; S19 fake full 256-call runs for T1-T10 (T5 via
`terminal_from_records` on 40 records); S20 D7-A/C/D5/D7-B/v35 inner suites;
S21 protected-root lifecycle + D7-B/C immutability; S22 forbidden paths.
Full new suite: **30 passed** (22 S + 8 F) in 114.33 s.

## 8. D7-C raw C19 regression classification

Raw D7-C suite (no deselection): `1 failed, 19 passed`. The failure is
`test_c19_protected_root_lifecycle_and_g2_r1d_absence` at its
`assert list(WS.glob(bo.OUT_ROOT_PREFIX + "*")) == []` line, because the
accepted D7-C root
`workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae`
now exists as frozen baseline (and the same test's `decoder_executed is False`
assertion is stale too).

Classification: **legitimate stale pre-execution environmental invariant**,
pre-existing (the test was written in `391fc6b0` before the D7-C execution), not
caused by D7-D, and not hiding a D7-C regression: the other 19 D7-C tests pass,
and the D7-D S20 deselection is scoped to exactly that one test with the reason
recorded in the test docstring and comment. The packet forbids modifying D7-C,
so deselect-with-documentation is the correct in-scope behavior. **Does not
block.** Suggested follow-up (separate scoped change, e.g. closeout): refresh
`test_c19` to post-acceptance invariants (root exists and is immutable;
`decoder_executed`/`result_created` true) so the full D7-C suite is green
without deselection.

## 9. Protected roots, authorization, no-root, no-push

- D7-C root: six files present with the exact frozen sizes
  (282 / 23599 / 2709 / 1130 / 362 / 728 B); size+mtime diff identical before and
  after the reviewer's full-suite run.
- Model-F root metadata (names/sizes/mtime) read-only and unchanged; its binary
  content was never opened by the reviewer or by the tests (directory metadata
  only, injected loaders in tests).
- `workspace/d7_d_schedule_discriminator_*`: absent before and after all
  reviewer runs; no UUID created.
- D7-D `cycle_state.yaml`: every authorization flag false
  (`implementation_authorized`, `d7d_execution_authorized`,
  `formal/synthetic/real_execution_authorized`, `scientific_promotion`,
  `g1_authorized`, `g2_authorized`), `decoder_executed: false`,
  `result_created: false`; `layer_interface_implementation` starts with
  `DEFERRED`. D7-C state confirmed accepted predecessor, authorizations false.
- No push: branch remains `ahead` of
  `origin/formal-ir-v72p1-addendum-clean`; the review commit is local only.

## 10. Forbidden changes

- HEAD `43f07186` adds only the four authorized new files and deletes nothing
  (`git show --numstat`: 4 files, insertions only).
- D7-A/B/C modules and tests, D7-C runner, v35, D5, the OpenSpec change and the
  D7-D prereg/execution packet are byte-unchanged at HEAD and unchanged in the
  worktree (`git diff HEAD -- <paths>` = 0 lines).
- Pre-existing dirty worktree (preserved, unrelated to D7-D):
  `docs/research-cycle-sop.md`, `docs/v35-algorithm-development-report.md`,
  `workspace/pytest-evidence-test/output/expanded_evidence_manifest.json`, plus
  CRLF/stat noise. Packet section 2 requires preserving these.

## 11. Non-blocking observations

1. Certification doc F01 quoted value: the doc states max-abs 2.776e-17 for the
   F01 kernel sweep; the reviewer's verbatim re-execution of the same test body
   observes 2.2204e-16 (still far below the 1e-10 gate; all other doc values
   reproduce, F02-F07 to the quoted digits). Cosmetic evidence-value
   discrepancy; it does not affect the PASS. If the exact figure matters for
   provenance, restate it as observed or refresh the row in a scoped docs
   commit (not this review).
2. ROW_LAYERED binding path: direct `v35.decode_row_layered_fftqspa` bind rather
   than `d5.bind_historical_decoder()`. Same function object, same kwargs,
   numerically identical; only the wrapper container differs (raw
   `DecoderResult` instead of D5's dict, so the recorded `status` is the true
   decoder status rather than the wrapper's default). Manifest `decoder_ids`
   documents the direct shape. Recommend one clarifying line in the Pre-EXECUTE
   review or closeout so Pre-RESULT readers are not surprised by status values.
3. Verifier edge-update check validates against the manifest's
   `row_degree_sums` (written from the in-memory frozen matrix), not a
   recomputation from the deterministic matrix. Scalar tamper is caught (S16);
   a consistent dual tamper of manifest+record is outside the trusted-local
   threat model. Optional hardening only.
4. Environmental note: the required S20 regression runs the frozen D7-B suite,
   whose own nested L10 run uses `-o addopts=` (no `-p no:cacheprovider`) and
   therefore refreshes the gitignored `workspace/.pytest_cache`. The
   certification subset itself writes no repo path. Pre-existing upstream test
   behavior, not a D7-D defect and not git-visible.

## 12. Verdict

- Blocking issues: none.
- Verdict: **D7_D_IMPLEMENTATION_REVIEW_PASS**.
- One scoped implementation rework is not needed; scientific ambiguity does not
  arise. Next gate per packet section 13: independent Pre-EXECUTE review; all
  authorizations remain false, no D7-D root/UUID, no execution.
