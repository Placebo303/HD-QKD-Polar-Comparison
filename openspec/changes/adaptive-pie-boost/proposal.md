# Proposal: adaptive-pie-boost

**状态：DRAFT — 骨架已落盘，待 T0 explore 冻结后进入 apply。归属 polar-mainline（AGENTS.md §0），不触 research-line。**

## 1. Goal

验证**算法自适应是否带来结果提升**：为每文件做轻量自适应择优（per-file 3 点 × 6 组合共 18 候选内选最优），随后**仅跑四组损耗（6/10/16/20dB）各自冻结基线最高 PIE 对应点位**与自适应最优做同点位对比，量化 ΔPIE / Δser / ΔSKR。结论以增量证据与对照表为准，不承诺固定倍数提升。

> 新增量后缀 `_adaptive_v1`，三目录物理隔离，留2核，并发 `workers=max(2,cpu-2)`。

## 2. Why

- **文件间异质性未被 per-tier 一刀切覆盖**：`polar-aggressive-7x-recovery` T1c per-tier 5 锚 sweep 与 `auto-ir-param-scan` 探索显示，40ps 为不敏感区下界、10ps 为细筛粒度，窄 bin 高维格对 `delay_override` 与 `window/anchor` 敏感度分化；per-tier 最优锚（T1c 全档 10ps）无法消化单文件的 `peak_center` 漂移与通量差异。
- **全量 121 格重跑成本高，需先在冻结基线最优点位上做最小对比**：四档最高 PIE 点位为已验证的“天花板对照”（四档 max 9.31/9.51/9.59/9.59，121/121 真值），在此 4 点上做 18 候选择优即可回答“自适应是否提升”，成本≈ 4×18 物化 + 4 次重跑，远低于 484 全量。
- **需算法化而非人工调参**：将 `auto_ir_scan.py` 的外层循环薄封装为可复现算法（枚举→物化→收集 ser/PIE→Wilson 区间→选优→回退），避免人工 per-point sweep。

不做此变更的后果：新文件仍沿用 per-tier 最优锚，窄 bin 格 IAB 损失无法自动回收；无算法化对比证据。

## 3. What

### 3.1 自适应算法：per-file 3 点 × 6 组合择优

| 维度 | 符号 | 候选集（初拟，T0 `gates_frozen.json` 冻结） | 备注 |
|---|---|---|---|
| 延时锚 | `delay_override` | 以 `pairing_v2` 的 `peak_center_ps` 为中心，3 点：`{center-Δ, center, center+Δ}`，Δ 初拟 40ps（窄 bin 可细化至 10ps，仅对敏感文件） | 复用 T1c 40ps 不敏感区先验 |
| 有效配对窗口 × 帧锚 | `window_ps × anchor` | 6 组合：`window_ps ∈ {35,40,45}ns × anchor ∈ {0, +offset}`（offset 由 explore 定量，初拟 20ps） | 3×2=6，覆盖阈值位移区间 |
| 合计 | — | **3 × 6 = 18 候选/文件** | 预算上限 18，留2核并行 |

- **目标函数**：主 `max PIE_reconciled_net`（审计表 `actual_ir_block_table.csv` 为准，扫描期以 `PIE_est` 代理）；辅 `min ser` 作窗口/锚粗筛诊断列，Wilson 95% CI（`n=n_eff_pairs`）判不敏感区重叠即等价。
- **选优与回退**：每文件 18 候选内 `PIE` 最优即 `per_file_opt`；若 18 候选全失败或无正增益则回退至 **per-tier 最优锚（T1c 10ps）**，记 `optimal_source=fallback_per_tier`，保证每文件必有可用参数。

### 3.2 对比口径：仅四组冻结基线最高 PIE 点位

- **输入**：四档冻结基线 `polar_e2e_results.csv` 中 `PIE_practical` 最大行对应的 `(d,bw,blk)` 点位各 1 个（6/10/16/20dB 共 4 点，来自 `results/paper_grade_aggressive_v1` 或 `authoritative` 的已验证真值，不重算）。
- **执行**：对该 4 点各自跑 18 候选自适应择优→以每文件最优点位重跑全链（`round1a → actual_ir → security`）落 `_adaptive_v1` 增量根→生成 `_adaptive_vs_frozen.csv`（4 行，列：`loss_db,d,bw,blk,PIE_frozen,PIE_adaptive,ΔPIE,ser_frozen,ser_adaptive,Δser,beta_frozen,beta_adaptive,optimal_params`）。
- **判定**：逐档 ΔPIE 披露，Wilson 区间不重叠视为显著；不设硬性“必须提升”门，结论如实记录（含负增益/不敏感）。

