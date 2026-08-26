# OpenSpec Design: formal-ir-v44-soft-prior-conditioning

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（待本线程独立 plan ACCEPT 后进入 `PLAN_ACCEPTED / EXECUTE_NOT_AUTHORIZED`）
**Cycle**: `V44P0`
**Predecessor**: V43P0 `formal-ir-v43-soft-marginal-diagnostic`（terminal `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`，result SHA `4e2ed4db`；继承其 Lane C / 三矩阵 / 90/1.0 / 9 blocks×2 arms=18 calls 恰好一次 / J6 SCOPED 路径 / Master Stop Rule 形态；本变更仅把 `cond_soft_marginal` 替换为单一 `cond_soft_prior`，延续五终态与 orthogonal 标志语义，重命名 `SOFT_MARGINAL` 为 `SOFT_PRIOR` 相关）

## 1. 科学问题（单一，明确来源）

在 Lane C 图结构与译码设置完全冻结下，**无码 soft prior** `q_i(u1)= Σ_{u2} counts[u1·32+u2,b] / Σ_{u1',u2'} counts[u1'·32+u2',b] = P(U1|B=b)`（纯 `counts_true + bob`，零额外通信，`counts` 为公共先验不计泄漏，每 `b` 归一和=1、floor 1e-15）是否在相同门禁（G1'≥7/9 且 G2'≥2/源 且 G3' zero-wrong）下保留信号？以冻结门禁判定分流：BOTH pass 则支持继续 soft/joint conditioning；oracle-only 则判定 soft-prior conditioning 不足；both fail 则转 joint/protograph/MET；anomalous（soft pass + oracle fail）仅检查，不解释为 soft 优于 oracle。所有分流仅描述方向、不授权任何后继。

**机制来源明确性**（spike 已验证）：`q_i` 仅依赖 `counts_true` 与 `bob`，无 Alice 真值、无事后权重、无 C04 调参、无 L1 decoder 复用；归一/退化/稳定性已通过 spike 校验。

## 2. 前代绑定与只读输入

只读：

- 结构权威 `comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json`
- V25 TRAIN counts 经 accepted `load_v25_channel_counts()` 唯一入口（公共先验，零额外通信）
- V40/V41/V42/V43 run_01 summary 仅作身份/溯源引用；V43 已 durable（terminal `V43_ORACLE_ONLY_SOFT_MARGINAL_BOTTLENECK`，result SHA `4e2ed4db`）；不 import v39/v40/v41/v42/v43 模块

## 3. 冻结样本集（9 个新块，预注册）

延续 `390x` 源前缀递增约定，`390110-115 / 210-215 / 310-315` 已被 V42+V43 占用，本变更取其后三枚/源：

| source | 新 block seeds |
|---|---|
| 1M | 390116, 390117, 390118 |
| 1p5M | 390216, 390217, 390218 |
| 2M | 390316, 390317, 390318 |

FORBIDDEN 并集 = V36_A3(15: 360101-105/360201-205/360301-305) ∪ V39(15: 390101-105/390201-205/390301-305) ∪ V40 probe(3: 390106/390206/390306) ∪ V41 confirm(9: 390107-109/390207-209/390307-309) ∪ V42 diagnostic(9: 390110-112/390210-212/390310-312) ∪ V43 diagnostic(9: 390113-115/390213-215/390313-315) = **60 seeds**。九枚新区为每源 x16-x18 连续递增，无内部重复，与全部六族零重叠（P3/J2 机械复验）。

采样语义与既有协议一致：`sample_empirical_block(V25 TRAIN counts, block_seed, BLOCK_LENGTH=1024)` + `factorize_f03`；每块样本计算一次并被两臂共享（配对保证 §10）。

## 4. 冻结 workload C01-C18（恰好 18 calls）

顺序冻结（D7）：源 1M/1p5M/2M，块按 seed 升序，`cond_oracle` 在 `cond_soft_prior` 之前：

