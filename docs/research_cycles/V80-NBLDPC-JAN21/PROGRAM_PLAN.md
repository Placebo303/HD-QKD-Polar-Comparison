# V80 — Jan-21 类数据上的 NB-LDPC 程序重启（计划，docs-only）

- 状态：PLAN，无执行、无数据访问、无 commit/push。
- 依据：`V72P3G8-PRIOR-EFFICIENCY/DECISION_BRIEF.md` §10.4 解除条件
  **已由用户确认达成**：Jan-21 类是主用数据类；目标 = 真实可行的 NB-LDPC。
- 封存范围修正：INFORMATION-CLOSURE 仅对 20260123_* 池类有效；
  Jan-21 类（H_full ≈ 0.55–0.80 bits/符号）不受约束。

---

## 1. 为什么这里能成（与过去所有失败的区分）

### 1.1 设计点完全不同

过去 D/G 系列死亡区：H ≈ 3.7–4.3 bits/符号 → 有效码率 ≈0.06–0.26
（m/n 0.63–0.94），容量下界就吃光净收益。

Jan-21 类设计点：

| 量 | 值 | 出处 |
|---|---|---|
| H(A\|B) 全符号 | ≈0.55–0.80 bits/符号（10 bits） | V19 `H_full=0.549955`；V25 ≈0.80 |
| 帧长 | 256 符号/帧（既有帧格式）；会计单位 = 4 帧超帧 n=1024（单 64-bit tag 摊薄，帧格式本身不变） | V25/v72p2d5：`1024 frames × 256 pairs`；超帧见 §1.3 |
| 目标 f（冻结口径，见 §1.3） | ≤1.3（整帧含 tag）⇒ 超帧 n=1024 泄漏预算 ≤1065 bits（H=0.8；H=0.8326 锚点 ≤1108）/ 帧等效 ≤266 | 净收益目标（原“≤267–332 bits/帧（n=256 单帧、tag 口径混杂）”已 SUPERSEDED，见 §1.3） |
| 对应 m（q=1024，冻结口径） | 网格 24–31 行 → rate 0.879–0.906（≈0.88–0.91）；含 tag n=256 单帧实际 f≈1.43–1.75（H=0.8326 锚点），永不达标；超帧 n=1024 下 m=24 点 f≈1.20，m≤26 达标（H=0.8326 锚点；H=0.8 时 m≤25） | 审计 P4（§1.3；原“m≈24–31 ⇒ f≤1.3（暗含 tagless）”已 SUPERSEDED） |
| 对应符号误码 | ≈4–8%（H≈0.8 的量级） | 容量换算 |
| 现状对照 | R3 f≈12.1 → 2486 bits/帧（冻结口径含 tag：f≈12.0，泄漏 2550 bits/帧，H=0.8326 锚点）；binary V19 f=4.17 → 587 bits/帧（冻结口径含 tag：f≈4.62，泄漏 651 bits/帧，H=0.549955 常数） | V13-R3 / V19 实测（原 tagless 口径值保留作历史；冻结口径换算见 §1.3） |

**rate 0.89–0.91 是常规 LDPC 舒适区**，不是 0.99 的死亡区；每帧要纠的
符号错误约 10–20 个。纠错可行性已由 R3 在同类数据上证明（98.5% exact，
f≈12.1 过度供给），本程序是**纯效率程序**：同样能纠，泄漏从 2486 → 267
bits/帧（9×；tagless 单帧旧口径，已 SUPERSEDED——冻结口径见 §1.3：超帧 n=1024 整帧含 tag，预算 ≤1065 bits/超帧即 ≤266/帧等效）。

### 1.2 净收益账（n-based canonical：net = A·5·n − leak，A=已接受帧数；冻结口径含 tag，见 §1.3）

| 方法 | 泄漏/帧（含 tag） | 净/帧（gross 5·256=1280） | 净/符号 |
|---|---|---|---|
| R3（现状） | 2550（2486+64） | ≈−1270 | −4.96 bits |
| binary MLC（现状 f=4.17） | 651（587+64） | ≈+629 | +2.46 bits |
| **NB-LDPC 目标（f=1.3, H=0.8，超帧实现）** | 预算 266/帧等效（超帧 1065） | **超帧 ≈+4055（帧等效 ≈+1014）** | **+3.96 bits** |

