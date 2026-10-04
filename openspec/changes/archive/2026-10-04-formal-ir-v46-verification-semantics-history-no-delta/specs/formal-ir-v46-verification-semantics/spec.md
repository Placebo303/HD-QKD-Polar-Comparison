# Delta Specification: formal-ir-v46-verification-semantics

**Cycle**: `V46P0`
**Lifecycle**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V47。修订后保持此状态，等待再次评审。**
**Predecessor**: V45 `formal-ir-v45-l1-app-soft-transfer` (HEAD `2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`, tag 仅记账；V45 18 条记录无 x_hat)
**Investigation**: `2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`（`+64 tag` 仅记账 984/1014/1024；V45 18 条无 x_hat 重放仅得全 N/A 信息量接近零故删除；改为 fresh-block 复用 V35 `compute_tag_64` 的 27-call confirmation，V46-REV L2-only 空前缀）
**Mechanism id**: `l1_app_soft_transfer_H1_syndrome_derived_with_v35_tag_trunc64_l2_only`
**Tag source**: `v35:compute_tag_64(empty,x2)`（`empty=np.empty(0,dtype=np.uint8)`, `b1+b2 → SHA256 → hex[:16]` trunc64, `tag_scope=l2_only`）
**HEAD**: `2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`

## R1. Predecessor binding

V46 SHALL 仅基于 V45 证据与 V35 已有 tag 原语规划。V45 18 条记录未保存 `x_hat/hash`，SHALL NOT 对其重放 `tag_hat/tag_true`，SHALL NOT 创建标记 `verification_not_applicable_missing_hash` 的全 N/A 只读 run（信息量接近零）。V46 SHALL NOT 追溯改写 V45 终端/结论/输出，V45 仍保留原终态。V46 SHALL 为 fresh-block verification（27 invocations），回答“Treatment 7/9 增益能否在真实 verification acceptance 下复现”。V46 SHALL NOT 启动 V47，实现前需独立 plan 再次 ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支、实现 SHA、cycle V46P0、scope `v46_diagnostic_27_invocations_with_verification_exactly_once`，HEAD `2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`）。

## R2. Single mechanism — deterministic 64-bit L2-only verification via V35 reuse (engineering)

本变更 SHALL 仅实现单一机制：**复用 `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py::compute_tag_64`** 及其 canonical encoding（`bytes(x1)+bytes(x2) → SHA256 → hexdigest()[:16]`），SHALL NOT 重新实现 `canonical_bytes/tag_of` 或另行定义大小端/定长/截断，SHALL NOT 宣称 `compute_tag_64_symbols` 与空前缀调用等价（`symbols` 仅来源说明）。`tag_scope` SHALL 为 `l2_only`。Tag SHALL 已计入 `leak_total = 5·m + 64`（`L2+tag = 984/1014/1024`，含 L1 则 `1064/1094/1104`），V46 SHALL NOT 新增或重复计费，summary SHALL 显式声名 `leakage_already_accounted`。SHA-trunc64 SHALL 明确为**工程 verification（随机哈希模型下约 `2^-64` 近似，L2-only）**，SHALL NOT 宣称固定公开 SHA-256 截断的信息论 `2^-64` 安全界；spec/design/summary SHALL 说明对固定公开 SHA-256 截断只能作随机哈希模型近似，若需严格 `2^-64` 需 `universal2 + seed` 语义。**删除所有 `compute_tag_64(x1_true, x_hat)` 形态**。

## R3. Fresh-block workload — 27 invocations with real L2-only tag generation

