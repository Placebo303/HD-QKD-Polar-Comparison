你是 D5 当前两层 GF32 rate-mother/BP 路径的独立 route-stop 评审。不要采信实现者的 terminal class、CAL 分数、75-call 统计或路线结论；直接审计 prereg、脚本、JSON、源码和提交，并按任务包做有限独立复现。

任务包全文：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_ROUTE_STOP_REVIEW_R1_TASK_PACKET.md`

基线 HEAD `d6fabf09`；链 `247f8adc → f0e4a1cf → d6fabf09`；当前 gate `D5_ROUTE_STOP_REVIEW`。完整读包后按 S01–S12 执行，结论只能是 `D5_ROUTE_STOP_REVIEW_PASS` 或 `..._FAIL`。

重点防止过度外推：`L1_BP_THRESHOLD_NOT_RECOVERABLE_AT_N64` 只能表示预注册的3 estimator/grid、4 paired blocks、测试矩阵/decoder 下没有恢复，不能写成普适 BP 阈值定理。“E2 optimum”只能指冻结候选族。route-stop 只能关闭当前 D5 两层 rate-mother/BP operating path，不能否定 GF32、NB-LDPC、其他图/decoder、larger blocks 或真实数据路线。

在独立非正式 review root 内最多运行12次显式注入的 development calls，复核 E2 的 n64 m59/m64 与 n256 m236/m256，并重点复现 seed 2026090601 的 syndrome-ok/exact-false 事件。每call 120s watchdog，绝不调用CLI phase或正式根。随后 fresh 跑四文件D5套件，要求零失败。

硬禁令：不许正式G1重跑/恢复、G2、VAL、真实IR、正式根写/hash/删移、VOID读取、改代码/测试/OpenSpec/状态/日志/memory/既有报告、修复、git写/push/cleanup。唯一新建持久文件 `D5_ROUTE_STOP_REVIEW_R1.md`，不提交。

PASS closure 必须精确为 `D5_CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH_STOPPED`，且只说明当前路径不应进入G2/n1024；后继必须另立改变明确算法组件的新 proposal，由主线程选择。

按任务包 §5 回报并原样结束：

`D5 当前两层 rate-mother/BP 路径停止候选已完成独立评审；这不否定 GF32/NB-LDPC 主线，也不授权 G2 或任何后继执行。`
