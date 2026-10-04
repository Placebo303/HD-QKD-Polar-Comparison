# HD-QKD 信息调和路线长期科学审查报告（修正版 v2，2026-08-23）

**审查人角色**：长期只读 scientific roadmap reviewer。
**本版状态**：取代同日对话版。相对 v1 的三处修订（均经用户独立核对确认）：
① 开放项 1 由「等待 A9 裁决」更新为「verifier-fix `3110cb0e` 已完成、等待 F-G1 独立复核与最终主控 ACCEPT/REJECT」；
② B1 NLL 单位修正（229–245 为每 n=1024 块的 raw posterior NLL 均值 ≈0.224–0.239 bits/symbol；更正文件 `docs/nbldpc-v32-main-verdict-unit-correction-20260823.md`）；
③ 路线改名 R1–R4 并将 V33 exact-V31-rate empirical-P ensemble DE 定为最高价值前置门（corrected matched finite-control 仅在 V33 全过后成为下一项高价值实验）。

**证据截止状态（2026-08-23 第二次更新，逐项只读核实）**：verifier-fix `3110cb0e` 之后 **F-G1 独立复核已 ACCEPT**；audit-correction 变更终态 `audit_corrected_rate_aligned_de_required`，已归档至 `openspec/changes/archive/2026-08-23-formal-nonbinary-ldpc-v32-operating-point-audit-correction/`（closeout 提交 d76a55c3 + b1171cc9）。V32 科学归因仍为 `bridge_inconclusive`（main-review 层），无 qualification/promotion。**V33 已注册为活动 OpenSpec 变更目录，四件套候选草案（proposal/design/tasks/spec）均已写入并标注 DRAFT_PENDING_FREEZE_REVIEW；独立 freeze review 未完成、判敛公式待定稿，DE 计算本体仍未授权执行。**

---

## 一、V1–V32 方法演化图（按七层压缩）

### 层 1：channel/model evidence

| 阶段 | 内容 | 结果 |
|---|---|---|
| V1–V24 主线 | QSC p=.20/.30 对称先验、V17 independent-plane product、折叠小 q 结构化模型 | 工作假设；后被证明严重失配 |
| V13-D01 | 错误为孤立单符号扰动（run 长 ≤3），99.3% 差分落在 [0,128)，MSB→LSB 单调位面失配 | 经验观测 |
| **V25** | 三源 type2_2026-01-21 经验信道：SER 0.2398/0.2545/0.2557；误差 ∈{−1,0,+1}、方向随 delay 符号翻转且时间稳定；C03/C04/C05 holdout NLL≈0.807–0.828 bits/symbol 远优于 QSC(3.20–3.35) 与 V17 product(3.32–3.50)；chain-rule 闭合 ≤5e-9 | `pass_ready_for_de_change`，独立 verifier ok |

**层状态：completed**（限定三源 train split 与 source/delay 条件化口径）。模型层证据，不构成有限码可行性。

### 层 2：asymptotic ensemble evidence

负结果（冻结门一次执行的不可变证据）：V9A 零 eligible → STOP；V10 `failed_ensemble`（.2153/.1984/.3166/无 eligible）；V11 `failed_coupling`（三种 SC 几何全部负增益）；V14 结构化高码率 12 点全不收敛（熵地板 0.288–0.357 vs 收敛阈 0.01）；V17 `mechanism_unverified`（位面机制锚点 Δ=0.0075>0.005）；V18/V19–V23 plain 天花板 R≈0.60–0.63（f≈4.18）、短块 Bob-only FER 0.5625–0.625 触发停止门、single-edge 内核 135 候选 0 收敛。

正结果（窄范围）：V8 文献复现 PASS（proxy 0.0624 vs 发表 0.069，机制背书非 GF(1024) 证据）；**V26** A02（F03, GF32+GF32）在 f=1.3 下 30/30 收敛（λ={2:1}+harmonic-exact concentrated checks），A01 GF2 residual 层 f=1.3 失败/f=1.6 通过；V27R 四 block_len×三源全确认；V31-M1 m1=16 下 60/60 DE confirmation PASS（两个 n）。

**层状态：partial**。正证据绑定在 λ={2:1} 单一最弱族 + F03 因子化 + 经验信道 + true-predecessor-conditioned 的窄操作点；`d3_next_question.json` 明确禁止把 V26 f=1.3 外推到 V31 实际层率。

### 层 3：finite-budget evidence

V27R 冻结：m_total=floor((1.3·n·H−64)/5)，n=1024 → {200,206,208}，realized f∈[1.29409,1.29974]<1.3；64-bit tag 只计入总泄漏。审计 v2 D2 与 V31 manifest 交叉核对一致（|ΔH|≤2e-15）。