### 3.3 输入 → 输出

- 输入：4 点的 `ttbin (+.1 分片)` + 冻结基线对照 `polar_e2e_results.csv` 最高 PIE 行
- 输出：
  1. `per_file_scan_trace.csv`（4×18=72 行量级，每候选 `ser/PIE_est/leak/IAB/Wilson CI/runtime`）
  2. `per_file_optimal_params.csv/json`（4 行，每文件最优 + `objective_value/fallback_flag`）
  3. 增量 IR 产物（序列池/候选/sidecar + 重跑产物）落 `*_adaptive_v1`
  4. 对照表 `_adaptive_vs_frozen.csv`（4 行）+ 门报告

## 4. Scope

**In scope**
- 薄封装扫描器 `tools/auto_ir_scan.py` 复用/扩展（外层 3×6 枚举，留2核 ThreadPool，Numba 双指针共享排序复用，不新增冻结基线透传参数）
- 增量落盘 `*_adaptive_v1` 三目录隔离与守卫（`real_sequences_adaptive_v1` / `authoritative_adaptive_v1` / `paper_grade_adaptive_v1` 或聚合 `results/adaptive_v1/`，pool_root 必须含 `adaptive_v1` 子串）
- 门与证据：`G_adaptive`（ΔPIE 分布披露）、`G_budget`（≤18/文件）、复用 `G2/G3/G4` 污染/溯源门
- 仅 4 点对比的 pipeline 与验证脚本（`compare_adaptive_vs_frozen.py` 等）

**Out of scope**
- 冻结基线其余逻辑（Polar SC/SCL 内核、安全有限长公式、finite-key 审计生成）——除已批准的三参数透传（`pool_root/delay_override/calibration_table`）外不动
- `results/paper_grade_v3` / `results/authoritative` / `results/paper_grade_v4_rate_search_fix` / `*_lossfix_v1` / `*_aggressive_v1` 既有产物 —— 只读
- 全量 121 格×4 档重跑、SCL/块长/GA 等解码器升级（需另起 OpenSpec）
- research-line（nonbinary LDPC / formal IR / qLDPC）—— 归属 sibling 仓库（AGENTS.md §0）
- 不改 `comparison_bench/` Polar 语义；comparison 仅只读桥接

## 5. Non-Goals

- 不承诺自适应必带来固定倍数 PIE 提升；以实测 ΔPIE 分布与审计表为准，40ps 不敏感区可判定为“无增益亦无损”。
- 不在 T0 阈值/预算冻结前启动任何真实数据扫描。
- 不引入 SHA-256 完整性清单/原子写/备份回滚/文件锁等重型防御（AGENTS.md §5.7），以 Git 基线 + 字节比对 + 结构化校验为准。
- 不覆盖任何 `results/` 既有输出；全部增量命名。
- 不将扫描器做成通用超参优化框架；仅覆盖上述 3×6 轻量搜索。

## 6. 决策点 Q1–Q4（T0 explore 冻结，用户裁决）

| 决策项 | 选项 | 推荐 | 含义 |
|---|---|---|---|
| **Q1 搜索粒度** | A. 固定 40ps Δ × 3窗×2锚（18/文件）<br>B. 自适应：40ps 粗筛→10ps 细化 top2 邻域（≤22/文件） | **A 起步** | 4 点对比成本敏感，固定 40ps 先验证增益存在性；B 仅当 4 点中敏感文件>50% 且 ΔPIE>0.05 时评估 |
| **Q2 目标函数** | A. `max PIE_reconciled_net` 主<br>B. `min ser` 辅 | **A 主 + B 辅** | 主门以 PIE 判定，ser 窗口/锚粗筛代理并记诊断列 |
| **Q3 预算** | A. ≤18 物化/文件<br>B. ≤12 物化/文件 | **A（18）** | 3×6 天然预算 18，留2核下 4×18=72 物化 <5min（配对 0.31s + 排序 0.17m 先验） |
| **Q4 回退** | A. 失败→回退至 per-tier 最优锚（T1c 10ps）<br>B. 失败→跳过不产出 | **A** | 保证每文件必有可用参数，fallback 行不计入均值或按冻结口径显式约定 |

