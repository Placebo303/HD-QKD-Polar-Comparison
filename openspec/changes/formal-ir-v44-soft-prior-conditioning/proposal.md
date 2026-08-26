# OpenSpec Proposal: formal-ir-v44-soft-prior-conditioning

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（待本线程独立 plan ACCEPT 后进入 `PLAN_ACCEPTED / EXECUTE_NOT_AUTHORIZED`，当前仍为 `PLAN_CANDIDATE`，通过后进入 `DEVELOPMENT_RESULT_ACCEPTED` 需另行 result 接受）
**Domain**: Formal Information Reconciliation / Nonbinary LDPC research
**Change ID**: `formal-ir-v44-soft-prior-conditioning`
**Cycle ID**: `V44P0`
**Predecessor cycle**: `V43P0` (`formal-ir-v43-soft-marginal-diagnostic`)
**Predecessor terminal**: `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`（V43 已 durable：result SHA `4e2ed4db`，`V43P0` 18-call 配对诊断完成；V43 对 U1 软边缘化 `P(U2|Bob)` 的 insufficiency 已固化）
**Predecessor result SHA**: `4e2ed4db`
**Predecessor accepted plan SHA**: 绑定于 V43 冻结证据（本变更 A12 复核时绑定）
**Branch / HEAD**: `Placebo303/HD-QKD-Polar-pipeline` `formal-ir-mainline`，HEAD `4e2ed4db` 前

## Why

V43 以 `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK` 固化：Lane C 在相同门禁下 `cond_soft_marginal`（对 U1 求和得 `P(U2|Bob)`）不保留信号，soft marginalization 不足。二、三阶段调查已验证：

- **无现成 L1 soft decoder 可复用**（现有实现均硬判或 oracle，无可直接复用的软先验译码路径）；
- **唯一零泄漏公开输入**为 `q_i(u1)= Σ_{u2=0..31} counts[u1·32+u2, b] / Σ_{u1',u2'} counts[u1'·32+u2', b] = P(U1|B=b)`，纯 `(counts_true, bob)` 来源，已做 spike 验证：归一（每 `b` 和=1）、退化（均匀/尖峰边界）、稳定性（floor 1e-15 防零）；
- **禁止** Alice 真值（`u1_alice/u2_alice` 仅用于 syndrome 与 `exact` 判定，不入先验）、事后权重（post-hoc reweight）、C04 类调参。

V44 在**机制来源明确且无 oracle 泄漏**的前提下创建，回答下一个最小归因问题：

**将 hard/边缘化路径替换为无码 soft prior `q_i(u1)`（Bob-only soft，仅 `counts+bob`），Lane C 同图同参下是否在冻结门禁内保留信号？区分 conditioning failure（oracle-only）与 structure failure（both fail），不并行测试多种 joint/soft 方案。**

单一机制、最小 fresh-block workload、严格隔离与可复现会计。

## Scope

本规划轮仅冻结 V44P0 soft-prior conditioning 诊断协议：

1. **单一机制（零泄漏）**：`cond_soft_prior` 冻结为无码 soft prior `q_i(u1)= Σ_{u2} counts[u1·32+u2,b] / Σ_{u1',u2'} counts[u1'·32+u2',b]`，纯 `counts_true + bob` 构造，每位置 `b` 独立归一（和=1，floor 1e-15），通信/leakage 0 extra（`counts` 为已公开的公共先验，不计入本轮泄漏），不并行测试多种 joint/soft 方案，不引入新矩阵/joint 迭代/decoder 新参/pilot/噪声/量化/失配信道律/C04 调参。
2. **最小 fresh-block workload（恰好 18 calls）**：每源 3 个从未使用的 TRAIN 新块（1M=390116/390117/390118，1p5M=390216/390217/390218，2M=390316/390317/390318），每块确定性采样一次并被两臂共享；每对用该源 Lane C ordinal-2 代表矩阵、单一冻结设置 `max_iter=90, damping_alpha=1.0`、GF(32) poly 37、syndrome 来自真 `u2_alice`、成功=`exact_l2`；唯一两臂 `cond_oracle` vs `cond_soft_prior`；三矩阵复用 `lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302`。
3. **FORBIDDEN 零重叠 60**：V36_A3(15) ∪ V39(15) ∪ V40 probe(3) ∪ V41 confirm(9) ∪ V42 diagnostic(9) ∪ V43 diagnostic(9) = **60 seeds** 已占用；九枚新区 `x16-x18/源` 连续递增，无内部重复，与全部六族零重叠（P3/J2 机械复验）。
4. **每条件独立门禁**：`G1' ≥7/9`、`G2' 每源 ≥2/3`、`G3' 该臂 wrong_codewords==0`（`wrong = syndrome_ok && !exact_l2`，永不计为 exact）。
5. **总量互斥五终态机 + orthogonal 标志**：`V44_EVIDENCE_INVALID` 优先；其余四态 `V44_BOTH_PASS / V44_ORACLE_ONLY_SOFT_BOTTLENECK / V44_GO_STRUCTURE / V44_ANOMALOUS_INVERSION` 穷尽互斥覆盖 `(oracle_pass, soft_prior_pass)` 平面；`needs_1p5m_structure_branch` 当且仅当 `oracle exact on 1p5M < 2/3` 时立旗，独立于终态。
6. 预算记账（planned/completed/started actuals）、科学 preflight 优先失效（零 call 停止）、硬上限 18 且结构性拒绝第 19 call、增量证据输出、`errors_initial` 严格 per-pair 跨臂等值门（J6）、Master Stop Rule、no-rerun/no-post-hoc-tuning 边界。

本轮不执行。实现须先获独立 plan ACCEPT；任何实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；诊断执行需显式用户 `EXECUTE_AUTH` 绑定到精确实现 SHA，scope `v44_diagnostic_18_calls_exactly_once`。

## Non-goals

- 非参数搜索、非调参：单点 90/1.0，无迭代/damping 网格、warm start、第二设置，不改冻结的 `cond_soft_prior` 定义，不做 C04 类调参。
- 不并行测试多种 joint/soft 方案；不跑 baseline、Phase B、Lane B，不增矩阵（仅三枚 lane_c ordinal-2）。
- 不复用任何历史块作诊断样本；不追加 blocks、补跑、rerun/resume、结果后改阈值/改机制/加 seeds/加权重；无论结果如何不做第二轮诊断。
- 终态不作优劣/资格/晋升/FER/渐近阈值/SKR/安全/真帧陈述，不自动启动后继；后继方向仅描述性。
- 不改 constructor/loader/evaluator/decoder，不改 v35/v38，不 import v39/v40/v41/v42/v43 模块；`counts` 为公共先验不计泄漏，不引入额外通信。

## Affected specs

新增 delta spec：`specs/formal-ir-v44-soft-prior-conditioning/spec.md`。
不修改任何既有 spec、代码、测试、输出、memory 文件。

## Lifecycle

V43 predecessor lifecycle=`DEVELOPMENT_RESULT_ACCEPTED`（terminal `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`，result SHA `4e2ed4db`）。V44 当前为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；独立计划接受后进入 `PLAN_ACCEPTED / EXECUTE_NOT_AUTHORIZED`，`development_execution_authorized`、`formal_execution_authorized`、`scientific_promotion`、`implementation_started`、`production_outputs_created` 均为 false。需独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定到精确实现 SHA，scope `v44_diagnostic_18_calls_exactly_once`）方可进入实现/执行；V44 不追溯改写历史结论。