**层状态：completed（asymptotic-only 口径）**。

### 层 4：finite graph/code evidence——当前主战场

| 版本 | 构造 | 结果 |
|---|---|---|
| V28 | V27 分配物化 + Bob-only 顺序译码 | 工程 complete；noiseless 恢复仅为工程检查；诚实发现稀疏高码率码 + 均匀 QSC 先验受限 |
| V28R 审计 | 15 support groups、multiplicity 69、303 重复射影类、922 列、1107 个保证 weight-2 对 ⇒ **d_min≤2** | 构造级缺陷确证 |
| V29 | V28R 矩阵回溯 gate | 9 块后不可逆停止（exact/tag=1；1+91=92<95；prefix FER 8/9 **为观测前缀值、不是完整 FER**）→ `v29_finite_gate_fail` |
| V30R | projective-safe balanced/PEG 包 | M3 屏 0/6×2 包 → `finite_graph_fail` |
| V31 | m1=16 确定性重构双族 | PEG L2 秩亏（200→199、414→413）确定性拒绝；QC 全秩 projective-safe 但 L2 从不 syndrome 收敛：n=1024 完整负结果 300/300 exact/tag=0；n=2048 仅有 1M 的 14 块前缀（post-hoc 应急）→ `finite_graph_fail`、生命周期 **ARCHIVED_PARTIAL** |
| 对照：V13-R3 | 连通 girth-8 图替换退化图 | E01 64/64、A01 128/128、A02 256/256——但为 f≈12 低效率操作点 + 旧池/legacy 数据，不可迁移 |

**层状态：negative（有界）**。三个独立构造族在同一效率操作点一致失败且失败模式一致；明确**不是 NB-LDPC 全局失败**。

### 层 5：decoder evidence

FFT-QSPA 工程验证（brute-force 一致性 maxerr≈1e-17、fail-closed、B0 噪声端到端 6/6）。科学归因 **unverified**：V32 因 B1 生成律与经验 posterior 失配（Q 质量 23.9–25.5% 落在 P 零格，full E_Q[−log P]=∞；**B1 raw posterior NLL mean ≈229–245 bits per n=1024 block，即约 0.224–0.239 bits/symbol**，对参考条件熵 ≈0.80–0.83 bits/symbol；60/60 主动发散），主评审否决 `finite_graph_decoder_mismatch` 归因，终态降级 **`bridge_inconclusive`（main-review 层）**。有效残余信号：B3/B4 改善但不达 syndrome（≈250→≈179），更像 trapping/消息传递天花板；B2 的 1024 是 not-run 哨兵。

**层状态：engineering completed / scientific attribution unverified**。

### 层 6：real-data qualification

| 方法 | 状态 | 域 |
|---|---|---|
| binary LDPC v5 | **promoted，384/384** | 旧 10 dB Type-II 捕获，q=1024 Gray 256-symbol bw120/180/200；v4 的 16dB/10dB-v2 最严层 125/128 为保留非提升失败 |
| cascade_formal_v1 | **promoted**（synthetic 32/32×2 + real 60/60） | 锁定域 d=1024、64 symbol、bw120、SER [0.20,0.30) |
| NB-LDPC | **从未 qualification/promotion** | 最高历史状态：V13-R3 `ready_for_fresh_confirmation`（回溯）+ legacy drift audit 188/192、全量 8284/8412；fresh 通道被 intake 拒绝/drift 门阻断 |
| Polar baseline | frozen baseline | frame-identical 比较从未进行 |

**层状态：两条非 NB 方法 completed（各自锁定域）；NB 线 unverified**。

### 层 7：system-level release

无系统级发布。`docs/CURRENT_MAINLINE.md` 定义 Route A actual-IR finite-key 报告线；comparison_bench 外包裹层存在；push 待授权。

**层状态：not started（NB）/ 定义完成（报告线）**。

---

## 二、瓶颈定位（按证据强度排序）

1. **有限图/码转换层**：三个独立构造族一致失败，唯一通过对照是 B0 噪声 plumbing。
2. **系综族贫弱**：唯一渐近通过的族是 λ={2:1}；所有更丰富族的搜索全线失败；degree-2 有限距离性质差与 V28R d_min≤2 缺陷互证。
3. **层间分配失衡（部分成立）**：L1 泄漏/需求比 3.0444–3.2176（过配），L2 仅 1.15665–1.16185（薄边际）；总纯 syndrome gap +179.7373/+184.6204/+187.4558 bits（≈18% 余量）。分配是否构成渐近阻断正是 V33 要回答的问题。
4. **有限长度边际**：n=1024 不确定度 ≈820–853 bits 对 1000–1040 parity bits。
5. **decoder**（悬而未决）：调度/阻尼/EMS 在该操作点未测。
6. **GF 边标签**：必要非充分（V28R 证明可单独摧毁 d_min；修好后仍失败）。
7. **信道失配**：模型层已解决（V25）；残余为操作性风险（V32-B1 事故教训：合成对照必须从经验联合采样）。
8. **验证数据集**：单日三源、无跨日外部效度、fresh acquisition 无数据源——阻塞所有最终证据层级。

