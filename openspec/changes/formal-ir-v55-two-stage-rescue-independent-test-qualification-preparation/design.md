# OpenSpec Design: formal-ir-v55-two-stage-rescue-independent-test-qualification-preparation

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **仅规划与数据就绪资格准备，不实现新方法，不执行 decoder，不创建 run_01。等待独立复审与数据就绪裁决。**
**Cycle**: `V55P0`
**Predecessor**: `formal-ir-v54-two-stage-incremental-l2-rescue` (plan HEAD `bf5dd1686049156540328bac264296b17fee546c`, branch `formal-ir-mainline`), **freeze HEAD** `efd34ef318014e1d0505605062057b042e2180eb` (branch `formal-ir-mainline`) — 分层修订保持同一冻结
**Feasibility**: V54 二阶段 `H_total m2+16 嵌套满秩` 已在 V54 spike 三源实证（rank 200/206/208, nested True, row≤16, col_inc≤1, E≈96, leak +40+40）；独立 TEST 的方法侧 feasibility 已足，**唯一 blocker 是数据侧**：需与 2026-01-21 V13 不同的 ≥`S×B` 帧分层独立采集可用性（decoder-free 可检，分层）。
**V54 history note**: V54 `PLAN_CANDIDATE` 未执行 decoder，其 45块 held-out 仍属 development held-out 确认，非独立 TEST；V55 不复用其结论作门禁依据。
**Key judgement**: **算法主线已足够好（V54 二阶段在 held-out 上 rank/nested/泄漏/预算均已冻结可构造），当前 blocker 是独立 TEST 数据缺失（分层）**，而非方法需再调参。

## 1. 科学问题与关键判断

> 在**完全冻结 V54 二阶段完整方法**（首遍 `H1-16 + L1-APP + Lane C` 与泄漏 `1064/1094/1104` 等价起点，`H_inc1 8×1024 Δ8 + H_inc2 8×1024 Δ8` 二阶段 rescue 已冻结 `m2/m2+8/m2+16 嵌套满秩`）的**相同参数**下，**新增分层独立采集 session 的 `S×B` TEST（按物理条件 strata 平衡）能否以预注册分层门禁（per-stratum 10/15 或 20/30 + coverage 35/45 或 70/90 + undetected==0）判定方法在未见数据上的真实泛化？若数据尚不可用，则需何种新数据才算“准备好”（按 strata）？**

- **对照**：无新对照臂；`base` 即 `old Lane C` 单遍结果（同一次译码兼 old），`stage1` 为 `Δ8` 后结果，`final(stage2)` 为 `Δ16` 后结果；比较为 `base vs stage1 vs final` 配对（描述性，门禁仅 `final` 的 per-stratum 与 coverage-domain）。
- **不改项**：不改 support/标签/prior/MET图/`m2`/H1/`max_iter/damping`/`H_inc1/H_inc2`/泄漏公式；**不测新矩阵/标签/prior/阈值/decoder参数**，新增即 `EVIDENCE_INVALID`。
- **B=15 vs 30 的规模**：V54 及之前 held-out 均为 45块 development 确认（分源15不稳定于 70/90 级门禁）；独立 TEST 分层后每 stratum `B=30`（`S=3→90`）使 `70/90` 的 Wilson 下界可区分于偶然性；若数据受限则 `B=15`（`S=3→45`）以 `35/45` 同等 77.8% 门禁保持统计可比性，预算 `90-180` 成比例；每 stratum 块数必须平衡。
- **通过后的 claim 边界**：即使 `V55_INDEPENDENT_TEST_PASS`，仍仅为**分层独立 TEST 在目标域上的泛化确认**（单次 `S×B`，特定新 session strata），不等同全域 FER/阈值/SKR/资格/晋升；需在报告中显式标注各 stratum 的 session 日期/物理条件与 `split_manifest` 外新数据身份。
- V55 不回答 H1 压缩、标签谱或先验因子，仅回答**二阶段方法在分层独立 TEST 上的数据就绪资格与预注册门禁**。

## 2. 冻结语义 — V54 方法零改

