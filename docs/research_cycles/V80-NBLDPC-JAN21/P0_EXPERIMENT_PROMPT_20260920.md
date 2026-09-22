# P0 Experiment Prompt (2026-09-20) — FROZEN, NOT GRANTED

- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). ID G-P0: frozen only, authorizes NOTHING.
- Entrypoint: `docs/research_cycles/V80-NBLDPC-JAN21/P0_EXPERIMENT_PACKET_20260920.md` (§§1–9 frozen).
- Why: de-risk the L1 budget trade (m1≥6 ⇒ m2≤202) BEFORE any L1 build; the 188–208 cliff is unmapped.
- Arms (L2-only, genie-u1, max TWO): `--arm A202` PRIMARY (m=202, leak 1074, f_super≈1.2597) + `--arm A200` SECONDARY (m=200, leak 1064, f_super≈1.2480). A206 REJECTED (circulated 1.2715 = f(204); non-budget point).
- Semantics (exact O1/O1R): triple b~p_b/u1~g1/u2~g2; y=b&31; rows=γ₂(·|b,u1); XOR prior; `decode_error_domain_posterior` ONLY; max_iter=300/streak 3; GENIE true-u1 (D1 ceiling).
- Seeds PAIRED with O1R: `2026095601+idx` idx=0..239, stream `o1_blk:{seed}` (declared reuse, packet §3 rg-note); construct seed 2026092001/trials 20; 240 blocks = 240 decodes/arm.
- Pins: fc==0 + rank-full + construct-twice-identical (mismatch → STOP-BLOCKED); girth recorded-not-gated (dry-construct pins measured at Pre-EXEC).
- Gates per arm standalone: fails/240≤12 AND f_super≤1.3; early-stop at 13th fail; per-60 tally report-only; no rerun/no tuning.
- D_blind=0 MEASURED + sensitivity Δf=D/852.544. f_L2 informational only.
- Budgets: ≤900 s/arm; wall ≤3600 s/window; per-decode 300 s; RSS <4 GiB; root `workspace/p0_<uuid8>` (fresh, absence proven); ≤1 `--resume-from` (wall-partial only).
- Interpretation: A202 PASS ⇒ L1 MAY proceed at m2≤202; FAIL ⇒ memo alternatives re-open. NO auto-proceed either way; report to main thread.
- STOP on any science-input change. Extend `formal_ir/v80_o1_campaign.py` only (D1–D5); frozen modules untouched.
- Deliverables: `P0_RESULT_20260920.md` + `rows.json` + `block_accounting.csv`. Does NOT establish L1/threshold/combined-FER/S3.
- Pre-EXECUTE Q0–Q6 + fresh explicit grant required before ANY execution. This prompt authorizes NOTHING.
