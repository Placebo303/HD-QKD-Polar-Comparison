# TIMING 耗时实测 Packet（2026-09-24）— DRAFT, FROZEN-PENDING, NOT GRANTED

## §0 身份与关系

- 任务 IDs（拟）：**TIMING-1**（本文件 = prereg + 冻结科学输入 + 授权边界）/ **TIMING-2**（配套执行面 `TIMING_PROBE_PROMPT.md`）/ **TIMING-3**（本任务创建范围声明）。
- Acceptance ID（拟）：**G-TIMINGPROBE**；子项 **E1–E8**（§8）。
- Track：本冻结任务 = docs-only/planner，**无 track gate**（AGENTS §1.2 矩阵"Documentation-only"）；**首次合成执行 = EXPLORE**（五条资格见 §7，无 `EXPLORE_HEAVY`）。
- 分支/基线：`formal-ir-v72p1-addendum-clean` / 冻结时点 **`8e9c8526`**（不切分支、不 commit、不 push；实际 HEAD 在 Pre-EXECUTE 重测记录）。
- 上游：`P4_FEAS_PACKET.md` §5 L70–71（600 s 单调用帽 / 1800 s 臂帽 / 3600 s 批次 ceiling 目前是**提议+估**，本包为其提供实测依据）；`docs/EXECUTION_PLAN_20260922.md` §3 S0.2 语境（只引用）。
- 配套 prompt：`TIMING_PROBE_PROMPT.md`（两文件制）。append-only 日志（执行时新建）：`docs/research_cycles/V80-NBLDPC-JAN21/TIMING_EXPLORATION_LOG.md`；批次末独立评审：`TIMING_BATCH_END_REVIEW.md`。本包不新建其他执行文件。

## §1 目的与假设（测，不宣称）

1. **目的**：在**合成矩阵 only**上实测三段墙钟耗时，为 P4 §5 三帽定值提供依据：
   - (R) **GF(32) RREF**：`rank_GF1024` 对 **m=400 与 m=416 行**、n∈{1024, 2048} 的随机稠密矩阵（nested leading-400 与全矩阵 416 的行形态对应物）；
   - (P) **PEG 主循环**：`peg_construct` 小规模稀疏族 (n,m)∈{(512,104),(1024,208)}，同 λ/ρ/trials 形状（`λ={2:1}`, `ρ=make_rho(1−m/n)`, `trials=20`）；
   - (G) **BFS girth 计算**：在 (P) 产出图上单独计时 girth/BFS 段。
   外推规则（冻结）：n=2048 全尺度 PEG 单调用耗时 = 实测 (P) 常数 × edge 数线性缩放（2048×2=4096 edges 对 1024×2=2048 edges），**report-only 外推，非预测非承诺**；(R) 在 n=2048 上**直接实测**不经外推。
2. **假设（待测，非主张）**：三段耗时在本机为便宜量级、远低于 600/1800 帽——**本包不预设任何 wall 数字**（P4-3 同构禁令）。
3. **零译码**：`decode_calls=0` REQUIRED 全程；无 FER/效率/SKR/泄漏任何口径（§9）。

## §2 冻结科学输入（改动任一项 ⇒ STOP 回主线程）

