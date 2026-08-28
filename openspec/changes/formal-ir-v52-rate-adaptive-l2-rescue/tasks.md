# OpenSpec Tasks: formal-ir-v52-rate-adaptive-l2-rescue

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行 decoder，不写产出。等待独立评审。本轮仅完成 decoder-free 嵌套 spike。**
**Execution status**: 本轮仅完成 decoder-free 嵌套 spike；以下 P1..E 任务待独立 plan ACCEPT 后方可进入；当前不跑 decoder，不写产出。
**HEAD**: `6aa33eadc872bb4551f458ee750a94cd24566314`（plan SHA；实现冻结时重绑至未来 implementation SHA）
**Predecessor**: `6aa33eadc872bb4551f458ee750a94cd24566314` (formal-ir-mainline)
**Delta m**: `Δm=8` per source 冻结

## Phase A — 语义冻结（plan ACCEPT 后）

- [ ] **A1** 冻结首遍五元组：`n=1024, m2=184/190/192, GF32 poly37, Lane C ordinal-2 二值 support/标签/位置置换, H1-16 rank16 80b, L1-APP `q_i` via `BP_i` (TRAIN prior), decoder `90/1.0 early-stop`, verification `syndrome_ok && tag_ok` L2-only `compute_tag_64(empty,x2)`；`leak_base=5*m2+80+64 →1064/1094/1104`；`exact_full=exact_u1&&exact_l2 oracle` 报告 promises。
- [ ] **A2** 冻结增量矩阵 `H_inc` (`Δm=8` per source)：`8×1024 GF32 poly37`、`col_degree_inc∈{0,1}`、`row_degree≤16`、`无零增量行`、`rank_joint==m2+8`、`nested H_base==H_joint[:m2]`、`independence==Δm` (rank 增量)、确定性 PEG-增量 `SeedSequence([60000x,1/2/3])`、禁止 seed 搜索、第二候选与调 `Δm`；`E_inc` 报告、`leak_joint=leak_base+40` 公式冻结、已成功帧不增泄漏。
- [ ] **A3** 冻结两遍条件协议：`pass1(H_base)` → `verify1(syndrome&&tag)` 通过则停 `leak_base`；否则 `s_inc=H_inc*u2_true`、`s_joint=[s_base;s_inc]`、`pass2(H_joint)` → `verify2`，`leak=leak_base if verify1 else leak_joint`；报告 `first_pass_success / rescued_by_increment / final_exact_full` 三计数及 `rescue_rate` 描述性。
- [ ] **A4** 冻结 15 fresh held-out blocks：与 `FORBIDDEN 171 = 96+45(V48)+15(V50 391xxx)+15(V51 392xxx)` block ID 零重叠、无内部重复、每源均分 5、连续 IDs `393001..393005 / 393101..393105 / 393201..393205` 且每块写死 `4` 真实 `frame_ids` 与 `held_out_ordinal_start/end`（见 design §2.4），与 V48/V50/V51 180+60+60 帧 `frame_ids` 零重叠 per source 可机械校验；`sampling_mode=deterministic_four_consecutive_frames_heldout_fresh`。
- [ ] **A5** 冻结 paired workload（old vs V52）：每块同 `bob` 同 `P_i(U2)`，`old` 臂单遍 `H_base`，`V52` 臂条件两遍；每块至多 `1 old L2 +1 pass1 + ≤1 pass2` (≤3 L2 decodes) + 共享 `1 L1`；总 `15 L1` + `≤45 L2` records 概念预算；冻结 `paired Δexact = final_V52 - old` 描述性、McNemar `b/c` 仅描述。
- [ ] **A6** 冻结报告承诺 SHALL：`first_pass_success_count / incremental_rescue_count / final_exact_full / per_source (1M/1p5M/2M) / average_leakage / failed_conditional_leakage / joint_rank+nested+independence / real_tag_acceptance / paired_old_vs_incremental (fresh)`；显式 `avg_leak = (N_success*leak_base + N_rescue_attempt*leak_joint)/N`、`failed_conditional=leak_joint`、`successful_conditional=leak_base`。
- [ ] **A7** 冻结记录与聚合：`15` 块 paired 记录、`v52_summary.json` 含 `first/rescued/final/old` 分层、每源分源、平均/条件泄漏、`f_avg/f_failed`、`H_inc provenance (Δm=8 det1 joint_rank/nested/independence/E_inc/row_max)`、`tag acceptance`、`paired Δexact`、`四类/G3'`、门禁描述、provenance 含每块 `frame_ids/ordinal`；`tag_scope=l2_only`。
- [ ] **A8** 冻结终态：`V52_EVIDENCE_INVALID` 优先、`V52_NESTED_RESCUE_COMPLETE` 描述性完成；无晋升阈值；`rescue_gain = final_V52>old` 仅旗标。

