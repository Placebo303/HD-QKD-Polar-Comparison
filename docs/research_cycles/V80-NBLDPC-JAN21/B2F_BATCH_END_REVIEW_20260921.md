# B2F Batch-End Review (2026-09-21) — EXPLORE §10.3; reviewer-go taste (step-5-preview); read-only, no patches, no run

Verdict: PASS. Batch evidence MAY be promoted as EXPLORE synthetic gate-(a) decodability evidence under the flatter Bayes-marginal L2 prior. Genie retirement is NOT established: the two-construct-seed replication (fresh construct seed, e.g. F208) remains MANDATORY before any genie-retirement wording; this batch authorizes nothing toward S3/real-data/qualification/publication.

Independent re-verification (recomputed from artifacts; the result doc was not trusted):
1. Gates: F208 fails 0/240 FER 0.000, 240 success; F202 6/240 FER 0.025 at idx 29/37/85/97/202/233 = seeds 2026095630/5638/5686/5698/5803/5834, all max_iter_reached @300, converged=False, quarters 2/2/2/0. Gate (a) ≤12 both PASS. Gate (b) recomputed (5m+64)/852.54422 = 1.2949475 (F208) / 1.2597587 (F202) ≤ 1.3 — accounting identity (FXR-3); manifest matches to 6+ dp.
2. Ledger/pins: rows 240 = decodes 240 = blocks_completed 240 both arms; manifest pins n1024, m208/m202, fc0, rank=m, girth8 (recorded), peg-irregular, sockets2048, parity0, construct 2026092001/trials20, λ{2:1} — match packet Q3. rows.json ↔ block_accounting.csv field-identical (0 mismatches incl. u1_source MARGINAL, d_u1 0.0, leak 1104.0/1074.0); group_accounting.csv byte-identical (md5 identity, O1R precedent); leak sums 264960/257760.
3. Seeds/provenance: all block seeds = 2026095601+idx both arms (paired O1R/P0/L1B/b2e); no re-seed; thresholds unchanged (bar 12, iter 300/streak 3, caps 300 s/3600 s/4 GiB). Order OK: F208 started 15:29:05Z (.start) and exited 0 before F202 launch 15:41:26Z; elapsed at F202 launch 12.4–12.7 min ≤ 50; no arm swap.
4. Budget: /usr/bin/time walls 672.55 s / 1346.90 s ≤ 3600; max RSS 173,680/173,816 KB ≈ 170 MiB ≪ 4 GiB; exit status 0; zero `--resume-from`, 1 window each, continuations_used=0, no auto-relaunch; max decode 74.07 s < 300 s.
5. Claim ceiling: FXR-1 honored (≈852.5 ≈ H_full·n, ~26 b/block flatter than genie 826.266; "must NOT be read as entropy parity"); D-u1=0.0 structural; u1_mismatches 8.083/17 report-only; no genie-retirement wording; no L1-code/FER-route/S3/real-data/qualification/publication claim; no cross-arm pooling; paired seeds → no independence claim; synthetic only.
6. Scope: git status = only the new untracked result doc (plus pre-existing unrelated .codebuddy/); git diff on frozen o1/s2c/l1b/b2e/v28/fftqspa EMPTY; roots gitignored under workspace/; results/ and comparison_bench/outputs_comparison/ untouched; no commit/push.

Findings (all non-blocking):
- BFR-1: doc quotes F208 start 15:28:44Z vs .start artifact 15:29:05Z (21 s); ordering/≤50-min conclusions hold either way — cite the artifact.
- BFR-2: manifest F208 arm_role carries packet §3's "genie retires…" budget-relevance phrasing; not a claim, but add a one-line guard against misreading.
- BFR-3: result doc never states "b2e falsified only the hard-argmax commitment" explicitly (cross-ref only) — suggest one clause.
- BFR-4: FXR-1 mislabeled-anchor lesson is a reusable failure mode → docs/troubleshooting.md candidate (deferred).

Checklist:
- [x] Matches frozen packet (arms/gates/seeds/thresholds)
- [x] Artifacts independently re-verified
- [x] No scope creep; frozen modules untouched
- [ ] troubleshooting/decision-log update (BFR-4, deferred)
- [ ] Two-construct-seed replication remains REQUIRED before genie-retirement wording