| call | source | block_seed | condition | matrix_id (lane_c ordinal 2) |
|---|---|---|---|---|
| C01 | 1M | 390116 | cond_oracle | lane_c_1M_s383102 |
| C02 | 1M | 390116 | cond_soft_prior | lane_c_1M_s383102 |
| C03 | 1M | 390117 | cond_oracle | lane_c_1M_s383102 |
| C04 | 1M | 390117 | cond_soft_prior | lane_c_1M_s383102 |
| C05 | 1M | 390118 | cond_oracle | lane_c_1M_s383102 |
| C06 | 1M | 390118 | cond_soft_prior | lane_c_1M_s383102 |
| C07 | 1p5M | 390216 | cond_oracle | lane_c_1p5M_s383202 |
| C08 | 1p5M | 390216 | cond_soft_prior | lane_c_1p5M_s383202 |
| C09 | 1p5M | 390217 | cond_oracle | lane_c_1p5M_s383202 |
| C10 | 1p5M | 390217 | cond_soft_prior | lane_c_1p5M_s383202 |
| C11 | 1p5M | 390218 | cond_oracle | lane_c_1p5M_s383202 |
| C12 | 1p5M | 390218 | cond_soft_prior | lane_c_1p5M_s383202 |
| C13 | 2M | 390316 | cond_oracle | lane_c_2M_s383302 |
| C14 | 2M | 390316 | cond_soft_prior | lane_c_2M_s383302 |
| C15 | 2M | 390317 | cond_oracle | lane_c_2M_s383302 |
| C16 | 2M | 390317 | cond_soft_prior | lane_c_2M_s383302 |
| C17 | 2M | 390318 | cond_oracle | lane_c_2M_s383302 |
| C18 | 2M | 390318 | cond_soft_prior | lane_c_2M_s383302 |

18 行去重得 **3 枚唯一矩阵**（lane_c × source，ordinal-2）；成员/顺序漂移即 J12。

## 5. 代表矩阵（常量，复用 V42/V43 冻结身份）

Lane C ordinal-2 / source，沿用 V42/V43 三枚冻结 id（以 committed v41 模块常量表校验）：

- `lane_c_1M_s383102` (383102)
- `lane_c_1p5M_s383202` (383202)
- `lane_c_2M_s383302` (383302)

经 accepted V38 构造器确定性重建，与 committed 结构权威（含 Lane C `position_permutations`）严格比对（J3）；重建 decoder-free。

## 6. 译码合约（单点冻结；双条件组合路径）

18 calls 共享数值合约：

| parameter | value |
|---|---|
| field | GF(32), poly 37 |
| max_iter | 90 |
| damping_alpha | 1.0 |
| syndrome | 来自真 `u2_alice` |
| success | `exact_l2` vs 真 `u2_alice` |
| posterior 函数 | oracle 臂用 `get_conditional_posterior_l2(counts_true, bob, selector)`；soft-prior 臂用按 §7 的 `q_i(u1)` 构造的软先验（见 §7） |

每臂唯一差异：喂给译码的 conditioning 构造 —

- `cond_oracle`：selector = 真 `u1_alice`，`posterior = get_conditional_posterior_l2(counts_true, bob, u1_true)`（能力上界）；
- `cond_soft_prior`：不对 U1 做 hard 估计，不引入 Alice 真值，直接以 `q_i(u1)=P(U1|B=b)` 为 L1 软先验（§7 冻结定义），零额外通信。

**D15 组合路径**：`evaluate_single_block` 硬编码 oracle conditioning 且 `counts` 参数兼作采样与后验，复用会破配对。V44 模块沿 V42/V43 模式组合同一组 accepted 原语单薄环路（`sample_empirical_block` 每块一次 → `factorize_f03` → per-arm 先验/后验 → `syndrome_of_gf32(H, u2_alice)` → `decode_row_layered_fftqspa(...)`），复刻 v38 992-1030 仅改 conditioning 构造；数值均来自 accepted 模块；`decode_fn` 可注入，默认 accepted 解码器，测试注入 fake，生产 `fake_runner=False`（无 fake-runner CLI 选项）。`wrong_codeword = syndrome_ok and not exact_l2` 按记录派生，永不计为 exact，偏离即 J9。

## 7. O1 — soft-prior 条件机制（冻结，单一）

Hard `u1_hat`、V43 soft-marginal、多 joint/soft 并行路径**均禁用**。Soft-prior 冻结定义（verbatim，后续不得更改）：

