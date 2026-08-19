# V25 Closeout Addendum (V26 启动前补录，不重跑证据)

日期：2026-08-18（V26 主线程书面确认）
状态：**ADDENDUM** — 仅记录实现/命名勘误与 verifier 边界，不重跑 V25、不改变 V25
       holdout、不改变已冻结结论或已归档证据。V25 `pass_ready_for_de_change` 有效结论
       保持不变。

## 1. C03 “pooled delta” 实现实际与 C04 相同

- `run_m1` 中虽然预计算了跨 source 的 `pooled_hist`，但循环体内**没有使用它**；第
  406 行在每个 source 内重新计算 `pooled_ab = modular_delta_hist_ab(a_tr, b_tr)`，
  再以 `c03 = _delta_to_cond_table(_delta_model_hist(pooled_ab))` 构造表。
- 因此 C03 与 C04（同 source 的 `delta_s`）在同一个 source 的循环内**完全相同**。
- 这**不影响** C04 ≈ 0.81–0.83 bits（holdout NLL，远优于 QSC≈3.2 / V17≈3.3）的
  有效结论，也不影响 M3/M4 分层熵与候选。
- **措辞修正**：本阶段不得再称 “C03 pooled delta 提供跨 source 聚合证据”。V26
  （若需要跨 source 聚合）应使用 C04 source-delta 或直接使用 train `N_ab`，不使用
  “pooled” C03 语义。

## 2. M4 选择规则只是“层数最少”，并非信息论排序的最优方案

- 所有可逆分解的总条件熵按 chain rule 必然等于同一个 H(A|B)（对给定 labeling），
  因此按 “总 H 最小” 做不了区分。
- `_m4_pick` 的实际区分标准是 **先层数最少、再（在层数相同时）取更小的 total H**；
  这是一个确定性预选规则，不是经信息论/DE 排序求得的最优方案。
- **措辞修正**：F01 / F03 在本阶段应称“**预选探索点**（preselected exploration
  points）”，不得称“经信息论排序得到的最优方案”。V26 的 A01/A02 仅在 F01/F03
  natural labeling（MSB→LSB）上做测试，不宣称全局最优。

## 3. 现有 verifier（V001）的检查边界

- `verify_run` 只检查必需文件是否齐全、`gate_summary` 与 `chain_rule_check` 的
  `all_closed` 一致性、status 合法性与 pass 触发条件是否满足。
- **并没有**从 `channel_counts.npz` 重算全部统计（注释也明确写了 “recompute ... is
  heavy; instead verify stored ... consistency”）。
- 因此 V001 是文件/内部状态一致性检查，不是对原始统计的独立重算。
- **V26 M0 语义**：V26 的 M0 应独立重建 layer priors（从 channel_counts.npz /
  C04 source-delta 逐样本构造逐层条件 posterior），顺便完成更强语义复核（验每个
  posterior 非负、归一化、域名正确、与 V25 H_i 在 1e-3 bit/symbol 内一致）。这替代
  且强化了 V25 的只读 verifier 对“统计正确性”的覆盖。

## Tasks 状态修正

V25 实际已被 P102 ACCEPT 并实现运行（M0–M4 完成、只读 verifier ok=true、
status=pass_ready_for_de_change），故 P001/P002 的只读审查与 P102 的 freeze review
ACCEPT 均已完成；归档前将 tasks.md 中 P001/P002/P102 三项打勾，与顶部 ACCEPT 状态
保持一致（见 `tasks.md` 修改记录）。

---
- 本 addendum 不重跑任何 V25 计算，不改变已归档证据与 holdout。
- 仅影响：(a) 报告措辞；(b) tasks.md 状态；(c) V26 M0 的 verifier 边界要求。
