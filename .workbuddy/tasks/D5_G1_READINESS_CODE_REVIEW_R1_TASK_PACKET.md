# D5-G1-READINESS-CODE-REVIEW-R1 — independent review of G1 readiness

## 0. Scope and verdict

Independently review the complete candidate, not only the ABI repair:

- specification/review commit `d47e7da1`;
- implementation commit `614aab9e`;
- Windows ABI repair `cf61ee63`.

Create one verdict:

- `G1_READINESS_CODE_REVIEW_PASS` — implementation matches every reviewed
  requirement and may proceed to a separate Pre-EXECUTE packet/review; or
- `G1_READINESS_CODE_REVIEW_FAIL` — name blocking findings and the smallest
  required repair.

This is read-only review. It is not implementation acceptance, execution
authorization, G1 result acceptance, or G2 permission.

## 1. Hard prohibitions

- No production decoder and no CLI `--phase` invocation, even a refusal probe.
- No Model-F prepare/verify.
- No CAL/VAL/parquet/raw-row read.
- No write/delete/move/rename/copy/hash/normalization under formal evidence
  roots. A fresh task-specific pytest basetemp under `workspace/` is allowed
  and must be removed after resolving and verifying its exact path.
- No edit to `.py`, existing `.md`, OpenSpec, cycle state, decision log, or
  memory.
- No git add/commit/push/reset/stash/checkout/clean/rebase/revert/amend/
  renormalize.
