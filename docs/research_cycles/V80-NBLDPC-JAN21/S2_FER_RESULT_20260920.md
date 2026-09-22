# S2 FER Result — 2026-09-20 (EXPLORE synthetic; V1 arm only)

- Track: EXPLORE synthetic. Machine verdict ONLY per frozen gates; no S2-entry decision, no qualification claim.
- Root: `workspace/s2_fer_2752f403` (`manifest.json` + `rows.json` executor, `group_accounting.csv` operator). Logs: `/tmp/opencode/s2_fer_run1.log`, `.time`.
- Provenance: V1 `construct_l2(seed=2026092001, max_trials=20)`; `four_cycles==1158` assert PASSED pre-run (`verify.four_cycles_ok: true`). Frame seeds literal V1 `2026096001+idx`, used idx 0..15 (groups 0–3). Decoder log-FFT-SPA `max_iter=300`, `qber=0.05`, QSC p=0.05 proxy.
- Per-group (all FAIL; 0/16 frames `exact_match`; `converged` all false):
  - g0 seed 2026096001: iters 7/300/300/204, status conv_nosynd ×3 + max_iter ×1, wall 53.61 s
  - g1 seed 2026096005: iters 7/300/90/192, conv_nosynd ×3 + max_iter ×1, wall 38.74 s
  - g2 seed 2026096009: iters 174/238/192/174, conv_nosynd ×4, wall 50.70 s
  - g3 seed 2026096013: iters 300/88/7/300, conv_nosynd ×2 + max_iter ×2, wall 43.10 s
- FER point estimate (completed groups): 4/4 = 1.0. Rule-of-three upper bound (3/n): N/A — applies only with 0 failures; failures = 4.
- f_super = 1.2246 (1044/852.544, D_blind = 0 MEASURED — no blind/puncturing rounds in campaign path, NEVER assume zero). Sensitivity: Δf_super = D_blind/852.544 (16 bits ≈ +0.019; headroom to 1.3 is 64.31 bits).
- Machine verdict: **FAIL** (executor `FAIL-early-stop`, 4th group failure). Gate (a) superframe FER ≤5% (≤3/60): 4 fails already exceed → FAIL. Gate (b) f_super ≤1.3: 1.2246 → pass. AND → FAIL.
- Budget: 1 window used (`continuations_used: 0/1`); elapsed 186.18 s of 3600 s cap; wall 3:11.81; RSS max 153080 kB (~150 MiB) < 4 GiB; max per-decode ~19.8 s < 300 s. No continuation (terminal FAIL state is not resumable; none used).
- Ledger: 16 decodes / 4 groups_completed (`ledger_ok`, `rows_ok` true). Process exit status 0.
- V2 arm: packet runs V2 IFF V1 FAIL — V2 NOT run here (separate grant/Pre-EXECUTE required).
