# P4 n=2048 构造可行性 Packet (2026-09-23 · **v2 re-freeze 2026-09-24 — “M2改prompt就runner”**) — FROZEN, NOT GRANTED

- 任务 IDs：**P4-1**（本文件 = prereg + 冻结科学输入 + 授权边界）/ **P4-2**（配套执行面 `P4_FEAS_PROMPT.md`）/ **P4-3**（本任务范围禁令，见 §11）。
- Acceptance ID（拟）：**G-P4FEAS**。本文件是冻结件，**不是授权**；授权任何执行 = 0。**未授权不得执行。**
- Track：**EXPLORE**（零解码、便宜、有界、可逆；无 `EXPLORE_HEAVY` 注记——见 §7）。
- 分支 / 基线：`formal-ir-v72p1-addendum-clean` / **`8e9c8526`**（冻结时点；不切分支、不 commit、不 push；实际 HEAD 在 Pre-EXECUTE 重测记录）。
- 计划出处：`docs/ROADMAP-20260921.md` P4（§3 触发条件/算术/块数代价/子臂/代价/轨道）+ §4 决策树 FAIL 分支 + §2 DECISION-1（双数并列、本臂基、零失败臂认证规则）+ §8 复核项 5（1.25734→1.25741）；
  `docs/V80_BASELINE_20260921.md` §2（`f_super=(5m+64)/852.544`、content=852.544 b、slope 4.785675、m1+m2≤208 硬顶、A208 余量 4.3075 canonical、λ_total=leak_EC+64 ≡ ε_EV≈2⁻⁶³）+ §0.1 retained-frozen（no-pooling、`undetected` 隔离、no f_super-as-f_eff）；
  `docs/EXECUTION_PLAN_20260922.md` §3 **S0.2**（P4 构造可行性 n=2048 PEG/联合图、零解码、EXPLORE、无依赖、便宜）+ §3 S-A（G0=(A) 主路径首步 S0.2 必须 PASS）+ §5 门禁；
  AGENTS.md §1.2（EXPLORE 两文件制 + 合约）+ §10.3（单次 batch-end）+ 轨 P P-1。
- 上游证据语境（只引用、不重证）：X1 route-gate `m_min` = 2M **204** / 1.5M **203** / 1M **197**（冻结网格分辨率；between-grid 未映射）+ **joint 可认证集合 = ∅**（route-pass ∧ count-certifiable，key-eligible **200/276/364**）；
  **P1 Stage-1 最新事实**（`P1_STAGE1_BATCH_END_REVIEW.md` PASS_WITH_FINDINGS + decision-log 2026-09-23 两条）——
  R1（2026092001/girth8）：Stage-1 k=84/240 → rescued 83/84 → 最终 F=1/240、f_eff=1.284196、headroom 30.48 b → **FAIL(a)**；
  R2（2026092011/girth6）：k=138/240 → rescued 138/138 → 最终 F=0/240、f_eff=1.275008、headroom 21.31 b vs gate 21.5 b（差 0.19 b）→ **FAIL(c)**；
  N_req 402/575（report-only）> key-eligible 200/276/364 ⇒ n=1024 上无一臂同时满足三门；
  机械结论（rescue 在冷全矩阵形态下有效，221/222 转化）与门结论（无一臂全过）是两回事，后者才进决策树。
- G0 与路线顺位语境（冻结前提，不是授权）：
  G0=B 已裁决（decision-log 2026-09-22：主文 = 实测效率曲线 + 同数据 MLC/R3 对照；F3 取代 ROADMAP" P1 失败 ⇒ P4 自动升为必经"——P4 不因 P1-FAIL 自动升格，第二代并行定位）；
  2026-09-23 落档把 P1 Stage-1 判为 **P4-elevation 输入**（不是 P1-PASS 通往 P3 的门票）；
  用户路线裁决（本次冻结任务给出）：按 **① P4-elevation → ③ 并行 → ② S-B 窄路**顺序推进，本包是路线 **① 入口**。
  **本包不裁决 P4 是否升为 S3 必经，只产出可行性证据**（见 §4 末、§9）。
