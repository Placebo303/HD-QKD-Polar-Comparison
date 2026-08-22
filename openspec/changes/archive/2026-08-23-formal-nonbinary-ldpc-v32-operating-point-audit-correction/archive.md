# Archive: formal-nonbinary-ldpc-v32-operating-point-audit-correction — 2026-08-23

**Change:** `formal-nonbinary-ldpc-v32-operating-point-audit-correction`
**Archived to:** `openspec/changes/archive/2026-08-23-formal-nonbinary-ldpc-v32-operating-point-audit-correction/`
**Date:** 2026-08-23
**Schema:** operating-point-audit-correction (A1–A12 + Candidate Fix F-B1/F-C1/F-D1/F-T/F-G1)

## Verdict: ACCEPTED — ARCHIVED

Codex 主控裁决链：
1. 2026-08-22 主审：`EVIDENCE_VALID_BUT_ATTRIBUTION_INCONCLUSIVE`（execution/recount/
   mechanical terminal ACCEPT；B1 matched-control 前提 REJECT）— 见
   `docs/nbldpc-v32-main-review-verdict-20260822.md`。
2. 2026-08-23 correction candidate 整体暂 REJECT（唯一阻塞：infinity iff 语义）。
3. 2026-08-23 verifier-fix commit `3110cb0e` → **F-G1 = ACCEPT** → durable closeout 授权。

## Terminal

- **Change A12 终态：`audit_corrected_rate_aligned_de_required`**（main-adjudication
  层级，A9 矩阵 C01–C13 全 ✓；执行时点 CLI 快照 `audit_verifier_blocked` 系 C13 未满足
  的诚实记录，保留于 corrected_branch_decision.json 不改写）。
- **V32 科学状态**：finite-DE bridge raw record 有效但归因不成立；B1 非 matched control
  （Q_B1 generator/posterior law mismatch，support-miss ≈ 0.2395/0.2541/0.2553）；
  empirical P 仅 nominal budget feasible；原始 Q_B1 信息论不可行。

## Authoritative Evidence

- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v32_operating_point_audit_v2/run_01/`
  八件（含 readonly_review.json 与 operator_handoff.md）。
- 旧审计 `.../nbldpc_v32_operating_point_audit/run_01/` 十件与 V32 bridge run_01 十三件
  字节不变；前者标注四标签 lifecycle。

## Durable Docs

- decision-log：2026-08-23 条目「V32 finite-DE bridge + operating-point audit
  correction — durable closeout (ACCEPTED)」。
- addendum：`docs/nbldpc-v32-operating-point-audit-correction-addendum-20260823.md`。
- memory：`AGENT_PROJECT_MEMORY.md` 顶层 2026-08-23 节（Observed / Rejected
  interpretation / Next authorized boundary 三层）。

## Delta Spec Sync

- Delta spec 不并入 `openspec/specs/`——本变更是 audit-only correction，无可复用方法
  spec（沿用 Change A 先例）。旧审计 change 的 delta spec 同样保持 archived 原样。

## Next Authorized Boundary

唯一下一问题：exact-V31-rate empirical-P ensemble DE（层率表冻结于 d3_next_question.json）。
候选 change `formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic`
处于 `DRAFT_PENDING_FREEZE_REVIEW`；DE 执行需 freeze 后显式授权。fixed-graph /
decoder / NB-Polar successor 选择未决。

## Invariants

- 五 protected roots 与 archive 全部字节不变（29 绑定 SHA256 drift=[]）。
- 无 DE/decoder/graph-builder/raw-pipeline 执行；无 push；AGENTS.md 用户改动保留未 stage。
- 测试终态：T0=8 / T1=26 / T2=13 / 全量 47 passed（含 fix 后两方向 infinity 语义、
  run-root 护栏、manifest 字段级 tamper 全套）。

## Commit Chain

`59ba0236` freeze → `0765d893` impl → `29a5dafe` evidence+review → `3110cb0e`
verifier-fix (ACCEPT) → 本 closeout commit（durable docs + archive move）。
