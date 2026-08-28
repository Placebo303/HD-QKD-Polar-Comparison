# OpenSpec Design: formal-ir-v52-rate-adaptive-l2-rescue

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行 decoder，不创建 run_01。等待独立评审。**
**Cycle**: `V52P0`
**Predecessor**: `6aa33eadc872bb4551f458ee750a94cd24566314` (plan HEAD, branch `formal-ir-mainline`)
**Feasibility**: 增量 `Δm=8` 嵌套 L2 行可在 `n=1024, m2=184/190/192, GF32 poly37, row≤16` 下 decoder-free 联合满秩且嵌套（已由 spike 三源实证 `rank==m2+8`）；15 fresh held-out 块富余；两遍条件执行预算 `15×(1 old + 首遍+条件二遍)` 描述性

## 1. 科学问题（单因子增量冗余）

> 在**相同首遍 `H1-16 + L1-APP + 原 Lane C` 与泄漏 `1064/1094/1104` 等价起点**下，**仅对首遍未通过帧额外公开 `Δm=8` 行并重译**能否以**可控的平均泄漏增量**换取**纠错成功率提升**？其折中 `Δexact vs Δleak_avg` 及失败条件泄漏如何？

- **对照**：`old Lane C` 单遍 (`H_base m2×1024`)。
- **实验**：`V52 incremental` 两遍 (`H_base` 首遍；`H_joint=[H_base;H_inc] m_joint=m2+8` 条件二遍)。
- **不改项**：不改 support/标签/prior/MET 图/decoder/先验；不引入第二 `Δm` 候选或新 MET 图。
- V52 不回答 H1 压缩、标签谱或先验因子，仅回答**嵌套增量 rescue 的成功-泄漏折中**。

## 2. 冻结语义