- 配套 prompt：`P4_FEAS_PROMPT.md`（两文件制）。批次日志（执行时新建，append-only）：`P4_FEAS_EXPLORATION_LOG.md`；批次末独立评审（执行后）：`P4_FEAS_BATCH_END_REVIEW.md`。本包不新建其他执行文件。

## §1 目的与假设（测，不宣称）

1. **目的**：在冻结 PEG 族下实测 n=2048 构造可行性——两构造实例各构造一个全矩阵（n=2048、m=416、λ={2:1}、ρ 集中、trials 20），验证构造 pins（fc=0 + rank-full + twice-identical GATED；girth 记录不设门）与 nested 基能力（leading-400 rank-400 REQUIRED），**零解码调用**（`decode_calls=0` REQUIRED）。回答"S0.2：(A) 是否物理可行"中**构造一半**的问题；DE 阈值点（P2 可并入）不在本包。
2. **假设（待测，非主张）**：O1 族在 n=1024 上 PEG 构造可行（A188/A208/A202/A200/A192/A196 既有 pins）⇒ 同族在 n=2048 同速率点构造可行；本包只测构造 pins，不测阈值、不测 FER、不测 rescue 转化。
3. **预注册非预测（P4-3 禁令执行）**：以下全部是 **MEASURED 结果，无点预测**——每臂 fc、rank（full/base）、twice-identical、girth、family、wall/RSS（逐臂）。ROADMAP 的条件算术（m=416 ⇒ leak 2144 ⇒ f=1.25741 ⇒ 余量≈72.6 b ⇒ N≥338）**仅作算术引用**，不是臂预测；既有 n=1024 的 fc=0/girth8(6)/rank-full pins **不得**跨 n 预设为本包结果；平均校验度、wall、girth 无一数字预测。本包冻结计算规则（§3）与门（§4），永不冻结结果数值。

## §2 冻结科学输入（改动任一项 ⇒ STOP，回主线程；必要时先 OpenSpec）

