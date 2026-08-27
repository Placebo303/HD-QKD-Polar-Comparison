# OpenSpec Design: formal-ir-v51-lane-c-label-nbace

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行。等待独立评审。**
**Cycle**: `V51P0`
**Predecessor**: V50 `V50_FACTORIAL_COMPLETE` (E_structure=-6, E_prior=0) HEAD `e3e14c9518bf44d03054e720a6230ea11d08f99a`
**Plan HEAD**: `c67a071f3b59924e81bd2bbbd452ab45f5a5c0e9` branch `formal-ir-mainline`
**Feasibility**: 三源 Lane C support 184/190/192×1024 decoder-free 可重建且满秩；确定性标签重标 decoder-free 可执行且保持支撑/秩/4/6/8 不变，仅改变退化谱；V50 已验证 held-out 池 1683 frames / 430k pairs 富余；45-call paired 预算冻结

## 1. 科学问题（单因子标签谱）

> 在**相同 support/置换/m2/泄漏/decoder**下，**确定性边标签重标**能否改善 Lane C 的代数退化环谱（优先消除 4-环，再改善 6/8-环），并在配对 held-out 块上体现 `exact_full` 增益？

- **因子**：`Lane C 原标签` vs `Lane C 新标签`（同支撑、同学置换、同 m2/泄漏/decoder，仅 `1..31` 标签不同）。
- **谱主目标**：真实可重算的词典序 `(degenerate_4 ↓, degenerate_6 ↓, degenerate_8 ↓, cand)` 越小越好；4-环优先于 6-环优先于 8-环（1M 2个deg4、2M 1个需优先消除，原从 deg6 开始错误已修正）。自定义 `check_extrinsic_score(C)=ACE(C)-100 若退化 else ACE(C)` 仅作次级报告，不得声称为文献标准 NB-ACE。
- **准入**：三源均不得按词典序恶化且至少一源严格改善，才进入 decoder 实验；否则 `V51_LABEL_NO_IMPROVEMENT` blocker。原“至少一源改善”已废止（会允许另两源恶化）。
- V51 不回答结构/MET、先验、综合阈值/SKR，仅回答支撑冻结下的标签谱与配对译码效应。

## 2. 冻结语义

### 2.1 固定不变项（不得调参）

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 |  |
| m2 per source | 184 (1M), 190 (1p5M), 192 (2M) | `SOURCE_CHECKS` |
| GF | GF32 `poly=37` | `GF2mField.create(32)` |
| 支撑 | Lane C ordinal-2 二值 support 与位置置换 | `construct_lane_c_prototype` + `position_permutations` |
| 泄漏 | `leak_total=5*m2+5*16+64 → 1064/1094/1104` | 恒 `m1=16`, L2-only tag |
| H1 | `V31-H1-QC-16×1024 rank16 80b` | V31 权威 |
| 译码 | `decode_row_layered_fftqspa` `max_iter=90,damping 1.0, early-stop` | V43/V50 同构 |
| Verification | `tag_scope=l2_only, compute_tag_64(empty_uint8,x2)` trunc64 | V35 |

- 原标签与新标签**同支撑**、同 `row_deg/col_deg` 分布、同 `4/6/8 支撑环数`；仅 `coeff ∈1..31` 不同；`rank==m2` 与 `dc_max≤16` 保持。

### 2.2 确定性标签优化器（decoder-free，单次）

