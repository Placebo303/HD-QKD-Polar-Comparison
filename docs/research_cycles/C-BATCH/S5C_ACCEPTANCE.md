# S-5c 独立 Pre-RESULT 验收（2026-10-10，独立线程 + 聚焦复审）

> 独立审查线程结论逐字转录（只读审查，未写任何文件；主线程仅转录）。
> 初审：R-a PASS，R-b FAIL，R-c FAIL，R-d PASS，R-e PASS。
> 返工后聚焦复审：RE_REVIEW_PASS（下）→ 总体 **PRE_RESULT_REVIEW_PASS**。

初审原文要点：
- R-a: PASS — smoke→full 链、用户确认引用、full 2040.6 s ≤7200 s、
  1.26×639×1.5≈1204 预算、fresh 根、639 连续块行、每格一次。
- R-b: FAIL — `s5c_cells.json` 内表误用 S-3 bug 端点（三重 AND，全膨胀），
  与 RESULT 声明的 S-4d-hard-okA 端点矛盾；块行缺 undetected 列。
- R-c: FAIL — RESULT §2 "首次回到 1 附近"字面违反 R17。
- R-d: PASS — 冻结零 diff；冻结配置与验证一致；未 push。
- R-e: PASS — smoke 墙钟缺口、McNemar 修正、A3 手术均自声明。

返工：
1. 新补充文件 `s5c_mcnemar.json`（加法；落盘表不动）：GF5-exact vs
   S-4d-hard-okA，分源 17/14/11/4/0，pooled 46/0，p=2.842170943040401e-14
   （=2⁻⁴⁵；复审员纠正：主线程 prompt 笔误写成 2/2^42，文件与 RESULT 数值正确）。
2. RESULT 措辞改为"回到 1 附近"，引用补充文件并宣布落盘内表作废；
   脚本内同段加注（不重跑）。

聚焦复审原文：
RE_REVIEW_PASS — (1) s5c_mcnemar.json 方法与数值吻合（pooled 46/0
p≈2.8e-14）；s5c_cells.json 未动（仍存作废膨胀表）；(2) RESULT 引用补充文件，
f_ref 无"首次"，(?i)first 零命中（除 L54 自声明行）；(3) 脚本 POST-LANDING
FIX 注释在位，未重跑，无新机器根。

主线程接受：S-5c 可 solidify（RESULT 已落盘，不再改动）。
注：块行缺逐块 exact（schema 局限）与 undetected 列缺失（U=0/639 故无信息损失）
均已记录；McNemar 主判据用落盘时 exact 门控表。
