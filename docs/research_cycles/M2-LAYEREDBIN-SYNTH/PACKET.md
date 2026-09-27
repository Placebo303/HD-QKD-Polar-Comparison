# M2 分层二元 LDPC 合成批次包 (M2-LAYEREDBIN-SYNTH) — FROZEN, NOT GRANTED

## §0 身份

- Acceptance ID (拟): **G-M2-LAYEREDBIN-SYNTH**。本包是冻结件，**不是授权**；授权任何执行 = 0。**未授权不得执行。停在授权前。**
- Track: 本次起草 = **doc-only 包起草，无 track gate** (AGENTS.md §1.2 矩阵 Documentation-only); **FUTURE 首次合成执行 = EXPLORE** (合成、有界、可逆；`EXPLORE_HEAVY` 注记按成本另定)。
- 分支: `formal-ir-v72p1-addendum-clean`; 冻结时点 HEAD **`8e9c8526`**。执行前必须重测 HEAD (若 HEAD 已移动则按 §3 停止门处理，重证分支/清洁度/输出缺席，不 silently 沿用旧时点)。
- 配套执行面: `M2-LAYEREDBIN-SYNTH-PROMPT.md` (同一授权边界) + 单一 append-only `EXPLORATION_LOG.md`。一包一 prompt，一授权覆盖冻结条件臂序列。
- 规划-only。本包不执行、不写 workspace、不 commit、不 push。

## §1 目的

1. 以**分层二元 (layered-binary) LDPC**做合成批次验证: **10 Gray 位面按位面熵分配行数 + 盲协调 (blind reconciliation)**，替换 V19 保守行数基线，测出本方法的合成 FER-vs-披露曲线。
2. 与 T1 / X1 **同网格可比**: 同 M0 网格 (F1)，同 N=240 分母，同会计列 (F5)，使分层二元臂与 NB (T1/X1) 臂可并排比较而不混淆构造。
3. 维度探针结论定位: 逐位面分解信息损失 **0.545% 仅为选型依据 (selection rationale)，非胜出证据**。本包不因该数主张分层二元优于 NB；胜负只看本包实测 FER/披露/效率。
4. 假设 (待测，非主张): 按位面熵分配 + 多段小步长盲协调能在 matched-disclosure 披露量级下达到与 NB 同量级 FER，且救援段公开量可单列审计。

## §2 冻结臂表 F1–F6

### F1 数据 (合成配对帧)

- 输入唯一来源 (只读): 冻结 `gamma_f03.npz` / `gamma_f03_pb.npz` (2M 冻结 lineage；1M/1.5M 用同 F03 estimator 家族已冻结 bundle，只读绑定，不重拟合；任何重拟合 = 科学输入变更 → STOP)。
- 网格 (同 M0 网格，三源各 2 点，共 6 臂基准 + 对照/盲臂见 F2–F3):
  - 1M: **{197, 201}**；1.5M: **{203, 207}**；2M: **{204, 208}**。
- 每臂 **N=240 块同分母** (paired blocks；失败数/240 为 FER 分母，不得另设分母)。
- 合成采样 only；零 `.ttbin` 读 (任何 `.ttbin` 读 = STOP-BLOCKED)。种子/流见 F4。

### F2 码率分配表 (10 Gray 位面按熵分配)

- 10 Gray 位面按位面熵分配总行数 m (本臂 m 基；见 F5 f 定义)。分配输入为**冻结** `H_L1+H_L2`:
  - 1M **0.801038** / 1.5M **0.825566** / 2M **0.832563** — 仅作分配输入，**不重拟合** (no refit；重估 H 即新包)。
- 每臂冻结一行分配表: `{plane j=0..9: 熵份额, 分配行数 m_j, Σm_j = m}` (执行时由 prompt 登记具体整数；本包冻结分配规则，不冻结逐行整数以外的任何自由度)。
- 对照设计 (同臂 m 基):
  - **matched-disclosure 对照臂**: 总披露与 NB 同量级 (同 m 下披露对齐，供并排比较)。
  - **盲协调臂**: 一组盲协调臂 (初始行 + 增量段，见 F3)，总披露 = 实际使用段累积 (含救援段单列)。
