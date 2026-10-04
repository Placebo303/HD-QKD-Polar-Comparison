# Design: Speed Up NBLDPC v5 Qualification Execution (Parallel + Flush + Log Wrapper)

## 1. Contract

The frozen v5 runtime (`nonbinary_v5_runtime.py`) owns plan schema, frame
generation, identity-freshness, selection, confirmation materialization,
artifact layout, and strict replay.  This wrapper reuses those functions
without modifying them.

Public API (all in `formal_ir/nonbinary_v5_exec_wrapper.py`):

- `parallel_run(config, output=None, *, workers=None, flush_every=64,
  log_path=None, runner=None, _test_only=False, fatal_hook=None)` ->
  dict (same shape as `runtime.run`)
- `resume_run(config, output=None, *, workers=None, flush_every=64,
  log_path=None, runner=None, _test_only=False, fatal_hook=None)` -> dict
- `finalize_invalid(config, out, exc, state)` -> same semantics as
  `runtime._finalize_invalid`, plus `partial_state.json`.

`config` is a `runtime.RouteConfig`; the wrapper works for every v5 route
(v5a/v5b/v5c/v5d) because it only calls frozen runtime helpers.

## 2. Deterministic parallel execution

Frame decoding is embarrassingly parallel: every `(policy, frame)` outcome
depends only on `(config, frame, policy, seeds, codebook)` and the runner.
There is no shared mutable state and no global RNG (each frame uses its own
PCG64 seed records from the plan).

Execution order for dev (and confirmation) is defined by the frozen
`_expected_development` order: policy-major, frame-major.  The wrapper:

1. Rebuilds the ordered task list exactly as `runtime.run` does.
2. Decodes tasks in parallel with a `multiprocessing.Pool` (chunksize 1,
   worker count `workers` defaulting to `os.cpu_count()`), each worker
   importing the route core module (spawn-safe: pickles only
   `(frame, policy, seeds)` + a runner name, never decoder state).
3. Collects results and re-sorts into the frozen order.
4. Then runs selection/readiness/confirmation materialization/execution
   through the same frozen helpers.

**Determinism proof (T0)**: on the same plan and the same runner, the wrapper
with `workers=1` and with `workers=N` produces byte-identical rows, events,
and artifacts as the frozen serial `runtime.run` (verified with fake runners
in tests; production runs additionally self-check the ordered result list
against the expected frame sequence before any write).

Spillover guarantee: the decoder `_run` loop is pure NumPy/Python over local
state; a worker that crashes (OS error, hardware) raises inside `Pool.map`
which the wrapper converts into a crash finalize (section 3) — it never
produces a partial package silently.

## 3. Periodic flush, crash finalize, one resume

**Flush**: after every `flush_every` completed tasks the worker parent writes
`partial_state.json` (atomic: write temp + rename) with:

- `schema`: `nbldpc_v5_exec_partial_v1`
- `plan_sha256`: hash of the plan file bytes
- `completed`: ordered list of `{policy_sha256, frame_id}` keys done so far
- `rows`: the completed outcome rows (CSV-ordered)
- `events`: the completed transcript events (canonical byte stream)

The flush is evidence that stays consistent with the frozen artifact
semantics: rows/events already produced are exactly the prefix of the final
package under the frozen order (parallel collection re-sorted).

**Crash finalize**: on exception or on detected worker death, the wrapper
writes the invalid package exactly as `runtime._finalize_invalid` would
(`formal_run_manifest.json` with `run_status=invalid_run`, partial
`formal_frame_outcomes.csv`/`formal_transcript.jsonl` if any rows exist,
plus `partial_state.json`), then re-raises.  A killed process (no Python
exception) leaves the directory with only `pre_run_plan.json` plus a
`partial_state.json` written by the flush; `verify` keeps treating that
directory as plan-only-and-invalid (the frozen verify already accepts
`plan_only`; the wrapper documents that a resume is required).

**Resume (at most once)**: `resume_run` validates that the directory is
either plan-only (with or without `partial_state.json`) and that the plan
still passes `runtime._validate_plan` (this re-checks provenance, so resume
is blocked by the same HEAD-drift rule — intentional).  It re-decodes only
the missing tasks (the completed ones are trusted from `partial_state` and
re-inserted in order), then proceeds with selection/confirmation/
finalization exactly like a fresh run.  After a resume completes, the
directory contains the normal eight artifacts; a second resume is rejected
(`partial_state.json` no longer present and directory is not plan-only).

The frozen "interrupted execution SHALL remain incomplete/invalid" rule is
preserved: the interrupted attempt is an `invalid_run` package, and the
resume is a distinct, pre-registered, at-most-once continuation that never
touches the plan.

## 4. Progress log

`log_path` (default `<parent_of_run_dir>/<run_id>.execution.log` when None; the
log MUST live outside the package directory so the eight-artifact set stays
exact) records, one line per event: wall timestamp, event type (`start`,
`flush`, `worker_error`, `selection`, `readiness`, `confirmation`, `done`,
`crash`), counters (completed/total, per stratum verified counts), and worker
health.  The log is excluded from the eight artifacts and from provenance
(monitoring only, exactly like wall time).

## 5. CLI

`cli/run_formal_nonbinary_v5_exec.py`:

```
python -m comparison_bench.src.comparison_bench.cli.run_formal_nonbinary_v5_exec \
  <lane-module-path> plan|execute|resume|verify [--workers N] [--flush-every N] [--log PATH]
```

The lane module path selects the route (e.g.
`comparison_bench.src.comparison_bench.formal_ir.nonbinary_v5b_ir_qualification`).
`plan` and `verify` delegate to the frozen runtime; `execute`/`resume` use the
wrapper.

## 6. Acceptance (T0-T3)

- T0: import/compile; determinism proof — fake-runner parallel vs frozen
  serial byte-identical (rows, events, artifacts) at workers 1 and 4; tiny
  crash-finalize shape check.
- T1: focused unit/tamper — flush boundary correctness (flush_every=1),
  resume at several interruption points (0, mid-dev, dev-complete,
  mid-confirmation), double-resume rejection, plan mutation rejection,
  partial-state forgery rejection, production API rejects injected runner.
- T2: complete fake qualification + strict fake replay through the wrapper
  (promoted and non-promoted paths) on a fresh writable UUID root with
  `-p no:cacheprovider`.
- T3: regression (v5a/v5b suites stay green, v4-with-suspension baseline),
  independent mechanical review, scoped manifest, no official v5 output
  created by the wrapper change.

## 7. Risks and mitigations

- **Multiprocessing on Windows**: spawn start method requires picklable task
  args and a module-level worker entry; the wrapper ships a module-level
  `_decode_one(args)` and passes only plain data (frame dicts, seed records,
  policy specs).  `RouteConfig.core` is not pickled; workers receive
  `core_module_name` and import it.
- **Worker death mid-run**: `Pool.map` raises; wrapper crash-finalizes with
  the last flush state and re-raises; resume is then possible once.
- **Determinism drift**: any parallel result that reorders rows breaks the
  T0 determinism test; the re-sort is enforced before selection is computed.
- **HEAD-drift replay rule**: unchanged; resume validates plan provenance and
  is blocked by the same rule, by design.
