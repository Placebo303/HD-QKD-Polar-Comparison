# Phase P independent readiness review R1 (D7 X1–X4 master packet)

- Authority: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md` §6 P10 and §7.
- Reviewer: independent session, separate context from the Phase P implementation operator.
- Verdict: `PASS_WITH_FINDINGS` — P01–P09 implemented and test-covered; no blockers; P10 review performed, not self-accepted.

## Confirmed (raw evidence in review transcript)

- P01/P02: `--historical-provenance-probe` production path calls `probe_historical_decoder_provenance(decode_fn=None)` exactly once, no silent fallback; JSON contract enforced (`decoder_calls: 1`, `writes: 0`); exit 0 only for exact `CHECK_UPDATED` + finite + shape-valid + iterations >= 1, else exit 2 `X1_PROVENANCE_PROBE_FAILED`; refusal precedes probe work while the flag is false; no file/root written; `--consistency` unchanged and relabelled `same-input synthetic consistency`.
- P03–P06: selector (immutable X2 root, f=1.2 invoked/non-crash/finite/non-exact, identity preserved, no dedup/replacement), plan-before-bind, zero-selected terminal, deterministic reconstruction, field-exact `ROW_LAYERED_90` baseline replay gate with first-mismatch STOP, 7-file never-overwrite writer, label `STRONG_REFERENCE_DIAGNOSTIC`.
- P07: refusal on false flag before X2 read/bind/root creation.
- P08/P09: `--g2` requires `x4_g2_execution_authorized`, asserts every other D5 execution flag false, aborts on existing root, calls `run_g2_synthetic(authorized=True)` exactly once, never mutates a D5 flag; additive per-layer/wall/RSS fields only.
- Prior finding resolved: `bind_reference_ladder_decoders` wrapper/kwargs/signature coverage via fake module plus a clean-subprocess real v35 import + real bind in the production CLI layout, with no wrapper invocation; true-condition binding probe belongs to X3 Pre-EXECUTE before authorization consumption.
- Tests replayed independently: new suite 55 passed; consistency suite 36 passed; bp+decert+new 92 passed; predecessor suites 165/32/62/32 passed; `py_compile` exit 0. Mixed cross-suite invocation fragility is pre-existing and disclosed; per-group invocation is the T1 protocol.
- Zero production decoder/CAL/VAL calls; frozen roots `workspace/d7_r1_multigraph_20260913_r1`, `workspace/d7_r1_reference_ladder_20260913_r1`, `workspace/v72p2d5_g2/20260906_r1` absent; all eight authorization flags false; branch `formal-ir-v72p1-addendum-clean`, HEAD `278fdf07`, no commit/staging/push.

## X3 call accounting adjudication

Not a contract violation. Total = 3S + R ≤ 576 − 2R ≤ 576 (proof in Task 1 wording); verified by subset enumeration and the full-matrix test (S = 192, ladder = 576, reconstruction = 0). The record's former "672" wording is corrected to the construction bound; X3 Pre-EXECUTE/Pre-RESULT must check `ladder_calls + reconstruction_calls ≤ 576` from actual records.

## Non-blocking findings carried to phase Pre-EXECUTE

1. X3 `X3_ENGINEERING_BLOCKED` currently exits 0 (only baseline mismatch maps to exit 1); document the mapping or make it nonzero at X3 Pre-EXECUTE.
2. `run_g2_bridge` existence check is repo-rooted while the writer resolves the G2 root CWD-relative; under the frozen command (CWD = repo root) they coincide. Prefer passing the resolved `out_dir` in the runner closure at X4 Pre-EXECUTE.
3. Per-call watchdogs (X1/X4 120 s, X3 480 s) are external, not in-process; X3 Pre-EXECUTE must record the external watchdog command/owner explicitly.
4. `X3_BASELINE_REPLAY_MISMATCH_BLOCKED` also covers ladder crashes/reconstruction errors; Pre-RESULT breakdown must read the `where` field.
5. `run_g2_bridge` coerces a non-dict runner return to `{}` (latent only); guard at X4 Pre-EXECUTE.
6. OpenSpec delta spec was not extended for Phase P entrypoints (design §9 + tasks P cover them); optional consistency item.

## Lifecycle

- Terminal: `X1_READY_AWAITING_EXPLICIT_AUTHORIZATION`.
- All execution flags remain false; no authorization consumed; X1–X4/G1/D7-H still dormant and separately user-authorized.
- Next gate: main-thread X1 authorization (`x1_consistency_probe_authorized: true` + exact command + target absence + budget/stop rules, per packet §8).
