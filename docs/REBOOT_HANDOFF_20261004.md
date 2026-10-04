# REBOOT HANDOFF — 仓库毛病总结 + 强制规则 + 下一阶段计划（2026-10-04）

> 文档类别：documentation-only（AGENTS.md §1.2 矩阵，无 track gate）。本文不授权任何执行。
> 适用对象：**接手本仓库的任何新 session / agent**。开工前必读全文。
> 地位：本文是对 AGENTS.md 的**更严格补充**（AGENTS.md §1.2 允许领域追加更严的科学要求）；
> 与 AGENTS.md 冲突时以 AGENTS.md 为准，但本文 §2 的禁令只会更严、不会更松。
> 数字来源：本文 §1 的数字来自 2026-10-04 只读审计（两份子代理报告 + 主线程现场核对），
> 引用前请按给出的路径复核；标「推导」的不是测量值。

---

## 0. 一句话现状

8 月以来 1000+ 次提交、140 个周期目录，**真实帧上最好的实测 `f_eff` 仍是 1.46–1.75**（M0，
`docs/research_cycles/M0-REALFRAME/RESULT.md`），合成上约 1.28；而隔壁 Polar 仓库在**同量级数据**
（495,415 对）上用 MSD + 长码 + 期望良率口径 + 增量披露，三天收口，平均 f ≈ 1.35（推导，见 §3.1）。
项目不是缺算力或缺数据，而是**方法论和流程出了系统性问题**。下面逐条列出，并定为强制规则。

---

## 1. 前任 session 犯过的错误（事实清单，不得重犯）

### E1 在一个与真实瓶颈无关的玩具上做随机游走
- 2026-09-30 → 10-04 跑了约 36 个 `NBLDPC-GF32-*` 探针：H52×128 GF32、iid 合成信道、
  **同一组 6 张固定图**、每批 192 帧，每次只改一个旋钮（damping、iter-cap、row-order、
  label、degree、MRB、joint-topk、edge-state、residual…）。
- 结果：绝大多数 `NO_SUFFICIENT_SIGNAL`；唯一正信号 soft-prior rescue（142→156）代价
  约 6× BP 迭代；后续十余个变体增量都在 ±4 以内。
- 128 符号块与真实主线（1024 符号超帧、真实信道）几乎无关；**合成→真实本身已被证伪为
  可靠代理**（M0：6 臂中 5 臂真实差于合成）。

### E2 实验在统计上注定看不见目标效应
- 192 对配对、典型增量 ±2–4：单侧符号检验 p ≈ 0.06–0.25，与噪声不可区分；只有 ±12 以上
  才可能显著。每批事先没有算 MDE（最小可检测效应）就开跑。
- 预注册的 control range 反复自我失效：5 批因基线超出 153 上限被判
  `CONTROL_RANGE_UNINFORMATIVE`；分类器 bug 出现两次。

### E3 自设一个结构上永远过不了的门，然后围着它打转
- `f_eff ≤ 1.3` 的零失败认证需要 `N_req` ≈ 2842 块（A208），而 3 s 采集的 key-eligible 块仅
  200/276/364（`docs/V80_BASELINE_20260921.md` §2–3）。
  `RESEARCH_DIRECTION_REPORT_20260924.md` 自己承认这是「在 3 s 数据上注定失败」的自设门。
- 隔壁仓库根本不用这种门：用**期望良率** `Y = kept − tag − kept·Σp̂`（p̂ 来自样本外验证帧）
  + 多 seed 配对 + SE/MDE，FER 1–3% 也照样给出可比较、可发表的效率。

### E4 KILL 掉一条路线之前没对照理论和邻仓
- Stage 0「逐面二元分配」KILL（`workspace/s0_1bbe38ac/`）：
  `comparison_bench/src/comparison_bench/cli/perplane_stage0.py:103` 每面码率用**无条件**
  `h2(p_k)`，Σh2 ≈ 1.64·H(A|B) ⇒ f=1.3 需 1875 bit > 1104 ⇒ KILL。
- 但按链式法则，**MSD 逐面条件译码**下 Σ H(b_k | B, b_<k) = H(A|B)。隔壁
  `../HD-QKD_Polar_Release/low_dim_opt/README.md` §2 原话：「低维效率低的主因是逐比特面独立硬判决；
  MSD 条件译码把上限抬回 I_AB」。我们 KILL 的恰好是已知的错误设计，正确设计从未被测试。
- Layered-Binary 基线 36/28,000 很可能同病（推导，待核实）。

