# fix-candidate-loss-namespace

**已批准（2026-08-25 用户裁决 Q1–Q4 后解除 DRAFT）。决策记录：**
**Q1** = 16dB 共享 56 格一并复验（重物化+重跑受影响点）；
**Q2** = 方案 A（10dB、6dB 各全网格 121 格重物化）；
**Q3** = 残余共享池三目录隔离改名 `real_sequences_quarantined_20260825`（在 T5.3 执行）；
**Q4** = 新输出采纳增量命名 `*_lossfix_v1`。

## Why

2026-08-25 取证确认（`results/paper_grade_v4_rate_search_fix/DATA_PROVENANCE_INCIDENT_20260825.md`）：
候选序列物化层使用**无损失命名空间**的共享池
（`results/real_sequences/d{d}_bw{bw}/blk0`，2026-03-18 物化；池已基本删除），
导致 16/10/6dB 三档共用同一物理输入：

- 10∩16：56 格字节级相同
- 6∩16：56 格字节级相同
- 6∩10：40 格字节级相同
- 6dB 受影响并集 ≈ 61 格；20dB 干净（独立 t15 物化，0 共享）

跨损失档候选输入并非独立样本 ⇒ 任何 10/6dB 跨损失对比不成立，
v4 长跑已被用户授权终止。修复对象是**候选数据物化层**
（命名空间设计），不是运行参数或流程逻辑。

## What

1. 为候选序列池引入**按损失源命名空间**的布局（key = 源ttbin标签 × d × bw）。
2. 用仍在仓内的原始提取工具链，从四档原始 ttbin 重新物化受影响档的候选序列。
3. 建立自检门：确定性复现锚点 + 跨档字节唯一性 + map_sanity/档位序校验 + 溯源指纹。
4. 在新命名空间上重跑 10dB、6dB，并按 Q1 复验 16dB 共享 56 格，完成验证与收尾。

## Feasibility Verdict（只读调查结论）

| 档 | 判定 | 关键证据 |
|---|---|---|
| 20dB | 不需要重建（干净档） | 事件记录 §3；t15 独立物化 |
| 16dB | **rebuildable** | 原始 `Type2_5s_16dB_2026-01-30_224900.ttbin` 存在 |
| 10dB | **rebuildable** | 原始 `Type2_5s_10dB_2026-01-30_224808.ttbin` 存在 |
| 6dB | **rebuildable** | 原始 `Type2_5s_6dB_2026-01-30_224719.ttbin` 存在 |

原始数据根：`D:\Data\Raw Data\QKD_Loss\TypeII_776.1nm_3s\`（即 WSL `$PROJECT_DATA_ROOT/Raw Data/QKD_Loss/TypeII_776.1nm_3s`），
四个记录目录及主 .ttbin 文件（含 `.1.ttbin` 分片）均已逐一验证存在。

## Scope

**In scope**
- `src/workflow/export_joint_sequence_sidecar.py`：仅加一个可选 pool-root 参数（默认行为不变）
- `experiments/run_e2e_pipeline.py`：仅加对应透传 CLI 旗标
- 新增：按损失命名空间的物化驱动脚本 + 自检脚本（放 `tools/` 新文件，不动既有逻辑）
- 新输出目录：新候选目录（增量命名）+ 新序列池根
- 重跑产物：`four_loss_parts_frames300` 的后继目录（新名，不覆盖旧证据）

**Out of scope**
- 冻结基线其余逻辑（Polar 解码、安全分析、finite-key 公式）
- 已保留的事件证据目录（267 文件）与 `loss_6dB` 空骨架 —— 只读
- `results/paper_grade_v3/` 旧基线 —— 只读参考
- research-line 工作（AGENTS.md §0 边界）

## Affected Specs

- 新增 capability：`candidate-materialization`（命名空间布局、自检门、失败处置）
- 无既有 spec 需修改（本次为缺陷修复 + 新约束）

## Decision Items —— 已全部裁决（2026-08-25，见顶部决策记录）

1. ~~16dB 共享 56 格是否复验~~ → **复验**（Q1）
2. ~~重建范围~~ → **方案 A：全网格 121 格/档**（Q2）
3. ~~残余共享池处置~~ → **隔离改名**（Q3，T5.3 执行）
4. ~~输出命名~~ → ***_lossfix_v1 增量命名**（Q4）
