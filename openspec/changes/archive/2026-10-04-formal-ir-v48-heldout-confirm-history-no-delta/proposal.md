# OpenSpec Proposal: formal-ir-v48-heldout-confirm

**Status**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V49。等待独立评审。本修订为 V48 四工件最小修订，不进入实现。**
**Domain**: Formal IR / held-out confirmation
**Change ID**: `formal-ir-v48-heldout-confirm`
**Cycle ID**: `V48P0`
**Predecessor**: `formal-ir-v47-h1-redundancy-compression` (PLAN_CANDIDATE, 54-call 三臂 H1 前缀诊断, HEAD `4342e1a7dc4d0d84d83f5d374cb9b38cdefb0c24`, branch `formal-ir-mainline`) — V48 仅做数据调查结论的 held-out 复现，不改 V47 机制
**Investigation SHA / Branch / HEAD**: `4342e1a7dc4d0d84d83f5d374cb9b38cdefb0c24` / `formal-ir-mainline` (规划冻结时绑定，执行时 `git rev-parse` 精确重绑；V48 数据调查：held-out 1683 frames / 430k pairs 存在且零重叠 channel_counts)
**Lifecycle**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`
**Prior provenance**: V25 `channel_counts.npz` 仅由 TRAIN 构建；evaluation 块来自 held-out (split_manifest 60/20/20 hold 区间)
**Block budget**: **45 blocks（每源 15，均分）冻结唯一路径**，`BLOCK_LENGTH=1024` pairs = 连续 4 frames / block（每帧 256 pairs），**删除 30-block / 60-call 备案路径**

> ponytail lite: 本轮仅单候选 H1-16 + Lane C held-out 冻结复现；更懒路径是零新增执行直接引用 V47 TRAIN 块结论，需独立评审确认 held-out 增益是否值得 90-call 预算。

## Goal

在**完全冻结主候选 H1-16 (16×1024, 80 bits, 1064/1094/1104) + L1APP syndrome-derived BP posterior + Lane C ordinal-2 `90/1.0` + L2-only `compute_tag_64(empty,x2)` verification** 且**prior 始终 TRAIN-only** 的前提下，回答：

> **该主候选在未参与 `channel_counts.npz` 构建的独立 held-out 块上，能否以同等 `exact_full` 门禁复现 TRAIN 块的增益？**

单一变量是**评估数据源（TRAIN→held-out）**，不调参、不换矩阵、不换 decoder、不重估 prior，仅做 held-out 泛化确认。

## Non-Goals

- 不调任何译码/矩阵参数（`m1=16` 固定，Lane C 三矩阵 ordinal-2 冻结，`max_iter=90,damping_alpha=1.0,GF32 poly37` 冻结，L1APP 公式冻结，`tag_scope=l2_only` 冻结）。
- 不以 held-out 重估或更新 prior / `channel_counts` / `P(U1|B) / P(U2|B,u1)`；prior 始终只由 TRAIN `channel_counts.npz` 经 `load_v25_channel_counts()` 构建。
- 不新增 decoder / 矩阵 / 参数网格 / 联合图 / MET / 真帧 FER 外推 / 阈值 / SKR / 安全 / 资格 / 晋升陈述。
- 不改写/覆盖 V46/V47 任何已有输出与终态（只读）；V48 证据隔离新根。
- 不引入第二候选或多臂对比（仅单臂 H1-16 held-out，对照为 TRAIN 同候选历史结果，不在同 run 内重跑 TRAIN）。
- 不启动 V49；不并行第二分支；任何执行需独立 plan ACCEPT + 显式 `EXECUTE_AUTH`。
- 不对 V25 TRAIN counts 做任何 held-out 泄漏；不把 held-out block 用于训练或校准。
- **不保留 30-block / 60-call 备案路径**（本修订删除 24/30、7/10 阈值，仅保留 45-block / 90-call 冻结路径）。

## Scope

1. **冻结主候选（单臂）**：`H1-16 = V31-H1-QC-16×1024` (rank16, QC-cyclic-projective, GF32 poly37, 80 bits) + `L1APP` (`p_i(u1)=P(U1|B_i)` 来自 V25 TRAIN C；`s1=H1·u1^Alice`；`BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs` BP posterior / APP approximation, 冻结 early-stop；`q_i=softmax(BP_i)`；`P_i(U2)=Σ q_i(u1)·P(U2|B_i,u1)`) + `Lane C ordinal-2` 三矩阵 (`lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302`) `90/1.0` + `L2-only verification compute_tag_64(empty,x2)` (V35 `b1+b2→SHA256→hex[:16]` trunc64, `empty=np.empty(0,dtype=np.uint8)`, `tag_scope=l2_only`)。泄漏固定：`1064 (1M, 920+80+64) / 1094 (1p5M, 950+80+64) / 1104 (2M, 960+80+64)`，`f_total=leak/[N(H1+H2)] N=1024`，**不得调参**。
2. **Prior 隔离**：prior 始终只由 TRAIN `channel_counts.npz` 构建；evaluation blocks 来自 held-out frame 的确定性分散窗口（见 §4 与 design §3），**禁止用 held-out 重估 prior**（J4 校验 loader 来源为 TRAIN）。
3. **Held-out 块预算（冻结唯一路径）**：**45 blocks（每源 15，均分）冻结唯一路径**，库存 1683 frames / 430k pairs：1M 400 / 1p5M 554 / 2M 729 frames；连续 `block_seed` 390328+（每源均分，见 design §3）**仅作 block ID**，与此前 `FORBIDDEN 96 = 87 (V36_A3..V45+V46) + 9 (V47 390125-127/225-227/325-327)` **零重叠、无内部重复**。**删除 30-block 备案（10/源×3）及其 60-call 路径**。
4. **采样语义（唯一化）**：**禁止 `sample_empirical_block(held_out_pool, seed, 1024)` 随机抽取**；唯一采用**连续 4 帧拼成 1024 pairs（每帧 256 pairs 已确认）**的确定性窗口。**禁止取 hold 区间最前 60 帧**；采用覆盖整个 hold 区间的 **15 个分散不重叠窗口**：`start_j = floor(j * (H-4)/14), j=0..14`，每个 start 对应 `[start,start+3]` 四帧。`H` 为该源 hold 区间帧数（1M 400 / 1p5M 554 / 2M 729），对应起止见 design §3 明细表。原 `390128–142 / 390228–242 / 390328–342` **保留为 block ID，但不再作为随机 seed，必须逐一绑定上述 frame ordinal 窗口**（一一映射）。records 必须保存：四个 `frame_id`、held-out ordinal `start/end`、`pairs_count=1024`、`sampling_mode=deterministic_spread_four_consecutive_frames`。
5. **Workload（冻结唯一路径）**：每块 `L1 BP 1 + L2 1 =2` invocations；**45 块 → 90 decoder calls**（L1 45 + L2 45 records）。**删除 60-call 路径**。Summary 记录 `l1 / l2 / total` planned/completed/started actuals（唯一 45）。
6. **每块报告**：`exact_u1 / exact_l2 / exact_full (=exact_u1&&exact_l2, oracle)`、每源 `exact_full` 聚合、四类 `exact / detected_verification_failure / decoder_non_syndrome_failure / undetected_accepted_wrong`、`L1/L2 iterations/runtime`、`APP entropy / ||q-p||1 (=mean_abs_diff)` 分布、**固定泄漏 1064/1094/1104**、`tag_ok/tag_scope` verification acceptance（L2-only `compute_tag_64(empty,x2)`），以及本修订新增的 `frame_ids[4] / held_out_ordinal_start / held_out_ordinal_end / pairs_count / sampling_mode`。
7. **门禁（冻结唯一路径）**：参考 V47 `7/9≈77.8%` 与 `2/3≈66.7%`：
   - **45 块（15/源）冻结唯一门禁**：`G1: exact_full ≥35/45 (77.8%)`，`G2: 每源 exact_full ≥10/15 (66.7%)`，`G3': undetected_accepted_wrong==0`。等价 `≥78%` 绝对阈值（35/45=77.78% 临界，36/45=80% 更严，冻结为 35/45）。
   - **删除 30 块分支**：不再保留 `G1 ≥24/30 (80%)` / `≥23/30 (76.7%)` 与 `G2 ≥7/10` 算术。
   - 通过当且仅当 G1∧G2∧G3' 全满足；`L1 wrong` 单独报告不入 G3'；四类与 V46/V47 同构，`G3'=undetected==0`（`tag_ok&&!exact` 计数 0，随机哈希模型 `≈2^-64` 工程近似）。
