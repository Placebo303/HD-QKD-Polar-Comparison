# OpenSpec Design: formal-ir-v47-h1-redundancy-compression

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V48。等待独立评审。**
**Cycle**: `V47P0`
**Predecessor**: V46 `formal-ir-v46-verification-semantics` (result SHA `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`, branch `formal-ir-mainline`)
**Investigation anchor**: `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`
**HEAD**: `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`（实现冻结时 `git rev-parse` 精确重绑）
**Feasibility**: V47 可行性核查已全部成立（H1 前缀满行秩、Lane C 三矩阵冻结、V46 路径复用、54-call 预算、87 隔离后新区）

## 1. 科学问题（单一，H1 冗余压缩）

> 在固定 Lane C 三矩阵 ordinal-2 + L2 `90/1.0` + V46 L1APP soft-transfer + L2-only verification + V46 四类/G3' 冻结下，**能否用更小的 H1 冗余 `m1 ∈ {8,12,16}` 通过同等 `exact_full` 门禁，从而以更低总泄漏实现同等完整 reconciliation？**

- 前代 V46 已用 `H1-16 (80 bits)` 在 9 块 fresh-block 上验证 Treatment `7/9` 增益的 verification acceptance 语义；V47 **不改任何 V46 机制**，只做 H1 行数压缩。
- 若 `H1-8` 或 `H1-12` 通过门禁，则 V31 H1 的 80-bit 冗余可压缩（`leak_total` 降低 20/40 bits）；若均不通过则保留 `H1-16` 基线。
- V47 不回答“是否可压缩 L2”或“是否可换 decoder/图”，仅回答 H1 冗余压缩。

## 2. 冻结语义（全部沿用 V46，仅 H1 行数可变）

### 2.1 固定不变项

| 项 | 冻结值 | 来源 |
|---|---|---|
| Lane C L2 矩阵 | `lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302` ordinal-2 | V38/V46 权威 |
| L2 译码 | `max_iter=90, damping_alpha=1.0, GF32 poly37, row_layered FFT-QSPA, 冻结 early-stop` | V43/V46 |
| L1APP 公式 | `p_i(u1)=P(U1|B_i)`, `s1=H1^{m1}·u1^Alice`, `BP_i=decode(H1^{m1},p_i,s1).bp_posterior_beliefs`, `q_i=softmax(BP_i)`, `P_i(U2)=Σ q_i P(U2|B,u1)` | V45/V46 O1 |
| Verification | `tag_scope=l2_only`, `compute_tag_64(empty_uint8, x2)`, `b1+b2→SHA256→hex[:16]` trunc64, `tag_ok=(candidate==target)`, `empty=np.empty(0,dtype=np.uint8)` | V35/V46 |
| 四类/G3' | `exact / detected_verification_failure / decoder_non_syndrome_failure / undetected_accepted_wrong`, `G3': undetected==0` (`tag_ok&&!exact` 计数 0) | V46 |
| APP 语义 | `bp_posterior_beliefs` 为 APP approximation 非精确 APP | V45/V46 |

- **Control 缺席**：不再运行 V43 `P(U2|B)` 零泄漏臂；三臂均为 Treatment 形态（L1APP + L2-only verification），对照是 `H1-16`。
- `L1 wrong`（`syndrome_ok_l1 && !exact_u1` 或 `!syndrome_ok_l1`）单独报告，不入 G3'，但作诊断上下文。

### 2.2 单变量 H1 前缀嵌套

- **V31 H1 物料**：`V31-H1-QC-16×1024`（`m1=16, n=1024, GF32 poly37, QC-cyclic-projective, rank16, max_support_occupancy≤31, projective_safe, full_row_rank`）来自 `nonbinary_v31.build_matrix_packet(m1=16, ...)` 经 `build_layer(16,1024)` 确定性构造。
- **前缀定义**：
  ```python
  H1_16 = V31_H1  # 16×1024, 80 bits
  H1_12 = H1_16[:12, :]  # 12×1024, 60 bits, 前 12 行
  H1_8  = H1_16[:8, :]   #  8×1024, 40 bits, 前 8 行
  # 满足 H1_8 ⊂ H1_12 ⊂ H1_16 行前缀嵌套
  ```
- **满行秩已验证**：可行性核查已验证 `rank(H1_8)=8`, `rank(H1_12)=12`, `rank(H1_16)=16`（GF32, poly37）；三者均 `capacity_ok / projective_safe` 继承（前缀不增支撑占用）。
- **Syndrome**：`s1^{m1} = H1^{m1} · u1^Alice`（GF32），`m1=8→40 bits, 12→60 bits, 16→80 bits`，计入 `leak_total`。
- **QSPA 调用**：`decode_row_layered_fftqspa(H1^{m1}, p_i, s1^{m1})`，`m1` 越小校验越少，`q_i` 退化向 `p_i`。

### 2.3 总泄漏（含 L2+tag）

`leak_total(m1) = 5·m2 + 5·m1 + 64`，`m2 ∈ {184,190,192}`（`L2 syndrome 920/950/960`，按 source 1M/1p5M/2M），`m1∈{8,12,16}`：

| arm | m1 | 1M (m2=184) | 1p5M (m2=190) | 2M (m2=192) |
|---|---|---|---|---|
| H1-8  | 8  | 1024 (920+40+64) | 1054 (950+40+64) | 1064 (960+40+64) |
| H1-12 | 12 | 1044 (920+60+64) | 1074 (950+60+64) | 1084 (960+60+64) |
| H1-16 | 16 | 1064 (920+80+64) | 1094 (950+80+64) | 1104 (960+80+64) |

`f_total = leak_total / [N·(H1+H2)]`，`N=1024`，`H_i` 每符号 bits/symbol（V25）；三臂非等泄漏比较，结论表述为“更小 `m1` 在更低泄漏下是否通过同等门禁”。

### 2.4 时序与四类（V46 同构）

```
decode(H1^{m1}, p_i, s1^{m1}) → exact_u1 / syndrome_ok_l1 / wrong_l1 / iterations_l1 / BP entropy / ||q-p||1
        ↓  (per-arm, q_i=softmax BP)
