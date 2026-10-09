# B123 独立 Pre-RESULT 验收（2026-10-09，独立线程）

> 独立审查线程结论逐字转录（只读审查，未写任何文件；主线程仅转录，不改写 verdict）。

- R-a: PASS — module+args identical (interpreter path alias only); wall_s_total 2209.1s ≤ 7200s; script refuses existing roots (msd_b123_stats.py L308-311).
- R-b: PASS — spot-checks match (T2-1M bw200 G=0.804−0.2407=0.5633 CI [0.5562,0.5704]; B3 T2-1M cal p=0.06074 = C0_RESULT §1; T0 scans minimize at −50); 8 ok + 2 blocked (T0-1.5M/2M blocked_low_peak_to_bg, no fallback L350-355); no FER/leakage/undetected keys.
- R-c: PASS — descriptive-only ceiling kept (gain as empirical upper bound, A5 rates deferred, no FER/efficiency/route claims); gate max(0.02,3%×H)≈0.024 vs min lower bound 0.4810, A5+A6 correct (~20×).
- R-d: PASS — no 'first'/'theory-wrong' claim in B123_RESULT.md (only self-declaration meta-mention); git diff --stat -- src/ experiments/ tools/ empty (only additive untracked wrappers).
- R-e: PASS — T2-1M 525949 vs Z-2 525831 (+118, 0.02%) explicitly recorded with C-0 cross-check 525949 exact.

Overall: **PRE_RESULT_REVIEW_PASS**

主线程接受：B123 可 solidify（RESULT 已落盘，不再改动）。
