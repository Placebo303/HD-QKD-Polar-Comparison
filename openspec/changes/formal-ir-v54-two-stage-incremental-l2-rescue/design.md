# OpenSpec Design: formal-ir-v54-two-stage-incremental-l2-rescue

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **仅规划，不实现，不执行 decoder，不创建 run_01。等待独立复审。**
**Cycle**: `V54P0`
**Predecessor**: `formal-ir-v53-rate-adaptive-l2-heldout-confirm` (plan HEAD `93c12fa5a8524eb5a8a52d071f135c653c746ebaf`, branch `formal-ir-mainline`), **freeze HEAD** `bf5dd1686049156540328bac264296b17fee546c` (branch `formal-ir-mainline`)
**Feasibility**: V52/V53 已实证 `H_inc1` 嵌套 `rank==m2+8`；新增 `H_inc2` 同构造在 `n=1024, m2=184/190/192, GF32 poly37, row≤16, col≤1` 下 decoder-free 联合 `m2+16` 满秩嵌套可行（spike 三源实证）；1M/1p5M/2M hold 库存 1683 frames 中，排除 V48-V53 共 135 区间 540 帧已用后仍富余约 1143 帧（约 285 个非重叠 4 帧窗口理论上限），分散选 15/源=45块可行；三阶段条件执行预算 `45 L1+45 base+≤45 stage1+≤45 stage2=90-180 硬帽180` 描述性
**V53 history note**: V53 `33/45 差2未过35/45` 仅作历史描述，V54 门禁不降至 33/45

## 1. 科学问题（单因子二阶段增量 rescue，45块）

> 在**完全冻结 V52/V53 完整方法**（首遍 `H1-16 + L1-APP + 原 Lane C` 与泄漏 `1064/1094/1104` 等价起点，增量 `H_inc1 8×1024 Δm=8` 首阶段 rescue 已冻结）的**相同参数**下，**再叠加第二张确定性 `H_inc2 8×1024 Δm=8` 的二阶段 rescue（累计 Δm=16）在 45 个全新 held-out blocks 上能否以可控的平均泄漏增量弥补 V53 差 2 的 gap 且区分 `Δ8 已足` vs `Δ16 增量价值`？**

- **对照**：无新对照臂；`base` 即 `old Lane C` 单遍结果（同一次译码），`stage1` 为 V53 等价首增量后结果，`final(stage2)` 为二阶段后结果；比较为 `base vs stage1 vs final` 配对（描述性）。
- **不改项**：不改 support/标签/prior/MET图/`m2`/H1/`max_iter/damping`/`H_inc1`；仅新增 `H_inc2` 一张确定性矩阵，不引入第三增量或多档搜索，不做 seed 搜索或阈值调优。
- **45 vs 30 的规模**：沿用 V53 论证（30块分源仅10不稳定），45块分源15仍为最小确认规模。
- **通过后的 claim 边界**：即使 `V54_DELTA8_ALREADY_SUFFICIENT` 或 `V54_DELTA16_ADDED_VALUE_SIGNAL`，仍仅为 `development confirmation`，**不等同 `formal qualification`**。下一阶段 `qualification` 需**新采集或独立 TEST 分裂**（`split_manifest` 外的新日期/源或新鲜 holdout，且 `counts` 不重用），并走独立 OpenSpec change 与执行授权。
- V54 不回答 H1 压缩、标签谱或先验因子，仅回答**二阶段嵌套增量在 45块 held-out 上的 stage1 充分性与 stage2 增量价值**。

## 2. 冻结语义

