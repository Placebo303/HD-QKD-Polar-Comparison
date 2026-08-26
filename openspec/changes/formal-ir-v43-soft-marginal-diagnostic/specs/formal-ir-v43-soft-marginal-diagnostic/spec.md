# Delta Specification: formal-ir-v43-soft-marginal-diagnostic

**Cycle**: `V43P0`
**Lifecycle of this change**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（待本线程接受结果后进入 `DEVELOPMENT_RESULT_ACCEPTED`，当前仍为 `PLAN_CANDIDATE`，接受后改为 `DEVELOPMENT_RESULT_ACCEPTED`）
**Predecessor**: V42P0 `formal-ir-v42-conditional-realism-diagnostic` — terminal `V42_GO_STRUCTURE / BOTH_ARMS_GATES_FAILED`，accepted plan SHA 53fb371655c5d8c644395ef07dcd9e0a24ec804f，implementation/execution SHA f2ea4fa2c97f6c2ffe5fe6c27f0d84c8f7874e9b，result SHA 1920939200f02be91a8c4849a711ffa7857c5f8f

## R1. Predecessor binding

V43P0 SHALL build only on V42P0 evidence（`formal-ir-v42-conditional-realism-diagnostic`，terminal `V42_GO_STRUCTURE / BOTH_ARMS_GATES_FAILED`，accepted plan SHA 53fb371655c5d8c644395ef07dcd9e0a24ec804f，implementation/execution SHA f2ea4fa2c97f6c2ffe5fe6c27f0d84c8f7874e9b，result SHA 1920939200f02be91a8c4849a711ffa7857c5f8f；Lane C 18-call 配对诊断形态）。V43 SHALL NOT retroactively alter any historical terminal/lifecycle/conclusion, and SHALL NOT import v39/v40/v41/v42 modules. V43 执行授权 SHALL 仅需 V43 自身独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支、完整实现 SHA、cycle V43P0、scope `v43_diagnostic_18_calls_exactly_once`）。

## R2. Question and shape

本变更 SHALL 精确回答一个问题 — 在 Lane C 图结构与译码设置完全冻结下，将 oracle-L1 条件 `cond_oracle` 替换为软边缘化 `cond_soft_marginal`（R7 verbatim）是否在相同门禁（G1'≥7/9 且 G2'≥2/源 且 G3' zero-wrong）下保留信号 — 以**恰好 18 次真实 decoder calls、单阶段、恰好一次**：9 块各配对解两次（`cond_oracle` 与 `cond_soft_marginal`）。仅 Lane C；无 baseline、无新增矩阵、无 decoder 参数调优、无历史块复用。

## R3. Frozen sample set and pairing

样本 SHALL 为恰好 9 个新 TRAIN 开发块，冻结常量：1M=390113/390114/390115，1p5M=390213/390214/390215，2M=390313/390314/390315，以 `sample_empirical_block(V25 TRAIN counts, block_seed, 1024)` + `factorize_f03` 采样。每块确定性样本 `(idx, alice, bob)` SHALL 算一次并被两臂共享；一对的两 calls SHALL 仅在喂给后验的 conditioning 构造上不同。

## R4. Seed-registry disjointness

机械 registry 断言（J2）SHALL 在实现时校验：九枚内无重复；与 V36_A3(360101-105/360201-205/360301-305) ∪ V39(390101-105/390201-205/390301-305) ∪ V40 probe(390106/390206/390306) ∪ V41 confirm(390107-109/390207-209/390307-309) ∪ V42 diagnostic(390110-112/390210-212/390310-312) 共 51 枚零重叠；且每源恰 3。Registries 以拷贝数据常量进入。

## R5. Representative matrices

Lane C SHALL 用其 ordinal-2 代表矩阵/源，冻结常量：`lane_c_1M_s383102`、`lane_c_1p5M_s383202`、`lane_c_2M_s383302`。18 行去重为 3 枚唯一矩阵。Preflight SHALL 经 accepted 构造器确定性重建全部三枚，严格匹配 committed 结构权威（含 Lane C `position_permutations`），否则 J3；代表身份漂移亦 J3。

