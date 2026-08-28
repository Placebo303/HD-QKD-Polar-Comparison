# OpenSpec Proposal: formal-ir-v54-two-stage-incremental-l2-rescue

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **仅规划，不实现，不执行 decoder，不创建正式 run_01。等待独立复审。**
**Domain**: Formal IR / Rate-adaptive L2 two-stage incremental rescue (nested HARQ Δ8→Δ16, 45 blocks)
**Change ID**: `formal-ir-v54-two-stage-incremental-l2-rescue`
**Cycle ID**: `V54P0`
**Predecessor**: `formal-ir-v53-rate-adaptive-l2-heldout-confirm` (plan HEAD `93c12fa5a8524eb5a8a52d071f135c653c746ebaf`, branch `formal-ir-mainline`), **plan HEAD** `bf5dd1686049156540328bac264296b17fee546c` (branch `formal-ir-mainline`, freeze `formal-ir-mainline`)
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, `formal_execution_authorized=false`
**V53 history**: V53 `33/45 (差2未过35/45)`仅作历史描述，非门禁依据；V54仍以`35/45 & 每源10/15 & undetected==0`为门禁，不因差两个改阈值

> ponytail lite: 本轮仅 decoder-free 二阶段嵌套秩/样本注册表复核 + 四OpenSpec工件；更懒路径是零新增行直接宣告 V53 12/15 rescue 已足，需独立评审确认 Δ16 二阶段是否值得额外 40b/块与二次 rescue 预算。

## Goal

在**完全冻结 V52/V53 完整方法**（`H1-16 + syndrome-derived L1-APP via BP_i + 原 Lane C support/标签/置换/先验/MET图全部不改 + m2 184/190/192 + H_inc1 8×1024 GF32 poly37 det1 + H_joint1=[H_base;H_inc1] + decoder 90/1.0 poly37 + L2-only 64-bit verification + TRAIN-only prior + verification-only rescue`）的前提下，回答：

> **在 45 个全新未使用 held-out blocks 上，条件二阶段增量（首遍仅用 base，首遍未过则 +H_inc1 8 行重译，仍未过则 +H_inc2 再8行重译，累计 Δm=16）能否以可控的平均泄漏增量稳定达到 `final exact_full ≥35/45 且每源≥10/15 且 undetected==0`？若 stage1 已过门禁则记为 Δ8 已足，若 stage1 未过但 stage2 final 过门禁则记为 Δ16 增量价值信号。**

1. **唯一新增变量**：`H_inc2 8×1024` per source，**确定性单张**，必须满足 `rank([H_base;H_inc1])==m2+8`（已由 V52/V53 spike 实证）且 `rank([H_base;H_inc1;H_inc2])==m2+16`，即 `rank_increment_2==8` 且 `H_total=[H_base;H_inc1;H_inc2]` 嵌套（`H_base==H_total[:m2]` 且 `H_joint1==H_total[:m2+8]`）。**禁止 seed 搜索/多候选/用 V53 outcomes 选行/调行度上限** — 构造确定性 PEG-增量 `SeedSequence([600004/600005/600006,1/2])` 单次生成，`row_degree≤16`，`col_degree_inc2≤1`，`无零行`，`E_inc2≈96`。

2. **45 fresh held-out blocks**：每源 15 共 45，每块连续 4 真实 held-out frames（`pairs_count=1024, BLOCK_LENGTH=1024`）。汇总 `V48/V50/V51/V52/V53` 已用 `frame_ids`（V48 45块180帧 + V50 15块60 + V51 15块60 + V52 15块60 + V53 45块180 =135块540帧 held-out + 早期 `FORBIDDEN 96` TRAIN开发不计），枚举剩余**非重叠**四连续窗口（`start 0..H-4 per source, H=400/554/729, base=1600/2213/2916`），过滤与已用区间重叠者得剩余 `K2`，按 `ordinal` 排序后以 `index_j=floor(j*(K2-1)/14) j=0..14` 确定性分散选择 15/源。Design 逐块冻结 `block ID / held_out_ordinal_start/end / frame_ids[4] / pairs_count`。建议 IDs `395001-015 / 395101-115 / 395201-215`仅作标识，**真实以 frame_ids 为准**，由 `spike_nested_rescue_stage2.py` 实测固化。