### 2.1 固定不变项（冻结方法，零改，V52/V53 complete method）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 | |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | Lane C `SOURCE_CHECKS` ordinal-2 `38310x` |
| GF | GF32 `poly=37` (`0b100101`) | `GF2mField.create(32)` |
| 泄漏 base | `leak_base=5*m2+5*16+64 → 1064/1094/1104` | 恒 `m1=16`, tag 64b L2-only |
| 泄漏 stage1 | `leak_stage1=5*(m2+8)+80+64 → 1104/1134/1144 (+40)` | `Δm=8` |
| 泄漏 stage2 | `leak_stage2=5*(m2+16)+80+64 → 1144/1174/1184 (+80)` | `Δm=16` |
| H1 | `V31-H1-QC-16×1024 rank16 80b` 母矩阵 | V31 权威 |
| 译码 | `decode_row_layered_fftqspa` `max_iter=90,damping 1.0, early-stop` | V43/V52 同构 |
| L1-APP | `p_i(u1)=P(U1|B_i)` → `BP_i=decode(H1,p_i,s1).bp_posterior_beliefs` → `q_i=softmax(BP_i)` → `P_i(U2)=Σ q_i P(U2|B,u1)` | TRAIN prior `channel_counts.npz` |
| Verification | `tag_scope=l2_only, compute_tag_64(empty_uint8,x2)` trunc64, `syndrome_ok && tag_ok` 双条件 | V35 |
| 四类/G3' | `exact / detected / decoder_non_syndrome / undetected`, `G3' undetected==0` 单独表 | V46/V52 |
| H_inc1/H_joint1 | `h_inc_1M_det1 / h_inc_1p5M_det1 / h_inc_2M_det1` `8×1024` det1 + `h_joint1 192/198/200×1024` nested | V52 冻结 |
| Prior | `TRAIN-only` via `load_v25_channel_counts()`，evaluation blocks 来自 held-out | V25 |
| Rescue触发 | `verification-only`：仅未通过 `verify` 才进入下一阶段，已通过帧不增加泄漏不重译 | V52/V53 |

- `exact_* = array_equal(x_hat, u2_true)` oracle 主判据，同时报告 `exact_u1/exact_l2`；`exact` 仅统计不触发增量。
- 相同 `bob`/`prior`/`P_i(U2)` 在 `base vs stage1 vs final` 间共享；仅 `H_L2/syndrome` 不同。
- `Δm=8` 首阶段与 `Δm=8` 二阶段累计 `Δm=16`，**不得新造 H_inc1 或试 Δm=4/12/16 之外多档**。

### 2.2 二阶段增量矩阵 `H_inc2`（唯一新增，Δm=8，禁止 seed 搜索）

- 每源确定性矩阵 `h_inc2_{source}_det2` shape `8×1024`, `GF32 poly37`, `row_degree≤16`, `col_degree_inc2∈{0,1}` (每列在第二增量中至多一新增边)、`row非零`、`无零增量行`、与已有联合 `rank_GF32(H_total)==m2+16`。
- **嵌套性**：`H_total = vstack([H_base, H_inc1, H_inc2])`，`H_base == H_total[0:m2, :]` 逐比特相等；`H_joint1 == H_total[0:m2+8, :]`；`syndrome_base` 与 `syndrome_joint1` 分别为 `syndrome_total` 前缀（`GF32` 线性）。
- **独立性**：`rank(H_inc1 \ rowspace(H_base)) ==8` 已冻结；`rank(H_inc2 \ rowspace([H_base;H_inc1])) ==8`，即 `rank(H_total)-rank(H_joint1)==8` 且 `rank(H_total)-rank(H_base)==16`。
- **构造（decoder-free 确定性，第二张）**：基于 `SeedSequence([600004/600005/600006,1])` 的 PEG-增量（与 V52 H_inc1 同构但独立 id）：按 `n=1024` 列序，每列若需新增边则在 `Δm2=8` 行中按当前行度升序选最小度行（以 `SeedSequence([det2,1]).permutation(8)` tie-break），保证行度均衡 `≤16`；`coeff` 由 `SeedSequence([det2,2])` 的 `sample_uniform_gf32_nonzero` 按规范边序映射。**本变更不重新设计 H_inc1**，仅新增 H_inc2 的确定性单次生成，**禁止 seed 搜索、多候选、用 V53 outcomes 选行**。
- **泄漏**：`leak_stage1 = leak_base+40`（`5*Δm`）；`leak_stage2 = leak_base+80`（`5*16`）；`Δleak per stage=40` 冻结。`first_pass_success_leak=leak_base (1064/1094/1104)`；`stage1_success_leak=leak_stage1 (1104/1134/1144)`；`stage2_leak=leak_stage2 (1144/1174/1184)`（stage2 成功与最终失败同为 `leak_stage2`）；`per_source_avg[s]=leak_base[s]+40×N_stage1_attempted[s]/15+40×N_stage2_attempted[s]/15`，`overall_avg=(Σ leak_base[source(block)]+40×N_stage1_total+40×N_stage2_total)/45`（`N_stage1_total=count(!verify_base)` overall，`N_stage2_total=count(!verify_base && !verify_stage1)` overall，因三源 `leak_base` 不同禁止用单一 `leak_base+40N/45` 当 overall）。
- **行度**：`E_inc2≈96` 报告，`joint total E_total ≈ E_base + 96 + 96`，`joint row_max≤16`（每阶段独立 ≤16）。
- **V48-V53 无接触**：常量与校验不读其 outcomes，仅读其已用 `frame_ids` 作重叠过滤。

### 2.3 三阶段协议（条件 HARQ，verification-only）

```
per block per source (45 blocks):
  prior = TRAIN prior (shared)
  H1 s1 via true u1, L1 decode → BP → q → P(U2)  // 45次总计，per block 1
  base: decode_L2(H_base, P(U2), s_base) → verify_base = syndrome_ok && tag_ok ; exact_base
  if verify_base:  final_exact = exact_base, leak = leak_base (=1064/1094/1104), stage=base, used_inc1=False, used_inc2=False
  else:
    s_inc1 = H_inc1 * u2_true ; s_joint1=[s_base; s_inc1]
    stage1: decode_L2(H_joint1, P(U2), s_joint1) → verify_stage1 ; exact_stage1
    if verify_stage1: final_exact = exact_stage1, leak = leak_stage1 (=1104/1134/1144), used_inc1=True, used_inc2=False
    else:
      s_inc2 = H_inc2 * u2_true ; s_total=[s_base; s_inc1; s_inc2]
      stage2: decode_L2(H_total, P(U2), s_total) → verify_stage2 ; exact_stage2
      final_exact = exact_stage2, leak = leak_stage2 (=1144/1174/1184) 无论成功/失败, used_inc1=True, used_inc2=True
  // exact_* 仅 oracle 统计，触发仅 verification
  // 每块 L1 1 + base L2 1 + 条件 stage1 ≤1 + 条件 stage2 ≤1；45块总 45 L1+45 base+≤45 stage1+≤45 stage2=90-180 硬帽180，L2 45-135