> Q1–Q4 在 T0 `explore_report.md → gates_frozen.json` 中冻结，后续 T1–T3 不得漂移。

## 7. Impact Scope

| 域 | 文件/模块 | 影响 |
|---|---|---|
| 新增工具（唯一生产代码触点） | `tools/auto_ir_scan.py`（复用/扩展）+ `tools/compare_adaptive_vs_frozen.py`（新） | 薄封装外层循环，留2核，复用现有 materialize/verify，不改内核 |
| 冻结基线透传（复用） | `src/workflow/export_joint_sequence_sidecar.py` | **不新增**透传参数，复用 `pool_root/delay_override/calibration_table` 三参数（默认 None 逐字节兼容） |
| 新增输出根 | `results/real_sequences_adaptive_v1/` 等（design §3） | 增量命名，物理隔离，守卫 fail-closed |
| 门与证据 | `openspec/changes/adaptive-pie-boost/evidence/` | trace、最优表、对比表、门报告、review 接受态 |
| 文档 | `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md` | 仅在 T3 收尾追加条目（plan 阶段不写） |

## 8. Affected Specs

- 新增 capability：`adaptive-pie-boost`（`G_adaptive` 增长披露门、per-file 3×6 择优语义、4 点 max PIE 对比契约、预算与回退）— delta spec 见 `specs/adaptive-pie-boost/spec.md`
- 复用（只读引用，不修改）：`aggressive-timing-calibration` 的池隔离与 `G_timing`、`auto-scan-gate` 的 `G_scan` 思想
- 无既有 spec 需原地修改（增量命名空间隔离）

## 9. Acceptance Criteria（分阶段门）

- **T0**：`explore_report.md` 与 `evidence/gates_frozen.json` 冻结（Q1–Q4 + 4 点 frozen max PIE 点位清单 + 阈值）；`compileall` + import 通过；池隔离守卫 tamper 通过；reviewer-go T0 PASS；data-lock/code-lock 冻结点落盘。
- **T1**：4 点 × 18 候选扫描完成且 `per_file_scan_trace.csv` 可归因（72 行量级，Wilson CI 齐全）；`G_budget` 合规；回退注入测试通过；reviewer-go T1 PASS。
- **T2**：以每文件最优参数全链重跑至 `*_adaptive_v1`（4 点各 `round1a_summary.txt` + `actual_ir_block_table.csv` + `security_calibrated_master_table.csv`），validator 行数对齐；`_adaptive_vs_frozen.csv` 4 行生成且 ΔPIE 可复现；`G_adaptive` 披露 + `G2/G4` PASS；reviewer-go T2 PASS。
- **T3**：对比报告与审计表完成；`per_file_optimal_params.csv/json` 固化；reviewer-go 终审 PASS + memory triage + `/finish-change` 可归档判定。

> 本 proposal 阶段仅冻结上述验收结构，不执行验收动作；任何真实数据执行需用户显式授权后方可启动（AGENTS.md §5.6）。

## 10. 约束回声

- 留2核：`workers = max(2, cpu_count-2)`，披露 `scan_wall_s / sort_s`；不引入重型机制（AGENTS.md §5.7）。
- 不覆写 `paper_grade_v3` / `authoritative`；增量 `*_adaptive_v1` 隔离；保精度 `frames300/seed20260228/tag_bits64/shards16` 不变。
- 走 OpenSpec：proposal → design → tasks → apply → review → archive，每阶段 reviewer-go 独立审查（只出 findings 不改文件）。

## 11. 自适应算法摘要（供 design 展开）

```
for each loss in {6,10,16,20}dB:
  frozen_max = argmax PIE_practical in polar_e2e_results.csv (1 point/loss)
  candidates = {delay_center ±Δ} × {window ∈ {35,40,45} × anchor ∈ {0,offset}}  # 3×6=18
  for c in candidates (ThreadPool workers=max(2,cpu-2)):
    materialize(pool_root=adaptive_v1, delay_override=c.delay, window=c.window, anchor=c.anchor)  # frames300
    collect ser/PIE_est/leak/IAB/Wilson CI → per_file_scan_trace.csv
  optimal = argmax PIE_est (Wilson 不重叠辅判) else fallback_per_tier
  rerun full chain with optimal → paper_grade_adaptive_v1
  compare optimal vs frozen_max → _adaptive_vs_frozen.csv (ΔPIE/Δser)
```
