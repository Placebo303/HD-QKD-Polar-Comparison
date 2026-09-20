# O1 Experiment Prompt (2026-09-20) — FROZEN, NOT GRANTED

- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). ID G-O1: frozen only, authorizes NOTHING.
- Entrypoint: `docs/research_cycles/V80-NBLDPC-JAN21/O1_EXPERIMENT_PACKET_20260920.md` (§§1–9 frozen).
- Run ONE arm: `--arm A188|A208` (n=1024, λ={2:1}, m=188|208, seed 2026092001/trials 20, pins fc0/g8/rank-full); 60 blocks = 60 decodes; seeds `2026095501+idx`, stream `o1_blk:{seed}`; root `workspace/o1_<uuid8>` (fresh, absence proven).
- Constructor asserts first (STOP on mismatch + construct-twice-identical). A208 only: run A208-DE pre-check first (V26 `run_mcde_posterior`, S1 convention), record DE-cover label.
- Semantics (exact): triple draw b~p_b/u1~g1/u2~g2 (delta-at-0); y=b&31; rows=γ₂(·|b,u1); XOR-centered prior; `decode_error_domain_posterior` ONLY; max_iter=300/streak 3; GENIE true-u1 (D1 ceiling).
- Per-block exact_match; early-stop at 4th block fail → FAIL. Gates per arm: fails/60≤3/60 AND f_super≤1.3 (A188 1.177652; A208 1.294947, ~4.3 b headroom).
- D_blind=0 MEASURED + sensitivity Δf=D_blind/852.544. f_L2 informational only.
- Budgets: 60 decodes ≈660 s est; wall ≤3600 s/window; per-decode 300 s; RSS <4 GiB; ≤1 `--resume-from` (wall-partial only).
- STOP on any science-input change. New module only (`formal_ir/v80_o1_campaign.py`); frozen modules untouched.
- Deliverables: `O1_RESULT_20260920.md` + `rows.json` + `block_accounting.csv`. Does NOT establish L1/two-layer/S3/qualification; block≠S2c-group.
- Pre-EXECUTE Q0–Q6 + fresh explicit grant required before ANY execution. This prompt authorizes NOTHING.