- 旧表（gross 1472/1536 系、tag 口径混杂：R3 −1014/−4.0、binary +885/+3.5、NB +1205/+4.7）已 SUPERSEDED，保留作历史，不删除。
- NB 目标行是 f=1.3 精确预算（非整数 m）；整数 m 实现必须走超帧：q=1024 取 m=25/超帧（泄漏 1064，净 +4056）或 DE 可达点 m=24（泄漏 1024，净 +4096，f≈1.20）；分层臂 m_total=49（m₂=47+m₁≈2，泄漏 1044，净 +4076，f≈1.22）。n=256 单帧无整数 m 达标。
- NB 相对 binary 现状：泄漏约 2.4× 改进（2.54 → 1.04 bits/符号，含 tag 口径：651/256=2.54，266/256=1.04）。
- 相对 R3：净收益从负转正，且码率从 ~0.04 提到 ~0.90。

### 1.3 f 口径冻结（2026-09-20，用户已批准，docs-only 冻结）

此前并存三种 f 口径（审计 P4/P8）：
1. 层单位 f（DE gate 用，如 L2 层 f_row=1.1375 @ m₂=47）；
2. 整帧 tagless f（runner `f_implied=10m/(n·H)`，如 SECONDARY m=24 f=1.126）；
3. 整帧含 tag f（泄漏分子 +64，如 PRIMARY (245+64)/213.1≈1.45）。

冻结选择（唯一口径）：**整帧含 tag f，帧组为 n=1024 超帧（4×256，既有帧格式不变，单 64-bit tag 摊薄）**。
算术规则：单帧泄漏 = 5·m_total + 64（GF(32)² 分层臂，每行 5 bits）或 10·m + 64（q=1024 直接臂）；
超帧泄漏 = 4×单帧 syndrome + 64；分母 content = n·H_full（超帧 n=1024）。
冻结理由：含 tag 下 n=256 单帧 f 下限 ≈1.43（m=24），恒 >1.3、永不达标；超帧回到 ≈1.20–1.22。

验算数（锚点 H_full=0.83256272，content₂₅₆=213.136，content₁₀₂₄=852.544）：
- m=24→31 含 tag 单帧 f = 1.4263 → 1.7547（≈1.43–1.75）；tagless 1.1260 → 1.4545（仅 m≤27 tagless 达标）。
- 超帧：m=24 f=1.2011（≈1.20）；分层 m_total=49（m₂=47+m₁≈2）f=1.2246（≈1.22）；审计 P4 记 ≈1.21，差异仅 H 取整。
- f≤1.3 预算：单帧 277.08（syndrome ≤213.08 ⇒ q=1024 m≤21 / 分层 m_total≤42，DE 点 24/49 均失败——故必须用超帧）；
  超帧 H=0.8 预算 1064.96（m≤25 / m_total≤50）；超帧 H=0.8326 预算 1108.31（m≤26 / m_total≤52）。
- 净收益 canonical（net=A·5·n−leak）：R3 1280−2550=−1270；binary 1280−651=+629；
  NB nominal 超帧 5120−1064.96=+4055.04（帧等效 +1013.76）。

复核命令（纯算术，无项目模块/DE/内核；本会话无 shell 执行工具未能运行，请主线程单命令复核，预期输出与上取整一致）：
`.venv/bin/python -c "H=0.83256272;n=256;C=n*H;print('content256',round(C,3));print('f_tag_24',round(304/C,4),'f_tag_31',round(374/C,4));print('f_less_24',round(240/C,4),'f_less_31',round(310/C,4));Cs=4*C;print('content1024',round(Cs,3));print('sf_m24',round(1024/Cs,4),'sf_L49',round(1044/Cs,4));print('budget256',round(1.3*C,2),'budgetSF08',round(1.3*4*204.8,2),'budgetSF083',round(1.3*Cs,2));print('netR3',1280-2550,'netBin',1280-651,'netSF',round(5120-1.3*4*204.8,2))"`

- PA 感知采样（Tauz et al. ITW 2024，见 `LITERATURE_PA_AWARE.md`）维持为 deferred S3 会计备选项；S1/S2 不受其影响、无变化。

## 2. 文献地图（2026-09-19 扫描；Zotero + web）

### 2.1 已有/已验

