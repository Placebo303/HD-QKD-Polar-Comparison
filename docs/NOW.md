# NOW — 一屏现状（2026-09-28，docs-only）

> 新会话只读本页 + `docs/EXECUTION_PLAN_20260922.md` 即可接手。
> 本页不授权任何执行（无解码 / DE / 真实数据 / commit / push / 资格化 / 发表）。
> Track：documentation-only（AGENTS.md §1.2 矩阵，无 track gate）。

## 1. 分支 / HEAD / 脏树（读取于 2026-09-28；**任何执行前必须重测**）

- 分支：`formal-ir-v72p1-addendum-clean`（实测）。
- HEAD：`23183c73`（full `23183c73fd4b1597f2c42a6e9b06fa2de4402b9c`）。
  本分支已把 M0/M1/M2/M3 全部周期与 M2 会计修正提交并普通非强制推送到
  `origin/formal-ir-v72p1-addendum-clean`（两笔：`4c57ee9f` 主干 137 文件、
  `23183c73` 并行会话的跨仓 Polar 对比）。**本分支尚无对应 PR**；PR #1 挂的是
  另一 base（`formal-ir-v80-nbldpc-jan21`），与本分支无关。
- 工作区（`git status --porcelain` 2026-09-28 实测）：
  - tracked dirty **2**：`M docs/NOW.md`、`M docs/decision-log.md`
    （均为本轮 CHAN-QUALITY-SURVEY 记录及后续文档修正所致；
    本页自指快照不含本页的改动内容）；
  - 未提交（untracked）**18 条目**，分组如下——
    新增 CLI runner **6**：
    `comparison_bench/src/comparison_bench/cli/cq_channel_survey_armA.py`、
    `comparison_bench/src/comparison_bench/cli/cq_channel_survey_armB.py`、
    `comparison_bench/src/comparison_bench/cli/perplane_stage0.py`、
    `comparison_bench/src/comparison_bench/cli/u1_ceiling_probe.py`、
    `comparison_bench/src/comparison_bench/cli/proxy_recal_sampler.py`、
    `comparison_bench/src/comparison_bench/cli/joint_pricing.py`（JOINT-PRICING
    包新增脚本，由另一 agent 起草；本任务不触碰该路径）；
    新增 fake-only 测试 **5**：
    `comparison_bench/tests/test_chan_quality_survey_fake.py`、
    `comparison_bench/tests/test_perplane_stage0_fake.py`、
    `comparison_bench/tests/test_u1_ceiling_fake.py`、
    `comparison_bench/tests/test_proxy_recal_fake.py`、
    `comparison_bench/tests/test_joint_pricing_fake.py`（JOINT-PRICING
    包新增测试，由另一 agent 起草；本任务不触碰该路径）；
    新增周期目录 **7**：
    `docs/research_cycles/CHAN-QUALITY-SURVEY/`、
    `docs/research_cycles/PERPLANE-BINARY-LDPC/`、
    `docs/research_cycles/U1-CEILING-PROBE/`、
    `docs/research_cycles/PROXY-RECALIBRATION/`、
    `docs/research_cycles/NEXT-STEP-OPTIONS/`、
    `docs/research_cycles/SESSION-AUDIT-20260928/`、
    `docs/research_cycles/JOINT-PRICING/`（其下仅一文件
    `PREREG_AND_AUTH.md`，其首自述为 FROZEN 待 Pre-EXECUTE + 授权的
    解析定价包，由另一 agent 起草；本任务不触碰该路径）。
    各周期机器根在 `workspace/` 下的新根（`cq_15d6f160/`、`cq_4af91a87/`、
    `s0_1bbe38ac/`、`u1_probe_2d29578d/`、`proxy_recal_3481c8d2/` 等），
    `workspace/` 被 gitignore 故不入 porcelain；
  - 早前记录的 71 条未跟踪与 6 项 tracked dirty 已随上述两笔提交清零——
    本页曾于本轮再次出现过「声称已更新快照行而实际未改」的缺陷，故任何执行前
    必须**重测**，不得引用本页数字。
