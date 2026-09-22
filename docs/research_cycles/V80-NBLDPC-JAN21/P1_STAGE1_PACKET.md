# P1 Stage-1 速率自适应救援 Packet (2026-09-22) — FROZEN, NOT GRANTED

- 任务 IDs：**P1S1-1**（本文件 = prereg + 冻结科学输入 + 授权边界）/ **P1S1-2**（配套执行面 `P1_STAGE1_PROMPT.md`）/ **P1S1-3**（本任务范围禁令，见 §11）。
- Acceptance ID（拟）：**G-P1S1**。本文件是冻结件，**不是授权**；授权任何执行 = 0。**未授权不得执行。**
- Track：**EXPLORE**（合成、有界、可逆；`EXPLORE_HEAVY` 成本注记——2 臂 ×（240 基线解码 + ≤k 救援解码），单臂 wall ≤3600 s）。
- 分支 / 基线：`formal-ir-v72p1-addendum-clean` / **`85e0771f`**（不切分支、不 commit、不 push）。
- 计划出处：`docs/ROADMAP-20260921.md` §3 P1（`m_base=200`、救援 `Δm=8`、单段、总行 ≤208、预算 ≤3600 s/臂；预测数字待实测；复核项 3/6/7/10 已纳入）+ §2 DECISION-1（双数并列、本臂基、零失败臂认证规则）+ §4 决策树；`docs/V80_BASELINE_20260921.md` §2（`f_super=(5m+64)/852.544`、content=852.544 b、slope 4.785675、m1+m2≤208 硬顶、A208 余量 4.3075 canonical / 4.31 rounded、λ_total=leak_EC+64 ≡ ε_EV≈2⁻⁶³）+ §0.1 retained-frozen（P1 §§3/6–7：nested、COLD、NO warm-start、NO non-nested、NO two-segment、门 (a)(b)(c)、预算/停止/失败保留、FORBIDDEN 含 pooling 与 6+4）；`docs/EXECUTION_PLAN_20260922.md` §3 S-B（G0=B 主路径：S0.1 → P1 单段救援 → P3 → P5 n=1024；P4 作第二代）+ §5 门禁（S0.1-gate、P5-gate 禁止句）；AGENTS.md §1.2（EXPLORE 两文件制 + 合约）+ §10.3（单次 batch-end）。
- 上游证据语境（只引用、不重证）：X1 route-gate `m_min` = 2M **204** / 1.5M **203** / 1M **197**（冻结网格分辨率；`X1_BATCH_END_REVIEW.md` §7），且 **joint 可认证集合为空**（route-pass ∧ count-certifiable = ∅，key-eligible **200/276/364**）；b2f F202 6/240 @2026092001、b2g F202 4/240 @2026092011、F208 0/240（两实例各报）；X1-2M-200S = standalone m=200（REVISE R6：≠ P1 nested leading-200，CENSORED-bar12）——**旧观测，不得作本包任何臂预测**。
- 唯一合法实测锚（S0.1，分列消费，禁合并）：`S0_1_BATCH_END_REVIEW.md`（PASS_WITH_FINDINGS，S0.1-gate PASS）——
  - S01-R1（2026092001，girth 8）：**79/240**，FER 0.329167，u79，871.9 s；
  - S01-R2（2026092011，girth 6）：**119/240**，FER 0.495833，u116，1010.5 s；
  - 同基 `f_super=1.248029`，`N_req=277` report-only。本包以前述分列锚为**机制语境引用**（救援前提的合理性语境），**不作配对块身份**（新 seed-base ⇒ 新帧实现），**不作点预测**（见 §1.3）。
