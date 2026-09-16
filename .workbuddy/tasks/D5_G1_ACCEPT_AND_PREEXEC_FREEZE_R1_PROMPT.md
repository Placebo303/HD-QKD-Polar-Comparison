你是 D5 G1 的文档生命周期 session。本任务只接受已经独立评审通过的 readiness 实现并冻结 Pre-EXECUTE 包；不授权、不执行 G1。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_ACCEPT_AND_PREEXEC_FREEZE_R1_TASK_PACKET.md`

完整读完后严格执行 §1→§8。

先核验两个评审文件：主体必须为 `G1_READINESS_CODE_REVIEW_PASS`，补遗必须为 `G1_CODE_REVIEW_SCOPE_ADDENDUM_PASS` 且准确记录三个 pytest 文件 `219 passed`。任一不符就 STOP。

只允许七个路径：落地两个评审文件；新建 `G1_IMPLEMENTATION_ACCEPTANCE_R1.md` 和 `G1_PRE_EXECUTE_PACKET_R1.md`；修改 cycle_state；append decision-log 与 memory。禁止任何代码或 workspace 变更。

Pre-EXECUTE 包必须冻结：实现 `cf61ee63`、新根 `20260907_r2`、440 calls、900 s 科学墙钟、960 s watchdog、2 GiB peak RSS、前瞻 signal、七个 outcome、一次授权按尝试消耗、无 retry、独立 Pre-RESULT 才能接受。

cycle_state 只能新增五个 G1 implementation 字段并把 next_gate 改到 `INDEPENDENT_G1_PRE_EXECUTE_REVIEW`；九个授权位与 promotion 必须保持 false。不得新增 attempts/completed/result。

不跑 pytest，不跑 decoder，不跑任何 `--phase`，不读 CAL/VAL/parquet 行，不碰正式根，不 push。只用逐路径 stage；暂存不恰好七路径就 STOP，不自行 reset/checkout。

完成后按 §8 汇报，最后原样写：

`G1 readiness 实现已接受且 Pre-EXECUTE 包已冻结；G1 仍未授权、未执行；等待独立 Pre-EXECUTE 评审。`
