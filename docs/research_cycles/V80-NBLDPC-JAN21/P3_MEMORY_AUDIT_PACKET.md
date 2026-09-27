# P3 真实帧记忆/一致性审计包（P3_MEMORY_AUDIT_PACKET）— FROZEN, NOT GRANTED

- Status: **FROZEN — NOT GRANTED — NOT AUTHORIZED — NOT EXECUTED**（docs-only 冻结；零解码；无 commit/push）。
- 版本（**re-freeze v2，2026-09-23，PROPOSED**）: v1 冻结时 T-M1..T-M4 = TBD；v2 = 主线程填数修订，**仅改 §2.5 阈值列 + 本版本头**（§2.5 判定算子列、T-C0 REUSED 行、§4 FAIL 分支原词「帧级条件化/漂移处理」及全文其余一字未动；docs-only，无授权、无执行）。**敏感度依据（T-M4 阈值来源）**: `Δf ≈ 1.26 × 0.01 / 0.83 ≈ 0.015`（阈值论证，非预测）。
- Track（恰其一）: **DECIDE**（真实/原始数据 + 路由门 + 未来 publication 数字上游；AGENTS.md §1.2 适用性矩阵“真实数据开发/验证 → DECIDE 全合约”）。
- 基线（provenance，非执行锁）: 用户声明仓库基线 `8e9c8526`；执行前由 Pre-EXECUTE 实测记录实际分支/HEAD，本包不做 SHA 相等断言（AGENTS.md §10.3）。
- 路线位置：用户裁决顺序 ① P4-elevation → ③ 并行（P4 构造可行性 + P3 包冻结同时推进）→ ② S-B 窄路。**本包属 ③，只冻结不执行**，与并行 P4 包互不触碰。
- 权威上游：`docs/ROADMAP-20260921.md` §1.2-item-5 / §3-P3 / §4 决策树 / §6-R2；`docs/EXECUTION_PLAN_20260922.md` S0.4 + P3-gate；AGENTS.md §1.2 / §3 / §10.3；X1/P1 结论（记忆假设“未证伪≠已验证”）。
- Acceptance ID: **G-P3-MEM**（包冻结已完成；授权、执行、结果、验收一律未发生）。
- 必读已执行：EXECUTION_PLAN S0.4/P3-gate、ROADMAP P3、AGENTS §1.2/§10.3、P3_CENSUS 系列（含 P3_A1_REVIEW F-4 电池功率 caveat）已读。

## 0. 授权边界与停门语句（全文有效）

1. 本包**不授权**任何解码/DE/构图/真实数据访问/`tools/longrun_*|minrerun_*|routeA_*`/commit/push/资格化/发表 claim。
2. 本包冻结后**停止在显式授权门前**：下一步须用户对 `P3_MEMORY_AUDIT_PREREG_AND_AUTH`（或等价单一 append-only 记录中的授权节）显式授权 + Pre-EXECUTE PASS 后方可执行；无授权不得执行。
3. 本包内**无任何预测结果**（无 FER / 无 f / 无 success / 无失败数预测）。容差仅设判定规则与阈值槽位（§2.5），阈值外的一切数值断言一律禁止（P3-3）。
4. 本包**不修改**以下任何对象（P3-3 禁碰清单）：P1 族（含 P1_PACKET/PROMPT/STAGE1 系列）、P4 包（另一并行任务）、S0.1 族（含 S0_1_M200 系列）、`docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`（若存在）、`docs/decision-log.md`、`AGENTS.md`、`src/`（`git diff -- src/` 必须为空）。

## 1. 问题与假设（待检验，非 claim）

