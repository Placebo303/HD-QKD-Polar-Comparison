# OpenSpec Tasks: formal-ir-v46-verification-semantics

**Lifecycle**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V47。修订后保持此状态，等待再次评审。**
**Execution status**: 本轮不授权任何实现/执行；以下任务待独立 plan 再次 ACCEPT 后方可进入 A-phase；当前不跑 decoder，不写产出。已删除基于缺失 x_hat 对 V45 18 条记录的 tag 重放方案（全 N/A 只读 run 禁止）。V46-REV 冻结 `tag_scope=l2_only` 与 `compute_tag_64(empty, x2)`。
**HEAD**: `2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`

## Phase A — 语义冻结（plan 再次 ACCEPT 后）

- [ ] **A1** 冻结 tag 复用语义（L2-only）：**直接复用 `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py::compute_tag_64`**（`b1+b2 → SHA256 → hex[:16]` trunc64），不重新实现 `canonical_bytes/tag_of/归一化`，不宣称 `compute_tag_64_symbols` 与空前缀调用等价（仅来源说明）；`tag_scope=l2_only`；`target_tag=compute_tag_64(empty_uint8, x2_true)`、`candidate_tag=compute_tag_64(empty_uint8, x2_hat)`，其中 `empty_uint8=np.empty(0,dtype=np.uint8)`，`tag_ok=(candidate==target)`；**删除所有 `compute_tag_64(x1_true, x_hat)` 形态**；Control/Treatment 均此形态，不使用 x1_true 或共享 L1 decode；64-bit 与当前 L2+tag 泄漏口径一致；`tag_ok==false` 计作非 exact/rejected；保存 `tag_ok` 必需，不必保存完整 `x_hat`；明确 SHA-trunc64 为**工程 verification（随机哈希模型约 `2^-64` 近似）**，不宣称信息论 `2^-64` 界（严格界需 universal2+seed）；本轮 tag 只验证 L2，`exact_full` 仍 oracle 报告（`exact_u1&&exact_l2`）。
- [ ] **A2** 冻结重分类与门禁新语义：四类 `exact / detected_verification_failure (syndrome_ok&&!exact&&!tag_ok) / decoder_non_syndrome_failure (!syndrome_ok&&!exact) / undetected_accepted_wrong (tag_ok&&!exact, 工程近似≈2^-64)`；`structure_failure` 更名为 `decoder_non_syndrome_failure`（`!syndrome_ok&&!exact` 可能来自图/先验/迭代/BP 动力学，不单归因结构）；G3 改为 `undetected_accepted_wrong==0`（`tag_ok&&!exact` 计数为 0），不要求 decoder 永不产生 `syndrome_ok&&!exact`（被 gate 捕获为 detected 即不违规）；`exact_l2` 仍 oracle 判真；pre-tag 时序（`wrong/G3/exact` 在 verification 之前）断言。
- [ ] **A3** 冻结终态可区分：`detected_verification_failure / decoder_non_syndrome_failure / undetected_accepted_wrong / exact` 四类正交计数与 `reclassified`；五终态 `V46_*` 在 `undetected==0` 新 G3' 下判定。
- [ ] **A4** 冻结 fresh-block 与隔离根：9 个新块 `390122-124/390222-224/390322-324`（每源 3，见 design §3，与 FORBIDDEN 78 零重叠）；增量根 `comparison_bench/outputs_comparison/formal_ir_methods/v46_verification_semantics/run_01/` fail-closed；最小文件集含 `target_tag/candidate_tag/tag_ok/tag_scope/reclassified` 四类；无 NPZ。
- [ ] **A5** 冻结 V45 边界：不追溯重放 V45 18 条记录，不创建全 N/A 只读 run，不改 V45 终态/文件；V46 用 fresh blocks 验证“Treatment 7/9 增益能否在真实 verification acceptance 下复现”。
- [ ] **A6** 冻结其余 V45 同构常量：BP posterior beliefs / APP approximation 表述、泄漏口径（`L2 920/950/960 +64=984/1014/1024, Treatment 1064/1094/1104, f_total=leak/[N(H1+H2)] N=1024`）、J6 `errors_initial` 严格 per-pair 等值门、译码合约 `90/1.0 poly37 early-stop`、H1 `16×1024` 与 Lane C 三矩阵 ordinal-2。

