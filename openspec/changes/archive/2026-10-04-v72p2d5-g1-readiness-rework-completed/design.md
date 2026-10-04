# Design: G1 readiness rework

Status: `IMPLEMENTATION_CANDIDATE_ONLY`. No execution, no authorization, no
CAL/VAL/raw read, no formal output. All wording below transcribes
`G1_PACKET_REVIEW_R1.md` D1–D6 and OQ decisions; this change invents no
threshold, root, label, or formula.

## 1. Fresh root (D1)

- `G1_FORMAL_ROOT = "workspace/v72p2d5_g1/20260907_r2"`, exactly.
- Old root `workspace/v72p2d5_g1/20260906_r1` stays `VOID_RETAINED_IN_PLACE`:
  untouched, never reused, overwritten, compared, or cited. Tests owning the
  G1 production literal are updated; no other root changes.

## 2. RSS measurement and sampling (D2, OQ-G1-RSS)

- Keep the existing Unix `resource` path unchanged.
- Windows fallback uses stdlib `ctypes` only: `GetCurrentProcess` plus
  `GetProcessMemoryInfo` reading the current Python process working set in
  bytes, with the correctly sized `PROCESS_MEMORY_COUNTERS` structure.
  Return `None` when the API is unavailable or returns false. No `psutil`;
  no process-tree claim (the historical decoder runs in-process).
- Sampling: call `_rss_bytes()` once after every completed APP block result
  (after any paired oracle call for that block) of the G1 scan — 200 APP
  block results across both `f` values, covering the interleaved oracle
  decodes.
- Persist `peak_rss_bytes` per `f` as the max of the non-`None` samples for
  that `f`; persist run-level `peak_rss_bytes` as the max of the per-`f`
  peaks. The persisted peak is a sampled maximum (a lower bound on the true
  peak). Never report a single end-of-run reading as a peak.
- Gate: `<2 GiB` reference is `2147483648` bytes. If run-level RSS is `None`
  (unknown) or `>= 2 GiB`, no PASS may be claimed (`G1_RESOURCE_OVERRUN`).

## 3. Aggregate observability (D3)

- Per `f`, persist exactly the existing fields plus:
  `app_syndrome_ok_count`, `app_iterations_total`, `app_iterations_max`,
  `oracle_syndrome_ok_count`, `oracle_iterations_total`, `nonfinite_count`,
  `peak_rss_bytes`.
- Retain run-level `nonfinite` and `decoder_calls`; add run-level
  `peak_rss_bytes`, `wall_seconds`, `outcome`.
- Scalar aggregates only. No raw symbols, beliefs, priors, or per-block
  records.
- Enforced identities/bounds: attempted = 100 per `f`; APP exact and APP
  syndrome counts in `[0, 100]`; oracle exact and syndrome counts in
  `[0, 20]`; `app_failure_fraction == 1 - app_exact_count/attempted`;
  `app_iterations_max <= 2*MAX_ITER` with totals nonnegative; oracle
  iteration total nonnegative; decoder calls = 440 on the frozen G1 path.

## 4. Signal rule and completed-path classification (OQ-G1-SIGNAL, OQ-G1-OUTCOME)

- Prospective signal rule (integer counts govern; denominator 100):

```text
zero nonfinite
AND rates nondecreasing
AND top APP exact count > 0
AND (top APP exact count > low APP exact count
     OR both APP exact counts == attempted)
```

- For a normally returned G1 run, classify in this order (first match wins):
  1. `G1_NONFINITE_OR_CRASH_BLOCKED` when `nonfinite > 0`;
  2. `G1_OVERRUN_900S` when entrypoint wall exceeds 900 s;
  3. `G1_RESOURCE_OVERRUN` when RSS is unknown or `>= 2 GiB`;
  4. `G1_TREND_PASS` when the signal rule holds;
  5. otherwise `G1_COMPLETED_NO_SIGNAL_FAIL`.
- `passed` is true iff `outcome == "G1_TREND_PASS"`.
- `G1_PRE_EXECUTION_BLOCKED` and `G1_WATCHDOG_TIMEOUT_VOID` are
  operator-side labels: those paths do not normally return a four-file
  result. A Python exception is fail-loud: never catch it merely to
  manufacture a normal evidence bundle (the operator may label a crash
  `G1_NONFINITE_OR_CRASH_BLOCKED`). No recovery or partial-output machinery.
- `wall_seconds` is measured from entry into `run_g1_synthetic` through
  completion of model loading, decoder binding, mother construction, and
  decoding, immediately before evidence writing. Evidence-writing time and
  process startup are reported separately by the future operator's outer
  wall; an outer wall over 900 s overrides any stored pass during Pre-RESULT
  review.

## 5. Fail-loud writers (D4)

- In both G1 and G2 writers replace the duplicated nested fallback with
  direct required-key access: `float(item["app_failure_fraction"])`.
- Public field name and definition unchanged; no legacy compatibility.
- G1 JSON/CSV/report/summary carry the new aggregate fields needed to
  recompute the completed-path outcome. G2 receives only the fail-loud
  correction; G2 grading and schema are otherwise unchanged.

## 6. No-subdirectory invariant (D5)

- Add an explicit no-subdirectory invariant to both test-file formal-root
  snapshot helpers (`test_v72p2d5_gf32_rate_mother.py` and
  `test_v72p2d5_model_f_input.py`): any formal root containing a direct
  subdirectory child fails loudly.
- Keep the existing top-level file name/size/mtime snapshot. No recursive
  hashing, no manifest system.

## 7. Reachability contract (D6)

- Static plus fake tests prove the future external-file sentinel contract
  can reach the first injected decoder call with accepted input while tmp
  output remains empty. Unit tests never read the real Model-F root.
- The real-root external-file probe (file outside the repo, cwd at repo
  root, no `python -c`, no `sys.path` insertion, six D6 conditions) is
  deferred to Pre-EXECUTE and is not run here.

## 8. Explicitly not in design

Watchdog execution, prepare/verify replay, CAL/VAL reads, G2 regrading,
seed/row/width/budget changes, new dependencies, monitors, retry/resume,
hashes, manifests, compat layers, generic abstractions.
