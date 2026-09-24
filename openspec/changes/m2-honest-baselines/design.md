# M2 Honest Baselines — Design

Status: documentation-only 冻结契约。无执行、无授权、无新数。Müller 块长调度若有歧义，标"待澄清表"，不猜数（歧义项走 `/opsx-explore` 冻结后才可实现）。

## 1. HD-Cascade 二进制映射

- 10-bit 符号 → Gray 码（无原文依据，永标 assumed）→ 位面分组；Alice 为参考，Bob 本地纠错；离线对账模型（已认证公开信道假设与 formal 方法边界一致，不新增安全主张）。
- 按位分组：同一 Gray 位面内的比特组成 Cascade 块；块长表按位面分组分别冻结（见 §3 待澄清表规则）。
- 级联传播：跨 pass/跨位面的 lookback 传播语义与既有 `single_kernel` 一致，本 change 只增量扩展，不重定义。

## 2. HD-Cascade 块长与并行版

- 起点：`comparison_bench/src/comparison_bench/methods/cascade_lite.py` + `comparison_bench/src/comparison_bench/methods/cascade/single_kernel.py`，只增量（约 300–500 行），并行版优先。
- Müller 2024 三改命名（仓内已文档化版本；出处：`docs/RESEARCH_DIRECTION_REPORT_20260924.md` §6/M2 + 用户 2026-09-24 三 PDF 原文阅读，按Müller原文ar5iv 2307.02225v2 §2.3.2/Table 2）：① 二进制映射 10bit→appropriate binary representation位面分组（Gray无原文依据，永标assumed）；② 按位分组块长调度；③ 级联传播规则。实现时每改一 task（T1=改①，T2=改②，T3=改③，见 `tasks.md` T1–T3）；并行版消息数会计独立一 task（T4）。assumed-v1 provisional值（[8,4]/max_passes 4/sweep 1/消息公式）非原文，真值为QBER-自适应k1..k6公式，n=2^16 bits。
- 待澄清表（表结构冻结，数值待填；**不猜数**）：

| 改项 | 原文节号 | 精确定义 | 块长表真值 | 状态 |
|---|---|---|---|---|
| ① 二进制映射 10bit→appropriate binary representation位面分组（Gray无原文依据，永标assumed） | §2.3.2 item1 | map appropriate binary + QBER_BIN 公式（无 Gray） | —（本改无块长表） | 已关闭 |
| ② 按位分组块长调度 | Table 2（§2.3.2） | QBER-自适应 k1..k6 公式（`[.]` = nearest int 取整） | n=2^16 bits；位面 × pass → 初始块长/增长规则/封顶按 Table 2 k1..k6 真值（assumed-v1 `[8,4]` 非原文，见下差异声明） | 已关闭 |
| ③ 级联传播规则 | §2.3.2 item3 | Mod-5 替代 + 收齐错误列表再统一 cascade + early-stop（首轮 cascade > 95%） | —（本改无块长表） | 已关闭（B2-App A.2 部分关闭注记） |

- 说明：provenance = Müller 原文 ar5iv 2307.02225v2（§2.3.2/Table 2；用户 2026-09-24 三 PDF 原文阅读；仓内对照见 `docs/RESEARCH_DIRECTION_REPORT_20260924.md` §6/M2 + L3 行）。上表三行已按 planner 关闭值落字（①②已关闭，③已关闭附 B2-App A.2 部分关闭注记）。assumed-v1 差异声明：PACKET §7-4 assumed-v1 provisional 值（[8,4]/max_passes 4/sweep 1/消息公式）非原文，真值为 QBER-自适应 k1..k6 公式（n=2^16 bits）；未关/`/opsx-explore` 前禁引 Müller 真值主张。关闭状态（planner 2026-09-25）：B1 关闭（引文）；B2 部分关闭；B3 open；B4/B5 关闭。q1024 外推注记：Müller HD-Cascade 实测字母表 q∈{4,8,32}，用于本项目 q=1024 处为外推，永标 assumed。剩余 open 项（B3 + App 剩余）仍走 `/opsx-explore` 冻结后才可实现；冻结规则：实现 change 在剩余项关闭前不得填数。

