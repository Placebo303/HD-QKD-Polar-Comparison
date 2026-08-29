# Design: polar-aggressive-7x-recovery

## 1. 总览与复用基线

- 本变更在 `fix-candidate-loss-namespace` 已验证的 lossfix 命名空间与 `G0–G4` 门体系之上叠加激进恢复层；复用其池 key 约束（`(src_tag,d,bw,blk)`）与确定性重跑语义。
- 全部新增产物与旧产物**物理隔离**（§2 三目录分离 + §5 增量命名），任何对 `results/` 既有路径的覆盖冲动先取授权（tasks Stop Rules）。
- 研究代码工程策略（AGENTS.md §5.7）约束：不引入 SHA-256 清单/原子写/备份回滚等重型机制；以 Git 基线 + 字节比对 + 结构化校验为准。

## 2. 命名空间 `_aggressive_v1` 与三目录分离

### 2.1 增量命名

- 后缀：`_aggressive_v1`（Q5 已批准）。任何新目录/文件与同名 lossfix/v3 产物仅以后缀区分，禁止无后缀写入。

### 2.2 三目录物理隔离（与 lossfix 旧根零交集）

```
results/real_sequences_aggressive_v1/<src_tag>/d{d}_bw{bw}/blk{b}/
    a_eff.npy, b_eff.npy, materialize_meta.json

results/authoritative_aggressive_v1/e2e_<tier>_fullgrid_pairing_v2_candidate_aggressive_v1/
    sidecars/ , grid_tables/ , MANIFEST.csv

results/paper_grade_aggressive_v1/four_loss_parts_frames300_aggressive_v1/<loss_XXdB>/
    round1a_summary.txt , actual_ir_block_table.csv , security_calibrated_master_table.csv
```

- `<src_tag> ∈ {loss20dB_t15, loss16dB, loss10dB, loss6dB}`（沿用 fix-candidate 映射；loss20dB 仅作参照，不重建）。
- 旧根 `results/real_sequences/`、`results/real_sequences_ns/`、`results/authoritative_nsfix/`、`results/paper_grade_v4_rate_search_fix/` 保持只读；新根永不回写旧根。
- WSL 等价：`$PROJECT_RESULTS_ROOT/real_sequences_aggressive_v1` 等（AGENTS.md §5.4 路径纪律）。

### 2.3 隔离校验

- 驱动脚本启动时断言：`pool_root` 必须包含 `aggressive_v1` 子串；`out_root`/`candidate_dir` 同理；否则 fail-closed。
- T0/T1 含 tamper 测试：人为指向旧根应被守卫拒绝。

## 3. 最小改动清单（冻结基线触碰面，Q7 约束）

> **原则**：仅新增可选透传参数，默认行为逐字节兼容旧调用；任何超出清单的改动需另起 OpenSpec + review-go 三阶（Q7）。

| 文件 | 改动 | 默认行为 |
|---|---|---|
| `src/workflow/export_joint_sequence_sidecar.py` | `materialize_real_sequences_for_point(...)` 与 `export_sidecar_for_point(...)` 增 `pool_root: str\|None = None`, `delay_override: int\|None = None`, `calibration_table: Path\|None = None`；池路径 `base = Path(pool_root) if pool_root else legacy`；`used_delay_ps = delay_override if not None else peak_center_ps`；死时校正查表 `calibration_table[src_tag][d][bw]` 应用于 `pairing_window / singles` 校正 | 三参数皆 `None` 时与旧硬编码路径/自动锚定/无校正逐字符一致 |
| `experiments/run_e2e_pipeline.py` | 新增 `--real-seq-pool-root`, `--delay-override-ps`, `--calibration-table` CLI 旗标，透传至 `_run_extract_batch` → worker init → export 调用 | 不传参时与旧 CLI 等价 |
| `tools/materialize_aggressive_candidates.py` | **新文件**：按档循环设 `HDQKD_TTBIN_FILE_OVERRIDE` + `pool_root` + `out_root` + `calibration_table`，钉死 `pairing_mode=nearest / pairing_v2 / occupancy_filter=0 / max_pairs=0` 等自由度 | — |
| `tools/build_calibration_table.py` | **新文件**：从 `ttbin_metrics.json` 单光子率/通量拟合死时/堆积/游走校正表 | — |
| `tools/verify_aggressive_gates.py` | **新文件**：`G_growth / G_timing / G0–G4` 复用 | — |