- **输入**：各源二值 support `B=(H≠0)`，行度 `row_deg`，枚举 `c4/c6/c8 = enumerate_canonical_simple_cycles(B)`，`edge→cycle_ids` 索引（复用，不重枚举）。
- **ACE 定义**：`ACE(C)= Σ_{check∈C} (row_deg(check)-2)`（对 `dv=2` 正则，纯 check 外向度）。支撑冻结故 `ACE` 仅由拓扑决定，标签无关。
- **代数退化**：`is_deg(C,H)= classify_cycle_algebraic_degeneracy(C,H)`（`rank < |C|` → 退化）。`deg4= Σ is_deg(c4)` 等；主可验证量为 `degenerate_4/6/8`、`generalized_girth`、`nondeg_frac`。
- **自定义 check_extrinsic_score（非文献 NB-ACE）**：`check_extrinsic_score(C)= ACE(C) -100` 若 `is_deg(C)`，否则 `ACE(C)`。退化惩罚仅为自定义次级报告量，保证退化环得分低于非退化环；**不得声称为文献标准 NB-ACE**。备选互换报告 `min_deg_ace = min{ ACE(C) | is_deg(C)}` 同为次级量。
- **Generalized girth**：`g = min{ len(C) | is_deg(C)}`（4/6/8/None）；`nondeg_frac = (support-deg)/support`（可验证）。
- **主优化目标（词典序，越小越好，可重算）**：`key = (deg4, deg6, deg8, cand)`，其中 `cand` 为候选标签值 `1..31` 用于 tie-break；6-环前增加 4-环优先级，符合 1M/2M 存在 deg4 的事实。自定义 `check_extrinsic_score` 不参与主词典序，仅在报告中作为次级谱 `min_check_extrinsic6/8` 并列展示。
- **算法（高效增量）**：canonical 边序 `get_canonical_support_edges(B)`，维护全局 `deg4/6/8` 计数与 `is_deg` 数组；对每条边利用预计算 `edge_to_cycle_ids[edge]` 仅重算包含该边的环的 `is_deg` 变化，增量计算候选 `key=(deg4',deg6',deg8',cand)`，选最小 `key`（tie 最小 `cand`）；至多 `max_sweeps=2`，早停于零更新；全程确定性、零随机、`SeedSequence` 不参与；**不为每个候选复制完整 is_deg 数组**，仅局部重算 incident cycles。
- **约束**：`support_exact_equal`, `rank==m2`, `support_cycles_4/6/8 不变`；`deg4` 优先处理而非仅报告。
- **禁止**：根据译码 `exact`/`errors_final` 回搜标签或多 seed 择优；标签优化为一次 decoder-free 过程；禁止将自定义量称为文献 NB-ACE。

### 2.3 decoder-free 谱对比 freeze

每源一行原 vs 新：

| 字段 | 冻结 | 类型 |
|---|---|---|
| `support_exact_equal` | `True` | 主可验证 |
| `rank` | `==m2` 原/新一致 | 主可验证 |
| `support_cycles_4/6/8` | 不变 | 主可验证 |
| `degenerate_4/6/8` | 标签决定，需报告 `Δdeg4, Δdeg6, Δdeg8`，主词典序 | 主可验证 |
| `generalized_girth, nondeg_frac6/8` | 谱主量 | 主可验证 |
| `min_check_extrinsic6/8, min_deg_ace6/8` | 自定义次级报告（原 NB-ACE 命名已废止，不得作文献声称） | 次级报告 |

三源准入为词典序一致性条件（见 §4），非单源单指标。

### 2.4 块与 workload（15 新 held-out, paired, 45 calls, 条件）

库存：`1683 frames / 430k pairs` hold 区间中 **未使用且与 V50 391xxx 亦零重叠者**。

冻结新 15 块（每块写死 `4` 真实 `frame_ids` 与 `ordinal`，与 V50 `391001..` `391101..` `391201..` 窗口零重叠，且与 FORBIDDEN 156 = 141(V36..V50)+15(V50) 零重叠 per source 连续）：

| source | block ID | held_out_ordinal `[start,end]` | frame_ids[4] (global) | pairs |
|---|---|---|---|---|
| 1M (H=400, base1600) | 392001 | [7,10] | [1607,1608,1609,1610] | 1024 |
| 1M | 392002 | [35,38] | [1635,1636,1637,1638] | 1024 |
| 1M | 392003 | [63,66] | [1663,1664,1665,1666] | 1024 |
| 1M | 392004 | [91,94] | [1691,1692,1693,1694] | 1024 |
| 1M | 392005 | [119,122] | [1719,1720,1721,1722] | 1024 |
| 1p5M (H=554, base2213) | 392101 | [12,15] | [2225,2226,2227,2228] | 1024 |
| 1p5M | 392102 | [51,54] | [2264,2265,2266,2267] | 1024 |
| 1p5M | 392103 | [90,93] | [2303,2304,2305,2306] | 1024 |
| 1p5M | 392104 | [130,133] | [2343,2344,2345,2346] | 1024 |
| 1p5M | 392105 | [169,172] | [2382,2383,2384,2385] | 1024 |
| 2M (H=729, base2916) | 392201 | [18,21] | [2934,2935,2936,2937] | 1024 |
| 2M | 392202 | [70,73] | [2986,2987,2988,2989] | 1024 |
| 2M | 392203 | [122,125] | [3038,3039,3040,3041] | 1024 |
| 2M | 392204 | [174,177] | [3090,3091,3092,3093] | 1024 |
| 2M | 392205 | [225,228] | [3141,3142,3143,3144] | 1024 |

