# G0B 真实点门（G0B_REALPOINT_GATE）— 草案冻结件（2026-09-23）— DRAFT / NOT GRANTED / NOT AUTHORIZED / NOT EXECUTED

- 文件性质：**docs-only 草案**。Track = **documentation-only — 无 track gate**
  （`AGENTS.md` §1.2 适用性矩阵 "Documentation-only changes" 行）；**裁决权在用户**，
  本文件不代裁决、不预支裁决。
- 本文件**不授权任何执行**：零解码、零构造、零真实数据访问、零 `.ttbin`/`gamma` 读取、
  零 commit/push、零 `results/` 与 `comparison_bench/outputs_comparison/` 写入。
- 创建范围（P4-3 式声明）：本任务**只新建本文件一份**。不改
  `docs/ROADMAP-20260921.md`、`docs/EXECUTION_PLAN_20260922.md`、
  `docs/decision-log.md`、`docs/NOW.md`、`AGENTS.md`、`docs/troubleshooting.md`、
  `src/`/`experiments/`/`tools/`；**不碰 NOW / P3 族 / P4 族 / P1 族 / S0.1 族**任何文件。
  工作树中的既有改动（`AGENT_PROJECT_MEMORY.md`、`docs/NOW.md`、
  `comparison_bench/src/comparison_bench/cli/p4_feas_construct.py`、
  `comparison_bench/tests/test_p4_feas_construct_fake.py`、
  `docs/research_cycles/EXPLORE-20260923-DIMENSION-PROBE/`、
  `openspec/changes/same-data-comparison-metrics/` 等）**与本任务无关，原样保留**。
- 基线（provenance，非执行锁）：`8e9c8526`，分支 `formal-ir-v72p1-addendum-clean`
  （AGENTS §10.3：不做 SHA 相等断言）。
