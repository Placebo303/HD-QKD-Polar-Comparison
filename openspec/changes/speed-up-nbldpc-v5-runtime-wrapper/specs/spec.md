# Spec: speed-up-nbldpc-v5-runtime-wrapper

## Requirements

### R1: Frozen runtime stays frozen

The wrapper SHALL live in new files under `formal_ir/` and `cli/`.  It SHALL
NOT modify `nonbinary_v5_runtime.py`, any v5a/v5b route source, v1-v4
sources, existing plans, packages, or artifacts.  The wrapper SHALL reuse the
frozen runtime's plan schema, frame generation, identity-freshness,
selection, readiness, confirmation materialization, eight-artifact layout,
invalid-run retention, and strict replay logic without changing their
behavior or outputs.

### R2: Deterministic parallel execution

`parallel_run` SHALL execute the identical task set the frozen serial path
would execute (same plans, frames, seeds, policies, codebooks) with a
standard-library multi-process pool (worker count configurable, default
`os.cpu_count()`).  Decode tasks SHALL be embarrassingly parallel: each
`(policy, frame)` outcome depends only on its plan-bound inputs; workers
SHALL receive only plain picklable data and import the route core module by
name.  Collected results SHALL be re-sorted into the exact frozen order
(policy-major, frame-major) before selection, readiness, and confirmation are
computed.  For an identical plan and runner, the wrapper SHALL produce
byte-identical rows, events, and artifacts as the frozen serial `run`,
verified at `workers=1` and `workers=N`.

### R3: Periodic flush and crash finalize

After every `flush_every` completed tasks (default 64, atomic write via
temp+rename), the wrapper SHALL write `partial_state.json` (schema
`nbldpc_v5_exec_partial_v1`) containing: plan SHA256, completed task keys
`{policy_sha256, frame_id}` in frozen order, the completed outcome rows, and
the completed transcript events.  On exception or worker death, the wrapper
SHALL finalize an `invalid_run` package exactly as the frozen runtime's
invalid path would (manifest, any partial CSV/transcript, plus
`partial_state.json`) and re-raise.  A killed process SHALL leave the
directory plan-only (or plan-plus-partial-state); the frozen "interrupted
execution SHALL remain incomplete/invalid" rule is preserved in all cases.

### R4: One resume at most

`resume_run` SHALL accept a directory that is plan-only (with or without
`partial_state.json`) and SHALL re-validate the plan (provenance included)
before touching anything.  It SHALL re-decode only the missing tasks, insert
the trusted completed rows from `partial_state` in frozen order, and complete
selection/confirmation/finalization exactly like a fresh run.  After a
successful resume the directory SHALL contain the normal eight artifacts; a
second resume SHALL be rejected.  Resume SHALL be blocked by the same plan
provenance/HEAD-drift rule as the frozen replay — by design.

### R5: Progress log

The wrapper SHALL write a monitoring-only progress log (default
`<parent_of_run_dir>/<run_id>.execution.log`, always outside the package
directory) with wall timestamps and event lines (start, flush, worker error,
selection, readiness, confirmation, done, crash) plus counters.  The log
SHALL NOT be part of the eight artifacts, SHALL NOT enter provenance, SHALL
NOT live inside the package directory, and SHALL NOT contain rows, decisions,
or forbidden diagnostics.

### R6: Wrapper acceptance

T0 SHALL prove compile/import and the determinism contract (parallel vs
frozen serial byte-identical with fake runners at workers 1 and 4).  T1 SHALL
cover flush boundaries (`flush_every=1`), resume from several interruption
points, double-resume rejection, plan mutation rejection, partial-state
forgery rejection, and production-API runner injection rejection.  T2 SHALL
run complete fake qualifications and strict fake replays (promoted and
non-promoted paths) under a fresh writable UUID root with the pytest cache
disabled.  T3 SHALL show v5a/v5b suites green, the v4-with-suspension
baseline unchanged, a scoped manifest, and zero official v5 output created
by this change.

## Behavior

The qualification lifecycle is unchanged: plan once (frozen helpers), execute
once (wrapper), verify strictly once (frozen helpers).  `execute` may
alternatively be a resume when a previous attempt was interrupted and left
the package invalid or plan-only.  All scientific semantics (gates,
readiness, promotion, leakage, transcript, artifact set, caps) are exactly
those of the frozen v5 contract.

## Acceptance Criteria

- A1: No frozen v5/v1-v4 source file is modified; the wrapper adds new files
  only.
- A2: Parallel execution is byte-identical to the frozen serial path on the
  same plan and runner (T0).
- A3: Interruption leaves an `invalid_run` package (or plan-only state) with
  a valid `partial_state.json`; resume completes the package once and a
  second resume is rejected (T1).
- A4: Plan mutation and partial-state forgery are rejected; production
  runner injection is rejected (T1).
- A5: T2 fake qualification and strict fake replay pass; T3 regression shows
  v5a/v5b suites green and no official v5 output (T2/T3).
