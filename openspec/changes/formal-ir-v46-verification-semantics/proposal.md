# OpenSpec Proposal: formal-ir-v46-verification-semantics

**Status**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED` — **只规划、不实现、不执行、不启动 V47。修订后保持此状态，等待再次评审。**
**Domain**: Formal IR / verification semantics
**Change ID**: `formal-ir-v46-verification-semantics`
**Cycle ID**: `V46P0`
**Predecessor**: `formal-ir-v45-l1-app-soft-transfer` (PLAN_CANDIDATE, HEAD `fbfc35a5`) — V45 27-invocation 诊断；tag 仅记账未落地
**Investigation SHA**: `fbfc35a5ece95c35de8d897a7bf7200e0176c7a8`（修订锚点）
**Branch / HEAD**: `Placebo303/HD-QKD-Polar-pipeline` `formal-ir-mainline`, HEAD `fbfc35a5ece95c35de8d897a7bf7200e0176c7a8`（规划冻结时绑定，执行时精确重绑）
**Lifecycle**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`

> ponytail lite: 本轮修订前方案试图对 V45 已有 18 条无 x_hat 记录重放 tag，重分类只能得 `verification_not_applicable_missing_hash`，信息量接近零且会产生全 N/A 只读 run，已删除；更懒路径是沿用 exact oracle 判真不新增 verification。

## Goal

在**不改 V45 已有输出、不新增泄漏、不重新实现 tag 编码**的前提下，把 `+64 tag` 从纯记账补为**可执行的工程 verification**：**复用 V35 已有 `compute_tag_64 / compute_tag_64_symbols` 及其 canonical encoding**（`bytes(x1)+bytes(x2)` 拼接 → SHA-256 前 16 hex = trunc64，不重新实现 `canonical_bytes/tag_of`），在**下一次 fresh-block L1APP paired run（27 calls：L1 9 + Control L2 9 + Treatment L2 9，与 V45 同构）**中**实际生成 Alice target tag、重算 candidate tag、保存 `tag_ok`（`tag_hat==tag_true`），不必保存完整 `x_hat`**。验证语义为工程 verification（随机哈希模型下约 `2^-64` 近似），不宣称固定公开 SHA-256 截断的信息论 `2^-64` 安全界（严格界需 universal2 + seed 语义）。

单一科学问题（fresh-block 验证）：**Treatment 的 7/9 类增益能否在真实 verification acceptance（`tag_ok` gate）下复现**，以 `exact / detected_verification_failure / decoder_non_syndrome_failure / undetected_accepted_wrong` 四类可区分终态度量。

## Non-Goals

- 不对 V45 已有 18 条无 `x_hat` 记录做 tag 重放；**不创建全 N/A 只读 run**，不产生 `verification_not_applicable_missing_hash` 占位的零信息 run。
- 不重新实现 `canonical_bytes` / `tag_of` / 归一化；**直接复用 V35 `compute_tag_64 / compute_tag_64_symbols`** 的输入编码与截断（`b1+b2 → SHA256 → hex[:16]`，`symbols → (x1,x2) → compute_tag_64`）。
- 不新增 decoder / 矩阵 / 参数网格 / 调参 / 联合图 / 真帧 FER / 阈值 / SKR / 安全 / 资格 / 晋升陈述。
- 不改写/覆盖 V45 任何已有输出与终态（V45 仍保留原终态，只读）；V46 证据隔离新根。
- 不新增泄漏：64-bit 已计入 `leak_total = 5·m + 64`（Control 984/1014/1024，Treatment 1064/1094/1104），V46 不重复计费；`tag_ok==false` 计作非 exact/rejected frame。
- 不宣称固定公开 SHA-256 截断的信息论 `2^-64` 界；`tag_match && !exact ≈2^-64` 仅为随机哈希模型工程近似。
- 不启动 V47；不并行第二分支。

## Scope

1. **单一机制（复用 V35）**：`target_tag = compute_tag_64(x1_true,x2_true)`（Alice 侧生成，计泄漏 64 已含），`candidate_tag = compute_tag_64(x1_true, x_hat)` 或 `compute_tag_64_symbols(symbols_hat)` 等价路径，`tag_ok = (candidate_tag==target_tag)`；确定性、可重算；V46 不重新定义 canonical encoding。
2. **Fresh-block workload（27 invocations，18 L2 records + 9 L1）**：9 个全新 TRAIN 块（每源 3，后述 §Scope.4），每块 `L1 BP 1 + Control L2 1 + Treatment L2 1 =3`，共 `9×3=27` decoder invocations；L2 records 仍 18 条。沿用 V45 冻结：Control=`V43 P(U2|B)=Σ p_i P(U2|B,u1)`（零额外泄漏），Treatment=`Σ q_i P(U2|B,u1), q_i=softmax BP_posterior(H1,p_i,s1)`（额外 80-bit L1 syndrome）；H1 `16×1024 QC-cyclic-projective rank16` 复用，Lane C 三矩阵 ordinal-2 `lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302`，单点 `max_iter=90,damping_alpha=1.0,GF32 poly37,BP posterior beliefs / APP approximation, 冻结 early-stop`。
3. **Verification acceptance gate**：`decoder exact` 仍为成功判据门禁；`detected tag mismatch (tag_ok==false)` 计作**非 exact / rejected frame**，不计 exact；G3 改为 **`undetected_accepted_wrong ==0`**（`tag_ok==true && !exact` 的计数为 0），不要求 decoder 永不产生错误码字（`syndrome_ok && !exact` 仍可能出现，但被 gate 捕获为 detected 即不违规）。
4. **新 9 块预注册与 FORBIDDEN 78**：V36_A3(15) ∪ V39(15) ∪ V40probe(3) ∪ V41(9) ∪ V42(9) ∪ V43(9) ∪ V44(9) ∪ V45(9) = **78 seeds 已占用**；九枚新区与该并集零重叠、无内部重复、每源各 3（`390122-124 / 390222-224 / 390322-324`，为 V45 `390119-121/219-221/319-321` 之后连续三枚/源，具体见 design §3）。与 V45 同为连续 `390x` 递增约定。
5. **四类终态可区分**：每条 L2 记录与 per-condition/per-source 聚合分别报告 `exact` / `detected_verification_failure (syndrome_ok && !exact && !tag_ok)` / `decoder_non_syndrome_failure (!syndrome_ok && !exact)` / `undetected_accepted_wrong (tag_ok && !exact)`；`structure_failure` 更名为 `decoder_non_syndrome_failure`（`!syndrome_ok && !exact` 可能来自图/先验/迭代/BP 动力学，不单归因结构）。
6. **工程近似语义**：`tag_match && !exact` 的 `≈2^-64` 降为**随机哈希模型工程近似**，明确对固定公开 SHA-256 截断只能作此近似；若需严格 `2^-64` 需 universal2 + seed 语义，本轮不做。
7. **V45 冻结**：不追溯修改 V45，不重写其终态/结论/文件；V45 仍为纯记账态，V46 用 fresh blocks 回答“Treatment 7/9 增益能否在真实 verification acceptance 下复现”。