## Phase B — 聚焦测试（仅 fake runner/decode_fn；零生产解码）

- [ ] **B1** Seed-registry 校验：拒重复、错形状、分别与各族重叠（V36_A3 15、V39 15、V40 probe 3、V41 9、V42 9、V43 9、V44 9、V45 9 共78）；接受冻结九枚 `390122-124/222-224/322-324`。
- [ ] **B2** 重建匹配逻辑：H1 与三 L2 分别注入 metric 漂移（含 `position_permutations`/`capacity`/`projective`/`rank`）→ J 路径；两次重建一致；代表身份错→ J 路径。
- [ ] **B3** Tag 复用与分流测试（L2-only 空前缀）：`compute_tag_64` 确定性、`hex[:16]` 长度语义、`v35_tag_import_ok`（仅 `compute_tag_64`，`symbols` 仅来源说明）；**不变性测试：改变 `x1_true` 不得改变 V46 L2 tag**（`compute_tag_64(empty,x2)` 与任意 x1 无关）；**敏感性测试：改变 `x2` 必须改变测试锚点 tag**（固定 empty 前缀下 x2 变化必致 tag 变化）；四类分流：`syndrome_ok&&!exact&&!tag_ok → detected_verification_failure`、`!syndrome_ok&&!exact → decoder_non_syndrome_failure`、`tag_ok&&!exact → undetected_accepted_wrong (工程近似)`、`exact → exact`；G3' 仅 `undetected==0` 触发，`detected` 不触发；并断言不存在 `compute_tag_64(x1_true, x_hat)` 调用路径。
- [ ] **B4** 哨兵与泄漏测试：control 六项 + treatment fake 七项（同 V45）+ `v35_tag_import_ok`（L2-only 空前缀） + `tag_scope_l2_only` + `leakage_accounted`（`984/1014/1024 vs 1064/1094/1104` 区分，`leakage_already_accounted` 声名，工程 verification 声名 `SHA-trunc64 random-hash approx, L2-only`）+ `exact_full` oracle 声名（不经 tag）；不测真实 `q≠p` gate（真实非平凡仅执行期，`q≈p` 为阴性非 invalid）；校验不重新实现 `canonical_bytes`（import 断言）且不宣称 symbols 等价。
- [ ] **B5** 配对一致性：同 seed 重采样一致（样本算一次共享）；缺/重块-条件组合→J6/J12；J6 严格门注入：篡改单臂 `errors_initial`→J6→`V46_EVIDENCE_INVALID` 且零 decoder calls；字段 `pairing_errors_initial_equal` 仍上报；跨条件 outcome 差异不判完整性失败；`tag_ok` 差异亦为诊断量。
- [ ] **B6** 真值表测试：枚举 integrity ok/failed × (control_pass, treatment_pass) 四格 {TT BOTH retained→V46_BOTH_RETAINED, TF control-only→V46_L1APP_NO_VALUE_OR_HARM, FT treatment-only→V46_L1APP_ADDED_VALUE_SIGNAL, FF both fail→V46_GO_STRUCTURE}；各落且仅落一终态；EVIDENCE_INVALID 优先；穷尽互斥。另校验 orthogonal 标志 `needs_1p5m_structure_branch` 当且仅当 `control exact on 1p5M < 2/3` 时为 true；校验四类计数完备与 G3' `undetected==0` 判定。
- [ ] **B7** Wrong/undetected 三态（基于新 G3'）：(i) control 臂注入 `detected`→ control 臂 `stopped_for_analysis[cond_control]=true` 但 G3' 仍通过（因 `undetected==0`），另一臂不受影响；(ii) control 臂注入 `undetected`→ control G3' 失败、`control_arm_undetected_anomaly=true`；(iii) 双臂 `undetected`→双 G3' 失败→GO_STRUCTURE 且双 stopped_for_analysis。无跨臂否决。
- [ ] **B8** 预算帽：fake 模式结构拒第 28 call（J10，总硬帽 27，区分 l1 9/control 9/treatment 9/total 27）；planned/started/completed actuals 一致且分层记录。
- [ ] **B9** 科学 preflight 失败路径：J2/J3/J4/J5 各注入→建增量根、三件套（invalid notice、空 records、summary planned 27 / l1 0 / control 0 / treatment 0 / total 0、无聚合、terminal EVIDENCE_INVALID）且零 decoder calls。
- [ ] **B10** Partial 保留：注入中途 `BaseException`→预建根内原样保留 raw partial（含 `tag_ok`/`tag_scope` partial）、started/completed actuals（分 l1/control/treatment/total）、仅失败标记、无性能聚合/门禁/终态，重抛可观测。
- [ ] **B11** CLI 守卫：缺旗→非零、零 calls、不创建；target SHA 与 HEAD (`2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`) 或 origin 分支任一不等→拒；四文件任一 SCOPED dirty（含 v35 替代旧 v45）→拒（J1）；输出根已存在→拒且不创建（J7，Tier 0）。
- [ ] **B12** 记录 schema 完备含 `target_tag/candidate_tag/tag_ok/tag_scope=l2_only/reclassified∈{exact,detected_verification_failure,decoder_non_syndrome_failure,undetected_accepted_wrong}` 与 `condition`/`h1_matrix_id`/`exact_l2/exact_u1/exact_full/bp_posterior_entropy`；`exact_full` 不经 tag（oracle）；译码参数断言：每记录 poly 37、90/1.0、无 warm-start 键、early-stop 冻结（J9）；control 先验 `Σ p_i P(U2|B,u1)`、treatment 先验 `Σ q_i P(U2|B,u1)`（`q_i=softmax decode(H1,p_i,s1).bp_posterior_beliefs`）；断言无 `x1_true` 进 candidate 路径。
- [ ] **B13** 写出合约：文件集精确（records 含 tag_ok/tag_scope/reclassified 四类、summary 含分层记账 27 + 四类聚合 + G3' `undetected==0` 明细）、CSV/JSON 行对等、已存在根 fail-closed（J7）、不写 NPZ、summary 含 `leakage_already_accounted` + 工程 verification L2-only 声名 + provenance 含 tag 源 `v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only`；并校验 `Control 984/1014/1024 vs Treatment 1064/1094/1104 (syndrome 920/950/960) f_total` 含 N；校验 `tag_match&&!exact` 为工程近似声名（非信息论界）且 `exact_full` oracle 声名。

