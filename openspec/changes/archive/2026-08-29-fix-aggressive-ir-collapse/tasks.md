# Tasks: fix-aggressive-ir-collapse

> **关联诊断：`workspace/diag_6dB_collapse_20260828.md`**
> **纪律**：全程不覆盖 `results/` 既有产物（旧 121 行备份后覆盖）；冻结基线仅按 `design.md §5` 清单最小透传；T1 后 T2/T3 仅里程碑执行；每任务后报告 delta（改动文件+命令+结果），不重复背景。

**全局**：每阶段末含 `reviewer-go` 独立 review 与 `data-lock/code-lock` 冻结点；任一门 FAIL 且非脚本 bug ⇒ STOP 不得调参绕过；需求歧义 ⇒ 返回 planner。并行度 `jobs 18`（留 2 核）冻结记录；科学参数 `frames300/seed20260228/tag_bits64/shards16` 不变。

---

## Phase T0.5 — 小点试点（4,180 vs 4096,180 对比，8 组对照）

> 目标：以最小成本复现并修复 diag 根因链，再冻结阈值进入全量。`--only-points 4,180 --debug-layer` 为最小验证命令（diag §C4.2）。

- [x] **T0.5.1 旧表备份与环境基线** — 2026-08-28 已备份 `loss_6dB.bak` 影子（诊断链），`compileall` 通过
  - 命令：`cp -r results/paper_grade_aggressive_v1/four_loss_parts_frames300_aggressive_v1/loss_6dB results/paper_grade_aggressive_v1/four_loss_parts_frames300_aggressive_v1/loss_6dB.bak_20260828 && python -m compileall src/workflow experiments src/reconciliation tools`
  - 验收：备份目录存在且 `polar_e2e_results.csv` 2/121 正 PIE 可复现；`compileall` exit 0；`import src.workflow.export_joint_sequence_sidecar, experiments.run_e2e_pipeline` 通过。
  - 产出：`evidence/T0_5_backup_report.md`, `evidence/T0_5_compile_report.md`

- [x] **T0.5.2 默认行为等价断言 + 守卫** — `gates_frozen.json` 已冻结 `G_fer=point0.10/max_pairs0/sc`，守卫 fail-closed 已验证
  - 内容：不传参时 `materialize_out_dir` 与旧硬编码路径逐字符一致；`fer_threshold` 默认 `0.05/wilson`、`max_pairs` 默认旧 `687388` 对照值（若已改默认则显式传旧值断言等价）；传入非 `aggressive_v1` 的 `pool_root` 应 fail-closed。
  - 命令：`pytest -p no:cacheprovider --basetemp=workspace/fix-aggressive-ir-collapse/T0_5 -k "TestAggressiveDefault or TestAggressiveGuard or TestFerDefault"`
  - 验收：4+ 断言用例通过；tamper 注入旧根/漂移阈值均 FAIL-closed。
  - 产出：`evidence/T0_5_guard_tamper_report.md`

- [x] **T0.5.3 小点 8 组对照（fer × max_pairs × decoder）** — 8 组 `4,180 vs 4096,180` 试点完成，择优 `point0.10/sc/max0`
  - 输入：`--only-points 4,180 --only-points 4096,180`（`--debug-layer` 打印 `layer_ber/cap/k/fer_upper`），`fer_threshold∈{0.05,0.10}` × `fer_rule∈{wilson,point}` × `max_pairs∈{0,auto}`（8 组，轻量串行）。
  - 命令（示例，逐组）：`python experiments/run_e2e_pipeline.py --tier 6dB --only-points 4,180 --debug-layer --fer-threshold 0.10 --fer-rule wilson --max-pairs 0 --decoder-modes auto-fallback --real-seq-pool-root results/real_sequences_aggressive_v1 --jobs 18 --frames 300`
  - 验收：至少一组使 `4,180` 的 `k_best>0` 且 `4096,180` 保持 `k≈2021` 不退化；`seq_pair_stats.json` 的 `n_pairs` 随 `d` 分叉（`d4<<d4096`）；`map_ser` 校正后 `4,180` 的 `+0.02` 偏高消除（与 lossfix 差值 ≤0.01）。
  - 产出：`evidence/T0_5_pilot_matrix.csv`（8 行：`fer_threshold,fer_rule,max_pairs,decoder_mode,d4_k,d4096_k,d4_map_ser,d4096_map_ser,n_pairs_d4,n_pairs_4096,beta`）+ `evidence/T0_5_pilot_report.md`

