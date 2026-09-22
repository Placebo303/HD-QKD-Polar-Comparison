# S2 FER V2 Result — 2026-09-20 (EXPLORE synthetic; V2 arm only)

- Track: EXPLORE synthetic. Machine verdict ONLY per frozen gates; no S2-entry decision, no qualification claim, no S3 claim.
- Root: `workspace/s2_fer_c5a176ee` (`manifest.json` + `rows.json` + `group_accounting.csv`, all executor-emitted). Logs: `/tmp/opencode/s2_fer_v2.log`, `/tmp/opencode/s2_fer_v2.time`.
- Provenance: V2 `construct_l2(seed=2026096101, max_trials=100)`; `four_cycles=1140` < 1158 → V2 VALID (`verify.four_cycles_ok: true`); `min_girth=0` (reported). Frame seeds literal V2 `2026096301+idx`, used idx 0..15 (groups 0–3). Decoder log-FFT-SPA `max_iter=300`, `qber=0.05`, QSC p=0.05 proxy.
- Per-group (all FAIL; 1/16 frames `exact_match` — g0f1 seed 2026096302 iter=2):
  - g0 seed 2026096301: iters 300/2/98/8, max_iter ×1 + conv_nosynd ×2 + success ×1, wall 27.20 s
  - g1 seed 2026096305: iters 300/300/300/7, max_iter ×3 + conv_nosynd ×1, wall 61.31 s
  - g2 seed 2026096309: iters 196/300/7/300, max_iter ×2 + conv_nosynd ×2, wall 49.97 s
  - g3 seed 2026096313: iters 120/86/98/2, conv_nosynd ×3 + converged-no-exact ×1, wall 19.08 s
- FER point estimate (completed groups): 4/4 = 1.0. Rule-of-three upper bound (3/n): N/A — applies only with 0 failures; failures = 4.
- f_super = 1.2246 (1044/852.544, D_blind = 0 MEASURED — no blind/puncturing rounds in campaign path, NEVER assume zero). Sensitivity: Δf_super = D_blind/852.544 (16 bits ≈ +0.019; headroom to 1.3 is 64.31 bits).
- Machine verdict: **FAIL** (executor `FAIL-early-stop`, 4th group failure). Gate (a) superframe FER ≤5% (≤3/60): 4 fails already exceed → FAIL. Gate (b) f_super ≤1.3: 1.2246 → pass. AND → FAIL.
- Budget: 1 window used (`continuations_used: 0/1`); elapsed 157.59 s of 3600 s cap; wall 2:40.52; RSS max 153364 kB (~150 MiB) < 4 GiB; max per-decode ~21.0 s < 300 s. No continuation (terminal FAIL state, not wall-exhaustion).
- Ledger: 16 decodes / 4 groups_completed (`ledger_ok`, `rows_ok` true). Process exit status 0.
- Cross-ref: V1 `S2_FER_RESULT_20260920.md` (FAIL-early-stop 4/4, four_cycles=1158); V2 (four_cycles=1140) likewise FAILs at the 4th group → no S3; fallback review owns next step.
