# Design: auto-ir-param-scan

**状态：DRAFT — 纯规划阶段，implementation deferred。阈值/预算数值留空待 `explore_report.md` 冻结。**

---

## 1. 总览与复用基线

- 本变更在 `fix-candidate-loss-namespace` 的 lossfix 命名空间与 `polar-aggressive-7x-recovery` 的 `_aggressive_v1` 探索之上，新增**每文件自适应**层；复用其池 key 约束 `(src_tag, d, bw, blk)`、确定性重跑语义与 `G_growth` 门思想。
- 全部新增产物与旧产物**物理隔离**（§3 三目录分离 + 增量命名），复用 `polar-aggressive-7x-recovery` 的 review 发现教训：池覆写与 `gates_frozen` 均值误算的根因是**门阈值未冻结先执行 + 池根未做 fail-closed 守卫**；本设计将二者列为 T0 前置门。
- 研究代码工程策略（AGENTS.md §5.7）约束：不引入 SHA-256 清单/原子写/备份回滚等重型机制；以 Git 基线 + 字节比对 + 结构化校验为准；扫描器以**薄封装 + 复用现有 verify**为原则。

---

## 2. 架构决策

### 2.1 扫描器形态：IR 流程**外层循环**（selected） vs 内嵌

| 方案 | 描述 | 取舍 |
|---|---|---|
| **A. 外层循环（selected）** | `tools/auto_ir_scan.py` 作为 IR 流程外层：对每文件枚举候选参数→调用现有 `materialize`/`export_sidecar`/`run_e2e` 单点物化→收集 `ser/PIE`→选优→最优参数再走一次全链重跑落盘 | **选中**：零侵入冻结基线；与 `materialize_aggressive_candidates.py` 复用池隔离语义；门可独立于解码内核复用 `verify_aggressive_gates`；失败回退易实现（per-file 粒度） |
| B. 内嵌 IR 内核 | 在 `run_e2e_pipeline.py` 内加扫描分支，单次调用内完成多参搜索 | 拒绝：侵入冻结基线主路径；与 AGENTS.md §5.1 基线保护冲突；回退与审计粒度粗 |

> 决策：采用 **A 外层循环**；扫描器仅做参数枚举与结果聚合，单点物化/解码仍走现有已验证路径（`export_joint_sequence_sidecar` + `run_e2e_pipeline` 的既有透传）。

### 2.2 与 materialize / aggressive 管线复用与池隔离

```
ttbin (src_tag/d/bw/blk)
  │
  ▼
auto_ir_scan.py  ──枚举候选──►  materialize_real_sequences_for_point(pool_root=auto_scan_v1, delay_override, calibration_table)
                                  │  (复用 polar-aggressive-7x-recovery 的三参数透传，不新增参数)
                                  ▼
                          real_sequences_auto_scan_v1/<src_tag>/d{d}_bw{bw}/blk{b}/
                                  │
                                  ▼
                          export_sidecar_for_point → sidecar_meta.json (delay_override, calibration_table_sha256)
                                  │
                                  ▼
                          verify_gates (G2/G3/G4 复用 + G_scan 新增)
                                  │
                                  ▼
                          per_file_scan_trace.csv ──选优──► per_file_optimal_params.csv
                                                              │
                                                              ▼
                                                     全链重跑（最优参数）→ paper_grade_auto_scan_v1
```

- **池隔离**：复用 `polar-aggressive-7x-recovery` 的 fail-closed 守卫——`pool_root` 必须含 `auto_scan_v1` 子串，否则拒绝；`candidate_dir`/`out_root` 同理。彻底避免 review 发现的“池覆写”类 defect 复发。
- **确定性**：单候选点双跑一致性（G1 等价）仅在 T1 抽检，不对全量扫描做全双跑（成本控制，T1c 经验：G1 抽检已可捕获非确定性）。

### 2.3 门的演进：从污染检测到增益度量

