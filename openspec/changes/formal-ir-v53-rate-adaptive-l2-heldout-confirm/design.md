# OpenSpec Design: formal-ir-v53-rate-adaptive-l2-heldout-confirm

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **仅规划，不实现，不执行 decoder，不创建 run_01。等待独立复审。**
**Cycle**: `V53P0`
**Predecessor**: `formal-ir-v52-rate-adaptive-l2-rescue` (plan HEAD `6aa33eadc872bb4551f458ee750a94cd24566314`, branch `formal-ir-mainline`), **freeze HEAD** `d61d5a3189b54fc0b82e2df688dae3e9bde5ff8e` (branch `formal-ir-mainline`)
**Feasibility**: V52增量`Δm=8`嵌套L2行已由spike三源实证`rank==m2+8`满秩嵌套；1M/1p5M/2M hold库存1683 frames /430k pairs中，排除V48 180+V50 60+V51 60+V52 60=360帧已用后仍富余约1323帧（331个非重叠4帧窗口理论上限），分散选15/源=45块可行；两遍条件执行预算`45 L1+45 base+≤45 rescue=90-135 硬帽135`描述性
**V52 history note**: V52 `12/15`仅作历史描述，非门禁依据

## 1. 科学问题（单因子held-out确认，45块最小稳定规模）

> 在**完全冻结V52完整方法**（首遍`H1-16 + L1-APP + 原Lane C`与泄漏`1064/1094/1104`等价起点，增量`H_inc 8×1024 Δm=8`条件rescue）的**相同参数**下，**V52的增量效应在45个未使用held-out blocks上能否以`35/45`门禁稳定复现？**

- **对照**：无新对照臂；`base/pass1`即`old Lane C`单遍结果（同一次译码），`final`为条件rescue后结果；比较为`base vs final`配对（`Δexact = final - base`描述性）。
- **不改项**：不改support/标签/prior/MET图/`m2`/H1/`max_iter/damping`/`Δm`；不引入第二增量候选或多档率自适应；不做seed搜索或阈值调优。
- **45 vs 30的最小规模论证**：30块分源仅10/源，二项标准误`sqrt(p(1-p)/10)`在`p≈0.8`时约`0.126`，10/15门禁的误判率高；45块分源15/源，标准误约`0.103`，且`35/45`与`10/15`为`7/9≈77.8%`与`2/3≈66.7%`的整数化等比（`35/45=77.78%`与`10/15=66.7%`），是满足每源稳定估计的最小确认规模，过小30块会因单源10样本抖动导致门禁不稳定。
- **通过后的claim边界**：即使`V53_HELDOUT_CONFIRM_PASS`，仍仅为`development confirmation`（方法在held-out上的稳定性确认），**不等同`formal qualification`**。下一阶段`qualification`需**新采集或独立TEST分裂**（`split_manifest`外的独立日期/源或新鲜holdout，且`counts`不重用），并走独立OpenSpec change与执行授权，不能由V53直接晋升为qualification。
- V53不回答H1压缩、标签谱或先验因子，仅回答**嵌套增量rescue在45块held-out上的稳定性**。

## 2. 冻结语义

