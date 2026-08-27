# OpenSpec Proposal: formal-ir-v45-l1-app-soft-transfer

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **不实现、不运行 decoder，等待独立评审**。任何实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；诊断执行需显式用户 `EXECUTE_AUTH` 绑定到精确实现 SHA。
**Domain**: Formal Information Reconciliation / Nonbinary LDPC research
**Change ID**: `formal-ir-v45-l1-app-soft-transfer`
**Cycle ID**: `V45P0`
**Predecessor cycle**: `V43P0` (`formal-ir-v43-soft-marginal-diagnostic`) 与 `V44P0` (`formal-ir-v44-soft-prior-conditioning` PLAN_REVISE_REQUIRED)
**Predecessor terminal**: `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`（V43 已 durable：result SHA `4e2ed4db`，V43 18-call 配对诊断完成；V44 处置 `NO_NOVEL_MECHANISM` 冻结见 `docs/formal-ir-mathematical-method-map-v25-v44.md §3.4 §7.1`）
**Predecessor accepted plan SHA**: 绑定于 V43 冻结证据（V45 A12 复核时绑定；V44 plan SHA `c51a21c0` 冻结作被否决参照）
**H1 provenance**: `V31 H1 (m1=16, n=1024, GF32 poly37, QC-cyclic-projective, rank16, max_support_occupancy≤31, projective_safe)` 来自 `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v31.py::build_matrix_packet(m1=16, ... family=QC-cyclic-projective)` 经 `build_layer(16,1024)` 确定性构造；候选 H1 已存在但尚未科学验收为本 soft-transfer 的 H1，不得默认已验（见图谱 §5 分支 A）
**Branch / HEAD**: `Placebo303/HD-QKD-Polar-pipeline` `formal-ir-mainline`，HEAD 以实现冻结时 `git rev-parse` 绑定
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，`development_execution_authorized=false`，`formal_execution_authorized=false`，`scientific_promotion=false`，`implementation_started=false`，`production_outputs_created=false`；不启动 V46

> ponytail lite: 已按最小单一机制冻结；更懒路径是零新增诊断直接沿用 V43 结论，需独立评审确认新机制信息是否值得 18-call 预算。

## Goal

在固定 Lane C 三矩阵与译码设置完全冻结下，验证**真实 syndrome-derived L1 APP 软转移**是否改善 V43 soft marginal。唯一科学问题（单一机制、单一对照）：

> **“V31 H1 + 通用 GF32 FFT-QSPA 条件 `q_i(u1)=softmax L_i` 产生的 syndrome-derived L1 APP，能否在固定 Lane C L2 图上改善 V43 soft marginal？”**

其中 `q_i(u1)` 必须来自**通用 `(H1, prior, syndrome)` 接口**的 L1 行分层 FFT-QSPA 软输出：

```
p_i(u1)=P(U1|B_i)= Σ_{u2} C[u1·32+u2, b_i] / Σ_{u1',u2'} C[u1'·32+u2', b_i]   (V25 C, floor 1e-15, 每 b 归一)
s1 = H1 · u1^Alice   (GF32, 真 Alice L1 符号，公开计泄漏)
L_i = decode_row_layered_fftqspa(H1, p_i(u1), s1).final_beliefs   (GF32 行分层 FFT-QSPA，现有实现复用)
q_i = softmax(L_i)   (每位置和=1)
P_i(U2)= Σ_{u1} q_i(u1) · P(U2|B_i, u1)   (V25 条件后验，送固定 L2 译码)
```

对照臂为 V43 `P(U2|B)=Σ p_i(u1)P(U2|B,u1)`（零泄漏 marginal），两臂同块配对、同 H_L2、同 90/1.0 同参，差异仅 `q_i` 来源（syndrome-derived APP vs Bob-only marginal）。

## Non-Goals