| # | 项 | 冻结值 |
|---|---|---|
| F1 | 臂数与 case 表 | **T1 稠密-RREF**：`m∈{400,416} × n∈{1024,2048}` = 4 case × **repeats=3** = 12 次 `rank_GF1024` 调用（矩阵 = seed 专属 RNG 的 **i.i.d. 均匀** GF(32) 随机稠密，纯内存）。**满秩机制**：满秩由 i.i.d. 随机生成自然达成、不做满秩修补或拒绝重生成，实测 `rank` 逐 case 记录为证（`rank_recorded_not_gated` + `rank_eq_m` 入诊断列，**只记录不作门**）。**T2 稀疏-PEG**：`(n,m)∈{(512,104),(1024,208)}` × seeds×2 = **4 次 `peg_construct`**，每次内部分段计时 `peg_main` 与 `bfs_girth`。**恰此两臂，冻结顺序 T1→T2，禁加 case/加 repeats/加尺度。** |
| F2 | 种子 | 专用 timing 种子（**非** P4 谱系）：T1 矩阵种子 `2026092401..2026092412`（按 case×repeat 顺序逐一分配）；T2 PEG 种子 `2026092421, 2026092422`（每尺度各两次）。**禁用 `2026092001`/`2026092011`**（保 P4 F3 `rg` 独占门）；执行者不得自行发明种子 ⇒ 冲突即 STOP。 |
| F3 | 构造形状 | T2 = `peg_construct(n, m, λ={2:1} edge-perspective, ρ=make_rho(1−m/n), seed, trials=20, field=GF(32))` 逐字（`nonbinary_v26_mcde.make_rho` 只读复用，P4 F2 先例）；family 戳记记录、**不设 three-shift-cyclic 门**（本包只计时不验 pins——P4 pins 属 P4 自身）。T1 = 随机稠密生成器（runner 内 ≤30 行，`numpy` + GF(32) 表，§5.7 最小实现）。 |
| F4 | 信道/数据 | **无**：零 `.ttbin`、零 `gamma_f03*.npz`、零 bundle/refit；任何读取 = STOP-BLOCKED。 |
| F5 | 解码器/先验 | **无**：`decode_calls=0` REQUIRED；任一解码/DE/图核生产调用 = STOP-BLOCKED。 |
| F6 | 计时口径 | 每 case 每 phase 单独 `time.perf_counter()` 段计时；`wall_s`（段）+ `wall_s_total`（case）+ `rss_peak`（`resource.getrusage` 峰值）逐 case 记录；1 CPU、无并行、无 warm-up 段（repeats 即自然 warm 序列，3 次全记，**禁只报最快**）。 |
| F7 | 定值产出（report-only） | 三行拟议（**输出为"依据"，不是自动生效的帽**）：`cap_single_call = max(实测单调用 wall) × 安全系数 k`（k 冻结 = **4**，与 P4 L71"4× 宽松帽"同源）；`cap_arm ≈ Σ(1×T1 全 case + 2×T2) × k`；`batch_ceiling = 2 × cap_arm`。三值以实测代入、四舍五入到整百秒，**由主线程在 P4 §5 另行裁决采纳**（本包无权改 P4 冻结件）。 |
| F8 | 停止/失败类别 | 单调用超 **600 s** = `INCOMPLETE-call` 记录、**不续跑不重试**（该超时本身即是"帽太小"的有效实测证据）。**双保险 = 内层检测 + 批次级 timeout，无 per-call 抢占**：600 s 由 **runner 内层 deadline 检测**（超限落 `INCOMPLETE-call` 并停续跑，非 CLI 旗标），外层唯一兜底是 §6 cmd1 的**批次级** `timeout -k 10 1810`；**不为单 case 另起外部 `timeout` 进程、无 per-call 抢占式杀进程**；批次 wall 超 ceiling = `INCOMPLETE-batch` 保留、永不续跑；异常 = 该 case 记 `error` 保留原始 traceback。**至多 1 次预注册工程修复**（仅基础设施失败；科学输入/seeds/阈值全不变；失败尝试同日志保留；未用则写 `no repair path used` 行；第二次失败 ⇒ STOP-BLOCKED，AGENTS §1.2）。 |

## §3 产出字段（冻结计算规则）

逐 case 行（`timing_records.jsonl`，append-only）以 **`case_id`** 唯一标识，**核心列（冻结词汇）**：

- **`segments` = `{phase: wall_s}` 映射**：每 phase 一段 `time.perf_counter()` 墙钟；phase∈{`rref`,`peg_main`,`bfs_girth`}，键字面 = T1 `{rref_s}` / T2 `{peg_main_s, bfs_girth_s}`（**无顶层 `wall_s` 列**，段值只在 `segments` 映射内）；
- **case 级词汇**：`case_id`、`arm∈{T1,T2}`、`n`、`m`、`repeat`、`seed`、`trials`、`edges`（T1 = `m×n` 稠密格数；T2 = 图边数，F7 线性外推输入）、`wall_s_total`（= Σ `segments`，case 总墙钟）、`rss_peak`、`decode_calls(=0)`、`terminal∈{ok,INCOMPLETE-call,error}`、`claim_ceiling`；
- **附加诊断列许可**：核心列之外允许附加诊断列/诊断桶（实现侧 `deadline_s`、`batch_ceiling_s`、`info` 等），附加列不改变核心列语义、不豁免下方禁列。

