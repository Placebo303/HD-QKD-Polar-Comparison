# V80-P2 Finite-Length vs Structured-Channel Decomposition — Proposal

- Charter: `docs/ROADMAP-20260921.md` §3 P2 (science-depth track, parallel with P1).
- Packet: `docs/research_cycles/V80-NBLDPC-JAN21/P2_PACKET.md` (Acceptance ID G-P2, frozen NOT granted) + `P2_PROMPT.md`.
- Track: EXPLORE synthetic. This change itself authorizes no execution and consumes no budget; arm execution needs a fresh explicit grant + Pre-EXECUTE; batch-end review closes the batch.
- Standing: this is the only currently identifiable route to a generalizable contribution (`LITERATURE_DIRECTION_MEMO_20260921.md` §4(i)) — literature cannot split finite-length from structured-channel penalty (Zhou: binary, QBER 2%, n ≥ 2^16, arXiv-HTML-derived; Müller: binary BSC, n = 2^16).

## Why (what changed)

- Flagship f ≈ 1.29 sits +0.129 above Müller LDPC 1.166 with no decomposition; settling it requires (i) one MC-DE threshold point at the joint rate (V26 kernel reuse) and (ii) a soft-marginal FER curve over m ∈ [180,208] on the frozen channel.
- The curve must not double-count P1: m = 200 is OWNED BY P1 (consumed here by reference only), m ∈ {202, 208} by citation (b2f), m ∈ {192, 196, 204} newly measured here (@instance 2026092001 only), m ∈ [180,188] explicitly out of scope (genie already FAILs; scoping rationale frozen in packet).

## Scope (frozen)

- Arm (i): q = 32, λ = {2:1}, ρ = make_rho(0.796875), joint sampler, S1-CONFIRM sampling, seeds {2026094951, 2026094952}; reproducibility gate |Δf_DE| ≤ 0.05; budget ≤ 96 DE calls + ≤ 1200 s.
- Arm (ii): 3 new points {196, 204, 192} in that priority order within ≤ 3600 s total; bar-12 early-stop with censored-partial plotting; monotonicity reported (either outcome, no inference).
- Assembly: m_min − m_DE = finite-length penalty; m_DE − 170.5 = structured-channel/construction penalty (m_DE ≡ f_DE × 852.544/5). DIAGNOSTIC only.

## Non-goals

- No extrapolation of the decomposition to other channels/noises/alphabets.
- No FER/SKR/qualification/publication/real-data claim; no joint-A2 construction; no P1 re-measurement of m = 200.
- No new decoder, kernel change, or accounting change.

## Affected specs

- `specs/v80-p2-finite-length-decomposition/spec.md` (delta: DE point, curve partition + precedence, assembly rule, budgets).

> **SUPERSEDED 2026-09-21 by `docs/V80_BASELINE_20260921.md`** — planning authority moved to the consolidated baseline; retained for history. No new OpenSpec change created (consolidation is documentation-only).
