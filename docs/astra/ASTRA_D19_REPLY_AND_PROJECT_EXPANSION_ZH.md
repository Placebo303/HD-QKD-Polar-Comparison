# 对 Astra D19 审查的答复与全项目扩展说明

## 1. 对本轮审查的接受范围

我们接受 Astra 报告中的三个核心方法学判断：

1. D19 当前必须保持 STOP，不能把 4408 直接换掉后冒充原冻结总体未变。
2. 构造器准入、准入后的译码效果和部署管线可靠性必须分开记账。
3. 六张图复用八个公共区块形成交叉重复，不能把 48 个 cell 当成独立
   Bernoulli 试验。

但我们不接受把“是否采用双臂联合准入总体”提升为整个项目的唯一下一决策。
D19 是当前一个局部有限长验证门；项目最终目标是实际 HD-QKD 数据上的高性能
信息协调，包括纠错成功、实际泄漏、吞吐、资源和 accepted-frame 净产出。

## 2. 对 P0 问题的现有回答

### P0-1：目标选择

- 全项目首要目标：在实际 HD-QKD 数据上得到可复现、可核算泄漏的高性能 IR，
  最终比较 accepted-frame 净产出；不是单独最大化构造成功率，也不是单独优化
  合成 exact recovery。
- D19 的局部主目标：允许把“双臂联合准入图上的有限长译码差异”作为一个明确
  标注的条件诊断量。
- 同时必须单列构造准入率和失败类型。条件诊断不得外推为单次请求管线可靠性。
- 因此：**局部接受联合准入总体，拒绝把它当成部署总体。**

### P0-2：规则、修订和权限

- `AGENTS.md` 是仓库规则；D19 权威 readiness packet 是
  `.workbuddy/tasks/D19_L2_FINITE_ENSEMBLE_VALIDATION_READINESS_R1_TASK_PACKET.md`。
- 原 D19 冻结集合禁止 replacement/search，4408 触发的 STOP 有效。
- 任何 seed-stream、准入总体、统计量或预算变化都必须进入新的 amendment/packet，
  不能改写旧 STOP。
- 截至本答复，没有 D19 科学执行授权，也没有授权构造器重设计或 T=72 准入批次。

### P0-3：两处数值冲突的静态核对

现有代码、测试和 OpenSpec 一致给出：

```text
DV3_BASELINE_DELTA_DE = 0.5468113653656221
ELIGIBILITY_DELTA_DE  = 0.5077488653656221
ROW_STEP              = 5/128 = 0.0390625
```

因此：

- eligibility 是 baseline 减一个 `m` 行步长，即 `5/128` bit/source-symbol；
- D18 观测的 bracket midpoint 从 DV3 的 `0.546811...` 到 L020 的
  `0.351498...`，差值实际是 `25/128 = 0.1953125`；
- `EXPLORATION_LOG.md` 中把这个 midpoint 差写成 `baseline - 5/128` 是文档等式
  错误，不是代码常量；
- 同一日志出现的 `0.5077483653656221` 是转录错误。代码、测试、proposal、design、
  spec 和 readiness 使用 `0.5077488653656221`。

这次只记录诊断，不修改历史追加式证据。后续若形成 amendment，应加入显式
corrigendum，分别命名 `m/n` 行步长和 `delta=5m/n-H_L2` 差值，避免再次混淆。

### P0-4：24-cell profile

已有记录是 setup-only、零 decoder：24 个 arm-width-seed cell 中 23 个准入；
唯一失败为 n256/DV3/2026094408，原因是
`no eligible check placement at variable 255 socket 2`。n128 为 12/12，n256 为
11/12。原 profile 没有写入正式 result root；现有最接近原始证据的是 readiness、
测试中的逐 cell 断言，以及 `profile_graphs()` / `profile_only()` 的字段合同。

### P0-5：构造器边界

D19 复用接受的 D10-R2 connectivity-first PEG 构造器，不允许在 D19 内新增或
修补构造器。4408 的失败是确定性 greedy trajectory dead-end；当前证据说明它
不是 socket 算术不可能，也不足以说明度序列整体不可构造。是否需要回溯、重启
或不同 PEG tie-break，是独立构造器研究问题。

### P0-6：种子总体

D19 使用冻结的连续整数标签，不应自动解释成来自已定义概率总体的随机抽样：

- graph seeds：n128 `2026094401..4406`，n256 `2026094407..4412`；
- block seeds：n128 `2026094501..4508`，n256 `2026094511..4518`；
- coefficient namespace：
  `v10_seed("d19:l2:coeff:{width}:{arm}:{graph_seed}")`。

