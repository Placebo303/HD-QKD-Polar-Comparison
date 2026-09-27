# HD-QKD 信息协调（IR）未来方向规划报告 — 2026-09-24

- 性质：规划报告，documentation-only（AGENTS.md §1.2 矩阵：无 track gate）。**本文件不授权任何执行**；
  其中涉及真实数据的步骤仍须走 DECIDE（compact 三文件形式即可，AGENTS §1.2 已允许）。
- 依据：本仓库 `docs/ROADMAP-20260921.md`、`docs/V80_BASELINE_20260921.md`、`docs/EXECUTION_PLAN_20260922.md`、
  `docs/NOW.md`、`docs/research_cycles/V80-NBLDPC-JAN21/`（X1 / P1 Stage-1 / S0.1 / LITERATURE_* / REALPOINT_*）、
  `docs/research_cycles/EXPLORE-20260923-DIMENSION-PROBE/FINDINGS.md`、`docs/DATA_INVENTORY_20260921.md`、git 历史；
  外部文献 12 篇（§3，其中 3 篇直接同类工作已读原文 PDF）。
- 本报告新增的唯一数值计算：§4 有限长极限（正态近似），输入为已冻结的合成信道
  `gamma_f03.npz` / `gamma_f03_pb.npz`（只读、零解码、零写盘、零 `.ttbin`），脚本见附录 A。
  它是**规划估计**，不是 FER/SKR/资格化主张。

> **2026-09-26 状态更新（覆盖下文 2026-09-24 的“尚未执行/待复算”时态）**：M0 的三源真实帧已完成；6 臂中 5 臂真实 FER 的 95% Wilson 区间高于对应合成区间，NB 结果是 **u2-only，u1 经 argmax 且正确率未验证**（`M0-REALFRAME/RESULT.md` 与独立接受）。M2 同帧 T3 的原始执行产物也已完成，但实际公开量、tag 单位、FER 单位与表中 f 不一致，真实 LB 后端不明、HDC 是 assumed-v1，**主线程科学接受 WITHHELD，D2 第三分支暂停**（`M2-REALCOMP/MAIN_ADJUDICATION_20260926.md`）；不能用它宣称三种方法族排名。M1 有限长算术独立复算为 **PASS_WITH_FINDINGS**（`M1-FINITE-LENGTH/RECOMPUTE_VERDICT.md`）：表 4.1 与 2M 表 4.2 在冻结 NPZ H 锚点下复现，n=2048 的 2M 粗估节省精算 0.056314；复算 prompt 列出的 R1 修正 H 与 NPZ H 不同，后续引用必须标注所用 H。P2 仍暂停、不取消。M3-a 嵌套 200+8 在两组固定种子下完成合成**构造可行性**门槛并经独立批末审查；后续 G-M3B-PAIRED 用这两张图与旧 P1 同 240 合成帧配对，Stage-1 非 exact 从 84/138 降至 10/15，两臂救援后均 0/240 最终失败，独立批末审查 PASS（`M3B-NESTED-PAIRED/PACKET.md` 与 `workspace/m3b_nested_paired_20260926/EXPLORATION_LOG.md`）。这仅是两实例合成诊断，不能认定一般 FER 优势或真实帧性能；按尝试计的 f 为模型值，非实际公开量。P2、P3/P4 与 M2 D2 状态不因本批改变。本段只更新证据状态，不授权执行或提升为发表主张。

---

## 0. 一页结论

1. **终点其实可以写成一张表**：Jan-21 三源（1M / 1.5M / 2M）× 三种方法（我们的 NB-LDPC / 分层二元 LDPC /
   HD-Cascade）× 四个数（f、FER、交互消息数、吞吐 sym/s），全部在**同一批真实帧**上实测。
   2026-09-24 起草时 **36 格里 0 格有真实数据**；此后 M0/M2 已产出真实帧数据，但 M2 三方法可比表的科学接受仍被暂停，完整可信的表尚未形成。
2. **三个被忽视的硬事实**：
   - 起草时 V80 解码器尚未在真实帧上运行；此后 M0 已完成三源真实帧闭环，并发现合成代理失配。
   - 真实数据**每源只有 3 秒采集**（key-eligible 超帧 200 / 276 / 364）。之前的“结构性不可认证”
     本质上是数据量问题，不是编码问题。（用户已确认不会有长采集，单点认证句永久退出主张，见 §6 M5。）
   - 吞吐应和**我们自己的源**比（口径见 §1.2(c)）：2M 源端约 3.3×10⁵ 对/s，IR 单线程约 370 符号/s，约 900 倍。
     ROADMAP 原对照“1.83 kb/s vs 6.7 kb/s（Müller 他系统采集率）≈ 3.7 倍”保留，两数分列，口径不同，不互相替代。
3. **本次新算出的关键数字（§4）**：n=1024 符号时，这个信道的有限长理论极限（正态近似，ε=1%）只有
   **f\* ≈ 1.064**（不含 tag）。我们实测约 **1.196**（2M，X1 路由门 m=204，同 ~1% FER）。拆开看：
   **码/译码差距 ≈ 0.13，有限长 ≈ 0.06，64-bit tag ≈ 0.075**。
   ⇒ 主要杠杆是**码设计**，不是加长帧（P4 的 n=2048 只能省 ≈0.02 的极限加 ≈0.04 的 tag）。
   **状态：独立复算 PASS_WITH_FINDINGS，仍只是有限长规划估计**；引用须注明所用 H 基。P2 **暂停、不取消**：P2 的 MC-DE 阈值测的是
   码集合的渐近门限，与这里的信息论有限长极限是不同的量，它能把 0.13 的码差距再拆成“集合门限”与“有限长码”两部分。