| # | 项 | 冻结值 |
|---|---|---|
| F1 | 臂数 | **恰好 2 臂**：`P4F-R1` 构造谱系 **2026092001**（n=1024 girth 8 记录值）；`P4F-R2` 构造谱系 **2026092011**（n=1024 girth 6 记录值）。**分别报告，禁合并**（含跨实例 pins/计数相加）。**新实例规则**：两谱系整数是 n=2048 构造的 RNG 种子（沿用）；若构造器要求新种子（冲突/不可用），执行者**不得自行发明**⇒ STOP 回主线程并附论证，新实例需主线程另决（"沿用/或新实例需论证"即此门）。 |
| F2 | 构造（单矩阵 + nested 基能力） | PEG 不规则族：**n=2048 GF(32) 符号，m=416，λ={2:1}**（edge perspective，O1 族同形），**ρ=`make_rho(1−416/2048)=make_rho(0.796875)`** 集中校验分布（`nonbinary_v26_mcde.make_rho` 只读复用，P2 §2 先例），**trials=20**（O1 族同值），field GF(32)，`family="peg-irregular"` 戳记 + **three-shift-cyclic 拒绝门**（`refuse_three_shift_cyclic`，v80_s2_peg 冻结语义）。全矩阵 = rows[0,416)。**Nested 基能力**（未来冷救援可测性，不在本包执行）：leading-400 rows[0,400) 必须 rank-400（P1 200→208 Δm=8 按速率缩放到 400→416 Δm=16 的构造对应物；本包只验 pins，不披露、不解码、不冻结 Stage 执行——Stage 是否沿用 cold nested 由未来解码包另决）。**NO 第二矩阵族**（平均校验度见 F2.1）；**NO 非 PEG 族**。 |
| F2.1 | 联合图（A2）处置与 19.7 注记 | 本包构造的矩阵即 **PEG@2048 / 联合图共用构造**：矩阵本身是信道无知的图 + GF(32) 标号，"L2 延长"与"joint A2 单因子图"的区别在未来 sampler/解码器用法（JOINT (u1,u2) vs L2 bundle，P2 §2），**不在本包矩阵构造**——故不另冻第二矩阵。`S2_ROUTE_DECISION_MEMO` L25 的"平均校验度 19.7"是 **m≈208 算术**（4096 edges/208），已被 P2 §2 明确 SUPERSEDED（m=416  governing）：冻结 m=416 下 dv=2 ⇒ 4096 edges/416 ⇒ **≈9.85**，与 n=1024 A208 的 9.8 同一健康区间，**明确不是** L1 稠密病理（256–341）。19.7 不得再引为本包设计数。 |
| F3 | 种子 / 流 | 构造 RNG 种子 = F1 两谱系整数（`peg_construct(2048,416,λ,ρ,seed,trials=20,field)` 逐字）；**无配对块、无 block seeds、无 stream `o1_blk:{seed}`**（零块、零解码——与 S0.1/P1S1 的 240 块族有本质区别）。**FRESH 性**：n=2048 矩阵是新对象，与 n=1024 A208 矩阵**无同一性主张**（同种子整数 ≠ 同矩阵；维度不同）。Pre-EXECUTE 以 rg 证明 n=2048 构造种子字面仅命中本包族。 |
| F4 | 信道 | **无**——构造是信道无知的，**零 `.ttbin` 读取、零 `gamma_f03*.npz` 读取/refit**（任一读取 = STOP-BLOCKED；构造不需要 bundle，读了即越界）。 |
| F5 | 先验/解码器 | **无**——**零解码调用**（`decode_calls=0` REQUIRED，全程）；无先验公式、无 v28、无 max_iter/streak、无 exact_match（仅未来包的前向引用）。任一生产解码 = STOP-BLOCKED。 |
| F6 | 构造 pins（dry + 执行 MEASURED，零解码） | 全矩阵：**`fc=0` GATED + `rank==416` GATED + twice-identical GATED**（同源 triples 构造两次逐字节一致；O1/X1/P1S1 先例），否则 **STOP-BLOCKED**；基码：**`rank(rows[0,400))==400` REQUIRED**，否则 **STOP-BLOCKED**；girth **measured/recorded/not-gated**（逐实例记录）；family 戳记 + three-shift-cyclic 拒绝；sockets/parity **recorded**（O1 先例，非门）。 |
| F7 | 会计（冻结恒等式，非门） | 见 §2.1 口径延拓。单 anchor 基：H_anchor=0.83256272 b/sym ⇒ content_2048=2048×0.83256272=**1705.088 b**；cap=1.3×1705.088=**2216.61 b**；`leak(m)=5m+64`（tag **64 bits 每超帧，不翻倍**）；m=416 ⇒ leak **2144 b** ⇒ `f_super=2144/1705.088`=**1.25741**；headroom=2216.61−2144=**72.61 b**（≈72.6）；斜率 **4.785675**（m/n 恒定时尺度不变，ROADMAP §8）；`N_req=⌈3·4.785675/(1.3−1.25741)⌉`=**338** report-only（仅零失败相关）；λ_total=leak_EC+64（≡ε_EV≈2⁻⁶³）**形式不变**。**绝不把 f_super 当 f_eff 报**。单基，**不另算第二基**（per-source H_MM 基不在本包）。 |
| F8 | 认证语境 | **key-eligible 200/276/364 仅引用为语境，本包一个也不消耗**（零块）；N 规则 report-only：338 **仅当未来零失败解码臂才相关**，无 N 预设；**本包不作任何可认证/文献可比 `f_eff≤1.3` 主张**（X1 joint-∅ 不被本包触碰）。前向语境（S-A 用，不在本包裁决）：n=2048 下每源块数 250/345/455 ⇒ 1M 源（250<338）若走 (A) 须降级为诊断性，headline 由 1.5M/2M 承担（ROADMAP §3–§4）。 |
| F9 | 早停 / 块循环 | **N/A**（无块循环，无 bar-12）：每臂恰好一次构造（+ 一次 twice-identical 复构 = 2 次 `peg_construct` 调用/臂）。wall-partial ⇒ `INCOMPLETE-wall` 保留、永不续跑（§5）。 |
| F10 | 失败类别 | 构造 FAIL = pin 门 miss（fc≠0 / rank≠full / 两次不一致）或异常；`INCOMPLETE-wall` 单列；**`undetected` N/A**（零解码 ⇒ 无综合征 ⇒ 无 undetected 列；任何解码形态输出 = STOP-BLOCKED）。 |

