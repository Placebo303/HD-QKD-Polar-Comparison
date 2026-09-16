# D7-E RSS Telemetry Rework — WSL A2 Prompt

在 `HD-QKD_Polar_Comparison` 的 `formal-ir-v72p1-addendum-clean` 分支执行：

`.workbuddy/tasks/D7_E_RSS_TELEMETRY_REWORK_VENV_A2_TASK_PACKET.md`

完整读取任务包、仓库根 `AGENTS.md`、D7-E OpenSpec、R1/A1 execution packets、renewed Pre-EXECUTE review、现行 RSS 实现/测试和 cycle state。按 T0→T7 自主完成；只回 §12 delta。

这是零 decoder 的 WSL telemetry 修订，不是 D7-E 执行授权。不得生成 UUID、翻授权位、创建 D7-E 科学根或运行任何 scientific decoder。核心修订固定为：Linux/WSL 只从 `/proc/self/status` 的唯一 `VmHWM: <positive integer> kB` 读取当前进程峰值 RSS，严格换算为 bytes；不可读或不合法即 fail-closed；不再让 `ru_maxrss` 参与 WSL 决策，不引入 psutil、subprocess、重试、轮询、平均或 provider 框架。

先冻结 OpenSpec/addendum，再实现最小 parser/read wrapper，补确定性 fake 测试，完成独立 implementation review 和 renewed Pre-EXECUTE review。live E09 只允许在最终 Pre-EXECUTE 中运行一次，不得采样到满意为止。任何 in-scope regression、科学常量漂移、root/UUID 出现、授权变化或 scope 越界立即 STOP，不自行扩修。

允许长时间自主推进实现、测试、复审和本地 scoped commits；不得 push、broad-stage、清理包外脏树，也不得顺便修复无关 stale tripwire。最终必须停在 fresh explicit authorization 门，旧授权不可复用。
