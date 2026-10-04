# OpenSpec Design: formal-ir-v46-verification-semantics

**Lifecycle**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V47。修订后保持此状态，等待再次评审。**
**Cycle**: `V46P0`
**Predecessor**: V45 `formal-ir-v45-l1-app-soft-transfer` (HEAD `2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`)
**Investigation anchor**: `2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`（V45 记账 tag 未落地；V45 18 条记录无 x_hat 的 tag 重放信息量接近零故删除）
**HEAD**: `2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`（实现冻结时 `git rev-parse` 精确重绑）
**Revision**: V46-REV L2-only — `tag_scope=l2_only`, `compute_tag_64(empty, x2)` 空前缀复用

## 1. 科学问题（单一，fresh-block verification）

> 在固定 Lane C 三矩阵 + V31 H1 + 同参 `90/1.0` 冻结下，**syndrome-derived L1 APP 软转移 Treatment（`Σ q_i P(U2|B,u1)`, `q_i=softmax BP_posterior(H1,p_i,s1)`）相对 V43 soft-marginal Control（`P(U2|B)=Σ p_i P(U2|B,u1)`）的 7/9 类增益，能否在**真实 64-bit L2-only verification acceptance（`tag_ok`）**下复现？**

- 分支冻结：当前属“tag 仅记账”分支 → 规划**复用 V35 已有 `compute_tag_64` 的 fresh-block confirmation**；不走“对 V45 18 条无 x_hat 记录的重放”（已删除：`x_hat` 缺失 → `tag_hat/tag_true` 无法生成，只能得 `verification_not_applicable_missing_hash`，信息量接近零，不得创建全 N/A 只读 run）。
- 若 tag 已实际执行则应改规划“保存最小 decoded-difference 诊断 + L2 图/陪集调查”，本轮不走（互斥）。
- V45 仍保留原终态与记账语义，不追溯修改；V46 用全新 9 块回答上述复现问题。

## 2. 冻结语义

### 2.1 Tag 来源与复用（不重新实现，L2-only 空前缀）

- **复用函数**（verbatim，不重新实现 canonical 编码）：
  ```python
  from comparison_bench.src.comparison_bench.formal_ir.v35_algorithm_development import (
      compute_tag_64,
  )
  # v35 已冻结：
  # def compute_tag_64(x1, x2) -> str:
  #     b1 = bytes(np.asarray(x1, dtype=np.uint8).reshape(-1).tolist())
  #     b2 = bytes(np.asarray(x2, dtype=np.uint8).reshape(-1).tolist())
  #     return hashlib.sha256(b1 + b2).hexdigest()[:16]
  # 注：compute_tag_64_symbols 仅作为来源说明，不宣称与空前缀调用等价
  ```
  V46 SHALL 直接调用该函数及其 canonical encoding（`b1+b2` 拼接 → SHA-256 → hex 前 16 字符 = trunc64），SHALL NOT 另行实现 `canonical_bytes` / `tag_of` / 大小端/定长归一化，不宣称 `compute_tag_64_symbols` 与空前缀调用等价。
- **L2-only 冻结**：`tag_scope=l2_only`；`target_tag = compute_tag_64(empty_uint8, x2_true)`，`candidate_tag = compute_tag_64(empty_uint8, x2_hat)`，其中 `empty_uint8 = np.empty(0, dtype=np.uint8)`。**删除所有 `compute_tag_64(x1_true, x_hat)` 形态**（避免把 Alice 真值 x1_true 放入 Bob 候选 tag 引入 oracle 并破坏 Control 不计 80-bit 泄漏口径）。
- **对称性**：Control 和 Treatment 使用**完全相同的 L2 verification**，不使用 `x1_true` 或共享 L1 decode；64-bit tag 与当前 `L2+tag` 泄漏口径一致（已含 64）。
- **生成/比对**：`target_tag = compute_tag_64(empty, x2_true)`（Alice 侧，计泄漏 64 已含），`candidate_tag = compute_tag_64(empty, x2_hat)`（Bob 重算），`tag_ok = (candidate_tag == target_tag)`；每条 L2 record 保存 `target_tag/candidate_tag/tag_ok`，**不必保存完整 `x_hat`**（节省空间，仍可验 acceptance；若需诊断可另行按需保存 `decoded_difference` 最小集，非必需）。
- **Determinism**：同一 `x2` 必得同一 tag（`empty` 固定）；实现提供双向重算一致性（Alice vs Bob）自检。
- **测试不变量**：改变 `x1_true` 不得改变 V46 L2 tag；改变 `x2` 必须改变测试锚点 tag（见 tasks B3）。
- **L2 边界**：本轮 tag **只验证 L2**，不代表完整 `(U1,U2)` 帧验证；`exact_full = exact_u1 && exact_l2` 仍为 oracle development metric，单独报告。
- **Leakage**：已计入 `leak_total`（`L2+tag = 920/950/960 +64 = 984/1014/1024`，Treatment 若含 L1 则 `1064/1094/1104`），V46 不新增、不重复计费，summary 显式标注“leakage already accounted”。

