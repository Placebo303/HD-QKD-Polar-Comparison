# Design: adaptive-pie-boost

**状态：DRAFT — 骨架，阈值/预算数值留空待 `explore_report.md → gates_frozen.json` 冻结。**

## 1. 总览与复用基线

- 本变更在 `fix-candidate-loss-namespace` 的 lossfix 命名空间与 `polar-aggressive-7x-recovery` / `auto-ir-param-scan` 的池隔离、G2/G3/G4 门体系之上，新增**每文件双层自适应**层；复用其池 key 约束 `(src_tag, d, bw, blk)`、确定性重跑语义与 `G_growth/G_scan` 三阈值门思想，但将对比收敛至**仅四组冻结基线最高 PIE 点位**（6/10/16/20dB 各 1 点，共 4 点），成本从 484 全量降至 4×18 候选 + 4 次重跑。
- 全部新增产物与旧产物**物理隔离**（§3 三目录分离 + `*_adaptive_v1` 后缀），复用既有教训：池覆写与 `gates_frozen` 均值误算根因是**门阈值未冻结先执行 + 池根未做 fail-closed 守卫**；本设计将二者列为 T0 前置门。
- 研究代码工程策略（AGENTS.md §5.7）约束：不引入 SHA-256 清单/原子写/备份回滚/文件锁等重型机制；以 Git 基线 + 字节比对 + 结构化校验为准；扫描器以**薄封装 + 复用现有 verify**为原则，留2核 `workers=max(2,cpu-2)`。

## 2. 架构决策

### 2.1 扫描器形态：IR 流程**外层循环**（selected） vs 内嵌

| 方案 | 描述 | 取舍 |
|---|---|---|
| **A. 外层循环（selected）** | `tools/auto_ir_scan.py` 复用/扩展作为 IR 外层：对每文件枚举 18 候选→调现有 `materialize`/`export_sidecar` 单点物化→收集 `ser/PIE`→Wilson 区间→选优→最优参数再走一次全链重跑落盘 | **选中**：零侵入冻结基线；与 `materialize_aggressive_candidates.py` 复用池隔离语义；门可独立于解码内核复用 `verify_*_gates`；失败回退易实现（per-file 粒度）；仅 4 点成本可控 |
| B. 内嵌 IR 内核 | 在 `run_e2e_pipeline.py` 内加扫描分支，单次调用内完成多参搜索 | 拒绝：侵入冻结基线主路径；与 AGENTS.md §5.1 冲突；回退与审计粒度粗 |

> 决策：采用 **A 外层循环**；扫描器仅做参数枚举与结果聚合，单点物化/解码仍走现有已验证路径（`export_joint_sequence_sidecar` + `run_e2e_pipeline` 的既有三参数透传，不新增参数）。

### 2.2 与 materialize / aggressive 管线复用与池隔离

```
frozen_max points (4): polar_e2e_results.csv --argmax PIE--> (d,bw,blk) per loss
        │
        ▼
ttbin (src_tag/d/bw/blk)  ──►  auto_ir_scan.py ──枚举 18 候选 (3 delay × 6 window/anchor)──►
                                   │  (复用三参数透传 pool_root/delay_override/calibration_table，不新增)
                                   ▼
                           real_sequences_adaptive_v1/<src_tag>/d{d}_bw{bw}/blk{b}/
                                   │
                                   ▼
                           export_sidecar_for_point → sidecar_meta.json (delay/window/anchor 指纹)
                                   │
                                   ▼
                           verify_gates (G2/G3/G4 复用 + G_adaptive/G_budget 新增)
                                   │
                                   ▼
                           per_file_scan_trace.csv (4×18=72 行) ──选优──► per_file_optimal_params.csv (4 行)
                                                                               │
                                                                               ▼
                                                                      全链重跑（最优参数）→ paper_grade_adaptive_v1 (4 点)
                                                                               │
                                                                               ▼
                                                                      _adaptive_vs_frozen.csv (4 行对比)
```

- **池隔离**：复用 fail-closed 守卫——`pool_root` 必须含 `adaptive_v1` 子串，否则拒绝；`candidate_dir`/`out_root` 同理。彻底避免“池覆写”类 defect。
- **确定性**：单候选点双跑一致性（G1 等价）仅在 T1 抽检 1–2 点，不对 72 候选全双跑（成本控制，T1c 经验复用）。
- **留2核**：`workers = max(2, cpu_count-2)`，实测披露 `scan_wall_s / sort_s / per_point_s`；T0.7 先验 18 点 0.17m、sort 0.31s 已验证配对非瓶颈，瓶颈在 polar 译码，故 72 候选配对 <1m，4 次重跑译码 ~30s/点。