## Phase B — 聚焦测试（仅 fake runner/decode_fn；零生产解码）

- [ ] **B1** Seed-registry 校验：拒重复/错形状/与 FORBIDDEN 171 block ID 零重叠 per source 连续 + 与 V50 391xxx、V51 392xxx、V48 `frame_ids` 零重叠；接受新区 `393001..` `393101..` `393201..`。
- [ ] **B2** 嵌套矩阵重建匹配：`H_base m2×1024` 与 committed v38 常量一致；`H_inc 8×1024` 注入 `rank_joint` / `nested` / `independence` 漂移 → J 路径；重建一致；代表身份错 → J；校验 `rank_joint==m2+8`、`H_base==H_joint[:m2]`、`rank_increment==8`、`row_degree_max≤16`、`col_degree_inc≤1`、`leak_joint==leak_base+40`。
- [ ] **B3** 泄漏公式校验：`leak_base 1064/1094/1104`；`leak_joint 1104/1134/1144`；`avg_leak` 公式 `leak_base + (1-p1)*40` 可重算；`failed_conditional==leak_joint`、`successful_conditional==leak_base`。
- [ ] **B4** Tag 复用与四类分流（L2-only 空前缀）：`compute_tag_64` 确定性、`hex[:16]`、`tag_scope==l2_only`；`pass1/pass2` 各自 `syndrome_ok&&!exact&&!tag_ok→detected` 等四类；`G3' undetected==0` 单独表；`first_pass_success` 以 `tag_ok` 判但同时报告 `exact` 预留。
- [ ] **B5** 哨兵与嵌套与泄漏校验：每源首块 `393001/393101/393201` 各 `L1→P_i(U2)` 通路 + `h_base_ok` + `h_inc_nested_ok` + `joint_rank_ok` + `independence_ok` + `leakage_accounted (base/joint/avg/conditional)` + `tag_scope_l2_only` + `sampling_mode/frame_ids`。
- [ ] **B6** 样本一致性（fresh held-out）：同 ID 重采样一致；缺/重 block →J6；校验 fresh 块非 V50/V51/V48 块。
- [ ] **B7** 真值表（描述性完成）：integrity ok/failed × `V52_NESTED_RESCUE_COMPLETE / V52_EVIDENCE_INVALID` 互斥；另校验 `rescue_gain = final_V52 > old` 描述性旗标可区分；`first/rescued/final` 计数一致性 `final = first + rescued + (其他失败)`。
- [ ] **B8** 预算与配对序校验：fake 结构校验每块至多 `1 old +1 pass1 + ≤1 pass2` 条件序冻结（源 1M/1p5M/2M、块升序、块内 `old→V52_pass1→(条件)V52_pass2`）。
- [ ] **B9** 写出合约：文件集精确（≤45 L2 行含 `arm/pass_index/used_increment/matrix_id/joint` + `frame_ids/sampling_mode/ordinal` + `leak_total/leak_joint/avg`；summary 含 `first/rescued/final/old` 分层 + 每源 + 平均/条件泄漏 + `f_*` + `joint_rank/nested/independence` + paired `old vs V52` + 四类/G3' + 终态）、CSV/JSON 行对等、已存在根 fail-closed、禁写 NPZ、provenance 含 `H_inc Δm=8 det1` + fresh held-out 溯源含每块 `frame_ids/ordinal`。

## Phase C — preflight（decoder-free，授权前）

- [ ] **P1** 重建 `Lane C base m2×1024` 三矩阵与 committed `rank/support` 比对；重建 `H_inc 8×1024` 三矩阵与 `joint_rank==m2+8 / nested / independence==8 / row≤16 / col≤1` 校验；`compute_tag_64` 可 import；校验 `leak_base/joint` 公式；校验 fresh 15 held-out 池可达且与 FORBIDDEN 171 及 V48/V50/V51 `frame_ids` 零重叠；零求值器、零写盘。
- [ ] **P2** 在首块 `393001/393101/393201` 跑 `L1 shared →P_i(U2)` 通路 + `h_base/h_inc/nested/rank/independence` + `tag_ok` + `leakage_accounted` + `sampling_mode/frame_ids/ordinal`；仅报 PASS/BLOCKED.
- [ ] **P3** 以拷贝 FORBIDDEN 171 机械校验 J2（新区 15 IDs block ID 零重叠 per source 且每块 `frame_ids` 与 V48/V50/V51 零重叠、无重复、每源均分连续，design §2.4）并确认输出根缺席；仅报 PASS/BLOCKED.

