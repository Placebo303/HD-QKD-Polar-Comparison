# REALPOINT NB1024 真实单点 Packet（G0=B 同批可测收益 · n=1024 S-B 窄路）— FROZEN DRAFT / NOT GRANTED / NOT AUTHORIZED / NOT EXECUTED

- 文件性质：**docs-only 冻结草案**（planner 窄路线大纲逐字落档，零新数值、零新阈值、零结果预设）。
  - Track（**本任务 = 建档**，恰其一）：**documentation-only — 无 track gate**（`AGENTS.md` §1.2 适用性矩阵
    "Documentation-only changes" 行）；**裁决权在用户**，本文件不代裁决、不预支裁决。
  - Track（**本包未来执行**，恰其一）：**DECIDE**（真实数据 + 报告/认证语境 —— §1.2 矩阵
    "Real-data development/validation" / "Publication/report numbers" 行）。预算与授权**全 BLANK**
    （§7/§10）⇒ 未冻结完成、未授权、未执行。
- 本文件**不授权任何执行**：零解码、零构造、零真实数据访问、零 `.ttbin`/`gamma` 读取、
  零 benchmark/smoke、零 commit/push、零 `results/` 与 `comparison_bench/outputs_comparison/` 写入。
- 创建范围（P4-3/G0B 式声明）：本任务**只新建本文件与 `REALPOINT_NB1024_PROMPT.md` 两份 docs**。
  **不改** `G0B_REALPOINT_GATE.md`、`SAME_DATA_CMP_METRICS.md`、**P3 族**（`P3_MEMORY_AUDIT_*` 等）、
  **P4 族**（`P4_FEAS_*` 等）、**TIMING 件**（`S2_TIMING_PROBE_20260920.md` 等）、`docs/NOW.md`、
  `docs/decision-log.md`、`AGENTS.md`、`docs/troubleshooting.md`、`docs/ROADMAP-20260921.md`、
  `docs/EXECUTION_PLAN_20260922.md`、`src/`/`experiments/`/`tools/`；工作树中的既有改动
  （`AGENT_PROJECT_MEMORY.md`、`docs/NOW.md`、p4 thin runner 与 fake-only 测试、
  `docs/research_cycles/EXPLORE-20260923-DIMENSION-PROBE/`、`openspec/changes/*` 等）**与本任务无关，原样保留**。
- 基线（provenance，非执行锁）：`8e9c8526`，分支 `formal-ir-v72p1-addendum-clean`
  （`AGENTS.md` §10.3：不做 SHA 相等断言；执行前 Pre-EXECUTE 实测重记）。
- 上游只读出处（本文件全部为重述/转录，零新数值、零新阈值）：
  - `docs/decision-log.md:4850–4859`（G0=B 裁决 + F3/F4）、`:4885`（P1 Stage-1 batch-end）、
    `:4897`（禁单点认证）、`:4901`（G-P1S1 授权用完）、`:4859`（P5 仍需独立冻结）、`:4438`（V80 q-prior：PRIMARY GF(32)²-layered / SECONDARY direct-q1024）；
  - `docs/research_cycles/V80-NBLDPC-JAN21/G0B_REALPOINT_GATE.md` §1（七元组）/§2（口径分离）/§4（门前提）/§6（claim ceiling）/§7（空授权块）；
  - `docs/research_cycles/V80-NBLDPC-JAN21/SAME_DATA_CMP_METRICS.md` §1–§9 与 §10（A-CMPE-1..7）；
  - `docs/research_cycles/V80-NBLDPC-JAN21/P1_STAGE1_PACKET.md` F2/F7/F9/F10/§4/§5、`P1_STAGE1_BATCH_END_REVIEW.md` §8；
  - `docs/research_cycles/V80-NBLDPC-JAN21/P3_MEMORY_AUDIT_PACKET.md` §2.1/§2.5/§4/§7；
  - `docs/research_cycles/V80-NBLDPC-JAN21/P4_FEAS_PACKET.md` F1/F2/F8/§10(a)；
  - `docs/ROADMAP-20260921.md:222–236`（P5 配置/样本量前提/会计/对照臂/门）与 `:259–277`（决策树 + 2026-09-21 修正）；
  - `docs/EXECUTION_PLAN_20260922.md` §3 **S-B**、`:217`（P3-gate FAIL 时禁把合成 FER 当真实 FER）、§5 门禁；
  - `docs/V80_BASELINE_20260921.md` §2 / §0.1 / §5-i（冻结会计与 retained-frozen）；
  - `docs/hd-qkd-ir-comparison-owned-roadmap-20260907.md` **M2–M5**（真实单点 → 公开开销闭环 → 扫描 → 安全资格与最终选点；measured/assumed/projected/qualified 必须分开）；
  - `docs/research_cycles/EXPLORE-20260923-DIMENSION-PROBE/TRACEABILITY.md` 末段（"What this packet does NOT establish" 承接句）。