3. **三阶段协议（verification-only）**：`base = decode(H_base, P_i(U2), s_base)` → `verify_base=syndrome_ok && tag_ok`；若通过则停 `leak=leak_base (1064/1094/1104)`；否则 `stage1 = decode(H_joint1, P_i(U2), s_joint1)` where `s_joint1=[s_base; s_inc1]` (`s_inc1=H_inc1·u2_true`) → `verify_stage1`；若通过则停 `leak=leak_base+40 (1104/1134/1144)`；否则 `stage2 = decode(H_total, P_i(U2), s_total)` where `s_total=[s_base; s_inc1; s_inc2]` (`s_inc2=H_inc2·u2_true`) → `verify_stage2`，**无论 stage2 成功或最终失败均计 `leak=leak_base+80 (1144/1174/1184)`**。`exact_full = exact_u1 && exact_l2` 仅 oracle 统计，**不触发增量**，触发仅 `verification`。

4. **预算**：每块 `L1 1 + base L2 1 + stage1≤1 + stage2≤1`，总 `L1 45 + base45 + stage1 0-45 + stage2 0-45 = 总90-180 硬帽180`，`L2 45-135`。`base` 兼 `old Lane C` 语义已在 V52/V53 去重，此处三阶段共享同一 `L1→P_i(U2)` 与 `bob`/`prior`。预计实际 `≈112 + 约12 stage2`（若 stage1  rescue 率 ~30%，stage2 需救约 12 块）。

5. **主门禁与四终态**：门禁仍 `final_exact_full ≥35/45 (77.78%) 且每源≥10/15 (66.7%) 且 undetected==0`，**不因 V53 差两个改阈值**。四终态互斥（`EVIDENCE_INVALID` 优先）：
   - `V54_DELTA8_ALREADY_SUFFICIENT` — `stage1` 已过门禁（`stage1_exact_full≥35/45 ∧ 每源≥10/15 ∧ undetected==0` 且 `joint1_rank==m2+8` 等完整性通过）
   - `V54_DELTA16_ADDED_VALUE_SIGNAL` — `stage1` 未过但 `stage2 final` 过门禁
   - `V54_DELTA16_INSUFFICIENT` — `stage1`与`final`均未过门禁但完整性通过
   - `V54_EVIDENCE_INVALID` — 完整性/守卫/秩/嵌套/重叠/记账失败优先
   不加复杂终态，不晋升 qualification。

6. **本轮止于 PLAN**：只产出 decoder-free 二阶段嵌套 spike + 45块 registry + 四OpenSpec 工件，状态 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；**不得实现/执行 decoder，不得创建正式 `.../v54_*/run_01/`。**

**报告承诺（shall）**：proposal/design/tasks/specs 显式承诺最终报告 SHALL 包含 — `base_exact_full` 与 `verify_base` 分别计数（禁止假定 `base_exact==verify_base`）、`stage1_exact_full` 与 `verify_stage1` 分别计数、`final_exact_full` 与 `verify_final` 分别计数、`stage1_rescued = stage1_exact - base_exact` 中 `used_inc1 && stage1_exact` 者、`stage2_rescued = final - stage1` 中 `used_inc2 && final_exact` 者、`N_stage1_attempted=count(!verify_base)` 与 `N_stage2_attempted=count(!verify_stage1 && !verify_base)` 及 `rescue_rate_stage1=rescued_stage1/N_stage1_attempted` 与 `rescue_rate_stage2=rescued_stage2/N_stage2_attempted`（禁止用 `45-base_exact` 作分母）、每源分层、三类泄漏（`first_pass_success_leak / stage1_success_leak / stage2_leak(成功与最终失败同为 leak_base+80)`）及 `per_source_avg[s]=leak_base[s]+40×N_stage1_attempted[s]/15+40×N_stage2_attempted[s]/15` 与 `overall_avg=(Σ leak_base[source(block)]+40×N_stage1_total+40×N_stage2_total)/45`（因三源 `leak_base` 不同禁止用单一 `leak_base+40N/45` 当 overall）、`per-stage avg disclosure per attempted frame`、`total_disclosed_bits=Σ leak_total` 与 `disclosure_per_final_exact_block=total_disclosed_bits/final_exact_full_count（为0则null）`（删除含糊 `final_accepted_bits`，若保留 `f_avg` 则分母为 `1024×(H(U1|B)+H(U2|U1,B))` 禁 `N_blocks×(H1+H2)`）、`iterations/runtime/residual`、四类 `exact/detected/decoder_non_syndrome/undetected`、`paired` 明细（`base vs stage1 vs final`）；`V53 33/45` 仅历史描述。

## Non-Goals

