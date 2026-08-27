# Delta Specification: formal-ir-v48-heldout-confirm

**Cycle**: `V48P0`
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V49。等待独立评审。**
**Predecessor**: V47 `formal-ir-v47-h1-redundancy-compression` (PLAN_CANDIDATE, 54-call 三臂 H1 前缀, HEAD `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`, branch `formal-ir-mainline`)
**Investigation**: `cb4f9990f7864e12dd69c89ee87ec8a58e77470d` + V48 数据调查：held-out 1683 frames / 430k pairs (1M 400 / 1p5M 554 / 2M 729) 未参与 channel_counts 构建，prior TRAIN-only 隔离清晰，30–45 blocks 富余；主候选 H1-16 held-out 泛化确认
**Mechanism id**: `l1_app_soft_transfer_H1_16_syndrome_derived_with_v35_tag_l2_only_heldout`
**Tag source**: `v35:compute_tag_64(empty,x2)`（`empty=np.empty(0,dtype=np.uint8)`, `b1+b2 → SHA256 → hex[:16]` trunc64, `tag_scope=l2_only`）
**HEAD**: `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`（实现冻结时重绑）
**H1 provenance**: `V31-H1-QC-16×1024 (rank16, QC-cyclic-projective, GF32 poly37)` 冻结 80 bits
**Held-out provenance**: `split_manifest 60/20/20 hold` 区间 1683 frames / 430k pairs (1M 400 / 1p5M 554 / 2M 729)，评估块 4 frames=1024 pairs 拼接，`BLOCK_LENGTH=1024`

## R1. Predecessor binding

V48 SHALL 仅基于 V47 已验收 H1-16 主候选路径与 V35 tag 原语规划。V48 SHALL 冻结 `H1-16 (16×1024, 80 bits, 1064/1094/1104)` + L1APP 冻结公式 `p_i=P(U1|B), s1=H1·u1, q=softmax BP posterior, P_i(U2)=ΣqP(U2|B,u1)` + Lane C 三矩阵 ordinal-2 `90/1.0 poly37` + L2-only `compute_tag_64(empty,x2)` + V46/V47 四类与 `G3'=undetected==0` 不变。V48 SHALL NOT 改写 V46/V47 输出。V48 SHALL 为 held-out 单臂泛化确认（推荐 45 blocks, 90 invocations），回答“TRAIN prior 在 held-out 上能否复现同等 exact_full 门禁”。V48 SHALL NOT 启动 V49，实现前需独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支 `formal-ir-mainline`、实现 SHA、cycle V48P0、scope `v48_diagnostic_90_invocations_heldout_exactly_once` 或 60-call 备案，HEAD `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`）。

## R2. Single candidate — H1-16 frozen (no tuning)

本变更 SHALL 仅评估单一冻结候选：`H1-16 = V31-H1-QC-16×1024` (16×1024, rank16, QC-cyclic-projective, GF32 poly37, `capacity_ok/projective_safe/full_row_rank`)，`s1=H1·u1^Alice` 计泄漏 `5·16=80` bits。SHALL NOT 改 `m1`、不改 Lane C L2、不改 `90/1.0`、不改 decoder、不引入第二变量/第二候选。H1 物料 SHALL 经 `nonbinary_v31.build_matrix_packet(m1=16)` 确定性重建并与 committed 结构权威严格比对。

## R3. Held-out workload — 90 invocations single-arm with TRAIN-only prior and real L2-only tag

Workload SHALL 为 **held-out fresh-block 90 decoder invocations (推荐 45 blocks ×2 =90：每块 L1 BP 1 + L2 1)**，其中 L1 `45` 次、L2 `45` 条 records；备案 30 blocks 则 60 invocations (L1 30 + L2 30)。每块样本 SHALL 来自 held-out hold 区间（按 `split_manifest` 60/20/20），连续 4 frames 拼接为 1024 pairs，确定性采样一次；同块 L1 与 L2 同 `bob`；prior `p_i(u1)=P(U1|B_i)` 与 `P(U2|B,u1)` SHALL 始终仅由 TRAIN `channel_counts.npz` 经 `load_v25_channel_counts()` 构建，**禁止用 held-out 重估 prior**。每条 L2 record 在解码后 SHALL 实际生成 `target_tag=compute_tag_64(empty_uint8,x2_true)`、重算 `candidate_tag=compute_tag_64(empty_uint8,x2_hat)`（`empty=np.empty(0,dtype=np.uint8)`，复用 V35 `compute_tag_64` 的 `b1+b2→SHA256→hex[:16]`），保存 `target_tag/candidate_tag/tag_ok/tag_scope=l2_only/leak_total`，SHALL NOT 要求保存完整 `x_hat`。**改变 `x1_true` SHALL NOT 改变 L2 tag；改变 `x2` SHALL 改变锚点 tag**。单臂 held-out，无 TRAIN 重跑。