## R6. Dual posterior-binding preflight

授权执行前，decoder-free、write-free preflight SHALL 在每源首块（390113/390213/390313）校验：(a) 六项 oracle 哨兵（`bob_gt_31`、捕获第二参量等于完整 `bob`、`corrected_equals_direct`、`corrected_differs_u2bob arraywise`、max-abs >1e-6、`argmax_divergence`）；(b) 四项 `cond_soft_marginal` 哨兵：`soft_marginal_public_inputs`、`carrier_identity_soft`（实际送 soft 臂解码的先验经 spy 捕获、等于按 R7 从 `counts_true` 求和归一的 soft 后验）、`arms_differ`（soft 先验至少一位置与 oracle 先验不同）、`soft_marginal_normalization_ok`（每 b 求和为 1）。零生产 decoder calls；失败走 R11 invalid 路径；哨兵可替换仅在 plan-review 阶段。

## R7. Decoder contract and composed dual-condition path

18 calls SHALL 均用 GF(32) poly 37、经 accepted 解码函数的 row-layered FFT-QSPA、来自真 `u2_alice` 的 syndrome、以 `exact_l2` 为唯一成功、单点冻结 `max_iter=90, damping_alpha=1.0`；无 warm start/retry/第二设置。Oracle 臂 selector SHALL 为真 `u1_alice`，`posterior = get_conditional_posterior_l2(counts_true, bob, u1_true)`；`cond_soft_marginal` 臂 SHALL 精确为冻结软边缘化（verbatim）：

- `marginal_counts[u2,b] = Σ_{u1=0..31} counts_true[u1*32+u2, b]`
- `P_soft(U2=u2|Bob=b) = marginal_counts[u2,b] / Σ_{u2'} marginal_counts[u2',b]`
- 每 `b` 共享同一归一化；采样仍仅用同一 `counts_true` 且两臂共享一次生成的块
- SHALL NOT 引入 hard `u1_hat`、pilot、噪声、量化、joint 迭代、新矩阵、新 decoder 参数、失配信道律

命名边界：`cond_soft_marginal` 是“使用真实公共经验 counts 的理想化软边缘化”，NOT 任何具体 operational L1 方案，SHALL NOT 泛化为真实条件。机制身份 SHALL 与冻结常量断言一致且后续不得更改。因 `evaluate_single_block` 硬编码 oracle 且 `counts` 兼作采样，runner SHALL 按 design D15 组合 accepted v35 原语复刻 v38 992-1030 仅改 selector；数值均来自 accepted 模块；不改冻结文件。`wrong_codeword = syndrome_ok and not exact_l2` SHALL 单计且永不计为 exact；偏离即 J9。

## R8. Frozen workload and call order

Workload SHALL 精确为 C01-C18（design §4）：源 1M/1p5M/2M、块升序、pair 内 `cond_oracle` 在前；成员/顺序/配对漂移即 J12。

## R9. Per-condition gates

每条件臂独立以其 9 calls：G1' overall exact ≥7/9；G2' 每源 exact ≥2/3；G3' 该臂 wrong==0。臂通过当且仅当三条全满足；门禁仅判定条件保留，SHALL NOT 支持条件/lane 间优劣或比较排名。

## R10. Terminal machine

五终态、总量互斥：`V43_EVIDENCE_INVALID`、`V43_BOTH_CONDITIONS_PASS`、`V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`、`V43_GO_STRUCTURE`、`V43_ANOMALOUS_INVERSION`（保留 V42 异常语义，覆盖 `oracle_fail && soft_pass`）。完整性优先、首命中胜：

