# Design: fix-aggressive-ir-collapse

> **关联诊断：`workspace/diag_6dB_collapse_20260828.md`（分支 `polar-aggressive-7x-recovery`，HEAD `847b768`）**
> 本 design 按 P0–P4 分节逐条对应诊断根因；门阈值冻结与回滚预案见 §8。

## 1. 总览与复用基线

- 本变更在 `polar-aggressive-7x-recovery` 的 `_aggressive_v1` 增量命名空间之上**原地修复**（不新增 `_v2` 后缀），复用其池 `key=(src_tag,d,bw,blk)` 与确定性重跑语义。
- 已落盘失真表 `results/paper_grade_aggressive_v1/.../loss_6dB` 121 行保留作对比基线（备份至 `*.bak_20260828/` 后覆盖重跑）。
- 研究代码工程策略（AGENTS.md §5.7）：不引入 SHA-256 清单/原子写/备份回滚重型机制；以 Git 基线 + 字节比对 + 结构化校验为准。
- 路径纪律（AGENTS.md §5.4）：优先 WSL/POSIX，遗留 Windows 绝对路径仅作溯源。

## 2. 命名与隔离（复用 _aggressive_v1）

```
results/real_sequences_aggressive_v1/<src_tag>/d{d}_bw{bw}/blk{b}/
    a_eff.npy, b_eff.npy, materialize_meta.json, seq_pair_stats.json

results/paper_grade_aggressive_v1/four_loss_parts_frames300_aggressive_v1/<loss_XXdB>/
    round1a_summary.txt, actual_ir_block_table.csv (P4后 per-block 130k行),
    security_calibrated_master_table.csv, polar_diag_summary.csv, polar_layer_metrics.csv
```

- `<src_tag> ∈ {loss20dB_t15, loss16dB, loss10dB, loss6dB}` 沿用 fix-candidate 映射；20dB 仅参照不重跑。
- 旧根 `results/paper_grade_v3` / `authoritative` / `authoritative_nsfix` / `paper_grade_v4_rate_search_fix` 只读。
- 驱动启动断言：`pool_root` 含 `aggressive_v1` 子串，否则 fail-closed（复用 `polar-aggressive-7x-recovery` design §2.3 守卫）。

## 3. P0 — fer_acceptance 阈值放宽（T1 引爆点直接开关）

**根因**：`diag §C1.2–C1.3` `one_sided_wilson_upper < 0.05` 对 `BER≈0.04 cap≈0.739` 的层判 `k=0`（`frozen=4096, fer_*` 空），仅 `BER<1e-4 fer_upper=0.042` 能过。

**设计**：

- `src/reconciliation/real_polar_sc_rescue.py` 将阈值外置为参数 `fer_threshold: float = 0.05` 与 `fer_rule: {one_sided_wilson_upper_lt_threshold, point_estimate_lt_threshold}`。
- 默认修复值：`fer_threshold=0.10`（与 `fix-candidate-loss-namespace` 前 lossfix 时期实测通过阈值对齐）+ 点估计对照分支 `fer_point_estimate = fer_errors/fer_trials < threshold`。
- `experiments/run_e2e_pipeline.py` 新增 `--fer-threshold` / `--fer-rule` 透传至 worker；不传参时与旧 `0.05/wilson` 逐字符一致（默认行为等价断言覆盖）。
- 校验：`--only-points 4,180 --debug-layer` 打印 `layer_ber/cap/k_best/fer_errors/fer_trials/fer_upper`；预期 `d4/bw180 L0` 在 `0.10` 下 `k>0`（对标 lossfix `k≈629`），`4096/180` 保持 `k≈2021` 不退化。

**冻结**：T0.5 试点择优 `wilson0.10` vs `point0.05`，胜者写入 `evidence/gates_frozen.json: G_fer.threshold`，后续 T1–T3 不漂移。

## 4. P1 — SC→SCL 自动 fallback（SCL 未尝试修复）

**根因**：`diag §C1.3` 847 层中 845 层 `decoder_mode_best=""`，`strategy_all_layers_failed_fer` 先于译码判死；`polar_e2e_results.csv` `layers_success_sc=0` 全 121 点，`layers_success_scl=1` 仅 2 点。

**设计**：

- `src/reconciliation/real_polar_sc_rescue.py` 新增 `decoder_modes: {sc, scl, auto-fallback}`；`auto-fallback` 语义：先 SC 搜索 `k`，若 `fer_upper≥threshold` 则自动以 SCL-16 重搜同一 `k` 候选（复用既有 `cpp_scl_wrapper`，不引入 GPU/FPGA）。
- `experiments/run_e2e_pipeline.py` 新增 `--decoder-modes auto-fallback`（默认 `auto-fallback` 修复后；旧行为 `sc` 可显式回退用于对照）。
- 记录：`polar_layer_metrics.csv` 每层 `decoder_mode_best ∈ {sc,scl}` 非空；`fer_trials=300` 固定（`frames300` 约束）。

