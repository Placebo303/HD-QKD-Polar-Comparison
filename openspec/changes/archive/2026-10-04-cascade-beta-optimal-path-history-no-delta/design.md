# Design: cascade-beta-optimal-path — FINAL_GATE

> 权威验收见 `FINAL_GATE.md`。本文件为实现约束与数据契约的展开；与 FINAL_GATE 不一致时以 FINAL_GATE 为准。旧 §4 "24→90 点/Pareto" 已作废。

## 1. 方法与边界

- 只读外层实现：仅在 `comparison_bench/` 内新增/复用最小脚本，不改 `src/`/`experiments/`/`tools/` 冻结基线
- 复现性：固定随机种子、`run_manifest.json` 记录 code/exec 哈希、`ACCEPTED_PLAN_SHA` 绑定，held-out 分片冻结
- 输入：合成帧（IID 或位面相关性生成）+ 逻辑与 `cascade_formal_v1` 同构的 Cascade 执行器（FIFO 完整、块大小可配、passes 可配）；不引入新 decoder 族
- 幂等：每点独立 manifest，失败保留为证据，不重调重跑

## 2. 网格：12–18 点小生死门

- 维度：`BER ∈ {0.01, 0.094}`（独立信道，不可平均）× `b0 ∈ {4,8,16}`（初始块 bits）× `max_passes ∈ {6,7,8}`（或统一 8，见 FINAL_GATE 变体）
- 去重后约 12–18 点：2×3×2=12（6/8 passes）或 2×3×3=18（6/7/8 passes）；默认执行 18 点，资源不足时至少保证 12 点（4/8 ×6/8 passes 为必测，16 为对照）
- 固定约束：FIFO look-back = 完整（所有已揭露 parity 均可回溯参与纠错），块大小按 Cascade 倍增规则演进（`b, 2b, 4b...` 上限 `n_bits/2`），每 pass 奇偶全覆盖
- Caps：继承 formal `5s/frame, 100k events`；超限记为 `resource_limit` 失败，不计入 success
- 每点样本：每信道 ≥200 帧（推荐 320 帧，约 2× 正式 32 帧规模的十倍，便于 FER<5% 估计）；种子预注册、不可复用 held-out 种子

## 3. 报告口径（每信道独立，禁止跨信道平均宣称）

- 帧定义：`frame_bits = n_symbols * log2(q) = 64 * 10 = 640 bits`
- 状态机（冻结）：`verified_success`（Toeplitz 64-bit tag 校验通过且纠后与 Alice 完全一致）、`verify_failed`（tag 未过或纠后不一致）、`undetected`（tag 通过但纠后不一致，哈希碰撞，单列隔离，永不并入 success/FER 分子）、`resource_limit`/`aborted`
- FER：`FER = (verify_failed + undetected + resource_limit) / total`，或等价 `1 - verified_success/total`；undetected 单独列，不可合并
- 泄漏分解（仅 accepted 帧计入 β/yield）：
  - `leak_parity` — 初始块 parity 揭露
  - `leak_bisection` — 二分纠错 parity 揭露
  - `leak_tag` — Toeplitz tag 64 bits（仅 verified_success 帧计入）
  - `leak_total = leak_parity + leak_bisection + leak_tag`，transcript 有序事件求和
  - `leak_accepted_mean = mean(leak_total | verified_success)`；失败帧的 leak 仅作诊断列，不参与 β
- β（冻结公式）：
  - 理论最小 `L_min = frame_bits * h2(BER)`，`h2(p) = -p log2 p - (1-p) log2(1-p)`
  - `β_accepted = L_min / leak_accepted_mean`（∈(0,1]，越高越接近容量；与 `f = 1/β` 互为倒数）
  - Gate 阈值 `β>0.9` 等价 `f < 1.111...`；**失败帧不计入 β 分子分母**，禁止"全帧平均 β"口径