P_i(U2)=Σ q_i P(U2|B,u1) → syndrome_of_gf32(H_L2, u2_alice) → decode_row_layered_fftqspa(H_L2, P_i(U2), syndrome) → exact_l2 / syndrome_ok_l2 / wrong_l2 / iterations_l2 / exact_full (=exact_u1&&exact_l2)
        ↓  (pre-tag, 沿用 V46)
verification L2-only: target_tag=compute_tag_64(empty, x2_true); candidate_tag=compute_tag_64(empty, x_hat); tag_ok=(candidate==target)
        ↓
reclassified:
  exact                              → exact (tag_ok&&exact)
  syndrome_ok && !exact && !tag_ok   → detected_verification_failure
  !syndrome_ok && !exact             → decoder_non_syndrome_failure
  tag_ok && !exact                   → undetected_accepted_wrong (≈2^-64 工程近似)
```

`exact_full` 仍 oracle `exact_u1 && exact_l2`，不经 tag；`exact_u1` 来自 `argmax q_i` hard decision。

## 3. 冻结样本集（9 新块，FORBIDDEN 78 + V46 9 =87 隔离）

延续 `390x` 源前缀递增，V46 占用 `390122-124/222-224/322-324`（x22-x24/源）后，本变更取其后三枚/源（x25-x27/源）：

| source | 新 block seeds (x25-x27) |
|---|---|
| 1M | 390125, 390126, 390127 |
| 1p5M | 390225, 390226, 390227 |
| 2M | 390325, 390326, 390327 |

FORBIDDEN 并集 = V36_A3(15: 360101-105/360201-205/360301-305) ∪ V39(15: 390101-105/390201-205/390301-305) ∪ V40 probe(3: 390106/390206/390306) ∪ V41 confirm(9: 390107-109/390207-209/390307-309) ∪ V42 diagnostic(9: 390110-112/390210-212/390310-312) ∪ V43 diagnostic(9: 390113-115/390213-215/390313-315) ∪ V44 diagnostic(9: 390116-118/390216-218/390316-318) ∪ V45 diagnostic(9: 390119-121/390219-221/390319-321) = **78 seeds**；另 V46 9 枚 `390122-124/222-224/322-324` 已占用，总隔离 **87 seeds**。九枚新区为每源 x25-x27 连续递增，无内部重复，与全部 87 零重叠（P3/J2 机械复验）。采样语义：`sample_empirical_block(V25 TRAIN counts, block_seed, BLOCK_LENGTH=1024)` + `factorize_f03`；每块样本计算一次并被三臂共享。

## 4. 冻结 workload（54 decoder invocations，27 L2 records）

**预算**：每块每臂 `L1 BP 1 + Treatment L2 1 =2` invocations，共 `9×3×2=54` decoder invocations；L2 performance records `27` 条（每臂 9），L1 invocations `27` 次。Summary 分别记录 `l1=27 / h1_8_l2=9 / h1_12_l2=9 / h1_16_l2=9 / total=54`（planned/completed/started actuals）。

L2 records 顺序冻结（源 1M/1p5M/2M，块升序，臂按 `h1_8 → h1_12 → h1_16`）：

| call | source | block_seed | arm | H1 | matrix_id (lane_c) |
|---|---|---|---|---|---|
| C01 | 1M | 390125 | h1_8  | H1_8  (8×1024)  | lane_c_1M_s383102 |
| C02 | 1M | 390125 | h1_12 | H1_12 (12×1024) | lane_c_1M_s383102 |
| C03 | 1M | 390125 | h1_16 | H1_16 (16×1024) | lane_c_1M_s383102 |
| C04 | 1M | 390126 | h1_8  | H1_8  | lane_c_1M_s383102 |
| C05 | 1M | 390126 | h1_12 | H1_12 | lane_c_1M_s383102 |
| C06 | 1M | 390126 | h1_16 | H1_16 | lane_c_1M_s383102 |
| C07 | 1M | 390127 | h1_8  | H1_8  | lane_c_1M_s383102 |
| C08 | 1M | 390127 | h1_12 | H1_12 | lane_c_1M_s383102 |
| C09 | 1M | 390127 | h1_16 | H1_16 | lane_c_1M_s383102 |
| C10 | 1p5M | 390225 | h1_8  | H1_8  | lane_c_1p5M_s383202 |
| C11 | 1p5M | 390225 | h1_12 | H1_12 | lane_c_1p5M_s383202 |
| C12 | 1p5M | 390225 | h1_16 | H1_16 | lane_c_1p5M_s383202 |
| C13 | 1p5M | 390226 | h1_8  | H1_8  | lane_c_1p5M_s383202 |
| C14 | 1p5M | 390226 | h1_12 | H1_12 | lane_c_1p5M_s383202 |
| C15 | 1p5M | 390226 | h1_16 | H1_16 | lane_c_1p5M_s383202 |
| C16 | 1p5M | 390227 | h1_8  | H1_8  | lane_c_1p5M_s383202 |
| C17 | 1p5M | 390227 | h1_12 | H1_12 | lane_c_1p5M_s383202 |
| C18 | 1p5M | 390227 | h1_16 | H1_16 | lane_c_1p5M_s383202 |
| C19 | 2M | 390325 | h1_8  | H1_8  | lane_c_2M_s383302 |
| C20 | 2M | 390325 | h1_12 | H1_12 | lane_c_2M_s383302 |
| C21 | 2M | 390325 | h1_16 | H1_16 | lane_c_2M_s383302 |
| C22 | 2M | 390326 | h1_8  | H1_8  | lane_c_2M_s383302 |
| C23 | 2M | 390326 | h1_12 | H1_12 | lane_c_2M_s383302 |
| C24 | 2M | 390326 | h1_16 | H1_16 | lane_c_2M_s383302 |
| C25 | 2M | 390327 | h1_8  | H1_8  | lane_c_2M_s383302 |
| C26 | 2M | 390327 | h1_12 | H1_12 | lane_c_2M_s383302 |
| C27 | 2M | 390327 | h1_16 | H1_16 | lane_c_2M_s383302 |

另有 27 次 L1 invocations（每块每臂一次，记为 L1-01..L1-27，与上表 C01-C27 一一对应按 `block_seed × arm`），总计 54。27 行去重得 **3 枚唯一 L2 矩阵** + **1 枚 V31 H1 母矩阵**（前缀切片）；成员/顺序漂移即 J12。

## 5. 代表矩阵与译码合约（冻结）

- **Lane C ordinal-2 / source**：`lane_c_1M_s383102`、`lane_c_1p5M_s383202`、`lane_c_2M_s383302`（以 committed v38 模块常量表校验）。
- **H1 母矩阵**：`V31-H1-QC-16×1024`（`m1=16, n=1024, family=QC-cyclic-projective, GF32 poly37, rank16, capacity_ok, projective_safe, full_row_rank`），前缀 `H1_8/H1_12` 继承秩与 projective。
- **译码合约**：54 invocations 共享 `GF32 poly37, max_iter=90, damping_alpha=1.0, syndrome from true u_alice / s1^{m1}=H1^{m1}·u1^Alice, success primary = exact_full (=exact_u1&&exact_l2) 门禁，同时报告 exact_u1/exact_l2/exact_full, decoder = 通用 decode_row_layered_fftqspa(H,prior,syndrome).bp_posterior_beliefs (BP posterior / APP approximation, 冻结 early-stop)`。
- **O1 机制**：每臂 `P_i^{m1}(U2)=Σ q_i^{m1} P(U2|B_i,u1)`，`q_i^{m1}=softmax BP_i(H1^{m1},p_i,s1^{m1})`，其中 `p_i(u1)=P(U1|B_i)` 来自 V25 C，`f_total=leak_total/[N(H1+H2)] N=1024`，泄漏见 §2.3。
- **D15 组合路径**：`sample_empirical_block` 每块一次 → `factorize_f03` → per-arm `L1 p_i→s1^{m1}→BP_i^{m1}→q_i^{m1}` → `P_i(U2)` → `syndrome_of_gf32(H_L2,u2_alice)` → `decode_row_layered_fftqspa` + `compute_tag_64(empty,x2)` L2-only verification，`decode_fn` 可注入，默认 accepted 解码器。
- **V35 复用点**：`target_tag/candidate_tag/tag_ok` 在每条 L2 记录解码后立即计算（`empty+x2` L2-only）；`tag_ok==false` 即 `detected`，`tag_ok==true && !exact` 即 `undetected`。

## 6. 每臂门禁（exact_full，G3' undetected==0）

对 `X ∈ {h1_8, h1_12, h1_16}`，各以其 9 条 L2 records 判定：

- G1：X 的 overall `exact_full ≥ 7/9`
- G2：X 的每源 `exact_full ≥ 2/3`（每源 3 块中至少 2 块 `exact_full`）
- G3'：X 的 **`undetected_accepted_wrong ==0`**（`tag_ok==true && !exact_l2` 或 `!exact_full` 的 undetected 计数为 0；以 `!exact_l2` 计，与 V46 一致）

X 通过当且仅当三条全满足；门禁仅判定臂保留，不支持臂间优劣排序。`detected_verification_failure` 不触发 G3'（被 gate 捕获即不违规）；不要求 decoder 永不产生 `syndrome_ok && !exact`。`L1 wrong`（`syndrome_ok_l1 && !exact_u1` 或 `!syndrome_ok_l1`）单独报告与诊断上下文，不入 G1/G2/G3'。

同时每臂报告：`exact_u1 / exact_l2 / exact_full` 总量与每源、`detected / decoder_non_syndrome / undetected`、`L1/L2 iterations/runtime 均值/中位数`、`APP entropy / ||q-p||1 (=mean_abs_diff)` 分布。

## 7. 终态机（总量互斥；EVIDENCE_INVALID 优先；first-match 最小 m1）

五终态（总量互斥，覆盖三臂 pass 平面；first-match 按 `8→12→16` 升序最小通过者）：

```text
0. 任意完整性/执行失败 -> V47_EVIDENCE_INVALID
1. pass_h1_8 == true  -> V47_H1_8_RETAINED
     (H1-8 保留：最小冗余 40 bits 通过门禁，泄漏最低)