### §2.1 n=2048 口径延拓说明（冻结重述，不改科学阈值）

- 超帧口径从 n=1024 延拓到 **n=2048 GF(32) 符号**，H_anchor **不变**（0.83256272 b/sym，V80_BASELINE §2 整帧含 64-bit tag 冻结口径；per-source H_MM 不在本包另算）。
- content 线性缩放：852.544 b → **1705.088 b**（2048×0.83256272）；cap 同比：1108.31 b → **2216.61 b**。
- 每帧综合征预算翻倍是因为 **m 按速率翻倍**（208→416，rate 1−416/2048=0.796875 与 A208 的 0.796875 同值），公式形状不变：`f_super=(5m+64)/(2048·H_anchor)`；tag 保持 **64 bits/超帧**（不翻倍），tag 占比 0.0751→**0.0375**（O-B 行）。
- 科学阈值**零改动**：1.3 门、λ_total=leak_EC+64（≡ε_EV≈2⁻⁶³）、tag 比特数、H_anchor、斜率 4.785675、N 规则 `⌈3·4.785675/(1.3−f)⌉`、`undetected` 隔离、禁合并——全部重述自 V80_BASELINE §2/ROADMAP §2，形状不变，只是分母 n 从 1024 换成 2048。
- 块数代价（前向引用，不消耗）：n=2048 下 1M/1.5M/2M = 250/345/455 超帧（ROADMAP §1.2 表）；认证 N≥338 ⇒ 1M 源不可认证（250<338）——这是未来 S-A 包的判定表输入，不是本包结论。

## §3 度量与产出模式（冻结计算规则）

- 逐臂（`construction.json` + pins 报告，列名与 O1/X1/P1S1 构造段同构）：`arm, construct_seed, n, m, lambda_edge, rho_edge, trials, family, four_cycles, rank_full, rank_base_400, twice_identical, girth, sockets, parity, wall_s, rss_peak, H_anchor, content_2048, f_super_416, headroom_ctx, N_req_ctx, claim_ceiling`。
- 逐臂会计恒等行（§2 F7 逐字）：content_2048=1705.088、leak=2144、f_super=1.25741、headroom 72.61 b、N_req 338（report-only）——**恒等行，非 f_eff**（零解码 ⇒ 无 FER ⇒ 无 f_eff）。
- **禁**：跨实例合并任何 pins/计数；跨 n 单调性/可转移性推断（n=1024 pins ⇒ n=2048 pins）；引 f_super 为 f_eff；把本包 pins 当 FER/转化率/泄漏实测；选运行点；另算第二基。

## §4 门（二元；零解码可判定形式）

- **门 (a)**：构造 pins PASS（HARD，逐臂）：`fc=0` AND `rank_full==416` AND twice-identical AND `rank_base_400==400`。任一 miss ⇒ 该臂 FAIL。
- **门 (b)**：`f_super=1.25741 ≤ 1.3` 按冻结恒等式成立（逐臂报告行；算术恒等，非科学门——与 P1S1 §4(b) 同性质）。
- **门 (c)**：nested 基能力 PASS（= (a) 中 `rank_base_400==400` 的独立陈述行：未来 400→416 冷救援在构造侧可测；本包不执行 Stage）+ N_req 338 report-only 上下文行（key-eligible 引用不消耗）。
- 判读（记录，不裁决路线）：全三门 PASS（两臂）⇒ 向主线程报告"构造可行，P4 解码/DE 包可进入各自冻结"；任一门 FAIL ⇒ 向主线程返回"构造不可行（pin/基缺失），P4 路线阻塞"。**两种返回都不是 S3 前置裁决**——P4 是否升为 S3 必经由主线程在未来 DECIDE 门另决（G0=B F3 约束下），**本包不裁决**。
- 显式不可判定声明：P1 式 (a) 最终 FER=0 / (b) 实测 f / (c) headroom≥21.5 b 在零解码下**不可判定**（无 FER ⇒ 无 f_eff ⇒ 无 headroom 实测）， deferred 至未来解码包；不得把本包 (a)(b)(c) 读成 P1 §4 的通过/失败映射。