### 2.1 固定不变项（冻结方法，零改，V52 complete method）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 | |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | Lane C `SOURCE_CHECKS` ordinal-2 `38310x` |
| GF | GF32 `poly=37` (`0b100101`) | `GF2mField.create(32)` |
| 泄漏 base | `leak_base=5*m2+5*16+64 → 1064/1094/1104` | 恒`m1=16`, tag 64b L2-only |
| 泄漏 joint | `leak_joint=5*(m2+8)+80+64 → 1104/1134/1144 (+40)` | `Δm=8` |
| H1 | `V31-H1-QC-16×1024 rank16 80b`母矩阵 | V31权威 |
| 译码 | `decode_row_layered_fftqspa` `max_iter=90,damping 1.0, early-stop` | V43/V52同构 |
| L1-APP | `p_i(u1)=P(U1|B_i)` → `BP_i=decode(H1,p_i,s1).bp_posterior_beliefs` → `q_i=softmax(BP_i)` → `P_i(U2)=Σ q_i P(U2|B,u1)` | TRAIN prior `channel_counts.npz` |
| Verification | `tag_scope=l2_only, compute_tag_64(empty_uint8,x2)` trunc64, `empty=np.empty(0,dtype=np.uint8)`, `syndrome_ok && tag_ok`双条件 | V35 |
| 四类/G3' | `exact / detected / decoder_non_syndrome / undetected`, `G3' undetected==0`单独表 | V46/V52 |
| H_inc/H_joint | `h_inc_1M_det1 / h_inc_1p5M_det1 / h_inc_2M_det1` `8×1024` det1 + `h_joint 192/198/200×1024` nested | V52冻结 |
| Prior | `TRAIN-only` via `load_v25_channel_counts()`，evaluation blocks来自held-out | V25 |
| Rescue触发 | `verification-only`：仅首遍`!verify_base`才rescue，已通过帧不增加泄漏不重译 | V52 |

- **首遍**`L1 wrong`单独报告，不入G3'；`exact_full = exact_u1 && exact_l2` oracle主判据，同时报告`exact_u1/exact_l2`。
- 相同`bob`/`prior`/`P_i(U2)`在`base vs final`间共享；仅`H_L2/syndrome`不同。
- `Δm=8`唯一，**不得新造H_inc或试Δm=4/12/16**。

### 2.2 增量矩阵`H_inc`（唯一，Δm=8，冻结复用V52 det1，禁止新造）

- 每源确定性矩阵`h_inc_{source}_det1` shape `8×1024`, `GF32 poly37`, `row_degree≤16`, `col_degree_inc∈{0,1}` (每列至多一新增边)、`row非零`、`无零增量行`、联合`rank_GF32(H_joint)==m2+8`。
- **嵌套性**：`H_joint = vstack([H_base, H_inc])`，`H_base == H_joint[0:m2, :]`逐比特相等；`syndrome_base`为`syndrome_joint`前缀。
- **独立性**：`rank(H_inc \ rowspace(H_base)) ==8`，即`rank(H_joint)-rank(H_base)==8`。
- **构造（decoder-free确定性，复用V52）**：基于`SeedSequence([600001/600002/600003,1])`的PEG-增量（见V52 spike §4），保证行度均衡`≤16`且与base无短环次级；`coeff`由`SeedSequence([det,2/3])`的`sample_uniform_gf32_nonzero`按规范边序映射。**本变更不重新设计构造规则**，仅复核`rank/nested/independence/row≤16/col≤1/E_inc≈96/泄漏+40`。
- **泄漏**：`leak_joint = leak_base+40`（`5*Δm`）；`Δleak=40`冻结。`first_pass_success_leak=leak_base (1064/1094/1104)`；`rescued_success_leak=leak_joint (1104/1134/1144)`；`final_failure_leak=leak_joint`；`avg_leak = leak_base +40×N_rescue_attempted/45`（`N_rescue_attempted =45 - N_first_pass_success`，含救回与仍失败）。
- **V48/V50/V51/V52无接触**：常量与校验不读其outcomes，仅读其已用`frame_ids`作重叠过滤。

### 2.3 两遍协议（条件HARQ，去重）

```
per block per source (45 blocks):
  prior = TRAIN prior (shared)
  H1 s1 via true u1, L1 decode → BP → q → P(U2)  // 45次总计，per block 1
  base/pass1 (兼old baseline): decode_L2(H_base, P(U2), s_base) → verify_base = syndrome_ok && tag_ok ; exact_base
    // 此一次确定性译码同时作为old Lane C baseline与V53 pass1；old_exact = exact_base, old_verify = verify_base，不另译码
  if verify_base:  final_exact = exact_base, leak = leak_base (=first_pass_success_leak 1064/1094/1104), rescued=False, used_increment=False
  else:           s_inc = H_inc * u2_true ; s_joint=[s_base;s_inc]
                  rescue: decode_L2(H_joint, P(U2), s_joint) → verify2 = syndrome_ok_joint && tag_ok_joint
                  final_exact = exact_rescue, leak = leak_joint (=rescued_success_leak 1104/1134/1144 若救回 else final_failure_leak), rescued = (verify2 && exact_rescue), used_increment=True
  // 每块 L1 1 + base L2 1 + 条件rescue ≤1；45块总 45 L1+45 base+≤45 rescue=90-135 硬帽135，L2 ≤90
