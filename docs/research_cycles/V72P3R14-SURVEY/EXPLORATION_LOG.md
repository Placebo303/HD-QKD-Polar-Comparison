# EXPLORATION_LOG — V72P3R14-SURVEY

## 2026-09-18 — Characterization audit (windows-only, zero decoder calls)

Track: EXPLORE. Scope: USED-key characterization audit across 3 surveyed
sessions. No decoder invocation. Wall: 7.4s / 600s cap.

Inventory (as surveyed):
- 1M: 2130 frames / 4260 blocks
- 1p5M: 5125 frames / 10250 blocks
- 2M: 5513 frames / 11026 blocks
- USED-key table as surveyed (no re-extraction, no block picking).

Weights (U2 per-block, USED key):
- 1M: mean 72.70, med 73, min 51, max 93, p99 86
- 1p5M: mean 77.62, med 78, min 55, max 95, p99 90
- 2M: mean 90.07, med 90, min 65, max 108, p99 102
- U1 similar: 69.76 / 74.82 / 87.88 (1M / 1p5M / 2M means)
- Prior-entropy/block ≈ 4.343 ± 0.008 ALL sessions — session-blind weak prior.

Estimator (ASSUMED-labelled, Â = 0.6; NOT confirmation evidence):
- m_est = ceil(mean) + 8; m_est99 variant; k = 128 − m
- net = k·5·Â − (5m + 64)
- Ranking: 1M −328 > 1p5M −368 > 2M −472 — ALL negative
- Closed form: net = 320 − 8m ⇒ positive iff m < 40 iff weight < 32;
  observed means 72–90, far above.

Verdict: NO-POSITIVE-REGIME — survey forces no window.

Anti-peeking: complied. Windows-only rule; no block picking; CAL-class
numbers never used as confirmation evidence.

Cost: 7.4s wall of 600s cap. No decision-log entry (characterization only,
reviewer rule pattern).