- 单元断言（T0）：不传参时 `materialize_out_dir` 与旧硬编码路径逐字符一致；`delay_override=None` 时 `used_delay_ps == peak_center_ps`。
- 未在清单中的文件（`src/reconciliation/*`, `tools/longrun_*`, `comparison_bench/*`）**禁止**修改。

## 4. 新 G_growth 门定义（Q6 按 explore 报告建议）

> 阈值以 `explore` 阶段报告落盘为准（`openspec/changes/polar-aggressive-7x-recovery/explore_report.md`），此处冻结门结构与判定语义，T1 前完成阈值数值冻结。

### 4.1 G_growth — 增长门（主门，决定是否由试点进入 C1b/C1c 与全量）

- **输入**：8 格试点（C1a）的 `PIE_reconciled_net` / `SKR_reconciled_net_bps` 与 lossfix 同格对照；或 12 格验证（C1b）的增量分布。
- **判定**（满足任一即 PASS，进入下一阶段；否则 STOP）：
  1. 试点格均值 `ΔPIE = mean(PIE_aggressive − PIE_lossfix)` ≥ `G_growth.mean_delta_PIE`（explore 建议值，预期 0.1–0.3 bits/sym 量级）；
  2. 或中位数 `median ΔPIE` ≥ `G_growth.median_delta_PIE`；
  3. 或正增益格占比 `frac(ΔPIE > 0)` ≥ `G_growth.positive_frac`（explore 建议 6/8 或 7/8）。
- **离群隔离**：16dB d=2048 相关格（Q8）不计入上述均值/中位数，仅单独标注分析。
- **失败处置**：G_growth FAIL ⇒ 就地 STOP，不得调参绕过；产物与诊断表归档，交主线裁决是否进入 C1b 修正或直接终止。

### 4.2 G_timing — 定时一致性门（C1a/C1b 专用）

- **跨档字节唯一性**（复用 lossfix G2）：同 (d,bw) 不同 src_tag 的 `a_eff/b_eff` sha256 零碰撞。
- **档位序单调性**：档均值 ser 严格有序 `6 > 10 > 16 > 20`（复用 lossfix G3 终版硬条件）；逐格倒置仅诊断，不门控（沿用 2026-08-26 lesson）。
- **锚定一致性**：固定锚模式下 `used_delay_ps` 在同格多次物化中字节一致；`sidecar_meta.json` 记录 `delay_override` 与 `calibration_table` 指纹。

### 4.3 复用门（沿用 fix-candidate 终版语义）

- **G0 预检**：ttbin 存在性 + sha256 + 归档指纹抽验。
- **G1 确定性**：每档 ≥3 格双跑物化字节一致。
- **G4 溯源完整性**：每个 sidecar 记录 `source_ttbin` 路径+sha256、`processing_rule_version`、`src_tag`、`pool_root` 指纹。

### 4.4 阈值冻结流程（Q6）

1. `/opsx-explore` 产出 `explore_report.md`（含 `G_growth` 三阈值建议 + `Q8` 离群判定依据）。
2. 主线在 T0 review 中冻结阈值写入 `design.md §4` 附录（或独立 `gates_frozen.json`），后续 T1–T5 均以冻结值为准，不得执行期漂移。

## 5. 输出落盘（增量命名，不覆盖）