---

## §0 本文件不做什么（全文有效）

1. **不裁决**：本文件对路线、分支（S-B / S-A）、运行点、帧长、模型**不作选择、不作判定**；
   七元组只做**冻结重述**，门前提只做**事实状态记录**。全文不含"选定 / 定案 / 裁决完成"式措辞
   （引文中出现的"选定"指未来包的冻结动作，本文件对该动作无判定）。
2. **无执行授权语句**：§10 授权块**全 BLANK**，未填 = 未授权；本文件不是授权路径，
   任何未来执行须走本包 Pre-EXECUTE + 显式用户授权。
3. **预算数值一律 `[BLANK — TIMING 帽定后填]`**（§7）：本文件不填预算数、不设 ceiling、
   不冻结 UUID、不代做输出缺席检查。
4. **引文为原文转录**（带出处行号/节号），转录不构成新裁决，也不放宽任何原文门。
5. **Claim ceiling（本文件最高产出）** = 一个待授权 DECIDE 包的**草案结构**：
   G0=B 定位 + 七元组 + 计数分离与认证语境 + 门前提 + 报告合同 + 空预算/空授权块。
   **非**：路线裁决、运行点选择、FER/`f_eff`/泄漏/SKR/资格化/发表句、
   可认证 `f_eff ≤ 1.3` 句、执行授权。

---

## §1 路线定位：G0=B 主攻同批可测收益

1. **G0 = (B) 已裁决**（2026-09-22 用户书面给出，`decision-log.md:4852` 逐字）：
   主文主张 = 实测效率（measured reconciliation efficiency）+ **同一数据上的 MLC/R3 对照**
   （same-data MLC/R3 comparison）；不选 (A) 文献可证成主张，不触发 (C) 新采集。
   → 本包主张面 = **同批（same-data）可测收益**：同一批 Jan-21 超帧、同一会计口径下的
   实测纠错收益 + 公开开销收益 + 同数据对照行。
2. **F3/F4 范围裁定**（`decision-log.md:4854–4857`）：F3 —— "P1 失败 ⇒ P4 在 S3 之前成为必经"
   分支被取代，**P4 不因 P1-FAIL 自动升为 S3 前置必经**，n=2048 定位**第二代并行**；
   F4 —— "f_eff ≤ 1.3 结构性拿不到"类表述**限定在冻结网格分辨率内**，不得外推，不构成对外认证句。
3. **同批对照臂（必做，转录自 `ROADMAP-20260921.md:232–234`）**：二元 MLC 基线重跑 + R3
   —— 同数据、同会计口径的最有说服力比较；历史口径义务（tagless/冻结口径、H 基、原生单遍综合征、
   **不可比即标**）按 `SAME_DATA_CMP_METRICS.md` §6 执行（A-CMPE-6）。
4. **S-B 窄路语境**（`EXECUTION_PLAN_20260922.md` §3 S-B）：S0.1 → P1 单段救援 → P3 →
   P5 n=1024（key-eligible 200/276/364；对照 = 二元 MLC + R3）→ P6 吞吐；P4 n=2048 作第二代并行。
   本包是该主路径下 **n=1024 真实单点**（owned-roadmap **M2** 新域真实单点）的候选冻结件草案。
5. **数据源语境（转录，非新设）**：Jan-21 三源 **1M / 1.5M / 2M**（CW 时间-能量纠缠、ToA 分箱；
   IR 只消费 `H(X|Y)`，与偏振/BBM92 无关 —— ROADMAP DECISION-3）；**分源报告、禁跨源合并**
   （统计量、计数、FER、判定一律逐源分列；"不得合并源凑通过" —— P3 §4）。真实数据访问 = **DECIDE** 合约。
6. **身份注记（事实记录）**：`decision-log.md:4859` 与 `docs/NOW.md` §5-2 记录 **P5 仍需独立冻结包
   （+ 显式授权）方可执行**；本包是否即该独立冻结包，由主线程与用户在授权门确定 ——
   **本文件不预判、不替代 P5-gate、不预授权**（前提 ≠ 授权，见 §4）。