- 上游只读出处（本文件全部为重述/转录，零新数值、零新阈值）：
  - `docs/decision-log.md:4850–4859`（G0=B 裁决条，F3 见 §5.1）；
  - `docs/research_cycles/V80-NBLDPC-JAN21/P1_STAGE1_BATCH_END_REVIEW.md` **§8**（门映射与路线输入，见 §5.2）；
  - `docs/research_cycles/V80-NBLDPC-JAN21/P4_FEAS_PACKET.md` **§10(a)**（入口语境三前提，见 §4）；
  - `docs/research_cycles/V80-NBLDPC-JAN21/P3_MEMORY_AUDIT_PACKET.md` **§2.5**（预注册容差：T-C0 REUSED + T-M1..M4 PROPOSED re-freeze v2）/**§7**（授权签字块全 BLANK）；
  - `docs/ROADMAP-20260921.md:224–228`（P5 配置与样本量前提，见 §5.3）与 `:259–277`（决策树 + 2026-09-21 修正）；
  - `docs/hd-qkd-ir-comparison-owned-roadmap-20260907.md` **M2–M5**（真实单点 → 公开开销闭环 → 扫描 → 安全资格与最终选点；measured/assumed/projected/qualified 必须分开）；
  - `docs/research_cycles/EXPLORE-20260923-DIMENSION-PROBE/TRACEABILITY.md` **末段**（"What this packet does NOT establish" 承接句 + R1–R3 最终主张 + 归档状态表）。

---

## §0 本文件不做什么（全文有效）

1. **不裁决**：本文件对任何分支（S-B / S-A）、运行点、帧长、模型**不作选择、不作判定**；
   七元组只做**冻结重述**，两分支只做**并列对照**，门前提只做**事实状态记录**。
   全文不含任何"选定 / 定案 / 裁决完成"式的措辞（对引文中出现的"选定"字样，
   其指向是未来包的冻结动作，本文件对该动作无判定）。
2. **无执行授权语句**：§7 授权块**全 BLANK**，未填 = 未授权；本文件不是授权路径，
   任何未来执行须走对应包自己的 Pre-EXECUTE + 显式用户授权。
3. **预算数值一律 `[TO BE FILLED AT PRE-EXECUTE]`**：本文件不填预算数、不设 ceiling、
   不冻结 UUID、不代做输出缺席检查。
4. **引文为原文转录**（§5 带行号），转录不构成新裁决，也不放宽任何原文门。
5. **Claim ceiling（本文件最高产出）** = 一个待授权门的**草案结构**：
   七元组 + 口径分离表 + 两分支对照 + 门前提 + 空授权块。
   **非**：路线裁决、分支选择、运行点选择、FER/`f_eff`/泄漏/SKR/资格化/发表句、
   可认证 `f_eff ≤ 1.3` 句、执行授权。

---

## §1 冻结七元组（草案重述；改动任一 ⇒ 新包，不在本文件内修订）

| # | 分量 | 冻结值（重述，零改动；出处见右列） |
|---|---|---|
| 1 | **数据源** | Jan-21 三源 **1M / 1.5M / 2M**（CW 时间-能量纠缠、ToA 分箱；IR 只消费 `H(X|Y)`，与偏振/BBM92 无关 — ROADMAP DECISION-3）。**分源报告、禁跨源合并**（统计量、计数、FER、判定一律逐源分列；"不得合并源凑通过" — P3 §4）。真实数据访问 = **DECIDE** 合约。出处：`P3_MEMORY_AUDIT_PACKET.md` §2.1/§2.2、`PRIOR_COST_ACCOUNTING_DECISION_20260921.md` §D。 |
| 2 | **(d, τ, n_IR)** | **d = 1024**（ToA 分箱维数）；**τ**（时间/门控参数，owned-roadmap M4 的扫描轴：固定 `d,n_IR` 扫 `tau`）沿用所引用包的冻结口径，**本文件不新设 τ 数值**；**n_IR = 1024（S-B 窄路）或 2048（P4 证据线）** — 超帧长度，单位 GF(32) 符号。三参数**各自成列、不合并、不互相代表**（`SAME_DATA_CMP_METRICS.md` §5-2）。**改长度（1024↔2048）或改模型（信道/先验/生成器/解码器形态）= 新包**。出处：owned-roadmap M2/M4、`P3_MEMORY_AUDIT_PACKET.md` §2.1、`EXECUTION_PLAN_20260922.md` §3 S-A/S-B。 |
| 3 | **q** | **q = 32**（GF(32)，5 b/综合征符号 ⇒ `leak(m) = 5m + 64`，tag **64 b/超帧不翻倍**）。q 与 d、n_IR 分列，q 不代表 d、不代表 n_IR。出处：`V80_BASELINE_20260921.md` §2、`P4_FEAS_PACKET.md` F7/§2.1。 |
| 4 | **码构造** | **PEG 不规则族**（`family="peg-irregular"`，`λ={2:1}` edge-perspective，`ρ=make_rho(1−m/n)` 集中校验分布，`trials=20`，three-shift-cyclic 拒绝门）+ **构造谱系**（n=1024：**2026092001** girth 8 / **2026092011** girth 6，两实例**分列禁合并**，含跨实例 pins/计数相加禁止）+ **嵌套基**：n=1024 ⇒ 基 `rows[0,200)`、单段披露 `rows[200,208)`、**总行 208 ≤ 208 硬顶**（NO warm-start / NO non-nested / NO two-segment）；n=2048 ⇒ 全矩阵 416、**嵌套基 `rows[0,400)` rank-400 REQUIRED（400 → 416）**，NO 第二矩阵族。出处：`P1_STAGE1_PACKET.md` F2/F2.1、`P4_FEAS_PACKET.md` F1/F2/F6。 |
| 5 | **先验 / gamma** | `gamma_f03.npz`（+ `gamma_f03_pb.npz`）= **一次性工厂标定、只读、永不重拟合**；复用事实 O1/O1R/P0/L1B/B2E/B2F/B2G/X1 保留；**跨源复用禁止**（X1 §4 — 1M/1.5M bundle 须各自物化，每源自付标定成本）；**每源 1.50× 机会成本入账**（仓库 60/20/20 split ⇒ 先验成本 = 1.50× 它所开启的密钥；任何 SKR/净钥分子必须报告 forgone key）。0.12–0.26× 与 1.8× 为**已撤回**数，不得作规划数。出处：`V80_BASELINE_20260921.md` §5-i、`PRIOR_COST_CLAIM_REVIEW_20260921.md` §2c、`EXECUTION_PLAN_20260922.md` §3 S0.3、`decision-log.md:4787,4801,4827`。 |
| 6 | **速率救援 + 认证判定** | **单段救援**（`m_base=200` → 总行 **208 硬顶**；两段/多段 OUT-OF-BOX，须另包）；**bar**：内部 bar（fails ≤ 12，FER ≤ 5% 路线继续/停止门）**仅 report-only，不早停、不裁决**（Stage-1 解完全部 240 块）；**终态语义**：单调用超时 = 终态（块计 fail，不续跑）、`INCOMPLETE-wall` 保留不续跑、无 retry/resume/adaptive、"grant spent" 后无重跑；**`undetected` 单列并计为失败**（在失败集合内、**永不并入 success**）；**认证判定** = `N_req = ⌈3·4.7857 / (1.3 − f_super)⌉` **report-only** 与该源 key-eligible 计数**逐源**比较（n=1024 ⇒ 200/276/364；n=2048 ⇒ 每源 250/345/455 且 N=338），谁认证得了逐源判定，禁单臂/单门 cherry-picking。出处：`P1_STAGE1_PACKET.md` F9/§4、`P1_STAGE1_BATCH_END_REVIEW.md` §8、`ROADMAP-20260921.md:226–228`、`SAME_DATA_CMP_METRICS.md` §5-1/§5-3、TRACEABILITY E7。 |
| 7 | **预算 / 停止门** | **全部 `[TO BE FILLED AT PRE-EXECUTE]`**：单窗口 wall 上限、批次总 ceiling、单调用/单次构造帽、峰值 RSS、CPU 数、机器根 UUID（fresh additive + 缺席证明）、输出缺席与保护根快照、focused fake-only 测试输出。停止规则**形状**重述自 `P1_STAGE1_PACKET.md` §5 / `P4_FEAS_PACKET.md` §5 / `P3_MEMORY_AUDIT_PACKET.md` §5（科学输入变动 ⇒ STOP；违禁读取/解码 ⇒ STOP-BLOCKED；wall-partial ⇒ 终态保留）；**数值本文件不填，本文件不设授权路径**。 |

**变更规则**：七元组任一分量的值、单位、口径或判定规则发生改动（含**改长度、改模型**）
= **新包**（+ 必要的 OpenSpec），不得原地静默改写本文件（P3 §6 修订规则同形）。

---

## §2 口径分离表（d/q/n_IR 分列 + 合成 / 真实 / key-eligible **三组计数严格分离**；census 另量纲）

### §2.1 维度参数（不是任何计数；各自成列，不合并、不互相代表）

| 参数 | 冻结值 | 含义 / 禁止 |
|---|---|---|
| `d` | **1024** | ToA 分箱维数（HD-QKD 字母表维数）。禁止用 `d` 代表 `q` 或 `n_IR`。 |
| `q` | **32** | 有限域 / 字母表 GF(32)。禁止用 `q` 代表 `d` 或 `n_IR`。 |
| `n_IR` | **1024**（S-B 窄路） / **2048**（P4 证据线） | IR 块长（GF(32) 符号/超帧）。禁止跨 n 直接并列计数或推单调性。 |
| `τ` | 沿用所引用包冻结口径（owned-roadmap M4 扫描轴） | 固定 `d` 的 τ 扫描与 `d×τ` 泛化分开；本文件不填 τ 数值。 |

### §2.2 三组计数分离（永不出现在同一分母里；分组小计，禁换算、禁相加、禁替代）

| 分组 | 口径 | 单位 | 数值 | 出处 | 禁止 |
|---|---|---|---|---|---|
| ① **合成** | 合成 240 块族（S0.1 / P1 Stage-1） | 配对块 / 臂 | **240 / 臂**（两构造实例分列：S0.1 seeds `2026095601+idx`、P1S1 seeds `2026096401+idx`） | `S0_1_M200_PACKET.md` F9、`P1_STAGE1_PACKET.md` F3/F9 | 禁与真实超帧、key-eligible、1200 帧探针换算/相加；合成 FER 不得当真实 FER |
| ① **合成**（探针） | 维度探针格点帧数 | 帧 / 格点 | **1200 帧 / 格点**（A1 网格；A1f/A1g 1200；r=10 对照 102/1200、2/1200） | TRACEABILITY E4/F3a/R2、`FINDINGS.md` §1/§7.9 | 禁并入 240 块族；不同格点/不同分组方案禁合并（R2 明示不合并）；探针不替真实结论句固定适用 |
| ② **真实** | 真实超帧 **n=1024** | 超帧 / 源 | **500 / 691 / 911**（池 2000/2767/3645 帧 ⇒ 2103 合计） | `ROADMAP-20260921.md:224–225`、§1.2 表、`decision-log.md:3078` | **非**认证计数；禁与 key-eligible 混用 |
| ② **真实** | 真实超帧 **n=2048** | 超帧 / 源 | **250 / 345 / 455**（合计 1051） | `ROADMAP-20260921.md:224–225`、`P4_FEAS_PACKET.md` F8/§2.1 | 同上；禁跨 n 相加 |
| ③ **key-eligible** | 牺牲标定样本后可承载认证判定的计数（sacrifice-the-sample DEFAULT） | 认证计数 / 源 | **200 / 276 / 364**（池 840） | `PRIOR_COST_ACCOUNTING_DECISION_20260921.md` §D、`decision-log.md:4801`、`P4_FEAS_PACKET.md` F8 | **唯一**认证判定口径；禁用 500/691/911 冒充（2.5× 高估）；MLC 历史 500/500 属其原始帧数，**不得**当作本组计数（`SAME_DATA_CMP_METRICS.md` §6-1） |
| ③ **key-eligible**（对应 n=2048） | 待逐源列判定表 | — | **不代列**：`⌈3·4.7857/(1.3−f_super)⌉` 须与该源块数逐源比较后才知；S3/S-A 包冻结前必须逐源列出该判定表 | `ROADMAP-20260921.md:226–228` | 本文件不填该表、不作可认证句 |
| **另量纲（不在①②③内）** | census raw-stream 计数 | 原始流记录（**另一量纲**） | **129763 / 180536 / 239420** 量级 | `P3_MEMORY_AUDIT_PACKET.md` §2.1（引 `P3_A1_REVIEW` F-5） | **禁混用、禁替代**超帧口径；不得换算进任何分母 |

**三分离一句话**：**合成组 / 真实组 / key-eligible 组**分组小计，永不出现在同一分母里；
census raw-stream 是**另一量纲**，排在三组之外；`d`/`q`/`n_IR` 是维度参数，不是计数
（`SAME_DATA_CMP_METRICS.md` §5-2/§5-3 同形条款）。

---

## §3 两分支对照（并列事实；**不裁决**走哪一支）

| 项 | **S-B 窄路（n=1024）** | **S-A 段 / P4 证据线（n=2048）** |
|---|---|---|
| 出处 | `EXECUTION_PLAN_20260922.md` §3 **S-B**（G0=(B) 主路径：S0.1 → P1 单段救援 → P3 → P5 n=1024；P4 作第二代并行） | `EXECUTION_PLAN_20260922.md` §3 **S-A**（G0=(A) 首步 S0.2 构造可行性必须 PASS → P4 构造+DE → P3 → P5 n=2048；1.5M/2M headline、1M 诊断） |
| 真实超帧 / 源 | **500 / 691 / 911** | **250 / 345 / 455** |
| 认证计数语境 | key-eligible **200/276/364**；N_req（report-only）P1 实测 402（R1）/ 575（R2） > eligible ⇒ 该批无一臂达成三门同过 | N_req **338**（m=416 恒等式，report-only，仅零失败臂相关）；**1M 源 250 < 338 ⇒ 1M 降级为诊断性**，headline 只能由 1.5M/2M 承担（`ROADMAP-20260921.md:214–216,269–270`、`P4_FEAS_PACKET.md` F8/§2.1） |
| 门映射（评审已记录的事实，非本文件裁决） | `P1_STAGE1_BATCH_END_REVIEW.md` §8：R1 **FAIL(a)**（F=1/240）、R2 **FAIL(c)**（21.31 < 21.5 b；r=57.5% > 57.0% cap）；两臂**无一同时满足三门**；机械救援有效（221/222）与门结论是两回事 | `P4_FEAS_PACKET.md` §4：零解码下 P1 式 (a)(b)(c) **不可判定**，只产构造 pins 证据；**P4 是否升为 S3 必经不在该包**（G0=B F3 约束） |
| G0=B 下的定位（引文见 §5.1） | G0=B 主文 = 实测效率 + 同数据 MLC/R3 对照；本对照仅列两支差异供未来门使用 | **第二代并行**路线，不因 P1-FAIL 自动升格为 S3 前置必经 |

> 对照表**不构成**分支选择、不构成 S3 前置裁决、不构成运行点选择；
> 走哪一支、何时走，由主线程与用户在未来门上决定（本文件无该权限）。

---

## §4 门前提（前提状态 = **事实记录**，非裁决、非授权）

本门草案的**前提**（并列于 `P4_FEAS_PACKET.md` §10(a) 三前提同形，逐项照抄其性质 —— "三者是冻结前提，不是授权"）：

1. **P4 batch-end 独立评审存在且可读**（`P4_FEAS_PACKET.md` §6-3 要求的**单次**
   batch-end 独立评审：授权边界、机器门、保留失败、修复若用、最终证据、claim ceiling）。
   - 状态（事实）：`P4_FEAS_PACKET.md` 版本头 = **FROZEN, NOT GRANTED**；
     `P4_FEAS_BATCH_END_REVIEW.md` 在本仓**不存在**（该包未执行 ⇒ 无批次评审）
     ⇒ 前提 1 **当前不具备**。
2. **如该分支判定需要 P3 记忆/一致性门 verdict**（`P3-gate` 二元形式：
   T-C0 ∧ T-M1 ∧ T-M2 ∧ T-M3 ∧ T-M4 全在预注册容差内 ⇒ 放行 S3 讨论；
   任一超差 ⇒ 先做帧级条件化/漂移处理，不得把合成 FER 当真实 FER —— P3 §4 原文形状）。
   - 状态（事实）：`P3_MEMORY_AUDIT_PACKET.md` 版本头 = **FROZEN — NOT GRANTED —
     NOT AUTHORIZED — NOT EXECUTED**；§2.5 的 T-M1..M4 为 **PROPOSED — re-freeze v2**
     （授权时仍须逐项确认）；§7 授权签字块**全 BLANK** ⇒ 无 verdict。
3. **入口语境已记录**（`P4_FEAS_PACKET.md` §10(a) 原文三前提：P1 Stage-1 P4-elevation
   输入 + G0=B F3 + 用户顺序 ①→③→② —— "三者是冻结前提，不是授权"）。

**前提 ≠ 授权**：前提的满足、不满足及其后果由主线程与用户在未来门上处理；
本文件**不补做、不催做、不授权补做**任何一项（P4 执行、P3 执行、verdict 获取均不在本文件范围）。

---

## §5 原文引用（转录，带出处；不放宽、不改写）

### §5.1 G0=B 裁决条 — F3 原文

出处：`docs/decision-log.md:4850–4859`（条目标题与 F3 逐字）：

> ### 2026-09-22: G0=B裁决 (用户授权)
>
> **Scope (F3/F4)**:
> - **F3**: `docs/ROADMAP-20260921.md:209,268` 的 "P1 失败 ⇒ P4 在 S3 之前成为必经" 分支被本裁决取代——P4 不因 P1-FAIL 自动升为 S3 前置必经。
> - P4 n=2048 定位为**第二代并行**路线，不阻塞 S3；可与主路径并行做零解码构造可行性（本条不授权任何解码执行）。

（同条 `:4859` 结尾："本条为裁决落档（docs-only）：**P1/P5 均未执行**，无任何臂、无认证句、
无 FER/SKR/qualification/publication 主张。" —— 本文件继承同一上限。）

### §5.2 P1 门原文（`P1_STAGE1_PACKET.md` §4，逐字）

> ## §4 门（二元；Stage-1 上下文仅 report-only）
>
> - **门 (a)**：最终 **F/240 = 0**（HARD —— DECISION-1 认证作用域：零失败臂 ONLY；240 块 1 次失败 ⇒ Clopper–Pearson 上界 ≈1.94% ≫ f≈1.25 处 1.045% 容限，`docs/ROADMAP-20260921.md` §2）。Stage-1 `k/240` 对内部 bar（fails ≤ 12，FER ≤ 5% 路线继续/停止门）**仅 report-only 上下文**，无裁决含义。
> - **门 (b)**：`f ≤ 1.3` 本臂基：worst-case（全触发，总行 208）`f_super=1.294947 ≤ 1.3` 按构造成立 **AND** 实测 `f_exp ≤ 1.3`（由门 (c) 蕴含）。
> - **门 (c)**：headroom = `1108.31 − E[leak]` ≥ **21.5 b**（⇔ 所需 N ≤ 570；20 b ⇒ N ≥ 612——不用；ROADMAP §8 项 6）。等效触发率 cap：`r ≤ (1086.81−1064)/40` = **57.0%**。
> - 判读：PASS（全三门）⇒ 向主线程报告（决策树 PASS 分支：P3 审计 → P5 n=1024）；FAIL（任一门，含救援不转化 ⇒ "悬崖不可救援"）⇒ 向主线程返回（决策树 FAIL 分支：P4 升为 S3 前置必经；本身即对 P4 的决定性输入）。**均不授权任何后续执行**。

出处：`P1_STAGE1_BATCH_END_REVIEW.md` §8（逐字节选，完整条以该文件为准）：

> ## §8 Route input to main thread (not a route adjudication — decision stays with main thread under a future DECIDE gate)
>
> - Gate-mapped outcome per frozen packet §4 (recorded, not裁决 by this review): **neither arm satisfies all three gates simultaneously** — R1: (a) FAIL (F=1/240≠0), (b) PASS, (c) PASS (30.48≥21.5); R2: (a) PASS (F=0), (b) PASS, (c) FAIL marginal (21.31<21.5 by 0.19 b; r=57.5% > 57.0% cap). … This batch therefore **does not constitute a P1-PASS ticket into P3 memory-audit DECIDE**; promoting R2's zero-fail alone while dropping its (c) FAIL and R1's (a) FAIL would be single-arm/single-gate cherry-picking, explicitly forbidden by the per-instance/claim-ceiling rules.

注：§5.2 第二段判读中的 "P4 升为 S3 前置必经" 属 **P1 包冻结时的决策树原文**，
其效力受 §5.1 F3 裁决约束（"P4 不因 P1-FAIL 自动升为 S3 前置必经"）——
两段均为**转录**，本文件不调和、不裁决二者关系，冲突处理权在主线程与用户。

### §5.3 ROADMAP P5 配置与样本量前提（`ROADMAP-20260921.md:224–228`，逐字）

> - **配置**：P1（或 P4）选定的冻结配置；Jan-21 三源；全部可用超帧
>   （n=1024：**500 / 691 / 911**；n=2048：**250 / 345 / 455**——非每源 2103/1051）。
> - **样本量前提**：只有在选定臂的 `f_super` 使 `⌈3·4.7857/(1.3−f_super)⌉` 小于
>   该源块数时，该源才能承载 headline 的 f_eff ≤ 1.3 断言；否则该源降级为诊断性。
>   **S3 的包必须在冻结前逐源列出这一判定表。**

（引文中的"选定"指未来包的冻结动作；本文件对该动作**无**判定、无预设。）

---

## §6 Claim ceiling 与 FORBIDDEN

**仅**：本草案结构本身（七元组、口径分离表、两分支对照、门前提状态、原文转录、空授权块），
供未来真实点门的包**引用**。

**非 / 上限锚**：
- owned-roadmap **M3**："安全观测量不足时只报告 reconciled/public-EC 结果，不冒充 secure key"；
  **M5**：measured / assumed / projected / qualified 四列必须分开，协议观测量 + 有限长度参数 +
  epsilon budget 全合格前无 secure-key 选点；
- TRACEABILITY **末段**："What this packet does NOT establish"（任何真实数据 FER/效率/泄漏/SKR、
  任何一般性优势、分配 simplex 最优性……）原样承接，本文件不扩大其外延；
- `P3_MEMORY_AUDIT_PACKET.md` §4 claim ceiling：记忆门 verdict 不是 FER/SKR/资格化/发表结论，
  对外句必须带"未证伪 ≠ 已验证 + 电池粒度"限定。

**FORBIDDEN（本文件与引用本文件的任何材料共同遵守）**：
- 改 `docs/ROADMAP-20260921.md` / `docs/EXECUTION_PLAN_20260922.md` /
  `docs/decision-log.md` / `docs/NOW.md` / `AGENTS.md` / `docs/troubleshooting.md`；
- 碰 **NOW / P3 族 / P4 族 / P1 族 / S0.1 族**文件；
- 执行任何解码、构造、真实数据访问、`tools/longrun_*|minrerun_*|routeA_*`、
  `experiments/run_e2e_pipeline.py`；
- **commit / push**；
- 跨源 / 跨构造实例合并任何计数或 FER；把 census raw-stream 计数与超帧口径混用；
- 把 `undetected` 并入 success/FER-as-quoted；把 `f_super` 当 `f_eff` 报；
- 把本文件读作执行授权、路线裁决、运行点选择或认证句来源。

**创建范围复述**：本任务**仅新增此一份文件**（本文件），无其他新增、无修改、无执行、
无 commit、无 push。

---

## §7 授权块（**全 BLANK** — 未填 = 未授权；本文件唯一填充处，且本文件不构成授权路径）

- Acceptance ID（拟）：`G-G0B-RP`
- grant verbatim：`[BLANK — 未授权，不得执行]`
- 分支 / HEAD（Pre-EXECUTE 实测记录，本文件不做 SHA 相等断言）：`[BLANK — 未执行]`
- 臂 / 机器根 UUID（fresh additive + 缺席证明）：`[BLANK — TO BE FROZEN AT PRE-EXECUTE]`
- 预算确认（**全部待填，本文件不设数**）：
  - ① 单窗口 wall 上限：`[TO BE FILLED AT PRE-EXECUTE]`
  - ② 批次总 ceiling：`[TO BE FILLED AT PRE-EXECUTE]`
  - ③ 单调用 / 单次构造帽（超时 = 终态，不续跑）：`[TO BE FILLED AT PRE-EXECUTE]`
  - ④ 峰值 RSS：`[TO BE FILLED AT PRE-EXECUTE]`
  - ⑤ CPU 数：`[TO BE FILLED AT PRE-EXECUTE]`
  - ⑥ 输出缺席 + 保护根快照字节一致 + `git diff -- src/` EMPTY：`[BLANK — 未检查]`
  - ⑦ focused fake-only 测试输出：`[BLANK — 未运行]`
- Pre-EXECUTE 记录：`[BLANK — 未执行]`
- 门前提状态（§4）：前提 1 不具备（P4 batch-end 不存在）；前提 2 无 verdict（P3 未授权）
  —— **事实记录，非裁决**
- 日期 / 主线程：`[BLANK]`
- 签名：`[BLANK]`

（未填 = 未授权。本文件不授权构造、不授权解码、不授权真实数据访问、不授权 commit/push、
不授权任何 P1 §9 / P2 / X1 / P3 / P4 / P5 臂。）
