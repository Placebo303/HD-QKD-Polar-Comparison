# CROSS-BATCH-AUDIT-20260929

## Provenance

- 来源：主线程转录 reviewer-go 返回的跨批次只读审计原文，逐字落盘；未重新物化、未改写任何判定或措辞。
- 审计范围：`PROXY-NONSTATIONARY-FAITHFULNESS`（C 轨）、`N2048-BUDGET-RECALC` v2（B 轨第一步）、`N2048-GAIN-SWEEP`（B 轨第二步）三批的「发现 → 判定词 → 主线程决策」链，及围栏继承、缺陷处置、成本纪律、过度声称排查。**未重跑任何已封存批次的执行**，仅算术重推导。
- 审计分支 / HEAD：`formal-ir-v72p1-addendum-clean` / `23183c73`（只读，未改文件、未 commit/push）。
- 主线程采纳的更正（2026-09-29，处置 N-C1）：此前对外表述「B 轨第三步需新成本类」**措辞过强，作废**。更正为：**B 轨第二步在本冻结定义内耗尽**；任何复检需新包 + 新授权，且须论证科学输入变更为何可能跨越 0.09 鸿沟；若新包仍在 1200 s 内，则属**方法假设变更**而非成本类升级。审计已列出同 WALL 内成本可行的替代路径（细网格 0.01 ≈145 s、深帧 3000 ≈178 s / 30000 ≈696 s、SCL/DE 优化集 ≈166 s、解析界秒级），但均属**新科学假设**，不得由 agent 自动发起。N-C2 的步数口径一并更正为 **>2 步**（非 >3 步）。本采纳不改变任何数值结论。

---

## reviewer-go 返回原文（逐字转写）

Verdict: pass with comments

Blocking Issues:
- 无。本轮三批的机械判定词→主线程5决策链经独立重算全部成立，无翻转词级的推理错误，无越权自动推进，无过度声称落盘。C-KILL / CALIBRE-OK / GAIN-UNTESTABLE-IN-CLASS 三词均由本批证据按冻结规则唯一推出；B轨停止（不自动开第三步、不切A）正确。

Non-Blocking Suggestions:
- N-C1（第5条决策措辞过强，须更正）："g_req下沿在本成本类内不可达⇒B轨第三步需新成本类"方向正确但"需新成本类"不严密。穷尽同WALL=1200s内替代路径后，真正耗尽的是"本冻结定义"（BSC+H-1/H-5+BHAT DESIGN_P 0.25+SC+0.05网格+300帧+FER*1e-3），任何复检都需新包+新授权并论证跨越0.09鸿沟的机制；但新包未必需要更高WALL（见核心结论）。建议改述为："B轨第二步在本冻结定义内耗尽；任何复检需新包+新授权，且须论证科学输入变更为何可能跨越0.09鸿沟；若新包仍在1200s内则是方法假设变更而非成本类升级；不得由agent自动发起。"
- N-C2（N4步数口径小 imprecise）: Gain审查N4称"noise cannot bridge, would need >3 steps"。独立重算 gap=0.133333-0.041667=0.091667，单步量子0.05/1.2≈0.0417，0.0917/0.0417≈2.2步，故应为">2步"，非">3步"。结论不变（1步隐藏0.0834<0.1333），仅措辞修正；引用时仍须带"empirical 0/300 first-pass, never true-FER proof"。
- N-C3（AC-G07作用域澄清）: Gain根机器件（TABLE/PRED/PROV/VERDICT/RUN_LOG/gain218.py/test）19-pattern零命中已验；BATCH_END_REVIEW.md内CALIBRE-OK/51.0/0.098260/direct/double出现系审查 enforcement 的元讨论（说明禁词与围栏），不计入AC-G07操作件 sweeping。建议后续包明示"AC-G07 sweep scope = operator artifacts pre-review；review doc meta-mention exempt"。
- N-C4（v1/AMENDMENT状态措辞）: AMENDMENT-01.md首行自称PROPOSAL，与v2 §supersession"superseded-before-execution记录状态"一致（未生效即归档），非矛盾。但引用时一律以v2 disposition为准："v1+AMENDMENT retained unmodified, not citable as current authority"。
- N-C5（TABLE缺陷长期携带）: N1处置（accept as-is + 禁读f_star/g_synth列 + 一律由f_scan/fer_emp重算 + 干净TABLE需新窄包）恰当，不低估。但缺陷TABLE将永久存于该批根，属footgun；任何下游引用必须逐字携带N1限定，promotion须排除该列。
- N-C6（C轨授权形式偏差已追认）: C轨§14要求"点名packet+§8上限verbatim"，实际D-3 verbatim「那就开始C，持续推进」未点名、未含三上限，靠主线程解释桥接。主线程已追认并担责，实质边界（冻结范围/预算/零真实数据/零decoder）未破；后续包已放宽为"main-thread explanation+budget restatement suffices"（v2/GAIN均按此执行）。仅限EXPLORE低风险比例审查原则下接受，不得引为DECIDE先例。
- N-C7（时间戳粒度）: C轨T-3a与T-2同秒、Gain PRED<TABLE<T-VERDICT以mtime+文件序+代码序（sampler 295-309先于312-314；gain 205-211 refuse-without-PRED）保证先算后测，成立；建议未来包要求单调perf_counter/纳秒戳。

