# OpenSpec Tasks: formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **仅规划与数据就绪资格准备，不实现新方法，不执行 decoder，不创建正式 TEST 输出。等待独立复审与数据就绪裁决。本轮仅完成四工件 + decoder-free 清单脚本/报告。**
**Execution status**: 本轮仅完成四工件 + `check_v55_data_readiness.py` (decoder-free G1-G7) + `data_readiness_report.md`；以下 Phase G 及之后任务待 `V55_QUALIFICATION_PLAN_READY` + 独立 plan ACCEPT + `EXECUTE_AUTH` 后方可进入；当前不跑 decoder，不创建 `.../v55_*/run_01`。
**HEAD**: `efd34ef318014e1d0505605062057b042e2180eb`（plan SHA；实现冻结时重绑至未来 implementation SHA）
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` (`bf5dd1686049156540328bac264296b17fee546c`, branch `formal-ir-mainline`)
**Delta m**: `Δm=8+8=16` per source 冻结（V54 已冻，V55 不新增），总 `180-360` 硬帽360
**Data status**: `V55_DATA_NOT_READY` 为当前预期终态（非失败，需新数据），`G1-G7` 未全过前不得进入 Phase G

## Phase A — 语义冻结（plan ACCEPT 前，本轮已冻结）

- [ ] **A1** 冻结方法完全体（零改，首遍与二阶段）：`n=1024, m2=184/190/192, GF32 poly37, Lane C ordinal-2二值support/标签/位置置换, H1-16 rank16 80b, L1-APP q_i via BP_i (TRAIN prior channel_counts.npz), H_inc1 8×1024 det1 + H_joint1 192/198/200, H_inc2 8×1024 det2 + H_total 200/206/208, decoder 90/1.0 early-stop, verification syndrome_ok&&tag_ok L2-only compute_tag_64(empty,x2), leak_base 5*m2+80+64 →1064/1094/1104, leak_stage1+40, leak_stage2+80, exact_full=exact_u1&&exact_l2 oracle, Δm=8+8 唯一**；V55 **不测新矩阵/标签/prior/阈值/decoder参数**，新增即 EVIDENCE_INVALID。
- [ ] **A2** 冻结二阶段增量矩阵（唯一已冻变量，V55 不新增）：`8×1024 GF32 poly37` ×2 per source、`col_degree_inc∈{0,1}`、`row_degree≤16`、`无零行`、`rank_joint1==m2+8`、`rank_total==m2+16`、`nested1 H_base==H_joint1[:m2]`、`nested2 H_base==H_total[:m2] && H_joint1==H_total[:m2+8]`、`independence_1==8` (rank_joint1 - rank_base)、`independence_2==8` (rank_total - rank_joint1)、确定性 PEG-增量 `SeedSequence([600001-600003,1/2])` 与 `SeedSequence([600004-600006,1/2])` 各 source、禁止 seed 搜索/第二候选/调 Δm；`E_inc≈96` 报告、`leak_stage1==leak_base+40, leak_stage2==leak_base+80` 公式冻结。
- [ ] **A3** 冻结三阶段条件协议（未来执行，预冻结）：`base(H_base)` → `verify_base` 通过则停 `leak_base`；否则 `s_inc1=H_inc1*u2_true`、`s_joint1=[s_base;s_inc1]`、`stage1(H_joint1)` → `verify_stage1` 通过则停 `leak_stage1`；否则 `s_inc2=H_inc2*u2_true`、`s_total=[s_base;s_inc1;s_inc2]`、`stage2(H_total)` → `verify_stage2`，`leak=leak_stage2` 无论成功/失败；`exact_*` 仅 oracle 统计不触发，三阶段均 `verification-only`；报告 `base_exact_full` 与 `verify_base` 分别计数、`stage1` 与 `verify_stage1` 分别、`final` 与 `verify_final` 分别，门禁仅用 `final` 累计量。
- [ ] **A4** 冻结合格 TEST 样本要求（建议，非本轮执行）：每源各一独立 session（≠2026-01-21 V13），每源 ≥120 frames 建议≥160，每帧 256 pairs，每块 4 连续帧 1024 pairs，不入 prior/方法选择，冻结前不看解码结果；主样本 `30 blocks/source ×3 =90 blocks, 360 frames`，于新 session 内枚举 `[0..F-4]` 过滤已用区间得 `K≥30`，`index_j=floor(j*(K-1)/29) j=0..29` 分散选 30/源，两两非重叠 gap≥4 且与 V13 及 V48-V54 零重叠；建议 IDs `396001-030/396101-130/396201-230` 仅标识，真实由 `frame_ids` 决定；`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55`、`BLOCK_LENGTH=1024`。
- [ ] **A5** 冻结 paired workload（预冻结，三阶段共享 L1）：每块同 `bob` 同 `P_i(U2)`，`base L2` 1次 → 条件 `stage1 ≤1` → 条件 `stage2 ≤1`，共享 `L1 1`；每块 `L1 1+base 1+stage1 ≤1+stage2 ≤1`（L2 1-3）；总 `90 L1+90 base+≤90 stage1+≤90 stage2=180-360 硬帽360 (L2 90-270)`。
- [ ] **A6** 冻结报告承诺 SHALL（未来执行）：`base_exact_full` 与 `verify_base` 分别计数（禁止假定相等）/ `stage1_exact_full` 与 `verify_stage1` 分别 / `final_exact_full` 与 `verify_final` 分别 / `stage1_rescued / stage2_rescued` / `N_stage1_attempted=count(!verify_base)` 与 `N_stage2_attempted=count(!verify_stage1&&!verify_base)`（overall & per-source）/ `rescue_rate_stage1/stage2` / 每源分层 / `first_pass_success_leak / stage1_success_leak / stage2_leak / per_source_avg[s]=leak_base[s]+40×N_stage1[s]/30+40×N_stage2[s]/30` 与 `overall_avg=(Σ leak_base+40×N_stage1_total+40×N_stage2_total)/90` / `avg_disclosure_per_attempted_frame(=overall_avg/1024)` / `total_disclosed_bits` 与 `disclosure_per_final_exact_block=total/final_count（为0则null）` / `f_avg` 若保留则分母 `1024×(H(U1|B)+H(U2|U1,B))` 禁 `N_blocks×(H1+H2)` / `Wilson 95%` 仅报告 / 迭代/runtime/residual / 四类；`V54 45块` 仅历史描述。
- [ ] **A7** 冻结记录与聚合（预冻结）：`90` 块三阶段条件记录、`v55_summary.json` 含 `base/stage1/final` 三层 `exact` 与 `verify` 分别计数分层+每源+`per_source_avg` 与 `overall_avg` +`Wilson 95%`+`H_inc1 joint1_rank/nested/independence` 与 `H_inc2 total_rank/nested/independence` provenance、`tag acceptance`、paired `base vs stage1 vs final`、`rescue_rate`、四类/G3'、门禁明细（`final` 的 G1/G2/G3' 数值与 `V55_*` 终态）、claim boundary。
- [ ] **A8** 冻结终态四者+DATA_NOT_READY（互斥，`DATA_NOT_READY` 与 `EVIDENCE_INVALID` 优先于 PASS/FAIL）：`V55_DATA_NOT_READY`（G1-G7 任一不过，非失败，需新数据）、`V55_EVIDENCE_INVALID`（完整性/秩/嵌套/重叠/记账失败）、`V55_INDEPENDENT_TEST_PASS`（`final≥70/90 ∧ 每源20/30 ∧ undetected==0 ∧ rank/nested/verification/记账` 满足）、`V55_INDEPENDENT_TEST_FAIL`（完整性通过但未过门禁）；门禁不因 V54 结论改阈值；`PASS/FAIL` 仅当 `DATA_READY` 后执行才可判定。
- [ ] **A9** 冻结执行偏差防复发与数据就绪门前置：不使用 600s 外部 timeout（建议≥3600s或不设）、若返回 session/cell ID 只轮询同一进程禁重启、中断时保留 raw partial 及调用计数不生成 aggregate、不得自动重跑；**G1-G7 未过即拒**（`V55_DATA_NOT_READY`），输出根已存在即拒；“仅四工件+decoder-free 清单脚本/报告，不得实现/执行 decoder” 已冻结。

