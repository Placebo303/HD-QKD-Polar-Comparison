# OpenSpec Design: formal-ir-v50-l2-structure-factorial

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V51。等待独立评审。**
**Cycle**: `V50P0`
**Predecessor**: V48 held-out-confirm result `28228b9d` + diagnostic `f58955f3e794dbde11b4d813eec061182319846d`, branch `formal-ir-mainline` HEAD `f58955f3e794dbde11b4d813eec061182319846d`
**Feasibility**: 单一等泄漏真 MET 候选可在 `n=1024, m2=184/190/192, GF32 poly37, dc_max=16, E=2560 ({dv2:512,dv3:512})` 下 decoder-free 构造并通过秩/零列/4-cycle/链环门（已由 spike 三矩阵实证）；全 `dv=2` 非 MET，若用则改名 `PEG-dv2, E=2048`；15 未使用 held-out 块富余；90-call 2×2 因子预算冻结

## 1. 科学问题（两个正交因子，单一等泄漏结构候选）

> 在**相同 `m2` 与泄漏**下，**结构**（Lane C `L=8,w=2`  vs  单一等泄漏 protograph/MET `P0-MET-1`）与 **先验**（TRAIN vs TRAIN+VAL）的各自因果贡献是多少？

- **主方向（结构）**：真 MET 混合度 `P0-MET-1 {dv2:512,dv3:512}` vs Lane C；simple effect `C-A` 为 `TRAIN` 先验下结构效应（非主效应）。
- **正交对照（先验）**：`B-A` 为 `Lane C` 结构下先验 simple effect（`TRAIN+VAL` vs `TRAIN`）。
- **主效应与交互**：`E_structure=(C+D-A-B)/2`，`E_prior=(B+D-A-C)/2`，`E_interaction=(D-C)-(B-A)`；另保留四个 simple effects `C-A / D-B / B-A / D-C`。
- V50 不回答 H1 压缩或综合泄漏优化，仅回答等泄漏结构与先验两因子的分解效应。

## 2. 冻结语义（单候选等泄漏结构 + 双 prior）

