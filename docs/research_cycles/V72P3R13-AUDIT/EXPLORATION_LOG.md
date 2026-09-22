# V72P3R13-AUDIT Exploration Log (analysis track, zero calls)

## 2026-09-18: R13 AUDIT solidification — PIVOT verdict (0/90 candidates vs >=14 rule)

- Track: analysis. Zero decoder/execution calls in this task. Solidification writes only; main-thread ACCEPTANCE granted. No re-judgment. Pool reads FORBIDDEN — worked from evidence roots only.
- Scope: single entry. No other files in `docs/research_cycles/V72P3R13-AUDIT/`.

### A1 — Histograms (residual-error distributions)

- Combined: 0/0/0/13/77 (bins as recorded in evidence roots).
- R11: 22/98/61.88/65.
- R12: 21/95/62.88/66.
- Per-seed splits: same shape +/-1.0 across seeds.
- Reading: R11 vs R12 distributions are the same shape within +/-1.0; no seed or run explains the miss.

### A2 — Success contrast

- Residual-at-success: all 0.
- Stage S0/S1/S2: R11 0/26/61; R12 3/15/61.
- Iters-to-converge <= 56; buckets 52/26/8/1 + 43/30/6/0.
- Pre-success residuals span 20-90, same range as failures.
- Reading: successes converge fast (<=56) with residual 0; pre-success residuals overlap the failure range, so residual magnitude alone does not separate near-miss from success.

### A3 — Cap analysis

- Exhausted pegged 270/270 = 100%.
- Early-exit failures = 9 tag-escalations residual-0, zero give-ups.
- Accepted-at-cap 0/166.
- Reading: cap-peg ⇔ fail holds exactly; no accepted frame sat at cap, and no failure was an early give-up.

### A4 — Verdict PIVOT

- Verdict: PIVOT. 0 < 14 (frozen near-miss bar); min 21-22 > 2x bar.
- Residuals are structural (21+), not marginal misses.
- Surprise: frame 2166/block87 S0=33 -> S1=20 -> S2=61, sole R11 S2>S1 case.
- S1>S0 in 65/90 — cold-restart worsens far misses.

### A5 — Efficiency

- Per-accepted ≈ 646-649 vs per-exhausted 664.
- S2 sole high-yield stage 61/61.
- 35.73% disclosure burned on exhausted frames.

### Routing OUT

- PIVOT accepted → S3 rejected.
- Next R14 multi-session weight survey (teed, not started here).