- 禁止用 V19 保守行数直接冒充本基线 (见 §3 停止门第 4 条)。

### F3 盲协调段表 (初始行 + 增量步长，多段小步长)

- 每盲臂冻结一段表: `初始行 m_init + 增量步长 {Δm_1, …, Δm_k}` (多段**小步长**；段数/步长执行前在 prompt 登记，执行中不得改表)。
- **救援段公开量单列**: 救援段 (rescue segment) 的公开量在会计中**单列** (见 F5 λ_total 分解)，不得并入 leak_EC 掩盖。
- 无自适应搜索、无阈值调参；段表走完仍失败 = 该臂 FAIL (CENSORED/failed 按 F5 图例记录)，不加段续跑。

### F4 构造种子 + 译码 pin

- 构造种子 (冻结字面量，T1/X1 同源流): 种子 `2026095601+idx` (idx 0..239)，流 `o1_blk:{seed}`；构造实例 SINGLE `2026092001` (曲线相干；不得多实例混池)。
- 构造 pins: **fc=0 + rank-full + twice-identical GATED**，girth recorded-not-gated。臂 ID 携带构造标签 (`M2LB-*-S<m>-layered`)。
- 译码 pin: 二元置信传播 max_iter / streak 在 prompt 登记冻结值后不得更改 (本包 pin 位置，具体整数由 prompt 冻结；任何译码核/DE/图核改动 = STOP)。
- `exact_match` accept；NO genie/argmax；`undetected` 独立成类 (见 F5)。

### F5 会计 (A-CMPE-1..7 全列)

每臂必须输出 A-CMPE-1..7 全列 (列缺失 = 机器门 FAIL):

- **attempted** (尝试块数；正常 240；bar-12 早停/INCOMPLETE 按实际记录并标注 CENSORED)。
- **exact_match = ¬failed 图例**: `exact_match` 接受；图例中 `¬failed` 仅为显示别名，不得改接受语义。
- **accepted / accepted_wrong 独立**: accepted 与 accepted_wrong 分列，`undetected` 永不并入 success。
- **f_super / f_notag / f_eff 本臂 m 基**: 以本臂实际 m 为基 (`f_super=(5m+64)/(1024·H_src)` 用 F2 冻结 H；`f_notag` 去 tag 对照；`f_eff=f_super+4.785675·FER` 冻结斜率；FER>0 时永不以 f_super 冒充 f_eff)。
- **λ_total 分解**: `λ_total = leak_EC + 64 (tag) + 救援公开量单列（不并入 f 分子） + 控制轮次/帧单列（如适用）`；`1.50×prior` 机会成本另起一行 report-only，不进 λ_total、不进 f 分子（prior 系数 1.50 冻结；不得合并/省略任一项）。
- **wall / RSS / 每帧消息数**: 每臂 wall (单窗上限见 §6) + max RSS（已有保留）+ 每帧消息数列（LDPC 级口径：层二元取 LDPC 级 3.14 口径独立标注；Müller Cascade 446 口径不混用，两口径不可互比须标）。
- **历史/探针行 (A-CMPE-6)**: 历史行（R3/MLC）与本包口径不一致即标“不可比”+原因（H 基/tag/池/分解）；r=10 探针独立成本行（2.1 s vs 19.4 s，native 臂不利如实，不并入主序列）；探针不替真实结论（§5 固定句逐字携带）；V19 f=4.169 为稻草人数，禁作本对照。
- **四列归属 (A-CMPE-7)**: 每个对外数字落 `measured` / `assumed` / `projected` / `qualified` 之一；本批合成结果 = `measured`（本机本实现）；分配输入 H = `assumed`；无预测外推（`projected` 为空）。
- **N_req report-only vs 200/276/364**: N_req 按冻结规则计算，仅 report-only，与 key-eligible 200/276/364 并排呈现，不做 certifiability 主张。
- **d / q / n_IR 分离**: d (汉明/符号距离口径) / q (字母表，Gray 位面 q=2×10 层声明) / n_IR (IR 块长) 各单列，不得混为一数。

### F6 根 (workspace)

