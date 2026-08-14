# 非二元 LDPC V13：现有数据诊断长规划

状态：**PLAN DRAFTED / EXECUTION NOT AUTHORIZED**（2026-08-14）。

OpenSpec change：
`openspec/changes/formal-nonbinary-ldpc-v13-existing-data-diagnostics/`

本文件先把“我们现在能问什么”与“仍然不能声称什么”分开。它不是解码
执行说明，也不是新一轮参数搜索授权。P01--P07 目前只是起草，P08 独立
只读 freeze review 尚未完成；所有 D/R/I/E/A/C 项均未授权、未运行。

## 先回答：为什么现有数据够用，但又不能当 fresh evidence

V12 的 `source_partition_blocked` 并不表示手头没有数据。V12 重建出的
10 dB 池有 2304 行，bw120、bw180、bw200 各 768 行；其中 bw200 也有
768 行。问题是 V12 要求四帧必须是跨 V4/V5 历史身份都没有出现过的
`sacrificed_real_canary`。这些行的 frame/payload identities 已被历史
包覆盖，因此合格的 fresh bw200 行是 0，而不是原始池大小为 0。

所以，本规划分两层看待同一批数据：

1. **作为算法诊断数据，它足够。** 768 个 bw200 行以及其他两层可以
   用来统计真实符号差分、错误位置/突发形状、bit-plane mismatch、
   QSC 先验失配、syndrome/数值轨迹，并在离线用 Alice truth 做事后
   exact-correction 检查。它们还可以支持一个小规模 development screen
   和一个历史帧审计。
2. **作为 V12 fresh canary，它不够。** “不够”不是数量不够，而是身份
   新鲜性不满足预注册合同。复用这些身份只能叫
   `diagnostic_only` / `retrospective_reuse`，不能叫 fresh canary、
   confirmation、qualification、promotion，也不能产生
   `observed_fresh_correction`。

这使得“先诊断算法、暂不重新采集”成为科学上可执行且边界诚实的路线。
如果诊断最终只达到 `ready_for_fresh_confirmation`，是否重新采集仍由用户
另开 change 决定；不会由 V13 自动启动采集。

## 已冻结的前置事实

V13 只绑定既有结果的含义，不改写任何失败：

| 事实 | V13 中的用途 | 明确不能做什么 |
|---|---|---|
| V7 R1A | 有限 GF(1024) 基线，此前其合成 p=.20/.30 canary 失败且无 real-data 证据 | 不把历史失败改成成功，不重跑同义路线 |
| V10 | `failed_ensemble`，说明冻结的 DE-PEG-FFT-QSPA ensemble gate 未过 | 不找“最接近”的 ensemble，不重开搜索 |
| V11 | `failed_coupling`，空间耦合 gate 未过 | 不重开 G1/G2/G3 或借其失败做参数调优 |
| V12 | `source_partition_blocked`，fresh 身份无法建立 | 不重开 X01/X02，不放宽排除清单 |
| binary V5 | 同一 10 dB Type-II、q=1024、Gray、256-symbol、bw120/bw180/bw200 域每层 128/128，合计 384/384；只作 frame-difficulty/control 参照 | 不复制 V5 泄漏数字、prior、matrix、模型或把 binary 成功当成 NB 必然成功 |

binary V5 的 384/384 表明这些帧并非普遍不可处理，但它不能区分“NB
接口错”“QSC prior 失配”“FFT-QSPA 数值不收敛”“finite graph/rate
不合适”等原因。V13 的目标正是把这些原因分开。

## 数据域与角色重建

### 主层与跨层顺序

P02 先从完整可追溯池、V4 transfer locks、V5 development/partition
locks、V5 sealed real frames 以及所有可发现的身份型 formal package
重建 ledger。P03 将 **bw200** 设为唯一 primary：先在 bw200 得到一个根因
判定，再按预注册规则检查 bw120/bw180。不能因为某层看起来容易就提前
改变主层或挑选候选。

### 三种互斥角色

每行只能有一个角色：

- `characterization`：只提供不解码的 channel aggregate；不用于候选
  同帧调参；
- `development`：优先从既有 V5 development 角色重建，允许用于 NB
  的诊断 development，但不变成 confirmation；
- `retrospective_audit`：优先使用此前封存的 128 个 V5 frame-identical
  real control/audit frames，用于候选冻结后的事后审计。

角色的“优先使用”不是对 V5 文件重新标注，也不是覆盖 V5 证据。ledger
需要同时记录 frame ID、payload ID、stratum、原角色、来源路径和是否能
证明 frame-identical；公共输出只保存必要身份/聚合，不复制 raw Alice/Bob
数组。如果某一行历史角色无法无歧义地恢复，直接进入
`blocked_role_ledger`，不借用、不拆分、不继续解码。

