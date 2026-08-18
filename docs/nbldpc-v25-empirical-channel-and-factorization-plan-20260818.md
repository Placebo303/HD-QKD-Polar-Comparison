# V25: Empirical Timestamp Channel Characterization and Multilevel Nonbinary Factorization Gate

> Frozen task packet — 2026-08-18。本文档是给 DeepSeek（实施 subagent）的冻结任务说明，
> 用于防止以下误解/错误方向：
> - 把 1024-bin 物理系统直接改成 512-bin；
> - 公开低位后只纠正高位；
> - 在 GF(512)/GF(256) 上继续盲搜 degree distribution；
> - 把 V24 的失败扩大成“所有高维 NB-LDPC 都失败”；
> - 用 QSC 或独立位面模型代替真实时间戳条件信道。
>
> 按 Ponytail lite 原则，V25 只解决“真实信道是什么、应该怎样分层”，
> 不提前实现 DE、MET、有限码或新解码器。

## 1. 任务名称

`V25: Empirical Timestamp Channel Characterization and Multilevel Nonbinary Factorization Gate`

OpenSpec change 名称（建议）：

`formal-nonbinary-ldpc-v25-empirical-timestamp-channel-and-multilevel-factorization-gate`

## 2. 总目标

对项目已有的到达时间戳、Alice/Bob 配对符号和冻结诊断证据进行系统整理，建立可审计的经验条件信道模型，并判断保留 1024-bin 高维原始符号、但使用 GF(512)、GF(256)、GF(32)、GF(16) 或 GF(8) 分层 NB-LDPC 是否具备信息论和信道结构上的合理性。

V25 只回答：

1. Alice/Bob 到达时间符号错误遵循什么规律？
2. 过去使用的 QSC、独立 Gray 位面和 translation-averaged 模型丢失了什么结构？
3. GF(1024) 原始符号应该如何可逆分层？
4. 哪种分层值得进入下一阶段 DE？
5. GF(512)/GF(256) 是否应该作为主要候选，还是仅作为对照？
6. delay、source、bin boundary、parity、jitter 和 accidentals 分别产生了什么影响？

V25 不得宣称：

- 已经得到可用 NB-LDPC；
- 已经满足 FER；
- 已经达到 \(f\leq1.3\)；
- GF(512) 或 GF(256) 已被证明可收敛；
- 已完成 qualification 或 promotion。

## 3. 冻结科学背景

必须在 proposal、design、report 中明确记录：

1. V24 只排除了：
   > 在冻结的 V17 聚合信道模型、GF(1024)、bounded single-edge λ/ρ 搜索空间内，没有找到满足预注册 DE 门的候选。
2. V24 没有排除：
   - GF(512)；
   - GF(256)；
   - multilevel NB-LDPC；
   - source-conditioned 信道；
   - Bob-full-side-information 分层解码；
   - local/global 混合图码；
   - true protograph/MET；
   - 重新校准 delay 后的经验信道。
3. V19 只说明“公开 LSB”会恶化泄漏账本。它没有测试所有低位也被编码的 multilevel reconciliation。
4. 现有 q512 probe 只有极小诊断预算，不能作为 GF(512) 不可行的证据。
5. V17 的联合信道是十个 Gray 位面边缘 BER 的 product-of-marginals，不是从完整 \(P(A\mid B)\) 拟合得到的经验联合信道。

## 4. 必须使用的数学定义

### 4.1 原始符号

\[
A\in\{0,\ldots,1023\}
\]
为 Alice 在一个 frame 内的原始 time-bin symbol。

\[
B\in\{0,\ldots,1023\}
\]
为 Bob 的完整 10-bit time-bin observation。

这里的 1024 表示原始物理高维字母表。后续分层不得改变这一事实。

### 4.2 条件元数据

\[
Z=(\text{source},\text{file},\text{acquisition block},
\text{bin width},\text{delay setting},\text{boundary class},\ldots)
\]

只有当 \(Z\) 是 Alice 和 Bob 都已知的公共实验配置，或能由公共数据确定时，才允许解码器使用 \(Z\)。