```
对每位置 b ∈ bob（长度 1024）：
  raw_q[u1, b] = Σ_{u2=0..31} counts_true[u1*32+u2, b]
  q_i(u1 | B=b) = raw_q[u1, b] / Σ_{u1'=0..31} raw_q[u1', b]
  数值稳定：分母 floor 1e-15；每 b 求和 =1（容差 1e-12 内校验）
  通信/leakage：0 extra（counts_true 为已公开的公共先验，不计入本轮泄漏）
```

等价于经验联合分布在 `u2` 维求和后按 `b` 归一得 `P(U1|B)`；每 `b` 独立归一；采样仍仅用同一 `counts_true`，两臂共享一次生成的块；**禁止**引入 Alice 真值、事后权重/pilot/噪声/量化/joint 迭代/新矩阵/新 decoder 参数/失配信道律/C04 调参。`cond_soft_prior` 是“使用真实公共经验 counts 的无码 Bob-only 软先验”，不是具体 coded L1 方案，不得泛称为真实条件；spike 已验证归一/退化（均匀、尖峰）/稳定性（floor）。

诊断上下文（永不 gate）：可报告 per-source `q_i` 与 oracle 先验的统计差异（熵、max 概率等，仅上下文）。

## 8. 每条件门禁（路由/归因保留）

对 X ∈ {cond_oracle, cond_soft_prior}，各以其 9 calls 判定：

- G1'：X 的 overall exact ≥ 7/9
- G2'：X 的每源 exact ≥ 2/3
- G3'：X 的 wrong_codewords == 0

X 通过当且仅当三条全满足；仅判定条件保留，不支持条件/ lane 间优劣排序。

## 9. 终态机（总量互斥；EVIDENCE_INVALID 优先）

五终态：`V44_EVIDENCE_INVALID`、`V44_BOTH_PASS`、`V44_ORACLE_ONLY_SOFT_BOTTLENECK`（原 SOFT_MARGINAL 重命名为 SOFT_PRIOR）、`V44_GO_STRUCTURE`、`V44_ANOMALOUS_INVERSION`（保留 V42/V43 异常语义：soft pass + oracle fail）：

```text
0. 任意完整性/执行失败 -> V44_EVIDENCE_INVALID
1. pass_oracle AND pass_soft_prior -> V44_BOTH_PASS
     （BOTH pass：soft-prior 在相同门禁（G1'≥7/9 且 G2'≥2/源 且 G3' zero-wrong）下保留信号 → 支持继续 soft/joint conditioning）
2. 仅 pass_oracle -> V44_ORACLE_ONLY_SOFT_BOTTLENECK
     (oracle-only（即 V44_ORACLE_ONLY_SOFT_BOTTLENECK）：soft prior conditioning 不足)
3. 均不通过 -> V44_GO_STRUCTURE
     (both fail（即 V44_GO_STRUCTURE）：转 joint/protograph/MET)
4. 仅 pass_soft_prior -> V44_ANOMALOUS_INVERSION
     (anomalous（soft pass + oracle fail）：仅检查，不解释为 soft 优于 oracle)
```

规则 1-4 穷尽互斥覆盖 `(pass_oracle, pass_soft_prior)` 平面，规则 0 优先；真值表测试枚举 integrity ok/failed × 四格并断言互斥必做（T5）。

Wrong 处理（逐臂局部，D4 教训）：记录、永不计为 exact、仅通过本臂 G3' 生效、并置 `stopped_for_analysis[condition]=true`；无全局 wrong 规则、无跨臂否决；任意 oracle 臂 wrong 立旗 `oracle_arm_wrong_codeword_anomaly=true`。

所有终态下：不追加块、不补跑、不做第二轮诊断、不调阈值/机制；不自动启动后继。**orthogonal 标志**：`needs_1p5m_structure_branch` 当且仅当 `oracle exact on 1p5M < 2/3` 时立旗，独立于上述终态，不再与 conditioning 混在一起。

## 10. O3 配对语义

- 同 `block_seed` 的确定性样本 `(idx, alice, bob)` 每块算一次并传两臂（结构配对保证）。
- 同 H（该源 lane_c ordinal-2）、同设置 90/1.0、同域/多项式、同 syndrome、同样本；两臂**唯一**差异为 conditioning 构造（§6/§7）。
- 跨条件残差差异（`errors_final/iterations/exact_l2/syndrome_ok/wrong_codeword`）是**诊断量本身**，永不作完整性失败。