- 复用 `fix-candidate-loss-namespace` 的 **G2 跨档字节唯一性**（污染检测）与 `polar-aggressive-7x-recovery` 的 **G_growth 增长门**（增益度量）双层思想：
  - **污染门**（必过）：`G_scan_contamination` — 同 (d,bw) 不同 `src_tag` 的 `a_eff/b_eff` sha256 零碰撞；任何碰撞即 STOP（沿用 lossfix G2 硬条件）。
  - **增益门**（`G_scan` 主门）：per-file `ΔPIE = PIE_per_file_opt − PIE_per_tier_opt` 的分布门，阈值结构复用 `G_growth` 的三阈值形态（均值/中位数/正占比），但统计单元从“格”变为“文件”，阈值在 T0 `gates_frozen.json` 中冻结。
  - **预算门**（`G_budget`）：每文件物化次数 ≤ 冻结预算（Q3），超时/超预算即截断并回退。

---

## 3. 增量命名与三目录分离

### 3.1 后缀与物理隔离

- 后缀：`_auto_scan_v1`（与 `_lossfix_v1` / `_aggressive_v1` 正交，仅以后缀区分，禁止无后缀写入）。
- 三目录（与 lossfix/aggressive 旧根零交集）：

```
results/real_sequences_auto_scan_v1/<src_tag>/d{d}_bw{bw}/blk{b}/
    a_eff.npy, b_eff.npy, materialize_meta.json, pool_manifest_entry

results/authoritative_auto_scan_v1/e2e_<tier>_fullgrid_pairing_v2_candidate_auto_scan_v1/
    sidecars/, grid_tables/, MANIFEST.csv  (每文件最优参数对应的候选集)

results/paper_grade_auto_scan_v1/four_loss_parts_frames300_auto_scan_v1/<loss_XXdB>/
    round1a_summary.txt, actual_ir_block_table.csv, security_calibrated_master_table.csv
    （仅最优参数重跑产物；扫描过程 trace 不落此根）

openspec/changes/auto-ir-param-scan/evidence/
    per_file_scan_trace.csv, per_file_optimal_params.csv, gates_frozen.json,
    G_scan_report.md, budget_report.md, old_vs_new_per_tier_vs_per_file.csv
```

- WSL 等价：`$PROJECT_RESULTS_ROOT/real_sequences_auto_scan_v1` 等（AGENTS.md §5.4）。

### 3.2 隔离校验

- 驱动启动断言：`pool_root` 含 `auto_scan_v1` 子串；`out_root`/`candidate_dir` 同理；否则 fail-closed。
- T0 含 tamper 测试：人为指向旧根（`real_sequences`/`real_sequences_aggressive_v1`/`authoritative`）应被守卫拒绝。
- 不覆写旧根：`results/paper_grade_v3`、`results/authoritative`、`results/paper_grade_v4_rate_search_fix`、`results/*_lossfix_v1`、`results/*_aggressive_v1` 保持只读。

---

## 4. 最小改动清单（冻结基线触碰面）

> **原则**：本变更**不新增**冻结基线透传参数；仅复用 `polar-aggressive-7x-recovery` 已立项的三参数透传，默认行为逐字节兼容旧调用；任何超出清单的改动需另起 OpenSpec + review-go 三阶。

| 文件 | 改动 | 默认行为 |
|---|---|---|
| `tools/auto_ir_scan.py` | **新文件（唯一新增生产代码）**：薄封装外层循环；入参 `--ttbin-root / --candidate-root / --pool-root / --scan-config / --objective {pie,ser,skr} / --budget-per-file / --out-root`；内核循环：枚举候选→调 `materialize_real_sequences_for_point(..., pool_root, delay_override, calibration_table)`→调 `export_sidecar_for_point`→收集 `ser/PIE`→Wilson 区间→选优→回退判定→最优参数全链重跑 | — |
| `tools/verify_auto_scan_gates.py` | **新文件**：`G_scan` + `G_budget` + 复用 `G2/G3/G4` 校验；输入 `per_file_scan_trace.csv` + `per_file_optimal_params.csv` + `MANIFEST.csv` | — |
| `src/workflow/export_joint_sequence_sidecar.py` | **不改**（复用既有三参数透传） | 三参数皆 `None` 时与旧硬编码路径/自动锚定/无校正逐字符一致 |
| `experiments/run_e2e_pipeline.py` | **不改**（复用既有 CLI 旗标透传） | 不传参时与旧 CLI 等价 |
| `comparison_bench/*` | **禁止修改** | — |
| `src/reconciliation/*`, `tools/longrun_*` | **禁止修改** | — |

