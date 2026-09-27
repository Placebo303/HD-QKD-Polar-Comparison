# SAME-DATA 同数据比较指标清单（(e) 清单全文）

- Packet: `PACKET-E SAME-DATA-METRICS-SPEC`（doc-only spec + OpenSpec proposal 草案）。
- Track: **documentation-only — 无 track gate**（`AGENTS.md` §1.2 适用性矩阵
  "Documentation-only changes" 行）。本文件**不授权任何执行**：零解码、零真实数据
  访问、零 benchmark/smoke、零 commit/push。
- 配套 OpenSpec 草案：`openspec/changes/same-data-comparison-metrics/proposal.md`
  （**仅 proposal**；不含 `design.md`/`tasks.md`/`specs/`，不改任何现有 spec，不改主干）。
- 禁止面（本 packet 明令）：不写 `comparison_bench/` 任何代码或列；不跑
  benchmark/smoke；不 commit/push。
- 上游依据（只读）：
  - `docs/ROADMAP-20260921.md` §3 **P5**（line ~224 起：同数据、同会计口径的
    MLC/R3 对照臂 + P5 会计条款）与 §5 对外表述规范；
  - `docs/research_cycles/EXPLORE-20260923-DIMENSION-PROBE/TRACEABILITY.md`
    （MLC f=4.169 / 587 bits/帧 / 500/500；R3 f≈12 单遍本原综合征；
    R2 行 r=10 native≈9× wall，2.1 s vs 19.4 s）；
  - `docs/research_cycles/V80-NBLDPC-JAN21/P1_STAGE1_BATCH_END_REVIEW.md` **§8**
    （路线输入留主线程；单臂/单门 cherry-picking 禁令）及其 §2/§7-F3 列语义；
  - `docs/hd-qkd-ir-comparison-owned-roadmap-20260907.md` **M5**
    （measured / assumed / projected / qualified 必须分开；先 reconciled-net 选点，
    协议观测量+有限长度参数+epsilon budget 全合格后才有 secure-key 选点）；
  - `AGENTS.md` **§5.3**（schema stability：列名/键名/CLI 不得静默改变）、
    **§5.5**（科学语义：`undetected` 不得转成 `ok`、泄漏口径方法特定、
    `beta_eff_empirical` 只推导）。
- 验收项：**A-CMPE-1 … A-CMPE-7**（见 §10；ID 稳定，回报只引用 ID）。

---

## §0 适用范围

本清单冻结"**同数据比较**"（P5 对照臂：本程序 NB-LDPC vs 二元 MLC 基线 vs
R3，Jan-21 三源同一批超帧、同一会计口径）应报告的**全部指标列与标注义务**。
它是 report-contract（报什么、怎么标），**不是实现**：本文件不定义任何 CSV
文件名、不修改 `comparison_bench/` 既有 schema、不新增任何生产列。将来任何把它
落成代码/列的实现 change 必须另开 OpenSpec change，并遵守 §5.3 静默变更禁令。

---

## §1 每源结果计数列（per-source outcome columns）

1. 四个计数**各自独立成列，逐源（1M / 1p5M / 2M）分列**：
   - `attempted` — 该源尝试的块/超帧数；
   - `exact_match` — 精确匹配恢复数；**`success := ¬failed`（＝`exact_match`）**；
     `decoded`（译码器返回/走综合征路径）**≠ success**，须带一行图例
     （P1 batch-end review §7-F3 的列语义教训）；
   - `accepted` — 最终协议接受数；
   - `accepted_wrong`（`undetected`）— 错误接受数，**独立列**。
2. **`undetected` 绝不并入 `success`，绝不并入 FER 的分子当成功**（ROADMAP §3-P5
   会计条款；`AGENTS.md` §5.5；TRACEABILITY E7 口径：undetected 计入失败帧，
   在 success 之外）。禁止把 `reference/stub/unavailable/decode_failed/
   no_verified_success` 静默转成 `ok`（§5.5）。
3. 禁止跨源、跨构造实例、跨臂合并任何上述计数（ROADMAP §5 禁令 5；
   P1 review §8 单臂/单门 cherry-picking 禁令）。

## §2 效率双数（f_super / f_eff）

1. 任何 f 断言**双数并列**：`f_super` 与 `f_eff`，**两个都报，禁止互相替代**
   （ROADMAP §2 DECISION-1、§5 必须 1/禁止 2）。
2. `f_eff = f_super + 4.785675·FER` 的 FER 项用**本臂自己的 m 基**（m=202 →
   1.259759；m=208 → 1.294947；混基是被明令纠正过的缺陷）。绝不允许把
   `f_super` 值当 `f_eff` 报（ROADMAP §5 禁令 2）。
