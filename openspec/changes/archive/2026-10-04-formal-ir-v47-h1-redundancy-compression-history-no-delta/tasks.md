# OpenSpec Tasks: formal-ir-v47-h1-redundancy-compression

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V48。等待独立评审。**
**Execution status**: 本轮不授权任何实现/执行；以下任务待独立 plan ACCEPT 后方可进入 A-phase；当前不跑 decoder，不写产出。V47-REV 冻结 H1 前缀 `8/12/16` 与 54-call 三臂。
**HEAD**: `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`

## Phase A — 语义冻结（plan ACCEPT 后）

- [ ] **A1** 冻结 H1 前缀与单变量语义：`H1-16=V31-H1 (16×1024,80b)` 母矩阵经 `nonbinary_v31.build_matrix_packet(m1=16,QC-cyclic-projective)` 确定性构造；`H1-12=H1_16[:12,:]` (12×1024,60b)；`H1-8=H1_16[:8,:]` (8×1024,40b)；`H1_8⊂H1_12⊂H1_16` 前缀嵌套、满行秩 `rank 8/12/16` 已验证（GF32 poly37）、`capacity_ok/projective_safe` 继承；单变量仅 `m1`，不改 Lane C L2、不改 `90/1.0`、不改 L1APP 公式与 L2-only verification；V47 不新增第二变量。
- [ ] **A2** 冻结 L1APP + verification 同构：`p_i=P(U1|B)` (V25 C `floor 1e-15`)、`s1^{m1}=H1^{m1}·u1^Alice`、`BP_i^{m1}=decode_row_layered_fftqspa(H1^{m1},p_i,s1^{m1}).bp_posterior_beliefs` (APP approximation, 冻结 early-stop)、`q_i^{m1}=softmax(BP_i^{m1})`、`P_i^{m1}(U2)=Σ q_i^{m1} P(U2|B,u1)`；`tag_scope=l2_only`，`compute_tag_64(empty_uint8,x2)` 空前缀复用 V35（`b1+b2→SHA256→hex[:16]`），不重实现 canonical，不宣称 symbols 等价；三臂均此形态，不使用 `x1_true` 进 candidate；SHA-trunc64 仅工程近似 `≈2^-64`，严格界需 universal2+seed。
- [ ] **A3** 冻结四类与门禁新语义：四类 `exact / detected_verification_failure (syndrome_ok&&!exact&&!tag_ok) / decoder_non_syndrome_failure (!syndrome_ok&&!exact) / undetected_accepted_wrong (tag_ok&&!exact, ≈2^-64)`；G3' 为 `undetected==0` 每臂；G1 `exact_full≥7/9`、G2 `每源 exact_full≥2/3`、`L1 wrong` 单独报告不入 G3'；`exact_full=exact_u1&&exact_l2` 为门禁主判据，同时报告 `exact_u1/exact_l2`；本轮 tag 只验 L2，`exact_full` oracle 不经 tag。
- [ ] **A4** 冻结 fresh-block 与隔离根：9 新块 `390125-127/390225-227/390325-327`（每源 3，x25-x27/源，见 design §3，与 FORBIDDEN 87 零重叠：78 + V46 9）；增量根 `comparison_bench/outputs_comparison/formal_ir_methods/v47_h1_redundancy_compression/run_01/` fail-closed；最小文件集含 `arm/h1_rows/target_tag/candidate_tag/tag_ok/tag_scope/reclassified/leak_total_this_arm` 四类；无 NPZ。
- [ ] **A5** 冻结 V46 边界：不追溯重放 V46 27-call 记录，不改 V46 终态/文件；V47 用 fresh 9 块验证 H1 压缩，对照是 `H1-16`，不再运行 V43 Control。
- [ ] **A6** 冻结其余同构常量：Lane C 三矩阵 ordinal-2、`90/1.0 poly37`、BP posterior beliefs / APP approximation、泄漏口径 `H1-8 1024/1054/1064 vs H1-12 1044/1074/1084 vs H1-16 1064/1094/1104 (5·m2+5·m1+64, f_total=leak/[N(H1+H2)] N=1024)`、J6 `errors_initial` 严格 per-block 三臂等值门、译码合约 90/1.0 early-stop。
- [ ] **A7** 冻结终态 first-match：五终态 `V47_H1_8_RETAINED / V47_H1_12_RETAINED / V47_H1_16_ONLY / V47_NO_H1_SIZE_RETAINED / V47_EVIDENCE_INVALID` 按 `8→12→16` 首个通过门禁者即终态；`V47_EVIDENCE_INVALID` 优先；orthogonal `needs_1p5m_structure_branch` 当且仅当 `h1_16 exact_full on 1p5M <2/3` 时立旗。