### 2.1 固定不变项（首遍，不得调参）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 |  |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | Lane C `SOURCE_CHECKS` ordinal-2 `383102/383202/383302` |
| GF | GF32 `poly=37` (`0b100101`) | `GF2mField.create(32)` |
| 泄漏 base | `leak_base=5*m2+5*16+64 → 1064/1094/1104` | 恒 `m1=16`, tag 64b L2-only |
| H1 | `V31-H1-QC-16×1024 rank16 80b` 母矩阵 | V31 权威 |
| 译码 | `decode_row_layered_fftqspa` `max_iter=90,damping 1.0, early-stop` | V43/V47 同构 |
| L1-APP | `p_i(u1)=P(U1|B_i)` → `BP_i` → `q_i=softmax(BP_i)` → `P_i(U2)=Σ q_i P(U2|B,u1)` | TRAIN prior `channel_counts.npz` |
| Verification | `tag_scope=l2_only, compute_tag_64(empty_uint8,x2)` trunc64, `syndrome_ok && tag_ok` 双条件 | V35 |
| 四类/G3' | `exact / detected / decoder_non_syndrome / undetected`, `G3' undetected==0` 单独表 | V46/V47 |

- **首遍** `L1 wrong` 单独报告，不入 G3'；`exact_full = exact_u1 && exact_l2` oracle 主判据，同时报告 `exact_u1/exact_l2`。
- 相同 `bob`/`prior`/`P_i(U2)` 在 paired 的 old vs V52 间共享；仅 `H_L2/syndrome` 不同。

### 2.2 增量矩阵 `H_inc` (唯一，Δm=8，禁止 seed 搜索)

- 每源确定性矩阵 `h_inc_{source}_det1` shape `8×1024`, `GF32 poly37`, `row_degree≤16`, `col_degree_inc ∈{0,1}` (每列至多一新增边), `row 非零`, `无零增量行`, 联合 `rank_GF32(H_joint)==m2+8`.
- **嵌套性**：`H_joint = vstack([H_base, H_inc])`，`H_base == H_joint[0:m2, :]` 逐比特相等；`syndrome_base` 为 `syndrome_joint` 前缀。
- **独立性**：`rank(H_inc \ rowspace(H_base)) == 8`，即 `rank(H_joint)-rank(H_base)==8`；等价 `check_independence_via_rank_increment`。
- **构造（decoder-free 确定性）**：基于 `SeedSequence([600001/600002/600003,1])` 的 PEG-增量：按 `n=1024` 列序，每列若随机判定需新增边则在 `Δm` 行中按当前行度升序选最小度行（以 `SeedSequence([det,2])` permutation tie-break），保证行度均衡 `≤16` 且避免与 base 形成短环为次级；coeff 由 `SeedSequence([det,3])` 的 `sample_uniform_gf32_nonzero` 按规范边序映射；标签 `1..31`。无 seed 轮询；构造规则不触 V48/V50/V51 outcomes。
- **泄漏**：`leak_joint = 5*(m2+Δm)+80+64 = leak_base + 5*Δm = leak_base+40`；`Δleak=40` 冻结。成功帧泄漏 `leak_base`；进入二遍的帧泄漏 `leak_joint`（无论救回与否）。
- **行度冻结**：`E_inc = Σ col_degree_inc` 约 `~ 8*~12 ≈ 96` (行均≈12)，具体由构造决定但 `≤128` 且每行≤16。
- **V48/V50/V51 无接触**：常量与校验不读其 outcomes。

### 2.3 两遍协议（条件 HARQ）

```
per block per source:
  prior = TRAIN prior (same for old and V52)
  H1 s1 via true u1, L1 decode → BP → q → P(U2)
  old arm:  decode_L2(H_base, P(U2), s_base) → verify1_old = syndrome_ok && tag_ok ; exact_old
  V52 arm:
    pass1: decode_L2(H_base, P(U2), s_base) → verify1 = syndrome_ok && tag_ok
    if verify1:  final_exact = exact_pass1, leak = leak_base, rescued=False, used_increment=False
    else:        s_inc = H_inc * u2_true ; s_joint=[s_base;s_inc]
                 pass2: decode_L2(H_joint, P(U2), s_joint) → verify2 = syndrome_ok_joint && tag_ok_joint
                 final_exact = exact_pass2, leak = leak_joint, rescued = (verify2 && exact_pass2 && !verify1), used_increment=True
