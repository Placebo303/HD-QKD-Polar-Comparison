# OpenSpec Tasks: formal-ir-v45-l1-app-soft-transfer

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **不实现、不运行 decoder，等待独立评审**。
**Execution status**: **PLAN_CANDIDATE 已生效：不启动实现/执行。** 以下 18-call 任务均待 plan ACCEPT 后方可进入 A-phase；当前不授权、C ne decoder。V43 已 durable（terminal `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`，result SHA `4e2ed4db`）；V44 已处置 `NO_NOVEL_MECHANISM`（plan SHA `c51a21c0`，恒等式 `q=P(U1|B) ⇒ P^{V44}=P^{V43}`）。本诊断仅当满足 §7 开放条件（`M_{H1,s1}≠1` 非平凡）时为新机制；当前不申请 `EXECUTE_AUTH`，不跑生产 decoder，不启动 V46。（V45 不改历史结论；冻结定义仅作 PLAN_CANDIDATE 参照）

## Phase A — 实现候选（plan ACCEPT 后）

- [ ] **A1** 创建模块 `comparison_bench/src/comparison_bench/formal_ir/v45_l1_app_soft_transfer.py`，按 design §6/D15 组合双条件路径（仅 accepted `nonbinary_v31` 构造、`v35` 原语 + `v38` 重建 helper；复用通用 `decode_row_layered_fftqspa` 接口实现 L1 APP 链 `p_i→s1→L_i→q_i→P_i(U2)`）；**不 import** v39/v40/v41/v42/v43/v44 模块（仅模式拷贝）；不改任何既有模块；`decode_fn` 可注入、默认 accepted 解码器；不新增 decoder。
- [ ] **A2** 冻结常量：9 枚新 block seeds（390119-121 / 390219-221 / 390319-321）；FORBIDDEN 并集拷贝数据（V36_A3 ∪ V39 ∪ V40-probe ∪ V41-confirm ∪ V42-diagnostic ∪ V43-diagnostic ∪ V44-diagnostic =69）；三枚 lane_c ordinal-2 代表矩阵 id（design §5）+ 一枚 H1 `V31-H1-QC-16×1024`；冻结 workload C01-C18 精确顺序与条件标签（§4）；条件名（`cond_oracle`、`cond_l1_app`）与机制 id `l1_app_soft_transfer_H1_syndrome_derived`；译码合约 90/1.0 poly 37 同参于 L1/L2（§6）；泄漏 `80+984/1014/1024（含64 tag) f_total=leak_total/[N(H1+H2)] N=1024`（§7）；预算硬帽 18（双臂共享）；输出根与最小文件集（§14）；终态名/原因含保留的 `V45_ANOMALOUS_INVERSION` 与重命名后的 `V45_ORACLE_ONLY_L1APP_BOTTLENECK`（§9）；master stop rule 原文；claim boundary；statistics note。
- [ ] **A3** 实现冻结的 `cond_l1_app` syndrome-derived 软转移（design §7 verbatim）：`p_i(u1)=Σ_{u2} C[u1·32+u2,b]/Σ_{u1',u2'} C`（每 b 归一和=1、floor 1e-15）、`s1=H1·u1^Alice`（GF32）、`L_i=decode(H1,p_i,s1).final_beliefs`（通用接口复用）、`q_i=softmax L_i`（每位置和=1、floor 1e-15）、`P_i(U2)=Σ q_i P(U2|B,u1)`；零额外 hard/再加权；并计算 `mean_abs_diff(q,p)` 非平凡性上下文；机制身份与冻结常量断言一致。
- [ ] **A4** Seed-registry 校验：九枚内无重复；与七族 69 并集机械零重叠；每源恰 3（J2）。
- [ ] **A5** H1 (QC 16×1024) + 3 枚 L2 唯一矩阵确定性重建并与 committed 结构权威严格比对含 `position_permutations`/`capacity`/`projective`/`rank`（H1 rank16）；代表身份等于冻结常量；decoder-free、write-free（J3 双重建）；三源 counts 经 accepted loader 形态/加载校验（J4）。
- [ ] **A6** 双条件绑定 preflight（390119/390219/390319）：oracle 六哨兵 + l1app 七哨兵（design §11：`l1_app_public_inputs`、`s1_is_H1_times_u1_true`、`l1_prior_is_P_U1_given_B`、`carrier_identity_l1app`、`arms_differ`、`l1app_normalization_ok`、`leakage_accounted`），decoder-free、write-free（J5）。
- [ ] **A7** 守卫 runner 时序（design §11 三层）：Tier 0 拒绝类最先且**不创建任何文件** — 默认拒绝、必带 `--execution-authorized`、HEAD 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值、SCOPED tracked-dirty 四文件（v45 模块、v45 CLI、v38 模块、v35 模块）(J1)、输出根已存在即拒 (J7) — 非零退出、零 calls；随后 Tier 1 科学 preflights A4-A6；preflight 失败→建根 + invalid notice + 空 records + summary（terminal EVIDENCE_INVALID，planned 18/started 0/completed 0，无聚合）、零 real calls、停止、不 rerun（D9）；成功→全部守卫/preflights 通过后、首个 decoder call 前建根。
- [ ] **A8** 双条件解码环按冻结序 C01-C18：每块一次确定性采样并共享给两臂；每 call 发记录（schema §12）；配对完备（每块每条件恰一次）+ 严格 per-pair 跨臂 `errors_initial` 等值门（D14/J6：两臂 `errors_initial` 必须严格相等，先于该对解码检查；不等→`V45_EVIDENCE_INVALID`，首对即零 calls；字段 `pairing_errors_initial_equal` 仍作冗余记录）；跨条件 outcome 差异永不判失败；译码参数断言（J9，同参 90/1.0 适用于 L1 与 L2）；共享硬帽 18 且结构拒第 19 call（J10）；workload/顺序断言（J12）；Tier 2 中途 `BaseException`：预建根内原样保留 raw partial + notice + summary(actuals) + 仅失败标记后重抛。
- [ ] **A9** 聚合与终态机：per-condition 聚合（`exact_total`/per-source/wrong）、per-source 聚合、per-block 配对结果 + errors_final delta、`l1app_diagnostics_by_source`（`mean_abs_diff(q,p)`、`H1` 审计、`iterations_l1` 分布，永不 gate）、两臂门禁评定（G1'≥7/9、G2'≥2/3/源、G3'臂内 zero wrong）、总量互斥五终态规则 0-4（BOTH pass / oracle-only / both fail / anomalous 四格冻结门禁判定，见 design §9：BOTH pass 为 L1-APP 在相同门禁下保留信号→支持继续，oracle-only 即 `V45_ORACLE_ONLY_L1APP_BOTTLENECK` 为 L1-APP 不足，both fail 即 `V45_GO_STRUCTURE` 为转 joint/protograph/MET，anomalous 即 `V45_ANOMALOUS_INVERSION` 为 l1app pass + oracle fail 仅检查不解释为 l1app 优于 oracle）及臂内 wrong 语义（`stopped_for_analysis`、`oracle_arm_wrong_codeword_anomaly`，无全局、无跨臂否决）+ `terminal_reason` 与路由轨迹；orthogonal 标志 `needs_1p5m_structure_branch` 当且仅当 `oracle exact on 1p5M < 2/3` 时立旗，独立于终态。
- [ ] **A10** 增量写出：design §14 精确文件集、CSV/JSON 对等、无 NPZ 输出强制、summary 内容按 §12 且门禁明细在 terminal 判定之后、verbatim stop rule、claim boundary、statistics note、provenance 含 O1 机制 id `l1_app_soft_transfer_H1_syndrome_derived` 与 `H1 rank16` 与 `80+984/1014/1024 f_total`；invalid-notice 路径。
- [ ] **A11** 新增 `scripts/execute_v45_l1_app_soft_transfer.py`：默认拒绝、必带旗、绑定 `fake_runner=False`、无 fake-runner CLI 选项、守卫失败非零退出、零 calls、不创建文件。
- [ ] **A12** 实现冻结时绑定前代常量：V43 terminal `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`，V43 result SHA `4e2ed4db`，V44 处置 SHA `c51a21c0` 恒等式 `P^{V44}=P^{V43}`，结构权威身份、V25 counts 溯源、V31 H1 物料身份 `QC-16×1024 rank16`（来自 committed 证据，非“已验 H1”）。

