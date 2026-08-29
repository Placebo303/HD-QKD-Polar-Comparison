# Proposal: auto-ir-param-scan

**状态：DRAFT — 纯规划阶段（plan-only），implementation deferred。用户指示：完成 proposal/design/tasks 三件套后收口，不进入 /opsx-apply。**

> 收口声明：本变更当前仅 plan 阶段，所有 tasks 处于待执行状态；不写生产代码、不改 `src/experiments/tools/results`、不启动真实数据扫描。后续是否进入 T0 由用户显式授权。

---

## 1. Goal

为**每个新到达的 ttbin 文件**在 IR 流程内自动扫描并选出最优参数，使不同文件的 `ser / 通量 / 窗口敏感性`差异被自适应消化，而非沿用一刀切的 per-tier 锚/窗配置。全流程以**小代价自动选优 → 大代价全量重跑**的二段式展开，最终产出每文件最优参数表与对应的 IR 产物。

复用并延伸 `polar-aggressive-7x-recovery` 的 T1c 经验：20 次物化 <6min、Wilson 区间判定有效性、40ps 不敏感区可作粗粒度先验。

---

## 2. Why（为何需要每文件自适应）

- **文件间异质性已实测**：T1c per-tier 5 锚 sweep（每档 5 锚×物化 20 次）显示不同 `d/bw/通量`组合对 `delay_override` 敏感度分化明显——T1c 中 200ps 位移在高维窄 bin 格上带来 IAB/PIE 可度量增益，而 40ps 粒度在多格上落入不敏感区（Wilson 区间重叠），一刀切锚无法兼顾。
- **一刀切锚/窗的天花板**：`polar-aggressive-7x-recovery` T1 C1a 8 格固定锚试点（`d=4096 × bw∈{40,200} × 4 档`）与 T1c 的 per-tier 最优锚全档 10ps 虽通过 `G_growth` 初筛，但属**per-tier 粗粒度最优**，未覆盖文件内 `peak_center` 漂移、通量差异、窗口竞争导致的 per-file 最优偏移。
- **全量重跑前需小代价择优**：121 格×4 档全量物化/重跑成本高（T5 量级数小时 + 校验链），在全量前对**单文件内多参候选**做轻量扫描可避免盲推次优点位；T1c 的 <6min/20 物化证明小样本扫描成本可控。
- **Review blocking 的启示**：`polar-aggressive-7x-recovery` review 发现 3 项 blocking（`gates_frozen` 均值误算、池覆写、G1 未真双跑）待修，说明**先冻结门与池语义、再扩量**的纪律必要；本变更将扫描器设计为外层循环+门复用，避免重蹈覆写/门误算风险。

**不做此变更的后果**：新文件到达时仍需人工 per-tier/per-point 事先 sweep，无法自动化；或直接沿用旧档 per-tier 最优锚，导致窄 bin 高维格 IAB 损失与 PIE 回退。

---

## 3. What

### 3.1 扫描参数与搜索空间边界（What is scanned）

| 参数 | 符号 | 搜索空间（初拟，T0 探索冻结） | 备注 |
|---|---|---|---|
| 延时锚 | `delay_override / peak_center_ps` | 每文件以 `pairing_v2` 的 `peak_center_ps` 为中心，±200ps 范围，步长 10ps（窄 bin）/ 40ps（宽 bin 粗筛），候选 5–9 点 | 沿用 T1c 粒度经验：40ps 为不敏感区下界，10ps 为细筛 |
| 有效配对窗口 | `effective_pairing_window_ps` | 30–50ns 区间，3–5 档（explore 冻结具体档位） | 复用 C1c 网格思想，但 per-file 自适应 |
| 帧起始锚 | `frame_anchor / frame_start_offset` | `{0, +offset}` 2 档（offset 由通量/窗口联动，explore 定量） | 轻量维度，失败即回退至 0 |
| SCL 列表大小 | `scl_list_size` | `{4, 8, 16}` 三档（默认 4→16 仅在增益档启用） | 成本敏感，详细见 design §2 |
| 冻结序轻量候选 | `freeze_order` | `{pw, tal_vardy_lite}` 2 档（`ga_full` 仅在 T2 后评估是否纳入） | 不在扫描器内做全 GA，仅轻量候选 |

