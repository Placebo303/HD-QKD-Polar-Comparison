# Delta Specification: formal-ir-v52-rate-adaptive-l2-rescue

**Cycle**: `V52P0`
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行 decoder，不创建 run_01。等待独立评审。**
**Predecessor**: `6aa33eadc872bb4551f458ee750a94cd24566314` (branch `formal-ir-mainline` plan HEAD)
**Mechanism id**: `nested_incremental_l2_rescue_delta8_conditional_harq`
**Tag source**: `v35:compute_tag_64(empty,x2)` (`empty=np.empty(0,dtype=np.uint8)`, `hex[:16]` trunc64, `tag_scope=l2_only`)
**HEAD**: `6aa33eadc872bb4551f458ee750a94cd24566314`（plan SHA；实现冻结时重绑至未来 implementation SHA）
**H1 provenance**: `V31-H1-QC-16×1024 rank16 80b`
**Candidate**: `H_base Lane C ordinal-2 (m2=184/190/192) + H_inc det1 8×1024 GF32 poly37 joint m2+8=192/198/200, row≤16, nested, rank_joint==m2+8`

## R1. Predecessor binding

V52 SHALL 仅基于 V38 Lane C 常量与 V35 tag 原语与 V31 H1 规划，复用 `n=1024` 与 `m2/leak_base` 定义，不改首遍 support/标签/prior/MET 图/decoder，不读取 V48/V50/V51 outcomes 选 `Δm` 或增量位置。V52 SHALL 冻结首遍 `H_base` 3 矩阵 ordinal-2 + `H_inc 8×1024` 嵌套增量 + `90/1.0 poly37` + `H1-16 80b` + L2-only `compute_tag_64(empty,x2)` + 两遍条件协议 + 15 fresh held-out paired workload。V52 SHALL NOT 启动 V53，实现前需独立 plan ACCEPT + 显式 `EXECUTE_AUTH`（绑定 `formal-ir-mainline`、未来实现 SHA，plan 引用 `6aa33eadc872bb4551f458ee750a94cd24566314`）。Spike 脚本任一 gate 失败 SHALL `sys.exit(1)` 非零退出，且 SHALL NOT 运行 decoder。

## R2. Frozen first pass (no change)

首遍 SHALL 冻结：`n=1024, m2=184/190/192, GF32 poly37, Lane C support/label/position_permutations, m1=16, leak_base=5*m2+80+64 →1064/1094/1104`；`H1 16×1024 rank16` 复用 `nonbinary_v31.build_matrix_packet`；`prior TRAIN` via `load_v25_channel_counts()` → `BP_i` → `q_i` → `P_i(U2)`；`decoder 90/1.0` early-stop；`verification = syndrome_ok && tag_ok` L2-only；`exact_full=exact_u1&&exact_l2` oracle。SHALL NOT 改首遍任何矩阵/先验/标签/MET/译码/泄漏。

## R3. Incremental nested matrix — Δm=8 (no seed search, no second candidate)

本变更 SHALL 仅评估单一冻结增量 `H_inc det1 8×1024` per source：`GF32 poly37`, `col_degree_inc∈{0,1}`, `row_degree≤16`, `无零增量行`, `E_inc` 报告，`H_joint=vstack([H_base,H_inc])`。SHALL 满足：`rank_GF32(H_joint)==m2+8`，`H_base == H_joint[0:m2,:]` 嵌套逐比特相等，`rank_increment==8`（独立性）。构造 SHALL 为确定性 PEG-增量 `SeedSequence([60000x,1/2/3])` 单次重建并与 spike §4 严格比对；`syndrome_base` 为 `syndrome_joint` 前缀。SHALL NOT 改 `Δm`、不引入第二增量候选、不搜 seed、不调行度上限、不以 outcomes 定增量。

## R4. Leakage and conditional disclosure — avg vs failed-conditional

