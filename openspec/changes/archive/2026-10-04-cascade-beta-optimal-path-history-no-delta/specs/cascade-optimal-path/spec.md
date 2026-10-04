# Spec: cascade-optimal-path — FINAL_GATE 冻结规约

> 本 spec 已按 `FINAL_GATE.md` 重写；旧 90 点/Pareto 4 条 Requirement 作废归档。

## ADDED Requirements

### Requirement: 合成 Sanity 小网格（FIFO 完整）

The system SHALL 执行合成 sanity 网格 `BER ∈ {0.01, 0.094} × b0 ∈ {4,8,16} × max_passes ∈ {6,7,8}`（去重后 12–18 点，至少保证 `b=4/8 × passes=6/8 × 双 BER` 的 8 点必测），FIFO look-back = 完整，块演进 `b,2b,4b…≤n_bits/2`，caps 5s/frame、100k events。

- 每点每信道 ≥200 帧（推荐 320），种子预注册，独立 manifest
- 超限记 `resource_limit` 失败，不计入 success

### Requirement: 分信道报告与失败帧隔离

The system SHALL 对每网格点分信道独立报告：

- `FER = 1 - n_verified_success/n_total`，`undetected` 单列永不并入 success/FER 分子
- `leak_parity, leak_bisection, leak_tag, leak_total`（transcript 求和，`leak_tag=64` 仅 success 帧）
- `leak_accepted_mean = mean(leak_total | verified_success)`；`leak_failed_mean` 仅诊断
- `β_accepted = (frame_bits * h2(BER)) / leak_accepted_mean`，`frame_bits=640`，`h2(p)=-p log2 p -(1-p)log2(1-p)`；失败帧不得计入 β
- `yield_effective = (1-FER) * mean((frame_bits - leak_total)/frame_bits | verified_success)`

跨信道平均、失败帧 β 冒充有效、undetected 合并均为违规，verifier 必须拒绝。

### Requirement: 位面相关性复现对照

The system SHALL 在同构网格上执行位面相关性对照：从真实 ttbin 冻结训练分片估计 `p_i = P(flip|plane=i) i=0..9`，按 plane 的 `p_i` 生成合成帧（plane 内 IID，plane 间非 IID），披露 `p_i` 向量与 `L_min` 计算口径（`mean(p_i)` 等效 BER 或 `Σ h2(p_i)*n_i` 精确值）。

- IID 网格与位面相关性网格同构并列输出 `final_gate_grid_results.csv` / `final_gate_plane_correlation_results.csv`
- 若 IID 过但位面相关性不过，则以位面相关性为准

### Requirement: held-out 三条件判决与退休

The system SHALL 在独立 held-out 分片（与训练/调试零重叠，manifest 声明来源与 seeds）上执行最终判决：

- 对双信道各自计算 `FER, β_accepted, undetected`
- `PASS` 当且仅当双信道同时满足 `FER<0.05 & β_accepted>0.9 & undetected==0`；否则 `RETIRE`
- 输出 `final_gate_heldout_verdict.json`（`verdict ∈ {PASS, RETIRE}`）与 `FINAL_GATE_REPORT.md`
- 若 `b=4/8` + 完整 FIFO + 6–8 passes 在 held-out 上仍 FAIL（含位面相关性不过），则正式退休 binary Cascade 主路线；不得通过放宽阈值、改用失败帧 β、跨信道平均或追加扫描规避 RETIRE

## 产出契约

- 输出根 `comparison_bench/outputs_comparison/cascade_beta_final_gate/run_01/`（append-only）
- 必含：`final_gate_grid_results.csv`, `final_gate_plane_correlation_results.csv`, `final_gate_heldout_verdict.json`, `final_gate_manifest.json`, `FINAL_GATE_REPORT.md`
- 配置冻结：`comparison_bench/configs/cascade_final_gate.yaml`
