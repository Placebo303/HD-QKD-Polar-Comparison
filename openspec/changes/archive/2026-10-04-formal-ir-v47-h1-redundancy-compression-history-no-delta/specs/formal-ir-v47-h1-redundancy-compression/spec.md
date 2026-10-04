# Delta Specification: formal-ir-v47-h1-redundancy-compression

**Cycle**: `V47P0`
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V48。等待独立评审。**
**Predecessor**: V46 `formal-ir-v46-verification-semantics` (result SHA `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`, branch `formal-ir-mainline`, 27-call verification)
**Investigation**: `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`（V46 Treatment `H1-16` 7/9 类增益 verification 下复现；V47 仅压缩 H1 冗余 `m1=8/12/16`，54-call 三臂 fresh-block）
**Mechanism id**: `l1_app_soft_transfer_H1_prefix_{8,12,16}_syndrome_derived_with_v35_tag_l2_only`
**Tag source**: `v35:compute_tag_64(empty,x2)`（`empty=np.empty(0,dtype=np.uint8)`, `b1+b2 → SHA256 → hex[:16]` trunc64, `tag_scope=l2_only`）
**HEAD**: `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`
**H1 provenance**: `V31-H1-QC-16×1024 (rank16, QC-cyclic-projective, GF32 poly37)` 前缀 `H1_8⊂H1_12⊂H1_16`，满行秩 `8/12/16` 已验证

## R1. Predecessor binding

V47 SHALL 仅基于 V46 已验收路径与 V35 tag 原语规划。V47 SHALL 冻结 Lane C 三矩阵 ordinal-2、`L2 90/1.0 poly37`、L1APP 公式 `p_i=P(U1|B), s1=H1·u1, q=softmax BP posterior, P_i(U2)=ΣqP(U2|B,u1)`、L2-only `compute_tag_64(empty,x2)`、V46 四类 `exact/detected/decoder_non_syndrome/undetected` 与 `G3'=undetected==0` 不变。V47 SHALL NOT 改写 V46 输出，V46 仍保留原终态。V47 SHALL 为 fresh-block H1 压缩（54 invocations 三臂），回答“能否用更小 `m1` 通过同等 `exact_full` 门禁”。V47 SHALL NOT 启动 V48，实现前需独立 plan ACCEPT + 显式用户 `EXECUTE_AUTH`（绑定 repository、分支 `formal-ir-mainline`、实现 SHA、cycle V47P0、scope `v47_diagnostic_54_invocations_h1_redundancy_exactly_once`，HEAD `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`）。

## R2. Single variable — H1 prefix nested 8/12/16 (only change)

本变更 SHALL 仅改变一个变量：`H1^{m1}` 行数 `m1∈{8,12,16}`（`40/60/80 bits`），定义为 `V31-H1-QC-16×1024` 的**行前缀**：`H1_16=V31_H1`, `H1_12=H1_16[:12,:]`, `H1_8=H1_16[:8,:]`，满足 `H1_8⊂H1_12⊂H1_16` 且 `rank 8/12/16` 已验证（可行性核查通过，GF32 poly37, `capacity_ok/projective_safe` 继承）。SHALL NOT 改 Lane C L2、不改 `90/1.0`、不改 decoder、不引入第二变量。`s1^{m1}=H1^{m1}·u1^Alice` 计泄漏 `5·m1`。

## R3. Fresh-block workload — 54 invocations three-arm with real L2-only tag

Workload SHALL 为 **fresh-block 54 decoder invocations**（`9 块 ×3 臂 ×2 =54`：每块每臂 `L1 BP 1 + Treatment L2 1`），其中 L1 `27` 次、L2 `27` 条 records（每臂 9）。每块样本 SHALL 确定性采样一次并被三臂共享；同块三臂同 `bob/counts`、同 `H_L2`（该源 lane_c ordinal-2）、同 `90/1.0 poly37`，差异仅 `H1^{m1}/s1^{m1}/q_i^{m1}`。每条 L2 record 在解码后 SHALL 实际生成 `target_tag=compute_tag_64(empty_uint8,x2_true)`、重算 `candidate_tag=compute_tag_64(empty_uint8,x2_hat)`（`empty=np.empty(0,dtype=np.uint8)`，复用 V35 `compute_tag_64` 的 `b1+b2→SHA256→hex[:16]`），保存 `target_tag/candidate_tag/tag_ok/tag_scope=l2_only/arm/h1_rows/leak_total_this_arm`，SHALL NOT 要求保存完整 `x_hat`。**改变 `x1_true` SHALL NOT 改变任一臂 L2 tag；改变 `x2` SHALL 改变锚点 tag**。三臂均为 Treatment 形态（L1APP + L2-only verification），SHALL NOT 运行 V43 Control（`P(U2|B)`），对照为 `H1-16`。SHALL NOT 复用历史 87 块。

