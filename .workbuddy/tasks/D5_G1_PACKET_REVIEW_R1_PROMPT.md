你是 D5 G1 冻结包的独立只读评审。你没有编写该包，也没有参与 P0/G1 的执行；不要采信作者自报结论，必须从源码、OpenSpec 与已接受记录独立核实。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_G1_PACKET_REVIEW_R1_TASK_PACKET.md`

被评审对象：
`D:/Code/HD-QKD_Polar_Comparison/docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_EXECUTION_PACKET_R1.md`
提交：`4bf2682a`

先完整读完任务包，再按 §2→§7 执行。结论只能是 `G1_PACKET_REVIEW_PASS` 或 `G1_PACKET_REVIEW_FAIL`。

这是只读评审，不是实现，也不是授权。禁止 decoder、任何 `--phase`、prepare/verify、CAL/VAL/parquet 行读取、workspace 证据写入、代码修改、既有文档修改、OpenSpec/状态修改，以及所有 git 写操作。

只允许新建：
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PACKET_REVIEW_R1.md`
不要提交，不要 push。

重点不是核对表面数字，而是裁清五件会决定 G1 是否有科学意义的事：

1. 旧 G1 根是永久 VOID，新授权运行必须使用一个真正不存在的新根；
2. Windows current-process working set 是否足以作为 2 GiB gate，以及怎样采样才配叫 peak；
3. 当前全零 exact 率也会 monotonic/pass，必须在看新数据前决定最小 meaningful-signal 规则；
4. 900 s 是科学预算，960 s watchdog 只是杀进程边界，不能混为一谈；
5. terminal labels 必须把 no-signal、nonfinite/crash、resource overrun、timeout 与 pre-exec blocked 分开，不能都塞进一个 `passed`。

对 D1–D6 逐项给 ACCEPT/REVISE/REJECT。对 OQ-G1-ROOT/RSS/SIGNAL/WATCHDOG/OUTCOME 必须逐项 DECIDED；任何一个仍 OPEN，整体就是 FAIL。

对 signal 规则保持前瞻性：不要用 VOID G1 根里的任何数字，也不要读取或引用它作为性能证据。你可以接受任务包推荐的“非递减 + top>0 + 严格改善或双点饱和 1.0”规则，也可以给一个更好的精确规则，但不能引入事后调参。

一般不需要跑 pytest：这是 packet review，源码阅读和算术足够。不要为了获得一个绿色数字而扩大执行面。

最后按任务包 §7 汇报，并原样写：

`G1 包评审不构成授权；G1 未执行；新 G1 根与 G2 根仍不存在。`

