# S0.1 软边际 m=200 FER 探针 Packet (2026-09-22) — FROZEN, NOT GRANTED

- 任务 IDs：**S01-1**（本文件 = prereg + 冻结科学输入 + 授权边界）/ **S01-2**（配套执行面 `S0_1_M200_PROMPT.md`）/ S01-3（本任务范围禁令，见 §11）。
- Acceptance ID（拟）：**G-S01M200**。本文件是冻结件，**不是授权**；授权任何执行 = 0。**未授权不得执行。**
- Track：**EXPLORE**（合成、有界、可逆；`EXPLORE_HEAVY` 成本注记可选——依据 `docs/EXECUTION_PLAN_20260922.md` §3 S0.1 行「EXPLORE（可 HEAVY 注记）」）。
- 计划出处：`docs/EXECUTION_PLAN_20260922.md` §3 轨 S / S0.1 行（240 配对块、两构造分报、EXPLORE 可 HEAVY、**先于任何 3600 s 级救援臂**）；§5 门禁 **S0.1-gate**。
- 冻结口径出处：`docs/V80_BASELINE_20260921.md` §2（`f_super=(5m+64)/852.544`、content=852.544 b、slope 4.785675、m1+m2≤208）、§1 不变量 I4–I6；`docs/ROADMAP-20260921.md` §3 P1（m_base=200 / Δm=8 / ≤208；10/240 为待实测外推）+ §8 复核项 3/10。
- 上游证据语境（只引用、不重证）：X1 已测 route-gate `m_min` = 2M **204** / 1.5M **203** / 1M **197**，且 **joint 可认证集合为空**（route-pass ∧ count-certifiable = ∅，`X1_BATCH_END_REVIEW.md` §7）；b2f F202 6/240 @2026092001、b2g F202 4/240 @2026092011、F208 0/240（两实例各报）。本探针不作 route/认证结论。
- G0 状态：**G0=B**（EXECUTION_PLAN §4 期 0 注记，2026-09-22 已给）⇒ 本包属 S-B 主路径首个科学探针。
- 依赖与顺位：**H0.1 之后**（X1 scoped 提交完成或用户显式豁免，Pre-EXECUTE 记录）；**先于**任何 3600 s 级 P1 救援臂的冻结/执行。
- 配套 prompt：`S0_1_M200_PROMPT.md`（两文件制，AGENTS §1.2 + EXECUTION_PLAN 轨 P P-1）。批次日志（执行时新建，append-only）：`S0_1_EXPLORATION_LOG.md`；批次末独立评审（执行后）：`S0_1_BATCH_END_REVIEW.md`。本包不新建其他执行文件。

## §1 目的与假设（测，不宣称）

1. **目的**：在 P1 救援臂（Stage-1 基线 + Stage-2 Δm=8 救援，≤3600 s/臂）之前，实测软边际 **m=200 基线 FER = k/240（逐构造实例）**，为 P1 "10/240" 外推提供**唯一合法实测锚**（EXECUTION_PLAN §5 S0.1-gate：m=200 软边际 FER 实测存在）。
2. **假设（待测，非主张）**：b2f 软边际谱系（D-u1=0 结构性为 0）下，m=200 基线块的失败集合可被 Δm=8 救援的机制前提，取决于实测 k；本包只测 k，不测救援。
3. **预注册非预测**：m=200 基线 FER 是 **MEASURED 结果，无点预测**。"10/240" 只作算术引用（r=10/240 ⇒ E[leak]=1064+40·(10/240)=1065.7 b ⇒ f≈1.250 ⇒ 余量≈42.6 b ⇒ N≥288，ROADMAP §3 P1）；**6+4 跨实例相加为被禁 pooling**（ROADMAP §8 项 10；B2G 禁令），本包两实例分别报、禁合并。
4. 与既有 m=200 点的关系（标注、不等同、不合并）：`X1-2M-200S` = **standalone** m=200（REVISE R6：≠ P1 nested leading-200，CENSORED 13/163）；b2f F202 = **m=202**（BY CITATION）；P0 A200 = genie 口径（context）。**本包测的 nested leading-200 基线是 P1 §3/§5 Stage-1 口径，三者互不替代、互不合并。** m=200 测量所有权属 P1（P2 禁重测条款不变）；本包 = P1 Stage-1 的先行单独探针，**P1 冻结契约不改、P1 不执行**；P1 日后是否按引用消费本结果由主线程在 P1 授权时另决（不在本包）。

## §2 冻结科学输入（改动任一项 ⇒ STOP，回主线程；必要时先 OpenSpec）

