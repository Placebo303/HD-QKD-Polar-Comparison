# OpenSpec Tasks: formal-ir-v50-l2-structure-factorial

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V51。等待独立评审。本轮先执行 spike。**
**Execution status**: 本轮仅完成 decoder-free 结构 spike；以下 P1..E 任务待独立 plan ACCEPT 后方可进入；当前不跑 decoder，不写产出。
**HEAD**: `f58955f3e794dbde11b4d813eec061182319846d`（实现冻结时重绑）

## Phase A — 语义冻结（plan ACCEPT 后）

- [ ] **A1** 冻结唯一等泄漏真 MET 候选 `P0-MET-1 {dv2:512,dv3:512} E=2560 dv_mean=2.5`（全 `dv2` 非 MET，若用则改名 `PEG-dv2 E=2048`）：`n=1024, m2=184/190/192` 按源、`GF32 poly37`、`无零列`、`满行秩`、`dc_max=16`、`max_degree2_chain≤4`、`degree2_pure_ring(len≤12)==0`（`G2` 精确：链为 `G2` 内内部校验度 2 的极大路径，环为双分长度 `≤12` 且全 `dv=2` 闭环）、`确定性 lifting/label`、`禁止 seed 搜索`、`support_cycles_4==0` 硬门、`6/8-cycles` 报告（含 `pure_*`）；与 Lane C 相同 `m2` 与泄漏 `1064/1094/1104` (920/950/960+80+64, 与 `E` 无关)、相同 decoder `90/1.0`；构造规则不接触 V48 outcomes。
- [ ] **A2** 冻结双 prior 正交对照：`TRAIN prior` (`channel_counts.npz` TRAIN 经 `load_v25_channel_counts()`) vs `TRAIN+VAL prior` (`TRAIN⊕VAL` 合并 counts 同接口)，仅影响 `L1 p_i→BP_i→q_i→P_i(U2)`，不改矩阵/泄漏/decoder。
- [ ] **A3** 冻结 15 未使用 held-out blocks：与 `FORBIDDEN 141 = 96(V36..V47)+45(V48)` block ID 零重叠、无内部重复、每源均分 5、连续 IDs `391001..391005 / 391101..391105 / 391201..391205` 且每块写死 `4` 真实 `frame_ids` 与 `held_out_ordinal_start/end`（见 design §2.4 冻结表），与 V48 180 帧 `frame_ids` 零重叠 per source 可机械校验；每块 `4 frames=1024 pairs (每帧256)`、`BLOCK_LENGTH=1024`、`sampling_mode=deterministic_four_consecutive_frames_heldout_unused`；增量根 `.../v50_l2_structure_factorial/run_01/` fail-closed；不接触 V48 outcomes。
- [ ] **A4** 冻结 2×2 workload（90 calls）：每块 `2×L1 (TRAIN/TRAIN+VAL) +4×L2 (A=TRAIN×LaneC, B=TRAIN+VAL×LaneC, C=TRAIN×P0, D=TRAIN+VAL×P0) =6`，共 `15×6=90` (`l1 30 / l2 60 / total 90`)；冻结主效应 `E_structure=(C+D-A-B)/2`、`E_prior=(B+D-A-C)/2`、`E_interaction=(D-C)-(B-A)`，并保留四个 simple effects `C-A(TRAIN下结构) / D-B / B-A(LaneC下先验) / D-C(P0下先验)`；`C-A` 为 simple effect 非主效应。
- [ ] **A5** 冻结每因子报告：`exact_u1/exact_l2/exact_full(=u1&&l2, oracle)` per factor/per source、四类 `exact/detected/decoder_non_syndrome/undetected`、`G3' undetected==0`、`L1/L2 iterations/runtime`、`APP entropy/||q-p||1` 分布、固定泄漏 `1064/1094/1104`、`tag_ok/tag_scope=l2_only` L2-only verification。
- [ ] **A6** 冻结终态：`V50_EVIDENCE_INVALID` 优先、`V50_FACTORIAL_COMPLETE` 描述性完成；orthogonal `structure_gain/due` 仅描述性旗标，不作晋升门禁。
- [ ] **A7** 冻结其余同构常量：Lane C 三矩阵 ordinal-2、`90/1.0 poly37`、`bp_posterior_beliefs / APP approximation`、`f_total=leak/[N(H1+H2)] N=1024`、`errors_initial` 严格 per-block-per-prior 单值、`H1 16×1024 rank16` 复用 `nonbinary_v31.build_matrix_packet`。