- 每窗口 `4 frames×256=1024 pairs`，`BLOCK_LENGTH=1024`；`sampling_mode=deterministic_four_consecutive_frames_heldout_unused_new`；新窗口与 V50 `391xxx` 间隙零重叠。
- **条件 Per block `3` calls**：`L1 shared (TRAIN) 1 + L2_old 1 + L2_new 1` 同块同 `bob` 同 `P_i(U2)`（仅 `H_L2` 标签不同）。
- **总预算（准入时）**：`15×3=45` (`L1 15 + L2 30` records)。

## 3. 代表矩阵与译码合约

- **Lane C 原**：`lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302` ordinal-2（`v38_architecture_triage`）。
- **Lane C 新**：`lane_c_1M_s383102_check_extrinsic / lane_c_1p5M_s383202_check_extrinsic / lane_c_2M_s383302_check_extrinsic` 同 support 确定性重标（`spike_label_nbace.py` 复现，命名已去 NB-ACE 化，旧 `nbace` 后缀兼容别名）。
- **H1**：`V31-H1-QC-16×1024` rank16。
- **译码合约**：45 calls 共享 `GF32 poly37, max_iter=90, damping 1.0, syndrome from true u, exact = array_equal(x_hat, u)`。

## 4. 门禁与配对效应（描述性，无晋升阈值）

谱准入（三源一致性，词典序）：`label_improved = (∀source: (deg4_new,deg6_new,deg8_new) ≤_lex (deg4_old,deg6_old,deg8_old)) ∧ (∃source: (deg4_new,deg6_new,deg8_new) <_lex (deg4_old,deg6_old,deg8_old))`。其中 `≤_lex` 为词典序不恶化，`<` 为严格改善（优先 deg4）。自定义 `check_extrinsic_score` 仅作次级报告，不参与准入主判。否则 `V51_LABEL_NO_IMPROVEMENT`，不建 45-call。原单源单指标准入已废止。

配对实验（准入后）：以 `exact_full = exact_u1 && exact_l2` 为主判，冻结配对统计：

- `paired_exact_full_new - old` per block、McNemar 表 `[[a=both exact, b=old exact new fail], [c=old fail new exact, d=both fail]]`、discordance `b+c`、exact 提升数 `c-b`。
- 同时报告 `errors_initial/final` 分布、`iterations/runtime` 分布；`G3' undetected==0` 单独表。
- 终态机（互斥，EVIDENCE_INVALID 优先）：
```
0. 任意完整性/守卫失败 -> V51_EVIDENCE_INVALID
1. else if !label_improved (存在恶化或无改善) -> V51_LABEL_NO_IMPROVEMENT (blocker, no decoder)
2. else -> V51_PAIRED_COMPLETE (descriptive, no promotion)
   orthogonal flags: label_gain = new>old
```

## 5. O3 配对语义

- 同 `block ID` 的 held-out 样本 `(idx,alice,bob)` 每块确定性一次，`L1` 单次生成 `q_i` 与 `P_i(U2)`，双 L2 同 `bob`/`q_i`/`P_i(U2)` 与各自 `H_L2` syndrome。
- 跨块 outcome 差异为诊断量，永不作完整性失败。

## 6. 科学 preflight、守卫序

1. **拒绝类最先**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定未来实现 SHA；四文件 SCOPED dirty（含 `v51` 模块、`v51` CLI、`v38_architecture_triage.py`、`v35_algorithm_development.py`）；输出根已存在即拒（J7）；任一拒绝零 calls 不建文件。
2. **科学 preflights（decoder-free, write-free）**：lane C 三 support 确定性重建与 committed `rank/support_cycles_4/6/8` 比对；标签重标 decoder-free 重建与 `support_exact_equal/rank/cycles 不变` 校验；谱准入 `label_improved` 三源词典序一致性布尔；TRAIN counts 形态；新 15 held-out 未使用池可达且与 FORBIDDEN 156 及 V48/V50 `frame_ids` 零重叠；首块哨兵 `392001/392101/392201` 各 `L1→P_i(U2)` 通路 + `tag_import_ok` + `leakage_accounted` + `tag_scope_l2_only`。
3. **Preflight 失败** → 建增量根写 `v51_invalid_notice.json` + 空 records + `v51_summary.json` (terminal `V51_EVIDENCE_INVALID` 或 `V51_LABEL_NO_IMPROVEMENT` 按谱准入) 后零 decoder calls 停止。
4. **建根**仅在全部守卫与 preflights 通过后、首个 decoder call 前。

## 7. 记录、聚合、summary