## §5 预算 / 范围 / 停止 / 失败保留（冻结；总量待主线程定）

- **预算**：**单臂 wall ≤ 1800 s**（单窗口；含 2 次 `peg_construct` + rank/girth pins + 报告；远低于 P1 3600 s 解码臂——便宜）；**批次总 ceiling 待主线程在授权时定**（提议 3600 s = 2×1800——**提议非冻结**，授权块勾选即定）；**单次 `peg_construct` 调用 ≤ 600 s**（超时 = 终态构造 FAIL，不续跑；4× 矩阵的宽松帽，见依据）；**RSS < 2 GiB**；**1 CPU**。unspent budget ≠ authorization。
  - 依据（估，非承诺）：n=1024 O1 族 trials-20 构造为秒~分钟级纯内存调用（`v80_o1_campaign.construct_arm` 无磁盘写）；n=2048 矩阵 4×（三元组 4096 条）仍纯内存，600 s 单调用帽有大余量；1800 s/臂含 twice-identical 双构 + 两次 rank（416 全秩经 `peg.rank_GF1024` RREF）+ girth 计数。
- **停止**：任何科学输入变动（n/m/tag/H/λ/ρ/seeds/trials/阈值/信道/解码器/假设/数据角色）⇒ STOP；任一 `.ttbin`/`gamma` 读取 ⇒ STOP-BLOCKED；任一解码调用（`decode_calls≠0`）⇒ STOP-BLOCKED；wall-partial ⇒ **`INCOMPLETE-wall` 保留、永不续跑**；**无 retry/resume/adaptive**。
- **失败保留 + 至多一次预注册工程修复**：仅限基础设施失败（进程死亡、无 pins 可得），科学输入/seeds/阈值/数据角色/假设**全部不变**，**≤1 次** repair+rerun，失败尝试在同一日志**保留记录**（含 exact error + unchanged-inputs 声明 + 保留位置）；未用修复时写明 "**no repair path used**" 行；第二次失败 ⇒ STOP-BLOCKED，batch-end 评审裁决（AGENTS §1.2 EXPLORE 合约）。
- **根**：机器根族 **`workspace/P4_FEAS/`**，逐臂 fresh additive `workspace/P4_FEAS/<arm>_<uuid8>/`（UUID 在 Pre-EXECUTE 冻结 + 缺席证明；本包留 `[TO BE FROZEN]` 占位）；`results/`、`comparison_bench/outputs_comparison/` **禁写**；既有证据根（`workspace/p3_census_3954637c/`、`workspace/p3_stage05_ee32030a/`、`workspace/r1_histogram_5e2a91c4/`、15 个 `workspace/x1_*`、2 个 `workspace/S0_1/`、2 个 `workspace/P1_STAGE1/`）**只读不碰**；`git diff -- src/` 必须 EMPTY（I4）。

## §6 交付物与证据清单（执行时产出；本任务不产出任何一项）

1. 逐臂根 `workspace/P4_FEAS/<arm>_<uuid8>/`：`P4FEAS_RESULT_<arm>.md` + `construction.json` + pins 报告（§3 字段；`decode_calls=0` 行）。
2. 批次日志 `docs/research_cycles/V80-NBLDPC-JAN21/P4_FEAS_EXPLORATION_LOG.md`（append-only）：条目 0 = Pre-EXECUTE Q0–Q6 记录（prompt §0）；条目 1–2 = 逐臂构造（冻结顺序 R1→R2，**由一次 runner 双臂单次调用覆盖**：`p4_feas_construct` 单次调用按机器门 R1→R2 续跑、前臂放行即续下一臂，无逐臂授权；**逐臂 per-arm 旧模板作废**）；条目 3 = 收口 tally（两臂终态、总 wall、修复用否）。保留失败/INCOMPLETE 臂不覆盖、不续跑。
3. `docs/research_cycles/V80-NBLDPC-JAN21/P4_FEAS_BATCH_END_REVIEW.md`：**单次** batch-end 独立评审（§10.3：授权边界、机器门、保留失败、修复若用、最终证据、claim ceiling）。无逐臂评审文件。
4. 关闭后由主线程执行 memory triage（AGENTS §3）——本包含指针，不代执行。

