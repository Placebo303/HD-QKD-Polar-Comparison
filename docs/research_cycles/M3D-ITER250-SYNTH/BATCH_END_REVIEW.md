# G-M3D-ITER250-SYNTH — BATCH-END + ESCALATION REVIEW (independent, EXPLORE)

- 日期: 2026-09-27 · 角色: 独立批末审查员 + AGENTS §10.3 要求的 FAIL 升级审查 · 只读
- 受审批次处置: **R1 FAIL / STOP，R2 正确未运行**
- 审查员未写任何文件、未运行任何译码器或臂 runner（含 `--dry`）、未用 git 写操作、未开任何 `.ttbin`、未触碰 `results/` / `comparison_bench/outputs_comparison/` / `docs/` / `openspec/`。全部为只读检查，算术内联展示。

**裁决: PASS_WITH_FINDINGS。** 一条 BLOCKING（B1），仅针对**已记录的假设级后果句**，不针对机械门判定。

**受审处置在机械意义上确认正确**: 门 FAIL 算术正确、R2 正确扣留、预算达成、日志与机器产物忠实支持所记录的尝试。不可支持的是日志中的假设级否定后果句（见 §2、§4、§6）。

## 1. PACKET 验收项逐条

| # | 项 | 状态 |
|---|---|---|
| 1 | R1 16/16 完成，`verdict=COMPLETE` | **PASS** — `rows.json` 16 行；summary `blocks_done=16`、`verdict=COMPLETE` |
| 2 | R1 身份门（配对种子/索引 vs 只读 M3-b 比较器） | **PASS** — 8 个 exact 索引(0–7) 全 `baseline_exact=true`；8 个 nonexact(127,158,186,192,193,204,210,217) 全 `baseline_exact=false`；每行满足 `seed=2026096401+block_idx`（抽查 block 0/127/193 对比较器：wall 2.3909724439727142 / 70.06459923798684 / 25.578361522057094，iter 10/300/110 完全一致）；runner 的 `validate_comparator` 另将两个 wall 总和钉到 1e-6 |
| 3 | R1 准确率门 | **PASS** — 8 个 exact 行 `new_exact=true`；8 个 nonexact `new_exact=false`；`new_undetected=0`、`new_undetected_unknown=0`、零 timeout 行；block 193 保持 `converged_no_syndrome`/110 iters |
| 4 | R1 资源门 | **PASS** — 单调用最大 wall 66.73978763003834 s < 90；elapsed 513.1959565710276 s < 1200；RSS 0.16473007202148438 GiB < 2 GiB |
| 5 | R1 runtime 门（nonexact 层 ≤ 516.273374667042 的 90% = 464.64603720033784 s） | **FAIL（机械正确）** — 8 行重算 475.64855074719526 s ✓；ratio 0.921311409975293 ✓；**超出 11.00251354685742 s**；节省 7.87% vs 需要 10% |
| 6 | exact 层 wall（仅描述性，无门） | **记录正确，未设门** — baseline 重算 29.048769954824824 ≈ 29.0487699548248 ✓；new 34.68751789513044 ✓；差 +5.63874794030564 s (+19.4%)，而 exact 层迭代数完全相同 124→124 ✓ |
| 7 | 迭代数描述 | **PASS** — baseline 124+(7×300+110)=2334 ✓；new 124+(7×250+110)=1984 ✓ |
| 8 | 双臂要求；R2 仅在 R1 COMPLETE + 四门全过时 | **PASS（程序）** — R1 `arm_pass=False` ⇒ R2 正确扣留；家族根仅含 `R1_17b6c2e9/` + `EXPLORATION_LOG.md`；`R2_45ad8f31` 不存在且被要求保持不存在 |
| 9 | 无重跑/续跑/调参/再授权；≤1 预登记工程修复 | **PASS** — 日志无重跑、续跑、门限/种子/图变更、真实数据读取、Stage 2；修复额度未用 |
| 10 | 批次预算 ≤2400 s；保护根只读 | **PASS（审查范围内）** — 单臂 513.196 s < 2400；`stage2_calls=0`；runner 拒绝非 fresh / 越界 / 禁止根；PRE-EXECUTE A3 记录保护根 diff 为空。审查员在禁跑约束下未复跑 `git diff`；无保护写入证据 |
| 11 | 单条追加日志；一次独立批末审查 | **PASS（结构）** — 单条 `EXPLORATION_LOG.md` 含 Pre-EXECUTE 条 + 完成条 + 尚无审查结论的声明；本文件即那次独立审查 |
| 12 | OpenSpec 一致性（M3D-01/02 实现 vs `m3d-iter250-synth`） | **PASS** — `decode_block_marginal(..., max_iter=250)` 覆盖默认保持（`MAX_ITER` 默认在 line 450 未动，校验 469–471，透传 490，回存 499）；每个 R1 行存证 `max_iter=250`；runner 四门（`_summarize` 302–384，门布尔 348–353）恰实现包的四个门，`NONEXACT_WALL_LIMIT=0.90`；claim ceiling 串在代码(379–383)、`rows.json`、与 `M3D_RESULT.md` 一致 |