每 L2 call record schema（含 `tag_scope=l2_only`）：
```
call_id, source, block_seed(block ID), label_id(old/new), matrix_id, h1_matrix_id, frame_ids[4], held_out_ordinal_start/end, pairs_count 1024, sampling_mode,
max_iter 90, damping 1.0, errors_initial, errors_final, exact_l2, exact_u1, exact_full,
syndrome_ok_l2/l1, wrong_codeword, target_tag, candidate_tag, tag_ok, tag_scope,
reclassified, iterations_l1/l2, bp_posterior_entropy, mean_abs_diff_q_p, leak_total 1064/1094/1104, status, runtime_s
```
Summary 含：谱对比表（原 vs 新 per source：rank/support/cycles/deg4/6/8/girth/nondeg_frac + 自定义 check_extrinsic 次级）、记账 `planned 45/l1 15/l2 30`、`30` 条 L2 聚合（overall/per-source）、配对表 `old vs new exact_full`、McNemar `b/c/discordance`、残留误码与 runtime 分布、四类计数、`f_total`、claim boundary、provenance（含自定义 check_extrinsic 定义与一次确定性重标 ID 与新 held-out 溯源，明确非文献 NB-ACE）。

## 8. 统计与断言边界

仅描述性；`n=15` blocks 配对；比例带 n 与 raw counts；区间 naive 未校正簇聚；无显著性晋升；终态仅 `V51_EVIDENCE_INVALID / V51_LABEL_NO_IMPROVEMENT / V51_PAIRED_COMPLETE`。

断言边界 verbatim：结果仅支持 `n=1024, m2=184/190/192` 上 Lane C 同支撑同 m2 同泄漏同 decoder `90/1.0` 的单次确定性标签重标（主目标词典序 `deg4 ↓, deg6 ↓, deg8 ↓` 优先 4-环，自定义 check_extrinsic_score 仅次级报告非文献 NB-ACE，禁止译码回搜）在 15 新未使用 held-out 块上的配对有界归因（`exact_full` oracle 不经 tag；L2-only tag `≈2^-64` 工程近似），`support/秩/4/6/8 支撑数不变`；`exact_full` paired 为主判，无 TRAIN+VAL 臂；均非真帧 FER 全集/阈值/SKR/资格/晋升证据。

## 9. 证据写出

固定增量根（decoder 前建，fail-closed）：
```
comparison_bench/outputs_comparison/formal_ir_methods/v51_lane_c_label_nbace/run_01/
```
文件：`v51_records.json/.csv` (30 L2 行)、`v51_summary.json`、`v51_invalid_notice.json`（失败时）、`v51_label_spectrum.json` (decoder-free 谱原 vs 新，含 deg4/6/8 主量与自定义 check_extrinsic 次级量)。CSV/JSON 行对等；禁写 NPZ。

## 10. 实现草图（后继轮次，当前未授权）

- `comparison_bench/src/comparison_bench/formal_ir/v51_lane_c_label_nbace.py`：import `construct_lane_c_prototype` 常量与 `v35.compute_tag_64`，实现 §2.2 确定性标签重标（`enumerate_canonical_simple_cycles` + `classify_cycle_algebraic_degeneracy` + ACE + 贪心 2-sweep 增量 `edge_to_cycle_ids` 局部重算）+ 15 新 held-out paired runner (per block `1 L1+2 L2`)。
- `scripts/execute_v51_label_nbace.py`：默认拒绝；`--execution-authorized --authorized-target-sha <sha>`；HEAD/origin 精确绑定未来实现 SHA；四文件 SCOPED dirty；谱准入三源词典序一致性布尔门；budget 硬帽 45；任一 gate 失败非零退出。
- 仅 fake-runner 测试；不以译码结果定标签；自定义量不得称为 NB-ACE。

## 11. 自由裁量 D1–D10

- D1 单次确定性标签重标（同支撑 184/190/192，主词典序 deg4/deg6/deg8）。
- D2 谱对比字段 freeze（support_equal/rank/4/6/8 不变/deg4/6/8/girth/nondeg_frac 为主，自定义 score 为次级）。
- D3 准入三源均不恶化且至少一源词典序严格改善，否则 blocker 不实验（原单源单指标已废止）。
- D4 15 新 held-out 块 `392001..` `392101..` `392201..` 连续，与 FORBIDDEN 156 及 V50 391xxx 与 V48 零重叠 per source。
- D5 45-call paired workload `L1 15 + L2 30`，主判 paired `exact_full` + discordance/residual/runtime。
- D6 无 TRAIN+VAL 臂。
- D7 call 序 `source 1M/1p5M/2M, block asc, within-block old→new`。
- D8 SCOPED dirty 四文件。
- D9 preflight 失败 invalid 三件套零 calls。
- D10 文件集 `30` 行记录 + `label_spectrum.json`（deg 主 + 自定义次级）+ 聚合 + 配对。