- Effective yield（仅 accepted 帧产出）：
  - `yield_per_accepted = (frame_bits - leak_total) / frame_bits`
  - `yield_effective = (1 - FER) * mean(yield_per_accepted | verified_success)`，等价 `mean(max(0, frame_bits - leak_total) * success_indicator) / frame_bits` 的帧平均
  - 单位 bits/frame 与 fraction 双列输出，不得用高 yield 掩盖高 FER

## 4. 位面相关性模型（非 IID 对照）

- 目标：检验"IID BER 下的 Cascade 成功是否在真实位面相关信道上消失"
- 估计：从真实 ttbin 冻结训练分片（非 held-out）解 Gray 10 位平面，统计 `p_i = P(flip | plane=i) = flips_i / bits_i`，`i=0..9`，按 source（1M/1p5M/2M）分别估计或 pooled 估计（冻结其一并记录）
- 生成：同网格参数下，合成帧每 bit 按所属 plane 的 `p_i` 独立采样翻转（plane 内 IID，plane 间非 IID）；帧结构保持 64 symbols ×10 bits
- 对照：同种子索引下输出 IID 网格 vs 位面相关性网格的并列结果表；位面相关性结果为真实性代理，IID 仅作 sanity
- 禁止：用单一 BER 的 IID 翻转冒充真实信道

## 5. held-out 判定与退休语义

- held-out：独立于训练统计与开发调试的冻结分片（真实 ttbin 或按 §4 位面模型生成的合成 held-out，二选一冻结并在 manifest 中声明；推荐真实 ttbin held-out 若可用，否则位面相关性合成 held-out 作为保守代理）
- 判定（同时满足为 PASS）：
  1. `FER < 0.05`（每信道独立判定，1% 与 9.4% 均需满足；任一不满足即判定失败）
  2. `β_accepted > 0.9`（每信道，仅 accepted 帧）
  3. `undetected == 0`（全 held-out 帧中零容忍）
- 输出：`FINAL_GATE_VERDICT ∈ {PASS, RETIRE}`，按信道分列 + 总判定；PASS 仅当双信道同时 PASS
- 退休：任一信道在 `b=4/8` + 完整 FIFO + 6–8 passes 下仍不满足三条件，即 `RETIRE` — 正式退休 binary Cascade 主路线，后续不再投入主线资源；仅允许归档与新路线提案

## 6. 产物与路径

- 输出根（append-only）：`comparison_bench/outputs_comparison/cascade_beta_final_gate/run_01/`（禁止覆盖既有 `results/`）
- 核心产物：
  - `final_gate_grid_results.csv`（每行一网格点：ber, b0, passes, fifo, n_frames, verified_success, fer, leak_*_accepted, beta_accepted, yield_effective, undetected）
  - `final_gate_plane_correlation_results.csv`（同构，位面相关性网格）
  - `final_gate_heldout_verdict.json`（held-out 三条件与总判定）
  - `final_gate_manifest.json`（seeds, p_i 向量, h2, L_min, code/exec SHA, plan SHA）
  - `FINAL_GATE_REPORT.md`（含 FER/β/yield 分信道表与 RETIRE/PASS 结论）
- 依赖：`numpy, pandas, pyyaml` 已有依赖，不新增重型依赖

## 7. 实现契约（给 coder-fast）

- 新增/复用最小模块：`comparison_bench/src/comparison_bench/methods/cascade_final_gate.py`（或复用 `cascade_formal_v1` 执行器，仅暴露 `b0/passes/fifo` 参数）
- 配置：`comparison_bench/configs/cascade_final_gate.yaml`（网格、seeds、p_i、caps 冻结）
- 测试：T0 编译/导入 + T1 小网格 smoke（每信道 4 帧）+ 公式单测（h2/β/yield/undetected 隔离），`pytest -p no:cacheprovider`
- 禁止：SHA/原子写/重试框架/通用 benchmark 抽象；失败即保留证据，不静默重跑