## 2. BLOCKING

### B1 — 日志中记录的后果句超出单次未重复运行所能建立的范围，禁止提升

位置: `workspace/m3d_iter250_synth_20260927/EXPLORATION_LOG.md` line 34:
> 「The retained finding is the negative answer to the frozen question: **lowering the iteration cap does not deliver the required call-cost saving, so the M3C wall-budget problem is not solved this way.**」

机械门 FAIL（本次 7.87% < 10%）正确且必须保留，但该句读作**假设级否定**——一个关于该 cap 的一般性主张——并进一步转成 M3C 后果（「不是这样解决的」）以及（按升级审查的提法）下游「吞吐工作成为承重项」的导向。

§4 的噪声分析显示：**11.0025 s 的缺口与本批内已直接展示的跑测间偏移同量级**——8 个 exact 格在**迭代数完全相同**的工作上 +5.6387 s（全部为正，+0.47~1.01 s/格），block 193 在**同样 110 次迭代**下 +1.6150 s；合计已demonstrated偏移 **7.253767212270778 s** vs 缺口 11.0025 s。**2.13pp 的余量，在 8 个格、单次测量、且基线是前一天跨日测的条件下，无法区分「cap 不足」与「噪声」。**

阻断范围: B1 的句子不得被提升进任何下游记录、decision-log 或后继包的动机。**本批证据只能提升为 §5 中的那条狭窄机械陈述。** 门 FAIL 本身、STOP、以及 R2 扣留均不受影响，继续成立。

## 3. NON-BLOCKING

- **N1 — 事后补写的日志条目（已披露，可接受）** — 日志 line 17 诚实记录完成条目由后续文档任务而非同期写入。来源可溯、数字溯至机器产物（审查员已核）。同期记录更佳；无需动作。
- **N2 — 未留存 shell 退出码产物** — 日志 line 22 已披露；完成性由 runner 终态判定 + 16 行产物佐证。轻微来源缺口；建议后续批次留存退出码。
- **N3 — 跨日基线对新运行的 wall 比较且无逐格重复** — 包冻结了该设计（逐格单次、单一 90% 门），执行合规；但该设计使任何接近门限的结果都不可解读。后续包应或做重复，或改按**迭代数**（确定性）设门，或预登记噪声余量。仅观察；本批不得返工（重跑被禁止）。
- **N4 — exact 层的整体变慢被正确处理** — 8 个 exact 格每格慢 0.47–1.01 s（+14–26%/格）已按描述性记录，且明确未被表述为回归（日志 line 36）。纪律正确；该层设为仅描述、无门是正确取舍（见 §4 C2）。

## 4. C1 / C2 判读

### C1 — 单次运行的 7.87% vs 10% **不足以**支持「降迭代上限无法交付所需调用成本节省」这一假设级主张。诚实读法: 本批**分不出这 2.13pp 的余量**。

单元数为 1 个已执行臂中的 8 个 nonexact 格，每格一次测量，零重复，基线在共享机器上于前一日（2026-09-26）测得，而新运行在 2026-09-27。缺口是在 516.2734 s 基线上的 11.0025 s。

对照之下，**同一批**直接展示了 cap **无法**影响的工作上的数秒级跑测间偏移: 8 个 exact 格执行的是逐字节相同的计算（10–24 次迭代收敛，两个 cap 都远未触及），却共 +5.6387 s（+19.4%，每格为正 0.47–1.01 s）；block 193 以**相同的 110 次迭代**到相同状态，却 +1.6150 s（+6.3%）。cap 无关工作上已demonstrated的合计偏移: 5.63874794030564 + 1.615019271965138 = **7.253767212270778 s** — 与 11.0025 s 缺口同量级。一个均匀的 +0.7 s/调用 偏移（exact 层均值）施加到 8 个 nonexact 调用上，本身就能解释掉 ~5.6 s。因此在 ~60–70 s 的单元上，跑测间方差**合理地**足以解释 0.921 与 0.900 之间的差别。