- 不改冻结方法任一部件：`H1-16`、`L1-APP syndrome-derived BP`、`Lane C` support/标签/置换/先验/`m2`/`leak_base 1064/1094/1104`、`H_inc1 det1`/`H_joint1 192/198/200` 、`decoder 90/1.0 poly37`、`L2-only compute_tag_64(empty,x2)`、`TRAIN-only prior`、`verification-only trigger`。
- 不新造 `H_inc1`、不试 `Δm=4/12/16` 除 `8+8` 二阶段外的多档搜索、不引入第三增量或多候选择优、不做 seed 搜索或阈值调优。
- 不以 `V48/V50/V51/V52/V53` outcomes 选择 `Δm` 或增量位置；不将已用 held-out 帧复用于 V54 评估（45块为未使用 fresh held-out，经剩余窗口枚举校验）。
- 不做 broad FER/阈值/SKR/安全/资格/晋升陈述；tag 仍 L2-only `≈2^-64` 工程近似；不做信息论安全界宣称。
- 不改写/覆盖 `V38–V53` 任何已有输出与终态（只读）；本规划轮不修改 `AGENT_PROJECT_MEMORY.md / docs/decision-log.md`。
- 不运行 decoder（spike 为 decoder-free 只读校验）；不创建正式输出；不启动 V55/下一阶段 qualification。
- **45块是 development held-out 确认规模，V54 通过仍是 `development confirmation`，下一阶段 qualification 需新采集/独立 TEST（`split_manifest` 外或新日期源），不能直接称 qualification。**

## Scope

1. **冻结方法（完全冻结，零改）**：`n=1024, m2=184(1M)/190(1p5M)/192(2M), GF32 poly37, H1 16×1024 rank16 80b (V31-H1-QC), L1-APP `q_i=softmax(BP_i)` via `BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs` (TRAIN prior `channel_counts.npz` via `load_v25_channel_counts()`), Lane C ordinal-2 support/标签/位置置换（`lane_c_*_s38310x`）、`H_inc1 8×1024` det1 + `H_joint1 192/198/200×1024`、`decoder max_iter=90 damping 1.0 early-stop`、`verification tag_scope=l2_only compute_tag_64(empty,x2) trunc64, syndrome_ok && tag_ok 判通过`；`leak_base=5*m2+80+64 →1064/1094/1104`，`leak_stage1=leak_base+40 →1104/1134/1144`，`leak_stage2=leak_base+80 →1144/1174/1184`。
2. **二阶段增量 `H_inc2`（唯一新增，`Δm=8` per source 第二张）**：`8×1024 GF32 poly37`、`row_degree≤16`、`col_degree_inc2≤1`、`无零行`、`E_inc2≈96`、`H_total=[H_base;H_inc1;H_inc2]` `200/206/208×1024`、`rank_total==m2+16`、`rank_increment_2==8`（`rank_total - rank_joint1==8`）、嵌套 `H_base==H_total[:m2]` 且 `H_joint1==H_total[:m2+8]`、`syndrome_base` 与 `syndrome_joint1` 分别为 `syndrome_total` 前缀。构造确定性 PEG-增量 `SeedSequence([600004/600005/600006,1/2])` 单次生成，禁止 seed 搜索、第二 `H_inc2` 候选与调参；`V53 outcomes` 零接触。
3. **45 fresh held-out blocks（冻结枚举算法，排除 V53 后）**：于 hold 区间（1M 400 base1600 / 1p5M 554 base2213 / 2M 729 base2916）内，枚举所有 `start 0..H-4` 的 `4` 帧窗口 `[start,start+3]`，过滤与已用 `V48 45区间 + V50 15 + V51 15 + V52 15 + V53 45 =135区间540帧` 重叠者得剩余集合 `S2` 按 `ordinal start` 排序 `K2=|S2|`，以 `index_j=floor(j*(K2-1)/14) j=0..14` 分散选择 15/源。Design 逐块写死 `block ID (建议395001..) / held_out_ordinal_start/end / frame_ids[4]=[base+start .. base+start+3] / pairs_count=1024 / sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v54`。与已用 `frame_ids` 零重叠 per source 可机械校验；与 `FORBIDDEN 96+135=231` block IDs 基础上新增。
4. **三阶段协议**：`base = decode(H_base, P_i(U2), s_base)` → `verify_base`；若通过则停 `leak=leak_base`；否则 `stage1 = decode(H_joint1, P_i(U2), s_joint1)` where `s_joint1=[s_base; s_inc1]`（`s_inc1=H_inc1·u2_true`）→ `verify_stage1`；若通过则停 `leak=leak_stage1=leak_base+40`；否则 `stage2 = decode(H_total, P_i(U2), s_total)` where `s_total=[s_base; s_inc1; s_inc2]`（`s_inc2=H_inc2·u2_true`）→ `verify_stage2`，`leak=leak_stage2=leak_base+80`（成功与最终失败同为+80）；`exact_*` 仅 oracle 统计不触发。`per_source_avg[s]=leak_base[s]+40×N_stage1[s]/15+40×N_stage2[s]/15`，`overall_avg=(Σ leak_base[source(block)]+40×N_stage1_total+40×N_stage2_total)/45`，`avg disclosure per attempted = overall_avg/1024`。
5. **门禁与四终态**：`G1 final≥35/45`，`G2 每源≥10/15`，`G3' undetected==0`；三条全满足且 `rank_total==m2+16 ∧ rank_joint1==m2+8 ∧ nested ∧ 记账` 通过则按 `stage1` 是否已过细分 `V54_DELTA8_ALREADY_SUFFICIENT / V54_DELTA16_ADDED_VALUE_SIGNAL`，否则 `V54_DELTA16_INSUFFICIENT`；`EVIDENCE_INVALID` 优先。不因 V53 差两个改阈值。
6. **Lifecycle 冻结**：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，任何实现/执行需独立 plan ACCEPT + 显式 `EXECUTE_AUTH` 绑定到精确实现 SHA；不启动下一阶段；本轮仅四工件+decoder-free 二阶段 spike。

