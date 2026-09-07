# G1 Result Acceptance R1 — sole frozen attempt accepted as synthetic completed-no-signal failure

```
G1_RESULT_ACCEPTED
scope: SYNTHETIC_COMPLETED_NO_SIGNAL_FAIL
outcome: G1_COMPLETED_NO_SIGNAL_FAIL
passed: false
```

- Accepted root: `workspace/v72p2d5_g1/20260907_r2` (exactly 4 files: `results.json`, `table.csv`, `report.md`, `execution_summary.json`). Phase `g1`, width 64, `f in {1.0, 1.2}`, frozen rows `1.0→m1 49/m2 43`, `1.2→m1 59/m2 52`, block seeds `2026090600..2026090699` (100 ordered ints). Accepted implementation `cf61ee63`.
- Evidence chain: `cf61ee63` (accepted G1 readiness implementation) → `6494b623` (pre-execution baseline) → `f4d577fb` (authorization: `g1_execution_authorized false→true`, single frozen-command attempt) → `58c68961` (consumed-attempt operator return, `true→false`, current HEAD). `6494b623..HEAD` is exactly those two commits; nothing else.
- Both reviews: Pre-EXECUTE review PASS (single frozen command, one attempt, no-retry/no-G2 authorization semantics) + Pre-RESULT review `G1_PRE_RESULT_REVIEW_R1.md` L117 `G1_PRE_RESULT_REVIEW_PASS` (R01–R09 all PASS, internal coherence only, not acceptance).
- Literal values (direct reads, all four files coherent): per f attempted `100`; APP exact `0/100`, rate `0.0`, failure fraction `1.0`; APP syndrome-ok `0`; oracle exact `0`; oracle syndrome-ok `0`; `app_iterations_max 180` (= 2×90 cap, `<= 180` met); APP iterations total `18000 = 100×180`; oracle iterations total `1800 = 20×90`; APP calls `100×2×2 = 400`, oracle calls `20×1×2 = 40`, `decoder_calls 440`; crashes `0`; nonfinite `0`; monotonic `true`. Arithmetic: `1 − 0/100 = 1.0`; `18000/180 = 100` blocks; `1800/90 = 20` oracle blocks; `400 + 40 = 440`.
- Resources pass, signal fails: stored entrypoint wall `238.86517630005255 s <= 900`; operator outer wall `239.110 s <= 900`; run peak RSS `115142656 B = max(114167808, 115142656) < 2147483648` (2 GiB). Signal recomputation: zero-nonfinite TRUE ∧ rates nondecreasing TRUE ∧ top APP exact `> 0` FALSE → signal FALSE → terminal `G1_COMPLETED_NO_SIGNAL_FAIL`, `passed=false` (passed iff `G1_TREND_PASS`). Resource success does not override the no-signal outcome.
- Isolation: `exact` (`x_hat == x_true`), `syndrome_ok` (decoder-reported ∧ recomputed match), and oracle counters are separate keys/counters; failure rate derives solely from APP exact; classification reads only nonfinite/wall/RSS/APP-exact/monotonic. Stored zeros stay literal zeros — no relabeling as FER, undetected success, correctness, or data quality.
- Consumed attempt / no rerun: the single authorized G1 attempt is consumed (`g1_execution_authorized: false` now). This acceptance grants no second G1 attempt, no retry/resume, no parameter change, no G2, no real-data work. G2 root `workspace/v72p2d5_g2` absent. All nine `*_execution_authorized` remain false; `scientific_promotion: false`.
- Nonclaims (explicitly rejected): not a trend pass; not FER/leakage/efficiency/key-rate evidence; not decoder-correctness or method-success evidence; not qualification, promotion, or G2 readiness; not permission to rerun; not a reinterpretation of the formal record. Acceptance trusts the negative record as internally coherent; it does not make the method pass.
- Next: bounded failure attribution only (`next_gate: G1_NO_SIGNAL_ATTRIBUTION_IN_PROGRESS`), under the D5 attribution packet. No formal CLI phase, no formal-root write, no VOID-interior read.