Tag SHALL 为 `compute_tag_64(empty_uint8,x2)` L2-only。泄漏 SHALL 冻结：`leak_base=5*m2+80+64`；`leak_joint=5*(m2+Δm)+80+64 = leak_base+40`。`leak_joint - leak_base = 5*Δm =40` 恒。Summary SHALL 承诺报告：`average_leakage = (N_first_success*leak_base + N_attempt_increment*leak_joint)/N`（`N=15`, `N_attempt_increment = N - N_first_success`，含救回与仍失败）；`failed_conditional_leakage = leak_joint`（最终失败帧均已尝试增量）；`successful_conditional_leakage = leak_base`；`f_avg = avg_leak / [N_blocks*(entropy)]` 描述性。已成功帧 SHALL NOT 增加泄漏。

## R5. Two-pass conditional protocol

每块 V52 臂 SHALL 执行：`pass1 = decode(H_base, P(U2), s_base)` → `verify1 = syndrome_ok_pass1 && tag_ok_pass1`；若 `verify1` 则停，`final_exact = exact_pass1`，`leak=leak_base`，`used_increment=False`；否则 `s_inc = H_inc * u2_true`，`s_joint=[s_base;s_inc]`，`pass2 = decode(H_joint, P(U2), s_joint)` → `verify2`，`final_exact = exact_pass2`，`leak=leak_joint`，`used_increment=True`，`rescued = (!verify1 && verify2 && final_exact)`。`old` 臂 SHALL 单遍 `decode(H_base)` 同 `bob/P(U2)`。`exact_*` SHALL 为 oracle `array_equal`，`tag_ok` 为真实 L2-only 哈希验收；公开成功以 `tag_ok` 判，`exact` 仅 oracle 统计但两者均报告。

## R6. Fresh held-out paired workload — 15 blocks old vs V52

Workload SHALL 为 `15` fresh held-out 块 的 paired 比较：每块共享 `L1` (`q_i`/`P(U2)`)，`old` 单遍 vs `V52` 首遍+条件二遍，同 `bob` 同 prior (TRAIN)，同 `H1`。与 `FORBIDDEN 171 = 96(V36..V47)+45(V48)+15(V50 391xxx)+15(V51 392xxx)` block ID 零重叠 per source 连续均分 `393001..`/`393101..`/`393201..` 且每块写死 `4` 真实 `frame_ids` 与 `held_out_ordinal_start/end`（design §2.4）与 V48/V50/V51 `frame_ids` 零重叠 per source 可机械校验、`sampling_mode=deterministic_four_consecutive_frames_heldout_fresh`、`pairs 1024`。SHALL NOT 复用 V48/V50/V51 的任何 `frame_ids`、SHALL NOT 用 outcomes 选块。SHALL NOT 重复比较 prior、标签或另一 MET 图。

## R7. Reporting promises — SHALL (explicit)

Summary SHALL 显式包含（overall 与 per-source 1M/1p5M/2M）：`first_pass_success_count`，`incremental_rescue_count (rescued_by_increment)`，`final_exact_full (V52)`，`old_exact_full`，`rescue_rate` 描述性；`per_source` 分解；`average_leakage`，`failed_conditional_leakage (leak_joint)`，`successful_conditional_leakage (leak_base)`，`f_avg/f_failed`；`joint_rank==m2+8`，`nested==True`，`independence==8`，`row_degree_max≤16`，`E_inc`；`real_tag_acceptance (tag_ok rate per pass)`；`paired_old_vs_incremental` per block (`Δexact = final_V52 - old`，McNemar `b/c` 仅描述)。以上 SHALL 在 proposal/design/tasks/specs 中显式承诺且在 summary 中兑现。

## R8. Outputs unchanged

V52 SHALL NOT 修改任何 V38–V51 已有输出；既有文件 byte-identical。V52 证据 SHALL 隔离于 `.../v52_rate_adaptive_l2_rescue/run_01/`，fail-closed。Tag SHALL 直接 import `v35.compute_tag_64`；prior SHALL 为 `TRAIN` 单一。

## R9. Evidence outputs — minimal fixed set (future, not in P0)