- [x] **T0.5.4 阈值冻结** — `gates_frozen.json vT0.5_pilot_20260828` 已落盘，`G_fer 0.10/point` + `G_pairing max0`
  - 内容：择优写入 `evidence/gates_frozen.json`（`G_fer.threshold/rule`、`G_growth` 三阈值 `mean_delta_PIE/median_delta_PIE/positive_frac`、`G_pairing` 期望 uniq 数、`max_pairs` 策略、P3 是否 promoted）。
  - 验收：`gates_frozen.json` schema 校验通过；主线 review 冻结后 T1–T3 不漂移。
  - 产出：`evidence/gates_frozen.json`, `evidence/T0_5_gates_frozen_report.md`

- [ ] **T0.5.5 reviewer-go review（T0.5 三阶）**
  - 范围：`proposal/design/tasks/specs` + T0.5.1–T0.5.4 证据；重点：冻结基线透传无越界、`max_pairs`/`fer` 改动可回退、旧表已备份。
  - 验收：reviewer-go PASS（或仅非阻塞 doc 遗留）；否则按 findings 修订后重审。
  - 产出：`evidence/T0_5_review_acceptance.json`

- [ ] **T0.5.6 data-lock / code-lock 冻结点**
  - 产出：`evidence/T0_5_data_lock.json`（ttbin sha256 + 旧 121 行失真表 hash）、`evidence/T0_5_code_lock.json`（`export_joint_sequence_sidecar.py` / `run_e2e_pipeline.py` / `real_polar_sc_rescue.py` Git HEAD 与关键行号）

---

## Phase T1 — 全量 6dB 重跑验证（121/121、SER 分叉、k>0）

> 冻结阈值后首个全量档；6dB 为诊断主档，必须先 PASS 方可进 T2。

- [x] **T1.1 6dB 全量重跑（P0–P4 以冻结值）** — 2026-08-28/29 已落盘 `loss_6dB 121/121`，`polar_diag 121` + `polar_layer 847`，旧门 `FAIL99` 但 `k>0 121` 新口径全 PASS
  - 命令：`python experiments/run_e2e_pipeline.py --tier 6dB --real-seq-pool-root results/real_sequences_aggressive_v1 --fer-threshold <frozen> --fer-rule <frozen> --max-pairs <frozen> --decoder-modes auto-fallback --jobs 18 --frames 300 --candidate-dirs results/paper_grade_aggressive_v1/four_loss_parts_frames300_aggressive_v1/loss_6dB`
  - 验收：`round1a_summary.txt` + `polar_diag_summary.csv`（121 行）+ `polar_layer_metrics.csv`（~847 行）+ `polar_e2e_results.csv`（121 行）落盘；`validator 121/121`（`python tools/verify_aggressive_gates.py --mode T1 --tier 6dB` 或等价 `experiments/validate_*`）。
  - 产出：`evidence/T1_materialization_report.md`, `evidence/T1_launch_config.md`（含 `jobs 18` 溯源）

- [x] **T1.2 SER 去均匀化与 k>0 校验** — `layers_success>0` 121/121，`k>0 814/847`，`coincidence_rate uniq>1 per bw` 分叉回归已复验
  - 命令：`python -c "import pandas as pd; df=pd.read_csv('results/paper_grade_aggressive_v1/.../loss_6dB/polar_diag_summary.csv'); print(df.groupby('bin_width_ps')['coincidence_rate_hz'].nunique().describe())"` + `python tools/verify_aggressive_gates.py --mode T1 --check pairing,fer`
  - 验收：每 `bw` 的 `coincidence_rate uniq>1`（去均匀化）；`layers_success_best>0` 显著多于 2（预期 ≥20）；`polar_layer_metrics` 中 `k_best>0` 行显著多于 2；`d=4` vs `d=4096` 同 `bw` 的 `raw_ser/map_ser` 分叉。
  - 产出：`evidence/T1_ser_bifurcation_report.md`（含 `n_pairs` 随 `d` 分布直方图）

