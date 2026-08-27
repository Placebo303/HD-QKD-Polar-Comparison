# OpenSpec Proposal: formal-ir-v47-h1-redundancy-compression

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V48。等待独立评审。**
**Domain**: Formal IR / H1 redundancy compression
**Change ID**: `formal-ir-v47-h1-redundancy-compression`
**Cycle ID**: `V47P0`
**Predecessor**: `formal-ir-v46-verification-semantics` (PLAN_REVISE_REQUIRED → result `DEVELOPMENT_RESULT_ACCEPTED`, result SHA `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`, branch `formal-ir-mainline`)
**Investigation SHA / Branch / HEAD**: `cb4f9990f7864e12dd69c89ee87ec8a58e77470d` / `formal-ir-mainline` (规划冻结时绑定，执行时 `git rev-parse` 精确重绑)
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`
**Feasibility**: V47 可行性核查已全部成立 (H1 前缀嵌套满行秩、V31 H1 物料可用、V46 路径复用、seed 连续性、54-call 预算)

> ponytail lite: 本轮仅单变量 H1 冗余压缩；更懒路径是零新增诊断直接沿用 H1-16，需独立评审确认压缩收益是否值得 54-call 预算。

## Goal

在**完全冻结 V46 已验收路径**的前提下，只改变一个变量——H1 冗余度 `m1 ∈ {8,12,16}`（40/60/80 bits，V31 H1 前缀嵌套、满行秩已验证），回答：

> **在固定 Lane C 三矩阵 ordinal-2 + L2 `90/1.0` + V46 L1APP soft-transfer 公式 + L2-only `compute_tag_64(empty,x2)` verification + V46 四类/G3' 语义下，能否用更小的 `m1` 通过同等 `exact_full` 门禁，从而降低总泄漏？**

三臂（`H1-8 / H1-12 / H1-16`）在**同一 9 块 fresh-block 集**上配对对比，对照是 `H1-16` 基线，不再运行 V43 Control。

## Non-Goals

- 不改 Lane C 三枚 L2 矩阵（`lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302` ordinal-2）、不改 L2 `max_iter=90,damping_alpha=1.0,GF32 poly37`、不改 L1APP 公式与 L2-only verification 语义。
- 不新增 decoder/矩阵/参数网格/调参/joint 图/MET/真帧 FER/阈值/SKR/安全/资格/晋升陈述。
- 不改写/覆盖 V46 任何已有输出与终态（V46 仍保留原终态与 78 块证据，只读）；V47 证据隔离新根。
- 不新增第二变量：不调 L2 泄漏、不调迭代/阻尼、不引入 hard/噪声/量化/失真律。
- 不启动 V48；不并行第二分支；任何执行需独立 plan ACCEPT + 显式 `EXECUTE_AUTH`。
- 不对 V46 已有 27-call 记录重放；V47 用全新 9 块回答压缩问题。

## Scope

1. **单变量 H1 前缀嵌套**：`H1-16 = V31 H1 (16×1024 QC-cyclic-projective rank16)`；`H1-8 = 前 8 行 (8×1024, 40 bits)`；`H1-12 = 前 12 行 (12×1024, 60 bits)`；三者前缀嵌套、满行秩已验证（可行性核查通过），确定性 `build_matrix_packet` 前缀切片。
2. **Fresh-block 9 块**：每源 3 块，共 9 块（`390125-127 / 390225-227 / 390325-327`，每源连续三枚，与此前 FORBIDDEN 78 零重叠、无内部重复）。FORBIDDEN 78 = V36_A3(15)+V39(15)+V40probe(3)+V41(9)+V42(9)+V43(9)+V44(9)+V45(9) =78；V46 9 块 `390122-124/222-224/322-324` 已纳入 FORBIDDEN；新区为 `390125-127/225-227/325-327`（x25-x27/源，V46 之后连续）。
3. **三臂 workload（54 decoder calls）**：每块每臂 `L1 BP 1 + Treatment L2 1 =2`，共 `9×3×2=54` decoder invocations；L2 performance records `9×3=27` 条；L1 invocations `27` 次。每块样本确定性采样一次并被三臂共享；同块三臂同 `bob`/`counts`、同 L2 矩阵（该源 Lane C ordinal-2）、同 `90/1.0`，差异仅 `H1` 行数与对应 `q_i`。
4. **L1APP 冻结公式**（V46 同构）：`p_i(u1)=P(U1|B_i)` 来自 V25 `C(a,b)`；`s1=H1^{m1}·u1^Alice`（`m1∈{8,12,16}` 对应 40/60/80 bits）；`BP_i = decode_row_layered_fftqspa(H1^{m1}, p_i, s1).bp_posterior_beliefs`（BP posterior / APP approximation，冻结 early-stop）；`q_i=softmax(BP_i)`；`P_i(U2)=Σ_{u1} q_i(u1)·P(U2|B_i,u1)`；L2 `exact` 判据不变。
5. **L2-only verification 冻结**：`tag_scope=l2_only`；`target_tag=compute_tag_64(empty_uint8, x2_true)`，`candidate_tag=compute_tag_64(empty_uint8, x2_hat)`（`empty=np.empty(0,dtype=np.uint8)`，复用 V35 `compute_tag_64` 的 `b1+b2→SHA256→hex[:16]`），`tag_ok=(candidate==target)`；四类 `exact / detected_verification_failure / decoder_non_syndrome_failure / undetected_accepted_wrong` 与 G3'=`undetected==0` 沿用 V46。
6. **总泄漏（含 L2+tag）**：`leak_total = 5·m2 + 5·m1 +64`，其中 `m2=184/190/192`（L2 syndrome 920/950/960），`m1=8→40,12→60,16→80`：
   - `H1-8:  1024 / 1054 / 1064` (920+40+64 / 950+40+64 / 960+40+64)
   - `H1-12: 1044 / 1074 / 1084`
   - `H1-16: 1064 / 1094 / 1104` (基线，与 V46 Treatment 一致)
   `f_total = leak_total / [N·(H1+H2)] N=1024`，三臂非等泄漏比较为额外 L1 冗余价值评估。
7. **每臂报告**：`exact_u1 / exact_l2 / exact_full (=exact_u1&&exact_l2)`、每源 `exact_full`、四类计数 `detected/decoder_non_syndrome/undetected`、`L1/L2 iterations/runtime`、`APP entropy / ||q-p||1`（`mean_abs_diff`），`L1 wrong` 单独报告。
8. **每臂门禁**：对 `X ∈ {H1-8, H1-12, H1-16}`，以其 9 条 L2 records 判定 `G1: exact_full ≥7/9`、`G2: 每源 exact_full ≥2/3`、`G3': undetected_accepted_wrong==0`；X 通过当且仅当三条全满足；`L1 wrong` 不入 G3' 但单独报告与诊断上下文。
9. **终态机（first-match 最小 m1）**：`V47_H1_8_RETAINED / V47_H1_12_RETAINED / V47_H1_16_ONLY / V47_NO_H1_SIZE_RETAINED / V47_EVIDENCE_INVALID`，按 `8→12→16` 顺序首个通过门禁者即终态（见 design §7）。
10. **对照语义**：不再运行 V43 Control（`P(U2|B)` 零泄漏臂）；对照是 `H1-16` 基线臂（80 bits），三臂均为 Treatment 形态（L1APP + L2-only verification）。