2. else if pass_h1_12 == true -> V47_H1_12_RETAINED
     (H1-12 保留：8 失败但 12 通过，60 bits)
3. else if pass_h1_16 == true -> V47_H1_16_ONLY
     (仅 H1-16 保留：仅基线 80 bits 通过，压缩失败)
4. else -> V47_NO_H1_SIZE_RETAINED
     (无 H1 尺寸保留：三臂均未通过，转结构/联合)
```

规则 1-4 穷尽互斥覆盖 `(pass_8, pass_12, pass_16)` 平面，规则 0 优先；真值表测试枚举 integrity ok/failed × 八格并断言互斥与 first-match。Summary 终态下区分四类计数与 G3' 判定（per-arm/per-source/per-block），`undetected` 计数即 G3' 依据；`L1 wrong` 单独表。

Wrong 处理（逐臂局部）：`detected_verification_failure` 并置 `stopped_for_analysis[arm]=true` 仅通过本臂 G3' 体现（`undetected==0` 仍可通过）；无全局 wrong，无跨臂否决；任意臂 `undetected` 立旗 `arm_undetected_anomaly[arm]=true`。

orthogonal 标志：`needs_1p5m_structure_branch` 当且仅当 `h1_16 exact_full on 1p5M < 2/3` 时立旗（以基线臂 1p5M 表现计），独立于终态。

## 8. O3 配对语义

- 同 `block_seed` 的确定性样本 `(idx, alice, bob)` 每块算一次并被三臂共享；每块三臂 L1 invocation 共享同一 `p_i` 但 `s1^{m1}/q_i^{m1}` 随 `m1` 不同。
- 同 H_L2（该源 lane_c ordinal-2）、同设置 90/1.0、同域/多项式、同 L2 syndrome；三臂唯一差异为 `H1^{m1}` 行数/`s1^{m1}`/`q_i^{m1}` → `P_i^{m1}(U2)` + 对应泄漏；三臂均做 `compute_tag_64(empty,x2)` L2-only verification（同样本 `x2_hat` 路径，不用 `x1_true`）。
- 跨臂残差差异（`errors_final/iterations/exact_full/syndrome_ok/tag_ok/wrong`）是诊断量本身，永不作完整性失败。
- `exact_full` 与 `exact_l2/exact_u1` 同时记录；`exact_u1` 来自 L1 hard decision（`argmax q_i`），`exact_u1==false` 不阻止 L2 软转移；`exact_full` 不经 tag。

完整性检查跨臂适用性：J2/J3/J4/J5/J6/J8-J12 与 V46 同构，仅将 78 更新为 87（78+9）、`structure_failure` 保持为 `decoder_non_syndrome_failure`、G3 保持 `undetected==0`、预算 27→54、三臂 first-match 终态。

## 9. 科学 preflight、守卫序、证据分层

守卫序冻结（沿用 V46 §9-§11，更新 54-call 与 H1 前缀）：

1. **拒绝类守卫最先、建目录前**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `git rev-parse origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定 `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`；四文件 SCOPED tracked-dirty 检查（v47 模块、v47 CLI、v38_architecture_triage.py、v35_algorithm_development.py（含 tag 源））；输出根已存在即拒（J7）；任一拒绝非零退出、零 calls、不创建任何文件。
2. **科学 preflights（decoder-free、write-free）**：seed-registry 校验（J2，87 并集：78 + V46 9，新区 9 零重叠）；H1 母矩阵 `16×1024` 与三前缀 `8/12/16` 确定性重建并与 committed 结构权威严格比对含 `full_row_rank/capacity/projective`（J3；前缀秩 8/12/16 分别校验）；三源 counts 形态/加载经 accepted loader（J4）；首块/源三臂绑定哨兵 `390125/390225/390325` — 仅校验数据通路：每臂 `control` 形态六项 + `treatment fake` 七项复用 + 新增 `h1_prefix_ok`（`H1_8⊂H1_12⊂H1_16` 行前缀、秩、切片一致性）与 `v35_tag_import_ok`（`compute_tag_64` 可 import 且 `empty+x2` 可用、`hex[:16]`、x1 不变/x2 敏感）与 `leakage_accounted`（`1024/1054/1064 vs 1044/1074/1084 vs 1064/1094/1104` 含 64 tag 工程 verification）+ `tag_scope_l2_only` 校验；真实 `q≠p`、L1 iterations/syndrome/exact/wrong、APP entropy/confidence 不在此 gate，仅执行期测量。
3. **Preflight 失败** → 建增量根，写 `v47_invalid_notice.json` + 空 records + `v47_summary.json`（terminal `V47_EVIDENCE_INVALID`，planned 54 / l1 27 / h1_8 0 / h1_12 0 / h1_16 0 / total 0，无聚合）后零 decoder calls 停止。
4. **建根**：仅在全部拒绝类守卫与科学 preflights 通过后、首个 decoder call 前。