- 非 joint GF1024 / GF64 提升图、非耦合联合因子图、非 MET/protograph 重设计（分支 C/D/E 禁止）。
- 不新增 decoder：复用现有 `decode_row_layered_fftqspa` 通用接口，不新增参数、调度、阻尼网格、warm-start；单点 `max_iter=90, damping_alpha=1.0, GF32 poly37`。
- 不做参数网格/调参/C04、pilot/噪声/量化/失配信道律。
- 不并行测试多种 joint/soft/iterative 方案；不跑 baseline/Phase B/Lane B；不增矩阵（仅复用 Lane C 三枚 ordinal-2 与单一 H1）。
- 不追溯改写 V43/V44 结论；不作 FER/阈值/SKR/安全/真帧/资格/晋升陈述；所有终态仅方向性、等待独立评审。
- 不启动 V46；后继仅当本诊断满足开放条件后另立 OpenSpec。

## Scope

本规划轮仅冻结 V45P0 L1-APP 软转移诊断协议，与 V43 同构（18 calls 恰好一次、两臂配对、每条件独立门禁、总量互斥五终态、J6 严格等值、零 rerun）：

1. **单一机制（syndrome-derived，非 Bob-only）**：
   - L1 先验 `p_i(u1)` 仅 `counts+bob`（公共先验，零额外通信）；`q_i` 必经 `M_{H1,s1→i}` 非平凡消息 `q_i ∝ p_i·M_{H1,s1→i}`，`M≡1` 则退化为 V43（恒等式 §3.4）故不计为新机制。
   - H1 复用 `V31 H1 (m1=16, n=1024, GF32, QC-cyclic-projective, rank16)` 确定性重建与结构权威比对（J3）；`s1=H1·u1^Alice` 计入总泄漏；_decoder 复用_，不新增 decoder。
   - L2 侧 `P_i(U2)=Σ q_i P(U2|B_i,u1)` 在固定 Lane C 三矩阵 `lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302` 上，单点 `90/1.0`，syndrome 来自真 `u2_alice`，成功=`exact_l2`。
2. **最小 fresh-block workload（恰好 18 calls）**：每源 3 个从未使用的 TRAIN 新块（1M=390119/390120/390121，1p5M=390219/390220/390221，2M=390319/390320/390321），每块确定性采样一次并被两臂共享；每对用该源 Lane C ordinal-2 代表矩阵、单一冻结设置、三矩阵复用。
3. **FORBIDDEN 零重叠 69**：V36_A3(15) ∪ V39(15) ∪ V40 probe(3) ∪ V41 confirm(9) ∪ V42 diagnostic(9) ∪ V43 diagnostic(9) ∪ V44 diagnostic(9) = **69 seeds** 已占用；九枚新区 `x19-x21/源` 连续递增，无内部重复，与全部七族零重叠（P3/J2 机械复验）。
4. **每条件独立门禁**：`G1' ≥7/9`、`G2' 每源 ≥2/3`、`G3' 该臂 wrong_codewords==0`（`wrong = syndrome_ok && !exact_l2`，永不计为 exact）。
5. **总量互斥五终态 + orthogonal 标志**：`V45_EVIDENCE_INVALID` 优先；其余四态 `V45_BOTH_PASS / V45_ORACLE_ONLY_L1APP_BOTTLENECK / V45_GO_STRUCTURE / V45_ANOMALOUS_INVERSION` 穷尽互斥覆盖 `(oracle_pass, l1app_pass)` 平面；`needs_1p5m_structure_branch` 当且仅当 `oracle exact on 1p5M < 2/3` 时立旗，独立于终态。
6. **泄漏显式**：L1 `80 bits (5·16)` + L2 各源 `984/1014/1024 bits（含 64 tag）`，即 per-source `leak_total = 5·m_total + 64`（`m_total∈{200,206,208}`，`N=1024`），`f_total = leak_total / [N·(H1+H2)]`，`N=1024`，`H_i` 每符号 bits/symbol；V43 对照臂零额外泄漏，比较时 decomposition 语义一致。
7. 预算记账（planned/completed/started actuals）、科学 preflight 优先失效（零 call 停止）、硬上限 18 且结构性拒绝第 19 call、增量证据输出、`errors_initial` 严格 per-pair 跨臂等值门（J6）、Master Stop Rule、no-rerun/no-post-hoc-tuning 边界。

