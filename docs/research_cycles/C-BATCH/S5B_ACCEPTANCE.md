# S-5b 独立 Pre-RESULT 验收（2026-10-09，独立线程）

> 独立审查线程结论逐字转录（只读审查，未写任何文件；主线程仅转录）。

PRE-RESULT review S-5b (DECIDE zero-decode, read-only):
- R-a PASS: command `msd_s5b_udef --full --output-root workspace/s5_udef/s5b_20261009`
  == frozen PREEXECUTE §3; wall_s_total 1155.8s ≤3600s; fresh-root guard
  `if root.exists(): raise SystemExit` (msd_s5b_udef.py L75-76);
  branch formal-ir-v72p1-addendum-clean, root new with exactly 3 files.
- R-b PASS: T2-1M 1.33e-5/blocks_wide 7/pred 6.8/landed 7 identical in RESULT
  table/s5b_summary.json/s5b_rows.jsonl/s5b_table.csv; T2-2M 4.99e-5/44/48.9/44
  and 0dB 2.25e-5/5/5.9/5 match; 5/5 blocks_wide==landed_U exact with pred
  within ±50%, narrow G1=recon=1.0 all 5 sources; 5-key per-source breakdown;
  summary grep null for undetected/FER/leakage/net/f and RESULT §3 declares
  them absent/uncomputed; GF(5)/prior_g reasoning only in RESULT §2(ii),
  absent from script.
- R-c PASS: RESULT stays at U≡wide-block + wide rates, cites m3 synthetic scan
  but defers joint selection to S-5a; §3 declares no decode/FER/leakage/net —
  matches PREEXECUTE §6 ceiling.
- R-d PASS: RESULT §3 R17 `μ 只作口径注释，无新码/首次`;
  `git diff --stat -- src/ experiments/ tools/` empty via pwsh.
- R-e PASS: script verbatim — symmetric fold, |e|>=2, N=4096 chunks,
  exact beta.ppf CI, S4D_U+C0_TAIL constants; alignment-blocked path, self-test.

Overall: **PRE_RESULT_REVIEW_PASS**

主线程接受：S-5b 可 solidify（RESULT 已落盘，不再改动）。
注：本验收覆盖零解码诊断部分；S-5a/S-5b 修法合成验证（调优中）适用批末审查。