```
0. 任意完整性/执行失败 -> V43_EVIDENCE_INVALID
1. pass_oracle AND pass_soft_marginal -> V43_BOTH_CONDITIONS_PASS
   (BOTH pass：soft-marginal 在相同门禁（G1'≥7/9 且 G2'≥2/源 且 G3' zero-wrong）下保留信号 → 支持继续 soft/joint conditioning)
2. 仅 pass_oracle -> V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK (reason SOFT_MARGINAL_ARM_GATE_FAILED)
   (oracle-only（即 V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK）：soft marginalization 不足)
3. 均不通过 -> V43_GO_STRUCTURE (reason BOTH_ARMS_GATES_FAILED)
   (both fail（即 V43_GO_STRUCTURE）：转 joint/protograph/MET)
4. 仅 pass_soft_marginal -> V43_ANOMALOUS_INVERSION (reason ORACLE_ARM_FAILED_WITH_SOFT_MARGINAL_ARM_PASSING)
   (anomalous（soft pass + oracle fail）：仅检查，不解释为 soft 优于 oracle)
```

`V43_ANOMALOUS_INVERSION` 断言边界：仅意味有限样本/迭代轨迹/条件后验差异需检查，SHALL NEVER 解释为 soft 优于 oracle。`V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK` 断言边界：损失仅归因于本次软边缘条件的局限，NOT Lane C 图结构，不归因到具体上游编码或真实系统。Wrong 处理仅臂内：记录、永不计 exact、仅通过本臂 G3'、并置 `stopped_for_analysis[condition]=true`；无全局、无跨臂否决；任意 oracle 臂 wrong SHALL 立旗 `oracle_arm_wrong_codeword_anomaly=true`。映射 SHALL 总量互斥覆盖全部 `(oracle_pass, soft_pass)` 组合，强制真值表测试枚举 integrity ok/failed × 四格并断言穷尽互斥；terminal 判定先于门禁明细展示；summary 仍分别报告两臂 wrong。**决策分流**（仅方向性，基于冻结门禁）：BOTH pass→支持继续 soft/joint conditioning；oracle-only→soft marginalization 不足；both fail→转 joint/protograph/MET；anomalous→仅检查，不解释为 soft 优于 oracle。后继方向仅 summary 描述，不授权任何后继；所有终态下不追加块/补跑/第二轮/调参/结果后改阈值或机制。

orthogonal 标志 `needs_1p5m_structure_branch` 当且仅当 `oracle exact on 1p5M < 2/3` 时为 true，独立于上述终态。

## R11. Integrity-first invalidation, guard ordering, and evidence tiers

Runner SHALL 一一实现 design §11 三层边界：

- **Tier 0 执行拒绝**（J1 默认拒绝/必带旗/HEAD 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值/SCOPED tracked-dirty 四文件；J7 输出根已存在）最先、fail-closed、**不创建任何文件**、非零退出、零 decoder calls。
- **Tier 1 科学 preflight 失败**（J2 含 V42 家族 51 并集、J3 严格重建、J4 counts、J5 哨兵）decoder-free；任一失败 SHALL 建增量根并写 invalid 三件套 — `v43_invalid_notice.json`、空 records、`v43_summary.json`（terminal `V43_EVIDENCE_INVALID`，planned 18 固定、started 0、completed 0，无聚合）后零 real calls 停止、不 rerun。
- **Tier 2 中途执行失败**（`BaseException`）：预建根内原样保留 raw partial + notice + summary(actuals) + 仅失败标记后重抛。
- **正常完成**：仅最小固定集（records json/csv + summary；无 NPZ）。

完整性失败 J1-J12 致 `V43_EVIDENCE_INVALID`；invalid/partial 上不解释性能。跨条件 outcome-field 比较（`errors_final/iterations/exact_l2/syndrome_ok/wrong_codeword`）SHALL NEVER 作完整性失败 — 其为诊断信号。J6 为严格 per-pair 跨臂 `errors_initial` 等值门（design §10/O3）：同块两臂 `errors_initial` MUST 严格相等，先于该对解码检查；不等即 J6→`V43_EVIDENCE_INVALID`（`errors_initial=sum(u2_alice!=u2_bob)` 与 selector 无关，跨臂不等即配对/求值器漂移）；字段 `pairing_errors_initial_equal` 仍作冗余记录。

## R12. Budget and stop rules

总预算 SHALL 不超 18 真实 decoder calls（双臂共享）；第 19 call SHALL 结构拒（J10）；恰好一次、无 rerun/resume。Master stop rule SHALL 原文记入 summary：