- 早前页所记 HEAD `8e9c8526`（2026-09-23）与 `ce85d61f` 均已过期。
- **注：以上仅为读取时点记录；任何执行前必须重测分支 / HEAD / 脏树。**
  本页在 2026-09-27 两次出现「声称已更新快照行而实际未改」的缺陷，故
  **不得引用本页数字作为执行依据**，必须现场重测。

## 2. G0 裁决与路线顺位（冻结前提，不是授权）

- **G0 = (B) 已裁决**（2026-09-22 用户书面给出）：主文主张 =
  实测效率曲线 + 同数据二元 MLC/R3 对照；(A) 文献可比认证作
  并行/第二代扩展。
- **F3（G0=B 范围裁定，decision-log:4855）**：ROADMAP「P1 失败 ⇒ P4 在 S3 之前
  成为必经」分支被本裁决取代——**P4 不因 P1-FAIL 自动升为 S3 必经**，n=2048
  定位**第二代并行**，不阻塞 S3。
- **用户路线顺序（冻结前提）**：**① P4-elevation → ③ 并行（P4 构造可行性 +
  P3 包冻结同时推进）→ ② S-B 窄路**。2026-09-23 落档把 P1 Stage-1 判为
  **P4-elevation 输入**（decision-log:4885），**不是** P1-PASS 门票。
- **范围观察（已裁定，非新主张）**：M2 同数据比较现为一工作方法
  （NB-LDPC）+ 两个已记录的负实现结果（HD-Cascade 0/28,000、
  Layered-Binary 36/28,000；见 §5 D-4/D-5），任一基线均无可填比较列，
  比 `RESEARCH_DIRECTION_REPORT_20260924.md` §0/§5 的三方法表
  更接近 G0=(B) 头条主张。原“两方法表”预期已由 T4 接受纠正，
  不再引用。

## 3. 已接受证据（含范围上限；均不含新的执行授权）

- **M0 真实帧**：独立 Pre-RESULT PASS；真实 FER 在 6 臂中 5 臂差于合成——
  合成信道尚未成为可信开发代理，真实帧之前须先做信道条件化。
  M0 为 u2-only 链（u1 经 argmax 全局恢复、未编码未验证），引用必须带标注。
- **M1 有限长复算**：`PASS_WITH_FINDINGS`；f* 约 1.064，分解为码差距约 0.13 /
  有限长约 0.06 / 64-bit tag 约 0.075；任何引用必须写清所用 H 基。
- **M3A 嵌套 200+8 构造**：批末 PASS，**仅构造可行性**（两组固定种子图满秩、
  四环为零、girth 6），不等 FER/泄漏/效率改善。
- **M3B 配对合成**：批末 PASS；Stage-1 非 exact 由 84/240、138/240 降至
  10/240、15/240，最终失败 0/240；两实例分别报告、**不合并**，**仅合成**。
- **M2-LB 合成 12 臂**：批末已关闭但定位 retained-assumed（后端恒为
  `numpy-minsum-fallback (assumed)`），禁 promotion。
- **H0.1** scoped 提交 `051e3687`；**H0.2** 具名分支推送 + PR #1 OPEN。
  **S0.1-gate PASS**（decision-log:4861）；P1 Stage-1 批末
  `PASS_WITH_FINDINGS` 但无一臂全过三门，G-P1S1 授权已用完。
- **NB-LDPC GF32 BP iteration-cap（2026-10-01）**：主线程仅接受冻结合成 iid marginal-shape screen `NO_SUFFICIENT_SIGNAL`；192 对/384 BP，control/candidate exact-and-syndrome=146/146、Delta=0、positive graphs=0/6。独立 P6 向量级复核 PASS；批次授权已消耗。细节：`docs/research_cycles/NBLDPC-GF32-ITER-CAP-20261001/` 与 `workspace/gf32_itercap_eb0eb231/`；无 FER/路线/真实信道/跨批次结论。