本轮不执行。实现须先获独立 plan ACCEPT；当前为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，等待独立评审；不启动 V46。

## Impact Scope

- **新增**：`openspec/changes/formal-ir-v45-l1-app-soft-transfer/` 四工件（proposal/design/tasks/specs）；未来实现仅新增 `comparison_bench/src/comparison_bench/formal_ir/v45_l1_app_soft_transfer.py` 与 `scripts/execute_v45_l1_app_soft_transfer.py`（本轮不创建）。
- **只读依赖**：`comparison_bench/src/comparison_bench/formal_ir/nonbinary_v31.py`（H1 构造）、`nonbinary_qspa.py`/`v38_architecture_triage.py`/`v35_algorithm_development.py`（accepted 原语/构造/解码）、`comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json`（结构权威）、V25 `channel_counts.npz` 经 `load_v25_channel_counts()`。
- **不修改**：任何既有 spec/代码/测试/输出、`results/`、`comparison_bench/outputs_comparison/` 已有 run_01、`AGENT_PROJECT_MEMORY.md`、`docs/decision-log.md` 以外；不 import `v39/v40/v41/v42/v43/v44` 模块（仅模式拷贝）。

## Acceptance Criteria

- [ ] 四工件齐全且一致：`proposal.md` / `design.md` / `tasks.md` / `specs/formal-ir-v45-l1-app-soft-transfer/spec.md` 在 `openspec/changes/formal-ir-v45-l1-app-soft-transfer/` 下，且科学问题、H1 物料、APP 链、泄漏公式、18-call workload、门禁、终态、J6、no-rerun 均与本 proposal 同构。
- [ ] H1 物料可复现：`V31 H1 (m1=16, n=1024, GF32, QC-cyclic, rank16)` 来自已验证 `build_matrix_packet` QC-cyclic 路径，且 `decode_row_layered_fftqspa(H1, p_i, s1).final_beliefs → softmax` 链无新增 decoder。
- [ ] L1 prior 与 syndrome 语义正确：`p_i(u1)=P(U1|B_i)` 来自 V25 `C(a,b)`，`s1=H1·u1^Alice` 真实 syndrome-derived，非 Bob-only marginal；L2 `P_i(U2)=Σ q_i P(U2|B_i,u1)` 在固定 Lane C 三矩阵 ordinal-2、90/1.0 上。
- [ ] Workload 冻结可机械校验：9 块 `390119-121/390219-221/390319-321` 与 69 FORBIDDEN 零重叠、C01-C18 顺序、`errors_initial` 严格 per-pair 等值、预算 18 硬帽、`needs_1p5m_structure_branch` orthogonal 语义与 V43 同构。
- [ ] 泄漏显式：`L1 80 + L2 984/1014/1024（含 64 tag）`，`leak_total=5·m_total+64`，`f_total=leak_total/[N(H1+H2)]` 含 `N`，且 status 值不被静默转 `ok`。
- [ ] 生命周期正确：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，`EXECUTE_NOT_AUTHORIZED` 等待独立评审，不启动 V46，plan SHA 可追溯。

## Tasks

见 `tasks.md`（Phase A 实现候选冻结常量与组合路径、Phase B 仅 fake-runner 聚焦测试、Phase C decoder-free preflight、Phase D 需 EXECUTE_AUTH 的恰好一次 18-call、Phase E 结果复核与 memory triage 里程碑；显式禁止清单与 V43 同构）。

## Lifecycle

V43 predecessor `DEVELOPMENT_RESULT_ACCEPTED`（terminal `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`，result SHA `4e2ed4db`）；V44 predecessor `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`（`NO_NOVEL_MECHANISM`，plan SHA `c51a21c0`，§3.4 恒等式 `q=P(U1|B) ⇒ P^{V44}=P^{V43}`）。V45 当前 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支、完整实现 SHA、cycle V45P0、scope `v45_diagnostic_18_calls_exactly_once`）方可进入实现/执行；V45 不追溯改写历史结论。