---

## §2 冻结七元组（草案重述；改动任一 ⇒ 新包，不在本文件内修订）

| # | 分量 | 冻结值（重述，零改动；出处见右列） |
|---|---|---|
| 1 | **d** | **d = 1024**（ToA 分箱维数，HD-QKD 字母表维数）。禁止用 `d` 代表 `q` 或 `n_IR`。出处：owned-roadmap M2/M4、`P3_MEMORY_AUDIT_PACKET.md` §2.1、`G0B_REALPOINT_GATE.md` §2.1。 |
| 2 | **q** | **q = 32**（GF(32)，5 b/综合征符号 ⇒ `leak(m) = 5m + 64`，tag **64 b/超帧不翻倍**）；**分层 GF(32)×GF(32)**（原始 10-bit 标签 5+5 可逆**编码分层**，F03；`decision-log.md:4438`：PRIMARY GF(32)²-layered、SECONDARY direct-q1024 —— 后者本包**不开**，见 §6）。q 与 d、n_IR 分列，q 不代表 d、不代表 n_IR。出处：`V80_BASELINE_20260921.md` §2、`G0B_REALPOINT_GATE.md` §1-3、`nbldpc-v25-empirical-channel-and-factorization-plan-20260818.md` §6 F03。 |
| 3 | **n_IR** | **n_IR = 1024（S-B 窄路）**，单位 GF(32) 符号/超帧。禁止跨 n 直接并列计数或推单调性；**改长度（1024↔2048）= 新包**。出处：owned-roadmap M2/M4、`EXECUTION_PLAN_20260922.md` §3 S-B、`G0B_REALPOINT_GATE.md` §1-2/§2.1。 |
| 4 | **码构造** | **PEG 不规则族**（`family="peg-irregular"`，`λ={2:1}` edge-perspective，`ρ=make_rho(1−m/n)` 集中校验分布，`trials=20`，three-shift-cyclic 拒绝门）+ **构造谱系**（n=1024：**2026092001** girth 8 / **2026092011** girth 6，两实例**分列禁合并**，含跨实例 pins/计数相加禁止）+ **嵌套基**：基 `rows[0,200)`、单段披露 `rows[200,208)`（40 b）、**总行 208 ≤ 208 硬顶**（**NO warm-start / NO non-nested / NO two-segment**；两段/多段 OUT-OF-BOX，须另包）。出处：`P1_STAGE1_PACKET.md` F2/F2.1、`P4_FEAS_PACKET.md` F1/F2、`G0B_REALPOINT_GATE.md` §1-4。 |
| 5 | **先验 / gamma** | `gamma_f03.npz`（+ `gamma_f03_pb.npz`）= **一次性工厂标定、只读、永不重拟合**；复用事实 O1/O1R/P0/L1B/B2E/B2F/B2G/X1 保留；**跨源复用禁止**（X1 §4 —— 1M/1.5M bundle 须各自物化，每源自付标定成本）；**每源 1.50× 机会成本入账**（仓库 60/20/20 split ⇒ 先验成本 = 1.50× 它所开启的密钥；任何 SKR/净钥分子必须报告 forgone key）。**0.12–0.26× 与 1.8× 为已撤回数，不得作规划数**。出处：`V80_BASELINE_20260921.md` §5-i、`PRIOR_COST_CLAIM_REVIEW_20260921.md` §2c、`EXECUTION_PLAN_20260922.md` §3 S0.3、`decision-log.md:4787,4801,4827`、`G0B_REALPOINT_GATE.md` §1-5。 |
| 6 | **速率救援 + 认证判定** | **单段救援**（`m_base=200` → 总行 **208 硬顶**）；**bar**：内部 bar（fails ≤ 12，FER ≤ 5% 路线继续/停止门）**仅 report-only，不早停、不裁决**（该源解完全部计划超帧，不因 bar 停止）；**终态语义**：单调用超时 = 终态（块计 fail，不续跑）、`INCOMPLETE-wall` 保留不续跑、无 retry/resume/adaptive、"grant spent" 后无重跑；**`undetected` 单列并计为失败**（在失败集合内、**永不并入 success**）；**认证判定** = `N_req` **report-only** 与该源 key-eligible 计数**逐源**比较（n=1024 ⇒ **200/276/364**），谁认证得了逐源判定，**禁单臂/单门 cherry-picking**。出处：`P1_STAGE1_PACKET.md` F9/F10/§4、`P1_STAGE1_BATCH_END_REVIEW.md` §8、`ROADMAP-20260921.md:226–228`、`SAME_DATA_CMP_METRICS.md` §5-1/§1、`G0B_REALPOINT_GATE.md` §1-6。 |
| 7 | **预算 / 停止门** | **全部 `[BLANK — TIMING 帽定后填]`**：单窗口 wall 上限、批次总 ceiling、单调用/单次解码帽、峰值 RSS、CPU 数、机器根 UUID（fresh additive + 缺席证明）、输出缺席与保护根快照、focused fake-only 测试输出。停止规则**形状**重述自 `P1_STAGE1_PACKET.md` §5 / `P4_FEAS_PACKET.md` §5 / `P3_MEMORY_AUDIT_PACKET.md` §5（科学输入变动 ⇒ STOP；违禁读取/解码 ⇒ STOP-BLOCKED；wall-partial ⇒ 终态保留）；**数值本文件不填，本文件不设授权路径**（详见 §7）。出处：`G0B_REALPOINT_GATE.md` §1-7。 |