- G0 状态：**G0=B**（EXECUTION_PLAN §4 期 0 注记）⇒ 本包属 S-B 主路径 P1 救援臂冻结。
- 配套 prompt：`P1_STAGE1_PROMPT.md`（两文件制，AGENTS §1.2 + EXECUTION_PLAN 轨 P P-1）。批次日志（执行时新建，append-only）：`P1_STAGE1_EXPLORATION_LOG.md`；批次末独立评审（执行后）：`P1_STAGE1_BATCH_END_REVIEW.md`。本包不新建其他执行文件。
- P1 §9 per-source 扩展（1M m_base=193 / 1.5M m_base=199）：RETAINED-FROZEN 但**不在本包**——需 X1 证据 + 独立 packet + 逐臂授权；本包仅冻结 2M 谱系 `m_base=200` 两臂，不消费、不改动 §9。

## §1 目的与假设（测，不宣称）

1. **目的**：在冻结 nested 构造下实测速率自适应救援——Stage-1 用同实例 A208 的 leading-200 行冷解码全部 240 块（基线 fails `k/240` = MEASURED）；Stage-2 对**恰好** Stage-1 非 success 块集披露 rows[200,208) 并 COLD 全矩阵重解码（最终 fails `F/240` = MEASURED）。检验"Δm=8 增量综合征把基线失败集转化为最终零失败、期望泄漏留在冻结盒内"这一假设。
2. **假设（待测，非主张）**：enacted 机制依据——同一批配对帧上，软边际 F202 失败块（b2f 6/240、b2g 4/240）所在的帧集在 m=208 冷全矩阵解码下为 0/240（两实例），即"+6/+8 行能救回这些确切的块"（冷全矩阵形态）；S0.1 锚（79/240、119/240，nested leading-200 同定义、不同帧实现）给出基线失败率量级语境。**仍未测**：(a) 新帧实现上的 Stage-1 `k`；(b) 增量 nested 路径的转化率（warm-start ≠ 冷启动差异已按设计排除，cold 形态本身仍待测）；(c) 触发率 `r` 与期望泄漏。
3. **预注册非预测（P1S1-3 禁令执行）**：以下全部是 **MEASURED 结果，无点预测**——Stage-1 `k/240`、FER、Stage-2 转化数、最终 `F/240`、触发率 `r`、`E[leak]`、`f_exp`、`f_eff`、headroom、iters/wall（逐臂）。ROADMAP 的条件算术（IF 基点 ≈10/240 全转化 THEN `E[leak]=1065.7 b ⇒ f≈1.250 ⇒ 余量≈42.6 b ⇒ N≥288`）**仅作算术引用**；"10/240" 不是实测量，**不得**作臂预测；X1-200S standalone 旧观测**不得**作臂预测；S0.1 的 79/240 与 119/240 **不得**跨包预设为本包 `k`（新帧实现）。本包冻结计算规则（§5），永不冻结结果数值。

## §2 冻结科学输入（改动任一项 ⇒ STOP，回主线程；必要时先 OpenSpec）