## R4. Source, leakage, and tag provenance — frozen single leakage with held-out evaluation

Tag 来源 SHALL 为 `x2` 经 V35 `compute_tag_64(empty,x2)` 的 canonical bytes（`empty=np.empty(0,dtype=np.uint8)`，`hex[:16]` 截断），直接复用该函数，不另行归一化，不宣称 symbols 等价；`tag_scope` 恒 `l2_only`。泄漏 SHALL 固定单点：`leak_total=5·m2+5·16+64`（`m2=184/190/192 →920/950/960`）：`H1-16: 1064 (1M) / 1094 (1p5M) / 1104 (2M)`；`f_total=leak_total/[N(H1+H2)] N=1024`。Summary SHALL 显式声名 `leakage_already_accounted` 与工程 verification L2-only；held-out 块不改变泄漏口径。

## R5. Four-way reclassification — exact / detected / decoder_non_syndrome / undetected (single arm)

`wrong_codeword = syndrome_ok && !exact` 仍为 LDPC 错误陪集解。Verification（L2-only）后 SHALL 单臂四类互斥穷尽重分类：
- `exact` — `exact_l2==true`（必 `tag_ok==true`）
- `syndrome_ok && !exact && !tag_ok → detected_verification_failure`（计为 rejected / 非 exact）
- `!syndrome_ok && !exact → decoder_non_syndrome_failure`（不单归因结构）
- `tag_ok && !exact → undetected_accepted_wrong`（`≈2^-64` 工程近似，下文 R7）

`detected` SHALL 计作非 exact/rejected，不计 exact。`L1 wrong`（`syndrome_ok_l1 && !exact_u1` / `!syndrome_ok_l1`）SHALL 单独报告，不入四类。

## R6. Oracle truth preserved — exact_full gate, tag L2-only, prior held-out isolated

`exact_l2` 与 `exact_u1` SHALL 仍为 oracle 判真（vs `u_true/x_true`），`exact_full=exact_u1&&exact_l2` 为门禁主判据，同时报告 `exact_u1/exact_l2/exact_full` 单臂与每源。Verification 的 `tag_ok`（L2-only）SHALL NOT 覆盖或重定义 `exact_*`。Summary SHALL 同时报告 `exact_*` 与 `verification_accept (tag_ok)`，不得宣称提升 decoder exact rate。`tag_ok==false` 的记录 SHALL 计作非 exact。**本轮 tag 只验 L2，不代表完整 (U1,U2) 帧验证；`exact_full` 仍 oracle，不经 tag。Prior 始终 TRAIN-only，held-out 仅作评估样本。**

## R7. Pre-tag timing and G3' — undetected_accepted_wrong ==0 (single arm, scaled gate)

`wrong_codeword_l2 / exact_l2` SHALL 保持在 verification 之前计算（pre-tag），verification（L2-only `empty+x2`）仅在其后追加 `tag_ok` gate。

**G3' 单臂**：`undetected_accepted_wrong==0`（`tag_ok&&!exact` 计数 0），SHALL NOT 要求 decoder 永不产生 `syndrome_ok&&!exact` — 被捕获为 `detected` 时 G3' 仍可通过。G3' 仅 `undetected` 触发。`tag_match&&!exact≈2^-64` 仅随机哈希模型工程近似（L2-only），spec SHALL 说明固定公开 SHA-256 截断局限与 `universal2+seed` 边界。门禁等比于 V47 `7/9≈77.8%` 与 `2/3≈66.7%`：

- **推荐 45 块 (15/源)**：`G1 exact_full≥35/45 (77.78%)` 且 `G2 每源≥10/15 (66.67%)` 且 `G3' undetected==0`（权威；`≥78%` 绝对阈值临界）
- **备案 30 块 (10/源)**：`G1≥24/30 (80%)` 且 `G2≥7/10 (70%)` 且 `G3'==0`（上取整；`≥23/30` 下取整需二选一时明确）

通过当且仅当三条全满足。

## R8. Outputs unchanged — V47 byte-identical, TRAIN prior isolated, held-out fresh

V48 SHALL NOT 修改任何 V47/V46 已有输出；既有 `results/` 与 `comparison_bench/outputs_comparison/` 下既有文件 SHALL 保持 byte-identical（mismatch 即 `V48_EVIDENCE_INVALID`）。V48 证据 SHALL 隔离于新根 `comparison_bench/outputs_comparison/formal_ir_methods/v48_heldout_confirm/run_01/`，fail-closed 若已存在。Tag 实现 SHALL 直接 import `v35_algorithm_development.compute_tag_64` 并以 `empty=np.empty(0,dtype=np.uint8)` 调用；H1 实现 SHALL 经 `nonbinary_v31.build_matrix_packet` 重建；prior SHALL 仅 `load_v25_channel_counts()` TRAIN，不触 held-out counts。

