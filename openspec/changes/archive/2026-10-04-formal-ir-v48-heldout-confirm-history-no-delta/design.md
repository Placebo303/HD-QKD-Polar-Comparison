# OpenSpec Design: formal-ir-v48-heldout-confirm

**Lifecycle**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V49。等待独立评审。本修订为四工件最小修订。**
**Cycle**: `V48P0`
**Predecessor**: V47 `formal-ir-v47-h1-redundancy-compression` (PLAN_CANDIDATE, 54-call 三臂, HEAD `4342e1a7dc4d0d84d83f5d374cb9b38cdefb0c24`, branch `formal-ir-mainline`)
**Investigation anchor**: `4342e1a7dc4d0d84d83f5d374cb9b38cdefb0c24` + V48 数据调查结论：独立 held-out 1683 frames / 430k pairs (1M 400 / 1p5M 554 / 2M 729) 未参与 `channel_counts.npz` 构建，prior TRAIN-only 隔离清晰，45 blocks 冻结唯一路径
**HEAD**: `4342e1a7dc4d0d84d83f5d374cb9b38cdefb0c24`（实现冻结时 `git rev-parse` 精确重绑）
**Feasibility**: held-out 库存富余、TRAIN prior 隔离可验证、Lane C 三矩阵冻结、H1-16 物料复用、90-call(45×2) 冻结唯一预算、每帧 256 pairs 已确认

## 1. 科学问题（单一，held-out 泛化确认）

> 在固定主候选 **H1-16 (16×1024, 80 bits) + L1APP syndrome-derived `q=softmax BP posterior` + Lane C ordinal-2 `90/1.0` + L2-only `compute_tag_64(empty,x2)` verification + 泄漏 1064/1094/1104** 且 **prior 始终 TRAIN-only** 下，**该候选在独立 held-out 块上的 `exact_full` 能否以同等门禁复现 TRAIN 块增益？**

- 前代 V47 在 TRAIN 开发块上以三臂 `H1-8/12/16` 诊断 H1 冗余；V48 不改任何机制，仅将评估数据源切换为 **held-out 确定性分散窗口**，考验 TRAIN 经验 prior 的泛化能力。
- 若 held-out 通过门禁，则 TRAIN prior 未过拟合 held-out 分布，增益可外推；若不通过则为数据源/分布敏感性信号，转结构/先验校准诊断。
- V48 不回答“是否可压缩 H1/L2”或“是否可换 decoder/图”，仅回答 held-out 泛化。

## 2. 冻结语义（沿用 V47 主候选，仅评估数据源可变）

### 2.1 固定不变项（不得调参）

