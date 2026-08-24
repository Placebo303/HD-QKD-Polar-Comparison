# Tasks: formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic

> **Status: RUN_COMPLETE_ER1_ACCEPTED**（2026-08-24）— V33 official `run_01`
> 已按用户 `EXECUTE_AUTH` 恰一次完成；30/30 PASS，ER1 ACCEPT，主控接受该
> ensemble-only 终态。任何 finite-control/successor 仍需新 OpenSpec 与授权。

## Allowed New Files（草案）

- `comparison_bench/src/comparison_bench/cli/run_nonbinary_v33_rate_aligned_empirical_de.py`
- `comparison_bench/tests/test_nonbinary_v33_rate_aligned_empirical_de.py`
- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v33_rate_aligned_empirical_de/run_01/*`
- workspace 测试根 `workspace/v33_<fresh-id>/*`（**绝不创建 official run_01 于测试中**）

## Forbidden

- 真实 DE 执行（授权门未过前含 smoke）；decoder/graph-builder/finite-control/
  raw-data pipeline/longrun/minrerun/routeA；sibling checkout；原始 .ttbin。
- 五 protected old roots + archive + src/experiments/tools/results 覆盖；
  n=2048 产物；memory/decision-log 编辑（本变更内）；qualification/promotion 措辞；
  push；git add -A；run_02/rerun/tuning/补 seed/screen-rank-select。

## Frozen Constants（候选——ACCEPT_FREEZE 前可被主控修订）

- **Binding Registry R1–R7**：唯一规范定义见 spec SHALL-BIND1（canonical 表，
  含完整路径/精确 key/Source ID ↔ m2 绑定/用途边界）；本文件不维护副本。
  stage-0 失败冻结语义（zero DE calls / 不进聚合 / overall=INCONCLUSIVE /
  五类 reason 枚举 missing_input / binding_drift / field_mismatch /
  allocation_mismatch / malformed_input / 无伪造 call 记录）见 design §1 与
  spec SHALL-SF1。n=1024；m1=16。
- **GF(32) identity**：GF2mField.create(32)；primitive polynomial = 37
  （0b100101）；polynomial basis；field_id =
  `c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`
  （与 V31 manifest 一致）。
- **Sampler semantics**：flatten P_s(A,B) 抽样；三源独立不合并；L1 用 P(U1|B)；
  L2 用同一真实 A 的真实 U1 条件；GF-XOR centering 真值 index-0；PCG64 固定
  draw order；非法条件分母 ⇒ INCONCLUSIVE(inconclusive_input_binding)，禁
  one-hot fallback。
- **状态机**：IMPLEMENTATION_CANDIDATE/EXECUTE_NOT_AUTHORIZED →（IR1 + 主控
  implementation ACCEPT）→ IMPLEMENTATION_ACCEPTED/EXECUTE_NOT_AUTHORIZED →
  （主控另行 EXECUTE_AUTH）→ 真实 DE 恰一次。
- **ρ 构造**：make_rho(R_i, lambda={2:1})；禁止 f=1.3 反推。
- **调用矩阵（候选）**：seeds 33101–33105；n_samples=2000；max_iter=200；
  entropy_tol=0.01 bits/symbol；streak=20；RNG=PCG64；30 calls。
- **机械判敛**：H_t = population mean categorical entropy (bits/symbol)；
  PASS ⟺ 概率全程有效且连续 streak=20 iterations H_t < 0.01 bits/symbol；
  max_iter=200 未满足（含有限振荡）⇒ FAIL。
- 终态三值 + INCONCLUSIVE reason codes（含 inconclusive_input_binding）；
  聚合优先级 INCONCLUSIVE > FAIL > PASS。
- 输出根 `nbldpc_v33_rate_aligned_empirical_de/run_01/`；execute 入口 collision
  检查一次，同 execute 内后续阶段不重复触发。

## Review IDs（唯一命名）

- **FR1** = freeze review（规格冻结审查）。
- **IR1** = implementation candidate review（实现候选验收，非实现者）。
- **ER1** = post-execution read-only evidence review（执行后只读证据复核，
  写 readonly_review.json 的唯一角色）。

## 阶段（草案）

- [x] P1 规格冻结：四件套定稿（判敛公式 H_t 逐字化）；reviewer-go **FR1** 审查；
  **主控 ACCEPT_FREEZE（2026-08-23，冻结基线 commit `0a050066`）**——全部 frozen
  constants、bindings、sampler、H_t、terminal、path/write guards、exact-once 与
  claim boundary 转为不可变；Candidate Call Matrix 候选值就此转正。
- [x] P2 实现 CLI + T0/T1（fake DE runner 显式注入；仅写 workspace fresh root，
  绝不创建 official run_01）。
  - 证据：T0 `10 passed, 39 deselected in 0.56s`（basetemp
    workspace/v33_run_0823d/t0）。
  - 证据：T1 `29 passed, 20 deselected in 8.92s`（basetemp
    workspace/v33_run_0823d/t1）。
- [x] P2R fake T2 全流程 + strict replay + exact-once 顺序断言 +
  official-root 创建守卫断言。
  - 证据：T2 `8 passed, 41 deselected in 2.56s`（basetemp
    workspace/v33_run_0823d/t2；strict replay norm() 白名单含
    freeze_digest_ref，主控 2026-08-23 裁决补入）。
  - 证据：T3 `2 passed, 47 deselected in 0.73s`（basetemp
    workspace/v33_run_0823d/t3）。
- [x] P3 **IR1 implementation candidate review**（独立 Luna，非实现者）+
  **T3**：真实输入只读 binding/identity 核验（R1–R7 存在性/SHA256/字面值）+
  protected roots pre/post unchanged——**不调用真实 DE**。
  - 2026-08-24 fix candidate：R4 从 V25 train counts 独立重算 F03 H 并核对
    m_total/f_total；R6 核对每源两组 rate+H identity；授权绑定 HEAD 与冻结调用
    矩阵；数值异常 reason 与 claim/provenance replay 加强。
  - 当前证据：compile/real-input prepare/selfcheck PASS；focused fake/read-only
    suite `55 passed`（`workspace/v33_ir1_acceptance_r7`）。独立 IR1 于 2026-08-24
    对精确提交 `5b8cfef3fa0c45534c3aaede30750e6ad49bd2f6` 给出 ACCEPT；官方
    `run_01` 不存在，未调用真实 DE/decoder/finite graph。
- [x] P3 END **implementation candidate handoff**。强制停止点：
  **IMPLEMENTATION_ACCEPTED / EXECUTE_NOT_AUTHORIZED** —— 主控 implementation
  ACCEPT 已记录；P4 仍需另行、显式 `EXECUTE_AUTH` 方可解锁。
- [x] P4 用户于 2026-08-24 明确授予 `EXECUTE_AUTH`；在 HEAD `41d31151` 上按
  固定顺序恰一次完成 30 calls。30/30 PASS，六个 cell 均 5/5 PASS；未运行
  decoder、finite-control 或 successor。
- [x] P4R **ER1** post-execution read-only evidence review：CLI strict verify
  `consistent / problems=[] / records_checked=30`；独立 Luna ER1 `ACCEPT`，仅新增
  `readonly_review.json`，protected roots observed unchanged。
- [x] P5 closeout：`operator_handoff.md`、终态与主控 ACCEPT 已记录；不自动启动
  matched finite-control。

## 强制停止点

1. 主控 ACCEPT_FREEZE 前不得实现；
2. IR1 + implementation ACCEPT 前不得执行真实 DE；
3. closeout 后立即停止等待主控裁决。

## Final Return Statement（逐字）

> V33 PASS，ER1 ACCEPT，Codex 主控 ACCEPT；已恰一次运行 30-call ensemble DE，
> 未运行 decoder、finite-control 或 successor；等待新 OpenSpec 与明确授权。