## Phase C — preflight（decoder-free，授权前）

- [ ] **P1** 重建 H1 (QC 16×1024) + 三 L2 矩阵；与 committed 结构权威含 permutations/capacity/projective/rank 严格匹配；校验 `compute_tag_64` 可 import 且空前缀 `empty+x2` 可用、`hex[:16]` 长度、x1 不变/x2 敏感不变量通过；零求值器调用、零写盘。
- [ ] **P2** 在 390122/390222/390322 跑双条件绑定 preflight（treatment 侧 fake beliefs 通路校验 `p_i→s1→BP_fake→q_fake` + `v35_tag_import_ok`（L2-only） + `leakage_accounted` + `tag_scope_l2_only`）；仅报 PASS/BLOCKED；真实 `q≠p` 不在此 gate。
- [ ] **P3** 以拷贝八族 registries 机械校验 J2（78 零重叠、无重复、每源 3）并确认输出根缺席；仅报 PASS/BLOCKED。

## Phase D — 授权诊断执行（需 EXECUTE_AUTH，27 invocations，fresh-block）

- [ ] **D1** 主线程获独立 plan 再次 ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支、完整实现 SHA、cycle V46P0、scope `v46_diagnostic_27_invocations_with_verification_exactly_once`，HEAD `2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`）。
- [ ] **D2** 恰好一次：`python scripts/execute_v46_l1_app_with_verification.py --execution-authorized --authorized-target-sha <sha>`；27 invocations（9 L1 + 9 control L2 + 9 treatment L2），18 L2 records，每条 L2 含 `target_tag/candidate_tag/tag_ok/tag_scope/reclassified` 四类（L2-only `empty+x2`）；保留增量 run_01 文件；出错/partial 止、原样保留 raw partial 无性能聚合、返回 blocker；不 rerun/resume/repair/tuning/加块/改 seed/机制/加权重/重实现 canonical；无论结果如何不做第二轮诊断；执行期测量真实 `q≠p`/`iterations`/`entropy` 与 `tag_ok` 分流。
- [ ] **D3** 只读 postcheck：记账（planned 27 / l1 9 / control 9 / treatment 9 / total 27，除非完整性停止）、L2 记录数 18 与序 C01-C18 配对正确、L1 9 次、`tag_ok`/`tag_scope` 与四类计数完整、无 NPZ 写、V38-V45 输出 byte-identical、summary 完备（含分层记账与 exact/detected/decoder_non_syndrome/undetected + G3' `undetected==0`、L2-only 声名）、门禁与终态独立重算（含 `needs_1p5m_structure_branch` orthogonal 校验与 `Control vs Treatment f_total` 核验与工程 verification L2-only 声名）。