## Alice truth 与 telemetry 边界

Alice truth 只允许在两个离线位置出现：

1. 生成 aggregate 诊断（例如 SER 直方图、symbol-difference 计数、
   bit-plane mismatch、burst/run/position 计数、经验条件熵）；
2. decoder 返回后做独立的 exact equality 检查。

Alice truth 不得进入 decoder prior、停止条件、候选选择、frame 顺序、
retry、fallback 或同帧参数。公共/持久 telemetry 不保存原始 Alice/Bob
数组和逐位置 error mask。允许保存的只是必要 aggregate 与 decoder-
internal trace：

- 每次迭代 syndrome residual / check-satisfaction 的计数；
- posterior concentration 或 entropy 的聚合值；
- NaN、underflow、normalization/non-finite 计数；
- stagnation/oscillation 指示；
- status、iteration count 及 schema/version/provenance。

未来若为 V7 R1A 设计可选 diagnostic hook，必须满足：hook-off 的 decoded
word、status、iterations 与原接口逐项相同；hook-on 只能增加上述 trace，
不能改变 word、status 或 iterations。hook 等价性未证明前，不得做真实
decode。

## 分阶段长计划

| 阶段 | 目的与冻结内容 | 当前状态/授权 |
|---|---|---|
| **P** 规划与角色冻结 | P01 绑定事实；P02 ledger；P03 bw200 primary；P04 互斥角色；P05 telemetry/Alice 边界；P06 资源/输出/停止；P07 根因表；P08 独立只读 freeze review | P01-P07 已起草；P08 待审，未授权执行 |
| **D** 诊断 | D01 无 decode channel characterization；D02 tiny engineering oracle；D03 hook equivalence；先完成 DT0/DT1/DT2 诊断工程测试，再由 D04 对 32 个 bw200 development frame 做 unchanged V7 R1A p=.20 baseline 一次；D05 根因报告+独立复核 | P08 与 DT0-DT2 通过后才可申请；本轮未授权 |
| **R** 根因后单因素候选 | R1 prior-only、R2 decoder-only、R3 code-only，三者最多选一个 | D05 前禁止；mixed/inconclusive 时停回 planner |
| **I** 最小实现 | 只改 `comparison_bench/`，实现唯一候选与诊断接口；随后完成 IT0/IT1/IT2/IT3 | 仅计划 |
| **E** development screen | 64 个冻结 bw200 development frames；baseline 与唯一 candidate 各一次；至少 1/64 exact-correct 才能继续 | 仅计划 |
| **A** retrospective audit | 128 个 frame-identical V5 control/audit frames；bw200 先过，才可跨层检查 | 仅计划 |
| **C** closeout | 独立 acceptance、memory triage、由用户决定是否另开 fresh-acquisition change | 仅计划 |

### P 阶段的冻结点

P08 是本 change 的唯一 Decision Requested：请独立 reviewer 只读检查
P01-P07 的事实、角色、边界、artifact、门槛和停止规则。通过 P08 不代表
可以解码；它只允许主线程随后另行申请 D 阶段。

### D 阶段的最小诊断

**D01：无解码 channel characterization。** 记录 raw SER 分布、GF symbol
difference 分布、bit-plane mismatch、burst/run/position aggregate、
QSC `p=.20` calibration/NLL mismatch，以及经验条件熵/必要泄漏下界。
这些是经验诊断，不能写成 Shannon capacity 或 finite-length proof。
对冻结 V7 R1A 图的只读结构性短环/girth 分析可作为 D01 邻近证据离线计算，
用于支撑 `code` 根因行；它不改变任何 D 任务边界。

**D02：工程 oracle。** 用 noiseless、single-error、tiny q/tiny n 的小例子
验证 GF 运算、mapping、syndrome、wrapper contract 与 small-instance
exact oracle。只要 oracle 失败，就记录
`diagnosis_class=interface`、`run_state=implementation_interface_fault`，
不跑真实数据 decoder。

**D03：telemetry equivalence。** 验证 hook-off/hook-on 的行为等价和
trace schema；不记录 Alice error locations。

**DT0/DT1/DT2：D 阶段工程测试。** D04 之前必须完成三层诊断工程测试：

- **V13-DT0** compile/import、结构检查、tiny GF/syndrome math、oracle
  limit 与 D02 engineering oracle；
