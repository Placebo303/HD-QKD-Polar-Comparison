# V72P2D1 后继算法路线研究

> `READ_ONLY_ALGORITHM_ROUTE_RESEARCH / EXECUTE_NOT_AUTHORIZED`
>
> 基点：`b04e575779034fb02dbcbc8a1695e1b8cf8db7db`，分支：
> `formal-ir-v72p1-addendum-clean`。本文是算法诊断与路线输入，不是
> OpenSpec 接受记录、实现授权、decoder 授权或科学 promotion 记录。
>
> 本文只记录当前仓库证据、明确标注的推断和候选方案。候选方案均为
> `PROPOSED`，不能从本文自动进入实现或真实执行。

## 1. 范围与证据等级

### VERIFIED（仓库或已落盘补证可直接核对）

- b04 补证提交保留原 V72P2D1 四个结果文件；补证命令和输入范围见
  `docs/research_cycles/V72P2D1-PARITY/OFFLINE_EVIDENCE.md`。
- 本轮算法路线探索使用固定提交树的源码、历史报告和已落盘结果进行静态
  分析；不把聊天中的自述替代仓库证据。
- b04 的 O1 补证实际读取的是 session
  `20260123_1M_600k_0dB` 的 VAL1726--1729 四个帧以及 registry，未读
  CAL；这一事实不能被概括成“补证完全未读 parquet”。本探索自身没有读取
  raw/parquet。

### INFERENCE（由 VERIFIED 证据支持，但不是已证实根因）

- 两臂均停在 Bob-oriented 的弱消息固定点，是当前最符合观测的解释：二元
  check 消息幅度相对于 prior/APP 太小，未把任何 hard bit 推离 Bob 候选。
- 该解释不等于已证明 factor dominance、代码容量极限、LDPC 类无效或某个
  单独图统计量是因果根因。

### PROPOSED（下一轮可经新计划冻结）

- 单块正交三臂、degree-role interleaving、M2 prior 对照和
  grouped-symbol mask BP 都只是后续候选；本文件不授执行。

## 2. b04 离线补证与图统计口径

OpenCode 在 b04 补证中报告并落盘了以下口径：

| 统计 | Arm A | Arm B | 状态与边界 |
|---|---:|---:|---|
| pure-H check--check `ΣC(k,2)` | 1196 | 1196 | 库内已验证；只描述二元 H |
| pure-H collision pairs | 1194 | 1194 | 库内已验证；禁止冒充 symbol rows |
| symbol-factor `ΣC(k,2)` | 8452 | 328 | workspace 离线复算值 |
| symbol/collision rows | 8170 | 326 | 外部预期，b04 workspace 未独立输出，仍非库内验证事实 |

`symbol-factor ΣC(k,2)` 将每个 check 行中的列按 `s = v // 10` 重分组；
一个 check 同时连到同一 symbol 的两个 bit 时，对该行贡献一个混合
symbol-factor/check 四环。pure-H 的 1196/1194 与该口径不同，不能互换。

因此，pure-H 统计相同只能说明二元 Tanner 图在列置换下的 check--variable
环统计相同；它不能推出固定 `sym*10+bit` 分组下的完整 factor graph 同构。
Arm B 的 parity-column permutation 改变了 bit 到 symbol 的归属，所以 A/B
在 mixed symbol-factor 口径下可能不同。

O1 为事后重构量
`O1(r) = weight(H_arm[:r] · (Alice XOR Bob))`，输入为上述四个 VAL 帧，
raw bit/symbol 错误为 3100/620。已报告的选择点为：

- `r=160`：A/B = `72/79`；
- `r=288`：A/B = `141/139`；
- `r=8992`：A/B = `4414/4422`；
- `r=9036`：A/B = `4434/4440`。

整条曲线必须标为 `POSTHOC_RECONSTRUCTED`。它不是原始 D1--D8 记录，不能
升级为图结构因果证据；b04 的 O1 也不改变原四文件或已接受的 A/B 结论。

