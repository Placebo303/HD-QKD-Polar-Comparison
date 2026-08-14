# 非二元 LDPC 高维 QKD 协商路线：文献对应与长程规划调研（2026-08-14，SciVerse）

## 1. 目的与现状基准

本调研用 SciVerse 对 V13 终态（`ready_for_fresh_confirmation`）之后的规划做
文献锚定：当前方法的效率短板（f≈12.1）、先验失配（|熵差| 2.17 bits）、以及
"效率可行性先行 + 结构化先验 + 高码率码 + 降复杂度解码"的下一步，分别对应
到文献证据，并给出长程方向与落实路线。

V13 终态关键数字（本仓库实证）：

| 量 | 值 |
|---|---|
| 数据域 | q=1024（Gray，10 bit/symbol），n=256，10 dB Type-II，SER 0.077 |
| 信道结构（非 QSC） | 99.3% 非零差分 < 128；位面失配 MSB→LSB 单调 3.1e-5→3.75e-2；孤立单符号错误（92.7% run 长度 1） |
| 经验条件熵 H(diff) | 0.547 bits/symbol（QSC p=.20 模型熵 2.722） |
| V13 R3 候选 | 连通 girth-8、rate 0.336、泄漏 6.64 bits/symbol、f≈12.1（vs H） |
| V13 纠错结果 | E01 64/64、A01 128/128、A02 256/256 exact_correct（历史复用身份） |

## 2. 文献对应表

### 2.1 HD-QKD 协商效率锚点（我们的对标基线）

