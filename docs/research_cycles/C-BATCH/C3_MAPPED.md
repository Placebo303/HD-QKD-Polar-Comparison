# C-3 映射参考表（主线程，只读已落盘行；跨 regime 参考，非 OPT 竞争）

> 推导脚本：`docs/research_cycles/C-BATCH/c3_mapped_derive.py`（R5）。
> 口径：`net_of_cell`（均匀格）+ 同公式逐块求和（非均匀格，已交叉验证一致）；
> kept = N·H_A（原材料，披露只在净项扣一次——初版双扣已修正，见脚本注释）；
> H_A=9.9976919099，H_AB=0.7981344445（T2-1M 标量；D-4 行 1.5366 复算吻合故同标量适用）；
> C_total = B·N（w_tail=0 假设）；跨 fresh/mapped 比较用 f_full + Net_per_used
> （mini 的 Net_per_coin 用规划 5M 作分母，口径不同，不可直比）。
> 证据类型分列（R1§6）：synthetic / real-clean-OOS / real-retest。

## 主表（p=0.24 与 NB 旧 regime 的参考行；F1/F2 校准点行待 fresh 矩阵）

| 行 | 方法 | 证据 | B×N | F/U | Net_seg (bit) | Net_per_used (bit/符合) | f_full | FER | β(附带) |
|---|---|---|---|---|---|---|---|---|---|
| G-5 RA-q5-gap0.08 m3.0 | A1 | synthetic (p=0.24) | 300×32768 | 0/0 | 89338610.55 | 9.0880 | 1.1397810138 | 0 | 0.988 |
| G-5 polar-SCL8-0.88 m3.0 | A2 | synthetic (p=0.24) | 300×32768 | 0/0 | 89250410.55 | 9.0790 | 1.1510224382 | 0 | 0.987 |
| F-1 4dB-diff | A6 | real-clean-OOS | 112×1024 | 0/0 | 1020647.29 | 8.8993 | 1.3761513517 | 0 | 0.967 |
| D-4 0dB-diff | A6 | real-retest | 260×1024 | 0/0 | 2335265.49 | 8.7713 | 1.5365985870 | 0 | 0.953 |
| A5 | — | 缺席（无块行；仅 three_way_compare 摘要数） | — | — | — | — | — | — | — |
| A7 | — | unavailable | — | — | — | — | — | — | — |

> FER 显示豁免注（C4 落定）：本表四行历史冻结证据的 FER 显示维持点估计 0
> （PAPER_NUMBERS §3–§4/§11 已载其 Wilson 上界：0/300→0.0126、0/112→0.033、
> 0/260→0.0146），不再改写为「未定」——改写历史冻结数的显示无信息增益，
> 上界已在源头冻结。C-3 新鲜格仍一律执行「未定」规则。

## 校准前参考隔离声明（M4 落定，C6）
- 本表四行均为**校准前工作点**（p≈0.24 二元 / p≈0.12–0.26 NB 旧 regime）的证据，
  只作 regime 变迁的参照锚点。
- **不得与 C-3/M 波校准点行并列排序或比较优劣**（p_op 不同，kept 基数不同，
  f 分母不同）；论文中引用须标注"pre-calibration reference"。
- 校准点的无结构对照（A6/A5 在 p* 处）不存在——缺口如实记录，禁声不断言。

f 交叉：G-5 两行与 PAPER_NUMBERS §1–§2 十位小数一致；F-1 与 §4 精确一致；
D-4 与 §11 差 6.9e-11（均值 vs 逐块求和的显示舍入）。

## 更正记录（C3_LOG.md §0 事实修正）
- C3_LOG.md 称"历史行摘要 JSON 缺位（workspace 无 G-5/Z-1/Z-3/F-1/S-5/D-4 摘要 JSON）"**不属实**：
  `workspace/g5_bakeoff/g5_20261008/g5_summary.json`、
  `workspace/f1_oos/f1_20261007/f1_summary.json`、
  `workspace/d4_oos/d4_20261007/d4_summary.json` 及三份块行 JSONL 均存在且可读
  （本表即由其逐块映射得出，f 与冻结数十位一致为证）。
- 处置：mapped 参考职责由主线程接管（本表）；full 操作员继续 fresh 矩阵，
  其 LOG 该句以本更正为准（不要求重跑；批末审查备案）。
- Z-1/Z-3 行未入本表（N=16384 backbone 为 f(p) 曲线非净密钥口径，
  跨表需另行对齐，不在本批范围）。

## Claim 上限
本表只提供跨 regime 参考锚点；任何"校准点上某方法更优"的结论须待 fresh
F1/F2 OPT 行（mini/full）落定，fresh/mapped 永不混排。