- **V13-DT1** role-ledger、Alice isolation、telemetry hook equivalence；
- **V13-DT2** fresh workspace 中的 complete fake diagnostic lifecycle 和
  decoder-free replay。

它们不是候选实现测试；DT0-DT2 未通过时，D04 不得申请。

**D04：不改参数的 baseline probe。** 仅在 P08、V13-DT0-DT2 通过后，从
ledger 预注册 32 个 bw200 development frames，运行 unchanged V7 R1A
`p=.20` 一次，禁止重试、替换、按结果调参。这 32 个取自 V5 development
partition（`development_partition_ranks:[128,639]` = 每层 512 帧），与 128
个封存的 frame-identical audit 帧互斥。binary V5 仅做只读 frame
identity/control 导入；不能 exact frame-identical 时必须写明
`nearest-available control`。

**D05：根因报告。** 输出两个分离字段：`diagnosis_class` 只能是
`interface`、`prior`、`decoder`、`code`、`mixed`、`inconclusive` 六类；
`run_state` 对支持单因素结论取 `diagnosis_complete`，对 mixed/证据不足
取 `diagnosis_inconclusive`。D02/oracle 失败可以在 D05 之前直接取
`run_state=implementation_interface_fault`。不得把 class 当成 state。

## 根因判别表

| diagnosis_class | 需要观察到的证据 | run_state | 允许的下一条路 |
|---|---|---|---|
| `interface` | D02 field/mapping/syndrome/wrapper 失败，或 D03 等价性失败 | `implementation_interface_fault` | 停止；修复须新 amendment+review |
| `prior` | D02 正常，数值轨迹无明显接口错，但 D01 显示 `p=.20` QSC prior 与实际 aggregate/NLL 明显失配 | `diagnosis_complete` | 仅 R1 prior-only |
| `decoder` | 固定 prior/graph 下 D02 正常，D03 显示 non-finite、normalization、stagnation、oscillation 或 schedule 问题 | `diagnosis_complete` | 仅 R2 decoder-only |
| `code` | D01/D03 与接口兼容，且对冻结 V7 R1A 图的只读结构性短环/girth 分析（离线、D01 邻近）加上冻结的 `rank=170`/`m=170` 与 rate 事实解释了 fixed-interface 失败 | `diagnosis_complete` | 仅 R3 code-only |
| `mixed` | 同时有两个或以上未能拆开的因果类别 | `diagnosis_inconclusive` | 停止；不做 mixed sweep |
| `inconclusive` | 证据不能区分因果类别 | `diagnosis_inconclusive` | 停止并返回 planner |

此表是判别规则，不是对任何一类已经成立的断言。

## R 阶段的单因素纪律

D05 之后仍需 main-thread review 和 OpenSpec amendment，才可冻结一个
候选，且最多一个：

- **R1 prior-only**：仅当 `diagnosis_class=prior` 且
  `run_state=diagnosis_complete`；matrix、schedule、check count 不变；只使用
  characterization/development 的 cross-fitted、公开 global aggregate
  形成 prior；audit truth 不可见；
- **R2 decoder-only**：仅当 `diagnosis_class=decoder` 且
  `run_state=diagnosis_complete`；matrix、prior、check count 不变；只改 D02/D03
  指向的一个数值或 schedule 机制；
- **R3 code-only**：仅当 `diagnosis_class=code` 且
  `run_state=diagnosis_complete`；prior 和 decoder interface 不变；只改一个明确的
  finite graph/rate property。

不得同时改 prior+matrix+decoder，不得重跑 V7/V10/V11 已拒绝路线的同义
版本，不得把 audit frames 变成调参集。若 D05 class 为 mixed 或
inconclusive，run_state 为 `diagnosis_inconclusive`，三条路线全部锁死。

## E/A 门槛：研究继续门，不是 promotion 门

### E01 development screen

冻结 64 个 bw200 development frames。这 64 个同样取自 V5 development
partition（`development_partition_ranks:[128,639]` = 每层 512 帧），与 D04
的 32 个合计 96 个 bw200 development frames，且与 128 个封存的
frame-identical audit 帧互斥。baseline 与唯一 candidate 各执行一
次，所有失败保留。继续门要求：

- 至少 1/64 independently exact-corrected；
- syndrome consistency；
- post-decode exact check；
- 零 forbidden/internal/accounting failures。

0/64 立即记为 `failed_existing_data_feasibility` 并停止；1/64 只代表
值得继续审计，绝不是“通过性能门”。E01 之后若过门，E02 冻结 candidate，
禁止继续调参或替换。

### A01 retrospective audit

