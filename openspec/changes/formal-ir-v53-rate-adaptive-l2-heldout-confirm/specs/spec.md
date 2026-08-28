# Delta Specification: formal-ir-v53-rate-adaptive-l2-heldout-confirm

**Cycle**: `V53P0`
**Lifecycle**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED` — **修订中，仅规划，不实现，不执行 decoder，不创建 run_01。等待独立复审。**
**Predecessor**: `formal-ir-v52-rate-adaptive-l2-rescue` (branch `formal-ir-mainline` plan HEAD `93c12fa5a8524eb5a8a52d071f135c653c746ebaf` revised from `d61d5a3189b54fc0b82e2df688dae3e9bde5ff8e`)
**Mechanism id**: `nested_incremental_l2_heldout_confirm_delta8_45blocks_v53`
**Tag source**: `v35:compute_tag_64(empty,x2)` (`empty=np.empty(0,dtype=np.uint8)`, `hex[:16]` trunc64, `tag_scope=l2_only`)
**HEAD**: `93c12fa5a8524eb5a8a52d071f135c653c746ebaf`（revised from `d61d5a3189b54fc0b82e2df688dae3e9bde5ff8e`；实现冻结时重绑至未来implementation SHA）
**H1 provenance**: `V31-H1-QC-16×1024 rank16 80b`
**Candidate**: `H_base Lane C ordinal-2 (m2=184/190/192) + H_inc det1 8×1024 GF32 poly37 joint m2+8=192/198/200, row≤16, nested, rank_joint==m2+8`（完全冻结V52方法）
**V52 history**: `V52 12/15`仅历史描述，不作V53门禁依据

## R1. Predecessor binding（完全冻结，不新增H_inc）

V53 SHALL仅基于V52完整冻结方法（`H1-16 + syndrome-derived L1-APP + Lane C H_base 184/190/192 + H_inc 8×1024 det1 + H_joint + decoder 90/1.0 poly37 + L2-only tag + TRAIN-only prior + verification-only rescue`）规划，复用`n=1024`与`m2/leak_base`定义，不改首遍support/标签/prior/MET图/decoder/H_inc/H_joint，不新造H_inc，不试`Δm=4/12/16`，不读取`V48/V50/V51/V52` outcomes选`Δm`或增量位置。V53 SHALL冻结45 fresh held-out blocks的剩余窗口枚举算法（`all_starts 0..H-4`过滤已用区间得`K`，`index_j=floor(j*(K-1)/14)`分散选15/源）+ 两遍条件协议（`base兼old`去重，总`90-135`硬帽135）。V53 SHALL NOT启动下一阶段，实现前需独立plan ACCEPT + 显式`EXECUTE_AUTH`（绑定`formal-ir-mainline`、未来实现SHA，plan引用`d61d5a3189b...`）。Spike脚本任一gate失败SHALL `sys.exit(1)`非零退出，且SHALL NOT运行decoder。`45块是最小确认规模（30块分源仅10不稳定）`，`V53通过仍仅development confirmation`，下一阶段qualification需新采集/独立TEST。

## R2. Frozen method（完全冻结，零改）

冻结方法SHALL为：`n=1024, m2=184/190/192, GF32 poly37, Lane C support/label/position_permutations, m1=16, leak_base=5*m2+80+64 →1064/1094/1104, leak_joint=leak_base+40 →1104/1134/1144`；`H1 16×1024 rank16`复用`nonbinary_v31.build_matrix_packet`；`prior TRAIN` via `load_v25_channel_counts()` → `BP_i` → `q_i` → `P_i(U2)`；`decoder 90/1.0` early-stop；`verification = syndrome_ok && tag_ok` L2-only；`exact_full=exact_u1&&exact_l2` oracle。SHALL NOT改方法任一部件；`Δm=8`唯一。

## R3. Incremental nested matrix — Δm=8（复用V52 det1，无新造）

本变更SHALL复用V52单一冻结增量`H_inc det1 8×1024` per source：`GF32 poly37`, `col_degree_inc∈{0,1}`, `row_degree≤16`, `无零增量行`, `E_inc≈96`报告，`H_joint=vstack([H_base,H_inc])`。SHALL满足：`rank_GF32(H_joint)==m2+8`，`H_base == H_joint[0:m2,:]`嵌套逐比特相等，`rank_increment==8`（独立性）。构造SHALL为V52确定性PEG-增量`SeedSequence([60000x,1/2/3])`单次重建并与spike §4严格比对；`syndrome_base`为`syndrome_joint`前缀。SHALL NOT新造H_inc、不改`Δm`、不引入第二增量候选、不搜seed、不调行度上限、不以outcomes定增量。

## R4. Leakage and conditional disclosure — 三类+平均+披露/比特总量

Tag SHALL为`compute_tag_64(empty_uint8,x2)` L2-only。泄漏SHALL冻结：`leak_base=5*m2+80+64`；`leak_joint=5*(m2+Δm)+80+64 = leak_base+40`。`leak_joint - leak_base =40`恒。Summary SHALL承诺报告：`first_pass_success_leak = leak_base (1064/1094/1104)`；`rescued_success_leak = leak_joint (1104/1134/1144)`；`final_failure_leak = leak_joint`；`per_source_avg[s]=leak_base[s]+40×N_rescue_attempted[s]/15`（`N_rescue_attempted[s]=count(!verify_base) per source`）与`overall_avg=(Σ leak_base[source(block)]+40×N_rescue_total)/45`（`N_rescue_total=count(!verify_base) overall`，因三源`leak_base`不同禁止用单一`leak_base+40N/45`当`overall`）；`failed_conditional_leakage = leak_joint`；`avg_disclosure_per_attempted_frame = overall_avg /1024` bits/symbol 描述性（per source分层）；`total_disclosed_bits = Σ leak_total`（45块求和）与`disclosure_per_final_exact_block=total_disclosed_bits/final_exact_full_count`（`final_exact_full_count==0`则`null`，删除含糊`final_accepted_bits`）；`f_avg = avg_leak / [1024×(H(U1|B)+H(U2|U1,B))]`（若保留则分母为`1024×信息熵和`，禁`N_blocks×(H1+H2)`）描述性。仅`first_pass_success`帧SHALL NOT增加泄漏；`rescued_success`与`final_failure`均SHALL计`leak_joint`。不得再用单一`successful_conditional=leak_base`口径。`V52 12/15`仅历史描述，不纳入本R4门禁。

## R5. Two-pass conditional protocol（去重）

每块SHALL执行共享`base/pass1`（兼`old`）：`base = decode(H_base, P(U2), s_base)` → `verify_base = syndrome_ok_base && tag_ok_base`；该一次确定性译码同时作为`old` Lane C baseline（`old_exact=exact_base, old_verify=verify_base`）与V53 `pass1`，不重复译码；若`verify_base`则停，`final_exact=exact_base`，`leak=leak_base`（`=first_pass_success_leak`），`used_increment=False`；否则`s_inc = H_inc * u2_true`，`s_joint=[s_base;s_inc]`，`rescue = decode(H_joint, P(U2), s_joint)` → `verify2`，`final_exact=exact_rescue`，`leak=leak_joint`（`=rescued_success_leak若救回 else final_failure_leak`），`used_increment=True`，`rescued = (!verify_base && verify2 && final_exact)`。`old`臂结果SHALL由`base`结果确定性复用，不另执行`decode`。`exact_*` SHALL为oracle `array_equal`，`tag_ok`为真实L2-only哈希验收；公开成功以`tag_ok`判，`exact`仅oracle统计但两者均报告。每块`L1 1+base 1+rescue ≤1`，总`45 L1+45 base+≤45 rescue=90-135 硬帽135 (L2 45-90)`。

## R6. Fresh held-out 45 blocks — 剩余窗口枚举分散选择

Workload SHALL为`45` fresh held-out块的`base vs final` paired确认：每块共享`L1`，`base` 1次确定性译码兼作`old`与V53 `pass1`（同`H_base`同`s_base`，不重复），条件`rescue`仅对`base`未通过帧以`H_joint`重译，同`bob`同prior (TRAIN)，同`H1`。Held-out区间 per source `H=400/554/729, base=1600/2213/2916`，枚举`all_starts=0..H-4`的`[s,s+3]`四帧窗口，过滤与已用区间`U`（V48 45区间 + V50 15 + V51 15 + V52 15 + 早期块IDs）重叠者得`S`按`ordinal`排序`K=|S|≥15`，以`index_j=floor(j*(K-1)/14) j=0..14`分散选择15/源，建议block IDs `394001-015/394101-115/394201-215`仅标识（真实以`frame_ids=[base+s .. base+s+3]`为准），每块写死`held_out_ordinal_start/end`、`frame_ids[4]`、`pairs_count=1024`、`sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v53`、`BLOCK_LENGTH=1024`。SHALL与已用`V48/V50/V51/V52`的`frame_ids`零重叠per source可机械校验，且最终45块两两非重叠（gap≥4），否则`REGISTRY_INVALID`。SHALL NOT复用已用帧、SHALL NOT用outcomes选块。`45块是最小确认规模`。

## R7. Reporting promises — SHALL（explicit）

Summary SHALL显式包含（overall与per-source 1M/1p5M/2M）：`base_exact_full_count`与`verify_base=count(syndrome_ok&&tag_ok)`分别计数（禁止假定`base_exact==verify_base`），`incremental_rescue_count (rescued_by_increment)`，`final_exact_full`，`rescue_rate = rescued/N_rescue_attempted`（`N_rescue_attempted=count(!verify_base)` overall，per source `N_rescue_attempted[s]=count(!verify_base) per source`，禁止用`45-base_exact`作分母）描述性；`per_source`分层；`first_pass_success_leak (leak_base)`，`rescued_success_leak (leak_joint)`，`final_failure_leak (leak_joint)`，`per_source_avg[s]=leak_base[s]+40×N_rescue_attempted[s]/15`与`overall_avg=(Σ leak_base[source(block)]+40×N_rescue_total)/45`（`N_rescue_total=count(!verify_base)`，因三源`leak_base`不同禁单一`+40N/45`当`overall`），`avg_disclosure_per_attempted_frame (=overall_avg/1024)`，`total_disclosed_bits (=Σ leak_total)`与`disclosure_per_final_exact_block=total_disclosed_bits/final_exact_full_count`（`final_exact_full_count==0`则`null`，删除含糊`final_accepted_bits`，`f_avg`若保留分母`1024×(H(U1|B)+H(U2|U1,B))`禁`N_blocks×(H1+H2)`），`failed_conditional_leakage (leak_joint)`，`f_avg/f_failed`；`joint_rank==m2+8`，`nested==True`，`independence==8`，`row_degree_max≤16`，`E_inc`；`real_tag_acceptance (tag_ok rate per pass)`；`reclassified四类 exact/detected/decoder_non_syndrome/undetected`；`paired base vs final` per block（`Δexact = final - base`，McNemar `b/c`仅描述，去重）；`iterations/runtime/residual`分布。`V52 12/15`仅历史描述，不作门禁依据。以上SHALL在proposal/design/tasks/specs中显式承诺且在summary中兑现。

## R8. Primary gate — V53_HELDOUT_CONFIRM_PASS

Gate SHALL为：`V53_HELDOUT_CONFIRM_PASS iff final_exact_full ≥35/45 (77.8%) ∧ 每源≥10/15 (66.7%) ∧ undetected_accepted_wrong==0 (G3') ∧ joint_rank==m2+8 ∧ nested==True ∧ independence==8 ∧ verification l2_only ∧ 记账90-135硬帽且每块L1 1+base1+rescue≤1 ∧ 45 fresh块与已用frame_ids零重叠`。否则若完整性/守卫/秩/嵌套/重叠/记账失败 → `V53_EVIDENCE_INVALID`（优先），否则 → `V53_HELDOUT_CONFIRM_FAIL`。不加复杂终态。`PASS`定义SHALL等价于`35/45`绝对阈值（`7/9`等比）与`10/15`每源；`EVIDENCE_INVALID`优先。`PASS`后仍SHALL标注`development confirmation`，不晋升qualification。

## R9. Outputs unchanged & next-stage boundary

V53 SHALL NOT修改任何`V38–V52`已有输出；既有文件byte-identical。V53证据SHALL隔离于`.../v53_rate_adaptive_l2_heldout_confirm/run_01/`，fail-closed。Tag SHALL直接import `v35.compute_tag_64`；prior SHALL为`TRAIN`单一。V53通过SHALL NOT直接称`qualification`；下一阶段qualification SHALL需新采集/独立TEST（`split_manifest`外或新日期源，`counts`不重用），并走独立OpenSpec change。

## R10. Evidence outputs — minimal fixed set（future, not in P0）

授权写出SHALL仅为：`v53_records.json/.csv`（45-90 L2行：45 base_shared(兼old/pass1)+≤45 rescue，含`arm∈{base_shared,rescue}/pass_index/used_increment/matrix_id/joint/leak_total(1064/1094/1104或1104/1134/1144)/leak_joint/frame_ids/ordinal/sampling_mode/tag_ok`；总调用`45 L1+45 base+≤45 rescue=90-135 硬帽135`），`v53_summary.json`（含`base_exact_full`与`verify_base`分别计数分层+每源+`first_pass/rescued/failure/avg`泄漏分类（`per_source_avg[s]=leak_base[s]+40×N_rescue_attempted[s]/15 / overall_avg=(Σ leak_base+40×N_rescue_total)/45`，`N_rescue_total=count(!verify_base)`，因三源`leak_base`不同禁单一`+40N/45`当`overall`）+`avg disclosure`+`total_disclosed_bits`与`disclosure_per_final_exact_block`（为0则null，删除含糊`final_accepted_bits`，`f_avg`分母`1024×(H(U1|B)+H(U2|U1,B))`）+`joint_rank/nested/independence/E_inc/row_max`+paired `Δexact(去重)`+`rescue_rate=rescued/N_rescue_attempted（禁45-base_exact）`+四类/G3'+终态+门禁`35/45 & 10/15 & undetected==0`+claim boundary含`45块最小规模`与`development confirmation`），`v53_invalid_notice.json`（失败时）。禁写NPZ。P0轮SHALL NOT创建上述输出。

## R11. Integrity, guard ordering, seed registry, and execution deviation prevention

Runner SHALL三层：Tier0拒绝（默认拒绝、`--execution-authorized --authorized-target-sha`与`HEAD==origin/formal-ir-mainline==未来实现SHA`（plan引用`93c12fa5a8524eb5a8a52d071f135c653c746ebaf` revised from `d61d5a3189b...`）、`SCOPED dirty`四文件`v53模块/v53 CLI/v38/v35`、输出根已存在）、Tier1预检失败（J2 已用区间零重叠 per source + 最终45两两非重叠、`H_base rank/support`、`H_inc joint_rank/nested/independence/row≤16/col≤1/leak formula（per_source/overall区分，N_rescue=count(!verify_base)）`、TRAIN counts形态、fresh池`K≥45`且`index_j`分散）、Tier2中途异常保留raw partial。**执行偏差防复发**：执行器SHALL NOT使用600s外部timeout包裹decoder循环（建议≥3600s或不设外部timeout，decoder内部`90/1.0`早停已限时）；若执行返回`session_id/cell_id`，SHALL只轮询同一`session_id/cell_id`进程状态，SHALL NOT重启/重建新session/cell；若执行中断（`BaseException`/`timeout`/`OOM`/`KeyboardInterrupt`），SHALL保留已完成的raw partial（`v53_records.json`已写行与`started/completed`计数）且SHALL NOT生成`v53_summary.json`聚合，`terminal=V53_EVIDENCE_INVALID_INTERRUPTED`，且SHALL NOT自动重跑。P0 spike SHALL仅执行Tier1的decoder-free分支（write-free）且零decoder calls；任一gate失败SHALL `sys.exit(1)`。

## R12. Workload and stop rules（frozen fresh 45, 90-135）

总预算SHALL为`45`块去重`paired`：`L1 45`共享 + `base L2 45`(兼`old`/V53 `pass1`，同一次确定性译码)+`rescue L2 ≤45`(条件)= 总`90-135`硬帽135 (`L2 45-90`)。已删除小预算表述。P0轮SHALL NOT执行任何decoder call。`45块是最小确认规模，过小30块分源仅10不稳定`。

## R13. Records preservation

每解码SHALL一条记录；`base_shared` 45条(兼`old`与V53 `pass1`，不重复译码)，`rescue`至多45条（条件）。总`L2`记录`45-90`条，总调用`45 L1+45 base+≤45 rescue=90-135`硬帽135。Schema含`arm∈{base_shared,rescue}/pass_index/used_increment/matrix_id∈{base,joint}/h1_matrix_id/frame_ids[4]/held_out_ordinal/sampling_mode/max_iter 90/damping 1.0/errors_initial/final/exact_u1/exact_l2/exact_full/syndrome_ok/tag_ok/tag_scope/reclassified/target_tag/candidate_tag/iterations/bp_posterior_entropy/mean_abs_diff/leak_total(1064/1094/1104或1104/1134/1144)/leak_joint/status/runtime`（`old_exact`派生自`base_shared`，不另记录）。Prior仅`TRAIN`。

## R14. Claim boundary

结果仅支持`n=1024 m2=184/190/192 Δm=8`上`H_joint=[H_base;H_inc]嵌套增量`在`45` fresh held-out块（每源15，4帧=1024 pairs，`deterministic_four_consecutive_frames_heldout_fresh_v53`经剩余窗口`K-1`分散`index_j=floor(j*(K-1)/14)`选择，与已用360帧零重叠，两两非重叠）在`90-135` calls上的有界rescue归因（首遍冻结Lane C原support/标签/prior/MET图不改，`90/1.0 poly37 early-stop, leak_base 1064/1094/1104, leak_joint=leak_base+40，first_pass_success已成功帧不增泄漏(1064/1094/1104)，rescued与final_failure均为leak_joint(1104/1134/1144)，per_source_avg[s]=leak_base[s]+40×N_rescue_attempted[s]/15，overall_avg=(Σ leak_base[source(block)]+40×N_rescue_total)/45（`N_rescue_total=count(!verify_base)`，因三源`leak_base`不同禁单一`leak_base+40N/45`当`overall`），rescue_rate=rescued/N_rescue_attempted（`N_rescue_attempted=count(!verify_base)`禁`45-base_exact`，`base_exact_full`与`verify_base`分别报告），disclosure_per_final_exact_block=total_disclosed_bits/final_exact_full_count（为0则null，删除含糊final_accepted_bits，f_avg若保留分母1024×(H(U1|B)+H(U2|U1,B))）`，总`90-135硬帽135(old与pass1同一次确定性译码不重复), joint rank==m2+8 nested independence==8 row≤16 col≤1 确定性构造不触outcomes, L2-only tag≈2^-64`），`exact_full` oracle不经tag；`V52 12/15`仅历史描述；均非FER/阈值/SKR/安全/资格/晋升证据；`45块为最小确认规模，30块分源仅10不稳定；V53通过仍仅development confirmation，下一阶段qualification需新采集/独立TEST`；不启动下一阶段。

## R15. Lifecycle

本变更lifecycle SHALL保持`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`直至独立plan ACCEPT；P0先产decoder-free样本注册表（含45块`K/index_j`分散+零重叠校验）与嵌套矩阵复核报告与四工件，不提交正式输出；`implementation_started=false`, `production_outputs_created=false`。SHALL NOT启动下一阶段，且SHALL NOT运行decoder或创建`run_01`。