不得让解码器访问：

- Alice 真值；
- holdout 上拟合的参数；
- 未公开的 source 标签；
- 根据解码成功与否事后选择的模型。

### 4.3 经验信道

主要解码信道定义为：

\[
P(A\mid B,Z)
\]

而不是仅使用：

\[
P(A-B)
\]

也不是使用一个 q-ary symmetric crossover probability。

同时可以计算以下诊断量，但不能混为一谈：

- signed natural-bin offset：\(\Delta_{\mathrm{signed}}=A-B\)
- modular offset：\(\Delta_{\mathrm{mod}}=(A-B)\bmod 1024\)
- binary/Gray XOR mask：\(M=L(A)\oplus L(B)\)，其中 \(L\) 是指定的 symbol labeling。

### 4.4 条件熵

经验信息论下界为：

\[
H(A\mid B,Z)
\]

所有 reconciliation leakage 都必须归一化为“每个原始 1024-bin 符号的公开 bit 数”。

效率定义为：

\[
f=\frac{\mathrm{leak}_{\mathrm{IR}}}{H(A\mid B,Z)}
\]

不得只计算高位层的泄漏而忽略 residual 层。

## 5. “分层”与“物理降维”的区别

必须在文档中单独解释这两个实验。

### 5.1 编码分层

编码分层保持原始 200 ps bin 和 1024-bin frame 不变，只对原始符号标签作可逆分解。

例如 GF(512)+GF(2)：

\[
C=\left\lfloor A/2\right\rfloor,\qquad R=A\bmod 2
\]

其中 \(C\in\{0,\ldots,511\}\) 作为 GF(512) 层，\(R\in\{0,1\}\) 作为 binary residual 层，原始符号可由 \(A=2C+R\) 精确恢复。

GF(256)+GF(4)：

\[
C=\left\lfloor A/4\right\rfloor,\qquad R=A\bmod4
\]
恢复公式 \(A=4C+R\)。

这不是 GF(1024) 与 GF(512)×GF(2) 的有限域同构，而是原始 10-bit 标签的可逆分块。每个分层使用自己的有限域运算。

### 5.2 物理 bin 合并

把原始时间戳从 200 ps 重新物化成 400 ps 或 800 ps bin，会改变物理字母表、bin 数量、symbol pairing、边界位置、SER、每帧潜在原始信息量。它只能作为单独的物理粗粒化对照，不能与编码分层混写。

若执行该对照，必须：
- 使用同一份原始 `.ttbin`；
- 保持相同的 204.8 ns frame period；
- 保持锁定的 delay anchor；
- 分别物化 200/400/800 ps；
- 写入新的 additive output root；
- 不覆盖已有 pairs 或结果。

V25 默认不授权运行重型 raw pipeline。如果需要重新读取 `.ttbin`，应先提交精确输入、命令、预计资源和输出目录，等待主线程授权。

## 6. 候选分层

只评估以下预注册候选，不允许任意扩张组合：

| ID | 位宽分解 | 纠错层 |
|---|---:|---|
| F01 | 9+1 | GF(512)+GF(2) |
| F02 | 8+2 | GF(256)+GF(4) |
| F03 | 5+5 | GF(32)+GF(32) |
| F04 | 4+4+2 | GF(16)+GF(16)+GF(4) |
| F05 | 3+3+3+1 | GF(8)×3+GF(2) |

其中：
- F01、F02 是主要高维候选；
- F03 是复杂度明显较低的非二元对照；
- F04、F05 是文献优先的中小域对照；
- 不允许因为 F01/F02 域更大就默认它们更好；
- 不允许因为 F04/F05 域较小就称其为“非高维 QKD”。

物理源始终是 1024-bin 高维源。

## 7. Symbol labeling

只允许比较两个预注册 labeling：

### L01：Natural labeling
\[
L_N(A)=A
\]
保留物理 time-bin 的自然顺序，适合分析 signed ±1 和 coarse/residual 边界。