- 臂根 **`workspace/m2lb_<uuid8>`** fresh additive (每臂一根；UUID 执行前冻结)。
- 缺席证明 (Pre-EXECUTE): `workspace/m2lb_*` 缺席；`rg 'm2lb_|M2-LAYEREDBIN-SYNTH'` 仅命中本包三文件；`results/` 与 `comparison_bench/outputs_comparison/` 快照字节一致；`git diff -- src/` EMPTY。
- `results/`、`comparison_bench/outputs_comparison/` FORBIDDEN；已有证据根只读不碰。

## §3 停止门 (同 T1/X1)

1. **改科学输入 = 新包**: n/m/tag/H/λ/种子/阈值/信道/prior/段表/分配规则/假设/数据角色任一变更即 STOP，需新包 (执行者不得 silently 纠正后继续)。
2. **单臂超预算 = INCOMPLETE 不续跑**: 超 wall/terminal/RSS 任一上限即该臂 INCOMPLETE，保留、不续跑、不跨窗接力；第二失败即 STOP-BLOCKED，交 batch-end review 裁决。
3. **至多一次预注册 repair**: 仅基础设施失败可 repair+rerun 一次 (科学输入/种子/阈值/数据角色/假设不变，失败尝试保留在同根+同 log)；第二次失败即 STOP。
4. **V19 行数冒充 = STOP**: 用 V19 保守行数冒充本基线 (不按位面熵分配重算行数) 即 STOP；必须按 F2 位面熵分配重算行数后以新包/修订包重新冻结。
5. 任何 `.ttbin` 读、跨源信道复用、pooling 跨源/跨 m/跨实例、`undetected` 并入 success、f_super 冒充 f_eff 均为 STOP-BLOCKED。

## §4 EXPLORE 合约

- 一包一 prompt 对 (本包 + `M2-LAYEREDBIN-SYNTH-PROMPT.md`)；一授权覆盖冻结条件臂序列 (operator 在前一机器门通过时继续臂间执行，无逐臂授权)。
- 一结果根序列 + 一 append-only `EXPLORATION_LOG.md` (尝试、预注册工程纠正、最终证据、batch-end review)；无逐臂 authorization/return/repair-review/rerun-review 文件。
- 至多一次预注册 repair+rerun (科学输入/种子/阈值/数据角色/假设不变，失败保留同 log)。
- 多图/多种子默认: N=240 配对块 + 冻结种子流即满足 (不另发明种子轴)。
- 升级: 真实数据、路由关闭阈值、发表主张、破坏性输出、实质更高成本、科学输入/假设变更前必须升级 DECIDE。仅调用冻结译码器于合成 bundle 采样不强制 DECIDE。

## §5 CLAIM CEILING

- 合成分层二元 FER-vs-披露曲线 ONLY (fails/240 + 本臂 m 基 f_super/f_notag/f_eff + iters/wall + undetected log + λ_total 四项分解)。曲线不选 operating point；operating-point 决策是消耗本曲线 (+P1 救援结果) 的 LATER DECIDE 步骤。
- Generality 标题以 1M 打头 (anti-cherry-picking)；**2M-only 标题 FORBIDDEN**。
- `H_L1+H_L2` 以 F03 estimator + TRAIN 分割侧为条件 (每行携带 provenance + split side)；逐位面 0.545% 损失数为选型依据，不作方法胜出证据。
- f-margin IN 与 N-count certifiability 是不同 verdict，必须分开；禁止将单源 f_eff 表述为可发表/可比文献数。
- 固定句（任何引用本批数值的文档必须逐字携带）：**“合成探针不替代不预示任何真实 FER/效率/泄漏/SKR；D1 条件化分支下不得用本批合成数论证真实优劣。”**

## §6 机器门

