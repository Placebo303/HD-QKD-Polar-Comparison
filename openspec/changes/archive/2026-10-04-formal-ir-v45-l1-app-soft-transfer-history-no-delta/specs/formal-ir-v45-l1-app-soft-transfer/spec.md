# Delta Specification: formal-ir-v45-l1-app-soft-transfer

**Cycle**: `V45P0`
**Lifecycle of this change**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **不实现、不运行 decoder，等待独立评审**。
**Predecessor**: V43P0 `formal-ir-v43-soft-marginal-diagnostic` — terminal `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`，result SHA `4e2ed4db`（历史能力上界，非本轮对照）；V44 处置 `NO_NOVEL_MECHANISM`（plan SHA `c51a21c0`，`docs/formal-ir-mathematical-method-map-v25-v44.md §3.4` 恒等式 `P^{V44}=P^{V43}`）
**Control**: `P(U2|B)=Σ p_i(u1)P(U2|B,u1)`（V43 soft-marginal，零额外泄漏，本轮对照臂）
**Treatment**: `Σ q_i^{L1APP}(u1)P(U2|B,u1)`，`q_i=softmax BP_posterior`（syndrome-derived L1 APP，额外 80 bits）
**H1**: `V31 H1 (m1=16, n=1024, GF32 poly37, QC-cyclic-projective, rank16, max_support_occupancy≤31, projective_safe, full_row_rank)` 来自 `nonbinary_v31.build_matrix_packet(QC,16)` 确定性构造；候选 H1 已存在但尚未科学验收为本 soft-transfer 的 H1，禁止默认已验
**Mechanism id**: `l1_app_soft_transfer_H1_syndrome_derived`（syndrome-derived `q_i=softmax BP_posterior(H1,p_i,s1)`，`s1=H1·u1^Alice` 计 80 bits，非 Bob-only `P(U1|B)`；`BP_posterior` 为 APP approximation 非精确 APP，冻结 syndrome early-stop）
**Decoder**: 复用通用 `decode_row_layered_fftqspa(H, prior, syndrome).bp_posterior_beliefs`（`GF32 poly37, 90/1.0`，冻结 early-stop），L1/L2 同参，不新增 decoder
**Budget**: 27 decoder invocations（9 L1 + 9 Control L2 + 9 Treatment L2），18 L2 performance records
**HEAD**: `aa18c4af`

## R1. Predecessor binding

V45P0 SHALL build only on V43P0 evidence（`formal-ir-v43-soft-marginal-diagnostic`，terminal `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`，result SHA `4e2ed4db` 作历史参照）与 V44 处置 `NO_NOVEL_MECHANISM` 恒等式 `q=P(U1|B) ⇒ P^{V44}=P^{V43}`（`docs/formal-ir-mathematical-method-map-v25-v44.md §3.4 §7.2` 开放判据 `q^{(t)}∝p·M_{H1,s1}≠p`）。V43 oracle 仅作历史能力上界，SHALL NOT 作为本轮 paired 对照臂。V45 SHALL NOT retroactively alter any historical terminal/lifecycle/conclusion, and SHALL NOT import v39/v40/v41/v42/v43/v44 modules. V45 执行授权 SHALL 仅需 V45 自身独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支、完整实现 SHA、cycle V45P0、scope `v45_diagnostic_27_invocations_exactly_once`，HEAD `aa18c4af`）；V45 SHALL NOT 启动 V46。

## R2. Question and shape（单一 syndrome-derived 机制，对照为 V43 soft-marginal）

本变更 SHALL 精确回答一个问题 — 在 Lane C 图结构与译码设置完全冻结下，将 V43 soft-marginal 控制 `cond_control: P(U2|B)=Σ p_i P(U2|B,u1)` 替换为**单一** syndrome-derived L1 APP 软转移 `cond_l1_app: Σ q_i P(U2|B,u1)`（R7 verbatim：`V31 H1 + 通用 FFT-QSPA` 的 `q_i=softmax BP_posterior`，`s1=H1·u1^Alice`，BP posterior 为 APP approximation 非精确 APP）是否在相同门禁（G1'≥7/9 且 G2'≥2/源 且 G3' zero-wrong，基于 `exact_l2`）下改善 V43 soft-marginal — 以**恰好 27 次 decoder invocations（9 L1 + 18 L2）、其中 18 条 L2 performance records、单阶段、恰好一次**：9 块各配对解两次 L2（`cond_control` 与 `cond_l1_app`），每块另 1 次 L1。仅 Lane C + 单一复用 H1；无 baseline、无新增矩阵、无 decoder 参数调优、无历史块复用、**不并行测试多种 joint/soft/iterative 方案，不上 joint GF1024，不做参数网格，不以 oracle 为对照**。