汇总 `timing_summary.md`：按 phase×尺度分列（**禁跨 case 合并/取最快冒充代表值**）、F7 三行拟议代入值 + 外推式明写"report-only"。
**禁**：FER/f_eff/泄漏/SKR 列；跨机器泛化句；把 `ok` 之外状态改写为成功；点预测倒填。

## §4 停止门（二元、零译码可判定）

- **G-A 范围**：任一真实数据读取、任一 `decode_calls≠0`、任一禁写路径写入 ⇒ STOP-BLOCKED。
- **G-B 预算**：单 case 超 600 s ⇒ `INCOMPLETE-call`（记录即证据，不算失败）；批次超 ceiling ⇒ `INCOMPLETE-batch`，全部已写行保留、禁聚合覆盖、禁 rerun/resume/adaptive。
- **G-C 秩序**：T1 全部 12 case 完成（或终态）前禁进 T2；一次授权覆盖冻结臂序（无逐臂授权）。
- **G-D 变更**：任何 F1–F8 改动（含加尺度、加 repeats、改 k、改种子）⇒ STOP 回主线程；实现若需改冻结模块行为才能跑通 ⇒ STOP（先 OpenSpec，AGENTS §3）。

## §5 预算 / 允许 / 禁止文件

- **预算（本包自身，冻结提议、授权块定值）**：**单调用帽 600 s**（= 被测帽之一，超即 `INCOMPLETE-call`）；**批次总 ceiling ≤ 1800 s**（提案；执行时在授权块填定值——注意本包 ceiling 应 ≤ 被测的 3600 s，避免测帽包比帽还贵）；**RSS < 2 GiB**；**1 CPU**；unspent budget ≠ authorization。
- **允许文件（白名单，exhaustive）**：
  1. 新增 `comparison_bench/src/comparison_bench/cli/timing_probe_runner.py`（或复用 `p4_feas_construct.py` 的 fake/计时通路——**二选一，Pre-EXECUTE 冻结所选路径**；若复用则该文件仅以现有 flag 只读调用，**禁改其一字节**）；
  2. 新增 `comparison_bench/tests/test_timing_probe_fake.py`（fake-only、tiny 输入、`pytest -p no:cacheprovider`、测试根 = pytest **`tmp_path`**——零仓库写入，不占用 `workspace/TIMING/` 输出根、不新建 `_pytest_` 目录）；
  3. 输出根 **`workspace/TIMING/<uuid8>/`**（fresh additive；`timing_records.jsonl`、`timing_summary.md`）；
  4. `docs/research_cycles/V80-NBLDPC-JAN21/` 下四件：`TIMING_PROBE_PACKET.md`（本文件落档）、`TIMING_PROBE_PROMPT.md`、`TIMING_EXPLORATION_LOG.md`（append-only）、`TIMING_BATCH_END_REVIEW.md`（执行后）。
  5. 只读 import：`nonbinary_v10_peg`（`rank_GF1024`/`peg_construct`/`_bfs_distance`）、`nonbinary_v26_mcde.make_rho`——**行为零改动**。
