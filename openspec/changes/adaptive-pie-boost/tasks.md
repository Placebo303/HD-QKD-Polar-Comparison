# Tasks: adaptive-pie-boost

**约束**：全程不覆盖 `results/` 既有产物与事件证据；冻结基线仅复用三参数透传，本变更不新增透传；T1/T2 仅在里程碑执行；每个任务后报告 delta（改动文件+命令+结果），不重复背景。留2核 `workers=max(2,cpu-2)`，保精度 `frames300/seed20260228/tag_bits64/shards16`，增量 `*_adaptive_v1`。

**全局纪律**：每阶段末含 `reviewer-go` 独立 review 与 `data-lock / code-lock` 冻结点；任一硬门 FAIL 且非脚本 bug ⇒ STOP 不得调参绕过；需求歧义 ⇒ 返回 planner。

---

## Phase T0 — 探索冻结 / 结构门 / 阈值与 4 点清单落盘

- [ ] **T0.1 compile/import 结构检查**
  - 命令：`python -m compileall tools/auto_ir_scan.py tools/compare_adaptive_vs_frozen.py tools/verify_adaptive_gates.py` + `python -c "import tools.auto_ir_scan; import tools.compare_adaptive_vs_frozen"` + `python tools/auto_ir_scan.py --help`
  - 验收：exit 0；`--help` 含 `--pool-root/--scan-config/--objective/--budget-per-file/--frozen-manifest`；旧 materialize 路径未变；留2核参数 `workers=max(2,cpu-2)` 可见。
  - 产出：`evidence/T0_compile_report.md`。

- [ ] **T0.2 默认行为等价断言 + 守卫 tamper**
  - 用合成 point 在 tmp 根断言：不传参时 `materialize_out_dir == REPO_ROOT/"results"/"real_sequences"/f"d{d}_bw{bw}"/f"blk{block_index}"` 逐字符一致；`delay_override=None` 时 `used_delay_ps == peak_center_ps`；传入旧根（无 `adaptive_v1` 子串，如 `real_sequences` / `real_sequences_aggressive_v1` / `authoritative`）应被守卫拒绝。
  - 额外：`auto_ir_scan --pool-root results/real_sequences --scan-config tmp.yaml` 应 fail-closed；`--budget-per-file 19` 超 18 应拒绝或截断披露。
  - 命令：`pytest -p no:cacheprovider --basetemp=workspace/adaptive-pie-boost/T0 -k "TestAdaptiveDefault or TestAdaptiveGuard"`
  - 验收：4+ 断言用例通过；tamper 注入旧根/预算超限均 FAIL-closed。
  - 产出：`evidence/T0_guard_tamper_report.md`。

- [ ] **T0.3 explore 报告与阈值/预算/4 点清单冻结（Q1–Q4）**
  - 执行 `/opsx-explore` 落盘 `explore_report.md`：含
    - Q1 搜索空间建议（delay Δ=40ps / window {35,40,45} / anchor {0,offset}，18/文件，40ps 不敏感区先验与 72 物化 <1m 成本基线）；
    - Q2 目标函数建议（主 PIE + 辅 ser，Wilson 95% CI）；
    - Q3 预算上限建议（18/文件）+ 留2核并发冻结；
    - Q4 回退策略确认（per-tier 10ps fallback）；
    - `G_adaptive` 披露口径（均值/中位数/正占比/Wilson 显著数）；
    - **4 点 frozen max PIE 清单**：从冻结基线 `results/paper_grade_aggressive_v1/.../polar_e2e_results.csv`（或 `results/authoritative/...`）中每档 `PIE_practical` 最大行提取 `(loss_db,d,bw,blk,PIE,ser,ttbin_path)` 共 4 行，附 `ttbin` 存在性与 sha256。
  - 主线在 review 中冻结阈值写入 `evidence/gates_frozen.json`（`design.md §7` 附录镜像），后续 T1–T3 以冻结值为准，不得执行期漂移。
  - 产出：`explore_report.md` + `evidence/gates_frozen.json`（含 `frozen_max_points: [{loss_db,d,bw,blk,PIE_frozen,ttbin_sha256}]`）。
  - 阻塞：T0.3 未冻结前，T1 不启动任何真实数据扫描。

