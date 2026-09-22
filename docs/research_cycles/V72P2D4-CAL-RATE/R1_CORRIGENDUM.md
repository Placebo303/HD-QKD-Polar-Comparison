# V72P2D4R1 CORRIGENDUM — R1 返回块转录错勘误（R1 输出不动）

Date: 2026-09-05
Cycle: `V72P2D4R1-CAL-GF32-MODEL-RATE` (plan cycle `V72P2D4-CAL-RATE`, D4 R1)
HEAD: `a7a6ec62` on `formal-ir-v72p1-addendum-clean`

## 1. 勘误对象（只改本文，不改 R1 输出）

- R1 正式输出根 `comparison_bench/outputs_comparison/v72p2d4r1_cal_gf32_model_rate_audit_20260905/` 下四文件（`manifest.json/audit.json/table.csv/report.md`）**一律不改、不覆盖、不重跑**。
- 本勘误仅修正此前返回块中对 R1 主结果的转录口径；历史文件（`RESULT_SUMMARY.md` / `ATTEMPT_0_INVALID.md` / plan/implementation review）**一律不删除**。

## 2. 主结果正值（以 R1 输出与 RESULT_SUMMARY §4 为准）

- Selected `M2` mean（same caliber）: `L1=3.795171 / L2=3.183651 / joint=6.978821 bit/symbol`。
- 此前返回块中的 `3.897449 / 3.898673 / 7.796123` 系 **Attempt-0 转录错**：该组数来自旧 Attempt-0 根（`v72p2d4_cal_...`）symbol-shuffle 单模型路径（`cv mean_ce_joint=7.796122677407631 = 3.8974493104279024+3.8986733669797284`），已在 `ATTEMPT_0_INVALID.md §2` 记为 `INVALID_NON_EVIDENCE_UNTRACKED`，不得作为 D4 R1 主结果。

## 3. 模型身份（R1 口径，不变）

- `M0 = train marginal`，`M1 = full lambda1`，`M2 = layered`；`ranking M2/M1/M0`，selected `M2`。
- 上述身份以 R1 输出为准；返回块若有相异表述，以本节为准。

## 4. delta 事后回写违规

- `select_delta`（`0.02`）系事后回写，违反冻结口径：D4 冻结为 `Δ<0.01` 简单优先（见 `ATTEMPT_0_INVALID.md §2` 引用的 `D4T2-3`）。
- 该违规不改 R1 数值，但构成 R1 结论降级的直接原因之一。

## 5. R1 结论降级（不撤销 VAL0/decoder0，不 promotion）

- R1 降级为 `CANDIDATE_DESCRIPTIVE_EVIDENCE`；`r1_verdict = CANDIDATE_NOT_ACCEPTED`。
- `VAL0 / decoder0`（`decoder_calls=0/published_bits=0`，VAL 未用于拟合）**不撤销**，仍以 R1 输出与 `RESULT_SUMMARY.md §5` 为准。
- `scientific_promotion=false`；本次不做任何 promotion / 路线 A/B 推进 / 下界或失败定论。

## 6. cycle_state 变更

- `state: RESULT_REVISE_REQUIRED`，`r1_verdict: CANDIDATE_NOT_ACCEPTED`，`real/formal/promotion: false`，`next_gate: D4R2_INDEPENDENT_PLAN_REVIEW`。
- 详见同目录 `cycle_state.yaml`。