Checklist:
- [x] Matches OpenSpec spec（此处spec=三冻结包：C 252行 / v2 245行 / GAIN 191行；公式/门/阈值/列集/词集逐项对齐）
- [x] Tests pass（C 12/12；v2 10/10；GAIN 9/9，均有独立重算背书；本审计仅算术重推导，未重跑批次执行）
- [x] No scope creep（各一批一新根；src/experiments/tools/results/outputs_comparison未写；无commit/push；无真实数据接触；无DECIDE起草）
- [ ] docs/decision-log.md or docs/troubleshooting.md needs update? —— 否。三批均为EXPLORE合成/算术门，无新可复用 failure mode 或 durable decision；引用带限定即可。工作树M/docs系sibling遗留，非本批写入。

## 总体评估：发现→判定词→决策链是否成立

三批链条成立，无blocking级推理错误。

1. **C轨 STRUCTURALLY_INCOMPLETE_KILL（K-C2）**：`C_req=min(1800/40,10800/240)=min(45,45)=45`独立重算成立，双帽同束（段帽与总帽恰同为45，结构性非凑数）。`U_assume(0)=51.0>45`且`240×51.0=12240>10800`成立；U为既有描述性标签（未新测），α=0已最宽容。K-C1三分支确全不触发（control 0.0311/-0.00253/0.7509全静；drift z_med 7.11破带故all_quiet=False；Δ0.02≫1e-6）；FLAG=O_err(False)∧O_cost(False)=False。优先级C1>C2>C3 honored，C2中选无覆盖C1。词正确，措辞"该6×40/240分区结构性不可完成"未扩为代理不可行/信道平稳。
2. **B轨v1 STOP→Scheme C v2**：B-1/B-2定性为包缺陷正确。结构证明独立成立：`direct(t)-double=delta_pure+(128-t)`，`delta_pure∈{-1,0}`恒成立，故T1恒{+63,+64}、T2恒{-1,0}，与H/f取值无关，不存在换H/f通过的第二路径。实现与手向量与包字面一致，无工程缺陷。Scheme C（退役混合差→分解lineage+全局tag-free lemma+gap_tag非门列；K-B1/B2/B3准则阈值 provenance 不变；≤64松弛禁令）是唯一合规路径，repair额度不适用判断正确。
3. **B轨v2 CALIBRE-OK**：仅在K-B1（R-A-T1/T2 survive，R-B-T1死）→K-B2（H-5 f0 D_nom T1/T2/leak三臂恒等+8，符号一致非负；全网格f0 102/24/82/14/8、f1 -320/-412/-344/-424/-430同-t恒等已重算）→K-B3（`g_req=1-2080/L2048(f1,H)`五源0.133333/0.165329/0.141914/0.169329/0.171314，区间[13.33%,17.13%]派生算术非测量）全过后发出，顺序与短路 honored。全局引理10对delta_pure∈{-1,0}独立重算 bit-identical。词后仅作阈值许可（AC-G07禁词），未读作可行/通过/增益。
4. **B轨第二步 GAIN-UNTESTABLE-IN-CLASS**：仅由`g_synth(H-1)=1-1.15/1.2=0.041667<0.133333`（gap 0.0917）经K-G1 pass（125.76≤1200先算后测）+K-G2 pass（p_s/seed/constructor/FER*冻结无retune，DESIGN_P 0.25与p_s 0.2375/0.2593数值 distinct，g_synth仅自decoder counts）推出。非TESTABLE（需≥0.1333）、非CONTEXT-ONLY（无K-G2 breach）、非KILL（双H均达FER*）、非STOP。f*最小性四组fer单调+首过点已验（H-1 1024首1.20 [1.15处4/300]、2048首1.15、H-5双1.15）。
5. **主线程5决策**：(1)三向对比C首选/A不推荐（A换问题、无消费者、需ser≤0.18而五采集0.2386-0.2543无此源）支撑成立；(2)C KILL→B（预公开树）已依树执行；(3)v1 STOP判包缺陷非工程缺陷→Scheme C v2正确；(4)v2 CALIBRE-OK仅口径自洽不许可设计正确；(5)B终点停、不自动推进正确，唯"需新成本类"措辞过强（见N-C1与核心结论）。