- **NB-LDPC GF32 固定度类内行序（2026-10-01）**：主线程仅接受冻结合成 screen `NO_SUFFICIENT_SIGNAL`；192 对/384 BP，control/candidate exact-and-syndrome=152/148、Delta=-4、positive graphs=0/6。独立 R6 PASS；授权已消耗。细节：`docs/research_cycles/NBLDPC-GF32-ROW-ORDER-20261001/` 与 `workspace/gf32_roworder_44c394bc/`；不作路线/FER/真实信道/跨批次结论。

- **NB-LDPC GF32 common-paired 构造 canary（2026-10-01）**：主线程仅接受固定六组构造协议 `CONSTRUCTION_FEASIBLE`；14 次构造调用、13 个实际矩阵，独立 C4 PASS（rank 52、连通、profile/maps/common-seed）。`2026093905` 的候选 j0 放置失败被保留，j1 以共同 seed `2560859716` 选中；无 labels/BP/OSD/性能测试。细节：`docs/research_cycles/NBLDPC-GF32-CONSTRUCTION-CANARY-20261001/` 与 `workspace/gf32_construct_a9a18abe/`。这不代表随机图性能或路线结论；授权已消耗。

### 2026-10-01 — NB-LDPC GF32 admitted-matrix degree-profile screen

Main accepts batch `a9352bc1-ae56-443b-ae93-9dcfa85d4229` only as `NO_SUFFICIENT_SIGNAL` for the frozen common-admission profile bundle: 192 pairs/384 BP, control/candidate exact-and-own-syndrome=144/1, Delta=-143, positive graphs=0/6. Independent A5 PASS checked source/profile/deep-H lineage, all saved vector outcomes and accounting. The one-shot grant is consumed. Details: `docs/research_cycles/NBLDPC-GF32-DEGREE-ADMITTED-20261001/` and `workspace/gf32_degree_admitted_a9352bc1/`. This is not a degree-only causal result or NB-LDPC route rejection; no FER/`f_eff`/SKR, real-channel, qualification, publication, or cross-batch conclusion.

- **NB-LDPC GF32 endpoint ablation（2026-10-01）**：主线程接受同一批 192 个样本上的 DV3 constructor/deep 固定端点对照为 `COMPLETE_DESCRIPTIVE_ONLY`；192 对/384 次，exact-and-own-syndrome=1/1、Delta=0，配对 both/constructor-only/deep-only/neither=1/0/0/191；仅 graph 2026093906 有一对两臂共同成功。独立 A4 PASS；这不是标签因果归因、新 holdout 或路线结论。授权已消耗。结果/审查：`docs/research_cycles/NBLDPC-GF32-ENDPOINT-ABLATION-20261001/`；机器根：`workspace/gf32_endpoint_67ca7191/`。最终 wall/RSS checkpoint 在首轮 artifacts 写入后；末尾状态写入不递归计时。

- **NB-LDPC GF32 固定 DV2 check-graph census（2026-10-01）**：主线程接受六张固定图的 `DESCRIPTIVE_STRUCTURE_ONLY` 结果；λ₂=0.330706–0.379884，Fiedler sweep φ=`9/32, 8/31, 1/4, 35/127, 8/31, 35/127`，无退化标记。独立 C4 `PASS_WITH_FINDING`；RSS 原始 `ru_maxrss` 单位后验更正为 KiB，最大值 33,072 KiB=33,865,728 B（32.296875 MiB），低于 1 GiB；原运行时 guard 单位错误，不能称其正确执行了字节门。代码已修复，未重跑，原 manifest/census 不变。无译码、码距、FER、因果或路线结论。记录：`docs/research_cycles/NBLDPC-GF32-GLOBAL-CENSUS-20261001/`；机器根：`workspace/gf32_global_f4a0ff0d/`。

- **NB-LDPC GF32 soft-prior rescue（2026-10-01）**：独立 S4 PASS，主线程接受固定六图/PMF/BP90、192 fresh pairs 的有限合成描述：control155/candidate167、Delta=+12、六图差值+5/+1/+2/+1/+2/+1、valid-wrong0/0。冻结分类仍为 CONTROL_RANGE_UNINFORMATIVE（155>153），不能提升为机制门通过。物理414calls；control/candidate迭代4519/23591、call-wall27.92505/145.03111s；首轮写盘checkpoint145.379914s、高水位RSS138113024B。undetected NOT_MEASURED/verification NOT_IMPLEMENTED；无FER/f_eff/SKR、因果、路线或吞吐结论。批次UUID31dca97b-808c-4205-ac01-7c5ab7b9e9b5，workspace/gf32_softprior_31dca97b/；细节docs/research_cycles/NBLDPC-GF32-SOFT-PRIOR-RESCUE-20261001/。一次授权已消耗。

