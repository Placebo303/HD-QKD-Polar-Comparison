# FINAL_GATE — Binary Cascade 唯一生死门（冻结验收）

> 本文件为 `cascade-beta-optimal-path` 变更的**唯一验收口径**。与 `proposal.md`/`design.md`/`spec.md` 不一致时以本文件为准。旧 90 点 Pareto 口径已作废。

## 0. 一句话判决

在**完整 FIFO look-back + 小初始块 + 足量 passes** 的最有利条件下，若 binary Cascade 仍不能在独立 held-out 上同时满足 `FER<5% & β>0.9 & undetected==0`，则**正式退休 binary Cascade 主路线**。

## 1. 网格（12–18 点，FIFO 完整）

| 维度 | 取值 | 说明 |
|---|---|---|
| 信道 | `BER = 1%, 9.4%` | 双信道独立评估，禁止平均 |
| 初始块 `b0` | `4, 8, 16` bits | 16 为对照，4/8 为必测生死点 |
| 最大 passes | `6, 7, 8` | 至少覆盖 6 与 8；7 可选；去重后 12 点(6/8)或 18 点(6/7/8) |
| look-back | `FIFO 完整` | 所有已揭露 parity 均可回溯，不截断 |
| 块演进 | `b, 2b, 4b... ≤ n_bits/2` | 标准 Cascade 倍增，奇偶全覆盖 |
| Caps | `5s/frame, 100k events` | 继承 formal，超限记失败 |
| 样本 | `≥200 帧/点/信道` | 推荐 320 帧；种子预注册 |

执行优先级：`b=4/8 × passes=6/8 × 双 BER` 的 8 点为**必测最小集**；`b=16` 与 `passes=7` 为扩展对照（有资源则 18 点全测）。

## 2. 每点报告（分信道，失败帧 β 不计）

- `n_total, n_verified_success, n_verify_failed, n_undetected, n_resource_limit`
- `FER = 1 - n_verified_success/n_total`（undetected 单列，永不并入 success）
- `leak_parity, leak_bisection, leak_tag, leak_total`（transcript 求和；`leak_tag=64` 仅 success 帧）
- `leak_accepted_mean = mean(leak_total | verified_success)`
- `β_accepted = (frame_bits * h2(BER)) / leak_accepted_mean`，`frame_bits=640, h2(p)=-p log2 p -(1-p)log2(1-p)`；失败帧不参与 β
- `yield_effective = (1-FER) * mean((frame_bits - leak_total)/frame_bits | verified_success)`
- 同时输出 `leak_failed_mean` 仅作诊断，不得用于 β/yield

输出表：`final_gate_grid_results.csv`（IID）与 `final_gate_plane_correlation_results.csv`（位面相关性）同构。

## 3. 位面相关性模型（必做对照）

- 估计：真实 ttbin 冻结训练分片解 Gray 10 位平面，统计 `p_i = flips_i / bits_i, i=0..9`（按 source 分别或 pooled，二选一冻结并记录；推荐 pooled + per-source 双列披露）
- 生成：合成帧 64×10 bits，每 bit 按所属 `plane i` 以 `p_i` 翻转；plane 内 IID，plane 间非 IID
- 对照：同网格参数下 IID vs 位面相关性并列；位面相关性结果为真实性代理
- 产物：`p_i` 向量写入 `final_gate_manifest.json`，报告中披露 `h2` 与 `L_min` 计算所用 BER（IID 用标称 BER，位面相关性用 `mean(p_i)` 的等效 BER 或直接用 `sum_i h2(p_i)*n_i` 的精确 `L_min`，二选一冻结）

## 4. held-out 判定（独立数据，一锤定音）

- 数据：独立 held-out 分片（优先真实 ttbin held-out；若不可用则用 §3 位面相关性合成 held-out，需在 manifest 声明类型与来源）；与 `p_i` 估计、网格调试数据零重叠
- 评估：对 held-out 按最优网格点（或全网格，若宣称任一点过即 PASS 则需披露"选优"语义）执行 Cascade，统计双信道各自的 `FER, β_accepted, undetected`
- 阈值（同时满足）：
  1. `FER < 0.05`（1% 与 9.4% 双信道各自满足）
  2. `β_accepted > 0.9`（双信道各自满足，仅 accepted 帧）
  3. `undetected == 0`（全 held-out 零容忍）
- 判决：`FINAL_GATE_VERDICT = PASS` 当且仅当双信道同时满足三条件；否则 `RETIRE`
- 产物：`final_gate_heldout_verdict.json`（含每信道三条件布尔值与总判定）+ `FINAL_GATE_REPORT.md`

## 5. 退休语义

- 若 `b=4/8` + 完整 FIFO + 6–8 passes 在 held-out 上仍任一信道不满足阈值（或 IID 过但位面相关性不过），则 `RETIRE` — 正式退休 binary Cascade 主路线，不再作为主线投入；仅保留归档与新路线提案
- 不得通过放宽 `FER/β/undetected`、改用失败帧 β、跨信道平均、或追加扫描来规避 RETIRE
- RETIRE 仍需完成归档产物与 decision-log 记录

## 6. 产物清单（`comparison_bench/outputs_comparison/cascade_beta_final_gate/run_01/`）

- `final_gate_grid_results.csv`
- `final_gate_plane_correlation_results.csv`
- `final_gate_heldout_verdict.json`
- `final_gate_manifest.json`（seeds, p_i, h2, L_min, code/exec SHA, plan SHA, held-out 身份）
- `FINAL_GATE_REPORT.md`（分信道 FER/β/yield 表 + 判决陈述）
- `transcripts/`（可选，抽样 transcript 供审计，不强制全量）

## 7. 执行边界

- 不修改 `src/`/`experiments/`/`tools/`；不覆盖 `results/`；不新增重型依赖
- 测试隔离：test-only 路径必须显式传 fake runner，不得隐式进入生产 decoder
- 资源：单点 5s/frame 上限，总网格约 18*320*2 ≈ 11520 帧次，需预算门限与幂等续跑（失败保留，不重调）

## 8. 验收检查（pre-RESULT 必检）

- [ ] 网格覆盖 `b=4/8` + 完整 FIFO + 6/8 passes 双信道
- [ ] 每点报告含 FER/accepted leakage/β/yield 且失败帧 β 已隔离
- [ ] 位面相关性对照已执行且 `p_i` 已披露
- [ ] held-out 独立性可验证（与训练/调试零重叠）
- [ ] `undetected` 单列且为 0 时方为 PASS
- [ ] 判决为二元 `PASS/RETIRE`，无中间态