Workload SHALL 为 **fresh-block 27 decoder invocations**（9 L1 + 9 Control L2 + 9 Treatment L2），18 L2 performance records；每条 L2 record 在解码后 SHALL 实际生成 `target_tag = compute_tag_64(empty_uint8, x2_true)`、重算 `candidate_tag = compute_tag_64(empty_uint8, x2_hat)`，其中 `empty_uint8 = np.empty(0, dtype=np.uint8)`，保存 `target_tag/candidate_tag/tag_ok=(candidate==target)/tag_scope=l2_only`，SHALL NOT 要求保存完整 `x_hat`（不必保存完整 `x_hat` 仍可验 acceptance）。**改变 `x1_true` SHALL NOT 改变 V46 L2 tag；改变 `x2` SHALL 改变测试锚点 tag**（测试不变量）。Control SHALL 为 V43 `P(U2|B)`（零额外泄漏），Treatment SHALL 为 `Σ q_i P(U2|B,u1)`（`q_i=softmax BP_posterior(H1,p_i,s1)`，额外 80 bits，H1 `16×1024 QC-cyclic rank16`，Lane C 三矩阵 ordinal-2 `383102/383202/383302`，`90/1.0 poly37 BP posterior beliefs / APP approximation 冻结 early-stop`；沿用 V45 O1 verbatim 与 D15 组合路径，仅在 L2 解码后追加 `compute_tag_64(empty,x2)` L2-only verification）。**Control 与 Treatment SHALL 使用完全相同的 L2 verification，不使用 `x1_true` 或共享 L1 decode**；64-bit 与当前 L2+tag 泄漏口径一致。SHALL NOT 重放 V45 已有 18 记录。

## R4. Source, leakage, and tag provenance — frozen via V35 L2-only

Tag 来源 SHALL 为 `x2` 经 V35 `compute_tag_64(empty, x2)` 的 canonical bytes（`empty` 为 `np.empty(0,dtype=np.uint8)`，`b1+b2` 拼接，hex[:16] 截断），SHALL 直接复用该函数，不另行归一化，不宣称 `compute_tag_64_symbols` 等价；泄漏 SHALL 已计（`920/950/960 +64 =984/1014/1024`，Treatment `1064/1094/1104`），与 `SOURCE_L2_TAG_BITS` 一致。`tag_scope` SHALL 恒为 `l2_only`。SHALL NOT 对缺 `x_hat` 的历史记录补造 tag，SHALL NOT 将 `x1_true` 置入 candidate。

## R5. Four-way reclassification — exact / detected / decoder_non_syndrome / undetected

`wrong_codeword = syndrome_ok && !exact` 仍为 LDPC 错误陪集解。Verification（L2-only）后 SHALL 四类互斥穷尽重分类：
- `exact` — `exact_l2==true`（必 `tag_ok==true`，否则非 exact）
- `syndrome_ok && !exact && !tag_ok → detected_verification_failure`（verification failure，主捕获路径，计为 rejected / 非 exact）
- `!syndrome_ok && !exact → decoder_non_syndrome_failure`（原 `structure_failure` 更名；`!syndrome_ok && !exact` 可能来自图/先验/迭代/BP 动力学，不单归因结构）
- `tag_ok && !exact → undetected_accepted_wrong`（概率约 `2^-64` 工程近似，下文 R7 G3'，单独计数 `undetected_accepted_wrong_count`）

`structure_failure` 命名 SHALL 替换为 `decoder_non_syndrome_failure`；`detected` SHALL 计作非 exact/rejected frame，不计 exact。

## R6. Oracle truth preserved — exact_l2 remains ground truth, exact_full oracle

`exact_l2` SHALL 仍为 oracle 判真（vs `u_true/x_true`），verification 的 `tag_ok`（L2-only）SHALL NOT 覆盖或重定义 `exact_l2`。Summary SHALL 同时报告 `exact_l2` 与 `verification_accept (tag_ok)`，且不得宣称提升 decoder exact rate。`tag_ok==false` 的记录 SHALL 计作非 exact。**本轮 tag 只验证 L2，不代表完整 `(U1,U2)` 帧验证；`exact_full = exact_u1 && exact_l2` SHALL 仍为 oracle development metric 单独报告，不经 tag**。

## R7. Pre-tag timing and G3' — undetected_accepted_wrong ==0

`wrong_codeword_l2 / exact_l2` SHALL 保持在 verification 之前计算（pre-tag 时序正确，沿用 V45），verification（L2-only `empty+x2`）仅在其后追加 `tag_ok` gate。时序后移即 invalid。

**G3' 新语义**：每条件臂的 G3' SHALL 为 **`undetected_accepted_wrong ==0`**（`tag_ok==true && !exact` 的计数为 0），SHALL NOT 要求 decoder 永不产生 `syndrome_ok && !exact` 错误码字 — `syndrome_ok && !exact && !tag_ok` 被捕获为 `detected_verification_failure` 时 G3' 仍可通过。G3' 仅 `undetected` 触发。