- **Müller, Bacco, Oxenløwe, Forchhammer, ISTC 2023**（arXiv 2305.08631）——
  **Zotero 在库**（FN9JZSLS）。HD-QKD NB-LDPC + DE 优化度分布。
- **Müller et al., Quantum Inf. Process. 2024**（arXiv 2307.02225）——本仓库
  **V8 已复现其 Table 1**（q=4 R=0.75, DET 0.069, 差分容差内）。关键数字：
  q=4/8、rate 0.50–0.90、DE 集成效率 **1.024–1.080**、有限码 **n=30000**
  PEG + log-FFT-SPA（≤100 iter）+ blind reconciliation（puncturing/
  shortening 速率自适应），有限码效率 **1.078–1.14**，FER<1%。
  → **意义：MC-DE 工具链已对其 Table 1 验证过；其设计点（rate 0.5–0.9）
  恰覆盖我们的 0.89–0.91 区间。**

### 2.2 直接相关方法族

- **Kasai, Matsumoto, Sakaniwa, ISITA 2010**：QKD rate-compatible NB-LDPC
  ——速率自适应 NB-LDPC 的奠基文献。
- **Dupraz, Savin, Kieffer, IEEE Trans. Commun. 2015**：NB-LDPC 的
  Slepian-Wolf DE 理论（我们 V26 MC-DE 的方法学来源）。
- **Mitra, Tauz, Sarihan, Dolecek 2023**（energy-time entanglement QKD
  NB-LDPC 设计）：**高维符号映射到"低维但 >2"的域**——直接回答我们的
  "q=1024 直接 vs GF(32)² 分层"架构问题，必读。
- **Declercq & Fossorier, IEEE Trans. Commun. 2007（EMS）**+
  Li/Gunnam/Declercq TEMS：低复杂度 NB 解码器（q 大时降复杂度）。
- **Zhong et al., NJP 2015**：**q=1024 协调存在性证明**——layered 方案
  在 n=4000、p=39.6% 下 f≈1.15（文中 β 记号 1.17）。
- **2025 新文献**（待读全文）：IEEE 11440984（NB-LDPC QKD 后处理协议 +
  速率自适应）；Wiley qute.202500389（CV-QKD rate-adaptive NB-LDPC，
  域不同，仅取速率自适应思路）。
- **IEEE 11440984（FULL-TEXT-NOT-RETRIEVED，2026-09-20 追加）**：Crossref
  元数据确认题名为 *Non-binary LDPC Code-Based Post-Processing Protocol
  for QKD*（Chen/Han/Lv/Mao/Wu/Sun/Lv，ECCST 2025，pp. 6–9，DOI
  `10.1109/eccst68196.2025.11440984`）；8 条参考文献含 Li 2023 Opt. Express
  "Rate-adaptive non-binary LDPC codes for QKD information reconciliation"
  与 Zhao 2022 PTL "Performance analysis of NB-LDPC codes in high-QBER QKD
  systems"，速率自适应取向与 S1/S2 相关。全文未取得：websearch ×2 被取消、
  IEEE Xplore 页抓取无正文、arXiv 通用查询无命中——仅元数据+参考文献，
  无摘要/数字可录；待正式获取后再读。

### 2.4 补扫发现（2026-09-19 复核，SciVerse）

- **Müller, Ribezzo, Zahidy, Oxenløwe, Bacco, Forchhammer,
  *Efficient information reconciliation for high-dimensional quantum key
  distribution*, Quantum Information Processing 2024**（DOI
  `10.1007/s11128-024-04395-w`，arXiv 2307.02225，10 引，fwci 2.99）——
  **HD-QKD 上 NB-LDPC 与 Cascade 两种方法、接近 Slepian–Wolf 界**。
  这是 Müller 团队在我们正靶（HD-QKD NB-LDPC）上的**正式续作**，
  §2.1 的 V8 复现（Table 1, q=4/8）即对应此文；应作为 S1/S2 的直接对照。
- **Tauz, Mitra, Shreekumar, Sarihan, Wong, Dolecek, *Block-MDS QC-LDPC
  Codes with Application to High-Dimensional QKD*, ITW 2024**（DOI
  `10.1109/itw61385.2024.10806945`）——**HD-QKD 的 PA 感知 IR**：
  用采样放宽 IR 要求（不靠 f→1.0 也能保住最终密钥长度），Block-MDS
  QC-LDPC 构造。**与我们 n=256 小块、f 受限、64-bit tag 开销大的痛点
  直接对口**——提供"f 不必硬压到 1.0"的替代框架，是 §2.3 文献空白处
  最值得读的一篇。