> **边界声明**：搜索空间在 `explore_report.md → gates_frozen.json` 中冻结，后续 T1–T3 不得执行期漂移；任何扩维（如 `n=8192`）需另起 OpenSpec。

### 3.2 输入 → 输出

- **输入**：新文件的 `ttbin (+ .1 分片)` + `candidate` 侧car（或 `pairing_v2` 直出）；文件粒度为 `(src_tag, d, bw, blk)` 或按文件聚合的 batch。
- **输出**：
  1. `per_file_optimal_params.json/csv` — 每文件最优参数表（`file_id, d, bw, delay_opt, window_opt, anchor_opt, scl_opt, freeze_opt, objective_value, runner_meta`）；
  2. 对应最优参数的 IR 产物（序列池/候选/sidecar）落增量命名空间；
  3. 扫描过程表 `per_file_scan_trace.csv`（每候选点的 `ser, PIE_est, leak_EC, IAB, Wilson CI`）。

### 3.3 目标函数（Objective）

主口径候选（T0 决策 Q2 定夺，见 §6）：

- **候选 A（推荐）**：`max PIE_reconciled_net`（或 `PIE_est` 在无全解码时的代理），以审计表 `actual_ir_block_table.csv` 为准；
- **候选 B**：`min ser`（配对后原始 ser，成本最低，适合窗口/锚粗筛）；
- **候选 C**：`max SKR_reconciled_net_bps`（含通量权重，适合跨文件比较）。

> 设计层面支持三目标并记，门判定以冻结主目标为准，余量仅作诊断列（避免目标漂移）。

---

## 4. Scope

**In scope**

- 新增扫描器薄封装 `tools/auto_ir_scan.py`（外层循环，复用 `materialize` 与 `verify_gates`，见 design §4）；
- 增量落盘命名 `*_auto_scan_v1` 与三目录隔离复用（`real_sequences_auto_scan_v1` 等）；
- 每文件最优参数表 schema 与 `G_scan` 门定义（delta spec `auto-scan-gate`）；
- 小样本试点（2 文件×8 格）→ 全量扫描与门 → 固化归档的三阶段 plan（tasks.md），含 reviewer-go 与 data-lock 节点（仅规划，不执行）。

**Out of scope**

- 冻结基线其余逻辑（Polar SC/SCL 内核、安全有限长公式、finite-key 审计生成）—— 除 design §4 最小透传外不动；
- `results/paper_grade_v3` / `results/authoritative` / `results/paper_grade_v4_rate_search_fix` / `results/*_lossfix_v1` / `results/*_aggressive_v1` 既有产物 —— 只读；
- `fix-candidate-loss-namespace` 事件证据与 `polar-aggressive-7x-recovery` 的 T1 blocking 修复本身（本变更仅复用其池隔离/门思想，不代修）；
- research-line 方向（nonbinary LDPC / formal IR / qLDPC）—— 归属 sibling 仓库（AGENTS.md §0）；
- 不改 `comparison_bench/` 的 Polar 语义；comparison 仅作只读桥接。

---

## 5. Non-Goals

- 不承诺扫描必带来固定倍数 PIE 提升；以实测 `ΔPIE` 分布与审计表为准，40ps 不敏感区可判定为“无增益亦无损”。
- 不在 T0 阈值/预算冻结前启动任何真实数据扫描。
- 不引入 SHA-256 完整性清单等重型防御（AGENTS.md §5.7），以 Git 基线 + 字节比对 + 结构化校验为准。
- 不覆盖任何 `results/` 既有输出；全部增量命名。
- 不将扫描器做成通用超参优化框架；仅覆盖上表 5 参数的 per-file 轻量搜索。

---

## 6. 决策点 Q1–Q4（T0 explore 冻结，用户裁决）