### 2.1 固定不变项（冻结方法，零改，V54 complete method）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 | V31 |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | Lane C `SOURCE_CHECKS` ordinal-2 `38310x` |
| GF | GF32 `poly=37` (`0b100101`) | `GF2mField.create(32)` |
| 泄漏 base | `leak_base=5*m2+5*16+64 → 1064/1094/1104` | `m1=16`, tag 64b L2-only |
| 泄漏 stage1 | `leak_stage1=5*(m2+8)+80+64 → 1104/1134/1144 (+40)` | `Δm=8` |
| 泄漏 stage2 | `leak_stage2=5*(m2+16)+80+64 → 1144/1174/1184 (+80)` | `Δm=16` |
| H1 | `V31-H1-QC-16×1024 rank16 80b` 母矩阵 | V31 权威 |
| 译码 | `decode_row_layered_fftqspa` `max_iter=90, damping 1.0, early-stop` | V43/V52 同构 |
| L1-APP | `p_i(u1)=P(U1|B_i)` → `BP_i=decode(H1,p_i,s1).bp_posterior_beliefs` → `q_i=softmax(BP_i)` → `P_i(U2)=Σ q_i P(U2|B,u1)` | TRAIN prior `channel_counts.npz` |
| Verification | `tag_scope=l2_only, compute_tag_64(empty_uint8,x2)` trunc64, `syndrome_ok && tag_ok` 双条件 | V35 |
| 四类/G3' | `exact / detected / decoder_non_syndrome / undetected`, `G3' undetected==0` 单独表 | V46/V52 |
| H_inc1/H_joint1 | `h_inc_1M_det1 / h_inc_1p5M_det1 / h_inc_2M_det1` `8×1024` det1 + `h_joint1 192/198/200×1024` nested | V52 冻结 |
| H_inc2/H_total | `h_inc_1M_det2 / h_inc_1p5M_det2 / h_inc_2M_det2` `8×1024` det2 + `h_total 200/206/208×1024` nested | V54 冻结 |
| Prior | `TRAIN-only` via `load_v25_channel_counts()`，evaluation blocks 来自独立 TEST（非 TRAIN） | V25 |
| Rescue触发 | `verification-only`：仅未通过 `verify` 才进入下一阶段，已通过帧不增加泄漏不重译 | V52/V53/V54 |
| Δm | `8+8=16` per source 冻结，`leak_stage1-leak_base=40` `leak_stage2-leak_stage1=40` | V54 |

- `exact_* = array_equal(x_hat, u2_true)` oracle 主判据，同时报告 `exact_u1/exact_l2`；`exact` 仅统计不触发增量。
- 相同 `bob`/`prior`/`P_i(U2)` 在 `base vs stage1 vs final` 间共享；仅 `H_L2/syndrome` 不同。
- **V55 禁止任何新矩阵/标签/prior/阈值/decoder 参数变更**，违者 `EVIDENCE_INVALID`。

### 2.2 数据裁决（当前定性，不可逆）

- V13 `60/20/20 (TRAIN/VAL/HOLD)`：`split_manifest.json` 将 `2000/2767/3645` 帧（1M/1p5M/2M）按 `60% TRAIN / 20% VAL / 20% HOLD` 划分，HOLD 区间为 `H=400/554/729, base=1600/2213/2916`。
- **污染认定**：HOLD 已被 `V48 45块 + V50 15 + V51 15 + V52 15 + V53 45 + V54 45 =180块` 开发使用（V48-V54 已用 135-180 区间，540-720 帧），**已用于方法选择、增量秩验证、leakage 预算讨论与门禁探索**，即使 HOLD 仍有 `K2≈135/260/461` 剩余窗口未译码，也**不得改称为独立 TEST**（开发污染不可逆，selection bias 已注入）。
- **后果**：HOLD 剩余帧仅可作 development 诊断，不可作 qualification TEST；P0 必须**搜索/登记另一独立采集 session 集合**（与 `2026-01-21` V13 不同日期/采集 batch，按物理条件分层），若无则 `V55_DATA_NOT_READY`（非失败，需新数据，分层），**不得用 HOLD 冒充**。

### 2.3 合格 TEST 要求（分层，建议，非本轮执行，仅预冻结）

- **目标运行域声明（冻结）**：`D_target = { stratum_1M, stratum_1p5M, stratum_2M }`，三 stratum 分别对应物理条件 `delay -50ps/1M、+50ps/1p5M、+50ps/2M`（含各自功率/率/器件/信道参数）；`D_target` 为资格判定的必须覆盖域。超出 `D_target` 的新增物理条件（如新地点/器件/信道参数）为 exploratory stratum，不计入 `D_target` 门禁，仅作泛化探索。
- **库存**：先列 `available_independent_datasets` — 所有可用的其他独立数据集及其物理条件（采集日期/地点/器件/信道参数等 provenance），形成分层库存表。
- **Session**：建议每 stratum 各一个与 `2026-01-21 V13` 不同的独立采集 session（例如 `2026-0X-XX` 新采集），每 stratum **≥120 frames（建议≥160）**，每帧 **256 pairs**（`pairs.parquet` 每帧 256 行，`pair_idx 0..255` 连续），每块 **4 连续帧 =1024 pairs (`BLOCK_LENGTH=1024`)**。
- **隔离**：新 session **不入 prior 训练**（V25 `channel_counts.npz` 仍为 TRAIN-only，`split_manifest` 外），**不入方法选择**，**冻结前不得看解码结果**（先登记文件与 frame_ids，再译码）。
- **主样本（平衡）**：每主要 stratum `B ∈{15,30}` blocks（平衡，推荐 `30`；数据受限时 `15`），`S=|D_target|=3` 时共 `S×B =45 (B=15) 或 90 (B=30)` blocks，`S×B×4` frames。于新 session 每 stratum 内枚举 `all_starts=0..F-4`（F=每 stratum 总帧数，≥120），过滤与已用区间重叠者（与 V13 及 V48-V54 零重叠）得 `S2` 按 ordinal 排序 `K=|S2|`，以 `index_j=floor(j*(K-1)/(need-1)) j=0..need-1` 确定性分散选择 `need=B` 块/ stratum，验证两两非重叠 gap≥4 且与 V13 及 V48-V54 零重叠 per stratum。
- **不足处理**：数据不足的 stratum（`K < B`）仅 exploratory，不强行凑 `S×B`；该 stratum 判 `G7_FAIL → DATA_NOT_READY` 但不阻塞其他 stratum 的报告。
- **标识**：建议 block IDs 按 stratum 延续（如 `B=30` 时 `396001-030 / 396101-130 / 396201-230`；`B=15` 时 `397001-015` 等）仅作标识，真实以 `frame_ids[4]=[global_offset+start .. global_offset+start+3]` 为准，`sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_stratified`，`pairs_count=1024, BLOCK_LENGTH=1024`，**禁换块/禁重采样**。

### 2.4 三阶段协议（条件 HARQ，verification-only，预冻结，未来执行，分层）

```
per block per stratum (S×B blocks, e.g. 45 or 90):
  prior = TRAIN prior (shared, V25)
  H1 s1 via true u1, L1 decode → BP → q → P(U2)  // S×B 次总计，per block 1
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
  // 每块 L1 1 + base L2 1 + 条件 stage1 ≤1 + 条件 stage2 ≤1；S×B 块总 L1 SB+base SB+≤SB stage1+≤SB stage2=2SB-4SB 硬帽，L2 SB-3SB
