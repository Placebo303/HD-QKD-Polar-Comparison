# Design: perf-v38-triage-test-cost

## Context

约束：最小改动、可回滚、不改语义、不加依赖（尤其不加 xdist/numba 依赖）。
顺序刻意为 T0 基线 → P1 → P0 → P2 → P3 → P4：先拿最小风险的加载缓存，再做计算缓存与向量化，最后做分级与短路（影响面渐大）。

## Decisions

### D1 — 先 P1（`load_v31` + session field），再 P0（source support/cycles）

- P1 是纯加载去重，键空间小、失效直观，先落地可立即放大后续步骤的计时收益归因。
- P0 的 support/cycles 缓存键含求解参数，参数口径需 Task 1 先冻结；排在 P1 之后避免键定义反复。
- 拒绝的替代：先做 P0——参数未冻结时键容易定错，回滚成本更高。

### D2 — P1 键必须含文件 stat，不用纯路径键

- 纯路径 `lru_cache` 在文件被覆写时会返回 stale 结果 → 错误的科学结论风险。
- 键 = `(resolved_abs_path, mtime_ns, size)`，有界 `maxsize`；另提供 `cache_clear` 钩子供测试隔离。
- session field 缓存键 = 数据集标识/表头指纹，作用域限 session，teardown 丢弃，不跨进程/跨会话持久化。

### D3 — P2 只做 numpy 向量化，numba 仅对照

- 本变更默认路径只允许 numpy 向量化；numba（如已存在或新建对照）不得成为默认、不加依赖声明。
- 正确性门：与现有循环逐位相等（值、dtype、tie 顺序、NaN/inf、空/单元素行为），见 spec R3。
- 拒绝的替代：直接上 numba——引入编译开销与新依赖，违反最小改动；向量化已能验证收益天花板。

### D4 — P3 fake 短路不伪造 `raw_errors`

- fake/test-only 调用必须显式走 fake runner 入参（默认生产解码器不可隐式进入 fake），短路点只跳过重计算。
- `raw_errors` 保留形状/类型契约，但内容标记为 fake 占位且状态保持非 `ok`（`stub`/`fake` 等原值），绝不生成看似真实的错误样本。语义表见 spec R4。
- 拒绝的替代：fake 返回空/None 省事——会破坏下游形状假设，排查成本更高。

### D5 — P4 分级：slow 标记 + fixture 合并 + T1 单 lane 双跑

- `slow` 划分标准：实测耗时超阈值或已知重型（real-data、长帧、sweep、重型编排），Task 1 用 `--durations=20` 冻结名单。
- 编排 fixture 合并：只合并同一作用域、同一输入的重复 setup；合并后 setup 次数下降可数，不改变 fixture 语义。
- T1 = 单进程单 lane 跑 ` -m "not slow"` 全集，在同一 job 内连续双跑（cold + warm），用于分离“缓存收益”与“flake”；不用 xdist；Full = CI 矩阵分片（`not slow` 片 + `slow` 片）。
- 拒绝的替代：加 xdist 并行——引入新依赖与调度不确定性，且与“可分片 CI 矩阵”目标重复。

### D6 — 计时与回归门：`--durations=20` + 三档对比

- 所有计时命令统一加 `--durations=20 -p no:cacheprovider`，归档 top-20 表。
- T0 门为阻塞式（< 60s）；T1/Full 门为记录 + 增量对比式（相对 baseline 的 top-1/总量回归阈值见 spec R6）。
- 测试根统一用可写目录、与生产输出根分离；计时不受 pytest 缓存目录权限噪声干扰。

## Risks

- 缓存 stale → 错误结论：由 D2 的 stat 键 + Task 级 tamper/隔离测试覆盖。
- 向量化 tie/edge 行为漂移：由 R3 逐位相等门覆盖，不相等即 revert P2。
- fake 污染生产语义：由“显式 fake 入参 + 状态不可升级为 ok”覆盖。
