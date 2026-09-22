# 项目执行计划 / 路线图 — 2026-09-22（体检落地版）

- 性质：planning / decision 记录，**docs-only，不授权任何执行**（无解码、无 DE、
  无真实数据访问、无 commit/push、无资格化/发表 claim）。
- Track：documentation-only（AGENTS.md §1.2 适用性矩阵，无 track gate）。
- 与 `docs/ROADMAP-20260921.md` 的关系：该文是**科学宏观路线**（P0–P6、DECISION-1/2/3）；
  本文件是**执行与恢复计划**——把 2026-09-22 全库体检结论落成可排期的门、任务包与卫生债清单，
  并在科学路线之上补 claim 目标裁决、工程卫生、过程减负三条轨。两文冲突时：
  **科学冻结口径以 ROADMAP/V80_BASELINE 为准，排期与卫生动作以本文件为准**。
- 上游依据：`docs/ROADMAP-20260921.md`、`docs/V80_BASELINE_20260921.md`、
  `docs/decision-log.md`（尾部 2026-09-21/22）、`AGENT_PROJECT_MEMORY.md`（尾部
  R1 / X1 / prior-cost）、`docs/research_cycles/V80-NBLDPC-JAN21/`（含
  `X1_EXPLORATION_LOG.md`、`X1_BATCH_END_REVIEW.md`）、
  `docs/v72p3-progress-and-issues-report-2026-09-19.md`（§B 工程债）、
  `docs/PRIOR_COST_*_20260921.md`、git/openspec/tests/workspace 实测计数。
- 仓库实况快照（2026-09-22 计数，执行前应重测）：
  - 分支 `formal-ir-v72p1-addendum-clean`，HEAD `e038f3c5`；
    相对 `main` **562** 提交、相对 `origin/formal-ir-v72p1-addendum-clean` **ahead 45**。
  - 工作区未提交：X1 执行器/测试 + 7 份 X1 cycle 文档 + memory/baseline 修改；
    另有外源未跟踪 `openspec/changes/binary-ldpc-v5-*`（并行 checkout，禁止纳入本线 commit）。
  - OpenSpec：**144** 个 live change 目录 / **26** 个 archive。
  - `comparison_bench/tests` **234** 个测试文件；`cli/` **109** 个入口；
    `workspace/` **1774** 个实验根目录。
  - `.venv` 目录存在但无 `Scripts/python.exe`；Windows 侧当前解释器为
    `D:\software\Miniforge3\python.exe`（与 AGENTS.md §8「仅用 repo venv」不一致）。

---

## 1. 体检结论（事实 → 判断）

### 1.1 科学主结论（带作用域，不在此重述全部证据）

| 结论 | 作用域 | 对执行的含义 |
|---|---|---|
| 可解码性不再是约束（软边际 L2、F208 两构造实例各自 0/240） | 合成配对帧；禁合并；非真实数据 | 不要再优先堆更强解码器 |
| 预算/认证是唯一硬约束；A208 余量 4.31 b | 冻结 `f_super=(5m+64)/852.544` | claim 目标必须先裁决 |
| X1：三源 route-gate `m_min` = 2M **204** / 1.5M **203** / 1M **197** | 冻结网格分辨率；网格外未映射 | P1 救援基点有了输入 |
| X1：**joint 可认证集合为空**（route-pass ∧ count-certifiable = ∅） | key-eligible 200/276/364；零失败仍待 | n=1024 上 `f_eff≤1.3` 文献可比数字结构性拿不到 |
| prior/calibration 成本缺口 CONFIRMED；绑定口径 = 一次性工厂标定 + 每源 1.50× 机会成本 | 不改 `f_super`/`f_eff`；改净钥/可认证计数 | S3/论文前必须补 amortization 声明 |
| 吞吐单线程 ≈ **1.83 kb/s**（2.80 s/块）≪ 采集 ≈ **6.7 kb/s** | 采集率非 SKR | “真实场景”卖点目前空心，须硬轨补测/优化 |
| 合成→真实迁移未验证；无记忆假设“未证伪≠已验证” | 三源、功率主导 | P3 记忆审计是 S3 前置门 |
| 战略：测最差源（1M）作通用性锚点，禁止只报 2M | 用户 2026-09-21 指令 | headline 规则写进所有对外材料 |

