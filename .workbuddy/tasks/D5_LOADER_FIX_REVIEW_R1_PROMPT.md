# Paste-ready prompt — D5-LOADER-FIX-REVIEW-R1 independent review

Copy everything between the two `=====` lines into a FRESH session opened in
`D:/Code/HD-QKD_Polar_Comparison`. Do not reuse the session that wrote the fix.

=====

你是本次的**独立只读评审**。你没有写这个修复，也没有参与之前任何一次 D5 任务包的
执行；不要采信任何既有说法（**包括任务包 §3、§6 里转述给你的那些**），一切从源码
和实测重新推导。

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_LOADER_FIX_REVIEW_R1_PACKET.md`

先完整读完，再按 §2 → §8 执行。

被评审对象：commit `299416ae`（HEAD）与新增 OpenSpec change
`openspec/changes/v72p2d5-p0-model-f-consumer-path-fix/`。

要裁的问题：**这个修复是否正确、是否在范围内、测试是否足够——以及仓库现在是否
适合发起一次新的 P0 授权。**

背景：2026-09-07 一次已授权的 P0 调用在 0.376 秒内被拒，报
`MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`，而产物完好。根因是消费侧靠
包导入够产物，而 `python scripts/...` 启动时仓库根不在 `sys.path` 上。这次授权被
白白消耗掉了。

必须自己做、不许略过的几项：

1. **§5 可达性探针必须你自己跑。** 这是整起事故的关键点，不许采信任何人的结论。
   直接调 `run_p0_cost_synthetic`（不走 CLI，故不涉及授权），传 `authorized=True`
   + 正式根之外的全新 tmp `out_dir` + 首调即抛唯一哨兵的 probe decoder。期望拿到
   哨兵、probe 恰好被调 1 次、tmp 目录为空。跑完确认 P0/G2 正式根仍不存在、
   Model-F 根仍是 2 文件且大小 mtime 未变。**失败即阻塞发现。**
2. **§3 那处实现者自曝的判断题要你独立裁。** 兄弟模块自身按包名 import 对比度模块
   （`v72p2d3_gf32_contrast`），脚本启动下同样失败，于是实现者把它按文件路径预载并
   用 `setdefault` 注册进 `sys.modules` 的两个包名下（未改 `sys.path`、未改兄弟
   文件）。你要判断：这是"被指派修复的最小补完"还是"扩范围"？**特别要想清楚**：
   往 `sys.modules` 里塞本来不存在的包名，会不会在同进程别处（尤其 pytest 里
   rootdir 本来就在 `sys.path` 上、真模块可能已导入或稍后导入）造成遮蔽或冲突？
   `setdefault` 这层保护够不够？把风险讲明白。
3. **§4 测试是否真覆盖了逃逸条件。** 之前 195 个测试全绿却漏掉了这个 bug。看新增的
   `M22a`–`M22e`：有没有真的模拟脚本启动条件（仓库根与 `''` 都不在 `sys.path`），
   还是只对解析出来的路径做断言？有没有任何测试读了真实 Model-F 正式根（**不许**）？
   SAFE A/B/C 与 AST 静态守卫是否原封未动？
4. **§6 工作区状态发现，只评估不修。** 有一个只读检查发现：2026-09-07T17:22:29
   全部跟踪文件 mtime 同时变化，`git status` 现在报约 1887 个文件已修改，但
   `git diff` 对它们**没有任何文本内容差异**——只是行尾表示不同。你要独立核实数量、
   核实 `299416ae` 本身有没有夹带行尾变更、核实
   `test_T1_22_openspec_history_zero_mod` 是否仅因此失败，并判断这是化妆品问题还是
   实质问题、**是否阻塞新的 P0 授权**（R2 执行包有一个 `E6 干净跟踪树` 门禁会被它
   卡住）。给出你要求的处置方向：把清洁度门禁收窄到真实内容差异，还是要求仓库侧
   规范化。**只给建议，不许自己动手。**

硬约束：

- 授权 false。不许跑 decoder；不许跑 P0/G1/G2（除那次必须 exit 3 的未授权拒绝
  检查）；不许跑 prepare 脚本；不许读 CAL/VAL/parquet 行。
- **一旦 P0 或 G2 正式根出现，立刻 STOP 并作为严重发现上报。**
- `workspace/` 下除你自己新建的 pytest basetemp 与 tmp 目录外不许写；读真实
  Model-F 产物**仅限** §5 探针那一次。
- 不许改任何 `.py`、既有 `.md`、OpenSpec、`cycle_state.yaml`。
- **特别强调**：不许 `git add`、`commit`、`push`、`reset`、`stash`、`checkout`、
  `clean`、`rebase`、`revert`、`add --renormalize`，以及任何会写入跟踪文件的操作
  ——正因为 §6 那个批量重写发现，这条比平时更要紧。
- **发现问题只报告，不修复。** 查不动的标 `NOT_VERIFIABLE` 并写明原因。

产出：**只允许新建 1 个文件**
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/LOADER_FIX_REVIEW_R1.md`，
内容按任务包 §7。结论只能二选一：`LOADER_FIX_REVIEW_PASS`（并写明这不是授权，
以及授权时必须成立的条件）或 `LOADER_FIX_REVIEW_FAIL`（点名阻塞发现 + 重审前
必须做的那组修改）。

明确不主张的清单里必须包含这一条：**可达 ≠ 跑得完**，不许预测 P0 现在就能完成。

最后在消息里汇报：结论、检查表简表、可达性探针原文输出、`sys.modules` 风险判断
（一两句）、工作区发现与你的处置建议、pytest 原文行，以及——仅当仍成立时——

「P0 未授权、未执行；正式根仍不存在；next_gate 仍为 P0_PACKET_REVIEW。」

=====