**τ 注记**：τ（时间/门控参数，owned-roadmap M4 扫描轴）**沿用所引用包的冻结口径，本包不新设 τ 数值**
（`G0B_REALPOINT_GATE.md` §1-2 同形）。

**变更规则**：七元组任一分量的值、单位、口径或判定规则发生改动（含**改长度、改模型** —— 信道/先验/
生成器/解码器形态）= **新包**（+ 必要的 OpenSpec），不得原地静默改写本文件（P3 §6 / G0B §1 同形）。
详见 §9。

---

## §3 计数与口径分离 + 认证语境

### §3.1 三组计数严格分离（永不出现在同一分母里；分组小计，禁换算、禁相加、禁替代）

| 分组 | 口径 | 单位 | 数值 | 禁止 |
|---|---|---|---|---|
| ① **合成** | 合成 240 块族（S0.1 / P1 Stage-1；两构造实例分列） | 配对块 / 臂 | **240 / 臂** | 禁与真实超帧、key-eligible、探针换算/相加；**合成 FER 不得当真实 FER** |
| ① **合成**（探针） | 维度探针格点帧数 | 帧 / 格点 | **1200 帧 / 格点** | 禁并入 240 块族；不同格点/分组方案禁合并 |
| ② **真实** | 真实超帧 **n=1024** | 超帧 / 源 | **500 / 691 / 911**（池 2000/2767/3645 帧 ⇒ 2103 合计） | **非**认证计数；禁与 key-eligible 混用 |
| ③ **key-eligible** | 牺牲标定样本后可承载认证判定的计数（sacrifice-the-sample DEFAULT） | 认证计数 / 源 | **200 / 276 / 364**（池 840） | **唯一**认证判定口径；禁用 500/691/911 冒充（2.5× 高估） |
| **另量纲**（不在①②③内） | census raw-stream 计数 | 原始流记录 | **129763 / 180536 / 239420** 量级 | **禁混用、禁替代**超帧口径；不得换算进任何分母 |

（转录自 `G0B_REALPOINT_GATE.md` §2.2、`SAME_DATA_CMP_METRICS.md` §5-3。n=2048 语境
250/345/455 与 N_req 338 **仅前向引用、不属本包** —— 改长度 = 新包。）

### §3.2 N_req 认证语境（report-only）

1. **`N_req` report-only**：`N_req = ⌈3·4.785675/(1.3 − f_super)⌉` 只作报告行，标 "report-only"，
   **不作操作点选择**（`SAME_DATA_CMP_METRICS.md` §5-1；`ROADMAP-20260921.md:226` 与
   `G0B_REALPOINT_GATE.md` §1-6 同式作 `⌈3·4.7857/(1.3 − f_super)⌉`）；与 **key-eligible 200/276/364**
   分列对比，**谁认证得了逐源判定**。
2. **既有实测事实（report-only 引用，非本包预测）**：P1 两臂 N_req **402 / 575** > key-eligible
   200/276/364 ⇒ **无已选运行点、禁单点 `f_eff ≤ 1.3` 认证句**（`decision-log.md:4897`；
   与 X1 joint 可认证集 = ∅ 一致）；**可给实测效率曲线**。