- **NB-LDPC GF32 独立 soft-prior replica（实际2026-10-02，冻结ID20261001）**：独立R4 PASS，主线程接受仅本固定六图/PMF/BP90/192fresh frames的 MECHANISM_SIGNAL：C142/K156/Delta14，六图+3/+3/+2/+3/+1/+2，valid-wrong0/0。调用492，迭代5461/31393，call-wall32.912581/188.752185s，checkpoint189.115647s，高水位RSS146219008B；额外恢复伴随明显译码成本。UUIDcbe151fe-25f7-4990-8895-858091467e2b，workspace/gf32_softprior_replica_cbe151fe/；记录docs/research_cycles/NBLDPC-GF32-SOFT-PRIOR-REPLICA-20261001/。不提升首批CONTROL_RANGE_UNINFORMATIVE、不并表/汇总分母；无真实数据/N2048/n256/FER/f_eff/SKR/资格/安全/路线/吞吐结论。一次授权已消耗，无第三次复现。

## 4. 未接受或已停止（本节任一条均不得引用为正面结论）

- **M2 真实比较**：会计纠正 T0–T4 已完成并接受——接受对象仅为
  存量披露算术 + 诚实标签（T2：12/12 逐位精确；T3：PASS_WITH_FINDINGS
  零阻塞；T4 用户原话「可以接受这些」2026-09-27）。主线程科学接受
  **WITHHELD** 不变，五个阻塞发现不变。终点交付物为一工作方法
  （NB-LDPC 真实帧实测）+ 两个负实现结果（HDC 真实 `exact_match`
  28,000 块全 0；Layered-Binary 36/28,000、0.13%，块 FER
  0.9963–0.9995、超帧成功全 0），任一基线均无可填比较列，
  其 `leak_EC` 及一切派生列均附 `void-no-correction`，
  永不进排名。另见本页 §5 D-5：LB 验证路径有效（系弱译码器
  非硬门），`void-stub-artifact` 不适用于 LB。结构注记：
  旧展示 f（`f_notag = 5m/(1024·H)`）公式内根本无泄漏项，
  只取 `(m, H)`，跨族相等系机械强制（1M/m=197 两臂同列
  1.20048829，实测泄漏差 2.64x），该列在结构上无法区分方法。
- **M2-HDC 合成**：批末 **FAIL**，仅作边界干净执行记录与 harness 缺陷展品。
- **M3C 真实 2M 两臂**：**STOP**——R1 COMPLETE（383/383，372 最终 u2 成功），
  R2 `INCOMPLETE-wall`（352 成功 / 7 失败 / 24 未知，无 383 帧 FER），
  故无两图决定、无 FER/泄漏/f/SKR 结论，不接受。
- **M3D**：R1 批 FAIL（运行时门未过），R2 按冻结包正确未跑；独立批末审查已存在
  （`docs/research_cycles/M3D-ITER250-SYNTH/BATCH_END_REVIEW.md`，
  裁决 `PASS_WITH_FINDINGS`，一条 BLOCKING B1 仅针对日志中已记录的假设级
  后果句，不针对机械门判定）。B1 阻断的宽泛否定与 M3C 后果已由
  decision-log:5078 撤回（supersession，原文逐字保留）。本批当前唯一许可的
  结论形式是审查员允许的狭窄机械陈述（逐字）："M3D-R1's single-run point
  estimate did not meet the preregistered 10% gate, so this batch provides
  no positive signal for the 250-cap; whether the cap could meet the gate on
  repeat, on the second graph, or on real frames is unresolved, and no M3C or
  throughput-work consequence follows from this batch alone." 任何更强的
  「降 cap 无用 / M3C 墙预算问题不是这样解决的」句均不得引用。