- 另见：Müller et al. QET 2023（HD-QKD 用 Cascade 高效版，DOI
  `10.1049/icp.2023.3261`）；Borisov/Petrov/Tayduganov Entropy 2023
  （非对称自适应 LDPC 工业 QKD，arXiv 2212.01121，17 引）——速率自适应
  可参考。
- 追加（2026-09-20）：`LITERATURE_PA_AWARE.md`（Tauz et al. ITW 2024，
  arXiv:2403.00192，PA-aware IR 采样框架）记为 **deferred S3 会计备选项**；
  三 misfits：demo rate 0.2–0.4 vs 我们的 0.89–0.91；码长 ≈2000 vs n=256；
  给定 Eve 信息下符号条件独立性在 Jan-21 相关误差下未经检验。S1/S2 不变。

### 2.3 文献空白（我们的位置）

**未见**：q=1024（或 GF(32)²）、块长 256–1024、低 QBER（≈5%）、
真实 HD-QKD 数据上 f≤1.3 的 NB-LDPC 实测结果。我们的设计点恰在
文献空白处——既是风险也是贡献空间。

## 3. 程序步骤（门梯）

### S0 — Jan-21 证据净收益重审 + 设计点确认（EXPLORE，零成本）

读既有证据（不出新执行）：R3 8284/8412 记录、V19 binary 587 bits/帧、
V25 信道证据。产出：

- 每源（Jan-21 三源）实测 `H_full` 与逐位面/逐 plane 熵表（**确认设计点
  H 落在 0.55–0.80**，若某源显著更高则单独定档）；
- R3/binary 的净收益口径重算（§1.2 表的实测版）；
- 冻结设计点（n=256、q 架构选择、m 网格初值）。

判据：`H_full ≤ 1.0` ⇒ 进 S1；`> 1.5` ⇒ 回到逐源排查（该源接近
Jan-23 形态，单列）。

### S1 — DE 系综优化（EXPLORE，复用 V26 MC-DE）

- 在设计 rate（0.88–0.92 网格）上跑 MC-DE 优化 λ(x)（concentrated ρ、
  dv_max≤40、Differential Evolution）——完全按 Müller 2024 §2.2.2 /
  Dupraz 2015 协议，V26 内核已对其验证；
- 门：ensemble 效率 ≤1.15（对应 Müller 同水平）；
- q 架构优先级已按 decision-log 4436 翻转：**PRIMARY = GF(32)² 分层**
  （F03；L2 层速率须用层内口径 m₂=ceil(f·H_L2·n/5)，f=1.3 ⇒ m₂≈54，
  勿用全符号 m 网格）、**SECONDARY = q=1024 直接**；a=3–4 细化 defer。
  执行/审查状态见 `S1_READINESS.md` 与 `INDEPENDENT_REVIEW_20260919.md`。

### S2 — 构造 + 合成 FER 门（EXPLORE）

- **禁用 three-shift-cyclic GF(32) 母矩阵族**（V28–V31 已证明 d_min≤2：
  303 个重复射影类、1107 对比例列）。用 PEG/improved-PEG（Müller 同款）
  + 4-cycle/短环控制；
- log-FFT-SPA（V10 内核），≤300 iter；合成信道（V17/V25 类，QBER≈5%）；
- 门：FER ≤5%（blind reconciliation 速率自适应后）；效率 f≤1.3（冻结口径：整帧含 tag，超帧 n=1024 上度量，见 §1.3）⇒ 构造码率目标：q=1024 直接臂 m≤25（H=0.8，rate≥0.902）/ m≤26（H=0.83，rate≥0.898），分层臂 m_total≤50（H=0.8）/ ≤52（H=0.83）。S2 未授权（维持现状，无新增授权语句）。

### S3 — Jan-21 真实数据开发/确认（DECIDE，单独 prereg）

- development → sealed confirmation，真实 Jan-21 帧；
- 会计：undetected 隔离、披露按最终前缀、beta 只推导、单授权单次执行、
  additive UUID 根；
