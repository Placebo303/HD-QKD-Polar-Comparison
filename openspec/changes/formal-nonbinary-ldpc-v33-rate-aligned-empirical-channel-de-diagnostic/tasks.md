# Tasks: formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic

> **Status: DRAFT_PENDING_FREEZE_REVIEW** — freeze review 通过前不得勾选任何条目、
> 不得实现、不得执行。

## Allowed New Files（草案）

- `comparison_bench/src/comparison_bench/cli/run_nonbinary_v33_rate_aligned_empirical_de.py`
- `comparison_bench/tests/test_nonbinary_v33_rate_aligned_empirical_de.py`
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v33_rate_aligned_empirical_de/run_01/*`
- workspace 测试根 `workspace/v33_<fresh-id>/*`

## Forbidden

- 真实 DE 执行（授权门未过前含 smoke）；decoder/graph-builder/finite-control/
  raw-data pipeline/longrun/minrerun/routeA；sibling checkout；原始 .ttbin。
- 五 protected old roots + archive + src/experiments/tools/results 覆盖；
  n=2048 产物；memory/decision-log 编辑（本变更内）；qualification/promotion 措辞；
  push；git add -A；run_02/rerun/tuning/补 seed/screen-rank-select。

## 阶段（草案）

- [ ] P1 规格冻结：四件套定稿（判敛公式/聚合规则逐字化）；reviewer R1 审查；
  **主控 ACCEPT_FREEZE**（候选调用矩阵就此转正为冻结值）。
- [ ] P2 实现 + T0/T1（fake DE runner 显式注入）。
- [ ] P2R fake T2 全流程（可解→PASS / max_iter→FAIL / NaN→INCONCLUSIVE /
  zero-denominator→inconclusive_input_binding）+ strict replay + exact-once 顺序断言。
- [ ] P3 独立候选验收 R1（非实现者）。
- [ ] **P4 执行授权门：主控显式授权后，方得对真实输入运行 30 calls 一次。**
- [ ] P5 closeout：R2 独立重算写 readonly_review.json + candidate handoff +
  终态持久化。

## Frozen Constants（候选——ACCEPT_FREEZE 前可被主控修订）

- 层率表：L1 三源 0.984375；L2 0.8203125/0.814453125/0.8125（allocation
  `m1_16_n1024` 过滤核对）；m1=16；m2={184,190,192}；n=1024。
- ρ 构造：make_rho(R_i, lambda={2:1})；禁止 f=1.3 反推。
- 调用矩阵：seeds 33101–33105；n_samples=2000；max_iter=200；
  entropy_tol=0.01 bits/symbol；streak=20；RNG=PCG64；30 calls。
- 终态三值 + INCONCLUSIVE reason codes（含 inconclusive_input_binding）；
  聚合优先级 INCONCLUSIVE > FAIL > PASS。
- 输出根 `nbldpc_v33_rate_aligned_empirical_de/run_01/`；exact-once 固定顺序。

## 强制停止点

1. 主控 ACCEPT_FREEZE 前不得实现；
2. 实现 acceptance 前不得执行真实 DE；
3. closeout 后立即停止等待主控裁决。

## Final Return Statement（逐字）

> candidate_only，等待 Codex 主控 ACCEPT/REJECT；未运行 DE，未运行 decoder，未启动 successor。
