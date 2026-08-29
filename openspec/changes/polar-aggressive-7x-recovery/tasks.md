# Tasks: polar-aggressive-7x-recovery

**约束**：全程不覆盖 `results/` 既有产物与事件证据；冻结基线仅按 `design.md §3` 最小透传清单修改；T2/T3 仅在里程碑执行；每个任务后报告 delta（改动文件+命令+结果），不重复背景。

**全局纪律**：每阶段末含 `reviewer-go` 独立 review 与 `data-lock / code-lock` 冻结点；任一门 FAIL 且非脚本 bug ⇒ STOP 不得调参绕过；需求歧义 ⇒ 返回 planner。

---

## Phase T0 — 编译 / import / 结构门 + 探索冻结

- [ ] **T0.1 compile/import 结构检查**
  - 命令：`python -m compileall src/workflow/experiments/tools comparison_bench` + `python -c "import src.workflow.export_joint_sequence_sidecar; import experiments.run_e2e_pipeline"`
  - 验收：exit 0；新增可选参数 `pool_root / delay_override / calibration_table` 存在且默认 `None`；旧调用路径未变。
  - 产出：`evidence/T0_compile_report.md`。

- [ ] **T0.2 默认行为等价断言 + 守卫 tamper**
  - 用合成 point 在 tmp 根断言：不传参时 `materialize_out_dir == REPO_ROOT/"results"/"real_sequences"/f"d{d}_bw{bw}"/f"blk{block_index}"` 逐字符一致；`delay_override=None` 时 `used_delay_ps == peak_center_ps`；传入旧根（无 `aggressive_v1` 子串）应被守卫拒绝。
  - 命令：`pytest -p no:cacheprovider --basetemp=workspace/polar-aggressive-7x-recovery/T0 -k "TestAggressiveDefault or TestAggressiveGuard"`
  - 验收：4+ 断言用例通过；tamper 注入旧根/漂移 delay 均 FAIL-closed。
  - 产出：`evidence/T0_guard_tamper_report.md`。

- [ ] **T0.3 explore 报告与阈值冻结（Q6/Q8）**
  - 执行 `/opsx-explore` 落盘 `explore_report.md`：含 `G_growth` 三阈值（`mean_delta_PIE / median_delta_PIE / positive_frac`）建议 + `16dB d2048` 离群判定依据（`peak_sigma / singles` 遥测 + 不纳入均值门理由）。
  - 主线在 review 中冻结阈值写入 `design.md §4` 附录或 `evidence/gates_frozen.json`，后续 T1–T5 以冻结值为准。
  - 产出：`explore_report.md` + `evidence/gates_frozen.json`。

- [ ] **T0.4 reviewer-go review（T0 三阶之二：候选交付审查）**
  - 审查范围：`proposal.md / design.md / tasks.md / specs/*.md` + T0.1–T0.3 证据；重点：Q7 最小透传清单无越界、Q5 命名隔离、三目录分离守卫、G_growth 结构冻结。
  - 验收：reviewer-go PASS（或仅非阻塞 doc 遗留）；否则按 findings 修订后重审。

- [ ] **T0.5 data-lock / code-lock 冻结点**
  - `data-lock`：记录四档 ttbin 主文件+`.1` 分片存在性、sha256、记录目录（`evidence/T0_data_lock.json`）；与 `fix-candidate` 时期一致。
  - `code-lock`：记录 `src/workflow/export_joint_sequence_sidecar.py` 与 `experiments/run_e2e_pipeline.py` 的 Git HEAD 与关键行号（L1483 池路径等），确认默认行为未漂移。
  - 产出：`evidence/T0_data_lock.json`, `evidence/T0_code_lock.json`。

---

## Phase T1 — C1a 8 格固定锚试点 + G_growth 初筛

> **Q1 已批准：4096×{40,200}×4 档 = 8 格，固定锚（禁用 auto-peak）立即启动。**