### E5 算术 / 口径错误反复出现
已在案的例子（每一条都曾被当作结论引用过）：
- JOINT-PRICING：tag 64 bit 重复计入 ⇒ KILL 实为 MARGINAL（1100 vs 1104）。
- 「≈1099 vs 1104、回退后仍可行」从未实际计算；`+20%` 回退实为超 215 bit。
- M2 展示列 `f_notag = 5m/(1024·H)` 公式里**根本没有泄漏项**，跨方法相等是机械强制。
- MRB 批 `summary.json` 身份字段错误，需整批重聚合（`NBLDPC-GF32-MRB-REAGGREGATE-20261001`）。
- 失败诊断里把负 log-belief 直接归一化，truth-rank/熵统计全错后撤回（`NBLDPC-CORRECTION-PRIORITY-20261003.md`）。
- RSS 单位 KiB 当成 B，运行时字节门从未正确执行（GLOBAL-CENSUS）。
- NOW.md 两次声称「已更新快照」实际未改。
- 「2–4x」合成-真实倍数、「366 sym/s」吞吐在仓内**无测量来源**，却被流传引用。

### E6 流程吞噬科研
- 9 月提交：docs 165 vs feat 53 + fix 22（约 2:1）；decision-log 5,627 行；
  decision-log 中 STOP 39 行、KILL 19 行、INCOMPLETE 12 行。
- 31 个 `nbldpc_gf32_*.py` 共 26,053 行，每个约 1000 行，绝大部分是账本/manifest/资源样板，
  真正的算法差异只有几十行；58 个 gf32/nbldpc OpenSpec change 目录（一探针一 change）。
- 每批收尾都是「判定词 + pass with comments + 等用户裁决」，没有给出带预期收益的下一步建议。

### E7 授权后撞墙、数据全丢
- M3C R2 5,280 s INCOMPLETE；Proxy A >3,600 s **零落盘**；Proxy R2 35/40 块被 SIGTERM；
  C 轨 51 s/块 × 240 > 预算被判 KILL。根因：纯 Python 译码慢 + 不逐块落盘 + 开跑前没做计时 smoke。
- 10-03 用户指示「加速先放缓，只做改语言等不影响纠错能力的加速」被理解成「不做加速」，
  但不加速就跑不完真实帧实验——**等价数值移植是纠错研究的前置条件，不是旁支**。

### E8 不提交、仓库卫生失控
- HEAD 停在 2026-09-27（`23183c73`）；之后一周的全部工作（约 50 脚本、约 50 测试、约 40 周期目录、
  4 个 OpenSpec change）**全部未提交**，未跟踪条目 212 个。
- 约 165 个 tracked 文件仅因 CRLF/LF 显示为已修改（真实内容改动只有 5 个文件）。
- 仓库根出现路径拼接 bug 产物 `workspacegf32_full_eff_tests_20261002_e5/`、`..._full/`（缺 `/`）。

### E9 措辞越界与反复撤回
- M3D 宽泛否定句、B 轨「需新代价类」、裸「independent」、「no easier point」等均被撤回；
  每次撤回都要追加 supersession 文本，进一步膨胀文档。

---

## 2. 强制规则（MUST / MUST NOT）——违反任一条即视为任务失败

> 这些规则针对 §1 的具体错误。不得以「EXPLORE」「只是小探针」「流程要求」为由豁免。

### R1 先算效应能否被看见（针对 E2）
- **MUST**：任何解码实验在写包之前，先写出「目标效应大小」和按样本量算出的 MDE（80% 功效、α=0.05）。
  MDE > 目标效应 ⇒ **不得运行**，要么加样本、要么换设计。
- **MUST NOT**：用 n≤6 张图的逐图正负计数当证据；用 192 对检测 ±5 以内的差异。

### R2 每个实验必须说明它如何推动真实数据效率（针对 E1/E3）
- **MUST**：包首一句话写清「若成功，预计真实帧 f（或期望良率）改善多少、依据是什么」。写不出来就不做。
- **MUST**：合成信道只允许用**由真实联合直方图标定**的模型；iid marginal-shape 玩具信道不得再作主线证据。
- **MUST NOT**：再开新的 GF32 128 符号单旋钮探针（含任何 soft-prior 变体扫参）。soft-prior rescue
  只作为一个候选机制保留，下一次出现时必须是在真实标定信道 + 主线块长上。

