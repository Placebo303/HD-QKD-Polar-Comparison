# Delta Specification: formal-ir-v50-l2-structure-factorial

**Cycle**: `V50P0`
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V51。等待独立评审。**
**Predecessor**: V48 result `28228b9d` + diagnostic `f58955f3e794dbde11b4d813eec061182319846d` (deprecated), branch `formal-ir-mainline` plan HEAD `d95d46ac559ac9e5860ebcc793abc0500ba9b09b`
**Mechanism id**: `p0_met_single_equal_leakage_protograph_met_with_train_vs_trainval_prior_factorial`
**Tag source**: `v35:compute_tag_64(empty,x2)` (`empty=np.empty(0,dtype=np.uint8)`, `hex[:16]` trunc64, `tag_scope=l2_only`)
**HEAD**: `d95d46ac559ac9e5860ebcc793abc0500ba9b09b`（plan SHA；实现冻结时重绑至未来 implementation SHA，旧 `f58955f...` 已弃用）
**H1 provenance**: `V31-H1-QC-16×1024 rank16 80b`
**Candidate**: `P0-MET-1 p0_met_{1M,1p5M,2M}_det1`, `n=1024, m2=184/190/192`, `GF32 poly37`, 真 MET `{dv2:512,dv3:512} E=2560 dc_mean 2.5`（全 `dv2` 则 `PEG-dv2 E=2048`），`dc_max=16`, `support_cycles_4==0`

## R1. Predecessor binding

V50 SHALL 仅基于 V38 Lane C 常量与 V35 tag 原语规划，复用 `n=1024` 与 `m2` 定义，不读取 V48 outcomes 选结构或阈值。V50 SHALL 冻结 `P0-MET-1` 单一等泄漏真 MET 候选 `{dv2:512,dv3:512} E=2560` 与 `lane_c` 3 矩阵 ordinal-2 + `90/1.0 poly37` + `H1-16 80b` + L2-only `compute_tag_64(empty,x2)` + 四类 `G3'=undetected==0` 不变。V50 SHALL 为 15 未使用 held-out 块的 2×2 因子实验（结构×先验，共 90 calls）规划。V50 SHALL NOT 启动 V51，实现前需独立 plan ACCEPT + 显式 `EXECUTE_AUTH`（绑定 `formal-ir-mainline`、未来实现 SHA，plan 引用 `d95d46ac559ac9e5860ebcc793abc0500ba9b09b`，旧 `f58955f...` 已弃用）。Spike 脚本任一 gate 失败 SHALL `sys.exit(1)` 非零退出。

## R2. Single equal-leakage protograph/MET candidate — P0-MET-1 (no seed search)

本变更 SHALL 仅评估单一冻结候选 `P0-MET-1`：每源 `m2×1024` (`184/190/192`), `GF32 poly37`, `无零列` (`col_degree` 分布 `{dv2:512,dv3:512}` 无零列), `满行秩` (`rank_GF32==m2`), `E==2560`（全 `dv2` 则 `PEG-dv2 E==2048` 并改名）、`row_degree_max≤16`, `support_cycles_4==0` 硬门、`6/8-cycles` 报告（含 `pure_4/6/8` 仅作报告）、`max_degree2_chain≤4` 且 `degree2_pure_ring(len≤12)==0` 硬门（`G2` 精确、唯一权威 `pure_ring_via_graph`：链为 `G2` 内内部校验度 2 的极大路径，环为双分长度 `≤12` 且环上校验在 `G2` 内度均为 2 的全 `dv=2` 闭环；枚举 `pure_*` 双计数已清理）、确定性 lifting/label（含跨度层 4-cycle avoidance 修复）、禁止 seed 搜索、与 Lane C 相同 `m2` 与泄漏 `1064/1094/1104` (5·m2+80+64, 与 `E` 无关) 及 `f_total=leak/[N(H1+H2)] N=1024`、相同 decoder `90/1.0`。SHALL NOT 改 `m2/leak/max_iter/damping`、不引入第二候选。矩阵 SHALL 经确定性 PEG-MET 规则单次重建并与 spike §4 严格比对；脚本报告数值 SHALL 由 `spike_construct.py` 直出且 gate 失败时非零退出。