### 2.2 工程近似语义（固定公开 SHA-256 的局限）

- `tag_match && !exact` 的 `≈2^-64` SHALL 降为**随机哈希模型下的工程近似**，明确对**固定公开 SHA-256 截断**只能作此近似，不宣称信息论安全界。
- 若需严格 `2^-64` 界，需 **universal2 + seed 语义**（随机哈希族 + 公开 seed 采样/传输/验证），本轮不实现、不宣称；文档与 summary 显式说明该边界。

### 2.3 时序（pre-tag 正确性保留 + verification gate）

```
decode(H, prior, syndrome) → syndrome_ok / exact_l2 (oracle vs u_true) / wrong_codeword (=syndrome_ok && !exact) / G3'
        ↓  (pre-tag, 沿用 V45)
verification (L2-only): target_tag = compute_tag_64(empty, x2_true); candidate_tag = compute_tag_64(empty, x_hat); tag_ok = (candidate==target)
        ↓
reclassified (四类):
  exact                              → exact (tag_ok==true && exact, 必同时满足)
  syndrome_ok && !exact && !tag_ok   → detected_verification_failure (主捕获路径)
  !syndrome_ok && !exact             → decoder_non_syndrome_failure (原 structure_failure 更名)
  tag_ok && !exact                   → undetected_accepted_wrong (≈2^-64 工程近似，下文 G3')
```

`wrong_codeword_l2 / exact_l2` 均在 tag 检查之前计算，不得后移；verification 仅在其后追加 `tag_ok` acceptance gate。`tag_ok==false` 的记录 SHALL 计作**非 exact / rejected frame**，不计入 exact 统计。`exact_full` 仍由 `exact_u1 && exact_l2` 单独报告，不经 tag。

### 2.4 四类可区分（替代原二/三类）

- **exact**：`exact_l2 == true`（必 `tag_ok==true`，否则非 exact）。
- **detected_verification_failure**：`syndrome_ok && !exact && !tag_ok` — LDPC 陪集错误被 tag 捕获，计为 detected/rejected，不计 exact。
- **decoder_non_syndrome_failure**（原 `structure_failure` 更名）：`!syndrome_ok && !exact` — 译码未满足校验，成因可能为图/先验/迭代/BP 动力学等，不单归因结构，与 verification 正交。
- **undetected_accepted_wrong**：`tag_ok==true && !exact` — 概率约 `2^-64` 工程近似，仍 `!exact`，不计 exact，单独计数 `undetected_accepted_wrong_count`。

`exact_l2` 仍为 oracle 判真（ground truth），verification 不覆盖 exact；summary 同时报告 `exact_l2` 与 `verification_accept (tag_ok)`。`exact_full` 另行 oracle 报告。

### 2.5 V45 边界（不追溯）

V45 的 18 条记录未保存 `x_hat/hash`，SHALL 不追溯重放、不标记 `verification_not_applicable_missing_hash` 的零信息 run；V45 终态/结论/文件保持 byte-identical。不把 `errors_final=3` 同残留等同同码字。

## 3. 冻结样本集（9 个新块，预注册，FORBIDDEN 78）