- 单元断言（T0）：`auto_ir_scan --help` 可导入；不传 `--pool-root` 时守卫拒绝旧根；`per_file_optimal_params.csv` schema 校验通过。
- 未在清单中的文件**禁止**修改。

---

## 5. 输出落盘（增量命名，不覆盖）

| 产物 | 路径（增量命名） | 内容 |
|---|---|---|
| 扫描 trace | `evidence/per_file_scan_trace.csv` | `file_id, d, bw, tier, candidate_id, delay_override, window_ps, anchor, scl, freeze_order, raw_ser, PIE_est, leak_EC, Wilson_low/high, runtime_s` |
| 最优表 | `evidence/per_file_optimal_params.csv` + `per_file_optimal_params.json` | 每文件一行最优参数 + `objective_value` + `runner_meta (git HEAD, seed, frames)` |
| 新池 MANIFEST | `results/real_sequences_auto_scan_v1/MANIFEST.csv` | `src_tag,d,bw,blk,ttbin_path,ttbin_sha256,a_eff_sha256,b_eff_sha256,delay_override,window_ps,anchor,params_tag` |
| 新候选 | `results/authoritative_auto_scan_v1/...` | `sidecars/`, `MANIFEST.csv`, `grid_tables/`（仅最优参数） |
| 重跑产物 | `results/paper_grade_auto_scan_v1/...` | 每档 `round1a_summary.txt`, `actual_ir_block_table.csv`, `security_calibrated_master_table.csv` |
| 门证据 | `evidence/G_scan_report.md`, `evidence/budget_report.md`, `evidence/gates_frozen.json` | `G_scan`/`G_budget`/`G2` 报告 + 阈值冻结 |
| 对比报告 | `evidence/old_vs_new_per_tier_vs_per_file.csv` | `per-tier 最优锚 vs per-file 最优` 的 `ΔPIE/Δser/ΔSKR` 逐文件对照 |
| 探索报告 | `explore_report.md` | Q1–Q4 建议阈值/预算/目标函数 + 搜索空间冻结依据 |

- 旧根保持只读；新旧对比仅通过只读脚本生成 `old_vs_new` 报告，不回写旧目录。

---

## 6. 扫描策略细节

### 6.1 两阶段搜索（Q1=C 自适应，推荐）

```
Phase 1 粗筛：40ps 步长 × 3 窗 × 2 锚  →  ~12–18 候选/文件  →  以 ser/IAB 粗排，Wilson 区间判不敏感区
Phase 2 细化：仅对粗筛 top2 邻域以 10ps 步长细化  →  +4–6 候选  →  以 PIE 主目标选优
预算：Phase1 + Phase2 ≤ 10 (+可选 ≤4 SCL 档)  ≤ Q3 冻结上限
```

- 40ps 不敏感区的判定：Wilson 区间重叠即判等价，不再细化（T1c 经验复用）。
- 每候选点物化的 `frames` 固定为 `frames300`（与 lossfix/aggressive 一致，仅 T1 试点可用 `frames100` 加速，T2 全量恢复 300）。

### 6.2 目标函数与 Wilson 区间

