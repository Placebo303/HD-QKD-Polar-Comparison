# S-3 独立 Pre-RESULT 验收（2026-10-09，独立线程）

> 独立审查线程结论逐字转录（只读审查，未写任何文件；主线程仅转录）。

PRE-RESULT REVIEW — S-3 DECIDE real-decode (branch formal-ir-v72p1-addendum-clean, read-only):

- R-a: PASS — chain smoke→tune→tune-sup→full matches frozen §3+§8 (roots s3_smoke_20261009b/s3_tune_20261009/s3_20261009; mtimes 17:01<17:53<17:58<18:25 on 2026-10-09); wall_s_total 1644.8 ≤ 14400 cap; smoke 161s vs 120s overrun disclosed RESULT §5; fresh-root guard script L638-639, tune-sup additive-only (L625-634, writes solely s3_tune_sup.json L387).
- R-b: PASS — 1278 block rows = 639×2; U=0 in all 10 cells (recomputed) and smoke; okA soft 639/639 vs hard 592/639 recomputed from rows with per-source hard fails 15+14+12+6+0=47 exact; okB 0/1231 given okA; wasted-L sums recomputed exact (645001/950490/1329088/327108/143640); in-file mcnemar {} empty with post-hoc-from-rows honestly disclosed; no f_hard/f_soft keys anywhere (S-1 rule respected).
- R-c: PASS — full-chain negative (10 cells S=0) + level-A positive (47/0, p≈1.4e-14) each at its granularity; S-4 as proposal only ("新包另立,本批不执行"); sole banned-word hit is the self-declared-absence line; μ only as prediction parameter.
- R-d: PASS — `git diff --stat -- src/ experiments/ tools/` empty (only M docs pre-execute + additive untracked script/test/RESULT); R16 per-arm opt N=4096 by per-bit net (hard 7.64>6.10>2.82, soft 7.73>5.16>4.54 recomputable from landed Net_seg) + T_med secondary stated; gap-tie→min-disclosure and frac-tie→smaller-frac stated and code-matching (L440-463, sup table); embedded tune == landed tune (opt N 4096/4096, frac 0.1, no overrides key).
- R-e: PASS — all failures retained in RESULT §5 and code-verified: inversion bug + regression test test_exact_full_success_easy_point; grid.append present L413; QA=5 L29; B=20 L418-420; smoke overrun; mcnemar key-bug verified (lookup ka=`src/hard/N` vs cell keys `hard/N` → perpetual miss → {}); N-reselection by arithmetic without touching landed tune.
- §7 confirmation: PLAUSIBLE — RESULT cites user 2026-10-09 "可以开始s3" matching §7 request; dates/branch consistent (chat not visible to reviewer).

Overall: **PRE_RESULT_REVIEW_PASS** (no blocking reason).

主线程接受：S-3 可 solidify（RESULT 已落盘，不再改动）。
注：S-3 执行发生在 S 批批末审查之后，故适用 DECIDE Pre-RESULT 门（本验收），
不再另开第二次批末审查（S 批"只审查一次"约束维持）。