## Impact Scope

- **新增（本轮）**：`openspec/changes/formal-ir-v54-two-stage-incremental-l2-rescue/` 四工件（`proposal.md, design.md, tasks.md, specs/spec.md`）+ `spike_nested_rescue_stage2.py` + `spike_report.md`（decoder-free 二阶段嵌套/样本注册表复核）。
- **未来实现（本轮不创建）**：`comparison_bench/src/comparison_bench/formal_ir/v54_two_stage_incremental_l2_rescue.py`（仅组合 V53 冻结方法+确定性 H_inc2 + 45 fresh 块+三阶段条件 runner，不新增 decoder）+ `scripts/execute_v54_two_stage_rescue.py`；均直接 import `v38_architecture_triage` (Lane C) 与 `v35_algorithm_development::compute_tag_64`。
- **只读依赖**：`v38_architecture_triage.py` (Lane C 常量/构造器)、`v35_algorithm_development.py` (tag/Field)、`nonbinary_v31.py` (H1)、`load_v25_channel_counts()` (TRAIN prior)、held-out frame 池（1683 frames / 430k pairs 未使用校验，`split_manifest 60/20/20`）。
- **不修改**：任何既有 spec/代码/测试/输出、`V38–V53` 输出、`outputs_comparison`/`workspace`/`AGENT_PROJECT_MEMORY.md`/`docs/decision-log.md` 以外；不 import `v50/v51/v52/v53` 模块作生产解码。

## Acceptance Criteria