### 2.1 固定不变项（不得调参）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 |  |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | Lane C `SOURCE_CHECKS` |
| GF | GF32 `poly=37` (`0b100101`) | `GF2mField.create(32)` |
| 泄漏 | `leak_total=5*m2+5*16+64` → `1064/1094/1104` | 恒 `m1=16`, `tag 64b` L2-only |
| H1 | `V31-H1-QC-16×1024 rank16 80b` 母矩阵 | V31/V47 权威，经 `build_matrix_packet(m1=16)` |
| 译码 | `decode_row_layered_fftqspa` `max_iter=90,damping 1.0, early-stop` | V43/V47 同构 |
| Verification | `tag_scope=l2_only, compute_tag_64(empty_uint8,x2)` trunc64 | V35 |
| 四类/G3' | `exact / detected / decoder_non_syndrome / undetected`, `G3' undetected==0` | V46/V47 |

- **单臂结构候选**仅 `P0-MET-1`；Lane C 为对照结构，不在同 candidate 内重搜 seed。
- `L1 wrong` 单独报告，不入 G3'。

### 2.2 结构候选 P0-MET-1（唯一，禁止 seed 搜索）— 真 MET

- 每源确定性矩阵 `p0_met_{source}_det1` shape `m2×1024`, `GF32 poly37`, **真 MET 混合度 `{dv2:512,dv3:512}, E=2560, dv_mean=2.5`**（`E` 不决定泄漏；全 `dv=2 E=2048` 非 MET，若用则改名 `PEG-dv2`），`dc_max≤16`, `col_degree_min≥1` (分布 `512×2+512×3`, 无零列), `rank==m2`.
- **构造**：deterministic PEG-MET — 每列 `j` 按 `dv_list`（`j<512→2, else 3`）依次选最小度 check 集合中按 frozen `perm_p=SeedSequence([50000x,1])` tie-break 的 check 集合，且 `check_pairs_connected` 对 `dv=2` 的 1 对与 `dv=3` 的 3 对全局唯一 → `support_cycles_4==0` 硬门。 coeff 由 `SeedSequence([50000x,2])` 的 `sample_uniform_gf32_nonzero` 按规范边序映射。
- **Degree-2 约束（精确）**：定义 `G2` 为仅 `dv=2` 变量及其关联边诱导子图。**degree-2 链**为 `G2` 内极大路径且内部校验在 `G2` 内度为 2；`max_degree2_chain≤4` vars 硬门。**degree-2 纯环**为双分长度 `≤12`（即 `vars*2 ≤12`，`vars≤6`）且环上所有变量 `dv=2` 的闭环；`degree2_pure_ring(len≤12)==0` 硬门，度量为 `pure_ring_via_graph` 与枚举 `pure_4/6/8`（spike §5 实测）。
- **Lifting/label 确定性**：`Q=1` 直接有限矩阵（`2` 种变量类型即 MET 类型划分），shift/label 均由上述两个确定性子流派生；无随机 seed 轮询。
- **与 Lane C 等泄漏**：相同 `m2` → 相同 `leak_total=5*m2+80+64`，`f_total=leak/[N(H1+H2)] N=1024` 一致；`E` 不同不影响泄漏。
- **4-cycle 优先消除**：硬 `0`；`6/8-cycles` 仅报告（`enumerate_canonical_simple_cycles` + `classify_cycle_algebraic_degeneracy`，`pure_*` 单独报告）。
- **行度冻结**：`row_degree_max≤16`；`E=2560`（MET）/ `2048`（PEG-dv2）分别冻结，不以泄漏冻结 `E`。
- **V48 无接触**：常量与校验不读 `v48_*` outcomes。

### 2.3 先验因子（正交）

- **A/C 臂先验**：`TRAIN prior` — `counts_T = load_v25_channel_counts()` (TRAIN 60% 区间 `channel_counts.npz`).
- **B/D 臂先验**：`TRAIN+VAL prior` — `counts_TV = TRAIN⊕VAL` 合并 counts（按 `split_manifest 60/20/20` 的 TRAIN 与 VAL 帧 counts 相加，归一化同 `P(U1|B)/P(U2|B,u1)` 接口），经同一先验构造路径，不改 `channel_counts.npz` 文件。
- 先验仅影响 `L1 p_i(u1)=P(U1|B_i)` → `BP_i=decode(H1,p_i,s1).bp_posterior_beliefs` → `q_i=softmax(BP_i)` → `P_i(U2)=Σ q_i P(U2|B,u1)`；不改矩阵/泄漏/decoder。

### 2.4 块与 workload（15 未使用 held-out, 2×2 因子, 90 calls）

库存：`1683 frames / 430k pairs` hold 区间中 **未使用**者（排除 `FORBIDDEN 141 = 96(V36..V47)+45(V48)` block ID 且与 V48 180 帧 `frame_ids` 零重叠 per source）。

冻结新区（每块写死 `4` 真实 `frame_ids` 与 `ordinal`，与 V48 `HELDOUT_STARTS` 分散窗口零重叠，见 spike_report §8）：

| source | block ID | held_out_ordinal `[start,end]` | frame_ids[4] (global) | pairs |
|---|---|---|---|---|
| 1M (H=400, base1600) | 391001 | [14,17] | [1614,1615,1616,1617] | 1024 |
| 1M | 391002 | [42,45] | [1642,1643,1644,1645] | 1024 |
| 1M | 391003 | [70,73] | [1670,1671,1672,1673] | 1024 |
| 1M | 391004 | [98,101] | [1698,1699,1700,1701] | 1024 |
| 1M | 391005 | [127,130] | [1727,1728,1729,1730] | 1024 |
| 1p5M (H=554, base2213) | 391101 | [19,22] | [2232,2233,2234,2235] | 1024 |
| 1p5M | 391102 | [58,61] | [2271,2272,2273,2274] | 1024 |
| 1p5M | 391103 | [97,100] | [2310,2311,2312,2313] | 1024 |
| 1p5M | 391104 | [137,140] | [2350,2351,2352,2353] | 1024 |
| 1p5M | 391105 | [176,179] | [2389,2390,2391,2392] | 1024 |
| 2M (H=729, base2916) | 391201 | [25,28] | [2941,2942,2943,2944] | 1024 |
| 2M | 391202 | [77,80] | [2993,2994,2995,2996] | 1024 |
| 2M | 391203 | [129,132] | [3045,3046,3047,3048] | 1024 |
| 2M | 391204 | [181,184] | [3097,3098,3099,3100] | 1024 |
| 2M | 391205 | [232,235] | [3148,3149,3150,3151] | 1024 |

- 每窗口 `4 frames ×256=1024 pairs`，`BLOCK_LENGTH=1024`，`pair_idx 0..255` 连续；`sampling_mode=deterministic_four_consecutive_frames_heldout_unused`；新窗口均落在 V48 15 窗口间隙，与 V48 `frame_ids` 零重叠 per source 可机械校验（`BLOCK_WINDOWS` 比对）。
- **Per block `6` calls**：`L1_T (TRAIN) 1 + L1_TV (TRAIN+VAL) 1 + L2_{A,B,C,D} 4` (A=TRAIN×LaneC, B=TRAIN+VAL×LaneC, C=TRAIN×P0, D=TRAIN+VAL×P0)，同块同 `bob`。
- **总预算**：`15×6=90` (`L1 30 + L2 60` records). Summary 记 `l1=30 / l2=60 / total=90`.

## 3. 代表矩阵与译码合约

- **Lane C**：`lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302` ordinal-2 (committed v38 常量，复用).
- **P0-MET-1**：`p0_met_1M_det1 / p0_met_1p5M_det1 / p0_met_2M_det1` deterministic PEG-MET (spike §4).
- **H1**：`V31-H1-QC-16×1024` rank16.
- **译码合约**：90 calls 共享 `GF32 poly37, max_iter=90, damping 1.0, syndrome from true ut, exact = array_equal(x_hat, ut)`.

## 4. 门禁与效应（描述性，无阈值晋升）

每 `block×structure×prior` 一条 L2 record，共 60 条。V50 **不设 PASS/FAIL 绝对门禁**（因子实验为效应估计），仅报告主效应与 simple effects：

- 主效应 `E_structure=(C+D-A-B)/2`, `E_prior=(B+D-A-C)/2`（以 `exact_full` 求和差的半量）；交互 `E_interaction=(D-C)-(B-A)`。
- 四个 simple effects: `C-A` (TRAIN 下结构), `D-B` (TRAIN+VAL 下结构), `B-A` (LaneC 下先验), `D-C` (P0 下先验)；`C-A` 为 TRAIN 先验下的结构 simple effect，非主效应；McNemar 仅描述性。
- 同时报告 `exact_u1/exact_l2/exact_full` per factor/per source、四类计数、`L1/L2 iterations/runtime`、`APP entropy/||q-p||1` 分布；`G3' undetected==0` 单独表。