## R3. Frozen sample set and pairing

样本 SHALL 为恰好 9 个新 TRAIN 开发块，冻结常量：1M=390119/390120/390121，1p5M=390219/390220/390221，2M=390319/390320/390321，以 `sample_empirical_block(V25 TRAIN counts, block_seed, 1024)` + `factorize_f03` 采样。每块确定性样本 `(idx, alice, bob)` SHALL 算一次并被两臂共享（L1 与两 L2 共享同一块样本）；一对的两 L2 calls SHALL 仅在喂给 L2 译码的 conditioning 构造上不同（V43 soft-marginal `p_i` vs syndrome-derived `q_i`，H1/s1/L1 APP 仅 treatment 臂引入，control 臂不经 L1）。

## R4. Seed-registry disjointness

机械 registry 断言（J2）SHALL 在实现时校验：九枚内无重复；与 V36_A3(360101-105/360201-205/360301-305) ∪ V39(390101-105/390201-205/390301-305) ∪ V40 probe(390106/390206/390306) ∪ V41 confirm(390107-109/390207-209/390307-309) ∪ V42 diagnostic(390110-112/390210-212/390310-312) ∪ V43 diagnostic(390113-115/390213-215/390313-315) ∪ V44 diagnostic(390116-118/390216-218/390316-318) 共 **69 枚**零重叠；且每源恰 3。Registries 以拷贝数据常量进入。

## R5. Representative matrices

Lane C SHALL 用其 ordinal-2 代表矩阵/源，冻结常量：`lane_c_1M_s383102`、`lane_c_1p5M_s383202`、`lane_c_2M_s383302`。H1 SHALL 为 `V31-H1-QC-16×1024`（`m1=16, n=1024, family=QC-cyclic-projective, GF32 poly37, rank16, capacity_ok, projective_safe, full_row_rank`）。18 L2 records 去重为 3 枚唯一 L2 矩阵 + 1 枚 H1（另 9 L1 invocations 同 H1）。Preflight SHALL 经 accepted 构造器确定性重建全部四枚，严格匹配 committed 结构权威（含 Lane C `position_permutations` 与 H1 `capacity/projective/rank`），否则 J3；代表身份漂移亦 J3。

## R6. Dual posterior-binding preflight（仅 fake beliefs 通路，真实 APP 不在 preflight）

授权执行前，decoder-free、write-free preflight SHALL 在每源首块（390119/390219/390319）校验：(a) 六项 control 哨兵（`bob_gt_31`、捕获第二参量等于完整 `bob`、`corrected_equals_direct`、`corrected_differs_u2bob arraywise`、max-abs >1e-6、`argmax_divergence`）；(b) 七项 `cond_l1_app` 哨兵改为 **fake-beliefs 通路**：`l1_app_public_inputs`（L1 先验仅 counts/bob，拒 Alice 依赖）、`s1_is_H1_times_u1_true`（送 L1 解码的 syndrome 等于 `H1·u1^Alice` 的 spy 捕获）、`l1_prior_is_P_U1_given_B`（L1 prior 等于按 R7 从 `counts_true` 求和归一的 `p_i`）、`carrier_identity_l1app_fake`（实际送 L2 的先验经 spy 捕获、等于按 R7 `Σ q_fake P(U2|B,u1)` 且 `q_fake=softmax fake_BP`）、`l1app_normalization_ok_fake`（每位置 fake `q` 和=1，容差 1e-12，floor 1e-15）、`leakage_accounted`（summary 区分 Control 984/1014/1024 vs Treatment 1064/1094/1104，syndrome 920/950/960 + 80 + 64 tag）、`fake_path_verified`。零生产 decoder calls；失败走 R11 invalid 路径；哨兵可替换仅在 plan-review 阶段。**真实 `q≠p`、L1 iterations/syndrome_ok/exact/wrong、APP entropy/confidence SHALL NOT 在 preflight gate；真实 `q≈p` 或近 uniform SHALL 为阴性科学结果，非 `V45_EVIDENCE_INVALID`**。

## R7. Decoder contract and composed dual-condition path（syndrome-derived APP 软转移，BP posterior / APP approximation）