完整性检查跨条件适用性：

| 检查类 | 跨条件适用 |
|---|---|
| J2 registry / J3 重建 / J4 counts / J5 sentinels | 适用（共享 preflight，两臂继承） |
| workload & 配对完备：9 块各每条件一次、共 18 记录、顺序 C01-C18 | 适用（J6/J12） |
| 预算：18 started/completed 共帽 | 适用（J10） |
| 记录 schema、译码合约、NPZ 策略 | 适用（J8/J9/J11） |
| 跨臂 outcome-field 比较（errors_final/iterations/exact_l2/syndrome_ok/wrong_codeword） | 不适用 — 差异即信号 |
| `errors_initial` 一致性 | 臂内自洽 + 严格 per-pair 跨臂等值门（D14 沿用 V42/V43）：同块两臂 `errors_initial` 必须严格相等，先于该对解码检查；不等即 J6 → `V44_EVIDENCE_INVALID`（`errors_initial = sum(u2_alice != u2_bob)` 与先验构造无关，跨臂不等意味配对/求值器漂移）；字段 `pairing_errors_initial_equal` 仍作信息冗余记录 |

每对在 summary 记录 `both_exact/oracle_only_exact/soft_prior_only_exact/neither_exact` 及 `errors_final` delta（仅上下文）。

## 11. 科学 preflight、守卫序、证据分层

守卫序冻结（沿用 V42/V43/V40 经验）：

1. **拒绝类守卫最先、建目录前**：默认拒绝；必带 `--execution-authorized`；`git rev-parse HEAD` 与 `git rev-parse origin/formal-ir-mainline` 与 `--authorized-target-sha` 精确等值绑定；四文件 SCOPED tracked-dirty 检查（v44 模块、v44 CLI、v38_architecture_triage.py、v35_algorithm_development.py）；输出根已存在即拒（J7）；任一拒绝非零退出、零 calls、**不创建任何文件**。
2. **科学 preflights（decoder-free、write-free）**：seed-registry 校验（J2，六族并集 60，含 V43）；3 枚唯一矩阵确定性重建并与 committed 结构权威严格比对含 permutations（J3）；三源 counts 形态/加载经 accepted loader（J4）；首块/源双条件绑定哨兵 390116/390216/390316（J5）。
3. **Preflight 失败** → 建增量根，写 `v44_invalid_notice.json` + 空 records + `v44_summary.json`（terminal `V44_EVIDENCE_INVALID`，planned 18 / started 0 / completed 0，无聚合）后零 decoder calls 停止。
4. **建根**：仅在全部拒绝类守卫与科学 preflights 通过后、首个 decoder call 前。

哨兵（每探测块）：oracle 臂六项沿用 V41/V42/V43 形态（`bob_gt_31`、`captured_equals_bob`、`corrected_equals_direct`、`corrected_differs_u2bob_arraywise`、`corrected_differs_u2bob_maxabs>1e-6`、`argmax_divergence`）；soft-prior 臂四项：`soft_prior_public_inputs`（估计器仅允许 counts/bob 公开输入，拒 Alice 依赖）、`carrier_identity_soft_prior`（spy 捕获实际送解码的 soft prior 等于按 §7 从 `counts_true` 求和归一的 `q_i`）、`arms_differ`（soft prior 至少一位置与 oracle 后验/先验不同，证明非 oracle）、`soft_prior_normalization_ok`（每 `b` 求和为 1，容差 1e-12，floor 1e-15 生效）；探测失败仅 plan-review 可替换。

完整性检查（J2-J5 科学 preflight 类与 J6/J8-J12 解码环类致 `V44_EVIDENCE_INVALID`；J1/J7 为 Tier 0 拒绝不建目录）：