哨兵同 V46 §11 形态，仅更新 registry 与 H1 前缀/tag import（L2-only 空前缀）；`fake_path_verified` 保留。

## 10. 记录、聚合、summary

记录 schema（每 L2 call，在 V46 §10 基础上增 `arm/h1_rows/arm_leak_total` 与三臂聚合，`tag_scope=l2_only`）：

```
call_id("C01".."C27"), arm("h1_8"|"h1_12"|"h1_16"), h1_rows(8|12|16), source,
construction_seed, construction_seed_ordinal, block_seed, matrix_id, h1_matrix_id ("V31-H1-QC-16×1024 prefix m1=8/12/16"),
max_iter, damping_alpha, errors_initial, errors_final, exact_l2, exact_u1, exact_full,
syndrome_ok_l2, syndrome_ok_l1, wrong_codeword_l2, wrong_codeword_l1,
target_tag, candidate_tag, tag_ok, tag_scope("l2_only"),
reclassified ∈ {exact, detected_verification_failure, decoder_non_syndrome_failure, undetected_accepted_wrong},
iterations_l1, iterations_l2, bp_posterior_entropy, mean_abs_diff_q_p,
leak_total_this_arm (1024/1054/1064 或 1044/1074/1084 或 1064/1094/1104),
status, runtime_s
```

