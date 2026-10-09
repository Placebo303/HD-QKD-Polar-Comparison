# 现在只用软件就能做的工作（2026-10-09）

> 文档类别：任务包（documentation-only，本身不授权执行）。
> 上位：AGENTS.md、R1–R16、`docs/C_BATCH_PREREG_20261008.md`、`docs/research_cycles/C-BATCH/C_BATCH_ARBITRATION_20261009.md`。
> 论文定位已调整为**以实测为主**（见 §0）。新采集要等 `C4_PLAN.md` 采集规范定稿，本包不包含新采集。

## 0. 定位调整（写入预注册）
- 暂定标题：*Measured, not assumed: information reconciliation for arrival-time HD-QKD on real SPDC data*。
- 主张全部落在"测量"上：
  1. 真实信道测量；
  2. 用**标准码**测得的协调成本；
  3. 理论预测与实测的对照；
  4. 给实验者的实践建议。
- **不声称**：新码、"首次"、"理论错了"。
- **时延不对称的正确解读**：标准抖动模型加上残余时延偏移 μ，就能在一阶上定量解释观测结果，即 p ≈ E|Δ|/bw；未校准时约为 |μ|/bw，误差方向由 μ 的符号决定。偏移最可能来自旧对准流程的分辨率（100 ps 直方图取 bin 中心），属于流程量化误差，不是理论缺陷。
- 可能真正需要补充理论模型的，是**实测抖动形状与高斯的偏差**：σ≈25 ps 时，校准后预测 p≈0.10，实测为 0.06；C-2 的 κ 比也落在带外。这一点待 B1 确认。

## A. 纯软件，不读原始数据（可立即执行，属于 EXPLORE 或实现类）
| 编号 | 内容 | 交付 |
|---|---|---|
| A1 | 按 §0 修订 C 批预注册的 §0、§1、§7。文献换成已核对的 DOI（见 §D）。新增 R17（措辞：不写"首次"，不写"理论错误"，偏移按 μ 项解读） | 预注册修订版 |
| A2 | **对准代码审计**（只读，不改冻结基线）：在 `src/qkd_io/ttbin_pipeline.py:219-249` 及 R1/M0 对准路径里，确认偏移估计的直方图分辨率，以及取 bin 中心还是峰值插值。再用合成时间戳（已知 μ、σ）复现"粗直方图对准 → 残差约 ±50 ps"，并核对符号约定 | 审计记录 + 复现脚本 |
| A3 | **偏移 + 抖动的解析模型**：对任意 Δ 分布（高斯、高斯 + 均匀、双高斯）给出 p₊、p₋、H(e) 的闭式或数值式；用已落盘的 Z-2 / C-0 / C-2 统计拟合，产出对照表（未校准 p 与 p₋、校准后 p、p 随 1/bw 的缩放、残差） | 模型模块 + 对照表 |
| A4 | **仲裁遗留项**：D7 多种子（< 10 min）、D5 分母复算、D6 相同时间口径重算；撤回"T2 三源是累计前缀"的判断（三段独立采集，见 `docs/archive/v80/DATA_INVENTORY_20260921.md:22-24`）；ε_EC 以预注册为准，纳入；PAPER_DRAFT 的 [TODO-LIT] 用 §D 回填 | 修正记录 |
| A5 | **理论速率预测工具**：输入实测 Δ 分布，按 Birnie 等 / Boutros & Soljanin 的口径，计算 hard 与 soft 两种可达协调速率；用他们论文里的参数复现其结果作为自检 | 工具 + 自检 |
| A6 | **软时间信息译码接口**：两级二元链的第一级改为接受逐符号 LLR（由 Bob 在 bin 内的精细位置算出）；在合成高斯信道上验证 soft 相对 hard 的增益方向与 Boutros & Soljanin 一致。只做实现和合成验证 | 代码 + 测试 |
| A7 | **采集规范定稿**：run sheet 和段级 manifest 字段（光源类型 / 分路方式 / 滤波、两路 singles、符合率、VOA 设置及所在路、泵浦、时长、采前时延校准值、文件路径）；矩阵为光源 × singles × VOA，每点在不同时间各采 2 段；T0 复现检查；偶然符合背景段；**必须保留 ps 级原始时间戳**；长段分子段检查漂移 | `C4_PLAN.md` 修订 |

## B. 读已存原始数据，零解码（DECIDE：先写 Pre-EXECUTE，经用户确认后执行，事后做独立 Pre-RESULT）
| 编号 | 内容 |
|---|---|
| B1 | **原始时间差 Δ 分布**：对每段采集，在 ps 分辨率下画出 Δ 直方图；拟合高斯、高斯 + 均匀、双高斯，报告尾部形状；把每段按时间分 3 个子段估计 μ，检查漂移 |
| B2 | **软信息增益的上限**：经验估计 H(A \| B 的 bin) 与 H(A \| B 的精细时间)，以及两者之差（bit/符号），在 bw ∈ {100, 200, 400} ps 上各做一次 |
| B3 | **光源类型预试验（C-0b）**：2026-01-20 Type-0 nofilter（500K / 1M / 1.5M / 2M）与 2026-01-21 Type-II（1M / 1.5M / 2M），统计校准后的 p、误差支撑、估算的 CAR 和 H(A\|B) 分解 |

输出写到新的 `workspace/` 根；只统计，不生成密钥，不解码。

## C. 顺序
- 第一轮：A1、A2、A3、A4、A7 并行。
- 第二轮：B1–B3 在 Pre-EXECUTE 获用户确认后执行。
- 第三轮：A5、A6 视 B2 的增益决定；若 B2 显示软信息增益可以忽略，A6 只保留为负结果。
- 批末：一次独立审查 → scoped 提交，不 push。

## D. 已核对的文献（DOI 来自检索结果）
- Boutros & Soljanin, IEEE TCOM 2023 — 10.1109/tcomm.2023.3302135；arXiv 2301.00486
- Birnie, Cheng, Soljanin, IEEE TCOM 2023 — 10.1109/tcomm.2023.3244244；arXiv 2207.04146
- Brougham, Wildfeuer, Barnett, Gauthier, EPJ D 2016 — 10.1140/epjd/e2016-70357-4；arXiv 1506.04420
- Yang, Sarihan, Chang, Wong, Dolecek, Asilomar 2019 — 10.1109/ieeeconf44664.2019.9048898；arXiv 2001.00611
- Zhong et al., New J. Phys. 2015 — 10.1088/1367-2630/17/2/022002
- Liu et al., Appl. Phys. Lett. 2019 — 10.1063/1.5089784
- Mueller et al., Quantum Inf. Process. 2024 — 10.1007/s11128-024-04395-w
- Dolecek & Soljanin, IEEE BITS 2023（综述）— 10.1109/mbits.2023.3262237
- Morozov et al., IEEE Access 2025 — 10.1109/access.2025.3648803
- Kanitschar & Huber, Phys. Rev. Applied 2025（DOI 待核）