```

- `exact_* = array_equal(x_hat, u2_true)` oracle；`tag_ok` 为真实 L2-only 哈希；公开成功以 `tag_ok` 判，`exact` 仅作 oracle 统计但报告两者。
- **吞吐冻结**：每块 `L1 1(共享)+base 1+条件stage1 ≤1+条件stage2 ≤1`；总 `45 L1+45 base+≤45 stage1+≤45 stage2=90-180 硬帽180，L2 45-135`。

### 2.4 块与 workload（45 fresh held-out, 三阶段条件）

**库存**：`1683 frames / 430k pairs` hold 区间中**未使用且与已用区间零重叠者**。

- Hold 区间 per source（`split_manifest 60/20/20`）：
  - 1M: `H=400, base=1600, frames 1600..1999, total 2000, hold last 400`
  - 1p5M: `H=554, base=2213, frames 2213..2766, total 2767`
  - 2M: `H=729, base=2916, frames 2916..3644, total 3645`
- 已用区间 union `U2`（per source）由以下设计表汇总（`[start,end]` ordinal，`frame_ids=[base+start .. base+start+3]`）：
  - V48 15/源: 1M 0,28,56,84,113,141,169,198,226,254,282,311,339,367,396；1p5M 0,39,78,117,157,196,235,275,314,353,392,432,471,510,550；2M 0,51,103,155,207,258,310,362,414,466,517,569,621,673,725
  - V50 5/源: 1M 14,42,70,98,127；1p5M 19,58,97,137,176；2M 25,77,129,181,232
  - V51 5/源: 1M 7,35,63,91,119；1p5M 12,51,90,130,169；2M 18,70,122,174,225
  - V52 5/源: 1M 33,61,89,117,146；1p5M 44,83,122,162,201；2M 53,104,155,206,257
  - V53 15/源: 由 `spike_sample_registry.py` 按 `K=187/341/520` 分散 `index_j=floor(j*(K-1)/14)` 选 15/源（实际 starts 见 V53 spike_report §5-§6，已在 V53 冻结；V54 中视为已用，spike 脚本将重算 V53 selected 并纳入 `U2`）
  - 早期 `FORBIDDEN 96`（V36..V47，含 TRAIN 开发块，非 held-out，忽略 held-out 过滤但 block ID 级零重叠）
  - 合计 held-out 已用 `135` 区间（`V48 45 + V50 15 + V51 15 + V52 15 + V53 45 =135` 区间，每区间 4 帧共 540 帧）

**剩余非重叠四连续窗口枚举算法（冻结，V54 K2）**：

```
per source:
  all_starts = [0..H-4]
  filtered = [s for s in all_starts if not overlaps([s,s+3], U2_per_source)]
    # overlaps = 区间交集非空（[s,s+3] ∩ [u,u+3] != ∅）
  S2 = sorted(filtered)
  K2 = len(S2)
  # 要求 K2 ≥15 且分散选择后两两非重叠 gap≥4
  # S2 中窗口间可能仍步长1重叠，但分散选择保证最终15两两非重叠；若有重叠则 REGISTRY_INVALID
  selected2 = [S2[floor(j*(K2-1)/14)] for j in 0..14]
  # 若 selected2 中存在重叠（gap<4），则 REGISTRY_INVALID
  # 替代严格非重叠枚举：S2_strict = [s for s in S2 if s%4==0]（按4对齐，理论上限 100/138/182，过滤后仍≥15）
  # spike 将同时计算 K2 与 K2_strict 并报告，以 S2 分散选为准但保证最终15两两 gap≥4