27 invocations（含 9 L1 + 18 L2）SHALL 均用 GF32 poly 37、经 accepted 解码函数的 row-layered FFT-QSPA（复用通用 `decode_row_layered_fftqspa`，返回 `bp_posterior_beliefs` 为 BP posterior / APP approximation 非精确 APP，冻结当前 syndrome early-stop 行为）、L2 来自真 `u2_alice` 的 syndrome、L1 `s1=H1·u1^Alice` 计泄漏、以 `exact_l2` 为主要成功（L2-transfer），同时报告 `exact_full=exact_u1 && exact_l2`、单点冻结 `max_iter=90, damping_alpha=1.0` 同参于 L1 与 L2；无 warm start/retry/第二设置。L1 hard decision 不 exact 时仍继续 L2 软转移，不停止；`exact_full` 另行报告，不得把 `exact_l2` 成功而 `exact_u1` 失败的记录称为完整多级成功。Control 臂 SHALL 为 V43 soft-marginal `prior = Σ p_i(u1)P(U2|B,u1)=P(U2|B)`，`p_i` 来自 counts/bob；`cond_l1_app` 臂 SHALL 精确为冻结 syndrome-derived APP 软转移（verbatim，单一机制）：

- `p_i(u1) = Σ_{u2} C[u1·32+u2, b_i] / Σ_{u1',u2'} C[u1'·32+u2', b_i]`（`C` = V25 channel_counts，`b_i∈bob`，分母 floor 1e-15，每位置和=1）
- `s1 = H1 · u1^Alice`（GF32, `H1∈GF32^{16×1024}`，公开计 `80 bits =5·16`，`m1=16`）
- `BP_i = decode_row_layered_fftqspa(H1, p_i(u1), s1).bp_posterior_beliefs[i]`（每位置 32 长 log-beliefs，BP posterior / APP approximation 非精确 APP，冻结 early-stop，不新增 decoder；记录 `iterations_l1/syndrome_ok_l1/exact_u1/wrong_l1/entropy`）
- `q_i(u1) = softmax_{u1} BP_i(u1) = exp(BP_i(u1))/Σ_{u1'} exp(BP_i(u1'))`（每位置和=1，floor 1e-15 防零；`q_i ∝ p_i·M_{H1,s1→i}`，`M≡1` 则退化为 V43 soft-marginal）
- `P_i(U2=u2) = Σ_{u1} q_i(u1) · P(U2=u2|B=b_i,U1=u1)`，其中 `P(U2|B,u1)=C[u1·32+u2,b_i]/Σ_{u2'} C[u1·32+u2',b_i]`
- 采样仍仅用同一 `counts_true` 且两臂共享一次生成的块；`q_i` 由 `H1,s1` 的校验消息非平凡派生；真实 `q≠p` 仅执行期测量

**泄漏显式（修正单位）**：`m1=16 → 80 bits`；`m2 ∈ {184,190,192} → L2 syndrome 920/950/960 bits`；`m2+tag: 5·m2+64 = 984/1014/1024 bits`；`m_total=m1+m2 ∈ {200,206,208}`；Control `leak_total=5·m2+64=984/1014/1024`，Treatment `leak_total=5·m_total+64=1064/1094/1104`，`f_total=leak_total/[N·(H1+H2)]`，`N=1024`，`H_i` bits/symbol 来自 `SOURCE_H`。Control 与 Treatment 非等泄漏比较，结论仅为“额外 80-bit L1 syndrome information 的 L2 transfer value”，decomposition 语义显式区分。SHALL NOT 引入 Alice 真值直接入 L2 先验（`u1_true` 仅用于 `s1` 与 `exact`）、事后权重、hard `u1_hat`、pilot、噪声、量化、joint 迭代、新矩阵、新 decoder 参数、失配信道律、C04 调参、joint GF1024。机制身份 SHALL 与冻结常量 `l1_app_soft_transfer_H1_syndrome_derived` 断言一致且后续不得更改。因 `evaluate_single_block` 硬编码 oracle 且 `counts` 兼作采样，runner SHALL 按 design D15 组合 accepted `nonbinary_v31` + `v35` 原语复刻 v38 992-1030 仅改 conditioning 构造；数值均来自 accepted 模块；不改冻结文件。`wrong_codeword = syndrome_ok and not exact` SHALL 单计且永不计为 exact（区分 l2 与 l1）；偏离即 J9。H1 存在性不等价于验收性（图谱 §5 分支 A）。`bp_posterior_beliefs` 术语 SHALL 取代 `final_beliefs` 精确 APP 表述。