- [ ] 四工件+spike脚本/报告齐全一致且 lifecycle 为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，plan HEAD 绑定 `bf5dd1686049156540328bac264296b17fee546c`，`implementation_started=false`，明确“不实现不执行不创建 run_01，等待独立评审；严格 decoder-free”。
- [ ] 方法完全冻结可机械校验：`H1-16 rank16`、`L1-APP syndrome-derived BP`、`Lane C m2 184/190/192 support/标签/置换` 零改、`H_inc1 8×1024 det1 / H_joint1 192/198/200` 复用、`H_inc2 8×1024` 新增且 `H_total 200/206/208`、`decoder 90/1.0 poly37`、`leak_base 1064/1094/1104 leak_stage1+40 leak_stage2+80`、`tag L2-only`、`TRAIN-only`、`verification-only`、`Δm=8+8` 唯一且禁止新造第二张外候选。
- [ ] 二阶段增量矩阵冻结可机械校验：`H_inc2 8×1024 GF32 poly37`、`row≤16 col≤1 无零行`、`rank_joint1==m2+8`、`H_total rank==m2+16`、嵌套 `H_base==H_total[:m2] && H_joint1==H_total[:m2+8]`、独立性 `rank_increment_2==8`、`E_inc2≈96` 报告；禁止 seed 搜索与多候选及用 V53 outcomes 选行。
- [ ] Spike 可构造性已实证（decoder-free 三源实际生成 `H_base+H_inc1+H_inc2` 联合秩/嵌套/独立性/泄漏公式，零 decoder 调用，无正式 output；失败则 `sys.exit(1)` 并标记 `NESTED_NOT_CONSTRUCTIBLE` 或 `REGISTRY_INVALID` 或 `LEAKAGE_MISMATCH`）。
- [ ] 45 fresh held-out blocks 冻结：枚举剩余非重叠四连续窗口（`start 0..H-4` 过滤已用 135 区间 540 帧）、`K2≥45` 且分散选择 `index_j=floor(j*(K2-1)/14)`、与已用 `V48/V50/V51/V52/V53` 及 `FORBIDDEN` `frame_ids` 零重叠 per source、无内部重复、每源均分 15、连续建议 IDs `395001-015/395101-115/395201-215` 但真实以 `frame_ids` 为准、每块写死 `4 frame_ids` 与 `ordinal start/end`、`pairs_count=1024`、`sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v54` 可机械校验。
- [ ] 预算与泄漏冻结：`45 L1+45 base+≤45 stage1+≤45 stage2 =90-180 硬帽180 (L2 45-135)`、`leak_base 1064/1094/1104, stage1 1104/1134/1144, stage2 1144/1174/1184`、`total=Σbase+40*N_stage1+40*N_stage2, avg=total/45`、`per_source_avg[s]=leak_base[s]+40*N_stage1[s]/15+40*N_stage2[s]/15` 与 `overall_avg` 区分、`stage1/stage2 rescue_rate` 分别以 `N_stage1_attempted=count(!verify_base)` 与 `N_stage2_attempted=count(!verify_stage1 && !verify_base)` 为分母（禁止 `45-base_exact`）、`disclosure_per_final_exact_block=total/final_count（为0则null）`、`f_avg` 分母 `1024×(H(U1|B)+H(U2|U1,B))` 冻结。
- [ ] 门禁与四终态冻结：`V54_DELTA8_ALREADY_SUFFICIENT / V54_DELTA16_ADDED_VALUE_SIGNAL / V54_DELTA16_INSUFFICIENT / V54_EVIDENCE_INVALID` 互斥且 `EVIDENCE_INVALID` 优先；`PASS` 当且仅当 `final≥35/45 ∧ 每源≥10/15 ∧ undetected==0 ∧ rank/nested/记账` 满足，`ALREADY_SUFFICIENT` 需 `stage1` 已过，`ADDED_VALUE` 需 `stage1` 未过但 `final` 过；门禁 `35/45 & 10/15 & undetected==0` 不因 V53 差两个改阈值。
- [ ] 报告承诺显式 SHALL：`base_exact_full` 与 `verify_base` 分别计数、`stage1_exact_full` 与 `verify_stage1` 分别、`final_exact_full` 与 `verify_final` 分别、`stage1_rescued / stage2_rescued`、`N_stage1/N_stage2`、`rescue_rate_stage1/stage2`（分母分别为 `count(!verify_base)` 与 `count(!verify_stage1&&!verify_base)` 禁 `45-base_exact`）、每源分层、三类泄漏（`first_pass / stage1_success / stage2_leak`）、`per_source_avg` 与 `overall_avg` 区分（禁单一 base+40N/45 当 overall）、`avg disclosure per attempted`、`total_disclosed_bits` 与 `disclosure_per_final_exact_block`（为0则null）、`f_avg` 分母 `1024×(H(U1|B)+H(U2|U1,B))`、迭代/runtime/residual、四类、paired 明细；`V53 33/45` 仅历史描述。

## Tasks

见 `tasks.md`（Phase A 冻结方法+二阶段嵌套+45 fresh 块枚举算法；Phase B 仅 fake-runner 聚焦测试含嵌套/秩/泄漏/门禁与 45 块注册表；Phase C decoder-free preflight 与 spike 复核；Phase D 需 EXECUTE_AUTH 的至多 45 块三阶段条件执行 90-180 calls；Phase E 结果复核；显式禁止清单与防复发执行规则）。

## Lifecycle

前代 `formal-ir-v53-rate-adaptive-l2-heldout-confirm` (含 V53 45块确认规划，`93c12fa5...`，branch `formal-ir-mainline`)；V54 当前 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（HEAD `bf5dd1686049156540328bac264296b17fee546c`，branch `formal-ir-mainline`），保持不实现不执行、等待独立复审；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户 `EXECUTE_AUTH` 绑定到精确未来实现 SHA；不启动下一阶段。本轮仅四工件+decoder-free 二阶段样本注册表与矩阵复核，45块为 development held-out 确认，V54 通过仍仅 `development confirmation`，下一阶段 qualification 需新采集/独立 TEST，不能直接称 qualification。Spike 已设计为确定性嵌套 `H_total` `rank==m2+16` + 剩余窗口枚举分散选择 45 块 + 非零退出校验；仍停在 `PLAN_CANDIDATE` 未授权执行。