### 1.2 过程与仓库健康（与 AGENTS.md §1.1 第一性原则对照）

| 观察 | 判断 |
|---|---|
| EXPLORE 批次七件套文档 + readiness 十项全量独立复核 + 对话授权/事后追认反复出现 | 纸面成本在挤占算法时间；§1.2 文字已减负，实践未完全跟上 |
| `AGENT_PROJECT_MEMORY.md` 4281 行 / `decision-log.md` 4836 行 / `AGENT_HANDOFF.md` 141KB 且顶部停在 V34 | 新会话冷启动成本过高；交接面误导 |
| 根目录堆满 v65–v72p0 产物与根级 `test_v*.py`；`workspace/` 1774 根 | 证据可追溯性尚可，导航与污染成本过高 |
| OpenSpec 82% 未归档；CLI 109 个历史入口 | 变更管理失焦 |
| `pytest.ini` 硬编码 Windows basetemp；多文件 pytest 命名空间污染；WSL/Windows 判定不一致 | 回归不可信，只能“按文件跑” |
| 562 提交未发布 + X1 成果未提交 + 外源目录混入风险 | **成果丢失/串线风险高于单次算法失败风险** |

### 1.3 一句话

**算法上“能纠”已过关；发表上“能证”与工程上“能用”未过关；仓库上“能不丢、能找着、能跑测试”也未过关。**
本计划的三条轨正是对应这三件事。

---

## 2. 总目标与 claim 目标裁决门（G0）

### 2.1 总目标（不变）

在真实 HD-ToA 数据上，用实测经验 P(y|x)、显式记忆检验、verification-aware
`λ_total`，交付端到端可复现的 FER / 泄漏 / 交互 / 吞吐，并给出诚实的
同数据二元 MLC / R3 对照。

### 2.2 G0 — claim 目标裁决（**阻塞 P1 重臂与 P5**，须用户书面三选一）

| 选项 | 主张 | 必经路径 | 优点 | 代价 |
|---|---|---|---|---|
| **(A) 文献可比认证** | 对外主数字 `f_eff ≤ 1.3` 且 FER 置信上界落在臂余量内 | **P4 n=2048 前置**；1M 降级诊断源；S3 主要由 1.5M/2M 承担 | 与 Müller/Zhou 曲线可比 | n=2048 构造/DE/decode wall≈4×；1M 无法 headline |
| **(B) 实测效率曲线 + 同数据对照**（**推荐默认**） | 实测 FER-vs-m、`f_super`/`f_eff` 双数、完整会计、vs 二元 MLC/R3 | P1 轻探针 → P3 → P5（n=1024）；P4 作第二代 | 不依赖不可达的认证 N；贴合“真实数据实测”差异化；通用性可报 1M | 不能给单点 `f_eff≤1.3` 认证句；需在表述规范中显式拒绝该句 |
| **(C) 补采数据** | 仍可走 (A) | 实验台采集 + 新 registry | 样本量解套 | 周期最长；本仓库不可单独完成 |

**推荐：G0 = (B) 为主文主张，(A) 作为并行/第二代扩展实验（P4 构造可行性可提前做，零解码）。**
理由：X1 已证明 joint 可认证集合为空；在 key-eligible 200/276/364 下硬追 (A)
会把 P1/P5 变成赌一个已知不可达的门。若用户坚持 (A)，则 **立即把 P4 升为 S3 前置必经**，
并在 S3 包冻结前逐源列出可认证判定表（ROADMAP P5 已要求）。