## 5. 已作决定与开放项

- **D-1（tag 验证单位）**：**DEFERRED**，非阻塞；tag 总数继续分列、
  单 tag 列保持反事实标注；待冻结协议规范裁定 headline 列。
  D1 tag-unit 分析 memo（`docs/research_cycles/V80-NBLDPC-JAN21/D1_TAG_UNIT_MEMO_20260927.md`）
  已存在，仅为分析，不授权任何事，不改变任何数字；D-1 仍 deferred。
- **D-2（HDC/LB 的 `f_eff`）**：**DROPPED**；重引入须新预注册的方法专属
  单位一致定义，NB 1024 符号超帧斜率永不得默示复用。
- **D-3（D2 规则）**：**D2 在 M2 退役**；M2 无有效输入，后继经 M0/P1 实测
  缺口路由；范围仅限 M2。
- **D-4（HD-Cascade 列）**：**选项 (iii)**——HDC 作为已记录的负实现结果，
  每个 HDC 数字附双 void 标注，披露列标注
  `exhausted assumed schedule on uncorrected blocks — not a method property`。
  选项 (ii)（接真 verifier、新根重跑）已考虑并否决：它只改 `undetected`
  标签，不改变 `exact_match`、`leak_EC`、FER 任一值。
- **D-5（Layered-Binary 列）**：**与 D-4 平行处理**——LB 真实帧仅纠正
  36/28,000 块（0.13%），其披露及一切派生列附 `void-no-correction`，
  作已记录的负实现结果；备选 (ii)（去 void 标签裸留披露数）已否决，
  因其诱发本变更旨在阻止的排名解读。并行授权只读溯源——不重译码、
  不新执行，仅搜三源 M2 根与邻近记录有无现存后端痕迹。
- **D-6（CHAN-QUALITY-SURVEY 信道表征批）**：**已执行、已接受**——两臂终态
  （Arm A：CQ-20a/b OK，CQ-20c/d 终态 REFUSED；Arm B：CQ-J21a/b/c 全 OK），
  零译码；独立批末审查已存在并裁决 `PASS_WITH_FINDINGS`（零阻断），主线程
  接受已记录（`docs/research_cycles/CHAN-QUALITY-SURVEY/INDEPENDENT_ACCEPTANCE.md`，
  2026-09-27），两条审查待办（N-9 措辞收敛、`RESULT.md` §2.3 已改写；
  N-5 完整 Rev-2 ceiling、`ARM_B_SUMMARY.md` 已替换）均已关闭。
  信道结论只许围栏形式：零观测到的跨面共错、单面翻转结构（三元组：
  非对角恰 0.0、popcount 仅 {0,1}、每次误差翻面数 1.0；约一百万对零双翻只
  排除高于约 1e-6 的多面率，低于探测限的罕见双翻未排除，「独立」一词须附
  该限定）；`ser` 0.2386–0.2543；legacy `0.098260` 在冻结链下未复现
  （同组 0.2461；已记录差异是配对规则与流水线，此外成因未确立，window
  明确不在其列）；五个已测采集中无已测得的更易工作点，未测组按在案理由
  不提供证据。读法变化（**仅信道结构发现，零纠正实测**）：
  Layered-Binary 基线由"不可用"改为"结构指示、但尚无合格译码器实现"，
  不改变其 `void-no-correction` 负实现定位，不产生任何方法结论。