---

## 三、四条未来路线（新命名 R1–R4）

> 命名注记：为避免与本仓库历史 Route A（bit-plane 接口诊断）、Route B（v18 folded-DE 效率线）、Route C/D（见 `route-b-c-d-next-steps-plan-20260819.md`）混淆，本报告路线统一改用 **R1–R4**：
> - **R1 = matched empirical-P NB-LDPC**
> - **R2 = allocation/factorization redesign**
> - **R3 = binary-MLC / NB-Polar**
> - **R4 = HD-Cascade reference**

### R1：matched empirical-P NB-LDPC

- **前置条件（按序）**：
  1. **V33 exact-V31-rate empirical-P ensemble DE 全部通过**（这是当前不可跳过的最高价值前置门——若渐近层在该精确操作点不收敛，一切有限码工作无意义）；
  2. corrected matched finite-control 臂（合成样本从 V25 经验联合抽取、oracle-L1、V31 QC packet 不动）；
  3. 若继续有限码，需超出 λ={2:1} 的系综族先行 DE 通过。
- **最小实验**：V33 门之后的 corrected matched-control（20 块/源×3）：≥19/20 ⇒ 图+decoder 可用，瓶颈转向真实误差结构/有限余量；仍 0 ⇒ 在「DE 渐近通过」与「任何注入误差条件全灭」并立下，finite-conversion 层被强证伪。
- **最强停止条件**：control 失败 **且** 后续 ≥2 个新图族在 DE-PASS 后仍 finite-fail → 宣告需范式变更（protograph/MET/lifting），不再做矩阵微调。
- **失败退出**：冻结负结果，力量转 R3/R4；V13-R3 候选保留为唯一已验证 NB 调和器等 fresh 数据。
- **最终真实证据**：fresh acquisition 上预注册回溯→fresh 门（每源 ≥100 块 exact/tag ≥95%、false_accept=0、独立 replay）。

### R2：allocation/factorization redesign

- **前置条件**：显式联合优化判据（min-max 层 f subject to 各层 DE 收敛）；V25-M3 五个因子化族中仅 F01/F03 进过 DE，F02/F04/F05 未测。
- **最小实验**：纯 DE 可行域扫描（F02/F04/F05 × m1/m2 网格、总 f≤1.3、三源），输出可行区域图。零有限码零 decoder。必须预注册网格（V11 66.7h 教训）。
- **最强停止条件**：不存在任何（族，split）使全部层收敛于总 f≤1.3 ⇒ 绑定约束是系综族而非 split，并入 R1 前置或关闭。
- **失败退出**：可行域存在但有限 pilot 失败 → 回 R1 归因流程；空 → 转 R3。
- **成本注记**：参照 V26 实测（screen≈44s+confirm≈112s）与 V31 M1 预算，廉价高信息。

### R3：binary-MLC / NB-Polar

- **前置条件**：① 十比特链逐位级链式熵 H(U_j|B,Û_<j) 算术（审计 D2 仅覆盖两层 F03 口径）；② Polar 可靠序必须在经验信道下重新合成（冻结 baseline 序绑定其自身信道假设，**不可直接复用**）；③ plane_error_channel 机制对新池重校准。
- **最小实验**：P0a 逐位级纯算术可行性（复用审计 D2 方法论扩展到 bit 级）；P0b 极小 n 合成 soft-interface smoke（缺指标冻结，见第四节）。
- **最强停止条件**：某位级要求可用二元 constructions 无法可靠译码的率且该级 asymptotic DE 也失败；或 smoke 显示不可恢复误差放大。
- **关键红线**：Law A 名义可行只说明 NB-Polar 的「立即信息论否决条件」（总量需求>预算）**尚未触发**，**不证明 NB-Polar 可行**——两层 D2 结论不得被引用为对 R3 的支持。
- **失败退出**：保持 concept-only；不阻塞 R1/R4。
- **最终真实证据**：promoted-domain 风格 fresh real 确认 + method-specific leakage 分解的可比报告。

### R4：HD-Cascade reference