```

- `exact_*` oracle；`tag_ok` 真实 L2-only 哈希；公开成功以 `tag_ok` 判，`exact` 仅作 oracle 统计但报告两者。
- **吞吐冻结（分层成比例）**：每块 `L1 1(共享)+base 1+条件 stage1 ≤1+条件 stage2 ≤1`；总 `L1 SB+base SB+stage1≤SB+stage2≤SB=2SB-4SB 硬帽，L2 SB-3SB`。`S=3,B=30 → 180-360 硬帽360，L2 90-270`；`S=3,B=15 → 90-180 硬帽180，L2 45-135`。

## 3. 数据就绪门（本轮唯一实测，decoder-free，G1-G7 分层）

| 门 | 检查项 | 判定 | 失败终态 |
|---|---|---|---|
| G1 | 文件可读 | 每 stratum 新 session `pairs.parquet`/`pairs.csv` 可 open，行数 = frames×256，每列 `uint8/uint16` 合法 | `V55_DATA_NOT_READY` (G1_FAIL, per stratum) |
| G2 | provenance 完整 | 各 stratum session_id、采集日期≠2026-01-21、采集参数（延迟±50ps、功率/率、地点/器件）、文件哈希/行数可追溯，`provenance.json` 可读 | `V55_DATA_NOT_READY` (G2_FAIL, per stratum) |
| G3 | 各 stratum 明确 | `D_target` 各 stratum 各一 session，互异且与 V13 对应物理条件一一对应；exploratory strata 额外列出 | `V55_DATA_NOT_READY` (G3_FAIL) |
| G4 | 256/frame 1024/block | 每 stratum 每帧 256 pairs，每块 4 连续帧 1024 pairs，`BLOCK_LENGTH=1024`，`sampling_mode` 固定 | `V55_DATA_NOT_READY` (G4_FAIL, per stratum) |
| G5 | 与 V13 及 V48-V54 完全独立 | 新 session 各 stratum 全部帧与 V13 全部帧及 V48-V54 已用 540-720 帧零重叠，per stratum 机械校验 | `V55_DATA_NOT_READY` (G5_FAIL, per stratum) |
| G6 | V25 prior 只读 | `channel_counts.npz` 形态校验（`num_counts == TRAIN 60%`），**不读新 TEST 做训练**，`load_v25_channel_counts()` 可 import | `V55_EVIDENCE_INVALID` (G6_FAIL, 训练污染, 全局) |
| G7 | 冻结 per-stratum registry | 每目标域 stratum 枚举 `all_starts 0..F-4` 得 `S2`，`K≥B`，`index_j=floor(j*(K-1)/(B-1))` 分散选 B 块/ stratum，两两非重叠 gap≥4，与 V13 及 V48-V54 零重叠，可机械校验；`K<B` 则该 stratum `G7_FAIL` | `V55_DATA_NOT_READY` (G7_FAIL, per stratum; 允许 partial) |

- 目标域 `D_target` 全部 strata G1-G7 全过 → `V55_QUALIFICATION_PLAN_READY`（可进入正式 TEST 详细规划与 `EXECUTE_AUTH`）。
- 任一目标域 stratum 不过 → `V55_DATA_NOT_READY`（分层，非失败，需新数据），**不过则不得创建 production runner/tests/正式 output root**，仅报告缺口与所需新数据规格；非目标域 exploratory strata 的 `G7_FAIL` 不阻塞 `D_target` 的 READY 判定，但该 exploratory stratum 仅作探索性报告。
- 本轮脚本 `check_v55_data_readiness.py` 按 strata 执行 G1-G7 的 decoder-free 分支，零 `decode_*` 调用，`sys.exit(1)` 于任一目标域 G1-G7 失败（`V55_DATA_NOT_READY` 不等同 `EVIDENCE_INVALID`，但同样非零退出以阻断后续）。

## 4. 预算（预冻结，未来执行，分层成比例）

- `L1 S×B` 固定（每块 1 次 `H1→BP→P(U2)`，共享于三阶段）。
- `base L2 S×B` 固定（每块 1 次 `H_base`）。
- `stage1 L2 0–S×B` 条件（仅 `!verify_base` 者）。
- `stage2 L2 0–S×B` 条件（仅 `!verify_base && !verify_stage1` 者）。
- 总 `S×B L1+S×B base+0–S×B stage1+0–S×B stage2 =2SB–4SB 硬帽，L2 SB–3SB`，`per block 2-4 calls`，`base` 兼 old 不重复。
- 示例：`S=3,B=30 → 90+90+≤90+≤90=180-360 硬帽360，L2 90-270`；`S=3,B=15 → 45+45+≤45+≤45=90-180 硬帽180，L2 45-135`。
- 预计实际 `≈ 90+90+约30 stage1+约15 stage2 =225`（当 `S=3,B=30` 且 base 准确率 ~66%）；硬帽远未触及。

## 5. 门禁与效应（预冻结，描述性，含 PASS 门禁与终态，分层）

对 `S×B` 独立 TEST blocks（仅目标域）判定：

- **计数**：`base_exact_full` 与 `verify_base` 分别计数（禁止假定相等），`stage1_exact_full` 与 `verify_stage1` 分别，`final_exact_full` 与 `verify_final` 分别；`stage1_rescued = rescued_by_inc1`、`stage2_rescued = rescued_by_inc2`；`N_stage1_attempted=count(!verify_base)`、`N_stage2_attempted=count(!verify_base && !verify_stage1)`；分母禁止 `SB-base_exact`。
- **分层**：各 stratum 各自 `base/stage1/final/rescued_stage1/rescued_stage2` 与 `leakage/rescue_rate`，主要报告按 stratum，不混总分。
- **泄漏（三类+平均+总量，分层）**：`first_pass_success_leak=leak_base (1064/1094/1104)`；`stage1_success_leak=leak_stage1 (1104/1134/1144)`；`stage2_leak=leak_stage2 (1144/1174/1184)`（stage2 成功与最终失败同为 `leak_stage2`）；`per_stratum_avg[s]=leak_base[s]+40×N_stage1[s]/B+40×N_stage2[s]/B`，`coverage_avg=(Σ leak_base[source(block)]+40×N_stage1_total+40×N_stage2_total)/(S×B)`；`failed_conditional=leak_stage2`；`avg_disclosure_per_attempted=coverage_avg/1024` 描述性；`total_disclosed_bits=Σ leak_total` 与 `disclosure_per_final_exact_block=total_disclosed_bits/final_exact_full_count（为0则null）`。
- **矩阵**：每 stratum `base_rank==m2, joint1_rank==m2+8, total_rank==m2+16, nested_stage1==True, nested_stage2==True, independence_1==8, independence_2==8, row≤16`；`E_inc1/E_inc2` 报告。
- **Tag**：`tag_ok` 真实接受率 per stage per stratum，`G3' undetected==0` 单独表（全局）。
- **预注册门禁（冻结，分层）**：