## Phase D — 授权两遍条件执行（需 EXECUTE_AUTH，15 块 paired）

- [ ] **D1** 主线程获独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支 `formal-ir-mainline`、完整未来实现 SHA、cycle V52P0、scope `v52_nested_rescue_15_blocks_paired_exactly_once`，plan 引用 HEAD `6aa33eadc872bb4551f458ee750a94cd24566314`）。
- [ ] **D2** 恰好一次：`python scripts/execute_v52_nested_rescue.py --execution-authorized --authorized-target-sha <sha>`；按 design §2.3 两遍协议执行：`15 块 × (old 1 L2 + V52 pass1 1 + 条件 pass2 ≤1)`，每条 L2 记录含 `arm/pass_index/used_increment/matrix_id/target_tag/candidate_tag/tag_ok/reclassified` (L2-only) 与 `exact_u1/exact_l2/exact_full/errors/syndrome/entropy/||q-p||1/leak_total/leak_joint`；保留 `run_01`；出错止、原样保留 raw partial 无聚合、返回 blocker；不 rerun/resume/tuning/加块/改增量/重实现 canonical；无论结果不做第二轮；同块 old 与 V52 首遍同 `bob` 同 `P_i(U2)`；采样恒 deterministic fresh held-out.
- [ ] **D3** 只读 postcheck：记账 `first_pass_success / rescued / final_V52 / old`、`15` 块 paired 记录与序每块 `old→pass1→(条件)pass2` 正确、增量 `H_inc` provenance、fresh held-out `frame_ids/ordinal` 逐块比对 design §2.4、无 NPZ、V38–V51 输出 byte-identical、summary 完备（含 `first/rescued/final/old` 分层 + 每源 + 平均/条件泄漏 + `f_*` + `joint_rank/nested/independence` + paired + 四类/G3' + `tag acceptance` + 终态 + `leakage_formula`）、独立重算.

## Phase E — 结果复核

- [ ] **E1** 写 `OPERATOR_RETURN.md` 与 `DEVELOPMENT_RESULT.md` 候选；lifecycle 保持 result-candidate；含 `first_pass_success / incremental_rescue / final_exact_full / old_exact_full` (overall & per-source)、`avg_leak / failed_conditional_leak`、`joint_rank/nested/independence` 实测、`paired old vs V52 Δexact` per block 描述性、McNemar `b/c` 仅描述、四类计数、`l1` 执行期诊断上下文真实 `q≠p` 严格在 claim boundary 内（含 L2-only 工程近似与 `leak_base 1064/1094/1104` / `leak_joint+40` 已成功帧不增泄漏说明，不宣称 FER/晋升）。
- [ ] **E2** 主线程/reviewer 独立重算 `first/rescued/final/old`、泄漏、嵌套秩、配对与终态与四类；verdict 入 `REVIEW_VERDICT.md`.
- [ ] **E3** Memory triage 单独里程碑（本规划轮禁改 `AGENT_PROJECT_MEMORY.md`）；**不启动 V53**.

## 本变更期间显式禁止

plan ACCEPT 前实现；以 outcomes 回搜增量位置/调 `Δm` 或多候选择优；改首遍 support/标签/先验/度分布/m2/H1/泄漏/decoder；重复比较 prior、标签或另一全新 MET 图；新增第二增量候选或档位；以 V50/V51 outcomes 选持块；写 NPZ；把 wrong 计为 exact；作晋升排名；FER/阈值/SKR/安全/资格/晋升陈述；结果后加块/加 seed/改阈值/改机制；rerun/resume/补偿 partial；任何结果下开第二轮；自接受；自动启动后继（含 V53）；import `v50/v51` 模块作生产解码；任何 `compute_tag_64(x1_true,…)` 形态；改 H1/`m2` 泄漏或 `90/1.0` 或引入第二变量外泄漏变更；创建正式 `.../v52_*/run_01` 输出（P0 仅规划）；运行 decoder（P0 仅 decoder-free spike）；声称增量行非嵌套却计 `avg_leak`。