### R3 主度量是期望良率 / 带 CI 的 f，不是零失败认证（针对 E3）
- **MUST**：主度量用 `Y = kept − tag − kept·Σp̂`（p̂ 来自与选择不重叠的验证帧），等价报告
  `f = (H_A − Y)/H(A|B)`；多 seed 配对，报 SE 与下界。
- 零失败 `N_req` 认证保留为历史结论（`f_eff ≤ 1.3` 单点认证句仍禁止），**不再作为任何实验的门**。
- 此条改变 G0 口径，**已于 2026-10-04 获用户批准**（见 §4 D-1），即日生效。

### R4 KILL / 否定结论必须先过「理论 + 邻仓」两道检查（针对 E4）
- **MUST**：判 KILL 前写明 (a) 该结论是否违背已知理论界（链式法则、Slepian–Wolf、有限长近似），
  (b) 隔壁 `../HD-QKD_Polar_Release`（只读）或文献是否已有反例，(c) 被排除的是「这个设计」还是「这条路线」。
- **MUST NOT**：用无条件逐面熵、或任何已知次优结构的失败，去关闭一条路线。

### R5 数字只许由脚本算出，并独立复算（针对 E5）
- **MUST**：任何进入结论的数字由仓内脚本生成，并由第二个独立脚本或独立 reviewer 复算一致；
  手算 / 「约等于」不得进入结论句。
- **MUST**：口径公式里必须显式出现泄漏项、tag、失败惩罚；单位（bit/KiB/B/s）写在变量名或表头里。
- **MUST NOT**：引用仓内无测量来源的数字（「2–4x」「366 sym/s」等）而不标「推导/无来源」。
- **MUST**：更新 NOW.md 或任何快照后，用 `git diff` 实测确认改动已写入再声称「已更新」。

### R6 流程预算（针对 E6）
- 一条路线 = **一个** OpenSpec change + **一个** append-only 日志；不得一探针一 change。
- 一个实验的新增代码以算法为主：**禁止**每个探针复制一份千行账本样板；共用 runner/记账模块写一次、复用。
- 每批收尾 **MUST** 给出：结论（一句）+ 推荐的下一步 + 其预期收益 + 成本估计。
  「等用户裁决」只用于真正属于用户的决定（授权、口径、发布），不得用于推卸科学判断。
- 文档与代码比例：一周内 docs 类提交数不得超过算法代码类提交数。

### R7 先计时，逐块落盘（针对 E7）
- **MUST**：任何预计 > 10 min 的运行，先做 ≤ 2 min 的计时 smoke，用实测每块成本 × 块数 × 1.5 定预算。
- **MUST**：逐块（或逐段）写盘，撞墙时已完成部分可用。
- 数值逐位一致的加速（numba/C/C++ 移植、批量化）**属于纠错研究的使能工作**，与用户 10-03 指示一致，
  可以做；**不得**做改变数值/选择行为的「加速」（剪枝、first-valid 等）而不另立假设。

### R8 仓库卫生（针对 E8）
- **MUST**：每个里程碑按 scoped 清单提交到命名 `formal-ir-*` 分支；**禁** `git add -A`；
  push 只做普通非强制 push，且需用户确认。
- **MUST**：输出路径用 `pathlib` 拼接；跑完检查仓库根没有新增杂项目录。
- 不得 merge `polar-mainline`；隔壁仓库只读参考，代码思路可借鉴、不可整目录搬运进主线而不标出处。

### R9 措辞（针对 E9）
- 结论句只写测到的东西 + 适用范围；不写「无用」「不可能」「独立」这类全称句，除非有对应的界。

---

## 3. 隔壁 Polar 仓库的可借鉴做法（只读参考）

来源：`../HD-QKD_Polar_Release/low_dim_opt/README.md`、
`low_dim_opt/outputs/final_summary/FINAL_SUMMARY.md`、`final_table.csv`、
`docs/POLAR_VS_LDPC_CROSS_REPO_COMPARISON_20260927.md`（本仓）。

### 3.1 他们的结果（换算为 f，推导）
由 `final_table.csv` 的 `h_a_bits`、`i_ab`、`y_exp_O1b2_3seed_mean` 算 `f = (H_A − Y)/(H_A − I_AB)`：
O1b-2 十点均值 f ≈ 1.49；再按 O4-R 均值增益 +0.158 bit/对统一叠加（近似）≈ 1.35，
bw50 各点约 1.24–1.35。数据集不同（偏振纠缠 curve，d=32–512；我们 d=1024、SER≈0.24），
**不可直接横比**；测试端为已用数据上的再检验。

