# Tasks: perf-v38-triage-test-cost

顺序固定：T0 基线 → P1 → P0 → P2 → P3 → P4 → 三档对比。每步独立 commit、独立可回滚；后一步不得静默依赖前一步（回滚前一步后后续步骤要么仍通过、要么明确声明阻塞并同 revert）。

## Task 1 — T0 拆分验证与基线冻结（/opsx-explore 若符号不明）

- [ ] 确认并冻结：`load_v31`、`source support/cycles` 求解函数、`rank` 函数、fake runner 入口、编排 fixture 的确切文件/符号；输出清单（文件:行号）。
- [ ] 确认并冻结：T0/T1/slow 三档当前用例划分与 `slow` 候选名单；注册 `slow` mark（如缺）。
- [ ] 基线计时（不改代码）：`pytest -p no:cacheprovider --durations=20` 跑 T0/T1（Full slow lane 只取 top-20 样本，不做全量昂贵执行），归档三份 top-20 表 + wall time。
- 验证：清单完整、基线表已归档、T0 现状耗时已知。
- 回滚：纯文档/记录，无代码回滚。

## Task 2 — P1：`lru_cache(load_v31)` + session field

- [ ] `load_v31` 加有界 `lru_cache`，键含 `(resolved_abs_path, mtime_ns, size)`；提供测试隔离用的 `cache_clear` 路径。
- [ ] 会话级 fixture 缓存 field 映射（键 = 数据集标识/表头指纹），session teardown 丢弃。
- [ ] 测试：stat 变化必 miss、同文件复用命中、跨测试无污染、路径归一化（相对/绝对同文件命中同一条目）。
- 验证：T0 复跑 `--durations=20`，`load_v31` 相关条目下降且总数 < 基线；正确性测试全过。
- 回滚：删除装饰器/恢复直调 + 移除 session 缓存即回基线。

## Task 3 — P0：source 缓存（support + cycles）

- [ ] 以 Task 1 冻结的参数口径定义缓存键 `(source_id, support_params, cycles_params, source_stat)`；同键复用，不同参数/文件变化必 miss；有界容量。
- [ ] 测试：同参命中、改参 miss、文件变化 miss、无跨参污染；support/cycles 数值与直算逐位一致。
- 验证：T0/T1 复跑计时对比，support/cycles 热点下降；语义测试全过。
- 回滚：恢复直算调用即回基线（可保留 P1）。

## Task 4 — P2：rank 向量化（numba 不落地）

- [ ] numpy 向量化重写 rank 默认路径；保留原循环作对照（测试内或显式对照函数，不进默认路径）。
- [ ] 测试：随机 + 边界（空、单元素、并列、降序、NaN/inf、dtype）逐元素完全相等门；`--durations=20` 显示 rank 热点下降。
- [ ] numba（如有）仅放对照分支/文档提及，不默认启用、不加依赖。
- 验证：相等门全过 + 计时收益记录；任一不等即 revert 本步。
- 回滚：恢复循环实现即回基线（保留 P0/P1）。

## Task 5 — P3：fake 短路（保留 `raw_errors` 语义）

- [ ] test-only/fake 调用显式传 fake runner（生产默认路径不可隐式进 fake）；短路重计算但保留 `raw_errors` 形状/契约，状态保持非 `ok`（语义表见 spec R4）。
- [ ] 测试：fake vs 实路径的 `raw_errors` 形状/类型一致、可区分性（fake 标记存在）、状态值未升级、无伪造成功帧。
- 验证：T0/T1 计时中 fake 相关条目下降；语义测试全过。
- 回滚：恢复原调用链即回基线。

## Task 6 — P4：slow 标记 + 编排 fixture 合并 + T1 单 lane 双跑

- [ ] 按 Task 1 名单打 `@pytest.mark.slow` 并注册 mark；默认 lane = `-m "not slow"`；CI 矩阵 = `not slow` 片 + `slow` 片（无 xdist）。
- [ ] 合并编排层重复 fixture（同作用域同输入），记录 setup 次数变化；不改 fixture 语义。
- [ ] T1 单 lane 双跑：同一 job 内 `not slow` 集连续跑两次（cold + warm），分别记录 `--durations=20`。
- 验证：`pytest -m "not slow"` 本地通过；双跑 cold/warm 差值可解释；CI 分片定义可静态检查（workflow 可解析）。
- 回滚：去 mark/恢复原 fixture/取消双跑即回基线（mark 缺席时默认全跑行为不变）。

## Task 7 — 三档计时对比与回归门

- [ ] 同机复跑三档：T0（默认 lane）、T1 单 lane 双跑（cold/warm）、Full 分片定义（slow 片可只跑 top-20 样本 + 静态分片检查，避免昂贵全量），全部 `--durations=20 -p no:cacheprovider`。
- [ ] 输出对比表：baseline vs 最终的每档 wall time + top-20 delta；T0 < 60s 阻塞门，T1/Full 按 spec R6 阈值判回归。
- [ ] 归档计时表与结论（哪个 P 贡献最大、是否达标、残留热点）。
- 验证：门全部通过或残留项有明确 decision-log 记录；任一回滚不破坏本表可复算。
- 回滚：纯记录，无代码回滚。