## R4. Source, leakage, and tag provenance — frozen via V35 L2-only with H1 prefix

Tag 来源 SHALL 为 `x2` 经 V35 `compute_tag_64(empty,x2)` 的 canonical bytes（`empty=np.empty(0,dtype=np.uint8)`，`hex[:16]` 截断），直接复用该函数，不另行归一化，不宣称 symbols 等价；`tag_scope` 恒 `l2_only`。泄漏 SHALL 为 `leak_total=5·m2+5·m1+64`（`m2=184/190/192 →920/950/960`，`m1=8→40,12→60,16→80`）：
- `H1-8:  1024/1054/1064`
- `H1-12: 1044/1074/1084`
- `H1-16: 1064/1094/1104`（基线，与 V46 一致）
`f_total=leak_total/[N(H1+H2)] N=1024`。Summary SHALL 显式声名 `leakage_already_accounted` 与工程 verification L2-only。三臂非等泄漏比较仅为 H1 冗余压缩价值。

## R5. Four-way reclassification — exact / detected / decoder_non_syndrome / undetected (per arm)

`wrong_codeword = syndrome_ok && !exact` 仍为 LDPC 错误陪集解。Verification（L2-only）后 SHALL per-arm 四类互斥穷尽重分类：
- `exact` — `exact_l2==true`（必 `tag_ok==true`）
- `syndrome_ok && !exact && !tag_ok → detected_verification_failure`（计为 rejected / 非 exact）
- `!syndrome_ok && !exact → decoder_non_syndrome_failure`（不单归因结构）
- `tag_ok && !exact → undetected_accepted_wrong`（`≈2^-64` 工程近似，下文 R7）

`detected` SHALL 计作非 exact/rejected，不计 exact。`L1 wrong`（`syndrome_ok_l1 && !exact_u1` / `!syndrome_ok_l1`）SHALL 单独报告，不入四类。

## R6. Oracle truth preserved — exact_full gate, tag L2-only

`exact_l2` 与 `exact_u1` SHALL 仍为 oracle 判真（vs `u_true/x_true`），`exact_full=exact_u1&&exact_l2` 为门禁主判据，同时报告 `exact_u1/exact_l2/exact_full` per arm/per source。Verification 的 `tag_ok`（L2-only）SHALL NOT 覆盖或重定义 `exact_*`。Summary SHALL 同时报告 `exact_*` 与 `verification_accept (tag_ok)`，不得宣称提升 decoder exact rate。`tag_ok==false` 的记录 SHALL 计作非 exact。**本轮 tag 只验 L2，不代表完整 `(U1,U2)` 帧验证；`exact_full` 仍 oracle，不经 tag。**

## R7. Pre-tag timing and G3' per arm — undetected_accepted_wrong ==0

`wrong_codeword_l2 / exact_l2` SHALL 保持在 verification 之前计算（pre-tag），verification（L2-only `empty+x2`）仅在其后追加 `tag_ok` gate。

**G3' per arm**：每臂 `X∈{h1_8,h1_12,h1_16}` 的 G3' SHALL 为 **`undetected_accepted_wrong==0`**（`tag_ok&&!exact` 计数 0），SHALL NOT 要求 decoder 永不产生 `syndrome_ok&&!exact` — 被捕获为 `detected` 时 G3' 仍可通过。G3' 仅 `undetected` 触发。`tag_match&&!exact≈2^-64` 仅随机哈希模型工程近似（L2-only），spec SHALL 说明固定公开 SHA-256 截断局限与 `universal2+seed` 边界。门禁为 `G1 exact_full≥7/9` 且 `G2 每源 exact_full≥2/3` 且 `G3' undetected==0`。

## R8. Outputs unchanged — V46 byte-identical, V35 tag L2-only, H1 prefix frozen

V47 SHALL NOT 修改任何 V46 已有输出；V46 `results/` 与 `comparison_bench/outputs_comparison/` 下既有文件 SHALL 保持 byte-identical（mismatch 即 `V47_EVIDENCE_INVALID`）。V47 证据 SHALL 隔离于新根 `comparison_bench/outputs_comparison/formal_ir_methods/v47_h1_redundancy_compression/run_01/`，fail-closed 若已存在。Tag 实现 SHALL 直接 import `v35_algorithm_development.compute_tag_64` 并以 `empty=np.empty(0,dtype=np.uint8)` 调用；H1 实现 SHALL 经 `nonbinary_v31.build_matrix_packet` 前缀切片，不另行构造矩阵。