## Phase B — 数据裁决与新 session 搜索（本轮 P0，decoder-free）

- [ ] **B1** 数据裁决登记：确认 V13 HOLD 已污染结论（`V48 45 + V50 15 + V51 15 + V52 15 + V53 45 + V54 45 =180块` 已用，`split_manifest 60/20/20`），即使剩余 `K2≈135/260/461` 窗口未译码也不得改称 TEST；登记已用 `frame_ids` 540-720 帧清单可追溯。
- [ ] **B2** 新 session 搜索：于 `PROJECT_DATA_ROOT` / `comparison_bench/configs/` / 外部采集目录搜索与 `2026-01-21 V13` 不同日期的 1M/1p5M/2M 各一 session（建议 ≥120 frames 建议≥160），记录候选 `session_id / 日期 / 路径 / 帧数 / 延迟`，与 V13 及 V48-V54 零重叠校验。
- [ ] **B3** 若搜索后无可用新 session（`G1-G7` 任一不过），则标记 `V55_DATA_NOT_READY`（非失败，需新数据），**不得创建 production module/CLI/tests/正式 output root，不得用 HOLD 冒充，不得模拟 TEST 数据**；仅交付 `data_readiness_report.md` 缺口分析。
- [ ] **B4** 若有候选，则按 Phase C 算法冻结 90-block registry 候选（30/源，分散非重叠），但仍需 G1-G7 全过才 `V55_QUALIFICATION_PLAN_READY`。