- `ser` 粗筛阶段用 Wilson 95% CI（`n = n_eff_pairs`）判显著性；`PIE` 终选阶段以 `PIE_reconciled_net` 审计值为准，`PIE_est` 仅作扫描期代理。
- `beta_eff_empirical` 仍由泄漏/错误推导，不手填（AGENTS.md §5.5）。
- `beta` 不作为扫描目标，避免与 `leak_EC` 记账混淆。

### 6.3 失败回退（Q4=A）

| 触发 | 处置 |
|---|---|
| 单候选物化失败（异常/超时） | 跳过该候选，记 `candidate_status=failed`，不中断文件内其余候选 |
| 单文件全部候选失败或 `G_scan` 无正增益 | 回退至 **per-tier 最优锚**（T1c 结果：全档 10ps），该文件 `optimal_source=fallback_per_tier` |
| 单文件扫描超预算 | 截断至预算上限内最优，记 `truncated=true` |
| 跨档污染门 FAIL | 全局 STOP，不得调参绕过（沿用 AGENTS.md §10.1 纪律） |
| 需求歧义/未覆盖的冻结基线改动冲动 | 返回 planner / OpenSpec，不猜测 |

---

## 7. 门定义（阈值数值待冻结）

### 7.1 G_scan — 增长门（主门，决定是否由试点进入全量）

- **输入**：试点文件集的 `ΔPIE_file = PIE_per_file_opt − PIE_per_tier_opt` 分布（`per_file_optimal_params.csv` vs `per-tier 最优对照`）。
- **判定**（满足任一即 PASS，进入下一阶段；否则 STOP）：
  1. 均值 `mean ΔPIE ≥ G_scan.mean_delta_PIE`（explore 建议，预期 0.05–0.2 bits/sym 量级，小于 aggressive 的格均值门，因 per-file 增量更细）；
  2. 或中位数 `median ΔPIE ≥ G_scan.median_delta_PIE`；
  3. 或正增益文件占比 `frac(ΔPIE > 0) ≥ G_scan.positive_frac`（explore 建议 6/8 或 7/8 类比）。
- **Wilson 感知**：`ΔPIE` 的显著性以 Wilson 区间不重叠为辅判，仅作诊断，不替代主阈值。
- **失败处置**：G_scan FAIL ⇒ 就地 STOP，不得调参绕过；产物与诊断表归档，交主线裁决是否放宽预算或终止（ponytail lite：可直接采纳“per-tier 最优已足够”的简化结论，跳过全量）。

### 7.2 G_budget — 预算门

- 每文件物化次数 ≤ `G_budget.max_materializations_per_file`（Q3 冻结值，推荐 10）；
- 单文件扫描 wall-clock ≤ `G_budget.max_seconds_per_file`（explore 建议，预期 30–60s）；
- 超限即截断并记 `truncated`，不记为门 FAIL，但需在 `budget_report.md` 中披露截断率。

### 7.3 复用门（沿用 fix-candidate / aggressive 终版语义）

- **G2 跨档字节唯一性**：同 (d,bw) 不同 src_tag 的 `a_eff/b_eff` sha256 零碰撞（硬门）。
- **G3 档位序**：档均值 ser 严格有序 `6>10>16>20`（硬门）；逐文件/逐格倒置仅诊断，不门控。
- **G4 溯源完整性**：每个 sidecar 记录 `source_ttbin` 路径+sha256、`processing_rule_version`、`src_tag`、`pool_root` 指纹。

### 7.4 阈值冻结流程（Q1–Q4）

1. `/opsx-explore` 产出 `explore_report.md`（含 Q1 搜索空间、Q2 目标函数、Q3 预算、Q4 回退、G_scan 三阈值建议）。
2. 主线在 T0 review 中冻结阈值写入 `evidence/gates_frozen.json`（`design.md §7` 附录镜像），后续 T1–T3 均以冻结值为准，不得执行期漂移。

---

## 8. 回退预案