| # | 项 | 冻结值 |
|---|---|---|
| F1 | 臂数 | **恰好 2 臂**：`P1S1-R1` 构造实例 **2026092001**（girth 8 记录值）；`P1S1-R2` 构造实例 **2026092011**（girth 6 记录值）。**分别报告，禁合并**（含 6+4 式求和；含跨实例触发集/转化数相加）。 |
| F2 | 构造（nested，单段） | 基码 = 同实例冻结 **A208 矩阵的前 200 行 rows[0,200)**（nested leading-200；**非** P0 `construct_arm("A200",…)`；**不**新建 208 构造）。救援 = **单段**披露 **rows[200,208)**（40 b），救援解码 = **COLD 全矩阵重解码**（同 A208，rows[0,208)）。总行 **208 ≤ 208 硬顶**。**NO warm-start**（两 Stage 均从先验冷启动）；**NO non-nested fallback**（base-A200 + 全量重披露形态被禁——非平凡触发率下破盒）；**NO two-segment / multi-segment**（多段 ≤208 变体**不在本包冻结**，主线程若要须另行 packet + OpenSpec，见 §2.1）。基码子矩阵质量本身被测量（Stage-1）。 |
| F2.1 | 多段变体处置 | 用户"单段或多段但≤208"中，**本包只冻结单段 200→208**。多段（如 200→204→208，总行仍 ≤208）改变披露/解码动力学，受 retained-frozen NO two-segment 约束，**明确 OUT-OF-BOX**：不冻结、不授权、不预留预算；意向记录于此，主线程另决。 |
| F3 | 配对块 / seeds / stream | **240 配对块/实例**；seeds **新 seed-base `2026096401+idx`**，idx 0..239（⇒ 2026096401..2026096640）；stream **`o1_blk:{seed}`**（格式与 O1R/P0/L1B/b2e/b2f/b2g/X1/S0.1 同形）。**同整数两臂共用**（跨构造配对对比，**无独立性主张**）。**FRESH 性**：新区间与既有族（`2026095601..2026095840` 配对族——**禁复用**；`2026095501` O1 族；`2026096001/6101/6301` S2 族）零重叠——**与 S0.1 无块身份重合**，S0.1 锚仅机制语境引用（§1）。Pre-EXECUTE 以 rg 证明新区间命中仅限本包族（packet/prompt/未来 runner+测试/未来根）。 |
| F4 | 信道 | 2M 冻结合成信道：`docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` + `gamma_f03_pb.npz` **只读、永不 refit**；纯合成抽样，**零 `.ttbin` 读取**（任一读取 = STOP-BLOCKED）。 |
| F5 | 先验/解码器 | b2f 谱系 verbatim：π_i(e)=Σ_u1 γ1(u1\|b_i)·γ2(y_i⊕e\|u1,b_i)，y_i=b_i&31，`marg=np.einsum("nu,nuv->nv", g1c.T, cond)` + row-guard + `center_rows_prior`；喂 `v28.decode_error_domain_posterior(field, y.tolist(), dense, s_x, prior, 300)`；**max_iter=300 / streak 3**；接受 = **`exact_match`**；**NO genie u1 / NO argmax û1 / NO L1 码**。Stage-1 与 Stage-2 **均冷启动**（warm-start 禁令，F2）。 |
| F6 | 构造 pins（Pre-EXECUTE，dry 零解码） | A208：`fc=0` + rank **208** + twice-identical（b2f/b2g manifest 既有 pin，重申）；基码：**rank(rows[0,200)) = 200 REQUIRED**，否则 **STOP-BLOCKED**；girth **measured/recorded/not-gated**（逐实例记录）。 |
| F7 | 会计（冻结恒等式，非门） | 整帧含 64-bit tag 冻结口径：anchor H_full=0.83256272 b/sym ⇒ content=1024×0.83256272=**852.544 b**；cap leak ≤1.3×852.544=**1108.31 b**；`f_super=(5m+64)/852.544`；基线 leak **1064 b** ⇒ `f_super=1064/852.544=**1.24803**`；全触发 worst-case leak **1104 b** ⇒ `f_super=**1.294947** ≤ 1.3`（按构造恒等，非科学门）；`E[leak]=1064+40·r`（r=触发率=#rescued/240）；`f_exp=E[leak]/852.544`（本臂自己 blended 基）；`f_eff=f_exp+4.785675·(F/240)`（本臂自己最终 F）；headroom=`1108.31−E[leak]`。**绝不把 f_super/f_exp 当 f_eff 报**（F>0 时）。单 TRAIN/anchor 基，**不另算第二基**（P1 §9 per-source 基不在本包）。A208 余量 4.3075 canonical（4.31 rounded）；λ_total=leak_EC+64（≡ε_EV≈2⁻⁶³）口径不变（P1S1-3 禁改阈值）。 |
| F8 | 认证语境 | **key-eligible 200/276/364 仅引用为语境，本包一个也不消耗**（合成配对帧，不触任何真实帧/计数）；N 规则 report-only：`N_req=⌈3·4.785675/(1.3−f_exp)⌉`，**仅当最终 F=0 才相关**，无 N 预设；**本包不作任何可认证/文献可比 `f_eff≤1.3` 主张**（X1 joint-∅ 结论不被本包触碰）。 |
| F9 | 早停 / Stage-2 集合 | **禁止 bar-12 早停**：Stage-1 解完全部 240 块；Stage-2 覆盖对象 = **恰好** Stage-1 非 `success` 块集（exact_match false 全集；综合征有效但不匹配者归 `undetected` 类但仍在集合内——F10）。bar-12（fails≤12，DECISION-1 内部路线上下文）**仅 report-only**（Stage-1 上下文行），不触发停止、不裁决路线、不改变 Stage-2 集合。 |
| F10 | 失败类别 | 非 `exact_match` = fail：Stage-1 计入 `k`，最终计入 `F`；综合征有效但不匹配者另列 **`undetected` 单列，永不并入 success**（b2f-verbatim 规则，X1 F-a / S0.1 机器门先例）。 |