```
V55_DATA_NOT_READY  若任一目标域 stratum G1-G7 不过（分层，非失败，需新数据；exploratory strata partial 不算全局 FAIL 但该 stratum 仅探索）
else if 完整性/守卫/秩/嵌套/重叠/记账失败 → V55_EVIDENCE_INVALID 优先
else if per_stratum final_exact_full ≥ (B==30?20:10)/B 且 coverage_exact_full ≥ ceil(0.778×S×B)
        （即 S=3,B=30 时 70/90；S=3,B=15 时 35/45） ∧ 每目标域 stratum 均满足 per-stratum 门禁
        ∧ undetected==0 全局 ∧ rank/nested/verification/记账通过
     → V55_INDEPENDENT_TEST_PASS
else → V55_INDEPENDENT_TEST_FAIL (完整性通过但未过门禁)
```

- `base/stage1` 仅诊断，**最终以 `base→Δ16` 主判**，`stage1` 报告不取代最终；`Wilson 95%`/`rescue_rate`/`runtime`/`leakage` 仅报告（按 stratum）。
- 不加复杂终态，不晋升 qualification 外推。
- exploratory  strata（数据不足或非目标域）不计入门禁分母，仅报告 `exact/泄漏/rescue` 作泛化探索。

## 6. O3 配对语义与预注册统计（分层）