4. **诚实定位**：同维度（d=1024）的时间-能量系统，Zhong 等 2015 年用分层二元 LDPC、n=4000 符号就做到
   f≈1.17（不含 tag，Mueller 等 2024 的换算值）。我们目前约 1.20（不含 tag），**大致持平，还没领先**。
   计划里的同数据对照组“二元 MLC f=4.169”是 N=256 的保守原型，**是稻草人**，审稿人不会接受。
5. **建议的 8 周路线（§6）**：第 1 周先让真实帧闭环（M0，约 2–4 CPU 小时）；（原建议“向实验室要长采集”
   已被用户否决：采集以 3 s / 10 s 为单位，见 §6 M5 改写）；
   2–5 周补上诚实基线（M2）和码设计（M3，目标去 tag f ≤ 1.15），吞吐并行做（M4）；6–8 周写论文。
   每一步都有数值化的继续/转向规则。

---

## 1. 我们现在在哪（事实盘点）

### 1.1 科学资产（全部带作用域）

| 项 | 数值 | 作用域 / 出处 |
|---|---|---|
| 可解码性 | m=208 软边际 L2：0/240（实例 2026092001）、0/240（实例 2026092011） | 合成配对帧；两实例分报；`B2F/B2G_RESULT` |
| f_super @ m=208 | 1.2949（含 64-bit tag）；去 tag 1.2199 | 冻结口径 content=852.544 b |
| 三源路由门 m_min（≤12/240） | 2M **204**（2/240）/ 1.5M **203**（2/240）/ 1M **197**（3/240） | 合成、单实例、冻结网格；`X1_BATCH_END_REVIEW` |
| 速率自适应 200+8 | R1 f_eff 1.284（1/240）；R2 f_eff 1.275（0/240）；救援 221/222 | 合成；`P1_STAGE1_BATCH_END_REVIEW` |
| 信道结构 | 误差几乎都只翻一个 Gray 位面；有效差值字母表 11/1024；96.5% 误差 \|Δ\|<32 | V13 D01 冻结聚合；`DIMENSION-PROBE/FINDINGS` |
| 原生 GF(q) vs 逐位面二元（等披露、n=256） | FER 比 50.8× / 180.8× / 558× | 合成、特定构造与译码器；非普遍优势 |
| 真实数据用途至今 | 上述普查及 M0 三源 NB 真实帧解码；M2 三方法比较产物待科学接受 | M0 RESULT；M2 MAIN_ADJUDICATION |

### 1.2 被忽视的三个硬事实

**(a) 原真实帧闭环阻断已由 M0 解除。** 起草时 `REALPOINT_NB1024_PACKET.md` 的预算栏依赖 TIMING 探针，
而后者原本为 P4 的 PEG 构造定帽；M0 此后在独立 DECIDE 门下完成三源真实帧解码，并观察到合成代理失配。
旧 X1 / P1 的计时曾表明预算可以先行冻结；本段保留当时的依赖诊断，不再表示当前零解码。

**(b) 数据量是真正的认证瓶颈。** `DATA_INVENTORY_20260921.md`：全部 10 组采集都是约 3 s
（仅 1.12 那组实测 30 s，但因标签争议被隔离）。牺牲 60% 做先验标定后，key-eligible 只剩 200/276/364。
rule-of-three 在 A208 需要 N=2842，约相当于 60 秒采集。**用户已确认采集只有 3 s / 10 s 单位**，所以这条路不存在；
结论改为：不写单点认证句，报告带置信区间的平均 f 与 FER（§6 M5）。

**(c) 吞吐：两种口径分列（冻结口径，不互相替代）。**

| 口径 | 分子 | 分母 | 比值 | 出处 |
|---|---|---|---|---|
| **旧（ROADMAP §1.2-4，保留）** | 他系统采集 / 筛后速率 **6.7 kbit/s**（Müller 2025，**非本系统、非 SKR、非 IR 吞吐**） | 本 IR 单线程 **1.83 kb/s**（= 5120 b / 2.80 s，按每超帧 5120 bit 计） | ≈ 3.7× | ROADMAP；`LITERATURE_DIRECTION_MEMO` §2 |
| **新（本报告，自家）** | 本源端对速率 = A1 普查配对数 / 实测跨度：N = 525831 / 735780 / 982182 对，跨度约 3.0 s ⇒ **1.75 / 2.45 / 3.27 ×10⁵ 对/s**（1 对 = 1 个 10-bit ToA 符号） | 本 IR 单线程 = b2f 实测 672.6 s / 240 块 = 2.80 s / 1024 符号 ⇒ **约 366 符号/s**（合成帧、单进程、FFT-QSPA max_iter 300） | **约 480 / 670 / 900×** | A1 census；B2F_RESULT |

说明：新口径的分子是源端全部配对（部署时是否扣除标定样本另计）；分母是单线程，未计并行。
旧口径比较的是“他系统的速率”，不能说明本系统的实时性；这里只把两者并列，旧数不删、不改。

### 1.3 过程成本（git 实测，2026-08-13 起）

- 1087 次提交；文件改动计数 `.md` **3108** 次 vs `.py` **884** 次（约 3.5 : 1）；`openspec/changes` 改动 1452 次。
- V80 单个 cycle 目录 161 份文档；一个月内 4 份路线图（08-24、09-07、09-21、09-22）。
- 典型：一个只计时 PEG 构造的探针（零解码）有 8 条冻结输入 + 4 份配套文件的 packet。

这不是在批评审慎——真实数据、不可逆输出确实需要门。问题是**门的数量和科学产出不成比例**，
而且 AGENTS.md §1.1 自己已经写了：工程/审计只有在会导致错误科学结论时才能阻塞算法工作。

---

## 2. 为什么感觉像无头苍蝇：四个根因