## Phase B — 聚焦测试（仅 fake runner/decode_fn；零生产解码）

- [ ] **B1** Seed-registry 校验：拒重复、错形状、分别与各族重叠（V36_A3 15、V39 15、V40 probe 3、V41 9、V42 9、V43 9、V44 9、V45 9 共78 + V46 9 共87）；接受冻结九枚 `390125-127/225-227/325-327`；校验新区连续 x25-x27/源且与 87 零重叠。
- [ ] **B2** H1 前缀重建匹配：H1 母矩阵 `16×1024` 与三前缀 `8/12/16` 分别注入 metric 漂移（含 `rank/capacity/projective/行前缀切片`）→ J 路径；三次重建一致；代表身份错→ J 路径；校验 `H1_8⊂H1_12⊂H1_16` 行前缀与 `rank 8/12/16`。
- [ ] **B3** Tag 复用与分流测试（L2-only 空前缀，三臂共享）：`compute_tag_64` 确定性、`hex[:16]` 长度、`v35_tag_import_ok`（仅 `compute_tag_64`）；不变性：改变 `x1_true` 不得改变任一臂 L2 tag；敏感性：改变 `x2` 必须改变锚点 tag；四类分流 per-arm：`syndrome_ok&&!exact&&!tag_ok→detected`、`!syndrome_ok&&!exact→decoder_non_syndrome`、`tag_ok&&!exact→undetected`、`exact→exact`；G3' 仅 `undetected==0` 触发。
- [ ] **B4** 哨兵与泄漏测试：每源首块 `390125/390225/390325` 三臂各六项/七项 fake-beliefs 通路 + `h1_prefix_ok`（`8⊂12⊂16` 秩/切片）+ `v35_tag_import_ok` + `tag_scope_l2_only` + `leakage_accounted`（`1024/1054/1064 vs 1044/1074/1084 vs 1064/1094/1104` 三臂区分，`leakage_already_accounted` 声名，工程 verification 声名 `SHA-trunc64 random-hash approx, L2-only`）+ `exact_full` oracle 声名（不经 tag）；校验 `leak_total =5·m2+5·m1+64` per arm；校验不重实现 `canonical_bytes` 且不宣称 symbols 等价。
- [ ] **B5** 配对一致性（三臂）：同 seed 重采样一致（样本算一次三臂共享）；缺/重 `block-arm` 组合→J6/J12；J6 严格门注入：篡改单臂 `errors_initial`→J6→`V47_EVIDENCE_INVALID` 且零 decoder calls；字段 `pairing_errors_initial_equal` 仍上报（需三臂等值）；跨臂 outcome 差异不判完整性失败；`tag_ok` 差异亦为诊断量。
- [ ] **B6** 真值表测试（first-match 三臂）：枚举 integrity ok/failed × `(pass_8,pass_12,pass_16)` 八格 {T**→V47_H1_8_RETAINED, FT*→V47_H1_12_RETAINED, FFT→V47_H1_16_ONLY, FFF→V47_NO_H1_SIZE_RETAINED}（T=pass, F=fail, *=任意）；各落且仅落一终态；`EVIDENCE_INVALID` 优先；穷尽互斥与 first-match 最小 `m1` 语义；另校验 orthogonal `needs_1p5m_structure_branch` 当且仅当 `h1_16 exact_full on 1p5M <2/3` 时为 true；校验四类计数完备与 G3' `undetected==0` per arm。
- [ ] **B7** Wrong/undetected 三态（基于新 G3' per arm）：(i) 单臂注入 `detected`→该臂 `stopped_for_analysis[arm]=true` 但 G3' 仍通过（`undetected==0`），他臂不受影响；(ii) 单臂注入 `undetected`→该臂 G3' 失败、`arm_undetected_anomaly[arm]=true`；(iii) 三臂各注入 `undetected`→各 G3' 失败→`V47_NO_H1_SIZE_RETAINED` 且各 stopped_for_analysis。无跨臂否决；first-match 按剩余 pass 计。
- [ ] **B8** 预算帽：fake 模式结构拒第 55 call（J10，总硬帽 54，区分 l1 27 / h1_8 9 / h1_12 9 / h1_16 9 / total 54）；planned/started/completed actuals 一致且分层记录；校验 `C01-C27` 顺序冻结（源 1M/1p5M/2M、块升序、臂 `h1_8→h1_12→h1_16`）。
- [ ] **B9** 科学 preflight 失败路径：J2/J3/J4/J5 各注入→建增量根、三件套（invalid notice、空 records、summary planned 54 / l1 27 / h1_8 0 / h1_12 0 / h1_16 0 / total 0、无聚合、terminal EVIDENCE_INVALID）且零 decoder calls。
- [ ] **B10** Partial 保留：注入中途 `BaseException`→预建根内原样保留 raw partial（含 `tag_ok/tag_scope/partial arm`）、started/completed actuals（分 l1/h1_8/h1_12/h1_16/total）、仅失败标记、无性能聚合/门禁/终态，重抛可观测。
- [ ] **B11** CLI 守卫：缺旗→非零、零 calls、不创建；target SHA 与 HEAD (`cb4f9990f7864e12dd69c89ee87ec8a58e77470d`) 或 origin 分支任一不等→拒；四文件任一 SCOPED dirty（含 v47 替代 v46/v35）→拒（J1）；输出根已存在→拒且不创建（J7，Tier 0）。
- [ ] **B12** 记录 schema 完备含 `arm/h1_rows/target_tag/candidate_tag/tag_ok/tag_scope=l2_only/reclassified∈{exact,detected,decoder_non_syndrome,undetected}/exact_u1/exact_l2/exact_full/bp_posterior_entropy/mean_abs_diff_q_p/leak_total_this_arm` per arm；`exact_full` 不经 tag（oracle）；译码参数断言：每记录 poly 37、90/1.0、无 warm-start 键、early-stop 冻结（J9）；每臂 `P_i^{m1}(U2)=Σ q_i^{m1} P(U2|B,u1)`（`q_i^{m1}=softmax decode(H1^{m1},p_i,s1^{m1}).bp_posterior_beliefs`）；断言无 `x1_true` 进 candidate。
- [ ] **B13** 写出合约：文件集精确（records 27 行含 tag_ok/tag_scope/reclassified/leak per arm、summary 含分层记账 54 + 四类三臂聚合 + G3' per arm + first-match 终态）、CSV/JSON 行对等、已存在根 fail-closed（J7）、不写 NPZ、summary 含 `leakage_already_accounted` + 工程 verification L2-only 声名 + provenance 含 `H1 prefix 8/12/16` 与 tag 源 `v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only`；并校验三臂泄漏 `1024/1054/1064 vs 1044/1074/1084 vs 1064/1094/1104` (syndrome 920/950/960, `f_total` 含 N) 与 first-match 声名；校验 `tag_match&&!exact` 为工程近似声名且 `exact_full` oracle 声名。