## §3 度量与产出模式（冻结计算规则）

- 逐块（`rows.json`/`block_accounting.csv`，列名与 X1/S0.1 同构）：`block_idx, seed, iters, wall_s, decoded, failed, undetected, prior_entropy_bits, u1_mismatches`（后两项 report-only，b2f 先例）+ Stage 标记（stage1/stage2-rescue）。
- 逐臂：Stage-1 `k/240`（= 基线 fails）、`FER_Stage1=k/240`、救援转化数（rescued / attempted，明示 attempted = k 恒等）、最终 `F/240`、触发率 `r=#rescued/240`、`E[leak]=1064+40·r`、`f_exp`、`f_eff`（本臂自己最终 F）、headroom、undetected 计数（单列）、iters min/max（分 Stage）、wall 合计 + 块均值、峰值 RSS、构造标签（实例 + girth）、pins、信道路径、seeds/stream、`f_super` 双恒等行（基线 1.24803 / 全触发 1.294947）、bar-12 report-only 上下文行、S0.1-锚引用行（分列值 + "机制语境、非配对身份、非预测"声明）、claim-ceiling 行。
- **禁**：跨实例/跨块合并任何 FER/转化数；跨 m 单调性推断；引 f_super/f_exp 为 f_eff；把本包 Stage-1 `k/240` 当真实数据 FER；把 S0.1 的 79/119 当本包 `k` 的预测值引用。
- 报告基说明：F7 用 V80 冻结 anchor 基（与 P1 §2/§5 `E[leak]/852.544` 同基）；**不**另算第二基，避免混基。

## §4 门（二元；Stage-1 上下文仅 report-only）

- **门 (a)**：最终 **F/240 = 0**（HARD —— DECISION-1 认证作用域：零失败臂 ONLY；240 块 1 次失败 ⇒ Clopper–Pearson 上界 ≈1.94% ≫ f≈1.25 处 1.045% 容限，`docs/ROADMAP-20260921.md` §2）。Stage-1 `k/240` 对内部 bar（fails ≤ 12，FER ≤ 5% 路线继续/停止门）**仅 report-only 上下文**，无裁决含义。
- **门 (b)**：`f ≤ 1.3` 本臂基：worst-case（全触发，总行 208）`f_super=1.294947 ≤ 1.3` 按构造成立 **AND** 实测 `f_exp ≤ 1.3`（由门 (c) 蕴含）。
- **门 (c)**：headroom = `1108.31 − E[leak]` ≥ **21.5 b**（⇔ 所需 N ≤ 570；20 b ⇒ N ≥ 612——不用；ROADMAP §8 项 6）。等效触发率 cap：`r ≤ (1086.81−1064)/40` = **57.0%**。
- 判读：PASS（全三门）⇒ 向主线程报告（决策树 PASS 分支：P3 审计 → P5 n=1024）；FAIL（任一门，含救援不转化 ⇒ "悬崖不可救援"）⇒ 向主线程返回（决策树 FAIL 分支：P4 升为 S3 前置必经；本身即对 P4 的决定性输入）。**均不授权任何后续执行**。