**R1 — 优化目标是自造的内部门，而不是外部目标。**
“f_eff ≤ 1.3 且 FER 置信上界落在余量内”要求零失败且 N ≥ 2842，这在 3 秒的数据上**注定不可达**。
于是大量工作变成了围绕一个不可达门的会计推导（N_req、headroom 21.5 b vs 21.31 b 差 0.19 b……）。
G0=(B) 已经把主张改成“实测效率曲线”，但执行层面还在按旧门做决策树（P1 “FAIL(c) 差 0.19 b”）。
文献的做法：报告**平均 f 与 FER**（Müller 2025、Mueller 2024），或以密钥率为目标联合优化码率与 FER
（Mitra 2023 的目标函数是 (1−E)·R）。

**R2 — 没有闭环。** 合成→合成→合成，每一步都在回答“合成上还能否更好”，而真正决定论文的问题
“真实帧上表现如何”被 P3 → P4 → P5 串联的 DECIDE 门挡在最后。真实帧解码能直接给出
“同 (源, m, 构造) 下真实 FER 与合成是否一致”的证据；但这**不等于** P3 记忆审计通过——P3 的 T-M1..M4 仍按原门判定（见 §6 M0）。

**R3 — 对照组选错了，真正的同行不在表里。** 同类工作（§3）：Zhong 2015（d=1024，f≈1.17）、
Mitra/Tauz/Dolecek 2023–24（ET-QKD 的 NB-MLC）、Mueller/Forchhammer 2023–24（HD 的 NB-LDPC 与 HD-Cascade）。
计划中的对照组 V19 二元 MLC（f=4.169）是 N=256、保守行数的原型，它自己的文档都写着
“gap 源于保守的行数，不是概念障碍”。拿它当对照，论文的比较结论不成立。

**R4 — 过程压过科学。** 见 §1.3。每一轮的产出是“冻结的包”，不是“新测出的数”。

---

## 3. 文献告诉了我们什么（每条都落到具体含义）

| # | 文献 | 设定 | 关键数字（原文） | 对我们意味着什么 |
|---|---|---|---|---|
| L1 | Zhong et al., NJP 17, 022002 (2015) | CW 时间-能量纠缠，d=1024，SNSPD，已读原文 | 分层二元 LDPC（Zhou 等）；块长 4000 符号；β = 83.8%（N=2）到 91.2%（N=16384）；d=1024 时 SER 39.6%；7.0 Mbit/s 安全码率；“局部误差多为翻转最低位” | **最直接的同行**：同物理、同维度。Mueller 2024 换算为 f≈1.17（n=4000）。我们必须和它比；它也独立印证了“误差集中在低位面”的结构 |
| L2 | Mitra, Tauz, Sarihan, Wong, Dolecek, arXiv:2305.00956 (2023)；期刊版 QIP (2024) | ET-QKD，实验台实测信道 P(y\|x)，已读原文 | NB-MLC：把符号拆成若干 GF(2^a) 层；**a=3–4 时密钥率/时延最优**；码长 N=2000，FFT-SPA；**密钥率在 FER≈5% 处最大**；目标函数 (1−E)R；BIAWGN 上优化的度分布在 QKD 信道上反而更差 | ① 我们的 GF(32)×GF(32) 分层正是 a=5 的 NB-MLC——a 应作为扫描变量；② 用密钥率而非“零失败”作目标；③ 度分布要在**实测信道**上优化 |
| L3 | Mueller, Ribezzo, Zahidy, Oxenløwe, Bacco, Forchhammer, QIP (2024), arXiv:2307.02225 | HD-QKD，q 元对称信道 + 实验数据验证，已读原文 | NB-LDPC 集合效率 1.024–1.080（DE）；n=30000 有限长码 f 1.078–1.14；**HD-Cascade f=1.06/1.07/1.12（q=4/8/32）**，二元 Cascade 1.22/1.36/1.65；并行 HD-Cascade 每帧 239/189 条消息、FER<0.1%；用盲协调做速率自适应 | HD-Cascade 是**必须上的强基线**：效率可能比我们好，代价是交互。若它在我们数据上更好，NB-LDPC 的卖点就要改成“单向/低交互/低时延” |
| L4 | Tomamichel, Martinez-Mateo, Pacher, QIP 16 (2017) | 单向 IR 有限长基本极限 | “有限块长的实用码应当对照**该块长的基本极限**，而不是渐近极限” | 给出 §4 的方法：用正态近似估计有限长 / 码 / tag 三部分（2026-09-26 已独立复算，PASS_WITH_FINDINGS）；与 P2 的 DE 阈值互补，不替代 P2 |
| L5 | Müller et al., IET QTC (2025)（仓库已核） | 工业 BB84，n=2^16 | f_Cascade 1.036、f_LDPC 1.166；每帧消息 446 vs 3.14；f 不含 EV tag | 文献惯例 f 不含 tag ⇒ 我们对外应**并列报含 tag / 不含 tag 两个数** |
| L6 | Zhou et al., PR Applied 18, 044022 (2022)（仓库已核，arXiv-HTML） | Polar AIR，n=2^16–2^30 | f=1.046 @1 Gb；分子含 64-bit CRC | 唯一与我们 f_super 口径一致的文献；块长差 5 个数量级，只作方向参考 |
| L7 | Martínez-Mateo, Elkouss, Martín, “Blind reconciliation” (2012)；Kasai, Matsumoto, Sakaniwa, ISITA (2010) | 速率自适应 LDPC / 速率兼容 NB-LDPC | 单码多速率，少量交互换效率 | P1 的 200+8 救援是它的特例；可推广为多段小步长盲协调 |
| L8 | Poulliat, Fossorier, Declercq, IEEE TCOM 56(10) (2008) | (2,d_c) GF(q) LDPC | 用二进制像优化每行非零系数，同时改善瀑布区与错误平层 | 我们的 PEG 边标签是**随机的**（`nonbinary_v10_peg.py` 用 `label_rng`）。**假设**：优化边标签可改善瀑布区 / 平层；未验证，排在 M3-a（嵌套基修复）之后 |
| L9 | Boutros & Soljanin, arXiv:2301.00486 (2023)；Yang et al., Asilomar (2019) | 时间纠缠 QKD 的抖动信道 | 计算抖动下的密钥率并构造 IR 码；信道 = 局部（高斯）+ 全局（均匀）混合 | 信道建模参照；和我们“局部误差占 96.5%”的结构一致 |
| L10 | Liu et al., QST 9 (2022) | ET-QKD，242 km | f=1.25（q=3，n=1944，p=8%，Mueller 2024 换算） | 实验系统的现实水平参照 |
| L11 | Kanitschar & Huber, PRL 135, 010802 (2025)（仓库已核） | HD 时间/频率 bin，渐近 | 无 f/FER；H(X\|Y) 项纯经典 | 只作语境，不可作数值比较 |
| L13 | Sarihan, Chang, Chen, Cheng, Chin, Wong, CLEO (2024), doi:10.1364/cleo_at.2024.jw2a.225 | 高维到达时间 bin QKD | 用频率-偏振超纠缠消除“全局误差”，光子信息效率 +34% | 物理侧杠杆：全局（均匀）误差是 H(X\|Y) 的主要来源之一，可以作为给实验侧的建议，不属于 IR 本身 |
| L12 | GPU min-max NB-LDPC 解码（IEEE Xplore 7087640）；GF(32) ASIC（数百 Mbps） | 实现 | GPU 约 2 Mbps 量级；专用硬件 10²–10³ Mbps | 纯 Python 追不上源速率是预期内的；论文应定位为离线后处理，或给出明确的加速路径 |

