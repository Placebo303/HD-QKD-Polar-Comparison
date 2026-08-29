# Spec: aggressive-growth-gate

*Affected capability*: `aggressive-growth-gate` (新增) — 承载 `G_growth` 增长门、三目录落盘与回退隔离的契约。

## ADDED Requirements

### Requirement: G_growth gate structure

`G_growth` SHALL 以 `evidence/gates_frozen.json` 的冻结阈值判定，输入为试点/验证格的 `ΔPIE = PIE_aggressive − PIE_lossfix`，满足以下任一即 PASS 进入下一阶段：(a) 均值 `mean ΔPIE ≥ G_growth.mean_delta_PIE`；(b) 中位数 `median ΔPIE ≥ G_growth.median_delta_PIE`；(c) 正增益格占比 `frac(ΔPIE>0) ≥ G_growth.positive_frac`；16dB d2048 离群格 SHALL 不计入统计。

### Requirement: Gate threshold freezing

`G_growth` 三阈值 SHALL 由 `/opsx-explore` 产出的 `explore_report.md` 建议，并在 T0.3 review 中冻结写入 `design.md §4` 附录或 `evidence/gates_frozen.json`；后续 T1–T5 执行 SHALL 以冻结值为准，不得执行期漂移；阈值变更 SHALL 视为 design amend 并重审。

### Requirement: Incremental output landing

全部 C1/C2 产物 SHALL 落 `_aggressive_v1` 三目录（`real_sequences_aggressive_v1 / authoritative_aggressive_v1 / paper_grade_aggressive_v1`），其相对旧根的子路径仅以后缀 `_aggressive_v1` 区分；旧 `results/` 路径 SHALL 保持只读，任何覆盖冲动 SHALL 先取用户显式授权。

### Requirement: Stop and rollback semantics

任一门 FAIL 且非脚本 bug 时 SHALL 立即 STOP，不得调参/重跑绕过，产物与诊断表就地归档交主线裁决；需求歧义或超出 `design.md §3` 的冻结基线改动冲动 SHALL 返回 planner；回退至无校准/轻版路径的决策 SHALL 在对应阶段 review 中显式记录。

### Requirement: Review and lock discipline

每阶段（T0–T5）末 SHALL 含 `reviewer-go` 独立 review 与 `data-lock / code-lock` 冻结点；`data-lock` SHALL 记录 ttbin sha256 与当期物化格的 `a_eff/b_eff/chan_ll` 哈希，`code-lock` SHALL 记录冻结基线透传文件的 Git HEAD 与关键行号；review PASS 前 SHALL 不进入下一阶段的真实数据执行。
