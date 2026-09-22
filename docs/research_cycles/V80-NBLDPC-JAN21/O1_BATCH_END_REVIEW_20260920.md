# O1 Batch-End Review (2026-09-20) — EXPLORE, independent, batch-only
- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). Scope: packet/PreEXEC/executor-review/result 20260920 + roots `workspace/o1_0ab23d59` (A188), `o1_a10525fc` (DE), `o1_444c02cd` (A208). Verdict: **PASS_WITH_FINDINGS** (non-blocking only).
## 1. Machine gates — PASS
- A208: fails/60=0≤3 AND f_super=1.294947≤1.3 (recomputed 1104/852.54422528=1.29494748, exact). A188: 4 fails/14 blocks, FER 4/14=28.6%, FAIL-early-stop at 4th fail (block 13); f_super=1.177652≤1.3 (gate (b) met, gate (a) unattainable).
- Budgets interior: wall 290.4 s (A188) / 143.3 s (A208) vs 3600 cap; per-decode max 75.85 s / 4.21 s vs 300 cap; 0 continuations both; D_blind=0.0 measured.
## 2. Evidence consistency — PASS
- Result-doc numbers match manifests/rows/CSVs exactly: A208 60/60 exact, iters {7:3,…,18:1}; A188 14 rows, fails {5,7,8,13}, iters/statuses match; seeds gapless 2026095501+idx both arms; ledger==rows==csv counts.
- DE precheck: converged=true, 36 iters, final entropy ~3.1e-296, rho {9:0.141,10:0.859} per packet; campaign label `covered` via explicit `--de-label` (manifest `label_source`). Two-roots pattern (precheck root vs fresh campaign root, one window each) matches packet §3/§7.
## 3. Launch incident — PASS_WITH_FINDINGS
- OBR-1 (non-blocking): A188 first-launch silent death + `setsid nohup` relaunch is NOT retained in any O1 cycle doc (`/tmp/opencode/o1_*.log` hold final summaries only). No-contamination proven: one manifest/root, single wall window, continuations 0, gapless seeds, ledger==rows==csv. Recommend one incident line in RESULT before archive.
## 4. Retained failures / history — PASS
- A188 FAIL raw retained (14 rows, 4 fails, `partial=true`, FAIL-early-stop); no resume-after-terminal. S2c/S2b/V1/V2 history untouched: zero tracked modifications, no `results/`/`outputs_comparison/` writes.
## 5. Claim ceiling (explicit)
- SUPPORTS: at n=1024/m=208/λ={2:1}/genie-u1/empirical-2M/D_blind=0, synthetic block FER 0/60 with f_super 1.294947 meets frozen gates; A188 margin-sensitive (28.6% block FER).
- DOES NOT: no L1 (genie ceiling only); single-code block≠S2c group; headroom 4.31 bits so any blind disclosure fails gate (b); single seed-block run, no multi-seed replication; no S3/qualification/publication/route decision.
## 6. Process / scope hygiene — PASS
- OBR-2 (non-blocking): measured RSS 167/166 MB cited in RESULT but absent from manifests (cap only). No live campaign process (`ps` clean); no frozen-dir writes.
- This review **authorizes nothing**: no S3, no real-data work, no rerun, no commit/push.