## Phase C — 90-block 注册算法冻结（本轮 P0 冻结算法，未来数据就绪后实例化）

- [ ] **C1** 枚举算法：于新 session 每源 `F` 帧内，枚举 `all_starts=0..F-4` 的 `[s,s+3]` 窗口，过滤与已用区间（V13 全部 + V48-V54 540-720 帧）重叠者得 `S2` 按 ordinal 排序 `K=|S2|≥30`，以 `index_j=floor(j*(K-1)/29) j=0..29` 分散选 30/源，验证最终 90 间两两非重叠（gap≥4）且与已用零重叠 per source；`K<30` 则 `G7_FAIL → DATA_NOT_READY`。
- [ ] **C2** 标识：建议 IDs `396001-030/396101-130/396201-230` 仅标识，真实由 `frame_ids[4]=[global_offset+start .. global_offset+start+3]` 决定；每块写死 `4 frame_ids` 与 `held_out_ordinal_start/end`、`pairs_count=1024`、`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55`、`BLOCK_LENGTH=1024`。

## Phase D — 数据就绪门 G1-G7 decoder-free 校验（本轮 P0 唯一实测，零 decoder）

- [ ] **D1** `check_v55_data_readiness.py` 实现 G1-G7 decoder-free 检查：文件可读、provenance完整、三源明确、256/frame 1024/block、与 V13 及 V48-V54 完全独立、V25 prior只读、冻结 90-block registry；零 `import decoder`，零 `decode_*` 调用，任一失败 `sys.exit(1)`。
- [ ] **D2** `data_readiness_report.md` 生成：逐项 G1-G7 PASS/FAIL、候选 session 清单、已用区间重叠校验、`K/index_j` 分散结果、缺口分析与所需新数据规格（≥120 frames/源 建议≥160，每帧256 pairs，每块4帧，需新采集日期）。
- [ ] **D3** 裁决：全过 → `V55_QUALIFICATION_PLAN_READY`（可进入后续正式 TEST 详细规划）；不过 → `V55_DATA_NOT_READY`（非失败，需新数据），停留 PLAN_CANDIDATE，不进入 Phase G。

## Phase E — 预算/门禁/终态预注册（本轮 P0 预冻结，未来执行时生效）

- [ ] **E1** 预算预冻结：`L1 90 + base90 + stage1 0-90 + stage2 0-90 =180-360 硬帽360 (L2 90-270)`，`base`兼old不重复，每块 `L1 1+base1+stage1≤1+stage2≤1`。
- [ ] **E2** 门禁预冻结：`overall≥70/90 且每源≥20/30 且 undetected==0 且 rank/nested/verification/记账` 均过才 `PASS`，否则 `FAIL`，完整性失败 `EVIDENCE_INVALID`，数据缺失 `DATA_NOT_READY`；`base/stage1` 仅诊断，最终以 `base→Δ16` 主判，`stage1` 不取代最终；`Wilson/rescue/runtime/leakage` 仅报告。
- [ ] **E3** 四终态+DATA_NOT_READY 互斥：`V55_INDEPENDENT_TEST_PASS / V55_INDEPENDENT_TEST_FAIL / V55_EVIDENCE_INVALID` 另有 `V55_DATA_NOT_READY`（非失败，需新数据）；`DATA_NOT_READY` 时不产生任何 decoder 证据。

## Phase F — 本轮交付（P0，decoder-free）