- **前置条件**：无硬阻塞（cascade_formal_v1 已 promoted）；缺口是帧几何适配（64-symbol/bw120 vs type2 204800ps 帧）与交互轮次记账契约。
- **最小实验**：不变方法在 V25 冻结 validation blocks 同一误差实现上跑正式 Cascade，产出可比 leakage/runtime/FER 三元组。
- **最强停止条件**：声明交互/时延预算内无法在 SER≈0.25 完成 → 该域 non-promotion，保留难度锚点。
- **失败退出**：无需退出——Cascade 本就是系统级兜底；NB 路线不依赖它。
- **最终真实证据**：fresh real 帧 verified_success + universal2 tag 记账 + 独立 verify。

---

## 四、workspace V33 草案与 NB-Polar concept 审查（维持 v1 结论 + 状态更新）

**V33 草案可直接转入 OpenSpec**：冻结层率表（与 registry 一致，经独立核对确认）；`not_fixed_packet_de=true` 范围限定；三条机械停止门框架；执行边界纪律。

**表述不够精确处**：① 系综未定义（λ/ρ 族绑定缺失）；② 相对 V31-M1 的增量未声明（应标注为 V32 归因否决后的独立复现）；③ 「数值不稳定」缺冻结判据；④ 「R1–R7 绑定集」悬空引用。

**缺失 pre-registration 字段**：DE 内核哈希绑定；seeds/n_samples/max_iter/tol/streak；资源上限；输出根路径；verifier 计划；完整终态集；claim-boundary 措辞；A9/F-G1 裁决挂接。

**NB-Polar concept 可直接转入 OpenSpec**：P0 两步结构；泄漏双口径分列；adapter 复用清单与 sibling 边界。
**不够精确处**：① 极化序「可复用」不成立；② 「hard decision + 置信度」接口不足（需 P(U_i|B,Û_<i) 条件后验）；③ smoke 无指标；④ §7 否决条件已被 Law A 算术部分预答（两层口径名义可行），其真实增量只在十比特逐位级分解。
**缺失字段**：seeds/n/成功判据/输出根/terminal 集/forbidden 清单/资源界/claim boundary。

---

## 五、12 个月路线图与决策树（按 V33-first 重排）

### 决策树

```
N0  F-G1 独立复核 + 最终主控 ACCEPT/REJECT（audit-correction 变更）
    【已完成 2026-08-23：ACCEPT；终态 audit_corrected_rate_aligned_de_required；
      变更已归档（d76a55c3 + b1171cc9）。V32 归因维持 bridge_inconclusive。】
 └─ 已通过 → N1

N1  V33 exact-V31-rate empirical-P ensemble DE（最高价值不可跳过前置门）
 ├─ 任一源任一层不收敛 → rate_allocation_or_ensemble_fail
 │    → R2 可行域扫描 ─┬─ 存在可行(族,split) → 以最优格重入 N1/N2 流程
 │                     └─ 空 → R3 P0a / R4 提案
 └─ 三源两层全收敛（仅 ensemble 层结论）→ N2

N2  corrected matched empirical-P finite-control（经验联合采样 + oracle L1，
    V31 QC packet 不动，20×3）
 ├─ PASS ≥19/20 → 图/decoder 可用 → N3 有限试点（一个包、≤30 块/源屏门）
 │    ├─ PASS → 回溯 audit（V13 式互斥帧身份）→ fresh 确认（依赖 ND）
 │    └─ FAIL → 恰好一次设计迭代（换族/换分配）→ 再败 → 关闭操作点转 R3/R4
 └─ FAIL → 有限转换层强证伪 → 新图族一次机会（protograph/lifting/多term λ）
      → 成功进 N3，失败转 R3/R4

N3' R3 P0a/P0b 门（可与主线并行）；R4 Cascade-on-frozen-blocks 提案（独立价值）

ND  数据节点（贯穿全程）：fresh acquisition 到位？
 ├─ 否 → fresh-confirm 类门保持 blocked；NB 预算封顶在 DE/合成层
 └─ 是 → intake→drift-precheck→prepare→review→execute→verify 链推进
```

### 分季度安排

| 阶段 | 内容 | 出口判据 |
|---|---|---|
| M0–M1 | N0（F-G1+主控裁决）；V33 按第四节意见修订后立项执行 | N0/N1 判定 |
| M1–M3 | N1 结果分流（N2 / R2 / R3+R4 并行启动）；fresh acquisition 用户侧争取 | 操作点生死判定 |
| M3–M6 | 幸存路线有限试点或 R3 P0b；ND 复查 | 一个候选进入回溯 audit 或两至三条路线关闭 |
| M6–M9 | 回溯 audit → fresh 确认 change（若 ND 就绪） | `ready_for_fresh_confirmation` 级别复现 |
| M9–M12 | 至多一个 NB 候选 qualification 尝试；系统级比较包；文档/archive/push 决策 | promoted 或 immutable negative（均为合法终点） |