### L02：Binary-reflected Gray labeling
\[
L_G(A)=A\oplus(A\gg1)
\]
使相邻自然整数通常只改变一个 Gray bit，适合研究局部 jitter 如何分布到各层。

每种 factorization 都必须分别报告 natural 和 Gray labeling。

不得在 holdout 结果出来后发明第三种 mapping。若未来需要优化 mapping，必须另开 change。

## 8. 分层条件信道

对于分层 \(A\leftrightarrow(U_1,\ldots,U_m)\) 必须验证 chain rule：

\[
H(A\mid B,Z)=\sum_{i=1}^{m}H(U_i\mid B,Z,U_1,\ldots,U_{i-1})
\]

关键要求：
1. Bob 的输入必须保留完整 \(B\)，不能只保留 Bob 的 coarse layer。
2. 解码第 \(i\) 层时，只能使用 Bob 完整观测 \(B\)、公共元数据 \(Z\)、以及已经由 Bob-only 解码得到并通过验证的前层。
3. residual 层不能直接公开。
4. 每层 syndrome 都要进入总 leakage。
5. 分层不会降低 Shannon 极限总熵；它的作用是把一个难以设计的 GF(1024) 解码问题，变成若干更容易设计的条件 NB-LDPC 问题。

禁止写出“GF(256) 的 coarse conditional entropy 更低，所以总泄漏必然更低”。coarse entropy 降低的部分会进入 residual entropy。

## 9. 数据角色与切分

### 9.1 D01
D01/V17 可用于冻结 aggregate 对照、核对 SER、核对十个位面 BER、核对历史 entropy 数值。不得用于重建完整 \(P(A\mid B)\)，因为原证据包没有保存原始 joint arrays。

### 9.2 Legacy pairs
已有 timestamp-derived legacy pairs 可用于 characterization、channel-model comparison、factorization gate、source drift 分析。不得用于 fresh qualification、promotion、最终 FER 声明。

### 9.3 数据切分
每个 source/file 内按时间顺序切分：
- 前 60% frame：characterization/train；
- 中间 20% frame：validation/model selection；
- 后 20% frame：sealed holdout。

禁止：随机拆 symbol；同一 frame 同时进入 train 和 holdout；在 holdout 上估计 delay；根据 holdout 表现重新选择 mapping；将三个 source 先混合再随机切分。

如果某个文件 frame 太少，必须报告并停止该 source 的正式 gate，而不是静默改变比例。

## 10. 执行阶段

### P0：只读状态和输入审计
必须先读取 `AGENTS.md`、`AGENT_PROJECT_MEMORY.md`、`CURRENT_TASK.md`、`AGENT_HANDOFF.md`、`docs/decision-log.md`、V17–V24 相关 evidence/report/archive、pairs build manifest、sidecar metadata、数据源 provenance。

使用受限搜索（示例）：
```powershell
rg --files comparison_bench/outputs_comparison/nonbinary_diagnostics |
    rg "pairs\.parquet|build_manifest\.json|channel_diagnostics\.json|audit_report\.json"
rg --files openspec |
    rg "v17_multibit_channel_model\.json|lsb_public_capacity\.json|v24.*summary|tasks\.md"
```

输出 `data_inventory.json`，至少包含文件路径、source ID、acquisition 时间、frame 数、symbol 数、bin width、frame period、delay、pairing 规则、provenance、数据角色、是否允许 train/holdout/qualification。

本阶段不修改代码、不运行 DE、不读取重型原始数据。

### P1：OpenSpec 冻结
创建 V25 的 proposal.md / design.md / tasks.md / delta spec。OpenSpec 必须冻结上述定义、输入清单、数据切分、factorization、labeling、输出 schema、gate、禁止事项、失败终态。OpenSpec 未经独立 review ACCEPT 前，不得开始实现。

### M0：时间戳误差图谱
按 source、file、time block 分别计算：raw SER、signed delta histogram、modular delta histogram、\(|\Delta|\) 分位数、\(-1,0,+1\) 质量、正负偏移不对称、symbol parity、coarse-bin boundary crossing、frame boundary、Gray error-mask、Gray mask popcount、位面共同错误矩阵、error run-length、相邻 frame/error autocorrelation、随时间的 delay drift、occupancy/count-rate 分层。