**文献层面的三条结论：**
1. 高维 IR 的“新颖性”空间已经不大（Zhong 2015、Mitra 2023/24、Mueller 2023/24 都做过）。
   仍然空着的是：**CW 时间-能量 d=1024 真实数据上的端到端、完整披露会计、三方法同数据对比 + 有限长基准**。
   这与 G0=(B) 的定位一致，也是最现实的论文。
2. 效率上现实可达的目标：去 tag f ≈ 1.10–1.15（n≈10³–10⁴）。我们现在约 1.20。
3. 目标函数应当是密钥率 / 平均 f_eff（含 FER 代价），而不是“零失败认证”。

---

## 4. 本次新算的数字：有限长极限与差距分解

> **状态（2026-09-24 修订）**：本节是主线程单方算术，**尚未独立复算**。“H 与冻结值逐位一致”只说明输入读对了，
> 不说明拆分（0.132 / 0.064 / 0.075）与 n=2048 的“省约 0.057”是对的。独立复算（`reviewer-go-free`，提示词见
> `docs/research_cycles/M1-FINITE-LENGTH/RECOMPUTE_PROMPT.md`）通过前：本节只作规划估计，**不销任何冻结包**，
> P2 状态为**暂停**，不是取消。

**方法**：对冻结合成信道 P(x|y)（x = (u1,u2) ∈ 1024，y ∈ 1024），计算条件熵 H = E[−log₂P(X|Y)]
与条件信息方差 V = Var[−log₂P(X|Y)]；单向 IR 的最小披露量正态近似为
`L*(n, ε) ≈ n·H + √(n·V)·Q⁻¹(ε)`（Tomamichel 等 2017；三阶项约 ±½log₂n ≈ ±5 b，在 n=1024 时对 f 的影响 ≈ ±0.006）。
计算出的 H 与冻结值 H_L1+H_L2 **逐位一致**（0.801038 / 0.825566 / 0.832563），验证了张量轴的解读。

**表 4.1 有限长极限 f\* = L\*/(nH)（不含 tag；括号内为含 64-bit tag）**

| 源 | √V（b/符号） | n=1024, ε=1% | n=1024, ε=0.1% | n=2048, ε=1% | n=4096, ε=1% | n=16384, ε=1% |
|---|---|---|---|---|---|---|
| 1M | 0.761 | 1.069 (1.147) | 1.092 (1.170) | 1.049 (1.088) | 1.035 (1.054) | 1.017 (1.022) |
| 1.5M | 0.725 | 1.064 (1.140) | 1.085 (1.161) | 1.045 (1.083) | 1.032 (1.051) | 1.016 (1.021) |
| 2M | 0.734 | 1.064 (1.139) | 1.085 (1.160) | 1.045 (1.083) | 1.032 (1.051) | 1.016 (1.021) |

**表 4.2 差距分解（2M，n=1024，FER ≈ 1% 工作点 = X1 路由门 m=204，1020 b 综合征）**

| 分量 | 对 f 的贡献 | 等效行数（每行 5 b） |
|---|---|---|
| 熵（理想） | 1.000 | 170.5 |
| 有限长罚（ε=1%） | +0.064 | +10.9 |
| **码 / 译码器差距** | **+0.132** | **+22.6** |
| 64-bit 验证 tag | +0.075 | +12.8 |
| 合计 = 实测 f_super | 1.2715 | 216.8（=204 行 + tag） |

1M（m=197）与 1.5M（m=203）的码差距同样约 0.13（约 22 行）——三源一致，说明这是码本身的性质，不是某个源的特例。

**这张表（已独立复算，PASS_WITH_FINDINGS；仍为规划估计）对三个问题给出的判断：**
1. **ROADMAP §1.2-3“f 与 Müller 的 +0.129 缺口无法分解”**：按本估计，主体是码/译码（约 0.13），
   有限长约 0.06；引用须注明冻结 NPZ 的 H 基及近似性质。P2 的 DE 阈值还能把这 0.13 再拆成“集合门限差距”与“有限长码差距”，
   与本估计互补。