## §5 预算 / 范围 / 停止 / 失败保留（冻结；总量待主线程定）

- **预算**：**单臂 wall ≤ 3600 s**（两 Stage 合计，单窗口；= ROADMAP §3 / P1 §7 单臂上限；V80 §0.1 retained）；**批次总 ceiling 待主线程在授权时定**（提议 7200 s = 2×3600，S0.1 先例——**提议非冻结**，授权块勾选即定）；**单调用 ≤ 300 s**（超时 = 终态，块计 fail，不续跑）；**RSS < 2 GiB**；**1 CPU**。unspent budget ≠ authorization。
  - 依据（估，非承诺）：Stage-1 成本类 ≈ S0.1 实测 871.9/1010.5 s（同 nested-200 定义、不同帧实现——仅参考，非预测）；Stage-2 至多 240 次冷 208 解码（≈672.6 s/240 类，b2f F208）；和仍在 3600 s 窗内，有余量。
- **停止**：任何科学输入变动（n/m/tag/H/λ/seeds/阈值/信道/解码器/假设/数据角色）⇒ STOP；任一 `.ttbin` 读取 ⇒ STOP-BLOCKED；wall-partial ⇒ **`INCOMPLETE-wall` 保留、永不续跑**；**无 retry/resume/adaptive**。
- **失败保留 + 至多一次预注册工程修复**：仅限基础设施失败（进程死亡、无 verdict 可得），科学输入/seeds/阈值/数据角色/假设**全部不变**，**≤1 次** repair+rerun，失败尝试在同一日志**保留记录**（含 exact error + unchanged-inputs 声明 + 保留位置）；未用修复时写明 "**no repair path used**" 行；第二次失败 ⇒ STOP-BLOCKED，batch-end 评审裁决（AGENTS §1.2 EXPLORE 合约）。
- **根**：机器根族 **`workspace/P1_STAGE1/`**，逐臂 fresh additive `workspace/P1_STAGE1/<arm>_<uuid8>/`（UUID 在 Pre-EXECUTE 冻结 + 缺席证明；本包留 `[TO BE FROZEN]` 占位）；`results/`、`comparison_bench/outputs_comparison/` **禁写**；既有证据根（`workspace/p3_census_3954637c/`、`workspace/p3_stage05_ee32030a/`、`workspace/r1_histogram_5e2a91c4/`、15 个 `workspace/x1_*`、2 个 `workspace/S0_1/`）**只读不碰**；`git diff -- src/` 必须 EMPTY（I4）。

## §6 交付物与证据清单（执行时产出；本任务不产出任何一项）

1. 逐臂根 `workspace/P1_STAGE1/<arm>_<uuid8>/`：`P1S1_RESULT_<arm>.md` + `rows.json` + `block_accounting.csv`（§3 字段）。
2. 批次日志 `docs/research_cycles/V80-NBLDPC-JAN21/P1_STAGE1_EXPLORATION_LOG.md`（append-only）：条目 0 = Pre-EXECUTE Q0–Q6 记录（prompt §0）；条目 1–2 = 逐臂运行（冻结顺序 R1→R2，各按 §5 一次授权覆盖）；条目 3 = 收口 tally（两臂终态、总 wall、修复用否）。保留失败/INCOMPLETE 臂不覆盖、不续跑。
3. `docs/research_cycles/V80-NBLDPC-JAN21/P1_STAGE1_BATCH_END_REVIEW.md`：**单次** batch-end 独立评审（§10.3：授权边界、机器门、保留失败、修复若用、最终证据、claim ceiling）。无逐臂评审文件。
4. 关闭后由主线程执行 memory triage（AGENTS §3）——本包含指针，不代执行。