## R8. Frozen workload and call order

Workload SHALL 精确为 27 invocations：9 L1（每块一次）+ 18 L2 records C01-C18（design §4）：源 1M/1p5M/2M、块升序、pair 内 `cond_control` 在前；成员/顺序/配对漂移即 J12；H1/s1/L1 APP 仅 treatment 臂引入。Summary SHALL 分别记录 `l1=9 / control_l2=9 / treatment_l2=9 / total=27` 的 planned/completed/started actuals。

## R9. Per-condition gates（基于 exact_l2）

每条件臂独立以其 9 条 L2 records（primary `exact_l2`）：G1' overall exact_l2 ≥7/9；G2' 每源 exact_l2 ≥2/3；G3' 该臂 wrong==0。臂通过当且仅当三条全满足；门禁仅判定条件保留，SHALL NOT 支持条件/lane 间优劣或比较排名。同时报告 `exact_full` 聚合作完整 reconciliation 参照，但不入 G1'/G2'/G3'。

## R10. Terminal machine（新命名，基于 (control_pass, treatment_pass)）

五终态、总量互斥：`V45_EVIDENCE_INVALID`、`V45_BOTH_RETAINED`、`V45_L1APP_NO_VALUE_OR_HARM`、`V45_GO_STRUCTURE`、`V45_L1APP_ADDED_VALUE_SIGNAL`（覆盖 `(control_pass, treatment_pass)` 平面；oracle 不占维度）。完整性优先、首命中胜：

```
0. 任意完整性/执行失败 -> V45_EVIDENCE_INVALID
1. pass_control AND pass_treatment -> V45_BOTH_RETAINED
   (Both retained：L1-APP 软转移在相同门禁（G1'≥7/9 且 G2'≥2/源 且 G3' zero-wrong, 基于 exact_l2）下保留信号)
2. 仅 pass_control -> V45_L1APP_NO_VALUE_OR_HARM (reason TREATMENT_ARM_GATE_FAILED)
   (Control-only：L1-APP 无价值或有害，额外 80-bit 未改善 L2-transfer)
3. 均不通过 -> V45_GO_STRUCTURE (reason BOTH_ARMS_GATES_FAILED)
   (Both fail：转 joint/protograph/MET)
4. 仅 pass_treatment -> V45_L1APP_ADDED_VALUE_SIGNAL (reason CONTROL_ARM_FAILED_WITH_TREATMENT_PASSING)
   (Treatment-only：V45_L1APP_ADDED_VALUE_SIGNAL，仅检查，不作无条件优于 control 的泛化)
```

`V45_L1APP_ADDED_VALUE_SIGNAL` 断言边界：仅意味有限样本/迭代轨迹/条件先验差异需检查，SHALL NEVER 泛化为 treatment 无条件优于 control。`V45_L1APP_NO_VALUE_OR_HARM` 断言边界：损失仅归因于本次 L1-APP 软转移的局限（`M_{H1,s1}` 不足或 H1 自身不收敛，或额外 80-bit 未转化），NOT Lane C 图结构，不归因到具体上游编码或真实系统；结论为额外 80-bit 的 L2 transfer value 评估。`V45_BOTH_RETAINED` 为保留信号，非晋升依据。Wrong 处理仅臂内：记录、永不计 exact、仅通过本臂 G3'、并置 `stopped_for_analysis[condition]=true`；无全局、无跨臂否决；任意 control 臂 wrong SHALL 立旗 `control_arm_wrong_codeword_anomaly=true`。映射 SHALL 总量互斥覆盖全部 `(control_pass, treatment_pass)` 组合，强制真值表测试枚举 integrity ok/failed × 四格并断言穷尽互斥；terminal 判定先于门禁明细展示；summary 仍分别报告两臂 wrong 与 `exact_full`。**决策分流**（仅方向性，基于冻结门禁与 exact_l2）：BOTH retained→保留信号；control-only→L1-APP 无价值或有害；both fail→转 joint/protograph/MET；treatment-only→新增价值信号仅检查。后继方向仅 summary 描述，不授权任何后继；不启动 V46。旧命名 `V45_BOTH_PASS / V45_ORACLE_ONLY_L1APP_BOTTLENECK / V45_ANOMALOUS_INVERSION` 已移除，SHALL NOT 出现。

orthogonal 标志 `needs_1p5m_structure_branch` 当且仅当 `control exact on 1p5M < 2/3` 时为 true，独立于上述终态。