3. **逐源可认证判定表**：`ROADMAP-20260921.md:226–228` 要求该判定表在包冻结前逐源列出；
   本包**不代列**（per-source H 修正语境见 `V80_BASELINE_20260921.md` R1 修正案 +
   `R1_PRERESULT_REVIEW.md` §§3–4，report-only 引用），由主线程/用户在授权冻结时给出。
4. `d` / `q` / `n_IR` 三个参数**各自成列，不合并、不互相代表**（§2；`SAME_DATA_CMP_METRICS.md` §5-2）。

---

## §4 门前提（前提状态 = 事实记录，非裁决、非授权）

1. **P3 verdict 前提**：`P3_MEMORY_AUDIT_PACKET.md` 版本头 = **FROZEN — NOT GRANTED —
   NOT AUTHORIZED — NOT EXECUTED**；§2.5 的 T-M1..M4 为 **PROPOSED — re-freeze v2**、T-C0 = REUSED；
   §7 授权签字块**全 BLANK** ⇒ **当前无 verdict**。后果（事实）：**禁把合成 FER 当真实 FER**
   （`EXECUTION_PLAN_20260922.md:217`）；"未证伪 ≠ 已验证 + 电池粒度"限定强制保留（P3 §1/§4）。
2. **P1 Stage-1 事实**（`P1_STAGE1_BATCH_END_REVIEW.md` §8、`decision-log.md:4885/4897`）：
   R1 `2026092001` FAIL(a)（F=1/240）、R2 `2026092011` FAIL(c)（21.31 < 21.5 b，差 0.19 b；
   r=57.5% > 57.0% cap）；**无一臂同时满足三门**；机械救援有效与门结论是两回事；
   **G-P1S1 授权已用完**（`decision-log.md:4901`）⇒ 本包不在 G-P1S1 下运行，任何重跑须新 packet + 新授权。
3. **G0=B F3**：P4 不因 P1-FAIL 自动升为 S3 必经；n=2048 第二代并行（§1-2）。
4. **P5-gate**：P5 仍需独立冻结包 + 显式授权方可执行（`decision-log.md:4859`、`docs/NOW.md` §5-2）；
   本包**不替代** P5-gate、**不预授权**（§1-6 身份注记）。
5. **入口语境**（`P4_FEAS_PACKET.md` §10(a) 同形）：P1 Stage-1 P4-elevation 输入 + G0=B F3 +
   用户顺序 ①→③→② —— **三者是冻结前提，不是授权**。

**前提 ≠ 授权**：前提的满足、不满足及其后果由主线程与用户在未来门上处理；本文件**不补做、不催做、
不授权补做**任何一项（P3 执行、verdict 获取、P5 冻结均不在本文件范围）。

---

## §5 报告口径义务（报告合同；逐项覆盖，缺项 = Pre-RESULT FAIL）

1. **报告合同 = `SAME_DATA_CMP_METRICS.md` §10 验收项 `A-CMPE-1 … A-CMPE-7`**（ID 稳定，回报只引用 ID）：
   per-source 四计数独立列（`attempted` / `exact_match`=¬failed（`decoded`≠success 图例）/ `accepted` /
   `accepted_wrong`=`undetected`）；`f_super`/`f_eff` **双数并列**（本臂 m 基：m=202 → 1.259759、
   m=208 → 1.294947，**绝不互替、绝不把 f_super 当 f_eff 报**）；实际公开比特
   `leak_EC` + 64-bit tag ⇒ verification-aware `λ_total`，完整协议链逐项列开 + **每源 1.50× prior 机会成本行**；
   资源与交互（总/每块/每译码 wall + 峰值 RSS + 消息数；IR 吞吐与采集率分标）；`N_req` report-only vs
   key-eligible（200/276/364）+ `d`/`q`/`n_IR` 分离 + 三组计数分离；R3/MLC 历史口径标注与
   **不可比即标** + r=10 native≈9× 成本行独立 + 探针不替真实结论固定句；无安全观测量 ⇒ 仅
   "实测纠错/公开开销收益"、**禁 SKR** + 每个数字落 **measured/assumed/projected/qualified** 四列之一。