```

- `exact_* = array_equal(x_hat, u2_true)` oracle；`tag_ok`为真实L2-only哈希；公开成功以`tag_ok`判，`exact`仅作oracle统计但报告两者。
- **吞吐（去重后冻结）**：每块`L1 1(共享)+base L2/pass1 1(兼old)+条件rescue ≤1`；总`45 L1+45 base+≤45 rescue=90-135 硬帽135，L2 ≤90`。

### 2.4 块与workload（45 fresh held-out, 去重base兼old, 条件二遍）

**库存**：`1683 frames / 430k pairs` hold区间中**未使用且与已用区间零重叠者**。

- Hold区间 per source（`split_manifest 60/20/20`）：
  - 1M: `H=400, base=1600, frames 1600..1999, total 2000, hold last 400`
  - 1p5M: `H=554, base=2213, frames 2213..2766, total 2767`
  - 2M: `H=729, base=2916, frames 2916..3644, total 3645`
- 已用区间 union `U`（per source）由以下设计表汇总（`[start,end]` ordinal，`frame_ids=[base+start .. base+start+3]`）：
  - V48 15/源: 1M 0,28,56,84,113,141,169,198,226,254,282,311,339,367,396；1p5M 0,39,78,117,157,196,235,275,314,353,392,432,471,510,550；2M 0,51,103,155,207,258,310,362,414,466,517,569,621,673,725
  - V50 5/源: 1M 14,42,70,98,127；1p5M 19,58,97,137,176；2M 25,77,129,181,232
  - V51 5/源: 1M 7,35,63,91,119；1p5M 12,51,90,130,169；2M 18,70,122,174,225
  - V52 5/源: 1M 33,61,89,117,146；1p5M 44,83,122,162,201；2M 53,104,155,206,257
  - 早期`FORBIDDEN 96`（V36..V47，含TRAIN开发块，非held-out，忽略held-out过滤但block ID级零重叠）
  - 合计held-out已用`60`区间（`V48 45 + V50 15 + V51 15 + V52 15 =90`区间，但`V48`的45与`V50+51+52`的45叠加为90；`V36..V47`不占held-out故实际held-out已用=60? 待spike精确汇总；此处按90个held-out区间计）

**剩余非重叠四连续窗口枚举算法（冻结）**：

```
per source:
  all_starts = [0..H-4]  # 含重叠的所有可能4帧窗口
  filtered = [s for s in all_starts if not overlaps([s,s+3], U_per_source)]
    # overlaps = 区间交集非空（[s,s+3] ∩ [u,u+3] != ∅）
  S = sorted(filtered)  # 按ordinal start排序
  K = len(S)
  # 要求 K ≥ 15 且 S中任意两窗口已由filtered保证与U零重叠，但S内窗口间可能仍重叠（步长1导致相邻仅差1帧会重叠）。
  # 为得非重叠剩余窗口，再过滤为步长4对齐的非重叠子集？或保留步长1但分散选择保证最终15非重叠。
  # 本设计采用：S为步长1的剩余窗口，K约300/400/600，index_j分散选15后，验证15间两两非重叠（gap≥4），若有重叠则视为REGISTRY_INVALID。
  # 替代严格非重叠枚举：S_strict = [s for s in S if s%4==0]（按4对齐分区得100/138/182理论上限，过滤后K_strict约60-120仍≥15）。
  # spike将同时计算两种K并报告，以S（步长1）分散选为准，但保证最终15两两gap≥4；若不满足则FAIL。
  selected = [S[floor(j*(K-1)/14)] for j in 0..14]  # 确定性分散，j=0..14
  # 若selected中存在重叠（gap<4），则REGISTRY_INVALID