- [ ] **T0.4 reviewer-go review（T0 三阶之二：候选交付审查）**
  - 审查范围：`proposal.md / design.md / tasks.md / specs/adaptive-pie-boost/spec.md` + T0.1–T0.3 证据；重点：Q1–Q4 冻结完整性、18 候选 3×6 正交性、仅 4 点对比的成本合理性、外层循环零侵入性、池隔离守卫（`adaptive_v1` 子串）、`G_adaptive` 非硬门披露语义、留2核与保精度 300 帧、4 点清单与 ttbin 存在性。
  - 验收：reviewer-go PASS（或仅非阻塞 doc 遗留）；否则按 findings 修订后重审。
  - 产出：`evidence/T0_review_acceptance.json`（schema `t0_review_acceptance_v1`）。

- [ ] **T0.5 data-lock / code-lock 冻结点**
  - `data-lock`：记录 4 点 frozen max 对应的 ttbin 主文件+`.1` 分片存在性、sha256、分片校验（`evidence/T0_data_lock.json`）；与 `fix-candidate` / `polar-aggressive-7x-recovery` 的 T0 锁格式对齐，额外记录 `frozen_max_points` 的 `MANIFEST.csv` 行号与 PIE 值快照。
  - `code-lock`：记录 `src/workflow/export_joint_sequence_sidecar.py` 与 `experiments/run_e2e_pipeline.py` 的 Git HEAD 与关键行号（池路径等），确认默认行为未漂移；新增 `tools/auto_ir_scan.py` / `tools/compare_adaptive_vs_frozen.py` 的 HEAD 与 `--help` 快照、留2核代码行号。
  - 产出：`evidence/T0_data_lock.json`, `evidence/T0_code_lock.json`。

---

## Phase T1 — 4 点 × 18 候选扫描（3 点×6 组合择优）+ 披露

> **试点规模**：仅 4 点（6/10/16/20dB 各 1 frozen max 点）× 18 候选 = 72 物化，按 `evidence/gates_frozen.json` 冻结值枚举（Q1/Q3），留2核并行。

- [ ] **T1.1 4 点×18 候选扫描（外层循环）**
  - 输入：4 点的 ttbin/candidate；扫描空间按 `gates_frozen.json` 冻结值枚举（Q1/Q3），`frames300` 固定。
  - 驱动：`python tools/auto_ir_scan.py --frozen-manifest evidence/gates_frozen.json --pool-root results/real_sequences_adaptive_v1 --scan-config evidence/gates_frozen.json --objective pie --budget-per-file 18 --out-root results/authoritative_adaptive_v1 --workers max2`（实际 `workers=max(2,cpu-2)`，披露于 trace）
  - 验收：`per_file_scan_trace.csv` 落盘 72 行量级且每候选行含 `Wilson CI` 与 `runtime_s`；`sidecar_meta.json` 记录 `delay/window/anchor` 指纹；`MANIFEST.csv` 行数 = 72（+header）；无旧根覆写；`scan_wall_s <60s`（配对 <1m）披露。
  - 产出：`evidence/per_file_scan_trace.csv`, `evidence/per_file_optimal_params.csv`（4 行最优）, `evidence/T1_materialization_report.md`（含 `scan_wall_s/sort_s/per_point_s/workers`）。

- [ ] **T1.2 G_adaptive 披露 + 污染/预算门**
  - 执行 `python tools/verify_adaptive_gates.py --mode T1 --trace evidence/per_file_scan_trace.csv --optimal evidence/per_file_optimal_params.csv --frozen evidence/gates_frozen.json`：G2 跨档零碰撞、G3 档均值有序、G4 溯源完整、G_adaptive 披露（`mean ΔPIE/median/positive_frac/Wilson 显著数`）、G_budget 预算合规（≤18/文件，`scan_wall_s<60s`）。
  - 验收：G2/G4 PASS；G3 硬条件 PASS（逐点倒置仅诊断）；G_budget PASS；G_adaptive 披露完整（不阻断进入 T2，即使均值≤0 也进入 T2 完成 4 点重跑以产出对照表，结论措辞区分“提升/不敏感”）。
  - 产出：`evidence/T1_gates_report.md`, `evidence/T1_G_adaptive_report.md`（含 4 点 `ΔPIE_est` 初步披露 + Wilson 区间）。

- [ ] **T1.3 回退注入测试**
  - 人为注入单文件全候选失败（mock `materialize` 抛异常或 `candidate_status=failed` 覆盖），验证该文件回退至 per-tier 最优锚（T1c 10ps）且 `optimal_source=fallback_per_tier`，其余 3 文件不受影响。
  - 验收：回退路径可复现；`per_file_optimal_params.csv` 中 fallback 行 `objective_value` 标记为 `fallback` 且披露口径在 `gates_frozen.json` 中显式约定（计入或不计入均值）。
  - 产出：`evidence/T1_fallback_tamper_report.md`。