- **管线现状（2026-09-29，新会话接手用；每条均为证据状态，非授权）**：
  Stage 0 **KILL — settled**（`workspace/s0_1bbe38ac/`，CQ-J21c f=1.3 名义 1875 vs
  1104，超 771 bit；五源名义均超约 690–772 bit；回退 f=1.56 总量 2233、超 1129 bit，
  均为 §16.2 verified-standing）——其正确范围是**冻结的
  十个独立逐面分配在该 `f` 网格与预算下不可行**，**不**排除联合编码或结构
  化分层设计；独立批末审查**已 PASS with comments**（`workspace/s0_1bbe38ac/BATCH_END_REVIEW.md`，
  S0-01…S0-08 全过、零阻断），KILL 由暂定转为 settled（decision-log 2026-09-29
  已登记）；**无 Stage-1 许可**。联合编码的成本基准**已执行但误算**（executed-but-miscounted，2026-09-28 补记：`docs/research_cycles/JOINT-PRICING/PREREG_AND_AUTH.md` §17 确认 joint ceil 即含 tag 总数，`M + 64` 比较将每格超额多算恰 64 bit；修正后名义总量 1100 vs 1104、余约 4 bit，`+20%` 回退列 1319、超 215 bit；原 §5.2 KILL 撤回为证据保留，修正数落 §5.3(a) **MARGINAL** 带）——**R2 重估已执行并登记**（裁决 MARGINAL per §5.3(a)、独立批末审查 `workspace/jp_46c7ab3c/BATCH_END_REVIEW.md` PASS with comments；4-bit 薄余量本身阻断任何超“起草设计包”的下游用途）——在把 MARGINAL 转成正式路线决定之前，该阶段一切数字**不得作为执行依据引用**。
  任何设计开支须等主线程对 MARGINAL 薄余量的处置决定先行；本页不授权任何重估或设计执行。
  Proxy 重标定（Packet A）终态 **INCOMPLETE**：授权修复后重跑在 240 个
  Stage-1 块未完成时撞墙（wall > 3600 s），无产物落盘（`PROXY_RESULT.json` /
  `PROXY_SUMMARY.md` 未写出）；任何继续（更大预算、更少帧、分段落盘）须
  新包 + 新授权，不得放宽重读本包。PROXY-RECAL-R2 分段重跑（`workspace/proxy_recal_r2_093499fb/`）
  终态 **INCOMPLETE at segment 0**：35/40 块落盘（idx 0..34，逐块 wall 均值 51.0 s /
  max 80.8 s，峰值 RSS 0.189 GiB），外层 timeout 1800 s 于 block idx=35 处 SIGTERM、
  exit 124（§9 规则 7 预算违例，归因译码成本，仅饱和假设、无结论）；留存行
  fails 35/35、undetected 0/35 **仅耐久证据、非结果**，§8 修复资格 **NONE**
  （译码成本撞墙不属基础设施修复），segments 1–5 未启动、无 assembly、无 §5 词；
  已登记 decision-log 2026-09-29；任何继续须新包 + 新授权。U1 探针已执行并触发 §5.2 条款：
  头部天花板约束一切结局——完美 u1 至多省约 24.6 bit/超帧（约 0.03 in f），
  故选项 F 作为改进路线关闭（诊断价值保留；执行已按 decision-log 本日 U1 条目记录，独立批末审查仍 pending，通过前 U1 数字不得作为执行依据引用）。
- 跨批次审计已闭环（2026-09-29，`docs/research_cycles/CROSS-BATCH-AUDIT-20260929/AUDIT.md`，decision-log 同日本轮条目）：C 轨 `STRUCTURALLY_INCOMPLETE_KILL`（R2 同 6×40/240 分区）、B 轨 v2 `CALIBRE-OK`（仅口径自洽）、B 轨第二步 `GAIN-UNTESTABLE-IN-CLASS`（仅本成本类/合成条件）；三批独立批末审查均 pass with comments，跨批次审计 pass with comments / Blocking None；判决树到达 B 轨终点——**下一步需用户决定新科学假设**（同 WALL 内解析界/细网格/深帧/SCL 四条路径成本可行但均属新假设，agent 不得自动发起）；A（更易信道）仍不推荐；本行仅为指针，数字以审计与批次根为准，**不得引用本页数字作为执行依据**。
  三个流传数字是**推导量、非测量**，引用必须带标注：**「2–4x」
  合成-真实倍数**在仓内无记录来源（仅方向已验：M0 真实 5 差/1 一致/0 好），
  只能作委托方给定量级；**逐面熵比**邻近已验值（10 面 Σh2/H ≈ 1.642、
  0–4 面子集约 1.55）存在，但「字母表所编码的五个面」精确子集定义未找到；
  **吞吐数**（≈366 sym/s vs 480–900x）是两个推导之比，其 b2f 输入在
  decision-log:4745 自身即标「derived, pending independent arithmetic
  review」。用其中任一而无标注即违规。