**贯穿纪律**：no-rerun/no-tuning 于每个完成的门；旧 persisted terminal 以独立重算为准；测试通过≠科学验证；上游渐近证据不自动推广到有限码；V29/V30R/V31 为有限范围负结果而非全局失败。

---

## 六、总体判断

这条路线的科学资产真实且稀缺：holdout 验证的经验信道模型（V25）、该信道上 f=1.3 渐近收敛的 channel-informed DE（V26）、自洽的源自适应泄漏预算（V27R）、三次干净且边界诚实的有限码负结果（V28R/V29、V30R、V31）。真正瓶颈是**唯一渐近可行的系综族（λ={2:1}）与有限码需求之间的结构性错配**，叠加未完成的归因（V32 inconclusive）与被数据可得性卡死的最终证据通道。四条路线中，**V33 exact-V31-rate empirical-P ensemble DE 是当前不可跳过的最高价值前置门；只有 V33 全部通过后，corrected matched finite-control 才成为下一项高价值实验**；R2 是廉价的并行保险；R3 严格停留在 P0 门内直到前两者给出操作点判决；R4 是独立系统级参照。12 个月现实最佳结局是一个候选走到 fresh 确认门口，或两至三条路线带不可变负结果关闭——两种结局都按既有纪律以独立重算通过的不可变证据包收口，不做静默提升、不做事后放宽、不用工程测试冒充科学验证。

---

## 收尾声明

| 项目 | 状态 |
|---|---|
| 本次会话文件改动 | 新建 `docs/hd-qkd-ir-roadmap-review-20260823.md`（本文件）与 `docs/nbldpc-v32-main-verdict-unit-correction-20260823.md`（加法式更正，原 verdict 文件保持 byte-identical——就地编辑两次被环境中止，转为符合仓库先例的加法更正） |
| 禁止项遵守 | 未运行 DE/decoder/graph-builder/raw-data/longrun/minrerun/routeA/e2e；未 commit/push；未启动 successor |
| 独立验证记录 | coder-fast（read-only + focused tests）：HEAD=`3110cb0ebca973a3ac525fc9775d26ac288ba755`，subject=`fix(nbldpc-v32-audit-correction): enforce verifier semantic guards`；提交仅触及 verifier CLI/tests/tasks.md，docs/ 未动；`47 passed in 20.84s`（首次运行因 basetemp 父目录缺失报 40 errors，预建目录后复跑全绿——环境现象，非代码问题） |
| 用户独立核对采纳 | D2 gaps/L1/L2 ratio/Law B required/gaps、support-miss 三源值、V29 92<95 前缀性质、V31 ARCHIVED_PARTIAL 生命周期、V33 registry 一致性、Law A ≠ NB-Polar 可行性证明 |

**遗留开放项（均属用户/主控决策）**：
1. ~~等待 F-G1 复核~~ **已完成**：F-G1 = ACCEPT，audit-correction 变更已归档（终态 `audit_corrected_rate_aligned_de_required`，closeout 提交 d76a55c3 + b1171cc9）。V32 科学归因仍为 `bridge_inconclusive`，无 qualification/promotion。
2. **V33 立项收尾（当前活动停止点）**：变更目录 `formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic/` 已注册且四件套候选草案已写入（DRAFT_PENDING_FREEZE_REVIEW，含第四节修订意见：判敛公式需 freeze review 逐字定稿）；下一步 = 独立 freeze review → 主控 ACCEPT → 显式授权后 DE 才可执行一次。
3. V33 全过后的 R1 corrected-control / R2 扫描 / R4 提案授权顺序；
4. fresh acquisition 数据争取（最长杠杆）；
5. push 授权（长期待决）；
6. ~~待人工裁决的脏工作区项~~ **已解决（2026-08-23）**：用户确认非本人所为后，未知来源的整组未提交删除已全部按字节还原（`AGENT_PROJECT_MEMORY.md` 的 V32 ACCEPTED closeout 章节、`docs/decision-log.md` 的 2026-08-23 收口条目、addendum 文档、归档变更五文件）；还原后 `git status` 仅余 `M AGENTS.md`（用户本人修改，保留）、`M AGENT_PROJECT_MEMORY.md`（memory agent 新增 +31 行）、既有 `??` 未跟踪证据目录及本报告两份新文档。HEAD 保持 `b1171cc9` 不变；无 stage/commit/push。
