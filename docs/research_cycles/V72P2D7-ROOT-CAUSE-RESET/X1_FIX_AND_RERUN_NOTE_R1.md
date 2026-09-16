# X1 fixture fix and rerun note R1

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Status at write time: **`X1_FIX_APPLIED_PENDING_INDEPENDENT_REVIEW`** —
  fix applied and focused tests green; X1 has **not** been rerun and is not
  accepted. No authorization flag is true. No commit, no push, no cleanup.

## 1. Root cause

The X1 probe fixture used a zero syndrome with a uniform prior
(`_probe_fixture`, pre-fix). The historical row-layered decoder early-returns
at iteration 0 whenever `H @ argmax(prior) == syndrome`
(`comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py:835-854`);
`argmax(uniform prior) = 0` with `syndrome = 0` made that condition always
true, returning `iterations=0` + `PRIOR_ONLY`, which the frozen X1 success
contract (`CHECK_UPDATED`, `iterations >= 1`, exit 0) can never accept. The
decoder is correct; the fixture was unsatisfiable by construction. Verified
independently in `X1_FAILURE_VERIFICATION_R1.md`.

## 2. Exact fix (minimal; fixture only)

File:
`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
(function `_probe_fixture` only):

- `syndrome = np.array([1, 2], dtype=np.int64)` (was `np.zeros(2)`).
- `x_true = np.array([0, 1], dtype=np.int64)` (was `[0, 0]`).
- `h = [[1, 1], [1, 2]]` (GF32, poly 37) and the uniform prior unchanged.
- Docstring updated with the nonzero-syndrome rationale.

Deterministic-success argument: `H @ x_true = (1*0+1*1, 1*0+2*1) = (1, 2)`
equals the syndrome, while `H @ argmax(uniform prior) = H @ 0 = (0, 0) !=
(1, 2)`, so the iteration-0 early return cannot fire and at least one check
sweep runs. Per the decoder's exit paths (`v35_algorithm_development.py:856-936`)
both the converged exit (`iterations = it >= 1`) and the non-converged exit
(`iterations = max_iter >= 1`) then return provenance `CHECK_UPDATED`.

Scope statement: no decoder, success-contract, threshold, command, or CLI
change; `h`, prior, and all module constants untouched; no production decoder
call anywhere in the new tests.

## 3. Main-thread authorization (2026-09-13)

Authorized: this fixture fix, an independent implementation review, and
**exactly one** X1 rerun under a new authorization; then automatic
continuation X2 -> X3 -> X4 per the original A1 sequence, each phase gated by
its own independent review. During that rerun the X1 flag may be set true
only immediately before the process start and must be restored false
immediately after. At write time nothing has been rerun or executed; the
cycle state records `x1_rerun_authorization:
GRANTED_MAIN_THREAD_2026-09-13_PENDING_FIX_REVIEW` with all flags false.

## 4. Tests run (fake-injected only; no production decoder)

- `py_compile` on the edited module and test file: `PY_COMPILE_OK`.
- New pure-math fixture tests added in
  `comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py`:
  `test_x1_probe_fixture_syndrome_is_nonzero_and_consistent` (syndrome is
  `[1, 2]`, equals `syndrome_of_gf32(h, x_true)` and `_gf32_syndrome(h,
  x_true)`) and
  `test_x1_probe_fixture_iteration_zero_early_return_cannot_fire` (uniform
  prior `argmax` is the all-zero word; `syndrome_of_gf32(h, 0) != syndrome`).
- No existing test pinned the old zero-syndrome fixture (repo-wide grep:
  `_probe_fixture` appeared only in the source module). One unrelated
  existing test was updated because the mandated `cycle_state.yaml`
  correction moved the lifecycle marker:
  `test_cycle_state_ready_marker_and_all_flags_false` ->
  `test_cycle_state_marker_and_all_flags_false`, now asserting the mandated
  values (`state`/`terminal` =
  `X1_PROVENANCE_PROBE_FAILED_FIX_PENDING_REVIEW`, `next_gate` =
  `X1_FIX_INDEPENDENT_REVIEW`); the all-flags-false and
  `RETAINED_BYTE_IDENTICAL` assertions are unchanged.
- Focused run (fresh additive `workspace/v72p2d7_x1x4_test_<uuid>` basetemp,
  `-p no:cacheprovider`), three files
  (`test_v72p2d7_r1_x1x4_entrypoints.py`,
  `test_v72p2d7_r1_consistency_multigraph.py`,
  `test_v72p2d5_gf32_rate_mother.py`): first run 257 passed / 1 failed
  (the stale state-marker test above, pre-existing before the fixture fix);
  after the scoped test update 258 passed, exit 0. Exact commands and
  basetemps in the operator return.