- [ ] **T1.1 8 格试点物化（固定锚）**
  - 输入：`d=4096, bw∈{40,200}, tier∈{6,10,16,20}dB` 共 8 格；`delay_override` 固定为 lossfix 时期 `peak_center_ps` 基线值（或 explore 报告推荐的固定锚），`calibration_table=None`。
  - 驱动：`python tools/materialize_aggressive_candidates.py --tiers 6,10,16,20 --points d4096_bw40,d4096_bw200 --pool-root results/real_sequences_aggressive_v1 --delay-override-ps <fixed> --out-root results/authoritative_aggressive_v1/e2e_<tier>_..._aggressive_v1`
  - 验收：8 格 `a_eff/b_eff/chan_ll_table.npy` 落盘新池；`sidecar_meta.json` 记录 `delay_override` 指纹；`MANIFEST.csv` 8 行。
  - 产出：`evidence/T1_8grid_materialization_report.md`。

- [ ] **T1.2 G_timing + G0–G4 试点门**
  - 执行 `python tools/verify_aggressive_gates.py --mode T1 --pool-root results/real_sequences_aggressive_v1`：G1 双跑一致（每档 ≥3 格）、G2 跨档零碰撞、G3 档均值 ser 有序 6>10>16>20、G4 溯源完整、G_timing 锚定一致。
  - 验收：全部 PASS；逐格倒置仅诊断清单，不门控（沿用 lesson）。
  - 产出：`evidence/T1_gates_report.md`。

- [ ] **T1.3 G_growth 初筛（8 格 vs lossfix 对照）**
  - 对比 8 格 `PIE_reconciled_net` 与 lossfix 同格对照，计算 `mean ΔPIE / median ΔPIE / positive_frac`，以 `evidence/gates_frozen.json` 阈值判定。
  - 验收：任一阈值 PASS ⇒ 进入 T2；否则 STOP 归档（不得调参重跑），主线裁决。
  - 产出：`evidence/T1_G_growth_report.md`（含 `old_vs_new` 8 格表 + Q8 离群标注）。

- [ ] **T1.4 reviewer-go review（T1 三阶）**
  - 审查：8 格物化证据 + T1.2/T1.3 门报告 + 是否满足进入 T2 条件；重点：固定锚是否真实禁用 auto-peak、门失败是否未被绕过。
  - 产出：`evidence/T1_review_acceptance.json`（schema `t1_review_acceptance_v1`）。

- [ ] **T1.5 data-lock / code-lock 增量冻结**
  - 增量记录 8 格 `a_eff_sha256 / b_eff_sha256 / chan_ll_sha256`；code-lock 复核透传参数未越界。
  - 产出：`evidence/T1_data_lock.json`, `evidence/T1_code_lock.json`。

---

## Phase T2 — C1b 死时校准表 + 抽 12 格验证

> **Q2 已批准：立项 C1b 并授权新池；Q5 新池即 `real_sequences_aggressive_v1`。**

- [ ] **T2.1 校准表构建**
  - 执行 `python tools/build_calibration_table.py --input-ttbin-metrics <archived metrics> --output results/real_sequences_aggressive_v1/calib/calibration_table_aggressive_v1.json`
  - 输入：四档 `ttbin_metrics.json` 的 singles/通量/peak_sigma 遥测；输出：`per-tier × per-rate` 死时/堆积/游走参数（`deadtime_ps / pileup_coeff / walk_coeff` 等，显式单位）。
  - 验收：表文件落盘 + JSON schema 校验通过 + 单格 dry-run 应用无异常。
  - 产出：`evidence/T2_calibration_table_report.md` + `calibration_table_aggressive_v1.json`。

