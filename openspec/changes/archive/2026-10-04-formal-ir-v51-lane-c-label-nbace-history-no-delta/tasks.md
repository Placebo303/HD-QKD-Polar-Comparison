# OpenSpec Tasks: formal-ir-v51-lane-c-label-nbace

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行。等待独立评审。本轮仅完成 decoder-free 标签优化 spike。**
**Execution status**: 本轮完成 decoder-free spike；以下 P1..E 任务待独立 plan ACCEPT + 三源词典序准入后方可进入；当前不跑 decoder，不写产出。
**Plan commit**: resolved externally by independent PLAN_ACCEPT record; implementation SHALL bind the accepted full SHA.（实现冻结时重绑至未来 implementation SHA）
**Revision**: V51R1 — 修复 deg4 优先、自定义 score 命名、准入一致性、spike 增量效率、四工件去 NB-ACE 文献声称

## Phase A — 语义冻结（plan ACCEPT 后）

- [ ] **A1** 冻结基座：`n=1024, m2=184/190/192, GF32 poly37, Lane C 二值 support/位置置换/m2/泄漏 1064/1094/1104/decoder 90/1.0` 全部冻结，仅边标签 `1..31` 可变；三源 Lane C `s383102/383202/383302` ordinal-2 身份与 `row_deg/col_deg` 分布冻结。
- [ ] **A2** 冻结确定性标签优化器：输入二值 support，`ACE=Σ(row_deg-2)`，`is_deg` 经 `classify_cycle_algebraic_degeneracy`，自定义 `check_extrinsic_score=ACE-100 若退化 else ACE`（明确非文献 NB-ACE，仅次级报告）；主目标词典序 `(deg4, deg6, deg8, cand)` 优先 4-环（修正原 deg6 起点错误）；canonical 边序 greedy `1..31` 至多 2 sweeps，复用 `edge_to_cycle_ids` 仅重算 incident cycles 增量维护全局 `deg4/6/8`，不为每个候选复制完整 `is_deg` 数组；禁止译码回搜；`support_exact_equal/rank==m2/support_cycles_4/6/8 不变` 硬保证。
- [ ] **A3** 冻结 decoder-free 谱对比字段：每源原 vs 新 `support_exact_equal, rank, support_cycles_4/6/8, degenerate_4/6/8, generalized_girth, nondeg_frac6/8` 为主可验证量并列；`min_check_extrinsic6/8, min_deg_ace6/8` 为自定义次级报告量（原 NB-ACE 命名已废止）；`Δdeg4, Δdeg6, Δdeg8` 为主判据。
- [ ] **A4** 冻结谱准入（三源一致性）：`label_improved = (∀source: (deg4_new,deg6_new,deg8_new) ≤_lex (deg4_old,deg6_old,deg8_old)) ∧ (∃source: (deg4_new,deg6_new,deg8_new) <_lex (deg4_old,deg6_old,deg8_old))`，词典序优先 deg4；自定义 score 不参与准入主判；否则 `V51_LABEL_NO_IMPROVEMENT` blocker 不实验。原“∃source deg6/min_check_extrinsic 改善”已废止。
- [ ] **A5** 冻结 15 新未使用 held-out blocks：与 `FORBIDDEN 156 =141+15(V50 391xxx)` 零重叠、无内部重复、每源均分 5、连续 IDs `392001..392005 / 392101..392105 / 392201..392205` 且每块写死 `4` 真实 `frame_ids` 与 `ordinal start/end`（见 design §2.4），与 V48/V50 `frame_ids` 零重叠 per source 可机械校验；`sampling_mode=deterministic_four_consecutive_frames_heldout_unused_new`。
- [ ] **A6** 冻结条件 paired workload（仅当准入通过）：每块 `1×L1 shared +2×L2 (old vs new)=3`，共 `15×3=45` (`l1 15 / l2 30 / total 45`)；冻结配对主判 `exact_full`、McNemar `b/c/discordance`、残留误码/迭代/runtime 分布；无 TRAIN+VAL 臂。
- [ ] **A7** 冻结记录与聚合：`15` 新块 paired 记录、`v51_label_spectrum.json` 原 vs 新谱（deg 主 + 自定义 score 次级）、`v51_summary.json` 含谱对比+分层记账+配对表+四类/G3'；`f_total=leak/[N(H1+H2)] N=1024`、`tag_scope=l2_only`；provenance 中自定义量明确非文献 NB-ACE。
- [ ] **A8** 冻结终态：`V51_EVIDENCE_INVALID` 优先、`V51_LABEL_NO_IMPROVEMENT` 次之（存在恶化或无改善）、`V51_PAIRED_COMPLETE` 描述性完成；无晋升阈值。

