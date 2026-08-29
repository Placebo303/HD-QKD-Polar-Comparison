# Tasks: auto-ir-param-scan

**约束**：全程不覆盖 `results/` 既有产物与事件证据；冻结基线仅复用 `polar-aggressive-7x-recovery` 已立项的三参数透传，本变更不新增透传；T1/T2 仅在里程碑执行；每个任务后报告 delta（改动文件+命令+结果），不重复背景。

**全局纪律**：每阶段末含 `reviewer-go` 独立 review 与 `data-lock / code-lock` 冻结点；任一硬门 FAIL 且非脚本 bug ⇒ STOP 不得调参绕过；需求歧义 ⇒ 返回 planner。

**状态声明**：本 tasks.md 仅为 plan 产出，所有任务处于 `待执行` 状态；不执行 `/opsx-apply`，不跑真实数据扫描，待用户显式授权后方可进入 T0。

---

## Phase T0 — 探索冻结 / 结构门 / 阈值落盘

- [ ] **T0.1 compile/import 结构检查**
  - 命令：`python -m compileall tools/auto_ir_scan.py tools/verify_auto_scan_gates.py` + `python -c "import tools.auto_ir_scan; import tools.verify_auto_scan_gates"`
  - 验收：exit 0；`auto_ir_scan` 的 `--help` 可打印且含 `--pool-root/--scan-config/--objective/--budget-per-file`；旧 `materialize` 路径未变。
  - 产出：`evidence/T0_compile_report.md`。
  - 依赖：`explore_report.md` 初稿完成前可先做 import 检查。

- [ ] **T0.2 默认行为等价断言 + 守卫 tamper**
  - 用合成 point 在 tmp 根断言：不传参时 `materialize_out_dir == REPO_ROOT/"results"/"real_sequences"/f"d{d}_bw{bw}"/f"blk{block_index}"` 逐字符一致；`delay_override=None` 时 `used_delay_ps == peak_center_ps`；传入旧根（无 `auto_scan_v1` 子串，如 `real_sequences` / `real_sequences_aggressive_v1`）应被守卫拒绝。
  - 额外：`auto_ir_scan --pool-root results/real_sequences --scan-config tmp.yaml` 应 fail-closed。
  - 命令：`pytest -p no:cacheprovider --basetemp=workspace/auto-ir-param-scan/T0 -k "TestAutoScanDefault or TestAutoScanGuard"`
  - 验收：4+ 断言用例通过；tamper 注入旧根/预算超限均 FAIL-closed。
  - 产出：`evidence/T0_guard_tamper_report.md`。

- [ ] **T0.3 explore 报告与阈值/预算冻结（Q1–Q4）**
  - 执行 `/opsx-explore` 落盘 `explore_report.md`：含
    - Q1 搜索空间建议（delay 步长/窗口档位/锚档位/SCL 档位，含 40ps 不敏感区先验与 T1c 20 物化 <6min 成本基线）；
    - Q2 目标函数建议（主 PIE + 辅 ser，Wilson 区间判据）；
    - Q3 预算上限建议（≤10 起步）；
    - Q4 回退策略确认（per-tier 最优锚 fallback）；
    - `G_scan` 三阈值（`mean_delta_PIE / median_delta_PIE / positive_frac`）建议 + `G_budget` 上限。
  - 主线在 review 中冻结阈值写入 `evidence/gates_frozen.json`（`design.md §7` 附录镜像），后续 T1–T3 以冻结值为准，不得执行期漂移。
  - 产出：`explore_report.md` + `evidence/gates_frozen.json`。
  - 阻塞：T0.3 未冻结前，T1 不启动任何真实数据扫描。

- [ ] **T0.4 reviewer-go review（T0 三阶之二：候选交付审查）**
  - 审查范围：`proposal.md / design.md / tasks.md / specs/auto-scan-gate/spec.md` + T0.1–T0.3 证据；重点：Q1–Q4 冻结完整性、外层循环零侵入性、池隔离守卫、`G_scan` 结构与 `G_growth` 复用一致性、预算门合理性。
  - 验收：reviewer-go PASS（或仅非阻塞 doc 遗留）；否则按 findings 修订后重审。
  - 产出：`evidence/T0_review_acceptance.json`（schema `t0_review_acceptance_v1`）。

- [ ] **T0.5 data-lock / code-lock 冻结点**
  - `data-lock`：记录新文件 ttbin 的存在性、sha256、分片校验（`evidence/T0_data_lock.json`）；与 `fix-candidate` / `polar-aggressive-7x-recovery` 的 T0 锁格式对齐。
  - `code-lock`：记录 `src/workflow/export_joint_sequence_sidecar.py` 与 `experiments/run_e2e_pipeline.py` 的 Git HEAD 与关键行号（L1483 池路径等），确认默认行为未漂移；新增 `tools/auto_ir_scan.py` 的 HEAD 与 `--help` 快照。
  - 产出：`evidence/T0_data_lock.json`, `evidence/T0_code_lock.json`。