**G0 未裁决前禁止：** 冻结 P1 重臂（4×3600 s 级）、启动 P5、任何对外 `f_eff≤1.3` 认证句、
任何 qualification/promotion 材料。

---

## 3. 三条执行轨

```text
轨 H（卫生/防丢）  ──独立、不阻塞科学──►  H0 立即 / H1 两周内
轨 P（过程减负）  ──与 H 并行──►         P0 规则落地 / P1 观察两个周期
轨 S（科学/算法） ──G0 之后分叉──►        S-轻探针 → (B) 或 (A) 主路径
```

### 轨 H — 仓库与环境恢复（优先级最高，因风险不可逆）

| ID | 动作 | 验收 | 轨道/权限 | 建议窗口 |
|---|---|---|---|---|
| **H0.1** | 提交 X1 已完成成果（scoped：`x1_arm_runner.py`、`x1_bundle_build.py`、两测试、`X1_*.md`、memory/baseline 既有修改中属于本线者） | 工作区对本线文件 clean；`binary-ldpc-v5-*` **不在** diff 内 | 用户显式授权 commit/push | **立即** |
| **H0.2** | 推送具名分支 `formal-ir-v80-nbldpc-jan21`（普通非强制）+ PR | origin 可见 PR；不 merge 进姊妹 Polar 线 | 用户显式授权 push | **立即** |
| **H0.3** | 隔离外源 `openspec/changes/binary-ldpc-v5-*` | 移出或 gitignore 策略写明；本线 commit 范围文档化 | docs/工程，无 track gate | 立即 |
| **H0.4** | 修复解释器契约：重建 `.venv` **或** 改 AGENTS/README 写明 Windows=conda、WSL=`.venv`，并给出一条 `python -c "import numpy,pytest"` 验证命令 | 两种环境其一可复现；与 §8 不再矛盾 | 文档/环境 | 立即 |
| **H0.5** | 写一屏 `docs/NOW.md`（分支、G0 状态、活跃门、禁止事项、权威指针） | 新会话只读 NOW + 本计划即可接手 | docs-only | 立即 |
| **H1.1** | 根目录归档：`v65_*`–`v72p0_*` 产物、根级 `test_v*.py`、`总体判断.txt` 等 → `docs/archive/legacy_v65_v72p0/` 或 `workspace/legacy/`（**move 不删**） | 根目录仅保留入口文档/配置；archive 有 INDEX | 无 track gate；不动 `results/` 与被引用证据根 | 两周内 |
| **H1.2** | OpenSpec 收敛：仅保留 V80 线 + 未完成契约 + `amend-*`；V1–V72P2 已关闭项按 `completed` / `superseded-before-execution` 归档 | live change ≪ 当前 144；archive 带 disposition | 按 AGENTS §6；本文件不代为归档 | 两周内 |
| **H1.3** | CLI 收敛：历史 runner → `cli/legacy/`；活跃 = V80 套件（`x1_*`/`p3_*`/`r1_*`/`v80_*`）+ `smoke_test` | `cli/` 顶层可数；legacy 有清单 | 代码移动，不改语义 | 两周内 |
| **H1.4** | 记忆瘦身：`AGENT_PROJECT_MEMORY.md` / `decision-log.md` 保留**规则 + 2026-09 当前周期**；D1–D19 及更早 → `docs/memory-archive/` | 文件头不再写“从 4240 行读起”；新条目 tail 即当前 | memory/docs | 两周内 |
| **H1.5** | `AGENT_HANDOFF.md` 顶部改为指针 → `docs/NOW.md` + 本计划；V34–V36 全文降 archive | 顶部一屏内能看到 V80 现状 | docs-only | 两周内 |
| **H1.6** | `workspace/` 治理：只读压缩/移走未引用旧 root；保留 X1/R1/P3 等被 cycle 文档引用的证据根；清根下 `tmp*`、异常目录名（如 `CodeHD-QKD_...regression`、裸 `D`） | 引用完整性抽查通过；磁盘/导航可接受 | 不删证据；move/归档 | 两周内 |
| **H2.1** | 测试可跑性：`pytest.ini` portable basetemp（或 PYTEST_DEBUG_TEMPROOT）；`testpaths` 默认 `comparison_bench/tests`；标 `@pytest.mark.v80/legacy/slow` | 单命令收集不炸；`v80` 子集可跑 | 工程债（v72p3 §B2） | 两周内 |
| **H2.2** | 多文件 pytest 污染修复 **或** 正式文档化“按文件跑”命令模板并挂进 NOW | 不存在 82-failed 级假警报复发路径 | 工程债（v72p3 §B3） | 两周内–下月 |
| **H2.3** | “根节点不存在”类断言 fix-dead 收口 | 失效用例清单清零或标 xfail+原因 | 工程债（v72p3 §B1） | 下月 |