## 3. 静态 dataflow 审查

源码：`comparison_bench/src/comparison_bench/formal_ir/`
`v72p1_soft_joint_adapter.py`；诊断 harness：
`scripts/v72p2d1_parity_layout_diagnostic.py`。

### VERIFIED：活动路径的语义检查

- `local_factor_extrinsic` 输出的是目标 bit 的 `log P(bit=1) -
  log P(bit=0)`，最终 hard decision 使用 `app_llr > 0`；LLR 方向在源码中
  是一致的。
- local factor 将目标 bit 的 bit-to-factor 项置零，满足目标 bit
  self-exclusion。
- `variable_to_check` 由 `factor_to_bit` 加其他 check-to-variable 消息，
  再减去当前 edge 的 self message；没有发现把 factor-to-bit 漏掉或重复
  加入的活动路径错误。
- check update 显式读 `syndrome_target`，并包含 syndrome 与 check-degree
  parity 的符号处理；Numba 与 Python 路径均有该语义。
- checkpoint warm-start 只在臂内携带旧 c2v，新边以零初始化；A/B 不共享
  mutable c2v 状态。
- D1 是输入 syndrome 重算一致性，不是候选 syndrome 违反数。当前周期
  没有记录候选违反数、其分位数、`sum(c2v)`、prior-only 基准或边缘增益。

### VERIFIED：实际观测

- 两臂 72 个 checkpoint 的 candidate-vs-Bob bit/symbol 差异均为 0。
- APP 最大幅度约为 `0.788--0.8004`；单边 c2v 最大幅度约为
  `0.0244--0.0263`。A/B 总迭代数为 334/321，均在迭代上限前结束为
  `LADDER_EXHAUSTED`。
- 因而当前落盘证据支持“消息没有跨过 Bob hard-decision 边界”的观察，
  但由于没有持久化全量 LLR/边消息，不能进一步声称 factor dominance。

### VERIFIED：一个与本次 D1 失败无关的接口缺陷

`run_incremental_decoder` 在末尾已经计算
`variable_to_check_final`，但返回的 `variable_to_check` 填充的是旧的
`variable_to_check_active`。这是应在未来复用该接口前修复的真实 bug；
V72P2D1 实际使用的是 `run_decoder`，所以该缺陷不能解释当前 A/B 失败，
也不应借此改写已接受结果。

## 4. mother 的 degree-role 结构

### VERIFIED

当前 9036×10240、nnz=49620 的 mother 具有：

- 前 1204 个列（信息列区）degree 10--47，均值约 `26.2035`；
- 后 9036 个列中，9035 个为 degree-2，另 1 个为 degree-1；
- check degree 为 `{4: 1, 5: 4594, 6: 4441}`。

在固定 `sym*10+bit` 分组下：

| 量 | Arm A | Arm B |
|---|---:|---:|
| 每 symbol 总边数 min/median/max | 19/20/303 | 19/20/303 |
| 总边数 `<=25` 的 symbol | 903 | 903 |
| 总边数 `>=100` 的 symbol | 121 | 121 |
| symbol-factor `ΣC(k,2)` | 8452 | 328 |

B 的 parity-column permutation 显著改变 mixed symbol-factor 碰撞，却保留了
高 degree/低 degree 角色的分组失衡。因而 A/B 同败不能检验“完整
degree-role interleaving 是否有益”。

### PROPOSED：静态 degree-balanced full-column interleaver

一次不涉及 decoder 的确定性静态试算，把前 1204 个高连接列分散到每个
symbol，使每个 symbol 获得 1 或 2 个高 degree 列。试算得到：

- 每 symbol 总边数 min/median/max = `41/47/65`；
- `<=25` 与 `>=100` 的 symbol 均为 0；
- 同 check 同 symbol 碰撞行 = 95，symbol `ΣC(k,2)` = 95。

