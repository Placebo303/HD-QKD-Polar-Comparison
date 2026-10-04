## Historical implemented scope — formal-ir-v72p2d2-orthogonal-oneblock-triage

This section preserves only the archived, reviewed scope named below. It does not change the archived source. Current repository AGENTS.md and reboot handoff R1–R9 take precedence. This historical merge grants no new execution, acceptance, qualification, promotion, publication, decoder work, or probe restart.

<!-- Source: openspec/changes/archive/2026-10-04-formal-ir-v72p2d2-orthogonal-oneblock-triage-completed/specs/spec.md -->

## S-CLAIM：判别和科学边界

- **S-CLAIM-01**：L 只有 candidate escape、violation 下降或
  `syndrome_satisfied` 才支持调度路线；仅 runtime 变快不算纠错改善。
- **S-CLAIM-02**：I 只有 escape、violation 下降或 `syndrome_satisfied` 才支持
  该映射；单块不得证明普遍图因果。
- **S-CLAIM-03**：P 的消息/翻转变化但未满足 syndrome 只能归为 prior 影响；完全
  不变只削弱 prior-only 解释；不得宣称 M2 优胜。
- **S-CLAIM-04**：L/I/P 均无 hard-bit escape 时 SHALL 停止 binary edge-level
  flooding/layered/damping 微调，后继限定为 grouped-symbol mask BP tiny
  exhaustive 或同块 GF32 对照。
- **S-CLAIM-05**：任一臂出现 syndrome_satisfied 只允许进入同路线小样本
  confirmation plan，不直接进入 V73；不得作 FER、SKR、信息极限、LDPC 无效或
  跨 session 推广断言。
