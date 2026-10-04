# NBLDPC V19→V23 科学结论汇总（2026-08-17 修正版）

> Supersedes the 2026-08-16 global “route unreachable” wording. Current state:
> `NBLDPC_CURRENT_SINGLE_EDGE_TOOLING_BLOCKED`.

## 1. 目标与当前边界

目标仍为 q=1024、V17 结构化信道、`f_total<=1.3`。目前只能得出：已测试的
短块策略以及当前 V22b 单边 DE 内核下的有限候选没有通过。不能得出理论上
全路线不可达，也不能声称 true protograph/MET 已失败。

## 2. V19/V20 科学重分类

- `31/64`：oracle-aided best-of cascade upper bound，不是可执行 FER；
- `40/96`：top-4 oracle coverage，不是可执行 FER；
- standalone bounded4 `30/64`：未独立验证的 Bob-only estimate；
- V20 V01：counting-only，不是语义回放验证。

V20 已归档并保留修正说明。

## 3. V21：停止门成立，但验证不完整

状态：`CONCLUDED_STOP_GATE_TRIGGERED_PENDING_ARCHIVE`。

- S0 BP-only：24/64，FER 0.625；
- S1 bounded4-only：28/64，FER 0.5625；
- S2 BP-first-fallback-bounded4：28/64，FER 0.5625。

三者均 `>=0.45`，短块 OSD/top-K 分支停止。限制：P0/P1 未在执行前完整
冻结；只有 AST Alice-reference 测试，runtime Alice-injection semantic verifier
与 V01 未运行。AST 测试不能等同“Bob-only 语义验证通过”。

## 4. V22：当前内核/已测候选为负

状态：`CONCLUDED_CURRENT_KERNEL_NEGATIVE_PENDING_ARCHIVE`。

V22b 将 degree cap 提升至 512 后，已测试的 q=1024 V17 structured
rate≈0.9375 候选仍未收敛。低 QSC p=0.05 的 SC 控制结果不等同目标信道通过。
有限构造 I03、有限 Bob-only E02、V01 均因 DE 门未过而
`CANCELLED_BY_DE_GATE`/`NOT_RUN`。

结论仅限 tested candidates/current kernel；没有完成 bounded full
`lambda/rho` optimization，也没有测试 true MET。

## 5. V23：实际是 aggregate single-edge diagnostic

状态：`CONCLUDED_SINGLE_EDGE_DIAGNOSTIC_PENDING_ARCHIVE`。

历史目录名包含 MET/protograph，但实现只把 base matrix 压缩为 aggregate
edge-perspective `lambda/rho`，然后调用 V22b。拓扑位置与 edge-type state 被
丢弃，因此不是真正的 topology-preserving protograph DE 或 MET DE。

证据限制：raw `scan.json` 只有 3 个矩阵；consolidated summary 中额外的
regular/simple-irregular 点缺少对应独立 raw/verify package。I03 true MET 未实现，
V01 未运行。summary-only 点只能作为未独立验证诊断，不能用于穷尽性结论。

## 6. 修正后的总状态

`NBLDPC_CURRENT_SINGLE_EDGE_TOOLING_BLOCKED`：

- 短块可执行策略触发停止门；
- V22/V23 的已测 aggregate single-edge 候选在当前 V22b 内核下未通过；
- bounded full single-edge `lambda/rho` optimization 尚未执行；
- true protograph/MET 未测试；
- 无 finite-code/FER qualification/promotion 结论。

旧 `NBLDPC_ROUTE_BLOCKED`、全局“不可达”及“MET failed”表述均被本修正取代。

## 7. 收口与后继

详细计划见
`docs/nbldpc-v21-v24-closeout-and-successor-plan-20260817.md`。先完成 V21→V23
文档分类和独立只读 closeout review；用户另行授权后才按 V21→V22→V23
顺序实际归档。本轮不归档。

V24 仅规划 bounded single-edge optimization；DE PASS 前禁止有限码。真正
MET 只能在 V24 FAIL 后另开 change 并获得用户授权。
