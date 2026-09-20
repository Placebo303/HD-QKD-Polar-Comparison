# P0 Batch-End Review (2026-09-20) — EXPLORE independent

- Track EXPLORE synthetic; branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push; no execution).
- Scope: P0_RESULT + packet (§7) + PREEXEC + EXECUTOR_REVIEW + L1 memo + roots `workspace/p0_7a5c39e8` (A202) + `workspace/p0_a237aa12` (A200).
- Verdict: **PASS_WITH_FINDINGS** (A202 PASS, A200 PASS; 2 non-blocking findings; no blockers).

## 1. Gates recomputed (per-arm standalone, AND)
- A202: 0/240 FER 0.0 ≤12 ✓; 1074/852.54422528=1.25976 ≤1.3 ✓; quarters 0/0/0/0 (4/4 ≤3) ✓ → PASS.
- A200: 2/240 FER 0.008333 ≤12 ✓; 1064/852.54422528=1.24803 ≤1.3 ✓; quarters 1/0/0/1 (4/4 ≤3) ✓ → PASS.
- Budgets: 1 window/arm (cap 3600 s); 0 resumes/arm (max 1 WALL-PARTIAL, unused); per-decode max 54.1/76.1 s <300 ✓; RSS ~163 MiB <4 GiB.
- P0BR-01 (non-blocking): A200 elapsed 930.1 s exceeds packet §6 ≈900 s/arm estimate; interior to 3600 s window; estimate, not an AND-gate — no breach.

## 2. Evidence consistency (result == manifests == rows == CSVs)
- rows↔CSV 240/240 exact both arms (block/seed/exact_match/iterations); group CSVs byte-identical (O1R precedent).
- Seeds 2026095601–5840 both arms (paired O1R reuse; no-independence note in manifests); A200 fails idx 42 (…643) + 202 (…803), 300 iters `max_iter_reached`.
- Pins fc=0/girth 8/rank-full (202/200) + twice-identical gated; girth recorded-not-gated (R2 precedent) — matches dry pins.
- P0BR-02 (non-blocking): result-doc wall 765/937 s vs manifest elapsed 759.6/930.1 s (~1% source delta); both interior; manifest elapsed is canonical.

## 3. Interpretation rule §7 honored
- Result §7 quotes packet verbatim: A202 PASS ⇒ L1 MAY proceed with m2≤202; A200 PASS ⇒ m1=8 option alive; pooling FORBIDDEN; P0 authorizes nothing. No auto-proceed executed.

## 4. Retained failures / history
- A200 2 fails retained+labelled (rows+CSV+manifest+result agree); no rerun/tuning/resume; partial=false; o1*/o1r* roots untouched; `results/`/`outputs_comparison/` clean.

## 5. Claim ceiling (nothing beyond)
- "At n=1024/λ={2:1}/genie-u1/empirical-2M/D_blind=0, L2-only block FER meets gates at m2=202 (0.0) and m2=200 (0.00833) on O1R-paired frames; steep margin A188 fail↔A208 pass↔202/200 pass."
- NOT: no L1/threshold/combined chain; synthetic only; single-code block≠S2c-group; no S3/qualification/publication/route; per-arm only; P0↔O1R non-independent.

- No process remains; no frozen-dir writes. **Authorizes nothing / no S3; L1 build remains a main-thread decision.**