```

- `exact_* = array_equal(x_hat, u2_true)` oracle；`tag_ok` 为真实 L2-only 哈希；公开成功以 `tag_ok` 判，`exact` 仅作 oracle 统计但报告两者。
- **吞吐**：每块至多 1 次 L1 + old 1 L2 + V52 首遍 1 L2 + 条件二遍 1 L2。

### 2.4 块与 workload（15 fresh held-out, paired old vs V52, 条件二遍）

库存：`1683 frames / 430k pairs` hold 区间中 **未使用且与 FORBIDDEN 171 零重叠者**（`FORBIDDEN 171 = 96(V36..V47)+45(V48)+15(V50 391xxx)+15(V51 392xxx)`；V52 新 15 需与其零重叠 per source 且与 V48/V50/V51 帧 `frame_ids` 零重叠）。

冻结新 15 块（每块写死 `4` 真实 `frame_ids` 与 `ordinal`，与 `FORBIDDEN` 零重叠，见 spike_report §8）：

| source | block ID | held_out_ordinal `[start,end]` | frame_ids[4] (global) | base | H | pairs |
|---|---|---|---|---|---|
| 1M (H=400, base1600) | 393001 | [33,36] | [1633,1634,1635,1636] | 1600 | 400 | 1024 |
| 1M | 393002 | [61,64] | [1661,1662,1663,1664] | 1600 | 400 | 1024 |
| 1M | 393003 | [89,92] | [1689,1690,1691,1692] | 1600 | 400 | 1024 |
| 1M | 393004 | [117,120] | [1717,1718,1719,1720] | 1600 | 400 | 1024 |
| 1M | 393005 | [146,149] | [1746,1747,1748,1749] | 1600 | 400 | 1024 |
| 1p5M (H=554, base2213) | 393101 | [44,47] | [2257,2258,2259,2260] | 2213 | 554 | 1024 |
| 1p5M | 393102 | [83,86] | [2296,2297,2298,2299] | 2213 | 554 | 1024 |
| 1p5M | 393103 | [122,125] | [2335,2336,2337,2338] | 2213 | 554 | 1024 |
| 1p5M | 393104 | [162,165] | [2375,2376,2377,2378] | 2213 | 554 | 1024 |
| 1p5M | 393105 | [201,204] | [2414,2415,2416,2417] | 2213 | 554 | 1024 |
| 2M (H=729, base2916) | 393201 | [53,56] | [2969,2970,2971,2972] | 2916 | 729 | 1024 |
| 2M | 393202 | [104,107] | [3020,3021,3022,3023] | 2916 | 729 | 1024 |
| 2M | 393203 | [155,158] | [3071,3072,3073,3074] | 2916 | 729 | 1024 |
| 2M | 393204 | [206,209] | [3122,3123,3124,3125] | 2916 | 729 | 1024 |
| 2M | 393205 | [257,260] | [3173,3174,3175,3176] | 2916 | 729 | 1024 |

- 每窗口 `4 frames ×256=1024 pairs`，`BLOCK_LENGTH=1024`，`pair_idx 0..255` 连续；`sampling_mode=deterministic_four_consecutive_frames_heldout_fresh`；新窗口与 V50 `391xxx`/`392xxx` 及 V48 `HELDOUT_STARTS` 均零重叠 per source 可机械校验（`BLOCK_WINDOWS` 比对）。
- **Per block calls**：old 臂 `L1 0(共享) + L2 1 =1`，V52 臂 `L1 共享 1(总) + pass1 1 + 条件 pass2 ≤1`，合计每块 `≤4` L2 解码次；总预算 `15 块 × (最多 4 L2) = 60 L2 decodes` plus `15 L1`（共享）。
- **Paired 比较**：同 block ID 同 `bob` 同 `P(U2)`，`old_exact_full` vs `V52_final_exact_full`；增量救回定义为 `!old_exact_full && V52_final_exact_full` 且 `used_increment`。

## 3. 代表矩阵与译码合约

- **Lane C base**：`lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302` ordinal-2 (committed v38 常量，复用).
- **H_inc**：`h_inc_1M_det1 / h_inc_1p5M_det1 / h_inc_2M_det1` deterministic PEG-增量 `8×1024` (spike §4).
- **H_joint**：`h_joint = vstack([H_base, H_inc])` `192/198/200 ×1024` per source.
- **H1**：`V31-H1-QC-16×1024` rank16.
- **译码合约**：共享 `GF32 poly37, max_iter=90, damping 1.0, syndrome from true ut, exact = array_equal(x_hat, ut), tag from true x2 via compute_tag_64(empty,x2)`.

## 4. 门禁与效应（描述性，无阈值晋升）

每 `block×arm` 产一条 L2 record；V52 不设 PASS/FAIL 绝对门禁，仅报告：

- **计数**：`first_pass_success (V52 pass1 verify && exact)`, `incremental_rescue = rescued_by_increment` (pass1 失败但 pass2 exact), `final_exact_full (V52)`, `old_exact_full`；`rescue_rate = rescued / (15 - first_pass_success)` 描述性。
- **分源**：1M/1p5M/2M 各自 `first/rescued/final/old`。
- **泄漏**：`avg_leak = (N_first_success*leak_base + N_attempt_rescue*leak_joint)/N`，`failed_conditional_leak = leak_joint`（最终失败帧均已尝试增量），`successful_conditional_leak = leak_base`；`f_avg = avg_leak / [N(H1+H2)]` 报告。
- **矩阵**：每源 `base_rank==m2`, `joint_rank==m2+8`, `nested==True`, `independence==8`, `row_degree_max≤16`；`E_inc` 报告。
- **Tag**：`tag_ok` 真实接受率 per pass，`G3' undetected==0` 单独表；`syndrome_ok` vs `tag_ok` 分流。
- **Paired**：`Δexact = final_V52 - old` per block 描述性，McNemar `b/c` 仅描述性；`Δleak = avg_leak_V52 - leak_base_old`。
- 同时报告 `exact_u1/exact_l2/exact_full`、四类、迭代/运行时、`APP entropy/||q-p||1` 分布。

