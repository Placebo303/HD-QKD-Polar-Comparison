# L1B Experiment Prompt (2026-09-20) — FROZEN, NOT GRANTED

- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). ID G-L1B: frozen only, authorizes NOTHING.
- Entrypoint: `docs/research_cycles/V80-NBLDPC-JAN21/L1B_EXPERIMENT_PACKET_20260920.md` (§§1–9 frozen).
- Why: retire genie-u1 (D1 ceiling) — real L1 + combined chain at the two P0-passed budget points. TWO STAGES: Stage A gates Stage B.
- Configs (total 208 rows, leak 1104, f_super 1.294947): PRIMARY C6 (m1=6/m2=202) + SECONDARY C8 (m1=8/m2=200). L1: n=1024 GF(32) λ={2:1}; construct seed 2026092001/trials 20.
- Stage A (L1-only, FIRST): y1=(b>>5)&31; rows=p_u1_gb.T[b] (v26 L236-237); XOR prior (v28 L189-197); `decode_error_domain_posterior` ONLY; max_iter=300/streak 3; L1 exact = û1==u1.
- Blocks REUSED paired with O1R/P0: `2026095601+idx` idx=0..239, stream `o1_blk:{seed}` (declared reuse, packet §2 rg-note; NO independence claim).
- Pins: fc==0 + rank-full + twice-identical (STOP-BLOCKED on mismatch); girth recorded-not-gated. f_L1≈1.142/1.522 informational only.
- Stage A gates/arm: fails/240≤12 AND f_super 1.294947≤1.3; early-stop at 13th; no rerun/tuning. Per-config: A6⇒B6, A8⇒B8 independently.
- Stage B (passing configs only): L1 → û1 → L2 with û1 (y2=b&31; rows2=γ₂(·|b,û1)); system success = BOTH exact; genie RETIRED (`real-L1 chain`).
- Stage B gates/arm: system fails/240≤12 AND f_super≤1.3 (measured-D_blind); early-stop at 13th.
- DE precheck OPTIONAL-with-label (`exploratory`; Stage A proceeds regardless; gates unchanged).
- Budgets: A ≤900 s/arm (≈500 s est); B ≤1500 s/arm (≈1200 s est); wall ≤3600 s/window; per-decode 300 s; RSS <4 GiB; roots `workspace/l1b_<uuid8>` (≤4); ≤1 wall-partial `--resume-from` each.
- D_blind=0 MEASURED + sensitivity Δf=D/852.544; headroom 4.31 b unchanged; blind surcharge still open.
- Executor: NEW `formal_ir/v80_l1b_campaign.py` only (E1–E6); frozen modules untouched; fake-only tests.
- Interpretation: A FAIL ⇒ rework memo (no B that config); B FAIL ⇒ chain diagnosis; NO auto-proceed to S3; report to main thread.
- Deliverables: `L1B_RESULT_20260920.md` + `rows.json` + `block_accounting.csv`. Does NOT establish real-data/S3/route claims.
- Pre-EXECUTE Q0–Q6 + fresh explicit grant required before ANY execution (A-grant covers A only; B needs A PASS). This prompt authorizes NOTHING.