## Phase B — 聚焦测试（仅 fake runner/decode_fn；零生产解码）

- [ ] **T1** Seed-registry 校验：拒重复、错形状、分别与各族重叠（V36_A3、V39、V40 probe 390106/206/306、V41 390107-109/207-209/307-309、V42 390110-112/210-212/310-312、V43 390113-115/213-215/313-315、V44 390116-118/216-218/316-318）；接受冻结九枚。
- [ ] **T2** 重建匹配逻辑：H1 与三 L2 分别注入 metric 漂移（含 `position_permutations`/`capacity`/`projective`/`rank`）→ J 路径；两次重建一致；代表身份错→ J 路径。
- [ ] **T3** 哨兵测试：oracle 六项含 1e-6 max-abs 与 argmax divergence；`u2_bob` 替换被 `captured_equals_bob` 捕获；l1 估计器拒注 alice 依赖变体（公开输入合约，`p_i` 仅 counts/bob；`q_i` 仅 `p_i`+`M_{H1,s1}`）；`s1_is_H1_times_u1_true` spy 捕获替换的 s1；`carrier_identity_l1app` spy 捕获实际送 L2 的 `Σ q_i P(U2|B,u1)` 且 `q_i=softmax L_i`；`arms_differ` 在 `q_i==p_i` 或 `q_i` 均匀时→J5（M 非平凡门）；`l1app_normalization_ok` 越界/未归一→J5（含 floor 1e-15 校验）；`leakage_accounted` 缺 80 或 tag→J5。
- [ ] **T4** 配对一致性：同 seed 重采样一致（idx/alice/bob 同；样本算一次共享）；缺/重块-条件组合→J6/J12；J6 严格门注入：篡改单臂 `errors_initial`→J6→`V45_EVIDENCE_INVALID` 且零 decoder calls（先于该对解码触发）；字段 `pairing_errors_initial_equal` 仍上报；跨条件 outcome 差异不判完整性失败。
- [ ] **T5** 真值表测试：枚举 integrity ok/failed × (oracle_pass, l1app_pass) 四格 {TT BOTH pass→V45_BOTH_PASS, TF oracle-only→V45_ORACLE_ONLY_L1APP_BOTTLENECK, FT anomalous→V45_ANOMALOUS_INVERSION, FF both fail→V45_GO_STRUCTURE}；各落且仅落一终态（design §9 冻结门禁规则 0-4：BOTH pass 为 L1-APP 保留信号，oracle-only 为 L1-APP 不足，both fail 为转 joint/protograph/MET，anomalous 为 l1app pass + oracle fail 仅检查）；EVIDENCE_INVALID 优先；FT 落 `V45_ANOMALOUS_INVERSION`；穷尽互斥。另单独校验 orthogonal 标志 `needs_1p5m_structure_branch` 当且仅当 `oracle exact on 1p5M < 2/3` 时为 true。
- [ ] **T6** Wrong 三态（永不计 exact）：(i) oracle 臂注入→ oracle 臂 G3' 失败、`oracle_arm_wrong_codeword_anomaly=true`、`stopped_for_analysis[cond_oracle]=true`，另一臂不受影响，终态按剩余组合；(ii) l1app 臂注入→对称无 anomaly 旗；(iii) 双臂注入→双 G3' 失败→GO_STRUCTURE 且双 stopped_for_analysis。无跨臂否决。
- [ ] **T7** 预算帽：fake 模式结构拒第 19 call（J10）；planned/started/completed actuals 一致。
- [ ] **T8** 科学 preflight 失败路径：J2/J3/J4/J5 各注入→建增量根、三件套（invalid notice、空 records、summary planned 18/started 0/completed 0、无聚合、terminal EVIDENCE_INVALID）且零 decoder calls。
- [ ] **T9** Partial 保留：注入中途 `BaseException`→预建根内原样保留 raw partial、started/completed actuals、仅失败标记、无性能聚合/门禁/终态，重抛可观测。
- [ ] **T10** CLI 守卫：缺旗→非零、零 calls、不创建；target SHA 与 HEAD 或 origin 分支任一不等→拒；四文件任一 SCOPED dirty→拒（J1）；输出根已存在→拒且不创建（J7，Tier 0）。
- [ ] **T11** 记录 schema 完备含派生 `wrong_codeword` 与 `condition` 与 `h1_matrix_id`；译码参数断言：每记录 poly 37、90/1.0、无 warm-start 键（J9 注入）；oracle selector 等于真 `u1_alice`、l1app 先验等于按 §7 `softmax decode(H1,p_i,s1).final_beliefs` 的 `Σ q_i P(U2|B,u1)`（fixture 输入，每位置和=1、floor 1e-15，`s1=H1·u1_true`）。
- [ ] **T12** 写出合约：文件集精确、CSV/JSON 行对等、已存在根 fail-closed（J7）、不写 NPZ、summary 含 planned/completed/started、`l1app diagnostics`、per-arm/per-source 聚合、配对结果、两门禁明细（在 terminal 之后）、stopped_for_analysis/anomaly、verbatim stop rule、claim boundary；并校验 `needs_1p5m_structure_branch` 当且仅当 `oracle exact on 1p5M < 2/3` 时为 true 的 orthogonal 语义；校验 `80+984/1014/1024 f_total` 含 N。