终态机（互斥，EVIDENCE_INVALID 优先）：

```
0. 任意完整性/守卫失败 -> V52_EVIDENCE_INVALID
1. else -> V52_NESTED_RESCUE_COMPLETE (descriptive, no promotion)
   orthogonal flags: rescue_gain = final_V52 > old (描述性)
```

## 5. O3 配对语义

- 同 `block ID` 的 held-out 样本 `(idx,alice,bob)` 每块确定性一次，`L1` 单次生成 `q_i` 与 `P_i(U2)`，`old` 单遍与 `V52` 首遍同 `bob`/`P_i(U2)`/`s_base`/`H_base`；`V52` 二遍仅在首遍未通过时以同一 `bob`/`P_i(U2)` 与 `H_joint/s_joint` 重译。
- 跨块/跨臂 outcome 差异为诊断量，永不作完整性失败。

## 6. 科学 preflight、守卫序

1. **拒绝类最先**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定未来实现 SHA（plan 引用 `6aa33eadc872bb4551f458ee750a94cd24566314`）；四文件 SCOPED dirty（含 `v52` 模块、`v52` CLI、`v38_architecture_triage.py`、`v35_algorithm_development.py`）；输出根已存在即拒（J7）；任一拒绝零 calls 不建文件. Spike 脚本任一门禁失败时 `sys.exit(1)` 非零退出。
2. **科学 preflights（decoder-free, write-free）**：seed registry 校验（新区 15 与 FORBIDDEN 171 block ID 零重叠 per source 连续且与 V48/V50/V51 180+60+60 帧 `frame_ids` 零重叠）；`H_base` 三矩阵与 committed v38 常量 `rank/support` 比对；`H_inc` 确定性重建与 `joint_rank==m2+8 / nested / independence==8 / row≤16` 校验；`E_inc` 与 `leak_base/joint` 公式校验 (`leak_joint=leak_base+40`)；TRAIN counts 形态校验；held-out fresh 池可达；首块哨兵 `393001/393101/393201` 各 `L1→P_i(U2)` 通路 + `tag_import_ok` + `leakage_accounted` + `tag_scope_l2_only`.
3. **Preflight 失败** → 建增量根写 `v52_invalid_notice.json` + 空 records + `v52_summary.json` (terminal `V52_EVIDENCE_INVALID`, planned 15) 后零 decoder calls 停止.
4. **建根**仅在全部守卫与 preflights 通过后、首个 decoder call 前.

## 7. 记录、聚合、summary

每 L2 call record schema（含 `tag_scope=l2_only, arm∈{old,V52_pass1,V52_pass2}`）：

```
call_id, source, block_seed(block ID), arm(old/V52_pass1/V52_pass2), pass_index(1/2), used_increment(bool),
matrix_id(base/joint/inc), h1_matrix_id, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, sampling_mode,
max_iter 90, damping 1.0, errors_initial, errors_final, exact_l2, exact_u1, exact_full,
syndrome_ok_l2/l1, wrong_codeword, target_tag, candidate_tag, tag_ok, tag_scope,
reclassified, iterations_l1/l2, bp_posterior_entropy, mean_abs_diff_q_p, leak_total (1064/1094/1104 or +40), leak_joint, status, runtime_s
```

