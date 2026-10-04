# SESSION-AUDIT-20260928 — 独立回溯审计（main 线程一个工作会话）

- 日期: 2026-09-28 · 性质: **回溯审计**（retrospective audit），非 Pre-RESULT 门、非批末审查
- 审计员: 独立只读线程。**未写任何文件、未运行任何译码器/构造/pytest/科学命令、未开任何 `.ttbin` 或信道包、未 commit/push**
- 审计对象: 本分支 `4c57ee9f`（137 文件）与 `23183c73` 两笔提交，以及 M2 会计修正、CHAN-QUALITY-SURVEY、M3D、PERPLANE Stage 0、U1 探针、PROXY-RECALIBRATION 五个周期的记录与产物
- **方法要求（审计员自述）**：不采信任何文档的自我评估。每条结论都要找到支撑它的产物并核对；无法核实者明说无法核实，而非因怀疑而否定。
- **独立性要求（审计员自述）**:委托方**未**告知其弱点位置与数量。审计员若未发现问题亦为有效结果，前提是其确实查证过。

## 1. 总体评估

**产物上扎实**：两个作废基线与整套会计机制。**过度声称处均已按流程撤回**（M3D）。多数 DECIDE 工作围栏得当。

本会话的核心信道发现**在围栏形式下成立，在短形式下被过度声称**。逐面 KILL 算术作为**暂定算术**成立且已被正确标注为暂定。**联合编码「装得下」不是发现**。三个吞吐/来源数字是推导量或委托方给定量，仅在最新文件中被正确标注——不是测量。

**未发现静默数据损坏、未发现覆写根、未发现未授权执行。** 两处陈旧的方向页陈述与两处短形式标题，会误导只引标题的未来读者。

## 2. 十条主张的判定