| # | 项 | 冻结值 |
|---|---|---|
| F1 | 臂数 | **恰好 2 臂**：`S01-R1` 构造实例 **2026092001**（girth 8 记录值）；`S01-R2` 构造实例 **2026092011**（girth 6 记录值）。**分别报告，禁合并**（含 6+4 式求和）。 |
| F2 | m 点 | **m=200 单点**。基码 = 同实例冻结 **A208 矩阵的前 200 行 rows[0,200)**（nested leading-200；P1 §3 口径）。**非** P0 `construct_arm("A200",…)`；**不**新建 208 构造；**不披露**救援行 rows[200,208)；无 warm-start 问题（无 Stage-2）。 |
| F3 | 配对块 | **240 配对块/实例**；seeds **`2026095601+idx`**，idx 0..239；stream **`o1_blk:{seed}`**（与 O1R/P0/L1B/b2e/b2f/b2g/X1 同帧配对对比，**无独立性主张**）。 |
| F4 | 信道 | 2M 冻结合成信道：`docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` + `gamma_f03_pb.npz` **只读、永不 refit**；纯合成抽样，**零 `.ttbin` 读取**（任一读取 = STOP-BLOCKED）。 |
| F5 | 先验/解码器 | b2f 谱系 verbatim：π_i(e)=Σ_u1 γ1(u1\|b_i)·γ2(y_i⊕e\|u1,b_i)，y_i=b_i&31，`marg=np.einsum("nu,nuv->nv", g1c.T, cond)` + row-guard + `center_rows_prior`；喂 `v28.decode_error_domain_posterior(field, y.tolist(), dense, s_x, prior, 300)`；**max_iter=300 / streak 3**；接受 = **`exact_match`**；**NO genie u1 / NO argmax û1 / NO L1 码**。 |
| F6 | 构造 pins（Pre-EXECUTE，dry 零解码） | A208：`fc=0` + rank **208** + twice-identical（b2f/b2g manifest 既有 pin，重申）；基码：**rank(rows[0,200)) = 200 REQUIRED**，否则 **STOP-BLOCKED**；girth **measured/recorded/not-gated**。 |
| F7 | 会计 | **`f_super = (5·200+64)/852.544 = 1064/852.544 = 1.24803`**（V80_BASELINE §2 整帧含 64-bit tag 冻结口径：anchor H_full=0.83256272 b/sym ⇒ content=1024×0.83256272=852.544 b；1064/852.544=1.24803）；`f_eff = f_super + 4.785675·FER`（**逐实例各自 FER**，同基）；gate (b) `f_super ≤ 1.3` 在冻结 m 上**按构造成立**（算术恒等，非科学门）。**绝不把 f_super 当 f_eff 报**（FER>0 时）。 |
| F8 | 认证语境 | **key-eligible 200/276/364 仅引用为语境，本包一个也不消耗**（合成配对帧，不触任何真实帧/计数）；report-only：`N_req(f_super=1.24803)=⌈3·4.785675/(1.3−1.24803)⌉ = **277**`，零失败规则仅当 k=0 才相关；**本包不作任何可认证/文献可比主张**（X1 joint-∅ 结论不被本包触碰）。 |
| F9 | 早停 | **禁止 bar-12 早停**：两臂各解完全部 240 块——锚需要完整 k/240。bar-12（fails≤12，DECISION-1 内部路线上下文）**仅 report-only**，不触发停止、不裁决路线。 |
| F10 | 失败类别 | 非 `exact_match` = fail，计入 k；综合征有效但不匹配者另列 **`undetected` 单列，永不并入 success**（b2f-verbatim 规则，X1 F-a 先例）。 |

## §3 度量与产出模式（冻结计算规则）

- 逐块（`rows.json`/`block_accounting.csv`，列名与 X1 同构）：`block_idx, seed, iters, wall_s, decoded, failed, undetected, prior_entropy_bits, u1_mismatches`（后两项 report-only，b2f 先例）。
- 逐臂：`k/240`（= Stage-1 基线 fails）、`FER = k/240`、undetected 计数（单列）、iters min/max、wall 合计 + 块均值、峰值 RSS、构造标签（实例 + girth）、pins、信道路径、seeds/stream、`f_super=1.24803`、`f_eff=1.24803+4.785675·FER`（本臂自己的 k）、bar-12 report-only 上下文行、S0.1-gate 贡献行、claim-ceiling 行。
- **禁**：跨实例/跨块合并任何 FER 数；跨 m 单调性推断；引 f_super 为 f_eff；把本包 k/240 当真实数据 FER。
- 报告 `TRAIN/anchor` 基说明：F7 用 V80 冻结 anchor 基（与 P1 §2/§5 `E[leak]/852.544` 同基）；**不**另算第二基，避免混基。

## §4 门与 S0.1-gate（二元）

