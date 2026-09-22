# Prompt — D5 decomposition successor closeout A1

继续当前任务，但只执行作者修订件：

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/D5_DECOMPOSITION_SUCCESSOR_CLOSEOUT_A1_TASK_PACKET.md`

主线程已明确裁决：

- Q1 = YES：允许且仅允许一次新鲜的四文件 pytest 独立验证；不是科学 decoder 重跑，不许 retry。
- Q2 = YES：允许一次只读 names/sizes/mtime_ns 元数据采集；stat 不算修改或“碰证据”，但仍禁止读内容与 hash。
- 不得伪造缺失的原始 pre-snapshot。DS13 改按 A1 的“既有接受基线一致 + mtime 早于首个新分数 + 包内零路径触碰 + A1 测试前后元数据一致”关闭。

严格执行：baseline → A1 测试一次 → 安全删除仅自己的 basetemp → 只读保护根 stat → 写唯一 `TEST_EVIDENCE_APPENDIX.log` → 单文件第4 commit → 独立读回关闭 DS12/DS13/DS15。任何失败或偏差立即 STOP，贴原始输出，不重跑、不修复。

不得编辑既有 report/state/log/memory/code/tests/OpenSpec；不得运行 decoder 或任何 `--phase`；不得读正式根内容或 VOID；不得执行/创建 G2；不得 push/clean/reset/stash/checkout/amend/rebase。已知 CRLF porcelain 噪声保持原样。

完成后只回报 A1 delta，不重述整个历史。不要开始 graph/mother successor；最终 gate 保持 `D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL`。

