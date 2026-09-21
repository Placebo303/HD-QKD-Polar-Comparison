# P1 Operator Prompt (2026-09-21) — FROZEN, NOT GRANTED

- Track EXPLORE synthetic (EXPLORE_HEAVY); branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). ID G-P1: frozen only, authorizes NOTHING.
- Entrypoint: `docs/research_cycles/V80-NBLDPC-JAN21/P1_PACKET.md` (§§1–8 frozen).
- Run ONE arm: `--arm P1-R1|P1-R2` (instance 2026092001|2026092011; frozen same-instance A208 matrix; base = its LEADING 200 rows, rescue rows [200,208)); 240 blocks, seeds `2026095601+idx`, stream `o1_blk:{seed}`; root `workspace/p1_<uuid8>` (fresh, absence proven).
- Stage 1: cold-decode all 240 with base-200 code (b2f soft-marginal prior, v28 max_iter 300/streak 3, exact_match accept; NO genie/argmax/L1). Stage 2: COLD full-208 re-decode of EXACTLY the Stage-1 non-success blocks (undetected-class logged separately, never success). WARM-START FORBIDDEN.
- Report-only per block: `prior_entropy_bits`, `u1_mismatches`. Metrics: trigger rate r, E[leak] = 1064+40·r, f_exp = E[leak]/852.544 (own basis), f_eff = f_exp+4.785675·(F/240), headroom = 1108.31−E[leak].
- Gates per arm (AND): (a) final fails/240 = 0 HARD; (b) f ≤ 1.3 own basis (worst-case 1.294947 by construction + f_exp); (c) headroom ≥ 21.5 b (⇔ r ≤ 57.0%). Stage-1 k/240 vs bar 12 is context only.
- Budgets: wall ≤ 3600 s/arm total (single window); per-decode ≤ 300 s terminal; RSS < 2 GiB; NO resume/retry/adaptive search (≤1 preregistered engineering repair+rerun ONLY for infrastructure failure, inputs unchanged).
- STOP on any science-input change. New module only; frozen modules untouched; fake-only tests.
- Deliverables: `P1_RESULT_*.md` + `rows.json` + `block_accounting.csv` per root; append-only `EXPLORATION_LOG.md`; one batch-end independent review.
- Interpretation: PASS ⇒ report (P3→P5 path); FAIL ⇒ return (P4-mandatory path); no rerun/tuning; no S3. Synthetic only; no pooling across instances; never quote f_exp as f_eff if F > 0. Does NOT establish FER/route/S3/qualification/real-data claims.
- Pre-EXECUTE Q0–Q6 + fresh explicit user grant required before ANY execution. This prompt authorizes NOTHING.

> **SUPERSEDED 2026-09-21 by `docs/V80_BASELINE_20260921.md`** — planning authority moved there; retained for history.