延续 `390x` 源前缀递增约定，V45 占用 `390119-121/219-221/319-321`（x19-x21/源）后，本变更取其后三枚/源（x22-x24/源）：

| source | 新 block seeds |
|---|---|
| 1M | 390122, 390123, 390124 |
| 1p5M | 390222, 390223, 390224 |
| 2M | 390322, 390323, 390324 |

FORBIDDEN 并集 = V36_A3(15: 360101-105/360201-205/360301-305) ∪ V39(15: 390101-105/390201-205/390301-305) ∪ V40 probe(3: 390106/390206/390306) ∪ V41 confirm(9: 390107-109/390207-209/390307-309) ∪ V42 diagnostic(9: 390110-112/390210-212/390310-312) ∪ V43 diagnostic(9: 390113-115/390213-215/390313-315) ∪ V44 diagnostic(9: 390116-118/390216-218/390316-318) ∪ V45 diagnostic(9: 390119-121/390219-221/390319-321) = **78 seeds**。九枚新区为每源 x22-x24 连续递增，无内部重复，与全部八族零重叠（P3/J2 机械复验）。采样语义：`sample_empirical_block(V25 TRAIN counts, block_seed, BLOCK_LENGTH=1024)` + `factorize_f03`；每块样本计算一次并被两臂共享。

## 4. 冻结 workload（27 decoder invocations，18 L2 records，沿用 V45）

**预算**：每块 `L1 BP 1 + Control L2 1 + Treatment L2 1 =3` invocations，共 `9×3=27` decoder invocations；L2 performance records 18 条（C01-C18）；Summary 分别记录 `l1=9 / control_l2=9 / treatment_l2=9 / total=27`（planned/completed/started actuals）。

L2 records 顺序冻结（D7）：源 1M/1p5M/2M，块按 seed 升序，`cond_control` 在 `cond_l1_app` 之前：

| call | source | block_seed | condition | matrix_id (lane_c ordinal 2) | H1 |
|---|---|---|---|---|---|
| C01 | 1M | 390122 | cond_control | lane_c_1M_s383102 | V31-H1-QC-16×1024 |
| C02 | 1M | 390122 | cond_l1_app | lane_c_1M_s383102 | V31-H1-QC-16×1024 |
| C03 | 1M | 390123 | cond_control | lane_c_1M_s383102 | V31-H1-QC-16×1024 |
| C04 | 1M | 390123 | cond_l1_app | lane_c_1M_s383102 | V31-H1-QC-16×1024 |
| C05 | 1M | 390124 | cond_control | lane_c_1M_s383102 | V31-H1-QC-16×1024 |
| C06 | 1M | 390124 | cond_l1_app | lane_c_1M_s383102 | V31-H1-QC-16×1024 |
| C07 | 1p5M | 390222 | cond_control | lane_c_1p5M_s383202 | V31-H1-QC-16×1024 |
| C08 | 1p5M | 390222 | cond_l1_app | lane_c_1p5M_s383202 | V31-H1-QC-16×1024 |
| C09 | 1p5M | 390223 | cond_control | lane_c_1p5M_s383202 | V31-H1-QC-16×1024 |
| C10 | 1p5M | 390223 | cond_l1_app | lane_c_1p5M_s383202 | V31-H1-QC-16×1024 |
| C11 | 1p5M | 390224 | cond_control | lane_c_1p5M_s383202 | V31-H1-QC-16×1024 |
| C12 | 1p5M | 390224 | cond_l1_app | lane_c_1p5M_s383202 | V31-H1-QC-16×1024 |
| C13 | 2M | 390322 | cond_control | lane_c_2M_s383302 | V31-H1-QC-16×1024 |
| C14 | 2M | 390322 | cond_l1_app | lane_c_2M_s383302 | V31-H1-QC-16×1024 |
| C15 | 2M | 390323 | cond_control | lane_c_2M_s383302 | V31-H1-QC-16×1024 |
| C16 | 2M | 390323 | cond_l1_app | lane_c_2M_s383302 | V31-H1-QC-16×1024 |
| C17 | 2M | 390324 | cond_control | lane_c_2M_s383302 | V31-H1-QC-16×1024 |
| C18 | 2M | 390324 | cond_l1_app | lane_c_2M_s383302 | V31-H1-QC-16×1024 |