3. FER>0 与 FER=0 的认证作用域、rule-of-three `N_req` 作用域随数字一起标注
   （ROADMAP §2 DECISION-1 作用域限定）。

## §3 实际公开比特与完整协议链（disclosure accounting）

1. 报**实际公开比特**，逐源分解：`leak_EC` + **64-bit 验证 tag** ⇒
   **verification-aware `λ_total = leak_EC + 64`**（≡ ε_EV ≈ 2⁻⁶³ 的
   Kanitschar–Huber 桥接行；ROADMAP §3-P5、§2 DECISION-3）。
2. 完整协议链必须逐项列开：EC 泄漏、**验证标签**、**控制轮次/控制帧**、
   （若有）blind/incremental 救援段公开量——每项单列，不合并成一个不透明数字。
3. **prior 成本单列一行**：每源 **1.50× 机会成本**（60/20/20 切分下 prior 是
   它所开启的 key 的 1.50 倍；`v80-prior-cost-accounting` 7 SHALLs 的绑定数字；
   0.12–0.26× 已撤回不得作 planning number）。prior 成本进 SKR 分子/机会成本
   行，**不进 `f_super`/`f_eff` 分子**（prior disclosure ≠ EC leakage）。
4. 泄漏是**方法特定**的：只有分解语义一致时才允许横向相减（§5.5）；
   口径不一致时按 §8 标"不可比"。

## §4 资源与交互（resources, P6）

逐臂逐源报告：

1. **总 wall**（该臂全部块）；
2. **每块 wall**；
3. **每次译码 wall**（含最大值/超时语义：timeout = terminal，fail，无重跑）；
4. **峰值 RSS**（对照预算如 <2 GiB）；
5. **交互消息数/轮数**（P6：对标 Müller 的 446 Cascade vs 3.14 messages 口径，
   标注那是每帧消息数）；
6. 吞吐行须区分 **IR 吞吐 / 采集率**：6.7 kbit/s 是采集/筛后速率，
   **不是 SKR、不是 IR 吞吐**（ROADMAP §5 禁令 3）。

## §5 样本量、资格与计数分离

1. **`N_req` report-only**：`N_req = ⌈3·4.785675/(1.3 − f_super)⌉` 只作报告行，
   标 "report-only"，**不作操作点选择**；与 **key-eligible** 计数
   （**200/276/364**，非 500/691/911）分列对比，谁认证得了逐源判定。
2. **`d` / `q` / `n_IR` 三个参数分离报告**：维数 d、有限域/字母表 q、IR 块长
   n_IR 各自成列，不合并、不互相代表（owned-roadmap 边界：固定 d 的 tau 扫描与
   d×τ 泛化分开）。
3. **三组计数严格分离**：**合成**计数、**真实**计数、**key-eligible** 计数
   分组小计，永不出现在同一分母里；合成 FER 不得当真实 FER
   （ROADMAP §1.2-5、§3-P3 门）。

## §6 历史口径标注（R3 / MLC）

1. **MLC 二元基线行**：历史实测 `f = 4.169`、`587 bits/帧`、`500/500`，H 基
   `H_full = 0.549955`，**tagless 历史口径**（冻结口径含 tag 换算 f≈4.62、
   651 bits/帧——两口径都列或标"历史 tagless"）。500/500 是其原始帧数，
   **不得**当作本清单 §5 的 key-eligible 计数。
2. **R3 行**：`f ≈ 12`（≈12.1），单遍**本原综合征**（TRACEABILITY C2：
   `(1−0.336)·256·10 = 1699.84 bits/帧 = 6.64 bits/symbol`，m=170≤n=256，
   算术上等同单遍本原综合征；"必须是交互/多趟"的说法已撤回 C3），原生
   q=1024 / n=256 / rate 0.336，8284/8412 exact。
3. **不可比即标**：历史行与新行在 H 基、tag 口径、块长、数据池、会计分解上
   任一不一致时，该单元格必须带"**不可比**"标注 + 不可比原因（H 基/tag/池/
   分解），**不得**给跨口径差值（ROADMAP §5 必须 4；§5.5 泄漏口径条款）。
   MLC f=4.169 与 "just below the ceiling" 的邻近说法已撤回（TRACEABILITY C4），
   不得引用。

## §7 探针成本行与探针作用域