- [ ] **T1.4 reviewer-go review（T1 三阶）**
  - 审查：72 行 trace 可归因性 + T1.2/T1.3 门报告 + 18 候选正交性 + 是否满足进入 T2 条件（G2/G4/budget PASS 即进入）；重点：外层循环是否真实复用现有物化路径、回退是否未被绕过、预算与留2核是否合规、frames300 是否保精度。
  - 产出：`evidence/T1_review_acceptance.json`（schema `t1_review_acceptance_v1`）。

- [ ] **T1.5 data-lock / code-lock 增量冻结**
  - 增量记录 4×18 候选的 `a_eff_sha256 / b_eff_sha256 / chan_ll_sha256` 抽样（至少每文件 2 候选）；code-lock 复核扫描器未越界修改冻结基线、留2核代码未漂移。
  - 产出：`evidence/T1_data_lock.json`, `evidence/T1_code_lock.json`。

---

## Phase T2 — 4 点最优全链重跑与 _adaptive_vs_frozen 对比

> **范围**：以 `per_file_optimal_params.csv` 的 4 行最优参数，各自全链重跑至 `paper_grade_adaptive_v1`，生成 4 行对照表。

- [ ] **T2.1 4 点最优全链重跑（round1a → actual_ir → security）**
  - 以 4 行最优参数分档重跑至 `results/paper_grade_adaptive_v1/four_loss_parts_frames300_adaptive_v1/<loss_XXdB>/`（`--delay-override-ps <per-file-opt> --effective-pairing-window-ps <opt> --frame-anchor <opt>` 等按文件透传，`frames300/seed20260228` 不变）。
  - 验收：每档 `round1a_summary.txt` + `actual_ir_block_table.csv` + `security_calibrated_master_table.csv` 齐全；每文件 validator 行数对齐（1 行/文件，或按 block 粒度对齐）；`beta_eff_empirical` 仍由泄漏/错误推导，不手填（AGENTS.md §5.5）；无旧根覆写。
  - 产出：`evidence/T2_rerun_report.md` + `evidence/T2_validator_report.md`（含每档 `PIE/ser/beta` 快照）。

- [ ] **T2.2 _adaptive_vs_frozen 对比表生成**
  - 执行 `python tools/compare_adaptive_vs_frozen.py --frozen evidence/gates_frozen.json --adaptive evidence/per_file_optimal_params.csv --adaptive-results results/paper_grade_adaptive_v1 --output results/adaptive_v1/_adaptive_vs_frozen.csv`（镜像至 `evidence/_adaptive_vs_frozen.csv`）。
  - 对照表 schema（4 行，列）：`loss_db,d,bw,blk,PIE_frozen,PIE_adaptive,ΔPIE,ser_frozen,ser_adaptive,Δser,beta_frozen,beta_adaptive,window_frozen,window_adaptive,delay_frozen,delay_adaptive,optimal_source,Wilson_low/high,significant_flag`
  - 验收：4 行对齐且 `ΔPIE` 可复现（`PIE_adaptive - PIE_frozen` 逐行可算）；`Δser` 与 trace 一致；`beta` 非手填校验通过；Wilson 显著标记与 T1.2 一致。
  - 产出：`results/adaptive_v1/_adaptive_vs_frozen.csv` + `evidence/_adaptive_vs_frozen.csv` + `evidence/T2_compare_report.md`。

- [ ] **T2.3 G_adaptive 终披露 + 污染/预算全量门**
  - 复用 `verify_adaptive_gates.py --mode T2`：全量 G2/G4 溯源 + 4 点 `ΔPIE` 的均值/中位数/正占比/Wilson 显著数终披露（含与 T1 的增量分解：delay vs window/anchor 贡献拆分，若可归因）。
  - 验收：`G2/G4` PASS；`G_adaptive` 披露完整；`G_budget` 仍 PASS。
  - 产出：`evidence/T2_gates_report.md`, `evidence/T2_G_adaptive_report.md`, `evidence/T2_gain_decomposition.csv`（可选，若不可拆分则记为“联合择优不可拆”）。

