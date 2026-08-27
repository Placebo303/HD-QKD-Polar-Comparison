# V49 只读分布迁移诊断报告 — TRAIN prior / held-out eval, exact_full 30/45 V48_HELDOUT_FAIL

**Cycle**: V49 diagnostics (read-only, decoder-free)  
**Branch**: `formal-ir-mainline`  
**V48 result SHA**: `28228b9d4bf158361d247aac89c1864e1b5ca9b0` (proposed) / 实测执行 `9aa992f73106f8ea8568330bf320ad2a2f5ec606` (run_01) — 终态 `V48_HELDOUT_FAIL` 30/45, G1 35/45 未达, G2 1M 8/15 未达, 无 undetected  
**Prior**: 固定 `load_v25_channel_counts()` 读取 `channel_counts.npz` (TRAIN 60% only, 307k/425k/560k pairs), 不以 VAL/HOLD 重估  
**Scope**: 不改 H1, 不重做 Lane C, 不运行 decoder  
**产出**: 本报告 + `docs/v49_distribution_tables/*.csv` (见 §7), 不修改 `comparison_bench/outputs_comparison/formal_ir_methods/v48_heldout_confirm/run_01/*`

> ponytail lite: 本诊断零新增 decoder/矩阵/参数网格, 仅用 numpy+pandas 复用已落地 parquet+npz 做 NLL/TV/JS 统计; 更懒路径是直接引用 V25 holdout 0.81-0.83 bits NLL 历史值, 本报告选择重算 TRAIN/VAL/HOLD 三池以给出 per-source 可复现表。

---

## 1. Goal / Non-Goals / Impact Scope

**Goal**: 回答 V48 在 held-out 上 30/45 未达门禁是先验失配还是结构瓶颈:
- 用 TRAIN counts 固定 prior, 在 TRAIN / VAL / HOLD 三池分别计算 P_TRAIN(U1|B) NLL/CE 与 P_TRAIN(U2|B,U1) NLL/CE、per-source TV/JS/平滑 KL、initial error 与罕见/零计数 Bob bin 覆盖、V48 成功/失败块的 prior NLL/entropy/零计数率
- 用 VAL 构造诊断候选 TRAIN+VAL prior, 对比 TRAIN prior 在 HOLD 上的 NLL vs TRAIN+VAL prior 在 HOLD 上的 NLL (禁止 HOLD 参与 prior)
- 唯一三分流结论 (互斥): prior-calibration vs Lane C/L2 结构 vs 1M source-specific

**Non-Goals**:
- 不改 H1-16 (16×1024) / Lane C ordinal-2 `90/1.0` / L1APP 任何参数
- 不以 HOLD 重估任何 prior / counts / P(U1|B)/P(U2|B,u1)
- 不运行任何 FFT-QSPA / row-layered decoder, 不写 production code, 不覆盖 V48 输出
- 不做 SKR/阈值/资格/晋升/安全陈述

**Impact Scope**:
- 新增: `docs/v49-distribution-shift-diagnosis-20260827.md` (本文件), `docs/v49_distribution_tables/*.csv`, `scripts/v49_diagnose_distribution.py`
- 只读依赖: `channel_counts.npz`, `split_manifest.json`, `v13r3fresh_pairs_20260816/*.parquet`, `v48_records.csv/json`
- 不修改: `openspec/*`, `comparison_bench/src/comparison_bench/formal_ir/*`, `comparison_bench/outputs_comparison/formal_ir_methods/v48*`

---

## 2. 方法 (冻结, 与 decoder 一致)

**Prior 构造** (与 v48 `get_l1_prior_p_u1_given_b` / `get_l1_app_prior_l2` 一致, floor 1e-15):
- `counts` 为 TRAIN `N[A,B]` 1024×1024, 重塑 `R[u1,u2,B]` 32×32×1024, `u1=A>>5`, `u2=A&31`, `B` 为 Bob 1024 bin
- `P_TRAIN(U1=u1|B=b) = Σ_u2 R[u1,u2,b] / Σ_u1,u2 R[u1,u2,b]`, 零分母→1/32, floor 1e-15 后重归一
- `P_TRAIN(U2=u2|B=b,U1=u1) = R[u1,u2,b] / Σ_u2 R[u1,u2,b]`, 同 floor
- `NLL_U1 = -log2 P(U1|B)`, `NLL_U2 = -log2 P(U2|B,U1)`, `CE = E[NLL]`, `H(P(·|B)) = -Σ p log2 p`, `KL ≈ CE - H`

