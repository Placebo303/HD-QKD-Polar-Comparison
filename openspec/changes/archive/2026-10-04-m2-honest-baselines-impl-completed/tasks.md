# Tasks: M2 Honest Baselines (Implementation Record; doc-only, no execution)

本 `tasks.md` 仅为 T10 schema 确认 checklist 与 grant 前门记录。本 change 内不执行其中任何实现/执行动作。若有歧义，停并返回 planner，不猜。

- [ ] T10 — Schema 确认 checklist（全部关闭后方可追认）：
  - [ ] 新键追认：`messages_per_frame_actual`（provisional）、`leak_EC`/`blind_stages` 分解、`f` 三数（本臂 m 基）、`undetected` 隔离、446/3.14 分列，均为新方法自有命名空间；
  - [ ] pin 位：种子 / 段表 / 块长表 pin 位 BLANK 状态确认，grant-time 填（HdCascade seed 占位；layered `2026092001` 与 F4 一致）；
  - [ ] MAJOR-1 消息公式 pin：每帧消息数公式口径 pin；
  - [ ] MAJOR-3 `m_j≤n` 门已加确认；
  - [ ] 4 MINOR 已清确认。
- [ ] Grant 前门（执行授权前必须全部关闭）：
  - [ ] 待澄清表关闭；
  - [ ] F2/F3/F4 pins 填入；
  - [ ] Pre-EXECUTE 机器门（`AGENTS.md` §3/§10.3；显式用户授权 + 目标输出缺席 + 聚焦测试）。

约束：仅允许本 change 两文件；禁建 `design.md`/`specs/`；禁改 `openspec/specs/` 主干、`m2-honest-baselines` 既有文件、M2 三包、M0、`docs/decision-log.md`、`AGENTS.md`；禁写代码、禁执行、禁 commit/push。