### 3.2 方法要点
1. **MSD 多层编码**：逐比特面二元码，第 k 面用 P(b_k | y, 已译 b_<k) 的条件 LLR 表
   （由经验联合直方图构建，`diff_pmf` 平滑 α=1）。
2. **长码**：每面 N = 16384（我们超帧 1024 符号，10 月探针只有 128）。
3. **码率阶梯**：样本外 FER 曲线 + 按期望良率联合选 (序, k)（O1b-2，+0.093 bit/对）。
4. **增量披露**：失败时补发校验位重译（O4-R，+0.158 bit/对，单项最大）。
5. **评价**：期望良率主度量；3 seed × 10 点 = 30 对配对；事先算 MDE（W1）。
6. **快译码器**：C++ SCL L=8（`low_dim_opt/core/scl_cpp/`）。
7. **流程**：每步一个预登记包、一个采纳/不采纳判定，阶段三天收口并出 FINAL_SUMMARY。

---

## 4. 下一阶段计划

### 用户裁决（2026-10-04，用户原话「第一点换成带期望良率的f第二点确实可以停下第三点可以这么做第四点让在S1里面一起提交」）
- **D-1 已裁决**：主度量换为**带期望良率的 f**，即 `f = (H_A − Y)/H(A|B)`，
  `Y = kept − tag − kept·Σp̂`（p̂ 来自样本外验证帧），多 seed 配对报 SE/下界。R3 即日生效；
  零失败 `N_req` 认证不再作为任何实验的门（`f_eff ≤ 1.3` 单点认证句仍禁止）。
- **D-2 已裁决**：**正式停止** GF32 128 符号单旋钮探针线。已有结果按 §5 S4 归入 `_closed/` 并写 SUMMARY。
- **S6 处置已批准**：新增「executed-exploration-closed：归档、写 archive.md、不合并 delta」处置的做法获准；
  执行 session 起草该 OpenSpec 修订 change 后即可按此批量归档（处置表需随提交附上）。
- **本文与配套 prompt** 不单独提交，在 §5 S1 中一并提交。

### 仍待用户决定（agent 不得自行决定）
- **D-3** 真实帧 DECIDE 运行的授权与墙钟预算（P2 起需要）。
- **D-4** 任何 push。

### P0 仓库整理与归档（立即，无科学执行）
完整方案见 §5。P0 完成前不开新的科学实验。

### P1 条件熵重算 Stage 0（EXPLORE，零译码，分钟级）
- 用 CHAN-QUALITY-SURVEY 已有的联合直方图（`docs/research_cycles/CHAN-QUALITY-SURVEY/`、对应 `workspace/cq_*` 根），
  按 MSD 顺序（LSB→MSB 与 MSB→LSB 两种）计算 Σ_k H(b_k | B, b_<k)，以及按有限长近似
  （正态近似 / 已知二元 LDPC/Polar 在 N=1024、16384 下的码差距）估计的 Σ m_k，对照 1104 预算。
- 输出：一张表 + 一句结论（MSD 下逐面二元路线是否进入预算内、余量多少）。
- 若不进入预算：记录理由，转 P3 的 NB-LDPC 线；若进入：做 P2。

### P2 MSD 多层二元码原型（EXPLORE→DECIDE）
- 在**由真实联合直方图标定**的合成信道上实现 MSD + 二元 LDPC（或借鉴隔壁 Polar SCL），
  块长至少比较 N=1024 与 N=16384；度量用期望良率 + 样本外 FER；先算 MDE 再定帧数。
- 再上真实帧（DECIDE，完整 Pre-EXECUTE/授权/Pre-RESULT）。

### P3 并行：NB-LDPC 主线的使能工作
- 数值逐位一致的译码核加速（numba/C），以 bit-identical 测试守门（R7）。
- soft-prior rescue 作为候选机制，仅在真实标定信道 + 1024 符号超帧上做一次功效足够的配对对照。
- 增量披露（已有 `NBLDPC-GF32-INCREMENTAL-SYNDROME-20261004` 草案）改为在主线块长、期望良率口径下重写。

### P4 同数据对照列
- 用冻结 Polar 基线（或隔壁 production 配置，只读调用、不改其代码）在**同一批采集**上补一列，
  否则 G0=(B) 的同数据比较依旧为空。属 DECIDE。

---

## 5. 仓库整理与归档方案（P0 的执行规格）