### 2.3 门的演进：从污染检测到增益披露

- 复用 **G2 跨档字节唯一性**（污染检测）与 **G_growth/G_scan 增长门**（增益度量）双层思想，但本变更**不设硬性“必须提升”门**（proposal §3.2）：
  - **污染门**（必过）：`G_adaptive_contamination` — 同 (d,bw) 不同 `src_tag` 的 `a_eff/b_eff` sha256 零碰撞；任何碰撞即 STOP（沿用 lossfix G2 硬条件）。
  - **增益披露门**（`G_adaptive` 主披露）：per-file `ΔPIE = PIE_adaptive_opt − PIE_frozen_max` 的 4 点分布披露，含均值/中位数/正占比 + Wilson 显著性辅判，不阻断归档，仅决定结论措辞（“提升/不敏感/回退”）。
  - **预算门**（`G_budget`）：每文件物化次数 ≤18，超时即截断并回退至 per-tier 锚。

## 3. 增量命名与三目录分离

### 3.1 后缀与物理隔离

- 后缀：`_adaptive_v1`（与 `_lossfix_v1` / `_aggressive_v1` / `_auto_scan_v1` 正交，仅以后缀区分，禁止无后缀写入）。
- 三目录（与旧根零交集，聚合根可选 `results/adaptive_v1/`）：
```
results/real_sequences_adaptive_v1/<src_tag>/d{d}_bw{bw}/blk{b}/
    a_eff.npy, b_eff.npy, materialize_meta.json

results/authoritative_adaptive_v1/e2e_<tier>_fullgrid_pairing_v2_candidate_adaptive_v1/
    sidecars/, grid_tables/, MANIFEST.csv  (每文件最优参数对应的候选集，4 点)

results/paper_grade_adaptive_v1/four_loss_parts_frames300_adaptive_v1/<loss_XXdB>/
    round1a_summary.txt, actual_ir_block_table.csv, security_calibrated_master_table.csv
    （仅最优参数重跑产物；扫描过程 trace 不落此根）

# 聚合等效（task 约束的 results/adaptive_v1/*）：
results/adaptive_v1/
    per_file_scan_trace.csv, per_file_optimal_params.csv, _adaptive_vs_frozen.csv, MANIFEST.csv

openspec/changes/adaptive-pie-boost/evidence/
    per_file_scan_trace.csv, per_file_optimal_params.csv, gates_frozen.json,
    G_adaptive_report.md, budget_report.md, _adaptive_vs_frozen.csv
```

- WSL 等价：`$PROJECT_RESULTS_ROOT/real_sequences_adaptive_v1` 等（AGENTS.md §5.4）。

### 3.2 隔离校验

- 驱动启动断言：`pool_root` 含 `adaptive_v1` 子串；`out_root`/`candidate_dir` 同理；否则 fail-closed。
- T0 含 tamper 测试：人为指向旧根（`real_sequences`/`real_sequences_aggressive_v1`/`authoritative`/`paper_grade_v3`）应被守卫拒绝。
- 不覆写旧根：`results/paper_grade_v3`、`results/authoritative`、`results/paper_grade_v4_rate_search_fix`、`results/*_lossfix_v1`、`results/*_aggressive_v1` 保持只读。

## 4. 最小改动清单（冻结基线触碰面）

> **原则**：本变更**不新增**冻结基线透传参数；仅复用 `polar-aggressive-7x-recovery` 已立项的三参数透传，默认行为逐字节兼容旧调用；任何超出清单的改动需另起 OpenSpec + review-go 三阶。

