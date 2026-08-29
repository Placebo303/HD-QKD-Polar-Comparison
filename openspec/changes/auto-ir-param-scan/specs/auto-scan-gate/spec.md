# Spec: auto-scan-gate

*Affected capability*: `auto-scan-gate` (新增) — 承载每文件自适应扫描的 `G_scan` 增长门、预算门、回退契约与增量落盘的 delta spec。

> 本 spec 为增量能力，不修改既有 `aggressive-*` / `candidate-materialization` spec；全部产物落 `_auto_scan_v1` 隔离命名空间。

## ADDED Requirements

### Requirement: Per-file optimal parameter table

系统 SHALL 为每个新文件产出 `per_file_optimal_params.csv`（镜像 `per_file_optimal_params.json`），每行 SHALL 含 `file_id, src_tag, d, bw, tier, delay_override_opt_ps, effective_pairing_window_ps_opt, frame_anchor_opt, scl_list_size_opt, freeze_order_opt, objective, objective_value, optimal_source ∈ {scan, fallback_per_tier}, gates_frozen_sha256, runner_meta`；该表 SHALL 为 IR 全链重跑的唯一参数源，且 SHALL 通过 JSON schema 校验。

### Requirement: Scan trace completeness

系统 SHALL 为每文件的每次候选物化记录 `per_file_scan_trace.csv` 的一行，含 `file_id, candidate_id, delay_override, window_ps, anchor, scl, freeze_order, raw_ser, PIE_est, leak_EC_bits, IAB_est, Wilson_low/high, runtime_s, candidate_status ∈ {ok, failed, truncated}`；`candidate_status=failed` 的行 SHALL 不计入最优选拔，但 SHALL 保留于 trace 供诊断。

### Requirement: G_scan growth gate structure

`G_scan` SHALL 以 `evidence/gates_frozen.json` 的冻结阈值判定，输入为全量文件的 `ΔPIE_file = PIE_per_file_opt − PIE_per_tier_opt` 分布（`per_file_optimal_params.csv` vs per-tier 最优对照），满足以下任一即 PASS 进入下一阶段：(a) 均值 `mean ΔPIE ≥ G_scan.mean_delta_PIE`；(b) 中位数 `median ΔPIE ≥ G_scan.median_delta_PIE`；(c) 正增益文件占比 `frac(ΔPIE>0) ≥ G_scan.positive_frac`；`fallback_per_tier` 文件的计入规则 SHALL 由 `gates_frozen.json` 显式约定且执行期不得漂移。

### Requirement: Gate threshold freezing

`G_scan` 三阈值与 `G_budget` 上限 SHALL 由 `/opsx-explore` 产出的 `explore_report.md` 建议，并在 T0.3 review 中冻结写入 `evidence/gates_frozen.json`（`design.md §7` 附录镜像）；后续 T1–T3 执行 SHALL 以冻结值为准，不得执行期漂移；阈值变更 SHALL 视为 design amend 并重审。

### Requirement: Budget gate

`G_budget` SHALL 约束每文件的物化次数 ≤ `G_budget.max_materializations_per_file`（Q3 冻结值，推荐 10）且单文件扫描 wall-clock ≤ `G_budget.max_seconds_per_file`；超限 SHALL 截断并记 `truncated=true` 于 trace，不记为门 FAIL，但 SHALL 在 `budget_report.md` 中披露截断率；任何超预算的“补跑” SHALL 视为阈值漂移并被拒绝。

### Requirement: Fallback to per-tier optimum

任一文件的全部候选失败或 `G_scan` 在该文件上无正增益时，系统 SHALL 回退该文件至 **per-tier 最优锚**（T1c 结果，全档 10ps 或 `gates_frozen.json` 冻结的 per-tier 表），该行 SHALL 标记 `optimal_source=fallback_per_tier` 且 `objective_value` 记为 `fallback`；fallback 行 SHALL 通过 `verify_auto_scan_gates.py` 的回退注入 tamper 测试。

### Requirement: Incremental output landing

全部扫描期物化与最优参数重跑产物 SHALL 落 `_auto_scan_v1` 三目录（`real_sequences_auto_scan_v1 / authoritative_auto_scan_v1 / paper_grade_auto_scan_v1`），其相对旧根的子路径仅以后缀 `_auto_scan_v1` 区分；旧 `results/` 路径（含 `*_lossfix_v1` / `*_aggressive_v1`） SHALL 保持只读，任何覆盖冲动 SHALL 先取用户显式授权；扫描器启动时 SHALL 对 `pool_root/out_root/candidate_dir` 做 `auto_scan_v1` 子串 fail-closed 守卫。

### Requirement: Contamination and provenance gates

`G_scan_contamination`（等价 G2） SHALL 校验同 (d,bw) 不同 `src_tag` 的 `a_eff/b_eff` sha256 零碰撞，零容忍；`G3` 档均值 `ser` 严格有序 `6>10>16>20` SHALL 为硬门，逐文件/逐格倒置仅诊断；`G4` 溯源 SHALL 要求每个 sidecar 记录 `source_ttbin` 路径+sha256、`processing_rule_version=pairing_v2`、`src_tag`、`pool_root` 指纹。

### Requirement: Stop and rollback semantics

任一硬门 FAIL 且非脚本 bug 时 SHALL 立即 STOP，不得调参/重跑绕过，产物与诊断表就地归档交主线裁决；`G_scan` 增益门 FAIL 时 SHALL 采纳“per-tier 已足够”的简化结论归档（ponytail lite），不得以放宽阈值重筛绕过；需求歧义或超出 `design.md §4` 的冻结基线改动冲动 SHALL 返回 planner。

### Requirement: Review and lock discipline

每阶段（T0–T3）末 SHALL 含 `reviewer-go` 独立 review 与 `data-lock / code-lock` 冻结点；`data-lock` SHALL 记录当期扫描文件的 ttbin sha256 与物化格的 `a_eff/b_eff/chan_ll` 抽样哈希，`code-lock` SHALL 记录扫描器与冻结基线透传文件的 Git HEAD 与关键行号；review PASS 前 SHALL 不进入下一阶段的真实数据执行。

### Requirement: Wilson-aware selection

`ser` 粗筛阶段的显著性 SHALL 以 Wilson 95% CI（`n = n_eff_pairs`）判定不敏感区（CI 重叠即等价），`PIE` 终选以 `PIE_reconciled_net` 审计值为准；`Wilson_low/high` SHALL 落盘于 `per_file_scan_trace.csv`，`G_scan` 报告 SHALL 以 Wilson 感知披露 `ΔPIE` 显著性格数。
