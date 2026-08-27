# Delta Specification: formal-ir-v45-l1-app-soft-transfer

**Cycle**: `V45P0`
**Lifecycle of this change**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **不实现、不运行 decoder，等待独立评审**。
**Predecessor**: V43P0 `formal-ir-v43-soft-marginal-diagnostic` — terminal `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`，result SHA `4e2ed4db`；V44 处置 `NO_NOVEL_MECHANISM`（plan SHA `c51a21c0`，`docs/formal-ir-mathematical-method-map-v25-v44.md §3.4` 恒等式 `P^{V44}=P^{V43}`）
**H1**: `V31 H1 (m1=16, n=1024, GF32 poly37, QC-cyclic-projective, rank16, max_support_occupancy≤31, projective_safe, full_row_rank)` 来自 `nonbinary_v31.build_matrix_packet(QC,16)` 确定性构造；候选 H1 已存在但尚未科学验收为本 soft-transfer 的 H1，禁止默认已验
**Mechanism id**: `l1_app_soft_transfer_H1_syndrome_derived`（syndrome-derived `q_i=softmax decode(H1,p_i,s1).final_beliefs`，`s1=H1·u1^Alice` 计 80 bits，非 Bob-only `P(U1|B)`）
**Decoder**: 复用通用 `decode_row_layered_fftqspa(H, prior, syndrome).final_beliefs`（`GF32 poly37, 90/1.0`），L1/L2 同参，不新增 decoder

## R1. Predecessor binding

V45P0 SHALL build only on V43P0 evidence（`formal-ir-v43-soft-marginal-diagnostic`，terminal `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`，result SHA `4e2ed4db`；Lane C 18-call 配对诊断形态）与 V44 处置 `NO_NOVEL_MECHANISM` 恒等式 `q=P(U1|B) ⇒ P^{V44}=P^{V43}`（`docs/formal-ir-mathematical-method-map-v25-v44.md §3.4 §7.2` 开放判据 `q^{(t)}∝p·M_{H1,s1}≠p`）。V45 SHALL NOT retroactively alter any historical terminal/lifecycle/conclusion, and SHALL NOT import v39/v40/v41/v42/v43/v44 modules. V45 执行授权 SHALL 仅需 V45 自身独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支、完整实现 SHA、cycle V45P0、scope `v45_diagnostic_18_calls_exactly_once`）；V45 SHALL NOT 启动 V46。

## R2. Question and shape（单一 syndrome-derived 机制）

本变更 SHALL 精确回答一个问题 — 在 Lane C 图结构与译码设置完全冻结下，将 oracle-L1 条件 `cond_oracle` 替换为**单一** syndrome-derived L1 APP 软转移 `cond_l1_app`（R7 verbatim：`V31 H1 + 通用 FFT-QSPA` 的 `q_i=softmax L_i`，`s1=H1·u1^Alice`，非 Bob-only marginal）是否在相同门禁（G1'≥7/9 且 G2'≥2/源 且 G3' zero-wrong）下改善 V43 soft marginal — 以**恰好 18 次真实 decoder calls、单阶段、恰好一次**：9 块各配对解两次（`cond_oracle` 与 `cond_l1_app`）。仅 Lane C + 单一复用 H1；无 baseline、无新增矩阵、无 decoder 参数调优、无历史块复用、**不并行测试多种 joint/soft/iterative 方案，不上 joint GF1024，不做参数网格**。

## R3. Frozen sample set and pairing

样本 SHALL 为恰好 9 个新 TRAIN 开发块，冻结常量：1M=390119/390120/390121，1p5M=390219/390220/390221，2M=390319/390320/390321，以 `sample_empirical_block(V25 TRAIN counts, block_seed, 1024)` + `factorize_f03` 采样。每块确定性样本 `(idx, alice, bob)` SHALL 算一次并被两臂共享；一对的两 calls SHALL 仅在喂给 L2 译码的 conditioning 构造上不同（oracle 真 U1 vs syndrome-derived `q_i`，H1/s1/L1 APP 仅 l1app 臂引入）。

## R4. Seed-registry disjointness

