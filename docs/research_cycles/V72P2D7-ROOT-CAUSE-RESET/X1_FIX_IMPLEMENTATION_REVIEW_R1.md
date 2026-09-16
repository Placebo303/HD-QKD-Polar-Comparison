# X1 fixture fix — independent implementation review R1

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Reviewer context: independent implementation review in a separate context,
  assigned by the main thread on 2026-09-13; read-only over the scoped fix,
  tests, and code paths. The X1 probe was not re-executed by the reviewer;
  nothing was repaired, tuned, cleaned, or committed.
- Artifacts under review: the scoped fixture fix recorded in
  `X1_FIX_AND_RERUN_NOTE_R1.md` (§2), the changed file
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
  (`_probe_fixture` only), the focused test additions/update in
  `comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py`, and the
  mandated `cycle_state.yaml` marker correction.
- Supersedes nothing: `X1_FAILURE_VERIFICATION_R1.md` (root cause of the
  R1 failure) remains valid history.

## 1. Verdict

**`PASS_WITH_FINDINGS`** — no blockers. By code analysis the fixed default
fixture deterministically satisfies the frozen X1 success contract
(`CHECK_UPDATED`, finite shape-valid beliefs, `iterations >= 1`, exit 0), and
the fix stays inside the authorized fixture-only scope. The rerun remains
gated on the explicit `x1_consistency_probe_authorized` flag.

## 2. Deterministic-contract statement (verified against code)

- Fixture (`_probe_fixture`): `h = [[1, 1], [1, 2]]` over GF32 (poly 37),
  uniform prior shape `(2, 32)`, `syndrome = [1, 2]`, `x_true = [0, 1]`.
- Consistency: `H @ x_true = (1*0 + 1*1, 1*0 + 2*1) = (1, 2)` equals the
  syndrome, so the fixture is a valid decode instance.
- Early-return guard cannot fire: the guard at
  `v35_algorithm_development.py:835` compares
  `syndrome_of_gf32(h, argmax(prior))` with the syndrome;
  `argmax(uniform prior)` is the all-zero word and `H @ 0 = (0, 0) != (1, 2)`.
  The iteration-0 `PRIOR_ONLY` path is therefore unreachable for this fixture.
- Both decoder exit paths return `CHECK_UPDATED` with `iterations >= 1`:
  - converged exit (`v35_algorithm_development.py:890-909`):
    `iterations = it` with `it >= 1` (loop starts at 1), provenance
    `CHECK_UPDATED`;
  - non-converged exit (`v35_algorithm_development.py:911-936`):
    `iterations = max_iter = 90 >= 1`, provenance `CHECK_UPDATED`.
- Shape/finiteness: the bound historical decoder
  (`bind_historical_decoder`; `max_iter=90`, `damping_alpha=1.0`,
  `warm_beliefs=None`) returns `final_beliefs` with the prior's `(2, 32)`
  shape, computed from a finite uniform prior and finite FWHT check messages;
  the R1 failure run already observed `belief_shape_ok=true`,
  `beliefs_finite=true` with this same adapter.
- No other default-fixture failure mode identified. The bound adapter's dict
  return is handled by the probe's dict branch; the only non-contract exit
  would be a decoder exception, which would surface as CLI exit 3 and is not
  plausible for this hand-checkable 2x2 fixture.
- Contract unchanged: no decoder, threshold, command, CLI, or success-contract
  semantics were modified; only the fixture inputs and its docstring.

## 3. Findings (non-blocking)

- **NB-1 (execution-flag wording).** The single executable gate for the X1
  rerun remains `x1_consistency_probe_authorized`; the scheduled
  `x1_rerun_authorization: GRANTED_MAIN_THREAD_2026-09-13_PENDING_FIX_REVIEW`
  is a documentary note, not an additional flag. The rerun must not be read as
  a new authorization for X2–X4, which stay unused/false.
- **NB-2 (untracked test file overwritten in place).**
  `comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py` is untracked
  (`??` in `git status`), so the fix's edit has no committed baseline diff;
  the current in-place content is the artifact of record. Non-blocking for the
  rerun; relevant only to later audit/diffability.
- **NB-3 (one test file modified).** Exactly one test file was touched by the
  fix: the two new pure-math fixture tests plus the single state-marker test
  rename/update in `test_v72p2d7_r1_x1x4_entrypoints.py`. The other focused
  test files (`test_v72p2d7_r1_consistency_multigraph.py`,
  `test_v72p2d5_gf32_rate_mother.py`) are unmodified.
- **NB-4 (reusable fixture-satisfiability lesson).** The R1 failure was
  fixture-induced, not decoder-induced: any decoder contract with an
  iteration-0 consistency early return requires the default fixture's syndrome
  to be nonzero and consistent with the truth. Carry this lesson to final
  triage/`docs/troubleshooting.md` handling when the cycle closes.

## 4. Test replay (operator re-run at review persistence time)

- Focused replay (three files, fresh additive basetemp
  `workspace/v72p2d7_x1x4_replay_1789275497_434429`, `-p no:cacheprovider`):
  **258 passed, exit 0** (21.95 s).
- Targeted replay (the two fixture tests +
  `test_cycle_state_marker_and_all_flags_false`): **3 passed, exit 0**
  (2.39 s).
- `py_compile` on the changed source module, both X1–X4 test files, and
  `scripts/v72p2d7_consistency_multigraph.py`: `PY_COMPILE_OK`.
- Zero production decoder calls during fix and replay: the fixture tests are
  pure math, and every CLI test monkeypatches
  `probe_historical_decoder_provenance` with fakes.
- Note: this replay was executed before the cycle-state advancement that opens
  the rerun gate; after `next_gate` moves to `X1_RERUN_EXECUTION` the
  state-marker test still asserts the pre-rerun markers and will require a
  scoped update at the next state-changing boundary (flagged to the main
  thread).

## 5. Boundary confirmations

- Zero production decoder calls during the fix (fake-injected tests only).
- No commit, no staging, no push; branch `formal-ir-v72p1-addendum-clean` and
  HEAD `278fdf0742255de0d030649965b6feffb11bc23d` unchanged.
- X2/X3/X4 frozen execution roots still absent:
  `workspace/d7_r1_multigraph_20260913_r1`,
  `workspace/d7_r1_reference_ladder_20260913_r1`,
  `workspace/v72p2d5_g2/20260906_r1`.
- All authorization flags false at review time.

## 6. Disposition

Fix accepted for the authorized single X1 rerun. Next gate:
`X1_RERUN_EXECUTION`, executed exactly once under the main-thread
authorization of 2026-09-13, with the flag set true only immediately before
the process start and restored false immediately after. This review does not
authorize X2–X4, D7-H, G1 rerun, real data, n=1024, tuning, or promotion.
