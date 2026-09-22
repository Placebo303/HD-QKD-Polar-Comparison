# B2E Batch-End Review (2026-09-21) — EXPLORE_HEAVY synthetic batch, ONE record

- Independently reviewed `B2E_RESULT_20260921.md` against the frozen packet+Amendment, `B2E_PREEXEC_20260921.md`, `B2E_EXECUTOR_REVIEW_20260921.md`, and roots `workspace/b2e_799c2d57` (B202) + `workspace/b2e_681b442d` (B208) — manifest.json, rows.json, block_accounting.csv, `/tmp/opencode/b2e_B{202,208}.{log,time}`. Read-only: no edits, no run, no switch/commit/push. Branch `formal-ir-v72p1-addendum-clean`.

## Verdict: PASS_WITH_FINDINGS — all findings non-blocking; batch evidence promotable

## 1. Gates recomputed from artifacts — CONFIRMED
- 13/13 fails both arms; every row `exact_match=False`, `status=max_iter_reached`, `iterations=300`. Last row = block 12 / seed 2026095613 = the 13th fail ⇒ terminal early-stop at bar+1; `partial=true`, `next_block=13`, `continuations_used=0`.
- Gate (a): 13 fails > 12 ⇒ FAIL both arms (definitive — fails are monotone; the remaining 227 blocks cannot rescue it).
- Gate (b) recomputed from rows.json: B202 (1074+26.187875)/852.544 = 1.290476 ≤ 1.3 PASS; B208 (1104+26.187875)/852.544 = 1.325665 > 1.3 FAIL. Arm verdicts B202 FAIL(a), B208 FAIL(a+b) — match result doc and both manifests.
- d_u1 stats reproduced exactly (mean 26.1879 / p50 25.1404 / p90 32.9515 / p99 37.2748 / max 37.7247); u1_mismatches mean 7.6923 / max 13; du0 (1.259759 / 1.294947) and 5×k sensitivity (1.304873 / 1.340061) match; per-block >1.3 counts 1 (B202) / 13 (B208) match.
- Budgets interior: wall 963 s / 922 s < 3600; max RSS 167,928 / 167,680 KB ≈ 164 MB ≪ 4 GiB; per-decode 72.8–76.8 s (B202) / 69.7–71.9 s (B208), all ≤ 300 s; exit 0; 1 wall window each; no INCOMPLETE-wall; no `--resume-from` in either command line.

## 2. Evidence consistency — CONFIRMED
- rows.json == block_accounting.csv on every shared field (both arms); log summaries == manifests on every carried key; result-doc tables == manifests == rows.
- d_u1 and u1_mismatches byte-identical across arms on all 13 paired seeds 2026095601–5613 ⇒ pairing (same (b,u1) marginal) confirmed as recorded; no independence claim made.
- Executor + test file byte-identical to reviewed commit 050644c6; `test_v80_b2e_campaign.py` → 38 passed (15.7 s); frozen o1/s2c/l1b untouched (`git diff` empty); exactly 2 `workspace/b2e_*` roots; `results/` + `outputs_comparison/` untouched; no result-artifact commit.

## 3. Adaptive-order record — CONFIRMED
- B202 first, B208 second; B202 reached a terminal verdict and elapsed at B208 launch ≈ 19.5 min ≤ 50 min ⇒ skip rule correctly NOT triggered. No arm swap/substitution: exactly the two frozen arms, one invocation each, n-blocks/seeds/thresholds unchanged.

## 4. Claim ceiling
- Supported: replacing genie-u1 by MAP-û1 makes the L2 decode fail on every tested block (13/13 both arms, all at 300 iterations, status max_iter_reached) ⇒ the cheap-estimator path is falsified under this machinery; gate (b) readings as computed (B202 1.2905 PASS / B208 1.3257 FAIL). Attribution to the MAP substitution (rather than a pre-existing L2 decodability limit) rests on the paired genie arms O1R/P0/L1B on the same frames — pairing recorded, no independence claim.
- NOT supported / not claimed: no L1-code-necessity proof (only that THIS estimator fails here); no u1-repair-mechanism conclusion; no genie retirement; no S3; no FER/route/threshold/real-data/qualification/publication claim; no cross-arm pooling. BXR-01 materialized as ~70–77 s/block but gate (a) fired first — no budget verdict.
- Failure mode is non-convergence (300 iters, max_iter_reached), not converged-to-wrong-codeword; the result doc records this faithfully.

## 5. Authorization — CONFIRMED
- Standing pre-authorization 2026-09-20/21; Amendment recorded pre-run (annotate-only; supersedes only the §4 gating reading); one invocation per arm; no rerun, no tuning, no resume. This review authorizes NOTHING, grants no execution, and triggers no S3 / auto-proceed.

## Findings (all non-blocking)
- **BER-01** (precision): the executor divides by `CONTENT_BITS = 1024×H_FULL_O1 = 852.54422528`, while the frozen packet/Amendment and result-doc prose state the literal `852.544`. Offset ≈ 3.4e-7 on every f_super value; verdict-neutral for both arms (B202 1.2904760 vs 1.2904764; B208 1.3256648 vs 1.3256652). Manifest arithmetic is internally consistent (arm-mean = mean of per-block values at constant leak_bits). Recommend docs and executor agree on the constant before any claim-bearing reuse.
- **BER-02** (process): execution order deviated from the packet §2 nominal PRIMARY-first labels (B208 PRIMARY); B202 ran first as a recorded main-thread adaptation within the frozen set. Gate-neutral (§5 per-arm AND, no pooling) — order cannot change either verdict.
- **BER-03** (phrasing): result doc states gate (a) as "13/13 > 12" while the gate is `fails/240 ≤ 12` (absolute count). The count reading is correct and definitive under terminal early-stop; suggest "13 fails of 240 planned" in future records.
- **BER-04** (trivial): result doc says measured gate-(b) means "match" the Amendment pre-registered observations (≈1.2906 / ≈1.3258); measured 1.2904760 / 1.3256648 differ by ~1.2–1.4e-4 (measured mean d_u1 26.1879 below the 1024×H_L1 anchor 26.2779). Covered by the ≈ notation; immaterial.

## Checklist
- [x] Gates recomputed from artifacts and match
- [x] Evidence consistent (result doc == manifests == rows == CSVs == logs)
- [x] Budgets interior; no INCOMPLETE-wall; 0 continuations; no reruns
- [x] No scope creep (2 frozen arms, 2 fresh roots, frozen modules untouched, forbidden trees untouched)
- [x] Tests pass (38 new; frozen modules untouched)
- [ ] decision-log / troubleshooting update: not required — no durable decision, no new failure mode; BER-01 is a main-thread item only if the constant is ever amended.
