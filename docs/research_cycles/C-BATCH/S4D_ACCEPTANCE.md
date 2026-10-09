# S-4d 独立 Pre-RESULT 验收（2026-10-09，独立线程 + 聚焦复审）

> 独立审查线程结论逐字转录（只读审查，未写任何文件；主线程仅转录）。
> 初审：R-a PASS，R-b FAIL，R-c PASS，R-d PASS，R-e PASS。
> 返工后聚焦复审：RE_REVIEW_PASS（下）→ 总体 **PRE_RESULT_REVIEW_PASS**。

初审原文（5 项）：
- R-a: PASS — mtime 链 GE→门→smoke→full 与冻结一致；full 4067.3 s ≤14400 s；
  fresh 根；被杀根缺席且 §5 记录替代执行。
- R-b: FAIL — RESULT §3 pooled McNemar 行（46/0，p≈4e-28）与落盘表矛盾
  （分源求和 42/0；解码端点复算 46/0 系另一端点；p≈4e-28 系跨臂 double-count）。
- R-c: PASS — 再检验标注、无泛化、S-4c defer、机制陈述、μ 参数化；
  `第一个真实全链`判为内部事实里程碑（R17 但书允许，非发表新颖性主张）。
- R-d: PASS — 冻结零 diff；S-3 文件 diff 仅 _block_once 两处变量修复 + 注释，
  无阈值/种子/码率改动；未 push。
- R-e: PASS — 被杀运行、U 异常、schema 局限、修复与回归测试、N 选择均保留记录。

返工：RESULT §3 改为 exact 门控分臂 pooled 42/0、p≈4.5e-13（不跨臂合并），
并注明解码端点 46/0 与作废的 92/0。

聚焦复审原文：
RE_REVIEW_PASS: (1) s4d_cells.json mcnemar 分源 soft_only plain=[16,11,11,4,0]，
fixed 相同，hard_only 全 0，分臂求和 42/0；(2) 精确双侧 McNemar 2/2^42≈4.5e-13，
而 2/2^92≈4e-28 证实 4e-28 系作废的 92/0 double-count；(3) RESULT §3
59–65 行（16/0、11/0、11/0、4/0、0/0 两臂相同，分臂 pooled 42/0 p≈4.5e-13，
不跨臂合并，外加 46/0 说明与作废的 92/0）全部吻合；(4) 抽查 T2-1M
soft/plain S=121 Net=4674591 与 JSON 及 RESULT 表一致。

主线程接受：S-4d 可 solidify（RESULT 已落盘，不再改动）。