**本批建立了什么**: 预登记门在本次单次 R1 运行上未达到（机械 FAIL，正确地停住了 R2）。
**本批没有建立什么**: cap 是否真的无法交付 10%；重复是否会通过；关于 R2 图实例的任何结论。
**该 FAIL 不得被读作比「R1 的点估计一次未达冻结门」更强的否定。**

### C2 — exact 层变慢的原因是测量/系统性偏移，不是迭代 cap；代码排除了 cap 效应，但无法区分具体系统源

`decode_block_marginal`（`v80_b2f_campaign.py` 448–509）把 `max_iter` 直传 `decode_error_domain_posterior` → `decode_fftqspa`（`nonbinary_v10_fftqspa.py` 307–455），其循环为 `for iteration in range(1, max_iter + 1)`，在 syndrome 成功（434–436）或 streak 收敛（437–439）时提前 break；kernel 标注「Deterministic — no RNG anywhere」（line 318）。8 个 exact 格全部在 10–24 次迭代收敛——远低于任一 cap——故在 cap 250 与 300 下执行的浮点轨迹**相同**，**不存在任何迭代数相关代码路径能让它变慢**。先验、采样器、图、种子均冻结。

因此 +5.64 s 是纯粹的跑测间 wall 方差: 机器负载、首次调用预热（8 个 exact 格是本次运行的前 8 次调用，与预热/分配器/BLAS 初始化的偏移一致）、缓存或线程放置。**代码与单次设计无法区分这些系统源**——无预热对照、无重复、无分阶段计时——此限度如实陈述。包的设计（该层仅描述、不设门）**完全正确**: 对一个干预无法移动的分层设门本就会无效，而日志拒绝把它称作回归是正确的。

## 5. 可说 / 不可说

**可支持（可提升，须带来源）**:

1. R1 以 `max_iter=250` 执行了 16/16 个冻结的 M3D-R1 Stage-1 调用，`stage2_calls=0`，全部单调用/单臂/RSS 预算内（513.196 s，0.1647 GiB）。
2. 身份与准确率成立: 8/8 选定的 exact 行仍 exact，8/8 选定的 nonexact 仍 nonexact，零 undetected，零 timeout。
3. 预登记的 R1 runtime 门在本次单次运行上未达到: nonexact 层新 wall 475.64855074719526 s > 限 464.64603720033784 s（ratio 0.921311409975293；节省 7.87% vs 需要 10%；缺口 11.0025 s）。
4. 按冻结的条件规则，R2 正确未运行；未达成双臂 PASS；**未建立任何 selected synthetic call-cost signal**。
5. exact 层 wall 由 29.0487699548248 升至 34.68751789513044 s（+5.6387 s），**在迭代数完全相同**的条件下，按描述性记为跑测间偏移，**不是**关于 cap 的发现。
6. 不随之而来任何 FER / 吞吐 / 真实数据 / 泄漏 f / SKR / 显著性 / 图族主张（claim ceiling 在 `M3D_RESULT.md`、`rows.json` summary、代码与日志中均被遵守）。

**不可支持（不得提升）**:

1. 「降迭代上限无法交付所需调用成本节省」作为一般性/假设级否定。
2. 「M3C 的墙预算问题不是这样解决的」作为本批的后果。
3. 任何由本批导出的「吞吐工作成为承重项」导向。
4. 关于 R2 图实例的任何陈述、任何池化/合并臂的量、任何对真实数据（M3C）的跨读。
5. 任何「cap 会拖慢成功调用」的主张（exact 层上升是已demonstrated的偏移，§4 C2）。

## 6. 升级后果判读

本批测的是**一个 cap 取值（250）**、在**合成**（非 M3C 真实）帧上、**仅 Stage 1**（而 M3C 的超时发生在 **Stage 2**：R1 39 个 Stage-1 nonexact → 39 次 Stage-2 尝试；R2 死在 Stage-2 frame 160）、在**一张图**的 8+8 个选定格上、**每格一次**、对照**跨日基线**，以噪声量级的 2.13pp 未达门。故「M3C 墙预算问题被证明无法靠降 cap 解决、从而使吞吐工作成为承重项」在证据上属**过度推论**（BLOCKING B1）。

**审查员允许的最强后果表述（逐字）**:

> "M3D-R1's single-run point estimate did not meet the preregistered 10% gate, so this batch provides no positive signal for the 250-cap; whether the cap could meet the gate on repeat, on the second graph, or on real frames is unresolved, and no M3C or throughput-work consequence follows from this batch alone."

任何后继都需要新的冻结问题、预算与授权；M3C STOP 记录的约束（无已接受的双臂决策、无 FER 提升）不因本批改变。

## 7. 阻塞

无。审查完成。唯一需主线程的动作是归档本审查并执行 B1 的提升限制。