8. **终态**：`V48_HELDOUT_PASS / V48_HELDOUT_FAIL / V48_EVIDENCE_INVALID`（单臂，无 first-match；EVIDENCE_INVALID 优先；`V48_HELDOUT_PASS` 当且仅当 G1∧G2∧G3' 通过）。
9. **Lifecycle**：`PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，`production_outputs_created=false`；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户 `EXECUTE_AUTH` 绑定到精确实现 SHA；**不启动 V49**。
10. **O3 配对语义**：同 block 内 `L1→L2` 同 prior (TRAIN)；held-out 样本仅作 L1 prior 输入的 `B_i` 与 L2 syndrome 真值来源；`errors_initial` 同块单值；跨块差异为诊断量。

## Impact Scope

- **新增**：`openspec/changes/formal-ir-v48-heldout-confirm/` 四工件（本轮仅此；本修订仅改四工件，不实现、不执行）。
- **未来实现（本轮不创建）**：`comparison_bench/src/comparison_bench/formal_ir/v48_heldout_confirm.py`（仅组合 V47 已验收 H1-16 + L1APP + Lane C + V35 tag L2-only，不新增 decoder/矩阵，TRAIN prior loader 隔离，采样改为确定性分散四帧窗口）+ `scripts/execute_v48_heldout_confirm.py`；均直接 import `v35_algorithm_development::compute_tag_64` 与 `nonbinary_v31::build_matrix_packet` + `v38_architecture_triage`。
- **只读依赖**：`v35_algorithm_development.py` (tag 源)、`nonbinary_v31.py` (H1)、`v38_architecture_triage.py` (Lane C 权威)、V25 `channel_counts.npz` TRAIN 经 `load_v25_channel_counts()`、`split_manifest.json` hold 区间定义、held-out frame 池（1683 frames / 430k pairs，1M 400 / 1p5M 554 / 2M 729）；V47 summary 仅溯源对照。
- **不修改**：任何既有 spec/代码/测试/输出、V46/V47 输出、`AGENT_PROJECT_MEMORY.md`、`docs/decision-log.md` 以外；不 import `v39..v47` 模块作生产解码（仅模式拷贝）。

## Acceptance Criteria

- [ ] 四工件齐全一致且 lifecycle 为 `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`（本修订）→ plan ACCEPT 后转为 `PLAN_CANDIDATE`，HEAD 绑定 `4342e1a7dc4d0d84d83f5d374cb9b38cdefb0c24`，明确“不实现不执行不启动 V49，等待独立评审”。
- [ ] 固定不变项冻结：`H1-16 (16×1024, 80 bits)` + `L1APP syndrome-derived BP posterior` 冻结公式 + `Lane C ordinal-2 90/1.0 GF32 poly37` + `L2-only verification compute_tag_64(empty,x2)` + 泄漏 `1064/1094/1104` (5·m2+5·m1+64, m2=184/190/192) + `f_total N=1024`，不得调参。
- [ ] Prior 隔离冻结：prior 始终只由 TRAIN `channel_counts.npz` 构建，evaluation blocks 来自 held-out 确定性分散窗口（4 frames=1024 pairs，按 `split_manifest` 60/20/20 hold 区间，`start_j=floor(j*(H-4)/14)`），禁止用 held-out 重估 prior（J4 可机械校验）；禁止 `sample_empirical_block(held_out_pool,seed,1024)` 随机抽取。
- [ ] Held-out 库存与块预算冻结：1683 frames / 430k pairs (1M 400 / 1p5M 554 / 2M 729) 对应 **唯一 45 blocks（每源 15）**，新 IDs `390328+` 连续每源均分，与 `FORBIDDEN 96 = 87+9(V47)` 零重叠、无内部重复、每源均分，连续性可机械校验；**已删除 30-block / 60-call 备案路径**。`H-4/14` 分散窗口表与一一映射可机械校验。
- [ ] Workload 冻结唯一路径：每块 `L1 1 + L2 1 =2`，**45 块→90 calls（L1 45 + L2 45 records）**，每块样本确定性一次（`deterministic_spread_four_consecutive_frames`），单臂无 TRAIN 重跑；records 必含 `frame_ids[4] / held_out_ordinal_start/end / pairs_count=1024 / sampling_mode`。
- [ ] 每块分别报告 `exact_u1/exact_l2/exact_full`、每源 `exact_full`、四类 `detected/decoder_non_syndrome/undetected`、`L1/L2 iterations/runtime`、`APP entropy/||q-p||1` 分布、固定泄漏、verification acceptance `tag_ok/tag_scope`，以及 `frame_ids / ordinal 窗口`。
- [ ] 门禁冻结唯一路径：等比于 V47 `7/9≈77.8%`，**45 块下 `exact_full ≥35/45` 且 `每源 ≥10/15` 且 `undetected==0`**；**30 块阈值 24/30、23/30、7/10 已删除**；`L1 wrong` 单独报告。
- [ ] 终态冻结：`V48_HELDOUT_PASS / V48_HELDOUT_FAIL / V48_EVIDENCE_INVALID`，互斥覆盖，EVIDENCE_INVALID 优先。
- [ ] `tag_scope=l2_only`、`compute_tag_64(empty,x2)` 空前缀复用、不重实现 canonical、`exact_full` oracle 不经 tag、`SHA-trunc64` 仅工程近似（`≈2^-64`，严格界需 universal2+seed）。

## Tasks

见 `tasks.md`（Phase A 冻结 H1-16/Lane C/prior 隔离/泄漏/门禁 35/45 与 96 隔离 + 确定性分散窗口一一映射、Phase B 仅 fake-runner 聚焦测试含 held-out 样本隔离与 90-call 与门禁 + sampling_mode/frame_ids 校验 + 禁止随机抽取、Phase C decoder-free preflight 含 TRAIN prior 与 held-out 分散窗口可达、Phase D 需 EXECUTE_AUTH 的恰好 90 invocations held-out fresh-block 确定性窗口、Phase E 结果复核；显式禁止清单含“禁止用 held-out 重估 prior、禁止调参、禁止多臂、禁止 V49、禁止 30-block 备案、禁止随机抽取 `sample_empirical_block(held_out_pool,seed,1024)`、禁止取 hold 前 60 帧”）。

## Lifecycle

V47 前代 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（`4342e1a7dc4d0d84d83f5d374cb9b38cdefb0c24`，branch `formal-ir-mainline`）；V48 当前 `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`，本四工件最小修订后仍保持不实现不执行、等待独立 plan 评审；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户 `EXECUTE_AUTH` 绑定到精确实现 SHA；不启动 V49。
