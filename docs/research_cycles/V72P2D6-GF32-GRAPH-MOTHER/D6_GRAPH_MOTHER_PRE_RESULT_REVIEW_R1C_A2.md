# D6 Graph Mother Pre-RESULT Review R1c-A2 (independent, read-only)

Status: PRE_RESULT_REVIEW_R1C_A2
Branch: formal-ir-v72p1-addendum-clean
HEAD: 047e6d6232ff87c56eebd2af71a454d5494c1735
Out-root: workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b
Revision: R1c-A2
Reviewer: reviewer-go (independent, read-only)
Date-UTC: 2026-09-09
Scope: D6 R1c-A2 section-8 new root E2/E3/E4/E5. No decoder execution, no phase execution, no edits except this file.

## Verdict

Verdict: D6_R1C_A2_PRE_RESULT_REVIEW_FAIL

FAIL blocks solidification. No repair, no rerun, no new decoder calls, no result acceptance. Fix requires OpenSpec/verify amendment and new explicit authorization, not silent pass.

## E2 execution (EXITED, development-only)

- E2 done line: terminal D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY, calls 184, setup 18, wall 8349.6, peak_rss 88764416. Matches manifest.json and summary.json and command_log.txt tail.
- Outer wall about 8355 s from 12:58:37 to 15:17:52 local, inner wall 8349.6445 s, delta about 5 s startup. Consistent.
- Process 34468 exited/reaped at re-check, stderr 0 bytes, no traceback. Single runner invocation only.
- Budgets: scientific 184, setup 18, total 202, all at or below 2500. Wall below 43200. Per-call max about 3.65 s below 120. No retry/respawn evidence in this stage.

## E3 revocation (recovered)

- Revoke commit 047e6d62 restores development_decoder_authorized true to false, single-file change on cycle_state.yaml. Verified via git show.
- Current cycle_state.yaml: development_decoder_authorized false, all other execution keys false, scientific_promotion false, g2_execution_authorized false, evidence_root null, terminal null. Authorization consumed, no residual true flag.

## E4 verify (exit 1, honestly reported, unrepaired)

- Verifier call exactly once without model-f-root and without workers: python scripts/v72p2d6_graph_mother_development.py --out-root workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b --verify, exit 1, VERIFY FAIL.
- Operator return reports 13 checks ok and 2 fails, literal and unrepaired: semantic-key-no-dup n=184, scaling-recompute with advancing empty list. This matches prereg A2-07 any-FAIL-means-VERIFY-FAIL rule.
- No verify rerun, no manual cell replay, no parameter change after verify. True/false list in operator return claims retry/rerun/resume/second-root/code-change/phase/formal-G1/G2/P0/VAL/real/VOID-read/push all false. No contrary evidence in six files.

## E5 checklist (read-only recomputation from six files)

1. UUID fresh and single:
   - Root workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b is the only workspace/d6_graph_mother_r1c star entry. No second r1c root. UUID dd8c4defe67742a8b2bc1b634c116d6b differs from three VOID names. Result: ok.

2. No VOID and no formal reuse:
   - Three VOID roots exist (existence-only True/True/True), contents never opened/hashed/compared by this review. Code grep history shows zero VOID hits in implementation. Out-root refuses overwrite and requires explicit out-root. No formal-root writes evidenced. Result: ok.

3. Arms, seeds, rows, decoder, prior:
   - Arms: 8 in structure (B0/B1/T1-T4/M1/M2), selected 5 (B0/B1/T1/T3/M1). Rows: n64 L1 49/59/64 and L2 43/52/64, x2 for n128 (98/118/128 and 86/104/128), x4 for n256 (196/236/256 and 172/208/256). Matches prereg. Seeds: canary 2026091000-1003, scaling 2026091100-1103, confirmation 2026091010-1025 empty because advancing empty so no confirmation dispatch. Seed-domain check ok in verifier. Decoder: cold max_iter 90, damping 1.0, warm None, L1 to APP-L2 plus oracle-diagnostic-only per records (L1/L2-APP/L2-oracle modes only). Prior: command_log prior E2 identity counts 1024/1024 and LAMBDA_STAR 137.3823795883264, CAL-only. Result: ok.

4. setup/scientific at or below 2500:
   - decoder_records.csv 184 rows, call_idx 1 to 184 continuous. summary calls 184, manifest scientific 184, setup 18, total 202. 202 below 2500. Verifier calls-consistent and le-2500 ok. Result: ok.

5. 43200 and 120s, no retry, PID and respawn:
   - Wall 8349.6 below 43200. Chunk walls 3.176/3.003/7.190 all below 5400, chunk_wall_blocked false. Per-record timeout false, wall_timeout false, watchdog_ok true for all 184, wall_s max about 3.65 below 120. worker_pid present on all counted rows, 18 distinct pids, respawn_pid empty, no respawn, no retry. Verifier timeout-watchdog and pid-present ok. Result: ok.

6. Request 18, effective 18, aggregate below 2GiB:
   - Requested 18, effective 18, no downscale. main 112836608, 18 worker rss each about 88 MB, aggregate 1697669120 below 2147483648. Peak single 118226944, peak aggregate 1711198208, run peak 88764416. Semantics string fail-closed-strict-unknown-None-no-zero-substitution-no-single-as-aggregate. No zero substitution, no single-as-aggregate. rss_block_terminal null. Verifier rss-strict and effective-le-requested ok. Result: ok.