- 同 stratum 同 `block ID` 的独立 TEST 样本 `(idx,alice,bob)` 每块确定性一次（4帧窗口 `frame_ids[4]`），`L1` 单次生成 `q_i` 与 `P_i(U2)`，`base` → `stage1`（仅 `!verify_base`）→ `stage2`（仅 `!verify_after_stage1`）条件递进，同 `bob`/`P_i(U2)`/`s` 的嵌套前缀，`exact` 仅 oracle 统计。
- 跨块/跨臂 outcome 差异为诊断量，永不作完整性失败。
- 预注册统计：per-stratum `10/15 或 20/30` 与 coverage `35/45 或 70/90` 的 Wilson 95% 下界将按 stratum 与 coverage 分别报告，但**不作门禁**；仅分层硬门禁作判定。

## 7. 科学 preflight、守卫序、执行偏差防复发（预冻结，未来执行）

1. **拒绝类最先**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定未来实现 SHA（plan 引用 `efd34ef...`）；四文件 SCOPED dirty（含 `v55` 模块、`v55` CLI、`v38`、`v35`）；数据就绪门 `G1-G7` 按 strata 未过即拒（任一目标域 stratum `V55_DATA_NOT_READY`）；输出根已存在即拒（J7）；任一拒绝零 calls 不建文件。
2. **科学 preflights（decoder-free, write-free，未来执行前）**：分层 `G1-G7` 全检（per stratum `B=15/30` 可达性 + `K≥B`）+ `H_base` 三矩阵与 committed v38 常量 `rank/support` 比对 + `H_inc1/H_inc2` 确定性重建与 `rank_total==m2+16 / nested / independence==8 / row≤16 / col≤1 / E≈96 / leak+40+40` 校验 + TRAIN counts 形态校验 + 各 stratum 独立 TEST 池 `K≥B` 可达 + 每 stratum 首块哨兵 `L1→P_i(U2)` 通路。
3. **执行偏差防复发（冻结）**：
   - 不使用 600s 外部 timeout；建议 `--timeout` 至少 `3600s` 或不设外部 timeout（decoder 内部 `90/1.0` 早停已限时）。
   - 若执行返回 `session/cell ID`，只轮询同一 `session/cell ID` 进程状态，禁止 `restart`/`recreate` 新 session。
   - 中断保留 raw partial 不聚合、不自动重跑。
