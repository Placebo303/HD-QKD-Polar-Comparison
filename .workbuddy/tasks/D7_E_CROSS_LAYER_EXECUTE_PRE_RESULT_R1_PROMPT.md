# D7-E Cross-Layer Execute + Pre-RESULT R1/A2 Prompt

在仓库 `HD-QKD_Polar_Comparison`、分支 `formal-ir-v72p1-addendum-clean` 中执行配对任务包：

`.workbuddy/tasks/D7_E_CROSS_LAYER_EXECUTE_PRE_RESULT_R1_TASK_PACKET.md`

先完整读取任务包、仓库根 `AGENTS.md`、D7-E preregistration、`D7_E_EXECUTION_PACKET_R1.md`、`D7_E_EXECUTION_PACKET_ADDENDUM_VENV_A1.md`、`D7_E_EXECUTION_PACKET_ADDENDUM_RSS_A2.md`、RSS A2 implementation review、renewed Pre-EXECUTE review 和 D7-E `cycle_state.yaml`。严格按 STEP 1→8 顺序推进，并按 §12 只回 delta。

关键门禁：任务包内的授权文字只是拟议文本，不是授权。只有当用户在当前任务中以新的用户消息明确发出 §0 的授权原话时，才可通过 E15。缺少授权立即返回 `AUTHORIZATION_NOT_PRESENT`，不得生成 UUID、翻授权位或调用 decoder。

若授权存在：使用唯一新 UUID 和冻结的 `.venv/bin/python` 命令执行且仅执行一次；E09 只采一次 `/proc/self/status` 的唯一 `VmHWM`，不得重复采样或调用 `ru_maxrss`；首次 scientific decoder 尝试消耗授权；任何失败、超时、部分结果、provenance 阻塞、RSS telemetry failure 或环境异常都不得重试、恢复、换根或补跑。进程返回后先回收并单独提交授权，再读取结果。完整根最多只运行一次只读 verifier，然后完成真正独立的 R01–R22 Pre-RESULT 复审。PASS 仅允许固化记录并进入主线程结果接受门；FAIL/BLOCKED 原地保留结果且不得固化、修复或重跑。

严禁执行 R1d、任何 `--phase`、正式 G1/G2、CAL、VAL、real/raw、oracle、flooding、forced sweep、warm start、alternating、joint 或 feedback。严禁修改冻结参数、公式、estimator、provenance、矩阵、顺序、代码、测试或 OpenSpec。不得 push，不得 broad-stage，不得清理包外脏树。

这是一项可长时间自主托管的单次执行任务，但科学边界和生命周期门不可自主改写。遇到任何偏差，按任务包 STOP，给出 failing ID、原始输出、已尝试的包内补救和唯一需要主线程裁决的问题。