- Q-M1（帧内记忆）: 真实帧是否存在帧内符号相关，使无记忆符号级 `gamma_f03` 生成器系统性偏乐观？
- Q-M2（帧间记忆/漂移）: 是否存在帧间相关或块间漂移（自相关、block-H 序列斜率/极差）？
- Q-M3（一致性）: 在冻结超帧划分下，超帧错误权重分布、逐列边缘/联合直方图与 `gamma_f03` 生成器是否定量一致（χ²/TV 距离、权重分布分位数对比）？
- Q-M4（可迁移性）: 上述差异是否在预注册容差内，从而允许把合成 FER 向真实外推的讨论进入 S3；否则必须先做帧级条件化/漂移处理。
- X1/P1 继承结论（措辞冻结）: “记忆假设未证伪≠已验证”（P3_A1_REVIEW F-4：ACF 电池在 ~1 pair/frame 下对帧内记忆结构性失明；P3-gate 关闭该缺口前，合成 FER 不得当真实 FER）。
- Pre-registered NON-prediction（冻结）: 不预注册任何 H_full 值、漂移统计量、自相关值、FER/f 值；ROADMAP“低 H 买余量”在固定 m 下为假（P3_CENSUS §9.3），本包不做该方向假设。

## 2. 冻结科学输入

### 2.1 数据（真实 HD-ToA 帧；统计量级访问；零解码）

- 范围：Jan-21 三源真实帧 **1M / 1.5M / 2M**（CW 时间-能量纠缠、ToA 分箱、d=1024；IR 只消费 H(X|Y)，与偏振/BBM92 无关——ROADMAP DECISION-3）。
- 超帧划分（冻结，唯一口径）: n=1024 GF(32) 符号超帧；块数口径为冻结池 **2000/2767/3645 帧 → 500/691/911 超帧**（ROADMAP §1.2-item-1 / decision-log:3078）。census 实测 raw-stream 计数（129763/180536/239420 量级）是**另一量纲**，本包不得混用、不得替代（P3_A1_REVIEW F-5）。
- 访问方式（冻结）: **零解码或仅统计量级访问**——允许读事件流做计数/直方图/相关统计；**0 decoder 调用、0 DE 调用、0 图构造、0 `tools/*` 重跑**。任何解码器调用即 STOP-BLOCKED（科学输入变更）。
- `.ttbin` 成员语义（继承冻结禁令）: 严禁同时打开配对两成员并拼接（NESTED/SUPERSET，非不交分块；P3_CENSUS §2 A1）；合法模式仅 base 自动跟随或 `.1` 单分片二选一。本包默认消费已解析帧表（registry/parquet），不重新发明配准参数。

### 2.2 统计量（逐帧/逐块一致性检验；分源报告，禁合并）

三源各自独立计算、独立报告、**禁跨源合并、禁跨构造实例合并**：

1. **超帧错误权重分布**：每超帧错配符号数（Alice–Bob 符号比较，统计量，非解码）的经验分布：mean/median/p99/max + 全直方图；与 §2.4 生成器期望分布做分位数对比。
2. **逐列边缘与联合直方图**：列边缘分布 + 联合 `(x,y)` 稀疏直方图；与 `gamma_f03` 生成器同口径对照（χ²/TV 距离，见 §2.5）。
3. **帧内/帧间相关性**：mean-centered lag-k ACF（mismatch 指示子 + block-H_full 序列双轨）；漂移 = 连续 4-帧块 H_full 的 max−min + 最小二乘斜率（P3_CENSUS §7.2 同定义，小样本 caveat 原样继承）。
4. **与 `gamma_f03` 生成器的定量差异**：χ²/TV 距离、权重分布分位数对比、支持集/占有率对照；2M 作对照源（V80 冻结信道源）。

### 2.3 记忆假设检验设计（冻结）

- H0（零假设）: 无记忆符号级模型（`gamma_f03` 生成器）在可测粒度下充分描述真实帧。
- H1（备择）: 存在帧内记忆或帧间记忆/漂移，合成 FER 系统性偏乐观。
- 检验机（冻结）: §2.2 的四个统计量各自对照 §2.5 容差做 PASS/FAIL；**任一 FAIL 即整包 FAIL**（P3-gate 见 §4）。ACF 电池功率 caveat 必须写入结果：`SE ≈ 1/√n_frames`，电池仅对 ≳0.005 量级帧间相关有功率，对帧内记忆结构性失明——“未证伪≠已验证”措辞强制保留。

### 2.4 时延/PPP 与 prior/gamma（冻结；描述性，不重拟合）

