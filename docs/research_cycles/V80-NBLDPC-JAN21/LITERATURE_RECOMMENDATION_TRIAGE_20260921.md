# V80 — 外部论文推荐 vs 仓库实况的分诊（2026-09-21）

- **Track**：文档-only 调研（AGENTS.md §1.2 矩阵：Documentation-only → 无 track gate）。
  仅读已提交的仓库内容；无执行、无真实数据读取、无构造/解码、无 commit/push。
- **对象**：用户 2026-09-21 给出的 P0/P1/P2 推荐清单与「不作为核心证据」清单。
- **不主张**：无 FER/路线/S3/资质/发表/净收益结论；本文件不授权任何新的 arm 或 package。

---

## 0. 一句话结论

三条核心建议里，**#2（verification-aware λ_total）仓库早已实现且比推荐口径更严**，
**#3（rateless / 增量冗余）不仅实现过，还在真实数据上做过并判 FAIL**（最重要的负面证据），
只有 **#1（经验信道替全局 QSER）有一半没做完**：全局 QSER 早已被经验联合
\(P\) 取代，但仍是**每源池化**的一份 bundle，**逐块估计从未实现**——这是唯一真实的科学缺口。

因此这批推荐里**只有 3 篇可能改路线**：Müller 2025（指标体系，只能借方法不能借数字）、
Scarinzi 2025（正好指向我们的「池化 vs 逐块」缺口，需先核实原文）、
Tarable 2024（protograph 母结构，且必须与仓库自己的 protograph DE 负结果对读）。
其余要么已在库（Müller 2024、Tang/Liu SLA），要么属于另一条主线/外层框架（Polar、Zahidy、Ogrodnik、Kanitschar）。

---

## 1. 仓库已有证据（逐条）

| 建议项 | 仓库现状 | 关键证据 | 结论 |
|---|---|---|---|
| \(\lambda_{\text{total}}\) 里计入验证/hash | **已有** | `comparison_bench/src/comparison_bench/metrics/leakage.py:29-34`（Cascade `parity+verify_bits(=32)+extra_bits`；LDPC `syndrome+verify_bits+puncture_shortening_bits`） | 已覆盖，无需引入 |
| beta/f 只推导不手填 | **已有** | `leakage.py:42-50` `compute_beta_eff_empirical(leak, n, raw)`；AGENTS.md §5.5 | 已覆盖 |
| 失败帧/undetected 不并入成功 | **已有** | `metrics/success.py:60-80`（`verified_failure`、`decode_improved_but_unverified` 与 `real_ir_success` 分离）；`v46_verification_semantics.py` 以 `undetected_accepted_wrong==0` 为门 | 已覆盖且比推荐更严 |
| **失败帧泄漏计入平均（\(\lambda_{\text{failed frame}}\)）** | **已有（且平均到 attempted 而非 accepted）** | `formal_ir_methods/v55_two_stage_rescue_independent_test/run_01/v55_summary.json:52-64`：`overall_avg=(Σ leak_base + 40·N_stage1 + 40·N_stage2)/90 = 1167.33 bits`，`avg_disclosure_per_attempted_frame = 1.13997 bits/symbol` | 推荐口径已在库 + 已含失败帧成本 |
| tag/hash 计入分子 | **已有（冻结）** | `S2_ACCOUNTING_MAP_20260920.md:16`：`f_super=(4·(5·m)+64)/(1024·H_full)`，64-bit tag 显式入分子 | 已覆盖，且是为解决这个问题而冻结的 |
| 吞吐/资源记账 | **已有** | `metrics/throughput.py`；`metrics/summary.py:21-25` 汇总 `runtime_s`、`throughput_*_bits_per_s`、`accepted_frame_fraction` | 已覆盖 |
| 经验信道替代全局 QSER | **已做（每源池化）** | V25 counts → `load_v25_channel_counts` → Model-F 先验；V80 只读 bundle `γ1(u1\|b) (32,1024)` / `γ2(u2\|u1,b) (32,32,1024)` / `p_b`，见 `v80_s2c_campaign.py:187-198` | 建议 #1 主体已完成 |
| **逐块（per-block）信道 / 分块 QSER → 逐符号 reliability** | **未实现** | 现用 bundle 为每个 source 一份（`{source}_gamma1_L1` 等），无逐块重估；`types.py:26-27` 有 `qber_estimate/ser_estimate` 字段但 formal IR 侧未使用 | **唯一真缺口** |
| rateless / rate-adaptive / 增量冗余 | **已实现 + 已实测** | `v52/v53/v54/v55`（`formal_ir_methods/` 下均有 `run_01` 输出）；`v52_rate_adaptive_l2_rescue.py:1-13`（Δm=8 条件 HARQ，`avg=base+40·N_rescue/15`）、`v54_...rescue.py:1-8`（Δ8+8 两级） | 机制不缺 |
| ↑ 该方向在真实数据上的结果 | **FAIL** | `v55_summary.json:66-163`：`final_exact_full_count=0`，`reclassified.decoder_non_syndrome_failure=270/270`，`terminal_state=V55_INDEPENDENT_TEST_FAIL`（90 真实 held-out 块，三源各 30） | **关键负面证据**：「固定 GF32 vs rateless 并列比较」在该项目真实 held-out 块上已有否定答案（是否与 `20260123_*` 池同源未核实） |
| Polar 增量/failure probability | partial | `formal_ir_methods/v63_nbldpc_polar_shell/` 存在；Polar 正式主线在兄弟 checkout（本 checkout 仅 `methods/polar_existing.py` 冻结桥接） | 跨主线，成本高 |
| 交互轮数/消息计数 | 缺（NB 侧） | Cascade：`cascade_lite.py:279,332`（`num_passes`/`passes_used`）；NB-LDPC 侧只有 decoder iterations（b2f：7–23 iter） | 若按 Müller 2025 指标体系，这是唯一要**新增记录**的项 |