run-length 不得跨越 source、file 或 frame 边界。必须将旧错误实现与 corrected 实现区分，不能重新引用已知错误的旧 run count。

### M1：信道模型比较
至少构建 C01 QSC baseline、C02 V17 independent Gray-plane product、C03 pooled additive signed-delta model、C04 source-conditioned delta model、C05 source+parity/boundary-conditioned model、C06 local-jitter+global-background mixture。

完整 sparse \(N[A,B]\) 和 \(P(A\mid B,Z)\) 作为经验描述产物保留；如果 predictive NLL 需要 smoothing，必须在 OpenSpec 中预注册 smoothing/backoff，不能事后调整。

每个模型在 validation 和 sealed holdout 上报告 negative log-likelihood、conditional entropy、calibration、zero-probability count、每个 source 的独立结果；pooled 结果仅作为补充，不得只报告 pooled average。

### M2：delay/alignment 门
对每个 source：只用 train 数据估计 delay；锁死 delay；在 validation/holdout 上计算 signed delta；比较校准前后 SER、±1 mass、offset sign、conditional entropy、time drift。

如果单向 ±1 在 delay 修正后大幅消失，应首先把它归类为 calibration/materialization 问题，而不是编码信道。如果不同 source 需要不同 delay，必须记录 source-dependent calibration；不得将其平均成一个全局参数。

### M3：multilevel factorization gate
对 F01–F05 和 L01–L02：
1. 用 train 数据确定分层解码顺序；
2. 顺序选择规则必须固定：每一步从尚未选择的层中，选择当前条件熵最小者；tie 使用固定 layer ID；
3. 在 validation 上选择候选；
4. 锁死后在 holdout 上验证；
5. 计算每层 \(H_i=H(U_i\mid B,Z,U_{<i})\)；
6. 验证
   \(\left|H(A\mid B,Z)-\sum_iH_i\right|\)
   使用同一联合计数器和同一 estimator 时应在浮点误差范围内闭合；
7. 对宽度 \(a_i\) 的 GF(\(2^{a_i}\)) 层，报告参考目标码率
   \(R_{i,\mathrm{ref}}=1-\frac{1.3H_i}{a_i}\)
   该值只是 \(f=1.3\) 下的信息论参考，不代表 DE 可达；
8. 报告复杂度代理：field size、每条消息长度、每次 check update 的 \(Q\log Q\) 级别、层数、需要的独立 parity-check matrix 数量、条件概率表规模。

### M4：架构选择
只允许以下终态：

- `pass_ready_for_de_change`：必须同时满足经验 structured model 在各 source holdout 上优于 QSC 和 V17 product；delay 和 source 规律已被区分；chain rule 闭合；所有 residual 都纳入纠错和 leakage；至少一个 factorization 具有稳定条件信道；可以给出每层冻结的 channel initialization；没有使用 Alice oracle；没有使用 holdout 调参。
- `fail_no_stable_factorization`：现有数据上没有稳定、可迁移的分层结构。
- `blocked_insufficient_joint_data`：D01 无 raw arrays，legacy 数据不足以支持下一阶段，需要 fresh timestamp/pairs。
- `blocked_alignment_unresolved`：主要误差仍无法与 delay/materialization 问题分离。

V25 PASS 仅允许提出 V26，不得自动启动 V26。

## 11. 输出文件

使用新的 additive output root，例如：

```text
comparison_bench/outputs_comparison/nonbinary_diagnostics/
  nbldpc_v25_YYYYMMDD/
    run_<timestamp>/
```

最少输出：

```text
data_inventory.json
split_manifest.json
channel_summary.json
delta_by_source.csv
gray_joint_masks.csv
channel_counts.npz
model_holdout_scores.csv
factorization_layers.csv
chain_rule_check.json
alignment_report.json
gate_summary.json
readonly_verify.json
```

以及：