| 决策项 | 选项 | 推荐 | 含义 |
|---|---|---|---|
| **Q1 搜索粒度** | A. 粗筛 40ps×3 窗×2 锚（~18 候选/文件）<br>B. 细筛 10ps×5 窗×2 锚（~50 候选/文件）<br>C. 自适应：先粗后细（40ps 粗筛→10ps 细化 top2 邻域） | **C** | 复用 T1c 经验：40ps 不敏感区作粗筛先验，10ps 仅在敏感文件上细化；兼顾成本与精度 |
| **Q2 目标函数** | A. `max PIE_reconciled_net`（主口径）<br>B. `min ser`（轻量代理）<br>C. `max SKR`（含通量） | **A 主 + B 辅** | 主门以 PIE 判定，ser 作窗口/锚粗筛代理并记诊断列；SKR 仅作跨文件归一参考 |
| **Q3 预算上限** | A. 每文件 ≤10 物化<br>B. 每文件 ≤20 物化<br>C. 每文件 ≤30 物化（含 SCL 档） | **A（≤10）起步，T1 后评估是否放宽至 B** | T1c 20 物化 <6min 证明 10 物化/文件成本可控；ponytail 最小可用先行 |
| **Q4 回退策略** | A. 任一文件扫描失败→回退至 per-tier 最优锚（T1c 结果）<br>B. 失败文件跳过不产出<br>C. 失败文件以 `ser` 次优锚回退 | **A** | 保证每文件必有可用参数；C 可作为 A 的诊断补充 |

> Q1–Q4 在 T0 explore 报告中给出建议值，主线在 T0 review 中冻结写入 `evidence/gates_frozen.json`，后续 T1–T3 不得漂移。

---

## 7. Impact Scope

| 域 | 文件/模块 | 影响 |
|---|---|---|
| 新增工具（唯一生产代码触点） | `tools/auto_ir_scan.py` | 新文件：外层扫描循环薄封装，复用现有 `materialize`/`verify` 逻辑，不改内核 |
| 冻结基线透传（可选） | `src/workflow/export_joint_sequence_sidecar.py` | **仅复用** `polar-aggressive-7x-recovery` 已立项的三参数透传（`pool_root/delay_override/calibration_table`），本变更不新增透传参数 |
| 新增输出根 | `results/real_sequences_auto_scan_v1/` 等（design §3） | 增量命名，物理隔离 |
| 门与证据 | `openspec/changes/auto-ir-param-scan/evidence/` | 扫描 trace、最优表、门报告、review 接受态 |
| 文档 | `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md` | 仅在 T3 收尾追加条目（plan 阶段不写） |

---

## 8. Affected Specs

- 新增 capability：`auto-scan-gate`（`G_scan` 增长门、每文件最优选优语义、预算与回退契约）— delta spec 见 `specs/auto-scan-gate/spec.md`
- 复用（只读引用，不修改）：`aggressive-timing-calibration` 的池隔离与 `G_timing` 思想、`aggressive-growth-gate` 的 `G_growth` 门结构
- 无既有 spec 需原地修改（增量命名空间隔离）

---

## 9. Acceptance Criteria（分阶段门，仅规划）

- **T0**：`explore_report.md` 与 `evidence/gates_frozen.json` 冻结（Q1–Q4 阈值/预算/目标函数落盘）；`compileall` + import 结构检查通过；池隔离守卫 tamper 通过；reviewer-go T0 PASS；data-lock/code-lock 冻结点落盘。
- **T1**：2 文件×8 格小样本试点物化完成且 `per_file_scan_trace.csv` 可归因；`G_scan` 初筛按冻结阈值判定（含 Wilson 区间）；任一文件失败按 Q4 回退至 per-tier 最优锚；reviewer-go T1 PASS；冻结点落盘。
- **T2**：全量扫描（覆盖新文件全集）与 `G_scan` 复筛 PASS；`per_file_optimal_params.csv` 全文件对齐且每文件 `objective` 可复现；跨档污染门（G2 等价）零碰撞；reviewer-go T2 PASS；冻结点落盘。
- **T3**：最优参数固化、产物落 `_auto_scan_v1` 三目录隔离、审计表与 `old_vs_new`（per-tier 最优 vs per-file 最优）对比完成；reviewer-go 终审 PASS + memory triage + `/finish-change` 可归档判定。

> 本 proposal 阶段仅冻结上述验收结构，不执行验收动作。

---

## 10. 约束回声

- 本变更**仅 plan 阶段**，implementation deferred，用户指示收口；任何对 `results/` 既有路径的写入需显式授权（AGENTS.md §5.2）。
- 复用 T1c 实证：20 物化 <6min、Wilson 区间判定、40ps 不敏感区作为 Q1/Q3 先验。
- 遵循 Research Code Engineering Policy（AGENTS.md §5.7）：最小实现、可复现、显式单位/假设、可验证小样本，拒绝重型防御与框架化。