| 文献 | 关键数据 | 对我们的含义 |
|---|---|---|
| Müller, Bacco, Oxenløwe, Forchhammer, *Information Reconciliation for HD-QKD using Nonbinary LDPC Codes*, ISTC 2023（[DOI](https://doi.org/10.1109/istc57237.2023.10273570)、[arXiv:2305.08631](https://arxiv.org/abs/2305.08631)） | 面向 HD-QKD 的 DE 优化度分布 | V8 已复现其表 1（q=4 R=0.75 门限 0.069）；路线本身成立 |
| Müller, Ribezzo, Zahidy, Oxenløwe, Bacco, Forchhammer, *Efficient IR for HD-QKD*, Quantum Inf. Process. 2024（[DOI](https://doi.org/10.1007/s11128-024-04395-w)、[arXiv:2307.02225](https://arxiv.org/abs/2307.02225)） | **dimension 8、QBER 3–15% 时 f = 1.078–1.14**；双方法（NB-LDPC + 高维 Cascade）；明确"QKD 场景以最小化泄漏为优先、延迟次要"；建议 EMS/TEMS 做长码/吞吐 | **我们的效率目标上界**：f≈1.1 是文献实证可及的水平；但该工作假设 QSC，未覆盖我们的结构化信道 |
| Pacher, Martinez-Mateo, Duhme, Gehring, Furrer, *IR for CV-QKD using NB-LDPC Codes*（arXiv 2016） | GF(8/16/32/64)，sum-product，效率 0.94–0.98 | 非二元 LDPC 在 QKD 协商的近界效率早已确立 |
| Martínez-Mateo, Elkouss, *Efficient reconciliation of CV-QKD with multiplicatively repeated non-binary LDPC codes*, EPJ Quantum Technol. 2025（[DOI](https://doi.org/10.1140/epjqt/s40507-025-00376-9)） | **(2,k)-正则 NB-LDPC 母码 + 乘性重复**；无需码设计；天然 rate-adaptive；短块可用；硬件友好；低 SNR 区优于 MET-LDPC | **与本仓库 V7 R1A/V13 R3 同构的码族**在 2025 年被独立验证为 CV-QKD 低码率区的最优选择——我们的"母码+重复"范式有文献背书；但它是低码率方向，我们缺的是高码率方向 |
| Liu, Wu, Tang, Yu, *Shannon-limit approached IR for QKD*（arXiv 2020，polar SLA） | f = 1.055–1.091（QBER 0.02–0.1，128Mb 块） | DV-QKD 实际系统的效率标杆（大块长）；小块的有限长代价是普适约束 |
| Treeviriyanupab, Zhang, *Efficient integration of rate-adaptive reconciliation with syndrome-based error estimation and subblock confirmation*, Entropy 26(1):53, 2024 | syndrome 估计 QBER + 码率自适应 + 子块确认，BB84 吞吐达理论极限 | **落实层的协议样板**：自适应码率 + 确认子块正是我们数据域（SER 随时间波动）需要的 |
| Gao et al., *Multi-matrix error estimation and reconciliation for QKD*, Opt. Express 2019 | 多 syndrome 联合 QBER 估计 + 多码方案 | 同上：误差率估计与码率选择联合 |
| 后续工作（2025，flagged for reading）：*Performance of Cascade and LDPC Codes for IR on Industrial QKD Systems*（[IET QT, DOI](https://doi.org/10.1049/qtc2.70003)）；*Adaptation of Error Correction Procedures to the Time-Bin QKD Protocol Implementation*（[IEEE Access 2025](https://doi.org/10.1109/access.2025.3648803)） | — | 工业系统落地 + time-bin 纠错适配，与本项目真实 time-bin 数据最贴近的两篇后续 |

### 2.2 方法与工具（DE、构造、解码）

| 文献 | 关键数据 | 对我们的含义 |
|---|---|---|
| Li, Fair, Krzymień, *Density Evolution for Nonbinary LDPC Codes Under Gaussian Approximation*, IEEE TIT 2009（[DOI](https://doi.org/10.1109/tit.2008.2011435)，被引 78，FWCI 8.35） | (q-1) 维 DE 在 Gaussian 近似下可用**单参数**刻画 | q=1024 全向量 MC-DE 不可行（V9A 失败点）→ 用该降维 DE 或概率域 MC-DE 替代 |
| Cohen, Raviv, Cassuto, *LDPC Codes Over the q-ary Multi-Bit Channel*, IEEE TIT 2019（[DOI](https://doi.org/10.1109/tit.2019.2900894)、[arXiv:1706.09146](https://arxiv.org/abs/1706.09146)） | q=2^s 逐位读取信道 + **边标签优化**，有限长提升数量级 | **与我们 Gray 位面结构精确同构**——边标签/位面视角是处理 10-bit 符号的成熟路线 |
| Klinc, Ha, McLaughlin, *Optimized puncturing and shortening distributions for NB-LDPC over BEC*, Allerton 2008（[DOI](https://doi.org/10.1109/allerton.2008.4797675)，top-10%） | 精心设计的 puncture/shorten 分布可在宽码率范围保持近容量 | **高码率实现的技术锚点**：从验证过的母码向上 rate-adapt，而不是每次新设计 |
| Arabaci, Djordjević, Saunders, Marcoccia, *High-Rate Nonbinary Regular QC-LDPC Codes for Optical Communications*, JLT 2009（[DOI](https://doi.org/10.1109/jlt.2009.2029062)，FWCI 5.08） | 高码率 NB 正则 QC-LDPC + FFT 解码无中间置换 | 高码率构造 + 解码实现的现成方案（光通信领域） |
| Song, Zeng, Lin, Abdel-Ghaffar, *Algebraic Constructions of Nonbinary QC-LDPC Codes*, ISIT 2006（[DOI](https://doi.org/10.1109/isit.2006.261679)，FWCI 6.62） | 代数 NB-QC-LDPC 三族，优于同长同率 RS | 代数构造（girth/结构化）来源 |
| Liu, Zhou, Zhou, *Nonbinary multiple rate QC-LDPC codes*, JCN 2012（[DOI](https://doi.org/10.1109/jcn.2012.6292249)） | 定信息长/定块长多码率 NB-QC | 多码率族 = 自适应协商的基础 |
| Qi, Zhao, Xu, Li, *A construction of the high-rate regular QC-LDPC codes*, EURASIP JWCN 2019（[DOI](https://doi.org/10.1186/s13638-018-1325-9)） | rate 4/5–12/13 的高码率 QC-LDPC、消 6-环构造 | 高码率正则 QC 的最新构造样例 |
| Zhang et al., *Threshold Saturation for Nonbinary SC-LDPC Ensembles*, IEEE Comm. Lett. 2016（[DOI](https://doi.org/10.1109/lcomm.2016.2600662)）；Andriyanova & Graell i Amat, IEEE TIT 2016（[DOI](https://doi.org/10.1109/tit.2016.2540800)） | 非二元 SC-LDPC 阈值饱和证明 | V11 `failed_coupling` 的理论基础仍在——SC 是 B 阶段成功后的**可选**长程选项 |
| Ben Yacoub, Liva, Paolini, *Bounds on the Error Probability of Nonbinary Linear Codes over the QSC*, CISS 2021（[DOI](https://doi.org/10.1109/ciss50987.2021.9400302)） | QSC 上 ML 界与 sphere-packing 参考 | DE 门的对照基准 |
| EMS 族：Li, Gunnam, Declercq, *Trellis based EMS*, ISWCS 2011（[DOI](https://doi.org/10.1109/iswcs.2011.6125307)）；Lacruz et al., *Reduced-Complexity NB-LDPC Decoder … Trellis Min–Max*, IEEE TVLSI 2016（[DOI](https://doi.org/10.1109/tvlsi.2016.2514484)，top-10%）；Pham Thi & Lee, TVLSI 2018（[DOI](https://doi.org/10.1109/tvlsi.2017.2775646)）；Lin et al., TCSII 2016（[DOI](https://doi.org/10.1109/tcsii.2016.2534820)） | T-MM/T-EMS 在 GF(32)/GF(64) 上 1.4–1.67 Gbit/s | GF(1024) 的 EMS 文献较薄（多止于 GF(256)）；本仓库 V5-C 已有 q=1024 的 damped-FFT-QSPA + EMS 实现，可内用 |

### 2.3 信道与误差模型（time-bin 高维）

| 文献 | 关键数据 | 对我们的含义 |
|---|---|---|
| Liu, Yao, Wang, et al., *Energy-time entanglement-based DO-QKD over optical fibers*, APL 2019（被引 40） | time-bin 4 bit/coincidence，QBER 4.95%，bin sifting 抑制抖动；LDPC 纠错 β=90% | time-bin 高维实测：误差由**时序抖动/色散**主导 → 相邻时隙串扰 → 小数值符号位移——与我们"99.3% 差分<128"同构 |
| Singh et al., *Photonic quantum information with time-bins: principles and applications*, arXiv 2025 | 色散致脉冲展宽 → time-bin 正交性下降 → QBER 上升 | 相邻符号误差的物理机制背书 |
| OAM-encoded HD-QKD survey, arXiv 2025 | crosstalk 是 OAM-QKD 最主要损伤 | 高维 QKD 普遍是"相邻模式串扰"而非 QSC——**结构化先验在文献上比 QSC 假设更贴近实验** |
| Müller 2024 方法节 | 明确假设"errors are typically uncorrelated and symmetric"（QSC） | 文献主流仍用 QSC；我们的数据拒绝 QSC——这是**我们的差异化优势**（H=0.547 << QSC 模型 2.722），也是文献尚未覆盖的地带 |

## 3. 关键数字对照（可行性判断的依据）

| 量 | V13 R3 现状 | 文献目标 | 差距与含义 |
|---|---|---|---|
| 效率 f | 12.1（vs 经验 H） | 1.078–1.14（Müller 2024, q=8）；1.055（polar 大块） | 差 ~11 倍；要达到 f≈1.2 需泄漏 ≈0.66 bits/symbol |
| 校验数 m | 170 | **15–20**（n=256、q=1024） | 码率从 0.336 → 0.92–0.94，构造范式必须换（高码率 NB-QC/代数构造 + puncture） |
| 先验模型 | QSC p=.20（熵 2.72） | 结构化相邻符号模型（经验 H 0.547） | 正确先验单独一项就把"模型熵"砍 4 倍；且真实信道下 DE 目标应比 QSC 码更优 |
| 解码复杂度 | FFT-QSPA 纯 Python，median 0.9 s/帧（rate 0.336） | T-MM/T-EMS 硬件 1.4–1.67 Gbit/s（q≤64） | q=1024 的 EMS 缺文献；离线处理场景延迟次要（Müller 2024 同观点） |

**可行性的核心矛盾**：文献的效率标杆（f≈1.1）都是在 **q≤64 + QSC + 较长块**下取得的；我们的目标（q=1024 + 结构化信道 + n=256）在三个维度上同时偏离文献主流——优势是信道熵更低（潜力大），劣势是**短块有限长代价 + 高维 DE/解码复杂度**。因此"当前计划"的可行性评级是**中等偏上但必须 DE 先行**，且必须防范 V9A/V10/V11 式的"直接上码反复失败"。

## 4. 当前计划可行性评估

1. **Fresh acquisition（把 R3 推进到 fresh 确认）**：可行性**高**。不依赖新技术，纯数据/流程；仓库已有 binary V5 的 Phase-6/7 real qualification 管线可复用。风险仅在于新采集数据是否仍满足 SER≈0.077、误差结构不变——若变化，结构化先验需要 rate-adaptive 重估（Treeviriyanupab & Zhang 2024 的样板）。
2. **效率联合设计（结构化先验 + 高码率 + DE 门）**：可行性**中**。每一项都有文献方法（Cohen 2019 位面视角、Klinc 2008 puncture、Arabaci 2009 高码率 QC、Li 2009 降维 DE），但**没有任何一篇文献在 q=1024 + n=256 的组合上示范过**；这是我们的新地带。**必须以 DE/threshold 门为先**——历史上 V9A（GF(1024) MC-DE 零候选）、V10（DE-PEG 门 failed）、V11（SC 门 failed）三次失败都发生在"跳过可行性门直接构造"。
3. **EMS/T-MM 降复杂度解码（q=1024）**：可行性**中-高**。文献方法成熟但止于 q≤256；仓库内 V5-C 已有 q=1024 EMS 雏形。建议作为 B 阶段的可选项而非前置。

## 5. 长程方向（A→D）

- **A 证据完备期**：fresh acquisition change → R3 候选 fresh canary/confirmation（复用 binary V5 资格管线；新帧身份）。
- **B 效率期（核心）**：B1 冻结结构化信道模型（从修正后的 D01 聚合导出相邻符号权重，公开聚合 cross-fit）；B2 **DE 门**（q=1024 概率域 MC-DE 或 Li 2009 降维 DE，结构化模型下求 f≤1.3 的度分布/码率可行性）；B3 高码率码构造（NB-QC 代数族 + 消短环 + puncture/shorten 速率适配）；B4 解码器选择（先 FFT-QSPA 离线，后 EMS 若吞吐需要）。
- **C 部署期**：rate-adaptive 协商（syndrome 估计 QBER → 选码率 → 子块确认；Treeviriyanupab & Zhang 2024 样板）。
- **D 长程**：仅在 B 成功后考虑非二元 SC-LDPC（Zhang 2016 阈值饱和）作为再进一步的门槛路线；V11 教训：SC 必须在冻结 ensemble 之后。

## 6. 落实路线（OpenSpec 序列）

1. **V14（效率可行性门，先规划后执行）**：冻结信道模型 + DE 门定义（f≤1.3、合成根、资源/停止规则）+ 独立 freeze review；执行 DE 门一次（复用 V8-60 修正后的 QSC MC-DE 机制，扩展到结构化信道；如全向量不可行则用降维 DE 并在计划中预注册）。**门不过 = 路线冻结为"只做 fresh 确认 R3 现状"**。
2. **V15（高码率候选）**：仅在 V14 门过后：高码率 NB-QC（rate 0.92–0.94，girth≥8）+ 结构化先验 + FFT-QSPA/EMS；合成 qualification（新根、预注册、fresh canary）→ 若过，接 fresh 实数据确认（用户决定采集）。
3. **V16（部署适配，可选）**：rate-adaptive + syndrome QBER 估计 + 子块确认。
4. **Housekeeping**：V12 archive 决定（用户）；V13 archive 在用户确认 fresh 路线后归档。

## 7. 风险登记

| 风险 | 文献缓解 |
|---|---|
| q=1024 全向量 DE 不可行（V9A 前科） | Li 2009 降维；Cohen 2019 位面/边标签 DE；或先 q=64/256 分层验证再外推 |
| 短块 n=256 有限长代价大（f 目标难达） | 长块（n=512/1024）在 fresh 采集中预留；puncture 优化分布（Klinc 2008） |
| 结构化先验随信道漂移失配 | rate-adaptive 每块重估（Treeviriyanupab & Zhang 2024；Gao 2019 多 syndrome 估计） |
| 高码率 + 短环 → error floor | 代数 QC 构造消 4/6-环（Qi 2019；Song 2006）；T-MM 的 min-max 对 floor 敏感度记录 |
| EMS 在 q=1024 的性能损失未知 | 内部 V5-C q=1024 EMS + V8 的独立 oracle 先做等价性/损失验证 |

## 8. 引用完整性说明

带链接的条目为 SciVerse 检索直接返回的 DOI/URL；Pacher 2016、Liu 2020（polar
SLA）、Gao 2019、Liu 2019（DO-QKD）、Singh 2025 等条目来自 SciVerse 全文
chunk，链接未逐一核验，引用时以标题+年份+载体为准。后续深入时用
`read_content` 精读 Müller 2024 第 3–4 节与 Martínez-Mateo & Elkouss 2025
第 3 节的完整效率曲线。