## Impact Scope

- **新增**：`openspec/changes/formal-ir-v47-h1-redundancy-compression/` 四工件（本轮仅此）。
- **未来实现（本轮不创建）**：`comparison_bench/src/comparison_bench/formal_ir/v47_h1_redundancy_compression.py`（仅组合 V46 L1APP 路径 + H1 前缀切片 + V35 tag L2-only，不新增 decoder/矩阵）+ `scripts/execute_v47_h1_redundancy_compression.py`；均直接 import `v35_algorithm_development::compute_tag_64` 与 `nonbinary_v31::build_matrix_packet` 前缀。
- **只读依赖**：`v35_algorithm_development.py`（tag 源）、`nonbinary_v31.py`（H1 构造）、`v38_architecture_triage.py`（结构权威）、V38 Lane C 三矩阵、V25 `channel_counts.npz` 经 `load_v25_channel_counts()`；V46 summary 仅溯源。
- **不修改**：任何既有 spec/代码/测试/输出、V46 输出、`AGENT_PROJECT_MEMORY.md`、`docs/decision-log.md` 以外；不 import `v39/v40/v41/v42/v43/v44/v45/v46` 模块作生产解码（仅模式拷贝）。

## Acceptance Criteria

- [ ] 四工件齐全一致且 lifecycle 为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，HEAD `cb4f9990f7864e12dd69c89ee87ec8a58e77470d` 绑定，明确“不实现不执行不启动 V48，等待独立评审”。
- [ ] 固定不变项冻结：Lane C 三矩阵 ordinal-2、`L2 90/1.0`、`L1APP soft-transfer 公式`（`p_i=P(U1|B), s1=H1·u1, q=softmax BP posterior, P_i(U2)=ΣqP(U2|B,u1)`）、`L2-only verification compute_tag_64(empty,x2)`、V46 四类与 `G3'=undetected==0`。
- [ ] 单变量 H1 冻结：`H1-8(8×1024,40b)/H1-12(12×1024,60b)/H1-16(16×1024,80b)` 为 V31 H1 前缀嵌套、满行秩已验证，不引入第二变量。
- [ ] 9 块新 `390125-127/390225-227/390325-327` 与 FORBIDDEN 78 零重叠、无内部重复、每源各 3、连续 x25-x27/源，已冻结可机械校验（FORBIDDEN 78 + V46 9 =87 隔离后新区）。
- [ ] Workload 冻结：每块每臂 `L1 1 + L2 1`，总 `9×3×2=54` decoder calls（27 L1 +27 L2 records），三臂配对同块共享样本，对照为 `H1-16`，不再运行 V43 Control。
- [ ] 每臂分别报告 `exact_u1/exact_l2/exact_full`、每源 `exact_full`、四类 `detected/decoder_non_syndrome/undetected`、`L1/L2 iterations/runtime`、`APP entropy/||q-p||1`。
- [ ] 总泄漏冻结：`H1-8 1024/1054/1064, H1-12 1044/1074/1084, H1-16 1064/1094/1104`（`5·m2+5·m1+64`，`f_total` 含 N）。
- [ ] 门禁冻结：每臂 `exact_full ≥7/9`、每源 `≥2/3`、`undetected==0`，`L1 wrong` 单独报告，选择通过门禁的最小 `m1`。
- [ ] 终态机冻结：`V47_H1_8_RETAINED / V47_H1_12_RETAINED / V47_H1_16_ONLY / V47_NO_H1_SIZE_RETAINED / V47_EVIDENCE_INVALID`，按 `8→12→16` first-match。
- [ ] `tag_scope=l2_only`、`compute_tag_64(empty,x2)` 空前缀复用、不重实现 canonical、`exact_full` oracle 不经 tag、`SHA-trunc64` 仅工程近似（`≈2^-64`，严格界需 universal2+seed）。

## Tasks

见 `tasks.md`（Phase A 冻结 H1 前缀与泄漏/门禁/终态、Phase B 仅 fake-runner 聚焦测试含三臂 54-call 与 first-match、Phase C decoder-free preflight 含 H1 前缀秩校验、Phase D 需 EXECUTE_AUTH 的恰好 54 invocations fresh-block、Phase E 结果复核；显式禁止清单含“禁止改 L2、禁止第二变量、禁止 V43 Control、禁止重实现 tag、禁止跨臂否决”）。

## Lifecycle

V46 前代 `DEVELOPMENT_RESULT_ACCEPTED`（result SHA `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`，branch `formal-ir-mainline`）；V47 当前 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，修订后仍保持此状态等待独立 plan 评审；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户 `EXECUTE_AUTH` 绑定到精确实现 SHA；不启动 V48。