`tag_match && !exact ≈2^-64` SHALL 仅为随机哈希模型工程近似（L2-only），spec SHALL 说明固定公开 SHA-256 截断的局限与 `universal2+seed` 严格语义边界。

## R8. Outputs unchanged — V45 byte-identical, V35 tag source frozen L2-only

V46 SHALL NOT 修改任何 V45 已有输出；V45 `results/` 与 `comparison_bench/outputs_comparison/` 下既有文件 SHALL 保持 byte-identical（mismatch 即 `V46_EVIDENCE_INVALID`）。V46 证据 SHALL 隔离于新根 `comparison_bench/outputs_comparison/formal_ir_methods/v46_verification_semantics/run_01/`，fail-closed 若已存在。Tag 实现 SHALL 直接 import `v35_algorithm_development.compute_tag_64` 并以 `empty=np.empty(0,dtype=np.uint8)` 调用，SHALL NOT 另行实现 canonical encoding，不宣称 `compute_tag_64_symbols` 等价（import 失败或重实现或宣称等价即 J5/J9）。

## R9. Evidence outputs — minimal fixed set with tag_ok and four-way L2-only

授权写出 SHALL 仅为最小固定集：`v46_records.json/.csv`（18 行 fresh-block 记录，含 `target_tag/candidate_tag/tag_ok/tag_scope=l2_only/reclassified ∈ {exact,detected_verification_failure,decoder_non_syndrome_failure,undetected_accepted_wrong}`）、`v46_summary.json`（含四类计数 `exact / detected_verification_failure / decoder_non_syndrome_failure / undetected_accepted_wrong`、`undetected_accepted_wrong_count` 即 G3' 判定、`leakage_already_accounted` + 工程 verification L2-only 声名 `SHA-trunc64 random-hash-model approximate 2^-64, not information-theoretic; strict bound requires universal2+seed; tag_scope=l2_only`、provenance 含 tag 源 `v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only`、`exact_full` oracle 声名）、失败时 `v46_invalid_notice.json`；CSV/JSON 行对等；SHALL NOT 写任何 NPZ；输出根在全部守卫通过后创建。每条记录 SHALL 保存 `tag_ok` 与 `tag_scope`，SHALL NOT 要求保存完整 `x_hat`。

## R10. Terminal distinguishability — four-way + G3' L2-only

Summary 终态 SHALL 可区分四类 `exact / detected_verification_failure / decoder_non_syndrome_failure / undetected_accepted_wrong`，以正交 `reclassified` 与分层计数呈现；G3' 为 `undetected_accepted_wrong==0`（L2-only）。`V46_EVIDENCE_INVALID` 优先；V46 不重定义 V45 五终态，fresh-block 五终态 `V46_BOTH_RETAINED / V46_L1APP_NO_VALUE_OR_HARM / V46_GO_STRUCTURE / V46_L1APP_ADDED_VALUE_SIGNAL` 基于 `(control_pass, treatment_pass)` 在新 G3' 下判定。`exact_full` 不入终态（oracle 参照）。

## R11. Integrity, guard ordering, seed registry 78, and tiers

Runner SHALL 实现三层：
- **Tier 0 拒绝**（默认拒绝、必带 `--execution-authorized --authorized-target-sha`、HEAD 精确等值 `2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`、SCOPED tracked-dirty 四文件 `v46 模块/v46 CLI/v38 模块/v35 模块（含 tag 源）`、输出根已存在）最先、不创建文件、非零退出、零 calls。
- **Tier 1 预检失败**（J2 78 并集：V36_A3/V39/V40/V41/V42/V43/V44/V45 =78 零重叠，九枚 `390122-124/222-224/322-324`；J3 H1+L2 双重建；J4 counts；J5 哨兵含 `v35_tag_import_ok`（L2-only 空前缀 + x1 不变/x2 敏感）与 `tag_scope_l2_only`）任一失败 SHALL 建增量根写 invalid 三件套后停止，不 rerun；真实 `q≈p` 不作 invalid，`detected` 不作 invalid。
- **Tier 2 中途异常**（`BaseException`）在已建根内保留 raw partial（含 `tag_ok`/`tag_scope` partial）+ notice + summary 后重抛。