另有 9 次 L1 invocations（每块一次，记为 L1-01..L1-09，与上表块一一对应），总计 27。18 行去重得 **3 枚唯一 L2 矩阵**（lane_c × source，ordinal-2）+ **1 枚唯一 H1**（V31 QC-cyclic 16×1024）；成员/顺序漂移即 J12。H1 与 L2 矩阵分别重建比对（J3 双重建）。

## 5. 代表矩阵与译码合约（冻结，沿用 V45 §5-§6）

- **Lane C ordinal-2 / source**：`lane_c_1M_s383102`、`lane_c_1p5M_s383202`、`lane_c_2M_s383302`（以 committed v41 模块常量表校验）。
- **H1**：`V31-H1-QC-16×1024`（`m1=16, n=1024, family=QC-cyclic-projective, GF32 poly37, rank16, capacity_ok, projective_safe, full_row_rank`）。
- **译码合约**：27 invocations 共享 `GF32 poly37, max_iter=90, damping_alpha=1.0, syndrome from true u2_alice / s1=H1·u1^Alice (80 bits), success primary = exact_l2 (L2-transfer) 同时报告 exact_full=exact_u1&&exact_l2, decoder = 通用 decode_row_layered_fftqspa(H,prior,syndrome).bp_posterior_beliefs (BP posterior / APP approximation, 冻结 early-stop)`。
- **O1 机制**：Control `P_i^{control}(U2)=Σ p_i(u1)P(U2|B,u1)`，Treatment `P_i^{treat}(U2)=Σ q_i(u1)P(U2|B,u1), q_i=softmax BP_i(H1,p_i,s1)`，其中 `p_i(u1)=P(U1|B_i)` 来自 V25 C，`s1` 计 80 bits，`BP_i` 为 BP posterior beliefs / APP approximation 非精确 APP，`f_total=leak_total/[N(H1+H2)] N=1024`，泄漏 `Control 984/1014/1024 vs Treatment 1064/1094/1104 (L2 syndrome 920/950/960+80+64)`。
- **D15 组合路径**：沿 V42/V43 模式单薄环路（`sample_empirical_block` 每块一次 → `factorize_f03` → L1 `p_i→s1→BP_i→q_i` → per-arm L2 prior → `syndrome_of_gf32(H_L2,u2_alice)` → `decode_row_layered_fftqspa` + `compute_tag_64(empty, x2)` verification），`decode_fn` 可注入，默认 accepted 解码器，`wrong_codeword = syndrome_ok and not exact` 永不计 exact。
- **V35 复用点**：`target_tag/candidate_tag/tag_ok` 在每条 L2 记录解码后立即计算（`empty+x2` L2-only）；`tag_ok==false` 即 `detected_verification_failure`，`tag_ok==true && !exact` 即 `undetected_accepted_wrong`。

## 6. 每条件门禁（路由/归因保留，G3 新语义）

对 X ∈ {cond_control, cond_l1_app}，各以其 9 条 L2 records 判定：

- G1'：X 的 overall exact_l2 ≥ 7/9
- G2'：X 的每源 exact_l2 ≥ 2/3
- G3'：X 的 **`undetected_accepted_wrong ==0`**（`tag_ok==true && !exact` 计数为 0）

X 通过当且仅当三条全满足；门禁仅判定条件保留，不支持条件间优劣排序。`detected_verification_failure` 不触发 G3'，仅 `undetected_accepted_wrong` 触发。不要求 decoder 永不产生 `syndrome_ok && !exact`（其被 gate 捕获为 detected 时 G3' 仍可通过）。同时报告 `exact_full` 作完整 reconciliation 参照，但不入 G1'/G2'/G3' 且不经 tag（L2-only）。

## 7. 终态机（总量互斥；EVIDENCE_INVALID 优先；新命名沿用 V45）

五终态（总量互斥，覆盖 `(control_pass, treatment_pass)` 平面；oracle 不占维度）：