- [ ] **T2.4 reviewer-go review（T2 三阶）**
  - 审查：4 点重跑产物与最优表一一对应性 + 对比表 4 行对齐 + 增益披露是否混淆 per-tier 与 per-file 贡献 + 重跑产物是否与冻结基线同口径（`frames300` 同 `leak` 记账语义）；重点：`_adaptive_vs_frozen.csv` 是否仅 4 行且未引入额外点位。
  - 产出：`evidence/T2_review_acceptance.json`。

- [ ] **T2.5 data-lock / code-lock 增量冻结**
  - 增量记录 4 点最优的 `a_eff/b_eff/chan_ll` 哈希 + `per_file_optimal_params.csv` 的 sha256 + 对照表 sha256；code-lock 复核透传未触解码内核、留2核未漂移。
  - 产出：`evidence/T2_data_lock.json`, `evidence/T2_code_lock.json`。

---

## Phase T3 — 固化与归档

- [ ] **T3.1 old-vs-new 对比与审计表**
  - 生成：`per-tier 最优锚 vs per-file 最优` 的 `PIE/ser/SKR` 跨档对比扩展表（4 行主表 + 72 行 trace 诊断附表）+ `leak_EC_actual_bits` 重算对照（如启用层丢弃则复用 `leak_negative_layer_accounting` 语义，否则仅披露 `leak`）。
  - 验收：对比表 4 行主表 + 72 行附表对齐；科学结论边界明确标注“哪些档 per-file 增益显著（Wilson 不重叠）、哪些落在 40ps 不敏感区”。
  - 产出：`evidence/T3_old_vs_new_report.md`, `evidence/T3_old_vs_new_per_tier_vs_per_file.csv`, `evidence/T3_security_audit_table.csv`（或复用 `T2_validator_report` 扩展）。

- [ ] **T3.2 最优参数固化**
  - 固化 `per_file_optimal_params.csv/json` 为 `results/real_sequences_adaptive_v1/calib/per_file_optimal_params_adaptive_v1.json`（或 `results/adaptive_v1/per_file_optimal_params_adaptive_v1.json` 聚合镜像，`evidence/` 双份），含 `file_id, loss_db, d, bw, blk, delay_opt, window_opt, anchor_opt, objective_value, fallback_flag, gates_frozen_sha256, runner_meta`。
  - 验收：JSON schema 校验通过；单文件 dry-run 以固化参数重跑可复现 `objective_value`（Wilson 区间内）；`gates_frozen_sha256` 可追溯。
  - 产出：`evidence/T3_optimal_params_freeze_report.md` + 固化 JSON/CSV。

- [ ] **T3.3 review-go 终审（三阶）+ 记忆归档**
  - reviewer-go 终审：门全量、重跑产物、对比表 4 行、最优表固化、是否满足归档条件；重点：是否满足“每文件扫描失败回退至 per-tier 最优锚”的契约、是否仅 4 点对比未扩量、增量 `*_adaptive_v1` 未覆写冻结基线。
  - 追加 `AGENT_PROJECT_MEMORY.md` / `docs/decision-log.md` 条目（per-file 3×6 自适应结论 + 4 点 ΔPIE 披露 + 预算/留2核冻结值）。
  - 执行 `memory triage` + `/finish-change` 判定可归档性。
  - 产出：`evidence/T3_review_acceptance.json`, `evidence/T3_memory_triage.md`。

- [ ] **T3.4 冻结点归档**
  - 产出：`evidence/T3_data_lock.json`（4 点采样哈希）、`evidence/T3_code_lock.json`（扫描器与冻结基线透传参数快照、留2核行号）、`evidence/T3_manifest_final.csv`（72 行 MANIFEST 终态）。

---

## Stop Rules（全局）

- 任一硬门 FAIL（G2/G4/污染门）且非脚本 bug ⇒ 立即 STOP，不得调参/重跑绕过；产物就地保留，主线裁决。
- 发现需求歧义或超出 `design.md §4` 的冻结基线改动冲动 ⇒ 返回 planner / OpenSpec（AGENTS.md §3）。
- 任何对 `results/` 既有路径（`paper_grade_v3/authoritative/paper_grade_v4_rate_search_fix/*_lossfix_v1/*_aggressive_v1`）的写入 ⇒ 先取用户显式授权（AGENTS.md §5.2），否则拒绝。
- 并行度按 `workers=max(2,cpu-2)` 冻结并记入溯源；科学参数 `frames300/seed20260228/tag_bits64/shards16` 全程不变（扫描期 T1 亦为 300，不擅自降为 100）。
- 本变更聚焦 4 点 max PIE 对比；任何扩量至全量 121 格需另起 OpenSpec 并重走 explore 冻结。