## Phase B — 聚焦测试（仅 fake runner/decode_fn；零生产解码）

- [ ] **B1** Seed-registry 校验：拒重复/错形状/与 FORBIDDEN 156 零重叠 per source 连续 + 与 V50 391xxx 与 V48 `frame_ids` 零重叠；接受新区 `392001..` `392101..` `392201..`。
- [ ] **B2** 重标一致性：同支撑重建 `Lane C new` 与原支撑精确相等、`rank==m2`、`support_cycles_4/6/8` 不变；标签谱 `deg4/6/8` 可重算，自定义 `check_extrinsic_score` 可重算但仅次级；`support_exact_equal==True` 硬门；校验 `edge_to_cycle_ids` 增量路径与全量重算一致（抽样）。
- [ ] **B3** Tag 复用与四类：`compute_tag_64` 确定性、`tag_scope==l2_only`；配对 `old vs new` 四类与 `G3' undetected==0` 单独表；McNemar 表可由 `exact_full` 派生。
- [ ] **B4** 哨兵与谱准入：每源首块 `392001/392101/392201` 各 `L1→P_i(U2)` 通路 + `label_spectrum_ok` + `support_equal_ok` + `rank_ok` + 三源词典序一致性 `label_improved` 布尔可机械判定（∀不恶化 ∧ ∃严格改善，优先 deg4）。
- [ ] **B5** 预算帽（冻结 45 条件）：fake 结构拒第 46 call（J10，总硬帽 45 @15块, l1 15/l2 30/total 45）；校验每块序 `old→new`。
- [ ] **B6** 写出合约：文件集精确（30 L2 行含 `label_id old/new` + `frame_ids/sampling_mode/ordinal`；`label_spectrum.json` 原 vs 新谱 deg 主 + 自定义次级；summary 含分层记账 45 + 配对聚合 + 谱对比 + 四类/G3' + 终态）、CSV/JSON 行对等、已存在根 fail-closed、禁写 NPZ、provenance 含自定义 `check_extrinsic_score` 定义（明确非文献 NB-ACE）+ 一次确定性重标 ID。

## Phase C — preflight（decoder-free，授权前）

- [ ] **P1** 重建 Lane C 原三矩阵 `383102/383202/383302` 与 committed `rank/support_cycles_4/6/8/deg4/6/8` 比对；重标 `new` 三矩阵 decoder-free 重建与 `support_exact_equal/rank/cycles 不变` 校验；`compute_tag_64` 可 import；校验三源词典序一致性 `label_improved` 布尔（∀不恶化 ∧ ∃改善，优先 deg4）；校验新 15 held-out 未使用池可达且与 FORBIDDEN 156 及 V50 `frame_ids` 零重叠；零求值器、零写盘。
- [ ] **P2** 在首块 `392001/392101/392201` 跑 `L1 shared →P_i(U2)` 通路 + `label_spectrum` + `support_equal` + `rank` + `leakage_accounted` + `sampling_mode/frame_ids/ordinal`；仅报 PASS/BLOCKED。
- [ ] **P3** 以拷贝 FORBIDDEN 156 机械校验 J2（新区 15 IDs block ID 零重叠且每块 `frame_ids` 与 V50/V48 零重叠、无重复、每源均分连续，design §2.4）并确认输出根缺席；仅报 PASS/BLOCKED。