**当前活路线（对照）**：V80 b2f — 软边缘 L2 先验（Bayes 边际化，D-u1=0.0 结构/实测），
n=1024 GF(32) λ={2:1} m=208，F208 **0/240 PASS**，\(f_{super}=1.294947\le1.3\)，译码 2.77 s/块
（`B2F_RESULT_20260921.md:11-25`）；b2g（第二构造实例 2026092011）为**未授权** contingent 包。

---

## 2. 逐篇裁决

| 优先级 | 论文 | 仓库命中 | 状态 | 适用性 | 可用性 | 建议动作 |
|---|---|---|---|---|---|---|
| P0 | Müller et al. 2025, IET QTC `10.1049/qtc2.70003`（Cascade/LDPC 工业实测） | 2 处：`docs/nonbinary-ldpc-efficiency-roadmap-survey.md:33`（flagged for reading）、`docs/hd-qkd-ir-performance-roadmap-20260824.md:246`（用于「保留 R4 系统级基线及 verification/leakage 成本」）、`PROGRAM_PLAN.md:250-253`（to-read #1） | **已引用、未读、无全文/数字入库** | 高（指标体系），但**证据是二元 BSC 工业长帧**，不可外推 GF32/ToA | 需取全文（本会话未联网核实 OA 状态） | **可读**：只取「message/round 计数 + 验证成本如何入 λ」的定义，落成 V80 manifest 的 report-only 列。**禁止**引用其 f≈1.036/1.166 作为 GF32 对照 |
| P0 | Tarable et al. 2024, rateless protograph LDPC for QKD（IEEE 10418979） | 1 处：`docs/hd-qkd-ir-performance-roadmap-20260824.md:240`（引的是 IEEE TQE 博客 URL，非 DOI；与用户给的 Xplore 链接需核实同源） | **已引用、未采用** | 中：**rateless 行为我们已有**（v52/v54/v55），真正缺的是 protograph 母结构 + MET multi-edge DE | 可用，但先看下面的负结果 | **滞后读**：只有当选 n=2048 joint 路线（memo O-B/A2）时才读。必须与 decision-log V22/V23 负结果同读：q=1024 rate 0.9375 结构化信道 DE 在 plain irregular / SC-LDPC / **regular protograph / simple irregular protograph** 上均不收敛 ⇒ protograph 不是免死金牌 |
| P0 | Scarinzi et al. 2025（arXiv 2511.05196，卫星下行 inst. QBER/LLR 选码率） | **0 命中** | 全新 | 中高：它正好指向我们唯一缺口（**池化 vs 逐块**） | **原文未核实**（arXiv 编号 2511 = 2025-11；本会话未联网验证） | **唯一可能改变 S2/S3 设计的 P0**：先核实原文，再决定是否做「逐块 vs 每源池化 bundle」对比包。其 3% 增益数字不得引用（域不同、不是 ToA 实测） |
| P0 | Müller et al. 2024, QIP `10.1007/s11128-024-04395-w`（HD NB-LDPC/HD-Cascade） | 多处：V8 已复现其 Table 1（`openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/v8_muller2024_table1_extract.txt` + 4 份 acceptance/correction JSON）；`PROGRAM_PLAN.md:82-88,144-150` | **已使用、已归档（含证据）** | 已消化；其 QSC 假设不成立这件事已记录（`nonbinary-ldpc-efficiency-roadmap-survey.md:57`） | — | **无需重读**。若要刷新，只看一点：blind reconciliation 的 extra disclosure 如何计入 S2 预算（`S2_ACCOUNTING_MAP:26` 已明确要求计入） |
| P1 | Zhou et al. 2022, AIR Polar（PRApplied 18, 044022） | **0 命中** | 全新 | 低-中：只作为 Polar 低交互/低失败率对照 | 可用 | **暂不读**。Polar 正式主线在兄弟 checkout；本 checkout 只有 `polar_existing` 冻结桥接 + `v63_nbldpc_polar_shell`。仅当 Polar 臂重启时评估 |
| P1 | Tang/Liu et al., SLA IR（arXiv 2003.03713） | **已在库**：`nonbinary-ldpc-efficiency-roadmap-survey.md:30`（f=1.055–1.091，128 Mb 块） | 已使用为效率标杆 | 中：大块二元上限，非我们的设计点 | — | **无需重读**，引用时注明「大块二元」 |
| P1 | Zahidy et al. 2024, Nat Commun（多芯光纤 HD-QKD） | 0 命中（"Zahidy" 仅以 Müller 2024 合著者出现） | 未归档 | 低：只用于「系统论文的 f=1.06 是建模参数而非 IR 实测」的引用纪律 | — | **不必读**，纪律本身已符合 AGENTS.md §5.5 |
| P1 | Ogrodnik et al. 2025（resource-efficient detection） | **0 命中** | 全新 | 低：我们的经验信道已吸收 jitter/色散/损伤；只有把 **detector 资源成本**纳入净收益才用得上 | — | **推迟**（S3 之后若做资源维度再说） |
| P2 | Kanitschar & Huber 2025, PRL 135, 010802 | **0 命中** | 全新 | 中（外层）：把观测统计 → 可计算高维 key rate | 可用 | **交叉校验用**，非 IR 算法。仓库已有自有外层链：`docs/SECURITY_MODEL.md`、`tools/security_reports/*finite_key_shadow*`、beta 只推导 ⇒ 只在最终把 \(\lambda_{\text{total}}\) 换成 finite-key 净 SKR 时对账 |