---

## Phase T1 — 小样本试点（2 文件 × 8 格）+ G_scan 初筛

> **试点规模**：选 2 个新文件（覆盖不同通量/窗口敏感性）× 8 格（`d∈{64,1024,4096} × bw∈{40,200}` 子集，按 explore 建议抽样），每文件按 Q1 自适应策略扫描（粗筛 40ps + 细化 10ps 邻域，≤10 候选/文件）。

- [ ] **T1.1 2 文件×8 格试点扫描（外层循环）**
  - 输入：2 文件的 ttbin/candidate；扫描空间按 `evidence/gates_frozen.json` 冻结值枚举（Q1/Q3）。
  - 驱动：`python tools/auto_ir_scan.py --ttbin-root <per-file> --pool-root results/real_sequences_auto_scan_v1 --scan-config evidence/gates_frozen.json --objective pie --budget-per-file 10 --out-root results/authoritative_auto_scan_v1`
  - 验收：每文件 `per_file_scan_trace.csv` 落盘且每候选行含 `Wilson CI`；`sidecar_meta.json` 记录 `delay_override/window_ps/anchor` 指纹；`MANIFEST.csv` 行数 = 文件数×格数×候选数（试点 ≤160 行量级）。
  - 产出：`evidence/T1_scan_trace.csv`, `evidence/T1_materialization_report.md`。

- [ ] **T1.2 G_scan 初筛 + 污染/预算门**
  - 执行 `python tools/verify_auto_scan_gates.py --mode T1 --trace evidence/T1_scan_trace.csv --optimal evidence/T1_optimal_params.csv`：G2 跨档零碰撞、G3 档均值有序、G4 溯源完整、G_scan 三阈值判定（`mean/median/positive_frac`）、G_budget 预算合规。
  - 验收：G2/G4 PASS；G3 硬条件 PASS（逐格倒置仅诊断）；G_scan 任一阈值 PASS ⇒ 进入 T2，否则 STOP 归档（不得调参重跑），主线裁决是否采纳“per-tier 已足够”简化结论。
  - 产出：`evidence/T1_gates_report.md`, `evidence/T1_G_scan_report.md`（含 `old_vs_new` 2 文件对照 + Wilson 区间披露）。

- [ ] **T1.3 回退注入测试**
  - 人为注入单文件全候选失败（mock `materialize` 抛异常），验证该文件回退至 per-tier 最优锚（T1c 10ps）且 `optimal_source=fallback_per_tier`，其余文件不受影响。
  - 验收：回退路径可复现；`per_file_optimal_params.csv` 中 fallback 行 `objective_value` 标记为 `fallback` 且不计入 G_scan 均值（或按冻结口径计入，需在 gates_frozen 中显式约定）。
  - 产出：`evidence/T1_fallback_tamper_report.md`。

- [ ] **T1.4 reviewer-go review（T1 三阶）**
  - 审查：2 文件试点 trace 可归因性 + T1.2/T1.3 门报告 + 是否满足进入 T2 条件；重点：外层循环是否真实复用现有物化路径、回退是否未被绕过、预算是否合规。
  - 产出：`evidence/T1_review_acceptance.json`（schema `t1_review_acceptance_v1`）。

- [ ] **T1.5 data-lock / code-lock 增量冻结**
  - 增量记录 2 文件×8 格×候选的 `a_eff_sha256 / b_eff_sha256 / chan_ll_sha256` 抽样；code-lock 复核扫描器未越界修改冻结基线。
  - 产出：`evidence/T1_data_lock.json`, `evidence/T1_code_lock.json`。

---

## Phase T2 — 全量扫描与门

> **全量范围**：新文件全集（按实际到达文件数，plan 阶段记为 N_files，占位）；每文件仍按冻结预算 ≤10 候选扫描；通过后再做最优参数全链重跑。

- [ ] **T2.1 全量扫描（per-file 自适应）**
  - 驱动同 T1.1，输入扩展至全量 N_files；输出追加至 `MANIFEST.csv`（总计 N_files×8 格×候选数行）。
  - 验收：全量 `per_file_scan_trace.csv` 落盘；`sidecar_meta.json` 记录 `calibration_table_sha256`（如启用）；无旧根覆写。
  - 产出：`evidence/T2_scan_trace.csv`, `evidence/T2_materialization_report.md`。