## §7 EXPLORE 资格与合约（AGENTS §1.2 + §10.3）

- 五条资格：① 输入 = 无（构造仅消费 RNG 种子；非敏感、零 `.ttbin`、零 bundle——比"已批准开发输入"更弱）；② fresh additive `workspace/P4_FEAS/` 根，可逆、有界（2 臂 ×2 构造调用，单臂 ceiling 1800 s、总量待定）；③ 不产生 FER/SKR/资格化/晋升/发表主张（见 §9）；④ 无破坏性覆盖、无新对外动作；⑤ 纯构造 ⇒ 非 DECIDE（n 变更是未来解码包的科学输入变更，本包零解码不触发 DECIDE；调用解码器**零次** a fortiori 不强制 DECIDE）。
- 合约（两文件制）：**一个 packet+prompt 对**（本文件 + `P4_FEAS_PROMPT.md`，授权边界写在本 packet 内）+ **一个 append-only log** + **一个 batch-end 独立评审**；一次授权覆盖冻结臂序（操作者在前一机器门放行时继续下一臂，无逐臂授权）；至多一次预注册 repair+rerun；multi-seed 由两谱系满足（构造 RNG 维度的双实例；不另造 seed 轴）。
- 升级：转真实数据、关路阈值、发表主张、破坏性输出、成本显著上升、科学输入/假设变更、**或任一解码/DE 调用** ⇒ 必须先升 DECIDE（未来 P4 解码/DE 包）。

## §8 范围外 / FORBIDDEN（执行者与本任务共同遵守）

- 无真实/Jan-21 数据；无 `.ttbin`/`gamma` 读取；无解码器/DE/图核改动；无先验 refit；**零解码调用**；**不执行 P1 §9 per-source 臂、P2、X1 任何臂、任何解码/DE 臂**；不选运行点；不改任何冻结输入（F1–F10）；不发明 seeds/路径/计数/pins。
- 禁跨实例 pooling；禁 `undetected` 议题（N/A——零解码，无列可并）；禁引 f_super 为 f_eff；禁跨 n 单调性/可转移性推断；禁 warm-start/non-nested/two-segment **执行**（本包无 Stage 执行；未来 Stage 形态由未来包另冻）。
- 禁写 `results/`、`comparison_bench/outputs_comparison/`；禁改 `src/`；禁 `tools/longrun_*`/`minrerun_*`/`routeA_*`；禁 `experiments/run_e2e_pipeline.py`；禁碰 **P1 族**（`P1_PACKET.md`、`P1_STAGE1_*`、`workspace/P1_STAGE1/`）、**S0.1 族**（`S0_1_*`、`workspace/S0_1/`）、`docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`、`docs/decision-log.md`、`AGENTS.md`、`docs/troubleshooting.md`、`src/`（P4-3 禁单全集）；**禁 commit / push**。
- 若实现需要改动任何冻结模块/行为才能跑通 ⇒ **STOP 回主线程**（行为变更先 OpenSpec），执行者不得自行改需求或补常数。

## §9 Claim ceiling

- **仅**：n=2048 PEG 构造**可行性**（逐实例 pins + nested 基能力 + 冻结算术恒等行），为路线①入口证据。
- **非**：机制性能（无 FER/转化率/泄漏实测）、SKR、资格化、路线裁决（P4 是否升为 S3 必经**不在本包**）、运行点选择、真实数据 FER、可认证/文献可比 `f_eff≤1.3` 句、发表材料。key-eligible 计数只引用不消耗。通用性表述若日后引用本包，必须两实例分列，**只报单实例冒充结论 = 禁止**。

## §10 授权门（EXPLICIT USER GATE — 停在这里）

