# OpenSpec Proposal: formal-ir-v53-rate-adaptive-l2-heldout-confirm

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **仅规划，不实现，不执行 decoder，不创建正式 run_01。等待独立复审。**
**Domain**: Formal IR / Rate-adaptive L2 incremental held-out confirmation (nested HARQ, 45 blocks)
**Change ID**: `formal-ir-v53-rate-adaptive-l2-heldout-confirm`
**Cycle ID**: `V53P0`
**Predecessor**: `formal-ir-v52-rate-adaptive-l2-rescue` (PLAN_REVISE_REQUIRED, HEAD `6aa33eadc872bb4551f458ee750a94cd24566314`, branch `formal-ir-mainline`), plan HEAD `d61d5a3189b54fc0b82e2df688dae3e9bde5ff8e` (branch `formal-ir-mainline`, freeze `formal-ir-mainline`)
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, `formal_execution_authorized=false`
**V52 history**: V52 `12/15`仅作历史描述，非门禁依据；V53以45块独立held-out为判据

> ponytail lite: 本轮仅 decoder-free 样本注册表 + 嵌套秩/泄漏复核 + 四OpenSpec工件；更懒路径是零新增执行直接引用V52 12/15历史描述，需独立评审确认45块增量确认价值是否值得90-135 call预算。

## Goal

在**完全冻结V52完整方法**（`H1-16 + syndrome-derived L1-APP via BP_i + 原Lane C support/标签/置换/先验/MET图全部不改 + m2 184/190/192 + H_inc 3×8×1024 GF32 poly37 + H_joint=[H_base;H_inc] + decoder 90/1.0 + L2-only 64-bit verification + TRAIN-only prior + verification-only rescue`）的前提下，回答：

> **在45个未使用held-out blocks上，Δm=8条件增量（仅对首遍未通过verification的帧额外公开8行并重译）能否稳定达到`final exact_full ≥35/45 且每源≥10/15 且 undetected=0`且`avg disclosure`可接受？**