- **G-A (路由门)**: fails/240 ≤ 12 (内部 continue/stop 上下文，非 certifiability)。bar-12 早停臂 = FAIL + CENSORED (fails-at-stop/blocks-at-stop + projected NEVER)，永不外推至 240，永不 pool。
- **G-B (效率门)**: 本臂 m 基 `f_super ≤ 1.3` (F2 冻结 H)。
- **G-C (N 规则 + 表述禁令)**: `N ≥ ceil(3·4.785675/(1.3−f_super))` 逐臂求值 (预期高 m 通过 (a) 处几乎全 FAIL)；**FORBIDDEN: 将任何单源 f_eff 表述为 certifiable 文献可比数**。
- **G-D (绑定门)**: `bind_empirical_bundle()` shape/normalization gates + R1 校验和恒等式 + F2 分配表 Σm_j=m + F3 段表冻结一致性；FAIL 即该源 STOP-BLOCKED (他源可继续)，无 fallback bundle。
- **G-E (完整性/停止)**: 预算 (§6 预算: 每臂 wall ≤1800 s；单 decode terminal ≤300 s；RSS <4 GiB；1 CPU；总上限 = 已尝试臂数×1800 s) 持有；零 `.ttbin` 读；无跨源复用；无 pooling；无 `undetected` 合并；无 f_super-as-f_eff；无跨 m 单调性推断；`git diff -- src/` empty；保护根 untouched。FAIL 即 STOP-BLOCKED，batch-end review 裁决。
- 批次仅以 batch-end 独立 review + main-thread acceptance 关闭。任一门 FAIL 阻断该臂证据 promotion；永不 publish-then-patch。

## §7 授权块 (FROZEN + R1修订指针, 12臂已执行见LOG Entry3/4)

- §7-1 Bundle 根 UUID: **N/A (read-only, no build)** — 本包不构造新 bundle，只读消耗冻结 bundle，无新根待签。
- §7-2 臂根模式 (`m2lb_<uuid8>`): `workspace/m2lb_<uuid8>` fresh additive，每臂一根共 12 根；uuid8 冻结真值 01:18eb57a9 02:99d2bfef 03:d4d24a1a 04:2c09cb2d 05:bb3120fc 06:261d611c 07:24f99582 08:407d9236 09:b9a4fdd7 10:aae025fc 11:84150bd6 12:fc719214 (与 §7-7 臂序 01–12 一一对应，与 12 实建根一一对应)。
- §7-3 精确 bundle 路径 + key 前缀冻结: 只读 `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz` + 同胞 `gamma_f03_pb.npz`；key 前缀 `1M` / `1p5M` / `2M` (三源分 key 域)；key 形态为冻结 bundle 内三源各自独立 key (不跨源复用、不跨源拼 key)；防混声明: 三源 key 永不混用/复用/pooling，错 key = STOP-BLOCKED。f 分母用 FROZEN_H **0.801038 (1M) / 0.825566 (1.5M) / 0.832563 (2M)**，**永不用 H_corr**。
- §7-4 F2 分配表整数 + F3 段表 + F4 max_iter/streak 冻结值: F4 译码 pin **max_iter=300 / streak=3** (冻结后不得更改)。F2 等份额规则 + largest-remainder (10 Gray 位面按位面熵等份额分配总行数 m，余数按 largest-remainder 落整，Σm_j=m)；6 行整数表 (m:[分配]): **197:[20×7,19×3]**；**201:[21,20×9]**；**203:[21×3,20×7]**；**207:[21×7,20×3]**；**204:[21×4,20×6]**；**208:[21×8,20×2]**。F3 matched 全量 (matched-disclosure 对照臂用全量 m)；blind 臂 **m_init=m-20，Δ=[4×5]** (5 段每段 +4)，6 行表: 197:177+4×5→197；201:181+4×5→201；203:183+4×5→203；207:187+4×5→207；204:184+4×5→204；208:188+4×5→208。非均匀段表 BLOCKED 注: 任何非均匀步长/加段/改段表 = STOP-BLOCKED (须新包)。
- §7-5 网格/种子/实例 verbatim 确认: 网格 **1M{197,201} / 1.5M{203,207} / 2M{204,208}**，**N=240**；种子 **`2026095601+idx`** (idx 0..239)，流 **`o1_blk:{seed}`**；构造实例 **`2026092001`** (SINGLE，不得多实例混池)。
- §7-6 预算上限确认: 每臂 **wall≤1800s**，单 decode **terminal≤300s**，**RSS<4GiB**，**1 CPU**；总额 **12×1800=21600s**；**EXPLORE_HEAVY** 注记。
- §7-7 臂序确认 (12 臂表): **01–06 matched** (1M 打头: 01:1M-197-matched，02:1M-201-matched，03:1.5M-203-matched，04:1.5M-207-matched，05:2M-204-matched，06:2M-208-matched)；**07–12 blind** (2M→1.5M→1M: 07:2M-204-blind，08:2M-208-blind，09:1.5M-203-blind，10:1.5M-207-blind，11:1M-197-blind，12:1M-201-blind)。一授权覆盖条件序列: operator 在前一机器门通过时继续臂间执行，无逐臂授权。
- §7-8 显式用户授权 (签名或逐字 conversation grant 记录): 用户 verbatim 一并授权 — **“授权不用找我，我现在一并授权”** (签名栏填该句原文，不代签他名；主线程见证已落)。
- §7-9 日期 / 主线程: **2026-09-24** / 主线程见证已落 (12臂已执行待batch-end，主线程 acceptance 待签)。

