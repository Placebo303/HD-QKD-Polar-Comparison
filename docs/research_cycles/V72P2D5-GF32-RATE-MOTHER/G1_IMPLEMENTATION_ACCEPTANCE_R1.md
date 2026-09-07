# G1 Implementation Acceptance R1 — implementation only, no authorization

- Status: `G1_IMPLEMENTATION_ACCEPTED_R1 / EXECUTE_NOT_AUTHORIZED`.
- Accepted implementation: `cf61ee63` (`cf61ee63f5b76b0223838717b1344e0e7c3867ee`), including predecessor `614aab9e` (G1 readiness implementation) and specification/review commit `d47e7da1` (review + OpenSpec).
- Review chain (all PASS, implementation readiness only):
  - packet review PASS;
  - readiness code review PASS (`G1_READINESS_CODE_REVIEW_R1.md` says `G1_READINESS_CODE_REVIEW_PASS`);
  - scope addendum PASS (`G1_READINESS_CODE_REVIEW_SCOPE_ADDENDUM_A1.md` says `G1_CODE_REVIEW_SCOPE_ADDENDUM_PASS`, exact frozen three pytest files, `219 passed`);
  - live Windows `_rss_bytes()` returns a positive integer without decoder execution.
- Accepted functionality (implementation readiness only):
  - fresh G1 formal root `workspace/v72p2d5_g1/20260907_r2`;
  - Windows RSS ABI (three signatures set before invocation, `PMC_SIZEOF 72`) and 200-sample peak semantics (one sample per completed APP block after paired oracle; per-f peak = max available; run peak = None if any required sample None);
  - aggregate exact/syndrome/iteration/RSS fields (per-f and run scalars incl. `app_iterations_max`, `decoder_calls 440`);
  - prospective signal rule (frozen in Pre-EXECUTE packet §4.6);
  - outcome precedence (seven labels, frozen in Pre-EXECUTE packet §4.5);
  - fail-loud writers (missing `app_failure_fraction` raises, both G1+G2);
  - no-subdirectory guard (top-level name/size/mtime snapshot, any direct child dir fails);
  - test-only reachability/isolation (authorized synthetic tests use fake decoder, injected arrays, tmp output only; no test binds production decoder or formal root).
- Accepted scope is implementation readiness only. No decoder/G1 result, no FER, no leakage, no key rate, no qualification, no G2 claim of any kind.
- Real external-file Model-F sentinel remains mandatory in Pre-EXECUTE (true script-launch reachability probe from a Python file outside the repo; first-call sentinel fires exactly once before any real decoder call).
- Watchdog semantics remain mandatory in Pre-EXECUTE (binary existence plus harmless 3-second rehearsal returning 124; `-k`/timeout semantics verified there, not here).
- Implementation acceptance grants no authorization. All nine authorizations remain false; promotion remains false. G1 remains unauthorized and unexecuted.

## Disclosed boundaries (verbatim)

1. Process wall can exceed stored entrypoint wall; operator outer wall controls the 900 s final classification during Pre-RESULT review.
2. `app_iterations_max<=180` is asserted/recomputed, not clamped by production.
3. Python exception, watchdog timeout, and pre-exec refusal remain operator-side labels and do not manufacture a normal four-file result.
4. G1 remains synthetic trend evidence, never real FER or qualification.

## Lifecycle effect

- `next_gate` moves `G1_PACKET_REVIEW` → `INDEPENDENT_G1_PRE_EXECUTE_REVIEW`.
- Next step is the independent Pre-EXECUTE review of the frozen packet; that reviewer may not flip authorization or run G1.
