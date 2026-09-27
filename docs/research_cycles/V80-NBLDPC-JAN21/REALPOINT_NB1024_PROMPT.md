# REALPOINT NB1024 真实单点 — 执行提示面（REALPOINT_NB1024_PROMPT）— FROZEN DRAFT, NOT GRANTED, NOT AUTHORIZED, NOT EXECUTED

- 配套 prereg：`REALPOINT_NB1024_PACKET.md`（§0–§11 冻结草案；两文件制，AGENTS §1.2 矩阵）。
- Track（本 prompt 创建任务）：**documentation-only — 无 track gate**；Track（未来执行，恰其一）：
  **DECIDE**（真实数据 + 报告/认证语境）。本 prompt **不改变** PACKET 的任何冻结值；
  **本 prompt 自身不构成授权**，授权任何执行 = 0。
- 基线 provenance（非执行锁）：`8e9c8526` / `formal-ir-v72p1-addendum-clean`；
  实际分支/HEAD 由 Pre-EXECUTE Q0 实测记录（AGENTS §10.3：不做 SHA 相等断言）。
- 入口语境（冻结前提，不是授权，P3/P4 同形）：P1 Stage-1 P4-elevation 输入（R1 FAIL(a)/R2 FAIL(c)、
  N_req 402/575 > eligible）+ G0=B F3（P4 不自动升格）+ 用户顺序 ①→③→②；G0=B 主攻**同批可测收益**。
- **未授权不得执行。** §7 授权块全 BLANK = 未授权；任何解码/构造/真实数据访问须先走
  PACKET §10 授权门 + Pre-EXECUTE PASS + 显式用户授权。

---

## §0 白名单（本 prompt 允许面；白名单之外一律禁止）

1. **可读（只读引用，零写入）**：
   - `REALPOINT_NB1024_PACKET.md`（本包冻结契约 §0–§11）；
   - `G0B_REALPOINT_GATE.md`、`SAME_DATA_CMP_METRICS.md`（报告合同 A-CMPE-1..7）；
   - `P1_STAGE1_PACKET.md` / `P1_STAGE1_BATCH_END_REVIEW.md`、`S0_1_M200_PACKET.md` /
     `S0_1_BATCH_END_REVIEW.md`（构造/救援/锚语境）；
   - `P3_MEMORY_AUDIT_PACKET.md`（§4 门形式 + §7 空授权块 = P3 verdict 前提事实）、
     `P4_FEAS_PACKET.md`（F1/F2/F8 语境，只读不执行）；
   - `docs/ROADMAP-20260921.md`、`docs/V80_BASELINE_20260921.md`、`docs/EXECUTION_PLAN_20260922.md`、
     `docs/NOW.md`、`docs/decision-log.md`、`AGENTS.md`（只读）；
   - `S2_TIMING_PROBE_20260920.md`（timing 参考件，只读；其 smoke 结果无 FER 含义）；
   - `gamma_f03.npz` / `gamma_f03_pb.npz`（**只读、永不重拟合**；读取本身即真实数据/先验访问动作，
     仅在授权后按冻结输入清单进行，任一越界 = STOP-BLOCKED）。
2. **可写（仅授权后，且仅在 Pre-EXECUTE 冻结的目标根与日志内）**：
   - fresh additive 机器根 `[TO BE FROZEN AT PRE-EXECUTE]`（UUID 冻结 + 缺席证明）；
   - 本包 append-only 日志 `docs/research_cycles/V80-NBLDPC-JAN21/REALPOINT_NB1024_EXPLORATION_LOG.md`
     （执行时新建，append-only；条目 0 = Pre-EXECUTE 记录）；
   - 本包结果记录 `RESULT`（或等价单一 append-only 记录的结果节）与机器伪影（授权时冻结命名）。
3. **可执行**：仅 Pre-EXECUTE 冻结的确切命令（uuid 占位，授权时一次性实例化；
   `PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python …`，解释器只用 `.venv/`）。