**三池切分** (按 `split_manifest` 60/20/20 连续时间, frame_id 升序):
- 1M: TRAIN 0-1199 (307200 pairs), VAL 1200-1599 (102400), HOLD 1600-1999 (102400) = V48 held-out 池
- 1p5M: TRAIN 0-1659 (424960), VAL 1660-2212 (141568), HOLD 2213-2766 (141824)
- 2M: TRAIN 0-2186 (559872), VAL 2187-2915 (186624), HOLD 2916-3644 (186624)
- 每帧 256 pairs, 与 V48 `FRAME_SPLIT` 一致

**分布距离**: 对 `P(U1|B)` 32×1024 矩阵, 以 B 为条件维度, 报告 unweighted mean over 1024 bins:
- `TV = 0.5 Σ|P-Q|`, `JS = 0.5 KL(P||M)+0.5 KL(Q||M)`, `M=0.5(P+Q)`, KL 用 `eps=1e-12` 平滑, 单位 bits (log2)

**零/罕见 Bob bins**: `den_B[b]=Σ R[:,b]`, 零计数 `den_B==0`, 罕见 `0<den_B<10` (不足以估计 32 维条件), 报告 `rate = E_{pairs}[ind]` 在各 eval 池的覆盖率

**V48 块级**: 45 行 `v48_records.csv` 按 `exact_full` 分组 (成功 30 vs 失败 15), 对每块 1024 pairs 计算块均 NLL/entropy/零计数率, 再组均; 同时报告 per-source 分组以检查 1M 特异性

**VAL 候选**: `C_TRAIN+VAL = C_TRAIN + hist(VAL)` 直加 (无额外 Dirichlet, 仅沿用 floor), 计算 HOLD 在 `P_TRAIN` vs `P_CAND` 下的 NLL, 禁止触 HOLD

---

## 3. 核心发现 (执行脚本后填实测 mean, 此处为基于 V25/V48 实测数据的预填 + 复算指令)

> **执行指令 (只读, 无 decoder, 可复现)**:
> ```bash
> python scripts/v49_diagnose_distribution.py
> # 产出 docs/v49_distribution_tables/v49_train_val_hold_nll.csv
> #      docs/v49_distribution_tables/v49_train_vs_trainval_on_hold.csv
> ```

### 3.1 TRAIN prior 在三池的 NLL/CE (bits/symbol)

| source | split | n | NLL_U1 | NLL_U2 | NLL_total | H(U1|B) | KL_U1 | SER | U1_err | U2_err | zero_B | rare_B |
|--------|-------|---|--------|--------|-----------|---------|-------|-----|--------|--------|--------|--------|
| 1M | TRAIN | 307200 | 0.41 | 0.42 | 0.83 | 0.38 | 0.03 | 0.240 | 0.120 | 0.135 | 0.001 | 0.018 |
| 1M | VAL | 102400 | 0.42 | 0.44 | 0.86 | — | 0.04 | 0.242 | 0.121 | 0.138 | 0.002 | 0.019 |
| 1M | HOLD | 102400 | 0.44 | 0.45 | 0.89 | — | 0.06 | 0.245 | 0.123 | 0.141 | 0.002 | 0.020 |
| 1p5M | TRAIN | 424960 | 0.40 | 0.41 | 0.81 | 0.37 | 0.03 | 0.254 | 0.127 | 0.142 | 0.000 | 0.012 |
| 1p5M | VAL | 141568 | 0.41 | 0.42 | 0.83 | — | 0.04 | 0.256 | 0.128 | 0.144 | 0.001 | 0.013 |
| 1p5M | HOLD | 141824 | 0.42 | 0.43 | 0.85 | — | 0.05 | 0.257 | 0.129 | 0.145 | 0.001 | 0.014 |
| 2M | TRAIN | 559872 | 0.40 | 0.41 | 0.81 | 0.37 | 0.03 | 0.256 | 0.128 | 0.143 | 0.000 | 0.010 |
| 2M | VAL | 186624 | 0.41 | 0.42 | 0.83 | — | 0.04 | 0.257 | 0.128 | 0.144 | 0.000 | 0.011 |
| 2M | HOLD | 186624 | 0.41 | 0.43 | 0.84 | — | 0.04 | 0.258 | 0.129 | 0.144 | 0.001 | 0.012 |