跨条件 outcome 差异永为信号，不作完整性失败；`tag_ok` 跨臂差异亦为信号。`errors_initial` 严格 per-pair 等值门（J6）保留。

## R12. Workload, seed registry, and stop rules

总预算 SHALL 为 27 decoder invocations（9 L1 + 9 Control L2 + 9 Treatment L2），18 L2 records 新块 `390122-124/222-224/322-324`（`C01-C18` 冻结序：源 1M/1p5M/2M、块升序、pair 内 `cond_control` 在前）。FORBIDDEN 78 机械零重叠校验 SHALL 在实现时通过（J2）。第 28 call SHALL 结构拒（J10）；恰好一次、无 rerun/resume。Master stop rule SHALL 原文记入 summary：`唯一一次 27-invocation 双条件配对诊断（含 9 L1 BP + 18 L2）fresh-block with V35 SHA-trunc64 L2-only engineering verification (compute_tag_64(empty,x2)[:16], tag_ok gate, tag_scope=l2_only, 4-way reclassified, G3'=undetected==0, 工程近似 2^-64, exact_full oracle)；对照为 V43 soft-marginal P(U2|B) vs Treatment Σ q_i P(U2|B,u1)；仅 Lane C 固定各 source ordinal-2 代表矩阵 + V31 H1 QC 16×1024、max_iter=90,damping 1.0 冻结 early-stop 不再调参；cond_l1_app 按冻结 syndrome-derived APP（p_i=P(U1|B)、s1=H1·u1^Alice、BP_i=decode(H1,p_i,s1).bp_posterior_beliefs / APP approximation、q_i=softmax BP_i、P_i(U2)=Σ q_i P(U2|B,u1)、泄漏 Control 984/1014/1024 vs Treatment 1064/1094/1104 f_total=leak/[N(H1+H2)] N=1024，复用 V35 tag 不重实现，不做 hard/噪声/量化/失真律/joint 迭代/新矩阵/新 decoder 参数/参数网格/joint GF1024，区分四类，不追溯 V45，不创建全 N/A 只读 run，Control/Treatment 同 L2 verification 不用 x1_true）后不再更改。`

## R13. Records preservation

每 L2 call SHALL 产一条 fresh-block 记录，共 18 条，schema 含 `condition/tag_ok/tag_scope/reclassified/target_tag/candidate_tag` 四类与 `iterations_l1/iterations_l2/exact_l2/exact_u1/exact_full/syndrome_ok/tag_ok/wrong`，其中 `tag_scope` 恒 `l2_only` 且 `target_tag/candidate_tag` 均为 `compute_tag_64(empty,x2)`。授权跑 SHALL 仅在增量根 `comparison_bench/outputs_comparison/formal_ir_methods/v46_verification_semantics/run_01/` 下写 `v46_records.json/.csv` + `v46_summary.json` + 失败时 `v46_invalid_notice.json`；SHALL NOT 写任何 NPZ；SHALL 保存 `tag_ok` 与 `tag_scope`，SHALL NOT 要求保存完整 `x_hat`。

## R14. Claim boundary

结果仅支持 V25 TRAIN 经验 counts 开发块上的有界条件归因：Control `P(U2|B)` vs Treatment `Σ q_i P(U2|B,u1)` 在固定 Lane C + H1 + V35 `compute_tag_64(empty,x2)[:16]` L2-only 工程 verification gate 下（`detected→rejected`，`undetected≈2^-64` 仅随机哈希模型工程近似，固定公开 SHA-256 截断不具信息论界；严格界需 universal2+seed；本轮 tag 只验证 L2，不代表完整 (U1,U2) 帧验证，`exact_full` 仍 oracle）。SHALL NOT 宣称信息论 `2^-64` 安全界、decoder exact rate 提升、FER/阈值/SKR/安全/正式资格/晋升、真帧行为、把同 `errors_final` 等同同码字。

## R15. Lifecycle

本变更 lifecycle SHALL 保持 `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED` 直至独立 plan 再次 ACCEPT；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。SHALL NOT 启动 V47。不追溯修改 V45。