**校验**：`4,180` 在 fallback 下 `decoder_mode_best=scl` 且 `k>0`；`layers_success_scl` 显著多于 2。

**回退**：若 SCL 膨胀 `leak_EC_actual_bits` 致 `PIE` 净负，则与 P0 阈值联调，必要时回退至 `sc` 对照分支（design §8）。

## 5. P2 — max_pairs 动态化（T0 首现 均匀化根因）

**根因**：`diag §C0.2–C0.3` `n_pairs=687388` 全 `d` 恒定 → `coincidence_rate` 同 `bw` 11d 一致（`bw20 168550.33`）、`raw_ser` 跨 `d` 趋同。

**设计**：

- `src/workflow/export_joint_sequence_sidecar.py` `materialize_real_sequences_for_point(..., max_pairs: int|str = 0)` 语义：
  - `0` = 解固定截断，按真实 TTbin `candidate pairs` 全量（预期 lossfix 分布回归）；
  - `auto` = 按 `d×bw` 等比截断 `max_pairs = base_pairs * (d*bw)/(d0*bw0)`（`base_pairs` 取 `d=4,bw=20` 的 TTbin 实测值，避免大 `d` OOM）；
  - 旧硬编码 `687388` 仅作回归对照值保留，不再默认。
- `experiments/run_e2e_pipeline.py` 新增 `--max-pairs {0,auto,<int>}`。
- 校验：`seq_pair_stats.json` `n_pairs` 随 `d` 递减（例 `bw180: d4≈224k vs d4096≈687k` 量级分叉回归 lossfix `d4 224k / d4096 ~687k` 的 `bw` 相关分布）；`_tmp_grid_table.csv` `coincidence_rate uniq>1 per bw`；`frame_period_ps = d*bw` 显式记录于 `sidecar_meta.json`。

**回退**：若 `0` 致 `d4096` 内存超限，自动降级至 `auto` 等比（§8）。

## 6. P3 — map_ser / peak_sigma 归一化校正（偏高 0.02 修复）

**根因**：`diag §C0.1` 同点 `map_ser +0.02`（`d4/bw180 0.0886 vs 0.0694`）、`peak_sigma 53.7 vs 150.24` 随 `d` 的 `gate_width_ps==bw` 归一化不一致。

**设计**：

- `src/workflow/export_joint_sequence_sidecar.py` 排查 `delta_mode / near_neighbor_frac / peak_sigma_ps` 计算中 `gate_width_ps / frame_period_ps / peak_to_bg` 的 `d` 归一化；
- 校正：`map_ser = raw_ser * (1 + walk_coeff * peak_sigma/gate_width)` 类走查（具体系数以代码走读为准，不预设公式），使 `d4` 与 `d4096` 在同 `bw` 下 `map_ser` 分叉回归 lossfix `≈0.02` 差值以内。
- 记录 `peak_sigma_ps / peak_center_ps / peak_to_bg` 于 `polar_diag_summary.csv`（已存在，仅校验其随 `d` 单调性）。

**校验**：`4,180` vs `4096,180` 的 `map_ser` 在修复后差值与 lossfix 同点差值一致（`±0.01` 容差），不跨 `0.1` 阈值误判。

**回退**：若校正过度致大 `d` SER 低估，则回退至仅 P2 修复的 `map_ser`（P3 标记 `non_promoted`）。

## 7. P4 — per-block 130k 行对齐（121 行汇总 → 明细）

**根因**：`diag §C2.1` `actual_ir_block_table.csv` aggressive 121 行汇总 vs lossfix 130253 行 per-block 明细；`beta=0` 时无法细粒度复盘 `k/rate/leak/block_success`。

**设计**：

- `experiments/run_e2e_pipeline.py` 的 `actual_ir` 落盘恢复为 per-block 明细：每 `(d,bw,layer,block)` 一行，列 `point_id, d, bw, layer_idx, block_index, decoder_mode_used, k_used, rate_used, total_leak_ec_bits, block_success_flag, fer_upper`（对齐 lossfix `stage1_actual_ir` schema）。
- 加汇总视图 `actual_ir_block_summary.csv`（121 行，`mean beta / PIE`）供门快速校验；主表为明细 `130k±` 行（`121点×平均层×300帧`）。
- 兼容：`security_calibrated_master_table.csv` 仍以汇总行为主，不改其 schema。

**校验**：`loss_6dB/actual_ir_block_table.csv` 行数 `≈130k`（容差 ±5%），`block_success_flag=1` 占比与 `polar_layer_metrics rescue_success` 一致；`beta_eff_empirical` 由明细 `Σk / Σleak` 推导可复现。

## 8. 门阈值冻结更新与回滚预案

### 8.1 门定义

