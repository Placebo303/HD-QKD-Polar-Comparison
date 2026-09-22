# Spec delta: G1 readiness rework

Change: `v72p2d5-g1-readiness-rework`. Delta against the merged
`v72p2d5-p0-g1-g2-production-path` behavior. All values transcribe
`G1_PACKET_REVIEW_R1.md`; nothing here re-decides them.

## Delta 1 — G1 production root

- SHALL: `G1_FORMAL_ROOT` equals exactly
  `workspace/v72p2d5_g1/20260907_r2`.
- SHALL NOT: use `workspace/v72p2d5_g1/20260906_r1` as a G1 production
  target; touch, reuse, overwrite, compare, or cite that VOID root.

## Delta 2 — RSS

- SHALL keep the Unix `resource`-based `_rss_bytes()` path.
- SHALL add a stdlib-`ctypes` Windows fallback reading the current-process
  working set via `GetCurrentProcess` + `GetProcessMemoryInfo` with the
  correctly sized `PROCESS_MEMORY_COUNTERS`; SHALL return `None` when the
  API is unavailable or returns false.
- SHALL sample once after every completed APP block result (after any paired
  oracle call); SHALL persist per-`f` `peak_rss_bytes` as the max non-`None`
  sample and run-level `peak_rss_bytes` as the max of per-`f` peaks.
- SHALL treat `None` as resource-unknown and `>= 2147483648` bytes as
  resource-over; either SHALL prevent `passed == true`. SHALL NOT report a
  single end-of-run reading as a peak. SHALL NOT claim process-tree RSS.

## Delta 3 — Observability

- SHALL persist per `f`: attempted (= 100), APP exact count/rate/failure
  fraction, `app_syndrome_ok_count`, `app_iterations_total`,
  `app_iterations_max`, `oracle_syndrome_ok_count`,
  `oracle_iterations_total`, `nonfinite_count`, `peak_rss_bytes`.
- SHALL persist run-level: `nonfinite`, `decoder_calls` (= 440 on the frozen
  G1 path), `peak_rss_bytes`, `wall_seconds`, `outcome`.
- SHALL satisfy: `app_failure_fraction == 1 - app_exact_count/attempted`;
  APP counts in `[0, 100]`; oracle counts in `[0, 20]`;
  `app_iterations_max <= 2*MAX_ITER`; iteration totals nonnegative.
- SHALL NOT persist raw symbols, beliefs, priors, or per-block records.

## Delta 4 — Outcome

- SHALL implement the signal rule: zero nonfinite AND rates nondecreasing
  AND top APP exact count > 0 AND (strict improve OR both == attempted).
- SHALL classify normally returned runs in order: nonfinite→
  `G1_NONFINITE_OR_CRASH_BLOCKED`; wall > 900 s→`G1_OVERRUN_900S`; RSS
  unknown/over→`G1_RESOURCE_OVERRUN`; signal holds→`G1_TREND_PASS`;
  otherwise→`G1_COMPLETED_NO_SIGNAL_FAIL`.
- SHALL set `passed` true iff `outcome == "G1_TREND_PASS"`.
- `G1_PRE_EXECUTION_BLOCKED` and `G1_WATCHDOG_TIMEOUT_VOID` are
  operator-side only. Exceptions SHALL be fail-loud (no catch-to-manufacture
  a normal bundle).
- SHALL measure `wall_seconds` from `run_g1_synthetic` entry through
  decoding, immediately before evidence writing; an outer wall over 900 s
  overrides any stored pass at Pre-RESULT review.

## Delta 5 — Writers

- SHALL read `app_failure_fraction` in both G1 and G2 writers as
  `float(item["app_failure_fraction"])` with no fallback or rename.
- G1 outputs SHALL carry the aggregate fields needed to recompute the
  completed-path outcome. G2 grading/schema otherwise unchanged.

## Delta 6 — Test invariant

- SHALL fail loudly in both test-file snapshot helpers when a formal root
  has a direct subdirectory child, while keeping the top-level
  name/size/mtime comparison. No recursive hashing.

## Delta 7 — Sentinel

- The real-launch sentinel probe SHALL remain a Pre-EXECUTE check and SHALL
  NOT run in this change. Unit tests SHALL NOT read the real Model-F root.

## Unchanged

Seeds, row tables, width, `f` values, block counts, oracle subset, decoder
parameters, budgets, G2 grading, Model-F input, P0/G0 behavior.