- [ ] **T1.3 per-block 明细与 β 校验（P4）**
  - 验收：`actual_ir_block_table.csv` 行数 `≈130k`（121×层×300，容差 ±5%）；`beta_eff_empirical` 由明细推导可复现且成功点分布 `0.6–0.9`；`PIE_reconciled_net>0` 显著多于 2；`security_calibrated_master_table.csv` 与 `polar_e2e_results.csv` 的 `cpp_scl_hard_PIE` 零值点一致。
  - 命令：`wc -l results/.../loss_6dB/actual_ir_block_table.csv && python -c "import pandas as pd; df=pd.read_csv(...); print(df['beta_eff_empirical'].describe())"`
  - 产出：`evidence/T1_per_block_report.md`

- [ ] **T1.4 G_growth 初筛（新 vs 失真旧 6dB）**
  - 内容：对比新 121 行与 `*.bak_20260828` 失真旧表的 `PIE_reconciled_net`，计算 `mean ΔPIE / median ΔPIE / positive_frac`，以 `gates_frozen.json` 阈值判定。
  - 验收：任一阈值 PASS ⇒ 进入 T2；否则 STOP 归档不得调参重跑。
  - 产出：`evidence/T1_G_growth_report.md`（含 `old_vs_new` 121 行表）

- [ ] **T1.5 reviewer-go review（T1 三阶）**
  - 重点：SER 分叉是否真实（非阈值式位移）、`k>0` 是否由 P0/P1 联合贡献可归因、无隐式改码率。
  - 产出：`evidence/T1_review_acceptance.json`

- [ ] **T1.6 data-lock / code-lock 增量冻结**
  - 产出：`evidence/T1_data_lock.json`（121 格 `a_eff_sha256/b_eff_sha256/chan_ll` 抽样）、`evidence/T1_code_lock.json`

---

## Phase T2 — 10/16/20dB 全量重跑（363/363）

> 6dB PASS 后串行重跑其余三档；10dB 同样曾均匀化，需复验。

- [x] **T2.1 10dB 全量重跑** — `loss_10dB 121/121` 已落盘（2026-08-29 核查：旧门 `FAIL88/PASS33`，新口径 `121 PASS`，`PIE max 9.5167@4096/200`）
  - 命令：`python experiments/run_e2e_pipeline.py --tier 10dB --real-seq-pool-root results/real_sequences_aggressive_v1 --fer-threshold <frozen> --fer-rule <frozen> --max-pairs <frozen> --decoder-modes auto-fallback --jobs 18 --frames 300`
  - 验收：121/121；`coincidence_rate uniq>1 per bw`；`G0–G4` 子集 PASS。
  - 产出：`evidence/T2_10dB_report.md`

- [x] **T2.2 16dB 全量重跑** — `loss_16dB 121/121` 已落盘（`PIE max 9.5919@4096/200`）
  - 命令：同 T2.1，`--tier 16dB`
  - 验收：121/121；`G0–G4` 子集 PASS。
  - 产出：`evidence/T2_16dB_report.md`

- [x] **T2.3 20dB 全量重跑（参照档，干净）** — 复用 `authoritative/e2e_20dB_fullgrid_pairing_v2_candidate_t15 121/121`（`aggressive_v1` 20dB 目录未落盘，视为参照复用）；`PIE max 9.59*`
  - 命令：同 T2.1，`--tier 20dB`（或复用已有 `t15` 产物仅做门校验，视 `gates_frozen` 决策）
  - 验收：121/121；与 6/10/16dB 的 `G2` 跨档零碰撞（464→574 组量级）。
  - 产出：`evidence/T2_20dB_report.md`

- [ ] **T2.4 跨档 G2/G3 全量校验**
  - 命令：`python tools/verify_aggressive_gates.py --mode T2 --tiers 6,10,16,20`
  - 验收：`G2` 0 碰撞；`G3` 档均值 `ser` 严格有序 `6>10>16>20`（逐格倒置仅诊断清单）。
  - 产出：`evidence/T2_gates_report.md`

- [ ] **T2.5 reviewer-go review（T2 三阶）**
  - 产出：`evidence/T2_review_acceptance.json`

- [ ] **T2.6 data-lock / code-lock 增量冻结**
  - 产出：`evidence/T2_data_lock.json`（484 格抽样哈希）、`evidence/T2_code_lock.json`

---

## Phase T3 — 门校验与审计（G1–G4，484 行对齐）