4. **本 prompt 创建任务的可写面**：仅本文件与 `REALPOINT_NB1024_PACKET.md` 两份 docs。
5. 白名单**不可由执行者自行扩展**：新增可读/可写/可执行项 = 包修订（re-freeze，PACKET §9），
   不得静默扩面。

## §1 禁令（全文有效；任一违反 = STOP-BLOCKED）

1. **禁碰文件（一个字节不改）**：`G0B_REALPOINT_GATE.md`、`SAME_DATA_CMP_METRICS.md`、
   **P3 族**（`P3_MEMORY_AUDIT_*` / `P3_CENSUS_*` / `P3_STAGE05_*` / `P3_A1_REVIEW.md`）、
   **P4 族**（`P4_FEAS_*`）、**TIMING 件**（`S2_TIMING_PROBE_20260920.md`）、`docs/NOW.md`、
   `docs/decision-log.md`、`AGENTS.md`、`docs/troubleshooting.md`、`docs/ROADMAP-20260921.md`、
   `docs/EXECUTION_PLAN_20260922.md`、`docs/V80_BASELINE_20260921.md`、`AGENT_PROJECT_MEMORY.md`、
   **P1 族 / S0.1 族 / X1 族**文件与既有证据根、`src/`/`experiments/`/`tools/`
   （`git diff -- src/` 必须 EMPTY）。
2. **禁改冻结值**：PACKET §2 七元组（d=1024、q=32 分层 GF(32)×GF(32)、n_IR=1024 S-B、
   PEG 谱系 2026092001 girth8 + 2026092011 girth6 分列、嵌套基 `rows[0,200)`+`rows[200,208)` 硬顶 208、
   先验一次性只读 + 每源 1.50×、单段救援 bar report-only + `undetected` 单列 + `N_req` report-only vs
   200/276/364）、会计常数（852.544 / 1108.31 / 4.785675 / 1.248029 / 1.294947 / tag 64 b /
   4.3075 canonical）、门与阈值、claim ceiling —— **改任一 = 新包**（PACKET §9：**改长度/改模型 = 新包**），
   执行者不得自行改需求或补常数。
3. **禁执行面越界**：禁 `tools/longrun_*|minrerun_*|routeA_*`；禁 `experiments/run_e2e_pipeline.py`
   （原始数据）；禁 benchmark/smoke；禁 warm-start / non-nested / two-segment / multi-segment；
   禁跨源、跨构造实例、跨臂合并任何计数/FER（含 6+4 式求和）；禁单臂/单门 cherry-picking。
4. **禁口径违规**：禁 `undetected` 并入 success/FER 分子；禁把 `f_super`/`f_exp` 当 `f_eff` 报；
   禁用 500/691/911 冒充 key-eligible；禁 census raw-stream 计数与超帧口径混用；禁合成 FER 当真实 FER
   （P3 verdict 缺席期间强制，见 §3）；禁把 6.7 kbit/s 说成 SKR/IR 吞吐；禁把数据说成 BBM92 偏振层；
   禁引撤稿 Mao。
5. **禁状态静默转换**：`reference/stub/unavailable/decode_failed/no_verified_success` 不得转成 `ok`
   （AGENTS §5.5）；超时 = 终态不续跑；`INCOMPLETE-wall` 保留不续跑；无 retry/resume/adaptive。
6. **禁输出面**：禁写 `results/`、`comparison_bench/outputs_comparison/`、既有证据根；
   **禁 commit / push**；禁 `git add -A`（只按 scoped manifest）；禁 merge 姊妹线/向姊妹线分支推送。
7. **禁 claim**：禁 SKR / secure-key / 资格化 / composable 安全 / publication claim；
   **禁单点 `f_eff ≤ 1.3` 认证句**（N_req 402/575 > 200/276/364、joint 可认证集 = ∅ ——
   `decision-log.md:4897`；可给**实测效率曲线**）；禁路线裁决句、禁运行点选择句。