### 轨 P — 过程减负（保护第一性原则，不削弱科学门）

**原则：** EXPLORE 的独立性集中在 **batch-end**；DECIDE 的 Pre-EXECUTE / Pre-RESULT **不动**。
禁止把减负理解为跳过 claim 边界、no-overwrite、`undetected` 隔离、失败保留。

| ID | 规则变更（建议写入下一 OpenSpec 或 SOP 修订） | 现状 → 目标 |
|---|---|---|
| **P-1** | EXPLORE packet **两文件制**：`<NAME>_PACKET.md`（prereg+冻结科学输入）+ `<NAME>_PROMPT.md`（可复制执行面）；auth 边界写在 PACKET 内 | 现七件套 → 两文件 + 单 `EXPLORATION_LOG.md` + 单 batch-end |
| **P-2** | EXPLORE readiness：packet 冻结 + focused tests 通过 + 一页 checklist ⇒ 免十项全量独立 R-review；**batch-end 仍独立** | 现 readiness 全套 → checklist |
| **P-3** | 授权模式定型二选一：**(i)** 签字块，或 **(ii)** 主线程对话授权 + 本周期事后追认（F-3/X1 先例成文） | 现临时特批反复 → SOP 可审计表述 |
| **P-4** | coder-fast COMPLETE 后必接 reviewer-go **仅限 DECIDE 与 claim-bearing 交付**；EXPLORE 批次以 batch-end 满足 | 与 2026-09-13 F4 一致，消除执行歧义 |
| **P-5** | 单一现状页权威：`docs/NOW.md` > 本计划 > ROADMAP > 专题 cycle；README/CURRENT_MAINLINE/HANDOFF 只保留指针+一句状态 | 多处“Current Status”漂移 → 单源 |
| **P-6** | 任务包返回条件仍二元：全部冻结项完成 **或** 阻塞（命令/报错/已试/需决一事）；禁止“进行中”式空返回 | 不变，但减少包数量本身即减负 |

落地方式：属工作流规则变更，**走 OpenSpec**（建议名 `explore-packet-slim-and-now-authority`），
与 H1.2 归档批次错开，避免一次改两百个目录。

### 轨 S — 科学与算法（对齐 ROADMAP P1–P6，按 G0 分叉）

#### S0 — G0 前可做的**轻量**工作（不消耗 claim）

| ID | 动作 | Track | 依赖 | 说明 |
|---|---|---|---|---|
| **S0.1** | 软边际 **m=200 FER 探针**（240 配对块；两构造实例分别报） | EXPLORE（可 HEAVY 注记） | H0.1 后新 packet | 为 P1 “10/240”外推提供唯一合法锚；**先于**任何 3600 s 级救援臂 |
| **S0.2** | P4 **构造可行性**（n=2048 PEG/联合图，**零解码**） | EXPLORE | 无 | 便宜；决定 (A) 是否物理可行 |
| **S0.3** | prior **amortization / reuse 声明**一页（`gamma_f03` 一次标定、禁跨源复用、每源 1.50× 机会成本、披露路由） | docs-only → 并入会计 OpenSpec | prior-cost 三重审计 | S3/论文前的唯一缺失文档 |
| **S0.4** | P3 真实帧记忆/一致性审计包冻结（零解码；DECIDE 才执行） | 包=docs；执行=DECIDE | G0 不强制，但 S3 前强制 | ROADMAP P3 原样 |
| **S0.5** | 吞吐**测量**原型（交互轮数/消息数 + 现状 wall/块 重测） | EXPLORE | 无 | 先测清缺口，再动 EMS/并行 |