其中 `reclassified` 由 `exact/syndrome_ok/tag_ok` 派生，四类互斥穷尽。L1 27 次 invocations 记账单列（per-arm L1 诊断随行）。`tag_scope` 恒为 `l2_only`；`target_tag/candidate_tag` 均为 `compute_tag_64(empty,x2)`。

Summary 含：记账（planned 54 / l1 27 / h1_8 9 / h1_12 9 / h1_16 9 completed/started actuals，total 54，structural/preflight decoder_calls=0）；`l1_diagnostics_by_arm_by_source`（执行期测量永不 gate：`mean_abs_diff(q^{m1},p)`、`APP entropy/confidence`、`H1_rank/capacity_ok/projective_ok` per `m1`、`iterations_l1` 分布、`exact_u1/syndrome_ok_l1/wrong_l1` per arm）；per-arm 聚合（`exact_l2/exact_u1/exact_full` 总量与每源、`detected / decoder_non_syndrome / undetected` 各计数、`wrong_codeword` 明细、G3' `undetected==0` 判定、迭代/运行时均值、entropy/||q-p||1 分布）；per-source-per-arm 聚合；per-block 三臂配对结果 + errors_final delta + exact_full/tag_ok 对照 + `leak_total` 对照；三臂门禁明细（G1/G2/G3' 数值与 pass/fail，基于 `undetected==0` 新 G3'）在 terminal 判定之后；路由轨迹；`terminal_state`+`terminal_reason`（V47 新命名 first-match）；`stopped_for_analysis` 每臂；`arm_undetected_anomaly` 每臂；`needs_1p5m_structure_branch` orthogonal 标志；master stop rule 原文；claim boundary（含工程近似、L2-only 与三臂非等泄漏 `1024/1054/1064 vs 1044/1074/1084 vs 1064/1094/1104` 说明）；statistics note；provenance（authorized target SHA、HEAD/origin 绑定、前代 plan/execution SHAs、结构权威身份、H1 物料身份 `V31-H1-QC-16×1024 prefix 8/12/16 rank 8/12/16`、V25 counts 溯源、O1 机制 id `l1_app_soft_transfer_H1_prefix_{8,12,16}_syndrome_derived_with_v35_tag_l2_only`、tag 源 `v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only`、泄漏三臂 `1024/1054/1064 vs 1044/1074/1084 vs 1064/1094/1104` + L2 syndrome 920/950/960 + f_total，含工程 verification 声名 `SHA-trunc64 random-hash-model approximate 2^-64, not information-theoretic; strict bound requires universal2+seed; L2-only`）。