- **禁止文件（exhaustive）**：`results/`、`comparison_bench/outputs_comparison/`（禁写，§5.2）；`src/`、`experiments/`、`tools/`（冻结基线，`git diff -- src/` MUST EMPTY）；**P1 族**（`P1_PACKET.md`、`P1_STAGE1_*`、`workspace/P1_STAGE1/`）、**S0.1 族**（`S0_1_*`、`workspace/S0_1/`）；P4 族写操作（`P4_FEAS_PACKET.md`/`P4_FEAS_PROMPT.md`/`workspace/P4_FEAS/` 只读不碰，本包**无权**改其 §5）；真实 **`.ttbin` / `gamma_f03*.npz`**；`AGENTS.md`、`docs/decision-log.md`、`docs/troubleshooting.md`、`docs/NOW.md`、`docs/EXECUTION_PLAN_20260922.md`；`tools/longrun_*`/`minrerun_*`/`routeA_*`、`experiments/run_e2e_pipeline.py`；**禁 commit / push**。

## §6 命令模板（占位符执行时冻结）

```
# 0) 聚焦 fake-only 测试（Pre-EXECUTE Q4；已验证 pytest 命令，磁盘根 = pytest tmp_path，无 --root）
.venv/bin/pytest -p no:cacheprovider -q comparison_bench/tests/test_timing_probe_fake.py

# 1) 唯一一次授权执行（一次授权覆盖 T1→T2 冻结臂序）
timeout -k 10 1810 .venv/bin/python -m comparison_bench.src.comparison_bench.cli.timing_probe_runner \
  --root workspace/TIMING/<uuid8> --uuid8 <uuid8> --execution-authorized --execute-real \
  --batch-cap-s <BATCH_CEILING> --rss-gib 2   # 单调用 600 s = runner 内层 deadline 检测（F8，非 CLI 旗标）；1810 = 批次级 timeout 双保险
```

## §7 EXPLORE 资格与合约（AGENTS §1.2 + §10.3 + §5.7）

- 五条资格：① 输入 = 合成 RNG 矩阵/图，非敏感、零真实数据；② fresh additive `workspace/TIMING/<uuid8>`，有界可逆（16 次计时调用、ceiling ≤1800 s）；③ 无 FER/SKR/资格/晋升/发表主张（§9）；④ 无破坏性覆盖、无新对外动作；⑤ 零译码 ⇒ 非 DECIDE（任一解码/DE 调用即须先升 DECIDE）。
- 合约（两文件制）：一个 packet+prompt 对 + 一个 append-only log + 一个 batch-end 独立评审；一次授权覆盖冻结臂序；至多一次预注册 repair+rerun；repeats=3 + 双 seeds 满足"变异性可能混淆时 multi-seed 默认"。
- §5.7 最小实现：runner ≤ ~200 行、stdlib+numpy、无校验和/锁/重试框架/schema 层；每个防御机制先答"防的具体失败模式"，无则省略。
- 升级：真实数据、解码/DE 调用、关路阈值、发表主张、破坏性输出、成本显著上升 ⇒ 先升 DECIDE。

## §8 验收 ID（冻结；执行后由 batch-end 评审核对，本任务不 acceptance）

| ID | 验收项 |
|---|---|
| **E1** | 白名单外零改动：`git status` 符合 §5 允许清单；`git diff -- src/` EMPTY；禁写路径零新增（含 `results/`、`outputs_comparison/`、P1/S0.1/P4 族）。 |
| **E2** | fake-only focused 测试 PASS 并附完整输出（Q4）。 |
| **E3** | 恰好 16 case（12 rref + 4 peg）按冻结顺序产出，**无加项**；每行 `decode_calls=0`、`terminal` 三态之一，禁改写。 |
| **E4** | 实际使用种子逐字 = F2；**禁用种子在产出零使用**：`2026092001`/`2026092011` 在 `timing_records.jsonl`、`timing_summary.md`、`TIMING_EXPLORATION_LOG.md` 零命中；**源字面仅限** `FORBIDDEN_SEEDS` 常量声明或拒绝（refusal）上下文——本包 runner/测试源码中该两字面在其他位置零命中（拒绝逻辑引用常量、不写字面）；核对 pattern 精确 = `rg '2026092001\|2026092011'`（两字面交替，非 `202609200[11]` 字符类写法）（P4 F3 独占门未污染）。 |
| **E5** | 预算合规：单 case ≤600 s 或 `INCOMPLETE-call` 记录；批次 ≤ ceiling；RSS < 2 GiB 有记录；无 rerun/resume。 |
| **E6** | `timing_records.jsonl`/`timing_summary.md` 字段 **⊇ §3 核心列**（允许附加诊断列）且**零 §3 禁列**（FER/f_eff/泄漏/SKR 列）；F7 三行含实测代入 + k=4 + 外推式 "report-only" 标记；无最快值挑选。 |
| **E7** | append-only 日志条目 0（Pre-EXECUTE Q0–Q6）→ 逐 case 条目 → 收口 tally + `no repair path used`/修复记录，齐全且未覆盖。 |
| **E8** | claim ceiling 遵守（§9 全句禁令零违反），batch-end 独立评审 PASS。 |