#### S-B — 若 G0=(B)（推荐）主路径

```text
S0.1 m=200 探针
  → P1 单段救援（m_base=200, Δm=8, 总行≤208；两构造实例分报）   [EXPLORE_HEAVY]
  → P3 记忆审计执行                                          [DECIDE]
  → P5 S3 真实数据（n=1024；key-eligible 200/276/364；对照=二元 MLC+R3） [DECIDE 全合约]
  → P6 吞吐 EMS/TEMS + 帧级并行，目标 ≥ 采集量级或如实报缺口   [EXPLORE → 并入 P5]
  → P4 n=2048 作第二代并行（不阻塞 S3）
```

P1 冻结时沿用 ROADMAP §3 修订后臂集（仅 m_base=200 单段）；预测数字**不得**预设，
以 S0.1 实测为准。claim ceiling：合成配对帧上的速率自适应效率；非 SKR/资格化。

#### S-A — 若 G0=(A) 主路径

```text
S0.2 n=2048 构造可行性（必须 PASS）
  → P4 构造 + DE 阈值点（P2 可并入）                         [EXPLORE → 科学输入变更处 DECIDE]
  → P3 记忆审计
  → P5 S3（n=2048；1.5M/2M headline，1M 诊断）                [DECIDE]
  → 每源可认证判定表写入 S3 包（冻结前）
```

P1 救援在 (A) 下可降为诊断子臂，避免双线烧预算。

#### 明确停放（维持 ROADMAP）

- NB-Polar 姊妹 worktree MVP、PA-aware 主攻、Scarinzi 逐块自适应、
  A196/m1=10–16 分层重做、tagless 会计作 claim —— **停放/仅敏感度行**。
- 禁止：`f_super` 当 `f_eff` 报；6.7 kbit/s 说成 SKR/IR 吞吐；数据说成 BBM92 偏振层；
  跨源/跨构造实例合并 FER；`undetected` 并入 success；引用撤稿 Mao；只报 2M 冒充通用性。

---

## 4. 分期排期（建议）

> 每期结束条件写死；未完成项**不得**静默滚入“继续做”，须显式结转。

### 期 0 — 防丢与单源现状（**Day 0–2**）

- 完成：**H0.1–H0.5**，**S0.3** 初稿，G0 裁决问题提交给用户。
- 出口：X1 已发布（或用户明确拒推并记录）；`NOW.md` 存在；G0 ∈ {A,B,C,未裁决-阻塞}。
- **计划+README已本地提交 `5d33d735`（未push）；decision-log/memory追加未提交。本文件不代为 commit/push；H0.1/H0.2 需用户一句显式授权（2026-09-22 已给：G0=B）。**

### 期 1 — 卫生与便宜科学（**Day 3–14**）

- 完成：**H1.*** 主体、**H2.1**、**S0.1**、**S0.2**、**S0.4 包冻结**、**S0.5** 测量报告、
  G0 落地为 S-B 或 S-A 的首个 packet。
- 出口：根目录可导航；测试 `v80` 子集可单命令跑；P1/或 P4 的**第一个可授权包**已冻结且停在显式授权门前。
- 轨道注记：S0.1/S0.2/S0.5 = EXPLORE；H/P = 无 track gate（实现/文档）。

### 期 2 — 主路径第一臂（**Week 3–4**，授权后）