机械 registry 断言（J2）SHALL 在实现时校验：九枚内无重复；与 V36_A3(360101-105/360201-205/360301-305) ∪ V39(390101-105/390201-205/390301-305) ∪ V40 probe(390106/390206/390306) ∪ V41 confirm(390107-109/390207-209/390307-309) ∪ V42 diagnostic(390110-112/390210-212/390310-312) ∪ V43 diagnostic(390113-115/390213-215/390313-315) ∪ V44 diagnostic(390116-118/390216-218/390316-318) 共 **69 枚**零重叠；且每源恰 3。Registries 以拷贝数据常量进入。

## R5. Representative matrices

Lane C SHALL 用其 ordinal-2 代表矩阵/源，冻结常量：`lane_c_1M_s383102`、`lane_c_1p5M_s383202`、`lane_c_2M_s383302`。H1 SHALL 为 `V31-H1-QC-16×1024`（`m1=16, n=1024, family=QC-cyclic-projective, GF32 poly37, rank16, capacity_ok, projective_safe, full_row_rank`）。18 行去重为 3 枚唯一 L2 矩阵 + 1 枚 H1。Preflight SHALL 经 accepted 构造器确定性重建全部四枚，严格匹配 committed 结构权威（含 Lane C `position_permutations` 与 H1 `capacity/projective/rank`），否则 J3；代表身份漂移亦 J3。

## R6. Dual posterior-binding preflight

授权执行前，decoder-free、write-free preflight SHALL 在每源首块（390119/390219/390319）校验：(a) 六项 oracle 哨兵（`bob_gt_31`、捕获第二参量等于完整 `bob`、`corrected_equals_direct`、`corrected_differs_u2bob arraywise`、max-abs >1e-6、`argmax_divergence`）；(b) 七项 `cond_l1_app` 哨兵：`l1_app_public_inputs`（L1 先验仅 counts/bob，拒 Alice 依赖）、`s1_is_H1_times_u1_true`（送 L1 解码的 syndrome 等于 `H1·u1^Alice` 的 spy 捕获）、`l1_prior_is_P_U1_given_B`（L1 prior 等于按 R7 从 `counts_true` 求和归一的 `p_i`）、`carrier_identity_l1app`（实际送 L2 的先验经 spy 捕获、等于按 R7 `Σ q_i P(U2|B,u1)` 且 `q_i=softmax L_i`）、`arms_differ`（l1app 先验至少一位置与 oracle 先验不同，且 `q_i≠p_i` 非平凡）、`l1app_normalization_ok`（每位置 `q_i` 和=1，容差 1e-12，floor 1e-15）、`leakage_accounted`（summary 计 80+L2 leakage）。零生产 decoder calls；失败走 R11 invalid 路径；哨兵可替换仅在 plan-review 阶段。

## R7. Decoder contract and composed dual-condition path（syndrome-derived APP 软转移）

18 calls SHALL 均用 GF32 poly 37、经 accepted 解码函数的 row-layered FFT-QSPA（复用通用 `decode_row_layered_fftqspa`）、L2 来自真 `u2_alice` 的 syndrome、L1 `s1=H1·u1^Alice` 计泄漏、以 `exact_l2` 为唯一成功、单点冻结 `max_iter=90, damping_alpha=1.0` 同参于 L1 与 L2；无 warm start/retry/第二设置。Oracle 臂 SHALL 为真 `u1_alice`，`posterior = get_conditional_posterior_l2(counts_true, bob, u1_true)`；`cond_l1_app` 臂 SHALL 精确为冻结 syndrome-derived APP 软转移（verbatim，单一机制）：

- `p_i(u1) = Σ_{u2} C[u1·32+u2, b_i] / Σ_{u1',u2'} C[u1'·32+u2', b_i]`（`C` = V25 channel_counts，`b_i∈bob`，分母 floor 1e-15，每位置和=1）
- `s1 = H1 · u1^Alice`（GF32, `H1∈GF32^{16×1024}`，公开计 `80 bits =5·16`）
- `L_i = decode_row_layered_fftqspa(H1, p_i(u1), s1).final_beliefs[i]`（每位置 32 长 log-beliefs，通用接口复用，不新增 decoder）
- `q_i(u1) = softmax_{u1} L_i(u1) = exp(L_i(u1))/Σ_{u1'} exp(L_i(u1'))`（每位置和=1，floor 1e-15 防零；`q_i ∝ p_i·M_{H1,s1→i}`，`M≡1` 则退化为 V43）
- `P_i(U2=u2) = Σ_{u1} q_i(u1) · P(U2=u2|B=b_i,U1=u1)`，其中 `P(U2|B,u1)=C[u1·32+u2,b_i]/Σ_{u2'} C[u1·32+u2',b_i]`
- 采样仍仅用同一 `counts_true` 且两臂共享一次生成的块；`q_i` 由 `H1,s1` 的校验消息非平凡派生