## R9. Evidence outputs — minimal fixed set with per-arm tag and H1 prefix

授权写出 SHALL 仅为最小固定集：`v47_records.json/.csv`（27 行 fresh-block 记录，含 `arm/h1_rows/target_tag/candidate_tag/tag_ok/tag_scope=l2_only/reclassified/exact_u1/exact_l2/exact_full/leak_total_this_arm/iterations_l1/iterations_l2/bp_posterior_entropy/mean_abs_diff_q_p`）、`v47_summary.json`（含 per-arm/per-source 四类计数 `exact/detected/decoder_non_syndrome/undetected`、`undetected` 即 G3'、`exact_full/ exact_u1/ exact_l2`、`leakage_already_accounted` 三臂 `1024/1054/1064 vs 1044/1074/1084 vs 1064/1094/1104` + `f_total` + 工程 verification L2-only 声名 `SHA-trunc64 random-hash-model approximate 2^-64, not information-theoretic; strict bound requires universal2+seed; tag_scope=l2_only`、provenance 含 H1 前缀 `8/12/16 rank 8/12/16` 与 tag 源 `v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only`、first-match 终态）、失败时 `v47_invalid_notice.json`；CSV/JSON 行对等；SHALL NOT 写任何 NPZ；输出根在全部守卫通过后创建。每条记录 SHALL 保存 `arm/h1_rows/tag_ok/tag_scope`，SHALL NOT 要求保存完整 `x_hat`。

## R10. Terminal distinguishability — first-match minimal m1 with per-arm four-way

Summary 终态 SHALL 为 first-match 最小 `m1`：
- `V47_H1_8_RETAINED`（`pass_h1_8`）
- `V47_H1_12_RETAINED`（`!pass_h1_8 && pass_h1_12`）
- `V47_H1_16_ONLY`（`!pass_h1_8 && !pass_h1_12 && pass_h1_16`）
- `V47_NO_H1_SIZE_RETAINED`（三臂均 fail）
- `V47_EVIDENCE_INVALID` 优先
其中 `pass_X` 为 `G1 exact_full≥7/9 && G2 每源≥2/3 && G3' undetected==0` per arm。Summary SHALL 可区分每臂四类 `exact/detected/decoder_non_syndrome/undetected` 与 `L1 wrong` 单独表，G3' 为 `undetected==0`（L2-only）。`V47_EVIDENCE_INVALID` 优先；穷尽互斥 first-match。

## R11. Integrity, guard ordering, seed registry 87, and tiers

Runner SHALL 实现三层：
- **Tier 0 拒绝**（默认拒绝、必带 `--execution-authorized --authorized-target-sha`、HEAD 精确等值 `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`、SCOPED tracked-dirty 四文件 `v47 模块/v47 CLI/v38 模块/v35 模块（含 tag 源）`、输出根已存在）最先、不创建文件、非零退出、零 calls。
- **Tier 1 预检失败**（J2 87 并集：78 (V36_A3/V39/V40/V41/V42/V43/V44/V45) + V46 9 =87，新区 9 零重叠 `390125-127/225-227/325-327`；J3 H1 母矩阵+三前缀 `8/12/16` 秩/切片双重建；J4 counts；J5 哨兵含 `h1_prefix_ok` + `v35_tag_import_ok`（L2-only）与 `tag_scope_l2_only` + `leakage_accounted` 三臂）任一失败 SHALL 建增量根写 invalid 三件套后停止，不 rerun；真实 `q≈p` 不作 invalid，`detected` 不作 invalid。
- **Tier 2 中途异常**（`BaseException`）在已建根内保留 raw partial（含 `arm/tag_ok/tag_scope` partial）+ notice + summary 后重抛。

跨臂 outcome 差异永为信号，不作完整性失败；`tag_ok` 跨臂差异亦为信号。`errors_initial` 严格 per-block 三臂等值门（J6）保留。

## R12. Workload, seed registry, and stop rules

