# Proposal: formal-nonbinary-ldpc-v26-channel-informed-multilevel-de-gate

> Status: **RUN_COMPLETE — pass_target_f13**（2026-08-19；A02/F03 GF32+GF32 在 f=1.3 全收敛；
> 报告 docs/nbldpc-v26-channel-informed-multilevel-de-report-20260819.md）。 只做两种分层架构的
> channel-informed 的 multilevel MC-DE 门；不做大规模 degree 撞库、不做有限码、
> 不做 FER/MET/qualification/promotion。
> V25 closeout addendum 见 `formal-nonbinary-ldpc-v25-.../evidence/addendum_v26_closeout.md`。

## What

把 V25 得到的经验条件信道 `P(A|B, source, delay)` 正确地转换成**每一层的
posterior-message population**，然后检验 F01 与 F03 在固定小型 NB-LDPC 系综下距离
`f=1.3`（reconciliation efficiency）还有多远。

效率定义（代码与证据使用，单位 bits/symbol；`width = log2(q)` 为该层域宽）：

\[
f_i=\frac{\mathrm{leak}_i}{H_i},\qquad
\mathrm{leak}_i=(1-R_i)\log_2 q_i
\]

其中 `leak_i = m_i log2(q_i) / n` 为该层每符号公开泄漏的比特数。于是层码率满足

\[
R_i=1-\frac{f_i H_i}{\log_2 q_i}
\]

注意**不是** `f=R/H`、`R=f\cdot H`——那种写法把 bit/符号 与 归一化泄漏 混在一起，
会在有限码阶段算错码率与泄漏。上式为代码 `target_rate_layer` 所用的正确换算。

只测两种测试架构：

### A01 — F01 高域架构
```
原始1024-bin symbol
    ├─ L1: GF(512)，9 bit（MSB）
    └─ L2: GF(2)，1 bit residual（LSB）
```

### A02 — F03 中域架构
```
原始1024-bin symbol
    ├─ L1: GF(32)，高5 bit
    └─ L2: GF(32)，低5 bit
```

## Why

- 若某架构在 `f=1.3` 下所有 layer/source/confirm-seed 全部收敛（posterior entropy
  → ≤0.01 bit/symbol），则允许提出该架构的**有限码/构造** change（仍无 FER/
  qualification/promotion）。
- 若 `f=1.3` 失败但 `f=1.6/2.0` 通过：架构与 channel adapter 有效，当前固定
  degree-2 系综与目标仍有差距，下一步做 bounded degree optimization。
- 若直到 `f=2.0` 仍无完整架构通过：仅代表当前 posterior adapter + random-coefficient
  MC-DE + degree-2 concentrated-check 基线未收敛，不代表 multilevel NB-LDPC 理论不可行。

## Scope

- 从 V25 train `N_ab`（`channel_counts.npz`）或 C04 source-delta 模型构建真正逐样本的
  层条件 posterior `P(U_i | B, source, delay, U_<i)`；保留三个 source 独立信道与 Bob
  full side information；保留 ±1 正负方向；不把三个 source 平均成一个主信道。
- 扩展现有 MC-DE 内核（V14/V22/V24 只接受平移不变 `w[delta]`）以接受**任意 posterior
  population** 注入；GF(2)/GF(32)/GF(512)；随机非零 edge coefficient 的 GF 乘法
  permutation；true-symbol centering；bits/symbol entropy。
- 复用冻结 `nonbinary_field.py` 的 GF32/GF512 primitive polynomial 与 symbol
  encoding，不重写域运算。
- 只使用固定系综 `lambda={2:1.0}` + harmonic-exact concentrated check distribution
  生成 `rho`；不做 λ/ρ 大规模随机搜索。
- 在 `f ∈ {1.3, 1.6, 2.0}` 上小规模 screen（400 samples / 100 iter / 2 seeds），对
  每个架构最低通过 `f` 做五 seed confirmation（2000 samples / 200 iter）。
- 输出每个 architecture/layer/source/seed 的 entropy trace、rate、f 和终态。

## Out of scope（V26 不应做什么）

- 不进行 λ/ρ 大规模随机搜索；不撞库 degree。
- 不复用 V17 product channel；不把 layer channel 压成一个 averaged `w`。
- 不直接构造 finite parity-check matrix；不运行 EMS/FFT-QSPA finite decoder；不报告 FER。
- 不做 MET；不做 fresh/raw `.ttbin` 读取；不改变 factorization；不用 holdout 调参。
- 不 push。

## Decision states (M4 终态，仅允许以下之一)

- `pass_target_f13`
- `target_fail_slack_pass`
- `fixed_ensemble_no_convergence`
- `implementation_blocked_layer_channel_semantics`
- `resource_blocked`
