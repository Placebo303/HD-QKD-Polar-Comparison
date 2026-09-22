# D6 R1c-A6 结构路径性能 prompt（零 decoder，A5 之后执行）

你负责一个可自主托管的 D6 R1c-A6 性能任务。完整任务包：

`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D6_R1C_A6_STRUCTURE_PERF_T2_ACCELERATION_TASK_PACKET.md`

完整读完后按 §0→§7 连续完成。不要为普通代码判断、测试修复、profiling、benchmark 或写文档询问主线程；仅在全部冻结项完成或出现会改变冻结科研契约的唯一 blocker 时返回。

背景（已量化）：A4 已把 scaling 结构 10897.7s→2.5s、n64 42.2s→21.0s（arm 剪枝 + 两次构造 replay + overflow 透传）。**唯一剩下的慢 arm 是 T2_CYCLE_GREEDY**：候选数 `|B|(|B|-1)/2*(|C|-2)` = n64 4.67M / n128 76.7M / n256 1.24B，实测每候选 ~8.3–8.9µs，单层 wall ≈41s / 650s / 2.85h（正是当初卡住 n=256 的那一段）。T1_PEG 的 BFS 已不再重要（非 T2 臂在 n256 合计仅 1.5s）。风险点：A5 若把 T2 修好，T2 很可能成为冻结 `best_T` fallback，scaling 段会重新吃到 2.85h/layer，直接撞 chunk 5400s 熔断——所以本任务既是加速也是 R1d 就绪前提。

**先决条件**：A5 的 closeout 提交必须已存在（两者改同一批文件）。若不存在，只做 §5 只读清单后返回。

等价性原理（本任务的许可证）：候选集由 `used_pairs/used_triples` 固定，键的最后一个字段是排序三元组且唯一标识候选，因此字典序 argmin 唯一且与枚举顺序无关。允许向量化与分阶段过滤；**禁止**改键、改字段顺序、改 tie-break、改候选集、改贪心顺序、用浮点近似整数键、用未证明等价的 top-K 短名单。生产输出（support/H/structure_records.csv/selected_arms.json/eligibility/结构排序）必须逐位不变。

硬指标：T2 单层 n64≤5s、n128≤90s、n256≤600s（总体≥10×）；n64 全 8 臂≤8s；非 T2 臂回退≤10%；scaling fb-only 不超过 A4 after-side 的 2×；RSS<2GiB；零 decoder 调用；无重试框架。未达标按 `PERF_TARGET_NOT_MET` 返回并保留参考路径。

等价门必须全过：8 臂×2 层×{64,128,256} support 数组相等（n256 T2 参考可跑一次，计入 4h 结构only 预算）；T2 每变量选择轨迹相等；已提交的 A2 n64 证据逐字节不变；结构排序/eligibility/selected_arms 不变；determinism replay 与并行/串行相等；A4 剪枝与“每 (n,arm,layer) 至多两次构造”不回退。

§5 只读清单（不实现）：v38 三档与残留热点（lane-A ~20s = ~3.78M tiny rank 调用；perf-v38 已把全文件 1513s→807s）、两个编排测试（~340s each）、D5/D6 结构助手（`audit_prefix` GF32 rank、`compute_girth`、`_build_M_support` 全对枚举、`build_dv3_nested_support`）、V30R 式 DE/decoder 阶段（74.8s/719.9s）等；给测量值 + 热点符号 + 预期收益 + 语义风险 + 是否需 OpenSpec 的优先级菜单。

不许 push、不许自行接受结果、不许请求 run 授权、不许改授权键；R1c-A2 根与已提交证据 immutable；工作树脏项原样保留，严格逐路径 stage。

完成后按 §7 只回 delta，并原样结束：

`D6 R1c-A6 结构路径性能收口完成并独立复核：T2 精确等价加速达成（或 PERF_TARGET_NOT_MET 并附热点证据），A4 收益未回退，全程零 decoder 调用，未授权任何 run，不 push。`