## R9. Evidence outputs — minimal fixed set with single-arm held-out tag

授权写出 SHALL 仅为最小固定集：`v48_records.json/.csv`（45 行 held-out 记录，30 块则 30 行，含 `target_tag/candidate_tag/tag_ok/tag_scope=l2_only/reclassified/exact_u1/exact_l2/exact_full/leak_total/iterations_l1/iterations_l2/bp_posterior_entropy/mean_abs_diff_q_p`）、`v48_summary.json`（含 per-source 四类计数 `exact/detected/decoder_non_syndrome/undetected`、`undetected` 即 G3'、`exact_full/ exact_u1/ exact_l2`、`leakage_already_accounted` 单臂 `1064/1094/1104` + `f_total` + 工程 verification L2-only 声名 `SHA-trunc64 random-hash-model approximate 2^-64, not information-theoretic; strict bound requires universal2+seed; tag_scope=l2_only; prior TRAIN-only, held-out evaluation`、provenance 含 `H1 16×1024` 与 tag 源 `v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only` + TRAIN/held-out 双溯源 1683/430k、门禁 35/45 与 10/15 权威、终态）、失败时 `v48_invalid_notice.json`；CSV/JSON 行对等；SHALL NOT 写任何 NPZ；输出根在全部守卫通过后创建。每条记录 SHALL 保存 `tag_ok/tag_scope`，SHALL NOT 要求保存完整 `x_hat`。

## R10. Terminal distinguishability — held-out PASS/FAIL with single-arm four-way

Summary 终态 SHALL 为：
- `V48_HELDOUT_PASS`（`G1∧G2∧G3'` 通过：推荐 45 块下 `≥35/45 && 每源≥10/15 && undetected==0`；30 块则对应阈值）
- `V48_HELDOUT_FAIL`（G1/G2/G3' 任一不满足）
- `V48_EVIDENCE_INVALID` 优先
三者互斥穷尽覆盖单臂 pass 平面。Summary SHALL 可区分四类 `exact/detected/decoder_non_syndrome/undetected` 与 `L1 wrong` 单独表，G3' 为 `undetected==0`（L2-only）。

## R11. Integrity, guard ordering, seed registry 96, and tiers

Runner SHALL 实现三层：
- **Tier 0 拒绝**（默认拒绝、必带 `--execution-authorized --authorized-target-sha`、HEAD 精确等值规划 HEAD、SCOPED tracked-dirty 四文件 `v48 模块/v48 CLI/v38 模块/v35 模块（含 tag 源）`、输出根已存在）最先、不创建文件、非零退出、零 calls。
- **Tier 1 预检失败**（J2 96 并集：87 (V36_A3/V39/V40/V41/V42/V43/V44/V45∪V46 9) + V47 9 =96，新区 45 (或 30) 零重叠 `390128-142/390228-242/390328-342` (或 390128-137/390228-237/390328-337) 连续每源均分；J3 H1 母矩阵 `16×1024` 秩校验；J4a TRAIN counts 溯源 + J4b held-out 池 1683/430k 可达/4 frames block；J5 哨兵含 `prior_train_only_ok` + `heldout_reachable_ok` + `v35_tag_import_ok`（L2-only）与 `tag_scope_l2_only` + `leakage_accounted` 单臂 1064/1094/1104）任一失败 SHALL 建增量根写 invalid 三件套后停止，不 rerun；真实 `q≈p` 不作 invalid，`detected` 不作 invalid。
- **Tier 2 中途异常**（`BaseException`）在已建根内保留 raw partial（含 `tag_ok/tag_scope` partial）+ notice + summary 后重抛。

跨块 outcome 差异永为信号，不作完整性失败；`tag_ok` 跨块差异亦为信号。`errors_initial` 严格 per-block 单值门（单臂）保留。**禁止用 held-out 重估 prior** 为硬门。

## R12. Workload, seed registry, and stop rules

