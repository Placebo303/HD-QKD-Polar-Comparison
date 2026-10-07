# Z-3 INDEPENDENT ACCEPTANCE（主线程接受记录）

- Pre-RESULT 独立审查 **PASS**（R13 全对合：A-exact ∧ B-exact ∧ d=512 重建；
  E_L/f 逐行重算一致；跳过有理由；曲面映射按格分类）。
- 主线程接受本 DECIDE 结果（ceiling 内）：曲面 12 已测 / 18 未测（按类标注）；
  代表点 (512,400)×{4dB 0/7（单数 UNDECIDED），0dB 0/16}，合并 23/23 为跨 p
  混合一致性（pooled-consistency），f≈1.26–1.27 为零失败名义值，效率界来自合成。
- R13：逐块 a_ok/exact_full/undetected/L_A/L_B/extra；und 隔离。
- Ceiling：新点一致性 only；不估 FER（Wilson 0.354/0.194 为界非估计）；
  不推广出测试格。
- 证据链：Z3_PREEXECUTE.md → z3_surface.json + blocks_z3.jsonl（23 块）→
  z3_summary.json → 本接受记录。