## 11. 统计与断言边界

仅描述性；样本 tiny 且成簇（54 invocations = 9 唯一块 ×3 臂 × (1 L1+1 L2)；27 L2 records 三臂配对）；比例报告带 n 与 raw counts；任何打印区间 naive 且未校正簇聚；无显著性检验；主要门禁仅 `exact_full` 且 `tag_ok` gate 后仍计 `exact`，`exact_u1/exact_l2` 另行报告且不经 tag（L2-only）；`detected` 不计 exact；三臂非等泄漏比较仅为 H1 冗余压缩价值评估，不宣称容量/阈值/SKR。

断言边界 verbatim：结果仅支持 V25 TRAIN 经验 counts 开发块上的有界 H1 冗余压缩归因 — 三臂 `H1-8/H1-12/H1-16` 按 O1 以 V31 H1 前缀 `8/12/16` + 通用 FFT-QSPA `q_i^{m1}=softmax BP posterior / APP approximation` 做真实 syndrome-derived 软转移、L2 在固定 Lane C 三矩阵 ordinal-2 上 90/1.0 单点、`leak_total H1-8 1024/1054/1064 vs H1-12 1044/1074/1084 vs H1-16 1064/1094/1104 (L2 syndrome 920/950/960 + m1·5 +64 tag, f_total, 工程 verification L2-only)`，复用 V35 `compute_tag_64(empty,x2)[:16]`，不改结构/阈值，`undetected≈2^-64` 仅随机哈希模型工程近似（固定公开 SHA-256 截断；严格界需 universal2+seed），三臂非等泄漏比较为更小 `m1` 价值评估；均非真帧 FER 证据，不推阈值/SKR/正式执行/资格/晋升；终态仅方向性 first-match 最小 `m1`，不启动 V48。

