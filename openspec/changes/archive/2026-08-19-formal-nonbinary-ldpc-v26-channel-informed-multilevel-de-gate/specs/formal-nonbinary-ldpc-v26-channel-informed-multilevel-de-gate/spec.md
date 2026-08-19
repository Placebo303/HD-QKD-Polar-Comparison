# Spec: formal-nonbinary-ldpc-v26-channel-informed-multilevel-de-gate

> Status: RUN_COMPLETE delta spec for V26 channel-informed multilevel DE gate (terminal pass_target_f13).

## Requirements

### R1: Layer-conditional posterior adapter
- 对 F01 (GF512+GF2) 与 F03 (GF32+GF32) 的 natural labeling（MSB→LSB），为每层
  构造逐样本 posterior `P(U_i | B, source, delay, U_<i)`。
- Posterior 必须非负、归一化，符号域正确（GF2/GF32/GF512）。
- Adapter 平均 posterior entropy 与 V25 layer entropy 在 `1e-3` bit/symbol 内一致。
- ±1 正负方向分别保留；三个 source 保持独立；1M 与 1p5M/2M population 不静默合并。
- 某层 posterior 若以 `1e-3` 之外的偏差偏离 V25 H，M0 视为 FAIL。

### R2: MC-DE receives arbitrary posterior population
- 不接受平移不变 `w[delta]` 作为唯一输入；必须能注入任意 `(n,q)` posterior
  population。
- 支持 GF(2)、GF(32)、GF(512)；复用冻结 `nonbinary_field.py` 域。
- 随机非零 edge coefficient 的 GF 乘法 permutation 应用到消息下标。
- true-symbol centering：把每个 sample 的真实层符号移到下标 0。
- entropy 以 bits/symbol 计（= base-q entropy × log2(q)）。

### R3: Fixed ensemble screen
- 只使用 `lambda = {2: 1.0}` 与 harmonic-exact concentrated check distribution。
- 测试 `f ∈ {1.3, 1.6, 2.0}`，2 arch × 2 layer × 3 source × 2 seeds = 72 calls。
- screen：n_samples=400, max_iter=100, seeds=[26001,26002], tol=0.01 bits, streak=20。
- 效率换算严格采用 `f_i = leak_i / H_i`、`leak_i = (1-R_i) log2(q_i)`、
  `R_i = 1 - f_i H_i/log2(q_i)`（bits/symbol；width=log2(q)）。**禁止**使用
  `f=R/H`、`R=f·H`——那是错误换算，会在有限码阶段错算码率与泄漏。

### R4: Confirmation
- 只对每个架构 screen 中最低通过 f 运行：n_samples=2000, max_iter=200,
  seeds=[26101..26105]。
- 通过 = 两层都过、三 source 都过、五 seed 都过、无错误/非有限值、final mean
  entropy ≤0.01 bits/symbol 连续 20 轮、每层单独留证。
- screen 无通过点则不运行 confirmation。

### R5: Terminal state
- 仅允许 `pass_target_f13` / `target_fail_slack_pass` / `fixed_ensemble_no_convergence` /
  `implementation_blocked_layer_channel_semantics` / `resource_blocked`。

### R6: Prohibitions
- 不做 λ/ρ 大规模随机搜索；不撞库 degree；不复用 V17 product channel；不把 layer
  channel 压成 averaged `w`；不构造 finite parity-check matrix；不运行 finite
  decoder；不报告 FER；不做 MET；不读 fresh/raw `.ttbin`；不改变 factorization；
  不用 holdout 调参；不 push。
