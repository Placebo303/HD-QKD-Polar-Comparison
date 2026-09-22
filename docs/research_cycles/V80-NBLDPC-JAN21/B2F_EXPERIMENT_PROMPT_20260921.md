# B2F Experiment Prompt (2026-09-21) — FROZEN, NOT GRANTED

- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). ID G-B2F: frozen only, authorizes NOTHING.
- Entrypoint: `docs/research_cycles/V80-NBLDPC-JAN21/B2F_EXPERIMENT_PACKET_20260921.md` (§§1–8 frozen).
- Run ONE arm: `--arm F208|F202` (n=1024 GF(32), λ={2:1}, m=208|202, construct seed 2026092001/trials 20 via the A208/A202 instance; pins fc0 + rank-full + twice-identical, girth recorded-not-gated); 240 blocks = 240 decodes; block seeds `2026095601+idx`, stream `o1_blk:{seed}`; root `workspace/b2f_<uuid8>` (fresh, absence proven).
- Prior (frozen formula): after the triple draw and y=b&31: `g1c = g1[:, b]`; `cond = g2[:, :, b].transpose(2,0,1)`; `marg = np.einsum("nu,nuv->nv", g1c.T, cond)`; per-row renormalize (row-sum guard; non-positive/non-finite → delta-at-0); `prior = center_rows_prior(marg, y)`; feed `v28.decode_error_domain_posterior(field, y.tolist(), dense, s_x, prior, 300)`. NO genie u1, NO argmax u1, NO L1 code. max_iter=300/streak 3; accept = `exact_match` (x̂==u2).
- Report-only per block: `prior_entropy_bits` = Σ_i H(π_i) (1e-300 guard) and `u1_mismatches` (û1=argmax_u g1[u,b]; not a disclosure, not a criterion).
- Gates per arm (AND): (a) fails/240 ≤ 12, early-stop at the 13th fail; (b) f_super = (5m+64)/852.544 ≤ 1.3 unchanged O1 basis (F208 1.294947, F202 1.259759; D-u1 = 0.0 measured label, never-assume-zero note retained). No pooling across arms.
- Budgets: 240 decodes ≈600 s/arm est — MEASURE the first block; b2e risk: non-convergence ≈70 s/decode (300 iters) ⇒ gates must fire before the wall cap or INCOMPLETE-wall with ≤1 continuation; NEVER a false PASS; per-decode >300 s = terminal overrun. Wall ≤3600 s/window; RSS <4 GiB; ≤1 `--resume-from` (wall-partial only); no auto-relaunch.
- STOP on any science-input change. New module only (`formal_ir/v80_b2f_campaign.py`); frozen modules untouched; fake-only tests.
- Deliverables: `B2F_RESULT_20260921.md` + `rows.json` + `block_accounting.csv` per root.
- Interpretation: PASS ⇒ report to main thread — NO genie-retirement wording without a two-construct-seed replication; FAIL ⇒ return for the A2/O-D decision; no rerun/tuning; no S3. Does NOT establish FER/route/S3/qualification/genie-retirement; synthetic only; block ≠ S2c-group; paired seeds shared with O1R/P0/L1B/b2e (no independence claim).
- Pre-EXECUTE Q0–Q6 + fresh explicit grant required before ANY execution. This prompt authorizes NOTHING.