> 唯一一次 18-call 双条件配对诊断；仅 Lane C、固定各 source ordinal-2 代表矩阵、max_iter=90、damping_alpha=1.0，不再调参；cond_soft_marginal 按冻结软边缘化（marginal_counts[u2,b]=Σ_u1 counts_true[u1*32+u2,b]，P_soft=marginal/Σ_u2' marginal，每 b 共享归一化，不做 hard u1_hat，无 pilot/噪声/量化/失配信道律/joint 迭代/新矩阵/新 decoder 参数）后不再更改。无论结果如何：不追加 blocks、不补跑、不做第二轮诊断。

## R13. Records and evidence outputs

每 call SHALL 产一条记录，schema 见 design §12（含 `condition`）。授权跑 SHALL 仅在增量根 `comparison_bench/outputs_comparison/formal_ir_methods/v43_soft_marginal_diagnostic/run_01/` 下写：`v43_records.json/.csv`、`v43_summary.json`，完整性失败时加 `v43_invalid_notice.json`；CSV/JSON 对等；SHALL NOT 写任何 NPZ；SHALL NOT 以非 accepted loader 读 NPZ；输出根在全部守卫与 preflights 通过后、首个 decoder call 前创建，已存在即 fail-closed（J7）；summary SHALL 含 planned/completed/started actuals、`soft_marginal_diagnostics_by_source`（上下文永不 gate）、per-condition 聚合、per-source 聚合、per-block 配对结果与 errors_final delta、两臂门禁明细（在 terminal 之后）、路由轨迹、terminal+reason、`stopped_for_analysis`、`oracle_arm_wrong_codeword_anomaly`、`needs_1p5m_structure_branch`（当且仅当 `oracle exact on 1p5M < 2/3` 时为 true，orthogonal 标志）、verbatim stop rule、claim boundary、statistics note、provenance 含 O1 机制 id；既有 results/、V38-V42 输出保持 byte-identical。

## R14. Lifecycle, authorization

本变更 lifecycle SHALL 保持 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（待本线程接受结果后进入 `DEVELOPMENT_RESULT_ACCEPTED`，当前仍为 `PLAN_CANDIDATE`，接受后改为 `DEVELOPMENT_RESULT_ACCEPTED`）直至独立 plan ACCEPT；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。单次诊断执行需显式用户 `EXECUTE_AUTH`（绑定 repository、分支、完整实现 SHA、cycle V43P0、scope `v43_diagnostic_18_calls_exactly_once`）；CLI SHALL 默认拒绝、要求 `--execution-authorized --authorized-target-sha <sha>`、校验 HEAD 与 origin/formal-ir-mainline 精确等值、执行 SCOPED tracked-dirty；禁止 rerun/tuning/阈值或机制替换/加 seeds/自接受/自动后继。

## R15. Claim boundary

结果仅支持 V25 TRAIN 经验 counts 开发块上的有界条件归因。Oracle 臂为真 Alice L1 的能力上界（实践不可得）；`cond_soft_marginal` 臂按 R7 用真实公共经验 counts 做理想化软边缘化（`counts_true` 对 `u1` 求和归一、每 `b` 共享归一化，不做 hard 估计、无 pilot/噪声/量化/失真律）且两臂共享一次生成的块，NOT 任何具体 coded/operational L1 结果，SHALL NOT 泛化为真实条件；`V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK` 仅归因到本次软边缘条件的局限，永不归因到具体上游编码或真实系统；`V43_ANOMALOUS_INVERSION` 仅意味有限样本/迭代/后验差异需检查，永不作 soft 优于 oracle 的证据；均非真帧 FER 证据，不推阈值/SKR/正式执行/资格/晋升。无论结果如何禁止：FER、渐近阈值、SKR、安全、正式资格/晋升、真帧行为、条件/lane 间优劣或比较排名、历史门禁“现已通过”陈述；成功仅 `exact_l2`；样本 tiny 且成簇（9 唯一块 ×2 配对条件）且未校正簇聚。