- B 轨五批判定词已闭环登记（2026-09-29，decision-log 同日三条：v1 STOP 包缺陷 → v2 `CALIBRE-OK` 仅口径自洽 → Gain `GAIN-UNTESTABLE-IN-CLASS` 仅本成本类/合成 → Scaling `SCALING-BOUND-EXCLUDES` 仅本代价类 → Residual `RESIDUAL-THINNER`；C 轨 `STRUCTURALLY_INCOMPLETE_KILL`；v2/Gain/Scaling/Residual/C 五批（v1 为记录态除外）+ CROSS-BATCH-AUDIT 与各批 T-4 均 pass with comments，Blocking None）；B 轨收敛读法（**本冻结定义/代价类内**治 +20% 回退需跨 N 增益 13.33%–17.13%、标度上界 10.24% 仍低门 0.031；合并读法，非任一批判定词，不作普遍物理不可能主张）；**下一步为 DECIDE 用户级裁决，材料已备齐**；A 轨仍不推荐；本行仅为指针，数字以 decision-log 与批次根为准，**不得引用本页数字作为执行依据**。

## 6. 活跃门（PASS 已注出处；未过 = 对应动作禁止）

| 门 | 状态 / 含义 |
|---|---|
| **S0.1-gate** | **PASS**（2026-09-22，decision-log:4861）→ P1 Stage-1 锚就绪 |
| **P3-gate** | **未过**：re-freeze v2 仍 PROPOSED，授权签字块 BLANK ⇒ **禁把合成 FER 当真实 FER** |
| **P4** | **FROZEN NOT GRANTED**：授权块空白 ⇒ **禁任何构造执行**；只产可行性证据 |
| **P5-gate** | **需独立冻结**：未冻结前不可启动 |
| **P6-gate** | **未量化**：吞吐缺口未量化 ⇒ 禁「真实场景可用」句 |

## 7. 禁止事项（全文有效）

1. **禁单点 `f_eff ≤ 1.3` 认证句**：N_req 超出 key-eligible 块数。
2. **禁 merge 姊妹线**：不把 `polar-mainline` / 姊妹 checkout 内容并入本线，
   也不向姊妹线分支推送；发布只走命名 formal-IR 分支 + PR，普通非强制 push。
3. **禁 `git add -A`**：只按 scoped manifest 提交。
4. **每个 HDC 与 Layered-Binary 数字必带 void 标注，永不进跨方法排名**；
   HDC `f_ec_actual` 约 9.8–10.2、LB 约 3.8–3.9 均不得读作方法优劣，
   不得填入任何比较列。
5. **禁 Layered-Binary 后端推断**：真实后端 unknown，在案缺失即缺失，
   不得以合成批或现装环境推断。
6. 本页与计划均不授权执行；每个 EXPLORE/DECIDE 包仍按
   AGENTS.md §1.2 / §10.3 独立授权与评审。
7. **禁把本批 SER 当方法结果**：CHAN-QUALITY-SURVEY 任一 `ser` 数字
   均为零纠正信道表征，不得呈现为方法结果；`0.098260` 永不得当作测量引用。

## 8. 权威指针（细节按此顺序下钻）

1. **PLAN** — `docs/EXECUTION_PLAN_20260922.md`（排期、门禁、卫生轨）
2. **ROADMAP** — `docs/ROADMAP-20260921.md`（科学宏观路线 P0–P6、DECISION）
3. **BASELINE** — `docs/V80_BASELINE_20260921.md`（冻结科学口径）
4. **cycle** — `docs/research_cycles/M0-REALFRAME/`、`M1-FINITE-LENGTH/`、
   `M2-REALCOMP/`、`M2-HDCASCADE-SYNTH/`、`M2-LAYEREDBIN-SYNTH/`、
   `M3A-NESTED-200P8/`、`M3B-NESTED-PAIRED/`、`M3C-REAL-U2-2M/`、
   `M3D-ITER250-SYNTH/`（专题证据与 log）