## Phase C — preflight（decoder-free，授权前）

- [ ] **P1** 重建 H1 (QC 16×1024) + 三 L2 矩阵；与 committed 结构权威含 permutations/capacity/projective/rank 严格匹配；零求值器调用、零写盘。
- [ ] **P2** 在 390119/390219/390319 跑双条件绑定 preflight（含 L1 APP 链：`p_i→s1→L_i→q_i`）；仅报 PASS/BLOCKED。
- [ ] **P3** 以拷贝七族 registries 机械校验 J2（零重叠、无重复、每源 3）并确认输出根缺席；仅报 PASS/BLOCKED。

## Phase D — 授权诊断执行（需 EXECUTE_AUTH）

- [ ] **D1** 主线程获独立 plan 复核 verdict 与显式用户 `EXECUTE_AUTH`（绑定 repository、分支、完整实现 SHA、cycle V45P0、scope `v45_diagnostic_18_calls_exactly_once`）。
- [ ] **D2** 恰好一次：`python scripts/execute_v45_l1_app_soft_transfer.py --execution-authorized --authorized-target-sha <sha>`；保留增量 run_01 文件；出错/partial 止、原样保留 raw partial 无性能聚合、返回 blocker；不 rerun/resume/repair/tuning/加块/改 seed/机制/加权重；无论结果如何**不做第二轮诊断**。
- [ ] **D3** 只读 postcheck：记账（planned 18 / completed 18 / started 18，除非完整性停止）、记录数与序 C01-C18 配对正确、无 NPZ 写、V38-V44 输出 byte-identical、summary 完备、门禁与终态独立重算（含 `needs_1p5m_structure_branch` orthogonal 校验与 `80+984/1014/1024 f_total` 核验）。