## 核心结论：B轨是否真封闭、有无更低成本替代路径（本次审计核心）

**本冻结定义内封闭，包内无剩余路径；任何复检需新包+新授权；但"必须新成本类"不成立——多个同WALL内方法假设变更在成本上可行，缺的是科学机制论证与授权，而非WALL。**

冻结定义=`BSC(p_s H-1/H-5)+Bhattacharyya DESIGN_P 0.25+LLR-SC+0.05网格+300帧+FER*≤1e-3+WALL1200`。包内：网格/F_per/constructor/FER*全冻结，§5单repair已耗于`KeyError:'t_pred'`，第二修未授权，TABLE缺陷不得静默重进。故同包内无合法更低成本路径。

同WALL=1200s内成本核算（`T_pred=G_pts×F_per×t_frame_upper+120`，t_frame_upper=0.0008）：
- **换H点**：H-1已最松（0.1333），H-2…H-5更高（0.14-0.17），无更低门。封闭。
- **细网格0.01**：G_pts 24→104，T_pred≈145s<1200s，同WALL可行。但连续界：f*_1024∈(1.15,1.20]、f*_2048∈(1.10,1.15]→max g≈1-1.10/1.20≈0.083<0.1333；除非天花板截断（真f*_1024>1.20，≥1.327才达门，需+2.5步），细网格 alone 不能桥接0.09鸿沟。新包+授权才可试，非成本类升级。
- **深帧3000/30000**：24×3000×0.0008+120≈178s；24×30000×0.0008+120≈696s，均<1200s，同WALL可行。0/300分辨弱（95%上界~0.01，P(0|1e-3)≈0.74），深采样可能非对称翻转（1024上翻而2048不翻）理论上可扩g，但需≥2步非对称误差，新证据+新包才可裁决；当前0.09鸿沟覆盖±1步量化+典型噪声，不覆盖最坏非对称深采样翻转——引用必须带N4限定。
- **改构造器（DE优化集/SCL L=4-8/CRC）**：L=8时T_pred≈166s<1200s，同WALL可行。SCL同时改善双N，f比值效应不定，13%（需比值1.15，gap缩减80%）远超极化标度律预期（μ≈3.6-4时 doubling gap缩减~16%，对应g~0.027），但未被当前SC-only sweep证伪。属新科学假设，需新包，与WALL无关。
- **放松FER*至1e-2**：更便宜同WALL，但观测fer曲线在1e-2处g≈0（双N f*~1.15），不能达门。收紧至1e-4需深帧（仍可<1200s），效应不定，需新包。
- **解析界（DE/GA/有限长界）替代sweep**：成本秒级，远低于WALL。标度律同样预测达不到f比值13%，属佐证性新包而非推翻性路径；证据类型不同，需新包。
- **减范围（单H/少点）**：更便宜但不能增大g，成本已通过（3s/52s≪1200s），瓶颈是增益幅度非成本。无用。