Summary 含：记账 `first_pass_success / rescue_by_increment / final_exact_full / old_exact_full` (overall & per-source)；`N=15`；`avg_leak / failed_conditional_leak / successful_conditional_leak`；`Δleak=40*(1-p1)`；`H_inc joint_rank/nested/independence/E_inc/row_max` provenance；L1 诊断；四类计数；G3'；门禁描述；`f_avg`；paired `old vs V52` per block 描述性 (`Δexact`, McNemar `b/c` 仅描述)；claim boundary；provenance（含 `H_inc det1` 与 fresh held-out 溯源含每块 `frame_ids/ordinal`）。

## 8. 统计与断言边界

仅描述性；`n=15` blocks 配对；比例带 n 与 raw counts；区间 naive 未校正簇聚；无显著性晋升；终态仅 `V52_EVIDENCE_INVALID / V52_NESTED_RESCUE_COMPLETE`。

断言边界 verbatim：结果仅支持 `n=1024, m2=184/190/192, Δm=8` 上 `H_joint=[H_base;H_inc] 8×1024 嵌套增量` 在 `15` fresh held-out 块上的有界 rescue 归因（首遍冻结 Lane C 原 support/标签/prior/MET 图不改，decoder `90/1.0 poly37`，泄漏 `leak_base 1064/1094/1104` / `leak_joint=leak_base+40` 仅失败帧追加，已成功帧不增泄漏，`row≤16 full rank nested independence==8` 确定性构造不触 outcomes, L2-only tag `≈2^-64` 工程近似），`exact_full` oracle 不经 tag；均非真帧 FER 全集/阈值/SKR/资格/晋升证据；不启动 V53.

## 9. 证据写出

固定增量根（decoder 前建，fail-closed）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v52_rate_adaptive_l2_rescue/run_01/
```

文件：`v52_records.json/.csv` (≤45 L2 行：15 old + ≤30 V52 pass1/pass2)、`v52_summary.json`、`v52_invalid_notice.json`（失败时）. CSV/JSON 行对等；禁写 NPZ.

## 10. 实现草图（后继轮次，当前未授权）

- `comparison_bench/src/comparison_bench/formal_ir/v52_rate_adaptive_l2_rescue.py`：import `construct_lane_c_prototype` 常量与 `v35.compute_tag_64`，实现确定性 `H_inc 8×1024` (§2.2，PEG-增量 tie-break `SeedSequence([60000x,1/2/3])`，`col≤1 row≤16 joint rank`) + 双臂 runner (per block `old 1 L2 + V52 pass1 1 + 条件 pass2 ≤1`).
- `scripts/execute_v52_nested_rescue.py`：默认拒绝；`--execution-authorized --authorized-target-sha <sha>`；HEAD/origin 精确绑定未来实现 SHA（plan `6aa33ead...`）；四文件 SCOPED dirty；budget 硬帽 15 块条件执行；任一 gate 失败非零退出.
- 仅 fake-runner 测试；不以 outcomes 定增量或调 `Δm`.

## 11. 自由裁量 D1–D10

- D1 单一增量 `Δm=8` per source 嵌套 rescue，15 块 paired old vs V52。
- D2 seed registry 新区 15 `393001..` `393101..` `393201..` 与 FORBIDDEN 171 零重叠且与 V48/V50/V51 帧零重叠 per source 连续，每块写死 4 真实 `frame_ids` 与 `ordinal`。
- D3 代表矩阵 3 Lane C base + 3 H_inc det1 (8×1024) + 3 H_joint (m2+8)。
- D4 泄漏公式 `leak_base 1064/1094/1104` / `leak_joint+40` 冻结，已成功帧不增泄漏。
- D5 报告门禁描述性 `first/rescued/final/old`，`avg_leak/failed_conditional`，`paired Δexact`。
- D6 哨兵每源首块 `393001/393101/393201` 单 L1 通路。
- D7 call 序 `source 1M/1p5M/2M, block asc, within-block old→pass1→(条件)pass2`。
- D8 SCOPED dirty 四文件。
- D9 preflight 失败 invalid 三件套零 calls。
- D10 文件集条件行记录 + 聚合 + 效应 + provenance.
