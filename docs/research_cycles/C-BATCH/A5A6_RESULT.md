# A5/A6 第三轮结果（B2 门控 PASS，2026-10-09）

> 门判定（`B123_PREEXECUTE.md` §5，`B123_RESULT.md` §B2）：主要 bw=200 ps 上
> G≈0.49–0.58 bit/符号（8/8 源；CI 半宽 ≤0.006；最小 n=30907），阈值
> max(0.02, 3%·H(A|B))≈0.024 → 超阈值约 20 倍。→ **做 A5 和 A6**。
> 设计见 `A5A6_PACKET.md`。均为实现 + 合成验证，无真实解码。

## A5 理论速率预测工具

- 文件：`comparison_bench/src/comparison_bench/formal_ir/msd_a5_soft_rate.py`
  （新建，加法）；测试 `comparison_bench/tests/test_a5_soft_rate.py`（4 passed）。
- 口径：hard = SW 界 H(A|B_bin)；soft = H(A|B_fine) = E[H(e|v)]（8 子 bin，
  与 B2 同口径）；P(e=k|v) 由抖动 CDF 给出（A5 文件头注）。
- 自检（合成）：μ=0 对称 P₊₁=P₋₁；全网格 soft≤hard；σ≫bw 时增益→0（<0.01）；
  校准窄抖动增益方向为正（>0.2）；B2 经验交叉（T2-1M 标称）：
  混合律下 R_hard=0.8099 vs 0.8040（±0.01 内）、R_soft=0.2618 vs 0.2407（±0.03 内）。
- 重要发现：纯高斯低估软增益（R_soft=0.324 vs 0.241），B1 混合律闭合大部分差距
  ——同一"形状非高斯"线索的第三次出现（A3 κ、C-2 p 0.10/0.06、B1 尾、B2 交叉）。
- 速率表（`workspace/swnow_20261009/a5_20261009/a5_rates.json`，12 行)：
  校准后（μ=0）增益：bw100 ≈0.24、bw200 ≈0.20、bw400 ≈0.15（混合律）；
  即使校准后仍远超 0.02 阈值。
- 未声称：论文原参数逐数复现（两文完整工作点不在仓内；工具实现其口径，
  自检为闭式 + 经验交叉，见文件头注 R9）。

## A6 软时间信息译码接口

- 文件：`comparison_bench/src/comparison_bench/formal_ir/msd_a6_soft_llr.py`
  （新建，加法）。第一级接受逐符号 LLR（Bob 按 bin 内精细位置 + Δ 分布算出）；
  标准 RA 系综实例（n=512, m=256, q=3，种子 7；与 G-5 同构造）；
  `ldpc.BpOsdDecoder`（product_sum，serial，max_iter=50，OSD_CS order=1），两臂同码同参。
- 合成验证（校准点：σ=25, μ=0, bw=200, p_model≈0.099；B=200 配对块，种子 20261009；
  `workspace/swnow_20261009/a6_20261009/a6_result.json`，墙钟 2.6 s）：
  - hard FER = **0.845**，soft FER = **0.01**；
  - 配对：both_ok=31，hard_only=0，soft_only=**167**，both_fail=2；
    McNemar 精确 p≈0（167/0 全向 soft）。
- 方向与 Boutros & Soljanin 一致（soft 所需披露不超过 hard，同 FER 下；
  此处同披露下 soft FER 低两个数量级）。 smoke 曾发现 FER 标签笔误（已修正，
  同日志保留）。
- 上限：只做实现和合成验证；真实数据验证不在本轮范围（R17：只写测到的东西）。

## 第三轮结论

B2 门 PASS → A5（有用）+ A6（正结果）均完成。软时间信息的经验增益、
理论界增益、译码增益三向一致（~0.5 / ~0.2 / FER 0.845→0.01）。