```

- **K的富余校验**：`H-4+1` =397/551/726，减去已用区间覆盖约`60*4=240`帧的膨胀覆盖（每已用区间排除约7个start），剩余`K≈150-500`仍远≥15，分散可行。

- **冻结新45块（建议IDs仅标识，真实由frame_ids决定）**：

  - 建议block IDs: `394001..394015` (1M 15), `394101..394115` (1p5M 15), `394201..394215` (2M 15) — **仅作标识与排序键，真实以frame_ids/ordinal为准**，与 prior block IDs (`390xxx/391xxx/392xxx/393xxx`) 零重叠可机械校验。
  - 每块属性：`block_id` (建议394xxx), `held_out_ordinal_start/end = [selected, selected+3]`, `frame_ids[4]=[base+start .. base+start+3]`, `pairs_count=1024`, `sampling_mode=deterministic_four_consecutive_frames_heldout_fresh_v53`。
  - **Design逐块冻结值**：由`spike_sample_registry.py`按上述算法实际运行后输出的`selected`决定，本design.md §2.4冻结算法与示例，spike_report.md冻结实际数值。**示例（待spike实测固化，当前为算法示意占位，spike执行后替换为实测值）**：

| source | block ID (suggested) | held_out_ordinal `[start,end]` (example) | frame_ids[4] (global, example) | pairs | sampling_mode |
|---|---|---|---|---|---|
| 1M (H=400, base1600) | 394001 | [4,7] | [1604,1605,1606,1607] | 1024 | deterministic_four_consecutive_frames_heldout_fresh_v53 |
| 1M | 394002 | [20,23] | [1620,1621,1622,1623] | 1024 |  |
| 1M | 394003 | [48,51] | [1648,1649,1650,1651] | 1024 |  |
| … | … | … | … | … |  |
| 1M | 394015 | [392,395] | [1992,1993,1994,1995] | 1024 |  |
| 1p5M (H=554, base2213) | 394101 | [5,8] | [2218,2219,2220,2221] | 1024 |  |
| … | 394115 | [545,548] | [2758,2759,2760,2761] | 1024 |  |
| 2M (H=729, base2916) | 394201 | [7,10] | [2923,2924,2925,2926] | 1024 |  |
| … | 394215 | [720,723] | [3636,3637,3638,3639] | 1024 |  |

  - 实际冻结以spike输出为准，proposal/design/spike_report三处一致；spike未执行前design示例仅示意，待执行后principal复核固化。

- 每窗口`4 frames×256=1024 pairs`，`BLOCK_LENGTH=1024`，`pair_idx 0..255`连续；`sampling_mode`固定。
- **Per block calls（去重后冻结）**：每块`L1 1(共享)+base L2/pass1 1(兼old)+条件joint rescue ≤1`；每块L2 1-2次，总预算`45 L1+45 base L2+≤45 rescue L2 = 总90-135 硬帽135，L2 ≤90`。
- **Paired比较（去重语义）**：同block ID同`bob`同`P(U2)`，`base_exact_full` vs `V53_final_exact_full`；增量救回定义为`!base_exact_full && V53_final_exact_full && used_increment`。

## 3. 代表矩阵与译码合约

- **Lane C base**：`lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302` ordinal-2 (committed v38常量，复用).
- **H_inc**：`h_inc_1M_det1 / h_inc_1p5M_det1 / h_inc_2M_det1` deterministic PEG-增量`8×1024` (V52 spike §4, 复用).
- **H_joint**：`h_joint = vstack([H_base, H_inc])` `192/198/200 ×1024` per source.
- **H1**：`V31-H1-QC-16×1024` rank16.
- **译码合约**：共享`GF32 poly37, max_iter=90, damping 1.0, syndrome from true ut, exact = array_equal(x_hat, ut), tag from true x2 via compute_tag_64(empty,x2)`.

## 4. 门禁与效应（描述性，含PASS门禁）

对`45` held-out blocks判定：

- **计数**：`base_exact_full` (首遍单遍, 兼old), `final_exact_full` (V53条件rescue后), `incremental_rescue = final - base`中`used_increment && final_exact`者, `rescue_rate = rescued / (45 - base_exact)`描述性。
- **分源**：1M/1p5M/2M各自`base/final/rescued`。
- **泄漏（三类+平均）**：`first_pass_success_leak = leak_base (1064/1094/1104)`；`rescued_success_leak = leak_joint (1104/1134/1144)`；`final_failure_leak = leak_joint`；`avg_leak = leak_base +40×N_rescue_attempted/45 = (N_first_success*leak_base + N_rescue_attempted*leak_joint)/45`（`N_rescue_attempted =45 - N_first_success`）；`failed_conditional = leak_joint`；`f_avg = avg_leak / [N(H1+H2)]`等报告；`avg disclosure per attempted frame = avg_leak /1024` bits/symbol 描述性。
- **比特总量**：`total_disclosed_bits = Σ leak_total`（45块求和），`final_accepted_bits = Σ (verify_final? (1024*? - leak) ??)`描述性（净有效载荷概念，不作SKR宣称）。
- **矩阵**：每源`base_rank==m2`, `joint_rank==m2+8`, `nested==True`, `independence==8`, `row_degree_max≤16`；`E_inc`报告。
- **Tag**：`tag_ok`真实接受率per pass，`G3' undetected==0`单独表；`syndrome_ok` vs `tag_ok`分流。
- **Paired**：`Δexact = final - base` per block描述性，McNemar `b/c`仅描述性；`Δleak = avg_leak - leak_base`。
- 同时报告`exact_u1/exact_l2/exact_full`、四类、迭代/运行时、`APP entropy/||q-p||1`分布。
- **V52 12/15仅历史描述**，不在V53判据中引用作阈值依据。