- [ ] **T2.2 抽 12 格验证物化（带校准表）**
  - 抽样：覆盖 `d∈{64,1024,4096} × bw∈{40,120,200} × tier∈{6,16}dB` 的 12 格（含 T1 的 8 格中 4 格 + 新增 8 格），`--calibration-table <table>` 启用死时校正。
  - 驱动与落盘同 T1.1 增量追加至 `MANIFEST.csv`（总计 20 行）。
  - 验收：12 格落盘新池；`sidecar_meta.json` 记录 `calibration_table_sha256`。
  - 产出：`evidence/T2_12grid_materialization_report.md`。

- [ ] **T2.3 G_growth 复筛（12 格）+ G_timing 全量门**
  - 复用 `verify_aggressive_gates.py --mode T2`：12 格的跨档唯一性/档位序/确定性/溯源 + 12 格 `ΔPIE` 的 `G_growth` 阈值复筛（含与 T1 的增量增益分解）。
  - 验收：`G_growth` PASS ⇒ 进入 T3；否则 STOP 归档，主线裁决是否回退至无校准路径。
  - 产出：`evidence/T2_gates_report.md`, `evidence/T2_G_growth_report.md`。

- [ ] **T2.4 reviewer-go review（T2 三阶）**
  - 审查：校准表拟合合理性（单位/量纲/边界）+ 12 格门证据 + 增益分解是否混淆 C1a 与 C1b 贡献。
  - 产出：`evidence/T2_review_acceptance.json`。

- [ ] **T2.5 data-lock / code-lock 增量冻结**
  - 增量记录校准表 sha256 + 12 格数组哈希；code-lock 复核 `calibration_table` 透传未触解码内核。
  - 产出：`evidence/T2_data_lock.json`, `evidence/T2_code_lock.json`。

---

## Phase T3 — C1c 窗口/帧锚网格寻优 + 层丢弃

- [ ] **T3.1 有效配对窗口/帧锚网格搜索**
  - 网格：`effective_pairing_window_ps ∈ {explore 推荐 3–5 档}` × `frame_start_anchor ∈ {0, +offset}`（explore 报告冻结网格）；在 T2 的 12 格上以 `IAB_est` / `ser` 为目标做网格寻优，记录每点最优窗口/锚。
  - 驱动：`tools/sweep_window_anchor.py`（新文件，仅调 `materialize` 参数，不改解码）。
  - 验收：网格结果落 `evidence/T3_window_anchor_sweep.csv`，每点最优参数写入 `calibration_table` 扩展字段或独立 `window_anchor_opt.json`。
  - 产出：`evidence/T3_window_anchor_sweep_report.md`。

- [ ] **T3.2 层丢弃阈值寻优（C3）**
  - 在 12 格的最优窗口/锚配置上，以 `PIE_reconciled_net` 为目标搜索层丢弃阈值（`net_layer < 0` 丢弃 + 验证位分摊重算），复用 `results/diagnostics/leak_negative_layer_accounting_20260814/run_accounting.py` 记账语义。
  - 验收：每档/每维度最优丢弃掩码落 `evidence/T3_layer_drop_mask.json`；92 点转正逻辑可复现。
  - 产出：`evidence/T3_layer_drop_report.md`。

- [ ] **T3.3 T3 门与增益分解**
  - 执行 `verify_aggressive_gates.py --mode T3`：窗口/锚/层丢弃三者的增量 `ΔPIE` 分解表（C1a vs C1b vs C1c-C3），`G_growth` 终筛（12 格均值/中位数/正占比）。
  - 验收：分解表清晰可归因；`G_growth` PASS ⇒ 进入 T4，否则 STOP。
  - 产出：`evidence/T3_gates_report.md`, `evidence/T3_gain_decomposition.csv`。

- [ ] **T3.4 reviewer-go review（T3 三阶）**
  - 审查：窗口/锚搜索是否覆盖窄 bin 阈值位移区间、层丢弃是否与 `leak_EC_actual_bits` 记账一致、无隐式改码率。
  - 产出：`evidence/T3_review_acceptance.json`。

- [ ] **T3.5 data-lock / code-lock 增量冻结**
  - 冻结最优窗口/锚/掩码的 JSON sha256 + 对应 12 格输出哈希。
  - 产出：`evidence/T3_data_lock.json`, `evidence/T3_code_lock.json`。