在此前封存的 128 个 frame-identical V5 control/audit frames 上，candidate
各执行一次。baseline 是否同行执行必须事先写进计划，不能看到 candidate
结果后临时加入。建议沿用 V7 readiness 强度：

- `>=120/128` verified exact corrections；
- 零 forbidden failures；
- median `<=120 s/frame`；
- key-dependent reconciliation disclosure `<=8.75`
  bits/input-symbol，tag 单列。

未过则 `retrospective_non_ready`，停止。全过也只能是
`ready_for_fresh_confirmation`，不产生 fresh correction、qualification 或
promotion。只有 bw200 A01 过门后，A02 才能做预注册的 bw120/bw180
retrospective cross-stratum check；跨层结果不能提升状态。

## 输出、路径与测试

未来诊断输出只使用新的 additive 根：

`comparison_bench/outputs_comparison/nonbinary_diagnostics/<run_id>/`

最小 artifact 集合为：

```text
data_role_ledger.json
channel_diagnostics.json
diagnostic_outcomes.csv
decoder_telemetry.jsonl
root_cause_report.json
diagnostic_run_manifest.json
```

每个 artifact 应标记 `diagnostic_only`、`retrospective_reuse`、run_state、
diagnosis_class（适用时）、命令、时间、git commit、配置和适用的 frame
IDs；其中 `diagnostic_outcomes.csv` 必须包含 baseline、candidate
development、retrospective audit 三类行，并带 `phase`、`method` 字段。不得写
`formal_ir_methods` official qualification root，不覆盖已有输出。测试
使用新建 `workspace/nbldpc_v13_<uuid>/`，执行时采用
`pytest -p no:cacheprovider`。

诊断工程测试（D04 前）按以下顺序冻结：

- **V13-DT0** compile/import、结构检查、tiny GF/syndrome math、oracle
  limit；
- **V13-DT1** role-ledger、Alice isolation、hook equivalence；
- **V13-DT2** complete fake diagnostic lifecycle 和 decoder-free replay。

候选实现测试（E01 前）另行按以下顺序冻结：

- **V13-IT0** 候选 compile/import、结构检查和 tiny math；
- **V13-IT1** unit/boundary、Alice isolation、role-ledger、hook equivalence、
  no-overwrite、failure、telemetry tamper；
- **V13-IT2** complete fake candidate diagnostic lifecycle 和 decoder-free
  replay；
- **V13-IT3** scoped regression、冻结目录、dirty-worktree scope、官方
  输出根缺失检查。IT0-IT3 未通过时 E01 不得执行。

研究代码策略下，不设计 checksums/hash DAG、签名、原子写、锁、重试框架
或为假想环境准备的过度 schema 防御。只保留普通 Git/provenance 字段，
并在每次失败时原样保留当前 artifact。

## 状态集合与停止条件

允许的 `run_state` 只有：

`plan_only`、`blocked_role_ledger`、`implementation_interface_fault`、
`diagnosis_complete`、`diagnosis_inconclusive`、
`failed_existing_data_feasibility`、
`retrospective_non_ready`、`ready_for_fresh_confirmation`、
`invalid_diagnostic_execution`。

`diagnosis_class` 独立取 `interface`、`prior`、`decoder`、`code`、`mixed`、
`inconclusive` 六值，不能替代 run_state。

以下词在 V13 中禁止：`promoted`、`qualified`、
`observed_fresh_correction`。

出现以下任一情况立即停止并保留 evidence：角色不清、oracle/interface
失败、hook 等价性失败、Alice 信息越界、缺分母、重试/替换/覆盖、官方
输出根误写、未分类 failure，或根因证据不足。不得用“接近通过”替代
声明的状态。

## 什么时候才需要重新采集

重新采集不是 V13 诊断的前置条件。它在以下条件同时满足时才值得向用户
提出：

1. V13 沿 existing-data diagnostic 路线得到至少
   `ready_for_fresh_confirmation`；
2. 候选已按新 amendment 冻结，且没有继续调参的余地；
3. 用户确实要把结果提升为 fresh canary、confirmation、qualification
   或 promotion。

届时必须另开 OpenSpec change：新采集、新 frame/payload identities、新
partition review、新的 prepare/review/execute/verify 链。V13 不能把旧
身份“洗成”fresh，也不能因诊断全绿而自动启动采集。

## 当前交接

本轮只创建/更新规划和交接文档；没有代码、测试、输出、解码器执行、
归档或 Git stage/commit/push。当前 scientific next 是 V13-P08 独立只读
freeze review；V12 archive 是可独立决定的 housekeeping，不再阻塞 V13
plan review。P08 未通过前，V13 不进入 D04 或任何真实 decoder。