**主门禁（冻结）**：

```
V53_HELDOUT_CONFIRM_PASS iff
  final_exact_full ≥35/45 (77.78%) ∧
  每源 final_exact_full ≥10/15 (66.7%) ∧
  undetected_accepted_wrong ==0 (G3') ∧
  joint_rank==m2+8 ∧ nested==True ∧ independence==8 ∧ row≤16 ∧
  verification tag_scope==l2_only ∧
  记账 45 L1+45 base+≤45 rescue=90-135 硬帽且每块L1 1+base1+rescue≤1 ∧
  45 fresh块与已用frame_ids零重叠
else if 完整性/守卫/秩/嵌套/重叠/记账失败 → V53_EVIDENCE_INVALID (优先)
else → V53_HELDOUT_CONFIRM_FAIL
```

- 终态仅三者互斥覆盖，`EVIDENCE_INVALID`优先；`PASS`当且仅当`G1∧G2∧G3'∧rank/nested/记账`全满足；`FAIL`为未满足门禁但完整性通过。
- 通过仍仅`development confirmation`，不晋升qualification。

## 5. O3 配对语义

- 同`block ID`的held-out样本`(idx,alice,bob)`每块确定性一次（4帧窗口`frame_ids[4]`），`L1`单次生成`q_i`与`P_i(U2)`，`base/pass1`同一次确定性译码兼作`old`与`V53`首遍（同`bob`/`P_i(U2)`/`s_base`/`H_base`，不重复译码），`rescue`仅在`base`未通过时以同一`bob`/`P_i(U2)`与`H_joint/s_joint`重译。
- 跨块/跨臂outcome差异为诊断量，永不作完整性失败。

## 6. 科学preflight、守卫序、执行偏差防复发

1. **拒绝类最先**：默认拒绝；必带`--execution-authorized`；`git rev-parse HEAD`与`origin/formal-ir-mainline`与`--authorized-target-sha`精确等值绑定未来实现SHA（plan引用`d61d5a3189b54fc0b82e2df688dae3e9bde5ff8e`）；四文件SCOPED dirty（含`v53`模块、`v53` CLI、`v38_architecture_triage.py`、`v35_algorithm_development.py`）；输出根已存在即拒（J7）；任一拒绝零calls不建文件。Spike脚本任一门禁失败时`sys.exit(1)`非零退出。
2. **科学preflights（decoder-free, write-free）**：seed registry校验（新区45与已用区间零重叠per source + 与V48/V50/V51/V52 `frame_ids`零重叠，无内部重复，每源均分15且分散`index_j`）；`H_base`三矩阵与committed v38常量`rank/support`比对；`H_inc`确定性重建与`joint_rank==m2+8 / nested / independence==8 / row≤16 / col≤1 / E_inc≈96 / leak_base/joint`公式校验；TRAIN counts形态校验；held-out fresh池可达（1683 frames, 剩余K≥45）；首块哨兵`394001/394101/394201`各`L1→P_i(U2)`通路+`tag_import_ok`+`leakage_accounted`+`tag_scope_l2_only`。
3. **执行偏差防复发（冻结）**：
   - **不使用600s外部timeout**：执行器不得以外层600s timeout包裹decoder循环；建议`--timeout`至少`3600s`或不设外部timeout（decoder内部`90/1.0`早停已限单块运行时）。
   - **session/cell ID轮询规则**：若执行返回`session_id/cell_id`，主线程/监督器**只轮询同一`session_id/cell_id`的进程状态**（`poll`/`wait`），**禁止`restart`/`recreate`新session/cell**；若轮询超时或失联，保留raw partial并标记`V53_EVIDENCE_INVALID_INTERRUPTED`，不自动重跑。
   - **中断保留**：若执行在`90-135` calls中途中断（`KeyboardInterrupt`/`timeout`/`OOM`/`BaseException`），已完成的`raw partial`（`v53_records.json`已写行与`started/completed`计数）**原样保留**在预建根内，**不生成`v53_summary.json`聚合**，`completed < planned`且`terminal=V53_EVIDENCE_INVALID_INTERRUPTED`；不自动重跑或补偿。
   - **不自动重跑**：任何`FAIL`或`EVIDENCE_INVALID`后，**禁止自动`rerun/resume/retry`**；需新`EXECUTE_AUTH`且新独立`run_02`（本变更仅`run_01`）。