8. **禁范围扩张**：**暂不开 A1 / 全 q（direct-q1024）/ SKR**（PACKET §6）；
   **Mitra / Müller 只作选型依据，不得作胜出证据或可比性能/认证证据**（PACKET §6-4）。
9. **禁自填**：预算槽、授权块、UUID、命令、门前提状态 —— 任何留白**不得由执行者填写**
   （留白/不符 ⇒ STOP 回主线程）。

## §2 前置停止条件（Pre-EXECUTE；任一不满足 ⇒ 不执行）

1. PACKET §10 授权块**恰好一处**填全（grant verbatim、UUID、预算 ①–⑧、确切命令、日期/签名）。
   留白/不符 ⇒ STOP，**不得自行填写**。
2. Pre-EXECUTE Q0–Q5 全 PASS 并写入日志条目 0：
   - **Q0** 目标分支 `formal-ir-v72p1-addendum-clean`（不切分支；`git branch --show-current` +
     `git rev-parse HEAD` 实测记录，冻结时点基线 `8e9c8526` 仅为 provenance）。
   - **Q1** 范围清洁：可写面仅白名单 §0-2；`git diff -- src/` EMPTY；脏树按显式文件清单界定
     （PACKET §1-创建范围所列既有改动原样保留，不纳入本包）；禁碰文件零改动。
   - **Q2** 冻结契约核对：PACKET §2 七元组逐项与授权时冻结一致（含"改长度/改模型 = 新包"未触发声明）。
   - **Q3** 输出缺席：目标根不存在（`test -e` 为否，UUID 立即复证）；`results/` 与
     `comparison_bench/outputs_comparison/` before 快照已记录；保护根快照字节一致。
   - **Q4** focused fake-only 测试 PASS 并附输出：
     `PYTHONPATH=/mnt/d/Code/HD-QKD_Polar_Comparison .venv/bin/python -m pytest -p no:cacheprovider -o addopts="" comparison_bench/tests/<REALPOINT_NB1024_TEST_FILE [TO BE FROZEN]> -q`
     —— 测试**显式传 fake runner**，不得隐式触发生产解码/真实数据管线（AGENTS §10.1-8）。
   - **Q5** 预算闭合：**TIMING 帽已由主线程定**，PACKET §7 槽 ①–⑧ 全部填实（见 §5 顺序）；
     授权块填全。
3. **P3 verdict 前提已记录**（见 §3）且后果句已写入日志条目 0。

## §3 P3 verdict 前提（强制记录；前提 ≠ 授权）

1. **记录事实**：`P3_MEMORY_AUDIT_PACKET.md` = **FROZEN — NOT GRANTED — NOT AUTHORIZED —
   NOT EXECUTED**；§2.5 T-M1..M4 = PROPOSED re-freeze v2、T-C0 = REUSED；§7 授权签字块**全 BLANK**
   ⇒ **P3-gate 无 verdict**（真实帧记忆审计未执行）。
2. **强制后果句（逐字写入日志条目 0 与结果记录）**：
   > "P3-gate 无 verdict ⇒ **禁把合成 FER 当真实 FER**（`EXECUTION_PLAN_20260922.md:217`）；
   > 记忆假设**未证伪 ≠ 已验证**，且带电池粒度 caveat（ACF 电池对 ≳0.005 量级帧间相关才有功率、
   > 对帧内记忆结构性失明 —— P3 §1/§2.3）；本包对外句强制带该限定。"
3. 本 prompt **不补做、不催做、不授权补做** P3 执行或 verdict 获取；P3 状态改变只经其自身包 +
   显式用户授权（PACKET §4）。
4. 若执行期间发现 P3 包状态与上述记录不符（例如被授权/被执行/被改动）⇒ **STOP 回主线程**，
   不得自行解释。

## §4 同数据表引用（报告义务；回报只引用 ID）

