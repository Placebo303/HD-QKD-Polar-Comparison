# S-2 EXPLORE packet — 稳健先验：TRAIN内CV选型 + S-1代理验证（草案，G-0后冻结执行）

> Track: **EXPLORE**。授权：持续推进（S-2在内）。结果根：`workspace/s2_prior/`（待建）。
> 前置：G-0 通过（代理可信），否则本包不执行。

## 候选（R10下比较，零译码选型）
1. 平移不变差分 PMF `P(b|a)=g(b−a)` + 均匀背景（隔壁 diff_pmf α=1先例）。
2. 参数化：抖动高斯/拉普拉斯 + 意外符合背景。
3. 加概率下限的 plug-in（floor 网格，如 1e-4/1e-3/1e-2）。

## 选型（零译码）
在 TRAIN 内交叉验证：按 frame 分 fold，用 held-out 对数似然 + 校准误差
（分桶预测vs经验）挑。输出：选定先验族 + 参数 + CV证据。

## 验证（S-1代理，G-0配置）
选定先验在 S-1 Tier1/Tier2 上重调 MSD（m_0按先验h重定 + K rescue重调）：
目标 N=16384 f ≤ 1.30、valid-wrong=0，且候选间结论稳定（ top-2 先验差距 < MDE）。
NB臂用同一先验重跑（u1残错对比）。

## MDE/预算
CV零译码（分钟级）；代理验证沿用 S-1 B（MSD 100/NB 60）；上限 21600 s。
成功：代理上复现消失（MSD plane-1失败率回到genie量级）+ valid-wrong=0。
