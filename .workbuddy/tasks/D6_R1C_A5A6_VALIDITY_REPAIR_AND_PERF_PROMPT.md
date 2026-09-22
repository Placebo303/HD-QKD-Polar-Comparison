# D6 R1c-A5+A6 合并任务 prompt（零 decoder，一次跑完两轨）

你负责一个可自主托管的 D6 R1c-A5+A6 合并任务。**唯一权威任务包**：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D6_R1C_A5A6_VALIDITY_REPAIR_AND_PERF_TASK_PACKET.md`

（单独的 `D6_R1C_A5_*` 与 `D6_R1C_A6_*` 两个文件已被本包整体吸收，仅作追溯，不要再按它们执行。）完整读完后按 §0→§7 连续完成。不要为普通代码判断、测试修复、结构分析、profiling、benchmark 或写文档询问主线程；仅在全部冻结项完成或出现会改变冻结科研契约的唯一 blocker 时返回。

当前事实：起始 HEAD 应为 `1a09220a`。R1c-A3 已被主线程采纳为“实现/结构阻塞的开发尝试”固化结果（stored `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` 保留但不得引用，184 次调用不得复用）；R1c-A4 已被采纳为 `READY`（仅结构路径，10897.7s→2.5s，n64 逐标量相等）；两者都不授权任何 run。

主线程只读结构审计（零 decoder，独立脚本在 `workspace/mainthread_a5_audit_7f3c1d9ab2e54a6f8c0d1e2f3a4b5c6d/`）已确认：冻结 eligibility 只检查**变量**度、从不检查**检查行**度；T3/T4 在 f1.2+square 出现度=1 行，M1 全宽度/层出现度=1 行，M2 在 L2 square 出现度=1 行；T2 在 n64 缺秩（63/62 vs 64）；B0/B1 在 n128 L2 base-pair 重复、n256 前缀不连通。A2 只暴露 T3/M1，是因为旧闸门选中的就是 {B0,B1,T1,T3,M1}。只补闸门会让 n64 只剩 {B0,B1,T1} 且无合格 M 臂→scaling 失去 M 腿，实验近乎空转，故路线为“有效性收口 + 可采纳修复 + R1d 就绪”。

第二轨（T2 加速）是 R1d 就绪的**前提**而非可选：T2 候选数 4.67M/76.7M/1.24B（n64/n128/n256），实测每候选 ~8.3–8.9µs，单层 ~41s/650s/2.85h；A5 修好 T2 后它很可能成为冻结 `best_T` fallback，scaling 会重新吃 2.85h/layer 并撞 chunk 5400s 熔断。等价许可证 = 键末字段（排序三元组）唯一标识候选 ⇒ 字典序 argmin 唯一且顺序无关，因此允许向量化与分阶段过滤，**禁止**改键/字段顺序/tie-break/候选集/贪心顺序、浮点近似整数键、未证明的 top-K 短名单。

绝对边界：零 decoder 调用（单元测试只能显式 fake）；不许 `--phase`、G1、G2、VAL、real/raw、新科学根；不许改 R1c-A2 六文件根与已提交 A2/A3 证据；不许改 D5/`v35`/`src`/`experiments`/`tools`；不许改冻结旋钮（arms/seeds/rows/prior/decoder/系数/SC 宽度/M 的 N2/选择与终局阈值/预算）；不许以 decoder 结果挑选修复或优化；本包不落地六文件 schema 变更；不 push、不自行接受结果、不请求 run 授权、不改授权键；工作树脏项（V35、perf-v38、CRLF churn 等）原样保留，严格逐路径 stage。

执行顺序（同一批文件，必须串行）：Track A 先（prereg → 独立矩阵 → 根因证明 → 落地 I1 闸门与执行期 crash 优先级 → 可采纳修复沙箱研究 → 结构成本投影 A5-10 → R1d 就绪包），Track B 后（A6 基线 profiling → 精确等价 T2 加速 → 七个等价门含沙箱 T2 门 → 性能验收 → 仓库级慢任务只读清单）。提交按 §6 七段，Track A 与 Track B 分提交、分评审；三个独立只读评审（A5 实现、A5 有效性/就绪、A6 性能），每个最多一轮 rework。修复不可行时给 `STRUCTURALLY_INFEASIBLE_AS_FROZEN` 证明 + 最小重定义菜单（`REQUIRES_MAIN_THREAD_RULING`，不得落地）。性能未达标按 `PERF_TARGET_NOT_MET` 返回并保留参考路径。

完成后按 §7 只回 delta，并原样结束：

`D6 R1c-A5/A6 合并任务已完成并独立复核：I1（检查行度≥2）缺陷已证明并被闸门封堵、修复候选与 R1d 就绪包待主线程裁决；T2 精确等价加速达成（或 PERF_TARGET_NOT_MET 并附热点证据），A4 收益未回退；全程零 decoder 调用，R1c-A2 根保持 immutable，授权全 false，G2 未授权、未执行。`