## Impact Scope

- **新增**：`openspec/changes/formal-ir-v46-verification-semantics/` 四工件（本轮仅此修订）。
- **未来实现（本轮不创建）**：`comparison_bench/src/comparison_bench/formal_ir/v46_verification_semantics.py`（仅组合 V45 L1APP 路径 + V35 tag 调用，不新增 decoder/矩阵/参数）+ `scripts/execute_v46_l1_app_soft_transfer_with_verification.py`（或复用 V45 runner 增 tag 路径）；均直接 import `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py::compute_tag_64,compute_tag_64_symbols`，不重新实现 canonical 编码。
- **只读依赖**：`comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`（tag 源）、`nonbinary_v31.py`（H1 构造）、`v38_architecture_triage.py`/`v35` 原语、V38 结构权威、V25 `channel_counts.npz` 经 `load_v25_channel_counts()`；V45 summary 仅作溯源引用。
- **不修改**：任何既有 spec/代码/测试/输出、V45 输出、`AGENT_PROJECT_MEMORY.md`、`docs/decision-log.md` 以外；不 import `v39/v40/v41/v42/v43/v44` 模块（仅模式拷贝）。

## Acceptance Criteria

- [ ] 四工件齐全一致且 lifecycle 为 `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`，HEAD `fbfc35a5ece95c35de8d897a7bf7200e0176c7a8` 绑定，明确“不实现不执行不启动 V47，等待再次评审”。
- [ ] 已删除基于缺失 `x_hat` 对 V45 18 条记录的 tag 重放方案，不创建全 N/A 只读 run。
- [ ] Tag 语义冻结为复用 V35 `compute_tag_64 / compute_tag_64_symbols`（`b1+b2 → SHA256 → hex[:16]` / `symbols → x1/x2 → compute_tag_64`），不重新实现 canonical 编码；fresh-block 中实际生成 `target_tag`、重算 `candidate_tag`、保存 `tag_ok`，不必保存完整 `x_hat`；泄漏已计 `984/1014/1024` 含 64，不重复计；SHA-trunc64 明确为工程 verification，不宣称信息论 `2^-64` 界（随机哈希模型近似，严格界需 universal2+seed）。
- [ ] 9 个新块与 FORBIDDEN 78 零重叠（V36_A3/V39/V40/V41/V42/V43/V44/V45 =78）已冻结且可机械校验（每源 3，连续 390122-124/222-224/322-324）。
- [ ] 区分四类 `exact / detected_verification_failure / decoder_non_syndrome_failure / undetected_accepted_wrong`；`structure_failure` 已更名为 `decoder_non_syndrome_failure`；G3 改为 `undetected_accepted_wrong==0`，detected mismatch 计作非 exact/rejected，不要求 decoder 永不产生错误码字。
- [ ] `tag_match && !exact ≈2^-64` 已降为工程近似并说明固定公开 SHA-256 截断的局限与 universal2 严格语义边界。
- [ ] `exact_l2` 仍为 oracle 判真，pre-tag 时序保留，verification 仅在其后追加 `tag_ok` gate；BP posterior beliefs / APP approximation、泄漏口径、J6 等冻结与 V45 一致。
- [ ] V45 未被追溯修改，V46 终态回答“Treatment 7/9 增益能否在真实 verification acceptance 下复现”而非重写 V45。

## Tasks

见 `tasks.md`（Phase A 冻结复用语义与 9 块/78 registry、Phase B 仅 fake-runner 聚焦测试含 tag_ok 分流与 G3 新语义、Phase C decoder-free preflight 含 V35 import 与 registry 校验、Phase D 需 EXECUTE_AUTH 的恰好 27 invocations fresh-block 含真实 tag 生成/比对、Phase E 结果复核；显式禁止清单含“禁止重放 V45 18 条、禁止重实现 canonical、禁止宣称信息论 2^-64”）。

## Lifecycle

V45 前代 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（`fbfc35a5`）；V46 当前 `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`，修订后仍保持此状态等待独立 plan 再次评审；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户 `EXECUTE_AUTH` 绑定到精确实现 SHA；不启动 V47。