```

- **K2 的富余校验**：`H-4+1`=397/551/726，减去 `135` 区间覆盖约 `135*7≈945` 排除窗口（每已用区间排除约7个 start 的重叠膨胀），剩余 `K2≈ 120-350` 仍远 ≥15，分散可行（1M 预计 `K2≈142`，1p5M `≈260`，2M `≈380`，以 spike 实测为准）。

- **冻结新45块（建议 IDs 仅标识，真实由 frame_ids 决定）**：

  - 建议 block IDs: `395001..395015` (1M 15), `395101..395115` (1p5M 15), `395201..395215` (2M 15) — **仅作标识与排序键，真实以 frame_ids/ordinal 为准**，与 prior block IDs (`390xxx/391xxx/392xxx/393xxx/394xxx`) 零重叠可机械校验。
  - 每块属性：`block_id` (建议395xxx), `held_out_ordinal_start/end = [selected2, selected2+3]`, `frame_ids[4]=[base+start .. base+start+3]`, `pairs_count=1024`, `sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v54`。
  - **Design 逐块冻结值**：由 `spike_nested_rescue_stage2.py` 按上述算法实际运行后输出的 `selected2` 决定，本 design.md §2.4 冻结算法与示例，spike_report.md 冻结实际数值。**示例（待 spike 实测固化，当前为算法示意占位，spike 执行后替换为实测值）**：

| source | block ID (suggested) | held_out_ordinal `[start,end]` (example) | frame_ids[4] (global, example) | pairs | sampling_mode |
|---|---|---|---|---|---|
| 1M (H=400, base1600) | 395001 | [4,7] | [1604,1605,1606,1607] | 1024 | deterministic_four_consecutive_frames_heldout_fresh_v54 |
| 1M | 395002 | [20,23] | [1620,1621,1622,1623] | 1024 |  |
| … | … | … | … | … |  |
| 1M | 395015 | [392,395] | [1992,1993,1994,1995] | 1024 |  |
| 1p5M (H=554, base2213) | 395101 | [5,8] | [2218,2219,2220,2221] | 1024 |  |
| … | 395115 | [545,548] | [2758,2759,2760,2761] | 1024 |  |
| 2M (H=729, base2916) | 395201 | [7,10] | [2923,2924,2925,2926] | 1024 |  |
| … | 395215 | [720,723] | [3636,3637,3638,3639] | 1024 |  |

  - 实际冻结以 spike 输出为准，proposal/design/spike_report 三处一致；spike 未执行前 design 示例仅示意，待执行后 principal 复核固化。

- 每窗口 `4 frames×256=1024 pairs`，`BLOCK_LENGTH=1024`，`pair_idx 0..255` 连续；`sampling_mode` 固定。
- **Per block calls 冻结**：每块 `L1 1(共享)+base 1+条件 stage1 ≤1+条件 stage2 ≤1`；每块 L2 1-3 次，总预算 `45 L1+45 base+≤45 stage1+≤45 stage2=90-180 硬帽180，L2 45-135`。
- **Paired 比较**：同 block ID 同 `bob` 同 `P(U2)`，`base_exact_full` vs `stage1_exact_full` vs `final_exact_full`；stage1/stage2 救回定义为 `!verify_base && stage1_exact && used_inc1` 与 `!verify_stage1 && final_exact && used_inc2`。

## 3. 代表矩阵与译码合约

- **Lane C base**：`lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302` ordinal-2 (committed v38常量，复用).
- **H_inc1**：`h_inc1_1M_det1 / h_inc1_1p5M_det1 / h_inc1_2M_det1` deterministic PEG-增量 `8×1024` (V52 det1, SeedSequence 600001-3, 复用).
- **H_inc2**：`h_inc2_1M_det2 / h_inc2_1p5M_det2 / h_inc2_2M_det2` deterministic PEG-增量 `8×1024` (新增 det2, SeedSequence 600004-6).
- **H_joint1**：`h_joint1 = vstack([H_base, H_inc1])` `192/198/200 ×1024` per source.
- **H_total**：`h_total = vstack([H_base, H_inc1, H_inc2])` `200/206/208 ×1024` per source.
- **H1**：`V31-H1-QC-16×1024` rank16.
- **译码合约**：共享 `GF32 poly37, max_iter=90, damping 1.0, syndrome from true ut, exact = array_equal(x_hat, ut), tag from true x2 via compute_tag_64(empty,x2)`.

## 4. 门禁与效应（描述性，含 PASS 门禁与四终态）

对 `45` held-out blocks 判定：

- **计数**：`base_exact_full` (oracle首遍) 与 `verify_base=count(syndrome_ok&&tag_ok)` 分别计数（禁止假定相等），`stage1_exact_full` 与 `verify_stage1` 分别，`final_exact_full` 与 `verify_final` 分别；`stage1_rescued = rescued_by_inc1` (base 失败但 stage1 exact)，`stage2_rescued = rescued_by_inc2` (stage1 失败但 stage2 exact)；`rescue_rate_stage1 = stage1_rescued / N_stage1_attempted`（`N_stage1_attempted=count(!verify_base)` overall；per source `N_stage1_attempted[s]=count(!verify_base) per source`），`rescue_rate_stage2 = stage2_rescued / N_stage2_attempted`（`N_stage2_attempted=count(!verify_base && !verify_stage1)` overall）描述性，禁止用 `45-base_exact` 作分母。
- **分源**：1M/1p5M/2M 各自 `base/stage1/final/rescued_stage1/rescued_stage2`。
- **泄漏（三类+平均+总量）**：`first_pass_success_leak = leak_base (1064/1094/1104)`；`stage1_success_leak = leak_stage1 (1104/1134/1144)`；`stage2_leak = leak_stage2 (1144/1174/1184)`（stage2 成功与最终失败同为 `leak_stage2`）；`per_source_avg[s]=leak_base[s]+40×N_stage1_attempted[s]/15+40×N_stage2_attempted[s]/15`，`overall_avg=(Σ leak_base[source(block)]+40×N_stage1_total+40×N_stage2_total)/45`（`N_stage1_total=count(!verify_base)` overall，`N_stage2_total=count(!verify_stage1 && !verify_base)` overall，因三源 `leak_base` 不同禁止用单一 `leak_base+40N/45` 当 overall）；`failed_conditional = leak_stage2`；`f_avg = avg_leak / [1024×(H(U1|B)+H(U2|U1,B))]`（若保留则分母为 `1024×信息熵和`，禁 `N_blocks×(H1+H2)`）等报告；`avg disclosure per attempted frame = overall_avg /1024` bits/symbol 描述性；`total_disclosed_bits = Σ leak_total` 与 `disclosure_per_final_exact_block=total_disclosed_bits/final_exact_full_count（为0则null）`。
- **阶段费率**：`stage1_attempt_rate = N_stage1_total/45`，`stage2_attempt_rate = N_stage2_total/45`，`stage1_rescue_rate` 与 `stage2_rescue_rate` 分别报告，`stage2_added_value = final - stage1`。
- **矩阵**：每源 `base_rank==m2`, `joint1_rank==m2+8`, `total_rank==m2+16`, `nested_stage1==True`, `nested_stage2==True`, `independence_1==8`, `independence_2==8`, `row_degree_max≤16`；`E_inc1/E_inc2` 报告。
- **Tag**：`tag_ok` 真实接受率 per stage，`G3' undetected==0` 单独表；`syndrome_ok` vs `tag_ok` 分流。
- **Paired**：`Δexact_stage1 = stage1 - base`, `Δexact_stage2 = final - stage1`, `Δexact_total = final - base` per block 描述性，McNemar `b/c` 仅描述性；`Δleak_per_source[s]=40×(N_stage1[s]+N_stage2[s])/15`，`Δleak_overall=40×(N_stage1_total+N_stage2_total)/45`。
- 同时报告 `exact_u1/exact_l2/exact_full`、四类、迭代/运行时、`APP entropy/||q-p||1` 分布。
- **V53 33/45 仅历史描述**，不在 V54 判据中引用作阈值依据。

