# S-5 INDEPENDENT ACCEPTANCE（主线程接受记录）

- Pre-RESULT 独立审查 **PASS**（R13：exact_full 蕴含 u2-exact 且五面全对；
  undetected 隔离且作用域明确；E_L/f 逐行重算一致；一致带 verdict 逐源记录；
  G-1 分项记录；ceiling 完整）。
- 主线程接受本 DECIDE 结果（ceiling 内）：
  首个真实全符号 NB 数（f 1.915/1.787/1.647，und 0），标注"已用数据再检验"；
  G-1 未通过（点门 miss，valid-wrong met）——G-1 门本身是否过严不在本批裁决，
  如实记录供后续路线参考。
- 已知 caveat：`_real_one` rok_u2 rescue 路径收窄（本次 nu=0 无影响），下次真实运行前修。
- 证据链：S5_PREEXECUTE.md（附条件授权+双条件核验+检查单）→ blocks_s5_*.jsonl
  （875超帧逐块）→ s5_nb_summary.json → S5_RESULT.md → 本接受记录。
  审查结论与主线程接受一致，无分歧保留。
