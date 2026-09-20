# B2E Experiment Prompt (2026-09-21) — FROZEN, NOT GRANTED

- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). ID G-B2E: frozen only, authorizes NOTHING.
- Entrypoint: `docs/research_cycles/V80-NBLDPC-JAN21/B2E_EXPERIMENT_PACKET_20260921.md` (§§1–9 frozen).
- Run ONE arm: `--arm B208|B202` (n=1024 GF(32), λ={2:1}, m=208|202, construct seed 2026092001/trials 20 via the A208/A202 instance; pins fc0 + rank-full + twice-identical, girth recorded-not-gated); 240 blocks = 240 decodes; block seeds `2026095601+idx`, stream `o1_blk:{seed}`; root `workspace/b2e_<uuid8>` (fresh, absence proven).
- u1 source = MAP: û1_i = argmax_u g1[u,b_i] from the frozen bundle (no refit, no decoder, no DE, no L1 construction). Rows = `posterior_rows_l2(bundle,b,û1)`; y=b&31; XOR-centered prior; `decode_error_domain_posterior` ONLY; max_iter=300/streak 3; accept = `exact_match` (x̂==u2). Genie ceiling REMOVED for this arm.
- Measure per block: k = Σ 1[û1_i≠u1_i] (measurement only, not a disclosure); D-u1 = 5·k; f_super = (m·5 + 64 + D-u1)/852.544.
- Gates per arm (AND): (a) fails/240 ≤ 12, early-stop at the 13th fail; (b) EVERY completed block's f_super ≤ 1.3 — the conservative D-u1 reading GATES; f_super_du0 (D-u1=0.0 measured label) is report-only, never gated. No pooling across arms.
- At the MEASURED mean D-u1 ≈ 40.5 b: B208 ≈ 1.342453, B202 ≈ 1.307264 (both > 1.3 — gate (b) is the binding constraint; per-block counts decide, not the mean). Do NOT substitute the tagless 1.267384/1.232195 variants.
- Budgets: 240 decodes ≈600–900 s/arm; wall ≤3600 s/window; per-decode ≤300 s; RSS <4 GiB; ≤1 `--resume-from` (wall-partial only); no auto-relaunch.
- STOP on any science-input change. New module only (`formal_ir/v80_b2e_campaign.py`); frozen modules untouched; fake-only tests.
- Deliverables: `B2E_RESULT_20260921.md` + `rows.json` + `block_accounting.csv` per root.
- Interpretation: PASS on BOTH arms ⇒ L1-code-free path opens (report to main thread, no auto-proceed); ANY FAIL ⇒ return to main thread with the b2a/b2c options; no rerun/tuning. Does NOT establish FER/route/S3/qualification/genie-retirement; synthetic only; block ≠ S2c-group.
- Pre-EXECUTE Q0–Q6 + fresh explicit grant required before ANY execution. This prompt authorizes NOTHING.