- 验收：f 实测（冻结口径：整帧含 tag，超帧 n=1024，见 §1.3）、FER、净收益（目标超帧 ≈+4055，帧等效 ≈+1014，nominal f=1.3/H=0.8；DE 可达点 ≈+4076–4096；原“≈+1200 bits/帧（tag-excluded gross）”已 SUPERSEDED）、与 binary/R3 对照。S3 未授权（维持 DECIDE 单独 prereg 要求，无新增授权语句）。

## 4. 风险与护栏

1. **R3 可纠但 f 高 ≠ 低 f 也可纠**：rate 0.89 的码没有 R3 的 6× 冗余，
   FER 风险在构造质量（d_min/短环）——S2 的 PEG+环控制就是为此；
2. **q=1024 直接 = SECONDARY 臂**（V14/V22–24 历史风险；H≈0.8 时等效
   rate 0.88–0.91）；PRIMARY = GF(32)² 分层（decision-log 4436）。分层臂
   必须用**层内速率**（L2 上限 1−H_L2/5≈0.839；全符号网格 24–31 在其上，
   实测 0/420 收敛——见 `INDEPENDENT_REVIEW_20260919.md`）；
3. **有限长**：n=256 只有 205 bits 熵/帧，64-bit tag 占比大——必要时
   多帧合并成 n=1024–2048 的超帧（Jan-21 池有 8412 帧，可分组），
   这是会计选择不是数据选择；
4. 先验：沿用 Model-F 链（V17/V25 时代它就是在这类数据上工作的，
   f≈4.17 的 binary 也用它）；S0 顺带复测其熵口径；
5. 禁止：未授权执行、覆盖证据根、为变绿改断言、把 Jan-23 closure 结论
   外推到 Jan-21（反之亦然）。

## 5. 文献通道（2026-09-19 已就绪）

两条通道都已可用，查文献**先 Zotero 再 SciVerse**（Zotero 是已筛过的）：

- **Zotero**：`zotero-search` skill（需 Zotero 桌面端运行）。
  已在库：Müller ISTC 2023（HD-QKD NB-LDPC）。
- **SciVerse MCP**：server 名 `sciverse`，已接入 CodeBuddy 配置
  `C:\Users\admin\.codebuddy\mcp.json`（此前只在 WorkBuddy 侧）。
  安装体 = `C:\Users\admin\.workbuddy\binaries\node\versions\22.22.2-3\` 下
  `node.exe` + `node_modules\sciverse-mcp-server\dist\cli.js`（v0.14.2）。
  工具：`search_papers` / `semantic_search` / `read_content` / `get_resource` /
  `list_catalog`。已实测 `search_papers` 真实返回（token 有效）。
  **新装 MCP 需重启会话**才出现在工具列表；重启前可 stdio JSON-RPC 直连。
- 已知待读（SciVerse 检索所得；§2.4 已核实引用）：
  1. Müller 等, *Performance of Cascade and LDPC Codes for Information
     Reconciliation on Industrial QKD Systems*, **IET Quantum Communication
     2025**, DOI 10.1049/qtc2.70003（引用已核实；工业系统实测 + blind
     协议，与"真实可行"目标最贴）；
  2. **Tauz/Mitra/Dolecek Block-MDS QC-LDPC（ITW 2024）——见 §2.4，
     PA 感知 IR，对 n=256 小块最贴，优先读**；
  3. Müller 等 *Efficient IR for HD-QKD*, QIP 2024（DOI
     10.1007/s11128-024-04395-w）——直接对照（=V8 复现源的正式版）；
  4. Borisov 等 Entropy 2023（非对称自适应 LDPC，arXiv 2212.01121，
     速率自适应思路）。

## 6. 立即下一步（已被执行取代，2026-09-19 晚注）

- S0 已 ACCEPTED（`S0_RESULT.md`）；S1 readiness 完成（`S1_READINESS.md`，
  45+6 测试经独立复跑通过）；S1 执行中且存在阻断级发现（PRIMARY 层速率
  网格不可行 / 门度量不含收敛）——见 `INDEPENDENT_REVIEW_20260919.md`。
   修复 + 独立复审（D5-delta 模式）完成前，不得解释 S1 结果、不得进 S2/S3。
- HOLD 状态见 `S1_HOLD_20260919.md`（2026-09-19，docs-only，无授权）。