2. **P4（n=2048）值不值得作主杠杆**：按本估计 n=1024→2048 的极限约降 0.019，tag 从 0.075 降到 0.0375，
   合计约 0.057，小于码差距约 0.13 ⇒ 规划上**先做码设计**；P4 降级的依据还包括用户确认的短块 / 低时延约束（§6 M5）。
3. **P1 救援的基码有结构缺陷（2026-09-24 追加核实，只构造、零解码）**：P1 的 m=200 基码取自
   A208 构造的**前 200 行**。实测这 200 行下变量节点度分布为 `{2: 953, 1: 70, 0: 1}`——
   **70 个度为 1 的节点、1 个完全不被任何校验覆盖的节点**（A208 全 208 行时为 `{2: 1024}`）。
   这解释了 Stage-1 失败率为何高达 35% / 57.5%，且失败中 81/84、134/138 是“满足校验但译错”：
   未覆盖 / 弱覆盖符号上的错误对综合征不可见。对照：X1 的**独立构造** m=200 / 199 码失败率约 8% / 6%
   （13/163、13/203，提前停止），且几乎没有 undetected。
   ⇒ 速率自适应本身没问题，问题出在“截取前 k 行”的嵌套方式。改为**先造好基码、再增量加行**
   （速率兼容扩展）应能把 Stage-1 失败率从约 35–57% 降到约 8%，按冻结会计估算
   E[leak] ≈ 1064 + 40×0.08 ≈ 1067 b ⇒ f ≈ 1.252（含 tag）/ 1.177（去 tag），比现在的 1.275 好约 0.02。
   这是 M3 里成本最低的一项（§6 M3-a）。

**注意事项**：信道是由 TRAIN 直方图构建的无记忆模型；正态近似在 n=1024、高码率下有 O(log n / n) 误差；
这是规划用的基准线，不是可达性证明。实用短码通常离正态近似还有 0.03–0.08 的距离，
所以现实目标定为**去 tag f ≈ 1.13–1.15**，而不是 1.064。

---

## 5. 北极星与终点线

**论文主张（与 G0=(B) 一致）**：
> 在 CW 时间-能量纠缠、d=1024 到达时间编码的真实数据上，给出三种 IR 方法在同一批帧上的
> 端到端实测：效率 f（含 / 不含 tag）、FER（undetected 单列）、交互消息数、吞吐；
> 以同块长的有限长理论极限为基准，定量拆解差距来源；给出完整的披露会计。

**终点表（`NORTH_STAR` 表，每个实验必须填或收窄其中至少一格）**：

| 源 \ 方法 | NB-LDPC（本线） | 分层二元 LDPC（Zhong/Zhou 式，盲协调） | HD-Cascade（Mueller 2024） | 有限长极限 |
|---|---|---|---|---|
| 1M | f / f_notag / FER / msgs / sym/s | 同左 | 同左 | 1.069（已算） |
| 1.5M | … | … | … | 1.064（已算） |
| 2M | … | … | … | 1.064（已算） |

当前填充度：12 格有 3 格（仅极限列）。**每周复盘只问一件事：这周这张表多了几个数？**

---

## 6. 路线图（8 周，自 2026-09-24 起）

> 轨道判定按 AGENTS §1.2 矩阵。真实数据步骤均为 DECIDE，使用 compact 三文件形式
> （`PREREG_AND_AUTH.md` / `RESULT.md` / `INDEPENDENT_ACCEPTANCE.md`），不再为其建立前置依赖链。

### M0 — 真实帧闭环（第 1 周）★最高优先

- **做什么**：用**现有、已冻结**的 V80 解码链（b2f 软边际先验、v28 300/3、实例 2026092001），
  在 Jan-21 三源的 key-eligible 超帧（200 / 276 / 364，TEST 侧）上跑两个臂：
  (i) 每源 X1 路由门 m_min（1M 197 / 1.5M 203 / 2M 204）；(ii) m=208（2M）/ 各源 m_max 封顶。
  同一批帧上顺带输出两列**观测**（全 10 位一致率、每超帧误差数），零额外解码成本。
  **观测 ≠ 放行**：这两列不构成 P3 记忆审计 verdict，P3 的 T-M1..M4 仍按原门判定；
  M0 的 D1 判定只决定开发代理，任何对外句子仍须来自真实帧实测，不得引用合成 FER 冒充真实 FER。
- **成本**：840 超帧 × 2 臂 × 约 3–5 s ≈ **1.5–2.5 CPU 小时**；单次解码帽沿用 300 s；RSS < 2 GiB。
- **轨道**：DECIDE（真实数据）。可直接从已起草的 `REALPOINT_NB1024_PACKET.md` 改：删去对 TIMING 探针的
  预算依赖，预算栏填上面的实测值。
- **产出**：每源真实 FER、f_super / f_notag / f_eff、undetected 单列；**真实 vs 合成 FER 之比**。
- **决策规则 D1**：同 m 下真实 FER ≤ 2× 合成（且 95% 区间重叠）⇒ 合成信道是可信的开发代理，M3 继续在合成上迭代；
  > 2× ⇒ 记忆/漂移建模升为第一优先（逐帧自适应先验、帧级条件化）。

### M1 — 有限长基准（独立算术复算已完成）

- 把附录 A 的计算整理为一个 ≤50 行的 CLI（只读 npz，stdout 输出），并补上 ε 扫描与三阶项敏感度。
- 原规划轨道：EXPLORE（合成、无写盘）；2026-09-26 独立算术复算已给出 PASS_WITH_FINDINGS（见 `M1-FINITE-LENGTH/RECOMPUTE_VERDICT.md`）。P2 **暂停、不取消**：
  两者测的是不同的量（信息论极限 vs 集合门限），后续是否执行 P2 仍需独立路线判断。