## §8 验收 ID (G-M2-LAYEREDBIN-SYNTH 子项 E1–E8；同 T1 结构，种子表/段表断言改为本包表)

| ID | 断言 |
|---|---|
| E1 | F1 网格/分母: 三源 6 基准点齐全 (1M{197,201}/1.5M{203,207}/2M{204,208})，每臂 attempted=240 (或 CENSORED/INCOMPLETE 带原因)，分母无替换。 |
| E2 | F2 分配表: 每臂 10 平面分配行 Σm_j=m；H 输入为冻结 0.801038/0.825566/0.832563 且无 refit；matched-disclosure 对照臂 + 盲臂齐全；无 V19 行数冒充。 |
| E3 | F3 段表: 盲臂段表 = 冻结初始行 + 增量步长多段小步长；救援段公开量单列；无加段续跑。 |
| E4 | F4 种子/构造/译码: 种子流 `2026095601+idx`/`o1_blk:{seed}` + 实例 2026092001；fc=0 + rank-full + twice-identical GATED；max_iter/streak 为冻结值；零核改动。 |
| E5 | F5 会计: A-CMPE-1..7 全列 (attempted / exact_match=¬failed 图例 / accepted / accepted_wrong 独立 / f_super/f_notag/f_eff 本臂 m 基 / λ_total = leak_EC+64+救援单列+控制轮次/帧单列如适用；1.50×prior 另起一行 report-only 不进 λ_total 不进 f 分子 / wall+RSS+每帧消息数(LDPC 级口径) / N_req report-only vs 200/276/364 / d/q/n_IR 分离)。任一列缺失即 FAIL。 |
| E6 | F6 根/缺席: 臂根 `workspace/m2lb_<uuid8>` fresh additive + 缺席证明四项齐全；保护根字节一致；`git diff -- src/` EMPTY。 |
| E7 | 停止门/机器门: §3 四条 + G-A…G-E 二值 verdict 逐臂记录；INCOMPLETE/CENSORED/BLOCKED 保留未覆盖；repair≤1 且输入不变见证齐全。 |
| E8 | Claim ceiling: §5 逐句遵守 (1M 打头；无 2M-only 标题；无 operating-point 选择；0.545% 仅选型依据；f-margin 与 N-count 分开；无 FER/SKR/qualification/promotion/publication 主张)。 |

## §9 与 T0 关系

- T0 (若存在，为 NB/T1 前置合成基线) 拥有其 m=200 测量与构造；本包 M2LB 测量**按引用消耗** T0/X1 的 NB 对照点，永不替代其构造 (STANDALONE-vs-nested 区分沿用 X1 §2.3/§2.8: 同 m 数值非 interchangeable)。
- 网格重叠点 (如 2M{204,208} 若他包已跑) 遵守 run-ONCE: 先跑者测量，后者按引用消耗，永不重测、永不 pool、永不跨批合并曲线。
- 本包 median 产出 (分层二元曲线 + λ_total 分解) 供 LATER DECIDE 路由步骤与 P1 救援基座共同消费；本包内不做路由关闭决策。
