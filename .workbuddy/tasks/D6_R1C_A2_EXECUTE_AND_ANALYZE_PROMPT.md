# D6 R1c-A2 §8 autonomous execution prompt

你是 D6 R1c-A2 的长时自主执行与分析操作员。完整任务包在：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D6_R1C_A2_EXECUTE_AND_ANALYZE_TASK_PACKET.md`

先完整读完任务包，再严格依次执行 E0→E6。不要为常规工程判断、中间进度、运行较慢、结果阴性或分析选择询问主线程；只在全部工作完成，或命中会改变冻结科研契约的具体硬 blocker 时返回。

用户的逐字授权如下，必须原样写入授权记录与最终回报：

> 我现在明确授权执行 D6 R1c-A2 §8：仅允许使用冻结的 R1c-A2 实现，对一个全新的 `workspace/d6_graph_mother_r1c_<uuid>/` 根进行一次 development-only 执行；使用固定 Model-F 输入根和 `--workers 18` 请求值，实际并发只能按已评审的 RSS 规则向下调整；总计不超过 2500 次 decoder 调用、12 小时 wall、单次调用 120 秒、总 RSS 小于 2 GiB。授权由首次科学 decoder 尝试消耗；不得重试、恢复、复用任何 VOID 根、修改参数或代码，不得执行任何 `--phase`、正式 G1、G2、VAL、real/raw。运行结束后必须停止并进行独立 Pre-RESULT 复审，复审通过前不得接受或提交结果。

当前冻结基线是分支 `formal-ir-v72p1-addendum-clean`、HEAD `5bd82418`；A2 prereg/OpenSpec=`03eff680`，实现测试=`15f1de79`，独立双评审=`5bd82418`。如实际不符，按任务包 E0 STOP，不自行修复。

E0 通过后只生成一个 UUID，并固定唯一输出根
`workspace/d6_graph_mother_r1c_<uuid>/`。先创建授权记录，将且仅将 D6
`cycle_state.yaml` 的 `development_decoder_authorized` 从 false 翻为 true，按包提交。随后从仓库根恰好调用一次：

```powershell
python scripts/v72p2d6_graph_mother_development.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d6_graph_mother_r1c_<uuid> --workers 18
```

`<uuid>`必须替换为 E0 唯一生成的同一个值。不得生成第二根。首次科学 decoder 尝试即消耗授权；无论成功、失败、timeout、crash、partial、RSS/wall blocker 或结果不理想，均不得重试、重跑、恢复、手工补 cell、换根、改参数或改代码。

进程结束后，在打开结果载荷之前，立即把
`development_decoder_authorized` 恢复为 false 并按包单独提交。然后只允许一次不解码的机械验证：

```powershell
python scripts/v72p2d6_graph_mother_development.py --out-root workspace/d6_graph_mother_r1c_<uuid> --verify
```

接着写未提交 operator return，并交给真正独立的只读 reviewer 完成
`D6_R1C_A2_PRE_RESULT_REVIEW_PASS|FAIL`。执行操作员不得自审。FAIL 就停止，绝不修复或重跑；PASS 后才可对已有六文件标量做深入分析、形成结果报告并按任务包白名单本地提交。分析可以充分，但不得新增 decoder calls，不得自行接受结果或启动后继路线。

硬禁令：不运行任何 `--phase`、正式 G1、G2、P0、VAL、real/raw；不读三个 VOID 根内容，不复用其根；不碰正式证据根；不改代码、测试、OpenSpec、科学参数或冻结文件；不 broad-stage、不 clean/reset/stash/checkout/rebase/amend、不 push。工作树中 V35、perf-v38、CRLF churn 和其它既有脏项全部原样保留。

必须持续记录进程和 worker 身份；只终止本任务确切启动的进程。严格执行 2500 calls、43200s、120s/call、aggregate RSS<2GiB、RSS 降核只允许 18→14→12→8、无 retry。任何未知 RSS、预算越界、fsync/verify/证据不一致均按冻结终局 fail-closed，不得通过修改结果文件来“修好”。

完成后只回任务包 §10 的 delta，不复述项目历史，并原样结束：

`D6 R1c-A2 已完成唯一授权的 development-only 执行；授权已消耗并恢复为 false；结果已完成独立 Pre-RESULT 复审与有界分析，但尚未由主线程接受；正式 G1 未重跑，G2 未授权、未执行。`
