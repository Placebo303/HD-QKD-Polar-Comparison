# V26 Channel-Informed Multilevel DE Gate — Report (2026-08-19)

终止态：**pass_target_f13**

## 摘要

V26 把 V25 的经验条件信道 `P(A|B, source, delay)` 正确转换成每层的 posterior-message
population（`P(U_i | B, source, delay, U_<i)`），并把现有 MC-DE 内核扩展为接受任意
posterior population（GF2/GF32/GF512 + 随机非零 edge coefficient permutation +
true-symbol centering + bits/symbol entropy）。在固定 `lambda={2:1}` + harmonic-exact
concentrated checks 系综下检验两种架构离 `f=1.3` 多远。

**结论：A02（F03, GF32+GF32）在 f=1.3 下全部 layer × source × confirm-seed 收敛
（final mean entropy 0.00000 bits/symbol）。A01（F01, GF512+GF2）f=1.3 失败，但其
GF512 L1 层本身在 f=1.3 收敛；失败集中在 GF2 residual（L2）层（degree-2 系综下距
目标有差距；f=1.6 通过）。**

## 效率定义与目标码率（worst-source H）

### 效率定义

与代码 `target_rate_layer` 一致（单位 bits/symbol，`width = log2(q)` 为该层域宽）：

\[
f_i=\frac{\mathrm{leak}_i}{H_i},\qquad
\mathrm{leak}_i=(1-R_i)\log_2 q_i=\frac{m_i\log_2 q_i}{n},\qquad
R_i=1-\frac{f_i H_i}{\log_2 q_i}
\]

其中 `H_i` 为该层条件熵（bits/symbol），`m_i` 为该层校验行数、`n` 为块长。
**不是** `f=R/H`、`R=f\cdot H`（bit/符号 与归一化泄漏不能混淆）。

### 架构与目标码率（worst-source H）

| 层 | q | width | worst H | f=1.3 rate |
|---|---:|---:|---:|---:|
| A01 L1 GF512 | 512 | 9 | 0.41624778 | 0.93988 |
| A01 L2 GF2   | 2   | 1 | 0.41631494 | 0.45879 |
| A02 L1 GF32  | 32  | 5 | 0.02566205 | 0.99333 |
| A02 L2 GF32  | 32  | 5 | 0.80690067 | 0.79021 |

screen：72 DE calls（2 arch × 2 layer × 3 source × 3 f × 2 seed，n=400, iter≤100）。
confirmation：5-seed（26101..26105，n=2000, iter≤200）在每架构最低通过 f 上运行。

## M0 adapter 语义门（过）

- 每个 posterior 非负、归一化；GF512/GF32/GF2 域名正确。
- adapter entropy 与 V25 `H_i` 一致：max |ΔH| ≈ 5e-9 bits/symbol（容差 1e-3）。
- ±1 方向保留；1M/1p5M/2M 三 source 独立不合并；natural factorization 可逆；L2
  条件中真正包含已知 L1。
- → 未触发 `implementation_blocked_layer_channel_semantics`。

## M1 内核机制测试（全过）

- GF4/GF8 小型 brute-force check-node vs jitted WHT 系数核：maxerr ≈ 1e-17。
- all-one 系数退化：GF4/GF8 对 brute force，GF32/GF512 对 V14 已冻结无系数核，
  maxerr ≈ 1e-17。
- adapter 输入熵 == MC-DE iteration-0 熵（err=0）。
- 固定 seed 重放完全一致。
- GF2 BSC：与 V14 QSC 冻结核收敛一致 + noiseless 退化收敛。

## M2/屏幕结果

| (arch, layer) | f=1.3 | f=1.6 | f=2.0 |
|---|---:|---:|---:|
| A01 L1 GF512 | 6/6 | 6/6 | 6/6 |
| A01 L2 GF2   | **0/6** | 6/6 | 6/6 |
| A02 L1 GF32  | 6/6 | 6/6 | 6/6 |
| A02 L2 GF32  | 6/6 | 6/6 | 6/6 |

## M3 确认（5 seed）

- **A02 @ f=1.3：30/30 收敛**，final mean entropy 0.00000 bits/symbol。
- A01 @ f=1.6：30/30 收敛。

## 终态

**pass_target_f13**（best passing f: A01=1.6, A02=1.3）

- 允许提出 A02（GF32+GF32 / F03）的有限码/构造 change；仍无 FER/qualification/promotion。
- A01 的 f=1.3 失败集中在 GF2 residual（L2）；L1 GF512 本身在 f=1.3 收敛。固定
  degree-2 系综对低码率 binary residual 有差距，非路线失败；后续可做 bounded degree
  optimization 或在 L2 层改构。

## 证据

- `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v26_20260818/`
  - `run_02/`（**canonical**）：`RUN_MANIFEST.json`（role=canonical）、`m0_report.json` /
    `m1_report.json`、`screen_results.json` / `confirmation_results.json`（每
    layer/source/seed 的 entropy trace、rate、f）、`calls_summary.json` /
    `gate.json`（terminal=pass_target_f13）、`readonly_verify.json`（ok=true）。
  - `run_01/`（**deterministic repeat**）：科学结果与 canonical 逐字段一致（72 screen
    + 60 confirmation 全匹配，0 mismatch），`RUN_MANIFEST.json`（role=
    deterministic_repeat），只读 verifier `verify_run` = ok。
- **只读 verifier**（`verify_run`）：独立从 `channel_counts.npz` 重建 adapters，重跑
  M0/M1，重算全部 72 screen + 60 confirmation 调用、A02@f=1.3 30/30、rate/rho/seed/
  熵轨迹与终态，并与持久化产物逐项比对（run_01、run_02 均 0 mismatch）。
- **M1 修正（closeout）**：`adapter_input_entropy_matches_iter0` 现在真实进入
  MC-DE 首轮（`max_iter=1` + `record_channel_entropy`），校验 DE 实际消耗的信道熵
  与 adapter 独立抽样熵一致（err_replay=0，err_model≈0.009<0.03）；`gf2_bsc_reference`
  改为明确判定的 centered GF2 BSC：noiseless 必须收敛、可行性率（f=2.0, rate≈0.427）
  必须收敛、容量附近（f=1.0, rate≈0.714）必须正确判负（不再"双不收敛=agree"）。
- **source↔delay 显式元数据**：`SOURCE_METADATA`（1M/1p5M/2M → delay_used_ps
  −50/+50/+50、n_pairs 512000/708352/933120）写入 adapter、M0 detail 与
  `RUN_MANIFEST.json`。
- **24h 资源门实现**：`RESOURCE_LIMIT_SECONDS=24h`，`_run_gated_stage` 按 per-call
  累计 wall-clock，超限保存已完成调用并返回 `resource_blocked`；V26 实测
  screen≈44s + confirm≈112s，门未触发。
- 输入：V25 `channel_counts.npz`（run_04 或 fallback）；冻结 `nonbinary_field.py`。

## 禁止项遵守

未做 degree 随机搜索、有限码、FER、MET、fresh qual、raw `.ttbin`、public residual、
Alice-oracle、holdout 调参、push。