```text
0. 任意完整性/执行失败 -> V46_EVIDENCE_INVALID
1. pass_control AND pass_treatment -> V46_BOTH_RETAINED
     （Both retained：L1-APP 在 verification acceptance 下仍保留信号）
2. 仅 pass_control -> V46_L1APP_NO_VALUE_OR_HARM
     (Control-only：L1-APP 无价值或有害，额外 80-bit 未在 verification 下改善)
3. 均不通过 -> V46_GO_STRUCTURE
     (Both fail：转 joint/protograph/MET)
4. 仅 pass_treatment -> V46_L1APP_ADDED_VALUE_SIGNAL
     (Treatment-only：新增价值信号仅检查，不作无条件优于 control 的泛化)
```

规则 1-4 穷尽互斥覆盖 `(pass_control, pass_treatment)` 平面，规则 0 优先；真值表测试枚举 integrity ok/failed × 四格并断言互斥必做。summary 终态下区分四类计数 `exact / detected_verification_failure / decoder_non_syndrome_failure / undetected_accepted_wrong`（per-condition/per-source/per-block），`undetected_accepted_wrong` 计数即 G3' 判定依据。

Wrong 处理（逐臂局部）：`detected_verification_failure` 并置 `stopped_for_analysis[condition]=true` 仅通过本臂 G3' 需为 `undetected==0` 语义体现；无全局 wrong，无跨臂否决；任意 control 臂 `undetected` 立旗 `control_arm_undetected_anomaly=true`。

orthogonal 标志：`needs_1p5m_structure_branch` 当且仅当 `control exact on 1p5M < 2/3` 时立旗，独立于终态。

## 8. O3 配对语义

- 同 `block_seed` 的确定性样本 `(idx, alice, bob)` 每块算一次并传两臂；每块 L1 invocation 共享同一 `p_i/s1` 求 `q_i`。
- 同 H_L2（该源 lane_c ordinal-2）、同设置 90/1.0、同域/多项式、同 L2 syndrome、同样本；两臂唯一差异为 L2 先验构造（V43 soft-marginal `p_i` vs syndrome-derived `q_i`）+ Treatment 的 `tag_ok` gate；H1/s1/L1 APP 仅 treatment 臂引入，control 臂亦做 `compute_tag_64(empty, x2)` L2-only verification（同样本 `x2_hat` 路径，不用 x1_true）。
- 跨条件残差差异（`errors_final/iterations/exact_l2/syndrome_ok/tag_ok/wrong_codeword`）是诊断量本身，永不作完整性失败。
- `exact_full` 与 `exact_l2` 同时记录；`exact_u1` 来自 L1 hard decision（`argmax q_i`），`exact_u1==false` 不阻止 L2 软转移；`exact_full` 不经 tag。

完整性检查跨条件适用性：J2/J3/J4/J5/J6/J8-J12 与 V45 同构，仅将 69 更新为 78 与 `structure_failure` 更名为 `decoder_non_syndrome_failure`、G3 更新为 `undetected==0`；`errors_initial` 严格 per-pair 跨臂等值门（D14/J6）保留。

## 9. 科学 preflight、守卫序、证据分层

守卫序冻结（沿用 V45 §11）：