| 门 | 语义 | 阈值来源 | 硬条件 |
|---|---|---|---|
| **G0** | ttbin 存在性+sha256 抽验 | 复用 fix-candidate | FAIL→STOP |
| **G1** | 每档 ≥3 格双跑字节一致 | 复用 | FAIL→STOP |
| **G2** | 跨档字节唯一性 `a_eff/b_eff` 零碰撞（~574 组） | 复用 | FAIL→STOP |
| **G3** | 档均值 `ser` 严格有序 `6>10>16>20` | 复用（逐格倒置仅诊断） | FAIL→STOP |
| **G4** | 溯源完整 `source_ttbin/sha256/processing_rule_version/pairing_path` | 复用 | FAIL→STOP |
| **G_timing** | 锚定一致性（若启用 `delay_override`） | 复用 polar-aggressive | 诊断 |
| **G_growth** | 新 vs 失真旧 6dB 的 `ΔPIE` 均值/中位数/正占比 | **T0.5 冻结**（§8.2） | PASS 方可进 T2 |
| **G_pairing** | `coincidence_rate uniq>1 per bw` 且 `n_pairs` 随 `d` 单调分叉 | T0.5 冻结 | FAIL→P2 回退 |
| **G_fer** | `fer_threshold/rule` 冻结值（`0.10/wilson` 或 `point` 胜者） | T0.5 冻结 | 后续不漂移 |

### 8.2 冻结流程（T0.5 完成）

1. T0.5 小点以 `fer_threshold ∈ {0.05,0.10}` × `fer_rule ∈ {wilson,point}` × `max_pairs ∈ {0,auto}` 做 2×2×2=8 组对照（仅 2 点，轻量）。
2. 择优写入 `openspec/changes/fix-aggressive-ir-collapse/evidence/gates_frozen.json`（含 `G_fer.threshold/rule`、`G_growth` 三阈值、`G_pairing` 期望 uniq 数、`max_pairs` 策略）。
3. 主线 review 冻结后 T1–T5 以此为准，不得执行期漂移。

### 8.3 回滚预案

| 触发 | 处置 |
|---|---|
| 任一门 FAIL 且非脚本 bug | **STOP**，产物就地保留，不得调参绕过；主线裁决（AGENTS.md §10.1） |
| `max_pairs=0` OOM | 降级 `max_pairs=auto` 等比截断 |
| `fer_threshold=0.10` 致 FER 膨胀 | 切 `fer_rule=point` 对照分支，以 evidence 择优 |
| P3 过校正致大 `d` SER 低估 | P3 标记 `non_promoted`，仅 P2 生效 |
| `actual_ir` 明细落盘过大（>500MB/档） | 仅对 6dB 全量明细，10/16/20dB 先汇总 121 行，明细按需抽样 |
| 对 `results/` 既有路径的非备份覆盖 | 先取用户显式授权（AGENTS.md §5.2），否则拒绝 |
| 需求歧义/未覆盖的冻结基线改动冲动 | 返回 planner / OpenSpec，不猜测 |

## 9. 并发与资源

- 主机 20 逻辑核，**留 2 核**：`--jobs 18`（或 `workers=12, metric-jobs=12, shards=16` 等价，见 `fix-candidate-loss-namespace/evidence/phase4_launch_config.md` 基准），记入 `evidence/*_launch_config.md` 溯源。
- 全量 `121×4` 按 `6→10→16→20` 串行分档重跑，避免峰值 RSS 超限；`n=4096` 大帧优先。
- 科学参数冻结：`frames300 / seed20260228 / tag_bits64 / shards16` 不变。

## 10. 验证链

```
T0.5 小点 (4,180 vs 4096,180) --debug-layer 8组对照
  → gates_frozen.json 冻结
  → T1 6dB 全量 121/121 验证 SER分叉/k>0/β≈0.7-0.8
  → T2 10/16/20dB 全量 363/363
  → T3 G0-G4全门 + old_vs_new 484行对比
```

- 每阶段产物落 `openspec/changes/fix-aggressive-ir-collapse/evidence/`（`T0_5_* / T1_* / T2_* / T3_*` 前缀）。
- 旧失真表备份：`results/paper_grade_aggressive_v1/.../loss_6dB/*.bak_20260828/`（`cp -r` 后覆盖）。

## 11. 自由度钉死清单（重跑时显式固定）

- `pairing_mode=nearest`, `processing_rule_version=pairing_v2`, `occupancy_filter=0`, `frame_len_symbols` 与 lossfix 一致；`HDQKD_NEAREST_FRAME_THRESHOLD_PS=40000` 默认；`HDQKD_ALIGN_DEBUG=0`；`visibility_assumed=0.95`。
- `max_pairs`/`fer_threshold`/`fer_rule`/`decoder_modes` 以 `gates_frozen.json` 为准，命令行显式传入并记入 `sidecar_meta.json` 与 `run_manifest.json`。

## 附录 A. 与 explore 的衔接

- 本 design 阈值数值留空待 T0.5 小点报告落盘后在 review 中冻结；在此之前 T1 不启动真实数据全量执行。
- 若 explore 发现更廉价的纯 `max_pairs=0` 即可覆盖 `map_ser` 校正收益，则在证据中记录并由主线裁决是否跳过 P3（ponytail lite：以最小可用校正为准）。