1. 结果记录与 Pre-RESULT 必须逐项覆盖 `SAME_DATA_CMP_METRICS.md` §10 验收项
   **A-CMPE-1 … A-CMPE-7**（ID 稳定，回报只引用 ID，不复述条款全文改写）：
   - **A-CMPE-1**：per-source 四计数独立列（`attempted` / `exact_match`=¬failed（`decoded`≠success
     图例）/ `accepted` / `accepted_wrong`=`undetected`）；`undetected` 禁并入 success/FER；禁跨源/跨实例合并。
   - **A-CMPE-2**：`f_super` 与 `f_eff` 双数并列，`f_eff` 用本臂 m 基（202 → 1.259759 / 208 → 1.294947），
     禁互相替代、禁把 `f_super` 当 `f_eff`。
   - **A-CMPE-3**：`leak_EC` + 64-bit tag ⇒ verification-aware `λ_total`；完整协议链逐项列开；
     **每源 1.50× prior 机会成本行**。
   - **A-CMPE-4**：总/每块/每译码 wall + 峰值 RSS + 交互消息数；IR 吞吐与采集率分标。
   - **A-CMPE-5**：`N_req` report-only vs key-eligible（**200/276/364**）分列；`d`/`q`/`n_IR` 分离；
     合成/真实/key-eligible 三组计数分离。
   - **A-CMPE-6**：R3/MLC 历史口径标注（tagless/冻结口径、H 基、原生单遍综合征）+ "不可比即标"；
     r=10 native≈9× 成本行独立 + **探针不替真实结论固定句**（逐字照抄 SAME_DATA §7-2）。
   - **A-CMPE-7**：无安全观测量 ⇒ 仅"实测纠错/公开开销收益"、**禁 SKR**（M5 选点禁令）；
     每个数字落 measured / assumed / projected / qualified 四列之一。
2. 缺任一项 ⇒ **Pre-RESULT FAIL**（阻塞固化，见 §6）。

## §5 预算（TIMING 帽定后填；本 prompt 不设任何数）

1. PACKET §7 槽 ①–⑧ **全部 `[BLANK — TIMING 帽定后填]`**：单窗口 wall 上限、批次总 ceiling、
   单调用/单次解码帽、峰值 RSS、CPU 数、机器根 UUID、输出缺席 + 保护根快照 + `git diff -- src/` EMPTY、
   focused fake-only 测试输出。
2. **填入顺序（冻结）**：① 主线程定 **TIMING 帽**（依 timing 证据裁定；`S2_TIMING_PROBE_20260920.md`
   为既有参考件 —— mean-case ≈3433 s vs 3600 s 窗口、worst-case ≈4735 s 超窗、RSS ≈721 MB、
   verdict MARGINAL，report-only，其 smoke 结果无 FER 含义）→ ② Pre-EXECUTE 把槽 ①–⑧ 填实
   → ③ 授权块（PACKET §10）填全 → ④ 才可执行。
3. **倒序/缺项 ⇒ STOP**，执行者**不得自行填数或沿用他包预算**；`unspent budget ≠ authorization`。
4. 停止语义随预算生效：超时 = 终态（不续跑）；wall-partial ⇒ `INCOMPLETE-wall` 保留、永不续跑；
   无 retry/resume/adaptive；"grant spent" 后无重跑。

## §6 执行与评审（一次授权 + 独立 Pre-RESULT）

1. **一次授权**：单一 FRESH EXPLICIT USER GRANT（PACKET §10 授权块，签名或本周期 verbatim 对话
   授权记录 —— F-3/X1/X1S 先例，仅限本周期）覆盖本包**全部臂序列**（臂序列由授权块冻结；
   无逐臂授权、无二次确认循环；操作者在前一机器门放行时继续下一臂）。
2. **Pre-EXECUTE 记录**（日志条目 0）：Q0–Q5 证据 + P3 verdict 前提句（§3-2 逐字）+ 入口语境 +
   TIMING 帽定值与预算填实截屏/文本。**任一 FAIL ⇒ 阻塞执行**（AGENTS §3 Pre-EXECUTE 强制）。