1. **拒绝类守卫最先、建目录前**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `git rev-parse origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定 `2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`；四文件 SCOPED tracked-dirty 检查（v46 模块、v46 CLI、v38_architecture_triage.py、v35_algorithm_development.py（含 tag 源））；输出根已存在即拒（J7）；任一拒绝非零退出、零 calls、不创建任何文件。
2. **科学 preflights（decoder-free、write-free）**：seed-registry 校验（J2，八族并集 78）；H1 (QC 16×1024) 与 3 枚 L2 唯一矩阵确定性重建并与 committed 结构权威严格比对含 permutations/capacity/projective/rank（J3 双重建）；三源 counts 形态/加载经 accepted loader（J4）；首块/源双条件绑定哨兵 390122/390222/390322 — 仅校验数据通路：control 六项 + treatment fake 七项（同 V45 §11）+ 新增 `v35_tag_import_ok`（`compute_tag_64` 可 import 且 `compute_tag_64(empty, x2)` 空前缀形态可用、`hex[:16]` 长度、x1 不变性/x2 敏感性）与 `leakage_accounted`（含 64 tag 工程 verification 声名）+ `tag_scope_l2_only` 校验；真实 `q≠p`、L1 iterations/syndrome/exact/wrong、APP entropy/confidence 不在此 gate，仅执行期测量。
3. **Preflight 失败** → 建增量根，写 `v46_invalid_notice.json` + 空 records + `v46_summary.json`（terminal `V46_EVIDENCE_INVALID`，planned 27 / l1 0 / control 0 / treatment 0 / total 0，无聚合）后零 decoder calls 停止。
4. **建根**：仅在全部拒绝类守卫与科学 preflights 通过后、首个 decoder call 前。

哨兵同 V45 §11 形态，仅更新 registry 与 tag import（L2-only 空前缀）；`fake_path_verified` 保留。

## 10. 记录、聚合、summary

记录 schema（每 L2 call，在 V45 §12 基础上增 `target_tag/candidate_tag/tag_ok` 与四类，`tag_scope=l2_only`）：

```
call_id("C01".."C18"), condition("cond_control"|"cond_l1_app"), source,
construction_seed, construction_seed_ordinal, block_seed, matrix_id, h1_matrix_id,
max_iter, damping_alpha, errors_initial, errors_final, exact_l2, exact_u1, exact_full,
syndrome_ok_l2, syndrome_ok_l1, wrong_codeword_l2, wrong_codeword_l1,
target_tag, candidate_tag, tag_ok, tag_scope("l2_only"),
reclassified ∈ {exact, detected_verification_failure, decoder_non_syndrome_failure, undetected_accepted_wrong},
iterations_l1, iterations_l2, bp_posterior_entropy, mean_abs_diff_q_p,
status, runtime_s
```

其中 `reclassified` 由 `exact/syndrome_ok/tag_ok` 派生，四类互斥穷尽。L1 9 次 invocations 记账单列。`tag_scope` 恒为 `l2_only`；`target_tag/candidate_tag` 均为 `compute_tag_64(empty, x2)`。

Summary 含：记账（planned 27 / l1 9 / control 9 / treatment 9 completed/started actuals，total 27，structural/preflight decoder_calls=0）；`l1_diagnostics_by_source`（执行期测量永不 gate：`mean_abs_diff(q,p)`、`APP entropy/confidence`、`H1_rank/capacity_ok/projective_ok`、`iterations_l1` 分布、`exact_u1/syndrome_ok_l1/wrong_l1`）；per-condition 聚合（`exact_l2_total`、`exact_full_total`、每源、`detected_verification_failure / decoder_non_syndrome_failure / undetected_accepted_wrong` 各计数、`wrong_codeword` 明细、G3' `undetected==0` 判定）；per-source 聚合；per-block 配对结果 + errors_final delta + exact_full/tag_ok 对照；两臂门禁明细（G1'/G2'/G3' 数值与 pass/fail，基于 `undetected==0` 新 G3'）在 terminal 判定之后；路由轨迹；`terminal_state`+`terminal_reason`（新命名 V46）；`stopped_for_analysis` 每条件；`control_arm_undetected_anomaly`；`needs_1p5m_structure_branch` orthogonal 标志；master stop rule 原文；claim boundary（含工程近似、L2-only 与非等泄漏说明）；statistics note；provenance（authorized target SHA、HEAD/origin 绑定、前代 plan/execution SHAs、结构权威身份、H1 物料身份 `V31-H1-QC-16×1024 rank16`、V25 counts 溯源、O1 机制 id `l1_app_soft_transfer_H1_syndrome_derived_with_v35_tag_l2_only`、tag 源 `v35:compute_tag_64(empty,x2)[:16] tag_scope=l2_only`、泄漏 `Control 984/1014/1024 vs Treatment 1064/1094/1104` + L2 syndrome 920/950/960 + f_total，含工程 verification 声名 `SHA-trunc64 random-hash-model approximate 2^-64, not information-theoretic; strict bound requires universal2+seed; L2-only`）。

## 11. 统计与断言边界

仅描述性；样本 tiny 且成簇（27 invocations = 9 唯一块 × (1 L1 + 2 L2)；18 L2 records 配对）；比例报告带 n 与 raw counts；任何打印区间 naive 且未校正簇聚；无显著性检验；主要成功仅 `exact_l2` 且 `tag_ok` gate 后仍计 `exact`，`exact_full` 另行报告且不经 tag（L2-only）；`detected` 不计 exact。

断言边界 verbatim：结果仅支持 V25 TRAIN 经验 counts 开发块上的有界条件归因 — control 为 V43 soft-marginal `P(U2|B)`，`cond_l1_app` 按 O1 以 V31 H1 + 通用 FFT-QSPA `q_i=softmax BP posterior / APP approximation` 做真实 syndrome-derived 软转移、L2 在固定 Lane C 三矩阵 ordinal-2 上 90/1.0 单点、`Control 984/1014/1024 vs Treatment 1064/1094/1104 (L2 syndrome 920/950/960 + 80 + 64 tag, f_total, 工程 verification L2-only)`，复用 V35 `compute_tag_64(empty,x2)[:16]`，不改结构/阈值，`undetected≈2^-64` 仅随机哈希模型工程近似（固定公开 SHA-256 截断；严格界需 universal2+seed），Control/Treatment 非等泄漏比较为额外 80-bit 价值评估；均非真帧 FER 证据，不推阈值/SKR/正式执行/资格/晋升；终态仅方向性，不启动 V47。

## 12. 证据写出与增量输出根

固定增量根（在解码前建，fail-closed 若已存在；科学 preflight 失败亦建仅放 invalid 三件套）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v46_verification_semantics/run_01/
```