## R3. Factorial workload — 90 calls on 15 unused held-out blocks with TRAIN vs TRAIN+VAL prior

Workload SHALL 为 `15` 未使用 held-out 块 × `6`=90 decoder calls：每块 `L1_T 1 + L1_TV 1 + L2_{A,B,C,D} 4`（`A=TRAIN×LaneC, B=TRAIN+VAL×LaneC, C=TRAIN×P0, D=TRAIN+VAL×P0`），`L1 30` + `L2 60` records。与 `FORBIDDEN 141` block ID 零重叠 per source、连续、均分（每源5 `391001..`/`391101..`/`391201..`）且每块写死 `4` 真实 `frame_ids` 与 `held_out_ordinal_start/end`（design §2.4 冻结表）与 V48 180 帧 `frame_ids` 零重叠 per source 可机械校验、每块 `4 frames=1024 pairs (256/frame)`、`sampling_mode=deterministic_four_consecutive_frames_heldout_unused`。每块 L1 双 prior 同 `bob` 不同 `counts` (`counts_T` vs `counts_TV=TRAIN⊕VAL`)；每块 4 L2 同 `bob` 派生 `P_i(U2)=Σ q_i P(U2|B,u1)` 与各自 `H_L2` syndrome。SHALL NOT 复用 V48 45 块的任何 `frame_ids`、SHALL NOT 用 `sample_empirical_block` 随机池作正式样本（FAKE 测试除外）。

## R4. Leakage and tag provenance — frozen equal leakage

Tag SHALL 为 `compute_tag_64(empty_uint8,x2)` trunc64 直复用，不另行归一化；`tag_scope` 恒 `l2_only`。泄漏 SHALL 固定：`H1-16 1064/1094/1104` 等泄漏于 Lane C；P0 同 `m2` 同泄漏（`E=2560` 与泄漏无关）。Summary SHALL 声名 `leakage_already_accounted` 与工程 verification L2-only.

## R5. Four-way reclassification

`wrong_codeword = syndrome_ok && !exact` 仍为 LDPC 错误陪集解。Verification 后 SHALL 四类互斥重分类：`exact` (`exact_l2`), `detected` (`syndrome_ok&&!exact&&!tag_ok`), `decoder_non_syndrome` (`!syndrome_ok&&!exact`), `undetected` (`tag_ok&&!exact`, `≈2^-64` 工程近似，下文 R7). `L1 wrong` 单独报告不入四类.

## R6. Oracle truth preserved

`exact_l2/exact_u1` SHALL 仍为 oracle 判真，`exact_full=exact_u1&&exact_l2` 为主判据，同时报告 per factor/per source。`tag_ok` (L2-only) SHALL NOT 覆盖 `exact_*`.

## R7. Pre-tag timing and G3' (descriptive)

`wrong_codeword/exact` SHALL 在 verification 之前计算。`G3'` SHALL 为 `undetected==0` 描述性报告，不作晋升门禁。`≈2^-64` 仅随机哈希模型工程近似，不宣称信息论界。

## R8. Outputs unchanged

V50 SHALL NOT 修改任何 V38–V48 已有输出；既有文件 byte-identical。V50 证据 SHALL 隔离于 `.../v50_l2_structure_factorial/run_01/`，fail-closed。Tag SHALL 直接 import `v35.compute_tag_64`；prior SHALL 分别 `counts_T` / `counts_TV`.

## R9. Evidence outputs — minimal fixed set (future, not in P0)