## 3. HD-Cascade 消息数与泄漏会计

- 交互消息数按 Müller 口径：**每帧消息数**，Cascade 446 vs LDPC 3.14 对标行独立标注（A-CMPE-4；P6）。
- 泄漏分列：`leak_EC`（Cascade 公开奇偶/二分位）+ 64-bit tag + 控制轮次/控制帧公开量逐项单列 ⇒ verification-aware `λ_total = leak_EC + 64`（+ 控制项）；禁合并成不透明数字（A-CMPE-3）。
- `undetected`（`accepted_wrong`）独立列，禁并入 success/FER（A-CMPE-1）。
- `f_super` 与 `f_eff` 本臂 m 基双数并列，禁互相替代（A-CMPE-2）。

## 4. 分层二元 LDPC：逐位面熵分配

- 逐 Gray 位面熵分配码率：使用**冻结**位面熵 `H_L1 + H_L2`（0.801038 / 0.825566 / 0.832563），**不重拟合**，不引入新训练/校准读取。
- 每位面独立构造（n=64 既有族语义保持；新构造参数在实现 change 冻结，本 design 只冻结"每位面构造"结构要求）。
- 替换对象：V19 保守行数（f=4.169）稻草人行；替换后历史行按 A-CMPE-6 标口径与"不可比即标"。

## 5. 分层二元 LDPC：盲协调与译码冻结

- 盲协调：多段小步长增量综合征揭示；每段公开量计入 `leak_EC` 分解（A-CMPE-3）。
- 二元 SPA：`max_iter`–streak（收敛连续轮）组合冻结，实现 change 不得调参；本 design 冻结"冻结"要求本身，具体数值由实现 change 引用既有冻结配置，不在此发明。
- 每位面综合征一致性 + Toeplitz 验证（t=64）为成功必要条件（与 formal 边界一致）。

## 6. 共通：计数、参数与状态列

- `d`/`q`/`n_IR` 分离报告（维数/字母表/IR 块长各成列）。
- 三组计数分离：合成 / 真实 / key-eligible；per-source `attempted`/`exact_match`(=success=¬failed，`decoded`≠success 图例)/`accepted`/`accepted_wrong` 独立列。
- `N_req` report-only vs key-eligible（200/276/364）分列；`N_req` 不作操作点选择。
- measured / assumed / projected / qualified 列归属：每个对外数字落四列之一；无安全观测量 ⇒ 禁 SKR（A-CMPE-7）。
- 历史行不可比即标（H 基/tag/池/分解任一不一致即标 + 原因，禁跨口径差值）。

## 7. A-CMPE-1..7 逐条映射（full）

| ID | HD-Cascade 落点 | 分层二元落点 |
|---|---|---|
| A-CMPE-1 | §3 undetected 隔离；per-source 四计数 | §6 per-source 四计数；综合征一致≠success 图例 |
| A-CMPE-2 | §3 双数并列（本臂 m 基） | §6 双数并列（本臂 m 基） |
| A-CMPE-3 | §3 leak_EC+64tag+控制轮次分列 | §5 盲协调各段公开量分列 + 64tag |
| A-CMPE-4 | §3 wall/RSS/每帧消息数（446 口径） | §5 wall/RSS/每译码 wall + 消息数（3.14 口径对照） |
| A-CMPE-5 | §6 d/q/n_IR；N_req vs 200/276/364；三组计数 | 同左 |
| A-CMPE-6 | §4 历史行标注；探针行独立 | §4 V19 f=4.169 行标注；探针固定句 |
| A-CMPE-7 | §6 claim ceiling + 四列归属 | 同左 |

## 8. Explicitly not in design

- 具体块长数值（歧义部分）、新码族参数、SPA 数值、阈值门、输出文件名/新列定义、任何执行授权。