## §9 Claim ceiling

- **仅**：本机、本 Python 实现、本合成 case 表上的 **wall_s / rss_peak 实测数字** + k=4 换算的**三帽拟议值** + 尺度外推式（明标 report-only）——供主线程为 P4 §5 定值。
- **非（全句禁）**：任何 FER、f_eff/效率、泄漏、SKR、可认证性主张；"P4 构造可行"（那是 P4 包自己的门）；跨机器/跨实现泛化；"600/1800/3600 已被证明安全"（帽是工程预算，不是安全证明）；把本包数字当 P4 pins、当发表材料、当路线裁决。

## §10 与 P4 双臂的关系（显式边界）

- 本包**不开 P4 双臂**、不构造 P4 的 n=2048 PEG 实例、不消耗 P4 谱系种子、不碰 `workspace/P4_FEAS/`。
- **本包 PASS 仅表示"三帽可定值"**（有实测依据可填 P4 §5 L70–71 的"估"）：主线程据 F7 另行裁决是否/如何更新 P4 §5，那是 P4 冻结件的显式修订动作，**不在本包授权内**。
- **本包不构成、不部分构成、不预授权 P4 执行**：P4 的 Pre-EXECUTE Q0–Q6、授权块、1800 s 臂帽与门 (a)(b)(c) 判读全部原样保留，仍需其自身 FRESH EXPLICIT USER GRANT。反向同理：P4 未授权不阻塞本包（本包无依赖，`docs/EXECUTION_PLAN` S0.2 语境只读引用）。

## §11 Pre-EXECUTE 待填槽（执行时填，未填 = 未授权）

- **Q0** 目标分支 `formal-ir-v72p1-addendum-clean`，Pre-EXECUTE 实测 HEAD：`________`（8e9c8526 仅冻结时点）。
- **Q1** 范围清洁：仅 §5 白名单文件 additive；脏树按显式文件清单界定（现知外源脏项 `AGENT_PROJECT_MEMORY.md`、`docs/NOW.md`、P4/openspec 未跟踪件**不纳入本包**）：`________`。
- **Q2** F1–F8 逐项核对：`________`。
- **Q3** 输出缺席证明：`test ! -e workspace/TIMING/` 输出 + 种子字面 `rg` 仅命中本包族：`________`；**根 UUID8 冻结**：`workspace/TIMING/________`。
- **Q4** focused fake-only 测试 PASS 输出：`________`。
- **Q5** Grant 前零生产调用：零 `peg_construct`/`rank_GF1024` 生产执行、零解码、零真实数据读取：`________`。
- **Q6** 预算定值：单 case ≤600 s ✓；**批次 ceiling = ________ s**（提案 ≤1800）✓；RSS < 2 GiB ✓；1 CPU ✓：`________`。

### §11 授权块（空白待签；未填 = 未授权；全包唯一填充处）

- Acceptance ID `G-TIMINGPROBE`；grant verbatim：________；根 UUID8：`workspace/TIMING/________`（Pre-EXECUTE 冻结 + 缺席已确认）：________；预算确认（单 case 600 s ✓；批次 ceiling ＝ ________ ✓；RSS < 2 GiB ✓；1 CPU ✓；零 `.ttbin`/零 gamma/零解码/零 `results/` 与 `outputs_comparison/` 写入 ✓）：________；日期 / 主线程：________；签名：________。