终态机（互斥，EVIDENCE_INVALID 优先）：

```
0. 任意完整性/守卫失败 -> V50_EVIDENCE_INVALID
1. else -> V50_FACTORIAL_COMPLETE (descriptive, no promotion)
   orthogonal flags: structure_gain = C>A, prior_gain = B>A (描述性)
```

## 5. O3 配对语义

- 同 `block ID` 的 held-out 样本 `(idx,alice,bob)` 每块确定性一次，`L1_T` 与 `L1_TV` 同 `bob` 不同 prior counts，同块 4 个 L2 同 `bob`、`H1 q_i` 派生 `P_i(U2)` 与各自 `H_L2` syndrome.
- 跨块/跨因子 outcome 差异为诊断量，永不作完整性失败。

## 6. 科学 preflight、守卫序

1. **拒绝类最先**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定 `f58955f3e794dbde11b4d813eec061182319846d`；四文件 SCOPED dirty（含 `v50` 模块、`v50` CLI、`v38_architecture_triage.py`、`v35_algorithm_development.py`）；输出根已存在即拒（J7）；任一拒绝零 calls 不建文件.
2. **科学 preflights（decoder-free, write-free）**：seed registry 校验（新区 15 与 FORBIDDEN 141 block ID 零重叠 per source 连续且与 V48 180 帧 `frame_ids` 零重叠）；P0 母矩阵 `E=2560`（MET）确定性重建与 `full_row_rank/capacity/4-cycle/chain-ring/dc_max` 比对（含 `G2` 精确链/环）；TRAIN 与 TRAIN+VAL counts 形态校验；held-out 未使用池可达；首块哨兵 `391001/391101/391201` 各 `L1_T/L1_TV→P_i(U2)` 通路 + `tag_import_ok` + `leakage_accounted` (1064/1094/1104, 与 `E` 无关) + `tag_scope_l2_only`.
3. **Preflight 失败** → 建增量根写 `v50_invalid_notice.json` + 空 records + `v50_summary.json` (terminal `V50_EVIDENCE_INVALID`, planned 90) 后零 decoder calls 停止.
4. **建根**仅在全部守卫与 preflights 通过后、首个 decoder call 前.

## 7. 记录、聚合、summary

每 L2 call record schema（含 `tag_scope=l2_only`）：

```
call_id, source, block_seed(block ID), prior_id(TRAIN/TRAIN_VAL), structure_id(lane_c/p0_met),
matrix_id, h1_matrix_id, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, sampling_mode,
max_iter 90, damping 1.0, errors_initial, errors_final, exact_l2, exact_u1, exact_full,
syndrome_ok_l2/l1, wrong_codeword, target_tag, candidate_tag, tag_ok, tag_scope,
reclassified, iterations_l1/l2, bp_posterior_entropy, mean_abs_diff_q_p, leak_total 1064/1094/1104, status, runtime_s
```