4. **Preflight失败** → 建增量根写`v53_invalid_notice.json` + 空records + `v53_summary.json` (terminal `V53_EVIDENCE_INVALID`, planned 90-135)后零decoder calls停止。
5. **建根**仅在全部守卫与preflights通过后、首个decoder call前。

## 7. 记录、聚合、summary

每L2 call record schema（含`tag_scope=l2_only, arm∈{base_shared,rescue}`，`base_shared`兼`old`与`V53_pass1`，确定性复用不重复译码）：

```
call_id, source, block_seed(block ID 394xxx), arm(base_shared/rescue), pass_index(1/2), used_increment(bool),
matrix_id(base/joint), h1_matrix_id, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, sampling_mode,
max_iter 90, damping 1.0, errors_initial, errors_final, exact_l2, exact_u1, exact_full,
syndrome_ok_l2/l1, wrong_codeword, target_tag, candidate_tag, tag_ok, tag_scope,
reclassified, iterations_l1/l2, bp_posterior_entropy, mean_abs_diff_q_p, leak_total (1064/1094/1104 or 1104/1134/1144), leak_joint, status, runtime_s
  // leak_total = first_pass_success_leak(1064/1094/1104) 若base通过 else leak_joint(1104/1134/1144)；old_exact派生自base_shared，不另记录
```

Summary含：记账`base_exact_full / rescued_by_increment / final_exact_full / old_exact_full(derived from base)` (overall & per-source, 45块)、`N=45`、`first_pass_success_leak(1064/1094/1104) / rescued_success_leak(1104/1134/1144) / final_failure_leak(leak_joint) / avg_leak(=leak_base+40×N_rescue_attempted/45) / failed_conditional_leak(leak_joint) / avg_disclosure_per_attempted_frame / total_disclosed_bits / final_accepted_bits`描述性；`Δleak=40×N_rescue_attempted/45`；`H_inc joint_rank/nested/independence/E_inc/row_max` provenance；L1诊断；四类计数；G3'；门禁明细（G1/G2/G3'数值与PASS/FAIL，基于`undetected==0`，35/45与10/15权威）；`f_avg`；paired `base vs final Δexact` per block描述性（McNemar `b/c`仅描述，去重）；claim boundary；provenance（含`H_inc det1`与fresh held-out溯源含每块`frame_ids/ordinal`与`K/index_j`）。

## 8. 统计与断言边界

仅描述性；`n=45` blocks配对；比例带n与raw counts；区间naive未校正簇聚；无显著性晋升；终态仅`V53_EVIDENCE_INVALID / V53_HELDOUT_CONFIRM_PASS / V53_HELDOUT_CONFIRM_FAIL`。