**泄漏显式**：`leak_L1=5·16=80`；per-source `leak_L2+tag =5·m2+64`（`m2=m_total-16`：1M 984, 1p5M 1014, 2M 1024；`m_total∈{200,206,208}, N=1024`）；总计 `leak_total=5·m_total+64 = leak_L1+leak_L2+tag`，`f_total=leak_total/[N·(H1+H2)]`，`N=1024`，`H_i` bits/symbol 来自 `SOURCE_H`。V43 对照臂零额外泄漏，比较时 decomposition 语义一致。SHALL NOT 引入 Alice 真值直接入 L2 先验（`u1_true` 仅用于 `s1` 与 `exact`）、事后权重、hard `u1_hat`、pilot、噪声、量化、joint 迭代、新矩阵、新 decoder 参数、失配信道律、C04 调参、joint GF1024。机制身份 SHALL 与冻结常量 `l1_app_soft_transfer_H1_syndrome_derived` 断言一致且后续不得更改。因 `evaluate_single_block` 硬编码 oracle 且 `counts` 兼作采样，runner SHALL 按 design D15 组合 accepted `nonbinary_v31` + `v35` 原语复刻 v38 992-1030 仅改 conditioning 构造；数值均来自 accepted 模块；不改冻结文件。`wrong_codeword = syndrome_ok and not exact_l2` SHALL 单计且永不计为 exact；偏离即 J9。H1 存在性不等价于验收性（图谱 §5 分支 A）。

## R8. Frozen workload and call order

Workload SHALL 精确为 C01-C18（design §4）：源 1M/1p5M/2M、块升序、pair 内 `cond_oracle` 在前；成员/顺序/配对漂移即 J12；H1/s1/L1 APP 仅 l1app 臂引入。

## R9. Per-condition gates

每条件臂独立以其 9 calls：G1' overall exact ≥7/9；G2' 每源 exact ≥2/3；G3' 该臂 wrong==0。臂通过当且仅当三条全满足；门禁仅判定条件保留，SHALL NOT 支持条件/lane 间优劣或比较排名。

## R10. Terminal machine

五终态、总量互斥：`V45_EVIDENCE_INVALID`、`V45_BOTH_PASS`、`V45_ORACLE_ONLY_L1APP_BOTTLENECK`、`V45_GO_STRUCTURE`、`V45_ANOMALOUS_INVERSION`（保留 V42/V43 异常语义，覆盖 `oracle_fail && l1app_pass`）。完整性优先、首命中胜：

```
0. 任意完整性/执行失败 -> V45_EVIDENCE_INVALID
1. pass_oracle AND pass_l1app -> V45_BOTH_PASS
   (BOTH pass：L1-APP 软转移在相同门禁（G1'≥7/9 且 G2'≥2/源 且 G3' zero-wrong）下保留信号 → 支持继续 soft/joint conditioning)
2. 仅 pass_oracle -> V45_ORACLE_ONLY_L1APP_BOTTLENECK (reason L1APP_ARM_GATE_FAILED)
   (oracle-only：L1-APP 软转移不足)
3. 均不通过 -> V45_GO_STRUCTURE (reason BOTH_ARMS_GATES_FAILED)
   (both fail：转 joint/protograph/MET)
4. 仅 pass_l1app -> V45_ANOMALOUS_INVERSION (reason ORACLE_ARM_FAILED_WITH_L1APP_ARM_PASSING)
   (anomalous（l1app pass + oracle fail）：仅检查，不解释为 l1app 优于 oracle)
```