文件（最小固定集）：

- `v46_records.json` / `.csv`（每 L2 call 一行，共 18 行，含 `target_tag/candidate_tag/tag_ok/reclassified/tag_scope`；L1 诊断随行或单独数组）
- `v46_summary.json`（§10 内容，含四类计数、分层记账 27、门禁明细、工程 verification L2-only 声名、provenance 含 tag 源）
- `v46_invalid_notice.json`（仅完整性失败时）

CSV/JSON 行对等；禁写任何 `.npz`；禁以非 accepted loader 读 NPZ；既有 `results/`、V38-V45 输出保持 byte-identical。

## 13. 实现草图（后继轮次，当前未授权）

- 新模块 `comparison_bench/src/comparison_bench/formal_ir/v46_verification_semantics.py`：仅 import accepted `nonbinary_v31.build_layer/build_matrix_packet` / `v38` 重建 helper / `v35.compute_tag_64`；按 V45 D15 组合双条件路径（含 L1 APP 链 `p_i→s1→BP_i→q_i→P_i(U2)`，BP posterior / APP approximation，early-stop 冻结）并在每 L2 解码后调用 `compute_tag_64(empty, x2)` 生成/比对 tag（L2-only）；不 import v39/v40/v41/v42/v43/v44；registry 以拷贝数据常量进入（含 78）；不重新实现 canonical 编码，不引入 `compute_tag_64_symbols` 等价宣称。
- 新 CLI `scripts/execute_v46_l1_app_with_verification.py`：默认拒绝；必带 `--execution-authorized --authorized-target-sha <sha>`；HEAD 与 origin/formal-ir-mainline 精确等值绑定 `2f5f91431a85cc3e3801a1ec6a8a38bd22f2b032`；四文件 SCOPED dirty（含 v35）；绑定 `fake_runner=False`；无 fake-runner CLI 选项；守卫失败非零退出、零 calls、不创建文件；budget 硬帽 27。
- 仅 fake-runner 测试；测试中不做生产解码；真实 `tag_ok` 分流仅执行期测量；增加 x1 不变/x2 必变 tag 不变量测试。

## 14. 自由裁量决策 D1-D15（主线程复核清单，沿用 V45 并更新 V46）