总预算 SHALL 为 54 decoder invocations（27 L1 +27 L2: 每臂 `9 L1 +9 L2`），27 L2 records 新块 `390125-127/225-227/325-327`（`C01-C27` 冻结序：源 1M/1p5M/2M、块升序、臂 `h1_8→h1_12→h1_16`）。FORBIDDEN 87 机械零重叠校验 SHALL 在实现时通过（J2）。第 55 call SHALL 结构拒（J10）；恰好一次、无 rerun/resume。Master stop rule SHALL 原文记入 summary：`唯一一次 54-invocation 三臂 H1 前缀配对诊断（含 27 L1 BP +27 L2）fresh-block with V35 SHA-trunc64 L2-only engineering verification (compute_tag_64(empty,x2)[:16], tag_ok gate, tag_scope=l2_only, 4-way reclassified, G3'=undetected==0 per arm, 工程近似 2^-64, exact_full=exact_u1&&exact_l2 oracle, exact_full≥7/9 & 每源≥2/3, first-match 最小 m1)；三臂 H1-8(40b,8×1024) vs H1-12(60b,12×1024) vs H1-16(80b,16×1024) 为 V31 H1 前缀嵌套 rank 8/12/16，对照为 H1-16，仅 Lane C 固定各 source ordinal-2 代表矩阵 + V31 H1 前缀、max_iter=90,damping 1.0 冻结 early-stop 不再调参；每臂 L1APP 按冻结 syndrome-derived APP（p_i=P(U1|B)、s1^{m1}=H1^{m1}·u1^Alice、BP_i^{m1}=decode(H1^{m1},p_i,s1^{m1}).bp_posterior_beliefs / APP approximation、q_i^{m1}=softmax BP_i^{m1}、P_i^{m1}(U2)=Σ q_i^{m1} P(U2|B,u1)、泄漏 H1-8 1024/1054/1064 vs H1-12 1044/1074/1084 vs H1-16 1064/1094/1104 f_total=leak/[N(H1+H2)] N=1024，三臂非等泄漏比较，复用 V35 tag L2-only 不重实现，不做 hard/噪声/量化/失真律/joint 迭代/新矩阵/新 decoder 参数/参数网格/joint GF1024，区分四类 per arm，L1 wrong 单独报告，不追溯 V46，不复用历史 87 块，对照为 H1-16 不运行 V43 Control）后不再更改。`

## R13. Records preservation

每 L2 call SHALL 产一条 fresh-block 记录，共 27 条，schema 含 `arm/h1_rows/condition/tag_ok/tag_scope/reclassified/target_tag/candidate_tag` 四类与 `iterations_l1/iterations_l2/exact_l2/exact_u1/exact_full/syndrome_ok/tag_ok/wrong/leak_total_this_arm` per arm，其中 `tag_scope` 恒 `l2_only` 且 `target_tag/candidate_tag` 均为 `compute_tag_64(empty,x2)`。授权跑 SHALL 仅在增量根 `comparison_bench/outputs_comparison/formal_ir_methods/v47_h1_redundancy_compression/run_01/` 下写 `v47_records.json/.csv` + `v47_summary.json` + 失败时 `v47_invalid_notice.json`；SHALL NOT 写任何 NPZ；SHALL 保存 `arm/h1_rows/tag_ok/tag_scope`，SHALL NOT 要求保存完整 `x_hat`。

## R14. Claim boundary

结果仅支持 V25 TRAIN 经验 counts 开发块上的有界 H1 冗余压缩归因：三臂 `H1-8/H1-12/H1-16` 按 O1 以 V31 H1 前缀 `8/12/16` + 通用 FFT-QSPA `q_i^{m1}=softmax BP posterior / APP approximation` 做真实 syndrome-derived 软转移、L2 在固定 Lane C 三矩阵 ordinal-2 上 90/1.0 单点、`leak_total H1-8 1024/1054/1064 vs H1-12 1044/1074/1084 vs H1-16 1064/1094/1104 (L2 syndrome 920/950/960 + m1·5 +64 tag, f_total, 工程 verification L2-only)`，复用 V35 `compute_tag_64(empty,x2)[:16]`，不改结构/阈值，`undetected≈2^-64` 仅随机哈希模型工程近似（固定公开 SHA-256 截断；严格界需 universal2+seed），三臂非等泄漏比较为更小 `m1` 价值评估；均非真帧 FER 证据，不推阈值/SKR/正式执行/资格/晋升；终态仅方向性 first-match 最小 `m1`，不启动 V48。SHALL NOT 宣称信息论 `2^-64` 安全界、decoder exact rate 提升、FER/阈值/SKR/安全/正式资格/晋升、真帧行为、把同 `errors_final` 等同同码字。

## R15. Lifecycle

本变更 lifecycle SHALL 保持 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` 直至独立 plan ACCEPT；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。SHALL NOT 启动 V48。不追溯修改 V46。任何执行 SHALL 需显式用户 `EXECUTE_AUTH` 绑定到精确实现 SHA 与 HEAD `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`。