- **本 packet 冻结 ≠ 授权。任何构造执行前必须同时满足：**
  (a) 入口语境已记录：P1 Stage-1 P4-elevation 输入（R1 FAIL(a)/R2 FAIL(c)，N_req 402/575>eligible）+ G0=B F3（P4 不自动升格）+ 用户顺序 ①→③→②——三者是冻结前提，不是授权；
  (b) 执行面就绪：thin runner **`p4_feas_construct`**（`comparison_bench/src/comparison_bench/cli/p4_feas_construct.py`；逐字跑 F1–F6，`peg_construct` + pins + `decode_calls=0` 门；双臂单次调用 R1→R2 机器门续跑）+ fake-only focused 单文件测试已实现——**实现本身无 track gate**（AGENTS §1.2 矩阵），track gate 挂在首次合成执行；
  (c) **Pre-EXECUTE Q0–Q6**（记入日志条目 0）：Q0 目标分支 `formal-ir-v72p1-addendum-clean`（不切分支；HEAD 在 Pre-EXECUTE 重测记录，基线 8e9c8526 仅为本冻结时点）；Q1 范围清洁（仅 additive runner+测试+Pre-EXECUTE 记录；`git diff -- src/` EMPTY；脏树按显式文件清单界定，外源 `openspec/changes/binary-ldpc-v5-*` 不纳入）；Q2 冻结契约 F1–F10 逐项核对；Q3 输出缺席（`workspace/P4_FEAS/` 不存在）+ 构造种子字面 rg 仅命中本包族 + 保护根快照字节一致；Q4 **focused 单文件 fake-only 测试 PASS 并附输出**（E5 规则：batch-end 必须附此输出）；Q5 dry pins 门（F6 字面；**Grant 前零构造之外的任何生产调用为零，特别是零解码**）；Q6 闭合（总量 ceiling 已定 + 下方授权块填全）；
  (d) **FRESH EXPLICIT USER GRANT**，填入下方授权块（签名，或本周期 verbatim 对话授权记录——F-3/X1/X1S 先例，仅限本周期）；
- **未授权不得执行。** 本文件不授权构造、不授权测试长跑、不授权 commit/push、不授权 P1 §9 / P2 / X1 / 任何解码-DE 臂。

### §10(d) 授权块（空白待签；未填 = 未授权；全包唯一填充处）

- Acceptance ID `G-P4FEAS`；grant verbatim：________；臂根 UUID（R1/R2）：`P4F-R1_[TO BE FROZEN]` / `P4F-R2_[TO BE FROZEN]`（Pre-EXECUTE 冻结，签署时缺席已确认）：________；预算确认（单臂 wall ≤1800 s ✓；总量 ceiling ＝ ________ ✓；单次构造 ≤600 s，超时 = 终态 FAIL、不续跑 ✓；RSS < 2 GiB ✓；1 CPU ✓；零 `.ttbin`/零 bundle 读取/零解码/零 `results/` 与 `outputs_comparison/` 写入 ✓）：________；日期 / 主线程：________；签名：________。（全包唯一授权填充处；未来 Pre-EXECUTE 记录的 Q6 预算/签字镜像栏不是授权路径。）

## §11 本任务（planner 冻结）创建范围声明 — P4-3

- 本任务**只新建**本文件与 `P4_FEAS_PROMPT.md` 两份 docs；**未执行任何构造/解码/测试长跑**；**未改动** P1 族、S0.1 族、`docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`、`docs/decision-log.md`、`AGENTS.md`、`docs/troubleshooting.md`、`src/`/`experiments/`/`tools/` 或任何其他文件；**未 commit、未 push**。
- 科学阈值未动：1.3 门、λ_total=leak_EC+64（≡ε_EV≈2⁻⁶³）、tag 64 bits、H_anchor=0.83256272、content/slope/cap 常数形状、N 规则、`undetected` 隔离、禁合并——全部**重述**自 V80_BASELINE §2 / ROADMAP §2，零改动（分母 n 1024→2048 是口径延拓 §2.1，不是阈值改动）。
- 结果数值未预设：§1.3 所列全部结果字段 `[TO BE MEASURED]`，本包无一构造成功/失败预测数字（含 fc/girth/rank/wall ——禁预设，P4-3 执行）。
