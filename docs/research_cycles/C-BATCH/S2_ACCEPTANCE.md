# S-2 独立 Pre-RESULT 验收（2026-10-09，独立线程）

> 独立审查线程结论逐字转录（只读审查，未写任何文件；主线程仅转录）。

S-2 DECIDE zero-decode H(A|B) Pre-RESULT review complete (read-only,
branch formal-ir-v72p1-addendum-clean). All five items PASS; overall
PRE_RESULT_REVIEW_PASS, no blocking reason. Evidence summary:
(R-a) command module+flags+root identical to frozen S2_PREEXECUTE §3,
wall_s_total 1206.3s ≤ 7200s, fresh-root guard at msd_s2_softmap.py:179-181,
root created 2026-10-09 with exactly 3 files.
(R-b) T2-1M bw200 0.8039/0.3891/0.2406/0.2405 identical across
RESULT/summary/csv/rows.jsonl; prefix fits (T2-1M -48.0/13.34/0.0069;
10dB -45.0/11.86/0.0076) match; CIs T2-1M Hs_cal [0.2322,0.2489] and
10dB Hh_uncal [0.7747,0.7969] match; n_pairs-n_test=10000 on all 8;
8/8 ok, 24 rows, no blocked; T0-1.5M/2M out of scope per Pre-EXECUTE §1
(B123-blocked carryover); undetected/FER/leakage/f absent except correct
absence declarations.
(R-c) descriptive H table + CIs, model cols labeled reference only, no
FER/efficiency/route claims, soft-calibration-independence as measured
equality (diff ≤0.002), decoder deferred to S-3.
(R-d) no forbidden wording (only absence self-declaration), mu as prediction
parameter per S1 §5, git diff --stat src/experiments/tools empty, new files
untracked-additive only.
(R-e) 0.02-0.05 soft underprediction recorded as reference gap, estimator
frozen and implemented verbatim with prefix-only fitting.

Overall: **PRE_RESULT_REVIEW_PASS**

主线程接受：S-2 可 solidify（RESULT 已落盘，不再改动）。