`V45_ANOMALOUS_INVERSION` 断言边界：仅意味有限样本/迭代轨迹/条件先验差异需检查，SHALL NEVER 解释为 l1app 优于 oracle。`V45_ORACLE_ONLY_L1APP_BOTTLENECK` 断言边界：损失仅归因于本次 L1-APP 软转移的局限（`M_{H1,s1}` 不足或 H1 自身不收敛），NOT Lane C 图结构，不归因到具体上游编码或真实系统。Wrong 处理仅臂内：记录、永不计 exact、仅通过本臂 G3'、并置 `stopped_for_analysis[condition]=true`；无全局、无跨臂否决；任意 oracle 臂 wrong SHALL 立旗 `oracle_arm_wrong_codeword_anomaly=true`。映射 SHALL 总量互斥覆盖全部 `(oracle_pass, l1app_pass)` 组合，强制真值表测试枚举 integrity ok/failed × 四格并断言穷尽互斥；terminal 判定先于门禁明细展示；summary 仍分别报告两臂 wrong。**决策分流**（仅方向性，基于冻结门禁）：BOTH pass→支持继续 L1 soft 转移；oracle-only→L1-APP 不足；both fail→转 joint/protograph/MET；anomalous→仅检查，不解释为 l1app 优于 oracle。后继方向仅 summary 描述，不授权任何后继；不启动 V46。

orthogonal 标志 `needs_1p5m_structure_branch` 当且仅当 `oracle exact on 1p5M < 2/3` 时为 true，独立于上述终态。

## R11. Integrity-first invalidation, guard ordering, and evidence tiers

Runner SHALL 一一实现 design §11 三层边界：

- **Tier 0 执行拒绝**（J1 默认拒绝/必带旗/HEAD 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值/SCOPED tracked-dirty 四文件 `v45 模块/v45 CLI/v38 模块/v35 模块`；J7 输出根已存在）最先、fail-closed、**不创建任何文件**、非零退出、零 decoder calls。
- **Tier 1 科学 preflight 失败**（J2 含 69 并集、J3 H1+L2 双重建、J4 counts、J5 哨兵）decoder-free；任一失败 SHALL 建增量根并写 invalid 三件套 — `v45_invalid_notice.json`、空 records、`v45_summary.json`（terminal `V45_EVIDENCE_INVALID`，planned 18 固定、started 0、completed 0，无聚合）后零 real calls 停止、不 rerun。
- **Tier 2 中途执行失败**（`BaseException`）：预建根内原样保留 raw partial + notice + summary(actuals) + 仅失败标记后重抛。
- **正常完成**：仅最小固定集（records json/csv + summary；无 NPZ）。

完整性失败 J1-J12 致 `V45_EVIDENCE_INVALID`；invalid/partial 上不解释性能。跨条件 outcome-field 比较（`errors_final/iterations/exact_l2/syndrome_ok/wrong_codeword`）SHALL NEVER 作完整性失败 — 其为诊断信号。J6 为严格 per-pair 跨臂 `errors_initial` 等值门（design §10/O3）：同块两臂 `errors_initial` MUST 严格相等，先于该对解码检查；不等即 J6→`V45_EVIDENCE_INVALID`（`errors_initial=sum(u2_alice!=u2_bob)` 与先验构造无关，跨臂不等即配对/求值器漂移）；字段 `pairing_errors_initial_equal` 仍作冗余记录。

## R12. Budget and stop rules

总预算 SHALL 不超 18 真实 decoder calls（双臂共享，L1 解码计入 per-call runtime 不额外计 budget）；第 19 call SHALL 结构拒（J10）；恰好一次、无 rerun/resume。Master stop rule SHALL 原文记入 summary：

> 唯一一次 18-call 双条件配对诊断；仅 Lane C 固定各 source ordinal-2 代表矩阵 + V31 H1 QC 16×1024、max_iter=90、damping_alpha=1.0 不再调参；cond_l1_app 按冻结 syndrome-derived APP（p_i(u1)=P(U1|B)、s1=H1·u1^Alice、L_i=decode(H1,p_i,s1).final_beliefs、q_i=softmax L_i、P_i(U2)=Σ q_i P(U2|B,u1)、泄漏 80+984/1014/1024 f_total=leak_total/[N(H1+H2)] N=1024，H1 复用 rank16 QC-cyclic，通用 FFT-QSPA 复用不新增 decoder，不做 hard 估计/pilot/噪声/量化/失配信道律/joint 迭代/新矩阵/新 decoder 参数/参数网格/joint GF1024）后不再更改。无论结果如何：不追加 blocks、不补跑、不做第二轮诊断、不并行测试多方案、不启动 V46。