| 文件 | 改动 | 默认行为 |
|---|---|---|
| `tools/auto_ir_scan.py` | **复用/扩展（唯一生产代码触点）**：增 3×6 枚举分支与 `--adaptive-vs-frozen` 对比模式；入参 `--pool-root / --scan-config / --objective pie / --budget-per-file 18 / --frozen-manifest`；内核循环：枚举 18→调 `materialize_real_sequences_for_point(..., pool_root, delay_override)`→调 `export_sidecar_for_point`→收集 `ser/PIE`→Wilson→选优→回退→最优全链重跑；留2核 `workers=max(2,cpu-2)`，Numba 双指针+共享排序复用 | 不传 `--pool-root` 时守卫拒绝旧根；默认 `objective=pie` |
| `tools/compare_adaptive_vs_frozen.py` | **新文件（可选，若 auto_ir_scan 已含对比则为 thin wrapper）**：输入 `per_file_optimal_params.csv` + 冻结 `polar_e2e_results.csv` max 行，输出 `_adaptive_vs_frozen.csv`（4 行，ΔPIE/Δser/Wilson） | — |
| `tools/verify_adaptive_gates.py` | **新文件或复用 `verify_auto_scan_gates.py`**：`G_adaptive` + `G_budget` + 复用 `G2/G3/G4`；输入 `per_file_scan_trace.csv` + `MANIFEST.csv` | — |
| `src/workflow/export_joint_sequence_sidecar.py` | **不改**（复用既有三参数透传） | 三参数皆 `None` 时与旧硬编码路径/自动锚定/无校正逐字符一致 |
| `experiments/run_e2e_pipeline.py` | **不改**（复用既有 CLI 旗标透传） | 不传参时与旧 CLI 等价 |
| `comparison_bench/*` | **禁止修改** | — |
| `src/reconciliation/*`, `tools/longrun_*` | **禁止修改** | — |

- 单元断言（T0）：`auto_ir_scan --help` 可导入且含 `--pool-root/--scan-config/--objective/--budget-per-file/--frozen-manifest`；不传 `--pool-root` 时守卫拒绝旧根；`per_file_optimal_params.csv` schema 校验通过。
- 未在清单中的文件**禁止**修改。

## 5. 输出落盘（增量命名，不覆盖）

| 产物 | 路径（增量命名） | 内容 |
|---|---|---|
| 扫描 trace | `evidence/per_file_scan_trace.csv` + `results/adaptive_v1/per_file_scan_trace.csv` | `file_id, loss_db, d, bw, blk, candidate_id, delay_ps, window_ps, anchor, raw_ser, PIE_est, leak_EC, Wilson_low/high, runtime_s`（72 行量级） |
| 最优表 | `evidence/per_file_optimal_params.csv` + `.json` + `results/adaptive_v1/per_file_optimal_params.csv` | 每文件 1 行最优（4 行）+ `objective_value` + `fallback_flag` + `runner_meta (git HEAD, seed, frames)` |
| 新池 MANIFEST | `results/real_sequences_adaptive_v1/MANIFEST.csv` | `src_tag,d,bw,blk,ttbin_path,ttbin_sha256,a_eff_sha256,b_eff_sha256,delay_ps,window_ps,anchor,params_tag` |
| 新候选 | `results/authoritative_adaptive_v1/...` | `sidecars/`, `MANIFEST.csv`, `grid_tables/`（仅 4 点最优） |
| 重跑产物 | `results/paper_grade_adaptive_v1/...` | 每档 `round1a_summary.txt`, `actual_ir_block_table.csv`, `security_calibrated_master_table.csv`（4 点，重跑 validator 对齐） |
| 对照表 | `results/adaptive_v1/_adaptive_vs_frozen.csv` + `evidence/_adaptive_vs_frozen.csv` | `loss_db,d,bw,blk,PIE_frozen,PIE_adaptive,ΔPIE,ser_frozen,ser_adaptive,Δser,beta_frozen,beta_adaptive,optimal_params`（4 行） |
| 门证据 | `evidence/G_adaptive_report.md`, `evidence/budget_report.md`, `evidence/gates_frozen.json` | `G_adaptive`/`G_budget`/`G2` 报告 + 阈值冻结 |
| 探索报告 | `explore_report.md` | Q1–Q4 阈值/预算/4 点清单 + 搜索空间冻结依据 |

- 旧根保持只读；新旧对比仅通过只读脚本生成 `_adaptive_vs_frozen.csv`，不回写旧目录。

## 6. 扫描策略细节

### 6.1 18 候选生成（Q1=A 固定 40ps）

```
candidates = []
for delay in [center-40ps, center, center+40ps]:          # 3
  for window in [35,40,45]ns:                              # 3
    for anchor in [0, +offset]:                            # 2
      candidates.append((delay, window, anchor))           # 3×3×2? 需 3×6=18，故 window×anchor 固定为 6 组合：
# 实际 6 组合 = window ∈ {35,40,45} × anchor ∈ {0,offset} 的 3×2=6，与 delay 3 正交 → 18
# 若 explore 定 window 2 档则改为 window 2×anchor 3 等价，总量保持 18
预算：18/文件，4 文件共 72 物化，并行 workers=max(2,cpu-2)，预期配对 <1m
```