- 时延/PPP：若无可信路径，**仅作描述性记录**（三源分布形态报告，report-only），**不重拟合、不反哺任何先验或信道参数**。任何拟合即科学输入变更，STOP-BLOCKED。
- 既有 prior/gamma 标定（冻结）: `docs/research_cycles/V80-NBLDPC-JAN21/gamma_f03.npz`（+ `gamma_f03_pb.npz`）**只读、永不重拟合、跨臂复用即一次性工厂标定**；跨源复用**禁止**（X1 §4）；本包不产生新 bundle，不改变任何既有标定；`beta` 只推导（本包不涉及 beta 计算，如 S3 需要则另包）。
- ROADMAP 地位：本包**不锁定、不修改** ROADMAP/EXECUTION_PLAN；科学冻结口径以 ROADMAP/V80_BASELINE 为准（EXECUTION_PLAN 头部冲突规则）；本包是其 S0.4/P3 子项的冻结实现。

### 2.5 预注册容差（判定规则冻结；数值槽位冻结；无预测）

| # | 统计量 | 判定算子（冻结） | 阈值（冻结状态） |
|---|---|---|---|
| T-C0 | 2M 对照 H_full vs V80 锚 `0.83256272` | `\|Δ\| ≤ 0.01` | **REUSED**（P3_CENSUS §6 控制门既有冻结值，非新设） |
| T-M1 | 超帧权重分布 vs 生成器（TV + 分位数） | TV/分位数双项同时在限内 | **PROPOSED — re-freeze v2（2026-09-23）**: TV ≤ 0.05 且 median/p99 相对差 ≤ 10%（绝对差 ≥ 2 时 ≤ 2） |
| T-M2 | 逐列边缘/联合 vs `gamma_f03`（χ²/TV） | χ² p 值下限 + TV 上限 | **PROPOSED — re-freeze v2（2026-09-23）**: χ² p ≥ 0.01 且 TV ≤ 0.05（分箱方案先冻结，后算 χ²） |
| T-M3 | 帧间 ACF lag-1..k | `\|acf\| ≤ k·SE`，k 预注册 | **PROPOSED — re-freeze v2（2026-09-23）**: lag 1..5，k = 3，`\|acf\| ≤ 3·SE`，SE = `1/√n_frames`（定义已冻结）；电池功率 caveat（≳0.005 量级才有功率、帧内结构性失明）强制写入结果 |
| T-M4 | block-H 漂移（slope / max−min） | slope 上限 + max−min 上限（小样本 caveat 下解读） | **PROPOSED — re-freeze v2（2026-09-23）**: 连续 4-帧块 `H_full` max−min ≤ 0.01 b/sym 且 \|slope\| ≤ 0.002 per block；敏感度依据 `Δf ≈ 1.26×0.01/0.83 ≈ 0.015`（小样本 caveat 下解读） |

- P3-3 合规声明（re-freeze v2，2026-09-23 更新）: 上表 T-C0 仍为既有冻结值（**REUSED**，非新设）；T-M1..T-M4 已由主线程填数为 **PROPOSED** 阈值（填数 = 包修订 re-freeze v2，见版本头，非静默手写）。**阈值以外**本包不声明任何容差数值，不声明任何预测结果（无 FER/f/success/失败数/“预期通过”句）。授权仍须主线程/用户在授权时逐项确认 §2.5 数值；未确认即按 PROMPT §1-1 阻断执行。
- 多重比较：T-M1..M4 任一 FAIL 即整包 FAIL（§4）；不得事后挑显著项拼凑 PASS。

## 3. DECIDE 合约（五件套；AGENTS.md §1.2 + §10.3）

