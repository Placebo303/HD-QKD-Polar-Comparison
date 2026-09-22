# NOW — 一屏现状（2026-09-22，docs-only，H0.5）

> 新会话只读本页 + `docs/EXECUTION_PLAN_20260922.md` 即可接手。
> 本页不授权任何执行（无解码 / DE / 真实数据 / commit / push / 资格化 / 发表）。
> Track：documentation-only（AGENTS.md §1.2 矩阵，无 track gate）。

## 1. 分支 / HEAD（读取于 2026-09-22；**任何执行前必须重测**）

- 分支：`formal-ir-v72p1-addendum-clean`
- HEAD：`051e3687`（hygiene: H0.1 commit X1 scoped tree + F1 fix + G0=B log）
- 工作区（读取于本次编辑）：2 个 tracked dirty（`.gitignore`、
  `docs/EXECUTION_PLAN_20260922.md`）+ 5 个新 docs 未提交
  （`H0_3_ISOLATION.md`、`H0_4_INTERPRETER.md`、本页、
  `S0_1_M200_PACKET.md`、`S0_1_M200_PROMPT.md`）；另存在外源未跟踪目录
  `openspec/changes/binary-ldpc-v5-*`（并行 checkout，**禁止纳入本线 commit**）。

## 2. G0 状态

- **G0 = (B) 已裁决**（2026-09-22 用户书面给出）：主文主张 =
  实测效率曲线 + 同数据二元 MLC/R3 对照；(A) 文献可比认证作
  并行/第二代扩展。

## 3. 已完成

- **H0.1** X1 scoped 提交：`051e3687`（G0=B 授权记录在案；无执行授权）。
- **H0.2** 具名分支推送 + **PR #1：OPEN，未 merge**。

## 4. 活跃门（未过 = 对应动作禁止）

| 门 | 状态 / 含义 |
|---|---|
| **S0.1-gate** | 未过：m=200 软边际 FER 实测缺失 → 禁按既有外推冻结 P1 |
| **P3-gate** | 未过：真实帧记忆审计未执行 → 禁把合成 FER 当真实 FER |
| **P5-gate** | F2 已落地（G0=B 下报告完整性门）→ P5 可进入独立冻结；未冻结前不可启动，仍禁执行 |
| **P6-gate** | 未过：吞吐缺口未量化写入对外表述 → 禁“真实场景可用”句 |

## 5. 禁止事项（全文有效）

1. **P1 重臂**（3600 s 级）需**独立冻结包 + 独立授权**，且先过 S0.1-gate。
2. **P5** F2 已落地；仍需 **独立冻结包** 过 P5-gate 后方可执行（当前无执行授权）。
3. **禁 `f_eff ≤ 1.3` 认证句**：G0=(B) 下不得对外写该单点认证主张。
4. **禁 merge 姊妹线**：不把 `polar-mainline` / 姊妹 checkout 内容并入本线，
   也不向姊妹线分支推送；发布只走命名 formal-IR 分支 + PR，普通非强制 push。
5. **禁 `git add -A`**：只按 scoped manifest 提交，防止外源
   `binary-ldpc-v5-*` 混入（crosstalk 风险）。
6. 本页与本计划均不授权执行；每个 EXPLORE/DECIDE 包仍按
   AGENTS.md §1.2 / §10.3 独立授权与评审。

## 6. 权威指针（细节按此顺序下钻）

1. **PLAN** — `docs/EXECUTION_PLAN_20260922.md`（排期、门禁、卫生轨）
2. **ROADMAP** — `docs/ROADMAP-20260921.md`（科学宏观路线 P0–P6、DECISION）
3. **BASELINE** — `docs/V80_BASELINE_20260921.md`（冻结科学口径）
4. **cycle** — `docs/research_cycles/V80-NBLDPC-JAN21/`（专题证据与 log）

冲突规则：科学冻结口径以 ROADMAP / V80_BASELINE 为准；排期与卫生动作以
PLAN 为准；README / HANDOFF 的状态段仅保留指向本页的指针。