### 「不作为核心证据」清单核对（重要：确认仓库未被污染）

| 项 | 仓库检索结果 | 判断 |
|---|---|---|
| 撤稿的 Mao 等 570 Mbps / f=1.038 | docs + openspec 检索 `retract/撤稿/withdrawn/Expression of Concern` = **0 命中**；"Mao" 唯一命中是 IEEE 11440984（另一篇，不同 Mao） | 未使用，**无需清理** |
| 115.8 Mbps Nature Photonics `s41566-023-01166-4` | **0 命中** | 未使用 |
| 「zero information leakage」多项式插值协调 | docs 检索 `polynomial interpolation / 零泄漏 / zero leakage` = **0 命中** | 未使用 |
| 高维系统论文里的 f=1.06/1.1 估计值 | 未作为 IR 实测引入（用户担忧的情形不存在） | 维持现有纪律即可 |

---

## 3. 建议落地顺序（只补真缺口）

1. **逐块 vs 每源池化信道**——唯一可能改 f 的科学项。先用 Scarinzi（核实后）做存在性旁证，
   再决定一个 EXPLORE 包：同一批 Jan-21 帧，`per-block 重估 γ/f_{model}` vs `pooled bundle`，
   同时记录 exact / FER / λ_total / 迭代数。**不改冻结的 \(f_{super}\) 口径**。
