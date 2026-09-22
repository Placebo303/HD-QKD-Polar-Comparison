# P2 Operator Prompt (2026-09-21) — FROZEN, NOT GRANTED

- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). ID G-P2: frozen only, authorizes NOTHING.
- Entrypoint: `docs/research_cycles/V80-NBLDPC-JAN21/P2_PACKET.md` (§§1–7 frozen).
- Arm (i) DE: ONE threshold point at joint rate 0.796875 (m = 416/n = 2048; f = 1.25741 governs; memo L25 m≈208 line is superseded); V26 `run_mcde_posterior` read-only, q = 32/λ = {2:1}/ρ = make_rho(0.796875), JOINT sampler (S1-CONFIRM); screen 4000/60 + confirm 16000/100; seeds EXACTLY {2026094951, 2026094952}; root `workspace/p2_<uuid8>` (fresh, absence proven).
- Gate (i): |f_DE(s1) − f_DE(s2)| ≤ 0.05 ⇒ reproducible; else NON-REPRODUCIBLE, no decomposition. Budget: ≤96 DE calls + ≤1200 s; per-call ≤300 s; RSS <2 GiB.
- Arm (ii) curve: NEW soft-marginal points m ∈ {196, 204, 192} (THAT ORDER, wall permitting), instance 2026092001 ONLY, 240 paired blocks `2026095601+idx`; b2f formula/decoder/pins; bar-12 early-stop (censored partials plotted distinctly); m = 200 REFUSED (P1-owned); 202/208 by citation (b2f 6/240, 0/240); 180–188 out of scope. Budget: ≤3600 s total; per-decode ≤300 s; RSS <2 GiB.
- Gate (ii): report monotone OR explicitly non-monotone/censored — no inference either way.
- Assembly: m_min − m_DE = finite-length; m_DE − 170.5 = structured (m_DE ≡ f_DE×852.544/5); unresolved ⇒ ">208", no inference. DIAGNOSTIC only, never extrapolated.
- STOP on any science-input change. New thin modules only; frozen kernel/modules untouched; fake-only tests.
- Deliverables: `P2_DE_RESULT.md` + `P2_CURVE_RESULT.md` + assembly note + machine artifacts per root; append-only `EXPLORATION_LOG.md`; one batch-end independent review.
- Precedence: P1 first; P2-(i) may parallel; P2-(ii) assembles after P1 Stage-1; never re-measure m = 200 here. Synthetic only; no pooling; no off-channel extrapolation. Does NOT establish FER/SKR/qualification/real-data claims.
- Pre-EXECUTE Q0–Q6 + fresh explicit user grant required per arm before ANY execution. This prompt authorizes NOTHING.

> **SUPERSEDED 2026-09-21 by `docs/V80_BASELINE_20260921.md`** — planning authority moved there; retained for history.