## Phase D — 授权 paired 执行（需 EXECUTE_AUTH 且谱准入通过，至多 45 calls @15 块）

- [ ] **D1** 主线程获独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支 `formal-ir-mainline`、完整未来实现 SHA、cycle V51P0、scope `v51_lane_c_label_nbace_45_calls_paired_exactly_once`，三源词典序准入 `label_improved=True` 已验证，自定义 score 非文献声称已确认）。
- [ ] **D2** 恰好一次：`python scripts/execute_v51_label_nbace.py --execution-authorized --authorized-target-sha <sha>`；`45 calls (L1 15 + L2 30: 15×(1 L1+2 L2 old/new))`，30 L2 records（per block paired `old vs new`），每条含 `label_id/matrix_id/target_tag/candidate_tag/tag_ok/reclassified` (L2-only) 与 `exact_u1/exact_l2/exact_full/entropy/||q-p||1/leak_total/frame_ids/sampling_mode`；保留 `run_01`；出错止、原样保留 raw partial 无聚合、返回 blocker；不 rerun/resume/tuning/加块/改标签/重实现 canonical；无论结果不做第二轮；同块 old/new 同 `bob` 同 `P_i(U2)` 同 prior TRAIN；采样恒 deterministic 新 held-out。
- [ ] **D3** 只读 postcheck：记账 `planned 45 / l1 15 / l2 30 / total 45`、L2 30 记录与序每块 `old→new` 正确、`label_id` 双溯源、新 held-out 块 `frame_ids/ordinal` 逐块比对 design §2.4、无 NPZ、V38–V50 输出 byte-identical、summary 完备（含谱原 vs 新 deg 主 + 自定义次级 + 分层记账 + 配对 McNemar/discordance + 残留/迭代/runtime + 四类/G3' + 终态 + provenance 非 NB-ACE 声称）、独立重算。

## Phase E — 结果复核

- [ ] **E1** 写 `OPERATOR_RETURN.md` 与 `DEVELOPMENT_RESULT.md` 候选；lifecycle 保持 result-candidate；含谱对比原 vs 新（deg4/6/8 主 + 自定义次级）、terminal (`V51_EVIDENCE_INVALID / V51_LABEL_NO_IMPROVEMENT / V51_PAIRED_COMPLETE`)、配对 `old vs new exact_full`、McNemar `b/c/discordance`、per-block 残留/迭代/runtime、四类计数、`l1` 执行期诊断上下文真实 `q≠p` 严格在 claim boundary 内（不宣称 FER/晋升，不声称自定义量为文献 NB-ACE）。
- [ ] **E2** 主线程/reviewer 独立重算谱/配对/机器/终态与四类；verdict 入 `REVIEW_VERDICT.md`。
- [ ] **E3** Memory triage 单独里程碑（本规划轮禁改 `AGENT_PROJECT_MEMORY.md`）；**不启动 V52**。

## 本变更期间显式禁止

plan ACCEPT 前实现；以译码结果回搜 seed/重标或多候选择优；改 support/置换/行列度/m2/泄漏/decoder；新增第二标签或多臂；以 V50 outcomes 选持块；写 NPZ；把 wrong 计为 exact；作晋升排名；FER/阈值/SKR/安全/资格/晋升陈述；结果后加块/加 seed/改阈值/改机制；rerun/resume/补偿 partial；任何结果下开第二轮；自接受；自动启动后继（含 V52）；import `v39..v50` 模块作生产解码；任何 `compute_tag_64(x1_true,…)` 形态；改 H1/`m2` 泄漏；创建正式 `.../v51_*/run_01` 输出（P1 仅规划）；运行 decoder（P1 仅 decoder-free spike）；声称自定义 `check_extrinsic_score` 为文献标准 NB-ACE；为每个候选复制完整 `is_deg` 数组的低效实现。