2. **会计恒等式（n=1024 冻结重述，非门）**：H_anchor=0.83256272 b/sym ⇒ content=**852.544 b**；
   cap=1.3×852.544=**1108.31 b**；`f_super=(5m+64)/852.544`；基线 leak **1064 b** ⇒
   `f_super=1.248029`（m=200）；全触发 worst-case leak **1104 b** ⇒ `f_super=1.294947 ≤ 1.3`（按构造恒等）；
   斜率 **4.785675**；A208 余量 **4.3075 canonical（4.31 rounded）**；`f_eff = f_super + 4.785675·FER`
   （FER 项用本臂自己的 m 基）；`λ_total = leak_EC + 64`（≡ ε_EV ≈ 2⁻⁶³）。出处：`V80_BASELINE_20260921.md`
   §2、`P1_STAGE1_PACKET.md` F7、`SAME_DATA_CMP_METRICS.md` §2/§3。
3. **终态与失败语义**：超时 = 终态（块计 fail，不续跑）；`INCOMPLETE-wall` 单列保留；
   `undetected` 单列、计为失败、永不并入 success；禁把 `reference/stub/unavailable/decode_failed/
   no_verified_success` 静默转成 `ok`（`AGENTS.md` §5.5）。

---

## §6 范围外 / 暂不开 / 文献定性（执行面与本文件共同遵守）

1. **暂不开 A1**（本包不启动 A1 相关臂/线；其外延不在本文件定义，开启须另包 + 独立授权）。
2. **暂不开全 q**（direct-q1024 / 原始 1024 字母表直接编码路线 —— SECONDARY，
   `decision-log.md:4438`；本包只走 §2-2 的 GF(32)×GF(32) 分层）。
3. **暂不开 SKR**：secure-key / 净钥 / 资格化 / composable 安全 / publication claim 全部范围外
   （owned-roadmap M3/M5；`v80-prior-cost-accounting` claim-ceiling SHALL）。
4. **Mitra / Müller = 选型依据，非胜出证据**：其文献只支撑"为什么选这条路线"（NB-MLC、分层、
   信道知情设计、方向可行性），**不得**引作本包方法胜出、可比性能或认证证据
   （其 QSC / q=8 / 长帧 / 二元口径与本项目不同；引用纪律与禁令见 `decision-log.md:4665/4672/4689`、
   `nonbinary-ldpc-efficiency-roadmap-survey.md`、`nbldpc-v25-empirical-channel-and-factorization-plan-20260818.md` §表）。
5. **其他 FORBIDDEN（全文有效）**：禁跨源/跨构造实例/跨臂合并任何计数或 FER（含 6+4 式求和）；
   禁 census raw-stream 与超帧口径混用；禁 `undetected` 并入 success/FER 分子；禁把 `f_super`/`f_exp`
   当 `f_eff` 报；禁单点 `f_eff ≤ 1.3` 认证句；禁单臂/单门 cherry-picking；禁把 6.7 kbit/s 说成
   SKR/IR 吞吐；禁把数据说成 BBM92 偏振层；禁引撤稿 Mao；禁只报单源/单实例冒充通用性；
   禁改 §2 七元组任一值；禁跑 `tools/longrun_*|minrerun_*|routeA_*`、`experiments/run_e2e_pipeline.py`；
   **禁 commit / push**；禁把本文件读作执行授权、路线裁决、运行点选择或认证句来源。

---

## §7 预算 / 停止 / 失败保留（全 BLANK；TIMING 帽定后填）

- **预算数值一律 `[BLANK — TIMING 帽定后填]`**：
  ① 单窗口 wall 上限；② 批次总 ceiling；③ 单调用/单次解码帽（超时 = 终态，不续跑）；
  ④ 峰值 RSS；⑤ CPU 数；⑥ 机器根 UUID（fresh additive + 缺席证明）；⑦ 输出缺席 + 保护根快照
  字节一致 + `git diff -- src/` EMPTY；⑧ focused fake-only 测试输出。
  **填入顺序**：TIMING 帽（单调用/单窗口 wall 上限，由主线程依 timing 证据裁定 ——
  `S2_TIMING_PROBE_20260920.md` 为既有 timing 参考件，report-only，其 smoke 结果无 FER 含义）
  → Pre-EXECUTE 把预算槽填实 → 授权块（§10）填全 → 才可执行。本文件**不填任何预算数、不设
  ceiling、不冻结 UUID、不代做输出缺席检查**；执行者**不得自行填数**。`unspent budget ≠ authorization`。