```text
docs/nbldpc-v25-empirical-channel-and-factorization-report-YYYYMMDD.md
```

不需要增加 checksum manifest、原子写入框架、数据库、cache framework、并发执行框架、自动重试、新的通用抽象层。

## 12. 最小测试与独立验证

至少测试 T01–T12：

- T01：natural/Gray labeling 可逆；
- T02：F01–F05 分层可逆；
- T03：所有分层重构回原始 0–1023；
- T04：train/validation/holdout 无 frame 重叠；
- T05：signed delta 与 modular delta 不混淆；
- T06：run 不跨文件/frame；
- T07：chain rule 在 tiny synthetic joint table 上闭合；
- T08：公开 residual 会增加 leakage 的负例；
- T09：Bob-full 与 Bob-coarse 条件信道不可混用；
- T10：Alice oracle 访问检测；
- T11：holdout 参数不可回写 train model；
- T12：输出 verifier 从原始统计重算 terminal gate。

独立 verifier 必须：只读、不调用生产执行器、不修改 evidence、从 counts 和 frozen config 重算主要指标、重算 terminal state、输出 ok=true/false 和具体问题列表。

## 13. 禁止事项

未经新授权，禁止：
- 运行 V24 搜索；
- 扩大 λ/ρ 搜索；
- 实现 true MET；
- 实现有限长度 NB-LDPC；
- 报告 FER；
- 运行 fresh qualification；
- 公开 residual/LSB；
- 把 q512/q256 coarse SER 当成总 reconciliation FER；
- 使用 Alice 真值选择候选；
- 用 holdout 选择 mapping；
- 修改冻结 Polar baseline；
- 运行 `experiments/run_e2e_pipeline.py`；
- 运行任何 `longrun_*`、`minrerun_*`、`routeA_*`；
- 覆盖已有 outputs；
- push。

## 14. 验收报告格式

DeepSeek 每轮只报告：
1. 本轮完成的 task ID；
2. 修改文件；
3. 执行命令；
4. 测试结果；
5. 新建输出；
6. 是否触及禁止目录；
7. 当前 gate；
8. 剩余任务；
9. 如阻塞：精确命令、精确错误、已尝试措施、只请求一个必要决策。

不得用“基本完成”“结果看起来不错”“应该可行”等模糊表述。

## 文献与任务对应关系

| 文献 | 支持本任务的内容 | 不允许外推的内容 |
|---|---|---|
| [Mitra et al., 2024](https://doi.org/10.1007/s11128-024-04343-8) | NB-MLC(a)、较小非二元域分层、前层作为侧信息、channel-informed code design | 不证明本项目 GF512/GF256 必然成功；其主要实验不是当前 10-bit V17 信道 |
| [Zhou et al., 2013](https://doi.org/10.1109/ITA.2013.6502993) | 大字母表/time-bin secret-key 分层、mapping、multistage decoding | 主要是 binary layers，不等同于已实现 NB-LDPC |
| [Yang et al., 2019/2020](https://arxiv.org/abs/2001.00611) | ET-QKD 的 local jitter + global background、channel-informed local/global graph | GF32 仿真增益不能直接作为本项目预期 |
| [Müller et al., 2024](https://doi.org/10.1007/s11128-024-04395-w) | 高维符号映射到更低但仍非二元的符号；GF4/GF8 NB-LDPC | 使用 QSC，不能替代本项目经验时间戳信道 |
| [Dupraz et al., 2015](https://doi.org/10.1109/TCOMM.2014.2382126) | 带侧信息的 NB-LDPC/Slepian–Wolf DE；每层条件信道设计 | 不是 ET-QKD 实验结果 |
| [Boutros & Soljanin, 2023](https://arxiv.org/abs/2301.00486) | 从 timing jitter 建立 transition probability 和 soft likelihood | 不能替代对本项目 timestamp 文件的经验估计 |
| [Sayir, 2014](https://arxiv.org/abs/1407.4342) | NB-LDPC 消息复杂度与 field size、truncated-message 思路 | 截断消息不保证没有性能损失 |
