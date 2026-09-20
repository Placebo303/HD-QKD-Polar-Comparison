# S2 Timing Probe — 2026-09-20 (EXPLORE, timing only)
Track: EXPLORE timing probe; no FER claims; bounds G-S2FER Pre-EXECUTE only.
Construction: `construct_l2(seed=2026092001)` → four_cycles ACTUAL=1158 (expected 1158, match); family=peg-irregular; construct wall 0.03 s.
Harness: `smoke_decode_frame(max_iter=300)`, synthetic QSC QBER≈5% hook; 1 warm-up + 3 timed (seeds 1 / 2,3,4); pure in-memory, no workspace/results writes.
Warm-up wall: 19.29 s (first-call JIT warmup).
Timed walls: 14.84 s (238 it), 19.65 s (300 it), 8.19 s (128 it) → mean 14.23 s, max 19.65 s.
Extrapolation (240 decodes): warm-up + 240×mean ≈ 19.3 + 3414 ≈ 3433 s vs 3600 s window → headroom ≈167 s (~5%).
Worst-case bound (240×max): ≈4735 s > 3600 s — per-decode variance is the schedule risk.
Verdict: MARGINAL (>3000 s) — fits the window on mean but with thin margin; batching/checkpointing advised for Pre-EXECUTE.
RSS peak: ≈721 MB (single process).
Env: python 3.12.3, numpy 2.5.3, numba 0.67.0; branch formal-ir-v72p1-addendum-clean; total probe wall ≈62 s.
Note: smoke outcomes carry no FER meaning (N=1 each); no conclusion beyond fit-vs-window.
