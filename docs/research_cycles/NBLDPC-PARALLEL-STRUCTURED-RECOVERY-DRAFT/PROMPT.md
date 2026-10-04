# 配套 prompt：NB-LDPC 平行结构化恢复路线草案

日期：2026-09-29；快照 UUID：`11560eec-3b05-4c21-a309-30a45c2fdc18`。

权威入口：[PROPOSAL.md](PROPOSAL.md)。Track: **DECIDE（路线提案）**。

状态：**DRAFT / NOT GRANTED / NO EXECUTION**。本 prompt 只委派文档细化与只读核验，不能作为构造、测试 decoder 或真实数据访问授权；不得从用户“平行推进”推导出冻结批次执行许可。

## 可复制 prompt

> 仓库：HD-QKD_Polar_Comparison；分支在开始时只读核对，预期 formal-ir-v72p1-addendum-clean。本轮禁止 commit/push、git add -A 和跨线 merge。当前脏树有并发工作，保留所有无关修改。
>
> 当前 change：NBLDPC-PARALLEL-STRUCTURED-RECOVERY-DRAFT；尚无已接受的实现 OpenSpec。入口 docs/research_cycles/NBLDPC-PARALLEL-STRUCTURED-RECOVERY-DRAFT/PROPOSAL.md；状态 DECIDE_ROUTE_PROPOSAL / DRAFT / NOT GRANTED。本轮任务是完善拟案，不是运行实验。
>
> 阅读本库 AGENTS.md、AGENT_PROJECT_MEMORY.md 最新有关条目和入口文件。按 Ponytail lite 执行。主线程持有科学路线、阈值、OpenSpec 和最终验收；你只完成被冻结的文档细化。你不是唯一工作者，不改其他人的文件，不写个人长期记忆。
>
> 目标：保留 NB-LDPC 与 NB-Polar 平行推进，忠实引用 A1 的有限条件 NB 对二元优势，提出一个可检验的新结构机制以改善完整 U1+U2 恢复。不要重新提出已测软边缘化、200+8 嵌套图或 P1 冷救援作为新方法。
>
> 允许动作：只读现有代码、冻结包、小型已公开结果摘要；在本目录这两份文档内提出可审阅修订。修改前先读原文。不得读取原始/受保护数据、旧结果大型数组、.ttbin，不能执行测试、构造器、decoder、DE、随机扫描或 benchmark；不得改源代码、旧包、NOW、decision-log、AGENTS、memory。
>
> 具体输出：核实候选相对 D10–D13、L1B、Stage-0、Joint Pricing 的准确新 delta；给出与已有 forward/decoder 相容的接口和复用清单；列出一个匹配对照、完整恢复/公开量定义、最小多图多种子设计及停止规则。不能在草案阶段生成 protograph 矩阵、图文件或可执行命令。若候选必须同时改度分布、预算、prior 或双向调度，则返回主线程说明唯一所需决定，不能自行扩大方案。
>
> 严格保留边界：Joint MARGINAL 双数同引且其禁设计终态不解除；B/C 旧闭环不重开；P3/P4/D7-H 单独门控。路线裁决也不自动解除 P4；任何 R1/R2 构图之前，须明确 P4 对新候选的适用范围并有覆盖具体范围的新授权。三禁令和 §11 天花板不变。HDC/LB void 不作基线。历史合成局部成功不升格真实完整恢复。未来纯合成 EXPLORE 与真实 DECIDE 分包，不给多阶段一揽子执行授权。
>
> 返回 D-01…D-10 的完成情况、确切改动/建议、证据路径及 UUID、仍待用户裁决的最少事项。无能力填定的科学输入明确标 NOT FROZEN。不要把预算建议说成实测耗时，不给成功概率，不把文档审查写成算法接受。
>
> STOP：发现新路线落在旧禁设计范围而没有明确解禁；需要保护数据、运行程序或修改源代码才能继续；存在科学定义歧义；发生目标文件并发冲突。此时返回具体阻塞与所需的单一主线程决定，保留已读事实。

## 后续执行授权不在本文件内

未来如用户接受新路线，主线程先建立 OpenSpec 和对应单一 track 的执行包，填齐科学参数、命令、种子、资源、输出不存在检查和独立审查安排，再请求该包的显式授权。本文件不提供可复制的实验授权句，避免把未冻结合同当成可执行批次。
