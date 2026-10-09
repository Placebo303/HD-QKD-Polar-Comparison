# S-4a 独立 Pre-RESULT 验收（2026-10-09，独立线程）

> 独立审查线程结论逐字转录（只读审查，未写任何文件；主线程仅转录）。

S-4a Pre-RESULT review (read-only, branch formal-ir-v72p1-addendum-clean):

- R-a: PASS — module+args identical to S4A_PREEXECUTE §3 frozen command; wall_s_total=1373.5s ≤7200s (s4a_summary.json); fresh-root guard at msd_s4a_signdiag.py:142-145; output root holds exactly 3 files (s4a_summary.json, s4a_rows.jsonl, s4a_table.csv).
- R-b: PASS — T2-1M bw200 cal agree 0.6093==sgn 0.60929 (JSON/csv/rows/RESULT); G1=recon=1.0 in all 48 cells; block rows T2-1M 248.6/220/245/286/298, T2-1.5M max 345, T2-2M max 398 (<410); 8/8 cal agree==sgn within 0.002; 49-line CSV carries per-source×bw cal+uncal columns; RESULT §4 records voided uncal-mu synth + mu_cal recompute via same analyze() with marked-rate match; §5 declares no FER/leakage/net-key, f not computed.
- R-c: PASS — flip fork REFUTED (agree==sgn, not <<50%), mappings exact (48/48 G1=recon=1.0), third fork taken with code/accounting attribution + fine-conditioned-prior fix direction; S-curve values are measured (match JSON sgn_by_fine); no decode/efficiency/route claims (§5 ceiling statement).
- R-d: PASS — no 'first'/'theory-wrong'/new-code language (sole 'FER' hit is the §5 absence declaration); mu framed only as prediction parameter (§5); `git diff --stat -- src/ experiments/ tools/` empty via pwsh.
- R-e: PASS — true-marked ee!=0, guess b1^a0^1, 8 sub-bins, N_BLK=4096, bootstrap seed 20261011/cap 30000 all verbatim vs Pre-EXECUTE; S-2 wording fix not scored per instruction.

Overall: **PRE_RESULT_REVIEW_PASS** (no blocking reason).

主线程接受：S-4a 可 solidify（RESULT 已落盘，不再改动）。