### M2 — 诚实基线（第 1–3 周）

- **HD-Cascade**：在现有 `methods/cascade/` 上实现 Mueller 2024 的三项修改（二进制映射 + 按位分组块长 + 级联传播），
  先实现并行版（消息数可控）。约 300–500 行。
- **分层二元 LDPC**：逐 Gray 位面，用**按位面熵分配的码率**和盲协调（替换 V19 的保守行数）。
  维度探针已证明逐位面分解在信息层面只损失 0.545%——这个基线在效率上可能很强，必须认真做。
- **顺序**：先合成（EXPLORE，每方法 1 个批次），再并入 M0 后继的真实数据 DECIDE 包，同帧同会计。
- **决策规则 D2**（真实数据上）：
  - HD-Cascade 去 tag f 比 NB-LDPC 低 > 0.05 ⇒ 论文如实报告，NB-LDPC 的定位改为“单向、1 条消息、低时延”，
    并给出在给定信道时延下的密钥吞吐对比；
  - 分层二元 ≥ NB-LDPC ⇒ “高维必须用非二元码”的叙事不成立，主线转向“分层二元 + 信道建模”（更便宜、更快）。

### M3 — 码设计，挖 0.13 的码差距（第 2–5 周）

按“单位成本收益”排序，全部先在合成上做（EXPLORE），每项一个批次：

| 编号 | 动作 | 依据 | 成本 | 预期 |
|---|---|---|---|---|
| M3-a | 速率兼容嵌套：先 PEG 造好 m_base 基码，再增量加救援行（保证基码无度 ≤1 节点），替代“截取 A208 前 200 行” | §4 第 3 点（已核实 70 个度 1 节点 + 1 个未覆盖节点） | 只改构造，一次 P1 式合成批次 | 基码失败率约 35–57% → 约 8%，f 约 −0.02 |
| M3-b | 边标签优化：按 Poulliat 等 2008 为每行选非零系数（替代随机 `label_rng`） | L8 | 只改构造 | 瀑布区与平层同时改善 |
| M3-c | 非规则度分布：在**实测信道**上用现有 V26 MC-DE 内核做度分布优化，目标函数用密钥率 / f_eff | L2、L3 | ≤100 次 DE 调用 | 文献在 q-SC 上可达集合效率 1.02–1.08 |
| M3-d | 分层粒度 a 扫描：10 位符号拆成 GF(2^a) 层，a ∈ {3,4,5} | L2（a=3–4 最优）；维度探针（误差集中在低位面） | 中 | 同时降复杂度（利好 M4） |
| M3-e | 多段小步长盲协调：替换单段 +8 行 | L7 | 小 | 把平均披露压到曲线下缘 |

- **目标**：合成上 n=1024、FER ≤ 1% 时去 tag f ≤ **1.15**（2M 约 ≤ 196 行，比现在少约 8 行）。
- **决策规则 D3（第 5 周）**：M3 合计改善 < 0.03 ⇒ 接受 n=1024 上约 1.20，此时剩下的杠杆只有块长，
  P4（n=2048）重新启用；改善 ≥ 0.05 ⇒ 保持 n=1024（时延、吞吐都更好），P4 继续停放。

### M4 — 吞吐（第 1–6 周，并行）

- 先 profile 一次（现有 FFT-QSPA 的热点），再做：numba / C 化核心循环 → 帧级多进程 → EMS/T-EMS 或
  更小域（M3-d 若 a=3–4 可行，校验节点复杂度按 q² 从 1024 降到 64–256）。
- **目标**：单机实测 ≥ 10⁴ 符号/s（约为现状 30 倍）；报告与源速率 1.75–3.27×10⁵ 的剩余差距。
- **决策规则 D4**：达不到 10⁴ ⇒ 论文明确定位为离线后处理，不写“实时可用”。

> **2026-09-24 用户裁定（M5 改写）**：实验室采集以 3 s / 10 s 为单位，将来的实际实施也不会一次处理大量数据，
> **不会有 ≥60 s 的长采集**。因此：(i) 单点 `f_eff ≤ 1.3` 认证句**永久退出主张**，论文报告带置信区间的平均 f 与 FER；
> (ii) 短块长（n=1024）与低时延成为**工程约束**而不只是偏好 ⇒ P4（n=2048）进一步降级，码设计（M3）是唯一效率主杠杆；
> (iii) tag 摊销（每帧 64 b 占 f 的 0.075）在短块下更重要，列入 M3 候选；
> (iv) 若同一配置下有多次 3 s / 10 s 采集，可以作为**独立会话**分列报告（不合并），用于检验跨会话稳定性。
> 下文 M5 原稿保留为历史记录。

### M5 — 数据：向实验室要长采集（已由上方用户裁定取代）

- **请求内容**：Type2 在 1M / 1.5M / 2M 三个速率点各采 **≥ 60 s**，在**两个不同日期**各一次；
  同时保存 `run_config` / 采集日志（上游配置曾不可得，是 PM/EB 与安全章节的阻塞项）。
- **效果**：key-eligible 超帧 ×20（约 4000 / 5500 / 7300），rule-of-three 认证在 A208 需要的 2842
  变得可达；先验标定可以用另一天的数据，不再牺牲 60% 样本；跨日漂移可以直接检验（替代记忆审计的功效瓶颈）。
- 同时：查清 1.12 那组 30 s 采集的标签争议，若可解则立即多出 10 倍数据。
- 如果拿不到新数据：论文照做，报告带置信区间的平均 f 与 FER，不写单点认证句（与 G0=B 一致）。

### M6 — 论文（第 6–8 周）

