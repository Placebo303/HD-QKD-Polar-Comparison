# Proposal: cascade-beta-optimal-path — FINAL_GATE 唯一生死门

Status: FROZEN — 本变更唯一验收为 `FINAL_GATE.md`。此前 90 点 Pareto 方案作废，不再执行。

## Goal（本变更达成什么）

用**最小可证伪实验**判定 binary Cascade 是否值得继续作为 HD-QKD 主路线：

- 合成 sanity：独立 BER 1% 与 9.4% 双信道，初始块 `b ∈ {4,8,16}`，完整 FIFO look-back，最多 6–8 passes，每信道×块×passes 约 12–18 点小网格，彻底排除"块过大/look-back 受限/pass 不足"的借口
- 分开报告每个信道：`FER`、`accepted-frame leakage`（含分解）、`β`、`effective yield`，失败帧的 β 不得计入有效
- 真实位面相关性复现：从真实 ttbin 位面统计 `P(flip|plane)` 生成合成帧，检验 IID 假设是否掩盖失败
- held-out 一锤定音：独立 held-out 集上同时满足 `FER<5% & β>0.9 & undetected==0` 方为 PASS，否则正式退休 binary Cascade 主路线

## Non-Goals（明确不做）

- 不做 90 点 / 1386 点全扫描、Pareto 前沿、β-泄漏大数据分析
- 不修改 `src/`、`experiments/`、`tools/` 冻结基线，不重跑 Polar/LDPC 资格
- 不覆盖 `results/`、`comparison_bench/outputs_comparison/` 已固化生产输出
- 不引入 SHA/原子写/重试框架等生产化加固（研究代码最小可用即可）
- 不在失败帧上用"平均 β"或"吞吐"宣称有效

## Why（为什么只留生死门）

历史 Cascade 在固定 `[16,32,64,128]`/4-pass 下通过过合成/真实门限，但未回答：换小初始块+完整回溯+足量 passes 能否在真实位面相关信道上达到可用 FER/β。继续扩大扫描只会稀释判决力。本门限把资源收敛到可直接证伪的一次性判定：过则继续，不过则退休。

## Scope

- In scope:
  - 合成 IID 双 BER 网格（12–18 点）+ 真实位面相关性复现网格（同构 12–18 点对照）
  - 冻结 reporting 口径与公式（FER/泄漏分解/β/yield，失败帧隔离）
  - held-out 独立评估与 PASS/RETIRE 二元判决
  - `FINAL_GATE.md` + `spec.md` + `tasks.md` 冻结，coder-fast 可直接执行
- Out of scope:
  - 任何超出 FINAL_GATE 的扫描、Pareto、跨方法排名、Polar 对比
  - 新 decoder 重写、通用 benchmark 框架升级

## 生死门定义（摘要，权威见 FINAL_GATE.md）

- 网格：`BER ∈ {0.01, 0.094} × b ∈ {4,8,16} × passes ∈ {6,7,8}` 笛卡尔积去重后 12–18 点，FIFO look-back = 完整（所有已揭露 parity 可回溯），caps 继承 formal（5s/frame, 100k events）
- 报告：每点独立输出 `FER`、`leak_accepted_mean` 及其分解、`β_accepted`、`yield_effective`；失败帧不计入 β/yield 分子
- 位面相关性对照：同一网格用 `P(flip|plane=i) (i=0..9)` 从真实 ttbin 位面直方图采样复现，不用单一 IID BER
- 判定：仅在**独立 held-out** 上评估，同时满足 `FER<0.05 & β_accepted>0.9 & undetected==0` 为 PASS；否则 RETIRE（见 §5）

## Risks

| 风险 | 缓解 |
|---|---|
| 用 IID 掩盖真实相关性失败 | 强制位面相关性对照，非可选 |
| 用失败帧高 β 误判有效 | 冻结"仅 accepted 帧计 β"语义，verifier 强制隔离 |
| held-out 泄露/复用 | held-out 冻结分片，生成 seeds 与训练估计分离，manifest 绑定 |
| 阈值主观 | 阈值写入 FINAL_GATE/spec，pre-RESULT 独立复核，不可事后放宽 |

## Acceptance Checklist

- [ ] `FINAL_GATE.md` 已创建且为唯一验收口径（90 点旧口径已标记作废）
- [ ] `design.md` 与 `spec.md` 与 FINAL_GATE 网格/公式/判定一致
- [ ] `tasks.md` 含 12–18 点合成+位面相关性双网格、分解口径、held-out 判定、RETIRE 归档任务
- [ ] `git status` 仅新增/修改本 change 下 markdown，无生产代码改动