- 40ps 不敏感区判定：Wilson 区间重叠即等价，不再细化（T1c 经验复用）。
- 每候选点物化 `frames` 固定 `frames300`（保精度，不用 frames100 加速，除非 gates_frozen 显式授权试点）。
- `Δ=40ps` 为初拟，若 explore 发现 16dB 窄 bin 敏感则对该档局部改 Δ=10ps（需 gates_frozen 显式按档覆盖）。

### 6.2 目标函数与 Wilson 区间

- `ser` 粗筛用 Wilson 95% CI（`n=n_eff_pairs`）判显著性；`PIE` 终选以 `PIE_reconciled_net` 审计值为准，`PIE_est` 仅作扫描期代理（`PIE_est = IAB - leak_EC/n` 近似）。
- `beta_eff_empirical` 仍由泄漏/错误推导，不手填（AGENTS.md §5.5）。
- 扫描期不以 `beta` 为目标，避免与 `leak_EC` 记账混淆。

### 6.3 失败回退（Q4=A）

| 触发 | 处置 |
|---|---|
| 单候选物化失败（异常/超时） | 跳过该候选，记 `candidate_status=failed`，不中断文件内其余候选 |
| 单文件 18 候选全失败或无正增益 | 回退至 **per-tier 最优锚（T1c 10ps）**，该文件 `optimal_source=fallback_per_tier` |
| 单文件扫描超预算（>18） | 截断至 18 内最优，记 `truncated=true` |
| 跨档污染门 FAIL（G2） | 全局 STOP，不得调参绕过（AGENTS.md §10.1） |
| 需求歧义/未覆盖的冻结基线改动冲动 | 返回 planner / OpenSpec，不猜测 |

## 7. 门定义（阈值数值待冻结，结构先行）

### 7.1 G_adaptive — 增长披露门（主披露，不阻断归档）

- **输入**：4 点的 `ΔPIE = PIE_adaptive_opt − PIE_frozen_max` 分布（`_adaptive_vs_frozen.csv`）。
- **披露**（非 PASS/FAIL 硬门，结论措辞依据）：
  1. 均值 `mean ΔPIE`（预期 0.02–0.15 量级，若 >0 则“平均提升”）；
  2. 中位数 `median ΔPIE`；
  3. 正增益档占比 `frac(ΔPIE>0)`（4 档中 3/4、4/4 等）；
  4. Wilson 显著档数（`ΔPIE` 的 PIE 置信区间不重叠档数）。
- **失败处置**：若均值≤0 且正占比≤0.5，则结论为“自适应在冻结最优点位上未带来显著提升（不敏感区）”，仍可归档（ponytail lite：采纳“per-tier 最优已足够”简化结论）。

### 7.2 G_budget — 预算门

- 每文件物化次数 ≤18（Q3 冻结值）；
- 单文件扫描 wall-clock ≤60s（不含全链重跑译码；配对子预算 ≤1s/点，实测 0.31s 排序+0.5s/点）；
- 超限即截断并记 `truncated`，不记为硬门 FAIL，但需在 `budget_report.md` 中披露截断率。

### 7.3 复用门（沿用 fix-candidate / aggressive 终版语义）

- **G2 跨档字节唯一性**：同 (d,bw) 不同 `src_tag` 的 `a_eff/b_eff` sha256 零碰撞（硬门）。
- **G3 档位序**：档均值 ser 严格有序 `6>10>16>20`（硬门）；逐点倒置仅诊断，不门控（沿用 2026-08-26 lesson）。
- **G4 溯源完整性**：每个 sidecar 记录 `source_ttbin` 路径+sha256、`processing_rule_version`、`src_tag`、`pool_root` 指纹。

### 7.4 阈值冻结流程（Q1–Q4 + 4 点清单）

1. `/opsx-explore` 产出 `explore_report.md`（含 Q1 搜索空间、Q2 目标函数、Q3 预算、Q4 回退、G_adaptive 披露口径、**4 点 frozen max PIE 清单** `(loss,d,bw,blk,PIE)`）。
2. 主线在 T0 review 中冻结阈值写入 `evidence/gates_frozen.json`（`design.md §7` 附录镜像），后续 T1–T3 均以冻结值为准，不得执行期漂移。

## 8. 回退预案