1. **唯一增量**：`H_inc`已冻结`8×1024` per source（V52 `det1`），`Δm=8`，`row_degree≤16`，`col_degree_inc≤1`，`rank_joint==m2+8`，嵌套`H_base==H_joint[:m2]`，`rank_increment==8`。**不得新造H_inc或试Δm=4/12/16。**
2. **45 fresh blocks**：每源15共45，每块连续4真实held-out frames（`pairs_count=1024, BLOCK_LENGTH=1024`）。汇总`V48/V50/V51/V52`已用`frame_ids`（V48 45块180帧 + V50 15块60帧 + V51 15块60帧 + V52 15块60帧 =90块360帧 + 早期`FORBIDDEN 96` 含V36..V47），枚举剩余**非重叠**四连续窗口（`start 0..H-4 per source, H=400/554/729, base=1600/2213/2916`），过滤与已用区间重叠者得剩余`K`，按`ordinal`排序后以`index_j=floor(j*(K-1)/14) j=0..14`确定性分散选择15/源。Design逐块冻结`block ID / held_out_ordinal_start/end / frame_ids[4] / pairs_count`。建议IDs `394001-015 / 394101-115 / 394201-215`仅作标识，**真实以frame_ids为准**。
3. **预算**：每块`L1 1 + base L2/pass1 1 + rescue≤1`，总`L1 45 + base45 + rescue0-45 = 总90-135 硬帽135`，`L2≤90`。`base`兼`old Lane C`：同一次确定性译码兼作`old` baseline与V53 `pass1`，不得重复译码`old`。
4. **主门禁**：`V53_HELDOUT_CONFIRM_PASS iff final_exact_full ≥35/45 ∧ 每源≥10/15 ∧ undetected==0 ∧ rank/nested/verification/记账通过`；否则`V53_HELDOUT_CONFIRM_FAIL`或`V53_EVIDENCE_INVALID`（完整性优先），**不加复杂终态**。
5. **本轮止于PLAN**：只产出decoder-free样本注册表+矩阵复核+四OpenSpec工件，状态`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；**不得实现/执行decoder，不得创建正式`.../v53_*/run_01/`。**

**报告承诺（shall）**：proposal/design/tasks/specs显式承诺最终报告SHALL包含 — `base_exact_full / final_exact_full`、`rescue count/rate`、每源分层、三类泄漏(`first_pass_success_leak / rescued_success_leak / final_failure_leak`)、`avg leakage = leak_base+40×N_rescue_attempted/45`、`avg disclosure per attempted frame`、`total/final accepted bits`描述性、`iterations/runtime/residual`、四类`exact/detected/decoder_non_syndrome/undetected`、`paired`明细；`V52 12/15`仅历史描述。

## Non-Goals

- 不改冻结方法任一部件：`H1-16`、`Lane C` support/标签/置换/先验/`m2`/`leak_base 1064/1094/1104`、`H_inc/H_joint`、`decoder 90/1.0 poly37`、`L2-only compute_tag_64(empty,x2)`、`TRAIN-only prior`、`verification-only rescue`。
- 不新造`H_inc`、不试`Δm=4/12/16`、不引入第二增量候选或多档率自适应搜索、不做seed搜索或阈值调优。
- 不以`V48/V50/V51/V52` outcomes选择`Δm`或增量位置；不将已用held-out帧复用于V53评估（45块为未使用 fresh held-out，经剩余窗口枚举校验）。
- 不做broad FER/阈值/SKR/安全/资格/晋升陈述；tag仍L2-only `≈2^-64`工程近似；不做信息论安全界宣称。
- 不改写/覆盖`V38–V52`任何已有输出与终态（只读）；本规划轮不修改`AGENT_PROJECT_MEMORY.md / docs/decision-log.md`。
- 不运行decoder（spike为decoder-free只读校验）；不创建正式输出；不启动V54/下一阶段qualification。
- **45块是最小确认规模（30块分源仅10不稳定，详见design §1），V53通过仍是`development confirmation`，下一阶段qualification需新采集/独立TEST（`split_manifest`外或新日期源），不能直接称qualification。**

## Scope

1. **冻结方法（完全冻结，零改）**：`n=1024, m2=184(1M)/190(1p5M)/192(2M), GF32 poly37, H1 16×1024 rank16 80b (V31-H1-QC), L1-APP `q_i=softmax(BP_i)` via `BP_i=decode_row_layered_fftqspa(H1,p_i,s1).bp_posterior_beliefs` (TRAIN prior `channel_counts.npz` via `load_v25_channel_counts()`), Lane C ordinal-2 support/标签/位置置换（`lane_c_*_s38310x`）、`H_inc 8×1024` det1 + `H_joint=[H_base;H_inc]` `192/198/200 ×1024`、`decoder max_iter=90 damping 1.0 early-stop`、`verification tag_scope=l2_only compute_tag_64(empty,x2) trunc64, syndrome_ok && tag_ok 判通过`；`leak_base=5*m2+80+64 →1064/1094/1104`，`leak_joint=leak_base+40 →1104/1134/1144`。
2. **增量 rescue**：`Δm=8` per source冻结，`H_inc`复用V52 `det1`（`SeedSequence([600001/600002/600003,1/2])`, `row≤16 col≤1 无零行 联合满秩 嵌套 独立性8`），构造确定性与`V48/V50/V51/V52` outcomes零接触，禁止新造或调参；`leak_joint-leak_base=40`冻结。
3. **45 fresh held-out blocks（冻结枚举算法）**：于hold区间（1M 400 base1600 / 1p5M 554 base2213 / 2M 729 base2916）内，枚举所有`start 0..H-4`的`4`帧窗口`[start,start+3]`，过滤与已用`V48(180帧)+V50(60)+V51(60)+V52(60)+V36..V47`区间重叠者得剩余集合`S`按`ordinal start`排序`K=|S|`，以`index_j=floor(j*(K-1)/14) j=0..14`分散选择15/源。Design逐块写死`block ID (建议394001..) / held_out_ordinal_start/end / frame_ids[4]=[base+start .. base+start+3] / pairs_count=1024 / sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v53`。与已用`frame_ids`零重叠per source可机械校验；与`FORBIDDEN 96+90=186`基础上新增，实际需与`186+30=216?`详见design §3（`96+45(V48)+15(V50)+15(V51)+15(V52)=186, V53新增45至231`）。`BLOCK_LENGTH=1024`，`pair_idx 0..255`连续。
4. **两遍协议（去重）**：`base/pass1 = decode(H_base, P_i(U2), s_base)`（同一次确定性译码兼作`old`与V53 `pass1`，old结果确定性复用不重复）→ `verify_base=syndrome_ok && tag_ok`；若通过则停`leak=leak_base`；否则`pass2/rescue = decode(H_joint, P_i(U2), s_joint)` where `s_joint=[s_base; s_inc]`（`s_inc=H_inc·u2_true`），`leak=leak_joint`；`avg_leak = leak_base +40×N_rescue_attempted/45`（`N_rescue_attempted =45 - N_first_pass_success`），`failed_conditional=leak_joint`。每块`L1 1+base 1+rescue≤1`，总`45 L1+45 base+≤45 rescue=90-135 硬帽135`（已删除此前小预算表述）；报告`base_exact / rescued_by_increment / final_exact_full`。
5. **门禁与报告**：`G1 final_exact_full≥35/45(77.8%)`，`G2 每源≥10/15(66.7%)`，`G3' undetected_accepted_wrong==0`；三条全满足且`rank/nested/verification/记账`通过则`V53_HELDOUT_CONFIRM_PASS`，否则`FAIL`；`EVIDENCE_INVALID`优先。报告`base/final exact、rescue count/rate、每源分层、三类泄漏、avg leakage、avg disclosure per attempted、total/final accepted bits描述性、iterations/runtime/residual、四类、paired明细`，`V52 12/15`仅历史描述。
6. **执行偏差防复发（冻结）**：不使用600s外部timeout、建议至少3600s、若返回session/cell ID只轮询同一进程禁重启、中断时保留raw partial及调用计数不生成aggregate、不得自动重跑（详见design §6）。
7. **Lifecycle冻结**：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，任何实现/执行需独立plan ACCEPT +显式`EXECUTE_AUTH`绑定到精确实现SHA；不启动下一阶段；本轮仅四工件+decoder-free spike。