## §7 EXPLORE 资格与合约（AGENTS §1.2 + §10.3）

- 五条资格：① 输入 = 已持久化直方图的合成抽样（非敏感、已批准开发输入，零 `.ttbin`）；② fresh additive `workspace/P1_STAGE1/` 根，可逆、有界（2 臂 ×（240+≤240）解码，单臂 ceiling 3600 s、总量待定）；③ 不产生 FER/SKR/资格化/晋升/发表主张（见 §9）；④ 无破坏性覆盖、无新对外动作；⑤ 纯合成 ⇒ 非 DECIDE。
- 合约（两文件制）：**一个 packet+prompt 对**（本文件 + `P1_STAGE1_PROMPT.md`，授权边界写在本 packet 内）+ **一个 append-only log** + **一个 batch-end 独立评审**；一次授权覆盖冻结臂序（操作者在前一机器门放行时继续下一臂，无逐臂授权）；至多一次预注册 repair+rerun；multi-seed 由 240 配对块 + 冻结 seed 流满足（不另造 seed 轴；新区间本身即 FRESH 性）。
- 升级：转真实数据、关路阈值、发表主张、破坏性输出、成本显著上升、或科学输入/假设变更 ⇒ 必须先升 DECIDE。对冻结解码器在合成抽样上调用**不**强制 DECIDE。

## §8 范围外 / FORBIDDEN（执行者与本任务共同遵守）

- 无真实/Jan-21 数据；无解码器/DE/图核改动；无先验 refit（`gamma_f03.npz` 只读）；**不执行 P1 §9 per-source 臂、P2、X1 任何臂**；不选运行点；不改任何冻结输入（F1–F10）；不发明 seeds/路径/计数/pins（新区间 outside 既有族是冻结值，不是发明）。
- 禁跨实例 pooling（含 6+4；含触发集/转化数相加）；禁 `undetected` 并入 success；禁引 f_super/f_exp 为 f_eff；禁跨 m 单调性推断；禁 warm-start；禁第二构造矩阵；禁 two-segment/multi-segment。
- 禁写 `results/`、`comparison_bench/outputs_comparison/`；禁改 `src/`；禁 `tools/longrun_*`/`minrerun_*`/`routeA_*`；禁 `experiments/run_e2e_pipeline.py`；禁碰 **`docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`、`docs/decision-log.md`、`AGENT_PROJECT_MEMORY.md`、既有 runner/测试、S0.1 族文件**（packet/prompt/preexec/log/review + `workspace/S0_1/` + `s01_m200_runner` 系）；**禁 commit / push**。
- 若实现需要改动任何冻结模块/行为才能跑通 ⇒ **STOP 回主线程**（行为变更先 OpenSpec），执行者不得自行改需求或补常数。

## §9 Claim ceiling

- **仅**：合成配对帧上的速率自适应救援**效率**（逐实例 Stage-1 `k/240` + 转化数 + 最终 `F/240` + 冻结基 `E[leak]`/`f_exp`/`f_eff` + iters/wall + undetected 单列），为 S-B 主路径的 P1 证据。
- **非**：SKR、资格化、路线裁决、运行点选择、真实数据 FER、可认证/文献可比 `f_eff≤1.3` 句、发表材料。key-eligible 计数只引用不消耗。通用性表述若日后引用本包，必须两实例分列，**只报单实例冒充结论 = 禁止**。

## §10 授权门（EXPLICIT USER GATE — 停在这里）

