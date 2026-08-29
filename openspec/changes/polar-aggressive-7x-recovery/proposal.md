# Proposal: polar-aggressive-7x-recovery

**状态：已批准（2026-08-27 用户按推荐全部批准 Q1–Q8）。本文档为执行依据，决策记录见 §8。**

## 1. Goal

在 `fix-candidate-loss-namespace` 完成后的干净 lossfix 命名空间之上，以**激进但可控**的路径恢复并超越因码率搜索保守性与定时劣化导致的 PIE 损失，目标**全网格平均 PIE 提升约 7× 语义的恢复**（以 6/10/16/20dB 全 121 格的 `PIE_reconciled_net` / `SKR_reconciled_net_bps` 为主口径，以实测为准，不承诺固定倍数数值）。

核心抓手按优先级排序：

1. **C1 上游定时校准**（锚定/死时/窗口）—— 抬 IAB 上限，属源头增益；
2. **C2 解码器升级**（信道自适应冻结序 Tal-Vardy→GA + SCL 升级 + 块长评估）—— 抬 β/逼近容量；
3. **C3 层丢弃记账**（负净收益层丢弃）—— 统计已验证 +29.1% SKR 增益的落地。

## 2. Why

- `docs/decision-log.md 2026-08-14` 量化：细阶梯+300 帧仅回收 0.01–0.03 bits/bit/层，主 gap 0.14–0.20 来自 PW 固定序 + SCL-4 + n=4096 的解码能力上限；负净收益层未丢弃导致 92 点被压零。
- `AGENT_PROJECT_MEMORY.md 2026-08-26` 诊断：档间 ser 差异主因为速率相关定时劣化（死时/堆积/时间游走），100% 错误为 ±1 邻 bin 穿越，窄 bin 阈值式位移；`pairing_v2` 的 auto-peak 重锚定（~100ps 粒度）与物理劣化不可分，属上游白捡收益洼地。
- `fix-candidate-loss-namespace` 已重建 lossfix 新池并通过跨档唯一性门，但 PIE 仍需激进策略恢复；`polar-mainline` 边界要求 Polar 基线语义稳定，故以**增量命名空间**承载激进探索。

## 3. What

本变更交付（均在 `_aggressive_v1` 增量命名空间内）：

- **C1a 固定锚试点**：固定 `used_delay_ps`（禁用 auto-peak 漂移重锚定），在 8 格锚点 `d=4096 × bw∈{40,200} × 4 档` 上立即启动对比，度量 IAB/ser 收窄程度。
- **C1b 死时校准**：立项死时校准表 `calibration_table`（per-tier/per-rate 参数化死时/堆积/游走校正），授权新建独立序列池（不复用 lossfix 池），抽 12 格独立验证。
- **C1c 窗口/帧锚网格寻优**：有效配对窗口 `effective_pairing_window_ps` 与帧起始锚的网格搜索，结合层丢弃阈值寻优。
- **C2 解码器**：分步 Tal-Vardy 轻版先行 → 全 GA 信道自适应冻结序；SCL 从 4 升至 16 并丢弃 L10/11（Q4）；块长 n=4096→8192 可选评估。
- **门与落盘**：新增 `G_growth` 增长门（按 explore 报告阈值），全部产物落 `_aggressive_v1` 三目录隔离。
- **C1/C2 衔接**：C1 增益先行度量，再叠加 C2，避免收益混淆。

## 4. Scope

**In scope**

- 新增 `tools/` 驱动脚本与校准表（`calibration_table.json/yaml`）、锚定/窗口搜索驱动、`_aggressive_v1` 专用 wrapper；仅通过 `pool_root / delay_override / calibration_table` 三参数透传触碰冻结基线（design §3）。
- 新序列池根 `results/real_sequences_aggressive_v1/` 与新候选/重跑输出根（design §2/§5）。
- 自检门扩展：`G_growth`（增长门）、`G_timing`（定时一致性）、原 `G0–G4` 复用。
- 16dB d=2048 离群点的标注与隔离分析（Q8）。

**Out of scope**

- 冻结基线其余逻辑（Polar SC/SCL 内核、安全有限长公式、finite-key 审计表生成）—— 除 design §3 最小透传外不动。
- `results/paper_grade_v3/`、`results/authoritative/`、`results/paper_grade_v4_rate_search_fix/` 既有产物 —— 只读。
- `fix-candidate-loss-namespace` 事件证据与 `results/real_sequences_quarantined_20260825` —— 只读。
- research-line 方向（nonbinary LDPC / formal IR / qLDPC）—— 归属 sibling 仓库（AGENTS.md §0）。
- 不改 `comparison_bench/` 的 Polar 语义；comparison 仅作只读桥接。

## 5. Non-Goals

- 不承诺固定 7× 数值口径；以实测 `PIE_reconciled_net` 分布与审计表为准。
- 不在 8 格试点完成前启动全量 121 格重跑。
- 不引入 SHA-256 完整性清单等重型防御（AGENTS.md §5.7），以 Git 基线 + 字节比对为准。
- 不覆盖任何 `results/` 既有输出；全部增量命名。