- 填满 §5 的表 → DECIDE 形式的数值定稿（Pre-RESULT 独立复核）→ 撰写。
- 同类工作发表在 Quantum Information Processing（Mitra 2024、Mueller 2024、Tomamichel 2017）等期刊，可作为目标档次参考。

### 时间线

```text
周   1        2        3        4        5        6        7        8
M0  ███                                                    真实帧闭环 → D1
M1  ██                                                     有限长基准
M5  ▲请求 ···························(等实验室)···········  长采集 → 数据×20
M2      ████████████                                       HD-Cascade + 分层二元 → D2
M3          ███████████████████                            码设计 → D3
M4  ████████████████████████████████                       吞吐 → D4
M6                                   ████████████████████  定稿与写作
```

---

## 7. 停止 / 降级清单

| 项 | 处理 | 理由 |
|---|---|---|
| P2（MC-DE 阈值点 + m 扫描，≤96 DE 调用） | **暂停**（不取消） | §4 算术已独立复算；DE 阈值与有限长极限是不同的量，可能仍需要 |
| P4（n=2048）作 S3 前置 | **降级**到 D3 之后 | 块长杠杆约 0.057，码杠杆约 0.13 |
| TIMING 探针（为 P4 定帽） | **停放** | 只服务 P4；M0 的预算已有实测依据 |
| P3 记忆审计 | **暂停**；其门不变 | M0 的附带列只是观测，**不构成 P3 verdict**；T-M1..M4 仍按原门判定 |
| P1 新臂（3600 s 级） | M3 出更好的码之前不开 | 在旧码上继续救援收益有限 |
| rule-of-three 可认证性作为路由门 | 保留为报告行，**不作决策门** | 3 s 数据上不可达；G0=B 已改主张 |
| 更多会计审计（prior 成本等） | 冻结现状，论文阶段再用 | 已 RATIFIED，不影响 f |
| V19 二元 MLC（f=4.169）作同数据对照 | **替换**为 M2 的两个基线 | 稻草人 |

---

## 8. 过程建议（在 AGENTS.md 现有框架内，不削弱任何科学门）

1. **一张表驱动**：新建一页 `docs/NORTH_STAR.md`，只放 §5 的表和每格来源。每周复盘看新增了几个数。
2. **用足已有的精简形式**：DECIDE 用 compact 三文件；EXPLORE 用 packet + prompt + 一份 log + 一次 batch-end review
   （AGENTS §1.2 已允许）。不再为探针类工作起草 8 项冻结输入表。
3. **不建依赖链**：一个包只能依赖**已完成的数**，不能依赖另一个未授权的包（REALPOINT 等 TIMING 就是反例）。
4. **可度量的比例**：每两周看一次 `git log` 的 `.md` / `.py` 改动比，目标从 3.5 : 1 降到 ≤ 1.5 : 1。
5. 若要把第 2–3 条写成规则，按 AGENTS §6 走一个小的 OpenSpec change；本报告不代为修改 AGENTS.md。

---

## 9. 风险

| 风险 | 影响 | 应对 |
|---|---|---|
| 真实 FER 远差于合成（D1 走转向分支） | M3 在合成上的迭代失去意义 | 先做信道条件化 / 自适应先验；这正是早做 M0 的价值 |
| HD-Cascade 在效率上胜出 | NB-LDPC 的主卖点削弱 | 如实报告；以交互 / 时延 / 单向性定位；这个结果本身也是贡献 |
| 实验室拿不到长采集 | 单点认证句仍不可写 | G0=B 本来就不需要；报平均值与置信区间 |
| 码设计收益 < 0.03 | 效率停在约 1.20 | D3 转 P4；或接受并把重点放在测量与对比上 |
| 吞吐无法逼近源速率 | “实时”不可声称 | D4：定位为离线后处理 |

---

## 10. 需要你拍板的三件事（2026-09-24 已裁定）

- **裁定 1**：同意 M0 真实帧闭环提到最前 → 包见 `docs/research_cycles/M0-REALFRAME/`（停在执行授权前）。
- **裁定 2**：无长采集（3 s / 10 s 为单位）→ 见 §6 M5 改写。
- **裁定 3**：论文定位 = “实测 + 基准 + 三方法同数据对比”；码设计出结果后再议是否升级主张。

（以下为原提问，保留为历史记录。）

1. **是否同意把 M0（真实帧闭环）提到最前**，并把 P2 / P4 / TIMING 降级、P3 并入 M0？
   M0 是 DECIDE：同意后我按 compact 三文件形式出 `PREREG_AND_AUTH.md` + 配套 prompt，停在你的执行授权前。
2. **能否向实验室提长采集请求**（≥ 60 s × 三速率 × 两天 + 采集配置）？这是对认证与记忆问题最便宜的解法，
   只有你能发起。
3. **论文定位**：按 §5 的“实测 + 基准 + 三方法同数据对比”（与 G0=B 一致），还是坚持“新码超越文献”？
   后者需要 M3 拿到 ≥ 0.05 的改善才有底气，建议先按前者推进，M3 结果出来后再决定是否升级主张。

---

## 参考文献