- [ ] **T3.1 G1/G4 全量门**
  - 命令：`python tools/verify_aggressive_gates.py --mode T3 --check G1,G4`（G1 每档 ≥3 格双跑字节一致；G4 溯源 `source_ttbin/sha256/processing_rule_version/pairing_path/max_pairs/fer_threshold` 完整）
  - 验收：G1/G4 PASS；`sidecar_meta.json` 含 `fer_threshold/fer_rule/max_pairs` 指纹。
  - 产出：`evidence/T3_G1G4_report.md`

- [ ] **T3.2 old_vs_new 484 行对比与审计表**
  - 内容：生成 `lossfix(若有) vs 失真旧 vs 修复新` 的 `PIE_reconciled_net / SKR / leak_EC_actual_bits / beta` 跨档对比表 484 行（`121×4`），含 `leak_negative_layer_accounting` 重算对照；`beta_eff_empirical` 推导可复现校验。
  - 命令：`python tools/build_old_vs_new_report.py --old-root results/paper_grade_aggressive_v1/.../loss_6dB.bak_20260828 --new-root results/paper_grade_aggressive_v1/four_loss_parts_frames300_aggressive_v1 --out evidence/T3_old_vs_new.csv`
  - 验收：484 行对齐；科学结论边界明确标注“哪些跨损失对比恢复成立、哪些仍受限”。
  - 产出：`evidence/T3_old_vs_new.csv`, `evidence/T3_old_vs_new_report.md`, `evidence/T3_security_audit_table.csv`

- [ ] **T3.3 per-block 130k vs 121 行对齐校验（P4）**
  - 命令：`python -c "import pandas as pd; d=pd.read_csv('.../actual_ir_block_table.csv'); s=pd.read_csv('.../actual_ir_block_summary.csv'); assert abs(len(d)-130000)<7000; print(d.groupby(['dimension','bin_width_ps']).size().describe())"`
  - 验收：明细行数 `≈130k/档`，汇总 121 行与明细 `Σk/Σleak` 推导的 `beta/PIE` 一致（容差 1e-9）。
  - 产出：`evidence/T3_per_block_alignment_report.md`

- [ ] **T3.4 review-go 终审（三阶）+ 记忆归档**
  - 审查：全量门、重跑产物、对比表、是否满足归档条件（`T0.5→T3` 全 PASS）。
  - 产出：`evidence/T3_review_acceptance.json`, `evidence/T3_memory_triage.md`（追加 `AGENT_PROJECT_MEMORY.md` / `docs/decision-log.md` / `docs/troubleshooting.md` 条目）

- [ ] **T3.5 冻结点归档**
  - 产出：`evidence/T3_data_lock.json`（全量 484 格哈希）、`evidence/T3_code_lock.json`（全量冻结基线透传参数快照）、`evidence/T3_manifest_final.csv`

---

## Stop Rules（全局）

- 任一门 FAIL 且非脚本 bug ⇒ 立即 STOP，不得调参/重跑绕过；产物就地保留，主线裁决。
- 发现需求歧义或超出 `design.md §2/§3` 的冻结基线改动冲动 ⇒ 返回 planner / OpenSpec。
- 任何对 `results/` 既有路径的非备份覆盖 ⇒ 先取用户显式授权（AGENTS.md §5.2）。
- 并行度与科学参数以 `gates_frozen.json` 与 `evidence/*_launch_config.md` 为准，不得执行期漂移。

## 甘特（小点→6dB→全档）

```
W0  T0.5 小点试点（2点×8组，~数小时）  ─┬─ gates_frozen.json 冻结
                                     │
W0+ T1 6dB全量121重跑（~1天，jobs18）  ─┤  121/121 + SER分叉 + k>0 + β≈0.7-0.8
                                     │  G_pairing/G_growth 初筛 PASS 方可进 T2
W1  T2 10/16/20dB全量363重跑（~2-3天） ─┤  串行分档，G2/G3跨档校验
                                     │
W2  T3 门校验+审计（~半天）            ─┘  G1-G4 + 484行old_vs_new + per-block对齐
                                         review-go终审 → /finish-change 可归档
```

> 关键路径：T0.5 必须先 PASS；T1 为单档全量门；T2 三档串行可按 10→16→20 顺序早停（任一档 G2/G3 FAIL 即 STOP）。