- Findings are reported, never repaired.
- Only one new file:
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_READINESS_CODE_REVIEW_R1.md`.

## 2. Baseline and provenance

Verify independently:

1. `d47e7da1` contains exactly the accepted review and four OpenSpec files.
2. `614aab9e` contains exactly core + two test files.
3. `cf61ee63` contains exactly core + rate-mother test + readiness tasks.
4. No production file outside the D5 core changed in the candidate.
5. Current lifecycle: P0 cost accepted only, `next_gate: G1_PACKET_REVIEW`,
   all nine authorizations false, promotion false.
6. Retained `20260906_r1` G1 root remains unchanged by name/size/mtime;
   proposed `20260907_r2` and G2 roots are absent.

Capture pre/post stat snapshots of all D5 formal roots. Compare exact
name/size/mtime; do not hash workspace evidence.

## 3. Requirements traceability

Build a table mapping every item D1–D6 and A01–A13 from
`G1_PACKET_REVIEW_R1.md` to concrete code, tests, and OpenSpec. Mark each
`PASS`, `FAIL`, or `NOT_VERIFIABLE`.

Any unresolved A01–A10 or A13 is blocking. A11/A12 must be verified directly
in this review. Do not accept the implementer's mapping without reading the
actual diff and current source.

## 4. Correctness audit

### C1 — root and no-overwrite

- Current `G1_FORMAL_ROOT` is exactly `workspace/v72p2d5_g1/20260907_r2`.
- Old `20260906_r1` is not a production target anywhere in the current G1
  path, but remains documented as VOID.
- The writer refuses an existing target before writing any file.
- Tests never use the default G1 root on an authorized path.

### C2 — real Windows RSS ABI

Inspect the live implementation, not only mocks:

- Unix `resource` path remains intact.
- Windows structure layout is correct for 64-bit Python: two DWORD fields and
  eight pointer-sized fields; `sizeof(PROCESS_MEMORY_COUNTERS)==72` on this
  host.
- `GetCurrentProcess.restype`, `GetProcessMemoryInfo.argtypes`, and
  `GetProcessMemoryInfo.restype` are set before invocation.
- The returned value is current-process `WorkingSetSize` bytes, not peak or
  process-tree RSS.
- false/unavailable/exception returns `None`, never zero/fabricated data.

Run a direct, unpatched live `_rss_bytes()` call. Require `type(value) is int`
and `value>0`. Report the literal value. If it returns `None`, verdict is FAIL.

Review the fake API tests and state whether they would fail if any one of the
three signatures were removed. A fake that merely accepts assignments is not
sufficient unless invocation asserts them.

### C3 — sampling and peak semantics

- Exactly one RSS sample follows every completed APP block, after the paired
  oracle call when applicable: 200 samples on frozen G1.
- Per-`f` peak is max of available samples.
- Run peak is max across all samples/per-`f` peaks only when every required
  sample is known.
- Any `None` sample makes run RSS unknown and prevents pass.
- `>=2 GiB` blocks pass; `<2 GiB` may pass.
- A thrown decoder exception aborts fail-loud and cannot produce a false peak
  or normal evidence bundle.

### C4 — aggregate observability

For each `f`, verify attempted, APP exact/rate/failure, APP syndrome,
APP iteration total/max, oracle exact/syndrome/iterations, nonfinite, and peak
RSS are computed from the correct record fields and persisted in JSON/CSV.

Check arithmetic and bounds for the frozen path:

- attempted 100 each;
- oracle subset 20 each;
- total calls 440;
- APP iteration max <=180;
- failure fraction identity;
- counts never exceed their denominators;
- no raw symbols, beliefs, priors, or per-block samples are persisted.

State clearly whether these are guaranteed by implementation, tests, or only
recomputed during later review. Do not overclaim runtime validation if the code
does not explicitly validate an identity.

### C5 — signal and outcome

Independently truth-table at least:

- `0,0` → `G1_COMPLETED_NO_SIGNAL_FAIL`;
- `10,20` → `G1_TREND_PASS`;
- `100,100` → `G1_TREND_PASS`;
- `50,50` → `G1_COMPLETED_NO_SIGNAL_FAIL`;
- decreasing positive rates → no-signal fail;
- nonfinite overrides wall/RSS/signal;
- wall `>900` overrides RSS/signal;
- RSS unknown/`>=2 GiB` overrides signal;
- wall exactly 900 and RSS just below 2 GiB remain eligible.

Verify `passed is true` iff outcome is `G1_TREND_PASS`, both in
`run_g1_phase` and after `run_g1_synthetic` reclassifies with the broader
entrypoint wall.

Confirm the timer begins after authorization check but before Model-F load and
decoder binding, and stops immediately before evidence writing. State the
remaining distinction from operator process wall; this is disclosed, not a
reason to silently broaden the code.

Confirm Python exceptions remain fail-loud. Operator-only labels
`G1_PRE_EXECUTION_BLOCKED` and `G1_WATCHDOG_TIMEOUT_VOID` must not be fabricated
as normal four-file results.

### C6 — writer behavior

- G1 and G2 writers directly require `app_failure_fraction`; missing key raises.
- G2 grading/schema is otherwise unchanged by the candidate.
- G1 four files contain enough scalar fields to recompute completed-path
  classification.
- no-overwrite behavior remains.

### C7 — lifecycle guard depth

Both test helper copies must fail on any direct child directory while retaining
top-level file name/size/mtime snapshots. Independently exercise the helper in
a scratch path outside formal roots:

- absent→absent passes;
- present flat→unchanged passes;
- present→new nested directory fails;
- absent→created directory fails.

Remove only the review scratch. No recursive hashing is expected.

### C8 — reachability and isolation

- Static/fake reachability tests use injected arrays, fake decoder, tmp output.
- No unit test reads the accepted real Model-F artifact.
- SAFE A/B/C and AST guard remain effective.
- No test-level `authorized=True` synthetic call can bind the production decoder
  or use a formal output root.
- The real external-file probe remains deferred to Pre-EXECUTE; do not perform
  it in this review because it reads the accepted Model-F artifact.

## 5. Test execution

Use a unique basetemp under `workspace/` and `-p no:cacheprovider`.

1. `py_compile` core and both D5 scripts.
2. Run focused G1 readiness/RSS/outcome/writer/guard/isolation tests.
3. Run the complete three-file D5 suite.
4. Require zero failures; the existing unknown `cache_dir` warning is benign.
5. Verify formal-root snapshots unchanged and new G1/G2 roots absent.
6. Remove only the review's basetemp after exact resolved-path validation.

Do not use a green suite as a substitute for C1–C8 source review.

## 6. Review report

Create only `G1_READINESS_CODE_REVIEW_R1.md` with:

1. role, commits, lifecycle, non-authorization statement;
2. D1–D6/A01–A13 traceability table;
3. C1–C8 findings;
4. live RSS value, ABI/layout result, fake-test adequacy;
5. sampling count/peak/None semantics;
6. signal/outcome truth table;
7. schema and writer audit;
8. focused/full test literal lines;
9. pre/post root snapshots;
10. commands run and explicitly not run;
11. blocking and non-blocking findings;
12. final verdict token.

PASS means only `READY_FOR_G1_PRE_EXECUTE_PACKET`. It does not accept the
implementation into scientific use by itself, authorize G1, or permit G2.

## 7. Return

Report verdict, traceability counts, C1–C8 summary, live RSS literal,
truth-table results, focused/full pytest lines, root equality, all findings,
and prohibition true/false list.

End:

`G1 readiness 代码评审不构成执行授权；G1 未执行；新 G1 根与 G2 根仍不存在。`