4. **Preflight 失败** → 写 `v55_invalid_notice.json` + 空 records + `v55_summary.json` (terminal `V55_EVIDENCE_INVALID` 或 `V55_DATA_NOT_READY` 分层) 后零 decoder calls 停止。
5. **建根**仅在全部守卫与 preflights 通过后、首个 decoder call 前。

## 8. 记录、聚合、summary（预冻结，未来执行，分层）

每 L2 call record schema（含 `tag_scope=l2_only, arm∈{base,stage1,stage2}, stratum`）：

```
call_id, source/stratum, block_seed(block ID), arm(base/stage1/stage2), pass_index(1/2/3), used_inc1(bool), used_inc2(bool),
matrix_id(base/joint1/total), h1_matrix_id, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, sampling_mode(stratified),
max_iter 90, damping 1.0, errors_initial, errors_final, exact_l2, exact_u1, exact_full,
syndrome_ok_l2/l1, wrong_codeword, target_tag, candidate_tag, tag_ok, tag_scope,
reclassified, iterations_l1/l2, bp_posterior_entropy, mean_abs_diff_q_p, leak_total (1064/1094/1104 or 1104/1134/1144 or 1144/1174/1184), leak_stage1, leak_stage2, status, runtime_s
```

Summary 含：按 strata 记账 `base_exact_full` 与 `verify_base` 分别计数（per stratum & coverage-domain `S×B`）、`stage1_exact_full` 与 `verify_stage1` 分别、`final_exact_full` 与 `verify_final` 分别、`stage1_rescued / stage2_rescued / final`、`N_stage1_attempted=count(!verify_base)` 与 `N_stage2_attempted=count(!verify_stage1&&!verify_base)`（per stratum & coverage）、`rescue_rate_stage1/stage2` per stratum、`per_stratum_avg` 与 `coverage_avg`、`Wilson 95%` per stratum & coverage、`total_disclosed_bits` 与 `disclosure_per_final_exact_block` 等描述性；`Δleak_per_stratum`，`Δleak_coverage`；`H_inc1 joint1_rank/nested/independence` 与 `H_inc2 total_rank/nested/independence` provenance；L1 诊断；四类计数；G3'；门禁明细（`final` 的 per-stratum 与 coverage G1/G2/G3' 数值与 `V55_*` 终态）；`Wilson 95%`；paired `base vs stage1 vs final` per block 描述性；`V54 45块` 仅历史描述；exploratory strata 单独章节（不计入门禁）。

## 9. 证据写出（预冻结，未来执行，不在本轮）

