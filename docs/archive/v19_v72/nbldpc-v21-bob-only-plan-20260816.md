# NBLDPC V21 Bob-Only Decoder Validation Plan (2026-08-16)

Status: PLAN — frozen task packet, pending main-thread acceptance

## 0. 背景与触发条件
V20 审查确认：`31/64` 是 oracle-aided best-of cascade 上界，`40/96` 是 top-4
oracle list coverage；两者都不是可执行解码器 FER。standalone bounded4 约
`30/64`（summary 陈述）是唯一接近 Bob-only 的策略，但没有独立 raw/verify 包。
本计划只做**科学语义修正 + Bob-only 验证**，不继续扩样 OSD/top-K，不进入
qualification/promotion。

## 1. 目标
在 q=1024、f≤1.3 的同一诊断信道点上，用**Bob-only 可执行策略**得到可复现的
FER，并与 oracle 上界明确区分。若所有 Bob-only 策略仍 FER≥0.45，则冻结短块
OSD/top-K 分支为 `scientific_not_ready`，转入 V22 结构化构造路线。

## 2. 硬约束（V21 frozen contract）
- 候选生成与选择阶段**不得访问 Alice**；只允许 `(field, matrix, syndrome,
  channel_prior_w, max_iter, codebook)` 等 Bob 可见量。
- Alice 只允许出现在最终离线指标计算中。
- 完整泄漏必须包括所有公开/验证 bits：
  `f_total = (syndrome_bits + public_bits + verification_bits) / (n * H_full)`。
- 全新 synthetic seeds，不复用 V19/V20 的 64/96 帧调参集。
- 不修改 frozen `src/ experiments/ tools/ results/`；新代码只放
  `comparison_bench/`；证据 additive；本地 commit，不 push。
- 每轮更新 CURRENT_TASK / AGENT_HANDOFF / AGENT_PROJECT_MEMORY。

## 3. Phase 0：V20 证据修正与收口
1. 新增 audit addendum，不覆盖旧证据：
   - `31/64` → `oracle_aided_best_of_cascade_upper_bound`；
   - `40/96` → `top4_oracle_list_coverage`；
   - standalone bounded4 `30/64` → `unverified_bob_only_estimate`；
   - V01 → `counting_only_verifier`（非语义验收、非 strict replay）。
2. 统一 OpenSpec V20 status：
   `CONCLUDED_PENDING_SCIENTIFIC_CORRECTION_AND_ARCHIVE`。
3. decision-log 追加 V20 closeout。
4. 语义修正完成后再移动 V20 到 archive。

## 4. Phase 1：V21 Bob-only 策略验证
新 change：`formal-nonbinary-ldpc-v21-bob-only-selector-validation`。

### 4.1 允许文件
- 新增：`comparison_bench/src/comparison_bench/formal_ir/nonbinary_v21_bob_only.py`
- 新增 CLI：`comparison_bench/src/comparison_bench/cli/run_v21_bob_only.py`
- 新增测试：`comparison_bench/tests/test_nonbinary_v21_bob_only.py`
- 输出根：`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v21_20260816/`

### 4.2 策略定义（固定，不允许运行中改）
- **S0 BP-only**：只使用 FFT-QSPA 的 `e_hat`；若 `e_hat is None` 或
  syndrome 不一致则 `decode_failed`；否则接受 BP 候选。Bob-only。
- **S1 bounded4-only**：每帧始终运行 `bounded_weight_ml_decode(max_weight=4)`；
  接受其唯一候选。Bob-only。
- **S2 BP-first-fallback-bounded4**：若 BP 返回 syndrome-consistent 候选则接受
  BP 候选；否则运行 bounded4 并接受其候选。这是 V20 cascade 的合法 Bob-visible
  版本（fallback 条件只用 syndrome_ok，不用 Alice）。

### 4.3 指标（分离记录）
- `exact_correct`（单选中候选真实 FER）
- `exact_mismatch` / `decode_failed`
- `candidate_list_contains_alice`（仅诊断）
- `alice_rank`（仅诊断）
- `syndrome_bits`、`public_bits`、`verification_bits`
- `f_plain` 与 `f_total`
- `runtime_s`

### 4.4 执行矩阵（一次执行）
- q=1024，n∈{64, 80}，m/n=0.0625（f_plain≈1.136）。
- 新 seeds：`2026091001..2026091008`（每 seed 8 frames）。
- S0/S1/S2 在同一帧集合上各跑一次；不得重跑/调参。
- 输出每策略独立包 + 汇总包。

### 4.5 语义 verifier（新增）
- 静态检查：解码函数签名不接受 `alice`；候选选择函数只接受 Bob 可见参数。
- 运行时注入检查：用 `unittest.mock` 替换 Alice 数组并确认候选集合逐位不变。
- 指标阶段才允许引用 Alice。

## 5. Phase 2：停止门
- 若 S0/S1/S2 在 ≥64 全新帧上的 Bob-only FER 全部 ≥0.45：
  - 冻结短块 OSD/top-K 路线为 `scientific_not_ready`；
  - 不进入 fresh qualification；
  - 更新 decision-log/memory，转 Phase 3。
- 若任一策略 FER < 0.45 且 f_total≤1.3：
  - 记录为 `bob_only_diagnostic_success`（仍 diagnostic_only）；
  - 再评估是否立项 fresh development。

## 6. Phase 3：新码族路线（停止门触发后）
新 change：`formal-nonbinary-ldpc-v22-structured-construction`。
1. 先做 paper-faithful MET/protograph 或 SC-LDPC 参考复现 + 结构化信道 DE gate；
2. DE 通过后才构造 n≥512/1024 有限码；
3. 所有 blind/retry/public verification bits 计入 f；
4. 只有 Bob-only FER 显著下降且 f_total≤1.3，才进入 fresh development。

## 7. 验收项（stable IDs）
- P0-1：V20 addendum 文件存在且旧证据未改；
- P0-2：V20 三文件 status 统一；
- P0-3：decision-log 有 V20 closeout；
- P1-1：V21 模块/CLI/测试实现且测试通过；
- P1-2：语义 verifier 通过（Bob-only 检查）；
- P1-3：执行矩阵完成，输出指标分离；
- P2-1：停止门判定并记录。
