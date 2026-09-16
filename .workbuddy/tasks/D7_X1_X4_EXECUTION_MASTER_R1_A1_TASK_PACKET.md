# D7 X1–X4 Execution Master R1 — Authorization Addendum A1

## Authority

User authorization received in the main thread on 2026-09-13:

> 我可以授权执行X1-X4，一次性完成都可以

This addendum supplements, and does not replace, `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md`. All frozen commands, inputs, roots, ceilings, claim limits, no-overwrite rules, and STOP conditions remain binding.

## Authorized sequence

The user explicitly authorizes one sequential attempt of X1, X2, X3, and X4 under the master packet. Authorization is phase-specific but granted together here. It permits automatic progression only through the following gates:

1. X1 may start after the already accepted Phase P readiness boundary.
2. X2 may start only if X1 exits 0 and its literal JSON satisfies the frozen success contract.
3. X3 may start only if X2 completes with full coverage and without resource/crash/nonfinite/engineering blocker, and an independent X2 Pre-RESULT review passes. X3 is scientifically warranted as the frozen strong-reference diagnosis of X2 failures. If X2 contains zero eligible failed f=1.2 records, X3 must record `X3_NOT_APPLICABLE_NO_FAILED_CALLS` with zero calls and may proceed to its review.
4. X4 may start only if X3 completes, is not applicable, or returns a reviewed non-blocking diagnostic result, and an independent X3 Pre-RESULT review passes.
5. D7-H, G1 rerun, real data, n=1024, tuning, promotion, and every action outside X1–X4 remain unauthorized.

## Authorization consumption

- Each X phase receives exactly one process-start attempt.
- Set only the imminent phase flag true. Restore it false immediately after that attempt, before review or progression.
- A refusal, exception, timeout, crash, resource stop, partial root, nonzero engineering terminal, or failed review consumes that phase authorization and terminates the entire chain.
- No retry, resume, alternate root, seed replacement, parameter adjustment, cleanup, or later-phase execution is authorized.
- An authorization for a later phase remains unused if an earlier STOP occurs; it must not be exercised outside this chain without a new user decision.

## Required independent reviews

The one-time authorization does not waive the repository's independent gates.

- After X1: independently check command/exit/stdout/stderr/timestamps, exactly one decoder call, zero writes, exact provenance, finite shape-valid beliefs, iterations >=1, flag restored false.
- After X2: independently check 384-slot coverage or valid earlier blocker, per-graph/per-f records, exact/syndrome separation, call count, wall/RSS, no overwrite, and claim ceiling.
- After X3: independently verify selector identity, `ladder_calls + reconstruction_calls <=576`, baseline replay equality, `where` breakdown for every blocker, per-arm records, wall/RSS, and claim ceiling.
- Before X4 execution, close or explicitly adjudicate these carried findings: repo-rooted G2 writer path, non-dict runner rejection, and external 120-second per-call watchdog ownership.
- After X4: independently verify the frozen n=256 matrix, 1320-call ceiling, actual calls/coverage, four-state grading, per-layer counters, wall/RSS, exact/syndrome separation, and absence of automatic continuation.

An execution operator must not perform its own independent acceptance. If an independent reviewer is unavailable, STOP before the next phase and return `BLOCKED_REVIEW_UNAVAILABLE`.

## Execution commands

Use exactly the commands frozen in the master packet:

```powershell
.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --historical-provenance-probe

.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_r1_multigraph_20260913_r1 --wall-budget-s 900

.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --reference-ladder --x2-root workspace/d7_r1_multigraph_20260913_r1 --out-root workspace/d7_r1_reference_ladder_20260913_r1 --wall-budget-s 3600

.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --g2
```

The operator must apply the master packet's outer watchdogs and record process ownership. Do not launch more than one execution phase concurrently.

## Evidence and lifecycle

- Add one authorization record under `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/` quoting the user authorization and this addendum.
- Preserve X1 transcript and each later phase's immutable fresh result root.
- Add one independent review record per completed phase; compact files are acceptable.
- Update `cycle_state.yaml` additively after each attempt and review. Never mark a later phase executed before its process starts.
- Do not solidify or commit a result before its independent Pre-RESULT review passes.
- Coherent scoped commits are allowed after reviewed phase boundaries; no push.

## Terminal return

Return exactly one:

### COMPLETE

All applicable X1–X4 attempts and required reviews completed; all flags restored false. Report exact commands, exits, calls, roots/files, wall/RSS, primary results, review verdicts, changed-file manifest, commits, and the remaining D7-H decision. Do not claim qualification or promotion.

### BLOCKED

Report the first failed gate, raw command/output/error, whether its authorization was consumed, retained evidence, unused later authorizations, and the single main-thread decision needed. Confirm no later phase ran and no retry/cleanup occurred.

