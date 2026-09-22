# D6 R1c-A5 结构有效性与修复研究 prompt（零 decoder）

你负责一个可自主托管的 D6 R1c-A5 任务。完整任务包：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D6_R1C_A5_VALIDITY_REPAIR_R1D_READINESS_TASK_PACKET.md`

完整读完后按 §0→§12 连续完成。不要为普通代码判断、测试修复、结构分析、写文档或运行时间询问主线程；仅在全部冻结项完成或出现会改变冻结科研契约的唯一 blocker 时返回。

当前事实：R1c-A3 已被主线程采纳为“实现/结构阻塞的开发尝试”固化结果（`PASS_BLOCKED_RUN`，stored 的 `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` 保留但不得引用），R1c-A4 已被采纳为 `READY`（仅结构路径，10897.7s→2.5s，n64 逐标量相等），但两者都不授权任何 run。起始 HEAD 应为 `1a09220a`。

主线程已用只读结构审计（零 decoder，独立脚本在 `workspace/mainthread_a5_audit_7f3c1d9ab2e54a6f8c0d1e2f3a4b5c6d/`）确认：冻结 eligibility 只检查**变量**度，从不检查**检查行**度；T3/T4 在 f1.2+square 前缀出现度=1 行，M1 在全部宽度/层出现度=1 行，M2 在 L2 square 出现度=1 行；T2 在 n64 rank 缺秩（63/62 vs 64）；B0/B1 在 n128 L2 有 base-pair 重复、n256 前缀不连通。A2 只暴露出 T3/M1，是因为旧闸门选中的就是 {B0,B1,T1,T3,M1}。若只补最小度闸门，n64 只剩 {B0,B1,T1}，且没有合格的 M 臂→§8.4 scaling 失去 M 腿，实验近乎空转。因此主线程路线裁决为：**有效性收口 + 可采纳的构造修复 + R1d 就绪包**（不是停线，也不是纯闸门）。

本任务绝对不授权任何 decoder：不许运行、重试、恢复、补 cell、新建科学根；不许 `--phase`、G1、G2、VAL、real/raw；不许改 R1c-A2 六文件根或已提交的 A2/A3 证据；不许改 D5/`v35`/`src`/`experiments`/`tools`；不许改 arms/seeds/rows/prior/decoder/coefficient/SC 宽度/M 的 N2/选择与终局阈值；不许随机搜索、种子调参、参数扫描；不许以 decoder 结果挑选修复（本任务零 decoder，违反即契约违规）。修复候选只在沙箱模块里探索，生产 builder 输出必须与 HEAD 逐字节相同；落地的只有 A5-03 的 I1 闸门与 A5-06 的执行期 crash 优先级终局。

先 OpenSpec/prereg，再独立复现全量有效性矩阵（不得继承主线程脚本或结论），再做逐族根因证明，再落地闸门+执行完整性（含 fake-only 测试），再做可采纳修复研究与性能/等价守卫，再做 R1d 结构成本投影（§7b A5-10：若修复后 T2 成为冻结 fallback，n128/n256 的 T2 构造仍是小时级，必须按 chunk 5400s 预算判定“需 A6 优化”或“该宽度不可派发”），再做两个独立只读评审（代码 + 有效性/就绪），最后写 R1d 就绪包并 append-only 更新 cycle_state/decision-log/memory。修复不可行时给出 `STRUCTURALLY_INFEASIBLE_AS_FROZEN` 证明与最小重定义菜单（标记 `REQUIRES_MAIN_THREAD_RULING`，不得落地）。任何 R1d 执行仍需新的 Pre-EXECUTE + 主线程显式授权；不得自行接受结果、不得请求授权、不 push。工作树里 V35、perf-v38、CRLF churn 和其它既有脏项全部原样保留，严格逐路径 stage。

完成后按任务包 §12 只回 delta，并原样结束：

`D6 R1c-A5 有效性收口与修复研究已完成并独立复核：I1（检查行度≥2）缺陷已证明并被闸门封堵，修复候选与 R1d 就绪包待主线程裁决；全程零 decoder 调用，R1c-A2 根保持 immutable，授权全 false，G2 未授权、未执行。`