## Phase B — 聚焦测试（仅 fake runner/decode_fn；零生产解码）

- [ ] **B1** Seed-registry 校验：拒重复/错形状/与 FORBIDDEN 141 block ID 重叠（`96+45`）且与 V48 180 帧 `frame_ids` 重叠 per source；接受新区 `391001..` `391101..` `391201..` 15 IDs per source 连续均分零重叠且 `frame_ids` 零重叠（design §2.4 冻结表）。
- [ ] **B2** P0 重建匹配：`P0-MET-1 m2×1024` 真 MET `{dv2:512,dv3:512} E=2560`（PEG-dv2 则 `E=2048`）注入 metric 漂移 → J 路径；重建一致；代表身份错 → J；校验 `rank==m2`、`col_degree_min≥1`、`dc_max≤16`、`E==2560`（或 `2048` 若 PEG）、`support_cycles_4==0`、`max_chain≤4`、`pure_ring(≤12)==0`（`G2` 精确）。
- [ ] **B3** Tag 复用与四类分流（L2-only 空前缀）：`compute_tag_64` 确定性、`hex[:16]`、`tag_scope==l2_only`；`x1` 不变/`x2` 敏感；`syndrome_ok&&!exact&&!tag_ok→detected` 等四类；`G3' undetected==0` 单独表。
- [ ] **B4** 哨兵与双 prior 与链环与 4-cycle 校验：每源首块 `391001/391101/391201` 各 `L1_T/L1_TV→P_i(U2)` 通路 + `prior_train_ok` + `prior_train_val_ok` + `v35_tag_import_ok` + `leakage_accounted` (1064/1094/1104) + `tag_scope_l2_only` + `chain_ring_ok` + `four_cycle_zero` + `sampling_mode/frame_ids`。
- [ ] **B5** 样本一致性（未使用 held-out）：同 ID 重采样一致；缺/重 block →J6；校验未使用块非 V48 块。
- [ ] **B6** 真值表（描述性完成）：integrity ok/failed × `V50_FACTORIAL_COMPLETE / V50_EVIDENCE_INVALID` 互斥；另校验 `structure_gain = C>A` 与 `prior_gain = B>A` 描述性旗标可区分。
- [ ] **B7** 预算帽（冻结 90）：fake 结构拒第 91 call（J10，总硬帽 90 @15块, l1 30/l2 60/total 90）；校验 `A,B,C,D` 每块序冻结（源 1M/1p5M/2M、块升序、块内 A→B→C→D）。
- [ ] **B8** 写出合约：文件集精确（60 L2 行含 `prior_id/structure_id/tag_ok/reclassified/leak` + `frame_ids/sampling_mode` + `held_out_ordinal`；summary 含分层记账 90 + 因子聚合 + 主效应 `E_structure/E_prior/E_interaction` 与四个 simple effects + 四类/G3' + 终态）、CSV/JSON 行对等、已存在根 fail-closed、禁写 NPZ、provenance 含 `P0-MET-1 {dv2:512,dv3:512}` 确定性 ID + held-out 未使用溯源（含每块 `frame_ids/ordinal`）+ 双 prior 溯源。

## Phase C — preflight（decoder-free，授权前）

- [ ] **P1** 重建 `P0-MET-1 m2×1024` 三矩阵（真 MET `E=2560`）；与 committed v38 常量 `dc_max/capacity` 比对（含 `G2` 精确链/环）；校验 `compute_tag_64` 可 import 且 `empty+x2` 可用；校验 TRAIN 与 TRAIN+VAL counts 形态可达；校验未使用 held-out 池可达且与 FORBIDDEN 141 block ID 及 V48 180 帧 `frame_ids` 零重叠；校验 4 frames=1024/256 per frame；零求值器、零写盘。
- [ ] **P2** 在首块 `391001/391101/391201` 跑双 prior 绑定 preflight（`p_i→s1→BP_fake→q_fake` 双 prior + `chain_ring_ok(G2精确)` + `four_cycle_zero` + `tag_ok` + `leakage_accounted(与E无关)` + `sampling_mode/frame_ids/ordinal`）；仅报 PASS/BLOCKED.
- [ ] **P3** 以拷贝 FORBIDDEN 141 机械校验 J2（新区 15 IDs block ID 零重叠且每块 `frame_ids` 与 V48 零重叠、无重复、每源均分连续，design §2.4 冻结表）并确认输出根缺席；校验 4 frames/block 按 hold 帧序分散拼接可行；仅报 PASS/BLOCKED.