- **停止规则形状（重述，不填数）**：任何科学输入变动（n/m/tag/H/λ/ρ/seeds/阈值/信道/解码器/
  假设/数据角色）⇒ STOP；任一违禁读取/解码调用 ⇒ STOP-BLOCKED；wall-partial ⇒ **`INCOMPLETE-wall`
  保留、永不续跑**；**无 retry/resume/adaptive**；"grant spent" 后无重跑。
- **失败保留（DECIDE）**：DECIDE 不可变失败保留；**无预注册工程修复+重跑条款**（与 EXPLORE 不同）；
  任何重跑 = 新 packet + 新授权 + 新根（`AGENTS.md` §1.2 DECIDE 合约、`P3_MEMORY_AUDIT_PACKET.md` §3-失败保留）。
- **根与 no-overwrite**：新输出仅入 fresh additive 根（族名授权时冻结）；`results/`、
  `comparison_bench/outputs_comparison/`、既有证据根**一律只读**。

---

## §8 Claim ceiling 与上限锚

**仅**：同批（same-data）**可测收益**报告面 —— 实测纠错效率（`f_super`/`f_eff` 双数、分源、逐实例分列）、
公开开销（`leak_EC`、64-bit tag、控制轮次、每源 1.50× prior 行）、接受率与 `undetected` 单列、
运行资源，及与同数据 MLC/R3 对照齐备的报告行；+ 本草案结构本身（七元组、计数分离、门前提、
报告合同、空授权块）供未来真实点门的包**引用**。

**非 / 上限锚**：
- owned-roadmap **M3**："安全观测量不足时只报告 reconciled/public-EC 结果，不冒充 secure key"；
  **M5**：measured / assumed / projected / qualified 四列必须分开，协议观测量 + 有限长度参数 +
  epsilon budget 全合格前无 secure-key 选点；
- 单点 `f_eff ≤ 1.3` 认证句（N_req 402/575 > 200/276/364、joint 可认证集 = ∅ —— `decision-log.md:4897`）；
- TRACEABILITY 末段 "What this packet does NOT establish" 原样承接，本文件不扩大其外延；
- `P3_MEMORY_AUDIT_PACKET.md` §4 claim ceiling（"未证伪 ≠ 已验证 + 电池粒度"限定强制保留）；
- `v80-prior-cost-accounting` claim-ceiling SHALL（prior 成本、forgone key 报告义务）；
- 路线裁决、运行点选择、A1/全 q 结论、SKR/资格化/发表材料 —— 一律不在本包。

---

## §9 修订规则（改长度 / 改模型 = 新包）

1. 七元组任一分量的值、单位、口径或判定规则发生改动（含**改长度 1024↔2048、改模型** ——
   信道/先验/生成器/解码器形态）= **新包**（+ 必要的 OpenSpec），**不得原地静默改写本文件**
   （P3 §6 / G0B §1 修订规则同形）。
2. 报告口径（§5）、门前提（§4）、claim ceiling（§8）的任何放宽 = 包修订（re-freeze + 新版本号），
   不得静默改写。
3. §7 预算槽与 §10 授权块的**填入不属修订**（其唯一填充处即 §7/§10，且按 §7 顺序在
   TIMING 帽定后 / 授权时填）；填入前**未填 = 未授权**。

---

## §10 授权门（EXPLICIT USER GATE — 停在这里）+ 授权块（全 BLANK）

- **本 packet 冻结草案 ≠ 授权。任何执行前必须同时满足：**
  (a) §4 门前提状态已记录（P3 无 verdict 的后果句、P1 事实、F3、P5 独立冻结要求、入口语境三前提）；
  (b) **P3 verdict 前提已记录**且后果句（禁把合成 FER 当真实 FER + "未证伪≠已验证 + 电池粒度"）
      写入执行记录（执行面清单见 PROMPT §4）；
  (c) **TIMING 帽已定 + §7 预算槽 ①–⑧ 全部填实**（填入顺序见 §7；倒序/缺项 = STOP）；
  (d) **Pre-EXECUTE PASS** 并记录：分支/HEAD 实测、范围清洁（白名单 + `git diff -- src/` EMPTY +
      脏树按显式文件清单界定）、冻结契约 §2 逐项核对、确切命令冻结（占位，授权时冻结）、
      输出缺席（目标根不存在 + 保护根快照字节一致）、focused fake-only 测试 PASS 并附输出；
  (e) **FRESH EXPLICIT USER GRANT**，填入下方授权块（签名，或本周期 verbatim 对话授权记录 ——
      F-3/X1/X1S 先例，仅限本周期）；