| id | 检查 |
|---|---|
| J1 | 授权/拒绝失败（默认拒绝、缺旗、SHA 非精确等值、SCOPED dirty 违规） |
| J2 | seed-registry 违规（九枚内重复、与 60 并集重叠、非每源 3） |
| J3 | 矩阵重建与权威不一致（含 permutations）或代表身份漂移 |
| J4 | counts 形态/加载失败 |
| J5 | 哨兵失败（oracle 六或 soft 四） |
| J6 | 配对违规：块-条件缺失/重复/总量非 18；臂内 `errors_initial` 自洽失败；严格 per-pair 跨臂 `errors_initial` 等值门 |
| J7 | 输出根已存在（fail-closed） |
| J8 | NPZ 策略违规（任意 NPZ 写、非 accepted loader 的 V25 访问） |
| J9 | 译码参数合约偏离（含 warm-start 键） |
| J10 | 记账违规（共享硬帽 18，第 19 call 结构拒，planned/started/completed 不一致） |
| J11 | 记录 schema 缺字段 |
| J12 | workload 漂移（集合/顺序/配对 ≠ 冻结 C01-C18） |

中途 `BaseException`：在已建根内原样保留 raw partial records + notice + summary（带 started/completed actuals）后重抛；不做性能聚合/门禁评定。

### 三层证据边界

| tier | 触发 | 落盘 | 进程 |
|---|---|---|---|
| Tier 0 执行拒绝 | J1/J7 | 不创建任何文件 | 非零退出、零 calls |
| Tier 1 科学 preflight 失败 | J2/J3/J4/J5 | 建增量根；invalid 三件套（planned 18/started 0/completed 0，无聚合） | 零 decoder calls，停止，不 rerun |
| Tier 2 中途 BaseException | 解码环任意异常 | 根内原样 partial + notice + summary(actuals) + 仅失败标记 | 重抛 |
| 正常完成 | 记录完整、完整性 ok | 最小固定集：records json/csv + summary；无 NPZ | exit 0 |

## 12. 记录、聚合、summary

记录 schema（每 call）：

```
call_id("C01".."C18"), condition("cond_oracle"|"cond_soft_prior"), source,
construction_seed, construction_seed_ordinal, block_seed, matrix_id,
max_iter, damping_alpha, errors_initial, errors_final, exact_l2, syndrome_ok,
wrong_codeword, iterations, status, runtime_s
```

Summary 含：记账（planned 18 / completed/started actuals，structural/preflight decoder_calls=0）；`soft_prior_diagnostics_by_source`（上下文，永不 gate）；per-condition 聚合（`exact_total`、per-source、wrong）；per-source 聚合；per-block 配对结果 + errors_final delta；两臂门禁明细（G1'/G2'/G3' 数值与 pass/fail）在 terminal 判定**之后**；路由轨迹；`terminal_state`+`terminal_reason`；`stopped_for_analysis` 每条件；`oracle_arm_wrong_codeword_anomaly`；`needs_1p5m_structure_branch`（当且仅当 `oracle exact on 1p5M < 2/3` 时为 true，orthogonal 标志）；master stop rule 原文；claim boundary；statistics note；provenance（authorized target SHA、HEAD/origin 绑定、前代 plan/execution SHAs、结构权威身份、V25 counts 溯源、O1 机制 id `soft_prior_q_no_code_counts_bob_only`）。
## 13. 统计与断言边界

仅描述性；样本 tiny 且成簇（18 calls = 9 唯一块 ×2 配对条件）；比例报告带 n 与 raw counts；任何打印区间 naive 且未校正簇聚；无显著性检验；成功仅 `exact_l2`。

断言边界 verbatim 约定：结果仅支持 V25 TRAIN 经验 counts 开发块上的**有界条件归因** — oracle 臂为真 Alice L1 的能力上界（实践不可得），`cond_soft_prior` 臂按 §7 用真实公共经验 counts 做无码 Bob-only 软先验 `q_i(u1)=P(U1|B=b)`、**不做** hard `u1_hat`/边缘化之外的多方案、零额外通信（counts 公共先验不计泄漏）、无 pilot/噪声/量化/失配信道律/C04 调参，不是具体 coded L1 方案，不得泛化为真实条件；均非真帧 FER 证据，不推阈值/SKR/正式执行/资格/晋升。无论结果如何禁止：FER、渐近阈值、SKR、安全、正式资格/晋升、真帧行为、条件/lane 间优劣或比较排名、历史门禁“现已通过”陈述、对 `V44_ORACLE_ONLY_SOFT_BOTTLENECK` 归因到具体上游编码或真实系统、对 `V44_ANOMALOUS_INVERSION` 读作 soft 优于 oracle。路由终态仅方向性、自动不启动任何后继。