### 5.1 现状（2026-10-04 实测，执行前须重测）
- **仓库根**：tracked 的 V65–V72P0 报告 10 个、`v6x/v7x_*.json|csv` 约 45 个、`test_v6x–v72*_small.py` 8 个、
  `总体判断.txt`、`dsh-opencode-go-pro.patch.yml`、`HANDOFF.md`/`AGENT_HANDOFF.md`/`CURRENT_TASK.md`/
  `REVIEW_CHECKLIST.md`/`RUN_COMMANDS.md`；tracked 目录 `tmp_v27r/`(10)、`tmp_v28r/`(2)、`v72p1_synthetic_qual/`(4)。
- **仓库根未跟踪杂项**：`tmp*/` 10 个、`v39_review_tmp_20260825/`、`.pytest_l1d2_wall_*`、`.pytest_tmp_v33_*`、
  `.pytest-v3-coder/`，以及**路径拼接 bug 产物** `CodeHD-QKD_Polar_Comparisonworkspacev30r_testsregression/`、
  `workspacegf32_full_eff_tests_20261002_e5/`、`..._full/`。
- **docs/** 顶层 104 个 md；`docs/research_cycles/` 140 个目录（其中约 39 个 GF32 微探针）；
  `docs/decision-log.md` 5,627 行；`AGENT_PROJECT_MEMORY.md` 4,717 行。
- **openspec/changes/** 约 170 个未归档 change（`formal-*` 78、`explore-*` 36、`v72p2d*` 等）。
- **cli/** 167 个脚本；**tests/** 305 个文件；`workspace/` 2,475 个根、18 GB（gitignored）；
  `comparison_bench/outputs_comparison/` 532 MB。
- 约 165 个 tracked 文件仅有 CRLF/LF 差异。

### 5.2 不可违反的整理规则
- **只用 `git mv`**（保留历史）；**不删除任何 tracked 文件**；未跟踪杂项先移入隔离区，删除须用户逐项同意。
- **不碰冻结基线**：`src/`、`experiments/`、`tools/`、`results/`（AGENTS.md §5.1/§5.2）；不改 `outputs_comparison/` 内容。
- **不改历史文档正文**（decision-log、周期 RESULT 等是 append-only 证据）；路径变化一律记入
  `docs/archive/PATH_MAP.md`（旧路径 → 新路径），而不是批量改写旧文档里的引用。
- **每一步单独提交**，提交前 `git status` 核对清单；代码移动后必须跑 smoke 测试
  （`.venv` 解释器，`pytest -p no:cacheprovider`，写到新 `workspace/<task>/<uuid>`）。
- 不 merge 姊妹线；push 需用户确认。

### 5.3 步骤（按序，每步一个提交）
**S1 先保全再整理**：按 scoped 清单提交 9-27 之后未提交的工作（GF32 脚本/测试/周期目录、4 个 OpenSpec change、
NOW/decision-log/troubleshooting/memory 改动、`v35_algorithm_development.py` 的 4 行改动需先读懂再决定），
**连同本文 `docs/REBOOT_HANDOFF_20261004.md` 与 `docs/prompts/REBOOT_HANDOFF_20261004_PROMPT.md`**；
并在 decision-log 追加一条记录 §4 的用户裁决 D-1/D-2/S6。
不提交 `workspace/`、pytest 临时目录。

**S2 换行归一**：新增 `.gitattributes`（`* text=auto`，`*.py/*.md/*.json/*.csv eol=lf` 或按仓库现状选定一种），
`git add --renormalize .` 单独成一个「只改换行」提交，提交说明里写明无内容变化，并用
`git diff --ignore-all-space --stat HEAD~1` 证明。

**S3 仓库根清空到最小集**：根目录只保留 `AGENTS.md`、`README.md`、`AGENT_PROJECT_MEMORY.md`、`LICENSE`、
`requirements.txt`、`pytest.ini`、`wsl-env.sh`、`.gitignore`、`.gitattributes` 以及代码顶层目录。
- V65–V72P0 报告 + 对应 json/csv → `archive/v65_v72p0/`（按版本分子目录）；
- `test_v6x–v72*_small.py` → `archive/v65_v72p0/tests/`，并在 `pytest.ini` 中排除 `archive/`
  （先确认这些测试当前是否被 CI/主测试集引用）；
- `tmp_v27r/`、`tmp_v28r/`、`v72p1_synthetic_qual/` → `archive/legacy_tmp/`；
- `HANDOFF.md`、`AGENT_HANDOFF.md`、`CURRENT_TASK.md` → `docs/archive/handoffs/`（被本文取代）；
  `REVIEW_CHECKLIST.md`、`RUN_COMMANDS.md` → `docs/`（若内容仍有效）否则归档；
- `总体判断.txt`、`dsh-opencode-go-pro.patch.yml` → `archive/misc/`；
- 未跟踪杂项（tmp*、路径 bug 目录、旧 pytest 临时目录）→ `workspace/_quarantine_20261004/`，
  列清单给用户决定是否删除；并修复产生 `workspace` 无分隔符路径的那段代码（grep `workspacegf32`、`v30r_tests`）。

**S4 docs 分层**：
- `docs/` 顶层只留现行权威：`NOW.md`、`REBOOT_HANDOFF_20261004.md`（本文）、`ROADMAP-20260921.md`、
  `V80_BASELINE_20260921.md`、`EXECUTION_PLAN_20260922.md`、`decision-log.md`、`troubleshooting.md`、
  `research-cycle-sop.md`、新建 `INDEX.md`；其余按时代移入 `docs/archive/<era>/`
  （如 `v19_v72/`、`v80/`、`routes/`、`reports_202609/`）。
- `docs/research_cycles/` 按状态分两层：进行中的留在原处；已关闭的移入 `docs/research_cycles/_closed/<line>/`，
  line 例：`nbldpc_gf32_microprobes_20260930_1004/`、`m0_m3d/`、`v80_nbldpc_jan21/`、`chan_quality_btrack_ctrack/`、
  `joint_pricing_stage0_u1_proxy/`。**每个 line 写一页 `SUMMARY.md`**：一张表（周期、假设、样本量、结果、判定词、
  机器根路径）+ 三行结论 + 仍可复用的东西。GF32 微探针 line 的 SUMMARY 可直接以 §1 E1/E2 为结论。
- `docs/archive/WORKSPACE_INDEX.md`：周期 → `workspace/` 机器根映射（workspace 本身 gitignored，不移动、不删除；
  18 GB 的清理由用户另行决定）。

**S5 两本大账封存重开**：
- `docs/decision-log.md` 整本 `git mv` 为 `docs/archive/decision-log-to-20261004.md`；新建 `docs/decision-log.md`，
  首段为**现行有效决定摘要（≤ 200 行）**：每条一行，带指向旧账行号的指针；此后正常 append。
- `AGENT_PROJECT_MEMORY.md` 同法：旧版移入 `docs/archive/`，新版压缩到只含仍然有效的结构/口径/数据策略/禁令
  （AGENTS.md §2 要求它是耐久记忆；压缩须经 memory triage，不得丢失 §6 schema 约定）。

**S6 OpenSpec 归档**：
- 对约 170 个未归档 change 做一张处置表：已实现+已执行+已评审 → 按 AGENTS.md §6 处置 (1) 归档；
  冻结但从未执行 → 处置 (2) superseded-before-execution。
- 已执行的 EXPLORE 探针 change（如 GF32 系列）若按处置 (1) 会把探针级 SHALL 合并进 `openspec/specs/`、污染现行规格。
  **先起一个 OpenSpec 修订 change**，增设「executed-exploration-closed：归档、写 archive.md、不合并 delta」处置
  （做法已获用户批准，见 §4），该 change 落地后再按处置表批量归档。
- 归档后 `openspec/changes/` 只留现行路线的 change。

**S7 代码整理（最后做、可延后）**：
- 把 31 个 `nbldpc_gf32_*.py` 与其他已关闭探针脚本移入 `comparison_bench/src/comparison_bench/cli/probes_closed/`
  （或 `research/archive/`），对应测试同步移动；`python -m` 路径变化记入 PATH_MAP。
- 抽出一个共用的探针 runner（记账/manifest/资源/落盘），后续实验只写算法差异（§2 R6）。
- 每次移动后跑 smoke；任何测试失败即停，修复后再继续。

**S8 收尾**：`docs/INDEX.md` 写清「从哪里开始读」；NOW.md 重写为一屏（≤ 80 行），只指向现行权威；
提交；向用户报告提交清单，并请其确认 push。

---

## 6. 接手 checklist（每个新 session 开工第一件事）
1. 读 AGENTS.md、本文、`docs/NOW.md`；现场重测分支 / HEAD / 脏树（不要引用任何文档里的快照数字）。
2. 确认本次任务落在 §4 / §5 哪一步；不在其中的任务先问用户。
3. 写包前过一遍 §2 R1–R9，在包首逐条写「本包如何满足」。
4. 收尾时按 R6 给出推荐下一步 + 预期收益 + 成本，并按 R8 提交（push 需用户确认）。