## Phase E — 结果复核

- [ ] **E1** 写 `OPERATOR_RETURN.md` 与 `DEVELOPMENT_RESULT.md` 候选；lifecycle 保持 result-candidate；含 terminal（V46 新命名）、路由轨迹、per-condition/per-source 四类聚合、配对结果、门禁明细（基于 `undetected==0` 新 G3'，L2-only）、`l1` 执行期诊断上下文（真实 `q≠p`/entropy/iterations/syndrome/tag_ok）及有界方向性分流（BOTH retained / control-only / both fail / treatment-only 四格冻结门禁判定 + orthogonal `needs_1p5m_structure_branch`）严格在 claim boundary 内（含 L2-only、工程近似与非等泄漏说明，不宣称信息论 2^-64，`exact_full` oracle）。
- [ ] **E2** 主线程/ reviewer 独立重算信号/机器/终态与四类计数；verdict 入 `REVIEW_VERDICT.md`。
- [ ] **E3** Memory triage 单独里程碑（本规划轮禁改 `AGENT_PROJECT_MEMORY.md`）；不启动 V47。

## 本变更期间显式禁止

plan 再次 ACCEPT 前实现；对 V45 18 条无 x_hat 记录重放 tag 或创建全 N/A 只读 run 或标记 `verification_not_applicable_missing_hash` 的零信息 run；重新实现 `canonical_bytes/tag_of` 或不复用 V35 `compute_tag_64` 或宣称 `compute_tag_64_symbols` 与空前缀调用等价；宣称固定公开 SHA-256 截断的信息论 `2^-64` 安全界（仅随机哈希模型工程近似，严格界需 universal2+seed）；把 `detected` 计为 exact 或把 `undetected` 静默为 success；保留旧 `structure_failure` 命名；保留旧 G3 `wrong_codewords==0`（应为 `undetected==0`）；新增 decoder/矩阵/参数网格/调参；加事后权重/C04；改写/覆盖 V45 输出或追溯改其终态；以非 accepted loader 读 NPZ；写任何 NPZ；复用历史块（78 seeds 含 V45 9）作样本；把 wrong 计为 exact；作条件/lane 优劣或比较排名；FER/阈值/SKR/安全/资格/晋升/真帧陈述；结果后加块/加 seeds/改阈值/改机制/加权重；rerun/resume/补偿 partial；任何结果下开第二轮诊断；任何结果下调 decoder 参数；把跨条件 outcome 差异判为完整性失败；自接受；自动启动后继（含 V47）；import v39/v40/v41/v42/v43/v44 模块作生产解码；**任何 `compute_tag_64(x1_true, x_hat)` 形态（含经 symbols 的 x1 依赖）**。