1. **9× 成本行（独立标注，不并入主序列）**：r=10 强二元对照——
   reference `codebook_v4` 102/1200 @ D=584、wall ≈ **2.1 s**；本原
   GF(32)×GF(32) split 2/1200 @ D=580、wall ≈ **19.4 s**（每 1200 帧）⇒
   **native ≈9× 运行时（对该臂不利）**。这是 EXPLORE 探针的**资源成本行**，
   TRACEABILITY R2：**不合并**进 GF(4/8/16) 系列（分组方案不同）。
2. **探针不替真实结论句（固定句，逐份报告照抄）**：
   > "本行是合成探针（EXPLORE, `diagnostic_only`）的运行时成本测量，
   > **不替代、不预示任何真实数据上的 FER、效率、泄漏或 SKR 结论**；
   > 真实结论只能来自 P5 的 DECIDE 合约。"
3. 探针的 50.8×–558×（β=2 整数失败计数）等 FER 比值若引用，必须带其全部作用域
   （n=256、dv=3 random-regular 单系综、matched disclosure、max_iter=60、
   单一功率路径），并同样适用第 2 条固定句。

## §8 主张上限（claim ceiling）

1. **无安全观测量 ⇒ 只能写"实测纠错收益 / 公开开销收益"**：
   reconciled/public-EC 结果、公开 EC 开销、接受率、运行资源——
   **禁止 SKR、secure-key、资格化、composable 安全、publication claim**
   （owned-roadmap M3："安全观测量不足时只报告 reconciled/public-EC 结果，
   不冒充 secure key"；`v80-prior-cost-accounting` claim-ceiling SHALL）。
2. **SKR 选点禁令**：协议观测量、有限长度参数、epsilon budget 全部合格之前
   不得给出 secure-key-rate 最优点（owned-roadmap **M5**）。
3. 结论句不越出数据作用域：不跨源/跨实例合并、不从合成外推真实、
   不把采集率说成 SKR/IR 吞吐（ROADMAP §5 禁令 1/3/5）。

## §9 状态分列（measured / assumed / projected / qualified）

1. 每个对外数字必须落在**四列之一**（owned-roadmap M5：四者必须分开）：
   - `measured` — 本仓库实测，带 artifact 指针；
   - `assumed` — 显式假设，带假设内容；
   - `projected` — 外推/预测（如 ROADMAP P1 的算术预测行，标"非承诺、证据不足"）；
   - `qualified` — 已过适用资格化门（当前基线下多为 `—`）。
2. 未落列的数字**不得出现在对外表格**；`beta_eff_empirical` 只能由泄漏/误差
   输入推导，永不手填（§5.5）。

## §10 验收项（A-CMPE-1..7，ID 稳定，回报只引用 ID）

| ID | 验收项 | 覆盖条款 |
|---|---|---|
| **A-CMPE-1** | per-source 四计数独立列（`attempted` / `exact_match`＝`success`＝¬failed（含 `decoded`≠success 图例） / 最终 `accepted` / `accepted_wrong`=`undetected`），`undetected` 禁并入 success/FER，禁跨源/跨实例合并 | §1 |
| **A-CMPE-2** | `f_super` 与 `f_eff` 双数并列，`f_eff` 用本臂 m 基，禁互相替代、禁把 f_super 当 f_eff | §2 |
| **A-CMPE-3** | 实际公开比特：`leak_EC` + 64-bit tag ⇒ verification-aware `λ_total`，加验证标签、控制轮次等完整协议链逐项列开，加每源 1.50× prior 机会成本行 | §3 |
| **A-CMPE-4** | 资源耗时：总 / 每块 / 每译码 wall + 峰值 RSS + 交互消息数（P6），IR 吞吐与采集率分标 | §4 |
| **A-CMPE-5** | `N_req` report-only vs key-eligible（200/276/364）分列；`d`/`q`/`n_IR` 分离；合成/真实/key-eligible 三组计数分离 | §5 |
| **A-CMPE-6** | R3/MLC 历史口径标注（tagless/冻结口径、H 基、原生单遍综合征）与"不可比即标"；r=10 native≈9×（2.1 s vs 19.4 s）成本行独立 + 探针不替真实结论固定句 | §6, §7 |
| **A-CMPE-7** | 无安全观测量 ⇒ 仅"实测纠错/公开开销收益"、禁 SKR（M5 选点禁令）；每个数字落 measured/assumed/projected/qualified 四列之一 | §8, §9 |

## §11 明令禁止（本 packet）

- 写 `comparison_bench/` 任何代码或列；
- 跑 benchmark / smoke；
- commit / push；
- 把本清单当成执行授权或科学结论（0 字节科学执行）。