这些数值是本次路线研究的即时静态复算，未固化脚本，也未形成可执行证据包。
这是布局候选，不是已接受母图、不是性能证据，也没有解除 V72P2D1 的
一次性执行边界。若采用，必须另立新 change，并把列映射、syndrome、
先验和输出目录全部冻结。

## 5. prior 与信息结构

### VERIFIED：两个现有 prior 参考

- V72P2/D1 使用 M0 hierarchical prior，
  `λ = 221.22162910704503`；CAL-CV CE 约 `7.1350`，VAL CE 约
  `7.1500`。其拟合/选参路径为 CAL-only，之后用全 CAL 重拟合。
- V70R1 曾有 CAL-only 选择的 M2 Laplace+uniform prior：VAL CE
  `6.7871`，CAL--VAL gap 约 `0.0393`，参数数为 4。M2 没有在 V72P2
  decoder 中测试。

### INFERENCE：为什么 bit-edge BP 可能难以自举

V70 的 1M joint CE 约为 `7.150` bit/symbol，bitwise 分解损失约
`D_bits=1.804`；对应的独立位近似总 CE 约 `8.954` bit/symbol，而当前
9036 行披露约为 `9036/1024 = 8.824` bit/symbol。

在该模型与该记账口径下，如果 decoder 实际只使用近似独立的 bit 信息，
其有效 prior 信息可能已经超过可披露 syndrome 预算；这解释了为什么
“利用 symbol 内联合相关性”是必要条件。它不是信息论 impossibility proof，
也不能单独证明当前 finite mother 已超过真实容量。

M2 的较低 VAL CE 可能改善模型失配，也可能使 Bob-oriented prior 更尖锐、
从而更难逃离当前固定点；所以只能做受控 A/B，不能从 CE 直接推断 decoder
一定改善。

## 6. 历史成功与边界

### VERIFIED

- 旧 GF32 主候选在相关同域真实数据上有 V54 development `43/45`，V64
  full-symbol verification `22/24`，且记录的 undetected 为 0；这些是实际
  成功证据，但不自动转移到当前 binary mother。
- V5-C2 的 `384/384` 属于另一条已冻结的域/方法边界，只能作历史成功
  背景，不能替代当前路线的证据。
- V67--V72P1 主要提供容量、kernel、synthetic qualification、接口和
  诊断证据；不能冒充真实纠错成功。
- V72P0 的 tiny-tree BP 与 exhaustive posterior 一致，只验证小树和
  local-factor 语义；不验证当前 loopy mother 的有限长度性能。

### INFERENCE

V72P2D1 的 0/1 单块诊断不足以淘汰 GF32，也不足以证明 binary LDPC 类
无效。当前更合理的结论是：该具体 binary edge-level flooding 组合尚未
产生能跨越 Bob 候选的消息传播。

## 7. 下一周期的正交诊断（PROPOSED，未授权）

复用已存 baseline，仅做一个固定块、一次性三臂对照；不先扩大到九块，
不把单块结果写成 FER/SKR/信息极限。

| 臂 | 仅改变的因素 | 目的 |
|---|---|---|
| L | 原 H + M0 prior + 真正 layered BP | 区分 schedule/更新顺序问题 |
| I | degree-balanced full interleaver + M0 prior + flooding | 区分 symbol 分组与 degree-role 失衡 |
| P | 原 H + 冻结 M2 prior + flooding | 区分 prior 模型与固定点锁定 |

统一逐 checkpoint 记录：

- candidate syndrome violation count；
- candidate-vs-Bob bit/symbol flips；
- `max(abs(factor_to_bit))`；
- `max_v(abs(sum(c2v incident to v)))`；
- APP margin 的固定分位数；
- iterations、residual、finite、syndrome/tag/exact verification。

### 分支停止规则

- L 只有在产生候选 escape、违反数下降或验证成功时才支持继续 layered
  路线；仅 runtime 变快不构成 FER 或 f_actual 改善。
- I 若出现明显 escape 或违反数下降，才冻结其列映射并另做图设计；一次
  单块变化不能宣称一般性结构因果。