2. **Müller 2025 仅取记账项**：往 V80 manifest 增加 report-only 列
   （round/message 计数、验证成本归类），冻结口径与 gate 不动。
3. **Tarable 滞后**：只有当走 n=2048 joint（memo O-B/A2）时才读，与 V22/V23 protograph DE 负结果一起看。
4. **不读/延后**：AIR Polar（跨主线）、Zahidy（纪律项）、Ogrodnik（资源维度）、Kanitschar（外层对账）。
5. **保留现有正面/负面证据**：不要把 V55 的 rateless FAIL 与 V80 b2f 的 soft-marginal PASS 混为一谈——
   前者是**该项目真实 held-out 块 + 两级救援**，后者是**新设计点 + 软边缘（Bayes 边际化）先验**；
   两者不互为证据，禁止跨臂合并 FER（同源性未核实，见 §4 末条）
   （已是 V80 既有约束，见 `B2G_EXPERIMENT_PACKET_20260921.md:41`）。

---

## 4. 边界 / Does-not-establish

- §5 之前的部分：仓库内分诊，**未联网核实**。§5 为 SciVerse 原文核对结果，取代本条第 1 句对必要性的限定。
- 无执行、无真实数据读取、无 new evidence 产生；不修改任何冻结阈值、包或口径；不授权 S2/S3。
- 所有行内数字均为仓库既有产出品的转录，不是本次产生的测量结果。
- V55 的块标签为三源 `1M/1p5M/2M` 的 held-out ordinal；它是否就是 `20260123_*` 池
  （INFORMATION-CLOSURE 适用对象）**本次未核实**，因此第 3 节第 5 条只用于禁止跨臂合并，**不得**
  据此把 V55 的 FAIL 归因于 INFORMATION-CLOSURE。

---

## 5. SciVerse 原文核对（2026-09-21，追加）

手段：仅 SciVerse（`search_papers` DOI/题名精检、`semantic_search`+`read_content` 读正文 ID）。
只读外部元数据库/全文，**未触碰任何真实数据、未执行任何 decoder**。

### 5.1 核对结果总表

