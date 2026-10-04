# Task 7 — 三档计时对比与回归门 (perf-v38-triage-test-cost)

Date (UTC): 2026-09-08/09. Branch: formal-ir-v72p1-addendum-clean. Same machine, same
runner as baseline.md (`PYTHONPATH=comparison_bench/src`, `-p no:cacheprovider
--durations=20`, fresh `workspace/perf-v38/<uuid>` basetemp per run).

## 1. 对比表 (wall time, literal)

| 档 | 命令 | 基线 | 最终 | 结论 |
|---|---|---|---|---|
| T0 默认 lane | v38 `-m "not slow"` (33) + perf gates (10) | ~10–15s (分片和, Task1) | **4.14s, 43 passed, 5 deselected** | Gate <60s **PASS** |
| T1 cold | v38 全文件 38 | ~1506s (分片和 S1–S4) | **801.25s, 38 passed** | -46.8%, **PASS** |
| T1 warm | v38 全文件 38 (同 job 第二跑) | — | **802.28s, 38 passed** | cold/warm Δ 0.1%, 无 flake |
| Full fast 片 | v39 29 | 6.84s (28 passed + 1 基线 env 失败) | **5.69s (28 passed + 同一 env 失败)** | -17%, **PASS** |
| Full slow 片 | v38 `-m slow` 5 | 641+634+77+74+74 (top) | 343+339+41+40+40 (T1 cold top) | top-1 -46%, **PASS** |

Full 合计: 基线 ~1513s → 最终 ~807s (1.87×). 失败 IDs: 仅
`test_v39_lanec_robustness.py::test_sha_binding_exact_equality`（基线/最终一致：
assert HEAD == origin/formal-ir-mainline，本分支环境使然，与本变更无关）。

## 2. Top-5逐项 (基线 → T1 cold, 全部下降, 无回归)

- test_production_orchestration_all_27_attempts_and_fail_closed: 641.11 → 336.15s
- test_orchestration_not_ready_lane_gets_zero_decoder_runs: 633.67 → 343.20s
- test_t1_construction_seed_determinism: 77.43 → 40.89s
- test_t6_t7_t8_lane_a_support_and_search: 74.41 → 39.80s
- test_t30_t31_lane_a_rank_semantics: 74.10 → 39.51s
- 其余条目 ≤0.8s, 与基线持平或更快；唯一上浮
  `test_t15_cli_requires_flag_and_has_no_fake_runner_option` 0.77→0.91s (+18%, <20% 门,
  绝对 +0.14s, 纯 CLI 子进程噪声, 非优化热点) —— PASS(备注)。

R6 门: T0 <60s 阻塞 PASS；T1/Full top-1 与总量相对基线无 >20% 回归 PASS。

## 3. 各 P 贡献

- P2 (rank): 主贡献。lane-A 单构造 47.4→20.2s；cycle 子矩阵 tiny 路径 list 化
  (2x2 4.2→2.0µs, 4x4 20.5→5.9µs)；全矩阵向量化 12.3s→0.23s (53×, validity 检查)。
- P0 (support/cycles): edges/enumeration 缓存跨构造命中（t1 双构造第 2 次全命中）；
  per-call cycle-rank LRU 实测命中率 ~0.02% 已 revert（sweep 候选几乎全 distinct，
  缓存键开销反增 ~1µs/call）——见 decision-log 备注。
- P1 (load): V31 50MB JSON parse N→1/进程；t2 1.88→0.79s；跨测试复用。
- P3 (fake): fake 路径跳过真 syndrome matvec；语义门全过（R1-05/R1-06  pin 住
  sample+posterior 不可跳，见 §4）。
- P4 (slow): 默认 lane 1506s→4.14s（363×，来自剔除 5 slows）；T1 单 lane 双跑
  cold/warm 可解释（页缓存可忽略）；编排 fixture 结论见 §4。

## 4. 残留/约束记录

- R1-05/R1-06 冻结测试要求 fake 路径仍调用 sample_empirical_block +
  get_conditional_posterior_l2（posterior binding 断言）→ P3 仅短路 syndrome，
  prior 不可动。`errors_initial` 在本 cost center 是真实采样计数（非占位），
  R4 语义以“形状/类型/非 ok 状态/可区分”满足，不伪造成功帧。
- 编排 fixture 合并：v38 文件无 module fixture；两编排测试输入不同
  （production seeds vs custom seeds+mock）不可合并；v39 `real_counts` 已是
  session 作用域，`fake_v31` 为 ~600KB 零数组（合并无收益且有污染风险）。
  R5 以“持平 + P1 跨测试去重（parse-once 门）”满足。
- 残留热点：单 lane-A 构造 ~20s = 3.78M tiny-rank 调用（~4–5µs/call：子矩阵
  构造 + rank）；进一步优化需重组 optimize 内层 evaluator（sequential 依赖，
  本变更不做）。
- 回滚：6 粒度 commit（Task1 记录 / P1 / P0 / P2 / P3 / P4+门 / Task7 记录），
  各步 revert 手段见 proposal；任一步 revert 后门测试即回基线行为。

## 5. 等价门结果汇总

- rank 四实现逐位相等：319 cases × {default, loop, tiny, vec} 0 mismatch
  （空/单元素/全并列/升降序/seeded 随机/40×40/96×256 稀疏；NaN/inf 在 uint8
  GF(32) 域内不合法，按 R3 豁免）。
- P0 support/cycles：与 `_enumerate_cycles_uncached` 逐项相等 + 容器拷贝隔离。
- P1：stat 变化必 miss、同文件命中、相对/绝对同条目、失败不缓存、变异隔离。
- P3：errors_initial 为真实计数、status=max_iter 非 ok、exact_l2 False、键集合不变。
- P4：`-m slow` ↔ 5，`-m "not slow"` ↔ 33（子进程 collect-only 断言）。