3. **一次执行 + 一次结果记录**：fresh 根内按冻结命令执行一次；产出 `RESULT`（或等价单一
   append-only 记录的结果节）+ 机器伪影（分源表、逐臂计数、墙钟/RSS）；分源分列、逐实例分列、
   `undetected` 单列；失败/`INCOMPLETE-wall` 臂**保留不覆盖、不续跑**。
4. **独立 Pre-RESULT**（独立线程/评审者；发布或提交前**强制**）逐项重核：
   (i) 计划阈值/门与 PACKET §2/§5 一致（无静默改值）；
   (ii) 泄漏公式分解：`leak(m)=5m+64`、`λ_total = leak_EC + 64`、tag 64 b/超帧不翻倍、
       `f_super=(5m+64)/852.544`、`f_eff` 本臂 m 基、prior 1.50× 行**不进** `f_super`/`f_eff` 分子；
   (iii) `undetected` 隔离：在失败集合内、永不并入 success/FER 分子；
   (iv) 分源分解：1M/1.5M/2M 各自成表，无合并行；三组计数分离（240/臂、500/691/911、
        200/276/364、census 另量纲）未混用；
   (v) 披露会计：`leak_EC` + tag + 控制轮次 + 救援段 + prior 行逐项列开；
   (vi) 计划语义 vs 伪影：A-CMPE-1..7 全覆盖（§4）、claim ceiling 行在、P3 后果句在、
        无单点认证句、无 SKR 句、Mitra/Müller 未被引作胜出证据；
   (vii) 禁区：`git diff -- src/` EMPTY、禁碰文件零改动、无输出根越界、无 commit/push。
   **Pre-RESULT FAIL ⇒ 立即返工阻塞固化，不得先发布后补**（AGENTS §3 Pre-RESULT 强制）。
5. **主线程接受**：`INDEPENDENT_ACCEPTANCE.md`（或等价记录的验收节）由主线程裁决接受/改道/停止；
   本 prompt 与执行者**均不得自授接受、自授资格化**。
6. 关闭后由主线程执行 memory triage（AGENTS §3）—— 本包含指针，不代执行。

## §7 返回条件与授权块

### §7-1 返回条件（二元；禁止"进行中"式空返回）

- **COMPLETE**：全部冻结项完成时返回 —— 授权块填全 + Pre-EXECUTE Q0–Q5 PASS（附证据与 P3 前提句）+
  一次执行 + 结果记录（分源/分列/`undetected` 单列 + A-CMPE-1..7 覆盖表）+ 独立 Pre-RESULT PASS +
  证据路径 + claim ceiling 行 + 未使用/使用的修复声明（DECIDE：无预注册修复，任何重跑 = 新授权）。
- **BLOCKER**：concrete 阻塞时返回 —— 失败命令、exact error/traceback、已试补救、
  **只需主线程裁决的一件事**。

### §7-2 授权签字块（**全 BLANK** — 未填 = 未授权；与 PACKET §10 同步，唯一填充处是 PACKET §10）

- PREREG 状态：`DRAFT_FROZEN_PENDING_AUTHORIZATION`
- 用户授权 verbatim：`[BLANK — 未授权，不得执行]`
- 臂序列 / 机器根 UUID：`[BLANK — TO BE FROZEN AT PRE-EXECUTE]`
- TIMING 帽与预算 ①–⑧：`[BLANK — TIMING 帽定后填]`
- Pre-EXECUTE verdict：`[BLANK — 未执行]`
- 独立 Pre-RESULT verdict：`[BLANK — 未执行]`
- 主线程接受：`[BLANK — 未接受]`
- 日期 / 主线程 / 签名：`[BLANK]`

**未授权不得执行。本 prompt 不授权解码、不授权构造、不授权真实数据访问、不授权 commit/push、
不授权任何臂；本 prompt 授权任何执行 = 0。**