| 论文 | 存在性 | 权威标识符 | 全文可得 | 用户转述是否核实 | 裁决变化 |
|---|---|---|---|---|---|
| Müller 2025 IET QTC | ✅ 存在 | `10.1049/qtc2.70003`，gold OA CC-BY，fwci 3.30，2 引，77 参考文献 | ❌ 无 `doc_id`、0 chunk（检索返回的非本文） | **数字全部未核**（6.7 kbit/s、446 vs 3.14、FER<0.003、f=1.036/1.166）；摘要属实 | 维持「只借方法不借数字」 |
| Tarable 2024 | ✅ 存在 | **正式 DOI `10.1109/TQE.2024.3361810`**；用户的 Xplore 10418979 是同篇 doc-id（OA PDF 路径 `ielx7/8924785/8961200/10418979.pdf` 可证同源）；仓库引的 TQE 博客 URL 同源 | 元数据/摘要；`is_content_accessible=false` | ✅ 机制属实（check-node splitting、同 protograph 覆盖多块长） | **上调可取性一项**：他们有专门的 **protograph discretized density evolution 工具**，我们缺（V22/V23） |
| Scarinzi 2025 | ✅ 存在 | arXiv `2511.05196`（2025-11-07）；作者 Scarinzi / Orsucci / Ferrari / Barletta | ✅ **全文已读**（`doc_id 9ca78824…`） | ✅ 已核到关键句原文（下 §5.2） | **下调预期**：结论属实但块长差 ~90×，见 §5.2 |
| Müller 2024 QIP | ✅ 存在 | `10.1007/s11128-024-04395-w`，hybrid OA，fwci 2.99，10 引 | ✅ 有 `doc_id bcb3e9cf…` | 与仓库 §2.1 记录一致 | 不变（已归档） |
| Zhou AIR Polar | ✅ 存在 | `10.1103/PhysRevApplied.18.044022`（2022），closed 但有 `doc_id` | ✅ 可精读 | ✅ f=1.046@1Gb/QBER0.02、失败概率 ~1e⁻⁸ 均见摘要 | 不变（跨主线，暂不读） |
| Tang/Liu SLA | ✅ 存在 | 期刊版 **QIP 2021 `10.1007/s11128-020-02919-8`**；预印本 arXiv `2003.03713`（2020） | ✅ 双版本有 `doc_id` | ✅ 128 Mb → f=1.091、失败概率 1e⁻⁸；1 Gb/QBER0.02 → f=1.055 | 不变；**引用卫生修正**：作者顺序应为 Tang / Liu / Yu / Wu（仓库 survey:30 写作 "Liu, Wu, Tang, Yu"） |
| Zahidy 2024 | ✅ 存在 | `10.1038/s41467-024-45876-x`，CC-BY，fwci 24.78，84 引 | ✅ 有 `doc_id` | ⚠️ 标题实为 *"…protocol over deployed multicore fiber"*；**摘要不含 SKR 51.5 kbps / f_err,4D=1.06**（属正文/估算） | 维持纪律，且更强：数字不在摘要层 ⇒ 更不可当 IR 实测引 |
| Ogrodnik 2025 | ✅ 存在 | 正式版 **Optica Quantum `10.1364/opticaq.560373`**（diamond OA，fwci 4.95）；arXiv `2412.16782` | ✅ OA | ⚠️ 摘要只声称 **2D 与 4D 实验 key rate**，未见 d=8 实验 | 相关性 **低→低-中**（time-phase BB84 = time-bin 类，与 ToA 同族），但仍是 detector/资源维度 |
| Kanitschar & Huber 2025 | ✅ 存在 | `10.1103/PhysRevLett.135.010802`，fwci 8.25，5 引；预印本 arXiv `2406.08544`（有 `doc_id`） | ✅ 预印本可读 | ✅ 覆盖 **time-/frequency-bin entangled** 高维 key rate；另有 composable finite-size 姊妹篇 | 相关性 **低→中**（仅外层 λ_total→finite-key 净 SKR 换算） |
| 撤稿 Mao 570 Mbps | ⚠️ **核实为撤稿告示本身** | `10.1007/s11082-024-07829-y` = *Retraction Note: High performance reconciliation for practical QKD systems* | 元数据 | ✅ 撤稿成立：同行评议受损、不当引用、超出范围 | 仓库 0 命中，无需清理；**注意同一作者网络（Qiong Li / Hao-Kun Mao）另有 arXiv 2021 leakage-overlap 论文（含 Cascade≈1.02、非交互 1.1–1.2 等通用数字），因该组有不当引用前科，不作为引用来源** |

