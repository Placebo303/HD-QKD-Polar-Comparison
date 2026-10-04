# Proposal: perf-v38-triage-test-cost

## Goal

把测试成本降到可日常迭代的水平：**本地 T0 < 60s**，全套测试在 CI 可分片执行（矩阵分片，不引入新并行框架）。
用最小、可回滚的缓存 + 向量化 + 分级执行手段消除重复 I/O 与重复计算，不触碰任何算法结论。

## Non-Goals（明确不做）

- 不改算法语义：解码/协调逻辑、support 求解语义、label 分布、泄漏量分解口径一律不变。
- 不加 `pytest-xdist`（或任何新的并行/重试/缓存依赖）；P2 先做 numpy 向量化，不加 numba 依赖。
- 不做跨会话持久化缓存、不做 output/results 回写优化、不碰 `src/`、`experiments/`、`tools/` 冻结基线。
- 不把 `stub` / `fake` / `unavailable` / `decode_failed` 结果伪装成 `ok`。

## Background

测试耗时主要来自三类可消除浪费（待 Task 1 用 `--durations=20` 实测确认量级，不猜数字）：

1. 重复加载：同一 V31/数据源文件被多个用例反复解析（P1）。
2. 重复计算：同一 source 的 support/cycles 结构被反复求解（P0）；rank 逐元素 Python 循环（P2）。
3. 分级缺失：慢用例混在默认 lane 里，本地一次全跑太贵；编排 fixture 重复 setup；fake 路径仍走重计算（P3/P4）。

## Scope（P0–P4，全改不分批、按序落地）

- **P0 — source 缓存（support + cycles）**：同一 source + 同一参数的 support/cycles 结果复用，键/失效见 spec。
- **P1 — `lru_cache(load_v31)` + session field**：`load_v31` 加有界 `lru_cache`（键含文件 stat，防 stale）；会话级 fixture 缓存已解析的 field 映射，session 结束即弃。
- **P2 — rank 向量化（numba 延后）**：本变更只落地 numpy 向量化路径；numba 实现（如有）仅作对照分支、不默认启用、不加依赖。向量化输出必须与现有逐位循环逐位相等。
- **P3 — fake 短路（保留 `raw_errors` 语义）**：fake/test-only 路径短路重计算，但 `raw_errors` 的形状/契约/可区分性不变，语义表见 spec。
- **P4 — slow 标记 + 编排 fixture 合并 + T1 单 lane 双跑**：`slow` 标记划分三档；合并编排层重复 fixture；T1 保持单进程单 lane（不用 xdist），在同一 job 内双跑一次（cold + warm / repeat）以区分缓存收益与 flake。

## Impact Scope

- **可能影响**：`comparison_bench/` 下的测试分级与 fixture、V31/source 加载路径、rank 计算函数、fake runner 短路点、`pyproject`/`pytest.ini`/`conftest.py` 的 mark 注册、CI workflow 的分片矩阵。确切符号与文件在 Task 1 确认（首任务即冻结清单）。
- **明确不碰**：`src/`、`experiments/`、`tools/`（冻结基线）、`results/` 与 `comparison_bench/outputs_comparison/` 生产输出、算法语义与状态值口径、任何新依赖。

## Acceptance Criteria

1. 本地 `T0`（默认 lane） wall time < 60s（`pytest -p no:cacheprovider --durations=20` 实测，记录 top-20）。
2. CI 全套可分片：`not slow` lane 与 `slow` lane 可在矩阵中独立运行、各自通过，不过度依赖执行顺序；不引入 xdist。
3. 缓存正确性：P0/P1 键/失效按 spec 实现；stat 变化必 miss；测试间无跨污染（session 结束即弃，除非 spec 明确允许 warm 复用）。
4. rank 逐位相等门：向量化 vs 现有循环在随机 + 边界用例上逐元素完全相等（含 dtype/tie/NaN-inf 处理）。
5. fake 语义门：`raw_errors` 契约与状态可区分性按语义表保持，无伪造成功。
6. 每个 P 按序独立可回滚：revert 单步即回 baseline，后续步骤不隐式依赖它。

## Rollback Strategy

- 每个 Task 独立 commit；任一步回归即 revert 该步，不动其他步。
- 缓存类步骤回滚手段为删除装饰器/恢复直调 + `cache_clear`，行为回到直算；rank 回滚为恢复循环实现；fake 回滚为恢复原调用链；P4 回滚为取消 mark/恢复原 fixture（mark 本身对未标记用例无影响）。