7. crash/nonfinite/syndrome/exact separation, no oracle promotion:
   - Exact true 40, syndrome true 40, disagreements 0. Crash true 64 (T3/M1 ValueError Check node requires degree ge 2), nonfinite 64, iterations -1 for those, finite false. Exact true only where syndrome true and finite true and crash false. Oracle true never upgrades L1/APP exact: same cell L1/APP remain false while oracle true in many T1 cases. manifest and summary oracle_never_upgrades_exact true. confirmation_safety zeros reflect empty confirmation stage, not decoder stage, as operator return notes. Result: ok.

8. Blind selection and terminal recomputation:
   - selected_arms.json freeze decoder-blind-from-structure-only, eligible true 6 (B0/B1/M1/T1/T3/T4) false 2 (M2/T2), selected 5, fallbacks best_T T1 and best_M M1, structural_order_new T1/M1/T3. Canary f12_exact all 0, f12_iter B0/B1/T1 720 else 0, sq_exact 0, advancing empty, confirmation_counts empty, confirmation_width 64, terminal D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY. Verifier terminal-replay and coverage and manifest-consistent ok. Result: ok.

9. Six files, scalar, ordered, checkpoint and fsync:
   - Six files present with sizes and mtimes: command_log 3752, decoder_records 37937, manifest 2389, selected_arms 678, structure_records 11479, summary 1708. Scalar-only payload, deterministic order per verifier six-files ok. call_idx ordered rewrite 1..184. structure 144 rows (3 widths x 48) ordered by arm/n/layer/prefix. command_log flush rows 104/144/184 and structure checkpoints 96/144 present. Fsync fail-closed in code (reviewed, not re-executed). Result: ok.

10. Inner/outer wall and chunk semantics:
    - Inner 8349.6445, outer about 8355, delta startup. Structure-parallel walls 29.0/451.4/7845.0 dominate total, decoder chunks 3-7 s. chunk_wall_blocked false, no chunk over 5400, wall-budget verifier ok. Result: ok.

11. Verify result handling:
    - 13 ok plus 2 fails as above. Overall VERIFY FAIL. Per A2-07 any fail means VERIFY FAIL. Pre-RESULT must block. See Blocking Issues. Result: blocking fail.

12. Protected roots unchanged:
    - Model-F input names/sizes/mtime only: model_f_input_summary.json 752, model_f_input.npz 208467, 2026-09-07 02:07:07. Content not reread. VOID existence-only. No formal writes. Result: ok.

13. Authorization false:
    - Post-revoke false verified. No other true authorization. Result: ok.

14. G2 absent:
    - No D6 G2 artifact. Test-Path false for D6 G2 paths pre/post per operator return. Only unrelated V72P2D5 p0g1g2 roots exist. Result: ok.

15. CAL-only boundary:
    - No VAL/real/raw/parquet outside CAL-TRAIN, no phase/G1/G2, no n1024 formal, no qualification/promotion. Claim boundary CAL-only finite development evidence, not formal performance/FER/leakage/key-rate. Result: ok.

## Blocking Issues

- B1: verifier semantic-key-no-dup FAIL n=184. Verify code keys by arm/seed/point/mode without n. Scaling reuse of seeds 2026091100-1103 across n128 and n256 for same arm/point/mode inevitably duplicates (40 no-n duplicates by independent count; with-n keys 184 unique). Execution reuse matches frozen 4-seed scaling set, but verifier definition per prereg A2-07 item 3 rejects it. Any FAIL means VERIFY FAIL. Blocks solidification.
- B2: verifier scaling-recompute FAIL with advancing empty. by_cell keyed without n collapses widths and mixes scaling seeds into canary recomputation, so canary_re cannot match summary canary when scaling present. Same n-agnostic root cause as B1, plus width/canary mixing. Blocks solidification.
- Consequence: E6 result file must not be written, no acceptance, no promotion, no rerun/retry/resume/repair-run. New OpenSpec/verify amendment plus fresh explicit authorization required for any next run.

## Non-Blocking Suggestions

- Amend verify semantic key to include n (arm/n/seed/point/mode) or split canary vs scaling seed domains explicitly, and fix by_cell to key by n, with separate canary vs scaling recomputation. Record as OpenSpec delta, not silent code patch.
- Clarify scaling seed intent for two widths with only four seeds: either keep reuse and fix verifier, or provide eight distinct seeds. Do not reinterpret frozen seeds in review.
- Keep dirty unscoped worktree untouched; scoped cleanliness for this root is proven by single-root inventory and six-file evidence. Next packet should re-verify branch and scoped diffs before any new execution.
- Recommend human review for verifier-contract fix because it changes acceptance semantics.

## Checklist

- [x] Matches OpenSpec spec (R1c-A2 frozen science and mechanics ok, except verifier contract mismatch now exposed by FAIL)
- [x] Tests pass (prior implementation 32/32 and pre-execute ok; this review ran no tests and no decoder/phase per scope)
- [x] No scope creep (this file only, no code/param/result edits)
- [ ] docs/decision-log.md or docs/troubleshooting.md needs update? No update by this review; verifier-contract lesson should be recorded via OpenSpec amendment if owners accept, not here.

Reviewer did not edit code, did not execute decoder or phase, did not read VOID contents or formal roots beyond existence and names/sizes/mtime, did not touch G2/VAL/real/raw.