故第5条"不自动推进"正确（预公开树无"UNTESTABLE→自动第三步"，且任何变更皆新科学输入）；唯须将理由从"需新成本类"修正为N-C1措辞。H-1 f*_1024居网格顶（1.20=max）天花板截断残留须随引（需+0.09即>2步才威胁门，已记录）。

## 围栏继承链

- **CALIBRE-OK**：Gain包§13围栏+AC-G07输出禁词正确继承，仅作阈值 provenance（§2 G-INT verbatim值+公式派生/tag-free/非测量标签），机器件零命中（TABLE/PRED/PROV/VERDICT/RUN_LOG/code/test全验）。BATCH_END_REVIEW提及系 enforcement 元讨论，非放行。
- **51.0s**：C轨始终descriptive（JSON `_descriptive`、log/driver `NOT performance`）；B轨未误用为单价/吞吐——Gain t_frame_upper来自no-write探针median 0.000378×2→0.0008（32帧RAM内），机器件`51.0`零命中已验。继承正确。
- **v1手向量**：v2 §9.3 + Gain §13永久禁引（≈+8 thin-surplus形单向量不得作D_nom/余量/可行信号），执行中确实未引用：v2 T-2全表重发20格+T3符号+不变性，AC-04/05重发；v2 test 2199系H-5 lemma illustration（delta_pure=-1）非禁向量；v2 log/GAIN根对v1根仅作"retained untouched"陈述，无结果引用。
- **v1与AMENDMENT-01权威性**：v2 supersession明确 sole authority=v2，v1(205行)+AMENDMENT(406行) record-only retained unmodified not citable；下游仅引B-1/B-2/B-3动机与disposition，不引阈值。AMENDMENT首行PROPOSAL与v2 disposition一致。继承正确。

## 过度声称排查（(a)-(e)，逐批D-1/D-2/D-3/日志/包）

- (a)名义余量当放行：无。+8恒等三臂从未作thin-surplus结论（v2 fence+review禁令）；JOINT 1100余4恒与1319超215双数字同引，无solo-nominal；C 51.0/12240从未作性能/吞吐。
- (b)理想乘法/派生算术当发现：无。斜率84-85/168-170、`2·1036+64=2136 vs 2208余72`、`1.2·2136=2563 vs 2208超355`、`g_req`区间、`g_synth`一律标derived/non-measurement/decoder-count derivation on synthetic frames。
- (c)context当判定输入：无。S_a/S_spread/U1~24.6在三批零门输入（grep零命中）；gap_tag/delta_pure在v2非门列（无阈值，code/test/CSV/VERDICT已验）；H-5上沿0.171314仅context，门仅下沿。
- (d)合成/代理与真实帧混比：无。三批零真实数据接触（无bundle/.ttbin/rows.json/parquet/(a,b)开读，import白名单+path-gate+rg已验）；C S-N6、GAIN §11(b)合成限定逐字携带。
- (e)单点外推：无。H-5 g=0.0仅context（量化解释N3）；control安静未引为真实信道；UNTESTABLE未引为N=2048不可行/B轨终止/增益不存在（fence已验）。

## 已知缺陷处置（N1/N3/N4/N5）