## 6. Impact Scope

| 域 | 文件/模块 | 影响 |
|---|---|---|
| 冻结基线透传 | `src/workflow/export_joint_sequence_sidecar.py` | 增 `pool_root`, `delay_override`, `calibration_table` 可选参数（默认行为不变） |
| 冻结基线透传 | `experiments/run_e2e_pipeline.py` | 增对应 CLI 旗标透传 |
| 新增工具 | `tools/materialize_aggressive_candidates.py`, `tools/verify_aggressive_gates.py`, `tools/build_calibration_table.py` | 新文件，不改旧工具 |
| 新数据根 | `results/real_sequences_aggressive_v1/` | 新增独立池（三目录隔离之一） |
| 新候选根 | `results/authoritative_aggressive_v1/` | 新增候选目录（三目录隔离之二） |
| 新重跑根 | `results/paper_grade_aggressive_v1/` | 新增重跑产物（三目录隔离之三） |
| 文档 | `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md` | 仅在 T5 收尾追加条目 |

## 7. Affected Specs

- 新增 capability：`aggressive-timing-calibration`（C1a/C1b/C1c 定时校准、锚定策略、窗口寻优）
- 新增 capability：`adaptive-polar-freezing`（C2 Tal-Vardy/GA 自适应冻结序、SCL16、块长）
- 新增 capability：`aggressive-growth-gate`（G_growth 门、层丢弃阈值、离群标注）
- 无既有 spec 需原地修改（增量命名空间隔离）

## 8. Acceptance Criteria（分阶段门）

- **T0**：`compileall` + import 通过；默认参数等价断言 + 守卫 tamper 通过；`explore_report.md` 与 `gates_frozen.json` 冻结；reviewer-go T0 PASS；data-lock/code-lock 落盘。
- **T1**：8 格固定锚物化完成且 `sidecar_meta.json` 含 `delay_override`；`G_timing`/`G0–G4` 全 PASS；`G_growth` 8 格初筛按冻结阈值判定 PASS 后方可进 T2；含 reviewer-go + 冻结点。
- **T2**：`calibration_table_aggressive_v1.json` 落盘且 schema 校验通过；12 格带表物化完成；`G_growth` 12 格复筛 PASS；含 reviewer-go + 冻结点。
- **T3**：窗口/锚网格搜索与层丢弃掩码落盘且增益分解表可归因；`G_growth` 终筛 PASS；含 reviewer-go + 冻结点。
- **T4**：Tal-Vardy 轻版 → 全 GA 分步可复现；SCL16+L10/11 丢弃与块长评估产物齐全；`G_growth` C2 分解 PASS 或标记 `non_promoted`；含 reviewer-go + 冻结点。
- **T5**：484 格全量物化+门全 PASS+全链重跑 validator 121/121；`old_vs_new` 484 行对比表与离群单独章节完成；reviewer-go 终审 PASS + memory triage + `/finish-change` 可归档判定。

## 9. 决策记录 Q1–Q8（2026-08-27 用户全部按推荐批准）

| 决策项 | 选项与推荐 | 用户裁决 | 含义 |
|---|---|---|---|
| **Q1 C1a 启动** | A. C1a 8 格固定锚试点立即启动（4096×{40,200}×4档） | **A 已批准** | 固定 `used_delay_ps` 禁用 auto-peak，8 格锚点先行度量档间 ser 差收窄 |
| **Q2 C1b 立项** | A. 立项 C1b 死时校准并授权新池 | **A 已批准** | 新建 `calibration_table` + 独立池 `real_sequences_aggressive_v1/` |
| **Q3 C2 路径** | A→B 分步: Tal-Vardy 轻版先行再全 GA | **A→B 已批准** | 先轻量化 Tal-Vardy 验证增益，再推进全 GA 自适应冻结序 |
| **Q4 SCL 策略** | A. SCL16 + 丢弃 L10/11 | **A 已批准** | SCL 4→16，丢弃净负层 L10/11（4K 维度最高两层） |
| **Q5 命名** | A. 增量命名 `_aggressive_v1` | **A 已批准** | 全部新产物后缀 `_aggressive_v1`，三目录隔离 |
| **Q6 门阈值** | 按 `explore` 报告建议 | **已批准** | `G_growth` 等阈值以 explore 阶段报告为准（design §4） |
| **Q7 基线触碰** | A. 允许触冻结基线但需独立 OpenSpec+review-go 三阶 | **A 已批准** | 仅 pool_root/delay_override/calibration_table 三参数透传，需独立 review-go 三阶审查 |
| **Q8 离群处理** | A. 16dB d2048 离群标注 | **A 已批准** | 16dB d=2048 异常点标注隔离，不纳入均值门统计，单独分析 |

> 约束回声：Q7 的“允许触碰”以 design §3 最小透传清单为边界，任何超出清单的冻结基线改动需另起 OpenSpec 并重走 review-go 三阶；Q6 阈值细节在 design §4 冻结后 T1 前完成 explore 报告落盘。