---

## Phase T4 — C2 GA / Tal-Vardy + SCL / 块长

> **Q3 已批准：Tal-Vardy 轻版先行再全 GA；Q4 已批准：SCL16 + 丢弃 L10/11。**

- [ ] **T4.1 Tal-Vardy 轻版冻结序（per-layer 信道自适应）**
  - 实现：`tools/build_tal_vardy_freeze_order.py`（轻版：每层 BER 估计 + Tal-Vardy 极化权重构冻结序，保持 n=4096, SCL-4 基准对照）。
  - 在 T3 最优配置的 12 格上跑 `run_real_polar_max_pie.py` 的轻版冻结序分支（新增 `--freeze-order tal_vardy_lite`，默认 `pw` 不变）。
  - 验收：12 格 `k_best` 与冻结序一一对应可复现；`G_growth` 子筛（Tal-Vardy vs PW）记录。
  - 产出：`evidence/T4_tal_vardy_lite_report.md`。

- [ ] **T4.2 全 GA 自适应冻结序**
  - 实现：`tools/build_ga_freeze_order.py`（全 GA：密度演进 per-layer 最优冻结序）。
  - 同 12 格以 `--freeze-order ga_full` 重跑，对比 Tal-Vardy 轻版与 PW 的 `ΔPIE` 分解。
  - 验收：GA 冻结序在高噪声层（BER≥3.8%）回收 gap 的证据表；若 GA 无增益则保留 T4.1 轻版为 C2 终态。
  - 产出：`evidence/T4_ga_full_report.md`。

- [ ] **T4.3 SCL16 + 层丢弃 L10/11（Q4）**
  - 将 SCL 从 4 升至 16（`--scl-list-size 16`），并丢弃 d=4096 的 L10/11（最高两层净负层），在 12 格上重跑校验 `accepted_frame_fraction` 与 `leak_EC_actual_bits` 重算。
  - 验收：SCL16 解码成功率与泄漏重算表可复现；`beta_eff_empirical` 仍由泄漏/错误推导，不手填（AGENTS.md §5.5）。
  - 产出：`evidence/T4_scl16_drop_report.md`。

- [ ] **T4.4 块长评估（n=4096 → 8192 可选）**
  - 在 12 格子集（4 格抽样）评估 n=8192 的 `ΔPIE` vs 解码成本（`--block-length 8192`）；若单位 PIE 增益/成本比低于阈值则不推广至全量。
  - 验收：成本-增益对照表；是否进入全量 8192 由主线裁决。
  - 产出：`evidence/T4_block_length_report.md`。

- [ ] **T4.5 C2 综合门与增益分解**
  - 执行 `verify_aggressive_gates.py --mode T4`：C2 各子项（Tal-Vardy / GA / SCL16 / 块长）的 `ΔPIE` 分解 + `G_growth` 终筛；确保 C1 与 C2 增益不混淆（分层对照表）。
  - 验收：C2 增益分解清晰；`G_growth` PASS ⇒ 进入 T5，否则仅 C1 产物进入审计。
  - 产出：`evidence/T4_gates_report.md`, `evidence/T4_gain_decomposition.csv`。

- [ ] **T4.6 reviewer-go review（T4 三阶）**
  - 审查：Q7 最小透传外无冻结基线越界、Tal-Vardy/GA 冻结序是否 per-layer 信道自适应且可复现、SCL16 成本是否可接受。
  - 产出：`evidence/T4_review_acceptance.json`。

- [ ] **T4.7 data-lock / code-lock 增量冻结**
  - 冻结 12 格在各 C2 分支下的输出哈希 + 冻结序文件 sha256。
  - 产出：`evidence/T4_data_lock.json`, `evidence/T4_code_lock.json`。

---

## Phase T5 — 全量 121 格重跑与审计