- **S0.1-gate（计划门，本包产出）**：两实例 m=200 软边际基线 FER **实测存在**（各臂 240/240 完整、非 wall-partial）⇒ **PASS** ⇒ P1 救援臂方可进入其自己的 packet 冻结/授权序（本包不授权 P1 任何执行）。任一臂 `INCOMPLETE-wall`/BLOCKED ⇒ **gate NOT satisfied** ⇒ **禁止按 10/240 外推冻结 P1**（EXECUTION_PLAN §5）。
- gate (b)：`f_super ≤ 1.3` —— 冻结 m 上按构造 PASS（F7），无裁决含义。
- bar-12 上下文：k≤12 记 `route-ctx PASS`，k>12 记 `route-ctx FAIL`——**均仅 report-only**；路线裁决是主线程的后续决定，不在本包。
- 批次关闭条件：两臂终态 + 单一 append-only 日志无歧义 + **§10.3 单次 batch-end 独立评审** + 主线程接受。评审 FAIL ⇒ 阻止该批证据晋级，回炉，不补跑未评审臂。**无逐臂评审/逐臂授权文件。**

## §5 预算 / 范围 / 停止 / 失败保留（冻结）

- **预算（≤ 单臂轻量；unspent budget ≠ authorization）**：**单臂 wall ≤ 3600 s**（单窗口，= P1 §7 单臂上限；本包工作量严格小于 P1 双 Stage 臂），**批次总 ceiling ≤ 7200 s**；**单调用 ≤ 300 s**（超时 = 终态，块计 fail，不续跑）；**RSS < 2 GiB**；**1 CPU**。
  - 依据（估，非承诺）：X1-2M-200S 1589.7 s/163 块（含 13 fail，≈9.75 s/块）+ b2f F202 1346.9 s/240（5.6 s/块）+ F208 672.6 s/240 ⇒ 全 240 嵌套基码估 **≈2200–2600 s/臂**；1800 s 上限会高概率 `INCOMPLETE-wall` 而毁掉锚，故取 3600 s。
- **停止**：任何科学输入变动（n/m/tag/H/λ/seeds/阈值/信道/解码器/假设/数据角色）⇒ STOP；任一 `.ttbin` 读取 ⇒ STOP-BLOCKED；wall-partial ⇒ **`INCOMPLETE-wall` 保留、永不续跑**；**无 retry/resume/adaptive**。
- **失败保留 + 至多一次预注册工程修复**：仅限基础设施失败（进程死亡、无 verdict 可得），科学输入/seeds/阈值/数据角色/假设**全部不变**，**≤1 次** repair+rerun，失败尝试在同一日志**保留记录**（含 exact error + unchanged-inputs 声明 + 保留位置）；未用修复时写明 "**no repair path used**" 行；第二次失败 ⇒ STOP-BLOCKED，batch-end 评审裁决（AGENTS §1.2 EXPLORE 合约）。
- **根**：机器根族 **`workspace/S0_1/`**，逐臂 fresh additive `workspace/S0_1/<arm>_<uuid8>/`（UUID + 缺席证明在 Pre-EXECUTE）；`results/`、`comparison_bench/outputs_comparison/` **禁写**；既有证据根（`workspace/p3_census_3954637c/`、`workspace/p3_stage05_ee32030a/`、`workspace/r1_histogram_5e2a91c4/`、15 个 `workspace/x1_*`）**只读不碰**；`git diff -- src/` 必须 EMPTY（I4）。

## §6 交付物与证据清单（执行时产出；本任务不产出任何一项）

1. 逐臂根 `workspace/S0_1/<arm>_<uuid8>/`：`S01_RESULT_<arm>_m200.md` + `rows.json` + `block_accounting.csv`。
2. 批次日志 `docs/research_cycles/V80-NBLDPC-JAN21/S0_1_EXPLORATION_LOG.md`（append-only）：条目 0 = Pre-EXECUTE Q0–Q6 记录（见 §10）；条目 1–2 = 逐臂运行（冻结顺序 R1→R2，各一次调用）；条目 3 = 收口 tally（两臂终态、总 wall、修复用否）；修复若用，附 exact error + unchanged-inputs 声明 + 保留位置。
3. `docs/research_cycles/V80-NBLDPC-JAN21/S0_1_BATCH_END_REVIEW.md`：**单次** batch-end 独立评审（§10.3：授权边界、机器门、保留失败、修复若用、最终证据、claim ceiling）。无逐臂评审文件。
4. 关闭后由主线程执行 memory triage（AGENTS §3）——本包含指针，不代执行。

## §7 EXPLORE 资格与合约（AGENTS §1.2 + §10.3）