**主门禁与四终态（冻结）**：

```
V54_EVIDENCE_INVALID 优先 若 完整性/守卫/秩/嵌套/重叠/记账失败
else if final_exact_full ≥35/45 (77.78%) ∧ 每源 final_exact_full ≥10/15 (66.7%) ∧ undetected_accepted_wrong ==0 (G3')
        ∧ joint1_rank==m2+8 ∧ total_rank==m2+16 ∧ nested_stage1 && nested_stage2 ∧ 记账90-180硬帽且每块L1 1+base1+stage1≤1+stage2≤1 ∧ 45 fresh块与已用零重叠
     then if stage1_exact_full ≥35/45 ∧ 每源≥10/15 ∧ undetected==0  → V54_DELTA8_ALREADY_SUFFICIENT  (stage1 已足，stage2冗余)
          else → V54_DELTA16_ADDED_VALUE_SIGNAL (stage1未过但final过，Δ16增量有价值)
else → V54_DELTA16_INSUFFICIENT (final未过但完整性通过)
```

- 四终态互斥覆盖，`EVIDENCE_INVALID` 优先；`V54_DELTA8_ALREADY_SUFFICIENT` 需 `stage1` 与 `final` 同时过门禁；`V54_DELTA16_ADDED_VALUE_SIGNAL` 需 `stage1` 未过但 `final` 过；门禁 `35/45 & 10/15 & undetected==0` 不因 V53 差两个改阈值。
- 通过（前两者）仍仅 `development confirmation`，不晋升 qualification。

## 5. O3 配对语义