Summary 含：记账 `planned 90/l1 30/l2 60`、L1 诊断、`60` 条 L2 聚合（overall/per-source/per-prior/per-structure）、主效应 `E_structure/E_prior` 与交互 `E_interaction` 及四个 simple effects `C-A/D-B/B-A/D-C`、四类计数、G3'、门禁描述、`f_total`、claim boundary、provenance（含 `P0-MET-1 {dv2:512,dv3:512} E=2560` 确定性 ID 与 held-out 未使用溯源、prior 双溯源）。

## 8. 统计与断言边界

仅描述性；`n=15` blocks 配对；比例带 n 与 raw counts；区间 naive 未校正簇聚；无显著性晋升；终态仅 `V50_EVIDENCE_INVALID / V50_FACTORIAL_COMPLETE`。

断言边界 verbatim：结果仅支持 `n=1024, m2=184/190/192` 上 `P0-MET-1` 真 MET 单一等泄漏结构候选 `{dv2:512,dv3:512} E=2560`（全 `dv2` 则为 `PEG-dv2 E=2048`）与 `TRAIN vs TRAIN+VAL` 先验在 `15` 未使用 held-out 块上的 2×2 有界因子归因（decoder `90/1.0 poly37, early-stop`、泄漏 `1064/1094/1104` 等泄漏仅由 `m2` 决定与 `E` 无关、`dc_max=16, 4-cycles==0, 6/8-cycles 报告, 链≤4/纯环≤12==0 (G2 精确), GF32 满秩无零列, 确定性 lifting/label, 禁止 seed 搜索, 构造不触 V48 outcomes, L2-only tag `≈2^-64` 工程近似），`exact_full` oracle 不经 tag；均非真帧 FER 全集/阈值/SKR/资格/晋升证据；不启动 V51.

## 9. 证据写出

固定增量根（decoder 前建，fail-closed）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v50_l2_structure_factorial/run_01/
```

文件：`v50_records.json/.csv` (60 L2 行)、`v50_summary.json`、`v50_invalid_notice.json`（失败时）. CSV/JSON 行对等；禁写 NPZ.

## 10. 实现草图（后继轮次，当前未授权）

- `comparison_bench/src/comparison_bench/formal_ir/v50_l2_structure_factorial.py`：import `construct_lane_c_prototype` 常量与 `v35.compute_tag_64`，实现 `P0-MET-1` 真 MET 确定性 PEG-MET（`dv2:512,dv3:512 E=2560`，§2.2，含 `G2` 链/环）+ 双 prior loader (`TRAIN` / `TRAIN+VAL` 合并) + 2×2 runner (per block `2 L1 +4 L2`).
- `scripts/execute_v50_structure_factorial.py`：默认拒绝；`--execution-authorized --authorized-target-sha <sha>`；HEAD/origin 精确绑定 `f58955f3e794dbde11b4d813eec061182319846d`；四文件 SCOPED dirty；budget 硬帽 90.
- 仅 fake-runner 测试；不以 V48 outcomes 定结构.

## 11. 自由裁量 D1–D10

- D1 单候选等泄漏真 MET P0-MET-1 `{dv2:512,dv3:512} E=2560`，15 块 2×2=90 calls，与 Lane C 同 m2 同泄漏（`E` 不决定泄漏）.
- D2 seed registry 新区 15 `391001..` `391101..` `391201..` 与 FORBIDDEN 141 block ID 零重叠且与 V48 180 帧零重叠 per source 连续，每块写死 4 真实 `frame_ids` 与 `ordinal`.
- D3 代表矩阵 3 Lane C ordinal-2 + 3 P0-MET-1 det1 (`E=2560`).
- D4 先验 TRAIN vs TRAIN+VAL 正交.
- D5 门禁描述性主效应 `E_structure/E_prior` 与交互 `E_interaction` 及四个 simple effects，无晋升阈值；`C-A` 为 simple effect；G3' `undetected==0` 单独表.
- D6 哨兵每源首块双 prior 通路.
- D7 call 序 `source 1M/1p5M/2M, block asc, within-block A,B,C,D`.
- D8 SCOPED dirty 四文件.
- D9 preflight 失败 invalid 三件套零 calls.
- D10 文件集 60 行记录 + 聚合 + 效应 + provenance.
