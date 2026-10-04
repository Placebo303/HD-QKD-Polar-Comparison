# Tasks: M2 Honest Baselines (spec-only; no code in this change)

本 `tasks.md` 为后续**实现 change** 的有序任务冻结（spec-only 本 change 内不执行其中任何一项）。若任务有歧义，停并返回 planner，不猜。

- [ ] T1 — Cascade 改①二进制映射 10bit→Gray 位面分组（`design.md` §2 命名 + 待澄清表①行）：增量起于 `cascade_lite.py` + `cascade/single_kernel.py`，只增不改既有逻辑；歧义处标待澄清、不猜数。
- [ ] T2 — Cascade 改②按位分组块长调度（`design.md` §2 命名 + 待澄清表②行）：同上增量约束；块长表真值待 `/opsx-explore` 关闭后才可填。
- [ ] T3 — Cascade 改③级联传播规则（`design.md` §2 命名 + 待澄清表③行）：同上增量约束；歧义处标待澄清、不猜数。
- [ ] T4 — Cascade 并行版消息数会计：每帧消息数口径（Müller 446 vs 3.14），`leak_EC` + 64 tag + 控制轮次分列。
- [ ] T5 — 分层二元分配表：逐 Gray 位面熵分配（冻结 H_L1+H_L2：0.801038 / 0.825566 / 0.832563，不重拟合），替换 V19 f=4.169 稻草人。
- [ ] T6 — 分层二元每位面构造（n=64 族语义保持；参数由实现 change 冻结）。
- [ ] T7 — 分层二元盲协调：多段小步长；二元 SPA `max_iter`–streak 冻结；综合征一致 + Toeplitz t=64 成功条件。
- [ ] T8 — 两方法 fake-only 单测（Cascade）：注入 fake，不触真实数据/解码器执行。
- [ ] T9 — 两方法 fake-only 单测（分层二元）：同上。
- [ ] T10 — A-CMPE-1..7 映射自查：逐条引用 ID，确认双数/分列/隔离/四列归属/claim ceiling；无 schema 改动确认（AGENTS §5.3）。

约束：实现 change 须遵守 proposal/design 的 schema 稳定声明与歧义"待澄清表"规则；禁改 `openspec/specs/` 现有文件。