授权写出 SHALL 仅为：`v50_records.json/.csv` (60 L2 行含 `prior_id/structure_id/tag_ok/reclassified/leak/frame_ids/held_out_ordinal/sampling_mode`), `v50_summary.json` (含分层记账 90 + 因子聚合 主效应 `E_structure/E_prior/E_interaction` 与四个 simple effects + 四类/G3' + `f_total` + provenance 等泄漏 P0 `{dv2:512,dv3:512}` 与双 prior + 未使用 held-out 溯源含每块 `frame_ids/ordinal`), `v50_invalid_notice.json`(失败时). 禁写 NPZ。P0 轮 SHALL NOT 创建上述输出.

## R10. Terminal distinguishability — factorial complete (descriptive)

Summary 终态 SHALL 为：`V50_EVIDENCE_INVALID` 优先、`V50_FACTORIAL_COMPLETE` (描述性完成, orthogonal `structure_gain/due` 仅旗标). SHALL NOT 设 `V48_HELDOUT_PASS` 式晋升门禁.

## R11. Integrity, guard ordering, seed registry 141, and tiers

Runner SHALL 三层：Tier0 拒绝（默认拒绝、`--execution-authorized --authorized-target-sha` 与 `HEAD==origin/formal-ir-mainline==未来实现SHA`（plan 引用 `d95d46ac...`，旧 `f58955f...` 已弃用）、`SCOPED dirty` 四文件 `v50 模块/v50 CLI/v38/v35`、输出根已存在）、Tier1 预检失败（J2 141 并集 96+45 新区 15 block ID 零重叠且与 V48 180 帧 `frame_ids` 零重叠、`P0 rank/dc/E/4-cycle/chain-ring(G2精确, graph权威)`、双 prior counts 形态、未使用池可达）、Tier2 中途异常保留 raw partial。P0 spike SHALL 仅执行 Tier1 的 decoder-free 分支（write-free）且零 decoder calls；任一 gate 失败 SHALL `sys.exit(1)`。

## R12. Workload and stop rules (frozen 90)

总预算 SHALL 为 `90` (`L1 30 + L2 60: 15×(2+4)`) `A,B,C,D` 每块序 `A→B→C→D`、源 `1M→1p5M→2M`、块升序。第 91 call 结构拒（J10）；恰好一次、无 rerun/resume。P0 轮 SHALL NOT 执行任何 call。

## R13. Records preservation

每 L2 SHALL 一条记录共 60 条，schema 含 `prior_id/structure_id/matrix_id/h1_matrix_id/frame_ids[4]/held_out_ordinal/sampling_mode/max_iter 90/damping 1.0/errors_initial/final/exact_* /syndrome_ok/tag_ok/tag_scope/reclassified/target_tag/candidate_tag/iterations_l1/l2/bp_posterior_entropy/mean_abs_diff/leak_total`. Prior 仅 `TRAIN`/`TRAIN+VAL`，结构仅 `lane_c`/`p0_met`.

## R14. Claim boundary

结果仅支持 `n=1024 m2=184/190/192` 上单一等泄漏真 MET P0-MET-1 `{dv2:512,dv3:512} E=2560 dc_mean 2.5`（全 `dv2` 则 `PEG-dv2 E=2048`）与 `TRAIN vs TRAIN+VAL` 在 15 未使用 held-out 块上的 2×2 有界因子归因（`90/1.0 poly37, early-stop, leak 1064/1094/1104 与E无关, dc_max=16 4-cycles==0 6/8 报告 链≤4 纯环≤12==0(G2精确) 满秩无零列 确定性 label 禁 seed 搜索 构造不触 V48 L2-only tag≈2^-64`），`exact_full` oracle 不经 tag；均非 FER/阈值/SKR/安全/资格/晋升证据；不启动 V51。

## R15. Lifecycle

本变更 lifecycle SHALL 保持 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` 直至独立 plan ACCEPT；P0 先产 spike 报告与四工件，不提交正式输出；`implementation_started=false`, `production_outputs_created=false`。SHALL NOT 启动 V51。
