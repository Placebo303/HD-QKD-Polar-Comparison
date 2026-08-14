# Proposal: formal-nonbinary-ldpc-v13-r3-fresh-acquisition

> 状态：PLANNING —— 2026-08-15 按用户更新后的目标（P1：立即优先）立项。

## What

对 V13 冻结候选 `nbldpc_v13_r3_code_v1` 执行**一次 fresh acquisition
确认**：在新的帧/载荷数据（新采集，身份与全部历史锁不重叠）上，用
**完全不变的** R3 码本、QSC p=.20 先验、flooding FFT-QSPA 接口与
max_iter=100，回答唯一问题：**"R3 在 fresh 数据上是否仍能精确纠错"**。

本 change **不**做：promotion/qualification 宣称、任何调参、候选替换、
帧替换、重跑、码本/先验/迭代上限修改、效率优化（效率仍约 f≈12）。

## Why

- V13 全部证据（E01 64/64、A01 128/128、A02 bw120 128/128 + bw180
  128/128）基于**历史帧身份**（V4/V5 身份锁覆盖），最高状态只能是
  `ready_for_fresh_confirmation`——不是 promotion/qualification/fresh
  correction。
- 这是当前证据收益最高、技术不确定性最低的路线：候选已被 D05 诊断
  为 `code` 类根因并修复（连通 girth-8 图），历史数据上 448/448 精确
  纠错；唯一未验证的是**分布漂移后的 fresh 泛化**。
- V14 效率门已冻结效率路线（gate_state=fail），fresh-confirmation-only
  路线不受影响；本 change 是用户更新目标中的 P1 立即优先项。

## Scope

- 新建 OpenSpec change（本 change），**不复用 V12 执行身份**，不自动
  宣称 promotion。
- 冻结内容（详见 design.md §1–§7）：
  1. 新 frame/payload identities（命名空间与历史锁不重叠，排除验证）；
  2. acquisition/window/stratum 设置（数据源声明、bw200 主 / bw120、
     bw180 次）；
  3. characterization、canary、confirmation 角色隔离（互斥、预注册）；
  4. R3 码本、先验、迭代上限**保持不变**；
  5. 分布漂移与无 eligible frame 的停止规则；
  6. 所有失败原样保留，禁止替换帧、调参或重跑。
- 流程保持：冻结新采集身份与角色 → prepare → 主线程独立 review →
  单次 fresh execute → 一次只读 verify → **fresh-confirmed** /
  **frozen failure**。

## Out of scope

- 效率改进（f≤1.3 目标属 P2/V17 门）；SC-LDPC、位面分解、多边族构造；
  V15/V16 重启（已归档为 aborted drafts，需新 DE 门 PASS）；
  Polar/其他方法比较；任何官方 `formal_ir_methods` 资格根写入。

## Success criteria

- prepare 产出冻结的身份台账（含 zero-eligible 情形）并经主线程
  review；
- 若无 eligible 帧或漂移超限 → 按冻结停止规则产出 frozen failure；
- 否则单次 fresh execute + 一次只读 verify → 判定
  `fresh-confirmed`（全绿）或 `frozen failure`（任一失败原样保留）。