## R11. Integrity-first invalidation, guard ordering, and evidence tiers

Runner SHALL 一一实现 design §11 三层边界：

- **Tier 0 执行拒绝**（J1 默认拒绝/必带旗/HEAD 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值（HEAD `aa18c4af`）/SCOPED tracked-dirty 四文件 `v45 模块/v45 CLI/v38 模块/v35 模块`；J7 输出根已存在）最先、fail-closed、**不创建任何文件**、非零退出、零 decoder calls。
- **Tier 1 科学 preflight 失败**（J2 含 69 并集、J3 H1+L2 双重建、J4 counts、J5 哨兵 fake-beliefs 通路）decoder-free；任一失败 SHALL 建增量根并写 invalid 三件套 — `v45_invalid_notice.json`、空 records、`v45_summary.json`（terminal `V45_EVIDENCE_INVALID`，planned 27 固定（l1 9/control 9/treatment 9/total 27）、started 0（分层 0）、completed 0，无聚合）后零 real calls 停止、不 rerun。
- **Tier 2 中途执行失败**（`BaseException`）：预建根内原样保留 raw partial + notice + summary(actuals 分 l1/control/treatment/total) + 仅失败标记后重抛。
- **正常完成**：仅最小固定集（records json/csv 18 行 + summary 含分层记账 27；无 NPZ）。

完整性失败 J1-J12 致 `V45_EVIDENCE_INVALID`；invalid/partial 上不解释性能。跨条件 outcome-field 比较（`errors_final/iterations/exact_l2/syndrome_ok/wrong_codeword`）SHALL NEVER 作完整性失败 — 其为诊断信号。J6 为严格 per-pair 跨臂 `errors_initial` 等值门（design §10/O3）：同块两臂 `errors_initial` MUST 严格相等，先于该对解码检查；不等即 J6→`V45_EVIDENCE_INVALID`（`errors_initial=sum(u2_alice!=u2_bob)` 与先验构造无关，跨臂不等即配对/求值器漂移）；字段 `pairing_errors_initial_equal` 仍作冗余记录。真实 `q≈p` SHALL NOT 致 invalid。

## R12. Budget and stop rules

总预算 SHALL 为 27 decoder invocations（9 L1 + 9 Control L2 + 9 Treatment L2）；L2 performance records 18。Summary SHALL 分别记录 `l1=9 / control_l2=9 / treatment_l2=9 / total=27` 的 planned/completed/started actuals。第 28 call SHALL 结构拒（J10）；恰好一次、无 rerun/resume。Master stop rule SHALL 原文记入 summary：

> 唯一一次 27-invocation 双条件配对诊断（含 9 L1 BP + 18 L2）；对照为 V43 soft-marginal `P(U2|B)`（Control）vs Treatment `Σ q_i P(U2|B,u1)`；仅 Lane C 固定各 source ordinal-2 代表矩阵 + V31 H1 QC 16×1024、max_iter=90、damping_alpha=1.0 冻结 early-stop 不再调参；cond_l1_app 按冻结 syndrome-derived APP（p_i(u1)=P(U1|B)、s1=H1·u1^Alice、BP_i=decode(H1,p_i,s1).bp_posterior_beliefs / APP approximation、q_i=softmax BP_i、P_i(U2)=Σ q_i P(U2|B,u1)、泄漏 Control 984/1014/1024 (syndrome 920/950/960+64 tag) vs Treatment 1064/1094/1104 (含 80) f_total=leak_total/[N(H1+H2)] N=1024，H1 复用 rank16 QC-cyclic，通用 FFT-QSPA 复用不新增 decoder，不做 hard 估计/pilot/噪声/量化/失配信道律/joint 迭代/新矩阵/新 decoder 参数/参数网格/joint GF1024，区分 exact_l2 与 exact_full，Control/Treatment 非等泄漏比较为额外 80-bit 价值评估）后不再更改。无论结果如何：不追加 blocks、不补跑、不做第二轮诊断、不并行测试多方案、不启动 V46。

## R13. Records and evidence outputs