## R13. Records and evidence outputs

每 call SHALL 产一条记录，schema 见 design §12（含 `condition` 与 `h1_matrix_id` 与 `iterations_l1`）。授权跑 SHALL 仅在增量根 `comparison_bench/outputs_comparison/formal_ir_methods/v45_l1_app_soft_transfer/run_01/` 下写：`v45_records.json/.csv`、`v45_summary.json`，完整性失败时加 `v45_invalid_notice.json`；CSV/JSON 对等；SHALL NOT 写任何 NPZ；SHALL NOT 以非 accepted loader 读 NPZ；输出根在全部守卫与 preflights 通过后、首个 decoder call 前创建，已存在即 fail-closed（J7）；summary SHALL 含 planned/completed/started actuals、`l1app_diagnostics_by_source`（上下文永不 gate：`mean_abs_diff(q,p)`、`H1_rank/capacity/projective`、`iterations_l1` 分布）、per-condition 聚合、per-source 聚合、per-block 配对结果与 errors_final delta、两臂门禁明细（在 terminal 之后）、路由轨迹、terminal+reason、`stopped_for_analysis`、`oracle_arm_wrong_codeword_anomaly`、`needs_1p5m_structure_branch`（当且仅当 `oracle exact on 1p5M < 2/3` 时为 true，orthogonal 标志）、verbatim stop rule、claim boundary、statistics note、provenance 含 O1 机制 id `l1_app_soft_transfer_H1_syndrome_derived` 与 `H1 rank16` 与 `80+984/1014/1024 f_total`；既有 results/、V38-V44 输出保持 byte-identical。

## R14. Lifecycle, authorization

本变更 lifecycle SHALL 保持 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` 直至独立 plan ACCEPT；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。单次诊断执行需显式用户 `EXECUTE_AUTH`（绑定 repository、分支、完整实现 SHA、cycle V45P0、scope `v45_diagnostic_18_calls_exactly_once`）；CLI SHALL 默认拒绝、要求 `--execution-authorized --authorized-target-sha <sha>`、校验 HEAD 与 origin/formal-ir-mainline 精确等值、执行 SCOPED tracked-dirty；禁止 rerun/tuning/阈值或机制替换/加 seeds/自接受/自动后继；V45 SHALL NOT 启动 V46。

## R15. Claim boundary

结果仅支持 V25 TRAIN 经验 counts 开发块上的有界条件归因。Oracle 臂为真 Alice L1 的能力上界（实践不可得）；`cond_l1_app` 臂按 R7 以 V31 H1 (16×1024 QC-cyclic rank16) + 通用 `decode_row_layered_fftqspa(H1,p_i,s1).final_beliefs → softmax q_i` 做真实 syndrome-derived 软转移、L2 在固定 Lane C 三矩阵 ordinal-2 上 90/1.0 单点、`80+984/1014/1024 f_total=leak_total/[N(H1+H2)] N=1024` 计泄漏，无 hard/噪声/量化/失真律/C04/joint GF1024，不是耦合图/分支 C/D/E，不得泛化为真实条件；`V45_ORACLE_ONLY_L1APP_BOTTLENECK` 仅归因到本次 L1-APP 软转移的局限，永不归因到具体上游编码或真实系统；`V45_ANOMALOUS_INVERSION` 仅意味有限样本/迭代/先验差异需检查，永不作 soft 优于 oracle 的证据；均非真帧 FER 证据，不推阈值/SKR/正式执行/资格/晋升。无论结果如何禁止：FER、渐近阈值、SKR、安全、正式资格/晋升、真帧行为、条件/lane 间优劣或比较排名、历史门禁“现已通过”陈述；成功仅 `exact_l2`；样本 tiny 且成簇（9 唯一块 ×2 配对条件）且未校正簇聚。
