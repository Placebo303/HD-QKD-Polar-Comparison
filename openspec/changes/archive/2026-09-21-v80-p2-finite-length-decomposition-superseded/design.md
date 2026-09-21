# V80-P2 Finite-Length Decomposition — Design

Sources: `docs/research_cycles/V80-NBLDPC-JAN21/P2_PACKET.md`,
`LITERATURE_DIRECTION_MEMO_20260921.md` §4(i), `docs/ROADMAP-20260921.md` §3 P2.
Condensation only; no new numbers.

## Joint rate (resolved)

- m = 416 over n = 2048 GF(32) symbols ⇒ rate 0.796875; leak 2144; content 1705.088; f = 1.25741. The route-memo L25 "m≈208 rows" line is superseded by its own L30 accounting (m = 208 would give f < 1, impossible); m = 416 governs.

## Arm (i) DE point

- Kernel `nonbinary_v26_mcde.py::run_mcde_posterior` read-only; ρ = make_rho(0.796875) (O1 precedent); JOINT (u1,u2) sampler, S1-CONFIRM convention (new thin sampler code only); screen 4000/60 + confirm 16000/100; seeds {2026094951, 2026094952} (S1_READINESS.md).
- Gate: |f_DE(s1) − f_DE(s2)| ≤ 0.05 (S1 flip-rule granularity). Budget: ≤96 calls + ≤1200 s; per-call ≤300 s; RSS <2 GiB.

## Arm (ii) curve partition (m ∈ [180,208], instance 2026092001, paired blocks)

- NEW {196 → 204 → 192} (wall permitting, ≤3600 s total); OWNED-BY-P1 {200} (reference only, never re-measured here); BY-CITATION {202: b2f 6/240; 208: b2f 0/240}; OUT-OF-SCOPE [180,188] (genie FAILs + weaker marginal prior ⇒ expected FAIL; scoping, not claim).
- Per-point: b2f formula/decoder/pins; bar-12 early-stop (censored partials distinct); own-basis f reporting; per-60 tally report-only.
- Gate: monotonicity over completed points reported (monotone or explicitly non-monotone/censored, no inference; no cross-m monotonicity assumed).

## Assembly + precedence + auth

- m_min (smallest 0/240 @2001 soft-marginal; else ">208 unresolved") − m_DE (≡ f_DE×852.544/5) = finite-length; m_DE − 170.5 = structured (170.5 = 852.544/5). DIAGNOSTIC, never extrapolated.
- P1 first; P2-(i) may parallel; P2-(ii) assembles after P1 Stage-1; P1 outcome never invalidates its owned measurement. Joint A2 in neither packet.
- Freeze consumes nothing; per-arm Pre-EXECUTE + fresh grant required; one append-only log + one batch-end review; fresh `workspace/p2_<uuid8>` roots; same repair/forbidden regime as P1 (no retry/resume/adaptive search; real-data/constant/pooling/extrapolation/m = 200-measurement forbidden).