每 L2 call SHALL 产一条记录，共 18 条，schema 见 design §12（含 `condition`=`cond_control`/`cond_l1_app` 与 `h1_matrix_id` 与 `iterations_l1/iterations_l2/exact_l2/exact_u1/exact_full/syndrome_ok_l1/syndrome_ok_l2/wrong_l1/wrong_l2/bp_posterior_entropy/mean_abs_diff_q_p`）。L1 9 次 invocations 记账单列，诊断随行。授权跑 SHALL 仅在增量根 `comparison_bench/outputs_comparison/formal_ir_methods/v45_l1_app_soft_transfer/run_01/` 下写：`v45_records.json/.csv`（18 行）、`v45_summary.json`（含分层记账与 exact_l2/exact_full 双报告）、完整性失败时加 `v45_invalid_notice.json`；CSV/JSON 对等；SHALL NOT 写任何 NPZ；SHALL NOT 以非 accepted loader 读 NPZ；输出根在全部守卫与 preflights 通过后、首个 decoder call 前创建，已存在即 fail-closed（J7）；summary SHALL 含 planned 27（分层）/completed/started actuals、`l1_diagnostics_by_source`（执行期测量永不 gate：`mean_abs_diff(q,p)`、`APP entropy/confidence`、`H1_rank/capacity/projective`、`iterations_l1/syndrome_ok_l1/exact_u1/wrong_l1` 分布）、per-condition 聚合（区分 exact_l2 与 exact_full）、per-source 聚合、per-block 配对结果与 errors_final delta、两臂门禁明细（基于 exact_l2，在 terminal 之后）、路由轨迹、terminal+reason（新命名）、`stopped_for_analysis`、`control_arm_wrong_codeword_anomaly`、`needs_1p5m_structure_branch`（当且仅当 `control exact on 1p5M < 2/3` 时为 true，orthogonal 标志）、verbatim stop rule、claim boundary（含非等泄漏）、statistics note、provenance 含 O1 机制 id `l1_app_soft_transfer_H1_syndrome_derived` 与 `H1 rank16` 与 `Control 984/1014/1024 vs Treatment 1064/1094/1104 (syndrome 920/950/960) f_total`；既有 results/、V38-V44 输出保持 byte-identical。

## R14. Lifecycle, authorization

本变更 lifecycle SHALL 保持 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` 直至独立 plan ACCEPT；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。单次诊断执行需显式用户 `EXECUTE_AUTH`（绑定 repository、分支、完整实现 SHA、cycle V45P0、scope `v45_diagnostic_27_invocations_exactly_once`，HEAD `aa18c4af`）；CLI SHALL 默认拒绝、要求 `--execution-authorized --authorized-target-sha <sha>`、校验 HEAD 与 origin/formal-ir-mainline 精确等值、执行 SCOPED tracked-dirty；禁止 rerun/tuning/阈值或机制替换/加 seeds/自接受/自动后继；V45 SHALL NOT 启动 V46。

## R15. Claim boundary

结果仅支持 V25 TRAIN 经验 counts 开发块上的有界条件归因。Control 臂为 V43 soft-marginal `P(U2|B)`（零额外泄漏）；`cond_l1_app` 臂按 R7 以 V31 H1 (16×1024 QC-cyclic rank16) + 通用 `decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs / APP approximation → softmax q_i` 做真实 syndrome-derived 软转移、L2 在固定 Lane C 三矩阵 ordinal-2 上 90/1.0 单点（冻结 early-stop）、`Control 984/1014/1024 vs Treatment 1064/1094/1104 (L2 syndrome 920/950/960 + 80 + 64 tag) f_total=leak_total/[N(H1+H2)] N=1024` 计泄漏，无 hard/噪声/量化/失真律/C04/joint GF1024，不是耦合图/分支 C/D/E，不得泛化为真实条件；Control 与 Treatment 非等泄漏比较，结论仅为“额外 80-bit L1 syndrome information 的 L2 transfer value”；`V45_L1APP_NO_VALUE_OR_HARM` 仅归因到本次 L1-APP 软转移的局限，永不归因到具体上游编码或真实系统；`V45_L1APP_ADDED_VALUE_SIGNAL` 仅意味有限样本/迭代/先验差异需检查，永不作无条件优于 control 的证据；`exact_l2` 为主要诊断，`exact_full` 另行报告，`exact_u1==false` 的软转移仍计但不称完整成功；均非真帧 FER 证据，不推阈值/SKR/正式执行/资格/晋升。无论结果如何禁止：FER、渐近阈值、SKR、安全、正式资格/晋升、真帧行为、条件/lane 间优劣或比较排名、历史门禁“现已通过”陈述；成功主判 `exact_l2`；样本 tiny 且成簇（9 唯一块 × (1 L1 + 2 L2)）且未校正簇聚。