- [ ] **F1** 四工件齐全一致：`proposal.md, design.md, tasks.md, specs/spec.md` lifecycle `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，HEAD `efd34ef...`，`implementation_started=false`，明确 decoder-free。
- [ ] **F2** 可选清单脚本/报告齐全：`check_v55_data_readiness.py`（decoder-free G1-G7）+ `data_readiness_report.md`（逐项 PASS/FAIL + 缺口分析），零 decoder 调用，无正式 output。
- [ ] **F3** 独立复审：plan 未自授 `PLAN_ACCEPTED`，等待独立评审与数据就绪裁决；推送后停在 `PLAN_CANDIDATE`。

## Phase G — 授权三阶段条件执行（需 V55_QUALIFICATION_PLAN_READY + 独立 plan ACCEPT + EXECUTE_AUTH，90块三阶段，180-360 calls，未来轮次，本轮不执行）

- [ ] **G1** 主线程获独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支 `formal-ir-mainline`、完整未来实现 SHA、cycle V55P0、scope `v55_two_stage_rescue_independent_test_90_blocks_triple_exactly_once`，plan 引用 HEAD `efd34ef318014e1d0505605062057b042e2180eb`，且 `G1-G7` 已为 `V55_QUALIFICATION_PLAN_READY`）。
- [ ] **G2** 恰好一次：`python scripts/execute_v55_independent_test.py --execution-authorized --authorized-target-sha <sha>`；按 design 三阶段协议执行：`90块 × (base 1 + 条件 stage1 ≤1 + 条件 stage2 ≤1)`，每块 `L1 1+base L2 1+stage1 ≤1+stage2 ≤1`，总 `180-360 硬帽360 (L2 90-270)`；**执行偏差防复发**：不设 600s 外部 timeout（建议≥3600s或不设）、若返回 session/cell ID 只轮询同一进程禁重启、中断时保留 raw partial 及调用计数不生成 aggregate、不得自动重跑；每条 L2 记录含 `arm∈{base,stage1,stage2}/pass_index/used_inc1/used_inc2/matrix_id/target_tag/candidate_tag/tag_ok/reclassified` (L2-only) 与 `exact_u1/exact_l2/exact_full/errors/syndrome/entropy/leak_total/status/runtime`；保留 `run_01`；出错止、原样保留 raw partial 无聚合、返回 blocker；不 rerun/resume/tuning/加块/改增量/重实现 canonical；无论结果不做第二轮；同块 base→stage1→stage2 同 `bob` 同 `P_i(U2)`；采样恒 deterministic 独立 TEST `K/index_j` 分散。
- [ ] **G3** 只读 postcheck：记账 `base_exact_full` 与 `verify_base` 分别计数（禁止假定相等）、`stage1_exact_full` 与 `verify_stage1` 分别、`final_exact_full` 与 `verify_final` 分别、`stage1_rescued / stage2_rescued / final`、`.stage1/stage2 attempt counts`、`90` 块三阶段记录与序每块 `base→(条件)stage1→(条件)stage2` 正确、增量 `H_inc1` 与 `H_inc2` provenance、独立 TEST `frame_ids/ordinal` 逐块比对 design G1-G7 分散选择、无 NPZ、`V38–V54` 输出 byte-identical、summary 完备（含 `base/stage1/final` 三层 `exact` 与 `verify` 分别分层+每源+`first_pass/stage1_success/stage2_leak/per_source_avg/overall_avg`/`Wilson 95%`/paired 四类/G3' 等）、独立重算；校验门禁 `70/90 & 20/30 & undetected==0` 且 `base→Δ16` 主判。
- [ ] **G4** 写 `OPERATOR_RETURN.md` 与 `DEVELOPMENT_RESULT.md` 候选；lifecycle 保持 result-candidate；含 `base/stage1/final` 三层 `exact` 与 `verify` 分别计数、`rescued`、分源、`N_stage1/N_stage2`、`rescue_rate`、`per_source_avg/overall_avg`、`Wilson 95%`、`total_disclosed_bits` 与 `disclosure_per_final_exact_block` 等描述性。

## 本变更期间显式禁止

plan ACCEPT 前实现；以 outcomes 回搜增量位置/调 Δm 或多候选择优；改首遍 support/标签/先验/度分布/m2/H1/泄漏/decoder；重复比较 prior、标签或另一全新 MET 图；新增第三增量或档位；以 V48-V54 outcomes 选持块或调 Δm 或用 V13 HOLD 剩余帧冒充独立 TEST；写 NPZ；把 wrong 计为 exact；作晋升排名；FER/阈值/SKR/安全/资格/晋升扩大陈述；结果后加块/加 seed/改阈值/改机制；rerun/resume/补偿 partial；任何结果下开第二轮；自接受；自动启动后继（含下一阶段）；import `v50/v51/v52/v53/v54` 模块作生产解码；任何 `compute_tag_64(x1_true,…)` 形态；改 H1/`m2` 泄漏或 `90/1.0` 或引入第二变量外泄漏变更；创建正式 `.../v55_*/run_01` 输出（P0 仅规划）；运行 decoder（P0 仅 decoder-free G1-G7）；声称 V13 HOLD 剩余帧可改称独立 TEST；用模拟 TEST 数据冒充真实采集；创建 production module/CLI/tests/正式 output root（P0 禁止）；自授 `PLAN_ACCEPTED` 或伪造 `V55_QUALIFICATION_PLAN_READY`（需 G1-G7 全过才 READY）。
