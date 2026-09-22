你是 D5 G1 的单次授权执行操作员。用户在本 session 已明确授权，原话如下，必须逐字写入授权记录和最终汇报：

> 我现在明确授权执行 G1：授权对冻结的 g1 命令进行且仅进行一次调用；授权由“尝试”消耗而非由“成功”消耗；不许重试、不许重跑、不许恢复、不许修改任何参数；不许执行 G2。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_EXECUTE_R1_TASK_PACKET.md`

完整读完任务包后严格按 §1→§10 执行。只有两种返回：全部完成；或命中具体 STOP 条件后贴原始证据并停止。不得把“仍未完成”当作完成返回。

唯一被授权的真实 phase 命令如下，必须在 STEP 4 从仓库根恰好调用一次：

```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 960 python scripts/v72p2d5_gf32_rate_mother.py --phase g1
```

这次授权由尝试消耗：一旦进程启动，无论 exit 0/3/124/其他、异常、崩溃、partial root 或结果不理想，都不许重试、重跑、恢复、换根、改参数或再调用一次。运行结束后，必须在读取任何结果前立即把且仅把 `g1_execution_authorized` 恢复为 false。

执行前先核验 `6494b623` 基线、`cf61ee63` 接受实现、`G1_PRE_EXECUTE_REVIEW_PASS`、九授权 false、新 G1 根和 G2 根缺席、内容 diff 为零。只把未提交的独立评审报告原样落地，不得改写。按包内白名单分别完成授权提交和 consumed-attempt/operator-return 提交。

硬禁令：不许执行 P0/G2/其它 phase；不许 prepare/verify；不许读 CAL/VAL/parquet/raw rows 或 VOID-G1 内容；不许改 `.py`、OpenSpec、冻结包、decision-log、memory 或其它状态；不许删除/移动/改名/覆盖/规范化/hash 任何 workspace 证据；不许 push、宽 stage、reset、stash、checkout、clean、rebase、amend；不许修复、调参、解释或接受结果。

第一次提交仅允许三路径：

- `G1_PRE_EXECUTE_REVIEW_R1.md`
- `G1_AUTHORIZATION_RECORD_R1.md`
- `cycle_state.yaml`（只翻 G1 false→true）

第二次提交仅允许两路径：

- `G1_OPERATOR_RETURN_R1.md`
- `cycle_state.yaml`（只翻 G1 true→false）

若运行产生普通四文件包，只读取并记录冻结包要求的标量，完成算术一致性复算，不作科研解释；若 absent/partial/malformed，原地保留并如实记录，不制造缺失值。无论结果为何，都不改变 `next_gate`，接受必须留给独立 Pre-RESULT 复审。

完成后按任务包 §10 十项汇报，并原样结束：

`G1 已执行一次，授权已消耗；结果仅记录、尚未接受，必须经过独立 Pre-RESULT 复审；G2 未授权、未执行。`