- [ ] **T2.2 G_scan 复筛（全量）+ 污染/预算全量门**
  - 复用 `verify_auto_scan_gates.py --mode T2`：全量跨档唯一性/档位序/溯源 + 全量 `ΔPIE` 的 G_scan 阈值复筛（含与 T1 的增量增益分解：粗筛 vs 细化 vs SCL 的 ΔPIE 贡献）。
  - 验收：`G_scan` PASS ⇒ 进入 T3；否则 STOP 归档，主线裁决是否回退至 per-tier 最优终态。
  - 产出：`evidence/T2_gates_report.md`, `evidence/T2_G_scan_report.md`, `evidence/T2_gain_decomposition.csv`。

- [ ] **T2.3 最优参数全链重跑（round1a → actual_ir → security）**
  - 以 `per_file_optimal_params.csv` 的每文件最优参数，分档重跑至 `results/paper_grade_auto_scan_v1/four_loss_parts_frames300_auto_scan_v1/`（`--delay-override-ps <per-file-opt> --effective-pairing-window-ps <opt> --frame-anchor <opt> --scl-list-size <opt>` 等按文件透传）。
  - 验收：每档 `round1a_summary.txt` + `actual_ir_block_table.csv` + `security_calibrated_master_table.csv` 齐全；validator 121/121（或按实际格数 N 对齐）。
  - 产出：`evidence/T2_rerun_report.md` + `evidence/T2_validator_report.md`。

- [ ] **T2.4 reviewer-go review（T2 三阶）**
  - 审查：全量 trace 完整性 + 门证据 + 增益分解是否混淆 per-tier 与 per-file 贡献 + 重跑产物是否与最优表一一对应。
  - 产出：`evidence/T2_review_acceptance.json`。

- [ ] **T2.5 data-lock / code-lock 增量冻结**
  - 增量记录最优参数 JSON sha256 + 全量输出采样哈希；code-lock 复核透传未触解码内核。
  - 产出：`evidence/T2_data_lock.json`, `evidence/T2_code_lock.json`。

---

## Phase T3 — 固化与归档

- [ ] **T3.1 old-vs-new 对比与审计表**
  - 生成：`per-tier 最优锚 vs per-file 最优` 的 `PIE_reconciled_net / SKR_reconciled_net_bps / leak_EC_actual_bits / ser` 逐文件对比表 + `leak_negative_layer_accounting` 重算对照（如启用层丢弃）。
  - 验收：对比表 N_files×8 格对齐；科学结论边界明确标注“哪些文件 per-file 增益显著、哪些落在 40ps 不敏感区”。
  - 产出：`evidence/T3_old_vs_new_report.md`, `evidence/T3_old_vs_new_per_tier_vs_per_file.csv`, `evidence/T3_security_audit_table.csv`。

- [ ] **T3.2 最优参数固化**
  - 固化 `per_file_optimal_params.csv/json` 为 `results/real_sequences_auto_scan_v1/calib/per_file_optimal_params_auto_scan_v1.json`（或 `evidence/` 镜像），含 `file_id, d, bw, delay_opt, window_opt, anchor_opt, scl_opt, freeze_opt, objective_value, fallback_flag, gates_frozen_sha256`。
  - 验收：JSON schema 校验通过；单文件 dry-run 以固化参数重跑可复现 `objective_value`（Wilson 区间内）。
  - 产出：`evidence/T3_optimal_params_freeze_report.md`。

- [ ] **T3.3 review-go 终审（三阶）+ 记忆归档**
  - reviewer-go 终审：全量门、重跑产物、对比表、最优表固化、是否满足归档条件；重点：是否满足“每文件扫描失败回退至 per-tier 最优锚”的契约。
  - 追加 `AGENT_PROJECT_MEMORY.md` / `docs/decision-log.md` 条目（per-file 自适应结论 + 预算/目标函数冻结值）。
  - 执行 `memory triage` + `/finish-change` 判定可归档性。
  - 产出：`evidence/T3_review_acceptance.json`, `evidence/T3_memory_triage.md`。

- [ ] **T3.4 冻结点归档**
  - 产出：`evidence/T3_data_lock.json`（全量采样哈希）、`evidence/T3_code_lock.json`（扫描器与冻结基线透传参数快照）、`evidence/T3_manifest_final.csv`。

---

## Stop Rules（全局）

- 任一硬门 FAIL 且非脚本 bug ⇒ 立即 STOP，不得调参/重跑绕过；产物就地保留，主线裁决。
- 发现需求歧义或超出 `design.md §4` 的冻结基线改动冲动 ⇒ 返回 planner / OpenSpec。
- 任何对 `results/` 既有路径的写入 ⇒ 先取用户显式授权（AGENTS.md §5.2）。
- 并行度按主机逻辑核数冻结并记入溯源；科学参数 `frames300 / seed20260228 / tag_bits64 / shards16` 全程不变（扫描期 T1 可用 `frames100` 加速需在 gates_frozen 中显式授权）。
- 本变更当前仅 plan 阶段，T0–T3 均处于待执行；任何真实数据执行需用户显式授权后方可启动。