| # | 主张 | 判定 | 决定性证据 |
|---|---|---|---|
| 1 | HDC 与 LB 真实基线作废；LB 36/28,000、HDC 0/28,000 | **SUPPORTED** | 三个根 `block_accounting.csv` 的 `exact_match` 列：HDC 全 0，合计 6560+9184+12256=28,000；LB 12+7+5+6+3+3=36（0.13%），block FER 0.9963–0.9995，超帧成功为零。void 标签在代码上正确：`hd_cascade.py:224-229` 无条件 `accepted=True, toeplitz_verified=False` 加门 `:280-281` 无法返回成功；LB 验证器在工作（1M-197 拒绝 3268/3280、undetected 215），故 `void-stub-artifact` 正确地**未**施加于 LB，`void-no-correction` 正确地施于两者 |
| 2 | 显示的效率列从不读公开量，结构上无法区分方法 | **SUPPORTED** | `m2real_runner.py:247-255` 的 `f_super=(5m+64)/(1024H)`、`f_notag=5m/(1024H)` 只取 `(m,H)`；`lambda_parts.leak_EC` 在 `:786-801` 另行累加。1M/m197 记录泄漏 1,707,485 vs 646,160（2.6425×）而两族同显 1.20048829。T2 12/12 逐位精确 |
| 3 | 真实 LB 后端不可恢复，且是结构性的而非记录丢失 | **SUPPORTED** | `m2real_runner.py:878-880` 调用 fallback 时不传 `sidecar`；`m2lb_arm_runner.py:1514,1525-1530` 在 `sidecar=None` 时跳过写入；`sidecar` 一词在 `m2real_runner.py` 中出现 **0 次**；每根恰 3 文件，`grep -i backend` 0 命中，`rows.json` 17/34/37 键均无后端字段。选择 `resolve_spa_decode_fn:1482-1504` 是 `find_spec("ldpc")` 的纯函数。**重跑同一命令复现同一空缺**。围栏正确：当前环境 `ldpc` 缺席、`wall_s` 0.078–0.093 s 软信号，均被拒绝作为证据 |
| 4 | Gray 位面相互独立 / 五次采集零共错单翻转 | **OVERSTATED** 作「相互独立」；**SUPPORTED** 作围栏三元组 | 五个 JSON 显示 `expected_planes_flipped` 两路线均 1.0（Arm A 的 0.9999999999999999 仅为浮点求和次序）、非对角恰 0.0、popcount 仅 {0,1}。但 `n_pairs` 合计约 1M；零双翻只排除高于约 1e-6 的多面率，**低于探测限的罕见双翻未排除**。接受记录 §6 与 Part B(i) 已要求探测限限定与三元组引用、禁止裸用「独立」，**但 `RESULT.md:64`、`PERPLANE PROPOSAL.md` §1 H1、`NOW.md` §5 D-6、`decision-log.md:5122` 仍在句中裸用**。且全部测于单一强加分箱 1024×200 ps |
| 5 | Stage 0 逐面率分配在既定预算下不可行；联合编码替代方案可装下同一预算 | **拆分**：前半 **SUPPORTED**（暂定），后半 **UNSUPPORTED** | `workspace/s0_1bbe38ac/S0_SUMMARY.md`：CQ-J21c f=1.3 名义 1875 vs 1104，超 771；五源名义均超 690–772；一致性间隙 +0.498–0.533 bit/符号。算术可自冻结 `p_k` 复现。但 `STAGE0_LOG.md` 收口与 `NEXT-STEP-OPTIONS/PROPOSAL.md:136` 均标注独立审查待做 ⇒ **KILL 在其落定前为暂定**。联合的「≈1099 vs 1104 装下（勉强）」（§1 选项 E）是 `1.3×0.8257×1024` 的**理想乘法，无 ceil、无回退、无构造、从未执行**，余量 5 bit（0.45%）。**按包自身的 +20% 回退（等效 f=1.56），联合需约 1319 bit，超约 215 bit。联合回退分析不存在。**「会装得下」把 5 bit 理想余量说成发现；正确表述是一个待做的解析 TODO |
| 6 | 降迭代上限不能解决墙预算问题 | 宽泛形式 **UNSUPPORTED**（已被正确阻断）；窄形式 **SUPPORTED** | `M3D-ITER250-SYNTH/BATCH_END_REVIEW.md` B1（line 30-39）阻断日志 line 34 的一般否定与 M3C 后果；§6（line 89-92）只允许逐字「单次点估计未达 10% 门…未决，不由此推出 M3C 或吞吐后果」。依据：11.0025 s 缺口 vs 同批内 cap-无关工作上已demonstrated的 7.2538 s 偏移（exact 层 5.6387 s + block 193 同 110 迭代 1.6150 s）、2.13pp 余量、跨日基线、Stage-1 合成 vs M3C Stage-2 越界的范围错配。`decision-log.md:5078-5084` 已标 5072 条目 SUPERSEDED，传播扫描干净。`docs/NOW.md:87`「审查待做」**已陈旧——审查已存在** |
| 7 | u1 估计路径无开发余量 | 仅有界天花板形式 **SUPPORTED**；作为实测最优性 **OVERSTATED** | 头部界 `H(U1|B)≈0.024×1024≈24.6 bit，24.576/(1024×0.826)≈0.029` 算术正确（熵占比 2.94–3.02%）。`workspace/u1_probe_2d29578d/U1_RESULT.json` q 5.7–9.4e-4 vs ser ~0.25（比 0.002–0.004），在具名 IID-INVERSION 下。包 §§3.3/5.4/11 明示：q 是弥散等效指数非实测计数；突发会高估、u2 条件化可能低估；精确真相属 DECIDE 后继 F2-EXACT-U1。`U1_LOG.md` 标注审查待做。「F 在任何结局下关闭为改进路线」成立；「u1 实测近乎最优、无余量」超出该界 |
| 8 | 可用数据中不存在更易工作点 | 绝对形式 **OVERSTATED**；围栏形式 **SUPPORTED** | 五次实测采集 ser 0.23856707–0.25433839 同带；CQ-20c/d REFUSE 不产冻结链 SER（peak_to_bg 85.01/58.73<100，offset 从未借用）；SHG 范围外并记 cw 泵浦更高噪声之由；1.12 因 29.9999524 s 对 `3s` 标签隔离。接受 N-6 与 Part B(ii) 要求围栏形式并禁止本体形式，**但 `RESULT.md:70`、`decision-log.md:5122`、`NOW.md:121-124`、`PERPLANE PROPOSAL.md:86` 使用绝对形式作标题**。**不得单独引用标题** |
| 9 | 主线 GF(32) 基本处于公开量预算天花板 | **OVERSTATED** | M0 2M-m208 名义 `5×208+64=1104` **按定义即等于预算 1104**（`STAGE0_PACKET.md` §3.5 链），`f_super` 1.29375 对 1.3 门，FER 16/383 [0.025875,0.066776]，最小实测 `f_eff` 1.464047。**这是同义反复的名义相等，不是经验天花板发现。** 实际公开量未知：M0 `rows.json` 无 `leak_EC`/tag 账本（键仅 m/superframe/exact/undetected/full10/status），`CORRECTION_RESULT.md:226-230` 明禁构造 NB 实际公开量列。若主张指名义则成立但平凡；若指实际公开量余量则不成立 |
| 10 | 「2–4×」「1.6×」「≈366 sym/s vs 480–900×」的来源 | 三者皆为推导量或委托方给定量，**不是测量**；标注决定判定 | 「2–4×」作记录数字 **UNSUPPORTED**：`NEXT-STEP §8` 明记方向已验（M0 5 更差/1 一致/0 更好），但**仓内查无该倍数**，bundle 从未打开，合成 SER 仓内未知。只能作委托方给定量级。「1.6×」**OVERSTATED**：邻近已验为 10 面 Σh2/H=1.642（J21c，1.3559/0.8257）、planes 0–4 子集约 1.55，但「字母表所编码的五个面」这一精确子集定义未找到。「≈366 sym/s vs 1.75–3.27e5 对/s，差 480–900×」作标注推导 **SUPPORTED**、作测量 **UNSUPPORTED**：366=1024/2.80，而该 b2f 数字在 `decision-log.md:4745` 自身即被标「derived, pending independent arithmetic review」；配对率由 M0 计数÷约 3 s；差距是两个推导之比。`NEXT-STEP-OPTIONS` §1 选项 D 与 §8 正确携带双标注，**必须始终带标注引用** |