| 产物 | 路径（增量命名） | 内容 |
|---|---|---|
| 新池 MANIFEST | `results/real_sequences_aggressive_v1/MANIFEST.csv` | `src_tag,d,bw,blk,ttbin_path,ttbin_sha256,a_eff_sha256,b_eff_sha256,delay_override,calibration_table_sha256,params_tag` |
| 新候选 | `results/authoritative_aggressive_v1/e2e_<tier>_fullgrid_pairing_v2_candidate_aggressive_v1/` | `sidecars/`, `MANIFEST.csv`, `grid_tables/` |
| 重跑产物 | `results/paper_grade_aggressive_v1/four_loss_parts_frames300_aggressive_v1/` | 每档 `round1a_summary.txt`, `actual_ir_block_table.csv`, `security_calibrated_master_table.csv` |
| 校准表 | `results/real_sequences_aggressive_v1/calib/calibration_table_aggressive_v1.json` | per-tier/per-rate 死时参数 |
| 门证据 | `openspec/changes/polar-aggressive-7x-recovery/evidence/` | `G0–G4`, `G_growth`, `G_timing` 报告 + 8/12/全量诊断表 |
| 探索报告 | `openspec/changes/polar-aggressive-7x-recovery/explore_report.md` | Q6 阈值 + Q8 离群依据 |

- 旧 `results/paper_grade_v3/`, `results/authoritative/`, `four_loss_parts_frames300_lossfix_v1/` 保持只读；新旧对比仅通过只读脚本生成 `old_vs_new` 报告，不回写旧目录。

## 6. 回退预案

| 触发 | 处置 |
|---|---|
| 任意门 FAIL（G_growth/G_timing/G0–G4）且非脚本 bug | **STOP**，产物就地保留，不得调参/重跑绕过；主线裁决是否修正校准表或终止变更 |
| 需求歧义/未覆盖的冻结基线改动冲动 | 返回 planner / OpenSpec，不猜测（AGENTS.md §3） |
| 校准表拟合发散或 8 格试点零增益 | 回退至 C1a 固定锚纯对照（无校准），G_growth 仍按冻结阈值判定；若仍 FAIL 则终止 C1b/C1c |
| C2 Tal-Vardy 轻版无增益 | 不进入全 GA；保留轻版证据，C2 标记 `non_promoted`，仅 C1 产物进入 T5 审计 |
| 16dB d2048 离群恶化 | 该格隔离标注，不纳入全量均值门；单独诊断 `peak_sigma` / `singles` 遥测 |
| 对 `results/` 既有路径的写入 | 先取用户显式授权（AGENTS.md §5.2），否则拒绝 |

- **回退语义**：任何 STOP 均为**不可重跑/不可调参**的证据冻结（沿用 AGENTS.md §10.1 科学门纪律）；修正需新 OpenSpec 或本变更的显式 amend 并重走 review-go。
- **探索期回退**（ponytail lite 语义）：若 C1a 8 格试点度量显示档间 ser 差收窄 < 预期且 IAB 无提升，可直接采纳“固定锚有益但校准表非必需”的简化结论，跳过 C1b 深度校准而进入 C1c/C2。

## 7. 测试分层（对齐 AGENTS.md §10.1）

- **T0**：`compileall` + import + 默认路径等价断言 + 守卫 tamper（指向旧根应拒绝）。
- **T1**：G1 双跑一致性 + G_timing 锚定一致性 tamper（注入 `delay_override` 漂移应 FAIL）+ 合成 ttbin 最小回路（patched reader，不触真实数据）。
- **T2**：真实 ttbin 小样试点（≤12 格）端到端物化 + 门校验；通过后再扩量。
- **T3**：全量物化 + 跨档对比回归（对照 lossfix 趋势，不逐位）。

## 8. 与 explore 的衔接

- 本 design 的阈值数值留空待 `explore_report.md` 落盘后在 T0 review 中冻结；在此之前 T1 不启动真实数据执行。
- 若 explore 发现更廉价的纯窗口寻优即可覆盖死时校正收益，则在报告中记录并由主线裁决是否跳过 C1b（ponytail lite：以最小可用校正为准）。

## 附录 A. 自由度钉死清单（重跑时显式固定）

- `pairing_mode=nearest`, `processing_rule_version=pairing_v2`, `occupancy_filter=0`, `max_pairs=0`, `frame_len_symbols` 与 lossfix 一致；`HDQKD_NEAREST_FRAME_THRESHOLD_PS` 保持默认 40000；`HDQKD_ALIGN_DEBUG=0`；JSON meta 的 `created_at` 不参与字节比对。
