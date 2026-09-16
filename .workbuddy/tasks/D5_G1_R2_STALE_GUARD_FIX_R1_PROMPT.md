你负责完成 D5 G1 information-recovery R2 候选的唯一已知测试收口。任务很窄，但你可以自主诊断同一根因造成的测试问题并迭代到完整三文件套件全绿，无需逐步请示。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_R2_STALE_GUARD_FIX_R1_TASK_PACKET.md`

基线 HEAD `21576add`。当前唯一已知失败是 `test_G1R01_fresh_root_literal_and_old_barred` 末尾仍断言合法的 `workspace/v72p2d5_g1/20260907_r2` 必须不存在。把它改成与函数开头快照比较的不变性断言，保留所有 root literal、old-root exclusion、VOID retention 和全根不变性检查。

同时最小扩展 `test_T1_23_no_formal_root_absence_assertion`，让它除既有 `assert not root.exists()` 外，也能捕获这次漏掉的 `_snapshot_dir(formal-root) is None` / `== None` 等价缺席断言。不要把它重写成通用静态分析框架。

只允许改 rate-mother 测试文件和现有 R2 OpenSpec `tasks.md`；不改生产代码、状态、报告、memory、decision-log 或 workspace 证据。不得运行 decoder/phase/诊断或读 Model-F/CAL/VAL。跑 focused 和 exact 三文件套件到零失败，使用独立 basetemp，只删自己目录。

按任务包精确暂存两文件、提交、不 push。完成后按 §6 汇报并原样结束：

`R2 候选已完成测试生命周期收口；生产实现与正式证据未改，等待独立信息恢复评审。`