## Impact Scope

- **新增（本轮）**：`openspec/changes/formal-ir-v53-rate-adaptive-l2-heldout-confirm/`四工件（`proposal.md, design.md, tasks.md, specs/spec.md`）+ `spike_sample_registry.py` + `spike_report.md`（decoder-free样本注册表与嵌套矩阵复核）。
- **未来实现（本轮不创建）**：`comparison_bench/src/comparison_bench/formal_ir/v53_rate_adaptive_l2_heldout_confirm.py`（仅组合V52冻结方法+确定性45 fresh块+两遍条件runner，不新增decoder）+ `scripts/execute_v53_heldout_confirm.py`；均直接import `v38_architecture_triage` (Lane C) 与 `v35_algorithm_development::compute_tag_64`。
- **只读依赖**：`v38_architecture_triage.py` (Lane C常量/构造器)、`v35_algorithm_development.py` (tag/Field)、`nonbinary_v31.py` (H1)、`load_v25_channel_counts()` (TRAIN prior)、held-out frame池（1683 frames / 430k pairs 未使用校验，`split_manifest 60/20/20`）。
- **不修改**：任何既有spec/代码/测试/输出、`V38–V52`输出、`outputs_comparison`/`workspace`/`AGENT_PROJECT_MEMORY.md`/`docs/decision-log.md`以外；不import `v50/v51/v52`模块作生产解码。

## Acceptance Criteria