- **本 packet 冻结 ≠ 授权。任何解码执行前必须同时满足：**
  (a) 入口语境：S0.1-gate 满足已记录（锚存在；`S0_1_BATCH_END_REVIEW.md` PASS_WITH_FINDINGS）+ G0=B 已记录（EXECUTION_PLAN §4 期 0）——二者是冻结前提，不是授权；
  (b) 执行面就绪：thin runner（若无既有 CLI 逐字跑 F1–F5）+ fake-only focused 单文件测试已实现——**实现本身无 track gate**（AGENTS §1.2 矩阵），track gate 挂在首次合成执行；
  (c) **Pre-EXECUTE Q0–Q6**（记入日志条目 0）：Q0 目标分支 `formal-ir-v72p1-addendum-clean`（不切分支；HEAD 在 Pre-EXECUTE 重测记录，基线 85e0771f 仅为本冻结时点）；Q1 范围清洁（仅 additive runner+测试+Pre-EXECUTE 记录；`git diff -- src/` EMPTY；脏树按显式文件清单界定，外源 `openspec/changes/binary-ldpc-v5-*` 不纳入）；Q2 冻结契约 F1–F10 逐项核对；Q3 输出缺席（`workspace/P1_STAGE1/` 不存在）+ 新 seed 区间 rg 仅命中本包族 + 保护根快照字节一致；Q4 **focused 单文件 fake-only 测试 PASS 并附输出**（E5 规则：batch-end 必须附此输出）；Q5 dry 零解码 pins（F6：A208 fc=0/rank208/twice-identical、基码 rank=200、girth 记录）——**Grant 前零生产解码**；Q6 闭合（总量 ceiling 已定 + 下方授权块填全）；
  (d) **FRESH EXPLICIT USER GRANT**，填入下方授权块（签名，或本周期 verbatim 对话授权记录——F-3/X1/X1S 先例，仅限本周期）；
- **未授权不得执行。** 本文件不授权解码、不授权测试长跑、不授权 commit/push、不授权 P1 §9 / P2 / X1 任何臂。

### §10(d) 授权块（空白待签；未填 = 未授权；全包唯一填充处）

- Acceptance ID `G-P1S1`；grant verbatim：`G-P1S1 GRANT：授权P1 Stage-1速率自适应救援执行（2臂 P1S1-R1/P1S1-R2，m_base=200+Δm=8→总行208≤208硬顶，Stage-2=Stage-1非success全集，分列禁合并，双旗标 --execute-real --execution-authorized，基线HEAD e2236766）`；臂根 UUID（R1/R2）：`P1S1-R1_ef7da79b` / `P1S1-R2_22754019`（Pre-EXECUTE 冻结，签署时缺席已确认）；预算确认（单臂 wall ≤3600 s ✓；总量 ceiling ＝ 7200 s ✓；单调用 ≤300 s，超时 = 终态、块计 fail、不续跑 ✓；RSS < 2 GiB ✓；1 CPU ✓；零 `.ttbin` / 零真实数据 / 零 `results/` 与 `outputs_comparison/` 写入 ✓）；日期 / 主线程：2026-09-22 / main；签名 from kai；UUID: P1S1-R1_ef7da79b / P1S1-R2_22754019。（全包唯一授权填充处；`P1_STAGE1_PREEXEC.md` Q6 预算/签字镜像栏不是授权路径。）

## §11 本任务（planner 冻结）创建范围声明 — P1S1-3

- 本任务**只新建**本文件与 `P1_STAGE1_PROMPT.md` 两份 docs；**未执行任何解码/测试长跑**；**未改动** `docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`、`docs/decision-log.md`、`AGENT_PROJECT_MEMORY.md`、任何既有 runner/测试、S0.1 族文件、`src/`/`experiments/`/`tools/` 或任何其他文件；**未 commit、未 push**。
- 科学阈值未动：m1+m2≤208 硬顶、A208 余量（4.3075 canonical / 4.31 rounded）、λ_total=leak_EC+64（≡ε_EV≈2⁻⁶³）、content/slope/cap 常数——全部**重述**自 V80_BASELINE §2，零改动。
- 结果数值未预设：§1.3 所列全部结果字段 `[TO BE MEASURED]`，本包无一数字预测。