授权写出 SHALL 仅为：`v52_records.json/.csv`（≤45 L2 行：15 old + ≤30 V52 pass1/pass2，含 `arm/pass_index/used_increment/matrix_id/joint/leak_total/leak_joint/frame_ids/ordinal/sampling_mode/tag_ok`），`v52_summary.json`（含 `first/rescued/final/old` 分层 + 每源 + 平均/条件泄漏 + `f_*` + `joint_rank/nested/independence/E_inc/row_max` + paired `Δexact` + 四类/G3' + 终态 + `leakage_formula`），`v52_invalid_notice.json`（失败时）。禁写 NPZ。P0 轮 SHALL NOT 创建上述输出。

## R10. Terminal distinguishability — nested rescue complete (descriptive)

Summary 终态 SHALL 为：`V52_EVIDENCE_INVALID` 优先、`V52_NESTED_RESCUE_COMPLETE`（描述性完成，`rescue_gain = final_V52 > old` 仅旗标）。SHALL NOT 设晋升门禁。

## R11. Integrity, guard ordering, seed registry 171, and tiers

Runner SHALL 三层：Tier0 拒绝（默认拒绝、`--execution-authorized --authorized-target-sha` 与 `HEAD==origin/formal-ir-mainline==未来实现SHA`（plan 引用 `6aa33ead...`）、`SCOPED dirty` 四文件 `v52 模块/v52 CLI/v38/v35`、输出根已存在）、Tier1 预检失败（J2 171 并集 新区 15 block ID 零重叠 per source + 与 V48/V50/V51 `frame_ids` 零重叠、`H_base rank/support`、`H_inc joint_rank/nested/independence/row≤16/col≤1/leak formula`、TRAIN counts 形态、fresh 池可达）、Tier2 中途异常保留 raw partial。P0 spike SHALL 仅执行 Tier1 的 decoder-free 分支（write-free）且零 decoder calls；任一 gate 失败 SHALL `sys.exit(1)`。

## R12. Workload and stop rules (frozen fresh 15)

总预算概念上 SHALL 为 `15 块 paired old vs V52`：`L1 15` 共享 + `L2 old 15` + `L2 V52 pass1 15` + `L2 V52 pass2 ≤15 (条件)`。P0 轮 SHALL NOT 执行任何 decoder call。

## R13. Records preservation

每解码 SHALL 一条记录；`old` 臂 15 条，`V52 pass1` 15 条，`V52 pass2` 至多 15 条（条件）。Schema 含 `arm∈{old,V52_pass1,V52_pass2}/pass_index/used_increment/matrix_id∈{base,joint,inc}/h1_matrix_id/frame_ids[4]/held_out_ordinal/sampling_mode/max_iter 90/damping 1.0/errors_initial/final/exact_u1/exact_l2/exact_full/syndrome_ok/tag_ok/tag_scope/reclassified/target_tag/candidate_tag/iterations/bp_posterior_entropy/mean_abs_diff/leak_total/leak_joint/status/runtime`。Prior 仅 `TRAIN`。

## R14. Claim boundary

结果仅支持 `n=1024 m2=184/190/192 Δm=8` 上 `H_joint=[H_base;H_inc] 嵌套增量` 在 `15` fresh held-out 块上的有界 rescue 归因（首遍冻结 Lane C 原 support/标签/prior/MET 图不改，`90/1.0 poly37 early-stop, leak_base 1064/1094/1104, leak_joint+40 已成功帧不增泄漏, joint rank==m2+8 nested independence==8 row≤16 col≤1 确定性构造 不触 outcomes, L2-only tag≈2^-64`），`exact_full` oracle 不经 tag；均非 FER/阈值/SKR/安全/资格/晋升证据；不重复 prior/标签/MET 对比；不启动 V53。

## R15. Lifecycle

本变更 lifecycle SHALL 保持 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` 直至独立 plan ACCEPT；P0 先产 decoder-free 嵌套 spike 报告与四工件，不提交正式输出；`implementation_started=false`, `production_outputs_created=false`。SHALL NOT 启动 V53，且 SHALL NOT 运行 decoder 或创建 `run_01`。