| 触发 | 处置 |
|---|---|
| 任意硬门 FAIL（G_scan_contamination/G2/G4）且非脚本 bug | **STOP**，产物就地保留，不得调参/重跑绕过；主线裁决是否修正扫描空间或终止变更 |
| G_scan 增益门 FAIL | STOP 归档；可裁决回退至 per-tier 最优锚作为终态（不视为失败产物的覆写） |
| 单文件扫描失败 | 按 Q4=A 回退至 per-tier 最优锚，该文件 `fallback` 标记 |
| 校准表/旧 per-tier 最优锚缺失 | 扫描器启动前断言失败，fail-closed，不进入扫描 |
| 对 `results/` 既有路径的写入 | 先取用户显式授权（AGENTS.md §5.2），否则拒绝 |
| 需求歧义 | 返回 planner / OpenSpec，不猜测（AGENTS.md §3） |

- **回退语义**：任何 STOP 均为**不可重跑/不可调参**的证据冻结（AGENTS.md §10.1）；修正需新 OpenSpec 或本变更的显式 amend 并重走 review-go。
- **ponytail lite 语义**：若 T1 试点显示 per-file 增益全落在 40ps 不敏感区内（Wilson 重叠），可直接采纳“per-tier 最优已足够，per-file 扫描非必需”的简化结论，跳过 T2 全量而直接归档（需 review-go 确认）。

---

## 9. 测试分层（对齐 AGENTS.md §10.1，仅规划）

- **T0**：`compileall` + import + 默认路径等价断言 + 守卫 tamper（指向旧根应拒绝）+ 合成 ttbin 最小回路（patched reader，不触真实数据）。
- **T1**：G1 抽检双跑一致性 + `G_scan` 初筛 + 回退注入测试（人为注入单文件全失败应回退至 per-tier 锚）；合成 file 最小回路。
- **T2**：真实 ttbin 小样试点（≤2 文件×8 格）端到端扫描 + 门校验；通过后再扩量至全量。
- **T3**：全量扫描 trace 完整性 + `old_vs_new` 跨档对比回归（对照 per-tier 最优趋势，不逐位）。

---

## 10. 与 explore 的衔接

- 本 design 的阈值/预算/搜索空间数值留空待 `explore_report.md` 落盘后在 T0 review 中冻结；在此之前 T1 不启动真实数据执行。
- 若 explore 发现更廉价的纯窗口寻优即可覆盖延时锚收益，则在报告中记录并由主线裁决是否收缩搜索空间（ponytail lite：以最小可用搜索为准）。

---

## 11. 加速设计（2026-08-29 实测重规划 — 瓶颈在 polar 而非配对）

> **重规划依据**：T0.7 实测（18 点 0.17m、G_scan 预算 40m、per-point 2.01s、sort 0.31s、jobs 18 留2核、6dB 真值 59m/16dB 58m/20dB 51m）证伪原假设“配对是瓶颈”，瓶颈已转移至 polar 译码。

### 11.1 实测 vs 原设计对比

| 维度 | 原设计（proposal 2026-08-28 前） | T0.7 实测 | 重规划结论 |
|---|---|---|---|
| **瓶颈定位** | 配对耗时主导，需 Numba+共享排序+ThreadPool+batch 复用+ G_scan<2m/文件 联合压至 40m 内 | 配对 0.31s（占 scan 10.2s 的 3%），译码 60m/121≈30s/点（另档真值 51–59m） | **瓶颈在 polar 译码而非配对**；配对已非优化主战场 |
| **配对加速** | Numba 双指针 O(N+M) + Rust 备选 + 共享排序 + ThreadPool + batch 复用 + 分层 4 值→121 点细调 | 共享排序仅 0.31s、Numba 已利用、ThreadPool jobs18 留2核下 18 点 0.17m（10.2s） | 保留 **Numba+共享排序+ThreadPool(留2核)** 为**已验证基线**；Rust/分层细调降为**按需**（仅当 per-point>10s 或档全量>120m 时评估） |
| **G_scan 目标** | <2m/文件（预算 40m/18 点≈2.2m/点） | 0.17m/文件（10.2s/18 点≈0.57s/点，2.01s 含 sleep 桩） | 重设 **G_scan <1m/文件**（已达 0.17m，余量 6×）；不扩展至 <2m |
| **G_full_121 目标** | 未显式（隐含 <40m 全量） | 59m/58m/51m 真值（121 点全量） | 重设 **G_full_121 60m/档**（对齐真值中位，不追 <40m） |
| **并发约束** | 未量化 | jobs18 留2核（workers=max(2,cpu-2)）已验证 | 冻结**留2核**，不引入重型机制 |

