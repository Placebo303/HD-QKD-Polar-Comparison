# D6 R1c-A3 post-run verifier rework prompt

你负责一个可自主托管的 D6 R1c-A3 后置取证任务。完整任务包：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D6_R1C_A3_POSTRUN_VERIFIER_REWORK_TASK_PACKET.md`

完整读完后按 §1→§11 连续完成。任务包含两个严格分离的轨道：先完成 A3 历史结果 verifier/终局收口，再完成 A4 structure/scaling 性能优化。不要为普通代码判断、测试修复、profiling、优化实现、分析细节或运行时间询问主线程；仅在全部完成或出现会改变冻结科研契约的唯一 blocker 时返回。

当前事实：R1c-A2 唯一授权已消耗，HEAD 应为 `047e6d62`，现有 immutable 根为
`workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b`。旧 verifier exit 1：semantic key 缺 `n`，scaling 聚合也缺 `n` 并混合 canary/scaling。另有 64 条 attempted crash/nonfinite，错误为 `ValueError('Check node requires degree >= 2')`，但存储终局却是 `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY`。你必须同时解决键、阶段重算和 crash/nonfinite 终局优先级，不能只让 verifier 变绿。

本任务绝对不授权任何 decoder：不许运行、重试、恢复、补 cell 或新建第二科学根；不许任何 `--phase`、正式 G1、G2、VAL、real/raw；不许修改现有六文件根；不许复用/读取 VOID；不许改 arms/rows/seeds/prior/decoder/thresholds/budgets。单元测试只能显式 fake。

先 OpenSpec/prereg，后独立取证重算，再最小代码+测试，再独立代码评审。评审 PASS 后，只允许对现有根调用一次纯只读 `--verify`。随后重新做真正独立 Pre-RESULT。若 degree failures 使科研终局无效，应明确给 `PASS_BLOCKED_RUN`，不得把它包装成 topology no-recovery；若仍 FAIL，停止且不修复不重跑。

只有 A3 Pre-RESULT PASS 后才可按包把历史根、原始 A2 FAIL、A3 修订和分析固化为本地提交。随后直接进入 A4，不用回来请示：先 structure-only profiling，再做 scaling 只构建 frozen fallback arms（不得在无资格时重建 T2）、把每 arm/layer 的三次 support/mother 构造降到最多两次且保持独立 replay、消除重复 prefix audit/diagnostic rebuild。要求 n128+n256 scaling structure wall 至少 3x 改善，n64 精确等价且回退不超过 10%。A4 可做最多 3 小时 structure-only benchmark，但 decoder calls 必须为 0。

A3 与 A4 必须分 OpenSpec、分提交、分评审；A4 新代码绝不能用于改写 A2 历史执行身份。若 3x 未达成，按 `PERF_TARGET_NOT_MET` 带 profile 返回，不许偷偷删科学工作。A4 完成也不授权新 D6 run。不得自行接受结果或启动下一算法路线，不 push。工作树里 V35、perf-v38、CRLF churn 和其它既有脏项全部原样保留，严格逐路径 stage。

完成后按任务包 §10 只回 delta，并原样结束：

`D6 R1c-A2 的历史执行未重跑；A3 已修复并独立复核后置 verifier/终局语义，现有根保持 immutable；结果仍待主线程裁决，G2 未授权、未执行。`
