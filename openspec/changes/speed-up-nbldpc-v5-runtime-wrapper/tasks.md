# Tasks: Speed Up NBLDPC v5 Qualification Execution

## Phase 1: Contract freeze

- [x] 1.1 (W0) Freeze wrapper contract: deterministic parallel semantics
  (frozen order re-sort), flush/`partial_state.json` schema
  `nbldpc_v5_exec_partial_v1`, crash finalize, one-resume rule, monitoring-only
  log, allowed/forbidden files (new `formal_ir/nonbinary_v5_exec_wrapper.py`,
  new `cli/run_formal_nonbinary_v5_exec.py`, tests; frozen runtime and all
  route sources forbidden), T0-T3 acceptance matrix, no official v5 output.

## Phase 2: Implementation

- [x] 2.1 (W1) Implement `formal_ir/nonbinary_v5_exec_wrapper.py`:
  `parallel_run` reusing frozen runtime helpers (plan validation, task list,
  selection, readiness, confirmation, artifacts), multi-process decode pool
  (stdlib `multiprocessing` only, module-level `_decode_one`, plain-data
  tasks, spawn-safe on Windows), frozen-order re-sort, `execution.log`.
- [x] 2.2 (W2) Implement periodic flush + crash finalize: atomic
  `partial_state.json` every `flush_every` tasks; exception/worker-death path
  writes `invalid_run` package + partial state and re-raises; killed-process
  state = plan-only + partial state.
- [x] 2.3 (W3) Implement `resume_run`: plan re-validation (provenance
  included), missing-task decode, completed-row trust from partial state in
  frozen order, full finalization, second-resume rejection.
- [x] 2.4 (W4) Implement `cli/run_formal_nonbinary_v5_exec.py` with
  `plan|execute|resume|verify` actions delegating plan/verify to frozen
  helpers and execute/resume to the wrapper.

## Phase 3: Acceptance before any route use

- [x] 3.1 (W5-T0) Compile/import; determinism proof — fake-runner parallel
  vs frozen serial byte-identical (rows, events, artifacts) at workers 1 and
  4; tiny crash-finalize shape check.
- [x] 3.2 (W6-T1) Focused unit/tamper suite: flush boundary
  (`flush_every=1`), resume at 0 / mid-dev / dev-complete / mid-confirmation,
  double-resume rejection, plan mutation rejection, partial-state forgery
  rejection, production-API runner injection rejection.
- [x] 3.3 (W7-T2) Complete fake qualification + strict fake replay (promoted
  and non-promoted paths) through the wrapper under a fresh writable UUID
  root with pytest cache disabled.
- [x] 3.4 (W8-T3) Regression: v5a/v5b suites green, v4-with-suspension
  baseline unchanged; independent mechanical review (hash records, frozen
  directory diffs, scoped manifest, no official v5 output).

## Phase 4: Handover to Route C

- [x] 4.1 (W9) Register completion; hand off to
  `formal-nonbinary-ldpc-v5-multistage-ir` so Route C adds the wrapper to its
  provenance and executes via `parallel_run`.

## Verification Notes (2026-08-01)

- Wrapper source closure frozen at commit `34cdc53` (nonbinary_field /
  codebook / qspa / shared / v3 / v4_ir / v5_runtime / v5a / v5b /
  v5_exec_wrapper + CLI + 9 test files + both OpenSpec change dirs).
- W5-T0: `test_t0_parallel_matches_serial_at_workers_1_and_4` 1 passed
  (18.47s); `test_t0_parallel_promoted_matches_serial` 1 passed (17.86s).
- W6-T1: focused group 9 passed (40.73s); `t1_resume_from_every_interruption_point`
  1 passed (64.71s); partial+resume+double-resume group 5 passed (97.42s).
- W7-T2: `t2_fake_qualification_and_strict_replay_promoted` 1 passed
  (13.90s); `t2_fake_qualification_non_promoted_and_invalid_retention`
  1 passed (14.25s) — after fixing a test-local runner that blocked spawn
  workers (partial_runner moved to module level).
- Full wrapper suite: 16 passed in 158.33s.
- W8-T3: v5a/v5b suites 62 passed (328.88s), v4 nbldpc 20 passed (93.25s)
  with official packages temporarily suspended (pre-existing self-conflict,
  unrelated); official package hashes verified unchanged after restore
  (`workspace/t3_official_packages_hash.json`); frozen directories clean
  (`git diff` empty for v5_runtime + route sources); no official v5 output
  created by the wrapper.
- Bugs fixed during acceptance (wrapper only, no frozen files touched):
  1) `_confirm_tasks` confirmation_material was written to a local copy and
     never stored in the package policy_doc — package lacked
     confirmation_material; now written into the passed policy_doc
     (parallel_run + resume_run call sites).
  2) `resume_run` only accepted plan-only dirs; now also accepts
     invalid_run packages (crash finalize) and deletes stale artifacts
     before resuming (normal writes use "x" mode).
  3) resume selection used rows containing confirmation rows; now split at
     `development_total` (dev rows only for `_select`, confirmation residue
     checked by policy_sha + length).
  - partial_state rows now carry `rows_sha256` (rows+events digest);
    resume rejects mismatches.
  - Tests: byte-identical assertion corrected to the deterministic subset
    (codebook/candidate manifests + development rows) since confirmation
    seeds are secrets-random (frozen semantics) — full-package bytes differ
    across runs by design.
- W9 handoff: baseline + wrapper frozen at `34cdc53`; Route C (V5-C1..C5)
  pending in `formal-nonbinary-ldpc-v5-multistage-ir`.
