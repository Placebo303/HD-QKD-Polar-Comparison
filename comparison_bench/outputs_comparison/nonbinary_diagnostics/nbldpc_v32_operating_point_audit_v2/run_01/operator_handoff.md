# Operator Handoff — nbldpc_v32_operating_point_audit_v2/run_01

- Change: `formal-nonbinary-ldpc-v32-operating-point-audit-correction`
- Role: operator closeout（A10，candidate-only 组装）
- Runtime HEAD（执行时点，写入 audit_manifest.json）: `0765d8939b05275eb2f7a8fd8babc296ce910781`

## Status

- `candidate_only = true`
- `main_acceptance_pending = true`
- `qualification = false`
- `promotion = false`

Final Return Statement（逐字）：

> candidate_only，等待 Codex 主控 ACCEPT/REJECT；未运行 DE，未运行 decoder，未启动 successor。

---

## 1. Changed files

提交链：`59ba0236`（freeze 四件套）→ `0765d893`（impl：CLI 1301 行 + tests 1075 行 + tasks）
→ 本 Commit 3（evidence + handoff + tasks A7–A10）；运行时 HEAD = `0765d893`。

## 2. Commands and results

- `python -m comparison_bench.src.comparison_bench.cli.run_nonbinary_v32_operating_point_audit_correction all`
  exit 0（真实输入只读 correction 执行一次，六件产出）。
- pytest T0=8 / T1=16 / T2=13 全过（37/37，单文件套件）。
- R2 独立重算 verdict：**ACCEPT_CANDIDATE_EVIDENCE**（W1–W8 全 PASS；
  readonly_review.json blocking_findings 空 ⇒ C13 成立）。

## 3. Evidence root

`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit_v2/run_01/`
— v2 run_01 八件清单：`audit_manifest.json`、`d0_failure_signature.json`、
`d1_support_mismatch.json`、`d2_dual_law_feasibility.json`、`d3_next_question.json`、
`corrected_branch_decision.json`、`readonly_review.json`、`operator_handoff.md`（本文件）。

## 4. Dirty worktree scope

- `AGENTS.md` 用户改动（+18/-0 未暂存，未 stage，保留在 worktree）。
- 历史 untracked 输出目录若干（未触碰、未 stage）。
- 本轮新增仅 `nbldpc_v32_operating_point_audit_v2/` 与两个 workspace 草案文件
  （`workspace/nb_polar_feasibility_concept/README.md`、
  `workspace/drafts/v33_rate_aligned_empirical_de_change_draft.md`）。

## 5. Frozen roots diff

五 protected old roots 前后哈希一致（29 绑定 SHA256 drift=[]；R2-W6）。
目录计数不变：bridge run_01 = 13 件、旧审计 run_01 = 10 件、V31 = 16 件。

## 6. Known limitations

(a) 执行时点 `corrected_branch_decision` 快照为 `audit_verifier_blocked`（C13 当时未满足），
R2 后 main A9 裁决升级候选终态为 `audit_corrected_rate_aligned_de_required`；快照保留不改写。
(b) MC conditional mean 仅计非命中样本（zero_hit_policy 冻结于 manifest）。
(c) d1 md 未标注 catastrophic 由 support-miss 分支触发（json 有完整数值）。
(d) margin 方法为 simple gap reporting，非有限长渐近界。
(e) T3 为最小集 smoke；full frozen T3 regression not in scope。

## 7. Exact next authorization boundary

等待 Codex 主控对候选终态 `audit_corrected_rate_aligned_de_required` 的 ACCEPT/REJECT。
ACCEPT 后才允许 A11（decision-log / addendum / memory triage）与 A12（archive / commit decision）。
下一实验阶段（V33 exact-rate empirical-P ensemble DE）须另行 OpenSpec 冻结且 DE 执行前需显式授权
（候选草案见 `workspace/drafts/v33_rate_aligned_empirical_de_change_draft.md`，draft only）。

## 8. Headline（照录）

- **D0**：三谓词全过，`signature_mismatch=false`。
- **D1**：三源 q_mass `0.2394680 / 0.2541265 / 0.2553477`；
  `full_expected_nll = infinity ×3`；conditional mean `0.3969 / 0.4262 / 0.4312`；
  truncated CE `7.9091 / 7.7778 / 7.7688`。
- **D2**：Law A nominal-only feasible（gap L1 ≈ 54–55 / L2 ≈ 125–134 / pure total ≈ 180–187 bits）；
  Law B infeasible（H_Q `3.1921 / 3.3626 / 3.3773` → required `3268.7 / 3443.3 / 3458.4`
  vs pure syndrome `1000 / 1030 / 1040`，gap `−2268.7 / −2413.3 / −2418.4` bits）。
- **D3**：问题定义完成未执行，`new_DE_change_required=true`；
  最终候选终态 **audit_corrected_rate_aligned_de_required**。