- P 若显著改变消息/翻转但仍不验证，记录为 prior 影响并停止直接推广；
  若没有变化，则削弱“仅 prior 模型导致失败”的解释。
- 三臂都不产生 hard-bit escape 时，停止 binary edge-level 微调，进入
  grouped-symbol mask BP 的 tiny exhaustive qualification，或做同块 GF32
  对照；不继续无差别加迭代、调 damping 或扩样。

## 8. grouped-symbol mask BP（PROPOSED）

当前 bit-edge BP 将一个 symbol 拆成 10 个 bit 变量，再由 local factor
恢复联合 prior。候选替代是直接把每个 1024-state symbol 作为一个变量：

1. 对每条 binary check，收集该 check 在同一 symbol 内连接的 bit 集合，
   把它表示成一个 XOR mask；
2. 每个 `(check, symbol)` 只保留一个 scalar parity message；
3. symbol-to-check 更新使用完整 1024-state prior 与其余 mask 消息，按
   该 mask 的 parity 做边缘化；
4. check-to-symbol 仍按 binary parity SPA 组合这些 scalar messages。

朴素实现约有 41169 个 unique `(check, symbol)` group，每轮约 42M 个
state-level evaluations；这是数量级估算，不是 runtime 证据。它的价值在于
直接传播 symbol 内联合信息，并消除同一 check 内多个 bit edge 造成的
人工 factor-cycle；它仍可能受图结构和高码率限制。

最小验证顺序应是：tiny `k=2/3` exhaustive posterior → 小 loopy synthetic
对照 → 单块真实诊断。没有这些验证前，不得称其能够成功或突破容量。

## 9. 文献方向（仅方向，不构成路线接受）

- PEG：通过渐进边增长控制短环，是重新构造图时的基础候选；不保证当前
  联合信道上的 finite-length BP 成功。Primary：
  [Progressive-edge-growth Tanner graphs](https://doi.org/10.1109/TIT.2004.839541)。
- Layered BP：改变更新调度，常用于更快收敛；不能把 schedule 改善等同于
  capacity 或 FER 突破。Primary：
  [Layered decoding for LDPC codes](https://doi.org/10.1109/SIPS.2004.1363033)。
- Spatial coupling：可改变渐近阈值行为，但会引入 coupling、边界和有限长度
  代价；当前结构化信道上必须先做针对性 DE。Primary：
  [Threshold saturation via spatial coupling](https://arxiv.org/abs/1001.1826)。
- Non-binary LDPC：更自然地保留高维符号相关性，但必须使用正确的 full-vector
  channel/message 语义，不能把 q-ary 文献结果替换成当前 bit-edge 近似。Primary：
  [Efficient Information Reconciliation for High-Dimensional QKD](https://arxiv.org/abs/2305.08631)。

PEG/ACE、layered、SC 和 NB 各自解决不同问题；它们都不能脱离实际信道、
码率、finite-length 图和 decoder 验证而被表述成容量突破。

## 10. 本轮边界与当前停止状态

- 本次 algorithm-route exploration 未读取 raw/parquet 内容，未运行 decoder，
  未修改代码、既有结果或 lifecycle；仅新增本研究文档并追加一段记忆 triage。
- b04 离线 O1 补证是独立事实：它读取了已冻结的四个 VAL1726--1729 帧，
  未读 CAL，并且全程标 `POSTHOC_RECONSTRUCTED`。
- tag、Git SHA 和输出目录审计仍是生命周期正确性的必要背景，但不是解释
  当前算法失败的主要阻塞点；当前优先级应是消息传播、degree-role 分组和
  联合 prior 的可区分算法实验。
- 当前状态保持 `READ_ONLY_ALGORITHM_ROUTE_RESEARCH /
  EXECUTE_NOT_AUTHORIZED`。任何 L/I/P、interleaver、mask BP 或 GF32 对照
  均需新计划、独立 review 和明确执行授权。
