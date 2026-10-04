---
slug: "speed-up-nbldpc-v5-runtime-wrapper"
createdAt: "2026-08-01T00:00:00.000Z"
---

# Proposal: Speed Up NBLDPC v5 Qualification Execution (Parallel + Flush + Log Wrapper)

## Why

Routes A and B of `formal-nonbinary-ldpc-v5-multistage-ir` each took about
45-55 minutes of single-core wall time (512 outcomes, workers:1, results
written only atomically at the end).  Two concrete costs:

1. **Latency**: a 20-core machine runs one core.  Route C (and D) still need
   execution, and each further route repeats the ~50 minute cost.
2. **Crash fragility**: an interrupted execution currently loses every outcome
   (the directory stays plan-only; only the exception path writes an invalid
   package).  There is no partial evidence and no way to continue a long run
   after a machine/session interruption.

This change adds a **wrapper** around the frozen v5 runtime that (a) executes
the per-frame decodes in parallel with byte-identical deterministic results,
(b) periodically flushes partial outcome state so an interruption retains
auditable evidence and can be resumed once, and (c) writes a progress log.
The frozen `nonbinary_v5_runtime.py` and all v5a/v5b sources stay untouched,
so existing evidence chains keep their provenance.

## Scope

- New `formal_ir/nonbinary_v5_exec_wrapper.py`:
  - `parallel_run(config, output, *, workers, flush_every, log_path, _test_only, runner, fatal_hook)` —
    executes the same plan/execute lifecycle as the frozen runtime but with a
    deterministic multi-process decode stage; results are collected and
    written in the exact frozen frame order so the package is byte-identical
    to the serial path.
  - Periodic flush of completed rows/events into a sidecar partial-state file;
    on crash (exception, kill, machine loss) the directory is finalized as an
    `invalid_run` package plus a `partial_state.json` recording exactly which
    frames completed.
  - `resume_run(config, output, *, workers, flush_every, log_path, _test_only, runner, fatal_hook)` —
    at most one resume per package: re-validates the plan and partial state,
    decodes only the missing frames, and completes the normal eight-artifact
    package.
  - Progress log: wall time, per-policy/per-stratum counters, worker health.
- New CLI `cli/run_formal_nonbinary_v5_exec.py` with `plan`/`execute`/`resume`/
  `verify` actions bound to a route lane module.
- Route C in `formal-nonbinary-ldpc-v5-multistage-ir` will add the wrapper to
  its `source_files` provenance and use `parallel_run` for its execution.

## Out of Scope

- Modifying `nonbinary_v5_runtime.py`, v5a/v5b sources, v1-v4 sources, plans,
  packages, or artifacts.
- Changing any v5 scientific semantics: gates, readiness, promotion, leakage
  accounting, transcript format, artifact set, caps, or the "interrupted
  execution stays incomplete/invalid" rule (the wrapper preserves it and adds
  an explicit one-time resume path that keeps the plan immutable).
- External dependencies: `multiprocessing` from the standard library only.
- Re-running v5a/v5b packages; touching their evidence.
- Route C/D implementation itself (owned by the v5 change).

## Affected Specs

- Add `speed-up-nbldpc-v5-runtime-wrapper`.
