# Tasks: Speed Up NBLDPC v5 Qualification Execution

## Phase 1: Contract freeze

- [ ] 1.1 (W0) Freeze wrapper contract: deterministic parallel semantics
  (frozen order re-sort), flush/`partial_state.json` schema
  `nbldpc_v5_exec_partial_v1`, crash finalize, one-resume rule, monitoring-only
  log, allowed/forbidden files (new `formal_ir/nonbinary_v5_exec_wrapper.py`,
  new `cli/run_formal_nonbinary_v5_exec.py`, tests; frozen runtime and all
  route sources forbidden), T0-T3 acceptance matrix, no official v5 output.

## Phase 2: Implementation

- [ ] 2.1 (W1) Implement `formal_ir/nonbinary_v5_exec_wrapper.py`:
  `parallel_run` reusing frozen runtime helpers (plan validation, task list,
  selection, readiness, confirmation, artifacts), multi-process decode pool
  (stdlib `multiprocessing` only, module-level `_decode_one`, plain-data
  tasks, spawn-safe on Windows), frozen-order re-sort, `execution.log`.
- [ ] 2.2 (W2) Implement periodic flush + crash finalize: atomic
  `partial_state.json` every `flush_every` tasks; exception/worker-death path
  writes `invalid_run` package + partial state and re-raises; killed-process
  state = plan-only + partial state.
- [ ] 2.3 (W3) Implement `resume_run`: plan re-validation (provenance
  included), missing-task decode, completed-row trust from partial state in
  frozen order, full finalization, second-resume rejection.
- [ ] 2.4 (W4) Implement `cli/run_formal_nonbinary_v5_exec.py` with
  `plan|execute|resume|verify` actions delegating plan/verify to frozen
  helpers and execute/resume to the wrapper.

## Phase 3: Acceptance before any route use

- [ ] 3.1 (W5-T0) Compile/import; determinism proof — fake-runner parallel
  vs frozen serial byte-identical (rows, events, artifacts) at workers 1 and
  4; tiny crash-finalize shape check.
- [ ] 3.2 (W6-T1) Focused unit/tamper suite: flush boundary
  (`flush_every=1`), resume at 0 / mid-dev / dev-complete / mid-confirmation,
  double-resume rejection, plan mutation rejection, partial-state forgery
  rejection, production-API runner injection rejection.
- [ ] 3.3 (W7-T2) Complete fake qualification + strict fake replay (promoted
  and non-promoted paths) through the wrapper under a fresh writable UUID
  root with pytest cache disabled.
- [ ] 3.4 (W8-T3) Regression: v5a/v5b suites green, v4-with-suspension
  baseline unchanged; independent mechanical review (hash records, frozen
  directory diffs, scoped manifest, no official v5 output).

## Phase 4: Handover to Route C

- [ ] 4.1 (W9) Register completion; hand off to
  `formal-nonbinary-ldpc-v5-multistage-ir` so Route C adds the wrapper to its
  provenance and executes via `parallel_run`.