## 14. 证据写出与增量输出根

固定增量根（在解码前建，fail-closed 若已存在；科学 preflight 失败亦建仅放 invalid 三件套）：

```
comparison_bench/outputs_comparison/formal_ir_methods/v44_soft_prior_conditioning/run_01/
```

文件（最小固定集）：

- `v44_records.json` / `.csv`（每 call 一行）
- `v44_summary.json`（§12 内容）
- `v44_invalid_notice.json`（仅完整性失败时）

CSV/JSON 行对等；禁写任何 `.npz`；禁以非 accepted loader 读 NPZ；既有 `results/`、V38-V43 输出保持 byte-identical。

## 15. 实现草图（后继轮次，当前未授权）

- 新模块 `comparison_bench/src/comparison_bench/formal_ir/v44_soft_prior_conditioning.py`：仅 import accepted v35 原语与 v38 构造/重建 helper；按 D15 组合双条件路径；不 import v39/v40/v41/v42/v43；registry 以拷贝数据常量进入；runner/writer/SHA 绑定/SCOPED-dirty/preflight 复用 V39-V43 成熟模式。
- 新 CLI `scripts/execute_v44_soft_prior_conditioning.py`：默认拒绝；必带 `--execution-authorized --authorized-target-sha <sha>`；HEAD 与 origin/formal-ir-mainline 精确等值绑定；四文件 SCOPED dirty；绑定 `fake_runner=False`；无 fake-runner CLI 选项；守卫失败非零退出、零 calls、不创建文件。
- 仅 fake-runner 测试；测试中不做生产解码。

## 16. 自由裁量决策 D1-D15（主线程复核清单）

- **D1 形态**：单阶段配对诊断，仅 Lane C，恰好 18 calls，无 baseline/分期/额外矩阵；**单一机制** `cond_soft_prior`，不并行测试多种 joint/soft 方案。
- **D2 seed registry**：九枚 x16-x18/源冻结；FORBIDDEN 并集 = V36_A3 ∪ V39 ∪ V40-probe ∪ V41-confirm ∪ V42-diagnostic ∪ V43-diagnostic =60；规划时零重叠已验，实现复验 J2。
- **D3 代表矩阵**：三枚 lane_c ordinal-2 id 死写（§5）；严格重建比对而非 import 事实。
- **D4 wrong 作用域**：仅臂内（G3'+stopped_for_analysis+oracle 异常旗）；无全局 wrong，无跨臂否决。
- **D5 门禁阈值**：沿用 V41/V43 形态逐臂（≥7/9，≥2/3/源，零 wrong）。
- **D6 哨兵落点**：每源首块 390116/390216/390316。
- **D7 call 序**：源 1M/1p5M/2M、块升序、pair 内 oracle 先。
- **D8 SCOPED-dirty 范围**：v44 模块+v44 CLI+v38 模块+v35 模块。
- **D9 preflight 失败证据策略**：invalid 三件套零 calls；拒绝类不建目录（V40 教训）。
- **D10 文件集**：最小固定集；永不写 NPZ。
- **D11 终态命名**：五终态含保留的 `V44_ANOMALOUS_INVERSION` 及重命名后的 `V44_ORACLE_ONLY_SOFT_BOTTLENECK`。
- **D12 后继语**：仅方向性（§1/§9），不授权。
- **D13 O1 机制**：soft-prior 按 §7 冻结（`q_i(u1)=Σ_{u2} counts/Σ_{u1',u2'} counts`，每 `b` 共享归一化，floor 1e-15，零额外通信，无 hard/噪声/量化/失真律/C04）；一经冻结不再更改；来源仅 `counts+bob`，spike 已验。
- **D14 errors_initial 策略**：沿用 V42/V43 严格 per-pair 跨臂等值 J6 门，先于该对解码检查，不等→`V44_EVIDENCE_INVALID`；字段 `pairing_errors_initial_equal` 仍作冗余记录。
- **D15 组合双条件路径**：替代复用 `evaluate_single_block`；单码路径、可注入 `decode_fn`；plan-review attention 项。
