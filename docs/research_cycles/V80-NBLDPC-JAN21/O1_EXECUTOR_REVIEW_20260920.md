# O1 Executor Review (2026-09-20) — EXPLORE, code-only, no run
- Track EXPLORE synthetic. Branch `formal-ir-v72p1-addendum-clean` (no switch/commit/push). Scope: 3 new files only (v80_o1_campaign.py, test_v80_o1_campaign.py, O1_PREEXEC_20260920.md); frozen diff empty (s2c/v10_peg/v28/v26_mcde/s2_peg); `ls workspace/o1_*` none — zero decodes here.
- Verdict: PASS_WITH_FINDINGS (non-blocking only). Focused tests rerun: 32 passed in 6.04 s.
- E1: ARMS pins fc0/g8/rank-full both arms; construct-twice-identical; STOP-BLOCKED on mismatch (packet §2). E2/E3: s2c helpers reused read-only (bundle/sampler/rows/center); own (n,m) block decode; y=b&31; GENIE-u1 ceiling label; `decode_error_domain_posterior` only (bare-name grep clean); (n,m) wiring guard.
- E4: block seeds literal 2026095501+idx; stream `o1_blk:` distinct from `s2c_emp:`; rg `20260955` clean outside O1 files. E5: block = acceptance unit (`exact_match is True`); fails/60<=3 AND f_super<=1.3 (1.177652/1.294947 recomputed match); early-stop at 4th fail; A208 blind-risk line present.
- E6/E7: checkpoint-per-block; <=1 wall-partial resume (2nd refuses, zero decodes); caps 3600/300 s/4 GiB; dual-flag gate; `--de-precheck` A208-only frozen MC-DE point (S1-CONFIRM conv), refuses if record exists, label defaults exploratory.
- O1R-1 (non-blocking): no 1-block dry decode yet (Pre-EXEC Q5 transparent); operator runs one per grant — first window measures per-decode wall/iters (packet §7).
- O1R-2 (non-blocking): tree carries unrelated untracked/modified files (other workstreams); O1 scope itself clean — keep run root fresh, sweep nothing in.
- Statement: the two-arm run may proceed under standing pre-authorization; this review authorizes nothing itself.