- 五条资格：① 输入 = 已持久化直方图的合成抽样（非敏感、已批准开发输入，零 `.ttbin`）；② fresh additive `workspace/S0_1/` 根，可逆、有界（2×240 解码，ceiling 7200 s）；③ 不产生 FER/SKR/资格化/晋升/发表主张（见 §9）；④ 无破坏性覆盖、无新对外动作；⑤ 纯合成 ⇒ 非 DECIDE。
- 合约（两文件制）：**一个 packet+prompt 对**（本文件 + `S0_1_M200_PROMPT.md`，授权边界写在本 packet 内）+ **一个 append-only log** + **一个 batch-end 独立评审**；一次授权覆盖冻结臂序（操作者在前一机器门放行时继续下一臂，无逐臂授权）；至多一次预注册 repair+rerun；multi-seed 由构造满足（240 配对块 + 冻结 seed 流，不另造 seed 轴）。
- 升级：转真实数据、关路阈值、发表主张、破坏性输出、成本显著上升、或科学输入/假设变更 ⇒ 必须先升 DECIDE。对冻结解码器在合成抽样上调用**不**强制 DECIDE。

## §8 范围外 / FORBIDDEN（执行者与本任务共同遵守）

- 无真实/Jan-21 数据；无解码器/DE/图核改动；无先验 refit（`gamma_f03.npz` 只读）；**不执行 P1/P2/X1 任何臂**；不选运行点；不改任何冻结输入（F1–F10）；不发明 seeds/路径/计数/pins。
- 禁跨实例 pooling（含 6+4）；禁 `undetected` 并入 success；禁引 f_super 为 f_eff；禁跨 m 单调性推断。
- 禁写 `results/`、`comparison_bench/outputs_comparison/`；禁改 `src/`；禁 `tools/longrun_*`/`minrerun_*`/`routeA_*`；禁 `experiments/run_e2e_pipeline.py`；禁碰 **`docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`、`.gitignore`、`README.md`、`AGENTS.md`**；**禁 commit / push**。
- 若实现需要改动任何冻结模块/行为才能跑通 ⇒ **STOP 回主线程**（行为变更先 OpenSpec），执行者不得自行改需求或补常数。

## §9 Claim ceiling

- **仅**：合成配对帧上的 m=200 软边际**效率探针**（逐实例 k/240 + f_super/f_eff 冻结基 + iters/wall + undetected 单列），为 P1 提供实测锚。
- **非**：SKR、资格化、路线裁决、运行点选择、真实数据 FER、可认证/文献可比 `f_eff≤1.3` 句、发表材料。key-eligible 计数只引用不消耗。通用性表述若日后引用本包，必须两实例分列，**只报单实例冒充结论 = 禁止**。

## §10 授权门（EXPLICIT USER GATE — 停在这里）

- **本 packet 冻结 ≠ 授权。任何解码执行前必须同时满足：**
  (a) 入口前置：H0.1（X1 scoped 提交）完成或用户显式豁免（记录于日志条目 0）；
  (b) 执行面就绪：thin runner（若无既有 CLI 逐字跑 F1–F5）+ fake-only focused 单文件测试已实现——**实现本身无 track gate**（AGENTS §1.2 矩阵），track gate 挂在首次合成执行；
  (c) **Pre-EXECUTE Q0–Q6**（记入日志条目 0）：Q0 目标分支 `formal-ir-v72p1-addendum-clean`（不切分支）；Q1 范围清洁（仅 additive runner+测试；`git diff -- src/` EMPTY；脏树按显式文件清单界定，外源 `openspec/changes/binary-ldpc-v5-*` 不纳入）；Q2 冻结契约 F1–F10 逐项核对；Q3 输出缺席 + `rg 'S01_|S0_1_M200'` 仅命中本包族 + 保护根快照字节一致；Q4 **focused 单文件 fake-only 测试 PASS 并附输出**（E5 风险：batch-end 必须附此输出）；Q5 dry 零解码 pins（F6：A208 fc=0/rank208/twice-identical、基码 rank=200、girth 记录）——**Grant 前零生产解码**；
  (d) **FRESH EXPLICIT USER GRANT**，填入下方授权块（签名，或本周期 verbatim 对话授权记录——F-3/X1/X1S 先例，仅限本周期）：
  - **授权块（空白待签；未填 = 未授权）**：Acceptance ID `G-S01M200`；grant verbatim：________；臂根 UUID（R1/R2）：________；预算确认（≤3600 s/臂、≤7200 s 总）：________；日期 / 主线程：________。
- **未授权不得执行。** 本文件不授权解码、不授权测试长跑、不授权 commit/push、不授权任何 P1 臂。

## §11 本任务（planner 冻结）创建范围声明 — S01-3

- 本任务**只新建**本文件与 `S0_1_M200_PROMPT.md` 两份 docs；**未执行任何解码/测试长跑**；**未改动** `docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`、`.gitignore`、`README.md`、`AGENTS.md` 或任何其他文件；**未 commit、未 push**。