断言边界 verbatim：结果仅支持`n=1024, m2=184/190/192, Δm=8`上`H_joint=[H_base;H_inc] 8×1024 嵌套增量`在`45` fresh held-out块（每源15，4帧=1024 pairs，`deterministic_four_consecutive_frames_heldout_fresh_v53`经剩余窗口`K-1`分散`index_j=floor(j*(K-1)/14)`选择，与已用360帧零重叠）在`90-135` calls上的有界rescue归因（首遍冻结Lane C原support/标签/prior/MET图不改，decoder `90/1.0 poly37`, 泄漏`leak_base 1064/1094/1104` / `leak_joint=leak_base+40 (40=5*Δm)`, `first_pass_success已成功帧不增泄漏(1064/1094/1104)，rescued_success与final_failure均为leak_joint(1104/1134/1144)，avg_leak=leak_base+40×N_rescue_attempted/45`，总`90-135 硬帽135(old与pass1同一次确定性译码不重复)`，`row≤16 full rank nested independence==8`确定性构造不触outcomes, L2-only tag `≈2^-64`工程近似），`exact_full` oracle不经tag；`V52 12/15`仅历史描述；均非真帧FER全集/阈值/SKR/资格/晋升证据；`45块为最小确认规模，30块分源仅10不稳定；V53通过仍仅development confirmation，下一阶段qualification需新采集/独立TEST`；不启动V54。

## 9. 证据写出

固定增量根（decoder前建，fail-closed）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v53_rate_adaptive_l2_heldout_confirm/run_01/
```

文件：`v53_records.json/.csv` (90-135 calls: 45 base_shared(兼old/pass1)+ ≤45 rescue；每块`L1 45 + base45 + rescue≤45`；`L2 45-90`行)、`v53_summary.json`、`v53_invalid_notice.json`（失败时）. CSV/JSON行对等；禁写NPZ. 本轮`P0`不创建上述输出。

## 10. 实现草图（后继轮次，当前未授权）

- `comparison_bench/src/comparison_bench/formal_ir/v53_rate_adaptive_l2_heldout_confirm.py`：import `construct_lane_c_prototype`常量与`v35.compute_tag_64`，实现确定性`H_inc 8×1024`复用（§2.2，V52 det1，`joint rank`）+ 45 fresh块剩余窗口枚举分散选择（§2.4，`K-1`公式，零重叠校验）+ 单base译码兼old/V53 pass1 + 条件rescue runner (per block `base 1(兼old)+条件rescue ≤1`，总`45 L1+45 base+≤45 rescue=90-135 硬帽135`).
- `scripts/execute_v53_heldout_confirm.py`：默认拒绝；`--execution-authorized --authorized-target-sha <sha>`；HEAD/origin精确绑定未来实现SHA（plan `d61d5a3189b...`）；四文件SCOPED dirty；budget硬帽45块条件执行；执行偏差防复发（不设600s timeout、建议≥3600s、session/cell ID只轮询同一进程禁重启、中断保留raw partial不聚合、不自动重跑）；任一gate失败非零退出.
- 仅fake-runner测试；不以outcomes定增量或调`Δm`.

## 11. 自由裁量 D1–D11

- D1 完全冻结V52方法（H1/L1-APP/Lane C/H_inc/H_joint/decoder/prior/verification），仅评估45 fresh held-out。
- D2 单一增量`Δm=8` per source嵌套rescue，45块 `base vs final`配对。
- D3 剩余窗口枚举`[0..H-4]`过滤已用区间得`K`，`index_j=floor(j*(K-1)/14)`分散选15/源，建议IDs `394001..`但真实以`frame_ids`为准。
- D4 代表矩阵3 Lane C base +3 H_inc det1 (8×1024)+3 H_joint (m2+8)。
- D5 泄漏公式`leak_base 1064/1094/1104` / `leak_joint+40`冻结，`first_pass_success_leak=leak_base / rescued_success_leak=leak_joint / final_failure_leak=leak_joint / avg_leak=leak_base+40×N_attempt/45`冻结。
- D6 报告门禁`base/final/rescued`与三类泄漏+avg/披露+比特总量描述性 + 四类/G3' + paired `Δexact(去重)`，`V52 12/15`仅历史。
- D7 哨兵每源首块`394001/394101/394201`单L1通路。
- D8 终态`V53_EVIDENCE_INVALID / V53_HELDOUT_CONFIRM_PASS / V53_HELDOUT_CONFIRM_FAIL`，`EVIDENCE_INVALID`优先。
- D9 执行偏差防复发：不设600s timeout、建议≥3600s、session/cell ID只轮询同一进程禁重启、中断保留raw partial不聚合、不自动重跑。
- D10 `45块最小确认规模（30块分源仅10不稳定），V53通过仍仅development confirmation，下一阶段qualification需新采集/独立TEST`。
- D11 文件集条件行记录+聚合+效应+provenance，45块分散`K/index_j`与`frame_ids`逐块冻结。