- **未授权不得执行。** 本文件不授权解码、不授权构造、不授权真实数据访问、不授权测试长跑、
  不授权 commit/push、不授权任何臂。

### §10 授权块（**全 BLANK** — 未填 = 未授权；本包唯一授权填充处）

- Acceptance ID（拟）：`G-REALPOINT-NB1024`
- grant verbatim：`[BLANK — 未授权，不得执行]`
- 分支 / HEAD（Pre-EXECUTE 实测记录，本文件不做 SHA 相等断言；冻结时点基线 `8e9c8526`）：`[BLANK — 未执行]`
- 机器根 UUID（fresh additive + 缺席证明）：`[BLANK — TO BE FROZEN AT PRE-EXECUTE]`
- 预算确认（**全部待填，本文件不设数**；TIMING 帽定后填）：
  - ① 单窗口 wall 上限：`[BLANK — TIMING 帽定后填]`
  - ② 批次总 ceiling：`[BLANK — TIMING 帽定后填]`
  - ③ 单调用 / 单次解码帽（超时 = 终态，不续跑）：`[BLANK — TIMING 帽定后填]`
  - ④ 峰值 RSS：`[BLANK — TIMING 帽定后填]`
  - ⑤ CPU 数：`[BLANK — TIMING 帽定后填]`
  - ⑥ 输出缺席 + 保护根快照字节一致 + `git diff -- src/` EMPTY：`[BLANK — 未检查]`
  - ⑦ focused fake-only 测试输出：`[BLANK — 未运行]`
- 确切命令（uuid 占位，授权时一次性冻结）：`[BLANK — 未冻结]`
- 门前提状态（§4）：P3 **无 verdict**（包 NOT GRANTED、§7 全 BLANK）；P1 无一臂全过三门、
  G-P1S1 已用完；P5 仍需独立冻结 —— **事实记录，非裁决**
- Pre-EXECUTE 记录：`[BLANK — 未执行]`
- 独立 Pre-RESULT verdict：`[BLANK — 未执行]`
- 主线程接受：`[BLANK — 未接受]`
- 日期 / 主线程：`[BLANK]`
- 签名：`[BLANK]`

（未填 = 未授权。本文件不授权构造、不授权解码、不授权真实数据访问、不授权 commit/push、
不授权任何臂；本 prompt 与本 packet 授权任何执行 = 0。）

---

## §11 本任务（planner 大纲落档）创建范围声明

- 本任务**只新建**本文件与 `REALPOINT_NB1024_PROMPT.md` 两份 docs；**未执行**任何解码/构造/
  测试长跑/真实数据访问/benchmark/smoke；**未改动** `G0B_REALPOINT_GATE.md`、`SAME_DATA_CMP_METRICS.md`、
  P3 族、P4 族、TIMING 件（`S2_TIMING_PROBE_20260920.md`）、`docs/NOW.md`、`docs/decision-log.md`、
  `AGENTS.md`、`docs/troubleshooting.md`、`docs/ROADMAP-20260921.md`、`docs/EXECUTION_PLAN_20260922.md`、
  `AGENT_PROJECT_MEMORY.md`、`src/`/`experiments/`/`tools/`、既有 runner/测试、S0.1/P1 族文件
  或任何其他文件（工作树既有改动原样保留）；**未 commit、未 push**。
- 科学阈值未动：1.3 门、`λ_total = leak_EC + 64`（≡ ε_EV ≈ 2⁻⁶³）、tag 64 b、H_anchor 0.83256272、
  content 852.544 / cap 1108.31 / 斜率 4.785675、`leak(m)=5m+64`、m1+m2≤208 硬顶、A208 余量
  4.3075 canonical（4.31 rounded）、N 规则、key-eligible 200/276/364、bar fails≤12/FER≤5% report-only、
  `undetected` 隔离、每源 1.50×、禁合并 —— 全部**重述**自上游冻结件，零改动。
- 结果数值未预设：本包无任何结果预测（无 FER/f/headroom/成功率/通过判定预测）；§3-2 引用的
  402/575、FAIL(a)/FAIL(c) 等均为**既有实测事实的 report-only 引用**，非本包预测。
- 范围收紧项（planner 大纲）：**暂不开 A1 / 全 q / SKR**；**Mitra/Müller 标选型依据、非胜出证据**；
  预算全 BLANK（TIMING 帽定后填）；授权全 BLANK；改长度/改模型 = 新包。