## Phase C — preflight（decoder-free，授权前）

- [ ] **P1** 重建 H1 母矩阵 `16×1024` + 三前缀 `8/12/16`；与 committed 结构权威含 `full_row_rank/capacity/projective` 严格匹配（秩 8/12/16 分别校验，`H1_8⊂H1_12⊂H1_16` 切片一致）；校验 `compute_tag_64` 可 import 且空前缀 `empty+x2` 可用、`hex[:16]`、x1 不变/x2 敏感通过；零求值器调用、零写盘。
- [ ] **P2** 在 `390125/390225/390325` 跑三臂绑定 preflight（三臂 fake beliefs 通路 `p_i→s1^{m1}→BP_fake^{m1}→q_fake^{m1}` + `h1_prefix_ok` + `v35_tag_import_ok` + `leakage_accounted` + `tag_scope_l2_only`）；仅报 PASS/BLOCKED；真实 `q≠p` 不在此 gate。
- [ ] **P3** 以拷贝 87 registries（78+V46 9）机械校验 J2（新区 9 与 87 零重叠、无重复、每源 3、连续 x25-x27）并确认输出根缺席；仅报 PASS/BLOCKED。

## Phase D — 授权诊断执行（需 EXECUTE_AUTH，54 invocations，fresh-block）