- 同 `block ID` 的 held-out 样本 `(idx,alice,bob)` 每块确定性一次（4帧窗口 `frame_ids[4]`），`L1` 单次生成 `q_i` 与 `P_i(U2)`，`base` → `stage1`（仅 `!verify_base`）→ `stage2`（仅 `!verify_stage1 && !verify_base`）条件递进，同 `bob`/`P_i(U2)`/`s` 的嵌套前缀，`exact` 仅 oracle 统计。
- 跨块/跨臂 outcome 差异为诊断量，永不作完整性失败。

## 6. 科学 preflight、守卫序、执行偏差防复发

1. **拒绝类最先**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定未来实现 SHA（plan 引用 `bf5dd1686049156540328bac264296b17fee546c`）；四文件 SCOPED dirty（含 `v54` 模块、`v54` CLI、`v38_architecture_triage.py`、`v35_algorithm_development.py`）；输出根已存在即拒（J7）；任一拒绝零 calls 不建文件。Spike 脚本任一门禁失败时 `sys.exit(1)` 非零退出。
2. **科学 preflights（decoder-free, write-free）**：seed registry 校验（新区 45 与已用 135 区间零重叠 per source + 与 V48-V53 `frame_ids` 零重叠，无内部重复，每源均分 15 且分散 `index_j`）；`H_base` 三矩阵与 committed v38 常量 `rank/support` 比对；`H_inc1` 确定性重建与 `joint1_rank==m2+8 / nested / independence==8 / row≤16 / col≤1 / E_inc≈96 / leak_stage1==leak_base+40` 校验；`H_inc2` 确定性重建与 `total_rank==m2+16 / nested_stage2 / independence_2==8 / row≤16 / col≤1 / E_inc2≈96 / leak_stage2==leak_base+80` 校验；TRAIN counts 形态校验；held-out fresh 池可达（1683 frames, 剩余 `K2≥45`）；首块哨兵 `395001/395101/395201` 各 `L1→P_i(U2)` 通路+`tag_import_ok`+`leakage_accounted`+`tag_scope_l2_only`。
3. **执行偏差防复发（冻结）**：
   - **不使用 600s 外部 timeout**：执行器不得以外层 600s timeout 包裹 decoder 循环；建议 `--timeout` 至少 `3600s` 或不设外部 timeout（decoder 内部 `90/1.0` 早停已限单块运行时）。
   - **session/cell ID 轮询规则**：若执行返回 `session_id/cell_id`，主线程/监督器**只轮询同一 `session_id/cell_id` 的进程状态**（`poll`/`wait`），**禁止 `restart`/`recreate` 新 session/cell**；若轮询超时或失联，保留 raw partial 并标记 `V54_EVIDENCE_INVALID_INTERRUPTED`，不自动重跑。
   - **中断保留**：若执行在 `90-180` calls 中途中断（`KeyboardInterrupt`/`timeout`/`OOM`/`BaseException`），已完成的 `raw partial`（`v54_records.json` 已写行与 `started/completed` 计数）**原样保留**在预建根内，**不生成 `v54_summary.json` 聚合**，`completed < planned` 且 `terminal=V54_EVIDENCE_INVALID_INTERRUPTED`；不自动重跑或补偿。
   - **不自动重跑**：任何 `FAIL` 或 `EVIDENCE_INVALID` 后，**禁止自动 `rerun/resume/retry`**；需新 `EXECUTE_AUTH` 且新独立 `run_02`（本变更仅 `run_01`）。
4. **Preflight 失败** → 建增量根写 `v54_invalid_notice.json` + 空 records + `v54_summary.json` (terminal `V54_EVIDENCE_INVALID`, planned 90-180) 后零 decoder calls 停止。
5. **建根**仅在全部守卫与 preflights 通过后、首个 decoder call 前。

## 7. 记录、聚合、summary

每 L2 call record schema（含 `tag_scope=l2_only, arm∈{base,stage1,stage2}`，`base` 兼 old 与 V54 首阶段 `pass1`）：

```
call_id, source, block_seed(block ID 395xxx), arm(base/stage1/stage2), pass_index(1/2/3), used_inc1(bool), used_inc2(bool),
matrix_id(base/joint1/total), h1_matrix_id, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, sampling_mode,
max_iter 90, damping 1.0, errors_initial, errors_final, exact_l2, exact_u1, exact_full,
syndrome_ok_l2/l1, wrong_codeword, target_tag, candidate_tag, tag_ok, tag_scope,
reclassified, iterations_l1/l2, bp_posterior_entropy, mean_abs_diff_q_p, leak_total (1064/1094/1104 or 1104/1134/1144 or 1144/1174/1184), leak_stage1, leak_stage2, status, runtime_s
  // leak_total = first_pass_success_leak(1064/1094/1104) 若 base 通过 else stage1_success_leak(1104/1134/1144) 若 stage1 通过 else leak_stage2(1144/1174/1184)；base/stage1/stage2 三层分别
```

