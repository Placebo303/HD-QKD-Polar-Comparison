# Spec delta: perf-v38-triage-test-cost

## R1 — P1 `load_v31` 缓存键与失效（MUST）

- SHALL 以 `(resolved_abs_path, mtime_ns, size)` 为缓存键；相对/绝对/符号链接指向同一文件 SHALL 命中同一条目。
- SHALL 有界（`maxsize` 为有限常量并在代码处注明）；SHALL 提供测试隔离路径（`cache_clear` 或等效 fixture）。
- 同一路径文件内容变化（mtime_ns/size 任一变化）SHALL miss 并重载；不同文件 SHALL 互不污染。
- SHALL NOT 跨进程/跨会话持久化；SHALL NOT 把加载失败缓存为成功。

## R2 — P0 source 缓存键与失效 + session field（MUST）

- source support/cycles 缓存键 SHALL 包含 `(source_id, support_params, cycles_params, source_stat)`；任一分量变化 SHALL miss。
- 求解参数口径 SHALL 与现有直算路径同一来源（不另起一套默认值）；缓存命中结果 SHALL 与直算数值逐位一致。
- session field 缓存 SHALL 以 `(dataset_id_or_path, header_fingerprint)` 为键，作用域限 pytest session，session 结束 SHALL 丢弃；不同数据集 SHALL 互不污染。
- SHALL NOT 改变 support 求解语义、cycles 语义与 label 分布。

## R3 — rank 逐位相等门（MUST）

- 向量化 rank 输出 SHALL 与现有循环实现逐元素完全相等：值相等、dtype 一致、并列（tie）顺序一致、空/单元素/降序行为一致、NaN/inf 处理一致。
- 验证集 SHALL 至少覆盖：空、单元素、全并列、升/降序、随机（含种子复现）、NaN/inf（如域内合法）。
- numba 路径 SHALL NOT 成为默认；引入 numba 依赖 SHALL 视为本变更之外的独立变更。
- 任一反例 SHALL 阻塞 P2 落地并 revert。

## R4 — fake 短路语义表（MUST）

| 输入条件 | 短路行为 | `raw_errors` | status |
|---|---|---|---|
| test-only 显式 fake 调用 | 跳过重计算，走 fake runner | 保留形状/类型契约，内容为明确标记的 fake 占位，不伪造真实错误样本 | 保持非 `ok`（原 `stub`/`fake`/`unavailable` 等，不升级） |
| 生产/默认解码调用 | SHALL NOT 进入 fake | 与现状一致 | 与现状一致 |
| fake 下游聚合 | 按占位可区分处理 | SHALL 可区分 fake vs 真实（标记存在） | SHALL NOT 计入成功/FER 分子 |

- SHALL NOT 把 `decode_failed` / `no_verified_success` / `stub` 静默转为 `ok`；SHALL NOT 缩减 `raw_errors` 维度以“省时间”。

## R5 — slow 划分与分片（MUST）

- `slow` SHALL 注册为 pytest mark；划分 SHALL 基于 Task 1 冻结的 `--durations=20` 名单（阈值与名单同归档）。
- 默认 lane SHALL 为 `-m "not slow"`；T1 SHALL 为单进程单 lane、无 xdist，并在同一 job 内双跑（cold + warm各一次）。
- CI 全套 SHALL 可表达为 `not slow` 片 + `slow` 片的矩阵分片；任一片 SHALL 可独立运行。
- 编排 fixture 合并 SHALL 仅合并同作用域同输入的重复 setup；合并前后 fixture 语义 SHALL 不变，setup 次数 SHALL 可数下降或持平。

## R6 — `--durations=20` 回归门（MUST）

- 全部计时命令 SHALL 使用 `pytest -p no:cacheprovider --durations=20` 并归档 top-20 表。
- T0（默认 lane）wall time SHALL < 60s，否则阻塞。
- T1/Full SHALL 与 Task 1 基线对比：若 top-1 条目耗时或 lane 总量回归超 20%（或任一已优化热点反弹超 20%）SHALL 视为回归并 revert 对应步骤；对比表 SHALL 随结果归档。
- 三档（T0 / T1 cold+warm / Full 分片定义+抽样）SHALL 在同一机器/同一提交下复算，对比结论 SHALL 可复现。