因此 Astra 提出的二项准入率区间只能作为新随机抽样合同下的候选设计，不能直接
套在当前连续标签列表上。

### P0-7：预算

目前没有批准 T=72，也没有已接受的 5% 构造拒绝率硬门槛。请把 24、48、72
构造检查分别作为低、中、高预算设计进行价值比较，而不是默认最大方案。
任何新预算仍需独立审查和用户授权。

## 3. 全项目审查的新中心

下一轮不要只回答“如何解除 D19”。请把项目看作以下证据链：

```text
真实/校准信道人口
  -> 条件分解和先验
  -> 码族/度分布的渐近潜力
  -> 有限图构造与 decoder
  -> 跨层消息与增量冗余
  -> 真实帧接受、误接受和实际泄漏
  -> reconciled-net yield
  -> 独立安全输入齐备后才讨论 secure yield
```

D19 位于“渐近潜力 -> 有限图”之间。即使 D19 完美解决，后面仍有跨层消息、
rate adaptation、真实数据外推、泄漏和安全输入等更高价值的不确定性。

## 4. 请求 Astra 进行的全项目问题组合

### G1 — 信道模型与人口身份是否足以支撑码设计？

审查 CAL/VAL、session/source identity、Model-F 浓度、分层熵和分布漂移。给出
“何时必须重估信道而不是继续调码”的可证伪门槛。

### G2 — 哪一种码族最值得继续投入？

比较 NB-LDPC 的 irregular/protograph/MET/rate-adaptive 路线、冻结 binary Polar
基线、binary-LDPC 邻接路线和隔离的 NB-Polar 候选。比较的是预期信息增益和到达
真实净产出的距离，不是文档成熟度。NB-LDPC 仍是当前主线，不能因为一个构造
失败自动转向 Cascade。

### G3 — DE、有限图和 decoder 之间缺少什么理论桥？

把 D17–D19 当作案例，但提出可复用的最小理论对象：ensemble threshold、
constructor-conditioned population、finite-length scaling、decoder schedule/cap 和
graph variability 分别如何进入预测。

### G4 — 跨层信息怎样转移而不重复计算？

基于 D7-E/F/G，给出 factor ownership、extrinsic/cavity 方程、tree positive
control、loopy recurrence diagnostic 和 posterior-double-counting negative control。
不要把 oracle lift 当成可实现 decoder 成功。

### G5 — rate adaptation 是否比继续找单一固定图更有价值？

研究按帧追加 syndrome/repetition/puncture/shorten 的收益，目标函数至少同时包含
accepted fraction、actual disclosure、误接受、运行时间和交互成本。说明需要什么
证据才能决定“固定码继续优化”与“增量冗余母码”之间的资源分配。

### G6 — 最小真实数据 DECIDE 实验是什么？

冻结一个 operating point，隔离 CAL/selection/confirmation，定义 attempted、exact、
protocol accepted、accepted-wrong/undetected、各类 disclosure、retained symbols、
runtime 和 per-session breakdown。不要在安全输入缺失时输出伪 SKR。

### G7 — 项目级方法选择应采用什么决策函数？

提出一个不被单一指标劫持的比较框架，至少覆盖：

```text
correction success / FER
actual leakage and beta_eff_empirical
accepted-wrong risk
accepted-frame retained yield
runtime and memory
interaction/authentication cost
model/constructor robustness
distance to real-data qualification
```

给出停止、继续、转向旁线的明确条件，以及最有价值的下一项信息，而不是生成
无限实验清单。

### G8 — 哪些复杂流程正在阻碍算法研究？

区分真正防止错误科学结论的 gate 与纯文档债。提出可以删除、合并或降频的流程，
但不得削弱 real-data、claim-bearing、undetected、leakage 和 no-overwrite 边界。

## 5. 期望返回

请输出：

1. 全项目因果图和当前最薄弱的三条边；
2. G1–G8 的逐项结论、已知/未知和关键反例；
3. 按科学价值、决策价值、成本和依赖关系排序的 Top 5；
4. 一个 3 个月研究组合：主线 70%、高风险高回报旁线 20%、基础合同 10%；
5. 明确哪些工作现在不应做；
6. 最后只给一个近期主决策，但同时说明它服务于哪一个全项目目标。

所有建议继续使用 `OBSERVED / DERIVED / PROPOSED / UNKNOWN` 标签。不得把本次
全项目审查解释为代码修改、实验执行、真实数据或发表授权。
