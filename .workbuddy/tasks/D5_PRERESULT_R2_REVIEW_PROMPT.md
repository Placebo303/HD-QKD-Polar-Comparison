# Paste-ready prompt — D5-PRERESULT-R2 independent Pre-RESULT re-review

Copy everything between the two `=====` lines into a FRESH session opened in
`D:/Code/HD-QKD_Polar_Comparison`. Do not reuse the session that executed
D5-DISPO-R1 — this review must be independent of the work it reviews.

=====

你是本次的**独立只读评审**。你没有参与被评审的实现、处置记录或上一个任务包的
执行；不要采信任何既有结论，一切从实际产物重新推导。

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_PRERESULT_R2_REVIEW_PACKET.md`

先完整读完，再按 §2 → §7 执行。

要裁的问题（不要预设答案）：上一次独立评审
`MODEL_F_INPUT_PRE_RESULT_REVIEW_R1.md` 给出 `PRE_RESULT_REVIEW_FAIL`，唯一
blocker 是 PR16——未授权的 G1 正式产物 `workspace/v72p2d5_g1/20260906_r1/`
（`decoder_calls=440`）在 `g1_execution_authorized=false` 时存在。此后主线做了
**纯文档处置**（commit `b986ca11` / `7c59d375` / `20204726`）：把该目录原样保留，
以记录方式判为作废，而**没有删除**。

**你要独立判断：这个记录式处置是否足以清除 PR16。** PASS 和 FAIL 都是合法结论，
按你自己核出来的证据说话，不要因为主线已经做了处置就倾向于放行。

硬约束：

- 授权状态 false。不许运行 decoder，不许运行 `--phase p0-cost|g1|g2`，不许运行
  `v72p2d5_prepare_model_f_input.py`（prepare/verify 授权已消耗，禁止重放）。
- 不许 `pandas.read_parquet`、不许读 CAL/VAL/原始行；pyarrow 只读元数据可以。
- `workspace/` 下一律不许删/移/改名/复制/规范化/算 hash/以写模式打开；
  `stat`、`json.load`、`numpy.load(allow_pickle=False)` 可以。
- 不许改任何 `.py`、任何既有 `.md`、`cycle_state.yaml`、`decision-log.md`、
  `AGENT_PROJECT_MEMORY.md`、`openspec/**`、任何既往评审文件。
- 不许 `git add/commit/push/reset/stash/checkout --/clean/rebase/revert`。
- 不许改任何 `*_execution_authorized`、不许接受结果、不许推广、不许授权 P0。
- 不许写 `RESULT_SUMMARY` / `OPERATOR_RETURN` / `run_01`。
- **发现问题只报告，不修复。** 查不动的项标 `NOT_VERIFIABLE` 并写明原因，不要
  猜，也不要悄悄换成更弱的检查。

必须自己重算、不得抄 R1 数值的部分：Model-F 两个文件的存在性与键名、
`counts_ab` 的 shape/dtype/sum/min/max/nonzero/负值、`p_b` 的
shape/dtype/sum/有限性、边缘恒等式
`p_b == counts_ab.sum(axis=0)/counts_ab.sum()`（报最大绝对偏差，并说明错轴
`axis=1` 是否可区分）、summary JSON 全字段及其与数组的自洽性。与 R1 有出入就
明确写出来——R1 是证据，不是权威。

重点判断项（这条决定隐患是否会复发）：读 `TEST_ISOLATION_REWORK_EVIDENCE_R1.md`
声称的 SAFE A/B/C 隔离与 AST 静态守卫，再去看测试源码，判断
`authorized=True` 的合成调用现在是否**仍有可能**触到生产 decoder 或正式输出根。

产出：**只允许新建 1 个文件**
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/MODEL_F_INPUT_PRE_RESULT_REVIEW_R2.md`，
结构比照 R1（编号检查 + 每项 PASS/FAIL/NOT_VERIFIABLE + 重算值 + 前后 stat 快照
+ 明确写出你执行了什么、没执行什么 + 结论块）。结论只能二选一：

- `PRE_RESULT_REVIEW_PASS`（`READY_FOR_MAIN_RESULT_ACCEPTANCE`，并写明这只是
  就绪信号，不等于接受，也不等于 P0 授权）
- `PRE_RESULT_REVIEW_FAIL`（点名唯一 blocking 检查 + 主线需做的唯一决定）

无论哪个结论，都要写出证据支持的最强论断，以及明确不主张的清单（不主张 FER、
泄漏、密钥率、资格、方法结论、G1 性能结论）。

不许新建其它文件，不许提交，不许推送，不许改状态，不许授权 P0。

最后在消息里（不是文件里）汇报：结论、检查表简表、pytest 原文行、与 R1 的分歧，
以及——仅当它仍然成立时——这一句：

「PR16 仅以记录方式处置；P0 未授权。」

=====