- [ ] **T5.1 全量物化（121 格 × 4 档）**
  - 以 T3 最优窗口/锚/层丢弃 + T4 最优冻结序/SCL 配置，在新池全量物化 121 格/档（并行度按主机核数冻结记录，科学参数 `frames300 / seed20260228 / tag_bits64 / shards16` 不变）。
  - 验收：每档 121 格 `a_eff/b_eff/chan_ll_table.npy` 落盘新池；`MANIFEST.csv` 484 行（含 `chan_ll_sha256`）。
  - 产出：`evidence/T5_materialization_report.md`。

- [ ] **T5.2 门全量校验**
  - 执行 `verify_aggressive_gates.py --mode T5`：G1 全量双跑抽检（每档 ≥5 格）、G2 全量跨档零碰撞（574 组量级）、G3 档均值有序、G4 全量溯源、G_timing 锚定一致、G_growth 全量阈值（均值/中位数/正占比，Q8 离群已隔离）。
  - 验收：G1/G2/G4/G_timing PASS，G3 硬条件 PASS（逐格倒置仅诊断），G_growth PASS。
  - 产出：`evidence/T5_gates_report.md`。

- [ ] **T5.3 全链重跑（round1a → actual_ir → security）**
  - 驱动：`python experiments/run_e2e_pipeline.py --candidate-dirs results/authoritative_aggressive_v1/e2e_<tier>_... --real-seq-pool-root results/real_sequences_aggressive_v1 --delay-override-ps <frozen> --calibration-table <frozen> --freeze-order <frozen> --scl-list-size <frozen>` 分档重跑至 `results/paper_grade_aggressive_v1/four_loss_parts_frames300_aggressive_v1/`。
  - 验收：每档 `round1a_summary.txt` + `actual_ir_block_table.csv` + `security_calibrated_master_table.csv` 齐全；validator 121/121。
  - 产出：`evidence/T5_rerun_report.md` + `evidence/T5_validator_report.md`。

- [ ] **T5.4 old-vs-new 对比与审计表**
  - 生成：`lossfix vs aggressive_v1` 的 `PIE_reconciled_net / SKR_reconciled_net_bps / leak_EC_actual_bits` 跨档对比表 + `leak_negative_layer_accounting` 重算对照 + 16dB d2048 离群单独章节。
  - 验收：对比表 484 行对齐；科学结论边界明确标注“哪些跨损失对比恢复成立、哪些仍受限”。
  - 产出：`evidence/T5_old_vs_new_report.md`, `evidence/T5_security_audit_table.csv`。

- [ ] **T5.5 review-go 终审（三阶）+ 记忆归档**
  - reviewer-go 终审：全量门、重跑产物、对比表、是否满足归档条件。
  - 追加 `AGENT_PROJECT_MEMORY.md` / `docs/decision-log.md` / `docs/troubleshooting.md` 条目（T5 收尾时一并补入 2026-08-26 待办的鉴别诊断表）。
  - 执行 `memory triage` + `/finish-change` 判定可归档性。
  - 产出：`evidence/T5_review_acceptance.json`, `evidence/T5_memory_triage.md`。

- [ ] **T5.6 冻结点归档**
  - 产出：`evidence/T5_data_lock.json`（全量 484 格哈希）、`evidence/T5_code_lock.json`（全量冻结基线透传参数快照）、`evidence/T5_manifest_final.csv`。

---

## Stop Rules（全局）

- 任一门 FAIL 且非脚本 bug ⇒ 立即 STOP，不得调参/重跑绕过；产物就地保留，主线裁决。
- 发现需求歧义或超出 `design.md §3` 的冻结基线改动冲动 ⇒ 返回 planner / OpenSpec。
- 任何对 `results/` 既有路径的写入 ⇒ 先取用户显式授权（AGENTS.md §5.2）。
- 并行度按主机逻辑核数冻结并记入溯源；科学参数 `frames300 / seed20260228 / tag_bits64 / shards16` 全程不变。