## 3. 过程纪律

**围栏**：M2 会计修正堪称典范（claim ceiling、void 标签、D-1 延后不定头条、无排名、T4 范围）。M3D B1 执行典范——过度声称经 supersession 撤回而非静默改写。Stage0/U1/Proxy 三包的围栏正确（无 FER/效率/泄漏/f/SKR、无方法句、零 `.ttbin`/包接触、新根）。

**围栏设计问题**：Stage 0 在 1104 单 tag 预算上判 KILL，而 D-1 延后不定头条。**771 bit 的超额是稳健的**——一致的 16-tag 会计下（Σm+1024 对 1104+960）超额仍为 771 bit，故结论存活，**但包应显式陈述该稳健性**。

**标题破坏围栏**（主张 4、8 的绝对形式）。`decision-log.md:5122` 的「is an artifact of」强于接受记录 N-9 的「further cause unestablished」；按 `NEXT-STEP §8`，**以较弱的接受措辞为准**。

**`NOW.md` 准确性：在当前时点陈旧。** HEAD `23183c73` 正确；**porcelain 少计**——只列 2 dirty + 4 untracked（仅 CQ），漏 `PERPLANE`/`U1`/`PROXY`/`NEXT-STEP` 四目录与 `perplane_stage0.py`、`u1_ceiling_probe.py`、`proxy_recal_sampler.py` 及测试。§4 M3D「review still pending」**为假**（审查已存在，PASS_WITH_FINDINGS）。§5 D-6「审查待做、无可提升」**已过期**——`CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md` 已存在且两条待办（N-9 措辞、N-5 完整 ceiling）已关闭。页面自述「声称已更新快照实则未改、必须重测、不得引用数字」是诚实的且起缓解作用，但未来 agent 仍须按 §1 注记重测。

**Track 分类：正确。** CQ 为 DECIDE 正确（真实 `.ttbin` + 路线相关；零解码不豁免）。M2 会计为 DECIDE 正确（承声明的重算）。M3D 为 EXPLORE 正确。Stage 0 为 EXPLORE 正确并给出显式 §0.1 论证（对已落盘统计量做算术，非数据接触）。U1 为 EXPLORE 可辩护但激进（对真实帧布尔计数）；升级到 DECIDE 后继 F2-EXACT-U1 的围栏正确。Proxy 为 EXPLORE_HEAVY 正确。