- **D1 形态**：单阶段配对诊断，仅 Lane C + 单一复用 H1，27 invocations（9 L1 + 18 L2）、无 baseline/分期/额外矩阵；单一机制 `cond_l1_app`（syndrome-derived APP 软转移）对照 `cond_control`（V43 soft-marginal），复用 V35 tag 作 L2-only verification gate，不并行多方案，不上 joint GF1024。
- **D2 seed registry**：九枚 x22-x24/源冻结（390122-124/222-224/322-324）；FORBIDDEN 并集 = V36_A3 ∪ V39 ∪ V40-probe ∪ V41-confirm ∪ V42-diagnostic ∪ V43-diagnostic ∪ V44-diagnostic ∪ V45-diagnostic =78；规划时零重叠已验，实现复验 J2。
- **D3 代表矩阵**：三枚 lane_c ordinal-2 id 死写（§5）+ 一枚 H1 `V31-H1-QC-16×1024` 死写；严格重建比对而非 import 事实（J3 双重建，H1 含 capacity/projective/rank）。
- **D4 detected 作用域**：`detected_verification_failure` 仅臂内计为 rejected 不计 exact，通过 `stopped_for_analysis` 标记；G3' 仅 `undetected_accepted_wrong==0` 生效，无全局、无跨臂否决。
- **D5 门禁阈值**：沿用 V43 形态逐臂（≥7/9，≥2/3/源，`undetected==0`），基于 `exact_l2` + `tag_ok`（L2-only）。
- **D6 哨兵落点**：每源首块 390122/390222/390322，fake-beliefs 通路 + `v35_tag_import_ok`（L2-only 空前缀 + x1 不变/x2 必变）。
- **D7 call 序**：源 1M/1p5M/2M、块升序、pair 内 control 先。
- **D8 SCOPED-dirty 范围**：v46 模块+v46 CLI+v38 模块+v35 模块（含 tag 源）。
- **D9 preflight 失败证据策略**：invalid 三件套零 L2 calls（total 0）；拒绝类不建目录。
- **D10 文件集**：最小固定集（records 含 tag_ok/reclassified/tag_scope + summary 含四类）；永不写 NPZ。
- **D11 终态命名**：五终态 `V46_BOTH_RETAINED / V46_L1APP_NO_VALUE_OR_HARM / V46_GO_STRUCTURE / V46_L1APP_ADDED_VALUE_SIGNAL` + `V46_EVIDENCE_INVALID`，四类计数与 G3' 新语义。
- **D12 后继语**：仅方向性（§1/§7），不授权；不启动 V47。
- **D13 O1 机制**：L1 APP 软转移按 §5 冻结（`p_i→s1→BP_i→q_i→P_i(U2)` 单向，复用通用 FFT-QSPA BP posterior / APP approximation，泄漏区分 Control vs Treatment，early-stop 冻结）+ V35 `compute_tag_64(empty,x2)[:16]` L2-only 工程 verification。
- **D14 errors_initial 策略**：沿用 V45 严格 per-pair 跨臂等值 J6 门。
- **D15 组合双条件路径 + tag**：替代复用 `evaluate_single_block`；单码路径、可注入 `decode_fn`；在 L2 解码后追加 `compute_tag_64(empty,x2)` L2-only 比对，无 `x_hat` 全量保存需求。

## 15. V44/V45 处置衔接与本诊断新颖性边界

V44 `q=P(U1|B)` 已证退化为 V43 `P(U2|B)`；V45 以 `M_{H1,s1}` 非平凡消息为必要条件（`q^{(t)}∝p·M^{(t)}_{H1,s1}≠p`）。V46 在此之上追加 **V35 L2-only 工程 verification gate**（`empty+x2`）：`syndrome_ok && !exact` 不再静默为陪集错误，`!tag_ok` 捕获为 `detected`，仅 `tag_ok && !exact`（工程近似 `2^-64`）为 `undetected_accepted_wrong` 并触发 G3'。`decoder_non_syndrome_failure`（`!syndrome_ok && !exact`）与 verification 正交。真实 `mean_abs_diff(q,p)` 与 `APP entropy` 仅执行期诊断上下文。Control/Treatment 共享同一 L2-only verification，不引入 x1 oracle。