- **N1 TABLE f_star回显f_scan+g_synth空**：确认bug（gain218.py:243-244 `else f`应`else fstar`、`""`应per-H g；f_star集={0.95..1.2} echo，g_synth={''}）。VERDICT正确（自fer行独立重算一致）。单repair已耗于KeyError，第二修属二次repair包内未授权，拒绝自授正确。Accept as-is+引用限制（禁读该列，一律f_scan/fer_emp+首过规则重算）恰当，严重性未低估，前提是限定逐次携带；干净TABLE需新窄包。
- **N3 H-5 g=0.0**：1-1.15/1.15机械正确；双N同落1.15单步点，量化解释成立；即使+1隐藏步0.0834<0.1333，鸿沟覆盖。Context-only+网格量化限定恰当。
- **N4 0/300分辨**：冻结机械规则合规但弱（95%上界~0.01，P(0|1e-3)≈0.74，不证真FER≤1e-3）。"噪声不能桥接"在对称噪声下成立，非对称深翻转理论可能，需N4限定（empirical first-pass never true-proof）+步数更正为>2步。处置恰当，未低估。
- **N5 探针与sweep同SC**：非循环正确。§4定价探针本即同一SC实现；K-G2仅覆盖p_s/constructor/g_synth sourcing，不覆盖timing；timing耦合不 circularize gain。

## 决策树本身与成本纪律

- 预公开树"C KILL→B；B合成门KILL→全停回用户；不得自动切A"一致执行：C KILL→v2新包新授（非原包编辑）；v1 STOP→v2修订新授（非repair）；v2 OK→仅阈值许可；sweep UNTESTABLE→停，无自动第三步，无切A。无任何越权（无agent自授新授权、无真实/DECIDE/commit/push）。
- 成本纪律真正生效非纸面：C T-3a先于draws（文件序+代码序），零decoder白名单+assert+rg；Gain PRED先于TABLE（mtime 13:12:23<13:13:15+entry refuse-without-PRED），WALL1200+600s沉默线武装（timeout+内部guard+逐点落盘），repair单次 enforcement（拒第二修）。实际成本琐细（0.19s；3.05s/52s span）故cap未受压，但门结构上不可绕过。M3C 5280/A 3600零落盘/R2 1800 35/40三死亡围栏在Gain §2/§4冻结携带，未重测，正确。

## 仍存疑的开放问题

1. H-1 f*_1024居网格顶截断：真最优可能>1.20（0/300容许真FER达~1%），需+0.09（>2步）才威胁门；当前证据下稳健，但深采样非对称翻转未被排除——任何复检须新包。
2. 0/300统计分辨：同上，深帧同WALL可行，结论限于"经验首过"，非真FER证明。
3. 构造器泛化：结论限于Bhattacharyya DESIGN_P 0.25+SC；SCL/DE优化集是不同假设，未被本批证伪亦未被证实，需新包。
4. R2单价转述性：C K-C2依赖上游R2描述性51.0/80.8（未本包实测）；若上游修正需新包重算。
5. 授权形式：C轨弱档已追认；v2/GAIN宽松§14（解释+重述即足）仅限EXPLORE；DECIDE不得援引。

## 可以引用（须连带限定） / 不可以引用

