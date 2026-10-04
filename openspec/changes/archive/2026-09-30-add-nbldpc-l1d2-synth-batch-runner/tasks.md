# Tasks — NB-LDPC L1-degree2 Stage-2 synthetic batch runner

Branch `formal-ir-v72p1-addendum-clean`. Track DECIDE. This change approval is
NOT execution authorization (DEC-1 still required). No commit/push by the
operator. Existing files are read-only; this change adds only the five
documents in its manifest.

Evidence already landed (implementation-only, cited here, not modified):

- T1 runner done: `comparison_bench/src/comparison_bench/cli/
  nbldpc_l1d2_synth_batch.py` (evidence: `test_nbldpc_l1d2_synth_batch.py`
  18 passed).
- T2 seed rename done: `comparison_bench/src/comparison_bench/formal_ir/
  nbldpc_l1_degree2_layout.py` (seed 37xx + `_PRIOR` full set + L2 map,
  evidence: `test_nbldpc_l1_degree2_seeds.py` 4 passed +
  `test_nbldpc_l1_degree2_layout.py` 7 passed).
- T3 canary sort fix done (evidence: `test_nbldpc_l1_degree2_driver.py`
  4 passed; `--canary` help reads "minimum graph seed
  x minimum data seed") → four files 33 passed total.

- [x] T1: Stage-2 runner implemented (evidence: 18 passed in
  `test_nbldpc_l1d2_synth_batch.py`; dual-arm
  `oracle=False` hardcoded; no production decoder binding in the module).
- [x] T2: seeds renamed to 37xx + `_PRIOR` full set + L2 map in the layout
  module (evidence: 4 passed in `test_nbldpc_l1_degree2_seeds.py` + 7 passed
  in `test_nbldpc_l1_degree2_layout.py`).
- [x] T3: canary sort-then-first fix (evidence: 4 passed in
  `test_nbldpc_l1_degree2_driver.py`) + help text aligned
  to "minimum graph seed x minimum data seed" (order-independent).
- [x] T4: freeze the DECIDE packet `PREREG_AND_AUTH.md` (science-input freeze
  table, exact commands with `<UUID>` placeholder, single out-root + absence
  precheck, schema, dual-row scale arithmetic, budget + canary, machine-gate
  decision procedures, no-overwrite + forbidden zones, claim ceiling,
  P4/DEC-1 authorization statement template with date/signature blank,
  S1-S8 sign-off list).
- [x] T5: Pre-EXECUTE review (intended branch; scoped code/config/test/packet
  cleanliness; frozen contract; explicit user authorization DEC-1 with
  date/signature; target-output absence; focused tests). FAIL blocks
  execution.
- [x] T6: single execution of the frozen exact commands (n128, then n256
  only if COND-3 permits); no retry/resume/sample-reduction/seed-change;
  over-cap STOP with results retained.
- [x] T7: write `RESULT.md` (raw counts, paired direction, per-graph deltas,
  cost; `accepted_wrong` isolated; disclosure on attempted).
- [x] T8: independent Pre-RESULT review (plan thresholds, leakage-formula
  decomposition, `undetected` isolation, per-source breakdown, disclosure
  accounting, plan semantics vs actual artifacts). FAIL blocks
  solidification.
- [x] T9: write `INDEPENDENT_ACCEPTANCE.md` (independent thread/reviewer).
- [x] T10: main-thread acceptance and archiving decision (completed
  2026-09-30; disposition: completed — delta merged into
  `openspec/specs/synth-batch-runner/spec.md`, change archived at
  `openspec/changes/archive/2026-09-30-add-nbldpc-l1d2-synth-batch-runner/`).

Stop rules: any Pre-EXECUTE/Pre-RESULT FAIL → stop; unauthorized input/call,
old-output conflict, material science-parameter change, truth entering the
operational path, attribution-match failure, disclosure leakage, or budget
exhaustion → stop with products retained; never publish-then-patch.