固定增量根（decoder 前建，fail-closed）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v55_two_stage_rescue_independent_test/run_01/
```

文件：`v55_records.json/.csv` (`S×B` 块对应 `SB-3SB` L2行：`SB base + ≤SB stage1 + ≤SB stage2`；总 calls `2SB-4SB` 硬帽)、`v55_summary.json`（分层）、`v55_invalid_notice.json`（失败时）、`v55_data_readiness.json`（分层 `G1-G7` 逐 stratum）。CSV/JSON 行对等；禁写 NPZ. **本轮 `P0` 不创建上述输出**，仅在 `openspec/changes/.../data_readiness_report.md` 报告分层 G1-G7 逐项与 `V55_DATA_NOT_READY` 分层缺口。

## 10. 实现草图（后继轮次，当前未授权，仅当目标域全 DATA_READY 后）

- `comparison_bench/src/comparison_bench/formal_ir/v55_two_stage_rescue_independent_test.py`：import `construct_lane_c_prototype` 常量与 `v35.compute_tag_64`，实现确定性 `H_inc1 det1` 复用 + `H_inc2 det2` 新增 + 分层 `S×B` 独立 TEST 剩余窗口枚举分散选择（`K-1` 公式 per stratum，零重叠校验）+ 三阶段条件 runner (per block `base 1+条件 stage1 ≤1+条件 stage2 ≤1`，总 `2SB-4SB` 硬帽，分层预算)。
- `scripts/execute_v55_independent_test.py`：默认拒绝；`--execution-authorized --authorized-target-sha <sha>`；HEAD/origin 精确绑定未来实现 SHA（plan `efd34ef...`）；四文件 SCOPED dirty；分层 `G1-G7` 数据就绪门前置（目标域全 READY）；budget 硬帽 `S×B` 块三阶段条件执行；执行偏差防复发（不设 600s timeout、建议≥3600s、session/cell ID 只轮询同一进程禁重启、中断保留 raw partial 不聚合、不自动重跑）；任一目标域 gate 失败非零退出。
- 仅 fake-runner 测试通过后才可进入数据就绪后的正式 TEST；不以 outcomes 定增量或调 `Δm`。

## 11. 自由裁量 D1–D11（分层修订）

- D1 完全冻结 V54 方法（H1/L1-APP/Lane C/H_inc1/H_inc2/decoder/prior/verification 零改），V55 不新增矩阵/标签/prior/阈值。
- D2 单一二阶段 `Δm=8+8` per source 嵌套 rescue，`S×B` 块 `base vs stage1 vs final` 三阶段配对（未来执行，分层）。
- D3 新 session 分层搜索与分层 `G1-G7` decoder-free 数据就绪门，`V55_DATA_NOT_READY` 分层非失败语义，库存先行。
- D4 分层独立 TEST `S×B` 注册算法：每 stratum `[0..F-4]` 枚举过滤已用区间得 `K`，`index_j=floor(j*(K-1)/(B-1))` 分散选 B/ stratum，建议 IDs 按 stratum 延续但真实以 `frame_ids` 为准；不足 strata 仅 exploratory。
- D5 预算 `2SB-4SB` 硬帽（`S=3,B=15→90-180`；`S=3,B=30→180-360`），`base` 兼 old 不重复，分层成比例。
- D6 预注册门禁分层：`per-stratum 10/15或20/30 ∧ coverage 35/45或70/90 ∧ undetected==0`，`base/stage1` 仅诊断，最终 `base→Δ16` 主判；`Wilson/rescue/runtime/leakage` 仅报告；exploratory 不计入门禁。
- D7 哨兵每 stratum 首块单 L1 通路（未来执行）。
- D8 终态 `V55_DATA_NOT_READY (分层) / V55_EVIDENCE_INVALID / V55_INDEPENDENT_TEST_PASS / V55_INDEPENDENT_TEST_FAIL`，`DATA_NOT_READY` 非失败，partial 允许。
- D9 执行偏差防复发：不设 600s timeout、建议≥3600s、session/cell ID 只轮询同一进程禁重启、中断保留 raw partial 不聚合、不自动重跑。
- D10 `S×B` 块分层独立 TEST 确认规模（45 块 `B=15` 或 90 块 `B=30` 均可；原 45块 development 不稳定），通过仍仅分层独立 TEST 确认，不扩大为全域 FER。
- D11 文件集条件行记录+聚合+效应+provenance，分层 `S×B` 分散 `K/index_j` 与 `frame_ids` 逐块冻结；本轮仅交付四工件+decoder-free 分层清单脚本/报告。