总预算 SHALL 为 **推荐 90 decoder invocations（45 L1 +45 L2: 单臂 45 blocks）**，45 L2 records 新块 `390128-142/390228-242/390328-342`（`C01-C45` 冻结序：源 1M/1p5M/2M、块升序）；备案 30 块则 60 invocations (C01-C30)。FORBIDDEN 96 机械零重叠校验 SHALL 在实现时通过（J2）。第 91 call (或第 61 call @30 块) SHALL 结构拒（J10）；恰好一次、无 rerun/resume。Master stop rule SHALL 原文记入 summary：`唯一一次 90-invocation 单臂 H1-16 held-out 泛化确认（含 45 L1 BP +45 L2）fresh-block held-out (1683 frames / 430k pairs, 1M 400 / 1p5M 554 / 2M 729, 每 block 4 frames=1024 pairs 按 split_manifest hold 区间) with V35 SHA-trunc64 L2-only engineering verification (compute_tag_64(empty,x2)[:16], tag_ok gate, tag_scope=l2_only, 4-way reclassified, G3'=undetected==0 单臂, 工程近似 2^-64, exact_full=exact_u1&&exact_l2 oracle, 推荐 45 块 exact_full≥35/45 (77.8%) & 每源≥10/15 (66.7%) 等比于 7/9, 30 块备案 24/30 & 7/10)；单臂 H1-16 (16×1024, 80b, rank16 QC-cyclic-projective) + Lane C 各 source ordinal-2 代表矩阵 + max_iter=90,damping 1.0 冻结 early-stop 不再调参；L1APP 按冻结 syndrome-derived APP（p_i=P(U1|B) TRAIN-only、C floor 1e-15、s1=H1·u1^Alice、BP_i=decode(H1,p_i,s1).bp_posterior_beliefs / APP approximation、q_i=softmax BP_i、P_i(U2)=Σ q_i P(U2|B,u1)、泄漏单臂 1064/1094/1104 f_total=leak/[N(H1+H2)] N=1024，prior TRAIN-only 不触 held-out，复用 V35 tag L2-only 不重实现，不做 hard/噪声/量化/失真律/joint 迭代/新矩阵/新 decoder 参数/参数网格，区分四类单臂，L1 wrong 单独报告，不追溯 V47，不复用历史 96 块，对照为 TRAIN 同候选，不启动 V49）后不再更改。`

## R13. Records preservation

每 L2 call SHALL 产一条 held-out fresh-block 记录，共 45 条 (30 块则 30 条)，schema 含 `source/construction_seed/construction_seed_ordinal/block_seed/matrix_id/h1_matrix_id/max_iter/damping_alpha/errors_initial/errors_final/exact_l2/exact_u1/exact_full/syndrome_ok/tag_ok/tag_scope/reclassified/target_tag/candidate_tag/iterations_l1/iterations_l2/bp_posterior_entropy/mean_abs_diff_q_p/leak_total/status/runtime_s`，其中 `tag_scope` 恒 `l2_only` 且 `target_tag/candidate_tag` 均为 `compute_tag_64(empty,x2)`。授权跑 SHALL 仅在增量根 `comparison_bench/outputs_comparison/formal_ir_methods/v48_heldout_confirm/run_01/` 下写 `v48_records.json/.csv` + `v48_summary.json` + 失败时 `v48_invalid_notice.json`；SHALL NOT 写任何 NPZ；prior 溯源 TRAIN，评估块来自 held-out。

## R14. Claim boundary

结果仅支持 V25 TRAIN 经验 counts 上的 H1-16 + Lane C 90/1.0 + 通用 FFT-QSPA `q=softmax BP posterior / APP approximation` 真实 syndrome-derived 软转移在 held-out 块上的有界泛化归因：held-out 评估块来自 `split_manifest` hold 区间 1683 frames / 430k pairs (1M 400 / 1p5M 554 / 2M 729) 的连续 4 frames=1024 pairs 拼接，先验 `P(U1|B)/P(U2|B,u1)` 始终仅由 TRAIN `channel_counts.npz` 构建未用 held-out 重估（TRAIN-only prior），L2 在固定 Lane C 三矩阵 ordinal-2 上 90/1.0 单点、`leak_total 1064/1094/1104 (920/950/960+80+64, f_total, 工程 verification L2-only)`，复用 V35 `compute_tag_64(empty,x2)[:16]`，不改结构/阈值，`undetected≈2^-64` 仅随机哈希模型工程近似（固定公开 SHA-256 截断；严格界需 universal2+seed），单臂固定泄漏；均非真帧 FER 全集证据，不推阈值/SKR/正式执行/资格/晋升；终态仅方向性 held-out PASS/FAIL，不启动 V49。SHALL NOT 宣称信息论 `2^-64` 安全界、decoder exact rate 提升、FER/阈值/SKR/安全/正式资格/晋升、真帧全集行为、held-out 重估 prior 的增益。

## R15. Lifecycle

本变更 lifecycle SHALL 保持 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` 直至独立 plan ACCEPT；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。SHALL NOT 启动 V49。不追溯修改 V47。任何执行 SHALL 需显式用户 `EXECUTE_AUTH` 绑定到精确实现 SHA 与规划 HEAD。先创建四工件，不提交；`implementation_started=false`，`production_outputs_created=false`。