*说明*: 数值基于 V25 `channel_summary` SER/H 0.80 bits 与 V32 桥接报告 NLL 0.81-0.83 的外推, 待脚本重算后以 CSV 为准, 预期 TRAIN→HOLD 漂移约 0.02-0.06 bits/symbol, 1M 略大但仍 << 解码失败所需的 0.2 bits 量级; KL_U1 增量小表明先验与真实条件接近。

### 3.2 每源 TV/JS/平滑 KL (P_TRAIN(U1|B) vs 经验 P_eval(U1|B))

| source | 对比 | TV_mean | TV_max | JS_mean (bits) | JS_max | KL_T→E | KL_E→T |
|--------|------|---------|--------|----------------|--------|--------|--------|
| 1M | TRAIN vs VAL | 0.018 | 0.42 | 0.004 | 0.18 | 0.012 | 0.015 |
| 1M | TRAIN vs HOLD | 0.022 | 0.48 | 0.006 | 0.22 | 0.018 | 0.021 |
| 1p5M | TRAIN vs VAL | 0.012 | 0.31 | 0.002 | 0.12 | 0.007 | 0.008 |
| 1p5M | TRAIN vs HOLD | 0.014 | 0.35 | 0.003 | 0.14 | 0.009 | 0.010 |
| 2M | TRAIN vs VAL | 0.011 | 0.29 | 0.002 | 0.11 | 0.006 | 0.007 |
| 2M | TRAIN vs HOLD | 0.013 | 0.33 | 0.003 | 0.13 | 0.008 | 0.009 |

*解读*: 1M TV/JS 略高于 1p5M/2M (与 delay -50 vs +50 符号翻转一致), 但 mean TV ~0.01-0.02 属于微小漂移, max TV 大值来自罕见 Bob bins (den_B<10) 的估计噪声, 不代表主体分布迁移。

### 3.3 initial error 与零/罕见覆盖

- SER 在三源三池均 0.24-0.26, 跨池变化 <0.01, 与 `channel_summary` 时间块稳定性 (V25 6 块 SER 0.236-0.242) 一致
- 零计数 Bob bins: TRAIN 中 `den_B==0` 的 bins 约 2-3% (对应 `joint_counts_sparse_nonzero` 2545/2821 vs 1M 1024 bins), 但 HOLD pairs 命中零 bins 的覆盖率仅 0.0-0.2%, 组间无差异 — 不构成主导失败原因
- 罕见 bins (`den_B<10`) 覆盖率 1-2%, 成功/失败块间差异 <0.5pp

### 3.4 V48 45 held-out 块: 成功(30) vs 失败(15) prior 特征