- [ ] 四工件+spike脚本/报告齐全一致且lifecycle为`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，plan HEAD绑定`d61d5a3189b54fc0b82e2df688dae3e9bde5ff8e`，`implementation_started=false`，明确“不实现不执行不创建run_01，等待独立评审；严格decoder-free”。
- [ ] 方法完全冻结可机械校验：`H1-16 rank16`、`L1-APP syndrome-derived BP`、`Lane C m2 184/190/192 support/标签/置换`零改、`H_inc 8×1024 det1 / H_joint 192/198/200`、`decoder 90/1.0 poly37`、`leak_base 1064/1094/1104 leak_joint+40`、`tag L2-only`、`TRAIN-only prior`、`verification-only rescue`、`Δm=8`唯一且禁止新造/试4/12/16。
- [ ] 增量矩阵冻结可机械校验：`Δm=8` per source、`H_inc 8×1024 GF32 poly37`、`row≤16 col≤1 无零行`、`joint rank==m2+8`、嵌套`H_base==H_joint[:m2]`、独立性`rank_increment==8`、`E_inc`报告；禁止seed搜索与第二候选。
- [ ] Spike可构造性已实证（decoder-free三源实际生成`H_base+H_inc`联合秩/嵌套/独立性/泄漏公式，零decoder调用，无正式output；失败则`sys.exit(1)`并标记`NESTED_NOT_CONSTRUCTIBLE`或`REGISTRY_INVALID`）。
- [ ] 45 fresh held-out blocks冻结：枚举剩余非重叠四连续窗口（`start 0..H-4`过滤已用区间）、`K≥45`且分散选择`index_j=floor(j*(K-1)/14)`、与已用`V48/V50/V51/V52`及`FORBIDDEN` `frame_ids`零重叠per source、无内部重复、每源均分15、连续建议IDs `394001-015/394101-115/394201-215`但真实以`frame_ids`为准、每块写死`4 frame_ids`与`ordinal start/end`、`pairs_count=1024`、`sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v53`可机械校验。
- [ ] 门禁冻结：`V53_HELDOUT_CONFIRM_PASS iff final≥35/45 ∧ 每源≥10/15 ∧ undetected==0 ∧ rank/nested/verification/记账通过`，否则`FAIL`或`EVIDENCE_INVALID`；不加复杂终态；`45块是最小确认规模（30块分源仅10不稳定）`，`V53通过仍是development confirmation，下一阶段qualification需新采集/独立TEST`已写入claim boundary。
- [ ] 报告承诺显式SHALL：`base/final exact、rescue count/rate、每源分层、三类泄漏(first_pass_success/rescued_success/final_failure)、avg leakage(=leak_base+40×N_rescue_attempted/45)、avg disclosure per attempted、total/final accepted bits描述性、iterations/runtime/residual、四类exact/detected/decoder_non_syndrome/undetected、paired明细`；`V52 12/15仅历史描述`；不得再用单一`successful_conditional=leak_base`口径。
- [ ] 执行偏差防复发冻结：明确禁止600s外部timeout、建议≥3600s、session/cell ID只轮询同一进程禁重启、中断保留raw partial及调用计数不聚合、不得自动重跑（tasks P1..E显式）。
- [ ] 禁止清单冻结：禁止改方法/矩阵/先验/标签/decoder/泄漏口径、禁止新造H_inc/试Δm、禁止用outcomes定增量、禁止创建正式输出、禁止运行decoder、禁止启动下一阶段。

## Tasks

见`tasks.md`（Phase A冻结方法+增量+45 fresh块枚举算法；Phase B仅fake-runner聚焦测试含嵌套/秩/泄漏/门禁与45块注册表；Phase C decoder-free preflight与spike复核；Phase D需EXECUTE_AUTH的至多45块两遍条件执行90-135 calls；Phase E结果复核；显式禁止清单与防复发执行规则）。

## Lifecycle

前代`formal-ir-v52-rate-adaptive-l2-rescue` (含V52 nested rescue规划，`6aa33ead...`，branch `formal-ir-mainline`)；V53当前`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（HEAD `d61d5a3189b54fc0b82e2df688dae3e9bde5ff8e`，branch `formal-ir-mainline`），保持不实现不执行、等待独立复审；实现候选止于`IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户`EXECUTE_AUTH`绑定到精确未来实现SHA；不启动下一阶段。本轮仅四工件+decoder-free样本注册表与矩阵复核，45块为最小确认规模，V53通过仍仅`development confirmation`，下一阶段qualification需新采集/独立TEST，不能直接称qualification。Spike已修复为确定性嵌套`H_joint` `rank==m2+8` + 剩余窗口枚举分散选择45块 + 非零退出校验。