## 12. 证据写出与增量输出根

固定增量根（在解码前建，fail-closed 若已存在；科学 preflight 失败亦建仅放 invalid 三件套）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v47_h1_redundancy_compression/run_01/
```

文件（最小固定集）：

- `v47_records.json` / `.csv`（每 L2 call 一行，共 27 行，含 `arm/h1_rows/target_tag/candidate_tag/tag_ok/reclassified/tag_scope/leak_total_this_arm`；L1 诊断随行或单独数组）
- `v47_summary.json`（§10 内容，含四类计数、分层记账 54、三臂门禁明细、first-match 终态、工程 verification L2-only 声名、provenance 含 H1 前缀与 tag 源、三臂泄漏）
- `v47_invalid_notice.json`（仅完整性失败时）

CSV/JSON 行对等；禁写任何 `.npz`；禁以非 accepted loader 读 NPZ；既有 `results/`、V38-V47 输出保持 byte-identical。

## 13. 实现草图（后继轮次，当前未授权）

- 新模块 `comparison_bench/src/comparison_bench/formal_ir/v47_h1_redundancy_compression.py`：仅 import accepted `nonbinary_v31.build_layer/build_matrix_packet` 前缀切片 / `v38` 重建 helper / `v35.compute_tag_64`；按 V46 D15 组合三臂路径（含每臂 L1 APP 链 `p_i→s1^{m1}→BP_i^{m1}→q_i^{m1}→P_i(U2)`，BP posterior / APP approximation，early-stop 冻结）并在每 L2 解码后调用 `compute_tag_64(empty,x2)` 生成/比对 tag（L2-only）；不 import v39/v40/v41/v42/v43/v44/v45/v46；registry 以拷贝数据常量进入（含 87+9）；不重新实现 canonical 编码，不引入 `compute_tag_64_symbols` 等价宣称。
- 新 CLI `scripts/execute_v47_h1_redundancy_compression.py`：默认拒绝；必带 `--execution-authorized --authorized-target-sha <sha>`；HEAD 与 origin/formal-ir-mainline 精确等值绑定 `cb4f9990f7864e12dd69c89ee87ec8a58e77470d`；四文件 SCOPED dirty（含 v47 替代 v46）；绑定 `fake_runner=False`；无 fake-runner CLI 选项；守卫失败非零退出、零 calls、不创建文件；budget 硬帽 54。
- 仅 fake-runner 测试；测试中不做生产解码；真实 `tag_ok` 分流仅执行期测量；增加 H1 前缀秩/切片一致性测试与 first-match 终态测试。

## 14. 自由裁量决策 D1-D15（主线程复核清单，沿用 V46 并更新 V47）

- **D1 形态**：单变量 H1 压缩诊断，三臂 Treatment 配对、54 invocations（27 L1 +27 L2）、无 V43 Control baseline；H1-16 为对照，三臂共享同块同 L2，仅 H1 行数差异；不并行多方案，不上 joint GF1024。
- **D2 seed registry**：九枚 x25-x27/源冻结（390125-127/225-227/325-327）；FORBIDDEN 并集 78（V36_A3∪V39∪V40∪V41∪V42∪V43∪V44∪V45）+ V46 9 =87 隔离后新区零重叠；规划时零重叠已验，实现复验 J2。
- **D3 代表矩阵**：三枚 lane_c ordinal-2 id 死写（§5）+ 一枚 H1 母矩阵 `V31-H1-QC-16×1024` 死写并前缀 `8/12/16` 秩校验；严格重建比对而非 import 事实（J3 三重建，H1 含 capacity/projective/rank per prefix）。
- **D4 detected 作用域**：`detected_verification_failure` 仅臂内计为 rejected 不计 exact，通过 `stopped_for_analysis[arm]` 标记；G3' 仅 `undetected==0` 生效，无全局、无跨臂否决；first-match 不因单臂 detected 否决他臂。
- **D5 门禁阈值**：沿用 V46 形态逐臂（≥7/9，≥2/3/源，`undetected==0`），基于 `exact_full` + `tag_ok`（L2-only），`L1 wrong` 单独报告。
- **D6 哨兵落点**：每源首块 390125/390225/390325，三臂各六项/七项 fake-beliefs 通路 + `h1_prefix_ok`（`8⊂12⊂16` 秩/切片）+ `v35_tag_import_ok`（L2-only 空前缀 + x1 不变/x2 敏感）。
- **D7 call 序**：源 1M/1p5M/2M、块升序、臂按 `h1_8→h1_12→h1_16`。
- **D8 SCOPED-dirty 范围**：v47 模块+v47 CLI+v38 模块+v35 模块（含 tag 源）。
- **D9 preflight 失败证据策略**：invalid 三件套零 L2 calls（l1 27→0, 各臂 0, total 0）；拒绝类不建目录。
- **D10 文件集**：最小固定集（records 27 行含 tag_ok/reclassified/tag_scope/leak + summary 含四类三臂+first-match）；永不写 NPZ。
- **D11 终态命名**：五终态 `V47_H1_8_RETAINED / V47_H1_12_RETAINED / V47_H1_16_ONLY / V47_NO_H1_SIZE_RETAINED` + `V47_EVIDENCE_INVALID`，first-match 最小 `m1`。
- **D12 后继语**：仅方向性（§1/§7），不授权；不启动 V48。
- **D13 O1 机制**：L1 APP 软转移按 §5 冻结（`p_i→s1^{m1}→BP_i^{m1}→q_i^{m1}→P_i(U2)` 单向，复用通用 FFT-QSPA BP posterior / APP approximation，泄漏区分三臂，early-stop 冻结）+ V35 `compute_tag_64(empty,x2)[:16]` L2-only 工程 verification。
- **D14 errors_initial 策略**：沿用 V46 严格 per-block 三臂等值 J6 门（同 seed 三臂 `errors_initial` 严格等值）。
- **D15 组合三臂路径 + tag**：单码路径、可注入 `decode_fn`；在 L2 解码后追加 `compute_tag_64(empty,x2)` L2-only 比对，无 `x_hat` 全量保存需求。

## 15. V46 处置衔接与本诊断新颖性边界

V46 已以 `H1-16` 在 9 块上验证 `exact_full` + verification 新语义；V47 在此之上追加 **H1 前缀压缩**：`m1=8/12` 的 `s1^{m1}` 更短、`q^{m1}` 更接近 `p`，考验 L1 APP 在更低冗余下是否仍能支撑 `exact_full ≥7/9`。真实 `mean_abs_diff(q^{m1},p)` 与 `APP entropy` 按 `m1` 分臂诊断上下文。三臂共享同一 L2-only verification，不引入 x1 oracle；泄漏差异仅 `m1·5`。