- [ ] **D1** 主线程获独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支 `formal-ir-mainline`、完整实现 SHA、cycle V47P0、scope `v47_diagnostic_54_invocations_h1_redundancy_exactly_once`，HEAD `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`）。
- [ ] **D2** 恰好一次：`python scripts/execute_v47_h1_redundancy_compression.py --execution-authorized --authorized-target-sha <sha>`；54 invocations（27 L1 + 27 L2: 每臂 9 L1 +9 L2），27 L2 records（每臂 9），每条 L2 含 `arm/h1_rows/target_tag/candidate_tag/tag_ok/tag_scope/reclassified` 四类（L2-only `empty+x2`）与 `exact_u1/exact_l2/exact_full/bp_posterior_entropy/mean_abs_diff_q_p/leak_total_this_arm`；保留增量 run_01 文件；出错/partial 止、原样保留 raw partial 无性能聚合、返回 blocker；不 rerun/resume/repair/tuning/加块/改 seed/机制/加权重/重实现 canonical；无论结果如何不做第二轮诊断；执行期测量真实 `q^{m1}≠p`/`iterations`/`entropy`/`||q-p||1` 与 `tag_ok` 分流 per arm。
- [ ] **D3** 只读 postcheck：记账（planned 54 / l1 27 / h1_8 9 / h1_12 9 / h1_16 9 / total 54，除非完整性停止）、L2 记录数 27 与序 C01-C27 三臂配对正确、L1 27 次、`tag_ok`/`tag_scope` 与四类计数完整 per arm、无 NPZ 写、V38-V46 输出 byte-identical、summary 完备（含分层记账与 exact/detected/decoder_non_syndrome/undetected + G3' `undetected==0` per arm、三臂 `exact_full`/`exact_u1`/`exact_l2`、first-match 终态、迭代/运行时/entropy/||q-p||1 per arm、L2-only 声名）、门禁与终态独立重算（含 `needs_1p5m_structure_branch` orthogonal 校验与三臂 `f_total` 核验与工程 verification 声名）。

## Phase E — 结果复核

- [ ] **E1** 写 `OPERATOR_RETURN.md` 与 `DEVELOPMENT_RESULT.md` 候选；lifecycle 保持 result-candidate；含 terminal（V47 新命名 first-match）、路由轨迹、三臂 per-arm/per-source 四类聚合与 `exact_full`/`exact_u1`/`exact_l2`、三臂配对结果、门禁明细（基于 `undetected==0` per arm，L2-only，`L1 wrong` 单独表）、`l1` 执行期诊断上下文（真实 `q^{m1}≠p`/entropy/iterations/||q-p||1/syndrome/tag_ok per arm）及有界方向性分流（`H1_8_RETAINED / H1_12_RETAINED / H1_16_ONLY / NO_H1_SIZE_RETAINED` 四格冻结门禁 first-match + orthogonal `needs_1p5m_structure_branch`）严格在 claim boundary 内（含 L2-only、工程近似与三臂非等泄漏 `1024/1054/1064 vs 1044/1074/1084 vs 1064/1094/1104` 说明，不宣称信息论 2^-64，`exact_full` oracle，H1 前缀 8/12/16）。
- [ ] **E2** 主线程/reviewer 独立重算信号/机器/终态与四类计数与 first-match；verdict 入 `REVIEW_VERDICT.md`。
- [ ] **E3** Memory triage 单独里程碑（本规划轮禁改 `AGENT_PROJECT_MEMORY.md`）；不启动 V48。

## 本变更期间显式禁止

plan ACCEPT 前实现；对 V46 27-call 记录重放 tag 或复用历史块（87 seeds 含 V46 9）作样本；重新实现 `canonical_bytes/tag_of` 或不复用 V35 `compute_tag_64` 或宣称 `compute_tag_64_symbols` 与空前缀调用等价；宣称固定公开 SHA-256 截断的信息论 `2^-64` 安全界（仅随机哈希模型工程近似，严格界需 universal2+seed）；把 `detected` 计为 exact 或把 `undetected` 静默为 success；保留旧 G3 `wrong_codewords==0`（应为 `undetected==0`）；新增 decoder/矩阵/参数网格/调参；加事后权重；改写/覆盖 V46 输出或追溯改其终态；以非 accepted loader 读 NPZ；写任何 NPZ；把 wrong 计为 exact；作跨臂优劣排名（仅 first-match 最小 `m1`）；FER/阈值/SKR/安全/资格/晋升/真帧陈述；结果后加块/加 seeds/改阈值/改机制/加权重；rerun/resume/补偿 partial；任何结果下开第二轮诊断；任何结果下调 decoder 参数；把跨臂 outcome 差异判为完整性失败；自接受；自动启动后继（含 V48）；import v39/v40/v41/v42/v43/v44/v45/v46 模块作生产解码；任何 `compute_tag_64(x1_true, x_hat)` 形态；**改 L2 矩阵或 `90/1.0` 或引入第二变量或运行 V43 Control 臂**。