### 11.2 保留 vs 降级清单

- **保留（已验证，不回退）**：
  - `numba.njit` 双指针 O(N+M) `coincidence`（`tools/auto_ir_scan.py:_coincidence_count`，numpy bisect 仅 fallback）
  - 共享排序：每 ttbin `a_ts/b_ts` 各排序 1 次（`sort_cost_s` 披露，实测 0.31s）
  - ThreadPool 留2核：`workers=max(2,cpu-2) ∩ jobs`，已验证 18 点并行 0.17m
  - batch 复用/增量续跑：`manifest.csv` 追加 + `done set` 跳过已做
  - 薄封装：仅 `tools/auto_ir_scan.py` + `verify_auto_scan_gates.py`，不侵入 `src/experiments/tools`

- **降为按需（不删代码，仅不默认启用）**：
  - Rust 备选：仅当单点配对 >5s 或 N+M>1e7 且 Numba 仍 >1s 时评估
  - 分层 4 值→121 点细调：仅当 G_scan 显示敏感文件占比 >30% 且 ΔPIE 中位数 >0.1 时评估
  - 额外缓存/原子写/文件锁：按 AGENTS.md §5.7 禁止，除非证实具体失败模式

### 11.3 重设门与预算

- `G_scan_cost_min` 阈值：由 **<40m** 重设为 **<1m/文件**（18 点则 <18m 总量，但单文件口径 <1m）；`tools/auto_ir_scan.py` 中 `G_scan_cost_budget_min=40` 同步改为 1（单文件）或保持 40 作总预算兼容披露，校验 `scan_wall < 60s` 即 PASS（已达 10.2s）。
- `G_full_121` 新增档级门：121 点全量（含译码）**≤60m/档** 为 PASS，>60m 触发诊断（不阻断扫描，仅披露 polar 侧成本）。
- `G_budget.max_seconds_per_file`：由 30–60s 重标为 **≤60s**（含配对+选优，不含全量译码）；配对子预算 **≤1s/点**（实测 0.31s 排序+0.5s/点配对）。

### 11.4 文档与实现收敛

- 原“Numba 双指针 / Rust 备选 / 共享排序 / ThreadPool / batch 复用 / G_scan<2m/文件 / 分层 4→121”7 项中，3 项已验证保留、2 项按需、2 项重标目标；实现收敛于 **tools/auto_ir_scan.py 薄封装**，不引入重型机制（AGENTS.md §5.7）。

---

## 附录 A. 自由度钉死清单（扫描时显式固定）

- `pairing_mode=nearest`, `processing_rule_version=pairing_v2`, `occupancy_filter=0`, `max_pairs=0`, `frame_len_symbols` 与 lossfix/aggressive 一致；`HDQKD_NEAREST_FRAME_THRESHOLD_PS` 保持默认 40000；`HDQKD_ALIGN_DEBUG=0`；JSON meta 的 `created_at` 不参与字节比对。
- 扫描器新增自由度仅限 §2 表内 5 参数；其余自由度（`n, code_rate` 等）不在扫描器内变动。

## 附录 B. 术语

- **per-tier 最优**：T1c sweep 产出的每档统一最优锚（当前全档 10ps）。
- **per-file 最优**：本变更扫描器为单文件选出的最优参数组合。
- **G_scan**：per-file 增益门（`ΔPIE` 分布门），结构复用 `G_growth` 但统计单元为文件。