## Phase E — 结果复核

- [ ] **E1** 写 OPERATOR_RETURN.md 与 DEVELOPMENT_RESULT.md 候选；lifecycle 保持 result-candidate；含 terminal、路由轨迹、per-condition/per-source 聚合、配对结果、门禁明细、`l1app` 诊断上下文（`M_{H1,s1}` 非平凡性）及有界方向性分流（BOTH pass / oracle-only / both fail / anomalous 四格冻结门禁判定 + orthogonal `needs_1p5m_structure_branch` 当且仅当 `oracle exact on 1p5M < 2/3`）严格在 claim boundary 内。
- [ ] **E2** 主线程/ reviewer 独立重算信号/机器/终态；verdict 抄入 REVIEW_VERDICT.md。
- [ ] **E3** Memory triage 单独里程碑（本规划轮禁改 AGENT_PROJECT_MEMORY.md）；不启动 V46。

## 本变更期间显式禁止

plan ACCEPT 前实现；实现时自选/改非 L1-APP 机制或并行测试多 joint/soft/iterative 方案或上 joint GF1024；新增 decoder/第二 H1/参数网格；加事后权重/C04 调参/引入 Alice 真值直接入 L2 先验（仅 s1 与 exact 可用）；授权 Phase D 外跑任何生产 decoder 或 longrun/minrerun/routeA 脚本；动 V35/V38/V39/V40/V41/V42/V43/V44 代码/测试/docs/输出、AGENT_PROJECT_MEMORY.md、既有 OpenSpec 变更、constructors/loaders/evaluators/decoders、results/、任何官方输出根；import v39/v40/v41/v42/v43/v44 模块；以非 accepted loader 读 NPZ；写任何 NPZ；复用历史块（360101-105 族、390101-321 族 69 seeds）作样本；把 wrong 计为 exact；作条件/lane 优劣或比较排名；FER/阈值/SKR/安全/资格/晋升/真帧陈述；结果后加块/加 seeds/改阈值/改机制/加权重；rerun/resume/补偿 partial；任何结果下开第二轮诊断；任何结果下调 decoder 参数；把跨条件 outcome 差异判为完整性失败；自接受；自动启动后继（含 V46）。
