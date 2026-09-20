# O1R Batch-End Review (2026-09-20) — EXPLORE independent, authorizes NOTHING

- Verdict: PASS (both arms; no blocking issues; 1 non-blocking note).
- Scope: O1R replication batch only — R1 workspace/o1r_732dea76, R2
  workspace/o1r_793ce1d8. Standing pre-authorization; amendment recorded
  pre-run; nothing else executed. This review authorizes nothing / no S3.
- [ORBR-1] Gates recomputed from artifacts ✓ (both arms): fails 0/240 ≤ 12;
  FER 0.0; f_super 1104/852.54422528 = 1.294947 ≤ 1.3; quarters 0/0/0/0
  (le3 4/4); ledger 240/240; rows 240, CSV 240, 0 fails; verdict PASS each.
  Budgets interior: wall 548.0/561.9 s ≤ 3600; per-decode cap 300 s unhit;
  RSS < 4 GiB per result doc; 1 window/arm; 0 continuations; no early-stop.
- [ORBR-2] Evidence consistency ✓: result doc == manifests == rows == CSVs
  spot-checked (blk0 R1 it7/R2 it9, seed 2026095601, leak 1104, f_super
  1.294947, D_blind 0.0). Seeds gapless 2026095601+idx 0..239, paired
  R1↔R2 (same seed ⇒ same triple, o1_blk: domain). Pins: R1 fc0/girth8/
  rank208; R2 fc0/girth6-recorded-not-gated/rank208, Amendment cited in
  manifest ✓. Iters distributions match result doc both arms.
- [ORBR-3] Retained failures ✓: none new (0 fails both arms); prior O1
  history (A188 FAIL) untouched; no deviations — no relaunch incidents,
  no resumes, no second continuations, partial=false, exit paths clean.
- [ORBR-4] (non-blocking) RSS figures (~165 MB) live in result doc only,
  not manifests; wall/RSS both interior so no gate impact. Suggest adding
  RSS to manifest at next executor touch; no action required.
- Claim ceiling — SUPPORTS: "A208 PASS replicates: pooled 0/480 across two
  construction instances (girth 8 and 6) with paired frames, gates met in
  both arms." Does NOT: no L1 (genie-u1 D1 ceiling = upper bound); synthetic
  only; single-code block semantics; D_blind=0 with 4.31-bit headroom (any
  blind disclosure fails gate b); girth-6 carried as unexplained covariate;
  no multi-construction-family generalization; no S3/qualification/
  publication/route decision.
- Authorization boundary ✓: standing pre-authorization per amendment review;
  amendment recorded pre-run (R2 girth recorded-not-gated, seeds
  pre-committed ⇒ no tuning); Q6 commands run verbatim; no other execution.