1. **PREREG_AND_AUTH**（已接受的 prereg）：本 PACKET + PROMPT 为 prereg 本体；`P3_MEMORY_AUDIT_PREREG_AND_AUTH.md`（或等价单一 append-only 记录中的授权节）经用户显式授权签字后方为 accepted prereg。签字块在本包留空（见 §7）。
2. **Pre-EXECUTE**（执行前门）: 按 PROMPT 的 Q 清单逐项验证——意向分支、scoped 清洁、冻结科学合约（§2）、确切命令、预算、目标输出 absence、显式用户授权、focused 测试。任一 FAIL 即阻塞执行。
3. **一次执行 + 一次结果记录**：一台机器根 `workspace/P3_MEM/<uuid>/`（fresh additive，预先不存在）；产出 `RESULT.md`（或等价单一 append-only 记录中的结果节）+ 机器伪影（分源表、统计量 JSON、无事件数组落盘）。
4. **独立 Pre-RESULT**（发表/固化前门）: 独立线程按 PROMPT 清单重核计划阈值、泄漏公式分解（本包 N/A，显式标注）、`undetected` 隔离（本包 N/A，显式标注无解码）、分源分解、披露会计、计划语义 vs 实际伪影。FAIL 即阻塞固化，立即返工，不得先发表后补。
5. **主线程接受**：`INDEPENDENT_ACCEPTANCE.md`（或等价记录中的验收节）由主线程裁决接受/改道/停止；压缩三文档形式（PREREG_AND_AUTH / RESULT / INDEPENDENT_ACCEPTANCE）+ 机器伪影是允许的等价形式；单一 append-only 记录在无歧义时可替代分态文档。
- 失败保留：DECIDE 不可变失败保留；无预注册工程修复+重跑条款（与 EXPLORE 不同）；任何重跑 = 新授权 + 新根。
- No-overwrite：`results/`、`comparison_bench/outputs_comparison/`、既有证据根一律只读；新输出仅入 `workspace/P3_MEM/<uuid>/`。

## 4. P3-gate 判定形式（冻结；S3 前置门）

```
P3_MEMORY_AUDIT（G-P3-MEM，三源分报）
  ├─ PASS（T-C0 ∧ T-M1 ∧ T-M2 ∧ T-M3 ∧ T-M4 全在预注册容差内）
  │     └→ 放行 S3 讨论（S3 仍需独立 DECIDE 包 + 逐源可认证判定表；本包不放行 S3 执行）
  └─ FAIL（任一统计量超出容差，或电池功率不足以判定关键机制）
        └→ 先做帧级条件化/漂移处理；不得把合成 FER 当真实 FER；
           不得合并源“凑通过”；S3 包冻结前必须引用本包 FAIL 项
```

- claim ceiling（冻结）: 本包最高产出 = “记忆/一致性差异是否在容差内”的门 verdict；**不是** FER/SKR/资格化/发表结论；任何对外句必须带“未证伪≠已验证 + 电池粒度”限定。

## 5. 预算与停止规则（PROPOSED 上限；授权时确认）

- 提议上限（复用 P3_CENSUS 先例，非新执行授权）: trio wall ≤ 5400 s（单源 ≤ 1800 s）、单读 wall ≤ 300 s、peak RSS < 4 GiB、每源读 ≤ 2 次、0 解码/DE/构图。最终预算以 Pre-EXECUTE 确认值为准。
- STOP-BLOCKED（任一即停，无 fallback）：对齐/配准未通过而用默认参数继续；同时打开配对两成员；重拟合 gamma/prior；调用解码器/DE/构图；目标根已存在（非 fresh）；混用块数口径；跨源合并统计量。
- Focused 测试（执行前必须通过，fake-only）：stats-only 模块导入/形状/归一化门 + no-decode 守卫测试（显式断言无 decoder/DE/graph 调用路径）。

## 6. 修订规则

- 本包冻结后任何科学输入/阈值/预算/授权边界变更 = 包修订（re-freeze + 新版本号），不得原地静默改写。
- P4 包、P1 族、S0.1 族的变更不得写入本包；本包的 TBD 填数不得写入他包。

## 7. 授权签字块（BLANK — 本包未授权）

- PREREG 状态：`DRAFT_FROZEN_PENDING_AUTHORIZATION`
- 用户授权签名：`[BLANK — 未授权，不得执行]`
- Pre-EXECUTE：`[BLANK — 未执行]`
- Pre-RESULT：`[BLANK — 未执行]`
- 主线程接受：`[BLANK — 未接受]`