1. T. Zhong, H. Zhou, R. D. Horansky, et al., “Photon-efficient quantum key distribution using time–energy entanglement with high-dimensional encoding,” New J. Phys. 17, 022002 (2015). https://iopscience.iop.org/article/10.1088/1367-2630/17/2/022002
2. D. Mitra, L. Tauz, M. C. Sarihan, C. W. Wong, L. Dolecek, “Non-Binary LDPC Code Design for Energy-Time Entanglement Quantum Key Distribution,” arXiv:2305.00956 (2023). https://arxiv.org/abs/2305.00956 ；期刊版：D. Mitra, J. Shreekumar, L. Tauz, et al., “Efficient information reconciliation in quantum key distribution systems using informed design of non-binary LDPC codes,” Quantum Inf. Process. (2024), doi:10.1007/s11128-024-04343-8. https://link.springer.com/article/10.1007/s11128-024-04343-8
3. R. Mueller, D. Ribezzo, M. Zahidy, L. K. Oxenløwe, D. Bacco, S. Forchhammer, “Efficient information reconciliation for high-dimensional quantum key distribution,” Quantum Inf. Process. (2024), doi:10.1007/s11128-024-04395-w；arXiv:2307.02225. https://arxiv.org/abs/2307.02225
4. R. Müller, D. Bacco, L. K. Oxenløwe, S. Forchhammer, “Information Reconciliation for High-Dimensional Quantum Key Distribution using Nonbinary LDPC codes,” ISTC (2023), arXiv:2305.08631. https://arxiv.org/abs/2305.08631
5. M. Tomamichel, J. Martínez-Mateo, C. Pacher, D. Elkouss, “Fundamental finite key limits for one-way information reconciliation in quantum key distribution,” Quantum Inf. Process. 16, 280 (2017), doi:10.1007/s11128-017-1709-5；arXiv:1401.5194. https://arxiv.org/abs/1401.5194
6. Müller et al., IET Quantum Communication (2025), doi:10.1049/qtc2.70003（仓库 `LITERATURE_DIRECTION_MEMO_20260921.md` 已核）。
7. H. Zhou, B.-Y. Tang, H. Chen, et al., “Appending Information Reconciliation for Quantum Key Distribution,” Phys. Rev. Applied 18, 044022 (2022)；arXiv:2204.06971. https://arxiv.org/abs/2204.06971
8. J. Martínez-Mateo, D. Elkouss, V. Martín, “Blind Reconciliation,” arXiv:1205.5729 (2012). https://arxiv.org/abs/1205.5729
9. K. Kasai, R. Matsumoto, K. Sakaniwa, “Information reconciliation for QKD with rate-compatible non-binary LDPC codes,” ISITA (2010). https://ieeexplore.ieee.org/document/5649550/
10. C. Poulliat, M. Fossorier, D. Declercq, “Design of regular (2,d_c)-LDPC codes over GF(q) using their binary images,” IEEE Trans. Commun. 56(10), 1626–1635 (2008). https://www.researchgate.net/publication/224334002_Design_of_regular_2dc-LDPC_codes_over_GFq_using_their_binary_images
11. J. J. Boutros, E. Soljanin, “Time-Entanglement QKD: Secret Key Rates and Information Reconciliation Coding,” arXiv:2301.00486 (2023). https://arxiv.org/abs/2301.00486
12. S. Yang, M. C. Sarihan, K.-C. Chang, C. W. Wong, L. Dolecek, “Efficient Information Reconciliation for Energy-Time Entanglement Quantum Key Distribution,” Asilomar (2019)；arXiv:2001.00611. https://arxiv.org/abs/2001.00611
13. J.-Y. Liu, Z. Lin, D. Liu, et al., “High-dimensional quantum key distribution using energy-time entanglement over 242 km partially deployed fiber,” Quantum Sci. Technol. 9 (2023/2024), doi:10.1088/2058-9565/acfe37. https://iopscience.iop.org/article/10.1088/2058-9565/acfe37
14. F. Kanitschar, M. Huber, PRL 135, 010802 (2025)（仓库已核，仅语境）。
15. Min-Max 非二元 LDPC 的 GPU 实现：“Efficient Min-Max nonbinary LDPC decoding on GPU,” IEEE (2014). https://ieeexplore.ieee.org/document/7087640/

16. M. C. Sarihan, K.-C. Chang, Y. Chen, X. Cheng, H.-H. Chin, C. W. Wong, “Enhancing Photon Information Capacity in High-Dimensional Arrival-time-bin QKD through Polarization Hyperentanglement,” CLEO (2024), doi:10.1364/cleo_at.2024.jw2a.225.

来源核验等级：[1][2][3] 本次直接读取原文 PDF 文本；[3][5][16] 另经 sciverse 元数据核对（[5] 作者为 Tomamichel、Martínez-Mateo、Pacher、Elkouss 四人）；[7] 读取摘要与开放全文片段；[6][14] 沿用仓库既有核验；
其余为检索元数据，仅作方向性引用，写论文前需逐篇复核。

---

## 附录 A — 有限长极限计算（可复现，只读，零写盘）

```python
import numpy as np
from statistics import NormalDist
d = "docs/research_cycles/V80-NBLDPC-JAN21/"
g, pb = np.load(d + "gamma_f03.npz"), np.load(d + "gamma_f03_pb.npz")
Qinv = lambda e: NormalDist().inv_cdf(1 - e)
for s in ["1M", "1p5M", "2M"]:
    g1 = g[f"{s}_gamma1_L1"]            # [u1, b]      = P(u1 | b)，axis0 归一
    g2 = g[f"{s}_gamma2_L2condU1"]      # [u1, u2, b]  = P(u2 | u1, b)，axis1 归一
    P = g1[:, None, :] * g2             # P(x | b)，x = (u1, u2)
    J = P * pb[f"{s}_p_b"][None, None, :]
    m = J > 0
    lp = np.zeros_like(J); lp[m] = -np.log2(P[m])
    H = (J * lp).sum(); V = (J * lp**2).sum() - H**2
    for n in (1024, 2048, 4096, 16384):
        for eps in (1e-2, 1e-3):
            L = n * H + np.sqrt(n * V) * Qinv(eps)
            print(s, n, eps, round(L / (n * H), 4), round((L + 64) / (n * H), 4))
```

H 输出与冻结的 `H_L1 + H_L2` 一致：0.801038 / 0.825566 / 0.832563（b/符号）。
