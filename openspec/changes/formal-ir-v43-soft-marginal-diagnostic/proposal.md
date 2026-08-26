# OpenSpec Proposal: formal-ir-v43-soft-marginal-diagnostic

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（待本线程接受结果后进入 `DEVELOPMENT_RESULT_ACCEPTED`，当前仍为 `PLAN_CANDIDATE`，接受后改为 `DEVELOPMENT_RESULT_ACCEPTED`）
**Domain**: Formal Information Reconciliation / Nonbinary LDPC research
**Change ID**: `formal-ir-v43-soft-marginal-diagnostic`
**Cycle ID**: `V43P0`
**Predecessor cycle**: `V42P0` (`formal-ir-v42-conditional-realism-diagnostic`)
**Predecessor terminal**: `V42_GO_STRUCTURE / BOTH_ARMS_GATES_FAILED`（V42 已 durable：accepted plan SHA 53fb371655c5d8c644395ef07dcd9e0a24ec804f，implementation/execution SHA f2ea4fa2c97f6c2ffe5fe6c27f0d84c8f7874e9b，result SHA 1920939200f02be91a8c4849a711ffa7857c5f8f）
**Predecessor implementation/execution SHA**: `f2ea4fa2c97f6c2ffe5fe6c27f0d84c8f7874e9b`
**Predecessor accepted plan SHA**: `53fb371655c5d8c644395ef07dcd9e0a24ec804f`
**Predecessor result SHA**: `1920939200f02be91a8c4849a711ffa7857c5f8f`

## Why

V42 已以 terminal `V42_GO_STRUCTURE / BOTH_ARMS_GATES_FAILED` 固化（accepted plan SHA 53fb371655c5d8c644395ef07dcd9e0a24ec804f，implementation/execution SHA f2ea4fa2c97f6c2ffe5fe6c27f0d84c8f7874e9b，result SHA 1920939200f02be91a8c4849a711ffa7857c5f8f），冻结了 `cond_estimated_l1`（hard MAP `u1_hat`）对 Lane C 的条件真实性诊断。V43 在**完全冻结 Lane C 图结构与译码设置**的前提下，用最小增量回答下一个归因问题：

**Lane C 的损失是否来自 hard decision 本身？若去掉 `u1_hat` 硬判、改为对 U1 不确定性做软边缘化 `P(U2|Bob)=Σ_u1 P(U1=u1,U2|Bob)`，是否在相同门禁下保留信号？**

两臂配对、9 个 fresh blocks 各解一次、共 18 calls 恰好一次，不引入新矩阵/joint 迭代/decoder 参数，不引入 pilot/噪声/量化/失配信道律。

## Scope

本规划轮仅冻结 V43P0 软边缘诊断协议：

1. **配对诊断（恰好 18 calls）**：每源 3 个从未使用的 TRAIN 新块（1M=390113/390114/390115，1p5M=390213/390214/390215，2M=390313/390314/390315），每块确定性采样一次并被两臂共享；每对用该源 lane_c ordinal-2 代表矩阵、单一冻结设置 `max_iter=90, damping_alpha=1.0`、GF(32) poly 37、syndrome 来自真 `u2_alice`、成功=`exact_l2`。无 baseline、无额外矩阵、无 Lane B。
2. **两条件/块**：`cond_oracle` = `get_conditional_posterior_l2(counts_true, bob, u1_true)`（能力上界）；`cond_soft_marginal` = 对 U1 求和的边缘后验 `P(U2|Bob)=Σ_u1 P(U1=u1,U2|Bob)`，用 `counts_true` 对 `u1` 维求和归一得到，每 `b` 共享同一归一化，不做 hard `u1_hat`（design §7 定义冻结）。
3. **每条件独立门禁**：`G1' >=7/9`、`G2' 每源 >=2/3`、`G3' 该臂 wrong_codewords==0`（判断条件保留，非优劣排序）。
4. **总量互斥终态机**：`V43_EVIDENCE_INVALID` 优先；其余四态 `V43_BOTH_CONDITIONS_PASS` / `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK` / `V43_GO_STRUCTURE` / `V43_ANOMALOUS_INVERSION` 穷尽互斥覆盖 `(oracle_pass, soft_pass)` 平面；wrong 仅臂内作用，oracle 臂 wrong 额外立旗。
5. **决策分流（仅方向性描述，不自动启动后继；基于冻结门禁，无模糊措辞）**：
   - BOTH pass（`V43_BOTH_CONDITIONS_PASS`：`pass_oracle AND pass_soft_marginal`）：soft-marginal 在相同门禁（G1'≥7/9 且 G2'≥2/源 且 G3' zero-wrong）下保留信号 → 支持继续 soft/joint conditioning
   - oracle-only（即 `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`：`pass_oracle AND NOT pass_soft_marginal`）：soft marginalization 不足
   - both fail（即 `V43_GO_STRUCTURE`：`NOT pass_oracle AND NOT pass_soft_marginal`）：转 joint/protograph/MET
   - anomalous（soft pass + oracle fail，即 `V43_ANOMALOUS_INVERSION`：`NOT pass_oracle AND pass_soft_marginal`）：仅检查，不解释为 soft 优于 oracle
   - orthogonal 标志 `needs_1p5m_structure_branch` 当且仅当 `oracle exact on 1p5M < 2/3` 时立旗，独立于上述终态
6. 预算记账（planned/completed/started actuals）、科学 preflight 优先失效（零 call 停止）、硬上限 18 且结构性拒绝第 19 call、增量证据输出。

本轮不执行。实现须先获独立 plan ACCEPT；任何实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；诊断执行需显式用户 `EXECUTE_AUTH` 绑定到精确实现 SHA，scope `v43_diagnostic_18_calls_exactly_once`。

## Non-goals

- 非参数搜索、非调参：单点 90/1.0，无迭代/damping 网格、warm start、第二设置，不改冻结的 `cond_soft_marginal` 定义。
- 不跑 baseline、Phase B、Lane B，不增矩阵（仅三枚 lane_c ordinal-2）。
- 不复用任何历史块作诊断样本；不追加 blocks、补跑、rerun/resume、结果后改阈值/改机制/加 seeds；无论结果如何不做第二轮诊断。
- 终态不作优劣/资格/晋升/FER/渐近阈值/SKR/安全/真帧陈述，不自动启动后继；后继方向仅描述性。
- 不改 constructor/loader/evaluator/decoder，不改 v35/v38，不 import v39/v40/v41/v42 模块。

## Affected specs

新增 delta spec：`specs/formal-ir-v43-soft-marginal-diagnostic/spec.md`。
不修改任何既有 spec、代码、测试、输出、memory 文件。

## Lifecycle

当前 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（待本线程接受结果后进入 `DEVELOPMENT_RESULT_ACCEPTED`，当前仍为 `PLAN_CANDIDATE`，接受后改为 `DEVELOPMENT_RESULT_ACCEPTED`），`development_execution_authorized`、`formal_execution_authorized`、`scientific_promotion`、`implementation_started`、`production_outputs_created` 均为 false。V42 已 durable（terminal `V42_GO_STRUCTURE / BOTH_ARMS_GATES_FAILED`，accepted plan SHA 53fb371655c5d8c644395ef07dcd9e0a24ec804f，implementation/execution SHA f2ea4fa2c97f6c2ffe5fe6c27f0d84c8f7874e9b，result SHA 1920939200f02be91a8c4849a711ffa7857c5f8f）。需独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定到精确实现 SHA，scope `v43_diagnostic_18_calls_exactly_once`）方可进入实现/执行；V43 不追溯改写历史结论。