## Phase D — 授权 2×2 因子执行（需 EXECUTE_AUTH，90 calls @15 块）

- [ ] **D1** 主线程获独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支 `formal-ir-mainline`、完整实现 SHA、cycle V50P0、scope `v50_factorial_90_calls_2x2_exactly_once` 冻结，HEAD `f58955f3e794dbde11b4d813eec061182319846d`）。
- [ ] **D2** 恰好一次：`python scripts/execute_v50_structure_factorial.py --execution-authorized --authorized-target-sha <sha>`；`90 calls (L1 30 + L2 60: 15×(2 L1+4 L2))`，60 L2 records（per factor 每源/每结构/每 prior），每条含 `prior_id/structure_id/target_tag/candidate_tag/tag_ok/reclassified` (L2-only) 与 `exact_u1/exact_l2/exact_full/entropy/||q-p||1/leak_total/frame_ids/sampling_mode`；保留 run_01；出错止、原样保留 raw partial 无聚合、返回 blocker；不 rerun/resume/tuning/加块/改 seed/机制/加权重/重实现 canonical；无论结果不做第二轮；执行期测量真实 `q≠p`/`iterations`/`tag_ok` 分流；采样恒 deterministic 未使用 held-out.
- [ ] **D3** 只读 postcheck：记账 `planned 90 / l1 30 / l2 60 / total 90`、L2 60 记录与序每块 `A,B,C,D` 正确、L1 30 次、`prior_id` 双溯源、未使用 held-out 块（`frame_ids/ordinal` 逐块比对 design §2.4）、无 NPZ、V38–V48 输出 byte-identical、summary 完备（含分层记账与主效应 `E_structure/E_prior/E_interaction` 及四个 simple effects + 四类/G3' + 终态 + `f_total` + provenance）、独立重算.

## Phase E — 结果复核

- [ ] **E1** 写 `OPERATOR_RETURN.md` 与 `DEVELOPMENT_RESULT.md` 候选；lifecycle 保持 result-candidate；含 terminal (`V50_EVIDENCE_INVALID / V50_FACTORIAL_COMPLETE`)、路由轨迹、因子聚合与主效应 `E_structure/E_prior/E_interaction` 及四个 simple effects `C-A/D-B/B-A/D-C`、per-block 结果、四类计数、`l1` 执行期诊断上下文（真实 `q≠p`/entropy/iterations/||q-p||1/tag_ok）严格在 claim boundary 内（含 L2-only 工程近似与等泄漏 1064/1094/1104（与 `E` 无关）与未使用 held-out `frame_ids` 说明，不宣称 FER/晋升）。
- [ ] **E2** 主线程/reviewer 独立重算信号/机器/终态与四类与主效应；verdict 入 `REVIEW_VERDICT.md`.
- [ ] **E3** Memory triage 单独里程碑（本规划轮禁改 `AGENT_PROJECT_MEMORY.md`）；**不启动 V51**.

## 本变更期间显式禁止

plan ACCEPT 前实现；对 V48 45 块重放或复用已用 held-out 块作评估；以 V48 outcomes 选结构/阈值；新增第二 protograph/MET 候选或 seed 搜索或调参/调泄漏/调 decoder；以非 accepted 双 prior loader 读 counts；写任何 NPZ；把 wrong 计为 exact；作单臂优劣晋升排名；FER/阈值/SKR/安全/资格/晋升陈述；结果后加块/加 seeds/改阈值/改机制；rerun/resume/补偿 partial；任何结果下开第二轮；自接受；自动启动后继（含 V51）；import v39..v48 模块作生产解码；任何 `compute_tag_64(x1_true,…)` 形态；改 H1/L2 `m2` 泄漏或 `90/1.0` 或引入第二变量外泄漏变更；创建正式 `.../v50_*/run_01` 输出（P0 仅规划）；运行 decoder（P0 仅 decoder-free spike）.
