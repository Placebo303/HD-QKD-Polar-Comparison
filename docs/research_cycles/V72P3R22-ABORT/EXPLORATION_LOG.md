# V72P3R22-ABORT — EXPLORATION_LOG (abort-predictor audit)

## 2026-09-18 — R22 abort-predictor audit (analysis track, zero calls, ~1 min wall)

- Track: analysis only. No decoder/execution calls, no data generation, no commit. Close-out write.
- Feature audit:
  - iters dead: all exhausted + all S2-accepts pegged at 90; P(exhaust | iters≠90) = 0/41.
  - Residual separation tables (S0/S1 bins), incl joint worst (both≥71): 69/109 = 0.63 — no separable cut.
  - S2-accept range blankets exhausted range.
- ROC (in-sample, optimistic):
  - Rule A T=95: 8 aborted / 480 saved / 0 lost.
  - Rule B T=91: 8 aborted / 800 saved / 0 lost.
  - Both ≪ 1500 bar; decision edge rides sample maxima (S2-accept max 93/94) → fragile.
  - Exhausted burned 59760 bits pool-wide (~36%).
- Verdict: PREDICTOR-DEAD — no threshold meets lost==0 & ≥1500. Reopen needs NEW signals (e.g. per-iteration trajectories / syndrome dynamics, neither logged).
- Routing: OUT — abort line closed.