**修复边界：被遵守。** M3D/Stage0 修复额度未用。U1 的测试代码修正发生在执行前，正确地未计入 §8。Proxy 第一次尝试的 F6 REFUSE（零块、缺 `four_cycles`/`rank`/`min_girth` 三字段透传）获授权为单次 §8 工程修复并附逐字授权，同种子/图/门限，失败留存；重跑 INCOMPLETE（wall>3600 s）终态，无第二次修复，无放宽重读——**堪称典范**。区分修复（管道遗漏、门未动）与科学变更（采样器、种子、规则）划得正确。

**记录中不成立的实例**：裸用「独立」；绝对式「无更易点」；若单独引用被取代条目则 M3D 宽泛否定；无推导标注的 2–4×/1.6×/366；把联合 1099 当发现；把主线贴天花板当实际公开量发现；把 NOW 的陈旧门状态当现状引用。

**做得好的**：M2 四段门加 T2 逐位精确与独立 T3；Rev 2 supersession 注记逐字保留 Rev 1 并附日期更正；F-p window 泛化更正注记（1000 对 200、分析窗口来自代码非 header、对数字无影响）；拒绝纪律（CQ-20c/d 的 offset 从未借用、proxy 验证 REFUSE 语义、M3D 的 R2 正确扣留）。

## 4. 无人发现的事项

- **NOW 的 porcelain 与审查状态陈旧**（超出 N-7 碎片注记的范围）。
- **Proxy 的 INCOMPLETE 本身即信号且现已搁浅**：M3B-R1 在**容易**的合成上 250 次解码 1767 s，而重标定后**更难**的信道上 240 次跑不完 3600 s，提示大量 `max_iter=300` 饱和——即**率硬化信号**。但行数据随 kill 全丢，D-1/D-2 未写。按 ceiling 不得提升，但**新包应使用分段落盘，使部分行能在超时后存活**。
- **U1 的 R 值 0.44–0.62**（u2 成功内的超帧级不一致）非常高；「近乎最优」完全依赖到「每超帧约 1 个错」的 IID 反演。**plug-in H 或反演的不确定度未传播**。下一读者可能把 q 误当测量。
- **CQ-20c/d 的 argmax bin 8191（−50 ps）与通过组一致**——存在弱峰，仅低于门被正确拒绝。值得作为未来探针目标记下，**但不得借为证据**。

## 5. 单一最 consequential 的弱点与补救

**联合结构方案「靠 5 bit 活着」的叙事。** 独立方案死 771 bit（暂定但稳健），联合方案活 1099 对 1104 的理想值——5 bit 之前还有 ceil、有限长、tag 分列会计与回退。**按 Stage 0 自身的 +20% 回退，联合方案超约 215 bit。** 联合回退/ceil 分析不存在，而选项 E 被推荐为廉价前置并可能吸收设计开销。

**补救**：在任何 Stage-1 式构造包之前，先冻结并执行秒级的 E 解析定价包（选项图已草拟的 T-N2）：同一批冻结 CQ JSON，`ceil(1024·f·H)` 加 +10%/+20% 回退列，按 D-1 分列所有 tag 总量，对实测 `H(A|B)` 作一致性检查，**只有带回退仍装下才判 PASS**。若失败则在零设计成本下放弃 E；若勉强通过，则在任何合成筛选（其本身尚需重标定代理）获得资助前，要求用户对 5 bit 边际值明确表态。

## 6. 确认

未写、未改、未删；未运行译码器、构造、pytest 或任何 python 科学命令；未开任何 `.ttbin` 或信道包（`gamma_f03.npz`、`pairs.parquet`、`x1_*.npz` 从未触碰）；未 commit/push。仅只读检查：`git branch/log/show/status/diff`、`ls`、`cat/head/tail`、`grep/rg`、对 `block_accounting.csv` 的 `awk` 行计数、`sed` 行范围、`wc`。