Summary 含：记账 `base_exact_full` 与 `verify_base` 分别计数（overall & per-source, 45块）、`stage1_exact_full` 与 `verify_stage1` 分别、`final_exact_full` 与 `verify_final` 分别、`stage1_rescued / stage2_rescued / final`、`N_stage1_attempted=count(!verify_base)` 与 `N_stage2_attempted=count(!verify_stage1&&!verify_base)`（overall & per-source, 45块）、`rescue_rate_stage1/stage2`（分母分别为 `N_stage1_attempted` 与 `N_stage2_attempted` 禁 `45-base_exact`）、`N=45`、`first_pass_success_leak(1064/1094/1104) / stage1_success_leak(1104/1134/1144) / stage2_leak(1144/1174/1184, 成功与失败同)` / `per_source_avg[s]=leak_base[s]+40×N_stage1[s]/15+40×N_stage2[s]/15 / overall_avg=(Σ leak_base+40×N_stage1_total+40×N_stage2_total)/45` / `failed_conditional_leak(leak_stage2)` / `avg_disclosure_per_attempted_frame / total_disclosed_bits / disclosure_per_final_exact_block=total_disclosed_bits/final_exact_full_count（为0则null）` 描述性；`Δleak_per_source=40×(N_stage1[s]+N_stage2[s])/15`，`Δleak_overall=40×(N_stage1_total+N_stage2_total)/45`；`H_inc1 joint1_rank/nested/independence` 与 `H_inc2 total_rank/nested/independence` provenance；L1 诊断；四类计数；G3'；门禁明细（`stage1` 与 `final` 的 G1/G2/G3' 数值与 `V54_*` 四终态）；`f_avg`；paired `base vs stage1 vs final` per block 描述性（McNemar `b/c` 仅描述）；claim boundary；provenance（含 `H_inc1 det1` 与 `H_inc2 det2` 与 fresh held-out 溯源含每块 `frame_ids/ordinal` 与 `K2/index_j`）。

## 8. 统计与断言边界

仅描述性；`n=45` blocks 三阶段配对；比例带 n 与 raw counts；区间 naive 未校正簇聚；无显著性晋升；终态仅 `V54_EVIDENCE_INVALID / V54_DELTA8_ALREADY_SUFFICIENT / V54_DELTA16_ADDED_VALUE_SIGNAL / V54_DELTA16_INSUFFICIENT`。

断言边界 verbatim：结果仅支持 `n=1024, m2=184/190/192, Δm=8+8` 上 `H_total=[H_base;H_inc1;H_inc2] 8+8×1024 嵌套增量` 在 `45` fresh held-out 块（每源15，4帧=1024 pairs，`deterministic_four_consecutive_frames_heldout_fresh_v54` 经剩余窗口 `K2-1` 分散 `index_j=floor(j*(K2-1)/14)` 选择，与已用 540 帧零重叠）在 `90-180` calls 上的有界二阶段 rescue 归因（首遍冻结 Lane C 原 support/标签/prior/MET图不改，decoder `90/1.0 poly37`, 泄漏 `leak_base 1064/1094/1104` / `leak_stage1=leak_base+40 (40=5*Δm)` / `leak_stage2=leak_base+80`, `first_pass_success 已成功帧不增泄漏(1064/1094/1104)，stage1_success 为 leak_stage1(1104/1134/1144)，stage2 成功与最终失败均为 leak_stage2(1144/1174/1184)，per_source_avg[s]=leak_base[s]+40×N_stage1[s]/15+40×N_stage2[s]/15，overall_avg=(Σ leak_base[source(block)]+40×N_stage1_total+40×N_stage2_total)/45（分母 45，因三源 leak_base 不同禁单一 leak_base+40N/45 当 overall）`，总 `90-180 硬帽180(L1 45+base45+stage1≤45+stage2≤45)`, `row≤16 full rank nested independence 8+8` 确定性构造不触 outcomes, L2-only tag `≈2^-64` 工程近似，`rescue_rate_stage1=rescued_stage1/N_stage1_attempted, rescue_rate_stage2=rescued_stage2/N_stage2_attempted（分母分别为 count(!verify_base) 与 count(!verify_stage1&&!verify_base) 禁45-base_exact，base_exact 与 verify_base 分别报告）`，`disclosure_per_final_exact_block=total_disclosed_bits/final_exact_full_count（为0则null）`，`f_avg` 分母 `1024×(H(U1|B)+H(U2|U1,B))`），`exact_full` oracle 不经 tag；`V53 33/45` 仅历史描述；均非真帧 FER 全集/阈值/SKR/资格/晋升证据；`45块为 development held-out 确认规模；V54通过仍仅 development confirmation，下一阶段 qualification 需新采集/独立 TEST`；不启动下一阶段。