可引用（每次必带限定，单句模板见D-4）：
- C："合成非平稳代理（N=383/R=500/paired/Binomial(1024,p)/Δ0 vs 0.02）control复现安静（z 0.031/r-0.0025/D 0.751）且drift以z 7.11破带具敏感性（K-C1全不触发），但在R2同6×40/240分区双帽1800/10800既有描述性U_mean 51.0（α=0最宽容）下51.0>45且12240>10800→STRUCTURALLY_INCOMPLETE_KILL(K-C2，该分区结构性不可完成，按三向结论路由B需新包新授）"+§11天花板。
- v2："v2 T-2同-t配对R-A-T1/T2 D_nom=+8bit（H-5 f0无增益基线）；全局tag-free lemma delta_pure∈{-1,0}（10对）；派生（非测量）g_req[13.33%,17.13%] tag-free LEAK作后sweep阈值输入；CALIBRE-OK=口径自洽+nominal符号一致非负+区间交付，仅许可后sweep阈值设定"+§11 verbatim；AC-05必带"H≈0.82-0.83窗口，H-1/H-3按各自比例理论判"。
- GAIN："N2048-GAIN-SWEEP（EXPLORE合成1200s类）：H-1 g_synth=0.0417（网格量化f*_1024=1.20[0/300@1.20;4/300@1.15] f*_2048=1.15[0/300] 6点步0.05 300帧/点 经验FER*首过 BSC(p H-1 0.2375/H-5 0.2593)+BHAT 0.25+LLR-SC K-G1 125.76≤1200 K-G2 pass）<0.133333⇒GAIN-UNTESTABLE-IN-CLASS；H-5 g=0.0仅context；TABLE f_star/g_synth列缺陷禁读，一律VERDICT+f_scan/fer_emp重算；0/300系经验首过非真FER证明。"

不可以引用：
- 任何FER/效率/泄漏/f/SKR/key/方法优劣/排名/合表/代理=真实信道/真实recal许可/吞吐性能读法；51.0作吞吐；80.8>45作独立门；240×51作10/240基线；control安静作真实信道结论；FLAG=False作诚实证；FAITHFUL（未得）作放行；v1单手向量作D_nom/余量/可行信号；+8作thin-surplus结论；g_req作测量/已达增益；CALIBRE-OK作N=2048可行/B轨通过/增益已得；UNTESTABLE作N=2048不可行/B轨终止/K-B3失败/增益不存在；g_synth作真实增益；H-5零作零增益证明；TABLE f_star列作f*；无合成+1200s类+网格/FER限定之裸引；0.098260作测量；void基线；单nominal MARGINAL；35/35趋势；已闭项重开。

## D-4文本（仅返回不落盘，主线程授权后另行落盘）

> # CROSS-BATCH AUDIT D-4 (PROXY-NONSTAT + N2048-BUDGET-RECALC v2 + N2048-GAIN-SWEEP)
> - Verdict: **pass with comments** (blocking none). 三词独立重算成立：C `STRUCTURALLY_INCOMPLETE_KILL(K-C2)`（45/51.0/12240前置算术，双帽同束，K-C1全不触发，FLAG False）；v2 `CALIBRE-OK`（K-B1→B2→B3顺序短路，D_nom+8三臂恒等，delta_pure∈{-1,0}，g_req[0.133333,0.171314]派生）；GAIN `GAIN-UNTESTABLE-IN-CLASS`（K-G1 125.76≤1200 pass；K-G2 pass；K-G3 0.041667<0.133333 fail，gap 0.0917）。
> - 主线程5决策支撑成立；第5条停止正确，唯"需新成本类"改述为"本冻结定义耗尽，复检需新包+新授权并论证跨0.09鸿沟机制；同WALL内细网格/深帧/换构造器/解析界成本上可行但属新假设，非成本类升级；不得自动推进"。
> - 围栏继承全PASS：CALIBRE-OK仅阈值许可（AC-G07机器件零命中）；51.0未误用（GAIN用探针0.000378×2）；v1手向量禁引且未引；v1/AMENDMENT record-only未作权威。
> - 缺陷处置：N1 accept as-is+禁读列（VERDICT正确，重算路径 intact，第二修拒授正确）；N3量化限定；N4经验首过限定（>2步更正）；N5非循环。严重性未低估，前提限定逐次携带。
> - 成本纪律生效（先算后测代码强制+WALL/600s guard+单repair enforcement），非纸面；时间戳粒度下批须纳秒/单调戳。
> - 可引/禁引按上节；开放问题：H-1顶截断、0/300分辨、构造器泛化、R2单价转述性。
> - Claim ceiling: 本审计为只读推理审计，未重跑已封存执行，未改文件，未commit；审计结论落盘需主线程另行授权。