5. **M2 会计 OpenSpec** — `openspec/changes/m2real-accounting-correction/`
  （MAC-1..9，design §1..§12，`void-stub-artifact` / `void-no-correction`）
6. **HDC 批末审查** — `docs/research_cycles/M2-HDCASCADE-SYNTH/BATCH_END_REVIEW.md`
  （FAIL）；**M3D 包与 Pre-EXECUTE** —
   `docs/research_cycles/M3D-ITER250-SYNTH/`

**冲突规则**：**科学口径以 ROADMAP / V80_BASELINE 为科学权威**；排期与卫生动作以
PLAN 为准；README / HANDOFF 状态段、**旧状态页与探针历史措辞仅作历史指针，不得
重定路线**（重定路线只能经主线程 + ROADMAP / V80_BASELINE 修订）。本页与上述任一
权威冲突时，一律以 ROADMAP / V80_BASELINE 为准。

**NB-LDPC GF32 MRB EXPLORE**：原批次 `ebbbe5c2` 已完成但其 `summary.json` 身份字段错误，不能单独引用；更正权威 `e1d549f7` 是对同一 192 对试验的存档行重聚合，屏幕结论 `NO_SUFFICIENT_SIGNAL`（149/149，Δ=0；43 个候选救援均为 syndrome-valid wrong）。见 `docs/research_cycles/NBLDPC-GF32-MRB-REAGGREGATE-20261001/RESULT.md`；不产生 FER/路线/因果主张。两个批次均已关闭，本条不授予重跑。

## NB-LDPC GF32 MRB top-6 — 2026-10-01

Batch `df44e589` is closed/main-accepted only as `NO_SUFFICIENT_SIGNAL` for its frozen synthetic comparison: 151/151, Delta=0, positive graphs=0/6. Independent P7 PASS; the grant is consumed. See `docs/research_cycles/NBLDPC-GF32-MRB-TOP6-20261001/RESULT.md` and `INDEPENDENT_ACCEPTANCE.md`. No route, FER/f_eff/SKR, or cross-batch claim; no rerun or extension is authorized.

## NB-LDPC GF32 MRB order-1 reachability — 2026-10-01

Batch `c4fab9ba` is closed/main-accepted only as a finite synthetic MRB-basis reachability diagnostic. Independent `faithful_scope` recomputed the 192 NPZ vectors/permutations/RREFs/distances/reconstructions. Counts: raw exact D0=146; syndrome-fail=46, all D_free>=2; D1=0; syndrome-valid-wrong=0. Per graph exact/fail: 26/6, 23/9, 24/8, 25/7, 22/10, 26/6. This bounds only the tested frame-specific MRB bases; no global code/decoder or route conclusion follows. Disclosure=49920 bits; wall=89.9558 s (terminal summary/manifest/log excluded), max arm=0.5948 s, sampled max RSS=121819136 B/795 checkpoints, NPZ=6402852 B, resource markers/violations=0. Verification=NOT_IMPLEMENTED; undetected=NOT_MEASURED. See `docs/research_cycles/NBLDPC-GF32-MRB-REACHABILITY-20261001/RESULT.md` and `INDEPENDENT_ACCEPTANCE.md`. No FER/f_eff/SKR/throughput/qualification/publication or cross-batch claim. This batch authorization is consumed; this closeout creates no additional execution authority.

## NB-LDPC GF32 degree-profile construction attempt — 2026-10-01

Batch `8c881d42` is main-accepted only as `INCOMPLETE`. Nine constructor matrices were admitted at rank 52; candidate seed `2026093905` failed placement at variable 127/socket 2. No labels, pairs, or decodes occurred, so the performance screen was not reached. The recorded integrity counter 1 is solely the construction/admission STOP; resource/auth violations are 0. See `docs/research_cycles/NBLDPC-GF32-DEGREE-PROFILE-20261001/RESULT.md` and `INDEPENDENT_ACCEPTANCE.md`. No route or performance conclusion; grant consumed, no rerun or seed replacement.