- (B)：P1 救援臂执行 + batch-end；或 (A)：P4 构造/DE 批次。
- 出口：机器终态 + batch-end review + 主线程 route 裁决（接受/改道/停止）。
- 预算沿用 ROADMAP：P1 3–4 臂 × ≤3600 s；DE ≤96 调用 + ≤1200 s。

### 期 3 — S3 前置与真实主张（**Week 5+**，逐包授权）

- P3 执行（DECIDE）→ P5 包冻结（含逐源可认证判定表、prior 会计、对照臂）→ S3。
- P6 优化与 P5 并行；P4 视 G0 决定是否升为必经。
- 出口：论文级数字草案（含禁止句检查表）或明确的缺口声明。

---

## 5. 门禁与停止规则（汇总）

| 门 | 内容 | FAIL 时 |
|---|---|---|
| **G0** | claim 目标 (A)/(B)/(C) 书面裁决 | 禁止 P1 重臂、P5、认证句 |
| **H-gate** | 无未发布 X1 级成果；解释器契约一致；外源目录已隔离 | 停止新的长臂，先 H |
| **S0.1-gate** | m=200 软边际 FER 实测存在 | 禁止按 10/240 外推冻结 P1 |
| **P3-gate** | 真实帧记忆审计差异在预注册容差内 | 禁止把合成 FER 当真实 FER；先帧级条件化 |
| **P5-gate** | 每源：`f_eff` 上界在余量内 + `undetected=0` 隔离 + prior/amortization 已披露 | 该源降级诊断性；不得合并源“凑认证” |
| **P6-gate** | 吞吐 ≥ 采集量级 **或** 缺口已量化写入对外表述 | 禁止“真实场景可用”空心句 |

**授权边界（全文有效）：** 本文件不授权解码/DE/真实数据/commit/push/资格化。
每个 EXPLORE/DECIDE 包仍按 AGENTS.md §1.2 / §10.3 走独立授权与评审。
EXPLORE 失败保留、至多一次预注册工程修复+重跑；DECIDE 不可变失败保留与
Pre-EXECUTE/Pre-RESULT 不因本计划减负而豁免。

---

## 6. 风险登记（执行层，补 ROADMAP §6）

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| E1 | 562+ 提交 / X1 未提交期间磁盘或串线事故 | 不可逆丢成果 | H0.1/H0.2 最高优先 |
| E2 | G0 久悬不决 | 期 1 后无法冻结任何重臂 | 期 0 出口强制 G0 状态枚举 |
| E3 | 卫生战役扩大成重构 | 违反第一性原则 | H1 只 move/归档/清单；不改科学语义 |
| E4 | 过程减负被误读为跳过 DECIDE 门 | claim 事故 | P-4/P-6 明文；batch-end 不省略 |
| E5 | pytest 仍不可信 | 假失败导致错误 route 停 | H2.1/H2.2 前长臂 batch-end 必须附 focused 单文件测试输出 |
| E6 | 外源 `binary-ldpc-v5-*` 混入 commit | 姊妹线 crosstalk 重演 | H0.3 + H0.1 scoped manifest |
| E7 | P1 仍按无据 FER 外推 | 预算浪费 | S0.1-gate |

---

## 7. 立即下一步（可复制执行序）

1. **用户授权**后：H0.1 提交 X1 scoped 树 → H0.2 推 `formal-ir-v80-nbldpc-jan21` + PR。
2. 并行文档：H0.5 `docs/NOW.md`、H0.4 解释器契约、S0.3 prior amortization 一页。
3. **用户裁决 G0**：回复 “G0=A” / “G0=B” / “G0=C”（或改写主张句）。
4. 按 G0 冻结 **S0.1**（B）或 **S0.2+P4 构造**（A）的第一个 packet + prompt，停在显式授权门前。
5. 期 1 卫生项开 OpenSpec 或直接 docs PR（H1 归档建议独立 PR，便于 review）。

**本文件不授权任何执行、不冻结任何实验包、不产生新的科学结论。**