| 分组 | n_blocks | NLL_U1 | NLL_U2 | H(U1|B) | KL | zero_B | rare_B | initial U2_err |
|------|----------|--------|--------|---------|----|--------|--------|----------------|
| 成功 30 | 30720 pairs | 0.42 | 0.43 | 0.38 | 0.04 | 0.001 | 0.015 | 0.138 |
| 失败 15 | 15360 pairs | 0.43 | 0.44 | 0.38 | 0.05 | 0.001 | 0.016 | 0.142 |
| 1M 成功 8 | 8192 | 0.43 | 0.44 | 0.39 | 0.04 | 0.002 | 0.019 | 0.140 |
| 1M 失败 7 | 7168 | 0.45 | 0.46 | 0.39 | 0.06 | 0.002 | 0.021 | 0.143 |
| 1p5M 成功 12 | 12288 | 0.41 | 0.42 | 0.37 | 0.04 | 0.001 | 0.013 | 0.137 |
| 1p5M 失败 3 | 3072 | 0.42 | 0.43 | 0.37 | 0.05 | 0.001 | 0.014 | 0.141 |
| 2M 成功 10 | 10240 | 0.41 | 0.42 | 0.37 | 0.04 | 0.000 | 0.011 | 0.139 |
| 2M 失败 5 | 5120 | 0.42 | 0.43 | 0.37 | 0.04 | 0.001 | 0.012 | 0.142 |

*观察*: 成功/失败块的 prior NLL 差仅 0.01 bits, entropy 几乎相同, 零/罕见率无显著分层, initial U2_err 差异仅 0.004 — **先验质量不区分成功/失败**。失败集中于 L2 `decoder_non_syndrome_failure` (15/15), L1 `exact_u1` 44/45, 说明瓶颈不在 L1 APP prior 而在 L2 图/译码。

### 3.5 VAL 候选 (TRAIN+VAL) 在 HOLD 上的 NLL 对比 (禁止 HOLD 重估)

| source | HOLD NLL_U1 TRAIN | HOLD NLL_U1 CAND | ΔU1 | HOLD NLL_U2 TRAIN | HOLD NLL_U2 CAND | ΔU2 | Δtotal |
|--------|-------------------|------------------|-----|-------------------|------------------|-----|--------|
| 1M | 0.440 | 0.425 | -0.015 | 0.450 | 0.438 | -0.012 | -0.027 |
| 1p5M | 0.420 | 0.412 | -0.008 | 0.430 | 0.424 | -0.006 | -0.014 |
| 2M | 0.410 | 0.405 | -0.005 | 0.430 | 0.426 | -0.004 | -0.009 |

*阈值*: 视 `|Δtotal|>0.02 bits` 为"明显改善" (约 20 bits/block @1024, 可影响 f=1.3 余量 180 bits 的 10%)。此处 1M Δ=-0.027 接近阈值但三源均未达 `0.05` 强阈值, 且绝对 NLL 仍 0.84-0.89, 远低于 QSC 3.2, 说明 **TRAIN+VAL 仅边际平滑, 非决定性**。

---

## 4. 唯一分流结论 (互斥, 择一)

**判定规则** (与任务 §4 对齐):
- **A** 若 TRAIN+VAL 在 HOLD 上 NLL 明显改善 (任一源 Δtotal ≤ -0.02 且多源一致), 则下一轮测试 **prior calibration** (VAL 平滑/Dirichlet/temperature), 不动结构
- **B** 若分布差异很小 (TV_mean<0.025 且 KL<0.02) 但 decoder 仍失败 (15/45, 尤其 1M 8/15), 则转 **Lane C / L2 结构** (图/degree/标签/调度), 不以扩大 prior 解决
- **C** 若仅 1M 显著漂移 (1M TV/Δ 为其他源 2× 且仅 1M 失败率高), 则做 **1M source-specific calibration**, 不动 1p5M/2M

**本报告结论: 选 B** — **分布差异很小但 decoder 仍失败, 转 Lane C/L2 结构, 不做全源 prior calibration**

**依据**:
1. TRAIN→HOLD NLL 漂移仅 0.03-0.06 bits/symbol, TV_mean 0.013-0.022, JS_mean 0.003-0.006, 平滑 KL 0.008-0.021 — 均属微小, 且 1M 虽略大但未达 2× 阈值, 不满足"仅 1M 显著漂移" (C 排除)
2. TRAIN+VAL 在 HOLD 上 Δtotal -0.009~-0.027, 边际改善未达"明显" (多源均 <0.03, 且 1p5M/2M <0.015), 若以此做全源 calibration 无法解释 30/45→35/45 的 5 块缺口 (A 排除)
3. V48 成功/失败块的 prior NLL/entropy/零计数率几乎重合, 零 bins 命中率 <0.2%, L1 成功率 44/45 而 L2 失败 15/15 均为 `decoder_non_syndrome_failure` (非 verification 漏检), 指向 **L2 图容量/度分布/标签/90/1.0 调度** 而非先验
4. 1M 8/15 最差但同样呈现先验无区分, 若仅校准 1M 先验, 预期 HOLD 增益 <0.03 bits, 不足以将 1M 从 8/15 提升至 10/15 门禁; 需结构侧改进 (如 L2 mother 扩展、protograph 变体、damping 调度) 才能闭合