## 9. 证据写出

固定增量根（decoder 前建，fail-closed）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v54_two_stage_incremental_l2_rescue/run_01/
```

文件：`v54_records.json/.csv` (45-135 L2行：45 base + ≤45 stage1 + ≤45 stage2；每块 `L1 45 + base45 + stage1≤45 + stage2≤45`；`L2 45-135` 行)、`v54_summary.json`、`v54_invalid_notice.json`（失败时）. CSV/JSON 行对等；禁写 NPZ. 本轮 `P0` 不创建上述输出。

## 10. 实现草图（后继轮次，当前未授权）

- `comparison_bench/src/comparison_bench/formal_ir/v54_two_stage_incremental_l2_rescue.py`：import `construct_lane_c_prototype` 常量与 `v35.compute_tag_64`，实现确定性 `H_inc1 8×1024` 复用（V52 det1，`joint1 rank`）+ 确定性 `H_inc2 8×1024` 新增（det2, `total rank`）+ 45 fresh 块剩余窗口枚举分散选择（`K2-1` 公式，零重叠校验）+ 三阶段条件 runner (per block `base 1+条件 stage1 ≤1+条件 stage2 ≤1`，总 `45 L1+45 base+≤45 stage1+≤45 stage2=90-180 硬帽180`).
- `scripts/execute_v54_two_stage_rescue.py`：默认拒绝；`--execution-authorized --authorized-target-sha <sha>`；HEAD/origin 精确绑定未来实现 SHA（plan `bf5dd168...`）；四文件 SCOPED dirty；budget 硬帽 45块三阶段条件执行；执行偏差防复发（不设 600s timeout、建议≥3600s、session/cell ID 只轮询同一进程禁重启、中断保留 raw partial 不聚合、不自动重跑）；任一 gate 失败非零退出.
- 仅 fake-runner 测试；不以 outcomes 定增量或调 `Δm`.

## 11. 自由裁量 D1–D11

- D1 完全冻结 V52/V53 方法（H1/L1-APP/Lane C/H_inc1/H_joint1/decoder/prior/verification 零改），仅新增 `H_inc2` 第二张 `8×1024` 嵌套二阶段。
- D2 单一二阶段 `Δm=8+8` per source 嵌套 rescue，45块 `base vs stage1 vs final` 三阶段配对。
- D3 剩余窗口枚举 `[0..H-4]` 过滤已用 135 区间得 `K2`，`index_j=floor(j*(K2-1)/14)` 分散选 15/源，建议 IDs `395001..` 但真实以 `frame_ids` 为准。
- D4 代表矩阵 3 Lane C base +3 H_inc1 det1 (8×1024)+3 H_inc2 det2 (8×1024)+3 H_total (m2+16)+3 H_joint1 (m2+8)。
- D5 泄漏公式 `leak_base 1064/1094/1104` / `leak_stage1+40` / `leak_stage2+80` 冻结，`first_pass_success_leak=leak_base / stage1_success_leak=leak_stage1 / stage2_leak=leak_stage2 / per_source_avg[s]=leak_base[s]+40×N_stage1[s]/15+40×N_stage2[s]/15 / overall_avg=(Σ leak_base+40×N_stage1_total+40×N_stage2_total)/45` 冻结，`stage1/stage2 rescue_rate` 分母分别为 `count(!verify_base)` 与 `count(!verify_stage1&&!verify_base)`。
- D6 报告 `base/stage1/final` 三层 `exact` 与 `verify` 分别计数、`stage1_rescued/stage2_rescued`、`per_source_avg` 与 `overall_avg` 区分、三类泄漏+`disclosure_per_final_exact_block`（为0则null）+ 四类/G3' + paired `Δexact`，`V53 33/45` 仅历史。
- D7 哨兵每源首块 `395001/395101/395201` 单 L1 通路。
- D8 终态 `V54_EVIDENCE_INVALID / V54_DELTA8_ALREADY_SUFFICIENT / V54_DELTA16_ADDED_VALUE_SIGNAL / V54_DELTA16_INSUFFICIENT`，`EVIDENCE_INVALID` 优先，门禁 `35/45 & 10/15 & undetected==0` 不因 V53 差两个改阈值。
- D9 执行偏差防复发：不设 600s timeout、建议≥3600s、session/cell ID 只轮询同一进程禁重启、中断保留 raw partial 不聚合、不自动重跑。
- D10 `45块 development held-out 确认规模（30块分源仅10不稳定），V54通过仍仅 development confirmation，下一阶段 qualification 需新采集/独立 TEST`。
- D11 文件集条件行记录+聚合+效应+provenance，45块分散 `K2/index_j` 与 `frame_ids` 逐块冻结。