| 触发 | 处置 |
|---|---|
| 任意硬门 FAIL（G2/G4/污染门）且非脚本 bug | **STOP**，产物就地保留，不得调参/重跑绕过；主线裁决是否修正扫描空间或终止变更 |
| G_adaptive 披露为无提升 | 不阻断归档；结论记为“4 点最优点位上自适应未显著超越 per-tier 最优”，产物与诊断表归档 |
| 单文件扫描失败 | 按 Q4=A 回退至 per-tier 最优锚，该文件 `fallback` 标记 |
| 4 点 frozen max 清单缺失或 ttbin 缺失 | 扫描器启动前断言失败，fail-closed，不进入扫描 |
| 对 `results/` 既有路径的写入 | 先取用户显式授权（AGENTS.md §5.2），否则拒绝 |
| 需求歧义 | 返回 planner / OpenSpec，不猜测（AGENTS.md §3） |

- **回退语义**：任何 STOP 均为**不可重跑/不可调参**的证据冻结（AGENTS.md §10.1）；修正需新 OpenSpec 或本变更的显式 amend 并重走 review-go。
- **ponytail lite 语义**：若 4 点扫描显示增益全落在 40ps 不敏感区内（Wilson 重叠），可直接采纳“per-tier 最优已足够，per-file 自适应非必需”简化结论，跳过扩展而直接归档（需 review-go 确认）。

## 9. 测试分层（对齐 AGENTS.md §10.1）

- **T0**：`compileall` + import + 默认路径等价断言 + 守卫 tamper（指向旧根应拒绝）+ 合成 ttbin 最小回路（patched reader，不触真实数据）+ frozen max 4 点清单存在性校验。
- **T1**：72 候选扫描 trace 完整性 + `G_adaptive` 披露 + 回退注入测试（人为注入单文件全失败应回退至 per-tier 锚）；合成 file 最小回路。
- **T2**：4 点最优全链重跑 + `_adaptive_vs_frozen.csv` 行数/列对齐 + validator 对齐 + `beta` 非手填校验。
- **T3**：`old_vs_new` 对比回归（对照 frozen 最优趋势，不逐位）+ 固化表 schema 校验。

## 10. 与 explore 的衔接

- 本 design 的阈值/预算/搜索空间/4 点清单数值留空待 `explore_report.md` 落盘后在 T0 review 中冻结；在此之前 T1 不启动真实数据执行。
- 若 explore 发现更廉价的纯窗口寻优即可覆盖延时锚收益，则在报告中记录并由主线裁决是否收缩搜索空间（ponytail lite：以最小可用搜索为准）。

## 11. 加速与成本设计（复用 T0.7 实测）

- **配对非瓶颈**：共享排序 0.31s + Numba 双指针 0.5s/点，72 候选配对 <1m；**瓶颈在 polar 译码** 30s/点，故 4 次重跑 ~2m，72 候选扫描 + 4 重跑总量 <5m。
- **保留**：Numba `njit` 双指针、共享排序、ThreadPool 留2核、batch 复用/增量续跑、薄封装。
- **降为按需**：Rust 备选、分层 4→121 细调（仅当 per-point>10s 或档全量>60m 时评估）。
- **重设门**：`G_scan_cost <1m/文件`（已达 0.17m）；`G_full_121 60m/档`（仅作全量参考，本变更 4 点不触发）。

## 附录 A. 自由度钉死清单（扫描时显式固定）

- `pairing_mode=nearest`, `processing_rule_version=pairing_v2`, `occupancy_filter=0`, `max_pairs=0`, `frame_len_symbols` 与 lossfix/aggressive 一致；`HDQKD_NEAREST_FRAME_THRESHOLD_PS` 保持默认 40000；`HDQKD_ALIGN_DEBUG=0`；JSON meta 的 `created_at` 不参与字节比对。
- 扫描器新增自由度仅限 §6.1 表内 3×6；其余自由度（`n, code_rate, scl` 等）不在扫描器内变动（`scl` 固定 4，除非 gates_frozen 显式授权 `scl ∈ {4,8}` 扩展）。

## 附录 B. 术语

- **per-tier 最优**：T1c sweep 产出的每档统一最优锚（当前全档 10ps）。
- **per-file 最优**：本变更扫描器为单文件（4 点各文件）选出的 18 候选内最优。
- **G_adaptive**：4 点 ΔPIE 披露门，结构复用 `G_scan` 但统计单元为档、样本仅 4。
- **frozen_max**：冻结基线 `polar_e2e_results.csv` 中每档 PIE_practical 最大行对应的点位。