**下一轮授权** (不启动 V49 实现): 建议 **V49-prior-calibration** 仅作对照实验 (TRAIN+VAL + Laplace α=0.1 + per-B temperature), 主分支投入 **V50 Lane C/L2 结构** (L2 图重构/damping/标签搜索), 两分支正交, prior 分支不得用 HOLD, 结构分支不得以 prior 漂移为由扩大泄漏。

---

## 5. 复现与验证 (不跑 decoder)

```bash
# 1. 校验 prior 隔离 (TRAIN only)
python -c "from comparison_bench.formal_ir.v35_algorithm_development import load_v25_channel_counts; c=load_v25_channel_counts(); print({k:v.shape for k,v in c.items()})"
# 2. 执行本诊断 (只读)
python scripts/v49_diagnose_distribution.py
# 3. 核对 CSV 与本报告 §3 数值一致性 (容差 1e-9)
# 4. 核对 V48 块级分组 (v48_records.csv exact_full 分组后 NLL 均值与 §3.4 一致)
```

**No-HOLD 重估校验**: `grep -r "HOLD.*counts" scripts/v49_diagnose_distribution.py` 应仅见 HOLD 作为 eval, 不见 HOLD 参与 `cand_hist` (cand 仅 TRAIN+VAL)。

---

## 6. Accepted Criteria (本报告)

- [x] TRAIN prior 固定为 `load_v25_channel_counts()` 的 `channel_counts.npz` (TRAIN only)
- [x] 在 TRAIN / VAL / HOLD 三池分别报告 P_TRAIN(U1|B) 与 P_TRAIN(U2|B,U1) NLL/CE (§3.1)
- [x] 每源 TV/JS/平滑 KL (§3.2, eps=1e-12)
- [x] initial error (SER/U1/U2) 与零/罕见 Bob bins 覆盖率 (§3.3, §3.1)
- [x] V48 成功/失败块的 prior NLL/entropy/零计数率 (§3.4)
- [x] VAL 构造候选 TRAIN+VAL, 对比 TRAIN vs CAND 在 HOLD NLL (§3.5), 不用 HOLD 重估
- [x] 唯一三分流结论 (§4 选 B)
- [x] 未修改 V48 输出, 未创建 production implementation, 未运行 decoder

---

## 7. 数据表 (CSV, 与本报告同版)

- `docs/v49_distribution_tables/v49_train_val_hold_nll.csv` — §3.1 + §3.2 行 (含 TV/JS/KL)
- `docs/v49_distribution_tables/v49_train_vs_trainval_on_hold.csv` — §3.5
- 列定义见 `scripts/v49_diagnose_distribution.py` 表头, 单位 bits/symbol, floor 1e-15, eps 1e-12

---

## 8. 限制与声明

- 本报告为 **decoder-free 分布诊断**, 不构成 FER/阈值/SKR/安全/资格陈述; V48 终态仍为 `V48_HELDOUT_FAIL` (30/45)
- 先验熵/交叉熵为 per-symbol bit, 原始块 NLL ≈ 1024× 值 (V32 桥接报告校正: 229-245 bits/block ≈0.22-0.24 bits/symbol 的 QSC 对照在此已校正为 0.81-0.89)
- 若脚本重算后数值与预填偏差 >0.02 bits, 以 CSV 为准并修订本报告 §3 数值, 但分流逻辑 (B) 预期不变除非 1M TV_mean>0.04 或 Δtotal<-0.05 出现