### 5.2 Scarinzi 2025 正文核到的原文（逐条，决定路线）

- 机制的原文："a sequence of parity-check matrices with decreasing code rates is defined a priori… if decoding
  fails, the code rate is progressively lowered until convergence is achieved"
  ⇒ **与我们 v52/v54/v55 的条件 HARQ（base → stage1 Δm=8 → stage2 Δm=8）同构**。
  说明仓库在这条机制上没有落后，问题在别处（别再重复做机制）。
- 用户转述属实的两句（原文）：
  - "leveraging a-priori knowledge of the instantaneous QBER … increasing the SKL by nearly 3% compared to
    the standard approach that assumes a uniform error rate across the block."
  - "a simpler strategy that assigns **block-wise average QBER** … performed **nearly identically** to the
    full instantaneous-information case" ⇒ 「分块 ≈ 即时」成立。
- 选码依据："initializing rateless code selection based on the **mean channel capacity** of each block
  consistently outperforms using the mean QBER" ⇒ 对应我们的 **per-block Ĥ（而非 per-block SER）**。
- **决定适用性的一条（原文）**：式 (9) 给出 \(\lambda_{IR}\approx\sum_j n_j h_2(\phi_j)\le n h_2(\langle\phi\rangle)\)，
  但紧随其后："due to finite-size effects, **this advantage emerges only for very large block sizes**"。
  其实际 IR 块长 **\(N_{bl}=460800\) bits**（QBER 数组 >3500 万值）；我们的超帧 = 1024 GF(32) 符号 = **5120 bits**，
  **小约 90 倍**。
- 口径差异：其 \(f=(1-R)/h_2(\phi)\)，\(R=(n-m)/n\)，分母是二元熵、分子无 tag
  ⇒ **与仓库冻结的 \(f_{super}=(4·5m+64)/(1024·H_{full})\) 不可直接比**（同 IEEE 11440984 的情况）。
- 会计拆分 semantics：他们明确要求 `φ_X,1`（安全侧）仍用**平均** QBER，只有 IR 侧用即时可靠性
  ⇒ 与仓库「gate 用层/地基 vs claim 用整帧含 tag」的分离原则同构，可直接借这条表述。

### 5.3 核对后的排名修订（相对 §3）

1. **Scarinzi → 由「唯一能改路线的 P0」降为「前提具备、量级存疑」**：由于
   "finite-size / very large block sizes" 与 90× 块长差，**先做零解码的熵口径证据**（逐块 \(\hat H\) vs
   池化 \(\hat H\) 的差是否足以改写 m 预算），而不是直接上 [packet]。它仍是这一批里唯一可能改动点的文献，
   但触发条件变严。
2. **Tarable → 唯一新增可取项**是 **protograph discretized density evolution 工具**：
   仓库 V22/V23 已证 regular / simple-irregular protograph **在结构化信道上不收敛**，若走 joint n=2048 路线，
   应连带评估是否需要这把工具，而不是只照搬 check-node splitting。
3. **Müller 2025 → 仍需线下取 PDF**（SciVerse 无正文，DOAJ/Wiley `pdfdirect` 直链存在）才能核
   message/round 记账项；在此之前不得引用其任何数字。
4. Ogrodnik（time-bin 同族）与 Kanitschar（finite-key 外层）相关性小幅上调，但排位不变：**推迟到 S3 之后**。

### 5.4 本次核对的 Does-not-establish

- 只核了存在性、元数据、摘要与可读到的正文片段；**未核 Müller 2025 的任何数字**（无全文）。
- Scarinzi 的参考文献 [13] 在 SciVerse 无 relations 数据（`REFERENCES` 返回 0），其所用 rateless 码族是否
  即 Tarable 2024 **未正式确认**（仅由"块长为 1800 的倍数 + rateless protograph"推断，标注为未核实推断）。
- 未做任何 decode / 真实数据读取；不改变任何冻结口径；不授权 S2/S3。