| 项 | 冻结值 | 来源 |
|---|---|---|
| H1 母矩阵 | `V31-H1-QC-16×1024` (16×1024, rank16, QC-cyclic-projective, GF32 poly37) | V31/V47 权威 |
| L1APP 公式 | `p_i(u1)=P(U1|B_i)` (V25 TRAIN C, floor 1e-15), `s1=H1·u1^Alice`, `BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs` (APP approx, 冻结 early-stop), `q_i=softmax(BP_i)`, `P_i(U2)=Σ q_i P(U2|B,u1)` | V45/V46/V47 O1 |
| Lane C L2 矩阵 | `lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302` ordinal-2 | V38/V47 权威 |
| L2 译码 | `max_iter=90, damping_alpha=1.0, GF32 poly37, row_layered FFT-QSPA, 冻结 early-stop` | V43/V47 |
| Verification | `tag_scope=l2_only`, `compute_tag_64(empty_uint8, x2)` (`b1+b2→SHA256→hex[:16]` trunc64), `empty=np.empty(0,dtype=np.uint8)`, `tag_ok=(candidate==target)` | V35/V46/V47 |
| 四类/G3' | `exact / detected_verification_failure / decoder_non_syndrome_failure / undetected_accepted_wrong`, `G3': undetected==0` | V46/V47 |
| APP 语义 | `bp_posterior_beliefs` 为 APP approximation 非精确 APP | V45/V47 |

- **单臂**：仅 `H1-16`，不含 `H1-8/12` 压缩臂；对照为 TRAIN 同候选历史结果，不在同 run 内重跑 TRAIN。
- `L1 wrong` 单独报告，不入 G3'。

### 2.2 Prior 隔离（核心冻结）

- **TRAIN-only prior**：`channel_counts.npz` 仅由 TRAIN 60% 区间构建（`split_manifest.json` 60/20/20：TRAIN / VAL / HELD-OUT hold），经 `load_v25_channel_counts()` 加载；V48 evaluation blocks 来自 **held-out 20% hold 区间**的帧池（1683 frames：1M 400 / 1p5M 554 / 2M 729，430k pairs），**禁止用 held-out 重估 prior**（J4 校验 loader 来源与 counts 溯源为 TRAIN）。
- **Evaluation 块定义（唯一化）**：**禁止 `sample_empirical_block(held_out_pool, block_seed, 1024)` 随机抽取**；每 block = held-out 区间内**连续 4 frames = 1024 pairs（每帧 256 pairs 已确认）按确定性分散窗口拼接**（按 `split_manifest` hold 帧序，`start_j = floor(j*(H-4)/14), j=0..14`），`BLOCK_LENGTH=1024` pairs，`pair_idx` 连续；`block_seed`（390128–142 等）**仅作 block ID，不再作为随机 seed**，必须逐一绑定窗口（§3）。records 必须保存 `frame_ids[4] / held_out_ordinal_start / held_out_ordinal_end / pairs_count=1024 / sampling_mode=deterministic_spread_four_consecutive_frames`。
- **跨区间隔离**：TRAIN 与 held-out 帧键零重叠（由 `split_manifest` 保证），counts 构建与评估样本双重隔离；实现中以 `load_v25_channel_counts()` 权威隔离校验。
- **禁止路径**：禁止取 hold 区间最前 60 帧作评估；禁止任何随机池抽取；禁止将 held-out counts 用于 prior。

### 2.3 泄漏（单候选固定）

`leak_total = 5·m2 + 5·m1 + 64`，`m1=16→80`，`m2 ∈ {184,190,192}` (920/950/960)：

| candidate | m1 | 1M (m2=184) | 1p5M (m2=190) | 2M (m2=192) |
|---|---|---|---|---|
| H1-16 (frozen) | 16 | **1064** (920+80+64) | **1094** (950+80+64) | **1104** (960+80+64) |

`f_total = leak_total / [N·(H1+H2)] N=1024`；单泄漏点比较，无压缩臂非等泄漏对比。

### 2.4 时序与四类（V46/V47 同构，单臂）

```
TRAIN prior: C(a,b) (TRAIN counts) → P(U1|B), P(U2|B,u1)
held-out block (deterministic 4 consecutive frames → 1024 pairs, sampling_mode=deterministic_spread_four_consecutive_frames):
  p_i(u1)=P(U1|B_i) ──┐
  s1=H1(16×1024)·u1^Alice ─→ decode(H1, p_i, s1) → q_i=softmax BP → P_i(U2)=Σ q_i P(U2|B,u1)
                                                      ↓
                         syndrome_of_gf32(H_L2(该源 lane_c), u2_alice) → decode_row_layered_fftqspa(H_L2, P_i(U2), syndrome) → exact_l2/syndrome_ok/wrong/iterations/runtime
                                                      ↓
                         verification L2-only: target=compute_tag_64(empty,x2_true); candidate=compute_tag_64(empty,x2_hat); tag_ok=(candidate==target)
                                                      ↓
                         reclassified: exact / detected / decoder_non_syndrome / undetected (G3' undetected==0)
```

`exact_full = exact_u1 && exact_l2` oracle，不经 tag；`exact_u1` 来自 `argmax q_i`。

## 3. 冻结样本集（held-out，45 blocks 冻结唯一路径，确定性分散窗口）

库存：**1683 frames / 430k pairs**，未参与 `channel_counts.npz` 构建：

| source | held-out frames H | 估算 blocks (4 frames/block) | 冻结 15 blocks |
|---|---|---|---|
| 1M | 400 | 100 | 15 |
| 1p5M | 554 | 138 | 15 |
| 2M | 729 | 182 | 15 |
| **合计** | **1683** | **~420** | **45** |

**冻结唯一路径：45（每源 15，均分）**，连续 `block_seed` **390328+ 每源均分仅作 block ID**：

| source | 15 block IDs (x28–x42, 连续，仅作 ID) | 对应 held-out ordinal 窗口 `[start, start+3]` (H 决定) |
|---|---|---|
| 1M (H=400) | **390128, 390129, …, 390142** (15) | 0,28,56,84,113,141,169,198,226,254,282,311,339,367,396 各起 4 帧 |
| 1p5M (H=554) | **390228, 390229, …, 390242** (15) | 0,39,78,117,157,196,235,275,314,353,392,432,471,510,550 各起 4 帧 |
| 2M (H=729) | **390328, 390329, …, 390342** (15) | 0,51,103,155,207,258,310,362,414,466,517,569,621,673,725 各起 4 帧 |

- **确定性分散窗口公式**：`start_j = floor(j * (H-4)/14), j=0..14`，每窗口 `[start_j, start_j+3]` 四帧连续、**15 窗口互不重叠**且覆盖整个 hold 区间（非仅前 60 帧）。每帧 256 pairs → 每窗口 `4×256=1024` pairs。
- **一一映射**：`390128↔1M start 0、390129↔1M start 28、…、390142↔1M start 396`；1p5M 与 2M 同理按上表顺序绑定。**block ID 不得再作随机 seed**。
- **禁止路径**：禁止 `sample_empirical_block(held_out_pool, seed, 1024)`；禁止取 hold 最前 60 帧；禁止随机打散或跨窗口重叠采样。
- **FORBIDDEN 96** = 87 (V36_A3 15 + V39 15 + V40 3 + V41 9 + V42 9 + V43 9 + V44 9 + V45 9 + V46 9) + V47 9 (390125-127/225-227/325-327) = **96 seeds**，新区 45 与该并集**零重叠、无内部重复、每源均分、连续**（P3/J2 机械复验）。
- **30-block 备案已删除**：不再保留 `390128–137 / 390228–237 / 390328–337` 10/源×3 及其 60-call 算术。

**明细（逐 ID→窗口，供 J2/J4b 机械校验）**：

- 1M (H=400): 390128→[0,3], 390129→[28,31], 390130→[56,59], 390131→[84,87], 390132→[113,116], 390133→[141,144], 390134→[169,172], 390135→[198,201], 390136→[226,229], 390137→[254,257], 390138→[282,285], 390139→[311,314], 390140→[339,342], 390141→[367,370], 390142→[396,399]
- 1p5M (H=554): 390228→[0,3], 390229→[39,42], 390230→[78,81], 390231→[117,120], 390232→[157,160], 390233→[196,199], 390234→[235,238], 390235→[275,278], 390236→[314,317], 390237→[353,356], 390238→[392,395], 390239→[432,435], 390240→[471,474], 390241→[510,513], 390242→[550,553]
- 2M (H=729): 390328→[0,3], 390329→[51,54], 390330→[103,106], 390331→[155,158], 390332→[207,210], 390333→[258,261], 390334→[310,313], 390335→[362,365], 390336→[414,417], 390337→[466,469], 390338→[517,520], 390339→[569,572], 390340→[621,624], 390341→[673,676], 390342→[725,728]

每窗口四帧的 `frame_id` 与 `held_out_ordinal_start/end`、`pairs_count=1024`、`sampling_mode=deterministic_spread_four_consecutive_frames` 必须写入每条 record。

## 4. 冻结 workload（90 invocations @45 blocks，单臂，冻结唯一路径）

**预算（冻结唯一）**：每块 `L1 BP 1 + L2 1 =2` invocations，共 **45×2=90 decoder invocations**；L2 records **45 条**，L1 invocations **45 次**。Summary 记录 `l1=45 / l2=45 / total=90`（planned/completed/started actuals）。**删除 60-call 路径**。

| call | source | block ID (非随机 seed) | held-out ordinal 窗口 | H1 | matrix_id (lane_c) |
|---|---|---|---|---|---|
| C01 | 1M | 390128 | [0,3] | H1_16 (16×1024) | lane_c_1M_s383102 |
| C02 | 1M | 390129 | [28,31] | H1_16 | lane_c_1M_s383102 |
| … | 1M | … | … | … | … |
| C15 | 1M | 390142 | [396,399] | H1_16 | lane_c_1M_s383102 |
| C16 | 1p5M | 390228 | [0,3] | H1_16 | lane_c_1p5M_s383202 |
| … | 1p5M | … | … | … | … |
| C30 | 1p5M | 390242 | [550,553] | H1_16 | lane_c_1p5M_s383202 |
| C31 | 2M | 390328 | [0,3] | H1_16 | lane_c_2M_s383302 |
| … | 2M | … | … | … | … |
| C45 | 2M | 390342 | [725,728] | H1_16 | lane_c_2M_s383302 |

另有 45 次 L1 invocations（L1-01..L1-45，与上表 C01-C45 一一对应），总计 90。

L2 records 顺序冻结：源 1M→1p5M→2M，块升序。去重得 **3 枚唯一 L2 矩阵** + **1 枚 H1 母矩阵**；成员/顺序漂移即 J12。

## 5. 代表矩阵与译码合约（冻结，单臂）

- **Lane C ordinal-2 / source**：`lane_c_1M_s383102`、`lane_c_1p5M_s383202`、`lane_c_2M_s383302`（以 committed v38 模块常量表校验）。
- **H1 母矩阵**：`V31-H1-QC-16×1024`（`m1=16, n=1024, family=QC-cyclic-projective, GF32 poly37, rank16, capacity_ok, projective_safe, full_row_rank`）。
- **译码合约**：90 invocations 共享 `GF32 poly37, max_iter=90, damping_alpha=1.0, syndrome from true u_alice / s1=H1·u1^Alice, success primary = exact_full (=exact_u1&&exact_l2) 门禁，同时报告 exact_u1/exact_l2/exact_full, decoder = 通用 decode_row_layered_fftqspa(H,prior,syndrome).bp_posterior_beliefs (BP posterior / APP approximation, 冻结 early-stop)`。
- **O1 机制**：`P_i(U2)=Σ q_i P(U2|B_i,u1)`，`q_i=softmax BP_i(H1,p_i,s1)`，`p_i(u1)=P(U1|B_i)` 来自 V25 TRAIN C，`f_total` 含 N。
- **D15 组合路径**：`deterministic_spread_four_consecutive_frames(held_out_frame_pool, ordinal_start, 4)→ factorize_f03 → L1 p_i→s1→BP_i→q_i → P_i(U2)` → `syndrome_of_gf32(H_L2,u2_alice)` → `decode_row_layered_fftqspa` + `compute_tag_64(empty,x2)` L2-only verification，`decode_fn` 可注入。**禁止 `sample_empirical_block(held_out_pool, seed, 1024)` 路径**。
- **V35 复用点**：`target_tag/candidate_tag/tag_ok` 在每条 L2 记录解码后立即计算（`empty+x2` L2-only）；`tag_ok==false` 即 `detected`，`tag_ok==true && !exact` 即 `undetected`。

## 6. 门禁（冻结唯一路径，单臂，G3' undetected==0）

对单候选 H1-16，以其 **45 条 L2 records** 判定，参考 V47 `7/9≈77.78%` 与 `2/3≈66.67%`：

**45 块（15/源）— 冻结唯一门禁**：

- G1：overall `exact_full ≥ 35/45` (77.78%，等比 `7/9×45=35`，`≥78%` 绝对阈值临界)
- G2：每源 `exact_full ≥ 10/15` (66.67%，等比 `2/3×15=10`)
- G3'：`undetected_accepted_wrong ==0` (`tag_ok==true && !exact_l2` 计数 0)

**删除 30 块备案算术**（原 `≥24/30` / `≥23/30` / `≥7/10` 均删除）。

通过当且仅当 G1∧G2∧G3' 全满足。`detected_verification_failure` 不触发 G3'；`L1 wrong` 单独报告。按比例与绝对阈值（`≥78%`）均满足时通过，算术以 **35/45 与 10/15** 为权威。

同时报告：`exact_u1 / exact_l2 / exact_full` 总量与每源、四类计数、`L1/L2 iterations/runtime`、`APP entropy / ||q-p||1`。

## 7. 终态机（单臂，互斥；EVIDENCE_INVALID 优先）

三终态（总量互斥，覆盖单臂 pass 平面）：

```text
0. 任意完整性/执行失败 -> V48_EVIDENCE_INVALID
1. pass == true  (G1∧G2∧G3' 全满足) -> V48_HELDOUT_PASS
2. else -> V48_HELDOUT_FAIL
```

其中 `pass = (exact_full≥35/45 && 每源≥10/15 && undetected==0)` @45 块。Summary 终态下区分四类计数与 G3' 判定，`L1 wrong` 单独表。

Wrong 处理：`detected_verification_failure` 并置 `stopped_for_analysis=false` 仅通过 G3' 体现（`undetected==0` 仍可通过）；`undetected` 立旗 `undetected_anomaly=true` 且 G3' 失败。

orthogonal 标志：`needs_heldout_structure_branch` 当且仅当 held-out `exact_full <35/45` 或某源 `<10/15` 时立旗（独立于终态，仅作后继诊断提示）。

## 8. O3 配对语义（单臂 held-out，确定性窗口）

- 同 `block ID` 的 held-out 样本 `(idx, alice, bob)` 每块算一次（确定性四帧窗口 `frame_ids[4]`），L1 与 L2 同 `bob`/`counts`（TRAIN prior）；每块 L1 `s1/q_i` 单值。
- 同 H_L2（该源 lane_c ordinal-2）、同设置 90/1.0、同域/多项式、同 L2 syndrome；`P_i(U2)` 由 held-out `B_i` 与 TRAIN prior 结合。
- 跨块残差差异（`errors_final/iterations/exact_full/syndrome_ok/tag_ok/wrong`）是诊断量本身，永不作完整性失败。
- `exact_full` 与 `exact_l2/exact_u1` 同时记录；`exact_u1` 来自 L1 hard decision（`argmax q_i`）。
- 完整性检查：J2/J3/J4/J5/J6/J8-J12 与 V47 同构，仅将 87→96（87 + V47 9）、预算 54→90 冻结唯一、单臂终态、三源 held-out 分散窗口可达校验。

## 9. 科学 preflight、守卫序、证据分层

守卫序冻结（沿用 V47 §9–§11，更新 90-call 冻结唯一与 held-out 确定性窗口与 TRAIN prior 隔离）：

1. **拒绝类守卫最先、建目录前**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `git rev-parse origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定规划 HEAD `4342e1a7dc4d0d84d83f5d374cb9b38cdefb0c24`；四文件 SCOPED tracked-dirty 检查（v48 模块、v48 CLI、v38_architecture_triage.py、v35_algorithm_development.py（含 tag 源））；输出根已存在即拒（J7）；任一拒绝非零退出、零 calls、不创建任何文件。
2. **科学 preflights（decoder-free、write-free）**：seed-registry 校验（J2，96 并集：87 + V47 9，新区 45 零重叠 per source 连续 x28+，且一一映射到分散窗口）；H1 母矩阵 `16×1024` 确定性重建并与 committed 结构权威严格比对含 `full_row_rank/capacity/projective`（J3；秩 16 校验）；两类 counts 形态：TRAIN `channel_counts.npz` 经 accepted TRAIN loader (J4a, 溯源 TRAIN) 与 held-out 池可达/帧数 1683/430k 校验 (J4b, 按 `split_manifest` hold 区间，校验分散窗口 15/源不重叠且每窗口 4 帧=1024 pairs、禁止最前 60 帧截断)；首块/源单臂绑定哨兵 `390128/390228/390328` — 仅校验数据通路：`L1 p_i→s1→BP_fake→q_fake` 单臂六项 + `treatment fake` 七项复用 + `v35_tag_import_ok`（`compute_tag_64` 可 import 且 `empty+x2` 可用、`hex[:16]`、x1 不变/x2 敏感）与 `leakage_accounted`（`1064/1094/1104` 含 64 tag 工程 verification）+ `tag_scope_l2_only` + `prior_train_only_ok`（loader 未触 held-out）+ `sampling_mode=deterministic_spread_four_consecutive_frames` + `frame_ids/ordinal` 窗口校验；真实 `q≠p`、L1 iterations/syndrome/exact/wrong、APP entropy/confidence 不在此 gate，仅执行期测量。
3. **Preflight 失败** → 建增量根，写 `v48_invalid_notice.json` + 空 records + `v48_summary.json`（terminal `V48_EVIDENCE_INVALID`，planned 90 / l1 45 / l2 45 / total 90，无聚合）后零 decoder calls 停止。
4. **建根**：仅在全部拒绝类守卫与科学 preflights 通过后、首个 decoder call 前。

哨兵同 V47 §11 形态，仅更新 registry (96) 与单臂与 held-out prior 隔离与 tag L2-only 空前缀与确定性窗口；`fake_path_verified` 保留。

## 10. 记录、聚合、summary

记录 schema（每 L2 call，单臂，`tag_scope=l2_only`，`sampling_mode=deterministic_spread_four_consecutive_frames`）：

```
call_id("C01".."C45"), source,
construction_seed, construction_seed_ordinal, block_seed(block ID, 非随机 seed), matrix_id, h1_matrix_id ("V31-H1-QC-16×1024, m1=16"),
frame_ids[4], held_out_ordinal_start, held_out_ordinal_end, pairs_count(1024), sampling_mode("deterministic_spread_four_consecutive_frames"),
max_iter, damping_alpha, errors_initial, errors_final, exact_l2, exact_u1, exact_full,
syndrome_ok_l2, syndrome_ok_l1, wrong_codeword_l2, wrong_codeword_l1,
target_tag, candidate_tag, tag_ok, tag_scope("l2_only"),
reclassified ∈ {exact, detected_verification_failure, decoder_non_syndrome_failure, undetected_accepted_wrong},
iterations_l1, iterations_l2, bp_posterior_entropy, mean_abs_diff_q_p,
leak_total (1064/1094/1104),
status, runtime_s
```

其中 `reclassified` 由 `exact/syndrome_ok/tag_ok` 派生，四类互斥穷尽。L1 45 次 invocations 记账单列。`tag_scope` 恒 `l2_only`；`target_tag/candidate_tag` 均为 `compute_tag_64(empty,x2)`。`frame_ids` 为该窗口四帧真实 frame_id，`held_out_ordinal_start/end` 为 hold 区间内 ordinal，`pairs_count` 恒 1024。

Summary 含：记账（planned 90 / l1 45 / l2 45 completed/started actuals，total 90）；`l1_diagnostics`（执行期测量永不 gate：`mean_abs_diff(q,p)`、`APP entropy/confidence`、`H1_rank/capacity_ok/projective_ok`、`iterations_l1` 分布、`exact_u1/syndrome_ok_l1/wrong_l1`）；聚合（`exact_l2/exact_u1/exact_full` 总量与每源、`detected / decoder_non_syndrome / undetected` 各计数、`wrong_codeword` 明细、G3' `undetected==0` 判定、迭代/运行时均值、entropy/||q-p||1 分布）；per-source 聚合；per-block 结果 + errors_final、exact_full/tag_ok 对照 + `leak_total` + `frame_ids/ordinal/sampling_mode`；门禁明细（G1/G2/G3' 数值与 pass/fail，基于 `undetected==0` 单臂，35/45 与 10/15 权威）在 terminal 判定之后；路由轨迹；`terminal_state`+`terminal_reason`；`stopped_for_analysis`；`undetected_anomaly`；`needs_heldout_structure_branch` orthogonal 标志；master stop rule 原文；claim boundary（含工程近似、L2-only 与单臂固定泄漏 1064/1094/1104 与确定性分散窗口说明）；statistics note；provenance（authorized target SHA `4342e1a7dc4d0d84d83f5d374cb9b38cdefb0c24`、HEAD/origin 绑定、前代 plan/execution SHAs、结构权威身份、H1 物料身份 `V31-H1-QC-16×1024 m1=16 rank16`、V25 TRAIN counts 溯源 + held-out 池 1683/430k 溯源、分散窗口 `start_j=floor(j*(H-4)/14)` 与明细表、O1 机制 id `l1_app_soft_transfer_H1_16_syndrome_derived_with_v35_tag_l2_only_heldout_deterministic_spread`、tag 源 `v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only`、泄漏 `1064/1094/1104` (L2 syndrome 920/950/960 +80+64) + `f_total`，含工程 verification 声名 `SHA-trunc64 random-hash-model approximate 2^-64, not information-theoretic; strict bound requires universal2+seed; L2-only`）。

## 11. 统计与断言边界

仅描述性；样本 tiny 但 held-out 独立（90 invocations = 45 唯一 held-out 块 ×(1 L1+1 L2)；45 L2 records 单臂）；比例报告带 n 与 raw counts；任何打印区间 naive 且未校正簇聚；无显著性检验；主要门禁仅 `exact_full` 且 `tag_ok` gate 后仍计 `exact`，`exact_u1/exact_l2` 另行报告且不经 tag（L2-only）；`detected` 不计 exact；单臂固定泄漏，不宣称容量/阈值/SKR。

断言边界 verbatim：结果仅支持 V25 TRAIN 经验 counts 上的 H1-16 + Lane C 90/1.0 + 通用 FFT-QSPA `q=softmax BP posterior / APP approximation` 真实 syndrome-derived 软转移在 held-out 块上的有界泛化归因 — held-out 评估块来自 `split_manifest` hold 区间 1683 frames / 430k pairs (1M 400 / 1p5M 554 / 2M 729) 的确定性分散窗口 `start_j=floor(j*(H-4)/14)` 各 4 帧=1024 pairs（非最前 60 帧、非随机抽取），先验 `P(U1|B)/P(U2|B,u1)` 始终仅由 TRAIN `channel_counts.npz` 构建、未用 held-out 重估，L2 在固定 Lane C 三矩阵 ordinal-2 上 90/1.0 单点、`leak_total 1064/1094/1104 (920/950/960+80+64, f_total, 工程 verification L2-only)`，复用 V35 `compute_tag_64(empty,x2)[:16]`，不改结构/阈值，`undetected≈2^-64` 仅随机哈希模型工程近似（固定公开 SHA-256 截断；严格界需 universal2+seed），单臂固定泄漏；均非真帧 FER 全集证据，不推阈值/SKR/正式执行/资格/晋升；终态仅方向性 held-out PASS/FAIL，不启动 V49。

## 12. 证据写出与增量输出根

固定增量根（在解码前建，fail-closed 若已存在；科学 preflight 失败亦建仅放 invalid 三件套）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v48_heldout_confirm/run_01/
```

文件（最小固定集）：

- `v48_records.json` / `.csv`（每 L2 call 一行，共 45 行，含 `target_tag/candidate_tag/tag_ok/reclassified/tag_scope/leak_total` + `frame_ids[4]/held_out_ordinal_start/held_out_ordinal_end/pairs_count/sampling_mode`；L1 诊断随行或单独数组）
- `v48_summary.json`（§10 内容，含四类计数、分层记账 90、门禁明细、终态、工程 verification L2-only 声名、provenance 含 H1 与 tag 源与 TRAIN/held-out 双溯源与分散窗口表、单臂泄漏 1064/1094/1104）
- `v48_invalid_notice.json`（仅完整性失败时）

CSV/JSON 行对等；禁写任何 `.npz`；禁以非 accepted TRAIN loader 读 NPZ；既有 `results/`、V38–V48 输出保持 byte-identical。

## 13. 实现草图（后继轮次，当前未授权）

- 新模块 `comparison_bench/src/comparison_bench/formal_ir/v48_heldout_confirm.py`：仅 import accepted `nonbinary_v31.build_layer/build_matrix_packet` (H1-16) / `v38` 重建 helper / `v35.compute_tag_64`；按 V47 D15 组合单臂 held-out 路径（含 L1 APP 链 `p_i→s1→BP_i→q_i→P_i(U2)`，BP posterior / APP approximation，early-stop 冻结）并在每 L2 解码后调用 `compute_tag_64(empty,x2)` 生成/比对 tag（L2-only）；prior loader 仅 `load_v25_channel_counts()` TRAIN，不 import held-out counts 作 prior；registry 以拷贝数据常量进入（含 96+45）；采样改为 `deterministic_spread_four_consecutive_frames` 查表（`start_j` 明细），禁止 `sample_empirical_block` 路径；不重新实现 canonical 编码。
- 新 CLI `scripts/execute_v48_heldout_confirm.py`：默认拒绝；必带 `--execution-authorized --authorized-target-sha <sha>`；HEAD 与 origin/formal-ir-mainline 精确等值绑定规划 HEAD `4342e1a7dc4d0d84d83f5d374cb9b38cdefb0c24`；四文件 SCOPED dirty（含 v48 替代 v47/v35）；绑定 `fake_runner=False`；无 fake-runner CLI 选项；守卫失败非零退出、零 calls、不创建文件；budget 硬帽 90。
- 仅 fake-runner 测试；测试中不做生产解码；真实 `tag_ok` 分流仅执行期测量；增加 TRAIN prior 隔离测试与 held-out 分散窗口可达测试与 `sampling_mode/frame_ids` 校验。

## 14. 自由裁量决策 D1–D15（主线程复核清单，V48 新增 held-out，修订后冻结唯一路径）

- **D1 形态**：单臂 H1-16 held-out 泛化诊断，45 blocks 单臂 (90 invocations: 45 L1 +45 L2)，无多臂/压缩对照；对照为 TRAIN 同候选历史结果，不在同 run 内重跑 TRAIN。
- **D2 seed registry + 确定性窗口**：新区每源 x28+ 连续 IDs `390128-142/390228-242/390328-342` 仅作 block ID；FORBIDDEN 96 = 87 (V36_A3∪V39∪V40∪V41∪V42∪V43∪V44∪V45∪V46 9) + V47 9，新区与 96 零重叠 per source 连续均分；实现复验 J2；窗口按 `start_j=floor(j*(H-4)/14)` 一一映射（§3 明细），禁止随机抽取与最前 60 帧截断。**删除 30-block 备案**。
- **D3 代表矩阵**：三枚 lane_c ordinal-2 id 死写（§5）+ 一枚 H1 母矩阵 `V31-H1-QC-16×1024` 死写并秩校验；严格重建比对（J3）。
- **D4 detected 作用域**：`detected_verification_failure` 计为 rejected 不计 exact，通过 `undetected==0` 的 G3' 体现；单臂无跨臂否决。
- **D5 门禁阈值（冻结唯一）**：45 块 `≥35/45 (77.8%)` 且 `每源 ≥10/15 (66.7%)` 且 `undetected==0`，基于 `exact_full` + `tag_ok` (L2-only)；**删除 30 块 `≥24/30`/`≥7/10` 算术**；`L1 wrong` 单独报告，等比于 V47 `7/9`。
- **D6 哨兵落点**：每源首块 390128/390228/390328，单臂六项/七项 fake-beliefs 通路 + `prior_train_only_ok` + `heldout_reachable_ok`（分散窗口 15/源不重叠、每窗口 4 帧=1024、frame_ids 可达）+ `v35_tag_import_ok` + `tag_scope_l2_only` + `sampling_mode` + `leakage_accounted` (1064/1094/1104, `leakage_already_accounted` 声名，工程 verification 声名)。
- **D7 call 序**：源 1M/1p5M/2M、块升序。
- **D8 SCOPED-dirty 范围**：v48 模块+v48 CLI+v38 模块+v35 模块（含 tag 源）。
- **D9 preflight 失败证据策略**：invalid 三件套零 L2 calls（l1 45→0, l2 45→0, total 0）；拒绝类不建目录。
- **D10 文件集**：最小固定集（records 45 行含 tag_ok/tag_scope/reclassified/leak + frame_ids/ordinal/sampling_mode、summary 含分层记账 90 + 四类聚合 + G3' + 终态）；永不写 NPZ。
- **D11 终态命名**：三终态 `V48_HELDOUT_PASS / V48_HELDOUT_FAIL / V48_EVIDENCE_INVALID`，互斥覆盖，EVIDENCE_INVALID 优先。
- **D12 后继语**：仅方向性（§1/§7），不授权；**不启动 V49**。
- **D13 O1 机制**：L1 APP 软转移按 §5 冻结（`p_i→s1→BP_i→q_i→P_i(U2)` 单向，复用通用 FFT-QSPA BP posterior / APP approximation，泄漏单点固定，early-stop 冻结）+ V35 `compute_tag_64(empty,x2)[:16]` L2-only 工程 verification + TRAIN-only prior + 确定性分散窗口。
- **D14 errors_initial 策略**：沿用 V47 严格 per-block 单值。
- **D15 组合单臂路径 + tag + held-out 确定性窗口**：单码路径、可注入 `decode_fn`；在 L2 解码后追加 `compute_tag_64(empty,x2)` L2-only 比对；held-out 块来自 frame 池确定性分散四帧窗口，prior 不触 held-out，禁止随机抽取。

## 15. V47 处置衔接与本诊断新颖性边界

V47 已在 TRAIN 9 块上以三臂验证 H1 冗余压缩；V48 在此之上追加 **held-out 泛化**：同一 H1-16 + 同 prior (TRAIN) + 同 Lane C 90/1.0 在 held-out **45 块确定性分散窗口**上的独立复现，考验 TRAIN 经验 prior 在 held-out 分布上的外推能力。真实 `mean_abs_diff(q,p)` 与 `APP entropy` 按 held-out 测量，不与 TRAIN 混计；泄漏固定 1064/1094/1104，门禁等比于 V47 `7/9`。TRAIN prior 隔离与 held-out 零重叠 + 分散窗口覆盖为本诊断核心科学边界。
